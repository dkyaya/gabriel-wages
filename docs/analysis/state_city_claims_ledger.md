# State/City Claims Ledger

**Canonical path:** `docs/analysis/state_city_claims_ledger.md` — this filename is permanent and does not change between sessions. **Do not fork a new dated copy of this file.** If you are about to write `state_city_claims_ledger_<date>.md`, stop — edit this file in place instead. (The file was originally created as `state_city_claims_ledger_2026-07-14.md` on 2026-07-14 and renamed to this permanent path the same week; the changelog at the bottom preserves that history.)

**Type:** living, persisted analytical working document. Not a report. Extend this file in place in future sessions rather than recreating it — update a city's entry when new sources are ingested, codified, or a claim's status changes; add new state sections as new states clear the matched-design bar. Add a dated changelog line at the bottom for every session that touches this file; that is how staleness is tracked, not the filename.

**Purpose:** a durable bridge between the corpus's raw source inventory and future claim-centered reporting. `docs/analysis/state_city_claim_map_2026-07-12.csv` is the machine-readable index this file is built from; `docs/analysis/claim_register_2026-07-12.csv` is the authoritative claim text, evidence strength, and report-readiness for every `CLM-2026-07-12-XX` ID cited below. This file exists so a future session can read "what does the corpus currently let us say about city X" in prose, without re-deriving it from the CSVs or from a chat history it wasn't part of.

**Last updated:** 2026-07-14 (initial build) — see the changelog at the bottom for the full revision history and what changed in each pass. `data/contracts.csv` had 64 rows across 19 cities in 5 states (MA, OH, TX codified; PA, NJ source-availability/partially-ingested) as of the initial build. 16 cities were ingested and codified (real GABRIEL evidence-layer rows exist). 2 MA cities (Worcester, Arlington) were ingested but not yet codified. Philadelphia PA and 3 NJ cities (Newark, Trenton, and — candidate-only — Jersey City) had real ingested `data/contracts.csv` rows but **zero codified evidence** — every PA/NJ claim below is a source-availability/design-level hypothesis, not coded evidence, and is labeled as such throughout. Do not cite any PA/NJ finding in this file as codified evidence in a future report unless a later changelog entry confirms a codify wave ran.

**How to read the `Claims` sections below:** every claim is scoped to what the cited sources actually show, follows the claim-centered discipline in `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md`, and cites a `CLM-2026-07-12-XX` ID where one exists. A claim with no CLM ID is a hypothesis this file is proposing pending codify, not an established project claim — treat it as provisional.

---

# Massachusetts

Codified evidence layer: 338 evidence-layer rows across 9 cities (per `national_corpus_expansion_preflight_2026-07-12.md`). MA is the corpus's densest cross-occupation base — the state most likely to support a genuine within-city, cross-occupation wage-mechanism comparison, but no single MA city yet has a uniform, full occupation grid.

## Franklin, MA

**Sources**
- `ma_franklin_police_2022` — Franklin Police Association CBA, 2022-2025.
- `ma_franklin_fire_2022` — Professional Firefighters of Franklin (IAFF Local 2637) CBA, 2022-2025.
- `ma_franklin_library_2022` — Franklin Public Library Staff Association CBA, 2022-2025.
- `ma_franklin_public_works_2022` — AFSCME Council 93 Local 1298 DPW CBA, 2022-2025.
- `ma_franklin_other_2022` — AFSCME Council 93 Local 1298 Custodians CBA, 2022-2025.

**Claims / Relevant findings**
Franklin, alongside Seekonk, anchors `CLM-2026-07-12-03` (Massachusetts cross-occupation base): five occupation classes in one overlapping 2022-2025 cycle let the same-city, same-cycle design run cleanly, with no cross-city or cross-cycle confound. Franklin's police and fire rows both show verified `overtime_callback_holdover_mandatory_extra_work` and `hazard_risk_stress_or_line_of_duty_rationale` evidence; its public works and library rows show `classification_reclassification_or_grade_structure` — the pattern `CLM-2026-07-12-04` and `CLM-2026-07-12-05` are built on (safety pressure paired with conversion channels; non-safety wage-setting routed through classification/grade language instead).

**Limits / Gaps**
Mechanism presence only, not wage-effect size — codify detects that a clause exists in a curated window, not how much it matters. No repeat cycle yet (only the 2022-2025 window is codified). Report-ready as an evidence-base description per `claim_readiness_table_2026-07-12.csv`, not as a stronger causal claim.

## Seekonk, MA

**Sources**
- `ma_seekonk_police_2022` — FOP Mass C.O.P. Local #215 CBA, 2022-2025.
- `ma_seekonk_fire_2022` — IAFF Local 1931 CBA, 2022-2025.
- `ma_seekonk_library_2023` — Seekonk Public Library Employee Association CBA, 2023-2026.
- `ma_seekonk_public_works_2023` — AFSCME Council 93 Local 1701 DPW CBA, 2023-2026.
- `ma_seekonk_teacher_2021` — Seekonk Educators Association CBA, 2021-2024.

**Claims / Relevant findings**
Seekonk is the corpus's widest single-city occupation spread (police, fire, library, public works, teacher — 6 occupation classes across the ingest/pipeline.py row set). It is the second dense MA anchor for `CLM-2026-07-12-03`, and its public-works row is one of only 3 verified-present `non_safety_wage_restraint_or_admin_channel` rows in the entire corpus — a thin attribute this city helps establish.

**Limits / Gaps**
Same curated-window/mechanism-presence limits as Franklin. No repeat cycle. Report-ready as an evidence-base description, not a stronger claim.

## Wayland, MA

**Sources**
- `ma_wayland_police_2020` — police CBA, 2020-2023.
- `ma_wayland_fire_jlmc_2020` — IAFF Local 1978 JLMC arbitration award, 2020-2023.
- `ma_wayland_other_2021` — AFSCME Local 690 (Wayland-1/Wayland-2) CBA, 2021-2023 (OCR-recovered from a scanned document).
- `ma_wayland_public_works_2020`, `ma_wayland_library_2020` — DPW and library CBAs, 2020-2023.

**Claims / Relevant findings**
Wayland is one of the few MA cities with a fire *interest-arbitration award* (JLMC) directly codified, in principle useful for `CLM-2026-07-12-06` (the arbitration-distinction claim) and `CLM-2026-07-12-04` (minimum-staffing/continuous-coverage evidence — Wayland fire has a verified `minimum_staffing_or_continuous_coverage` row).

**Limits / Gaps**
**Named, specific weakness:** the fire JLMC award itself returned **zero** verified-present attributes in codify (per `source_inventory_for_report_2026-07-10.csv`) — do not cite Wayland fire as a strong arbitration-distinction source until this is reviewed; the award may simply not contain the specific 19-attribute-codebook language codify looks for, or the codify window may have missed it. `ma_wayland_other_2021` is OCR-messy text quality (bounded OCR recovery). No repeat cycle.

## Boston, MA

**Sources**
- `ma_boston_police_2020` — Boston Police Patrolmen's Association MOA, 2020-2025 (in `data/contracts.csv`, only partially codified per the coverage audit).
- `ma_boston_clerical_admin_2023` — SENA/USW Local 9158 CBA, 2023-2027.

**Claims / Relevant findings**
A `matched_pair` (police + clerical_admin), supporting `CLM-2026-07-12-03` as a large-city data point, but Boston is the corpus's biggest single city and currently contributes only 2 occupation classes.

**Limits / Gaps**
**No fire leg at all.** This is the single highest-value gap in the entire codified MA set: a Boston fire source (large department, likely interest-arbitration-heavy) would materially strengthen both the cross-occupation base claim and the safety-conversion-channel claim. `recommended_next_action=scan_more`.

## Georgetown, MA

**Sources**
- `ma_georgetown_police_2020` — police (command staff) CBA, 2020-2023.
- `ma_georgetown_other_2020` — AFSCME Council 93 Local 939 (Custodians) CBA, 2020-2023.

**Claims / Relevant findings**
A small-town `matched_pair` supporting `CLM-2026-07-12-03` as a smaller-jurisdiction contrast point to Franklin/Seekonk.

**Limits / Gaps**
No fire leg. `other` occupation class needs recognition-clause confirmation before any more specific label is assigned. Lower priority than closing Boston's fire gap, given town size.

## Somerville, MA

**Sources**
- `ma_somerville_police_spsoa_2012` — Somerville Police Superior Officers Association arbitration award, 2012-2018.
- `ma_somerville_police_spea_2012` — Somerville Police Employees Association arbitration award, 2012-2015 (in `data/contracts.csv`; not among the cities the codified evidence-layer breakdown enumerates by name in the preflight doc, but present in the corpus).

**Claims / Relevant findings**
`ma_somerville_police_spsoa_2012` is **the single strongest source in the corpus**: 9 verified-present attributes, the richest of any codified contract, and the corpus's only verified `peer_comparator_wage_comparability` row. It anchors `CLM-2026-07-12-06` (arbitration distinction) and is the sole primary support for `CLM-2026-07-12-07` (comparator wage evidence — itself `needs_more_evidence`, `report_ready=no`, because one row is thin support for a general claim).

**Limits / Gaps**
**Somerville is safety-only — one of 5 currently unmatched safety units in the corpus** (per `AGENTS.md`'s coverage-discipline rule, this is flagged dead weight for the cross-occupation design specifically, even though the source itself is excellent). Closing this gap (a Somerville clerical/DPW/library CBA in an overlapping cycle) is the single highest-leverage source-acquisition target in the whole corpus: it would let the strongest existing source finally support a real triad comparison.

**Sourcing pass, 2026-07-14 (no ingestion — document not locatable).** A targeted, document-first search (city HR pages, union sites, Legistar and the city's older IQM2 legislative-document portal, council appropriation orders) confirmed real, specific, current non-safety candidates exist but found no downloadable agreement text for any of them:
- **SMEU (formerly SMEA) Unit B** — the city's largest bargaining unit, covering DPW, Water & Sewer, Library, City Clerk, Parking, and Inspectional Services across ~25 departments; current MOA covers FY2023-2025 (ratified Jan. 2025). Named, cycle-dated, department-scoped — but no PDF found on `somervillema.gov`, the union's own site (`smeaunion.org`/`smeu.org`, "Contract Clock" page returned 403), Legistar, or the IQM2 archive.
- **SEIU Local 3 (Firemen and Oilers) Custodians** — original contract FY2023-FY25, a 2025/2026 wage-reopener MOA also referenced. Same non-locatable-document pattern.
- **SMEA Unit D** — ISD/Parking staff, PD clerical staff, DPW custodial/facilities supervisors; MOA for FY2023-2025 signed January 22, 2026 (per the city's own news page) — again, announcement only, no attached document.
- A city-hosted legislative-document portal (`somervillecityma.iqm2.com`, archive of 2010-2022 council records) does exist and does host some real CBA-adjacent PDFs (confirmed by retrieving the already-known `ma_somerville_police_spsoa_2012` award through it, and a 2012-2015 Fire Alarm Unit CBA appropriation from the same era) — but its full-text search is out of service, and no SMEA/SEIU Local 3 non-safety agreement text surfaced through Google's `site:` search of it. Council appropriation orders (both on Legistar and IQM2) fund these agreements but do not attach the executed CBA/MOA text itself, so per `claim_testing_source_wave_methodology_2026-07-12.md` Step 4 they are `context_only`, not `ingest_next`.
- **Not ingested** — no document met the provenance bar (a locatable, actual agreement text, not a news summary or funding order). Per the task's own instruction, weak/unconfirmed candidates are documented, not speculatively ingested.
- **Next-step recommendation:** direct outreach to Somerville HR (`personnel@somervillema.gov`) or the union (SMEU/SEIU Local 3) is the most likely way to obtain the actual document — but that is a direct-request route, not open-web sourcing, and was out of scope for this pass (no FOIA/PRR route was used or is being proposed; a direct informal document request to a union or HR press contact is a judgment call for a future session, not exercised here).

## Newton, MA

**Sources**
- `ma_newton_police_2015` — police CBA, 2015-2018 (ingested; large scanned-photo PDF, `text_quality=partial`).

**Claims / Relevant findings**
Context only — not enumerated among the codified evidence-layer cities in `national_corpus_expansion_preflight_2026-07-12.md`, so treat as **not currently primary support** for any CLM. A 2026-07-13/14 deterministic re-extraction confirmed a genuine, verbatim "ARTICLE XIV NO STRIKE CLAUSE" — real content exists in this document even though it isn't part of the primary codified set.

**Limits / Gaps**
Safety-only, unmatched (one of the corpus's 5 unmatched safety units). Lower priority than Somerville given Somerville's stronger existing evidence quality. A Newton non-safety CBA in an overlapping cycle would close this.

## Worcester, MA — **not yet codified**

**Sources**
- `ma_worcester_fire_2017` (IAFF Local 1009, 2017-2020), `ma_worcester_clerical_admin_2017` (Local 490, 2017-2020, MOA-style — incorporates a prior base CBA by reference, full base not in corpus), `ma_worcester_public_works_2017` (Local 170, 2017-2020) — all in `data/contracts.csv`.

**Claims / Relevant findings**
**None yet — evidence-eligible, not evidence-bearing.** Worcester has a real fire + 2-non-safety set ingested (`matched_pair` design status) but has never been run through GABRIEL/codify; 0 evidence-layer rows exist for this city. Do not cite Worcester in support of any claim until codified.

**Limits / Gaps**
No police leg. The cheapest possible next step in the entire corpus: codify what is already ingested (no new sourcing needed) before searching for a Worcester police source.

## Arlington, MA — **not yet codified**

**Sources**
- `ma_arlington_fire_2021` (IAFF, FY2022-2024), `ma_arlington_public_works_2015`/`_2018`/`_2021` (AFSCME Local 680, multiple cycles) — in `data/contracts.csv`.

**Claims / Relevant findings**
**None yet.** Same pattern as Worcester: fire + public_works `matched_pair` ingested, uncodified, 0 evidence-layer rows.

**Limits / Gaps**
No police leg at all. Codify existing contracts before new sourcing.

---

# Ohio

Codified evidence layer: 270 evidence-layer rows across 4 cities — the corpus's cleanest matched-triad design, all four cities under Ohio's shared ORC Chapter 4117 public-sector bargaining framework. `CLM-2026-07-12-01` (Ohio matched triads) is `report_ready=yes` at the state level, anchored by all four cities below.

## Columbus, OH

**Sources**
- `oh_columbus_police_2023` — FOP Capital City Lodge No. 9 CBA, 2023-2026.
- `oh_columbus_fire_2023` — IAFF Local 67 CBA, 2023-2026.
- `oh_columbus_other_2024` — AFSCME Ohio Council 8 Local 1632 CBA, 2024-2027.

**Claims / Relevant findings**
One of Columbus's strongest single-city results for `CLM-2026-07-12-01`: both safety rows originally showed verified `interest_arbitration_or_formal_impasse_backstop` evidence and the non-safety row shows verified `classification_reclassification_or_grade_structure` evidence — the core pattern the Ohio claim rests on.

**Limits / Gaps**
**Data-integrity correction (2026-07-13):** the police and fire rows' `arbitration_clause_text` was discovered to be non-verbatim (fabricated/paraphrased text, not found anywhere in the source PDF) and was corrected to `interest_arbitration_flag=0`/cleared, per `wage_mechanism_evidence_checklist.md` item 15. **This changes Columbus's current deterministic-extraction-layer support for `CLM-2026-07-12-01`'s interest-arbitration pattern specifically** — manual document review confirmed genuine ORC 4117.14(G) impasse/conciliation language exists in the Columbus Fire source, but no safe general regex trigger currently captures it (a documented, open extraction gap, not fabricated to compensate). **Note:** this correction was applied only to `data/contracts.csv`'s deterministic layer; whether it also affects `docs/analysis/gabriel_codify_evidence_layer.csv` (the separate GABRIEL evidence layer the claim register actually cites) has **not been checked this session** — if the GABRIEL evidence layer was built from the same fabricated span, `CLM-2026-07-12-01`'s Columbus evidence may need re-verification. Flagged as a source need below.

## Cleveland, OH

**Sources**
- `oh_cleveland_police_2025` — Cleveland Police Patrolmen's Association CBA, 2025-2028.
- `oh_cleveland_fire_2025` — Cleveland Fire Fighters Local 93 CBA, 2025-2028.
- `oh_cleveland_other_2022` — AFSCME Ohio Council 8 Local 100 CBA, 2022-2025.

**Claims / Relevant findings**
Supports `CLM-2026-07-12-01`: police shows verified interest/impasse evidence, non-safety shows verified classification evidence.

**Limits / Gaps**
Cleveland fire has a previously flagged/unverified interest-arbitration row, already excluded from primary support per `claim_consolidation_summary_2026-07-12.md` — do not cite it until re-audited. (Separately, a 2026-07-13 regression check on the deterministic layer found and fixed a subcontracting/privatization-dispute false positive on Cleveland's `other` row — see `wage_mechanism_evidence_checklist.md` item 17 — that finding is now resolved.)

## Cincinnati, OH

**Sources**
- `oh_cincinnati_police_2024` (FOP Queen City Lodge No. 69, non-supervisors), `oh_cincinnati_police_sup_2024` (same lodge, supervisors), `oh_cincinnati_fire_2023` (IAFF Local 48), `oh_cincinnati_other_2025` (Cincinnati Organized and Dedicated Employees).

**Claims / Relevant findings**
Contributes to `CLM-2026-07-12-01` but with the corpus's weakest per-contract signal.

**Limits / Gaps**
**Fire and the police-supervisor unit both returned zero verified-present attributes** — an explicit, named limitation of `CLM-2026-07-12-01`. This is the priority re-codify target among the four Ohio triad cities (broader-window or full-document codify recommended). The 2026-07-13 extractor fix also found and applied a genuine new `me_too_clause_flag` positive on the fire row (a verbatim "'Me-too' with FOP on wages..." clause, previously blank) — worth incorporating into a future codify wave's evidence base.

## Toledo, OH

**Sources**
- `oh_toledo_police_2024` (TPPA), `oh_toledo_fire_2024` (Local 92), `oh_toledo_other_2024` (Local 2058).

**Claims / Relevant findings**
Toledo police is one of four sources anchoring `CLM-2026-07-12-06` (arbitration distinction) alongside San Antonio, Houston, and Somerville — dual role, also supporting `CLM-2026-07-12-01`. The 2026-07-13 extractor fix found a genuine new `interest_arbitration_flag` positive on the police row (a verbatim "shall be subject to an interest arbitration" clause inside a long Cost Containment Committee article, previously missed) — this strengthens Toledo's existing arbitration-distinction role in a future codify wave.

**Limits / Gaps**
Non-safety (`other_2024`) shows only 2 verified-present attributes — one of the thinner non-safety results in the Ohio set.

---

# Texas

Codified evidence layer: 173 evidence-layer rows across 3 cities. Texas is the corpus's clearest example of **institutionally uneven** safety wage-setting — a genuine matched triad in one city (Houston) and safety-only/safety-adjacent designs elsewhere, which is itself the claim (`CLM-2026-07-12-02`), not a data gap to be explained away.

## Houston, TX

**Sources**
- `tx_houston_police_2024` (HPOU CBA), `tx_houston_fire_2024` (IAFF Local 341 arbitration award), `tx_houston_other_2024` (HOPE/AFSCME Local 123 CBA).

**Claims / Relevant findings**
Houston is **Texas's only genuinely matched triad** — anchors `CLM-2026-07-12-02` (Texas institutional unevenness) and is the sole comparator for `CLM-2026-07-12-08`'s "outside Houston" gap framing. Also contributes to `CLM-2026-07-12-06` (arbitration distinction).

**Limits / Gaps**
Single-city base for the *entire* Texas non-safety comparison — source-production effects (Houston simply has more public labor-relations infrastructure) may be driving the apparent pattern rather than a genuine institutional difference. A second matched Texas non-safety city (San Antonio or Austin general-municipal) is needed to stop relying on Houston alone. `CLM-2026-07-12-02` is `report_ready=yes`, but explicitly as a source/design claim, not a substantive wage-gap claim.

## Austin, TX

**Sources**
- `tx_austin_police_2024`, `tx_austin_fire_2023`, `tx_austin_nursehealth_2023` (Austin EMS Association).

**Claims / Relevant findings**
Contributes to `CLM-2026-07-12-04` (safety pressure conversion channels) — Austin fire shows verified `minimum_staffing_or_continuous_coverage`.

**Limits / Gaps**
**Austin's third leg (EMS/nurse_health) is safety-adjacent, not an ordinary civilian comparator** — it sits under the same Ch.143 Civil Service Commission as police/fire. Do not cite Austin as a clean matched triad without this caveat; the source inventory itself labels this "exploratory." An Austin general-municipal (clerical, public works) CBA distinct from EMS is the specific gap.

## San Antonio, TX

**Sources**
- `tx_san_antonio_police_2022` (SAPOA CBA), `tx_san_antonio_fire_2024` (IAFF Local 624 CBA).

**Claims / Relevant findings**
San Antonio police is **the corpus's clearest single-document test of the interest-vs-grievance arbitration distinction** (`CLM-2026-07-12-06`) — the same document contains both a Chapter 174 impasse procedure and a separate grievance-arbitration clause, correctly separated by codify.

**Limits / Gaps**
**Deliberately unmatched** (added for institutional-contrast value, per the source inventory's own note — not a data gap to be apologized for). Documented false negative on peer-comparator language: the codify pass missed genuine comparator wording that a manual audit later found (`CLM-2026-07-12-07` limitation). Safety-only — one of the corpus's 5 unmatched safety units. **A San Antonio general-municipal non-safety CBA is the single highest-priority non-safety gap in the entire current corpus**, explicitly named `urgent` in `claim_driven_source_needs_2026-07-12.csv` (`CLM-2026-07-12-08`).

**Sourcing pass, 2026-07-14 (no ingestion — evidence points to structural non-availability, not a search-coverage failure).** Investigated whether San Antonio has any real general-municipal non-safety union/CBA:
- **AFSCME Local 2021** represents ~6,000 San Antonio civilian employees, but by its own account (`afscme2021.org/about`) that representation runs through an **Employee Management Committee (EMC)** — an advisory body that "wins city buy-in on priorities" through persuasion, plus a Strategic Planning Committee and a PAC. No signed collective bargaining agreement is referenced anywhere on the union's own materials; the city's own `sa.gov/.../Collective-Bargaining` page returned 403 (blocked, not confirmed empty) but every other source describes the EMC as advisory/non-binding, not a contract.
- **Institutional root cause identified:** Texas Government Code Chapter 617 prohibits public-sector collective bargaining generally; police and fire in Texas cities that opt in (San Antonio has) get a statutory carve-out via Local Government Code Chapter 174 (the Fire and Police Employee Relations Act) — which is exactly why `tx_san_antonio_police_2022` and `tx_san_antonio_fire_2024` exist as real CBAs. San Antonio has not extended an equivalent statutory bargaining channel to civilian employees; instead, general wage-setting runs through council-adopted **Municipal Civil Service Rules** (approved by council resolution, 1977) and a council-set classification/pay plan (Administrative Directive AD 4.13A) — real, public, findable documents, but **unilateral administrative instruments, not bilaterally negotiated union contracts**. They have no bargaining-unit counterparty or recognition clause and so do not meet this project's unit-of-observation definition (`AGENTS.md`: "one row = one bargaining unit's contract") — not ingested, and would not be schema-eligible as a `source_type=cba` row even if ingested.
- Checked San Antonio Water System (SAWS, a separate municipal utility entity) for a possible CWA/utility-worker CBA as an alternative non-safety lead — found no evidence of one; also would be a different legal employer than "City of San Antonio," weakening its value as a same-city comparator even if found.
- **Read as an evidenced update to `CLM-2026-07-12-08`/`H6`, not new coded evidence**: this is a sourcing/institutional finding (added to both CSVs' `notes` fields this session), not a codify result, and does not change either item's `status`/`evidence_strength`/`report_ready`. It does upgrade the gap's characterization from "not yet found" to "plausibly structural" — a real civilian CBA may simply not exist for this employer.
- **Next-step recommendation:** if a San Antonio non-safety comparator is still wanted, the more promising path is no longer "search harder for a hidden CBA" but either (a) treat San Antonio's civil-service/administrative pay-setting documents as a *different* kind of comparator specifically for the `civil_service_or_statutory_employment_channel` attribute (a research-design decision, not a sourcing task, and not made here), or (b) redirect the Texas non-safety search to Austin or Houston, where AGENTS.md's non-safety search already succeeded once (Houston `other`, Austin `nurse_health`).

---

# Pennsylvania

**No PA city is codified.** Every finding below is a source-availability/design-level hypothesis per `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md` — real `data/contracts.csv` rows exist for Philadelphia, but none have been through GABRIEL/codify.

## Philadelphia, PA — **ingested, design-ready for codify, not yet codified**

**Sources**
- `pa_philadelphia_police_2025` — FOP Lodge 5 Act 111 interest-arbitration award, 2025-2027 (arbitration_award, city/union-hosted).
- `pa_philadelphia_fire_2017` — IAFF Local 22 Act 111 interest-arbitration award, 2017-2020 (arbitration_award, city-hosted).
- `pa_philadelphia_other_2021` — AFSCME DC33 CBA, 2021-2024 (`occupation_class=other`, recognition-clause-first).
- `pa_philadelphia_other_2025` — AFSCME DC47 Locals 2186/2187 term sheet, 2025-2028 (`other`; a 5-document compiled packet, see `extractor_fix_and_philadelphia_fire_gap_2026-07-13.md` for the full breakdown — execution is a totality-of-evidence judgment, not one clean signature).
- `pa_philadelphia_other_2017` — AFSCME DC47 Local 2186 MOA, 2017-2020 (`other`; incorporates a 2009-2017 base CBA by reference, base not in corpus).

**Claims / Relevant findings**
**Philadelphia is now matched on both legs — the strongest PA design and, alongside Trenton NJ, the strongest PA/NJ matched-triad candidate outside Ohio.** Police (2025-2027) overlap-cycle vs. the DC47 2025-2028 term sheet; fire (2017-2020) **exact-cycle** vs. the DC47 Local 2186 2017-2020 MOA. If codified, this design could test `H1`/`H2`/`H4`/`H6`/`H7` — whether Ohio-style matched-triad patterns (safety interest-arbitration backstops paired with conversion channels; non-safety routed through classification/admin language instead) generalize to a large non-Ohio city under a different statutory framework (PA Act 111 for safety, PA Act 195/PERA for non-safety). **This is a hypothesis about what codify might find, not a coded finding** — no CLM ID applies yet.

**Limits / Gaps**
Zero codified evidence — everything above is design-level (real sources exist, cycles genuinely overlap, but no GABRIEL/codify has run). The DC47 2025-2028 term sheet's execution rests on persistent union hosting + news corroboration + same-round side letters' apparent signatures, not one unambiguous signature page. The 2017-2020 MOA incorporates a base CBA not in the corpus, limiting what classification/workload language this row alone can show. `recommended_next_action=codify_more`.

## Pittsburgh, PA — **candidate-only, no sources ingested**

**Sources (candidates only, not ingested)**
FOP Fort Pitt Lodge 1 (found only on Scribd, unofficial host); IAFF Local 1 (named, no document found across two search rounds); AFSCME Local 2719 (a confirmed, recently-signed CBA with a located union contracts page — the only leg with real document-level provenance).

**Claims / Relevant findings**
None — no rows ingested. If sourced, could test `H1`/`H7`.

**Limits / Gaps**
Non-safety is the only leg with a real lead; police needs an official-domain replacement for the Scribd copy; fire has zero document lead. `recommended_next_action=scan_more`.

## Allentown, PA — **candidate-only, no sources ingested**

**Sources (candidates only)**
FOP Lodge 10 (named, no document); IAFF Local 302 (named, contract-documents page possibly access-gated); SEIU Local 668 (corrected union identity — an earlier scan round had wrongly assumed AFSCME for the non-safety leg).

**Claims / Relevant findings**
None. If sourced, could test `H1`/`H2`/`H7`.

**Limits / Gaps**
No leg has reached document level after two search rounds — currently the weakest large PA city scanned. `recommended_next_action=scan_more`.

## Erie, PA — **candidate-only, no sources ingested**

**Sources (candidates only)**
FOP Lodge 7/Haas Memorial Lodge (2001 case-law reference only — 24+ years old); IAFF Local 293 (named, no document); AFSCME Local 2206 (confirmed ratified 2026-03-04 contract, document not located).

**Claims / Relevant findings**
None. Lowest-priority of the five PA cities scanned.

**Limits / Gaps**
A jurisdiction false positive (Erie County, NY) must continue to be excluded from any future search. `recommended_next_action=scan_more`.

## Reading, PA — **candidate-only, no sources ingested**

**Sources (candidates only)**
A "Reading Public Library CBA" candidate — **confirmed false in a prior session: the actual document is a construction/electrical-contractor bid contract, not a labor agreement, and is no longer a valid candidate.** AFSCME Local 2763 (a confirmed dated agreement, document not located); FOP Lodge #9 (named, no document); IAFF Local 1803 (named, no document).

**Claims / Relevant findings**
None. The corrected candidate list leaves Reading with a confirmed non-safety union lead but zero document-level sources at all.

**Limits / Gaps**
The police leg has zero document or award evidence, blocking any matched-design claim regardless of non-safety strength. Explicitly held out of prior recommended ingestion batches for this reason.

---

# New Jersey

**No NJ city is codified.** Newark and Trenton have real, ingested `data/contracts.csv` rows (design-level matched pairs/triads); Jersey City, Paterson, and Elizabeth remain candidate-only.

## Trenton, NJ — **ingested, design-ready for codify, not yet codified**

**Sources**
- `nj_trenton_other_2019` — AFSCME Local 2281 (Supervisory Employees) CBA, 2019-2023.
- `nj_trenton_police_2019` — PBA Local 11 CBA, 2019-2024 (via a City Council resolution authorizing execution).
- `nj_trenton_fire_2021` — Trenton Fire Officers Association/FMBA Local 206 CBA, 2021-2026.

**Claims / Relevant findings**
**Trenton is the strongest PA/NJ matched-design result to date — all three occupation classes pairwise cycle-overlap in 2021-2023**, found via direct NJ PERC public-sector-contracts index browsing by employer name (a technique that succeeded after generic web search had failed twice across two prior sessions). If codified, directly tests `H1`/`H2`/`H4`/`H7` and the Ohio-triad-generalizability question in a state with a *different* interest-arbitration structure (NJ's Police and Fire Public Interest Arbitration Reform Act, an external statutory process, vs. Ohio's ORC 4117 or PA's Act 111). **Hypothesis, not coded finding — no CLM ID yet.**

**Limits / Gaps**
Zero codified evidence. Two deterministic-extraction issues were found and corrected on the fire row (`wage_mechanism_evidence_checklist.md` item 13, including an inversion — the source text explicitly *excludes* fiscal matters from interest arbitration, which is itself a substantively interesting institutional fact once read correctly). `recommended_next_action=codify_more`.

## Newark, NJ — **ingested, matched pair, not yet codified**

**Sources**
- `nj_newark_other_2020` — Teamsters Local 97 CBA, 2020-2023 (covers **municipal attorneys**, not sanitation/public works — a recognition-clause correction from the union-name assumption).
- `nj_newark_police_2018` — FOP Lodge 12 CBA, 2018-2023 (overlaps the non-safety row for 2020-2023).
- `nj_newark_fire_2013` — Newark Firefighters Union CBA, 2013-2015 (does not overlap; design-level addition only).

**Claims / Relevant findings**
Newark police genuinely cycle-overlaps the non-safety row — a real matched pair, not merely design-level occupation-class presence. If codified, could test `H1`/`H2`/`H7`.

**Limits / Gaps**
Fire (2013-2015) doesn't overlap anything and is the oldest/weakest leg. A more current Newark fire document (IAFF Local 1860, 2017-2023 term) was identified by name/cycle via PERC-index browsing across two sessions but its document has never been located — the single most useful still-open PA/NJ sourcing gap. Zero codified evidence.

## Jersey City, NJ — **candidate-only, structurally strong but out-of-window**

**Sources (candidates only, direct PDFs found but not ingested)**
Jersey City PSOA CBA 2009-2012; IAFF Local 1066 resolution 2009-2015; JC Public Employees Local 245 MOA 2015; JC Public Employees Local 246 2015 — all four via direct PERC-index PDFs.

**Claims / Relevant findings**
None yet — **structurally the strongest matched-triad candidate shape found in either state** (all three roles, two distinct non-safety unions), but every document is dated ~2009-2015, mostly outside the project's 2014-2024 observation window.

**Limits / Gaps**
Needs current-cycle (2020s) successors located before any of these four documents would meet the CBA source-verification standard. Not a "sources don't exist" problem — a document-vintage problem.

## Paterson, NJ — **candidate-only, non-safety gap disqualifying**

**Sources (candidates only, named units, no documents)**
PBA Local 1 (named via a 2021 PERC interim-relief decision); FMBA Local 2/Tactical Fire Officers Association (named via a 2012 PERC decision, including a live staffing-level grievance).

**Claims / Relevant findings**
None. The live TFOA staffing grievance is plausibly relevant to `H4` (minimum-staffing centrality) if the underlying document is ever located.

**Limits / Gaps**
Non-safety is a hard, repeated gap across two search rounds — the only Paterson-domain PERC documents found are for the school district, a different employer entirely. This disqualifies the matched-triad design regardless of how well-documented the safety side is. `recommended_next_action=hold`.

## Elizabeth, NJ — **weakest city in either state**

**Sources**
Elizabeth Superior Officers Association — a generic PERC synopsis reference only, no named local for fire or non-safety.

**Claims / Relevant findings**
None — insufficient evidence to scope even a hypothesis.

**Limits / Gaps**
Deprioritized relative to the other four NJ cities. `recommended_next_action=hold`.

---

# Cross-state synthesis

- **Report-ready-adjacent claims today rest entirely on MA/OH/TX** — 16 codified cities. `CLM-2026-07-12-01` (Ohio matched triads) and `CLM-2026-07-12-06` (arbitration distinction) are the two strongest, `report_ready=yes`; `CLM-2026-07-12-02` (Texas unevenness) is `report_ready=yes` as a design/source claim specifically, not a wage-gap claim. `CLM-2026-07-12-07` (comparator evidence) and `CLM-2026-07-12-08` (Texas non-safety outside Houston) are both explicitly `needs_more_evidence`/`report_ready=no` — do not overstate either in any future report.
- **Philadelphia PA and Trenton NJ are the two strongest candidates for the next codify wave** — both now genuinely matched-design (not just occupation-class-present), found via the same document-level, primary-source-first method (union locals' own contract archives, direct PERC-index browsing) rather than generic search.
- **A Somerville MA non-safety CBA remains the single highest-leverage source-acquisition target in the whole corpus** — real, current, department-scoped candidates are now named (SMEU Unit B; SEIU Local 3 Custodians) but no document was locatable as of 2026-07-14; see the Somerville section for the full sourcing trail.
- **San Antonio TX's non-safety gap now has a probable institutional explanation, not just a search failure**: civilian employees are represented through a non-binding advisory committee, not a CBA, consistent with TX Gov't Code Ch. 617's general bargaining prohibition and the absence of a civilian-specific statutory carve-out (unlike police/fire's Ch. 174 channel). See the San Antonio section for the full finding and its two evidence-generating sources.
- **PA/NJ source availability is uneven and should not be treated as a uniform "PA/NJ" bloc**: Philadelphia and Trenton are strong; Jersey City is strong-but-out-of-window; Newark is a real matched pair with one gap; Pittsburgh/Allentown/Erie/Reading/Paterson/Elizabeth range from weak to essentially unscoped.
- **The Columbus/GABRIEL-evidence-layer contamination question (open as of 2026-07-14's earlier build) is resolved: no contamination found.** See "What would change this ledger" below.

## Source needs (cross-cutting, from this build)

1. A Somerville MA non-safety CBA (highest-leverage single acquisition in the corpus) — SMEU Unit B (DPW/Water&Sewer/Library/Clerk/Parking/Inspectional Services, FY23-25) and SEIU Local 3 Custodians (FY23-25) are the named targets; direct outreach to Somerville HR or the unions is the most likely next path, not further open-web search.
2. A San Antonio TX general-municipal non-safety CBA — now a lower-confidence target given the 2026-07-14 finding that civilian wage-setting there runs through non-bargaining administrative/civil-service channels; if still pursued, treat as possibly redirecting to a different comparator concept rather than searching harder for a hidden CBA.
3. A Boston MA fire source (closes the corpus's largest-city gap).
4. Newark NJ's current-cycle IAFF Local 1860 fire CBA (2017-2023 term, identified but never located across two sessions).
5. Current-cycle (2020s) successors to Jersey City's four dated (2009-2015) PERC documents.

## What would change this ledger

- Any codify wave against Philadelphia or Trenton would move those two cities from "design-level hypothesis" to "codified evidence" and requires a full rebuild of their sections plus new `CLM-2026-07-12-XX` (or successor) claim IDs.
- **Columbus/GABRIEL contamination check (resolved 2026-07-14, no rebuild needed):** verified directly that `docs/analysis/gabriel_codify_evidence_layer.csv`'s Columbus police/fire `interest_arbitration_or_formal_impasse_backstop` excerpts (and all 37 of Columbus's `present`-status evidence rows) are genuine, independently-grounded verbatim excerpts from the source PDFs — confirmed via a direct substring/whitespace-normalized match against a fresh extraction of both PDFs. They read as different text than, and are structurally unrelated to, the fabricated `arbitration_clause_text` found and corrected in `data/contracts.csv` on 2026-07-13 (that fabricated text itself does NOT match the source PDFs, even normalized — confirming it really was fabricated, not just reformatted). The codify evidence-window builder (`gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv` etc.) constructs its windows directly from page-anchored source-PDF text, structurally independent of the `data/contracts.csv` text fields — so this contamination pathway was never possible. All 7 evidence IDs supporting `CLM-2026-07-12-01` were individually re-checked and are `grounded`/`viewer_verified=1`. **No claim support changed; no downstream artifact needed a fix or rebuild.**
- A Worcester/Arlington codify pass (cheapest available next step — sources already ingested) would add 2 more codified MA cities with no new sourcing required.

---

## Changelog

- **2026-07-14 (initial build)** — Covering all 19 cities currently in `data/contracts.csv` post-commit `9c1cb2c` and that session's `no_strike_clause_flag` fix. Built from `docs/analysis/state_city_claim_map_2026-07-12.csv`, `docs/analysis/claim_register_2026-07-12.csv`, `docs/analysis/claim_consolidation_summary_2026-07-12.md`, `docs/analysis/national_corpus_expansion_preflight_2026-07-12.md`, `docs/analysis/national_corpus_current_coverage_gap_audit_2026-07-12.md`, and `docs/analysis/extractor_fix_and_philadelphia_fire_gap_2026-07-13.md`.
- **2026-07-14 (rename + Columbus check + sourcing pass)** — File renamed from `state_city_claims_ledger_2026-07-14.md` to this permanent path (content and changelog history preserved; see the note at the top of this file). Resolved the open Columbus/GABRIEL-evidence-layer contamination question with no rebuild needed (see "What would change this ledger" above). Ran a targeted sourcing pass for Somerville MA and San Antonio TX non-safety comparators: no documents were ingested (neither passed the provenance bar), but both sections above now carry a detailed sourcing trail — Somerville has named, cycle-current candidate unions with no locatable document; San Antonio's gap now has a probable institutional explanation (no civilian CBA exists; wage-setting runs through non-bargaining administrative channels). `docs/analysis/claim_register_2026-07-12.csv` (`CLM-2026-07-12-08`) and `docs/analysis/hypothesis_tracker_2026-07-12.csv` (`H6`) both got a `notes`-field-only update recording the San Antonio institutional finding; no `status`/`evidence_strength`/`report_ready` field changed on either.
