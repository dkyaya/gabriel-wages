# Direct SDK Scout Backend

Date: 2026-07-20

Stage: infrastructure implementation plus a later operational note recording the separately authorized three-city NJ transport result. The implementation task itself ran only one synthetic smoke; neither task performed source verification, ingestion, `gabriel.codify`, canonical-data edits, or claim-stage promotion.

## Plain-English result

The state-source scout now has an opt-in live backend that sends its prompts directly through the OpenAI SDK Responses API instead of depending on GABRIEL's wrapper orchestration. The historical GABRIEL backend remains the default, and dry-run behavior is unchanged. For the Harvard HUIT proxy, use `--live-backend direct-sdk` when a future research scout is separately authorized, especially after a GABRIEL preflight fails.

The new path first passed exactly one synthetic live test. It sent `Reply with OK.` to `gpt-5.4-nano` through `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`, with the bearer and `Ocp-Apim-Subscription-Key` header names, no tools or web search, zero SDK retries, and a 30-second timeout. It returned `OK.`, a response ID, 10 input tokens, 0 reasoning tokens, and 6 output tokens. Credential values and `.env` contents were not logged.

An immediately subsequent, separately authorized New Jersey run established the hosted-web-search boundary: Newark, Jersey City, and Camden completed 3/3 with nonempty responses, response IDs, positive output tokens, eight parsed candidates, and no connection or parser failure. Those candidate facts remain scout-stage and unverified, but the transport result makes direct SDK the preferred HUIT-proxy scout backend. See `national_batch01_nj_live_direct_sdk_scout_review_2026-07-20.md`.

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

## Estimate-only cost reporting added for national runs

Direct Responses usage now preserves `input_tokens`, `output_tokens`, nested reasoning tokens, and `total_tokens` when the SDK exposes them. Per-run JSON/CSV summaries retain the historical `*_tokens_total` fields and also write the explicit names `input_tokens`, `output_tokens`, `reasoning_tokens`, and `total_tokens`.

`docs/analysis/direct_sdk_pricing_config_2026-07-20.json` is the configurable pricing source. Its `gpt-5.4-nano` entry uses the standard OpenAI text-token prices visible on the official model page when checked 2026-07-21: USD 0.20 per 1M input tokens and USD 1.25 per 1M output tokens. This is deliberately `estimate_only=true`. It is not evidence of Harvard HUIT contract/proxy billing and excludes hosted-web-search or other tool fees, cached-input treatment, taxes, credits, discounts, and adjustments. The Responses `reasoning_tokens` detail is treated as included in `output_tokens`, so it is reported but not charged a second time.

The direct-SDK summary therefore keeps actual `cost_available=false` and `total_cost=null`, while separately reporting `estimated_cost_available`, `estimated_input_cost`, `estimated_output_cost`, `estimated_reasoning_cost`, `estimated_total_cost`, `estimate_only`, `pricing_source_note`, `pricing_effective_date`, `reasoning_billing_mode`, and estimate scope. `pricing_missing_or_unconfirmed=true` remains explicit for the included OpenAI-reference estimate because HUIT billing is unconfirmed. If the config is missing, malformed, lacks the selected model, has null required rates, or leaves nonzero reasoning billing unknown, token usage is still preserved and the live run continues with `estimated_cost_available=false`.

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

## Example live scout command — only after separate authorization

The implementation was used successfully for the locked Newark, Jersey City, and Camden input in a later task. The following remains an example shape; never rerun it or substitute another slice without separate authorization and a fresh smoke preflight:

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

Every live run requires explicit, separate authorization because it enables hosted web search and sends research prompts. Outputs remain unverified scout-stage leads and should be added to the national queue and scout-coverage accounting. Deep source verification is now deferred to coordinated later waves before any ingestion, codification, canonical coverage change, or claim use.

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

- The NJ direct-SDK run established live HUIT hosted-search transport and source extraction for three prompts, not broad service reliability or candidate truth.
- Newark, Jersey City, and Camden candidate URLs, source ownership, employer/unit identity, operative cycles, document completeness, matched-comparison value, and duplicates remain unverified scout-stage questions.
- OpenAI Responses usage exposes tokens but not billed dollar cost. Direct-run summaries keep actual cost unavailable and provide only a separately labeled, configurable token-price estimate. The included public OpenAI rate basis is not confirmed HUIT billing and excludes web-search/tool fees.
- HUIT/GABRIEL's intermittent behavior and the precise causal role of the headerless rate-limit probe remain unresolved. The new backend removes those wrapper-specific components from the required scout path rather than claiming to repair GABRIEL itself.
- Future state slices still require a fresh synthetic preflight, separate live authorization, zero/controlled retries, preserved artifacts, queue/coverage updates, and later coordinated verification before ingestion.
