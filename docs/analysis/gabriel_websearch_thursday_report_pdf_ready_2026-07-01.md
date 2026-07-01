# City-by-City Public-Source Discovery and Extraction with a Custom GABRIEL Web-Search Callback

**Date:** 2026-07-01  
**Status:** PDF-ready abbreviated draft; seed/dry-run scaffold only

## 1. Executive summary

- No built-in local GABRIEL web-search function was found in this repo.
- We implemented a custom `get_all_responses_fn` scaffold as the integration boundary for city-by-city discovery plus extraction.
- The scaffold currently returns GABRIEL-compatible `Identifier` / `Response` dataframe output with parseable JSON payloads.
- A proposed live `web_search` contract is now concrete enough for adapter-fit discussion.
- The five-city seed harness covers Boston, Somerville, Newton, Wayland, and Seekonk.
- Current outputs are 5 city responses, 15 source rows, and 34 extraction rows.
- No live web search was executed and no ingestion was performed.

## 2. Problem and goal

The immediate problem is not scoring local text. It is finding public, reasoning-rich municipal labor sources city by city: awards, JLMC materials, bargaining packets, mediation proposals, committee presentations, and clean public CBAs.

The goal of this scaffold is to help with that acquisition step. It is designed to discover candidate sources, classify them into the right lane, and extract short structured evidence before any later manual ingestion decision.

This is an acquisition/extraction assistant scaffold. It is not production measurement, not automatic ingestion, not causal evidence, and not broad scraping.

## 3. What we built

- A custom GABRIEL callback scaffold: `custom_get_all_responses(...)`.
- A proposed bounded live backend contract:

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

## 4. Proposed callback and backend contract

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

Expected discovery fields from a live backend are:

- `title`
- `url`
- `snippet`
- `source_domain`
- `published_date`
- `retrieval_status`

The contract is intentionally small. That keeps it easy to adapt if the toolkit backend already returns something close but not identical.

## 5. Five-city seed demo

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

## 6. Worked example

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

## 7. Design choices and guardrails

Key design choices:

| Design choice | Decision | Reason |
| --- | --- | --- |
| backend contract | Small bounded `web_search` signature | Keeps the adapter surface narrow |
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

## 8. What we need to confirm Thursday

The open questions are adapter-fit questions, not blockers:

- Does the existing backend already match the proposed `web_search` signature?
- If not, what fields does it return and what adapter is needed?
- Will the live backend return snippets only, page text, or both?
- Should extraction happen inside the callback or in a second GABRIEL pass?
- Is there an official error-object format?
- What rate limits matter for a bounded five-city test?

## 9. Optional live smoke test

A one-city Boston live smoke test was considered but not executed because no safe repo-local search backend or approved search API client was available. The report remains seed-mode only. The adapter contract is ready for toolkit-creator confirmation, and no ingestion was performed.

## 10. Next live-test plan

If a safe backend is available, the first live test should stay tightly bounded:

- same five cities;
- domain filters on;
- max six queries per city;
- max five results per query;
- retain max ten sources per city;
- extract max three spans per source;
- compare live outputs to seeded calibration rows;
- keep ingestion separate.

Bottom line: the scaffold is ready as a bounded acquisition/extraction assistant. The next step is adapter confirmation and then a five-city live test, not immediate production use.
