# Targeted exact-span rating validation — 2026-07-26

Internal gates passed for exactly 201 locked positive spans. The bounded preflight passed on 7/7 representative spans across all four mechanism families. The live run produced 173 schema-valid ratings and 28 explicit quarantines, reconciling to 201/201. Every valid quote passed exact-substring validation (173/173), and all downstream and claim boundaries remain closed. Decision: `targeted_evidence_span_rating_201_completed_with_quarantine`.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py` — passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_extraction_321.py` — 28/28 passed.
- `.venv/bin/python scripts/test_targeted_text_layer_extraction_321.py` — 26/26 passed.
- `.venv/bin/python scripts/test_targeted_pdf_text_layer_readiness_387.py` — 25/25 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_201.py` — 22/22 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69/69 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed.
- `npm --prefix docs/dashboard run build` — passed, with only the existing bundle-size warning.
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform to `docs/schema.md`.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py` — passed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units.
- `git diff --check` — passed.

## Rating and boundary checks

- Preflight: 7/7 schema-valid and exact-quote-valid rows; four mechanism families covered.
- Valid ratings: 173.
- Quarantine: 28 (`quote_not_exact_span_substring`: 27; `forbidden_final_claim_language`: 1).
- GABRIEL/API/model calls: 259 total bounded calls, including preflight, live requests, and bounded retries.
- Raw prompts saved: 0; raw responses saved: 0.
- URL opens, downloads, PDF/page access, OCR, PDF rendering, ingestion, codification, wage-gap calculations, regressions, treatment-effect estimates, and final causal claims: 0.
- Global analysis readiness: false.
- Exact-span summary review is allowed next over only the 173 valid ratings, with all 28 quarantines explicitly excluded.
