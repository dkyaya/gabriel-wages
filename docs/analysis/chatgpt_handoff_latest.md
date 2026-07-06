# ChatGPT Handoff Log

Reverse-chronological handoff for ChatGPT/Codex planning. Unlike `PROGRESS.md`, this file is more explicit about current interpretation, artifact paths, open decisions, and the recommended next run.

Last updated: `2026-07-07T04:00:00-04:00`

---

## 2026-07-07T04:00:00-04:00 - PI-facing report outline, draft, review checklist, and production plan created

**Commit:** pending in current session (`Draft safety and non-safety wage mechanisms report`)

### Current State After This Entry

- Confirmed the prior pre-report must-have evidence review session's changes (`016711c`, "Review must-have evidence before report") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/report_outline_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_draft_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_production_plan_safety_non_safety_wage_mechanisms_2026-07-06.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added. **No PDF, DOCX, PPTX, or other final-formatted artifact was created** — this run produced a markdown draft and supporting planning files only, per the task's explicit scope boundary.

### What This New Package Does

- **Report outline and claims map** (`report_outline_...md`): a detailed pre-draft planning document covering the title block, intended audience/purpose, a section-by-section breakdown (purpose, key claims, evidence basis, caveats, tables/callouts, and what-not-to-overclaim for each of the report's 8 sections), a report-level claim hierarchy (central / supporting / caveats / source-design findings / deferred), recommended tables and callouts, and 5 explicitly flagged open decisions for the PI (custodial/facilities naming, dispatcher prominence, transit's space allocation, nurse_health's placement, appendix sizing).
- **Report draft** (`report_draft_...md`): the full PI-facing markdown draft, using the exact specified title/subtitle. Contains an Executive Summary (4 paragraphs), 8 Main Takeaways, an 11-row Evidence Map table, Group-by-Group Findings for all 11 groups (police, fire, teachers, DPW, clerical/admin, library, custodial/facilities, dispatchers, nurse_health, sanitation, transit — each with status/mechanisms/evidence-basis/MA-notes/national-caveat/source-needs), a Mechanism-by-Mechanism Synthesis across all 13 specified mechanisms, a Massachusetts and National Nuance section naming the three distinct MA wage-impasse regimes now identified (JLMC, ordinary Chapter 150E, and the MBTA's own M.G.L. c. 161A statute), a tiered (must-have/useful/optional-deferred) Source Needs section, and 4 appendix tables.
- **Central narrative preserved:** the draft states directly that the key distinction is not "safety is hard, non-safety is easy" but "police/fire combine real upward pressure with a stronger pressure-to-wage conversion institution (JLMC), while non-safety groups' real pressures translate through classification systems, buffering, outsourcing, governance distance, budget constraints, or a weaker impasse pathway."
- **Review checklist** (`report_review_checklist_...md`): flags claims needing PI review (the central-finding framing, group-retention labels, custodial/facilities completeness claim, the Iowa counterexample's prominence), claims needing source strengthening before a final version (the dispatcher wage-tier comparison, nurse_health's single-city generalizability, sanitation's unconfirmed signals, transit's single-data-point finding), open formatting decisions, tables that may be too large, sections that may need tightening, 5 suggested PI questions, and an artifact-generation readiness checklist.
- **Production plan** (`report_production_plan_...md`): recommends DOCX first, then PDF; explains how to apply the Georgia/11pt/charcoal-heading/Harvard-crimson-accent style guide; allocates which tables belong in main text vs. appendix; proposes filename conventions; explains how to preserve file-name citations for auditability; and states explicitly what not to do (no new corpus rows, no OEWS build, no PRRs, no GABRIEL restart) until source acquisition is separately approved.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route the report draft and review checklist to the user/PI for review.
2. Once PI feedback is incorporated, proceed to a dedicated formatting run (DOCX first, then PDF) per the production plan.
3. Do not begin any new source-acquisition run, OEWS/municipal descriptive baseline build, or GABRIEL work from this state.

### Notes For ChatGPT Review

- This report draft is explicitly not a final, causal-evidence document — every claim in it is graded as current-corpus evidence, external/national context, or an identified source need, and the draft's own language ("current corpus shows," "evidence suggests," "requires additional sourcing") should be preserved in any future edit rather than tightened into unhedged assertions.
- Do not generate any PDF, DOCX, or PPTX from this draft without first routing it through PI review per the review checklist — the task explicitly deferred artifact generation to a later run.
- The group-retention frame used in this draft (central/strong comparison/public-safety-adjacent/secondary/source-design case/deferred) was supplied as a fixed input for this run; any future revision to that frame should originate from PI feedback, not from a future session's own re-derivation.
- Every claim in the draft traces to an already-existing session memo or CSV; no new corpus review or web research occurred this session.

---

## 2026-07-07T01:00:00-04:00 - Dispatchers, custodial/facilities, and nurse_health confirmed via direct corpus re-reads

**Commit:** pending in current session (`Review must-have evidence before report`)

### Current State After This Entry

- Confirmed the prior all-groups audit session's changes (`c111829`, "Audit wage mechanisms across groups") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.md`
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.csv`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (Section 11 rows NH01/CF01/CF02/DP-D01/DP-D02/DP-D03 upgraded from `not searched`/assumed to `confirmed in current corpus`; intro and Section 14 updated)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (5 rows updated to `current_corpus`; no rows added/deleted)
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv` (4 new rows appended, H40-H43, previously missing from this table)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified — a bounded OCR pass on Wayland's already-collected CBA was performed entirely under `/tmp/`, never written back. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a verification/confirmation pass, not a new mechanism-development session — every finding traces to already-collected corpus text.

### What This New Package Does

- **Arlington dispatchers, confirmed.** Direct re-read of `ma_arlington_public_works_2015` found a dedicated Article XXI ("Community Safety Dispatchers"): 9-person complement plus Lead Dispatcher, minimum-coverage-of-two rule, EMD stipend, and a requirement that dispatcher vacations be approved by "the Chief of Fire or Police." No per-classification base-wage table exists in this CBA (only unit-wide % increases; actual rates live in an external Classification and Pay Plan document not in this project's corpus). `binding_arbitration_statute` confirmed as MA G.L. c. 150E, not JLMC.
- **Custodial/facilities, confirmed.** Georgetown's and Franklin's custodial CBAs both contain complete, multi-step salary schedules with genuine classification tiers — Georgetown's Licensed-vs-Unlicensed Maintenance pay differential (~11%) directly parallels DPW's CDL/hoisting-license findings. Arlington adds supplementary bundled evidence.
- **Wayland nurse_health/dispatch, confirmed via a bounded OCR pass.** A 48-page, previously cover-page-only-readable scan was fully OCR'd (2,186 lines). Found substantive, dollar-figure wage-grade tables for both Community Health Nurses/Public Health Nurse (G-15/G-7A) and JCC Dispatcher/Coordinator (G-3/G-4), a Masters-degree nursing stipend, and a documented wage-restraint finding (nurse wages excluded from a 2022 compensation study). No custodial content exists in this document. The unit spans at least 9 distinct professional fields — far more fragmented than its name suggests.
- **Group-retention recommendations upgraded:** dispatchers → `keep_public_safety_adjacent` (confirmed); custodial/facilities → `keep_strong_comparison` (confirmed, schema-blocked only administratively); nurse_health → `keep_secondary` (upgraded from `defer`; substantive but single-city/fragmented-unit).

### Checklist, Roadmap, Source-Needs, and Hypothesis-Disposition Updates

- `wage_mechanism_evidence_checklist.md` Section 11's six rows (NH01, CF01, CF02, DP-D01, DP-D02, DP-D03) all moved from `not searched`/assumed to `confirmed in current corpus`, with full evidentiary detail.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the confirmations and the recommended move to PI-facing report planning.
- `all_groups_source_needs_2026-07-06.csv`: 5 rows updated from `partial`/`absent` to `current_corpus` (Arlington dispatcher text, Wayland OCR ×2, Georgetown/Franklin custodial full-text, Arlington/Wayland `binding_arbitration_statute` check); no rows added or deleted.
- `hypothesis_disposition_audit_2026-07-06.csv`: H40-H43 appended (they existed in the hypothesis matrix since the prior session but had never been dispositioned in this table) — H41 (custodial outsourcing) and H42 (dispatch coverage pressure) now `keep_central`/`strong_current_corpus`; H40 (nurse_health) and H43 (dispatch civilian-status undertranslation) `keep_supporting`/`moderate_current_corpus`.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Move to PI-facing report outline/planning, using the updated group-retention table (`pre_report_must_have_evidence_review_2026-07-06.md` §6) as the current state of record.
2. Bring the `custodial`/`facilities` schema decision to the user/PI in parallel with report planning, not as a blocking prerequisite.
3. No further OCR or re-extraction pass is needed for any of the three documents reviewed this session.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Do not re-request an OCR pass on `ma_wayland_afscme_1_2_2020_2023.pdf` — this session's extraction is complete (2,186 lines) and sufficient; the temporary OCR files exist only under `/tmp/` and are not part of this repository.
- Do not treat Arlington's dispatcher evidence as including a base-wage comparison to police/fire — no per-classification dollar table exists in this specific CBA; that comparison remains open (see H43's evidence_status).
- Do not treat nurse_health as a strong, headline comparison group — the evidence is genuinely substantive but rests on one city inside an unusually fragmented, nine-profession bargaining unit; report it as a secondary finding with that composition caveat stated explicitly.
- The `custodial`/`facilities` occupation_class schema decision remains open and is a user/PI action item, not something this or any prior session has authority to resolve by editing `data/contracts.csv`.

---

## 2026-07-06T22:00:00-04:00 - All groups scoped and audited; next-stage synthesis inputs prepared

**Commit:** pending in current session (`Audit wage mechanisms across groups`)

### Current State After This Entry

- Confirmed the prior transit governance-fit session's changes (`cf6e32b`, "Scope transit governance and wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_remaining_groups_scope_2026-07-06.md`
  - `docs/analysis/non_safety_remaining_groups_source_gaps_2026-07-06.md`
  - `docs/analysis/all_groups_wage_mechanism_audit_2026-07-06.md`
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv`
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 11 for nurse_health/custodial/dispatchers, 7 rows; Sections 12-16 renumbered; Purpose section updated with pointers to the 3 new synthesis files; Section 14 gained 2 new corpus-evidence-summary bullets)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H40-H43)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (2 new forward-looking rows; 1 existing row's notes extended; no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- **This is not the final PI-facing report.** This session prepared the audit and recommendations (`all_groups_wage_mechanism_audit_2026-07-06.md`, `all_groups_source_needs_2026-07-06.csv`, `hypothesis_disposition_audit_2026-07-06.csv`) that will feed a later report whose format is decided separately.

### What This New Package Does

- **Scopes the three remaining ambiguous non-safety groups** (nurse_health/public health, custodial/facilities, dispatchers) with a full corpus-coverage check, Massachusetts/national context, and per-group recommendations. The most consequential finding: a direct re-read of already-collected corpus text (no new ingestion) found genuine hidden/bundled content for all three groups on the first scoping pass — `ma_wayland_other_2021` (coded `other`) names "nurses" and "dispatch" in its own metadata; a `pdftotext` re-read of Arlington's already-collected `public_works` CBA confirmed explicit "Community Safety Dispatchers" language (9-person complement, minimum-coverage-of-two rule); `ma_georgetown_other_2020`/`ma_franklin_other_2022` are confirmed custodial units mislabeled `other` for lack of a controlled-vocabulary value.
- **Recommendations:** nurse_health — defer (thinnest corpus foothold, sharpest population-mismatch risk vs. national hospital-nursing data); custodial/facilities — include, pending a `custodial`/`facilities` schema decision; dispatchers — include as a distinct **public-safety-adjacent** category (neither ordinary non-safety nor safety-equivalent), contingent on a full re-read of the Arlington text and independent verification of the dispatcher-bearing rows' `binding_arbitration_statute` field (not yet assumed by extension).
- **Audits all 11 groups examined to date** (police, fire, teachers, DPW, clerical/admin, library, sanitation, transit, nurse_health, custodial/facilities, dispatchers) across mechanism strength, evidence basis, design fit, source needs, and national/Massachusetts nuance, plus a 20-row mechanism-by-mechanism table.
- **Recommended narrative:** police/fire combine multiple genuine upward-pressure mechanisms (recruitment strain, overtime spirals, hazard/credentialing, political salience) with a strong, direct translation institution (JLMC). Every other group faces real pressures of its own — DPW's water/wastewater retirement wave, sanitation's fatal-injury-rate comparison, teachers' documented shortage, dispatchers' own 24/7 minimum-staffing rule — but these translate through classification/reclassification systems, staffing substitution, service buffering, contractor/governance distance (transit, sanitation for a majority of cities), or civilian-status classification (dispatchers), not through a comparable direct institutional backstop.
- **Dispositions all 39 hypothesis-matrix rows** (14 keep_central, 12 keep_supporting, 3 merge — H3/H12 as a compensating-differentials pair — 4 demote, 3 defer, 0 drop_for_now) in `hypothesis_disposition_audit_2026-07-06.csv`.
- **Structures 44 source-target rows** by priority (must_have/useful/optional/defer) across all groups in `all_groups_source_needs_2026-07-06.csv`, with no source fetched or ingested.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 11 ("Nurse_health, custodial/facilities, and dispatcher mechanisms checklist," 7 rows: NH01-NH02, CF01-CF02, DP-D01-DP-D03), with Sections 12-16 renumbered from the prior 11-15; the Purpose section now points to the 3 new all-groups synthesis files; Section 14 (corpus evidence summary) gained bullets for transit and for the 3 remaining groups.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the scoping/audit/source-needs work and its recommended next steps.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv`: 4 new rows appended (H40-H43: `nurse_health_professional_labor_market_pressure`, `custodial_facilities_outsourcing_and_service_buffering`, `dispatch_public_safety_adjacent_coverage_pressure`, `dispatch_civilian_status_undertranslation`), via the same surgical append-only technique validated in prior sessions. Existing 39 rows confirmed unchanged (`git diff --numstat`: 4 insertions, 0 deletions).
- `police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv`: 2 new forward-looking rows (`custodial_facilities` → Janitors and Cleaners SOC 37-2011; `dispatchers` → Public Safety Telecommunicators SOC 43-5031), both explicitly flagged as not-yet-controlled-vocabulary `project_occupation_class` values; 1 existing `nurse_health` row's notes extended. No OEWS data build.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Close the "must-have" zero-cost, already-in-corpus items: full re-read of Arlington's dispatcher text for wage/step data; OCR re-extraction of `ma_wayland_afscme_1_2_2020_2023.pdf`; full-text re-read of the two already-collected custodial CBAs (Georgetown, Franklin).
2. Bring the `custodial`/`facilities` controlled-vocabulary schema decision to the user/PI.
3. Prepare the PI-facing report next (format TBD, decided separately), using this session's audit/source-needs/hypothesis-disposition files as direct inputs — do not run a broader new source-acquisition plan first.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- This session is explicitly **not** the final PI-facing report — it prepares the audit and recommendations that will feed one; do not treat any file created this session as report-ready prose without further editorial work.
- Do not assume dispatchers are Chapter 150E-covered by extension the way sanitation's institutional finding was (SN09) — this was explicitly flagged as an open, not-yet-independently-verified question for the two dispatcher-bearing rows (Arlington, Wayland).
- Do not cite the nurse_health, custodial/facilities, or dispatcher findings as "confirmed in current corpus" beyond the specific already-collected-text findings described above (Arlington's dispatcher language; Georgetown's/Franklin's custodial metadata) — every other claim for these three groups is either external context or an unread/unOCR'd fragment.
- This project's corpus still holds zero `nurse_health` rows and no `custodial`/`dispatcher`-classified rows at all (schema gap); nothing in this session changed that.

---

## 2026-07-06T18:00:00-04:00 - Transit governance and wage mechanisms scoped; deferred as governance-mismatched

**Commit:** pending in current session (`Scope transit governance and wage mechanisms`)

### Current State After This Entry

- Confirmed the prior Seekonk public works sanitation-language scan (`7bc8776`, "Scan Seekonk public works sanitation language") was already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_transit_governance_mechanism_scope_2026-07-06.md`
  - `docs/analysis/non_safety_transit_governance_scan_2026-07-06.csv`
  - `docs/analysis/non_safety_transit_source_gaps_2026-07-06.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 10, "Transit mechanisms checklist," 9 rows TR01-TR09; Sections 11-15 renumbered; XC09 cross-referenced)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H36-H39)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (one small annotation to the existing `transit` row's `notes` field; no new row, no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a governance-fit assessment and mechanism-scoping session, not a corpus-build, source-acquisition, or GABRIEL session — it resolves the transit scoping decision left open since `wage_mechanism_project_checkpoint_2026-07-05.md` §11 (item 2).

### What This New Package Does

- Confirms zero `transit` rows exist in `data/contracts.csv` or `data/city_coverage.csv`, and confirms (via a full-field keyword search) that no existing row contains genuine transit-, bus-, transport-, traffic-, or parking-related content.
- **Classifies all nine current project cities' transit governance via bounded web research:** four (Arlington, Boston, Newton, Somerville) fall under the MBTA (a Massachusetts state authority, M.G.L. c. 161A); five (Franklin, Georgetown, Seekonk, Wayland, Worcester) fall under a regional transit authority (GATRA, MeVa/MVRTA, MWRTA, WRTA respectively), with Seekonk uniquely also served by Rhode Island's RIPTA. **Zero `city_operated_transit` cases were found.**
- **Most consequential finding:** Massachusetts RTAs are required by M.G.L. c. 161B to contract actual operations to a private operating company — directly confirmed for Worcester, where WRTA's unionized (ATU Local 22) bus operators are employed by First Transit, Inc./Central Mass Transit Management (CMTM), not WRTA or the City of Worcester. This is a structurally deeper, state-law-mandated version of sanitation's private-hauler finding, applying uniformly across all five RTA-served cities rather than as a city-level choice.
- **A genuinely new institutional finding:** the MBTA has its own compulsory interest-arbitration statute (M.G.L. c. 161A §§19C-19G), distinct from both JLMC (police/fire) and Chapter 150E §9 (teachers/DPW/clerical-admin/library/sanitation-by-extension) — a third Massachusetts arbitration regime this project had not previously catalogued, though it governs the MBTA's own employees as a state authority, not any of this project's nine city governments.
- **Sharpest quantified wage-to-staffing finding in this project to date, for any occupation:** the MBTA's 2024 bus-operator starting-pay raise ($22.21 to $30/hour) was followed by a reported 365% surge in operator applications — a state-authority-specific data point, not yet shown to generalize to any RTA or a smaller wage adjustment.
- **Governance-fit conclusion:** transit does not fit this project's city-level matched-CBA design, for all nine current cities without exception. Recommends deferring transit indefinitely as governance-mismatched, rather than developing it as a fifth non-safety comparison group.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 10 ("Transit mechanisms checklist," 9 rows: TR01-TR09, explicitly marked as scoping-stage since zero corpus rows exist), with Sections 11-15 renumbered from the prior 10-14; XC09 (arbitration/impasse backstop) cross-referenced with the new MBTA c. 161A finding.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming transit's governance-fit scoping is complete and recommending deferral.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H36-H39: `transit_route_service_coverage_pressure`, `transit_operator_shortage_and_missed_service`, `transit_contracting_governance_distance`, `transit_service_cut_buffering`); the existing 35 rows were not touched (confirmed via `git diff --numstat`: 4 insertions, 0 deletions).
- `police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` gained one small annotation to the existing `transit` row's `notes` field only (confirmed via `git diff --numstat`: 1 insertion, 1 deletion — a single-cell edit); no new row, no OEWS data build.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Defer transit indefinitely as governance-mismatched; do not pursue targeted transit source acquisition as this project's next comparison-group development step.
2. If a future, explicitly non-matched-city institutional case study is ever wanted, the MBTA's ATU Local 589 CBA/c. 161A arbitration history and WRTA's CMTM/ATU Local 22 arrangement are the two most information-rich targets identified — each requires its own explicit authorization before any acquisition.
3. Move to the checkpoint memo's other still-open scoping decisions (nurse_health's population mismatch; custodial/facilities and dispatcher schema questions) or a broader non-safety source-acquisition-gap review next, per user/PI direction.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Every transit finding in this session is bounded public-source desk research classifying governance *structure*, not a corpus-confirmed wage mechanism — do not cite any finding as "confirmed in current corpus" (this project's corpus holds zero `transit` rows).
- Do not conflate the MBTA's c. 161A compulsory-arbitration finding with this project's central JLMC-vs-Chapter-150E police/fire-vs-non-safety-municipal-employee finding — c. 161A governs a state authority's own employees, not any of this project's city governments, and does not change that central finding.
- Do not treat WRTA's CMTM/First Transit arrangement as evidence about GATRA, MeVa, or MWRTA specifically — the private-operator model was directly confirmed only for WRTA this session; its extension to the other three RTAs is a reasonable inference from the general M.G.L. c. 161B requirement, not an independently verified fact for each.
- Do not treat the MBTA's 2024 wage-raise-then-hiring-surge finding as evidence about any of this project's nine city governments — it describes the MBTA's own workforce as a state authority.
- This project's corpus still holds zero `transit` rows; nothing in this session changed that, and this session's governance-fit conclusion recommends against pursuing acquisition that would change it under the current design.

---

## 2026-07-06T15:30:00-04:00 - Seekonk public works CBA sanitation language scan completed

**Commit:** pending in current session (`Scan Seekonk public works sanitation language`)

### Current State After This Entry

- Confirmed the prior sanitation service-structure scan's changes (immediately prior, same date) were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.md`
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.csv`
- Updated:
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (light: 2026-07-06 update note to gap item 2)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (light: SN08 row update)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new 2026-07-06 update block)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a bounded, existing-corpus inspection session: read the already-collected Seekonk public works CBA in full (PDF text extraction, 675 lines), searched systematically for sanitation-related language, and classified the evidence.

### What This New Package Does

- Inspects the already-collected `ma_seekonk_public_works_2023` CBA full text for explicit and bundled sanitation/solid-waste language, the zero-cost next step recommended by the prior city-service-structure scan.
- **Finding: `sanitation_possible_but_unconfirmed`.** Zero explicit sanitation terminology found anywhere in the document. Two substantive-but-unconfirmed signals: (1) "Transfer Station" explicitly named in the hours-of-work section with different scheduling (any consecutive 5 days excluding Sunday), but no linked job title or duty description; (2) CDL training reimbursement mentioned for "eligible employees," consistent with truck-operation roles, but not explicitly sanitation-linked.
- **Remaining uncertainties:** whether the PDF's text extraction captured all Appendices and job-description Schedules (direct re-opening of the original PDF recommended); whether Seekonk's town operates its own curbside collection or contracts it out (marked "mixed/unclear" in the prior city-service-structure scan); and whether Transfer Station/CDL language together suffice to classify sanitation work as present in the unit.
- **Recommended integration:** combine this contract-inspection finding with Seekonk's service-delivery-structure verification to reach a final determination on whether Seekonk should be treated as a `sanitation_dpw_bundled` site (if municipal-staffed and Appendix-confirmed) or remain unresolved.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Confirm whether the original Seekonk public works PDF contains a job-description Appendix/Schedule that text-extraction may have missed.
2. If Appendix exists, integrate with Seekonk's service-structure determination to classify the row as sanitation-relevant or not.
3. Do not authorize Worcester or Somerville acquisition efforts as immediate follow-ons.

### Notes For ChatGPT Review

- This is an existing-corpus inspection only; no new document was acquired or ingested.
- `data/contracts.csv` was **not** edited — the Seekonk row remains as-is, classified as "possible but unconfirmed."
- Do not cite Transfer Station or CDL language as confirmed sanitation work until Appendix/service-structure questions are resolved.

---

## 2026-07-06T14:00:00-04:00 - Sanitation service structure mapped across current project cities

**Commit:** pending in current session (`Map sanitation service structure`)

### Current State After This Entry

- Confirmed the prior sanitation-scoping session's changes (`136fc29`, "Scope sanitation wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.md`
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.csv`
- Updated:
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (light: scan-completed note; gap item 2 closed)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (light: Section 9 scan-completed note)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (surgical single-cell extensions to H33 and H35 only; 35 rows/12 columns otherwise unchanged)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a bounded, public-source desk-research session classifying residential sanitation service structure (municipal / private-contractor / regional / mixed / DPW-bundled) for this project's 9 current cities — not a corpus-build, ingestion, or GABRIEL session.

### What This New Package Does

- Classifies all 9 current project cities (Arlington, Boston, Franklin, Georgetown, Newton, Seekonk, Somerville, Wayland, Worcester) into a controlled `preliminary_service_structure` vocabulary using each city's own trash/DPW/procurement web pages and (for Newton) regional news coverage.
- **5 of 9 cities (Arlington, Boston, Franklin, Georgetown, Newton) show clear private-hauler contracting** for residential collection — meaning sanitation workers there are structurally unlikely to appear in any municipal CBA this project could collect.
- **Seekonk, Wayland, and Worcester show a DPW-bundled/mixed structure**, where collection duties are plausibly folded into existing `public_works` job descriptions rather than organized as a distinct title.
- **Somerville is `dpw_bundled_unclear`** (lower confidence) — it has zero `public_works` rows in this project's corpus and is independently one of the three cities on this project's longstanding unmatched-safety-unit list.
- **Most consequential new finding:** a July 2025 Republic Services/Teamsters strike hit Newton and 13 other Boston-area suburbs simultaneously, confirming that private-hauler workforces can be unionized, but typically as multi-city, private-sector bargaining units — a genuine design-fit problem for this project's one-city-one-municipal-bargaining-unit comparison logic, not merely a data-availability inconvenience.
- **Two concrete, ranked future source targets:** (1) Seekonk — a zero-cost re-read of the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content, since the town's Pay-As-You-Throw program is run by the same DPW; (2) Worcester — a higher-effort new-source-identification target, since the existing `ma_worcester_public_works_2017` row is confirmed clerical-only ("DPW Clerks"), leaving Worcester's actual field/operations DPW workforce entirely unrepresented. Somerville is a third, lower-confidence lead. The other 5 cities are explicitly **not** recommended as near-term acquisition targets.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` Section 9 gained one scan-completed note pointing to SN08/H35 (`sanitation_dpw_bundling`) and SN06/H33 (`sanitation_contractor_substitution`). Not rewritten.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the scan and its recommended next steps.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv`: H33 (`sanitation_contractor_substitution`) and H35 (`sanitation_dpw_bundling`) had their `non_safety_relevance_or_counterpoint` fields extended with this session's city-specific findings, via exact-string surgical edits (not a full-file rewrite, to preserve the file's legacy quoting convention). No new rows; 35 rows/12 columns confirmed unchanged.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Re-read the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content — zero-cost, no new ingestion required.
2. Treat a Worcester field/operations-DPW source-identification effort, and a broader Somerville DPW/general-government source-acquisition effort, as separate future tasks requiring their own explicit authorization — not a default next step from this state.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a five-city web pilot as the immediate next step from this state.

### Notes For ChatGPT Review

- Every finding in this scan is bounded public-source desk research classifying service *structure*, not a corpus-confirmed wage mechanism — do not cite any city's classification as "confirmed in current corpus."
- Do not treat Worcester's or Somerville's source-identification leads as authorized acquisition tasks; both are flagged as needing a separate, explicit go-ahead given their higher effort/lower-confidence profile relative to Seekonk's zero-cost re-read.
- Do not treat the Newton/Republic-Services private-hauler strike finding as evidence of a wage *mechanism* result — it is a design-fit observation (multi-city bargaining units do not fit this project's one-city-one-unit comparison logic), not a measured wage outcome.
- This project's corpus still holds zero `sanitation` rows; nothing in this session changed that.

---

## 2026-07-06T10:00:00-04:00 - Sanitation / solid waste wage mechanisms scoped

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior library-mechanism-and-corpus-scan session's changes (`6397378`, "Inspect library wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_sanitation_solid_waste_mechanism_scope_2026-07-05.md`
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 9, "Sanitation / solid waste mechanisms checklist," 9 rows; Sections 10-14 renumbered; XC09 extended by structural inference to a sixth non-safety group)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H32-H35)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was NOT edited** — zero `sanitation` rows exist, and no correction was identified in any `public_works`/`other` row's metadata.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. No new corpus row was added. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was a **scoping and source-planning session**, not a corpus-scan session — this project's corpus holds zero `sanitation` rows, a materially different starting point than teachers, DPW, clerical/admin, or library, all of which had at least some corpus text to work from.

### What This New Package Does

- Confirms zero `sanitation` rows exist in `data/contracts.csv`, and confirms — via direct field inspection plus cross-reference against the prior DPW full-corpus-scan session — that none of the seven already-collected `public_works` documents contains any sanitation-, refuse-, or recycling-specific title or duty language.
- **Sharpest quantified finding in this project to date:** national trade-press reporting citing BLS Census of Fatal Occupational Injuries data now places refuse/recycling collection's fatality rate (37.4-41.4 per 100,000 workers) above police's own, described directly as "considerably higher than in law enforcement." This sharpens, with hard numbers, the qualitative "sanitation hazard may exceed police's" claim already flagged in the original police/fire workforce-refinement memo.
- **Confirms real, complete (not merely supplemental) private-hauler contracting as a Massachusetts practice**, via four towns' own municipal web pages (Dedham, Andover, Marshfield, Brookline) — a materially different, more substitution-capable contractor profile than DPW's largely seasonal contractor use, and a plausible explanation for why this project's five DPW-collecting cities show no distinct sanitation title.
- **Confirms ~70% of Massachusetts communities have a consolidated DPW**, with solid waste frequently organized as a named division within it (not a free-standing department) — directly explaining sanitation's organizational "invisibility" inside this project's existing `public_works` corpus.
- **Extends the project's central institutional finding (no JLMC access) to sanitation by direct structural inference**, not independent re-verification — JLMC's eligibility rule (already verified four times: police/fire only, no essential-service exception for teachers, DPW, clerical/admin, or library) provides no basis to expect a sanitation-specific exception, and no source encountered this session suggests one.
- Treats contractor/private-hauler substitution as having **both** an upward-pressure reading (genuine private-sector wage competition) and a downward-pressure reading (wage-restraining substitution) explicitly, rather than assuming either direction — consistent with genuinely mixed academic privatization-cost research reviewed this session.
- Flags `sanitation_dirty_work_compensating_differential` explicitly as a hypothesis requiring evidence, not an assumed mechanism, mirroring the discipline already applied to gendered-occupational-valuation hypotheses elsewhere.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 9 ("Sanitation / solid waste mechanisms checklist," 9 rows: SN01-SN09, explicitly marked as scoping-stage since zero corpus rows exist), with Sections 10-14 renumbered from the prior 9-13; XC09 (arbitration/impasse backstop) extended to note sanitation's structurally-inferred (not independently re-verified) sixth-group status.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming sanitation's scoping completion and restating the recommended next step (source-acquisition planning, not a new mechanism-development group).
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H32-H35: `sanitation_route_coverage_pressure`, `sanitation_contractor_substitution`, `sanitation_mechanization_route_restructuring`, `sanitation_dpw_bundling`); the existing 31 rows were not touched.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Sanitation source-acquisition planning: confirm whether any of this project's current nine cities directly employs collection workers versus contracting the function entirely, and re-read the five already-collected `public_works` CBAs' job-description language (not just title language) for collection-duty content — no new ingestion required for the latter.
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Every sanitation finding in this session is either bounded external desk research or a structural extension of an already-verified fact — **none is corpus-confirmed**, since zero sanitation rows exist. Do not cite any sanitation mechanism as "confirmed in current corpus."
- Do not cite the sanitation fatal-injury-rate comparison to police as a causal or Massachusetts-specific claim — it is national data, cited via trade press, not this project's own corpus or a Massachusetts-specific source.
- Do not assume contractor/private-hauler substitution is wage-restraining by default — this session explicitly found the mechanism can run in either direction, and academic cost research does not settle which effect dominates.
- The central open question for any future sanitation work is whether this project's own nine cities employ sanitation workers directly at all, or contract the function out entirely — this determines whether a corpus-scan-style session (like library's) or a source-acquisition-first session (unlike any prior non-safety group) is the right next step.

---

## 2026-07-05T20:30:00-04:00 - Library wage mechanisms and corpus scan completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior Somerville-metadata-audit-and-checkpoint session's changes (`fe99104`, "Audit Somerville metadata and checkpoint wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_library_wage_mechanism_and_corpus_scan_2026-07-05.md`
  - `docs/analysis/non_safety_library_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 8 library table, 8 rows; Sections 9-13 renumbered; XC09 updated)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H28-H31)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was NOT edited** — all three `library` rows' existing metadata was directly verified against source documents and found already accurate.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was library's full deeper-inspection pass — the fourth non-safety comparison group, and the first one developed in a single combined session (mechanism refinement + institutional verification + corpus scan) rather than two separate memos, since it required no new source acquisition.

### What This New Package Does

- Reviews all three already-collected `library` corpus rows (Seekonk, Franklin, Wayland) in full, including an ad hoc, read-only OCR pass for Wayland's image-only scan.
- **Confirms library's part-time/page staffing model is structurally distinct from every other occupation class reviewed so far**: part-time employment is a permanent, core bargaining-unit category in all three documents (unlike teachers' separate substitute pool or DPW's seasonal-only part-time use), and pages are explicitly excluded from bargaining-unit coverage at Franklin — meaning this project's corpus has no wage data at all for the most page-like tier.
- **Directly contradicts, rather than confirms, the volunteer-substitution sub-hypothesis**: Franklin's Article 28 explicitly bars replacing bargaining-unit hours with volunteer labor without union agreement — the clearest on-point textual signal in this scan, running counter to a naive buffering story.
- **Confirms professional (MLS/MLIS) credentialing as a real but uneven, modest mechanism**: Franklin pays an explicit degree-tier stipend (up to $1,900/year for MLS/MLIS); Seekonk has no degree-linked pay at all; Wayland treats a Master's degree only as an education-leave benefit. This uneven pattern, even within this project's own three cities, is itself evidence against treating library credentialing as a guaranteed wage floor the way teacher licensure functions.
- **Confirms a fourth independent instance of the project's central institutional finding**: library employees follow the ordinary Chapter 150E Section 9 route with no JLMC access, per the MMA Select Board Handbook's own direct language ("it is common for clerical and library employees to be union members"). A library-specific budget-floor mechanism was also identified: the MBLC's Municipal Appropriation Requirement (municipal library appropriation generally may not fall below ~102.5% of the prior three years' average, subject to waiver) — a real but weaker/waivable analog to teachers' Chapter 70 floor.
- **Replicates, a fourth time, the peer-community-comparability absence** already documented for `public_works` and `clerical_admin` — no wage-comparator language was found in any of the three library documents.
- National context (ALA/PLA 2024 staff survey; BLS occupational wage data; a dated 2006 ALA-APA compression study, explicitly flagged as not current) is kept clearly separated from Massachusetts-specific and current-corpus evidence throughout.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 8 ("Library mechanisms checklist," 8 rows: LB01-LB08), with Sections 9-13 renumbered from the prior 8-12 accordingly; XC09 (arbitration/impasse backstop) updated to reflect a fourth independent non-safety confirmation.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming library's deeper-inspection completion and restating sanitation as the next-priority group.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H28-H31: `library_professional_credentialing`, `library_classification_reclassification`, `library_part_time_volunteer_buffering`, `library_service_deferral`); the existing 27 rows were not touched.

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
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo next (desk research only, since zero `sanitation` rows currently exist in this project's corpus).
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Library's volunteer-substitution sub-hypothesis is **contradicted**, not confirmed — do not cite "libraries use volunteers to buffer staffing costs" as a finding; Franklin's own contract explicitly prohibits it.
- Do not treat MLS/MLIS credentialing as a universal or guaranteed wage premium — it is confirmed present (as a stipend) at only one of this project's three library cities.
- Do not conflate the MBLC's Municipal Appropriation Requirement with Chapter 70's net-school-spending floor — the library mechanism is a weaker, waivable, rolling-local-baseline requirement, not a state-formula-driven legal mandate.
- Do not treat this memo's national ALA/PLA and BLS citations as Massachusetts-specific or as describing any of this project's three library cities directly — they are bounded national context only, per this project's standing discipline.

---

## 2026-07-05T19:00:00-04:00 - Somerville metadata audit closed and project mechanism checkpoint completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior authorized-cleanup session's changes (`47f8d25`, "Apply approved metadata cleanup") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/somerville_police_metadata_audit_2026-07-05.md`
  - `docs/analysis/somerville_police_metadata_audit_edits_2026-07-05.csv`
  - `docs/analysis/wage_mechanism_project_checkpoint_2026-07-05.md`
- Updated:
  - **`data/contracts.csv`** (2 rows, 1 field each: `binding_arbitration_statute`)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: two new notes; not rewritten)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block; not rewritten)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` was **not** updated — reviewed, no major missing/redundant hypothesis found.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This session had two parts: a narrow, fully-verified metadata correction (Somerville `binding_arbitration_statute`) and a broad strategic-synthesis checkpoint — neither is a data-build, GABRIEL, or ingestion session.

### What This New Package Does

**Part 1 — Somerville metadata audit, resolved with a direct edit:**
- Both `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012` had `binding_arbitration_statute` values (`ocr_messy`, `clean`) that were actually `text_quality` values — the same field-misplacement pattern already corrected for Boston's clerical/admin row, but never previously flagged for these two rows until discovered incidentally during the prior application session.
- Verified via direct `pdftotext` re-extraction of both source PDFs: both are genuine JLMC award-and-decision documents (dockets JLMC-17-6072 and JLMC-14-4174), and each row's own `total_comp_note` field already correctly states `"MA G.L. c. 1078 (JLMC)"` — a redundant, in-row confirmation that made this correction higher-confidence than the earlier Boston fix (which relied on an OCR/typo inference rather than a sibling field's direct statement).
- **Applied directly:** both rows' `binding_arbitration_statute` now reads `MA G.L. c. 1078 (JLMC)`, matching all 13 other police/fire rows' convention. A closing sweep (`binding_arbitration_statute` vs. the `text_quality` vocabulary, all 32 rows) found **zero** remaining instances of this pattern.

**Part 2 — project mechanism checkpoint, a synthesis-only stocktake:**
- Consolidated the full mechanism-development arc to date (original police/fire memos; teacher, DPW, and clerical/admin mechanism-refinement-plus-institutional-verification sequences; the national municipal workforce scan; the public-sector impasse/arbitration state-law citation audit) into one memo.
- Documents, per occupation group (police, fire, teachers, DPW, clerical/admin): main upward and restraint mechanisms, current corpus evidence, external/national evidence, Massachusetts-specific caveats, and unresolved gaps.
- Includes an 11-row evidence-strength table (peer wage comparability, arbitration/impasse backstop, overtime/staffing spiral, recruitment/retention, credential/licensing scarcity, classification/reclassification, service deferral/buffering, contractor substitution, public salience, budget capacity/fiscal constraint, source-document production effects) and a section on what the current CBA-heavy, discourse-empty corpus can and cannot show.
- **Key recommendation:** `library` is the highest-priority next non-safety group, since all three `library` corpus rows (Seekonk, Franklin, Wayland) already exist and are already coverage-matched to safety pairs — a full corpus-scan-plus-institutional-verification session can run with **no new source acquisition**. `sanitation` is next-priority for a mechanism-refinement/institutional-context memo (desk research only, since zero `sanitation` rows currently exist). Transit, nurse_health, custodial/facilities, and dispatchers each need a scoping/schema decision from the user/PI before further work (§11 of the checkpoint memo).
- **Notable new finding surfaced while assembling the checkpoint:** this project's own corpus already contains dispatchers ("Community Safety Dispatchers") embedded, unlabeled, inside a `public_works`-classified Arlington bargaining unit — a composition-fragmentation detail not previously flagged as its own issue.

### Checklist and Roadmap Updates

- `wage_mechanism_evidence_checklist.md` §11 gained two new notes: the Somerville resolution (with a pointer to the new audit memo/CSV) and a pointer to the checkpoint memo's next-priority recommendation. Not rewritten.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one new update block summarizing current deeper-inspection status (teachers/DPW/clerical-admin) and the checkpoint's ordered next-group recommendation. Not rewritten.

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
Both outputs are identical, in every count, to the pre-edit baseline.

### Recommended Next Step

1. Run a library corpus-scan-plus-institutional-verification session (mirroring the DPW/clerical/admin two-memo pattern) using the three already-collected `library` rows — no new ingestion needed.
2. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo next (desk research only).
3. Bring the checkpoint memo's three flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Both Somerville police rows' `binding_arbitration_statute` now correctly reads `MA G.L. c. 1078 (JLMC)` — do not cite the old `ocr_messy`/`clean` values, which were metadata artifacts, not evidence about anything substantive.
- The checkpoint memo (`wage_mechanism_project_checkpoint_2026-07-05.md`) is a synthesis of existing findings, not new research — cite the underlying occupation-specific memos for full citations and quoted contract text; the checkpoint is a fast-scan index and prioritization document.
- `library` is recommended as the next non-safety group specifically because it is already-collected, not because it is conceptually more important than sanitation or transit — do not read the priority order as a claim about which mechanism matters most.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is the library corpus scan.

---

## 2026-07-05T17:15:00-04:00 - Authorized production metadata cleanup applied

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior metadata cleanup audit session's changes (`2e0a808`, "Audit metadata cleanup candidates") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_application_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_applied_edits_2026-07-05.csv` (29 rows)
- Updated:
  - **`data/contracts.csv`** (9 rows, 22 field-level changes — the first production edit to this file since the metadata-cleanup arc began)
  - `docs/schema.md` (2 field-definition clarifications: `interest_arbitration_flag`, `comparability_clause_flag`)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: one new note, 3 short "RESOLVED" annotations; not rewritten)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no new rows were added; no `occupation_class` value was changed.
- `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was the authorized production-edit follow-up to the prior audit-only session — the first session in this cleanup arc to actually write to `data/contracts.csv`.

### What This New Package Does

- Applies the user's two explicit schema decisions: (1) `comparability_clause_flag` now means peer wage / peer-community / peer-employer wage comparability specifically — not health-insurance, workers'-comp, internal-classification, or discipline/fact-pattern "comparable" language; (2) `retrieval_method=public_download` describes this project's own access method (not a document's original legal provenance), so MuckRock-hosted-but-openly-downloaded Somerville rows correctly remain `public_download`.
- **Corrects 5 non-wage `comparability_clause_flag` false positives:** Arlington `public_works` x2, Seekonk fire, Wayland fire, Wayland other — flag flipped `1`→`0`, with the non-wage finding preserved in `comparability_referent` (a schema-existing field) rather than discarded.
- **Re-extracts the corpus's first two true-positive peer-wage-comparability rows:** both Somerville police JLMC-award rows had the genuine "wages and benefits of comparable towns" statutory-criteria text sitting in their own `arbitration_clause_text` field, uncaptured by `comparability_text`. This session extracted the exact verbatim span (same wording, same line breaks) into `comparability_text`, with `comparability_referent` naming the referent.
- **Corrects 4 `interest_arbitration_flag` false positives** (Boston clerical/admin, Arlington `public_works` x2, Seekonk `public_works`) — all four had clause text describing grievance or civil-service disciplinary arbitration, not wage-setting interest arbitration.
- **Corrects Boston clerical/admin's 3-field misalignment:** `longevity_detail` (held a general unit-description note) and `total_comp_note` (held a bare, misleading JLMC citation) were swapped; `binding_arbitration_statute` (held `"clean"`, a `text_quality` value) was corrected to `"MA G.L. c. 150E"` — but only after this session directly re-extracted `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` and independently confirmed the citation at 3 locations in the source text (lines 95, 485, 1047 of the extracted text), resolving the prior audit's "medium-high confidence, pending PDF re-verification" flag.
- **Records both schema decisions in `docs/schema.md`** so future ingestion does not repeat the same miscoding.
- **New finding, explicitly not corrected:** while verifying the Boston edit, this session discovered both Somerville police rows' `binding_arbitration_statute` fields also hold `text_quality` values (`ocr_messy`, `clean`) instead of a statute name — the same pattern as Boston's, but never previously audited or approved. Left untouched, per this session's boundary against unapproved edits, and flagged for a future audit-and-approval cycle rather than fixed opportunistically.

### Checklist Update

- `wage_mechanism_evidence_checklist.md` §11 gained one new top-of-section note (production cleanup applied, both schema decisions stated, pointer to the new memo/CSV, the new unresolved finding flagged) plus short "RESOLVED 2026-07-05" annotations appended to items 1, 2, and 6 (not rewritten). Items 3, 4, 5, and 7 remain as historical record (no edit was needed for those).

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
Both outputs are identical, in every count, to the pre-edit baseline — expected, since no applied edit touches `occupation_class`, cycle dates, or `obs_id`.

### Recommended Next Step

1. Review the `data/contracts.csv` diff directly (this session verified it programmatically — before/after row count 32, column count 34, and exactly the 9 intended obs_ids and their intended fields changed, nothing else) before treating the cleanup as final.
2. Decide whether to authorize a short follow-up audit-and-approval cycle for the newly-discovered Somerville `binding_arbitration_statute` anomaly — do not correct it without going through the same audit-then-approve process, even though the likely correct value (`"MA G.L. c. 1078 (JLMC)"`) is fairly obvious from cross-corpus pattern matching.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is reviewing this cleanup's diff and deciding on the Somerville follow-up.

### Notes For ChatGPT Review

- `data/contracts.csv` now has real, applied edits — this is the first entry in this handoff log where that file's diff is nonzero. Prior "no production edits" language in earlier entries applied to those specific sessions only.
- Do not cite `ma_boston_clerical_admin_2023`'s `binding_arbitration_statute` as `"clean"` or its `total_comp_note` as a bare JLMC citation any longer — both are corrected as of this session.
- Do not treat `ma_somerville_police_spsoa_2012`/`_spea_2012`'s `binding_arbitration_statute` fields (`"ocr_messy"`/`"clean"`) as reliable — this is a newly-discovered, not-yet-corrected anomaly; do not silently "fix" it without a dedicated audit-and-approval step first.
- `comparability_clause_flag=1` now reliably means peer-wage comparability across the whole corpus (2 true positives: the two Somerville police rows); `comparability_clause_flag=0` rows that previously had non-wage "comparable" text still retain that text's nature documented in `comparability_referent`.

---

## 2026-07-05T15:30:00-04:00 - Metadata cleanup audit completed (audit-first; no production edits)

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior citation-audit session's changes (`b18d6bd`, "Audit public sector impasse arbitration sources") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_audit_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows)
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (one concise status note at the top of §11 only)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; **no production metadata edits were made to `data/contracts.csv` or any other production file.**
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded, audit-first metadata-cleanup review — the task queued at the end of every session since the national scan — not a data-build, GABRIEL, or ingestion session.

### What This New Package Does

- Verifies, row by row against `data/contracts.csv` (via direct `csv.DictReader` inspection, not memo paraphrase) and against underlying corpus PDFs where useful, the 7 metadata issues already tracked in `wage_mechanism_evidence_checklist.md` §11, plus 3 newly-scoped issues (a corpus-wide `comparability_clause_flag` audit, an `occupation_class`/unit-title spot check, and a light provenance-field consistency check).
- **Most consequential finding — `comparability_clause_flag` is unreliable corpus-wide, not just at Arlington.** All 7 currently-flagged rows capture non-wage "comparable" language (drug-testing standard, workers'-comp medical-provider continuation, health-insurance plan-contribution parity, work-group-realignment eligibility). For the two Somerville JLMC-award rows specifically, the genuine peer-wage-comparability text — the award's own "wages and benefits of comparable towns" statutory-criteria language — is demonstrably already present in the dataset, just in the wrong field (`arbitration_clause_text` instead of `comparability_text`). This means those two rows can be corrected by re-extraction alone, with no new source acquisition.
- **Boston `clerical_admin` row (`ma_boston_clerical_admin_2023`) — sharper than previously documented.** This is a three-field misplacement, not a single stray citation: `total_comp_note` holds a bare `"MA G.L. c. 1078 (JLMC)"` citation; `longevity_detail` holds general unit-description text that belongs in `total_comp_note`; and `binding_arbitration_statute` holds `"clean"` — a `text_quality`-vocabulary value that does not belong in that field at all (this specific sub-finding is new to this audit). The row's own `interest_arbitration_flag=1` also appears miscoded: the captured `arbitration_clause_text` is pure grievance-procedure definitional language with no interest-arbitration content, consistent with clerical/admin's externally-confirmed JLMC ineligibility.
- **`interest_arbitration_flag` scope confirmed and enumerated.** 4 of the 6 rows flagged `interest_arbitration_flag=1` (Boston clerical/admin; both Arlington `public_works` cycles; Seekonk `public_works`, whose own clause states verbatim "Final binding arbitration will prevail on grievances only") contain grievance/discipline arbitration text, not wage-setting interest arbitration. Only the two Somerville police rows genuinely contain interest-arbitration text.
- **3 of the 7 originally-tracked issues require no further action**, with concrete confirmation: Seekonk clerical/admin's school-committee affiliation, `public_works`' cross-municipality bundling variation, and Worcester's successor-MOA/incorporation-by-reference limitation are all already stated plainly in the affected rows' own `total_comp_note` fields.
- **Teacher-aide/paraprofessional merge risk not realized.** Direct `pdftotext` extraction of the sole current `teacher` row (Seekonk Educators Association) confirms the contract itself places teacher aides outside the bargaining unit, under School Committee determination — no wage or step-schedule content for aides exists inside this teacher-classified row.
- Produced `metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows): 16 marked `production_edit_needed=yes` (4 boolean/flag corrections, 3 value corrections/swaps on the Boston row, 4 re-extractions on the Somerville rows, 5 notes-only `comparability_referent` clarifications), 3 marked `needs_followup` (schema-scope decisions that should precede any row edit), and 1 a `docs/schema.md` definition-clarification suggestion (not a data edit).

### Living Checklist Update

- `wage_mechanism_evidence_checklist.md` §11 gained one concise status note at the top (audit completed, proposed edits in the new CSV, no production edits made, next step is approval). The 7 existing tracked-issue entries were not rewritten; this audit's findings live in the new dated memo and CSV, cross-referenced from the checklist.

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

1. Review `metadata_cleanup_proposed_edits_2026-07-05.csv` and resolve the 3 `needs_followup` schema-scope decisions (comparability-flag wage-specificity; FOIA-vs-public_download retrieval-method convention; the third `needs_followup` row is the comparability-flag decision applied to the Arlington rows specifically), then authorize a narrowly-scoped production-edit session limited to exactly the 16 flagged rows/fields.
2. That future production-edit session should re-verify the Boston `binding_arbitration_statute` proposed value ("MA G.L. c. 150E") directly against `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` before writing it — the audit's supporting evidence (an in-row OCR/typo clue plus cross-corpus pattern-matching) is medium-high, not full, confidence.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is resolving the metadata-cleanup follow-ups above.

### Notes For ChatGPT Review

- Do not treat `data/contracts.csv`'s `comparability_clause_flag`/`comparability_text` fields as reliable signals of peer-jurisdiction wage comparability as currently populated — this audit found 0 true positives among the 7 currently-flagged rows, and 2 false negatives (the Somerville rows, where the correct text exists but in the wrong field).
- Do not cite `ma_boston_clerical_admin_2023`'s `binding_arbitration_statute` field (currently `"clean"`) or `total_comp_note` field (currently a bare JLMC citation) at face value; both are confirmed data-quality anomalies pending approval of the proposed corrections in the new CSV.
- Do not treat `interest_arbitration_flag=1` as proof of wage-setting interest arbitration without reading `arbitration_clause_text` directly — 4 of 6 currently-flagged rows are grievance/discipline arbitration.
- No production metadata edits have been made as of this entry; all corrections above are proposals pending approval.

---

## 2026-07-05T13:56:32-04:00 - Public-sector impasse/arbitration state-law citation audit completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior national-scan session's changes (`41d10b1`, "Add national municipal workforce mechanism scan") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/public_sector_impasse_arbitration_state_law_citation_audit_2026-07-05.md`
  - `docs/analysis/public_sector_impasse_arbitration_state_law_table_2026-07-05.csv`
- Updated:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md` (small targeted patches only — see below)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (concise additions to XC09, XC10 only)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H7, H17 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded citation-audit and state-law source-verification session, not a data-build or GABRIEL session.

### What This New Package Does

- Audits the national scan's public-sector impasse/arbitration claims against primary legal sources for 12 required states (MA, NJ, NY, MI, RI, PA, WY, OK, IA, NC, SC, VA) plus two contrast states (WI, IL), with every claim labeled by source type (primary statute/agency vs. secondary summary) and confidence level.
- **Confirmed with primary-source citations:** compulsory or state-invocable binding police/fire interest arbitration in NJ (N.J.S.A. 34:13A-14 to -21), NY (Civil Service Law §209.4), MI (Act 312 of 1969), RI (Gen. Laws Ch. 28-9.1/28-9.2/28-9.5), PA (Act 111 of 1968), OK (Title 11 §51-101), and IL (5 ILCS 315/14); North Carolina's total public-sector bargaining prohibition (G.S. 95-98, 1959); Virginia's 2020/2021 local-option reform (Va. Code §40.1-57.2).
- **Corrected:** Wyoming's statute (W.S. §§27-10-101 to -109) is confirmed **fire-only** — no comparable Wyoming police statute was found, correcting the national scan's more general phrasing.
- **Most consequential finding — Iowa:** Iowa Code §20.22 is confirmed via primary source as a **general, all-covered-public-employee** binding, final-offer-selection arbitration statute in place since the 1970s — not teacher-specific, as the prior session's framing implied. Iowa's 2017 reform (House File 291) did not remove this for non-safety units (including teachers); it instead narrowed their bargaining scope (mostly base wages) and arbitration criteria (removing ability-to-pay and past-contract consideration, adding a mandatory public/private wage comparison) for any unit under 30% Iowa-defined "public safety employees." Iowa is now both a confirmed counterexample to "non-safety never gets compulsory arbitration" *and* an example of a state building its own safety-favoring asymmetry through a different lever (scope/criteria, not availability) than anything in this project's Massachusetts corpus.
- **Flagged as weakest-sourced:** South Carolina's bargaining prohibition is affirmed by consistent secondary-source consensus (Ballotpedia, CEPR, multi-state legal trackers) but could not be traced to a single primary statute as clean as North Carolina's within this session's bounded search — explicitly not cited with the same confidence.
- **Flagged as legally unsettled:** Wisconsin's 2011 Act 10 exempted police/fire/state troopers from general public-employee bargaining restrictions, but a December 2024 Dane County ruling struck down that exemption as an equal-protection violation under the Wisconsin Constitution — sourced only from secondary/journalistic reporting, status unsettled, likely under appeal. This is directly relevant to this project's "public-safety institutional privilege" framing: it shows the safety/non-safety distinction is not treated as self-evidently constitutional everywhere it appears.
- A source-reliability discrepancy flagged in the prior national-scan session (a secondary source's inconsistent characterization of Massachusetts's own teacher-strike rules) was not the focus of new research this session but remains flagged in the scan memo, unresolved by further primary-source work this session.

### National Scan Patches (Task C — small corrections only, not a rewrite)

- Wyoming corrected to fire-only with the primary citation (W.S. §§27-10-101 to -109) added, in both the police section (§4) and fire section (§5).
- Iowa's description sharpened in §6 and in the claim table (§11) to state it is a general public-employee mechanism with its own 2017 safety-favoring asymmetry, not a simple teacher-specific exception.
- Citation-audit pointers added to the JLMC-pattern table row (§9) and the NC/SC/VA bargaining-rights paragraph (§7), distinguishing primary-confirmed (NC, VA) from secondary-only (SC) claims.

### Living Checklist and Hypothesis Matrix Changes

- `wage_mechanism_evidence_checklist.md`: concise additions to XC09 (arbitration/impasse backstop — full citation list and Iowa nuance) and XC10 (public salience — Wisconsin equal-protection finding). No heavy rewrite.
- Hypothesis matrix: small edits to H6 (arbitration_or_impasse_backstop — full citation list, WY/IA corrections), H7 (political_support_or_public_salience — Wisconsin finding), and H17 (non_safety_wage_restraint — Iowa's scope/criteria-restriction lever). No new rows.

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

1. Conduct the metadata-cleanup audit of the 7 issues tracked in the living checklist's Section 11 — audit-first, confirming each issue against its underlying source document before any direct edit to `data/contracts.csv`. This citation audit was a parallel task and does not change that sequencing.
2. If future capacity allows, close the follow-up items this audit flagged: South Carolina's primary statute, Wyoming's police-specific equivalent (if any), Rhode Island's possible teacher-specific chapter, Pennsylvania's non-safety strike-right claim, and Wisconsin's primary Act 10 text/court opinion.
3. Continue updating the living checklist in place after future work.

### Notes For ChatGPT Review

- Do not cite Wyoming as covering police arbitration; the confirmed statute is fire-only.
- Do not describe Iowa's arbitration mechanism as teacher-specific; it is a general public-employee statute, and Iowa's own 2017 reform actually adds a safety-favoring wrinkle within it.
- Do not cite South Carolina's bargaining prohibition with the same confidence as North Carolina's; SC lacks an equally clean primary citation in this project's research to date.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the metadata-cleanup audit.

---

## 2026-07-05T12:52:27-04:00 - National municipal workforce mechanism scan completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior living-checklist session's changes (`7557e59`, "Create wage mechanism evidence checklist") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (in-place edits to 11 mechanism rows: PD01, PD12, FD03, FD12, TC10, TC12, DP12, CA01, CA03, CA13, XC09)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H1, H6, H9, H11 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded national qualitative scan, conducted via public-source desk research, not a data-build or GABRIEL session.

### What This New Package Does

- `national_municipal_workforce_mechanism_scan_2026-07-05.md` scans national context across police, fire, teachers, DPW/public works, and clerical/admin, with the specific purpose of distinguishing general U.S. municipal mechanisms from Massachusetts-specific institutions this project's prior sessions verified.
- **Most consequential finding:** compulsory police/fire interest arbitration — the policy pattern underlying Massachusetts's JLMC — recurs in at least New Jersey, New York, Michigan, Rhode Island, Pennsylvania, Wyoming, and Oklahoma. The *pattern* (a no-strike-for-compulsory-arbitration trade specific to police/fire) generalizes; the *specific vehicle* (JLMC) is Massachusetts's own implementation, not a national template.
- **School finance:** the general foundation-formula architecture behind Chapter 70 (a state spending floor filled by state aid after a local-capacity-based required contribution) is confirmed as the dominant national school-finance model (Urban Institute), with structurally comparable formulas confirmed in New Jersey and Wisconsin. Chapter 70's specific 82.5% cap and net-school-spending definition remain Massachusetts-specific parameters.
- **Fire:** NFPA data quantifies the national volunteer-firefighter decline directly (897,750 in 1984 to 676,900 in 2020, a 25% decline against ~40% U.S. population growth), with IAFF documenting communities converting to all-career departments as the adaptation — now a quantified national trend, not only a qualitative framing.
- **Police:** MissionSquare/SLGE's 2024 survey confirms real national police staffing difficulty (68% hard-to-fill) but shows it is not the single hardest local-government occupation — mental health (83%), nursing (77%), and corrections (74%) all rank higher in the same survey.
- **Clerical/admin:** formal civil-service classification-and-reclassification-appeal architecture (the basis of Boston's mechanism) is confirmed as a national norm (NY, NJ, federal OPM, Massachusetts's own state Civil Service Commission all share it) — Boston's specific narrow "arbitrary or capricious" arbitration standard remains an untested-elsewhere local parameter within that general architecture.
- **Important counterexamples/caveats surfaced, not smoothed over:** at least Iowa is documented to extend compulsory, state-labor-board-ordered arbitration to teachers, unlike Massachusetts's voluntary-only route; and the entire "non-safety lacks JLMC access" finding for DPW and clerical/admin presumes public-sector bargaining rights exist at all, which is false in North Carolina and South Carolina and was false in Virginia before a 2020 local-option reform. A secondary source's inconsistent characterization of Massachusetts's own teacher-strike rules was flagged explicitly rather than silently resolved, with this project's own primary-source (Mass.gov DLR) verification treated as authoritative for Massachusetts.
- Grounded the gendered-occupational-valuation hypothesis further in credible academic literature (Paula England's research; IWPR occupational-segregation research; a CRS report noting comparable-worth policy has "made the most headway in state and local governments") while explicitly declining to upgrade its status for this project's own specific findings, per the task's explicit instruction to keep it a hypothesis requiring evidence.

### Living Checklist Update

- `wage_mechanism_evidence_checklist.md` updated in place across 11 mechanism rows (PD01, PD12, FD03, FD12, TC10, TC12, DP12, CA01, CA03, CA13, XC09), adding national-scan findings without overwriting the existing table structure. Verified every edited row retains exactly 13 pipe delimiters (12 columns). `confirmed in external sources` was added only where the scan found credible support; uncertain claims (e.g., the project-specific gendered-occupational-valuation claim) were explicitly kept at their prior, more cautious status.

### Hypothesis Matrix Changes

- H1 (`recruitment_retention_pressure`): added the MissionSquare/SLGE calibration finding (police staffing pressure real but not uniquely severe among local-government occupations).
- H6 (`arbitration_or_impasse_backstop`): added the multi-state compulsory-arbitration pattern and the Iowa/NC/SC/VA counterexamples.
- H9 (`fiscal_capacity_ability_to_pay`): added the national foundation-formula generalization finding.
- H11 (`public_safety_service_necessity`): added the NFPA quantified volunteer-decline figures.
- No new rows added, since no wholly new national mechanism family was identified — every finding sharpened or qualified an existing hypothesis. Verified 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Roadmap Update

- `non_safety_comparison_roadmap_2026-07-04.md` gained one closing note confirming the national scan is complete and the next planned step is the metadata-cleanup audit, restating that national-general and Massachusetts-specific evidence should stay explicitly distinguished in future work.

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

1. Conduct the metadata-cleanup audit of the 7 issues tracked in the living checklist's Section 11 — audit-first, confirming each issue against its underlying source document before any direct edit to `data/contracts.csv`.
2. Continue updating the living checklist in place after any future corpus scans, OEWS/DESE/BLS descriptive baseline, or GABRIEL extraction run.
3. Keep national-general and Massachusetts-specific evidence explicitly distinguished in any future PI-facing synthesis.

### Notes For ChatGPT Review

- Do not treat JLMC, Chapter 70, or Proposition 2½ as national institutions; they are Massachusetts's specific implementations of more general, but not universal, national patterns (compulsory police/fire arbitration; foundation-formula school finance; local property-tax levy limits).
- Do not treat the "non-safety lacks compulsory arbitration" finding as universal; Iowa is a documented counterexample for teachers, and the finding presumes bargaining rights exist at all, which is false in NC, SC, and pre-2020 VA.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the metadata-cleanup audit.

---

## 2026-07-05T12:32:37-04:00 - Living wage-mechanism evidence checklist created

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior clerical/admin corpus-scan and Massachusetts clerical/admin impasse-context session's changes (`41be1b3`, "Scan clerical admin corpus and clarify impasse context") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (undated, living reference file — do not fork a dated copy; update in place)
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No national web scan or five-city web pilot was run; no new broad web research was conducted (this was a synthesis session over existing memos, not a research session).
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a synthesis and repo-organization session, consolidating existing findings into one canonical reference rather than producing new mechanism research.

### What This New Package Does

- `wage_mechanism_evidence_checklist.md` consolidates every wage-mechanism hypothesis developed across all prior sessions — the 27-row hypothesis matrix plus additional cross-cutting mechanisms and source-family entries not previously tabulated together — into one working checklist covering police, fire, teachers, DPW/public works, clerical/admin, and cross-cutting categories.
- Defines and uses a fixed status vocabulary (`not searched`, `partially searched`, `confirmed in current corpus`, `confirmed in external sources`, `weak evidence`, `not found in current corpus`, `contradicted`, `needs metadata cleanup`, `not applicable`) and a 12-column table structure (mechanism_id, mechanism, occupation_group, wage_pressure_direction, plausible_channel, evidence_that_would_support, evidence_that_would_weaken_or_contradict, best_source/document_types, current_repo_evidence, verification_status, next_action, notes) applied consistently across ~80 mechanism rows.
- Includes a source/document-type inventory (17 families, from CBAs and arbitration awards through national association reports), a current-corpus-evidence summary contrasting the DPW/clerical-admin corpus-rich picture against the teacher external-sources-rich picture, a tracked (not corrected) list of 7 known metadata-cleanup issues, and an update protocol instructing future sessions to update rows in place rather than fork new dated files.
- Explicitly frames every substantive claim as a pointer back to the underlying occupation-specific memo, so the checklist stays a fast-scan working reference rather than a competing source of truth.
- Highlights, by putting all five occupation groups side by side for the first time, that the arbitration/impasse-backstop finding (JLMC compulsory interest arbitration confirmed unique to police/fire, with teachers, DPW, and clerical/admin all independently verified to share the same Chapter 150E Section 9 route) is now the single most thoroughly cross-verified finding in the project.

### Roadmap Update

- `non_safety_comparison_roadmap_2026-07-04.md` gained one closing note pointing to the new checklist, restating that the next planned step is the national qualitative scan across police, fire, teachers, DPW/public works, and clerical/admin, and that metadata cleanup should follow the national scan and be audit-first, not direct-edit-first.

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

1. Run the national qualitative scan across police, fire, teachers, DPW/public works, and clerical/admin.
2. After the national scan, conduct a metadata-cleanup audit of the issues tracked in the new checklist's Section 11 — audit-first, not direct-edit-first.
3. Update the checklist in place after the national scan, the metadata-cleanup audit, any future corpus scans, and any future OEWS/DESE/BLS descriptive baseline or GABRIEL extraction run.

### Notes For ChatGPT Review

- Do not treat `wage_mechanism_evidence_checklist.md` as a replacement for the occupation-specific memos it summarizes; it is a fast-scan index, and full citations/quoted contract text live in the memos it points to.
- Do not add a dated filename fork of the checklist in a future session; update the existing file in place per its own update protocol (Section 12).
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the national qualitative scan, followed by a metadata-cleanup audit.

---

## 2026-07-05T12:01:59-04:00 - Clerical/admin existing-corpus scan and Massachusetts impasse context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior clerical/admin mechanism session's changes (`75b8c22`, "Refine clerical admin wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md`
  - `docs/analysis/ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md` (light edit: closed gaps 3 (partial), 4, 13, 15)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: second clerical/admin update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H23, H24 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional-verification and internal-corpus-review session, not a data-build or GABRIEL session.

### What This New Package Does

- **Existing corpus review:** identified all three `clerical_admin` occupation-class rows in `data/contracts.csv` (Worcester, Boston, Seekonk), confirmed all three corpus files exist, and read their actual text in full (native extraction for Worcester and Boston; a prior session's ad hoc, read-only OCR pass reused for Seekonk's image-only file). Findings: Boston's contract contains the most procedurally restrictive reclassification mechanism found anywhere in this project's corpus to date — a Compensation Grade Appeals process whose arbitration is explicitly limited to an "arbitrary or capricious" standard (not a full merits review), with an explicit, twice-stated contractual exclusion of workload/technology-driven duty changes as valid reclassification grounds; a CDL stipend embedded in a nominally clerical/admin unit; and a documented departmental-merger history (BCYF, Public Facilities/DND, Environment Department, Office of Historic Preservation) revealing the unit spans far more than clerical titles (Grants Manager, Network Administrator, Facilities Manager, Aquatics Manager, and others). Worcester's document remains a short successor MOA with no classification/reclassification content. Seekonk's is a school-based Administrative Secretaries unit with a simple longevity schedule and no reclassification apparatus. No peer-community wage-comparability, pay-compression, or workload/backlog language was found in any of the three documents.
- **Massachusetts clerical/admin impasse verification:** confirms, via the Massachusetts Municipal Association's Select Board Handbook, that "clerical and administrative employees do not qualify for JLMC services" — the most direct confirmation found yet for any of the three non-safety groups (naming the occupation class explicitly rather than requiring inference from a general non-police/fire rule). So clerical/admin bargaining follows the same general Chapter 150E Section 9 route already confirmed for teachers and DPW. A new institutional wrinkle: some administrative positions closest to municipal executive leadership are "confidential employees" excluded from collective bargaining entirely, meaning their pay is set unilaterally, not through any bargaining/impasse process at all.
- Flags and precisely corrects a `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row: a stray "MA G.L. c. 1078 (JLMC)" citation sits in the wrong field (`total_comp_note` instead of `binding_arbitration_statute`), which could be misread as evidence of JLMC coverage. Verified directly against the actual contract text that no JLMC reference exists in the document. Not corrected in `data/contracts.csv`, per this session's review-only scope; flagged for a future data-quality pass.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): one small, targeted addition adding the verified MA clerical/admin institutional corroboration (the explicit MMA Select Board Handbook naming, the narrower CGA arbitration standard, and the confidential-employee exclusion wrinkle) alongside the teacher- and DPW-specific verifications already present.
- H23 (`clerical_admin_classification_restraint`) and H24 (`clerical_admin_reclassification_pressure`): both sharpened with the full corpus-scan findings (the exclusive, narrow-remedy CGA procedure; the explicit workload/technology exclusion language).
- No new rows added; verified 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_clerical_admin_source_gaps_2026-07-05.md`: gaps 3 (reclassification requests, partially closed — process documented, outcome data remains hard), 4 (pay-grade/step structures), 13 (peer-community comparisons), and 15 (MA clerical/admin impasse-process verification) marked CLOSED with pointers to the new memos.
- `non_safety_comparison_roadmap_2026-07-04.md`: a second clerical/admin update note added confirming both open items from the prior session (institutional verification; corpus review) are now resolved, and that all three non-safety comparison groups have completed both stages.

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

1. Move to the national qualitative scan across police, fire, teachers, DPW, and clerical/admin per the existing roadmap, since both clerical/admin uncertainties from the prior session are now resolved.
2. If a clerical/admin-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in the new corpus-scan memo, and treat pay-compression, workload/backlog, and recruitment/retention framing as new-source-acquisition gaps, not further-review gaps.
3. Flag the `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row for a future data-quality pass; do not correct it outside a review-only session's scope.

### Notes For ChatGPT Review

- Do not restate the task brief's reference to "H10 arbitration_or_impasse_backstop" — in the current matrix, `arbitration_or_impasse_backstop` is H6; H10 is `credentialing_training_burden`. Both the corpus-scan and impasse memos note the correct current identifier.
- Do not read the stray "MA G.L. c. 1078 (JLMC)" text in Boston's `total_comp_note` field as evidence of JLMC coverage for that unit — it is a field-alignment artifact, and the actual contract text contains no JLMC reference.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is the national qualitative scan across all five occupation groups.

---

## 2026-07-05T11:17:24-04:00 - Clerical/admin wage mechanism refinement developed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior DPW corpus-scan and Massachusetts DPW impasse-context session's changes (`d1b4969`, "Scan DPW corpus and clarify impasse context") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_wage_mechanism_refinement_2026-07-05.md`
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: clerical/admin findings update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H23-H27; small extension to H17)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only light review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded context-building/hypothesis-refinement session focused on clerical/administrative municipal workers as the third non-safety comparison group, not a data-build or GABRIEL session.

### What This New Package Does

- Develops clerical/admin as the "plainest" non-safety comparison group: unlike teachers (credentialing/salience) and DPW (operational/licensing), clerical/admin generally lacks both kinds of ready-made justification, which isolates what pure wage-setting institutions can restrain on their own.
- Maps clerical/admin into distinct sub-titles (clerk/senior clerk/principal clerk, administrative/executive assistant, office manager, payroll/accounting staff, assessor/collector/treasurer staff, town/city clerk staff, school administrative assistants, department-nested clerical roles, supervisors) rather than treating it as one homogeneous occupation.
- Surfaces a concrete, corpus-grounded reclassification mechanism: Boston's clerical/admin CBA documents a formal "OHR Classification and Compensation Unit" review process for reclassification applications, with management rights explicitly reserved over reorganize/reclassify decisions — the basis for two new hypotheses distinguishing classification-system restraint from reclassification-as-the-visible-channel.
- Identifies that this project's Seekonk `clerical_admin` row (Administrative Secretaries) is a school-based unit, not a general municipal office unit, directly illustrating the composition caution already applied to teachers and DPW.
- Grounds the pay-compression mechanism in a directly quantified, multi-state estimate: The Century Foundation's analysis of the cost of raising local-government workers above a $15 minimum wage threshold across six jurisdictions **including Massachusetts**, ranging 0.2% (DC) to 1.0% (Illinois) of payroll per year, weighted average ~0.6%.
- Confirms a real Massachusetts shared-services mechanism via Mass.gov's Efficiency and Regionalization grant program, with concrete examples (shared Regional Sustainability Coordinator across Westford/Carlisle; shared Town Administrator across Berkshire Regional Planning Council/Savoy).
- Explicitly flags gendered occupational valuation ("comparable worth") as a hypothesis requiring dedicated evidence, not an established fact about this project's cities, per the task's explicit instruction to handle this carefully.
- Explicitly separates Massachusetts-specific findings (the three corpus examples, the Massachusetts-inclusive minimum-wage-compression estimate, the Massachusetts shared-services grant program) from purely national background (MissionSquare recruitment/retention reporting, general automation-vendor material) throughout.

### Hypothesis Matrix Changes

- Added H23 `clerical_admin_classification_restraint`, H24 `clerical_admin_reclassification_pressure`, H25 `clerical_admin_pay_compression`, H26 `clerical_admin_service_backlog_absorption`, H27 `clerical_admin_lower_public_salience` as new rows, all with police/fire relevance marked low, consistent with the existing schema (12 columns unchanged). Unlike the DPW session (where the analogous public-salience hypothesis was folded into H7), this session added `clerical_admin_lower_public_salience` as its own row, per this session's task brief explicitly listing it among the 5 recommended additions.
- Lightly extended H17 (`non_safety_wage_restraint`) counterpoint field to note the clerical/admin extension as the "plainest" test case.
- Verified: 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- 15 clerical/admin source gaps identified in `non_safety_clerical_admin_source_gaps_2026-07-05.md`, several partially closed this session via bounded web search and light corpus read (national recruitment/retention context, the Massachusetts-inclusive minimum-wage-compression estimate, Massachusetts shared-services examples, the Boston reclassification-process example) and others flagged as open (full corpus review of all three `clerical_admin` rows, Massachusetts-specific vacancy/turnover/backlog data, clerical/admin-specific impasse-process verification, and gendered-occupational-valuation evidence).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a concise clerical/admin findings update note under the existing Section 3, including the recommendation that a national qualitative scan across police, fire, teachers, DPW, and clerical/admin is the natural next major step now that all three non-safety comparison groups have an initial mechanism map.

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

1. Verify whether Massachusetts clerical/admin bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers and DPW.
2. Conduct a full document-by-document review of this project's three already-collected `clerical_admin` corpus rows, mirroring the dedicated DPW corpus-scan session.
3. Move to a national qualitative scan across police, fire, teachers, DPW, and clerical/admin, now that all three non-safety comparison groups have an initial mechanism map in place.

### Notes For ChatGPT Review

- Do not treat the gendered-occupational-valuation discussion as an established finding; it is explicitly flagged as a hypothesis requiring dedicated evidence not yet gathered.
- Do not treat this session's light, illustrative corpus read (three cities) as equivalent in depth to the dedicated DPW corpus-scan session; a fuller review remains a recommended next step.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is clerical/admin impasse verification, a fuller corpus review, and then the national qualitative scan.

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
