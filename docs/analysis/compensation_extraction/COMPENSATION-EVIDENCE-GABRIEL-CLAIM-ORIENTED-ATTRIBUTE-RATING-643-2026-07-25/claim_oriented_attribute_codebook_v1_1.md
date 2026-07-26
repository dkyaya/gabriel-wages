# Claim-oriented compensation attribute codebook v1.1

This stable codebook rates one supplied exact span at a time. Ratings describe document wording; they do not estimate wage effects, wage gaps, or causality.

Version migration: v1.1 adds `strike_or_no_strike_constraint` and preserves all v1 attribute meanings.

## 1. `automatic_raise_mechanism`

Raises occur automatically through COLA, CPI, step, seniority, schedule, or contract formula.

Exclusion: Exclude a one-time discretionary increase without an automatic rule.

## 2. `bargaining_power_signal`

Text shows union bargaining, arbitration, settlement, memorandum, factfinding, or negotiated leverage affecting pay.

Exclusion: Do not infer bargaining power from the mere existence of a CBA.

## 3. `market_or_comparability_pressure`

Pay is justified by market comparison, peer municipalities, recruitment, retention, or competitiveness.

Exclusion: Do not infer market pressure from a wage schedule alone.

## 4. `rank_or_specialization_premium`

Pay differs by rank, certification, classification, specialty, hazard, assignment, or role.

Exclusion: Titles without stated compensation differentiation are insufficient.

## 5. `implementation_or_retroactivity_advantage`

Text gives favorable effective dates, retroactivity, staged increases, delayed or accelerated implementation, or other timing terms that may affect compensation.

Exclusion: Do not assign advantage from a date alone without comparative support.

## 6. `fiscal_constraint_signal`

Text cites budget limits, affordability, funding, fiscal crisis, tax limits, or municipal finance constraints.

Exclusion: Do not infer a fiscal constraint from government authorship alone.

## 7. `parity_or_internal_equity_signal`

Text uses parity, compression, internal equity, or alignment with other employees or units.

Exclusion: Equal percentages alone do not establish parity language.

## 8. `non_base_compensation_signal`

Text concerns overtime, stipend, longevity, certification, healthcare, pension, leave, equipment, reimbursement, or other non-base compensation.

Exclusion: Do not treat non-base compensation as base-wage evidence.

## 9. `base_wage_direct_value`

Text directly reports base wage, hourly rate, salary, step, grade, pay band, percentage raise, or effective date.

Exclusion: Do not infer, annualize, or coerce a value not directly stated.

## 10. `safety_advantage_signal`

Text suggests a mechanism that may advantage police, fire, or safety compensation relative to non-safety.

Exclusion: A safety occupation label without comparative mechanism language is insufficient.

## 11. `non_safety_constraint_signal`

Text suggests non-safety pay is constrained, standardized, delayed, weaker, or less differentiated.

Exclusion: A non-safety occupation label alone is insufficient.

## 12. `gap_narrowing_signal`

Text suggests parity, equity, compression relief, shared raises, or another mechanism that may narrow safety/non-safety differences.

Exclusion: Do not claim an actual narrowed gap without an approved quantitative comparison.

## 13. `strike_or_no_strike_constraint`

Text discusses strike rights, no-strike clauses, work stoppage restrictions, essential-service limits, strike or slowdown penalties, labor-peace clauses, or arbitration/factfinding substitutes for strike leverage.

Exclusion: Do not infer direction; use neutral_or_unclear unless the supplied text states direction.

## 14. `weak_or_no_claim_support`

Evidence is too weak for claim support in this phase and carries a specific reason code.

Exclusion: Do not use when another attribute is clearly supported by the exact span.

## Controlled rating fields

Every attribute receives `attribute_present`, `direction_of_pressure`, `evidence_strength`, `claim_relevance`, `reason_code`, `supporting_quote`, and `claim_boundary`.

For `strike_or_no_strike_constraint`, direction is never assumed; use `neutral_or_unclear` unless the supplied text states a directional mechanism.
