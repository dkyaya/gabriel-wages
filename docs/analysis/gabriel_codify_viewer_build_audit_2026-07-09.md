# GABRIEL Codify Viewer Build Audit — 2026-07-09

## Command run

```text
python scripts/build_codify_evidence_viewer.py
```

(default arguments: `--input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv`, `--evidence-out docs/analysis/gabriel_codify_evidence_layer.csv`, `--html-out docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`)

Output:

```text
Codify evidence layer + viewer build summary
  input rows read:        92
  evidence rows written:  92
  present:                53
  not_found:              39
  grounded present:       53
  evidence CSV:           docs/analysis/gabriel_codify_evidence_layer.csv
  html browser:           docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html
```

Re-run a second time (idempotency check) produced byte-for-byte identical row counts and no errors — the script is safe to re-run without side effects, and future codify runs can extend `--input` to a concatenation of multiple output CSVs (or the script can be re-invoked once per new pilot output) to append further rows to `gabriel_codify_evidence_layer.csv`.

## Evidence table row counts

- Total rows: **92** (4 contracts × 19 attributes + 15 extra rows for attributes with more than one matched snippet).
- `present`: **53**.
- `not_found`: **39**.
- `evidence_id` duplicates: **0** (checked programmatically at write time; the script raises if any are found).
- `source_file` populated for all 92 rows (looked up from `docs/analysis/*evidence_windows*.csv` by `contract_id`).
- `excerpt` populated for all 53 `present` rows and blank for all 39 `not_found` rows (enforced: the script raises if a `present` row has a blank excerpt).

## Browser path

`docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` — 104,453 bytes, self-contained (no `<script src=...>`, no external `<link href="http...">`, no CDN references of any kind).

## Filter capabilities

Sidebar dropdown filters for: state, city, contract_id, occupation_class, source_role, attribute, evidence_status, source_grounding_status — plus a free-text search box (matches against excerpt and notes text, case-insensitive) and a "Show not_found rows" toggle (present-only by default). A "Reset filters" button clears all of the above. A live counts panel shows total rows, present, not_found, grounded present, and the currently-selected/filtered count, all computed client-side from the embedded data.

## Whether excerpts are highlighted

**Yes.** Verified at three levels:
1. Source-level: `highlightExcerpt()` wraps excerpt text in `<mark>...</mark>` (dynamically, per rendered card — the excerpt itself already *is* the exact matched span GABRIEL codify returned, so the highlight wraps the whole excerpt rather than a substring search within a larger passage, since this viewer's "cards" show one excerpt at a time rather than a full source document).
2. Syntax-level: the embedded `<script>` block was extracted and checked with `node --check` — **passed, no syntax errors**.
3. Data-level: the embedded `const EVIDENCE = [...]` JSON was extracted and parsed with `json.loads()` — **92 rows, 53 present, all fields intact**, confirming the data GABRIEL codify produced is faithfully embedded and available to the highlighting/filtering JS at page load.

No live browser rendering/screenshot was performed in this sandboxed session (no browser automation tool available); verification relied on syntax checking, data-parsing checks, and direct code review of the rendering functions (`renderCards`, `renderTable`, `applyFilters`), all consistent with correct behavior.

## Limitations

- No actual browser screenshot was taken to visually confirm on-screen rendering — code-level and data-level checks stand in for it. The user should open the file directly (`open docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` or double-click it) to do a final visual pass.
- The viewer's "Cards" mode highlights the excerpt as a whole (since GABRIEL codify's output is already a short verbatim span, not a position within a longer passage) rather than highlighting a sub-span within a larger surrounding-context block — a deliberate simplification appropriate to this project's compact evidence windows, distinct from GABRIEL's own notebook viewer (which highlights spans within a full passage of text).
- `source_file` is resolved via a best-effort lookup against `docs/analysis/*evidence_windows*.csv` files already in the repo; if a future codify run's `contract_id` isn't present in any evidence-windows CSV, `source_file` will be blank for those rows (not an error, just missing metadata).
- The evidence table currently reflects only the one full-codebook pilot run (4 contracts). It is structurally ready to accumulate more rows from future pilot runs (append-friendly schema, collision-resistant `evidence_id` scheme keyed by run date + contract + attribute + sequence), but no accumulation has been exercised yet since there is only one run's worth of data so far.

## Recommended next step before scaling codify

1. Open the browser file directly and do a manual visual/interaction pass (filters, card navigation, table view) before relying on it for real review work.
2. When a second codify pilot run happens, re-run `scripts/build_codify_evidence_viewer.py` with `--input` pointed at a combined/concatenated CSV of all output files to date (or extend the script with a `--append` mode that unions multiple input CSVs) so `gabriel_codify_evidence_layer.csv` and the browser stay a single durable, cumulative view rather than being overwritten per run.
3. Continue requiring a source-grounding audit (as in `gabriel_codify_full_codebook_audit_2026-07-09.md`) before any new run's rows are merged into the evidence layer — this build script does not itself re-verify grounding, it only carries forward whatever `source_grounding_status` the input CSV already recorded.
