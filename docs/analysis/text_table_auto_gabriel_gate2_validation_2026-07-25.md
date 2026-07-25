# Gate 2 validation record

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

Validation result: **PASS**

## Execution gates

- The 150-case `--dry-run` completed before any live call: 150 cases, 769
  bounded pages, zero GABRIEL requests, zero failed cases.
- The one-case `--preflight-only --allow-gabriel` completed next: one
  successful strict-schema response, zero failed cases.
- The 150-case live run used `--allow-gabriel` only after that preflight:
  150 successful responses, 150 strict-schema-valid responses, zero failed or
  unavailable cases.
- Backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`.
- Full-run wall time: 452.075 seconds.

## Required commands

All exited zero:

```text
.venv/bin/python -m py_compile scripts/run_auto_gabriel_text_table_adjudication.py
.venv/bin/python -m py_compile scripts/test_auto_gabriel_text_table_adjudication.py
.venv/bin/python -m py_compile scripts/test_auto_gabriel_text_table_adjudication_gate2.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py
.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication.py
.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate2.py
.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
git diff --check
```

Results:

- Gate 1 regression tests: 14 passed.
- Gate 2 synthetic/mock tests: 10 passed.
- Repository schema: passed; 64 contracts, zero discourse rows, 64 coverage
  rows, and 3 city-attribute rows.
- Ingestion pipeline: 60 passed, 0 failed.
- Coverage: 64 contracts, 19 cities, 28 healthy matched pairs (10 exact and 18
  overlap), 2 exploratory adjacent pairs, and 6 unmatched safety units.
- Dashboard data: 51 states/DC, 35,589 municipalities, 2,436 scout-covered,
  and 4,726 candidate rows; calibration JSON parses.
- Dashboard frontend production build: passed. The existing greater-than-500
  kB chunk advisory is non-fatal.
- `git diff --check`: passed.

## Packet and output checks

- Ledger rows/unique calibration IDs: 150/150.
- Maximum GABRIEL input page count: 6.
- Maximum bounded input text: 6,000 characters per case.
- Navigation cap: no more than 4 pages per case.
- Request metadata rows: 150.
- Metadata rows reporting a prior label in the prompt: 0.
- Metadata rows reporting raw prompt saved: 0.
- Metadata rows reporting raw response saved: 0.
- Metadata rows reporting credential value saved: 0.
- Metadata rows reporting authorization header saved: 0.
- Failed-cases file: absent because there were no failures.
- Output files named as raw prompt/response, full text, table cells, or wage
  rows: 0.
- Secret-pattern scan across Gate 2 artifacts and status docs: 0 hits.
- Dashboard Gate 2 fields match the ledger/decision: 100% schema validity, 9
  high-confidence ready, 13 schema-update ready, 23 second review, 105
  excluded, 26.25% likely/p1 ready, 1.5152% wrong page, and
  `continue_schema_refinement`.

## Immutable inputs and authorities

Starting and final SHA-256 values match:

| Artifact | SHA-256 |
| --- | --- |
| Original calibration input | `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` |
| REVIEW1 reviewed CSV | `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c` |
| REVIEW2 reviewed CSV | `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a` |
| Independent blinded input | `a85cf58bd91fa523154824253bbdb5f63ca8150fb134330f8352643fcd5016ff` |
| Independent render manifest | `a77b80dea8288acd42816aa26865babd2300d8875d4619137d25a1528561f005` |
| Gate 1 ledger | `1bc8f564f47254f98f7ac0e0ba947c35bd6cb5d41df81112c5fb03f74dc665a0` |
| Gate 1 summary | `c1bb62d5e1cda8a8a9da9bbf128a61df439d4c551ba02d4af030edb9838544ec` |
| Gate 1 decision | `f0d277bd65f34fe058a0ab5a8c71a7a1062e13deb642a7856ee58b2516039893` |
| Durable text/table ledger | `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03` |
| Durable PDF-readiness ledger | `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953` |
| Durable source-review ledger | `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f` |
| `data/contracts.csv` | `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8` |
| `data/city_coverage.csv` | `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3` |

Git diff scoping also confirms no change under `corpus/`, durable routing,
metadata/content-triage, source-review, PDF-readiness, or text/table-detection
ledgers. Original calibration, REVIEW1, REVIEW2, independent packet inputs,
and Gate 1 outputs have no diff.

## Forbidden-action audit

- URLs/hosted search opened: 0
- downloads/redownloads: 0
- OCR runs: 0
- wage extraction runs or prompts: 0
- smaller extraction pilots: 0
- full text or complete tables saved: 0
- final/structured wage values saved: 0
- ingestion actions: 0
- `gabriel.codify` actions: 0
- durable-ledger mutations: 0
- wage-gap calculations/claims: 0
- regressions: 0
- remote inspections/fetches/pulls/pushes: 0

The only network/model actions were the explicitly authorized one-case
preflight and the subsequent 150 bounded GABRIEL adjudication calls.
