# Report Appendix — 2026-07-10

Supporting tables for `docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`. Deterministic reference material only — no GABRIEL/codify, Harvard Proxy, or model/API calls were made to produce this appendix; every table below is compiled directly from `docs/analysis/gabriel_codify_evidence_layer.csv` and `docs/analysis/report_assets/`.

## A. 19-attribute codebook glossary

| attribute | label | definition |
|---|---|---|
| benefits_total_compensation_or_pension | Benefits, total compensation, or pension | Health insurance, pension, retirement, deferred compensation, paid leave, uniform allowance, equipment allowance, or non-wage benefits that affect compensation. |
| budget_capacity_or_fiscal_constraint | Budget capacity / fiscal constraint | Fiscal capacity, budget constraints, ability to pay, appropriations, tax limits, fiscal emergency, budgetary shortfall, or city financial condition used to shape wages. |
| civil_service_or_statutory_employment_channel | Civil-service or statutory employment channel | Civil-service provisions, statutory employment protections, meet-and-confer statutes, Chapter 174/142/146 references, Chapter 4117/SERB references, appointment/promotion rules, or statutory channels structuring bargaining or wage-setting. |
| classification_reclassification_or_grade_structure | Classification, reclassification, or wage-grade structure | Wage setting through classification systems, grades, steps, job titles, reclassification, compensation studies, wage schedules, or grade appeals. |
| grievance_or_contract_interpretation_arbitration | Grievance or contract-interpretation arbitration | Arbitration used for grievances, discipline, contract interpretation, enforcement, or disputes under an existing agreement. Excludes interest arbitration over successor contract terms. |
| hazard_risk_stress_or_line_of_duty_rationale | Hazard, risk, stress, or line-of-duty rationale | Explicit wage or benefit language tied to hazard, risk, injury, stress, line-of-duty harm, dangerous conditions, public-safety exposure, or physical/psychological burden. |
| interest_arbitration_or_formal_impasse_backstop | Interest arbitration / formal impasse backstop | Wage-setting or successor-contract settlement shaped by formal impasse institutions, such as interest arbitration, conciliation, factfinding, mediation-to-award processes, or bargaining in the shadow of formal impasse resolution. Excludes ordinary grievance arbitration. |
| management_rights_or_service_flexibility | Management rights / service flexibility | Management rights to assign, schedule, transfer, reorganize, determine staffing, set operations, change methods, deploy personnel, or maintain service flexibility. |
| minimum_staffing_or_continuous_coverage | Minimum staffing / continuous coverage | Minimum staffing, required crew levels, continuous coverage, 24/7 service obligations, station coverage, mandatory coverage, or inability to defer service. |
| no_strike_or_work_stoppage_constraint | No-strike / work-stoppage constraint | No-strike, no-slowdown, no-lockout, essential-service continuity, or statutory work-stoppage constraints. |
| non_safety_wage_restraint_or_admin_channel | Non-safety wage restraint / administrative channel | Evidence that non-safety wages are routed through administrative pay plans, classification systems, consultation rather than bargaining, weaker impasse pathways, delayed studies, pay-grade adjustments, or limited wage channels. |
| other | Other wage-mechanism evidence | Relevant wage-mechanism evidence not captured by the other attributes. Use sparingly. |
| overtime_callback_holdover_mandatory_extra_work | Overtime, callback, holdover, or mandatory extra work | Overtime, callback, holdover, mandatory overtime, court time, extra duty, standby/on-call, shift extension, or premium compensation for extra work demands. |
| peer_comparator_wage_comparability | Peer / comparator wage comparison | Explicit use of peer cities, comparable communities, external labor markets, comparator jurisdictions, or comparable bargaining units to justify wage levels, increases, or schedules. |
| premium_pay_differentials | Premium pay / differentials | Shift differentials, assignment differentials, specialty pay, longevity, night/weekend pay, holiday premiums, bilingual pay, paramedic pay, detail rates, or other add-ons beyond base wage. |
| staffing_shortage_recruitment_retention | Staffing shortage, recruitment, or retention | Explicit concern about vacancies, recruitment, retention, hiring, turnover, staffing shortages, labor supply, attrition, or inability to fill positions. |
| subcontracting_outsourcing_or_volunteer_substitution | Subcontracting, outsourcing, or substitution | Contracting out, outsourcing, privatization, volunteer substitution, non-unit labor replacement, civilianization, or restrictions on replacing bargaining-unit work. |
| training_certification_credential_premiums | Training, certification, credential, or education premiums | Wage premiums, stipends, incentives, requirements, or career ladders linked to training, certifications, degrees, licenses, credentials, or specialist qualifications. |
| union_security_or_institutional_power | Union security / institutional power | Union recognition, dues or agency checkoff, exclusive representation, release time, union access, bulletin boards, labor-management committees, bargaining rights, or institutional supports for union power. |

Source: unique `(attribute, attribute_label, attribute_definition)` tuples from `gabriel_codify_evidence_layer.csv`, one row per attribute.

## B. Source inventory — all 37 codified contracts

`verified_present_attribute_count` = number of this contract's attributes with `evidence_status=present AND viewer_verified=1` (out of 19 possible).

| state | city | contract_id | occupation | safety_group | source_type | text_quality | verified present attrs |
|---|---|---|---|---|---|---|---|
| MA | Boston | ma_boston_clerical_admin_2023 | Clerical / administrative | non_safety | cba | clean | 3 |
| MA | Franklin | ma_franklin_fire_2022 | Fire | safety | cba | clean | 6 |
| MA | Franklin | ma_franklin_library_2022 | Library | non_safety | cba | clean | 5 |
| MA | Franklin | ma_franklin_other_2022 | Other / mixed municipal | non_safety | cba | clean | 4 |
| MA | Franklin | ma_franklin_police_2022 | Police | safety | cba | clean | 8 |
| MA | Franklin | ma_franklin_public_works_2022 | Public works / DPW | non_safety | cba | clean | 2 |
| MA | Georgetown | ma_georgetown_other_2020 | Other / mixed municipal | non_safety | cba | clean | 0 |
| MA | Georgetown | ma_georgetown_police_2020 | Police | safety | cba | clean | 7 |
| MA | Seekonk | ma_seekonk_fire_2022 | Fire | safety | cba | clean | 5 |
| MA | Seekonk | ma_seekonk_library_2023 | Library | non_safety | cba | clean | 4 |
| MA | Seekonk | ma_seekonk_police_2022 | Police | safety | cba | clean | 4 |
| MA | Seekonk | ma_seekonk_public_works_2023 | Public works / DPW | non_safety | cba | clean | 5 |
| MA | Seekonk | ma_seekonk_teacher_2021 | Teachers / school employees | non_safety | cba | clean | 7 |
| MA | Somerville | ma_somerville_police_spsoa_2012 | Police | safety | arbitration_award | clean | 9 |
| MA | Wayland | ma_wayland_fire_jlmc_2020 | Fire | safety | arbitration_award | clean | 0 |
| MA | Wayland | ma_wayland_other_2021 | Other / mixed municipal | non_safety | cba | ocr_messy | 5 |
| OH | Cincinnati | oh_cincinnati_fire_2023 | Fire | safety | cba | clean | 0 |
| OH | Cincinnati | oh_cincinnati_other_2025 | Other / mixed municipal | non_safety | cba | clean | 1 |
| OH | Cincinnati | oh_cincinnati_police_2024 | Police | safety | cba | clean | 4 |
| OH | Cincinnati | oh_cincinnati_police_sup_2024 | Police | safety | cba | clean | 0 |
| OH | Cleveland | oh_cleveland_fire_2025 | Fire | safety | cba | ocr_messy | 12 |
| OH | Cleveland | oh_cleveland_other_2022 | Other / mixed municipal | non_safety | cba | clean | 9 |
| OH | Cleveland | oh_cleveland_police_2025 | Police | safety | cba | clean | 7 |
| OH | Columbus | oh_columbus_fire_2023 | Fire | safety | cba | clean | 10 |
| OH | Columbus | oh_columbus_other_2024 | Other / mixed municipal | non_safety | cba | clean | 12 |
| OH | Columbus | oh_columbus_police_2023 | Police | safety | cba | clean | 6 |
| OH | Toledo | oh_toledo_fire_2024 | Fire | safety | cba | clean | 4 |
| OH | Toledo | oh_toledo_other_2024 | Other / mixed municipal | non_safety | cba | clean | 2 |
| OH | Toledo | oh_toledo_police_2024 | Police | safety | cba | clean | 3 |
| TX | Austin | tx_austin_fire_2023 | Fire | safety | cba | clean | 10 |
| TX | Austin | tx_austin_nursehealth_2023 | Health / EMS / nurse-health | safety_adjacent | cba | clean | 10 |
| TX | Austin | tx_austin_police_2024 | Police | safety | cba | ocr_messy | 10 |
| TX | Houston | tx_houston_fire_2024 | Fire | safety | arbitration_award | clean | 8 |
| TX | Houston | tx_houston_other_2024 | Other / mixed municipal | non_safety | cba | clean | 9 |
| TX | Houston | tx_houston_police_2024 | Police | safety | cba | clean | 7 |
| TX | San Antonio | tx_san_antonio_fire_2024 | Fire | safety | cba | clean | 5 |
| TX | San Antonio | tx_san_antonio_police_2022 | Police | safety | cba | ocr_messy | 6 |

Two rows (`oh_cincinnati_fire_2023`, `oh_cincinnati_police_sup_2024`, `ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) show 0 verified-present attributes despite being codified — codify was run against a curated excerpt window for each, and returned `not_found` (or an excerpt that did not pass the verified-present filter) for all 19 attributes in that window. This reflects the excerpt-selection limitation documented in the main report's Method and Limitations sections, not an assertion that these contracts contain no wage-mechanism language.

Source: `docs/analysis/report_assets/source_inventory_for_report_2026-07-10.csv`.

## C. Report tables and figures generated this run

Figures (referenced inline in the report scaffold):

| file | used in report section |
|---|---|
| `report_assets/mechanism_presence_overall_by_safety_group_2026-07-10.png` / `.svg` | Headline Finding |
| `report_assets/arbitration_distinction_by_state_occupation_2026-07-10.png` / `.svg` | Mechanism Evidence Patterns — interest vs. grievance arbitration |
| `report_assets/pressure_conversion_mechanisms_by_occupation_2026-07-10.png` / `.svg` | Mechanism Evidence Patterns — pressure-to-wage conversion |
| `report_assets/massachusetts_cross_occupation_matrix_2026-07-10.png` / `.svg` | State Findings — Massachusetts |
| `report_assets/texas_institutional_contrast_2026-07-10.png` / `.svg` | State Findings — Texas |
| `report_assets/ohio_matched_triad_mechanism_matrix_2026-07-10.png` / `.svg` | State Findings — Ohio |

One additional figure was generated this run but not embedded inline in the Markdown scaffold — kept here as an appendix-only reference:

| file | contents |
|---|---|
| `report_assets/mechanism_presence_by_state_2026-07-10.png` / `.svg` | verified-present rate per attribute, broken out by state (MA/TX/OH) — the chart form of `mechanism_presence_by_state_2026-07-10.csv` below |

Underlying CSV tables (not directly embedded in the Markdown scaffold, but the source data behind the figures and prose claims above):

| file | contents |
|---|---|
| `report_assets/source_inventory_for_report_2026-07-10.csv` | one row per codified contract (37 rows) — state, city, occupation, safety_group, source_type, text_quality, verified-present attribute count |
| `report_assets/mechanism_presence_by_occupation_2026-07-10.csv` | verified-present rate per attribute, broken out by `occupation_class` |
| `report_assets/mechanism_presence_by_state_2026-07-10.csv` | verified-present rate per attribute, broken out by `state` |
| `report_assets/mechanism_presence_by_state_occupation_2026-07-10.csv` | verified-present rate per attribute, broken out by `state` x `occupation_class` |
| `report_assets/city_mechanism_matrix_2026-07-10.csv` | verified-present attribute matrix, one row per contract, one column per attribute |
| `report_assets/top_mechanisms_by_group_2026-07-10.csv` | most frequent verified-present attributes, ranked within each `safety_group` (safety / safety_adjacent / non_safety) |

## D. Using the interactive viewer

`docs/analysis/gabriel_codify_excerpt_browser_latest.html` — open directly in a browser (no server required). Lets a reader:

- filter coded excerpts by state, city, occupation class, and mechanism attribute;
- read each excerpt alongside its source contract, location, and grounding status;
- toggle "Show unverified / unsupported evidence" to reveal the 9 flagged/unverified `present` rows this report excludes from its headline counts and figures (see `report_evidence_layer_audit_2026-07-10.md` for the full list and flag reasons) — these remain in the underlying evidence layer, not deleted.

A dated archival snapshot of this run's viewer state is preserved separately at `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_expanded_texas_ohio.html`; `gabriel_codify_excerpt_browser_latest.html` always points at the most current build.
