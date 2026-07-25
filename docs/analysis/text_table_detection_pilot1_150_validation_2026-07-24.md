# Text/Table Detection Pilot 1 Validation

Date: 2026-07-25

Pilot: `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24`

## Result

**PASS.** The locked plan, three bounded local lane outputs, final lane
audit, dashboard data, frontend build, repository schema, ingestion
regressions, protected-file boundaries, and no-forbidden-activity checks all
passed.

No durable text/table-detection merge was run.

## Commands run

The following required commands completed successfully:

```bash
.venv/bin/python -m py_compile scripts/prepare_text_table_detection_pilot.py
.venv/bin/python -m py_compile scripts/text_table_detection_sources.py
.venv/bin/python -m py_compile scripts/audit_text_table_detection_lanes.py
.venv/bin/python -m py_compile scripts/test_text_table_detection_planning.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py

.venv/bin/python scripts/test_text_table_detection_planning.py

.venv/bin/python scripts/audit_text_table_detection_lanes.py \
  --manifest docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24/text_table_detection_pilot_manifest.json \
  --output-dir tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24/final_local_detection_validation_lane_audit

.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
git diff --check
```

The dashboard frontend also passed:

```bash
cd docs/dashboard
npm run build
```

## Test and audit results

- Python compilation: five scripts passed.
- Text/table-detection synthetic and mock tests: 14 passed, zero failed.
- Ingestion regression tests: 60 passed, zero failed.
- Repository schema validation: passed.
- Coverage audit: 64 contracts, 19 cities, 28 healthy matched pairs
  (10 exact and 18 overlap), two exploratory adjacent pairs, and six
  unmatched safety units.
- Final lane audit: 150 / 150 terminal rows; three
  `completed_merge_eligible` lanes.
- Final audit recommendation:
  `merge_all_text_table_detection_lanes`.
- Dashboard data generation: 18 JSON files.
- Dashboard JSON parse check: 18 / 18 passed.
- Dashboard frontend production build: passed.
- Whitespace/error check: `git diff --check` passed.

## Locked input and result checks

| Lane | Rows | SHA-256 |
|---|---:|---|
| 1 | 50 | `98d273658e4e51101b97eb19ec783485f6ddf68dfbbc3b07c2a7bb3bd38168d9` |
| 2 | 50 | `f2636a5b80e6e37e28ceccab4bd2d2c4058aecbe2dba37c6181203c20fe2defd` |
| 3 | 50 | `8747e82eced3f76db14cfdebd75a407d20766dd504ef8a2d3f301db9cfc787e0` |

Independent checks confirmed:

- 150 unique text/table-detection, PDF-readiness, source-review, and
  candidate-queue identities;
- all selected readiness-authority rows are
  `parse_text_layer_later` with `present` or `partial` text;
- 150 / 150 live results are terminal `detection_checked`;
- artifact path, recorded hash, and recorded byte size match the durable
  readiness authority;
- candidate contract-period hints are at most 300 characters;
- candidate hints contain zero currency, comma-delimited salary, or
  percentage patterns;
- output directories contain only the expected CSV, JSON, timing, and audit
  files;
- complete page/document text files: zero; and
- secret-indicator matches in product artifacts: zero.

## Immutable boundaries

No tracked difference exists from the starting commit for:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- `corpus/`;
- national scout candidate queue or coverage accounting;
- durable URL-routing ledgers;
- durable content-triage ledgers;
- durable source-review ledgers; or
- durable PDF-readiness ledgers.

Post-run SHA-256 values are:

- contracts: `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- city coverage: `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- candidate queue: `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- scout coverage accounting:
  `bad2948a2990e91280b510e5d93c1ab29aa65959f83693a641a1e902836e5a21`;
- routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- content-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`;
- source-review ledger:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`;
  and
- PDF-readiness ledger:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`.

The unrelated untracked root `package-lock.json` remained untouched.

## Forbidden-activity confirmation

The lane summaries and final audit record all of the following as zero:

- URLs opened;
- network/API/model calls;
- downloads and redownloads;
- OCR runs;
- complete page/document text artifacts;
- final wage values extracted;
- ingestion actions;
- codify actions; and
- durable text/table-detection merges.

No scouting, URL verification, live source review, wage-gap calculation,
causal claim, regression, remote inspection, or push occurred.
