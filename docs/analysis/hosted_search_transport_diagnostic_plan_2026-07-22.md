# Hosted-Search Transport Diagnostic Plan — 2026-07-22

## Objective

Determine whether the established HUIT direct-SDK Responses route can complete hosted-search requests after two Tier 1 runs passed a no-search preflight but failed immediately on their first two search-enabled calls.

## Fixed bounded suite

The suite uses `gpt-5.4-nano`, a 30-second per-call timeout, low hosted-search context, one request at a time, and zero SDK retries. The CLI hard cap is four calls, but the planned suite has only three because no alternate low-cost model is documented as supported on this proxy.

| # | Kind | Exact prompt | Tools/search | Pass evidence |
|---:|---|---|---|---|
| 1 | No-search control | `Reply with OK.` | omitted | `OK`/`OK.`, response ID, positive output tokens |
| 2 | Trivial hosted-search query | `Use web search to answer in one sentence: what is the official website of the City of Boston?` | hosted `web_search`, context `low` | response ID, nonempty text, positive output tokens |
| 3 | Municipality-style hosted-search query | `Use web search and answer in JSON with keys municipality, state, source_type, url_count. Find whether Oklahoma City, OK has official municipal labor agreement or salary schedule pages. Return url_count as a number.` | hosted `web_search`, context `low` | response ID, nonempty text, positive output tokens, requested JSON keys and numeric `url_count` |
| 4 | Optional alternate-model comparison | not planned | not applicable | omitted because the repository documents no alternate low-cost model as supported on this HUIT route |

Maximum actual API/model calls: **3**, despite invoking the helper with `--max-calls 4`. There are no hidden retries.

## Execution order

First write a plan-only artifact set with `external_calls_attempted=0`. After confirming it contains no credentials and the planned suite is correct, run exactly one bounded live invocation into a separate fresh directory. Do not rerun it if it fails.

## Stop criteria

The helper stops before any further call when:

- the no-search control fails;
- two consecutive search-enabled transport/timeout failures occur;
- credential-like material is detected and redacted;
- the hard call ceiling would be exceeded.

## Interpretation

- **A:** no-search and both hosted-search calls pass. The route is currently healthy; a later fresh full Tier 1 retry can be considered. A diagnostic-only one-row scout probe is permitted by this task but remains optional.
- **B:** no-search passes but at least one search-enabled call fails before ID/text/tokens. Do not rerun the 150-row scout.
- **C:** the no-search control fails. Stop live/API work and address the baseline route.
- **D:** search transport returns ID/text/tokens but the requested output fails content/schema handling. Diagnose prompt/parser behavior before a full scout.

## Accounting boundary

The helper neither loads the Tier 1 input nor writes scout candidates. It does not open returned URLs and does not update national candidate queue, scout coverage, dashboard data, priority data, canonical contracts, city coverage, corpus, ingestion, codification, or claims. All content remains infrastructure-diagnostic only.
