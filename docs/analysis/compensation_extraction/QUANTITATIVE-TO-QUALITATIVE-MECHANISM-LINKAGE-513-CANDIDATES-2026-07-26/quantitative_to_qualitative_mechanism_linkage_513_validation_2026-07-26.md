# Quantitative-to-qualitative mechanism linkage validation — 2026-07-26

Internal deterministic scope, hash, quarantine, strict-linkage, raw-value, and downstream-boundary gates passed.

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_quantitative_to_qualitative_mechanism_linkage_513.py scripts/test_quantitative_to_qualitative_mechanism_linkage_513.py` — passed.
- `.venv/bin/python scripts/test_quantitative_direct_text_claim_triage_862.py` — 14 passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_rating_summary_173.py` — 16 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69 passed.
- `.venv/bin/python scripts/test_quantitative_to_qualitative_mechanism_linkage_513.py` — 15 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; dashboard data rebuilt.
- `npm --prefix docs/dashboard run build` — passed; Vite production build completed.
- `.venv/bin/python scripts/validate.py` — passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `.venv/bin/python ingest/audit_coverage.py` — passed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units reported without changing data.
- `.venv/bin/python scripts/run_quantitative_to_qualitative_mechanism_linkage_513.py --resume` — passed with `completed_outputs_valid_zero_writes` for 513 quantitative and 609 qualitative scope rows.
- `git diff --check` — passed.

## Boundary and integrity results

- Quantitative input scope reconciles to exactly 513 candidates; no noncandidate row entered linkage.
- Qualitative input scope reconciles to 609 supported, valid bounded mechanism records; all 28 targeted quarantines and all 7 legacy exclusions remain excluded.
- Raw quantitative value strings were preserved byte-for-byte; normalization, imputation, annualization, wage-gap calculation, outcome comparison, regression, and treatment-effect counters remain zero.
- No URL, download, PDF/page, retained-source, full-extracted-text, OCR, rendering, hosted-search, model/API, ingestion, or codification operation occurred.
- Global analysis readiness remains false.
- The dashboard reports `quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready_global_analysis_closed`.
