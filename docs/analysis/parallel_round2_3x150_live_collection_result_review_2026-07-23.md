# Parallel Round 2 3×150 Live Collection Result Review

Date: 2026-07-23
Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

## Decision

The first three-lane live collection completed successfully. All three isolated
lanes are `completed_merge_eligible`, completed municipality IDs do not overlap,
lane-local candidate exports are byte-identical to each lane's
`parsed_candidates.csv`, and the offline auditor recommends
`merge_all_lanes`.

This is a collection result only. No queue, coverage, yield, dashboard,
project-phase, or priority builder ran. A later explicitly authorized serial
merge must decide whether to apply the lane outputs to national accounting.

## Evidence gates

- Readiness audit: pass.
- Locked inputs: 150 rows per lane; 450 distinct municipality IDs and 450
  distinct Census government IDs; no overlap.
- Current ordinary eligibility: pass for all 450 rows; no retry, failure-only,
  covered, or canonical municipality was selected.
- Search hints: five deterministic hints for all 450 rows.
- Stronger preflight: pass for the no-search control, trivial hosted-search
  call, municipality-style hosted-search call, and parseable one-row scout
  probe.
- Diagnostic probe: quarantined from official evidence and accounting.
- Fresh dry-runs: pass, 150/150 prompts and hints in each lane, with no backend
  call.
- Live controls: direct SDK, `gpt-5.4-nano`, low search context, compact
  prompts, deterministic hints, one in-lane parallelism, adaptive
  `3/5/15/10` pacing with `25/2` windows, 90-second inner and outer timeout,
  zero SDK retries, lane-specific cost logs, and lane-local candidate exports.

## Launch and wall-clock timing

| Event | UTC |
|---|---|
| Lane 1 launch | 2026-07-23 22:28:45 |
| Lane 2 launch | 2026-07-23 22:33:30 |
| Lane 3 launch | 2026-07-23 22:37:35 |
| Lane 1 finish | 2026-07-23 23:52:59 |
| Lane 3 finish | 2026-07-23 23:57:00 |
| Lane 2 finish / round end | 2026-07-24 00:02:22 |

Measured launch spacing was 4m45s from Lane 1 to Lane 2 and 4m05s from Lane 2
to Lane 3. The target was four minutes. The first spacing includes the
coordinator's explicit post-gate filesystem/session check and tool transition;
the second was within five seconds. This deviation did not alter lane inputs or
live settings, and no immediate transport or lifecycle failure appeared before
either sibling launch.

Parallel wall-clock elapsed from the first prompt start through the final prompt
finish was 5,615.561 seconds (1h33m35.561s). Effective combined throughput was:

- 288.484 attempted rows/hour;
- 285.919 parseable rows/hour.

For comparison, Parallel Round 1 achieved 165.391 attempted rows/hour. This
round's combined attempted throughput was about 74.4% higher while moving from
two to three isolated lanes.

## Lane results

| Metric | Lane 1 | Lane 2 | Lane 3 | Combined |
|---|---:|---:|---:|---:|
| Attempted | 150 | 150 | 150 | 450 |
| Parseable | 148 | 149 | 149 | 446 |
| Candidate-positive municipalities | 132 | 125 | 126 | 383 |
| Parseable-empty municipalities | 16 | 24 | 23 | 63 |
| Failure-only | 2 | 1 | 1 | 4 |
| Stopped before request | 0 | 0 | 0 | 0 |
| Candidate lead rows | 335 | 343 | 307 | 985 |
| Runner elapsed, seconds | 5,053.578 | 5,331.764 | 4,764.610 | — |
| Runner elapsed, readable | 1h24m13.578s | 1h28m51.764s | 1h19m24.610s | — |
| Effective lane rows/hour | 106.855 | 101.280 | 113.336 | 288.484 parallel |
| Exit code | 0 | 0 | 0 | — |
| Audit classification | `completed_merge_eligible` | `completed_merge_eligible` | `completed_merge_eligible` | `merge_all_lanes` |

No lane needed or used a resume.

## Failure-only rows and outer-timeout behavior

| Lane | Municipality | State | Municipality ID | Failure type |
|---|---|---|---|---|
| 1 | Twinsburg | OH | `cog_2025_194843` | `empty_response_no_response_id` |
| 1 | Oakland Park | FL | `cog_2025_189806` | `empty_response_no_response_id` |
| 2 | Hollister | CA | `cog_2025_161242` | `outer_timeout` |
| 3 | College Place | WA | `cog_2025_176888` | `empty_response_no_response_id` |

The Hollister request exceeded the configured 90-second outer guard. The runner
checkpointed it as a terminal `outer_timeout`, increased Lane 2's adaptive
sleep, and continued. The process did not hang. There were no two-consecutive
transport failures and no stopped-before-request rows.

## Adaptive pacing

| Metric | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| Total sleep, seconds | 520.202 | 885.212 | 520.220 |
| Mean attempted-row elapsed, seconds | 30.216 | 29.638 | 28.290 |
| Median attempted-row elapsed, seconds | 27.453 | 29.062 | 28.193 |
| Observed adaptive level min/median/max, seconds | 3 / 3 / 5 | 3 / 5 / 10 | 3 / 3 / 5 |
| Backoff events | 0 | 1 | 0 |
| Step-down events | 2 | 4 | 2 |

The one outer timeout caused Lane 2's single backoff event. The lane later
stepped down deterministically and completed. The other lanes spent most of the
round at the three-second minimum after stability step-downs.

## Candidate leads by state

These counts are unverified source-discovery leads, not verified evidence.

| State | Lane 1 | Lane 2 | Lane 3 | Combined |
|---|---:|---:|---:|---:|
| AK | 0 | 7 | 0 | 7 |
| AR | 0 | 5 | 0 | 5 |
| CA | 7 | 10 | 21 | 38 |
| CT | 3 | 0 | 1 | 4 |
| DE | 1 | 0 | 3 | 4 |
| FL | 27 | 32 | 15 | 74 |
| IA | 6 | 10 | 11 | 27 |
| ID | 0 | 5 | 2 | 7 |
| IN | 16 | 8 | 20 | 44 |
| KY | 1 | 3 | 8 | 12 |
| MA | 18 | 10 | 6 | 34 |
| MD | 6 | 7 | 6 | 19 |
| ME | 3 | 0 | 3 | 6 |
| MI | 27 | 23 | 24 | 74 |
| MN | 7 | 14 | 13 | 34 |
| MS | 0 | 0 | 2 | 2 |
| MT | 4 | 5 | 3 | 12 |
| ND | 1 | 3 | 0 | 4 |
| NE | 1 | 2 | 6 | 9 |
| NH | 4 | 9 | 0 | 13 |
| NM | 0 | 4 | 0 | 4 |
| NV | 3 | 3 | 0 | 6 |
| NY | 0 | 2 | 2 | 4 |
| OH | 97 | 95 | 89 | 281 |
| OK | 1 | 3 | 2 | 6 |
| OR | 34 | 23 | 15 | 72 |
| RI | 0 | 6 | 0 | 6 |
| SD | 0 | 0 | 3 | 3 |
| VT | 0 | 3 | 0 | 3 |
| WA | 34 | 24 | 36 | 94 |
| WI | 29 | 27 | 14 | 70 |
| WY | 5 | 0 | 2 | 7 |
| **Total** | **335** | **343** | **307** | **985** |

Candidate-positive municipality counts by state, combined across lanes, were:
AK 2, AR 3, CA 14, CT 2, DE 2, FL 37, IA 11, ID 3, IN 20, KY 7,
MA 11, MD 6, ME 2, MI 29, MN 16, MS 1, MT 4, ND 3, NE 6, NH 3,
NM 2, NV 2, NY 2, OH 84, OK 4, OR 29, RI 2, SD 1, VT 1, WA 39,
WI 32, and WY 3.

## Usage and cost

The finalized timing ledgers recorded approximately:

- 13,062,430 input tokens;
- 988,745 output tokens;
- 577,360 reasoning tokens;
- 14,051,175 total tokens.

The estimate-only lane costs were $1.31832335, $1.27191265, and
$1.25818125, or approximately $3.84841725 combined. No provider-billed total
was available in the artifacts.

## Artifact and overlap audit

- All three expected input hashes match.
- Each lane has 150 terminal timing rows and zero pending rows.
- Completed municipality-ID overlap across lanes: zero.
- Lane-local candidate export count: exactly one per lane.
- Each lane-local candidate export is byte-identical to its lane-local
  `parsed_candidates.csv`.
- Candidate exports were not written to shared `docs/analysis/`.
- Audit artifact errors: none.
- Offline recommendation: `merge_all_lanes`.

## Boundaries and next action

The 446 parseable outcomes could move official scout coverage from 1,091 to
approximately 1,537 if a later serial merge accepts all three lane outputs.
That is only a planning estimate; official coverage remains 1,091 until the
canonical builders run in a separate authorized task. The estimated remaining
distance to the approximately 2,000 checkpoint after such a merge would be 463
municipalities.

The next action is a separate coordinator-controlled serial merge using the
three-lane merge template. That task must re-audit hashes, exports, failures,
overlap, and merge eligibility; rebuild national accounting exactly once; and
then refresh yield/dashboard/project-phase data. No verification, ingestion,
codification, wage-gap analysis, causal claim, or regression has occurred.
