# Text/Table Manual Calibration Schema

## Purpose and stage boundary

This schema supports later human or adjudicated review of a fixed calibration
packet. It separates:

1. frozen heuristic detection signals;
2. manual calibration judgments;
3. possible extraction-pilot scheduling;
4. final extracted wage observations, which are not created here.

The preparation task initializes every review row as unreviewed. It does not
open PDFs or make substantive judgments.

## Identity and inherited detection fields

| Field | Meaning |
|---|---|
| `calibration_id` | Deterministic row-level calibration identity, derived from the calibration round and `text_table_detection_id`. |
| `calibration_round_id` | Packet ID: `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`. |
| `text_table_detection_id` | Durable detection-row identity. |
| `pdf_readiness_id` | Durable PDF-readiness identity. |
| `source_review_id` | Durable source-review identity. |
| `candidate_queue_row_id` | Original candidate identity. |
| `state` | State abbreviation inherited from detection. |
| `municipality` | Municipality inherited from detection. |
| `government_name` | Government/employer label inherited from detection. |
| `unit_type` | Police, fire, or non-safety unit type. |
| `candidate_source_type` | Candidate document/source type. |
| `priority_for_content_review` | Upstream p1/p2 content-review priority. |
| `source_officialness_rating` | Preliminary source-review officialness signal. |
| `source_relevance_rating` | Preliminary source-review relevance signal. |
| `document_type_rating` | Preliminary source-review document-type signal. |
| `pdf_page_count` | Durable technical page count. |
| `content_artifact_path` | Pointer to the already-retained local PDF; the planner does not open it. |
| `wage_table_signal` | Frozen heuristic wage-table signal. |
| `contract_period_signal` | Frozen heuristic contract-period signal. |
| `table_like_structure_signal` | Frozen heuristic table-structure signal. |
| `candidate_wage_pages` | Comma-separated 1-indexed page hints; not wage observations. |
| `candidate_wage_page_count` | Count of candidate page hints. |
| `candidate_contract_period_text` | Existing bounded, redacted detection hint; no new text is extracted. |
| `detection_notes` | Frozen detector note. |

The packet also preserves calibration-relevant provenance such as
`source_review_pilot_id`, `page_count_bin`, `text_layer_status`,
`wage_table_signal_confidence`, `contract_period_confidence`,
`extraction_pilot_priority`, `recommended_next_action`, and
`table_detection_method`.

## Manual-review fields

| Field | Initial value | Purpose |
|---|---|---|
| `reviewer` | blank | Reviewer identity or initials. |
| `reviewed_at` | blank | ISO timestamp or date of completed review. |
| `calibration_status` | `not_reviewed` | Workflow status. |
| `page_hint_precision_label` | `unknown` | Whether candidate wage pages are correct. |
| `wage_table_present_label` | `unknown` | Whether a wage table appears in the document. |
| `wage_table_page_match_label` | `unknown` | Exact/nearby/wrong-page relationship. |
| `contract_period_present_label` | `unknown` | Whether a contract period is present. |
| `contract_period_hint_match_label` | `unknown` | Whether the bounded hint matches. |
| `table_layout_type` | `unknown` | Dominant wage-table layout. |
| `extraction_complexity_label` | `unknown` | Expected extraction difficulty. |
| `false_positive_family` | `unknown` | Short controlled/free-text family label developed during calibration. |
| `extraction_schema_notes` | blank | Bounded notes about needed fields or rules. |
| `recommended_extraction_action` | `unknown` | Post-review scheduling judgment. |
| `reviewer_confidence` | `unknown` | Reviewer confidence label; rubric recommends high/medium/low/unknown. |
| `reviewer_notes` | blank | Short review note; no complete page/document text. |

## Allowed values

### `calibration_status`

- `not_reviewed`
- `reviewed`
- `needs_second_review`
- `exclude_from_calibration`

### `page_hint_precision_label`

- `correct`
- `partially_correct`
- `incorrect`
- `not_applicable`
- `unknown`

### `wage_table_present_label`

- `yes`
- `maybe`
- `no`
- `unknown`

### `wage_table_page_match_label`

- `exact`
- `nearby`
- `wrong_page`
- `no_wage_table`
- `unknown`

### `contract_period_present_label`

- `yes`
- `maybe`
- `no`
- `unknown`

### `contract_period_hint_match_label`

- `correct`
- `partially_correct`
- `incorrect`
- `no_period_found`
- `unknown`

### `table_layout_type`

- `step_grade`
- `rank_step`
- `classification_table`
- `hourly_schedule`
- `annual_salary_schedule`
- `percent_increase_schedule`
- `appendix_table`
- `prose_only`
- `no_wage_table`
- `other`
- `unknown`

### `extraction_complexity_label`

- `easy`
- `moderate`
- `hard`
- `not_extractable`
- `unknown`

### `recommended_extraction_action`

- `include_in_wage_extraction_pilot`
- `include_after_schema_update`
- `manual_review_only`
- `exclude_for_now`
- `OCR_later`
- `unknown`

## Content restrictions

- Do not paste complete page or document text.
- Do not transcribe full wage tables.
- Do not record final wage values in this calibration file.
- Keep reviewer notes short and structural.
- Candidate page numbers are hints, not extracted observations.
- Manual labels do not mutate or replace durable detection/source/readiness
  ratings.
