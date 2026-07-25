# Gate 2 versus Gate 1 comparison

Gate 2 ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

Gate 1 ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

Both gates used the same 150 blinded calibration identities, the same local
PDF artifacts, the same six-page/four-navigation-page limit, and the same
1,500-character-per-page/6,000-character-per-case limits. Neither prompt
included REVIEW1, REVIEW2, or prior automated gate labels.

## Headline comparison

| Metric | Gate 1 | Gate 2 | Change |
| --- | ---: | ---: | ---: |
| Schema-valid GABRIEL responses | 150/150 (100%) | 150/150 (100%) | 0 pp |
| High-confidence ready | 12 | 9 | -3 |
| Ready with schema update | 16 | 13 | -3 |
| Total ready | 28 | 22 | -6 |
| Second review | 19 | 23 | +4 |
| Exclude for now | 103 | 105 | +2 |
| Original likely/p1 ready | 27/80 (33.75%) | 21/80 (26.25%) | -6 rows / -7.50 pp |
| Candidate-bearing wrong page | 9/132 (6.82%) | 2/132 (1.52%) | -7 / -5.30 pp |
| All-case no candidate | 71 | 105 | +34 |
| Exact page | 46 | 38 | -8 |
| Adjacent page | 9 | 2 | -7 |
| Later-table pointer | 5 | 2 | -3 |
| Unknown relationship | 10 | 1 | -9 |

Gate 2 improved precision in the narrow sense that `wrong_page` and
`unknown` became rare. It did not improve discovery recall: most former
wrong/unknown/adjacent outcomes became `no_candidate_page`, and the ready set
contracted.

## Gate-label transitions

- Of 12 Gate 1 high-confidence rows, 3 remained high confidence, 6 moved to
  schema-update-ready, and 3 moved to second review.
- Of 16 Gate 1 schema-update-ready rows, 4 moved to high confidence, 5
  remained schema-update-ready, and 7 moved to second review.
- Of 19 Gate 1 second-review rows, 2 became high confidence, 2 became
  schema-update-ready, 10 remained second review, and 5 were excluded.
- Of 103 Gate 1 excluded rows, 100 remained excluded and 3 moved to second
  review. None became extraction-ready.

For the original 80 likely/p1 rows specifically, Gate 2 produced 9 high
confidence, 12 schema-update-ready, 16 second-review, and 43 excluded rows.
The 53 Gate 1 likely/p1 non-ready rows did not supply the hoped-for reserve of
missed tables: 39 Gate 1 exclusions stayed excluded, one moved to second
review, three of the prior second-review rows became ready, four became
excluded, and six remained second review.

## Page relationships and navigation

Among the 132 rows with supplied candidate pages, Gate 2 relationships were
38 exact, 2 adjacent, 2 later-table pointers, 2 wrong, 87 no-candidate, and 1
unknown. Gate 1 had 46 exact, 9 adjacent, 5 later pointers, 9 wrong, 53
no-candidate, and 10 unknown for the same denominator.

The changed relationships show what happened:

- 9 Gate 1 wrong pages became no-candidate;
- 9 of 10 unknowns became no-candidate;
- 8 exact pages and 6 adjacent pages became no-candidate;
- 4 of 5 later-table pointers became no-candidate;
- 2 no-candidate rows became wrong-page.

Gate 2 found a nonzero printed/PDF page offset on 48 cases, but GABRIEL
confirmed only 2 later-table relationships. This is useful negative evidence:
offset inference is a diagnostic, not proof that a referenced wage table was
found.

## Wage schedules, table families, and compact sheets

GABRIEL wage-schedule presence changed from 37 yes / 12 maybe / 101 no to 36
yes / 7 maybe / 107 no. The dominant visual families remained prose or no
table: Gate 2 returned 65 `prose_only` and 30 `no_table` rows.

Gate 2 identified two compact compensation sheets rather than Gate 1's one.
Neither became ready: the existing compact case remained second review and a
Gate 1 classification-pay case changed to compact but moved from
schema-update-ready to second review. The deterministic
`compact_compensation_candidate` diagnostic appeared on 45 cases, far more
than the two model-confirmed compact sheets. It therefore remains a ranking
feature, not an authorization rule.

Non-wage control remained strict. No ready row had a GABRIEL negative
non-wage family. Gate 2 returned 105 `exclude_for_now` rows; negative types
and families remained categorically ineligible for high confidence.

## Representation

The ready set shrank from 28 to 22:

- unit types: Gate 1 was 16 non-safety / 7 fire / 5 police; Gate 2 is 10
  non-safety / 7 fire / 5 police;
- source types: Gate 1 covered 12 wage plans, 10 CBAs, 5 ordinances, and 1
  arbitration award; Gate 2 covers 11 wage plans, 7 CBAs, and 4 ordinances;
- Gate 2 therefore fails the documented representation rule because it has
  fewer than 30 total ready rows and loses arbitration-award representation.

## Runtime and request volume

Gate 2 evaluated 769 local pages versus 738 in Gate 1 and supplied 632,553
bounded text characters versus 585,644. It used 682 existing renders versus
734 because newly selected navigation/offset pages did not always have a
pre-existing rendered aid.

Gate 2 used 434,547 input tokens and 39,357 output tokens (473,904 total),
versus 382,480 input and 40,447 output tokens (422,927 total) in Gate 1. Wall
runtime fell from 493.799 seconds to 452.075 seconds despite the larger input.
Per-row elapsed values are not summed for comparison because the transport
records batch-relative elapsed time; wall-clock summary values are the
appropriate runtime measure.

## Interpretation

Gate 2 resolved Gate 1's loose `wrong_page`/`unknown` labeling, preserved
schema reliability and non-wage vetoes, and demonstrated that bounded printed
page offsets can be diagnosed. It did not find enough additional wage tables.
The result is stronger evidence that candidate discovery remains low recall
or that many upstream likely/p1 signals were prose/non-table false positives.
It does not authorize extraction at either scale.
