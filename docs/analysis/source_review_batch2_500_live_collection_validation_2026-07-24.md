# Source-Review Batch 2 Live Collection Validation

Date: 2026-07-24

## Result

**PASS.** `SOURCE-REVIEW-BATCH2-500-2026-07-24` has exactly 500
terminal source-review rows in two 250-row lanes. Both lanes are
`completed_merge_eligible`, artifact integrity passed, and the audit
recommendation is `merge_all_source_review_lanes`.

This validation does not perform a durable source-review merge.

## Commands and outcomes

- Six Python compilation checks passed:
  `source_review_sources.py`, `audit_source_review_lanes.py`,
  `prepare_source_review_pilot.py`, `merge_source_review_lanes.py`,
  `test_source_review_planning.py`, and `build_dashboard_data.py`.
- `scripts/test_source_review_planning.py`: 24 tests passed. Tests are
  offline or mocked; the new 500-row exclusion/balancing regression passed.
- The final source-review lane audit reported 500/500 rows and
  `merge_all_source_review_lanes`.
- `scripts/build_dashboard_data.py` completed and rebuilt all dashboard
  data.
- All 16 dashboard JSON files parsed.
- The dashboard frontend production build passed.
- `scripts/validate.py` passed: 64 contracts, zero discourse rows, 64
  coverage rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60 passed, zero failed.
- `ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy matched
  pairs (10 exact and 18 overlap), two exploratory adjacent pairs, and six
  unmatched safety units.
- `git diff --check` passed.

## Independent scope, identity, and artifact checks

- Manifest selection: 500 rows; two lanes; 250/250.
- Lane input SHA-256:
  - Lane 1:
    `41a93aafc50c628db05de4597600ceccb20429d9c0a24d926a751b21ac061cef`
  - Lane 2:
    `51050f366f98313719d1848aefec7ea3983c5abad0ceaa6433f7c1617c2469c9`
- Live ledgers equal the locked lane inputs by both `source_review_id` and
  `candidate_queue_row_id`.
- Unique source-review IDs: 500.
- Unique candidate-queue IDs: 500.
- Overlap with durable Pilot 1 candidate IDs: zero.
- Overlap with durable Pilot 1 source-review IDs: zero.
- Terminal outcomes: 495 `reviewed_metadata_and_artifact_saved` and five
  `download_timeout`.
- Access outcomes: 495 `reached` and five `timeout`.
- Download outcomes: 495 `artifact_saved` and five `timeout`.
- Observed content types: 495 `application/pdf` and five `unknown`.
- All 495 content artifacts and all 500 response-metadata artifacts resolve
  inside their lane-local `candidate_artifacts/` directory.
- All 495 content SHA-256 values and recorded byte sizes independently
  match, and every retained content artifact begins with a PDF signature.
- Retained content bytes: 1,008,783,033.
- Retained response-metadata bytes: 543,237.
- Maximum content artifact: 9,476,151 bytes.
- Content samples, document parses, PDF parses, and OCR runs: zero.
- The 500 metadata JSON files contain no secret-bearing keys.

Exactly two live lanes ran; no third lane or retry directory was used.

## Immutability and phase-boundary checks

The following files match their pre-task SHA-256 values:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- the national candidate queue;
- the cumulative durable URL-routing ledger;
- the cumulative durable metadata-triage ledger;
- the durable latest source-review ledger.

The durable latest source-review ledger remains the 150-row Pilot 1 ledger,
and no durable Batch 2 source-review directory exists. `corpus/` has no git
status change.

The dashboard records `batch2_500_collected_not_merged`, 500 collected rows,
`batch2_500_merge_status = not_started`, and 150 cumulative merged
source-review rows.

No durable Batch 2 merge, scout accounting, broader URL verification,
routing/triage/source-review ledger mutation, parsing, OCR, content-sample
write, ingestion, `gabriel.codify`, wage extraction, wage-gap calculation
or claim, causal claim, or regression occurred. No remote was inspected and
nothing was pushed.

Validation logs are under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/batch2_500_live_collection_validation_2026-07-24/`
