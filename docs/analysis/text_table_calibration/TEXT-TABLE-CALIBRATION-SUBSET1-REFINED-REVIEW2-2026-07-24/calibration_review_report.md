# Text/Table Calibration Review Report

- review ID: `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`
- method: `codex_refined_visual_table_gate_v1`
- rows: 150
- reviewed/adjudicated rows: 150
- calibration status: `requires_independent_adjudication`
- next recommendation: `independent_refined_calibration_decision`

This is deterministic assisted local adjudication, not human manual review. It inspected bounded candidate/adjacent/context pages and retained controlled labels only.

## Page-hint precision

- correct: 84
- incorrect: 42
- not_applicable: 17
- partially_correct: 6
- unknown: 1

## Wage-table presence

- maybe: 16
- no: 56
- unknown: 1
- yes: 77

## Contract-period hint match

- correct: 96
- incorrect: 1
- no_period_found: 11
- partially_correct: 23
- unknown: 19

## Extraction complexity

- easy: 26
- hard: 44
- moderate: 48
- not_extractable: 32

## Recommended action

- exclude_for_now: 32
- include_after_schema_update: 15
- include_in_wage_extraction_pilot: 74
- manual_review_only: 29

## Boundaries

- no URLs, downloads, network calls, or OCR
- no full page/document text or complete tables saved
- no final wage values, ingestion, or codification
- original prepared calibration CSV preserved
