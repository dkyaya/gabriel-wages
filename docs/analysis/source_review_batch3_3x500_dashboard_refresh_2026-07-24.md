# Source-Review Batch 3 (3×500) Dashboard Refresh

Date: 2026-07-24

## Status

The dashboard now reports Batch 3 as durably merged:

- `source_review_phase = batch3_3x500_merged`;
- `latest_source_review_batch_id =
  SOURCE-REVIEW-BATCH3-3X500-2026-07-24`;
- `latest_source_review_merge_id =
  SOURCE-REVIEW-BATCH3-3X500-MERGE-2026-07-24`;
- `source_review_live_status = batch3_3x500_merged`;
- `batch3_3x500_rows_merged = 1500`;
- `batch3_3x500_artifact_saved_rows = 1480`;
- `batch3_3x500_timeout_rows = 16`;
- `batch3_3x500_forbidden_rows = 4`;
- `batch3_3x500_connection_error_rows = 0`;
- `batch3_3x500_content_artifact_bytes = 3189614089`;
- `batch3_3x500_total_artifact_bytes = 3191238543`;
- `batch3_3x500_max_content_artifact_bytes = 10470269`;
- `cumulative_merged_source_review_rows = 2150`;
- `cumulative_artifact_saved_rows = 2124`; and
- `next_recommendation = text_layer_page_count_readiness_pilot`.

Durable pointers shown by the dashboard are:

- `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`
- `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`

Both represent all 2,150 durable rows. The dashboard builder validates both
the 1,500-row round summary and the 2,150-row cumulative summary before
emitting the merged status.

## Frontend

The Source Review card now shows:

- Batch 3 merged;
- 2,150 cumulative durable source-review rows;
- 1,480/1,500 Batch 3 saved artifacts;
- 2,124 cumulative saved artifacts;
- 16 Batch 3 timeouts and four forbidden outcomes;
- zero Batch 3 connection errors; and
- the bounded text-layer/page-count readiness pilot as the next
  recommendation.

The frontend continues to state that PDFs remain unparsed and that ingestion,
codification, wage extraction and wage-gap analysis have not started.

## Downstream boundary

- source rating:
  `batch3_preliminary_artifact_review_merged`;
- content download:
  `batch3_bounded_artifacts_merged`;
- extraction readiness:
  `preliminary_artifact_metadata_only`;
- ingestion: `not_started`;
- codification: `not_started`;
- wage extraction: `not_started`; and
- wage-gap analysis: `not_started`.

The dashboard does not describe these records as final content ratings,
confirmed CBAs, analysis-ready evidence or wage observations. No retained PDF
was parsed or OCRed, and no wage data were extracted.
