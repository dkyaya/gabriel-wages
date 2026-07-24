# Source-Review Pilot 1 HTTPX Retry Dashboard Refresh

Date: 2026-07-24

## Status

The dashboard now reports the repaired Pilot 1 HTTPX retry as durably merged:

- `source_review_phase = pilot1_httpx_merged`;
- `latest_source_review_pilot_id =
  SOURCE-REVIEW-PILOT1-150-2026-07-24`;
- `latest_source_review_merge_id =
  SOURCE-REVIEW-PILOT1-HTTPX-MERGE-2026-07-24`;
- `source_review_live_status = pilot1_httpx_merged`;
- `pilot1_rows_merged = 150`;
- `pilot1_artifact_saved_rows = 149`;
- `pilot1_forbidden_rows = 1`;
- `pilot1_connection_error_rows = 0`;
- `pilot1_content_artifact_bytes = 301970460`;
- `pilot1_max_content_artifact_bytes = 10319152`;
- `pilot1_preliminary_medium_extraction_readiness_rows = 149`;
- `original_failed_attempt_status =
  preserved_unmerged_superseded_transport`;
- `next_scaling_recommendation = plan_500_after_relay_review`.

The durable latest pointer shown by the dashboard is:

`docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`

The dashboard builder reads the durable source-review summary and emits these
values, so routine dashboard rebuilds preserve the merged state. The Source
Review section shows 149/150 artifacts saved, states that the original
transport-failed attempt was superseded, and keeps content interpretation and
downstream work visibly separate.

## Downstream boundary

- source rating:
  `pilot1_preliminary_artifact_review_merged`;
- content download:
  `pilot1_bounded_artifacts_merged`;
- extraction readiness:
  `pilot1_preliminary_artifact_metadata_only`;
- ingestion: `not_started`;
- codification: `not_started`;
- wage extraction: `not_started`;
- wage-gap analysis: `not_started`.

The dashboard does not describe these records as final content ratings or
analysis-ready evidence. PDFs were not parsed or OCRed, and no wage data were
extracted. Planning a 500-row follow-on is a recommendation for relay review,
not authorization to run it.
