# GABRIEL Codify Viewer Build Audit — 2026-07-09 (updated: Texas/Ohio scale-up append/union rebuild)

This memo supersedes the two same-named memos from earlier the same day (first the repo/data-facing build, then the PI-facing overhaul of the 4-row pilot output). This update audits the rebuild that unions the original 4-row pilot output with the new 8-row Texas/Ohio scale-up output via the builder's new append/union mode (Task B).

## Builder command

```text
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-latest-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html
```

This is the same command given in this run's task instructions, with one adjustment: `--archive-html` is accepted as a synonym for the existing `--html-out` flag (both map to the same destination), so the dated/archival output lands at `gabriel_codify_excerpt_browser_2026-07-09_scaleup.html` rather than overwriting the earlier same-day `gabriel_codify_excerpt_browser_2026-07-09.html` — deliberately preserving that file untouched rather than replacing it unintentionally. `git status` confirms it is not modified by this run.

## Input files included

1. `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` — the original 4-row pilot output (92 rows).
2. `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — this run's 8-row Texas/Ohio scale-up output (173 rows).

## Append/union mode verification (Task B)

Before this real rebuild, the new multi-input logic was smoke-tested:
- Default invocation (no `--input`) still reads exactly the original single pilot CSV and reproduces the pre-overhaul row counts (92 rows, 0 duplicates skipped) — confirms the existing default `python scripts/build_codify_evidence_viewer.py` behavior is unbroken.
- The same file passed twice (`--input a.csv,a.csv`, comma-separated) correctly wrote 92 evidence rows with **92 duplicates skipped** — confirms the full-row-content dedup logic works and rebuilds are idempotent.
- An earlier version of the dedup logic (keyed on `(contract_id, attribute, run_id)` alone) was found, during this same testing, to incorrectly collapse legitimate multi-excerpt rows (`gabriel.codify()` sometimes returns more than one distinct excerpt for the same attribute in the same run — e.g. `tx_houston_fire_2024` / `grievance_or_contract_interpretation_arbitration` has 2 genuinely different excerpts). Fixed by deduping on full row content instead (every field must match, not just the identifying triple) before this run's real rebuild.

## Evidence-layer row counts after this rebuild

- Input rows read (total, across both files): **265** (92 + 173).
- Duplicate rows skipped: **0** (the two input files do not overlap — the pilot and scale-up covered entirely different contract_ids).
- Evidence rows written: **265**.
- `present` (evidence found): **148**.
- `not_found`: **117**.
- `evidence_id` duplicates: **0** (checked programmatically at write time, as before).
- `contract_label` resolved from `data/contracts.csv` for **265/265** rows (all 12 distinct contract_ids across both batches are present in `data/contracts.csv`).
- **Verified in source text** (evidence found *and* confirmed as a verbatim match in its own row's `source_output_file`'s window): **148** (100% of present rows) — this count includes the one flagged header-leakage artifact row (`oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`; see `gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md`), since it is a genuine substring of its window text even though that window text is not genuine source-document content. That row's `notes` field carries the flag explicitly; it is not silently indistinguishable from the other 147 genuinely-sourced present rows.

## Viewer paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` — 494,551 bytes.
- **Dated archival copy for this run:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html` — 494,551 bytes, byte-identical to latest.
- **Untouched, still present:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` (the earlier same-day 92-row archival copy from the viewer overhaul) — confirmed via `git status` that this file was not modified by this rebuild.

## Whether cascading filters and plain-English labels remain intact

Yes — no changes were made to `build_html_doc()`, `HTML_TEMPLATE`, or any of the JS filtering/rendering functions this run; only the Python-side row-assembly path (`build_evidence_rows()`/`write_evidence_csv()`/`main()`) was changed to support multiple inputs. Verified directly on the rebuilt `_latest.html`:
- `node --check` on the extracted `<script>` block — **passed**.
- `json.loads()` on both embedded `const EVIDENCE = [...]` (265 rows) and `const ATTRIBUTES = [...]` (19 entries) — both parsed cleanly.
- All 4 Texas/Ohio matched cities (Houston, Austin, Columbus, Cleveland) now show both a safety (`police`/`fire`) and a non-safety comparison occupation (`other` for Houston/Columbus/Cleveland; `nurse_health` for Austin, plus `fire` for Austin) in the parsed `EVIDENCE` data — confirmed programmatically by grouping rows by `(state, city)` and listing distinct `occupation_class` values.

## Manual testing recommendations (unchanged from the prior audit — still outstanding)

1. Open `docs/analysis/gabriel_codify_excerpt_browser_latest.html` directly in a browser.
2. Confirm the state/city/contract cascading filters now show all 4 Texas/Ohio matched cities, not just Houston/Austin from the original pilot.
3. Filter to `oh_cleveland_fire_2025` and confirm the flagged `interest_arbitration_or_formal_impasse_backstop` card's "Notes" section visibly shows the methodology-flag text (a live-browser check that the flag reads clearly to a PI, not just that it exists in the CSV).
4. Toggle "Show mechanisms with no evidence" and confirm `peer_comparator_wage_comparability` now appears with a visibly larger `not_found` count across the combined 12-contract dataset.
5. Copy-excerpt/copy-citation buttons — still not interactively tested in a real browser this session; same limitation as the prior audit.

## Next step before scaling further

Fix the window-assembly header-leakage failure mode identified in `gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md` (neutral, keyword-free window-section headers) before the next codify batch, then run a curated Massachusetts codify batch — the append/union mode built and verified this run is what makes that a clean `--input` addition rather than a full rebuild-from-scratch.
