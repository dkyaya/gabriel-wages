# Text/Table Calibration Subset 1 Validation

## Result

**Passed.** The offline calibration planner produced exactly 150 unique,
unreviewed rows from the 1,828-row durable detection authority. The packet
contains 80 likely, 58 possible, and all 12 unlikely wage-table signals.
Independent checks found zero authority-field mismatches, zero protected or
durable input changes, zero packet PDFs or full-text files, and zero
secret-shaped values.

## Commands

The following validation commands completed successfully:

```text
.venv/bin/python -m py_compile scripts/prepare_text_table_calibration_subset.py
.venv/bin/python -m py_compile scripts/test_text_table_calibration_planning.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py
.venv/bin/python scripts/test_text_table_calibration_planning.py
.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
cd docs/dashboard && npm run build
git diff --check
```

The calibration suite passed 9 / 9 synthetic offline tests. The repository
schema validator passed. The ingestion suite passed 60 / 60 tests. The
dashboard JSON builder and Vite production build passed.

## Packet and authority checks

- calibration rows: 150
- unique calibration, detection, PDF-readiness, source-review, and candidate
  identities: 150 each
- durable detection authority rows: 1,828
- inherited identity/artifact/page/text/signal mismatches: 0
- manual reviews completed: 0
- every `calibration_status`: `not_reviewed`
- likely / possible / unlikely: 80 / 58 / 12
- extraction priority p1 / p2 / p3: 80 / 63 / 7
- packet PDF files: 0
- packet `.txt` or full-text files: 0
- secret-shaped values: 0

The generated packet hashes match
`calibration_subset_manifest.json`. The dashboard calibration JSON parses and
reports `subset1_prepared_not_reviewed`; downstream extraction, ingestion,
codification, and wage-gap statuses remain `not_started`.

## Protected state

SHA-256 checks confirm that `data/contracts.csv`,
`data/city_coverage.csv`, the scout candidate queue, durable routing ledger,
durable metadata-triage ledger, durable source-review ledger, durable
PDF-readiness ledger, and durable text/table-detection ledger are unchanged
from the starting state. The `corpus/` filename-list hash remains:

`32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322`

Coverage remains 64 contracts across 19 cities, with 28 healthy matched pairs
(10 exact and 18 overlap), two exploratory adjacent pairs, and six unmatched
safety units.

## Activity boundary

Preparation opened zero PDFs and zero URLs. It made zero network/API/model
calls, performed zero additional text extractions, ran zero OCR, retained zero
full-text artifacts, extracted zero final wage values, and performed zero
ingestion, codification, or durable-ledger mutations. No remote was inspected
and nothing was pushed.

Detailed command logs and independent JSON/Markdown checks are under:

`tmp/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/validation_2026-07-24/`
