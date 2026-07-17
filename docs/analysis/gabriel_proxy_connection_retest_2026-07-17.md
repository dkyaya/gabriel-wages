# GABRIEL / Harvard Proxy Connection Retest

Date: 2026-07-17
Scope: one synthetic infrastructure-only smoke test; no research scout, Massachusetts rerun, source verification, ingestion, codification, or corpus/data change

## Why this retest was run

HUIT reported that the API is working on its side and asked for the current returned error. The prior 2026-07-16 diagnosis found only empty `Connection error.` rows, including on a synthetic no-search request. This retest provides a fresh, tightly bounded observation from the same local proxy/key-loading path without issuing any municipal or research query.

## Result

The smoke test **failed**. It does not meet the required connectivity-success condition: the one returned GABRIEL row has no response text, no response ID, and `model_response_succeeded=false`; its error is exactly `['Connection error.']`.

The exact diagnostic invocation was:

```bash
python tmp/gabriel_proxy_connection_retest_2026-07-17/gabriel_proxy_smoke_test.py
```

It sent one synthetic JSON-only prompt through `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`, with model `gpt-5.4-nano`, `n_parallels=1`, `web_search=False`, low search context, and 90-second timeout/max-timeout. It made no source-discovery request.

## Error details for HUIT

| Field | Current result |
|---|---|
| Exact returned error | `['Connection error.']` |
| Response ID | absent |
| Response text | absent |
| Model-response success | `false` |
| Input tokens | `13` |
| Reasoning / output tokens | absent / absent |
| Recorded cost | `2.6e-06` |
| Model | `gpt-5.4-nano` |
| Endpoint/base URL | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` |
| Local configuration presence | project `.env` found; Harvard subscription-key variable present after local load; no values recorded |

GABRIEL also logged: `1 API connection errors encountered, indicating network instability or bandwidth limitations`. The local Python process successfully imported and invoked GABRIEL, and a row was returned/charged, but no model response was received. The evidence therefore most strongly indicates a proxy/API transport-path failure. It does **not** identify the subcause: HUIT should check proxy routing/availability and any upstream service path. The generic client error cannot rule authentication, backend model availability, or an intermediary network failure in or out. It does not resemble a parser failure (there is no response to parse), rate limit, or ordinary timeout; no HTTP status or provider-specific auth/model error was surfaced.

The Matplotlib cache warnings in the console log are local, unrelated import/cache warnings and are not the failed API request.

## Massachusetts status and next step

Connectivity does **not** appear restored. Do not run Massachusetts, another state scout, source verification, ingestion, `gabriel.codify`, or claim work yet.

If a future synthetic test succeeds and Massachusetts is separately authorized, use a fresh output directory and this exact locked rerun command:

```bash
python scripts/gabriel_state_source_scout.py \
  --state MA \
  --municipalities-csv docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-17 \
  --prompt-mode minimal \
  --max-prompts 8 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live
```

That command is a recommendation only. It was not run here and must remain a separately authorized, scout-stage action.

## Preserved artifacts

All retest artifacts are under `tmp/gabriel_proxy_connection_retest_2026-07-17/`: the diagnostic script, raw GABRIEL row, non-secret metadata, console log, and requested validation/audit outputs.
