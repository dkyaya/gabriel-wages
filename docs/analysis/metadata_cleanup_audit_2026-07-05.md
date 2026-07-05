# Metadata Cleanup Audit — 2026-07-05

**Type:** dated audit memo, one-time review. Companion machine-readable table: `metadata_cleanup_proposed_edits_2026-07-05.csv`.

## 1. Purpose and scope

This memo is an **audit-first review**, not a cleanup. It inspects the metadata-cleanup issues already tracked in `wage_mechanism_evidence_checklist.md` §11 and in recent occupation-specific corpus-scan memos, verifies each one directly against `data/contracts.csv` and (where useful) the underlying corpus source documents, and proposes concrete, row-level edits for later approval.

**No production metadata or corpus files were edited in this session.** `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, and `inbox/` were read only. No GABRIEL run, model/API call, Harvard proxy call, OEWS/BLS download, or ingestion occurred.

This memo does not make causal claims about why police/fire wages rise faster than other municipal occupations. It is exclusively about the reliability of the metadata that any future causal analysis or GABRIEL run would depend on.

## 2. Audit method

**Files inspected in full this session:** `AGENTS.md` (not present in repo — see §7), `PROGRESS.md`, `docs/analysis/chatgpt_handoff_latest.md`, `docs/analysis/wage_mechanism_evidence_checklist.md`, `docs/schema.md`, `scripts/validate.py`, `data/contracts.csv`, `data/city_coverage.csv`, `docs/analysis/non_safety_dpw_existing_corpus_scan_2026-07-04.md`, `docs/analysis/non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md`.

**Files confirmed present and referenced (content already digested via the full-length summaries embedded in `PROGRESS.md` and `chatgpt_handoff_latest.md`, which themselves quote extensively from each memo):** `docs/analysis/public_sector_impasse_arbitration_state_law_citation_audit_2026-07-05.md` and its companion CSV, `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md`, `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv`, `docs/analysis/ma_dpw_bargaining_impasse_context_2026-07-04.md`, `docs/analysis/ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`, `docs/analysis/non_safety_teacher_wage_mechanism_refinement_2026-07-04.md`, `docs/analysis/ma_teacher_bargaining_school_finance_institutional_context_2026-07-04.md`, `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md`.

**Primary verification performed this session (read-only):**
- Parsed `data/contracts.csv` with Python's `csv.DictReader` to inspect exact field-by-field values for every row with `interest_arbitration_flag=1`, every row with `comparability_clause_flag=1`, all `clerical_admin` rows, all `public_works` rows, and the single `teacher` row. This is the primary evidentiary basis for most findings below — it does not rely on any memo's paraphrase.
- Ran `pdftotext` (already the project's standard extraction tool) against `corpus/ma_seekonk/ma_seekonk_educators_association_2021_2024.pdf`, `corpus/ma_worcester/worcester_local1009_fire_cba_2017-2020.pdf`, `corpus/ma_worcester/worcester_local490_clerical_cba_2017-2020.pdf`, and `corpus/ma_worcester/worcester_local170_dpw_cba_2017-2020.pdf`, then `grep`-searched the extracted text for terms relevant to the tracked issues (paraprofessional/teacher-aide language; successor/incorporation-by-reference language; school-committee references). Output was written only to a session-local scratch directory, never back into `corpus/` or `data/contracts.csv`.
- Attempted `pdftotext` on `corpus/ma_seekonk/ma_seekonk_admin_secretaries_afscme_local_1701_2021_2024.pdf`; it produced no extractable text (confirmed image-only scan, consistent with its `ocr_messy` flag). Rather than re-run OCR, this memo relies on the prior session's already-completed, read-only OCR finding (documented in `non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md` and corroborated by this row's own `total_comp_note` field, which is legible without OCR and independently states the school-committee affiliation).
- Ran `python scripts/validate.py` and `python ingest/audit_coverage.py` (read-only checks; see §8 results below).

## 3. Summary of findings

| issue_id | issue | affected_rows_or_files | severity | verification_status | recommended_later_action | production_edit_needed |
| --- | --- | --- | --- | --- | --- | --- |
| MC01 | Arlington `public_works` `comparability_clause_flag=1` captures workers'-comp/health-plan "comparable" language, not peer-wage comparability | `ma_arlington_public_works_2015`, `ma_arlington_public_works_2018` | medium | **CONFIRMED** (direct CSV read) | Add clarifying `comparability_referent` value; decide flag-scope question at the schema level before touching the boolean | notes-only now; flag-value change needs a schema decision first |
| MC02 | Boston `clerical_admin` row: three-field misalignment (`total_comp_note`, `longevity_detail`, `binding_arbitration_statute`) plus a likely-wrong `interest_arbitration_flag` | `ma_boston_clerical_admin_2023` | high | **CONFIRMED** (direct CSV read, field-by-field) | Swap `total_comp_note`/`longevity_detail` content; correct `binding_arbitration_statute`; flip `interest_arbitration_flag` to 0 | yes — 4 concrete field-level edits proposed |
| MC03 | Seekonk `clerical_admin` is a school-committee (Administrative Secretaries) unit, not general-municipal clerical | `ma_seekonk_clerical_admin_2021` | low | **CONFIRMED, already adequately documented** | None required; `total_comp_note` already states the school-committee affiliation | no |
| MC04 | `public_works` bundles different functions (DPW field staff, clerical "DPW Clerks," multi-department labor-service units) differently by municipality | `ma_worcester_public_works_2017`, `ma_arlington_public_works_2015`, `ma_arlington_public_works_2018`, `ma_arlington_public_works_2021` | low | **CONFIRMED, already adequately documented** | None required; `total_comp_note` already states the bundling composition for every affected row | no |
| MC05 | Teacher assistants/paraprofessionals risk being merged with teachers | `ma_seekonk_teacher_2021` (only current `teacher` row) | low | **CONFIRMED — no merge found** | Monitor only; enforce the distinction if/when a TA-inclusive row is ever added | no |
| MC06 | `interest_arbitration_flag` is coded for *any* binding arbitration clause, not specifically wage-setting *interest* arbitration | `ma_arlington_public_works_2015`, `ma_arlington_public_works_2018`, `ma_seekonk_public_works_2023`, `ma_boston_clerical_admin_2023` | high | **CONFIRMED** (direct CSV read; clause text is grievance/discipline arbitration in every one of these 4 rows) | Flip flag to 0 on all 4 rows; add a field-definition clarification to `docs/schema.md` distinguishing interest vs. grievance arbitration | yes — 4 row-level edits proposed (1 shared with MC02) |
| MC07 | Worcester's three 2017 rows are short successor MOAs incorporating a prior base CBA "by reference," not full restated agreements | `ma_worcester_fire_2017`, `ma_worcester_clerical_admin_2017`, `ma_worcester_public_works_2017` | low | **CONFIRMED, already adequately documented** | None required; `total_comp_note` already states the successor-MOA/incorporation-by-reference limitation for all three rows | no |
| MC08 | `comparability_clause_flag=1` never captures genuine peer-jurisdiction wage comparability anywhere in the current corpus — it is 0-for-7 on the mechanism the flag exists to test, and in two cases (Somerville) the correct wage-comparator text is demonstrably present elsewhere in the same row | `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_arlington_public_works_2015`, `ma_arlington_public_works_2018`, `ma_seekonk_fire_2022`, `ma_wayland_fire_2020`, `ma_wayland_other_2021` | **high** | **CONFIRMED** (direct CSV read of all 7 flagged rows) | Re-extract `comparability_text`/`comparability_referent` for the two Somerville rows from the verbatim span already sitting in their own `arbitration_clause_text` field; add clarifying `comparability_referent` notes for the other 5; revisit the flag's operational definition project-wide | yes — 2 high-confidence re-extractions proposed; 5 notes-only additions |
| MC09 | `occupation_class` vs. unit-title spot check (police/fire/teacher/public_works/clerical_admin) | corpus-wide | low | **CONFIRMED — no new mismatches beyond MC03/MC04** | None beyond MC03/MC04 | no |
| MC10 | `source_type`/`source_corpus`/`retrieval_method`/`text_quality` light consistency check | `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012` | low | **PARTIALLY VERIFIED — judgment call, not a clear error** | Human call on whether `retrieval_method=public_download` or `foia` better fits a MuckRock-hosted FOIA release | needs_followup |

## 4. Detailed issue review

### MC01 — Arlington `public_works` comparability flag

**Evidence inspected:** direct `csv.DictReader` read of `data/contracts.csv` rows `ma_arlington_public_works_2015` and `ma_arlington_public_works_2018`.

**Finding:** both rows have `comparability_clause_flag=1`. The `comparability_text` field in both is identical, verbatim: *"If an employee has been out of work as a result of a work related injury and the Town's workers' compensation/line of duty office is advised by the employee's physician or the Town's examining physician or comparable medical provider..."* This is a workers'-compensation continuation clause, not peer-jurisdiction wage comparability. `comparability_referent` is blank in both rows. This directly confirms the finding already logged in `wage_mechanism_evidence_checklist.md` §11 item 1 and `non_safety_dpw_existing_corpus_scan_2026-07-04.md` §3.

**Recommended later correction:** add a verbatim-consistent value to `comparability_referent` — e.g., "workers' compensation / line-of-duty medical-provider comparability (non-wage)" — so future readers do not need to re-derive this from the flag alone. Whether to also change `comparability_clause_flag` itself to 0 is a schema-scope question (see MC08), not a simple correction, because the clause genuinely contains the word "comparable" and the field's current definition in `docs/schema.md` does not specify "wage comparability" — it just says `comparability_clause_flag: 0/1`.

**Risk if left unresolved:** a future GABRIEL run or PI-facing summary could cite this flag as evidence that DPW/public-works bargaining has peer-wage comparator language, which would be false and would understate the actual finding (DPW peer-wage comparability language is a confirmed absence in this corpus).

**Affects current analysis:** yes, if anyone reads `comparability_clause_flag` as a proxy for "has wage comparator language" without checking `comparability_text`. Does not affect anything already published, since no PI-facing synthesis has cited this flag directly.

**Type of correction:** notes-only now (add `comparability_referent` text); a flag-value change requires a schema decision first (see §5).

### MC02 — Boston `clerical_admin` field alignment (sharper than previously documented)

**Evidence inspected:** direct `csv.DictReader` read of every field in `ma_boston_clerical_admin_2023`, cross-checked against `docs/schema.md`'s authoritative column order and against the row's own 400-word `arbitration_clause_text` excerpt.

**Finding — three misplaced values, not just one:**
- `longevity_detail` (should be longevity-specific free text, or blank) instead holds a general unit-summary sentence: *"Full base CBA. City-wide administrative/clerical unit; merged units include SENA 9158E (Public Facilities/DND) and 9158F (BCYF). Has no-strike and binding arbitration clauses."* This reads like it belongs in `total_comp_note` ("free text for non-base items not forced into columns" per `docs/schema.md`), not `longevity_detail`.
- `total_comp_note` (should hold that kind of general note) instead holds only: `"MA G.L. c. 1078 (JLMC)"` — a bare JLMC statute citation. This is the anomaly the prior clerical/admin session already flagged (`wage_mechanism_evidence_checklist.md` §11 item 2), confirmed here directly. Read naively, a bare "JLMC" citation in a clerical/admin row's total-comp note could be misread as evidence of JLMC coverage. It is not: `ma_clerical_admin_bargaining_impasse_context_2026-07-05.md` (via the MMA Select Board Handbook) confirms clerical/admin employees are explicitly ineligible for JLMC services, and this row's own `arbitration_clause_text` contains zero JLMC references — only ordinary grievance-procedure definitions.
- `binding_arbitration_statute` (should hold a statute name, e.g. the pattern seen in every other `clerical_admin`/`public_works` row: `"MA G.L. c. 150E"`) instead holds `"clean"` — a `text_quality`-vocabulary value that does not belong in this field at all. This specific sub-finding was **not** previously documented in the checklist (which flagged the `total_comp_note` anomaly but described `binding_arbitration_statute` only as "holds a `text_quality`-style value," without independently verifying or proposing its correct value) — this audit sharpens it into a concrete proposed edit. Note that `text_quality` at the end of the row is also correctly `"clean"` — the row has the full, correct field count (34 of 34), so this is a content-placement error, not a missing-comma/shifted-column error that would break `validate.py` (and indeed `validate.py` does not check free-text-field content, so this row passes validation cleanly despite the misalignment).

**Independent corroborating detail:** the row's own `arbitration_clause_text` opens with *"the City of Boston and the Union recognize that Chapter I SOE, Section 8 of the General Laws provides a mechanism for arbitration..."* — "Chapter I SOE" is very likely a scan/typo rendering of "Chapter 150E," which would make **"MA G.L. c. 150E"** the correct `binding_arbitration_statute` value, consistent with every other non-safety row in the corpus. This is offered as a well-supported hypothesis, not a certainty — the recommended edit table (§6) flags it for direct re-verification against the original PDF before execution, per this project's verbatim-capture discipline.

**Finding — `interest_arbitration_flag` likely miscoded:** this row has `interest_arbitration_flag=1`, but the entire captured `arbitration_clause_text` is grievance-definition language ("Grievance Form," "Grievant," "Grievance," day-counting rules) with no interest-arbitration content (no impasse trigger, no statutory criteria, no ability-to-pay/comparator-wage language of the kind seen in the genuinely interest-arbitration Somerville rows). Combined with the external, corpus-independent finding that clerical/admin is JLMC-ineligible, `interest_arbitration_flag=1` here appears to be a mis-set flag, not a captured interest-arbitration clause. See MC06 for the broader pattern this instance belongs to.

**Recommended later correction:** see the four Boston-row edits in `metadata_cleanup_proposed_edits_2026-07-05.csv` (swap `total_comp_note`/`longevity_detail` content; correct `binding_arbitration_statute` to `"MA G.L. c. 150E"` pending direct PDF re-verification; flip `interest_arbitration_flag` to `0`).

**Risk if left unresolved:** highest of any issue in this audit — this is the row most likely to produce a false "clerical/admin has JLMC-style interest arbitration" claim if read at face value by a future analyst or GABRIEL prompt that trusts the flag/statute fields without reading the clause text.

**Affects current analysis:** yes, directly, if the corpus is ever queried programmatically (e.g., "which clerical_admin rows have interest_arbitration_flag=1 or cite JLMC") rather than read row-by-row as prior sessions have done.

**Type of correction:** production CSV edit (4 fields, 1 row) — requires approval.

### MC03 — Seekonk `clerical_admin` school-based unit

**Evidence inspected:** `ma_seekonk_clerical_admin_2021`'s `total_comp_note` field directly (no OCR needed for this field, since it is RA-written summary text, not extracted contract text): *"Official Seekonk school-contract archive PDF. Local OCR confirms agreement between Seekonk School Committee and AFSCME Local 1701 administrative secretaries for July 1 2021 through June 30 2024."*

**Finding:** confirmed — this is a school-committee unit, not a general-municipal one, and the metadata already says so in plain language. The `non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md` session's OCR read additionally confirmed (via the contract's own text) that the unit reports into Seekonk Public Schools' nursing and student-services structure.

**Recommended later correction:** none required to `data/contracts.csv`; the information already exists. If a future session wants to make this queryable without reading `total_comp_note` prose, the schema-safe option would be a new optional `unit_scope` or `funding_source` column (school vs. general-municipal) applied consistently across `clerical_admin` and `teacher` rows — a schema question, not a data-quality fix, and out of scope for this audit.

**Risk if left unresolved:** low — the affected budget-structure distinction (Chapter 70/net school spending vs. ordinary municipal general fund) is already discussed in `ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`; no current analysis conflates the two.

**Affects current analysis:** no.

**Type of correction:** no action.

### MC04 — `public_works` bundling variation

**Evidence inspected:** `total_comp_note` fields for all seven `public_works` rows, direct CSV read.

**Finding:** confirmed, and already well-documented in the metadata itself:
- `ma_worcester_public_works_2017`'s `total_comp_note` states plainly: *"DPW unit (Teamsters Local 170, DPW Clerks)."* — an administrative/clerical sub-unit inside a `public_works`-classified row.
- `ma_arlington_public_works_2015`/`_2018`'s `total_comp_note` states: *"Covers Labor Service (DPW, custodians), clerical, civil engineers grades 1-3, and administrative personnel (excludes police/fire/school committee)."* — a genuinely multi-function bundled unit.
- `ma_arlington_public_works_2021` (successor contract, same bargaining unit) inherits the same composition by construction, though its own `total_comp_note` does not re-state it (OCR-limited row; see MC07-adjacent note in `non_safety_dpw_existing_corpus_scan_2026-07-04.md` §4).

**Recommended later correction:** none required for the four rows above, since the composition is already stated. Consider adding a one-line composition note to `ma_arlington_public_works_2021`'s `total_comp_note` for consistency with its two predecessor cycles (low priority, cosmetic).

**Risk if left unresolved:** low — a naive "average public_works wage" calculation across cities would still blend clerical, custodial, and field-operations pay scales, but this is a known, already-documented limitation, not a silent one.

**Affects current analysis:** yes in the sense that any future wage-level aggregation must account for this, but this is a design consideration for that future analysis, not a metadata defect today.

**Type of correction:** no action (optional cosmetic note on one row).

### MC05 — Teacher assistants/paraprofessionals

**Evidence inspected:** `pdftotext` extraction of `corpus/ma_seekonk/ma_seekonk_educators_association_2021_2024.pdf` (the only `teacher` row in the corpus), `grep`-searched for "paraprofessional," "teacher aide," and "instructional aide."

**Finding:** the contract's own recognition-adjacent text states the district *"agrees to employ, from time to time, clerical personnel and teacher aides to assist teachers... the number of teacher aides to be used and the duties to be performed by them shall be determined by the Committee."* This explicitly places teacher aides outside the Educators Association bargaining unit and under unilateral School Committee determination — i.e., aides are not merged into this `teacher`-classified row's own wage schedule or unit composition. No paraprofessional/aide wage or step-schedule language appears inside the Educators Association contract.

**Recommended later correction:** none required. This is a monitoring item, not a current defect: `data/contracts.csv` currently has zero TA/paraprofessional rows, so there is nothing to merge or un-merge today.

**Risk if left unresolved:** none currently; risk would only materialize if a future ingestion batch added a TA/paraprofessional row and coded it `occupation_class=teacher`.

**Affects current analysis:** no.

**Type of correction:** no action (monitoring only).

### MC06 — `interest_arbitration_flag` scope

**Evidence inspected:** direct CSV read of every row with `interest_arbitration_flag=1` (6 rows total) and its paired `arbitration_clause_text`.

**Finding:** of the 6 rows flagged `interest_arbitration_flag=1`, only 2 (`ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`) contain genuine interest-arbitration text (impasse-trigger language, statutory ability-to-pay/comparator-wage criteria, a named arbitration panel deciding a wage award). The other 4 contain grievance- or discipline-scoped arbitration text:
- `ma_arlington_public_works_2015`/`_2018`: *"A grievance involving the suspension, dismissal, removal or termination of an employee under civil service law and rules may... be subject to binding arbitration..."* — civil-service disciplinary arbitration, not wage-setting arbitration.
- `ma_seekonk_public_works_2023`: *"Final binding arbitration will prevail on grievances only."* — explicit, unambiguous grievance-only scope stated in the union's own contract language.
- `ma_boston_clerical_admin_2023`: pure grievance-definition text (see MC02).

This confirms and sharpens `wage_mechanism_evidence_checklist.md` §11 item 6, which had already flagged the naming mismatch qualitatively; this audit adds the specific row-level enumeration and confirms all 4 non-Somerville rows share the same pattern.

A related but distinct observation: most JLMC-eligible police/fire rows (e.g., `ma_worcester_fire_2017`, `ma_boston_police_2020`, `ma_arlington_fire_2021`, `ma_newton_police_2015`, `ma_georgetown_police_2020`, `ma_seekonk_police_2022`, `ma_seekonk_fire_2022`, `ma_franklin_*`, `ma_wayland_*`) have `interest_arbitration_flag=0` despite correctly citing `"MA G.L. c. 1078 (JLMC)"` in `binding_arbitration_statute`. This is not necessarily wrong — for most of these rows, `arbitration_clause_text` is blank because the underlying document is only partially OCR'd or the award text was never separately collected, and per this project's "capture verbatim, never pre-code" discipline (`CLAUDE.md`), the flag should stay 0 until real clause text is captured, rather than being set to 1 on the strength of institutional inference alone. This is flagged as a documentation clarification, not a data error: readers should understand `interest_arbitration_flag=0` on a JLMC-cited safety row as "clause text not yet captured," not "this unit lacks interest arbitration."

**Recommended later correction:** flip `interest_arbitration_flag` to `0` on the 4 misflagged rows (`ma_arlington_public_works_2015`, `ma_arlington_public_works_2018`, `ma_seekonk_public_works_2023`, `ma_boston_clerical_admin_2023`); add a field-definition clarification to `docs/schema.md` stating explicitly that `interest_arbitration_flag` should track wage-setting/impasse interest arbitration specifically, distinct from grievance/discipline arbitration (which the existing `arbitration_clause_text` field can still capture verbatim regardless of type).

**Risk if left unresolved:** high — this flag is a natural candidate for any future cross-occupation "who has compulsory interest arbitration" query, and as currently coded it would return 4 false positives (3 non-safety, 1 which happens to also be the JLMC-eligibility-confused Boston row).

**Affects current analysis:** yes, though every substantive claim in this project's memos to date about interest arbitration was independently verified against clause text and external sources (per `wage_mechanism_evidence_checklist.md` XC09), so no published finding currently relies on this flag at face value.

**Type of correction:** production CSV edit (4 rows, 1 field each; the Boston row's flag flip is shared with MC02's edit set).

### MC07 — Worcester MOA incorporation-by-reference

**Evidence inspected:** `pdftotext` extraction and `grep` of `worcester_local490_clerical_cba_2017-2020.pdf` and `worcester_local170_dpw_cba_2017-2020.pdf`; `total_comp_note` field for `ma_worcester_fire_2017` (image-only PDF; not re-OCR'd this session, relying on the already-legible metadata field and the prior session's OCR-based note).

**Finding:** confirmed, and already stated in each row's own metadata:
- Clerical (`ma_worcester_clerical_admin_2017`) and DPW (`ma_worcester_public_works_2017`) `total_comp_note` fields both state: *"Successor MOA (states it is pending drafting of a new contract document; incorporates prior base CBA by reference)."* Direct text-extraction confirms the underlying PDF language: *"...have been negotiating for a successor contract... pending the drafting of a successor contract document."*
- Fire (`ma_worcester_fire_2017`) `total_comp_note` states: *"Signed successor MOA, 2017-2020 cycle... OCR-recovered wages..."* — same successor-MOA pattern, slightly less explicit about "incorporates prior base CBA by reference" wording specifically, but the same document type.

**Recommended later correction:** none required for clerical/DPW, where the limitation is already explicit. Optional, low-priority: align fire's `total_comp_note` wording to explicitly say "incorporates prior base CBA by reference" for consistency with its two sibling rows from the same bargaining cycle, if/when the fire PDF is re-OCR'd for any other reason. Not worth a standalone OCR pass on its own.

**Risk if left unresolved:** low — all three rows already carry a `text_quality`/`total_comp_note` signal that the document is a partial/successor instrument, so a careful reader is already warned.

**Affects current analysis:** no.

**Type of correction:** no action (one optional cosmetic wording alignment).

### MC08 — `comparability_clause_flag` general audit (highest-severity finding)

**Evidence inspected:** direct CSV read of all 7 rows with `comparability_clause_flag=1`, cross-referenced against each row's own `arbitration_clause_text` where present.

**Finding:** every single one of the 7 flagged rows captures a non-wage use of the word "comparable," and in two cases the genuinely relevant wage-comparator text is demonstrably sitting elsewhere in the very same row:

| obs_id | occupation | what `comparability_text` actually captures | genuine wage-comparator text exists elsewhere in this row? |
| --- | --- | --- | --- |
| `ma_somerville_police_spsoa_2012` | police | drug-testing "reasonable suspicion... comparable fact patterns" | **yes** — `arbitration_clause_text` for this same row states the Arbitration Panel considered *"the municipality's ability to pay, wages and benefits of comparable towns, and the cost of living"* |
| `ma_somerville_police_spea_2012` | police | identical drug-testing clause | **yes** — same "wages and benefits of comparable towns" language appears in this row's own `arbitration_clause_text` |
| `ma_arlington_public_works_2015` | public_works | workers'-comp "comparable medical provider" clause | not found in this corpus (confirmed absence, per MC01/`non_safety_dpw_existing_corpus_scan_2026-07-04.md`) |
| `ma_arlington_public_works_2018` | public_works | same workers'-comp clause | not found in this corpus |
| `ma_seekonk_fire_2022` | fire | work-group realignment eligibility ("years of employment... somewhat comparable") | not checked beyond this row; unrelated to wages |
| `ma_wayland_fire_2020` | fire | health-insurance "comparable plan" contribution-parity clause | not checked beyond this row; unrelated to wages |
| `ma_wayland_other_2021` | other | identical health-insurance clause | not checked beyond this row; unrelated to wages |

For the two Somerville rows, this means the extraction pass that populated `comparability_text` picked the first (or a keyword-convenient) span containing "comparable" rather than the analytically relevant one, even though the correct span was already captured verbatim in a sibling field of the same row. This is the clearest, most concretely fixable instance in this audit: no new source acquisition or judgment call is needed, only a targeted re-extraction of a span that is already inside the dataset.

**Recommended later correction:**
1. For the two Somerville rows: extract the verbatim "wages and benefits of comparable towns" phrase (and appropriate surrounding context) from the award text already present in `arbitration_clause_text` into `comparability_text`, and set `comparability_referent` to the verbatim referent named in the clause (comparable towns/municipalities, per the statutory ability-to-pay/comparator criteria the award cites).
2. For the other 5 rows: add a clarifying `comparability_referent` value describing what kind of "comparable" language was actually captured (non-wage), per the same treatment proposed for MC01.
3. Revisit the flag's operational definition project-wide (see §5) — the current corpus provides zero examples of `comparability_clause_flag=1` correctly signaling peer-wage comparability, which is the specific mechanism the project's own hypothesis matrix (H5, PD11) is trying to test.

**Risk if left unresolved:** highest in this audit alongside MC02/MC06. Any query of the form "find rows with peer-wage comparability language" run against `comparability_clause_flag`/`comparability_text` as currently populated would return zero true positives corpus-wide and two false negatives (the Somerville rows, which do have the language, just in the wrong field) — a systematic undercount, not merely a labeling nuisance.

**Affects current analysis:** yes, directly. `wage_mechanism_evidence_checklist.md` row PD11 already correctly documents the Somerville comparator language by pointing to the JLMC award text directly rather than to the `comparability_text` field — so no published finding is currently wrong, but this is because prior sessions worked around the field rather than because the field itself is reliable.

**Type of correction:** 2 high-confidence re-extractions (Somerville) + 5 notes-only additions (the rest), plus a schema-definition discussion — all proposed as concrete edits in the companion CSV, none executed.

### MC09 — `occupation_class`/unit-title consistency spot check

**Evidence inspected:** `bargaining_unit_name` field across all police, fire, teacher, public_works, and clerical_admin rows.

**Finding:** no new mismatches found beyond what MC03 (Seekonk clerical_admin/school) and MC04 (public_works bundling) already cover. Police and fire unit names are self-consistent (e.g., "Newton Police Association," "Franklin Police Sergeants Union," "Professional Firefighters of Franklin"). The one genuinely ambiguous title — Worcester's "DPW Clerks" under `public_works` — is already addressed under MC04.

**Recommended later correction:** none beyond MC03/MC04.

**Risk if left unresolved:** low.

**Affects current analysis:** no, beyond what MC03/MC04 already cover.

**Type of correction:** no action.

### MC10 — `source_type`/`source_corpus`/`retrieval_method`/`text_quality` light audit

**Evidence inspected:** all 32 rows' provenance fields; `scripts/validate.py` (which already enforces the controlled vocabularies and passes cleanly).

**Finding:** no clear enum violations exist (validate.py already confirms this). One soft judgment call: `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012` have `retrieval_method=public_download`, but `source_url_or_cite` points to `cdn.muckrock.com/foia_files/...` — i.e., the documents were originally obtained via a FOIA request (by a third party, MuckRock) and are now re-hosted for open public download. Both `public_download` (the current state of access) and `foia` (the original acquisition method) are defensible readings of the controlled vocabulary; `docs/schema.md` does not specify which should govern when a FOIA-obtained document is later openly re-hosted.

**Recommended later correction:** a human call on which convention this project wants going forward (current-access-method vs. original-acquisition-method), applied consistently to any future MuckRock-sourced or similarly re-hosted document.

**Risk if left unresolved:** low — this affects provenance metadata precision, not any substantive wage-mechanism finding.

**Affects current analysis:** no.

**Type of correction:** needs_followup (a documentation/convention decision, not a factual correction).

## 5. Proposed cleanup principles

1. **Distinguish peer-jurisdiction wage comparability from benefits/internal/non-wage comparability.** `comparability_clause_flag` and `comparability_text` should not be considered reliable signals of the project's central comparator-ratchet hypothesis (H5) until re-extracted per MC08. Any future extraction pass (manual or GABRIEL-assisted) should require the matched "comparable" span to reference wages, salary, or compensation of another jurisdiction/unit specifically — not health plans, medical providers, or scheduling eligibility.
2. **Distinguish interest arbitration from grievance arbitration.** `interest_arbitration_flag` should track wage-setting/impasse arbitration only. Grievance, discipline, and contract-interpretation arbitration clauses remain valuable and should still be captured verbatim in `arbitration_clause_text`, just without setting the interest-arbitration flag on that basis alone.
3. **Distinguish source type/field label from document contents.** A field's name is not evidence that its content matches; MC02 shows a single row can have every provenance field individually valid (passing `validate.py`) while still containing three semantically misplaced values. Any future audit should keep spot-checking content against field intent, not just against the controlled vocabulary.
4. **Preserve `occupation_class`; add notes when units are mixed or school-based.** None of this audit's findings warrant reclassifying any row. Where a unit's composition is genuinely mixed (MC04) or its institutional home differs from what the occupation label might suggest (MC03), the existing `total_comp_note` free-text field is schema-safe and, in most cases examined here, already used correctly for exactly this purpose.
5. **Never change production data without a row-level proposed edit and rationale.** Every proposed change in the companion CSV names the exact row, field, current value, and proposed value, with a confidence level and the evidence checked — no batch or heuristic edits.
6. **Keep corpus documents untouched.** All verification in this audit was read-only against already-collected corpus PDFs (via `pdftotext`, the project's existing extraction tool) or against `data/contracts.csv` directly. No file under `corpus/` was moved, renamed, or modified, and no OCR output was written back to disk outside the session scratch directory.

## 6. Proposed edit table summary

See `docs/analysis/metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows) for the full machine-readable table. In summary:
- **16 rows are marked `production_edit_needed=yes`** — a concrete `data/contracts.csv` field write, spanning 5 obs_ids: `ma_boston_clerical_admin_2023` (4 fields: `total_comp_note`, `longevity_detail`, `binding_arbitration_statute`, `interest_arbitration_flag`), `ma_arlington_public_works_2015`/`_2018` (`interest_arbitration_flag` + `comparability_referent`, 2 fields each), `ma_seekonk_public_works_2023` (`interest_arbitration_flag`), `ma_somerville_police_spsoa_2012`/`_spea_2012` (`comparability_text` + `comparability_referent` re-extracted from existing in-row text, 2 fields each), and single `comparability_referent` clarifying-note additions to `ma_seekonk_fire_2022`, `ma_wayland_fire_2020`, and `ma_wayland_other_2021`. Of these 16, 4 are boolean/flag corrections (`interest_arbitration_flag`), 3 are value corrections/swaps on the Boston row, 4 are re-extractions of already-in-dataset text (the two Somerville rows), and 5 are notes-only `comparability_referent` clarifications that add context without changing any boolean.
- **3 rows are marked `needs_followup`**: whether to also change `comparability_clause_flag` boolean values project-wide once the flag's operational scope is clarified (one row under MC01, one under MC08), and the FOIA-vs-public_download `retrieval_method` convention question (MC10).
- **1 row is a documentation/schema edit, not a data edit** (`production_edit_needed=no (schema/docs edit, not a data edit)`): clarifying the `interest_arbitration_flag` definition in `docs/schema.md` (MC06).
- **Issues requiring no CSV action at all** (not represented as rows in the CSV, since there is nothing concrete to approve): MC03 (already adequately documented), MC04 (already adequately documented for the rows that matter), MC05 (no current defect, monitoring only), MC07 (already adequately documented), MC09 (fully covered by MC03/MC04).

## 7. Items not resolved

- `AGENTS.md` was listed among the files to read first but does not exist in this repository (only `CLAUDE.md` does, which was already loaded as this session's standing instructions). This is noted per the task's instruction to flag missing files and continue.
- The exact correct value for `ma_boston_clerical_admin_2023`'s `binding_arbitration_statute` ("MA G.L. c. 150E" is proposed with medium-high, not full, confidence) should be directly re-verified against the original PDF's Article/Section numbering before being written to production, since the supporting textual clue ("Chapter I SOE, Section 8") is itself a plausible OCR/typo artifact rather than a clean citation.
- Whether `comparability_clause_flag` should be redefined to require wage-specific content, versus kept as a generic "contains the word 'comparable'" flag with the distinction pushed entirely into `comparability_referent`, is a schema design choice this audit surfaces but does not resolve — it affects the flag's value on all 7 currently-flagged rows plus (if the Somerville re-extraction is executed) how the flag should be treated for the two Somerville rows' *actual* wage-comparator clause.
- Whether Worcester fire's `total_comp_note` should be re-worded to explicitly state "incorporates prior base CBA by reference" (matching its two sibling 2017 rows) was identified as a low-priority cosmetic option but not scoped in detail, since it is not evidentiarily consequential.
- No new corpus documents were opened beyond those already referenced by the rows under audit; a handful of tracked mechanism-checklist items (e.g., Section 9's still-`not searched` police/fire minimum-staffing clause review) remain outside this metadata-cleanup audit's scope entirely and are unaffected by this session.

## 8. Recommended next step

**Recommend refining the metadata schema/definitions before authorizing a production edit run.** Specifically:
1. Resolve the two `needs_followup` schema-scope questions in §7 (the `comparability_clause_flag` operational definition, and the FOIA/public_download retrieval-method convention) — these affect how the row-level edits in the companion CSV should actually be written, not just whether to write them.
2. Once resolved, authorize a short, narrowly-scoped production-edit session limited to exactly the rows and fields in `metadata_cleanup_proposed_edits_2026-07-05.csv` with `production_edit_needed=yes` (9 field-level edits across 5 rows) — that session should re-verify the Boston `binding_arbitration_statute` value against the source PDF directly (per §7) before writing it, run `python scripts/validate.py` after editing, and update `data/city_coverage.csv` only if any edit changes coverage-relevant fields (none of the proposed edits do, since none touch `occupation_class`, cycle dates, or `obs_id`).
3. Do not proceed to a GABRIEL run, an OEWS/municipal descriptive baseline build, or new ingestion from this state — the standing recommended sequence (national scan → metadata audit → metadata cleanup) is on track, and metadata cleanup should complete before any measurement run that would depend on the cleaned fields (especially `comparability_clause_flag`/`comparability_text`, given MC08's severity).
