# Independent human text/table adjudication rubric

Date: 2026-07-24

## Core visual test

Wage, salary, pay, increase, step, grade, or compensation language is not
enough. A conventional wage/salary schedule is confirmed only when the
reviewed page visibly connects employee, classification, grade, or rank rows
to wage, rate, salary, step, hourly, annual, or other recurring base-pay
columns. The relationship must be visually legible; text alignment or nearby
numbers alone does not satisfy the test.

A compact compensation sheet is a separate affirmative category. Use it only
when a compact visual list associates named roles, ranks, or compensation
components with corresponding pay amounts in a stable row/value layout. Do
not use it for ordinary wage prose, scattered monetary amounts, an aggregate
budget, or incentive language without a usable role-to-pay relationship.

## Negative families

Do not confirm a wage schedule for:

- prose describing percentage or dollar increases without a schedule;
- benefit, premium, insurance, pension, leave, or reimbursement tables;
- department budgets, payroll totals, fund summaries, fiscal impacts, or
  aggregate expenditure tables;
- classification/rank lists without corresponding pay;
- incentive, bonus, longevity, stipend, or differential prose without a
  usable schedule;
- contents, index, appendix-divider, cover, signature, or front-matter pages;
- non-wage appendices or other numeric tables.

Choose the closest `human_visual_table_type`, record the negative family in
`human_non_wage_family`, and normally set
`human_wage_schedule_present=no`. Use `maybe` only for genuine visual
ambiguity—not as a substitute for reading the page.

## Candidate-page relationship

- `exact_table_page`: a listed candidate page itself visibly satisfies the
  conventional schedule or compact-sheet rule.
- `adjacent_to_table`: a listed nearby page, not the candidate page itself,
  visibly satisfies the rule.
- `points_to_later_table`: the candidate/nearby page is contents, index, or an
  appendix pointer that names a target, and the named target is also checked
  inside the listed navigation-page budget and visibly satisfies the rule.
- `wrong_page`: candidate pages exist, but none of the bounded candidate,
  nearby, or verified navigation targets shows the claimed schedule.
- `no_candidate_page`: no candidate page was supplied.
- `unknown`: the bounded images/pages cannot support a defensible judgment.

Never call a contents/index page an exact or adjacent wage table. If it names
a target outside the listed budget, set `human_navigation_needed=yes`,
`human_navigation_target_found=no`, and require second review. A pointer may
be labeled `points_to_later_table` only after the target is visually checked
within budget.

## Navigation rule

The packet lists candidate pages, ±1 nearby pages, and no more than four
navigation-context pages. Inspect only those pages. Do not roam through the
document. If a source page points to several targets, prioritize an explicitly
named salary/wage/compensation schedule target and do not exceed the listed
budget. Record:

- whether navigation was needed;
- whether the named target was found within the listed pages;
- whether the target itself met the row/column or compact-sheet test.

When the bounded packet cannot reach a named target, choose
`second_review_required`; do not infer the target's contents from its title.

## Extraction recommendation

- `extraction_ready`: visually confirmed schedule or compact sheet, bounded
  page relationship resolved, stable row/column meaning, and no unresolved
  layout ambiguity.
- `extraction_ready_with_schema_update`: visually confirmed and bounded, but
  a distinct schema/layout rule is needed, including a valid compact
  compensation sheet or complex multi-period header.
- `second_review_required`: genuine ambiguity, missing bounded navigation
  target, weak render, conflicting page relationship, or low confidence.
- `exclude_for_now`: prose/non-wage/front matter, a wrong page without a
  resolved target, or material that is not extractable under the stated
  schedule definition.

The recommendation is calibration metadata only. Do not transcribe wage
values.

## Future authorization gate

The completed human file may support extraction only if all of these are
true:

1. the human-confirmed strict likely/p1 rate is at least 80%;
2. the candidate-bearing wrong-page rate is no more than 15%;
3. `extraction_ready` plus `extraction_ready_with_schema_update` rows are
   numerous and diverse enough to support the proposed scale;
4. no systematic false-positive family remains unresolved, including wage
   prose, benefits, budgets/fiscal tables, classification-without-pay,
   non-wage appendices, or index/navigation errors;
5. compact compensation sheets have an explicit schema rule and are not mixed
   with ordinary prose.

Failure of any condition keeps the 500-document extraction and any smaller
pilot closed and returns the workflow to refinement.
