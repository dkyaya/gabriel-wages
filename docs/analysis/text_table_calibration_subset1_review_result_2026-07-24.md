# Text/Table Calibration Subset 1 Review Result

## Outcome

The 150-row calibration packet completed a bounded
`codex_assisted_local_adjudication` review. This was not independent human
manual review. The helper verified each retained artifact against the durable
hash and byte size, opened only the 150 locked local PDFs, and inspected at
most five candidate, adjacent, or first-page-context pages per document.

The result is **fail for extraction authorization**. The assisted labels meet
the specified likely-signal concordance threshold, but 55 / 150 rows need
second review, 59 are structurally hard, and the adjudicator shares text and
numeric-structure features with the original detector. A five-row rendered
page challenge then found material disagreement in all five cases: four
purported table layouts were wage-related prose or a document front page, and
one `no_wage_table` result had a contents entry pointing to a later salary
table. Assisted concordance must not be reported as independent ground-truth
precision.

## Execution

- review ID:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
- input rows: 150
- reviewed/adjudicated rows: 150
- fully reviewed under assisted rules: 95
- needs second review: 55
- local PDFs opened: 150
- pages inspected: 630
- pages returning text: 612
- bounded characters inspected in memory: 1,447,440
- parser: `pypdf 6.13.2`
- elapsed local review time: 10.915 seconds
- missing artifacts / hash failures / size failures: 0 / 0 / 0
- original input SHA-256 before and after:
  `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`

One unlikely row from North Plainfield, New Jersey returned no text on its two
bounded context pages. It remains `needs_second_review`; OCR was not run.
`pypdf` repaired several malformed object pointers but produced no terminal
parser failure.

## Visual QA gate

Five calibration artifacts were selected after the assisted pass to challenge
`step_grade`, `rank_step`, `annual_salary_schedule`, `hourly_schedule`, and
`no_wage_table` outcomes. One rendered page from each locked local artifact
was inspected.

- The four assisted layout labels did not show the claimed table structure on
  the checked page; they showed wage-related prose, benefit provisions, a
  memorandum, or a document front page.
- The assisted `no_wage_table` case had a contents page that explicitly
  pointed to a later salary table, outside the bounded pages used by the
  assisted rule.

This is a small challenge sample rather than a row-level relabeling of the
entire packet. It is nevertheless sufficient to reject the assisted pass as
an extraction gate. The detailed record is in
`calibration_visual_qa_spotcheck.md`.

## Assisted review labels

### Page-hint precision labels

- correct: 118
- partially correct: 14
- incorrect: 0
- not applicable because no candidate hint: 17
- unknown because bounded pages yielded no text: 1

Among the 132 rows with an adjudicable candidate hint, 132 were correct or
partially correct under the assisted structural rules. This is detector /
adjudicator concordance, not independent precision.

### Wage-table presence labels

- yes: 112
- maybe: 22
- no: 15
- unknown: 1

### Wage-table page match

- exact: 132
- nearby: 0
- wrong page: 2
- no wage table: 15
- unknown: 1

### Contract-period labels

Contract-period presence:

- yes: 99
- maybe: 30
- no: 20
- unknown: 1

Contract-period hint match:

- correct: 68
- partially correct: 30
- incorrect: 12
- no period found: 20
- unknown: 20

By frozen contract-period signal:

- likely: 61 correct, 25 partial, 12 incorrect, 8 no period found
  (86 / 106 correct-or-partial);
- possible: 7 correct, 5 partial, 2 no period found, 11 unknown;
- unlikely: 10 no period found and 9 unknown.

### Layout

- step/grade: 65
- rank/step: 40
- annual salary schedule: 15
- hourly schedule: 8
- prose only: 5
- appendix table: 1
- no wage table: 15
- unknown: 1

### Extraction complexity

- easy: 11
- moderate: 65
- hard: 59
- not extractable under this bounded pass: 15

### Recommended action

- include in a wage-table extraction pilot: 76
- include after schema update: 36
- manual review only: 23
- exclude for now: 15

Reviewer confidence:

- high: 51
- medium: 83
- low: 16

## Usefulness by calibration stratum

“Useful” means an assisted `yes`/`maybe` presence label or a
correct/partially-correct page hint.

| Stratum | Rows | Useful | Assisted useful rate | Correct/partial hints |
|---|---:|---:|---:|---:|
| likely signal | 80 | 80 | 100.0% | 80 |
| possible signal | 58 | 53 | 91.4% | 52 |
| unlikely signal | 12 | 1 | 8.3% | 0 |
| extraction p1 | 80 | 80 | 100.0% | 80 |
| extraction p2 | 63 | 54 | 85.7% | 52 |
| extraction p3 | 7 | 0 | 0.0% | 0 |
| police | 51 | 45 | 88.2% | 45 |
| fire | 44 | 40 | 90.9% | 39 |
| non-safety | 55 | 49 | 89.1% | 48 |

By source type:

- wage schedule / compensation plan: 29 / 30 useful;
- memorandum / settlement: 15 / 15;
- ordinance / policy: 15 / 16;
- arbitration award: 7 / 8;
- CBA: 67 / 80;
- factfinding: 1 / 1.

By preliminary officialness:

- official municipal: 45 / 52 useful;
- official state repository: 21 / 23;
- official union: 15 / 16;
- uncertain: 44 / 50;
- unknown: 9 / 9.

By page-count bin, assisted useful rates range from 81.8% for 26–50 pages to
100% for over 100 pages. This does not establish population prevalence
because the calibration sample deliberately oversampled signal and edge
strata.

## False-positive and extraction issues

The 38 non-`not_applicable`/unknown false-positive-family assignments were:

- other bounded signal without a confirmed table: 18;
- benefit table: 10;
- non-wage schedule: 4;
- classification without pay: 2;
- index or contents: 1;
- numeric appendix: 1;
- percentage prose: 1;
- unknown because no bounded text: 1.

Common extraction difficulties are multi-page continuation, partial text
layers, ambiguous prose/schedule boundaries, rank/classification labels that
need normalization, and effective-date columns that must remain linked to
rate basis. Hard or nonextractable labels affect 74 / 150 rows.

## Scale recommendation

Do **not** run the proposed 500-document extraction. The calibration does not
provide an independent precision estimate, and the visual challenge found
systematic confusion between wage-related prose and actual tables/layouts.

The next task should refine the detector and calibration schema to require
visual or structural table evidence, add separate labels for “wage language”
and “actual tabular schedule,” and then rerun an independently adjudicated
calibration subset. If that revised review passes, begin with a smaller
provisional extraction pilot before considering 500 documents. Do not extract
all 1,828 or run OCR automatically.

## Activity boundary

No URL was opened, nothing was downloaded or redownloaded, OCR did not run,
no complete page/document text or table was saved, and no final wage value or
analysis-ready wage observation was created. No ingestion, codification,
scout accounting, durable-ledger mutation, wage-gap work, regression, remote
inspection, or push occurred. The original prepared calibration input remains
byte-identical to its committed version.
