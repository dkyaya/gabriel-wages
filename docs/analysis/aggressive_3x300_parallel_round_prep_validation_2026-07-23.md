# Aggressive 3×300 Parallel Round Preparation — Validation

Date: 2026-07-23

## Disposition

**PASS.** The active 3×300 plan, dashboard/status correction, documentation,
tests, and protected/accounting boundaries all pass offline validation.

Validation logs are under:

`tmp/aggressive_3x300_parallel_round_prep_validation_2026-07-23/`

## Commands and results

- Nine requested Python modules compiled successfully.
- `python scripts/test_parallel_scout_lanes.py`: **7/7 passed** using synthetic
  lane artifacts only.
- `python scripts/test_gabriel_state_source_scout_direct_sdk.py`: **26/26
  passed** using mocked/no-network backends.
- `python scripts/test_gabriel_state_source_scout_prompt.py`: **12/12 passed**.
- The exact requested `aggressive_300` planner command reproduced all three
  lane hashes.
- `python scripts/build_scout_yield_learning_report.py`: passed using existing
  committed scout artifacts.
- `python scripts/build_dashboard_data.py`: passed; output remains 51 states/DC,
  35,589 municipalities, 1,537 covered, and 3,347 candidate rows.
- `python scripts/validate.py`: passed at 64 contracts, zero discourse rows, 64
  coverage rows, and three city-attribute rows.
- `python ingest/test_pipeline.py`: **60/60 passed**.
- `python ingest/audit_coverage.py`: 28 healthy matched pairs (10 exact, 18
  overlap), two exploratory adjacent pairs, and six unmatched safety units.
- Dashboard production build: passed with 42 modules transformed.
- Every dashboard JSON file parses.
- `git diff --check`: passed.

The first frontend build itself completed successfully, but its `tee` target
used one too many parent-directory segments and could not create the log. The
build was immediately rerun with the correct repository-relative log path and
passed; the successful output is preserved.

## Locked input checks

- Total rows: **900**
- Lane rows: **300 / 300 / 300**
- Lane hashes:
  - `2965bd65a3f5c6fe816f52c3e9f2ce657cd9ff472db6733233bcaa4ad081fee1`
  - `6057e1c71b74e0342127cad32a183c2b310af704ea5ebab61e5eb7483b3896a7`
  - `9934026f076a978957de5ae5767eed2ff236646d384285585aeecbddcc50843a`
- Unique municipality IDs: **900**
- Unique nonblank Census IDs: **900**
- Cross-lane municipality/Census overlap: **0 / 0**
- Exact five-hint sets: **900/900**
- Retry/failure-only/already-covered/already-canonical rows:
  **0 / 0 / 0 / 0**
- Priority distribution: **Tier 1 606; Tier 2 294**
- Confidence distribution: **high 303; medium 248; low 349**
- Live command previews include three lane-local candidate export paths,
  compact prompts, exact hints, adaptive pacing, max/cap 300, one in-lane
  parallelism, 90-second timeout, and eight-minute starts.

## Status and protection checks

- Dashboard status is `aggressive_3x300_planned_not_run`.
- The active round ID, 900-attempt projection, expected 2,429 post-merge total,
  +429 margin, and `intentional_user_approved` overshoot marker are present.
- The 3×160 round is marked `superseded_preserved_not_active`.
- Dashboard text continues to state that candidate leads are unverified and
  wage gaps have not been calculated; no wage-gap layer is active.
- `data/contracts.csv` SHA-256 remains
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`.
- `data/city_coverage.csv` SHA-256 remains
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`.
- The combined `corpus/` digest remains
  `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a`.
- National candidate queue and municipality/state coverage hashes remain
  `e04077a9…f9af8`, `398770e8…7657`, and `6fa6615c…9435`.
- Priority, top-target, failure-retry, and hint inputs are unchanged.
- The unrelated untracked root `package-lock.json` remains untouched.

No live scout, API/model/hosted-search call, diagnostic, smoke preflight, URL
verification, extraction, ingestion, `gabriel.codify`, queue/coverage rebuild,
wage-gap calculation or claim, causal claim, regression, remote action, or
push occurred.
