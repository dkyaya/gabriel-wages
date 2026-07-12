# National Corpus Current Coverage and Gap Audit - 2026-07-12

## Scope

This audit describes current corpus and evidence coverage before national expansion. It does not add sources, run codify, or prepare a report.

## Coverage by State

- **MA:** 32 contracts; 338 evidence-layer rows; 16 codified sources.
- **OH:** 13 contracts; 270 evidence-layer rows; 13 codified sources.
- **TX:** 8 contracts; 173 evidence-layer rows; 8 codified sources.

**Assessment:** Massachusetts supplies dense local cross-occupation coverage, Ohio supplies the cleanest matched-triad design, and Texas supplies institutional unevenness plus important public-safety-only gaps. No other states are currently in `data/contracts.csv`.

## Coverage by City and Matched-Triad Status

- **Arlington, MA:** 2 occupation classes (fire, public_works); status `safety_non_safety_partial`.
- **Boston, MA:** 2 occupation classes (clerical_admin, police); status `safety_non_safety_partial`.
- **Franklin, MA:** 5 occupation classes (fire, library, other, police, public_works); status `police_fire_non_safety_triad`.
- **Georgetown, MA:** 2 occupation classes (other, police); status `safety_non_safety_partial`.
- **Newton, MA:** 1 occupation classes (police); status `safety_only`.
- **Seekonk, MA:** 6 occupation classes (clerical_admin, fire, library, police, public_works, teacher); status `police_fire_non_safety_triad`.
- **Somerville, MA:** 1 occupation classes (police); status `safety_only`.
- **Wayland, MA:** 5 occupation classes (fire, library, other, police, public_works); status `police_fire_non_safety_triad`.
- **Worcester, MA:** 3 occupation classes (clerical_admin, fire, public_works); status `safety_non_safety_partial`.
- **Cincinnati, OH:** 3 occupation classes (fire, other, police); status `police_fire_non_safety_triad`.
- **Cleveland, OH:** 3 occupation classes (fire, other, police); status `police_fire_non_safety_triad`.
- **Columbus, OH:** 3 occupation classes (fire, other, police); status `police_fire_non_safety_triad`.
- **Toledo, OH:** 3 occupation classes (fire, other, police); status `police_fire_non_safety_triad`.
- **Austin, TX:** 3 occupation classes (fire, nurse_health, police); status `police_fire_non_safety_triad`.
- **Houston, TX:** 3 occupation classes (fire, other, police); status `police_fire_non_safety_triad`.
- **San Antonio, TX:** 2 occupation classes (fire, police); status `safety_only`.

**Matched-triad note:** Austin has police, fire, and `nurse_health`, but EMS/nurse_health is safety-adjacent rather than an ordinary general municipal non-safety comparator. Treat it as exploratory, not as the ideal triad design.

## Coverage by Occupation Class

- `police`: 17 contracts.
- `fire`: 13 contracts.
- `other`: 8 contracts.
- `public_works`: 7 contracts.
- `clerical_admin`: 3 contracts.
- `library`: 3 contracts.
- `teacher`: 1 contracts.
- `nurse_health`: 1 contracts.

**Occupation gap:** Police and fire dominate. Non-safety coverage exists, but it is concentrated in `other`, `public_works`, `clerical_admin`, `library`, `teacher`, and `nurse_health`; there are no current `sanitation`, `transit`, or `parks_rec` rows.

## Coverage by Safety Group

- Safety contracts: 30.
- Non-safety contracts: 23.
- Codified source inventory: Counter({'safety': 22, 'non_safety': 14, 'safety_adjacent': 1}).

**Gap:** The current design needs more matched non-safety units. Safety-only additions can be useful for impasse, arbitration, and comparator-source claims, but they should not dominate the next wave.

## Coverage by Source Type

- Current causal source types: {'cba': 49, 'arbitration_award': 4}.
- Codified inventory source types: {'cba': 34, 'arbitration_award': 3}.

**Gap:** The corpus is overwhelmingly CBA-based. There are only four arbitration-award rows and no factfinding rows in `data/contracts.csv`. Comparator and peer-wage evidence is likely under-detected without awards, factfinding reports, and wage studies.

## Coverage by Text Quality

- Current contract text quality: {'ocr_messy': 12, 'clean': 39, 'partial': 2}.
- Codified inventory text quality: {'clean': 33, 'ocr_messy': 4}.

**Implication:** Clean public PDFs should remain the first-choice source type for a large expansion wave. OCR-heavy sources can be useful but should not be the backbone of a two-week national push unless they serve a high-value claim.

## Verified-Present Attribute Coverage

- `overtime_callback_holdover_mandatory_extra_work`: 34 verified-present rows.
- `classification_reclassification_or_grade_structure`: 34 verified-present rows.
- `grievance_or_contract_interpretation_arbitration`: 29 verified-present rows.
- `benefits_total_compensation_or_pension`: 29 verified-present rows.
- `union_security_or_institutional_power`: 25 verified-present rows.
- `management_rights_or_service_flexibility`: 24 verified-present rows.
- `premium_pay_differentials`: 19 verified-present rows.
- `civil_service_or_statutory_employment_channel`: 18 verified-present rows.
- `training_certification_credential_premiums`: 15 verified-present rows.
- `no_strike_or_work_stoppage_constraint`: 10 verified-present rows.
- `interest_arbitration_or_formal_impasse_backstop`: 8 verified-present rows.
- `subcontracting_outsourcing_or_volunteer_substitution`: 8 verified-present rows.
- `hazard_risk_stress_or_line_of_duty_rationale`: 8 verified-present rows.
- `other`: 7 verified-present rows.
- `staffing_shortage_recruitment_retention`: 5 verified-present rows.
- `minimum_staffing_or_continuous_coverage`: 5 verified-present rows.
- `non_safety_wage_restraint_or_admin_channel`: 3 verified-present rows.
- `budget_capacity_or_fiscal_constraint`: 2 verified-present rows.
- `peer_comparator_wage_comparability`: 1 verified-present rows.

**Attribute gap:** `peer_comparator_wage_comparability` has only 1 verified-present row; `non_safety_wage_restraint_or_admin_channel`, `budget_capacity_or_fiscal_constraint`, staffing shortage, and minimum staffing remain thin. These should guide source-type selection.

## Strongest Current Evidence Areas

- Ohio matched triads under a shared labor-law framework (`CLM-2026-07-12-01`).
- The distinction between interest/formal impasse arbitration and grievance arbitration (`CLM-2026-07-12-06`).
- Texas institutional unevenness as a design/source-coverage finding (`CLM-2026-07-12-02`).
- Massachusetts cross-occupation mechanism development in Franklin and Seekonk (`CLM-2026-07-12-03`).

## Weakest Current Evidence Areas

- Peer/comparator wage evidence: one verified-present row and one documented San Antonio false negative (`CLM-2026-07-12-07`).
- Texas non-safety outside Houston: not report-ready (`CLM-2026-07-12-08`).
- Factfinding and impasse-source coverage beyond a handful of awards.
- Non-safety bargaining under specialized or weak public-sector bargaining regimes.

## Where Source Availability Appears Promising

Based on current repo planning, not a live scan, the most promising next states are those likely to offer public contracts and institutional contrast: Pennsylvania, New Jersey, Illinois, and New York. California, Washington, Oregon, Minnesota, Connecticut, Rhode Island, Maryland, and Colorado may be useful after a source-availability scan, but should not be assumed until public matched triads are verified.

## Where Non-Safety Comparisons Remain Thin

- Texas outside Houston is the clearest immediate gap.
- Safety-only cities such as San Antonio, Newton, and Somerville remain useful for institutional analysis but not for the core matched comparison unless non-safety rows are added.
- National expansion should treat non-safety source discovery as the bottleneck, not an afterthought once safety sources are found.

## Where Public-Safety-Only Sources May Still Be Useful

Safety-only arbitration awards, factfinding reports, and statutory impasse records can test hypotheses about conversion channels, comparator wage evidence, and formal backstops. They should be collected only when they serve a specific claim or hypothesis and should be clearly flagged as non-comparative until matched non-safety sources are found.

## Evidence Needed by Leading Hypothesis

1. **Safety pressure plus conversion channels:** more matched triads with safety overtime/callback/premium/minimum-staffing evidence and matched non-safety contrasts.
2. **Safety impasse/arbitration backstops:** police/fire CBAs plus awards/factfinding under states with formal safety bargaining channels, paired with non-safety contracts in the same cities.
3. **Non-safety classification/admin channel:** non-safety wage appendices, classification plans, and reclassification language across new states.
4. **Staffing/continuous coverage/premium centrality:** public safety CBAs with staffing, overtime, callback, and premium-pay sections; comparable non-safety windows to test contrast.
5. **Peer/comparator evidence:** arbitration awards, factfinding reports, wage studies, and full windows around appendices/attachments.
6. **Texas-style unevenness:** states with specialized safety bargaining and weaker non-safety pathways; collect matched and nonmatched cases deliberately.
7. **Ohio-style triads:** states with clean public police/fire/non-safety CBA availability under a shared framework.
8. **Massachusetts-style dense local comparison:** additional states with multiple occupations in the same city/town to test generalizability.

## Claim Relevance Summary

- `CLM-2026-07-12-01` (Ohio matched triads): status `supported_provisional`, strength `moderate`. Expansion need: Full-document or broader-window codify for Ohio non-safety rows; Ohio SERB impasse/arbitration materials for the same cities and cycles; repeat cycles in Columbus/Cleveland/Cincinnati/Toledo.
- `CLM-2026-07-12-02` (Texas institutional unevenness): status `supported_provisional`, strength `moderate`. Expansion need: More Texas non-safety sources if publicly available, especially San Antonio/Austin clerical, public works, or general municipal units; repeat Houston cycles.
- `CLM-2026-07-12-03` (Massachusetts cross-occupation base): status `supported_provisional`, strength `moderate`. Expansion need: Codify the remaining Massachusetts rows; add repeat cycles in Franklin/Seekonk; add matched non-safety rows for Somerville/Newton safety units where available.
- `CLM-2026-07-12-04` (Safety pressure conversion channels): status `supported_provisional`, strength `moderate`. Expansion need: Repeat cycles for current cities; additional matched triads in states with public CBAs; full-document coding of minimum-staffing and premium-pay sections.
- `CLM-2026-07-12-05` (Non-safety classification/admin channel): status `supported_provisional`, strength `moderate`. Expansion need: Broader non-safety windows with wage appendices; more Texas non-safety units; repeat cycles in Franklin/Seekonk/Wayland/Cleveland.
- `CLM-2026-07-12-06` (Arbitration distinction): status `supported_provisional`, strength `strong`. Expansion need: Additional impasse/arbitration awards or factfinding documents in Ohio and Massachusetts; reviewer audit of all interest-arbitration positives.
- `CLM-2026-07-12-07` (Comparator wage evidence gap): status `needs_more_evidence`, strength `low`. Expansion need: Interest-arbitration awards, factfinding reports, wage studies, and broader windows around appendices/attachments; codebook refinement/re-run for comparator language.
- `CLM-2026-07-12-08` (Texas non-safety outside Houston gap): status `needs_more_evidence`, strength `low`. Expansion need: Targeted public-source verification for Texas non-safety units if available; otherwise document institutional non-availability as a design limitation.
