# Independent bounded review validation - 2026-07-25

- Exactly two unresolved groups reviewed: `pass`
- Both ambiguities preserved: `pass`
- Working-out-of-classification provenance links: `pass`
- Wasco shadow-only record repair: `pass`
- Five newly canonicalized duplicates preserved: `pass`
- Fourteen duplicate-provenance rows preserved: `pass`
- Corrected and upstream input hashes unchanged: `pass`
- Duplicate observation IDs: `pass` (0)
- Invalid bounded page pointers: `pass` (0)
- Base/non-base contamination: `pass` (0)
- Unresolved conflict rate at most 2%: `pass` (0.1049%)
- All 1,826 readable hashes covered: `pass`
- OCR-later documents untouched: `pass`
- Analysis readiness remains false: `pass`
- GABRIEL/API, new extraction, and new selection: `false`

Repository-wide command results are appended after the required validation
suite completes.

## Repository-wide validation results

- Python compilation: pass for the independent-review runner/test, prior
  targeted-conflict-QA runner, and dashboard builder.
- Independent bounded-review tests: 10 passed.
- Prior readable parse-text targeted-conflict-QA tests: 9 passed.
- Remaining-readable extraction tests: 14 passed.
- 1,000-document extraction tests: 12 passed.
- 1,000-document targeted-QA tests: 9 passed.
- 500-document extraction tests: 10 passed.
- 500-document targeted-QA tests: 8 passed.
- Automated GABRIEL Gate 1 tests: 14 passed; only mocked/dry-run transports
  executed.
- Automated GABRIEL Gate 2 tests: 10 passed; only mocked/dry-run transports
  executed.
- Automated GABRIEL Gate 3 tests: 9 passed; only mocked/dry-run transports
  executed.
- Dashboard data generation: pass for 51 states/DC, 35,589 municipalities,
  2,436 scout-covered municipalities, and 4,726 candidate rows.
- Dashboard production build: pass. The existing Vite chunk-size advisory is
  non-blocking.
- Repository schema validation: pass; 64 contracts, 0 discourse rows, 64
  coverage rows, and 3 city-attribute rows.
- Ingestion pipeline tests: 60 passed, 0 failed.
- Coverage audit: 19 cities, 28 healthy matched pairs (10 exact and 18
  overlap), 2 exploratory adjacent matches, and 6 unmatched safety units.
- `git diff --check`: pass.
