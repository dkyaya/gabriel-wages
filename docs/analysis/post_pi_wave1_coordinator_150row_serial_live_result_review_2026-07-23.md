# Post-PI Wave 1 Coordinator 150-Row Serialized Live Result Review

Date: 2026-07-23

Disposition: **STOPPED — `merge_eligible=false`; national accounting is unchanged.**

## Run identity and gates

- Official output directory: `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1`
- Run ID: `all_2026-07-23_105131`
- Locked input SHA-256: `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Worker relay assessment: passed for all three relays.
- Locked 150-row input audit: passed.
- Stronger live preflight gate: passed.
- One-row probe: parseable and quarantined; excluded from all official accounting.
- Fresh 150-row dry-run review: 150/150 passed.
- Prompt mode: compact.
- Deterministic search hints: attached and matched 150/150.
- Adaptive sleep/backoff: enabled with min/base/max/backoff `3/5/15/10` and stability/failure windows `25/2`.
- Serialization: `n_parallels=1`; direct-SDK retries zero.
- Resume used: no.

## Stop condition

The sole authorized live process created the complete prompt preview, lifecycle metadata, and a 150-row timing ledger, then entered the first direct-SDK hosted-search request. That request did not return or checkpoint after more than five minutes—several multiples of the configured 90-second request timeout. The coordinator stopped the process with SIGINT as an unbounded lifecycle stall.

The preserved raw runner metadata remains at `execution_status=live_started`, `live_attempted=true`, and `backend_call_returned=false`. It should not be reinterpreted as a completed row result. No response ID, text, token usage, parser result, candidate handoff, failed-parse ledger, cost record, or row-level completion was emitted.

## Outcome counts

| Measure | Count | Interpretation |
|---|---:|---|
| Locked/in-scope rows | 150 | Exact coordinator input |
| Backend request initiated | 1 | Rank 1 entered the SDK call; no returned lifecycle evidence |
| Checkpointed attempted rows | 0 | No timing row advanced beyond pending |
| Completed rows | 0 | No response completed |
| Parseable rows | 0 | None |
| Candidate-positive municipalities | 0 | None |
| Parseable-empty municipalities | 0 | None |
| Official timeout/failure-only municipalities | 0 | The stalled row is not promoted into failure-only accounting |
| Abandoned in-flight row | 1 | Rank 1, no returned result |
| Stopped before request | 149 | Ranks 2–150 were never reached |

All 150 records in the preserved `row_timing.csv` remain `success_status=pending_live_attempt` and `parse_status=pending`; the in-flight/never-reached distinction is therefore documented in this review and `stop_note.txt`, not fabricated into the immutable runner ledger.

## Candidate counts

No candidate artifact exists. Candidate-row and candidate-positive-municipality counts are zero for every state and every worker:

- States: CT 0, FL 0, IA 0, MA 0, MI 0, NV 0, OH 0, OR 0, WA 0, WI 0.
- Workers: worker_1 0, worker_2 0, worker_3 0.

These zeroes describe this stopped run only; they are not findings that the municipalities lack sources.

## Usage, timing, and adaptive behavior

- Captured model token usage: unavailable; no response returned.
- Captured or estimated run cost: unavailable; no cost log was emitted.
- Prompt/input-token comparison with Tier 1 Wave 2: unavailable because this run returned no usage record.
- Approximate wall time before coordinator stop: about 5 minutes 49 seconds, from lifecycle metadata initialization at 10:51:31 ET to the approximately 10:57:20 ET interruption.
- Total checkpointed row elapsed time: unavailable.
- Total actual sleep: 0 seconds; the runner never reached an inter-row sleep.
- Average/median row time: unavailable.
- Effective completed rows/hour: 0.
- Adaptive sleep actually used: none.
- Backoff events: 0.
- Step-down events: 0.

The prior completed-run runtimes remain:

| Comparator | Runtime |
|---|---:|
| Wave 1 live | 115m 37s |
| Wave 2 live | 102m 30s |
| Tier 1 Wave 1 live | 112m 03.519s |
| Tier 1 Wave 2 live | 95m 38.638s |

The stopped run is not throughput-comparable to those completed waves. Compact prompts, hints, and adaptive pacing passed all offline gates and the bounded one-row probe, but their 150-row stability cannot be evaluated from a first-request stall.

## Merge and resume decision

`merge_eligible=false`.

- No queue, coverage, dashboard, or yield-learning rebuild occurred.
- No scout coverage accounting changed.
- No municipality from this run is marked candidate-positive, parseable-empty, or failure-only.
- The diagnostic probe remains quarantined and is not counted.
- Resume was not used because there are zero completed municipality IDs and no parseable partial artifacts. A skip-completed resume would select the entire input and would therefore be functionally a new full run, not a bounded continuation.
- The stopped output directory is immutable and must never be reused.
- A future retry should use the full unchanged locked input in a fresh output directory, but only after a separate diagnosis demonstrates that the direct-SDK request timeout is actually enforced around the hosted-search lifecycle.

## Checkpoint status and limitations

Official progress remains **794/2,000 scout-covered municipalities**, leaving approximately **1,206**. The planning estimate remains **8–9 successful 150-row waves**, depending on parseable yield.

The failure occurred before any official row outcome, so this review supports no source-availability, wage-gap, mechanism, causal, or regression inference. No source verification, URL opening outside the hosted-search request path, extraction, ingestion, rating, `gabriel.codify`, wage-gap calculation, or candidate promotion occurred.
