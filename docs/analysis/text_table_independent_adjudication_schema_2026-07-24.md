# Independent human text/table adjudication schema

Date: 2026-07-24
Packet ID: `TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`

## Purpose

One row is one calibration PDF case. The human-facing CSV preserves identity
and bounded page references while hiding all REVIEW1/REVIEW2 judgments,
detector signals, extraction gates, prior recommended actions, snippets, and
structured wage values.

## Blinded identity and page fields

| Field | Meaning |
|---|---|
| `adjudication_case_id` | Deterministic blinded packet identity derived from packet ID plus calibration ID. |
| `calibration_id` | Original immutable calibration identity. |
| `source_review_id` | Durable source-review identity. |
| `pdf_readiness_id` | Durable PDF-readiness identity. |
| `candidate_queue_row_id` | Candidate-queue identity. |
| `state` | State abbreviation. |
| `municipality` | Municipality label. |
| `government_name` | Government/employer label carried from the calibration input. |
| `unit_type` | Police, fire, or non-safety source-review unit group. |
| `candidate_source_type` | Candidate document/source family. |
| `pdf_page_count` | Existing readiness page count. |
| `blinded_candidate_pages` | Original bounded candidate page hints, without the detector label that produced them. |
| `blinded_nearby_pages` | In-range pages within the configured candidate-page window, excluding candidate pages. |
| `blinded_navigation_pages` | Deterministically selected front/end navigation context within the configured budget, excluding candidate and nearby pages. |
| `content_artifact_path` | Pointer to the retained local PDF; it is not a URL. |

## Human-review fields and allowed values

`human_reviewer` is free text. `human_reviewed_at` should be ISO 8601.
`human_notes` is a short free-text diagnostic that must not reproduce a full
table or a set of wage values.

| Field | Allowed values |
|---|---|
| `human_review_status` | `not_reviewed`, `reviewed`, `needs_second_review`, `exclude_from_adjudication` |
| `human_wage_schedule_present` | `yes`, `maybe`, `no`, `unknown` |
| `human_candidate_page_relationship` | `exact_table_page`, `adjacent_to_table`, `points_to_later_table`, `wrong_page`, `no_candidate_page`, `unknown` |
| `human_visual_table_type` | `step_grade`, `rank_step`, `classification_pay_table`, `hourly_schedule`, `annual_salary_schedule`, `compact_compensation_sheet`, `percent_increase_only`, `prose_only`, `benefits_table`, `budget_or_fiscal_table`, `classification_without_pay`, `index_or_contents`, `front_matter`, `non_wage_table`, `no_table`, `other`, `unknown` |
| `human_non_wage_family` | `not_applicable`, `benefits`, `budget_or_fiscal`, `classification_without_pay`, `incentive_or_bonus_prose`, `index_or_contents`, `front_matter`, `non_wage_appendix`, `memorandum_without_table`, `other`, `unknown` |
| `human_navigation_needed` | `yes`, `no`, `unknown` |
| `human_navigation_target_found` | `yes`, `no`, `not_applicable`, `unknown` |
| `human_extraction_complexity` | `easy`, `moderate`, `hard`, `not_extractable`, `unknown` |
| `human_extraction_recommendation` | `extraction_ready`, `extraction_ready_with_schema_update`, `second_review_required`, `exclude_for_now`, `unknown` |
| `human_confidence` | `high`, `medium`, `low`, `unknown` |

Before review, `human_review_status` is `not_reviewed`; the categorical
judgment fields are `unknown`; reviewer, timestamp, and notes are blank.

## Fields deliberately forbidden from the human-facing file

The packet must not carry `wage_table_signal`, any REVIEW1/REVIEW2 label,
`extraction_gate_label`, `wage_schedule_table_confirmed_label`,
`candidate_page_relationship_label`, prior `recommended_extraction_action`,
prior reviewer identity/notes, detector snippets, complete page/document text,
complete tables, or structured wage values.

## Output interpretation

Human fields are calibration judgments, not wage observations. A completed
row may inform a later authorization decision, but it cannot itself authorize
extraction until the aggregate gates and systematic-error review are applied.
