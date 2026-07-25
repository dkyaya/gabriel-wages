# Source-Review Batch 3 (3×500) Serial Merge Result

Date: 2026-07-24

## Result

`SOURCE-REVIEW-BATCH3-3X500-2026-07-24` was merged exactly once into
the durable source-review layer. The round-specific Batch 3 result contains
1,500 terminal rows: 1,480 bounded PDF artifacts saved, 16 timeout outcomes,
and four forbidden outcomes.

The cumulative durable layer combines the previously merged 150-row Pilot 1
ledger, the 500-row Batch 2 ledger, and Batch 3. It contains 2,150 unique
source-review rows and preserves all three rounds.

No URL, source, or document was accessed during this offline merge.

## Merge command

```bash
.venv/bin/python scripts/merge_source_review_lanes.py \
  --manifest docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/source_review_pilot_manifest.json \
  --audit-summary tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/serial_merge_lane_audit_2026-07-24/source_review_lane_audit_summary.json \
  --output-dir docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH3-3X500-2026-07-24 \
  --pilot-id SOURCE-REVIEW-BATCH3-3X500-2026-07-24 \
  --merge-id SOURCE-REVIEW-BATCH3-3X500-MERGE-2026-07-24 \
  --prior-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --prior-summary-json docs/analysis/source_review_ledgers/source_review_summary_cumulative.json
```

This command was executed once. The merge tool:

- refused any pre-existing Batch 3 round output;
- required cumulative and latest pointers to be byte-identical to the
  explicit 650-row prior ledger and summary;
- validated every prior and Batch 3 identity, terminal status, artifact path,
  hash and size;
- preserved rollback bytes for all existing cumulative/latest pointers; and
- atomically replaced cumulative/latest only after all gates passed.

## Durable outputs

Batch 3:

- ledger:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/source_review_ledger.csv`
- summary:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/source_review_summary.json`
- merge audit:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/source_review_merge_audit.md`

Cumulative/latest:

- cumulative ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`
- cumulative summary:
  `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`
- latest ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`
- latest summary:
  `docs/analysis/source_review_ledgers/source_review_summary_latest.json`

The cumulative and latest ledgers are byte-identical with SHA-256
`e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`.
The cumulative and latest summaries are byte-identical with SHA-256
`21e36de3552e3db09fa2090ed46509d702b3d69237d31f5c49082fb1ad9b475a`.

The round-specific Batch 3 ledger SHA-256 is
`cf67670da9b48fee69e88fb4b71dc5fcf8d9ae713f104751bf33e381e22a9f4b`.

## Identity and terminal coverage

Batch 3:

- durable / terminal rows: 1,500 / 1,500;
- unique source-review IDs: 1,500;
- unique candidate-queue IDs: 1,500;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- prior durable candidate overlap: 0;
- prior durable source-review-ID overlap: 0;
- lane rows: 500 / 500 / 500; and
- durable stage:
  `bounded_artifact_review_not_parsed` for all 1,500 rows.

Cumulative:

- durable / terminal rows: 2,150 / 2,150;
- unique source-review IDs: 2,150;
- unique candidate-queue IDs: 2,150;
- duplicate identities: 0; and
- merged batch rows:
  - Pilot 1: 150;
  - Batch 2: 500;
  - Batch 3: 1,500.

Artifact paths continue to point to the retained lane-local source-review
directories. No content artifact was copied into `corpus/` or the durable
ledger directory.

## Batch 3 terminal source-access outcomes

### `source_review_status`

- `reviewed_metadata_and_artifact_saved`: 1,480
- `download_timeout`: 16
- `download_forbidden`: 4

### `url_access_status`

- `reached`: 1,480
- `timeout`: 16
- `forbidden`: 4

### `download_status`

- `artifact_saved`: 1,480
- `timeout`: 16
- `forbidden`: 4

### Observed content type

- `application/pdf`: 1,480
- `unknown`: 20

Connection, TLS, not-found, too-large, unsupported-content-type and generic
error counts are zero.

## Batch 3 artifact integrity

- retained content artifacts: 1,480;
- retained response-metadata artifacts: 1,500;
- rows with content hashes: 1,480;
- rows with independently matching content hashes: 1,480;
- retained PDF bytes: 3,189,614,089;
- response-metadata bytes: 1,624,454;
- retained total artifact bytes: 3,191,238,543;
- maximum retained PDF: 10,470,269 bytes;
- content samples: 0;
- documents parsed: 0;
- PDFs parsed: 0; and
- OCR runs: 0.

Every nonblank durable content path resolves inside its corresponding Batch 3
live lane. Recorded sizes and SHA-256 hashes match the retained files.

## Preliminary Batch 3 ratings

These are access- and artifact-metadata signals. They are not final
content-supported ratings.

### Source officialness

- `official_state_repository`: 471
- `official_municipal`: 468
- `uncertain`: 451
- `unknown`: 87
- `official_union`: 23

### Relevance and identity match

- source relevance: 1,480 `possible`, 20 `unknown`;
- municipality match: 1,480 `possible`, 20 `unknown`;
- employer match: 1,480 `possible`, 20 `unknown`;
- bargaining-unit match: 1,480 `possible`, 20 `unknown`;
- safety-unit match signal: 1,500 `unknown`; and
- non-safety-unit match signal: 1,500 `unknown`.

### Document type and extraction readiness

- document type: 1,359 `cba_candidate`, 141 `unknown`;
- extraction readiness: 1,480 `medium`, 20 `not_ready`;
- wage-table signal: 1,500 `unknown`;
- wage-growth signal: 1,500 `unknown`;
- mechanism-language signal: 1,500 `unknown`;
- PDF page count: 1,500 `unknown`; and
- text-layer status: 1,500 `unknown`.

A `cba_candidate` label does not establish that an artifact is a CBA, matches
the intended employer or bargaining unit, or contains wage data.

## Cumulative source-review result

Across Pilot 1, Batch 2 and Batch 3:

- durable rows: 2,150;
- saved PDF artifacts: 2,124;
- timeout outcomes: 21;
- forbidden outcomes: 5;
- connection errors: 0;
- retained PDF bytes: 4,500,367,582;
- response-metadata bytes: 2,330,781;
- total retained artifact bytes: 4,502,698,363;
- maximum retained PDF: 10,470,269 bytes;
- rows with matching content hashes: 2,124;
- `application/pdf`: 2,124;
- observed content type `unknown`: 26;
- extraction readiness `medium`: 2,124;
- extraction readiness `not_ready`: 26; and
- documents/PDFs parsed and OCR runs: 0 / 0 / 0.

Cumulative preliminary officialness:

- `official_municipal`: 785;
- `official_state_repository`: 536;
- `uncertain`: 677;
- `unknown`: 100; and
- `official_union`: 52.

Cumulative source relevance and municipality/employer/unit match are each
2,124 `possible` and 26 `unknown`. Cumulative document type is 2,003
`cba_candidate` and 147 `unknown`. All 2,150 wage-table, wage-growth and
mechanism-language signals remain `unknown`.

## Comparison across durable rounds

| Measure | Pilot 1 | Batch 2 | Batch 3 | Cumulative |
|---|---:|---:|---:|---:|
| Durable rows | 150 | 500 | 1,500 | 2,150 |
| Saved PDFs | 149 | 495 | 1,480 | 2,124 |
| Timeout | 0 | 5 | 16 | 21 |
| Forbidden | 1 | 0 | 4 | 5 |
| Connection errors | 0 | 0 | 0 | 0 |
| Retained PDF bytes | 301,970,460 | 1,008,783,033 | 3,189,614,089 | 4,500,367,582 |
| PDF parses / OCR | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

## Post-Batch-3 recommendation

The metadata-triage layer has 773 raw download-allowed identities not in the
2,150-row cumulative ledger: 13 p1 and 760 p2. After the planner's default
duplicate, oversized, blocked, defer, exclude and disposition gates, the
remaining eligible pool is 726 p2 rows and zero p1/p3 rows.

Do not automatically download that remaining p2 pool. The current bottleneck
is no longer basic HTTP access:

- retained PDFs have not been parsed;
- page counts and text-layer status are unknown;
- wage/mechanism signals remain unknown;
- retained content already exceeds 4.5 GB; and
- preliminary access metadata cannot establish substantive rating quality.

The recommended next task is a bounded 100–200-row text-layer/page-count
readiness pilot over retained Pilot 1, Batch 2 and Batch 3 artifacts. It
should record page counts, text-layer presence and basic parseability without
OCR, wage extraction, ingestion or codification.

## Merge-only boundary

The merge itself opened zero URLs, made zero network/API/model calls,
downloaded zero documents, parsed zero documents or PDFs, and ran zero OCR.
It did not update scout queue or coverage accounting, durable URL-routing
ledgers, or durable metadata-triage ledgers. It did not ingest sources, run
`gabriel.codify`, source-rate documents as final, extract wage tables or wage
values, calculate wage gaps, make wage-gap or causal claims, or run
regressions.
