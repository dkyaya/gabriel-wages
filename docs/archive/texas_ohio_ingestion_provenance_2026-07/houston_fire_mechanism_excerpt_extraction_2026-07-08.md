# Houston Fire Mechanism Excerpt Extraction — 2026-07-08

Source-text audit only, for `tx_houston_fire_2024`, drawn from all three fetched documents (Arbitration Opinion and Award, primary; Settlement Agreement and Release and MOU, companions). Short verbatim excerpts, no inference of mechanism strength or effect. See the companion CSV for the full excerpt table.

## Summary by mechanism

- **peer_comparator_wage_comparability** — not_found. The only "compar-" matches concern comparing FY26 Special/Incentive Pay costs to "Fiscal Year 2024 actual amounts paid" (a same-city budget baseline), not peer-city wage comparability.
- **arbitration_impasse_backstop** — present. The Award quotes CBA Article 14's grievance-arbitration clause at length: the arbitrator's decision "shall be final and binding," but the arbitrator's authority "shall be limited to the interpretation and application of the terms of this Agreement" with no authority "to establish provisions of a new agreement." **This is grievance/contract-interpretation arbitration, not Sec.174.1535 compulsory interest arbitration** — the schema's `interest_arbitration_flag` will not be set on this row.
- **staffing_recruitment_retention** — not_found.
- **overtime_callback_minimum_staffing** — present. The MOU quotes CBA Article 22 Section 5 holiday-overtime premium rates (time-and-a-half / double-time for call-in or held-over overtime on recognized/premium holidays). No explicit minimum-staffing-level language found.
- **classification_reclassification_wage_schedule** — present. The Award quotes CBA Article 17 Section 2's full fiscal-year base-salary schedule (10% FY25; 3%+escalator FY26-27; 4%+escalator FY28-29) and Article 2's Bargaining Unit definition and Article 6's civil-service precedence clause.
- **training_certification_education** — present. The MOU ties EMT Suppression/Administration Assignment Pay (CBA Article 17 Section 9) to holding "a current valid State of Texas EMT certification." The Award's Article 2 quote also defines bargaining-unit membership partly by Val Jahnke Training Academy graduation.
- **premium_pay_differentials** — present. The Settlement sets specific uniform-allowance dollar credits ($300/$300/$800 across FY25-FY29) tied to CBA Article 27 Section 2a.
- **subcontracting_outsourcing** — not_found.
- **total_compensation_benefits** — present. The Settlement allocates $1.5M/year for Holiday Buy Back (reallocating a $250K laundry-service fund) and permits sick-reserve balances to fund Deferred Cash Out/Rollover Election options; the MOU caps aggregate Special/Incentive Pay growth at $10M/year, "exclusive of FICA and pension contributions."
- **safety_risk_public_safety** — present. Article 17 Section 2's escalator footnote ties the raise to the City and Association jointly securing "additional new revenues to the City for public safety"; the Award's own findings (not a CBA clause) further reason that new ambulance-service revenue "pays for public safety."
- **other** — present. The Award quotes CBA Article 25's "Joint Labor-Management Committee" (JLMC) as a cooperative workforce-development partnership — named similarly to, but functionally distinct from, Massachusetts's compulsory-interest-arbitration JLMC. Filed under "other" specifically to avoid conflating the two.

No GABRIEL, Harvard Proxy, or model/API scoring was applied to characterize these excerpts — flags/strength judgments are left to the toolkit's later measurement pass, per the project's capture-verbatim-never-pre-code rule.
