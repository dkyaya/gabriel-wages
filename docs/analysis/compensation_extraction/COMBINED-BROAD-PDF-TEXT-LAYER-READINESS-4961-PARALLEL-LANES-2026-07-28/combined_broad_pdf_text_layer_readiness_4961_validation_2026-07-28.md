# Validation report

Coordinator reconciliation passed: 4,961 unique locked identities, exact lane sizes, identical master/union identities, controlled statuses, and all path/size/SHA-256 checks. The predecessor retained ledgers were not mutated.

All required commands exited 0 on 2026-07-28:

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`
- `.venv/bin/python scripts/test_combined_broad_source_review_download_5589.py`
- `.venv/bin/python scripts/test_combined_broad_candidate_review.py`
- `.venv/bin/python scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py`
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`
- `.venv/bin/python scripts/test_combined_broad_pdf_text_layer_readiness_4961.py`
- `.venv/bin/python scripts/build_dashboard_data.py`
- `npm --prefix docs/dashboard run build`
- `.venv/bin/python scripts/validate.py`
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed
- `git diff --check`

The first run of the historical Tier C dashboard regression test detected that refreshed overview prose had dropped its exact archival sentence. The sentence was restored without changing current readiness metrics or map scope, and the test then passed. No source, readiness classification, or immutable predecessor ledger was changed by that repair.

Forbidden-action counters reconcile to zero: source-review reruns, redownloads, durable text/table/span extraction, OCR, PDF rendering, evidence rating/model/API calls, ingestion, codification, quantitative normalization/comparison, wage-gap/regression/treatment-effect work, population-prevalence claims, and final causal claims. The dashboard map remains total scout coverage only and global analysis readiness remains false.
