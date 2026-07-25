# Future prompt: automated text/table GABRIEL gate 2 refinement

This is a future calibration/refinement prompt. Do not run wage extraction.

## Starting point

Use the final outputs from
`TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`. Gate 1 achieved:

- 150/150 schema-valid GABRIEL adjudications;
- 6.82% wrong-page rate among candidate-bearing cases;
- 12 high-confidence ready rows;
- 16 schema-update ready rows;
- 19 second-review rows;
- 103 excluded rows;
- only 27/80 likely/p1 rows ready (33.75%).

The extraction decision is `continue_schema_refinement`. Neither 500-document
extraction nor a smaller pilot is authorized.

## Objective

Refine bounded candidate-page and table-family rules on the same 150 local
calibration artifacts. Focus on the 53 likely/p1 rows that did not receive a
ready label and the 19 second-review rows. Determine whether failures reflect:

- truly absent wage schedules;
- wage prose with no schedule;
- a missed exact/adjacent table page;
- a contents/index target not reached inside the page budget;
- a compact compensation sheet needing its own structural rule;
- benefit, budget, classification-only, front-matter, or non-wage tables;
- weak local geometry despite a true visible schedule.

## Required refinements

1. Preserve the six-page maximum, 1,500 characters per page, and 6,000
   characters per case.
2. Continue strict API JSON Schema output plus independent local validation.
3. Add deterministic reason codes for no-candidate versus wrong-candidate
   outcomes.
4. Audit whether the bounded navigation detector maps printed page numbers to
   PDF page numbers correctly without opening URLs or expanding to whole-PDF
   reading.
5. Define stronger visual/render features for row/column alignment and compact
   sheets without OCR.
6. Keep wage prose, benefits, budget/fiscal, classification-without-pay,
   front matter, and contents-only pages ineligible for high confidence.
7. Keep REVIEW1/REVIEW2 and gate-1 labels out of the primary adjudication
   prompt; use them only for post-run comparison.
8. Recompute likely/p1 ready rate, wrong-page rate, schema-valid rate,
   non-wage false positives, unit/source representation, and unresolved
   ambiguity.

## Stop conditions

Stop without extraction if:

- strict preflight fails;
- schema-valid rate is below 95%;
- likely/p1 ready rate is below 80%;
- wrong-page rate exceeds 15%;
- a systematic non-wage family remains extraction-positive;
- the ready set is not representative.

Do not run wage extraction, an extraction pilot, the 500-document prompt, OCR,
downloads, URL review, ingestion, `gabriel.codify`, wage-gap analysis, or
regressions.
