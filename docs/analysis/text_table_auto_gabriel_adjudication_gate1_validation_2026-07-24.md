# Automated GABRIEL adjudication gate 1 validation

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

Validation date: 2026-07-25

## Command results

All requested validation commands exited 0:

- `.venv/bin/python -m py_compile scripts/run_auto_gabriel_text_table_adjudication.py`
- `.venv/bin/python -m py_compile scripts/test_auto_gabriel_text_table_adjudication.py`
- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication.py`
  — 14 tests passed.
- `.venv/bin/python scripts/build_dashboard_data.py`
  — built all dashboard JSON products successfully.
- `.venv/bin/python scripts/validate.py`
  — all rows conform; 64 contracts, 0 discourse rows, 64 coverage rows, and 3
  city-attribute rows.
- `.venv/bin/python ingest/test_pipeline.py`
  — 60 passed, 0 failed.
- `.venv/bin/python ingest/audit_coverage.py`
  — 64 contracts, 19 cities, 28 healthy matches (10 exact, 18 overlap), 2
  exploratory adjacent matches, and 6 unmatched safety units.
- `git diff --check`
  — passed.

The dashboard frontend production build also passed. Vite transformed 48
modules and emitted only its existing advisory that one JavaScript chunk is
larger than 500 kB after minification.

## Gate-run validation

- No-call dry run: 150 cases, 738 pages, 0 failed cases, 0 GABRIEL calls.
- Original live preflight: 1/1 schema-valid.
- Initial full pass: 122 schema-valid; 28 schema-invalid responses rejected.
- Strict JSON Schema replacement preflight: 1/1 schema-valid.
- Final replacement pass: 150 cases, 150 successful schema-valid responses,
  0 failed/unavailable cases, 738 pages, and 734 existing renders used.
- Final output size: six non-image files, approximately 292 KiB in total.
- Final request metadata says prior labels were absent, raw prompts/responses
  were not saved, credential values and authorization headers were not saved,
  and input page/text bounds were recorded for every case.

The first partial pass is not merged into the final ledger. Invalid responses
were never repaired or interpreted heuristically.

## Immutable inputs and protected state

SHA-256 checks remained identical for:

- original calibration input;
- REVIEW1 reviewed CSV;
- REVIEW2 reviewed CSV;
- independent blinded input;
- independent render manifest.

All 785 local render images still match the manifest byte sizes and SHA-256
values. `git diff --name-only` is empty for:

- original calibration packet;
- REVIEW1 outputs;
- REVIEW2 outputs;
- independent adjudication packet inputs;
- text/table detection ledgers;
- PDF-readiness ledgers;
- source-review ledgers;
- `data/contracts.csv`;
- `data/city_coverage.csv`;
- `corpus/`.

No routing or metadata-triage ledger is changed in the working tree.

## Safety and secrecy checks

- GABRIEL/API calls occurred only after a successful one-case preflight and
  only with `--allow-gabriel`.
- GABRIEL used the configured HUIT Responses direct SDK backend and
  `gpt-5.4-nano`; no secret value is recorded.
- The configured credential value is absent from every persistent gate output.
- No raw prompt, raw response, auth header, cookie, token, API key, or
  credential value is saved.
- Dashboard JSON parses and records calibration, not extraction.
- No URL was opened and no hosted search was called.
- No document was downloaded or redownloaded.
- No OCR, wage extraction, extraction pilot, 500-document extraction,
  ingestion, `gabriel.codify`, final wage observation, wage-gap calculation,
  wage-gap claim, causal claim, or regression occurred.
- No durable ledger, protected CSV, corpus file, independent packet input, or
  prior review output was mutated.
- No git remote was inspected or modified; nothing was pushed, fetched, or
  pulled.

## Outcome

Validation passes. The extraction decision remains
`continue_schema_refinement`; both extraction scales remain prohibited.
