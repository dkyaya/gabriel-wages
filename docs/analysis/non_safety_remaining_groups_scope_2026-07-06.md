# Remaining Non-Safety Groups Scope — Nurse/Health, Custodial/Facilities, Dispatchers — 2026-07-06

**Type:** dated scoping memo. Resolves the three remaining ambiguous non-safety groups flagged as open scoping decisions since `wage_mechanism_project_checkpoint_2026-07-05.md` §11 (items 3, 6, 7).

## 1. Purpose and scope

This memo scopes three occupation groups this project has not yet examined in depth: `nurse_health`/public health, custodial/facilities/building maintenance, and dispatchers/911 telecommunicators. It includes Massachusetts institutional context and bounded national context for each. It does not ingest documents, run GABRIEL, or make a causal claim about why any group's wages move the way they do — it is governance/mechanism scoping only, feeding a later cross-group audit (`all_groups_wage_mechanism_audit_2026-07-06.md`) and, eventually, a PI-facing report whose format is decided separately. This run does not draft that report.

## 2. Current corpus coverage

**Direct matches:** none. `data/contracts.csv` (32 rows) has zero rows with `occupation_class = nurse_health`, and no dedicated dispatcher or custodial occupation class exists in the controlled vocabulary at all — both would currently have to be coded `other` if collected as their own bargaining unit.

**Hidden/bundled coverage — the most consequential finding of this memo:** a direct re-read of already-collected corpus text (no new ingestion) found genuine hidden content for all three groups:

- **`ma_wayland_other_2021`** (Local 690 Wayland-1 and Wayland-2, AFSCME, currently coded `other`): its own `total_comp_note` field states the recognition clause "covers mixed town employees including clerical, DPW, **nurses**, **dispatch**, and other positions." This single row is a candidate hidden source for *three* of this session's four groups simultaneously (nurse_health, dispatchers, and possibly custodial/facilities under "other positions"). The underlying PDF (`corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf`) is a scanned, no-text-layer document — a `pdftotext` extraction attempted this session returned zero lines, confirming only the cover page has been OCR'd to date, per the row's own note.
- **`ma_arlington_public_works_2015/2018/2021`** (AFSCME Local 680, three contract cycles): the row's `total_comp_note` already states the unit "Covers Labor Service (DPW, custodians), clerical, civil engineers grades 1-3, and administrative personnel." A direct `pdftotext` re-read of the 2015-cycle PDF this session (already-collected text, no new ingestion) confirmed explicit, detailed "Community Safety Dispatchers" language: a defined staffing complement ("nine (9) persons and a Lead Dispatcher"), an explicit minimum-coverage rule ("Coverage must be maintained by a full complement of two (2) dispatchers at all times"), and sick-call-in/coverage-backfill language. This is genuine, already-in-corpus, dispatcher-specific mechanism text — the richest single piece of dispatcher evidence this project has, requiring zero new acquisition to use.
- **`ma_georgetown_other_2020`** (AFSCME Local 939, coded `other`): its `total_comp_note` confirms this unit is "Georgetown School Department custodians/matrons/maintenance unit" — a direct custodial/facilities match, currently invisible under the generic `other` label.
- **`ma_franklin_other_2022`** (AFSCME Local 1298, coded `other`): its `total_comp_note` confirms this unit is "Custodians" — the same pattern as Georgetown, a direct custodial/facilities match hidden under `other`.

**Adjacent, not core:** none identified beyond the above.

**Absent:** no direct nurse_health-only bargaining unit, no direct dispatcher-only bargaining unit, and no direct custodial-only bargaining unit outside the two `other`-coded rows above exists anywhere in this project's corpus.

### Task A coverage table

| possible_group | contract_id | city | occupation_class | unit/title | source_type | year/period | corpus file path | file exists | relevance | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nurse_health | ma_wayland_other_2021 | Wayland | other | Local 690 Wayland-1/Wayland-2, AFSCME | cba | 2021-2023 | corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf | yes (scanned, no text layer beyond cover page) | possible_hidden_or_bundled | Recognition clause names "nurses" explicitly per the row's own `total_comp_note`; job-title-level detail requires an OCR pass not performed this session |
| custodial/facilities | ma_georgetown_other_2020 | Georgetown | other | AFSCME Local 939 (Custodians) | cba | 2020-2023 | corpus/ma_georgetown/... (path not re-verified this session; see existing row) | yes | direct_match (mislabeled) | `total_comp_note` explicitly states "custodians/matrons/maintenance unit" — a direct custodial match currently coded `other` because custodial/facilities has no controlled-vocabulary value |
| custodial/facilities | ma_franklin_other_2022 | Franklin | other | AFSCME Local 1298 (Custodians) | cba | 2022-2025 | corpus/ma_franklin/... (path not re-verified this session; see existing row) | yes | direct_match (mislabeled) | `total_comp_note` explicitly states "Classified as other because custodians are not a controlled occupation class" |
| custodial/facilities | ma_arlington_public_works_2015/2018/2021 | Arlington | public_works | AFSCME Local 680 | cba | 2015-2024 (3 cycles) | corpus/ma_arlington/ma_arlington_afscme_cba_fy2016_2018.pdf (+2 successor files) | yes | possible_hidden_or_bundled | `total_comp_note` names "custodians" as part of the broader Labor Service unit; not separately classified or re-read for job-description-level custodial content this session |
| dispatchers | ma_wayland_other_2021 | Wayland | other | Local 690 Wayland-1/Wayland-2, AFSCME | cba | 2021-2023 | corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf | yes (scanned, no text layer beyond cover page) | possible_hidden_or_bundled | Recognition clause names "dispatch" explicitly per the row's own `total_comp_note` |
| dispatchers | ma_arlington_public_works_2015/2018/2021 | Arlington | public_works | AFSCME Local 680 | cba | 2015-2024 (3 cycles) | corpus/ma_arlington/ma_arlington_afscme_cba_fy2016_2018.pdf (+2 successor files) | yes | direct_match (mislabeled/bundled) | Direct `pdftotext` re-read this session (already-collected text) confirms explicit "Community Safety Dispatchers" language: 9-person complement plus Lead Dispatcher, minimum 2-dispatcher coverage rule, sick-call-in backfill language — the richest dispatcher evidence in this project's corpus |
| nurse_health/dispatchers/custodial (composite) | — | all 9 cities | — | — | — | — | n/a | not_relevant | No other row's fields (checked via full-CSV keyword search for "custodian," "janitor," "dispatch," "telecommunicator," "911," "nurse," "health," "clinic," "maintenance," "facilities," "building," "hvac," "electrician," "plumb") showed any further hits beyond those already listed above and the ones noted in the sanitation/transit scans |

Do not edit `data/contracts.csv`. This table is descriptive only.

## 3. Nurse_health / public health

### Occupation/classification map

- **Public health nurses** — municipal or regional health-department employees performing community health, immunization, communicable-disease, and inspectional-adjacent work; distinct from clinical hospital nursing.
- **School nurses** — employed by the school committee/district, embedded in school-finance and school-committee bargaining channels (per this project's teacher-group findings) rather than general municipal government.
- **Municipal health department nurses** — general local board-of-health staff who may hold a nursing credential but perform a mix of clinical and administrative/regulatory duties.
- **Inspectional/public health staff** (health agents, sanitarians) — regulatory/inspectional roles, not nursing per se, but often organizationally co-located with public health nurses in the same municipal department; out of core scope for a "nurse" comparison group unless a specific bargaining unit bundles them.
- **Clinic/community health roles** — relevant primarily where a city operates its own community health clinic (uncommon among this project's nine cities; not identified this session).
- **Emergency medical roles** — explicitly kept distinct per task instruction; EMS/paramedic work already appears in this project's fire mechanism map (FD04, EMS/paramedic credential scarcity) and should not be merged into a nurse_health comparison group.
- **Hospital nurses** — explicitly out of scope. Hospital nursing is overwhelmingly a private or quasi-public-authority employment relationship (not a general municipal-government bargaining unit) and is the dominant source of the "national nursing shortage" narrative; using hospital-nursing evidence to characterize this project's municipal comparison group would be a population mismatch, as the checkpoint memo already flagged.

### Current corpus status

Zero direct `nurse_health` rows. One hidden, unconfirmed candidate: `ma_wayland_other_2021`'s recognition clause names "nurses" among the mixed titles covered, but the underlying document has not been OCR'd beyond its cover page, so no nurse-specific title, wage, or duty language is currently readable from this project's own corpus.

### Massachusetts context

Municipal and school employees, including nurses, bargain under the ordinary M.G.L. c. 150E framework — the same statute already independently verified (four times, for teachers, DPW, clerical/admin, and library) to carry no JLMC-equivalent compulsory-arbitration backstop. School nurses specifically are very likely embedded in the school committee's own bargaining unit and budget process (the same Chapter 70/net-school-spending and Proposition 2½ channels already documented for teachers), rather than in general municipal government — a school-finance-channel question, not a JLMC-eligibility question. No source found this session (or in any prior session) suggests any nurse_health-specific carve-out from ordinary Chapter 150E; this project treats "no JLMC access" as a high-confidence structural extension of the same already-four-times-verified rule, not an independently re-verified fact.

### Bounded national context

A projected national RN shortage remains real but is now more precisely calibrated than a blanket "nursing crisis" headline: HRSA's most recent workforce projections describe roughly an 8% RN shortage by 2028 easing to about 3% by 2038 (108,960 FTE RNs), with the gap concentrated in nonmetropolitan areas (a projected 11% nonmetro shortage vs. 2% metro by 2038) — a geographic-concentration nuance directly relevant to whether any of this project's nine (all reasonably metro-adjacent Massachusetts) cities would even be expected to show acute nurse-supply strain. Hospital RN turnover (about 16.4% in 2024 per the NSI National Health Care Retention & RN Staffing Report) and BLS's projected need for 275,000+ additional nurses by 2030 are both hospital-sector-dominated figures and should not be read onto municipal/public-health nursing without a separate, distinct source.

### Upward wage-pressure mechanisms

- Credential/licensure (RN licensure is a real, state-administered barrier, though a much larger and more portable credential market than police/fire academy training or teacher licensure).
- Healthcare labor-market competition (a municipal nurse's outside option is a private hospital/clinic job, a materially different competing labor pool than DPW's construction-trades competition or clerical/admin's general office-work competition).
- Pandemic/public-health shocks (COVID-19 sharply and visibly raised public-health-nursing workload and, in some jurisdictions, hazard-pay/temporary-premium pay — a genuinely public-health-specific channel, distinct from hospital travel-nurse premium pay).
- Professionalization without a police/fire-style wage backstop (nursing is a credentialed profession with real licensure requirements, but — like library's MLS/MLIS finding — credentialing alone has not been shown, anywhere in this project's prior work, to guarantee a strong wage-bargaining backstop).

### Wage-restraint or alternate-translation mechanisms

- Gendered occupational valuation, explicitly flagged as a hypothesis requiring dedicated evidence, not an assumed mechanism — nursing is a heavily female-dominated occupation, the same comparable-worth caution already applied (and explicitly not upgraded past "weak evidence") to clerical/admin (CA13) and library (LB08).
- School-finance or health-department-budget channels: a school nurse's wage-setting sits inside the same Chapter 70/net-school-spending/Proposition 2½ framework as teachers; a health-department nurse's wage-setting sits inside the general municipal levy/budget process, with no nurse-specific floor or ceiling mechanism identified this session (unlike library's MBLC Municipal Appropriation Requirement).
- Service deferral/program cuts/clinic reductions — plausible but untested for any of this project's cities this session.
- Public salience that may spike in crises (a pandemic, a public-health emergency) but not persist — a genuinely distinct salience profile from police/fire's more evenly distributed, incident-driven salience.

### Comparison to other groups

Nurse_health most resembles library on the "real credential, uneven wage translation" axis (MLS/MLIS parallels RN licensure) and most resembles teachers on the "school-finance-channel-if-school-based" axis, while sharing DPW's/clerical-admin's confirmed absence of any JLMC-equivalent backstop. It differs from every group examined so far in having a genuinely crisis-episodic (not steady-state) salience profile and the most credible competing-private-sector-labor-market story of any non-safety group (a hospital job is a much closer substitute for a municipal nursing job than a private trucking job is for a DPW job).

### Claim/counterpoint/evidence-needed table

| claim | counterpoint | evidence needed |
| --- | --- | --- |
| Municipal nurses face real recruitment pressure from a competing hospital labor market | This project's cities are small-scale employers of at most a handful of nurses each; national hospital-sector shortage data does not describe this population | City-specific vacancy/turnover data for health-department or school-nurse positions (not available in current corpus) |
| Pandemic-era public-health demand created a lasting wage-setting precedent | COVID-era hazard/premium pay was often temporary and may not have converted into a permanent base-wage or classification change | Direct CBA or budget-document language showing whether any COVID-era premium became permanent |
| Nurse credentialing (RN licensure) functions like library's MLS/MLIS — real but unevenly rewarded | Not yet tested for any of this project's cities; the Wayland row's nurse content is not currently readable | An OCR pass of `ma_wayland_afscme_1_2_2020_2023.pdf` to read actual nurse-specific classification/pay language |

### Source targets

An OCR re-extraction of the already-collected `ma_wayland_afscme_1_2_2020_2023.pdf` (no new ingestion — the document is already in corpus) is the single best next step to resolve whether nurse-specific wage/classification language exists in this project's own corpus. Beyond that, any dedicated nurse_health acquisition would require identifying which, if any, of this project's remaining eight cities has a genuinely municipal (not school-embedded, not hospital-affiliated) public-health nursing bargaining unit — not attempted this session.

### Recommendation

**Include only as a specific subtype (municipal/public-health nurses, explicitly not hospital nurses), and only after the Wayland OCR re-read.** Do not treat nurse_health as a standalone acquisition priority ahead of that zero-cost step. See Section 7 for the full disposition.

## 4. Custodial / facilities / building maintenance

### Occupation/classification map

- **Custodians/janitors** — the core, already-confirmed-in-corpus category (Georgetown, Franklin, both currently coded `other`; Arlington, bundled inside `public_works`).
- **School custodians** — a school-committee-bargained subset; Georgetown's row is explicitly a "School Department" unit.
- **Municipal building maintenance / facilities maintenance** — broader than custodial (cleaning) work; includes skilled trades (HVAC, electrical, plumbing) — not separately confirmed in this project's corpus this session.
- **Grounds/building services** — plausibly overlaps with DPW's parks/grounds functions; not separately confirmed this session.
- **Contractors/vendors** — a plausible outsourcing alternative to any of the above; not investigated for any of this project's cities this session.
- **DPW overlap** — Arlington's confirmed "Labor Service (DPW, custodians)" bundling is the clearest documented instance of this overlap in this project's corpus.

### Current corpus status

Direct matches exist, but are currently mislabeled. `ma_georgetown_other_2020` and `ma_franklin_other_2022` are both explicitly, unambiguously custodial bargaining units per their own `total_comp_note` fields, coded `other` only because the controlled vocabulary has no `custodial`/`facilities` value — this is a schema gap, not a data-acquisition gap, exactly as the checkpoint memo (§9) already flagged. Arlington's `public_works` rows bundle custodians alongside DPW/clerical/administrative titles in one unit, a composition-fragmentation pattern directly analogous to the DPW classification-fragmentation mechanism (DP09) already confirmed for this project's DPW corpus generally.

### Massachusetts context

Both confirmed custodial units (Georgetown, Franklin) bargain under ordinary Chapter 150E; Georgetown's is explicitly school-committee-employed ("School Department"), placing it in the same school-finance channel as teachers, while Franklin's and Arlington's appear to be general-municipal units. No source found this or any prior session suggests any custodial/facilities-specific JLMC-style backstop; this is a high-confidence structural extension of the already-multiply-verified rule, not independently re-tested.

### Bounded national context

This session's bounded search found real Massachusetts examples of unionized school custodial staff (Winchester's SEIU Local 888 custodians; Everett's SEIU Local 888 custodial contract, FY2026 starting rate $31.46/hour) but no specific national or Massachusetts source on custodial outsourcing/contracting trends, skilled-trades scarcity for building maintenance, or pandemic-era cleaning-burden data — these remain genuinely open, not resolved, gaps (see the companion source-gap memo).

### Upward wage-pressure mechanisms

- Service essentiality but lower public salience — school/building custodial failures (an unclean building, a broken HVAC system) are real service issues but draw far less acute public attention than a safety incident, closely mirroring DPW's and clerical/admin's already-documented lower-salience findings.
- Building safety/cleanliness/health considerations, sharpened during COVID-19 (a genuinely new, dated pandemic-cleaning-burden channel not previously examined for any group in this project).
- School-opening constraints — a school cannot open if it is not clean/safe/heated, a real, dated, operationally-binding constraint structurally similar to (though less acute than) DPW's snow-removal-before-schools-open logic.
- Skilled-trades scarcity (HVAC/electrical/plumbing), a CDL-adjacent credentialing story parallel to DPW's mechanic/equipment-operator classification tiers — not yet confirmed present in any of this project's custodial rows specifically.

### Wage-restraint or alternate-translation mechanisms

- Outsourcing/contracting — a plausible, DPW-and-sanitation-style substitution channel; not confirmed for any of this project's cities this session.
- Classification/pay grades — the Arlington bundling pattern (custodians folded into a broader Labor Service classification alongside DPW/clerical/administrative titles) is directly analogous to DPW's already-confirmed classification-fragmentation mechanism (DP09).
- Shift work/overtime — plausible, untested this session.
- Maintenance backlog as service buffering — directly analogous to DPW's service-deferral mechanism (DP08/H21), untested this session for custodial-specific evidence.

### Comparison to other groups

Custodial/facilities most closely resembles DPW in structure (classification fragmentation, service-essentiality-but-lower-salience, plausible outsourcing) but with a lower credentialing/licensing profile than DPW's CDL/hoisting/water-operator tiers for at least the core custodial (as opposed to skilled-trades) function. It resembles clerical/admin and library on the lower-public-salience axis. Unlike nurse_health or dispatchers, it has no genuinely new institutional or crisis-salience wrinkle identified this session — its primary distinguishing feature for this project is that it is a **schema gap, not a source-acquisition gap**: this project already has two clean, already-collected, currently-mislabeled custodial CBAs sitting in its corpus.

### Claim/counterpoint/evidence-needed table

| claim | counterpoint | evidence needed |
| --- | --- | --- |
| Custodial work is a distinct, useful non-safety comparison group | It may simply replicate DPW's/clerical-admin's already-documented low-salience, classification-restrained findings without new mechanism variety | A direct re-read of the Georgetown and Franklin custodial CBAs' full text for wage schedule, classification, and any hazard/pandemic-cleaning language (not performed this session beyond the `total_comp_note` field) |
| Custodial/facilities work is frequently outsourced, restraining municipal wages | Not tested for any of this project's cities this session; the two confirmed rows are in-house, unionized municipal/school units, not contracted | A source-acquisition check of whether any of this project's nine cities contracts custodial services to a private vendor (not attempted this session) |

### Source targets

Reclassifying (not re-acquiring) `ma_georgetown_other_2020` and `ma_franklin_other_2022` under a proper controlled-vocabulary value is the highest-value, zero-new-ingestion next step, but requires a schema decision (adding a `custodial`/`facilities` value to `occupation_class`) before any CSV edit — explicitly a user/PI decision per the checkpoint memo, not something this memo authorizes. Beyond that, a full re-read of both already-collected documents' complete text (not performed this session) would be the natural next desk-research step.

### Recommendation

**Include, contingent on a schema decision.** This is the group with the lowest source-acquisition cost of the three (both target documents are already in corpus) but the clearest schema blocker (no controlled-vocabulary value exists yet). See Section 7.

## 5. Dispatchers / 911 telecommunicators

### Occupation/classification map

- **Police dispatchers / fire dispatchers / EMS dispatchers** — in many jurisdictions a single combined function (as Arlington's "Community Safety Dispatchers" title suggests) rather than three separate roles.
- **911 telecommunicators** — the general national/professional term for the same function, used in current federal reclassification advocacy.
- **Civilian dispatchers** — the key structural fact: dispatchers are typically non-sworn, civilian employees, even when embedded within or physically co-located with a police/fire operation.
- **Regional emergency communication centers (RECCs)** — a genuinely important Massachusetts-specific governance layer (see below), analogous in spirit to transit's regional-authority governance-distance finding.
- **Police/fire bargaining units versus separate civilian units** — this project's own corpus shows dispatchers bundled into a *public_works*-classified unit (Arlington), not a police- or fire-classified one — the opposite of what one might assume from "public-safety-adjacent" framing.
- **Transportation/DPW dispatchers** — explicitly kept distinct from 911/public-safety dispatch per task instruction; not identified in this project's corpus (Arlington's dispatchers are explicitly "Community Safety," i.e., public-safety-function dispatchers bundled inside a DPW-classified unit by bargaining-unit composition, not transportation dispatchers performing a DPW function).

### Current corpus status

**Direct, already-in-corpus, mechanism-rich text exists** — the strongest starting position of any of this session's three groups. Arlington's `public_works`-classified AFSCME Local 680 CBA (three cycles, 2015-2024) explicitly names "Community Safety Dispatchers" with a defined staffing complement (nine dispatchers plus a Lead Dispatcher), an explicit minimum-coverage rule (a full complement of two dispatchers at all times), and backfill/sick-call-in language — genuine 24/7-minimum-staffing mechanism text, already collected, requiring zero new ingestion to use. Wayland's `other`-coded row also names "dispatch" among its covered titles, though the underlying document has not been OCR'd beyond its cover page.

### Massachusetts context

Both identified dispatcher-bearing rows (Arlington, Wayland) are coded under ordinary municipal occupation classes (`public_works`, `other`), not `police` or `fire`, and their `binding_arbitration_statute` fields (per this project's already-established metadata-cleanup discipline) should be checked, not assumed, before drawing any JLMC-related conclusion — this memo did not independently re-verify Arlington's or Wayland's `binding_arbitration_statute` field content this session, and any future work should do so directly rather than assuming dispatchers share police/fire's JLMC eligibility merely because of their public-safety-adjacent function. **No source found this session suggests dispatchers are JLMC-eligible in Massachusetts**, and the strong prior (dispatchers are civilian AFSCME/municipal-general-unit employees, not sworn police/fire personnel) is that they follow the ordinary Chapter 150E route — but this project has not independently verified this for dispatchers the way it has for teachers, DPW, clerical/admin, and library, so it should be flagged as a genuinely new institutional question, not simply assumed by extension. A distinct, real Massachusetts institutional layer exists regardless of the arbitration-statute question: the **State 911 Department** operates a Development Grant, a Support and Incentive Grant, and a Training Grant program that funds regional emergency communication centers (RECCs) and defrays "Enhanced 911 Telecommunicator Personnel Costs" — a real, state-level funding/regionalization infrastructure layered on top of whatever bargaining regime applies to any specific city's dispatchers. Massachusetts also shows two concrete, dated examples of the "professionalization without full wage-power translation" mechanism: Boston Mayor Michelle Wu's 2023 executive order recognizing Boston 911 telecommunicators as Public Safety/First Responders (a symbolic/administrative recognition, not confirmed to carry an automatic wage or classification consequence), and 2019 Massachusetts legislative bills (S.1529, H.2366) to reclassify certified emergency telecommunicators from Group 1 to Group 2 of the state public retirement system — a genuine, concrete, pension-classification (not base-wage) lever distinct from anything else this project has documented for any occupation group.

### Bounded national context

A live, currently-unresolved national reclassification debate is directly relevant here: public safety telecommunicators are still classified under "Office and Administrative Support Occupations" in the federal Standard Occupational Classification system, not as protective-service workers, despite sustained advocacy (APCO International, NENA) and federal legislation (the "Enhancing First Response Act"/9-1-1 SAVES Act, passed by the U.S. Senate in 2025) that would reclassify dispatchers as "Protective Service Occupations." As of an October 2024 NCSL report, 25 states have enacted or adopted resolutions reclassifying telecommunicators as first responders or under another public-safety occupational category, while the federal Office of Management and Budget explicitly declined to reclassify the occupation in the 2018 SOC revision, stating directly that "the work performed is that of a dispatcher, not a first responder" — as sharp and explicit a national-level statement of the civilian/public-safety-adjacent boundary question as this project has found for any mechanism. This is precisely the kind of professionalization-without-automatic-wage-power and public-support-without-wage-translation pattern this project's task brief asks this memo to test.

### Upward wage-pressure mechanisms

- 24/7 minimum staffing — directly corpus-confirmed for Arlington (explicit minimum-coverage-of-two rule).
- Public-safety salience without sworn status — dispatchers sit at the exact safety/non-safety boundary this project's whole design depends on distinguishing, per the checkpoint memo's own framing (§9).
- Emotional stress/trauma exposure — a real, plausible mechanism (hearing emergency calls directly), not yet evidenced in this project's corpus text beyond the staffing-complement language already found.
- Recruitment/retention and overtime/staffing shortages — the minimum-coverage rule found in Arlington's text structurally guarantees an overtime/callback dynamic whenever the complement of nine falls below the two-dispatcher floor, directly analogous to DPW's and police/fire's already-documented overtime-staffing-spiral mechanism (XC03).
- Certification/training — Massachusetts's own 560 CMR 5.00 establishes certification requirements for "enhanced 911 telecommunicators" and governs emergency medical dispatch — a real, state-administered credentialing regime, not yet linked to any specific pay tier in this project's corpus.
- Regionalization — RECCs represent a genuine governance shift (multiple towns' dispatch consolidated into one center), directly parallel in structure to transit's regional-authority governance-distance finding, though for dispatchers the underlying employees may still be municipal (not necessarily privately contracted the way RTA transit operators are) — not independently confirmed this session.

### Wage-restraint or alternate-translation mechanisms

- Classification and pay equity with police/fire — the central, unresolved question: whether dispatchers' civilian status caps their pay well below sworn officers' despite comparable stress/24-7-coverage burdens, a genuine under-translation hypothesis this project has not yet tested with wage data.
- Possible under-translation of public-safety pressure into wages because of civilian status — precisely the federal SOC classification fight (dispatcher vs. "first responder") suggests this may be a real, nationally-recognized phenomenon, not merely a hypothesis unique to this project's cities.
- Bundling inside a non-safety-classified unit (Arlington's `public_works` coding) may itself be a wage-restraining administrative artifact — if dispatcher pay is negotiated as part of a broader DPW/clerical/administrative unit rather than its own bargaining unit, dispatcher-specific pressure may not translate into dispatcher-specific wage movement the way a standalone unit's bargaining might allow.

### Comparison to other groups

Dispatchers most closely resemble police/fire on operational mechanism (24/7 minimum staffing, overtime-spiral dynamics, emotional/stress exposure) but resemble non-safety groups (DPW, clerical/admin) on institutional status (civilian, likely Chapter 150E, likely no JLMC access, bundled into a general municipal unit rather than a sworn-officer unit). This dual character is exactly why the task brief treats them with extra care, and exactly why this memo does not simply fold them into either the safety or the non-safety comparison group without further institutional verification.

### Should dispatchers belong in non-safety comparison, public-safety-adjacent comparison, or excluded/deferred?

**Public-safety-adjacent — a distinct third category, not simply non-safety.** Dispatchers should not be treated as an ordinary non-safety comparison group (their operational profile is too close to police/fire's for that framing to be honest), and should not be treated as safety-equivalent either (their civilian status, likely Chapter 150E coverage, and the live national SOC-classification fight all point the other way). The most defensible framing is a distinct "public-safety-adjacent" category whose entire analytical value lies in testing whether public-safety-style operational pressure translates into public-safety-style wages *without* public-safety-style institutional backstops (JLMC access, sworn status) — a genuinely different test than any other group in this project offers.

### Claim/counterpoint/evidence-needed table

| claim | counterpoint | evidence needed |
| --- | --- | --- |
| Dispatchers face police/fire-style 24/7 minimum-staffing pressure | Corpus-confirmed for Arlington specifically; not yet shown to generalize to any other city's dispatchers | Wayland's OCR'd dispatch-specific text; other cities' dispatcher arrangements (not identified this session) |
| Dispatchers' civilian status caps wage translation of public-safety pressure | This is exactly the federal SOC reclassification debate's core dispute; not yet tested with this project's own wage data | Arlington's/Wayland's dispatcher-specific base-wage schedule compared with the same city's police/fire base wages, controlling for tenure/step |
| Massachusetts treats dispatchers as ordinary Chapter 150E, non-JLMC employees | Not independently verified this session for Arlington's or Wayland's specific `binding_arbitration_statute` field; assumed by extension from dispatchers' civilian status, not confirmed | Direct check of Arlington's and Wayland's `binding_arbitration_statute` field values and underlying arbitration-clause text |

### Source targets

Arlington's already-collected CBA text is the single richest, zero-cost dispatcher source in this project's corpus and should be re-read in full (not just the "Community Safety Dispatchers" excerpts found this session) for base-wage/step data specific to the dispatcher classification, compared against the same document's DPW and custodial classifications. Wayland's OCR re-extraction (shared with the nurse_health and custodial questions above) would be the second target. Massachusetts's 560 CMR 5.00 telecommunicator certification regulation and the State 911 Department's grant-program materials are additional, not-yet-read Massachusetts institutional sources.

### Recommendation

**Include as a public-safety-adjacent comparison, contingent on the Arlington re-read.** This is simultaneously the most conceptually valuable and the most classification-sensitive of the three groups. See Section 7.

## 6. Cross-group comparison among these three

**Most useful for the project:** dispatchers, by a clear margin. They test a genuinely new question (public-safety operational pressure without public-safety institutional backstops or sworn status) that no other group in this project's mechanism map currently tests, and they already have real, quotable, already-collected corpus text (Arlington) supporting that test.

**Easiest to source:** custodial/facilities. Two of the three groups' target documents (Georgetown, Franklin) are already fully collected, correctly retrievable by `full_text_path`, and unambiguously classified in their own metadata — the only blocker is a controlled-vocabulary schema decision, not any acquisition effort.

**Most design risk:** nurse_health. It has the thinnest corpus foothold (an unread, unOCR'd fragment inside a mixed-title recognition clause), the sharpest population-mismatch risk of any group this project has considered (national nursing-shortage data is overwhelmingly hospital-sector), and the least-developed Massachusetts institutional story of the three (no nurse-specific budget-floor or arbitration-related finding was identified this session, unlike library's MBLC mechanism or teachers' Chapter 70).

**Should be inspected next, if any:** the Arlington dispatcher re-read and the Wayland OCR pass, in that order — both are zero-new-ingestion, already-in-corpus tasks that would resolve genuine open questions for two (Wayland) or three (Wayland plus the standalone Arlington re-read) of this session's groups simultaneously.

## 7. Recommended treatment

- **nurse_health:** **defer.** Zero new source acquisition should be authorized ahead of the zero-cost Wayland OCR pass; even after that pass, this group's population-mismatch risk (hospital-nursing data does not describe this project's likely small, heterogeneous municipal/school nursing population) means it should not be prioritized ahead of dispatchers or custodial/facilities.
- **custodial/facilities:** **include, pending a schema decision.** The two already-collected, already-correctly-documented custodial CBAs (Georgetown, Franklin) are ready to be properly classified the moment the user/PI authorizes a new `custodial`/`facilities` controlled-vocabulary value; Arlington's bundled custodial content is a secondary, lower-priority target requiring its own job-description-level re-read.
- **dispatchers:** **include, as a public-safety-adjacent category, contingent on the Arlington re-read.** This is the highest-value group of the three, precisely because it is already partially evidenced in this project's own corpus and because it tests a genuinely novel mechanism question. It should not be merged into either the safety or non-safety comparison group without first re-verifying its institutional (arbitration-statute) status directly, per Section 5.

## 8. Recommended next step

Proceed to the all-group cross-audit and source-needs planning already scoped for this session (`all_groups_wage_mechanism_audit_2026-07-06.md`, `all_groups_source_needs_2026-07-06.csv`, `hypothesis_disposition_audit_2026-07-06.csv`), not to a new source-acquisition run. The two zero-cost, already-in-corpus re-reads identified above (Arlington dispatcher text; Wayland OCR pass) are the most concrete near-term follow-ups, but do not require a separate authorization decision the way genuinely new source acquisition would — they are re-reads of documents already in `corpus/`, in the same spirit as the Seekonk sanitation-language re-read performed in a prior session.
