# Future Coordinator Prompt Template — Serial Merge After Parallel Scout Lanes

Use only after parallel lane processes have terminated and the offline combined audit exists. This prompt is a separate accounting authorization boundary.

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
- diagnostic/probe exclusions;
- protected-file and national-accounting baselines.

Stop if any audit artifact is missing, any input hash differs, or completed IDs overlap.

## Recommendation decision

### `merge_all_lanes`

Proceed only when every lane is `completed_merge_eligible`, all lineages are complete, and no completed IDs overlap.

### `merge_completed_lanes_only_with_user_approval`

Proceed only if the user explicitly approves merging the named completed lanes and excluding the named zero-parseable failed lanes. Document that the round scope changed. Do not infer approval from the audit.

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

Do not refresh priority tiers unless the documented 300–600-success cadence, another deterministic threshold, or explicit strategy requires it. Do not change methodology.

## Validation, commit, and relay

Run the complete runner, builder, schema, ingestion, coverage, JSON, frontend-build-if-changed, protected-file, diagnostic-quarantine, and diff validation suite. Confirm candidate rows remain unverified and no wage-gap or causal claim was added.

Create one coordinator commit and one relay containing all shared accounting changes, lane/audit lineage, validation evidence, post-commit status/log, changed-file inventory, and next task. Do not push or inspect remotes.

---
