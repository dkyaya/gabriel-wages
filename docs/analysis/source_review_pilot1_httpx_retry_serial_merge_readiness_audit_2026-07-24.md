# Source-Review Pilot 1 HTTPX Retry Serial-Merge Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The repaired HTTPX retry is ready for one offline serial durable
source-review merge. Only the fresh `attempt2_httpx` lane ledgers are eligible
inputs. The original transport-failed attempt and the diagnostic probe are
explicitly excluded.

Work began at local commit
`5e14f635e377384b7bf0ffbed018600d2f25c33f`. The tracked worktree was clean.
The unrelated untracked root `package-lock.json` was present before work and
remains out of scope. Local ancestry includes `5e14f63`, `1544750`,
`d97f5e4`, `a0c2445`, `b94aad9`, `79df80c`, and `e028432`.

## Locked input checks

The committed pilot manifest still describes exactly 150 selected rows in
two lanes of 75 rows. Its recomputed input hashes match:

- Lane 1:
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`
- Lane 2:
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`

The merge audit uses the existing transient
`tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/pre_httpx_retry_manifest.json`.
It is an exact locked-manifest copy whose only operative change is that its
live-output pointers select:

- `lane_1_live_attempt2_httpx`
- `lane_2_live_attempt2_httpx`

The committed locked manifest is not modified.

## Fresh lane audit

The exact command was:

```bash
.venv/bin/python scripts/audit_source_review_lanes.py \
  --manifest tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/pre_httpx_retry_manifest.json \
  --output-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/serial_merge_httpx_retry_lane_audit_2026-07-24
```

The audit reports:

- Lane 1: `completed_merge_eligible`, 75/75 rows;
- Lane 2: `completed_merge_eligible`, 75/75 rows;
- planned / ledger / terminal rows: 150 / 150 / 150;
- cross-lane duplicate source-review IDs: 0;
- cross-lane duplicate candidate-queue IDs: 0;
- `reviewed_metadata_and_artifact_saved`: 149;
- `download_forbidden`: 1;
- connection errors: 0;
- content artifacts: 149;
- metadata artifacts: 150;
- rows with content hashes: 149;
- content samples: 0;
- documents/PDFs parsed: 0 / 0;
- OCR runs: 0;
- artifact integrity: passed; and
- recommendation: `merge_all_source_review_lanes`.

All 149 content paths resolve inside their retry lane, and their recorded
hashes and sizes match the retained artifacts.

## Superseded and diagnostic outputs

The original failed attempt remains immutable:

- Lane 1 tree digest:
  `b84e9fb3bc7a162cb035cffe8e8a8ecaf8c820bce1bf1c1bda278ec0fe32c356`
- Lane 2 tree digest:
  `e977f0c9843f8bdb507e596c5c8a333b3fdce18b3f33866faa8ef36568f25aab`

Those ledgers contain 149 superseded connection errors and one forbidden
outcome. They are diagnostic provenance only and are not merge inputs.

The ten-row diagnostic probe also remains immutable, with tree digest
`2fba18b476a0f3594744889ea2ec141f23359df2af53cc32ac817c67151d13b5`.
Its nine artifacts and one forbidden outcome are not merge inputs.

The operative comparison is therefore:

| Result | Original failed attempt | HTTPX retry to merge |
|---|---:|---:|
| Terminal rows | 150 | 150 |
| Connection errors | 149 | 0 |
| Forbidden | 1 | 1 |
| Retained content artifacts | 0 | 149 |
| Matching content hashes | 0 | 149 |

## Protected-layer and exactly-once gate

No durable `docs/analysis/source_review_ledgers/` directory exists. The merge
has not previously run.

Baseline hashes remain:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- canonical candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- cumulative routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`

No ingestion, codification, wage extraction, wage-gap analysis or claim,
causal claim, regression, scout-accounting change, or downstream output was
created from Pilot 1.

## Merge boundary

The authorized merge may create or update only the durable source-review
ledger, its summary/audit/latest pointers, source-review dashboard status, and
documentation. It will not open a URL, download or parse a document, run OCR,
run a scout or URL verifier, call an API/model/hosted search, mutate candidate
queue or scout coverage, mutate routing or metadata-triage ledgers, write to
`corpus/`, ingest, codify, extract wages, calculate wage gaps, make empirical
claims, or run regressions.
