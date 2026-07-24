# Future Coordinator Prompt — User-Approved Aggressive 3×300 Live Collection

Use only under separate explicit live authorization. This prompt authorizes
live collection and lane audit only; it does **not** authorize a serial
accounting merge.

Work only in:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Do not inspect remotes, push, fetch, pull, verify source URLs independently,
ingest, codify, calculate wage gaps, make causal claims, or run regressions.

## Locked round

Round:

`POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`

Read every manifest, input, audit, dry-run command, live command, and merge
handoff under:

`docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/`

Recompute and require:

- Lane 1: 300 rows; SHA-256
  `2965bd65a3f5c6fe816f52c3e9f2ce657cd9ff472db6733233bcaa4ad081fee1`
- Lane 2: 300 rows; SHA-256
  `6057e1c71b74e0342127cad32a183c2b310af704ea5ebab61e5eb7483b3896a7`
- Lane 3: 300 rows; SHA-256
  `9934026f076a978957de5ae5767eed2ff236646d384285585aeecbddcc50843a`
- 900 unique municipality IDs and 900 unique Census government IDs;
- zero cross-lane overlap;
- 900/900 complete exact five-hint sets;
- current ordinary eligibility for every row; and
- zero covered, canonical, retry, or failure-only rows.

Stop without substitution if any lock or eligibility check fails.

## Evidence gates

1. Require a clean tracked worktree and the committed planner, lane auditor,
   lane-local export support, adaptive pacing, and outer-timeout ancestry.
2. Run the stronger preflight in plan-only mode and confirm zero external calls.
3. Run exactly one authorized stronger live gate with one diagnostic scout
   probe. Require response ID/text/token evidence for no-search, trivial
   hosted-search, and municipality-style hosted-search controls, plus a
   parseable one-row scout result. Quarantine every probe artifact from official
   evidence and accounting.
4. Run the exact three commands in `lane_dry_run_commands.md`. For each lane,
   require 300 compact prompts, 300/300 hint matches, exact locked identities,
   adaptive `3/5/15/10` with `25/2` windows, terminal dry timing, no backend
   call, and all strict employer/unit/source/stage controls.
5. Create fresh isolated live directories and lineage notes. Refuse to reuse or
   overwrite an existing output.

## Collection

Run the exact commands in `lane_live_commands.md`. Retain:

- direct SDK with `gpt-5.4-nano` and low search context;
- `--state ALL --allow-mixed-states`;
- compact prompts and the locked deterministic hint CSV;
- exact max/cap 300;
- `--n-parallels 1` inside each lane;
- fixed fallback sleep five seconds and adaptive min/base/max/backoff
  `3/5/15/10`, with stability/failure windows `25/2`;
- 90-second inner and outer per-row timeout;
- zero SDK retries;
- lane-specific cost logs; and
- lane-local `--candidate-export-dir .../candidate_exports`.

Launch Lane 1. Wait exactly eight minutes and confirm there is no immediate
widespread transport, lifecycle, parser, artifact, protected-file, or secret
failure. Launch Lane 2, wait exactly eight minutes, repeat the health check, and
launch Lane 3. Scheduled offsets are minute 0/8/16. Do not launch a fourth lane.

Allow a lane's built-in two-consecutive-transport-failure stop to act. Preserve
healthy sibling lanes unless failure is widespread or shared artifacts are in
danger. Never resume into the same directory. Preserve partial outputs and
prepare a fresh lane-specific resume recommendation unless the active live
authorization explicitly permits a resume.

## Audit and stop

After every lane terminates, run:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/post_lane_audit_attempt1
```

Review lane classifications, hashes, parseable/positive/empty/failure/stopped
counts, candidate rows, lane-local export byte identity, outer timeouts,
adaptive events, per-lane and combined throughput, and completed municipality
overlap. Create the collection review, validation evidence, local collection
commit, and relay required by the live task.

Do not run queue, coverage, yield, dashboard, project-phase, or priority
builders. Stop before serial merge regardless of the recommendation.

This is the user-approved aggressive scale run. At the recent parseable rate it
may bring official coverage to roughly 2,429 after a later successful merge,
overshooting the approximately 2,000 checkpoint by roughly 429. After that
separate merge, broad scouting should pause and the project should begin
verification, extraction, ingestion, source rating, descriptive
wage-growth-gap analysis, mechanism-correlation documentation, and the planned
dashboard gap filter. Regressions remain deferred.
