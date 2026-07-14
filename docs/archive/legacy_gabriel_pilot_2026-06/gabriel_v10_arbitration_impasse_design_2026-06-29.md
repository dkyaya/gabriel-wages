# GABRIEL v10 Design Memo: `arbitration_or_impasse_backstop`

**Date:** 2026-06-29

## 1. Purpose

This memo defines a possible GABRIEL v10 attribute called `arbitration_or_impasse_backstop`. It is a conceptual and implementation-readiness note only. It does not run GABRIEL, does not change scoring code, and does not add new data.

## 2. Why v10 is needed after v9

GABRIEL v9 established a real `comparability_emphasis` signal, but that signal is heavily concentrated in safety-side arbitration and award-style documents, especially the Somerville police awards. Ordinary CBAs and MOAs mostly scored low, while the strongest non-safety comparability evidence found so far is the Boston BTU bargaining page, which is mechanism-proxy rather than causal-corpus reasoning text.

That pattern creates an institutional-pathway question. The relevant mechanism may be not only explicit comparability language, but also bargaining conducted in the shadow of formal impasse-resolution institutions such as arbitration, factfinding, mediation, stipulated awards, and JLMC-style proceedings. A v10 attribute would test that possibility directly.

## 3. Proposed attribute name

`arbitration_or_impasse_backstop`

## 4. Attribute definition

`arbitration_or_impasse_backstop` measures whether a document indicates that wage-setting or contract settlement is shaped by formal impasse-resolution institutions, including arbitration, interest arbitration, factfinding, mediation, stipulated awards, JLMC proceedings, statutory criteria, or bargaining in the shadow of such procedures.

The attribute should not merely detect the word `arbitration` in boilerplate grievance language. It should focus on contract-formation or wage-setting context, not routine grievance arbitration clauses.

## 5. What counts as evidence

Evidence should count when the document discusses one or more of:

- interest arbitration;
- arbitration award;
- stipulated award;
- factfinding;
- mediation after bargaining impasse;
- impasse resolution;
- Joint Labor-Management Committee (`JLMC`);
- statutory criteria for resolving contract terms;
- panel or arbitrator reasoning about wages, ability to pay, internal comparison, external comparison, recruitment/retention, or cost of living;
- settlement reached after or under threat of impasse, arbitration, factfinding, or mediation;
- explicit references to bargaining deadlock, unresolved contract terms, or formal dispute-resolution pathways.

## 6. What does not count

Do not count:

- ordinary grievance-arbitration clauses in CBAs;
- boilerplate contract-administration procedures;
- disciplinary arbitration unrelated to wage setting;
- generic legal citations with no impasse or wage-setting context;
- union/employer disagreement without evidence of a formal impasse process;
- ordinary settlement language with no mediation, arbitration, factfinding, or JLMC signal.

## 7. Expected positive cases

Expected positive cases from the current corpus or adjacent reviewed materials include:

- Somerville police arbitration awards, where the arbitration panel explicitly reasons about wages, comparables, and statutory criteria.
- Wayland fire JLMC material, because it is a public-safety impasse-resolution document even if v9 comparability language was weak.
- Any factfinding or stipulated-award style document that resolves open wage terms or frames settlement through statutory criteria.
- Mechanism-proxy materials, if that corpus is later enabled, that explicitly describe settlement after mediation, bargaining deadlock, or bargaining under an impasse backstop.

## 8. Expected negative cases

Expected negative cases include:

- ordinary final CBAs that simply list wage schedules and term dates;
- MOAs that record settled outcomes without discussing impasse procedures;
- grievance procedure sections with routine arbitration language;
- salary schedules and compensation appendices without bargaining-pathway context;
- public bargaining updates that discuss wages but do not indicate any impasse-resolution mechanism.

## 9. Ambiguous cases and how to handle them

Ambiguous cases will matter here more than in v9 because the token `arbitration` appears in multiple institutional contexts.

Key ambiguity classes:

- **Grievance arbitration vs. interest arbitration.**
  Rule: count only if arbitration is tied to contract formation, wage setting, unresolved successor terms, impasse, or statutory wage-setting criteria.

- **Settlement after pressure vs. settlement under a formal backstop.**
  Rule: do not count generic settlement language unless the document links it to mediation, impasse, factfinding, JLMC, or arbitration.

- **JLMC or mediation references without wage substance.**
  Rule: moderate score at most unless the document connects the process to contract terms, wage movement, or open economic issues.

- **Mechanism-proxy documents that describe bargaining procedure but are not causal documents.**
  Rule: if later enabled, score them, but always preserve `source_corpus` and analyze separately from causal rows.

- **Legal/statutory references.**
  Rule: count only when the statute is invoked as part of resolving contract terms or wage issues, not as a background citation.

Use `ambiguity_flag` whenever the model finds process language but the contract-formation or wage-setting connection is weak.

## 10. Recommended prompt language for GABRIEL

Recommended prompt concept:

> Score `arbitration_or_impasse_backstop` from 0 to 100 based on whether this document indicates that wage-setting or successor-contract settlement is shaped by formal impasse-resolution institutions such as interest arbitration, arbitration awards, stipulated awards, factfinding, mediation after impasse, JLMC proceedings, or statutory wage-setting criteria. Focus on contract formation and economic-term resolution. Do not count ordinary grievance arbitration, disciplinary arbitration, or boilerplate dispute procedures unless the passage clearly ties them to unresolved contract terms or wage settlement. Provide short verbatim supporting excerpts only when they literally appear in the document.

Recommended scoring anchors:

- `0` = no evidence of impasse, arbitration, factfinding, mediation, or JLMC backstop in wage-setting or contract-formation context.
- `25` = generic or weak dispute-resolution signal, not clearly tied to wage setting.
- `50` = clear impasse, mediation, factfinding, or arbitration context, but weak connection to wage outcomes.
- `75` = formal impasse, arbitration, factfinding, or JLMC process clearly tied to contract terms or wage settlement.
- `100` = award, factfinding, or JLMC reasoning directly resolves or frames wage terms using statutory criteria, comparability, ability to pay, or related economic reasoning.

## 11. Recommended output fields

Recommended output fields:

- `obs_id`
- `arbitration_or_impasse_backstop_score`
- `rationale`
- `supporting_excerpts`
- `no_evidence_explanation`
- `source_type`
- `source_corpus`
- `occupation_class`
- `safety_flag`
- `quote_verification_status`
- `excerpts_failed`
- `excerpts_flagged_irrelevant`
- `ambiguity_flag`
- `boilerplate_grievance_arbitration_flag`

Suggested optional implementation fields if the runner later wants more diagnostics:

- `process_type_guess` with values like `interest_arbitration`, `factfinding`, `mediation`, `jlmc`, `stipulated_award`, `unclear`
- `economic_terms_link_flag`
- `statutory_criteria_flag`

## 12. Quote-verification requirements

Quote verification should match the v8/v9 discipline:

- supporting excerpts must be verbatim;
- failed or paraphrased excerpts must not count as support;
- grievance-arbitration boilerplate should be flagged as irrelevant when it is not tied to contract formation or wage settlement;
- award-outcome sentences can count only when they are part of process reasoning, not when they are isolated result statements with no institutional context;
- the model should be conservative when only generic legal or procedural language is available.

This attribute needs an especially strong irrelevance screen because the word `arbitration` is common in contexts that are not relevant to wage-setting backstops.

## 13. How to analyze v10 results

v10 should be analyzed separately by:

- `source_type`
- `source_corpus`
- `safety_flag`
- `occupation_class`
- `city`
- matched pair
- CBA-only subset
- arbitration/factfinding/award subset
- mechanism-proxy/discourse subset if that corpus is later enabled

Recommended analysis views:

- pooled distribution, with the same caveat structure used in v9;
- safety vs. non-safety within source-type subsets;
- matched-pair summaries by city and match tier;
- award-style vs. ordinary CBA contrasts;
- cross-tab with `comparability_emphasis` to see whether explicit comparator language and impasse-backstop language travel together or separately.

## 14. Risks and failure modes

Main risks:

- **False positives from grievance arbitration boilerplate.**
  This is the largest implementation risk.

- **Source-type confounding.**
  Award-style documents may score high simply because they expose reasoning, not because safety bargaining always has a stronger backstop.

- **Mechanism-proxy leakage.**
  If discourse or mechanism-proxy documents are later enabled, they may inflate the apparent prevalence of impasse-pathway language relative to the causal corpus.

- **Sparse non-safety reasoning documents.**
  The same problem seen in v9 may persist here.

- **Statutory-language overcounting.**
  A statute citation alone is weaker than actual use of statutory criteria in resolving economic terms.

- **Thin MOA problem.**
  Safety settlements may still resolve under an impasse shadow without recording that shadow in the final document.

## 15. Recommendation

Recommendation: **4. first hand-code a small gold set.**

Why:

- the false-positive risk from grievance arbitration is high enough that running all 32 causal rows immediately would likely produce noisy first-pass results;
- the corpus already contains a few high-value positive and negative exemplars that can anchor a gold set;
- a small hand-coded set will clarify prompt boundaries before any full-run decision;
- the project is already operating under a source-type caveat, so a rushed all-row run would risk turning that caveat into measurement error.

Suggested gold-set composition:

- Somerville police awards as clear positives;
- Wayland fire JLMC and any other award-style or impasse-pathway documents as process-positive tests;
- ordinary CBAs with grievance arbitration language as false-positive tests;
- one or two non-safety mechanism-proxy materials, if later allowed in a separate lane, as out-of-corpus comparison cases.

After the gold set:

1. refine prompt boundaries;
2. decide whether an all-32 causal run is justified;
3. only then consider a broader pilot or a full v10 run.

## Gold-set pointers

The first small hand-coded gold set for this attribute now lives at:

- `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`

Those files should be used before any v10 model pass to pressure-test the grievance-arbitration false-positive boundary.

## Gold dry-run note

The first bounded dry-run on the 11-row gold set lives at:

- `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- `docs/analysis/gabriel_v10_gold_dryrun_report_2026-06-29.md`
- `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv`

The candidate prompt passed the main grievance-arbitration boundary for Boston SENA, Seekonk DPW, and Seekonk teachers, and it kept Boston BTU low despite peer-wage comparison content. One formal failure occurred on Arlington DPW, but manual inspection found a separate duration/reopener clause referencing an impasse procedure with mediation/factfinding and money issues. Treat that row as a gold-set contamination or construct-boundary case before any all-32 causal pilot.

## Repaired gold-set retry note

The repaired gold set and one bounded retry live at:

- `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`
- `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`
- `docs/analysis/gabriel_v10_gold_repaired_dryrun_report_2026-06-30.md`
- `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv`

The repaired retry produced zero formal boundary failures. Clean grievance-only traps stayed low, clear positives stayed high, and Boston BTU stayed at zero. Arlington DPW 2015 and 2018 were recoded as ambiguous future-reopener/impasse edge cases and both scored `60`, which should be treated as a construct-boundary result rather than a grievance-arbitration prompt failure. A small all-32 causal pilot is now reasonable if those reopener/impasse cases are flagged and results remain stratified by `source_type` and ordinary-CBA versus award-style documents.
