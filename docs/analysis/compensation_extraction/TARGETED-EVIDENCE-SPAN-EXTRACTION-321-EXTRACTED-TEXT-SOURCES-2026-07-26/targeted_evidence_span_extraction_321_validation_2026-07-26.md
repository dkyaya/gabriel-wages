# Targeted evidence-span extraction validation — 2026-07-26

Internal invariants passed for the immutable 321-artifact scope. PDF/HTML counts reconciled to 289/32, all source outcomes reconciled to 321, every exact span passed substring/offset/SHA validation, and all 108 preserved exclusions remained outside the queue. Decision: `targeted_evidence_span_extraction_321_completed_rating_ready`.

## Completed validation

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_targeted_evidence_span_extraction_321.py scripts/test_targeted_evidence_span_extraction_321.py` — passed.
- `.venv/bin/python scripts/test_targeted_evidence_span_extraction_321.py` — 28/28 passed, including force-majeure strike/lockout rejection, non-constraint appropriation rejection, exact offsets/hashes, candidate-only positive-span gating, and dashboard closure.
- `.venv/bin/python scripts/test_targeted_text_layer_extraction_321.py` — 26/26 passed.
- `.venv/bin/python scripts/test_targeted_pdf_text_layer_readiness_387.py` — 25/25 passed.
- `.venv/bin/python scripts/test_targeted_source_review_download_429.py` — 24/24 passed.
- `.venv/bin/python scripts/test_compensation_evidence_claim_oriented_phase_close.py` — 69/69 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; dashboard reports exact-span rating ready and global analysis closed.
- `npm --prefix docs/dashboard run build` — passed; Vite emitted only its pre-existing large-chunk advisory.
- `.venv/bin/python scripts/validate.py` — passed: 64 contracts, 0 discourse rows, 64 coverage rows, 3 city-attribute rows.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py` — passed: 28 healthy matched pairs, 2 exploratory adjacent matches, 6 unmatched safety units.
- `git diff --check` — passed.

## Integrity and idempotence

- Upstream text-extraction, readiness, and source-review input directories have no git diff.
- Completed-output tree SHA-256 before and after `--resume`: `c3d2ec126e632b9cb095e020f9d1b11b3722e95b8d9fb616bcbd78bb6d4f6423`.
- `--resume` returned `completed_outputs_valid_zero_writes`.
- URL opens, downloads, OCR, PDF rendering, model/API calls, ratings, ingestion, codification, statistics, wage-gap calculations, regressions, treatment effects, final causal claims, and durable-ledger merges: 0.
- Global analysis readiness remains false.
