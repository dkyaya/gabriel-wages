# Aggressive 3×300 Supersession and Readiness Audit

Date: 2026-07-23

Active round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`

Superseded round: `POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23`

## Disposition

**PASS — the refreshed accounting and priority layers support an offline,
live-ready 3×300 plan. No dry run, preflight, or live collection is authorized
by this audit.**

Work began at
`67a41c40b48c693da893d82809ad84e827bd2d8a` on `main`. The tracked worktree
was clean, and exact local ancestry confirms that HEAD includes `67a41c4`,
`8b653b2`, `d015800`, `4f9c865`, and `3a7d762`. The unrelated untracked root
`package-lock.json` was reported and left untouched.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- the five requested Parallel Round 2 merge, checkpoint, priority, and
  aggressive-readiness documents
- all requested preserved 3×160 planning documents and the complete
  `POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/` directory
- the aggressive scaling design, operating procedure, live template, and serial
  merge template
- the complete
  `POST-PI-PARALLEL-AGGRESSIVE-3X300-FEASIBILITY-2026-07-23/` feasibility
  directory
- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv`
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv`
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv`
- `docs/analysis/state_priority_summary_2026-07-22.csv`
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`
- `docs/analysis/municipality_search_hints_2026-07-22.csv`
- current dashboard priority, targets, project-phase, parallel-status, and
  operations JSON
- the requested planner, auditor, scout runner, preflight, dashboard, and yield
  builder scripts
- the direct-SDK outer-timeout and scout speed/stability implementation notes

These are the current canonical equivalents identified by `PROGRESS.md` and
`chatgpt_handoff_latest.md`.

## Current position

- Scout-covered municipalities: **1,537 / 2,000**
- Progress: **76.85%**
- Remaining: **463**
- Candidate-positive municipalities: **1,267**
- Parseable-empty municipalities: **270**
- Failure-only/retry municipalities: **27**
- URL-bearing unverified queue rows: **3,347**

The unchanged priority methodology was refreshed at the Round 2 merge:

- Future-scout eligible: **34,046**
- Tier 1 eligible in the priority summary: **628**
- Tier 2 eligible: **3,420**
- Failure-only retry targets: **27**

The ordinary planner excludes 22 Tier 1 rows that remain marked
retry/failure-only in the refreshed operational file, leaving 606 ordinary
Tier 1 rows for this plan before deterministic Tier 2 continuation.

## Supersession decision

The 3×160 plan was prepared at `67a41c4` to land close to the checkpoint. The
user has now explicitly selected 3×300 and accepted the likely overshoot.
The 3×160 inputs, audits, and prompts remain preserved as historical planning
artifacts, but they are not the active next round and must not be launched
unless the user later reverses this decision.

Three lanes × 300 provides 900 attempts. Applying the recent 446/450 parseable
rate projects approximately 892 new successful coverage outcomes, approximately
2,429 covered after a later successful serial merge, and an approximate
checkpoint margin of **+429**. If all 900 rows parse, the maximum planning total
is 2,437. These are operational projections, not live evidence or accounting.

## Controls, constraints, and risks

- Ordinary discovery only; all 27 failure-only/retry rows stay separate.
- Current covered and canonical rows are excluded.
- Municipality and Census IDs must be unique within and across all lanes.
- Every row must carry all five deterministic hints.
- Each lane remains internally serialized with compact prompts, adaptive
  pacing, the 90-second outer timeout, a unique output/cost path, and a
  lane-local candidate export.
- Starts are scheduled at minute 0, 8, and 16.
- Larger lanes increase wall time, hosted-search capacity exposure, partial-lane
  lineage risk, and the cost of a later resume decision.
- Live collection and lane audit remain separate from national accounting.
- Queue, coverage, yield, dashboard, and priority builders must not run inside a
  lane or during the collection-only task.
- After a successful serial merge exceeds approximately 2,000, broad scouting
  should pause for the downstream cycle.

No live scout, worker scout, API/model/hosted-search call, diagnostic,
preflight, source URL verification, extraction, ingestion, `gabriel.codify`,
queue/coverage rebuild, wage-gap calculation or claim, causal claim, or
regression occurred.
