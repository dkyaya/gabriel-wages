# Gate 2 dashboard status note

The text/table calibration dashboard now reports
`calibration_phase = auto_gabriel_gate2_completed` and identifies
`TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25` as the latest automated
gate, with Gate 1 retained as the prior gate.

Displayed Gate 2 facts are:

- 150 cases and 100% strict-schema GABRIEL validity;
- 9 high-confidence-ready, 13 schema-update-ready, 23 second-review, and 105
  excluded rows;
- 21/80 (26.25%) original likely/p1 ready;
- 2/132 (1.52%) candidate-bearing wrong pages;
- decision `continue_schema_refinement`;
- next recommendation `refine_auto_gabriel_gate3_candidate_discovery`.

The dashboard continues to show wage extraction, ingestion, codification, and
wage-gap analysis as `not_started`. Its caveats state that automated
adjudication is calibration, no final wage values were extracted, OCR and
ingestion did not occur, and GABRIEL saw bounded page packets only.
