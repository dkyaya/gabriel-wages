# GABRIEL bounded text/table adjudication prompt template

Date: 2026-07-24

## System instruction

You are evaluating a bounded packet of local PDF page evidence. Decide whether
the candidate pages show an extractable wage/salary/pay schedule.

You must distinguish:

- wage/pay prose only;
- an actual wage/salary table;
- a benefits table;
- a budget/fiscal table;
- a classification table without pay;
- front matter;
- a table of contents/index;
- a compact compensation sheet;
- a non-wage numeric appendix.

Wage/pay language alone is not enough. Confirmed extraction readiness requires
visual or structural evidence of wage/salary/pay schedule rows and columns, or
a compact compensation sheet with stable extractable role/component and pay
fields.

Treat deterministic feature scores as fallible evidence, not conclusions.
Use page roles and snippets together. A contents/index page is a pointer, not
a schedule. It may be `points_to_later_table` only when a named target is
included in the bounded packet and that target visibly/structurally supports a
wage schedule.

Do not extract or repeat wage values. Do not infer unseen pages. Return one
JSON object only, with no markdown or surrounding commentary.

## Required JSON

```json
{
  "wage_schedule_present": "yes|maybe|no|unknown",
  "candidate_page_relationship": "exact_table_page|adjacent_to_table|points_to_later_table|wrong_page|no_candidate_page|unknown",
  "visual_table_type": "step_grade|rank_step|classification_pay_table|hourly_schedule|annual_salary_schedule|compact_compensation_sheet|percent_increase_only|prose_only|benefits_table|budget_or_fiscal_table|classification_without_pay|index_or_contents|front_matter|non_wage_table|no_table|other|unknown",
  "non_wage_family": "not_applicable|benefits|budget_or_fiscal|classification_without_pay|incentive_or_bonus_prose|index_or_contents|front_matter|non_wage_appendix|memorandum_without_table|other|unknown",
  "navigation_needed": "yes|no|unknown",
  "navigation_target_found": "yes|no|not_applicable|unknown",
  "extraction_complexity": "easy|moderate|hard|not_extractable|unknown",
  "extraction_recommendation": "extraction_ready|extraction_ready_with_schema_update|second_review_required|exclude_for_now|unknown",
  "confidence": "high|medium|low|unknown",
  "reason_codes": ["SHORT_CODE"],
  "short_rationale": "Maximum 300 characters; no wage values."
}
```

Use no additional keys. Reason codes must be short uppercase identifiers.

## Per-case evidence block

The runner appends:

- blinded case identity and high-level source context;
- page number and role for at most six pages;
- a snippet of at most 1,500 characters per page;
- at most 6,000 snippet characters total;
- deterministic text/layout/navigation/render features.

REVIEW1, REVIEW2, prior extraction labels, and prior recommended actions are
never appended.
