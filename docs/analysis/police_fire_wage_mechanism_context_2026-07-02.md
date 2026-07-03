# Police and Fire Wage Mechanism Context Memo

**Date:** 2026-07-02  
**Scope:** mechanism-development memo only; no GABRIEL run, no ingestion, no causal claim

## 1. Purpose and scope

This memo steps back from the current GABRIEL implementation work and asks a broader mechanism question: why might police and firefighter wages be high, or rise faster than other municipal occupations, in at least some places and periods?

The goal is to develop competing mechanisms, counterarguments, and evidence requirements. It does **not** establish causal effects. It also does **not** assume that any one mechanism is unique to public safety. For each candidate mechanism, the key question is whether it operates differently, more intensely, or more persistently for police and fire than for comparison municipal occupations.

## 2. Current project baseline

### Corpus status

The current causal corpus is still modest and Massachusetts-heavy. As of the latest validation/audit state reflected in the repo, it contains 32 causal rows across 9 cities, with 12 healthy matched safety rows, 9 exact-cycle matches, and 3 overlap-cycle matches. The strongest explicit wage-setting reasoning remains concentrated in a small number of award-style safety documents.

### What v9 means in plain English

v9 is the current `comparability_emphasis` GABRIEL attribute. In plain English, it asks whether a document explicitly justifies wages by referring to peer communities, comparator jurisdictions, parity relationships, or other external wage benchmarks.

v9 is useful as a descriptive measure of explicit comparator talk in documents. It is **not** a clean occupation effect because the strongest reasoning documents in the current corpus are disproportionately safety-side arbitration awards. In that sense, v9 is both descriptive and source-type-confounded.

### What v10 means in plain English

v10 is a proposed/tested `arbitration_or_impasse_backstop` attribute. In plain English, it asks whether wage-setting is shaped by formal impasse institutions such as interest arbitration, JLMC proceedings, mediation, factfinding, stipulated awards, or bargaining in the shadow of those procedures.

That is only one institutional mechanism. Even if v10 eventually scores strongly for police or fire, it would not by itself explain all wage pressure. It would only show that formal dispute-resolution backstops are more visible in the wage-setting path.

### What the Boston web test did and did not show

The bounded Boston GABRIEL web test showed that carefully constrained source discovery can work in this environment. It did **not** produce a substantive measure of any wage mechanism. It was a source-discovery and implementation proof-of-bounds result, not a mechanism result.

## 3. Police labor-market background

Several overlapping mechanisms could generate police wage pressure.

First, police hiring markets may be tight even when nominal applicant counts recover. The BLS Occupational Outlook Handbook reports 62,200 projected annual openings for police and detectives over 2024-2034, many from replacement demand rather than net growth, and describes a job with stressful, dangerous, shift-based work and common overtime ([BLS OOH, Police and Detectives](https://www.bls.gov/ooh/protective-service/police-and-detectives.htm)). That combination suggests that agencies may need to pay not just to attract any applicants, but to attract applicants who can meet academy, background, physical, and retention demands.

Second, post-2019/2020 staffing stress should be treated as multi-causal. A plausible mechanism is that public scrutiny after George Floyd, broader legitimacy conflict, and anti-police sentiment reduced applications or increased exits in some jurisdictions. But that should sit alongside other candidate explanations: COVID-era labor-market disruption, retirement waves, burnout, slower hiring pipelines, competition from other law-enforcement employers, and wider outside options. An AP summary of a 2024 PERF survey reports both improvement in 2023 hiring and continuing large-department staffing gaps, which fits a recovery-but-not-resolution story rather than a single-shock explanation ([AP on PERF survey, 2024-04-28](https://apnews.com/article/7e39156a80de2d75e22bd554adc8f887)).

Third, police work includes burdens that can matter for compensation even when not fully visible in a salary schedule: round-the-clock shift coverage, court appearances, overtime, callback, emotional strain, exposure to violence, liability risk, and extensive entry/training requirements. BLS notes that police have some of the highest injury and illness rates of any occupation, that shift work is necessary at all times, and that academy training plus rigorous qualifications are standard ([BLS OOH, Police and Detectives](https://www.bls.gov/ooh/protective-service/police-and-detectives.htm)).

Counterargument: none of this proves unusual scarcity. Some departments may still receive many applicants, and in some places the problem may be processing speed, standards, or lateral competition rather than low applicant interest. The evidence needed would be agency-level time series on applicants per academy seat, pass-through rates, vacancy duration, exits, retirements, and lateral transfers, ideally compared with non-safety municipal hiring pipelines in the same labor market.

## 4. Firefighter labor-market background

Fire has a different labor-market structure from police, so firefighter wage pressure should not be assumed to arise from the same pathway.

The first distinction is career versus volunteer. BLS reports that paid firefighters held about 344,900 jobs in 2024, but those counts exclude volunteers, and volunteer firefighters still account for the largest share of firefighters nationwide, especially in communities under 25,000 ([BLS OOH, Firefighters](https://www.bls.gov/ooh/protective-service/firefighters.htm)). That matters because pressure can appear as wage pressure in career departments, but as recruitment, retention, training, and turnout strain in volunteer or combination systems.

The second distinction is that public esteem does not automatically imply abundant qualified career supply. BLS describes firefighters as typically needing EMS training, fire-academy training, physical testing, ongoing credential maintenance, and work schedules with long shifts and common overtime ([BLS OOH, Firefighters](https://www.bls.gov/ooh/protective-service/firefighters.htm)). Firefighter work also now includes large EMS burdens in many jurisdictions, not just fire suppression. So "well-liked occupation" does not automatically mean easy staffing at the credentialed career margin.

Third, firefighter median pay can still be lower than police pay despite training and EMT requirements. The 2024 BLS median was $59,530 for firefighters versus $77,270 for police and detectives ([BLS OOH, Firefighters](https://www.bls.gov/ooh/protective-service/firefighters.htm); [BLS OOH, Police and Detectives](https://www.bls.gov/ooh/protective-service/police-and-detectives.htm)). Plausible reasons include occupational composition differences, different local labor markets, the presence of many volunteer and combination systems, different promotion structures, and the fact that some firefighter burdens may show up in overtime, staffing rules, or training budgets rather than in base wage levels.

Fourth, firefighter hazards and coverage constraints remain real even in an occupation with positive public standing. BLS reports high injury/illness rates, long shifts, common overtime, and heavy protective gear, while NIOSH maintains a dedicated firefighter safety program and a National Firefighter Registry for Cancer because exposure risk is a serious national concern ([BLS OOH, Firefighters](https://www.bls.gov/ooh/protective-service/firefighters.htm); [CDC/NIOSH Firefighters](https://www.cdc.gov/niosh/firefighters/); [National Firefighter Registry for Cancer](https://www.cdc.gov/nfr/)).

Fifth, volunteer recruitment and retention problems may transmit into wage pressure only indirectly. If volunteer pipelines weaken, communities may face more paid-on-call compensation, more training and turnout subsidies, more reliance on combination staffing, or pressure to professionalize formerly volunteer coverage.

Definitions for non-specialists:

- `NFPA` = National Fire Protection Association, a major standards-setting and research organization in the fire space ([NFPA](https://www.nfpa.org/)).
- `FPRF` = Fire Protection Research Foundation, NFPA's research affiliate ([FPRF](https://www.nfpa.org/education-and-research/research/fire-protection-research-foundation)).
- `NVFC` = National Volunteer Fire Council, a national organization focused on volunteer fire and EMS support, training, advocacy, and recruitment/retention resources ([NVFC](https://www.nvfc.org/)).

Counterargument: many firefighter jobs remain highly sought after in some metro departments, so wages may reflect institutional rules, overtime design, or city fiscal capacity more than true applicant scarcity. The evidence needed would be department-level applicant counts, academy selectivity, volunteer turnout and attrition, EMS share of call volume, staffing minimums, and the relationship between vacancies and overtime spending.

## 5. Non-safety comparison

Vacancies, sick time, PTO, overtime, training, and retention pressures are not unique to police and fire. Schools, nursing and public health, transit, sanitation, snow removal, utilities, and emergency public works can all face staffing problems, hard schedules, and service demands.

The relevant question is not whether these pressures exist elsewhere, but whether police and fire face a different operating environment:

- 24/7 coverage and immediate response expectations
- minimum staffing rules or de facto floor staffing
- emergency-response constraints
- callback and mandatory overtime
- limited ability to defer work into the next day or next week
- stronger political/public salience when service degrades

Even here, the comparison should stay disciplined. Transit operators, school staff, nurses, dispatchers, sanitation crews during storms, and public works during weather or infrastructure emergencies can also face hard coverage constraints. So the evidence question is comparative intensity: are absences, vacancies, and schedule gaps more operationally costly in police/fire than in those non-safety units, and if so under what institutional conditions?

Counterargument: many non-safety municipal jobs are also hard to replace on short notice, and some have equally binding service obligations. Evidence would need to compare vacancy duration, overtime substitution, service deferral options, and downstream service disruption across unit types within the same city.

## 6. Arbitration and bargaining backstops

Interest arbitration and grievance arbitration are different. Grievance arbitration resolves disputes about contract interpretation. Interest arbitration resolves unresolved terms in bargaining, often including wages. That distinction matters because the present project is about wage-setting, not routine contract administration.

Massachusetts JLMC is one institutional case, not the entire national story. It is useful because it gives police and fire a visible public-sector impasse infrastructure, but broader-state snippets may reveal other mechanisms, including conventional mediation/factfinding, final-offer arbitration, local statutory backstops, or no special backstop at all.

Formally, arbitrators are usually supposed to apply statutory or contractual criteria rather than simply split the difference. In practice, the literature raises several possibilities:

- a criteria-applying model, where the arbitrator tries to reach a legally supportable and reasonable outcome;
- a shadow-of-arbitration model, where the credible risk of third-party resolution shapes settlements before an award;
- a middle-ground model, where parties expect arbitrators to avoid extremes;
- final-offer arbitration variants, which can alter bargaining incentives by forcing a choice among party offers rather than free-form compromise.

The classic literature also discusses `chilling effects` and `narcotic effects`. In this context, a chilling effect means parties may bargain less seriously because arbitration is available. A narcotic effect means repeated use of arbitration may make the parties increasingly dependent on it over time. These are hypotheses, not settled facts for this project.

A further possibility is documentation asymmetry. Arbitration and impasse settings may generate more written comparability reasoning even if comparator logic also exists outside safety bargaining. That could make safety wage-setting look more comparator-driven in text than it really is in the full bargaining universe.

Counterargument: arbitration may be more visible in documents than more important in outcomes. The evidence needed would compare wage movement in otherwise similar settlements with and without formal impasse procedures, and also compare how often comparability language appears in award-style documents versus ordinary agreements.

## 7. Wage trend data sources

### BLS OEWS

OEWS can measure occupation-level wages nationally, by state, and by metropolitan/nonmetropolitan area. BLS explicitly states that OEWS produces annual employment and wage estimates for roughly 830 occupations and makes them available for the nation, states, and metropolitan/nonmetropolitan areas ([OEWS overview](https://www.bls.gov/oes/)). This is the strongest public source for descriptive police-versus-fire wage trends across places.

Limits:

- occupation-level, not bargaining-unit-level;
- public and private employers can be mixed depending on how the table is pulled;
- metro/nonmetro is not the same as municipality;
- county-level occupational wage measurement is not the standard OEWS geography for this use case.

### Census ASPEP

ASPEP provides state and local government civilian employment and gross March payroll by government function ([ASPEP](https://www.census.gov/programs-surveys/apes.html)). This is useful for public-sector context, especially police/fire function payroll and staffing at broader government-function levels.

Limits:

- payroll is by function, not bargaining unit;
- monthly March payroll is not a clean annual wage measure;
- local detail is not the same as city-by-unit contract wage schedules.

### State payroll or pension transparency

These can sometimes produce municipal employee-level or title-level pay distributions, overtime, and retirement patterns. They may be the best route to county- or city-specific descriptive pay structures where available.

Limits:

- often inconsistent across states;
- titles do not always map cleanly to bargaining units;
- overtime and base pay may be mixed in ways that complicate trend interpretation.

### Local payroll/overtime reports

These are useful for mechanism discovery, especially overtime/staffing spirals and callback burden.

Limits:

- not standardized;
- often anecdotal or highly city-specific;
- can exaggerate tail cases if treated as broad evidence.

### Contract wage schedules

CBAs and MOAs can often be converted into unit-level negotiated base-wage series when the schedules are explicit and comparable over time. This is probably the cleanest route to bargaining-unit wage trends, but only where public contracts already exist in the corpus or are otherwise clearly public.

Limits:

- missing contracts create survivorship bias;
- step structures, longevity, and side letters complicate comparability;
- scheduled rates are not the same as realized earnings.

### Is county-level or unit-level measurement realistic?

County-level occupational wage trend measurement is realistic for some descriptive purposes only if a public source clearly supports that geography. Unit-level bargaining-unit wages are generally **not** available in national datasets like OEWS or ASPEP. Real bargaining-unit wage trends will usually require contract schedules, municipal salary ordinances, or payroll transparency files. So a national unit-level panel is not realistic from BLS/Census alone.

## 8. Expanded hypothesis map

1. `labor_scarcity_recruitment_pressure`
   Police or fire wages rise because departments need to attract and keep enough qualified workers in a constrained labor market.

2. `post_2020_police_legitimacy_morale_shock`
   Police wages rise because post-2020 public scrutiny, morale problems, resignations, and reduced applicant interest increased the compensation needed to staff departments.

3. `compensating_differentials_risk_stress_hours`
   Wages rise as compensation for dangerous, stressful, irregular, or highly intrusive working conditions.

4. `overtime_staffing_spiral`
   Understaffing leads to more overtime and callback; overtime dependence raises total compensation pressure and can itself worsen retention.

5. `comparator_ratchet`
   Wage setting is pulled upward by peer-city comparisons, parity expectations, or regional ratcheting.

6. `arbitration_impasse_backstop`
   Formal impasse procedures or bargaining in their shadow strengthen wage demands or increase settlement leverage.

7. `political_salience_public_safety_premium`
   Elected officials may pay more to avoid visible public-safety deterioration than to avoid slower degradation in less salient services.

8. `union_power_institutional_privilege`
   Police/fire unions may enjoy stronger bargaining leverage, favorable statutes, or more durable organizational power.

9. `budget_capacity_property_tax_base`
   Richer jurisdictions can pay more, and police/fire may capture disproportionate shares of that capacity.

10. `credentialing_training_barriers`
   Wages rise because entry and maintenance requirements narrow supply or increase replacement costs.

11. `volunteer_to_career_transition_pressure`
   Fire wages rise where weakening volunteer systems push departments toward more paid coverage.

12. `risk_liability_legal_exposure`
   Wages rise because employers must compensate for exposure to injury, trauma, litigation, and career-ending incidents.

## 9. Claim / counterpoint / evidence table

| mechanism | plausible claim | counterpoint | evidence that would distinguish it | likely source types | relevance to police | relevance to fire | relevance to non-safety comparison |
| --- | --- | --- | --- | --- | --- | --- | --- |
| labor scarcity / recruitment pressure | Departments must pay more to attract enough qualified applicants | Applicant pools may be large, with the bottleneck in standards or processing | Applicants per opening, academy fill rates, pass-through rates, vacancy duration, exit rates | BLS, PERF, local HR reports, city budgets | high | medium-high | compare with teacher, transit, nursing, DPW hiring pipelines |
| post-2020 policing climate | Public scrutiny and morale shocks reduced police supply | Could instead reflect retirements, COVID labor disruption, or agency competition | Application trends before/after 2020, retirements, resignations, surveys, lateral flows | PERF, city staffing reports, news, union statements | high | low | not a general non-safety explanation |
| compensating differentials | Risk, stress, and shifts require wage premia | Many non-safety jobs are also risky or stressful | Injury rates, irregular hours, shift premiums, retention response to hazard exposure | BLS OOH, NIOSH, workers-comp data | high | high | compare with transit, sanitation, nursing, public works emergencies |
| overtime / staffing spiral | Understaffing raises overtime, which raises compensation expectations and burnout | Overtime may be symptom rather than cause | Vacancy and OT time series, callback rules, leave coverage, exit hazards | payroll reports, budgets, contracts | high | high | compare with snow ops, transit, hospital/EMS roles |
| comparator ratchet | Peer-city wages become bargaining anchors and ratchet pay upward | Comparator language may reflect document style more than true causation | Matched text plus wage-trend linkage across peers | arbitration awards, bargaining packets, CBAs | high | medium-high | comparability can also appear in teacher and other public bargaining |
| arbitration / impasse backstop | Formal impasse rules strengthen wage leverage | Could mostly increase documentation, not outcomes | Compare settlements with/without backstops; award incidence; language frequency | awards, JLMC pages, arbitration scholarship | high | high | some non-safety sectors may also use factfinding/mediation |
| political salience / public safety premium | Officials pay more to avoid visible safety failure | Some non-safety breakdowns are also highly salient | Budget responses to staffing crises across units | budgets, council minutes, news | high | high | compare with schools, transit, sanitation, snow events |
| union power / institutional privilege | Police/fire unions have stronger leverage or protected status | Fiscal and labor-market constraints may dominate | Statutory rules, bargaining timelines, impasse outcomes, strike constraints | legal sources, arbitration scholarship, state statutes | high | high | compare with teacher or clerical regimes |
| budget capacity / tax base | Rich places can simply afford higher safety pay | Capacity may raise all wages, not just safety pay | Within-city allocation patterns and across-city fiscal gradients | Census, CAFRs, payroll data | medium | medium | essential general control, not safety-specific |
| credentialing / training barriers | Training and credential rules narrow supply | Credentials may matter more for quality than wages | Pass/fail rates, academy bottlenecks, credential maintenance costs | BLS, NVFC, state academy/credential rules | medium | high | compare with CDL, nursing, licensing in other city jobs |
| volunteer-to-career transition pressure | Volunteer weakness pushes communities toward paid coverage and higher wages | Some areas respond with stipends, aid, or consolidation instead | Volunteer headcount, turnout, conversion to career staffing, paid-on-call growth | NVFC, NFPA/FPRF, local fire studies | low | high | mainly a fire-specific comparison channel |
| risk / liability / legal exposure | Legal and personal exposure raises compensation demands | Exposure may affect morale more than wages | Litigation, disability retirement, workers-comp, insurance, PTSD leave | local claims data, NIOSH, budget docs | high | medium-high | compare with corrections, nursing, transit safety roles |

## 10. Implications for GABRIEL/source extraction

Future candidate attributes should separate mechanisms more cleanly:

- `recruitment_retention_pressure`
  Count explicit discussion of applicant shortages, vacancies, hiring difficulty, resignations, retirements, failed academy classes, lateral competition, or retention incentives.
  Do **not** count generic staffing mentions with no pressure signal.

- `overtime_staffing_pressure`
  Count mandatory overtime, callback, leave-coverage strain, minimum staffing, vacancy-driven overtime, and service reduction due to understaffing.
  Do **not** count ordinary wage schedules that happen to mention overtime rates.

- `hazard_or_working_conditions`
  Count danger, injury, trauma, stress, shift burden, constant readiness, exposure, or work-environment compensation arguments.
  Do **not** count generic pride/respect language.

- `training_credentialing_burden`
  Count academy, EMS/EMT, certification maintenance, physical testing, background requirements, and training-time burdens when linked to supply or compensation.
  Do **not** count mere job-description boilerplate.

- `public_safety_service_necessity`
  Count arguments that immediate coverage, emergency response, minimum staffing, or inability to defer work make staffing unusually consequential.
  Do **not** count generic public-service mission statements.

- `arbitration_or_impasse_backstop`
  Count interest arbitration, factfinding, mediation after impasse, JLMC, stipulated awards, and bargaining in the shadow of those processes.
  Do **not** count grievance arbitration boilerplate.

- `comparability_emphasis`
  Count explicit peer-jurisdiction wage reasoning, parity, or comparator tables tied to compensation.
  Do **not** count CPI/COLA or generic "market adjustment" language unless external wage comparison is explicit.

- `fiscal_capacity_ability_to_pay`
  Count ability-to-pay arguments, tax-base constraints, revenue limits, budget stress, or fiscal reserves when tied to wage-setting.
  Do **not** count generic budget descriptions with no bargaining relevance.

- `political_support_or_public_salience`
  Count arguments that public, elected officials, or political risk make police/fire outcomes unusually salient.
  Do **not** count generic praise of first responders.

- `union_power_or_institutional_leverage`
  Count references to statutory leverage, bargaining protections, institutional standing, or unusual procedural advantages.
  Do **not** count generic union presence.

- `post_2020_policing_climate`
  Count explicit discussion of post-2020 scrutiny, legitimacy, morale, resignations, or recruitment impacts.
  Do **not** treat any mention of George Floyd or protests as sufficient by itself without a staffing or bargaining link.

## 11. Recommended next empirical steps

### Desk research

Stay in mechanism-development mode. Expand the memo's source base with a small, curated set of public sources from BLS, Census, PERF, NFPA/FPRF/NVFC, Mass JLMC, and a few arbitration-law references.

### Trend-data pull

Start with descriptive wage and employment trends from OEWS and functional payroll context from ASPEP. Treat bargaining-unit wage trend construction as a separate, harder layer.

### Public-source snippet extraction

Extract a small number of mechanism-rich public snippets from broader states and cities, explicitly not limited to Massachusetts, to see whether police/fire wage explanations differ across institutional environments.

### GABRIEL attribute design

Use the attribute candidates above to create a mechanism map before scaling model runs. The point is to reduce conceptual crowding between comparability, arbitration, staffing, and hazard stories.

### Ingestion

Keep ingestion separate. This memo does not justify new ingestion or broad web-search scaling. The recommended next step is still mechanism development, not corpus expansion for its own sake.

## Sources referenced in this memo

- BLS Occupational Outlook Handbook, Police and Detectives: <https://www.bls.gov/ooh/protective-service/police-and-detectives.htm>
- BLS Occupational Outlook Handbook, Firefighters: <https://www.bls.gov/ooh/protective-service/firefighters.htm>
- BLS Occupational Employment and Wage Statistics overview: <https://www.bls.gov/oes/>
- Census Annual Survey of Public Employment & Payroll: <https://www.census.gov/programs-surveys/apes.html>
- CDC/NIOSH Firefighters: <https://www.cdc.gov/niosh/firefighters/>
- CDC National Firefighter Registry for Cancer: <https://www.cdc.gov/nfr/>
- NFPA: <https://www.nfpa.org/>
- Fire Protection Research Foundation: <https://www.nfpa.org/education-and-research/research/fire-protection-research-foundation>
- National Volunteer Fire Council: <https://www.nvfc.org/>
- AP summary of PERF staffing survey, 2024-04-28: <https://apnews.com/article/7e39156a80de2d75e22bd554adc8f887>
