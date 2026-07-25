# Automated GABRIEL compensation-evidence adjudication report

Gate: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`
Mode: `live_resume`
Method: `automated_bounded_rendered_image_plus_text_layout_gabriel_compensation_evidence_adjudication`

## Status

- Cases: 150
- Local bounded pages evaluated: 769
- Capped text characters supplied: 632553
- Image evidence used: `true`
- Image fallback occurred: `false`
- GABRIEL backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`
- Schema-valid responses: 150 / 150
- Categories: `{"mixed_quant_qual_ready": 84, "non_wage_compensation": 31, "not_compensation_relevant": 7, "qual_mechanism_ready": 12, "quant_compact_ready": 1, "quant_table_ready": 14, "reference_navigation_only": 1}`

## Decision

`500_doc_compensation_extraction_allowed`

- 500-document compensation extraction allowed: `true`
- Smaller compensation pilot allowed: `false`
- Original likely/p1 ready rate: 87.50%
- GABRIEL schema-valid rate: 100.00%

## Boundary

Only bounded local evidence was adjudicated. No URL, hosted search, download,
OCR, wage extraction, qualitative final extraction, ingestion, codification,
wage-gap analysis, full-text/table saving, or raw prompt/response saving occurred.
