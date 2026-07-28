# Validation report

All required validation commands passed on 2026-07-28.

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_parallel_live_scout.py`: passed.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed.
- `.venv/bin/python scripts/test_combined_broad_candidate_review.py`: passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 6,919 scout-covered municipalities, and 13,041 candidate rows.
- `npm --prefix docs/dashboard run build`: passed; Vite emitted only the existing non-fatal chunk-size advisory.
- `.venv/bin/python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py`: passed, 60 tests and 0 failures.
- `git diff --check`: passed.

Candidate-review invariants also passed: 9,065 reviewed rows reconcile to 7,642 broad-scout candidates plus 1,423 supplementary verification rows; 5,589 source-review-ready rows contain only reachable or reused-prior-verified statuses; all four local lanes are complete; every reviewed row remains not downloaded, not source-reviewed, not extracted, not rated, not ingested, not codified, non-causal, and not globally analysis-ready. The map remains total scout coverage only.
