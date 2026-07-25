# Text/Table Detection Refine 1 Validation

## Result

**Passed.** The refined visual/table gate is prepared for a later REVIEW2.
No REVIEW2, wage extraction, or 500-document extraction run occurred.

## Commands and results

The required compilation checks passed:

```text
.venv/bin/python -m py_compile scripts/review_text_table_calibration_subset.py
.venv/bin/python -m py_compile scripts/test_text_table_calibration_review.py
.venv/bin/python -m py_compile scripts/test_text_table_calibration_review_refined.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py
```

Review tests:

- legacy synthetic/offline suite: 10 passed, 0 failed;
- refined synthetic/offline suite: 9 passed, 0 failed.

The refined suite covers wage prose without a table, benefits tables,
classification-only tables without pay, contents/index navigation to a later
salary table, confirmed wage-table structure, identity preservation,
immutable original/REVIEW1 files, bounded render/page/snippet budgets,
controlled values, and no network/OCR/full-text output.

Repository checks:

- dashboard data build: passed;
- all dashboard JSON files parse;
- dashboard production build: passed with 48 modules transformed;
- `scripts/validate.py`: passed;
- `ingest/test_pipeline.py`: 60 passed, 0 failed;
- `ingest/audit_coverage.py`: passed;
- `git diff --check`: passed;
- changed-file secret-pattern scan: passed.

Coverage snapshot:

- contracts: 64;
- cities: 19;
- healthy matched pairs: 28 (10 exact, 18 overlap);
- exploratory adjacent pairs: 2;
- unmatched safety units: 6.

## Immutable authorities

The following SHA-256 values remained equal to their starting baselines:

- original calibration input:
  `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`;
- REVIEW1 reviewed CSV:
  `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c`;
- REVIEW1 summary:
  `48711714817c45246cefce8168a22c661d726e3cce8c24c97081abb04f236455`;
- durable text/table-detection ledger:
  `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03`;
- durable PDF-readiness ledger:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`;
- durable source-review ledger:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`;
- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- sorted corpus filename inventory:
  `32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322`.

Git path checks also found no changes to durable routing,
metadata-triage, source-review, PDF-readiness, or text/table-detection
ledgers; scout queue/coverage accounting; protected files; or `corpus/`.
The future REVIEW2 output directory does not exist.

## Safety confirmation

- selected calibration PDFs opened: 0;
- synthetic test-fixture PDFs opened: bounded local fixtures only;
- URLs opened: 0;
- network/API/model/hosted-search calls: 0;
- downloads/redownloads: 0;
- OCR runs: 0;
- retained full-page/full-document text or complete tables: 0;
- wage-table or final wage-value extraction: 0;
- ingestion or `gabriel.codify`: 0;
- wage-gap calculations, regressions, or causal claims: 0;
- remote inspection or push: 0.

The dashboard correctly reports
`refinement_prepared_after_failed_review`, prior gate `fail`,
`refined_re_review_before_extraction`, and all downstream stages
`not_started`.
