# Report Polish Preflight — 2026-07-10

## Purpose

This run reviews and polishes the already-committed safety/non-safety wage-mechanism report scaffold: fixes known issues, creates the missing graph audit file, verifies all report assets and figure references, tightens prose for PI readability, and prepares the report for a later final DOCX/PDF export. **No GABRIEL/codify, Harvard Proxy, or model/API calls are authorized this run. No new source collection, no FOIA/PRR. No final DOCX/PDF artifact is produced.**

## Repo state at start of this run

- `git status`: clean except untracked `.claude/` (a leftover worktree from an earlier session) and `tmp/` (scratch/relay-bundle directory). No unexpected uncommitted changes.
- Latest commit: `74836f7` — "Commit report scaffold: safety/non-safety wage-mechanism evidence patterns", stacked on `20a0f26` ("Codify expanded Texas and Ohio sources") and `9c42999` ("Expand Texas and Ohio sources").
- `data/contracts.csv` and `data/city_coverage.csv`: confirmed **unchanged** since `74836f7` (`git diff 74836f7 -- data/contracts.csv data/city_coverage.csv` returns empty).
- `docs/analysis/report_assets/` exists: **20 files** (7 PNG, 7 SVG, 6 CSV).

## Report files found

| file | lines | status |
|---|---|---|
| `report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md` | 147 | present, committed |
| `report_appendix_tables_2026-07-10.md` | 117 | present, committed — contains the known "Two rows" typo |
| `report_scaffold_preflight_2026-07-10.md` | 62 | present, committed |
| `report_evidence_layer_audit_2026-07-10.md` | 133 | present, committed |
| `report_graph_audit_2026-07-10.md` | — | **missing** — this run's Task B creates it |

## Report asset files found (`docs/analysis/report_assets/`)

CSVs (6): `city_mechanism_matrix_2026-07-10.csv`, `mechanism_presence_by_occupation_2026-07-10.csv`, `mechanism_presence_by_state_2026-07-10.csv`, `mechanism_presence_by_state_occupation_2026-07-10.csv`, `source_inventory_for_report_2026-07-10.csv`, `top_mechanisms_by_group_2026-07-10.csv`.

Figures (7, each PNG+SVG): `mechanism_presence_overall_by_safety_group_2026-07-10`, `mechanism_presence_by_state_2026-07-10`, `arbitration_distinction_by_state_occupation_2026-07-10`, `pressure_conversion_mechanisms_by_occupation_2026-07-10`, `ohio_matched_triad_mechanism_matrix_2026-07-10`, `massachusetts_cross_occupation_matrix_2026-07-10`, `texas_institutional_contrast_2026-07-10`.

All 20 files present; no PNG/SVG pair is missing its counterpart.

## Evidence layer snapshot (`docs/analysis/gabriel_codify_evidence_layer.csv`)

- Total rows: **781**.
- `evidence_status=present`: **293**. `not_found`: **488**.
- `viewer_verified=1` present rows (used for headline graphs): **284**.
- `viewer_verified=0` present rows (flagged/unverified, excluded from headline graphs): **9**.
- `source_grounding_status=grounded`: **289**.
- Distinct codified contracts: **37** (of 53 total in `data/contracts.csv`).
- States: MA, TX, OH. Distinct cities with evidence: **13**.

## Known issues to fix this run

1. `docs/analysis/report_graph_audit_2026-07-10.md` was requested in the prior report-scaffold run but never created — **missing**, create per Task B spec.
2. `docs/analysis/report_appendix_tables_2026-07-10.md` line 75 says "Two rows" but lists four contract IDs (`oh_cincinnati_fire_2023`, `oh_cincinnati_police_sup_2024`, `ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) — fix to "Four rows."
3. Graph references and paths in the report scaffold need verification against the actual files in `report_assets/` (all six inline `![...]()` image references, plus the appendix's figure/table index).
4. Prose in the main scaffold should be tightened for PI readability while preserving: evidence-pattern (not causal-proof) framing; the binary present/not_found nature of codify; that only verified-present rows back headline graphs; and avoiding "the leading cause" as a factual claim.

## Checks to run this session

- `python scripts/validate.py`
- `python ingest/audit_coverage.py`
- Evidence-layer and report-asset CSVs parse cleanly (Python `csv` module, no width mismatches).
- Every image reference in the report scaffold resolves to an existing file relative to `docs/analysis/`.
- `report_graph_audit_2026-07-10.md` (once created) lists every graph/table asset actually present in `report_assets/`.
- Confirm `data/contracts.csv` and `data/city_coverage.csv` remain byte-identical to their state at `74836f7` after this run's edits.
- Confirm no GABRIEL/codify, Harvard Proxy, model, or API calls occurred (no new entries in `logs/api_spend_log.csv`, no new codify output files).

## Explicit scope confirmation

**No GABRIEL/codify calls, no Harvard Proxy/model/API calls, and no new source collection (web search, FOIA/PRR, or corpus downloads) are authorized or will occur in this run.** This run edits Markdown (report scaffold, appendix, new graph audit, light guidance-doc updates) and, only if a clear error is found, an existing report-asset CSV — it does not regenerate graphs, touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`, and does not produce a final PDF/DOCX artifact.
