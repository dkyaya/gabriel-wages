# Navigation and table-rule refinement plan

Date: 2026-07-24

## Objective

Use independent human adjudication to replace text-positive shortcuts with
visible page evidence, while keeping navigation tightly bounded and preserving
the failed REVIEW2 extraction prohibition.

## Proposed rule set

1. **Visible row/column confirmation is decisive.** A normal schedule needs
   role/classification/rank rows plus wage/rate/salary columns on the same
   visually checked page.
2. **Compact sheets are separate.** A stable role-or-component-to-pay list may
   be `compact_compensation_sheet` and schema-update ready; it must not be
   forced into the conventional grid rule.
3. **Language-only evidence is negative.** Wage-increase, incentive, bonus,
   and salary prose without a usable schedule is `prose_only` or
   `percent_increase_only`.
4. **Negative table families are explicit.** Benefits, fiscal/budget,
   classification-without-pay, and other non-wage tables cannot satisfy the
   wage schedule rule.
5. **Page relationship follows the evidence.** Candidate, adjacent, later
   target, wrong page, and no candidate are mutually exclusive terminal
   judgments.
6. **Navigation is fail-closed.** Contents/index/appendix pages are pointers,
   never table confirmations. A later target counts only when its page is
   named and visually checked inside the four-page navigation budget.
7. **Unreached targets go to second review.** A promising title outside the
   bounded packet is not presumed positive and is not an extraction-ready row.
8. **Authorization remains aggregate.** Human results must meet the 80%
   strict likely/p1 confirmation threshold, the 15% wrong-page ceiling, scale
   sufficiency, and systematic-error-family closure before any extraction.

## How adjudication will refine the rules

After the human CSV is completed, cross-tab table type, negative family,
candidate-page relationship, complexity, recommendation, and confidence by
the original signal/priority in a separate analysis step. REVIEW1/REVIEW2
labels may be unblinded only after the independent human file is frozen.
Disagreement review should identify rule changes, not overwrite the human
record.

No rule in this plan authorizes wage extraction.
