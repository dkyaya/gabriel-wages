# Schema-repair validation

- No-write dry run: passed; writes before output creation: 0.
- Package SHA-256 checks: 5/5 passed before and after repair.
- New rollback-safe output directory under `docs/analysis`: passed.
- Immutable package ledgers modified: no.
- Durable bridge inputs modified: no.
- Non-base duplicate source columns: repaired by ordinal position; zero disagreements.
- One-to-one identity/raw-hash bridge: 1826/1,826.
- Active mixed joins: 371/371 valid.
- Qualitative coded view created: no; navigation only.
- Two unresolved groups / five members quarantined: yes.
- Non-base lane separate and reference lane control-only: yes.
- OCR-later documents included: no.
- Analysis dataset, ingestion input, or codified output created: no.
- Analysis readiness remains false.

## Executed validation commands

- `.venv/bin/python -m py_compile scripts/repair_compensation_evidence_final_provisional_schemas.py scripts/test_compensation_evidence_final_provisional_schema_repair.py scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/test_compensation_evidence_final_provisional_schema_repair.py`: 13/13 passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows represented.
- `npm --prefix docs/dashboard run build`: passed; Vite emitted only its existing non-blocking chunk-size warning.
- `.venv/bin/python scripts/validate.py`: passed; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py`: 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py`: passed; 64 contracts, 19 cities, 28 healthy matched pairs (10 exact and 18 overlapping), 2 exploratory adjacent matches, and 6 unmatched safety units.
- `git diff --check`: passed.

## Forbidden-stage verification

No GABRIEL/API, extraction, document selection, URL opening, hosted search, download, redownload, PDF opening, OCR, source review, verification, ingestion, codification, analysis-dataset creation, wage-gap calculation, regression, or causal analysis occurred. OCR-needed count in the 1,826-row bridge is zero; all rows retain `present` or `partial` parse-text status.
