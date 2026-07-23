# Tier 1 Wave 2 priority refresh decision — 2026-07-22

## Decision

REFRESH. Tier 1 Wave 2 produced 148 parseable/successfully covered municipalities, exceeding the task's 135-row threshold. The existing deterministic priority builder was run without changing methodology, then dashboard data was rebuilt so the priority JSON uses the refreshed layer.

## Checkpoint

- Priority-tier baseline was originally built at 504 successfully covered municipalities.
- Tier 1 Wave 1 added 142 successful outcomes.
- Tier 1 Wave 2 added 148 successful outcomes.
- Post-tiering successful additions: 290.
- Current successful coverage: 794.
- Current failure-only retry targets: 20.

Although the cumulative post-tiering addition is ten short of the general 300-scout lower cadence, the explicit per-task rule authorizes refresh because this wave alone exceeded 135 parseable rows.

## Refreshed outputs

- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv`
- `docs/analysis/national_municipality_priority_tier_summary_2026-07-22.csv`
- `docs/analysis/state_priority_summary_2026-07-22.csv`
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv`
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv`
- `docs/analysis/national_priority_tier_build_summary_2026-07-22.md`
- `docs/analysis/national_priority_tiering_sensitivity_analysis_2026-07-22.md`
- `docs/analysis/national_priority_tiering_validation_2026-07-22.md`

Refreshed headline results are 35,589 total rows, 34,789 future-scout eligible, Tier 1 all-row count 1,780, Tier 2 3,559, Tier 3 7,118, Tier 4 10,676, Tier 5 12,456, Tier 1 eligible 1,227, Tier 2 eligible 3,478, and 20 separate failure-retry targets.

The scoring weights, smoothing, thresholds, confidence rules, failure treatment, and interpretation are unchanged. Scores remain research-operational heuristics, not facts about unionization, department existence, source availability, wage gaps, or causality.

Dashboard priority outputs were rebuilt after this refresh:

- `docs/dashboard/data/priority_summary.json`
- `docs/dashboard/data/state_priority_summary.json`
- `docs/dashboard/data/top_priority_targets.json`

Recommended next priority refresh: after roughly another 300–600 successful scouts, or at approximately 1,094–1,394 covered municipalities.
