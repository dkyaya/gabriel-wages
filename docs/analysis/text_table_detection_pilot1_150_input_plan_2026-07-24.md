# Text/Table Detection Pilot 1 Input Plan

Date: 2026-07-24

Pilot: `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24`

## Result

**PASS.** The offline planner locked 150 unique durable
`parse_text_layer_later` rows in three balanced 50-row lanes. It selected no
`ocr_later` row, opened no URL, and opened or parsed no PDF.

The planner command was:

```bash
.venv/bin/python scripts/prepare_text_table_detection_pilot.py \
  --pdf-readiness-ledger-csv docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --triage-ledger-csv docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv \
  --output-dir docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24 \
  --pilot-id TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24 \
  --sample-size 150 \
  --num-lanes 3 \
  --state-diversity \
  --include-partial-text-layer \
  --exclude-ocr-later \
  --plan-only
```

## Locked lanes

| Lane | Rows | Input SHA-256 |
|---|---:|---|
| 1 | 50 | `98d273658e4e51101b97eb19ec783485f6ddf68dfbbc3b07c2a7bb3bd38168d9` |
| 2 | 50 | `f2636a5b80e6e37e28ceccab4bd2d2c4058aecbe2dba37c6181203c20fe2defd` |
| 3 | 50 | `8747e82eced3f76db14cfdebd75a407d20766dd504ef8a2d3f301db9cfc787e0` |

Across the locked inputs:

- detection IDs: 150 unique;
- PDF-readiness IDs: 150 unique;
- source-review IDs: 150 unique;
- candidate-queue IDs: 150 unique;
- nonblank artifact paths: 150;
- nonblank content hashes: 150;
- positive byte sizes: 150;
- represented artifact bytes: 217,728,578;
- represented pages: 7,309; and
- `ocr_later` rows: 0.

## Selection universe

- durable PDF-readiness rows: 2,124;
- default-eligible `parse_text_layer_later` rows: 1,828;
- explicitly excluded `ocr_later` rows: 296; and
- selected rows: 150.

The selection is deterministic and diversity-weighted. It is a diagnostic
sample, not a prevalence-weighted estimate.

## Selected distributions

### PDF-readiness text layer

- `present`: 107
- `partial`: 43

### Metadata priority

- p1: 67
- p2: 83

### Unit type

- police: 51
- fire: 44
- non-safety: 55

### Source-review round

- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 30
- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 35
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 85

### Candidate source type

- CBA: 76
- wage schedule or compensation plan: 28
- memorandum or settlement: 17
- ordinance or policy: 17
- arbitration award: 10
- factfinding: 2

No parse-text-eligible `pay_plan` row was needed to satisfy the locked
selection. Wage schedules, memoranda, ordinances/policies, arbitration
awards, and factfinding documents are represented alongside CBA candidates.

### Preliminary officialness signal

- official municipal: 49
- official state repository: 24
- official union: 18
- uncertain: 43
- unknown: 16

These are inherited preliminary source-review signals, not final
content-supported classifications.

### Page-count bin

- 1-10: 39
- 11-25: 28
- 26-50: 29
- 51-100: 34
- over 100: 20

### State distribution

All 50 states plus DC are represented.

- 5 rows: MT
- 4 rows: DE, GA, KY, MD, MO, WY
- 3 rows: AK, AZ, CA, CO, CT, FL, HI, IA, ID, IL, IN, KS, LA, MA,
  ME, MI, MN, MS, NE, NH, NJ, NM, NV, NY, OH, OK, OR, PA, RI, SD,
  TX, UT, VA, WA, WI
- 2 rows: AL, AR, DC, NC, ND, SC, VT
- 1 row: TN, WV

## Planning boundary

Planning read CSV/JSON metadata only:

- URLs opened: 0;
- network/API/model calls: 0;
- PDFs opened or parsed: 0;
- downloads/redownloads: 0;
- OCR runs: 0;
- full text written: 0;
- final wage values extracted: 0;
- ingestion/codification actions: 0; and
- durable ledger mutations: 0.

The three locked CSVs are the only artifacts authorized for the local pilot.
