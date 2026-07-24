# Source-Review Pilot Framework Validation

Date: 2026-07-24

## Result

**PASS.** The source-rating schema, deterministic pilot planner, fail-closed
dry-run runner, lane auditor, dashboard status, documentation, and locked
150-row pilot passed offline validation.

## Commands and results

The following compiled successfully:

```text
python -m py_compile scripts/prepare_source_review_pilot.py
python -m py_compile scripts/source_review_sources.py
python -m py_compile scripts/audit_source_review_lanes.py
python -m py_compile scripts/test_source_review_planning.py
python -m py_compile scripts/build_dashboard_data.py
```

`python scripts/test_source_review_planning.py` passed five test methods,
covering:

- p1/download-allowed filtering;
- duplicate, oversized, blocked, defer, exclude, and lower-disposition
  exclusion;
- exact 150-row and 75/75 lane planning;
- state diversity and deterministic source-review IDs;
- dry-run schema output with network-failing mocks;
- fail-closed rejection of non-dry review;
- two-lane dry-run audit; and
- upstream/protected-file immutability.

The exact requested planner command rebuilt the same lane CSV hashes:

- lane 1:
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`;
- lane 2:
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`.

Both explicit dry runs produced 75/75 `planned_not_reviewed` rows. The final
auditor reports:

- planned/ledger/terminal-planned rows: 150/150/150;
- classification: two `dry_run_passed` lanes;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- URL opens and network calls: 0;
- downloads: 0;
- document/PDF parses: 0;
- OCR runs: 0;
- content artifacts: 0; and
- recommendation: `dry_run_complete_no_live_source_review`.

Other validation:

- dashboard builder: passed; 51 states/DC, 35,589 municipalities, 2,436
  scout-covered, and 4,726 candidate rows;
- dashboard JSON parse: all 16 files passed;
- dashboard production build: passed with 45 modules;
- `python scripts/validate.py`: passed;
- `python ingest/test_pipeline.py`: 60 passed, 0 failed;
- `python ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact and 18 overlap), two exploratory adjacent pairs,
  and six unmatched safety units; and
- `git diff --check`: passed.

## Immutability and provenance checks

SHA-256 values remained unchanged:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- cumulative routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- cumulative metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`;
  and
- the corpus tree aggregate matched its start-of-task baseline.

Every candidate/final/source-locator URL in the 150 pilot rows is byte-identical
to its upstream metadata-triage row. A non-URL secret-pattern scan passed. The
existing unrelated untracked root `package-lock.json` remained untouched.

## Safety boundary

No URL was opened and no network/API/model/hosted-search call occurred. No
document was downloaded or parsed, and no OCR ran. No live source review,
scout-accounting change, routing-ledger or metadata-triage-ledger mutation,
source rating, extraction, ingestion, `gabriel.codify`, wage calculation,
wage-gap claim, causal claim, regression, remote action, or push occurred.

One dry-run invocation initially failed before creating output because the
`--no-download` CLI flag used an inverted Boolean parser. The parser was
corrected to a direct fail-closed flag, tests remained green, and the two
locked dry runs then passed. That pre-output failure performed no source or
network access.
