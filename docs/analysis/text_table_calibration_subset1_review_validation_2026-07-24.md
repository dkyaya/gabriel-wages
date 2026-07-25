# Text/Table Calibration Subset 1 Review Validation

## Result

**Passed operational and safety validation.** The extraction-authorization
gate is separately **failed** because the rendered-page challenge found
material disagreement in all five checked assisted outcomes.

## Commands

The following completed successfully from the coordinator repository:

```text
.venv/bin/python -m py_compile scripts/review_text_table_calibration_subset.py
.venv/bin/python -m py_compile scripts/test_text_table_calibration_review.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py
.venv/bin/python scripts/test_text_table_calibration_review.py
.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
.venv/bin/python tmp/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/validate_review_outputs.py
npm run build
git diff --check
```

## Automated results

- compiles: 3 / 3
- calibration-review tests: 10 / 10
- repository schema validation: passed
- ingestion tests: 60 / 60
- dashboard JSON files parsed: 19 / 19
- dashboard production build: passed
- independent review-output audit: passed
- eligible/opened local PDF paths: 150 / 150
- artifact hash/size failures: 0
- reviewed rows and unique locked identities: 150 / 150
- pages inspected / returning text: 630 / 612
- bounded full-text or complete-table output files: 0
- secret-shaped values: 0
- original calibration input preserved: yes
- protected and durable authority hashes preserved: yes
- corpus filename-list hash preserved: yes
- forbidden-activity counters: all zero

## Review-method and gate validation

The output correctly identifies its method as
`codex_assisted_local_adjudication`, not human manual review. The assisted
ledger contains 150 terminal rows, including 55 marked
`needs_second_review`. All labels use the controlled vocabularies and all
review notes satisfy the 300-character limit.

The five-row rendered-page spot-check was drawn only from the locked
calibration artifacts. It materially disagreed with all five assisted
outcomes. Consequently:

- `calibration_pass_status = fail`
- `next_recommendation = refine_detector_or_schema`
- the 500-document extraction prompt is blocked archival planning material

This gate failure is a substantive calibration finding, not an operational
validation failure.

## Protected boundaries

The independent audit confirmed that the following stayed byte-identical:

- `data/contracts.csv`
- `data/city_coverage.csv`
- durable URL-routing ledger
- durable metadata-triage ledger
- durable source-review ledger
- durable PDF-readiness ledger
- durable text/table-detection ledger
- original `calibration_review_input.csv`

No URL or network/API/model call occurred. No document was downloaded or
redownloaded. OCR, final wage extraction, ingestion, `gabriel.codify`,
wage-gap calculation, regression, remote inspection, and push did not occur.
No complete page/document text, copied PDF, complete table, or structured
wage observation was saved.

## Coverage snapshot

`ingest/audit_coverage.py` reports:

- contracts: 64
- cities: 19
- healthy matched pairs: 28
  - exact-cycle: 10
  - overlap-cycle: 18
- exploratory adjacent pairs: 2
- unmatched safety units: 6
