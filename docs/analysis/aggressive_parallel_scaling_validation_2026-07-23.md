# Aggressive Parallel Scaling Validation — 2026-07-23

## Result

**PASS.** All implementation, plan, dashboard, schema, ingestion, coverage,
protected-path, and diff checks completed with the system `python` shim. No virtual
environment fallback or dependency installation was needed.

## Requested commands

- Eight requested `python -m py_compile` invocations passed:
  planner, auditor, parallel tests, scout runner, direct-SDK tests, prompt tests,
  dashboard builder, and yield builder.
- `python scripts/test_parallel_scout_lanes.py` passed seven synthetic groups,
  covering:
  - three completed disjoint lanes → `merge_all_lanes`;
  - duplicate input/completed IDs → fail closed;
  - two complete plus one zero-parseable → completed-only with user approval;
  - one complete plus two partial parseable → do not merge;
  - missing and mismatched lane-local exports → do not merge;
  - three-lane throughput, outer-timeout, backoff, and step-down totals;
  - missing artifacts and zero shared accounting writes.
- `python scripts/test_gabriel_state_source_scout_direct_sdk.py` passed all mocked,
  no-network checks. The new test proves legacy serial exports remain under the
  historical analysis directory, configured lane exports are redirected, both
  copies match `parsed_candidates.csv`, and no extra shared export is created.
- `python scripts/test_gabriel_state_source_scout_prompt.py` passed 12 checks.
- Both requested planner invocations reproduced deterministic hashes and counts.
- `python scripts/build_scout_yield_learning_report.py` reproduced 51 states/DC,
  five reviewed waves/rounds, and 165.391 latest attempted rows/hour.
- `python scripts/build_dashboard_data.py` reproduced 35,589 universe rows, 1,091
  scout-covered municipalities, and 2,362 unverified queue rows.
- `python scripts/validate.py` passed: 64 contracts, zero discourse rows, 64 coverage
  rows, and three city-attribute rows.
- `python ingest/test_pipeline.py` passed 60/60.
- `python ingest/audit_coverage.py` reports 19 cities, 28 healthy pairs (10 exact,
  18 overlapping), two adjacent exploratory pairs, and six unmatched safety units.
- `git diff --check` passed.

## Plan and compatibility checks

### Round 2: 3 × 150

- Rows: 450 total; 150 per lane.
- Municipality IDs: 450 unique; overlap zero.
- Census government IDs: 450 unique/nonblank; overlap zero.
- Tier distribution: Tier 1 = 450.
- Current ordinary eligibility, no retry/failure-only/covered/canonical rows: PASS.
- Five-hint sets: 450/450.
- Lane hashes:
  - Lane 1: `320f4915a1aa487e791f67a31826572ac275edf5d4b87ecb99eec4b26279d86a`
  - Lane 2: `e06f9706d69bce72cabac6f57c8581d16651d0b00ecec5752787edda5fc5500a`
  - Lane 3: `501e36ff504ec2d5e3a1126eb1315db6fb31bbe5852c2be2590794661dd50665`
- Live previews contain compact mode, hints, adaptive controls, per-lane cost logs,
  and per-lane candidate export directories.
- Start offsets: 0, 240, and 480 seconds.

### Aggressive feasibility: 3 × 300

- Rows: 900 total; 300 per lane.
- Municipality IDs: 900 unique; overlap zero.
- Census government IDs: 900 unique/nonblank; overlap zero.
- Tier distribution: Tier 1 = 900.
- Current ordinary eligibility, no retry/failure-only/covered/canonical rows: PASS.
- Five-hint sets: 900/900.
- Lane hashes:
  - Lane 1: `2a19781c3cc6d1a10c03174b494f60c8df6c1414261e509e948977b620e040e9`
  - Lane 2: `ed36a0876216fe7084bc54b1008c4b176ffe6b3953d904fe9d1cef5ff43b9ec0`
  - Lane 3: `c13d587a3d70aa19f4ae27fe5a84890e9a5420242dd2199413c7c0990c7942c2`
- Start offsets: 0, 480, and 960 seconds.
- This is plan-only feasibility evidence, not live authorization.

A separate temporary offline invocation without `--profile`, `--num-lanes`, or
`--rows-per-lane` reproduced the legacy default of two lanes × 150, confirming the
planner’s existing two-lane behavior remains available.

## Dashboard and frontend

- Every `docs/dashboard/data/*.json` file parses.
- `parallel_scout_status.json` reads current coverage from canonical state
  accounting: 1,091/2,000 with 909 remaining.
- It reports the next test as 3 × 150, aggressive 3 × 250–300 as conditional,
  serial post-audit accounting, and lane-local candidate exports.
- Its caveat explicitly states that no three-lane live scout has run.
- `npm run build` in `docs/dashboard` passed with Vite 8.1.5: 42 modules
  transformed and the production bundle emitted successfully.
- Dashboard text does not claim wage gaps exist.

## Boundaries and protected data

- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` have no diff.
- The national candidate queue and national municipality/state coverage files have
  no diff. Dashboard/yield outputs were rebuilt only from existing committed
  accounting.
- No source was promoted, verified, extracted, ingested, codified, or used for a
  wage-gap or causal claim.
- No live scout, worker scout, real API/model/hosted-search call, diagnostic, smoke
  preflight, URL access, regression, remote inspection/action, or push occurred.
- The unrelated untracked root `package-lock.json` remains unchanged and excluded.
