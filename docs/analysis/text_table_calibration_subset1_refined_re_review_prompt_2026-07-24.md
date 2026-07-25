# Future Prompt: Refined Re-review of Calibration Subset 1

## Purpose

Run a new, bounded re-review of the same 150 calibration identities under
the refined visual table gate. This is a future task. **Do not run it as part
of refinement preparation.**

- calibration input:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv`
- prior diagnostic review:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
- new review ID:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`
- review mode: `refined_visual_gate_v1`

The original calibration input and all REVIEW1 outputs are immutable
provenance. REVIEW2 must write to a new directory.

## Scope and boundaries

The future task may open only the 150 retained local PDF artifacts named by
the calibration input. It must not open URLs, download or redownload files,
run OCR, call APIs/models/hosted search, run source review or scouts, extract
wage tables or final wage values, ingest documents, run `gabriel.codify`,
calculate wage gaps, or mutate any durable ledger.

Rendered pages, if used, must be temporary bounded diagnostics. Do not retain
complete page images, page text, document text, or tables. Evidence snippets
and notes remain capped at 300 characters per row.

## Readiness gates

Before running REVIEW2:

1. require a clean tracked worktree;
2. record hashes of the original input and REVIEW1 output files;
3. verify 150 unique calibration, text/table-detection, PDF-readiness, and
   source-review identities;
4. verify every eligible artifact path belongs to the same 150-row input;
5. run both legacy and refined review test suites;
6. stop if the renderer/parser is unavailable when visual confirmation is
   required.

## Review command

Use the project virtual environment and a new output directory:

```bash
.venv/bin/python scripts/review_text_table_calibration_subset.py \
  --input-csv docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv \
  --output-dir docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24 \
  --review-id TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24 \
  --review-mode refined_visual_gate_v1 \
  --candidate-page-window 1 \
  --max-pages-per-document 6 \
  --render-pages \
  --max-rendered-pages-per-document 3 \
  --navigation-page-budget 4 \
  --max-snippet-chars 300 \
  --require-visual-table-confirmation \
  --no-save-full-text
```

Run a dry-run first with the same arguments plus `--dry-run`. Stop if the
dry-run changes either original input or REVIEW1.

## Required REVIEW2 analysis

Report the refined distributions:

- wage-language and pay-numeric-language presence;
- visual table structure;
- confirmed wage/salary schedule;
- candidate-page relationship;
- contents/index/appendix navigation;
- confirmation method;
- extraction gate and bounded reasons;
- parser/render failures and page budgets.

Compare REVIEW2 with REVIEW1 row by row. Explicitly report:

- how many prior `yes` or `maybe` wage-table labels became prose, benefit,
  classification-only, non-wage, front-matter, or navigation cases;
- visual wage-table confirmation rate by original likely/possible/unlikely
  detector signal;
- wrong-page rate;
- hard/not-extractable or second-review share;
- p1 `pass_high_confidence` count;
- agreement on a random rendered-page QA challenge.

REVIEW2 remains assisted local adjudication unless an independent human
actually performs and records the decisions. Do not describe renderer
success or structural-feature agreement as human validation.

## Extraction decision

Make one explicit recommendation:

1. `500_doc_extraction_allowed` only if every refined rubric gate passes,
   including at least 80% likely-signal visual confirmation, no more than 15%
   wrong pages, at least 80% independent rendered-page QA agreement, and
   enough representative p1 high-confidence rows;
2. `smaller_extraction_pilot_only` if evidence supports a narrower,
   separately approved pilot but not 500 documents; or
3. `continue_schema_refinement` if the gates fail.

Until REVIEW2 is collected, independently challenged, and passes, the
500-document extraction prompt remains prohibited.
