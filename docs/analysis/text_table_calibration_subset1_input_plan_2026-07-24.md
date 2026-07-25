# Text/Table Calibration Subset 1 Input Plan

## Locked packet

- calibration round:
  `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`
- durable authority:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_cumulative.csv`
- durable authority rows: 1,828
- selected calibration rows: 150
- unique calibration/detection/PDF-readiness/source-review/candidate IDs:
  150 each
- manual review status: `not_started`
- calibration status on every row: `not_reviewed`

The planner command was:

```text
.venv/bin/python scripts/prepare_text_table_calibration_subset.py \
  --text-table-ledger-csv docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_cumulative.csv \
  --pdf-readiness-ledger-csv docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --output-dir docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24 \
  --calibration-id TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24 \
  --sample-size 150 \
  --stratify \
  --include-unlikely \
  --plan-only
```

## Signal allocation

- likely: 80
- possible: 58
- unlikely: 12

All 12 unlikely rows are included. The 58 possible rows comprise the requested
55-row base plus three explicit edge rows: both possible p3/manual-review
cases and one partial-text, over-100-page case. All seven durable p3/manual-
review rows are present across the possible and unlikely strata.

Selection-reason counts:

- `stratified_likely`: 80
- `stratified_possible`: 55
- `all_unlikely_boundary_case`: 12
- `manual_review_p3_edge`: 2
- `partial_text_over_100_edge`: 1

## Calibration-relevant distributions

### Extraction-pilot priority

- p1: 80
- p2: 63
- p3: 7

### Upstream content-review priority

- p1: 73
- p2: 77

### Unit type

- police: 51
- fire: 44
- non-safety: 55

### Candidate/source type

- CBA: 80
- wage schedule or compensation plan: 30
- memorandum or settlement: 15
- ordinance or policy: 16
- arbitration award: 8
- factfinding: 1

### Preliminary officialness

- official municipal: 52
- official state repository: 23
- official union: 16
- uncertain: 50
- unknown: 9

### Source-review batch

- Pilot 1: 26
- Batch 2: 38
- Batch 3: 86

### Page-count bin

- 1–10: 40
- 11–25: 24
- 26–50: 33
- 51–100: 38
- over 100: 15

### Text-layer status

- present: 98
- partial: 52

### Geography

- states plus DC represented: 51 / 51
- distinct state/municipality pairs: 150

The state distribution is recorded in
`calibration_sampling_summary.json`. The selector uses deterministic
rarity/diversity scoring inside fixed signal quotas and avoids duplicate
municipalities where possible.

## Candidate-page workload

- total candidate wage-page hints: 562
- rows with no candidate wage-page hint: 18

No-hint rows are deliberately retained where required by unlikely/manual edge
coverage so reviewers can assess false-negative or wrong-signal behavior.

## Integrity and scope

- selected PDF-readiness identity coverage: 150 / 150
- selected source-review identity coverage: 150 / 150
- inherited artifact path/page-count/text-layer mismatches: 0
- PDFs opened during planning: 0
- URLs opened during planning: 0
- additional text extraction: 0
- OCR: 0
- full text saved: 0
- final wage extraction: 0
- durable ledger mutations: 0

The packet contains only durable identities, metadata, detection signals,
candidate page numbers, the already-merged bounded/redacted contract-period
hint, and blank/unknown manual-review fields.
