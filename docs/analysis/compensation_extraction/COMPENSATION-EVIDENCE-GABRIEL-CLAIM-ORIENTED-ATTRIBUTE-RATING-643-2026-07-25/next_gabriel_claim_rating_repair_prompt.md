# Next task: bounded GABRIEL claim-rating quarantine repair

Decision: `gabriel_claim_rating_643_completed_with_quarantine`. Use only the schema-valid v1.1 row-level ratings and explicit quarantine metadata from `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-GABRIEL-CLAIM-ORIENTED-ATTRIBUTE-RATING-643-2026-07-25`.

Repair only the 35 explicitly quarantined IDs. Start with deterministic validation diagnostics; any model retry must be separately authorized, bounded to those IDs, and use the unchanged v1.1 schema. Do not compute cross-row summaries. Preserve document-level scope and do not treat ratings as wage effects or causal proof.

## Hard constraints

- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs or use hosted search.
- Do not download documents.
- Do not open PDFs or access PDF pages.
- Do not run OCR or use rendered images.
- Do not run scout, source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- Do not call GABRIEL/API or any model unless the repair task separately authorizes a bounded retry over only the quarantined IDs.
- Do not compute cross-row descriptive or inferential statistics during a quarantine repair.
- Do not calculate wage gaps or run regressions.
- Do not make final causal claims.
- Do not save raw prompts, raw responses, credentials, tokens, cookies, headers, or environment values.
- Do not include rows outside the valid rating output and explicit quarantine metadata.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof.
