# Source-Review Batch 3 (3×500) Dashboard Status Note

Date: 2026-07-24

The dashboard records Batch 3 as collected and audited but not durably
merged:

- `source_review_phase = batch3_3x500_collected_not_merged`;
- `source_review_live_status = batch3_3x500_collected_not_merged`;
- latest batch:
  `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`;
- Batch 3 rows collected: 1,500;
- Batch 3 merge status: `not_started`;
- retained Batch 3 artifacts: 1,480;
- Batch 3 timeout rows: 16;
- Batch 3 forbidden rows: 4;
- Batch 3 connection-error rows: 0;
- cumulative merged source-review rows: 650;
- source rating:
  `batch3_3x500_collected_not_merged`;
- content download:
  `batch3_3x500_collected_not_merged`;
- extraction readiness:
  `preliminary_batch3_not_merged`;
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

The dashboard does not add the 1,500 transient Batch 3 rows to the durable
650-row cumulative count. It does not describe preliminary access/artifact
signals as final content ratings, and it states that PDFs were not parsed or
OCRed.

The next recommendation is to merge Batch 3 serially after relay review,
then evaluate text-layer/page-count readiness before automatically
downloading the remaining default-eligible p2 pool.
