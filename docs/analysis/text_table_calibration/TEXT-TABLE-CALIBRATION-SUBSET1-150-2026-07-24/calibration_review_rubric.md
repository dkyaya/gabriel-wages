# Calibration Review Rubric

## Review unit

One row represents one retained PDF and its frozen candidate-page hints.
Reviewers later open the local artifact, inspect the hinted pages and nearby
pages when necessary, and label the row. Preparation does not open PDFs.

## Required review order

1. Confirm the artifact identity corresponds to the municipality, unit, and
   source metadata. Do not revise durable metadata in this file.
2. Inspect each candidate wage page, plus an immediately adjacent page only
   when needed to understand a split table.
3. Determine whether a genuine wage/pay schedule is present.
4. Compare the bounded contract-period hint with the document.
5. Record layout, difficulty, false-positive family, recommended action, and
   confidence.

## Core labels

- `page_hint_precision_label=correct`: all or substantively all hinted pages
  identify the wage table.
- `partially_correct`: at least one hint is useful but one or more hints are
  irrelevant, incomplete, or adjacent.
- `incorrect`: hints do not identify a wage table.
- `wage_table_present_label=yes`: a structured wage/pay schedule is visible.
- `maybe`: compensation information exists but table identity or scope is
  ambiguous.
- `no`: no wage table is found under the bounded review protocol.
- `wage_table_page_match_label=exact`: hinted page contains the relevant
  table; `nearby`: table is immediately adjacent; `wrong_page`: table exists
  elsewhere; `no_wage_table`: none is present.

## Contract-period labels

Use `correct` only when the bounded hint corresponds to the operative
agreement/contract period. Use `partially_correct` for a real but incomplete
or secondary date range, `incorrect` for unrelated dates, and
`no_period_found` when no period can be located under bounded review.

## False-positive families

Use short consistent labels such as `benefit_table`, `premium_or_allowance`,
`percentage_prose`, `classification_without_pay`, `numeric_appendix`,
`index_or_contents`, `date_table`, `non_wage_schedule`, or `other:<short>`.
Do not paste full text.

## Extraction boundary

Do not transcribe full tables or final wage values during calibration. Record
only structural labels and short notes necessary to design a later extraction
schema. Mark ambiguous cases `needs_second_review`.
