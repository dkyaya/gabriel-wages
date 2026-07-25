# Independent adjudication PREP1 dashboard status note

Date: 2026-07-25

The dashboard calibration card and generated status JSON now report:

- `calibration_phase = independent_adjudication_packet_prepared`;
- `latest_adjudication_prep_id = TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`;
- `prior_refined_review_id = TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`;
- `prior_extraction_decision = continue_schema_refinement`;
- `independent_human_review_status = packet_prepared_not_reviewed`;
- `wage_extraction_status = not_started`;
- `ingestion_status = not_started`;
- `codify_status = not_started`;
- `wage_gap_analysis_status = not_started`;
- `next_recommendation = independent_human_adjudication`.

The card states that 150 blinded cases and 785 bounded local page aids are
prepared, human review has not started, prior labels/actions are absent from
the human-facing CSV, and neither the 500-document nor smaller extraction run
is authorized. The frontend change is limited to the existing calibration
card; there is no dashboard redesign.

The displayed caveats are explicit: REVIEW2 did not authorize extraction, the
human packet is blinded to prior labels, and no wage extraction has started.
OCR, ingestion, and codification also remain unrun.
