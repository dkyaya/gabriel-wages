# GABRIEL Web-Search Thursday Presentation Outline

## Slide 1

**Title:** Why search/extraction matters for the wage project

- The project needs more than final CBAs; it needs public documents that explain wage-setting logic.
- The current bottleneck is city-by-city discovery of reasoning-rich municipal labor sources.
- Search assistance is most valuable upstream, before manual ingestion and formal measurement.

Suggested visual/table if any: simple workflow strip showing `source discovery -> evidence extraction -> manual ingestion review`.

## Slide 2

**Title:** What GABRIEL was asked to do

- Search Massachusetts cities one by one rather than run broad generic retrieval.
- Return multiple source attributes, not just URLs.
- Extract short evidence spans from retained sources.
- Support discovery, classification, and extraction in one bounded workflow.

Suggested visual/table if any: small four-box diagram with `discover`, `classify`, `extract`, `review`.

## Slide 3

**Title:** What we found locally

- No built-in local GABRIEL web-search function was present in the repo.
- Existing runners score already-local text inputs.
- `ingest/fetchers/` is portal-specific scaffolding, not a generic search interface.
- That pushed us to the tutorial callback boundary rather than an existing search utility.

Suggested visual/table if any: two-column table, `present locally` vs `missing locally`.

## Slide 4

**Title:** Custom callback design

- Implemented `custom_get_all_responses(...)` as a custom `get_all_responses_fn` scaffold.
- Input is prompt batch plus identifiers; output is a dataframe with `Identifier` and `Response`.
- `Response` is always parseable JSON and includes source candidates, extractions, config, and notes.
- Current default mode is seed/dry-run only.

Suggested visual/table if any: short code signature plus one sample JSON field list.

## Slide 5

**Title:** Proposed live `web_search` contract

- Proposed contract is `web_search(query, *, max_results, domains, city, state) -> list[dict]`.
- Expected fields are `title`, `url`, `snippet`, `source_domain`, `published_date`, and `retrieval_status`.
- The contract is intentionally minimal so an existing backend can be adapted with low friction.
- Extraction is intended to happen after retained candidate selection.

Suggested visual/table if any: one-row API contract table with argument names and returned keys.

## Slide 6

**Title:** Five-city seed demo

- Seed cities: Boston, Somerville, Newton, Wayland, Seekonk.
- Outputs: 5 city responses, 15 source rows, 34 extraction rows.
- Live web search executed: no.
- Ingestion performed: no.

Suggested visual/table if any: compact city table with source and extraction counts.

## Slide 7

**Title:** Worked JSON example

- Show one short seeded payload example, ideally Boston.
- Highlight `Identifier`, `city`, `status`, source-candidate count, extraction count, one source example, and one extraction example.
- Emphasize that the callback output is already shaped for flattening into working tables.

Suggested visual/table if any: small JSON callout box or two-column `field` / `example value` table.

## Slide 8

**Title:** Example source classifications

- Boston BTU: mechanism-proxy, high comparability, not impasse evidence.
- Somerville police awards: causal calibration positives for JLMC/arbitration.
- Wayland fire JLMC: positive impasse-pathway example.
- Seekonk official archive: clean ingestability check; Newton: mostly manual-review or mechanism-proxy leads.

Suggested visual/table if any: 5-row example table with `city`, `source`, `lane`, `why it matters`.

## Slide 9

**Title:** Guardrails and corpus separation

- No automatic ingestion, no PRRs, no licensed or paywalled search targets.
- No broad scraping and no causal claims.
- Keep causal, mechanism-proxy, discourse, and lead-only lanes separate.
- Do not treat grievance arbitration or peer-wage comparison alone as impasse evidence.

Suggested visual/table if any: guardrail checklist.

## Slide 10

**Title:** Thursday decision points / next live pilot

- Confirm or revise the proposed backend contract.
- Decide whether extraction happens inside the callback or as a second GABRIEL pass.
- Decide whether the backend returns snippets only, page text, or both.
- Agree on first five-city live-test caps and keep ingestion separate.

Suggested visual/table if any: next-step box with `adapter confirmation -> five-city live pilot -> manual review`.
