# Aggressive 3×300 Readiness After Parallel Round 2

Date: 2026-07-23

## Current position

Parallel Round 2's 3 × 150 live collection completed with all three lanes
merge-eligible, and the authorized serial merge completed successfully.
Official scout coverage is now **1,537 / 2,000**, leaving **463** municipalities
to the project-management checkpoint.

The framework is technically capable of running 3 × 300, but that is no longer
the default operational recommendation. At the Round 2 parseable rate
(446/450, or about 99.1%), 900 attempts would yield approximately 892
successful coverage outcomes. That would bring coverage to roughly 2,429 and
overshoot the checkpoint by about 429.

## Recommendation

- Proceed with 3 × 300 only if the user explicitly wants to finish broad
  source-discovery scale-up quickly and accepts a material checkpoint
  overshoot.
- Otherwise prepare a fresh checkpoint-targeted three-lane round from the
  refreshed priority and coverage layers.

Pure division gives `463 / 3 = 154.3`, so 155 rows per lane is the minimum
even split (465 total attempts). At the recent 99.1% parseable rate, that could
land a few municipalities short. A modest failure buffer suggests **160 rows
per lane** (480 total), which would be expected to add about 476 successful
outcomes and finish near 2,013—close to the approximate checkpoint while
preserving three-lane symmetry.

The final size must be selected from current ordinary eligible rows and locked
with no coverage, canonical, retry/failure-only, municipality-ID, or Census-ID
overlap. After that round's serial merge reaches approximately 2,000, broad
scouting should pause. The next phase is verification, extraction, ingestion,
source quality/extractability rating, descriptive wage-growth-gap analysis,
mechanism-correlation documentation, and the planned dashboard gap filter.
Regressions remain deferred.
