# Refined REVIEW2 validation

Date: 2026-07-24
Validated at: 2026-07-25T15:12:30Z
Review: `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`

## Result

**PASS.** REVIEW2 completed for all 150 locked calibration artifacts, the
dashboard reflects the failed extraction authorization gate, and all project,
ingestion, immutability, scope, bounded-output, and secret-safety checks
passed.

## Commands

The following completed successfully:

```text
.venv/bin/python -m py_compile scripts/review_text_table_calibration_subset.py scripts/test_text_table_calibration_review.py scripts/test_text_table_calibration_review_refined.py scripts/build_dashboard_data.py
.venv/bin/python scripts/test_text_table_calibration_review.py
.venv/bin/python scripts/test_text_table_calibration_review_refined.py
.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
npm run build  # from docs/dashboard
git diff --check
```

Results:

- Python compilation: pass
- Legacy calibration-review tests: 10/10 pass
- Refined calibration-review tests: 9/9 pass
- Dashboard data build: pass
- Dashboard production build: pass; Vite emitted only its existing
  chunk-size advisory
- Repository schema validation: pass
- Ingestion tests: 60/60 pass
- Diff whitespace check: pass

## REVIEW2 integrity and bounds

- reviewed rows: 150
- unique calibration IDs: 150
- unique text/table-detection IDs: 150
- unique PDF-readiness IDs: 150
- unique source-review IDs: 150
- unique candidate-queue row IDs: 150
- selected artifact-path set equals original 150-row input: yes
- every production row records one local PDF open: yes
- maximum retained reviewer-note length: 132 characters
- maximum retained extraction-gate-reason length: 114 characters
- PDF/image/text artifacts in REVIEW2 output: 0
- temporary rendered-page directory removed: yes
- dashboard JSON parses: yes
- high-risk secret signature matches in changed files: 0

The independent challenge retained only its 18-row label/diagnostic CSV. Its
temporary contact sheets and rendered images were deleted and are excluded
from the relay.

## Immutability

The following SHA-256 values still equal their pre-review values:

| Authority or protected input | SHA-256 |
|---|---|
| Original calibration input | `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` |
| REVIEW1 reviewed CSV | `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c` |
| REVIEW1 summary | `48711714817c45246cefce8168a22c661d726e3cce8c24c97081abb04f236455` |
| Durable text/table detection ledger | `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03` |
| Durable PDF-readiness ledger | `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953` |
| Durable source-review ledger | `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f` |
| `data/contracts.csv` | `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8` |
| `data/city_coverage.csv` | `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3` |
| Sorted corpus filename inventory | `32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322` |

No changed path exists under routing, metadata triage, source review, PDF
readiness, durable text/table detection, `data/contracts.csv`,
`data/city_coverage.csv`, or `corpus/`.

## Safety confirmations

- only the original 150 selected local PDF artifacts were eligible/opened;
- URLs opened: 0;
- network/API/model calls: 0;
- redownloads: 0;
- OCR runs: 0;
- full document/page text retained: 0;
- full tables retained: 0;
- final wage extraction: 0;
- ingestion actions: 0;
- codify actions: 0;
- durable-ledger mutations: 0;
- remote inspection/push: 0.

The original input and REVIEW1 remained byte-identical. The unrelated
pre-existing untracked root `package-lock.json` remained untouched.

## Corpus snapshot

`ingest/audit_coverage.py` reports 64 contracts, 19 cities, 28 healthy
matched pairs (10 exact and 18 overlap), two exploratory adjacent matches,
and six unmatched safety units.

## Validation note

An initial independent audit assertion expected the CSV boolean
`pdf_opened_review` to serialize as `true`; the reviewed CSV correctly uses
the project convention `1`. The read-only assertion was corrected and the
full audit then passed. No production output or protected input was changed
by that check.
