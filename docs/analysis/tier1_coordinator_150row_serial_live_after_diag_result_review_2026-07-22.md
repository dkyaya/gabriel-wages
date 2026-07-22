# Tier 1 coordinator 150-row live result after hosted-search diagnostic

Date: 2026-07-22
Run: `all_2026-07-22_164144`
Output: `tmp/tier1_coordinator_150row_serial_live_after_diag_direct_sdk_2026-07-22_attempt1`
Disposition: **complete and merge-eligible, with 142 parseable outcomes and eight isolated timeout-only municipalities excluded from successful coverage.**

## Lineage and execution

- Parent `c6b3664` and retry `25445fe` each stopped after two immediate transport failures, produced zero parseable rows and zero candidates, and were never merged.
- Diagnostic `b74e82d` passed the no-search control, two hosted-search calls, and a one-row Oklahoma City production-runner probe. Those diagnostic/probe outputs remain quarantined and were not used in this accounting.
- The official full run used locked input SHA-256 `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`.
- Exactly one full coordinator process used direct SDK, `state=ALL`, mixed-state authorization, exact max/cap 150, `n_parallels=1`, five-second spacing, 90-second timeout, and zero SDK retries.
- The process started `2026-07-22T20:41:44Z`, finished `2026-07-22T22:33:47Z`, exited 0, and reached `execution_status=completed`.
- The staged lineage note was copied into the output after the runner created and closed its fresh directory. The runner's nonempty-directory guard therefore remained intact.
- No resume was used or needed: all 150 rows were attempted once and all 150 raw/timing records reached a terminal state.

## Outcome accounting

- Locked / attempted / raw / timing rows: 150 / 150 / 150 / 150.
- Parseable rows: 142.
- Candidate-positive municipalities: 99.
- Parseable-empty municipalities: 43.
- Failure-only municipalities: 8.
- Stopped-before-request rows: 0.
- URL-bearing candidate rows: 268.

All 142 parseable outcomes contain response IDs, nonempty text, and positive output-token counts. Candidate-positive, parseable-empty, and timeout-only identity sets are disjoint and account for all 150 input rows.

## Results by state

| State | Attempted | Parseable | Candidate-positive | Parseable empty | Failure-only | Candidate rows |
|---|---:|---:|---:|---:|---:|---:|
| AK | 1 | 1 | 1 | 0 | 0 | 3 |
| AL | 6 | 6 | 3 | 3 | 0 | 4 |
| AR | 2 | 1 | 0 | 1 | 1 | 0 |
| AZ | 11 | 10 | 5 | 5 | 1 | 12 |
| CO | 9 | 9 | 5 | 4 | 0 | 11 |
| CT | 3 | 3 | 3 | 0 | 0 | 10 |
| DC | 1 | 1 | 1 | 0 | 0 | 5 |
| FL | 15 | 14 | 14 | 0 | 1 | 38 |
| GA | 7 | 7 | 2 | 5 | 0 | 2 |
| HI | 1 | 1 | 1 | 0 | 0 | 3 |
| IA | 4 | 4 | 3 | 1 | 0 | 11 |
| ID | 1 | 1 | 1 | 0 | 0 | 2 |
| IN | 2 | 0 | 0 | 0 | 2 | 0 |
| KS | 4 | 4 | 2 | 2 | 0 | 3 |
| KY | 2 | 2 | 2 | 0 | 0 | 5 |
| LA | 3 | 3 | 2 | 1 | 0 | 5 |
| MA | 9 | 9 | 8 | 1 | 0 | 22 |
| MD | 1 | 1 | 1 | 0 | 0 | 3 |
| MI | 4 | 4 | 4 | 0 | 0 | 8 |
| MN | 4 | 4 | 3 | 1 | 0 | 10 |
| MO | 5 | 4 | 3 | 1 | 1 | 6 |
| MS | 1 | 1 | 0 | 1 | 0 | 0 |
| NC | 8 | 8 | 1 | 7 | 0 | 3 |
| NE | 2 | 2 | 2 | 0 | 0 | 7 |
| NM | 2 | 2 | 2 | 0 | 0 | 6 |
| NV | 4 | 3 | 3 | 0 | 1 | 12 |
| OH | 2 | 2 | 2 | 0 | 0 | 7 |
| OK | 3 | 3 | 3 | 0 | 0 | 8 |
| OR | 3 | 3 | 3 | 0 | 0 | 11 |
| RI | 1 | 1 | 1 | 0 | 0 | 3 |
| SC | 3 | 3 | 1 | 2 | 0 | 1 |
| SD | 1 | 1 | 1 | 0 | 0 | 3 |
| TN | 7 | 7 | 4 | 3 | 0 | 9 |
| UT | 1 | 1 | 1 | 0 | 0 | 3 |
| VA | 7 | 7 | 3 | 4 | 0 | 7 |
| WA | 6 | 5 | 4 | 1 | 1 | 14 |
| WI | 4 | 4 | 4 | 0 | 0 | 11 |
| **Total** | **150** | **142** | **99** | **43** | **8** | **268** |

## Results by worker

| Worker | Ranks | Attempted | Parseable | Candidate-positive | Empty | Failure-only | Candidate rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| worker_1 | 1–50 | 50 | 45 | 35 | 10 | 5 | 93 |
| worker_2 | 51–100 | 50 | 47 | 30 | 17 | 3 | 89 |
| worker_3 | 101–150 | 50 | 50 | 34 | 16 | 0 | 86 |

## Isolated failures and stop-gate review

The eight failure-only rows were Phoenix AZ (row 2), Kansas City MO (6), Indianapolis city (balance) IN (13), Las Vegas NV (20), Tampa FL (40), Fort Wayne IN (67), Little Rock AR (91), and Vancouver WA (99). Each was an `APITimeoutError` recorded as `timeout_or_capacity` after approximately 90–96 seconds, with no response ID, text, or token usage. The failures were non-consecutive and each was followed by a successful parseable response. They are excluded from successful coverage and retained for a later retry decision.

There was no two-consecutive connection collapse, systematic JSON/schema failure, stopped-before-request row, lifecycle loss, artifact loss, protected canonical-file mutation, or detected secret exposure. The run is merge-eligible under the same isolated-failure accounting used for the first two successful coordinator waves.

## Timing, usage, and cost

- Total elapsed: 6,723.519 seconds (112m 03.519s).
- Recorded sleep: 745.208 seconds (12m 25.208s).
- Average attempted-row request time: 39.850 seconds.
- Median attempted-row request time: 36.398 seconds.
- Effective throughput: 80.315 rows/hour.
- Input / reasoning / output / total tokens: 4,258,356 / 196,927 / 309,071 / 4,567,427.
- Estimate-only standard text-token cost: `$1.23800995`; actual billed HUIT/hosted-search cost is unavailable.

Compared with Wave 1 (6,937 seconds; 115m37s), this run was 213.481 seconds (3m33.481s) faster and approximately 2.48 rows/hour higher. Compared with Wave 2 (6,149.884 seconds; 102m29.884s), it was 573.635 seconds (9m33.635s) slower and approximately 7.49 rows/hour lower. Five-second pacing remained operationally stable—every row was attempted and artifacts completed—but the 8/150 isolated timeout rate is higher than the prior waves and should be monitored.

## Tier 1 yield comparison

Tier 1 targeting produced 268 candidate rows, versus 246 in Wave 1 and 223 in Wave 2: +22 (+8.9%) and +45 (+20.2%), respectively. Candidates per parseable municipality were approximately 1.887, versus 1.651 in Wave 1 and 1.507 in Wave 2. Candidate-positive municipalities were 99, one more than Wave 2 but 13 fewer than Wave 1; among parseable rows, the positive rate was 69.7%, between Wave 1 (75.2%) and Wave 2 (66.2%). Thus Tier 1 improved candidate-row density against both prior waves, but did not improve the municipality-positive rate against Wave 1. This is operational yield evidence, not proof that the tier score predicts verified source quality.

## Stage boundary and priority decision

All 268 rows remain unverified scout-stage leads. No result was independently opened, downloaded, verified, ingested, codified, promoted to canonical data, or used as claim evidence. Later verification must still establish exact employer, unit, provenance, completeness, dates, wages, duplicates, access, and matched city-cycle overlap.

National priority tiers were not rebuilt. The method is deterministic and integrated, but this wave adds only 142 successful scouts since the last tier build, below the documented 300–600-scout recalculation cadence. Priority CSVs and priority-specific dashboard JSON therefore still describe pre-Tier-1-Wave-1 coverage (504 covered, 10 failure-only), while current scout/queue dashboard panels reflect 646 covered and 18 failure-only. Refresh the priority layer after another 158–458 successful scouts, or sooner if the PI needs immediately synchronized priority counts.
