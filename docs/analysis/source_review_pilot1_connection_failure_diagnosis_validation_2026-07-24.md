# Source-Review Pilot 1 Connection-Diagnosis Validation

Date: 2026-07-24

## Result

All implementation, mock-transport, diagnostic-probe, artifact, dashboard,
schema, ingestion-pipeline, protected-layer, and formatting checks passed.

The shell `python` shim remains unavailable, so all Python commands used
`.venv/bin/python`.

## Commands and outcomes

- Five requested Python compile checks passed.
- `scripts/test_source_review_planning.py`: 17 passed, 0 failed. All test
  transport was fake or `httpx.MockTransport`; no real network call occurred.
- Ten-row diagnostic dry run: 10 planned rows, zero URL/network/download/
  parse/OCR/artifact activity.
- One ten-row live diagnostic probe: 10/10 terminal rows, exactly ten logical
  URL opens, nine bounded PDF artifacts with hashes, one forbidden response,
  and zero connection errors.
- Dashboard data rebuild passed for 51 states/DC, 35,589 municipalities,
  2,436 scout-covered municipalities, and 4,726 candidate rows.
- All 16 dashboard JSON files parse.
- Dashboard frontend production build passed with Vite 8.1.5.
- `scripts/validate.py` passed: 64 contracts, zero discourse rows, 64 coverage
  rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60 passed, 0 failed.
- Coverage audit: 28 healthy matched pairs (10 exact, 18 overlap), two
  exploratory adjacent matches, and six unmatched safety units.
- `git diff --check` passed.

Validation logs are under:

`tmp/source_review_connection_diagnosis_validation_2026-07-24/`

## Probe identity and scope

- Probe input rows: 10.
- Original Pilot 1 Lane 1 / Lane 2 split: 5 / 5.
- Unique source-review IDs: 10.
- Unique candidate-queue IDs: 10.
- Exact input-to-ledger identity equality: yes.
- Rows outside the locked 150-row pilot: 0.
- Additional live probes: 0.
- Full 150-row retry: not run.
- 500/750/1,000-row scale-up: not run.
- Durable source-review merge: not run.

## Artifact checks

- Content artifacts: 9.
- Matching SHA-256 hashes: 9.
- PDF signatures: 9.
- Total retained content bytes: 12,536,566.
- Maximum artifact bytes: 3,328,197, below the 26,214,400-byte cap.
- Metadata artifacts: 10.
- Every artifact path exists and resolves inside the diagnostic output.
- Content samples: 0.
- Document/PDF parses: 0 / 0.
- OCR runs: 0.
- Metadata secret/header findings: 0.

## Protected-layer checks

Hashes remain:

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
the candidate queue, durable routing ledgers, and durable metadata-triage
ledgers.

## Boundary confirmation

No full Pilot 1 retry or scaling occurred. No durable source-review merge,
scout-accounting change, routing/triage-ledger mutation, PDF parse, OCR,
ingestion, codification, wage extraction, wage-gap calculation or claim,
causal claim, regression, remote inspection, or push occurred.
