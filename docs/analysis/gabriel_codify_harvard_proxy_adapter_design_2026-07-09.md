# GABRIEL Codify Harvard Proxy Adapter Design — 2026-07-09

## Interface findings

The prior dry-run pilot (`gabriel_codify_interface_inspection_2026-07-08.md`) established that `gabriel.codify()`'s docstring advertises `response_fn` and `get_all_responses_fn` injection points. This session traced the **actual source code** (installed `gabriel` v1.1.8, `site-packages/gabriel/api.py` → `gabriel/tasks/codify.py` → `gabriel/utils/openai_utils.py`) to confirm the hooks are genuinely wired end-to-end, not just documented:

- `gabriel.api.codify(...)` passes `response_fn`/`get_all_responses_fn` straight through to `Codify(cfg, ...).run(df, column_name, ..., response_fn=response_fn, get_all_responses_fn=get_all_responses_fn, **response_kwargs)`.
- `Codify.run()` forwards `**kwargs` (including these two) into `self._gather_iteration(..., **kwargs)`.
- `_gather_iteration()` forwards `**kwargs` into the final `await get_all_responses(prompts=prompts, identifiers=identifiers, ..., **kwargs)` call.
- `get_all_responses()` in `openai_utils.py` is where the hooks are actually consumed: if `get_all_responses_fn` is set it fully replaces the batch call; otherwise `response_callable = response_fn or get_response` is awaited once per prompt.

**Critically:** `get_all_responses()` only calls `_require_api_key()` (which raises if `OPENAI_API_KEY` is unset) when `using_custom_response_fn` is `False`. Supplying a custom `response_fn` **skips the `OPENAI_API_KEY` requirement entirely** — this is exactly the mechanism needed to route codify through a credential GABRIEL doesn't natively know about (`HARVARD_SUBSCRIPTION_KEY`).

### `response_fn` contract (confirmed from source, not just docstring)

- Must be an `async` callable accepting a `prompt` argument (positional or keyword).
- Receives whatever keyword arguments its own signature accepts, drawn from `get_response`'s parameter set as forwarded by `codify()` — in particular `model`, `reasoning_effort`, `json_mode`, `n`, `timeout`, `use_dummy`. Declaring `**kwargs` on the adapter safely absorbs anything not explicitly needed.
- Must return one of: a list of response strings, a `(responses, duration)` pair, or a `(responses, duration, raw)` tuple. This pilot's adapter returns the 3-tuple form.
- `n_parallels`/rate-limiting is **not** managed internally when a custom `response_fn` is supplied (`manage_rate_limits = not using_custom_response_fn`) — the caller is responsible for not overwhelming the downstream API. This pilot sets `n_parallels=1` to keep calls strictly sequential, matching the existing Harvard Proxy scaffold's own sequential-call pattern.

### Chunking/batching math that determines the actual live-call count

`codify()`'s internal `_gather_iteration()` splits each row's text into word-count chunks (`max_words_per_call`, default 1000) **and** splits the codebook into category batches (`max_categories_per_call`, default 8). Total live calls = `rows × chunks_per_row × category_batches_per_chunk × n_rounds_completion_passes`. With the default settings, this pilot's 19-attribute codebook (`ceil(19/8) = 3` batches) and default `n_rounds=2` (which adds a second completion/refinement pass when `n_rounds > 1` and categories are static) would have produced **up to 24 calls for 4 rows** — far over the 4-call cap. This run explicitly sets:
- `max_categories_per_call=19` (all 19 attributes in one call per row)
- `max_words_per_call=1500` (comfortably larger than every selected window, so each row is exactly one chunk — see Task D windows, all under 700 words)
- `n_rounds=1` (skip the multi-round completion loop entirely)

With these three settings, **4 rows × 1 chunk × 1 category batch × 1 round = exactly 4 live calls**, matching this run's hard cap precisely.

## Adapter route chosen

**Option 1 (preferred): `response_fn` injection**, not a hand-rolled bypass wrapper. This is a genuine, native `gabriel.codify()` run — GABRIEL still builds the per-window coding prompt from the codebook via its own Jinja2 template, parses the JSON response, aggregates results across categories, and returns a coded DataFrame. The adapter's only job is the actual HTTP call: format the prompt GABRIEL already built, send it to the Harvard proxy endpoint, and return the raw completion text back to GABRIEL for parsing.

### Why chosen over `get_all_responses_fn`

`get_all_responses_fn` fully replaces GABRIEL's batching/orchestration (I would have to re-implement chunking, category-batching, retries, and DataFrame assembly myself). `response_fn` is documented as the "lightweight" per-prompt hook and, per the source trace above, is sufficient on its own to bypass the `OPENAI_API_KEY` requirement while letting GABRIEL keep doing everything else it already does well. This keeps the adapter small (~30 lines) and keeps the run a genuinely *native* codify pilot rather than a "codify-compatible" reimplementation — satisfying the task's stated preference for Option 1 when supported.

### Adapter implementation (routing pattern)

Reuses the exact Harvard Proxy client construction already established and working elsewhere in this repo (`ingest/extract_spans.py`, `scripts/proxy_pilot_must_have_sources.py`):

```python
from openai import OpenAI

client = OpenAI(
    api_key=subscription_key,               # from HARVARD_SUBSCRIPTION_KEY
    base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
    default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
)

async def harvard_proxy_response_fn(prompt, *, model=None, reasoning_effort=None,
                                     json_mode=False, n=1, timeout=None,
                                     use_dummy=False, **kwargs):
    def _call():
        return client.chat.completions.create(
            model=model or "gpt-5.4-nano",
            reasoning_effort=reasoning_effort or "low",
            response_format={"type": "json_object"} if json_mode else None,
            messages=[{"role": "user", "content": prompt}],
        )
    resp = await asyncio.to_thread(_call)
    content = resp.choices[0].message.content or ""
    return ([content], None, [content])
```

The synchronous `OpenAI` client (matching this repo's established pattern, not the untested `AsyncOpenAI`) is run in a thread via `asyncio.to_thread` to satisfy `response_fn`'s `async` requirement without introducing a second, unverified async-client code path.

**Model choice:** `gpt-5.4-nano`, not GABRIEL's own default `gpt-5.4-mini` — `gpt-5.4-nano` is the specific model already confirmed working through this repo's Harvard proxy endpoint (`scripts/proxy_pilot_must_have_sources.py`'s `MODEL = "gpt-5.4-nano"`, tracked in `scripts/log_api_spend.py`'s pricing table). `gpt-5.4-mini` has never been exercised against this specific proxy in this repo and could plausibly not be provisioned there even if it is a valid general model name.

## Credential safety check

Presence-only checks (no values printed, logged, or written to any file):

```text
Before loading .env:  OPENAI_API_KEY NOT SET | OPENAI_BASE_URL NOT SET | HARVARD_SUBSCRIPTION_KEY NOT SET
After python-dotenv's load_dotenv():           HARVARD_SUBSCRIPTION_KEY SET (length reported only, no value)
```

`.env` is git-ignored (`git check-ignore -v .env` confirms) and not tracked (`git ls-files .env` returns nothing). This session did not open, `cat`, or otherwise read `.env`'s contents directly at any point — presence and length were confirmed exclusively via `python-dotenv`'s standard `load_dotenv()` loader (already an installed, unmodified third-party package) writing into `os.environ`, which this session then queried with `os.environ.get(...)` and `len(...)` only. The Harvard proxy `base_url` (`https://go.apis.huit.harvard.edu/ais-openai-direct/v2`) is not a secret — it is already present, unredacted, in this repo's own committed source (`ingest/extract_spans.py`).

## Live-call safety decision

**Safe to attempt a capped live run.** `HARVARD_SUBSCRIPTION_KEY` is available (via `.env` + `load_dotenv()`), the adapter route is well-understood from source-level inspection (not guesswork), and the call-count math above guarantees exactly 4 calls for 4 rows under the settings chosen. Per the task's hard boundary, the first live call will be treated as a go/no-go test: if it fails for a nontrivial adapter/API reason, live calls stop immediately and the failure is documented rather than retried.

## Limitations

- This adapter has never been exercised before this session — the source-level reasoning above is thorough but unverified until the first real call returns.
- `response_fn` disables GABRIEL's internal rate-limiting; safe here only because calls are kept strictly sequential (`n_parallels=1`) and capped at 4.
- JSON-mode enforcement depends on the Harvard proxy endpoint correctly honoring `response_format={"type": "json_object"}`, which is already confirmed working in this repo's existing scaffold (`proxy_pilot_must_have_sources.py`) but with a different (much shorter, hand-built) prompt — GABRIEL's own codify prompt template is longer and more complex, and has not previously been sent through this endpoint.
- Cost/usage logging (`scripts/log_api_spend.py`) is not wired into GABRIEL's own internal call path; this pilot logs usage manually inside the adapter for consistency with repo convention.

## Exact max-call cap

**4 live calls maximum**, enforced in code (not just via a CLI flag) in `scripts/gabriel_codify_pilot.py`. `max_categories_per_call=19`, `max_words_per_call=1500`, and `n_rounds=1` are set specifically so 4 selected rows produce exactly 4 calls, not more.
