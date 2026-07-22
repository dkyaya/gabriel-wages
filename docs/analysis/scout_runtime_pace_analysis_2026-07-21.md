# Scout runtime and pace analysis — 2026-07-21

## Result

The completed mixed-state coordinator run provides enough evidence to separate backend request time from configured inter-row sleep, but not enough to reconstruct exact per-row wall-clock start/finish timestamps. Run `all_2026-07-21_193524` took 1 hour, 55 minutes, 37 seconds wall-clock. Of that, 37 minutes, 15 seconds was scheduled 15-second spacing across the 149 gaps between 150 sequential requests.

Changing the sequential spacing from 15 seconds to 5 seconds would reduce scheduled sleep to 12 minutes, 25 seconds and save 24 minutes, 50 seconds for the same 150-row shape. Holding observed backend time and other overhead fixed, the projected wall-clock duration is about 1 hour, 30 minutes, 47 seconds. This is a pace hypothesis for the next separately authorized run, not a reliability guarantee and not live authorization.

## Evidence inspected

Artifacts under `tmp/coordinator_150row_serial_live_direct_sdk_2026-07-21/` include:

- `run_metadata.json`;
- `raw_outputs.csv`;
- `failed_parses.csv`;
- `parsed_candidates.csv`;
- `cost_summary.json` / `cost_summary.csv`;
- `batch_cost_log.csv`;
- `sanitized_console.log`; and
- `prompt_preview.md`.

The old run predates `row_timing.csv` and input-hash resume metadata. Its raw ledger nevertheless has `Time Taken`, input/reasoning/output/total tokens, response-ID presence, success, error, and response fields for every returned row.

## Recovered pace measures

| Measure | Recovered value |
|---|---:|
| Wall start | `2026-07-21T23:35:17Z` |
| Wall finish | `2026-07-22T01:30:54Z` |
| Total wall time | 6,937 seconds (115m 37s) |
| Input rows / raw rows | 150 / 150 |
| Parseable rows | 149 |
| Failed rows | 1 timeout |
| Candidate-positive municipalities | 112 |
| Parseable-empty municipalities | 37 |
| Sum of per-row backend `Time Taken` | 4,693.886 seconds (78m 13.886s) |
| Mean backend time, all attempts | 31.293 seconds |
| Median backend time, all attempts | 29.020 seconds |
| Minimum / maximum backend time | 10.768 / 90.055 seconds |
| Mean successful request time | approximately 30.898 seconds |
| Mean wall time per attempted row | 46.247 seconds |
| Effective observed throughput | approximately 77.84 rows/hour |

The sole failure was Moreno Valley, CA (`cog_2025_161238`), with `timeout_or_capacity` and 90.055 seconds of recorded time. All 149 successful rows have response IDs and positive input, output, reasoning, and total token fields.

## Sleep decomposition

The runner slept only between requests, not after the final request. A 150-row sequential queue therefore has 149 configured sleep intervals.

| Pace | Calculation | Scheduled sleep |
|---|---:|---:|
| Prior setting | 149 × 15 seconds | 2,235 seconds (37m 15s) |
| New default test setting | 149 × 5 seconds | 745 seconds (12m 25s) |
| Estimated saving | 149 × 10 seconds | 1,490 seconds (24m 50s) |

The recorded backend-time sum plus scheduled prior sleep is 6,928.886 seconds, only 8.114 seconds below the recovered total wall time. That close reconciliation supports the estimate. Under the five-second setting, a simple fixed-backend projection is 5,447 seconds (90m 47s), about 99.14 rows/hour and 21.5% less wall time.

## What the old logs cannot measure

The pre-instrumentation artifacts do not preserve:

- exact wall-clock start and finish timestamps for each row;
- actual `asyncio.sleep` duration or scheduler jitter for each gap;
- whether any local per-row serialization/parsing time was hidden within the small residual overhead;
- hosted-search substep latency, proxy queueing, or server-side tool timing;
- intermediate throughput over time, as opposed to final batch throughput; or
- a byte-level input hash and terminal row-identity ledger suitable for fail-closed resume.

File modification timestamps are batch-level evidence only and should not be treated as per-row timing. The old failed-parse ledger can identify Moreno Valley, but the old directory is intentionally not eligible for the new safe resume path because it lacks `input_csv_sha256` and `row_timing.csv`.

## Recommendation

For the next separately authorized coordinator live scout:

1. retain direct SDK, `prompt_mode=minimal`, low search context, zero SDK retries, and `n_parallels=1`;
2. set `--sleep-between-prompts 5` explicitly so the pace is auditable even though five seconds is also the new default;
3. require a fresh output directory and inspect `row_timing.csv` plus the timing fields in `run_metadata.json` after completion;
4. stop on the existing two-consecutive no-ID/no-text/no-token transport-collapse rule, systematic parsing failure, or artifact/lifecycle loss;
5. if instability returns, do not add concurrency—raise sequential spacing to 8–10 seconds, then 15 seconds if needed; and
6. use the new resume planner only for a post-patch parent run with a matching input hash and terminal timing ledger. Never resume into the parent directory.

No live request, smoke request, source access, verification, ingestion, codification, or queue/coverage rebuild occurred during this analysis.
