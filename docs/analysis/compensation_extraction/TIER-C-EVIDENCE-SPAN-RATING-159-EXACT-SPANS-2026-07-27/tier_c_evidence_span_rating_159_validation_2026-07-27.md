# Tier C exact-span rating validation — 2026-07-27

Internal gates passed. Valid plus quarantine reconciles to 159; every valid quote is an exact span substring; model input and downstream boundaries remain closed. Decision: `tier_c_evidence_span_rating_159_completed_with_quarantine`. Repository command results are appended after the required suite.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_tier_c_evidence_span_rating_159.py` — passed.
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` — passed.
- `.venv/bin/python scripts/test_tier_c_readiness_dashboard_map_update.py` — passed.
- `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py` — 12/12 passed.
- `.venv/bin/python scripts/test_tier_c_evidence_span_rating_159.py` — passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows rebuilt.
- `npm --prefix docs/dashboard run build` — passed; Vite built the production bundle. Its existing chunk-size advisory is non-fatal.
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `git diff --check` — passed.

## Rating and safety reconciliation

- Locked rating queue: 159.
- Valid ratings: 140.
- Quarantine: 19.
- Valid plus quarantine: 159.
- Representative preflight: 8/8 valid after one bounded repair call for a persistent exact-quote failure.
- Total GABRIEL/API/model request attempts: 199, comprising 12 preflight attempts and 187 live attempts.
- Raw prompts saved: 0; raw responses saved: 0.
- URL opens, downloads, PDF/page accesses, retained-source accesses, full-text accesses, OCR runs, and PDF rendering runs: 0.
- Ingestion, codification, wage-gap, regression, treatment-effect, national/population-prevalence, and final-causal work: 0.
- Dashboard map filter: total scout coverage only.
- Dashboard map data date: 2026-07-27.
- Global analysis readiness: false.
