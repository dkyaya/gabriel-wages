# Remaining readable parse-text extraction validation — 2026-07-25

- Exact new unique hashes: `pass` (826)
- Corrected 1,000 seed API calls: `pass` (0)
- New strict-schema cases: `pass` (826)
- Cumulative unique readable hashes: `pass` (1826)
- Packet limits: `pass`
- Invalid bounded pointers: `pass` (0)
- Duplicate observation IDs: `pass` (0)
- Base/non-base contamination: `pass` (0)
- Conflict-rate gate (<=2%): `pass` (1.9372%)
- Police/fire/non-safety coverage: `pass`
- Raw prompts/responses, full text/tables, encoded images saved: `false`

Repository-wide validation commands are recorded after the complete test suite.

## Repository-wide validation

- Python compilation for the remaining-pool runner, shared extraction runner, 1,000-case targeted-QA runner, and dashboard builder: pass.
- Remaining parse-text extraction tests: 14 / 14 pass.
- 1,000-document extraction tests: 12 / 12 pass.
- 1,000-document targeted-QA tests: 9 / 9 pass.
- 500-document extraction tests: 10 / 10 pass.
- 500-document targeted-QA tests: 8 / 8 pass.
- Automated GABRIEL Gate 1 tests: 14 / 14 pass.
- Automated GABRIEL Gate 2 tests: 10 / 10 pass.
- Automated GABRIEL Gate 3 compensation tests: 9 / 9 pass.
- Dashboard data generation: pass.
- Dashboard production build: pass (non-blocking bundle-size warning only).
- `scripts/validate.py`: pass (64 contracts, 0 discourse, 64 coverage, 3 city attributes).
- `ingest/test_pipeline.py`: 60 / 60 pass.
- `ingest/audit_coverage.py`: pass; 28 healthy matched pairs, 2 exploratory adjacent pairs, and 6 unmatched safety units.
- `git diff --check`: pass.

The focused one-case metadata contains exactly one preflight and one live row,
both for `cexrem_4a267735daf6729f5c4e4835`; no seed or stored-case resend is
present. Sensitive-value and forbidden-artifact checks are recorded in the
relay validation manifest.
