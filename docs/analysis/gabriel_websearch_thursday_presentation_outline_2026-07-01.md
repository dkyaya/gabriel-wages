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

**Title:** Tutorial correction: primary live path vs fallback path

- The tutorial indicates built-in GABRIEL web mode should be the main live path.
- `modality="web"` and `web_search=True` are standard routes; `get_all_responses_fn` is the advanced route.
- That changes the framing: test built-in web mode first, use the custom callback only if schema control is needed.
- The repo issue is not conceptual lack of web mode; it is lack of project wiring into the city-by-city source schema.

Suggested visual/table if any: two-column table, `primary live path` vs `fallback path`.

## Slide 4

**Title:** What we found locally

- Existing runners score already-local text inputs.
- `ingest/fetchers/` is portal-specific scaffolding, not a generic city web-search workflow.
- The repo had not yet wired built-in GABRIEL web mode into the project's source/extraction tables.
- That made a fallback scaffold useful, but not primary.

Suggested visual/table if any: two-column table, `present locally` vs `still to wire`.

## Slide 5

**Title:** Built-in live path to test first

- Primary path should be `gabriel.whatever(..., web_search=True)` for city web reports.
- Use `web_search_filters` for city/domain control.
- Use `search_context_size` to tune report richness.
- Then run `gabriel.extract` or light structured parsing on those reports.

Suggested visual/table if any: one short workflow strip or compact parameter table.

## Slide 6

**Title:** Custom callback scaffold as fallback/advanced option

- Implemented `custom_get_all_responses(...)` as a fallback `get_all_responses_fn` scaffold.
- Input is prompt batch plus identifiers; output is a dataframe with `Identifier` and `Response`.
- `Response` is always parseable JSON and includes source candidates, extractions, config, and notes.
- This remains useful if built-in web outputs are not structured enough.

Suggested visual/table if any: short code signature plus one sample JSON field list.

## Slide 7

**Title:** Five-city seed demo

- Seed cities: Boston, Somerville, Newton, Wayland, Seekonk.
- Outputs: 5 city responses, 15 source rows, 34 extraction rows.
- Live web search executed: no.
- Ingestion performed: no.

Suggested visual/table if any: compact city table with source and extraction counts.

## Slide 8

**Title:** Worked JSON example

- Show one short seeded payload example, ideally Boston.
- Highlight `Identifier`, `city`, `status`, source-candidate count, extraction count, one source example, and one extraction example.
- Emphasize that the callback output is already shaped for flattening into working tables.

Suggested visual/table if any: small JSON callout box or two-column `field` / `example value` table.

## Slide 9

**Title:** Example source classifications

- Boston BTU: mechanism-proxy, high comparability, not impasse evidence.
- Somerville police awards: causal calibration positives for JLMC/arbitration.
- Wayland fire JLMC: positive impasse-pathway example.
- Seekonk official archive: clean ingestability check; Newton: mostly manual-review or mechanism-proxy leads.

Suggested visual/table if any: 5-row example table with `city`, `source`, `lane`, `why it matters`.

## Slide 10

**Title:** Guardrails and corpus separation

- No automatic ingestion, no PRRs, no licensed or paywalled search targets.
- No broad scraping and no causal claims.
- Keep causal, mechanism-proxy, discourse, and lead-only lanes separate.
- Do not treat grievance arbitration or peer-wage comparison alone as impasse evidence.

Suggested visual/table if any: guardrail checklist.

## Slide 11

**Title:** Next test after the tutorial correction

- Next test is a Boston-only built-in GABRIEL web smoke test.
- Confirm exact invocation details and built-in output structure first.
- Use the custom callback only if project-specific schema control is still required.
- Keep ingestion separate.

Suggested visual/table if any: next-step box with `Boston built-in smoke test -> assess output structure -> decide if fallback is needed`.
