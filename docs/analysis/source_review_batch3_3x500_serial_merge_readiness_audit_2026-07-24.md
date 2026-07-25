# Source-Review Batch 3 (3×500) Serial-Merge Readiness Audit

Date: 2026-07-24

## Result

**PASS.** `SOURCE-REVIEW-BATCH3-3X500-2026-07-24` is ready for one
offline serial durable source-review merge. The only new operative inputs
are:

- `tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/lane_1_live_attempt1/source_review_ledger.csv`
- `tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/lane_2_live_attempt1/source_review_ledger.csv`
- `tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/lane_3_live_attempt1/source_review_ledger.csv`

Work began at local commit
`46923a2d2dc9a5e911df31adffef1f5ea6790511`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` was present before
work and remains outside this task. Local ancestry includes `46923a2`,
`12b3f10`, `ed042c1`, `5e14f63`, `1544750`, `b94aad9`, `79df80c`, and
`e028432`.

## Locked input and identity gates

The committed Batch 3 manifest points directly to the intended live
`attempt1` directories. It selects 1,500 rows in three 500-row lanes.
Recomputed hashes match the manifest:

- Lane 1:
  `fab5d2666465460fbad18f3039b614e0793ba8179673ae55832f0302627af774`
- Lane 2:
  `54d149db261956c45c9539b077498c50a6644d02aa0f05da7038f3d3c4422c9f`
- Lane 3:
  `aa4b1afa17daf2d2eabd38d0b012df8fe864671dc52a7b20f62b8801020a4991`

For each lane, the locked input and live ledger have exact equality by both
`source_review_id` and `candidate_queue_row_id`. Across Batch 3:

- planned / live / terminal rows: 1,500 / 1,500 / 1,500;
- unique source-review IDs: 1,500;
- unique candidate-queue IDs: 1,500;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- overlap with the prior 650 durable candidate identities: 0;
- overlap with the prior 650 durable source-review IDs: 0; and
- prospective cumulative unique identities: 2,150 candidate IDs and 2,150
  source-review IDs.

The selected metadata priorities remain 1,097 p1, 403 p2, and zero p3.

## Fresh lane audit

The exact command was:

```bash
.venv/bin/python scripts/audit_source_review_lanes.py \
  --manifest docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/source_review_pilot_manifest.json \
  --output-dir tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/serial_merge_lane_audit_2026-07-24
```

The audit reports:

- Lane 1: `completed_merge_eligible`, 500/500 rows;
- Lane 2: `completed_merge_eligible`, 500/500 rows;
- Lane 3: `completed_merge_eligible`, 500/500 rows;
- `reviewed_metadata_and_artifact_saved`: 1,480;
- `download_timeout`: 16;
- `download_forbidden`: 4;
- connection errors: 0;
- content artifacts: 1,480;
- response-metadata artifacts: 1,500;
- rows with content hashes: 1,480;
- retained PDF bytes: 3,189,614,089;
- response-metadata bytes: 1,624,454;
- maximum retained PDF bytes: 10,470,269;
- content samples: 0;
- documents/PDFs parsed: 0 / 0;
- OCR runs: 0;
- artifact integrity: passed; and
- recommendation: `merge_all_source_review_lanes`.

All nonblank content paths resolve inside their live lane directories. The
fresh audit rechecked every retained artifact's path, recorded SHA-256 and
byte size.

## Existing durable layer and exactly-once gate

The prior durable source-review layer is intact:

- Pilot 1 ledger: 150 rows, SHA-256
  `2bcfe2295950f9805322d1cbbaf08051bd93b08cb632067d688ec6f894bde109`;
- Batch 2 ledger: 500 rows, SHA-256
  `8f3312613fdaf414b675900b7edc003bf6d9eff995dd7730833838f5ae93fd76`;
- cumulative/latest ledger: 650 rows, SHA-256
  `6724b1629508c50c5859fd609f7b7ed5f40449d210505e5205ab3472cade5744`;
  and
- cumulative/latest summary: SHA-256
  `3ef63c9a794aa835067fec2bb23d83c82747434eec8b889d22dee13bd37b11de`.

The cumulative and latest pairs are byte-identical. No durable Batch 3
directory exists, so the Batch 3 merge has not previously run.

The merge tool must treat the existing cumulative/latest ledger and summary
as the explicit prior durable layer. It must validate their equality before
atomically replacing the cumulative/latest pointers with the combined
Pilot 1 + Batch 2 + Batch 3 result. It must continue to fail closed if the
Batch 3 round-specific outputs already exist.

## Protected-layer baselines

Pre-merge SHA-256 values are:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- national candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- scout coverage state accounting:
  `bad2948a2990e91280b510e5d93c1ab29aa65959f83693a641a1e902836e5a21`;
- cumulative URL-routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`;
  and
- 79-file `corpus/` tree:
  `51ad68563c08cca200172d03915c4c673da3f1fcab287919e94d7df227717fa3`.

No ingestion, codification, wage extraction, wage-gap analysis or claim,
causal claim, regression, scout-accounting change, or downstream evidence
output was created from Batch 3.

## Merge boundary

The authorized merge may create or update only:

- the 1,500-row durable Batch 3 source-review ledger, summary, and merge
  audit;
- the cumulative/latest source-review ledger and summary;
- source-review dashboard/status outputs; and
- merge documentation and validation artifacts.

It will not open a URL, call a network/API/model service, download or parse a
document, run OCR, run a scout or URL verifier, mutate scout accounting,
mutate durable URL-routing or metadata-triage ledgers, write to `corpus/`,
ingest, codify, extract wage tables or values, calculate wage gaps, make
empirical or causal claims, or run regressions.

All retained rating fields remain preliminary access/artifact-metadata
signals. The merge will not promote them into final content ratings,
extraction-ready evidence, ingested sources, codified evidence, or
analysis-ready wage observations.
