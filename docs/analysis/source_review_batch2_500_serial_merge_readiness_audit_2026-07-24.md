# Source-Review Batch 2 Serial-Merge Readiness Audit

Date: 2026-07-24

## Result

**PASS.** `SOURCE-REVIEW-BATCH2-500-2026-07-24` is ready for one
offline serial durable merge. The only operative inputs are:

- `tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/lane_1_live_attempt1/source_review_ledger.csv`
- `tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/lane_2_live_attempt1/source_review_ledger.csv`

Work began at local commit
`4db43178481e84620c0762da62fcc7b94b7d7672`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` was present before
work and remains out of scope. Local ancestry includes `4db4317`,
`ed042c1`, `5e14f63`, `1544750`, `b94aad9`, `79df80c`, and `e028432`.

## Locked identity gates

The committed manifest points directly to the intended live `attempt1`
directories. It selects 500 rows in two lanes of 250. Recomputed input
hashes match the manifest:

- Lane 1:
  `41a93aafc50c628db05de4597600ceccb20429d9c0a24d926a751b21ac061cef`
- Lane 2:
  `51050f366f98313719d1848aefec7ea3983c5abad0ceaa6433f7c1617c2469c9`

The planned inputs and live ledgers have exact equality by both
`source_review_id` and `candidate_queue_row_id`. Across Batch 2:

- planned / live / terminal rows: 500 / 500 / 500;
- unique source-review IDs: 500;
- unique candidate-queue IDs: 500;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- overlap with Pilot 1 candidate identities: 0;
- overlap with Pilot 1 source-review identities: 0.

Pilot 1 contains 150 distinct durable identities. Pilot 1 plus Batch 2
therefore yields 650 unique candidate identities and 650 unique
source-review identities.

## Fresh lane audit

The exact command was:

```bash
.venv/bin/python scripts/audit_source_review_lanes.py \
  --manifest docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_pilot_manifest.json \
  --output-dir tmp/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/serial_merge_lane_audit_2026-07-24
```

The audit reports:

- Lane 1: `completed_merge_eligible`, 250/250 rows;
- Lane 2: `completed_merge_eligible`, 250/250 rows;
- `reviewed_metadata_and_artifact_saved`: 495;
- `download_timeout`: 5;
- connection errors: 0;
- content artifacts: 495;
- metadata artifacts: 500;
- rows with content hashes: 495;
- content samples: 0;
- documents/PDFs parsed: 0 / 0;
- OCR runs: 0;
- artifact integrity: passed;
- recommendation: `merge_all_source_review_lanes`.

All recorded content paths remain lane-local. The prior independent
collection validation verified every retained artifact's path, SHA-256,
recorded byte size, and PDF signature.

## Exactly-once and protected-layer gate

The durable Pilot 1 ledger remains intact at:

`docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv`

It has 150 rows and SHA-256
`2bcfe2295950f9805322d1cbbaf08051bd93b08cb632067d688ec6f894bde109`.
The existing latest pointer is byte-identical to that Pilot 1 ledger.

No durable Batch 2 directory exists, and no cumulative source-review ledger
exists. The requested Batch 2 merge has not previously run.

Pre-merge protected hashes are:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- national candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- cumulative URL-routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`

No ingestion, codification, wage extraction, wage-gap analysis or claim,
causal claim, regression, or scout-accounting output was created from
Batch 2.

## Merge boundary

This merge may create only:

- the 500-row durable Batch 2 source-review ledger, summary, and merge audit;
- a 650-row cumulative source-review ledger and summary;
- cumulative latest pointers;
- source-review dashboard/status and documentation updates.

It will not open a URL, call a network/API/model service, download or parse a
document, run OCR, run a scout or URL verifier, mutate scout accounting,
mutate durable URL-routing or metadata-triage ledgers, write to `corpus/`,
ingest, codify, extract wages, calculate wage gaps, make empirical claims,
or run regressions.
