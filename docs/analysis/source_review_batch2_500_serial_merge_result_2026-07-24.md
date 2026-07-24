# Source-Review Batch 2 Serial Merge Result

Date: 2026-07-24

## Result

`SOURCE-REVIEW-BATCH2-500-2026-07-24` was merged exactly once into the
durable source-review layer. The round-specific Batch 2 result contains 500
terminal rows: 495 bounded PDF artifacts saved and five timeout outcomes.

The cumulative durable layer combines the previously merged 150-row Pilot 1
ledger with Batch 2. It contains 650 unique source-review rows and preserves
both rounds rather than replacing Pilot 1 with the newest batch.

No URL, source, or document was accessed during this offline merge.

## Merge command

```bash
.venv/bin/python scripts/merge_source_review_lanes.py \
  --manifest docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_pilot_manifest.json \
  --audit-summary tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/serial_merge_lane_audit_2026-07-24/source_review_lane_audit_summary.json \
  --output-dir docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH2-500-2026-07-24 \
  --pilot-id SOURCE-REVIEW-BATCH2-500-2026-07-24 \
  --merge-id SOURCE-REVIEW-BATCH2-500-MERGE-2026-07-24 \
  --prior-ledger-csv docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv \
  --prior-summary-json docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_summary.json
```

This command was executed once. The merge tool refuses an existing
round-specific or cumulative output and requires existing latest pointers to
match the explicitly supplied prior durable ledger and summary.

## Durable outputs

Batch 2:

- ledger:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_ledger.csv`
- summary:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_summary.json`
- merge audit:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_merge_audit.md`

Cumulative/latest:

- cumulative ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`
- cumulative summary:
  `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`
- latest ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`
- latest summary:
  `docs/analysis/source_review_ledgers/source_review_summary_latest.json`

The cumulative and latest ledgers are byte-identical. Their SHA-256 is
`6724b1629508c50c5859fd609f7b7ed5f40449d210505e5205ab3472cade5744`.
The cumulative and latest summaries are also byte-identical.

## Identity and terminal coverage

Batch 2:

- durable rows / terminal rows: 500 / 500;
- unique source-review IDs: 500;
- unique candidate-queue IDs: 500;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- Pilot 1 identity overlap: 0;
- durable stage:
  `bounded_artifact_review_not_parsed` for all rows.

Cumulative:

- durable rows / terminal rows: 650 / 650;
- unique source-review IDs: 650;
- unique candidate-queue IDs: 650;
- Pilot 1 rows: 150;
- Batch 2 rows: 500.

## Batch 2 terminal outcomes

### `source_review_status`

- `reviewed_metadata_and_artifact_saved`: 495
- `download_timeout`: 5

### `url_access_status`

- `reached`: 495
- `timeout`: 5

### `download_status`

- `artifact_saved`: 495
- `timeout`: 5

### Observed content type

- `application/pdf`: 495
- `unknown`: 5

Connection, forbidden, TLS, not-found, too-large, unsupported-type, and
generic-error counts are zero for Batch 2.

## Batch 2 artifact integrity

- retained content artifacts: 495;
- retained response-metadata artifacts: 500;
- rows with content hashes: 495;
- rows with matching retained-content hashes: 495;
- retained PDF bytes: 1,008,783,033;
- retained total artifact bytes, including metadata: 1,009,326,270;
- median retained PDF: 1,249,035 bytes;
- maximum retained PDF: 9,476,151 bytes;
- content samples: 0;
- documents parsed: 0;
- PDFs parsed: 0;
- OCR runs: 0.

Every durable content-artifact path continues to point to its retained
lane-local `lane_*_live_attempt1/candidate_artifacts` file. Recorded hashes
and byte sizes match.

## Batch 2 preliminary ratings

These are access- and artifact-metadata signals, not final content-supported
ratings.

Source officialness:

- `official_municipal`: 235
- `official_state_repository`: 47
- `official_union`: 22
- `uncertain`: 185
- `unknown`: 11

Relevance and intended-identity match:

- source relevance: 495 `possible`, 5 `unknown`;
- municipality match: 495 `possible`, 5 `unknown`;
- employer match: 495 `possible`, 5 `unknown`;
- bargaining-unit match: 495 `possible`, 5 `unknown`.

Document type and technical extraction readiness:

- document type: 495 `cba_candidate`, 5 `unknown`;
- extraction readiness: 495 `medium`, 5 `not_ready`;
- wage-table signal: 500 `unknown`;
- wage-growth signal: 500 `unknown`;
- mechanism-language signal: 500 `unknown`.

## Cumulative source-review result

Across Pilot 1 and Batch 2:

- `reviewed_metadata_and_artifact_saved`: 644;
- `download_forbidden`: 1;
- `download_timeout`: 5;
- observed `application/pdf`: 644;
- observed `unknown`: 6;
- content artifacts / matching hashes: 644 / 644;
- metadata artifacts: 650;
- retained PDF bytes: 1,310,753,493;
- maximum retained PDF: 10,319,152 bytes;
- preliminary `medium` extraction readiness: 644;
- preliminary `not_ready`: 6;
- wage-table, wage-growth and mechanism-language signals:
  650 `unknown` each.

## Comparison with Pilot 1

| Measure | Pilot 1 | Batch 2 | Cumulative |
|---|---:|---:|---:|
| Durable rows | 150 | 500 | 650 |
| Saved PDF artifacts | 149 | 495 | 644 |
| Other terminal outcomes | 1 forbidden | 5 timeouts | 1 forbidden, 5 timeouts |
| Connection errors | 0 | 0 | 0 |
| Retained PDF bytes | 301,970,460 | 1,008,783,033 | 1,310,753,493 |
| Maximum PDF bytes | 10,319,152 | 9,476,151 | 10,319,152 |
| PDF parses / OCR | 0 / 0 | 0 / 0 | 0 / 0 |

## Batch 3 implication

The clean cumulative merge supports preparing
`SOURCE-REVIEW-BATCH3-1000-2026-07-24` after relay review. The metadata
triage layer contains 1,760 p1/download-allowed identities; after the 650
durably reviewed identities, 1,110 remain. Applying the existing default
duplicate exclusion leaves 1,097 eligible identities, enough for a
1,000-row Batch 3 plan.

Batch 3 is not prepared or run in this task.

## Merge-only boundary

The merge opened zero URLs, made zero network/API/model calls, downloaded
zero documents, parsed zero documents or PDFs, and ran zero OCR. It did not
update scout queue or coverage accounting, durable URL-routing ledgers, or
durable metadata-triage ledgers. It did not ingest sources, run
`gabriel.codify`, source-rate documents as final, extract wage tables or
wage values, calculate wage gaps, make wage-gap or causal claims, or run
regressions.
