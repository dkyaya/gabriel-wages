# Full Retained PDF-Readiness Serial Merge Validation

Date: 2026-07-24

Merge ID: `PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`

## Result

**PASS.** The durable cumulative PDF-readiness ledger, exact retained-PDF
authority equality, merge provenance, dashboard status, immutable upstream
layers, and project test suites pass all requested gates.

The merge was executed exactly once. Validation did not open a URL or
retained PDF, parse a PDF, download a document, run OCR, save extracted text,
extract wages, ingest, or codify.

## Compilation and offline/mock tests

The following modules compiled:

- `scripts/prepare_pdf_readiness_pilot.py`;
- `scripts/pdf_readiness_sources.py`;
- `scripts/audit_pdf_readiness_lanes.py`;
- `scripts/merge_pdf_readiness_lanes.py`;
- `scripts/test_pdf_readiness_planning.py`; and
- `scripts/build_dashboard_data.py`.

`scripts/test_pdf_readiness_planning.py` passed 21 / 21 tests. In addition
to the planner, local runner, and auditor coverage, merge tests require:

- preservation of all rows and readiness fields across multiple rounds;
- failure on duplicate PDF-readiness, source-review, or candidate identity;
- failure on a nonterminal row;
- failure on a non-merge-eligible audit;
- failure on retained-source identity mismatch;
- failure on artifact path, hash, byte-size, or content-type mismatch;
- failure on a forbidden-activity counter;
- failure when the durable target already exists;
- byte-identical cumulative/latest pointers;
- zero protected-layer mutation; and
- no network connection.

All tests use temporary synthetic CSVs, local PDF fixtures, and mocks. The
merge tests do not open PDFs.

## Final lane audits

Pilot 1:

- planned / ledger / terminal: 150 / 150 / 150;
- three `completed_merge_eligible` lanes;
- recommendation: `merge_all_pdf_readiness_lanes`.

Remainder:

- planned / ledger / terminal: 1,974 / 1,974 / 1,974;
- four `completed_merge_eligible` lanes;
- recommendation: `merge_all_pdf_readiness_lanes`.

Across both rounds, duplicate readiness/source-review/candidate identities,
missing rows, unexpected rows, hash failures, missing artifacts, and terminal
parser errors are zero.

## Independent durable-ledger verification

The independent CSV/JSON-only verifier confirmed:

- source-review rows: 2,150;
- retained-PDF source-review rows: 2,124;
- durable readiness rows: 2,124;
- unique readiness/source-review/candidate IDs: 2,124 / 2,124 / 2,124;
- exact retained source-review-ID equality: yes;
- exact retained candidate-queue-ID equality: yes;
- inherited identity, path, hash, size, content-type, and source-metadata
  mismatches: 0;
- readiness status: 2,124 `readiness_checked`;
- text layer present / partial / absent: 1,608 / 220 / 296;
- technical parseability high / medium / low: 1,608 / 220 / 296;
- next action parse-text-layer / OCR-later: 1,828 / 296;
- page counts: 2,124;
- page minimum / p90 / maximum: 1 / 84 / 463;
- total pages: 108,028;
- copied PDFs in the durable readiness directory: 0;
- forbidden-activity counters: 0;
- cumulative/latest ledger byte equality: yes; and
- cumulative/latest summary byte equality: yes.

Output hashes:

- cumulative readiness ledger:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`;
- cumulative readiness summary:
  `37de7bd0f0df859d7313dea2211c1362b548808d47211fbc9784097d6cdc3b16`.

## Dashboard

- `scripts/build_dashboard_data.py`: passed;
- dashboard JSON files parsed: 17 / 17;
- frontend Vite production build: passed;
- `pdf_readiness_phase = full_retained_merged`;
- retained PDFs / readiness rows: 2,124 / 2,124;
- durable merge status: `merged`;
- technical readiness: `complete_for_retained_pdfs`; and
- next recommendation: `text_layer_table_detection_pilot`.

OCR, ingestion, codification, wage extraction, and wage-gap analysis remain
`not_started`.

## Repository and ingestion validation

- `scripts/validate.py`: passed;
- `ingest/test_pipeline.py`: 60 passed, 0 failed;
- `ingest/audit_coverage.py`: completed; and
- `git diff --check`: passed.

Coverage remains:

- contracts: 64;
- cities: 19;
- healthy matched pairs: 28;
- exact-cycle pairs: 10;
- overlap-cycle pairs: 18;
- exploratory adjacent pairs: 2; and
- unmatched safety units: 6.

## Immutable upstream and protected layers

Post-merge hashes equal the pre-task values:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`;
- scout accounting:
  `bad2948a2990e91280b510e5d93c1ab29aa65959f83693a641a1e902836e5a21`;
- durable routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`;
- durable metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`;
- cumulative source-review ledger:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`;
- cumulative source-review summary:
  `21e36de3552e3db09fa2090ed46509d702b3d69237d31f5c49082fb1ad9b475a`;
- complete `corpus/` tree:
  `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a`.

## Safety and process boundary

- URLs opened during merge/validation: 0;
- network/API/model calls: 0;
- downloads/redownloads: 0 / 0;
- retained PDFs opened or parsed during merge/validation: 0;
- OCR runs: 0;
- full extracted-text artifacts: 0;
- wage tables/values extracted: 0 / 0;
- ingestion/codify actions: 0 / 0;
- scout queue/coverage mutations: 0;
- routing/metadata-triage/source-review-ledger mutations: 0;
- contracts/city coverage/`corpus/` mutations: 0;
- wage-gap calculations, causal claims, and regressions: 0;
- secret indicators in merged/product artifacts: 0; and
- remote inspection, fetch, pull, or push: 0.

The unrelated untracked root `package-lock.json` remains untouched.
