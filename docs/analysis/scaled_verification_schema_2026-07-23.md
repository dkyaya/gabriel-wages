# Scaled Candidate-Source Verification Schema

Date: 2026-07-23/24
Schema version: `2.0.0`

## Purpose and stage boundary

The durable verification ledger records whether a candidate source lead is
real, reachable, relevant to the exact municipal employer and unit, and worth
downstream processing. Verification is not document ingestion, wage
extraction, GABRIEL codification, proof of a matched comparison, a wage-gap
calculation, or claim evidence.

One ledger row preserves one original candidate-queue identity, even when
several rows resolve to the same underlying URL. Exact duplicates share a
`duplicate_source_group_id`; they are linked, not deleted.

## Required identity fields

| Field | Definition |
|---|---|
| `verification_id` | Stable unique ID derived from the original queue row ID. |
| `candidate_queue_row_id` | Original `queue_id`; never rewritten. |
| `candidate_queue_stable_key` | Durable candidate key; initially equal to the queue ID. |
| `municipality_id` | Authoritative project municipality ID. |
| `census_gov_id` | Census government-units ID from the committed universe. |
| `state` | Two-letter state/DC abbreviation. |
| `municipality` | Project municipality label. |
| `government_name` | Authoritative Census government name. |
| `candidate_url` | Original queue locator, unchanged. |
| `candidate_title` | Original scout candidate title. |
| `candidate_source_type` | Scout-stage document-type label. |
| `candidate_priority` | `high`, `medium`, `low`, or `held`. |
| `candidate_status_before_verification` | Scheduled/hold/duplicate/canonical/rejection disposition. |

Planning inputs may also carry state yield, population, unit type, scout
confidence, source owner, triage score, source wave, and stable duplicate keys.
These are ordering/audit metadata, not verification findings.

## Required verification fields

| Field | Meaning |
|---|---|
| `verification_status` | Controlled terminal or review status below. |
| `verification_status_detail` | Concise reason or sub-status. |
| `url_reachable` | `yes`, `no`, `not_checked`, or `unknown`. |
| `http_status_code` | Observed HTTP status, blank when unavailable/not checked. |
| `final_url` | Redirect-resolved URL, preserving the original separately. |
| `redirect_detected` | `yes`, `no`, `not_checked`, or `unknown`. |
| `content_type` | Observed response content type. |
| `source_officialness` | Controlled provenance class below. |
| `employer_match_status` | Exact/wrong/unclear/not-checked employer result. |
| `municipality_match_status` | Exact/wrong/unclear/not-checked municipality result. |
| `source_document_type_verified` | Reviewer-confirmed document type. |
| `source_year_or_period` | Visible verified year/cycle information; no invented dates. |
| `safety_unit_signal` | Whether police/fire unit evidence is visible. |
| `non_safety_unit_signal` | Whether comparison-unit evidence is visible. |
| `wage_data_signal` | Whether wage content appears present; no extraction here. |
| `wage_growth_extractability` | Controlled extractability value below. |
| `mechanism_language_signal` | Controlled mechanism-language signal below. |
| `duplicate_source_group_id` | Stable exact-URL/source group. |
| `canonical_source_candidate` | Whether the source may warrant canonical review; not promotion. |
| `verification_notes` | Brief evidence-based reviewer note. |
| `reviewer` | Reviewer identity or process ID. |
| `verified_at` | ISO timestamp for actual live/manual review. |
| `artifact_path` | Lane-local verification artifact, never a corpus promotion. |

## Controlled verification statuses

The bounded automated reachability pass uses conservative transport/document
statuses:

- `reachable_http`
- `reachable_html`
- `reachable_pdf_or_document`
- `blocked_or_forbidden`
- `not_found`
- `timeout`
- `connection_error`
- `ssl_error`
- `too_large`
- `unsupported_scheme`
- `invalid_url`
- `error`
- `duplicate_of_verified_source`
- `duplicate_same_url_pending`

`dry_run_planned` is the offline-only status. `pending` may appear in a
checkpointed, interrupted live ledger and is not terminal.

The later reviewer/enrichment layer may use:

- `verified_candidate_source`
- `verified_context_source`
- `duplicate_of_verified_source`
- `reachable_but_wrong_employer`
- `reachable_but_not_relevant`
- `unreachable`
- `blocked_or_forbidden`
- `needs_manual_review`
- `unsupported_file_type`
- `insufficient_metadata`
- `already_canonical`
- `error`

The automated ledger also records `redirect_chain_length`,
`content_length_header`, `bytes_read`, `fetch_elapsed_seconds`,
`error_type`, and `error_message_sanitized`. Its
`source_officialness_prelim`, `employer_match_prelim`,
`source_document_type_prelim`, `wage_data_signal_prelim`, and
`mechanism_language_signal_prelim` fields remain `unknown` or
`needs_content_review` unless a later authorized content-review stage supplies
evidence. They do not replace the durable reviewer-confirmed fields above.

## Controlled provenance and signal values

`source_officialness`:

- `official_municipal`
- `official_union`
- `state_repository`
- `third_party_reliable`
- `third_party_uncertain`
- `unofficial`
- `unknown`

`wage_growth_extractability`:

- `high`
- `medium`
- `low`
- `none`
- `unknown`

`mechanism_language_signal`:

- `likely_present`
- `possible`
- `unlikely`
- `unknown`

Signal fields are routing observations only. They do not extract a wage,
classify a mechanism, establish a matched cycle, or support a substantive
claim. Exact document text and wage tables belong to later provenance-gated
extraction/ingestion stages.
