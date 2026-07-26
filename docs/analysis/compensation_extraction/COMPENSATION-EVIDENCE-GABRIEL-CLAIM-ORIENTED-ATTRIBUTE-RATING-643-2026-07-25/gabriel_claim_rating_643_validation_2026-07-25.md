# GABRIEL claim-rating validation — 2026-07-25

- Input eligibility and 643-row count: passed.
- Authorized candidate ID-set hash: `0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b`; passed.
- Preflight: passed (8/8 schema-valid and exact-quote valid).
- Live valid ratings: 608.
- Live quarantine: 35.
- Valid + quarantine reconciliation: 643/643; passed.
- Positive exact-substring quote checks: 691/691; passed.
- Raw prompt/response persistence: zero; passed.
- Global analysis readiness: false; passed.
- Cross-row substantive statistics, wage gaps, regressions, and final causal claims: not performed.

## Validation commands

- Python compile for the runner, focused tests, and dashboard builder: passed.
- New GABRIEL claim-rating suite: 69/69 passed.
- Claim-oriented phase-close predecessor suite: 69/69 passed.
- Registry-acceptance predecessor suite: 73/73 passed.
- Pipeline-hardening predecessor suite: 48/48 passed.
- Combined focused suites: 259/259 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed.
- Completed-output `--resume`: passed with zero writes and no API calls.
- `git diff --check`: passed.
- Immutable upstream/package/durable-ledger changed-path check: zero violations.
