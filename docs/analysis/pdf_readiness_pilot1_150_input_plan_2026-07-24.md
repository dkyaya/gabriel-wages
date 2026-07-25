# PDF-Readiness Pilot 1 (150) Input Plan

Date: 2026-07-24

## Result

**PASS.** The deterministic offline planner locked 150 unique, already-
retained PDFs from the 2,124-artifact durable source-review pool. The three
lanes are balanced at 50 / 50 / 50 rows.

The planner command was:

```bash
.venv/bin/python scripts/prepare_pdf_readiness_pilot.py \
  --source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --output-dir docs/analysis/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24 \
  --pilot-id PDF-READINESS-PILOT1-150-2026-07-24 \
  --sample-size 150 \
  --num-lanes 3 \
  --state-diversity \
  --include-prior-batches \
  --plan-only
```

Planning opened zero URLs and zero PDFs. It made no network call, download,
parse, OCR, extraction, ingestion, codify, or durable-ledger mutation.

## Locked lanes

| Lane | Rows | Input SHA-256 |
|---|---:|---|
| 1 | 50 | `3d04c40eb0b150fb618944b01790dc33ac44d2143ea0176b05e5e75153f2aaca` |
| 2 | 50 | `aebf88b78d45e326da1eba60bc0fd0d98d1de784b66375d5dcbbfb9e977bed89` |
| 3 | 50 | `ee7c0f779d8e43c0826cc6db94cd69e57a24046f733e27fa1672d09836e5a124` |

All 150 rows have unique `pdf_readiness_id`, `source_review_id`, and
`candidate_queue_row_id` values. All have nonblank local artifact paths,
SHA-256 hashes, positive recorded sizes, and observed
`application/pdf` content type. Selected recorded artifact bytes total
334,676,242.

## Sampling design

The sample is deliberately **diagnostic and diversity-weighted**, not a
prevalence-weighted estimate of all 2,124 retained PDFs. The planner first
covers observed categories and then fills underrepresented cells
deterministically. This is appropriate for discovering parser and text-layer
failure modes but raw percentages should not be projected to the full
artifact population without weighting or a larger representative pass.

### Source-review round

- Pilot 1: 31
- Batch 2: 32
- Batch 3: 87

### Metadata priority

- p1: 66
- p2: 84

### Unit type

- police: 52
- fire: 45
- non-safety: 53

### State coverage

All 50 states plus DC are represented.

- four rows each: MT, TN, WY;
- two rows each: AL, AR, NC, ND, SC, WV; and
- three rows each: the remaining 42 states plus DC.

### Preliminary officialness signal

- official municipal: 48
- official state repository: 23
- official union: 17
- uncertain: 44
- unknown: 18

### Candidate source type

- CBA: 75
- wage schedule or compensation plan: 29
- memorandum or settlement: 17
- ordinance or policy: 15
- arbitration award: 10
- factfinding: 3
- pay plan: 1

### Preliminary document type

- `cba_candidate`: 75
- `unknown`: 75

### Artifact-size bin

- up to 512 KiB: 49
- 512 KiB to 2 MiB: 45
- 2 MiB to 5 MiB: 29
- over 5 MiB: 27

## Dry-run gate

All three dry-run lanes passed:

- terminal planned rows: 150 / 150;
- lane classifications: three `dry_run_passed`;
- readiness status: 150 `planned_not_checked`;
- local artifacts opened: 0;
- URLs/network/downloads: 0 / 0 / 0;
- OCR runs: 0;
- full-text artifacts: 0; and
- recommendation:
  `dry_run_complete_no_local_readiness_merge`.

The local readiness lanes were authorized only after this gate passed.
