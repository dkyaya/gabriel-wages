# Targeted exact-span rating summary validation — 2026-07-26

Internal deterministic gates passed for exactly 173 valid ratings with 28 quarantines preserved as exclusions. The valid and excluded sets are disjoint and reconcile to 201. All input hashes are pinned; no source document, retained file, full extracted-text artifact, URL, PDF, page, model, or network dependency is present in the runner.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py` — passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_201.py` — 22/22 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_extraction_321.py` — 28/28 passed.
- `.venv/bin/python scripts/test_targeted_text_layer_extraction_321.py` — 26/26 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_summary_173.py` — 16/16 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69/69 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed.
- `npm --prefix docs/dashboard run build` — passed, with only the existing bundle-size advisory.
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform to `docs/schema.md`.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py` — passed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units.
- Additional dashboard-regression suites — source review 24/24, source verification 25/25, candidate review 25/25, and PDF readiness 25/25 passed.
- `git diff --check` — passed.

## Boundary checks

- Valid ratings summarized: 173.
- Quarantined ratings excluded: 28.
- Valid plus excluded reconciliation: 201/201.
- GABRIEL/API/model calls: 0.
- URL opens, downloads, PDF/page access, retained-file access, full extracted-text access, OCR, rendering, ingestion, and codification: 0.
- Wage-gap calculations, regressions, treatment-effect estimates, population-prevalence claims, national claims, and final causal claims: 0.
- Raw prompts and raw responses saved: 0.
- Global analysis readiness: false.
