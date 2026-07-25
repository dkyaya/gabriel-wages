# Full Text/Table Detection Serial-Merge Validation

## Result

`passed`

The serial offline merge, durable outputs, dashboard refresh, and repository
boundaries passed all requested validation gates.

## Commands completed

The following compiled successfully:

- `scripts/prepare_text_table_detection_pilot.py`
- `scripts/text_table_detection_sources.py`
- `scripts/audit_text_table_detection_lanes.py`
- `scripts/merge_text_table_detection_lanes.py`
- `scripts/test_text_table_detection_planning.py`
- `scripts/build_dashboard_data.py`

The expanded synthetic/offline text-table suite passed 24 / 24 tests. It
includes multi-lane merge preservation; duplicate detection, PDF-readiness,
source-review, and candidate identity rejection; nonterminal and
non-merge-eligible rejection; authority identity and artifact-field mismatch
rejection; existing-target fail-closed behavior; no-network enforcement; and
protected-file stability.

The final lane auditor returned:

- planned / ledger / terminal: 1,828 / 1,828 / 1,828
- lane classification:
  `completed_merge_eligible` 4
- merge recommendation:
  `merge_all_text_table_detection_lanes`

The following also passed:

- `scripts/build_dashboard_data.py`
- `scripts/validate.py`
- `ingest/test_pipeline.py`: 60 passed, 0 failed
- `ingest/audit_coverage.py`
- `git diff --check`
- dashboard frontend production build
- dashboard JSON parsing

## Independent durable-output validation

An independent offline validator confirmed:

- durable / parse-text authority rows: 1,828 / 1,828
- exact PDF-readiness identity-set equality: yes
- exact source-review and candidate identity correspondence: yes
- exact inherited path/hash/size/type/page-count/text-layer equality: yes
- duplicate detection/readiness/source/candidate identities: 0 / 0 / 0 / 0
- terminal `detection_checked`: 1,828
- cumulative and latest ledger bytes: identical
- cumulative and latest summary bytes: identical
- full-run rows all carry the requested merge ID and non-extracted stage
- Pilot 1 rows separately concatenated: 0
- secret-shaped credential findings in durable artifacts: 0
- full extracted text files in durable artifacts: 0

## Protected scope

Starting hashes remain unchanged for:

- `data/contracts.csv`
- `data/city_coverage.csv`
- national candidate queue
- municipality scout-coverage ledger
- durable URL-routing ledger
- cumulative metadata-triage ledger
- cumulative source-review ledger
- cumulative PDF-readiness ledger

The `corpus/` file listing is unchanged, and `git diff` shows no protected or
upstream-ledger mutation.

The coverage snapshot remains:

- contracts: 64
- cities: 19
- healthy matched pairs: 28
  - exact-cycle: 10
  - overlap-cycle: 18
- exploratory adjacent matches: 2
- unmatched safety units: 6

## Prohibited activity confirmation

During the merge and validation:

- URLs opened: 0
- network/API/model calls: 0
- downloads/redownloads: 0 / 0
- PDF parsing / OCR during merge: 0 / 0
- full extracted text saved: 0
- final wage values extracted: 0
- ingestion / codify actions: 0 / 0
- scout queue/coverage accounting mutations: 0
- routing / metadata-triage / source-review / PDF-readiness mutations:
  0 / 0 / 0 / 0
- wage-gap calculations / regressions: 0 / 0
- remote inspection / fetch / pull / push: 0 / 0 / 0 / 0

Validation artifacts are under:
`tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/serial_merge_validation_2026-07-24/`.
