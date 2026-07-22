# Tier 1 Coordinator 150-Row Serialized Live Result Review

Date: 2026-07-22

Run: `all_2026-07-22_152105`

Disposition: **incomplete and not merge-eligible; stopped after two consecutive connection failures.** See the companion stop report for the operational decision.

## Execution result

The coordinator ran exactly one direct-SDK live process against locked input SHA-256 `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`. It used `--state ALL --allow-mixed-states`, exact max/cap 150, `n_parallels=1`, five-second spacing, a 90-second timeout, and zero SDK retries.

- Locked rows: 150.
- Actually attempted rows: 2.
- Newly attempted rows: 2.
- Resume-skipped rows: 0; no resume ran.
- Stopped-before-request rows: 148.
- Parseable rows: 0.
- Candidate-positive municipalities: 0.
- Parseable-empty municipalities: 0.
- Connection-failed attempted municipalities: 2 (Oklahoma City OK and Phoenix AZ).
- Candidate rows: 0.
- Exit code: 2.
- Lifecycle: fail-closed terminal artifacts present; no parseable municipality outcome.

The 150-row raw/failure tables include 148 terminal placeholders so the locked ordering remains auditable. Those placeholders are not backend attempts and must not be described as timeout/failure-only municipalities.

## State and worker result

| State | Attempted | Parseable | Candidate-positive | Parseable empty | Connection failures | Candidate rows |
|---|---:|---:|---:|---:|---:|---:|
| OK | 1 | 0 | 0 | 0 | 1 | 0 |
| AZ | 1 | 0 | 0 | 0 | 1 | 0 |
| Other 35 locked states | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **2** | **0** | **0** | **0** | **2** | **0** |

Candidate rows by all 37 locked states are zero. Candidate-positive municipalities by all states are zero.

| Worker | Attempted | Stopped before request | Parseable | Candidate-positive | Candidate rows |
|---|---:|---:|---:|---:|---:|
| Worker 1 | 2 | 48 | 0 | 0 | 0 |
| Worker 2 | 0 | 50 | 0 | 0 | 0 |
| Worker 3 | 0 | 50 | 0 | 0 | 0 |

## Timing, usage, and prior-wave comparison

- Total elapsed: 5.841 seconds.
- Recorded sleep: 5.001 seconds.
- Mean attempted-request time: 0.102 seconds.
- Median attempted-request time: 0.102 seconds.
- Metadata effective rate: 1,232.688 attempted rows/hour. This is a mathematically valid two-row early-stop rate, not meaningful production throughput.
- Input/reasoning/output/total tokens: unavailable / 0 recorded.
- Actual and estimate-only cost: unavailable.

Wave 1 completed 150 rows in 6,937 seconds (115m37s), and Wave 2 completed 150 in 6,149.884 seconds (102m29.884s). This run cannot be compared as a completed runtime or yield experiment because it stopped after two transport failures. It provides no evidence for or against Tier 1 targeting yield, and it does not test whether five-second pacing is stable over a queue. The first failure preceded any inter-request sleep, so the collapse cannot reasonably be attributed to accumulated five-second pacing.

## Merge, dashboard, and priority decision

The run is not merge-eligible: zero parseable outcomes exist and 148 targets were never requested. The national queue/coverage builders were not run, and the existing ten national failure-only municipalities were not changed. No dashboard JSON refresh ran because accounting did not change.

Priority tiers were not rebuilt. They still reflect pre-Tier-1-Wave-1 status, as planned; more importantly, this failed parent contributed no successful scout evidence. A future priority refresh remains appropriate after 300–600 additional successful scouts or an explicit request for immediate priority-dashboard reconciliation.

No source was independently opened, verified, downloaded, ingested, codified, promoted into canonical data, or used as claim evidence.
