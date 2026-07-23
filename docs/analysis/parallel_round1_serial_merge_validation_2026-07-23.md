# Parallel Round 1 Serial Merge Validation — 2026-07-23

Disposition: **PASS**

System `python` was usable; no `.venv` fallback was needed.

## Requested validation

- Thirteen requested Python modules compiled.
- `scripts/test_parallel_scout_lanes.py`: 7/7 synthetic offline checks passed.
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`: 25/25 mocked,
  no-network checks passed, including outer timeout, adaptive pacing, collapse,
  resume, lifecycle, and successful-response behavior.
- `scripts/test_gabriel_state_source_scout_prompt.py`: 12/12 checks passed.
- `scripts/validate.py`: passed; 64 contract rows conform.
- `ingest/test_pipeline.py`: 60/60 passed.
- `ingest/audit_coverage.py`: completed successfully.
- `git diff --check`: passed.
- `docs/dashboard && npm run build`: passed with 42 modules transformed.
- All 13 dashboard JSON files parse; the three priority JSON files parse.

The direct-SDK test suite prints expected argparse errors and synthetic
non-mergeable lifecycle messages as negative fixtures. Every fixture is
followed by its explicit PASS result and makes no network call.

## Accounting reconciliation

- Queue: 2,362 rows, including exactly 760 rows from the two approved
  Parallel Round 1 run IDs.
- Coverage: 1,091 successful = 884 candidate-positive + 207 parseable-empty.
- Failure-only: 23, including Newark OH, St. Cloud FL, and Waterloo IA with
  zero successful live-scout counts and zero queue candidate rows.
- Project phase: 1,091/2,000, 909 remaining, seven full comparable waves.
- The refreshed parallel status is
  `round1_completed_accounting_merged`.
- Priority source CSVs are unchanged. Their dashboard layers parse and are
  explicitly marked `stale_after_parallel_round1_merge`.

## Quarantine, protected paths, and secrets

- `data/contracts.csv` remains SHA-256
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`.
- `data/city_coverage.csv` remains SHA-256
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`.
- Git reports zero changes under `data/contracts.csv`,
  `data/city_coverage.csv`, or `corpus/`.
- Eleven diagnostic probe files are byte-identical to the prior committed
  live-collection relay copies. No queue row has a probe source path.
- Eight stopped `bd5e259` files are byte-identical to their original relay ZIP
  entries. Queue rows for stopped run `all_2026-07-23_105131`: zero.
- A conservative credential-pattern scan found no newly introduced matching
  lines. The few matches in regenerated/updated files are byte-identical lines
  already present at the starting commit (historical prose or URL substrings);
  no credential value was printed.

## Execution boundary

The only model-related code executed was the fully mocked, offline unit suite.
No live scout, API/model/hosted-search call, diagnostic, preflight, URL open or
verification, source ingestion, `gabriel.codify`, candidate promotion,
wage-gap calculation/claim, causal claim, regression, remote inspection, or
push occurred.

Validation output is preserved at
`tmp/parallel_round1_serial_merge_validation_2026-07-23/requested_validation.log`.
