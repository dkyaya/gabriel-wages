# Four-lane staggered live validation — 2026-07-25

Initial generation validation passed fail-closed: 2,000 locked targets, 4/4 queue hashes, 4/4 target-ID hashes, and credential presence all passed. The fixed-start/no-overlap scheduling contract failed before any hosted request.

## Command results

- New staggered-live preflight suite: **62/62 passed**.
- Required predecessor suites: **208/208 passed** (`77` dry-prep, `62` provisional-claim review, `69` claim-oriented phase close).
- Combined focused suites: **270/270 passed**.
- Python compilation for the dashboard builder, preflight runner, and focused suite: passed.
- Dashboard data build: passed.
- Dashboard production build: passed with only the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion tests: **60/60 passed**; tests only, no ingestion run.
- Coverage audit: passed (`28` healthy matched pairs, `6` unmatched safety units, `2` exploratory adjacent matches).
- Idempotent `--resume`: passed with zero writes, zero live calls, and unchanged required-output hashes.
- Credential/secret-pattern scan: passed; no secret value was printed or persisted.
- `git diff --check`: passed.

## Bugs found and fixed

The first local preflight implementation appended a terminal newline when recomputing the target-ID-set hashes, while the immutable preparation lock contract hashes the sorted IDs without a terminal newline. The validator was corrected, the uncommitted package was regenerated, and regression coverage now asserts byte-for-byte compatibility with the lock algorithm. All eight queue/ID hash checks now pass; the scheduling conflict is the sole failed preflight gate.
