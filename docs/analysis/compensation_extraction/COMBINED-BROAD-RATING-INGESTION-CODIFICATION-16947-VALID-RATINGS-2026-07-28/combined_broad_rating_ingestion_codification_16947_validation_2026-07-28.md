# Combined broad rating ingestion/codification validation

All deterministic package invariants passed: **16,947** valid ratings became durable ingested/codified records, lanes reconciled to **[4237, 4237, 4237, 4236]**, and **312** quarantines remained reference-only. Controlled schemas, layers, buckets, boxes, claim boundaries, map contract, and global-readiness=false passed. No model/API, source/full-text, extraction, OCR/rendering, normalization/comparison, statistical, prevalence, or causal operation ran.

## Command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_combined_broad_rating_ingestion_codification_16947.py scripts/test_combined_broad_rating_ingestion_codification_16947.py` — passed.
- `.venv/bin/python scripts/test_combined_broad_rating_ingestion_codification_16947.py` — 36/36 passed, including deterministic rebuild.
- `.venv/bin/python scripts/test_combined_broad_exact_span_rating_summary_16947.py` — 35/35 passed.
- `.venv/bin/python scripts/test_combined_broad_exact_span_rating_17259.py` — 25/25 passed.
- `.venv/bin/python scripts/test_combined_broad_span_extraction_3815.py` — passed for 3,815 sources and 17,259 exact candidates.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` — passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; 6,919 scout-covered municipalities and 13,041 candidate rows retained.
- `npm --prefix docs/dashboard run build` — passed; Vite emitted only its existing chunk-size advisory.
- `.venv/bin/python scripts/validate.py` — passed.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 passed.
- Git artifact-path tracking checks — zero retained-source or full-extracted-text paths tracked.
- `git diff --check` — passed.
