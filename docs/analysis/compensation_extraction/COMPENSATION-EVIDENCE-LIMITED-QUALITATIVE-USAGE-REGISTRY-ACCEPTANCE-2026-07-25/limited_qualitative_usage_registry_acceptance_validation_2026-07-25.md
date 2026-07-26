# Limited qualitative usage registry-acceptance validation

- Immutable registry-review inputs verified: 14.
- Dashboard baseline contracts signed: 2.
- Candidate ID-set, layer, and schema SHA-256 checks: passed.
- Registered scope: 643 accepted rows; zero excluded-lane contamination.
- Strict primary manifest: 56 rows and non-analytic.
- Evidence rows and analysis outputs created: zero.
- Global/full readiness and analysis-facing promotion: false.

## Executed validation

- Python compilation: passed for the registry-acceptance runner, its focused test suite, and the dashboard builder.
- Registry-acceptance focused suite: 73/73 passed.
- Nine predecessor suites: 488/488 passed.
- Combined focused suites: 561/561 passed.
- Dashboard data build: passed.
- Dashboard production build: passed; the existing non-fatal Vite chunk-size warning remains.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion pipeline tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed; 28 healthy matches (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes.
- Partial-output completion validation: passed fail-closed.

## Hardening finding

The first full predecessor pass found that six older materialized-output tests and the registry-review dashboard validator rejected the new descendant acceptance phase because their explicit closed-phase allowlists ended at registry review. The allowlists now include only the exact registry-acceptance phase and overall status, while all readiness, promotion, contamination, scope, and non-analysis assertions remain unchanged. A registry-review regression test covers the descendant acceptance state.
