# Future Coordinator Prompt — Checkpoint 3×160 Serial Accounting Merge

Use only after every live lane for
`POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23` has terminated and a complete
offline lane audit exists. This prompt is the separate serial accounting
authorization boundary; do not run it during preparation or live collection.

Work only in:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Do not inspect remotes, push, fetch, pull, run live scouts or diagnostics,
verify URLs, ingest, codify, calculate wage gaps, make causal claims, or run
regressions.

## Merge evidence gate

Read the committed round manifest, all three locked inputs/audits, every lane
output and review, `parallel_lane_audit_summary.json`,
`parallel_lane_audit_report.md`, and `merge_recommendation.md`.

Recompute:

- the three locked input hashes and 160-row counts;
- current input eligibility and all cross-lane municipality/Census uniqueness;
- lane classifications and terminal timing;
- parseable, positive, empty, failure, stopped, pending, and candidate counts;
- completed municipality-ID overlap;
- each lane-local timestamped candidate export and byte identity with that
  lane's `parsed_candidates.csv`;
- outer-timeout, adaptive pacing, elapsed-time, throughput, and resume lineage;
- diagnostic/probe exclusion; and
- current protected-file and national-accounting baselines.

Proceed automatically only if every lane is `completed_merge_eligible`, all
exports match, no completed IDs overlap, and the auditor recommends
`merge_all_lanes`.

If the auditor recommends
`merge_completed_lanes_only_with_user_approval`, stop unless the user
explicitly approves the named completed-only subset and exclusions. If any
partial lane has parseable rows, any artifact is ambiguous, or the
recommendation is `do_not_merge_until_resume_or_review`, do not run shared
builders.

## Exactly one serial accounting rebuild

Preserve audited lane candidate exports and state-usage artifacts in the
deterministic coordinator inputs. Register only the official lane lineages and
terminal failures in the unchanged builders. Never register diagnostic or
probe output.

Run each command exactly once:

```bash
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
python scripts/build_scout_coverage.py
```

Record queue, successful coverage, candidate-positive, parseable-empty,
failure-only, triage, state, and checkpoint before/after deltas. Prove no lane
was ingested twice and failure-only rows remain outside successful coverage.

Only after that succeeds, run:

```bash
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

Refresh yield learning, dashboard/project-phase JSON, the combined round
runtime/yield status, and official progress toward 2,000.

Decide whether to refresh priority tiers using the unchanged documented
300–600-success cadence or another explicit deterministic strategy trigger.
If a refresh is warranted, run the canonical priority builder once and rebuild
dashboard JSON afterward. Do not change methodology.

## Checkpoint transition

If official serial accounting reaches or slightly exceeds approximately 2,000:

- mark the source-discovery scale-up checkpoint reached;
- pause broad ordinary scouting;
- do not prepare another broad round automatically;
- create a post-checkpoint planning note for:
  verification → extraction → ingestion → source quality/extractability rating
  → descriptive wage-growth-gap analysis → mechanism-correlation
  documentation → dashboard wage-gap filtering;
- keep regressions deferred.

If merge-eligible results unexpectedly leave the project below 2,000, report
the exact shortfall and request a decision before preparing any narrow cleanup
round.

## Validation, commit, and relay

Run the complete no-network runner/builder tests, schema and ingestion tests,
coverage audit, dashboard/priority JSON parsing, frontend build if changed,
protected-file checks, diagnostic quarantine checks, and `git diff --check`.
Confirm all candidates remain unverified and no wage-gap or causal claim was
introduced.

Create one local merge commit and complete relay with lane/audit lineage,
changed files, validation evidence, post-commit status/log, and a next-phase
task note. Do not push or inspect remotes.
