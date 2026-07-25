# Post-REVIEW2 extraction decision

Date: 2026-07-24
Decision: **`continue_schema_refinement`**

## Rationale

The refined visual/table gate completed all 150 rows but failed every
authorization threshold that bears on current extraction:

- strict likely-signal table confirmation was 76.25%, below 80%;
- wrong-page rate was 31.82%, above 15%;
- independent rendered-page agreement was 55.56%, below 80%;
- the challenge exposed unresolved wage-prose, budget/benefit,
  compact-schedule, and contents-navigation errors.

The 74 assisted `pass_high_confidence` rows and 61 p1 high-confidence rows
cannot be projected into a 500-document design while the independent check
disagrees this often.

## Allowed next scale

No wage-table extraction scale is authorized—not 500 documents and not a
smaller pilot. The next bounded work should be calibration refinement only:

1. obtain independent human judgments for a balanced rendered-page subset;
2. revise candidate-page navigation so contents/appendix references can
   reach their named target page within a small explicit budget;
3. require visible repeated employee/classification rows and pay-period/rate
   columns for a high-confidence schedule;
4. distinguish aggregate fiscal, benefit, incentive-prose, and
   classification-only material;
5. add an explicit compact compensation-sheet category for schedule-like
   lists that are usable but not conventional tables;
6. run another blinded rendered-page challenge and require at least 80%
   agreement before reconsidering extraction.

## Prohibitions retained

The existing 500-document extraction prompt remains unexecuted and
unauthorized. OCR, ingestion, codification, final wage extraction, wage-gap
analysis, and regression work remain out of scope.
