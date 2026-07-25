# Automated GABRIEL gate 1 versus REVIEW1 and REVIEW2

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

Method: `automated_local_visual_layout_plus_gabriel_bounded_page_adjudication`

## Scope and comparability

The comparison joins all 150 rows by `calibration_id`. The automated primary
prompt used only the blinded independent-adjudication input, bounded local
text/layout evidence, and local render-derived features. REVIEW1 and REVIEW2
labels were joined only after the final automated ledger was complete.

REVIEW1 was permissive: 112 rows were labeled wage-table-present and 76 were
recommended for the extraction pilot. REVIEW2 was stricter: its final gate
labels were 74 `pass_high_confidence`, 15 `pass_with_schema_update`, 29
`second_review_required`, and 32 `fail_exclude`. The automated gate is stricter
still: 12 `extraction_ready_high_confidence`, 16
`extraction_ready_with_schema_update`, 19 `second_review_required`, and 103
`exclude_for_now`.

## REVIEW2 extraction-gate transitions

| REVIEW2 label | Auto high confidence | Auto schema update | Auto second review | Auto exclude |
|---|---:|---:|---:|---:|
| `pass_high_confidence` | 12 | 13 | 14 | 35 |
| `pass_with_schema_update` | 0 | 2 | 1 | 12 |
| `second_review_required` | 0 | 0 | 1 | 28 |
| `fail_exclude` | 0 | 1 | 3 | 28 |

- REVIEW2 `pass_high_confidence` rows downgraded from the corresponding
  automated high-confidence label: **62 of 74**.
- REVIEW2 `fail_exclude` or `second_review_required` rows upgraded to an
  automated ready label: **1 of 61**.
- The one upgrade was `cal_4453630dbcea0b4cd5ed3aed`. REVIEW2 treated it as a
  benefit-table wrong page, while the bounded packet contained a pay-scale
  table with role rows and minimum/market/maximum pay columns. GABRIEL labeled
  it an annual salary schedule; strong local structure supported only
  `extraction_ready_with_schema_update`, not the high-confidence gate.

## Wage-schedule presence changes

| REVIEW2 confirmed label | Auto yes | Auto maybe | Auto no |
|---|---:|---:|---:|
| `yes` | 29 | 10 | 38 |
| `maybe` | 3 | 1 | 12 |
| `no` | 5 | 1 | 50 |
| `unknown` | 0 | 0 | 1 |

The major change is the downgrade of 48 REVIEW2 `yes` rows to automated
`maybe` or `no`. This reflects the stricter requirement that wage language
must coexist with usable role/classification rows and pay/rate/salary columns
or a supported compact-compensation structure.

The final automated presence counts are 37 `yes`, 12 `maybe`, and 101 `no`.

## Candidate-page relationship changes

Final automated relationship counts are:

- `exact_table_page`: 46
- `adjacent_to_table`: 9
- `points_to_later_table`: 5
- `wrong_page`: 9
- `no_candidate_page`: 71
- `unknown`: 10

Only 36 of REVIEW2's 84 `exact_table_page` rows remained exact. Of the rest,
26 became `no_candidate_page`, 8 became adjacent, 4 became bounded later-table
pointers, 5 became unknown, and 5 became wrong-page. Of REVIEW2's 42
wrong-page rows, the automated system classified 27 as no-candidate-page, 8
as exact, 1 as adjacent, 1 as a later-table pointer, 3 as unknown, and 2 as
wrong-page. This is a definition change as well as a disagreement: the
automated gate separates an absent usable candidate from a supplied but wrong
candidate.

For the 132 cases that actually carried a candidate page, the automated
wrong-page estimate is **9 / 132 = 6.82%**, below the 15% threshold.

## Calibration-priority results

The original packet contains 80 likely/p1 rows, 63 p2 rows, and 7 p3 rows.

- Likely/p1: 12 high-confidence ready, 15 schema-update ready, 13 second
  review, and 40 excluded. Ready with high/medium confidence is **27 / 80 =
  33.75%**, well below the required 80%.
- P2: 0 high-confidence ready, 1 schema-update ready, 6 second review, and 56
  excluded.
- P3: all 7 excluded.

Thus 12 original likely cases became
`extraction_ready_high_confidence`; only 1 p2 case became
`extraction_ready_with_schema_update`.

## False-positive families

The automated system reduced the extraction-positive non-wage families:

- REVIEW2 index/contents: 23 excluded.
- REVIEW2 non-wage schedules: 15 excluded and 1 second review.
- REVIEW2 classification-without-pay: 2 excluded and 1 second review.
- REVIEW2 benefit-table: 2 excluded, 1 second review, and the single
  evidence-supported pay-scale correction described above.
- REVIEW2 bounded-signal-without-confirmed-table: 8 excluded and 1 second
  review.

No final ready row has a GABRIEL negative non-wage family. The final GABRIEL
non-wage counts include 25 benefits, 3 budget/fiscal, 2
classification-without-pay, 14 index/contents, 4 front matter, 3
incentive/bonus prose, 8 memorandum-without-table, 18 other, and 73
not-applicable.

## Unresolved cases and conclusion

Nineteen cases remain `second_review_required`. Although schema-valid coverage
and wrong-page performance pass their thresholds, the ready set is too small
and not representative enough for scale. The automated gate therefore resolves
many prior false positives but does **not** validate REVIEW1 or REVIEW2 as a
safe extraction authorization. The computed decision remains
`continue_schema_refinement`.
