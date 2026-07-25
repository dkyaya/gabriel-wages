# Independent text/table adjudication instructions

Packet: `TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`

This is an independent human review packet. Do not consult REVIEW1 or REVIEW2
labels while reviewing. Do not extract final wage values.

## Review boundary

- Inspect only each row's listed candidate, nearby, and navigation pages.
- Candidate context uses a ±1-page window.
- Navigation context is capped at 4 pages per case.
- Rendered aids are capped at 6 pages per case.
- If a contents/index/appendix page names a target outside the listed page
  budget, record navigation as needed but target not found; do not label the
  source page as an exact table.
- Record labels and short notes only. Do not save page text, full tables, or
  structured wage values.

## Decisive visual rule

Wage/pay language by itself is not a wage schedule. Confirm a conventional
wage schedule only when the inspected page visibly combines employee,
classification, grade, or rank rows with wage, rate, salary, step, hourly, or
annual pay columns. A genuinely compact compensation sheet may be labeled
separately when it presents named roles or compensation components with
corresponding pay amounts in a stable visual list, even without a conventional
grid.

Benefits, aggregate budgets, fiscal summaries, classification lists without
pay, percentage-increase prose, contents/index pages, front matter, and other
non-wage tables are not confirmed wage schedules.

## Allowed values

- `human_review_status`: `not_reviewed`, `reviewed`, `needs_second_review`, `exclude_from_adjudication`
- `human_wage_schedule_present`: `yes`, `maybe`, `no`, `unknown`
- `human_candidate_page_relationship`: `exact_table_page`, `adjacent_to_table`, `points_to_later_table`, `wrong_page`, `no_candidate_page`, `unknown`
- `human_visual_table_type`: `step_grade`, `rank_step`, `classification_pay_table`, `hourly_schedule`, `annual_salary_schedule`, `compact_compensation_sheet`, `percent_increase_only`, `prose_only`, `benefits_table`, `budget_or_fiscal_table`, `classification_without_pay`, `index_or_contents`, `front_matter`, `non_wage_table`, `no_table`, `other`, `unknown`
- `human_non_wage_family`: `not_applicable`, `benefits`, `budget_or_fiscal`, `classification_without_pay`, `incentive_or_bonus_prose`, `index_or_contents`, `front_matter`, `non_wage_appendix`, `memorandum_without_table`, `other`, `unknown`
- `human_navigation_needed`: `yes`, `no`, `unknown`
- `human_navigation_target_found`: `yes`, `no`, `not_applicable`, `unknown`
- `human_extraction_complexity`: `easy`, `moderate`, `hard`, `not_extractable`, `unknown`
- `human_extraction_recommendation`: `extraction_ready`, `extraction_ready_with_schema_update`, `second_review_required`, `exclude_for_now`, `unknown`
- `human_confidence`: `high`, `medium`, `low`, `unknown`

Reviewer names, timestamps, and notes are free text. Use ISO 8601 for
`human_reviewed_at`. Keep notes short and do not transcribe a complete table.
