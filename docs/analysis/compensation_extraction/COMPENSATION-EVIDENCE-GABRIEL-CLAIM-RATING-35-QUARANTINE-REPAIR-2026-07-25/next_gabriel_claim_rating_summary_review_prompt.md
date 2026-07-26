# Next task: GABRIEL claim-rating summary review

Decision: `gabriel_claim_rating_643_repaired_with_remaining_quarantine`. Review only the 636 schema-valid v1.1 ratings and preserve the 7 explicit remaining quarantine IDs as exclusions. Do not rerate them or reopen general QA. Compute only the explicitly authorized bounded summaries of the collected valid corpus.

## Hard constraints

- Do not fetch, pull, inspect remotes, or configure remotes.
- Do not open URLs, use hosted search, or download documents.
- Do not open PDFs, access PDF pages, run OCR, or use rendered images.
- Do not run scout, source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- Do not call GABRIEL/API or any model.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not use evidence outside the supplied exact spans.
- Do not save raw prompts, raw responses, credentials, tokens, cookies, auth headers, or environment values.
- Do not mutate upstream rating, evidence, extraction, QA, or durable ledgers.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof.
