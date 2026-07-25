# Dashboard status note: automated GABRIEL adjudication gate 1

The text/table calibration dashboard now records completion of
`TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`.

- Phase: `auto_gabriel_gate1_completed`
- Method:
  `automated_local_visual_layout_plus_gabriel_bounded_page_adjudication`
- Cases: 150
- GABRIEL schema-valid rate: 1.0
- Auto gate labels: 12 high-confidence ready, 16 schema-update ready, 19
  second review, 103 excluded
- Wrong-page rate: 0.068182
- Extraction decision: `continue_schema_refinement`
- 500-document extraction: not allowed
- Smaller extraction pilot: not allowed
- Wage extraction, ingestion, codification, and wage-gap analysis: not started
- Next recommendation: `refine_auto_gabriel_table_and_navigation_gate`

The dashboard caveats state that this is calibration rather than final wage
extraction, no final wage values were extracted, OCR and ingestion did not
occur, and GABRIEL saw bounded page packets only.
