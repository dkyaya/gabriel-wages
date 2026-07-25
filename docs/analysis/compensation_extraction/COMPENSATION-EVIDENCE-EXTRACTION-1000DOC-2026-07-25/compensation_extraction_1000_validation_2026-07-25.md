# Provisional 1,000-document extraction validation — 2026-07-25

## Outcome

Local implementation, packet, dashboard, repository, ingestion-regression,
and protected-state checks pass. The live extraction gate does not pass:
representative preflight was 5/6 strict semantic-schema valid. The runner
stopped before all live lanes, so this is a successful validation of the
fail-closed workflow—not a successful 1,000-document extraction.

## Commands

- `.venv/bin/python -m py_compile scripts/run_compensation_evidence_extraction.py scripts/run_compensation_extraction_targeted_qa.py scripts/build_dashboard_data.py scripts/test_compensation_evidence_extraction_1000.py` — pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication.py` — 14/14 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate2.py` — 10/10 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate3_compensation.py` — 9/9 pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_500.py` — 10/10 pass.
- `.venv/bin/python scripts/test_compensation_extraction_targeted_qa.py` — 8/8 pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_1000.py` — 6/6 pass.
- `.venv/bin/python scripts/build_dashboard_data.py` — pass; 51 states/DC,
  35,589 municipalities, 2,436 scout-covered municipalities, and 4,726
  candidate rows regenerated.
- `npm --prefix docs/dashboard run build` — pass; Vite production build
  completed. The existing bundle-size warning is non-fatal.
- `.venv/bin/python scripts/validate.py` — pass; 64 contracts, zero discourse,
  64 coverage rows, and three city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 pass.
- `.venv/bin/python ingest/audit_coverage.py` — pass; 28 healthy matched pairs
  (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched
  safety units.
- `git diff --check` — pass.

## Frozen selection and packet gates

- Exact cumulative identities: pass (1,000).
- Unique content hashes: pass (1,000).
- Corrected seed preserved without new calls: pass (500).
- New retained identities: pass (500).
- Unit representation: pass (363 police / 237 fire / 400 non-safety).
- Explicit selected non-safety partner pointers: pass (all rows).
- States/DC: 40; source families: six.
- Packet identity coverage: pass (1,000 cases; 5,767 rows).
- Page cap: pass (maximum six).
- Per-page text cap: pass (maximum 1,499).
- Per-case text cap: pass (maximum 5,999).
- Selection manifest SHA-256: pass,
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.

## GABRIEL gate

- GABRIEL called only after no-call freeze and local validation: pass.
- `--allow-gabriel` used: pass.
- Representative new cases attempted: six.
- Strict schema valid: five.
- Strict schema invalid: one (`mixed_ready` missing required sub-record type).
- Corrected seed calls: zero.
- Live new-document extraction attempts: zero.
- Preflight decision: fail closed.

## Artifact and mutation checks

- Raw prompt/response saved: false.
- Full document/page text saved: false.
- Full tables saved: false.
- Encoded image copies saved: false.
- Credentials, tokens, cookies, raw authorization headers, or environment
  values saved: false.
- Invalid or fabricated 1,000-document observation ledgers created: false.
- URLs/hosted search/download/redownload/OCR/scout/source review/verification:
  zero.
- Ingestion/`gabriel.codify`/final merge/wage-gap/regression: zero.
- Original Gate 1–3, durable source-review/PDF-readiness/text-table/content-
  triage, original 500 extraction, corrected targeted-QA, `data/contracts.csv`,
  `data/city_coverage.csv`, and `corpus/` mutations: zero.
- Remote inspection/fetch/pull/configuration: zero.

The only API activity was the six-case bounded preflight. Request metadata
contains hashes, sizes, timing, token counts, statuses, and redacted errors;
it contains no credential values or auth-bearing material.
