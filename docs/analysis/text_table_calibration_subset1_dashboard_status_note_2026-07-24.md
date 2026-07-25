# Text/Table Calibration Subset 1 Dashboard Status

The dashboard calibration layer records preparation only:

- phase: `subset1_prepared_not_reviewed`
- calibration ID:
  `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`
- packet rows: 150
- signal allocation: likely 80; possible 58; unlikely 12
- manual review: `not_started`
- final wage extraction: `not_started`
- ingestion: `not_started`
- codify: `not_started`
- wage-gap analysis: `not_started`

The status source is:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_sampling_summary.json`

The dashboard card explicitly states that the subset is prepared but not
reviewed and that candidate pages remain heuristic hints. It does not imply
precision has been estimated, extraction rules have been approved, or wage
values have been extracted.

Preparation used no PDF or URL access, no additional text extraction, no OCR,
no ingestion/codification, and no durable-ledger mutation.
