# Automated visual + GABRIEL adjudication gate 1 result

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

## Result

The completed method was
`automated_local_visual_layout_plus_gabriel_bounded_page_adjudication`.
It combined local PDF text-layer and geometry signals, existing local render
features, bounded contents/index navigation, a strict GABRIEL JSON judgment,
and deterministic fail-closed combination rules.

- Cases: **150**
- Local pages evaluated: **738**
- Existing rendered pages used for local features: **734**
- Bounded page-text characters supplied across prompts: **585,644**
- Per page maximum: **1,500**
- Per case maximum: **6,000**
- Pages per case maximum: **6**
- Navigation-page budget: **4**
- GABRIEL backend: `huit_openai_responses_direct_sdk`
- GABRIEL model: `gpt-5.4-nano`
- Successful schema-valid adjudications: **150**
- Failed or unavailable adjudications: **0**
- Schema-valid rate: **100.00%**
- Final live elapsed time: **493.799 seconds**

No raw prompt or response, full page text, full table, or structured wage
value was saved. Request metadata contains hashes, counts, status, timing, and
redacted failure fields only.

## Preflight and schema refinement

The original one-case preflight passed. The first 150-case pass produced 122
schema-valid responses and rejected 28: 24 malformed reason-code lists, 3
wrong-enum field placements, and 1 wrong relationship field placement. Those
28 were not accepted or heuristically repaired.

The runner was tightened to use a strict API JSON Schema while retaining the
same local evidence, prompt content, page budgets, and downstream validator.
A replacement one-case preflight passed, and the complete replacement
150-case pass achieved 150/150 schema validity. Only the replacement pass is
the final ledger and basis for this decision.

## Final labels

### Auto gate

- `extraction_ready_high_confidence`: **12**
- `extraction_ready_with_schema_update`: **16**
- `second_review_required`: **19**
- `exclude_for_now`: **103**

### Auto-gate confidence

- `high`: **93**
- `medium`: **51**
- `low`: **6**

### GABRIEL wage-schedule presence

- `yes`: **37**
- `maybe`: **12**
- `no`: **101**

### Candidate-page relationship

- `exact_table_page`: **46**
- `adjacent_to_table`: **9**
- `points_to_later_table`: **5**
- `wrong_page`: **9**
- `no_candidate_page`: **71**
- `unknown`: **10**

### Visual table type

- annual salary schedule: 10
- classification pay table: 9
- hourly schedule: 11
- step/grade: 13
- compact compensation sheet: 1
- benefits table: 5
- budget/fiscal table: 3
- classification without pay: 2
- index/contents: 8
- front matter: 5
- non-wage table: 1
- prose only: 67
- no table: 15

### Non-wage family

- `not_applicable`: 73
- benefits: 25
- budget/fiscal: 3
- classification without pay: 2
- index/contents: 14
- front matter: 4
- incentive/bonus prose: 3
- memorandum without table: 8
- other: 18

### Extraction complexity

- easy: 13
- moderate: 47
- hard: 4
- not extractable: 86

## Gate metrics

- Original likely/p1 denominator: **80**
- Original likely/p1 ready with high/medium confidence: **27**
- Original likely/p1 ready rate: **33.75%**
- Candidate-bearing denominator: **132**
- Wrong-page count: **9**
- Wrong-page rate: **6.82%**
- Total ready rows: **28**
- Ready unit types: police 5, fire 7, non-safety 16
- Ready source types: arbitration award 1, CBA 10, ordinance/policy 5,
  wage schedule/compensation plan 12
- Final ready rows with a GABRIEL negative non-wage family: **0**
- Second-review rows: **19**

## Extraction authorization criteria

| Criterion | Required | Observed | Pass |
|---|---:|---:|---|
| likely/p1 ready rate | at least 80% | 33.75% | no |
| wrong-page rate | at most 15% | 6.82% | yes |
| GABRIEL schema-valid rate | at least 95% | 100.00% | yes |
| non-wage/systematic ambiguity control | no major positive family | 0 negative-family ready rows; 12.67% second review | yes |
| representative ready set | at least 30 plus unit/source coverage | 28 | no |

The automated system fixed the schema-validity problem, sharply reduced the
wrong-page estimate, and downgraded most non-wage false positives. It did not
show that enough original likely/p1 candidates are true extraction-ready wage
schedules. The prior failure modes are therefore only partially resolved.

## Decision

`continue_schema_refinement`

- 500-document extraction allowed: **false**
- Smaller extraction pilot allowed: **false**
- Wage extraction started: **no**

The next task should refine candidate-page selection and the distinction
between prose/no-candidate cases and true wage-table pages, then repeat a
bounded calibration gate. It must not proceed to extraction on the strength of
the low wrong-page rate alone.

## Safety boundary

No URL was opened; no download, hosted search, OCR, wage extraction, ingestion,
`gabriel.codify`, wage-gap calculation, regression, or durable-ledger mutation
occurred. GABRIEL received only bounded, redacted evidence from the existing
150 local calibration cases.
