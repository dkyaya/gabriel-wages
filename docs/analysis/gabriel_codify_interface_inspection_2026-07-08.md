# GABRIEL `codify` Interface Inspection — 2026-07-08 (run executed 2026-07-09)

Bounded, read-only inspection of the installed `gabriel` package. No environment variable values, API keys, or `.env` contents were printed — only boolean presence/absence checks were run.

## Import status

```text
python3 -c "import gabriel; print(gabriel.__version__)"
gabriel imported OK
version: 1.1.8
```

`gabriel.__file__` resolves to `/Users/joachimjohnson/.pyenv/versions/3.11.7/lib/python3.11/site-packages/gabriel/__init__.py` — a real, locally installed package (not a stub). `hasattr(gabriel, 'codify')` is `True`. The top-level `gabriel` namespace also exposes `classify`, `rate`, `rank`, `extract`, `deidentify`, `discover`, `ideate`, `merge`, `compare`, `bucket`, `filter`, `paraphrase`, `debias`, `deduplicate`, `poll`, `view`, `whatever`, `seed`, `id8` — `codify` is one task among a larger suite, consistent with this being the general-purpose GABRIEL toolkit referenced elsewhere in this repo's docs.

## Signature

```python
gabriel.codify(
    df: Optional[pandas.DataFrame], column_name: str, *,
    save_dir: str,
    categories: Optional[Dict[str, str]] = None,
    additional_instructions: str = "",
    model: str = "gpt-5.4-mini",
    n_parallels: int = 650,
    max_words_per_call: int = 1000,
    max_categories_per_call: int = 8,
    file_name: str = "coding_results.csv",
    reset_files: bool = False,
    debug_print: bool = False,
    reasoning_effort: Optional[str] = None,
    modality: str = "text",
    n_rounds: int = 2,
    completion_classifier_instructions: Optional[str] = None,
    template_path: Optional[str] = None,
    response_fn: Optional[Callable[..., Awaitable[Any]]] = None,
    get_all_responses_fn: Optional[Callable[..., Awaitable[pandas.DataFrame]]] = None,
    **cfg_kwargs,
) -> pandas.DataFrame
```

## Docstring summary

"Passage coding: highlights snippets in text that match qualitative codes." Takes a DataFrame and a text column; `categories` is an optional `{code_name: description}` mapping (if omitted, the model infers categories itself — not desired for this pilot, since we want our own fixed 11-code mechanism codebook). `additional_instructions` appends free-text guidance to the coding prompt — this is where the pilot's verbatim-only / `not_found`-default / no-causal-inference rules will go. `df=None` loads cached results from `save_dir` instead of recomputing (useful for a dry inspection of a prior run, not relevant here since no prior run exists). `response_fn` / `get_all_responses_fn` are explicit injection points that let a caller fully replace the underlying model-call function — this is the mechanism by which this repo's existing Harvard Proxy calling pattern (see `scripts/proxy_pilot_must_have_sources.py`) *could* be wired into `codify()` in principle, though this pilot does not attempt that wiring (see credentials finding below).

## Underlying call path and credentials

`gabriel.utils.openai_utils` (the module `codify` calls into by default) resolves credentials as follows:
- `_require_api_key()` reads `OPENAI_API_KEY` from the environment and raises if unset.
- The HTTP client's `base_url` defaults to `os.getenv("OPENAI_BASE_URL")` or `https://api.openai.com/v1` if neither is set.
- `CodifyConfig` (the dataclass backing `codify()`) also exposes a `use_dummy: bool = False` flag — when `True`, the call path returns synthetic/dummy responses instead of making a real network call, useful for a fully offline structural dry-run.

**This project's established Harvard Proxy calling convention (`scripts/proxy_pilot_must_have_sources.py`) is a separate, hand-built code path** that reads `HARVARD_SUBSCRIPTION_KEY` and constructs its own `openai.OpenAI(...)` client pointed at the Harvard HUIT proxy endpoint — it does **not** go through `gabriel.codify()` at all. GABRIEL's own default path only recognizes `OPENAI_API_KEY` / `OPENAI_BASE_URL`, not `HARVARD_SUBSCRIPTION_KEY`. Wiring the two together would require passing a custom `response_fn` to `codify()` that internally calls the same Harvard-proxy client logic already in `proxy_pilot_must_have_sources.py`'s `_run_live()` — a nontrivial integration this pilot does not attempt, per the task's instruction to use the established proxy configuration "only if already supported by repo conventions" (it is not yet supported for `codify()` specifically).

**Credential check (presence/absence only, no values printed):**

```text
OPENAI_API_KEY: NOT SET
OPENAI_BASE_URL: NOT SET
HARVARD_SUBSCRIPTION_KEY: NOT SET
HARVARD_PROXY_BASE_URL: NOT SET
HARVARD_PROXY_ENDPOINT: NOT SET
ANTHROPIC_API_KEY: NOT SET
```

None of the credentials `gabriel.codify()`'s default call path needs (`OPENAI_API_KEY`, optionally `OPENAI_BASE_URL`) are present in this environment, and neither is this repo's own Harvard Proxy key (`HARVARD_SUBSCRIPTION_KEY`), which every prior Harvard Proxy session in this repo's history has also found unset (see `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md` and every `PROGRESS.md` entry that touches the proxy scaffold — all report dry-run only, no live call ever executed in this repo).

## Likely calling pattern (for reference / Task B/D design)

```python
import gabriel

result_df = gabriel.codify(
    df=evidence_windows_df,          # one row per (contract_id, window_id)
    column_name="window_text",       # the short verbatim excerpt column
    save_dir="tmp/gabriel_codify_pilots/<timestamp>/gabriel_save_dir",
    categories={                     # the 11-code mechanism codebook
        "peer_comparator_wage_comparability": "...",
        "arbitration_impasse_backstop": "...",
        # ... (see gabriel_codify_pilot_design_2026-07-08.md for full codebook)
    },
    additional_instructions=PILOT_INSTRUCTIONS,  # verbatim-only, not_found-default, no-causal-inference rules
    model="gpt-5.4-mini",
    reasoning_effort="low",
    n_rounds=1,                      # keep the pilot cheap and bounded
)
```

## Whether a live pilot is safe to attempt

**Not safe this session — no credentials are present.** Per this run's own hard boundary ("If the interface is unclear, credentials are missing, or output capture is unsafe, do not make live calls. Produce dry-run only"), Task E will produce a dry-run-only pilot output directory (`live_run_attempted=false`), not a live call. The interface itself is well-understood and structurally sound (signature, docstring, and injection points are all clear and documented above) — the sole blocker is the absence of any usable API credential in this environment, not an interface or safety concern with `codify()` itself.
