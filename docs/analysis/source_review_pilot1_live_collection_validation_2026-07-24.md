# Source-Review Pilot 1 Live Collection Validation

Date: 2026-07-24

## Result

All structural, identity, artifact-safety, dashboard, and protected-layer
validation checks passed. The content-yield scale gate did not pass because no
source body was retained.

The shell `python` shim was unavailable during the task. All Python commands
were therefore run with `.venv/bin/python`.

## Commands and outcomes

- Five requested Python compilation checks passed.
- `scripts/test_source_review_planning.py`: 13 passed, 0 failed; all network
  behavior in this test suite was mocked.
- Final live lane audit: 150/150 terminal rows, two
  `completed_merge_eligible` lanes, artifact integrity passed, and
  `merge_all_source_review_lanes`.
- Dashboard data rebuild passed for 51 states/DC, 35,589 municipalities, 2,436
  scout-covered municipalities, and 4,726 candidate rows.
- All 16 dashboard JSON files parse.
- Dashboard frontend production build passed with Vite 8.1.5.
- `scripts/validate.py` passed: 64 contracts, zero discourse rows, 64 coverage
  rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60 passed, 0 failed.
- Coverage audit: 28 healthy matched pairs (10 exact, 18 overlap), two
  exploratory adjacent matches, and six unmatched safety units.
- `git diff --check` passed.

Validation logs are under:

`tmp/source_review_pilot1_live_collection_validation_2026-07-24/`

## Identity and live-scope checks

- Lane input hashes match the locked values.
- Each input has 75 rows.
- Each live ledger has 75 terminal rows.
- Combined source-review ID equality with the inputs: exact.
- Combined candidate-queue ID equality with the inputs: exact.
- Unique source-review IDs: 150.
- Unique candidate-queue IDs: 150.
- URL attempts/network calls: 150 / 150.
- A third live lane does not exist.
- Both lane command exit codes are zero.
- No retry directory exists.
- No durable source-review ledger directory exists.

## Artifact checks

- Retained source-content artifacts: 0.
- Content hashes: 0.
- Content samples: 0.
- Lane-local response-metadata JSON files: 150.
- Metadata bytes: 114,939.
- Maximum metadata artifact: 805 bytes.
- Every metadata path resolves inside its lane and exists.
- Artifact-integrity audit: passed.
- Secret-pattern findings in metadata: 0.
- Unredacted sensitive query values in sanitized recorded URLs: 0.
- Raw-header/auth/cookie metadata keys: 0.

## Protected-layer checks

Recomputed hashes remain:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- canonical candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- cumulative URL-routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`.

The protected-path diff is empty for contracts, city coverage, `corpus/`,
the canonical queue, durable routing ledgers, and durable metadata-triage
ledgers.

## Boundary confirmation

Only the 150 locked locator attempts ran, in exactly two lanes with concurrency
four, 30/8/20-second limits, five redirects, 25 MiB, and samples off. No
durable source-review merge, retry, scout, URL-verification round,
scout-accounting update, routing/triage-ledger mutation, PDF parse, OCR,
source-content extraction, ingestion, codification, wage extraction,
wage-gap calculation/claim, causal claim, or regression occurred. Nothing was
pushed and no remote was inspected.
