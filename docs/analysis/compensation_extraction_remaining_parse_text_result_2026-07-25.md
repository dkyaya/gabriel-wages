# Remaining readable parse-text compensation extraction result

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-REMAINING-PARSE-TEXT-826-2026-07-25`

## Outcome

The remaining readable parse-text extraction stopped fail-closed at 825 of 826 strict-valid new cases. The seven-path representative preflight passed, GABRIEL ran only on the frozen remaining cases, and the corrected 1,000-document targeted-QA seed received zero model calls. One Hartland, Wisconsin police CBA case remained semantically invalid after ten bounded attempts because education/certification compensation was repeatedly placed in the base quantitative array.

Decision: `live_incomplete_schema_invalid`.

No cumulative 1,826-case provisional ledger was materialized and no new cumulative observation, duplicate, page-pointer, conflict, contamination, or QA count is claimed. The corrected 1,000-document targeted-QA shadow layer remains the latest complete valid provisional extraction layer.

## Frozen selection

- Remaining durable rows outside the prior selection: 827.
- Unique remaining readable content hashes selected: 826.
- Corrected no-call seed: 1,000 cases.
- Selection SHA-256: `43b768fba4e3d122727d2cbf9614885922a55be5f2bd1afd37d36f47a4695d81`.
- Units: 417 police, 202 fire, and 207 non-safety.
- States/DC: 48.
- Priorities: 430 p1, 391 p2, and 5 p3.
- Source families: 766 CBAs, 34 wage schedules/compensation plans, 10 memoranda/settlements, 10 ordinances/policies, 5 arbitration awards, and 1 factfinding record.

The 827-row/826-hash discrepancy is one exact North Miami, Florida content duplicate. The deterministic representative is `ttd_a930d5e423fad93db8dcaac1`; `ttd_ecb0448e2ddaf335f23eced8` remains documented as the excluded duplicate identity. The content hash was sent once.

## Packet and preflight

- Packet page records: 4,610.
- Maximum pages per case: 6.
- Maximum text characters per page: 1,499.
- Maximum text characters per case: 5,999.
- Full document/page text saved: no.
- Full tables saved: no.
- Raw prompts/responses saved: no.
- Encoded image copies saved: no.
- Seven-path preflight: 7/7 strict-valid.
- Backend: `huit_openai_responses_direct_sdk`.
- Model: `gpt-5.4-nano`.

An initial sandbox-restricted transport attempt could not reach the configured backend. It produced no valid adjudications and was superseded by the exact same authorized seven-case preflight, which passed 7/7. The definitive request metadata contains the successful preflight and live attempts only.

## Live checkpoint

- Frozen new cases: 826.
- Strict-valid stored cases: 825.
- Strict-valid rate: 99.8789%.
- Live request attempts: 861.
- Invalid or failed attempts: 36.
- Unresolved cases: 1.
- Seed GABRIEL calls: 0.
- Cumulative materialization: not run.
- QA: not run because materialization is all-or-nothing.

The sole unresolved identity is `cexrem_4a267735daf6729f5c4e4835`, corresponding to `ttd_539d4913967fae2729c554c2`, source review `sr_644c95449dcc515eb9b79120`, Village of Hartland, Wisconsin police, CBA. All ten attempts failed the same semantic rule: `education_or_certification` evidence may not appear in `quantitative_observations` as base wage.

The 825-case JSONL is a resumable intermediate checkpoint, not a lane ledger, cumulative provisional dataset, or analysis input. It must not be interpreted as complete extraction output.

## Decision and next action

The next action is a one-case education/certification-routing repair. A case-bounded contract should require non-base disposition when the only compensation evidence is education/certification pay, require an empty quantitative array, route the evidence exclusively to `non_base_wage_observations`, and prohibit fabrication. Only that unresolved case may be preflighted and called; the 1,000 seed and 825 stored remaining cases must not be resent.

Final merge, ingestion, codification, wage-gap analysis, regression, and any new selection or extraction remain prohibited.

## Boundary confirmation

No URL was opened; no hosted search, download/redownload, OCR, scout, source review, verification, ingestion, `gabriel.codify`, final merge, wage-gap calculation, regression, or causal analysis occurred. No durable upstream ledger, Gate output, original extraction ledger, or corrected targeted-QA shadow ledger was mutated. No full text/table, raw prompt/response, encoded image, credential value, token, cookie, or raw authorization header was retained.
