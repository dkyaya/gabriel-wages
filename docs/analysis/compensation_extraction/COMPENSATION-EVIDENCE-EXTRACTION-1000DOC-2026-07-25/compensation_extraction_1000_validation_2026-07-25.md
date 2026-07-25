# Repaired 1,000-document extraction validation — 2026-07-25

## Outcome

The mixed-disposition repair and unchanged six-path preflight pass. The live
new-cohort run is incomplete: 499 of 500 frozen new cases have strict-valid
structured results, while one longevity-routing case remains invalid. The
runner correctly stopped before cumulative materialization. Local tests,
dashboard generation, dashboard frontend build, repository validation,
ingestion regression tests, coverage audit, packet/hash controls, and protected
state checks pass.

Decision: `live_incomplete_schema_invalid`.

## Commands

- `.venv/bin/python -m py_compile scripts/run_compensation_evidence_extraction.py scripts/run_compensation_extraction_targeted_qa.py scripts/build_dashboard_data.py scripts/test_compensation_evidence_extraction_1000.py` — pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication.py` — 14/14 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate2.py` — 10/10 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate3_compensation.py` — 9/9 pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_500.py` — 10/10 pass.
- `.venv/bin/python scripts/test_compensation_extraction_targeted_qa.py` — 8/8 pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_1000.py` — 9/9 pass.
- `.venv/bin/python scripts/build_dashboard_data.py` — pass; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows regenerated.
- `npm --prefix docs/dashboard run build` — pass; Vite production build completed. The existing bundle-size warning is non-fatal.
- `.venv/bin/python scripts/validate.py` — pass; 64 contracts, zero discourse, 64 coverage rows, and three city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 pass.
- `.venv/bin/python ingest/audit_coverage.py` — pass; 28 healthy matched pairs (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check` — pass.

## Repair and regression gates

- `mixed_ready` missing quantitative sub-records: rejected.
- `mixed_ready` missing qualitative sub-records: rejected.
- Valid quantitative-only, qualitative-only, mixed, and non-base-only outcomes: accepted under mutually exclusive disposition rules.
- Non-base evidence inside the base quantitative array: rejected with a family-specific redacted error.
- Missing sub-record fabrication or post-hoc coercion: absent.
- Gate 1 and Gate 2 extraction modes: backward-compatible tests pass.
- Live 1,000 mode requires `--only-requires-gabriel yes`.

## Frozen selection and packet gates

- Exact cumulative identities: pass (1,000).
- Unique content hashes: pass (1,000).
- Corrected seed preserved: pass (500 identities; zero model calls).
- Frozen new identities: pass (500).
- Unit representation: pass (363 police / 237 fire / 400 non-safety).
- States/DC: 40; source families: six.
- Packet identity coverage: pass (1,000 cases; 5,767 rows).
- Page cap: pass (maximum six).
- Per-page text cap: pass (maximum 1,499).
- Per-case text cap: pass (maximum 5,999).
- Selection manifest SHA-256: pass,
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.

## GABRIEL gate and live result

- GABRIEL called only with `--allow-gabriel`, after local tests and preflight: pass.
- Unchanged representative preflight: 6/6 strict-valid.
- Corrected seed calls: zero.
- Frozen new cases requested: only the 500 `requires_gabriel=yes` identities.
- Live attempts: 551.
- Unique strict-valid live cases stored: 499/500 (99.8%).
- Request outcomes: 499 success, 51 schema-invalid, one request failure.
- Persistent unresolved case: `cex1000_150f3ac41a7919533b202cc2`.
- Persistent validation error: longevity evidence placed in base quantitative evidence.
- Cumulative materialization: not run.
- Cumulative observation, duplicate, page-pointer, conflict, contamination, and QA counts: not computed.

## Artifact and mutation checks

- The 499-case checkpoint contains only `extraction_case_id` plus validated parsed structured result; it is not a raw response or cumulative lane.
- Raw prompt/response saved: false.
- Full document/page text saved: false.
- Full tables saved: false.
- Encoded image copies saved: false.
- Credential, token, cookie, raw authorization header, or environment values saved: false.
- URLs/hosted search/download/redownload/OCR/scout/source review/verification: zero.
- Ingestion/`gabriel.codify`/final merge/wage-gap/regression: zero.
- Original Gate 1–3, durable source-review/PDF-readiness/text-table/content-triage, original 500 extraction, corrected targeted-QA, `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` mutations: zero.
- Remote inspection/fetch/pull/configuration: zero.

The corrected 500-document targeted-QA layer remains the latest complete valid
provisional extraction layer. The remaining readable parse-text pool is blocked
until the one frozen case is resolved and cumulative 1,000-case QA passes.
