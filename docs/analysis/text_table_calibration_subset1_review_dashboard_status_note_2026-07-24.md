# Text/Table Calibration Subset 1 Review Dashboard Status

The dashboard now records:

- phase: `subset1_reviewed`
- review ID:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
- rows reviewed/adjudicated: 150 / 150
- method: `codex_assisted_local_adjudication`
- calibration gate: `fail`
- next recommendation: `refine_detector_or_schema`
- wage extraction: `not_started`
- ingestion: `not_started`
- codify: `not_started`
- wage-gap analysis: `not_started`

Displayed assisted labels include 112 yes, 22 maybe, 15 no, and one unknown
wage-table-presence result; 118 correct and 14 partially-correct page-hint
labels; and 76 include-now, 36 include-after-schema-update, 23 manual-only,
and 15 exclude-for-now recommendations.

The dashboard card explicitly says the review is assisted rather than
independent human ground truth, that 55 rows need second review, and that the
five-row rendered-page challenge materially disagreed with all five assisted
outcomes. No final wage extraction, OCR, ingestion, or codification occurred.
