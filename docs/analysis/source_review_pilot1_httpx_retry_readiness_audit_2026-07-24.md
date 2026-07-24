# Source-Review Pilot 1 HTTPX Retry Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The repaired-client retry may proceed against exactly the two
locked 75-row Pilot 1 inputs. The retry remains a live collection and audit
task only: no durable source-review merge or larger batch is authorized.

Work began at local commit
`1544750f857bc2da8724a7dd48dd43b689532a6e`. The tracked worktree was clean.
The unrelated untracked root `package-lock.json` was present before work and
is out of scope. Local ancestry contains `1544750`, `d97f5e4`, `a0c2445`,
`b94aad9`, `79df80c`, and `e028432`.

## Preserved original attempt

The original failed `d97f5e4` output directories exist and will not be
overwritten:

- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_live_attempt1`
- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_2_live_attempt1`

Their ledgers contain 150 terminal rows: 149
`download_connection_error` outcomes and one `download_forbidden` outcome,
with zero retained content artifacts and zero content hashes. Baseline tree
digests are:

- Lane 1: `b84e9fb3bc7a162cb035cffe8e8a8ecaf8c820bce1bf1c1bda278ec0fe32c356`
  across 78 files.
- Lane 2: `e977f0c9843f8bdb507e596c5c8a333b3fdce18b3f33866faa8ef36568f25aab`
  across 78 files.

The original outcomes remain immutable diagnostic provenance and are not
merge inputs for this task.

## Diagnosis and probe gate

The connection diagnosis identified a source-review-only custom `urllib`
transport mismatch and replaced it with a bounded verifier-compatible
`httpx` client. Proxy inheritance remains disabled by default and
`--trust-env-proxy` will not be passed.

The preserved ten-row diagnostic probe exists with tree digest
`2fba18b476a0f3594744889ea2ec141f23359df2af53cc32ac817c67151d13b5`
across 22 files. It contains:

- 10 terminal rows;
- nine `reviewed_metadata_and_artifact_saved` outcomes;
- one repeated `download_forbidden` outcome;
- zero connection errors;
- nine lane-local content artifacts; and
- nine matching content hashes.

This materially passes the transport-repair gate while remaining too small
to authorize scaling.

## Locked inputs

The manifest selects exactly 150 rows in two lanes of 75 rows each.
Recomputed input hashes match the locked values:

- Lane 1:
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`
- Lane 2:
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`

Fresh output directories do not exist:

- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_live_attempt2_httpx`
- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_2_live_attempt2_httpx`

No durable `docs/analysis/source_review_ledgers/` layer exists for Pilot 1.

## Retry limits

The authorized retry is limited to:

- exactly the locked 150 identities, split 75/75;
- two lanes only, with Lane 2 launched only after Lane 1 establishes
  checkpointed outputs;
- concurrency four per lane;
- total/connect/read timeouts of 30/8/20 seconds;
- five redirects;
- 26,214,400 retained bytes per row;
- verifier-compatible `httpx` with environment proxy inheritance off;
- lane-local artifacts and metadata;
- content samples off;
- no PDF parsing, full-text extraction, or OCR.

The retry does not authorize a durable source-review merge; a 500-, 750-, or
1,000-row source-review batch; scout or URL-verification work; scout
accounting updates; routing or metadata-triage ledger mutation; corpus
writes; ingestion; `gabriel.codify`; wage extraction; wage-gap calculations
or claims; causal claims; or regressions.
