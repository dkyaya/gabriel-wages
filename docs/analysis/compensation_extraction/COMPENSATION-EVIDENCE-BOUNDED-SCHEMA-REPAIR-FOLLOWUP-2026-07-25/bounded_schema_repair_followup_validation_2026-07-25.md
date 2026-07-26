# Bounded schema-repair follow-up validation

- No-write dry run: passed; writes before materialization: 0.
- Immutable package SHA-256 checks: 5/5 passed.
- Prior package/repair inputs modified: no.
- Durable bridge inputs modified: no.
- Identity bridge cardinality: 1,826/1,826 unique.
- Exact cycle bridge: 1,255 established; all other identities explicitly quarantined.
- Matched-set bridge: 188 documents across 84 exact-period groups.
- Controlled occupation bridge: 1,291 established, including 72 deterministic non-safety subclasses; 535 uncertain non-safety identities quarantined.
- Retrieval provenance: 1,826/1,826 supported by durable structured fields.
- Quantitative raw and prior normalized fields preserved: yes.
- Two unresolved groups / five observations remain quarantined: yes.
- Qualitative coded view created: no; literal spans unavailable and navigation-only retained.
- Non-base companion and reference/control separation: preserved.
- OCR-later documents included: no.
- URL, PDF, OCR, GABRIEL/API, extraction, selection, ingestion, codification, analysis dataset, wage-gap, regression, or causal work: none.
- Analysis readiness remains false.

## Command results

- `python -m py_compile` for the predecessor repair runner, follow-up runner/test, and dashboard builder: passed.
- Predecessor schema-repair focused suite: 13/13 passed.
- Follow-up focused suite: 9/9 passed.
- Dashboard data rebuild: passed for 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- Dashboard production build: passed; Vite reported only its existing large-chunk advisory.
- `scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows conform.
- `ingest/test_pipeline.py`: 60/60 passed.
- `ingest/audit_coverage.py`: passed; 28 healthy matched pairs, two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.
