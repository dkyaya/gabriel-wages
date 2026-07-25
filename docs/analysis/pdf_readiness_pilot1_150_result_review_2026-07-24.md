# PDF-Readiness Pilot 1 (150) Result Review

Date: 2026-07-24

## Result

The bounded local readiness pilot completed 150 / 150 terminal rows in three
50-row lanes. All 150 retained artifacts passed local existence, byte-size,
SHA-256, and PDF-signature checks. `pypdf 6.13.2` computed page counts for
all 150 artifacts and encountered zero terminal parser errors.

No URL was opened, no network call or download occurred, OCR did not run,
and no extracted text was saved. The pilot extracted no wage table or wage
value and performed no ingestion or codification.

## Commands

Each lane used:

```bash
.venv/bin/python scripts/pdf_readiness_sources.py \
  --input-csv docs/analysis/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/lane_N_pdf_readiness_input.csv \
  --output-dir tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/lane_N_local_attempt1 \
  --max-pages-to-sample 3 \
  --max-text-chars-per-page 500 \
  --timeout-per-file 20 \
  --no-save-text
```

No full text or page text was written. `text_chars_sampled_total` records
only bounded character counts after discarding extracted strings.

## Terminal and integrity results

### `readiness_status`

- `readiness_checked`: 150

### Integrity and parser failures

- missing artifacts: 0
- hash or size mismatches: 0
- invalid PDF signatures: 0
- terminal parser errors: 0
- per-file timeouts: 0
- duplicate readiness/source-review/candidate identities: 0 / 0 / 0

All three lanes are `completed_merge_eligible`. The structural audit
recommendation is `merge_all_pdf_readiness_lanes`; no durable readiness merge
was run.

## Text-layer results

### `text_layer_status`

- `present`: 107
- `partial`: 19
- `absent`: 24
- `parser_error`: 0
- `unknown`: 0

Of 431 sampled pages, 341 returned at least one non-whitespace character.
The bounded character count is 142,281. This count is a parser diagnostic,
not retained document text and not a wage-content measure.

### `technical_parseability_rating`

- `high`: 107
- `medium`: 19
- `low`: 24
- `not_ready`: 0
- `unknown`: 0

### `recommended_next_action`

- `parse_text_layer_later`: 126
- `ocr_later`: 24

`ocr_later` marks a possible future technical strategy for sampled pages
without text. It does not authorize OCR and does not prove that every page in
those PDFs is image-only.

## Page-count distribution

- PDFs with page count: 150
- minimum: 1
- median: 37.5 (audit integer percentile: 37)
- mean: 47.63
- p90: 98
- maximum: 463
- total pages represented: 7,145

| Page-count bin | PDFs |
|---|---:|
| 1–10 | 40 |
| 11–25 | 21 |
| 26–50 | 30 |
| 51–100 | 45 |
| Over 100 | 14 |

## Text-layer breakdown by sampling dimension

| Dimension | Present | Partial | Absent |
|---|---:|---:|---:|
| Pilot 1 (31) | 21 | 6 | 4 |
| Batch 2 (32) | 23 | 0 | 9 |
| Batch 3 (87) | 63 | 13 | 11 |
| p1 (66) | 47 | 6 | 13 |
| p2 (84) | 60 | 13 | 11 |
| Police (52) | 38 | 3 | 11 |
| Fire (45) | 33 | 7 | 5 |
| Non-safety (53) | 36 | 9 | 8 |
| Official municipal (48) | 31 | 7 | 10 |
| Official state repository (23) | 18 | 4 | 1 |
| Official union (17) | 14 | 1 | 2 |
| Uncertain (44) | 30 | 5 | 9 |
| Unknown officialness (18) | 14 | 2 | 2 |

Candidate source-type results:

- arbitration awards: 9 present, 1 partial, 0 absent;
- CBAs: 53 present, 8 partial, 14 absent;
- factfinding: 2 present, 0 partial, 1 absent;
- memoranda/settlements: 13 present, 1 partial, 3 absent;
- ordinances/policies: 11 present, 3 partial, 1 absent;
- pay plan: 0 present, 0 partial, 1 absent; and
- wage schedules/compensation plans: 19 present, 6 partial, 4 absent.

Because the pilot intentionally over-samples rare states, source types,
officialness groups, p2 rows, and prior rounds, these distributions are
technical diagnostics rather than prevalence estimates for the full retained
corpus.

## Runtime

- Lane 1: 2.112 seconds
- Lane 2: 2.013 seconds
- Lane 3: 4.400 seconds
- Aggregate lane runtime: 8.525 seconds
- Average processing rate: approximately 17.6 artifacts per aggregate lane
  second

Runtime includes local hashing of 334,676,242 selected bytes, page-tree
opening, and bounded sampled-page extraction. The three lanes were run
serially in this task.

## Interpretation and recommendation

The selected retained PDFs appear broadly amenable to local text-layer
parsing:

- 126 / 150 have text on at least one sampled page;
- all 150 yield page counts;
- no artifact, hash, signature, or terminal parser failure occurred; and
- bounded local checks are inexpensive relative to downloading more data.

The strongest next step is a **larger local text-layer/page-count pass over
all 2,124 retained PDFs**, using the same no-text-retention and no-OCR
boundaries. That pass would produce population-wide technical readiness,
identify the text-layer-absent subset precisely, and support a better design
for later content review.

Do not move directly from this pilot to wage-table extraction. Text-layer
presence does not prove that a PDF is the intended CBA, matches the employer
or bargaining unit, contains wage tables, or is substantively relevant.
After a larger readiness pass and content/identity gates, a small bounded
wage-table extraction pilot may be designed separately. Finishing the
remaining p2 downloads is secondary because the current retained pool is
large and technically promising.

## Explicit boundary

- URLs opened: 0
- network/API/model calls: 0
- downloads/redownloads: 0
- OCR runs: 0
- full extracted text files: 0
- wage tables/values extracted: 0 / 0
- ingestion/codify actions: 0 / 0
- durable readiness merge: not run
- scout, routing, triage, and source-review ledger mutations: 0
- wage-gap calculations, causal claims, and regressions: 0
