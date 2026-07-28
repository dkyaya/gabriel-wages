# Validation report

All required lane-resume, coordinator, dashboard, repository, and ingestion validations passed on 2026-07-28.

## Results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_parallel_live_scout.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_scout_dry_run_prep.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py`: passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; generated 51 states/DC, 35,589 municipalities, 6,919 scout-covered municipalities, and 13,041 candidate rows.
- `npm --prefix docs/dashboard run build`: passed; Vite production build completed. The existing large-chunk advisory was non-fatal.
- `.venv/bin/python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py`: passed; 60 tests, 0 failures.
- `git diff --check`: passed.

## Reconciliation and boundaries

- Lane 004 locked/completed: 2,144/2,144.
- Final merged locked/completed: 8,574/8,574.
- Prior lane 004 sandbox-denied `ConnectError` rows counted: 0.
- Lanes 001–003 rerun count: 0.
- Candidate review, downloads, source review, content inspection, OCR, rendering, extraction, rating, ingestion, codification, and statistical analysis runs: 0.
- Dashboard map filter: total scout coverage only.
- Dashboard scout-covered municipalities: 6,919.
- Global analysis readiness: false.
