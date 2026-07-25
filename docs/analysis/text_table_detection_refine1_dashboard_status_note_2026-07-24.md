# Text/Table Detection Refine 1 Dashboard Status

The calibration dashboard now reports
`refinement_prepared_after_failed_review` for refinement
`TEXT-TABLE-DETECTION-REFINE1-VISUAL-TABLE-GATE-2026-07-24`.

The status preserves REVIEW1 as a failed, Codex-assisted diagnostic review.
It does not replace or re-label its 150 rows. The dashboard records:

- prior review:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`;
- prior extraction gate: `fail`;
- next recommendation: `refined_re_review_before_extraction`;
- refined REVIEW2 status: not started;
- wage extraction, ingestion, codification, and wage-gap analysis: not
  started.

The concise calibration card explains that the refined framework separates
wage prose, pay-number language, actual table structure, non-wage table
families, and index/appendix navigation. It also states that the earlier
five-row rendered challenge disagreed in all five cases and that the
500-document extraction run remains prohibited.

This status refresh does not imply that REVIEW2 ran, that visual table
precision was established, or that wage values were extracted. No URL,
download, OCR, ingestion, or codification action occurred.
