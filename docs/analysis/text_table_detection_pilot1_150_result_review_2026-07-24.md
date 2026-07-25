# Text/Table Detection Pilot 1 Result Review

Date: 2026-07-24

Pilot: `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24`

## Result

**PASS for bounded local table detection.** All 150 locked retained PDFs
received terminal local detection results. Every artifact hash and size
matched, no parser failed, all three lanes are `completed_merge_eligible`,
and the auditor recommends `merge_all_text_table_detection_lanes`.

The recommendation means the lane outputs are structurally mergeable. No
durable text/table-detection merge occurred in this task.

The pilot supports preparing a full local detection pass over the 1,828
`parse_text_layer_later` PDFs. The high heuristic signal rate also requires
manual calibration before any final wage-table or wage-value extraction.

## Commands and bounded settings

Each lane ran:

```bash
.venv/bin/python scripts/text_table_detection_sources.py \
  --input-csv <locked-lane-input.csv> \
  --output-dir <lane-local-attempt1-directory> \
  --max-pages-to-scan 10 \
  --max-text-chars-per-page 1500 \
  --timeout-per-file 30 \
  --no-save-text
```

The runner used `pypdf 6.13.2` and the deterministic
`bounded_keyword_numeric_structure_v1` heuristic. It scanned only
deterministic first, middle, last, and evenly distributed pages, counted
terms/numeric structure in memory, and discarded page text immediately.

It retained only:

- signal and confidence categories;
- one-based candidate page numbers;
- counts;
- generic notes; and
- at most 300 characters of currency/percentage-redacted contract-period
  text per document.

It retained no table cells, complete page text, document text, or final wage
values.

## Lane completion

| Lane | Rows | Terminal | Pages scanned | Pages with text | Runtime |
|---|---:|---:|---:|---:|---:|
| 1 | 50 | 50 | 421 | 392 | 8.821 s |
| 2 | 50 | 50 | 443 | 416 | 7.029 s |
| 3 | 50 | 50 | 431 | 395 | 6.630 s |

- aggregate lane runtime: 22.481 seconds;
- parallel wall-clock proxy: 8.821 seconds;
- combined throughput by wall proxy: approximately 61,216 rows/hour; and
- terminal rows: 150 / 150.

Lane 3 emitted `pypdf` repair warnings for several malformed object
pointers. The parser recovered; all affected documents still produced
terminal detection results and the terminal parser-error count is zero.

## Detection status

- `detection_checked`: 150
- `no_text_available`: 0
- `parser_error`: 0
- `artifact_missing`: 0
- `hash_mismatch`: 0
- other terminal errors/skips: 0

## Wage-table signals

| Signal | Rows | Confidence |
|---|---:|---|
| likely | 94 | high: 94 |
| possible | 55 | medium: 55 |
| unlikely | 1 | low: 1 |
| unknown | 0 | unknown: 0 |

The runner produced 599 candidate wage-page hints. These are page numbers,
not extracted tables or wage observations.

By candidate source type:

| Source type | Likely | Possible | Unlikely |
|---|---:|---:|---:|
| CBA | 45 | 31 | 0 |
| Wage schedule/compensation plan | 21 | 7 | 0 |
| Memorandum/settlement | 10 | 7 | 0 |
| Ordinance/policy | 11 | 6 | 0 |
| Arbitration award | 5 | 4 | 1 |
| Factfinding | 2 | 0 | 0 |

The 149/150 likely-or-possible rate is plausible in a source universe
dominated by CBAs and compensation documents, but it also shows that the
heuristic is deliberately sensitive. These signals must be manually
calibrated for precision before final wage-table extraction.

## Contract-period signals

| Signal | Rows | Confidence |
|---|---:|---|
| likely | 112 | high: 112 |
| possible | 20 | medium: 20 |
| unlikely | 18 | low: 18 |
| unknown | 0 | unknown: 0 |

Contract hints were limited to 300 characters. A post-run safety scan found
zero currency, comma-delimited salary, or percentage patterns in those
hints. Dates and years may remain because the field is specifically a
contract-period hint.

## Table-like structure

- `likely`: 135
- `possible`: 14
- `unlikely`: 1
- `unknown`: 0

The heuristic uses aligned text rows, numeric-token density, repeated
numeric rows, and pay/schedule terms. It does not reconstruct a table.

## Extraction-pilot priority

- p1: 94
- p2: 54
- p3: 2
- defer: 0
- exclude: 0

These are scheduling signals for later review. They do not replace metadata
priority and do not establish document relevance or a wage observation.

## Recommended next action

- `wage_table_extraction_pilot`: 94
- `larger_text_detection_pass`: 54
- `manual_review`: 2
- `contract_period_extraction_pilot`: 0
- `ocr_later`: 0
- `exclude_for_now`: 0

No recommendation authorizes extraction, OCR, ingestion, or codification by
itself.

## Bounded content totals

- pages scanned: 1,295;
- pages returning text: 1,203;
- bounded text characters inspected in memory: 1,499,904;
- complete page/document text artifacts written: 0;
- maximum retained contract-period hint: 300 characters;
- contract-hint money/percentage pattern violations: 0; and
- candidate page-number validity errors: 0.

## Sample coverage

### Source-review round

- Pilot 1: 30
- Batch 2: 35
- Batch 3: 85

### Metadata priority

- p1: 67
- p2: 83

### Unit type

- police: 51
- fire: 44
- non-safety: 55

### Text-layer status

- present: 107
- partial: 43

### Officialness signal

- official municipal: 49
- official state repository: 24
- official union: 18
- uncertain: 43
- unknown: 16

### Page-count bin

- 1-10: 39
- 11-25: 28
- 26-50: 29
- 51-100: 34
- over 100: 20

All 50 states plus DC are represented. These sample dimensions are
diagnostic coverage, not population weights.

## Interpretation

Bounded local text-layer and structure detection is technically useful:

- 150/150 retained PDFs were readable within the configured bounds;
- 1,203/1,295 scanned pages returned text;
- candidate wage-table pages and contract-period hints can be generated
  without saving page text or final wage values; and
- runtime is small relative to the retained corpus.

The pilot does not validate heuristic precision. A likely signal does not
prove the page contains a wage table, the intended contract, or the intended
unit. The page hints should support a later calibrated extraction pilot, not
be treated as extracted evidence.

## Recommendation

Prepare a full local text/table-detection run over all 1,828 durable
`parse_text_layer_later` PDFs, using the same hard caps and no-full-text
rule. Use four balanced lanes by default. Preserve the 150 pilot rows in the
full cumulative pass or rerun all 1,828 under the frozen heuristic version,
then stop before a durable merge.

Before final wage-table extraction, manually review a small stratified set
of likely, possible, and unlikely page hints to estimate false-positive and
false-negative rates and refine the extraction schema.

## Prohibited-activity confirmation

- URLs opened: 0;
- network/API/model calls: 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- full text artifacts: 0;
- final wage values extracted: 0;
- ingestion/codification actions: 0 / 0;
- durable text/table-detection merges: 0;
- scout/routing/triage/source-review/PDF-readiness mutations: 0; and
- wage-gap calculations, causal claims, and regressions: 0.
