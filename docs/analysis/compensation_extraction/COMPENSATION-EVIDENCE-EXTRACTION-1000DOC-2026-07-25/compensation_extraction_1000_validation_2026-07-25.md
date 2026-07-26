# Cumulative 1,000-document extraction validation — 2026-07-25

## Outcome

The one-case longevity preflight and live response passed, the frozen new
checkpoint reached 500/500, and cumulative provisional ledgers materialized
for all 1,000 identities. Structural integrity controls pass except for the
base/non-base routing gate: 126 active corrected-seed quantitative records are
flagged for targeted review. The resulting decision is
`blocked_by_integrity_qa_failure`.

## Commands

- `.venv/bin/python -m py_compile scripts/run_compensation_evidence_extraction.py scripts/run_compensation_extraction_targeted_qa.py scripts/build_dashboard_data.py` — pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_1000.py` — 12/12 pass.
- `.venv/bin/python scripts/test_compensation_evidence_extraction_500.py` — 10/10 pass.
- `.venv/bin/python scripts/test_compensation_extraction_targeted_qa.py` — 8/8 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication.py` — 14/14 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate2.py` — 10/10 pass.
- `.venv/bin/python scripts/test_auto_gabriel_text_table_adjudication_gate3_compensation.py` — 9/9 pass.
- `.venv/bin/python scripts/build_dashboard_data.py` — pass; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows regenerated.
- `npm --prefix docs/dashboard run build` — pass; Vite production build completed. The existing bundle-size warning is non-fatal.
- `.venv/bin/python scripts/validate.py` — pass; 64 contracts, zero discourse, 64 coverage rows, and three city-attribute rows conform.
- `.venv/bin/python ingest/test_pipeline.py` — 60/60 pass.
- `.venv/bin/python ingest/audit_coverage.py` — pass; 28 healthy matched pairs (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check` — pass.

## One-case controls

- Required identity: pass (`cex1000_150f3ac41a7919533b202cc2`).
- One-case preflight requests: exactly one; strict-valid.
- One-case live requests: exactly one; strict-valid.
- Other new cases resent: zero.
- Corrected seed calls: zero.
- One-case result: `non_base_wage`, zero quantitative records, zero
  qualitative records, two longevity non-base records.
- Packet bounds: six pages; 5,999 text characters; no per-page value exceeds
  1,500.
- Selection SHA-256: pass,
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.
- Original 499-case checkpoint was preserved during preflight and extended by
  exactly the valid longevity case during live execution.

## Cumulative ledger and QA controls

- Frozen identities: 1,000 / 1,000.
- New checkpoint cases: 500 / 500 unique.
- Cumulative case-level schema validity: 1,000 / 1,000 (100%).
- Packet rows: 5,767; packet limits pass.
- Active quantitative observations: 1,347.
- Active qualitative-mechanism observations: 1,464.
- Active mixed cases: 272.
- Active non-base-wage observations: 2,758.
- Reference/exclusion cases: 173.
- Duplicate observation IDs: zero.
- Invalid bounded page pointers: zero.
- Exact structured-content duplicates: nine canonicalized observations across
  seven groups; provenance preserved.
- Quantitative conflict groups: 82; 25 unresolved.
- Unresolved conflict rate: 1.8560%, below the 2% threshold.
- Possible base/non-base quantitative records: 126; integrity gate fails.
- Matched representation: pass (363 police / 237 fire / 400 non-safety).
- Review ledger: 215 rows, including 151 unresolved routing/conflict items.

## Artifact, secret, and mutation checks

- Raw prompt/response saved: false.
- Full document/page text saved: false.
- Full tables saved: false.
- Encoded image copies saved: false.
- Credential, API-key, token, cookie, raw authorization header, dotenv value,
  or environment value saved: false.
- Request metadata sensitive-value flags: zero.
- Secret-pattern scan findings were limited to source-code configuration key
  names and ordinary “pallbearer” evidence text; no secret value was present.
- URLs/hosted search/download/redownload/OCR/scout/source review/verification:
  zero.
- Ingestion/`gabriel.codify`/final merge/wage-gap/regression: zero.
- Gate 1–3, durable source-review/PDF-readiness/text-table/content-triage,
  original 500 extraction, corrected targeted-QA, `data/contracts.csv`,
  `data/city_coverage.csv`, and `corpus/` mutations: zero.
- Remote inspection/fetch/pull/configuration: zero.

The cumulative ledgers are provisional and separate from final analysis inputs.
Further readable parse-text extraction is blocked until targeted routing QA
reduces possible base/non-base contamination to zero and all other gates remain
green.
