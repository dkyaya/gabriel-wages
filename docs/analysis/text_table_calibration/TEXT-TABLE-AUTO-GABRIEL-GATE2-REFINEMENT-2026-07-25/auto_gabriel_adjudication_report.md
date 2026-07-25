# Automated visual + GABRIEL adjudication report

Gate: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`
Mode: `live`
Gate mode: `auto_gabriel_gate2_navigation_table_refine`
Method: `automated_local_visual_layout_navigation_offset_plus_gabriel_bounded_page_adjudication`

## Status

- Cases: 150
- Local bounded pages evaluated: 769
- Capped text characters supplied: 632553
- Rendered pages used for local features: 682
- GABRIEL backend: `huit_openai_responses_direct_sdk`
- GABRIEL model: `gpt-5.4-nano`
- Schema-valid responses: 150 / 150
- Failed/schema-invalid cases: 0
- Auto-gate labels: `{"exclude_for_now": 105, "extraction_ready_high_confidence": 9, "extraction_ready_with_schema_update": 13, "second_review_required": 23}`

## Decision

`continue_schema_refinement`

- 500-document extraction allowed: `false`
- Smaller extraction pilot allowed: `false`
- Original likely/p1 ready rate: 26.25%
- Wrong-page rate: 1.52%
- GABRIEL schema-valid rate: 100.00%

## Boundary

No URL or hosted search was used. No PDF/page text, complete table, or
structured wage value was saved. OCR, wage extraction, ingestion, codification,
wage-gap analysis, and durable-ledger mutation did not occur.
