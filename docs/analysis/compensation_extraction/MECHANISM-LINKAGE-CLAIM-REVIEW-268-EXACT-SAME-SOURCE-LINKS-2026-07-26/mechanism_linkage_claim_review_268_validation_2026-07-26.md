# Mechanism-linkage claim-review validation — 2026-07-26

Internal deterministic hash, exact-source scope, 268/208/90 reconciliation, exclusion, raw-value, claim-boundary, taxonomy, multiplicity, and downstream-closure gates passed.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_mechanism_linkage_claim_review_268.py scripts/test_mechanism_linkage_claim_review_268.py` — passed.
- `.venv/bin/python scripts/test_quantitative_to_qualitative_mechanism_linkage_513.py` — 15 passed.
- `.venv/bin/python scripts/test_quantitative_direct_text_claim_triage_862.py` — 14 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_summary_173.py` — 16 passed.
- `.venv/bin/python scripts/test_mechanism_linkage_claim_review_268.py` — 15 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; dashboard data rebuilt.
- `npm --prefix docs/dashboard run build` — passed; Vite production build completed.
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `.venv/bin/python ingest/audit_coverage.py` — passed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units reported without changing data.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69 passed.
- Dashboard compatibility regressions — 25 PDF-readiness, 25 candidate-review, 24 source-review/download, 25 verification, and 26 text-extraction tests passed.
- `.venv/bin/python scripts/run_mechanism_linkage_claim_review_268.py --resume` — passed with `completed_outputs_valid_zero_writes` for 268 pairs.
- `git diff --check` — passed.

## Boundary and integrity results

- The locked scope contains exactly 268 `linked` / `exact_same_source` pairs covering 208 quantitative rows and 90 qualitative records across 72 shared source lineages.
- No no-link, weak-context, unmatched, quarantined, unsupported, invalid, or noncandidate row entered the claim-review scope.
- Raw quantitative strings, units, readiness labels, qualitative claim boundaries, linkage reasons, and source/pair multiplicities were preserved exactly.
- Claim types reconcile to 15 direct-text co-location claims, 80 documentary mechanism-value scaffolds, 32 provisional mechanism linkages, 141 insufficient-for-claim records, and 0 not-allowed records.
- No normalization, imputation, annualization, outcome comparison, wage-gap calculation, regression, treatment-effect estimate, population/national claim, or final causal claim occurred.
- No URL, download, PDF/page, retained-source, full-extracted-text, OCR, rendering, hosted-search, model/API, ingestion, or codification operation occurred.
- Global analysis readiness remains false.
- The dashboard reports `mechanism_linkage_claim_review_268_completed_claim_memo_allowed_global_analysis_closed`.
