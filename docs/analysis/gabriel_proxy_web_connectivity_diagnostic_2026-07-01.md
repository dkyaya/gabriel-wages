# GABRIEL Proxy Web Connectivity Diagnostic

**Date:** 2026-07-01
**Scope:** Minimal connectivity diagnostic only; no ingestion and no production data changes.

## Result

Most likely category: **unknown**.

All four minimal diagnostic calls succeeded in the final approved run. That means the earlier Boston failure is not reproduced by tiny proxy, GABRIEL non-web, GABRIEL web-search, or raw Responses web-search checks; it may have been transient or specific to the larger Boston prompt/output path.

## Tests

| Test | Attempted | Success | Error type | Error message short | Endpoint/path | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| raw_openai_proxy_no_web | yes | yes |  |  | /chat/completions via Harvard proxy | Raw chat-completions call returned non-empty text; response text not recorded. |
| gabriel_non_web_proxy | yes | yes |  |  | gabriel.whatever(web_search=False) via Harvard proxy | GABRIEL non-web call returned non-empty text; response text not recorded. |
| gabriel_web_search_proxy | yes | yes |  |  | gabriel.whatever(web_search=True, search_context_size="low") via Harvard proxy | GABRIEL web-search call returned non-empty text; response text not recorded. |
| raw_openai_responses_web_search_proxy | yes | yes |  |  | /responses tools=[web_search] via Harvard proxy | Raw Responses API web-search tool request returned status=completed; response text not recorded. |

## Interpretation

- Raw non-web OpenAI success isolates base proxy URL, key, and header wiring.
- GABRIEL non-web success isolates ordinary `openai-gabriel` proxy compatibility.
- GABRIEL web-search failure after those two successes points to hosted web-search-tool support or GABRIEL's web-tool request shape.
- Raw Responses API web-search success would shift the likely issue toward the GABRIEL wrapper; raw web-search failure would shift it toward Harvard proxy hosted-tool support.
- In this final run, both web-search checks succeeded, so the diagnostic does not isolate a persistent proxy or hosted-tool incompatibility.

No API key or response text was written to this memo.
