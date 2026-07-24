# Checkpoint-Targeted 3×160 Readiness Audit

Date: 2026-07-23

Round: `POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23`

## Disposition

**PASS — current accounting and the refreshed priority layer support an
offline, checkpoint-targeted three-lane plan. No live action is authorized by
this audit.**

Work began at
`8b653b2ba14fc5e6b2a96a523ed3fe6100a780a8` on `main`. The tracked worktree
was clean. The unrelated untracked root `package-lock.json` was left untouched.
Exact local ancestry confirms that HEAD includes `8b653b2`, `4f9c865`,
`d015800`, `c4cf7d0`, and `3a7d762`.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- the five requested Parallel Round 2 merge/readiness/checkpoint documents
- `docs/analysis/aggressive_parallel_scaling_framework_design_2026-07-23.md`
- `docs/analysis/aggressive_parallel_scaling_operating_procedure_2026-07-23.md`
- `docs/analysis/parallel_round2_3x150_live_prompt_2026-07-23.md`
- `docs/analysis/aggressive_3x300_future_live_prompt_template_2026-07-23.md`
- `docs/analysis/parallel_scout_serial_merge_prompt_template_2026-07-23.md`
- `scripts/prepare_parallel_scout_lanes.py`
- `scripts/audit_parallel_scout_lanes.py`
- `scripts/test_parallel_scout_lanes.py`
- `scripts/gabriel_state_source_scout.py`
- `scripts/run_scout_preflight_gate.py`
- `docs/analysis/direct_sdk_outer_timeout_fix_summary_2026-07-23.md`
- `docs/analysis/scout_speed_stability_implementation_summary_2026-07-22.md`
- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv`
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv`
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv`
- `docs/analysis/state_priority_summary_2026-07-22.csv`
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`
- `docs/analysis/municipality_search_hints_2026-07-22.csv`
- current dashboard priority, target, project-phase, parallel-status, and
  scout-operations JSON

These are the current canonical equivalents identified by the progress and
handoff logs.

## Current accounting and strategy

- Scout-covered municipalities: **1,537 / 2,000**
- Progress: **76.85%**
- Remaining: **463**
- Candidate-positive: **1,267**
- Parseable-empty: **270**
- Failure-only: **27**
- URL-bearing candidate queue rows: **3,347**

Parallel Round 2 completed 450 attempts with 446 parseable outcomes, 383
candidate-positive municipalities, 63 parseable-empty municipalities, four
failure-only rows, and 985 URL-bearing leads. All three lanes were
merge-eligible and entered accounting through one later serial merge.

The unchanged priority methodology was refreshed after that merge:

- Future-scout eligible: **34,046**
- Tier 1 eligible: **628**
- Tier 2 eligible: **3,420**
- Failure-only retry targets: **27**

## Why 3×160

Three lanes × 160 rows provides 480 attempts against a remaining distance of
463. At the recent parseable rate of 446/450 (99.111%), the expected outcome is
approximately 476 newly covered municipalities and approximately **2,013**
covered after a later successful serial merge. If all 480 parse, the maximum
planning total is 2,017.

By contrast, 3×300 provides 900 attempts. At the same recent rate it would add
about 892 covered municipalities and reach roughly 2,429, overshooting the
workflow checkpoint by about 429. The smaller plan is therefore better aligned
with the instruction to pause broad discovery near 2,000.

## Controls, constraints, and risks

- Ordinary discovery only; all 27 failure-only/retry rows stay separate.
- Current successful coverage and canonical rows are excluded.
- Municipality and Census IDs must be unique within and across lanes.
- Every row must have all five deterministic hints.
- Each lane remains internally serialized with compact prompts, adaptive
  pacing, the outer timeout, a unique output directory and cost log, and a
  lane-local candidate export.
- Live collection, lane audit, and serial accounting remain separate
  authorization boundaries.
- The projection is not a guarantee. Actual transport failures, parseability,
  partial-lane results, and the conservative merge policy may leave coverage
  below or slightly above the checkpoint.
- Rank slicing concentrates some states, especially Ohio and California, but
  does not create identity overlap. This is an operational capacity concern to
  monitor during a later live task, not an eligibility failure.
- No future source-discovery round should be presumed after a successful merge
  reaches approximately 2,000.

No live scout, worker scout, API/model/hosted-search call, diagnostic,
preflight, URL verification, ingestion, `gabriel.codify`, accounting rebuild,
wage-gap calculation or claim, causal claim, or regression occurred in this
readiness work.
