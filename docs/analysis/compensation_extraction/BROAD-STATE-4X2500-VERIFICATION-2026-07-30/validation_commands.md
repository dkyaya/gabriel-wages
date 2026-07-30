# Validation commands

All commands passed on 2026-07-30.

- `python scripts/run_broad_state_4x2500_verification.py --validate` — 20/20 verification, phase-boundary, dashboard-map, and global-readiness gates passed; 5,768 merged rows and 3,950 source-review-ready rows reconciled.
- `python scripts/test_broad_state_4x2500_verification.py` — queue lock, exact lane distribution, stable priority interleaving, and locator canonicalization regression checks passed.
- `python scripts/validate.py` — repository data schema validation passed.
- `python ingest/test_pipeline.py` — 60 tests passed, 0 failed.
- `python -m py_compile scripts/run_broad_state_4x2500_verification.py scripts/test_broad_state_4x2500_verification.py scripts/build_broad_state_4x2500_verification_relay.py scripts/build_dashboard_data.py` — passed.
- `python scripts/build_dashboard_data.py` — passed with 16,887 scout-covered municipalities and 23,018 candidate rows; the map remains total scout coverage only.
- `npm --prefix docs/dashboard run build` — production dashboard build passed.
- `git diff --check` — passed.

The staged-file/large-file audit is recorded separately in `staged_file_audit.json` immediately before commit.
