# Hosted-Search Transport Diagnostic Results — 2026-07-22

## Result

**Diagnosis category A: the current direct-SDK route completed both no-search and hosted-search requests.** The suite made exactly three external calls under a four-call ceiling. Every call returned a response ID, nonempty text, and token usage; no exception, timeout, parser failure, or connection error occurred.

This rejects the narrow hypothesis that adding hosted search currently and independently causes immediate transport failure. It does not establish why the earlier two scout attempts failed: their identical subsecond `APIConnectionError` pattern remains most consistent with a transient outbound-network, HUIT proxy, or upstream transport condition that was not present during this diagnostic.

Artifacts: `tmp/hosted_search_transport_diagnostic_live_2026-07-22/`.

## Plan-only gate

The required plan-only invocation wrote three planned rows and recorded `external_calls_attempted=0`, `credential_values_loaded=false`, and `credential_values_logged=false`. All artifacts passed a credential-syntax scan before the live suite began.

Artifacts: `tmp/hosted_search_transport_diagnostic_plan_only_2026-07-22/`.

## Bounded live results

| Call | Search | Status | Response ID | Text | Input tokens | Reasoning tokens | Output tokens | Total tokens | Elapsed | Exception |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| No-search `Reply with OK.` | no | passed; returned `OK.` | present | present | 10 | 0 | 6 | 16 | 1.412s | none |
| City of Boston official-site query | yes | passed | present | present | 8,772 | 43 | 79 | 8,851 | 8.880s | none |
| Oklahoma City municipality-style query | yes | passed; requested JSON schema present | present | present | 17,319 | 844 | 964 | 18,283 | 21.450s | none |

The two hosted-search Responses objects exposed 39 and 43 source records respectively. Those URLs were not opened, downloaded, verified, promoted, or copied into national candidate accounting. Source counts here demonstrate tool execution only; they are not evidence about source quality or municipality availability.

## Failure-boundary interpretation

- No-search transport: healthy during this execution.
- Hosted-search trivial transport: healthy during this execution.
- Hosted-search municipality-style transport: healthy during this execution.
- Response extraction: healthy; IDs, text, and usage were present for all calls.
- Municipality-style content/schema: healthy for the diagnostic's small four-key JSON request.
- Timeouts: none.
- Exceptions: none.
- Parser/schema failures: none.
- Secret exposure: none detected; credential values were neither logged nor written.

Because the simple hosted-search calls passed, the helper did not identify a persistent search-only failure boundary. Because the same route had failed twice only minutes earlier, service or execution-context stability remains an operational risk; this is a point-in-time health result, not a guarantee for a 150-row duration.

## Optional model comparison

Not run. The repository documents `gpt-5.4-nano` as the supported low-cost model on this HUIT route and explicitly notes that `gpt-5.4-mini` has not been exercised there. Guessing an alternate model would add a confound and another external call without addressing the observed transport hypothesis.

## Accounting boundary

The three diagnostic responses are not scout evidence. No national queue, coverage, dashboard, priority, canonical contract, city-coverage, corpus, ingestion, codification, or claim file was changed. No returned URL was independently accessed.
