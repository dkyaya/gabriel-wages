# Source-Review Pilot 1 HTTPX Retry Serial Merge Result

Date: 2026-07-24

## Result

The repaired HTTPX retry for
`SOURCE-REVIEW-PILOT1-150-2026-07-24` was merged exactly once into the
durable source-review layer. The operative durable result contains 150
terminal rows: 149 bounded PDF artifacts saved and one forbidden response.
Only the two `lane_*_live_attempt2_httpx` ledgers were merged.

The original `d97f5e4` attempt remains preserved and unmerged as superseded
transport-diagnostic provenance. The ten-row diagnostic probe also remains
preserved and excluded. No URL, source, or document was accessed during this
offline merge.

## Merge command

```text
.venv/bin/python scripts/merge_source_review_lanes.py \
  --manifest tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/pre_httpx_retry_manifest.json \
  --audit-summary tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/serial_merge_httpx_retry_lane_audit_2026-07-24/source_review_lane_audit_summary.json \
  --output-dir docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24 \
  --pilot-id SOURCE-REVIEW-PILOT1-150-2026-07-24 \
  --merge-id SOURCE-REVIEW-PILOT1-HTTPX-MERGE-2026-07-24
```

This command was executed once. The merge script is fail-closed when its
durable output files already exist.

## Durable outputs

- Pilot ledger:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv`
- Pilot summary:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_summary.json`
- Pilot merge audit:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_merge_audit.md`
- Latest ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`
- Latest summary:
  `docs/analysis/source_review_ledgers/source_review_summary_latest.json`

The pilot and latest ledgers are byte-identical, as are the pilot and latest
summaries.

## Identity and terminal coverage

- durable ledger rows: 150;
- terminal rows: 150;
- unique `source_review_id` values: 150;
- unique `candidate_queue_row_id` values: 150;
- Lane 1 rows: 75;
- Lane 2 rows: 75;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- durable stage:
  `bounded_artifact_review_not_parsed` for all 150 rows.

The durable candidate identities equal the locked Pilot 1 inputs. Artifact
paths continue to point to retained, lane-local
`lane_*_live_attempt2_httpx/candidate_artifacts` files.

## Terminal source-access outcomes

### `source_review_status`

- `reviewed_metadata_and_artifact_saved`: 149
- `download_forbidden`: 1

### `url_access_status`

- `reached`: 149
- `forbidden`: 1

### `download_status`

- `artifact_saved`: 149
- `forbidden`: 1

### Observed content type

- `application/pdf`: 149
- `unknown`: 1

Connection, timeout, TLS, not-found, too-large, unsupported-type, and generic
error counts are all zero.

## Artifact integrity

- retained content artifacts: 149;
- retained response-metadata artifacts: 150;
- rows with content hashes: 149;
- rows whose retained bytes match the recorded hash: 149;
- retained content bytes: 301,970,460;
- maximum retained content artifact: 10,319,152 bytes;
- content samples: 0;
- documents parsed: 0;
- PDFs parsed: 0;
- OCR runs: 0.

Every nonblank durable content-artifact path resolves inside its corresponding
HTTPX retry lane directory. Recorded content sizes and SHA-256 hashes match
the retained files. The one forbidden row has no content artifact or content
hash, as expected.

## Preliminary rating distributions

These distributions are access- and artifact-metadata signals. They are not
final content-supported ratings.

### Source officialness

- `official_municipal`: 82
- `official_state_repository`: 18
- `official_union`: 7
- `uncertain`: 41
- `unknown`: 2

### Relevance and identity match

- source relevance: 149 `possible`, 1 `unknown`;
- municipality match: 149 `possible`, 1 `unknown`;
- employer match: 149 `possible`, 1 `unknown`;
- bargaining-unit match: 149 `possible`, 1 `unknown`;
- safety-unit match signal: 150 `unknown`;
- non-safety-unit match signal: 150 `unknown`.

### Document type and extraction readiness

- document type: 149 `cba_candidate`, 1 `unknown`;
- extraction readiness: 149 `medium`, 1 `not_ready`;
- wage-table signal: 150 `unknown`;
- wage-growth signal: 150 `unknown`;
- mechanism-language signal: 150 `unknown`.

No retained PDF was parsed, so page count and text-layer status remain
unknown. A `cba_candidate` label does not establish that the artifact is a
CBA, that it matches the intended employer or bargaining unit, or that it
contains wage data.

## Comparison with the superseded attempt

| Measure | Original `d97f5e4` attempt | Operative HTTPX retry |
|---|---:|---:|
| Terminal rows | 150 | 150 |
| Connection errors | 149 | 0 |
| Forbidden | 1 | 1 |
| Retained content artifacts | 0 | 149 |
| Rows with content hashes | 0 | 149 |
| Retained content bytes | 0 | 301,970,460 |

The original attempt remains intact as
`preserved_unmerged_superseded_transport`. It was neither read as an
operative lane nor incorporated into the durable ledger.

## Merge-only boundary

The merge itself opened zero URLs, made zero network/API/model calls,
downloaded zero documents, parsed zero documents or PDFs, and ran zero OCR.
It did not update scout queue or coverage accounting, durable URL-routing
ledgers, or durable metadata-triage ledgers. It did not ingest sources, run
`gabriel.codify`, source-rate documents as final, extract wage tables or wage
values, calculate wage gaps, make wage-gap or causal claims, or run
regressions.
