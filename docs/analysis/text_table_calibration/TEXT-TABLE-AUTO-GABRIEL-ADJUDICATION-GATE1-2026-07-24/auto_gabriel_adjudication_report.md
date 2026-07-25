# Automated visual + GABRIEL adjudication report

Gate: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`
Mode: `live`
Method: `automated_local_visual_layout_plus_gabriel_bounded_page_adjudication`

## Status

- Cases: 150
- Local bounded pages evaluated: 738
- Capped text characters supplied: 585644
- Rendered pages used for local features: 734
- GABRIEL backend: `huit_openai_responses_direct_sdk`
- GABRIEL model: `gpt-5.4-nano`
- Schema-valid responses: 150 / 150
- Failed/schema-invalid cases: 0
- Auto-gate labels: `{"exclude_for_now": 103, "extraction_ready_high_confidence": 12, "extraction_ready_with_schema_update": 16, "second_review_required": 19}`

## Decision

`continue_schema_refinement`

- 500-document extraction allowed: `false`
- Smaller extraction pilot allowed: `false`
- Original likely/p1 ready rate: 33.75%
- Wrong-page rate: 6.82%
- GABRIEL schema-valid rate: 100.00%

## Boundary

No URL or hosted search was used. No PDF/page text, complete table, or
structured wage value was saved. OCR, wage extraction, ingestion, codification,
wage-gap analysis, and durable-ledger mutation did not occur.
