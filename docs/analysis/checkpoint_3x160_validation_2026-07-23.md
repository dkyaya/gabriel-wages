# Checkpoint 3×160 Preparation Validation

Date: 2026-07-23

## Result

**PASS.** The checkpoint-targeted round is deterministic, current-eligible,
nonoverlapping, and offline-only. The repository `python` shim worked; the
virtual-environment fallback was not needed.

## Commands and results

- Nine requested `py_compile` checks passed.
- `scripts/test_parallel_scout_lanes.py`: 7/7 synthetic, no-network checks
  passed.
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`: 26/26 mocked,
  no-network checks passed.
- `scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 passed.
- The exact 3×160 planner command reproduced the same three locked hashes.
- Existing-data yield learning rebuilt at six reviewed waves/rounds, with
  official accounting unchanged.
- Dashboard data rebuilt at 51 states/DC, 35,589 municipality/township rows,
  1,537 covered municipalities, and 3,347 candidate rows.
- `scripts/validate.py`: passed at 64 contracts, zero discourse rows, 64
  coverage rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60/60 passed.
- `ingest/audit_coverage.py`: 28 healthy matched pairs (10 exact and 18
  overlap), two exploratory adjacent matches, and six unmatched safety units.
- Dashboard production build: passed with 42 modules transformed.
- `git diff --check`: passed.

Logs:

`tmp/checkpoint_3x160_parallel_round_prep_validation_2026-07-23/`

## Structural assertions

- Lane 1: 160 rows; SHA-256
  `fb924eea0bee80d3073235815b475ac6a238287d49c70d7d028490802ee82a3c`.
- Lane 2: 160 rows; SHA-256
  `812204917afeac05fb0e433a8439a56fa9063ea0d09603c602345cd1713450ed`.
- Lane 3: 160 rows; SHA-256
  `cac770459eda2a04b9e9410a8853432e75fa0d728adb06278264352fbe2adc1d`.
- Total rows: 480.
- Unique municipality IDs: 480.
- Unique Census IDs: 480.
- Cross-lane overlap: zero.
- Priority tier: Tier 1 for all 480.
- Complete exact hint sets: 480/480.
- Retry, failure-only, covered, and canonical rows: zero.
- Confidence: 187 high, 94 medium, and 199 low.
- All live command previews include compact prompts, exact hints, adaptive
  pacing, 90-second timeout, one in-lane parallelism, exact cap 160, and
  lane-local candidate exports.
- The future live and serial-merge prompts exist and preserve the
  collection/accounting boundary.

## Dashboard, accounting, and protection

- The dashboard labels the round `checkpoint_3x160_planned_not_run`.
- Official accounting remains 1,537 covered, 1,267 candidate-positive, 270
  parseable-empty, 27 failure-only, and 3,347 queue rows.
- All dashboard JSON parses.
- National queue and coverage files have no diff.
- Refreshed priority input files have no diff.
- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` have no diff.
- Dashboard text does not claim that wage gaps exist.

No live/API/model/hosted-search call, diagnostic, preflight, URL verification,
source ingestion, `gabriel.codify`, candidate promotion, wage-gap calculation
or claim, causal claim, regression, remote action, or push occurred.
