# Source-Review Batch 2 (500 Rows) Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The repository, durable Pilot 1 ledger, metadata-triage pool, disk
headroom, and source-review safeguards support preparing a locked 500-row
follow-on batch. Live access remains conditional on a deterministic plan,
exact Pilot 1 identity exclusion, two complete offline dry runs, and a clean
dry-run lane audit.

Work began at local commit
`ed042c126dfa3f1f869acbedf013da508144d9e5`. The tracked worktree was clean.
The unrelated untracked root `package-lock.json` was present before work and
remains out of scope. Local ancestry includes `ed042c1`, `5e14f63`,
`1544750`, `b94aad9`, `79df80c`, and `e028432`.

Neither the committed Batch 2 planning directory nor its temporary execution
directory existed before work.

## Durable Pilot 1 gate

The operative input used for exclusion is:

`docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv`

It has:

- durable rows: 150;
- unique `candidate_queue_row_id` values: 150;
- `reviewed_metadata_and_artifact_saved`: 149;
- `download_forbidden`: 1;
- connection errors: 0;
- durable stage `bounded_artifact_review_not_parsed`: 150;
- retained content artifacts / hashes: 149 / 149;
- retained content bytes: 301,970,460;
- documents/PDFs parsed: 0 / 0;
- OCR runs and content samples: 0 / 0.

These 150 candidate identities must be absent from Batch 2. The original
transport-failed Pilot 1 attempt and the diagnostic probe are not exclusion
or planning inputs because the durable operative ledger already represents
the locked Pilot 1 universe exactly once.

## Metadata-triage pool

The planning input is:

`docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`

Computed counts are:

- durable metadata-triage rows: 4,726;
- p1 rows: 1,760;
- all `content_review_download_allowed_later` rows: 2,923;
- raw p1, high-priority, CBA-labeled, reachable-PDF/document,
  download-allowed rows before prior-review exclusion: 1,760;
- Pilot 1 overlap with that eligible pool: 150;
- raw remaining rows after Pilot 1 exclusion: 1,610;
- duplicate-group rows excluded by the default source-review safety filter:
  13;
- final eligible pool after duplicate and prior-review exclusions: 1,597.

The 1,597 final eligible rows are all scheduled, CBA-labeled,
`application/pdf`, high-priority metadata candidates. They span 36 states
before selection. These are selection metadata, not confirmed
document-content findings.

## Why 500 is the next scale

Pilot 1 demonstrated complete terminal coverage, clean bounded HTTPX
transport, 149/150 artifact yield, lane-local artifacts, matching hashes and
sizes, and a low immediate transport/manual-review burden. A 500-row batch is
large enough to test storage, host diversity, artifact integrity, and rating
stability beyond the pilot while retaining two manageable 250-row
checkpoints and aggregate concurrency of eight.

Pilot 1 retained 301,970,460 bytes for 150 selected rows. Simple linear
capacity projections are:

- 500 selected rows: approximately 1,006,568,200 bytes;
- 750 selected rows: approximately 1,509,852,300 bytes;
- 1,000 selected rows: approximately 2,013,136,400 bytes.

The local volume has approximately 137 GiB free, so the bounded 500-row
projection is operationally feasible without changing byte ceilings or
writing to `corpus/`.

## Why 750/1,000 remain deferred

Pilot 1 did not parse PDFs, detect text layers or page counts, confirm
document relevance, confirm municipality/employer/unit matches, or evaluate
wage or mechanism content. Its ratings remain preliminary access/artifact
signals. Artifact volume is already substantial, and speed alone cannot
establish content-review usefulness. A clean 500-row collection and a
separate serial merge/relay review are required before considering 750; 1,000
requires an additional artifact-volume and rating-usefulness gate.

## Protected baselines

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- cumulative routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`
- latest durable source-review ledger:
  `2bcfe2295950f9805322d1cbbaf08051bd93b08cb632067d688ec6f894bde109`

## Authorization boundary

This task may plan, dry-run, and—only after all gates pass—open exactly the
locked 500 Batch 2 URLs in two bounded lanes. It must stop before durable
Batch 2 merge. It must not run scouts or broader URL verification; mutate
scout, routing, metadata-triage, or durable source-review accounting; write
to `corpus/`; parse PDFs; run OCR; ingest; codify; extract wage values;
calculate or claim wage gaps; make causal claims; run regressions; inspect
remotes; or push.
