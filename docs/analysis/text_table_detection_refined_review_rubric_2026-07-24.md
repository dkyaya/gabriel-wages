# Refined Text/Table Calibration Review Rubric

## Core rule

Review in two independent stages:

1. identify wage/pay language;
2. identify actual table or schedule structure.

Never infer stage 2 from stage 1. Wage prose, a memorandum describing a raise,
or a clause containing multiple amounts may be relevant but is not a wage
table.

## Page classification sequence

### 1. Front matter and navigation pages

Classify a page as `front_matter` when it is primarily a cover, title page,
signature page, transmittal memorandum, synopsis, or recommendation page and
lacks repeated wage rows/columns.

Classify as `index_or_contents` when the page lists document sections/pages.
If a bounded line references a salary table, wage schedule, pay plan, rate
schedule, or compensation appendix and includes a page number:

- record `candidate_page_relationship_label=points_to_later_table`;
- record `table_navigation_signal=index_or_contents` or
  `appendix_reference`;
- schedule only the referenced page and bounded neighbors within the
  navigation budget;
- do not call the contents page a table.

### 2. Wage and pay-number language

Record wage language separately. A page may be:

- wage language `yes`, pay-numeric language `yes`, but `prose_only`;
- wage language `yes`, pay-numeric language `no`, and `prose_only`;
- wage language `no` but a `benefits_table` or `non_wage_table`.

Amounts tied only to insurance premiums, pensions, allowances, leave,
reimbursements, or benefit contributions do not establish a wage schedule.

### 3. Structural table evidence

`confirmed_table` requires strong bounded evidence such as:

- at least two repeated data rows with comparable column counts;
- stable row labels plus repeated step/grade/rank/classification columns;
- repeated hourly/annual/rate cells aligned across employees, ranks,
  classifications, or effective dates;
- explicit local parser table geometry or strong row/column alignment;
- a rendered page that is available for independent visual checking when
  visual confirmation is required.

`possible_table` may be used for one strong row plus a clear header, a partial
text layer, a continuation page, or a table whose geometry is degraded.

Do not assign `step_grade`, `rank_step`, `hourly_schedule`, or
`annual_salary_schedule` unless table structure is confirmed or possible with
strong evidence. Headings or prose mentioning those terms are insufficient.

### 4. Negative table families

- `benefits_table`: structured insurance, pension, premium, leave, or
  contribution data without wage/salary/rate rows.
- `classification_only`: titles/classes/ranks without pay or rate columns.
- `non_wage_table`: other structured numeric schedules not tied to wages.
- `prose_only`: sentences or clauses, even when they contain wage terms and
  multiple numeric amounts.

### 5. Page relationship

- `exact_table_page`: an original candidate page contains the table.
- `adjacent_to_table`: a bounded neighbor contains it.
- `points_to_later_table`: a contents/index/appendix reference identifies a
  later table outside the direct candidate page.
- `wrong_page`: the candidate page has no qualifying table and no bounded
  navigation relation.
- `no_candidate_page`: the original detector supplied no page.
- `unknown`: evidence unavailable or parser/render failure.

## Gate decisions

### `pass_high_confidence`

Require all of:

- wage language `yes`;
- pay-numeric language `yes`;
- `confirmed_table`;
- wage schedule confirmed `yes`;
- exact or bounded-navigation-confirmed page relationship;
- no dominant benefits/non-wage classification;
- configured render/visual check completed when required;
- artifact integrity and page bounds passed.

### `pass_with_schema_update`

Use for a real wage table that is partial, continued, rotated, multi-header,
or structurally difficult but still bounded and reviewable.

### `second_review_required`

Use for:

- wage/pay prose without a confirmed table;
- contents/index pages that point to a later table not yet confirmed;
- `possible_table`;
- partial text, hard geometry, render unavailability, or disagreement between
  text and structure;
- uncertain benefit/classification boundaries.

### `fail_exclude`

Use for confirmed benefits/non-wage tables, classification-only pages without
pay, front matter without a useful navigation reference, or documents with no
wage-table evidence after bounded review.

## Later calibration pass criteria

A future re-review may authorize a 500-document extraction only when all of
the following are documented:

- likely-signal visual wage-table confirmation rate at least 80%;
- wrong-page rate at most 15%;
- hard/not-extractable share characterized and operationally acceptable;
- enough p1 `pass_high_confidence` rows to support a representative
  500-document selection;
- random rendered-page QA agreement at least 80%;
- independent review method documented;
- wage prose, benefits tables, classifications, front matter, and navigation
  pages audited as separate false-positive families.

Failure of any gate keeps the 500-document prompt blocked. A smaller
extraction pilot may be considered only after a separately approved,
independently calibrated result.
