# GABRIEL Web-Search Custom Function Design

**Date:** 2026-06-30  
**Status:** scaffold implemented in seed/dry-run mode; no live web search executed

## 1. Purpose

This memo documents a Thursday demonstration scaffold for routing bounded city-by-city public-source search and extraction through GABRIEL's custom full-prompt hook, without pretending that a live local search backend already exists.

The immediate goal is integration shape, not production acquisition, ingestion, or causal measurement.

## 2. GABRIEL Tutorial Hook Being Used

The hook assumed here is the tutorial pattern:

`get_all_responses_fn = custom_get_all_responses`

This repo did **not** contain a local built-in implementation of that hook. The new scaffold therefore implements the expected callable locally in:

- `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py`

## 3. What Is Actually Present Locally

Local inspection found:

- no matches in the repo for `response_fn`
- no matches in the repo for `get_all_responses_fn`
- no matches in the repo for `embedding_fn`
- no matches in the repo for `get_all_embeddings_fn`
- no matches in the repo for `json_mode`
- no matches in the repo for `web_search`

What **is** present:

- `analysis/gabriel_pilot/run_gabriel.py` and `run_gabriel_v10_gold_dryrun.py` call the OpenAI client directly on already assembled local text.
- `analysis/gabriel_pilot/run_gabriel_v9.py` is a wrapper around `run_gabriel.py`.
- `ingest/extract_spans.py` uses a direct OpenAI client for bounded span extraction fallback.
- `ingest/fetchers/` is fetcher scaffolding for open portals, not a generic GABRIEL web-search interface.

So the repo's current pattern is direct model invocation on local text, not a reusable search/extraction callback interface.

## 4. Proposed `custom_get_all_responses` Signature

```python
custom_get_all_responses(
    prompts,
    identifiers,
    json_mode=False,
    model=None,
    api_key=None,
    web_search=None,
    **kwargs,
)
```

## 5. Input Expectations

- `prompts`: list of prompt strings
- `identifiers`: list of equal-length identifiers
- `json_mode`: optional compatibility flag for future GABRIEL use
- `model`: optional passthrough for future backend use
- `api_key`: optional passthrough for future backend use
- `web_search`: optional callable for a future live search backend
- `**kwargs`: optional bounded live controls such as `enable_live_web_search`, `live_max_results`, and `live_query_limit`

Current city resolution is pilot-scoped and expects either:

- a known pilot city named in the prompt, or
- an identifier of the form `gabriel_websearch_city_{city}_2026_06_30`

## 6. Output Expectations

The function returns a pandas dataframe with exactly these columns:

- `Identifier`
- `Response`

`Response` is a JSON string with this shape:

```json
{
  "city": "Boston",
  "identifier": "gabriel_websearch_city_boston_2026_06_30",
  "status": "seed_dry_run",
  "json_mode_requested": true,
  "source_candidates": [...],
  "extractions": [...],
  "notes": [...]
}
```

## 7. Seed / Dry-Run Behavior

Default behavior is seed-only.

The scaffold reads:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`
- `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`

For each pilot city response, it returns:

- all seed source rows for that city in `source_candidates`
- all seed extraction rows for that city in `extractions`
- a clear `status` of `seed_dry_run`
- notes explicitly stating that live web search was not executed

If a city cannot be resolved from the prompt or identifier, the function returns empty arrays with status `no_seed_data_for_city`.

## 8. Optional Live `web_search` Behavior

Live mode is intentionally bounded and off by default.

It activates only if both are true:

- `web_search` is callable
- `enable_live_web_search=True` is passed

If enabled, the scaffold attempts to call:

```python
web_search(
    prompt=prompt,
    identifier=identifier,
    city=city,
    json_mode=json_mode,
    model=model,
    api_key=api_key,
    max_results=live_max_results,
    query_limit=live_query_limit,
    **kwargs,
)
```

Current default bounds:

- `live_max_results=5`
- `live_query_limit=3`

If the backend fails, the function falls back to seeded output with status `live_backend_failed_fallback_to_seed`.

Because the toolkit creator has not yet specified the callable shape or return object, this live path is a placeholder only.

## 9. Schema Mapping From Seed Files Into `Response`

`source_candidates` preserves the schema from:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`

Columns preserved:

- `search_id`, `search_date`, `city`, `state`, `query`, `result_rank`, `source_title`, `source_url`, `source_owner`, `source_owner_type`, `publication_or_document_date`, `retrieval_status`, `document_type_guess`, `unit_or_occupation_guess`, `occupation_class_guess`, `safety_flag_guess`, `cycle_start_guess`, `cycle_end_guess`, `source_corpus_recommendation`, `source_type_recommendation`, `causal_candidate`, `mechanism_proxy_candidate`, `discourse_candidate`, `lead_only`, `comparability_signal`, `arbitration_impasse_signal`, `wage_reasoning_signal`, `named_comparator_signal`, `download_or_ingest_recommendation`, `reason_for_recommendation`, `short_evidence_snippet`, `notes`

`extractions` preserves the schema from:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`

Columns preserved:

- `extraction_id`, `search_id`, `city`, `state`, `source_title`, `source_url`, `source_owner`, `document_type_guess`, `source_corpus_recommendation`, `unit_or_occupation_guess`, `occupation_class_guess`, `safety_flag_guess`, `cycle_or_document_date`, `attribute`, `attribute_signal`, `score_or_level`, `short_verbatim_excerpt`, `named_comparator_cities`, `impasse_process_terms`, `wage_terms`, `evidence_relevance`, `extraction_confidence`, `ingestion_recommendation`, `notes`

## 10. Thursday Toolkit Discussion Use

Use this scaffold as a concrete interface proposal, not as proof that live search is already integrated.

Recommended Thursday framing:

- show the function signature and returned dataframe shape
- show one seed response payload for a pilot city
- show that the response can be flattened back into source and extraction tables
- emphasize that the current scaffold is compatible with city-by-city bounded execution
- ask the toolkit creator how their actual `web_search` callable plugs into this shape

## 11. Questions For The Toolkit Creator

1. What exact object or function is passed as `web_search`?
2. Does it return URLs, snippets, page text, or structured documents?
3. Does it support domain filters or max results?
4. How should rate limits be handled?
5. Should extraction happen inside `custom_get_all_responses` or as a second GABRIEL call?
6. Is JSON mode supported for web-search responses?
7. Are citations and source URLs preserved automatically?
8. Can the function stream, or must it return a full dataframe?
9. What retry or error format is expected?
