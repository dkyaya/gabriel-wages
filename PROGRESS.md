# Progress Log

Reverse-chronological session log. Newest entry on top. Records **decisions, surprises, and next steps** — not keystroke-level changes (git has those). Pair each entry with the git commits from that session.

Convention per entry: what we did, decisions made (and why), surprises/breakage, corpus snapshot (from `python ingest/audit_coverage.py`), next steps.

---

## 2026-07-05 - DPW existing-corpus scan and Massachusetts DPW impasse context verified

**Did**
- Confirmed the prior DPW mechanism session's changes (`3addd14`, "Refine DPW public works wage mechanisms") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_existing_corpus_scan_2026-07-04.md`
  - `docs/analysis/ma_dpw_bargaining_impasse_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md` (light edit: closed gap items 9, 11, 12 with verified findings)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added a second DPW update note confirming both open items from the prior session are now resolved)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edit to H6 `arbitration_or_impasse_backstop` only, adding the DPW-specific institutional and corpus corroboration alongside the existing teacher-specific one; no new rows added)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Closed the two immediate DPW uncertainties flagged at the end of the prior DPW mechanism session: (1) whether Massachusetts DPW/public-works bargaining has any special JLMC-like backstop, and (2) whether this project's already-collected `public_works` CBAs actually contain the classification, licensing, overtime/emergency, and contractor-substitution language the DPW mechanism map hypothesizes.
- Reviewed `data/contracts.csv` (read-only) to identify all seven `public_works` occupation-class rows across five cities (Worcester, Arlington x3 cycles, Seekonk, Franklin, Wayland), confirmed all seven corpus files exist on disk, and read their content (using the project's existing `pdftotext` extraction for six files, plus an ad hoc, read-only `tesseract` OCR pass for two Wayland files that had no extractable text in their stored form). No files were added to `corpus/` and no rows were added to or edited in `data/contracts.csv`.
- Verified via Mass.gov DLR/JLMC pages and M.G.L. c. 150E that JLMC eligibility is limited to police and fire, with no public-works-specific backstop, and cross-confirmed this directly from the project's own corpus: every `public_works` row's `binding_arbitration_statute` field cites MA G.L. c. 150E (never the JLMC statute used by every police/fire row), and every arbitration clause found in that corpus is grievance/discipline-scoped, not interest-arbitration-scoped.

**Decisions and why**
- Ran ad hoc, session-local OCR (via `pdftoppm`/`tesseract`) on two image-only Wayland PDFs purely to make their already-collected content legible for this review, since the stored corpus files had no extractable text; the OCR output was not written back into `corpus/` or `data/contracts.csv`, consistent with the "review, not ingestion" scope of this session.
- Flagged a precise, corpus-level observation rather than a data correction: `data/contracts.csv`'s `comparability_clause_flag` is set to `1` for the two fully-readable Arlington `public_works` rows, but the flagged snippet in each case is a health-insurance/workers'-compensation "comparable" usage, not peer-jurisdiction wage comparability language — noted as an observation about how to read existing metadata, not acted on as a correction, since this session does not modify `data/contracts.csv`.
- Made only one small, targeted hypothesis-matrix edit (H6) rather than adding new rows or editing multiple DPW rows, consistent with the standing preference to improve the existing map with small edits.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any new document.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The existing corpus was substantially richer than expected on credential-to-pay linkage (detailed biweekly license-stipend schedules in Franklin; CDL-class-tied classification grades in Arlington) and on contractor-substitution language (Franklin's two outsourcing side letters, including a clause tying contractor mobilization during snow events to an in-house overtime-premium trigger), while genuinely absent on peer-community wage comparability and explicit recruitment/retention framing language across every document reviewed.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made. Prior DPW mechanism changes (`3addd14`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Move to the clerical/admin comparison group per `non_safety_comparison_roadmap_2026-07-04.md`, since both DPW uncertainties flagged at the end of the prior session are now resolved.
2. If a DPW-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in `non_safety_dpw_existing_corpus_scan_2026-07-04.md` Section 6, and treat peer-comparability and recruitment/retention framing as requiring new source acquisition rather than further review of already-collected documents.
3. Continue holding off on any GABRIEL/model run, OEWS/municipal descriptive baseline build, or ingestion until the clerical/admin comparison group is at least scoped.

## 2026-07-04 - DPW / public works wage mechanism refinement developed

**Did**
- Confirmed the prior non-safety teacher mechanism session (`efbfb31`) and the Massachusetts teacher institutional clarification session (`e409824`) were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_public_works_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added a DPW findings update note; roadmap not rewritten)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added 5 new rows H18-H22: `dpw_operational_essentiality`, `dpw_cdl_equipment_operator_scarcity`, `dpw_contractor_substitution`, `dpw_service_deferral`, `dpw_classification_fragmentation`; lightly refined H4 and H7 counterpoint fields to fold in DPW's overtime/emergency-response and public-salience nuances)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Developed public works/DPW as the second non-safety comparison group per the existing roadmap: the strongest *operational* (as opposed to teachers' credentialing/salience) comparison to police/fire, since DPW shares physical risk, licensure gating, and short-notice emergency response with public safety.
- Used bounded web search across Massachusetts-specific sources (Mass.gov hoisting-license and prevailing-wage pages, Mass.gov salary/CBA guides) and national sources (BLS Monthly Labor Review on truck-driver labor markets, national/NEIWPCC water-workforce reporting, APWA workforce materials, municipal snow-removal risk-management guidance), keeping the two source types explicitly distinguished throughout the memo rather than overgeneralizing from national context to Massachusetts.

**Decisions and why**
- Treated DPW as a multi-occupation category (laborers, equipment operators, CDL drivers, water/wastewater operators, mechanics, foremen) throughout, mirroring the teacher composition-effect discipline, rather than a single homogeneous "DPW wage" concept.
- Found and foregrounded a genuine counterargument to the CDL-scarcity mechanism: BLS's own 2019 Monthly Labor Review analysis found no evidence of a secular truck-driver shortage, with real driver wages up only ~1.1% since 2010 — a pattern inconsistent with chronic scarcity and more consistent with a retention/wage-framing problem that industry associations have called a "shortage" since the late 1980s. Applied the same skepticism to APWA's industry-association workforce-shortage framing.
- Identified water/wastewater operator certification, not CDL, as the strongest genuine DPW scarce-credential case, based on national and New England-regional (NEIWPCC) retirement-wave evidence.
- Surfaced a specific, checkable Massachusetts institutional wrinkle for the contractor-substitution mechanism: Massachusetts prevailing wage law ties public-construction contractor wages to locally collectively bargained rates, meaning contracting out DPW-type work does not simply undercut the wage paid for that specific work the way outsourcing might without such a law (though routine service contracts may not always be covered).
- Added only 5 new hypothesis-matrix rows and folded 2 more (DPW overtime/emergency response into H4; DPW public salience into H7) into existing-row refinements, consistent with the standing preference to improve the existing map over proliferating new rows.
- Kept the roadmap-memo edit light (one update note under the existing DPW section) rather than rewriting it, per this session's explicit instruction.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The CDL-shortage counterargument was a genuinely useful surprise: national industry reporting frames a large truck-driver deficit, but the authoritative BLS labor-economics analysis reaches the opposite conclusion, which is a sharper and more direct illustration of the project's "do not assume shortages automatically produce wage increases" discipline than anticipated going into this session.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made. Prior teacher mechanism (`efbfb31`) and Massachusetts teacher institutional (`e409824`) changes were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Review this project's already-collected `public_works` occupation-class CBAs for classification/pay-grade structure, credential-tied premiums, and comparator-district language, without new ingestion.
2. Verify whether Massachusetts DPW/public-works bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers (not directly re-verified for public works this session).
3. Move to the next non-safety comparison group (clerical/admin) per `non_safety_comparison_roadmap_2026-07-04.md`, only after the DPW source gaps above are addressed.

## 2026-07-04 - Massachusetts teacher bargaining and school finance institutional context verified

**Did**
- Confirmed the prior non-safety teacher mechanism session's changes were already committed (`efbfb31`, "Refine non-safety teacher wage mechanisms"), with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/ma_teacher_bargaining_school_finance_institutional_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md` (closed gap item 13 with the verified finding; light edit only)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (added a short update note pointing to the new institutional memo; light edit only)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined H5, H6, H9 counterpoint/signal/confound fields with verified institutional facts; no new rows added)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Used bounded web search of primary/near-primary Massachusetts sources (DESE Chapter 70 program pages, Mass.gov Department of Labor Relations impasse/JLMC pages, Massachusetts General Laws Chapter 150E Section 9) to verify the two institutional claims flagged as unverified in the prior teacher mechanism session.

**Decisions and why**
- Verified, rather than assumed, that Massachusetts teacher bargaining under M.G.L. c. 150E Section 9 has only mediation plus advisory (non-binding) factfinding, after which the school committee may unilaterally implement its last, best offer; a voluntary interest-arbitration route exists on paper but requires mutual agreement and school-committee authorization and is not typical in practice, per Mass.gov's own guidance that non-police/fire bargaining has "no arbitration process." Framed this precisely as a compulsory-(JLMC)-vs-voluntary-(Chapter 150E) institutional-design difference, not a has-backstop-vs-has-no-process-at-all difference, since the earlier hedge risked overstating the contrast.
- Verified the Chapter 70/school-finance mechanics: foundation budget, required local contribution (capped at 82.5% of foundation budget locally), net school spending as their sum, and the two-sided constraint this creates for schools (a state-mandated spending floor plus the same Proposition 2 1/2 levy-limit ceiling shared by other municipal departments) that most other municipal departments, including police/fire, do not have on the floor side.
- Made only small, targeted edits to hypothesis-matrix rows H5, H6, and H9 rather than adding new rows, consistent with the standing preference to refine the existing map; no hypothesis needed to be added or removed based on this session's findings.
- Kept source-gap and roadmap memo edits light (closing one gap item, adding one update note) rather than rewriting them, per this session's explicit instruction.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The verified institutional facts were more precise than the prior session's hedged framing anticipated: teachers are not literally barred from all arbitration (a narrow voluntary route exists), which required a careful correction rather than a simple confirmation of the original hypothesis.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made. Prior teacher mechanism changes were already committed (`efbfb31`) excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Cross-reference the new institutional memo from the existing PI-facing synthesis memo (`police_fire_wage_mechanism_synthesis_for_pi_2026-07-03.md`), so the PI-facing material states the compulsory-vs-voluntary arbitration distinction and Chapter 70 floor/ceiling structure as verified facts.
2. Move to the public works/DPW comparison group per `non_safety_comparison_roadmap_2026-07-04.md`, checking specifically whether DPW bargaining follows the same general Chapter 150E Section 9 process as teachers (neither has JLMC access).
3. Continue holding off on any GABRIEL/model run, OEWS/DESE build, or ingestion until source-gap and institutional work across teachers and the next comparison groups is further along.

## 2026-07-04 - Non-safety wage mechanism refinement started with teachers

**Did**
- Created:
  - `docs/analysis/non_safety_teacher_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md`
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added 5 new rows H13-H17: `teacher_supply_pressure`, `teacher_shortage_buffering`, `teacher_composition_effect`, `teacher_salary_schedule_rigidity`, `non_safety_wage_restraint`; lightly refined H5 and H9 counterpoint fields to fold in `teacher_peer_district_comparability` and `school_budget_constraint`)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Developed the "other side" of the police/fire wage-gap comparison for the first time: rather than only asking why safety wages might rise, this session asked why non-safety wages (starting with teachers) might be restrained even under comparable staffing strain.
- Used bounded web search (NCES/IES School Pulse Panel, Learning Policy Institute, NCTQ, Massachusetts DESE, Mass.gov Proposition 2 1/2 primer) to ground the teacher-supply, salary-schedule, and budget-constraint sections in real, cited sources rather than analyst judgment alone; flagged the two claims not directly verified this session (Chapter 70 state-aid mechanics; whether Massachusetts teacher bargaining lacks binding wage arbitration) explicitly as unverified and routed them to the new source-gap memo.
- Set up, but did not deeply research, the next two non-safety comparison groups (public works/DPW, then clerical/admin) in a sequencing roadmap, with brief notes on later groups (sanitation, facilities/custodial, libraries/parks, transit, nurses/health).

**Decisions and why**
- Started the non-safety side with teachers specifically because they share the most features with the safety side (credentialing, unionization, political salience, public esteem), making them the hardest and therefore most informative test case, rather than starting with a weaker comparison group.
- Kept paraprofessionals/teacher assistants explicitly separate from teachers throughout, per their distinct BLS occupational classification, and flagged this as a discipline requirement for any future extraction.
- Did not assume teacher shortages automatically translate into wage growth; instead developed a specific structural asymmetry (teacher-side buffering tends toward cheaper substitute labor or degraded service, while police/fire overtime buffering directly raises realized pay to existing staff) as a candidate explanation for muted non-safety wage translation, with an explicit counterargument (class-size-overage stipends can convert teacher buffering into a wage-adjacent cost).
- Added only 5 new hypothesis-matrix rows and folded 2 more into refinements of existing rows (H5, H9) rather than adding all 8 hypotheses discussed in the memo as separate rows, consistent with the standing instruction to prefer improving the existing map over proliferating new rows.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- Bounded web search surfaced a genuinely useful quantitative base (e.g., 74% of U.S. public schools reported difficulty filling at least one teaching vacancy entering 2024-25; roughly 3 in 4 sampled districts already offer some hard-to-fill differentiated pay) that sharpened several hypotheses beyond what analyst judgment alone would have supported.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made.**

**Next steps**
1. Verify the two claims flagged as unverified this session: Massachusetts's Chapter 70 state-aid formula mechanics, and whether Massachusetts teacher bargaining under M.G.L. c. 150E lacks any binding wage-arbitration backstop (per the teacher source-gap memo, item 13).
2. Review this project's existing city CBAs for teacher salary-schedule structure, hard-to-fill stipend/MOU language, and comparator-district language, since teacher units may already be present in the corpus for some cities.
3. Move to the next non-safety comparison group (public works/DPW) per `non_safety_comparison_roadmap_2026-07-04.md`, only after the teacher source gaps above are addressed.

## 2026-07-03 - Police/fire workforce context refinement and source-gap list created

**Did**
- Created:
  - `docs/analysis/police_fire_workforce_context_refinement_2026-07-03.md`
  - `docs/analysis/police_fire_workforce_context_source_gaps_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined rows H2, H6, H11 only; no new rows added)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Deepened the police/fire workforce mechanism map on four fronts the PI flagged: police recruitment/retention/morale and disentangling COVID-era disruption from George Floyd/BLM-driven scrutiny; firefighter wage pressure vs. public esteem and the career/volunteer distinction; non-safety counterexamples (nursing, transit, sanitation) with an explicit statement of what plausibly still differs for public safety; and the interest-vs-grievance arbitration distinction plus the evidentiary logic for testing split-the-difference vs. criteria-applying arbitrator behavior.
- This was a context-building/hypothesis-refinement session only, framed explicitly as bounded desk research.

**Decisions and why**
- Treated claims not already backed by a citation in the existing mechanism memo/bibliography as "background/analyst judgment, not yet source-verified" rather than inventing a citation, and routed those flagged claims into the new source-gap list for later verification.
- Refined existing hypothesis-matrix rows (H2 post-2020 climate, H6 arbitration backstop, H11 volunteer-to-career transition) rather than adding new hypothesis rows, per the instruction to prefer revising over expanding the matrix.
- Explicitly separated the George Floyd/BLM legitimacy channel from COVID-era labor disruption, pension-vintage retirement timing, and general 2021-2023 labor-market churn as four distinct, separately-testable channels, rather than treating any post-2020 staffing mention as legitimacy-channel evidence.
- Framed volunteer-to-career fire transition pressure as a three-channel, lagged transmission mechanism (combination-department conversion, overtime/minimum-staffing substitution, full professionalization) rather than a direct driver of existing career-CBA base wages.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session.**

**Next steps**
1. Close the highest-value source gaps first: a direct (non-AP-summary) PERF/IACP staffing-survey citation with a multi-year applicant trend, an NFPA/FPRF or NVFC citation on volunteer-firefighter headcount trends, and one or two arbitration-behavior sources (e.g., Farber/Bazerman final-offer-arbitration literature) that speak directly to the split-the-difference-vs-criteria debate.
2. Only after that source base is stronger, revisit which sharpened hypotheses are worth a dedicated GABRIEL attribute.
3. Keep the OEWS/ASPEP descriptive wage-trend baseline (already planned in `police_fire_wage_trend_baseline_implementation_plan_2026-07-03.md`) as the next data-build step, separate from this mechanism-refinement lane.

## 2026-07-03 - OEWS/ASPEP descriptive wage-trend baseline plan prepared

**Did**
- Created:
  - `docs/analysis/police_fire_wage_trend_baseline_implementation_plan_2026-07-03.md`
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv`
  - `docs/analysis/police_fire_wage_trend_baseline_note_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Confirmed the prior PI-facing mechanism synthesis commit was already in place, so no pre-work commit action was needed beyond leaving `tmp/` uncommitted.
- Built the next-step descriptive baseline plan around exact official OEWS and ASPEP entry points, including BLS annual tables, the Massachusetts state page, the Boston-Cambridge-Newton metro listing, ASPEP table IDs, the ASPEP datasets page, and the individual-unit-file route.

**Decisions and why**
- Kept the baseline explicitly descriptive and occupation-level because OEWS/ASPEP cannot recover bargaining-unit contract wages.
- Used national, Massachusetts, and Boston-Cambridge-Newton as the required first-pass geographies because they align with the project's current state focus while keeping the first build manageable.
- Chose a compact set of occupation mappings that are relatively interpretable in OEWS: police, firefighters, teachers, clerical/admin, maintenance/public works proxy, sanitation, and transit.
- Treated `public_works` and `clerical_admin` as proxy occupations rather than pretending OEWS titles perfectly match municipal bargaining units.
- Included the national industry-specific/by-ownership OEWS file as a public/private mix sensitivity check, while noting that it does not solve the state/metro ownership problem.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production corpus changes.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Next steps**
1. Implement the first OEWS descriptive panel for the selected occupations at national, Massachusetts, and Boston-Cambridge-Newton scales.
2. Pull the parallel ASPEP function-based context tables and decide which function codes best approximate police, fire, education, transit, and public-works-adjacent services.
3. Keep any later state expansion or ownership/public-sector refinement as a second-pass extension after the first baseline is stable.

## 2026-07-03 - PI-facing mechanism synthesis and source-QC pass completed

**Did**
- Created:
  - `docs/analysis/police_fire_wage_mechanism_synthesis_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Audited the mechanism bibliography for source-year and access-date ambiguity.
- Flagged which sources are authoritative, which are institutional-context sources, and which are illustrative secondary sources.
- Revised the mechanism memo lightly to reduce overclaiming and sharpen the evidence-needed framing.
- Added a short PI-facing synthesis memo that reframes comparability as one candidate mechanism inside a broader mechanism map.

**Decisions and why**
- Kept the source audit inside the existing CSV rather than spawning a separate QC appendix, so citation cautions now travel with the bibliography itself.
- Treated the AP summary of the PERF staffing survey as illustrative rather than authoritative until replaced by the underlying PERF release.
- Flagged BLS/Census landing-page citations as usable for planning but not as final table-level citations, because the page-year versus underlying-data-year distinction could confuse a PI-facing memo.
- Kept the synthesis short and conceptual rather than adding new evidence pulls, because the requested task was QC and framing rather than new empirical research.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Next steps**
1. Replace illustrative or indirect citations in the mechanism bibliography with direct primary artifacts before any more formal external circulation.
2. Build the first descriptive OEWS/ASPEP baseline.
3. Keep broader-state snippet work in a small mechanism-discovery lane before any new GABRIEL attribute run.

## 2026-07-03 - Broader police/fire wage mechanism memo and data-plan package created

**Did**
- Created:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_trend_data_plan_2026-07-02.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Built a broader mechanism-context memo that steps back from the current comparability/arbitration implementation lane and maps competing police/fire wage mechanisms, counterarguments, and evidence needs.
- Kept the work strictly outside ingestion and outside live GABRIEL/model execution.

**Decisions and why**
- Treated recruitment pressure, training burden, vacancies/PTO, and arbitration as candidate mechanisms rather than public-safety-specific truths.
- Centered a claim/counterpoint/evidence structure so the memo would not drift into confirmation of the current comparability story.
- Used Massachusetts/JLMC as one institutional case while explicitly keeping room for broader-state mechanism snippets.
- Kept the source bibliography curated rather than exhaustive so the package stays usable as a planning memo.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed in memo/planning space rather than corpus modification.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Next steps**
1. Stay in mechanism-development mode before any broader GABRIEL web-search scaling.
2. Pull a first descriptive OEWS/ASPEP trend baseline for police, fire, and selected non-safety comparison occupations.
3. Add a small broader-state public snippet set to test whether institutional mechanisms differ outside Massachusetts/JLMC.

## 2026-07-01 - Thursday package updated around Boston bounded built-in GABRIEL web success

**Did**
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Integrated the successful Boston graduated built-in web retry into the Thursday report package.
- Prepared a temporary ChatGPT handoff bundle for review.

**Decisions and why**
- Reframed the live finding as bounded success rather than blocked because the Boston graduated retry succeeded on attempt 2 and returned a preserved BPS source URL.
- Kept the reporting message narrow: built-in web source discovery works when bounded, while larger structured extraction still needs one-dimension-at-a-time tuning.
- Did not run additional live web-search or GABRIEL calls in this session because the task was report integration and handoff packaging only.
- Did not create charts from the live retry outputs because `n=1` does not justify numeric plotting.

**Surprises/breakage**
- No new runtime breakage in this session.
- Validation and coverage audit remained unchanged from earlier runs, confirming the session stayed outside ingestion and production data paths.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Thursday message**
```text
Built-in GABRIEL web mode works on a bounded Boston source-discovery query through the Harvard proxy, but larger structured extraction prompts need incremental tuning for stability.
```

**Next steps**
1. Keep the next technical run Boston-only.
2. Tune structured extraction one dimension at a time: prompt size, output cap, source metadata handling, and timeout behavior.
3. Do not broaden to a five-city live pilot, all-32 v10, or ingestion from this state.

## 2026-07-01 - Boston graduated built-in GABRIEL web retry succeeded on attempt 2

**Did**
- Created and ran:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py`
- Created graduated retry artifacts:
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_graduated_retry_2026-07-01/`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_sources_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_extractions_2026-07-01.csv`
  - `docs/analysis/gabriel_builtin_web_boston_graduated_retry_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Ran only Boston and stopped after the first useful successful result.
- Used `gabriel.whatever(web_search=True, search_context_size="low")`, `n_parallels=1`, and the existing Harvard proxy wiring.
- Attempt 3 was not run because attempt 2 produced non-empty response text and a parseable BPS/BTU source URL.
- Counted source rows from URLs explicitly retained in the response text, not every raw URL in GABRIEL's `Web Search Sources` metadata.
- Did not ingest, create production data, run five cities, run all-32 v10, recommend PRRs, or make causal claims.

**Surprises/breakage**
- Attempt 1 still failed with a connection error and no response.
- Attempt 2 succeeded and rediscovered the BPS `BTU Contract Negotiations` page.
- GABRIEL exposed many raw web-search source metadata URLs, but the concise response retained one directly relevant source; the working source/extraction CSVs record that retained item only.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Graduated retry snapshot**
```text
attempt 1 tiny Boston report: ran; failed with connection error
attempt 2 source discovery only: ran; succeeded
attempt 3 small attribute extraction: skipped after attempt 2 success
source rows: 1
working extraction rows: 1
URLs/citations preserved: yes
Boston BTU/BPS material rediscovered: yes
web search run: Boston-only graduated retry
ingestion performed: no
production corpus modified: no
```

**Next steps**
1. Keep the next live test Boston-only and tune one dimension at a time: prompt size, output cap, source metadata handling, and timeout behavior.
2. Do not run a five-city live pilot until a small Boston structured-output path is stable.
3. Keep ingestion separate from all web-search tuning runs.

## 2026-07-01 - GABRIEL/OpenAI proxy web-connectivity diagnostic completed

**Did**
- Created and ran a minimal diagnostic runner:
  - `analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py`
- Created diagnostic outputs:
  - `analysis/gabriel_pilot/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.csv`
  - `docs/analysis/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Kept prompts tiny and diagnostic-only: one raw non-web proxy call, one GABRIEL non-web call, one GABRIEL web-search call constrained to `openai.com`, and one raw Responses API web-search tool call.
- Wrote only sanitized status fields: test name, attempted/success flags, error type, short error message, endpoint/path, and notes.
- Did not rerun the full Boston web-search prompt, did not run a five-city pilot, and did not ingest or modify production data.
- Treated the final result category as `unknown`, because all four minimal diagnostics succeeded and the earlier Boston connection-error failure was not reproduced.

**Surprises/breakage**
- The first sandboxed diagnostic showed connection failures, so the same bounded diagnostic was rerun with approved network access.
- A too-low raw Responses web-search output cap produced an incomplete response; increasing only the diagnostic cap to 100 tokens allowed the raw web-tool check to complete.
- Final result: raw OpenAI non-web, GABRIEL non-web, GABRIEL `web_search=True`, and raw Responses web-search all succeeded on tiny prompts.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Connectivity diagnostic snapshot**
```text
raw OpenAI proxy no-web: succeeded
GABRIEL non-web: succeeded
GABRIEL web-search tiny diagnostic: succeeded
raw Responses API web-search tiny diagnostic: succeeded
result category: unknown
web search run: only tiny diagnostics constrained to openai.com
ingestion performed: no
production corpus modified: no
```

**Next steps**
1. Ask Hemanth/Harvard proxy support whether longer Responses API hosted web-search requests from `openai-gabriel` have proxy-side timeout, body-size, source-include, or logging constraints that could explain the larger Boston connection-error failure while tiny diagnostics succeed.
2. Do not broaden to Boston retry or five-city live testing until that environment question is resolved.
3. Keep ingestion separate from any future web-search smoke test.

## 2026-07-01 - openai-gabriel installed; Boston built-in web call failed with connection errors

**Did**
- Installed `openai-gabriel` into the active project virtual environment after the first sandboxed attempt failed DNS resolution for `pypi.org`.
- Verified `import gabriel` works and observed installed version `1.1.8`.
- Inspected signatures for `gabriel.whatever`, `gabriel.extract`, `gabriel.rate`, and `gabriel.classify`.
- Confirmed the native report-first path is callable by signature: `gabriel.whatever(..., web_search=True, web_search_filters=..., search_context_size=...)`.
- Created and ran:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`
- Created failed-run working artifacts:
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_dataframe.csv`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/gabriel_whatever_raw.csv`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/gabriel_whatever_raw_run_metadata.json`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_response.txt`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_sources_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_extractions_2026-07-01.csv`
- Updated:
  - `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Used built-in `gabriel.whatever(web_search=True)` as the primary live path, because package inspection confirmed the tutorial-described route exists.
- Passed the Harvard proxy credential at runtime as `api_key`, `base_url`, and `extra_headers`, matching existing project conventions without printing or committing secrets.
- Kept the test to one Boston prompt and `n_parallels=1`.
- Did not modify `requirements.txt`, because install/import succeeded but the built-in web call did not return a response; dependency pinning should wait until proxy/web-mode behavior is resolved.
- Did not run `gabriel.extract(modality="web")`, because `whatever(web_search=True)` was available by signature and the failure was live call execution rather than missing report-first support.

**Surprises/breakage**
- GABRIEL's top-level functions are async in this package version; the runner needed to await the result.
- GABRIEL attempted to install/upgrade `wheel` internally during runtime; the sandboxed attempt failed due DNS, but it did not change the final diagnosis.
- The first sandboxed live run failed with connection errors; an escalated rerun retried the incomplete row but still produced an empty response.
- Raw GABRIEL output shows `Successful=False`, `Error Log=["Connection error.", "Connection error.", "Connection error."]`, and no web-search sources.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Built-in web smoke-test snapshot**
```text
openai-gabriel installed/imported: yes
installed version: 1.1.8
built-in web mode callable by signature: yes
Boston smoke test executed: attempted via native GABRIEL path
GABRIEL web path used: gabriel.whatever(web_search=True)
live response returned: no
source rows created: 0
extraction rows created: 0
Boston BTU rediscovered: no
URLs/citations preserved: no
requirements.txt modified: no
ingestion performed: no
production corpus modified: no
recommended next step: confirm whether Harvard HUIT proxy supports Responses API web-search tools through openai-gabriel, or rerun in a standard OpenAI endpoint/key environment
```

**Next steps**
1. Ask Hemanth/toolkit creator whether built-in web mode should work through the Harvard HUIT proxy with the current `extra_headers` wiring.
2. If the proxy supports web tools, rerun only the same Boston prompt after the connection/proxy issue is fixed.
3. If the proxy does not support web tools, rerun the same Boston prompt only in an approved standard OpenAI endpoint/key environment.
4. Keep ingestion and any five-city pilot separate until the Boston built-in smoke test returns source/citation-bearing output.

## 2026-07-01 - Built-in GABRIEL web smoke test blocked locally

**Did**
- Confirmed the repo location and read the project instructions, handoff, Thursday report package, prompt template, seed outputs, and GABRIEL pilot runners requested for this task.
- Checked for an installed or vendored GABRIEL package and local tutorial notebook.
- Determined the Boston-only built-in GABRIEL web smoke test could not be executed in this environment because `gabriel` is not importable.
- Created:
  - `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Stopped before any live search because the built-in package was unavailable; faking results or falling back to the custom callback would violate the task boundary.
- Kept built-in GABRIEL web mode as the primary live path in the reports, because the tutorial correction still controls the framework.
- Kept `get_all_responses_fn` framed as fallback/advanced infrastructure for schema control or nonstandard backends.
- Did not create the Boston runner or result CSVs, because there was no callable built-in GABRIEL web API to run.

**Surprises/breakage**
- `import gabriel` failed.
- `python -m pip show gabriel GABRIEL gabriel-toolkit gabriel-ai` found no installed package.
- Repo search found no vendored GABRIEL package and no local uploaded tutorial notebook; `/mnt/data` was not present.
- Because no code was added, no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Built-in web smoke-test snapshot**
```text
built-in GABRIEL package importable: no
Boston smoke test executed: no
GABRIEL web path used: none
source rows created: 0
extraction rows created: 0
Boston BTU rediscovered: no live test run
URLs/citations preserved: none returned
ingestion performed: no
production corpus modified: no
recommended next step: get installable/importable GABRIEL package or toolkit environment from Hemanth/toolkit creator
```

**Next steps**
1. Ask Hemanth/toolkit creator for the installable/importable GABRIEL package version or exact environment where tutorial web-mode calls are available.
2. Rerun only the Boston smoke test after package availability is fixed.
3. Start with `gabriel.whatever(..., web_search=True, search_context_size="low")` if available; otherwise use the supported `gabriel.extract(..., modality="web")` route.
4. Keep ingestion and any five-city pilot separate until the Boston built-in smoke test succeeds.

## 2026-07-01 - All-repo declutter plan and manifest created

**Did**
- Read the core project instructions, status logs, schema, and hypothesis memos.
- Inspected the repo tree broadly across `docs/`, `docs/analysis/`, `docs/acquisition/`, `analysis/gabriel_pilot/`, `reports/`, `logs/`, `ingest/`, `scripts/`, `data/`, `corpus/`, and `inbox/`.
- Checked references where practical so active files were not mislabeled as disposable.
- Created:
  - `docs/analysis/repo_declutter_plan_2026-07-01.md`
  - `docs/analysis/repo_declutter_candidate_manifest_2026-07-01.csv`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Treated the task as archive planning only, because the user explicitly prohibited deleting, moving, renaming, or archiving anything yet.
- Kept `data/`, `corpus/`, `inbox/`, `ingest/`, validation scripts, and API spend logs in the do-not-touch or keep-active lanes, because they are either production inputs, production provenance, or active infrastructure.
- Split `analysis/gabriel_pilot/` into active code, active v9 outputs, branch-specific v10/web-search artifacts, and legacy generated outputs, because that directory is the main mixed-risk clutter area.
- Treated most `docs/acquisition/`, comparator memos, session snapshots, and old report exports as provenance to relocate later rather than clutter to discard.

**Surprises/breakage**
- `analysis/gabriel_pilot/` is much more mixed than the rest of the repo: active runners, active inputs, active v9 outputs, legacy v1-v8 outputs, web-search seed demos, and scratch/generated clutter all coexist in one directory.
- `reports/6_25/` is still referenced by current analysis docs, so it is not a safe immediate archive target without user review.
- No code changes were made, so no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Declutter snapshot**
```text
all-repo declutter plan created: yes
candidate manifest created: yes
files deleted: no
files moved: no
files renamed: no
recommended next step: user review before any actual archive operation
```

**Next steps**
1. Review the archive categories with the user before moving anything.
2. Do the first actual archive pass only after the Thursday package is finalized.
3. Handle `analysis/gabriel_pilot/` and `docs/analysis/` as staged, family-by-family cleanups rather than bulk folder moves.

## 2026-07-01 - Tutorial clarified built-in web mode; framework corrected

**Did**
- Re-read the current Thursday-report package and corrected the framing after the tutorial clarification supplied for this task.
- Created:
  - `docs/analysis/gabriel_tutorial_web_mode_note_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_repo_declutter_plan_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

**Decisions and why**
- Reframed built-in GABRIEL web mode as the primary live path, because the tutorial clarification indicates `modality="web"` and `web_search=True` are the standard routes and `get_all_responses_fn` is the advanced route.
- Kept the custom callback scaffold as fallback/advanced infrastructure, because it may still be useful for project-specific schema enforcement or nonstandard backend requirements.
- Kept the five-city seed counts unchanged and preserved the no-live-search/no-ingestion boundary, because this session was about correcting framework interpretation rather than generating new findings.
- Created a declutter/archive plan instead of moving files immediately, because the Thursday package is still active and should not be rearranged before report finalization.

**Surprises/breakage**
- The tutorial notebook itself was not accessible locally in this session at `/mnt/data` or under the repo, so the tutorial note records the tutorial correction used for this task and distinguishes it from repo-local inspection.
- No code changes were made, so no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Framework snapshot**
```text
built-in web mode treated as primary live path: yes
custom callback treated as fallback/advanced path: yes
declutter/archive plan created: yes
files deleted: no
files moved: no
live web search executed: no
ingestion performed: no
recommended next step: Boston-only built-in GABRIEL web smoke test
```

**Next steps**
1. Confirm exact built-in GABRIEL web-mode invocation details and output structure in this environment.
2. Run a Boston-only built-in web smoke test before any five-city live test.
3. Archive superseded support materials only after the Thursday report is finalized.

## 2026-07-01 - Live smoke test skipped; no safe backend available

**Did**
- Considered the requested one-city Boston live web-search smoke test.
- Inspected local dependencies, installed search-client packages, environment variable names, and repo references for a safe callable search backend.
- Determined no safe repo-local backend was available, so no live search was executed.
- Created:
  - `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- Added concise `Optional live smoke test` notes to:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated `docs/analysis/chatgpt_handoff_latest.md` and this log.
- Ran required checks.

**Decisions and why**
- Did not use general search-engine result scraping, because the task explicitly disallowed it.
- Did not treat session-level browser/search tools as a repo-local `web_search` backend, because they cannot be passed through the Python `custom_get_all_responses` scaffold as an executable adapter.
- Kept the Thursday package seed-mode only; the adapter contract remains ready for toolkit-creator confirmation.

**Surprises/breakage**
- No search API wrapper was present in `requirements.txt`.
- Installed-package probes found no SerpAPI, Serper, Brave, Tavily, Exa, Google API client, DuckDuckGo wrapper, or equivalent search client.
- The only local `.env` key advertised was the Harvard HUIT OpenAI proxy key already used for existing GABRIEL scoring and optional LLM span extraction.
- No code changes were made, so no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Live smoke-test snapshot**
```text
safe backend available: no
live smoke test executed: no
backend used: none
source rows created: 0
extraction rows created: 0
Boston BTU rediscovered: no live test run
ingestion performed: no
production corpus modified: no
```

**Next steps**
1. Ask the toolkit creator to confirm a callable backend or approved search API/client matching the proposed `web_search` contract.
2. If confirmed, rerun only the one-city Boston smoke test before expanding to any five-city live pilot.
3. Keep ingestion separate from any future live discovery test.

## 2026-07-01 - Thursday report polish and PDF-ready markdown created

**Did**
- Polished the main Thursday report draft for a toolkit-creator meeting:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created a shorter PDF-ready markdown companion:
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated the presentation outline to include a worked JSON example and explicit Thursday decision points.
- Updated `docs/analysis/chatgpt_handoff_latest.md` and this log.
- Ran required checks.

**Decisions and why**
- Added a short `What we built` section and a `What this is / what this is not` section so the document reads cleanly at the top without requiring the reader to infer scope.
- Added a short Boston worked JSON example to show the callback output shape without dumping a full payload.
- Reframed open questions as adapter-fit points, because the likely Thursday outcome is contract adjustment rather than feasibility uncertainty.
- Created a separate PDF-ready markdown so Wednesday-night conversion can happen without trimming the fuller draft in a hurry.

**Surprises/breakage**
- No new breakage.
- No code changes were needed, so no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Thursday package snapshot**
```text
main report polished: yes
pdf-ready markdown created: yes
presentation outline updated: yes
live web search executed: no
ingestion performed: no
seed counts unchanged: 5 city responses | 15 source rows | 34 extraction rows
recommended next step: convert PDF-ready markdown to PDF Wednesday night
```

**Next steps**
1. Do one quick read focused on PDF page length and table breaks.
2. Convert the PDF-ready markdown to PDF Wednesday night.
3. Keep any later live test separate from ingestion and bounded to the same five-city scaffold.

## 2026-07-01 - Thursday report draft package created

**Did**
- Created the Thursday-facing markdown report draft:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created the short presentation outline:
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- Created report asset tables under:
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`
- Updated `docs/analysis/chatgpt_handoff_latest.md` and this log.
- Ran required checks.

**Decisions and why**
- Kept the report code-adjacent but readable without forcing the toolkit creator to inspect Python files.
- Reused the existing five-city seed outputs as the empirical backbone of the draft so all counts and examples stay auditably tied to real local artifacts.
- Framed the scaffold as an acquisition/extraction assistant rather than a measurement engine, because no live backend is present locally and no live search was authorized.
- Kept the design language conservative: bounded search contract, explicit corpus-lane separation, no ingestion, no PRRs, and no causal claims.

**Surprises/breakage**
- No new breakage.
- No code changes were needed for this session, so no `py_compile` pass was required.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**Thursday report package snapshot**
```text
main report created: yes
presentation outline created: yes
asset tables created: yes
live web search executed: no
ingestion performed: no
seed counts used: 5 city responses | 15 source rows | 34 extraction rows
recommended next step: review report draft, then convert to PDF Wednesday night
```

**Next steps**
1. Review the report draft for whether it needs more executive polish or more callback-level technical detail.
2. If the framing is accepted, convert the markdown report to PDF Wednesday night.
3. Keep the next technical step bounded to backend-adapter confirmation and a five-city live test only if separately authorized.

## 2026-06-30 - GABRIEL web-search scaffold contract refined

**Did**
- Refined `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py` around a concrete live backend contract:
  - `web_search(query: str, *, max_results: int = 5, domains: list[str] | None = None, city: str | None = None, state: str | None = None) -> list[dict]`
- Updated the scaffold to preserve URLs and snippets explicitly and to always return parseable JSON strings in `Response`.
- Added structured error fields to the response payload: `status`, `error_type`, `error_message`, `source_candidates`, `extractions`, and `notes`.
- Added prompt-builder support for city-specific domain filters plus bounded caps for max results, retained sources, and extractions per source.
- Updated `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`, `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`, and `docs/acquisition/gabriel_websearch_city_prompt_template_2026-06-30.md`.
- Re-ran the seed demo and checks.

**Decisions and why**
- Treated the live backend contract as source discovery only: URLs, snippets, domains, dates, and retrieval status come from `web_search`, while extraction belongs inside `custom_get_all_responses`.
- Kept streaming unsupported because the Thursday integration point is a complete dataframe-returning hook, not a partial-update transport.
- Kept error handling simple and explicit: no retries, no silent failures, and seeded fallback only when a live backend was attempted and failed.
- Added evidence-origin fields (`search_snippet`, `page_text_excerpt`, `evidence_origin`) to the JSON payload shape so discovery-stage evidence can stay distinguishable from later page-text extraction.

**Surprises/breakage**
- No new breakage after the contract refinement.
- The flattened seed demo outputs stayed at the same row counts despite the richer JSON payload shape.

**Validation/audit results**
```text
python analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py
wrote responses: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv
wrote sources: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv rows=15
wrote extractions: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv rows=34

python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/gabriel_websearch_custom_fn.py
passed

python -m py_compile analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**custom GABRIEL web-search function snapshot**
```text
hook implemented: custom_get_all_responses
response serialization: always JSON string
streaming supported: no
live backend contract fixed: yes
domain filters exposed: yes
max-results support exposed: yes
error format: structured; no retries
live search executed: no
```

**seed demo snapshot**
```text
responses written: 5
source rows written: 15
extraction rows written: 34
seed row counts changed: no
```

**Thursday presentation snapshot**
```text
main contract to show: web_search(query, *, max_results, domains, city, state) -> list[dict]
discovery result keys: title, url, snippet, source_domain, published_date, retrieval_status
main design message: source discovery first, GABRIEL extraction second, all inside the custom hook boundary
live execution status: still seed/dry-run only
```

**Next steps**
1. Use the refined memo and current seed demo as the Thursday discussion artifact.
2. Ask the toolkit creator whether their actual backend already matches the proposed `web_search` signature or needs an adapter.
3. If a safe backend is later provided, test only the same five-city bounded pilot with domain filters and capped results.

## 2026-06-30 - GABRIEL custom web-search scaffold seed demo

**Did**
- Inspected the repo for GABRIEL extension hooks and confirmed there are no local matches for `response_fn`, `get_all_responses_fn`, `embedding_fn`, `get_all_embeddings_fn`, `json_mode`, or `web_search`.
- Created `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py` as a custom `get_all_responses_fn` scaffold with seed/dry-run default behavior and bounded optional live-mode placeholders.
- Created `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`.
- Ran the seed demo and wrote:
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`
- Created `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`.
- Updated `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md` and `docs/analysis/chatgpt_handoff_latest.md`.

**Decisions and why**
- Kept the implementation in seed/dry-run mode because the repo still lacks a safe local live-search backend and the task explicitly forbids broad live search unless that backend already exists.
- Used the existing 15-row source seed CSV and 34-row extraction seed CSV as the calibration harness so the scaffold demonstrates realistic output shape without inventing search results.
- Returned JSON payload strings inside a dataframe with `Identifier` and `Response`, because that is the narrowest plausible shape for the GABRIEL tutorial hook while staying easy to flatten back into source and extraction tables.
- Left optional live mode bounded and off by default, with explicit fallback to seeded payloads if a future backend callable fails.

**Surprises/breakage**
- The first demo run failed because the new scaffold resolved the repo root one directory too high; fixed by changing the root from `HERE.parent.parent.parent` to `HERE.parent.parent`.
- Validation, coverage audit, and both `py_compile` checks passed after that fix.

**Validation/audit results**
```text
python analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py
wrote responses: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv
wrote sources: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv rows=15
wrote extractions: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv rows=34

python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/gabriel_websearch_custom_fn.py
passed

python -m py_compile analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**custom GABRIEL web-search function snapshot**
```text
file: analysis/gabriel_pilot/gabriel_websearch_custom_fn.py
hook implemented: custom_get_all_responses
accepted args: prompts, identifiers, json_mode, model, api_key, web_search, **kwargs
default execution mode: seed_dry_run
live search executed: no
live mode default: off
live dependency still missing: real callable web_search backend contract from toolkit creator
```

**seed demo snapshot**
```text
pilot cities: Boston, Somerville, Newton, Wayland, Seekonk
responses written: 5
source rows written: 15
extraction rows written: 34
response payload fields: city, status, source_candidates, extractions, notes
docs/acquisition seed files overwritten: no
```

**Thursday presentation snapshot**
```text
core artifact: docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md
supporting artifact: analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv
main message: the integration shape is now concrete, but live search still depends on the toolkit creator exposing the backend callable and return schema
recommended discussion focus: backend signature, result object shape, citations/URLs, JSON mode, streaming, retries, and rate limits
```

**Next steps**
1. Use the new design memo and seed demo outputs as the Thursday discussion artifact.
2. Ask the toolkit creator for the exact `web_search` callable contract and expected return format.
3. If that backend becomes available, rerun only the same five-city bounded pilot before considering any broader search work.

## 2026-06-30 - GABRIEL web-search extraction pilot seed

**Did**
- Inspected local GABRIEL and ingestion tooling for a callable web-search function.
- Confirmed no local city/query GABRIEL web-search function is available in the repo.
- Created `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`.
- Created `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`.
- Created `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`.
- Created `docs/acquisition/gabriel_websearch_city_prompt_template_2026-06-30.md`.
- Updated `docs/analysis/chatgpt_handoff_latest.md` with the Thursday pilot status and next-run recommendation.

**Decisions and why**
- Treated the output as design/seed only because the repo has local GABRIEL scoring runners and fetcher scaffolding, but no safe web-search function that can accept city/query input and return URLs, snippets, source classifications, or multi-attribute extractions.
- Seeded the pilot from already known public leads and existing corpus metadata rather than doing broad web search or scraping.
- Kept the lane distinction explicit: causal candidates, mechanism-proxy materials, discourse candidates, and lead-only index pages are not merged.
- Used Boston BTU as a mechanism-proxy calibration source only; peer-wage comparison alone remains non-evidence for `arbitration_or_impasse_backstop`.
- Used Wayland DPW and Seekonk DPW as ordinary grievance-arbitration exclusion examples.

**Surprises/breakage**
- No executable GABRIEL web-search function was present locally.
- The only web-facing code found was `ingest/fetchers/`, whose live parsing is intentionally unimplemented until selectors are confirmed.
- An optional one-line CSV parse/count check initially failed due shell quoting, then passed with 15 source rows and 34 extraction rows.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

**GABRIEL web-search pilot snapshot**
```text
status: design/seed only; web-search function not executed
cities: Boston, Somerville, Newton, Wayland, Seekonk
source candidates retained: 15
sources per city: 3
known calibration sources included: Boston BTU, Somerville police JLMC/arbitration packets, Wayland fire JLMC, Seekonk official CBA archive PDFs
ingestion performed: no
```

**extraction snapshot**
```text
extraction rows: 34
attributes covered: comparability_emphasis, arbitration_or_impasse_backstop, wage_reasoning_density, named_comparator_signal, source_ingestability
Boston BTU: high comparability and named-comparator signal; no v10 impasse backstop from peer comparison alone
Somerville police awards: high comparability and high arbitration/impasse calibration
Newton materials: mechanism-proxy or manual-review leads
Wayland/Seekonk ordinary CBAs: source-ingestability or grievance-arbitration exclusion checks
```

**Thursday presentation snapshot**
```text
usable artifact: docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md
message: the schema and calibration harness are ready, but the repo did not expose the web-search function
ask for toolkit creator: provide invocation shape, credentials/env vars, rate limits, result schema, and extraction hook
recommended live run: five-city bounded pilot only, then compare against seeded calibration rows
```

**Next steps**
1. Use the summary memo as the Thursday discussion artifact.
2. If the toolkit creator exposes a callable GABRIEL web-search function, run the same five-city pilot live and compare returned results against the seeded calibration rows.
3. Keep ingestion paused until a separate task authorizes manual verification and pipeline processing.

## 2026-06-30 - repaired v10 gold set and bounded retry

**Did**
- Inspected Arlington DPW 2018 source text and confirmed the first-run failure was driven by Article XXX future reopener/impasse language, not grievance-arbitration boilerplate.
- Created `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`.
- Created `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`.
- Updated `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py` to accept explicit gold/input/output/audit paths so repaired retries do not overwrite first-run files.
- Built `analysis/gabriel_pilot/input_v10_gold_repaired_2026-06-30.csv`.
- Ran one bounded repaired retry and wrote `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv` plus `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_audit_2026-06-30.csv`.
- Created `docs/analysis/gabriel_v10_gold_repaired_dryrun_report_2026-06-30.md`.
- Updated the v10 design memo and ChatGPT handoff with repaired retry results and the next-run recommendation.

**Decisions and why**
- Recoded `ma_arlington_public_works_2018` from `false_positive_trap` to `ambiguous`, expected band `26_50`, because Article XXX references future reopener negotiations, Chapter 1078, mediation/factfinding, and money issues.
- Added `ma_arlington_public_works_2015` as a second ambiguous future-reopener/impasse edge case because it has the same structure.
- Recoded `ma_wayland_public_works_2020` from `clear_negative` to `false_positive_trap`, because its Article 30 grievance-and-arbitration procedure is a clean DPW/public-works boilerplate trap.
- Did not revise the prompt, because the repaired retry did not show a true prompt failure.
- Recommended a small all-32 causal pilot next, with future reopener/impasse clauses flagged during review and results stratified by source type.

**Surprises/breakage**
- Arlington future-reopener edge cases scored `60`, above the repaired expected `26_50` band but below clean award/JLMC positives. This is an open construct-boundary issue rather than a grievance-boilerplate failure.
- The local quote relevance screen still over-filters some process excerpts: both Arlington rows had verified-but-irrelevant-only quote status despite coherent model rationales.
- The repaired retry had zero formal audit failures.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**repaired v10 gold-set snapshot**
```text
rows: 12
clear_positive: 3
clear_negative: 3
false_positive_trap: 4
ambiguous / future-reopener edge cases: 2
mechanism-proxy rows included: 1
Arlington 2018: false_positive_trap -> ambiguous
Wayland DPW 2020: clear_negative -> false_positive_trap
Arlington 2015: added as ambiguous future-reopener edge case
```

**retry prompt-boundary results**
```text
formal audit failures: 0
clear_positive scores: 100, 92, 78
clear_negative scores: 10, 0, 0
false_positive_trap scores: 5, 15, 10, 5
ambiguous scores: 60, 60
Boston BTU mechanism-proxy negative: 0
clean grievance-only traps stayed <=25: yes
clear positives stayed >=51: yes
future reopener/impasse cases behaved plausibly: yes, upper-middle with construct caveat
prompt revision recommended: no
```

**Next steps**
1. Run a small all-32 causal v10 pilot only, not a production dataset.
2. Preserve `source_type`, `source_corpus`, and ordinary-CBA versus award-style stratification in any pilot report.
3. Add a review flag for future reopener/impasse clauses so Arlington-style cases are not confused with grievance boilerplate or full award-style positives.

## 2026-06-30 - v10 gold prompt dry-run

**Did**
- Built `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py` as a bounded v10 runner for the 11-row hand-coded gold set only.
- Created `analysis/gabriel_pilot/input_v10_gold_2026-06-29.csv` from the gold-set CSV, existing `contracts.csv` metadata, existing v9-extracted causal text, and memo-only Boston mechanism-proxy context.
- Ran the candidate `arbitration_or_impasse_backstop` prompt once and wrote `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv` plus `analysis/gabriel_pilot/results_v10_gold_dryrun_audit_2026-06-29.csv`.
- Created `docs/analysis/gabriel_v10_gold_dryrun_report_2026-06-29.md`.
- Updated the v10 design memo and latest ChatGPT handoff with the dry-run result and next-run recommendation.

**Decisions and why**
- Reused the existing v9 extracted full text for causal rows rather than re-extracting PDFs, because it is the same local source-text path and avoids touching corpus files.
- Kept Boston BTU as mechanism-proxy dry-run context from existing notes only, because no staged full page text was needed for the boundary test and the instruction prohibited broad scraping.
- Did not run a retry, because the lone failure was not grievance-arbitration boilerplate being over-scored; Arlington DPW contains a separate duration/reopener clause with impasse procedure, mediation/factfinding, and money-issue language.
- Recommended repairing the gold set before an all-32 pilot, because the Arlington row is now a construct-boundary or gold-contamination case rather than a clean false-positive trap.

**Surprises/breakage**
- The first sandboxed model call failed on DNS/network resolution; rerunning the same bounded script with approved network access succeeded.
- `ma_arlington_public_works_2018` was labeled as a grievance-arbitration trap, but the full text includes an Article XXX reopener/impasse clause: if agreement cannot be reached, parties may use mediation/factfinding under Chapter 1078 and present money issues to Town Meeting.
- The local quote relevance screen was conservative: it kept scores and audit fields usable, but it over-filtered some JLMC/stipulated-award and impasse excerpts.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py
passed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**v10 gold dry-run snapshot**
```text
gold-set rows scored: 11
clear_positive: n=3 | scores 96, 96, 88 | all >= 51
clear_negative: n=4 | scores 0, 10, 0, 0 | all <= 25
false_positive_trap: n=4 | scores 20, 70, 10, 15 | 3 of 4 <= 25
Boston BTU mechanism-proxy negative: score 0
formal boundary failures: 1
retry run: no
```

**Prompt-boundary results**
```text
grievance-only traps stayed low: mostly yes
false-positive traps all <= 25: no
clear positives all >= 51: yes
Boston peer-wage-only mechanism proxy stayed low: yes
main issue: Arlington is not a clean grievance-boilerplate trap because full text contains impasse/reopener language
recommendation: needs more gold rows / gold-set repair before all-32 causal pilot
```

**Next steps**
1. Decide whether future reopener clauses with mediation/factfinding and money-issue language count for `arbitration_or_impasse_backstop`.
2. Recode or replace Arlington in the gold set based on that decision.
3. Add at least one clean grievance-only DPW trap and one or two future-reopener edge cases, then run one bounded gold-set retry.

## 2026-06-29 - v10 gold set and ChatGPT handoff

**Did**
- Re-read the v10 design memo, mechanism-source notes, comparator synthesis memo, v9 results files, and the current contracts and coverage tables.
- Created `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv` as a small hand-coded gold set for `arbitration_or_impasse_backstop`.
- Created `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md` documenting row selection, composition, and prompt-boundary use.
- Created `docs/analysis/chatgpt_handoff_latest.md` as a reusable project-state handoff for future ChatGPT planning.
- Added a short gold-set pointer to `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`.
- Made a tiny filename-date cleanup in `docs/acquisition/ma_newton_somerville_boston_mechanism_source_plan_2026-06-26.md`.

**Decisions and why**
- Built the first gold set around three clean positives, three clean causal negatives, four grievance-arbitration false-positive traps, and one separate-lane Boston mechanism-proxy row, because the immediate v10 need is boundary discipline rather than broad coverage.
- Kept the Boston BTU page in the gold set only as a mechanism-proxy negative, because it is valuable for testing that peer-wage comparison content alone should not trigger `arbitration_or_impasse_backstop`.
- Used short quotes where already verified and locators where fast quote verification was not worth forcing, because the task was a hand-coded design scaffold rather than a new extraction pass.
- Kept ambiguous cases out of this first gold set, because the more urgent failure mode is over-scoring grievance boilerplate.

**Surprises/breakage**
- The current corpus supports cleaner trap design than expected: several ordinary CBAs contain arbitration-heavy grievance sections that are ideal anti-examples for v10.
- Two useful clean negatives came from Wayland and one from Worcester, which helps avoid collapsing the attribute into a pure safety/non-safety proxy.
- No code changes were needed, and the only small cleanup outside the gold-set files was a stale planning-note filename date.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**v10 gold-set snapshot**
```text
gold-set rows: 11
clear positives: 3
clear negatives: 4
false-positive traps: 4
ambiguous: 0
mechanism-proxy rows included: 1
main trap class: grievance-arbitration boilerplate in ordinary CBAs
```

**ChatGPT handoff snapshot**
```text
handoff file: docs/analysis/chatgpt_handoff_latest.md
includes: corpus snapshot, current interpretation, key artifact paths, open decisions, and suggested next Codex run
main recommendation carried forward: dry-run the v10 prompt on the gold set before any broader causal pass
```

**Next steps**
1. Dry-run candidate v10 prompt language against the 11-row gold set.
2. Review whether the prompt keeps grievance-arbitration boilerplate near `0` to `1_25` before considering any all-32 causal run.
3. Only after that boundary check, decide whether to add ambiguous edge cases or proceed to a small v10 pilot.

## 2026-06-29 - v10 arbitration/impasse attribute design memo

**Did**
- Re-read the v9 results, quote audit, public-source strategy note, mechanism-source summary, comparator design memo, comparator extraction memos, comparator synthesis memo, and the readable v9 preliminary PDF.
- Created `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md` as a conceptual and implementation-readiness memo for a possible v10 attribute named `arbitration_or_impasse_backstop`.
- Added a short pointer in `docs/hypotheses_public_source_strategy_2026-06-24.md` to the new v10 design memo.

**Decisions and why**
- Defined the attribute around formal impasse-resolution pathways that shape wage-setting or successor-contract settlement, because the observed v9 pattern points to an institutional-pathway gap rather than only a comparability-language gap.
- Made grievance-arbitration boilerplate the main exclusion rule, because it is the biggest false-positive risk for any arbitration-focused attribute.
- Recommended `source_type`- and `source_corpus`-stratified analysis from the start, because the current evidence already shows strong document-production confounding.
- Recommended first hand-coding a small gold set rather than running v10 immediately on all 32 causal rows, because the project needs prompt-boundary discipline before adding another source-type-sensitive score.

**Surprises/breakage**
- The existing project notes already point toward this attribute concept more directly than the earlier v9-only framing did: Wayland JLMC, Somerville awards, and the Boston proxy page all reinforce the same institutional-pathway caveat from different document lanes.
- No repo code changes were needed; this was a pure design-note task.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**v10 design snapshot**
```text
proposed attribute: arbitration_or_impasse_backstop
core focus: wage-setting or contract settlement under formal impasse-resolution pathways
main exclusion: grievance-arbitration boilerplate
recommended fields: v8/v9-style score, rationale, excerpts, ambiguity and boilerplate flags
recommended next move: hand-code a small gold set before any v10 run
run GABRIEL now: no
```

**Next steps**
1. Hand-code a small gold set of clear positives, clear negatives, and grievance-boilerplate false-positive traps.
2. Use that set to refine prompt boundaries before deciding whether a full 32-row causal pilot is justified.
3. Keep any eventual v10 analysis stratified by `source_type`, `source_corpus`, and award-style versus ordinary-CBA subsets.

## 2026-06-29 - Comparator stub and synthesis memo

**Did**
- Re-read the comparator design memo, the Somerville v9 causal edge memo, and the Boston BTU mechanism-proxy edge memo.
- Created `docs/analysis/comparator_mentions_stub_2026-06-29.csv` as a non-production 18-row stub assembled only from the two existing extraction memos.
- Created `docs/analysis/comparator_edge_synthesis_2026-06-29.md` as a short side-by-side synthesis note.
- Added a small cross-reference update in `docs/analysis/comparator_network_design_2026-06-29.md` pointing to the stub CSV and the synthesis memo.

**Decisions and why**
- Kept the stub under `docs/analysis/` rather than `data/` so it is visibly non-production and cannot be confused with a real dataset.
- Preserved `source_corpus = causal` for Somerville and `source_corpus = discourse` for Boston, with Boston’s mechanism-proxy status carried in `notes`, because the task was to preserve the tested extraction outputs rather than normalize them away.
- Kept `not_available` exactly where the source memos already used it, especially for Boston cycle dates and Somerville document dates, to avoid backfilling unsupported values.
- Did not add a validator script because the repo’s production validation pattern is centered on `data/` tables, and this stub is intentionally a memo-side scaffold.

**Surprises/breakage**
- No row-count mismatch surfaced: the stub cleanly resolves to 18 rows with the expected 10/8 split.
- The combined stub contains 15 unique comparator cities, which is enough to support later lightweight visualization work without yet justifying a production file.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Comparator-stub snapshot**
```text
stub rows: 18
source_corpus split: causal 10 | discourse 8
safety_flag split: 1 -> 10 | 0 -> 8
source_type split: arbitration_award 10 | bargaining_update 8
home_city split: Somerville 10 | Boston 8
unique comparator cities: 15
production comparator CSV created: no
```

**Next steps**
1. Use the stub for lightweight comparator-network validation or visualization work before creating any production file.
2. Keep the main H1 interpretation disciplined: causal named-city comparator evidence is still safety/arbitration-heavy, while non-safety named-city evidence currently sits in the mechanism-proxy/discourse lane.
3. Revisit a production `data/comparator_mentions.csv` only after additional same-lane evidence or validation work clarifies the right design.

## 2026-06-29 - Boston BTU comparator-edge extraction memo

**Did**
- Re-read the comparator design memo, the v9 causal comparator-edge memo, the Boston BTU deep-dive memo, and the Boston row in the mechanism-source queue.
- Re-verified the official Boston Public Schools / School Committee BTU negotiations page directly and confirmed the surrounding-district salary-comparison table title and visible district list.
- Created `docs/analysis/comparator_edges_from_boston_btu_table_2026-06-29.md` as a memo-only Boston mechanism-proxy comparator-edge extraction.
- Added a short cross-reference note in `docs/analysis/comparator_network_design_2026-06-29.md` pointing to the v9 causal memo and the new Boston memo.

**Decisions and why**
- Kept `source_corpus = discourse` for the Boston rows because the current design memo has settled on the repo's causal/discourse lane, while preserving in notes that the source is mechanism-proxy evidence.
- Used `document_date = 2025-04-30` because the official page HTML visibly provides `page-published = 2025-04-30T18:47:54Z`, making that date more defensible than `not_available`.
- Used `cycle_start` and `cycle_end = not_available` because the table is keyed to School Year 24-25 and the page discusses a 2024-2027 contract, but the table itself does not establish exact cycle boundary dates.
- Did not create a CSV because the Boston extraction produced 8 edges, which is below the helper-CSV threshold.

**Surprises/breakage**
- The verified table contains two Boston home-city rows before the surrounding-district rows, which made it important to separate home-city reference rows from actual comparator edges.
- The direct page fetch provided stronger provenance than the earlier memo alone because it exposed page metadata including `page-published`.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Boston mechanism-proxy comparator snapshot**
```text
table verified: yes
home city: Boston
comparator districts extracted: Cambridge; Wellesley; Brookline; Newton; Watertown; Milton; Dedham; Needham
edges extracted: 8
source type: bargaining_update
source corpus lane: discourse with mechanism-proxy note
CSV created: no
```

**Next steps**
1. Compare the 10 Somerville causal edges and the 8 Boston mechanism-proxy edges side by side.
2. Decide whether that is enough tested structure for a tiny comparator stub CSV.
3. If not, stay memo-first and extract one more bounded comparator case before productionizing.

## 2026-06-29 - v9 comparator-edge extraction memo

**Did**
- Reviewed the required v9 results, v9 quote audit, comparator-network design memo, Boston BTU deep-dive memo, and readable v9 preliminary PDF.
- Created `docs/analysis/comparator_edges_from_v9_verified_excerpts_2026-06-29.md` as a memo-only edge extraction from quote-audited causal evidence.
- Made a small cleanup to `docs/analysis/comparator_network_design_2026-06-29.md` so the proposed schema now separates `document_date` from `verification_date`, and the Boston illustrative rows no longer use the prior placeholder date as a document date.

**Decisions and why**
- Counted only quote-audit `supporting_relevant` excerpts as eligible starting material, because the task was to test extraction rules on already verified causal evidence.
- Required explicit named comparator municipalities for final edges, because vague phrases like "surrounding communities" do not support city-to-city network rows.
- Excluded the Arlington fire outside-detail excerpt from edge extraction even though it is verified and relevant, because it does not name a comparator city; "Town of Arlington" is the home municipality, not a comparator node.
- Kept the output markdown-only because the extraction produced 10 edges, which is not above the threshold for creating a helper CSV.

**Surprises/breakage**
- The v9 quote-audit file contains 10 verified relevant causal excerpts, but only 2 of them actually name comparator municipalities.
- All 10 extracted named-city edges come from Somerville police arbitration awards; no non-safety causal row contributes a named-city comparator edge yet.
- The earlier design memo did in fact blur Boston's verification date with document date in the illustrative rows, so that was corrected.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Comparator-edge extraction snapshot**
```text
v9 rows reviewed: 32
verified relevant causal excerpts: 10
named-city verified excerpts: 2
extracted edges: 10
edge-contributing source_obs_id values: ma_somerville_police_spsoa_2012; ma_somerville_police_spea_2012
non-edge verified comparability excerpts: 8
production CSV created: no
helper CSV created: no
```

**Date-field cleanup snapshot**
```text
design memo schema change: added verification_date
Boston illustrative rows: document_date changed from 2025-06-29 to not_available
Boston illustrative rows: verification_date set to 2026-06-29
added note: production comparator file should separate source document date from project verification date
```

**Next steps**
1. Manually extract comparator rows from the Boston BTU salary-comparison table using the cleaned date-field rules.
2. Compare those mechanism-proxy Boston rows against the Somerville causal edge list before creating any stub CSV.
3. Create a tiny machine-readable comparator stub only after causal and mechanism-proxy extraction conventions are both tested.

## 2026-06-29 - Comparator-network dataset design memo

**Did**
- Reviewed the required v9 outputs, quote audit, Boston BTU salary-comparison memo, mechanism-source summary, mechanism-source queue, and the readable v9 preliminary PDF.
- Created `docs/analysis/comparator_network_design_2026-06-29.md` as a design memo for a future city-to-city comparator network dataset.
- Kept `data/`, `corpus/`, and `inbox/` unchanged and did not create `data/comparator_mentions.csv`.

**Decisions and why**
- Defined the future comparator dataset at the mention level: one verified `home_city -> comparator_city` edge per row, because a single award or table can name many comparator municipalities.
- Recommended a strict source hierarchy led by verified GABRIEL excerpts and direct manual review, because queue labels and regex hits are useful discovery tools but too weak for production evidence.
- Recommended extracting from verified v9 excerpts next, rather than creating a stub CSV immediately, because the quote-audited causal excerpts are the cleanest current evidence base.
- Kept the Boston BTU page in a mechanism-proxy lane rather than treating it as causal evidence, because it is a verified public bargaining page, not a final reasoning document.

**Surprises/breakage**
- Current high-confidence named-city comparator evidence is still narrow: Somerville police awards and the Boston BTU salary-comparison table carry most of it.
- The reviewed Wayland JLMC material does not currently yield a verified named-city comparator example, so it was excluded from the memo's illustrative rows.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Comparator-network design snapshot**
```text
production CSV created: no
proposed future path: data/comparator_mentions.csv
recommended unit: one verified home_city -> comparator_city mention per row
high-confidence example rows in memo: 5
recommended next task: extract from v9 verified excerpts
lead-only sources retained: mechanism-source queue, regex candidates
```

**Next steps**
1. Extract a memo-only comparator edge list from the verified v9 excerpt set.
2. Manually extract the Boston BTU salary-comparison table into the same review format.
3. Decide on a tiny stub CSV only after the quote-based extraction rules are exercised on real examples.

## 2026-06-29 - Boston BTU salary-comparison lead verification

**Did**
- Verified the existing Boston `peer_wage_comparison` queue lead against the official Boston Public Schools / School Committee BTU negotiations page.
- Confirmed the page contains the table titled "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25."
- Created `docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md` as a short verification memo and left `data/`, `corpus/`, and `inbox/` unchanged.

**Decisions and why**
- Kept the Boston lead classified as `mechanism_proxy` because the verified source is a public bargaining/communications page rather than a final CBA, arbitration award, or factfinding report.
- Kept `comparability_signal = peer_wage_comparison` because the page directly compares Boston teacher salary levels with surrounding districts.
- Left the queue unchanged because the verified page matched the existing Boston row's classification (`wage_reasoning_signal = high`, `document_type = bargaining_update`, `priority = P1`).

**Surprises/breakage**
- No queue correction was needed; the existing Boston classification was already accurate.
- The strongest non-safety comparability evidence remains a public bargaining page rather than a causal-corpus reasoning document, so the source-type caveat for H1 remains central.

**Validation/test results**
```text
python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Next steps**
1. Retain the Boston BTU negotiations page as the primary public non-safety peer-wage mechanism lead.
2. Do not ingest the page into `contracts.csv`.
3. If later Boston follow-up is authorized, treat nearby bargaining materials as mechanism-proxy support unless a true final reasoning document appears.

## 2026-06-26 - Mechanism-source recon consolidation audit

**Did**
- Confirmed the Newton/Somerville/Boston mechanism-source planning file, three city recon memos, and combined queue all existed and were non-empty.
- Audited the three city memos against the filled planning note and confirmed each memo covers purpose, research value, source routes, search terms, candidate evidence, evidence classification, corpus-handling, stop rules, and recommended next action.
- Created `docs/analysis/mechanism_source_summary_2026-06-26.md` as a short PI-ready interpretation note and added a light cross-reference in `docs/hypotheses_public_source_strategy_2026-06-24.md`.
- Made one minimal queue correction so an index-only Boston row is no longer tagged as a `causal_candidate`.

**Decisions and why**
- Treated this as a consolidation and note-cleanup pass, not a new search, because the 2026-06-26 recon already produced the relevant bounded public-source evidence.
- Left the planning file untouched even though the earlier recon ran before it was filled in; the current task was to audit against it, not rewrite it.
- Kept Boston as the headline lead because it still provides the only explicit public non-safety peer-wage comparison in the audited queue.

**Surprises/breakage**
- The filled planning file still lists expected output filenames dated `2026-06-25`, while the actual recon outputs are dated `2026-06-26`; the underlying content is still coherent, so this pass only noted the mismatch.
- The queue was already structurally clean: 23 candidates, no duplicate `candidate_id` values, and no missing `city` or `source_url` fields.
- The only substantive queue issue was one Boston index route that overstated `likely_corpus_destination`.

**Validation/test results**
```text
python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Mechanism-source audit snapshot**
```text
recon files checked: 5
city memos complete against plan sections: Newton yes | Somerville yes | Boston yes
queue candidates: 23
queue correction made: 1
Boston strongest explicit peer-wage lead: yes
new ingestion recommended now: no
```

**Next steps**
1. The 2026-06-26 recon files now look complete for audit and PI review.
2. Boston remains the strongest public non-safety peer-wage lead.
3. Newton and Somerville, if revisited later, should use narrow manual packet follow-up rather than another broad recon pass.
4. No ingestion is recommended now from this mechanism-source set.
5. H1 remains plausible but underidentified.
6. Any v10 attribute design, especially `arbitration_or_impasse_backstop`, should wait for PI review of v9 plus this summary.
7. PRRs remain deferred.

## 2026-06-26 - Newton/Somerville/Boston mechanism-source recon

**Did**
- Ran a bounded public-only mechanism-source recon for Newton, Somerville, and Boston, focused on non-safety wage-reasoning evidence rather than CBA expansion.
- Created city memos for Newton, Somerville, and Boston plus a combined mechanism-source queue.
- Updated the public-source H1 strategy note and the v9 preliminary report source markdown with the post-v9 acquisition implication.
- Downloaded targeted public PDFs/HTML to `/tmp` for inspection only; no files were added to `corpus/`, `inbox/`, or `data/`.

**Decisions and why**
- Did not ingest any rows because the best new evidence is mechanism-proxy material: proposals, mediation materials, settlement summaries, public bargaining pages, presentations, CBA indexes, and ordinary CBAs.
- Treated Boston as the strongest peer-wage lead because the public BPS BTU negotiations page includes surrounding-district teacher salary comparisons.
- Treated Newton and Somerville as useful wage-rationale/proxy routes, but not as clean non-safety award/factfinding equivalents.
- Kept PRRs deferred and did not recommend them.

**Surprises/breakage**
- `docs/acquisition/ma_newton_somerville_boston_mechanism_source_plan_2026-06-26.md` existed but was empty, so the recon followed the user-supplied source routes directly and left the plan file untouched.
- BTU targeted bargaining-summary pages were public, but simple public HTML fetches exposed little clean body text; the BPS negotiations page and April 2025 presentation were more useful.
- Newton had the richest proposal/mediation trail, but no inspected Newton document provided a clean peer-district wage-comparison exhibit.

**Validation/test results**
```text
python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python ingest/test_pipeline.py
40 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Mechanism-source snapshot**
```text
queue candidates: 23
by city: Newton 9 | Somerville 8 | Boston 6
by priority: P1 8 | P2 5 | P3 9 | defer 1
likely destinations: mechanism_proxy 9 | causal_candidate 7 | acquisition_lead_only 7
comparability signals: peer_wage_comparison 1 | general_wage_rationale 9 | contract_cost_only 6 | unclear 5 | none 2
```

**Next steps**
1. Boston produced the strongest mechanism evidence because its public BPS BTU negotiations page has an explicit surrounding-district salary comparison.
2. Public non-safety peer-comparison evidence was found, but only as a mechanism proxy, not as a final causal-corpus document.
3. No causal rows were ingested; Newton/Somerville/Boston materials were documented as mechanism proxies, causal candidates, or acquisition leads.
4. H1 remains plausible but underidentified because the best non-safety evidence is not yet award/factfinding-equivalent.
5. v10 should consider `arbitration_or_impasse_backstop`, but only after PI review of v9 and this mechanism-source queue.
6. If more public-only acquisition is needed, prioritize Boston supplemental-appropriation materials and targeted Somerville/Newton packet review.
7. PRRs remain deferred.

## 2026-06-25 - GABRIEL v9 descriptive comparability run

**Did**
- Ran GABRIEL v9 as a comparability-only descriptive pass over all 32 causal-corpus rows.
- Added v9-only scripts: `analysis/gabriel_pilot/build_input_v9.py`, `analysis/gabriel_pilot/run_gabriel_v9.py`, and `analysis/gabriel_pilot/summarize_v9.py`.
- Created row-level results, quote audit, summary CSVs, matched-pair summary, figures, and the preliminary report scaffold at `docs/analysis/gabriel_v9_preliminary_report_2026-06-25.md`.
- Updated `docs/analysis/gabriel_v9_readiness_2026-06-25.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md` with short run/result notes.

**Decisions and why**
- Kept v9 to `comparability_emphasis` only because the first 32-row pass should establish a disciplined descriptive baseline before adding new attributes.
- Wrapped the v8 runner instead of altering v8 outputs, preserving full-text input, verbatim quote verification, bounded retry, and relevance filtering.
- Added a v9-specific exclusion for generic health-insurance "comparable plan" language because that wording is verbatim but not peer-wage comparability.
- Reported source-type, CBA-only, excluding-award, city-level, and matched-set sensitivities because source-type imbalance remains the main identification risk.

**Surprises/breakage**
- The initial scoring attempt failed with sandboxed connection errors and logged zero API calls; the escalated run succeeded.
- Building `input_v9.csv` required long OCR extraction for image-heavy rows, especially Newton and Wayland; the input builder was updated to write progressively and resume completed rows.
- v9 found one CBA with a verified relevant excerpt (`ma_arlington_fire_2021`, outside-detail rate language), but the high scores remain concentrated in Somerville safety arbitration awards.

**Validation/test results**
```text
python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python ingest/test_pipeline.py
40 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**GABRIEL v9 output snapshot**
```text
rows scored: 32
overall mean score: 10.41 | median: 5.0 | max: 88
safety mean: 16.80 | non-safety mean: 4.76
cba mean: 5.52 | arbitration_award mean: 57.67
cba-only mean: 5.52
excluding Somerville police awards mean: 5.33
excluding all arbitration_award rows mean: 5.52
verified relevant supporting excerpts: 10
flagged verbatim-but-irrelevant/ambiguous excerpts: 3
retry: 2 attempted, 1 recovered
API usage: 581,521 prompt tokens + 4,135 completion tokens
```

**Next steps**
1. v9 descriptively shows high comparability language in safety-side arbitration awards, but ordinary CBAs mostly score low.
2. H1 remains plausible but underidentified; v9 strengthens the source-type/document-production caveat more than an occupation-only claim.
3. Source-type confounding dominates the pooled safety/non-safety split because award-style reasoning documents are safety-side only.
4. Consider `arbitration_or_impasse_backstop` as a v10 attribute only after reviewing the v9 baseline.
5. More official portal ingestion is useful for robustness, but the higher-value gap is now non-safety reasoning evidence.
6. Mechanism-source search should prioritize Newton, Somerville, and Boston public materials.
7. PRRs remain deferred unless the PI changes preference.

## 2026-06-25 - GABRIEL v9 readiness and reporting-plan audit

**Did**
- Read the repo instructions, current strategy docs, schema, corpus tables, coverage audit code, and the latest GABRIEL runner/results materials before editing.
- Created `docs/analysis/gabriel_v9_readiness_2026-06-25.md` as a corpus-readiness, measurement-risk, and reporting-plan memo for the expanded 32-row corpus.
- Added short strategy/reporting notes to `docs/hypotheses_public_source_strategy_2026-06-24.md` and `docs/acquisition/ma_official_portal_expansion_2026-06-25.md`.
- Left `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `inbox/`, GABRIEL outputs, and scoring code unchanged.

**Decisions and why**
- Treated the corpus as ready for a first useful descriptive v9/reporting pass because it now has 32 rows, 9 cities, and 12 healthy matched safety rows.
- Recommended a comparability-only v9 rather than adding new attributes now, because the main current problem is source-type confounding and thin non-safety reasoning evidence, not lack of candidate attributes.
- Recommended running all 32 causal rows at the row level, but separating reporting by `source_type`, `text_quality`, and match tier to avoid overstating pooled occupation comparisons.

**Surprises/breakage**
- The current 32-row corpus remains heavily CBA-weighted: 29 `cba` rows versus 3 `arbitration_award` rows.
- Franklin and Wayland improve exact-cycle coverage materially, but they also increase the need for report-level aggregation discipline because some cities now contribute multiple safety rows in one cycle.
- Wayland's health-insurance "comparable plan" hits remain a live measurement-risk reminder: verbatim capture is correct, but not all "comparable" language is peer-wage comparability.

**Validation/test results**
```text
python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Next steps**
1. v9 now looks justified as a first descriptive reporting pass, provided the write-up is explicit that the output is descriptive and still source-type-confounded.
2. Keep v9 comparability-only for the first pass; revisit `arbitration_or_impasse_backstop` only after the baseline report exists.
3. Official portal expansion can still continue before or after v9, but it is no longer a prerequisite for a useful first reporting run.
4. The main remaining evidence gap is still non-safety reasoning documents comparable to the Somerville and Wayland safety-side award material.
5. The first report should prioritize row-level scores, quote-audit tables, city and matched-pair summaries, source-type splits, and exact-only versus exact+overlap sensitivities.

## 2026-06-25 - Franklin and Wayland official portal ingestion

**Did**
- Used only official Franklin and Wayland CBA portal routes; no PRRs, no licensed sources, no broad crawling, and no GABRIEL run.
- Downloaded and verified six Franklin FY23-FY25 CBAs and six Wayland priority documents through `inbox/manifest.csv` and `python ingest/process_inbox.py`.
- Ingested Franklin rows: `ma_franklin_fire_2022`, `ma_franklin_police_2022`, `ma_franklin_police_sergeants_2022`, `ma_franklin_public_works_2022`, `ma_franklin_library_2022`, and `ma_franklin_other_2022`.
- Ingested Wayland rows: `ma_wayland_police_2020`, `ma_wayland_fire_2020`, `ma_wayland_other_2021`, `ma_wayland_public_works_2020`, `ma_wayland_library_2020`, and `ma_wayland_fire_jlmc_2020`.
- Created `docs/acquisition/ma_official_portal_expansion_2026-06-25.md` and added short cross-references in the public-source strategy notes.

**Decisions and why**
- Classified Franklin custodians as `other` because custodians are not a controlled occupation class and the text does not justify forcing `public_works`.
- Kept Franklin Police Association and Police Sergeants as separate `police` rows because they are distinct bargaining units in the same town/cycle.
- Classified Wayland AFSCME 1 and 2 as `other` because recognition covers mixed town employees, and used `ma_wayland_other_2021` because the cover page gives July 1, 2021 through June 30, 2023.
- Ingested Wayland Fire JLMC as `source_type=arbitration_award` because the document is a JLMC stipulated award modifying the 2020-2023 fire agreement.

**Surprises/breakage**
- Wayland CBAs were image-only and required OCR; all were ingested as `ocr_messy`.
- Franklin's `30 Mile Radius - Police / Fire` item is a GIS radius map/list, not a CBA; it was documented as a possible mechanism/proxy lead and kept out of `corpus/`.
- The regex span extractor flagged some generic health-insurance “comparable plan” language in Wayland rows; treat this as verbatim but not necessarily wage-comparability evidence under the existing relevance-boundary note.

**Validation/test results**
```text
python ingest/process_inbox.py
ingested=12 quarantined=0 missing_file=0 skipped_duplicate=17
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/test_pipeline.py
40 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Next steps**
1. Franklin added exact-cycle healthy matched pairs for fire, police association, and police sergeants against same-cycle DPW, library, and custodians/other.
2. Wayland added exact-cycle healthy matched pairs for police and fire against same-cycle DPW and library; the JLMC award adds safety-side mechanism evidence and appears as an additional matched fire row.
3. Franklin's 30-mile radius GIS artifact is worth later mechanism/proxy review, not contract ingestion.
4. Continue official portal expansion to North Andover, Duxbury, Norwood, Ludlow, and Westwood before returning to weaker StateReference-only leads.
5. H1 remains viable without PRRs for another capped public-only pass, but non-safety reasoning evidence is still thin.
6. v9 GABRIEL remains premature, though the CBA/MOA panel is getting closer to a useful rerun once source-type caveats are reviewed.

## 2026-06-24 - Coverage audit match-tier update

**Did**
- Updated `ingest/audit_coverage.py` so coverage health is tiered into exact-cycle, overlap-cycle, adjacent-cycle, and unmatched safety rows using `cycle_start` and `cycle_end` from `data/contracts.csv`.
- Preserved exact-cycle reporting while adding overlap-cycle healthy matches and a separate exploratory adjacent section.
- Added self-contained tests for exact, overlap, adjacent, unmatched, and Seekonk-like match cases in `ingest/test_pipeline.py`.
- Added methodological notes to `docs/hypotheses.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`.

**Decisions and why**
- Counted exact-cycle and overlap-cycle safety/non-safety comparisons as healthy because both keep city and bargaining period sufficiently fixed for H1 text/mechanism comparison.
- Kept adjacent-cycle matches out of healthy counts because they are useful for exploratory context but weaker for city x time identification.
- Left schema fields, controlled vocabularies, data rows, corpus files, and GABRIEL code/output unchanged.

**Surprises/breakage**
- The updated logic also moves Boston police 2020-2025 into overlap-cycle matched status because the Boston clerical/admin 2023-2027 CBA overlaps by date.
- No adjacent-only exploratory matches appear in the current corpus.

**Validation/test results**
```text
python ingest/test_pipeline.py
40 passed, 0 failed

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3
```

**Corpus snapshot**
```text
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3 | cities: 7
healthy matched pairs: 6
  exact-cycle: 3
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Next steps**
1. Exact-cycle matched cities: Worcester, Arlington, and Georgetown.
2. Overlap-cycle matched cities: Boston and Seekonk; Seekonk police and fire are now matched to overlapping administrative secretaries, teachers, public works, and library CBAs.
3. Adjacent-only exploratory matches: none in the current corpus.
4. Remaining unmatched safety units: Somerville police superior officers 2012-2018, Somerville police patrol 2012-2015, and Newton police 2015-2018.
5. v9 GABRIEL remains premature until the overlap-tier framing and source-type caveats are reviewed.
6. Discuss with the PI whether to add a historical-institutionalization caveat: low CBA/MOA comparability language may reflect settled-document opacity rather than absence of comparability in bargaining.

## 2026-06-24 - Seekonk official contract archive ingestion

**Did**
- Used only the RA-verified official Seekonk Archive Center routes, with no broad search, no PRRs, and no GABRIEL run.
- Downloaded and first-page/entity-checked six public CBA PDFs: police, fire, administrative secretaries, educators, public works, and library.
- Added explicit `inbox/manifest.csv` rows and ingested six Seekonk rows through `python ingest/process_inbox.py`: `ma_seekonk_police_2022`, `ma_seekonk_fire_2022`, `ma_seekonk_clerical_admin_2021`, `ma_seekonk_teacher_2021`, `ma_seekonk_public_works_2023`, and `ma_seekonk_library_2023`.
- Updated the school-committee recon and StateReference triage notes to treat Seekonk as an official public CBA/MOA matched-pair candidate rather than a meeting-agenda target.

**Decisions and why**
- Ingested all six listed clean documents because public works and library were easy official PDF downloads with clear unit, employer, and term metadata.
- Left wage fields blank because wage increases were not needed for this pass and should not be manually judged during metadata ingestion.
- Did not ingest Comms & Clerical, aides, custodians, maintenance, agendas, or minutes because those were outside the first-pass boundaries or classification decisions.

**Surprises/breakage**
- The administrative secretaries PDF was image-only, but local OCR succeeded well enough for entity and term verification; it was ingested with `text_quality=ocr_messy`.
- `audit_coverage.py` still flags Seekonk police and fire as unmatched because the current audit requires exact cycle-window matches. Seekonk now has overlapping same-city safety and non-safety CBAs, but not a healthy exact-cycle pair under the audit.
- No Seekonk document required manual browser download once the official archive item IDs were used.

**Validation/test results**
```text
python ingest/process_inbox.py
ingested=6 quarantined=0 missing_file=0 skipped_duplicate=11
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3

python ingest/test_pipeline.py
35 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 20 | cities: 7
healthy matched pairs: 3
safety units unmatched: 6
```

**Next steps**
1. Seekonk became a clean overlapping public CBA batch, but not a healthy exact-cycle matched pair under the current coverage audit.
2. No Seekonk documents from this pass need manual download; future manual review should only revisit skipped mixed or unreviewed units if the team wants them.
3. School committee meeting packets remain lower priority for Seekonk because the contract archive was more valuable and the agenda route looked like ordinary agendas, not wage-comparison exhibits.
4. StateReference/city-portal ingestion can resume with this lesson: prioritize official portals that expose both safety and clean non-safety CBAs before StateReference-only follow-ons.
5. H1 remains viable without PRRs for one more public-only expansion pass, but the exact-cycle matching problem still matters.
6. v9 GABRIEL remains premature and was not rerun.

## 2026-06-24 - MA school committee materials recon pass

**Did**
- Reviewed the existing H1 strategy docs, schema, StateReference triage notes, and current corpus tables before doing any new work.
- Ran a narrow public-only recon pass on official school committee and district materials routes for Somerville, Newton, Boston, Georgetown, and an optional quick Seekonk route check.
- Created `docs/acquisition/ma_school_committee_meeting_materials_recon_2026-06-24.md` and added short follow-up notes to `docs/acquisition/ma_non_prr_public_source_expansion_2026-06-24.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`.

**Decisions and why**
- Treated school committee materials as proxy reasoning evidence rather than automatic contract evidence because packets, presentations, and minutes usually do not by themselves establish a causal contract row.
- Recommended one tightly scoped Newton-first packet review because Newton exposed the cleanest public archive structure and an explicit `Negotiations 2023-2024` route.
- Kept StateReference ingestion paused because this route looks more promising for the missing non-safety reasoning evidence than another immediate CBA/MOA-only ingestion pass.

**Surprises/breakage**
- Somerville’s official school committee route is stronger than expected: it exposes a public meeting-materials drive plus archived presentations, not just agendas and minutes.
- Boston’s BTU negotiations page is public and substantively useful, but the checked material looked more like bargaining narrative than explicit peer-city comparability exhibits.
- Georgetown’s school committee archives were reportedly lost during a town website change, which sharply limits its value as a packet route.
- The optional Seekonk official route failed at the TLS handshake level, so it was marked for manual browser review rather than pursued further.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. School committee materials look promising enough for one targeted public packet review, but mainly as proxy/discourse evidence rather than immediate causal-corpus ingestion.
2. The next municipality/source to test should be Newton school committee materials, especially the `Negotiations 2023-2024` archive.
3. Expected evidence split: Newton/Somerville/Boston meeting materials are more likely discourse or proxy mechanism evidence; only a final adopted agreement with clear provenance would be a causal-corpus candidate.
4. StateReference ingestion should remain paused until the Newton-first packet test shows whether public non-safety reasoning evidence is actually recoverable.
5. H1 remains viable without PRRs for one more public-only pass, but still underidentified if this packet route yields no explicit comparability materials.
6. v9 GABRIEL remains premature.

## 2026-06-24 - MA non-PRR public-source strategy pass

**Did**
- Reviewed the current H1 status, the StateReference seed/queue/triage notes, the non-safety factfinding recon, and the existing source-inventory notes.
- Ran a narrow live public-source check across StateReference, DLR Public Information Search, JLMC/DLR Mass.gov pages, Boston/Worcester/Newton public portals, Newton school committee materials, MuckRock, Internet Archive, and a public contract-archive route.
- Created `docs/acquisition/ma_non_prr_public_source_expansion_2026-06-24.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`, and added a short non-PRR update near the top of the StateReference triage note.

**Decisions and why**
- Kept H1 alive for one more structured public-only pass because public sources can still scale matched CBA/MOA pairs and may yield proxy reasoning evidence through meeting packets/exhibits even if final non-safety factfinding reports remain scarce.
- Did not recommend PRRs, per the PI preference and task boundary.
- Treated school committee meeting-materials pages as the main alternate proxy route for non-safety wage-comparability reasoning if DLR factfinding reports remain absent from the public web.

**Surprises/breakage**
- The live Newton city HR union-contracts route returned a permission block, while the Newton school contract page and school committee meeting-materials page remained public. That reinforces the need to distinguish “public in principle” from “reliably reachable.”
- The statewide MTA contracts route checked here did not expose a stable public contracts index, so local teacher-union pages remain a weaker fallback than district HR pages.
- The labor-contract archive route is public, but it visibly leans toward police/public-safety content and is less disciplined than official portals or StateReference for Massachusetts matched-pair work.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Next public-source families to investigate beyond StateReference: DLR Public Information Search exact-route checks, school committee meeting-materials archives, and large-city labor portals.
2. Most promising family for non-safety reasoning documents: school committee meeting materials and bargaining exhibits; DLR factfinding remains conceptually ideal but publicly thin.
3. More CBA/MOA pair ingestion is justified only after a short pre-download verification pass, with Seekonk still the best remaining candidate.
4. H1 remains viable without PRRs, but only as a public-only structured pass rather than an immediate measurement run.
5. Pivot hypotheses to keep alive: source-type/document-production, arbitration-backstop, wage-MOA opacity, and public-availability selection.
6. v9 GABRIEL remains premature.

## 2026-06-24 - MA StateReference triage pass

**Did**
- Paused live StateReference ingestion work and reviewed the saved seed memo, follow-on queue note, schema, current corpus tables, manifest, and staged `inbox/foia` PDFs.
- Added a staged-file disposition section to `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md` for the Hanover and Peabody follow-on PDFs that were downloaded but never ingested.
- Created `docs/acquisition/ma_statereference_phase1_triage_2026-06-23.md` with a municipality-level classification table, a capped next-wave list, and a separate large-municipality queue.

**Decisions and why**
- Shifted from candidate-by-candidate ingestion attempts to classification-first triage because the last follow-on wave showed too many failure modes: wrong jurisdiction, no same-cycle counterpart, dispatcher ambiguity, and mixed units.
- Kept Georgetown as the proof-of-concept clean pair but treated its `other` comparator as analytically secondary; the next wave should prioritize cleaner `clerical_admin`, `public_works`, or `teacher` targets where possible.
- Left staged PDFs in place because the repo has no established StateReference scratch/review convention beyond a one-off `DISCARD_` prefix for confirmed rejects.

**Surprises/breakage**
- The Hanover school-side staged PDF was easy to rule out once re-read locally: the first page names the Dresden and Hanover School Districts, confirming the wrong-jurisdiction failure without any new web work.
- The staged Peabody Local 365 OCR confirms a broad all-non-teaching school unit, which strengthens the case for classifying Peabody as mixed rather than merely incomplete.
- No pipeline/test runs were needed because no ingestion logic or data rows changed.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Top candidates for a future targeted ingestion prompt: Seekonk first; Woburn, Marlborough, Reading, and Great Barrington only after counterpart verification.
2. Ambiguous or mixed-unit candidates: Peabody, Georgetown DPW/clerical, Boxford, Millis, Gloucester, and any dispatcher-adjacent Lexington/Danvers records.
3. Large-city candidates needing separate handling: Springfield, Cambridge, Boston, Worcester, and Lynn.
4. Staged PDFs needing manual disposition: Hanover fire keep-only-if-paired later; Hanover school files discard after confirmation; Peabody files retain only for manual class/entity review.
5. PRRs still deferred.
6. v9 GABRIEL still premature.

## 2026-06-23 - MA StateReference follow-on batch

**Did**
- Continued the StateReference public-source pass after Georgetown and reviewed the current Georgetown rows in `data/contracts.csv` and `data/city_coverage.csv`.
- Verified Hanover, Peabody, Reading, Marlborough, and Danvers using targeted StateReference item pages and search results.
- Downloaded and locally staged Hanover and Peabody originals/OCRs for verification; no new rows were ingested.
- Updated `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md` with this wave’s attempted municipalities, statuses, and classification lessons.

**Decisions and why**
- Rejected Hanover because the school-side record is for the Dresden and Hanover School Districts in New Hampshire, so it is not a same-Massachusetts-municipality comparator.
- Rejected Reading and Marlborough because clean safety or non-safety singles exist, but not a same-cycle matched pair.
- Rejected Danvers because the targeted search surfaced only AFSCME units and dispatchers, not a police/fire contract; dispatchers remain outside the safety classes in this schema.
- Treated Peabody as ambiguous rather than cleanly ingestable: the police contract is fine, but the available school comparator is a mixed school-unit record covering cafeteria, clerks, and transportation, which is public and relevant but not a preferred single occupation class.
- Kept Georgetown's `other` comparator as acceptable but secondary. It is valid for coverage and pair formation, but the next batch should prefer cleaner `clerical_admin`, `public_works`, or `teacher` comparators when available.

**Surprises/breakage**
- The first Peabody/Reading search attempts hit sandbox DNS failures and had to be retried with approved public `curl` access.
- No ingestion pipeline run was needed because nothing new passed the clean-pair threshold.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Clean StateReference candidates still ready for targeted verification: none from the attempted top five; only later candidates if the team relaxes the stop rule.
2. Ambiguous candidates needing manual review: Peabody.
3. PRR-only targets remain deferred.
4. v9 GABRIEL remains premature.

## 2026-06-23 - MA StateReference Georgetown pilot

**Did**
- Read and preserved `docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md`.
- Verified three Georgetown StateReference DLR Contracts records and confirmed each had a visible public document attachment plus DLR Public Information Search original-source route.
- Downloaded original plus StateReference OCR PDFs for police command staff, DPW/clerical, and school custodians:
  - `inbox/foia/ma_georgetown_police_command_staff_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_police_command_staff_2020_2023_ocr.pdf`
  - `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023_ocr.pdf`
  - `inbox/foia/ma_georgetown_afscme_custodians_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf`
- Added explicit `obs_id` values to `inbox/manifest.csv` so `process_inbox.py` does not reprocess existing arbitration-award manifest rows under inferred duplicate IDs.
- Ingested two Georgetown rows through `python ingest/process_inbox.py`: `ma_georgetown_police_2020` and `ma_georgetown_other_2020`.
- Added processed OCR PDFs to:
  - `corpus/ma_georgetown/ma_georgetown_police_command_staff_2020_2023_ocr.pdf`
  - `corpus/ma_georgetown/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf`
- Created `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md`.
- Ran `python scripts/validate.py`, `python ingest/audit_coverage.py`, and `python ingest/test_pipeline.py`.

**Decisions and why**
- Coded Georgetown police command staff as `police` because the recognition clause covers Lieutenant, Sergeant, and Detective Sergeant and excludes patrolmen, dispatchers, chief, confidential, managerial, and other town employees.
- Coded Georgetown school custodians as `other` because the current controlled vocabulary has no custodial or school maintenance class; the recognition clause cleanly identifies custodians, matrons, and maintenance employees.
- Did not ingest Georgetown DPW/clerical because the recognition clause mixes Fire or Police Signal Operators, highway/DPW titles, and clerical/admin titles, so it is not a clean single occupation-class observation.
- Did not attempt Seekonk in this pass because Georgetown produced a new healthy matched pair and the task was deliberately narrow.

**Surprises/breakage**
- The original StateReference Georgetown PDFs were image-only. StateReference OCR PDFs were downloaded and used for ingestion; originals remain staged locally for provenance review.
- `process_inbox.py --dry-run` showed that old Somerville arbitration-award rows would be treated as new without explicit manifest `obs_id` values. The manifest metadata was tightened before the real run.
- The final `git status --short` still includes unrelated pre-existing changes outside this StateReference pilot, including GABRIEL files, graph deletions, prior docs, and logs. The StateReference-scoped changes are the Georgetown data/coverage/manifest rows, Georgetown corpus and inbox PDFs, the new queue note, and this PROGRESS entry.

**Validation**
```text
python ingest/process_inbox.py
ingested=2 quarantined=0 missing_file=0 skipped_duplicate=9
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3

python ingest/test_pipeline.py
35 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. More public StateReference candidates ready for targeted verification: Hanover, Peabody, Reading, Marlborough, Danvers, Lexington, Springfield, Woburn, Manchester, and Great Barrington.
2. Candidates needing manual verification: Georgetown DPW/clerical mixed unit; any dispatcher or signal-operator record; any school committee comparator whose occupation class is not obvious from the recognition clause.
3. PRR-only targets remain deferred; no PRRs were drafted or submitted.
4. v9 GABRIEL remains premature unless the team explicitly wants a CBA-panel run after reviewing the new Georgetown pair.

## 2026-06-23 — MA non-safety factfinding records-request packet

**Did**
- Confirmed `docs/acquisition/ma_non_safety_factfinding_recon_2026-06-23.md` exists and preserved it without substantive edits.
- Added a concise "Targeted recon follow-up" section to `docs/acquisition/ma_non_safety_awards_2026-06-23.md`.
- Created `docs/records_requests/ma_non_safety_factfinding_packet_2026-06-23.md` with DLR, Somerville, Boston, and Newton public-records request drafts; a manual DLR exact-search checklist; an intake checklist; and a request tracking table.
- Ran `python scripts/validate.py` and `python ingest/audit_coverage.py`.

**Decisions and why**
- Kept this as documentation/request prep only. No PDFs were downloaded, no corpus files were staged, and no data rows were added because no final non-safety factfinding report or interest-arbitration award is ready for ingestion.
- Put DLR first in the request sequence because the concrete docket leads and no-record confirmations are the cheapest way to distinguish final reports from petitions, strike rulings, ULP decisions, and representation decisions.
- Put Somerville first among city/school RAO targets because its two high-scoring police awards remain the most important current document-type confound.

**Surprises/breakage**
- None. The recon memo was present, so no fallback search or reconstruction was needed.
- `ingest/test_pipeline.py` was not run because no code or ingestion logic changed.

**Corpus snapshot**
```text
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Submit manually first: DLR master request, then Somerville city/school request, then Boston BTU `PS-17-5987` and Newton custodians/NTA verification requests.
2. Process returned records only after full documents are local: save under `inbox/foia/`, complete manifest metadata, first-page/entity-check the source, verify `source_type`, then use the ingestion pipeline.
3. v9 GABRIEL is still not justified until at least one genuine non-safety factfinding or interest-arbitration document is ingested and validated.

---

## 2026-06-23 — MA non-safety factfinding acquisition queue

**Did**
- Ran the required schema and coverage checks before editing: `scripts/validate.py` passed, and `ingest/audit_coverage.py` still reports 12 contracts, 5 cities, 2 healthy matched pairs, and 4 unmatched safety observations.
- Audited the current Massachusetts gap: Somerville, Boston, and Newton are the highest-value non-safety factfinding targets because their current safety rows are award-heavy and not same-cycle matched to non-safety award-style documents.
- Created `docs/acquisition/ma_non_safety_awards_2026-06-23.md` with a priority gap table, candidate/search-lead table, source-route notes, and manual-download/metadata instructions.
- Checked targeted official/public routes: Mass.gov JLMC decisions, Mass.gov DLR search/API results, and FY2015/FY2016/FY2024 DLR annual reports.

**Decisions and why**
- Did not add `contracts.csv` rows. No genuine non-safety factfinding or arbitration PDF was locally present, source-type verified, and ready for ingestion.
- Treated the Mass.gov JLMC page as safety-only. It is useful for future police/fire award targets, but it cannot provide non-safety comparators.
- Prioritized Somerville first because two police observations remain unmatched and a teacher/clerical factfinding report would directly test whether high Gabriel language is driven by safety status or award-document form.
- Treated the Newton Teachers Association 2023-2024 impasse trail as a future Newton-2025 pairing lead, not a comparator for the current 2015-2018 Newton police row.

**Surprises/breakage**
- Mass.gov search is a JavaScript app, but its official search API was usable with the public site referrer.
- Official hits were mostly DLR hearing-officer, CERB, prohibited-practice, representation, or strike-petition records rather than wage factfinding reports.
- DuckDuckGo HTML returned an anti-bot challenge during exact searches, so it was not used as an acquisition route.
- Three DLR annual-report PDFs were downloaded to `/tmp` for audit only; no source PDFs were staged in the corpus or inbox.

**Corpus snapshot**
```text
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Manual downloads still needed: Somerville teacher/SMEA DLR factfinding if it exists; Newton NTA 2023-2024 factfinding or binding-arbitration output if produced; Boston SENA/BTU non-safety factfinding if available.
2. Documents ready for ingestion: none.
3. v9 rerun: not justified until at least one genuine non-safety factfinding/arbitration document is ingested and validated.

---

## 2026-06-23 — GABRIEL v8 quote-quality hardening for comparability

**Did**
- Updated `analysis/gabriel_pilot/run_gabriel.py` for v8: default output is now `results_v8.csv`; v7 outputs are untouched.
- Added one bounded retry call per document for initially verbatim-failed excerpts. Retry replacements must pass the same `_verify_verbatim` guard before relevance classification.
- Tightened relevance handling: only verbatim + relevant excerpts enter `supporting_quotes`/`estimated_pages`; verbatim-but-irrelevant excerpts remain in `flagged_quotes`/`flagged_pages` as audit trail.
- Added v8 count columns: `excerpts_retry_attempted`, `excerpts_retry_recovered`. Existing v7 count columns are preserved; `excerpts_failed` now means final unrecovered verbatim failures after retry.
- Codified the wage-specific boundary in prompt/rules/tests/docs: wage/salary/pay/total-comp/benefit/longevity-pay peer comparisons can count; generic non-wage provision charts and generic cross-community variation are flagged/ignored.
- Added synthetic relevance-helper tests to `ingest/test_pipeline.py`.
- Ran GABRIEL v8 on 12 documents. Output: `analysis/gabriel_pilot/results_v8.csv`.

**V7 → V8 quote-count comparison (SPSOA/SPEA)**
| doc_id | v7 score | v8 score | v7 sub/rel/flag/fail | v8 sub/rel/flag/fail | v8 retry attempted/recovered |
|---|---:|---:|---:|---:|---:|
| `ma_somerville_police_spsoa_2012` | 92 | 92 | 4 / 2 / 2 / 0 | 6 / 4 / 2 / 0 | 0 / 0 |
| `ma_somerville_police_spea_2012` | 82 | 85 | 5 / 2 / 2 / 1 | 5 / 2 / 3 / 0 | 1 / 1 |

**Decisions (and why)**
- Retry does not change scores. It only repairs quote provenance, because scores should reflect the original document-level judgment, not whether a support quote was recovered.
- Relevance failures are explicit audit records, not support. This keeps irrelevant-but-real text out of verified support counts while preserving traceability.
- The longevity-pay boundary is wage-specific: prose comparing pay levels across communities can support H1; generic charts/tables that merely show variation are not support.

**Surprises / breakage**
- The first v8 command failed under sandboxed network access with connection errors and wrote an all-error `results_v8.csv`; reran with approved network access and overwrote it with the completed v8 run.
- After final helper tightening, reran v8 again so `results_v8.csv` matches the final code.
- Retry recovered 1 of 1 attempted Somerville failed excerpts in the final run, eliminating unrecovered verbatim failures there; this is useful but too small to prove retries solve persistent long-form award paraphrases.
- SPEA produced one additional flagged/ignored excerpt under the stricter boundary while preserving 2 relevant support excerpts and a high score.

**Tests / validation**
- `python ingest/test_pipeline.py` — 35 passed, 0 failed.
- `python scripts/validate.py` — passed.
- `python ingest/audit_coverage.py` — passed and produced the snapshot below.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Acquire non-safety arbitration awards; this remains the primary H1 gap needed to separate occupation effects from document-type effects.
2. Treat persistent Somerville long-form award paraphrase failures as a known quote-recovery limitation unless future runs show retries materially improve relevant support.
3. If v8 outputs are used in downstream summaries, report `excerpts_relevant` as verified support and `excerpts_flagged`/`flagged_quotes` only as audit evidence.

---

## 2026-06-22 — Port LLM fallback to OpenAI/Harvard; add AGENTS.md for Codex

**Did**
- Added `AGENTS.md` at repo root — identical copy of `CLAUDE.md`. Both files coexist so either Claude Code or Codex can read project instructions.
- Rewrote `ingest/extract_spans.py` `llm_pass()` to use the Harvard HUIT OpenAI proxy instead of the Anthropic API. Changes: env var `ANTHROPIC_API_KEY` → `HARVARD_SUBSCRIPTION_KEY`; `import anthropic` → `from openai import OpenAI`; Harvard endpoint + header pattern (same as `run_gabriel.py`); `client.chat.completions.create()` + `resp.choices[0].message.content`; `max_completion_tokens` (required by gpt-5.4-nano as a reasoning model); default model `claude-sonnet-4-6` → `gpt-5.4-nano`. Prompt content and `_verify_verbatim` anti-paraphrase guard left exactly unchanged.
- Updated `ingest/README.md` "LLM fallback setup" section: replaced `ANTHROPIC_API_KEY` / `claude-sonnet-4-6` with `HARVARD_SUBSCRIPTION_KEY` / `gpt-5.4-nano`; noted that the fallback now uses the same credential as the GABRIEL scripts.
- Updated root `README.md` "Added dependencies" section: replaced `anthropic` package / `ANTHROPIC_API_KEY` with `openai` / `HARVARD_SUBSCRIPTION_KEY`.
- Updated `requirements.txt`: removed `anthropic>=0.39`; added `openai>=1.0` (was already installed for GABRIEL scripts but not listed here).
- Confirmed no remaining `anthropic` / `ANTHROPIC_API_KEY` references outside of the historical 2026-06-15 PROGRESS.md entry (correct — not edited).

**Decisions (and why)**
- Unified credential: the project previously needed two separate API keys (`ANTHROPIC_API_KEY` for ingest, `HARVARD_SUBSCRIPTION_KEY` for GABRIEL). The fallback was already optional and off-by-default; porting it to the same Harvard endpoint removes the only remaining Anthropic dependency, simplifying setup and keeping all LLM calls on the institutional proxy.
- `gpt-5.4-nano` chosen for consistency with `run_gabriel.py` (same model in active use; same proxy; same pricing). The model is a reasoning model so `max_completion_tokens` replaces `max_tokens`.
- AGENTS.md is a verbatim copy of CLAUDE.md — no content divergence between the two agent instruction files.

**Surprises / breakage**
- None. `reportlab` was not installed in the active environment (needed by `test_pipeline.py` to build synthetic PDFs); installed it and all 26 tests passed. `scripts/validate.py` passed clean (corpus unchanged).

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
- (Unchanged from session 9.)

---

## 2026-06-19 (session 9) — v7 run: prompt exclusions + relevance re-check; DPW 2018 fixed

**Did**
- Added three new exclusion rules to `run_gabriel.py` PROMPT_TEMPLATE, extending the COLA/CPI note:
  1. "market adjustment" does not count as comparability unless text explicitly states the adjustment is based on wages paid by OTHER employers/jurisdictions.
  2. Bargaining unit names/abbreviations (e.g. "AFSCME: MC", "Local 490") are NOT peer jurisdictions.
  3. Award-outcome sentences (e.g. "the Panel awards X% for FY2014") are NOT comparability reasoning unless the same sentence also states the comparative justification.
- Added two-stage relevance check on verbatim-verified excerpts:
  - Stage 1 (rule-based): `_is_clearly_relevant` (keyword list) → pass; `_is_clearly_irrelevant` (award-outcome/market-adj/ruling-conclusion patterns) → flag; else ambiguous.
  - Stage 2 (model): ambiguous excerpts sent to model for binary yes/no relevance judgment.
  - Flagged excerpts (verbatim-pass, relevance-fail) go to `flagged_quotes`/`flagged_pages`; they are NOT silently discarded. New output columns: `excerpts_relevant`, `excerpts_flagged`.
- Fixed `max_completion_tokens`: raised 2000 → 4000 after first run failed on SPEA (SPEA at 256K chars + longer prompt exhausted the 2000-token cap).
- Fixed `_RELEVANCE_STRONG`: added curly-apostrophe variant of `"that city's or town's"` to catch the Arlington fire "outside detail rate" clause (PDF used curly apostrophes; the keyword was a straight apostrophe → match failed on first run).
- Updated `docs/hypotheses.md` H1 measurement boundary: documented that verbatim verification confirms quotes are REAL but not RELEVANT; described both failure modes found in v6 (market-adjustment label + award-outcome sentence).
- Ran GABRIEL v7 on 12 documents (second clean run after fixes). Output: `results_v7.csv`.

**V6 → V7 comparison**
| doc_id | v6 score | v7 score | Δ | sub | rel | flag | fail |
|--------|---------|---------|---|-----|-----|------|------|
| worcester_fire_2017 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_clerical_admin_2017 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_public_works_2017 | 5 | 10 | +5 | 2 | 0 | 1 | 1 |
| boston_police_2020 | 0 | 6 | +6 | 0 | 0 | 0 | 0 |
| boston_clerical_admin_2023 | 8 | 5 | −3 | 0 | 0 | 0 | 0 |
| **somerville_police_spsoa_2012** | **88** | **92** | **+4** | **4** | **2** | **2** | **0** |
| somerville_police_spea_2012 | 82 | 82 | 0 | 5 | 2 | 2 | 1 |
| arlington_fire_2021 | 25 | 30 | +5 | 1 | 1 | 0 | 0 |
| arlington_public_works_2015 | 0 | 8 | +8 | 0 | 0 | 0 | 0 |
| **arlington_public_works_2018** | **25** | **10** | **−15** | **0** | **0** | **0** | **0** | ← FIXED |
| arlington_public_works_2021 | 0 | 5 | +5 | 0 | 0 | 0 | 0 |
| newton_police_2015 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Arlington DPW 2018 — false positive fixed**
Score dropped 25 → 10. The model submitted 0 excerpts: the new exclusion rules ("market adjustment" without explicit external employer reference; bargaining unit abbreviations are not peer jurisdictions) caused the model not to treat the "AFSCME: MC market adjustment" passages as comparability evidence. Score 10 is in the 0–15 "no comparability" band — plausible; the document has internal salary schedule changes only. The v4 score (12) and v5 score (10) bracketed this same range; v6's 25 was the anomaly.

**SPSOA — 2 confirmed relevant excerpts; 2 correctly flagged**
Score increased 88 → 92 (still firmly in the 71–100 "primary justification" range). 4 submitted, 2 verbatim-pass + relevant, 2 verbatim-pass + flagged:
- RELEVANT [1]: "In the Police Arbitration Award the Panel decided to review a listing of comparable communities that was utilized by the Collins Center..." (genuine comparability frame)
- RELEVANT [2]: "The evidence further demonstrates that the overall compensation (including wages and benefits) provided to Somerville Police Superiors, although not the same, is comparable to what is provided to poli[ce in other communities]" (direct wage comparison)
- FLAGGED [1]: "The parties' proposals on wages and duration are as follows: CITY'S POSITION..." (proposals table, not comparability reasoning) → escalated to model, flagged
- FLAGGED [2]: "AWARD – DURATION & WAGE INCREASES... FY 2013 – 2.5%, FY 2014 – 2%..." → caught by `_is_award_outcome` rule (FY-year + percentage pattern with no comparability keywords)
The v6 run had 6 verified excerpts; v7 has 2 relevant + 2 flagged from 4 submitted. The model selected different excerpts this run (expected variance). The primary finding — high score, genuine comparability justification — is unaffected.

**SPEA — 2 confirmed relevant excerpts; 2 correctly flagged; 1 verbatim-fail**
Score: 82 (unchanged from v6).
- RELEVANT [1]: "wages and benefits of comparable towns" (criterion citation in panel reasoning)
- RELEVANT [2]: "when reviewing longevity payments in other communities the longevity pay for Somerville Police is lower than that provided in other communities, such as Boston, and Lynn." (cross-community comparison, wages tangential but present)
- FLAGGED [1]: "The chart demonstrates that longevity payments vary from community to community..." (cross-community comparison but about payment structure, not wage levels → model escalated, flagged)
- FLAGGED [2]: "As the chart shows alcohol testing for public safety officers is not an unusual contract provision: Community / Alcohol Testing / Arlington / Yes..." (comparison of non-wage contract provisions → model escalated, flagged)
The v6 padding excerpts (FY wage announcement; longevity ruling conclusion) were not submitted in v7 — the new prompt exclusions changed the model's excerpt selection.

**Arlington fire 2021 — outside-detail rate excerpt fixed**
Score: 25 → 30 (minor; still in 16–40 "mentioned in passing" band). The outside-detail rate excerpt ("paid at that city's or Town's outside detail rate") is now correctly classified as RELEVANT. In v7 run 1 it was incorrectly flagged because the PDF uses curly apostrophes (') while `_RELEVANCE_STRONG` only had a straight apostrophe ('). Fixed by adding both variants to the keyword list.

**Relevance check — 4 model escalations (clean run)**
4 excerpts across the 12 documents were ambiguous (not caught by rule-based positive or negative checks) and escalated to the model: 1 from SPSOA (proposals table → flagged), 1 from SPEA (longevity chart → flagged), 1 from SPEA (alcohol testing table → flagged), 1 from Worcester public works (new salary step → flagged). All 4 model escalations returned "no" (not peer-wage comparability). No escalations returned "yes" in this run — the ambiguous excerpts were genuinely borderline-to-irrelevant.

**Spend (v7)**
```
v7 run 1 (failed, SPEA max_tokens): 16 calls, 241,076p + 2,326c = $0.0511
v7 run 2 (clean):                   16 calls, 241,089p + 2,731c = $0.0516
──────────────────────────────────────────────────────────────────────────
v7 total (both runs):                           482,165p + 5,057c = $0.1028

Cumulative (v3–v7, all runs): ~$0.2999  [ESTIMATE — public list pricing; Harvard billed rate may differ]
```
The doubled cost for v7 (two runs) reflects the debugging run needed when SPEA hit the 2000-token cap. The clean run alone ($0.0516) is the marginal cost per 12-document pass.

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. The verbatim-fail rate for SPSOA and SPEA is persistent (model submits paraphrases for some excerpts). Consider whether to add a "re-submit failed excerpts with stricter verbatim instruction" retry loop, or accept that long-form awards will have some verbatim-fail excerpts alongside genuine ones.
2. SPEA's RELEVANT [2] (longevity pay in other communities) and FLAGGED [1] (longevity chart) are both legitimate cross-community observations but differ in whether they reference wages specifically. The current rule (model escalation) flagged the chart but passed the prose version — that distinction seems right but is model-dependent.
3. Non-safety arbitration awards remain the primary corpus gap for the H1 test.

---

## 2026-06-19 (session 8) — v6 run: multi-excerpt schema; SPSOA breakthrough; DPW 2018 flag

**Did**
- Rewrote `run_gabriel.py` SYSTEM prompt to request a list of up to 10 independent verbatim excerpts rather than a single quote. Each excerpt is 1-2 consecutive sentences from a single contiguous passage; excerpts may come from different parts of the document. Each verified separately via `_verify_verbatim`. Output columns changed from `supporting_quote`/`estimated_page` (strings) to `supporting_quotes`/`estimated_pages` (JSON-encoded lists) plus `excerpts_submitted`/`excerpts_verified`/`excerpts_failed` counts.
- Added correction note to session 5 PROGRESS.md entry for v3 cost ($0.036 → $0.048180).
- Ran GABRIEL v6 on 12 documents. Output: `results_v6.csv`.

**V6 excerpt counts (submitted → verified)**
| doc_id | v5 score | v6 score | Δ | submitted | verified | failed |
|--------|---------|---------|---|-----------|----------|--------|
| worcester_fire_2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_clerical_2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_public_works_2017 | 0 | 5 | +5 | 0 | 0 | 0 |
| boston_police_2020 | 5 | 0 | −5 | 0 | 0 | 0 |
| boston_clerical_2023 | 5 | 8 | +3 | 0 | 0 | 0 |
| **somerville_spsoa_2012** | 80 | **88** | +8 | **6** | **6** | **0** |
| somerville_spea_2012 | 75 | 82 | +7 | 9 | 7 | 2 |
| arlington_fire_2021 | 25 | 25 | 0 | 1 | 1 | 0 |
| arlington_dpw_2015 | 0 | 0 | 0 | 0 | 0 | 0 |
| **arlington_dpw_2018** | 10 | **25** | **+15** | **2** | **2** | **0** | ← FLAG |
| arlington_dpw_2021 | 0 | 0 | 0 | 0 | 0 | 0 |
| newton_police_2015 | 12 | 0 | −12 | 0 | 0 | 0 |

**SPSOA: breakthrough — 6 verified, all genuine**
All 6 excerpts passed verification and are substantively distinct comparability passages. Pages 51, 52, 56, 57, 60 — spread across the comparability analysis section. Example:
- p.52: *"The City argues that the wages and benefits of Somerville Superior Officers compare well with their counterparts in other comparable communities, and that Somerville Superior Officers rank at the top in terms of total compensation."*
- p.57: *"The Union's wage proposal for the last three years... is well above the base wage increases that have been agreed to in comparable communities. There is, therefore, no justification for increases of this magnitude..."*

No padding. Each excerpt covers a distinct analytical point (city argument vs. union argument vs. rank differential vs. award reasoning). Score increase 80→88 reflects the model now reading the full comparability section and registering how heavily it dominates the award's reasoning.

**SPEA: 7 verified, 2 padding detected**
7 of 9 submitted excerpts passed verification. Of the 7 verified, 5 are genuine comparability language. Two are padding:
- p.64 excerpt: *"The Panel Awards wage increases for the three-year period: FY 2013 – 2.5%, FY 2014 – 2%, FY 2015 – 2%"* — This is the award outcome, not comparability reasoning. Verbatim and verifiable, but not evidence of comparability language.
- p.77 excerpt: *"Accordingly, based on totality of facts there is insufficient justification to change the current longevity payments at this time."* — A ruling conclusion about longevity, not peer-wage comparison language.
Score (82) is still supported by the 5 genuine excerpts. Padding doesn't change the score, but it dilutes excerpt quality if used for annotation.

**Arlington DPW 2018: FLAG — score increase likely false positive**
Score jumped 10→25 with 2 verified excerpts about "market adjustment of 35 cents / 20 cents to the top step of AFSCME: MC, Office Administrative." These passages are NOT peer-wage comparability:
- "AFSCME: MC" is the bargaining unit abbreviation (AFSCME Municipal Council), not a reference to another municipality or peer wages.
- "Market adjustment" here means an internal salary table correction, not a comparison to wages paid elsewhere.
- The v5 score (10, BACPI-adjacent) and the v4 score (12) are more plausible than 25.
**Do not treat the v6 score of 25 for Arlington DPW 2018 as validated.** The model correctly extracted verbatim text but misread "market adjustment" as peer-wage comparability. The excerpts should be reviewed before use.

**Low-scoring documents — no padding problem**
All 8 documents scoring 0–8 returned 0 excerpts. The anti-padding instruction held: worcester fire, clerical, dpw (5, 0 excerpts), boston police, boston clerical (8, 0 excerpts), arlington dpw 2021, newton police all returned empty excerpt lists. None of these showed the 3+ excerpt inflation the task specified as the failure mode.

**v5 vs v6 cost**
```
v5: 237,891 prompt + 1,504 completion = $0.0495
v6: 238,923 prompt + 2,207 completion = $0.0505  (+703 completion tokens, +47%)
Difference: +$0.0010 for 12 documents
```
Completion tokens increased 47% (expected — model now writes multiple excerpts per document). Cost increase is negligible (~$0.001 per run). The 2,000-token `max_completion_tokens` cap was not hit.

**Corrected cumulative spend (v3–v6, all scripts):**
```
v3 (backfill, corrected): $0.048180
v4 (live):                $0.049001
v5 (live):                $0.049458
v6 (live):                $0.050543
────────────────────────────────────
Total:                    $0.1972  [ESTIMATE — public list pricing; Harvard billed rate may differ]
```

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Arlington DPW 2018 excerpt review: confirm whether "AFSCME market adjustment" language qualifies as comparability. If not, add "market adjustment" to the COLA/non-comparability note in the prompt.
2. SPEA padding: consider adding a filter to strip excerpts that are purely award-outcome sentences (no comparability language in the text itself).
3. Non-safety arbitration awards remain the primary corpus gap for the H1 test.

---

## 2026-06-19 (session 7) — v5 run: contiguous quote constraint + COLA clarification; spend log backfill

**Did**
- Task 1: Tightened quote request in `run_gabriel.py` SYSTEM prompt from open-ended "sentence(s)" to "ONE to TWO consecutive sentences from a SINGLE CONTIGUOUS PASSAGE." Blocks the synthesis failure mode where the model stitches non-adjacent fragments.
- Task 2: Added explicit COLA/CPI boundary to `PROMPT_TEMPLATE`: "cost-of-living index adjustments (CPI, BACPI, or similar) are NOT comparability language — they reference a price index, not other workers' wages." Also added the same clarification to `docs/hypotheses.md` under H1 as a permanent measurement boundary note.
- Task 3: Backfilled v3 run to `logs/api_spend_log.csv` as a manually-flagged row (`run_gabriel.py[v3-backfill]`). Recomputed cost at correct pricing: $0.048180 (v3 PROGRESS.md had reported $0.036 using the old $0.15/$0.60 rate; correct rate is $0.20/$1.25).
- Ran GABRIEL v5 on 12 documents. Output: `results_v5.csv`.

**V4 vs V5 comparison**

| doc_id | v4 score | v5 score | Δ | v4 quote | v5 quote | v5 page |
|--------|---------|---------|---|---------|---------|---------|
| worcester_fire_2017 | 0 | 0 | 0 | N | N | — |
| worcester_clerical_2017 | 0 | 0 | 0 | N | N | — |
| worcester_public_works_2017 | 0 | 0 | 0 | N | N | — |
| boston_police_2020 | 10 | 5 | −5 | N | N | — |
| boston_clerical_2023 | 0 | 5 | +5 | N | FAIL | — |
| somerville_spsoa_2012 | 80 | 80 | 0 | FAIL | FAIL | — |
| somerville_spea_2012 | 78 | 75 | −3 | Y | Y | p.60 |
| arlington_fire_2021 | 10 | 25 | +15 | N | Y | p.20 |
| arlington_dpw_2015 | 5 | **0** | **−5** | Y (BACPI) | N | — |
| arlington_dpw_2018 | 12 | 10 | −2 | Y (BACPI) | N | — |
| arlington_dpw_2021 | 0 | 0 | 0 | N | N | — |
| newton_police_2015 | 10 | 12 | +2 | N | N | — |

**COLA clarification effect (Task 2):**
- Arlington DPW 2015: 5 → 0. The v4 quote was the BACPI sentence ("adjusted to reflect the change in this Boston Adjusted Consumer Price Index"); with the explicit CPI boundary, the model correctly scores it 0 and leaves the quote blank.
- Arlington DPW 2018: 12 → 10 (minor). Notes now explicitly name BACPI as the reason for the low score. Quote dropped.
- No other documents were affected. Nothing that was scoring high due to CPI language — confirming the model was largely already making this distinction, and the clarification only tightened the edge case.

**Quote verification — did the contiguous constraint fix the SPSOA failure?**
No. SPSOA (score=80) failed verification again in v5. The constraint helps in principle (blocks stitching from different parts of the text) but SPSOA's comparability reasoning is distributed across many pages of a 256K-char document; the model cannot find a single 1–2 sentence passage that is both verbatim AND representative. The score (80) is correct — the failure is that the model produces a synthesized summary rather than lifting a verbatim excerpt. Mitigation to consider: cap the quote to a single sentence only, or accept that long-form arbitration awards with multi-page reasoning sections will consistently fail quote verification and treat the score alone as authoritative for those documents.

**New findings in v5:**
- Arlington fire (arlington_fire_2021) scored 25 (+15 from v4) and yielded a verified quote at p.20: "Any outside detail assignment outside the borders of the Town of Arlington shall be paid at that city's or Town's outside detail rate consistent with current practice..." This is a real comparability reference (pay set by reference to another jurisdiction's rate), though for outside details only, not base wages. Score 25 (within the 16–40 "mentioned in passing" band) is plausible. This is the first document outside the Somerville awards to produce a verified non-trivial quote.
- Two new quote failures: SPSOA (persistent) and Boston clerical (score went 0→5, a noise-level shift; the failure means the model tried but couldn't find a verbatim passage, consistent with genuinely low comparability language in that document).

**Qualitative quote quality (v4 vs v5):**
v4 had 3 verified quotes, but 2 were BACPI (CPI-index citations, now correctly excluded). v5 has 2 verified quotes, both genuine comparability language (SPEA's "wages and benefits of comparable towns" at p.60; Arlington fire's outside-detail-rate clause at p.20). Fewer verifications in v5, but higher-quality ones.

**Spend log — corrected total (as of v5):**
```
v3 run (backfill, 2026-06-18): 235,995 prompt + 785 completion = $0.048180  [corrected from $0.036 in session 5 log — used old pricing]
v4 run (live-logged):          236,859 prompt + 1,304 completion = $0.049001
v5 run (live-logged):          237,891 prompt + 1,504 completion = $0.049458
─────────────────────────────────────────────────────────────────────────────
Total (v3–v5):                 710,745 prompt + 3,593 completion = $0.1466

NOTE: All cost figures are ESTIMATES based on public OpenAI list pricing ($0.20/1M input,
$1.25/1M output for gpt-5.4-nano). Harvard's actual billed rate may differ.
```

**Corpus snapshot** (unchanged from session 6)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Decide on SPSOA strategy: single-sentence cap, or accept score-only for dense award documents.
2. Non-safety arbitration awards (JLMC, manual download) remain the primary corpus gap.
3. Consider updating v3 cost note in PROGRESS.md session 5 with the corrected figure.

---

## 2026-06-19 (session 6) — Verbatim quote + page extraction; local spend tracker

**Did**
- Added `page_number_at(text, offset)` helper to `ingest/extract_text.py`. Counts form-feed characters (`\x0c`) before `offset` in pdftotext output and returns a 1-based page number. Only meaningful for text-layer extractions (OCR output has no page markers and always returns 1).
- Added `test_page_number_at()` to `ingest/test_pipeline.py` using a 2-page synthetic PDF with forced `PageBreak()`. Confirmed page 1 and page 2 phrases return correct page numbers. Suite now 26/26 (was 22/22).
- Modified `analysis/gabriel_pilot/run_gabriel.py` to request a verbatim supporting quote alongside the score. Quote is verified using `_verify_verbatim` (same whitespace-normalized substring check as `ingest/extract_spans.py`). On failure: score kept, quote discarded, `gabriel_notes` flagged `[quote_verification_failed]`.
- Added `supporting_quote` and `estimated_page` columns to results output. Page number computed from quote's byte offset in the source text (only populated when `\x0c` page markers are present).
- Created `scripts/log_api_spend.py`. Appends one row per API call to `logs/api_spend_log.csv` (timestamp, script, model, prompt tokens, completion tokens, estimated cost). Also exposes `print_totals()` for end-of-run summaries. Pricing hardcoded as `gpt-5.4-nano: $0.20/1M input, $1.25/1M output` (verified 2026-06-19 via OpenRouter). **All cost figures are estimates based on public list pricing — Harvard's actual billed rate may differ due to institutional terms.**
- Ran GABRIEL v4 on 12 documents. Output: `results_v4.csv` (adds `supporting_quote`, `estimated_page` to v3 schema).

**V4 results**
- 3 documents returned verified quotes with page numbers.
- 1 quote verification failure: `ma_somerville_police_spsoa_2012` (score=80, quote discarded — model paraphrased rather than quoting verbatim; score retained).
- 8 documents scored 0–12 with empty or discarded quotes (correct: no comparability language → no meaningful quote to extract).

**Example verified quote (Somerville SPEA, p.53, score=78):**
> "In reaching the conclusions in the present award, the Arbitration Panel has considered the criteria set forth in the statute including the municipality's ability to pay, wages and benefits of comparable [communities]..."

**Example low-score quote (Arlington DPW, p.9, score=5):**
> "Hereafter the car allowance shall be adjusted to reflect the change in this Boston Adjusted Consumer Price Index (BACPI)." — Correctly low: a price index, not peer wage comparability.

**Spend log (first session):**
```
run_gabriel.py: 12 API calls
  prompt tokens:     236,859
  completion tokens: 1,304
  estimated cost:    $0.0490  [ESTIMATE — list pricing, not Harvard billed rate]
```

**Surprises**
- Quote verification failure on SPSOA (the longer of the two Somerville awards). The document has extensive comparability language but the model synthesized rather than copied verbatim. This is expected for dense, multi-paragraph comparability sections — the model finds it easier to paraphrase a long passage than to select and copy a single sentence. A possible mitigation: ask for a single sentence (≤50 words) rather than "sentence(s)". Not fixed this session.
- Both Arlington DPW 2015 and 2018 returned the exact same quote (the BACPI car-allowance sentence from p.9). This is verbatim and correctly verified — but it reveals that the model is anchoring on the same passage across documents, likely because it's the only quasi-external benchmark in both contracts. The `[quote_verification_failed]` flag is not tripped because the quote is real; it just isn't strong evidence of comparability.

**Corpus snapshot** (unchanged from session 5)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. Tighten quote prompt to request a single sentence (≤50 words) to reduce paraphrase failures.
2. Backfill v3 spend data into `api_spend_log.csv` (current log starts from v4 only — v3 cost was $0.036).
3. Non-safety arbitration awards (JLMC, manual download) remain the primary corpus gap.

---

## 2026-06-18 (session 5) — Harvard API wired; GABRIEL v3 full-text run; report_v3.md

**Did**
- Wired Harvard HUIT OpenAI proxy into `run_gabriel.py`. Credential: `HARVARD_SUBSCRIPTION_KEY` (single env var, stored in `.env` at repo root — added to `.gitignore`). The subscription key serves as both the `api_key` and the `Ocp-Apim-Subscription-Key` header; no separate OpenAI key is needed. Added `python-dotenv` to handle `.env` loading. Added `.env.example` documenting required variables. Scanned repo for hardcoded `sk-` strings — none found.
- Confirmed Harvard endpoint works: `gpt-5.4-nano` responded correctly (base_url and header confirmed in use).
- Raised `MAX_TEXT_CHARS` from 12,000 to 300,000 to send full document text. All 12 docs fit within 300K chars (largest: Somerville SPEA at 256K chars / ~64K tokens, ~16% of model's 400K-token context window).
- Ran GABRIEL v3 on 12 documents. Actual cost: $0.036 (235,995 prompt + 785 completion tokens). *(Corrected in session 7: $0.036 used old pricing $0.15/$0.60; correct rate $0.20/$1.25 gives $0.048180 — spend log updated.)*
- Generated v3 PNGs (`graph1_v3`, `graph2_v3`, `graph3_v3`). Fixed y-axis auto-scaling in `plot_results.py` so bars are not clipped when scores exceed 35.
- Wrote `analysis/gabriel_pilot/report_v3.md` (attribute definition, comparison table, captioned figures, summary with honest read on results).

**V1 / V2 / V3 comparison**

| Version | Model | Truncation | Score range | Safety mean | Non-safety mean | arbitration_award mean | cba mean |
|---------|-------|------------|-------------|-------------|-----------------|------------------------|----------|
| v1 | gpt-4o-mini | 12,000 chars | 10–20 | 16.7 | 13.3 | 15.0 | 14.3 |
| v2 | gpt-5.4-nano | 12,000 chars | 0–10 | 0.8 | 2.5 | 2.5 | 1.5 |
| v3 | gpt-5.4-nano | 300,000 chars | 0–85 | 28.8 | 3.3 | 81.5 | 3.0 |

**V3 produced real score spread.** The two Somerville police arbitration awards (2012) scored 78 and 85 — highest in the batch. The remaining 10 CBAs/MOAs scored 0–15. This is the expected pattern: arbitration awards contain the arbitrator's written reasoning (which cites named peer communities to justify the wage decision); CBAs record the agreed outcome without the reasoning.

**Surprises / results**
- **The truncation bug was the entire story.** At 12K chars, the arbitration awards were being read in their procedural header only (parties, stipulated facts, submission). The comparability analysis — which runs 10–50 pages deep in these documents — never reached the model. Raising to full text immediately produced the expected high scores.
- **Safety vs. non-safety gap (28.8 vs. 3.3) is confounded with document type.** The safety sample has two arbitration awards; the non-safety sample has zero. This is not a clean test of the safety hypothesis. To isolate occupation class from document type, the next run needs non-safety arbitration awards (e.g., JLMC awards for teacher or clerical units in the same cities).
- **CBA mean near-zero (3.0) is coherent, not a floor artifact.** CBAs for all five cities contain wage schedules, step tables, and COLA provisions but no explicit comparability reasoning. If anything, this is the baseline: the comparability text lives in the award documents, and whether it translates into CBA language that persists contract-to-contract is an open empirical question.

**Corpus snapshot** (unchanged from session 4)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **More documents — JLMC awards.** Manual browser download from mass.gov (still Akamai-blocked from CLI). Priority: arbitration awards for non-safety units to allow document-type-controlled comparison.
2. **Discuss safety/non-safety confound with Andrei.** The right specification (CBA-only, award-only, or mixed) affects what the attribute measures and how to interpret it.
3. **Scale to other states.** Massachusetts JLMC is the starting point. Pennsylvania PLRB, New York PERB, Michigan MERC next.
4. **Attribution spot-check.** Before scaling to >50 documents, do a 5-doc manual verification that scores are tracking comparability text, not document length or complexity.

---

## 2026-06-18 (session 4) — OCR install, model fix, anchored attribute, GABRIEL v2

**Did**
- Installed `pytesseract` + `pdf2image` Python wrappers (Tesseract 5.5.2 and poppler were already present system-wide). All 3 previously-skipped rows now OCR successfully: Worcester fire (9,808 chars, ocr_messy), Boston police MOA (14,832 chars, ocr_messy), Newton police CBA (127,200 chars, ocr_messy). input.csv rebuilt with 12/12 rows having real text.
- Corrected model: `gpt-5.4-nano` (released 2026-03-17) confirmed live via API. V1's substitution of `gpt-4o-mini` was wrong. Reasoning model differences: no `temperature` param, use `max_completion_tokens` not `max_tokens`, `reasoning_effort` is supported.
- Replaced vague attribute prompt with explicit behavioral anchors (0–15 / 16–40 / 41–70 / 71–100), requiring the model to cite specific textual evidence rather than picking a default bucket. Updated `run_gabriel.py`; added `--output` flag to write `results_v2.csv` without overwriting v1.
- Added `--results` / `--suffix` flags to `plot_results.py`; generated 3 v2 PNGs alongside v1 originals for side-by-side comparison.
- Cost v2: $0.0050 (30,108 prompt + 836 completion tokens, includes reasoning tokens).

**V1 vs V2 score comparison**

| | V1 (gpt-4o-mini, vague prompt) | V2 (gpt-5.4-nano, anchored) |
|---|---|---|
| Rows scored | 9/12 (3 skipped — no text) | 12/12 (OCR recovered) |
| Score range | 10–20 only | 0–10 only |
| Non-safety mean | 13.3 | 2.5 |
| Safety mean | 16.7 | 0.8 |
| Notes quality | Near-identical boilerplate | Specific clause citations per doc |

V2 is clearly reading more carefully — every note cites specific contract language. But scores collapsed toward zero rather than spreading across the 0–100 range. See "Surprises" below.

**Surprises / results**
- **Scores still near-floor in v2, but for a different and diagnosable reason.** V1's flat 10/20 scores were model laziness (vague prompt → default anchors). V2's near-zero scores are structurally correct: the first 12,000 chars of a CBA or arbitration award are invariably recognition clauses, management rights, grievance procedures — not the wage articles. The model correctly finds no comparability language because we're not feeding it the right section. This is a text-extraction problem, not a scoring problem.
- **Safety mean LOWER than non-safety in v2 (0.8 vs 2.5).** Counterintuitive if the hypothesis is that safety wages are comparability-driven. But both are near-zero and the difference is noise at n=6. Not a finding; artifact of which sections land in the first 12K chars of each document.
- **Arbitration awards scored the same as CBAs (2.5 vs 1.5).** The two Somerville SPEA/SPSOA awards are 230K+ chars; their comparability reasoning is deep in the body and not captured at 12K truncation. This is the strongest evidence that MAX_TEXT_CHARS is the binding constraint.

**Root cause and fix needed**
The 12,000-char truncation (`MAX_TEXT_CHARS`) cuts off before wage articles in long documents. Fix options in priority order:
1. **Smarter section targeting** — extract the last N chars of the document (or a middle window), or use keyword search to locate "wage"/"salary"/"comparab" sections before sending to the model.
2. **Raise MAX_TEXT_CHARS for awards** — the Somerville awards at 230K+ would be expensive at full length (~57K tokens each), but targeting 50K chars would land in the reasoning sections at reasonable cost.
3. **Chunk and max-score** — split each doc into 12K windows, score each, take the max. Adds ~5-10x API calls per long document.
Option 1 is the right next step before adding JLMC awards.

**Corpus snapshot** (unchanged from session 3)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **Fix text window in `run_gabriel.py`** — implement tail-window extraction (e.g., last 15K chars or a wage-section keyword scan) before re-running. This is the prerequisite before adding more documents.
2. **Add JLMC awards via browser download** — all 11 mass.gov URLs blocked from CLI; manual browser download needed. Once in corpus, rebuild input.csv and run v3.
3. **Newton + Arlington police** — manual downloads still needed (Akamai-blocked). 

---

## 2026-06-18 (session 3) — GABRIEL pilot: end-to-end scoring run + graphs

**Did**
- Confirmed Task 1 (obs_id dedup fix in `ingest/pipeline.py` + `process_inbox.py`) was already completed in the prior session — `_existing_obs_ids()` guard is live and green.
- Built `analysis/gabriel_pilot/` with `build_input.py`, `run_gabriel.py`, and `plot_results.py`. Input assembled from all 12 `contracts.csv` rows (text via `extract_text.py`). JLMC award downloads attempted but mass.gov returned 403 for all 11 URLs in `ma_award_inventory.csv` (Akamai block — requires browser session). Proceeded with 12 rows.
- Ran GABRIEL scoring: model `gpt-4o-mini`, temperature=0, `reasoning_effort` N/A (not a reasoning model), `response_format=json_object`. Attribute: `comparability_emphasis` (0–100). Previous run had all 401s from bad API key; re-ran with valid key. 9/12 rows scored; 3 skipped (Worcester fire, Boston police, Newton police — zero extractable text).
- Cost: $0.0032 (20,073 prompt + 234 completion tokens).
- Generated 3 graphs saved as PNGs in `analysis/gabriel_pilot/`: safety vs non-safety average, by source type, score-by-year scatter. Validator passes (12/0/12/3).

**Decisions (and why)**
- **Proceeded with 12 rows instead of target ~35–40.** mass.gov JLMC PDFs are Akamai-blocked from CLI for all 11 award URLs. Pilot's purpose is workflow practice, not statistical power — 12 rows is sufficient to exercise the end-to-end pipeline.
- **Used `gpt-4o-mini` instead of "gpt-5.4-nano" (no such model).** Cheapest production OpenAI chat model; no reasoning-effort parameter on chat completions. Noted in script header.

**Surprises / results**
- **Scores are flat: all 10 or 20.** Notes are nearly identical ("minimal references to comparability"). This is plausible for negotiated CBAs — comparability language appears prominently in arbitration *reasoning*, less so in CBAs which are concluded agreements. Two Somerville police awards (arbitration_award source_type) scored 10 and 20 — same range as CBAs. The model may be correct that explicit comparability language is sparse in these documents. Escalating to `reasoning=medium` or expanding to true JLMC awards with actual arbitrator reasoning sections would test whether the attribute is estimable at all.
- **Graph results (not findings — workflow practice only):** safety mean = 16.7, non-safety mean = 13.3 (n=3 vs n=6). arbitration_award mean = 15.0, cba mean = 14.3 (n=2 vs n=7). Differences are within noise at this scale.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018
  - Somerville SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **Get JLMC awards via browser** — all 11 mass.gov URLs in `ma_award_inventory.csv` need manual browser download (curl/requests blocked). Download to `inbox/`, add manifest rows, run `process_inbox.py` to add to corpus. This will bring arbitration awards with actual comparability reasoning into the GABRIEL run.
2. **Re-run GABRIEL with awards** — once JLMC PDFs are in `scratch_pdfs/`, rebuild `input.csv` and re-score. If all scores remain flat (10–20), revisit the attribute definition or switch to a more discriminating attribute (e.g., "arbitrator explicitly cites neighboring-city wage tables").
3. **Newton + Arlington police** — manual downloads still needed (Akamai-blocked). Priority: NPA FY19-FY21 + AFSCME 3092 FY20-FY24 to close Newton matched-pair gap.
4. **OCR install** (deferred) — Worcester fire and Boston police have ~0 extractable text; those rows will remain unscored until Tesseract is installed.

---

## 2026-06-17 (session 2) — Arlington IA collection + Newton portal mapping

**Did**
- Discovered the previous session's `ma_arlington_police_cba_2020_2022.pdf` was a wrong-jurisdiction file — Revize CMS path `revize/arlington` serves **Arlington Heights, IL** (Village, Metropolitan Alliance of Police Chapter 510), not Arlington, MA (Town). Renamed with `DISCARD_` prefix.
- Found Arlington MA's full document archive on Internet Archive (`Arlington_MA_ShowDocument_Id_*` collection). Identified all CBA-related items (fire, AFSCME, SEIU, RLPA). RLPA = Robbins Library Professional Association (library employees).
- Downloaded 3 Arlington CBAs from IA: IAFF Local 1297 fire FY2022-2024 (Jul 2021–Jun 2024, 44 pp, IA OCR); AFSCME Local 680 FY2018-2021 (Jul 2018–Jun 2021, 31 pp, clean); AFSCME Local 680 FY2021-2024 (Jul 2021–Jun 2024, 35 pp, poor OCR). FY2016-2018 AFSCME already in inbox from previous session.
- Extracted wage rates from AFSCME FY2018-2021: FY2019 = 2% + $0.35 market adj (Jan 2019), FY2020 = 2% + $0.20 market adj (Jan 2020), FY2021 = 1%. Fire FY2022-2024: Step 7 comparison gives ~4.84% (FY2023) and ~4.46% (FY2024).
- Wrote 5 manifest rows (Arlington fire, AFSCME ×3, Newton police LRIS), ran `process_inbox.py`, deduplicated re-ingested rows from contracts.csv and city_coverage.csv (pipeline has no skip-already-processed guard — see breakage note below).
- Mapped the full Newton union roster via IA snapshot of newtonma.gov (Dec 2025): identified AFSCME Local 3092 City Hall Associates (clerical, folder 445), Teamsters Local 25 DPW (folder 452), Newton Police Association (folder 450). Found document IDs for priority Newton downloads.
- **Git commits:** this session

**Decisions (and why)**
- **`occupation_class = public_works` for Arlington AFSCME Local 680.** The recognition clause covers "Labor Service including foremen" (DPW, custodians) as the primary unit, plus clerical grades. Labor Service is the larger portion; `public_works` is more accurate for the GABRIEL comparator than `clerical_admin`. Note in total_comp_note that the unit also includes clerical grades.
- **Fire (not police) as Arlington safety unit for now.** JLMC award JLMC-22-9174 for Arlington Police (APPA, May 2023, neutral Bonnie J. McSpiritt) is blocked by Akamai on mass.gov. The fire IAFF Local 1297 CBA is fully accessible via IA and creates a valid matched pair with the AFSCME FY2021-2024 (exact same Jul 2021–Jun 2024 cycle). Police can be added once mass.gov is reachable.
- **Newton police LRIS file logged as `partial` with estimated cycle dates.** The 43 MB scanned PDF has ~0 extractable text and an unknown cycle. File creation date (March 2018) suggests FY15-FY18. Flagged as ESTIMATED in total_comp_note. Portal confirms the correct document is NPA CBA FY15-FY18 (doc 65551) — same file, more reliable dates once OCR is available.

**Surprises / breakage**
- **Revize CMS namespace collision.** `cms2.revize.com/revize/arlington` is Arlington Heights, IL — not Arlington, MA. The URL appeared in a Google search result labeled "2020-2022 Police Contract" and was believable. Verified by reading the PDF text (Village, MAP union). Always read the first page of any document before writing a manifest row.
- **`process_inbox.py` re-ingests all manifest rows on every run.** No "processed" flag or archive mechanism exists. Running it a second time after adding new rows recreated all prior rows as duplicates, breaking validation. Fixed manually by deduplicating contracts.csv and city_coverage.csv. **Long-term fix needed:** either move processed manifest rows to `inbox/manifest_archive.csv` after each run, or add an obs_id existence check in `ingest/pipeline.py` before writing.
- **Newton portal documents are not individually archived on IA.** The newtonma.gov folder pages (AFSCME 3092 folder 445, NPA folder 450, Teamsters folder 452) ARE archived in December 2025 IA snapshots, and these reveal document IDs. But each showpublisheddocument URL resolves to an Akamai-blocked direct download with no IA copy. Manual browser download from newtonma.gov is the only route.
- **Arlington fire wage increases are high (~4.65% avg FY2023-FY2024).** Not a data error — this covers Jul 2021–Jun 2024, the high-inflation period. Cross-check against Newton and other cities when available.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025          [cycle gap vs SENA 2023-2027]
  - Somerville SPSOA 2012-2018       [no non-safety collected]
  - Somerville SPEA 2012-2015        [no non-safety collected]
  - Newton police 2015-2018 (est.)   [no non-safety collected]
```

**Next steps**
1. **Newton — manual browser download required** (all Akamai-blocked from CLI):
   - NPA Police CBA FY19-FY21: `https://www.newtonma.gov/home/showpublisheddocument/119347`
   - AFSCME 3092 FY20-FY24 MOA: `https://www.newtonma.gov/home/showpublisheddocument/78310`
   - Teamsters Local 25 FY20-24 MOA: `https://www.newtonma.gov/home/showpublisheddocument/77786`
   - The FY19-FY21 police + FY20-FY24 AFSCME pair would close Newton's matched-pair gap.
2. **Arlington police** — manual browser download of JLMC-22-9174 award: `https://www.mass.gov/doc/jlmc-22-9174-arlington-police-award/download`
3. **Fix process_inbox.py re-ingestion.** Add obs_id existence check or archive processed manifest rows.
4. **Install pytesseract + tesseract + poppler** (`pip install pytesseract pdf2image` + `brew install tesseract poppler`) before next OCR-heavy batch (Newton police LRIS, Boston BPPA MOA).
5. **Somerville non-safety (SMEA/SMEU)** — FOIA still the only route (unchanged).
6. **Boston clerical ~2019-2023** — predecessor SENA or SEIU 888 cycle to close Boston matched-pair gap (unchanged).
7. **Worcester c.66 FOIA** — still pending PI/RA submission (unchanged).

---

## 2026-06-17 — MA source inventory verification + Boston/Somerville ingest

**Did**
- Verified all 6 city URLs from `docs/ma_source_inventory.md`. Found 4 usable public sources; 2 cities (Quincy, Somerville HR) have no portal-hosted PDFs; 2 cities (Arlington, Newton) return HTTP 403 to automated fetchers.
- Downloaded 4 PDFs from confirmed-public sources (Boston OLR portal, Somerville MuckRock FOIA release). Inspected each with `pdftotext` + `pdfimages` before writing any manifest row.
- Ingested all 4 via `process_inbox.py` → `data/contracts.csv` + `data/city_coverage.csv`. Fixed a post-ingest duplicate obs_id. Added `city_attributes` rows for Worcester, Boston, Somerville. Validate and audit clean.
- **Git commit:** 9b9cc22

**Decisions (and why)**
- **`source_type = arbitration_award` for both Somerville docs.** The MuckRock release is an integrated document — base CBA (1997/2004) with all successive JLMC arbitration awards appended. The terminal document governing wages is the award, not the base CBA, so that's the type we record. This keeps the schema-type aligned with what GABRIEL will score.
- **Separate obs_ids for SPSOA and SPEA.** Both Somerville police units have `cycle_start = 2012-07-01`, so the pipeline's auto-generated key (`{city_id}_{occ}_{year}`) collided. Fixed by patching obs_ids to `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012`. Future mitigation: pass explicit `obs_id` in the manifest (the pipeline already accepts it from meta).
- **Included the BPPA MOA despite partial quality and no mechanism clauses.** A wage MOA is still valid for the dependent variable (pct_increase_annual). It creates the Boston safety row needed for the matched-pair structure. Mechanism fields are empty — correct for an MOA — and the `total_comp_note` says so explicitly.
- **pct_increase_annual on multi-year variable-rate awards:** used simple average — SPSOA 0.0225 (rates of 2.5/2/2/2/2.5/2.5% over 6 years), SPEA 0.022 (2.5/2/2% over 3 years). Same approach as prior Worcester rows.
- **Boston non-safety: chose SENA Local 9158 over SEIU 888 or AFSCME.** SENA is the most cleanly `clerical_admin`-typed unit; the portal name is explicit. SEIU 888 at Boston covers a wider range of occupations and would require more classification judgment.

**Surprises / breakage**
- **Boston portal posts MOAs for all safety units, full CBAs for non-safety.** BPPA (2020-2025) and IAFF Local 718 (2021-2024) are both explicitly labeled "MOA" in filenames and are 6-page scanned documents. Non-safety units (SENA, SEIU 888, AFSCME, OPEIU 6) all have 40–50-page full CBAs on the same portal. This is the same gap as Worcester: safety wages are negotiable but mechanism clauses are in older unreachable base CBAs. The SENA CBA keywords confirmed: `arbitration`, `binding arbitration` — non-safety has mechanism content that the safety MOA lacks.
- **BPPA PDF is entirely scanned phone-photos** (6 pages, all JPEG images at 150–300 dpi), not even scanner-grade. `pdftotext` → 0 chars; `extract_text.py` → 0 OCR chars (pytesseract not installed). Filed as `text_quality=partial`. Cycle dates estimated from portal title (2020-2025).
- **Somerville SPEA has a "parity" clause keyword** — distinct from the SPSOA, which doesn't. Parity clauses are a core GABRIEL measurement target; worth flagging for the analyst as a candidate for the comparability referent field.
- **Somerville SPSOA 6-year award.** One arbitration decision (May 2018, Gary D. Altman neutral) settled two consecutive 3-year cycles (2012-2015 and 2015-2018) in a single award, because the patrolmen's SPEA award was adopted by reference for the first period. Represented as one row spanning 2012-2018 rather than splitting — GABRIEL will score it from the single document.
- **Boston matched pair cycle gap.** BPPA safety unit (2020-2025) and SENA non-safety (2023-2027) have different `cycle_window` keys, so `audit_coverage.py` counts Boston police as unmatched even though the two contracts overlap 2023-2025. Fixing this requires a Boston clerical CBA for the ~2019-2023 predecessor cycle (not on the current portal — likely in the legacy archive at `cityofboston.gov/images_documents/`).
- **Quincy HR page is a directory, not a portal.** Lists union reps and phone numbers only; no PDFs linked. Must use the JLMC award for police and file a targeted FOIA for QPEA matching unit.

**Corpus snapshot**
```
contracts: 7 | discourse: 0 | coverage: 7 | city_attributes: 3
healthy matched pairs: 1  (Worcester fire 2017-2020 vs clerical_admin + public_works)
safety units unmatched: 3
  - Boston police 2020-2025  [cycle gap vs SENA 2023-2027]
  - Somerville SPSOA 2012-2018  [no non-safety collected]
  - Somerville SPEA 2012-2015   [no non-safety collected]
```

**Next steps**
1. **Somerville non-safety (SMEA/SMEU)** — not on city HR or Clerk pages. File a low-cost FOIA to Somerville (smaller ask than Worcester; would close two matched pairs at once).
2. **Boston clerical ~2019-2023** — find the SENA or SEIU 888 predecessor cycle in the legacy archive (`cityofboston.gov/images_documents/`) to match BPPA 2020-2025.
3. **Boston BPPA base CBA** — full mechanism clauses require the base agreement (not the MOA). Contact BPPA directly, check the legacy archive, or file c.66.
4. **Arlington + Newton** — manual browser download required (both 403 to fetchers). Arlington HR page explicitly says CBAs are attached. Newton city HR page same. Download Police + AFSCME (Arlington) and Police + clerical/DPW (Newton).
5. **Quincy** — verify JLMC award in `ma_award_inventory.csv` is sufficient for police mechanism clauses; then FOIA for QPEA CBA as the non-safety match.
6. **Install pytesseract + pdf2image** (`pip install pytesseract pdf2image` + `brew install tesseract poppler`) before the next batch that includes scanned documents.
7. **Worcester c.66 still pending** — no action this session; waiting on PI/RA submission.

---

## 2026-06-16 — Validator range-check + finalized Worcester records request

**Did**
- **Added a `pct_increase_annual` range-check to `scripts/validate.py`** (new generic `check_numeric_range` helper, written in the same style as `check_dates`/`check_enum`): rejects any value outside `0 ≤ x ≤ 0.25` or non-numeric, with a row-located error that names the offending value and explains the decimal convention. Blank still passes (field is optional). This closes the validator gap that let last session's `2.0` (=200%) slip through.
- **Documented the range** in `docs/schema.md` (`pct_increase_annual` row now states "valid range 0–0.25 … catches percent-vs-decimal slips like 2.0").
- **Added a test** to `ingest/test_pipeline.py` (`test_validator_pct_range`): `0.02` accepted, `2.0` rejected, blank passes, non-numeric rejected. Suite now **22/22 green** (was 18).
- **Finalized the Worcester c. 66 request** (`docs/records_requests/worcester_c66_2026-06.md`): deleted the entire "Internal notes" section (it referenced GABRIEL/pipeline/inbox internals — inappropriate for a government office). Re-verified the RAO from worcesterma.gov/public-records-requests — **unchanged** (Michael Manning, Law Dept, 455 Main St Room 301, RAO@worcesterma.gov). Requester block left as fillable blanks. **Not sent.**

**Decisions (and why)**
- **Made the helper generic, not pct-specific.** `check_numeric_range(table, rows, field, lo, hi, required, hint)` mirrors the existing helpers so future numeric fields (e.g. `years_to_top`) can reuse it; the pct-specific guidance lives in the `hint` passed at the call site.
- **Range cap 0.25 (25%).** Comfortably above any realistic single-year municipal raise, so legitimate values pass while any percent-as-whole-number slip (2.0, 3.0…) trips immediately.
- **Test targets the validator function directly** (imports `validate`, clears `validate.errors`, asserts) rather than building a CSV fixture — fast, hermetic, and consistent with the suite's no-pytest style.
- **Kept the request's DRAFT/NOT-SENT banner and the "Clarifying scope" MOA explanation** — the MOA-vs-base-CBA distinction is exactly what the records office needs to fulfill the request correctly; only the project-internal notes were removed.

**Surprises / breakage**
- None. Current corpus (all three rows at `0.02`) still validates clean; leak-check confirms no GABRIEL/pipeline/inbox/corpus references remain in the finalized request.

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). validate.py green; test_pipeline.py 22/22.

**Next steps**
- Submit the Worcester c. 66 request (PI/RA action); ingest returned base CBAs via `inbox/foia/` with `retrieval_method=foia` to capture the missing mechanism clauses.
- Extend matched collection to Boston (template) and the other verified cities.

---

## 2026-06-16 — Worcester wage backfill, inbox cleanup, base-CBA records request

**Did**
- **Backfilled** the Worcester fire row `pct_increase_annual` = `0.02` (OCR-recovered: 2% eff. July 1 2017/2018/2019, excl. Step 1) and updated its note to record the OCR reading.
- **Cleared the verified Worcester batch** to prevent re-ingestion duplicates: archived the 3 Worcester manifest rows from `inbox/manifest.csv` to a new `inbox/processed_manifest.csv`, and deleted the 3 staged originals from `inbox/foia/`. The `corpus/ma_worcester/` copies remain as the source of record. `inbox/manifest.csv` is back to header-only.
- **Drafted** a Massachusetts c. 66 public-records request for the full base CBAs (not just MOAs) for Local 1009 (fire), Local 490 (clerical), Local 170 (DPW), 2014–2024 window → `docs/records_requests/worcester_c66_2026-06.md`. **Not sent** — left for PI/RA review and self-submission.
- Re-ran `validate.py` (green) and `audit_coverage.py` (1 healthy matched pair intact) after every change.

**Decisions (and why)**
- **Found and fixed a 100× unit error.** `docs/schema.md` defines `pct_increase_annual` as a decimal (0.03 = 3%). The fire backfill of `0.02` is schema-correct — but it exposed that last session's clerical and DPW rows stored `2.0` (= 200%). Since this column is the analytical spine and the same 2% raise must encode identically, I corrected **both** to `0.02` (a spec-conformance fix, git-reversible), not just the fire row the task named. The validator doesn't range-check this field, so the error had passed silently — flagging that as a validator gap.
- **Archived rather than deleted manifest rows.** Moving processed rows to `inbox/processed_manifest.csv` (vs. commenting them out) keeps `manifest.csv` clean for the next batch while preserving a real, parseable record of what was ingested. Normalized the archived `pct` values to `0.02` too, so the wrong unit doesn't survive anywhere it could be copied back.
- **Records request recipient verified, not guessed:** Michael Manning, RAO, Worcester Law Dept, 455 Main St Room 301 / RAO@worcesterma.gov / GovQA portal (confirmed from worcesterma.gov, 2026-06-16). Request explicitly distinguishes the full base CBAs from the successor wage MOAs already collected, and cites M.G.L. c. 66 §10 + c. 4 §7(26).

**Surprises / breakage**
- The unit-convention bug above (2.0 vs 0.02) — caught only because the backfill forced a direct comparison. Worth a validator rule: range-check `pct_increase_annual` (e.g. 0 ≤ x ≤ 0.25) to catch percent-vs-decimal slips.
- `process_inbox.py` copies (doesn't move) inbox→corpus, so this manual archive+delete step is currently the de-dup mechanism. Candidate pipeline improvement: have `process_inbox.py` move processed files and auto-archive their manifest rows on success.

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). All three `pct_increase_annual` now `0.02`. inbox/manifest.csv: header-only (3 rows archived). validate.py green.

**Next steps**
- Submit the Worcester c. 66 request (PI/RA action); on receipt, ingest base CBAs via `inbox/foia/` with `retrieval_method=foia` to capture the mechanism clauses currently missing.
- Add a validator range-check for `pct_increase_annual` to catch unit slips.
- Extend matched collection to Boston (template) and the other verified cities.

---

## 2026-06-16 — Worcester matched collection (first real ingest)

**Did**
- Collected Worcester's first matched document set from the verified city HR portal (`worcesterma.gov/human-resources/collective-bargaining-agreements`), all 2017–2020 cycle (the one cycle all three units share — clean overlap inside 2014–2024):
  - **Safety:** Worcester Firefighters Local 1009, IAFF — `local-1009-moa-2017-2020.pdf`
  - **Non-safety:** NAGE Local 490 (clerical) — `local-490-moa-2017-2020.pdf`; Teamsters Local 170 (DPW) — `local-170-moa-2017-2020.pdf`
- Automated download worked (HTTP 200, browser User-Agent) — **no 403** this time, despite the inventory note; no manual grab needed. Files staged in `inbox/foia/`, described in `inbox/manifest.csv`, ingested via `process_inbox.py`.
- **All 3 ingested, 0 quarantined.** Copied to `corpus/ma_worcester/`. `validate.py` passes; `audit_coverage.py` shows 1 healthy matched pair (Worcester fire 2017–2020 vs [clerical_admin, public_works]).

**Decisions (and why)**
- **Occupation classes:** Local 490 → `clerical_admin`, Local 170 → `public_works` (DPW). Local 170 is technically the "DPW Clerks" Teamsters local, but classed as public_works to keep the two non-safety comparisons distinct (the design wants occupational variety, not two clerical rows). Noted in the row's `total_comp_note`.
- **Left `text_quality` blank in the manifest** so the extractor auto-tags it — correctly produced `clean` for the two text-layer MOAs and `ocr_messy` for the scanned fire doc.
- **Did not pre-fill clause spans** (per the verbatim rule); let the pipeline capture them. Filled only readily-visible wage structure: 2%/yr for the two MOAs. Left fire wages blank at manifest time (scanned) — now known post-OCR (see below).
- **Did not hand-edit `contracts.csv`** to backfill the fire wage (append-only discipline) — flagged as a backfill next step instead.

**Surprises / breakage**
- **These are successor *wage MOAs*, not full base CBAs.** All three explicitly state they supplement/supersede the prior agreement "pending the drafting of a new contract document." They carry wage/health terms only — **none contains interest-arbitration, comparability, me-too, or no-strike articles**, which live in the base CBA incorporated by reference. So all clause flags came back 0 across all three units. This is **correct pipeline behavior, not a regex gap** — there is genuinely no mechanism-clause text in these documents to capture.
- **No regex tuning needed from this batch.** The only `arbitrat` hit (clerical MOA) was *grievance* arbitration ("...not be subject to a grievance or arbitration..."), which the regex correctly did **not** capture as interest-arbitration. The grievance-vs-interest distinction held up.
- **The real gap is collection scope, not extraction:** to get the causal mechanism clauses GABRIEL needs (arbitration/comparability/no-strike), we must obtain the **full base CBAs**, which Worcester's portal may not post separately (the portal hosts successor MOAs). Likely a records request, or sourcing an older full agreement that the MOAs amend.
- Fire CBA had **no embedded text layer** (scanned) → OCR fired automatically (0 → ~1,962 chars/page) and produced clean, readable output; `ocr_messy` is the conservative auto-tag. Confirmed fire wages = **2% effective July 1 2017/2018/2019, excluding Step 1** (FY18–FY20). This value is not yet in `contracts.csv` (fire row `pct_increase_annual` left blank at ingest) — backfill candidate.
- Pipeline **copies** (not moves) inbox files to `corpus/`, so originals remain in `inbox/foia/`. Since `process_inbox.py` re-processes every manifest row each run, leaving them will duplicate these rows on the next batch — clear the staged originals or prune their manifest rows before the next run. (Left in place this session at request.)

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). cities with a safety contract: 1 (Worcester); no safety unit lacking a comparison.

**Next steps**
- Decide whether successor wage MOAs are sufficient for the wage-trajectory measure, or whether to pull **full base CBAs** (likely c.66 request) so the mechanism clauses are present for GABRIEL.
- Backfill the fire row `pct_increase_annual` = 2.0 (FY18–FY20, excl. Step 1) read from OCR; consider whether the timing difference (fire July 1 vs non-safety Jan 1 increases) matters for alignment.
- Resolve the inbox/manifest re-ingestion footgun before the next batch (clear staged originals or mark processed rows).
- Extend the same matched-collection pattern to Boston (template) and the other verified cities.

---

## 2026-06-16 — CBA source verification (MA award cities)

**Did**
- Established and recorded in `CLAUDE.md` the **"verified" standard** for a city's CBA sources: a city counts as verified only when all three hold, each logged in the inventory — (1) a *findable source* (central portal, union local, or a documented FOIA route), (2) a *safety CBA present* in the 2014–2024 window, and (3) a *matched non-safety CBA* from the same city overlapping the same cycle. A city with safety but no in-window comparison is flagged dead weight, not collected.
- Used **Boston as the template**: verified via the city's central Office of Labor Relations (OLR) portal (`boston.gov/departments/labor-relations`), which hosts ~21 bargaining units' CBAs as PDFs (safety + BTU teachers + clerical).
- Verified the other 5 award cities against the standard and updated `data/ma_award_inventory.csv` (added a `cba_source_url` column distinct from the JLMC `award_url`; set `safety_cba_status`, refined `matched_nonsafety_target`, logged source route + quirks). All 5 came back **verified**:
  - **Newton** — verified_portal. City HR union-contracts portal hosts safety + non-safety CBAs; NTA teachers via Newton Public Schools HR.
  - **Quincy** — verified_portal. Safety via JLMC arbitration awards on mass.gov; QEA teacher CBAs posted (quincypublicschools.com / quincyeducationassociation.org).
  - **Arlington** — verified_portal (town). Fire CBA on town HR page; police arbitration-prone (JLMC award); AEA teacher contracts on massteacher.org.
  - **Somerville** — verified_portal. No central city portal; police CBAs via a *completed* MuckRock FOIA release + MA DLR repository; SEU teachers posted. City verified on police.
  - **Worcester** — verified_portal. Single central HR portal hosts fire + police + clerical + DPW CBAs across multiple in-window cycles.
- Moved nothing: the inventory was already at `data/ma_award_inventory.csv` (untracked); it's now tracked.

**Decisions (and why)**
- **`award_url` ≠ CBA source.** The existing `award_url` points to JLMC interest-arbitration awards on mass.gov; those are not the signed CBAs. Added a separate `cba_source_url` so the *source of the contract text* is recorded explicitly, per the verification standard.
- **Worcester matched non-safety switched from teachers (EAW) to clerical/DPW.** EAW teacher contracts are not on the city HR portal (separate school employer, member-gated union site) and would need a c.66 request; NAGE Local 490 (clerical) and Teamsters Local 170 (DPW) are on the *same* portal as the fire CBA across overlapping cycles — a cleaner matched pair, so the target was changed.
- **All 5 logged as `verified_portal`** even where the cleanest safety text is an arbitration award (Quincy, Arlington police) or a FOIA-released PDF (Somerville police): a findable, obtainable in-window source exists for each. Caveats (signed-CBA-vs-award, fire-needs-c.66, scanned→OCR) are written into the row notes, not hidden behind the status.

**Surprises / breakage**
- **No outright FOIA-only or dead-weight cities** among the five — better than expected. The nuance is in *route*, not existence: Somerville has no city CBA portal at all (relies on MuckRock + MA DLR), and Quincy's signed police CBAs (vs. the awards) would still need a records request.
- City/town HR sites (Newton, Arlington) return **HTTP 403 to automated fetchers** — anti-bot. Documents are real and browser-downloadable, so collection will be manual `public_download`, consistent with the no-scraping discipline.
- Heavy **false-positive noise** from same-named places (Quincy IL; Arlington VA/TX/IL) — excluded; only the MA sources retained.
- Somerville police PDFs are scanned scanner output → expect `text_quality = ocr_messy` at collection.

**Corpus snapshot**
- contracts: 0 | discourse: 0 | matched pairs: 0 — unchanged; this was source *verification* only, no downloads. Inventory: 6 MA cities, all 6 `verified_portal` (Boston template + 5 verified this session).

**Next steps**
- Begin **matched collection** from verified sources, safety + its matched non-safety per city, starting with the cleanest single-portal case (Worcester) and Boston.
- For Somerville fire and Quincy signed police CBAs, queue **c.66 records requests** if the award/FOIA-release text proves insufficient.
- Route the first real documents through `inbox/` + `inbox/manifest.csv` + `python ingest/process_inbox.py`; then re-run `python ingest/audit_coverage.py` and update `data/city_coverage.csv`.

---

## 2026-06-15 — Project setup

**Did**
- Stood up the corpus-construction pipeline: schema (`docs/schema.md`), validator (`scripts/validate.py`), and ingestion layer (`ingest/`).
- Created Python venv, installed `requirements.txt`, installed system deps (poppler, tesseract).
- Initialized local git (no remote for now).
- Verified environment: `ingest/test_pipeline.py` → 18/18 passing; `scripts/validate.py` → passes on empty corpus.

**Decisions (and why)**
- `corpus/` stays **local**, not pushed — licensed (Westlaw/Lexis) and FOIA material can't be redistributed. If a GitHub remote is added later, uncomment `corpus/` in `.gitignore` *before* first push.
- Repo kept local for now; no GitHub remote yet.
- LLM span fallback: using an **Anthropic** key for `llm_pass()` only (Option C); GABRIEL toolchain stays on OpenAI separately. Two keys coexist.
- Clarified scope: this pipeline *builds the corpus*; GABRIEL is the *later* measurement layer that scores it. Distinct stages.

**Surprises / breakage**
- venv creation failed because the parent folder `Pol/Fire` was stored on disk as `Pol:Fire` (Finder shows `/`, filesystem uses `:`, which is the PATH separator). Renamed parent to a colon-free name to fix.

**Corpus snapshot**
- contracts: 0 | discourse: 0 | matched pairs: 0 — empty baseline, environment verified.

**Next steps**
- Run one real CBA through `inbox/foia/` + `inbox/manifest.csv` + `python ingest/process_inbox.py`.
- Inspect the unresolved-spans report to see whether the regex patterns match real contract language (arbitration / comparability / me-too phrasing varies by jurisdiction).
- Begin matched collection: for each safety unit, grab at least one non-safety unit in the same city + cycle.

---

<!-- Template for new entries — copy above this line:

## YYYY-MM-DD — <short title>

**Did**
-

**Decisions (and why)**
-

**Surprises / breakage**
-

**Corpus snapshot**
- contracts: N | discourse: N | matched pairs: N | gaps: ...

**Next steps**
-

-->
