# Dashboard full project-hub update notes — 2026-07-22

## Outcome

The static GitHub Pages dashboard was expanded from a source-discovery MVP into a permanent project and research-status hub. The existing geographic map, tile-grid alternate, state detail panel, hash routing, and printable state report remain in place.

Public URL:

<https://dkyaya.github.io/gabriel-wages/>

The dashboard continues to use committed local data only. No scout, API/model call, hosted search, URL verification, source ingestion, or codification occurred, and no source-discovery accounting input was edited.

## Major sections added or elevated

1. **Overview** — frozen national metrics, checkpoint label, prominent source-discovery caveat, and collected/current/forthcoming orientation.
2. **Coverage and geography** — preserved geographic and tile-grid map behavior with state detail.
3. **Scouting priority tiers** — Tier 1–Tier 5 remaining pools, separate retry lane, state high-priority workload, and operational-heuristic caveat.
4. **Scout operations** — four-wave runtime and throughput trends plus current preflight, compact-prompt, hints, adaptive pacing, and resume controls.
5. **Candidate queue** — funnel, unit/workload cards, state table, and explicit municipality-versus-row distinction.
6. **Verification pipeline** — candidate lead → verified source → ingested source → codified evidence → analysis-ready evidence, with a planned 50–100-row pilot.
7. **State yield and learning** — ten-state leaderboard, sample-confidence labels, minimum-sample warning, and 300–600-scout refresh rule.
8. **Reports library** — the current PI report as a primary hub section and a reserved future verification-report card.
9. **Methodology and definitions** — concise definitions for every discovery/evidence stage.
10. **Next steps** — PI decision among a verification pilot, further Tier 1 breadth, and a separate retry lane.

## Navigation and responsive behavior

`ProjectNavigation.jsx` provides sticky section navigation without consuming the state hash route. Buttons use `scrollIntoView`, leaving `#/state/<CODE>` and `#/state/<CODE>/report` intact. At 700 pixels and below, navigation collapses into a two-column menu; at 430 pixels it becomes one column. Long dashboard grids collapse progressively across 1100-, 1000-, 700-, and 430-pixel breakpoints.

The frontend production build passed. Browser-control discovery was unavailable in this environment, so the final QA used the successful Vite transform/build, compiled-bundle text assertions, JSON/schema checks, PDF asset bundling, and source-level responsive/accessibility review rather than an interactive browser screenshot pass.

## Data files used

The hub consumes the existing committed data layer:

- `state_summary.json`
- `candidate_queue_summary.json`
- `coverage_funnel.json`
- `analysis_readiness.json`
- `priority_summary.json`
- `state_priority_summary.json`
- `top_priority_targets.json`
- `scout_operations_summary.json`
- `scout_yield_by_state.json`
- `scout_runtime_trends.json`

It also consumes the new validated report-library layer:

- source: `docs/dashboard/reports/reports_index.json`
- generated data copy: `docs/dashboard/data/reports_index.json`

`scripts/build_dashboard_data.py` now validates required report fields, metrics snapshots, unique IDs, source/PDF existence, and the rule that exactly one report is current.

## PI report publication

The PI report was rebuilt with the project’s July 10 academic report language and is visible in:

- the header;
- the Reports Library main section; and
- the footer.

Public dashboard-relative path:

`reports/pi_progress_report_source_discovery_2026-07-22.pdf`

Vite bundles the PDF as a managed asset. The production build emitted the report successfully.

## Current frozen checkpoint

- Municipality/township universe: 35,589
- Scout-covered municipalities: 794
- Candidate-positive municipalities: 612
- Parseable-empty municipalities: 182
- Failure-only municipalities: 20
- URL-bearing candidate rows: 1,602
- Future-scout eligible: 34,789
- Tier 1 eligible: 1,227
- Tier 2 eligible: 3,478

Candidate rows remain unverified source leads. Tiers remain operational work-order heuristics. The dashboard does not report verified wage findings, bargaining-mechanism effects, or causal estimates.

## Deferred enhancements

Safe later improvements include automated accessibility regression tests, municipality-level exploration after privacy/provenance review, a structured project-wide verification ledger, and report-library filters after multiple reports exist. These are deliberately deferred until the underlying validated inputs exist.
