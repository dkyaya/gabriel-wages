# Final Report Number Cross-check

Result: **passed** (39 checks).

| Measure | Expected | Observed | Source | Result |
|---|---:|---:|---|---|
| scout-covered municipalities | 16887 | 16887 | dashboard coverage source | PASS |
| eligible municipality universe | 35589 | 35589 | national_municipality_universe.csv | PASS |
| national scout coverage rate | 47.45 | 47.45 | derived from coverage numerator/denominator | PASS |
| valid ratings | 18554 | 18554 | span_rating_summary.json | PASS |
| quarantines | 58 | 58 | span_rating_summary.json | PASS |
| careful claim candidates | 18 | 18 | rating_ingest_codify_summary.json | PASS |
| core finding ready | 472 | 472 | report_usability_summary.json | PASS |
| supporting examples | 528 | 528 | report_usability_summary.json | PASS |
| context only | 6860 | 6860 | report_usability_summary.json | PASS |
| downstream normalization needed | 5533 | 5533 | report_usability_summary.json | PASS |
| exclude from report | 5161 | 5161 | report_usability_summary.json | PASS |
| normalized quantitative records | 11548 | 11548 | normalization_summary.json | PASS |
| quantitatively supported growth records | 416 | 416 | normalization_rescue_gap_growth_summary.json | PASS |
| quantitative growth claims | 95 | 95 | normalization_rescue_gap_growth_summary.json | PASS |
| bounded candidates | 4 | 4 | bounded_wage_differential_validation_summary.json | PASS |
| PI-usable bounded candidates | 1 | 1 | bounded_wage_differential_validation_summary.json | PASS |
| conditional bounded candidates | 3 | 3 | bounded_wage_differential_validation_summary.json | PASS |
| rejected bounded candidates | 0 | 0 | bounded_wage_differential_validation_summary.json | PASS |
| non-base police | 1239 | 1239 | nonbase_compensation_side_audit.json | PASS |
| non-base fire | 280 | 280 | nonbase_compensation_side_audit.json | PASS |
| non-base combined_safety | 9 | 9 | nonbase_compensation_side_audit.json | PASS |
| non-base non_safety | 226 | 226 | nonbase_compensation_side_audit.json | PASS |
| non-base unclear | 1964 | 1964 | nonbase_compensation_side_audit.json | PASS |
| growth-claim police | 63 | 63 | growth_mechanism_side_audit.json | PASS |
| growth-claim fire | 15 | 15 | growth_mechanism_side_audit.json | PASS |
| growth-claim non_safety | 14 | 14 | growth_mechanism_side_audit.json | PASS |
| growth-claim unclear | 3 | 3 | growth_mechanism_side_audit.json | PASS |
| bargaining/strike safety | 714 | 714 | bargaining_dispute_pressure_audit.json | PASS |
| bargaining/strike non_safety | 292 | 292 | bargaining_dispute_pressure_audit.json | PASS |
| bargaining/strike mixed | 39 | 39 | bargaining_dispute_pressure_audit.json | PASS |
| bargaining/strike unclear | 671 | 671 | bargaining_dispute_pressure_audit.json | PASS |
| direct market/staffing safety | 33 | 33 | market_staffing_pressure_audit.json | PASS |
| direct market/staffing non_safety | 4 | 4 | market_staffing_pressure_audit.json | PASS |
| direct market/staffing unclear | 46 | 46 | market_staffing_pressure_audit.json | PASS |
| comparison tier position_schedule_comparable | 1 | 1 | comparison_readiness_tiers.json | PASS |
| comparison tier conditional_specific_blocker | 3 | 3 | comparison_readiness_tiers.json | PASS |
| comparison tier structurally_compatible_candidate_review | 27 | 27 | comparison_readiness_tiers.json | PASS |
| comparison tier moderate_manual_review | 87 | 87 | comparison_readiness_tiers.json | PASS |
| comparison tier not_ready | 189 | 189 | comparison_readiness_tiers.json | PASS |
