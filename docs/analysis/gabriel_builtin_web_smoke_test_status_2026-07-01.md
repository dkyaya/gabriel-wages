# GABRIEL Built-In Web Smoke Test Status

**Date:** 2026-07-01  
**Scope:** Boston-only built-in GABRIEL web smoke test  
**Status:** package installed/imported; built-in web call attempted; no response returned because the one request failed with connection errors

## 2026-07-01 update after installing `openai-gabriel`

The official package install succeeded after allowing network access for:

```text
python -m pip install openai-gabriel
```

Observed package:

- package: `openai-gabriel`
- installed version: `1.1.8`
- import command: `import gabriel`
- imported module path: `.venv/lib/python3.11/site-packages/gabriel/__init__.py`

The first sandboxed install attempt failed because the sandbox could not resolve `pypi.org`; the escalated install succeeded. No package source code was vendored or copied into the repo.

## Callable/signature inspection

After install, `gabriel` imported successfully and exposed all four expected functions:

- `gabriel.whatever`: available.
- `gabriel.extract`: available.
- `gabriel.rate`: available.
- `gabriel.classify`: available.

Signature support checked:

| Function | `web_search` | `web_search_filters` | `modality` | `search_context_size` | `save_dir` | `column_name` | `identifier_column` | `model` | `n_parallels` | `reset_files` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gabriel.whatever` | explicit | explicit | via kwargs | explicit | explicit | explicit | explicit | explicit | explicit | explicit |
| `gabriel.extract` | via kwargs | via kwargs | explicit | via kwargs | explicit | explicit | via kwargs | explicit | explicit | explicit |
| `gabriel.rate` | via kwargs | via kwargs | explicit | explicit | explicit | explicit | via kwargs | explicit | explicit | explicit |
| `gabriel.classify` | via kwargs | via kwargs | explicit | explicit | explicit | explicit | via kwargs | explicit | explicit | explicit |

The installed package confirms that the report-first path is callable as `gabriel.whatever(..., web_search=True, web_search_filters=..., search_context_size=...)`. It also confirms that `modality="web"` is present for `extract`, `rate`, and `classify`-style routes.

## Credential check

Only credential presence was checked; no secret values were printed.

- `HARVARD_SUBSCRIPTION_KEY`: present via repo `.env`.
- `OPENAI_API_KEY`: missing before runtime mapping.
- `OPENAI_BASE_URL`: missing before runtime mapping.

Existing repo runners use the Harvard HUIT OpenAI proxy:

- base URL: `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`
- credential env var: `HARVARD_SUBSCRIPTION_KEY`
- custom header needed by current project convention: `Ocp-Apim-Subscription-Key`

The smoke runner mapped the Harvard key at runtime into GABRIEL's native OpenAI call path by passing:

- `api_key=<HARVARD_SUBSCRIPTION_KEY>`
- `base_url=<Harvard proxy URL>`
- `extra_headers={"Ocp-Apim-Subscription-Key": <HARVARD_SUBSCRIPTION_KEY>}`

The key itself was not printed or written into code.

## Boston built-in web call attempt

Created and ran:

- `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`

Intended scope:

- one row;
- city: Boston, MA;
- identifier: `gabriel_builtin_web_boston_btu_2026_07_01`;
- path: `gabriel.whatever(web_search=True)`;
- model: `gpt-5.4-nano`;
- search context size: `low`;
- `n_parallels=1`;
- `reset_files=False`;
- target: public BPS/BTU salary-comparison and contract-negotiation sources.

The first sandboxed live run failed with connection errors. The same one-prompt runner was rerun with network escalation. GABRIEL retried the incomplete row, but the raw output still shows:

```text
Successful: False
Error Log: ["Connection error.", "Connection error.", "Connection error."]
Response: empty
Web Search Sources: empty
```

No source URLs, citations, snippets, page text, or model web summary were returned. Because no response was returned, no Boston BTU/BPS salary-comparison material was rediscovered by the live call.

Working artifacts from the failed call:

- `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_dataframe.csv`
- `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/gabriel_whatever_raw.csv`
- `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_response.txt`
- `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_2026-07-01.csv`
- `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_sources_2026-07-01.csv`
- `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_extractions_2026-07-01.csv`

Row counts:

- source rows: 0;
- extraction rows: 0;
- URLs/citations preserved: no, because none were returned;
- Boston BTU rediscovered: no, because the live call returned no response;
- ingestion: no;
- production measurement: no.

## Dependency decision

`requirements.txt` was not modified. The package installed and imported, but the built-in web call did not successfully return a response, so the dependency should not be pinned into project requirements until the proxy/web-mode failure is resolved.

## Current next step

Ask Hemanth/toolkit creator whether `openai-gabriel` built-in web mode is expected to work through the Harvard HUIT proxy with web-search tools and the `extra_headers` request option, or whether the smoke test needs a standard `OPENAI_API_KEY`/OpenAI endpoint environment. Then rerun the same Boston-only `gabriel.whatever(web_search=True)` test after that environment question is resolved.

## What was checked

- Confirmed the working directory was `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
- Read the project instructions, current handoff, Thursday report materials, city prompt template, seed source/extraction outputs, and current pilot runners.
- Searched the repo for local GABRIEL web-mode usage and tutorial/notebook files.
- Checked Python import/distribution availability for `gabriel`, `GABRIEL`, `gabriel-toolkit`, and `gabriel-ai`.
- Checked the local pilot scripts for existing GABRIEL web-mode invocation patterns.

## What was unavailable

Before installing `openai-gabriel`, the `gabriel` Python package was not importable in this environment. `python -m pip show` also found no installed distribution under the checked package names.

That earlier blocker is now resolved. The following are available after install:

- `gabriel.whatever`
- `web_search=True`
- `web_search_filters`
- `search_context_size`
- `modality="web"`
- `gabriel.extract`
- `gabriel.rate`
- `gabriel.classify`

No uploaded tutorial notebook was available locally in the repo or under `/mnt/data`; `/mnt/data` is not present in this session.

## Diagnosis

The original issue was an environment/package availability issue, not a negative finding about the toolkit design. After installing `openai-gabriel`, the package and signatures are available, but the one Boston native web call did not return a response. The remaining issue is live call execution through the current credential/proxy/network path.

Credentials were not printed. The session did reach the live invocation stage after mapping the Harvard proxy key into GABRIEL's native call path, but the request returned no response and GABRIEL recorded connection errors.

## Run decision

One Boston-only live web-search call was attempted through built-in GABRIEL web mode after package install. It returned no response because GABRIEL recorded connection errors.

No ingestion or production measurement happened.

## Next step for Hemanth/toolkit creator

Confirm whether the Harvard HUIT proxy supports OpenAI Responses API web-search tools through `openai-gabriel` with the `extra_headers` request option, or whether a standard OpenAI endpoint/key is required for built-in web mode. Then rerun only the Boston smoke test first. The specific invocation remains:

- `gabriel.whatever(..., web_search=True, search_context_size="low")`;
- otherwise `gabriel.extract(..., modality="web", search_context_size="low")`, if that is the supported route.

The custom `get_all_responses_fn` scaffold remains fallback/advanced infrastructure for schema control or nonstandard backends, not the primary live path.
