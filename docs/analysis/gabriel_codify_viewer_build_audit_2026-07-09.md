# GABRIEL Codify Viewer Build Audit — 2026-07-09 (updated: PI-facing overhaul)

This memo supersedes the same-named memo from earlier the same day, which audited the first (repo/data-facing) build. This update audits the overhauled, PI-facing viewer.

## Command run

```text
python scripts/build_codify_evidence_viewer.py
```

(default arguments: `--input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv`, `--evidence-out docs/analysis/gabriel_codify_evidence_layer.csv`, `--html-out docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, `--html-latest-out docs/analysis/gabriel_codify_excerpt_browser_latest.html`)

Output:

```text
Codify evidence layer + viewer build summary
  input rows read:          92
  evidence rows written:    92
  present (evidence found): 53
  not_found:                39
  verified present:         53
  rows with contract label from data/contracts.csv: 92/92
  evidence CSV:             docs/analysis/gabriel_codify_evidence_layer.csv
  dated html browser:       docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html
  latest html browser:      docs/analysis/gabriel_codify_excerpt_browser_latest.html
```

Re-run a second time (idempotency check) produced identical row counts and byte-identical HTML output. `gabriel_codify_excerpt_browser_2026-07-09.html` and `gabriel_codify_excerpt_browser_latest.html` were diffed and confirmed **identical** (both built from the same run, as intended — the dated file is a same-day archival snapshot, and future rebuilds will only update `_latest.html` plus a new dated file if the build date changes).

## Rows read/written and counts

- Input rows read: **92**.
- Evidence rows written: **92**.
- `present` (evidence found): **53**.
- `not_found` (no evidence found): **39**.
- `evidence_id` duplicates: **0** (checked programmatically at write time).
- `contract_label` resolved from `data/contracts.csv` for **92/92** rows (all 4 contracts in the current dataset are present in `data/contracts.csv`, so no fallback "City Occupation — contract_id" labels were needed this run — that fallback path exists and is ready for a future contract not yet cross-referenced there).
- Verified present (evidence found **and** confirmed as a verbatim match in its source window — formerly labeled "grounded present"): **53** (100% of present rows).

## Dated viewer path

`docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` — 194,714 bytes.

## Latest viewer path

`docs/analysis/gabriel_codify_excerpt_browser_latest.html` — 194,714 bytes, byte-identical to the dated file as of this build. **This is the file to open and share.**

## Implemented improvements (this overhaul)

- **Plain-English labels as primary display.** State, city, occupation, source role, attribute, evidence status, and grounding status all render as their plain-English label everywhere in the UI (filter dropdowns, card headers, table columns); the underlying snake_case/coded values are demoted to a per-card collapsible "Technical details" section.
- **Human-readable contract labels** (`contract_label`), derived conservatively from `data/contracts.csv` (`city_name`, `occupation_class`, `bargaining_unit_name`, `source_type`, `cycle_start`/`cycle_end`) — no invented text, only composed real fields. Example: `"Houston Fire — Houston Professional Fire Fighters Association, Local 341, International Association of Fire Fighters arbitration award, 2024–2029"`.
- **Attribute glossary** — all 19 mechanism definitions in a collapsible sidebar section, plus the specific definition re-shown inline on every card.
- **Cascading (faceted) filters** — implemented in `rebuildCascadingFilters()`/`rowsMatchingExcept()`: each dropdown's available options are recomputed from rows matching every *other* currently-selected filter, so selecting a state removes cities/contracts/attributes that don't occur in that state, and so on symmetrically in any order (not merely a fixed top-down chain).
- **Evidence-present-by-default attribute filter** — `rebuildAttributeOptions()` restricts the mechanism dropdown to attributes with at least one `present` row in the current filtered scope, with a "Show mechanisms with no evidence" checkbox to opt back into the full 19-attribute list.
- **"Grounded" renamed and explained.** Every UI instance now reads **"Verified in source text"** (`SOURCE_GROUNDING_LABELS["grounded"]`), with an explicit explanation in the top "How to use this viewer" section and the usage doc: it is a text-integrity check confirming the excerpt is a real verbatim match, **not** an analytical or causal claim.
- **"What this excerpt shows"** — a template-based, non-model-generated, attribute-specific sentence on every present-evidence card (`_what_excerpt_shows()` in Python), explicitly distinguishing interest/impasse arbitration from grievance arbitration and peer-comparator language from internal wage-schedule language, per Task D's requirements. `not_found` rows show the fixed sentence "No excerpt was returned for this attribute in the selected source window."
- **Causal-proof warning** shown three times: a persistent banner at the top of the page, inside the "How to use this viewer" section, and as a one-line reminder on every present-evidence card.
- **Copy conveniences** — "Copy excerpt" and "Copy citation" buttons per card, implemented in vanilla JS with `navigator.clipboard.writeText()` as the primary path and a `document.execCommand('copy')` hidden-textarea fallback for `file://` contexts where the Clipboard API may be restricted.
- **Dated + latest output pair** — `--html-out` (archival) and `--html-latest-out` (portable/shareable, stable filename) are both written from the same generated HTML string in one build.
- **Default sort order** — state → city → contract → attribute (by plain-English label), applied client-side after filtering.

## Verification performed (no browser-automation tool available)

- Extracted the embedded `<script>` block from `_latest.html` and syntax-checked with `node --check` — **passed**.
- Extracted and parsed both embedded `const EVIDENCE = [...]` (92 rows) and `const ATTRIBUTES = [...]` (19 entries, each with `code`/`label`/`definition`) JSON blocks with Python `json.loads()` — both parsed cleanly.
- Grepped for required phrases in the built HTML: `"Verified in source text"` (2 occurrences), `"What this excerpt shows"` (1, plus rendered per-card via JS), `"does not by itself"` (1, the causal-proof warning), `"Copy excerpt"`/`"Copy citation"` (2 each — CSS class name + JS label), `"Mechanism glossary"` (1), `"Show mechanisms with no evidence"` (2) — all present as expected.
- Confirmed **zero** `<script src=...>`, external `<link href="http...">`, or CDN references — fully self-contained.
- Confirmed **zero** occurrences of API-key-like strings (`api_key`, `subscription_key`, `sk-...` patterns) in the built HTML.
- Confirmed no stray unresolved `{{`/`}}` template-escape artifacts in the output (Python `.format()` braces resolved correctly throughout the large CSS/JS block).

## Limitations

- **No live browser screenshot/rendering was performed** — no browser-automation tool is available in this sandboxed session. Verification relies on syntax checking, data-parsing checks, and direct code review of the rendering/filtering functions. The user should open `gabriel_codify_excerpt_browser_latest.html` directly and manually exercise the filters, glossary, card navigation, table view, and copy buttons before relying on it for real review or sharing it further.
- **Clipboard behavior can vary by browser/OS when opening a `file://` URL** — the `execCommand('copy')` fallback is included specifically for this reason, but was not interactively tested in a real browser this session.
- **The evidence layer still only covers the 4 Texas/Ohio contracts** from the one full-codebook pilot run. Massachusetts is not yet included (by design — out of scope this session); the label maps already support it.
- **The builder still reads exactly one `--input` CSV and fully rewrites the evidence layer from it** — appending a second (e.g., Massachusetts) codify run's output requires either concatenating input CSVs first or extending the script with an explicit append/union mode (not built this session; documented as a near-term follow-up in the overhaul plan).
- Contract labels are only as good as `data/contracts.csv`'s own fields; for any future contract not yet present there, the builder falls back to a generic `"City Occupation — contract_id"` label rather than inventing a title.

## Manual testing recommendations

1. Open `docs/analysis/gabriel_codify_excerpt_browser_latest.html` directly in a browser.
2. Select a state, confirm the city dropdown narrows to only that state's cities; select a city, confirm the contract dropdown narrows further; clear the state and confirm options repopulate correctly.
3. Toggle "Show mechanisms with no evidence" on and off and confirm the attribute dropdown's option count changes accordingly.
4. Click "Copy excerpt" and "Copy citation" on a present-evidence card and paste somewhere to confirm the clipboard contents are correct.
5. Switch to Table view, confirm plain-English labels (not codes) appear in every column.
6. Expand "Technical details" on a card and confirm the raw contract_id/attribute code/evidence_id are shown there, not in the main card body.

## Next step before scaling codify

Scale codify to the remaining Texas/Ohio matched-city rows, then run a curated Massachusetts batch (per the overhaul plan's short-term roadmap), then extend `scripts/build_codify_evidence_viewer.py` with a genuine append/union mode (keyed on `evidence_id`) before the next rebuild, so the evidence layer and viewer accumulate across runs instead of being fully rewritten from a single input file each time.
