# Tier 1 Coordinator 150-Row Live Retry Result Review

Date: 2026-07-22

Parent: commit `c6b3664`, run `all_2026-07-22_152105`

Retry: run `all_2026-07-22_155934`

Disposition: **stopped on repeated connection collapse; incomplete and not merge-eligible. No resume or national rebuild ran.**

## Parent and retry lineage

The parent used locked input SHA-256 `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`, attempted only Oklahoma City and Phoenix, received two connection errors without text/IDs/tokens, and stopped the other 148 rows before request. It produced no parseable or candidate rows and was never merged.

The fresh retry used the identical locked file and the new output directory `tmp/tier1_coordinator_150row_serial_live_retry_direct_sdk_2026-07-22_attempt1`. The runner has no standalone `--lineage-note`; its similarly named flag is resume-only and it refuses a non-empty new output directory. The lineage note was therefore prepared before live in a sibling staging file and copied unchanged into the completed retry artifacts after exit. The runner was not edited.

## Retry execution

- Locked/input/raw/timing rows: 150 / 150 / 150 / 150.
- Actual backend requests: 2.
- Newly attempted rows: 2.
- Resume-skipped rows: 0; no resume ran.
- Stopped-before-request rows: 148.
- Parseable rows: 0.
- Candidate-positive municipalities: 0.
- Parseable-empty municipalities: 0.
- Connection-failed attempted rows: 2.
- Candidate rows: 0.
- Response IDs/text/token-bearing outcomes: 0.
- Exit code: 2.
- Execution status: `completed_no_parseable_outcome`; `model_response_succeeded=false`.

Oklahoma City, OK (`cog_2025_209170`) failed after 0.196 seconds. Phoenix, AZ (`cog_2025_207536`) failed after 0.005 seconds. Both are infrastructure/transport outcomes, not source-discovery failures. The other 148 rows were not attempted and are not failures.

## State and worker results

| State | Attempted | Parseable | Candidate-positive | Parseable empty | Connection failures | Candidate rows |
|---|---:|---:|---:|---:|---:|---:|
| OK | 1 | 0 | 0 | 0 | 1 | 0 |
| AZ | 1 | 0 | 0 | 0 | 1 | 0 |
| Other 35 locked states/DC | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **2** | **0** | **0** | **0** | **2** | **0** |

All 37 states/DC have zero candidate rows and zero candidate-positive municipalities.

| Worker | Attempted | Stopped before request | Parseable | Candidate-positive | Candidate rows |
|---|---:|---:|---:|---:|---:|
| Worker 1 | 2 | 48 | 0 | 0 | 0 |
| Worker 2 | 0 | 50 | 0 | 0 | 0 |
| Worker 3 | 0 | 50 | 0 | 0 | 0 |

## Timing and cost

- Total elapsed: 5.800 seconds.
- Recorded sleep: 5.001 seconds.
- Mean attempted-request time: 0.101 seconds.
- Median attempted-request time: 0.101 seconds.
- Metadata effective rate: 1,241.280 attempted rows/hour. This two-request early-stop arithmetic is not a production throughput estimate.
- Recorded input/reasoning/output/total tokens: zero/unavailable.
- Actual and estimate-only live cost: unavailable.

Wave 1 completed 150 rows in 115m37s and Wave 2 in about 102m30s. This retry cannot be compared as a completed runtime or yield test. It provides no evidence about whether cross-state Tier 1 targeting improves candidate yield and no sustained test of five-second pacing. The repeated subsecond first-request failure after a passing no-search smoke is consistent with an unstable hosted-search/transport path, not accumulated queue pacing; this is an operational inference, not a diagnosed external root cause.

## Resume, merge, dashboard, and priority decisions

No resume ran. The retry has zero successful parseable IDs, so skip-completed resume semantics would again select all 150 rows. More importantly, the identical immediate-collapse pattern has now occurred in both the parent and the fresh retry. Do not launch another automatic retry. Any future full-input retry requires separate authorization and evidence that the hosted-search transport path has changed or stabilized.

The retry is not merge-eligible. Queue/coverage builders did not run; no coverage accounting changed. National state remains 1,009 queue rows, 504 successful municipalities, 391 candidate-positive, 113 parseable-empty, and ten failure-only. Oklahoma City and Phoenix remain `not_scouted` and are not added as national failure-only targets from these infrastructure attempts.

Dashboard JSON was not refreshed because accounting was unchanged. Priority tiers were not rebuilt; they continue to reflect pre-Tier-1-Wave-1 coverage. A future priority refresh remains appropriate after 300–600 additional successful scouts, not after this zero-outcome retry.

No URL was independently opened/downloaded; no source was verified, ingested, codified, promoted, or used for claims.
