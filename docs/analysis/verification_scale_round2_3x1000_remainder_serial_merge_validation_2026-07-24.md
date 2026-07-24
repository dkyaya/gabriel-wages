# Verification Scale Round 2 3×1000 Remainder — Serial Merge Validation

Date: 2026-07-24
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`

## Result

PASS. The Round 2 round-specific ledger has 2,476 terminal rows. The
project-wide cumulative and latest ledgers have 4,726 terminal rows and cover
every URL-bearing queue identity exactly once. The serial merge made no
network call and did not change scout accounting or downstream evidence
layers.

## Commands and tests

The following compiled:

- `scripts/merge_verification_lanes.py`
- `scripts/audit_verification_lanes.py`
- `scripts/verify_candidate_sources.py`
- `scripts/prepare_scaled_verification_batches.py`
- `scripts/test_scaled_verification_batches.py`
- `scripts/build_dashboard_data.py`

`python scripts/test_scaled_verification_batches.py` passed all ten checks.
The added cumulative-merge test proves that a later round-specific merge does
not replace or discard an earlier round in cumulative/latest outputs. All
HTTP behavior in the suite used `httpx.MockTransport`; external calls were
zero.

The final lane audit command was:

```bash
python scripts/audit_verification_lanes.py \
  --manifest docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verification_round_manifest.json \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/final_serial_merge_validation_lane_audit_2026-07-24
```

It reproduces three `completed_merge_eligible` classifications, 2,476
planned/ledger/terminal rows, zero cross-lane duplicate IDs, zero accounting
mutations, and `merge_all_verification_lanes`.

Other validation:

- `python scripts/build_dashboard_data.py`: PASS;
- dashboard JSON parsing: PASS, 14 files;
- dashboard production build: PASS, 43 modules;
- `python scripts/validate.py`: PASS;
- `python ingest/test_pipeline.py`: PASS, 60 tests;
- `python ingest/audit_coverage.py`: PASS; and
- `git diff --check`: PASS.

## Durable-ledger validation

| Ledger | Rows | Unique verification IDs | Unique queue IDs | SHA-256 |
|---|---:|---:|---:|---|
| Round 1 | 2,250 | 2,250 | 2,250 | `8670071182468870693063786aedc423dcf958defd769f60d0a15d19271f3dcf` |
| Round 2 | 2,476 | 2,476 | 2,476 | `e1834b2e7b2bc7eede38e1aaefee64ee1931e7dc1360b49118f7f7f9995ef949` |
| Cumulative/latest | 4,726 | 4,726 | 4,726 | `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499` |

- Round 1 / Round 2 queue-ID overlap: 0.
- Cumulative queue identities equal the canonical 4,726 URL-bearing queue IDs.
- Every row is terminal.
- Every row has
  `verification_stage = url_reachability_metadata_verified`.
- Cumulative status-count sum: 4,726.
- Cumulative reachable/reused: 3,750 (79.3483%).
- Cumulative and latest ledger bytes: identical.
- Cumulative and latest summary objects: identical.
- Original Round 1 round-specific ledger hash: unchanged.

## Artifact and secret validation

- cumulative nonblank artifact references: 4,645;
- cumulative unique referenced metadata files: 4,551;
- missing artifact files: 0;
- artifact paths outside verification lane roots: 0;
- content samples introduced by merge: 0;
- full documents introduced by merge: 0; and
- secret/credential-shaped metadata findings: 0.

## Dashboard validation

`verification_status_summary.json` reports:

- `verification_phase = full_url_routing_merged`;
- rows routed: 4,726 / 4,726;
- routing coverage rate: 1.0;
- cumulative reachable/reused: 3,750 (0.793483);
- scheduled remaining: 0;
- full URL-bearing remaining: 0; and
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

## Protected and accounting boundary

Protected/accounting SHA-256 values remain:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- municipality coverage:
  `2339ecc448f0252a5a1d533e458688d7b9e8359a5b6af013784fef4f6847e96c`;
- state coverage:
  `bad2948a2990e91280b510e5d93c1ab29aa65959f83693a641a1e902836e5a21`;
- county coverage:
  `717fa7534f3bbc41c70136dab249a61cb037e72f5b65fa93ca18bb06ff5c6033`.

Coverage remains 64 contracts, 19 cities, 28 healthy matched pairs (10 exact,
18 overlap), two exploratory adjacent pairs, and six unmatched safety units.

This merge opened no URL, downloaded no document, and made no network,
API/model, hosted-search, or scout call. No queue/coverage accounting,
contract, city-coverage, or corpus file changed. No ingestion,
`gabriel.codify`, wage extraction, wage-gap calculation or claim, causal
claim, or regression occurred.
