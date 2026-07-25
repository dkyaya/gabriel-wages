# Refined REVIEW2 versus REVIEW1 comparison

Date: 2026-07-24
Calibration: `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`
Prior review: `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
Refined review: `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`

## Comparison basis

The comparison joins the two reviewed CSVs by `calibration_id`. All 150
identities matched one-to-one. REVIEW1 and the original calibration input
were read only. REVIEW2 used the same original 150-row input and wrote to a
new directory.

REVIEW2 is a stricter but still assisted local adjudication. It is not
independent human ground truth. Its principal improvement is to separate
wage language, pay-number language, structural table evidence, wage-schedule
confirmation, page relationship, and extraction authorization.

## REVIEW1 wage-table labels under the refined structure gate

REVIEW1 labeled 134 rows `yes` or `maybe` for wage-table presence. REVIEW2
mapped those rows as follows:

| REVIEW2 visual structure | Rows |
|---|---:|
| `confirmed_table` | 77 |
| `possible_table` | 15 |
| `index_or_contents` | 22 |
| `benefits_table` | 4 |
| `classification_only` | 3 |
| `non_wage_table` | 6 |
| `prose_only` | 6 |
| `front_matter` | 1 |

Of those 134 REVIEW1 yes/maybe rows, REVIEW2 assigned 74
`pass_high_confidence`, 15 `pass_with_schema_update`, 27
`second_review_required`, and 18 `fail_exclude`. Thus the refined workflow
did demote many previously positive rows. The independent challenge below
shows that the assisted refined labels still remain too permissive.

## REVIEW1 page-hint labels under the refined relationship gate

Among the 132 rows that REVIEW1 called `correct` or `partially_correct`,
REVIEW2 assigned:

| REVIEW2 candidate-page relationship | Rows |
|---|---:|
| `exact_table_page` | 84 |
| `adjacent_to_table` | 3 |
| `points_to_later_table` | 3 |
| `wrong_page` | 42 |

The resulting wrong-page rate is 42/132, or **31.82%**, using candidate-bearing
rows as the denominator. This exceeds the 15% authorization ceiling.

## Extraction-action changes

Sixty-nine rows retained the same action and 81 changed action.

| REVIEW1 action → REVIEW2 action | Rows |
|---|---:|
| `include_in_wage_extraction_pilot` → same | 46 |
| `include_in_wage_extraction_pilot` → `include_after_schema_update` | 13 |
| `include_in_wage_extraction_pilot` → `manual_review_only` | 10 |
| `include_in_wage_extraction_pilot` → `exclude_for_now` | 7 |
| `include_after_schema_update` → `include_in_wage_extraction_pilot` | 24 |
| `include_after_schema_update` → `manual_review_only` | 9 |
| `include_after_schema_update` → `exclude_for_now` | 3 |
| `manual_review_only` → `include_in_wage_extraction_pilot` | 4 |
| `manual_review_only` → `include_after_schema_update` | 2 |
| `manual_review_only` → same | 9 |
| `manual_review_only` → `exclude_for_now` | 8 |
| `exclude_for_now` → same | 14 |
| `exclude_for_now` → `manual_review_only` | 1 |

The 30 promotions into an extraction-oriented action demonstrate why this
comparison cannot itself establish precision: REVIEW2 is still an assisted
rule system, and the independent challenge disagreed with several promoted
or retained positives.

## Priority and original-signal results

| Priority | `pass_high_confidence` | `pass_with_schema_update` | `second_review_required` | `fail_exclude` |
|---|---:|---:|---:|---:|
| p1 | 61 | 7 | 8 | 4 |
| p2 | 13 | 8 | 19 | 23 |
| p3 | 0 | 0 | 2 | 5 |

| Original wage-table signal | Confirmed `yes` | `maybe` | `no` | `unknown` | Strict yes rate |
|---|---:|---:|---:|---:|---:|
| likely | 61 | 7 | 12 | 0 | 76.25% |
| possible | 16 | 9 | 33 | 0 | 27.59% |
| unlikely | 0 | 0 | 11 | 1 | 0.00% |

The likely group reaches 85.00% only if `maybe` is counted as confirmed. The
authorization rule calls for visual wage-table confirmation, so the strict
`yes` rate of 76.25% is the operative measure.

## Conclusion

REVIEW2 reduced some obvious false positives and made wrong-page,
contents/index, benefits, and non-wage cases visible. It did not establish an
independent precision estimate. The 31.82% wrong-page rate, sub-80% strict
likely confirmation rate, and failed blinded rendered-page challenge mean
the extraction gate remains closed.
