# Aggressive 3×300 Attempt 2 Validation

Date: 2026-07-23/24

## Gate and lifecycle checks

- Plan-only preflight: zero external calls.
- Exactly one stronger live gate invocation: one external call.
- Gate result: failed on `no_search_control_failed`.
- Hosted-search diagnostic calls: zero.
- Diagnostic probe calls: zero.
- Attempt 2 dry runs: zero.
- Attempt 2 live lanes: zero.
- Attempt 2 lane live scripts: not created because their prerequisite dry runs were suppressed.
- Attempt 2 lane audit: not run because no lane artifact exists and the committed manifest points to historical Attempt 1 roots.
- Attempt 1 artifacts remain present and unchanged by this task.

## Offline validation

- Seven Python modules compiled successfully.
- `scripts/test_parallel_scout_lanes.py`: 7/7 synthetic offline checks passed.
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`: 26/26 mocked/no-network checks passed.
- `scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 checks passed.
- `scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60/60 checks passed.
- `ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy matched pairs (10 exact and 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.

## Boundaries

- The three locked lane hashes, 900 unique municipality/Census IDs, current eligibility, zero overlap, and 900/900 hints were rechecked before preflight.
- No protected `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` change occurred.
- No dashboard or national accounting file changed.
- No queue, coverage, yield, dashboard/project-phase, or priority builder ran.
- The prepared probe input never produced a probe output and cannot enter accounting.
- No suspected credential value pattern was found in the Attempt 2 preflight artifacts.
- No shared `docs/analysis/gabriel_state_source_scout_candidates_*.csv` export was produced by Attempt 2.
- No live lane output was merged.
- No independent URL verification, source download, ingestion, `gabriel.codify`, wage-gap work, causal claim, regression, remote action, or push occurred.

