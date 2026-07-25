# Gate 2 failure diagnosis from the Gate 1 ledger

Date: 2026-07-25
Gate 2 ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

This diagnosis reads Gate 1 and original-calibration fields only. No PDF was
opened and no GABRIEL call was made for this report. Categories below may
overlap unless described as exhaustive.

## Likely/p1 non-ready population

The original likely/p1 denominator is 80. Gate 1 made 27 ready and 53
non-ready: 40 `exclude_for_now` and 13 `second_review_required`.

### Likely/p1 exclusions

Among the 40 excluded likely/p1 cases:

- 38 have meaningful local wage language but GABRIEL identified prose,
  no-table, front matter, contents, benefit/budget/classification, or another
  non-positive table type;
- 21 are `no_candidate_page`;
- 7 are relationship `unknown`;
- 5 are `wrong_page`;
- 2 have an index/contents family or type;
- 20 have an explicit negative family;
- final visual types are 26 prose-only, 5 no-table, 3 benefits, 2
  classification-without-pay, and one each index/contents, non-wage table,
  front matter, and budget/fiscal.

Gate 1's compact score is not a valid compact-sheet discriminator: 38 of 40
excluded likely/p1 cases score at least 0.50, including obvious prose and
negative families. Gate 2 must replace this aggregate saturation with direct
role-to-pay-line, repeated-row, and aligned-numeric-column evidence.

Recommended changes:

| Diagnostic group | Gate 2 rule or packet change |
|---|---|
| Wage language but no table | Add `candidate_is_prose_only`; require repeated role/pay rows or aligned pay columns before any ready label. |
| No candidate page | Add `no_candidate_detected`; use actual candidate±1 pages before fallback navigation and distinguish a missing plausible target from a materially unrelated supplied page. |
| Index/contents | Add `candidate_is_index_or_contents`; reserve bounded capacity for a referenced target and keep pointer-only packets out of high confidence. |
| Possible compact sheet | Replace aggregate compact scoring with direct compact role/pay-line evidence; add `compact_compensation_candidate` only when role/classification and pay-band/rate structure coexist. |
| Benefits/budget/classification/front matter/non-wage | Add family-specific deterministic codes and preserve categorical high-confidence exclusions. |

## Second-review cases

All 19 Gate 1 second-review rows contain `EVIDENCE_NOT_STRONG_ENOUGH`.
Additional final-rule codes are:

- `NEGATIVE_PAGE_FAMILY`: 7;
- `LOCAL_STRUCTURE_WEAK`: 4;
- `NAVIGATION_TARGET_UNRESOLVED`: 2.

Their GABRIEL relationships are 13 exact, 4 adjacent, and 2
points-to-later-table. Their visual types are 6 step/grade, 4 classification
pay, 4 hourly schedule, 3 prose-only, 1 annual schedule, and 1 compact
compensation sheet.

Recommended changes:

- For the 13 exact cases, make role/pay-row and aligned-column counts visible
  in the prompt and final rule instead of relying on aggregate geometry.
- For the 4 adjacent cases, prioritize candidate±1 pages and record whether
  the positive structure is on the candidate or an adjacent page.
- For the 2 later-table cases, reserve target capacity, detect printed/PDF page
  offsets from in-budget pages, and emit `target_table_outside_budget` when the
  referenced target cannot be included.
- Keep ambiguous positive types in second review unless local structure and a
  schema-valid GABRIEL judgment agree.

## No-candidate relationships

Gate 1 has 71 `no_candidate_page` cases:

| Source type | Count |
|---|---:|
| CBA | 47 |
| Memorandum/settlement | 9 |
| Wage schedule/compensation plan | 6 |
| Arbitration award | 5 |
| Ordinance/policy | 4 |

Unit types are 30 police, 18 fire, and 23 non-safety. Original signals are 21
likely, 38 possible, and 12 unlikely. Fifty-three rows have supplied candidate
pages; 18 do not.

Recommended change: treat `no_candidate_page` as an evidence conclusion, not
as a synonym for absent input. Gate 2 should inspect bounded candidate±1 pages
and navigation pages, then emit `no_candidate_detected` only when none shows a
plausible role/pay target. A supplied page that is clearly benefits, budget,
front matter, or unrelated becomes `wrong_page` only when it is materially
unrelated; wage prose without a table remains no-candidate/prose rather than
wrong by default.

## Unknown relationships

Ten Gate 1 cases are relationship `unknown`; all are excluded. Their source
types are 4 CBA, 2 ordinance/policy, 2 wage schedule/compensation plan, 1
factfinding, and 1 memorandum/settlement. Their visual types are 7 prose-only,
2 no-table, and 1 non-wage table.

Recommended change: deterministic local diagnostics should resolve these to
prose/no-candidate, a named negative family, or an actual bounded table
relationship. GABRIEL must not infer a schedule outside the packet.

## Candidate-selection design for Gate 2

Gate 2 retains six pages total. It should:

1. select candidate pages and generated candidate±1 neighbors explicitly;
2. preserve room for contents/index or appendix targets;
3. detect a printed page number and PDF-minus-printed offset only on pages
   already selected;
4. try the direct and safely offset target within the remaining page budget;
5. record unresolved references rather than scanning the PDF;
6. compute direct role/pay-row, repeated numeric-row, aligned-column, compact,
   and negative-family diagnostics;
7. let GABRIEL interpret those bounded facts while deterministic final rules
   continue to veto non-wage families and weak role/pay structure.

This refinement can improve page recall without increasing the packet size or
weakening the extraction authorization gate.
