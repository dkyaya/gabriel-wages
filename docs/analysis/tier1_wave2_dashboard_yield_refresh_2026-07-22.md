# Tier 1 Wave 2 dashboard and yield refresh — 2026-07-22

The deterministic state/wave yield report and dashboard JSON were refreshed after the merge-eligible accounting build. The yield layer now contains 51 state/DC rows and four reviewed 150-row waves.

Current operations totals reflected by the dashboard:

- 794 successfully scout-covered municipalities;
- 1,602 URL-bearing candidate queue rows;
- 612 candidate-positive municipalities;
- 182 parseable-empty municipalities;
- 20 failure-only municipalities;
- latest wave runtime 5,738.638 seconds;
- latest throughput 94.099 rows/hour;
- latest candidate production 205.136 parsed candidate rows/hour;
- latest density 2.209 parsed candidate rows per parseable municipality.

Updated operations files:

- `docs/dashboard/data/scout_operations_summary.json`
- `docs/dashboard/data/scout_yield_by_state.json`
- `docs/dashboard/data/scout_runtime_trends.json`
- `docs/dashboard/data/state_summary.json`
- `docs/dashboard/data/candidate_queue_summary.json`
- `docs/dashboard/data/coverage_funnel.json`
- `docs/dashboard/data/analysis_readiness.json`

The state-yield leaderboard now uses the 794-covered accounting state. Washington, Oregon, Ohio, Connecticut, Indiana, and several still-small samples improved strongly in this wave; the report continues to lower confidence for sparse states rather than treating extreme early rates as stable facts.

The frontend was not changed. Candidate counts remain unverified operational leads and carry no wage-gap or causal interpretation. Priority JSON was rebuilt again after the required priority refresh, so priority counts no longer lag this coverage update.
