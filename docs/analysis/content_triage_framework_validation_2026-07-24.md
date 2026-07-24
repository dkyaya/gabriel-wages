# Content-Triage Framework Validation

Date: 2026-07-24
Round: `CONTENT-TRIAGE-ROUND1-1000-2026-07-24`

## Result

**PASS.** The offline framework, deterministic 1,000-row plan, two 500-row
dry runs, combined lane audit, dashboard status, schema validator, ingestion
tests, coverage audit, protected-file checks, and artifact safety checks pass.

## Compilation and tests

The following compile:

- `scripts/prepare_content_triage_batches.py`
- `scripts/content_triage_sources.py`
- `scripts/audit_content_triage_lanes.py`
- `scripts/test_content_triage_planning.py`
- `scripts/build_dashboard_data.py`

`python scripts/test_content_triage_planning.py` passes six offline checks:

1. default selection includes only reachable/reused scheduled high-priority
   rows and reports routing exceptions separately;
2. exact-URL groups retain one representative and defer linked rows by
   default;
3. duplicates and lower-disposition candidates require explicit inclusion;
4. the dry runner writes terminal schema rows with zero network/content
   activity;
5. the two-lane auditor classifies complete dry outputs correctly; and
6. non-dry execution is rejected because live content triage is not
   implemented.

Tests use synthetic temporary CSVs and a network-failing socket patch. They do
not contact the network or mutate candidate queue, routing ledger, contracts,
or city coverage.

## Real plan and dry-run audit

The exact requested planner command was rerun successfully. It reproduces:

- selected rows: 1,000;
- lane rows: 500 / 500;
- hashes:
  `1ae2aef43cec1756c0169b1395f00d8a772ddd12fd98a6a70c5b2937b784bc2b`
  and
  `118f3ca494782d46e504bfb2ebded6c8afe9e22a7a81661808987ea78ae64688`;
- unique triage IDs: 1,000;
- unique candidate queue IDs: 1,000; and
- URLs opened/documents downloaded/documents parsed: 0 / 0 / 0.

Both existing dry-run outputs have 500 `triage_planned` rows. The final lane
audit reproduces:

- classification counts: two `dry_run_passed`;
- ledger/terminal rows: 1,000 / 1,000;
- cross-lane duplicate triage IDs: 0;
- cross-lane duplicate candidate queue IDs: 0; and
- recommendation: `dry_run_complete_do_not_merge_live_triage`.

## Dashboard and project checks

- `python scripts/build_dashboard_data.py`: PASS.
- Dashboard JSON parsing: PASS, **15 files**.
- Dashboard frontend production build: PASS, **44 modules**.
- `python scripts/validate.py`: PASS.
- `python ingest/test_pipeline.py`: PASS, **60 tests**.
- `python ingest/audit_coverage.py`: PASS.
- `git diff --check`: PASS.

One combined local validation command was initially launched from
`docs/dashboard`, so its repository-relative Python paths failed immediately;
it made no network call or state mutation. The frontend build in that call
passed, and every repository-root validation command was then rerun
successfully and recorded in the validation directory.

Coverage remains 64 contracts, 19 cities, 28 healthy matched pairs (10 exact,
18 overlap), two exploratory adjacent pairs, and six unmatched safety units.

## Protected and accounting invariance

Post-task SHA-256 values match the recorded pre-task values:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- canonical candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- cumulative routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- cumulative routing summary:
  `f701b48f94e65e6b7a5f26a2d3d479f05f86530d1f9f33ed3bd8e59c35f1fca0`;
- corpus aggregate:
  `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a`.

No scout queue/coverage builder ran. The framework added only planning,
dry-run, audit, documentation, and dashboard/status outputs.

## Safety boundary

Credential-shaped artifact findings are zero across the generated plan,
dry-run, audit, and content-triage dashboard files. No URL was opened and no
document was downloaded, parsed, or OCRed. No live URL verification or live
content triage ran. No network/API/model/hosted-search/scout call, ingestion,
`gabriel.codify`, wage extraction, wage-gap calculation or claim, causal
claim, regression, remote action, or push occurred.
