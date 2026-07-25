# Gate 3 compensation-evidence readiness audit

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`

Date: 2026-07-25

## Readiness result

**PASS FOR IMPLEMENTATION, DRY RUN, AND BOUNDED PREFLIGHT.** A supported
GABRIEL adjudication path exists. The OpenAI Responses SDK installed locally
exposes `input_image` inputs, but the configured HUIT endpoint/model's actual
acceptance of bounded data-URL images remains subject to the required one-case
vision preflight. The already proven bounded text/layout GABRIEL path is an
authorized fallback if vision input is unsupported.

The latest local commit before work was
`90891ea45aec078f37544891601fcd2801a7660c`. The tracked worktree was clean.
The only unrelated untracked items were the expected 785 local render aids
and the root `package-lock.json`; neither will be modified or committed.

Local ancestry checks passed for `90891ea`, `6b10da8`, `51f709a`, `c3580a4`,
`0e9430b`, `7438f1a`, `610f5e8`, `32ae355`, `827917b`, `11e689a`,
`b45876e`, `74a843a`, `985d581`, `46923a2`, `12b3f10`, `ed042c1`,
`79df80c`, and `e028432`. No remote was inspected.

## Why Gate 3 broadens the question

Gates 1 and 2 asked whether bounded pages showed a wage table suitable for a
narrow table-extraction path. That question protected precision, but it
discarded analytically useful evidence in settlement memoranda, bargaining
language, arbitration reasoning, CPI/COLA clauses, comparability language,
step-movement provisions, effective-date rules, and compensation-adjacent
benefit or stipend material.

Gate 3 instead classifies each case by its best research use. It keeps clean
tables and compact rate listings as quantitative evidence, recognizes prose
with specific rates/percentages/dates, preserves qualitative compensation-
setting mechanisms, separates non-base-wage compensation, and distinguishes
reference-only and genuinely irrelevant pages. This is classification only;
it creates neither quantitative observations nor coded mechanism evidence.

## Gate 2 authority and diagnosis

Gate 2 is complete and immutable:

- cases/schema-valid responses: 150/150 (100%);
- final labels: 9 high-confidence ready, 13 schema-update ready, 23 second
  review, and 105 excluded;
- original likely/p1 ready: 21/80 (26.25%);
- candidate-bearing wrong pages: 2/132 (1.52%);
- relationship `no_candidate_page`: 105;
- ready unit representation: 5 police, 7 fire, 10 non-safety;
- ready source representation: 7 CBAs, 4 ordinances/policies, and 11 wage
  schedules/compensation plans;
- decision: `continue_schema_refinement`.

Gate 2 demonstrated strong schema stability and narrow non-wage precision but
could not recover enough wage-table-ready cases. Gate 3 does not relabel those
failures as tables. It asks whether the same bounded pages nevertheless contain
specific quantitative prose, useful mechanism language, reference-only
signals, or non-base-wage compensation evidence.

## Render and GABRIEL capability

The independent render manifest contains 785 page images for all 150 cases,
at most six per case. All 785 files exist locally and total 106,889,932 bytes;
the largest six-image case is 1,208,902 bytes. Gate 3 may attach only selected
manifest images already within a case's six-page evidence packet.

Secret-safe configuration checks confirm:

- project dotenv present and credential configured;
- backend: `huit_openai_responses_direct_sdk`;
- model: `gpt-5.4-nano`;
- installed SDK version: 2.41.0;
- SDK image input type: present;
- bounded text/layout GABRIEL path: previously proven and available;
- request metadata can retain hashes/counts/status while omitting prompt,
  response, credentials, and authorization headers.

The execution order is mandatory: 150-case no-call dry run; one-case vision
preflight; automatic or separately invoked bounded text/layout preflight if
vision is unsupported; then a full 150-case run only in a preflight-proven
mode. A missing or failed text/layout GABRIEL path stops the live run.

## Frozen inputs

Starting SHA-256 values were recorded for the original calibration input,
REVIEW1, REVIEW2, independent blinded input/render manifest, Gate 1 ledger/
summary/decision, Gate 2 ledger/summary/decision, durable detection/readiness/
source-review ledgers, `data/contracts.csv`, and `data/city_coverage.csv`.
Gate 3 writes only to a new output directory. All frozen inputs and `corpus/`
must remain unchanged.

## Extraction remains prohibited

Gate 3 classifies potential research use. It does not extract rates, wage
rows, or qualitative mechanism observations. Even a positive decision creates
only a future-prompt authorization; no extraction runs during this task.

## Explicit boundary

- no source URL, hosted search, live source review, or URL verification;
- no download or redownload;
- no OCR;
- no wage extraction or final quantitative observations;
- no final qualitative mechanism extraction or observations;
- no full page/document text or complete tables saved;
- no ingestion or `gabriel.codify`;
- no wage-gap calculation/claim, causal claim, or regression;
- no mutation of durable routing, metadata/content-triage, source-review,
  PDF-readiness, or text/table-detection ledgers;
- no mutation of original calibration, REVIEW1, REVIEW2, independent packet,
  Gate 1, or Gate 2 outputs;
- no remote inspection, fetch, pull, push, or remote modification.
