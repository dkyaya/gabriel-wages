# Direct-SDK Timeout Implementation Notes

Date: 2026-07-23

Scope: offline inspection of the implementation at `bd5e259`.

## Current call path

`main()` prewrites the prompt preview, initial `run_metadata.json`, and planned `row_timing.csv`, then calls `run_direct_sdk_live_batch(...)` with `timeout=args.timeout`. The direct backend lazily loads the subscription credential without printing it and constructs:

```text
AsyncOpenAI(
    ...,
    timeout=httpx.Timeout(timeout),
    max_retries=max_retries,
)
```

For each row, the nested async `run_one()` records a wall-clock start timestamp and a monotonic start value, then directly awaits:

```text
client.responses.create(...)
```

At the inspected commit there is no `asyncio.wait_for`, `asyncio.timeout`, or equivalent outer per-row wall-clock deadline around that awaitable. The SDK/httpx timeout is the only call deadline.

## Existing response and exception behavior

- A completed response is translated by `direct_sdk_response_to_row()` into the historical raw schema, preserving response text, ID, token usage, status, sources, and elapsed time.
- Any ordinary exception raised back to `run_one()` is caught and translated by `_direct_sdk_failure_row()` into a returned row with no response text/ID/tokens, a sanitized exception entry, and elapsed time.
- The raw row later enters `parse_response_to_candidates()`. `classify_failure()` maps timeout/capacity text, connection errors, empty responses, and JSON errors into the failed-parse ledger.
- A failure with timeout/connection markers and no response text, ID, or output tokens is recognized by `is_direct_sdk_connection_failure_without_response()`.

The missing case is an awaitable that does not raise or return. No failure row can be constructed while control remains inside it.

## Timing and checkpoint path

Before live invocation, all selected timing records are written as `pending_live_attempt` / `pending`. Within `run_one()`, a returned response or exception creates an in-memory event containing:

- `prompt_started_at`;
- `prompt_finished_at`;
- elapsed seconds;
- actual/planned sleep;
- pacing mode and adaptive event.

After the full backend batch returns, `main()` parses raw rows, calls `finalize_row_timing()`, and rewrites `row_timing.csv`. Parseable rows become `completed_parseable`; failure rows become `failed`; rows not called after collapse become `stopped_before_request`.

Thus a hung first await prevents the in-memory event from becoming terminal and prevents the final timing rewrite. The planned ledger remains pending, exactly as observed in the stopped run.

## Consecutive-failure and adaptive behavior

The direct batch is sequential for authorized mixed-state live runs (`n_parallels=1`). After each returned chunk:

1. transport failures without response evidence increment `consecutive_connection_failures`;
2. any non-transport row resets that counter;
3. the adaptive controller observes the chunk as a transport failure or stable result;
4. adaptive mode backs off to the configured backoff level after one failure and to the maximum at its failure window;
5. after two consecutive no-evidence transport failures, every later row is synthesized as `stopped_before_request` and no additional request is made.

A terminal outer-timeout row with no ID/text/tokens naturally fits this path if its error marker is recognized as a transport timeout.

## Stopped rows

`_direct_sdk_stopped_row()` creates a raw failure-shaped row with no request evidence and an error marker `stopped_before_request_after_repeated_connection_errors`. Its timing event has blank started/finished/elapsed values. `finalize_row_timing()` records `live_attempted=no`, `success_status=stopped_before_request`, `parse_status=not_attempted`, and `failure_type=stopped_before_request`.

## Resume behavior

Resume reads a terminal parent `run_metadata.json` and `row_timing.csv`, proves the exact input hash, and identifies prior row outcomes by stable identity. `--skip-completed-municipality-ids` skips prior parseable rows and selects every nonparseable row. Failure-only resume normalizes authorized failure categories and can select timeouts. Nonterminal parents such as the stopped `bd5e259` directory are rejected.

An outer timeout should normalize to the existing `timeout` resume category while retaining a distinct raw/final failure type such as `outer_timeout`. This preserves the safe resume interface and makes the new guard auditable.

## Implementation requirements derived from inspection

- Retain `httpx.Timeout(timeout)` as the inner SDK/transport timeout.
- Wrap each `client.responses.create(...)` awaitable with an outer async deadline using the same configured timeout.
- Catch only the outer timeout separately and emit a sanitized, distinguishable terminal row.
- Preserve generic exception handling and successful response translation.
- Ensure timeout rows carry started/finished timestamps and elapsed time and are not left pending.
- Classify the row as `outer_timeout`, normalize it to resume category `timeout`, and count it in no-evidence transport collapse.
- Feed it to adaptive pacing as a transport failure.
- Preserve fixed pacing when adaptive mode is disabled.

## Files used

- `scripts/gabriel_state_source_scout.py`
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`
- `scripts/test_gabriel_state_source_scout_prompt.py`
- `scripts/run_scout_preflight_gate.py`
- `scripts/diagnose_direct_sdk_hosted_search_transport.py`
- `docs/analysis/scout_speed_stability_implementation_summary_2026-07-22.md`
- `docs/analysis/scout_speed_stability_next_wave_template_2026-07-22.md`
- the stopped-run and locked-input files listed in the companion failure audit.

No credential value or raw authorization configuration is reproduced here.
