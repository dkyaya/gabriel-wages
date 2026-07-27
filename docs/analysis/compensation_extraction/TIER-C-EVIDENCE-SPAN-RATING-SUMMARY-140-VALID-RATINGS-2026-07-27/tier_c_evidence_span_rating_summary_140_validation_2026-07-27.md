# Tier C evidence-span rating summary validation — 2026-07-27

Internal deterministic gates passed for exactly 140 valid ratings with 19 quarantines explicitly excluded. The 140 valid and 19 quarantined rows reconcile to the 159-row predecessor scope, with no quarantined rating entering any valid-summary statistic.

## Required command results

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_tier_c_evidence_span_rating_summary_140.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_evidence_span_rating_summary_140.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_evidence_span_rating_159.py` | PASS |
| `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_readiness_dashboard_map_update.py` | PASS |
| `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py` | PASS, 12/12 checks |
| `.venv/bin/python scripts/build_dashboard_data.py` | PASS; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows |
| `npm --prefix docs/dashboard run build` | PASS; Vite production bundle built successfully (existing non-fatal chunk-size advisory only) |
| `.venv/bin/python scripts/validate.py` | PASS; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform to `docs/schema.md` |
| `.venv/bin/python ingest/test_pipeline.py` | PASS; 60 passed, 0 failed |
| `git diff --check` | PASS |

## Summary invariants

- Valid summary ratings: 140.
- Quarantined ratings excluded: 19.
- Reconciled predecessor scope: 159.
- Model/API calls during summary review: 0.
- Rerating operations: 0.
- URL, download, PDF/page, retained-source, and full-extracted-text accesses: 0.
- OCR and PDF rendering operations: 0.
- Ingestion and codification operations: 0.
- Wage-gap, regression, treatment-effect, national, population-prevalence, and final-causal work: 0.
- Dashboard map filter remains total scout coverage only.
- Dashboard global analysis readiness remains `false`.
