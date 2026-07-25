# Calibration Extraction Layout Notes

## Layout counts

- `annual_salary_schedule`: 15
- `appendix_table`: 1
- `hourly_schedule`: 8
- `no_wage_table`: 15
- `prose_only`: 5
- `rank_step`: 40
- `step_grade`: 65
- `unknown`: 1

## Complexity counts

- `easy`: 11
- `hard`: 59
- `moderate`: 65
- `not_extractable`: 15

A later extraction schema should preserve effective dates, rate basis, unit/rank/classification labels, step/grade headers, and continuation-page relationships. These notes authorize no extraction run.

The counts above are assisted text-rule labels, not visually confirmed table
layouts. A rendered challenge of step-grade, rank-step, annual-salary,
hourly, and no-table cases materially disagreed with all five outcomes.
Detector/review-schema refinement must require actual structural or visual
table evidence before these layout categories can schedule extraction.
