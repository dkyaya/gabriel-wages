# Parallel Round 1 Live Collection Result Review — 2026-07-23

Disposition: **COLLECTION COMPLETE — both lanes are independently
`completed_merge_eligible`; the offline auditor recommends `merge_all_lanes` in
a later, separately authorized serial accounting task.**

No queue, coverage, yield-learning, project-phase, priority, or dashboard
builder was run in this task.

## Evidence gates

- Readiness and locked-input audit: PASS
- Lane 1 input:
  150 rows; SHA-256
  `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Lane 2 input:
  150 rows; SHA-256
  `f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`
- Input municipality-ID overlap: 0
- Input Census-ID overlap: 0
- Stronger preflight: PASS
- Diagnostic one-row probe: 1/1 parseable; quarantined
- Lane 1 fresh dry-run: PASS, 150/150 prompts and hints
- Lane 2 fresh dry-run: PASS, 150/150 prompts and hints

## Launch and timing

| Metric | Lane 1 | Lane 2 |
|---|---:|---:|
| Wrapper start, UTC | 2026-07-23 19:28:36 | 2026-07-23 19:37:58 |
| Wrapper finish, UTC | 2026-07-23 21:09:01 | 2026-07-23 21:17:26 |
| Runner elapsed | 6,024.615 s | 5,967.545 s |
| Runner elapsed, readable | 1h 40m 24.615s | 1h 39m 27.545s |
| Effective lane throughput | 89.632 rows/hour | 90.489 rows/hour |
| Exit code | 0 | 0 |

The actual start stagger was 562 seconds (9m22s). This exceeded the requested
2–5 minute interval because managed-tool scheduling took longer than the
reported polling interval. The deviation was detected from the persisted UTC
start files after both launches. The coordinator did not stop and relaunch a
lane, because doing so would have exceeded the exactly-two-live-process
authorization. The lanes still overlapped live collection for 1h31m03s.

Parallel wall-clock time, from Lane 1 start through Lane 2 finish, was 6,530
seconds (1h48m50s). Effective combined throughput was:

- 165.391 attempted rows/hour (300 rows); and
- 163.737 parseable rows/hour (297 rows).

No lane used resume.

## Results by lane

| Result | Lane 1 | Lane 2 | Combined |
|---|---:|---:|---:|
| Attempted/response rows | 150 | 150 | 300 |
| Parseable rows | 148 | 149 | 297 |
| Candidate-positive municipalities | 137 | 135 | 272 |
| Parseable-empty municipalities | 11 | 14 | 25 |
| Failure-only rows | 2 | 1 | 3 |
| Stopped-before-request rows | 0 | 0 | 0 |
| Candidate lead rows | 386 | 377 | 763 |
| Outer-timeout rows | 1 | 1 | 2 |

Lane 1 failures:

- Newark, Ohio (`cog_2025_209070`): `outer_timeout`, 90.006 seconds,
  no response ID or token usage.
- St. Cloud, Florida (`cog_2025_161668`):
  `empty_response_no_response_id`, 0.276 seconds, no response ID or token usage.

Lane 2 failure:

- Waterloo, Iowa (`cog_2025_207992`): `outer_timeout`, 90.006 seconds,
  no response ID or token usage.

Each outer timeout was checkpointed terminally instead of hanging. Neither
lane had consecutive failures, so the collapse stop rule did not stop later
rows.

## Candidate lead rows by state

| State | Lane 1 | Lane 2 | Combined |
|---|---:|---:|---:|
| CT | 27 | 1 | 28 |
| FL | 50 | 41 | 91 |
| IA | 3 | 12 | 15 |
| IN | 0 | 3 | 3 |
| KY | 0 | 1 | 1 |
| MA | 8 | 45 | 53 |
| MD | 0 | 7 | 7 |
| MI | 42 | 18 | 60 |
| MT | 0 | 7 | 7 |
| NE | 0 | 1 | 1 |
| NM | 0 | 12 | 12 |
| NV | 2 | 0 | 2 |
| OH | 135 | 133 | 268 |
| OR | 52 | 24 | 76 |
| RI | 0 | 10 | 10 |
| SD | 0 | 4 | 4 |
| WA | 61 | 37 | 98 |
| WI | 6 | 21 | 27 |
| **Total** | **386** | **377** | **763** |

Candidate-positive municipalities by state, combined:
CT 11, FL 39, IA 5, IN 2, KY 1, MA 19, MD 3, MI 23, MT 2, NE 1, NM 6,
NV 1, OH 81, OR 29, RI 3, SD 1, WA 35, and WI 10.

These are unverified scout-stage lead counts, not verified sources, ingested
contracts, wage data, or findings.

## Compact prompts, usage, and estimated cost

Both lanes used compact prompt mode and matched deterministic hints 150/150.

| Usage | Lane 1 | Lane 2 | Combined |
|---|---:|---:|---:|
| Input tokens | 4,678,116 | 4,546,945 | 9,225,061 |
| Output tokens | 361,684 | 355,807 | 717,491 |
| Reasoning-token detail | 204,078 | 198,056 | 402,134 |
| Total tokens | 5,039,800 | 4,902,752 | 9,942,552 |
| Estimate-only text-token cost | $1.387728 | $1.354148 | $2.741876 |

Actual cost is unavailable. The estimate excludes unconfirmed HUIT adjustments
and hosted-search/tool fees and must not be treated as billed cost.

## Adaptive sleep

| Metric | Lane 1 | Lane 2 |
|---|---:|---:|
| Total observed sleep | 1,102.212 s | 1,120.220 s |
| Mean attempted-row elapsed | 32.809 s | 32.309 s |
| Median attempted-row elapsed | 30.831 s | 30.062 s |
| Observed level min/median/max | 4.0 / 7.5 / 10.0 s | 5.0 / 7.5 / 10.0 s |
| Backoff events | 1 | 1 |
| Stable step-down events | 5 | 5 |
| Stable holds | 144 | 144 |

Compact prompts, deterministic hints, adaptive sleep, and the outer timeout
operated coherently in both lanes.

## Isolation and artifact caveat

Each complete lane artifact set is in its configured isolated live output
directory. The current serial runner additionally wrote its normal timestamped
candidate export under `docs/analysis/`:

- Lane 1:
  `gabriel_state_source_scout_candidates_all_2026-07-23_152836.csv`
- Lane 2:
  `gabriel_state_source_scout_candidates_all_2026-07-23_153758.csv`

Each timestamped file is byte-identical to its lane's isolated
`parsed_candidates.csv`. The filenames did not collide, and neither file was
used by a national builder. This is nevertheless an isolation caveat: before a
future parallel round, the runner should support directing or suppressing this
secondary export so every lane-created artifact stays under its lane root.

## Offline lane audit

- Lane 1 classification: `completed_merge_eligible`
- Lane 2 classification: `completed_merge_eligible`
- Input hashes valid: yes
- Completed municipality-ID overlap: 0
- Pending timing rows: 0
- Audit recommendation: `merge_all_lanes`
- Shared accounting writes by auditor: 0

The recommendation is not a merge authorization. The next action is a separate
coordinator-controlled serial merge task using the existing serial merge
prompt. That task should ingest both lane outputs into accounting exactly once,
refresh coverage/yield/dashboard only after its own gates pass, and decide how
to schedule the three failed municipalities separately from ordinary scouting.

Official progress remains 794/2,000 in this task. If—and only if—the later
serial merge accepts all 297 parseable outcomes, arithmetic progress would
become 1,091/2,000, leaving 909 municipalities and approximately seven more
successful 150-row waves at comparable parseability.

## Limitations

- Candidate leads have not been verified or ingested.
- Diagnostic preflight/probe output is quarantined.
- The stopped `bd5e259` output remains quarantined and non-evidence.
- Current official coverage remains 794 until a later serial merge.
- No wage-growth gap was calculated and no wage-gap, mechanism, regression, or
  causal claim is supported by this collection review.
