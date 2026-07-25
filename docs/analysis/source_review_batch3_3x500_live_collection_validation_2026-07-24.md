# Source-Review Batch 3 (3×500) Live Collection Validation

Date: 2026-07-24

## Result

Validation passed for the collected, audited, not-yet-merged
`SOURCE-REVIEW-BATCH3-3X500-2026-07-24` source-review batch.

The validation covered the locked inputs, all three dry-run lanes, all three
live lanes, retained artifacts, lane audits, generated dashboard data,
repository schema, ingestion regressions, protected files and durable
ledgers. No durable Batch 3 source-review merge was run.

## Commands and outcomes

- Six source-review/dashboard Python files compiled successfully with
  `.venv/bin/python -m py_compile`.
- `scripts/test_source_review_planning.py`: 28 tests passed. The tests use
  temporary data and mocked HTTP transports; they made no real network calls.
- Final source-review lane audit: 1,500/1,500 terminal rows,
  `completed_merge_eligible` for all three lanes, and
  `merge_all_source_review_lanes`.
- `scripts/build_dashboard_data.py`: passed and regenerated all 16 dashboard
  JSON files.
- Dashboard JSON parse check: all 16 files passed.
- Dashboard frontend production build: passed.
- `scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64
  coverage rows and three city-attribute rows.
- `ingest/test_pipeline.py`: 60 tests passed.
- `ingest/audit_coverage.py`: 64 contracts in 19 cities, 28 healthy matched
  pairs (10 exact and 18 overlap), two exploratory adjacent pairs and six
  unmatched safety units.
- `git diff --check`: passed.

The stored console outputs are under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/batch3_3x500_live_collection_validation_2026-07-24/`

The final validation lane audit is under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/final_live_collection_validation_lane_audit/`

## Independent scope and artifact checks

The collection-integrity verifier independently confirmed:

- 1,500 selected rows in exactly three 500-row lanes;
- 1,500 unique source-review IDs and candidate-queue row IDs;
- no overlap with the 650 identities in the cumulative durable
  source-review ledger;
- no fourth lane and no retry output;
- 1,480 saved PDF rows, 16 timeout rows and four forbidden rows;
- zero connection errors;
- 1,480 lane-local PDFs with matching recorded hashes and sizes and valid PDF
  signatures;
- 1,500 lane-local response-metadata JSON files;
- 3,189,614,089 retained PDF bytes;
- 1,624,454 response-metadata bytes;
- 3,191,238,543 total retained artifact bytes;
- 10,470,269 maximum retained PDF bytes;
- zero content samples, document parses, PDF parses and OCR runs; and
- no durable Batch 3 merge.

Every selected row has a terminal source-review status. Every retained
content-artifact path resolves under its own lane output directory. Artifact
metadata were checked for secret-bearing keys and none were found.

## Protected and durable state

Before and after the task, SHA-256 digests were equal for:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- `docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`;
- `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`;
- `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`;
- `docs/analysis/source_review_ledgers/source_review_ledger_latest.csv`;
- `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`;
  and
- `docs/analysis/source_review_ledgers/source_review_summary_latest.json`.

The `corpus/` tree was not written. No scout queue or coverage accounting,
URL-routing ledger, metadata-triage ledger or durable source-review ledger was
mutated. The unrelated untracked root `package-lock.json` remained untouched.

## Boundaries confirmed

Live URL access and bounded downloads were limited to the 1,500 locked Batch
3 inputs. No broader URL verification, scout, API/model/hosted-search call,
fourth lane or retry occurred. No retained PDF was parsed or OCRed, and no
full-text or content sample was extracted. No contract ingestion,
`gabriel.codify`, wage-table or wage-value extraction, wage-gap calculation,
causal claim or regression occurred. No remote was inspected and nothing was
pushed.

The collection is therefore validated as a bounded preliminary
source-access/artifact layer. It is not a durable source-review result until
a separately authorized serial merge succeeds.
