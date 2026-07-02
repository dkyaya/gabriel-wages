# GABRIEL Web-Search Thursday Presentation Outline

## Slide 1

**Title:** Why search/extraction matters for the wage project

- The project needs public documents that explain wage-setting logic, not only final CBAs.
- The operational bottleneck is city-by-city discovery of reasoning-rich municipal labor sources.
- Search assistance is most useful upstream, before manual ingestion and formal measurement.

Suggested visual/table if any: simple workflow strip showing `source discovery -> evidence extraction -> manual review`.

## Slide 2

**Title:** What GABRIEL was asked to do

- Search Massachusetts cities one by one rather than run broad generic retrieval.
- Return multiple source attributes, not just URLs.
- Extract short evidence spans from retained sources.
- Support discovery, classification, and extraction in one bounded workflow.

Suggested visual/table if any: small four-box diagram with `discover`, `classify`, `extract`, `review`.

## Slide 3

**Title:** Built-in path is the primary live path

- The tutorial indicates built-in GABRIEL web mode should be tested first.
- `gabriel.whatever(..., web_search=True)` is the main report-first route.
- The custom callback remains fallback infrastructure for schema control, not the default live path.
- The repo issue was project wiring, not lack of conceptual web capability.

Suggested visual/table if any: two-column table, `primary live path` vs `fallback path`.

## Slide 4

**Title:** Current package status

- Seed scaffold is ready: 5 city responses, 15 source rows, 34 extraction rows.
- `openai-gabriel` 1.1.8 is installed/imported.
- Built-in path confirmed: `gabriel.whatever(web_search=True)`.
- No ingestion or production data creation happened.

Suggested visual/table if any: compact status table.

## Slide 5

**Title:** Boston live testing sequence

- Larger Boston structured prompt failed with connection errors.
- Minimal diagnostics all succeeded.
- Graduated Boston retry:
  - attempt 1 failed
  - attempt 2 succeeded
  - attempt 3 skipped
- Returned source rows: 1; working extraction rows: 1.

Suggested visual/table if any: 3-row attempt table.

## Slide 6

**Title:** What the bounded success returned

- Returned source: BPS `BTU Contract Negotiations`.
- URL preserved: yes.
- Boston BTU/BPS material rediscovered: yes.
- Ingestion: no.
- This is a working source-discovery result, not a production extraction pipeline.

Suggested visual/table if any: one-row source callout table.

## Slide 7

**Title:** Thursday message

- Built-in GABRIEL web mode works on a bounded Boston source-discovery query through the Harvard proxy.
- The live finding is no longer “blocked.”
- The remaining issue is stability for larger structured extraction prompts.
- This is a bounded operational result, not a causal claim.

Suggested visual/table if any: one highlighted message box.

## Slide 8

**Title:** Compact results table

- Seed scaffold: 5 city responses, 15 source rows, 34 extraction rows.
- Package install: `openai-gabriel` 1.1.8 installed/imported.
- Large Boston prompt: connection errors.
- Minimal diagnostics: all succeeded.
- Graduated Boston retry: attempt 2 succeeded.

Suggested visual/table if any: reuse the 3-column report table verbatim.

## Slide 9

**Title:** What not to over-claim

- Do not claim full structured extraction stability yet.
- Do not claim ingestion readiness.
- Do not claim five-city live readiness.
- Do not create numeric plots from the one successful live retry.

Suggested visual/table if any: short guardrail checklist.

## Slide 10

**Title:** Next technical step

- Keep the next technical run Boston-only.
- Tune one dimension at a time:
  - prompt size
  - output cap
  - source metadata handling
  - timeout behavior
- Use the fallback callback only if built-in output structure remains insufficient.

Suggested visual/table if any: simple progression strip `bounded Boston success -> Boston structured tuning -> broader pilot decision`.
