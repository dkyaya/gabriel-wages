# Report Evidence-Layer Audit — 2026-07-10

Audits `docs/analysis/gabriel_codify_evidence_layer.csv` for use in the report scaffold. **No rows are dropped from the underlying CSV** — this audit determines what the report's graphs and headline counts should filter to (verified present evidence only), while the full 781-row layer remains intact and available in the viewer.

## Total rows

**781.**

## Present / not_found

- `present`: **293**
- `not_found`: **488**

## Verified / unsupported / unclear / not_applicable

- `source_grounding_status=grounded`: **289**
- `source_grounding_status=unclear`: **4** (all 4 are among the 9 flagged/unverified rows below — excerpt-boundary-leakage cases from the Seekonk/Wayland batch)
- `source_grounding_status=not_applicable`: **488** (every `not_found` row; grounding is only meaningful for a returned excerpt)
- `source_grounding_status=unsupported`: **0**
- `viewer_verified=1` (the report's "verified present" figure — evidence found, confirmed grounded, no reviewer flag): **284**
- `viewer_verified=0` (present but flagged/unverified, or `not_found`): **497**, of which **9** are `present` rows specifically flagged by a human reviewer (see below) and **488** are ordinary `not_found` rows.

## Counts by state

| state | rows | present | verified present |
|---|---|---|---|
| MA | 338 | — | 92 |
| OH | 270 | — | 93 |
| TX | 173 | — | 86 |

(293 present total; 284 - 3 do not sum to state present counts exactly here because "present" and "verified present" are reported separately above and below — see the state-level breakdown in `report_assets/mechanism_presence_by_state_2026-07-10.csv` for exact per-attribute figures.)

## Counts by city

| city | rows |
|---|---|
| Franklin | 110 |
| Seekonk | 103 |
| Cincinnati | 76 |
| Austin | 67 |
| Cleveland | 67 |
| Columbus | 66 |
| Houston | 65 |
| Toledo | 61 |
| Georgetown | 41 |
| San Antonio | 41 |
| Wayland | 40 |
| Boston | 22 |
| Somerville | 22 |

## Counts by occupation_class

| occupation_class | rows |
|---|---|
| police | 247 |
| fire | 206 |
| other | 172 |
| public_works | 46 |
| library | 43 |
| nurse_health | 26 |
| clerical_admin | 22 |
| teacher | 19 |

No `sanitation`, `transit`, or `parks_rec` rows — none of this project's currently-codified contracts fall in those classes.

## Counts by source_role

| source_role | rows |
|---|---|
| non_safety_general | 328 |
| police | 168 |
| fire | 148 |
| safety | 137 |

Note: `source_role` values are inconsistent across codify batches (earlier batches used `police`/`fire`; the most recent expanded Texas/Ohio batch used `safety` for both police and fire rows). The report's tables use `occupation_class` (consistently `police`/`fire`/etc. across all batches) as the authoritative field for `safety_group` classification, not `source_role`.

## Counts by attribute (all rows, present + not_found)

| attribute | total rows | verified present |
|---|---|---|
| classification_reclassification_or_grade_structure | 51 | 34 |
| overtime_callback_holdover_mandatory_extra_work | 49 | 34 |
| benefits_total_compensation_or_pension | 49 | 29 |
| management_rights_or_service_flexibility | 45 | 24 |
| union_security_or_institutional_power | 44 | 25 |
| grievance_or_contract_interpretation_arbitration | 47 | 29 |
| training_certification_credential_premiums | 41 | 15 |
| civil_service_or_statutory_employment_channel | 41 | 18 |
| premium_pay_differentials | 40 | 19 |
| no_strike_or_work_stoppage_constraint | 39 | 10 |
| hazard_risk_stress_or_line_of_duty_rationale | 38 | 8 |
| other | 38 | 7 |
| budget_capacity_or_fiscal_constraint | 37 | 2 |
| interest_arbitration_or_formal_impasse_backstop | 37 | 8 |
| minimum_staffing_or_continuous_coverage | 37 | 5 |
| non_safety_wage_restraint_or_admin_channel | 37 | 3 |
| peer_comparator_wage_comparability | 37 | 1 |
| staffing_shortage_recruitment_retention | 37 | 5 |
| subcontracting_outsourcing_or_volunteer_substitution | 37 | 8 |

`peer_comparator_wage_comparability` is the rarest verified-present attribute in the whole layer (1 of 37 coded contracts) — this is a genuine, previously-documented finding (see `gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md`'s discussion of a likely false negative on San Antonio police), not a data gap; the report should not overstate comparator-wage-language prevalence.

## Flagged/unverified present rows (excluded from headline verified-present counts)

**9 rows**, all pre-existing from earlier codify batches (0 new from the most recent expanded Texas/Ohio batch):

| contract_id | attribute | grounding | flag reason |
|---|---|---|---|
| `oh_cleveland_fire_2025` | interest_arbitration_or_formal_impasse_backstop | grounded | window-assembly section-header leakage (Texas/Ohio scale-up run) |
| `ma_franklin_fire_2022` | training_certification_credential_premiums | grounded | excerpt contains project scaffolding vocabulary |
| `ma_franklin_public_works_2022` | premium_pay_differentials | grounded | excerpt contains project scaffolding vocabulary |
| `ma_franklin_library_2022` | benefits_total_compensation_or_pension | grounded | excerpt contains project scaffolding vocabulary |
| `ma_boston_clerical_admin_2023` | premium_pay_differentials | grounded | excerpt contains project scaffolding vocabulary |
| `ma_seekonk_public_works_2023` | overtime_callback_holdover_mandatory_extra_work | unclear | excerpt-boundary leakage, cleaned |
| `ma_seekonk_library_2023` | management_rights_or_service_flexibility | unclear | excerpt-boundary leakage, cleaned |
| `ma_seekonk_police_2022` | overtime_callback_holdover_mandatory_extra_work | unclear | excerpt-boundary leakage, cleaned |
| `ma_seekonk_teacher_2021` | no_strike_or_work_stoppage_constraint | unclear | excerpt-boundary leakage, cleaned |

These remain in the evidence layer (nothing deleted) and are visible in the viewer via its "Show unverified / unsupported evidence" toggle, but are excluded from every count/graph/table in this report scaffold unless a figure is explicitly labeled otherwise.

## Duplicate evidence_id check

**0 duplicates** across all 781 `evidence_id` values.

## Missing labels/definitions check

- Rows missing `attribute_label` or `attribute_definition`: **0**.
- Rows missing `state_label`: **0**.
- Rows missing `contract_label`: **0**.

## Rule applied for the rest of this report scaffold

**Unless a figure or table is explicitly labeled otherwise, "present" in this report means `evidence_status=present AND viewer_verified=1`** (i.e., verified present, source-grounded, no reviewer flag). This is a stricter filter than the raw 293 `present` rows — it uses only the 284 rows that pass both the automated grounding check and the manual review flag, consistent with the viewer's own default-shown set.
