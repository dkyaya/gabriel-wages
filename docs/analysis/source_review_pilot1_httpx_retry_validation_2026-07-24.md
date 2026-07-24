# Source-Review Pilot 1 HTTPX Retry Validation

Date: 2026-07-24

## Result

**PASS.** The repaired-client retry, artifact layer, audit, dashboard, and
project validation gates all pass. The shell `python` shim was not used; all
Python commands used `.venv/bin/python`.

## Commands and outcomes

- Five requested Python compile checks passed:
  `source_review_sources.py`, `audit_source_review_lanes.py`,
  `prepare_source_review_pilot.py`, `test_source_review_planning.py`, and
  `build_dashboard_data.py`.
- `scripts/test_source_review_planning.py`: 17 passed, 0 failed. Its transport
  tests use fakes or `httpx.MockTransport`, not the network.
- The final lane audit used the implemented equivalent command:

  ```bash
  .venv/bin/python scripts/audit_source_review_lanes.py \
    --manifest tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/pre_httpx_retry_manifest.json \
    --output-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/final_httpx_retry_validation_lane_audit
  ```

  The transient manifest is an exact copy of the committed locked manifest
  with only dry/live output-directory pointers changed to the fresh retry
  directories. This was necessary because the committed manifest correctly
  preserves the original `attempt1` locations. It was not modified.

  The audit reports 150/150 terminal rows, two
  `completed_merge_eligible` lanes, no duplicate identities, clean
  artifact integrity, and `merge_all_source_review_lanes`.
- `scripts/build_dashboard_data.py` rebuilt all 16 JSON outputs.
  Every JSON file parses.
- The dashboard production build passed with 45 transformed modules.
- `scripts/validate.py` passed.
- `ingest/test_pipeline.py`: 60 passed, 0 failed.
- `ingest/audit_coverage.py` reports 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact and 18 overlapping), two exploratory adjacent
  pairs, and six unmatched safety units.
- `git diff --check` passed.

## Scope and artifact validation

- Locked input and retry ledgers have exact equality for all 150 unique
  source-review IDs and all 150 unique candidate-queue IDs.
- Exactly 150 URL/network attempts are recorded, all in the two locked lanes.
- There is no third retry lane.
- Every selected row has a terminal source-review status.
- All 149 retained content artifacts resolve within the two
  `lane_*_live_attempt2_httpx` directories.
- All 149 retained artifacts match their recorded SHA-256 hashes and byte
  sizes and begin with a PDF signature.
- Retained content totals 301,970,460 bytes; the largest artifact is
  10,319,152 bytes.
- All 150 response-metadata paths are lane-local and total 163,090 bytes.
- Metadata contains no authorization, cookie, proxy-authorization, raw-header,
  or generic header collection.
- Content samples: 0.
- Documents/PDFs parsed: 0/0.
- OCR runs: 0.

## Immutability and downstream boundaries

The protected files retain their baseline hashes:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- canonical candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- cumulative URL-routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`

No tracked `corpus/` file changed. The preserved original Lane 1, original
Lane 2, and diagnostic-probe directory-tree digests remain, respectively:

- `b84e9fb3bc7a162cb035cffe8e8a8ecaf8c820bce1bf1c1bda278ec0fe32c356`;
- `e977f0c9843f8bdb507e596c5c8a333b3fdce18b3f33866faa8ef36568f25aab`;
  and
- `2fba18b476a0f3594744889ea2ec141f23359df2af53cc32ac817c67151d13b5`.

No durable source-review ledger exists. No scout queue or coverage
accounting, routing ledger, or metadata-triage ledger changed. No ingestion,
`gabriel.codify`, wage extraction, wage-gap calculation or claim, causal
claim, or regression occurred. No API, model, hosted-search, scout, broader
URL-verification, remote, fetch, pull, push, or third-lane action occurred.
