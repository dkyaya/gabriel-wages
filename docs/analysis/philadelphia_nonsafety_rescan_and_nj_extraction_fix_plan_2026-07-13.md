# Philadelphia Non-Safety Re-Scan and NJ Extraction Fix Plan — 2026-07-13

Claim-driven memo, per `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md`. Two parts: (A) a detailed Philadelphia non-safety re-scan, with a Harrisburg/Pittsburgh fallback trigger that was not met; (B) an audit-first diagnosis and fix plan for the recurring NJ deterministic-extraction issues in `wage_mechanism_evidence_checklist.md` §15 items 8-13.

## 1. Current question

**Part A:** Can Philadelphia be upgraded from an exploratory-adjacent design into a genuinely useful matched-comparison city by finding a non-safety agreement overlapping the police window (2025-2027) or the fire window (2017-2020)? If not, is Harrisburg or Pittsburgh a better replacement target?

**Part B:** Why is the deterministic (regex-only) mechanism extractor producing recurring false positives and inversions specifically on New Jersey police/fire CBAs, and what is a concrete, auditable fix?

## 2. Evidence found

### Part A — Philadelphia

- **AFSCME Local 2187** (a DC47-affiliate local representing City of Philadelphia, Philadelphia Housing Authority, and Philadelphia Parking Authority employees — confirmed via independent reporting, e.g. PhillyVoice) hosts its own official "Contract Library" page. It contains a direct PDF: a "Term Sheet Agreement Between The City of Philadelphia and AFSCME District Council 47, Locals 2186 and 2187," term **July 1, 2025 — June 30, 2028**.
- This document (`https://www.afscme2187.org/_files/ugd/749f21_a8b8e0089c234877bbceb1f8833a82cb.pdf`) contains a bilateral, dated signature block ("FOR THE CITY OF PHILADELPHIA: / FOR AFSCME DISTRICT COUNCIL 47:", dated on or around 8/1) and substantial negotiated content (wages, ratification bonus, health & welfare fund lump sum, sick leave, bereavement, parental leave, working-out-of-class, legal services fund, a genuine Most-Favored-Nation/me-too clause pegging DC47's raise to DC33's).
- Ratification of this same tentative agreement is independently corroborated by contemporaneous news coverage (PhillyVoice, Philadelphia Inquirer, ~July 2025 — "white-collar city union approves contract").
- **This cycle overlaps the already-ingested Philadelphia police row (2025-2027) for the police row's entire term.** `ingest/audit_coverage.py` now reports this as a healthy **overlap-cycle matched pair**, not merely exploratory-adjacent.
- Recognition-clause-first review: Local 2187 covers general/white-collar City of Philadelphia + PHA + PPA employees; Local 2186 covers supervisors across city agencies — a mixed, multi-agency, multi-title unit. Classified `occupation_class=other`, consistent with the DC33 row already in the corpus.
- **The fire window (2017-2020) remains unresolved.** DC33's already-ingested cycle (2021-2024) and DC47's newly-ingested cycle (2025-2028) both postdate it; a 2018 `phila.gov` press release confirms a DC47 contract cycle existed covering roughly 2017-2020 ("City & DC 47 Reach Tentative Three Year Contract," retroactive to July 1, 2017 per news coverage), but no document for that specific cycle was locatable this session — checked `phila.gov/personnel/laborrel/47term.htm`, `dc47.org`, and AFSCME Local 2187/2186's own sites without success.
- **Rejected candidates, with reasons:**
  - DC33's `termsheet_0.pdf` (2025-2028 cycle) — a bare term sheet with no located signature evidence; rejected as a summary (unchanged from Wave 1).
  - DC33's `2024-2025oneyearextension.pdf` — cycle (~July 2024-June 2025) does not overlap either target window even if pulled; not pursued.
  - A `phila.gov`-hosted 2024-2025 DC33 one-year-extension document (filed as a public-records-discovery attachment) — same non-overlapping cycle issue; not pursued.
  - `dc47.org/contracts/` — returns 404; no direct contracts navigation found on the main DC47 domain.

### Part A — Harrisburg/Pittsburgh fallback

**Not triggered.** The task's explicit instruction was: "If Philadelphia remains fruitless, move immediately to a bounded PA fallback scan." Philadelphia is no longer fruitless — it now has a genuine overlap-cycle matched pair (police). Per the task's own conditional logic, the Harrisburg/Pittsburgh fallback scan was correctly not performed this session. This is a deliberate scope decision, not an oversight, and is flagged here explicitly so a future reader does not mistake the absence of a Harrisburg/Pittsburgh scan for an unaddressed task item.

### Part B — NJ extraction diagnosis

Read `ingest/extract_spans.py` directly (the deterministic Stage-1 regex extractor; no LLM/GABRIEL involved in any of the flagged rows — all six items 8-13, plus a newly-found item 14, were produced by regex alone).

**Root cause 1 — `interest_arbitration` triggers are too broad and context-blind:**
```python
"interest_arbitration": [
    r"\binterest arbitration\b",
    r"\bbinding arbitration\b",       # <- fires on ANY binding-arbitration clause
    r"\blast best offer\b",
    r"\bfinal[- ]offer arbitration\b",
    r"\bimpasse\b.{0,40}\barbitration\b",
],
```
`\bbinding arbitration\b` alone is sufficient to set the flag. It does not distinguish wage-setting interest arbitration from ordinary grievance/dispute arbitration over anything — legal-defense coverage disputes (`nj_newark_police_2018`), health-plan-definition disputes (`nj_trenton_police_2019`), or general contract-interpretation disputes. This single trigger is directly responsible for items 10 and 12, and contributed to the historical MA item 6 (already partially resolved 2026-07-05).

**Root cause 2 — no negation/exclusion awareness:**
The regex only checks for the *presence* of a trigger phrase within a paragraph; it never checks whether the surrounding sentence *negates* it. Both documented inversions follow the identical pattern — the flagged text explicitly excludes the unit from interest arbitration, and the regex still returns `flag=1`:
- `pa_philadelphia_other_2021` (item 9): "...but not employees who are eligible for interest arbitration..."
- `nj_trenton_fire_2021` (item 13): "Fiscal matters as wages, hours, and benefits are **not** subject to interest arbitration..."
- **Newly found this session, `pa_philadelphia_other_2025` (item 14):** the flagged text is a genuine Most-Favored-Nation clause (correctly flagged `me_too_clause_flag=1`) that merely *references* "bargaining units entitled to interest arbitration" as an exclusion category when scoping the comparison — not evidence DC47 itself has interest arbitration.

**Root cause 3 — `comparability` trigger is a bare word-root wildcard:**
```python
"comparability": [
    r"\bcomparab\w+\b",                # <- fires on ANY use of "comparable"/"comparability"
    ...
],
```
This fires on internal rank comparisons (`nj_newark_fire_2013`, item 11: "members of comparable rank"), benefits-plan comparisons (`nj_trenton_fire_2021`, item 13: "Optical Plan comparable to..."), and — from the pre-existing, already-resolved item 1 — health-insurance "comparable plan" clauses. None of these are peer-jurisdiction wage comparability, the substantive concept the schema field is meant to capture (per `docs/schema.md`'s own field note and the 2026-07-05 authorized redefinition).

**Why NJ specifically, if the weakness is general:** New Jersey's police/fire interest arbitration runs through an *external* statutory process (the NJ Police and Fire Public Interest Arbitration Reform Act, N.J.S.A. 34:13A-14 et seq.), not a clause embedded in the CBA itself. Consequently, NJ CBAs' own "arbitration" articles are almost always ordinary grievance arbitration, and when they *do* mention "interest arbitration," it is frequently to explicitly exclude it from the CBA's internal grievance-arbitration scope (since that topic is handled elsewhere, by statute). This means the general regex weakness (root causes 1-3, which are state-agnostic) manifests at a much higher rate specifically on NJ documents. The underlying code defect is not NJ-specific; its *symptom concentration* is.

## 3. Reasoning

The Philadelphia finding directly tests `H1`/`H2`/`H6`/`H7` (safety-pressure-conversion channels; arbitration backstops; institutional generalizability of the Ohio matched-triad pattern) in a second large city outside Ohio, now with a genuine cycle-overlapping non-safety comparator for the police leg specifically — not just occupation-class presence. This is the strongest single upgrade available this session, and it required exactly the document-level, primary-source-first discipline the task asked for (a union local's own "Contract Library," not a search-engine snippet) — the same discipline that caught the Reading "library CBA" false positive in a prior wave.

The NJ extraction diagnosis explains a real, structural weakness rather than a coincidence: every one of the six prior flagged items, plus the newly-found seventh (item 14), traces to one of exactly three narrow code patterns (bare "binding arbitration," no negation check, bare "comparable\w+"). This is good news for a fix — it is not six unrelated bugs, it is three.

## 4. Counterevidence / limits

- The Philadelphia DC47/Local 2187 document is a **compiled "contract library" packet**, not a single uniformly-executed instrument: the located signature block is tied to a specific Section 7/Exhibit-A incorporation clause, and several appended side letters within the same PDF still carry unresolved "[signature page to follow]" placeholders. Treated as executed based on the totality of evidence (persistent union hosting + external ratification news coverage + substantive negotiated content), not certainty — flagged explicitly in the row's `total_comp_note`.
- Philadelphia's fire window (2017-2020) remains genuinely unresolved — this re-scan closed the police gap, not the fire gap. Philadelphia is now a **matched pair (police)** plus one still-exploratory-adjacent leg (fire), not a fully matched triad in the cycle-overlap sense.
- Because the Harrisburg/Pittsburgh fallback trigger was not met, this session has **no new evidence** on whether either city would in fact be a better or worse candidate than Philadelphia. The claim here is narrower: Philadelphia is no longer fruitless, so the task's own conditional did not require testing the alternative.
- The Part B fix plan is a diagnosis and proposal, not an implemented or tested change. No `extract_spans.py` code was modified and no flagged `data/contracts.csv` rows were corrected this session, per the task's explicit "audit first, recommend specific changes second" instruction.
- The fix plan's negation-guard design is itself a heuristic (keyword-based), not a full parse; it will reduce, not eliminate, false positives, and could in principle introduce new false negatives (suppressing a genuine interest-arbitration mention that happens to co-occur with an unrelated negation cue nearby). This is exactly why a regression check against known-good historical hits (Section 6, item F below) should precede any production change.

## 5. What would change our mind

- **On Philadelphia:** discovering that the DC47/Local 2187 document is *not* actually the executed version (e.g., a cleaner, differently-dated final copy exists elsewhere showing different terms) would require re-verifying the overlap claim. A located 2017-2020-era Philadelphia non-safety document would close the remaining fire-window gap.
- **On the fix plan:** if a regression run (Section 6, item F) shows the proposed negation/co-occurrence guards suppress genuine positives currently relied upon in the claim register (e.g., Toledo police, San Antonio police, Somerville's comparator row), the specific guard thresholds (window size, cue list) would need to be revised before authorization, not the overall diagnosis.

## 6. Source needs

- A Philadelphia non-safety source (any DC33/DC47 predecessor local or cycle) covering 2017-2020, to close the fire-window gap.
- If a future session revisits the Harrisburg/Pittsburgh question independently of the Philadelphia trigger (e.g., simply to broaden PA beyond one city), a fresh targeted scan for police/fire/one general-municipal unit in each, per the same document-level discipline used here.
- For Part B: explicit authorization to (a) modify `ingest/extract_spans.py` per the fix plan below, and (b) run a regression check against the full set of currently-flagged rows (items 1, 6, 8-14) plus a sample of currently-*unflagged*, presumed-genuine positive rows, before any change is applied to production extraction.

## Recommended fix plan (Part B, not yet implemented)

**A. Narrow the `interest_arbitration` triggers.** Retire `\bbinding arbitration\b` as a standalone sufficient cue. Require it to co-occur (same paragraph, or a ~150-char window) with wage/impasse-specific vocabulary: `wages`, `salary`, `compensation`, `impasse`, `successor agreement`, or a named interest-arbitration statute/body (`Act 111`, `N.J.S.A. 34:13A`, `PIA Reform Act`, `JLMC`, `G.L. c. 1078`). Keep `\blast best offer\b`, `\bfinal[- ]offer arbitration\b`, and `\bimpasse\b.{0,40}\barbitration\b` as-is — no false positives observed on these three across the full corpus to date.

**B. Add a negation/exclusion guard.** Before setting any flag from a matched trigger, scan a short window around the match (same sentence, or ~80 chars preceding it) for negation/exclusion cues: `not subject to`, `excluded from`, `does not apply to`, `shall not (?:be submitted|apply|include)`, `other than`, `except`, `not including`, `not entitled to`. If present and modifying the trigger phrase, do not set the flag from that occurrence; continue scanning for a genuine (non-negated) occurrence elsewhere in the document before deciding the final flag value. This single guard would have caught both documented inversions (items 9 and 13) and the newly-found item 14.

**C. Require a referent match for `comparability`.** Currently `comparability_referent` is populated best-effort from `REFERENT_PATTERNS`, but the *flag* is set from the bare `\bcomparab\w+\b` hit regardless of whether a referent was found. Change: only set `comparability_clause_flag=1` when a `REFERENT_PATTERNS` match succeeds (peer-jurisdiction/wage-specific language). A bare "comparable" hit with no referent match should remain `unresolved` (eligible for LLM-fallback review later, not a firm deterministic positive). This single change would have suppressed items 1, 8, 11, and the comparability half of item 13.

**D. Structural note, not proposed for this session:** the schema has only one arbitration-type field pair (`interest_arbitration_flag`/`arbitration_clause_text`), so any grievance/discipline/benefits-dispute arbitration clause currently has nowhere else to be captured except mislabeling as interest arbitration. A parallel `grievance_arbitration_flag`/`grievance_arbitration_text` field pair would be the most complete structural fix, but this is a schema change requiring explicit PI/user authorization (per the standing "no schema changes are authorized without explicit approval" convention) and is **not** proposed for implementation here — flagged for future consideration only.

**E. NJ-specific guardrail (documentation, not code):** recommend adding a note to `docs/schema.md`'s `interest_arbitration_flag` field definition (pending authorization) that `flag=0` on an NJ police/fire CBA should not be read as "this unit lacks interest-arbitration protection" — virtually all NJ police/fire units are covered by the state PIA Reform Act regardless of CBA text, since that process sits outside the CBA. This is a claim-interpretation guardrail for future codify/report work, not an extraction-logic change.

**F. Before any production change:** re-run the regex pass (offline, no re-ingestion) against all 8 currently-flagged rows (items 1, 6 [4 rows], 8-14) as a true-negative regression check, and against known-good positive rows already cited as primary claim support (e.g., `tx_san_antonio_police_2022`, `oh_toledo_police_2024`, `ma_somerville_police_spsoa_2012`) as a true-positive regression check, before authorizing any change to `ingest/extract_spans.py` or any correction to `data/contracts.csv`.

## 7. Recommended next move

**Not another sourcing run, and not a first analytical/codify run — a narrow, already-completed ingestion (documented above) followed by scan/audit-only work.** Specifically:

1. This session already completed one narrowly-scoped ingestion (the Philadelphia DC47/Local 2187 non-safety row) because it cleared the stated gate; no further ingestion is recommended before the next codify-readiness review.
2. The next PA/NJ session should be **audit-only** for Part B: get explicit authorization for the fix plan in Section 6, implement items A-C in `extract_spans.py`, run the regression check (item F), and only then decide whether to correct the seven flagged production rows (items 1 [already resolved], 6 [already resolved], 8-14) — this is metadata cleanup, not new sourcing or codify.
3. Trenton NJ (matched triad, all three legs cycle-overlapping) and now Philadelphia PA (matched pair, police leg) are both ready, design-wise, for a first controlled codify wave — but that wave should wait until after the Part B extraction fix is authorized and applied, so codify runs against corrected deterministic-extraction spans rather than the currently-flagged ones.
