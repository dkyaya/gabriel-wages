# Remaining readable parse-text QA report

Status: `not_run_live_incomplete_schema_invalid`.

The live checkpoint contains 825 of 826 frozen new cases. Cumulative materialization is an all-or-nothing operation, so duplicate-ID, bounded-page-pointer, quantitative-conflict, base/non-base-contamination, and matched-representation QA were not computed for a partial cohort.

The sole unresolved case is `cexrem_4a267735daf6729f5c4e4835`. Its ten responses were rejected because education/certification compensation appeared in the base quantitative array. No response was coerced or fabricated.

The following required complete-run artifacts were deliberately not produced:

- five `lanes_new` extraction ledgers;
- five cumulative readable parse-text ledgers;
- `remaining_parse_text_conflict_review.csv`;
- cumulative observation, conflict, contamination, duplicate, or page-pointer counts.

The corrected 1,000-document targeted-QA shadow ledgers remain the latest complete valid provisional extraction layer. The 825-case checkpoint is resumable intermediate state only and is not analysis-ready.
