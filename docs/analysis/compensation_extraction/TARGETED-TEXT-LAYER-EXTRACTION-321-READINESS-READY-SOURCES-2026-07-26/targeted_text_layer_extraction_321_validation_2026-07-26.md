# Targeted text-layer extraction validation — 2026-07-26

Internal extraction invariants passed for the immutable 321-file scope. PDF/HTML counts reconciled to 289/32, all outcomes reconciled to 321, all extracted artifact hashes and paths passed, and all 108 readiness/source-review exclusions remained outside the queue. Decision: `targeted_text_layer_extraction_321_completed_evidence_extraction_ready`.

## Required validation results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_targeted_text_layer_extraction_321.py`: passed.
- `.venv/bin/python scripts/test_targeted_text_layer_extraction_321.py`: 26/26 passed.
- `.venv/bin/python scripts/test_targeted_pdf_text_layer_readiness_387.py`: 25/25 passed.
- `.venv/bin/python scripts/test_targeted_source_review_download_429.py`: 24/24 passed.
- `.venv/bin/python scripts/test_targeted_source_verification_tier_a_b.py`: 25/25 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py`: 69/69 passed after the downstream dashboard phase was added to the closed-readiness allowlist.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; dashboard data rebuilt.
- `npm --prefix docs/dashboard run build`: passed; the existing Vite chunk-size advisory remained non-blocking.
- `.venv/bin/python scripts/validate.py`: passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py`: 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py`: passed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units. No durable coverage row changed.
- `git diff --check`: passed.

## Integrity and boundary checks

- Immutable readiness/source-review input paths have no tracked diff.
- The extraction output reconciles to 321 `extracted_ok` rows, 321 saved artifacts, 29,926,541 characters, and 30,051,405 UTF-8 bytes.
- Output-tree SHA-256 before and after `--resume`: `8994c6e7fe1bbb38bfa888525f33eb9c7fefd6cdcc73fe20b68a5fe623d05aee`; resume reported zero writes.
- Task-output secret-pattern scan returned no matching file.
- URL opens, downloads, OCR, PDF rendering, model/API calls, ratings, ingestion, codification, statistics, wage-gap calculations, regressions, treatment effects, final causal claims, and durable-ledger merges: zero.
- Dashboard phase is `targeted_text_layer_extraction_321_completed_evidence_extraction_ready`; overall status is `targeted_text_layer_extraction_321_completed_evidence_extraction_ready_global_analysis_closed`.
