# Source-Review Batch 3 (3×500) Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The repository, durable identity layer, eligible metadata pool,
bounded HTTPX implementation, and disk headroom support preparing
`SOURCE-REVIEW-BATCH3-3X500-2026-07-24`.

Work began at local commit
`12b3f109f570068e61e899b23f5359ddcbd61c78`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` was present before
work and remains out of scope. Local ancestry includes `12b3f10`,
`ed042c1`, `5e14f63`, `1544750`, `b94aad9`, `79df80c`, and `e028432`.

No Batch 3 committed input directory or transient output directory existed
before planning.

## Canonical inputs used

- cumulative metadata-triage ledger:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`
- metadata-triage summary:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_summary_cumulative.json`
- cumulative durable source-review ledger:
  `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`
- cumulative durable source-review summary:
  `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`
- Pilot 1 durable ledger:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv`
- Batch 2 durable ledger:
  `docs/analysis/source_review_ledgers/SOURCE-REVIEW-BATCH2-500-2026-07-24/source_review_ledger.csv`
- candidate queue:
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`

## Durable source-review gate

The cumulative source-review ledger contains:

- 650 rows;
- 650 unique `source_review_id` values;
- 650 unique `candidate_queue_row_id` values;
- 150 Pilot 1 rows;
- 500 Batch 2 rows;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- retained PDF artifacts: 644;
- retained PDF bytes: 1,310,753,493;
- cumulative connection errors from repaired HTTPX runs: 0;
- document/PDF parses: 0 / 0;
- OCR runs: 0.

The cumulative source-review ledger SHA-256 before work is
`6724b1629508c50c5859fd609f7b7ed5f40449d210505e5205ab3472cade5744`.
It is read-only in this collection task.

## Metadata-triage and remaining pool

The metadata-triage ledger has 4,726 rows:

- p1: 1,760;
- p2: 1,232;
- p3: 360;
- defer: 1,372;
- exclude: 2.

`content_review_download_allowed_later` applies to:

- p1: 1,760;
- p2: 1,163;
- p3: 0;
- total: 2,923.

After excluding all 650 durable source-review candidate identities and the
planner's default duplicate, oversized, blocked, defer, exclude, and lower-
disposition rows, the eligible remainder is:

- p1: 1,097;
- p2: 1,129;
- p3: 0;
- total: 2,226.

The 1,500-row selection can therefore be filled in the required order:

- all 1,097 eligible remaining p1 rows;
- 403 p2 rows;
- 0 p3 rows.

No hardcoded count will be used by the planner. These counts must be
recomputed from the locked ledgers when the plan is written.

## Storage gate

The repository volume reported:

- total volume: approximately 460 GiB;
- available space: 142,334,700 KiB, approximately 135.7 GiB;
- existing `tmp/source_review_pilots` footprint: 1,300,872 KiB,
  approximately 1.24 GiB.

Pilot 1 plus Batch 2 retained 1,310,753,493 bytes across 644 artifacts and
650 selected rows:

- about 2.04 MB per retained artifact;
- about 2.02 MB per selected row;
- projected retained Batch 3 content: approximately 3,024,815,753 bytes,
  or about 3.0 GB, before metadata and filesystem overhead.

Available space exceeds the projected content volume by more than forty
times. Disk capacity is not a blocker. The live collection should still
retain the 25 MiB per-row cap and stop if free space changes materially
before launch.

## Scale decision

The user selected three lanes of 500 rows. This is more aggressive than the
earlier four-lane planning note, but remains bounded because:

- Pilot 1 and Batch 2 achieved complete terminal coverage;
- the repaired HTTPX path had zero connection errors;
- prior artifact hashes, sizes, and lane-local paths passed;
- the new plan is capped at 1,500 locked identities;
- each lane retains concurrency four, fixed timeouts, five redirects, and a
  25 MiB ceiling;
- content samples, parsing, OCR, ingestion, codification, and wage
  extraction remain disabled.

The collection must stop before merge. A separate serial task must audit and
authorize any durable source-review update.

## Protected-state baselines

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- cumulative URL-routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`
- cumulative source-review ledger:
  `6724b1629508c50c5859fd609f7b7ed5f40449d210505e5205ab3472cade5744`

## Authorization boundary

This task may plan, dry-run, and access only the locked Batch 3 rows. It may
write only lane-local transient source-review outputs plus planning,
dashboard, validation, commit, and relay artifacts. It may not mutate a
durable source-review, URL-routing, metadata-triage, scout-accounting,
contract, coverage, or corpus layer.

No ingestion, `gabriel.codify`, wage extraction, wage-gap calculation,
wage-gap or causal claim, or regression is authorized.
