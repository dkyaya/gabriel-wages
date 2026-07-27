# Quantitative direct-text claim triage validation — 2026-07-26

Decision: `quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready`.

Internal deterministic gates passed for exactly 862 preserved rows. The locked queue has 862 unique evidence IDs and a one-to-one lineage join; all raw value strings match the immutable source manifest. The 28 targeted exact-span quarantines are disjoint from this lane. The 326 rows without complete cycle lineage are excluded from mechanism-linkage candidacy and no missing value, unit, cycle, or rate was imputed.

Required command results:

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_quantitative_direct_text_claim_triage_862.py scripts/test_quantitative_direct_text_claim_triage_862.py` — passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_summary_173.py` — 16 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_201.py` — 22 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69 passed.
- `.venv/bin/python scripts/test_quantitative_direct_text_claim_triage_862.py` — 14 passed.
- `.venv/bin/python scripts/run_quantitative_direct_text_claim_triage_862.py --resume` — completed outputs valid; zero writes.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; dashboard data regenerated.
- `npm --prefix docs/dashboard run build` — passed; Vite production build completed (non-blocking chunk-size advisory only).
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `.venv/bin/python ingest/audit_coverage.py` — passed; 28 healthy matched pairs (10 exact, 18 overlap), 2 exploratory adjacent matches, and 6 unmatched safety units.
- `git diff --check` — passed.

Forbidden-action audit: zero URL opens, downloads, PDF/page accesses, retained-file accesses, full-extracted-text accesses, OCR runs, PDF rendering runs, GABRIEL/API/model calls, ingestion runs, codification runs, wage-gap calculations, regressions, treatment-effect estimates, population-prevalence claims, national claims, final causal claims, imputations, destructive normalizations, or annualizations. Global analysis readiness remains false.
