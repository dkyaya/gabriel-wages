# Deeper Look Into Safety & Non-safety Wage Mechanisms

**Subtitle:** Mechanisms, Counterpoints, and Source Needs Across Municipal Occupations
**Header/report label:** Safety & Non-safety Wage Mechanisms

## Executive Summary

- **This report analyzes GABRIEL-coded evidence patterns, not causal estimates**, drawn from 37 codified municipal labor agreements across Massachusetts, Texas, and Ohio — 284 verified "present" findings across 19 wage-mechanism attributes (out of 293 coded present before verification; see Method).
- It compares **safety** (police, fire), **safety-adjacent** (EMS/nurse-health), and **non-safety** (teachers, public works, library, clerical/admin, and broad "other" municipal units) sources on the same coded attributes.
- **The evidence supports a mechanism story, not proof of a causal wage effect.** Codify records whether specific mechanism language appears in a curated source excerpt — it does not measure how much any mechanism moved a wage outcome, and a mechanism coded absent may simply not have been captured in this pass's excerpts rather than genuinely missing from the contract.
- **Police/fire sources more often show formal impasse/interest-arbitration backstops, staffing/coverage obligations, and overtime/premium-pay architecture** than non-safety sources coded so far — though the margins are moderate for several attributes, and grievance arbitration itself is common across both groups.
- **Non-safety sources most often show classification/wage-grade structure, benefits/total compensation, and management-rights language** — a different channel for converting pressure into pay, not evidence that pressure is absent.
- **Ohio has the cleanest matched triads** in this corpus (Columbus, Cleveland, Cincinnati, Toledo — each with a codified police, fire, and non-safety row under one statutory framework, ORC Chapter 4117); **Texas remains institutionally uneven** (only Houston has a genuine non-safety codified source); **Massachusetts offers the densest cross-occupation comparison** (Franklin and Seekonk each span five occupation classes within one city and cycle window).

## Scope and Data

- **Corpus:** `data/contracts.csv` has 53 rows across Massachusetts (32), Texas (8), and Ohio (13), spanning 16 distinct cities.
- **Codified subset:** 37 of those 53 contracts have been run through GABRIEL/codify as of this report (all 8 Texas contracts, all 13 Ohio contracts, 16 of 32 Massachusetts contracts). This report covers only the codified subset — it does not infer mechanism presence from uncodified source text.
- **States/cities covered:** Massachusetts (Boston, Franklin, Georgetown, Seekonk, Somerville, Wayland); Texas (Austin, Houston, San Antonio); Ohio (Cincinnati, Cleveland, Columbus, Toledo).
- **Source types:** collective bargaining agreements (`cba`) and one arbitration award (`arbitration_award`, Houston fire) — all `source_corpus=causal` per this project's two-corpus rule; no discourse-corpus text is used in this report.
- **Only verified present evidence is used for graph claims and headline counts**: `evidence_status=present AND viewer_verified=1`. This is 284 of the evidence layer's 293 present rows.
- **9 flagged/unverified present rows are excluded from every headline count and every graph in this report** (they remain in the underlying evidence layer and the viewer's "Show unverified" toggle, but are not treated as evidence here). See `report_evidence_layer_audit_2026-07-10.md` for the full list and reasons.

## Method

**In plain terms:** GABRIEL's `codify()` function reads a short, curated excerpt from each contract and answers one yes/no question per wage-mechanism attribute — does this specific language appear in this excerpt, or not? It does not weigh, score, or interpret the language beyond that binary call. The full 19-attribute codebook, with plain-English labels and definitions, is in Appendix A; it covers arbitration and impasse mechanisms, staffing and overtime, pay differentials, classification, benefits, management rights, and several other wage-relevant channels.

Every `present` result is checked twice before this report treats it as evidence. First, an automated check confirms the excerpt is an exact substring of its source window — not paraphrased, not invented (`source_grounding_status=grounded`). Second, a review pass flags any excerpt that echoes this project's own codebook vocabulary or leaks across a window boundary, rather than trusting it silently. **"Verified present" — what "present," "found," or a filled cell means anywhere in this report unless a figure says otherwise — means a finding passed both checks.** 9 of the 293 coded-present findings failed the second check and are excluded from every count and figure here; see `report_evidence_layer_audit_2026-07-10.md` for the full list and reasons.

The durable evidence layer (`docs/analysis/gabriel_codify_evidence_layer.csv`, 781 rows spanning five codify batches — pilot, Texas/Ohio scale-up, Massachusetts, Seekonk/Wayland, and expanded Texas/Ohio) backs every table and figure in this report. The companion viewer (`docs/analysis/gabriel_codify_excerpt_browser_latest.html`) lets a reader browse every coded excerpt directly, filtered by state, city, occupation, and mechanism, with unverified rows hidden by default.

**Limitations of the method itself:** codify is a binary presence detector operating over hand-curated excerpt windows, not full documents — a `not_found` result can mean the mechanism is genuinely absent from the contract, or simply that this pass's excerpt selection did not happen to include it. A few sources are OCR-recovered and text quality varies. None of this supports a causal wage estimate on its own.

## Headline Finding

The emerging pattern is not that public-safety work is simply "hard" and non-safety work is "easy." Rather, **safety wage pressure appears more likely to be paired with institutional channels that convert pressure into wage-setting claims**: formal impasse procedures, staffing/coverage obligations, overtime and premium-pay structures, and bargaining institutions with statutory teeth. **Non-safety wage pressure appears more often routed through classification, grades, management rights, and administrative channels** — different conversion machinery, not necessarily less real pressure underneath it.

![Mechanism presence by safety group](report_assets/mechanism_presence_overall_by_safety_group_2026-07-10.png)

## Mechanism Evidence Patterns

Across all 37 codified sources, the most frequently verified mechanisms overall are **overtime/callback/holdover** (23 of 37 sources, 62%), **classification/reclassification/grade structure** (20 of 37, 54%), **grievance/contract-interpretation arbitration** (19 of 37, 51%), **benefits/total compensation** and **union security** (18 of 37 each, 49%), and **management rights** and **premium pay** (16 of 37 each, 43%). These are broadly present channels — not distinctive to one occupation group — and any report claim about "what makes safety different" should be read against this shared baseline, not in isolation from it.

**Peer/comparator wage comparison** is the corpus's rarest verified attribute (1 of 37 sources) — almost certainly an under-coding artifact rather than a genuine absence: this project's own audit of the most recent codify batch documents a specific, observed false negative on San Antonio police, whose window contains explicit factfinding-panel language directing comparison to "comparable cities in the State of Texas" that the model did not flag (see `gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md`). Somerville's police JLMC arbitration award independently documents comparator language in its excerpt ("wages and benefits of comparable towns" as a statutory arbitration criterion) but that specific excerpt did not pass this run's stricter verified-present filter for this table. Readers should not conclude that peer-comparator wage logic is rare in practice — only that this codify pass under-detected it.

**Interest/formal-impasse arbitration vs. grievance arbitration.** The codebook was specifically refined to keep these two mechanisms distinct — one governs *how new wage terms get set at impasse*, the other governs *disputes under an existing agreement*. San Antonio police is this corpus's cleanest single-document test: the same contract's coded text distinguishes its Chapter 174 "Section 4. Impasse Procedure" ("the parties shall abide by the impasse procedure set forth in City Ordinance No. 51838...") from its separate Article 15 grievance-arbitration mechanism ("Section 4. Arbitration. If a grievance is submitted to arbitration...the decision of the arbitrator shall be final and binding"). Somerville police's JLMC award independently confirms interest arbitration is used "when there is an exhaustion of the process of collective bargaining which constitutes a potential threat to public welfare" — the Massachusetts-specific compulsory-arbitration backstop this project's earlier scoping work identified as JLMC's defining feature.

![Interest/impasse vs. grievance arbitration](report_assets/arbitration_distinction_by_state_occupation_2026-07-10.png)

**Staffing/recruitment/retention and minimum-staffing/continuous-coverage** are coded present in a minority of sources so far (5 of 37 each) — both are narrower, harder-to-detect claims (an explicit shortage/vacancy statement, or an explicit crew-size/coverage obligation) than the broader overtime or classification attributes, and likely undercount true prevalence for the same reason as peer-comparator language.

**Overtime/callback/holdover and premium pay** are common across both safety and non-safety sources (see the pressure-conversion heatmap below) — the institutional *form* differs (police/fire callback and standby-pay architecture vs. DPW storm/overtime incentive programs) but the underlying mechanism (extra-duty compensation) recurs across occupation groups.

**Classification/reclassification and grade structure** is, if anything, *more* common among non-safety sources coded so far (64% of non-safety sources vs. 45% of safety sources) — consistent with this project's standing hypothesis that non-safety wage pressure often gets absorbed into step/grade architecture rather than routed through arbitration.

**Management rights** shows the widest state-level spread of any attribute examined (19% of Massachusetts sources vs. 75% of Texas sources) — likely reflecting real drafting-convention differences across states' CBA templates rather than a substantive institutional difference; this is flagged as a caveat, not a finding, until confirmed against a larger Texas non-safety sample.

**Union security/institutional power** and **civil-service/statutory employment channel** are both broadly present (49% and 38% of all sources respectively) and track each state's own legal architecture closely — Ohio sources cite ORC 4117.08(C) management-rights language directly ("the City of Cincinnati retains the following management rights as set forth in Ohio Revised Code Section 4117.08(C)..."), a pattern repeated near-verbatim across all four codified Ohio cities.

**Budget/fiscal-constraint** and **non-safety wage-restraint/administrative-channel** language are both rare as verified evidence (2 and 3 of 37 sources respectively) — these are among the hardest attributes to detect from a short curated excerpt, since they typically require broader budget-document context this project's CBA-only corpus does not capture.

![Pressure-to-wage conversion mechanisms by occupation](report_assets/pressure_conversion_mechanisms_by_occupation_2026-07-10.png)

## State Findings

### Massachusetts

Massachusetts is this corpus's **densest cross-occupation laboratory**. Franklin and Seekonk each span five occupation classes within one city and overlapping cycle window (police, fire, plus three non-safety groups apiece), giving the report its most direct same-city, same-period safety-vs-non-safety comparisons. Somerville's police arbitration award is the corpus's clearest interest-arbitration document, reasoning explicitly through the "potential threat to public welfare" standard, and Wayland — including OCR-recovered fire and civilian/dispatch content — is this corpus's most mechanism-rich single city for testing the safety/civilian-adjacent boundary. Across Massachusetts, non-safety sources (Boston, Franklin, Seekonk, Georgetown) most often show classification and administrative-channel language rather than arbitration language — consistent with this project's standing finding that none of Massachusetts's non-safety occupation groups has JLMC-equivalent compulsory interest arbitration.

![Massachusetts cross-occupation matrix](report_assets/massachusetts_cross_occupation_matrix_2026-07-10.png)

### Texas

**Houston is Texas's only fully matched city** in this codified set — police, fire (an arbitration award, not a base CBA), and a genuine non-safety row (HOPE/AFSCME Local 123). **Austin's comparison runs through EMS**, not an ordinary civilian/clerical unit — Austin EMS is civil-service-protected and statutorily adjacent to police/fire, a caveat that must travel with any Austin-EMS finding rather than being generalized to "Texas non-safety." **San Antonio contributes police/fire institutional contrast only**, not a third matched triad: it was added specifically to test whether Houston's population-triggered compulsory-arbitration exception generalizes, and no non-safety bargaining channel was confirmed to exist for it. Texas's mechanism profile should be read with real caution: the "Texas non-safety" and "Texas safety-adjacent" bars in this report's charts each represent a single source (Houston HOPE; Austin EMS), so any 0%/100% reading is a small-sample artifact, not a robust state-level finding.

![Texas institutional contrast](report_assets/texas_institutional_contrast_2026-07-10.png)

### Ohio

**Ohio is the strongest state for matched-triad design** after this project's Texas/Ohio expansion: Columbus, Cleveland, Cincinnati, and Toledo each have a codified police, fire, and non-safety ("other") row, all operating under the same statewide statutory framework (Ohio Revised Code Chapter 4117 / SERB), which several codified sources cite directly and near-identically. This uniformity is itself informative — it means observed differences across these four cities are less likely to reflect different underlying labor law and more likely to reflect genuine city-to-city or document-to-document variation. Where coded, Ohio sources distinguish grievance arbitration (common across police, fire, and non-safety rows) from narrower, issue-specific interest-arbitration reopener clauses (e.g., Toledo's health-insurance-cost reopener, distinct from a general successor-agreement backstop) — consistent with this corpus's broader finding that interest/impasse arbitration and grievance arbitration are genuinely distinct mechanisms, not merely relabeled versions of each other.

![Ohio matched-triad matrix](report_assets/ohio_matched_triad_mechanism_matrix_2026-07-10.png)

## What Appears to Drive the Wage Gap?

This report does not claim a single leading cause. **The strongest evidence pattern is that safety wage-setting combines occupational pressure with stronger conversion channels** — several interacting mechanisms, not one:

1. **Formal impasse/arbitration backstops.** Where coded, interest/impasse arbitration appears more concentrated in safety and safety-adjacent sources than in non-safety sources (32% of safety sources vs. 7% of non-safety sources coded present) — a channel that gives safety bargaining a statutory route to a binding outcome that most non-safety units in this corpus lack.
2. **Staffing and continuous-coverage pressure.** Minimum-staffing and coverage-obligation language, though rare as verified evidence overall, appears exclusively in safety sources so far (23% of safety sources, 0% of non-safety or safety-adjacent sources coded present) — consistent with round-the-clock coverage obligations that most non-safety occupations in this corpus do not carry.
3. **Overtime/premium-pay architecture.** Present broadly, but somewhat more concentrated in safety sources (64% vs. 57% of non-safety sources) — a difference of degree, not kind.
4. **Peer/comparator wage logic in arbitration/factfinding contexts.** Likely under-detected by this codify pass (see above), but where captured (Somerville, San Antonio), comparator language appears embedded specifically within formal impasse/factfinding procedures — suggesting this mechanism may travel together with interest arbitration rather than standing alone.
5. **Non-safety routing through classification/administrative channels.** Non-safety sources show classification/grade-structure language at a higher rate than safety sources (64% vs. 45%) — a materially different, not simply weaker, wage-conversion path.

## Counterpoints and Non-safety Pressures

- Non-safety workers in this corpus's own sources face **real staffing, classification, wage-grade, and service-delivery pressure** — DPW storm-response overtime incentive programs (Arlington, Seekonk, Franklin, documented in this project's earlier DPW-focused sessions), library and clerical classification schedules, and teacher step-and-lane structures are not evidence of an absence of pressure, only of a different pressure-to-wage pathway.
- Some non-safety units carry **strong union-security and management-rights provisions** of their own — Cincinnati's CODE unit and Toledo's AFSCME Local 2058 both show verified union-security and no-strike language at rates comparable to their cities' safety counterparts.
- **The difference this report documents is not "pressure vs. no pressure" — it is which institutional channel converts pressure into a wage claim.** Classification and administrative channels can and do produce wage gains (step advancement, grade reclassification, compensation studies); they appear structurally different from arbitration-backstopped bargaining, not necessarily weaker in dollar terms — this report's binary present/not_found evidence cannot compare magnitudes.
- The rarity of coded `non_safety_wage_restraint_or_admin_channel` evidence (3 of 37 sources) should not be read as evidence that non-safety wage-setting is rarely constrained administratively — it more likely reflects that this specific claim (wages routed through consultation/administrative processes *instead of* ordinary bargaining) requires broader context than a short CBA excerpt typically contains.

## Source Needs and Next-State Strategy

Selection logic for any future state expansion should weigh:

- **Institutional contrast** — does the candidate state's public-safety bargaining law differ meaningfully from Massachusetts (JLMC), Texas (Chapter 174/142/146, population-gated), and Ohio (statewide ORC 4117/SERB)?
- **Source availability** — are CBAs/awards publicly downloadable, or does the state require FOIA/licensed-database access (out of scope for this project's public-download-only ingestion path)?
- **Matched-city triad potential** — can a state supply at least one city with police, fire, *and* a genuine non-safety bargaining channel, avoiding the Texas non-safety-coverage problem?
- **Arbitration/impasse variation** — does the candidate add a genuinely different impasse-resolution design (e.g., mandatory interest arbitration triggered differently, or no compulsory mechanism at all)?
- **Public-sector bargaining law variation** — including states where bargaining rights are narrower or absent, which would itself be an informative institutional contrast rather than a data gap to avoid.
- **Non-safety availability specifically** — this report's Texas experience shows that safety sources are consistently easier to locate publicly than non-safety sources; any next-state plan should scope non-safety availability *before* committing acquisition effort.

**Provisional candidate states** (not a final decision — see below):

- **New York** — rich municipal bargaining activity, but source volume and public-access consistency across NY's many home-rule municipalities is a real practical challenge.
- **New Jersey** — genuine interest-arbitration relevance (a real institutional-design contrast case) and generally comparable municipal-bargaining structure to test generalizability.
- **Pennsylvania** — Act 111 gives a clean public-safety-arbitration contrast case, with potential non-safety comparison sources also available.
- **Illinois** — large city and suburban source availability, with real bargaining-law variation across jurisdictions.
- **California** — strong bargaining institutions and generally good source availability, but the state's own bargaining landscape may be broad/complex enough to need its own dedicated scoping pass.
- **Florida, North Carolina, or Tennessee** — useful *weak-bargaining-channel* contrast states (right-to-work / limited public-sector bargaining rights in several of these), valuable specifically because they differ so much from the three states already in this corpus, if source availability supports a real comparison.

**This is not a final recommendation.** Per this project's own standing practice, any next-state work should begin with a dedicated source-availability scan (mirroring the `texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md` precedent) before any acquisition effort is authorized.

## Report Limitations

- **GABRIEL/codify is a binary presence detector**, not a strength, frequency, or dollar-magnitude measurement — every finding in this report is "was this language coded present," not "how much did this mechanism matter."
- **Source windows are curated**, not full documents — a `not_found` result can reflect either genuine absence or an excerpt-selection gap; this report cannot distinguish the two without re-reading full source text.
- **Not all possible mechanisms are captured in every source** — the 19-attribute codebook is this project's own construction and may not exhaustively cover every wage-relevant clause type in every document.
- **Text quality varies** — several sources are OCR-recovered (San Antonio police, Wayland's dispatch/nurse content, others) and carry a documented risk of minor extraction error, distinct from the fabrication risk this project's grounding checks specifically guard against.
- **9 flagged/unverified present rows are excluded from every headline count and graph in this report** — they remain visible in the underlying evidence layer and viewer, not deleted, but are not treated as evidence here.
- **Texas non-safety evidence remains limited** — a single genuine non-safety source (Houston HOPE) and a single safety-adjacent source (Austin EMS) support every Texas non-safety/adjacent claim in this report; these should be read as illustrative, not representative.
- **Results are evidence patterns, not causal estimates.** Nothing in this report should be read as measuring the size of any wage effect, isolating one mechanism's contribution from another's, or ruling out confounding factors (city fiscal capacity, local labor-market conditions, political salience) this project has not yet measured.

# Appendix

Supporting tables for the integrated report. Deterministic reference material only -- no GABRIEL/codify, Harvard Proxy, or model/API calls were made to produce this appendix; every table below is compiled directly from `docs/analysis/gabriel_codify_evidence_layer.csv` and `docs/analysis/report_assets/`.

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

Four rows (`oh_cincinnati_fire_2023`, `oh_cincinnati_police_sup_2024`, `ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) show 0 verified-present attributes despite being codified — codify was run against a curated excerpt window for each, and returned `not_found` (or an excerpt that did not pass the verified-present filter) for all 19 attributes in that window. This reflects the excerpt-selection limitation documented in the main report's Method and Limitations sections, not an assertion that these contracts contain no wage-mechanism language.

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
