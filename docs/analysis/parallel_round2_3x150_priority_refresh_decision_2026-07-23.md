# Parallel Round 2 3×150 Priority Refresh Decision

Date: 2026-07-23

## Decision

**Refresh performed using the unchanged canonical methodology.**

The last national priority refresh occurred at 794 successfully scout-covered
municipalities. Parallel Round 1 added 297 and deliberately stopped just below
the documented 300-success lower trigger. Parallel Round 2 added another 446.
The combined 743 successful scouts since the last refresh clearly exceed the
documented 300–600 cadence.

Commands:

```text
python scripts/build_national_municipality_priority_tiers.py
python scripts/build_dashboard_data.py
```

No score component, weight, tier boundary, confidence method, government-type
eligibility rule, or retry rule changed.

## Refreshed outputs

- `national_municipality_priority_tiers_2026-07-22.csv`
- `national_municipality_priority_tier_summary_2026-07-22.csv`
- `state_priority_summary_2026-07-22.csv`
- `national_priority_tier_top_targets_2026-07-22.csv`
- `national_failure_retry_priority_2026-07-22.csv`
- the priority build summary, sensitivity analysis, and validation report
- dashboard `priority_summary.json`, `state_priority_summary.json`, and
  `top_priority_targets.json`

## Current counts

- Authoritative municipality/township rows: **35,589**
- Successfully covered: **1,537**
- Future-scout eligible: **34,046**
- Failure-only retry targets: **27**
- Tier 1 eligible: **628**
- Tier 2 eligible: **3,420**
- Tier 3 eligible: **6,934**
- Tier 4 eligible: **10,608**
- Tier 5 eligible: **12,456**

The dashboard marks the priority vintage current after the Round 2 merge and
records zero new successful scouts since this refresh. Priority tiers remain
research-operational scheduling heuristics, not findings. Any future ordinary
selection must still reconcile the ranked file against then-current coverage,
failure status, canonical overlap, and cross-lane identity exclusions before
locking inputs.
