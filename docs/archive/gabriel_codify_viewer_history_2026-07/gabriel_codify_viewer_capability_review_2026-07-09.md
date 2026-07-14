# GABRIEL Codify Viewer Capability Review — 2026-07-09

Bounded, read-only inspection of the installed `gabriel` package (version 1.1.8, package name `openai-gabriel`, upstream repo `https://github.com/openai/GABRIEL`). No live model calls, no secrets printed, no network fetch was needed — the installed source code itself was authoritative and sufficient.

## Where inspected

`gabriel.utils.passage_viewer` (`/Users/joachimjohnson/.pyenv/versions/3.11.7/lib/python3.11/site-packages/gabriel/utils/passage_viewer.py`, 2,858 lines), the module backing the top-level `gabriel.view` export already visible in `dir(gabriel)` during the prior pilot session's interface inspection. No bundled tutorial notebook (`.ipynb`) ships with the installed package or its `dist-info`; the upstream GitHub repo (`openai/GABRIEL`) was identified via package metadata (`Project-URL: Repository`) but was not fetched, since the installed source itself already gives ground-truth, more precise answers than a notebook's narrative description would.

## Does GABRIEL have a built-in codify viewer/highlighter?

**Yes — a real, fairly sophisticated one — but it is notebook-bound, not a standalone/portable HTML export tool.**

- **`gabriel.view(df, column_name, attributes=None, *, header_columns=None, max_passages=None, font_scale=1.0, font_family=None, color_mode="auto")`** is the public entry point. Its docstring explicitly supports the special string `attributes="coded_passages"` "for Codify outputs" — i.e., it is purpose-built to visualize exactly the kind of DataFrame `gabriel.codify()` returns (one text column, one snippet-list column per category).
- Internally, `view()` calls `_render_passage_viewer(...)`, which does `from IPython.display import HTML, display` and ends with `display(HTML(style_html + viewer_html))`. **It requires a live IPython/Jupyter (or Colab) kernel to render anything** — run outside a notebook, it builds the HTML string but has no supported way to save or return it as a file; `view()` always returns `None`.
- The rendered viewer is genuinely feature-rich: a dark, Colab-styled `.gabriel-codify-viewer` theme with `.gabriel-controls`/`.gabriel-nav-button` navigation controls, a color-coded category legend (`_build_legend_html`), and click-to-cycle highlighting — clicking a legend swatch scrolls to and briefly flashes the next occurrence of that category's highlighted span (`_build_highlighted_text`, which wraps each matched snippet substring in `<span class='gabriel-snippet' data-category=... style='background-color:...' title='...'>`).
- **The older `tkinter`-based `PassageViewer` class is explicitly retired** in this version: instantiating it raises `RuntimeError("The tkinter-based PassageViewer has been retired. Use gabriel.view(...) inside a notebook environment.")`. There is no supported desktop/standalone viewing path in GABRIEL 1.1.8 at all — notebook display is the only one.

## Relevant functions/classes/patterns found

- `gabriel.view()` / `_render_passage_viewer()` — main entry points (notebook-only).
- `_build_highlighted_text()` — substring-match highlighting technique: find each category's verbatim snippet text within the full passage, wrap it in a colored `<span>`, leave everything else as escaped plain text. This is a clean, reusable pattern.
- `_build_legend_html()` — category color legend with click-to-jump behavior.
- `_generate_distinct_colors()` — matplotlib `tab20`-based (or HSV-fallback) distinct color palette generator for N categories.
- `attributes="coded_passages"` special-case handling — auto-detects a `coded_passages` dict column (category → snippet list) as produced by `codify()`'s raw internal representation, distinct from the wide-column CSV format `codify()` actually returns to callers (one column per category, each holding a snippet list).

## Are these usable in this repo?

**Partially, and only with real friction.** The underlying HTML/CSS/JS `_render_passage_viewer` assembles (`style_html + viewer_html`) is self-contained (no external CDN dependencies visible in the inspected `<style>`/`<script>` blocks), so it is *technically* capturable by monkey-patching `IPython.display.HTML` to return the string instead of trying to render it, then writing that string to a file. This was deliberately **not done** for this project, for three reasons:
1. It depends on private, underscore-prefixed internals (`_render_passage_viewer`, `style_html`/`viewer_html` local variables) that are not a documented, stable public API — likely to break across GABRIEL versions.
2. GABRIEL's viewer is designed around **one text column with attribute-tagged spans inside it**, not this project's actual need: a **dataset-wide, multi-document evidence table** spanning many contracts, filterable by metadata columns (state, city, occupation_class, source_role, evidence_status, source_grounding_status) that have no equivalent concept in GABRIEL's viewer (its `header_columns` parameter only *displays* metadata above each passage; it does not provide filter dropdowns/faceted search across it).
3. `PassageViewer`'s retirement message itself confirms GABRIEL's own maintainers intend `view()` for live notebook use, not as a general-purpose exportable research-data browser.

## Recommended viewer strategy

**Build a project-local, self-contained static HTML viewer** (Task C), since GABRIEL's built-in display does not meet this project's actual requirement — a durable, git-committable, double-click-to-open file that supports faceted filtering across state/city/contract_id/occupation_class/source_role/attribute/evidence_status/source_grounding_status plus free-text search, which is outside GABRIEL's viewer's designed scope. The project-local viewer borrows one concrete design pattern from GABRIEL's approach worth reusing: **highlighting an excerpt by wrapping its exact matched text in a colored `<mark>`/`<span>` within its surrounding context**, rather than showing the excerpt as an isolated fragment with no visual anchor to its source window.
