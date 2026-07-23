# Parallel Round 1 Priority Refresh Decision — 2026-07-23

Decision: **DEFER national priority-tier rebuild.**

The latest priority build followed Tier 1 Wave 2 at 794 successful
scout-covered municipalities. Parallel Round 1 adds 297 successful scouts,
bringing current coverage to 1,091. The documented cadence is a refresh after
approximately 300–600 additional successful scouts. Because 297 is below the
lower deterministic trigger, this merge does not run
`scripts/build_national_municipality_priority_tiers.py`.

The methodology is unchanged. The canonical priority CSVs therefore retain
their Tier 1 Wave 2 vintage:

- `national_municipality_priority_tiers_2026-07-22.csv`
- `national_priority_tier_top_targets_2026-07-22.csv`
- `state_priority_summary_2026-07-22.csv`
- `national_failure_retry_priority_2026-07-22.csv`

The dashboard priority JSON files were regenerated for site consistency, but
their priority counts still come from those stale source CSVs. The builder now
marks them `stale_after_parallel_round1_merge`, records 297 successful scouts
since refresh, and requires every future ordinary selection to reconcile the
ranked rows against current coverage and failure-only status.

Recommended trigger: rebuild with the unchanged canonical methodology after
the next successful parseable scout outcomes take the post-refresh addition to
at least 300, or earlier only under a separate explicit strategy decision. No
priority methodology, substantive classification, or project finding changed.
