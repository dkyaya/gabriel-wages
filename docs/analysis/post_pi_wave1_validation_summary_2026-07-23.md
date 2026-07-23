# Post-PI Scale-Up Wave 1 Validation Summary

Date: 2026-07-23

Final disposition: **PASS**

## Required commands

| Command | Result |
|---|---|
| `python -m py_compile scripts/build_dashboard_data.py` | PASS |
| `python -m py_compile scripts/build_scout_yield_learning_report.py` | PASS |
| `python -m py_compile scripts/gabriel_state_source_scout.py` | PASS |
| `python -m py_compile scripts/run_scout_preflight_gate.py` | PASS |
| `python -m py_compile scripts/test_gabriel_state_source_scout_prompt.py` | PASS |
| `python -m py_compile scripts/test_gabriel_state_source_scout_direct_sdk.py` | PASS |
| `python -m py_compile scripts/build_post_pi_wave1_worker_inputs.py` | PASS |
| `python scripts/build_scout_yield_learning_report.py` | PASS — 51 states/DC, four reviewed waves, latest 94.099 rows/hour |
| `python scripts/build_dashboard_data.py` | PASS — 35,589 universe, 794 covered, 1,602 candidate rows |
| `python scripts/test_gabriel_state_source_scout_prompt.py` | PASS — 12 checks; temporary offline prompt dry runs only |
| `python scripts/test_gabriel_state_source_scout_direct_sdk.py` | PASS — 21 fully mocked/no-network checks |
| `python scripts/validate.py` | PASS — 64 contracts, 0 discourse, 64 coverage rows, 3 city-attribute rows |
| `python ingest/test_pipeline.py` | PASS — 60/60 |
| `python ingest/audit_coverage.py` | PASS — 28 healthy pairs (10 exact, 18 overlap), 2 adjacent exploratory, 6 unmatched safety |
| `git diff --check` | PASS |
| `cd docs/dashboard && npm run build` | PASS — Vite 8.1.5, 41 modules transformed |

The system `python` shim was usable; `.venv/bin/python` was not required.

## Dashboard/data checks

- `docs/dashboard/data/project_phase_summary.json` exists and parses.
- It reports 794 current covered, target 2,000, 1,206 remaining, 8–9 estimated waves, 1,602 candidate rows, 612 candidate-positive municipalities, and 20 failure-only municipalities.
- The operations and runtime JSON layers contain the same checkpoint context.
- All dashboard JSON outputs parse through the successful Vite import/build.
- The frontend contains **Source Discovery Scale-Up** and **Descriptive Wage-Gap Analysis, Planned**.
- Dashboard text explicitly says that no wage-growth gaps have been calculated and regressions are deferred.
- The map, reports PDF, state GeoJSON, and existing hub build remain bundled.
- Production artifacts: `index.html` 0.56 kB; CSS 30.61 kB (6.97 kB gzip); JS 362.30 kB (75.10 kB gzip); bundled report PDF 67.81 kB; state GeoJSON 293.56 kB.

## Locked-input checks

- Top input: exactly 150 data rows; 150 unique municipality IDs; 150 unique nonblank Census IDs.
- Worker inputs: exactly 50 rows each; concatenated Worker 1→2→3 identities equal the locked top-150 order.
- Priority tier: Tier 1 150; Tier 2 0.
- Retry / failure-only / currently covered / already canonical / prior official wave: 0 / 0 / 0 / 0 / 0.
- Ordinary future-scout eligible: 150/150.
- Five deterministic search hints: 150/150.
- Worker prompt controls: all required compact, hints, adaptive sleep/backoff, exact cap, mixed-state, relay-copy, timing, identity, strict employer/unit/source, and offline/no-backend instructions present.
- Worker split: rank-sliced contiguous; state concentration remains below both severe thresholds.

SHA-256:

- Top 150: `cf3287ddc831fd268b81334180fe35e11ffe472841f0a971dff09acbf9528079`
- Worker 1: `ac1cfad98cf21b97c5845b7b06b48718383668a57ee18a605d50b089fe20b9fc`
- Worker 2: `2c45d7ceff4b619b7dfa8d65bf7ce7b7d3846f2ff8a328e76faeec24f10e80a7`
- Worker 3: `574507500387ccbfb162504086b9463811b6906f765a2066d3a7d928ae17941d`

## Protected-state checks

Git comparisons confirm no changes to:

- `data/contracts.csv`
- `data/city_coverage.csv`
- `corpus/`
- national scout candidate queue
- municipality/state coverage accounting
- national priority tiers or top-target source
- failure-retry ledger

No live scout, worker dry-run, preflight, smoke, live diagnostic, API/model/backend call, hosted search, URL access, source verification, ingestion, `gabriel.codify`, candidate promotion, wage-gap calculation, causal analysis, fetch, pull, remote inspection, push, or secret/environment-value access occurred.
