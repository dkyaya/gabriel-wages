# Direct SDK Scout Backend

Date: 2026-07-20

Stage: infrastructure implementation and one synthetic no-search smoke test only. No municipality scout, source verification, ingestion, `gabriel.codify`, canonical-data edit, or claim-stage promotion occurred.

## Plain-English result

The state-source scout now has an opt-in live backend that sends its prompts directly through the OpenAI SDK Responses API instead of depending on GABRIEL's wrapper orchestration. The historical GABRIEL backend remains the default, and dry-run behavior is unchanged. For the Harvard HUIT proxy, use `--live-backend direct-sdk` when a future research scout is separately authorized, especially after a GABRIEL preflight fails.

The new path passed exactly one synthetic live test. It sent `Reply with OK.` to `gpt-5.4-nano` through `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`, with the bearer and `Ocp-Apim-Subscription-Key` header names, no tools or web search, zero SDK retries, and a 30-second timeout. It returned `OK.`, a response ID, 10 input tokens, 0 reasoning tokens, and 6 output tokens. Credential values and `.env` contents were not logged.

This makes the direct transport ready for a separately authorized, tightly bounded NJ live scout. It does not establish how the direct backend performs with hosted web search or with the three municipal prompts, because this task intentionally did not run either.

## Why the GABRIEL wrapper is unreliable here

The failed NJ preflight produced a GABRIEL row with `Successful=False`, empty response text, no response ID, no output tokens, and `Error Log=['Connection error.']`. The preserved instrumentation also showed that GABRIEL 1.1.8 ran a preliminary rate-limit probe before its model request. That probe attempted both `/responses` and `/chat/completions` using `Authorization` and `Content-Type`, but omitted `Ocp-Apim-Subscription-Key`.

Inspection of the installed package confirmed that this is not exposed as a supported configuration option:

- `get_all_responses()` calls `_get_rate_limit_headers(model, base_url=base_url)` for ordinary runs.
- `_get_rate_limit_headers()` accepts only `model` and `base_url` and constructs its own two-header dictionary.
- Caller `extra_headers` are forwarded to the actual model request but not to this preliminary probe.
- The only local ways to suppress or alter the probe would be to monkey-patch a private installed-package function or replace GABRIEL's response function, which would be brittle and would still leave GABRIEL's async client lifecycle, retries, checkpoint orchestration, and generic exception reduction on the critical path.

No installed package file was edited. A private-function monkey-patch was not applied because bypassing the wrapper is smaller at the project boundary, easier to test, and uses the already proven SDK request shape directly.

## Evidence supporting the direct SDK path

The earlier request-shape diagnosis sent one direct OpenAI SDK `responses.create` request with the same HUIT `/v2` base, `gpt-5.4-nano`, and dual-header configuration. It returned HTTP 200, a completed response, a response ID, and `OK`. That ruled out the base URL, `/responses` resource, model name, OpenAI SDK 2.41.0, and dual-header shape as current low-level problems.

The new backend smoke test repeated that decisive transport shape through the production scout module rather than the older standalone diagnosis helper. Its artifacts are under `tmp/direct_sdk_scout_backend_smoke_test_2026-07-20/`:

- `prompt_preview.md`
- `run_metadata.json`
- `raw_outputs.csv`
- `parsed_candidates.csv` (header only; the synthetic `OK.` response is deliberately not treated as candidate JSON)
- `failed_parses.csv` (header only; the infrastructure response succeeded)
- `cost_summary.json` (usage recorded; billed dollar cost unavailable from the SDK response)
- `diagnostic_results.json`
- `sanitized_console.log`

The smoke helper refuses to overwrite a nonempty output directory, which prevents a later preflight from silently replacing earlier evidence.

## What changed

`scripts/gabriel_state_source_scout.py` now supports:

- `--live-backend gabriel|direct-sdk`, defaulting to `gabriel` so existing live invocations do not silently change;
- `--direct-sdk-max-retries`, defaulting to `0` so retry behavior is explicit and bounded;
- a direct `AsyncOpenAI.responses.create` path using the established HUIT base, bearer authorization supplied by the SDK, and `Ocp-Apim-Subscription-Key` as a default header;
- the same low reasoning-effort setting and, for actual research scouts, the same hosted web-search tool with the requested `search_context_size` and source inclusion;
- bounded concurrency using the existing `--n-parallels`, chunk spacing using the existing `--sleep-between-prompts`, and the existing `--timeout` as the SDK request timeout;
- conversion of SDK responses into the historical raw-output columns consumed by the existing parser and cost/token summary code;
- a sanitized backend log that records configuration names and success/usage signals, but neither prompt/response bodies nor credential values;
- explicit `live_backend`, generic backend-success, and cost-availability metadata on live direct runs.

The direct SDK response is fed into the unchanged `parse_response_to_candidates()` path. Candidate normalization, deterministic scoring, `verification_status=unverified`, `promotion_status=raw_model_output`, parser failures, and quarantine behavior therefore remain shared between the two live backends. Prompt templates, NJ row context, candidate filtering semantics, staged/durable CSV writing, and canonical-data boundaries were not changed.

Dry runs still build prompts and write only `prompt_preview.md` plus `run_metadata.json`. They do not import the OpenAI SDK/GABRIEL live path, read credentials, or record a selected live backend. A no-network regression test exercises this behavior even when `--live-backend direct-sdk` is present.

## Synthetic direct-SDK smoke preflight

Use a fresh output directory and explicit outbound-network authorization:

```bash
python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir tmp/direct_sdk_scout_backend_smoke_test_YYYY-MM-DD_HHMMSS
```

The helper always uses exactly one prompt (`Reply with OK.`), `gpt-5.4-nano`, no tools/web search, one parallel request, no retries, and a 30-second timeout. Proceed only if `diagnostic_results.json` records all of the following:

- `success=true`;
- response text equal to `OK` or `OK.`;
- a present response ID;
- positive output tokens;
- `request_count=1`;
- `web_search=false` and tools omitted/disabled.

Do not reuse a nonempty output directory or reinterpret a failed infrastructure test as a source-availability result.

## Future NJ live scout command — only after separate authorization

The implementation is ready for the previously locked Newark, Jersey City, and Camden input, but this command was not run in this task:

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state NJ \
  --municipalities-csv docs/analysis/national_batch01_nj_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/NJ/national_batch01_nj_direct_sdk_live_YYYY-MM-DD_HHMMSS \
  --prompt-mode minimal \
  --max-prompts 3 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --model gpt-5.4-nano \
  --timeout 30 \
  --direct-sdk-max-retries 0
```

That future run requires explicit, separate authorization because it enables hosted web search and sends three research prompts. Its outputs would remain unverified scout-stage leads. Every returned URL would still require a distinct source-verification pass before any ingestion, codification, canonical coverage change, or claim use.

## Tests and safeguards

The new no-network test verifies that:

- the research request contains the same hosted web-search tool configuration and source inclusion;
- the synthetic smoke request omits tools, web search, and the scout-only reasoning setting;
- a mocked SDK response maps into the same raw row and parses through the existing candidate pipeline;
- the parsed fixture remains `unverified` and `raw_model_output`;
- secret-like values are redacted from exception/log text;
- dry-run artifacts and metadata remain backend-independent.

The existing six-check prompt contract test also remains green. Repository validation passed with 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows. Ingestion tests passed 60/60. Coverage remains 28 healthy pairs across 19 cities, with 6 unmatched safety units; no canonical data changed.

## What remains unverified

- No direct-SDK hosted-web-search request has run yet. The synthetic smoke test proves only the no-tool transport boundary.
- No NJ municipality prompt or source search ran, so Newark, Jersey City, and Camden source availability and candidate quality remain unobserved.
- The direct backend's web-search source extraction has fixture coverage but not live HUIT output coverage.
- OpenAI Responses usage exposes tokens but not billed dollar cost; direct-run cost summaries therefore mark cost unavailable rather than inventing a value.
- HUIT/GABRIEL's intermittent behavior and the precise causal role of the headerless rate-limit probe remain unresolved. The new backend removes those wrapper-specific components from the required scout path rather than claiming to repair GABRIEL itself.
- Candidate URLs, employer/unit identity, operative cycles, document completeness, and matched-comparison value remain verification-stage questions after any future scout.
