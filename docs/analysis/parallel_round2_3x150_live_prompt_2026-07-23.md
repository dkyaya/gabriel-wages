# Future Coordinator Prompt — Parallel Round 2, 3 × 150 Live Collection

Use this only under separate explicit live authorization. It does not authorize a
serial accounting merge.

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
Do not inspect remotes or push.

## Locked round

Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

Read the manifest, combined audit, all three lane inputs/audits, dry-run commands,
live commands, and merge handoff under:

`docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/`

Recompute:

- Lane 1: 150 rows; SHA-256
  `320f4915a1aa487e791f67a31826572ac275edf5d4b87ecb99eec4b26279d86a`
- Lane 2: 150 rows; SHA-256
  `e06f9706d69bce72cabac6f57c8581d16651d0b00ecec5752787edda5fc5500a`
- Lane 3: 150 rows; SHA-256
  `501e36ff504ec2d5e3a1126eb1315db6fb31bbe5852c2be2590794661dd50665`

Require 450 unique municipality IDs, 450 unique Census IDs, zero overlap, current
ordinary eligibility, zero retry/failure/canonical/covered rows, and 450 complete
five-hint sets. Stop without substitution if any check fails.

## Evidence gates

1. Require a clean tracked worktree and required implementation ancestry.
2. Run the stronger preflight plan-only, then exactly one authorized live gate with
   one diagnostic probe. Require no-search, trivial hosted-search, municipality-style
   hosted-search, and parseable scout-probe evidence. Quarantine every probe artifact.
3. Run the three generated dry-run commands. Require exact prompts/identities,
   compact mode, hints 150/150 per lane, adaptive settings, terminal dry timing, and
   no backend calls.
4. Create fresh isolated live directories and lineage notes.

## Collection

Run the exact commands in `lane_live_commands.md`. They must retain:

- direct SDK, `gpt-5.4-nano`, low search context;
- compact prompts and deterministic hint CSV;
- `--n-parallels 1` within each lane;
- adaptive `3/5/15/10`, stability/failure windows `25/2`;
- inner and outer timeout 90 seconds; zero SDK retries;
- lane-specific cost logs;
- lane-local `--candidate-export-dir .../candidate_exports`.

Launch Lane 1. Wait exactly four minutes and verify no immediate widespread
transport/lifecycle failure, then launch Lane 2. Repeat the four-minute wait/check,
then launch Lane 3. Do not launch another lane. Preserve a healthy sibling when one
lane fails unless the failure is widespread or artifacts are endangered.

## Audit and stop

After every lane terminates, run the offline lane auditor. Review classifications,
hashes, timing, parseable/positive/empty/failure/stopped counts, candidate rows,
lane-local export byte identity, timeouts, pacing, combined throughput, and completed
ID overlap. Create a collection result review and relay.

Do **not** run queue, coverage, yield, dashboard, project-phase, or priority builders.
Do not verify, ingest, codify, calculate wage gaps, make causal claims, or regress.
Stop before serial merge regardless of the recommendation. A later task must apply
the three-lane serial merge template.
