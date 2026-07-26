# GABRIEL claim-rating quarantine-repair validation — 2026-07-25

- Original valid ratings unchanged: 608/608; passed by canonical row hash.
- Repair input scope: 35/35 explicit quarantine IDs; passed.
- Newly repaired ratings: 28.
- Remaining quarantine: 7.
- Total valid plus quarantine: 643/643; passed.
- Positive exact-substring quote checks: 722/722; passed.
- Taxonomy/schema: unchanged v1.1 with 14 attributes; passed.
- Raw prompt/response persistence: zero; passed.
- Cross-row statistics, wage effects, wage gaps, regressions, and final causal claims: not performed.
- Global analysis readiness: false; passed.

## Validation commands

- Python compilation for the repair runner, focused tests, dashboard builder, and descendant validators: passed.
- New quarantine-repair suite: 64/64 passed.
- Predecessor 643-row rating suite: 69/69 passed.
- Claim-oriented phase-close predecessor suite: 69/69 passed.
- Pipeline-hardening predecessor suite: 48/48 passed.
- Combined focused suites: 250/250 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed.
- Completed-output idempotent `--resume`: passed with zero writes and zero API calls.
- `git diff --check`: passed.
- Immutable upstream/package/durable-ledger changed-path check: zero violations.
