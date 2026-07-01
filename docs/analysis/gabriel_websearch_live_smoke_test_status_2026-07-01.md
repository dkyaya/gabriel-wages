# GABRIEL Web-Search Live Smoke Test Status

**Date:** 2026-07-01  
**Scope:** Boston one-city live smoke-test decision

## Status

The live smoke test was not executed because no safe live web-search backend was locally available.

Local inspection found:

- no project dependency for a search API wrapper in `requirements.txt`;
- no installed search-vendor client packages such as SerpAPI, Serper, Brave, Tavily, Exa, Google API client, or DuckDuckGo wrappers;
- no search-backend environment variable in the active shell;
- no `.env` variable other than the Harvard HUIT OpenAI proxy key used by existing GABRIEL scoring and optional LLM span extraction.

The platform/browser search tools available to the Codex session are not a repo-local callable backend that can be passed through `custom_get_all_responses`. They also would not demonstrate the project scaffold as an executable local adapter.

## Decision

Seed mode remains the current executable demonstration.

The live test should wait for backend adapter confirmation from the toolkit creator or a clearly approved API/client that can return bounded search results with URL, title, snippet, source domain, date, and retrieval status.

## Guardrails Preserved

- No general search-engine result page was scraped.
- No paywalled, authenticated, blocked, or licensed source was used.
- No anti-bot barrier was bypassed.
- No documents were ingested.
- No production datasets were created or modified.
