# Rating-summary validation — 2026-07-28

Internal deterministic invariants pass. Exactly 16,947 valid ratings enter summary statistics; all 312 quarantines are excluded; the primary bucket union and dashboard assignments reconcile.

## Required command results

- `python -m py_compile scripts/build_dashboard_data.py`: passed.
- `scripts/test_combined_broad_exact_span_rating_17259.py`: 25/25 passed.
- `scripts/test_combined_broad_span_extraction_3815.py`: passed (3,815 source artifacts; 17,259 candidates).
- `scripts/test_combined_broad_text_extraction_4051.py`: passed.
- `scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed after allowing the completed rating-summary decision as a valid descendant state.
- `scripts/test_combined_broad_exact_span_rating_summary_16947.py`: 35/35 passed, including a deterministic idempotent rebuild.
- `scripts/build_dashboard_data.py`: passed; 6,919 total scout-covered municipalities remain the sole map metric.
- `npm --prefix docs/dashboard run build`: passed; one existing chunk-size advisory only.
- `scripts/validate.py`: passed.
- `ingest/test_pipeline.py`: 60/60 passed.
- Git artifact checks: no retained-source or full-extracted-text paths are tracked; no raw prompt/response artifact is tracked.
- No model/API calls, source/full-text access, rerating, extraction, ingestion, codification, normalization, comparison, statistical work, or causal analysis occurred.
- `git diff --check`: passed at pre-commit closeout.
