# PDF Technical-Readiness Schema

Date: 2026-07-24

## Purpose and stage boundary

This schema records bounded technical checks on already-retained local PDF
artifacts. It measures artifact integrity, page count, sampled text-layer
presence, parser behavior, and a technical next action.

It does **not** establish final source quality, substantive relevance,
employer or bargaining-unit match, wage-table presence, wage values,
extraction-ready evidence, ingestion, codified evidence, or an analysis-ready
wage observation.

No full extracted text belongs in this ledger. OCR, wage extraction,
ingestion, and codification are outside this stage.

## Identity and inherited source-review fields

| Field | Meaning |
|---|---|
| `pdf_readiness_id` | Deterministic identifier for one retained artifact in one readiness pilot. |
| `source_review_id` | Durable source-review identity. |
| `candidate_queue_row_id` | Candidate-queue identity. |
| `triage_id` | Metadata content-triage identity. |
| `verification_id` | URL-routing/verification identity. |
| `source_review_pilot_id` | Source-review round that retained the artifact. |
| `state` | Candidate state metadata. |
| `municipality` | Candidate municipality metadata. |
| `government_name` | Candidate government name. |
| `unit_type` | Scout unit type: police, fire, non-safety, or inherited value. |
| `candidate_source_type` | Candidate source-type metadata. |
| `priority_for_content_review` | Metadata-triage scheduling priority. |
| `source_officialness_rating` | Preliminary source-review access/domain signal. |
| `source_relevance_rating` | Preliminary source-review relevance signal. |
| `document_type_rating` | Preliminary source-review document-type signal. |
| `extraction_readiness_rating` | Preliminary source-review artifact-access signal. |
| `content_artifact_path` | Existing lane-local retained PDF path. |
| `content_hash` | Durable SHA-256 recorded by source review. |
| `content_byte_size` | Durable retained byte size. |
| `content_type_observed` | Source-review observed content type. |

The readiness layer must preserve these fields without upgrading them.

## Readiness fields

| Field | Meaning |
|---|---|
| `readiness_status` | Terminal local readiness outcome. |
| `readiness_status_detail` | Concise technical detail; no substantive source judgment. |
| `artifact_exists` | Whether the locked local path exists. |
| `artifact_hash_verified` | Whether local SHA-256 and size match the durable source-review record. |
| `pdf_signature_valid` | Whether the retained artifact begins with a PDF signature. |
| `parser_library` | Local parser used; Pilot 1 uses `pypdf`. |
| `parser_version` | Installed parser version. |
| `parser_elapsed_seconds` | Bounded wall time for one artifact. |
| `pdf_page_count` | Page count, or `unknown` on failure. |
| `text_layer_status` | Result from at most three sampled pages. |
| `sampled_pages_checked` | Number of pages passed to bounded text extraction. |
| `sampled_pages_with_text` | Sampled pages returning at least one non-whitespace character. |
| `text_chars_sampled_total` | Count after the 500-character-per-page cap; text itself is discarded. |
| `text_extraction_error_type` | Sanitized parser exception class. |
| `text_extraction_error_sanitized` | Short error category/details without paths, URLs, or credentials. |
| `technical_parseability_rating` | Technical scheduling signal only. |
| `recommended_next_action` | Technical follow-up category. |
| `ocr_needed_signal` | `yes` only when sampled pages have no text; this does not authorize OCR. |
| `reviewer` | Script/reviewer identity. |
| `reviewed_at` | UTC timestamp. |

## Controlled values

### `readiness_status`

- `planned_not_checked` — dry-run only; artifact not opened.
- `readiness_checked` — integrity and bounded parser check completed.
- `artifact_missing` — locked retained path is absent.
- `hash_mismatch` — byte size or SHA-256 differs from the durable record.
- `artifact_problem` — artifact does not have a valid PDF signature.
- `parser_error` — bounded parser could not complete.

Every non-dry-run row must have exactly one terminal status.

### `text_layer_status`

- `present` — every sampled page returned text.
- `absent` — no sampled page returned text.
- `partial` — only some sampled pages returned text, or a page-level parser
  error occurred while another sampled page returned text.
- `unknown` — dry-run or integrity gate prevented parser inspection.
- `parser_error` — parser or page-level extraction failed without usable
  sampled text.

### `technical_parseability_rating`

- `high` — page count succeeded and all sampled pages returned text.
- `medium` — sampled text layer is partial.
- `low` — page count succeeded but sampled pages have no text, or a bounded
  page-level parser limitation occurred.
- `not_ready` — artifact missing/mismatched/invalid or parser could not open.
- `unknown` — dry-run or no technical determination.

These are technical scheduling aids, not extraction-readiness or evidence
ratings.

### `recommended_next_action`

- `parse_text_layer_later`
- `manual_review`
- `ocr_later`
- `exclude_for_now`
- `retry_with_different_parser`
- `inspect_artifact_problem`

`ocr_later` identifies a technical subset only. OCR remains separately
authorized and is not run by this pilot.

## Prohibited outputs

The runner and ledger must not contain:

- full extracted page or document text;
- wage-table cells or wage values;
- mechanism-language spans or classifications;
- credentials, tokens, cookies, raw authorization headers, or environment
  values;
- copied PDF binaries;
- ingested/codified identifiers or evidence promotions; or
- wage-gap, causal, or regression results.
