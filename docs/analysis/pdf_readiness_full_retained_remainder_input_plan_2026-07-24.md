# Full Retained PDF-Readiness Remainder Input Plan

Date: 2026-07-24

Round: `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`

## Result

**PASS.** The offline planner selected every retained PDF artifact not
already represented in the completed 150-row Pilot 1 readiness outputs.

- retained PDF artifact universe: 2,124;
- Pilot 1 terminal readiness rows excluded: 150;
- selected remainder rows: 1,974;
- Pilot 1 plus remainder coverage: 2,124 / 2,124;
- remainder artifact bytes represented: 4,165,691,340;
- duplicate remainder PDF-readiness IDs: 0;
- duplicate remainder source-review IDs: 0;
- duplicate remainder candidate-queue IDs: 0;
- Pilot 1/remainder source-review overlap: 0; and
- Pilot 1/remainder candidate-queue overlap: 0.

The planner command was:

```bash
.venv/bin/python scripts/prepare_pdf_readiness_pilot.py \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --output-dir docs/analysis/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24 \
  --pilot-id PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24 \
  --all-remaining \
  --num-lanes 4 \
  --balance-lanes \
  --include-prior-batches \
  --exclude-readiness-ledger-csv tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/lane_1_local_attempt1/pdf_readiness_ledger.csv \
  --exclude-readiness-ledger-csv tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/lane_2_local_attempt1/pdf_readiness_ledger.csv \
  --exclude-readiness-ledger-csv tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/lane_3_local_attempt1/pdf_readiness_ledger.csv \
  --plan-only
```

Planning opened zero URLs and zero PDFs. It made no network call, download,
parse, OCR, extraction, ingestion, codify, or durable-ledger mutation.

## Locked lanes

| Lane | Rows | Input SHA-256 |
|---|---:|---|
| 1 | 494 | `299e7effbeae6ed59f1906ea94f6a77245ed4c1e5418cb30abd5ffd82950c23b` |
| 2 | 494 | `8b1460125963214f46d0c9a52d401d9ab9c4d0ff1dcd0287501d2efb5c93aa6d` |
| 3 | 493 | `46cdc9bd67fd56bf1a360d8099ce73e14d758f72cf839a55c8f5056b7b30e05c` |
| 4 | 493 | `40c662efebbed31b6ccce8e5c9fd7ff4d8038a697033a06a76af7fd77065216d` |

Every lane has unique PDF-readiness, source-review, and candidate-queue
identities. Every selected row has a nonblank lane-local artifact path,
nonblank recorded SHA-256, positive byte size, and observed
`application/pdf` content type.

## Remainder distribution

### Source-review round

- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 118
- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 463
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1,393

### Metadata priority

- p1: 1,661
- p2: 313

### Unit type

- police: 862
- fire: 461
- non-safety: 651

### Candidate source type

- CBA: 1,928
- wage schedule or compensation plan: 35
- memorandum or settlement: 6
- ordinance or policy: 5

### Preliminary document type

- `cba_candidate`: 1,928
- `unknown`: 46

### Preliminary officialness signal

- official municipal: 737
- official state repository: 513
- official union: 35
- uncertain: 633
- unknown: 56

### Artifact-size bin

- up to 512 KiB: 341
- 512 KiB to 2 MiB: 980
- 2 MiB to 5 MiB: 463
- over 5 MiB: 190

### State coverage

The complete remainder spans 39 states or state-equivalent jurisdictions:

- AK 11, CA 256, CO 11, CT 33, DC 2, DE 7, FL 115, GA 1;
- IA 29, ID 7, IL 196, IN 7, KS 10, KY 2, MA 70, MD 14;
- ME 21, MI 110, MN 56, MO 13, MT 20, NE 14, NH 20, NJ 25;
- NM 11, NV 19, NY 28, OH 534, OK 13, OR 66, PA 27, RI 10;
- SD 7, TX 36, VA 7, VT 3, WA 102, and WI 61.

These are inherited planning metadata, not substantive relevance or
source-quality determinations.

## Exact full-retained coverage gate

The completed Pilot 1 source-review identity set and the remainder source-
review identity set are disjoint. Their union has exactly 2,124 identities,
equal to the retained-PDF identity set in the cumulative durable
source-review ledger. Candidate-queue identity equality also holds at 2,124.

The remainder is therefore a complete complement, not a second sample.
Running all four locked lanes will produce local technical-readiness outcomes
for the full retained artifact universe while preserving Pilot 1 unchanged.
