# Gate 3 compensation-evidence schema

Schema version: `gate3_compensation_evidence_v1`

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`

The ledger classifies bounded evidence by its best research use. It is not an
extracted wage or mechanism dataset.

## Identity fields

- `gate3_compensation_id`
- `adjudication_case_id`
- `calibration_id`
- `source_review_id`
- `pdf_readiness_id`
- `candidate_queue_row_id`
- `state`
- `municipality`
- `government_name`
- `unit_type`
- `candidate_source_type`
- `pdf_page_count`
- `content_artifact_path`
- `candidate_pages_evaluated`
- `nearby_pages_evaluated`
- `navigation_pages_evaluated`

## Evidence classification

`compensation_evidence_category`:

- `quant_table_ready`
- `quant_compact_ready`
- `quant_prose_ready`
- `qual_mechanism_ready`
- `mixed_quant_qual_ready`
- `reference_navigation_only`
- `non_wage_compensation`
- `not_compensation_relevant`
- `second_review_required`
- `error`

`quantitative_evidence_present` and
`qualitative_mechanism_evidence_present`: `yes`, `maybe`, `no`, `unknown`.

`quantitative_evidence_type`:

- `wage_table`
- `salary_schedule`
- `hourly_rate_schedule`
- `annual_salary_schedule`
- `rank_step_schedule`
- `grade_step_schedule`
- `pay_band`
- `percentage_increase_schedule`
- `compact_compensation_sheet`
- `ordinance_rate_listing`
- `prose_specific_rate`
- `prose_percentage_raise`
- `none`
- `unknown`

`qualitative_mechanism_type`:

- `collective_bargaining_agreement_terms`
- `memorandum_or_settlement_terms`
- `arbitration_or_factfinding_reasoning`
- `CPI_or_COLA_indexing`
- `comparability_or_market_study`
- `parity_or_internal_equity`
- `step_movement_or_seniority`
- `rank_or_classification_differentiation`
- `certification_or_education_incentive`
- `longevity_or_service_based_pay`
- `fiscal_constraint_or_budget_logic`
- `wage_reopener_or_future_negotiation`
- `implementation_or_effective_date_logic`
- `none`
- `unknown`

`non_wage_compensation_type`:

- `benefits`
- `overtime`
- `stipend`
- `longevity`
- `education_or_certification`
- `pension`
- `leave`
- `reimbursements`
- `healthcare_contributions`
- `uniform_or_equipment`
- `other`
- `not_applicable`
- `unknown`

`extractable_quant_fields` is a bounded list, serialized with `|` in CSV. Its
allowed values are `rate`, `salary`, `hourly_rate`, `annual_salary`,
`percentage_increase`, `effective_date`, `step`, `grade`, `rank`,
`classification`, `unit`, and `contract_period`. An empty list is allowed.

`extractable_qual_fields` is a bounded list, serialized with `|` in CSV. Its
allowed values are `mechanism`, `bargaining_logic`, `indexing_formula`,
`comparability_basis`, `parity_logic`, `step_progression_rule`,
`eligibility_rule`, `implementation_rule`, `fiscal_constraint`,
`reopener_clause`, and `differentiation_logic`. An empty list is allowed.

`candidate_page_relationship`: `exact_evidence_page`,
`adjacent_to_evidence`, `points_to_later_evidence`, `wrong_page`,
`no_candidate_page`, or `unknown`.

`evidence_strength`: `high`, `medium`, `low`, or `unknown`.

`extraction_path_recommendation`:

- `quantitative_extraction_ready`
- `qualitative_extraction_ready`
- `mixed_extraction_ready`
- `extraction_ready_with_schema_update`
- `reference_followup_needed`
- `second_review_required`
- `exclude_for_now`
- `error`

`gate3_confidence`: `high`, `medium`, `low`, or `unknown`.

`gate3_reason_codes` is one to eight uppercase codes, serialized with `|`.
`gate3_short_rationale` is at most 300 characters and may not reproduce wage
values or full mechanism passages.

## GABRIEL and vision metadata

- `gabriel_request_id`
- `gabriel_backend`
- `gabriel_model`
- `gabriel_status`
- `gabriel_schema_valid`
- `gabriel_input_page_count`
- `gabriel_input_text_chars`
- `gabriel_used_images`
- `gabriel_elapsed_seconds`
- `vision_evidence_used`
- `vision_legibility`: `clear`, `partial`, `illegible`, `not_applicable`,
  `unknown`
- `image_table_structure_observed`: `yes`, `maybe`, `no`, `not_applicable`,
  `unknown`
- `image_role_pay_alignment_observed`: `yes`, `maybe`, `no`,
  `not_applicable`, `unknown`

If vision preflight fails and text/layout succeeds, `gabriel_used_images` and
`vision_evidence_used` are false, and the three vision judgments are
`not_applicable` or `unknown`.

## Classification rules

A case can be useful without a wage table. Qualitative mechanism language is
retained when it explains compensation setting, adjustment, negotiation,
differentiation, eligibility, or implementation. Benefits, stipends,
overtime, longevity, and similar material are classified as non-base-wage
compensation rather than automatically irrelevant. Reference-only pages do
not inherit unseen evidence. All labels describe bounded evidence, not final
research observations.
