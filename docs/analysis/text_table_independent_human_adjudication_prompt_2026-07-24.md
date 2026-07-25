# Future prompt: independent human text/table adjudication

This instruction is prepared for a future human review. Do not execute it as
part of packet preparation.

## Assignment

Open:

`docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/independent_adjudication_blinded_review_input.csv`

Read the packet instructions and independent rubric. Review all 150 cases
without opening or consulting REVIEW1 or REVIEW2 outputs or labels.

For each case:

1. inspect only `blinded_candidate_pages`, `blinded_nearby_pages`, and
   `blinded_navigation_pages`;
2. use the corresponding bounded rendered images when available;
3. determine whether a conventional wage/salary schedule or separate compact
   compensation sheet is visually present;
4. label the candidate-page relationship, visual table type, non-wage family,
   navigation need/result, extraction complexity, recommendation, and
   confidence;
5. enter reviewer name, ISO timestamp, terminal review status, and a short
   diagnostic note.

Wage/pay language alone is not a table. Confirm a conventional schedule only
when role/classification/rank rows and wage/rate/salary columns are visible.
Contents/index pages count only as bounded pointers, never exact tables.

Do not browse URLs, run OCR, transcribe complete tables, or extract final wage
values. Do not inspect pages outside the listed budget. If the bounded pages
cannot settle a named navigation target, select `second_review_required`.

Save the completed file in the same packet directory as:

`independent_adjudication_human_reviewed.csv`

Do not overwrite the original blinded input.
