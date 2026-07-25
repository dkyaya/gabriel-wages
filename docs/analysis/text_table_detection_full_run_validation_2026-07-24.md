# Full Text/Table Detection Run Validation

Date: 2026-07-25

Run: `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

## Overall result

**PASS.** The full bounded local collection contains 1,828 / 1,828 planned
rows, all four lanes are `completed_merge_eligible`, the full-run identity
set exactly equals the durable `parse_text_layer_later` authority, and every
selected row has terminal `detection_checked` status.

No durable text/table-detection merge occurred.

## Required commands

The following passed:

```bash
.venv/bin/python -m py_compile scripts/prepare_text_table_detection_pilot.py
.venv/bin/python -m py_compile scripts/text_table_detection_sources.py
.venv/bin/python -m py_compile scripts/audit_text_table_detection_lanes.py
.venv/bin/python -m py_compile scripts/test_text_table_detection_planning.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py

.venv/bin/python scripts/test_text_table_detection_planning.py

.venv/bin/python scripts/audit_text_table_detection_lanes.py \
  --manifest docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/text_table_detection_pilot_manifest.json \
  --output-dir tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/final_full_run_validation_lane_audit

.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
git diff --check
```

The text/table unit suite passed 16 / 16 tests. The ingestion suite passed
60 / 60 tests. The canonical validator reported 64 contracts, zero discourse
rows, 64 coverage rows, and three city-attribute rows.

The dashboard production build also passed:

```bash
cd docs/dashboard
npm run build
```

## Final lane audit

- planned rows: 1,828;
- ledger rows: 1,828;
- terminal rows: 1,828;
- lanes: four `completed_merge_eligible`;
- merge recommendation: `merge_all_text_table_detection_lanes`;
- duplicate detection/PDF-readiness/source-review/candidate IDs: 0;
- missing or unexpected rows: 0;
- hash failures: 0;
- missing artifacts: 0;
- parser errors: 0;
- heuristic-version mismatches: 0;
- invalid candidate-page hints: 0;
- bounded-hint overruns: 0; and
- full-text artifacts: 0.

## Independent identity and safety validation

A separate read-only validation compared every full-run row with the durable
PDF-readiness authority:

- full-run PDF-readiness IDs exactly equal all 1,828 eligible
  `parse_text_layer_later` IDs;
- source-review/candidate identity, artifact path, hash, size, content type,
  page count, and text-layer status match for every row;
- all 150 Pilot 1 identities are present and reproduce the frozen pilot
  results exactly across terminal status, scan counts, signals, candidate
  pages, bounded hints, priority, action, and notes;
- contract-period hints are at most 300 characters;
- retained hints contain zero currency, comma-delimited salary, or percentage
  patterns under the validation scan;
- all dashboard JSON files parse;
- no secret-like credential patterns were found in full-run plan/output
  artifacts; and
- no durable text/table-detection ledger exists.

## Protected and upstream state

Hashes and tracked diffs confirm no changes to:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- `corpus/`;
- the national scout candidate queue or scout coverage ledger;
- the durable URL-routing ledger;
- the cumulative metadata-triage ledger;
- the cumulative source-review ledger; or
- the cumulative PDF-readiness ledger.

The coverage audit remains:

- contracts: 64;
- cities: 19;
- healthy matched pairs: 28;
- exploratory adjacent matches: 2; and
- unmatched safety units: 6.

## Prohibited-activity confirmation

- URLs opened: 0;
- network/API/model calls: 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- complete page/document text artifacts: 0;
- final wage values extracted: 0;
- ingestion actions: 0;
- codify actions: 0;
- scout queue/coverage updates: 0;
- upstream durable-ledger mutations: 0;
- durable text/table-detection merges: 0; and
- wage-gap calculations, causal claims, and regressions: 0.
