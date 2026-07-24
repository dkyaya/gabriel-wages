# Source-Rating and Content-Review Schema

Date: 2026-07-24

## Purpose and boundary

This schema defines the future durable layer created only after a reviewer or
approved bounded review process inspects source content. It is distinct from:

1. candidate discovery;
2. URL-routing availability;
3. metadata-only triage;
4. final source review and rating;
5. extraction readiness established from content;
6. ingestion;
7. codified evidence; and
8. analysis-ready wage observations.

The present framework and pilot inputs do not populate final ratings. Unknown
values in dry-run output are intentional.

## Identity fields

| Field | Meaning |
|---|---|
| `source_review_id` | Deterministic identity for one candidate in one review pilot. |
| `triage_id` | Durable metadata-triage identity. |
| `candidate_queue_row_id` | Stable candidate-queue identity. |
| `verification_id` | Durable URL-routing identity. |
| `municipality_id` | Project municipality identity. |
| `census_gov_id` | Census government identity when available. |
| `state` | Two-letter state or DC code. |
| `municipality` | Municipality label. |
| `government_name` | Government/employer label inherited from candidate metadata. |
| `candidate_url` | Original candidate locator; not opened by planning. |
| `final_url` | Routed final locator; not opened by planning. |
| `source_locator` | Preferred locator for a future authorized review. |
| `candidate_title` | Candidate title inherited from discovery. |
| `candidate_source_type` | Candidate document-type label, not a final rating. |
| `candidate_status_before_verification` | Original candidate disposition. |
| `verification_status` | URL-routing outcome. |
| `content_type` | Routed response content type. |
| `triage_status` | Metadata-only triage status. |
| `priority_for_content_review` | Metadata-only review priority. |
| `recommended_next_action` | Metadata-only routing action. |

## Review and artifact fields

| Field | Meaning |
|---|---|
| `source_review_status` | Terminal or planned review workflow status. |
| `source_review_status_detail` | Concise reason for the workflow status. |
| `url_access_status` | Whether later authorized access succeeded. |
| `download_status` | Whether a bounded artifact was downloaded. |
| `content_artifact_path` | Lane-local or durable path to reviewed content. |
| `content_hash` | Cryptographic hash of the exact reviewed bytes. |
| `content_byte_size` | Bytes in the reviewed artifact. |
| `content_type_observed` | Content type confirmed during review. |
| `text_layer_status` | Whether usable text is present. |
| `pdf_page_count` | PDF page count when applicable. |
| `source_officialness_rating` | Content- and provenance-based source rating. |
| `source_relevance_rating` | Relevance to the research corpus. |
| `municipality_match_rating` | Match to the intended municipality. |
| `employer_match_rating` | Match to the intended employer. |
| `bargaining_unit_match_rating` | Match to the intended bargaining unit. |
| `safety_unit_match_signal` | Content-based safety-unit signal. |
| `non_safety_unit_match_signal` | Content-based non-safety-unit signal. |
| `document_type_rating` | Document type established from source content. |
| `contract_or_document_period_start` | Earliest applicable date/period. |
| `contract_or_document_period_end` | Latest applicable date/period. |
| `wage_table_signal` | Presence signal only; not extracted wages. |
| `wage_growth_signal` | Presence signal only; not a wage-growth measure. |
| `mechanism_language_signal` | Presence signal only; no causal interpretation. |
| `extraction_readiness_rating` | Readiness after technical/content review. |
| `extraction_mode_recommended` | Recommended later extraction route. |
| `duplicate_canonical_decision` | Canonical/duplicate decision after review. |
| `reviewer_notes` | Concise evidence and caveats supporting the rating. |
| `reviewer` | Human or approved deterministic reviewer identity. |
| `reviewed_at` | UTC ISO-8601 review timestamp. |

## Controlled values

### Source officialness

- `official_municipal`
- `official_union`
- `official_state_repository`
- `reliable_third_party`
- `uncertain`
- `unofficial`
- `unknown`

### Source relevance

- `high`
- `medium`
- `low`
- `none`
- `unknown`

### Municipality, employer, and unit match

- `confirmed`
- `likely`
- `possible`
- `mismatch`
- `unknown`

### Document type

- `cba`
- `wage_schedule`
- `compensation_plan`
- `ordinance`
- `arbitration_award`
- `memorandum_or_settlement`
- `factfinding_report`
- `budget_or_financial_record`
- `portal_index`
- `unrelated`
- `unknown`

### Extraction readiness

- `high`
- `medium`
- `low`
- `not_ready`
- `unknown`

### Recommended extraction mode

- `text_layer_pdf`
- `html_table`
- `pdf_table_extraction`
- `manual_review`
- `ocr_later`
- `oversized_strategy`
- `duplicate_skip`
- `exclude`

## Workflow statuses

The initial dry-run uses `planned_not_reviewed`. A later implementation should
define a small explicit terminal vocabulary, such as:

- `reviewed_relevant`
- `reviewed_context_only`
- `reviewed_not_relevant`
- `duplicate_of_reviewed_source`
- `download_failed`
- `needs_manual_review`
- `oversized_deferred`
- `excluded`

No status may imply ingestion, codification, wage extraction, or an
analysis-ready observation.

## Provenance and safety requirements

A live review must checkpoint every row, hash every retained content artifact,
keep artifacts lane-local until a separately audited merge, sanitize errors,
and record access/download/parse/OCR counters. It must never silently replace
metadata-only values with final ratings when content was unavailable.

Source rating requires source content. Metadata-only triage cannot produce a
final rating, cannot prove wage data exist, and cannot support wage-gap or
causal claims.
