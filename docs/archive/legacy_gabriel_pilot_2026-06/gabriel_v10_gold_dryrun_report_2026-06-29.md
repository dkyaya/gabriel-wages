# GABRIEL v10 Gold Dry-Run Report

**Date:** 2026-06-29  
**Attribute:** `arbitration_or_impasse_backstop`  
**Prompt version:** `v10_gold_dryrun_2026-06-29_candidate`

## 1. Purpose

This dry-run tested the candidate v10 prompt on the 11-row hand-coded gold set only. It was not a full v10 run and did not score all 32 causal rows. The main boundary test was whether ordinary grievance-arbitration boilerplate stays near zero while true interest-arbitration, JLMC, and stipulated-award cases score high.

## 2. Prompt Version Used

The script used the candidate prompt in `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py`, including the required instruction:

> Score `arbitration_or_impasse_backstop` from 0 to 100 based on whether this document indicates that wage-setting or successor-contract settlement is shaped by formal impasse-resolution institutions such as interest arbitration, arbitration awards, stipulated awards, factfinding, mediation after impasse, JLMC proceedings, or statutory wage-setting criteria.

The prompt also explicitly excludes ordinary grievance arbitration, disciplinary arbitration, boilerplate dispute procedures, and peer-wage comparison alone.

## 3. Gold-Set Composition

- Total rows: 11
- Clear positives: 3
- Clear negatives: 4
- False-positive traps: 4
- Mechanism-proxy rows: 1
- Ambiguous rows: 0

Input file: `analysis/gabriel_pilot/input_v10_gold_2026-06-29.csv`

## 4. Results Summary

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | 96, 96, 88 | 93.3 | 88 | 96 |
| `clear_negative` | 4 | 0, 10, 0, 0 | 2.5 | 0 | 10 |
| `false_positive_trap` | 4 | 20, 70, 10, 15 | 28.8 | 10 | 70 |

The Boston BTU mechanism-proxy negative scored `0`, so the prompt did not treat peer-wage comparison alone as v10 evidence.

## 5. Pass/Fail Against Boundary Tests

Formal audit result: **10 of 11 boundary tests passed.**

Passed:

- All clear positives scored at or above `51`.
- All clear negatives scored at or below `25`.
- Boston BTU scored `0`.
- Three of four false-positive traps scored at or below `25`.
- Ordinary grievance-arbitration boilerplate in Boston SENA, Seekonk DPW, and Seekonk teachers stayed low.

Failed:

- `gold_008` / `ma_arlington_public_works_2018` scored `70`, above the false-positive-trap threshold of `25`.

Manual inspection changes the interpretation of that failure. The Arlington full text contains an Article XXX duration/reopener clause stating that if agreement cannot be reached, either party may use an “impasse procedure (mediation and fact-finding)” under Chapter 1078, and either party may present “money issues” to Town Meeting. That is not ordinary grievance-arbitration boilerplate. It appears to be a gold-set contamination or construct-boundary case.

## 6. False Positives

Formal false positive:

- `ma_arlington_public_works_2018`: score `70`, expected `1_25`.

Interpretation:

- This is not a grievance-arbitration false positive.
- The model identified actual reopener/impasse language in the full CBA text.
- The original gold label was based on the grievance-arbitration locator, but the full document contains additional impasse/factfinding language.

## 7. False Negatives

No clear positive scored below `51`.

Scores:

- `ma_somerville_police_spsoa_2012`: `96`
- `ma_somerville_police_spea_2012`: `96`
- `ma_wayland_fire_jlmc_2020`: `88`

## 8. Quote-Verification Issues

Quote verification did its main job: no paraphrased excerpt was allowed to count as support. The quote audit is conservative, though:

- Positive rows had verified excerpts plus several verified-but-irrelevant flagged excerpts.
- `ma_wayland_fire_jlmc_2020` scored high, but only the short phrase `STIPULATED AWARD` survived the local relevance screen as supporting evidence; the rule screen should be improved before any broader pilot.
- `ma_arlington_public_works_2018` scored high but had no supporting excerpts retained after relevance filtering, which reinforces the need to resolve the Arlington boundary before using the prompt more broadly.
- `ma_boston_clerical_admin_2023` had one excerpt fail verbatim verification after retry.

## 9. Recommended Prompt Changes

Do not revise the grievance-arbitration exclusion based on this first run. The prompt correctly kept ordinary grievance-only examples low.

Resolve this construct boundary before a broader pilot:

- If generic future reopener clauses with mediation/factfinding and “money issues” are intended to count, recode Arlington as an ambiguous or weak-positive case rather than a false-positive trap.
- If v10 should count only invoked backstops that actually resolved current successor-contract terms, add a prompt rule: future reopening or duration clauses that merely preserve an option to use mediation/factfinding should score no higher than `25` unless the document shows the process was invoked or shaped the wage settlement.

Also improve the local relevance filter so JLMC/stipulated-award excerpts and impasse/reopener excerpts are not over-filtered when they are the model’s real evidence.

No retry was run. The single failure was not the stated failure mode of grievance boilerplate being over-scored, so a prompt retry would mostly retest a contaminated gold row.

## 10. Recommendation

Recommendation: **needs more gold rows** before an all-32 causal pilot.

The candidate prompt is promising on the main grievance-boilerplate boundary, but the gold set needs repair. Replace or recode the Arlington row, add at least one clean grievance-only DPW trap, and add one or two explicit future-reopener/impasse-procedure edge cases. After that, run one bounded retry on the revised gold set before considering the all-32 causal pilot.

## Output Files

- Results: `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv`
- Audit: `analysis/gabriel_pilot/results_v10_gold_dryrun_audit_2026-06-29.csv`
- Runner: `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py`
