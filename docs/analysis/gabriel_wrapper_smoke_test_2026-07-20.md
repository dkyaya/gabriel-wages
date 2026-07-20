# GABRIEL Wrapper Smoke Test — 2026-07-20

## Plain-English result

The GABRIEL wrapper works in the same explicitly outbound-network-approved context in which the direct OpenAI SDK control already worked. One synthetic `gabriel.whatever()` call sent only `Reply with OK.` with web search disabled and returned `OK.` successfully. This closes the remaining wrapper-path question without running a municipality scout, a source-search prompt, ingestion, or `gabriel.codify`.

The direct SDK control had already returned HTTP 200 and `OK` using the Harvard `/v2` Responses endpoint, `gpt-5.4-nano`, and both the bearer and Harvard subscription headers. The wrapper result is consistent with that control: the same fixed base URL, effective `/responses` resource, model, and dual-header setup work through GABRIEL too.

Massachusetts must **not** be rerun automatically. The result means a locked MA rerun can be considered later, but only as a separately authorized research task. No request-shape or scout-code change is justified by this test.

## Scope and exact command

- Starting local commit: `7eaf280cb0200231223df5c715200a11eb0f81dc` (`Diagnose HUIT OpenAI request shapes`).
- Command: `MPLCONFIGDIR=/tmp/gabriel-wrapper-smoke-mpl-cache python scripts/diagnose_gabriel_wrapper_smoke_test.py`.
- Output directory: `tmp/gabriel_wrapper_smoke_test_2026-07-20/`.
- Prompt: exactly `Reply with OK.`.
- Wrapper: `gabriel.whatever()` with one prompt and `n_parallels=1`.
- Model: `gpt-5.4-nano`.
- Base URL unchanged: `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`.
- Effective model resource unchanged: `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`.
- Web search: `False`; tools: empty list; no municipality/source-search prompt.
- Retry setting: `max_retries=0`; timeout and maximum timeout: 30 seconds; dynamic timeout disabled.
- Authentication configuration: bearer API key plus `Ocp-Apim-Subscription-Key`; values were never printed or saved.

## Sanitized wrapper result

| Field | Result |
|---|---|
| Wrapper call | succeeded |
| Response text | `OK.` |
| Response ID | `resp_021b2434463f6862006a5e6e339a5481a1a25228a924aa5a8b` |
| GABRIEL row status | `Successful=True`; `Error Log=[]` |
| Input / output / reasoning tokens | 10 / 6 / 0 |
| Cost | `0.0000095` |
| Model-request time | 1.160 seconds |
| Whole helper elapsed time | 12.112 seconds |
| Wrapper exception | none |
| Python executable | `/Users/joachimjohnson/.pyenv/versions/3.11.7/bin/python` |
| Python / GABRIEL / OpenAI SDK / httpx | 3.11.7 / 1.1.8 / 2.41.0 / 0.28.1 |

The selected project `.env` supplied the Harvard subscription credential after a non-overriding load. Before that load, `HARVARD_SUBSCRIPTION_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` were absent from the process. The Harvard key was present in the selected `.env`; the other listed variables were absent there. No `.env` contents or credential values were emitted.

## Preliminary rate-limit probe

The wrapper did run GABRIEL 1.1.8's preliminary rate-limit probe before the successful model request. Instrumentation that records only paths and header names observed four probe attempts: two to `/responses` and two to `/chat/completions`. Every probe used `Authorization` and `Content-Type`; none included `Ocp-Apim-Subscription-Key`.

This confirms the pre-existing GABRIEL implementation detail identified in the July audit: its probe does not forward caller-supplied extra headers. It did not prevent this wrapper smoke test from succeeding, so it is not a blocker for the current locked configuration. It remains a focused upstream hardening topic, not a reason to alter the proven base URL, resource, model, header pair, or scout.

## Comparison and interpretation

| Control | Result |
|---|---|
| Direct OpenAI SDK, explicitly network approved | HTTP 200; `OK`; 10 input and 5 output tokens; 3.21 seconds |
| GABRIEL wrapper, explicitly network approved | successful `whatever()` row; `OK.`; 10 input, 6 output, 0 reasoning tokens; model-request time 1.160 seconds |

Both controls used the same Harvard base, `/responses` family, `gpt-5.4-nano`, and bearer-plus-subscription-header setup. The direct control proves the low-level SDK/proxy path; this smoke test proves GABRIEL's wrapper orchestration, including its async client path, can also complete now. The July 16–17 failures therefore most likely reflect missing effective outbound-network authorization at the time of those commands or a transient local/HUIT transport condition, rather than a currently reproducible GABRIEL wrapper, URL, model, or header defect.

## Next step

Do not run MA automatically. The recommended next move is a separately authorized, locked Massachusetts rerun using the unchanged established configuration. If a future GABRIEL failure occurs while a direct SDK control remains healthy in the same approved context, then perform a focused Heavy debugging pass on GABRIEL internals—especially the headerless rate-limit probe, async-client lifecycle, and exception reduction—without speculative scout-code changes.

## Evidence

- [Sanitized structured result](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp/gabriel_wrapper_smoke_test_2026-07-20/diagnostic_results.json)
- [Sanitized console log](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp/gabriel_wrapper_smoke_test_2026-07-20/sanitized_console.log)
- [Diagnostic helper](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/scripts/diagnose_gabriel_wrapper_smoke_test.py)
