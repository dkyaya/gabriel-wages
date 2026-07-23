# Coordinator-Safe Parallel Scout Lane Framework

Date: 2026-07-23

Status: **offline framework design for an initial two-lane round; live execution not yet run.**

## Architecture

```text
one audited round manifest
          |
          +--> Lane 1: locked 150-row input -> isolated sequential live output
          |
          +--> Lane 2: locked 150-row input -> isolated sequential live output
                                     |
                       one post-lane offline audit
                                     |
                     one separately authorized serial merge
                                     |
                queue -> coverage -> yield -> dashboard
```

The unit of parallelism is an isolated lane process, not a concurrent request inside the scout runner. Every lane keeps `--n-parallels 1`.

## Concepts

- **Parallel round:** one coordinated collection event governed by a single immutable manifest and a fixed authorized lane count.
- **Lane:** one internally serialized scout process with a unique ID, input, output, cost log, and lineage.
- **Lane input CSV:** an immutable, hash-locked list of ordinary eligible municipalities assigned to exactly one lane.
- **Lane output directory:** a fresh path writable only by its lane process; it contains prompt, raw, timing, parse, cost, and lifecycle artifacts.
- **Lane manifest:** the round-level JSON authority for input paths/hashes, row counts, output paths, controls, isolation policy, and accounting prohibition.
- **Lane dry-run:** an offline prompt/artifact review for exactly one lane. It never authorizes another lane and never calls a backend.
- **Lane live collection:** a separately authorized direct-SDK process that writes only its isolated artifacts.
- **Lane result review:** a human-readable interpretation of one lane’s terminality, parseability, failures, stopped rows, candidates, and limitations.
- **Merge eligibility:** a lane-level determination that the input hash matches, required artifacts exist, the process is terminal, every input row has a coherent terminal outcome, and no stopped-before-request or lifecycle-loss condition makes the lineage incomplete.
- **Serial accounting merge:** one coordinator-controlled rebuild of shared national queue/coverage followed by yield/dashboard refresh, after the combined lane audit permits it.

## Supported modes

### Initial mode

- 2 lanes × 150 municipalities.
- 300 disjoint ordinary discovery targets.
- Each lane is internally sequential.
- Lane 2 starts 2–5 minutes after Lane 1.
- One stronger preflight gate precedes the round.

This is the maximum supported live mode until a complete two-lane round demonstrates stable capacity and clean accounting lineage.

### Future mode

- 3 lanes × 150 municipalities.
- Enabled by the planner and manifest schema, but not operationally recommended until the two-lane experiment completes without widespread transport collapse, artifact loss, overlap, or merge ambiguity.
- A three-lane authorization must reassess hosted-search capacity and stagger all starts.

## Non-negotiable rules

1. Each lane has a separate locked input CSV.
2. Each lane has a unique `lane_id`.
3. Each lane has a fresh, nonoverlapping output directory and cost log.
4. Municipality IDs cannot overlap across lanes.
5. Nonblank Census government IDs cannot overlap across lanes.
6. Existing coverage, canonical municipalities, retries, and failure-only targets are excluded from ordinary new-lane selection.
7. Each lane uses compact prompts, exact deterministic hints, adaptive sleep/backoff, and the tested outer timeout.
8. Each lane writes only to its own output directory while collecting.
9. Lane processes never rebuild queue, coverage, yield, priority, or dashboard outputs.
10. Lane processes never edit project logs or commit.
11. One final offline auditor reviews all lanes together.
12. One later, separately authorized serial merge owns every shared accounting write.

## Manifest contract

The round manifest records:

- schema version and round ID;
- `planned_not_run` status and plan-only provenance;
- lane count and rows per lane;
- supported initial/future lane limits;
- source priority, full-priority, coverage, failure, and hint files with hashes;
- per-lane ID, locked CSV path, SHA-256, row count, states, output path, cost-log path, and whether the input was copied unchanged;
- required direct-SDK controls;
- explicit accounting/commit prohibitions;
- combined municipality/Census uniqueness and hint-completeness results.

The manifest contains no credential value and grants no live authorization.

## Failure policy

### Both lanes complete and merge-eligible

Recommendation: `merge_all_lanes`.

The later serial merge must recheck input hashes, cross-lane identity uniqueness, artifact completeness, and accounting baselines before rebuilding shared outputs exactly once.

### One lane complete; one lane fails with zero parseable rows

Recommendation: `merge_completed_lanes_only_with_user_approval`.

The completed lane may be independently coherent, but merging only one lane changes the planned round scope. The auditor recommends rather than acts. Explicit user approval and a documented decision are required before the serial accounting step.

### One lane is partial with parseable rows

Recommendation: `do_not_merge_until_resume_or_review`.

Preserve the valid partial artifacts, but do not cherry-pick them automatically. Audit safe resume eligibility in a fresh lane-specific directory or obtain an explicit decision about the partial lineage.

### Both lanes are partial

Recommendation: `do_not_merge_until_resume_or_review`.

No accounting builder runs. Review each lineage independently and preserve the round manifest.

### Transport collapse in one lane

The affected lane applies its own two-consecutive no-evidence stop. If it has zero parseable rows and the other lane completed, use the completed-only-with-approval recommendation. If it has any parseable partial output or stopped rows after valid rows, withhold the entire round pending resume/review.

### Transport collapse in both lanes

Recommendation: `do_not_merge_until_resume_or_review`. Stop all activity, preserve artifacts, and investigate capacity before another live authorization.

### Missing or inconsistent artifacts

Recommendation: `do_not_merge_until_resume_or_review`. Missing metadata/timing, an input-hash mismatch, cross-lane completed-ID overlap, or nonterminal lifecycle state fails closed.

## Conservative first-run merge rule

The first parallel round merges automatically only at the recommendation level when both lanes are complete and independently merge-eligible. The auditor itself never runs builders. Completed-lane-only accounting always requires explicit user approval. Any parseable partial lane blocks automatic merge.

## Accounting boundary

The post-lane auditor writes only:

- `parallel_lane_audit_summary.json`;
- `parallel_lane_audit_report.md`;
- `merge_recommendation.md`.

It never invokes or imports a queue, coverage, yield, dashboard, priority, ingestion, verification, or codification builder. The later serial merge prompt is a separate task boundary.

## Interpretation boundary

Parallelism changes scheduling and elapsed collection time, not evidence status. Candidate rows remain unverified leads. Lane throughput and failure rates are operational diagnostics. No parallel plan, manifest, or completed scout lane supports a wage-gap, mechanism, state, or causal finding.
