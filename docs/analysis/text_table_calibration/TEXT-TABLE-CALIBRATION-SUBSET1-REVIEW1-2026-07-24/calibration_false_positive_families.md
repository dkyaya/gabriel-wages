# Calibration False-Positive Families

These are assisted bounded-review labels, not human-adjudicated final error codes.

- `benefit_table`: 10
- `classification_without_pay`: 2
- `index_or_contents`: 1
- `non_wage_schedule`: 4
- `not_applicable`: 112
- `numeric_appendix`: 1
- `other:bounded_signal_without_confirmed_table`: 18
- `percentage_prose`: 1
- `unknown`: 1

Common families guide classifier/schema refinement only. No wage values or page text are retained here.

## Visual QA correction

A five-row rendered-page challenge found material disagreement in every
checked case. In particular, wage-related prose/front matter had been assigned
specific table-layout labels, and a contents page referenced a later salary
table after an assisted `no_wage_table` outcome. These assisted family counts
therefore understate false-positive and bounded-page-miss risk and must not be
used as calibrated error rates.
