# Validation — provisional 500-document compensation extraction

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25`

## Result

Validation passed for repository integrity, packet bounds, final case-level
schema validity, separate-lane materialization, dashboard integration, and
forbidden-side-effect controls. Integrity QA passes. Scale QA remains on hold
by design; this document does not override
`premature_pending_targeted_qa`.

## Commands

All exited zero:

- `.venv/bin/python -m py_compile` for the Gate runner, extraction runner,
  extraction test, and dashboard builder.
- Gate 1 offline tests: 14 / 14.
- Gate 2 offline tests: 10 / 10.
- Gate 3 compensation offline tests: 9 / 9.
- Provisional extraction offline/mock tests: 10 / 10.
- `.venv/bin/python scripts/build_dashboard_data.py`.
- Dashboard `npm run build` (the existing Vite chunk-size warning remains
  informational).
- `.venv/bin/python scripts/validate.py`.
- `.venv/bin/python ingest/test_pipeline.py`: 60 / 60.
- `.venv/bin/python ingest/audit_coverage.py`.
- `git diff --check`.

Coverage remains 64 contracts, 19 cities, 28 healthy matches (10 exact and 18
overlap), two exploratory adjacent matches, and six unmatched safety units.

## Extraction and packet checks

- Selection: exactly 500 rows, 500 document IDs, and 500 content hashes.
- Frozen selection SHA-256:
  `2341e68426e5e62bdf406817fed17c703ee116d7c31af81f9e73b8b96ad583fb`.
- Packet: 2,843 page records; maximum six pages per case, 1,499 characters per
  page, and 5,999 per case.
- Packet manifest contains page pointers and feature counts, not bounded page
  text.
- Preflight: four of four successful and schema-valid.
- Live: 500 final schema-valid cases after bounded retries; 528 live attempts
  comprise 500 successes, 26 locally rejected semantic-schema responses, and
  two timeouts.
- Observation page pointers outside the frozen packet: zero.
- Duplicate observation IDs: zero.
- Exact structured-content duplicates are retained and flagged: two
  quantitative and one non-base-wage.
- Potential quantitative conflict groups: 83.
- Possible non-base-wage quantitative records flagged: 102.

## Artifact and secret safety

- Request metadata rows: 532 (four preflight plus 528 live attempts).
- Every metadata row says raw prompt, raw response, encoded image, credential
  value, and authorization header retention are false.
- Output directory contains no PDF, PNG, JPG, or JPEG file and no filename
  containing `raw_prompt` or `raw_response`.
- Secret-pattern scan passed. No key, token, cookie, credential value, raw
  authorization header, or dotenv value was printed or saved.
- The resumability checkpoint contains only parsed strict-schema case objects;
  each line is bounded below 17,000 characters and has only
  `extraction_case_id` and `result` top-level keys.
- No full document text, full page text, full table, or encoded image copy was
  saved.

## Immutable/protected inputs

Pre/post SHA-256 values match:

- Gate 3 ledger:
  `3b1d2014278b9151d490aa4d273eeec5cdcf5b05a438f97b693070a05bd70e1e`.
- Detection latest:
  `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03`.
- PDF readiness latest:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`.
- Source review cumulative:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`.
- Content triage latest:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`.
- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`.
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`.

Tracked diffs are empty for the original calibration input, REVIEW1, REVIEW2,
independent adjudication inputs, Gates 1–3, all durable ledgers, `corpus/`, and
the two protected data CSVs.

## Forbidden-action confirmation

GABRIEL calls occurred only after the four-case preflight passed and only with
explicit `--allow-gabriel`. The only network use was the authorized bounded
GABRIEL API transport. No URL was opened; no hosted search, download,
redownload, OCR, scout, source review, URL verification, ingestion,
`gabriel.codify`, final merge, wage-gap calculation, regression, remote
inspection, or push occurred.
