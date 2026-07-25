# Refined REVIEW2 independent rendered-page QA

Date: 2026-07-24
Review: `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`

## Method

This was a Codex-assisted rendered-page challenge, not human manual review.
Eighteen rows were selected deterministically from the 150-row packet before
their REVIEW2 refined labels were consulted:

- six original `likely` / p1 rows;
- six original `possible` rows spanning p2 and p3;
- six original `unlikely` rows spanning p2 and p3.

The challenge used only the rendered pages already permitted by the bounded
review design. Contact sheets displayed identity metadata and original
signal/priority, but not the REVIEW2 adjudication labels. Each row was first
assigned an independent table-structure, wage-schedule-confirmation,
candidate-page-relationship, and extraction-gate judgment. Only then were
those judgments compared with REVIEW2. Temporary contact sheets and rendered
images were deleted after this audit and are not retained or relayed.

Primary agreement requires both sides to agree on the material binary
decision: whether a wage schedule is visually supported and whether the row
is extraction-authorizable. Exact extraction-gate agreement is also reported
separately.

## Challenge composition

| Original signal | Rows |
|---|---:|
| likely | 6 |
| possible | 6 |
| unlikely | 6 |

| Extraction priority | Rows |
|---|---:|
| p1 | 6 |
| p2 | 7 |
| p3 | 5 |

## Results

- Primary material agreement: **10/18 (55.56%)**
- Primary material disagreement: **8/18 (44.44%)**
- Exact extraction-gate agreement: **8/18 (44.44%)**
- Required agreement for 500-document authorization: **at least 80%**
- Authorization challenge result: **fail**

The six original likely/p1 challenge rows were especially informative. Only
one visibly showed a repeated pay-range table. Five showed wage-increase
prose, budget material, front/memorandum material, or exhibit/navigation
material that REVIEW2 had nevertheless labeled as confirmed exact tables.

The possible group also exposed both error directions:

- wage prose and incentive prose were still promoted to table-positive
  outcomes;
- a compact one-page compensation sheet with visibly aligned salary and
  additional-pay rows was rejected as a non-wage table.

The unlikely group was usually kept out of extraction, but several contents
pages pointed to later compensation/wage sections and therefore need
navigation-aware second review rather than a simple negative label.

## Row-level audit

The bounded row-level labels are stored in:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24/calibration_visual_qa_assessments.csv`

No page images, full page text, complete table, or wage-value dataset is
retained. The assessment file contains only labels and short diagnostic
notes.

## Interpretation

The refined gate is more diagnostic than REVIEW1, but it is not independent
enough for extraction authorization. It still confuses wage prose and
aggregate budget/benefit material with actual schedule structure, and its
bounded navigation logic can stop before the table named by a contents or
appendix page. The 55.56% material agreement rate is far below the 80% gate.

No 500-document or smaller extraction run is authorized from this result.
The next step is independent human adjudication and narrower navigation/table
rules, followed by another blinded rendered-page challenge.
