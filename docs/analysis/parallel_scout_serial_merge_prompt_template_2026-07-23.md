# Future Coordinator Prompt Template — Serial Merge After Parallel Scout Lanes

Use only after parallel lane processes have terminated and the offline combined audit exists. This prompt is a separate accounting authorization boundary.

This template supports one to three lanes, including reviewed 150-, 250-, and
300-row profiles. Never assume a fixed lane count or row count; read both from the
locked manifest.

---

Work only in the main coordinator repository:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Serially merge an audited parallel scout round into national source-discovery accounting only if the audit recommendation and user authorization permit it. Do not inspect remotes, push, fetch, pull, verify URLs, ingest, codify, calculate wage gaps, make causal claims, or run regressions.

## Evidence gate

Read:

- the round manifest;
- every lane input and hash;
- every lane result review;
- `parallel_lane_audit_summary.json`;
- `parallel_lane_audit_report.md`;
- `merge_recommendation.md`;
- current queue/coverage methodology and builder scripts;
- current project-phase/yield/dashboard files.

Recompute:

- lane input hashes and row counts;
- lane terminal classifications;
- parseable/failure/stopped/pending/candidate counts;
- municipality/Census uniqueness across inputs;
- completed municipality-ID overlap;
- each configured lane-local candidate export and its byte identity with that lane's
  `parsed_candidates.csv`;
- per-lane and combined outer-timeout, adaptive pacing, elapsed-time, and throughput
  summaries;
- diagnostic/probe exclusions;
- protected-file and national-accounting baselines.

Stop if any audit artifact is missing, any input hash differs, completed IDs
overlap, or a required lane-local candidate export is absent, ambiguous, or differs
from `parsed_candidates.csv`.

## Recommendation decision

### `merge_all_lanes`

Proceed only when every manifest lane is `completed_merge_eligible`, all lineages
and lane-local exports are complete, and no completed IDs overlap. For a 3-lane
round, all three lanes must pass.

### `merge_completed_lanes_only_with_user_approval`

Proceed only if the user explicitly approves merging the named completed lanes and
excluding the named zero-parseable failed lanes. This applies equally to a
2-complete/1-failed three-lane round. Document that the round scope changed. Do not
infer approval from the audit.

### `do_not_merge_until_resume_or_review`

Do not run any shared builder. Preserve artifacts and prepare the required lane-specific resume or review.

## One serial accounting rebuild

If and only if authorized:

```bash
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
python scripts/build_scout_coverage.py
```

Run each exactly once from the coordinator repository, never concurrently. Audit queue rows, candidate-stage dispositions, successful coverage, positive/empty/failure-only counts, state deltas, and diagnostic quarantine. Confirm no duplicate lane result was ingested twice.

Then run:

```bash
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

Update:

- source-discovery progress toward approximately 2,000 covered municipalities;
- remaining checkpoint count and estimated waves;
- combined lane runtime/yield reporting;
- `parallel_scout_status.json` from planned to the exact audited result;
- project documentation and limitations.

Before authorizing another broad scouting round, compare updated official coverage
with the approximately 2,000 checkpoint. Stop broad scouting at or above it. A
3 × 250 or 3 × 300 merge may cross the checkpoint; do not automatically prepare
another discovery round afterward.

Do not refresh priority tiers unless the documented 300–600-success cadence, another deterministic threshold, or explicit strategy requires it. Do not change methodology.

## Validation, commit, and relay

Run the complete runner, builder, schema, ingestion, coverage, JSON, frontend-build-if-changed, protected-file, diagnostic-quarantine, and diff validation suite. Confirm candidate rows remain unverified and no wage-gap or causal claim was added.

Create one coordinator commit and one relay containing all shared accounting changes, lane/audit lineage, validation evidence, post-commit status/log, changed-file inventory, and next task. Do not push or inspect remotes.

---
