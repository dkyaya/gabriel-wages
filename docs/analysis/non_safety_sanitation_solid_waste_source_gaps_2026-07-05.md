# Sanitation / Solid Waste Source Gap List

**Date:** 2026-07-05
**Scope:** desk-research and source-acquisition planning only. Lists the highest-value evidence gaps surfaced by `non_safety_sanitation_solid_waste_mechanism_scope_2026-07-05.md`. This project's corpus currently holds zero `sanitation` rows, so nearly every gap below is a source-acquisition question, not a further-review-of-already-collected-documents question — a materially different starting point than the DPW, clerical/admin, or library source-gap memos, all of which closed most of their gaps against already-collected corpus text. This is a punch list for future sessions, not a completed data build or an ingestion authorization.

**2026-07-06 update — city-service-structure scan completed.** `sanitation_city_service_structure_scan_2026-07-06.md` (with a companion `.csv`) closed gap 1 and gap 2 below for this project's own nine cities specifically. Finding: at least five of nine cities (Arlington, Boston, Franklin, Georgetown, Newton) show clear evidence of private-hauler contracting for residential collection — sanitation is unlikely to be observable in these cities' municipal CBAs at all, for structural reasons, not just an unexplored gap. Two cities (Seekonk, Worcester) remain promising leads for a genuinely municipal-staffed or DPW-bundled collection workforce; Somerville is a third, lower-confidence lead entangled with a broader, pre-existing project gap (Somerville has no non-safety comparison unit of any kind). Gaps 3-15 below remain open except where individually noted; see the new scan memo §7 for the specific unresolved questions it could not close.

For each gap: why it matters, likely source families, a feasibility tag (`desk_research_feasible`, `data_build_feasible`, `likely_hard`), and which dimension it speaks to (wage levels, wage growth, staffing supply, classification, public health essentiality, outsourcing, route coverage, mechanization, overtime, budget/fees, or service deferral).

## 1. Whether sanitation is municipal, contracted, regionalized, or mixed by city

**Why it matters:** this is the foundational, prior-to-everything-else question for sanitation specifically, unlike any other non-safety group this project has developed — before any wage mechanism can be tested, it must be established whether a given city even has a municipal sanitation workforce for this project's causal corpus (municipal CBAs) to observe at all, or whether the function is entirely contracted to a private hauler.

**Likely source families:** individual municipal trash-collection/DPW web pages (this session confirmed this is a reliable, if city-by-city, source — Dedham, Andover, Marshfield, and Brookline's pages all stated their arrangement directly); Massachusetts Department of Environmental Protection (MassDEP) solid-waste program materials, if they maintain any statewide inventory of municipal-vs-contracted collection arrangements (not verified this session).

**Feasibility:** `desk_research_feasible` on a city-by-city basis (this session's bounded search of four Massachusetts towns found this information directly and quickly on each town's own website); `likely_hard` for a comprehensive statewide inventory without a centralized MassDEP or similar dataset, which was not identified this session.

**Dimension:** staffing supply (foundational — determines whether any other dimension is even testable for a given city).

## 2. Whether any of this project's current nine cities directly employs sanitation/collection workers — CLOSED 2026-07-06

**Why it matters:** directly operationalizes gap 1 for this project's specific city set (Worcester, Boston, Somerville, Arlington, Newton, Georgetown, Seekonk, Franklin, Wayland). This project's own corpus already shows no sanitation-specific title in any of the seven `public_works` documents from five of these cities (Worcester, Arlington, Seekonk, Franklin, Wayland) — but this could reflect functional folding into a "Laborer" title (gap 10 below) rather than contracted-out service, and this session did not resolve which explanation applies to any specific city.

**Status:** closed in `sanitation_city_service_structure_scan_2026-07-06.md`. City-by-city bounded web research found: Arlington, Franklin, Georgetown, and Newton show clear private-hauler contracting (high confidence for Arlington/Franklin/Newton, medium for Georgetown); Boston's residential collection is contracted (Capitol Waste Services) though street cleaning remains municipal; Seekonk and Worcester remain the two best candidates for a genuinely municipal-staffed or DPW-bundled collection workforce (Seekonk's already-collected `public_works` CBA needs only a job-description re-read; Worcester's existing corpus row is clerical-only, so its field/operations DPW workforce is entirely unrepresented in this project's corpus); Wayland is ambiguous, leaning toward a resident-choice private-hauler model for curbside; Somerville remains the least resolved (a budget document references "a contractual relationship" but municipal-crew involvement was not ruled out).

**Remaining sub-gap:** whether Seekonk's town-employed DPW workers (if they perform collection at all) are distinguishable from a single town-contracted hauler was not resolved from public pages alone — a job-description-level re-read of the already-collected CBA is the recommended next step, not further web search.

**Likely source families:** each of these nine cities' own DPW/public-works or trash-collection web pages (confirmed this session as a reliable, if city-by-city, source); municipal budget books listing a solid-waste line item (municipal-employee payroll) versus a hauling-contract line item (contracted-service expense).

**Dimension:** staffing supply / classification.

## 3. Sanitation applicant/vacancy/turnover evidence

**Why it matters:** the direct staffing-strain measure already used for every other occupation group in this project's comparison, and the specific evidence needed to test whether the national CDL-driver retention crisis (§5, §10 of the mechanism memo) shows up at the municipal (not just industry-wide) level.

**Likely source families:** SWANA/NWRA industry-level reporting (already identified this session, national and industry-wide, not municipal-specific); municipal HR/civil-service application records (not reviewed); a future sanitation-inclusive CBA, if one is collected.

**Feasibility:** `desk_research_feasible` for the national industry-level snapshot (already closed this session, with the caveat that it should be read skeptically per the industry-association-source discipline already applied to DPW's CDL debate); `likely_hard` for municipal-specific vacancy/turnover data, since no centralized Massachusetts municipal sanitation-workforce dataset was identified this session.

**Dimension:** staffing supply.

## 4. Private-hauler wage competition, Massachusetts-specific

**Why it matters:** tests the `sanitation_contractor_substitution` hypothesis's upward-pressure reading directly — whether municipal sanitation wages (where a municipal workforce exists) actually track local private-hauling-industry wage levels, as opposed to simply asserting a shared labor market exists.

**Likely source families:** BLS/OEWS occupational wage data for refuse/recyclable-material-collector and truck-driver categories (source context only, not to be built into a panel per this project's standing hard boundary); private waste-hauling company job postings for Massachusetts markets (illustrative only, not systematic).

**Feasibility:** `likely_hard` within this project's current scope, since any real test would require the OEWS-adjacent descriptive baseline work explicitly out of bounds for desk-research sessions; flagged here as a future, not immediate, task, mirroring the identical caution already applied to DPW's private-sector wage-tracking gap.

**Dimension:** wage levels / wage growth.

## 5. Contractor/substitution arrangements, Massachusetts-specific — PARTIALLY CLOSED 2026-07-05

**Why it matters:** tests the `sanitation_contractor_substitution` hypothesis directly — how common private-hauler contracting is among Massachusetts municipalities generally, and specifically for this project's own nine cities.

**Status:** partially closed this session at the illustrative level — four Massachusetts towns (Dedham, Andover, Marshfield, Brookline) were confirmed to use private-hauler arrangements for some or all of their residential collection service, via each town's own public web page. This establishes the arrangement is real and not rare in Massachusetts, but these four towns are not part of this project's current nine-city set.

**Remaining sub-gap:** whether any of this project's own nine cities uses a comparable arrangement (see gap 2), and whether Massachusetts prevailing-wage law covers routine solid-waste hauling service contracts specifically (the DPW mechanism memo already flags this as uncertain even for DPW-type service contracts generally, and this session did not independently verify it for hauling contracts specifically).

**Dimension:** outsourcing.

## 6. CDL/equipment skill requirements, Massachusetts-specific

**Why it matters:** this project's own DPW corpus already documents CDL-to-classification linkage in detail (Arlington's MEO grades, Franklin's stipend schedule) for general DPW driving roles; whether a comparable, sanitation-specific CDL/equipment-operator classification tier exists in any Massachusetts municipal sanitation or DPW-bundled-sanitation unit was not established this session.

**Likely source families:** a future sanitation-inclusive DPW CBA, if collected; Massachusetts hoisting-license and CDL administrative pages (already generally reviewed in the DPW mechanism work, not sanitation-specific).

**Feasibility:** `data_build_feasible` only once a relevant contract is identified and collected; not `desk_research_feasible` beyond the general (non-sanitation-specific) CDL/hoisting-license mechanics already documented for DPW.

**Dimension:** classification.

## 7. Overtime/holiday/schedule evidence, Massachusetts-specific

**Why it matters:** tests whether sanitation's route-coverage and holiday-schedule pressures (a route falling on a holiday typically requires a schedule shift for the whole week, a distinctive scheduling feature of collection work not shared by DPW's more emergency-triggered overtime) show up as a distinct contractual mechanism.

**Likely source families:** a future sanitation-inclusive CBA, if collected; municipal solid-waste annual reports.

**Feasibility:** `likely_hard` without a collected contract; `data_build_feasible` once one exists.

**Dimension:** overtime.

## 8. Route restructuring/mechanization evidence, Massachusetts-specific — PARTIALLY CLOSED 2026-07-05

**Why it matters:** tests the `sanitation_mechanization_route_restructuring` hypothesis directly for Massachusetts specifically, as opposed to the general national trend already documented.

**Status:** partially closed this session — the Town of Andover is confirmed, via its own municipal web page, to be requiring automated pickup and town-issued carts as part of a new hauling contract effective 2025, a direct Massachusetts example of the national mechanization trend already documented.

**Remaining sub-gap:** whether any of this project's own nine cities has undergone or is planning a comparable transition, and — the more analytically important remaining question — whether any documented transition shows a per-worker wage effect distinct from the headcount effect (per the main memo §6/§11's explicit caution that these are not the same prediction).

**Dimension:** mechanization.

## 9. Service frequency changes/missed pickup evidence, Massachusetts-specific

**Why it matters:** tests the `sanitation_mechanization_route_restructuring`-adjacent (folded) service-frequency-buffering hypothesis — whether any Massachusetts municipality has reduced collection frequency in response to budget or staffing pressure, and whether that generated a measurable public/political response (the key comparison point distinguishing sanitation's buffering channel from library's or DPW's more diffuse analogs).

**Likely source families:** municipal solid-waste annual reports; local news coverage of a specific frequency-reduction decision (illustrative only, not systematic proof); town meeting/select-board minutes.

**Feasibility:** `likely_hard` for a systematic multi-city series; `desk_research_feasible` only as an illustrative spot-check if a specific Massachusetts municipality is targeted, consistent with this project's standing caution against treating local news as broad proof.

**Dimension:** service deferral.

## 10. Injury/hazard evidence, Massachusetts-specific

**Why it matters:** the national fatal-injury-rate finding (§5, §10 of the mechanism memo — refuse/recycling collection now reportedly exceeding police's own fatal-injury rate) is the single most quantitatively striking finding in this scan, but it is national data; no Massachusetts-specific injury, workers'-compensation, or disability-retirement data for sanitation workers was reviewed this session.

**Likely source families:** Massachusetts Department of Labor Standards or Department of Industrial Accidents workers'-compensation data by occupation, if available at that granularity (not reviewed this session); a future sanitation-inclusive CBA, for any hazard-pay or safety-equipment clause.

**Feasibility:** `likely_hard` for occupation-specific Massachusetts injury data at the granularity needed; `data_build_feasible` for hazard-pay contract language once a relevant CBA is collected.

**Dimension:** wage levels (hazard-pay test) / staffing supply (injury-driven attrition).

## 11. Classification/pay-grade structures — the central open question for this occupation group

**Why it matters:** this is the most consequential remaining gap for understanding this project's own corpus specifically — whether sanitation duties, where they exist as a municipal function at all in this project's current cities, are (a) organized as a distinct classification/title within an existing `public_works` unit, (b) folded into a general "Laborer" classification with no distinct title (this project's own corpus is consistent with, but does not confirm, this explanation for its current five DPW-collecting cities), or (c) simply absent because the function is contracted out entirely (gap 1/2). This project's current corpus cannot distinguish between (b) and (c) without new source acquisition.

**Likely source families:** the five already-collected `public_works` CBAs' own classification/salary-grade schedules (already reviewed in the dedicated DPW corpus-scan session, which found no sanitation-specific title, but did not specifically test whether "Laborer" duties include collection work as a matter of job description rather than title); a future sanitation-specific or sanitation-explicit DPW CBA.

**Feasibility:** `data_build_feasible` for a closer re-read of the five already-collected `public_works` CBAs' job-description language specifically (not the classification-title language already reviewed), to test explanation (b) directly without new ingestion; `likely_hard` for explanation (c) without a municipal budget-line-item review per city (gap 2).

**Dimension:** classification.

## 12. Whether sanitation is bundled into DPW CBAs — see gap 11 above; treated as the same question

This gap is the same question as gap 11, restated in the terms the task brief uses; see gap 11 for the full discussion. Not treated as a separate, independent gap, to avoid double-counting the same open question.

## 13. Municipal solid waste budget/fee structures, Massachusetts-specific

**Why it matters:** tests whether a general-fund, enterprise-fund, or direct-fee funding structure (per the main memo §6) is associated with different sanitation staffing or wage outcomes — a structurally analogous question to DPW's water/sewer enterprise-fund distinction, but not yet examined for sanitation specifically.

**Likely source families:** municipal budget books; MassDEP solid-waste program materials, if they track funding-structure data across municipalities (not verified this session).

**Feasibility:** `data_build_feasible` for this project's specific cities if their budget books distinguish a solid-waste line item's funding source; `likely_hard` for a systematic multi-city Massachusetts series.

**Dimension:** budget/fees.

## 14. Massachusetts examples vs. national context

**Why it matters:** this session relied on a genuinely small number of illustrative Massachusetts examples (four towns for the contractor-substitution finding, plus a handful of consolidated-DPW/sanitation-division examples) alongside substantial national trade-press and academic context (BLS-derived fatal-injury data, SWANA/NWRA workforce reporting, academic privatization-cost literature). Future work should keep these explicitly distinguished, consistent with the discipline already applied in the teacher, DPW, clerical/admin, and library memos — and should be honest that this session's Massachusetts evidence base is thinner, proportionally, than any of those four prior sessions' Massachusetts evidence bases, precisely because no sanitation-specific Massachusetts contract or dedicated institutional source (comparable to the MMA Select Board Handbook's direct naming of "clerical and library employees") was identified this session naming sanitation workers specifically.

**Likely source families:** individual Massachusetts city/town DPW and solid-waste web pages (already a confirmed, reliable, if city-by-city, source this session); MassDEP solid-waste program materials for any statewide inventory; Massachusetts Municipal Association materials on consolidated-DPW practice (already partially reviewed this session).

**Feasibility:** `data_build_feasible` for a small number of additional illustrative Massachusetts examples via further city-by-city web review; explicitly not `desk_research_feasible` at a comprehensive statewide level, consistent with this session's scope boundary against comprehensive statewide coverage.

## 15. Massachusetts sanitation bargaining impasse-process verification

**Why it matters:** tests whether Massachusetts sanitation workers, where directly employed by a municipality, follow the ordinary Chapter 150E Section 9 route with no JLMC-equivalent backstop, mirroring the question already independently resolved four times (teachers, DPW, clerical/admin, library).

**Status:** treated in the main memo (§9) as a high-confidence direct extension of the already-four-times-verified JLMC eligibility rule (police and fire only, no essential-service or hazard-based extension identified in any of the four prior institutional-verification sessions), rather than as an independently re-verified finding requiring fresh legal research. No source encountered in this session's bounded research contradicts that scope or suggests a sanitation-specific exception.

**Remaining sub-gap:** a dedicated, sanitation-specific institutional-verification session (mirroring the standalone memos already produced for teachers and DPW) was not performed and is not recommended as a near-term priority, since this session's bounded research found no basis to expect a different answer than the extension already stated — a dedicated session would be confirmatory, not discovery-oriented, unless new evidence emerges suggesting otherwise.
