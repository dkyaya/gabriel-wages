# ChatGPT Handoff Log

Reverse-chronological handoff for ChatGPT/Codex planning. Unlike `PROGRESS.md`, this file is more explicit about current interpretation, artifact paths, open decisions, and the recommended next run.

Last updated: `2026-07-05T10:36:45-04:00`

---

## 2026-07-05T10:36:45-04:00 - DPW existing-corpus scan and Massachusetts DPW impasse context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior DPW mechanism session's changes (`3addd14`, "Refine DPW public works wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_existing_corpus_scan_2026-07-04.md`
  - `docs/analysis/ma_dpw_bargaining_impasse_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md` (light edit: closed gaps 9, 11, 12)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: second DPW update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edit to H6 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional-verification and internal-corpus-review session, not a data-build or GABRIEL session.

### What This New Package Does

- **Existing corpus review:** identified all seven `public_works` occupation-class rows in `data/contracts.csv` (Worcester, Arlington x3 cycles, Seekonk, Franklin, Wayland), confirmed all seven corpus files exist, and read their actual text (native extraction for six files; an ad hoc, session-local, read-only OCR pass for two image-only Wayland files whose content was not otherwise legible — output not written back to the corpus). Findings: extensive, source-grounded classification-to-credential-pay linkage (Arlington's CDL-class-tied Motor Equipment Operator grades; Franklin's detailed biweekly stipend schedule covering CDL, hoisting, water/wastewater, pesticide, and ASE mechanic certifications); rich contractor-substitution/outsourcing language (Franklin's two side letters, including a clause where contractor mobilization during snow events triggers an in-house overtime premium; Wayland's emergency-only non-union-labor carve-out); and a genuine, notable absence of peer-community wage-comparability language and explicit recruitment/retention framing in every document reviewed.
- **Massachusetts DPW impasse verification:** confirms, via Mass.gov DLR/JLMC pages and M.G.L. c. 150E, that JLMC eligibility is limited to police and fire (with only a narrow, still police/fire-confined discretionary extension), so DPW/public works bargaining follows the same general Chapter 150E Section 9 route already confirmed for teachers (mediation, advisory factfinding, potential unilateral last-best-offer implementation, rarely-invoked voluntary arbitration). This external finding is directly corroborated by the project's own corpus: every `public_works` row's `binding_arbitration_statute` field cites MA G.L. c. 150E, never the JLMC statute used by every police/fire row, and every arbitration clause found is grievance/discipline-scoped (Seekonk's contract states this explicitly: "Final binding arbitration will prevail on grievances only").
- Flags one metadata-reading observation without acting on it: `data/contracts.csv`'s `comparability_clause_flag` is set to `1` for two Arlington `public_works` rows, but the flagged snippet is a health-insurance/workers'-compensation "comparable" usage, not peer-jurisdiction wage comparability — noted for future readers of the existing metadata, not corrected in this session since `data/contracts.csv` is not modified.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): one small, targeted addition to the counterpoint field, adding the verified MA public-works/DPW institutional and corpus corroboration alongside the teacher-specific verification already present from the prior session. No new rows added; no other DPW rows (H18-H22) required substantive changes based on this session's findings, though the corpus scan memo documents which of those hypotheses are now corpus-supported, corpus-silent, or corpus-untestable.
- Verified: 23 total rows (22 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_dpw_public_works_source_gaps_2026-07-04.md`: gaps 9 (classification/pay-grade structures), 11 (union bargaining language), and 12 (peer-community comparisons) marked CLOSED with pointers to the new corpus-scan and impasse-context memos.
- `non_safety_comparison_roadmap_2026-07-04.md`: a second DPW update note added confirming both open items from the prior DPW session (institutional verification; corpus review) are now resolved.

### Validation/Audit Results

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

### Recommended Next Step

1. Move to the clerical/admin comparison group per the existing roadmap, since both DPW uncertainties flagged at the end of the prior DPW session are now resolved.
2. If a DPW-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in the new corpus-scan memo, and treat peer-comparability and recruitment/retention framing as new-source-acquisition gaps, not further-review gaps.
3. Do not begin GABRIEL/source-extraction prototyping, an OEWS/municipal descriptive baseline build, or ingestion from this state.

### Notes For ChatGPT Review

- Do not restate the task brief's reference to "H10 arbitration_or_impasse_backstop" — in the current matrix, `arbitration_or_impasse_backstop` is H6; H10 is `credentialing_training_burden`. The corpus-scan and impasse memos both use and note the correct current identifier.
- Do not treat the two Wayland files' content as coming from the project's stored corpus text; it was read via this session's ad hoc OCR pass only, which was not written back into `corpus/` or `data/contracts.csv`.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is scoping the clerical/admin comparison group.

---

## 2026-07-04T17:55:09-04:00 - DPW / public works wage mechanism refinement developed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior non-safety teacher mechanism session's changes (`efbfb31`) and the Massachusetts teacher institutional clarification session's changes (`e409824`) were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_public_works_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: DPW findings update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H18-H22; refined H4 and H7)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded context-building/hypothesis-refinement session focused on public works/DPW as the second non-safety comparison group, not a data-build or GABRIEL session.

### What This New Package Does

- Develops DPW/public works as the strongest available *operational* non-safety comparison to police/fire (physical risk, licensure gating, short-notice emergency response), complementing teachers' *credentialing/salience* comparison already developed in prior sessions.
- Maps DPW into distinct sub-occupations (laborers, equipment operators, CDL drivers, water/wastewater operators, mechanics, foremen) rather than treating it as one homogeneous occupation, mirroring the teacher composition-effect discipline.
- Surfaces a genuine, well-sourced counterargument to the CDL-scarcity mechanism: BLS's own 2019 Monthly Labor Review analysis found no evidence of a secular truck-driver shortage, with real driver wages up only ~1.1% since 2010 — inconsistent with chronic scarcity and more consistent with a retention/wage-framing problem that industry associations (echoed by APWA's national workforce-shortage framing) have called a "shortage" since the late 1980s.
- Identifies water/wastewater operator certification, not CDL, as the strongest genuine DPW scarce-credential case, based on national and New England-regional (NEIWPCC) retirement-wave evidence (30-50% of the water workforce eligible to retire within 5-10 years).
- Surfaces a specific Massachusetts institutional wrinkle: Massachusetts prevailing wage law ties public-construction contractor wages to locally collectively bargained rates, so contracting out DPW-type work does not simply undercut the wage paid for that specific work the way outsourcing might without such a law (though routine service contracts may not always be covered).
- Compares DPW emergency work (snow/storm response, water-main breaks) to police/fire emergency response, concluding DPW emergency needs more plausibly convert into overtime and contractor spending (reported at roughly 3x normal rates during active events) than into recurring base-wage pressure, given routine pre-arranged contractor substitution unavailable to police/fire.
- Explicitly separates Massachusetts-specific findings (hoisting license, prevailing wage law, municipal classification/CBA structure) from national background context (CDL debate, national water-workforce statistics, APWA framing) throughout, per this session's scope instruction not to overgeneralize.

### Hypothesis Matrix Changes

- Added H18 `dpw_operational_essentiality`, H19 `dpw_cdl_equipment_operator_scarcity`, H20 `dpw_contractor_substitution`, H21 `dpw_service_deferral`, H22 `dpw_classification_fragmentation` as new rows, all with police/fire relevance marked low, consistent with the existing schema (12 columns unchanged).
- Refined H4 (`overtime_staffing_spiral`) and H7 (`political_support_or_public_salience`) counterpoint fields to fold in DPW-specific nuances (contractor-substitution availability changing the overtime-spiral comparison; DPW's likely-lower but event-dependent public salience) rather than adding separate rows for those two.
- `dpw_water_sewer_license_scarcity` and `dpw_overtime_emergency_response` and `dpw_lower_public_salience`, three of the eight hypotheses named in this session's task brief, were deliberately not given their own CSV rows; the first is folded into H19's counterpoint as its strongest sub-case, and the latter two are folded into the H4 and H7 refinements respectively, consistent with the preference for a small number of high-value additions.
- Verified: 23 total rows (22 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- 13 DPW/public-works source gaps identified in `non_safety_dpw_public_works_source_gaps_2026-07-04.md`, several partially closed this session via bounded web search (national CDL/BLS labor-market debate, national/NEIWPCC water-workforce context, MA hoisting-license and prevailing-wage mechanics) and others flagged as open (Massachusetts-city-specific vacancy/overtime/classification data, whether DPW bargaining follows the same Chapter 150E Section 9 process as teachers, and whether this project's already-collected `public_works` CBAs contain classification premiums or comparator language).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a concise DPW findings update note under the existing Section 2, without a full rewrite.

### Validation/Audit Results

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

### Recommended Next Step

1. Review this project's already-collected `public_works` occupation-class CBAs for classification/pay-grade structure, credential-tied premiums, and comparator-district language, without new ingestion.
2. Verify whether Massachusetts DPW/public-works bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers.
3. Move to the clerical/admin comparison group per the existing roadmap, only after the DPW source gaps above are addressed.

### Notes For ChatGPT Review

- Do not restate the CDL "shortage" framing as an established scarcity fact; BLS's own analysis is the operative counter-evidence, and the correct framing is a live shortage-vs-retention-problem debate, not a settled shortage.
- Do not treat the national/NEIWPCC water-workforce statistics or APWA workforce-shortage framing as Massachusetts-city-specific findings; they are national/regional background context, not verified for this project's specific cities.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is reviewing already-collected corpus documents and verifying the DPW bargaining-impasse-process question.

---

## 2026-07-04T16:36:12-04:00 - Massachusetts teacher bargaining and school finance institutional context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior non-safety teacher mechanism session's changes were already committed as `efbfb31` ("Refine non-safety teacher wage mechanisms"), with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/ma_teacher_bargaining_school_finance_institutional_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md` (light edit: closed gap item 13)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added an update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined H5, H6, H9 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional/source-verification session, not a data-build or GABRIEL session.

### What This New Package Does

- Verifies the two Massachusetts-specific institutional claims the prior teacher mechanism session flagged as unverified, using primary/near-primary sources: DESE's own Chapter 70 program pages, Mass.gov Department of Labor Relations impasse and JLMC pages, and Massachusetts General Laws Chapter 150E Section 9.
- **Chapter 70/school finance:** confirms the foundation budget -> required local contribution (capped at 82.5% of foundation budget locally) -> Chapter 70 aid -> net school spending chain, and establishes that schools face a two-sided budget constraint (a state-mandated spending floor plus the same municipal Proposition 2 1/2 levy-limit ceiling shared by other departments) that most other municipal departments, including police/fire, do not have on the floor side.
- **Teacher bargaining impasse process vs. JLMC:** corrects, rather than simply confirms, the prior hedge. The precise, verified finding is that JLMC *orders* police/fire into compulsory binding interest arbitration upon certified impasse, while teachers (and most other MA public employees) under Chapter 150E Section 9 have only mediation plus advisory (non-binding) factfinding, after which the school committee may unilaterally implement its last, best offer. A voluntary arbitration route exists on paper for non-police/fire units but requires mutual agreement and school-committee authorization and is not typical in practice — Mass.gov's own guidance states non-police/fire bargaining has "no arbitration process." This is a compulsory-vs-voluntary institutional-design difference, not a has-backstop-vs-has-no-process-at-all difference, and the new memo is explicit about that correction.
- Includes a claim/correction/evidence table covering all five required claims (JLMC-like backstop absence, Chapter 70/local-contribution constraint, shortage buffering, peer-district comparability outside JLMC-style awards, and school-finance-vs-ordinary-ability-to-pay), each marked with a verification status and source support.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): counterpoint, textual-signal, and quant-data fields updated to state the verified compulsory-vs-voluntary distinction precisely, with a new textual signal (advisory/recommendations language, last-best-offer unilateral-implementation language) as the signature of the weaker non-safety process.
- H9 (`fiscal_capacity_ability_to_pay`): counterpoint, textual-signal, source-type, quant-data, and confound fields updated to state the verified two-sided floor/ceiling school-finance structure (net school spending floor plus Proposition 2 1/2 ceiling) precisely.
- H5 (`comparator_ratchet`): counterpoint field lightly updated to note that JLMC comparator criteria are statutorily mandated while teacher-side comparator claims have no equivalent compulsory enforcement mechanism.
- No new rows were added; verified 18 total rows (17 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_teacher_source_gaps_2026-07-04.md` gap item 13 (Massachusetts teacher bargaining impasse process) is now marked CLOSED with a pointer to the new institutional memo and a note on the one remaining sub-gap (city-specific override/net-school-spending-compliance history, not yet reviewed).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a short update note under the teachers section pointing to the new institutional memo, plus a reminder to check whether DPW bargaining (next in sequence) follows the same general Chapter 150E Section 9 process as teachers.

### Validation/Audit Results

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

### Recommended Next Step

1. Cross-reference the new institutional memo from the existing PI-facing synthesis memo, so PI-facing material states the compulsory-vs-voluntary arbitration distinction and Chapter 70 floor/ceiling structure as verified facts rather than hedged hypotheses.
2. Move to the public works/DPW comparison group per the existing roadmap, checking whether DPW bargaining follows the same Chapter 150E Section 9 process as teachers.
3. Do not begin GABRIEL/source-extraction prototyping, the OEWS/DESE descriptive baseline build, or ingestion from this state.

### Notes For ChatGPT Review

- Do not restate "teachers have no arbitration backstop at all" without the compulsory-vs-voluntary nuance verified this session; the precise claim is that JLMC compels arbitration upon impasse while teacher bargaining does not, not that teachers have zero statutory arbitration access whatsoever.
- Do not treat this session's Chapter 70 findings as sufficient for any city-specific school-finance claim in this project's current corpus; no city-level override or net-school-spending-compliance history was reviewed this session.
- Do not recommend a GABRIEL run as the immediate next step; the recommended next step is the PI-synthesis cross-reference and the DPW comparison group.

---

## 2026-07-04T11:50:03-04:00 - Non-safety wage mechanism refinement started with teachers

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/non_safety_teacher_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md`
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H13-H17; refined H5 and H9 counterpoint fields)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was explicitly a context-building/hypothesis-refinement session focused on the non-safety side of the comparison, not a data-build or GABRIEL session.

### What This New Package Does

- Develops, for the first time in this project, the "other side" of the police/fire wage-gap comparison: the gap can grow because safety wages accelerate, because non-safety wages are restrained, or both, and prior memos only addressed the first term.
- Starts with teachers specifically, not "non-safety" generically, because teachers share the most features with the safety side (credentialing, unionization, political salience, public esteem) and are therefore the hardest, most informative test case.
- Grounds the teacher-supply, composition, salary-schedule, and budget-constraint sections in real cited sources found via bounded web search this session: NCES/IES School Pulse Panel (74% of U.S. public schools had difficulty filling at least one teaching vacancy entering 2024-25, down from 79%; special education and ESL/bilingual hardest to fill by grade band), Learning Policy Institute (special ed/science/math the most common statewide shortage areas; ~1 in 8 positions unfilled or non-fully-certified), NCTQ (roughly 3 in 4 sampled districts already offer hard-to-fill differentiated pay; step-and-lane schedule mechanics), Massachusetts DESE (Teacher Salaries Report methodology), and Mass.gov (Proposition 2 1/2 levy-limit/override mechanics).
- Develops a structural asymmetry hypothesis: teacher-side shortage buffering (substitutes, emergency certification, larger classes, program cuts) tends to substitute toward cheaper labor or degraded service rather than raising pay to existing staff, unlike police/fire overtime/callback buffering, which directly raises realized compensation to incumbent workers — a candidate structural reason non-safety wage growth could lag even under comparable measured staffing strain.
- Explicitly flags two claims as unverified this session rather than asserting them: Massachusetts's Chapter 70 state-aid formula mechanics, and whether Massachusetts teacher bargaining under M.G.L. c. 150E lacks a binding wage-arbitration backstop (unlike police/fire under JLMC). Both are routed to the new source-gap memo as priority items.
- Sets up, without deeply researching, the next two non-safety comparison groups (public works/DPW, then clerical/admin) and briefly notes later groups (sanitation, facilities/custodial, libraries/parks, transit, nurses/health) in a sequencing roadmap.

### Hypothesis Matrix Changes

- Added H13 `teacher_supply_pressure`, H14 `teacher_shortage_buffering`, H15 `teacher_composition_effect`, H16 `teacher_salary_schedule_rigidity`, H17 `non_safety_wage_restraint` as new rows, all with police/fire relevance marked low (H17 medium/medium as the general cross-occupation mirror hypothesis), consistent with the existing schema (12 columns unchanged).
- Refined H5 (`comparator_ratchet`) and H9 (`fiscal_capacity_ability_to_pay`) counterpoint fields to fold in `teacher_peer_district_comparability` and `school_budget_constraint` respectively, rather than adding separate rows for those two, per the standing preference to improve the existing map over proliferating new rows.
- `non_safety_service_deferral_or_substitution`, the eighth hypothesis discussed in the new memo, was deliberately not given its own CSV row this session; it is documented as a general framing concept motivating `teacher_shortage_buffering` and the DPW/clerical roadmap, pending evidence from those later comparison groups.
- Verified: 18 total rows (17 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Highlights

- 13 teacher/non-safety source gaps identified in `non_safety_teacher_source_gaps_2026-07-04.md`, several partially closed this session via bounded web search (teacher vacancy rates, under-certification shares, shortage-area subjects, hard-to-fill stipend base rates, Proposition 2 1/2 mechanics) and others flagged as still open (long-term substitute use, grade/subject composition for this project's specific cities, district-level peer salary comparisons, and the Massachusetts teacher bargaining impasse-process verification).
- `non_safety_comparison_roadmap_2026-07-04.md` sequences public works/DPW second (tests operational similarity without safety's institutional/political-salience advantages) and clerical/admin third (cleanest available budget-capacity baseline), with brief notes on sanitation, facilities/custodial, libraries/parks, transit, and nurses/health as later groups.

### Validation/Audit Results

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

### Recommended Next Step

1. Verify the two claims flagged as unverified this session: Massachusetts Chapter 70 state-aid mechanics, and whether Massachusetts teacher bargaining lacks binding wage arbitration.
2. Review this project's existing city CBAs for teacher salary-schedule structure, hard-to-fill stipend/MOU language, and comparator-district language, where teacher units are already in the corpus.
3. Only after that, move to the public works/DPW comparison group per the new roadmap memo.

### Notes For ChatGPT Review

- Do not treat the Chapter 70 or Massachusetts teacher-arbitration claims as verified facts; they are explicitly flagged as background/analyst judgment pending direct verification.
- Do not recommend a GABRIEL run, an OEWS/DESE build, or ingestion as the immediate next step from this state; the recommended next step is closing source gaps and reviewing existing corpus CBAs for already-available teacher salary-schedule evidence.
- Do not merge teacher assistant/paraprofessional data or BLS categories into teacher-specific figures in any future work.

---

## 2026-07-04T10:41:22-04:00 - Police/fire workforce context refinement and source-gap list created

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_workforce_context_refinement_2026-07-03.md`
  - `docs/analysis/police_fire_workforce_context_source_gaps_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined H2, H6, H11 rows only; schema and row count unchanged; no new hypothesis rows added)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was explicitly a context-building/hypothesis-refinement session, not a data-build or GABRIEL session.

### What This New Package Does

- Deepens four areas the PI asked for more nuance on: (1) police applicant supply/recruitment/retention/morale, with an explicit disentangling of the George Floyd/BLM legitimacy channel from COVID-era labor disruption, pension-vintage retirement timing, and the broad 2021-2023 Great Resignation; (2) firefighter wage pressure vs. public esteem, the career/volunteer distinction, and why firefighter median pay can be lower than police despite EMT/training credentials, without implying anything about relative training quality; (3) non-safety counterexamples (nursing, transit, sanitation, public works, teachers) with an explicit statement of what plausibly still differs for public safety (zero-deferability at the moment of the call, the no-strike-for-interest-arbitration institutional trade-off); (4) the interest-vs-grievance arbitration distinction and the evidentiary logic (bunching/centering test, criteria-correlation test, conventional-vs-final-offer comparison) for telling split-the-difference behavior apart from criteria-applying behavior.
- Every claim not already backed by a citation in the existing mechanism memo/bibliography is explicitly flagged as "background/analyst judgment, not yet source-verified" rather than given an invented citation, and routed into the new source-gap list.
- Adds a claim/counterpoint/evidence-needed table and specific textual-signal guidance for future GABRIEL/source extraction, without prototyping or running any new attribute.

### Hypothesis Matrix Changes

- H2 (`post-2020 policing climate shock`): counterpoint and textual-signal fields now require the text to name a specific channel (legitimacy/scrutiny vs. COVID hiring disruption vs. retirement-eligibility timing vs. general labor-market competition) rather than scoring any post-2020 staffing mention as legitimacy-channel evidence.
- H6 (`arbitration or impasse backstop`): counterpoint field now names the no-strike/interest-arbitration statutory trade-off (e.g., MA JLMC) as the sharper, more checkable comparison to non-safety bargaining regimes, and adds award-level (offer/offer/award) capture guidance for a later bunching/centering test.
- H11 (`volunteer to career transition pressure`): now states the three-channel, lagged transmission mechanism explicitly (combination-department conversion, overtime/minimum-staffing substitution, full professionalization) so future evidence coding maps document type to the right channel.
- No new hypothesis rows were added; schema (12 columns, `hypothesis_id` through `priority`) is unchanged.

### Source-Gap List Highlights

Eight gaps identified, each with why-it-matters, likely source families, and a feasibility tag (`desk_research_feasible` / `data_build_feasible` / `likely_hard`): police applicant counts over time, police resignation/retirement series, firefighter applicant trend evidence, firefighter volunteer recruitment/retention evidence, training-cost/training-time evidence, overtime/vacancy budget reports with non-safety comparisons, arbitration award behavior/split-the-difference evidence, and the already-planned wage-trend baseline (listed for completeness only, not to be started from this session).

### Validation/Audit Results

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

### Recommended Next Step

1. Close the highest-value source gaps first: a direct (non-AP-summary) PERF/IACP staffing-survey citation with a multi-year applicant trend, an NFPA/FPRF or NVFC citation on volunteer-firefighter headcount trends, and one or two arbitration-behavior sources that speak directly to the split-the-difference-vs-criteria debate.
2. Only after that source base is stronger, revisit which sharpened hypotheses are worth a dedicated GABRIEL attribute.
3. Keep the OEWS/ASPEP descriptive wage-trend baseline as the next data-build step, separate from this mechanism-refinement lane.

### Notes For ChatGPT Review

- Do not treat the "background/analyst judgment, not yet source-verified" claims in the new refinement memo as sourced facts; they are flagged precisely because they still need a real citation.
- Do not recommend a GABRIEL run, an OEWS/ASPEP build, or ingestion as the immediate next step from this state; the recommended next step is closing source gaps first.
- Do not generalize the Massachusetts JLMC no-strike/interest-arbitration institutional case into a claim about national arbitration practice.

---

## 2026-07-03T15:55:58-04:00 - OEWS/ASPEP descriptive wage-trend baseline plan prepared

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_trend_baseline_implementation_plan_2026-07-03.md`
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv`
  - `docs/analysis/police_fire_wage_trend_baseline_note_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- The prior mechanism-synthesis work was already committed as `0cd3e91`, so no cleanup commit was needed before this run.

### What This New Package Does

- Turns the earlier trend-data concept memo into an implementation-ready OEWS/ASPEP baseline plan with exact official source entry points.
- Specifies the first-pass geography set: national, Massachusetts, and Boston-Cambridge-Newton, MA-NH.
- Specifies the first-pass occupation set and flags where the mapping is clean versus proxy-based.
- Makes explicit that OEWS and ASPEP are descriptive occupation/function sources, not bargaining-unit wage sources.

### Key Source Choices

- OEWS annual tables page: `https://www.bls.gov/oes/tables.htm`
- OEWS state estimates page: `https://www.bls.gov/oes/current/oessrcst.htm`
- OEWS metro/nonmetro page: `https://www.bls.gov/oes/current/oessrcma.htm`
- ASPEP tables page: `https://www.census.gov/data/tables/2025/econ/apes/annual-apes.html`
- ASPEP datasets page: `https://www.census.gov/data/datasets/2025/econ/apes/annual-apes.html`
- ASPEP methodology page: `https://www.census.gov/programs-surveys/apes/technical-documentation/methodology/annual/2025.html`
- ASPEP table IDs selected for the first pass:
  - `GOVSEMPTIMESERIES.GS00EMP01`
  - `GOVSEMPTIMESERIES.GS00EMP02`
  - `GOVSEMPTIMESERIES.GS00EMP03`

### Occupation Mapping Position

High-fit first-pass mappings:

- police -> `33-3051` Police and Sheriff's Patrol Officers
- fire -> `33-2011` Firefighters

Useful but imperfect comparison mappings:

- teacher -> elementary and secondary teachers
- clerical_admin -> Office Clerks, General
- public_works -> Maintenance and Repair Workers, General
- sanitation -> Refuse and Recyclable Material Collectors
- transit -> Bus Drivers, Transit and Intercity

The package is explicit that `clerical_admin` and especially `public_works` are proxy mappings rather than exact municipal-unit representations.

### Validation/Audit Results

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

### Recommended Next Step

1. Implement the first descriptive OEWS panel for the selected occupations and geographies.
2. Add ASPEP function-based context for police protection, fire protection, education, and other relevant functions.
3. Keep the interpretation descriptive and reserve bargaining-unit wage construction for separate CBA/payroll work.

## 2026-07-03T15:14:25-04:00 - PI-facing synthesis and source-QC pass completed

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_mechanism_synthesis_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.

### Source-QC Findings

- The bibliography now distinguishes between authoritative federal/state references, institutional-context sources, and illustrative secondary sources.
- The AP article summarizing the PERF staffing survey is retained only as an illustrative source and should be replaced with the direct PERF release before formal citation.
- BLS and Census landing-page references are fine for planning, but some entries still need exact table/report links before external-facing use because the page year and underlying data year are not the same thing.
- The OOH and related entries are now annotated with access date and underlying data-year cautions.

### Analytical Position After This Entry

- The mechanism memo now reads more explicitly as a hypothesis map rather than an ordered explanation.
- Comparability remains important, but the PI-facing framing is now broader: police/fire wage growth may reflect multiple interacting mechanisms rather than a single comparator story.
- The synthesis memo explains why police and fire may differ from each other and why non-safety comparison is part of mechanism definition, not just a robustness check.

### Validation/Audit Results

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

### Recommended Next Step

1. Replace indirect or illustrative bibliography items with exact primary citations where available.
2. Build the first descriptive OEWS/ASPEP baseline.
3. Keep broader-state mechanism discovery small and curated before any new GABRIEL design or run decision.

## 2026-07-03T14:02:03-04:00 - Broader police/fire wage mechanism memo package created

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_trend_data_plan_2026-07-02.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- The new memo explicitly steps back from implementation and develops competing police/fire wage mechanisms, counterarguments, and evidence requirements.
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.

### Analytical Position After This Entry

- v9 remains a descriptive `comparability_emphasis` baseline with strong source-type confounding.
- v10 remains a useful institutional-pathway concept, but only one mechanism among several.
- The broader mechanism space now includes recruitment/retention pressure, post-2020 policing climate, hazard/work burden, overtime spirals, political salience, fiscal capacity, credentialing/training barriers, volunteer-to-career fire pressure, and union/institutional leverage.
- The memo now treats each mechanism with an explicit counterpoint and a note on what evidence would distinguish it from alternatives.

### Validation/Audit Results

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

### Recommended Next Step

Stay in mechanism-development mode:

1. build a first descriptive OEWS/ASPEP trend baseline;
2. add a small broader-state public snippet set for mechanism discovery;
3. only then revisit whether new GABRIEL attributes should be prototyped from this expanded mechanism map.

## 2026-07-01T23:33:27-04:00 - Thursday report package integrated around Boston bounded built-in web success

**Commit:** pending in current session

### Current State After This Entry

- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Integrated the successful Boston graduated built-in GABRIEL web retry into the Thursday report package.
- The live finding is no longer framed as blocked.
- No additional live web-search or GABRIEL model/API calls were run in this integration session.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### Final Thursday Message

Built-in GABRIEL web mode works on a bounded Boston source-discovery query through the Harvard proxy, but larger structured extraction prompts need incremental tuning for stability.

### Integrated Result Summary

- `openai-gabriel` installed/imported: yes
- version: `1.1.8`
- built-in web path confirmed: `gabriel.whatever(web_search=True)`
- large Boston prompt: failed with connection errors
- minimal diagnostics: all succeeded
- graduated Boston retry:
  - attempt 1 failed
  - attempt 2 succeeded
  - attempt 3 skipped
- source rows: 1
- extraction rows: 1
- returned source: BPS `BTU Contract Negotiations` page
- URL preserved: yes
- Boston BTU/BPS material rediscovered: yes
- ingestion: no

### Recommended Next Step

Boston-only structured extraction tuning, one dimension at a time:

1. prompt size
2. output cap
3. source metadata handling
4. timeout behavior

### Notes For ChatGPT Review

- Do not recommend more live GABRIEL calls in the immediate next step beyond Boston-only structured tuning.
- Do not recommend a five-city pilot, all-32 v10, ingestion, PRRs, PDF generation, or slide generation from this state.
- Do not convert the one successful live retry into a numeric chart.

---

## 2026-07-01T18:42:30-04:00 - Boston graduated built-in GABRIEL web retry succeeded on attempt 2

**Commit:** pending in current session

### Current State After This Entry

- Created and ran:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py`
- Created graduated retry artifacts:
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_graduated_retry_2026-07-01/`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_sources_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_extractions_2026-07-01.csv`
  - `docs/analysis/gabriel_builtin_web_boston_graduated_retry_2026-07-01.md`
- Updated Thursday draft, PDF-ready report, and presentation outline.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.
- No five-city live pilot, all-32 v10 run, production dataset creation, PRR recommendation, or causal claim was made.

### Attempts Run

| Attempt | Result |
| --- | --- |
| 1 tiny Boston report | ran; failed with a connection error and no response |
| 2 source discovery only | ran; succeeded with non-empty response and a parseable source URL |
| 3 small attribute extraction | skipped after attempt 2 succeeded |

Returned source: BPS `BTU Contract Negotiations` page, `https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations`.

Counts:

- Source rows: 1.
- Working extraction rows: 1.
- URLs/citations preserved: yes, parseable URL in response text.
- Boston BTU/BPS material rediscovered: yes.
- Ingestion: no.

### Interpretation

Built-in GABRIEL web mode works on a small Boston source-discovery query through the Harvard proxy. The earlier larger Boston failure was not reproduced by the graduated retry, but attempt 1 still hit a connection error, so transient connection behavior remains possible. Larger structured extraction/output shape should be tuned incrementally before any broader pilot.

### Recommended Next Step

Keep the next run Boston-only and tune one dimension at a time: prompt size, output cap, source metadata handling, and timeout behavior. Do not run a five-city live pilot or ingestion until a small Boston structured-output path is stable.

### Validation/Audit Results

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

---

## 2026-07-01T18:27:47-04:00 - GABRIEL/OpenAI proxy web-connectivity diagnostic completed

**Commit:** pending in current session

### Current State After This Entry

- Created a minimal diagnostic runner:
  - `analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py`
- Created diagnostic outputs:
  - `analysis/gabriel_pilot/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.csv`
  - `docs/analysis/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.md`
- Updated Thursday-facing reports with a short diagnostic note.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.
- No full Boston web-search prompt, five-city live pilot, all-32 v10 run, production dataset creation, PRR recommendation, or causal claim was made.

### Diagnostic Tests Run

All tests used tiny prompts and sanitized result logging only.

| Test | Result |
| --- | --- |
| Raw OpenAI proxy, no web tools | succeeded |
| GABRIEL non-web call | succeeded |
| GABRIEL `whatever(web_search=True, search_context_size="low")` | succeeded in final bounded diagnostic |
| Raw OpenAI Responses API `tools=[web_search]` | succeeded with status `completed` |

The final diagnostic result category is **unknown**. The earlier Boston smoke-test failure was not reproduced by the minimal proxy/non-web/web-tool checks, so the result no longer supports a persistent proxy wiring problem, ordinary `openai-gabriel` proxy compatibility problem, or raw hosted web-search-tool support problem.

### Recommended Question For Hemanth / Harvard Proxy Support

Can the Harvard HUIT OpenAI proxy support longer Responses API hosted web-search requests from `openai-gabriel`, including `include=["web_search_call.action.sources"]`, domain filters, and `extra_headers`, and are there proxy-side timeout/body-size/logging limits that could explain why the larger Boston `gabriel.whatever(web_search=True)` run produced repeated connection errors while the tiny diagnostic succeeds?

### Validation/Audit Results

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

---

## 2026-07-01T12:09:13-04:00 - openai-gabriel installed; Boston built-in web call failed with connection errors

**Commit:** pending in current session

### Current State After This Entry

- `openai-gabriel` was installed into the active project virtual environment.
- `import gabriel` now succeeds.
- Built-in web mode is callable by signature through `gabriel.whatever(web_search=True, web_search_filters=..., search_context_size=...)`.
- A Boston-only built-in web smoke test was attempted through the native `gabriel.whatever(web_search=True)` path.
- The live call did not return a response: GABRIEL recorded `Successful=False` and three connection errors.
- No source URLs, citations, snippets, page text, or model web summary were returned.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### Install/Import Result

- Install command: `python -m pip install openai-gabriel`.
- First sandboxed install attempt failed due DNS resolution for `pypi.org`.
- Escalated install succeeded.
- Installed package/version: `openai-gabriel` 1.1.8.
- Imported module: `.venv/lib/python3.11/site-packages/gabriel/__init__.py`.
- Exposed functions: `whatever`, `extract`, `rate`, and `classify`.

### Signature Result

- `gabriel.whatever`: explicit `web_search`, `web_search_filters`, `search_context_size`, `save_dir`, `column_name`, `identifier_column`, `model`, `n_parallels`, and `reset_files`.
- `gabriel.extract`: explicit `modality`; `web_search`, `web_search_filters`, and `search_context_size` available via kwargs; `save_dir`, `column_name`, `model`, `n_parallels`, and `reset_files` explicit.
- `gabriel.rate` and `gabriel.classify`: explicit `modality` and `search_context_size`; web controls available via kwargs.

### Credential/Proxy Handling

- Only credential presence was checked; no values were printed.
- `HARVARD_SUBSCRIPTION_KEY` is present via `.env`.
- `OPENAI_API_KEY` and `OPENAI_BASE_URL` were not present before runtime mapping.
- The runner passed the Harvard key at runtime as GABRIEL `api_key`, the Harvard proxy base URL as `base_url`, and the Harvard subscription header through `extra_headers`.
- No key was written into code or committed.

### Boston Smoke-Test Result

- Runner created: `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`.
- Path used: `gabriel.whatever(web_search=True)`.
- Identifier: `gabriel_builtin_web_boston_btu_2026_07_01`.
- Model/search context: `gpt-5.4-nano`, `search_context_size="low"`.
- Scope: one Boston BPS/BTU public-source prompt.
- Result: failed API/web call; empty response.
- Raw GABRIEL result: `Successful=False`; `Error Log=["Connection error.", "Connection error.", "Connection error."]`; `Web Search Sources` empty.
- Source rows: 0.
- Extraction rows: 0.
- Boston BTU/BPS salary-comparison material rediscovered: no.
- URLs/citations preserved: no, none returned.

### Artifacts

- Created:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`
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

### Dependency Decision

`requirements.txt` was not modified. The package installed and imported, but the built-in web call did not successfully return a response; pinning `openai-gabriel` should wait until the Harvard proxy/web-mode issue is resolved.

### Recommended Next Step

Ask Hemanth/toolkit creator whether `openai-gabriel` built-in web mode is expected to work through the Harvard HUIT proxy with Responses API web-search tools and `extra_headers`, or whether the smoke test needs a standard OpenAI endpoint/key environment. Then rerun only the same Boston prompt.

### Validation/Audit Results

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

---

## 2026-07-01T13:30:00-04:00 - built-in GABRIEL web smoke test blocked locally by missing package

**Commit:** pending in current session

### Current State After This Entry

- A Boston-only built-in GABRIEL web smoke test was checked but not executed.
- Built-in GABRIEL web mode remains the primary live path conceptually.
- The local Python environment does not currently expose an importable `gabriel` package, so the built-in path could not be called here.
- No live web search was run.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### What Was Checked

- `import gabriel`: failed; no module found.
- `python -m pip show gabriel GABRIEL gabriel-toolkit gabriel-ai`: no installed package found.
- Repo search: no vendored GABRIEL package and no local tutorial notebook found.
- `/mnt/data`: not present in this session, so no uploaded tutorial notebook was available there.
- Existing pilot code: current runners use direct OpenAI calls over local text; no built-in GABRIEL web invocation exists in the repo.

### Availability Result

- `gabriel.whatever`: unavailable here.
- `web_search=True`: could not be tested.
- `web_search_filters`: could not be tested.
- `search_context_size`: could not be tested.
- `modality="web"`: could not be tested.
- `gabriel.extract`: unavailable here.
- `gabriel.rate`: unavailable here.
- `gabriel.classify`: unavailable here.

### What Changed

- Created:
  - `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Status Counts

- Boston smoke test ran: no.
- GABRIEL web path used: none; package unavailable.
- Source rows created: 0.
- Extraction rows created: 0.
- Boston BTU rediscovered: no live test ran.
- URLs/citations preserved: none returned.
- Ingestion performed: no.
- Code added: no.

### Recommended Next Step

Ask Hemanth/toolkit creator for the installable/importable GABRIEL package version or the exact environment where the tutorial web-mode calls are available. Then rerun only the Boston smoke test, starting with `gabriel.whatever(..., web_search=True, search_context_size="low")` if available, otherwise the supported `gabriel.extract(..., modality="web")` route.

### Validation/Audit Results

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

---

## 2026-07-01T13:20:00-04:00 - all-repo declutter plan and manifest created

**Commit:** pending in current session

### Current State After This Entry

- An all-repo declutter audit was completed.
- The scope was the full repo, not only the GABRIEL web-search area.
- No files were moved, deleted, or renamed.
- A narrative repo-wide declutter plan was created.
- A candidate manifest CSV was created with path-level recommended actions, timing, risk, and dependency notes.

### What Changed

- Created:
  - `docs/analysis/repo_declutter_plan_2026-07-01.md`
  - `docs/analysis/repo_declutter_candidate_manifest_2026-07-01.csv`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Main Recommendation

- Keep production data, corpus, inbox, ingestion code, validation scripts, and spend logs visible and untouched.
- Keep active v9 analysis code/results and current Thursday report-facing files visible.
- Archive Thursday-only support artifacts after the Thursday package is finalized.
- Archive v10 dry-run branch artifacts and legacy generated pilot outputs only after the v10/web-search branch stabilizes.
- Treat `docs/acquisition/`, comparator memos, session snapshots, and older report exports as provenance-preserving archive candidates rather than disposable clutter.

### Recommended Next Step

User review of the declutter categories and candidate archive layout before any actual archive operation.

### Status Checks

- Files deleted: no.
- Files moved: no.
- Files renamed: no.
- Live web search executed: no.
- Ingestion performed: no.

### Validation/Audit Results

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

---

## 2026-07-01T12:00:00-04:00 - tutorial clarified built-in web mode; report framework corrected

**Commit:** pending in current session

### Current State After This Entry

- The tutorial clarification changed the live-path framing materially.
- Built-in GABRIEL web mode is now treated as the primary live path.
- The custom `get_all_responses_fn` scaffold is now treated as a fallback and advanced schema-control path.
- The Thursday report draft, PDF-ready report, presentation outline, and custom-function memo were updated to reflect that change.
- A repo declutter/archive plan was created.
- No live web search was executed.
- No ingestion happened.

### What Changed

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

### Framework Correction

- Primary live path: built-in GABRIEL web mode.
- Report-first route: `gabriel.whatever(..., web_search=True)`.
- Extraction route: `gabriel.extract` or structured parsing on built-in web reports.
- Fallback route: custom `get_all_responses_fn` only if built-in outputs are not structured enough or if tighter schema control is needed.
- Project gap: the repo had not yet wired built-in web mode into the city-by-city source/extraction schema.

### Recommended Next Step

Run a Boston-only built-in GABRIEL web smoke test after confirming the exact invocation details and output structure in this project environment.

### Status Checks

- Files deleted: no.
- Files moved: no.
- Live web search executed: no.
- Ingestion performed: no.
- Seed counts unchanged: 5 city responses, 15 source rows, 34 extraction rows.

### Validation/Audit Results

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

---

## 2026-07-01T10:43:43-04:00 - live smoke test skipped; no safe backend available

**Commit:** pending in current session

### Current State After This Entry

- A bounded one-city Boston live smoke test was considered.
- The live smoke test was not executed because no safe repo-local search backend or approved search API client was available.
- Seed mode remains the current executable demonstration.
- No live result CSVs were created.
- No ingestion happened, and no production corpus files were modified.

### Backend Inspection Result

- `requirements.txt` has no search API dependency.
- Installed-package probes found no SerpAPI, Serper, Brave, Tavily, Exa, Google API client, DuckDuckGo wrapper, or similar search client.
- The active shell exposed no search-backend environment variable.
- The repo `.env` only advertised the Harvard HUIT OpenAI proxy key used by existing GABRIEL scoring and optional LLM span extraction.
- Session-level browser/search tools were not treated as a local callable backend for `custom_get_all_responses`.

### What Changed

- Created status memo:
  - `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- Added concise `Optional live smoke test` notes to:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated this handoff log and `PROGRESS.md`.

### Status Checks

- Live web search executed: no.
- Backend used: none; no safe backend locally available.
- Source rows created: 0.
- Extraction rows created: 0.
- Ingestion performed: no.
- Code added: no.

### Recommended Next Step

Ask the toolkit creator to confirm the actual backend adapter or provide an approved search API/client matching the proposed `web_search` contract before any live smoke test or five-city live pilot.

### Validation/Audit Results

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

---

## 2026-07-01T00:35:00-04:00 - Thursday report polish completed

**Commit:** pending in current session

### Current State After This Entry

- The main Thursday report draft has been polished for a toolkit-creator meeting.
- A shorter PDF-ready markdown companion now exists.
- The presentation outline now includes a worked JSON example and explicit Thursday decision points.
- No live web search was executed.
- No ingestion happened.

### What Changed

- Polished main report draft:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created PDF-ready abbreviated version:
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated presentation outline:
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- Updated this handoff log and `PROGRESS.md`.

### Main Polish Changes

- Added a short `What we built` section near the top.
- Added a `What this is / what this is not` subsection.
- Added one short worked JSON payload example from the seed demo.
- Reframed the open integration section as `Adapter-fit points for Thursday`.
- Added a final `Thursday decision points` section.
- Tightened wording to sound less like an internal repo log and more like a meeting document.

### PDF-Ready Artifact

- Created: `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Intended use: convert to PDF Wednesday night after final review.

### Status Checks

- Live web search executed: no.
- Ingestion performed: no.
- Seed counts unchanged: 5 city responses, 15 source rows, 34 extraction rows.

### Recommended Next Step

Convert the PDF-ready markdown to PDF Wednesday night after one final read for formatting and page length.

### Validation/Audit Results

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

---

## 2026-07-01T00:00:00-04:00 - Thursday report draft and presentation outline created

**Commit:** pending in current session

### Current State After This Entry

- The Thursday-facing report draft now exists and is presentation-ready in markdown.
- A short 9-slide presentation outline now exists as a separate markdown artifact.
- Report asset tables now exist under `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`.
- No live web search was executed.
- No ingestion happened.
- No production corpus tables or folders were modified.

### What Changed

- Created report draft:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created presentation outline:
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- Created report asset tables:
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/city_seed_demo_summary.csv`
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/design_choices_table.csv`
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/attribute_definitions_table.csv`
- Updated this handoff log and `PROGRESS.md`.

### Main Report Content

- Explains why city-by-city public-source discovery matters for the safety-wage project.
- States clearly that no built-in local GABRIEL web-search function was found.
- Documents the custom `get_all_responses_fn` scaffold and its callback signature.
- Explains the proposed live `web_search` backend contract and expected result keys.
- Summarizes the five-city seed demo, calibration examples, attribute definitions, guardrails, and bounded next-live-test plan.
- Frames the scaffold as acquisition/extraction assistance rather than production measurement.

### Seed Demo Snapshot Used In The Report

- Cities: Boston, Somerville, Newton, Wayland, Seekonk.
- City responses: 5.
- Source rows: 15.
- Extraction rows: 34.
- Live web search executed: no.
- Ingestion performed: no.

### Recommended Next Step

Review the Thursday report draft first, then convert it to PDF Wednesday night if the framing and level of technical detail look right.

### Validation/Audit Results

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

### Corpus Snapshot

```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

### Recommended Next Codex Run

If the report framing is approved, do a presentation-polish pass only: tighten executive language, decide whether the callback section needs one worked JSON example, and prepare a PDF conversion artifact. Do not switch into live search or ingestion work unless separately authorized.

---

## 2026-06-30T22:05:00-04:00 - scaffold contract refined

**Commit:** pending in current session

### Current State After This Entry

- No live web search was executed.
- The scaffold still runs in seed/dry-run mode and now has a concrete proposed live backend contract.
- `Response` is always a parseable JSON string, regardless of `json_mode`.
- Streaming is explicitly unsupported for now.
- Extraction is conceptually inside `custom_get_all_responses`, but the current live path remains a discovery-only placeholder because no safe backend exists locally.

### What Changed

- Refined `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py` to assume:
  - `web_search(query: str, *, max_results: int = 5, domains: list[str] | None = None, city: str | None = None, state: str | None = None) -> list[dict]`
- Fixed the expected discovery result keys to:
  - `title`
  - `url`
  - `snippet`
  - `source_domain`
  - `published_date`
  - `retrieval_status`
- Added structured error fields in the JSON response:
  - `status`
  - `error_type`
  - `error_message`
  - `source_candidates`
  - `extractions`
  - `notes`
- Added evidence-origin helper fields to the JSON payload shape where feasible:
  - `search_snippet`
  - `page_text_excerpt`
  - `evidence_origin`
- Updated the prompt template and design memo to include domain filters and result caps.
- Re-ran the seed demo successfully.

### Seed Demo Snapshot

- Seed demo ran: yes.
- City responses written: 5.
- Parsed source rows written: 15.
- Parsed extraction rows written: 34.
- Row counts changed: no.
- Live web search executed: no.

### Default Domain Filters

- Boston: `bostonpublicschools.org`, `boston.gov`, `btu.org`, `mass.gov`
- Somerville: `somervillema.gov`, `somerville.k12.ma.us`, `mass.gov`, `somervilleeducators.com`
- Newton: `newton.k12.ma.us`, `newteach.org`, `mass.gov`
- Wayland: `wayland.ma.us`, `mass.gov`
- Seekonk: `seekonk-ma.gov`, `seekonkschools.org`

### Recommended Thursday Talking Points

- The contract is now concrete enough to discuss adapter fit with the toolkit creator.
- The intended design is two-stage and token-efficient:
  1. source discovery with URLs and snippets
  2. GABRIEL extraction only on retained candidates
- The hook returns a full dataframe only; no streaming or retry protocol is assumed.
- If the toolkit creator already has a different discovery object shape, the main question is whether to adapt the backend into this contract or revise the scaffold.

### Recommended Next Codex Run

If the toolkit creator confirms a backend callable, adapt only the live path in `custom_get_all_responses` and rerun the same five-city bounded pilot with domain filters and capped results. Otherwise, keep the current scaffold as the Thursday demonstration artifact and do not attempt live search.

---

## 2026-06-30T21:00:00-04:00 - custom GABRIEL web-search scaffold added

**Commit:** pending in current session

### Current State After This Entry

- The repo still has no built-in local GABRIEL web-search function.
- A custom `get_all_responses_fn` scaffold now exists for Thursday demonstration use.
- The scaffold defaults to seed/dry-run mode using the existing five-city pilot CSVs.
- No live web search was executed.
- No ingestion happened, and no production corpus files were modified.

### What Changed

- Created custom hook scaffold: `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py`.
- Created seed demo runner: `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`.
- Created design memo: `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`.
- Updated the pilot summary note in `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`.
- Ran the seed demo and wrote:
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`

### Scaffold Status

- `custom_get_all_responses` implemented: yes.
- Required signature handled: `prompts`, `identifiers`, `json_mode`, `model`, `api_key`, `web_search`, `**kwargs`.
- Return shape: pandas dataframe with `Identifier` and `Response`.
- Default response mode: JSON payload string with `city`, `status`, `source_candidates`, `extractions`, and `notes`.
- Optional live path: placeholder only, bounded, off by default, and depends on a future callable `web_search` backend.

### Seed Demo Snapshot

- Seed demo ran: yes.
- City responses written: 5.
- Parsed source rows written: 15.
- Parsed extraction rows written: 34.
- Status: dry-run only; no live acquisition or search execution.

### Recommended Thursday Talking Points

- The local repo exposes direct model runners on local text, not a reusable web-search hook.
- The new scaffold shows the expected callback shape for city-by-city bounded source search plus extraction.
- The calibration harness is already attached through the 15 seeded source rows and 34 extraction rows.
- The toolkit creator still needs to specify the exact `web_search` callable contract, result schema, citation preservation behavior, and retry/rate-limit expectations.

### Recommended Next Codex Run

If the toolkit creator provides the real `web_search` backend shape, wire it into `custom_get_all_responses` and rerun only the same five-city pilot with strict result caps. If not, use the scaffold and memo as the Thursday integration discussion artifact and keep execution in seed mode only.

---

## 2026-06-30T18:55:45-04:00 - GABRIEL web-search extraction pilot seeded

**Commit:** pending in current session

### Current State After This Entry

- The v10 all-32 causal pilot is paused.
- The immediate priority shifted to a Thursday-facing GABRIEL web-search/source-extraction pilot.
- No local GABRIEL web-search function was found or executed.
- The repo contains GABRIEL scoring runners for local text inputs and ingestion fetcher scaffolding, but no safe city/query web-search interface that returns URLs, snippets, source classifications, or multi-attribute extractions.
- The pilot outputs are therefore design/seed artifacts from already known public leads and existing corpus metadata, not autonomous search results.
- No ingestion happened, and no production corpus files were modified.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Created source-discovery seed CSV: `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`.
- Created evidence-extraction seed CSV: `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`.
- Created presentation-ready summary memo: `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`.
- Created reusable city-search prompt template: `docs/acquisition/gabriel_websearch_city_prompt_template_2026-06-30.md`.
- Updated this handoff log and `PROGRESS.md`.

### Pilot Snapshot

- Pilot status: design/seed only; web-search function not executed.
- Cities covered: Boston, Somerville, Newton, Wayland, Seekonk.
- Source candidates retained: 15, with 3 per city.
- Extraction rows created: 34.
- Source families: BPS/BTU bargaining materials, Somerville police award packets, Newton teacher bargaining materials, Wayland JLMC/CBA sources, and Seekonk official archive CBAs.

### Calibration Status

- Boston BPS/BTU negotiations page was included as a seed calibration source, not rediscovered by local web search.
- Somerville police JLMC/arbitration materials were included as seed calibration sources, not rediscovered by local web search.
- Newton mechanism-proxy materials, Wayland fire JLMC, and Seekonk official CBA archive sources were included as seed checks for future live search.
- Boston BTU remains mechanism-proxy/discourse-lane evidence only; peer-wage comparison alone should not trigger `arbitration_or_impasse_backstop`.
- Ordinary grievance arbitration remains an exclusion boundary, illustrated with Wayland DPW and Seekonk DPW CBA rows.

### Open Decisions

- The toolkit creator needs to provide or expose the actual GABRIEL web-search invocation before this can become an executed acquisition assistant test.
- Future live runs should keep a hard cap by city and query, return source candidates before extraction, and preserve causal versus mechanism-proxy versus discourse lanes.
- Do not expand to ingestion until a separate ingestion task authorizes manual verification and pipeline processing.

### Recommended Next Codex Run

If the toolkit creator provides a callable GABRIEL web-search function, run the five-city pilot live using the template and compare returned sources against the seeded calibration rows. If no callable function is available, use the seed memo as the Thursday discussion artifact and ask for the missing web-search API shape: inputs, outputs, credentials, rate limits, and extraction schema.

---

## 2026-06-30T11:14:52-04:00 - v10 repaired gold retry completed

**Commit:** created by the session that added this entry; see latest `git log`

### Current State After This Entry

- The repaired v10 gold retry produced zero formal audit failures.
- Clean grievance-only traps stayed low.
- Clear positives stayed high.
- Boston BTU stayed at `0`, so peer-wage comparison alone still does not trigger v10.
- Arlington-style future reopener/impasse clauses scored `60`, which is an upper-middle result and remains an open construct-boundary issue.
- A small all-32 causal pilot is now reasonable, provided the run preserves source-type stratification and flags future reopener/impasse clauses for review.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Created repaired gold set: `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`.
- Created repair memo: `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`.
- Added path arguments to `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py` so repaired retries do not overwrite first-run files.
- Created repaired input: `analysis/gabriel_pilot/input_v10_gold_repaired_2026-06-30.csv`.
- Ran one bounded repaired retry.
- Created repaired retry results: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv`.
- Created repaired retry audit: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_audit_2026-06-30.csv`.
- Created repaired retry report: `docs/analysis/gabriel_v10_gold_repaired_dryrun_report_2026-06-30.md`.
- Updated the v10 design memo, this handoff log, `PROGRESS.md`, and API spend log.

### Arlington Construct Decision

`ma_arlington_public_works_2018` is no longer coded as a `false_positive_trap`.

Final repaired coding:

- `gold_label = ambiguous`
- `expected_score_band = 26_50`
- `evidence_type = mediation_impasse`
- `boilerplate_grievance_arbitration_trap = no`
- `economic_terms_link = yes`

Reason: Article XXX is a future reopener clause that allows mediation/factfinding under Chapter 1078 if agreement cannot be reached and expressly references money issues. That is not grievance-arbitration boilerplate. It is also not a clean award-style positive because the text does not show that the process was invoked or that it resolved wages.

`ma_arlington_public_works_2015` was added as a second ambiguous future-reopener/impasse edge case with the same coding logic.

### Repaired Gold-Set Composition

- Total rows: 12
- Clear positives: 3
- Clear negatives: 3
- False-positive traps: 4
- Ambiguous / future-reopener edge cases: 2
- Mechanism-proxy rows: 1

Important repair:

- `ma_wayland_public_works_2020` was recoded from `clear_negative` to `false_positive_trap` because the full text has a grievance-and-arbitration procedure limited to interpretation/application of the agreement, with no successor-contract impasse signal.

### Repaired Retry Results

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | `100, 92, 78` | 90.0 | 78 | 100 |
| `clear_negative` | 3 | `10, 0, 0` | 3.3 | 0 | 10 |
| `false_positive_trap` | 4 | `5, 15, 10, 5` | 8.8 | 5 | 15 |
| `ambiguous` | 2 | `60, 60` | 60.0 | 60 | 60 |

Boundary results:

- Clean grievance-only traps stayed at or below `25`: yes.
- Clear positives stayed at or above `51`: yes.
- Clear negatives stayed at or below `25`: yes.
- Boston BTU mechanism-proxy negative stayed low: yes, score `0`.
- Future reopener/impasse cases landed in an upper-middle band: `60`, plausible but worth flagging.
- Formal audit failures: 0.
- Prompt revision recommended: no.

### Open Construct Boundary

The remaining design decision is whether future reopener clauses with mediation/factfinding and money-issue language should count as moderate v10 evidence even when the document does not show the process was invoked.

If the PI wants v10 to count only invoked backstops, add a stricter prompt rule before the all-32 run. Otherwise, keep the current prompt and flag these cases during review.

### Recommended Next Codex Run

Run a small all-32 causal pilot for `arbitration_or_impasse_backstop`, not a production dataset. Preserve the repaired prompt, write new v10-only outputs, stratify by `source_type`, and add a review flag for future reopener/impasse clauses.

---

## 2026-06-30T10:56:17-04:00 - v10 gold dry-run completed

**Commit:** `ed67ffa` (`Dry run v10 prompt on gold set`)

### Current State After This Entry

- Do **not** run the all-32 v10 causal pilot yet.
- The candidate `arbitration_or_impasse_backstop` prompt handled ordinary grievance-arbitration boilerplate reasonably well.
- The gold set needs repair around Arlington-style future reopener/impasse clauses before broader scoring.
- H1 remains plausible but underidentified; v9 and v10 both still require strong source-type caveats.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Added bounded v10 gold-only runner: `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py`.
- Created gold-only input: `analysis/gabriel_pilot/input_v10_gold_2026-06-29.csv`.
- Ran one v10 dry-run on only the 11-row gold set.
- Created results: `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv`.
- Created audit: `analysis/gabriel_pilot/results_v10_gold_dryrun_audit_2026-06-29.csv`.
- Created report: `docs/analysis/gabriel_v10_gold_dryrun_report_2026-06-29.md`.
- Updated v10 design memo: `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`.
- Updated `PROGRESS.md` and `logs/api_spend_log.csv`.

### Dry-Run Design

- Scope: 11 hand-coded gold rows only.
- Not run on all 32 causal rows.
- Causal rows used existing local source text from `analysis/gabriel_pilot/input_v9.csv`.
- Boston BTU stayed in the separate mechanism-proxy lane and used only existing memo/locator context.
- No documents were ingested, downloaded, or added to `corpus/`.
- No v8/v9 outputs were modified.

### Results

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | `96, 96, 88` | 93.3 | 88 | 96 |
| `clear_negative` | 4 | `0, 10, 0, 0` | 2.5 | 0 | 10 |
| `false_positive_trap` | 4 | `20, 70, 10, 15` | 28.8 | 10 | 70 |

Boundary results:

- Clear positives all scored at or above `51`.
- Clear negatives all scored at or below `25`.
- Boston BTU mechanism-proxy negative scored `0`.
- Three of four false-positive traps stayed at or below `25`.
- Formal audit result: 10 of 11 rows passed.
- Retry run: no.

### Main Interpretation

The lone formal failure was `ma_arlington_public_works_2018`, which scored `70` despite being labeled as a false-positive trap. Manual inspection found that the full text contains an Article XXX duration/reopener clause referencing an impasse procedure with mediation/factfinding and money issues. That is not ordinary grievance-arbitration boilerplate.

This means the first dry-run did **not** clearly fail on the main feared prompt boundary. Instead, the Arlington row is probably a contaminated gold row or an unresolved construct-boundary case.

### Decisions Carried Forward

- Do not revise the grievance-arbitration exclusion based on this run; it worked on Boston SENA, Seekonk DPW, and Seekonk teachers.
- Do not proceed to an all-32 causal pilot yet.
- Resolve whether future reopener clauses with mediation/factfinding and money-issue language should count for v10.
- Improve the local v10 relevance screen before broader use; it over-filtered some JLMC/stipulated-award and impasse evidence.

### Checks

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

### Recommended Next Codex Run

Repair the v10 gold set before any all-32 causal pass:

1. Inspect Arlington DPW Article XXX and decide whether future reopener/impasse clauses count.
2. Recode Arlington as ambiguous/weak-positive if those clauses count, or add a stricter prompt rule if only invoked backstops count.
3. Add at least one clean grievance-only DPW trap.
4. Add one or two future-reopener/impasse edge cases.
5. Run one bounded gold-set retry.

---

## 2026-06-29T22:13:16-04:00 - v10 gold set and first handoff created

**Commit:** `4ff2b57` (`Create v10 gold set and ChatGPT handoff`)

### State After This Entry

- The project had a reusable ChatGPT handoff for future planning.
- The immediate recommended next step was to dry-run the v10 prompt on the 11-row gold set before any broader `arbitration_or_impasse_backstop` pass.
- The main implementation risk was false positives from ordinary grievance-arbitration boilerplate in CBAs.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### Research Interpretation

- H1 remained plausible but underidentified.
- GABRIEL v9 found its clearest `comparability_emphasis` signal in safety-side arbitration/award-style documents, especially the Somerville police awards.
- Ordinary CBAs and MOAs generally scored low on v9 comparability.
- The strongest non-safety peer-wage comparison found so far was the official Boston BTU bargaining page, but that evidence was mechanism-proxy/discourse-lane rather than causal-corpus reasoning text.
- The central caveat was source type and document production: explicit reasoning appears where institutions force it onto the page, not necessarily wherever it matters in bargaining.

### What Changed

- Created the first hand-coded v10 gold set: `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`.
- Created the gold-set memo: `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`.
- Created the first `docs/analysis/chatgpt_handoff_latest.md`.
- Added a gold-set pointer to `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`.
- Made a small filename-date cleanup in `docs/acquisition/ma_newton_somerville_boston_mechanism_source_plan_2026-06-26.md`.
- Updated `PROGRESS.md`.

### Gold-Set Composition

- Total rows: 11
- Clear positives: 3
- Clear negatives: 4
- False-positive traps: 4
- Ambiguous rows: 0
- Mechanism-proxy rows included: 1
- Main trap class: grievance-arbitration boilerplate in ordinary CBAs

Positive anchors:

- `ma_somerville_police_spsoa_2012`
- `ma_somerville_police_spea_2012`
- `ma_wayland_fire_jlmc_2020`

Negative/trap anchors:

- Wayland DPW and library ordinary CBAs
- Worcester fire safety-side negative
- Boston SENA, Arlington DPW, Seekonk DPW, and Seekonk teachers as arbitration-boilerplate traps
- Boston BTU bargaining page as a mechanism-proxy negative for peer-wage comparison alone

### Key Artifact Paths

- v9 preliminary report: `reports/6_25/v2/GABRIELv9_preliminary.pdf`
- Public-source strategy note: `docs/hypotheses_public_source_strategy_2026-06-24.md`
- Mechanism-source summary: `docs/analysis/mechanism_source_summary_2026-06-26.md`
- Boston BTU deep dive: `docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md`
- Comparator network design memo: `docs/analysis/comparator_network_design_2026-06-29.md`
- Comparator synthesis memo: `docs/analysis/comparator_edge_synthesis_2026-06-29.md`
- Comparator stub CSV: `docs/analysis/comparator_mentions_stub_2026-06-29.csv`
- v10 design memo: `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`
- v10 gold set CSV: `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- v10 gold set memo: `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`

### Open Decisions At This Point

- Whether the v10 attribute should stay causal-corpus-only for its first run, or whether a separate mechanism-proxy lane should be scored later.
- Whether the 11-row gold set was enough for prompt tuning, or whether a second-round set should add ambiguous edge cases.
- Whether the next empirical priority was a v10 pilot, more comparator extraction, or broader mechanism-source acquisition.

### Checks

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

### Recommended Next Codex Run At This Point

Use the gold set to draft and test exact v10 prompt language against the 11 hand-coded rows, with special attention to keeping grievance-arbitration boilerplate near `0` to `1_25` and keeping Boston BTU negative despite its strong peer-wage content.
