# Next task: bounded GABRIEL claim-oriented attribute rating

Do not run without separate explicit user authorization.

Rate only the 643 rows in `gabriel_claim_rating_ready_evidence_manifest.csv`. This is claim-oriented evidence measurement under `attribute_taxonomy_version = v1`; it is not generic tagging. Use the fixed codebook, schema, and prompt template. Require `supporting_quote` to be an exact substring of the supplied evidence span. Label any causal candidate as a provisional causal candidate requiring more evidence and testing. GABRIEL rating is not causal proof.

## Hard constraints

- Global analysis readiness remains false.
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
- Do not calculate wage gaps.
- Do not run regressions.
- Do not make final causal claims.
- Do not use navigation-only, companion/context, quarantined, or written-off rows as rating inputs.
- Do not alter the v1 definitions or controlled values.
- Do not fabricate, paraphrase, or supplement evidence with outside knowledge.
- Do not save raw model responses, raw prompts, credentials, secrets, full page text, or full documents.

Validate each returned object, verify exact quotes, and quarantine failures. Produce row-level ratings and QA metadata only. Do not compute cross-row descriptive statistics, national patterns, wage effects, wage gaps, regressions, or causal conclusions.
