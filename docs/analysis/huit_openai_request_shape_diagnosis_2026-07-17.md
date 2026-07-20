# HUIT OpenAI Request-Shape Diagnosis — 2026-07-17

## Plain-English summary

The smallest request shape that most closely matches the scout **works from this repository environment when outbound network access is explicitly authorized**. One OpenAI SDK `responses.create` call sent the harmless prompt `Reply with OK.` to the Harvard AIS proxy using the established `/v2` base, `gpt-5.4-nano`, and both the bearer and Harvard subscription headers. It returned HTTP 200, a completed Responses object, a response ID, and `OK` in 3.21 seconds.

Exactly **one** diagnostic request was sent. The script then stopped, as required. Direct HTTP Responses, subscription-only, and Chat Completions variants were not needed and were not sent.

This successful control rules out the following as current causes in the explicitly network-approved context:

- an invalid effective Harvard key;
- an unsupported `gpt-5.4-nano` model name;
- a bad `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` base;
- a missing or unsupported `/responses` resource;
- a conflict caused merely by sending both `Authorization` and `Ocp-Apim-Subscription-Key`;
- a basic incompatibility in OpenAI SDK 2.41.0 Responses serialization/parsing;
- an `OPENAI_BASE_URL` or standard proxy-variable override in the current process or selected `.env`.

The result strongly supports the earlier working-vs-broken report's leading diagnosis: the failed MA and synthetic GABRIEL commands likely ran without effective outbound-network access, or encountered a transient local network condition. It does **not** yet prove that the full GABRIEL wrapper works today, because this successful control intentionally removed GABRIEL and web search. If the historical commands did have network approval, GABRIEL orchestration or a transient service/network event remains the boundary to test.

Do not change the scout's base URL, route family, header pair, or model based on this result.

## Scope and safety controls

- Starting local commit: `dd53c4de98a84af37c9fec8f73bc674c4c9982ff` (`Compare working and failed GABRIEL scout runs`).
- Prompt: exactly `Reply with OK.`.
- Model: `gpt-5.4-nano`.
- Tools: omitted/disabled.
- Web search: omitted/disabled.
- Timeout: 30 seconds.
- OpenAI SDK retries: 0, preventing an SDK retry from consuming hidden calls.
- Planned diagnostic shapes: 4.
- Independent hard request ceiling: 6.
- Requests actually made: 1.
- Stop condition: first HTTP success.
- Research scout, MA scout, source ingestion, and `gabriel.codify`: not run.
- Credential values, request headers, `.env` contents, tokens, and cookies: not logged.

The diagnostic implementation is `scripts/diagnose_huit_openai_request_shapes.py`. Sanitized machine-readable and console evidence is under `tmp/huit_openai_request_shape_diagnosis_2026-07-17/`.

## Sanitized effective configuration

| Item | Sanitized result |
|---|---|
| Project `.env` | present and selected |
| Parent `.env` | absent |
| `HARVARD_SUBSCRIPTION_KEY` before `.env` load | absent |
| `HARVARD_SUBSCRIPTION_KEY` in selected `.env` | present |
| Effective `HARVARD_SUBSCRIPTION_KEY` | present |
| `OPENAI_API_KEY` before load / `.env` / effective | absent / absent / absent |
| `OPENAI_BASE_URL` before load / `.env` / effective | absent / absent / absent |
| `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY` | all absent before load, in `.env`, and effective environment |
| Effective base URL | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` |
| Effective resource URL | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses` |
| Model requested | `gpt-5.4-nano` |
| Model returned | `gpt-5.4-nano-2026-03-17` |
| Python | 3.11.7 |
| OpenAI SDK | 2.41.0 |
| httpx | 0.28.1 |
| python-dotenv | 1.2.1 |

The helper uses the same `.env` selection and non-overriding load behavior as the scout: project `.env` first, then parent `.env`, with `override=False`. The current process had no ambient Harvard key before loading, so the successful call used the project `.env` credential rather than an exported override.

## Request shapes considered and tested

| Label | Shape | Purpose | Outcome |
|---|---|---|---|
| A | OpenAI SDK `responses.create`; base `…/v2`; bearer plus subscription header | Closest minimal control for the scout's actual SDK request while removing GABRIEL and web search | **Tested: HTTP 200, completed, `OK`** |
| B + E | Direct HTTP `POST …/v2/responses`; bearer plus subscription header | Hold route, headers, model, and payload family fixed while removing SDK serialization | Not sent: A already proved the SDK form works |
| B + D | Direct HTTP `POST …/v2/responses`; subscription header only | Determine whether bearer authorization conflicts with the HUIT gateway | Not sent: A proved the dual-header form is accepted |
| C | Direct HTTP `POST …/v2/chat/completions`; bearer plus subscription header | Test Chat Completions only if both Responses variants fail | Not sent: Responses succeeded |
| F | Alternate model | Test only if artifacts suggest `gpt-5.4-nano` is unsupported | Not justified and not sent: Texas used the same model successfully, and A confirms it works now |

Requirements B and E describe the same direct Responses request once the required header mode is made explicit, so the plan combined them into one possible request rather than duplicating a call. The same logic combines B and D for the subscription-only variant.

## Exact sanitized result

| Field | Result |
|---|---|
| Timestamp | 2026-07-20 18:30:39 UTC; response dated 18:30:42 UTC |
| Shape | `A_sdk_responses_both_headers` |
| Request number | 1 of a hard maximum of 6 |
| Method/resource | OpenAI SDK `responses.create` → `POST /ais-openai-direct/v2/responses` |
| Header mode | bearer plus `Ocp-Apim-Subscription-Key`; values not logged |
| Status | HTTP 200 |
| Response object status | `completed` |
| Output | `OK` |
| Response ID | `resp_0e3dd466c96cbeb0006a5e695170ec81a0b6ee04e878513d1b` |
| Safe request-trace header | `x-request-id: 92eae6fe-2e32-422f-814d-c2a977283211` |
| Tokens | 10 input, 5 output, 15 total |
| Elapsed time | 3.21 seconds |
| Exception type/message | none / none |

No failed request exists in this new run, so there is no failure status or exception to report. The three unexecuted shapes are recorded as skipped—not failed—in both sanitized output files.

## Direct answers

### Does SDK usage fail while direct HTTP succeeds?

No. SDK usage succeeds. Because the first SDK call returned HTTP 200, a direct HTTP control would not isolate a current failure and was skipped under the early-stop requirement.

### Do Responses requests fail while Chat Completions succeeds?

No such contrast exists. Responses succeeds, so Chat Completions was unnecessary and not called. This is positive evidence for keeping the scout on Responses, not evidence about whether Chat Completions also works.

### Does header format matter?

The dual-header format is accepted: bearer authorization plus `Ocp-Apim-Subscription-Key` returned HTTP 200. The test does not claim both are individually necessary because the subscription-only variant was correctly skipped after success. It does rule out the theory that merely including both headers breaks the current request.

### Does the model name matter?

`gpt-5.4-nano` is supported on this route now. The service resolved it to `gpt-5.4-nano-2026-03-17` and returned a completed response. A model variant would have added cost and confounded the request-shape test, so none was sent.

### Does the base URL or request path need a fix?

No. The known configuration—base ending in `/v2`, with the SDK appending exactly one `/responses`—worked. There is no evidence supporting `/v1`, Chat Completions, an embedded `/responses` base, or any path rewrite.

## Relationship to the failed GABRIEL runs

The new success uses the same decisive low-level inputs as the scout:

- project `.env` Harvard credential;
- base `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`;
- effective `/v2/responses` resource;
- `gpt-5.4-nano`;
- bearer plus subscription-key headers;
- OpenAI SDK 2.41.0.

It differs intentionally by removing GABRIEL, tools, web search, municipality prompts, CSV inputs, parallel orchestration, checkpoint files, and retries. Those removals make it a clean infrastructure control rather than a scout.

The preserved failed smoke tests still went through `gabriel.whatever()`. They returned generic `Connection error.` rows with no HTTP status, response ID, or output. The current SDK control instead reached HUIT and completed. That contrast narrows the remaining explanations, but it is not a simultaneous A/B test: the failed wrapper calls occurred on July 16–17 and this successful SDK call occurred July 20 in an explicitly network-approved command context.

## Ranked remaining local causes

1. **Earlier GABRIEL diagnostics lacked effective outbound-network authorization.** This is now the strongest explanation. The current explicitly network-approved SDK call succeeds immediately with the same route/key/model/header setup, and the earlier comparison found that only the successful Texas command had a retained network-approved invocation. The earlier failures ended before any HTTP response or ID.
2. **GABRIEL-specific orchestration or client behavior.** Still untested today. The wrapper's actual Responses request should be equivalent, but GABRIEL adds a rate-limit probe, async orchestration, result/checkpoint handling, and its own error reduction. The prior audit found that its preliminary rate-limit probe does not forward the Harvard subscription header, although the actual model request does.
3. **A transient local network, HUIT proxy, or upstream availability event on July 16–17.** The new result establishes current health, not uninterrupted historical health. HUIT may also have changed or restored something between the failed and successful timestamps.
4. **A historical ambient Harvard key override.** Currently contradicted: the ambient variable was absent and the project `.env` key succeeded. It remains only a retrospective possibility because older smoke metadata did not record ambient-before-load status.

## What is now ruled out

- Current invalidity of the project `.env` Harvard key.
- Current lack of route support for `POST …/v2/responses`.
- Current lack of model support for `gpt-5.4-nano`.
- A current OpenAI SDK 2.41.0 serialization or Responses parsing defect.
- Dual-header rejection by the HUIT proxy.
- An effective current `OPENAI_BASE_URL` redirect.
- A current standard `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` override.
- Need to switch to Chat Completions or a model variant as a speculative fix.
- Municipality prompt, CSV shape, parser, or web-search content as a cause of this minimal path; none was present.

## What remains unknown

- Whether `gabriel.whatever(web_search=False)` succeeds today under the same explicitly network-approved execution context.
- Whether the earlier MA/smoke commands actually had outbound-network approval.
- Whether HUIT saw any of the July 16–17 failed requests.
- Whether HUIT or an upstream service recovered between July 17 and July 20.
- Whether subscription-only Responses or Chat Completions also works. Those are no longer relevant to fixing the established Responses path and were intentionally not tested.

## Recommended local fix and exact next step

The recommended local fix is operational, not a scout code change:

1. Keep the fixed `/v2` base, Responses family, `gpt-5.4-nano`, and dual-header construction unchanged.
2. Require explicit outbound-network authorization for every future HUIT diagnostic or authorized live job. Record that execution fact in sanitized run metadata so an infrastructure-approved call cannot be confused with one blocked by the command sandbox.
3. Do not resume MA or another research scout yet.

The exact next diagnostic, if separately authorized, is **one** synthetic `gabriel.whatever()` request with prompt `Reply with OK.`, `web_search=False`, `n_parallels=1`, no retry, no research input, and the same base/model/header settings, executed with explicit outbound-network permission. Capture the nested exception if it fails. Interpret it as follows:

- GABRIEL succeeds: prior incident was execution-context or transient transport/service state; no request-shape code fix is needed.
- GABRIEL fails while this SDK control succeeds in the same context: isolate the wrapper, beginning with its rate-limit probe and async client construction; do not alter the proven URL/model/header setup.

Only after a synthetic GABRIEL success, and only under separate authorization, should any MA research run be considered.

## Evidence

- Sanitized result JSON: `tmp/huit_openai_request_shape_diagnosis_2026-07-17/diagnostic_results.json`
- Sanitized console log: `tmp/huit_openai_request_shape_diagnosis_2026-07-17/sanitized_console.log`
- Diagnostic implementation: `scripts/diagnose_huit_openai_request_shapes.py`
- Working-vs-broken audit: `docs/analysis/gabriel_working_vs_broken_scout_comparison_2026-07-17.md`
- URL/base audit: `docs/analysis/gabriel_url_baseurl_audit_2026-07-17.md`
- Current scout call path: `scripts/gabriel_state_source_scout.py`, `run_live_batch()`
- Prior failed GABRIEL retest: `tmp/gabriel_proxy_connection_retest_2026-07-17/`
- Successful Texas control: `tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16/`

No secret value is included in this note or its referenced diagnostic outputs.
