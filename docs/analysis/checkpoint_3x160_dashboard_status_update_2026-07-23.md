# Checkpoint 3×160 Dashboard and Status Update

Date: 2026-07-23

## Result

Dashboard and operations status now identify
`POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23` as the next planned round.
The status is explicitly `planned_not_run`; no live result or new accounting is
represented.

The existing-data builders were run:

```text
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

They reproduced the committed official accounting:

- 1,537 scout-covered municipalities;
- 1,267 candidate-positive municipalities;
- 270 parseable-empty municipalities;
- 27 failure-only municipalities; and
- 3,347 unverified candidate queue rows.

No queue or coverage builder ran.

## Fields updated

`project_phase_summary.json` now includes:

- round ID `POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23`;
- status `planned_not_run`;
- three lanes and 160 rows per lane;
- 480 expected attempts;
- approximately 476 expected parseable outcomes at the recent 446/450 rate;
- approximately 2,013 expected post-merge coverage;
- an estimated +13 checkpoint margin; and
- a rule to pause broad scouting after a successful merge reaches
  approximately 2,000.

`parallel_scout_status.json` now reports:

- `checkpoint_3x160_planned_not_run`;
- `three_lane_checkpoint_round_planned`;
- four-minute lane start spacing;
- lane-local candidate exports and serial accounting;
- the completed Round 2 result as the latest live/merged round; and
- 3×300 as feasible but deferred because it would likely overshoot the
  checkpoint by more than 400 municipalities.

`scout_operations_summary.json` identifies the locked 3×160 ordinary round as
the next operating lane and records the downstream pause rule.

The Scout Operations frontend and dashboard README describe the same status:
the plan exists, it has not run, and its expected effect is operational
planning rather than evidence.

## Caveats

- Candidate rows remain unverified leads.
- The 476 expected parseable outcomes and 2,013 projected total are estimates,
  not live results or guaranteed accounting.
- Wage gaps have not been calculated, and the wage-growth-gap dashboard layer
  remains planned rather than active.
- Mechanism correlations have not been analyzed.
- Priority tiers remain operational scheduling inputs, not findings.
- No additional broad round should be presumed after the checkpoint is reached.

This status update made no live/API/model/hosted-search call, source
verification, ingestion, codification, queue/coverage change, wage-gap claim,
causal claim, or regression.
