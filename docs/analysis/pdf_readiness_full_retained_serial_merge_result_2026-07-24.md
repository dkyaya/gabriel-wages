# Full Retained PDF-Readiness Serial Merge Result

Date: 2026-07-24

Merge ID: `PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`

## Result

**PASS.** One serial offline merge combined exactly the 150 completed Pilot
1 rows and the 1,974 completed full-remainder rows. The durable cumulative
PDF-readiness ledger contains 2,124 terminal, unique rows and is exactly
equal to the retained-PDF subset of the cumulative source-review ledger.

No URL or retained PDF was opened during the merge. No network call,
download, redownload, PDF parse, OCR, extracted-text output, wage
extraction, ingestion, or codification occurred.

## Merge command

The merge script was executed exactly once:

```bash
.venv/bin/python scripts/merge_pdf_readiness_lanes.py \
  --manifest docs/analysis/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/pdf_readiness_pilot_manifest.json \
  --manifest docs/analysis/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/pdf_readiness_pilot_manifest.json \
  --audit-summary tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/cumulative_merge_readiness_audit_2026-07-24/pdf_readiness_lane_audit_summary.json \
  --audit-summary tmp/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/cumulative_merge_readiness_audit_2026-07-24/pdf_readiness_lane_audit_summary.json \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --output-dir docs/analysis/pdf_readiness_ledgers \
  --merge-id PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24
```

The tool validated every gate before atomically renaming a staging directory
into the previously absent durable target. It will fail closed if the target
directory already exists.

## Durable outputs

- cumulative ledger:
  `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`;
- cumulative summary:
  `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_cumulative.json`;
- cumulative merge audit:
  `docs/analysis/pdf_readiness_ledgers/pdf_readiness_merge_audit_cumulative.md`;
- latest ledger:
  `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv`; and
- latest summary:
  `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_latest.json`.

The cumulative and latest ledger files are byte-identical. The cumulative
and latest summary files are also byte-identical.

Every row records:

- `pdf_readiness_merge_id =
  PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`;
- one UTC `pdf_readiness_merged_at` timestamp; and
- `pdf_readiness_stage =
  technical_readiness_checked_not_extracted`.

## Coverage and exact equality

- total cumulative source-review rows: 2,150;
- retained-PDF source-review rows: 2,124;
- Pilot 1 rows merged: 150;
- remainder rows merged: 1,974;
- durable readiness rows: 2,124;
- retained-PDF readiness coverage: 100%;
- unique PDF-readiness IDs: 2,124;
- unique source-review IDs: 2,124;
- unique candidate-queue IDs: 2,124;
- duplicate readiness/source-review/candidate identities: 0 / 0 / 0;
- exact retained source-review-ID equality: yes;
- exact retained candidate-queue-ID equality: yes; and
- inherited identity, path, hash, size, content type, and source metadata
  mismatches: 0.

The merge compared readiness rows to retained source-review rows with status
`reviewed_metadata_and_artifact_saved`, observed `application/pdf`,
nonblank artifact path and hash, and positive byte size. It did not open the
artifact paths.

## Technical-readiness distributions

### Readiness status

- `readiness_checked`: 2,124

### Text layer

- `present`: 1,608
- `partial`: 220
- `absent`: 296

Thus 1,828 / 2,124, or approximately 86.1%, have text on at least one
bounded sampled page. The remaining 296 have no text on the sampled pages;
that does not prove every page is image-only.

### Technical parseability

- `high`: 1,608
- `medium`: 220
- `low`: 296

### Recommended technical next action

- `parse_text_layer_later`: 1,828
- `ocr_later`: 296

`ocr_later` is a planning category only. OCR has not run and is not
authorized by this merge.

## Page-count summary

- page counts: 2,124 / 2,124;
- minimum: 1;
- median: 44;
- mean: 50.860640;
- p90: 84;
- maximum: 463;
- total pages represented: 108,028;
- pages sampled in the prior local collections: 6,322;
- sampled pages with text: 5,201; and
- bounded character count: 1,997,021, with no text retained.

| Page-count band | PDFs |
|---|---:|
| 1-10 | 86 |
| 11-25 | 215 |
| 26-50 | 990 |
| 51-100 | 701 |
| Over 100 | 132 |

## Source-review and planning distributions

### Source-review round

- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 149
- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 495
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1,480

### Metadata priority

- p1: 1,727
- p2: 397

### Unit type

- police: 914
- fire: 506
- non-safety: 704

### Candidate source type

- CBA: 2,003
- wage schedule or compensation plan: 64
- memorandum or settlement: 23
- ordinance or policy: 20
- arbitration award: 10
- factfinding: 3
- pay plan: 1

### Preliminary officialness signal

- official municipal: 785
- official state repository: 536
- official union: 52
- uncertain: 677
- unknown: 74

The durable layer spans all 50 states plus DC. These dimensions are inherited
metadata and preliminary source-review signals, not content-supported
officialness, relevance, employer-match, unit-match, or wage findings.

## Integrity, parser, and activity counters

- content artifact bytes represented: 4,500,367,582;
- missing artifacts: 0;
- hash failures: 0;
- invalid PDF signatures: 0;
- terminal parser errors: 0;
- parser: `pypdf 6.13.2` for 2,124 rows;
- URLs opened: 0;
- network calls: 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- full extracted-text artifacts: 0;
- wage tables/values extracted: 0 / 0;
- ingestion/codify actions: 0 / 0;
- scout-accounting mutations: 0;
- routing-ledger mutations: 0;
- metadata-triage-ledger mutations: 0; and
- source-review-ledger mutations: 0.

## Technical interpretation

The retained PDF corpus is broadly amenable to later bounded text-layer
processing: every artifact has a page count, 86.1% have sampled text, and no
artifact failed the prior integrity or terminal parser gates.

This does **not** show that 86.1% contain wage tables, that the files are the
intended agreements, or that employer, bargaining unit, contract period,
source relevance, or wage content is confirmed. The durable result remains a
technical-readiness layer, not extracted, ingested, codified, or
analysis-ready evidence.

## Recommended next task

Plan a bounded 100-200 PDF text-layer content-structure and table-detection
pilot from the 1,828 `parse_text_layer_later` rows. The pilot should preserve
source-identity and substantive-relevance gates and should not yet extract
wage values across the retained corpus.

Do not automatically OCR the 296 no-sampled-text rows, resume broad scouting,
or download the remaining p2 sources before the text-layer/table-detection
yield is known.
