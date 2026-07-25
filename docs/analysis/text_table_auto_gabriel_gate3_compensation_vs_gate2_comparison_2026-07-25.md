# Gate 3 compensation evidence versus Gate 2

Gate 3: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`
Gate 2: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

## Material change

Gate 2 asked a narrow question: whether bounded pages established an
extractable wage schedule. Gate 3 asks which compensation-evidence use the same
bounded pages support. Gate 3 also supplied the existing rendered page images
to GABRIEL, while preserving the same 150 identities, six-page/four-navigation-
page budget, 1,500-character page cap, and 6,000-character case cap.

Gate 2 had 22 ready, 23 second-review, and 105 excluded rows. Gate 3 has 108
high/medium-confidence ready rows under its category/recommendation rule, no
second-review rows, one reference-only row, 31 non-wage-compensation rows, and
seven not-compensation-relevant rows.

## Gate 2 non-ready rows

Of the 105 Gate 2 `exclude_for_now` rows, Gate 3 classified 52 as
`mixed_quant_qual_ready`, 12 as `qual_mechanism_ready`, three as
`quant_table_ready`, 30 as `non_wage_compensation`, seven as
`not_compensation_relevant`, and one as `reference_navigation_only`. Sixty-four
meet the Gate 3 high/medium-confidence ready rule.

Of the 105 Gate 2 `no_candidate_page` rows, Gate 3 classified 54 as mixed, 11
as qualitative-mechanism, three as quantitative-table, 29 as non-wage
compensation, seven as irrelevant, and one as reference-only. Sixty-five meet
the Gate 3 ready rule. This change reflects a different evidence question and
actual rendered-image input; it is not a retroactive correction of the Gate 2
wage-table label.

Of the 23 Gate 2 `second_review_required` rows, 16 became mixed and six became
quantitative-table evidence; one became non-wage compensation. Twenty-two meet
the Gate 3 ready rule.

No Gate 2 excluded or no-candidate row received the best-use category
`quant_prose_ready`. Specific-rate or raise prose was generally classified as
mixed evidence when it also carried mechanism/implementation content: Gate 3's
quantitative subtype labels include 34 `prose_specific_rate` and 14
`prose_percentage_raise` cases.

## Gate 2 ready rows

All 22 Gate 2 ready rows remain ready under Gate 3: 16 are mixed, five are
quantitative tables, and one is a compact quantitative sheet. Gate 3 therefore
adds useful evidence without discarding Gate 2's precision-positive set.

## Evidence recovered

- Quantitative-support cases: 95, defined as a quantitative or mixed category
  with quantitative evidence present `yes`.
- Qualitative-mechanism-support cases: 92, defined as a qualitative or mixed
  category with qualitative evidence present `yes`.
- Mixed-category cases: 84.
- Reference-only cases: one.
- Gate 3 high/medium-confidence ready cases under the encoded decision rule:
  108.

Gate 3 ready representation is 36 police, 32 fire, and 40 non-safety cases,
compared with Gate 2's 5 police, 7 fire, and 10 non-safety cases. Ready source
families expand from three to six: 48 CBAs, 26 wage plans, 14 ordinances, 13
memoranda/settlements, six arbitration awards, and one factfinding source.

## Cost and boundedness

Both gates evaluated 769 local pages and supplied 632,553 bounded text
characters. Gate 2 used 682 rendered pages only for local derived features and
completed in 452.075 seconds. Gate 3 attached 682 existing rendered images
(93,613,400 bytes across requests) to GABRIEL. The primary image pass was
materially slower; it produced 145 strict-valid responses and five responses
with duplicate controlled array values. A bounded five-case retry after local
deduplication completed in 27.837 seconds and yielded the final 150/150 valid
ledger. Raw prompts, raw responses, images encoded for requests, full text,
and full tables were not saved.

## Interpretation

Broadening beyond wage tables recovered substantial project-useful evidence,
especially implementation rules, percentage changes, exact-rate prose, and
compensation-setting mechanisms. It also preserved a separate 31-row
non-base-wage category rather than calling those pages either wage-ready or
useless. The result supports a combined compensation-evidence extraction
design; it does not authorize treating every ready row as a classic wage table.
