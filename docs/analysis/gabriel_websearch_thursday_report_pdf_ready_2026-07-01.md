# City-by-City Public-Source Discovery and Extraction with GABRIEL Web Mode

**Date:** 2026-07-01  
**Status:** PDF-ready abbreviated draft; framework corrected after tutorial clarification; `openai-gabriel` installed, native web call attempted, no response returned

## 1. Executive summary

- The tutorial clarification indicates built-in GABRIEL web mode should be the primary live path.
- This repo had not yet wired built-in web mode into the project's city-by-city source and extraction schema.
- We implemented a custom `get_all_responses_fn` scaffold as a fallback and advanced schema-control path.
- The scaffold currently returns GABRIEL-compatible `Identifier` / `Response` dataframe output with parseable JSON payloads.
- A proposed fallback `web_search` contract is now concrete enough for adapter-fit discussion if the built-in path is not structured enough.
- The five-city seed harness covers Boston, Somerville, Newton, Wayland, and Seekonk.
- Current outputs are 5 city responses, 15 source rows, and 34 extraction rows.
- A Boston-only built-in GABRIEL web smoke test was attempted after installing `openai-gabriel` 1.1.8. The native web path was callable, but the one live request returned no response and GABRIEL recorded connection errors.
- No ingestion was performed.

## 2. Problem and goal

The immediate problem is not scoring local text. It is finding public, reasoning-rich municipal labor sources city by city: awards, JLMC materials, bargaining packets, mediation proposals, committee presentations, and clean public CBAs.

The goal of this framework is to help with that acquisition step. It is designed to discover candidate sources, classify them into the right lane, and extract short structured evidence before any later manual ingestion decision.

This is an acquisition/extraction assistant framework. It is not production measurement, not automatic ingestion, not causal evidence, and not broad scraping.

## 3. What we built

- A corrected framework that puts built-in GABRIEL web mode first.
- A custom GABRIEL callback scaffold: `custom_get_all_responses(...)`.
- A proposed bounded fallback backend contract:

```python
web_search(
    query: str,
    *,
    max_results: int = 5,
    domains: list[str] | None = None,
    city: str | None = None,
    state: str | None = None,
) -> list[dict]
```

- Two working output schemas:
  - source discovery;
  - evidence extraction.
- A five-city seed harness for calibration and Thursday discussion.

## 4. Primary path and fallback path

Primary live path after reading the tutorial:

- generate city web reports with `gabriel.whatever(..., web_search=True)`;
- constrain scope with `web_search_filters`;
- tune retrieved context with `search_context_size`;
- run `gabriel.extract` or structured parsing on those reports.

Fallback path:

- use `custom_get_all_responses(...)` only if project-specific schema control is needed or if built-in outputs are not structured enough.

## 5. Proposed callback and fallback backend contract

The callback takes prompt and identifier batches and returns a dataframe with:

- `Identifier`
- `Response`

`Response` is always parseable JSON. In seed mode it includes:

- `city`
- `status`
- `source_candidates`
- `extractions`
- `web_search_contract`
- `search_config`
- `notes`

Expected discovery fields from a live fallback backend are:

- `title`
- `url`
- `snippet`
- `source_domain`
- `published_date`
- `retrieval_status`

The fallback contract is intentionally small. That keeps it easy to adapt if the built-in path proves insufficient and a custom backend is still needed.

## 6. Five-city seed demo

The seed harness uses known public leads only. It is a dry-run scaffold, not a live search pilot.

| City | Source rows | Extraction rows | Calibration role |
| --- | ---: | ---: | --- |
| Boston | 3 | 7 | Non-safety peer-wage mechanism-proxy check |
| Somerville | 3 | 8 | Safety arbitration/JLMC positive calibration |
| Newton | 3 | 7 | Mediation and MOA edge-case review |
| Wayland | 3 | 6 | JLMC positive plus grievance-arbitration exclusion |
| Seekonk | 3 | 6 | Clean official archive ingestability check |

Total seed outputs:

- 5 city responses
- 15 source rows
- 34 extraction rows
- Live search executed: no
- Ingestion performed: no

## 7. Worked example

Short-form Boston example:

```json
{
  "Identifier": "gabriel_websearch_city_boston_2026_06_30",
  "city": "Boston",
  "status": "seed_dry_run",
  "source_candidates_count": 3,
  "extractions_count": 7,
  "example_source_candidate": {
    "source_title": "BTU contract negotiations page",
    "source_corpus_recommendation": "mechanism_proxy",
    "comparability_signal": "high"
  },
  "example_extraction": {
    "attribute": "comparability_emphasis",
    "attribute_signal": "high"
  },
  "notes": [
    "Live web search was not executed.",
    "Response is always parseable JSON."
  ]
}
```

## 8. Revised live path after reading the tutorial

- primary path: `gabriel.whatever(web_search=True)` to generate city web reports;
- extraction path: `gabriel.extract` or structured parsing on those reports;
- fallback path: custom `get_all_responses_fn` only if project-specific schema control is needed.

## 9. Design choices and guardrails

Key design choices:

| Design choice | Decision | Reason |
| --- | --- | --- |
| built-in live path | Test built-in GABRIEL web mode first | Aligns the project with the tutorial-default route |
| backend contract | Small bounded fallback `web_search` signature | Keeps the adapter surface narrow if custom plumbing is still needed |
| returned search fields | `title`, `url`, `snippet`, `source_domain`, `published_date`, `retrieval_status` | Preserves discovery provenance cleanly |
| domain filters | City-specific filters | Prioritizes official and high-value public sources |
| result caps | Hard caps on results, retained sources, and extractions | Keeps the workflow reviewable and token-efficient |
| always JSON response | Yes | Makes flattening and auditing deterministic |
| corpus-lane separation | Yes | Protects causal vs mechanism-proxy vs lead-only distinctions |

Guardrails:

- no automatic ingestion;
- no PRRs;
- no paywalled or licensed source acquisition;
- no broad scraping;
- no causal claims;
- no treating grievance arbitration as impasse evidence;
- no treating peer-wage comparison alone as impasse evidence.

## 10. What we need to confirm Thursday

The open questions are built-in web-mode fit questions, not blockers:

- What is the exact built-in invocation pattern in this environment?
- What output structure does built-in web mode return?
- Are `web_search_filters` enough for city/domain control?
- Should extraction happen through `gabriel.extract` or light structured parsing?
- If built-in outputs are not structured enough, what thin fallback adapter is needed?

## 11. Optional live smoke test

A one-city Boston live smoke test was considered but not executed. The corrected next step is a Boston-only built-in GABRIEL web smoke test after confirming invocation details and output structure in this environment. The report remains seed-mode only, and no ingestion was performed.

## 12. Built-in GABRIEL web smoke test

The Boston-only built-in smoke test advanced past the earlier package blocker:

- Package installed/imported: `openai-gabriel` 1.1.8.
- Native path callable: `gabriel.whatever(web_search=True)`.
- Intended scope: Boston BPS/BTU salary-comparison and contract-negotiation sources.
- Model/search context: `gpt-5.4-nano`, `search_context_size="low"`.
- Live call result: failed API/web call; GABRIEL recorded three connection errors, empty response text, and no web-search sources.
- Source rows created: 0.
- Extraction rows created: 0.
- Boston BTU rediscovered: no response returned.
- URLs/citations preserved: none returned.
- Ingestion: no.

The corrected framework still stands: built-in web mode is primary, and package availability is now resolved. The remaining question is whether the Harvard HUIT proxy supports built-in web-search tools through `openai-gabriel`, or whether the smoke test requires a standard OpenAI endpoint/key environment.

## 13. Next live-test plan

If a safe backend is available, the first live test should stay tightly bounded:

- Boston first, then the same five cities if the built-in path is adequate;
- domain filters on;
- max six queries per city;
- max five results per query;
- retain max ten sources per city;
- extract max three spans per source;
- compare live outputs to seeded calibration rows;
- keep ingestion separate.

Bottom line: built-in GABRIEL web mode should be tested first. The scaffold remains ready as a bounded fallback acquisition/extraction assistant if tighter schema control is needed.
