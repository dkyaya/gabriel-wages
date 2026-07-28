# Validation report

All required validation and build commands passed on 2026-07-28 after the four lane outputs were merged.

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_combined_broad_candidate_review.py`: passed.
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py`: passed.
- `.venv/bin/python scripts/test_broad_state_4x1000_parallel_live_scout.py`: passed.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed.
- `.venv/bin/python scripts/test_combined_broad_source_review_download_5589.py`: passed, including retained path/size/SHA-256 checks over all 4,961 unique retained files.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; generated 51 states/DC, 35,589 municipalities, 6,919 scout-covered municipalities, and 13,041 candidate rows.
- `npm --prefix docs/dashboard run build`: passed; Vite completed with its existing non-fatal large-chunk warning.
- `.venv/bin/python scripts/validate.py`: passed; all repository rows conform to `docs/schema.md`.
- `.venv/bin/python ingest/test_pipeline.py`: passed, 60 tests and zero failures.
- `git diff --check`: passed.

Coordinator reconciliation also passed: 5,589 locked rows equal 5,589 terminal results; lane sizes are exactly 1,397 / 1,397 / 1,397 / 1,398; 4,961 retained plus 628 excluded/deferred equals 5,589; retained files total 12,475,949,771 bytes; no partial files remain; and global analysis readiness remains false.
