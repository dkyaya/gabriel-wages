# Parallel Round 1 Live Collection Readiness Audit — 2026-07-23

Disposition: **PASS — the prepared two-lane round is eligible to proceed to the stronger preflight gate.**

This audit authorizes only the next evidence gates. It does not itself authorize a
live lane unless the stronger preflight and both fresh lane dry-runs also pass.

## Repository and lineage

- Repository: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`
- Branch: `main`
- Latest local commit before work:
  `4ee70150dd2a0c2fa5dac226f97a571ab1e50b68`
- Required ancestors confirmed with local ancestry checks:
  `4ee7015`, `3a7d762`, `6db14f0`, and `bef5077`
- Tracked worktree at start: clean
- Unrelated untracked local file: root `package-lock.json`; left untouched
- No git remotes were inspected, configured, validated, or modified.

## Manifest and locked inputs

- Round ID: `POST-PI-PARALLEL-ROUND1-2026-07-23`
- Manifest:
  `docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/parallel_round_manifest.json`
- Manifest status: exists, parses as JSON, declares two 150-row lanes, and uses
  `serial_merge_after_lane_audit`.
- Lane 1:
  - 150 data rows
  - SHA-256
    `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
  - byte-for-byte reuse of the locked Post-PI Wave 1 coordinator input
- Lane 2:
  - 150 data rows
  - SHA-256
    `f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`
- Combined:
  - 300 rows
  - 300 unique nonblank municipality IDs
  - 300 unique nonblank Census government IDs
  - zero cross-lane municipality-ID overlap
  - zero cross-lane Census-ID overlap
  - Tier 1: 300 rows

## Fresh eligibility checks

The locked rows were checked again against the current committed coverage,
failure/retry, and search-hint artifacts.

- Ordinary `future_scout_eligible_flag`: 300/300 true
- Retry rows: 0
- Failure-only rows: 0
- Successful current coverage overlap: 0
- Failure/retry priority-list overlap: 0
- Already-canonical flags: 0
- Locked `scout_coverage_status` other than `not_scouted`: 0
- Search-hint IDs present in the source hint file: 300/300
- Exact five-hint sets matching the source hint file: 300/300
- No rows were substituted.

## Live controls available

The current runner provides:

- compact prompt mode;
- deterministic municipality search hints;
- fixed and adaptive sleep/backoff controls;
- mixed-state locked-input support;
- one process/one direct-SDK request at a time within each lane;
- an SDK/http timeout plus the outer per-row `asyncio.wait_for` hard wall;
- terminal `outer_timeout` checkpointing and transport-collapse stop rules.

The outer-timeout implementation descends from commit `3a7d762`. The stopped
`bd5e259` serial output remains quarantined and is not a source of evidence.

## Isolated output paths

- Lane 1:
  `tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_live_direct_sdk_attempt1`
- Lane 2:
  `tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_live_direct_sdk_attempt1`

Both paths, both dry-run paths, both preflight paths, the diagnostic-probe path,
and the lane-audit path were absent at audit time. They are therefore fresh.

## Accounting boundary

This task is collection and lane audit only. It will not invoke the national
candidate-queue, coverage, scout-coverage, yield-learning, or dashboard builders.
Diagnostic preflight/probe artifacts will remain quarantined. No lane artifact
will be merged into national accounting in this task.

No live/API/model call, verification, ingestion, codification, wage-gap
calculation, causal analysis, accounting rebuild, push, fetch, pull, or remote
inspection occurred during this readiness audit.
