# Provisional 500-document compensation extraction readiness audit

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25`

## Result

**PASS FOR IMPLEMENTATION AND NO-CALL SELECTION FREEZE.** Live extraction is
not authorized until the exact 500-case packet passes local validation and a
four-path bounded GABRIEL preflight succeeds.

Work began at clean tracked commit
`207657535563117295f302ca04c220f50f4c868e`. The only unrelated untracked
items are the 785 previously rendered Gate 3 calibration pages and the root
`package-lock.json`; both remain outside this task and its commit. No remote
operation is needed or permitted.

## Local eligible universe

The latest text/table-detection ledger has 1,828 rows and 1,828 unique local
artifact paths. Every corresponding PDF-readiness row reports a checked local
artifact, verified hash, valid PDF signature, no OCR requirement, and high or
medium technical parseability. All artifact files exist locally. The universe
contains 1,826 unique content hashes after duplicate-content control.

Detection signals include 1,067 `likely/p1`, 749 possible, and 12 unlikely
cases. Unit coverage is 782 police, 439 fire, and 607 non-safety rows. Source
coverage includes 1,719 CBAs plus 109 wage plans, ordinances, memoranda,
arbitration awards, and factfinding documents.

There are 416 state/municipality groups with both at least one safety and one
non-safety candidate, comprising 1,119 eligible rows. This is sufficient to
freeze exactly 500 unique document identities while requiring a selected
non-safety partner for every selected police/fire document.

## GABRIEL configuration

The project dotenv exists and the required subscription credential appears
configured; no value was printed or saved. The authorized backend/model are
`huit_openai_responses_direct_sdk` and `gpt-5.4-nano`. Calls require explicit
`--allow-gabriel`, a successful no-call packet freeze, and a schema-valid
representative preflight.

## Immutable starting hashes

- Gate 3 ledger: `3b1d2014278b9151d490aa4d273eeec5cdcf5b05a438f97b693070a05bd70e1e`
- text/table detection: `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03`
- PDF readiness: `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`
- source review: `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`
- content triage: `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`
- `data/contracts.csv`: `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`: `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`

## Bounded extraction design

The runner will select at most six pages per document from durable candidate
page references and immediate neighbors. It will cap text at 1,500 characters
per page and 6,000 per case. Existing rendered images may be attached only
where already available; images will never be copied or encoded to disk.
Structured provisional observations, page pointers, confidence, reason codes,
and QA status may be saved. Full page/document text, full tables, raw prompts,
raw responses, and final analysis observations may not be saved.

## Explicit boundary

No URL/hosted search, download/redownload, OCR, scout, source review, URL
verification, ingestion, `gabriel.codify`, final analysis dataset, wage-gap
calculation, regression, causal claim, remote inspection, fetch/pull/push, or
durable-ledger mutation is allowed. The run must stop before final merge.
