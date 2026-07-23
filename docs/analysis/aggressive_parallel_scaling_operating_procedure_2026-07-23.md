# Aggressive Parallel Scout Scaling Operating Procedure — 2026-07-23

## 1. Prepare and lock

Run the offline planner with a named profile. For the next test use
`standard_150`, which produces three 150-row CSVs, individual audits, a combined
no-overlap audit, manifest, dry-run commands, live commands, and merge handoff.
Recompute all hashes and reconcile every row against current coverage, canonical
status, and failure/retry exclusions before live authorization.

The generated Round 2 manifest schedules Lane 1 at minute 0, Lane 2 at minute 4,
and Lane 3 at minute 8. Do not compress the stagger. For `aggressive_300`, use at
least eight minutes between starts; increase to ten minutes when recent transport
health is uncertain.

## 2. Gate and dry-run

Under a separate live task, run one stronger preflight gate and quarantine its
probe. Stop if any required control lacks response evidence or the one-row scout
probe is not parseable. Then run all lane dry-runs offline and require:

- exact locked row identities and counts;
- compact prompt mode;
- five hints per municipality;
- mixed-state authorization and lane cap;
- adaptive sleep metadata;
- strict employer/unit/source/no-public-records controls;
- complete dry timing with no backend call.

## 3. Launch and monitor 3 × 150

Start Lane 1 from the coordinator. After four minutes and a clean lifecycle check,
start Lane 2. Four minutes later, repeat the check and start Lane 3. Each process
must use its generated input, output directory, cost log, and
`candidate_exports/` directory. Each remains internally serialized.

Monitor process liveness, artifact checkpoints, row timing, outer timeouts,
consecutive transport failures, adaptive backoff, parsing stability, and protected
paths. Never start a fourth lane. Let a lane’s built-in collapse rule terminate that
lane. Stop all lanes only for widespread transport failure, systematic parsing
failure, artifact/lifecycle loss, protected-file mutation, or secret exposure.

## 4. Audit before any merge

After all processes terminate, run `scripts/audit_parallel_scout_lanes.py` against
the manifest. Require lane-local candidate exports to exist for every lane with
parseable outcomes and to match `parsed_candidates.csv` byte-for-byte. Review
per-lane classifications, throughput, timeout/backoff events, stopped rows, input
hashes, and completed-ID overlap.

- Merge all only after a separate serial task when all three lanes pass.
- If a lane is partial with parseable rows, resume or decide its disposition first.
- If a lane has zero parseable rows while siblings complete, preserve everything
  and request explicit approval before considering a completed-only merge.

Never run shared builders from the collection task or a lane process.

## 5. Advance—or stop

A successful 3 × 150 collection is not enough by itself; its later serial merge and
dashboard/checkpoint refresh must also pass. Then:

- choose `aggressive_250` when timeout/failure/backoff rates were elevated;
- choose `aggressive_300` only for a clean, balanced result with stable route health;
- retain three lanes and increase stagger with lane size;
- reevaluate the official checkpoint before authorizing the larger round.

At the current 1,091 coverage count, a fully parseable 3 × 300 round would exceed
the approximate 2,000 checkpoint once merged. It is a feasibility profile, not the
next live authorization. Stop broad scouting at or above the checkpoint and begin
the downstream verification-to-descriptive-analysis cycle.

## Candidate export behavior

Serial runs remain backward compatible: without `--candidate-export-dir`, the
timestamped handoff goes to `docs/analysis/`. Every generated parallel live command
sets that flag to its own lane’s `candidate_exports/` directory. This prevents
cross-lane shared-path noise while preserving the durable handoff and the canonical
lane-root `parsed_candidates.csv`.
