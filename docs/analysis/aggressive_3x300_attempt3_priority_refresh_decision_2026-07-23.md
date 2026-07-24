# Aggressive 3×300 Attempt 3 — Priority Refresh Decision

Date: 2026-07-23/24  
Decision: **refresh completed**

## Reason

Attempt 3 added 899 successfully scout-covered municipalities after the last
priority refresh and moved official coverage beyond the approximately
2,000-municipality workflow checkpoint. This materially changes ordinary
eligibility and state workloads. The existing canonical methodology was
therefore rebuilt once without changing its scoring, tier, confidence, or
failure-retry definitions:

```text
python scripts/build_national_municipality_priority_tiers.py
python scripts/build_dashboard_data.py
```

## Refreshed files

- `national_municipality_priority_tiers_2026-07-22.csv`
- `national_municipality_priority_tier_summary_2026-07-22.csv`
- `state_priority_summary_2026-07-22.csv`
- `national_priority_tier_top_targets_2026-07-22.csv`
- `national_failure_retry_priority_2026-07-22.csv`
- `national_priority_tier_build_summary_2026-07-22.md`
- `national_priority_tiering_sensitivity_analysis_2026-07-22.md`
- `national_priority_tiering_validation_2026-07-22.md`
- the dashboard priority, state-priority, and top-target JSON layers

## Current counts

- Municipality universe: 35,589
- Scout-covered: 2,436
- Future-scout eligible: 33,147
- Eligible Tier 1: 245
- Eligible Tier 2: 2,906
- Eligible Tier 3: 6,889
- Eligible Tier 4: 10,651
- Eligible Tier 5: 12,456
- Failure-only retry targets: 28

The builder's all-status tier totals are Tier 1 1,780, Tier 2 3,559, Tier 3
7,118, Tier 4 10,676, and Tier 5 12,456; the eligible counts above are the
relevant future-scout subset.

## Operating decision

The priority layer is current, but broad scouting is paused. It must not be
used to schedule another ordinary discovery wave until the verification,
extraction, and matching strategy has been reviewed by the user or PI. The
28 failure-only targets also remain separate and are not an implicit
authorization for a retry wave.

Priority tiers remain research-operational heuristics, not findings about
source availability, unionization, wage gaps, or causal effects.
