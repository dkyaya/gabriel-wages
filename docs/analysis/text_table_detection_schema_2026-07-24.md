# Text-Layer/Table-Detection Schema

Date: 2026-07-24

Status: local pilot schema; no durable detection ledger exists

## Purpose and evidence boundary

One row records one bounded local text-layer/table-detection attempt for one
already-retained, PDF-readiness-approved source-review artifact.

This layer records heuristic page and structure signals. It is not a wage
observation, a final document classification, ingested evidence, codified
evidence, or an analysis-ready record. Candidate wage pages are page hints
only. Text-layer presence and a likely table signal do not prove that a page
contains the intended bargaining unit's wage schedule.

The runner may hold bounded page text in memory while classifying signals.
It must not save full page or document text. The only permitted text output
is a redacted contract-period hint totaling no more than 300 characters per
document.

## Identity and inherited fields

- `text_table_detection_id`: deterministic ID for this pilot attempt.
- `pdf_readiness_id`: durable PDF-readiness identity.
- `source_review_id`: durable source-review identity.
- `candidate_queue_row_id`: candidate-queue identity.
- `triage_id`: metadata-triage identity.
- `verification_id`: URL-routing/verification identity.
- `source_review_pilot_id`: retained-artifact source-review round.
- `state`
- `municipality`
- `government_name`
- `unit_type`
- `candidate_source_type`
- `priority_for_content_review`
- `source_officialness_rating`
- `source_relevance_rating`
- `document_type_rating`
- `extraction_readiness_rating`
- `content_artifact_path`
- `content_hash`
- `content_byte_size`
- `pdf_page_count`
- `text_layer_status`

These fields are inherited unchanged from the durable PDF-readiness layer.
They must not be promoted from preliminary metadata to content-supported
findings by this pilot.

## Detection fields

- `detection_status`
- `detection_status_detail`
- `parser_library`
- `parser_version`
- `parser_elapsed_seconds`
- `pages_scanned`
- `pages_with_text`
- `total_text_chars_scanned`
- `wage_table_signal`
- `wage_table_signal_confidence`
- `candidate_wage_pages`
- `candidate_wage_page_count`
- `contract_period_signal`
- `contract_period_confidence`
- `candidate_contract_period_text`
- `pay_schedule_signal`
- `salary_schedule_signal`
- `hourly_rate_signal`
- `step_grade_signal`
- `rank_position_signal`
- `effective_date_signal`
- `bargaining_unit_signal`
- `public_safety_signal`
- `non_safety_signal`
- `table_like_structure_signal`
- `table_detection_method`
- `extraction_pilot_priority`
- `recommended_next_action`
- `detection_notes`
- `reviewer`
- `reviewed_at`

`candidate_wage_pages` contains comma-separated, one-based page numbers
only. It never contains table cells or wage values.

`candidate_contract_period_text` may contain a short date/period hint. It is
whitespace-normalized, currency and percent tokens are redacted, and the
combined output is capped at 300 characters per document.

## Controlled vocabularies

### `detection_status`

- `detection_checked`
- `no_text_available`
- `parser_error`
- `artifact_missing`
- `hash_mismatch`
- `skipped_not_parse_text_candidate`
- `error`

Every selected row must receive one terminal status.

### `wage_table_signal`

- `likely`
- `possible`
- `unlikely`
- `unknown`

### `contract_period_signal`

- `likely`
- `possible`
- `unlikely`
- `unknown`

### `table_like_structure_signal`

- `likely`
- `possible`
- `unlikely`
- `unknown`

### Confidence fields

`wage_table_signal_confidence` and `contract_period_confidence` use:

- `high`
- `medium`
- `low`
- `unknown`

### Component signals

The pay, salary, hourly, step/grade, rank/position, effective-date,
bargaining-unit, public-safety, and non-safety component fields use:

- `detected`
- `not_detected`
- `unknown`

### `extraction_pilot_priority`

- `p1`
- `p2`
- `p3`
- `defer`
- `exclude`

This priority schedules later human or extraction-pilot work. It is not the
metadata-triage priority and does not establish substantive relevance.

### `recommended_next_action`

- `wage_table_extraction_pilot`
- `contract_period_extraction_pilot`
- `larger_text_detection_pass`
- `manual_review`
- `ocr_later`
- `exclude_for_now`

No recommendation authorizes the action by itself.

## Deterministic signal policy

The pilot uses a documented keyword/numeric-structure heuristic:

- likely wage-table signal requires multiple pay/schedule concepts plus
  table-like numeric structure on at least one scanned page;
- possible wage-table signal requires weaker pay or structure evidence;
- likely contract-period signal requires agreement/effective/period context
  and bounded date/year evidence;
- possible contract-period signal requires weaker context or date evidence;
- unknown is reserved for unavailable text; and
- unlikely means bounded readable text lacked the relevant signals.

Money-like and percentage tokens may be counted in memory for structure
detection but are never written to the ledger.

## Prohibited outputs

The schema must not contain:

- final wage rates or salary values;
- reconstructed wage tables;
- full page or document text;
- OCR text;
- ingested contract rows;
- codified mechanism evidence;
- wage changes, wage gaps, regression outputs, or causal claims.
