# GABRIEL Codify Viewer Overhaul Plan — 2026-07-09

## 1. Purpose and scope

This run overhauls the local GABRIEL codify excerpt viewer for **usability and portability**, so it can be shared with and used directly by the PI, not just by whoever built the underlying data. **No new codify, Harvard Proxy, or model/API calls are made in this run** — every change operates on the existing `gabriel_codify_full_codebook_outputs_2026-07-09.csv` (4 contracts, 92 rows, from the prior Harvard Proxy pilot session). **Massachusetts support is prepared in the builder/viewer design, but no MA codify run happens this session** — the evidence layer and viewer must not hardcode assumptions that only Texas/Ohio exist, so that a future MA codify run's output can be appended without another rewrite.

## 2. Current viewer limitations

- **Underscored technical labels everywhere.** Attribute names (`peer_comparator_wage_comparability`), state codes (`TX`), source roles (`non_safety_general`), and evidence statuses (`not_found`) are shown as raw snake_case/codes, not plain English — fine for an RA, not for a PI skimming the tool.
- **Non-cascading filters.** All eight filter dropdowns (state, city, contract, occupation, source role, attribute, evidence status, grounding status) are populated from the *entire* dataset regardless of other selections, so picking a state doesn't narrow the city list, and picking a contract doesn't narrow the attribute list — a PI can select an impossible combination (e.g., a Texas state + an Ohio-only city) and just see an empty result with no explanation.
- **All attributes shown regardless of evidence.** The attribute dropdown lists all 19 codes even when most have zero `present` rows for whatever is currently filtered, cluttering the menu with dead options.
- **"Grounded" terminology is ambiguous and easy to over-read.** A PI seeing "grounded: grounded" could reasonably (and wrongly) read that as "this proves the finding," when it actually only means the excerpt text was verified as a real, verbatim substring of the source window — a text-integrity check, not an analytical claim.
- **Limited explanation of what an excerpt actually shows.** Cards display the raw excerpt and the raw attribute code with no plain-language bridge between "here is text" and "here is why this text was coded under this attribute."
- **No stable "latest" output name.** The only HTML file is date-stamped (`gabriel_codify_excerpt_browser_2026-07-09.html`); a future viewer rebuild would need a new dated file, and there's no single, obviously-current file to point a PI to or re-share after an update.

## 3. PI-facing viewer requirements

- Plain-English labels as the **primary** display everywhere; underscored technical IDs demoted to a collapsible "Technical details" section per card, not the main label.
- An attribute glossary (definitions for all 19 codes) accessible from a sidebar section and referenced inline near the attribute filter and on every card.
- Cascading filters: state constrains city; city constrains contract; contract/source constrains occupation/source-role/attribute options.
- Evidence-present default: the attribute filter defaults to only attributes with `present` evidence in the currently filtered set, with an explicit "Show attributes with no evidence" toggle to opt back in to the full list.
- "Verified in source text" replaces "grounded" as the primary label everywhere in the UI, with an explanation that this confirms text integrity, not an analytical/causal claim.
- A per-card "What this excerpt shows" line, generated from a fixed template keyed to the attribute (not a new model call), explicitly avoiding causal language.
- Copy-to-clipboard convenience for the excerpt text and for a full citation block (vanilla JS `navigator.clipboard`, no external library).
- Single self-contained static HTML file (embedded data + CSS + JS), openable directly with no server, with a stable `..._latest.html` filename alongside the dated archival copy.
- A standing warning, visible at the top of the page and not just buried in a tooltip: excerpts show evidence that a wage-mechanism *is discussed in the source text* — they do not by themselves prove any wage or causal effect.

## 4. Massachusetts preparation

Massachusetts is not run through codify this session — the project's existing MA corpus (14 contracts) and its extensive prior hand-built mechanism-excerpt work are a natural, high-value future codify target, but adding it now would violate this run's scope (no new model calls). What this run does instead: the evidence-layer builder (`scripts/build_codify_evidence_viewer.py`) and its label maps (state, occupation, source-role) already cover `ma` alongside `tx`/`oh` — nothing in the builder is Texas/Ohio-specific. The builder reads `--input` as a single codify-output CSV path with no state filtering logic; a future MA codify run's output CSV can be fed through the same `build_evidence_rows()`/`write_evidence_csv()`/`build_html()` pipeline unchanged. The only forward-looking gap (documented, not fixed this session — see the build audit's "next step") is that the builder currently only reads *one* `--input` file per run and fully overwrites the evidence layer from it; before a second (MA) codify run lands, the script should gain an append/union mode keyed on `evidence_id` so Texas/Ohio rows already in `gabriel_codify_evidence_layer.csv` survive being joined by new Massachusetts rows.

## 5. Short-term vs. long-term roadmap

**Short-term:**
1. Overhaul the viewer (this run).
2. Scale codify to the remaining Texas/Ohio matched-city rows not yet coded (`tx_houston_police_2024`, `tx_austin_fire_2023`, `oh_columbus_police_2023`, `oh_columbus_other_2024`, `oh_cleveland_police_2025`, `oh_cleveland_fire_2025`, `oh_cleveland_other_2022`).
3. Run a curated Massachusetts codify batch (a small, deliberately chosen sample first, mirroring how the Texas/Ohio pilot started small before scaling).
4. Rebuild the evidence layer and viewer from the combined output.

**Long-term:**
- A genuinely append-friendly evidence layer (union multiple codify-run CSVs by `evidence_id`, not overwrite).
- Reviewed / not-yet-reviewed flags per evidence row, so a human reviewer's sign-off is tracked separately from the model's own output.
- Free-text RA/PI notes attached to individual evidence rows, distinct from codify's own `notes` field.
- Side-by-side state/city comparison views (e.g., "show this attribute for Houston Fire next to Columbus Fire").
- Export-filtered-evidence-to-CSV/citation-list from within the viewer, for building report appendices.
- A generated report-appendix view (structured, citation-ready, but still explicitly not a causal-claims document) once enough evidence has accumulated and been reviewed.
