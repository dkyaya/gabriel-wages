# Parallel Scout Lane Framework Validation

Date: 2026-07-23

Disposition: **PASS — offline framework, two-lane plan, synthetic auditor, dashboard note, and future three-lane extension validated.**

## Compilation and unit tests

- Six requested Python compilation checks passed:
  - `scripts/prepare_parallel_scout_lanes.py`
  - `scripts/audit_parallel_scout_lanes.py`
  - `scripts/test_parallel_scout_lanes.py`
  - `scripts/gabriel_state_source_scout.py`
  - `scripts/test_gabriel_state_source_scout_direct_sdk.py`
  - `scripts/test_gabriel_state_source_scout_prompt.py`
- Parallel-lane synthetic suite: 7/7 reported checks passed.
- Direct-SDK fully mocked/no-network suite: 25/25 reported checks passed.
- Prompt suite: 12/12 reported checks passed.

The new lane tests use only temporary local CSV, JSON, and Markdown fixtures. They do not import or invoke a queue, coverage, yield, dashboard, API, or model client. The direct-SDK suite enters production lifecycle paths under fake clients only; no real credential or network call occurs.

## Required two-lane plan

The exact requested plan-only command passed and was rerun deterministically:

- Round: `POST-PI-PARALLEL-ROUND1-2026-07-23`
- Status: `planned_not_run`
- External calls: 0
- Dry runs: 0
- Lane 1: 150 rows; SHA-256 `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Lane 1 is byte-identical to the existing locked Post-PI Wave 1 coordinator input.
- Lane 2: 150 rows; SHA-256 `f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`
- Cross-lane municipality-ID overlap: 0.
- Cross-lane nonblank Census-ID overlap: 0.
- Missing Census IDs: 0.
- Exact complete five-hint sets: 300/300.
- Covered, canonical, retry, and failure-only rows: 0.
- Priority tier: Tier 1 for all 300 rows.

Lane 2 was selected deterministically from current ranked targets after joining the full priority, current coverage, canonical, failure/retry, and hint authorities and excluding Lane 1. No ad hoc row was substituted.

## Command and audit framework

Generated lane commands contain:

- direct SDK;
- state `ALL` and mixed-state authorization;
- exact 150-row max and hard cap;
- `--n-parallels 1` within each lane;
- compact prompt mode;
- deterministic search hints;
- adaptive settings `3/5/15/10/25/2`;
- 90-second SDK and runner-level outer timeout;
- zero SDK retries;
- unique lane output and cost-log paths.

The command and operating documents require one stronger preflight before the round, a 2–5-minute Lane 2 stagger, no more lanes than authorized, a cross-lane widespread-failure stop, artifact preservation, and no per-lane accounting or commit.

The real planned-round audit currently returns `do_not_merge_until_resume_or_review` with both lanes `not_started`, which is the correct fail-closed result before live execution.

Synthetic auditor coverage proves:

- two complete disjoint lanes → `merge_all_lanes`;
- duplicate municipality IDs across lanes → failure;
- one complete plus one zero-parseable failed lane → `merge_completed_lanes_only_with_user_approval`;
- a parseable partial lane → `do_not_merge_until_resume_or_review`;
- missing artifacts → `do_not_merge_until_resume_or_review`;
- candidate totals and stopped-before-request totals are exact;
- only the three audit/recommendation files are written; no queue, coverage, or dashboard file is created.

## Future three-lane support

A separate offline plan-only validation under `/private/tmp` prepared three 150-row lanes with:

- 450 unique municipality IDs;
- zero municipality overlap;
- 450 unique nonblank Census IDs;
- zero Census overlap;
- no external calls.

This proves planner/schema extension support. It does not authorize three-lane live execution, which remains deferred until the initial two-lane round demonstrates stable capacity and clean serial accounting.

## Dashboard and project validation

- `python scripts/build_dashboard_data.py`: passed.
- Dashboard totals remain 51 states/DC, 35,589 municipalities, 794 scout-covered, and 1,602 candidate rows.
- All dashboard JSON files parse.
- `parallel_scout_status.json` reports:
  - `parallel_mode_status=planned_not_run`;
  - two initial lanes;
  - three future lanes;
  - `serial_merge_after_lane_audit`;
  - no parallel live scout executed.
- The Scout Operations panel contains one concise planned-lane note and preserves candidate-stage caveats.
- `npm run build`: passed with 42 modules transformed.

## Repository and corpus validation

- `python scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- `python ingest/test_pipeline.py`: passed 60/60.
- `python ingest/audit_coverage.py`: 19 cities, 28 healthy matched pairs (10 exact and 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.
- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/`: unchanged.
- National candidate queue and scout coverage inputs: unchanged.
- National priority inputs and methodology: unchanged.
- Neither planned lane live output directory exists.

## Boundary

No live or worker scout, hosted-search diagnostic, smoke preflight, API/model/hosted-search call, URL access, source verification, extraction, ingestion, `gabriel.codify`, candidate promotion, national queue/coverage rebuild, wage-gap calculation or claim, causal claim, regression, remote operation, or push occurred.

Command logs are preserved under:

`tmp/parallel_scout_lane_framework_validation_2026-07-23/`
