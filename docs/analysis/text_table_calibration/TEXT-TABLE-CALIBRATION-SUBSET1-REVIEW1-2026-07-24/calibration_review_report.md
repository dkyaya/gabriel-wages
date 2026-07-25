# Text/Table Calibration Review Report

- review ID: `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
- method: `codex_assisted_local_adjudication`
- rows: 150
- reviewed/adjudicated rows: 150
- assisted-rule provisional status: `caution`
- final extraction gate after rendered-page QA: `fail`
- next recommendation: `refine_detector_or_schema`

This is deterministic assisted local adjudication, not human manual review. It inspected bounded candidate/adjacent/context pages and retained controlled labels only.

A later five-row rendered-page challenge materially disagreed with all five
assisted outcomes. These label counts are workflow diagnostics, not
independent precision estimates, and they do not authorize extraction. See
`calibration_visual_qa_spotcheck.md`.

## Page-hint precision

- correct: 118
- not_applicable: 17
- partially_correct: 14
- unknown: 1

## Wage-table presence

- maybe: 22
- no: 15
- unknown: 1
- yes: 112

## Contract-period hint match

- correct: 68
- incorrect: 12
- no_period_found: 20
- partially_correct: 30
- unknown: 20

## Extraction complexity

- easy: 11
- hard: 59
- moderate: 65
- not_extractable: 15

## Recommended action

- exclude_for_now: 15
- include_after_schema_update: 36
- include_in_wage_extraction_pilot: 76
- manual_review_only: 23

## Boundaries

- no URLs, downloads, network calls, or OCR
- no full page/document text or complete tables saved
- no final wage values, ingestion, or codification
- original prepared calibration CSV preserved
