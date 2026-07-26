# Claim-oriented attribute codebook v1

`attribute_taxonomy_version = v1`. Definitions are fixed across batches; any change requires a new version and migration note.

## `automatic_raise_mechanism`

Raises occur automatically through COLA, CPI, steps, seniority, a schedule, or a contract formula.

- Positive examples: CPI-linked adjustment, annual step progression, formula-driven schedule increase.
- Exclusion: Do not mark present for a one-time discretionary increase without an automatic rule.
- Claim relevance: direct_text, documentary_mechanism, causal_candidate.

## `bargaining_power_signal`

Text shows bargaining, arbitration, settlement, memorandum, or negotiated leverage affecting pay.

- Positive examples: arbitration award sets compensation, negotiated memorandum changes pay.
- Exclusion: Do not infer bargaining power from the mere existence of a CBA.
- Claim relevance: documentary_mechanism, causal_candidate.

## `market_or_comparability_pressure`

Pay is justified by peer comparisons, market evidence, recruitment, retention, or competitiveness.

- Positive examples: peer-city comparison, recruitment difficulty, retention adjustment.
- Exclusion: Do not infer market pressure from a wage schedule alone.
- Claim relevance: documentary_mechanism, causal_candidate.

## `rank_or_specialization_premium`

Pay differs by rank, classification, certification, specialty, hazard, assignment, or role.

- Positive examples: rank differential, certification premium, special assignment rate.
- Exclusion: Do not mark present when titles differ but no compensation difference is stated.
- Claim relevance: direct_text, documentary_mechanism, causal_candidate.

## `implementation_or_retroactivity_advantage`

Text gives effective dates, retroactivity, staged increases, or implementation timing that may affect compensation.

- Positive examples: retroactive raise, staged effective dates, implementation schedule.
- Exclusion: Do not assign a directional advantage from a date alone without comparative support.
- Claim relevance: direct_text, documentary_mechanism, causal_candidate.

## `fiscal_constraint_signal`

Text cites affordability, budgets, funding, fiscal crisis, tax limits, or municipal finance constraints.

- Positive examples: budget limit, affordability finding, funding shortfall.
- Exclusion: Do not infer a fiscal constraint from government authorship alone.
- Claim relevance: documentary_mechanism, causal_candidate.

## `parity_or_internal_equity_signal`

Text invokes parity, compression, internal equity, or alignment with another employee group.

- Positive examples: parity adjustment, compression relief, internal equity alignment.
- Exclusion: Do not infer parity merely because two groups receive the same percentage increase.
- Claim relevance: documentary_mechanism, causal_candidate.

## `non_base_compensation_signal`

Text concerns overtime, stipends, longevity, certification, healthcare, pensions, leave, equipment, or other non-base compensation.

- Positive examples: longevity stipend, overtime provision, healthcare contribution.
- Exclusion: Do not treat non-base compensation as base-wage evidence.
- Claim relevance: direct_text, context_only.

## `base_wage_direct_value`

Text directly reports a base wage, rate, salary, step, grade, pay band, percentage raise, or effective date.

- Positive examples: 3 percent raise, $25.00 hourly rate, salary schedule effective July 1.
- Exclusion: Do not mark present for inferred, annualized, or coerced values lacking direct support.
- Claim relevance: direct_text.

## `safety_advantage_signal`

Text suggests a mechanism that may advantage police, fire, or public-safety compensation relative to non-safety compensation.

- Positive examples: safety-only premium, police comparability provision, fire-specific retention increase.
- Exclusion: Do not infer advantage from a safety occupation label without comparative mechanism language.
- Claim relevance: causal_candidate.

## `non_safety_constraint_signal`

Text suggests non-safety pay is constrained, standardized, delayed, weaker, or less differentiated.

- Positive examples: delayed implementation, standardized non-safety schedule, explicit constraint on adjustments.
- Exclusion: Do not infer constraint solely from a non-safety occupation label.
- Claim relevance: causal_candidate.

## `gap_narrowing_signal`

Text suggests parity, equity, compression relief, or shared raises that may narrow safety/non-safety differences.

- Positive examples: equity adjustment, compression correction, shared across-unit increase.
- Exclusion: Do not claim an actual narrowed gap without separately approved quantitative comparison.
- Claim relevance: documentary_mechanism, causal_candidate.

## `weak_or_no_claim_support`

Evidence is too weak for claim support in this phase and must carry a specific reason code.

- Positive examples: ambiguous direction, missing comparison, insufficient evidence.
- Exclusion: Do not use when another attribute is clearly supported by the supplied evidence.
- Claim relevance: not_claim_ready.
