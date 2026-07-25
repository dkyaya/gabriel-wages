# Text/Table Calibration Subset 1 Readiness Audit

## Decision

`ready_to_prepare_offline_calibration_packet`

The durable full-run detection layer is structurally ready for a 150-row
manual calibration packet. This task prepares review materials only; it does
not open PDFs, perform manual review, change detection outcomes, or authorize
wage extraction.

## Repository gate

- pre-work HEAD:
  `32ae355693cda097a6ca0a6da7e7c2cf49f514b0`
- tracked worktree at start: clean
- unrelated untracked item preserved and excluded: `package-lock.json`
- requested ancestor commits confirmed:
  `32ae355`, `827917b`, `11e689a`, `b45876e`, `74a843a`,
  `985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`,
  and `e028432`
- git remotes inspected or modified: no
- fetch / pull / push: 0 / 0 / 0

## Durable authority

The calibration authority is:

`docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_cumulative.csv`

It contains:

- rows: 1,828
- unique `text_table_detection_id`: 1,828
- unique `pdf_readiness_id`: 1,828
- unique `source_review_id`: 1,828
- unique `candidate_queue_row_id`: 1,828
- detection status: `detection_checked` 1,828
- candidate wage-page hints: 7,649
- wage-table signal:
  - likely: 1,067
  - possible: 749
  - unlikely: 12
- extraction-pilot priority:
  - p1: 1,067
  - p2: 754
  - p3: 7
- recommended next action:
  - `wage_table_extraction_pilot`: 1,067
  - `larger_text_detection_pass`: 747
  - `contract_period_extraction_pilot`: 7
  - `manual_review`: 7

The durable summary is
`docs/analysis/text_table_detection_ledgers/text_table_detection_summary_cumulative.json`
and reports complete equality with the durable parse-text PDF-readiness
authority. The detection ledger contains signals, candidate page numbers, and
bounded redacted contract-period hints; it contains no final wage-value field
or final extracted wage observations.

## Why calibration is required

The frozen heuristic labels 1,816 of 1,828 rows likely or possible, a 99.3435%
high-recall rate. That is useful for scheduling but cannot be interpreted as
precision or wage-table prevalence. Manual review must measure:

1. whether hinted pages actually contain wage tables;
2. whether likely and possible signals have meaningfully different precision;
3. which prose, benefit, numeric, appendix, or other layouts create false
   positives;
4. whether bounded contract-period hints match the document;
5. which table layouts and extraction difficulties should shape a later pilot.

## Calibration design

Prepare 150 review rows:

- 80 likely;
- 58 possible, including the two possible p3/manual-review cases and one
  additional partial-text/long-document edge where available;
- all 12 unlikely rows.

The deterministic selector must retain all seven p3/manual-review rows and
diversify within signal quotas across unit type, source type, officialness,
source-review batch, page-count bin, state, municipality, text-layer status,
and recommended action. The 80 / 58 / 12 allocation adapts the requested
80 / 55 / 12 + three-edge design without changing the 150-row total.

## Explicit boundary

- local CSV/JSON/Markdown inputs only
- PDFs opened: 0
- URLs opened: 0
- additional text extraction: 0
- OCR: 0
- full-text output: 0
- final wage extraction: 0
- ingestion / codify: 0 / 0
- durable routing, triage, source-review, PDF-readiness, or text/table ledger
  mutation: 0
- manual review completed in this task: no

Page hints and bounded contract-period hints remain preliminary heuristic
inputs. Calibration labels are initialized as `not_reviewed`/`unknown`, not
filled or adjudicated.
