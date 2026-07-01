# GABRIEL Web-Search Custom Function Design

**Date:** 2026-06-30  
**Status:** scaffold implemented in seed/dry-run mode; no live web search executed

## Important framing update

After inspecting the tutorial guidance summarized for this project, built-in GABRIEL web mode is the primary live path and should be tested first.

The primary path to confirm is `gabriel.whatever(..., web_search=True)` for a city report, followed by either `gabriel.extract(..., modality="web")` or light structured parsing if the report needs to be converted into project source/extraction rows.

The custom callback scaffold documented here remains useful only if:

- built-in web mode does not preserve the project's source/extraction schema well enough;
- built-in web outputs are not structured enough for reliable downstream parsing; or
- a nonstandard backend is required.

In other words, this memo describes fallback/advanced infrastructure for schema control or nonstandard backends. It should not be presented as the project's primary built-in web-search route.

Update after the Boston smoke-test attempt: `openai-gabriel` 1.1.8 installed and exposed the built-in web parameters, so the custom callback is not needed to make GABRIEL importable. The remaining blocker is that the native `gabriel.whatever(web_search=True)` call returned no response through the current Harvard HUIT proxy path. That should be resolved at the built-in/proxy layer before treating the custom callback as a substitute.

## 1. Purpose

This memo documents a Thursday demonstration scaffold for routing bounded city-by-city public-source search and extraction through GABRIEL's custom full-prompt hook, without pretending that a live local search backend already exists.

The immediate goal is fallback integration shape, not production acquisition, ingestion, or causal measurement.

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
- `**kwargs`: optional bounded live controls such as `enable_live_web_search`, `max_results`, and `domain_filters`

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
  "error_type": null,
  "error_message": null,
  "json_mode_requested": true,
  "streaming_supported": false,
  "source_candidates": [...],
  "extractions": [...],
  "notes": [...]
}
```

`Response` is always serialized as a parseable JSON string regardless of `json_mode`.

## 7. Seed / Dry-Run Behavior

Default behavior is seed-only.

The scaffold reads:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`
- `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`

For each pilot city response, it returns:

- all seed source rows for that city in `source_candidates`
- all seed extraction rows for that city in `extractions`
- a clear `status` of `seed_dry_run`
- `search_config` with domain filters and result caps
- `web_search_contract` describing the expected backend signature
- notes explicitly stating that live web search was not executed

If a city cannot be resolved from the prompt or identifier, the function returns empty arrays with status `error` and `error_type = city_resolution_error`.

## 8. Proposed Live Backend Contract

The scaffold now assumes this exact callable shape:

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

Each returned result dict is expected to include:

- `title`
- `url`
- `snippet`
- `source_domain`
- `published_date`
- `retrieval_status`

This is a source-discovery contract. The scaffold preserves URLs and snippets explicitly, then leaves extraction inside `custom_get_all_responses`.

## 9. Domain Filters And Max Results

Live mode is intentionally bounded and off by default.

Domain filters mean limiting search to official or otherwise high-value public domains before broader public pages are considered. In the current pilot builder, those defaults are:

- Boston: `bostonpublicschools.org`, `boston.gov`, `btu.org`, `mass.gov`
- Somerville: `somervillema.gov`, `somerville.k12.ma.us`, `mass.gov`, `somervilleeducators.com`
- Newton: `newton.k12.ma.us`, `newteach.org`, `mass.gov`
- Wayland: `wayland.ma.us`, `mass.gov`
- Seekonk: `seekonk-ma.gov`, `seekonkschools.org`

The builder also exposes:

- `max_results_per_query`
- `max_sources_retained`
- `max_extractions_per_source`

These caps are intended to keep the Thursday workflow token-bounded and city-bounded.

## 10. Optional Live `web_search` Behavior

Live mode is intentionally bounded and off by default.

It activates only if both are true:

- `web_search` is callable
- `enable_live_web_search=True` is passed

If enabled, the scaffold attempts to call:

```python
web_search(
    prompt,
    max_results=max_results,
    domains=domains,
    city=city,
    state=state,
)
```

Current default bounds:

- `max_results=5`
- city-specific default domain filters from the prompt builder

The current live path does not stream and returns a complete dataframe only.

If the backend fails, the function falls back to seeded output with status `live_backend_failed_fallback_to_seed`.

Because no safe backend is present locally, this live path remains unexecuted in this repo.

## 11. Error Format

The scaffold does not retry. On errors, it returns structured fields inside the JSON response:

- `status = error` or `live_backend_failed_fallback_to_seed`
- `error_type`
- `error_message`
- `source_candidates`
- `extractions`
- `notes`

Examples:

- unresolved city: `status = error`, `error_type = city_resolution_error`
- live backend shape mismatch: `status = error`, `error_type = live_backend_shape_error`
- live backend exception with seed fallback: `status = live_backend_failed_fallback_to_seed`

## 12. Citation And Source URL Preservation

The scaffold explicitly preserves source URLs and snippets in the response payload.

In seed mode, source candidates include:

- `source_url`
- `short_evidence_snippet`
- `search_snippet`
- `page_text_excerpt`
- `evidence_origin`

In a future live mode, source candidates are expected to preserve:

- `url`
- `snippet`
- `source_domain`
- `evidence_origin = live_search_snippet`

This keeps source discovery provenance visible before any later extraction stage.

## 13. Two-Stage Token-Efficient Design

The intended design is:

1. source discovery with URLs and snippets
2. GABRIEL extraction only on retained candidates

That is the token-efficient path because it avoids doing extraction on every raw search hit. The current seed mode emulates the final output shape by returning both `source_candidates` and `extractions` in one payload, but conceptually those represent two stages.

## 14. Schema Mapping From Seed Files Into `Response`

`source_candidates` preserves the schema from:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`

Columns preserved:

- `search_id`, `search_date`, `city`, `state`, `query`, `result_rank`, `source_title`, `source_url`, `source_owner`, `source_owner_type`, `publication_or_document_date`, `retrieval_status`, `document_type_guess`, `unit_or_occupation_guess`, `occupation_class_guess`, `safety_flag_guess`, `cycle_start_guess`, `cycle_end_guess`, `source_corpus_recommendation`, `source_type_recommendation`, `causal_candidate`, `mechanism_proxy_candidate`, `discourse_candidate`, `lead_only`, `comparability_signal`, `arbitration_impasse_signal`, `wage_reasoning_signal`, `named_comparator_signal`, `download_or_ingest_recommendation`, `reason_for_recommendation`, `short_evidence_snippet`, `notes`

`extractions` preserves the schema from:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`

Columns preserved:

- `extraction_id`, `search_id`, `city`, `state`, `source_title`, `source_url`, `source_owner`, `document_type_guess`, `source_corpus_recommendation`, `unit_or_occupation_guess`, `occupation_class_guess`, `safety_flag_guess`, `cycle_or_document_date`, `attribute`, `attribute_signal`, `score_or_level`, `short_verbatim_excerpt`, `named_comparator_cities`, `impasse_process_terms`, `wage_terms`, `evidence_relevance`, `extraction_confidence`, `ingestion_recommendation`, `notes`

## 15. Why No Streaming For Now

Streaming is not supported because the immediate Thursday artifact is a complete dataframe-returning hook, not a UI transport layer. The integration point under discussion is batch-oriented: list of prompts in, dataframe out.

Holding the response until the full payload is available also keeps the source-candidate and extraction payloads aligned per identifier and avoids partial-state handling while the backend contract is still unsettled.

## 16. Thursday Toolkit Discussion Use

Use this scaffold as a concrete interface proposal, not as proof that live search is already integrated.

Recommended Thursday framing:

- show the function signature and returned dataframe shape
- show the proposed `web_search(query, *, max_results, domains, city, state)` contract
- show one seed response payload for a pilot city
- show that the response can be flattened back into source and extraction tables
- emphasize the two-stage design: source discovery first, extraction second
- emphasize that the current scaffold is compatible with city-by-city bounded execution and no streaming
- ask the toolkit creator whether their actual backend can satisfy this contract cleanly

## 17. Questions For The Toolkit Creator

1. Does the actual backend already accept `query`, `max_results`, `domains`, `city`, and `state`, or does the wrapper need to adapt to a different callable?
2. Are URLs and snippets always preserved in the backend result, or are they sometimes omitted?
3. If a page fetch happens after discovery, what object carries page text and citations into extraction?
4. How should rate limits be handled at the query level and the retained-source extraction level?
5. Is JSON mode relevant to the backend itself, or only to downstream model extraction calls?
6. Is the expected production pattern really one hook that handles both discovery and extraction, or should discovery and extraction be split into separate GABRIEL calls later?
