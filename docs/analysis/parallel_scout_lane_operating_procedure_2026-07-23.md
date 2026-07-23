# Parallel Scout Lane Operating Procedure

Date: 2026-07-23

Scope: coordinator-safe collection with two isolated, internally serialized 150-row lanes. This procedure is not live authorization.

## 1. Prepare the round offline

Start from clean tracked `main`, record unrelated untracked files, and confirm the current coverage, canonical, retry/failure, priority, and hint artifacts. Run:

```bash
python scripts/prepare_parallel_scout_lanes.py \
  --output-dir docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23 \
  --round-id POST-PI-PARALLEL-ROUND1-2026-07-23 \
  --num-lanes 2 \
  --rows-per-lane 150 \
  --existing-lane-input docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv \
  --priority-targets-csv docs/analysis/national_priority_tier_top_targets_2026-07-22.csv \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --plan-only
```

`--plan-only` writes inputs, hashes, audits, a manifest, and command previews. It never runs a scout or dry run. Require:

- exact Lane 1 hash `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`;
- exactly 150 rows per lane;
- no municipality or nonblank Census-ID overlap;
- no covered, canonical, retry, or failure-only row;
- 300/300 exact five-hint sets;
- no ad hoc substitution.

If eligibility has changed, stop and regenerate the entire plan; never edit a locked row manually.

## 2. Perform offline lane dry runs

Under a separately scoped preparation task, run one exact 150-row dry run per lane into separate dry-run directories. Audit all prompt identities, strict employer/unit/source controls, compact mode, hints, adaptive metadata, row timing, and the absence of backend calls. A dry-run pass does not authorize live execution.

## 3. Run the stronger preflight

Immediately before a separately authorized live round:

1. run the preflight gate in a fresh plan-only directory;
2. create one exact diagnostic probe input;
3. run exactly one stronger live gate with no-search, trivial hosted-search, municipality-style hosted-search, and the production one-row probe;
4. require response lifecycle and usage evidence plus a parseable probe;
5. quarantine probe output from all national accounting.

Do not launch either lane if the gate fails, the route is unstable, or the outer-timeout regression tests fail.

## 4. Launch two lanes safely

Use the exact commands in the round’s `lane_live_commands.md`.

- Lane 1 and Lane 2 are separate operating-system processes.
- Each uses `--n-parallels 1`; no request concurrency is added inside the runner.
- Each has a unique 150-row CSV, fresh output path, lineage note, and cost log.
- Each uses compact prompts, deterministic hints, adaptive `3/5/15/10/25/2`, zero SDK retries, and a 90-second inner plus outer timeout.
- Neither lane runs builders, edits shared docs, or commits.

Start Lane 1 first. Wait 2–5 minutes. Confirm that it has created its initial artifacts and has not shown an immediate widespread transport or lifecycle failure. Then start Lane 2. Do not start a third lane in the initial round.

## 5. Monitor without contaminating artifacts

Monitor only local process status and each lane’s own sanitized console, run metadata, and timing files. Do not open source URLs or copy candidates into shared tables.

Stop all lanes if:

- both lanes show repeated no-ID/no-text/no-token transport failures;
- hosted-search capacity appears broadly degraded;
- either process loses its lifecycle/artifact contract;
- systematic parser/schema failures appear;
- protected files change;
- any secret exposure appears.

A single lane’s ordinary isolated timeout does not require killing a healthy other lane; the existing lane collapse gate remains authoritative. A widespread cross-lane pattern does.

## 6. Handle lane failures

- **Both complete:** preserve outputs and audit together.
- **One complete, one zero-parseable failure:** preserve both; the auditor may recommend completed-lane-only merge, but explicit user approval is required.
- **One partial with parseable rows:** do not merge either automatically. Audit terminality and prepare a fresh-directory lane-specific resume if safe.
- **Both partial:** do not merge. Preserve every artifact and review capacity/lineage.
- **Nonterminal parent:** never resume by bypassing terminal gates.
- **Resume:** use the same lane input hash, a fresh output directory, and that lane’s parent only. Never resume across lanes or reuse an output directory.

## 7. Audit all lane outputs offline

After all processes terminate:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/post_lane_audit
```

Review:

- per-lane input hash and terminal status;
- parseable, failure, stopped, pending, and candidate counts;
- required metadata/timing/parse artifacts;
- no cross-lane completed-ID overlap;
- one of the three merge recommendations.

The auditor writes recommendations only. It cannot rebuild accounting.

## 8. Merge accounting once and serially

Use the separate serial-merge prompt only after reviewing the audit.

- `merge_all_lanes`: a later coordinator may rebuild the combined eligible lineage once.
- `merge_completed_lanes_only_with_user_approval`: stop until the user explicitly approves the narrowed scope.
- `do_not_merge_until_resume_or_review`: no shared builder runs.

When authorized, run candidate queue, coverage status, and scout coverage builders exactly once. Then refresh yield learning and dashboard/project-phase JSON. Review checkpoint deltas, protected paths, candidate-stage caveats, and diagnostic quarantine before one commit and relay.

Never run queue/coverage inside a lane. The builders consume repository-wide artifacts and write shared outputs; concurrent or per-lane runs can overwrite each other, observe incomplete sibling state, or create order-dependent counts.

## 9. Decide when to try three lanes

The planner supports `--num-lanes 3`, but three-lane live use remains deferred until the two-lane round demonstrates:

- both lanes completed without widespread transport collapse;
- outer timeouts and adaptive pacing behaved independently;
- artifact and cost-log isolation held;
- the combined auditor produced an unambiguous recommendation;
- one serial merge reproduced correct queue/coverage deltas;
- hosted-search capacity and elapsed-time gains justify another concurrency increase.

The three-lane decision requires a new authorization, new disjoint inputs, a fresh preflight, staggered starts, and the same single-merge boundary.

## Research boundary

This procedure manages source-discovery operations. Candidate rows remain unverified. It does not verify sources, extract or ingest wages, codify mechanisms, calculate wage gaps, support causal claims, or authorize regressions.
