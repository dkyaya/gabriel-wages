# Gate 2 bounded GABRIEL adjudication prompt template

Date: 2026-07-25
Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

## Instruction

You are evaluating a bounded packet of local PDF page evidence. Decide whether
the included pages show an extractable wage/salary/pay schedule. Judge only the
included evidence and never infer that a table exists on an unseen page.

Wage/pay language is not enough. A positive schedule requires structured
role, classification, rank, grade, or position evidence together with pay
bands, rates, salary columns, or repeated role-to-pay lines.

Use these relationship definitions:

- `exact_table_page`: a supplied candidate page itself contains the supported
  schedule;
- `adjacent_to_table`: an included candidate neighbor contains it;
- `points_to_later_table`: an included contents/index/appendix page points to a
  target and the target is also included with supporting table evidence;
- `wrong_page`: a supplied candidate exists but is materially unrelated or is
  a distinct non-wage family;
- `no_candidate_page`: the bounded packet lacks any plausible table target;
- `unknown`: evidence is genuinely insufficient to choose another value.

A contents/index page is a pointer, never a wage table by itself. If its target
is outside the packet, do not infer the target; use a non-ready recommendation.
Printed-page/PDF-page offsets are diagnostics only and are trustworthy only
when derived from included header/footer evidence.

A compact compensation sheet may be extractable when it contains a stable
structured mapping between roles/classifications and pay bands, rates, or
salaries. Compact formatting does not excuse missing role/pay structure.

Benefits, budget/fiscal, classification-without-pay, front matter, prose-only,
and non-wage numeric tables are never high-confidence wage schedules.

Do not extract or repeat wage values. Return one JSON object only, with no
markdown or additional keys.

## Strict JSON fields

The allowed fields and values remain the Gate 1 strict schema:

- `wage_schedule_present`: `yes`, `maybe`, `no`, `unknown`
- `candidate_page_relationship`: `exact_table_page`, `adjacent_to_table`,
  `points_to_later_table`, `wrong_page`, `no_candidate_page`, `unknown`
- `visual_table_type`: the documented schedule, compact, prose, negative-table,
  no-table, other, or unknown vocabulary
- `non_wage_family`: the documented negative-family vocabulary
- `navigation_needed`: `yes`, `no`, `unknown`
- `navigation_target_found`: `yes`, `no`, `not_applicable`, `unknown`
- `extraction_complexity`: `easy`, `moderate`, `hard`, `not_extractable`,
  `unknown`
- `extraction_recommendation`: `extraction_ready`,
  `extraction_ready_with_schema_update`, `second_review_required`,
  `exclude_for_now`, `unknown`
- `confidence`: `high`, `medium`, `low`, `unknown`
- `reason_codes`: one to eight short uppercase codes
- `short_rationale`: at most 300 characters and no wage values

Gate 2 supplies deterministic lowercase diagnostic codes alongside page
features. Relevant codes are:

- `no_candidate_detected`
- `candidate_is_prose_only`
- `candidate_is_index_or_contents`
- `target_table_outside_budget`
- `possible_printed_page_offset`
- `compact_compensation_candidate`
- `non_wage_numeric_table`
- `benefits_table`
- `budget_table`
- `classification_without_pay`
- `true_wage_table_evidence`
- `insufficient_role_pay_columns`

Treat these as transparent local diagnostics, not answer labels. The primary
prompt never contains REVIEW1, REVIEW2, or Gate 1 judgments or recommended
actions.

## Packet limits

- at most six pages;
- at most four navigation pages;
- at most 1,500 redacted text characters per page;
- at most 6,000 redacted text characters per case;
- no whole PDF, full page text, complete table, raw prior label, or wage-value
  output.
