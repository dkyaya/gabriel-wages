# Dashboard Scout-Operations Handoff — 2026-07-22

The dashboard builder now publishes three additional static, same-origin JSON files without changing the React frontend:

- `docs/dashboard/data/scout_operations_summary.json`: current discovery totals, latest wave runtime/throughput/density, timeout count, strengthened-preflight recommendation, and priority-refresh cadence.
- `docs/dashboard/data/scout_yield_by_state.json`: all 50 states plus DC, sample confidence, candidate-positive rate, candidate rows per covered municipality, empty/failure rates, recommendations, and a leaderboard restricted to states with at least 10 successful scouts.
- `docs/dashboard/data/scout_runtime_trends.json`: Wave 1, Wave 2, and Tier 1 runtime, rows/hour, candidates/hour, candidate density, failure count, and fixed sleep setting.

Recommended future UI additions are a compact operations panel, a runtime/yield trend chart, and a state-yield table whose default filter excludes low-confidence samples. A map metric may show candidate density only with a visible sample-size/confidence companion; it must not imply verified source abundance.

All candidate rows remain unverified scout leads. State yield measures discovery behavior, not contract validity, employer/unit match, matched cycles, wage gaps, unionization, or causal mechanisms. Priority counts may lag discovery accounting until the unchanged priority-tier builder is intentionally rerun after the documented 300–600-success checkpoint.

No frontend or deployment code was changed in this task.
