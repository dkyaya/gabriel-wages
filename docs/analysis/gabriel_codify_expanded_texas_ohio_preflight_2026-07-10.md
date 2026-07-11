# GABRIEL Codify — Expanded Texas/Ohio Preflight — 2026-07-10

## Purpose

This run merges the previously-recovered Texas/Ohio source-expansion commit into `main`, attempts a bounded OCR recovery for San Antonio police, then codifies the 9 newly expanded Texas/Ohio sources through the existing Harvard-Proxy-adapted `gabriel.codify()` pilot, appends the results to the durable evidence layer, and rebuilds the PI-facing viewer. **This run performs no report scaffolding and creates no final report artifacts** — it prepares the evidence layer for that future work.

## Merge status

`git merge worktree-tx-oh-expansion-recovery` — **fast-forward, clean**. Before merging, the main checkout's working tree held an untouched copy of the same uncommitted pre-interruption state (identical byte-for-byte to what the recovery run had already committed as `9c42999`, verified via SHA-256 checksum comparison for all 9 corpus PDFs and diff comparison for the 2 modified CSVs and 4 untracked docs). That state was stashed (`git stash push -u -m "pre-merge-backup-tx-oh-2026-07-10-relay"`, entry `18f89ec`) before the merge to clear the working tree, then confirmed identical to the merged result and left in the stash list as a redundant safety backup (not dropped this session).

- Latest commit after merge: `9c42999` — "Expand Texas and Ohio sources".
- `data/contracts.csv`: 53 data rows (44 pre-expansion + 9 new).
- `data/city_coverage.csv`: 53 data rows, 1:1 matched to contracts.
- `city_attributes`: 3 rows (unchanged).
- Distinct cities: 16.
- Healthy matched pairs (`ingest/audit_coverage.py`): 23 (exact-cycle: 9, overlap-cycle: 14).
- `python scripts/validate.py`: PASSED.

## Evidence-layer state before this run's codify batch

`docs/analysis/gabriel_codify_evidence_layer.csv`: **603 rows** (261 present: 252 verified + 9 flagged; 342 not_found), spanning Massachusetts, Texas (Houston, Austin), and Ohio (Columbus, Cleveland). Seekonk and Wayland (Massachusetts) are the most recently added cities. San Antonio, Cincinnati, and Toledo do not yet appear anywhere in the evidence layer.

## The 9 rows to be codified this run

| # | contract_id | state | city | occupation_class | text_quality |
|---|---|---|---|---|---|
| 1 | `tx_san_antonio_police_2022` | TX | San Antonio | police | `ocr_messy` (upgraded this session, see below) |
| 2 | `tx_san_antonio_fire_2024` | TX | San Antonio | fire | `clean` |
| 3 | `oh_cincinnati_police_2024` | OH | Cincinnati | police | `clean` |
| 4 | `oh_cincinnati_police_sup_2024` | OH | Cincinnati | police | `clean` |
| 5 | `oh_cincinnati_fire_2023` | OH | Cincinnati | fire | `clean` |
| 6 | `oh_cincinnati_other_2025` | OH | Cincinnati | other | `clean` |
| 7 | `oh_toledo_police_2024` | OH | Toledo | police | `clean` |
| 8 | `oh_toledo_fire_2024` | OH | Toledo | fire | `clean` |
| 9 | `oh_toledo_other_2024` | OH | Toledo | other | `clean` |

## San Antonio police OCR issue and bounded repair plan

At session start, `tx_san_antonio_police_2022` (`corpus/tx_san_antonio/tx_san_antonio_sapoa_police_cba_2022_2026.pdf`) was a 218-page image scan with `text_quality=partial` and essentially zero extractable text (`pdftotext` yields 218 characters total). Plan: a single bounded OCR pass (render all pages via `pdftoppm`, OCR via `tesseract`, combine into a cache file under `tmp/`) with a hard stop if runtime became excessive or output stayed unusable — full detail and outcome in `docs/analysis/san_antonio_police_bounded_ocr_recovery_2026-07-10.md`. Outcome (completed before this memo's final version): recovery succeeded (~4 minutes total, legible article-structured text across all 218 pages); `text_quality` updated to `ocr_messy` and `cycle_start` corrected to a document-confirmed date; all 9 rows above proceed to codify with a genuine source window, none skipped.

## Live-call cap

`scripts/gabriel_codify_pilot.py`'s hard cap (`HARD_MAX_CALLS`) is raised from 8 to 9 in code this run (a deliberate, documented code edit, not a CLI flag — consistent with this script's own established pattern of raising/lowering the cap per approved batch) to accommodate codifying all 9 selected rows in one run, each as its own isolated `gabriel.codify()` call. `--max-calls 9` will be passed explicitly.

## Stop rules (this run)

- No web search, no new source downloads, no FOIA/PRR, no new document ingestion.
- No edits to `docs/schema.md`.
- No edits to any corpus PDF (San Antonio police OCR reads the existing PDF only; the file itself is never modified).
- Max 9 live `gabriel.codify()` calls, each isolated per row; stop on first serious adapter/API failure; no retries; no broadening the sample.
- No full-corpus GABRIEL run.
- No model/API calls outside the capped `scripts/gabriel_codify_pilot.py` script.
- No printing, inspecting, copying, or committing API keys/secrets — credential presence is checked as a boolean only.
- **No final report PDF/DOCX artifacts are created in this run.** This run's explicit purpose is to prepare the evidence layer (codify + viewer rebuild) for a future report-scaffolding run — not to write the report itself.
- No causal claims stronger than the source evidence supports — codify output remains binary present/not_found evidence with source-grounding verification, not a causal-effect measurement.
