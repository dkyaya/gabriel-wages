# State/City Claims Ledger

**Canonical path:** `docs/analysis/state_city_claims_ledger.md` — this filename is permanent and does not change between sessions. **Do not fork a new dated copy of this file.** If you are about to write `state_city_claims_ledger_<date>.md`, stop — edit this file in place instead.

**Last updated:** 2026-07-14 (interpretive-standard rebuild + Worcester/Arlington/Philadelphia/Trenton evidence) — see the changelog at the bottom for full revision history.

## Interpretive standard (read this before adding or citing a claim)

This ledger exists to make **evidence-backed claims about what is causing or structuring the safety/non-safety wage-setting difference in a specific municipality** — not to inventory sources. A source list without a claim is not useful to a future report-writing session; a claim with no source trail is not trustworthy. Both halves are required.

The standard for every claim in this file:

- **The ledger is meant to make claims, not merely list sources.** Every municipality section below should answer "what does the evidence currently in this corpus let us say happened here, and why," not just "what documents exist for this city."
- **A claim does not need to be final or nationally generalizable to be useful.** A well-reasoned, well-bounded claim about one city in one cycle is a legitimate research output. Do not wait for national certainty before writing a municipal claim.
- **A claim should be the most defensible interpretation of the evidence currently available for that municipality** — not the most cautious possible statement, and not an overreach. Say what the evidence actually supports, plainly.
- **Every claim must include:** the evidence it rests on (with a locator another agent can follow), the reasoning connecting that evidence to the safety/non-safety wage-setting gap, the counterevidence or limits that bound it, and the specific future evidence that would change it.
- **Claims are allowed to be revised as new evidence arrives.** That is the research process, not a failure of a prior session's judgment. When a claim changes, say what changed and why in the claim itself or in the changelog — do not silently overwrite.
- **What is not acceptable:** a claim with no source trail, no reasoning connecting evidence to the wage-setting question, or no stated condition under which it would change. A claim that cannot be traced back to a `contract_id`/`evidence_id`/corpus path, or that could never in principle be revised by new evidence, does not belong in this file.

## Claim maturity vocabulary

Every claim and every municipality section below is labeled with one of these four statuses. Use them consistently — they are load-bearing for how a future report-writing session should treat the claim.

- **Design-ready** — real sources are ingested (`data/contracts.csv` rows exist) and the matched-comparison design is sound (safety + non-safety, overlapping or exact cycle), but GABRIEL/codify has not yet run. Any claim at this stage is provisional and must be labeled as resting on document content read directly, not on coded/verified evidence-layer output.
- **Codified-provisional** — GABRIEL/codify has run, evidence-layer rows exist and are grounded, but the claim is still bounded to one city, one cycle, or a small evidence base. This is the normal, expected state for most claims in this file — "provisional" here does not mean weak, it means honestly scoped.
- **Report-ready** — a claim with enough codified evidence, cross-checked reasoning, and stated limits that it could appear in a PI-facing report today, with its own stated caveats, without further work. Reserve this label; most claims in this corpus are not there yet.
- **Gap claim** — no real claim can yet be made about this municipality (no codified evidence, sometimes no ingested source at all). The only honest claim is about the gap itself: what is missing, why, and what would close it. Do not force a substantive claim onto a gap-claim city.

---

# Massachusetts

Codified evidence layer: 8 MA cities as of this build (Arlington, Boston, Franklin, Georgetown, Seekonk, Somerville, Wayland, Worcester) — the corpus's densest state, and the state offering the widest range of design types (full triads, matched pairs, one strong-but-unmatched source, and one uncodified matched pair).

## Franklin, MA

### Status
**Codified-provisional.**

### Sources
- `ma_franklin_police_2022` (Franklin Police Association, 2022-2025), `ma_franklin_police_sergeants_2022` (Franklin Police Sergeants Union, 2022-2025), `ma_franklin_fire_2022` (IAFF Local 2637, 2022-2025), `ma_franklin_public_works_2022` (AFSCME Local 1298, 2022-2025), `ma_franklin_library_2022` (MLSA Local 4928, 2022-2025), `ma_franklin_other_2022` (AFSCME Local 1298 Custodians, 2022-2025) — all exact-cycle 2022-2025, all in `data/contracts.csv`.
- Evidence locator: `docs/analysis/gabriel_codify_evidence_layer.csv` (`contract_id` = each `obs_id` above); `docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv`; viewer: `docs/analysis/gabriel_codify_excerpt_browser_latest.html`.

### Municipal Claims

#### Claim 1 — Franklin's safety wage-setting is structured around hazard/line-of-duty rationale and callback/overtime premiums; its non-safety wage-setting is structured around classification and salary-schedule mechanics
**Claim:** In Franklin's 2022-2025 cycle, police and fire wage-relevant language centers on hazard pay, line-of-duty provisions, and overtime/callback administration, while library, public works, and custodial wage-relevant language centers on step/grade placement and salary-schedule appendices, with comparatively little hazard or callback content.

**Evidence:** `ma_franklin_police_2022`: `hazard_risk_stress_or_line_of_duty_rationale` present ("Members are entitled to a hazardous duty pay stipend..."), `premium_pay_differentials` present (Section 12.3, "$20.00 bi-weekly" hazardous duty stipend), `minimum_staffing_or_continuous_coverage` present ("Shift replacement coverage when minimum staffing needs to be met"), multiple `overtime_callback_holdover_mandatory_extra_work` hits (callback minimum-4-hours rule). `ma_franklin_fire_2022`: `hazard_risk_stress_or_line_of_duty_rationale` present (Section 15.8, Line of Duty Death funeral/burial costs), `overtime_callback_holdover_mandatory_extra_work` present (emergency-recall premium pay), `training_certification_credential_premiums` present (education incentive). `ma_franklin_library_2022`, `ma_franklin_public_works_2022`, `ma_franklin_other_2022`: all three show `classification_reclassification_or_grade_structure` present (step tables, salary-schedule appendices), and comparatively thin/absent hazard or callback content (fire and police-sergeants both show `civil_service_or_statutory_employment_channel` and `grievance_or_contract_interpretation_arbitration` present via table-of-contents matches, weaker signal than clause-level hits).

**Evidence locator:** `evidence_id`s beginning `codify_20260710_ma_franklin_*`; `docs/analysis/gabriel_codify_massachusetts_audit_2026-07-09.md` for the original grounding audit.

**Reasoning:** The pattern is consistent with the codebook's own design: hazard/line-of-duty and callback/overtime attributes are the categories most directly tied to the physical and scheduling demands specific to police/fire work, while classification/grade attributes are the categories most directly tied to routine civilian pay administration. Franklin's evidence lands cleanly on that expected split, giving a within-city, same-cycle example of occupational specialization in wage-mechanism language.

**Counterevidence / limits:** Several of the strongest "present" hits (e.g. fire's `civil_service_or_statutory_employment_channel`, police's `other`) are table-of-contents/heading matches rather than substantive clause text — real but thin evidence, not a close reading of full articles. No `interest_arbitration_or_formal_impasse_backstop` evidence in any of the 6 Franklin rows — codify did not find, and this claim does not assert, any formal impasse mechanism here. This is presence-of-mechanism evidence, not a measurement of wage-outcome size.

**What would change our mind:** A full-document (not curated-window) re-codify of the Franklin non-safety rows turning up genuine hazard/callback content, or of the safety rows turning up equally rich classification content, would weaken the claimed occupational split.

**Source needs:** None — fully codified. A repeat Franklin cycle (post-2025) would test whether the pattern holds over time.

**Report hooks:** Good candidate for a "within-city occupational specialization" figure — 6 occupation classes, one city, one cycle, directly comparable attribute-presence bars.

---

## Seekonk, MA

### Status
**Codified-provisional.**

### Sources
- `ma_seekonk_police_2022` (FOP Mass C.O.P. Local #215, 2022-2025), `ma_seekonk_fire_2022` (IAFF Local 1931, 2022-2025), `ma_seekonk_public_works_2023` (AFSCME Local 1701, 2023-2026), `ma_seekonk_library_2023` (MLSA Local 4928, 2023-2026), `ma_seekonk_teacher_2021` (Seekonk Educators Association, 2021-2024) — overlapping-cycle, not exact-cycle, matched design. `ma_seekonk_clerical_admin_2021` is ingested but not codified (17-byte plain extraction, an unresolved scan).
- Evidence locator: `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv`; `docs/analysis/gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv`; `docs/analysis/gabriel_codify_seekonk_wayland_audit_2026-07-10.md`.

### Municipal Claims

#### Claim 1 — Seekonk's safety wage-setting shows a genuine minimum-staffing/coverage mechanism; no comparable coverage constraint appears in its non-safety rows
**Claim:** Seekonk fire's minimum-staffing rule (filling below-minimum shifts with mandatory overtime) is a real, distinct wage-cost driver not mirrored in any of Seekonk's codified non-safety occupation classes.

**Evidence:** `ma_seekonk_fire_2022`: `minimum_staffing_or_continuous_coverage` present — "the Fire Chief shall, for the next proceeding quarter, maintain the minimum staffing requirements for a shift by filling any vacancy, below the minimum, with an overtime shift" (grounded, verified). No `minimum_staffing_or_continuous_coverage` present hit in police, public_works, library, or teacher rows.

**Evidence locator:** `evidence_id` `codify_20260710_ma_seekonk_fire_2022_minimum_staffing_or_continuous_coverage_0`.

**Reasoning:** This is a specific, mechanical link between an occupational coverage requirement and a wage-cost channel (mandatory overtime to backfill a minimum): it shows exactly how a staffing constraint converts into compensation obligation, one of this project's core interpretive interests. Its absence in the four non-safety rows is a real, checked absence (all four were codified, not skipped).

**Counterevidence / limits:** One clause, one occupation class, one city. `ma_seekonk_public_works_2023` does show its own overtime/call-back language (`overtime_callback_holdover_mandatory_extra_work` present, twice) — non-safety is not overtime-free, just not staffing-minimum-driven in the codified text.

**What would change our mind:** A Seekonk DPW or library minimum-staffing clause discovered in a fuller read of the same documents, or a repeat fire cycle showing the minimum-staffing clause dropped, would change this claim's confidence.

**Source needs:** `ma_seekonk_clerical_admin_2021` remains a real gap (unusable scan) — recovering it (OCR, same bounded-recovery method used for Wayland/Arlington) would add a fourth genuine Seekonk non-safety data point.

**Report hooks:** Pairs well with Franklin's hazard/classification split as a second, independent within-MA occupational-specialization example.

#### Claim 2 — Seekonk public_works shows an explicit non-safety wage-restraint/reclassification-linked pay decision
**Claim:** Seekonk's DPW clerical staff had a scheduled wage increase explicitly withheld and replaced with a reclassification-linked adjustment instead — a direct instance of non-safety wages being routed through an administrative classification channel rather than a standard across-the-board increase.

**Evidence:** `ma_seekonk_public_works_2023`: `non_safety_wage_restraint_or_admin_channel` present — "Senior Clerks will forgo the wage increase for Fiscal Year 2024 in light of their reclassification and corresponding wage scale adjustment for said fiscal year" (grounded, verified).

**Evidence locator:** `evidence_id` `codify_20260710_ma_seekonk_public_works_2023_non_safety_wage_restraint_or_admin_channel_0`.

**Reasoning:** This is a concrete, dated example of the "non-safety wages routed through classification/administrative channel instead of open bargaining" pattern this project's codebook was built to detect — not an inference, a directly quoted contractual decision.

**Counterevidence / limits:** Single clause, single job title (Senior Clerks) within one bargaining unit — not evidence about DPW-wide or Seekonk-wide non-safety wage-setting.

**What would change our mind:** Finding the same pattern (a scheduled increase forgone for a reclassification adjustment) recurring across other Seekonk or Franklin non-safety units would strengthen this into a town-level or state-level pattern claim.

**Source needs:** None for this specific claim.

**Report hooks:** A strong, quotable, single-sentence example for a "how non-safety wages actually move" report section.

---

## Wayland, MA

### Status
**Codified-provisional (thin).**

### Sources
- `ma_wayland_other_2021` (AFSCME Local 690 Wayland-1/Wayland-2, 2021-2023, dispatch + Community Health Nurse + clerical + DPW-administrative bargaining unit) — the only codified Wayland row, OCR-recovered in a prior session after the standard extraction returned ~0 usable characters. `ma_wayland_fire_jlmc_2020` (IAFF Local 1978 JLMC arbitration award, 2020-2023) is ingested but was codified in the 2026-07-09 Massachusetts scale-up and returned **zero verified-present attributes** — do not cite it as evidence of anything. `ma_wayland_police_2020`, `ma_wayland_fire_2020`, `ma_wayland_public_works_2020`, `ma_wayland_library_2020` remain ingested, scan-quality, uncodified.
- Evidence locator: `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv`; `wayland_bounded_ocr_recovery_2026-07-10.md`.

### Municipal Claims

#### Claim 1 — Wayland's one codifiable non-safety document shows a broad, mixed-occupation bargaining unit with a wage-grade table and a civil-service statutory reference, but supports no safety/non-safety comparison
**Claim:** `ma_wayland_other_2021` demonstrates real, codifiable non-safety wage-mechanism content (a grade-based wage table for dispatch/nurse/clerical positions, a State Labor Relations Board case citation, union-security dues-deduction language) — but Wayland currently has **no matched safety-side evidence** to compare it against, because the only fire document that was actually codified (the JLMC award) returned nothing.

**Evidence:** `ma_wayland_other_2021`: `classification_reclassification_or_grade_structure` present (Grade G-1 through G-9 wage table), `civil_service_or_statutory_employment_channel` present ("positions declared appropriate by the State Labor Relations Board in Case No. MCR-4207"), `union_security_or_institutional_power` present (exclusive-representative recognition; AFSCME PEOPLE dues deduction), `training_certification_credential_premiums` present (CPR stipend), `overtime_callback_holdover_mandatory_extra_work` present (dispatcher holiday overtime rate).

**Evidence locator:** `evidence_id`s beginning `codify_20260710_ma_wayland_other_2021_*`.

**Reasoning:** This is a genuine, verified non-safety wage-mechanism source — useful on its own for the classification/civil-service side of the corpus's evidence base. But without a substantively codified Wayland safety counterpart, it cannot support a Wayland-specific safety/non-safety comparison claim, only a general non-safety-mechanism data point.

**Counterevidence / limits:** `ma_wayland_fire_jlmc_2020`'s zero-present result is itself informative only in a weak sense — a JLMC arbitration award's content may simply not overlap this codebook's 19 attributes well, not proof the underlying fire employment relationship lacks these mechanisms.

**What would change our mind:** Codifying one of the four remaining uncodified Wayland safety/non-safety rows (police, fire base CBA, public_works, library) — several are scan-quality and would need bounded OCR recovery first, the same method already proven on this row and on Arlington.

**Source needs:** OCR recovery + codify pass on `ma_wayland_police_2020` or `ma_wayland_fire_2020` (both scan-quality) would be the highest-value next step for Wayland specifically.

**Report hooks:** Cite only as a non-safety mechanism example; do not present as a Wayland safety/non-safety comparison in any report until a safety counterpart is codified.

---

## Boston, MA

### Status
**Codified-provisional (thin, one leg only).**

### Sources
- `ma_boston_police_2020` (Boston Police Patrolmen's Association, 2020-2025) — ingested, in the corpus's matched-pair design, but **not itself substantively codified this build** (0 present rows found in the evidence layer for this contract_id as of this ledger). `ma_boston_clerical_admin_2023` (SENA/USW Local 9158, 2023-2027) — codified, overlap-cycle with police.
- Evidence locator: `docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv`; `gabriel_codify_massachusetts_outputs_2026-07-09.csv`.

### Municipal Claims

#### Claim 1 — Boston's codified clerical/administrative union shows a formal, union-initiated grievance-arbitration pathway with real institutional teeth
**Claim:** Boston's SENA/USW Local 9158 clerical contract gives the union, not management, the exclusive right to initiate arbitration of a grievance — a specific institutional-power detail about how non-safety disputes escalate in this city.

**Evidence:** `ma_boston_clerical_admin_2023`: `grievance_or_contract_interpretation_arbitration` present, 4 separate hits, including "The Union shall have the exclusive right to initiate arbitration of a grievance."

**Evidence locator:** `evidence_id`s beginning `codify_20260709_ma_boston_clerical_admin_2023_grievance_or_contract_interpretation_arbitration_*`.

**Reasoning:** This is a genuine institutional-power finding (union-controlled arbitration initiation is not universal) but is scoped to grievance/dispute arbitration, not wage-setting interest arbitration — it speaks to enforcement power, not to how base wages are set.

**Counterevidence / limits:** **Boston's police leg is not meaningfully codified in this evidence layer** — this is the corpus's largest-city gap. No Boston-specific safety/non-safety comparison claim can be made until it is. One of the clerical row's `present` hits (`premium_pay_differentials`) is flagged `viewer_verified=0` (unverified) — excluded from primary support.

**What would change our mind:** A real codify pass on `ma_boston_police_2020` (currently untouched in the evidence layer) would be the single highest-value action for Boston specifically.

**Source needs:** Codify `ma_boston_police_2020` — already ingested, no new sourcing required, comparable in cost to the Worcester/Arlington wave.

**Report hooks:** Do not present Boston as a matched-comparison city in any report until the police leg is codified — currently only a non-safety data point.

---

## Georgetown, MA

### Status
**Codified-provisional (thin, one leg only).**

### Sources
- `ma_georgetown_police_2020` (AFSCME Local 939 Police Command Staff, 2020-2023) — codified. `ma_georgetown_other_2020` (AFSCME Local 939 Custodians, 2020-2023) — ingested, exact-cycle matched pair by design, **not substantively codified in this evidence layer** (0 present rows for this contract_id).
- Evidence locator: `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv`.

### Municipal Claims

#### Claim 1 — Georgetown's police command-staff contract ties a specific dollar benefit to line-of-duty death, alongside ordinary overtime and shift-differential language
**Claim:** Georgetown's police contract contains an explicit, dollar-denominated line-of-duty-death benefit (full accumulated sick-time payout to the estate) layered on top of standard overtime and shift-differential provisions — a direct, quotable hazard-compensation link.

**Evidence:** `ma_georgetown_police_2020`: `hazard_risk_stress_or_line_of_duty_rationale` present and `benefits_total_compensation_or_pension` present (three hits) — "in the event that an employee is killed in the line of duty working for the Town of Georgetown, the estate of the employee shall receive all accumulated sick time." Also `overtime_callback_holdover_mandatory_extra_work` present and `premium_pay_differentials` present (shift differentials, sergeant base-rate premium).

**Evidence locator:** `evidence_id`s beginning `codify_20260709_ma_georgetown_police_2020_*`.

**Reasoning:** This is a small-town, command-staff-specific example of hazard/line-of-duty rationale converting directly into a defined benefit — useful as a contrast point to Georgetown's town size (much smaller than Franklin/Seekonk) showing the same mechanism family recurs even in small jurisdictions.

**Counterevidence / limits:** **No matched non-safety comparison is possible** — the custodians' row exists in `data/contracts.csv` but was not substantively codified. This is a police-only data point for now, despite the design being a genuine matched pair.

**What would change our mind:** Codifying `ma_georgetown_other_2020` (custodians) would let Georgetown support a real, small-town safety/non-safety comparison — cheap (already ingested).

**Source needs:** Codify `ma_georgetown_other_2020`.

**Report hooks:** Useful as a small-town contrast to Franklin, once the custodians' row is codified.

---

## Somerville, MA

### Status
**Codified-provisional (rich single source, unmatched).**

### Sources
- `ma_somerville_police_spsoa_2012` (Somerville Police Superior Officers Association arbitration award, 2012-2018) — the corpus's single richest source (9 verified-present attributes). `ma_somerville_police_spea_2012` (Somerville Police Employees Association arbitration award, 2012-2015) — ingested, not in this evidence layer's present-row set for this build.
- Evidence locator: `docs/analysis/gabriel_codify_pilot_evidence_windows_2026-07-08.csv`; `docs/analysis/gabriel_codify_pilot_audit_2026-07-08.md`.

### Municipal Claims

#### Claim 1 — Somerville's police superior-officers arbitration award is the corpus's clearest example of a formal peer-comparator wage study driving a settlement
**Claim:** The Somerville SPSOA award explicitly rests on a University of Massachusetts Collins Center classification-and-compensation study benchmarked against named peer communities (Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, and others), plus explicit statutory "ability to pay" language and a description of the interest-arbitration process itself as a public-welfare-threat backstop.

**Evidence:** `interest_arbitration_or_formal_impasse_backstop` present — "Interest Arbitration process is utilized when 'there is an exhaustion of the process of collective bargaining which constitutes a potential threat to public welfare.'" `peer_comparator_wage_comparability` present — the Collins Center study, naming specific peer municipalities. `non_safety_wage_restraint_or_admin_channel` present — the same Collins Center study was also used to set **non-union City positions'** pay (i.e., the same comparator-study mechanism spans both this safety row and Somerville's civilian classification system). `budget_capacity_or_fiscal_constraint` present — explicit statutory "ability to pay" criteria. `classification_reclassification_or_grade_structure`, `overtime_callback_holdover_mandatory_extra_work`, `premium_pay_differentials`, `training_certification_credential_premiums` (x2), `grievance_or_contract_interpretation_arbitration` (x2) all also present.

**Evidence locator:** `evidence_id`s beginning `codify_20260708_ma_somerville_police_spsoa_2012_*`; this is the corpus's only verified `peer_comparator_wage_comparability` row, primary support for `CLM-2026-07-12-07`.

**Reasoning:** This single document independently demonstrates three distinct wage-setting mechanisms this project cares about — interest arbitration as impasse backstop, explicit peer-comparator benchmarking, and statutory ability-to-pay constraints — all in one arbitration award, with the comparator study explicitly spanning both the safety bargaining unit and the city's non-union civilian pay structure. That last point is itself a claim-relevant finding: it suggests Somerville's wage-comparison infrastructure (the Collins Center study) is not safety-specific, but a general municipal tool safety bargaining also drew on.

**Counterevidence / limits:** **Somerville is safety-only in this evidence layer — one of the corpus's unmatched safety units.** No non-safety Somerville row is codified, so this cannot yet support a Somerville-specific safety/non-safety *comparison* claim — only a rich safety-side claim. The award is from 2012-2018, more than a decade old relative to the project's most recent MA sources.

**What would change our mind:** A codified Somerville non-safety source (SMEU/SEIU Local 3, per the 2026-07-14 sourcing pass in the "Massachusetts institutional-availability" note below) showing whether the same Collins Center comparator study also shaped non-safety wages there would directly test whether this mechanism is safety-specific or general-municipal.

**Source needs:** A Somerville non-safety CBA — see the dedicated sourcing note below (still the single highest-leverage acquisition target in the corpus).

**Report hooks:** The strongest single-document evidence in the corpus for a peer-comparator figure or vignette; explicitly flag the "spans both safety and non-union civilian pay" detail as report-worthy.

### Sourcing note (2026-07-14, carried forward)
A document-first sourcing pass (city HR pages, union sites, Legistar, and an older IQM2 legislative-document archive) found specific, current, cycle-dated non-safety candidates — SMEU (formerly SMEA) Unit B (DPW/Water & Sewer/Library/Clerk/Parking/Inspectional Services, FY2023-2025) and SEIU Local 3 Custodians (FY2023-2025) — but no locatable agreement text for either. **Not ingested.** Direct outreach to Somerville HR or the unions is the most promising remaining path; further open-web search is unlikely to succeed (already run to its practical limit).

---

## Newton, MA

### Status
**Gap claim.**

### Sources
- `ma_newton_police_2015` (police CBA, 2015-2018; large scanned-photo PDF) — ingested, but **not in this build's codified evidence layer** (never run through GABRIEL/codify).

### Municipal Claims

No claim can be made about Newton's wage-setting mechanisms — this is a genuine gap, not a codified-but-thin result. The only accurate statement is about the gap itself: Newton has one ingested, verbatim-verified safety document (confirmed in a prior session to contain a genuine "ARTICLE XIV NO STRIKE CLAUSE") but zero codified evidence and zero non-safety comparison source. **Do not cite Newton in support of any claim.**

**Source needs:** A Newton non-safety CBA (parallel to the Somerville gap) would be needed before Newton could support even a safety-only claim comparable to Somerville's; codifying the existing police row would be the cheaper first step.

---

## Worcester, MA

### Status
**Codified-provisional (thin by construction).**

### Sources
- `ma_worcester_fire_2017` (IAFF Local 1009, 2017-2020), `ma_worcester_clerical_admin_2017` (NAGE Local 490, 2017-2020), `ma_worcester_public_works_2017` (Teamsters Local 170 DPW Clerks, 2017-2020) — all exact-cycle, all codified 2026-07-14.
- Evidence locator: `docs/analysis/gabriel_codify_worcester_arlington_outputs_2026-07-14.csv`; `docs/analysis/gabriel_codify_worcester_arlington_evidence_windows_2026-07-14.csv`; `docs/analysis/gabriel_codify_worcester_arlington_audit_2026-07-14.md`.

### Municipal Claims

#### Claim 1 — Worcester's three ingested documents are wage/benefits amendment MOAs, not base CBAs, and their thin codify results reflect that document type, not an absence of underlying mechanisms
**Claim:** All three Worcester rows amend a prior base contract not present in this corpus — the fire and clerical MOAs are explicitly "off the record... not binding until approved," and the public_works MOA is titled "DRAFT #1" on its own cover — so `not_found` on recognition/no-strike/interest-arbitration/minimum-staffing across all three documents is a fact about what these specific instruments cover, not evidence those mechanisms are absent from Worcester's underlying labor relationships.

**Evidence:** `ma_worcester_fire_2017` present attributes: `overtime_callback_holdover_mandatory_extra_work`, `benefits_total_compensation_or_pension` (x2), `subcontracting_outsourcing_or_volunteer_substitution` (a civilian Fire Engineer position added without displacing bargaining-unit work), `management_rights_or_service_flexibility` (x2), `civil_service_or_statutory_employment_channel` (x2, both weak — funding-clause and scope-of-work references, not classic civil-service language), `budget_capacity_or_fiscal_constraint` ("subject to funding in accordance with G.L. c. 150E"). `ma_worcester_clerical_admin_2017`: `grievance_or_contract_interpretation_arbitration` present (a new probationary-period article explicitly excluding discipline from grievance/arbitration), `classification_reclassification_or_grade_structure` (x2, wage-step language), `benefits_total_compensation_or_pension`, `other` (a position moved out of the bargaining unit). `ma_worcester_public_works_2017`: `overtime_callback_holdover_mandatory_extra_work` (a location-specific overtime rate), `classification_reclassification_or_grade_structure` (x3), `budget_capacity_or_fiscal_constraint` (ratification/appropriation clause).

**Evidence locator:** `evidence_id`s beginning `codify_20260714_ma_worcester_*`.

**Reasoning:** The document-type explanation is directly verifiable from the documents' own preambles (quoted above), not inferred — this is a case where a thin evidence-layer result has a specific, checkable, non-data-quality cause. It is included here explicitly so a future session does not mistake Worcester's thinness for an extraction failure or a genuine absence and either re-run codify pointlessly or draw a false negative conclusion about Worcester's labor relations.

**Counterevidence / limits:** The `subcontracting_outsourcing_or_volunteer_substitution`/civilianization finding (a new civilian Fire Engineer position, explicitly not displacing bargaining-unit work) is a real, useful data point on its own even though the surrounding document is thin — worth citing individually.

**What would change our mind:** Locating and ingesting Worcester's actual base contracts (the documents these three MOAs amend) would let a genuine Worcester triad claim be made; this session did not attempt that (out of scope for a bounded, cheap codify wave).

**Source needs:** The base 2014-2017 (or earlier) Worcester fire/clerical/DPW contracts, if locatable — would substantially upgrade Worcester from breadth-only to a real evidentiary triad.

**Report hooks:** Cite Worcester only for the specific civilianization finding and as a "breadth of cities" data point for `CLM-2026-07-12-03`; do not present it as a rich matched-triad result the way Arlington or the Ohio cities are.

---

## Arlington, MA

### Status
**Codified-provisional — the corpus's richest genuine matched pair.**

### Sources
- `ma_arlington_fire_2021` (IAFF Local 1297, FY2022-2024) and `ma_arlington_public_works_2021` (AFSCME Local 680, 2021-2024) — exact-cycle matched pair, both codified 2026-07-14. `ma_arlington_public_works_2021`'s source PDF (35 pages) originally extracted to only 5,620 usable characters via the standard pipeline; recovered via a bounded, single-pass OCR pass this session (105,305 characters). `ma_arlington_public_works_2015`/`_2018` (earlier, non-overlapping DPW cycles) remain ingested, not codified (excluded from this wave — no matched-pair value for the current fire cycle).
- Evidence locator: `docs/analysis/gabriel_codify_worcester_arlington_outputs_2026-07-14.csv`; `docs/analysis/gabriel_codify_worcester_arlington_evidence_windows_2026-07-14.csv`; `docs/analysis/gabriel_codify_worcester_arlington_audit_2026-07-14.md`.

### Municipal Claims

#### Claim 1 — Arlington's fire and public_works units access the SAME statutory impasse mechanism, not separate safety-specific and non-safety-specific channels
**Claim:** In Arlington's 2021-2024 cycle, both the fire and public_works units cite Chapter 1078 of the Acts of 1973 as their impasse-resolution backstop for unresolved successor-contract negotiations — a shared, town-wide statutory mechanism, not a safety-only interest-arbitration channel paired with a weaker or absent non-safety channel.

**Evidence:** `ma_arlington_fire_2021`: `interest_arbitration_or_formal_impasse_backstop` present — "provided that if agreement is not reached by January 2024 for the next year fiscal year, both or either party may utilize impasse procedures provided by law" (Article XXVII, Duration). `ma_arlington_public_works_2021`: `interest_arbitration_or_formal_impasse_backstop` present — "If agreement cannot be reached by January 15, 2024, then both or either parties may utilize the impasse procedure (mediation and fact-finding) set forth in section 9 of Chapter 1078 of the Acts of 1973" (Article XXX, Duration). Both rows also show `no_strike_or_work_stoppage_constraint` present (fire: "There shail be no strikes during the life of this Agreement"; public_works: "No employee covered by this agreement shall engage in, induce or encourage any strike, work stoppage, slow down...").

**Evidence locator:** `evidence_id`s `codify_20260714_ma_arlington_fire_2021_interest_arbitration_or_formal_impasse_backstop_0`, `codify_20260714_ma_arlington_public_works_2021_interest_arbitration_or_formal_impasse_backstop_0`, and the corresponding `no_strike_or_work_stoppage_constraint_0` IDs for both contracts.

**Reasoning:** Because both clauses cite the same numbered Massachusetts statute (Chapter 1078 of the Acts of 1973), this is not two independent findings that happen to look similar — it is direct textual evidence that Arlington's town government negotiates successor contracts for at least these two very different occupation classes under one shared statutory impasse framework. This is the clearest single-municipality evidence in the corpus that a state/local institutional design, not an occupation-specific one, can be the proximate driver of whether a bargaining unit has a formal impasse backstop at all.

**Counterevidence / limits:** This is one town, one cycle, two occupation classes (not a full triad — no Arlington police row is codified). It says nothing about whether the *outcomes* reached under this shared mechanism differ by occupation (codify measures mechanism presence, not bargaining outcomes or wage levels). It directly complicates, but does not disprove, the Ohio-triad pattern (`CLM-2026-07-12-01`) — Ohio's asymmetry could still be a real, ORC-4117-specific institutional fact even if Massachusetts's Ch. 1078 works differently.

**What would change our mind:** An Arlington police contract, if codified, showing this SAME shared-statute pattern would make this a full Arlington triad finding; showing a *different* impasse statute or no impasse language at all for police would complicate this claim further and suggest the symmetry is DPW/fire-specific rather than town-wide.

**Source needs:** An Arlington police CBA (not currently in `data/contracts.csv` at all — a genuine sourcing gap, distinct from the fire/DPW pair already codified).

**Report hooks:** This is the single most report-ready "complicates the Ohio narrative" finding in the current MA evidence base — see the National Claims section below for how this bears on cross-state generalization.

#### Claim 2 — Arlington public_works independently demonstrates the interest-vs-grievance arbitration distinction, in a non-safety document
**Claim:** `ma_arlington_public_works_2021` contains, in one document, a Duration-article successor-contract impasse clause coded separately from an Article VII civil-service/disciplinary grievance-arbitration clause — the first non-safety exemplar in the corpus of the methodological distinction this project relies on between interest/impasse arbitration and ordinary grievance arbitration.

**Evidence:** `grievance_or_contract_interpretation_arbitration` present (x2) — "A grievance which is, or upon proper appeal would be, within the jurisdiction of the Civil Service Commission... shall not be subject to the grievance and arbitration procedure of Article VII unless by mutual agreement" and "A grievance involving the suspension, dismissal, removal or termination of an employee under civil service law and rules may in any instance be subject to binding arbitration..." — both coded separately from the Duration article's `interest_arbitration_or_formal_impasse_backstop` finding in Claim 1 above.

**Evidence locator:** `evidence_id`s `codify_20260714_ma_arlington_public_works_2021_grievance_or_contract_interpretation_arbitration_0` and `_1`.

**Reasoning:** Prior corpus exemplars of this distinction (San Antonio police, Toledo police, Houston fire, Somerville police) were all safety occupations. This is the first time codify has correctly separated the two arbitration types within a single non-safety document, evidence that the distinction is a general coding capability, not an artifact of safety-specific document structure.

**Counterevidence / limits:** This is a coding/methodology claim (does codify correctly distinguish the two arbitration types), not a substantive wage-gap claim — see `CLM-2026-07-12-06`'s own stated scope.

**What would change our mind:** A future non-safety document where codify conflates the two arbitration types would weaken confidence in this general-capability claim.

**Source needs:** None specific to this claim.

**Report hooks:** Use as a methodology-guardrail citation alongside San Antonio, not as a substantive finding on its own.

#### Claim 3 — A likely-generalizable deterministic-extractor gap was found via this codify wave, now resolved (see Task 4 below)
**Claim:** `data/contracts.csv`'s deterministic `no_strike_clause_flag` for `ma_arlington_fire_2021` was a false negative — the GABRIEL/codify wave found genuine no-strike language the regex-based extractor missed because it only matched singular "no strike," never plural "no strikes." See "No-strike extractor fix" below for the resolution and its corpus-wide effect.

**Evidence locator:** `wage_mechanism_evidence_checklist.md` item 19.

---

# Ohio

Codified evidence layer: 4 OH cities (Cincinnati, Cleveland, Columbus, Toledo) — the corpus's cleanest matched-triad design, all four sharing Ohio's ORC Chapter 4117 public-sector bargaining framework. This is the state where `CLM-2026-07-12-01` is anchored and where the project's strongest report-ready cross-occupation claim currently lives.

## Columbus, OH

### Status
**Codified-provisional.**

### Sources
- `oh_columbus_police_2023` (FOP Capital City Lodge No. 9, 2023-2026), `oh_columbus_fire_2023` (IAFF Local 67, 2023-2026), `oh_columbus_other_2024` (AFSCME Ohio Council 8 Local 1632, 2024-2027) — overlap-cycle matched triad.
- Evidence locator: `evidence_id`s beginning `codify_20260709_oh_columbus_*`; `docs/analysis/wage_mechanism_evidence_checklist.md` items 15/16/18 for the data-integrity history on this city.

### Municipal Claims

#### Claim 1 — Columbus's safety units access ORC Chapter 4117's statutory impasse procedure by name; its non-safety union relies on classification/civil-service committee structures instead
**Claim:** Both Columbus police and fire cite Ohio Revised Code Chapter 4117's dispute-settlement procedure (fact-finding, conciliation, or arbitration) directly in their own contract text for successor-agreement negotiations, while the codified non-safety union (AFSCME Local 1632) shows classification/civil-service-committee language and no comparable interest-arbitration clause.

**Evidence:** `oh_columbus_fire_2023`: `interest_arbitration_or_formal_impasse_backstop` present, genuine, independently verified this session against fresh source-PDF text — "Upon request by the City, the parties shall jointly request from the Federal Mediation and Conciliation Service (FMCS) a list of seven (7) arbitrators..." `oh_columbus_police_2023`: `interest_arbitration_or_formal_impasse_backstop` present — "agree that the 2026 negotiations for a contract to succeed this Contract shall be conducted in accordance with the dispute settlement procedure set forth in Ohio Revised Code Chapter 4117," also `civil_service_or_statutory_employment_channel` present quoting the same statute. `oh_columbus_other_2024`: `civil_service_or_statutory_employment_channel` present ("Section 7.5. Civil Service Committee"), `classification_reclassification_or_grade_structure` present (x2), no `interest_arbitration_or_formal_impasse_backstop` present hit.

**Evidence locator:** `evidence_id`s `codify_20260709_oh_columbus_fire_2023_interest_arbitration_or_formal_impasse_backstop_0`, `codify_20260709_oh_columbus_police_2023_interest_arbitration_or_formal_impasse_backstop_0`.

**Reasoning:** This is the anchor case for `CLM-2026-07-12-01`'s asymmetric pattern, and it is now on especially firm footing: both interest-arbitration excerpts were independently re-verified in the 2026-07-14 Columbus/GABRIEL-evidence-layer contamination check (confirmed genuine, grounded, structurally unrelated to a prior session's fabricated `data/contracts.csv` text field), so this claim rests on doubly-checked evidence.

**Counterevidence / limits:** `not_found` on `interest_arbitration_or_formal_impasse_backstop` for the non-safety row is a curated-window absence, not a full-document proof of absence — the non-safety CBA may still contain ORC-4117 impasse language outside the codified window. Also, a prior session found the fabricated `data/contracts.csv` `arbitration_clause_text` field for both police and fire had unknown provenance (corrected, not fabricated by GABRIEL) — flagging that the underlying documents' provenance chain is not perfectly clean even though the codify layer itself is.

**What would change our mind:** A broader-window or full-document codify of `oh_columbus_other_2024` turning up genuine ORC-4117 language would weaken this specific claim (though `CLM-2026-07-12-01` would still hold across the other three Ohio cities).

**Source needs:** Full-document codify of the Columbus non-safety row.

**Report hooks:** The cleanest single-city ORC-4117 asymmetry example — good candidate for a report figure pairing safety/non-safety `interest_arbitration_or_formal_impasse_backstop` presence.

---

## Cleveland, OH

### Status
**Codified-provisional.**

### Sources
- `oh_cleveland_police_2025` (CPPA, 2025-2028), `oh_cleveland_fire_2025` (Local 93, 2025-2028), `oh_cleveland_other_2022` (AFSCME Local 100, 2022-2025) — exploratory-adjacent, not exact/overlap-cycle by `ingest/audit_coverage.py`'s own classification.
- Evidence locator: `evidence_id`s beginning `codify_20260709_oh_cleveland_*`.

### Municipal Claims

#### Claim 1 — Cleveland police's interest-arbitration reference is genuine and explicit; Cleveland's non-safety union shows management-rights language broad enough to include subcontracting/privatization authority
**Claim:** Cleveland police's contract explicitly references "the negotiations and/or interest arbitration which resulted in this Contract," while Cleveland's non-safety union's management-rights article gives the City authority "to privatize or subcontract" as an enumerated management right, alongside classification and shift-differential language — a genuinely different institutional flavor from Columbus/Toledo's more classification-only non-safety pattern.

**Evidence:** `oh_cleveland_police_2025`: `interest_arbitration_or_formal_impasse_backstop` present — "during the negotiations and/or interest arbitration which resulted in this Contract each had the unlimited right..." `oh_cleveland_other_2022`: `management_rights_or_service_flexibility` present (x3), including "to determine work methods; to privatize or subcontract; to determine the size and duties of the work force," and `subcontracting_outsourcing_or_volunteer_substitution` present independently.

**Evidence locator:** `evidence_id`s `codify_20260709_oh_cleveland_police_2025_interest_arbitration_or_formal_impasse_backstop_0`; `codify_20260709_oh_cleveland_other_2022_management_rights_or_service_flexibility_2`.

**Reasoning:** The privatization/subcontracting management right is a real, distinct wage-relevant institutional feature for Cleveland's non-safety workforce — a channel by which the City could substitute out unionized non-safety labor entirely, a different kind of "wage restraint" than Columbus's classification-committee approach. Combined with the confirmed police interest-arbitration language, Cleveland supports the same broad Ohio asymmetric pattern as Columbus, with its own institutional texture.

**Counterevidence / limits:** Cleveland fire has a previously flagged, unverified `interest_arbitration_or_formal_impasse_backstop` hit (a table-of-contents/legacy-code artifact, `viewer_verified=0`) — excluded from primary support per standing project practice; do not cite Cleveland fire's interest-arbitration status as established. Cleveland's design status is exploratory-adjacent, not a clean matched pair/triad by cycle.

**What would change our mind:** A cleaner Cleveland fire codify pass (full document, not the flagged window) resolving whether fire genuinely has interest-arbitration language would complete Cleveland's triad-level claim.

**Source needs:** Re-codify Cleveland fire with a corrected window.

**Report hooks:** Use the police/non-safety pairing; do not cite Cleveland fire's interest-arbitration status until re-verified.

---

## Cincinnati, OH

### Status
**Codified-provisional (weakest of the four OH cities).**

### Sources
- `oh_cincinnati_police_2024` (FOP Queen City Lodge No. 69, non-supervisors, 2024-2027), `oh_cincinnati_police_sup_2024` (same lodge, supervisors, 2024-2027), `oh_cincinnati_fire_2023` (IAFF Local 48, 2023-2026), `oh_cincinnati_other_2025` (CODE, 2025-2028).
- Evidence locator: `evidence_id`s beginning `codify_20260709_oh_cincinnati_*` and `codify_20260710_oh_cincinnati_*`.

### Municipal Claims

#### Claim 1 — Cincinnati's evidence is genuine but thin; only the non-supervisor police row and the non-safety row show real content
**Claim:** Cincinnati police (non-supervisors) shows management rights, overtime, and union-security content consistent with the broader Ohio pattern; Cincinnati's non-safety union shows a grievance-mediation process. Cincinnati fire and the police-supervisor unit returned **zero verified-present attributes** — a real evidentiary gap, not evidence of absence.

**Evidence:** `oh_cincinnati_police_2024`: `civil_service_or_statutory_employment_channel` present, `management_rights_or_service_flexibility` present (both from the same Article II Management Rights language), `overtime_callback_holdover_mandatory_extra_work` present, `union_security_or_institutional_power` present (contract-period/continuation language). `oh_cincinnati_other_2025`: `grievance_or_contract_interpretation_arbitration` present — "When a grievance is moved to mediation the Human Resources Director or designee(s)... shall meet with the Union."

**Evidence locator:** `evidence_id`s `codify_20260709_oh_cincinnati_police_2024_management_rights_or_service_flexibility_0`, `codify_20260710_oh_cincinnati_other_2025_grievance_or_contract_interpretation_arbitration_0`.

**Reasoning:** Cincinnati is the weakest-evidenced of the four Ohio triad cities — this is stated plainly in `CLM-2026-07-12-01`'s own `key_limitations` field and repeated here at the municipal level so a future report doesn't inadvertently treat Cincinnati as equally strong to Columbus/Toledo.

**Counterevidence / limits:** Two of Cincinnati's four rows (fire, police-supervisors) have zero verified-present rows — codify's curated window may simply have missed real content, not proof these documents lack mechanism language. A genuine new true positive was found in the 2026-07-13 extractor-fix session: `oh_cincinnati_fire_2023`'s `me_too_clause_flag` (a verbatim "'Me-too' with FOP on wages..." clause) — found by the deterministic layer, not yet reflected in the GABRIEL evidence layer, since that clause type isn't one of the 19 codebook attributes.

**What would change our mind:** A broader-window re-codify of Cincinnati fire and the police-supervisor unit is the single highest-value re-codify target among the four Ohio cities.

**Source needs:** Broader-window or full-document codify for Cincinnati fire and police-supervisors.

**Report hooks:** Cite Cincinnati cautiously; note its evidentiary thinness explicitly if used in any Ohio-wide figure.

---

## Toledo, OH

### Status
**Codified-provisional.**

### Sources
- `oh_toledo_police_2024` (TPPA Local 10, 2024-2026), `oh_toledo_fire_2024` (Local 92, 2024-2026), `oh_toledo_other_2024` (Local 2058, 2024-2027).
- Evidence locator: `evidence_id`s beginning `codify_20260710_oh_toledo_*`.

### Municipal Claims

#### Claim 1 — Toledo's safety units show minimum-staffing and interest-arbitration language; its non-safety union shows the same no-strike/no-lockout language as safety, without an interest-arbitration counterpart
**Claim:** Toledo fire cites a specific minimum-staffing ordinance section (2125.58) directly tied to recall/overtime pay; Toledo police has a genuine, previously-missed interest-arbitration clause ("If no agreement is reached, the matter shall be subject to an interest arbitration"); Toledo's non-safety union shares the SAME statutory-sounding no-strike/no-lockout language as fire, but has no codified interest-arbitration counterpart.

**Evidence:** `oh_toledo_fire_2024`: `minimum_staffing_or_continuous_coverage` present and `overtime_callback_holdover_mandatory_extra_work` present, both from "Members who are recalled for an emergency or to meet the minimum staffing language of 2125.58 shall be paid at the overtime rate..." `oh_toledo_police_2024`: `interest_arbitration_or_formal_impasse_backstop` present — a genuine positive found and added during the 2026-07-13 extractor-fix session (previously missed by the deterministic layer; independently confirmed by GABRIEL/codify here). `oh_toledo_other_2024`: `no_strike_or_work_stoppage_constraint` present, 3 hits, nearly identical framing to fire's own no-strike language ("essential to the public health, safety and welfare").

**Evidence locator:** `evidence_id`s `codify_20260710_oh_toledo_police_2024_interest_arbitration_or_formal_impasse_backstop_0`; `codify_20260710_oh_toledo_fire_2024_minimum_staffing_or_continuous_coverage_0`.

**Reasoning:** Toledo is a genuine within-city three-way comparison: fire's minimum-staffing/overtime linkage, police's confirmed interest-arbitration channel, and non-safety's shared no-strike framing but absent interest-arbitration — supporting the Ohio-wide asymmetric pattern on the interest-arbitration dimension specifically, while showing no-strike constraints are NOT occupation-specific in Toledo (a partial parallel to Arlington's finding, worth flagging).

**Counterevidence / limits:** Toledo's non-safety row showing shared no-strike language (like Arlington's shared impasse language) is itself a data point cutting against treating "no-strike constraints are safety-specific" as a general Ohio-wide fact — worth cross-referencing with the National Claims section.

**What would change our mind:** A broader-window codify of Toledo's non-safety row specifically checking for ORC-4117 interest-arbitration language would test whether the asymmetry holds on that dimension too, or whether Toledo's non-safety union also has an impasse backstop simply not yet found.

**Source needs:** None blocking; a full-document non-safety re-codify would sharpen this claim.

**Report hooks:** Good candidate for a three-way (safety/safety/non-safety) within-city comparison figure; flag the shared no-strike finding as a cross-reference to the Arlington/National Claims discussion.

---

# Texas

Codified evidence layer: 3 TX cities (Austin, Houston, San Antonio). Texas is the clearest example in the corpus of **institutionally uneven** safety wage-setting — a genuine matched triad in one city (Houston) and safety-only/safety-adjacent designs elsewhere, which is itself the claim, not a data gap to be explained away.

## Houston, TX

### Status
**Codified-provisional — Texas's only genuine matched triad.**

### Sources
- `tx_houston_police_2024` (HPOU, 2024-2025), `tx_houston_fire_2024` (IAFF Local 341 arbitration award, 2024-2029), `tx_houston_other_2024` (HOPE/AFSCME Local 123, 2024-2027).
- Evidence locator: `evidence_id`s beginning `codify_20260709_tx_houston_*`.

### Municipal Claims

#### Claim 1 — Houston's non-safety union has its own genuine impasse/mediation channel, directly complicating a Texas-wide "impasse backstops are safety-only" narrative
**Claim:** Houston's non-safety union (HOPE) has an explicit, named mediation process through the Federal Mediation and Conciliation Service for unresolved disputes — a real institutional channel functionally comparable to fire's civil-service/statutory framework, even though Houston's non-safety employees are not covered by the Chapter 174 Fire and Police Employee Relations Act that gives police/fire their formal bargaining rights.

**Evidence:** `tx_houston_other_2024`: `interest_arbitration_or_formal_impasse_backstop` present — "HOPE and the City shall select a mediator through a process of mutual agreement from the Federal Mediation and Conciliation Service (FMCS). B. Should HOPE elect to proceed..." `tx_houston_fire_2024`: `civil_service_or_statutory_employment_channel` present, explicitly naming "Chapter 174... the Fire and Police Employee Relations Act" and the "Civil Service Commission."

**Evidence locator:** `evidence_id` `codify_20260709_tx_houston_other_2024_interest_arbitration_or_formal_impasse_backstop_0`.

**Reasoning:** This is the first, and until Arlington the only, non-safety matched-pair evidence in the corpus showing a genuine formal dispute-resolution channel — establishing that Texas's institutional unevenness is not simply "safety has formal channels, non-safety has none," but something more specific: safety has a *statutory, Chapter-174-backed* channel with civil-service infrastructure, while non-safety (at least at Houston, the one TX city where it's codified) has a *negotiated, FMCS-mediated* channel instead. Both are real institutional mechanisms; they differ in legal footing, not in existence.

**Counterevidence / limits:** This is one non-safety union in one Texas city — cannot be generalized to Austin/San Antonio non-safety (neither has a codified general-municipal non-safety row; Austin's is EMS, safety-adjacent).

**What would change our mind:** A codified San Antonio or Austin general-municipal non-safety source either replicating or failing to replicate an FMCS-style channel would directly test whether this is a Houston-specific finding or a broader Texas pattern.

**Source needs:** See `CLM-2026-07-12-08`/San Antonio non-safety sourcing note below — still the corpus's most urgently-needed Texas source.

**Report hooks:** Central to `CLM-2026-07-12-02`; pair with the Arlington MA finding in the National Claims section as two independent examples of non-safety impasse-channel evidence outside Ohio.

---

## Austin, TX

### Status
**Codified-provisional (exploratory design — EMS leg is safety-adjacent).**

### Sources
- `tx_austin_police_2024` (Austin Police Association, 2024-2029), `tx_austin_fire_2023` (Austin Firefighters Local 975, 2023-2025), `tx_austin_nursehealth_2023` (Austin EMS Association, 2023-2027).
- Evidence locator: `evidence_id`s beginning `codify_20260709_tx_austin_*`.

### Municipal Claims

#### Claim 1 — All three Austin units, including EMS, sit under the same Chapter 142/143 civil-service framework and show genuine interest-arbitration/statutory-channel language — but EMS is not a clean non-safety comparator
**Claim:** Austin fire's agreement is explicitly effective "as of the date of the award in the interest arbitration proceeding that implements this Agreement" (a genuine, unambiguous interest-arbitration citation); Austin EMS explicitly invokes both Chapter 142 and Chapter 143 of the Texas Local Government Code and describes itself as bound by a "meet and confer statute" and a "statutorily imposed no strike or work slowdown" provision — meaning Austin's EMS union sits under the SAME broad civil-service statutory umbrella as police/fire, not a separate general-municipal non-safety framework.

**Evidence:** `tx_austin_fire_2023`: `interest_arbitration_or_formal_impasse_backstop` present (explicit "interest arbitration proceeding" reference), `hazard_risk_stress_or_line_of_duty_rationale` present, `minimum_staffing_or_continuous_coverage` present. `tx_austin_nursehealth_2023`: `civil_service_or_statutory_employment_channel` present (x3, citing both Ch. 142 and Ch. 143), `no_strike_or_work_stoppage_constraint` present ("statutorily imposed no strike or work slowdown"), `grievance_or_contract_interpretation_arbitration` present (x2).

**Evidence locator:** `evidence_id`s `codify_20260709_tx_austin_fire_2023_interest_arbitration_or_formal_impasse_backstop_0`; `codify_20260709_tx_austin_nursehealth_2023_civil_service_or_statutory_employment_channel_0/_1`.

**Reasoning:** Austin EMS's statutory citations make clear it is legally closer to public-safety civil-service employment than to an ordinary general-municipal bargaining unit — reinforcing, rather than undermining, the source inventory's own labeling of it as "safety-adjacent." This is useful negative evidence: it shows precisely *why* Austin cannot yet support a genuine safety/non-safety comparison, rather than just asserting the limitation.

**Counterevidence / limits:** Austin police shows `management_rights_or_service_flexibility` and `civil_service_or_statutory_employment_channel` present but no confirmed `interest_arbitration_or_formal_impasse_backstop` hit in this evidence layer — an asymmetry within Austin's own safety rows worth noting, not just a safety/non-safety asymmetry.

**What would change our mind:** A genuine Austin general-municipal (clerical, public works) non-safety source, if codified, would let Austin support the same kind of comparison Houston and Arlington now can.

**Source needs:** An Austin general-municipal non-safety CBA — a real, still-open gap distinct from Austin's own EMS document.

**Report hooks:** Use to explain, not just assert, why Austin's design is "safety-adjacent" rather than a clean triad.

---

## San Antonio, TX

### Status
**Codified-provisional — deliberately safety-only.**

### Sources
- `tx_san_antonio_police_2022` (SAPOA, 2022-2026), `tx_san_antonio_fire_2024` (Local 624, 2024-2027).
- Evidence locator: `evidence_id`s beginning `codify_20260710_tx_san_antonio_*`.

### Municipal Claims

#### Claim 1 — San Antonio police is the corpus's clearest single-document demonstration that interest arbitration and grievance arbitration are legally and textually distinct mechanisms
**Claim:** The same San Antonio police contract contains a Chapter 174-defined impasse procedure (Section 4, "Impasse Procedure") coded separately from an ordinary grievance-arbitration clause (also "Section 4. Arbitration," a different article) — codify correctly separated the two under different attributes within the same document.

**Evidence:** `tx_san_antonio_police_2022`: `interest_arbitration_or_formal_impasse_backstop` present — "In the event the City and the Association reach an impasse in collective bargaining negotiations, as such impasse is defined in Chapter 174..." `grievance_or_contract_interpretation_arbitration` present (x2) — "If a grievance is submitted to arbitration, within fourteen (14) calendar days, the City and the Association shall agree upon an arbitrator... The arbitrator shall not have the power to add to, amend, modify, or subtract from the provisions of this Agreement..."

**Evidence locator:** `evidence_id`s `codify_20260710_tx_san_antonio_police_2022_interest_arbitration_or_formal_impasse_backstop_0`, `codify_20260710_tx_san_antonio_police_2022_grievance_or_contract_interpretation_arbitration_0/_1`.

**Reasoning:** This is the founding example for `CLM-2026-07-12-06`'s methodological distinction, and remains the clearest because both clauses are explicit, statute-referencing, and unambiguous — a genuine within-document contrast, not an inference across two different documents.

**Counterevidence / limits:** San Antonio is **deliberately unmatched** (safety-only, added for institutional-contrast value per the original source inventory) — do not present as a data gap needing correction; also has a documented false negative on peer-comparator language (codify missed genuine comparator wording a manual audit later found — `CLM-2026-07-12-07` limitation).

**What would change our mind:** N/A for this specific methodology claim — it is well-established. A San Antonio non-safety source would open a different, separate comparison claim (see below).

**Source needs:** A San Antonio general-municipal non-safety CBA remains the corpus's single highest-priority non-safety gap, `CLM-2026-07-12-08`, explicitly named `urgent`.

### Sourcing note (2026-07-14, carried forward)
A 2026-07-14 sourcing pass found that San Antonio's ~6,000 civilian employees (AFSCME Local 2021) are represented through a non-binding advisory Employee Management Committee, not a collective bargaining agreement — consistent with Texas Gov't Code Ch. 617's general public-sector bargaining prohibition and San Antonio never extending an equivalent Ch. 174-style statutory channel to civilians (only police/fire have that; general wage-setting instead runs through council-adopted Municipal Civil Service Rules and a council pay plan, which have no bargaining-unit counterparty and are not schema-eligible as a CBA row). **This reframes San Antonio's non-safety gap from "not yet found" to "plausibly does not exist for this employer"** — see the National Claims section for how this bears on Texas's broader institutional pattern.

---

# Pennsylvania

Codified evidence layer: 1 PA city (Philadelphia), codified 2026-07-14. Pittsburgh, Allentown, Erie, and Reading remain candidate-only or gap-claim status — see their sections below.

## Philadelphia, PA

### Status
**Codified-provisional — codified 2026-07-14.**

### Sources
- `pa_philadelphia_police_2025` (FOP Lodge 5 Act 111 interest-arbitration award, 2025-2027), `pa_philadelphia_other_2025` (AFSCME DC47 Locals 2186/2187 term sheet, 2025-2028) — overlap-cycle matched pair. `pa_philadelphia_fire_2017` (IAFF Local 22 Act 111 interest-arbitration award, 2017-2020), `pa_philadelphia_other_2017` (AFSCME DC47 Local 2186 MOA, 2017-2020) — exact-cycle matched pair. `pa_philadelphia_other_2021` (AFSCME DC33, 2021-2024) ingested but not codified this wave (no matched-pair value for either current cycle).
- Evidence locator: `docs/analysis/gabriel_codify_philadelphia_trenton_outputs_2026-07-14.csv`; `docs/analysis/gabriel_codify_philadelphia_trenton_evidence_windows_2026-07-14.csv`; `docs/analysis/gabriel_codify_philadelphia_trenton_audit_2026-07-14.md`.

### Municipal Claims

#### Claim 1 — Philadelphia's safety wage-setting is explicitly PICA-budget-constrained; a wage increase is directly, contractually tied to a civilianization/operational-flexibility trade
**Claim:** Philadelphia police's Act 111 arbitration panel explicitly grounds its award in the Pennsylvania Intergovernmental Cooperation Authority (PICA) Act's statutory ability-to-pay and balanced-budget requirements, and grants a 1.5%+1.5% wage-schedule increase specifically **in exchange for** expanded civilianization/operational-flexibility provisions — a direct, quotable, contractually-explicit link between a non-wage institutional concession and a wage increase.

**Evidence:** `pa_philadelphia_police_2025`: `budget_capacity_or_fiscal_constraint` present (×2) — "In light of the PICA Act's requirement that the Panel make findings, supported by substantial evidence in the record, that the City has the ability to pay the cost of the Award..." and "1. The City is statutorily required to maintain a balanced budget." `management_rights_or_service_flexibility` + `subcontracting_outsourcing_or_volunteer_substitution` both present from the same clause — "8. Civilianization: a. In recognition of the operational flexibility included in this section of the Award, the City shall increase the wage schedule by 1.5% effective January 1, 2026, and by 1.5% effective January 1, 2027." `staffing_shortage_recruitment_retention` present (a retention-incentive directive to the parties).

**Evidence locator:** `evidence_id`s beginning `codify_20260714_pa_philadelphia_police_2025_*`.

**Reasoning:** This is one of the clearest, most explicit wage-for-concession trades in the entire corpus — most sources merely co-locate wage and management-rights language; this document states the causal link directly ("in recognition of the operational flexibility... the City shall increase the wage schedule"). It is strong evidence that at least part of Philadelphia's safety wage growth is a direct payment for institutional flexibility, not solely a hazard/market-driven increase.

**Counterevidence / limits:** This is one arbitration award, one city; the civilianization-for-wages trade may be Philadelphia/Act-111-specific rather than a general public-safety pattern. The `peer_comparator_wage_comparability` hit in this same document (PICA's tax-revenue-projection accuracy being "the most accurate of the peer cities they studied") is about fiscal-projection accuracy, not wage-level comparison — flagged in the evidence window notes as a possible over-coding; do not cite this as genuine wage-comparator evidence without re-reading the full excerpt.

**What would change our mind:** A second Philadelphia award cycle (pre- or post-2025-2027) showing the same civilianization-for-wages structure would confirm this as a recurring Philadelphia mechanism rather than a one-time award feature.

**Source needs:** An earlier or later Philadelphia police Act 111 award, if available, for a repeat-cycle comparison.

**Report hooks:** The clearest single-document "wage increase explicitly priced against a specific concession" example in the corpus — strong candidate for a report vignette.

#### Claim 2 — Philadelphia's codified non-safety union shows rich grievance-arbitration machinery but no interest-arbitration language — the corpus's cleanest non-Ohio replication of the Ohio-style asymmetric pattern
**Claim:** The AFSCME DC47 term sheet (Philadelphia's overlap-cycle non-safety comparator to police) shows a detailed, multi-step grievance-to-mediation-to-arbitration pathway for out-of-class/temporary-promotion disputes, but **zero** `interest_arbitration_or_formal_impasse_backstop` finding anywhere in the codified window — while Philadelphia police's Act 111 award is itself a product of interest arbitration. This is the cleanest non-Ohio example yet of the SAME asymmetric safety/non-safety pattern `CLM-2026-07-12-01` describes for Ohio.

**Evidence:** `pa_philadelphia_other_2025`: `grievance_or_contract_interpretation_arbitration` present ×5 — a full OOC/temporary-promotion dispute pathway ("Should a grievance concerning OOC/TP Disputes remain unresolved after Step IV of the grievance procedure, the parties may agree to submit the grievance to mediation..."; "Grievances not subject to arbitration and denied at Step IV... may be submitted to the Pennsylvania Bureau of Mediation"). No `interest_arbitration_or_formal_impasse_backstop` present hit for this contract.

**Evidence locator:** `evidence_id`s beginning `codify_20260714_pa_philadelphia_other_2025_grievance_or_contract_interpretation_arbitration_*`.

**Reasoning:** Pennsylvania's institutional design (Act 111 binding arbitration for police/fire specifically; Act 195/PERA for general municipal employees, which does not include binding interest arbitration) predicts exactly this asymmetry, and the codified text confirms it directly — this is a genuine, working replication of the Ohio pattern under an entirely different state statutory framework, the first such clean replication found this project. See National Claim 4 for how this changes the cross-state picture (previously 2-for-2 symmetric after Houston and Arlington; Philadelphia is now the first clean non-Ohio asymmetric counterexample to *that* emerging pattern).

**Counterevidence / limits:** A curated-window `not_found` result cannot prove full-document absence — the DC47 term sheet is one of a 5-document compiled packet (see `extractor_fix_and_philadelphia_fire_gap_2026-07-13.md`), and this window drew only from the main term sheet. `pa_philadelphia_other_2021` (DC33) was not codified this wave and could show a different pattern.

**What would change our mind:** Codifying `pa_philadelphia_other_2021` or a broader window of the DC47 packet finding genuine interest-arbitration language would weaken this specific claim.

**Source needs:** A broader-window codify of the full DC47 packet; codify of `pa_philadelphia_other_2021`.

**Report hooks:** Directly cite alongside the Ohio finding as a second-state confirmation of the safety/non-safety impasse asymmetry — see National Claim 4.

#### Claim 3 — Philadelphia fire's evidence was recovered from a model-response parsing anomaly, not a normal pipeline run — cite with the appropriate provenance caveat
**Claim:** `pa_philadelphia_fire_2017` shows the same Act 111/PICA pattern as police (interest arbitration, balanced-budget/ability-to-pay findings, a Civil Service Regulation 32 / Heart and Lung Act injury-benefit reference) — but this evidence was recovered manually after a duplicate-key JSON bug in the raw model response caused the pipeline's initial output to show a false all-`not_found` result for this contract.

**Evidence:** `interest_arbitration_or_formal_impasse_backstop` present (×2), `civil_service_or_statutory_employment_channel` present, `budget_capacity_or_fiscal_constraint` present (×3), `other` present. All independently re-verified as genuine verbatim substrings of the source PDF before use.

**Evidence locator:** `evidence_id`s beginning `codify_20260714_pa_philadelphia_fire_2017_*` — **all flagged `viewer_verified=0`** in the evidence layer per this project's standard irregular-provenance convention (see `docs/analysis/gabriel_codify_philadelphia_trenton_audit_2026-07-14.md` for the full technical account). The underlying text is independently confirmed genuine; the flag reflects irregular recovery process, not doubt about the content.

**Reasoning:** Including this claim (rather than silently treating Philadelphia fire as a zero-evidence row) avoids under-stating Philadelphia's actual evidence base, while the flag ensures a future session or report author knows to treat this specific row's provenance as non-standard.

**Counterevidence / limits:** This row's evidence, while independently verified, did not go through the pipeline's normal automated grounding path — treat with slightly more scrutiny than an ordinary `viewer_verified=1` row, even though the underlying text is genuine.

**What would change our mind:** N/A — this is a provenance/process note, not a substantive claim subject to revision by new evidence.

**Source needs:** None.

**Report hooks:** If citing Philadelphia fire's interest-arbitration/budget content in a report, footnote the recovery process or re-verify independently first.

---

## Pittsburgh, PA

### Status
**Gap claim — candidate-only, no sources ingested.**

No claim can be made. FOP Fort Pitt Lodge 1 (found only on Scribd, an unofficial host — not promotable per project sourcing standards); IAFF Local 1 (named, no document found across two search rounds); AFSCME Local 2719 (a confirmed, recently-signed CBA with a located union contracts page — the only leg with real document-level provenance). **Source needs:** an official-domain replacement for the police document; any document at all for fire.

## Allentown, PA

### Status
**Gap claim — candidate-only, no sources ingested.**

No claim can be made. FOP Lodge 10 (named, no document); IAFF Local 302 (named, contract-documents page possibly access-gated); SEIU Local 668 (corrected union identity for the non-safety leg). No leg has reached document level after two search rounds — the weakest large PA city scanned. **Source needs:** any document for any leg.

## Erie, PA

### Status
**Gap claim — candidate-only, no sources ingested.**

No claim can be made. FOP Lodge 7/Haas Memorial Lodge (2001 case-law reference only); IAFF Local 293 (named, no document); AFSCME Local 2206 (confirmed ratified 2026-03-04 contract, document not located). A jurisdiction false positive (Erie County, NY) must continue to be excluded from any future search. **Source needs:** any document for any leg; lowest priority of the five PA cities scanned.

## Reading, PA

### Status
**Gap claim — candidate-only, no sources ingested.**

No claim can be made. A "Reading Public Library CBA" candidate is confirmed false (the actual document is a construction/electrical-contractor bid contract). AFSCME Local 2763 (a confirmed dated agreement, document not located); FOP Lodge #9 and IAFF Local 1803 (named, no documents). The police leg has zero document or award evidence, blocking any matched-design claim regardless of non-safety strength. **Source needs:** any document for the police leg is the binding constraint.

---

# New Jersey

Codified evidence layer: 1 NJ city (Trenton), codified 2026-07-14 — the corpus's only genuine matched triad outside Ohio. Newark remains design-ready (partial), and Jersey City, Paterson, and Elizabeth remain candidate-only or gap-claim status — see their sections below.

## Trenton, NJ

### Status
**Codified-provisional — codified 2026-07-14. The corpus's only genuine matched TRIAD outside Ohio.**

### Sources
- `nj_trenton_other_2019` (AFSCME Local 2281 Supervisory Employees, 2019-2023), `nj_trenton_police_2019` (PBA Local 11, 2019-2024), `nj_trenton_fire_2021` (FMBA Local 206, 2021-2026) — all three pairwise cycle-overlap for 2021-2023.
- Evidence locator: `docs/analysis/gabriel_codify_philadelphia_trenton_outputs_2026-07-14.csv`; `docs/analysis/gabriel_codify_philadelphia_trenton_evidence_windows_2026-07-14.csv`; `docs/analysis/gabriel_codify_philadelphia_trenton_audit_2026-07-14.md`.

### Municipal Claims

#### Claim 1 — Trenton's police and fire CBAs explicitly EXCLUDE wages from their own internal arbitration article, deferring wage disputes to an external, statute-based process invisible in this window — a structurally distinct pattern from both Ohio and Arlington
**Claim:** Both Trenton police (Section 17.07) and Trenton fire (Section 14.06) contain nearly identical clauses stating that fiscal matters — wages, hours, benefits — are **not** subject to interest arbitration under the CBA's own internal grievance/arbitration article; disputes over those matters are implicitly routed elsewhere (consistent with New Jersey's external Police and Fire Public Interest Arbitration Reform Act, which this corpus's CBA text does not itself contain). This is a real, recurring, cross-occupation Trenton institutional pattern — not a one-document artifact.

**Evidence:** `nj_trenton_police_2019`: `interest_arbitration_or_formal_impasse_backstop` present — "Article XVI and Article XVII, relating to grievance procedure and arbitration, shall apply only to the settlement of disputes, differences or grievances between the Employer and any employee... Nothing herein shall require either party to submit fiscal matters such as wages, hours or benefits to interest arbitration." `nj_trenton_fire_2021`: `interest_arbitration_or_formal_impasse_backstop` present — "Fiscal matters as wages, hours, and benefits are not subject to interest arbitration. Only the President or the Grievance Committee can authorize a grievance moving to binding arbitration."

**Evidence locator:** `evidence_id`s `codify_20260714_nj_trenton_police_2019_interest_arbitration_or_formal_impasse_backstop_0`, `codify_20260714_nj_trenton_fire_2021_interest_arbitration_or_formal_impasse_backstop_0`. Cross-reference `wage_mechanism_evidence_checklist.md` item 13, which documents the deterministic-extraction layer independently finding and correctly labeling this same fire-row clause as an "inversion" in a prior session.

**Reasoning:** **Do not read `interest_arbitration_or_formal_impasse_backstop=present` here as "Trenton grants an internal interest-arbitration channel for wages" — it is the opposite.** The correct institutional reading: Trenton's internal CBA text for both safety occupations affirmatively carves wage disputes OUT of its own arbitration machinery, which is consistent with (though does not, on its own, prove) wage disputes being handled through NJ's external statutory interest-arbitration process instead — a process this corpus does not directly observe in CBA text the way it observes Ohio's ORC-4117 citations. This is a third, structurally distinct pattern from both Ohio (internal statutory citation) and Arlington (internal, town-wide shared-statute citation): **external deferral with an internal exclusion clause as the only textual trace.**

**Counterevidence / limits:** GABRIEL's `present` coding is technically defensible (the clause IS about interest arbitration), but is easy to misread without the full excerpt — exactly the kind of case `CLM-2026-07-12-06`'s reviewer-audit recommendation exists to catch at scale. This corpus cannot directly observe NJ's external statutory process's actual content from CBA text alone.

**What would change our mind:** Locating and codifying an actual NJ Police and Fire Public Interest Arbitration Reform Act award or proceeding record for Trenton (parallel to how Philadelphia's Act 111 awards ARE the arbitration proceeding's own output) would let this project observe the external process directly instead of inferring its existence from an exclusion clause.

**Source needs:** A Trenton (or other NJ city's) interest-arbitration award or PERC proceeding record, if publicly available — would substantially strengthen this claim from inference to direct observation.

**Report hooks:** Use as a worked example of why `interest_arbitration_or_formal_impasse_backstop=present` must be read at the excerpt level, not the flag level — pairs directly with `CLM-2026-07-12-06`'s existing San Antonio/Arlington guardrail examples.

#### Claim 2 — Trenton's non-safety union shows the same no-strike commitment as its safety counterparts but no interest-arbitration language of any kind, genuinely asymmetric on this dimension
**Claim:** Trenton's AFSCME Local 2281 (non-safety) CBA contains a direct, clause-stated no-strike commitment referencing the same NJ Chapter 123 statutory framework as police/fire's own no-strike articles, but shows **zero** interest-arbitration or impasse-procedure language anywhere in the codified window — genuinely asymmetric, unlike Arlington's shared-statute pattern.

**Evidence:** `nj_trenton_other_2019`: `no_strike_or_work_stoppage_constraint` present — "[the] rights of public employees to strike[, per] Chapter 123... The Union will not authorize or sanction any strike or job action during the term of this [Agreement]." No `interest_arbitration_or_formal_impasse_backstop` present hit for this contract; a full keyword scan of the extracted text confirms no interest-arbitration or impasse-procedure language exists anywhere in the document.

**Evidence locator:** `evidence_id` `codify_20260714_nj_trenton_other_2019_no_strike_or_work_stoppage_constraint_0`.

**Reasoning:** This is a genuinely useful contrast case: Trenton's no-strike commitment IS symmetric across safety and non-safety (echoing Arlington's finding that no-strike constraints are not occupation-specific), while its interest-arbitration exposure is NOT symmetric — non-safety simply has no impasse-backstop language, consistent with (though for a different textual reason than) Ohio's and Philadelphia's asymmetric pattern.

**Counterevidence / limits:** A `not_found` result cannot prove full-document absence, though the keyword scan here was thorough (checked "strike," "impasse," "interest arbitration" directly, not just codify's window).

**What would change our mind:** Genuine impasse language found in a broader-window or full-document re-codify.

**Source needs:** None blocking.

**Report hooks:** Directly relevant to National Claim 4 — Trenton's non-safety leg is asymmetric in outcome, even though its safety legs' textual mechanism (exclusion + external deferral) differs from Ohio's (internal citation).

---

## Newark, NJ

### Status
**Design-ready (partial — one genuine matched pair, one gap).**

### Sources
- `nj_newark_other_2020` (Teamsters Local 97, municipal attorneys, 2020-2023), `nj_newark_police_2018` (FOP Lodge 12, 2018-2023 — overlaps the non-safety row for 2020-2023, a real matched pair), `nj_newark_fire_2013` (Newark Firefighters Union, 2013-2015 — does not overlap; design-level context only).
- Evidence locator: none — not codified.

### Municipal Claims

No content claim yet — this is design-ready, not codified, and was not in scope for this session's Philadelphia/Trenton wave. The only claim is a design-level one: Newark police genuinely cycle-overlaps the non-safety row (2020-2023), a real matched pair despite fire being unmatched. **Source needs:** a more current Newark fire document (IAFF Local 1860, 2017-2023 term, identified by name/cycle via PERC-index browsing across two prior sessions but never located).

## Jersey City, NJ

### Status
**Gap claim — candidate-only, structurally strong but out-of-window.**

No claim can be made. Four direct PERC-index PDFs found (Jersey City PSOA 2009-2012; IAFF Local 1066 2009-2015; JC Public Employees Local 245 MOA 2015; JC Public Employees Local 246 2015) — structurally the strongest matched-triad candidate SHAPE found in either PA or NJ (all three roles, two distinct non-safety unions), but every document is dated ~2009-2015, mostly outside the project's 2014-2024 observation window. **Source needs:** current-cycle (2020s) successors to all four documents.

## Paterson, NJ

### Status
**Gap claim — candidate-only, non-safety leg disqualifying.**

No claim can be made. PBA Local 1 (named via a 2021 PERC interim-relief decision); FMBA Local 2/Tactical Fire Officers Association (named via a 2012 PERC decision, including a live staffing-level grievance — plausibly relevant to minimum-staffing hypotheses if ever located). Non-safety is a hard, repeated gap across two search rounds — the only Paterson-domain PERC documents found are for the school district, a different employer entirely, which disqualifies the matched-triad design regardless of safety-side documentation.

## Elizabeth, NJ

### Status
**Gap claim — weakest city in either PA or NJ.**

No claim can be made. Only a generic PERC synopsis reference for the Elizabeth Superior Officers Association, no named local for fire or non-safety. Deprioritized relative to the other four NJ cities.

---

# National Claims

**These claims are held to a stricter standard than the municipal claims above: they require evidence across multiple municipalities and, ideally, multiple states. A hypothesis is not a national claim — see `docs/analysis/hypothesis_tracker_2026-07-12.csv` for hypotheses (H1-H8), which are broader, less-bounded propositions this project is actively testing. A national claim below only exists when the corpus's current codified evidence, taken together across cities, actually supports it at the stated confidence level.**

## National Claim 1 — Ohio-specific: safety/non-safety impasse-mechanism asymmetry (Report-ready, Ohio-scoped only)

**Claim:** Within the four currently-coded Ohio matched-triad cities (Columbus, Cleveland, Cincinnati, Toledo), safety rows more often show formal impasse or interest-arbitration backstop language citing Ohio Revised Code Chapter 4117, while matched non-safety rows are better evidenced through classification, wage-grade, or grievance-administration channels.

**Municipal evidence base:** Columbus (Claim 1 above — the cleanest example, doubly-verified), Cleveland (Claim 1 above — police confirmed, fire unresolved), Toledo (Claim 1 above — police confirmed, non-safety shares no-strike but not impasse language), Cincinnati (thin, weakest of the four).

**Evidence pattern:** 4/4 Ohio cities show a safety-side interest-arbitration or formal-impasse citation in at least one safety row; 0/4 show a confirmed non-safety-side interest-arbitration citation in the codified window (Cincinnati and Toledo's non-safety rows were checked and returned `not_found`; Columbus and Cleveland's non-safety rows show classification/management-rights content instead).

**Reasoning:** This is this project's most consistent, cross-city, single-state pattern — the same statute (ORC 4117), cited in the same way, producing the same occupational split, four times independently. This is exactly the kind of repeated, checkable pattern that earns `report_ready=yes` status.

**Counterevidence / limits:** This is `CLM-2026-07-12-01`, explicitly Ohio-scoped — it is a claim about Ohio, under Ohio's specific statutory framework, and should never be read as a claim about safety/non-safety wage-setting nationally. `not_found` results are curated-window absences, not full-document proofs.

**What would change our mind:** A codified Ohio non-safety row later showing genuine ORC-4117 interest-arbitration language would weaken this claim within Ohio itself.

**Source needs:** Full-document (not curated-window) re-codify of the four OH non-safety rows would be the most direct test.

**Report hooks:** `CLM-2026-07-12-01` in `claim_register_2026-07-12.csv`, `report_ready=yes`. Safe to cite as an Ohio-specific finding in any report.

---

## National Claim 2 — Massachusetts-specific: at least one MA town shares a single statutory impasse channel across safety and non-safety (Codified-provisional, single-city)

**Claim:** In Arlington, Massachusetts, both a safety unit (fire) and a non-safety unit (public_works) access the SAME numbered state statute (Chapter 1078 of the Acts of 1973) as their impasse-resolution backstop for unresolved successor-contract negotiations — evidence that at least one Massachusetts municipality's impasse infrastructure is town-wide, not occupation-specific.

**Municipal evidence base:** Arlington, MA (Claim 1 above) — the only currently-codified MA city with matched safety and non-safety rows both showing interest-arbitration/impasse-backstop evidence.

**Evidence pattern:** 1/1 currently-tested MA matched pair shows this symmetric pattern. Franklin and Seekonk (MA's other matched-design cities) show ZERO interest-arbitration evidence in EITHER their safety or non-safety codified rows — a different pattern still (no impasse backstop found on either side, not an asymmetric one).

**Reasoning:** This is explicitly a single-city finding, presented as such. It matters because it is a genuine counterexample to treating "safety occupations uniquely have interest-arbitration backstops" as a fact about Massachusetts, let alone the nation — but it is one town, one cycle, and does not by itself establish a Massachusetts-wide pattern (Franklin/Seekonk's null result on this same attribute shows MA itself is not uniform).

**Counterevidence / limits:** Only 1 of 3 currently-matched MA cities shows this pattern; the other 2 show a different (null-impasse) pattern. This is explicitly NOT strong enough evidence to be a "Massachusetts pattern" claim yet — it is an Arlington-specific finding with cross-state implications flagged in National Claim 4 below.

**What would change our mind:** A second MA city (e.g. Boston, once its police leg is codified, or Georgetown once its custodians' row is codified) showing the same symmetric pattern would upgrade this from a single-city finding toward a real Massachusetts-level claim. A second MA city showing the Franklin/Seekonk null pattern instead would suggest Arlington, not Franklin/Seekonk, is the outlier.

**Source needs:** Codify Boston police, Georgetown custodians, or a second Arlington-adjacent MA town with a genuine matched pair.

**Report hooks:** Cite carefully as "one Massachusetts town" evidence, explicitly not a state-wide claim; directly relevant to the Ohio-generalizability discussion in National Claim 4.

---

## National Claim 3 — Texas-specific: institutionally uneven safety wage-setting, with non-safety substituting statutory/civil-service channels for collective bargaining where it exists at all (Report-ready as a design/source-structure claim, Texas-scoped)

**Claim:** Texas evidence is consistent with institutionally uneven safety wage-setting: a genuine matched triad exists only in Houston; Austin's third leg is safety-adjacent (EMS, under the same Ch. 142/143 civil-service framework as police/fire); San Antonio has no non-safety leg at all, and the 2026-07-14 sourcing pass found a probable institutional reason why — Texas Gov't Code Ch. 617 generally prohibits public-sector collective bargaining, with police/fire carved out locally via Ch. 174, and San Antonio has not extended an equivalent statutory channel to civilians.

**Municipal evidence base:** Houston (Claim 1 above), Austin (Claim 1 above), San Antonio (Claim 1 + sourcing note above).

**Evidence pattern:** 1/3 TX cities (Houston) has a genuine non-safety comparator with its own real impasse channel (FMCS mediation); 1/3 (Austin) has only a safety-adjacent comparator; 1/3 (San Antonio) has no comparator and a documented institutional reason to expect none exists for this employer.

**Reasoning:** This is a claim about *source structure and institutional design*, not about substantive wage-effect sizes — explicitly bounded that way in `CLM-2026-07-12-02`'s own text. It is report-ready at that scope because the pattern (civil-service/statutory channels standing in for collective bargaining outside the Ch. 174 carve-out) is now directly evidenced, not merely inferred from search failure.

**Counterevidence / limits:** Houston's own non-safety union DOES have a real impasse channel — so "Texas non-safety lacks formal channels" would be an overstatement; the more precise claim is about channel TYPE (statutory Ch. 174 vs. negotiated FMCS mediation vs., in San Antonio's case, no negotiated channel at all).

**What would change our mind:** A San Antonio or Austin general-municipal non-safety CBA, if found, would directly test whether Houston's pattern generalizes within Texas or is itself the outlier.

**Source needs:** San Antonio general-municipal non-safety CBA remains `urgent` per `CLM-2026-07-12-08`, though now a lower-confidence target given the institutional finding above.

**Report hooks:** `CLM-2026-07-12-02`, `report_ready=yes` as a design/source claim. Pair with National Claim 5 (Houston's FMCS-mediation finding) for a cross-state comparison.

---

## National Claim 4 — Cross-state (provisional, genuinely mixed): whether non-safety units share their safety counterpart's impasse-backstop mechanism is state/institution-specific, not a national pattern in either direction

**Claim (provisional — the evidence is now mixed, not one-directional):** The Ohio-style asymmetric pattern (`CLM-2026-07-12-01` — safety carries interest-arbitration/impasse-backstop language, non-safety does not) does NOT hold as a national default, but neither does its opposite. Across the 4 non-Ohio matched designs now tested, the result is a genuine 2-2 split: Houston TX and Arlington MA show a matched non-safety unit sharing a real impasse channel with its safety counterpart (symmetric); Philadelphia PA and Trenton NJ show the non-safety unit with NO comparable interest-arbitration finding, matching Ohio's asymmetric outcome — though Trenton reaches that outcome through a structurally different textual mechanism (an internal exclusion-and-external-deferral clause, not a simple internal absence).

**Municipal evidence base:** Houston, TX (Texas section Claim 1); Arlington, MA (Arlington section Claim 1); Philadelphia, PA (Philadelphia section Claim 2); Trenton, NJ (Trenton section Claims 1-2). Plus the anchor: 4 Ohio cities (`CLM-2026-07-12-01`).

**Evidence pattern:** 2 of 4 non-Ohio matched designs symmetric (Houston, Arlington); 2 of 4 asymmetric, matching Ohio's outcome (Philadelphia cleanly, Trenton via a different mechanism). No clean state/regional boundary explains the split on its own — Massachusetts (Arlington) is symmetric while a different Massachusetts-adjacent legal tradition (Trenton, NJ, sharing a Northeastern statutory-arbitration-for-safety heritage with PA) is asymmetric; Texas (Houston) is symmetric while Pennsylvania (Philadelphia) is cleanly asymmetric under a broadly similar two-track statutory design (Act 111 for safety only) to Ohio's.

**Reasoning:** The evidence does not support either "Ohio is the national default" or "Ohio is the outlier" as a clean characterization. What the four non-Ohio cases DO share is that each state's specific statutory architecture for safety-sector interest arbitration predicts its own outcome reasonably well when examined individually (Massachusetts's Ch. 1078 is genuinely town-wide/occupation-neutral in Arlington; Texas's Houston has a real negotiated non-safety impasse channel via FMCS; Pennsylvania's Act 111 is genuinely safety-exclusive, and its non-safety Act 195/PERA framework genuinely lacks binding interest arbitration; New Jersey's Police and Fire Public Interest Arbitration Reform Act is genuinely safety-exclusive by name) — the pattern is best explained institution-by-institution, not by a single cross-state rule in either direction.

**Counterevidence / limits:** **This claim explicitly walks back the earlier, more provisional 2-for-2-symmetric framing this ledger carried after the Worcester/Arlington wave alone.** That was correctly labeled provisional at the time; this update is exactly the kind of claim revision the project's own interpretive standard calls for as new evidence arrives, not a failure of the earlier framing. Sample size remains genuinely small (4 non-Ohio cities, mostly single arbitrary matched-pair/triad selections per state) — do not treat any single state's result as dispositive for that state, let alone nationally. Trenton's asymmetric result rests on an exclusion-clause reading that requires excerpt-level care to interpret correctly (see Trenton Claim 1).

**What would change our mind:** A fifth non-Ohio state, or a second city within an already-tested state (e.g., a second PA or NJ city, or a second MA/TX city beyond Arlington/Houston), would help determine whether the 2-2 split reflects genuine state-level institutional variation (the current best reading) or is still too small a sample to characterize confidently.

**Source needs:** A second Pennsylvania or New Jersey city (Pittsburgh, Newark, or Jersey City, if sources can be located per their gap-claim status above) would be the most direct next test, since it would either confirm PA/NJ as a genuine "asymmetric" bloc alongside Ohio or reveal within-state variation the way Massachusetts already shows (Arlington symmetric; Franklin/Seekonk showing neither pattern, since they have no codified interest-arbitration evidence at all on either side).

**Report hooks:** This is now the corpus's clearest example of genuine, evidence-driven uncertainty on a cross-state question — report it as exactly that (a real, current 2-2 split with a plausible institution-specific explanation for each case) rather than resolving it in either direction. Good candidate for a report section explicitly modeling how this project revises claims as evidence accumulates.

---

## National Claim 5 — Cross-state (Report-ready, methodological): the interest-vs-grievance arbitration distinction is a general coding capability, not an artifact of any one document, state, or occupation

**Claim:** GABRIEL/codify reliably distinguishes interest/formal-impasse arbitration from ordinary grievance/contract-interpretation arbitration within a single document, across multiple states and, now, across both safety and non-safety occupations.

**Municipal evidence base:** San Antonio TX police (original exemplar), Toledo OH police, Houston TX fire, Somerville MA police, and now Arlington MA public_works (the first non-safety exemplar).

**Evidence pattern:** 5 independent documents across 3 states and both occupation categories, each showing the two attributes correctly separated within one document.

**Reasoning:** This is a coding-reliability claim, not a substantive wage claim — but it is exactly the kind of claim that needs to be established and stated plainly before any report can safely use `interest_arbitration_or_formal_impasse_backstop` as a meaningful cross-city variable at all. Its growing cross-state, cross-occupation evidence base is why `CLM-2026-07-12-06` carries `evidence_strength=strong`.

**Counterevidence / limits:** This is a coding/method claim; a future document where codify conflates the two arbitration types would weaken it, and the corpus has not yet checked every present `interest_arbitration_or_formal_impasse_backstop`/`grievance_or_contract_interpretation_arbitration` pair for this kind of error at scale (a reviewer audit of all interest-arbitration positives remains an open item per `CLM-2026-07-12-06`'s own `additional_sources_needed`).

**What would change our mind:** A documented conflation case would immediately weaken this.

**Source needs:** The reviewer audit noted above.

**Report hooks:** `CLM-2026-07-12-06`, `report_ready=yes`. Use as a standing methodological guardrail in any report that relies on the interest-arbitration attribute.

---

# Cross-cutting synthesis and source needs

## Source needs (cross-cutting, from this build)

1. A Somerville MA non-safety CBA (highest-leverage single acquisition in the corpus, unchanged from prior builds) — SMEU Unit B and SEIU Local 3 Custodians are the named targets; direct outreach to Somerville HR or the unions is the most likely next path.
2. A San Antonio TX general-municipal non-safety CBA — lower-confidence given the institutional finding above, but still `urgent` per `CLM-2026-07-12-08` if pursued.
3. A Boston MA fire codify pass (already ingested — cheapest remaining MA gap) and a Georgetown MA custodians codify pass (also already ingested).
4. An Arlington MA police CBA — not currently in the corpus at all; would complete Arlington's triad and directly extend National Claim 2.
5. Newark NJ's current-cycle IAFF Local 1860 fire CBA (2017-2023 term, identified but never located across three sessions).
6. Current-cycle (2020s) successors to Jersey City's four dated (2009-2015) PERC documents.
7. A reviewer audit of all `interest_arbitration_or_formal_impasse_backstop` positives corpus-wide, to test National Claim 5 at scale — now higher-priority given Trenton's exclusion-clause finding (see Trenton Claim 1).
8. A second Pennsylvania or New Jersey city (Pittsburgh, Newark, or Jersey City) would be the most direct next test of National Claim 4's genuinely-mixed 2-2 split.
9. A Trenton (or other NJ city's) actual interest-arbitration award/PERC proceeding record, to directly observe NJ's external statutory process rather than infer it from an exclusion clause.

## What would change this ledger

- A second PA or NJ city's codify result (see source need 8 above) is now the direct next test of National Claim 4's 2-2 split.
- Confirming (or disproving) whether National Claim 2's Arlington pattern recurs in a second MA city would materially change how confidently National Claim 4 can be stated.
- A Boston police or Georgetown custodians codify pass (both cheap — already ingested) would let two more MA cities support real matched comparisons.
- **Philadelphia/Trenton codify pass (done 2026-07-14):** 7 live calls, 39 present on first pass (35 grounded cleanly, 4 correctly auto-flagged for boundary leakage); one new failure mode found and resolved (a duplicate-key JSON response for `pa_philadelphia_fire_2017` silently overwrote genuine findings with an empty duplicate — manually recovered, independently re-verified, and flagged per this project's standard irregular-provenance convention rather than silently promoted). National Claim 4 was substantially revised from "2-for-2 symmetric, provisional" to "genuinely mixed 2-2 split, best explained state-by-state" — see that section for the full account. This is exactly the kind of claim revision this ledger's own interpretive standard calls for.

---

## Changelog

- **2026-07-14 (initial build)** — Covering all 19 cities currently in `data/contracts.csv` post-commit `9c1cb2c`.
- **2026-07-14 (rename + Columbus check + sourcing pass)** — Renamed to permanent path. Resolved the Columbus/GABRIEL-evidence-layer contamination question (no contamination). Somerville MA and San Antonio TX non-safety sourcing pass (no ingestion; San Antonio institutional finding).
- **2026-07-14 (Worcester/Arlington codify wave)** — Codified Worcester and Arlington MA (5 calls, 49/49 grounded). Arlington surfaced the impasse-symmetry complication later formalized as National Claim 2/4 in this build.
- **2026-07-14 (interpretive-standard rebuild)** — Full restructure per explicit instruction: added the interpretive standard and claim-maturity vocabulary at the top of this file; rewrote every covered municipality section into the Claim/Evidence/Evidence-locator/Reasoning/Counterevidence/What-would-change-our-mind/Source-needs/Report-hooks structure; added the National Claims section (5 claims, explicitly held to a stricter cross-municipality standard than municipal claims); corrected the file's own prior citycount inaccuracies in the process. Philadelphia and Trenton sections written at design-ready status pending this session's Task 4 (no-strike extractor fix) and Task 5 (conditional Philadelphia/Trenton codify wave).
- **2026-07-14 (Philadelphia/Trenton codify wave, Task 5)** — Codified Philadelphia PA (police + fire + 2 non-safety legs) and Trenton NJ (full matched triad), 7 live calls, 39 present on first pass. Found and resolved a new failure mode (duplicate-key JSON response silently dropping genuine findings for `pa_philadelphia_fire_2017`) via manual, independently-verified recovery, flagged per standard convention. Philadelphia and Trenton sections rewritten with real codified claims. **National Claim 4 substantially revised**: from a provisional "2-for-2 symmetric" framing (Houston, Arlington) to a genuinely mixed 2-2 split (Houston/Arlington symmetric; Philadelphia/Trenton asymmetric, Trenton via a structurally distinct exclusion-clause mechanism) — best explained by state-specific institutional design, not a single national rule. Updated `claim_register_2026-07-12.csv` (CLM-06, new PA/NJ exemplars including the Trenton exclusion-clause guardrail case) and `hypothesis_tracker_2026-07-12.csv` (H1/H2/H7 notes) accordingly — no support-level or status field inflated. Total codified cities: 17 (8 MA + 4 OH + 3 TX + 1 PA + 1 NJ), verified directly from `gabriel_codify_evidence_layer.csv`.
