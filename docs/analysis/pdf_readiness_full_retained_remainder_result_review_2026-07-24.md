# Full Retained PDF-Readiness Remainder Result Review

Date: 2026-07-24

Round: `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`

## Result

The bounded local readiness pass completed 1,974 / 1,974 terminal remainder
rows in four lanes. Together with the preserved 150-row Pilot 1, local
technical-readiness coverage is now exactly 2,124 / 2,124 retained PDFs.

All remainder artifacts passed local existence, byte-size, SHA-256, and PDF-
signature checks. `pypdf 6.13.2` computed page counts for all 1,974
remainder artifacts and encountered zero terminal parser errors.

No URL was opened, no network call or download occurred, OCR did not run,
and no extracted text was saved. The pass extracted no wage table or wage
value and performed no ingestion or codification. No durable PDF-readiness
merge was run.

## Local commands

Each locked remainder lane used:

```bash
.venv/bin/python scripts/pdf_readiness_sources.py \
  --input-csv docs/analysis/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/lane_N_pdf_readiness_input.csv \
  --output-dir tmp/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/lane_N_local_attempt1 \
  --max-pages-to-sample 3 \
  --max-text-chars-per-page 500 \
  --timeout-per-file 20 \
  --no-save-text
```

The runner retained only counts, statuses, parser metadata, and sanitized
error categories. Page strings were discarded and no full or sampled text
was written.

## Remainder lane results

| Lane | Rows | Classification | Present | Partial | Absent |
|---|---:|---|---:|---:|---:|
| 1 | 494 | `completed_merge_eligible` | 379 | 53 | 62 |
| 2 | 494 | `completed_merge_eligible` | 367 | 54 | 73 |
| 3 | 493 | `completed_merge_eligible` | 369 | 53 | 71 |
| 4 | 493 | `completed_merge_eligible` | 386 | 41 | 66 |
| **Total** | **1,974** | four complete lanes | **1,501** | **201** | **272** |

The structural audit recommendation is
`merge_all_pdf_readiness_lanes`. This is a mergeability finding only; no
durable merge occurred.

## Remainder readiness outcomes

### `readiness_status`

- `readiness_checked`: 1,974

### `text_layer_status`

- `present`: 1,501
- `partial`: 201
- `absent`: 272
- `parser_error`: 0
- `unknown`: 0

Of 5,891 sampled pages, 4,860 returned at least one non-whitespace character.
The bounded character count is 1,854,740. This count is a parser diagnostic;
the characters themselves were discarded.

### `technical_parseability_rating`

- `high`: 1,501
- `medium`: 201
- `low`: 272
- `not_ready`: 0
- `unknown`: 0

### `recommended_next_action`

- `parse_text_layer_later`: 1,702
- `ocr_later`: 272

`ocr_later` is a future technical category only. OCR did not run, and
sampled-page absence does not prove every page is image-only.

## Remainder page-count distribution

- PDFs with page count: 1,974
- minimum: 1
- median: 45
- mean: 51.11
- p90: 84
- maximum: 284
- total pages represented: 100,883

| Page-count bin | PDFs |
|---|---:|
| 1–10 | 46 |
| 11–25 | 194 |
| 26–50 | 960 |
| 51–100 | 656 |
| Over 100 | 118 |

## Remainder integrity and parser failures

- missing artifacts: 0
- hash or size mismatches: 0
- invalid PDF signatures: 0
- terminal parser errors: 0
- per-file timeout outcomes: 0
- duplicate readiness/source-review/candidate identities: 0 / 0 / 0

`pypdf` emitted repair warnings for malformed cross-reference pointers in
some retained files. Those warnings did not prevent a terminal result, page
count, or bounded sampled-page classification for any row. They should be
preserved as a reason to retain parser/version provenance and to keep later
content extraction bounded.

## Remainder runtime

- Lane 1: 23.301 seconds
- Lane 2: 24.779 seconds
- Lane 3: 23.559 seconds
- Lane 4: 24.430 seconds
- aggregate lane runtime: 96.069 seconds
- approximate aggregate rate: 20.5 artifacts per aggregate lane second

Runtime includes hashing 4,165,691,340 bytes, opening page trees, bounded
sampled-page extraction, and checkpoint writing. The four lanes were run
serially.

## Remainder text-layer breakdown

### Source-review round

| Round | Present | Partial | Absent | Total |
|---|---:|---:|---:|---:|
| Pilot 1 source-review artifacts not in readiness Pilot 1 | 82 | 18 | 18 | 118 |
| Source Review Batch 2 | 318 | 63 | 82 | 463 |
| Source Review Batch 3 | 1,101 | 120 | 172 | 1,393 |

### Metadata priority

| Priority | Present | Partial | Absent | Total |
|---|---:|---:|---:|---:|
| p1 | 1,280 | 168 | 213 | 1,661 |
| p2 | 221 | 33 | 59 | 313 |

### Unit type

| Unit type | Present | Partial | Absent | Total |
|---|---:|---:|---:|---:|
| Police | 654 | 87 | 121 | 862 |
| Fire | 353 | 46 | 62 | 461 |
| Non-safety | 494 | 68 | 89 | 651 |

### Preliminary officialness

| Signal | Present | Partial | Absent | Total |
|---|---:|---:|---:|---:|
| Official municipal | 514 | 96 | 127 | 737 |
| Official state repository | 471 | 32 | 10 | 513 |
| Official union | 24 | 3 | 8 | 35 |
| Uncertain | 446 | 65 | 122 | 633 |
| Unknown | 46 | 5 | 5 | 56 |

### Candidate source type

| Source type | Present | Partial | Absent | Total |
|---|---:|---:|---:|---:|
| CBA | 1,459 | 199 | 270 | 1,928 |
| Wage schedule or compensation plan | 31 | 2 | 2 | 35 |
| Memorandum or settlement | 6 | 0 | 0 | 6 |
| Ordinance or policy | 5 | 0 | 0 | 5 |

These breakdowns describe technical parser outcomes. They do not establish
source officialness, document identity, bargaining-unit match, relevance, or
wage content.

## Combined Pilot 1 plus remainder

The two collected, unmerged readiness rounds are disjoint by source-review
and candidate-queue identity and together equal the retained-PDF identity
universe.

### Coverage

- retained PDFs: 2,124
- readiness-checked retained PDFs: 2,124
- technical-readiness coverage: 100%
- page counts obtained: 2,124
- parser/hash/missing/signature failures: 0 / 0 / 0 / 0

### Cumulative text-layer status

- `present`: 1,608
- `partial`: 220
- `absent`: 296

Thus 1,828 / 2,124 retained PDFs, or approximately 86.1%, have text on at
least one bounded sampled page. The remaining 296, approximately 13.9%, have
no text on the sampled pages.

### Cumulative technical parseability

- `high`: 1,608
- `medium`: 220
- `low`: 296

### Cumulative recommended next action

- `parse_text_layer_later`: 1,828
- `ocr_later`: 296

### Cumulative page-count distribution

- count: 2,124
- minimum: 1
- median: 44
- mean: 50.86
- p90: 84
- maximum: 463
- total pages represented: 108,028

| Page-count bin | PDFs |
|---|---:|
| 1–10 | 86 |
| 11–25 | 215 |
| 26–50 | 990 |
| 51–100 | 701 |
| Over 100 | 132 |

Across both rounds, 6,322 pages were sampled; 5,201 returned text. The
bounded character count is 1,997,021, with no text retained. Aggregate lane
runtime across the seven Pilot 1 and remainder lanes is 104.594 seconds.

## Interpretation and recommendation

The retained PDF universe is broadly amenable to local text-layer parsing:

- every retained PDF yields a page count;
- 86.1% have text on at least one sampled page;
- no file failed integrity or terminal parser gates; and
- the complete 4.50 GB retained population can be technically classified
  locally in under two aggregate lane minutes.

The next action should be a **single cumulative serial PDF-readiness merge**
of Pilot 1 plus the complete remainder, after relay review and separate
authorization. That merge should establish exact 2,124-row equality with the
retained-PDF subset of the durable source-review ledger.

After the cumulative merge:

1. design a bounded content/identity and structured-text evaluation over a
   representative subset of the 1,828 text-bearing PDFs;
2. evaluate table-detection methods without extracting or publishing wage
   values until source identity and relevance are confirmed; and
3. plan the 296-row no-sampled-text subset separately. Do not run OCR
   automatically.

More bulk downloading is not the immediate bottleneck. The project already
has complete technical readiness for the retained corpus. Text-layer
presence still does not prove that a PDF is the intended agreement, contains
a wage table, or supports analysis-ready evidence.

## Explicit boundary

- URLs opened: 0
- network/API/model calls: 0
- downloads/redownloads: 0
- OCR runs: 0
- full extracted-text files: 0
- wage tables/values extracted: 0 / 0
- ingestion/codify actions: 0 / 0
- durable readiness merges: 0
- scout, routing, triage, and source-review-ledger mutations: 0
- wage-gap calculations, causal claims, and regressions: 0
