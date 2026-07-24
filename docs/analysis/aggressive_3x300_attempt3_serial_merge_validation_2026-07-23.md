# Aggressive 3×300 Attempt 3 Serial Merge Validation

Date: 2026-07-23/24

## Requested validation

All requested commands passed using the repository `python` shim:

- 13 `py_compile` checks;
- seven synthetic parallel-lane tests;
- 26 mocked/no-network direct-SDK tests;
- 12 prompt and dry-run tests;
- `python scripts/validate.py`;
- 60 ingestion pipeline tests;
- `python ingest/audit_coverage.py`; and
- `git diff --check`.

The dashboard frontend production build also passed with 42 transformed
modules. All 13 dashboard JSON files parse, including the three priority
layers.

The corpus coverage audit remains:

- 64 contracts;
- 19 cities;
- 28 healthy matched pairs, including 10 exact-cycle and 18 overlapping-cycle;
- two exploratory adjacent matches; and
- six unmatched safety units.

## Accounting checks

- The candidate queue contains 4,726 unique URL-bearing rows.
- Municipality coverage contains 35,589 unique universe rows.
- Candidate-positive plus parseable-empty equals successful coverage:
  `1,858 + 578 = 2,436`.
- Shelby, Ohio remains failure-only and outside successful coverage.
- The failed-attempt ledger is 44 attempts across 28 failure-only
  municipalities.
- The project phase records `reached_exceeded`, a +436 margin, and broad
  scouting paused.
- The parallel status records
  `aggressive_3x300_completed_accounting_merged`.
- Priority outputs parse and report 33,147 future-eligible, 245 eligible Tier 1,
  2,906 eligible Tier 2, and 28 failure-retry targets.

## Boundary and quarantine checks

- `data/contracts.csv` retains SHA-256
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`.
- `data/city_coverage.csv` retains SHA-256
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`.
- The aggregate `corpus/` hash remains
  `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a`.
- No shared Attempt 3 timestamped candidate export exists under
  `docs/analysis/`.
- Queue artifacts contain no Attempt 1 aggressive lane root, Attempt 2
  preflight root, or Attempt 3 diagnostic-probe root.
- Attempt 1 and Attempt 2 quarantine roots remain present.
- The dashboard states that wage gaps have not been calculated and no gap
  layer is active.

## Scope confirmation

This task made no live scout, API, model, hosted-search, diagnostic, smoke
preflight, or independent URL call. It performed no source verification,
extraction, ingestion, `gabriel.codify`, candidate-to-evidence promotion,
wage-gap calculation or claim, causal claim, or regression. It did not inspect
or modify remotes and did not push.

The national candidate queue and coverage commands ran in the required
one-time serial sequence. Yield/dashboard and priority refreshes occurred only
after that sequence succeeded.

Command logs are preserved under:

`tmp/aggressive_3x300_attempt3_serial_merge_2026-07-23/command_logs/`
