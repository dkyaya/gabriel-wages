# GABRIEL v10 Gold-Set Memo: `arbitration_or_impasse_backstop`

**Date:** 2026-06-29

## 1. Purpose

This memo creates a small hand-coded gold set for the proposed GABRIEL v10 attribute `arbitration_or_impasse_backstop`. It is a prompt-boundary and evaluation scaffold only. It does not run GABRIEL, does not change scoring code, and does not create a production dataset.

## 2. How rows were selected

Rows were selected from the current repo materials with three priorities:

1. include clear positive examples where wage-setting is visibly shaped by arbitration, JLMC, or award-style process;
2. include clean negatives where ordinary CBAs record wage terms without any visible impasse-resolution pathway;
3. include explicit false-positive traps where the word `arbitration` appears in grievance or disciplinary boilerplate but not in contract-formation or wage-setting context.

Where possible, selections rely on already structured corpus rows in `data/contracts.csv`. One optional Boston BTU row is included as a separate mechanism-proxy lane because it is useful for boundary testing but should not be folded into the causal gold set.

## 3. Gold-set composition summary

- Total rows: 11
- Clear positives: 3
- Clear negatives: 4
- False-positive traps: 4
- Ambiguous: 0
- Mechanism-proxy rows included: 1

This is not perfectly balanced across occupation classes, because the current corpus has far richer verified positive process evidence in safety-side arbitration and JLMC documents than in ordinary non-safety CBAs.

## 4. Clear positives

- `ma_somerville_police_spsoa_2012` is the strongest interest-arbitration positive. The verified award language explicitly says the panel considered statutory criteria including ability to pay, comparable-town wages and benefits, and cost of living.
- `ma_somerville_police_spea_2012` is a second strong positive from the same institutional lane. It is useful to confirm that the attribute is not row-specific to one award file.
- `ma_wayland_fire_jlmc_2020` is a clean JLMC/stipulated-award positive. It matters because it tests whether the attribute can recognize a formal impasse-resolution document even when the most visible text is settlement mechanics and wage modifications rather than explicit comparator reasoning.

## 5. Clear negatives

- `ma_wayland_public_works_2020`
- `ma_wayland_library_2020`
- `ma_worcester_fire_2017`
- `boston_bps_btu_negotiations_page` as a separate mechanism-proxy negative

These rows matter for two reasons. First, they keep the model from treating any wage table or successor agreement as impasse-backstop evidence. Second, the Worcester fire row is a useful safety-side negative, which helps keep the attribute from collapsing into a police/fire proxy.

## 6. False-positive traps

- `ma_boston_clerical_admin_2023` contains prominent grievance-arbitration text under Chapter 150E Section 8, but the clause is about dispute handling under the agreement rather than unresolved successor terms or wage-setting.
- `ma_arlington_public_works_2018` is a discipline/grievance arbitration trap tied to suspension, dismissal, removal, or termination.
- `ma_seekonk_public_works_2023` is the cleanest short anti-example because it states that final binding arbitration applies to grievances only.
- `ma_seekonk_teacher_2021` is a useful school-side trap because it has a full multi-level grievance ladder culminating in arbitration, which could fool a prompt that keys too heavily on the token `arbitration`.

These four rows are the main reason to build the gold set before any v10 model pass.

## 7. Ambiguous cases

No ambiguous rows were included in this first small set. That was deliberate. The current need is to sharpen the positive/negative boundary before adding cases where process language is partial, indirect, or hard to verify.

## 8. Optional mechanism-proxy cases

The Boston BTU bargaining page is included as one optional separate-lane case:

- `boston_bps_btu_negotiations_page`

It contains explicit peer-wage comparison content and is valuable for H1 interpretation, but it should score as a v10 negative unless later review finds a real impasse-resolution signal. Including it here tests whether the eventual prompt can separate comparator content from arbitration/impasse-backstop content.

## 9. How this gold set should be used to refine the v10 prompt

Use the gold set to pressure-test four prompt boundaries:

1. distinguish interest arbitration, JLMC, stipulated-award, and wage-reasoning award language from routine grievance arbitration;
2. require a contract-formation or wage-setting link rather than any mention of arbitration;
3. avoid treating safety occupation alone as a positive cue;
4. avoid treating wage-comparison language alone as a positive cue when no impasse pathway is present.

The false-positive traps should be reviewed first. If the prompt cannot reliably keep those rows at `0` or `1_25`, it is not ready for a broader run.

## 10. Recommended next step

Recommended next step: **prompt dry-run on the gold set, followed by manual review before any all-32 causal run.**

That sequence is the most defensible next move because:

- the positive examples are already strong enough to anchor the upper end of the scale;
- the trap rows expose the main failure mode directly;
- a premature full-corpus pass would risk converting source-type confounding into measurement noise.
