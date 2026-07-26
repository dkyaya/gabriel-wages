# Bounded qualitative span and residual metadata repair validation

- No-write dry run: passed; writes before materialization: 0.
- Immutable package SHA-256 checks: 5/5 passed.
- Current follow-up anchors and packet hashes: passed.
- Prior/current/durable inputs changed during run: no.
- Qualitative page-pointer reconciliation: 1954/1,954.
- Retained bounded page-text payload count: 0; exact literal spans accepted: 0.
- Coded qualitative analysis view created: no.
- Residual cycle scope: 571 only; exact verified repairs: 104.
- Residual non-safety scope: 535 only; controlled explicit-label repairs: 167.
- Quantitative candidate/exception files: byte-identical carry-forward (862/1,045).
- Non-base companion/reference control files: byte-identical carry-forward (4,733/345).
- Two unresolved groups/five observations: byte-identical quarantine carry-forward.
- Package ledgers, prior repair outputs, current follow-up outputs, durable ledgers, and packet manifests modified: no.
- URL, download, PDF opening, OCR, GABRIEL/API, extraction, selection, ingestion, codification, analysis dataset, wage-gap, regression, or causal work: none.
- Analysis readiness remains false.

## Executed validation commands

- `.venv/bin/python -m py_compile scripts/run_compensation_evidence_bounded_schema_repair_followup.py scripts/run_compensation_evidence_bounded_qualitative_span_residual_metadata_repair.py scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_compensation_evidence_bounded_schema_repair_followup.py`: 9/9 passed.
- `.venv/bin/python scripts/test_compensation_evidence_bounded_qualitative_span_residual_metadata_repair.py`: 7/7 passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- `npm --prefix docs/dashboard run build`: passed; Vite emitted its existing advisory that one minified JavaScript chunk exceeds 500 kB.
- `.venv/bin/python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py`: 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py`: passed; 28 healthy matched pairs (10 exact-cycle, 18 overlap-cycle), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.

## Final integrity checks

- Five quantitative/non-base/reference/conflict carry-forward files are byte-identical to their approved predecessors: passed 5/5.
- Immutable package, prior repair, current follow-up, durable routing/readiness/detection, `data/`, and `corpus/` inputs have no tracked diff: passed.
- Coded qualitative analysis candidate is absent and all 1,954 rows remain navigation-only: passed.
- Dashboard analysis-readiness status is closed and `analysis_readiness` remains false: passed.
- Secret-pattern scan over new artifacts: passed with zero matches.
- PDF/image artifact scan within the new output directory: zero files.
