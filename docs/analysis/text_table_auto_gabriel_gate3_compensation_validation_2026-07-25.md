# Gate 3 compensation-evidence validation

Gate: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`

## Execution gates

- Readiness began at clean tracked commit
  `90891ea45aec078f37544891601fcd2801a7660c`; every requested ancestor was
  verified locally.
- The 150-case dry run completed over 769 bounded pages with zero API calls.
- The first image preflight reached the endpoint but was rejected before
  adjudication because the endpoint does not allow JSON Schema `uniqueItems`.
  No case response was produced. The unsupported transport keyword was removed
  while local controlled-value validation remained strict.
- The corrected one-case image preflight passed. Only then did the 150-case
  live run begin with `--allow-gabriel`.
- The primary pass returned 145 locally valid responses and five responses
  with repeated allowed qualitative-field values. A resumable five-case retry
  normalized duplicates locally and preserved the other 145 rows.
- Final result: 150/150 `success`, 150/150 schema valid, zero failed cases.
- Image evidence was used for all 150 cases; no fallback occurred.

## Required commands

All passed after the one placement defect described below was fixed:

- `python -m py_compile` for the runner, Gate 1 test, Gate 2 test, Gate 3 test,
  and dashboard builder.
- `scripts/test_auto_gabriel_text_table_adjudication.py`: 14/14 passed.
- `scripts/test_auto_gabriel_text_table_adjudication_gate2.py`: 10/10 passed.
- `scripts/test_auto_gabriel_text_table_adjudication_gate3_compensation.py`:
  9/9 passed, including mocked image-to-text fallback.
- `scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589
  municipalities, 2,436 scout-covered municipalities, and 4,726 candidate
  rows.
- `scripts/validate.py`: passed; 64 contracts, 0 discourse rows, 64 coverage
  rows, and 3 city-attribute rows.
- `ingest/test_pipeline.py`: 60/60 passed.
- `ingest/audit_coverage.py`: 28 healthy matched pairs (10 exact, 18 overlap),
  2 exploratory adjacent pairs, and 6 unmatched safety units.
- Dashboard production build: passed; the existing chunk-size advisory remains
  informational.
- `git diff --check`: passed after removal of two Markdown-template trailing
  spaces.

During the first regression pass, Gate 1/2 dry-run tests caught that the new
saved-rationale redaction loop had been inserted in the legacy output writer.
It was moved into the Gate 3 writer. All Gate 1, Gate 2, and Gate 3 tests then
passed. No source or adjudication authority was changed by this defect.

## Packet and artifact checks

- Ledger and request metadata each contain exactly 150 rows.
- Maximum pages and images per case: six.
- Maximum bounded prompt text per case: 6,000 characters; per-page construction
  remains capped at 1,500.
- Raw prompts, raw responses, encoded image copies, full text, full tables,
  structured wage observations, and final qualitative observations were not
  saved.
- Saved short rationales are at most 300 characters and numeric amounts/years
  are redacted. Reason codes and controlled field-family lists contain no wage
  values.
- Request metadata reports no prior labels in prompts, no raw prompt/response
  saving, no credential saving, and no authorization-header saving.
- Secret-pattern scans found no credential or auth-bearing artifact.
- Dashboard JSON parses and validates the Gate 3 source/decision invariants.

## Immutable authority checks

Before/after hashes remained equal for the original calibration input,
REVIEW1, REVIEW2, the independent blinded input/render manifest, Gate 1, Gate
2, `data/contracts.csv`, `data/city_coverage.csv`, and the cumulative
text/table-detection, PDF-readiness, and source-review ledgers. Representative
verified hashes include:

- original calibration input: `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`
- independent blinded input: `a85cf58bd91fa523154824253bbdb5f63ca8150fb134330f8352643fcd5016ff`
- Gate 1 ledger: `1bc8f564f47254f98f7ac0e0ba947c35bd6cb5d41df81112c5fb03f74dc665a0`
- Gate 2 ledger: `149a55c9d1843b4daecefd3bec6a7bb6f4ea41f469b33f2c20342d40be6fce9e`
- contracts: `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- coverage: `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`

No diff exists under protected `corpus/` or durable routing, metadata-triage,
source-review, PDF-readiness, or text/table-detection ledger paths.

## Side-effect boundary

GABRIEL calls occurred only after the corrected successful preflight and with
`--allow-gabriel`. No URL/hosted search, download/redownload, OCR, scout,
source review, URL verification, wage extraction, qualitative final
extraction, ingestion, `gabriel.codify`, wage-gap work, regression, remote
inspection, fetch/pull/push, or durable-ledger mutation occurred.
