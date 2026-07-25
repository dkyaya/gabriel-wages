# Full Text/Table Detection Run Result Review

Date: 2026-07-25

Run: `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

## Result

**PASS for collection and later serial merge.** The frozen bounded local
detector produced terminal results for all 1,828 durable
`parse_text_layer_later` PDFs. All four 457-row lanes are
`completed_merge_eligible`, and the audit recommends
`merge_all_text_table_detection_lanes`.

This recommendation means the lane-local outputs are structurally ready for
a separate serial merge. No durable text/table-detection merge occurred in
this task.

## Frozen method and commands

The run used the same `bounded_keyword_numeric_structure_v1` heuristic and
`pypdf 6.13.2` parser as Pilot 1. Each lane ran:

```bash
.venv/bin/python scripts/text_table_detection_sources.py \
  --input-csv <locked-lane-input.csv> \
  --output-dir <lane-local-attempt1-directory> \
  --max-pages-to-scan 10 \
  --max-text-chars-per-page 1500 \
  --timeout-per-file 30 \
  --no-save-text
```

The runner inspected bounded page text in memory and retained only page
numbers, counts, categorical signals, generic notes, and at most 300
characters of redacted contract-period hints per document. It retained no
table cells, complete page text, complete document text, or final wage
values.

## Lane completion and runtime

| Lane | Rows | Terminal | Pages scanned | Pages with text | Runtime | Input SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| 1 | 457 | 457 | 4,459 | 4,348 | 84.726 s | `eaec2dec027f332486199012175d876f284859f33c7c2b67b541a2b8f190a442` |
| 2 | 457 | 457 | 4,479 | 4,362 | 75.676 s | `dcd1413776de58b3981c5d0625c93de95702aed8739538d6b08c54328e70c0a8` |
| 3 | 457 | 457 | 4,467 | 4,335 | 81.142 s | `b71af7bbd072193cd2cd4755fba1aa64fd19e2b124dd4a55e11a1985b5ad1a2b` |
| 4 | 457 | 457 | 4,456 | 4,324 | 84.003 s | `b07b153a7f45510ad5a97bb8df259be8eec357c42fcd5984983951a550f04431` |

- aggregate lane runtime: 325.546 seconds;
- parallel wall-clock proxy: 84.726 seconds; and
- combined throughput by wall-clock proxy: approximately 77,672 rows/hour.

`pypdf` emitted repair warnings for malformed object pointers in some
already-retained PDFs, particularly one large Lane 2 artifact. The parser
recovered. No document ended in `parser_error`.

## Terminal and integrity results

- planned rows: 1,828;
- ledger rows: 1,828;
- terminal rows: 1,828;
- `detection_checked`: 1,828;
- duplicate detection, readiness, source-review, or candidate IDs: 0;
- hash mismatches: 0;
- missing artifacts: 0;
- parser errors: 0;
- invalid candidate-page hints: 0;
- hint-length overruns: 0;
- heuristic-version mismatches: 0; and
- complete-text artifacts: 0.

## Detection signals

### Wage-table signal

| Signal | Rows | Rate | Confidence |
|---|---:|---:|---|
| likely | 1,067 | 58.37% | high: 1,067 |
| possible | 749 | 40.97% | medium: 749 |
| unlikely | 12 | 0.66% | low: 12 |

The runner retained 7,649 candidate wage-page hints. They are one-based page
numbers, not extracted tables or wage observations.

### Contract-period signal

| Signal | Rows | Rate | Confidence |
|---|---:|---:|---|
| likely | 1,672 | 91.47% | high: 1,672 |
| possible | 103 | 5.63% | medium: 103 |
| unlikely | 53 | 2.90% | low: 53 |

Contract-period hints were capped at 300 characters per document. The
post-run scan found zero retained currency, comma-delimited salary,
percentage, or salary-like patterns in the bounded hints.

### Table-like structure

- `likely`: 1,717 (93.93%);
- `possible`: 107 (5.85%);
- `unlikely`: 4 (0.22%); and
- `unknown`: 0.

The detector counts aligned whitespace, repeated numeric rows, numeric-token
density, and pay/schedule terms. It does not reconstruct a table.

### Extraction-pilot priority

- p1: 1,067;
- p2: 754;
- p3: 7;
- defer: 0; and
- exclude: 0.

These are downstream scheduling signals only. They do not replace metadata
priority and do not establish document relevance or a wage observation.

### Recommended next action

- `wage_table_extraction_pilot`: 1,067;
- `larger_text_detection_pass`: 747;
- `contract_period_extraction_pilot`: 7; and
- `manual_review`: 7.

No recommendation authorizes final wage extraction, ingestion,
codification, or OCR by itself.

## Bounded-content totals

- pages scanned: 17,861;
- pages returning text: 17,369;
- bounded text characters inspected in memory: 21,232,318;
- candidate wage-page hints: 7,649;
- maximum retained contract-period hint: 300 characters;
- full page/document text files written: 0; and
- table cells or final wage values retained: 0.

## Coverage and signal breakdown

### Source-review round

- Pilot 1: 127;
- Batch 2: 404; and
- Batch 3: 1,297.

### Metadata priority

- p1: 1,501 — likely 857, possible 636, unlikely 8;
- p2: 327 — likely 210, possible 113, unlikely 4.

### Unit type

- police: 782 — likely 432, possible 345, unlikely 5;
- fire: 439 — likely 267, possible 168, unlikely 4;
- non-safety: 607 — likely 368, possible 236, unlikely 3.

### Candidate source type

| Source type | Rows | Likely | Possible | Unlikely |
|---|---:|---:|---:|---:|
| CBA | 1,719 | 988 | 720 | 11 |
| Wage schedule / compensation plan | 58 | 47 | 11 | 0 |
| Memorandum / settlement | 20 | 12 | 8 | 0 |
| Ordinance / policy | 19 | 13 | 6 | 0 |
| Arbitration award | 10 | 5 | 4 | 1 |
| Factfinding | 2 | 2 | 0 | 0 |

### Preliminary source officialness

| Officialness signal | Rows | Likely | Possible | Unlikely |
|---|---:|---:|---:|---:|
| Official municipal | 648 | 431 | 211 | 6 |
| Official state repository | 525 | 246 | 278 | 1 |
| Official union | 42 | 28 | 13 | 1 |
| Uncertain | 546 | 326 | 216 | 4 |
| Unknown | 67 | 36 | 31 | 0 |

These inherited ratings remain preliminary source-review signals.

### Page-count bin

| Page bin | Rows | Likely | Possible | Unlikely |
|---|---:|---:|---:|---:|
| 1–10 | 76 | 57 | 17 | 2 |
| 11–25 | 174 | 119 | 53 | 2 |
| 26–50 | 846 | 491 | 351 | 4 |
| 51–100 | 617 | 345 | 268 | 4 |
| Over 100 | 115 | 55 | 60 | 0 |

All 50 states plus DC are represented.

## Comparison with Pilot 1

Pilot 1 yielded 94 likely, 55 possible, and one unlikely wage-table signal
among 150 rows. The full run yielded 1,067 likely, 749 possible, and 12
unlikely signals among 1,828 rows. Likely-or-possible rates were therefore
99.33% in Pilot 1 and 99.34% in the full run.

All 150 Pilot 1 readiness identities were rerun under new full-run detection
IDs. An exact field comparison found zero mismatches across terminal status,
pages scanned, wage/contract/table signals and confidences, candidate-page
hints, bounded contract snippets, table method, extraction priority,
recommended action, and notes. The frozen heuristic is reproducible on the
overlap.

## Interpretation and calibration warning

The local detector is technically reliable within its bounds: every eligible
artifact produced a terminal result, hashes matched, and the Pilot 1 overlap
reproduced exactly. The near-universal likely-or-possible rate is not evidence
that nearly every PDF contains a usable wage table. The corpus is heavily
weighted toward CBAs and compensation materials, but the heuristic is also
deliberately sensitive. Its precision and false-negative behavior require
manual review before final wage extraction.

## Recommendation

Run a separate serial durable merge of these four full-run lanes if the relay
review accepts the audit. Because the full run reran every Pilot 1 identity
under the same frozen heuristic, treat the full-run rows as the uniform
cumulative result and preserve Pilot 1 as superseded diagnostic provenance.

After the merge, manually calibrate a stratified subset of likely, possible,
and unlikely page hints before designing any wage-table extraction pilot.
Do not proceed directly from heuristic signals to final wage values.

## Prohibited-activity confirmation

- URLs opened: 0;
- network/API/model calls: 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- full text artifacts: 0;
- final wage values extracted: 0;
- ingestion actions: 0;
- codify actions: 0;
- scout queue/coverage accounting updates: 0;
- routing, metadata-triage, source-review, or PDF-readiness ledger mutations: 0;
- durable text/table-detection merges: 0; and
- wage-gap calculations, causal claims, and regressions: 0.
