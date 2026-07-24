# Source-Review Pilot 1 HTTPX Retry Serial-Merge Validation

Date: 2026-07-24

## Result

**PASS.** The durable source-review merge, dashboard refresh, documentation,
and safeguards pass the requested offline validation. The merge was not
rerun during validation.

Validation outputs are retained under:

`tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/httpx_serial_merge_validation_2026-07-24/`

The final independent lane audit is retained under:

`tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/final_httpx_serial_merge_validation_lane_audit/`

## Code and test gates

- six requested Python compile checks: passed;
- `scripts/test_source_review_planning.py`: 23 passed;
- merge-specific tests cover:
  - preservation of all lane rows, content paths, hashes, and ratings;
  - duplicate source-review ID rejection;
  - duplicate candidate-queue ID rejection;
  - nonterminal-row rejection;
  - non-merge-eligible audit rejection;
  - fail-closed existing-output behavior; and
  - explicit exclusion of a synthetic superseded-attempt directory;
- all network behavior in the test suite uses mocks/local fixtures.

## Final source-review audit

The final audit reproduces:

- Lane 1: `completed_merge_eligible`, 75/75 rows;
- Lane 2: `completed_merge_eligible`, 75/75 rows;
- planned / ledger / terminal: 150 / 150 / 150;
- cross-lane duplicate source-review IDs: 0;
- cross-lane duplicate candidate-queue IDs: 0;
- artifact-saved / forbidden: 149 / 1;
- connection errors: 0;
- content artifacts / matching hashes: 149 / 149;
- content samples: 0;
- document parses / PDF parses / OCR: 0 / 0 / 0;
- artifact integrity: passed;
- recommendation: `merge_all_source_review_lanes`.

The final audit reads collection-time counters from the HTTPX retry. Those
counters correctly record 150 historical URL attempts and 149 historical
downloads. The durable summary separately records merge-time URL, network,
download, parse, PDF-parse, and OCR counters, all of which are zero.

## Durable ledger integrity

- ledger rows: 150;
- terminal rows: 150;
- unique source-review IDs: 150;
- unique candidate-queue IDs: 150;
- durable stage:
  `bounded_artifact_review_not_parsed` on every row;
- merge ID:
  `SOURCE-REVIEW-PILOT1-HTTPX-MERGE-2026-07-24` on every row;
- artifact paths lane-local to the repaired HTTPX retry: 149;
- retained artifact hashes and byte sizes independently matched: 149;
- pilot and latest ledgers byte-identical: yes;
- pilot and latest summaries byte-identical: yes;
- durable summary JSON parses: yes.

## Dashboard and project validation

- dashboard data builder: passed;
- source-review dashboard JSON parses: passed;
- dashboard phase: `pilot1_httpx_merged`;
- dashboard merge status: `merged`;
- dashboard Pilot 1 rows / saved / forbidden / connection errors:
  150 / 149 / 1 / 0;
- dashboard production frontend build: passed;
- `scripts/validate.py`: passed;
- `ingest/test_pipeline.py`: 60 passed, 0 failed;
- `ingest/audit_coverage.py`: passed;
- `git diff --check`: passed.

Coverage remains 64 contracts across 19 cities, with 28 healthy matched
pairs (10 exact and 18 overlapping), two exploratory adjacent pairs, and six
unmatched safety units.

## Immutable provenance and protected layers

The original transport-failed and diagnostic trees retain their pre-merge
digests:

- original Lane 1:
  `b84e9fb3bc7a162cb035cffe8e8a8ecaf8c820bce1bf1c1bda278ec0fe32c356`;
- original Lane 2:
  `e977f0c9843f8bdb507e596c5c8a333b3fdce18b3f33866faa8ef36568f25aab`;
- diagnostic probe:
  `2fba18b476a0f3594744889ea2ec141f23359df2af53cc32ac817c67151d13b5`.

Protected hashes remain:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- cumulative routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`.

No tracked change exists under `data/contracts.csv`,
`data/city_coverage.csv`, `corpus/`, the candidate queue, the URL-routing
ledger layer, or the metadata-triage ledger layer. All 150 HTTPX
response-metadata JSON files and the durable CSV schema passed a
secret/header-key check without printing values.

## Boundary confirmation

During this merge task there were zero URL opens, network/API/model calls,
document downloads, document/PDF parses, OCR runs, live source-review rows,
content samples, scouts, scout-accounting changes, routing-ledger changes,
metadata-triage-ledger changes, ingestion runs that mutate data,
`gabriel.codify` runs, wage extractions, wage-gap calculations or claims,
causal claims, regressions, remote inspections, fetches, pulls, or pushes.
