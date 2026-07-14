# Texas/Ohio Final Pre-Ingestion Approval Audit

**Date:** 2026-07-08
**Type:** final source-ingestion approval audit. Converts three prior sessions' Texas/Ohio scoping, legal-followup, and multi-city work into a small, exact, reviewable ingestion plan. **Does not ingest, download, or store any source document.** Prepares a small, approved first-batch plan for a later, separately-authorized acquisition run.

## 1. Purpose and scope

This is the final pre-ingestion audit for Texas/Ohio source acquisition, following directly from three prior sessions: an institutional scoping scan, a legal follow-up resolving two Texas statutory questions, and a multi-city scan broadening the assessment across eleven Texas and Ohio cities. Its job is narrower than any of those: **verify the CSV planning artifacts are mechanically sound (parseable, controlled-value clean, no vague or unfindable targets), and produce one clean, small, approved plan identifying exactly which sources should be fetched first, which should wait, and what metadata each should receive later.** No document is ingested, downloaded, or stored as project data in this session. No `data/contracts.csv` or `data/city_coverage.csv` row is added or edited.

## 2. Inputs reviewed

- `texas_ohio_state_comparison_institutional_scan_2026-07-07.md`
- `texas_ohio_candidate_source_targets_2026-07-07.csv`
- `texas_ohio_legal_source_audit_2026-07-07.csv`
- `texas_ohio_legal_followup_source_audit_2026-07-08.md`
- `texas_ohio_source_ingestion_audit_2026-07-08.csv`
- `texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md`
- `texas_ohio_multicity_source_targets_2026-07-08.csv`
- `report_addendum_state_comparison_plan_2026-07-07.md`
- `all_groups_source_needs_2026-07-06.csv`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, `wage_mechanism_evidence_checklist.md` (for cross-project consistency)
- `docs/schema.md`, `data/contracts.csv`, `data/city_coverage.csv` (for controlled-vocabulary and unit-of-observation ground truth)

CSV hygiene checks were performed with a lightweight Python script using the standard `csv` module: parseability, expected-column presence, controlled-value validity against each file's own declared vocabulary, exact-duplicate-row detection, and a scan for `ingest_now`/`first_batch`-tagged rows whose source description was too vague to locate later.

## 3. CSV hygiene findings

**This audit found and corrected genuine hygiene problems in three of the four reviewed CSVs — this is the single most consequential finding of this session.** Prior sessions authored these files with the Write/Edit tools as plain text, and several free-text cells (`source_target`, `source_availability`, `expected_comparison_value`, and similar descriptive fields) contained internal commas that were not wrapped in quotes. Python's `csv` module — which any later ingestion script would also use — splits an unquoted comma as a new column, silently shifting every field after it. This is exactly the kind of defect a human skim of the rendered table would not catch but a machine parse would break on.

- **`texas_ohio_source_ingestion_audit_2026-07-08.csv`**: 10 of 22 data rows had column-count mismatches (16-17 fields where 15 were expected). All 10 were repaired by merging the mis-split fields back with the correct comma restored, verified by re-parsing to exactly 15 columns on every row.
- **`texas_ohio_multicity_source_targets_2026-07-08.csv`**: 6 of 12 data rows had column-count mismatches (19-20 fields where 18 were expected). All 6 were repaired the same way. Two rows (Dallas, El Paso) required a full manual reconstruction after an initial automated merge attempt matched the wrong field span — verified by cross-checking every field against the session's own original research findings before finalizing.
- **`texas_ohio_candidate_source_targets_2026-07-07.csv`**: 8 of 11 data rows had column-count mismatches (15-19 fields where 14 were expected), including one row (Houston) requiring two separate merge operations. All 8 were repaired and verified.
- **`texas_ohio_legal_source_audit_2026-07-07.csv`**: 1 of 30 data rows was broken — a Ballotpedia URL containing literal commas had split into four fields. Repaired by rejoining the URL fragments.
- **Controlled-vocabulary drift, found and corrected after the column-count fixes:** even after every row parsed to the correct column count, two files had free-text descriptive sentences sitting in columns meant to hold only a short controlled value (`source_availability`/`expected_design_value` in the multi-city file; `expected_comparison_value` in the candidate-targets file). This was a second, independent defect — not a parsing bug, but a content-discipline lapse from when these fields were populated across multiple editing sessions. Every violation was corrected: the short controlled value was retained in its column, and the descriptive detail was preserved by moving it into an adjacent free-text column (`rationale` or `notes`) rather than being discarded.
- **The newly-created `texas_ohio_approved_source_plan_2026-07-08.csv` (Task C) was built directly as structured Python data and written with `csv.writer`**, which guarantees correct quoting regardless of embedded commas — this file was verified clean on first write and did not require post-hoc repair.
- **Remaining caveats:** this hygiene pass fixed mechanical parseability and controlled-value conformance. It did not re-verify every underlying factual claim in the repaired rows — those claims were carried over unchanged from the prior sessions' research (with source-type/confidence caveats already noted in each row's own `notes`/`caveat` field). A final full re-parse of all four files, plus the new approved-plan CSV, confirms **zero column-count mismatches, zero exact-duplicate rows, and zero controlled-value violations** across all five files as of this session.

## 4. First-batch city decision

**Confirmed: Houston, Austin, Columbus, and Cleveland remain the right first-batch cities.** Nothing in this session's hygiene work or research changed the substantive conclusions of the multi-city scan; this section restates the reasoning for a reader who has not seen that memo.

- **Houston, TX** — the richest single-city case in either state: a Chapter 174 fire unit under true, population-triggered compulsory arbitration (§174.1535), a Chapter 142 police unit under non-compulsory meet-and-confer, and a Chapter 146 non-safety unit (HOPE/AFSCME Local 123) under non-compulsory meet-and-confer — three institutional tiers in one city. Included as the Texas anchor.
- **Austin, TX** — included specifically to test whether Houston's institutional pattern generalizes. Austin independently shows the same Chapter 174-fire/Chapter 142-police split at roughly one-third Houston's population, with no population-triggered exception needed. This directly answers the concern that motivated the multi-city scan: the fire/police split is not a Houston artifact.
- **Columbus, OH** — the Ohio anchor: all four institutional tiers (police, fire, two non-safety unions) confirmed on one official portal, cross-checkable against Ohio SERB's independent archive.
- **Cleveland, OH** — included because this session's research found it to be at least as complete as Columbus, not merely a fallback: a rank-vs-supervisor police split (CPPA patrol + FOP Lodge 8 supervisors) adds a comparison dimension Columbus's single police CBA lacks, and all four tiers again have both current and prior CBAs on one official portal.
- **Backup/deferred cities remain backup/deferred** because either (a) their institutional classification rests on secondary sourcing not yet independently verified via a primary or official source (Dallas, El Paso), (b) no current, officially-hosted CBA was located for any tier this session (Akron), or (c) they are fully credible but simply not needed to answer the immediate design question once Houston+Austin and Columbus+Cleveland are secured (Fort Worth, San Antonio, Cincinnati, Toledo, Dayton). None of these cities is rejected outright — Section 7 states what would be needed to promote each.

## 5. Approved first-batch source design

15 sources are designated `approved_first_batch` in `texas_ohio_approved_source_plan_2026-07-08.csv` — within the requested 12-16 range.

| state | city | source role | source target | proposed use | proposed corpus | priority | reason | caveat |
|---|---|---|---|---|---|---|---|---|
| TX | Houston | fire | HPFFA/IAFF Local 341 CBA (2024-2029) | causal_evidence | causal | must_have | Population-triggered compulsory arbitration; closest Texas analogue to MA's JLMC | Located pages did not extract as readable text this session; confirm full-CBA vs. settlement-summary status |
| TX | Houston | police | HPOU Meet & Confer Agreement | causal_evidence | causal | must_have | Non-compulsory contrast to HPFFA within the same city | Contract-year currency not independently confirmed |
| TX | Houston | non_safety_general | HOPE/AFSCME Local 123 meet-and-confer agreement (2024) | causal_evidence | causal | must_have | The matched non-safety comparison unit; corrects prior "no channel" assumption | Recognition-clause department list not confirmed; likely spans multiple occupation classes |
| TX | Houston | budget_pay_plan | Civil-service classification/compensation pages | institutional_context | context_only | useful | Clarifies interaction with the HOPE agreement | Not yet confirmed whether it pre-dates, supplements, or is superseded by HOPE |
| TX | Austin | fire | Austin Firefighters Local 975 CBA (2023-2025 + proposed successor) | causal_evidence | causal | must_have | Demonstrates the Houston split generalizes to a sub-threshold city | Two CBA versions exist; confirm target at fetch time |
| TX | Austin | police | Austin Police Association meet-and-confer agreement (2024-2029) | causal_evidence | causal | must_have | Cleanest single Texas police source across all sessions | None material |
| TX | Austin | budget_pay_plan | Civil-service classification/compensation pages | institutional_context | context_only | useful | Fallback non-safety artifact given AFSCME 1624's uncertain status | Specific URL not re-confirmed this session |
| OH | Columbus | police | FOP Capital City Lodge No. 9 CBA (2023-2026) | causal_evidence | causal | must_have | Confirmed, dated, officially hosted; SERB cross-checkable | None material |
| OH | Columbus | fire | IAFF Local 67 CBA (2023-2026) | causal_evidence | causal | must_have | Matched to FOP CBA; SERB fact-finding report available for cross-check | None material |
| OH | Columbus | non_safety_general | AFSCME Local 1632 CBA (2024-2027) | causal_evidence | causal | must_have | Matched non-safety unit | Exact occupation-class composition unread |
| OH | Columbus | budget_pay_plan | Health Administrative Compensation Plan | institutional_context | context_only | useful | Non-bargaining-unit compensation reference | Context only, not a comparison unit |
| OH | Cleveland | police | CPPA CBA (2025-2028) | causal_evidence | causal | must_have | Rank-vs-supervisor split adds comparison dimension | None material |
| OH | Cleveland | fire | IAFF Local 93 CBA (2025-2028) | causal_evidence | causal | must_have | Matched to CPPA; equally complete to Columbus | None material |
| OH | Cleveland | non_safety_general | AFSCME Ohio Council 8 Local 100 CBA (2022-2025) | causal_evidence | causal | must_have | Matched non-safety unit | Exact occupation-class composition unread |
| OH | Cleveland | budget_pay_plan | City budget/pay-plan documentation | institutional_context | context_only | useful | Parallels Columbus's HACP | Specific URL not yet located — weakest-confirmed item in the batch |

## 6. Context-only legal/institutional sources

Five sources are designated `context_only` for pure legal/institutional interpretation, none of which should ever be treated as a `contracts.csv` row:

- **Texas Local Government Code Chapter 174** (Fire and Police Employee Relations Act) — includes §174.1535 (Mandatory Arbitration) and §174.163/174.153 (the general non-compulsory rule).
- **Texas Local Government Code Chapter 146** (Local Control of Municipal Employment Matters in Certain Municipalities) — explains HOPE's institutional basis and its population-gated scope (Houston-only).
- **Texas Local Government Code Chapter 142** (meet-and-confer) and **Texas Government Code Chapter 617** (general bargaining prohibition) — the baseline default rule against which Chapters 174/146 are carve-outs; Chapter 142's full text still rests partly on web-search synthesis rather than a direct fetch-and-read.
- **Ohio Revised Code Chapter 4117** (Public Employees' Collective Bargaining) — the closest single-state structural analogue to Massachusetts's JLMC-vs-Chapter 150E split.
- **Ohio SERB document archive** — a source-discovery/verification tool (fact-finding reports, conciliation awards, filed CBAs since 2012), used to cross-check city-posted copies, not a standalone acquisition target in itself.

## 7. Backup/deferred source design

- **Fort Worth / San Antonio (TX, backup):** both independently confirm the fire/police institutional-split pattern (Fort Worth) or the full-Chapter-174-without-compulsion contrast (San Antonio). **To promote:** confirm an official, current-cycle full-text CBA URL for each department (Fort Worth's current-cycle text was only referenced via city event pages this session; San Antonio's cycle dates need confirmation), and identify a non-safety comparison unit for San Antonio specifically, which remains entirely unidentified.
- **Cincinnati / Toledo (OH, backup):** both are fully confirmed, officially-documented alternatives to Cleveland — Cincinnati with a non-supervisor/supervisor police split, Toledo with the richest non-safety union variety (three AFSCME locals, Teamsters, UAW) in either state. **To promote:** for Cincinnati, no further work is strictly required beyond a final occupation-class read of CODE/Teamsters; for Toledo, resolve the multi-union non-safety structure into a coherent per-union contract_id plan before fetching, since a single document/single contract_id treatment would misrepresent the unit structure.
- **Dallas / El Paso / Akron / Dayton (deferred, not rejected):** Dallas needs an official-city-hosted (not aggregator-hosted) copy of its joint police+fire agreement and a resolution of whether its joint-unit structure needs a design decision before it can become a `contracts.csv` row at all; El Paso needs independent verification of its Chapter 174 adoption status beyond a single secondary bill-analysis source; Akron needs a dedicated follow-up search since no current CBA was located for any tier; Dayton needs its police-specific source located (its non-safety CBA and fire CBA are already confirmed, officially hosted).

## 8. Metadata and filename conventions for later ingestion

These are recommendations for a future, separately-authorized ingestion session — nothing here is applied to `data/contracts.csv` in this session.

- **`obs_id`/contract_id pattern:** `{state}_{cityslug}_{occupation_class}_{cycle_start_year}`, following this project's existing Massachusetts convention (e.g., `ma_cambridge_police_2019`). Proposed Texas/Ohio examples: `tx_houston_fire_2024`, `tx_austin_police_2024`, `oh_columbus_fire_2023`, `oh_cleveland_other_2022`. **None of these should be treated as final** — every proposed ID in the approved-plan CSV is marked "(tentative)" pending confirmation of the actual executed CBA's cycle_start year at fetch time, per this project's existing discipline against inventing contract terms from a description alone.
- **`occupation_class`:** existing schema values (`police`, `fire`, `teacher`, `sanitation`, `clerical_admin`, `public_works`, `transit`, `parks_rec`, `library`, `nurse_health`, `other`) are used directly for police and fire rows. Every non-safety general-employee union identified this session (HOPE, AFSCME Local 1632, AFSCME Ohio Council 8 Local 100) is provisionally marked `other`, consistent with this project's existing Wayland (`ma_wayland_other_2021`) bundled-unit precedent — each spans multiple job classifications and needs a direct recognition-clause read before final classification, which is explicitly **not** performed in this planning-only session.
- **`source_type`:** existing schema values for `contracts.csv` are only `cba`, `arbitration_award`, `factfinding`. Every meet-and-confer agreement, full Chapter 174 CBA, and general labor agreement identified in this batch is mapped to `cba` as the closest existing fit — **`meet_and_confer_agreement` is not a current schema value** and should not be added to `data/contracts.csv` without a schema decision; this audit's own `source_family` column uses it only as an internal planning label, not a schema value.
- **`source_corpus`:** `causal` for every approved CBA/agreement row; `context_only` (not a schema value, but this project's `docs/schema.md` only defines `causal`/`discourse` for the two real corpus tables) for every budget/pay-plan and legal/statutory row — these should never enter `data/contracts.csv` as rows at all, only exist as reference files if retained.
- **`retrieval_method`:** `public_download` for every approved and backup source identified this session — every located URL is a public government or public-union webpage, none behind a paywall or requiring FOIA.
- **`text_quality` expectation:** `unknown` for every not-yet-fetched target in this plan, since text quality cannot be assessed before the document is actually retrieved and run through `ingest/extract_text.py`.
- **Proposed file naming pattern:** `corpus/{state}_{cityslug}/{state}_{cityslug}_{union_or_dept}_{occupation_class}_cba_{cycle_start}_{cycle_end}.pdf`, following this project's existing convention (e.g., `corpus/ma_arlington/ma_arlington_fire_iaff_cba_fy2022_2024.pdf`). Exact filenames for every approved-batch row are proposed in `texas_ohio_approved_source_plan_2026-07-08.csv`'s `proposed_filename` column.
- **Expected causal/discourse/context role:** every approved CBA/meet-and-confer agreement is expected to be `causal` corpus; every statute, SERB archive page, and budget/pay-plan document is expected to be `context_only` and should not be forced into either the causal or discourse corpus tables.

## 9. Ingestion risks and guardrails

- **Do not ingest context-only legal statutes as CBAs.** Chapters 174, 146, 142, 617, and ORC 4117 are institutional-context documents, never `contracts.csv` rows.
- **Do not mix city labor agreements with state legal sources** in the same corpus table or citation without distinguishing source type explicitly.
- **Do not classify meet-and-confer agreements as arbitration awards.** A meet-and-confer agreement (Chapter 142/146) is a negotiated document with no compulsory arbitration behind it; only Houston Fire's Chapter 174 + §174.1535 combination and Ohio's ORC 4117.14(D)(1) conciliation-eligible units carry genuine compulsory-arbitration backing, and even those awards (if later collected) are a distinct `source_type` (`arbitration_award`) from the underlying CBA.
- **Do not treat budgets/pay plans as causal CBAs.** Every budget/pay-plan/classification document in this plan is `proposed_corpus=context_only`; none should be forced into the causal corpus even where it is the only available non-safety artifact for a given city.
- **Do not create FOIA/PRR tasks.** Every source in this plan is a public, non-FOIA, non-licensed source; none require a records request.
- **Do not infer missing contract terms from source descriptions.** Every `proposed_contract_id` in the approved plan is marked tentative; actual `cycle_start`/`cycle_end`/wage figures must come from the executed document text itself, once fetched, never from this session's summary descriptions.
- **Do not overstate Texas/Ohio representativeness.** Houston's compulsory-arbitration and non-safety-bargaining features remain confirmed population-gated to Houston alone; Austin, Columbus, and Cleveland were added specifically to avoid treating any one city as representative of its state, and this plan itself should not be cited as evidence that four cities represent either state's full institutional landscape.

## 10. Recommended next step

**The project is ready for controlled ingestion of the 15 approved first-batch sources, pending explicit user/PI approval to begin fetching.** Specifically:

- **Exact approved first batch:** the 15 rows marked `approved_first_batch` in `texas_ohio_approved_source_plan_2026-07-08.csv` (Section 5 above) — 11 causal CBA/agreement documents plus 4 budget/pay-plan context documents, across Houston, Austin, Columbus, and Cleveland.
- **Fetch to inbox first or corpus directly:** following this project's existing `ingest/README.md` convention, every source here is an open public portal (no licensed/authenticated source, no FOIA), so these should go through `ingest/fetchers/` programmatically, with each fetcher's `parse_listing()` selectors confirmed against the live page and a `--dry-run` pass completed before any live fetch — consistent with this project's existing "confirm before a real fetch run" discipline. None of these sources should go through `inbox/` + `manifest.csv`, since that path is reserved for licensed/FOIA material only.
- **User approval still needed before fetch:** yes — this session is planning/audit only, per its explicit scope boundary; no fetch, download, or ingestion should occur until the user/PI reviews this memo and the approved-plan CSV and explicitly authorizes an acquisition run.
- **Suggested agent/model:** the acquisition run itself (writing/testing `parse_listing()` selectors, running `--dry-run`, then a live fetch) is a mechanical, code-writing task well suited to the same agent/model configuration used for this project's existing `ingest/fetchers/` work — no specialized model change is needed for the fetch step itself. Any later occupation-class/recognition-clause review (resolving the `other`-tagged non-safety rows) would benefit from a careful, single-document close-read pass, consistent with how this project resolved the Wayland `other`-coded unit previously.
