# Next task: bounded GABRIEL claim-oriented attribute rating

Do not run this task without new explicit user authorization.

The current decision is `claim_oriented_phase_closed_gabriel_claim_rating_ready`. Run only the complete prepared prompt at `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25/next_gabriel_claim_oriented_attribute_rating_prompt.md`, and only after new explicit user authorization.

Use only the 643 exact-span rows in `gabriel_claim_rating_ready_evidence_manifest.csv`. Apply the stable `v1` 13-attribute codebook, require exact supporting quotes and claim boundaries, validate every rating against the source/evidence schema, and quarantine invalid model output.

Do not fetch sources, open PDFs/pages, OCR, extract, select documents, ingest, codify, compute cross-document statistics, calculate wage gaps, run regressions, or make final causal claims. Preserve all other categories and lanes outside the model input, label causal candidates as provisional, and keep global analysis readiness false.
