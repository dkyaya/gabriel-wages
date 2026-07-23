# Parallel Round 1 Dashboard, Yield, and Checkpoint Refresh — 2026-07-23

Disposition: **PASS — refreshed from the completed serial accounting merge.**

The coordinator ran:

```text
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

The yield layer now contains 51 state/DC rows and five reviewed operational
waves/rounds. The latest row is Parallel Round 1: 300 attempted, 297 parseable,
272 candidate-positive, 25 parseable-empty, three failures, 763 parsed lead
rows, 6,530 seconds parallel wall time, 165.391 attempted rows/hour, 420.643
candidate rows/hour, and 2.569 candidate rows per parseable municipality.

All 13 dashboard JSON files parse. `project_phase_summary.json` now reports:

- 1,091/2,000 scout-covered (54.5%);
- 909 remaining;
- approximately seven comparable 150-row waves remaining;
- 2,362 URL-bearing unverified queue rows;
- 884 candidate-positive municipalities; and
- 23 failure-only municipalities.

`parallel_scout_status.json` now records the two-lane round as completed and
serially merged after audit. It does not imply source verification. The Scout
Operations panel now describes the completed two-lane test, keeps three lanes
as an explicitly authorized future option, and renders the five-round runtime
trend.

The state-yield leaderboard changed materially as the Ohio-heavy round entered
the sample. The prior top five by candidate rows per covered municipality were
WA, MA, PA, FL, and MI. The refreshed top five are OH (3.220), IA (2.909), WA
(2.860), WI (2.750), and CT (2.737), each subject to the report's sample-size
and discovery-stage caveats. These are operational yields, not evidence quality
or wage findings.

Candidate rows remain unverified. Project-wide verification, extraction,
ingestion, rating, descriptive wage-growth-gap analysis, and mechanism
correlation documentation remain downstream work for the approximately
2,000-covered checkpoint. The wage-growth-gap map/filter remains planned and
inactive; regressions remain deferred.
