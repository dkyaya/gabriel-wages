# Automated visual + GABRIEL text/table adjudication schema

Date: 2026-07-24
Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

## Unit

One row is one blinded calibration PDF case. The primary GABRIEL prompt sees
only identity context, bounded page roles, capped page snippets, and local
feature summaries. It does not see REVIEW1/REVIEW2 labels or prior actions.

## Required identity and page fields

- `auto_adjudication_id`
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

## Required local evidence fields

- `local_text_signal_summary`
- `local_layout_signal_summary`
- `rendered_page_available`
- `rendered_page_count_used`
- `table_structure_feature_score`
- `wage_language_feature_score`
- `pay_numeric_feature_score`
- `navigation_feature_score`
- `non_wage_false_positive_feature_score`
- `compact_compensation_sheet_feature_score`

Scores are deterministic values from zero to one. Summaries contain bounded
counts/reason codes, not page text, table cells, or wage values.

## Required GABRIEL fields

- `gabriel_request_id`
- `gabriel_backend`
- `gabriel_model`
- `gabriel_status`
- `gabriel_schema_valid`
- `gabriel_wage_schedule_present`
- `gabriel_candidate_page_relationship`
- `gabriel_visual_table_type`
- `gabriel_non_wage_family`
- `gabriel_navigation_needed`
- `gabriel_navigation_target_found`
- `gabriel_extraction_complexity`
- `gabriel_extraction_recommendation`
- `gabriel_confidence`
- `gabriel_reason_codes`
- `gabriel_short_rationale`
- `gabriel_input_page_count`
- `gabriel_input_text_chars`
- `gabriel_elapsed_seconds`

Allowed values:

| Field | Allowed values |
|---|---|
| `gabriel_status` | `not_called`, `success`, `schema_invalid`, `request_failed`, `credential_unavailable`, `timeout` |
| `gabriel_schema_valid` | `true`, `false` |
| `gabriel_wage_schedule_present` | `yes`, `maybe`, `no`, `unknown` |
| `gabriel_candidate_page_relationship` | `exact_table_page`, `adjacent_to_table`, `points_to_later_table`, `wrong_page`, `no_candidate_page`, `unknown` |
| `gabriel_visual_table_type` | `step_grade`, `rank_step`, `classification_pay_table`, `hourly_schedule`, `annual_salary_schedule`, `compact_compensation_sheet`, `percent_increase_only`, `prose_only`, `benefits_table`, `budget_or_fiscal_table`, `classification_without_pay`, `index_or_contents`, `front_matter`, `non_wage_table`, `no_table`, `other`, `unknown` |
| `gabriel_non_wage_family` | `not_applicable`, `benefits`, `budget_or_fiscal`, `classification_without_pay`, `incentive_or_bonus_prose`, `index_or_contents`, `front_matter`, `non_wage_appendix`, `memorandum_without_table`, `other`, `unknown` |
| `gabriel_navigation_needed` | `yes`, `no`, `unknown` |
| `gabriel_navigation_target_found` | `yes`, `no`, `not_applicable`, `unknown` |
| `gabriel_extraction_complexity` | `easy`, `moderate`, `hard`, `not_extractable`, `unknown` |
| `gabriel_extraction_recommendation` | `extraction_ready`, `extraction_ready_with_schema_update`, `second_review_required`, `exclude_for_now`, `unknown` |
| `gabriel_confidence` | `high`, `medium`, `low`, `unknown` |

`gabriel_reason_codes` is a pipe-delimited serialization of a JSON list of
short codes. `gabriel_short_rationale` is at most 300 characters.

## Required final gate fields

| Field | Allowed values or meaning |
|---|---|
| `auto_gate_label` | `extraction_ready_high_confidence`, `extraction_ready_with_schema_update`, `second_review_required`, `exclude_for_now`, `gabriel_unavailable`, `error` |
| `auto_gate_confidence` | `high`, `medium`, `low`, `unknown` |
| `auto_gate_reason_codes` | Pipe-delimited short codes. |
| `auto_gate_rationale` | Bounded final explanation, at most 500 characters. |
| `auto_gate_passes_500_doc_criteria_candidate` | `true` or `false`. |

## Combination rules

GABRIEL is necessary for a live completed label but is never sufficient:

- `extraction_ready_high_confidence` requires schema-valid GABRIEL agreement,
  a confirmed positive table family, exact/adjacent/resolved-later page
  relationship, high or medium GABRIEL confidence, strong local wage/numeric/
  table evidence, render or geometry support, and no dominant non-wage family.
- Wage prose without local table structure cannot receive the high-confidence
  label.
- Benefits, budget/fiscal, classification-without-pay, front matter,
  contents-only, and non-wage tables cannot receive the high-confidence label.
- A contents/index pointer without a checked bounded target is
  `second_review_required`.
- A resolved navigation target may be
  `extraction_ready_with_schema_update`; it is high confidence only when the
  target itself has rendered or strong geometry evidence and every other
  positive rule passes.
- Missing/failed/schema-invalid GABRIEL calls fail closed as
  `gabriel_unavailable` or `error`.

These are calibration labels, not wage observations.
