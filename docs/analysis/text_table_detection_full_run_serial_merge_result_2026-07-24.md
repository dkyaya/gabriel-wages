# Full Text/Table Detection Serial-Merge Result

## Result

`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-MERGE-2026-07-24`
completed successfully as one serial offline merge.

The operative durable result contains only the four lane ledgers from
`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`. The earlier 150-row Pilot 1
is preserved as superseded diagnostic provenance and contributes zero
additional durable rows because all its PDF-readiness identities were rerun in
the full pass.

## Command

```text
.venv/bin/python scripts/merge_text_table_detection_lanes.py \
  --manifest docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/text_table_detection_pilot_manifest.json \
  --audit-summary tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/serial_merge_lane_audit_2026-07-24/text_table_detection_lane_audit_summary.json \
  --pdf-readiness-ledger-csv docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv \
  --output-dir docs/analysis/text_table_detection_ledgers \
  --merge-id TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-MERGE-2026-07-24
```

The production command was invoked exactly once.

## Durable outputs

- cumulative ledger:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_cumulative.csv`
- cumulative summary:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_summary_cumulative.json`
- cumulative merge audit:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_merge_audit_cumulative.md`
- latest ledger:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv`
- latest summary:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_summary_latest.json`

The cumulative and latest ledger bytes match, and the cumulative and latest
summary bytes match.

## Coverage and identity integrity

- durable rows: 1,828
- terminal rows: 1,828
- unique text-table detection IDs: 1,828
- unique PDF-readiness IDs: 1,828
- unique source-review IDs: 1,828
- unique candidate-queue IDs: 1,828
- duplicate counts for all four identity fields: 0
- exact equality with the durable `parse_text_layer_later` PDF-readiness
  subset: yes
- artifact path/hash/byte size/content type/page count/text-layer mismatches:
  0
- durable parse-text coverage rate: 1.0
- Pilot 1 rows concatenated: 0

## Detection results

- detection status:
  - `detection_checked`: 1,828
- wage-table signal:
  - likely: 1,067
  - possible: 749
  - unlikely: 12
- wage-table confidence:
  - high: 1,067
  - medium: 749
  - low: 12
- contract-period signal:
  - likely: 1,672
  - possible: 103
  - unlikely: 53
- contract-period confidence:
  - high: 1,672
  - medium: 103
  - low: 53
- table-like structure:
  - likely: 1,717
  - possible: 107
  - unlikely: 4
- extraction-pilot priority:
  - p1: 1,067
  - p2: 754
  - p3: 7
- recommended next action:
  - `wage_table_extraction_pilot`: 1,067
  - `larger_text_detection_pass`: 747
  - `contract_period_extraction_pilot`: 7
  - `manual_review`: 7

The full run scanned 17,861 bounded pages, found text on 17,369 scanned pages,
inspected 21,232,318 bounded characters in memory, and retained 7,649 candidate
wage-page hints. Parser metadata are pypdf 6.13.2 with frozen heuristic
`bounded_keyword_numeric_structure_v1`.

## Composition

- source-review rounds:
  - Pilot 1: 127
  - Batch 2: 404
  - Batch 3: 1,297
- content-review priority: p1 1,501; p2 327
- unit type: police 782; fire 439; non-safety 607
- source type:
  - CBA: 1,719
  - wage schedule or compensation plan: 58
  - memorandum or settlement: 20
  - ordinance or policy: 19
  - arbitration award: 10
  - factfinding: 2
- source officialness:
  - official municipal: 648
  - official state repository: 525
  - official union: 42
  - uncertain: 546
  - unknown: 67
- page-count bins:
  - 1–10: 76
  - 11–25: 174
  - 26–50: 846
  - 51–100: 617
  - over 100: 115
- text-layer status: present 1,608; partial 220

## Interpretation and next task

The likely-or-possible wage-table signal rate is 1,816 / 1,828, or 99.3435%.
That result shows high sensitivity, not established precision. Candidate page
numbers are heuristic hints, contract-period text is a bounded redacted hint,
and neither is an analysis-ready wage observation.

The next task should be a manually reviewed calibration subset before any
wage-table extraction pilot. Calibration must measure page-hint precision,
contract-period-hint usefulness, and false-positive patterns across strata.

## Offline and mutation boundaries

During the merge:

- URLs opened / network or API/model calls: 0 / 0
- downloads / redownloads: 0 / 0
- PDF parsing / OCR: 0 / 0
- full-text artifacts written: 0
- final wage values extracted: 0
- ingestion / codify actions: 0 / 0
- wage-gap calculations / regressions: 0 / 0
- scout-accounting mutations: 0
- durable routing / metadata-triage / source-review / PDF-readiness mutations:
  0 / 0 / 0 / 0

The merge created only the durable text/table-detection ledger and status
layer. It did not alter contracts, city coverage, or `corpus/`.
