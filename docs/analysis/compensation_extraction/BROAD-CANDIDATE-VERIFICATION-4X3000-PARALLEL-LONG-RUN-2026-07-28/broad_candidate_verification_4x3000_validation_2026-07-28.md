# Validation report

Generated coordinator invariants passed for the partial/resume-ready package. Three valid lanes reconcile to 6,430 merged rows; all 2,144 sandbox-denied lane 004 rows are quarantined and contribute zero verification/dashboard outcomes.

Validation commands:

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_parallel_live_scout.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_scout_dry_run_prep.py`: passed, including the zero-unsafe-write rerun check.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000.py`: passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 6,919 actually scout-covered municipalities, and 13,041 candidate rows.
- `npm --prefix docs/dashboard run build`: passed. Vite emitted its existing advisory that the main JavaScript chunk exceeds 500 kB; the build completed successfully.
- `.venv/bin/python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py`: passed, 60 tests and 0 failures.
- `git diff --check`: passed.
