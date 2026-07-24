# Aggressive 3×300 Dashboard and Status Update

Date: 2026-07-23

## Result

Dashboard and operations status now identify
`POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23` as the next planned round. Its
status is explicitly `planned_not_run`.

The existing-data builders were run:

```text
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

They preserve official accounting at:

- 1,537 scout-covered municipalities;
- 1,267 candidate-positive municipalities;
- 270 parseable-empty municipalities;
- 27 failure-only municipalities; and
- 3,347 unverified candidate queue rows.

No national queue or coverage builder ran.

## Status fields

`project_phase_summary.json` now includes:

- active round ID `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`;
- status `planned_not_run`;
- profile `aggressive_300`;
- three lanes and 300 rows per lane;
- 900 expected attempts;
- approximately 892 expected parseable outcomes at the recent 446/450 rate;
- approximately 2,429 projected post-merge coverage;
- an approximate +429 checkpoint margin;
- an explicit `intentional_user_approved` overshoot marker;
- an eight-minute lane-start stagger; and
- the preserved 3×160 round marked `superseded_preserved_not_active`.

`parallel_scout_status.json` now reports
`aggressive_3x300_planned_not_run`, lane-local candidate exports, serial
accounting after combined audit, and the same supersession and overshoot
boundary.

`scout_operations_summary.json`, the Scout Operations frontend, and the
dashboard README use the same active-round framing.

## Caveats

- The aggressive plan has not run.
- The 892 expected parseable outcomes and 2,429 projected total are estimates,
  not live evidence or official accounting.
- Candidate rows remain unverified leads.
- Wage gaps have not been calculated, and the wage-growth-gap map/filter remains
  planned rather than active.
- Mechanism correlations have not been analyzed.
- Priority tiers remain operational scheduling inputs, not findings.
- Broad scouting should pause after the aggressive round's later successful
  serial merge, unless the user or PI explicitly authorizes more discovery.

This status correction made no live/API/model/hosted-search call, source
verification, extraction, ingestion, codification, queue/coverage change,
wage-gap claim, causal claim, or regression.
