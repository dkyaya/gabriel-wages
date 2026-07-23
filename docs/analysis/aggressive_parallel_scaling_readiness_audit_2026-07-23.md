# Aggressive Parallel Scaling Readiness Audit — 2026-07-23

## Disposition

**PASS for offline framework preparation.** The next live-capacity experiment may be
prepared as three isolated lanes of 150 municipalities. A three-lane live run remains
separately gated and unauthorized by this audit. Lanes of 250–300 rows remain a
later step that requires a successful 3 × 150 collection and serial merge first.

## Repository and evidence gate

- Commit before work: `c4cf7d0de79a2a734adeb9eb03ee37ce02125e8a`
- Required ancestors confirmed: `c4cf7d0`, `4ee7015`, `3a7d762`, and `bef5077`.
- Tracked worktree before work: clean.
- Unrelated untracked item: root `package-lock.json`; it was not read into the
  implementation, changed, staged, or included.

Files used:

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- all six requested Parallel Round 1 result/merge/refresh/export-decision notes;
- the existing lane framework design, operating procedure, live prompt, serial merge
  template, planner, auditor, and synthetic tests;
- the scout runner, preflight/diagnostic scripts, runner tests, timeout-fix summary,
  speed/stability notes, and deterministic hint CSV;
- the Post-PI strategy/roadmap and current project/parallel/operations/runtime/yield
  dashboard JSON;
- the dashboard builder, yield builder, current priority tiers/top targets/failure
  file, and dashboard priority layers.

No later replacement was identified in `PROGRESS.md` or the handoff. The July 22
priority files remain the documented scheduling layer; they are deliberately
reconciled against the current July 23 coverage and failure status by the planner.

## Current checkpoint

- Official scout-covered municipalities: **1,091**
- Workflow checkpoint: **approximately 2,000**
- Remaining: **909**
- Progress: **54.5%**

Parallel Round 1 established that process-level parallel collection is viable:
two internally serialized 150-row lanes attempted 300 municipalities, produced 297
parseable outcomes, 272 candidate-positive municipalities, 25 parseable-empty
municipalities, three failure-only rows, and 763 candidate leads. The later serial
merge added 760 URL-bearing queue rows and moved coverage from 794 to 1,091.
Collection achieved 165.391 attempted rows/hour across both processes. Both lanes
were independently merge-eligible, their inputs and completed IDs did not overlap,
and one later serial accounting merge passed.

## Scaling decision

The user-approved ladder is:

1. completed: 2 × 150 and serial merge;
2. next: 3 × 150;
3. only after that collection and merge pass: 3 × 250 or 3 × 300.

The two-lane result supports a three-lane test because output isolation, per-row
outer timeouts, adaptive pacing, deterministic hints, lane auditing, and serial
accounting boundaries all worked. It does not establish unlimited hosted-search
capacity. Three live processes may increase transport contention and timeout rates.
Larger lanes also extend lifecycle exposure and make partial-lane resume lineage
more consequential.

## Limitations and controls required

- The old framework capped lanes at three but had no named size/stagger profiles.
- It generated only live commands and assumed a two-lane 2–5-minute launch pattern.
- The first parallel collection wrote timestamped candidate exports into shared
  `docs/analysis/`. They were byte-identical to lane-local `parsed_candidates.csv`
  and caused no accounting error, but the shared path creates collision/noise risk.
- Larger rounds increase hosted-search capacity risk, accounting collision risk,
  duplicate-selection risk, partial-lane failure risk, and resume-lineage complexity.
- Three-lane and larger-lane starts therefore require stronger fixed staggering,
  separate inputs/output/cost/export paths, and a combined fail-closed audit.
- Queue, coverage, yield, dashboard, and project-phase accounting must never run
  concurrently or from a lane. They remain one later coordinator-controlled serial
  merge after the round audit.
- A partial lane with parseable rows blocks merging until resume or explicit review.
  A completed-only subset can be merged only when every excluded lane has zero
  parseable rows and the user explicitly approves the changed scope.

## Boundary

This audit and the associated implementation are offline only. No live scout,
worker scout, API/model/hosted-search call, diagnostic, smoke preflight, URL access
or verification, extraction, ingestion, `gabriel.codify`, accounting promotion,
wage-gap calculation or claim, causal claim, regression, remote action, or push
occurred.
