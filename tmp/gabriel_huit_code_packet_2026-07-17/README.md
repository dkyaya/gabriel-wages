# GABRIEL / Harvard Proxy Failure Code Packet

## Summary

This packet contains the actual local code path and sanitized output from a one-prompt synthetic GABRIEL smoke test that returned `['Connection error.']`. It was prepared for HUIT to diagnose the Harvard proxy/API path. It contains no `.env` file, credential, subscription-key value, cookie, token, local key file, shell history, cache file, or research/corpus data.

## Exact diagnostic invocation

```bash
python tmp/gabriel_proxy_connection_retest_2026-07-17/gabriel_proxy_smoke_test.py
```

The script invokes `gabriel.whatever(...)` with one synthetic JSON-only prompt and these relevant settings:

| Setting | Value |
|---|---|
| Returned error | `['Connection error.']` |
| Endpoint/base URL | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` |
| Model | `gpt-5.4-nano` |
| `web_search` | `false` |
| Prompts | `1` |
| `n_parallels` | `1` |
| Timeout / max timeout | `90` / `90` seconds |
| Response ID | absent |
| Response text | absent |
| Output tokens | absent (zero output recorded) |
| Input tokens | `13` |
| Cost | `2.6e-06` |
| `.env` found | `true` |
| `HARVARD_SUBSCRIPTION_KEY` present after local load | `true` (value not included) |

## Included files

- `tmp/gabriel_proxy_connection_retest_2026-07-17/gabriel_proxy_smoke_test.py` — the exact synthetic diagnostic script run above. Its `main()` function loads the local environment, temporarily configures `OPENAI_API_KEY`/`OPENAI_BASE_URL`, then calls `gabriel.whatever(...)` with `base_url=HARVARD_PROXY_BASE_URL` and the Harvard subscription header. It records the returned row/error in metadata.
- `scripts/gabriel_state_source_scout.py` — the actual project scout runner. Its `run_live_batch()` function constructs the equivalent live proxy call path: it loads the local environment and passes `api_key`, `base_url`, and `extra_headers` into `gabriel.whatever(...)`. This file is included for comparison with the production scout path; no scout was run for this packet.
- `scripts/test_gabriel_state_source_scout_prompt.py` — the no-network helper test for the runner’s prompt and row-outcome interpretation. It confirms that process completion is not confused with a successful model response.
- `smoke_test_metadata_redacted.json`, `smoke_test_console_redacted.log`, and `raw_outputs.csv` — sanitized failure artifacts. The metadata and console filenames use `_redacted` because absolute local filesystem/cache paths were removed; no secret values were present.

The scout runner does not import another project-local Python module for the proxy call path. Its relevant non-standard dependencies (`gabriel`, `dotenv`, and `pandas`) are external packages and are not bundled here.

## Error recording

The smoke script reads the first returned GABRIEL dataframe row and writes the `Error Log`, response-ID presence, response presence, token fields, cost, and `model_response_succeeded` into `smoke_test_metadata_redacted.json`. The raw returned row is preserved in `raw_outputs.csv`. In this run, `gabriel.whatever(...)` returned a dataframe row rather than raising, but the row had `Successful=False`, blank response fields, and `['Connection error.']`.

## What HUIT should check

1. Trace a request to the listed `ais-openai-direct/v2` endpoint using the same model and subscription-key authentication scheme; the client does not receive an HTTP status or provider-specific error.
2. Check proxy routing, TLS/network transport, subscription-key authentication at the proxy, and upstream model availability for `gpt-5.4-nano`.
3. If server-side diagnostics identify a rejected or failed request, provide the HTTP/proxy error category so the client can distinguish authentication, routing, rate-limit, backend availability, and timeout failures.

No Massachusetts/state scout, GABRIEL/model/API call, ingestion, codification, or data/corpus operation was run while creating this packet.
