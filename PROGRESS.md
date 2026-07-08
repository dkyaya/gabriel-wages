# Progress Log

Reverse-chronological session log. Newest entry on top. Records **decisions, surprises, and next steps** — not keystroke-level changes (git has those). Pair each entry with the git commits from that session.

Convention per entry: what we did, decisions made (and why), surprises/breakage, corpus snapshot (from `python ingest/audit_coverage.py`), next steps.

---

## 2026-07-08 (Texas/Ohio final pre-ingestion approval audit session) - CSV hygiene defects found and corrected; 15-source approved first batch created; awaiting user approval to fetch

**Did**
- Final pre-ingestion approval audit converting the prior three Texas/Ohio sessions' scoping/legal-followup/multi-city work into a small, exact, reviewable ingestion plan. Explicitly scoped as audit/planning only — no ingestion, no corpus/inbox edits, no `data/contracts.csv`/`data/city_coverage.csv` edits, no document downloaded or stored.
- Confirmed the prior Texas/Ohio multi-city scan session's changes (`a3217b2`, "Compare Texas and Ohio candidate cities") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- **Ran lightweight Python CSV hygiene checks (parseability, expected columns, controlled-value validity, duplicate-row detection) on the four core Texas/Ohio planning CSVs, per Task A, and found genuine, consequential defects:** 19 of 75 total data rows across `texas_ohio_source_ingestion_audit_2026-07-08.csv` (10 of 22), `texas_ohio_multicity_source_targets_2026-07-08.csv` (6 of 12), and `texas_ohio_candidate_source_targets_2026-07-07.csv` (8 of 11 — note some rows had multiple mismatches counted once) had column-count mismatches caused by unescaped commas inside free-text cells written via the Write/Edit tools in prior sessions — a real defect that any future automated ingestion script (which would also use Python's `csv` module) would choke on, not merely a cosmetic issue. `texas_ohio_legal_source_audit_2026-07-07.csv` had 1 broken row (a Ballotpedia URL containing literal commas). Additionally, two files (`texas_ohio_multicity_source_targets_2026-07-08.csv` and `texas_ohio_candidate_source_targets_2026-07-07.csv`) had controlled-vocabulary drift — long descriptive sentences sitting in columns meant to hold only a short controlled value (`source_availability`/`expected_design_value`/`expected_comparison_value`).
- **Repaired every defect found:** merged mis-split fields back with the correct comma restored (verified against each row's own prior-session content, with two rows requiring full manual reconstruction after an initial automated merge matched the wrong field span), and moved controlled-vocabulary-violating descriptive text into an adjacent free-text column so no information was lost. Re-verified all four files parse-clean with zero column-count mismatches, zero duplicate rows, and zero controlled-value violations.
- Created:
  - `docs/analysis/texas_ohio_final_pre_ingestion_audit_2026-07-08.md` (10 sections: purpose/scope; inputs reviewed; CSV hygiene findings; first-batch city decision; approved first-batch source design table; context-only legal/institutional sources; backup/deferred source design; metadata/filename conventions for later ingestion; ingestion risks and guardrails; recommended next step)
  - `docs/analysis/texas_ohio_approved_source_plan_2026-07-08.csv` (38 rows: 15 `approved_first_batch` — Houston and Austin police/fire/non-safety/budget, Columbus and Cleveland police/fire/non-safety/budget — plus 5 `context_only` legal/institutional sources, 14 `backup` rows, and 4 `defer` rows; built directly as structured Python data and written with `csv.writer` to guarantee correct quoting)
- Updated (light touches):
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv` (hygiene-repaired; 9 first-batch rows cross-referenced to the new approved plan)
  - `docs/analysis/texas_ohio_multicity_source_targets_2026-07-08.csv` (hygiene-repaired, including 2 rows requiring manual reconstruction; 4 first-batch rows cross-referenced to the new approved plan)
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (hygiene-repaired, 8 rows fully reconstructed)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (1 row hygiene-repaired)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (1 new cross-cutting row)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7D)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (one-paragraph pointer added to the Purpose section)
  - `docs/analysis/chatgpt_handoff_latest.md`
- **No `data/contracts.csv` or `data/city_coverage.csv` edits.** No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents downloaded or stored as project data.
- Ran `python scripts/validate.py` (passed, byte-for-byte identical counts to baseline) and `python ingest/audit_coverage.py` (identical to baseline) — expected, since no corpus row was added, edited, or removed this session.

**Decisions and why**
- Treated the CSV hygiene check as the session's first and highest-priority task, before any content revision, since a broken CSV would make every subsequent revision (adding cross-references, updating priorities) unreliable — fixing structure before content avoided compounding the defect.
- Chose to rebuild `texas_ohio_approved_source_plan_2026-07-08.csv` directly as structured Python data (list of lists) written via `csv.writer`, rather than authoring it as plain text via the Write tool as in prior sessions, specifically to guarantee this new file could not repeat the same class of defect just found and fixed in the other four files.
- For the two multicity-file rows (Dallas, El Paso) where an automated merge-and-verify approach matched the wrong field span (producing a row that parsed correctly but had jumbled content), did not simply accept the parse-clean result — cross-checked field-by-field against each row's own original session content before finalizing, since column-count correctness alone does not guarantee content correctness.
- Kept the approved first batch at exactly 15 sources (within the requested 12-16 range) by explicitly declining to approve Austin's AFSCME Local 1624 consultation agreement as a first-batch non-safety source, since its specific document URL was never located — consistent with the hard boundary against approving vaguely-described, unfindable targets. Substituted Austin's civil-service classification/pay-plan pages as the approved-batch's non-safety fallback instead, with the consultation agreement demoted to `backup`.

**Surprises/breakage**
- No repo breakage from this session's own changes; validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline throughout.
- **Genuine surprise, and the most important finding of this session:** three of the four core Texas/Ohio planning CSVs from prior sessions had real, mechanically-verifiable parsing defects that had gone undetected through two full prior sessions of revision (the legal-followup and multi-city sessions both edited these files in place without ever running them through an actual CSV parser). A human reading the rendered table in a text editor would very plausibly not notice these breaks, since the visual line-wrapping looks unremarkable; only a machine parse exposes them. This is a durable process lesson for this project, now recorded explicitly in the new audit memo and the report checklist.
- A second, related surprise: fixing the column-count breaks was necessary but not sufficient — two files also had a subtler, independent defect (correct column count, wrong semantic content in a controlled-vocabulary column) that only surfaced once the parsing checks passed and a second-layer controlled-value check was run.

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
Identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**No `data/contracts.csv` or `data/city_coverage.csv` edits occurred this session. No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents were downloaded or stored as project data. No PRRs were recommended. No causal claim was made about Texas or Ohio wage outcomes. No first-batch city was treated as representative of its state.**

**Recommended next step**
1. Route `texas_ohio_final_pre_ingestion_audit_2026-07-08.md` and `texas_ohio_approved_source_plan_2026-07-08.csv` to the PI for review and explicit authorization to begin fetching.
2. If approved, begin with a `--dry-run` pass through `ingest/fetchers/` against the 15 approved-plan URLs (Houston + Austin police/fire/non-safety/budget; Columbus + Cleveland police/fire/non-safety/budget) before any live fetch, per this project's existing fetcher discipline.
3. Resolve the smaller remaining pre-ingestion items already flagged (Houston Fire Officers' Association-vs-HPFFA relationship; Columbus/Cleveland non-safety unions' exact occupation-class composition; Cleveland's and Austin's not-yet-located budget/pay-plan page URLs) alongside, not necessarily before, the dry-run.
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state — this session remains audit/planning only until explicit user authorization is given.

---

## 2026-07-08 (Texas/Ohio multi-city pre-ingestion scan session) - Broadened beyond Houston/Columbus across 11 additional cities; first ingestion batch recommended

**Did**
- Final pre-ingestion multi-city comparison scan across Texas and Ohio, responding to a PI/task concern that the prior two sessions' Houston/Columbus recommendation might be overfit to two population-exceptional cities rather than reflecting a genuine, broader institutional pattern. Explicitly scoped as planning/audit only — no ingestion, no corpus/inbox edits, no `data/contracts.csv`/`data/city_coverage.csv` edits.
- Confirmed the prior Texas/Ohio legal-followup session's changes (`9aee8fd`, "Audit Texas and Ohio source targets") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Conducted bounded web research across 5 additional Texas cities (San Antonio, Dallas, Austin, Fort Worth, El Paso) and 5 additional Ohio cities (Cleveland, Cincinnati, Toledo, Akron, Dayton), on top of the already-researched Houston and Columbus.
- **Key Texas finding: the fire-adopts-full-Chapter-174-bargaining/police-remains-Chapter-142-meet-and-confer institutional split found in Houston is NOT a Houston-specific artifact.** Austin and Fort Worth both show the identical split (full collective bargaining for fire, lighter meet-and-confer for police), confirmed via each city's own official labor-relations pages — meaning the *general institutional pattern* generalizes across at least three of five core Texas cities spanning a population range from ~980,000 to ~2.4 million. What remains genuinely Houston-specific is the *compulsory* nature of Houston Fire's arbitration (§174.1535, population-gated to ≥1.9 million) and the *existence* of a statutory non-safety bargaining channel (Chapter 146, population-gated to ≥1.5 million) — both confirmed, via the prior session's direct statute reads, to apply to no other Texas city. Dallas shows a third, distinct pattern (a single joint police+fire meet-and-confer agreement, not a fire/police split, and no Chapter 174 adoption at all). A genuinely new finding: Austin codified a first-of-its-kind, non-statutory "consultation agreement" with AFSCME Local 1624 in February 2026 — the closest non-safety analogue to Houston's HOPE found among the sub-threshold cities, though not a formal Chapter 146/142 relationship.
- **Key Ohio finding: Chapter 4117/SERB produces materially more consistent cross-city institutional comparability than Texas.** Cleveland and Cincinnati were both found, on direct research, to have all four institutional tiers (one or two police units, one fire unit, one or more non-safety units) fully documented on official city portals — Cleveland's structure (a rank-vs-supervisor police split plus fire plus non-safety, each with both a current and at least one prior CBA) is, if anything, more complete than Columbus's. Toledo shows the richest non-safety union variety of any city scanned in either state (three AFSCME locals, Teamsters, and UAW). Akron is confirmed the weakest-documented Ohio city (no current CBA located for any tier, though an active, unresolved fire-department impasse is documented in local news). Dayton is moderately confirmed, correcting the prior session's overly pessimistic "no portal found" assessment — an official City of Dayton Document Center does exist, hosting at least a non-safety union CBA.
- Created:
  - `docs/analysis/texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md` (9 sections: purpose/scope; why a multi-city scan is needed; Texas institutional variation across 6 cities; Texas threshold implications; Ohio institutional variation across 6 cities; Ohio statewide-framework implications; a 12-row candidate comparison table; recommended ingestion design; bottom-line recommendation)
  - `docs/analysis/texas_ohio_multicity_source_targets_2026-07-08.csv` (12 rows, one per city scanned, with controlled `ingestion_recommendation`/`priority` ratings)
- Updated (light-to-moderate touches):
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv` (Houston and Columbus rows' notes revised to designate `first_batch` status; San Antonio and Cincinnati rows revised to `backup`; 6 new rows added for Austin, Cleveland (×2), and Toledo)
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (Austin and Cleveland rows revised in place, upgraded from `useful` to `must_have`)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (4 existing Ohio rows resolved/revised; 3 new Texas rows added for the Fort Worth fire/police split, the Dallas joint-agreement pattern, and the Austin AFSCME consultation agreement)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (2 existing rows' notes revised to reflect first_batch designation; 1 new cross-cutting row added for the multi-city scan itself)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7C)
  - `docs/analysis/chatgpt_handoff_latest.md`
- **No `data/contracts.csv` or `data/city_coverage.csv` edits.** No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents downloaded or stored as project data — every source in the new memo and CSVs is a citation/URL.
- Ran `python scripts/validate.py` (passed, byte-for-byte identical counts to baseline) and `python ingest/audit_coverage.py` (identical to baseline) — expected, since no corpus row was added, edited, or removed this session.

**Decisions and why**
- Recommended Houston+Austin (not Houston alone) for Texas and Columbus+Cleveland (not Columbus alone) for Ohio as the first ingestion batch, specifically because the task's own core concern was whether the prior recommendation was overfit to two unusually large or well-documented cities — pairing each anchor city with a second, differently-sized or differently-documented city directly tests that concern rather than merely asserting it is unfounded.
- Chose Austin over Fort Worth or San Antonio as the Texas pairing city because Austin uniquely combines the same fire/police institutional split as Houston with a genuinely new (if non-statutory) non-safety channel, making it the single most information-rich sub-threshold city rather than merely the most convenient one.
- Chose Cleveland over Cincinnati or Toledo as the Ohio pairing city because Cleveland's institutional structure was found to be at least as complete as Columbus's own (not merely "second-best"), making the Ohio comparison strongest when built on two equally strong cities rather than one strong city and one runner-up.
- Did not attempt to independently re-verify El Paso's Chapter 174 adoption status beyond the secondary bill-analysis source already available, and explicitly labeled El Paso's institutional-status row as secondary-sourced-only — consistent with this project's established discipline of distinguishing primary-source-confirmed claims from secondary-synthesis claims, applied here to a city added only for breadth rather than as a near-term acquisition target.

**Surprises/breakage**
- No repo breakage. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- Genuine surprise: the fire-vs-police institutional split first identified in Houston recurred, unprompted, in both Austin and Fort Worth — this was not something either of the prior two sessions had reason to expect, since they had only examined Houston in this level of city-specific detail. Finding the same pattern in two more cities on the first broader pass is a stronger-than-expected confirmation that this is a genuine, if not universal, Texas institutional tendency rather than a coincidence specific to one city.
- A second genuine surprise: Ohio's four largest cities scanned (Columbus, Cleveland, Cincinnati, Toledo) all showed essentially the same complete four-tier institutional structure, each independently documented on an official city portal — a degree of cross-city consistency this project had not previously had reason to expect from a bounded search, and a sharp contrast to Texas's much more varied per-city institutional landscape.
- A third surprise: Austin's AFSCME Local 1624 consultation agreement, codified in February 2026, was found entirely by chance while searching for Austin's non-safety union status — this is a very recent, dated institutional event that neither of the prior two sessions could have anticipated, since Chapter 146's population-gating had made Austin's non-safety status seem like a likely dead end before this session's research.

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
Identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**No `data/contracts.csv` or `data/city_coverage.csv` edits occurred this session. No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents were downloaded or stored as project data. No PRRs were recommended. No causal claim was made about Texas or Ohio wage outcomes. No single city in either state was treated as representative of that state as a whole.**

**Recommended next step**
1. Route the multi-city scan memo, multi-city source-target table, and all revised tables to the PI for review.
2. If the PI approves, the recommended first ingestion batch is Houston + Austin (Texas) and Columbus + Cleveland (Ohio), prioritizing CBAs/agreements first, budget/pay-plan documents second (for non-safety comparison units in cities lacking a statutory bargaining channel), and impasse/fact-finding/conciliation awards third.
3. Before ingestion begins, resolve the smaller remaining follow-ups already flagged in the prior session (Houston Fire Officers' Association-vs-HPFFA relationship; Columbus/Cleveland/Cincinnati non-safety unions' exact occupation-class composition; current-version confirmation for Austin's, Fort Worth's, and Dallas's police/fire agreements).
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state — this session remains scoping/planning only.

---

## 2026-07-08 (Texas/Ohio legal follow-up and source-ingestion audit session) - Two Texas legal follow-ups resolved; Houston and Columbus reassessed and confirmed; ingestion audit CSV created

**Did**
- Followed directly from the prior Texas/Ohio state-comparison scoping session, resolving its two flagged Texas legal follow-ups (§174.1535 "Mandatory Arbitration"; Chapter 146 non-safety-adoption status) and reassessing Houston and Columbus as first source-acquisition targets in light of what that resolution revealed. Explicitly scoped as a follow-up legal/source audit and ingestion-planning run — no ingestion, no corpus/inbox edits, no data/contracts.csv or data/city_coverage.csv edits.
- Confirmed the prior Texas/Ohio scoping session's changes (`88e573d`, "Scope Texas and Ohio comparison") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Directly fetched and read the actual statutory text of Texas Local Government Code §174.1535 and §§146.001-146.002 (previously only flagged, not read, in the prior session), plus conducted bounded web research on Houston's and Columbus's specific police/fire/non-safety labor sources.
- **Resolved §174.1535 ("Mandatory Arbitration"):** it creates a true compulsory-binding-arbitration exception to Chapter 174's general no-compulsory-arbitration rule, but applies ONLY to a fire department serving a municipality with population ≥1.9 million. Houston (~2.39 million) is the only Texas city meeting this threshold — no other candidate city (San Antonio, Dallas, Austin, Fort Worth) is close. This makes Houston Fire the closest Texas analogue to Massachusetts's JLMC found in this project's research to date, though far narrower in scope (one city, one occupation).
- **Resolved Chapter 146 non-safety adoption status:** Chapter 146 is NOT a general local-option chapter any city can choose to adopt — §146.001(a) restricts it to a municipality with population ≥1.5 million, with no election or ordinance step. Houston is again the only qualifying Texas city. This directly corrects the prior session's assumption that Houston's non-safety employees likely have no bargaining channel: HOPE (Houston Organization of Public Employees), AFSCME Local 123, has been Houston's Chapter 146 non-safety meet-and-confer bargaining agent since 2008, reportedly representing 12,000+ employees across most city departments, with a current 2024 agreement officially hosted on a City of Houston HR page.
- **Also discovered (not previously known to this project):** Houston Fire Fighters (HPFFA, IAFF Local 341) operate under full Chapter 174 collective bargaining (voter-adopted 2003), not Chapter 142 meet-and-confer as the prior session's secondary-sourced city classification had assumed. Houston Police (HPOU) remain under Chapter 142 meet-and-confer. This means Houston now shows three distinct institutional tiers in one city: compulsory-arbitration fire, non-compulsory meet-and-confer police, and non-compulsory meet-and-confer non-safety — a within-city institutional range this project's Massachusetts corpus does not have (JLMC covers MA police and fire uniformly).
- **Confirmed Columbus's remaining source gaps from the prior session:** Columbus Fire Fighters (IAFF Local 67, CBA 2023-2026) and two non-safety unions (AFSCME Local 1632, CWA) are now specifically identified, all officially hosted on the same `columbus.gov` labor-relations portal as the previously-confirmed FOP police CBA, and cross-checkable against Ohio SERB's independently-filed record (a matching 2023 IAFF Local 67 fact-finding report was located).
- Created:
  - `docs/analysis/texas_ohio_legal_followup_source_audit_2026-07-08.md` (9 sections: purpose/scope; Chapter 174 clarification; Chapter 146 clarification; Houston candidate assessment; Ohio Chapter 4117/SERB confirmation; Columbus candidate assessment; a Houston-vs-Columbus comparison table; ingestion-readiness conclusion; what changed from the prior session)
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv` (19 rows of exact source targets — not downloaded documents — spanning Texas/Ohio statutory context, Houston's three tiers, Columbus's four contracts, and second-choice San Antonio/Cincinnati rows, each with a controlled ingestion_decision/priority/followup_needed rating)
- Updated (light-to-moderate touches):
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (Houston and Columbus rows revised in place to reflect this session's findings; no other rows touched)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (2 existing rows' `needs_followup` flipped to resolved with an explanatory note; 6 new rows added for §174.1535, HPFFA's Ch.174 status, HOPE/Ch.146, the official Houston police/non-safety source URLs, and Columbus's fire/non-safety sources)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (3 existing cross-cutting rows revised in place — the TX legal-followup row marked resolved; the Houston and Columbus rows upgraded from `absent`/no-document-identified to `partial`/specific-documents-identified)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7B: follow-up-completed status, Houston/Columbus ingestion-readiness, remaining pre-report decisions, and a reaffirmed caution against generalizing a Houston-only institutional finding to "Texas")
  - `docs/analysis/chatgpt_handoff_latest.md`
- **No `data/contracts.csv` or `data/city_coverage.csv` edits.** No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents downloaded or stored as project data — every source in the new memo and CSVs is a citation/URL; two official Houston PDFs were fetched transiently via the web-research tool for text extraction (which failed, a tooling limitation) but were not saved into this repository.
- Ran `python scripts/validate.py` (passed, byte-for-byte identical counts to baseline) and `python ingest/audit_coverage.py` (identical to baseline) — expected, since no corpus row was added, edited, or removed this session.

**Decisions and why**
- Prioritized resolving the two flagged Texas legal follow-ups with a direct statute fetch-and-read before touching the candidate-city assessment, since both follow-ups turned out to share the same population-gate structure and that structure changes which Texas city is actually the strongest candidate — resolving them first, rather than in parallel with the city reassessment, avoided writing a city assessment that would need to be re-corrected once the statutory text was read.
- Chose not to attempt a local download/OCR pass on the Houston PDFs that failed to extract via the web-research tool, even though this project's own `ingest/extract_text.py` utility could plausibly handle them — this run's explicit scope boundary is planning/audit only, and invoking the extraction pipeline against externally-fetched documents would blur the line between "planning" and "acquisition" in a way the task's hard boundaries (no ingestion, no documents downloaded/stored) were designed to prevent. Flagged this as the first step of a future acquisition session instead.
- Elected to correct the candidate-source-targets and legal-source-audit CSVs in place (revising the Houston/Columbus rows) rather than appending duplicate new rows, since the task explicitly asked to "confirm or revise" these tables and appending would have left a stale, now-incorrect Houston row sitting alongside a corrected one.

**Surprises/breakage**
- No repo breakage. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- Genuine surprise: both of the prior session's flagged Texas follow-ups resolved into the *same* underlying legal mechanism — a population threshold, gating first fire-arbitration compulsion (≥1.9 million) and second non-safety bargaining-channel existence (≥1.5 million) — and both thresholds happen to currently identify Houston as the sole qualifying Texas city. This was not anticipated going into this session; the two follow-ups looked unrelated in the prior session's framing.
- A second genuine surprise: the prior session's Texas institutional scan had classified Houston Fire as a Chapter 142 meet-and-confer city (based on a secondary bill-analysis source listing adoption dates by city); this session's more targeted research found Houston Fire actually operates under full Chapter 174 collective bargaining, adopted by a 2003 voter referendum. This is a correction, not merely new information, and is documented explicitly in Section 9 of the new follow-up memo so a future session does not re-introduce the earlier, incorrect classification.
- A third surprise, this one a tooling limitation rather than a substantive finding: none of the official Houston PDFs located this session extracted as readable text through the session's web-fetch tooling, despite being confirmed as legitimate, officially-hosted documents via search-result metadata and cross-referencing. This is noted explicitly in the new memo as a reason to use this project's own extraction pipeline at acquisition time, not as evidence the documents themselves are deficient.

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
Identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**No `data/contracts.csv` or `data/city_coverage.csv` edits occurred this session. No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents were downloaded or stored as project data. No PRRs were recommended. No causal claim was made about Texas or Ohio wage outcomes, and this session's Houston-specific findings are explicitly not generalized to "Texas" as a whole.**

**Recommended next step**
1. Route the new follow-up memo and ingestion audit CSV to the PI for review, alongside the revised candidate-target and legal-source-audit tables and the updated report checklist's new Section 7B.
2. If the PI wants to proceed toward acquisition, the recommended first step is resolving the small remaining pre-ingestion items (Houston Fire Officers' Association-vs-HPFFA relationship; Columbus AFSCME 1632/CWA occupation-class composition; confirming current-version status of each Houston contract) rather than jumping directly to ingestion.
3. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state — this session remains scoping/planning only.

---

## 2026-07-07 (Texas/Ohio state-comparison scoping session) - Institutional scan, candidate source-target table, and legal audit created; scoping only, no acquisition

**Did**
- Responded to a PI request to look beyond Massachusetts (PI's own words: "I think it is important to look at a state other than Mass, since Mass has this arbitration provision that many people say is responsible for crazy wages. Can you look at one or two other states?"), with Texas and Ohio suggested by the PI. This was explicitly scoped as institutional-law scoping and source-target planning, not causal evidence, and not a source-acquisition run.
- Confirmed the prior Harvard Proxy evidence-window scaffold revision session's changes were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Read (as required first-read inputs): `AGENTS.md`, this file, `docs/analysis/chatgpt_handoff_latest.md`, `docs/schema.md`, `data/contracts.csv`, `data/city_coverage.csv`, the core report/audit files, the existing 14-state public-sector impasse/arbitration citation audit (`public_sector_impasse_arbitration_state_law_citation_audit_2026-07-05.md` and its companion CSV), `all_groups_source_needs_2026-07-06.csv`, and `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`.
- Conducted bounded public web research (official state statute sites, state labor-relations agencies, municipal HR/labor-relations portals) on Texas Local Government Code Chapter 174 (Fire and Police Employee Relations Act), Chapter 142/146 (meet-and-confer / non-safety local-option bargaining), Texas Government Code Chapter 617 (general public-sector bargaining prohibition), and Ohio Revised Code Chapter 4117 (Public Employees' Collective Bargaining) plus SERB's fact-finding/conciliation process and public document archive.
- Created:
  - `docs/analysis/texas_ohio_state_comparison_institutional_scan_2026-07-07.md` (8 sections: purpose/PI request; why TX/OH are useful contrasts; state institutional profiles for MA/TX/OH; Texas focus; Ohio focus; a MA/TX/OH comparison table; implications for project hypotheses; recommended next step)
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (11 rows: 5 Texas candidate cities/jurisdictions — Houston, San Antonio, Austin, Dallas, Fort Worth — 5 Ohio candidates — Columbus, Cincinnati, Cleveland, Dayton, Akron — plus a statewide SERB-archive row, each with controlled-vocabulary availability/value/priority/fetch_later ratings)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (20 rows auditing specific legal/institutional claims by source type and confidence, distinguishing primary statute citations from secondary/news-hosted/web-search-synthesis sources)
  - `docs/analysis/report_addendum_state_comparison_plan_2026-07-07.md` (how this scan should feed the existing report draft: recommends a short main-text paragraph plus appendix pointer, not a full section; proposed paragraph language; what source work is needed before any TX/OH wage-mechanism claim could be added; how to phrase the PI's request without overclaiming; confirms no group/mechanism conclusions change)
- Updated (light touches):
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (4 new cross-cutting rows for TX/OH legal follow-ups and candidate-city acquisition items; no existing rows changed)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7A: PI-request context, incorporation decision needed, source-acquisition/citation-audit prerequisite, and a caution against implying Massachusetts is nationally representative)
  - `docs/analysis/chatgpt_handoff_latest.md`
- **Key Texas finding:** Texas's default rule (Gov't Code Ch. 617) prohibits public-sector collective bargaining and union recognition for all public employees, safety and non-safety alike. Police/fire get a narrow, locally optional carve-out — full collective bargaining under Local Gov't Code Ch. 174 (adopted city-by-city by referendum; confirmed non-compulsory arbitration under §174.163, requiring both parties' written mutual election to arbitrate under §174.153) or lighter meet-and-confer under Ch. 142 (adopted by ordinance; creates no duty to reach agreement). San Antonio uses full Ch. 174 bargaining for police (with a documented 2021 Prop B repeal-attempt ballot fight); Austin, Dallas, Fort Worth, and Houston use Ch. 142 meet-and-confer. Non-safety municipal employees generally have no bargaining channel absent a separate Ch. 146 local adoption (not yet confirmed for any candidate city); Houston's non-safety wages are set through a civil-service classification/pay-plan system instead of a CBA.
- **Key Ohio finding:** Ohio Revised Code Ch. 4117 is a single statewide statute covering all public employees (unlike Massachusetts's two-track JLMC/Ch.150E split); the safety/non-safety distinction operates within this one statute at the impasse stage — employees named on ORC 4117.14(D)(1)'s no-strike list (police, firefighters, and several other safety-adjacent categories including some dispatchers and nurses) are routed to compulsory, binding, final-offer conciliation if fact-finding fails, while other public employees (teachers, clerical, public works) retain a conditional statutory strike right instead of compulsory arbitration. SERB maintains a centralized, publicly searchable archive of CBAs, fact-finding reports, and conciliation awards since 2012 — a better centralized-records environment than any Massachusetts city this project has worked with.
- **No `data/contracts.csv` or `data/city_coverage.csv` edits.** No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents downloaded or stored — all Texas/Ohio findings are citations/URLs recorded in the new memo and CSVs, not fetched full-text.
- Ran `python scripts/validate.py` (passed, byte-for-byte identical counts to baseline) and `python ingest/audit_coverage.py` (identical to baseline) — expected, since no corpus row was added, edited, or removed this session.

**Decisions and why**
- Chose Houston and Columbus as the top-priority single-city acquisition candidates (Task B recommendation) — Houston for its combination of a located Fire CBA, a Chapter 142 meet-and-confer police process, and a clean civil-service-classification contrast for non-safety employees; Columbus for its centralized city labor-relations portal reportedly hosting all six of the city's union contracts alongside Ohio's statewide SERB backstop archive. San Antonio and Cincinnati were flagged as strong second-choice candidates rather than top picks, since San Antonio's Prop B history adds a live-politics caveat and Cincinnati's non-safety unit composition (CODE, Teamsters) was not read in enough depth this session to be fully confirmed.
- Recommended a short main-text paragraph plus appendix pointer, not a full new report section or Evidence Map row, for incorporating this scan into the existing report draft — because Texas and Ohio currently have zero corpus rows, and a full-section treatment risked visually implying evidentiary weight equivalent to the Massachusetts corpus-backed groups.
- Flagged (rather than resolved) two Texas legal follow-ups — §174.1535's "Mandatory Arbitration" text, and Chapter 146 non-safety adoption status per candidate city — as the highest-value next legal-citation-audit steps, consistent with this project's existing discipline (established in the 14-state citation audit) of distinguishing primary-source-confirmed claims from web-search-synthesis claims rather than asserting both with equal confidence.

**Surprises/breakage**
- No repo breakage. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- Genuine surprise: Texas's non-safety municipal employees are not merely under a *weaker* impasse mechanism (as in Massachusetts's Chapter 150E) — they generally have no state-recognized collective-bargaining channel at all, with civil-service classification/pay-plan systems substituting entirely. This is a structurally different kind of "non-safety wage restraint" than anything in this project's Massachusetts corpus and sharpens, rather than merely extends, the project's existing non-safety-wage-restraint hypothesis discussion.
- A second genuine surprise: Ohio's statutory no-strike/conciliation-eligible list (ORC 4117.14(D)(1)) is broader than "police and fire" — it separately names certain dispatchers and nurses, directly relevant to this project's own already-developed dispatcher public-safety-adjacent category from the 2026-07-06/07 sessions.

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
Identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**No `data/contracts.csv` or `data/city_coverage.csv` edits occurred this session. No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No documents were downloaded or stored — every Texas/Ohio source in the new memo and CSVs is a citation/URL, not a fetched full-text file. No PRRs were recommended. No causal claim was made about Texas or Ohio wage outcomes, and neither state is described as nationally representative.**

**Recommended next step**
1. Route the institutional scan, candidate-target table, legal-source-audit table, and addendum plan to the PI for review, alongside the updated report review checklist's new Section 7A.
2. If the PI wants to proceed, the recommended first acquisition targets are Houston (Texas) and Columbus (Ohio), each paired with a matched non-safety unit per this project's design discipline — not yet begun.
3. Before any acquisition, resolve the two flagged Texas legal follow-ups (§174.1535 text; Chapter 146 adoption status per candidate city) via a short, targeted citation-audit follow-up.
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state — this session is scoping only.

---

## 2026-07-07 (Harvard Proxy evidence-window scaffold revision session) - Pilot scaffold revised to use real corpus text, not contracts.csv metadata; dry-run only, no live calls

**Did**
- Confirmed the prior Harvard Proxy calling-scaffold session's changes (`dd94c1b`, "Add Harvard Proxy pilot scaffold") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Diagnosed and fixed a genuine gap in the prior session's scaffold: `scripts/proxy_pilot_must_have_sources.py` built its dry-run and (would-be) live prompts entirely from a single `data/contracts.csv` metadata field (`total_comp_note`), an RA-written administrative summary, rather than the actual corpus document text — insufficient for source-need questions (dispatcher staffing rules, custodial wage classifications, sanitation/transfer-station language) that depend on a document's own body content.
- Created:
  - `docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md` (7 sections: what the old scaffold did; why the metadata snippet was insufficient; why dry-run's `selected_rows.csv` correctly has no model answer; what evidence-window mode changes; safety protections retained; remaining limitations; recommended next step before live calls)
- Rewrote:
  - `scripts/proxy_pilot_must_have_sources.py` — dry-run (and, if ever live-approved, live) prompts now built from bounded evidence windows located by curated term search directly in each row's own already-collected corpus file, extracted via this project's existing `ingest/extract_text.py` utility (text-layer-first, local OCR fallback, no network access). Added named `--pilot-set` options (`must_have`, `dispatch_custodial`, `sanitation_seekonk`, `custodial_only`), an explicit `--contract-id`/`--terms` option for one-off exploratory dry-runs, and a new `evidence_windows.csv` output. Live mode now skips (does not call the proxy for) any row with zero evidence windows rather than sending an empty prompt.
- Updated (light-to-moderate touches):
  - `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md` (new "Evidence-window mode" section; updated dry-run/live command examples for the named pilot sets and `--contract-id`; new "do not run live if evidence_windows.csv is empty or irrelevant" rule; updated expected-outputs table; updated inspect-outputs and choose-pilot-rows sections)
  - `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md` (one new note in the output/logging-pattern section pointing to the evidence-window revision)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Tested the revised dry-run path directly, exercising all required pilot sets:** `--pilot-set dispatch_custodial --limit 2` (15 evidence windows each for Arlington/Franklin), `--pilot-set sanitation_seekonk --limit 1` (5 evidence windows for Seekonk), `--pilot-set must_have --limit 4` (all four rows, including a successful local OCR fallback for the `ocr_messy` Wayland file — 15 evidence windows found), and `--contract-id ma_georgetown_other_2020 --terms ...` (9 evidence windows). Directly inspected `evidence_windows.csv` and `prompt_preview.md` output and confirmed real, verbatim corpus passages are embedded — for Arlington specifically, confirmed the more specific multi-word target terms ("Lead Dispatcher," "complement," "EMD") successfully surfaced the substantive Article XXI staffing-complement and EMD-stipend text, even though a few generic single-word terms were consumed by earlier table-of-contents matches (a real, now-documented limitation, not a bug). Re-confirmed both live-mode safety-gate refusals (`--live` with no `--limit`; `--live --limit 5`) still work identically to the prior session, creating no output directory and reading no credential.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/` (evidence-window construction only reads already-collected files); did not run GABRIEL; did not make any live model/API/Harvard-proxy call; did not ingest any document; did not print, inspect, or commit any secret or `.env` content.

**Decisions and why**
- Reused this project's own existing `ingest/extract_text.py` utility for corpus text extraction rather than writing new extraction logic, per the task's explicit preference and this project's own discipline against re-implementing already-reviewed pipeline components.
- Kept `selected_rows.csv` free of any model-answer-shaped column, since dry-run mode never calls the proxy and there is no model output to record — documented this explicitly in the revision memo so a future session does not "fix" this by adding a placeholder answer field.
- Designed target-term lists to mix generic single words with specific multi-word phrases deliberately, after confirming empirically (via the Arlington dry-run) that generic single-word terms can be consumed by early, low-value matches (a table of contents) before the per-term match cap is reached — documented this as a real, known limitation rather than silently accepting a lower-quality result.
- Made live mode skip (not error on, not send an empty prompt for) any row with zero evidence windows, so a future live run cannot accidentally burn a call on a row this scaffold's own evidence search already flagged as unlikely to be useful.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- No significant surprises; the revision closed a gap this project's own evidentiary discipline (verbatim capture, not RA summary) would have flagged in any other context, and the dry-run tests confirmed the fix works as intended on the first attempt for every pilot set tried.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified (only read). No GABRIEL calls occurred. No live model/API/Harvard-proxy calls occurred — only dry-run (no-network-call) modes were exercised. No secrets, keys, or `.env` contents were printed, inspected, or committed. The prior Harvard Proxy calling-scaffold session (`dd94c1b`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. A user/PI should review the newest dry-run's `evidence_windows.csv` and `prompt_preview.md` for each pilot set of interest, confirming the evidence windows actually contain passages relevant to each source-need question, before any live pilot is considered.
2. If the evidence windows are confirmed relevant, a live pilot should proceed at 1-2 calls (not the full 3-call ceiling) until the prompt's requested structured-output schema and this scaffold's response-parsing logic are reviewed together.
3. Do not run `--live` from any future session without that explicit, out-of-band approval, and do not begin any broader GABRIEL run, OEWS/municipal descriptive baseline build, or production extraction run from this state.

---

## 2026-07-07 (Harvard Proxy calling-scaffold and dry-run safety review session) - Bounded pilot harness created; dry-run only, no live calls

**Did**
- Confirmed the prior PI-facing report planning session's changes (`aa13fa5`, "Draft safety and non-safety wage mechanisms report") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Inspected every existing script/doc that references the Harvard HUIT OpenAI proxy, GABRIEL, or `gpt-5.4-nano` (`analysis/gabriel_pilot/run_gabriel.py`, `run_gabriel_v9.py`, `run_gabriel_v10_gold_dryrun.py`, the built-in-web-search smoke/demo/diagnostic scripts, `ingest/extract_spans.py`'s `llm_pass()`, `scripts/log_api_spend.py`) via read-only inspection and targeted `grep` (never printing secret values, `.env` contents, or running any command that could echo them).
- Created:
  - `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md` (7 sections: existing call map; which scripts are safe to reuse; which are risky/too broad; environment variables expected without printing values; recommended safe calling pattern; recommended output/logging pattern; what live-call authorization should look like)
  - `scripts/proxy_pilot_must_have_sources.py` (a bounded, auditable dry-run/live pilot scaffold; defaults to dry-run; requires `--live` plus an explicit `--limit` of 1-3 for any real call; reads `HARVARD_SUBSCRIPTION_KEY` only inside the live-call code path; never prints the key; writes every run to a fresh, timestamped `tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/` directory and refuses to overwrite a prior run)
  - `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md` (dry-run and clearly-marked-do-not-run-unless-approved live command examples; expected outputs table; a pre-live-run safety checklist; how to inspect outputs; how not to commit tmp outputs; how to choose pilot rows)
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Key finding from the calling-scaffold review:** none of this project's existing GABRIEL/proxy scripts have a genuine no-network-call dry-run mode, despite one script's filename (`run_gabriel_v10_gold_dryrun.py`) suggesting otherwise — "dry-run" in that script's naming means "bounded to an 11-row gold set," not "no API call." None of the existing scripts enforce a numeric ceiling on live-call row count. The new scaffold created this session closes both gaps: a true no-call default, and a hard 3-row ceiling for any live mode.
- **Tested the dry-run path directly:** `python scripts/proxy_pilot_must_have_sources.py --dry-run --limit 2` ran successfully, wrote `run_config.json`, `selected_rows.csv`, and `prompt_preview.md` to a fresh timestamped directory, and its own log confirmed no network call was made and no subscription key was read. Also directly tested that `--live` with no `--limit`, and `--live --limit 5` (exceeding the ceiling), both refuse immediately with a clear error and create no output directory — confirming the safety gates work before any live call was ever attempted.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL; did not make any live model/API/Harvard-proxy call; did not ingest any document; did not print, inspect, or commit any secret or `.env` content.

**Decisions and why**
- Designed the pilot script's hardcoded `PILOT_ROWS` set to draw only from fields already present in `data/contracts.csv` (e.g., `total_comp_note`), rather than reading full corpus PDFs, to keep this scaffold's scope narrow and avoid re-implementing the project's existing PDF-extraction pipeline inside a pilot tool.
- Tied the hardcoded pilot rows directly to the clearest still-open "must-have" source-need item identified in the prior all-groups audit session (the Seekonk sanitation Appendix/job-description confirmation, still `partial` per `all_groups_source_needs_2026-07-06.csv`), with two additional rows (Arlington dispatcher wage detail, Wayland nurse_health credential detail) included as calibration examples even though those specific items are already resolved by direct human review.
- Read the subscription key only inside the live-call function (`_run_live`), never at module import time or in the dry-run path, so that simply importing or dry-running the script can never touch the credential — a stricter discipline than any existing script in this repository, none of which gate the key read behind an explicit live-mode flag.
- Reused `scripts/log_api_spend.py`'s existing `log_usage()`/`print_totals()` utility directly rather than reimplementing cost tracking, consistent with the calling-scaffold review's recommendation to reuse that component.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- The clearest surprise from the calling-scaffold review was that this project's existing "dry-run" naming convention (`run_gabriel_v10_gold_dryrun.py`) does not mean what the term implies elsewhere in this project's own documentation (e.g., fetcher scripts' `--dry-run` flags, which genuinely make no live call) — this is worth keeping in mind when reading any older session's references to a GABRIEL "dry run."

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL calls occurred. No live model/API/Harvard-proxy calls occurred — only a dry-run (no-network-call) mode was exercised. No secrets, keys, or `.env` contents were printed, inspected, or committed. The prior PI-facing report planning session (`aa13fa5`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. If the user/PI wants to test this scaffold against a real Harvard Proxy call, the recommended next step is an explicitly approved live pilot of at most 1-3 calls (per `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md`'s safety checklist), starting with the single clearest already-identified must-have item (the Seekonk sanitation Appendix/job-description confirmation).
2. Do not run `--live` from any future session without that explicit approval, and without first re-confirming `HARVARD_SUBSCRIPTION_KEY` is set and the estimated-cost logging in `logs/api_spend_log.csv` is being reviewed afterward.
3. Do not begin any broader GABRIEL run, OEWS/municipal descriptive baseline build, or production extraction run from this state — this session created a scaffold for future bounded pilots only, not a production pipeline.

---

## 2026-07-06 (PI-facing report planning and draft session) - Report outline, draft, review checklist, and production plan created

**Did**
- Confirmed the prior pre-report must-have evidence review session's changes (`016711c`, "Review must-have evidence before report") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/report_outline_safety_non_safety_wage_mechanisms_2026-07-06.md` (detailed outline: title block; audience/purpose; section-by-section purpose/claims/evidence/caveats/callouts for all 8 report sections; report-level claim hierarchy — central/supporting/caveats/source-design/deferred; recommended tables and callouts; 5 open decisions before formatting)
  - `docs/analysis/report_draft_safety_non_safety_wage_mechanisms_2026-07-06.md` (the full markdown report draft: Executive Summary, 8 Main Takeaways, an 11-row Evidence Map, Group-by-Group Findings for all 11 groups, Mechanism-by-Mechanism Synthesis across 13 mechanisms, Massachusetts and National Nuance, Source Needs/Next Steps with a 3-tier priority table, and 4 appendix tables)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (7 sections: claims needing PI review; claims needing source strengthening; open formatting decisions; tables that may be too large; sections that may need tightening; 5 suggested PI questions; an artifact-generation readiness checklist)
  - `docs/analysis/report_production_plan_safety_non_safety_wage_mechanisms_2026-07-06.md` (recommended next run; DOCX-first-then-PDF sequencing; style-guide application notes; main-text-vs-appendix table allocation; filename conventions; citation/auditability preservation; explicit do-not-do-until-source-acquisition-approved list)
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **This run produced a markdown draft and supporting planning files only.** No PDF, DOCX, PPTX, or other final-formatted artifact was created, consistent with the task's explicit boundary that formatting and artifact generation are deferred to a later run after user review.
- **Report content is a direct synthesis of prior session work, not new research.** Every claim in the draft traces to an already-existing memo, CSV, or corpus finding from this project's ~25 prior session artifacts (mechanism-refinement memos, corpus-scan memos, the national scan and citation audit, the all-groups audit, and the pre-report evidence-verification pass); no new corpus review, web research, or source acquisition occurred this session.
- **Group-retention frame applied as specified:** police, fire, teachers, DPW/public works as central; clerical/admin, library, custodial/facilities as strong comparison; dispatchers as public-safety-adjacent; nurse_health/public health as secondary; sanitation/solid waste as a source-design/governance case; transit deferred as a direct city-level comparison.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row; did not create any PDF/DOCX/PPTX artifact.

**Decisions and why**
- Organized the report around mechanisms (Section 5) as well as occupation groups (Section 4), per the task's explicit instruction that the mechanism-by-mechanism view is what best supports the "translation institutions, not difficulty" central argument.
- Followed the tone requirements closely: used hedged language ("current corpus shows," "evidence suggests," "requires additional sourcing") throughout; avoided causal verbs ("we proved," "causes," "explains why"); did not reference agent/model/session process language anywhere in the draft; used short, paraphrased evidentiary descriptions rather than long block quotations from underlying source documents, naming specific already-existing analysis files only where useful for auditability.
- Recommended, in the production plan, a DOCX-first-then-PDF sequencing for the eventual formatting run, reasoning that a still-reviewable document benefits from a directly-editable format before a final, harder-to-revise one.
- Flagged, rather than silently resolved, every open PI-facing decision the task specified (custodial/facilities naming, dispatcher prominence, transit's space allocation, nurse_health's placement, appendix sizing) in the outline and review checklist, since these are explicitly PI decisions per the task's own framing.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline, as expected for a documentation-only session.
- No new surprises arose during drafting; the underlying evidence base (from the prior pre-report evidence-review session) was already stable and internally consistent, which made the report draft a synthesis task rather than one requiring new reconciliation of conflicting findings.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. No PDF/DOCX/PPTX artifacts were created. The prior pre-report must-have evidence review session (`016711c`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Route the report draft and review checklist to the user/PI for review, focusing on the open questions and claims flagged in `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` §1, §2, and §6.
2. Once PI feedback is incorporated into the draft, proceed to a dedicated formatting run per `report_production_plan_safety_non_safety_wage_mechanisms_2026-07-06.md` (DOCX first, then PDF), applying the Georgia/11pt/charcoal-heading/Harvard-crimson-accent style guide.
3. Do not begin any new source-acquisition run, OEWS/municipal descriptive baseline build, or GABRIEL work from this state; the report explicitly recommends resolving its own "must-have" source needs (Section 7) only if and when the PI separately approves that work.

---

## 2026-07-06 (pre-report must-have evidence review session) - Dispatchers, custodial/facilities, and nurse_health confirmed via direct corpus re-reads; group-retention recommendations upgraded

**Did**
- Confirmed the prior all-groups audit session's changes (`c111829`, "Audit wage mechanisms across groups") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.md` (8-section memo: purpose/scope; target rows and corpus files; Arlington dispatchers; custodial/facilities; Wayland nurse_health/AFSCME 1/2; group-retention decision update table for all 11 groups; implications for source needs; recommended next step)
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.csv` (8-row machine-readable evidence table)
- Updated (light-to-moderate touches):
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (Section 11 rows NH01, CF01, CF02, DP-D01, DP-D02, DP-D03 all updated from `not searched`/assumed to `confirmed in current corpus`; intro paragraph and Section 14 corpus-evidence-summary bullet updated; Purpose section pointer added)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (5 rows updated from `partial`/`absent` to `current_corpus` reflecting this session's confirmations; no rows added or deleted)
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv` (4 new rows appended: H40-H43, which had been added to the hypothesis matrix in the prior session but never dispositioned in this table; all four now carry evidence-informed recommendations)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Task A/B (Arlington dispatchers):** direct `pdftotext` re-read of `ma_arlington_public_works_2015`'s full CBA text (1,863 lines, native text) confirmed a dedicated Article XXI ("Community Safety Dispatchers") with an explicit 9-person staffing complement plus Lead Dispatcher, a minimum-coverage-of-two rule, an EMD certification stipend, and a requirement that dispatcher vacation coverage be approved by "the Chief of Fire or Police." No per-classification base-wage table exists in this CBA — only unit-wide percentage increases; the actual base rates live in an external "Classification and Pay Plan" document not in this project's corpus. Confirmed the row's `binding_arbitration_statute` field reads MA G.L. c. 150E, not JLMC.
- **Task C (custodial/facilities):** direct `pdftotext` re-reads of `ma_georgetown_other_2020` (1,085 lines) and `ma_franklin_other_2022` (953 lines) found complete, multi-step salary schedules with genuine classification tiers. Georgetown's Appendix A shows a Licensed-vs-Unlicensed Maintenance pay differential (~11%), a direct DPW-style credential-to-pay finding; Franklin's Appendix A is a 5-step hourly schedule across 4 classifications, plus a subcontracting-restraint clause and a snow/ice double-time premium. Arlington's already-reviewed text adds supplementary custodial evidence (a dedicated Appendix B on custodial-vacancy procedures; a narrow boiler/furnace-cleaning outsourcing carve-out).
- **Task D (Wayland nurse_health/dispatch):** `ma_wayland_afscme_1_2_2020_2023.pdf` is a 48-page, image-only scan with zero native text. Per the task's allowance for a single bounded OCR attempt, ran `pdftoppm` (200 DPI) + `tesseract` across all 48 pages (no corpus file modified; OCR output kept only as a temporary working file, not written back to `corpus/` or `data/contracts.csv`). The extraction succeeded cleanly (2,186 lines) and found substantive, not incidental, evidence for both nurse_health and dispatchers: Community Health Nurses and Public Health Nurse have their own dollar-figure pay grades (G-15: $56,848-$61,311; G-7A: $75,946-$81,030), a Masters-degree credential stipend ($1,500/yr), and a documented wage-restraint finding ("Community Health Nurses' wages are in need of adjustment as they were not included in the May 2022 Compensation Study"); JCC Dispatcher and Dispatcher Coordinator have their own dollar-figure grades (G-3: $53,102-$56,631; G-4), shift differentials, and a "civilian dispatcher" appointed by the Police Chief as Training Officer. No custodial content exists in this document. The unit is far more fragmented than its name suggests, spanning at least 9 distinct professional fields.
- **Group-retention recommendations updated:** dispatchers upgraded to `keep_public_safety_adjacent` (confirmed); custodial/facilities upgraded to `keep_strong_comparison` (confirmed, schema-blocked only administratively); nurse_health upgraded from `defer` to `keep_secondary` (confirmed substantive, but single-city/fragmented-unit composition risk). All other groups (police, fire, teachers, DPW, clerical/admin, library, sanitation, transit) unchanged from the prior session's audit, since this session did not touch them directly.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/` (the OCR working files live only under `/tmp/`, outside the repository); did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Decisions and why**
- Treated this as a verification/confirmation pass, not a new mechanism-development session — every finding traces directly back to already-collected corpus text, re-read more thoroughly than in any prior session for these three groups specifically.
- Used the task's bounded OCR allowance exactly once, on the single most consequential unreadable file (Wayland's AFSCME 1/2 CBA), rather than attempting a broader re-OCR sweep; did not re-attempt Arlington's 2021-cycle CBA (whose stored OCR only recovered its table of contents), since the 2015/2018 cycles already provide sufficient, structurally-identical evidence for the same bargaining unit.
- Upgraded nurse_health from `defer` to `keep_secondary` rather than a stronger tier, given the evidence — while genuinely substantive — rests on a single city inside an unusually fragmented, nine-profession bargaining unit, a real composition caveat distinct from evidentiary thinness.
- Appended H40-H43 to the hypothesis disposition audit rather than treating their absence as an oversight to silently correct — they were added to the hypothesis matrix in the prior session but the disposition-audit CSV had not yet been extended to cover them; this session's evidence directly informs their dispositions.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- One mid-session correction: the first draft of `pre_report_must_have_evidence_review_2026-07-06.csv` was missing the task-specified `notes` column (15 columns instead of 16); caught via a direct column-count check and rewritten correctly before use.
- The clearest surprise was the depth of the Wayland OCR extraction — a document previously read only at the cover-page level across two prior sessions turned out to contain complete, dollar-figure wage-grade tables for both nurses and dispatchers, plus an explicit, quotable wage-restraint finding (nurse wages excluded from a compensation study) that this project had not previously documented for any occupation group.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. The prior all-groups audit session (`c111829`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Move to PI-facing report outline/planning, using the updated group-retention table (`pre_report_must_have_evidence_review_2026-07-06.md` §6) as the current state of record.
2. Bring the `custodial`/`facilities` controlled-vocabulary schema decision to the user/PI in parallel with report planning, not as a blocking prerequisite.
3. No further OCR or re-extraction pass is needed for any of the three documents reviewed this session. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, or new ingestion from this state.

---

## 2026-07-06 (remaining-groups scoping, cross-group audit, and source-needs planning session) - All groups scoped and audited; next-stage synthesis inputs prepared

**Did**
- Confirmed the prior transit governance-fit session's changes (`cf6e32b`, "Scope transit governance and wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_remaining_groups_scope_2026-07-06.md` (scopes nurse_health/public health, custodial/facilities, and dispatchers, with full Task-A corpus-coverage table, Massachusetts/national context, and per-group recommendations)
  - `docs/analysis/non_safety_remaining_groups_source_gaps_2026-07-06.md` (source-gap tables for all three groups)
  - `docs/analysis/all_groups_wage_mechanism_audit_2026-07-06.md` (the key cross-group audit: group-by-group table for all 11 groups examined to date, a 20-row mechanism-by-mechanism audit table, Massachusetts institutional audit, national nuance audit, source-type/evidence-quality audit, hypothesis disposition summary, source-acquisition needs, a recommended safety-vs-non-safety narrative, risks/caveats, and next steps)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (44 rows, structured source-target list by priority across all groups)
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv` (all 39 hypothesis-matrix rows dispositioned: keep_central/keep_supporting/merge/demote/defer/drop_for_now)
- Updated (all light-to-moderate touches):
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 11, "Nurse_health, custodial/facilities, and dispatcher mechanisms checklist," 7 rows NH01-NH02/CF01-CF02/DP-D01-DP-D03; Sections 12-16 renumbered from the prior 11-15; Purpose section updated with pointers to the 3 new synthesis files; Section 14 corpus-evidence-summary gained 2 new bullets for transit and the 3 remaining groups)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows appended: H40-H43, `nurse_health_professional_labor_market_pressure`, `custodial_facilities_outsourcing_and_service_buffering`, `dispatch_public_safety_adjacent_coverage_pressure`, `dispatch_civilian_status_undertranslation`; existing 39 rows untouched, confirmed via clean 4-insertion/0-deletion diff)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (2 new forward-looking rows for `custodial_facilities` and `dispatchers`, both explicitly flagged as not-yet-controlled-vocabulary values; 1 existing `nurse_health` row's notes extended; no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Task A (corpus coverage check for remaining groups):** confirmed zero direct rows for `nurse_health`, and confirmed no dedicated `custodial`/`dispatchers` controlled-vocabulary value exists at all. A direct re-read of already-collected corpus text (no new ingestion) found genuine hidden/bundled content for all three groups on the first scoping pass — a first in this project's history: `ma_wayland_other_2021`'s own `total_comp_note` names "nurses" and "dispatch" among covered titles (underlying PDF not yet OCR'd beyond its cover page); a direct `pdftotext` re-read of the already-collected Arlington `public_works` CBA (AFSCME Local 680) confirmed explicit "Community Safety Dispatchers" mechanism text (9-person staffing complement plus Lead Dispatcher, an explicit minimum-coverage-of-two rule); and `ma_georgetown_other_2020`/`ma_franklin_other_2022` (both coded `other`) are confirmed, correctly-documented custodial units, mislabeled only for lack of a controlled-vocabulary value.
- **Bounded web research** (WebSearch) confirmed: national RN-shortage data is now more precisely calibrated (~8% by 2028 easing to ~3% by 2038, concentrated in nonmetro areas) and remains hospital-sector-dominated, a population-mismatch risk for nurse_health; a live, unresolved national federal SOC-classification fight over whether 911 telecommunicators are civilian "dispatchers" or "protective service"/"first responder" workers (25 states have reclassified per NCSL Oct. 2024; the U.S. Senate passed the Enhancing First Response Act/9-1-1 SAVES Act in 2025; federal OMB explicitly declined in the 2018 SOC revision); and two concrete Massachusetts-specific dispatcher examples (Boston's 2023 mayoral executive order recognizing telecommunicators as First Responders; 2019 MA bills S.1529/H.2366 seeking a Group 1-to-Group 2 pension reclassification), neither confirmed to carry an automatic wage consequence.
- **Cross-group audit completed** across all 11 groups examined to date (police, fire, teachers, DPW, clerical/admin, library, sanitation, transit, nurse_health, custodial/facilities, dispatchers). Recommended narrative: police/fire combine multiple genuine upward-pressure mechanisms with a strong, direct translation institution (JLMC); every other group faces real pressures of its own that instead translate through weaker, alternate, or entirely absent channels (classification/reclassification, staffing substitution, service buffering, contractor/governance distance, or, for dispatchers, civilian-status classification).
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Decisions and why**
- Treated the three remaining groups (nurse_health, custodial/facilities, dispatchers) with the extra care the task required, especially dispatchers — explicitly recommended as a distinct **public-safety-adjacent** category, neither merged into ordinary non-safety comparison nor treated as safety-equivalent, pending independent re-verification of their `binding_arbitration_statute` field (not yet assumed by extension the way sanitation's Chapter 150E finding was).
- Recommended nurse_health be deferred (thinnest corpus foothold plus the sharpest population-mismatch risk of any group examined), custodial/facilities be included pending a schema decision (two already-collected rows are ready to reclassify), and dispatchers be included as public-safety-adjacent (richest already-in-corpus finding of the three, testing a genuinely new mechanism question).
- Extended the hypothesis matrix by exactly 4 rows (H40-H43), using the same surgical append-only technique validated in the prior sanitation/transit sessions, to avoid the CSV-rewrite pitfall documented in that earlier session.
- Added 2 small, explicitly forward-looking OEWS-crosswalk rows for custodial/facilities and dispatchers, flagged as not-yet-controlled-vocabulary values, per the task's instruction not to force an edit or build OEWS data.
- This session's cross-group audit and source-needs/hypothesis-disposition tables are explicitly framed as inputs to a later PI-facing report, not the report itself — consistent with the task's explicit instruction that this run is not the final PI-facing report.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- The clearest surprise was how much already-collected, already-in-corpus mechanism text existed for all three "remaining" groups without any new ingestion — particularly Arlington's explicit "Community Safety Dispatchers" staffing-complement language, which had never been surfaced in any prior session despite Arlington's `public_works` row being reviewed multiple times before (including in the original DPW corpus-scan session).

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. The prior transit governance-fit session (`cf6e32b`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Close the "must-have" zero-cost, already-in-corpus items first: full re-read of Arlington's dispatcher text for wage/step data; OCR re-extraction of `ma_wayland_afscme_1_2_2020_2023.pdf` (resolves nurse_health, dispatcher, and possible custodial content simultaneously); full-text re-read of the two already-collected custodial CBAs (Georgetown, Franklin) beyond their metadata fields.
2. Bring the `custodial`/`facilities` controlled-vocabulary schema decision to the user/PI — this blocks proper classification of 2 already-collected, already-correctly-documented rows and should not wait for a broader source-acquisition cycle.
3. Prepare the PI-facing report next (format to be decided separately), using this session's audit/source-needs/hypothesis-disposition files as direct inputs, rather than running a broader new source-acquisition plan first.
4. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, or new ingestion from this state.

---

## 2026-07-06 (transit governance-fit session) - Transit governance and wage mechanisms scoped; deferred as governance-mismatched

**Did**
- Confirmed the prior Seekonk public works sanitation-language scan (`7bc8776`, "Scan Seekonk public works sanitation language") was already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_transit_governance_mechanism_scope_2026-07-06.md` (14-section memo per task spec: purpose/scope; current corpus coverage; city-by-city governance table for all 9 cities; why transit matters; occupation/classification map; upward mechanisms; restraint mechanisms; Massachusetts institutional context; national context; claim/counterpoint table; governance-fit assessment; new hypotheses; source-extraction implications; recommended next step)
  - `docs/analysis/non_safety_transit_governance_scan_2026-07-06.csv` (machine-readable version, 9 rows x 13 columns, controlled `preliminary_transit_governance`/`likely_worker_observability`/`confidence` vocabularies)
  - `docs/analysis/non_safety_transit_source_gaps_2026-07-06.md` (13 tracked gaps: governance/staffing/safety/scheduling/contracting/budget evidence, each rated for feasibility)
- Updated (all light touches, no heavy rewrites):
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 10, "Transit mechanisms checklist," 9 rows TR01-TR09; Sections 11-15 renumbered from the prior 10-14; XC09 cross-referenced with the new MBTA arbitration-statute finding)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows appended: H36-H39, `transit_route_service_coverage_pressure`, `transit_operator_shortage_and_missed_service`, `transit_contracting_governance_distance`, `transit_service_cut_buffering`; existing 35 rows untouched)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (one small annotation added to the existing `transit` row's `notes` field; no new row, no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Task A (corpus coverage check):** confirmed zero `transit` rows in `data/contracts.csv` or `data/city_coverage.csv`, and confirmed (via a keyword search across every field of `data/contracts.csv`) that no existing row contains genuine transit-, bus-, transport-, traffic-, or parking-related content (the only keyword hits were false-positive substring matches, e.g. `rta` inside "certain"). `data/contracts.csv` and `data/city_coverage.csv` were **not edited**.
- **Task B (governance scan):** bounded web research (WebSearch) confirmed all nine of this project's current cities' transit service is governed by either the MBTA (Arlington, Boston, Newton, Somerville — a Massachusetts state authority under M.G.L. c. 161A) or a regional transit authority (Franklin/Seekonk: GATRA; Georgetown: MeVa/MVRTA; Wayland: MWRTA; Worcester: WRTA), with Seekonk uniquely served by both a Massachusetts RTA (GATRA) and an out-of-state authority (Rhode Island's RIPTA). **Zero `city_operated_transit` cases were found among this project's nine cities.**
- **Most consequential finding:** Massachusetts regional transit authorities are required by M.G.L. c. 161B to contract actual service operation to a private operating company — directly confirmed for Worcester, where WRTA's unionized (ATU Local 22) bus operators are actually employed by First Transit, Inc. (incorporated in Massachusetts as Central Mass Transit Management, CMTM), not WRTA or the City of Worcester. This is a structurally deeper, state-law-mandated version of sanitation's city-level private-hauler contracting finding — it applies uniformly across all five RTA-served cities in this project's set, not as a city-by-city choice.
- **A genuinely new institutional finding, not previously examined by this project:** the MBTA has its own compulsory interest-arbitration statute (M.G.L. c. 161A §§19C-19G, 1978), separate from both JLMC (police/fire) and the ordinary Chapter 150E §9 route already independently verified four times for teachers/DPW/clerical-admin/library. This is a third distinct Massachusetts arbitration regime — but it governs the MBTA's own employees as a state authority, not any of this project's nine city governments, so it does not change the project's central police/fire-vs-non-safety-municipal-employee finding.
- **Sharpest quantified wage-to-staffing finding in this project to date, for any occupation including police/fire:** the MBTA raised bus-operator starting pay from $22.21 to $30/hour in 2024 (part of settling agreements with all 28 of its affiliated unions for the first time in 15 years) and subsequently saw a reported 365% surge in operator applications — though this describes a state authority's own workforce, not any of this project's city governments, and has not been shown to generalize to any RTA or to a smaller wage adjustment.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Decisions and why**
- Treated this as a governance-fit assessment and mechanism-scoping session, not a corpus-scan or source-acquisition session — no new corpus rows, no ingestion, consistent with the task's explicit scope boundary and its "not a corpus-building run" framing.
- Concluded transit should be **deferred indefinitely as governance-mismatched** for this project's current city-level matched-CBA design, rather than pursued as a fifth non-safety comparison group, since every one of this project's nine cities' transit workforce sits outside its own municipal government by state-law design (MBTA state authority or RTA private-operator model), not by a city-level contracting choice the way sanitation's private-hauler pattern is.
- Added exactly 4 new hypothesis-matrix rows (route/service coverage, operator shortage, contracting/governance distance, service-cut buffering), folding safety-sensitive-work, split-shift-scheduling, mechanic/maintenance-skill, and regional-authority-budget-constraint discussion into the checklist's Section 10 without separate hypothesis-matrix rows, consistent with the standing preference for a small number of high-value additions.
- Made only a small, non-structural annotation to the existing OEWS crosswalk's `transit` row (no new row, no data build), per the task's explicit instruction not to force an edit or build OEWS data.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Surprises/breakage**
- No repo breakage from this session. Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.
- The clearest surprise was how much more structurally deep transit's governance-mismatch turned out to be compared with sanitation's: rather than a city-by-city contracting choice, transit's non-municipal-employment pattern applies to all nine of this project's cities without exception and appears to be a matter of Massachusetts state-law design (M.G.L. c. 161A for the MBTA; c. 161B for regional transit authorities), not a scoping question any further desk research within this project's current city set could resolve differently.
- The MBTA's own distinct compulsory-arbitration statute (c. 161A) was an unexpected find — a third institutional arbitration regime this project had not previously catalogued, layered on top of the already-established JLMC/Chapter 150E binary.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. The prior Seekonk public works sanitation-language scan (`7bc8776`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Defer transit indefinitely as governance-mismatched for this project's current design; do not pursue targeted transit source acquisition as a next comparison-group development step.
2. If a future institutional case study (separate from this project's matched-city occupation comparison) is ever wanted, the MBTA's ATU Local 589 CBA/c. 161A arbitration history and WRTA's CMTM/ATU Local 22 arrangement are the two most information-rich targets identified — each would require its own explicit authorization before any acquisition.
3. Move to the checkpoint memo's other still-open scoping decisions (nurse_health's population mismatch; custodial/facilities and dispatcher schema questions) or a broader non-safety source-acquisition-gap review next, per user/PI direction. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, or new ingestion from this state.

---

## 2026-07-06 (Seekonk public works sanitation language scan) - Seekonk CBA inspected for hidden sanitation language

**Did**
- Confirmed the prior sanitation-service-structure-scan session's changes (immediately prior, same date) were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.md` (8-section memo: purpose/scope; source inspected (row metadata + corpus status); search terms and method; detailed findings by mechanism type; classification of evidence; implication for sanitation source strategy; recommended next step; quality note)
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.csv` (machine-readable scan table, 1 row x 13 columns, controlled `evidence_classification` and `recommended_sanitation_use` vocabularies)
- Updated (all light touches, no heavy rewrites):
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (added a 2026-07-06 update note to gap item 2, clarifying Seekonk's remaining uncertainty after the CBA scan)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (SN08 row: added detailed 2026-07-06 scan findings; classification remains `not found in current corpus` pending Appendix verification and service-structure clarification)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new 2026-07-06 update block)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Existing-corpus inspection only (no new ingestion):** extracted full text from `corpus/ma_seekonk/ma_seekonk_public_works_afscme_local_1701_2023_2026.pdf` via `pdftotext` (675 clean lines); searched systematically for all sanitation-related keywords; found zero explicit sanitation terminology anywhere in the document. Two possible-but-unconfirmed signals: (1) "Transfer Station" explicitly named in hours-of-work section with distinct scheduling (any 5 consecutive days excluding Sunday), but no linked job title or duty description; (2) CDL training reimbursement mentioned for "eligible employees," consistent with truck-operation roles, but not explicitly sanitation-linked.
- **Overall classification:** `sanitation_possible_but_unconfirmed`. Pending confirmation that the PDF extraction included all Appendices (re-opening the original PDF directly recommended to confirm) and Seekonk's service-structure verification (municipal-vs-contractor status for curbside collection, flagged as "mixed/unclear" in the prior session's city-service-structure scan).
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Decisions and why**
- Treated this as a read-only existing-corpus inspection only — the Seekonk row already exists, the corpus file is already present, and the task is to determine whether hidden/bundled sanitation language is present in already-collected text without adding rows or ingesting new documents.
- Focused the search on job-description language (Transfer Station operations, CDL roles) rather than just job-title headers, consistent with the prior session's recommendation that this re-read target "job-description language, not just titles."
- Flagged the Appendix-extraction uncertainty (whether `pdftotext` captured the full contract including Schedules) rather than assuming absence of an Appendix means the Appendix does not exist in the source PDF.
- Did not attempt to infer Seekonk's private-vs-municipal collection status from CBA text alone; kept that question explicitly tied to service-structure verification (the prior session's city-by-city service-structure scan found Seekonk marked "mixed_municipal_and_contractor / dpw_bundled_unclear" pending further investigation).

**Surprises/breakage**
- No repo breakage; validation and coverage audit remained byte-for-byte unchanged from the pre-session baseline.

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

**Next steps**
- (Immediate follow-up, not a separate authorization) Confirm whether the original Seekonk public works PDF contains a job-description Appendix/Schedule that text-extraction may have missed; re-open the original PDF directly to check.
- (Pending broader sanitation strategy decision) Integrate Seekonk's service-delivery structure (municipal-vs-contractor, flagged as unclear in the prior session) with this contract-inspection finding to reach a final determination on whether Seekonk should be treated as a `sanitation_dpw_bundled` site (if municipal-staffed and Appendix confirms) or deprioritized.
- (Not recommended as immediate next step) Do not authorize Worcester or Somerville acquisition efforts at this time; both remain higher-effort, lower-confidence leads compared to resolving Seekonk's Appendix question.

---

## 2026-07-06 (sanitation city-service-structure session) - Sanitation service structure mapped across current project cities

**Did**
- Confirmed the prior sanitation-scoping session's changes (`136fc29`, "Scope sanitation wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.md` (8-section memo: purpose/scope; current project cities; city-by-city service-structure table for all 9 cities; cross-city findings; implications for wage-mechanism design; implications for corpus/source acquisition; unresolved questions; recommended next step)
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.csv` (machine-readable version, 9 rows x 13 columns, controlled `preliminary_service_structure`/`likely_worker_observability`/`confidence` vocabularies)
- Updated (all light touches, no heavy rewrites):
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (added a 2026-07-06 scan-completed note; closed gap item 2 on whether any of the nine cities directly employs collection workers)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (Section 9 sanitation checklist: added a scan-completed note pointing to SN08/H35 and SN06/H33)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (surgical single-cell extensions to H33 `sanitation_contractor_substitution` and H35 `sanitation_dpw_bundling`'s `non_safety_relevance_or_counterpoint` fields only; all 35 rows and 12 columns otherwise untouched)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **Bounded desk research (city/town web pages, procurement/DPW pages, news coverage of a July 2025 regional hauler strike) classified all 9 current project cities' residential sanitation service structure:** Arlington, Boston, Franklin, Georgetown, and Newton show clear private-hauler contracting for residential collection (5/9); Seekonk, Wayland, and Worcester show a DPW-bundled/mixed structure where collection duties are plausibly folded into existing public_works job descriptions; Somerville remains `dpw_bundled_unclear` (zero `public_works` rows in corpus, lower confidence).
- **Most consequential finding:** the July 2025 Republic Services/Teamsters strike, which hit Newton and 13 other Boston-area suburbs simultaneously, shows that even where a private hauler's workforce is unionized, it is typically a multi-city bargaining unit — a design-fit problem for this project's one-city-one-unit comparison logic, distinct from and more fundamental than ordinary data-availability difficulty.
- **Two concrete, ranked future source targets identified:** (1) Seekonk — a zero-cost re-read of the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content, since the town's Pay-As-You-Throw program is administered by the same DPW; (2) Worcester — a higher-effort new-source-identification target, since the existing `ma_worcester_public_works_2017` row is confirmed clerical-only ("DPW Clerks"), leaving Worcester's actual field/operations DPW workforce (which may perform the city's own "yellow bag" curbside collection) entirely unrepresented in this project's corpus. Somerville is a third, lower-confidence lead notable mainly because it sits on this project's longstanding unmatched-safety-unit list independent of the sanitation question. The other 5 cities are explicitly NOT recommended as near-term acquisition targets.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Decisions and why**
- Treated this as a source-acquisition-planning and service-structure-classification session only — no new corpus rows, no ingestion, no comprehensive statewide sweep, consistent with the task's explicit scope boundary to focus on this project's 9 current cities.
- Extended only H33 and H35 in the hypothesis matrix (the two hypotheses this scan's findings bear on most directly) via surgical single-cell edits rather than a full-file rewrite or new rows, preserving the matrix's existing legacy quoting convention and avoiding a large, purely cosmetic diff.
- Did not recommend the Worcester or Somerville acquisition efforts as authorized next steps; both require a separate, explicit go-ahead given their higher effort/lower-confidence profile relative to Seekonk's zero-cost re-read.

**Surprises/breakage**
- A first attempt to update the hypothesis matrix via `csv.DictReader`/`csv.DictWriter` produced a large, unwanted diff (CRLF line-ending conversion on the first attempt, then a quoting-convention mismatch on the second, each touching all 35 rows) because the file's legacy manual quoting convention always quotes columns 6-11 regardless of necessity, which Python's default `QUOTE_MINIMAL` does not replicate. Reverted via `git checkout` and redid the change as two surgical `Edit`-tool string replacements instead; confirmed via `git diff --numstat` (8 insertions/8 deletions, one hunk) and row/column count checks that the final diff touches only the two intended cells.
- No repo breakage otherwise; validation and coverage audit both passed cleanly and remained byte-for-byte unchanged from the pre-session baseline.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` and `data/city_coverage.csv` were NOT edited this session. `corpus/` and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. The prior sanitation-scoping session (`136fc29`) was already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Re-read the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content — zero-cost, no new ingestion required.
2. Treat a Worcester field/operations-DPW source-identification effort and a broader Somerville DPW/general-government source-acquisition effort as separate future tasks requiring their own explicit authorization, not a default next step.
3. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, new ingestion, or a five-city web pilot from this state.

---

## 2026-07-06 (sanitation session) - Sanitation / solid waste wage mechanisms scoped

**Did**
- Confirmed the prior library-mechanism-and-corpus-scan session's changes (`6397378`, "Inspect library wage mechanisms") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_sanitation_solid_waste_mechanism_scope_2026-07-05.md`
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 9, "Sanitation / solid waste mechanisms checklist," 9 rows SN01-SN09; Sections 10-14 renumbered from the prior 9-13; XC09 extended to a sixth non-safety group by structural extension, explicitly marked as not independently re-verified)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows appended: H32-H35, `sanitation_route_coverage_pressure`, `sanitation_contractor_substitution`, `sanitation_mechanization_route_restructuring`, `sanitation_dpw_bundling`; existing 31 rows untouched)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was not edited this session and required no correction** — a direct query confirmed zero `occupation_class=sanitation` rows exist, and a keyword search of all `public_works`/`other` rows' `bargaining_unit_name`/`total_comp_note` fields found no sanitation/refuse/recycling-bundling language to flag or correct.
- **Task A (corpus coverage check):** confirmed zero `sanitation` rows in `data/contracts.csv`, and confirmed (via direct field inspection plus cross-reference against the prior DPW full-corpus-scan session's findings) that none of the seven already-collected `public_works` documents contains any sanitation-specific title or duty language. This made the session a scoping/source-planning run rather than a corpus-scan run, mirroring the pattern used for teachers and DPW before their own corpus data existed, not library's combined corpus-plus-institutional pattern.
- **Most consequential finding:** national trade-press reporting citing BLS Census of Fatal Occupational Injuries data now places refuse/recycling collection's fatality rate (37.4-41.4 per 100,000 workers, depending on year cited) above police's own, described directly in at least one source as "considerably higher than in law enforcement" — the strongest quantified hazard-comparison finding developed in this project to date, sharpening the qualitative "sanitation hazard exceeds police" claim already flagged in the original police/fire workforce-refinement memo.
- **Massachusetts-specific finding:** confirmed, via direct review of four Massachusetts towns' own municipal web pages (Dedham, Andover, Marshfield, Brookline), that private-hauler contracting for an entire (not merely supplemental) municipal collection service is a real, non-rare Massachusetts practice — directly relevant to why this project's current five DPW-collecting cities show no distinct sanitation title, and a materially different contractor-substitution profile than DPW's largely seasonal/peak-demand contractor use. Also confirmed, via the Massachusetts Municipal Association's own materials, that roughly 70 percent of Massachusetts communities have a consolidated DPW, with solid waste frequently organized as a named division within it (Watertown, Framingham) rather than a free-standing department.
- **Institutional finding:** no sanitation-specific JLMC-like backstop was identified in bounded review; this was treated as a high-confidence direct structural extension of the already-four-times-independently-verified JLMC eligibility rule (police and fire only, no essential-service exception found in any of the four prior institutional-verification sessions for teachers, DPW, clerical/admin, and library), rather than requiring a fresh, independently re-verified institutional memo.
- Used bounded web search for national and Massachusetts context (BLS-derived fatal-injury data via trade press; SWANA/NWRA CDL-driver retention reporting; academic municipal-solid-waste privatization/intermunicipal-cooperation cost research; individual Massachusetts town web pages), keeping national, Massachusetts, and current-corpus evidence clearly distinguished throughout, per the discipline already established for every prior non-safety group.

**Decisions and why**
- Treated this session as a scoping/source-planning run, not a corpus-scan run, given zero sanitation rows — explicitly avoided presenting any mechanism as corpus-confirmed when it is, in fact, bounded external desk research or a structural extension of an already-verified fact.
- Added exactly 4 new hypothesis-matrix rows (route coverage, contractor substitution, mechanization/route restructuring, DPW bundling), folding public-health-essentiality, dirty-work-compensating-differential, and service-frequency-buffering sub-hypotheses into existing-row discussion instead, consistent with the standing preference for a small number of high-value additions and mirroring library's identical 4-vs-8 row-reduction discipline.
- Explicitly treated contractor/private-hauler substitution as having **both** an upward-pressure reading (genuine private-sector wage competition) and a downward-pressure reading (wage-restraining substitution), rather than assuming either direction by default, per this session's explicit analytical requirement and consistent with academic privatization-cost research's own genuinely mixed findings.
- Explicitly declined to assume dirty/difficult work automatically produces a wage premium, flagging `sanitation_dirty_work_compensating_differential` as a hypothesis requiring evidence rather than adding it as a confirmed mechanism or even as its own hypothesis-matrix row, mirroring the same restraint already applied to gendered-occupational-valuation hypotheses for clerical/admin and library.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new corpus row.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged, confirming the work stayed entirely within desk research, corpus inspection (read-only), and documentation updates.
- The clearest surprise was how directly and quickly Massachusetts municipal web pages confirmed real, complete (not merely supplemental) private-hauler contracting arrangements for four towns in a single bounded search — a sharper and more concrete Massachusetts-specific finding, on the first try, than this project's DPW or clerical/admin sessions found for their own contractor-substitution and budget-governance questions respectively, even though (unlike those sessions) no sanitation-specific Massachusetts institutional source naming sanitation workers directly (comparable to the MMA Handbook's direct naming of "clerical and library employees") was found.

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` was NOT edited this session — zero sanitation rows exist and no correction was identified or needed. `data/city_coverage.csv`, `corpus/`, and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. Prior library-mechanism-and-corpus-scan changes (`6397378`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Sanitation source-acquisition planning: confirm whether any of this project's current nine cities directly employs collection workers (versus contracting the function entirely), and, separately, re-read the five already-collected `public_works` CBAs' job-description language (not just title language) for collection-duty content — a task that requires no new ingestion.
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, or new ingestion from this state.

---

## 2026-07-05 (library session) - Library wage mechanisms and corpus scan completed

**Did**
- Confirmed the prior Somerville-metadata-audit-and-checkpoint session's changes (`fe99104`, "Audit Somerville metadata and checkpoint wage mechanisms") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_library_wage_mechanism_and_corpus_scan_2026-07-05.md`
  - `docs/analysis/non_safety_library_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 8, "Library mechanisms checklist," 8 rows LB01-LB08; Sections 9-13 renumbered from the prior 8-12; XC09 updated to reflect a fourth independent non-safety confirmation; Overview and purpose paragraphs lightly extended to mention library)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows appended: H28-H31, `library_professional_credentialing`, `library_classification_reclassification`, `library_part_time_volunteer_buffering`, `library_service_deferral`; existing 27 rows untouched)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was not edited this session.** All three `library` rows' existing metadata (`binding_arbitration_statute=MA G.L. c. 150E`, `interest_arbitration_flag=0`, `comparability_clause_flag=0`) was directly verified against the source documents and found already accurate — no tiny, obvious, schema-safe correction was identified or needed.
- Developed library workers as the fourth non-safety comparison group, in a single combined session (mechanism refinement, Massachusetts institutional verification, and a full document-by-document corpus scan), since library is the only non-safety group with already-collected, unexamined corpus rows. Reviewed all three `library` occupation-class rows (Seekonk, Franklin, Wayland) in full, including an ad hoc, session-local, read-only OCR pass for Wayland's image-only scan (output not written back to `corpus/` or `data/contracts.csv`).
- **Most consequential corpus finding:** Franklin's CBA contains both an explicit MLS/MLIS degree-tier stipend (Section 15.2, up to $1,900/year) and an explicit contractual prohibition on replacing bargaining-unit hours with volunteer labor (Article 28) — the clearest, most direct evidence in this scan, running counter to a naive "volunteers buffer library staffing costs" hypothesis. Wayland's OCR-recovered text yields the most granular single-unit classification structure found anywhere in this project's corpus to date (seven library grades plus a separate custodian grade, ten-step schedule). Seekonk's document is comparatively thin (no reclassification, credentialing, or volunteer language at all).
- **Institutional finding:** the Massachusetts Municipal Association's own Select Board Handbook states directly that "it is common for clerical and library employees to be union members" under the ordinary Chapter 150E framework — an explicit, near-primary-source confirmation extending the already-three-times-verified "no JLMC access" finding to a fourth non-safety occupation class. A library-specific budget-floor mechanism was also identified and verified externally: the Massachusetts Board of Library Commissioners' Municipal Appropriation Requirement, a weaker/waivable analog to teachers' Chapter 70/net-school-spending floor.
- Used bounded web search for national context (ALA/PLA's 2024 Public Library Staff Survey; BLS occupational wage data for Librarians vs. Library Assistants, Clerical; a dated 2006 ALA-APA non-MLS salary study, explicitly flagged as not current), keeping national and Massachusetts-specific evidence clearly distinguished throughout, per the discipline already established for teachers, DPW, and clerical/admin.
- Ran a peer-community comparability check across all three documents: **no** peer-jurisdiction wage-comparability language was found in any of them — a fourth independent replication of the identical absence already documented for every `public_works` and `clerical_admin` document reviewed in prior sessions.

**Decisions and why**
- Combined mechanism-refinement, institutional-verification, and corpus-scan into a single memo (rather than the two-memo pattern used for DPW and clerical/admin), since library's institutional verification required comparatively little new research once the MMA Select Board Handbook's own language was found to name library employees directly, and all three corpus documents were already available with no source-acquisition gap in between stages.
- Added exactly 4 new hypothesis-matrix rows (professional credentialing, classification/reclassification, part-time/volunteer buffering, service deferral), folding the public-support-without-wage-translation and lower-public-salience sub-hypotheses into existing-row discussion instead, consistent with the standing preference for a small number of high-value additions.
- Treated the volunteer-substitution sub-hypothesis as **contradicted, not confirmed**, given Franklin's explicit anti-substitution clause — a clear instance of the project's discipline to report what the evidence actually shows rather than defaulting to the plausible-sounding version of a hypothesis.
- Explicitly declined to upgrade the gendered-occupational-valuation hypothesis for library work beyond `weak evidence` (general literature only), mirroring the identical, deliberate restraint already applied to clerical/admin's CA13.
- Did not edit `data/contracts.csv` or `data/city_coverage.csv`; did not touch `corpus/` or `inbox/` beyond read-only inspection; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit both passed cleanly and remained byte-for-byte unchanged, confirming the work stayed entirely within desk research and read-only corpus review.
- The clearest surprise was the width of Wayland's single-unit classification spread (L-1 Library Assistant through L-7 Assistant Director, plus a separate custodian grade folded into the same pay grid) — a wider single-bargaining-unit composition spread than this project has documented for any other occupation class, DPW included, and a reminder that "library wages" is at least as composition-sensitive a concept as "DPW wages" or "teacher wages."

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
Both outputs are identical, in every count, to the pre-session baseline — expected, since no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

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

**`data/contracts.csv` was NOT edited this session — its existing library-row metadata was verified accurate. `data/city_coverage.csv`, `corpus/`, and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. Prior Somerville-metadata-audit-and-checkpoint changes (`fe99104`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo next, per `wage_mechanism_project_checkpoint_2026-07-05.md` §10 — desk research only, since zero `sanitation` rows currently exist in this project's corpus.
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Continue treating library's remaining gaps (vacancy/turnover data, librarian-vs-assistant/page composition, part-time staffing-share trends, MBLC ARIS/compliance-history review) as future source-acquisition targets, per `non_safety_library_source_gaps_2026-07-05.md`, not as further-review gaps on already-collected documents.

---

## 2026-07-05 (follow-up session) - Somerville metadata audit closed and project mechanism checkpoint completed

**Did**
- Confirmed the prior authorized-cleanup session's changes (`47f8d25`, "Apply approved metadata cleanup") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/somerville_police_metadata_audit_2026-07-05.md`
  - `docs/analysis/somerville_police_metadata_audit_edits_2026-07-05.csv`
  - `docs/analysis/wage_mechanism_project_checkpoint_2026-07-05.md`
- Updated:
  - **`data/contracts.csv`** — 2 rows edited, 1 field each (`binding_arbitration_statute` on both Somerville police rows).
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: two new notes; not rewritten).
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block; not rewritten).
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Did **not** update `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` — the checkpoint review found no major missing or redundant hypotheses in the existing 27-row matrix; library/sanitation mechanisms would need their own dedicated refinement sessions (mirroring how teacher/DPW/clerical hypothesis rows were added) before a CSV edit would be warranted, per the task's own "only if useful" instruction.
- **Part 1 — Somerville metadata audit:** verified, with full field-by-field CSV inspection plus direct `pdftotext` re-extraction of both source PDFs, that `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012` had `binding_arbitration_statute` values (`ocr_messy`, `clean`) that were actually `text_quality` values, not statute citations — the same misplacement pattern already corrected for Boston's clerical/admin row in the prior cleanup session, but never previously audited for these two rows. Both source PDFs are confirmed genuine JLMC award-and-decision documents (dockets JLMC-17-6072 and JLMC-14-4174), and each row's own `total_comp_note` field already correctly states "MA G.L. c. 1078 (JLMC)" — a redundant, in-row confirmation of the correct value. **This met the session's bar for a fully-verified, narrow, high-confidence, schema-safe edit, so `data/contracts.csv` was corrected directly**: both rows' `binding_arbitration_statute` now reads `MA G.L. c. 1078 (JLMC)`, matching the convention used by all 13 other police/fire rows in the corpus. A closing corpus-wide sweep (`binding_arbitration_statute` checked against the `text_quality` vocabulary across all 32 rows) found zero remaining instances of this pattern.
- **Part 2 — project mechanism checkpoint:** synthesized roughly a dozen prior memos (the original police/fire mechanism work, the three non-safety mechanism-refinement-plus-institutional-verification sequences for teachers/DPW/clerical-admin, the national municipal workforce scan, and the public-sector impasse/arbitration state-law citation audit) into a single stocktake memo covering current project architecture, per-occupation-group findings, the expanded hypothesis map, national-vs-Massachusetts-specific nuance, an evidence-strength table across 11 cross-cutting mechanisms, what the current CBA-heavy corpus can and cannot show, and a prioritized recommendation for the next non-safety comparison groups.

**Decisions and why**
- Edited `data/contracts.csv` directly for the Somerville correction, rather than only proposing it, because the task's explicit authorization criteria (fully verified, narrow, high-confidence, schema-safe) were clearly met — the correct value was already redundantly present in-row (`total_comp_note`), confirmed by direct source-document re-extraction, and consistent with a corpus-wide convention already used by 13 other rows. This is a stronger evidentiary basis than the earlier Boston correction, which required inferring the correct value from an OCR/typo clue rather than reading it directly from a sibling field in the same row.
- Ran a closing sweep (`binding_arbitration_statute` vs. `text_quality` vocabulary, all 32 rows) rather than assuming the two flagged rows were the only instances, since both the Boston and Somerville anomalies were discovered incidentally rather than by systematic design — the sweep confirmed no third instance exists, closing this specific issue family completely rather than leaving it open-ended.
- Recommended `library` as the highest-priority next non-safety group specifically because it requires **no new source acquisition** — all three `library` corpus rows (Seekonk, Franklin, Wayland) already exist and are already coverage-matched to safety pairs, making a full corpus-scan-plus-institutional-verification session (mirroring the DPW/clerical/admin pattern) immediately actionable without ingestion.
- Flagged, rather than resolved, three scoping questions (transit's regional-governance fit with this project's one-city-one-bargaining-unit design; nurse_health's population mismatch between national hospital-nursing evidence and this project's municipal focus; whether dispatchers/custodial units need a new controlled-vocabulary value) as decisions for the user/PI, since none of them can be resolved by desk research alone — they are project-design choices, not evidence questions.
- Did not touch `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not update the hypothesis matrix, since no major missing/redundant hypothesis was found.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit both passed cleanly, with identical row/column counts before and after the Somerville edit, and coverage output byte-for-byte unchanged (the edit touches no coverage-relevant field).
- The clearest surprise assembling the checkpoint memo: this project's own corpus already contains dispatchers ("Community Safety Dispatchers") embedded, unlabeled, inside a `public_works`-classified Arlington bargaining unit — a genuine, pre-existing composition-fragmentation finding that had not been surfaced as its own issue in any prior session, and that bears directly on how carefully any future dispatcher-related collection or classification decision needs to be made.

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
Both outputs are unchanged in every count from the pre-edit baseline.

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

**`data/contracts.csv` was edited this session (2 rows, 1 field each: `binding_arbitration_statute`), fully verified and within the session's narrow-edit authorization. `data/city_coverage.csv`, `corpus/`, and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. Prior authorized-cleanup changes (`47f8d25`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Run a library corpus-scan-plus-institutional-verification session (mirroring the DPW/clerical/admin pattern), using the three already-collected `library` rows — no new source acquisition needed.
2. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo (desk research only, no ingestion) as the next-priority non-safety group after library.
3. Bring the three scoping decisions in `wage_mechanism_project_checkpoint_2026-07-05.md` §11 (transit governance fit, nurse_health population mismatch, custodial/dispatcher schema questions) to the user/PI before doing any further work on those specific groups.

---

## 2026-07-05 (later same day) - Authorized production metadata cleanup applied

**Did**
- Confirmed the prior metadata cleanup audit session's changes (`2e0a808`, "Audit metadata cleanup candidates") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_application_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_applied_edits_2026-07-05.csv` (29 rows: 23 applied, 4 skipped_not_needed, 1 skipped_deferred, 1 skipped_needs_followup)
- Updated:
  - **`data/contracts.csv`** — 9 rows edited, 22 field-level changes, under explicit user authorization following the prior audit.
  - `docs/schema.md` — clarified the `interest_arbitration_flag` and `comparability_clause_flag` field definitions per the user's two approved schema decisions.
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: one new top-of-section note plus short "RESOLVED" annotations on items 1, 2, and 6; not rewritten).
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Applied the user's two approved schema decisions: (1) `comparability_clause_flag` now means peer wage/peer-community/peer-employer wage comparability specifically, not any generic "comparable" language; (2) `retrieval_method=public_download` describes this project's own access method, not a document's original legal provenance, so the two MuckRock-hosted Somerville rows correctly keep `public_download` (no change needed there).
- **Edit categories applied to `data/contracts.csv`:** (a) `comparability_clause_flag`/`comparability_referent` corrected on 5 non-wage rows (Arlington `public_works` x2, Seekonk fire, Wayland fire, Wayland other) — flag flipped `1`→`0`, referent populated with the non-wage clarification; (b) genuine peer-wage-comparability text re-extracted verbatim from the Somerville police rows' own `arbitration_clause_text` field into `comparability_text`/`comparability_referent` (2 rows); (c) `interest_arbitration_flag` corrected `1`→`0` on 4 rows found to be grievance/discipline arbitration, not interest arbitration (Boston clerical/admin, Arlington `public_works` x2, Seekonk `public_works`); (d) Boston clerical/admin's 3-field misalignment corrected — `longevity_detail`/`total_comp_note` swapped and `binding_arbitration_statute` corrected from `"clean"` to `"MA G.L. c. 150E"`, the latter only after directly re-extracting `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` this session and confirming the citation independently at 3 locations in the source text.
- Discovered, but did **not** correct, a new out-of-scope anomaly while verifying the Boston edit: both Somerville police rows' `binding_arbitration_statute` fields hold `text_quality`-vocabulary values (`ocr_messy`, `clean`) instead of a statute name — the same pattern as Boston's, but never previously audited or approved. Left untouched per this session's explicit boundary against unapproved edits; flagged in the new application memo for a future audit-and-approval cycle.

**Decisions and why**
- Extended the flag correction beyond the exact rows named in the prior proposed-edits table's boolean-value cells (which had marked the `comparability_clause_flag` question `needs_followup` rather than proposing specific flips) once the user's Decision 1 resolved the scope question — applying the flag flip to all 5 non-wage rows the prior audit had already evidenced (2 named explicitly under MC01, 3 implied under MC08's `needs_followup` schema-question row), not just the subset the audit table happened to spell out as separate CSV rows. Treated this as a direct, narrow application of explicit user approval, not a "broad new metadata redesign."
- Declined to fix the newly-discovered Somerville `binding_arbitration_statute` anomaly (§ above) despite it being an obvious, evidence-clear instance of the same MC02 pattern, because it was never presented to the user for approval through the audit process — this project's cleanup discipline requires audit-then-approve, and an opportunistic mid-session fix would violate that discipline even when the fix looks safe.
- Wrote all CSV edits programmatically (`csv.DictReader`/`DictWriter`) rather than by hand, and verified before/after row count (32), column count (34), and the file's CRLF-between-records/bare-LF-within-fields convention were unchanged, to avoid any silent formatting churn or column-shift risk.
- Did not touch `data/city_coverage.csv`, since none of the applied edits change `occupation_class`, cycle dates, or `obs_id`; confirmed this via an unchanged `ingest/audit_coverage.py` output.
- Did not touch `corpus/` or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not add any new row or new occupation_class value.

**Surprises/breakage**
- No repo breakage from this session.
- Validation passed cleanly after the edits, with identical row/column counts to before.
- Coverage audit output is byte-for-byte identical to before the edits, confirming none of the corrections touched any coverage-relevant field.
- The newly-discovered Somerville `binding_arbitration_statute` anomaly (found while double-checking the Boston fix, not while reviewing Somerville's own edited fields) was the main surprise — it shows the MC02 misplacement pattern is not unique to Boston, and a future full sweep of `binding_arbitration_statute` against the `text_quality` controlled vocabulary across all 32 rows would likely be a worthwhile, low-cost follow-up audit.

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
Both outputs are unchanged from the pre-edit baseline in every count.

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

**`data/contracts.csv` was edited this session (9 rows, 22 field-level changes) under explicit user authorization. `data/city_coverage.csv`, `corpus/`, and `inbox/` were not modified. No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. Prior metadata-cleanup-audit changes (`2e0a808`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Review the `data/contracts.csv` diff (`git diff` against the prior commit, or the relay bundle's patch file) to confirm the applied edits read correctly.
2. Decide whether to authorize a short, targeted follow-up audit-and-approval cycle for the newly-discovered Somerville `binding_arbitration_statute` anomaly before correcting it — do not fix it without going through the same audit-then-approve process used for everything else in this two-session cleanup arc.
3. Only after the above, resume research planning, future source acquisition, or GABRIEL/attribute design — each still requires its own explicit authorization; none is granted by this cleanup session.

---

## 2026-07-05 - Metadata cleanup audit completed (audit-first; no production edits)

**Did**
- Confirmed the prior citation-audit session's changes (`b18d6bd`, "Audit public sector impasse arbitration sources") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_audit_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows)
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (one concise status note added to the top of §11; the 7 tracked issues themselves were not rewritten)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Conducted the audit-first metadata-cleanup review queued at the end of every session since the national scan: verified the 7 metadata issues already tracked in the living checklist's §11, plus 3 newly-scoped issues (broader `comparability_clause_flag` audit, `occupation_class`/unit-title spot check, light provenance-field consistency check), directly against `data/contracts.csv` (via `csv.DictReader`, field by field) and, where useful, the underlying corpus PDFs (`pdftotext` + targeted `grep`, read-only, output kept in a session scratch directory only).
- **Most consequential finding:** `comparability_clause_flag` is unreliable corpus-wide — all 7 currently-flagged rows capture non-wage "comparable" language (drug-testing standards, workers'-comp medical-provider continuation, health-insurance plan parity, work-group-realignment eligibility), and for two of them (the Somerville JLMC award rows) the genuine peer-wage-comparability text ("wages and benefits of comparable towns") is demonstrably sitting one field over, in `arbitration_clause_text`, uncaptured by `comparability_text`.
- **Second major finding:** the Boston `clerical_admin` row's metadata anomaly (already flagged qualitatively in the checklist) is sharper than previously documented — it is a three-field misplacement (`total_comp_note` holds a bare JLMC citation; `longevity_detail` holds what should be `total_comp_note`'s content; `binding_arbitration_statute` holds `"clean"`, a `text_quality` value), plus a likely-miscoded `interest_arbitration_flag=1` on a row whose captured clause text is pure grievance-procedure definitions.
- **Third finding:** `interest_arbitration_flag=1` co-occurs with grievance/discipline-only arbitration text on 4 of 6 flagged rows (Boston clerical/admin; both Arlington `public_works` cycles; Seekonk `public_works`, whose own clause states "Final binding arbitration will prevail on grievances only") — confirming and enumerating the pattern the checklist had already flagged qualitatively.
- Confirmed, with concrete evidence, that 3 of the 7 originally-tracked issues (Seekonk clerical/admin's school-committee affiliation, `public_works` bundling variation, Worcester's successor-MOA/incorporation-by-reference limitation) require **no further action** — the relevant `total_comp_note` fields already document each of these clearly. Confirmed the teacher-aide/paraprofessional-merge risk is not realized in the current single `teacher` row (the Seekonk Educators Association contract explicitly places teacher aides outside the bargaining unit, under School Committee determination).

**Decisions and why**
- Produced a machine-readable proposed-edit table (20 rows: 16 marked `production_edit_needed=yes`, 3 `needs_followup`, 1 a schema/docs-only clarification) rather than editing `data/contracts.csv` directly, per this session's explicit audit-first, no-production-edit mandate.
- Flagged the Boston row's proposed `binding_arbitration_statute` correction ("MA G.L. c. 150E") as medium-high, not full, confidence, and explicitly recommended direct re-verification against the source PDF before any future session writes it, rather than asserting it outright from pattern-matching and an in-row OCR/typo clue alone.
- Surfaced two schema-level decisions (whether `comparability_clause_flag` should require wage-specific language; which `retrieval_method` value best fits a FOIA-obtained-but-now-openly-re-hosted document) as `needs_followup` items for human judgment, rather than resolving them unilaterally, since they affect the correct proposed value for multiple rows.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any document; did not recommend a PRR.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The `comparability_clause_flag` finding was more severe than the checklist's existing single-city (Arlington) framing suggested: it is a corpus-wide pattern (7 of 7 flagged rows), not an Arlington-specific quirk, and in the Somerville case the correct text was already present in the dataset, just in the wrong field — meaning re-extraction, not new source acquisition, is what closes it.

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

**No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. No production data/corpus changes were made — `data/contracts.csv` and `data/city_coverage.csv` were read-only this session, and no file under `corpus/` or `inbox/` was modified. Prior citation-audit changes (`b18d6bd`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Review `metadata_cleanup_proposed_edits_2026-07-05.csv` and resolve the 3 `needs_followup` schema-scope decisions (comparability-flag wage-specificity; interest-arbitration-flag definition already resolved as a docs clarification; FOIA-vs-public_download retrieval-method convention), then authorize a narrowly-scoped production-edit session limited to exactly the 16 flagged rows/fields.
2. That future production-edit session should re-verify the Boston `binding_arbitration_statute` proposed value directly against `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` before writing it, run `python scripts/validate.py` immediately after editing, and confirm no `data/city_coverage.csv` update is needed (none of the proposed edits touch `occupation_class`, cycle dates, or `obs_id`).
3. Do not begin a GABRIEL run, OEWS/municipal descriptive baseline build, or new ingestion until the metadata cleanup pass above is either completed or explicitly deprioritized.

---

## 2026-07-05 - Public-sector impasse/arbitration state-law citation audit completed

**Did**
- Confirmed the prior national-scan session's changes (`41d10b1`, "Add national municipal workforce mechanism scan") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/public_sector_impasse_arbitration_state_law_citation_audit_2026-07-05.md`
  - `docs/analysis/public_sector_impasse_arbitration_state_law_table_2026-07-05.csv`
- Updated:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md` (small, targeted patches only: corrected Wyoming to fire-only with primary citation; sharpened the Iowa description to a general public-employee mechanism with its own 2017 safety-favoring asymmetry; added citation-audit pointers to the JLMC-pattern table row and the NC/SC/VA bargaining-rights paragraph — did not rewrite the memo)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (concise additions to XC09 and XC10 only; did not rewrite the checklist)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H7, H17 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Audited the national scan's public-sector impasse/arbitration claims against primary legal sources (state statutes, state labor-relations-agency guidance) for 12 required states (Massachusetts, New Jersey, New York, Michigan, Rhode Island, Pennsylvania, Wyoming, Oklahoma, Iowa, North Carolina, South Carolina, Virginia) plus two contrast states (Wisconsin, Illinois), producing a citation-supported state-law table that separates confirmed statutory sources, secondary summaries, and needs-follow-up claims.

**Decisions and why**
- Corrected, rather than preserved, an imprecise claim: the original national scan cited "Wyoming" generally for compulsory police/fire arbitration; this audit found a confirmed primary statute (W.S. §§27-10-101 to -109) covering fire fighters only, with no comparable Wyoming police statute found, and patched the scan accordingly.
- Discovered and documented a materially more nuanced Iowa finding than the prior session's framing: Iowa Code §20.22 is a general, all-covered-public-employee binding arbitration statute (not teacher-specific) that predates and survives Iowa's 2017 reform (House File 291), which itself introduced a *different* kind of safety-favoring asymmetry (bargaining-scope and arbitration-criteria restriction for non-safety units, not arbitration-availability restriction) than any pattern documented in this project's Massachusetts corpus. Treated this as strengthening, not weakening, the "Iowa counterexample" finding, while adding real precision to it.
- Flagged South Carolina's public-sector bargaining prohibition as supported only by secondary-source consensus, not a clean primary statute comparable to North Carolina's G.S. 95-98, rather than asserting equal confidence for both states.
- Surfaced and prominently flagged a currently unsettled legal development (Wisconsin's December 2024 Dane County ruling striking down Act 10's police/fire bargaining exemption as an equal-protection violation) as directly relevant to this project's "public-safety institutional privilege" framing, sourced only from secondary/journalistic reporting and explicitly marked as such.
- Made only small, targeted edits to the national scan, living checklist, and hypothesis matrix, consistent with the task's explicit instruction not to rewrite any of them.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, any OEWS/BLS download/build, any metadata edit, or any ingestion.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The Iowa finding was the most significant surprise: what the prior session treated as a single "teacher exception" data point turned out, on closer primary-source inspection, to be a richer and more analytically useful case — a state whose general compulsory-arbitration mechanism confirms the counterexample while its 2017 reform independently illustrates an entirely different wage-restraint lever (scope/criteria restriction) than anything in this project's own corpus.

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

**No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. No production data/corpus changes were made. No metadata edits were made to `data/contracts.csv` or any other production file. Prior national-scan changes (`41d10b1`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Conduct the metadata-cleanup audit of the 7 issues tracked in `wage_mechanism_evidence_checklist.md` Section 11 — audit-first, confirming each issue against the underlying source document before any direct edit to `data/contracts.csv`. This remains the next queued task; this citation audit was a parallel institutional-verification task, not a substitute.
2. If future capacity allows, close the follow-up items flagged in this audit: South Carolina's primary statute, Wyoming's police-specific equivalent (if any), Rhode Island's possible teacher-specific chapter, Pennsylvania's non-safety strike-right claim, and Wisconsin's primary Act 10 text and court opinion.
3. Continue updating `wage_mechanism_evidence_checklist.md` in place after any future corpus scans, OEWS/DESE/BLS descriptive baseline, or GABRIEL extraction run.

## 2026-07-05 - National municipal workforce mechanism scan completed

**Did**
- Confirmed the prior living-checklist session's changes (`7557e59`, "Create wage mechanism evidence checklist") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (added national-scan findings to specific mechanism rows in place — PD01, PD12, FD03, FD12, TC10, TC12, DP12, CA01, CA03, CA13, XC09 — without overwriting the existing table structure; verified every edited row still has 13 pipe delimiters/12 columns)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note confirming the scan is complete and the next step is the metadata-cleanup audit)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H1, H6, H9, H11 only; no new rows, since no wholly new national mechanism was identified — the scan sharpened and qualified existing hypotheses rather than revealing a missing one)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Conducted bounded public-source desk research across all five occupation groups to distinguish general U.S. municipal wage-setting mechanisms from Massachusetts-specific institutions. Key findings: compulsory police/fire interest arbitration (JLMC's underlying policy pattern) is confirmed to recur in at least NJ, NY, MI, RI, PA, WY, and OK, not unique to Massachusetts; the general school-finance foundation-formula architecture behind Chapter 70 is the dominant national model (confirmed via Urban Institute and state examples in NJ and WI); NFPA data quantifies the national volunteer-firefighter decline directly (897,750 in 1984 to 676,900 in 2020); MissionSquare/SLGE survey data shows police staffing difficulty is real but not the single hardest local-government occupation to fill nationally; formal civil-service classification-and-reclassification-appeal architecture (the basis of Boston's clerical/admin mechanism) is a national norm, not a Massachusetts invention; and at least one state (Iowa) is a documented counterexample to the "non-safety lacks compulsory arbitration" finding for teachers, while DPW's and clerical/admin's "no JLMC access" finding presumes bargaining rights exist at all, which is false in NC, SC, and pre-2020 VA.

**Decisions and why**
- Updated the living checklist in place rather than creating a new dated summary, per its own update protocol; added `confirmed in external sources` status only where the national scan found credible, citable support, and explicitly left project-specific claims (e.g., gendered occupational valuation for this project's own cities) at their prior, more cautious status even where the general academic literature became better anchored.
- Flagged, rather than silently resolved, an internal source-reliability discrepancy: one secondary legal-reference source described Massachusetts's own teacher impasse process in terms that conflict with this project's own primary-source (Mass.gov DLR) verification; treated the primary-source Massachusetts finding as authoritative and the secondary source as an illustration of why tertiary summaries need independent verification, not as grounds to revise the Massachusetts-specific finding.
- Made only 4 small, targeted hypothesis-matrix edits (H1, H6, H9, H11) rather than adding new rows, since every national finding this session sharpened or qualified an existing hypothesis rather than revealing a genuinely new mechanism family.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, any OEWS/BLS download/build, any five-city web pilot, or any metadata edit; did not ingest any document.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The clearest generalizability finding of the session was that the *institutional pattern* behind JLMC (a no-strike-for-compulsory-arbitration trade specific to police/fire) recurs in a meaningful set of other states, even though the specific administrative vehicle (JLMC itself) is Massachusetts-only — a nuance this project's prior memos had implicitly assumed but never directly tested until this session.

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

**No GABRIEL/model/API/proxy calls occurred. No OEWS/BLS downloads occurred. No ingestion occurred. No production data/corpus changes were made. No metadata edits were made to `data/contracts.csv` or any other production file. Prior living-checklist changes (`7557e59`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Conduct the metadata-cleanup audit of the 7 issues tracked in `wage_mechanism_evidence_checklist.md` Section 11 — audit-first, confirming each issue against the underlying source document before any direct edit to `data/contracts.csv`.
2. Continue updating `wage_mechanism_evidence_checklist.md` in place after any future corpus scans, OEWS/DESE/BLS descriptive baseline, or GABRIEL extraction run, per the checklist's own update protocol.
3. Keep national-general and Massachusetts-specific evidence explicitly distinguished in any future PI-facing synthesis, per this session's core finding that institutional patterns (compulsory arbitration; foundation-formula school finance; civil-service classification appeals) generalize even where the specific named Massachusetts vehicles (JLMC, Chapter 70, Proposition 2½) do not.

## 2026-07-05 - Living wage-mechanism evidence checklist created

**Did**
- Confirmed the prior clerical/admin corpus-scan and Massachusetts clerical/admin impasse-context session's changes (`41be1b3`, "Scan clerical admin corpus and clarify impasse context") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (undated, living reference file)
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note pointing to the new checklist, its update discipline, and the next planned steps)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Consolidated every wage-mechanism hypothesis developed across all prior sessions (police, fire, teachers, DPW/public works, clerical/admin, and cross-cutting mechanisms — 27 hypothesis-matrix rows plus several additional cross-cutting and source-family entries) into one working checklist with a defined status vocabulary (`not searched`, `partially searched`, `confirmed in current corpus`, `confirmed in external sources`, `weak evidence`, `not found in current corpus`, `contradicted`, `needs metadata cleanup`, `not applicable`), a 12-column table structure (mechanism_id, mechanism, occupation_group, wage_pressure_direction, plausible_channel, evidence_that_would_support, evidence_that_would_weaken_or_contradict, best_source/document_types, current_repo_evidence, verification_status, next_action, notes), a source/document-type inventory, a current-corpus-evidence summary, a tracked (not corrected) list of known metadata-cleanup issues, and an update protocol for future sessions.
- This was a synthesis and repo-organization session only: no new broad web research was conducted, and every mechanism row was sourced from an existing memo rather than new investigation.

**Decisions and why**
- Built the checklist as a pointer-and-summary layer over the existing occupation-specific memos, not a replacement for them — every cell that makes a substantive claim links back to the memo where the underlying evidence and citations live, so this file stays usable without re-deriving every finding from scratch.
- Tracked known metadata-cleanup issues (the Arlington `public_works` comparability-flag mismatch, the Boston `clerical_admin` field-alignment anomaly, the `interest_arbitration_flag` naming-vs-usage gap, and others) explicitly without correcting any of them, consistent with this session's audit-first, no-metadata-edit boundary.
- Did not do new broad web research; the one clarification lookup performed (confirming the exact list of hypothesis IDs currently in `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv`) was a repo-internal check, not external research.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, any OEWS/BLS download/build, any national web scan, or any metadata edit.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- Assembling all five occupation groups side by side in one table made the arbitration/impasse-backstop finding (XC09 in the new checklist) unusually visible as the single most thoroughly cross-verified finding in the project to date: JLMC's compulsory interest arbitration is confirmed, independently, to be unique to police/fire, with teachers, DPW, and clerical/admin all separately verified to share the same Chapter 150E Section 9 route.

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

**No GABRIEL/model/API/proxy calls occurred. No national web scan or five-city web pilot was run. No OEWS/BLS downloads occurred. No ingestion occurred. No production data/corpus changes were made. No metadata edits were made to `data/contracts.csv` or any other production file. Prior clerical/admin corpus-scan/impasse-context changes (`41be1b3`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Run the national qualitative scan across police, fire, teachers, DPW/public works, and clerical/admin, per `non_safety_comparison_roadmap_2026-07-04.md`.
2. After the national scan, conduct a metadata-cleanup audit of the issues tracked in `wage_mechanism_evidence_checklist.md` Section 11 — audit-first (confirm each issue against the underlying source document) before any direct edit to `data/contracts.csv`.
3. Update `wage_mechanism_evidence_checklist.md` in place after the national scan, the metadata-cleanup audit, any future corpus scans, and any future OEWS/DESE/BLS descriptive baseline or GABRIEL extraction run, per the checklist's own update protocol (Section 12).

## 2026-07-05 - Clerical/admin existing-corpus scan and Massachusetts impasse context verified

**Did**
- Confirmed the prior clerical/admin mechanism session's changes (`75b8c22`, "Refine clerical admin wage mechanisms") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md`
  - `docs/analysis/ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md` (light edit: closed gap items 3 partially, 4, 13, and 15 with verified findings)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added a second clerical/admin update note confirming both open items are now resolved)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H23, and H24 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Closed the two immediate clerical/admin uncertainties flagged at the end of the prior clerical/admin mechanism session: (1) whether Massachusetts clerical/admin bargaining has any special JLMC-like backstop, and (2) whether this project's already-collected `clerical_admin` CBAs actually contain the classification, reclassification, compression, and workload language the clerical/admin mechanism map hypothesizes.
- Reviewed `data/contracts.csv` (read-only) to identify all three `clerical_admin` occupation-class rows across three cities (Worcester, Boston, Seekonk), confirmed all three corpus files exist on disk, and read their content in full (native `pdftotext` extraction for Worcester and Boston, plus a prior session's ad hoc, read-only OCR pass reused for Seekonk's image-only file). No files were added to `corpus/` and no rows were added to or edited in `data/contracts.csv`.
- Verified via the Massachusetts Municipal Association's Select Board Handbook that clerical and administrative employees are explicitly named as ineligible for JLMC services, and cross-confirmed this against the project's own corpus (Seekonk's `binding_arbitration_statute` field cites MA G.L. c. 150E; Boston's contract text shows only narrow-scope arbitration rights, none JLMC-style).

**Decisions and why**
- Found and precisely flagged a `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row: a stray "MA G.L. c. 1078 (JLMC)" citation sits in the `total_comp_note` field (not `binding_arbitration_statute`), which could be misread as evidence of JLMC coverage. Verified directly against the actual contract text that no JLMC reference exists anywhere in the document, and flagged this as a data-quality observation without correcting `data/contracts.csv`, consistent with this session's review-only scope.
- Surfaced a new institutional wrinkle not documented for teachers or DPW: some Massachusetts municipal administrative positions closest to executive leadership (Select Board/town manager office staff) are "confidential employees" excluded from collective bargaining entirely, meaning their pay is set unilaterally rather than through any bargaining or impasse process.
- Documented Boston's Compensation Grade Appeals (CGA) reclassification process in full, including its explicit, doubly-stated exclusion of workload/technology-driven duty changes as valid reclassification grounds — a sharper, more precisely restrictive finding than the prior session's lighter read anticipated for the `clerical_admin_automation_reorganization` discussion.
- Made only three small, targeted hypothesis-matrix edits (H6, H23, H24) rather than adding new rows or editing many rows, consistent with the standing preference to improve the existing map with small edits.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any new document.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- Boston's clerical/admin CBA was substantially richer than the prior session's light read anticipated: it documents the most procedurally restrictive reclassification mechanism found anywhere in this project's corpus to date (arbitration limited to an "arbitrary or capricious" standard), a CDL stipend embedded in a nominally clerical/admin unit, and a documented departmental-merger history revealing the unit spans far more than clerical titles (recreation, facilities, grants, network administration).

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

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made. Prior clerical/admin mechanism changes (`75b8c22`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Move to the national qualitative scan across police, fire, teachers, DPW, and clerical/admin per `non_safety_comparison_roadmap_2026-07-04.md`, since both clerical/admin uncertainties flagged at the end of the prior session are now resolved.
2. If a clerical/admin-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in `non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md` Section 6, and treat pay-compression, workload/backlog, and recruitment/retention framing as requiring new source acquisition rather than further review of already-collected documents.
3. Flag the `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row for a future data-quality pass; do not correct it in a review-only session.

## 2026-07-05 - Clerical/admin wage mechanism refinement developed

**Did**
- Confirmed the prior DPW corpus-scan and Massachusetts DPW impasse-context session's changes (`d1b4969`, "Scan DPW corpus and clarify impasse context") were already committed, with only `tmp/` left untracked; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_wage_mechanism_refinement_2026-07-05.md`
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added a clerical/admin findings update note, including the recommendation for a national qualitative scan as the next major step)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added 5 new rows H23-H27: `clerical_admin_classification_restraint`, `clerical_admin_reclassification_pressure`, `clerical_admin_pay_compression`, `clerical_admin_service_backlog_absorption`, `clerical_admin_lower_public_salience`; lightly extended H17's counterpoint field to note the clerical/admin extension)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Developed clerical/administrative municipal work as the third non-safety comparison group per the existing roadmap: the "plainest" non-safety comparison, lacking both teachers' credentialing/salience cover and DPW's operational/licensing cover, which makes it the best available test of what wage-setting institutions can restrain on their own.
- Used bounded web search across national sources (MissionSquare Research Institute's 2024 local-government recruitment/retention reporting citing BLS JOLTS data; The Century Foundation's minimum-wage-compression cost estimate, which explicitly includes Massachusetts as one of six jurisdictions analyzed; Mass.gov's Efficiency and Regionalization shared-services grant program with concrete Massachusetts examples; general municipal-software-vendor material on permitting/records automation) and a light, illustrative read (not a full corpus scan) of this project's three already-collected `clerical_admin` corpus rows (Worcester, Boston, Seekonk), using the project's existing `pdftotext` extraction plus a session-local, read-only `tesseract` OCR pass for the one image-only Seekonk file.

**Decisions and why**
- Treated clerical/admin as a multi-title category (clerk/senior clerk/principal clerk, administrative/executive assistant, office manager, payroll/accounting staff, assessor/collector/treasurer staff, town/city clerk staff, school administrative assistants, department-nested clerical roles, supervisors) throughout, mirroring the composition discipline already established for teachers and DPW.
- Found and foregrounded a concrete, corpus-grounded reclassification mechanism: Boston's clerical/admin CBA documents a formal "OHR Classification and Compensation Unit" review process for reclassification applications, with management rights explicitly reserved over reorganize/reclassify decisions — used this as the basis for two new hypotheses (`clerical_admin_classification_restraint`, `clerical_admin_reclassification_pressure`) rather than treating reclassification as purely speculative.
- Identified that this project's Seekonk `clerical_admin` row (Administrative Secretaries) is specifically a school-based unit (references to School Committee and Superintendent in its own contract text), directly illustrating the task's instruction to distinguish school administrative assistants from general municipal clerical staff within the same occupation class.
- Flagged gendered occupational valuation explicitly as a hypothesis requiring dedicated evidence, not an established fact about this project's cities, per the task's explicit instruction to handle this carefully and without unsupported claims.
- Added exactly the 5 hypothesis rows suggested in this session's task brief (including `clerical_admin_lower_public_salience` as its own row, unlike the DPW session where the analogous salience hypothesis was folded into an existing row) and made one small extension to H17's counterpoint field, consistent with the instruction to prefer a small number of high-value additions.
- Did not touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/`; did not run GABRIEL, model/API calls, the Harvard proxy, or any OEWS/BLS download/build; did not ingest any new document.

**Surprises/breakage**
- No repo breakage from this session.
- Validation and coverage audit remained unchanged, confirming the work stayed outside ingestion and production data changes.
- The Century Foundation's minimum-wage-compression cost estimate explicitly covering Massachusetts (alongside California, New York, New Jersey, Illinois, and DC) was a genuinely useful, directly quantified, multi-state-inclusive finding that sharpened the pay-compression mechanism well beyond what analyst judgment alone would have supported.

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

**No GABRIEL/model/API/proxy/OEWS/ingestion actions occurred in this session. No production data/corpus changes were made. Prior DPW corpus-scan/impasse-context changes (`d1b4969`) were already committed excluding `tmp/`; confirmed, not recommitted.**

**Next steps**
1. Verify whether Massachusetts clerical/admin bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers and DPW (highly likely by the same institutional logic, but not directly re-verified for clerical/admin specifically this session).
2. Conduct a full document-by-document review of this project's three already-collected `clerical_admin` corpus rows, mirroring the dedicated DPW corpus-scan session, since this session's read was intentionally light and illustrative only.
3. Move to a national qualitative scan across police, fire, teachers, DPW, and clerical/admin per `non_safety_comparison_roadmap_2026-07-04.md`, now that all three non-safety comparison groups (teachers, DPW, clerical/admin) have an initial mechanism map in place.

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
