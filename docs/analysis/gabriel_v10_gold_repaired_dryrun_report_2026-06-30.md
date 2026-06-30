# GABRIEL v10 Repaired Gold Dry-Run Report

**Date:** 2026-06-30  
**Attribute:** `arbitration_or_impasse_backstop`  
**Prompt version:** `v10_gold_repaired_dryrun_2026-06-30_candidate`

## 1. Purpose

This report evaluates one bounded retry of the v10 prompt on the repaired gold set. It does not run v10 on all 32 causal rows and does not create production measures.

The repaired set resolves the Arlington DPW issue from the first dry-run by moving Arlington from a grievance-arbitration false-positive trap to an ambiguous future-reopener/impasse edge case.

## 2. Repaired Gold-Set Composition

- Total rows: 12
- Clear positives: 3
- Clear negatives: 3
- False-positive traps: 4
- Ambiguous / future-reopener edge cases: 2
- Mechanism-proxy rows: 1

Files:

- Repaired gold set: `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`
- Repair memo: `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`
- Input: `analysis/gabriel_pilot/input_v10_gold_repaired_2026-06-30.csv`
- Results: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv`
- Audit: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_audit_2026-06-30.csv`

## 3. Score Summary By Gold Label

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | 100, 92, 78 | 90.0 | 78 | 100 |
| `clear_negative` | 3 | 10, 0, 0 | 3.3 | 0 | 10 |
| `false_positive_trap` | 4 | 5, 15, 10, 5 | 8.8 | 5 | 15 |
| `ambiguous` | 2 | 60, 60 | 60.0 | 60 | 60 |

Formal audit result: **0 boundary failures**.

## 4. Clear Positives Result

All clear positives stayed at or above `51`.

- `ma_somerville_police_spsoa_2012`: `100`
- `ma_somerville_police_spea_2012`: `92`
- `ma_wayland_fire_jlmc_2020`: `78`

The prompt continues to recognize interest-arbitration, JLMC, and stipulated-award evidence as high-signal v10 positives.

## 5. Clear Negatives Result

All clear negatives stayed at or below `25`.

- `ma_wayland_library_2020`: `10`
- `ma_worcester_fire_2017`: `0`
- `boston_bps_btu_negotiations_page`: `0`

The Wayland library score reflects grievance-arbitration text but remains low and within the allowed negative boundary.

## 6. False-Positive Trap Result

All false-positive traps stayed at or below `25`.

- `ma_wayland_public_works_2020`: `5`
- `ma_boston_clerical_admin_2023`: `15`
- `ma_seekonk_public_works_2023`: `10`
- `ma_seekonk_teacher_2021`: `5`

This is the main prompt-stability result: clean grievance-only arbitration did not trigger high v10 scores.

## 7. Ambiguous / Reopener Edge-Case Result

Both Arlington future-reopener edge cases scored `60`.

- `ma_arlington_public_works_2018`: `60`
- `ma_arlington_public_works_2015`: `60`

This is higher than the repaired expected band of `26_50`, but it is not a true prompt failure under the retry policy. The model correctly distinguished the Arlington clauses from ordinary grievance arbitration and explained that the clauses provide mediation/factfinding as an impasse-resolution backstop tied to money issues, while not directly awarding wage terms.

Interpretation: Arlington-style future reopener clauses appear to produce upper-middle scores. That is a construct-boundary decision for the research design, not evidence that the grievance-arbitration exclusion failed.

## 8. Boston BTU Mechanism-Proxy Result

Boston BTU scored `0`.

The prompt did not treat peer-wage comparison alone as evidence of `arbitration_or_impasse_backstop`. This boundary remains stable.

## 9. Grievance-Only Trap Boundary

Clean grievance-only traps stayed at or below `25`: **yes**.

The strongest repaired test is `ma_wayland_public_works_2020`, newly coded as a DPW grievance-only trap. It scored `5`.

## 10. Clear Positive Boundary

Clear positives stayed at or above `51`: **yes**.

The lowest clear positive was the Wayland fire JLMC stipulated award at `78`.

## 11. Future-Reopener / Impasse Edge-Case Boundary

Future-reopener edge cases landed in a plausible middle-to-upper-middle range: **yes, with a caveat**.

The two Arlington rows scored `60`, which is above the repaired expected `26_50` band but below the clean award/JLMC positives. The model’s rationale was coherent: it identified mediation/factfinding and money issues but also noted that the text does not show the process directly awarding or dictating wage terms.

If the PI wants v10 to count only invoked backstops, add a stricter prompt rule before an all-32 run. If future reopener/impasse options should count as institutional backstop evidence, the prompt is behaving consistently.

## 12. Recommendation

Recommendation: **small all-32 causal pilot is now reasonable**, with two constraints:

1. preserve `source_type`, `source_corpus`, and ordinary-CBA versus award-style stratification;
2. add an interpretive flag or review note for future reopener/impasse clauses, because they may score in the `51_75` range even when no award/factfinding actually resolved current wages.

No prompt revision is recommended from this repaired retry. The true failure criteria did not occur:

- no clean grievance-only trap scored above `25`;
- Boston BTU did not score above `25`;
- no clear positive scored below `51`;
- no clear negative scored above `25`.
