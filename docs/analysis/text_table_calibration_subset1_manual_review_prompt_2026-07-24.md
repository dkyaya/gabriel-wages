# Future Manual Review Prompt: Text/Table Calibration Subset 1

This document describes a future human-review task. It is not executed during
packet preparation.

## Scope

Review the 150 rows in:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv`

Use the accompanying workbook and rubric. Preserve the original prepared CSV
unchanged. Write completed judgments to a separately named reviewed output,
for example:

`tmp/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_reviewed_attempt1.csv`

Do not modify durable routing, metadata-triage, source-review, PDF-readiness,
or text/table-detection ledgers.

## Review procedure

For each row:

1. Open only the already-retained local path in `content_artifact_path`.
2. Confirm the artifact corresponds to the listed government, municipality,
   unit, and source type. Record discrepancies in short reviewer notes; do not
   repair durable metadata during calibration.
3. Inspect the 1-indexed pages in `candidate_wage_pages`.
4. Inspect an immediately adjacent page only when a table clearly continues
   across a page boundary or the hint is demonstrably nearby.
5. Record:
   - page-hint precision;
   - wage-table presence;
   - exact/nearby/wrong/no-table page match;
   - contract-period presence and hint match;
   - table layout;
   - extraction complexity;
   - concise false-positive family;
   - recommended extraction action;
   - reviewer confidence.
6. Set `calibration_status=reviewed` only when all required fields are
   complete. Use `needs_second_review` for ambiguity.

## Content boundary

- Do not transcribe full wage tables.
- Do not extract or normalize final wage values.
- Do not paste full pages or complete document text.
- Keep notes structural and short.
- Do not OCR absent/partial content.
- Do not ingest or codify documents.
- Do not calculate wage gaps or make causal claims.

## Calibration outputs to calculate later

After review and adjudication, report:

- precision of likely candidate-page hints;
- precision of possible candidate-page hints;
- behavior of all unlikely rows;
- false-positive families;
- contract-period-hint match rates;
- table-layout and complexity distributions;
- inter-reviewer or second-review disagreements, if applicable;
- recommendation for a bounded extraction pilot:
  likely-only, likely plus selected possible, or a narrower rule-based subset.

Do not treat the reviewed calibration sample as a population prevalence
estimate without accounting for the deliberate stratified oversampling.
