# Next task: bounded provisional claim review

Use only the completed 636-row valid-rating summaries. Preserve the seven quarantine rows as explicit exclusions. Review the documentary and provisional claim scaffold; do not rerate evidence or analyze the separate 862-row quantitative lane.

## Hard constraints

- Do not fetch or pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs or use hosted search.
- Do not download or redownload documents.
- Do not open PDFs or access PDF pages.
- Do not run OCR or use OCR-later documents or rendered images.
- Do not call GABRIEL/API or any model.
- Do not run scout or source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- Do not create a final or global analysis-facing dataset.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not use evidence outside the supplied exact spans or the 636 valid-rating summaries.
- Do not include the seven quarantine rows in claims.
- Do not save raw prompts, raw responses, credentials, secrets, tokens, cookies, auth headers, or environment values.
- Do not mutate upstream rating, evidence, repair, extraction, QA, or durable ledgers.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof and mechanism language is not evidence of realized wage effects.

Decision lineage: `gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed`.
