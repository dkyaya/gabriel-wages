# Parallel 4x1000 live scout validation — 2026-07-27

## Result

PASS. Four isolated staggered lanes reconcile to the committed 4,000-row lock. The coordinator merged 4,000 terminal outcomes: 3,997 parseable and 3 failed. It produced 7,014 discovery candidates and 6,437 deduplicated new-locator rows. The preserved 1,205-row prior queue plus the new rows yields a 7,642-row future combined-review scope.

The interrupted sequential attempt is quarantined and contributes zero rows to candidates or coverage. The four live lanes overlapped in wall-clock time. Lane 4 resumed from its last durable checkpoint after a conservative top-level-list parser repair; no completed parseable identity was rerun. Per-target scratch artifacts are retained locally and ignored by Git, while compact lane and coordinator ledgers are durable.

## Commands

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py` — PASS.
- `.venv/bin/python -m py_compile scripts/gabriel_state_source_scout.py scripts/run_broad_state_4x1000_live_scout.py scripts/run_broad_state_4x1000_parallel_live_scout.py` — PASS.
- `.venv/bin/python scripts/test_broad_state_4x1000_parallel_live_scout.py` — PASS.
- `.venv/bin/python scripts/test_broad_state_4x1000_scout_dry_run_prep.py` — PASS; completed-output rerun made zero writes.
- `.venv/bin/python scripts/test_broad_state_by_state_source_scout_wave.py` — PASS; completed-output rerun made zero writes.
- `.venv/bin/python scripts/test_bounded_tier_c_evidence_memo_supplement.py` — PASS.
- `.venv/bin/python scripts/build_dashboard_data.py` — PASS: 51 states/DC, 35,589 municipalities, 6,919 actual scout-covered municipalities, 13,041 candidate rows.
- `npm --prefix docs/dashboard run build` — PASS; Vite emitted only its existing non-fatal chunk-size warning.
- `.venv/bin/python scripts/validate.py` — PASS.
- `.venv/bin/python ingest/test_pipeline.py` — PASS, 60 tests.
- `git diff --check` — PASS.

## Boundaries

Candidate review, URL opening, HEAD/GET verification, download, source-document inspection, PDF/HTML access, OCR, rendering, text/span extraction, evidence rating, ingestion, codification, normalization, wage-gap calculation, regression, treatment-effect estimation, and national/population-prevalence/final-causal claims were not performed. Raw prompts, raw model responses, and secrets were not persisted. Dashboard global analysis readiness remains false and the map filter remains total scout coverage only.
