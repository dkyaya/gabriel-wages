# Future prompt: automated GABRIEL Gate 3 visual-evidence refinement

This is a future instruction document. Do not run it as part of Gate 2.

## Objective

Determine whether Gate 2's 105 `no_candidate_page` judgments—especially the
43 original likely/p1 cases in that relationship—reflect genuinely absent
wage schedules or a failure to communicate visually present tables through
text-only bounded packets.

Use the same frozen 150 identities and existing local artifacts. Start with a
targeted diagnostic of the Gate 2 unresolved likely/p1 and second-review rows,
then rerun the full 150-case authorization gate only after a one-case dry/live
preflight chain succeeds.

## Required refinement

1. Add an opt-in vision-evidence mode that supplies only the already-rendered,
   listed page images for a bounded case. Confirm the configured backend/model
   supports safe image input before any call. Stop if it does not; do not
   silently fall back to heuristic-only adjudication.
2. Keep at most six pages per case and four navigation pages. Never send a
   whole PDF, open a URL, download, or run OCR.
3. Keep text caps at 1,500 characters per page and 6,000 per case. Do not save
   raw prompts, raw responses, full page text, table cells, or wage values.
4. Replace police/fire-specific row requirements with page-local structural
   evidence that can recognize arbitrary job titles aligned to repeated pay
   columns. Require table headers plus repeated row/column geometry; do not
   treat numeric density alone as a table.
5. Apply benefit, budget, front-matter, and classification-only vetoes at the
   page supporting the positive judgment, not merely because another bounded
   page contains those terms.
6. Treat printed-page offsets as navigation proposals only. A later-target
   judgment requires the proposed target page to be inside the packet and to
   show the supporting table.
7. Calibrate compact compensation sheets from direct role/pay mappings.
   Existing `compact_compensation_candidate` scores are overinclusive and may
   not authorize readiness alone.
8. Keep REVIEW1, REVIEW2, Gate 1, and Gate 2 labels out of primary prompts.
   They may be used only after completion for comparison.

## Required decision

Compute the unchanged thresholds over all 150 rows:

- at least 64/80 original likely/p1 cases ready with high/medium confidence;
- candidate-bearing wrong-page rate no more than 15%;
- schema-valid GABRIEL rate at least 95%;
- representative police/fire/non-safety and source-type coverage;
- no ready non-wage false positives or unresolved systematic table family.

Return exactly one decision: `500_doc_extraction_allowed`,
`smaller_extraction_pilot_only`, or `continue_schema_refinement`. Do not run an
extraction prompt or pilot during this calibration task.

## Boundary

No URLs, downloads, OCR, scouts, source review, URL verification, wage
extraction, ingestion, `gabriel.codify`, full-text/table retention, wage-gap
analysis, regressions, durable-ledger mutation, remote inspection, or push.
