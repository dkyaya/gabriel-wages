# Source-Review Batch 2 Serial Merge Validation

Date: 2026-07-24

## Result

**PASS.** The offline Batch 2 serial merge produced a 500-row
round-specific durable ledger and a 650-row cumulative/latest durable
source-review layer. Identity, terminal-status, artifact-integrity,
protected-state, dashboard and pipeline checks passed.

The merge command was not rerun during validation.

## Durable ledger checks

- Batch 2 ledger rows / terminal rows: 500 / 500
- cumulative rows / terminal rows: 650 / 650
- Batch 2 unique source-review IDs: 500
- Batch 2 unique candidate-queue IDs: 500
- cumulative unique source-review IDs: 650
- cumulative unique candidate-queue IDs: 650
- Batch 2 overlap with Pilot 1 identities: 0
- Batch 2 durable stage:
  `bounded_artifact_review_not_parsed`
- cumulative and latest ledger files: byte-identical
- cumulative and latest summary files: byte-identical

The cumulative identity set equals the exact union of the 150 Pilot 1
identities and the 500 Batch 2 identities.

## Outcome and artifact checks

Batch 2:

- `reviewed_metadata_and_artifact_saved`: 495
- `download_timeout`: 5
- retained PDF artifacts / matching hashes: 495 / 495
- response-metadata artifacts: 500
- retained PDF bytes: 1,008,783,033
- maximum retained PDF: 9,476,151 bytes

Cumulative:

- `reviewed_metadata_and_artifact_saved`: 644
- `download_forbidden`: 1
- `download_timeout`: 5
- retained PDF artifacts / matching hashes: 644 / 644
- response-metadata artifacts: 650
- retained PDF bytes: 1,310,753,493
- maximum retained PDF: 10,319,152 bytes

An independent validation pass reopened every retained lane-local artifact,
recomputed all 644 SHA-256 hashes, compared recorded byte sizes, and checked
the PDF file signature. Every check passed. All 650 response-metadata paths
exist under their retained Pilot 1 or Batch 2 lane directories. No content
sample path is populated.

## Offline and protected-state checks

The validation confirmed:

- merge URL opens: 0;
- merge network calls: 0;
- merge downloads: 0;
- merge document/PDF parses: 0;
- merge OCR runs: 0;
- content samples: 0;
- no Batch 3 inputs or artifact directories were prepared;
- no scout queue or coverage accounting changes;
- no durable URL-routing ledger change;
- no durable metadata-triage ledger change;
- no Pilot 1 durable ledger change;
- no ingestion, codification, wage extraction, wage-gap calculation or
  regression work.

The pre-task SHA-256 values for `data/contracts.csv`,
`data/city_coverage.csv`, the candidate queue, cumulative routing ledger,
cumulative metadata-triage ledger and Pilot 1 durable source-review ledger
all remain unchanged. `corpus/` has no tracked change.

No credential-bearing response-metadata keys were found. Validation output
does not print URLs, credentials, authorization headers, cookies, tokens or
environment values.

## Commands and results

All required compilation checks passed for:

- `scripts/source_review_sources.py`
- `scripts/audit_source_review_lanes.py`
- `scripts/prepare_source_review_pilot.py`
- `scripts/merge_source_review_lanes.py`
- `scripts/test_source_review_planning.py`
- `scripts/build_dashboard_data.py`

Additional results:

- `scripts/test_source_review_planning.py`: 26 passed
- final Batch 2 lane audit: 500 / 500 terminal,
  `merge_all_source_review_lanes`
- `scripts/build_dashboard_data.py`: passed
- `scripts/validate.py`: passed; 64 contracts, 0 discourse, 64 coverage rows
- `ingest/test_pipeline.py`: 60 passed, 0 failed
- `ingest/audit_coverage.py`: 19 cities, 28 healthy pairs
  (10 exact-cycle, 18 overlap-cycle), 2 adjacent matches, 6 unmatched
  safety units
- dashboard production build: passed
- dashboard JSON parse: all 16 files passed
- `git diff --check`: passed
- independent durable merge and artifact validation: passed

Validation artifacts are under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/batch2_500_serial_merge_validation_2026-07-24/`

The final fresh lane-audit artifacts are under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/final_serial_merge_validation_lane_audit/`

## Interpretation boundary

The durable rows preserve preliminary source-access and artifact-metadata
signals. They are not final source-quality ratings and do not establish
source relevance, employer or unit match, wage-table presence, wage growth,
mechanism language, wage values, wage gaps or causal effects.
