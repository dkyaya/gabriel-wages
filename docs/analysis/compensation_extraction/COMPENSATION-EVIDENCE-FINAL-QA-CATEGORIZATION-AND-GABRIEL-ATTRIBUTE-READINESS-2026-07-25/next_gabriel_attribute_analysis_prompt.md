# Next task: bounded GABRIEL compensation-attribute analysis

Do not run this prompt without separate explicit user authorization.

Use only the 643 rows in `gabriel_attribute_ready_evidence_manifest.csv`. For each row, classify the exact provided evidence span using `gabriel_attribute_taxonomy_machine_readable.json`, `gabriel_attribute_schema_contract.json`, and `gabriel_attribute_assignment_prompt_template.md`. A future authorized run may call GABRIEL/API only for this bounded attribute assignment; it may not search for, retrieve, or extract evidence.

## Hard constraints

- Global analysis readiness remains false.
- GABRIEL analysis is not causal proof.
- Mechanism language is not evidence of wage effects.
- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs.
- Do not download or redownload documents.
- Do not open PDFs.
- Do not access PDF pages.
- Do not run OCR.
- Do not run extraction.
- Do not select new documents.
- Do not ingest.
- Do not run gabriel.codify.
- Do not compute descriptive statistics.
- Do not compute inferential statistics.
- Do not calculate wage gaps.
- Do not run regressions.
- Do not make causal claims.
- Do not save raw model responses, prompts, credentials, secrets, full page text, or full documents.
- Do not use navigation-only, companion/context, quarantined, or written-off rows as model inputs.
- Do not fabricate or paraphrase evidence. Evidence quotes must be exact substrings of the supplied span.
- Keep quantitative, non-base, reference/control, and conflict lanes separate.

Validate every model output against the schema and exact-span contract. Quarantine failed outputs rather than retrying indefinitely or weakening rules. Produce attribute assignments and QA metadata only; no statistics, effects, regressions, wage gaps, or causal conclusions.
