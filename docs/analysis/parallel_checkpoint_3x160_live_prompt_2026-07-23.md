# Future Coordinator Prompt — Checkpoint-Targeted 3×160 Live Collection

Use this prompt only under separate explicit live authorization. It authorizes
collection and lane audit only; it does **not** authorize a serial accounting
merge.

Work only in:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Do not inspect remotes, push, fetch, pull, verify URLs independently, ingest,
codify, calculate wage gaps, make causal claims, or run regressions.

## Locked round

Round:

`POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23`

Read every manifest, input, audit, command preview, and merge handoff under:

`docs/analysis/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/`

Recompute and require:

- Lane 1: 160 rows; SHA-256
  `fb924eea0bee80d3073235815b475ac6a238287d49c70d7d028490802ee82a3c`
- Lane 2: 160 rows; SHA-256
  `812204917afeac05fb0e433a8439a56fa9063ea0d09603c602345cd1713450ed`
- Lane 3: 160 rows; SHA-256
  `cac770459eda2a04b9e9410a8853432e75fa0d728adb06278264352fbe2adc1d`
- 480 unique municipality IDs and 480 unique Census government IDs
- zero cross-lane overlap
- 480/480 complete five-hint sets
- current ordinary eligibility for every row
- zero covered, canonical, retry, or failure-only rows

Stop without substitution if any lock or eligibility check fails.

## Evidence gates

1. Require a clean tracked worktree and the committed planner, lane-auditor,
   lane-local export, adaptive pacing, and outer-timeout ancestry.
2. Run the stronger preflight in plan-only mode. Confirm zero external calls.
3. Under the separate live authorization, run exactly one stronger live gate
   with one diagnostic scout probe. Require the no-search control, trivial
   hosted-search call, municipality-style hosted-search call, and one-row
   scout probe to return the documented response evidence and a parseable probe
   outcome. Quarantine all probe artifacts and never count them as official.
4. Run the exact three commands in `lane_dry_run_commands.md`. For each lane,
   require 160 compact prompts, 160/160 hint matches, exact locked identities,
   adaptive `3/5/15/10` with `25/2` windows, terminal dry timing, no backend
   call, and all strict employer/unit/source/stage controls.
5. Create fresh isolated live output directories and lineage notes. Refuse to
   reuse or overwrite any prior output.

## Collection

Run the exact commands in `lane_live_commands.md`. They must retain:

- direct SDK with `gpt-5.4-nano` and low search context;
- `--state ALL --allow-mixed-states`;
- compact prompts and the locked deterministic hint CSV;
- exact max/cap 160;
- `--n-parallels 1` inside each lane;
- fixed fallback sleep five seconds and adaptive min/base/max/backoff
  `3/5/15/10`, with stability/failure windows `25/2`;
- 90-second inner and outer per-row timeout;
- zero SDK retries;
- lane-specific cost logs; and
- lane-local `--candidate-export-dir .../candidate_exports`.

Launch Lane 1. Wait exactly four minutes and confirm no immediate widespread
transport, lifecycle, artifact, parser, protected-file, or secret failure.
Launch Lane 2, wait exactly four minutes, repeat the health check, and then
launch Lane 3. Do not launch a fourth lane.

Allow a lane's built-in two-consecutive-transport-failure stop to act. Preserve
healthy sibling lanes unless failure is widespread or shared artifacts are in
danger. Never resume into the same directory. Prefer preserving partial
outputs and preparing a separate lane-specific resume recommendation unless
the active live authorization explicitly and unambiguously permits a resume.

## Audit and stop

After every lane terminates, run:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/post_lane_audit_attempt1
```

Review lane classifications, hashes, parseable/positive/empty/failure/stopped
counts, candidate rows, lane-local export byte identity, outer timeouts,
adaptive events, per-lane and combined throughput, and completed municipality
overlap. Create the collection result review, validation evidence, local
collection commit, and relay required by the live task.

Do not run queue, coverage, yield, dashboard, project-phase, or priority
builders. Stop before serial merge regardless of the audit recommendation.

This round is intended to bring official coverage close to or slightly above
approximately 2,000 only after a later successful serial merge. Once that
merge reaches the checkpoint, broad scouting should pause for verification,
extraction, ingestion, source rating, descriptive wage-growth-gap analysis,
mechanism-correlation documentation, and the planned dashboard gap filter.
Regressions remain deferred.
