# Refined Text/Table Detection and Calibration Schema

## Purpose

This schema separates wage language from actual table evidence. It is a
technical screening and calibration schema, not a wage-extraction schema.
No field below is an analysis-ready wage observation.

All upstream identity, provenance, artifact-integrity, candidate-page,
PDF-readiness, and original detector fields must be preserved unchanged.
Refined outputs use a new review ID and never overwrite REVIEW1.

## Refined fields

### `wage_language_present_label`

Whether bounded reviewed material contains wage/pay/salary/compensation
language.

- `yes`
- `maybe`
- `no`
- `unknown`

This field alone never authorizes extraction.

### `pay_numeric_language_present_label`

Whether bounded reviewed material connects pay/rate language to numeric,
currency, percentage, hourly, annual, step, grade, rank, or classification
language.

- `yes`
- `maybe`
- `no`
- `unknown`

Incidental money, benefit contributions, percentages, or isolated numbers are
not enough for `yes`.

### `visual_table_structure_label`

The strongest bounded structural/visual classification of the reviewed page.

- `confirmed_table`
- `possible_table`
- `prose_only`
- `index_or_contents`
- `benefits_table`
- `classification_only`
- `non_wage_table`
- `front_matter`
- `unknown`

`confirmed_table` requires repeated row/column structure or explicit detected
table geometry. Wage prose, headings, memoranda, covers, contents pages, and
isolated numeric clauses cannot receive this label.

### `wage_schedule_table_confirmed_label`

Whether actual table structure is joined to wage/salary/rate content.

- `yes`
- `maybe`
- `no`
- `unknown`

`yes` requires `visual_table_structure_label=confirmed_table` plus usable
wage/pay row-and-column evidence. `maybe` may accompany a
`possible_table`. Wage language without table structure is `no`.

### `candidate_page_relationship_label`

How the original detector page hint relates to the strongest bounded table
evidence.

- `exact_table_page`
- `adjacent_to_table`
- `points_to_later_table`
- `wrong_page`
- `no_candidate_page`
- `unknown`

`points_to_later_table` records a bounded contents/index/appendix reference;
it does not claim that the later table was manually validated unless the
referenced page was also checked.

### `table_navigation_signal`

How the refined workflow reached or scheduled the relevant page.

- `direct`
- `nearby`
- `index_or_contents`
- `appendix_reference`
- `none`
- `unknown`

Navigation is capped by a separate page budget and recorded explicitly.

### `visual_confirmation_method`

The evidence mode supporting the structural label.

- `rendered_page`
- `text_structure_plus_rendered_check`
- `text_structure_only`
- `human_manual`
- `unknown`

A successful raster render confirms that the page was rendered, not that a
human reviewed it. Only an actual human adjudicator may use `human_manual`.

### `extraction_gate_label`

The refined scheduling gate.

- `pass_high_confidence`
- `pass_with_schema_update`
- `second_review_required`
- `fail_exclude`
- `unknown`

`pass_high_confidence` requires a confirmed wage/salary table, usable
row/column structure, a correct page relationship, and the configured visual
confirmation requirement. A prose-only wage page is always
`second_review_required` or `fail_exclude`.

### `extraction_gate_reason`

Bounded free text, maximum 300 characters. It explains the decisive evidence
without storing full page text, a complete table, or structured wage values.

## Supporting audit fields

Refined runs also record:

- `refined_review_mode`
- `navigation_pages_requested`
- `navigation_pages_inspected`
- `navigation_references_found`
- `rendered_pages_review`
- `rendered_page_count`
- `render_failures`
- `table_row_like_line_count`
- `table_column_evidence_count`
- `benefit_term_count`
- `wage_term_count_refined`
- `pay_numeric_token_count`

These are bounded diagnostics, not extracted table cells.

## Extraction boundary

`wage_language_present_label=yes` is not sufficient for extraction.
Extraction requires a confirmed wage/salary table or schedule with usable
rows and columns, or a separately approved clearly parseable equivalent. A
future calibration must measure this distinction independently before any
500-document run is authorized.
