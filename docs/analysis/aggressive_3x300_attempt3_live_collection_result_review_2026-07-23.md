# Aggressive 3×300 Attempt 3 Live Collection Result Review

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`  
Result: all three lanes completed; serial accounting merge deferred

## Prior quarantined attempts

- Attempt 1 (`dcf3cd5`) remains non-mergeable. Lane 1 made two immediate no-evidence connection-failure calls, produced zero parseable outcomes, checkpointed 298 rows as `stopped_before_request`, and suppressed Lanes 2–3.
- Attempt 2 (`18c3415`) remains non-mergeable. Its exactly one stronger live gate failed its first no-search call with a sanitized HTTP 500; no dry run or live lane ran.
- Neither lineage is municipality evidence or an accounting input.

## Attempt 3 gates

- The locked-input/readiness audit passed the three expected SHA-256 hashes, 900 current ordinary-eligibility checks, 900/900 exact five-hint sets, and zero municipality/Census overlap.
- Plan-only preflight recorded zero external calls.
- Exactly one stronger live gate passed the no-search, trivial hosted-search, municipality-style hosted-search, and one-row production-path probe controls. Each control had the required response evidence; the Newport, RI probe parsed with three unverified leads and remains quarantined.
- All three dry runs passed 300 compact prompts and 300/300 hint matches, exact identity order, adaptive `3/5/15/10` with `25/2` windows, terminal dry timing, strict source/unit/stage controls, and no backend call.

## Staged lane-health gates

The live runner initializes `row_timing.csv` before the batch but writes terminal row statuses only after the whole lane returns. The shell capture is likewise buffered until process exit. Consequently, an exact live count of ten parseable rows was not observable without changing the locked runner during a live task.

The coordinator used the prompt's conservative fallback:

- Lane 1 launched at `2026-07-23T22:16:45-04:00`. It remained alive well beyond the maximum two-consecutive 90-second timeout-collapse interval, with its initialized artifacts intact. The Lane 2 launch decision was recorded after 8 minutes 9 seconds; the persisted Lane 2 start was `22:25:40-04:00`, an actual gap of 8 minutes 55 seconds.
- Lane 2 passed the same sustained-process/no-collapse fallback. The launch decision was recorded after 9 minutes 50 seconds; managed-tool transition time put the persisted Lane 3 start at `22:38:40-04:00`, an actual Lane 2→3 gap of 13 minutes.
- Lane 3 was the third and final lane. No lane was suppressed, no fourth lane ran, and no resume ran.
- Terminal evidence later showed 299 parseable Lane 1 rows and 300 parseable Lane 2 rows, confirming that both predecessor lanes were in fact healthy. This terminal fact does not retroactively convert the live fallback into a contemporaneous ten-row count.

The live scripts wrote only `lineage_note.txt` before runner startup because the runner's immutable-output guard permits no other precreated lane-root entry. The runner created the lane-local candidate export; after termination, each script copied its captured console log and wrote the exit code into the lane root.

## Per-lane results

| Metric | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| exit code | 0 | 0 | 0 |
| attempted rows | 300 | 300 | 300 |
| parseable rows | 299 | 300 | 300 |
| candidate-positive municipalities | 214 | 200 | 177 |
| parseable-empty municipalities | 85 | 100 | 123 |
| failure-only rows | 1 | 0 | 0 |
| stopped before request | 0 | 0 | 0 |
| candidate lead rows | 548 | 456 | 385 |
| runtime | 2h37m03.437s | 2h17m31.981s | 2h07m02.049s |
| effective rows/hour | 114.608 | 130.878 | 141.694 |
| total sleep | 1,625.398s | 970.392s | 970.382s |
| outer timeouts | 1 | 0 | 0 |
| backoff events | 1 | 0 | 0 |
| step-down events | 7 | 2 | 2 |
| observed adaptive levels | 3–10s; median 5s | 3–5s; median 3s | 3–5s; median 3s |
| lane-local export | one; byte-identical | one; byte-identical | one; byte-identical |
| auditor classification | `completed_merge_eligible` | `completed_merge_eligible` | `completed_merge_eligible` |

Lane 1's sole failure is Shelby, OH (`cog_2025_209091`): the outer 90-second guard produced terminal `outer_timeout` evidence with no response ID or token usage. The adaptive controller backed off and the lane continued. This row is failure-only and must remain outside successful scout coverage in a later merge.

## Combined result

- Attempted: 900
- Parseable: 899
- Candidate-positive municipalities: 591
- Parseable-empty municipalities: 308
- Failure-only: 1
- Stopped before request: 0
- Candidate lead rows: 1,389
- Parallel wall-clock elapsed: 9,422.628 seconds (2h37m02.628s), measured from actual first/last row timestamps
- Effective attempted throughput: 343.853 rows/hour
- Effective parseable throughput: 343.471 rows/hour
- Adaptive events: one backoff and 11 step-downs
- Combined actual sleep: 3,566.172 seconds
- Outer timeouts: one
- Input/output/reasoning/total tokens: 23,706,931 / 1,577,994 / 987,280 / 25,284,925
- Estimated standard text-token cost: `$6.713879`, estimate-only; actual HUIT pricing, hosted-search/tool fees, and adjustments are unavailable

Candidate lead rows by state:

| State | Leads | State | Leads | State | Leads |
|---|---:|---|---:|---|---:|
| AK | 19 | AL | 5 | AR | 5 |
| AZ | 8 | CA | 387 | CO | 4 |
| CT | 6 | DE | 13 | IA | 16 |
| ID | 6 | IL | 3 | IN | 3 |
| KS | 27 | LA | 16 | MA | 6 |
| MD | 27 | ME | 41 | MI | 5 |
| MN | 81 | MO | 45 | MS | 8 |
| MT | 31 | ND | 7 | NE | 14 |
| NH | 18 | NM | 12 | NV | 11 |
| NY | 78 | OH | 245 | PA | 26 |
| RI | 8 | SD | 27 | TN | 15 |
| UT | 19 | VA | 16 | VT | 12 |
| WI | 100 | WV | 10 | WY | 9 |

These are unverified source-discovery leads, not verified sources, canonical data, or claim-supporting evidence.

## Export, overlap, and lane audit

Each lane produced exactly one timestamped CSV inside its own `candidate_exports/` directory. Every export is byte-identical to that lane's `parsed_candidates.csv`. No corresponding Attempt 3 export exists under shared `docs/analysis/`.

The committed planning manifest points to historical `attempt1` roots and the auditor does not implement the prompt's `--lane-output-root` option. The exact command used was:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/parallel_round_manifest_attempt3.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/post_lane_audit_attempt3
```

The small Attempt 3 manifest changes only live output/export roots and records actual launch offsets; it retains the locked inputs, hashes, and row counts. The auditor confirmed:

- all three input hashes valid;
- all three lanes `completed_merge_eligible`;
- no pending or stopped-before-request rows;
- no lane artifact error;
- zero completed municipality-ID overlap;
- all three lane-local exports byte-identical; and
- recommendation `merge_all_lanes`.

The recommendation is not a merge authorization.

## Accounting boundary and next action

No national candidate-queue, coverage, yield-learning, dashboard/project-phase, or priority builder ran. Official accounting therefore remains 1,537 scout-covered, 1,267 candidate-positive, 270 parseable-empty, 27 failure-only, and 3,347 URL-bearing queue rows.

No source URL was independently opened or verified; no source was ingested or codified; and no wage-gap calculation/claim, causal claim, or regression occurred.

No lane needs a resume. Under a separate explicit serial-merge authorization, rerun the lane audit, preserve Shelby, OH as failure-only, and process all three merge-eligible lanes through exactly one serial accounting rebuild. The probe and Attempts 1–2 must remain quarantined.

