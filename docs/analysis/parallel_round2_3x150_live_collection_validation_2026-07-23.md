# Parallel Round 2 3×150 Live Collection Validation

Date: 2026-07-23
Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

## Result

Validation passed. The three completed lane outputs are internally consistent,
isolated, and suitable for a later serial merge review. This validation does
not authorize or perform that merge.

## Commands and results

- Seven `py_compile` checks passed:
  - `scripts/gabriel_state_source_scout.py`
  - `scripts/run_scout_preflight_gate.py`
  - `scripts/audit_parallel_scout_lanes.py`
  - `scripts/prepare_parallel_scout_lanes.py`
  - `scripts/test_parallel_scout_lanes.py`
  - `scripts/test_gabriel_state_source_scout_direct_sdk.py`
  - `scripts/test_gabriel_state_source_scout_prompt.py`
- `python scripts/test_parallel_scout_lanes.py`: 7/7 synthetic,
  no-network checks passed.
- `python scripts/test_gabriel_state_source_scout_direct_sdk.py`: 26/26
  mocked/no-network checks passed, including outer timeout, adaptive stop,
  resume, and lane-local export behavior.
- `python scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 checks
  passed.
- `python scripts/validate.py`: passed; contracts 64, discourse 0, coverage 64,
  city attributes 3.
- `python ingest/test_pipeline.py`: 60/60 passed.
- `python ingest/audit_coverage.py`: 28 healthy matched pairs (10 exact,
  18 overlap), two exploratory adjacent matches, and six unmatched safety
  units.
- `git diff --check`: passed.

The command logs are under:

`tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/validation_2026-07-23/`

## Collection artifact checks

- Locked Lane 1 SHA-256:
  `320f4915a1aa487e791f67a31826572ac275edf5d4b87ecb99eec4b26279d86a`.
- Locked Lane 2 SHA-256:
  `e06f9706d69bce72cabac6f57c8581d16651d0b00ecec5752787edda5fc5500a`.
- Locked Lane 3 SHA-256:
  `501e36ff504ec2d5e3a1126eb1315db6fb31bbe5852c2be2590794661dd50665`.
- Lane 1 parsed/export SHA-256:
  `081dea566fcae6e3716e11b5b7fd3b258f1d7654d77cdfdc20059434186bc59e`.
- Lane 2 parsed/export SHA-256:
  `411254ec184354e312cd54c7290e440fdfb7075c26a7e21084c32da8d78020fa`.
- Lane 3 parsed/export SHA-256:
  `50f0a26107a08855c64a2ac6f351e9cfca303fdfab9fc63732c4fbf32ee6982c`.
- Exactly three `lane_*_live_direct_sdk_attempt1` output directories exist.
- Each lane has exactly 150 terminal timing rows and zero pending rows.
- Lane input hashes are valid; completed municipality-ID overlap is zero.
- Each lane-local timestamped export is byte-identical to
  `parsed_candidates.csv`.
- The one-row probe has a clearly named
  `quarantined_candidate_handoff.csv` and remains outside accounting.
- The stopped `bd5e259` lineage was neither read as evidence nor modified.

## Boundary checks

- No tracked diff exists under `data/contracts.csv`,
  `data/city_coverage.csv`, `corpus/`, dashboard data, the national candidate
  queue, national coverage status, or scout-yield outputs.
- No queue, coverage, yield, dashboard, project-phase, or priority builder ran.
- No fourth lane, resume lane, worker scout, or diagnostic rerun ran.
- No lane output was merged.
- No URL was independently opened or verified.
- No source verification, ingestion, `gabriel.codify`, wage-gap calculation or
  claim, causal claim, or regression occurred.
- No remote was inspected and nothing was pushed.

## Credential-pattern review

A broad masked scan found no bearer authorization header, API-key assignment,
recognized OpenAI key prefix, or legacy base62 OpenAI key shape. It initially
matched 26 `sk-...` substrings inside raw-response URLs. Masked context and
shape checks showed URL path/slug fragments such as words containing
`risk-...`, not credential values. No secret value was printed during review,
and no secret-like credential shape remains in the collected artifacts.
