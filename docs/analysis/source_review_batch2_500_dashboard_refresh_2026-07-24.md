# Source-Review Batch 2 Dashboard Refresh

Date: 2026-07-24

## Status

The dashboard now reports Batch 2 as durably merged:

- `source_review_phase = batch2_500_merged`;
- `latest_source_review_batch_id =
  SOURCE-REVIEW-BATCH2-500-2026-07-24`;
- `latest_source_review_merge_id =
  SOURCE-REVIEW-BATCH2-500-MERGE-2026-07-24`;
- `source_review_live_status = batch2_500_merged`;
- `batch2_500_rows_merged = 500`;
- `batch2_500_artifact_saved_rows = 495`;
- `batch2_500_timeout_rows = 5`;
- `batch2_500_connection_error_rows = 0`;
- `batch2_500_content_artifact_bytes = 1008783033`;
- `batch2_500_total_artifact_bytes = 1009326270`;
- `batch2_500_max_content_artifact_bytes = 9476151`;
- `cumulative_merged_source_review_rows = 650`;
- `cumulative_artifact_saved_rows = 644`;
- `next_scaling_recommendation = prepare_batch3_1000`.

The durable pointers shown by the dashboard are:

- latest:
  `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`;
- cumulative:
  `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`.

Both pointers represent the full 650-row cumulative layer. The dashboard
builder reads the cumulative durable summary and will not let the older
Batch 2 collection summary downgrade the project state back to “not
merged.”

## Frontend

The Source Review card now states that Batch 2 is merged, shows 650
cumulative rows, 495/500 Batch 2 artifacts saved and five timeouts, and
identifies Batch 3 1,000-row planning as the next recommendation. The
dashboard was not redesigned.

## Downstream boundary

- source rating:
  `batch2_preliminary_artifact_review_merged`;
- content download:
  `batch2_bounded_artifacts_merged`;
- extraction readiness:
  `preliminary_artifact_metadata_only`;
- ingestion: `not_started`;
- codification: `not_started`;
- wage extraction: `not_started`;
- wage-gap analysis: `not_started`.

The dashboard does not characterize preliminary ratings as final content
findings. PDFs were not parsed or OCRed, and no wage data were extracted.
Batch 3 is a planning recommendation subject to relay review, not an
authorization to run.
