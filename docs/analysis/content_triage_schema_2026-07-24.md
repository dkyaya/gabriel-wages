# Content-Triage and Extraction-Readiness Schema

Date: 2026-07-24

## Purpose and stage boundary

The durable content-triage ledger records a routing-aware decision about what
deserves deeper review. It does not download or ingest a source, extract a
wage, codify a mechanism, establish a matched city-cycle observation, or prove
a wage gap.

The stage sequence remains:

`candidate lead → URL-routing outcome → content-triaged source → source-quality rating → extraction-ready source → ingested source → codified evidence → analysis-ready wage observation`

## Identity and routing fields

| Field | Meaning |
|---|---|
| `triage_id` | Deterministic triage-stage identity. |
| `candidate_queue_row_id` | Immutable national candidate-queue row identity. |
| `verification_id` | Durable URL-routing identity. |
| `verification_round_id` | Round that produced the routing outcome. |
| `municipality_id` | Project municipality identity. |
| `census_gov_id` | Census government identity. |
| `state` | Two-letter state/DC code. |
| `municipality` | Candidate municipality label. |
| `government_name` | Authoritative government name from routing provenance. |
| `candidate_url` | Original candidate locator. |
| `final_url` | Final routed URL, if a response followed redirects. |
| `candidate_title` | Scout-supplied candidate title; still unverified. |
| `candidate_source_type` | Scout-supplied source-type label; still preliminary. |
| `candidate_status_before_verification` | Original scheduled/held/duplicate/canonical/rejected disposition. |
| `verification_status` | Terminal URL-routing status. |
| `content_type` | Canonicalized response content type. |
| `source_locator` | Final URL when available, otherwise original candidate URL. |

The lane input also retains triage bucket, candidate priority, routing lane,
duplicate group, source owner/unit labels, matched-set potential,
official-domain signal, selection rank, and stage provenance.

## Triage fields

| Field | Meaning |
|---|---|
| `triage_status` | Terminal or planned status at the triage stage. |
| `triage_status_detail` | Concise factual explanation of that status. |
| `source_relevance_prelim` | Metadata/content-based relevance judgment, explicitly preliminary. |
| `source_officialness_prelim` | Preliminary authority/ownership assessment. |
| `employer_match_prelim` | Whether the employer appears to match. |
| `municipality_match_prelim` | Whether the municipality appears to match. |
| `bargaining_unit_match_prelim` | Whether the bargaining unit appears to match. |
| `safety_unit_signal_prelim` | Preliminary police/fire signal. |
| `non_safety_unit_signal_prelim` | Preliminary comparison-unit signal. |
| `source_document_type_prelim` | Preliminary CBA/award/schedule/etc. type. |
| `source_year_or_period_prelim` | Period observed during later review. |
| `wage_table_signal_prelim` | Whether wage-table content may be present. |
| `wage_growth_signal_prelim` | Whether multiple time/effective-date wage observations may be present. |
| `mechanism_language_signal_prelim` | Whether later verbatim mechanism review may be useful. |
| `extraction_readiness_prelim` | Initial suitability for downstream structured extraction. |
| `priority_for_content_review` | `p1`, `p2`, `p3`, `defer`, or `exclude`. |
| `recommended_next_action` | Routing instruction for a later stage. |
| `duplicate_handling_status` | Canonical representative or linked-duplicate disposition. |
| `oversized_handling_status` | Ordinary/not oversized or separate-pass status. |
| `manual_review_reason` | Why human review is required. |
| `triage_notes` | Short factual notes; never a wage/causal conclusion. |
| `reviewer` | Later reviewer identity. Blank in planning/dry-run. |
| `triaged_at` | Later ISO timestamp. Blank in planning/dry-run. |

## Controlled values

`triage_status`:

- `triage_planned`
- `high_priority_content_review`
- `medium_priority_content_review`
- `low_priority_content_review`
- `duplicate_defer_to_canonical`
- `oversized_needs_separate_pass`
- `blocked_or_unreachable_defer`
- `not_relevant_on_metadata`
- `needs_manual_review`
- `already_canonical_context`
- `excluded_from_content_review`

For the metadata-only execution path, any non-planning terminal status is a
preliminary scheduling outcome derived solely from committed candidate and
routing fields. It is not a content-reviewed classification.

`source_relevance_prelim`:

- `likely_relevant`
- `possibly_relevant`
- `unlikely_relevant`
- `unknown`

`source_officialness_prelim`:

- `official_municipal`
- `official_union`
- `state_repository`
- `third_party_reliable`
- `third_party_uncertain`
- `unofficial`
- `unknown`

Employer, municipality, and bargaining-unit match values:

- `likely_match`
- `possible_match`
- `mismatch`
- `unknown`

Signal values:

- `likely_present`
- `possible`
- `unlikely`
- `unknown`

`extraction_readiness_prelim`:

- `high`
- `medium`
- `low`
- `none`
- `unknown`

`priority_for_content_review`:

- `p1`
- `p2`
- `p3`
- `defer`
- `exclude`

`recommended_next_action`:

- `content_review_download_allowed_later`
- `metadata_review_only`
- `duplicate_group_review`
- `oversized_strategy_later`
- `blocked_status_review_later`
- `exclude_for_now`
- `manual_review`

## Interpretation rules

- `triage_planned` means only that an identity and schema passed offline
  planning.
- A likely source type remains preliminary until content is reviewed.
- Triage does not authorize download, ingestion, codification, or extraction.
- Wage-table or wage-growth signals do not contain extracted wage values.
- Mechanism signals do not replace verbatim clause capture.
- No triage field proves a wage gap or causal mechanism.
- `reviewer = script_metadata_only` identifies deterministic offline
  classification, not human source review.
- `content_review_download_allowed_later` means only that a separately
  authorized content-review task may consider the row; it does not authorize
  source access in the metadata-only task.
- URL-routing exceptions have metadata-only terminal routes:
  `too_large` goes to `oversized_needs_separate_pass`; blocked/not-found goes
  to `blocked_or_unreachable_defer`; error/SSL/timeout/connection outcomes go
  to `needs_manual_review`; and duplicate statuses go to
  `duplicate_defer_to_canonical`.
- These exception routes are not findings that a municipality lacks a source.
- Original context, insufficient, duplicate, canonical, and rejected
  dispositions must remain visible and cannot be promoted solely because a URL
  was routed.
