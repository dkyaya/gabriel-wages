# Dashboard declutter/map correction and Tier C text/span validation — 2026-07-27

Internal invariants passed for the immutable 378-file scope. PDF/HTML counts reconcile to 317/61; all text outcomes reconcile to 378; only `extracted_ok` task-local artifacts entered deterministic span extraction; all exact span offsets and hashes passed. The map contract is total scout coverage only, the map date is visible, the dashboard-update policy is recorded, and global analysis readiness remains false. Decision: `dashboard_declutter_map_correction_tier_c_text_span_completed_rating_ready`. Required repository validation results are appended after the full suite.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_tier_c_readiness_dashboard_map_update.py`: passed.
- `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py`: 12/12 passed.
- `.venv/bin/python scripts/test_dashboard_fix_and_tier_c_source_review_download_556.py`: 26/26 passed.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`: passed, including read-only `--resume` validation.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- `npm --prefix docs/dashboard run build`: passed; production bundle generated. The size advisory was non-fatal.
- `.venv/bin/python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py`: 60 passed, 0 failed.
- `git diff --check`: passed.

No immutable input mutation, non-ready source inclusion, URL access, download, OCR, PDF rendering, model/API call, evidence rating, ingestion, codification, normalization, quantitative comparison, wage-gap calculation, regression, treatment-effect estimate, population-prevalence/national claim, final causal claim, geographic fabrication, raw prompt/response save, or durable-ledger merge occurred. Dashboard global analysis readiness remains false.
