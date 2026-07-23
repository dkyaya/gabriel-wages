# Parallel Round 1 Live Collection Validation — 2026-07-23

Disposition: **PASS**

## Requested validation

- Seven requested Python modules compiled.
- `scripts/test_parallel_scout_lanes.py`: 7/7 checks passed.
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`: 25/25 checks
  passed, including mocked never-returning calls, outer-timeout checkpointing,
  adaptive backoff, and collapse behavior.
- `scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 checks passed.
- `scripts/validate.py`: passed.
- `ingest/test_pipeline.py`: 60/60 checks passed.
- `ingest/audit_coverage.py`: completed successfully.
- `git diff --check`: passed.
- System `python` was usable; no virtual-environment fallback was needed.

Expected argparse errors printed by negative tests are test fixtures and were
followed by explicit PASS results.

## Corpus snapshot

- Contracts: 64
- Cities: 19
- Healthy matched pairs: 28
  - exact-cycle: 10
  - overlap-cycle: 18
- Exploratory adjacent matches: 2
- Unmatched safety units: 6

## Accounting and protected paths

A pre-live SHA-256 manifest covered 100 files in `corpus/`, dashboard data, and
the stopped `bd5e259` output. Post-validation comparison found:

- changed: 0
- missing: 0

Explicit committed hashes also remain:

- national candidate queue:
  `399966fd547dff87d742ea07db4c2004fa51e21574aeda8aad520215781b5992`
- municipality coverage:
  `7e6d185957004fab49d86ba4f45d89997aa35e1134332d0ecb839361ebee1180`
- state coverage:
  `19905a59fd50da77340ef66dd30aebba9cb8ae5400775483629cf94c270fef76`
- county coverage:
  `d1f21f5fd77d40229c978a9e84303834f808f6d5fda537641691379b8a9b0720`
- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`

The diagnostic one-row probe did not enter queue or coverage. No third lane
ran. No live output was merged.

## Secret and stage checks

An offline pattern scan covered 83 round/preflight/dry/live/audit/validation
and dated candidate-export files. It found zero API-key, bearer-header,
access-token, or client-secret patterns.

No source URL was independently opened or verified. No ingestion, codification,
candidate promotion, wage-gap calculation, regression, causal analysis,
dashboard refresh, priority rebuild, remote action, or push occurred.
