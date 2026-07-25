# Automated GABRIEL Gate 2 result

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

Method: `automated_local_visual_layout_navigation_offset_plus_gabriel_bounded_page_adjudication`

## Execution result

- Cases: 150
- GABRIEL backend: `huit_openai_responses_direct_sdk`
- GABRIEL model: `gpt-5.4-nano`
- Successful/schema-valid adjudications: 150/150 (100%)
- Failed or unavailable adjudications: 0
- Local pages evaluated: 769
- Existing rendered pages used for local features: 682
- Bounded text characters supplied: 632,553
- Wall runtime: 452.075 seconds
- Maximum observed packet: 6 pages and 6,000 bounded text characters
- Raw prompts/responses, full page text, full tables, and structured wage
  values saved: none

The no-call 150-case dry run passed before a one-case live preflight. The
preflight returned one successful strict-schema result. Only then was the
150-case live run started with `--allow-gabriel`.

## Final gate labels

| Label | Count |
| --- | ---: |
| `extraction_ready_high_confidence` | 9 |
| `extraction_ready_with_schema_update` | 13 |
| `second_review_required` | 23 |
| `exclude_for_now` | 105 |

Confidence was 110 high, 33 medium, and 7 low. High confidence includes many
confident exclusions; it must not be read as 110 extraction-ready cases.

## GABRIEL judgments

- Wage schedule present: 36 yes / 7 maybe / 107 no.
- Candidate relationship: 38 exact / 2 adjacent / 2 later-table / 2 wrong /
  105 no-candidate / 1 unknown.
- Extraction complexity: 1 easy / 45 moderate / 2 hard / 102 not
  extractable.
- Navigation needed: 9 yes / 118 no / 23 unknown.
- Navigation target found: 15 yes / 56 no / 68 not applicable / 11 unknown.

Dominant visual types were 65 prose-only, 30 no-table, 13 step-grade, 10
annual-salary, 8 classification-pay, 4 hourly, 4 benefits, 3
classification-without-pay, 3 index/contents, and 2 compact compensation
sheets. No ready row retained a GABRIEL negative non-wage family.

## Deterministic Gate 2 diagnostics

The most frequent diagnostics were 84 insufficient-role/pay-column cases, 73
benefit-term cases, 66 true-wage-table-evidence candidates, 65 no-candidate
cases, 51 non-wage numeric-table cases, 48 possible printed-page offsets, 45
compact candidates, 23 index/contents candidates, and 20 prose-only
candidates. These are overlapping local signals, not model labels.

Several counts are intentionally treated as overinclusive. In particular,
benefit terms appeared somewhere in 73 bounded packets while GABRIEL assigned
only 17 cases to the benefits family, and the compact diagnostic appeared 45
times while GABRIEL confirmed 2 compact sheets. Neither aggregate local signal
may independently authorize readiness.

The 23 second-review rows carry 18 generic insufficient-evidence codes, 10
local-structure-weak codes, 7 negative-family conflicts, 5 Gate 2
insufficient-role/pay-column vetoes, and 1 unresolved-navigation code. Counts
overlap by row.

## Authorization metrics

- Original likely/p1 ready: 21/80 = 26.25%; required at least 80%.
- Candidate-bearing wrong pages: 2/132 = 1.52%; required no more than 15%.
- Schema-valid responses: 150/150 = 100%; required at least 95%.
- Total ready rows: 22; fewer than the 30-row representation floor.
- Ready unit types: 10 non-safety / 7 fire / 5 police.
- Ready source types: 11 wage schedules/plans / 7 CBAs / 4 ordinances.
- Non-wage positive ready rows: 0.
- Systematic ambiguity check: passes under the encoded rule, but positive
  coverage and representation do not.

## Gate 1 failure-mode result

Gate 2 reduced wrong pages from 9 to 2 and unknown relationships from 10 to 1.
That apparent improvement largely reclassified weak packets as
`no_candidate_page`, which rose from 71 to 105. Ready rows fell from 28 to 22,
likely/p1 readiness fell from 33.75% to 26.25%, and second review rose from 19
to 23. Direct compact and offset rules did not recover enough positive cases.

The remaining central ambiguity is not a non-wage precision failure. It is
whether upstream likely/p1 documents truly lack schedule pages or whether
the bounded text/feature packet fails to make visually present tables legible
to the model. Gate 2 did not send rendered pixels to GABRIEL; it sent bounded
text plus derived render/layout features. That limitation matters most for
image-like, low-text, or arbitrary-job-title tables.

## Decision

`continue_schema_refinement`

The 500-document extraction is not allowed. A smaller extraction pilot is not
allowed. Gate 2 fails the 80% likely/p1 threshold by 53.75 percentage points,
has only 22 ready rows, and fails representation even though schema validity,
wrong-page control, and non-wage precision pass.

No URL, download/redownload, OCR, wage extraction, ingestion, codification,
wage-gap analysis, regression, durable-ledger mutation, remote inspection, or
push occurred.
