# Direct-SDK Hosted-Search Call-Path Notes — 2026-07-22

## Production call path

The direct-SDK control and the production hosted-search scout use the same implementation in `scripts/gabriel_state_source_scout.py`:

1. `_load_live_subscription_key()` loads the first existing dotenv file from the repository root or its parent with `override=False`.
2. The only required credential variable for this route is `HARVARD_SUBSCRIPTION_KEY`. Its value is supplied in memory both as the OpenAI SDK `api_key` and as the `Ocp-Apim-Subscription-Key` default header. The value is never written or printed.
3. `AsyncOpenAI` uses the fixed base `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`; the SDK appends `/responses` through `client.responses.create(...)`.
4. The OpenAI SDK supplies the `Authorization` bearer header. The client also supplies the HUIT subscription-key header by name. No `OPENAI_API_KEY` or `OPENAI_BASE_URL` environment value is required by this explicit client construction.
5. `run_direct_sdk_live_batch()` executes the calls, converts successful Responses objects into the legacy raw-row schema, catches exceptions, writes a sanitized configuration/result log, and returns a DataFrame to the existing scout parser.

## No-search versus hosted-search payload

Both paths call the same `build_direct_sdk_response_kwargs()` function and the same `client.responses.create(...)` method.

The no-search control sends:

- `model=gpt-5.4-nano`;
- `input="Reply with OK."`;
- no `tools`;
- no `include` list;
- no reasoning setting in the established smoke helper.

The production search-enabled path sends the same model and input field plus:

```text
reasoning={"effort": "low"}
tools=[{"type": "web_search", "search_context_size": "low"}]
include=["web_search_call.action.sources"]
```

Thus, this diagnostic can isolate hosted-search behavior without changing endpoint, client, credential-loading rule, header names, timeout implementation, retry setting, or response extraction.

## Model, context, timeout, and retry behavior

- Production model in both failed Tier 1 attempts: `gpt-5.4-nano`.
- Search context: the CLI `--search-context-size` value is inserted into the web-search tool; both failed attempts used `low`.
- Timeout: `AsyncOpenAI` receives `httpx.Timeout(timeout)`. The failed scouts used 90 seconds, while the bounded diagnostic uses 30 seconds.
- Retries: `AsyncOpenAI(max_retries=...)`; the failed scouts and diagnostic both use zero retries.
- Concurrency: `run_direct_sdk_live_batch()` chunks requests using `n_parallels`; the diagnostic calls it once per fixed prompt with one parallel lane.

## Response extraction

`direct_sdk_response_to_row()` records:

- response text from `response.output_text`;
- response ID from `response.id`;
- status from `response.status`;
- input, output, and total tokens from `response.usage`;
- reasoning tokens from `usage.output_tokens_details.reasoning_tokens`;
- hosted-search source objects by traversing the serialized response output.

A response is considered raw-successful when status is `completed`, or when status is absent but nonempty output text exists. The later scout parser separately validates the municipality candidate JSON contract.

## Exception and `connection_error` handling

The runner catches `Exception` around each SDK request and writes only the exception class plus a credential-redacted message into `Error Log`. In both Tier 1 attempts this became `APIConnectionError: Connection error.`; the nested network cause or HTTP status was not exposed in the saved row.

`is_direct_sdk_connection_failure_without_response()` treats a row as connection collapse when its error mentions connection, timeout, or capacity and all three decisive response signals are absent: response text, response ID, and output tokens. The scout parser then records the row as `connection_error` (or timeout where applicable). Two consecutive such rows stop the rest of a sequential batch and mark them `stopped_before_request`.

The new diagnostic helper preserves the same production exception reduction so it tests the actual route, while separately reporting exception class, sanitized message, response-signal presence, elapsed time, and whether failure is transport, timeout, incomplete response, or downstream schema/content.

## Security boundary

The helper reports environment-variable names and header names only. It never reports variable values, key length, prefix, suffix, hash, raw authorization headers, client objects, or dotenv contents. Returned URLs are not opened or independently verified, and diagnostic responses are not parsed into candidate or coverage files.
