# Combined broad exact-span rating validation — 2026-07-28

Internal coordinator invariants pass. Input/valid/quarantine reconciles 17,259 = 16,947 + 312. Quote/schema/forbidden-claim/artifact-completeness checks pass. Repository validation command results are appended after the required suite.

## Required command results

- `python -m py_compile scripts/build_dashboard_data.py`: passed.
- `scripts/test_combined_broad_span_extraction_3815.py`: passed (3,815 sources; 17,259 candidates).
- `scripts/test_combined_broad_text_extraction_4051.py`: passed.
- `scripts/test_retained_source_storage_history_repair.py`: passed.
- `scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed after adding the completed rating decision as an allowed descendant state.
- `scripts/test_combined_broad_exact_span_rating_17259.py`: 25/25 passed.
- `scripts/build_dashboard_data.py`: passed; current rating metrics synchronized.
- `npm --prefix docs/dashboard run build`: passed (one existing chunk-size advisory only).
- `scripts/validate.py`: passed.
- `ingest/test_pipeline.py`: 60/60 passed.
- Required-output inventory: 108/108 files present before final relay creation.
- Git artifact checks: no tracked retained-source or full-extracted-text paths; no rating output file over 50 MB.
- Raw prompt/response check: no raw prompt or raw response artifact saved.
- `git diff --check`: passed.
