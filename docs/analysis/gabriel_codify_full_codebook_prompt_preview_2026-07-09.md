# GABRIEL Codify Pilot Prompt Preview (script-generated)

Model: `gpt-5.4-nano` | Attributes: 19 | n_rounds=1 | max_categories_per_call=19 | max_words_per_call=1500

## Categories (full codebook)
```python
{
  "peer_comparator_wage_comparability": "Explicit use of peer cities, comparable communities, external labor markets, comparator jurisdictions, or comparable bargaining units to justify wage levels, wage increases, or wage schedules. Positive examples: 'comparable communities', 'peer cities', 'market comparison', 'competitive with surrounding municipalities'. Exclude internal equity only, or generic 'competitive wages' without an external comparator.",
  "interest_arbitration_or_formal_impasse_backstop": "Wage-setting or successor-contract settlement shaped by formal impasse institutions such as interest arbitration, statutory impasse arbitration, JLMC-type process, SERB conciliation, factfinding, mediation-to-award process, or bargaining in the shadow of formal impasse resolution. Positive examples: 'interest arbitration', 'conciliation award', 'factfinder recommendation', 'impasse procedures for unresolved successor agreement', 'binding arbitration for contract terms'. Exclude ordinary grievance arbitration, discipline arbitration, or contract-interpretation arbitration.",
  "grievance_or_contract_interpretation_arbitration": "Arbitration used for grievances, discipline, contract interpretation, enforcement, or disputes under an existing agreement. Positive examples: 'grievance arbitration', 'arbitrator shall interpret this agreement', 'disciplinary arbitration'. Exclude interest arbitration or impasse arbitration over successor wage terms unless clearly described.",
  "staffing_shortage_recruitment_retention": "Explicit concern about vacancies, recruitment, retention, hiring, turnover, staffing shortages, labor supply, attrition, or inability to fill positions. Positive examples: 'recruitment and retention', 'vacancies', 'hard to hire', 'staffing shortage'. Exclude routine staffing assignments without shortage/retention language.",
  "minimum_staffing_or_continuous_coverage": "Minimum staffing, required crew levels, continuous coverage, 24/7 service obligations, station coverage, mandatory coverage, or inability to defer service. Positive examples: 'minimum staffing', 'two employees on duty at all times', '24-hour coverage', 'shall maintain staffing'. Exclude ordinary work schedules without a coverage constraint.",
  "overtime_callback_holdover_mandatory_extra_work": "Overtime, callback, holdover, mandatory overtime, court time, extra duty, detail work, standby/on-call, shift extension, or premium compensation for extra work demands. Positive examples: 'callback pay', 'holdover', 'mandatory overtime', 'standby pay'. Exclude base wage schedules alone.",
  "classification_reclassification_or_grade_structure": "Wage setting through classification systems, grades, steps, job titles, reclassification, compensation studies, wage schedules, or grade appeals. Positive examples: 'classification plan', 'Grade 12', 'step schedule', 'reclassification', 'compensation study'. Exclude a one-off premium/differential without a classification structure.",
  "training_certification_credential_premiums": "Wage premiums, stipends, incentives, requirements, or career ladders linked to training, certifications, degrees, licenses, credentials, EMT/paramedic, EMD/E911, CDL, hoisting, water/wastewater, education, or specialist qualifications. Positive examples: 'certification pay', 'education incentive', 'paramedic premium', 'CDL stipend'. Exclude generic training obligations without wage implication unless clearly tied to job requirements.",
  "hazard_risk_stress_or_line_of_duty_rationale": "Explicit wage or benefit language tied to hazard, risk, injury, stress, line-of-duty harm, dangerous conditions, public-safety exposure, or physical/psychological burden. Positive examples: 'line of duty injury', 'hazardous duty', 'risk', 'stress', 'danger'. Exclude generic sick leave/injury leave without a risk rationale.",
  "premium_pay_differentials": "Shift differentials, assignment differentials, specialty pay, longevity, night/weekend pay, holiday premiums, bilingual pay, paramedic pay, detail rates, or other add-ons beyond base wage. Positive examples: 'shift differential', 'longevity', 'premium pay', 'special assignment pay'. Exclude base wage scales only.",
  "benefits_total_compensation_or_pension": "Health insurance, pension, retirement, deferred compensation, paid leave, total compensation, uniform allowance, equipment allowance, or other non-wage benefits that affect compensation. Positive examples: 'health insurance contribution', 'pension', 'uniform allowance', 'deferred compensation'. Exclude wage-only provisions.",
  "subcontracting_outsourcing_or_volunteer_substitution": "Contracting out, outsourcing, privatization, volunteer substitution, non-unit labor replacement, civilianization, or restrictions on replacing bargaining-unit work. Positive examples: 'contracting out', 'subcontracting', 'volunteers shall not replace', 'civilianization'. Exclude management rights clauses that do not mention substitution/outsourcing.",
  "management_rights_or_service_flexibility": "Management rights to assign, schedule, transfer, reorganize, determine staffing, set operations, change methods, deploy personnel, or maintain service flexibility. Positive examples: 'management retains the right to assign', 'determine staffing', 'transfer employees'. Exclude union rights or grievance provisions alone.",
  "no_strike_or_work_stoppage_constraint": "No-strike, no-slowdown, no-lockout, essential-service continuity, or statutory work-stoppage constraints. Positive examples: 'no strike', 'no slowdown', 'no work stoppage', 'no lockout'. Exclude generic discipline clauses.",
  "civil_service_or_statutory_employment_channel": "Civil-service provisions, statutory employment protections, meet-and-confer statutes, Chapter 174/142/146 references, Chapter 4117/SERB references, appointment/promotion rules, or statutory channels structuring bargaining/wage-setting. Positive examples: 'civil service', 'Chapter 174', 'Chapter 4117', 'meet and confer', 'SERB'. Exclude generic city authority without a statutory/legal channel.",
  "union_security_or_institutional_power": "Union recognition, dues/agency checkoff, exclusive representation, release time, union access, bulletin boards, labor-management committees, bargaining rights, or institutional supports for union power. Positive examples: 'exclusive bargaining representative', 'dues deduction', 'union leave', 'labor-management committee'. Exclude incidental mention of the union's name only.",
  "budget_capacity_or_fiscal_constraint": "Fiscal capacity, budget constraints, ability to pay, appropriations, tax limits, fiscal emergency, budgetary shortfall, or city financial condition used to shape wages. Positive examples: 'available funds', 'budget constraints', 'ability to pay', 'appropriation'. Exclude routine payroll administration.",
  "non_safety_wage_restraint_or_admin_channel": "Evidence that non-safety wages are routed through administrative pay plans, classification systems, consultation rather than bargaining, weaker impasse pathways, delayed studies, pay-grade adjustments, or limited wage channels. Positive examples: 'consultation policy', 'classification compensation plan', 'compensation study', 'not subject to collective bargaining', 'pay grade adjustment'. Exclude any non-safety clause unless it specifically shows wage-channel restraint/admin routing.",
  "other": "Relevant wage-mechanism evidence not captured above. Use sparingly and explain."
}
```

## additional_instructions
```text
You are coding short excerpts from public-sector labor agreements (collective
bargaining agreements, meet-and-confer agreements, or arbitration awards) for
the presence of specific wage-setting mechanisms. For EACH attribute below:

GLOBAL CODING RULES
- Use source text only.
- Do not infer causal effects.
- Do not infer institutional mechanisms from outside legal knowledge unless
  the source text explicitly references them.
- Do not mark interest_arbitration_or_formal_impasse_backstop present for
  ordinary grievance arbitration -- that belongs under
  grievance_or_contract_interpretation_arbitration instead.
- Do not mark peer_comparator_wage_comparability present for generic
  "competitive wages" unless a peer/external comparator is explicit.
- Use not_found when evidence is absent.
- Use unclear when the text is suggestive but not enough.
- Keep excerpts short. Avoid long copied passages.
- Preserve exact wording for excerpts -- copy verbatim, do not paraphrase.
- Attribute evidence to the source window only; this window is a compact
  reassembly of previously-identified passages from one bargaining document,
  not the full document -- do not assume missing context implies absence.

For EACH attribute, report:
1. evidence_status: "present", "not_found", or "unclear".
2. If present or unclear, a SHORT VERBATIM SPAN (under 40 words) copied
   EXACTLY from the excerpt text. Never invent or infer text not literally
   present in the excerpt.
3. excerpt_location if identifiable from the text (e.g. an article/section
   reference visible in the window).
4. confidence: "high", "medium", "low", or "not_applicable" (use
   not_applicable only when evidence_status is not_found).
5. A one-sentence caveat/note if the match is partial, fragmentary, or
   uncertain; otherwise leave it blank.

```

## Selected windows

### tx_houston_fire_2024 (tx_houston_fire_2024_full_w1)
- state/city/occupation_class: TX/Houston/fire
- source_file: corpus/tx_houston/tx_houston_hpffa_fire_arbitration_award_2026.pdf
- chars: 3363

### tx_houston_other_2024 (tx_houston_other_2024_full_w1)
- state/city/occupation_class: TX/Houston/other
- source_file: corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf
- chars: 5906

### tx_austin_nursehealth_2023 (tx_austin_nursehealth_2023_full_w1)
- state/city/occupation_class: TX/Austin/nurse_health
- source_file: corpus/tx_austin/tx_austin_aemsa_ems_meet_confer_2023_2027.pdf
- chars: 2649

### oh_columbus_fire_2023 (oh_columbus_fire_2023_full_w1)
- state/city/occupation_class: OH/Columbus/fire
- source_file: corpus/oh_columbus/oh_columbus_iaff67_fire_cba_2023_2026.pdf
- chars: 6674
