# GABRIEL Built-In Web Smoke Test Status

**Date:** 2026-07-01  
**Scope:** Boston-only built-in GABRIEL web smoke test  
**Status:** not executed; built-in GABRIEL package not available in this environment

## What was checked

- Confirmed the working directory was `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
- Read the project instructions, current handoff, Thursday report materials, city prompt template, seed source/extraction outputs, and current pilot runners.
- Searched the repo for local GABRIEL web-mode usage and tutorial/notebook files.
- Checked Python import/distribution availability for `gabriel`, `GABRIEL`, `gabriel-toolkit`, and `gabriel-ai`.
- Checked the local pilot scripts for existing GABRIEL web-mode invocation patterns.

## What was unavailable

The `gabriel` Python package is not importable in this environment. `python -m pip show` also found no installed distribution under the checked package names.

Because the package is absent, the following could not be confirmed as callable here:

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

This is an environment/package availability issue, not a negative finding about the toolkit design. The repo documents the tutorial-level understanding that built-in GABRIEL web mode should be the primary live path, but the installed local Python environment does not currently expose the `gabriel` package needed to test that path.

Credentials were not printed or inspected beyond package and repo-surface checks. Since the package itself is unavailable, this session did not reach a credentials or invocation-shape failure.

## Run decision

No live web search was executed.

No Boston runner was created, no source or extraction CSVs were generated, and no ingestion or production measurement happened.

## Next step for Hemanth/toolkit creator

Provide the installable/importable GABRIEL package version or the exact local environment where the tutorial web-mode calls are available, then rerun only the Boston smoke test first. The specific first invocation to confirm remains:

- `gabriel.whatever(..., web_search=True, search_context_size="low")`, if available;
- otherwise `gabriel.extract(..., modality="web", search_context_size="low")`, if that is the supported route.

The custom `get_all_responses_fn` scaffold remains fallback/advanced infrastructure for schema control or nonstandard backends, not the primary live path.
