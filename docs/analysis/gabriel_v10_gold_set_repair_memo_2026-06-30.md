# GABRIEL v10 Gold-Set Repair Memo

**Date:** 2026-06-30  
**Attribute:** `arbitration_or_impasse_backstop`

## 1. Purpose

This memo repairs the first v10 gold set after the initial 11-row dry-run. The repair resolves the Arlington DPW construct-boundary issue, adds a second future-reopener edge case, and recodes one ordinary DPW CBA as a cleaner grievance-arbitration trap.

The repaired gold set is:

- `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`

## 2. What Happened In The First Dry-Run

The first dry-run scored 10 of 11 rows within the intended boundary rules:

- clear positives scored high: `96, 96, 88`;
- clear negatives scored low: `0, 10, 0, 0`;
- Boston BTU mechanism-proxy peer-wage comparison scored `0`;
- three of four grievance-arbitration traps stayed at or below `25`.

The only formal failure was `ma_arlington_public_works_2018`, which was coded as a `false_positive_trap` but scored `70`.

## 3. Why Arlington Was Not A Clean False-Positive Trap

Arlington DPW 2018 contains ordinary grievance/disciplinary arbitration language, but the full text also contains a separate Article XXX duration/reopener clause. That clause says the parties agree to re-open negotiations for the next effective period, and if agreement cannot be reached by a deadline, either party may use the impasse procedure, including mediation and factfinding, under Chapter 1078. It also says either party may present money issues to Town Meeting.

That is not ordinary grievance arbitration. It is contract-formation process language tied to future successor negotiations and money issues. The first dry-run failure therefore exposed a contaminated gold label rather than a clean prompt failure.

## 4. Final Construct Decision

Future reopener clauses with mediation/factfinding and money-issue language should not be treated as grievance-arbitration boilerplate.

They also should not automatically score as high as a JLMC award, interest-arbitration decision, or stipulated award unless the document shows that the formal process was invoked or that it actually shaped wage settlement.

Coding decision:

- `ma_arlington_public_works_2018` is recoded from `false_positive_trap` to `ambiguous`.
- Expected band: `26_50`.
- Evidence type: `mediation_impasse`.
- Economic terms link: `yes`, because the clause expressly references money issues.
- Interpretation: weak/moderate process signal, not a clean positive.

The same construct decision is applied to `ma_arlington_public_works_2015`, which has the same future reopener/impasse structure.

## 5. Repaired Gold-Set Composition

- Total rows: 12
- Clear positives: 3
- Clear negatives: 3
- False-positive traps: 4
- Ambiguous / reopener edge cases: 2
- Mechanism-proxy rows included: 1

Label composition:

- `clear_positive`: Somerville SPSOA, Somerville SPEA, Wayland fire JLMC.
- `clear_negative`: Wayland library, Worcester fire, Boston BTU mechanism-proxy.
- `false_positive_trap`: Wayland DPW, Boston SENA, Seekonk DPW, Seekonk teachers.
- `ambiguous`: Arlington DPW 2018, Arlington DPW 2015.

## 6. New Clean Grievance-Only Trap

`ma_wayland_public_works_2020` is recoded from `clear_negative` to `false_positive_trap`.

Reason: the full text contains an Article 30 grievance-and-arbitration procedure defining a grievance as a dispute over the interpretation, meaning, or application of the agreement. It is useful as a DPW/public-works grievance-only trap because the process is contract administration, not successor-contract impasse or wage settlement.

## 7. New Future-Reopener / Impasse Edge Case

`ma_arlington_public_works_2015` is added as a second future-reopener edge case.

Reason: it contains the same Article XXX structure as the 2018 Arlington DPW agreement: future negotiations, a deadline if agreement cannot be reached, possible use of mediation/factfinding, Chapter 1078, and presentation of money issues to Town Meeting. It tests whether the prompt places this evidence in a middle band rather than treating it as grievance boilerplate or as a full award-style positive.

## 8. How The Repaired Gold Set Should Be Used

Use the repaired set for one bounded retry only. The target behavior is:

- ordinary grievance arbitration stays at or below `25`;
- peer-wage comparison alone stays at or below `25`;
- clear interest-arbitration/JLMC positives stay at or above `51`;
- Arlington-style future reopener/impasse clauses land in a plausible middle range, ideally `26_50`, unless the model provides defensible reasoning for a slightly higher weak-positive score.

Do not use this repaired set to make causal claims or production measures.

## 9. Recommended Next Step After Retry

If clean grievance traps stay low, Boston BTU stays low, and clear positives stay high, the prompt is probably stable enough for a small all-32 causal pilot.

If the Arlington-style edge cases score high again, treat that as a construct decision rather than an automatic prompt failure. Decide whether v10 should count future reopener/impasse options as weak positives or require evidence that the backstop was actually invoked.
