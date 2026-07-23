# Direct-SDK Outer Per-Row Timeout Fix Summary

Date: 2026-07-23

Status: **implemented and covered by offline mocked lifecycle tests.**

## What changed

The direct backend continues to construct `AsyncOpenAI` with the configured `httpx.Timeout(timeout)`. In addition, every per-row `client.responses.create(...)` awaitable is now wrapped by:

```text
asyncio.wait_for(..., timeout=timeout)
```

This outer deadline is in the scout runner rather than the SDK transport stack. If the SDK or hosted-search tool lifecycle does not return or raise within the configured row timeout, control returns to the runner through the outer timeout branch.

No prompt, model, search-hint, request-payload, serialization, retry, fixed-sleep, adaptive-setting, or successful-response translation behavior changed.

## Difference from the SDK/httpx timeout

The existing timeout is passed into the client and can govern connection, read, write, and pool behavior understood by the SDK/httpx stack. The stopped Post-PI request demonstrated that this was insufficient to bound the observed hosted-search lifecycle.

The new guard waits on the entire SDK response coroutine from the runner's event loop. It is independent of whether the inner client recognizes a particular phase as an HTTP read timeout. The same configured `--timeout` value is used for both layers so the CLI continues to expose one reviewed per-row deadline.

## Terminal timeout-row behavior

An outer expiry produces a normal raw direct-SDK failure row with:

- `Successful=false`;
- empty response text;
- empty response ID;
- empty input/output/reasoning/total token fields;
- empty web-search source list;
- measured elapsed seconds;
- sanitized error type `DirectSDKOuterTimeoutError`;
- sanitized message stating the configured outer per-row deadline.

Failure parsing classifies this row as `outer_timeout`, distinct from an SDK-raised `timeout_or_capacity`. The resume normalizer maps `outer_timeout` to the existing authorized category `timeout`, preserving backward-compatible resume selection.

Final `row_timing.csv` records the row as:

- `live_attempted=yes`;
- `success_status=failed`;
- `parse_status=failed`;
- `failure_type=outer_timeout`;
- nonblank prompt start and finish timestamps;
- nonblank elapsed seconds;
- no response ID or token usage.

It is therefore terminal and cannot remain `pending_live_attempt`.

## Adaptive pacing and collapse

`outer_timeout` error text is recognized by the existing no-response transport-failure predicate. Consequently:

- adaptive pacing observes the row as a transport failure and backs off;
- the consecutive no-ID/no-text/no-token counter increments;
- a successful or otherwise non-transport row still resets that counter;
- two consecutive outer timeouts trigger the existing fail-closed behavior;
- every later row is written as `stopped_before_request` without an SDK call.

Fixed sleep remains unchanged when `--adaptive-sleep` is absent.

## Offline test coverage

The no-network direct-SDK suite now includes a real never-returning coroutine under a fake `AsyncOpenAI` client. With a 0.02-second timeout it proves:

- `asyncio.wait_for` cancels the hanging call;
- elapsed row time tracks the configured deadline;
- two timeout rows receive `outer_timeout`;
- IDs, response text, sources, and all token fields remain empty;
- timing rows contain start/finish/elapsed evidence and are not pending;
- the first timeout produces adaptive `backoff`;
- the second timeout triggers collapse;
- the third row is `stopped_before_request` and the fake client is never called for it;
- timeout artifacts and sanitized logs contain no fixture credential;
- the fake client closes;
- a successful fake SDK response retains its response ID, text, token usage, hosted-search request shape, and fixed pacing behavior.

All calls are mocked; the test does not load a real credential or use the network.

## Stopped-run disposition

The `bd5e259` output remains immutable and quarantined. This code change does not retroactively assign a timeout to Lake Oswego or alter its all-pending ledger. That parent remains nonterminal, non-mergeable, and unsafe for resume.

The locked input remains:

`docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`

SHA-256:

`56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`

## Recommended next action

Under a separately authorized live task, use the generated retry prompt to:

1. prove the unchanged input hash and current eligibility;
2. use fresh plan-only, stronger-live-preflight, diagnostic-probe, dry-run, and full-live output directories;
3. run one serialized direct-SDK live scout with compact prompts, exact hints, adaptive `3/5/15/10/25/2`, 90-second inner and outer timeout, and zero SDK retries;
4. confirm any outer timeout becomes terminal near 90 seconds;
5. rebuild queue/coverage and then yield/dashboard only if the complete lineage is merge-eligible.

This implementation task made no live/API/model/hosted-search call and changed no source-discovery accounting.
