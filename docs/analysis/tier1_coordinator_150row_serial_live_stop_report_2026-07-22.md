# Tier 1 Coordinator 150-Row Live Stop Report

Date: 2026-07-22

Run: `all_2026-07-22_152105`

Disposition: **stopped on connection collapse; incomplete and not merge-eligible. Do not resume automatically.**

## Trigger

The single authorized coordinator process started with the exact locked input and required direct-SDK settings. Its first two requests both failed at the transport layer with no response text, response ID, or token usage:

1. Oklahoma City, OK (`cog_2025_209170`), Worker 1 rank 1: connection error after 0.198 seconds.
2. Phoenix, AZ (`cog_2025_207536`), Worker 1 rank 2: connection error after 0.005 seconds.

The runner applied the required two-consecutive-failure stop condition. The 5.001-second configured interval followed the first request; no request was sent for rows 3–150. Those 148 rows are recorded as `stopped_before_request`, not failed municipality scouts.

## Preserved lifecycle

- Process exit code: 2.
- Locked-input SHA-256: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`.
- Raw/timing ledger rows: 150/150, preserving input order.
- Actually attempted rows: 2.
- Parseable outcomes: 0.
- Candidate rows: 0.
- Response IDs/text/token-bearing rows: 0.
- Remaining stopped-before-request rows: 148.
- Metadata status: `completed_no_parseable_outcome`; `live_attempted=true`; `backend_call_returned=true`; `model_response_succeeded=false`.
- Total elapsed: 5.841 seconds; recorded sleep 5.001 seconds.
- Cost/token estimate: unavailable because the two failed requests returned no usage.

The runner's `live_succeeded=true` field means its backend routine returned a complete dataframe after applying the fail-closed stop; it does **not** mean any municipality response succeeded. The authoritative success fields are zero backend-success rows, zero nonempty/parseable outcomes, `model_response_succeeded=false`, and the explicit failure reason.

## Resume decision

No resume ran. Although the parent has complete lineage artifacts, the failure is the exact connection-collapse stop condition, there are no completed municipality IDs to preserve, and the task authorized only one coordinator live process. A fresh resume with `--skip-completed-municipality-ids` would still select all 150 rows and would amount to an immediate full rerun during an unstable transport condition. That is neither safe nor within this task's one-process limit.

Any future retry requires separate authorization, a fresh no-search smoke, a fresh output directory, the same input hash, and explicit lineage to this parent. It should occur only after the transport route is plausibly stable; it must not write into this output directory.

## Accounting and protection

National queue/coverage builders did not run. Dashboard JSON and priority tiers were not refreshed. Current national accounting therefore remains 1,009 queue rows, 504 successful municipalities, 391 candidate-positive, 113 parseable-empty, and ten failure-only municipalities. Oklahoma City and Phoenix are not newly counted as covered or nationally failure-only from this unmerged run.

The pre/post SHA-256 values for `data/contracts.csv`, `data/city_coverage.csv`, and the tracked corpus file set are identical. No verification, ingestion, codification, canonical promotion, claim use, remote action, or secret exposure occurred.
