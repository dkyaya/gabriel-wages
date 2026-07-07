# Harvard Proxy Calling-Scaffold Review — 2026-07-06

**Type:** dated safety review. Inventories every existing script or doc that references the Harvard HUIT OpenAI proxy or GABRIEL, and defines the safe calling pattern a future bounded pilot script should follow. **This review made no live API/model/proxy calls and did not print, inspect, or copy any secret value.**

## 1. Existing scripts/docs that mention Harvard Proxy, OpenAI, GABRIEL, or gpt-5.4-nano

| File | What it does |
| --- | --- |
| `analysis/gabriel_pilot/run_gabriel.py` | Production GABRIEL scoring script for the `comparability_emphasis` attribute (v8). Reads `analysis/gabriel_pilot/input.csv`, calls the Harvard proxy once per document (plus a relevance-check call and a bounded retry call per document), verifies every returned excerpt is a literal substring of the source text, writes `results_v8.csv`. Always makes live calls if `HARVARD_SUBSCRIPTION_KEY` is set — has no no-call mode. |
| `analysis/gabriel_pilot/run_gabriel_v9.py` | An earlier/parallel version of the same scoring pattern (not read in full this session; same calling pattern expected based on the file's presence alongside `run_gabriel.py` and `build_input_v9.py`). |
| `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py` | Scores the `arbitration_or_impasse_backstop` attribute against an 11-row hand-coded gold set. **Despite the filename, this script still makes live Harvard proxy calls** — "dry-run" here means "bounded to a small, curated gold set," not "no API call." Has a `--build-input-only` flag that skips all API calls, but no equivalent flag to preview the full run without calling. |
| `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py` | A smoke test exercising the proxy's built-in web-search tool capability against one Boston-related query. Live-call script. |
| `analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py` | A retry-hardened variant of the above. Live-call script. |
| `analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py` | A connectivity-diagnostic script for the proxy's web-search feature. Live-call script (makes a minimal call to confirm the proxy is reachable). |
| `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py` | A demonstration script for the proxy's web-search seeding feature. Live-call script. |
| `analysis/gabriel_pilot/build_input.py`, `build_input_v9.py` | Build the CSV inputs consumed by the scoring scripts above. Do not call the proxy themselves — pure data-preparation scripts. |
| `analysis/gabriel_pilot/summarize_v9.py`, `plot_results.py` | Post-processing/analysis scripts over already-generated results. Do not call the proxy. |
| `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py` | Defines a custom function/tool the proxy's web-search feature can call. Not itself a call-initiating script, but is loaded by the web-search demo/smoke scripts above. |
| `ingest/extract_spans.py` | Production ingestion component. Stage-1 regex-based clause extraction runs with no API calls at all. Stage-2 LLM fallback (`llm_pass()`) is optional and off unless `HARVARD_SUBSCRIPTION_KEY` is set; gated by an anti-paraphrase guard (`_verify_verbatim`-equivalent) that discards any returned span not a literal substring of the source. |
| `ingest/README.md` | Documents the two-stage extraction pipeline and states the LLM fallback "stays off unless `HARVARD_SUBSCRIPTION_KEY` is set in the environment," with no live-call flag required — the *presence* of the env var alone enables live calls in this component. |
| `ingest/test_pipeline.py`, `ingest/fetchers/__init__.py` | Reference GABRIEL/proxy-adjacent terms in test fixtures or fetcher scaffolding; not themselves call-initiating in a way relevant to this review. |
| `scripts/log_api_spend.py` | Not a caller. A shared utility (`log_usage()`, `print_totals()`) every scoring script above imports to append token/cost estimates to `logs/api_spend_log.csv`. Never touches or logs the subscription key itself — only model name, token counts, and an estimated dollar cost derived from public list pricing. |
| `scripts/validate.py` | References `gabriel`/`GABRIEL` only in comments/docstrings describing the project's purpose; makes no API calls. |
| `README.md`, `PROGRESS.md`, `docs/analysis/chatgpt_handoff_latest.md` | Documentation and session-log references to the proxy/GABRIEL migration history (e.g., the ingestion LLM fallback's 2026-06 switch from the Anthropic API to the Harvard proxy). Historical record, not executable. |
| `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md` | A status memo describing results of the web-search smoke-test scripts above. Documentation, not executable. |

## 2. Which scripts appear safe to reuse

- **`ingest/extract_spans.py`'s verbatim-verification pattern** (`_verify_verbatim`-equivalent logic) is the single most important pattern to reuse in any future pilot: it discards any model-returned span that is not a literal substring of the source text, which is exactly the anti-hallucination discipline this project's controlled-vocabulary and verbatim-capture rules require.
- **`scripts/log_api_spend.py`** is safe to import directly into any future pilot — it is a pure logging utility, never touches the subscription key, and already has the correct pricing/estimation caveats documented in its own docstring.
- **`analysis/gabriel_pilot/build_input.py`-style input-preparation scripts** are safe as a pattern to follow (build a CSV of rows-to-process first, inspect it, then call), though the specific files themselves are tied to the `comparability_emphasis` attribute and should not be reused directly for a different extraction task.

## 3. Which scripts are risky or too broad

- **`run_gabriel.py`, `run_gabriel_v9.py`, and `run_gabriel_v10_gold_dryrun.py`** all call the proxy once per row in their input file with no row-count ceiling or explicit `--live` gate — running any of them against a large input file would make an uncontrolled number of live calls. None of them should be run as part of this or any future scaffold-only session.
- **The web-search smoke/demo/diagnostic scripts** (`run_gabriel_builtin_web_smoke_boston.py`, `run_gabriel_builtin_web_boston_graduated_retry.py`, `diagnose_gabriel_proxy_web_connectivity.py`, `run_gabriel_websearch_seed_demo.py`) are the broadest risk in this inventory — they exercise the proxy's built-in web-search tool, which can itself make an unbounded number of external web requests per single API call, compounding cost and scope beyond a simple text-scoring call. These should not be used as a template for a bounded pilot.
- **`ingest/extract_spans.py`'s `llm_pass()`** is a production pipeline component, not a pilot tool. It is scoped correctly for its own purpose (single-document clause extraction) but is wired into the broader ingestion pipeline (`pipeline.py`, `process_inbox.py`) and should not be invoked directly or repurposed for a general-purpose pilot without going through the actual ingestion pathway this project's `AGENTS.md`/`ingest/README.md` describe.

## 4. Environment variables expected (without printing values)

- **`HARVARD_SUBSCRIPTION_KEY`** — the sole credential every proxy-calling script in this repository expects. Read from the process environment; every script also attempts to load it from a `.env` file (via `python-dotenv`) located in the script's own directory or a parent directory (repo root), stopping at the first `.env` found. A `.env` file exists in the repo root (confirmed present via a file-existence check only, not read) and is correctly excluded from version control (`.gitignore` lists `.env` and `.env.local`).
- No other environment variable is used by any proxy-calling script in this repository. The `openai` Python package's `OpenAI` client is initialized with `api_key=subscription_key` (a required constructor argument for the library) but the actual authentication with the Harvard proxy happens via the `Ocp-Apim-Subscription-Key` HTTP header, set explicitly in every script's `default_headers`.

## 5. Recommended safe calling pattern

1. **Default to no network call at all.** Any future pilot script's default mode should not import or instantiate the `OpenAI` client, should not read `HARVARD_SUBSCRIPTION_KEY`, and should not require the key to be present at all unless a live call is explicitly requested.
2. **Require an explicit opt-in flag for any live call**, separate from any other flag, so a live call cannot happen as a side effect of a typo or a default argument.
3. **Enforce a hard, small numeric ceiling on live-mode row count**, refusing to proceed if the requested count is missing or exceeds the ceiling — this project's existing scripts have no such ceiling, which is the single clearest safety gap this review identifies.
4. **Read the subscription key only inside the live-call code path**, never at module import time, so that importing or dry-running the script never touches the credential.
5. **Never print, log, or serialize the key itself** — only log model name, token counts, and estimated cost, exactly as `scripts/log_api_spend.py` already does.
6. **Reuse the verbatim-verification guard** for any extraction-style task, discarding any returned span that is not a literal substring of the input text, consistent with `ingest/extract_spans.py`'s existing discipline.
7. **Write every run's inputs and outputs to a fresh, timestamped directory**, never overwriting a prior run's outputs, so every pilot is independently auditable after the fact.

## 6. Recommended output/logging pattern

- A `run_config.json` recording exactly what was requested (dry-run vs. live, row selection, limit, model, template version) — written in every run, before any call is attempted.
- A `selected_rows.csv` recording exactly which rows were selected and their key identifying fields (not full document text) — written in every run.
- A `prompt_preview.md` showing the fully-rendered prompt(s) that would be (or were) sent — written in every run, so a reviewer can inspect exactly what the model would see without needing to re-run anything.
- A `dry_run_log.txt` (dry-run mode) or `live_run_log.txt` (live mode) recording a plain-text narrative of what happened, explicitly stating in dry-run mode that no network call occurred.
- A `responses.jsonl` (live mode only) recording each raw response alongside its associated row identifier, for auditability.
- A `parsed_outputs.csv` (live mode only, only if parsing logic exists) — structured, tabular results.
- Token/cost logging via the existing `scripts/log_api_spend.py` utility, in live mode only.
- Never write the subscription key, or any other secret, to any of the above files.

## 7. What live-call authorization should look like

A live call should require all of the following, verified in this order, before any network request is made:
1. An explicit `--live` flag (or equivalent), with no default that enables it.
2. An explicit `--limit N` argument, with no default value, where `N` is a positive integer no greater than 3 for this scaffold's intended use (bounded pilots, not production runs).
3. A pilot row selection that is either an explicit, small, named set of `contract_id` values, or a hardcoded pilot list already reviewed and approved as part of this scaffold — never "all rows" or an unbounded query result.
4. `HARVARD_SUBSCRIPTION_KEY` present in the environment at the moment the live-call code path is reached — read only then, not at script start.
5. A user or PI's explicit, out-of-band approval for that specific run (this scaffold does not and should not attempt to auto-approve its own live calls; the `--live` flag documents intent, it does not substitute for separate authorization).

No live call was made in the production of this review or any file in this session.
