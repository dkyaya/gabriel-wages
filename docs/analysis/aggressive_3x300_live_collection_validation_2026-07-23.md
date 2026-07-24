# Aggressive 3×300 Live Collection Validation

Date: 2026-07-23/24

## Results

- Seven requested Python modules compiled successfully.
- `scripts/test_parallel_scout_lanes.py`: 7/7 synthetic offline checks passed.
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`: 26/26 mocked/no-network checks passed.
- `scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 checks passed.
- `scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60/60 checks passed.
- `ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy matched pairs (10 exact and 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- Locked lane hashes, 900 unique municipality/Census IDs, zero overlap, current eligibility, and 900/900 five-hint sets were rechecked before live collection.
- All three dry-run timing ledgers contain 300 ordered terminal `dry_run_planned` rows.
- The one-row diagnostic probe remains under its dedicated preflight directory and is absent from official accounting.
- Lane 1’s timing ledger contains two terminal `connection_error` attempts and 298 terminal `stopped_before_request` rows; no row remains pending.
- Lane 2 and Lane 3 were not launched.
- The offline lane auditor wrote no accounting files and recommends `do_not_merge_until_resume_or_review`.
- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` are unchanged.
- National queue, coverage, yield, dashboard/project-phase, and priority accounting files are unchanged.
- No independent URL verification, ingestion, codification, wage-gap work, causal claim, regression, remote action, or push occurred.

The only external calls in this task were the exactly authorized stronger preflight’s four calls and Lane 1’s two failed direct-SDK requests. The plan-only preflight and all dry runs/tests were offline.

