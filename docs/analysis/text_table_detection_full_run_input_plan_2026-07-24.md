# Full Text/Table Detection Run Input Plan

Date: 2026-07-25

Run: `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

## Result

**PASS.** The offline planner locked every one of the 1,828 durable
`parse_text_layer_later` rows into four balanced 457-row lanes. It selected
no `ocr_later` row and opened no URL or PDF.

All 150 Pilot 1 PDF-readiness identities are included and will be rerun
under the new full-run text/table-detection namespace. Their Pilot 1 outputs
remain preserved; the new IDs prevent detection-ID collisions while the
PDF-readiness links establish that the full run supersedes those pilot
attempts for a later uniform cumulative merge.

The planner command was:

```bash
.venv/bin/python scripts/prepare_text_table_detection_pilot.py \
  --pdf-readiness-ledger-csv docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --triage-ledger-csv docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv \
  --output-dir docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24 \
  --pilot-id TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24 \
  --all-parse-text \
  --num-lanes 4 \
  --balance-lanes \
  --include-partial-text-layer \
  --exclude-ocr-later \
  --freeze-heuristic-version bounded_keyword_numeric_structure_v1 \
  --plan-only
```

## Locked lanes

| Lane | Rows | Input SHA-256 |
|---|---:|---|
| 1 | 457 | `eaec2dec027f332486199012175d876f284859f33c7c2b67b541a2b8f190a442` |
| 2 | 457 | `dcd1413776de58b3981c5d0625c93de95702aed8739538d6b08c54328e70c0a8` |
| 3 | 457 | `b71af7bbd072193cd2cd4755fba1aa64fd19e2b124dd4a55e11a1985b5ad1a2b` |
| 4 | 457 | `b07b153a7f45510ad5a97bb8df259be8eec357c42fcd5984983951a550f04431` |

Across the locked inputs:

- text/table-detection IDs: 1,828 unique;
- PDF-readiness IDs: 1,828 unique;
- source-review IDs: 1,828 unique;
- candidate-queue IDs: 1,828 unique;
- nonblank artifact paths and hashes: 1,828 / 1,828;
- positive byte sizes and page counts: 1,828 / 1,828;
- represented artifact bytes: 3,646,511,196;
- represented pages: 94,200;
- selected `parse_text_layer_later`: 1,828;
- selected `ocr_later`: 0;
- overlap with the 150-PDF Pilot 1: 150; and
- frozen heuristic: `bounded_keyword_numeric_structure_v1`.

## Full-run distributions

### Text-layer status

- `present`: 1,608
- `partial`: 220

### Metadata priority

- p1: 1,501
- p2: 327

### Unit type

- police: 782
- fire: 439
- non-safety: 607

### Source-review round

- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 127
- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 404
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1,297

### Candidate source type

- CBA: 1,719
- wage schedule or compensation plan: 58
- memorandum or settlement: 20
- ordinance or policy: 19
- arbitration award: 10
- factfinding: 2

### Preliminary officialness

- official municipal: 648
- official state repository: 525
- official union: 42
- uncertain: 546
- unknown: 67

These inherited values remain preliminary source-review signals.

### Page-count bin

- 1–10 pages: 76
- 11–25: 174
- 26–50: 846
- 51–100: 617
- over 100: 115

### State

All 50 states plus DC are represented:

- Ohio 528; California 238; Illinois 131; Florida 102; Washington 95;
  Michigan 94; Oregon 67; Wisconsin 57; Massachusetts 54; Minnesota 50;
- Texas 34; Iowa 29; New York 26; Connecticut 23; Nevada 21; Montana 20;
  Pennsylvania 19; Nebraska 17; New Hampshire 17;
- Alaska 14; New Mexico 14; Oklahoma 14; Colorado 13; Maine 13;
  Missouri 13; Kansas 11; Maryland 11; South Dakota 10; Delaware 9;
  Idaho 9; Virginia 9; Indiana 8; New Jersey 7; Rhode Island 7;
- Kentucky 5; Georgia 4; Wyoming 4; Arizona 3; Hawaii 3; Louisiana 3;
  Mississippi 3; Utah 3;
- Alabama 2; Arkansas 2; DC 2; North Carolina 2; North Dakota 2;
  South Carolina 2; Vermont 2; Tennessee 1; West Virginia 1.

## Exact-coverage and planning boundary

The selected PDF-readiness-ID set exactly equals the full durable
`parse_text_layer_later` set. No duplicate or missing eligible identity
exists. The four full-run detection-ID sets are unique and use the full-run
namespace.

Planning read CSV/JSON metadata only:

- URLs opened: 0;
- network/API/model calls: 0;
- PDFs opened or parsed: 0;
- downloads/redownloads: 0;
- OCR runs: 0;
- complete text written: 0;
- final wage values extracted: 0;
- ingestion/codification actions: 0; and
- durable ledger mutations: 0.

Only the four locked CSV inputs are authorized for the local full run.
