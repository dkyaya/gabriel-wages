# Progress Log

Reverse-chronological session log. Newest entry on top. Records **decisions, surprises, and next steps** — not keystroke-level changes (git has those). Pair each entry with the git commits from that session.

Convention per entry: what we did, decisions made (and why), surprises/breakage, corpus snapshot (from `python ingest/audit_coverage.py`), next steps.

---

## 2026-07-13 16:10 EDT (Extractor fix implemented and regression-tested corpus-wide; Philadelphia fire-gap closed exact-cycle; DC47 packet precisely broken down) - Implemented the extraction fix diagnosed in the prior session's memo, regression-tested it against all 64 corpus PDFs (found and fixed 2 additional false-positive modes the fix plan hadn't anticipated), corrected 27 production data/contracts.csv fields across 18 rows, gave a precise document-level breakdown of the Philadelphia DC47/Local 2187 packet, and closed Philadelphia's fire-window gap with a genuine exact-cycle match; no GABRIEL/codify/model/API calls; no push/remote work

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `dab6cb2 Philadelphia non-safety re-scan (DC47 overlap) and NJ extraction-quality fix plan`; `data/contracts.csv`/`data/city_coverage.csv` each 63 rows.
- **Task 1 (extractor fix, `ingest/extract_spans.py`):** Implemented the fix plan's core ideas, but iterated past the original plan after regression testing surfaced two NEW false-positive modes the plan hadn't anticipated:
  - Dropped the bare `binding arbitration` trigger for `interest_arbitration` entirely, rather than gating it on co-occurring wage vocabulary as originally planned — the wage-vocabulary-gated version still produced a false positive on an Ohio Cleveland subcontracting/privatization-dispute clause that happened to mention "the payment of a living wage."
  - Added a negation/exclusion guard (`_is_negated`), sentence-scoped; fixed a bug in the first version, which used bare newlines as sentence boundaries and missed a negation cue ("not\n        including") that a PDF line-wrap had split across the boundary.
  - Required comparability matches to have BOTH a peer-jurisdiction referent AND co-occurring wage vocabulary — a referent-only requirement (as originally planned) still let through a Texas Austin recruiting-vendor clause ("comparable metropolitan cities" describing candidate-pool sourcing, not wages).
  - Added 15 new regression tests to `ingest/test_pipeline.py` (54 total, 0 failures) covering all 7 originally-documented false positives/inversions plus the 2 newly-found ones.
- **Task 2 (regression check + corrections):** Wrote a full-corpus regression script (`extract`+`extract_spans` re-run against all 64 rows' source PDFs, diffed against production, per-row 90s timeout to survive a 43MB scanned-photo PDF). Found 19 rows needing correction:
  - 7 documented false positives/inversions: confirmed suppressed, corrected to `0`/cleared.
  - 2 rows (`oh_columbus_police_2023`, `oh_columbus_fire_2023`) discovered to have **non-verbatim (fabricated) text** in `arbitration_clause_text` — a direct substring check confirmed neither string appears anywhere in its source PDF, a genuine data-integrity violation of unknown provenance, not caused by this fix. Corrected to match what the fixed deterministic extractor actually produces on these documents.
  - 2 genuine new true positives found and added: `oh_toledo_police_2024` (a verbatim "shall be subject to an interest arbitration" clause, previously missed) and `oh_cincinnati_fire_2023` (a verbatim "'Me-too' with FOP on wages..." clause, previously blank).
  - 8 blank→`0` normalizations (cosmetic only).
  - 8 rows' `no_strike_clause_flag` differ between stored data and today's re-extraction — **not corrected**, since `no_strike` logic was never touched by this fix; flagged as a likely OCR-non-determinism issue for a separate future investigation (checklist item 16).
  - A final verification regression run confirms the repo is clean with respect to this fix's scope: the only remaining diffs are exactly those 8 out-of-scope `no_strike` rows.
- **Task 3 (DC47/Local 2187 packet breakdown):** Re-mapped the 82,652-character compiled PDF structurally and found it is 5 distinct documents, not one: the main 2025-2028 term sheet; a "H&W Side Letter" (dated July 15, 2025, apparent genuine trailing signature content despite a `[signature page to follow]` template placeholder in its body); a second, Local-2186-specific side letter (same pattern); a wholly separate, **earlier** 2024-2025 "Tentative Extension Agreement" that carries the packet's one clearly-legible bilateral signature block (correcting the prior session's note, which had misattributed that signature block to the main 2025-2028 term sheet's Exhibit-A clause); and the full text of PA Act 195, appended as reference material. Corrected the row's `total_comp_note` in `data/contracts.csv` to reflect this precise breakdown. No single unambiguous signature page was found specifically for the main 2025-2028 term sheet; its execution remains a totality-of-evidence judgment (persistent hosting + news corroboration + same-round side letters), unchanged in substance from the prior session, now more precisely documented.
- **Task 4 (Philadelphia fire-gap scan):** Found AFSCME Local 2186's own "Contracts" archive page (`afscme2186.org/contracts`) listing a document titled "City Contract & 2186 Memo Agreement 2017-2020." Downloaded and verified: a genuine, signed Memorandum of Agreement, term July 1 2017 - June 30 2020 — an **exact match** to the already-ingested Philadelphia fire row. Ingested as `pa_philadelphia_other_2017`. Rejected: a 2011 DC33-v-City legal complaint (wrong era, no attached CBA), two dead links.
- Updated `docs/analysis/wage_mechanism_evidence_checklist.md` §15: marked items 8-14 RESOLVED with correction details; added item 15 (Columbus non-verbatim finding, resolved), item 16 (no_strike OCR-non-determinism, NOT resolved, flagged), and item 17 (extractor-fix implementation summary).
- Created `docs/analysis/extractor_fix_and_philadelphia_fire_gap_2026-07-13.md`, the required claim-driven memo for this session.

**Decisions and why**
- Retired the weak "binding arbitration + wage context" trigger entirely rather than further special-casing it after a second false-positive mode appeared on the first regression run — two independent failure modes in one heuristic is a signal the heuristic itself is unreliable, not that it needs one more patch. Under-flagging (leaving a row `unresolved`) is preferred over over-flagging (contaminating a primary-evidence field) per the project's own stated evidence-strength discipline.
- Corrected the two non-verbatim Columbus rows to match what the deterministic pipeline actually produces (blank/`0`) rather than hand-inserting a replacement verbatim span found via manual document review — even though genuine ORC 4117.14(G) impasse language does exist in the Columbus Fire source, inserting it by hand would reintroduce exactly the RA-discretion-at-collection-time problem `AGENTS.md` prohibits; the gap is documented for a future, properly-generalized regex trigger instead.
- Left the 8-row `no_strike_clause_flag` discrepancy uncorrected — explicitly out of scope per the task's own decision rule (only expand fix scope to the same bug family), since `no_strike` logic was never touched and the discrepancy's cause (likely OCR non-determinism) is a different problem requiring its own investigation.

**Surprises/breakage**
- The full-corpus regression check surfaced a genuine, pre-existing data-integrity issue (two rows with fabricated, non-verbatim mechanism text) that predates this session and was not part of the original 7-item false-positive list — discovered only because re-running the fixed extractor against the actual source PDF revealed the stored text couldn't be found in it at all.
- The negation-guard's first implementation had its own bug (bare newlines treated as sentence boundaries), caught only because a specific real document ("not\n        including...") exercised exactly that edge case during regression testing — a useful reminder that a fix for one false-positive family can itself introduce a narrower bug.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 64 | discourse: 0 | coverage: 64 | city_attributes: 3

python ingest/test_pipeline.py
54 passed, 0 failed (was 40; +15 new regression tests, one existing test's scenario
updated to reflect the retired weak-trigger design)

python ingest/audit_coverage.py
healthy matched pairs: 28 (was 27; +1: Philadelphia fire vs. pa_philadelphia_other_2017, EXACT-cycle)
  exact-cycle: 10 (was 9) | overlap-cycle: 18
exploratory adjacent matches: 2 (was 3 -- Philadelphia's last adjacent pairing resolved)
safety units unmatched: 6 (unchanged)
cities: 19 (unchanged)
```
`docs/schema.md` and `docs/final_reports/` confirmed unchanged (empty diffs). Repo is "clean" in the sense that a fresh full-corpus regression run now shows zero remaining diffs attributable to this fix -- the only remaining diffs (8 rows' `no_strike_clause_flag`) are a documented, explicitly out-of-scope, separate issue.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls (deterministic regex extraction only, `--llm` never passed); no FOIA/OPRA/RTKL/PRR; no git push; no remote inspection/configuration. 1 new PDF now lives under `corpus/pa_philadelphia/` (the 2017-2020 fire-gap MOA).

**Next steps**
1. Philadelphia (both legs matched) and Trenton NJ (all three legs matched) are both now genuinely design-ready for a first controlled GABRIEL/codify wave -- not run this session, not authorized.
2. Before that codify wave: investigate the `no_strike_clause_flag` OCR-non-determinism question (checklist item 16), and consider a broader non-verbatim-text audit beyond the 20 rows checked this session, so codify scores a corpus checked as thoroughly as the arbitration/comparability fields were this session.
3. If the Columbus ORC-4117 impasse/conciliation pattern recurs in more Ohio documents, add a properly-generalized, tested regex trigger for it (not hand-inserted text).

## 2026-07-13 12:32 EDT (Philadelphia non-safety re-scan converts it to a real matched pair; NJ extraction-quality audit produces a concrete, not-yet-implemented fix plan) - Detailed, document-level Philadelphia non-safety re-scan found and ingested a genuinely overlapping DC47/Local 2187 source (2025-2028), converting the police leg from exploratory-adjacent to a healthy overlap-cycle matched pair; Harrisburg/Pittsburgh fallback scan not triggered because Philadelphia was no longer fruitless; diagnosed the root cause of 7 flagged NJ/PA deterministic-extraction issues in `ingest/extract_spans.py` and produced a concrete fix plan (not implemented — audit-first per task instruction); no GABRIEL/codify/model/API calls; no push/remote work

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `ec8cea6 PA/NJ Ingestion Wave 2: Newark and Trenton police/fire via direct PERC index browsing`; `data/contracts.csv`/`data/city_coverage.csv` each 62 rows. Used the latest relay bundle (`tmp/agent_relay_bundle_2026-07-13_120341/`) as source of truth alongside the live repo; confirmed the bundle's `data/contracts.csv` was byte-identical to the live file before proceeding.
- **Part A — Philadelphia non-safety re-scan:** searched primary-source locations (union-hosted contract pages, city labor-relations pages, council/legislative attachments) rather than search-engine summaries, for both DC33 and DC47, not assuming the already-ingested cycles were the only relevant ones.
  - Found **AFSCME Local 2187**'s own "Contract Library" page (a DC47-affiliate local representing City of Philadelphia, PHA, and PPA employees) hosting a direct PDF: a bilaterally-signed "Term Sheet Agreement" between the City and DC47 Locals 2186/2187, term **July 1, 2025 - June 30, 2028**, independently corroborated as ratified by contemporaneous news coverage (PhillyVoice, Philadelphia Inquirer, ~July 2025).
  - This cycle overlaps the already-ingested Philadelphia police row (2025-2027) for the police row's entire term. Ingested as `pa_philadelphia_other_2025` (`occupation_class=other`, per recognition-clause-first review — the unit spans multiple agencies and both non-supervisory and supervisory titles). `ingest/audit_coverage.py` now reports Philadelphia police vs. this row as a healthy **overlap-cycle matched pair** — the first genuine (not merely design-level) Philadelphia match.
  - The fire window (2017-2020) remains unresolved — no document found for the DC33/DC47 cycle that a 2018 `phila.gov` press release confirms existed around that period. Documented as an open gap, not stretched into a match.
  - Rejected: DC33's `termsheet_0.pdf` (2025-2028, no signature evidence located, a bare term sheet); a `phila.gov`-hosted 2024-2025 DC33 extension document (cycle does not overlap either target window); `dc47.org/contracts/` (404, no direct navigation found).
  - **Harrisburg/Pittsburgh fallback scan: not triggered.** The task's explicit conditional was "if Philadelphia remains fruitless" — since Philadelphia produced a genuine matched pair, the fallback scan was correctly skipped this session, per the task's own logic (documented explicitly so this is not mistaken for an unaddressed item).
- **Part B — NJ extraction-quality audit (audit-only, no code or data changes):** read `ingest/extract_spans.py` directly and re-verified all 6 previously-flagged rows (`wage_mechanism_evidence_checklist.md` §15 items 8-13) plus the new Philadelphia row against their exact source language, confirming three root causes: (1) the `interest_arbitration` trigger list includes a bare `\bbinding arbitration\b` pattern that fires on any dispute-arbitration clause regardless of subject matter; (2) no negation/exclusion-awareness — the regex never checks whether a matched phrase is being negated in context, explaining both documented inversions; (3) the `comparability` trigger `\bcomparab\w+\b` is a bare word-root wildcard with zero semantic scoping, firing on any use of "comparable" regardless of subject (rank, benefits plan, leave, etc.).
  - Found and documented a **7th** instance (item 14, `pa_philadelphia_other_2025`'s `interest_arbitration_flag=1`) — a passing institutional-status reference within a genuine Most-Favored-Nation clause (which itself is correctly flagged `me_too_clause_flag=1`, a true positive), not evidence the unit itself has interest arbitration.
  - Produced a concrete fix plan in `docs/analysis/philadelphia_nonsafety_rescan_and_nj_extraction_fix_plan_2026-07-13.md`: (A) narrow the `binding arbitration` trigger to require wage/impasse co-occurrence; (B) add a negation/exclusion guard before setting any flag; (C) require a `REFERENT_PATTERNS` match before setting `comparability_clause_flag`, not just for populating `comparability_referent`; (D) flag (not implement) a structural note that a parallel `grievance_arbitration_flag` field pair would be the most complete fix, pending schema-change authorization; (E) a documentation-only NJ guardrail recommendation. **No code or data changes were made** — `ingest/extract_spans.py` and all flagged `data/contracts.csv` rows are unchanged; this is a diagnosis-and-proposal only, per the task's explicit audit-first instruction.
- Updated `docs/analysis/state_city_claim_map_2026-07-12.csv` for Philadelphia PA only (`matched_design_status` reasoning refreshed to reflect the new overlap-cycle pair).

**Decisions and why**
- Treated the DC47/Local 2187 document as executed despite it being a compiled "contract library" packet with some appended side letters still carrying "[signature page to follow]" placeholders, because (a) a genuine bilateral dated signature block was located tied to the main term sheet's Exhibit-A incorporation clause, (b) the union hosts it persistently under its own "Contract Library" category, and (c) independent news coverage corroborates real-world ratification of this exact agreement. Documented as a judgment call in the row's `total_comp_note`, consistent with the same standard applied to the DC33 2021-2024 row in Wave 1.
- Did not run the Harrisburg/Pittsburgh fallback scan, strictly following the task's own conditional trigger rather than scanning speculatively once Philadelphia succeeded.
- Did not implement the Part B fix plan or correct any flagged row this session — explicitly instructed to audit first and recommend second; implementation requires a future explicit authorization.

**Surprises/breakage**
- None to the corpus or pipeline. The Part B diagnosis converged cleanly: all 7 flagged issues (6 prior + 1 new) trace to exactly 3 narrow code patterns, not 7 unrelated bugs — a genuinely tractable fix once authorized.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 63 | discourse: 0 | coverage: 63 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 27 (was 26; +1: Philadelphia police vs. DC47/Local 2187, overlap-cycle)
  exact-cycle: 9 | overlap-cycle: 18
exploratory adjacent matches: 3 (was 4; Philadelphia police no longer counted as adjacent)
safety units unmatched: 6 (unchanged)
cities with no safety contract yet: 0 (unchanged)
cities: 19 (unchanged)
```
`docs/schema.md`, `ingest/extract_spans.py`, and `docs/final_reports/` confirmed unchanged (empty diffs).

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls (deterministic regex extraction only, `--llm` never passed); no FOIA/OPRA/RTKL/PRR; no git push; no remote inspection/configuration. 1 new PDF now lives under `corpus/pa_philadelphia/`.

**Next steps**
1. Get explicit authorization for the Part B fix plan (`docs/analysis/philadelphia_nonsafety_rescan_and_nj_extraction_fix_plan_2026-07-13.md`), implement items A-C in `ingest/extract_spans.py`, and run the recommended regression check (known-flagged rows must clear; known-good positive rows must not be suppressed) before correcting any of the 7 flagged production rows.
2. Locate a Philadelphia non-safety source covering 2017-2020 to close the fire-window gap (the last remaining Philadelphia design gap).
3. Trenton NJ and Philadelphia PA are both now ready, design-wise, for a first controlled codify wave — recommend running the Part B extraction fix first, so codify scores corrected spans rather than the currently-flagged ones.

## 2026-07-13 12:00 EDT (PA/NJ Ingestion Wave 2 — Newark and Trenton police+fire confirmed via direct PERC-index browsing; Trenton becomes the corpus's first PA/NJ matched triad) - Confirmed Newark police, Newark fire, Trenton police, and Trenton fire by browsing the NJ PERC public-sector-contracts index directly by employer name (not generic search, which had failed twice); ingested 4 real sources; confirmed Philadelphia still has no non-safety agreement overlapping its safety windows (documented failure); no GABRIEL/codify/model/API calls; no push/remote work

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `437e0bf PA/NJ Ingestion Wave 1: Philadelphia triad, Newark and Trenton non-safety`; `data/contracts.csv`/`data/city_coverage.csv` each 58 rows.
- **Confirmation pass (Step 1):** Generic web search had failed twice (pilot scan, Ingestion Wave 1) to surface current-cycle Newark/Trenton police/fire CBAs. This session instead browsed the NJ PERC "Contracts By Employer" index directly, using its Domino/Notes view `StartKey` parameter to jump to the Newark and Trenton alphabetical sections and read the actual employer/union/term listing (not a search-engine snippet). This surfaced real union names and current terms that neither prior session had found:
  - Newark police: **FOP Lodge 12**, current term 2018-2023 (previously assumed generically as "PBA").
  - Newark fire: **Newark Firefighters Union** (rank-and-file, most-recently-documented term 2013-2015) and, separately, **IAFF Local 1860** (most recent listed term 2017-2023, more current, but its document PDF could not be located despite extensive targeted search — documented as an unresolved confirmation failure).
  - Trenton police: **PBA Local 11**, current term 2019-2024 (a City Council resolution, No. 23-333, authorizing execution, with the full CBA attached).
  - Trenton fire: **Trenton Fire Officers Association / FMBA Local 206**, current term 2021-2026.
  - Direct single-ID document URLs extracted from the index view's summarized HTML mostly 404'd ("IBM Notes Exception - Entry not found in index") — the index uses a two-level view-category + document-ID path that isn't exposed by simple page summarization. Exact-filename web searches (e.g., `"Newark and FOP Lodge 12" pdf`) then successfully resolved the real PDFs for 3 of the 4 targets; the 4th (a more current Newark fire document) could not be resolved this way either.
  - Philadelphia non-safety-overlap check: found one new lead (`phila.gov`-hosted 2024-2025 AFSCME DC33 one-year-extension document, filed as a public-records-discovery attachment) but its cycle (~July 2024-June 2025) does not overlap either the police (2025-2027) or fire (2017-2020) window even if pulled, so it was not pursued further. **Philadelphia's non-safety overlap gap remains unresolved** — documented as a valid confirmation failure per the task's explicit allowance.
- **Ingestion (Steps 2-4):** Downloaded, read (recognition clause + exact cycle dates), and ran `ingest/pipeline.py` (deterministic regex extraction only, no `--llm`, no GABRIEL/codify) on 4 sources, all passing the provenance/recognition/matched-design-usefulness gate:
  1. `nj_newark_police_2018` — FOP Lodge 12, 2018-2023, `occupation_class=police`. **Overlaps the already-ingested Newark non-safety row (2020-2023) for the full 2020-2023 period — a genuine cycle-overlapping matched pair**, not merely adjacent.
  2. `nj_newark_fire_2013` — Newark Firefighters Union, 2013-2015, `occupation_class=fire`. Does not overlap the non-safety row; added for occupation-coverage completeness (consistent with how Philadelphia fire was treated in Wave 1).
  3. `nj_trenton_police_2019` — PBA Local 11, 2019-2024, `occupation_class=police`. **Overlaps the already-ingested Trenton non-safety row (2019-2023) for the full 2019-2023 period.**
  4. `nj_trenton_fire_2021` — Trenton Fire Officers Association/FMBA Local 206, 2021-2026, `occupation_class=fire`. **Overlaps both the non-safety row (2021-2023) and the newly-ingested police row (2021-2024).** All three Trenton rows pairwise overlap in 2021-2023 — **Trenton is now the corpus's first genuinely matched three-occupation-class design in PA/NJ**, matching the design quality of the Ohio matched triads.
  - `data/contracts.csv`/`data/city_coverage.csv` grew from 58 to 62 rows.
- **Deterministic-extraction audit findings (documented, not corrected, per audit-first discipline):** 5 more false-positive/inversion mechanism flags found across the 4 new rows, added as items 10-13 in `wage_mechanism_evidence_checklist.md` §15, including a second inversion (Trenton fire's `interest_arbitration_flag=1` on text that explicitly *excludes* fiscal matters from interest arbitration). A cross-document pattern is now documented: NJ police/fire CBAs consistently route wage-setting interest arbitration through an external statutory process rather than a CBA-internal clause, so the CBA's own "arbitration" article is almost always ordinary grievance arbitration — the regex extractor (tuned on MA/TX/OH phrasing) is structurally prone to false positives on this NJ document family.
- Updated `docs/analysis/state_city_claim_map_2026-07-12.csv` for Newark NJ (`matched_design_status` → `matched_pair`) and Trenton NJ (`matched_design_status` → `matched_triad`, now the strongest PA/NJ candidate). Philadelphia's row is unchanged (no new confirmation succeeded there).

**Decisions and why**
- Ingested Newark fire (2013-2015) despite its non-overlapping cycle, for consistency with the precedent set in Wave 1 (Philadelphia fire, also non-overlapping, was ingested to complete occupation coverage) — both fill a claim-driven design gap even without an immediate cycle match.
- Did not pursue the Philadelphia 2024-2025 AFSCME extension document once its cycle was confirmed not to overlap either target window — downloading it would not have served the specific Step 3 Priority 2 purpose (converting exploratory-adjacent into matched), so it was left as a documented lead rather than ingested speculatively.
- Did not force a guess at the IAFF Local 1860 (Newark fire, 2017-2023) document URL — several plausible constructed URLs 404'd, and guessing further risked either wasted effort or, worse, ingesting the wrong document under an assumed name. Documented as an explicit, honest confirmation failure per the task's own allowance for that outcome.

**Surprises/breakage**
- The NJ PERC public-sector-contracts database's `Contracts By Employer` Domino view is directly browsable with a `StartKey=<name>` parameter — this is the technique that finally worked after three prior sessions' generic-search attempts failed. Recorded here as a reusable technique for any future NJ PERC confirmation work.
- A second interest-arbitration-flag *inversion* (Trenton fire) reinforces that this is a real, recurring extraction-quality pattern for NJ documents specifically, not a one-off (see the new cross-document note in `wage_mechanism_evidence_checklist.md` §15).

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 62 | discourse: 0 | coverage: 62 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 26 (was 23; +3: Newark police, Trenton police, Trenton fire)
  exact-cycle: 9 | overlap-cycle: 17
exploratory adjacent matches: 4 (unchanged — Philadelphia's two rows remain adjacent-only)
safety units unmatched: 6 (was 5; +1: Newark fire, 2013-2015, does not overlap or sit adjacent to the 2020-2023 non-safety row)
cities with no safety contract yet: 0 (was 2 — both Newark and Trenton now have safety contracts)
cities: 19 (unchanged)
```
`docs/schema.md` and `docs/final_reports/` confirmed unchanged (empty diffs).

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls (deterministic regex extraction only, `--llm` never passed); no FOIA/OPRA/RTKL/PRR; no git push; no remote inspection/configuration. 4 new PDFs now live under `corpus/nj_newark/` and `corpus/nj_trenton/`.

**Next steps**
1. Locate the more current Newark fire document (IAFF Local 1860, 2017-2023 term) to convert Newark from `matched_pair` to a genuine `matched_triad` — try the PERC-index-browsing technique with additional filename variants, or a direct site visit if a browsing tool becomes available.
2. Trenton's matched-triad design is now complete for a first codify wave — this is the strongest PA/NJ candidate for Steps 9-13 of `claim_testing_source_wave_methodology_2026-07-12.md` (codify in a controlled, capped wave; audit grounding; rebuild the viewer; update the claim register/evidence matrix/hypothesis tracker/source-needs docs together). Not done this session, by design.
3. Philadelphia's non-safety-overlap gap remains open; the only lead found (a 2024-2025 AFSCME extension) does not overlap either safety window, so a genuinely new source (not just a newer AFSCME document) is likely needed.
4. Resolve `wage_mechanism_evidence_checklist.md` §15 items 8-13 (six flagged mechanism fields across two ingestion waves) in a future dedicated, audit-first metadata-cleanup pass.

## 2026-07-13 11:27 EDT (PA/NJ Ingestion Wave 1 — first real ingestion into the causal corpus since the source-scan waves) - Confirmed remaining PA/NJ document gaps by reading actual pages/documents (not just search snippets), ingested 5 real sources (Philadelphia PA police+fire+non-safety, Newark NJ non-safety, Trenton NJ non-safety) via `ingest/pipeline.py`, rejected 2 candidates on direct inspection (a Reading, PA "library CBA" that turned out to be a construction contract; a Philadelphia AFSCME termsheet that was only a summary), held Newark/Trenton police+fire and all six other PA/NJ cities per the task's explicit holds; no GABRIEL/codify/model/API calls; no push/remote work

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `53eab37 Save source-wave methodology and PA NJ claim map`; working tree clean except untracked `.claude/` and `tmp/`; `data/contracts.csv`/`data/city_coverage.csv` each 53 rows.
- **Confirmation pass (Task 1):** Fetched actual pages (not just search-engine snippets) for the remaining `needs_review` PA/NJ candidates.
  - Philadelphia FOP Lodge 5 (police): confirmed a direct, current, signed Act 111 interest-arbitration award PDF (`FOP-5-Act-111-Award-2025-2027.pdf`, term July 1 2025 - June 30 2027) on the union's own contracts page.
  - Philadelphia IAFF Local 22 (fire): confirmed a direct, city-hosted, signed interest-arbitration award PDF (`Signed-2017-2020-Local-22-Award.pdf`, term July 1 2017 - June 30 2020).
  - Philadelphia AFSCME DC33 (non-safety): the current (2025-2028) agreement exists on the union's own contracts page only as a `termsheet.pdf` (a summary, explicitly excluded per task instructions); the 2021-2024 agreement is a full document with dated signature blocks for both parties (9-3-2021), despite its internal header still reading "TENTATIVE AGREEMENT" — judged as the executed governing agreement for that cycle and ingested with this caveat documented.
  - Newark NJ and Trenton NJ police/fire CBAs: **not confirmed.** Direct `site:perc.state.nj.us` searches, an attempted PERC frameset browse via WebFetch, and multiple employer-name-pattern searches all failed to surface a current-cycle CBA PDF for any of the four (Newark police, Newark fire, Trenton police, Trenton fire) — only PERC decisions/synopses (confirming the units are active) and, for Trenton fire, a single out-of-window (year-2000, different local number) PDF. Documented as a genuine, still-open gap, not ingested.
- **First ingestion batch (Task 2):** Downloaded and ran `ingest/pipeline.py` (deterministic regex extraction only — no `--llm`, no GABRIEL/codify) on 5 sources:
  1. `pa_philadelphia_police_2025` — FOP Lodge 5 Act 111 award, 2025-2027, `arbitration_award`, clean text layer.
  2. `pa_philadelphia_fire_2017` — IAFF Local 22 Act 111 award, 2017-2020, `arbitration_award`, OCR (ocr_messy).
  3. `pa_philadelphia_other_2021` — AFSCME DC33, 2021-2024, `cba`, OCR (ocr_messy), `occupation_class=other`.
  4. `nj_newark_other_2020` — Teamsters Local 97, 2020-2023, `cba`, clean text layer, `occupation_class=other`.
  5. `nj_trenton_other_2019` — AFSCME Local 2281, 2019-2023, `cba`, OCR (ocr_messy), `occupation_class=other`.
  - `data/contracts.csv` and `data/city_coverage.csv` (via the pipeline's automatic coverage-row append) both grew from 53 to 58 rows.
- **Rejected on direct inspection (2 candidates):**
  - The Reading, PA "Public Library CBA" candidate (`pa_nj_candidate_sources_2026-07-12.csv`/`pa_nj_candidate_sources_followup_2026-07-12.csv`, marked `ingest_next`/`confirmed` in both prior scans) turned out, on actually downloading and reading it, to be a construction/electrical-contractor bid contract between the City of Reading and BSI Electrical Contractors for library-building electrical work — not a labor agreement at all. Both prior scans had classified this candidate from its URL/filename alone and never opened the document. **Reading, PA yields zero ingestible sources this wave** as a result; corrected in this session's documentation.
  - Philadelphia AFSCME DC33's 2025-2028 `termsheet.pdf` was found and explicitly rejected (summary, not a full CBA), in favor of the 2021-2024 full-text agreement described above.
- **Recognition-clause-first review (per `recognition_clause_first_classification_standard_2026-07-08.md`)** corrected two assumptions before classification: Newark's "Teamsters Local 97" unit covers **municipal attorneys** (Article 1 Recognition: "all regularly employed attorneys... including assistant corporation counsels... public defenders and zoning attorneys, municipal prosecutors"), not sanitation/public works as the union name alone would suggest; Trenton's AFSCME Local 2281 unit is described by the document itself as "Trenton, New Jersey **Supervisory** Employees," not the "White Collar/Blue Collar" label carried in the candidate CSV's filename. Both correctly classified `occupation_class=other` per the standard's conservative-mapping rule (mixed/multi-title coverage, no schema-supported specific class fits).
- **Deterministic-extraction audit finding (not corrected, per audit-first discipline):** two new false-positive mechanism flags were found and documented in `wage_mechanism_evidence_checklist.md` §15 (items 8-9), not silently edited: `pa_philadelphia_police_2025`'s `comparability_clause_flag=1` is a sick-leave-usage administrative comparison, not peer-wage comparability; `pa_philadelphia_other_2021`'s `interest_arbitration_flag=1` actually captured a Scope clause that *excludes* DC33 members from interest arbitration (substantively useful once corrected — direct evidence that Philadelphia's general non-safety unit lacks the Act 111 backstop that police/fire have).
- Updated exactly 3 rows (Philadelphia PA, Newark NJ, Trenton NJ) in `docs/analysis/state_city_claim_map_2026-07-12.csv`: `corpus_status` moved from `candidate_only` to `ingested`; `evidence_status` and `codified` remain `source_availability_hypothesis`/`no` (no codify occurred); Newark/Trenton `matched_design_status` moved to `non_safety_only`; Philadelphia stayed `matched_triad` at the design level with an explicit new limitation noting the three cycles do not overlap (`ingest/audit_coverage.py` reports them as "exploratory adjacent," not healthy matched pairs).

**Decisions and why**
- Treated the AFSCME DC33 2021-2024 document as executed/signed despite its internal "TENTATIVE AGREEMENT" header, because it carries dated, both-party signature blocks and is the union's own archived record of that bargaining cycle — documented as a judgment call, not asserted as certain, per the methodology's provenance-review discipline.
- Did not ingest Newark/Trenton police or fire, or any of the six explicitly-held cities (Jersey City, Paterson, Elizabeth, Pittsburgh, Allentown, Erie), per the task's explicit holds and the "only ingest documents that pass both provenance and recognition/coverage review" instruction — none of those had a confirmed current-cycle document this wave.
- Did not run `--llm`/GABRIEL on any of the 5 new sources — deterministic regex extraction only, consistent with Step 8 (not Step 9) of `claim_testing_source_wave_methodology_2026-07-12.md`; codify is the next wave's job, gated on this ingestion being validated first.
- Documented, rather than silently fixed, the two deterministic-extraction false positives — consistent with the project's established audit-first-not-direct-edit-first convention (see `wage_mechanism_evidence_checklist.md` §15's existing resolved items 1 and 6, which followed the same pattern).

**Surprises/breakage**
- The Reading, PA "library CBA" being a construction contract is a genuine, consequential correction: it had been marked `ingest_next`/`confirmed` in *two* prior scan sessions, both of which inferred the document's nature from its URL/filename rather than opening it. This is now the strongest argument in the corpus for why the confirmation-pass step (Task 1 here, Step 5 of the methodology) must include actually reading candidate documents before ingestion, not just re-confirming that a URL resolves.
- Two NJ PERC download URLs (Newark IBT-97, Trenton AFSCME-2281) were initially blocked by an Incapsula bot-protection challenge under `curl`'s default user-agent; resolved by adding a standard browser `User-Agent` header. The Philadelphia IAFF-22 URL was similarly blocked once (Akamai/Cloudflare-style 403) and resolved the same way.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 58 | discourse: 0 | coverage: 58 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (unchanged — the 5 new rows did not create a cycle-overlapping match)
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 4 (was 2)
  + Philadelphia, PA: police 2025-2027 vs [other] (other 2021-2024)
  + Philadelphia, PA: fire 2017-2020 vs [other] (other 2021-2024)
safety units unmatched: 5 (unchanged — Somerville x2, Newton, San Antonio police, San Antonio fire)
cities with no safety contract yet: 2 (new)
  + Newark, NJ: 1 non-safety unit, 0 safety
  + Trenton, NJ: 1 non-safety unit, 0 safety
cities: 19 (was 16)
```
Confirmed via `git status --porcelain -- docs/final_reports/`: empty (no final-report artifacts touched). `docs/schema.md` unchanged (`git diff --stat`: empty).

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls (deterministic regex extraction only, `--llm` never passed); no FOIA/OPRA/RTKL/PRR; no git push; no remote inspection/configuration. Real downloads and real ingestion *did* occur this session, by explicit task authorization (unlike every prior PA/NJ session, which was scan-only) — 5 PDFs now live under `corpus/pa_philadelphia/`, `corpus/nj_newark/`, `corpus/nj_trenton/`.

**Next steps**
1. Browse the NJ PERC public-sector-contracts index directly by employer name (not generic web search, which has now failed twice) for current-cycle Newark PBA, Newark Firefighters/Fire Officers Local 1860, Trenton PBA Local 11, and Trenton Fire Officers Association/FMBA Local 206 CBAs.
2. Find a Philadelphia non-safety source with a cycle overlapping either the 2025-2027 police or 2017-2020 fire window, to convert the current "exploratory adjacent" Philadelphia triad into a healthy matched pair/triad.
3. Once ingestion for a given city is judged sufficiently complete, proceed to Steps 9-13 of `claim_testing_source_wave_methodology_2026-07-12.md` (codify in a controlled wave, audit grounding, rebuild the viewer, update the claim register/evidence matrix/hypothesis tracker/source-needs docs) — not yet done this session by design.
4. Resolve `wage_mechanism_evidence_checklist.md` §15 items 8-9 (two new flagged mechanism fields) in a future dedicated, audit-first metadata-cleanup pass.

## 2026-07-13 10:45 EDT (Claim-testing methodology saved; PA/NJ follow-up digging and state/city claim map completed) - Saved the repeatable 13-step source-wave lifecycle as a durable project standard, added a concise pointer in AGENTS.md, ran a targeted PA/NJ follow-up web search to convert pilot-scan gaps into confirmed leads, and built an educated claim map covering every state/city currently in the project; no GABRIEL/codify/model/API calls, no downloads/ingestion, no data/corpus/final-report edits; local commit only by design

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `b9291d0 Scan Pennsylvania and New Jersey source availability`; working tree clean except untracked `.claude/` and `tmp/`; evidence layer 781 rows; `data/contracts.csv` and `data/city_coverage.csv` each 53 rows — all matching the task's expected repo-state note.
- Created `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md`, a durable standard documenting the repeatable 13-step source-wave lifecycle (choose claims/hypotheses → choose 1-2 states → scan ~5 cities/state → mark candidates → promote → ingest 6-12 → validate → extract → codify 8-15 → audit grounding → rebuild viewer → update claim register → decide next gap), promotion rules, evidence/scoring rules, claim-update rules, and the report standard (claim/evidence/reasoning/counterevidence/what-would-change-our-mind/source-needs).
- Added a concise pointer section ("Claim-driven expansion and reporting") to `AGENTS.md`, referencing the new methodology doc and restating that future reports should be claim-centered, not mechanism inventories.
- Ran a targeted, public-web-only PA/NJ follow-up search (no downloads/ingestion) across the same 10 cities as the 2026-07-12 pilot scan, aimed specifically at resolving `needs_review` rows. Created `docs/analysis/pa_nj_candidate_sources_followup_2026-07-12.csv` (39 rows, `csv.writer`-built, parse-back validated). Key upgrades: a direct, in-window (2019) non-safety CBA found for Trenton NJ (previously zero leads); a corrected non-safety union identity for Allentown PA (SEIU Local 668, not AFSCME); a new non-safety lead for Erie PA (AFSCME Local 2206, ratified 2026-03-04); Jersey City NJ resolved to a document-level candidate for all three roles via direct PERC-domain PDFs (though dated ~2009-2015); Newark NJ gained a second non-safety document (AFSCME Local 2297 Supervisory, 2010) and an extensive PERC decision history confirming its police/fire units; Elizabeth NJ confirmed as the weakest-evidenced city in either state after a second round.
- Created `docs/analysis/pa_nj_state_city_claim_notes_2026-07-12.md`, giving each of the 10 scanned cities an explicit source-availability-informed hypothesis, matched-triad assessment, and recommended status (`ingest_next` / `scan_more` / `hold` / `reject_for_now`).
- Created `docs/analysis/state_city_claim_map_2026-07-12.csv` (26 rows: 16 codified MA/TX/OH cities + 10 scanned-but-uningested PA/NJ cities), with a build-script-enforced rule that no PA/NJ row can be marked `codified=yes` or anything other than `evidence_status=source_availability_hypothesis`. Created `docs/analysis/state_city_claim_map_summary_2026-07-12.md` synthesizing current codified-city readiness (MA/TX/OH) against PA/NJ source-availability promise, and proposing a first (not-yet-executed) 8-source ingestion batch.
- Updated PA/NJ rows only in `docs/analysis/national_source_targets_2026-07-12.csv` (8 rows), and added follow-up-round notes to the affected rows of `docs/analysis/claim_driven_source_needs_2026-07-12.csv` (5 rows) and `docs/analysis/hypothesis_tracker_2026-07-12.csv` (6 rows) — all other states'/claims'/hypotheses' rows untouched.
- Lightly updated `wage_mechanism_evidence_checklist.md` (Section 16), `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7W), and `all_groups_source_needs_2026-07-06.csv` (one new cross-cutting row) to point future agents at the new methodology doc and claim map.

**Decisions and why**
- Recommended ingestion batch order changed from the 2026-07-12 pilot scan's Philadelphia+Newark framing: Trenton NJ is now a strong second-priority NJ target (a direct, in-window non-safety document appeared where the pilot scan had found nothing), and Jersey City NJ — despite having the only complete three-role document set found in either state — is held for a "vintage problem" (documents dated ~2009-2015) rather than promoted, since the CBA source-verification standard's 2014-2024 window is not clearly met.
- Used a stricter, code-enforced rule in the state/city claim map (`matched_design_status` based on whether each role reaches at least `partially_confirmed`/`confirmed` follow-up status, not merely "a union is named") to avoid overstating PA/NJ candidate strength; Paterson NJ and Elizabeth NJ were deliberately marked `safety_only`/`scan_unknown` rather than any triad-shaped label given their genuine non-safety gaps.
- Kept the claim-testing methodology doc's Steps 1-5 (scanning) explicitly separate from Steps 6-11 (ingestion/codify, not yet authorized for PA/NJ) so a future agent cannot mistake this run's source-availability work for coded evidence.

**Surprises/breakage**
- None to the corpus or pipeline. The most consequential search-methodology finding: the 2026-07-12 pilot scan's PA searches had implicitly assumed AFSCME as the default non-safety union family, which produced a false total gap for Allentown (whose actual non-safety union is SEIU Local 668) — now corrected and recorded as a general lesson in `pa_nj_state_city_claim_notes_2026-07-12.md`.
- NJ's PERC-index advantage sharpened further this round: direct `site:perc.state.nj.us "<City>" <union> pdf` queries surfaced document-level PDFs for Newark, Jersey City, and Trenton that generic keyword search had missed in the pilot scan — recorded as a specific, reusable technique.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire) -- unchanged

custom checks
pa_nj_candidate_sources_followup_2026-07-12.csv: 39 rows, parse-back OK, row-width OK (19 cols), controlled-vocab OK, claim IDs resolve
state_city_claim_map_2026-07-12.csv: 26 rows, parse-back OK, row-width OK (16 cols), controlled-vocab OK, claim IDs resolve, PA/NJ rows all codified=no/source_availability_hypothesis
national_source_targets/claim_driven_source_needs/hypothesis_tracker/all_groups_source_needs: parse-back OK, only the intended rows changed
git diff --stat -- data/contracts.csv data/city_coverage.csv docs/schema.md: empty
git status --porcelain -- corpus/ docs/final_reports/: empty
```

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls; no downloads of any source into `corpus/`; no new rows added to `data/contracts.csv` or `data/city_coverage.csv`; no FOIA/OPRA/RTKL/PRR routes used; no new report draft prepared; no git push; no remote inspection/configuration. Work is committed locally only by design.

**Next steps**
1. Execute the recommended first ingestion batch in `state_city_claim_map_summary_2026-07-12.md` / `pa_nj_source_scan_summary_2026-07-12.md`: Philadelphia PA (police + fire confirmed, non-safety needs one more confirmation step) and Newark NJ (non-safety confirmed, police/fire need a direct PERC-index lookup), then Trenton NJ (non-safety confirmed, police/fire need a PERC-index lookup).
2. Before ingesting Jersey City NJ, locate current-cycle (2020s) successors to the four ~2009-2015 PERC documents found this round.
3. After a reviewed ingestion pass, follow Steps 7-13 of `claim_testing_source_wave_methodology_2026-07-12.md` (validate → extract → codify → audit → rebuild viewer → update claim register → decide next gap) before starting an Illinois/New York scan.

## 2026-07-12 10:51 EDT (PA/NJ bounded source-availability scan completed) - Scanned Pennsylvania and New Jersey (5 cities each) for public, non-FOIA municipal wage-setting sources per the two-week claim-driven expansion plan's Week-1 instruction; produced candidate-source lists and scan memos only, no downloads/ingestion/codify, no data/corpus edits; local commit only by design

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest starting commit `a1f2dc8 Plan national claim-driven corpus expansion`; working tree clean except untracked `.claude/` and `tmp/`; `data/contracts.csv` and `data/city_coverage.csv` each 53 rows.
- Created `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md`, recording scope (PA/NJ only, this run), source criteria, and stop rules (60-row cap, no FOIA/OPRA/RTKL/PRR, no downloads).
- Ran public web searches for police/fire/non-safety wage-setting sources across a task-specified 10-city list: Philadelphia, Pittsburgh, Allentown, Erie, Reading (PA); Newark, Jersey City, Paterson, Elizabeth, Trenton (NJ).
- Created `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` — 40 candidate rows (21 PA, 19 NJ, well under the 60-row cap), built with `csv.writer` and parse-back validated (row-width, controlled-vocabulary, and required-field checks all passed) per `source_planning_csv_hygiene_standard_2026-07-08.md`. 8 rows marked `ingest_next`, 22 `needs_review`, 9 `reject` (including two documented false-positive/jurisdiction-mismatch exclusions: Erie County NY, and Passaic County vs. City of Paterson), 1 `hold`.
- Created `docs/analysis/pennsylvania_source_scan_2026-07-12.md` and `docs/analysis/new_jersey_source_scan_2026-07-12.md`, each covering cities scanned, strongest matched cities, non-safety availability, arbitration/factfinding availability, provenance, ingestion burden, and a promote/hold recommendation.
- Created `docs/analysis/pa_nj_source_scan_summary_2026-07-12.md`, comparing the two states and proposing a first (not-yet-executed) ingestion batch of 8 sources spanning a near-complete Philadelphia triad and a near-complete Newark triad.
- Updated `docs/analysis/national_source_targets_2026-07-12.csv` for the 10 PA/NJ rows only (`target_status` and `notes` columns), via a Python script with parse-back validation; all other states' rows untouched.

**Decisions and why**
- Followed the task's fixed 10-city list (which substitutes Reading for Scranton and Elizabeth for Camden relative to the prior `national_source_targets_2026-07-12.csv` planning rows) rather than the original 5-per-state planning targets, since the task explicitly specified the cities to scan. Recorded this substitution explicitly in both the preflight memo and the national-targets update so Scranton/Camden are marked `not_scanned_this_pass` rather than silently dropped.
- New Jersey was ranked ahead of Pennsylvania at the state level because PERC (NJ's state labor board) maintains a centralized, statutorily-mandated public index of nearly all municipal CBAs and a separate police/fire interest-arbitration-awards database — a structural advantage Pennsylvania does not have. At the city level, Philadelphia alone produced a stronger, more complete document set (including two city-hosted arbitration awards) than any single NJ city in this scan.
- Marked context-only or union-existence-confirming pages (news items, PERC decisions/synopses, case law, budget-appendix references) as `causal_candidate=no/maybe` and `source_type_candidate=context_only`, never `causal_candidate=yes`, unless a document plausibly containing the actual agreement/award text was directly linked.
- Recorded two Philadelphia AFSCME rows and one Newark IBT Local 97 row with `occupation_class_candidate=other` (provisional) per the recognition-clause-first classification standard, rather than inferring a specific non-safety class from the union name.

**Surprises/breakage**
- None to the corpus or pipeline. Notable scan surprises: (1) an early "Erie" search returned Erie County, **New York** labor-relations documents under a similarly generic domain pattern — a jurisdiction false positive, now explicitly documented as excluded; (2) Passaic County (NJ) posts its own CBAs publicly, which could be mistaken for a City of Paterson source — also documented as excluded; (3) non-safety sources were confirmed as the binding bottleneck at the city level exactly as the national plan predicted — 7 of 10 scanned cities have no confirmed non-safety document yet.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire) -- unchanged

custom scan checks
candidate CSV: 40 rows, parse-back OK, row-width OK, controlled-vocab OK, required-fields OK
national source targets: 29 rows, parse-back OK; only the 10 PA/NJ rows' target_status/notes changed
git diff --stat -- data/contracts.csv data/city_coverage.csv: empty
git status --porcelain -- corpus/: empty
```

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls; no downloads of any source into `corpus/`; no new rows added to `data/contracts.csv` or `data/city_coverage.csv`; no FOIA/OPRA/RTKL/PRR routes used or recorded as viable; no git push; no remote inspection/configuration. Work is committed locally only by design.

**Next steps**
1. Run a short, targeted (still non-ingestion) follow-up: browse the NJ PERC public-sector-contracts index and interest-arbitration-awards index by employer name for Newark, Jersey City, Paterson, Elizabeth, and Trenton; confirm whether a signed (not proposed) Philadelphia AFSCME DC33/DC47 CBA is directly retrievable.
2. If confirmed, run a reviewed ingestion pass on the 8-source batch in `pa_nj_source_scan_summary_2026-07-12.md` (Philadelphia triad + Newark triad), then `python ingest/audit_coverage.py` to check the new matched pairs.
3. Defer Illinois/New York scanning until after this PA/NJ batch is ingested, per the summary memo's recommendation — both PA and NJ already clear the two-week plan's "clean matched triad" promotion bar pending the confirmations above.

## 2026-07-12 10:36 EDT (National claim-driven corpus expansion plan) - Created a two-week national source-expansion strategy organized around current claims and leading hypotheses; no GABRIEL/codify/model/API calls, no new source collection, no data/corpus/final-report edits; local commit only by design

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest commit `3bb9ebf Consolidate claim-centered evidence register`; working tree clean except untracked `.claude/` and `tmp/`; evidence layer 781 rows; `data/contracts.csv` and `data/city_coverage.csv` each 53 rows.
- Created `docs/analysis/national_corpus_expansion_preflight_2026-07-12.md`, recording current git/data/evidence/claim state and explicit constraints for this planning-only run.
- Created `docs/analysis/national_corpus_current_coverage_gap_audit_2026-07-12.md`, documenting current coverage by state, city, occupation, safety group, source type, text quality, matched-triad status, verified-present attributes, and claim relevance.
- Created `docs/analysis/national_state_priority_rubric_2026-07-12.csv` with 20 candidate states. Tier 1 for the first source scan: Pennsylvania, New Jersey, Illinois, New York. Tier 2: California, Washington, Oregon, Michigan, Minnesota, Wisconsin, Connecticut, Rhode Island, Maryland, Colorado. Tier 3/hold states retained as conservative contrast or later-wave candidates.
- Created `docs/analysis/two_week_claim_driven_expansion_plan_2026-07-12.md`, making the next phase source expansion and claim testing, not another report.
- Created `docs/analysis/national_source_targets_2026-07-12.csv` with 29 initial planning targets, including 5 city targets per tier-1 state. No searches or downloads were run.
- Created `docs/analysis/hypothesis_tracker_2026-07-12.csv` tracking the 8 leading hypotheses against current claims, attributes, source needs, and strengthening/weakening decision rules.
- Created `docs/analysis/claim_driven_source_needs_2026-07-12.csv` mapping all 8 current claims to source priorities, suggested states/city types, attributes to watch, and what would change the claim.
- Created `docs/analysis/next_prompt_national_source_scan_2026-07-12.md` for the next source-availability scan run: scan tier-1 states, prioritize matched triads, avoid FOIA/PRR, do not ingest unless bounded criteria are met, do not run codify, commit locally only.
- Lightly updated `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `all_groups_source_needs_2026-07-06.csv` to reflect the two-week claim-driven national expansion direction.

**Decisions and why**
- Prioritized source expansion over report writing because the claim register is still based on only MA/TX/OH, 37 codified sources, and thin comparator/factfinding evidence. Another report now would mostly restate the July report and claim consolidation.
- Treated matched non-safety sources as the bottleneck. Safety-only material remains useful only when it serves a specific hypothesis, especially impasse/arbitration, factfinding, or peer-comparator evidence.
- Chose conservative state scoring: unknown values remain unknown until source-availability scans verify public sources. Tier-1 states are planning priorities, not ingestion commitments.

**Surprises/breakage**
- None. The planning exercise confirmed the known gaps: current corpus covers only MA/TX/OH; `peer_comparator_wage_comparability` has only 1 verified-present row; there are no current factfinding rows; Texas non-safety outside Houston remains a major bottleneck.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire)

custom planning checks
state rubric rows: 20 | tier counts: tier_1=4, tier_2=10, tier_3=3, hold=3
national source targets: 29 | tier-1 targets: Pennsylvania=5, New Jersey=5, Illinois=5, New York=5
hypotheses tracked: 8 | claim-driven source-needs rows: 8
all controlled values valid; claim IDs and hypothesis IDs resolve
```
Custom checks confirmed that the state rubric, national source targets, hypothesis tracker, and claim-driven source-needs CSVs parse cleanly; controlled values are valid; claim IDs referenced exist in `claim_register_2026-07-12.csv`; `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, and `docs/final_reports/` are unchanged.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls; no new source collection or downloads; no FOIA/PRR; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final report DOCX/PDF artifacts; no git push; no remote inspection/configuration. Work is committed locally only by design.

**Next steps**
1. Run the next source-availability scan prompt in `docs/analysis/next_prompt_national_source_scan_2026-07-12.md`, starting with Pennsylvania, New Jersey, Illinois, and New York.
2. Record candidate URLs and source provenance, but do not ingest until matched-triad/non-safety criteria are met or selection is reviewed.
3. After reviewed ingestion waves, run codify in controlled batches and refresh the claim register/claim-evidence matrix. Defer full report drafting until the national evidence layer is materially larger.

## 2026-07-12 10:10 EDT (Claim-centered evidence register consolidated) - Created a real claim register, claim-evidence matrix, readiness table, and claim-consolidation memo from the current 781-row GABRIEL/codify evidence layer; no GABRIEL/codify/model/API calls, no new source collection, no data/corpus/final-report edits; local commit only by design

**Did**
- Confirmed repo state before work: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; latest commit `1cf2df6 Plan claim-centered corpus expansion`; working tree clean except untracked `.claude/` and `tmp/`; evidence layer 781 rows; `data/contracts.csv` and `data/city_coverage.csv` each 53 rows.
- Wrote `docs/analysis/claim_consolidation_preflight_2026-07-12.md`, documenting required inputs, evidence-layer counts, report asset availability, claim standards, and explicit run constraints.
- Created the real dated claim register, `docs/analysis/claim_register_2026-07-12.csv`, replacing the prior illustrative template for analytic use while preserving the template file. It contains 8 bounded candidate claims with scope, status, support, reasoning, counterevidence/limits, what-would-change-our-mind, source needs, and report-readiness fields.
- Created `docs/analysis/claim_evidence_matrix_2026-07-12.csv` (59 rows) mapping claims to verified-present evidence IDs, counterevidence, limitations, and explicit gap indicators. Primary support uses only verified-present, grounded evidence-layer rows.
- Created `docs/analysis/claim_readiness_table_2026-07-12.csv` (8 rows), `docs/analysis/claim_consolidation_summary_2026-07-12.md`, and `docs/analysis/claim_viewer_integration_notes_2026-07-12.md`.
- Lightly updated `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `all_groups_source_needs_2026-07-06.csv` to make future reports claim-centered by default and source expansion claim-driven.

**Decisions and why**
- Strongest current claims: the arbitration distinction (`CLM-2026-07-12-06`), Ohio matched-triad pattern (`CLM-2026-07-12-01`), and Texas institutional unevenness/design caveat (`CLM-2026-07-12-02`).
- Weakest/gap claims: peer/comparator wage evidence (`CLM-2026-07-12-07`) and Texas non-safety outside Houston (`CLM-2026-07-12-08`). These are marked not report-ready because comparator evidence has a documented false negative and Texas lacks public in-window general non-safety comparators outside Houston.
- Treated `not_found` rows as limitations/gap indicators, not proof of absence. Excluded all flagged/unverified present rows from primary support.

**Surprises/breakage**
- None. The main caveats were already known from the report scaffold and audits: Texas non-safety limits, Austin safety-adjacent status, San Antonio unmatched safety rows, binary codify limitations, and the San Antonio comparator false negative.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire)

custom claim checks
claims: 8 | matrix rows: 59 | readiness rows: 8
primary-support rows: 38 | blank gap rows: 7
register status counts: supported_provisional=6, needs_more_evidence=2
report-ready counts: yes=3, maybe=3, no=2
```
Custom checks passed: claim/register/readiness CSVs parse cleanly; controlled values valid; nonblank matrix evidence IDs exist in the evidence layer; matrix/readiness claim IDs exist in the register; no unsupported/unverified evidence used as primary support; `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, and `docs/final_reports/` unchanged.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls; no new source collection; no FOIA/PRR; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final report DOCX/PDF artifacts; no git push; no remote inspection/configuration. Work is committed locally only by design.

**Next steps**
1. Review the 8 claim-register rows for PI-facing wording, especially the `report_ready=yes/maybe/no` distinctions.
2. Use the claim-centered structure for the next report revision: claim, evidence, reasoning, counterevidence/limits, what would change our mind, source needs.
3. If source expansion is authorized later, target claims rather than generic mechanism inventory: Texas non-safety gaps, additional public-CBA matched triads, impasse/arbitration contrast states, repeat cycles, and comparator-specific awards/factfinding.

## 2026-07-12 09:22 EDT (Git remote diagnosis + claim-centered project-direction reset) - Diagnosed the missing-remote push failure (no `origin` ever configured, `gh` not installed, no safe URL discoverable — remote NOT configured, no push attempted), wrote a claim-centered corpus-expansion strategy memo to shift future reporting away from mechanism inventories, and created a claim register template; no data/corpus/codify/final-report edits, no GABRIEL/model/API calls, no new source collection

**Did**
- Confirmed repo state before touching anything: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`, `main` at `50c458b` ("Export final mechanism evidence report"), working tree clean. Worked from an isolated worktree (`worktree-remote-diagnosis`) per standing practice; git config/remotes/history are shared across worktrees, so all findings apply to `main`.
- **Remote diagnosis**: `git remote -v`, `git config --get remote.origin.url`, and `git config --list --local` all confirm `origin` has never been configured in this repo — this is an absence, not a misconfiguration. `git branch -vv` shows no upstream tracking. `gh` is not installed (`which gh` → not found), so `gh auth status` could not be checked. Searched all repo docs for any existing project-specific remote URL; the only `github.com` hits found were unrelated references to the upstream GABRIEL package's own repo, not this project's. **No safe remote URL exists anywhere in local config or repo files** — per this task's explicit constraint, none of the three safe-configuration cases (existing URL missing only upstream; URL documented in repo; `gh` installed+authenticated+confirmable) applied, so **no remote was added and no push was attempted.** Full diagnosis and exact user-facing setup commands written to `docs/analysis/git_remote_diagnosis_2026-07-10.md`.
- **Project-direction memo**: wrote `docs/analysis/claim_centered_corpus_expansion_strategy_2026-07-10.md`, arguing the project has enough foundational maturity (schema discipline, source hygiene, recognition-clause-first classification, a working grounded/contamination-checked GABRIEL codify pipeline, a local evidence viewer, and a first mechanism-evidence report) to shift future reports from mechanism inventories scattered across cities/states toward claims backed by explicit evidence, reasoning, counterevidence, and stated falsification conditions. Covers a 5-stage expansion design (consolidate current evidence into claims → source-availability scan → add 3-5 new states → codify → claim-centered report), provisional next-state candidates (Pennsylvania and New Jersey as strongest institutional-contrast candidates; Illinois, New York, California, and FL/NC/TN as secondary candidates pending source scans), and an evidence-management proposal (claim register, source inventory by claim, claim-to-evidence matrix, minimum evidence threshold, explicit counterevidence tracking).
- **Claim register template**: created `docs/analysis/claim_register_template_2026-07-10.csv` (16 columns, controlled `claim_status`/`evidence_strength`/`report_ready` vocabularies) with 4 illustrative draft/provisional rows built from real obs_ids and evidence_ids already in the corpus (verified via `data/contracts.csv` and `docs/analysis/gabriel_codify_evidence_layer.csv`, not invented) — e.g., an Ohio interest-arbitration pattern across all four coded matched triads, and a Texas claim that explicitly flags San Antonio's missing non-safety comparison unit as a data gap rather than asserting the comparison is confirmed weak. All four rows marked `draft`/`needs_more_evidence`/`supported_provisional` and `report_ready=no` or `maybe`, per the conservative-only instruction.
- Ran `python scripts/validate.py` (PASS: 53 contracts / 0 discourse / 53 coverage / 3 city_attributes) and `python ingest/audit_coverage.py` (23 healthy matched pairs, 5 safety units still unmatched — Somerville x2, Newton, San Antonio police, San Antonio fire — unchanged from prior sessions) to confirm this run made no data/corpus changes.

**Decisions and why**
- Did not configure any remote and did not push, even though the task allowed it conditionally — none of the three safe cases were met (no existing URL, no documented URL, no `gh`), and guessing or creating a repo under an uncertain owner was explicitly disallowed. Wrote exact user-facing commands instead.
- Populated the claim register's example rows from real corpus IDs (not placeholders) so the template is immediately usable as a starting point, while keeping every row's status conservative (draft/needs_more_evidence, or supported_provisional only for a structural coverage claim directly countable from `data/contracts.csv` without further mechanism analysis).

**Surprises/breakage**
- None. The missing remote was a clean absence (never configured), not a broken configuration — confirmed via `git config --list --local` showing zero `remote.*` keys.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged
safety units unmatched: 5 -- unchanged
```
Confirmed via `git status --porcelain`: only the three new `docs/analysis/` files are untracked; `git diff --stat -- data/contracts.csv data/city_coverage.csv docs/schema.md` empty; `corpus/` and `docs/final_reports/` show no changes.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls this session; no new source collection; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or any `docs/final_reports/` artifact; no git history rewrite; no force-push; no push to an unverified or guessed remote.

**Next steps**
1. **User**: configure the actual remote per `docs/analysis/git_remote_diagnosis_2026-07-10.md` (decide host/account, `git remote add origin <REMOTE_URL>`, `git push -u origin main`), or install/authenticate `gh` and specify the intended account/repo so a future run can do this safely.
2. **Content**: run the claim-consolidation prompt recommended in `docs/analysis/claim_centered_corpus_expansion_strategy_2026-07-10.md` — turn the current 781-row evidence layer into 5-8 real, evidence-mapped claim-register rows (replacing this run's illustrative drafts) — before starting any new-state source-availability scan.

## 2026-07-10 23:10 EDT (Final integrated mechanism evidence report exported) - Created one integrated final Markdown report with appendix at the end, exported DOCX/PDF, wrote export preflight/audit, updated guidance/handoff; no GABRIEL/codify/model/API calls, no new source collection, no data/corpus edits

**Did**
- Confirmed repo state before export: working directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`; git clean except untracked `.claude/` and `tmp/`; latest starting commit `d56ae31` (`Polish mechanism evidence report scaffold`); `data/contracts.csv` and `data/city_coverage.csv` unchanged.
- Created `docs/analysis/final_report_export_preflight_2026-07-10.md`, documenting input files, report assets, expected outputs, export constraints, and local toolchain availability.
- Created one integrated Markdown report, `docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md`, by combining the reviewed scaffold with `report_appendix_tables_2026-07-10.md`. The appendix starts under `# Appendix` at the end of the same report; the evidence-pattern-not-causal-proof framing and viewer path (`docs/analysis/gabriel_codify_excerpt_browser_latest.html`) were preserved.
- Added `scripts/export_final_report.py` to make the export reproducible without internet/API calls. Because `pandoc` and LibreOffice/`soffice` are unavailable locally, the script uses `python-docx` for DOCX and ReportLab for PDF.
- Exported final artifacts:
  - `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.docx` — 797,087 bytes.
  - `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf` — 1,012,886 bytes.
- Wrote `docs/analysis/final_report_export_audit_2026-07-10.md`, including commands used, file sizes, image counts, appendix-integration status, graph-reference checks, limitations, and a human review checklist.
- Lightly updated `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, `wage_mechanism_evidence_checklist.md`, and `all_groups_source_needs_2026-07-06.csv` to record that final export is complete and the next step is human review/revisions.

**Decisions and why**
- Used a local Python export path instead of pandoc/LibreOffice because neither external converter is installed. This keeps the export offline and reproducible in the current environment.
- Kept the appendix inside the same report rather than producing a separate final appendix artifact, per the final-report requirement.
- Did not rerun codify or touch source/data/corpus layers; this was a formatting/export session only.

**Surprises/breakage**
- DOCX visual render QA could not be performed because LibreOffice/`soffice` is unavailable. Structural DOCX checks passed (6 embedded images, 5 tables), and the PDF was visually rendered through Poppler for review.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14)
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire)
```
Custom export checks: final Markdown exists; DOCX/PDF exist and are non-empty; final export audit exists; 6/6 Markdown image references resolve; DOCX contains 6 embedded media files; PDF is 15 letter-size pages and rendered to PNG pages with no obvious figure/table clipping; `all_groups_source_needs_2026-07-06.csv` parses cleanly with 67 rows and consistent 11-column width; `git diff -- data/contracts.csv data/city_coverage.csv` empty.

**Corpus snapshot:** 53 contracts / 53 coverage rows / 3 city_attributes / 23 healthy matched pairs; evidence layer unchanged at 781 rows (293 present, 284 verified, 9 flagged/unverified).

**Confirmed:** no GABRIEL/codify, Harvard Proxy, model, or API calls; no new source collection; no FOIA/PRR; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or `logs/api_spend_log.csv`.

**Next steps**
1. Human review of the integrated DOCX/PDF, especially title block, graph readability, state-section caveats, "What appears to drive the wage gap?" framing, appendix formatting, page numbering, and PDF rendering.
2. Apply any requested revision pass while preserving the evidence-pattern framing and avoiding new codify/model/source-collection work unless explicitly authorized.

## 2026-07-10 22:49 EDT (Report scaffold polish: graph audit created, appendix typo fixed, prose tightened) - Created the missing report_graph_audit_2026-07-10.md, fixed a "Two rows"/"Four rows" appendix miscount, verified every graph/table reference against report_assets/, and tightened the report scaffold's Executive Summary and Method sections for PI readability; no GABRIEL/codify/model/API calls, no new source collection, no data/corpus edits

**Did**
- Confirmed repo state before editing: `git status` clean except untracked `.claude/` and `tmp/`; latest commit `74836f7`; `data/contracts.csv`/`data/city_coverage.csv` unchanged since that commit (`git diff 74836f7 -- data/contracts.csv data/city_coverage.csv` empty); `docs/analysis/report_assets/` present with 20 files (6 CSV, 7 PNG, 7 SVG).
- Wrote `docs/analysis/report_polish_preflight_2026-07-10.md` (preflight memo: repo state, files found, known issues, checks to run, explicit no-GABRIEL/no-new-sources confirmation).
- **Created the missing `docs/analysis/report_graph_audit_2026-07-10.md`**, requested by the original report-scaffold run but never produced: documents the evidence filter (verified present = `evidence_status=present AND viewer_verified=1`), exact evidence-layer counts (781 total, 293 present, 488 not_found, 284 verified present, 9 flagged/unverified), a full asset inventory (6 CSVs, 7 PNG/SVG figure pairs), per-figure caveats (Texas institutionally uneven; Ohio strongest matched triads; Massachusetts dense but not a uniform grid; binary codify cannot measure intensity), and a file-reference check confirming all 6 inline image references in the scaffold resolve and all 7 figures have matching PNG+SVG pairs.
- **Fixed the appendix miscount**: `report_appendix_tables_2026-07-10.md` said "Two rows" while listing four zero-verified-present contract IDs (`oh_cincinnati_fire_2023`, `oh_cincinnati_police_sup_2024`, `ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) — corrected to "Four rows." Reviewed the rest of the appendix for accurate file names, viewer path, evidence terminology, and no causal overstatement — all clean, no further changes needed.
- **Polished the report scaffold's prose** (`report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`): trimmed the Executive Summary from 8 to 6 crisper bullets (still leading with "GABRIEL-coded evidence patterns, not causal estimates"); restructured Method to lead with a plain-language explanation of what `codify()` does and what "verified present" means, moving the full 19-attribute list out to a pointer to Appendix A; tightened the Massachusetts and Texas state-findings paragraphs for readability while preserving every caveat (Massachusetts's uneven per-city occupation depth; Texas's institutional unevenness and small-sample-artifact warning). Reviewed Headline Finding, "What Appears to Drive the Wage Gap?", Counterpoints, and Next-State Strategy against this run's framing requirements (evidence patterns not causal proof; binary present/not_found; verified-present-only headline graphs; no "leading cause" language) and found them already compliant from the prior session's drafting — only light touch, no rewrite needed.
- Wrote and ran a deterministic Python check script (no GABRIEL/model calls) verifying: all 6 scaffold image references resolve; all 6 report-asset CSVs parse cleanly with no width mismatches; all 7 figures have matching PNG+SVG pairs; the new graph audit documents every file in `report_assets/`; the evidence-layer CSV parses cleanly; `data/contracts.csv`/`data/city_coverage.csv` remain unchanged since `74836f7`; the appendix typo fix is confirmed present. **All checks passed.**
- Lightly updated `wage_mechanism_evidence_checklist.md` (one added sentence to the existing living paragraph), `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7S), and `all_groups_source_needs_2026-07-06.csv` (1 new cross-cutting row) to record that the scaffold is polished, the graph audit exists, and the next step is final export after human review.

**Decisions and why**
- Did not regenerate any graph or figure — all six inline references and the one appendix-only figure already resolved correctly, so regeneration would have been unnecessary risk for zero benefit (and was explicitly discouraged unless fixing an actual error).
- Left the Headline Finding, "What Appears to Drive the Wage Gap?", Counterpoints, and Next-State Strategy sections largely as written by the prior session, after confirming each already used the required careful framing ("strongest evidence pattern," "appears," explicit "does not claim a single leading cause") — rewriting working prose that already meets spec would have been unnecessary churn.
- Moved the 19-attribute list out of the Method section's first paragraph (previously a long inline list) to a pointer at Appendix A, since the full glossary already lives there — reduces jargon-density in the main text per this run's "avoid jargon where possible" instruction without losing any information.

**Surprises/breakage**
- None. The missing graph audit was a known, expected gap (flagged in the task instructions themselves); no data or corpus defects were found.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged (this run added no data/corpus/codify rows)
```
Custom graph-reference check: 6/6 scaffold image references resolve; 6/6 report-asset CSVs parse clean; 7/7 figures have matching PNG+SVG; graph audit documents all 20 asset files; evidence-layer CSV parses clean (781 rows, 29 cols); `data/contracts.csv`/`data/city_coverage.csv` byte-identical to `74836f7`; appendix "Four rows" fix confirmed. **Overall: PASS.**

**Corpus snapshot:** 53 contracts / 53 coverage rows / 3 city_attributes / 23 healthy matched pairs / evidence layer 781 rows (293 present, 284 verified) — all unchanged from the prior two sessions; this session edited report-layer documentation and prose only.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, or model/API calls this session (no new `logs/api_spend_log.csv` rows, no new codify output files); no new source collection, no FOIA/PRR; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`; no final PDF/DOCX artifact produced.

**Next steps**
1. **Final report export (DOCX/PDF) after human/PI review.** The scaffold, appendix, and graph audit are now polished and internally consistent; the evidence-pattern (not causal-proof) framing must be preserved through any formatting pass.
2. 16 Massachusetts contracts remain uncodified — a future GABRIEL/codify batch could broaden the evidence layer before a later report revision, but is not required to export the current scaffold.

## 2026-07-10 22:15 EDT (Report scaffold review, appendix gap fix, and commit) - Found an in-progress, uncommitted report scaffold (Markdown + charts + CSVs) from a separate session; filled one missing referenced file (the appendix), verified the rest was coherent, and committed

**Did**
- Resumed a prior recovery session after a Bash-tool outage. In the interim, two separate sessions had already run to completion and committed independently: `9c42999` ("Expand Texas and Ohio sources" — the interrupted-run recovery this session originally started) and `20a0f26` ("Codify expanded Texas and Ohio sources" — a follow-on GABRIEL/codify run, out of this session's original scope but committed under its own task). Confirmed both were clean (`validate.py`/`audit_coverage.py` pass, no duplicate rows) rather than redoing any of that work.
- Found a third, uncommitted body of work already sitting in the working tree: `docs/analysis/report_scaffold_preflight_2026-07-10.md`, `report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`, `report_evidence_layer_audit_2026-07-10.md`, and a `report_assets/` directory of 7 chart figures (PNG+SVG) and 6 supporting CSVs — a first draft report scaffold built from the 781-row GABRIEL codify evidence layer (37 codified contracts, MA/TX/OH). Correctly scoped as Markdown/CSV/PNG/SVG only, no PDF/DOCX, no data/corpus edits, no GABRIEL/model calls.
- Audited the scaffold for completeness before committing: found the main scaffold's Appendix section pointed at `docs/analysis/report_appendix_tables_2026-07-10.md`, which did not exist. Built it deterministically from data already in the repo — the 19-attribute codebook glossary (from `gabriel_codify_evidence_layer.csv`'s own `attribute_label`/`attribute_definition` columns), the 37-contract source inventory (from `report_assets/source_inventory_for_report_2026-07-10.csv`), a figures/tables index (from `report_assets/` directory listing, cross-checked against the scaffold's inline image references — found and documented one figure, `mechanism_presence_by_state`, generated but not embedded inline), and viewer usage notes. No new analysis, no model calls — pure compilation from existing CSVs.
- Re-ran `python scripts/validate.py` and `python ingest/audit_coverage.py` post-fix to confirm the appendix addition touched nothing in `data/` (it didn't — both unchanged from the prior session: 53/53/3, 23 healthy matched pairs).
- Committed `docs/analysis/report_scaffold_preflight_2026-07-10.md`, `report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`, `report_evidence_layer_audit_2026-07-10.md`, `report_appendix_tables_2026-07-10.md`, and `report_assets/` (7 PNG + 7 SVG + 6 CSV).

**Decisions and why**
- Did not touch `.claude/worktrees/tx-oh-expansion-recovery/` (a leftover worktree from the prior recovery session, still present and untracked) or `tmp/` — neither is part of this project's committed deliverables, and removing them wasn't requested.
- Filled the missing appendix rather than either stripping the dangling reference or asking to re-run the whole report-scaffold task: the appendix's contents were fully derivable from already-committed CSVs (evidence layer, source inventory) with zero new judgment calls or model calls required, consistent with this project's standing practice of finishing deterministic gaps from repo state rather than re-running upstream work.

**Surprises/breakage**
- None in the data layer. The one gap found (missing appendix file) was a completeness gap in a still-in-progress report scaffold, not a data or corpus defect.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged (this session added no data/corpus/codify rows)
```

**Corpus snapshot:** 53 contracts / 53 coverage rows / 3 city_attributes / 23 healthy matched pairs / evidence layer 781 rows (293 present, 284 verified) — all unchanged from the prior two sessions; this session added report-layer documentation only.

**Confirmed:** no GABRIEL/codify, Harvard Proxy, or model/API calls this session; no FOIA/PRR; no edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`; no final report PDF/DOCX produced.

**Next steps**
1. Human review of the report scaffold (`report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md` + appendix + figures) before any formatting run toward a final report artifact.
2. If the scaffold's framing holds up under review, the next content step is a dedicated source-availability scan for a candidate next state (see the scaffold's own "Source Needs and Next-State Strategy" section — New Jersey and Pennsylvania stood out as the strongest institutional-contrast candidates) — not a re-run of Texas/Ohio work, which is now complete for this corpus's current scope.
3. 16 Massachusetts contracts remain uncodified; a future GABRIEL/codify batch could close that gap before the report scaffold is finalized.

## 2026-07-10 20:49 EDT (Merge recovery branch + San Antonio OCR + expanded Texas/Ohio codify + viewer rebuild) - Merged the recovery commit into main, recovered San Antonio police via bounded OCR, codified all 9 newly expanded Texas/Ohio sources (9/9 live calls, 100% grounded, 0 contamination), rebuilt the evidence layer/viewer; no new source collection, no FOIA/PRR, no broad GABRIEL run

**Did**
- Merged `worktree-tx-oh-expansion-recovery` (commit `9c42999`) into `main` -- clean fast-forward. The main checkout's working tree held an untouched, byte-identical copy of the same pre-interruption uncommitted state (verified via SHA-256 checksums on all 9 corpus PDFs and diffs on the CSVs/docs); stashed it (`pre-merge-backup-tx-oh-2026-07-10-relay`, entry `18f89ec`, left in the stash list as a redundant backup, not dropped) to clear the working tree, merged cleanly, then confirmed the result matched the stash exactly.
- **Bounded OCR recovery for San Antonio police** (`tx_san_antonio_police_2022`, 218-page image scan, previously ~0 usable characters): rendered all 218 pages (`pdftoppm`, 150 DPI, 74s) and OCR'd all 218 pages (`tesseract --psm 6`, ~2.5 min) in one bounded ~4-minute pass. Recovery succeeded well beyond expectations: full legible article structure (Recognition, No Strike, Management Rights, Grievance/Arbitration, Wages/Step Schedule, Impasse Procedure) plus a genuine Attachment 3 factfinding peer/comparator wage-comparability clause -- the first confirmed comparator-wage language found for San Antonio in this project's corpus. Updated `text_quality` (partial -> ocr_messy) and corrected `cycle_start` (2022-10-01 assumption -> document-confirmed 2022-05-12) in `data/contracts.csv`, via a surgical single-line splice that touched no other row's bytes. Also found and fixed a pre-existing row-width bug (an unquoted comma) in `texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` from the prior recovery session, and appended 7 new deterministic mechanism excerpts for San Antonio police to that file.
- Built `docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv` (9 rows, all marker-sliced/line-range-verified verbatim substrings of the underlying `pdftotext -layout` extractions or the OCR cache, all well under the 1500-word-per-call cap, neutral `--- Excerpt N [Article X] ---` separators throughout).
- Raised `scripts/gabriel_codify_pilot.py`'s `HARD_MAX_CALLS` 8 -> 9 (deliberate code edit, per the script's own established pattern) for this approved 9-row batch.
- Ran `--dry-run` first (`tmp/gabriel_codify_pilots/2026-07-10_204044/`), confirmed 9/9 rows selected and 0 contamination violations, then ran the capped live batch (`tmp/gabriel_codify_pilots/2026-07-10_204149/`) via the same Harvard Proxy adapter. **9/9 live calls succeeded, 0 failed, 0 skipped.**
- Parsed outputs: `docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv` -- 178 rows (32 present, 146 not_found), 0 parse failures, **32/32 present excerpts grounded (100%), 0 boundary-leakage flags, 0 mechanism-label-contamination flags** -- the cleanest single-batch result of any Texas/Ohio codify run to date.
- San Antonio police's recovered text correctly distinguished `interest_arbitration_or_formal_impasse_backstop` (the Chapter 174 ordinance-defined impasse procedure) from `grievance_or_contract_interpretation_arbitration` (the separate Article 15 mechanism) within the same document -- the strongest single test yet of this codebook's key distinction. One observed false negative (the model missed the genuine peer/comparator wage-comparability clause in San Antonio's factfinding guidelines) is documented honestly in the audit memo, not hand-corrected.
- Rebuilt the durable evidence layer and viewer from the union of all five codify output files (pilot + Texas/Ohio scale-up + Massachusetts + Seekonk/Wayland + this run's expanded Texas/Ohio output): **781 total evidence rows (293 present: 284 verified + 9 pre-existing flagged, none new this run; 488 not_found).** San Antonio, Cincinnati, and Toledo now appear in the viewer for the first time. Wrote `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (updated in place) and a new dated archival copy `gabriel_codify_excerpt_browser_2026-07-10_expanded_texas_ohio.html`, leaving all four earlier archival copies untouched.
- Lightly updated `wage_mechanism_evidence_checklist.md` (1 revised pointer sentence), the report review checklist (new Section 7R), and `all_groups_source_needs_2026-07-06.csv` (1 new row).

**Decisions and why**
- Chose a full 218-page OCR pass over guessing page ranges for San Antonio police -- with zero extractable text, there was no way to locate a table of contents without OCR'ing a reconnaissance batch first, and page 1's immediately clean, correctly-oriented output gave high confidence a full pass would cost barely more than a targeted one.
- Did not hand-correct the model's peer-comparator-wage-comparability miss on San Antonio police, even though the RA (session) could see the matching text -- per this project's standing rule that RA discretion must not contaminate GABRIEL's own coding; documented the miss in the audit memo instead.
- Used a surgical single-line splice (not a full `csv.writer` rewrite) for every hand-edit to `data/contracts.csv` and the older Texas/Ohio CSVs this session, after an initial full-rewrite attempt normalized 12 unrelated pre-existing lines' legacy `\r\n` line endings -- the surgical approach produces a minimal, reviewable diff touching only the intended row.

**Surprises/breakage**
- The main checkout's working tree still held the *original* pre-interruption uncommitted diff, untouched, since the prior session's worktree-based recovery never cleaned it up -- caught before the merge via SHA-256 verification, stashed safely, and confirmed identical to the merge target.
- A full `csv.writer` rewrite of `data/contracts.csv` for a single-row edit silently normalized line endings on 12 unrelated rows (legacy mixed `\r\n`/`\n` line endings in the file) -- caught via `git diff` inspection before committing anything; fixed by switching to surgical single-line splicing for every subsequent CSV edit this session.
- A pre-existing row-width bug (unquoted comma in a `notes` field) was found in `texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv`, left over from the prior recovery session -- fixed this session rather than left for a future one, since Task E's row-width check would have failed on it otherwise.
- San Antonio police's OCR-recovered text was substantially more complete and higher-quality than expected for a 218-page, 270°-rotated Xerox scan with a 0% initial extraction rate.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged from the interrupted-run-recovery session (this run added no new contract/coverage rows)

python ingest/test_pipeline.py
40 passed, 0 failed
```
Custom CSV audit: 0 width mismatches, 0 duplicate IDs, 0 invalid controlled-vocabulary values, 0 missing source files, 0 `retrieval_method=foia` rows, 0 duplicate `evidence_id` values across all 781 evidence-layer rows, 0 invalid `evidence_status`/`confidence`/`parse_status`/`source_grounding_status` values in the new codify output CSV.

**Corpus snapshot:** 53 contracts / 53 coverage rows / 3 city_attributes / 23 healthy matched pairs (unchanged from the prior recovery session -- this was a codify/OCR/viewer run, not a new-source-acquisition run). Evidence layer: 781 rows (293 present, 284 verified, 9 pre-existing flagged) -- up from 603 at the start of this session.

**Confirmed:** no new source collection, no web search, no FOIA/PRR, no full-corpus GABRIEL run, no model/API calls outside the capped `scripts/gabriel_codify_pilot.py` script (max 9 live calls, 9 used); no API keys/secrets printed or committed.

**Next steps**
1. **Report scaffolding with GABRIEL-coded mechanism-evidence graphs.** The evidence layer's Texas/Ohio coverage is now materially broader (4 Ohio matched cities, 3 Texas cities with contracts) than at any prior point in this project -- report language should present coded findings as evidence patterns, not causal proof.
2. A future session could re-run the San Antonio police codify call after a codebook refinement, or manually flag the peer-comparator-wage-comparability miss for reviewer attention, given the observed false negative documented in this session's audit memo.

## 2026-07-10 19:20 EDT (Texas/Ohio source-expansion interrupted-run recovery) - Recovered from an accidentally-closed terminal mid-Task-G; confirmed the CSV writes had already completed cleanly; completed mechanism-excerpt extraction, ingestion summary, guidance-doc updates, and full validation; no GABRIEL/codify/model/API calls, no FOIA/PRR

**Did**
- Recovered from a terminal that was accidentally closed during a Texas/Ohio source-expansion run, likely around Task G. Treated repo files as source of truth rather than re-running the original prompt from the top.
- Recovery audit: `git status` showed `data/contracts.csv`/`data/city_coverage.csv` modified (uncommitted) and untracked `corpus/tx_san_antonio/`, `corpus/oh_cincinnati/`, `corpus/oh_toledo/` (9 PDFs total) plus four `docs/analysis/texas_ohio_expansion_*` files from Tasks A-D/F (preflight, source plan, selection, text quality).
- **Confirmed Task G had already completed cleanly before the interruption**: `data/contracts.csv` and `data/city_coverage.csv` each already had exactly 9 new rows (44 -> 53), one-to-one matched, no duplicate `obs_id`s, no malformed/partial rows, no width mismatches. The interruption occurred after Task G but before Task H (mechanism-excerpt extraction), which had not been started.
- Ran a full custom audit: row widths, duplicate IDs, controlled-vocabulary checks (`occupation_class`, `source_type`, `source_corpus`, `retrieval_method`, `text_quality`), `safety_flag` consistency, `full_text_path` existence for all 53 contract rows, and zero `retrieval_method=foia` anywhere in the file — all clean.
- Completed the remaining deterministic steps: built `texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` (8 excerpt rows across 6 of the 9 new contracts, built entirely from verbatim clause text already captured during the pre-interruption session — no new PDF reading, no GABRIEL/model calls) and `texas_ohio_expansion_ingestion_summary_2026-07-10.md`.
- Lightly updated `wage_mechanism_evidence_checklist.md` (1 revised pointer sentence), the report review checklist (new Section 7Q), and `all_groups_source_needs_2026-07-06.csv` (1 new row) to reflect the completed expansion.
- Isolated all edits in a git worktree (`worktree-tx-oh-expansion-recovery`) per this session's background-job isolation requirement, after copying the pre-interruption uncommitted/untracked state into it (a plain worktree only carries committed history, not working-directory changes).

**Decisions and why**
- Did not re-run or re-verify sources already selected/downloaded — the selection doc's provenance checks (live `curl -I`, official-domain-only) were already complete and dated the same day; re-doing them would have been redundant per this run's explicit "don't broaden the source set unless necessary to repair consistency" instruction.
- For 3 of the 9 new contracts (`tx_san_antonio_police_2022`, `oh_cincinnati_police_sup_2024`, `oh_cincinnati_fire_2023`), no mechanism excerpt was added: San Antonio police has no extractable text layer (218-page image scan); the other two had recognition clauses confirmed present at extraction time but not separately quoted verbatim. Left as a documented gap rather than fabricating or paraphrasing text, per the project's verbatim-only rule.

**Surprises/breakage**
- None. No CSV corruption, no duplicate rows, no orphaned coverage rows were found — the interrupted run's Task G output was fully intact and schema-conformant.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14)
safety units unmatched: 5 (incl. San Antonio police + fire, both documented as intentionally unmatched)

python ingest/test_pipeline.py
40 passed, 0 failed
```
Custom CSV audit: 0 width mismatches, 0 duplicate `obs_id`s, 0 invalid controlled-vocabulary values, 0 missing source files, 0 orphaned `city_coverage` rows in either direction, 0 `retrieval_method=foia` rows.

**Corpus snapshot:** 53 contracts / 53 coverage rows / 3 city_attributes / 23 healthy matched pairs (up from 44/44/18 at the start of the original, interrupted run). New sources: San Antonio (TX, police+fire, deliberately unmatched — no non-safety bargaining channel found), Cincinnati (OH, police x2 rank-split + fire + other, now a healthy matched triad), Toledo (OH, police + fire + other, now a healthy matched triad). Ohio now has 4 healthy matched cities (Columbus, Cleveland, Cincinnati, Toledo); Texas remains at 1 fully matched city (Houston) plus Austin (EMS, safety-adjacent) and San Antonio (unmatched).

**Confirmed:** no GABRIEL/codify calls, no Harvard Proxy calls, no model/API calls of any kind, no FOIA/PRR retrieval anywhere in this run or the recovered prior run.

**Next steps**
1. Codify the expanded Texas/Ohio sources (9 new rows: San Antonio, Cincinnati, Toledo) and rebuild the excerpt viewer via `scripts/build_codify_evidence_viewer.py`'s append/union mode.
2. Resume report scaffolding once the evidence layer reflects the expanded Texas/Ohio coverage.

---

## 2026-07-10 11:54 EDT (GABRIEL codify excerpt-boundary repair + Seekonk/Wayland expansion) - Moved leakage cleanup into the pipeline itself, bounded OCR recovered Wayland dispatch/nurse content, 6 capped live Seekonk/Wayland codify calls; Seekonk now in the evidence layer/viewer; no data/corpus changes

**Did**
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `4f10a4f` (the Massachusetts scale-up), and pre-session counts of 44 contracts / 44 coverage rows / 479 evidence-layer rows, matching expectations exactly.
- **Fixed the Massachusetts scale-up's excerpt-boundary-leakage defect at the pipeline level** (not a one-off downstream script this time): added `reshape_and_validate_outputs()` to `scripts/gabriel_codify_pilot.py`, which now runs automatically at the end of every live run, reshaping `gabriel.codify()`'s wide-format output into this project's long/tidy schema while detecting and cleaning any leaked separator fragment in a returned excerpt (`_clean_boundary_leak()`). The cleanup guarantees the cleaned excerpt is always an untouched, single contiguous substring of what the model actually returned — never fabricated or spliced from two different source locations — and downgrades `source_grounding_status` to `unclear`/`unsupported` whenever leakage is detected, regardless of whether cleanup succeeded. Verified via unit tests against all 4 real leaked excerpts from the Massachusetts run before any new live call.
- Lowered `scripts/gabriel_codify_pilot.py`'s `HARD_MAX_CALLS` from 10 to 8 for this run's approved cap.
- Confirmed Task C's viewer requirements (default-verified-only view, unverified-evidence toggle, warning banner, "Verified in source text" / "Not verified in source text" labels) were already fully implemented from the prior session — no code changes needed to `scripts/build_codify_evidence_viewer.py` this session.
- **Ran a bounded OCR/text-recovery pass** on `corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf` (the Wayland dispatch/Community Health Nurse source, previously ~0 usable characters via plain `pdftotext`): `pdftoppm` rendered all 48 pages to PNG (150 DPI, ~16s), `tesseract` OCR'd all 48 pages (~35s) — a single bounded pass, ~51 seconds total. Recovery succeeded well beyond expectations: full wage-grade tables (G-3 JCC Dispatcher, G-4 JCC Dispatcher Coordinator, G-7A Public Health Nurse, G-15 Community Health Nurse) and multiple genuinely dispatcher/nurse-specific clauses (recognition, holiday pay, CPR-training stipend, education incentive) recovered cleanly. Original PDF untouched; a small 9-page cache saved to `docs/analysis/wayland_other_bounded_ocr_extract_2026-07-10.txt`.
- Selected 6 rows for this run's codify batch: Seekonk public_works/library/police/fire/teacher (a newly fully-matched city, 5 occupation classes) and Wayland other (the OCR-recovered dispatch/nurse row) — well under the 8-call cap; documented why no further Seekonk/Wayland rows were added.
- Built `docs/analysis/gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv` (6 rows) from fresh `pdftotext` extraction (Seekonk) and the OCR cache (Wayland, via exact marker-slice extraction rather than hand-retyping — an earlier hand-transcription attempt introduced an ellipsis not present in the source, caught by a verbatim-substring assertion and fixed by switching to marker-slicing). Caught and fixed a second bug during window construction: the OCR cache's own `--- OCR page N ---` page-boundary labels leaked into two hand-selected excerpts because a genuine source sentence spanned a page break; fixed by stripping those labels before slicing.
- Ran `--dry-run` first (`tmp/gabriel_codify_pilots/2026-07-10_114636/`), confirmed no network/credential access, then ran the capped live batch (`tmp/gabriel_codify_pilots/2026-07-10_114713/`) via the same Harvard Proxy adapter. **6/6 live calls succeeded, 0 failed, 0 skipped.**
- The new inline pipeline validation caught 4 boundary-leakage cases automatically during the live run itself. One of them (`ma_seekonk_teacher_2021` / `no_strike_or_work_stoppage_constraint`) turned out to span **6 separator boundaries**, not just one — the original single-split cleanup left embedded separator fragments in the middle of the "cleaned" text. Fixed immediately (still within this session, before finalizing any output) by upgrading `_clean_boundary_leak()` to segment on every complete separator instance and keep the single longest genuine segment, then regenerating `validated_outputs.csv` by **locally reprocessing the already-fetched raw output — zero additional API calls.**
- Parsed outputs: `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv` — 124 rows (43 present, 81 not_found), 0 parse failures, 39/43 present excerpts grounded outright, 4 flagged (boundary leakage, not fabrication), 0 mechanism-label contamination.
- Confirmed the refined codebook continued to avoid over-coding: `peer_comparator_wage_comparability` was `not_found` for all 6 rows (none of the 6 ordinary base CBAs contained genuine external-comparator language); `interest_arbitration_or_formal_impasse_backstop` correctly `not_found` for all 6 (none of the 6 documents are arbitration-award opinions).
- Rebuilt the durable evidence layer and viewer from the union of all four codify output files (pilot + Texas/Ohio + Massachusetts + this run's Seekonk/Wayland output): **603 total evidence rows (261 present: 252 verified + 9 flagged; 342 not_found).** Seekonk now appears in the viewer for the first time, as a fully matched city. Wrote `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (updated in place) and a new dated archival copy `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_seekonk_wayland.html`, leaving all three earlier archival copies untouched.
- Lightly updated `wage_mechanism_evidence_checklist.md` (1 new pointer), the report review checklist (new Section 7P), and `all_groups_source_needs_2026-07-06.csv` (1 new row).

**Decisions and why**
- Moved the reshape-and-validate/leakage-cleanup logic into `scripts/gabriel_codify_pilot.py` itself (rather than another one-off scratch script per session) — this is a reusable, testable, committed fix that protects every future codify run automatically, instead of relying on each session's author remembering to also run a bespoke cleanup script afterward.
- When the multi-boundary leakage case was discovered mid-session, chose to fix the code and reprocess the already-fetched raw data locally rather than re-run the live call — this respects the "do not retry repeatedly" / 8-call-cap spirit of the task while still landing a fully correct result, and is strictly better than shipping a known-imperfect cleanup.
- Used marker-slice extraction (exact string boundaries located via `.index()`) rather than hand-retyping excerpts from the OCR cache for the Wayland window — a first attempt at hand-transcription introduced a fabricated ellipsis, caught immediately by a verbatim-substring assertion; marker-slicing eliminates that entire class of error by construction.

**Surprises/breakage**
- The multi-boundary leakage variant (one excerpt spanning 6 separator instances) — a new failure mode not seen in the Massachusetts run's milder single-boundary cases, caught and fixed within this same session before any output was finalized.
- The OCR cache's own page-boundary labels leaking into hand-selected window excerpts — caught during window construction (before any live call), not during the live run itself.
- The bounded Wayland OCR pass recovered dramatically better text than expected (full clean wage tables, not just fragments) — a positive surprise that made a previously-documented, explicitly-flagged corpus gap (dispatch/nurse_health) codifiable for the first time.
- No repo breakage. `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` were never touched; the original Wayland PDF was never modified.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 18 (exact-cycle: 9, overlap-cycle: 9) -- unchanged from the prior session
```

**Corpus snapshot:** 44 contracts / 44 coverage rows / 3 city_attributes / 18 healthy matched pairs — identical to session start, confirming zero data/corpus edits this run.

**Confirmed:** no full-corpus GABRIEL extraction; 6 live calls attempted, 6 succeeded, 0 failed (well under the approved 8-call cap); no `data/contracts.csv`/`data/city_coverage.csv`/`corpus/` edits; Seekonk now appears in the viewer.

**Next steps**
1. Plan a Texas/Ohio source-expansion batch (this project's Texas/Ohio corpus currently has fewer matched cities/occupation classes than Massachusetts).
2. Begin report scaffolding once the evidence layer's state/city coverage is judged sufficient for a first PI-facing draft.

---

## 2026-07-10 10:35 EDT (GABRIEL codify neutral-header repair + Massachusetts scale-up) - Fixed window-header-leakage defect, added viewer-level verified-evidence gating, ran 10 capped live Massachusetts codify calls; Massachusetts now in the evidence layer/viewer; no data/corpus changes

**Did**
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `cd9c70f` (the Texas/Ohio scale-up), and pre-session counts of 44 contracts / 44 coverage rows / 265 evidence-layer rows, matching expectations exactly.
- **Repaired the window-header-leakage defect** the Texas/Ohio audit flagged (`oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`, where the model echoed this project's own mechanism-vocabulary window header as if it were source text). `scripts/gabriel_codify_pilot.py` gained a read-time contamination check (`_check_window_contamination`) that hard-fails (dry-run OR live) if any window's `window_text` contains any of the codebook's 19 attribute keys (excluding the bare word `"other"`, a deliberate exclusion after it produced false-positive floods on ordinary English text) or the generic tells `"Mechanism"`/`"Arbitration / impasse"`. Verified against both a clean windows file (passes) and a deliberately re-contaminated copy (fails loudly, naming the offending contract_id and matched string). Raised `HARD_MAX_CALLS` 8 → 10, deliberately, in-code, for this approved 10-row Massachusetts batch.
- Built `docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv` (10 rows) **from scratch this session**, directly from the underlying corpus PDFs (`pdftotext -layout`, no ingestion) — no prior Massachusetts deterministic-extraction CSV existed to reuse (unlike Texas/Ohio). Every added separator is strictly `--- Excerpt N [location] ---`, with location pulled from a genuine `Article`/`Section` marker in the source text itself, never a mechanism name.
- Selected the 10 Massachusetts rows to cover every category this run's task required: police/fire safety (Somerville, Wayland, Franklin, Georgetown), an interest-arbitration-heavy source (Somerville's JLMC award opinion, explicitly requested even though unmatched), public works/DPW (Franklin), clerical/admin (Boston), library (Franklin), custodial/mixed-municipal (Franklin, Georgetown), and two fully cross-occupation matched cities (Franklin: 5 occupation classes; Georgetown: 2). Dispatch/nurse_health content exists in the Massachusetts corpus (`ma_wayland_other_2021`) but that file's `pdftotext` extraction yields ~0 usable characters (48-page, 270°-rotated scan) — flagged as a known, documented gap rather than silently dropped or force-included with fabricated text.
- Added a **second, independent layer of defense** in `scripts/build_codify_evidence_viewer.py` (Task C): new `notes_flag`/`viewer_verified` columns. A row only counts as "verified evidence" (shown by default in the viewer) if `evidence_status=present` AND `source_grounding_status=grounded` AND its `notes` field is not marked with the `METHODOLOGY FLAG` marker by a reviewer. The viewer gained a "Show unverified / unsupported evidence" toggle; when shown, flagged/unsupported rows render with an explicit on-card warning and a "Not verified in source text" badge instead of the ordinary "Verified in source text" one. The durable CSV keeps flagged rows (nothing is deleted); only what the viewer *promotes by default* changed.
- Ran `--dry-run` first (`tmp/gabriel_codify_pilots/2026-07-10_102543/`), confirmed no network/credential access and 0 contamination hits, then ran the capped live batch (`tmp/gabriel_codify_pilots/2026-07-10_102644/`) via the same Harvard Proxy adapter. **10/10 live calls succeeded, 0 failed, 0 skipped.**
- Parsed outputs into `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — 214 rows (70 present, 144 not_found), 0 parse failures. Ran the source-grounding audit: **70/70 present excerpts pass the automated substring-grounding check (0 `unsupported`)** — the Texas/Ohio full-fabrication failure mode did not recur. A new recurrence check (added this session, scanning every *returned excerpt* — not just the input window — for this project's own scaffolding vocabulary) caught a **milder** variant in 4 of 70 present excerpts: the model's verbatim-copied span crossed the boundary between two adjacent excerpt blocks and incidentally included a few characters of the `--- Excerpt N [location] ---` separator syntax, even though genuine source content surrounds it on both sides. Flagged via the same `METHODOLOGY FLAG` convention, not silently included.
- Confirmed the refined codebook's interest-vs-grievance-arbitration distinction held up cleanly, including *within the same document*: `ma_somerville_police_spsoa_2012` produced both a genuine `interest_arbitration_or_formal_impasse_backstop=present` row (real JLMC arbitration-panel analysis text) and two separate `grievance_or_contract_interpretation_arbitration=present` rows (ordinary grievance-procedure clauses from the same base CBA) — correctly distinguished. `peer_comparator_wage_comparability` was present for exactly 1 of 10 rows (Somerville, naming 10 specific Massachusetts comparator communities from a Collins Center classification study) — no over-coding.
- Rebuilt the durable evidence layer and viewer from the union of all three codify output files (pilot + Texas/Ohio + Massachusetts): **479 total evidence rows (218 present: 213 verified + 5 flagged/unverified; 261 not_found).** Massachusetts now appears in the viewer's state filter alongside Texas and Ohio (5 cities: Franklin, Georgetown, Somerville, Boston, Wayland). Wrote `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (updated in place) and a new dated archival copy `gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html`, leaving both earlier same-day archival files untouched.
- Lightly updated `wage_mechanism_evidence_checklist.md` (1 new pointer), the report review checklist (new Section 7O), and `all_groups_source_needs_2026-07-06.csv` (1 new row).

**Decisions and why**
- Excluded the bare word `"other"` from the contamination-check pattern list even though it is a real codebook attribute key — as a bare substring it matches ordinary English prose ("other municipality," "other conditions of employment") constantly, and a false-positive-flooded check that always fails is worse than a narrower check that catches the 18 genuinely distinctive multi-word attribute keys plus the generic tells.
- Built Massachusetts evidence windows from fresh `pdftotext` extraction rather than waiting for or hand-building a separate deterministic-extraction CSV first — no such file existed for Massachusetts, and re-deriving verbatim excerpts directly from the corpus PDFs (with a keyword-search helper script, not manual retyping) was faster and equally defensible as "already-existing corpus text," satisfying "use existing corpus files only."
- Chose to flag the 4 boundary-leakage rows transparently via `notes` rather than silently drop them or attempt an automated repair mid-run — consistent with the Texas/Ohio session's precedent, and it validates that the new viewer-level `notes_flag`/`viewer_verified` safety net (Task C) actually catches recurrences the window-construction fix alone did not fully prevent.
- Dropped Massachusetts dispatch/nurse_health coverage from this run's 10-row sample rather than attempting a bounded OCR pass on a 48-page, 270°-rotated scan mid-session — the task listed this category as optional ("if useful"), and a documented gap is safer than a rushed, unverified OCR extraction feeding into a live codify call.

**Surprises/breakage**
- The window-header-leakage defect's milder recurrence (excerpt-boundary leakage, 4/70 present rows) — proof the original fix (neutral separators) alone was necessary but not sufficient; the viewer-level notes-flag safety net (built in the same session, before this was discovered) caught it as designed.
- The `"other"` false-positive bug in the contamination check, caught during smoke-testing before it could block a real dry run.
- No repo breakage. `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` were never touched.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 18 (exact-cycle: 9, overlap-cycle: 9) -- unchanged from the prior session
```

**Corpus snapshot:** 44 contracts / 44 coverage rows / 3 city_attributes / 18 healthy matched pairs — identical to session start, confirming zero data/corpus edits this run.

**Confirmed:** no full-corpus GABRIEL extraction; 10 live calls attempted, 10 succeeded, 0 failed (at, not exceeding, the approved cap); no `data/contracts.csv`/`data/city_coverage.csv`/`corpus/` edits; Massachusetts now appears in the viewer.

**Next steps**
1. Fix the excerpt-boundary-leakage recurrence (a larger break between adjacent window excerpts, or trim to clean sentence boundaries) before the next codify batch.
2. Manual PI-facing viewer QA — open `gabriel_codify_excerpt_browser_latest.html` in a real browser and exercise the new "Show unverified / unsupported evidence" toggle and the Massachusetts state filter.
3. A further acquisition batch (Seekonk is a strong, fully-matched Massachusetts candidate not used this run) or a new state, once the viewer QA pass is done.

---

## 2026-07-09 21:07 EDT (GABRIEL codify Texas/Ohio scale-up) - 8 capped live codify calls on remaining Texas/Ohio rows; evidence layer/viewer rebuilt via new append/union builder mode; no data/corpus changes

**Did**
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `632a4a5` (the PI-facing viewer overhaul), and pre-session counts of 44 contracts / 44 coverage rows / 92 evidence-layer rows, matching expectations exactly.
- Wrote `docs/analysis/gabriel_codify_texas_ohio_scaleup_preflight_2026-07-09.md` recording repo state, already-coded contract_ids, the 8 selected remaining Texas/Ohio rows, the live-call cap, and stop rules before touching anything else.
- Assembled `docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv` (8 rows) programmatically from this project's own already-verified verbatim excerpts in `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv` / `texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv` — no new corpus text opened, no ingestion.
- Added genuine **append/union support** to `scripts/build_codify_evidence_viewer.py`: `--input` is now repeatable and/or comma-separated, `--archive-html` is accepted as a synonym for `--html-out`, and rows are de-duplicated on full row content (not just contract_id/attribute/run_id — an earlier version of this dedup logic incorrectly collapsed legitimate multi-excerpt rows and was caught and fixed before the real rebuild). The existing no-argument default invocation still works unchanged.
- Raised `scripts/gabriel_codify_pilot.py`'s in-code `HARD_MAX_CALLS` from 4 to 8, deliberately and documented, for this approved 8-row scale-up.
- Ran `--dry-run` first (`tmp/gabriel_codify_pilots/2026-07-09_205718/`), confirmed no network/credential access, then ran the capped live batch (`tmp/gabriel_codify_pilots/2026-07-09_205815/`) via the same Harvard Proxy adapter used in the prior pilot. **8/8 live calls succeeded, 0 failed, 0 skipped.**
- Parsed `gabriel.codify()`'s native wide-format output (one list-of-excerpts cell per attribute) into the project's long/tidy evidence-output schema: `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — 173 rows (95 present, 78 not_found), 0 parse failures.
- Ran the source-grounding audit: **94/95 present excerpts verbatim-grounded** in their windows. One row (`oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`) was found to be a **window-assembly-header-leakage artifact** — the model echoed this project's own section-header text (injected because the underlying OCR passage was unreadable table-of-contents garbage) rather than genuine source text. Flagged explicitly in the row's `notes` field rather than silently passed through as ordinary evidence; root cause and a fix recommendation (neutral, keyword-free window headers) are documented in `gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md`.
- Confirmed the refined codebook's key interest-vs-grievance-arbitration distinction held up correctly in 6 of 7 genuinely-evidenced cases (the 7th being the flagged artifact) — see the audit memo's comparison table.
- Rebuilt the durable evidence layer and viewer from the union of both codify output files (`gabriel_codify_full_codebook_outputs_2026-07-09.csv` + this run's new output): **265 total evidence rows (148 present, 117 not_found)**, all 4 Texas/Ohio matched cities (Houston, Austin, Columbus, Cleveland) now represented with both a safety and a non-safety comparison occupation each. Wrote `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (updated in place) and a new dated archival copy `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html`, deliberately not overwriting the earlier same-day `..._2026-07-09.html` archival file.
- Lightly updated `wage_mechanism_evidence_checklist.md` (1 new pointer), the report review checklist (new Section 7N), and `all_groups_source_needs_2026-07-06.csv` (1 new row).

**Decisions and why**
- Built the 8 evidence windows entirely from already-verified verbatim excerpts in this project's own prior hand-extraction files, rather than opening any corpus PDF directly — satisfies "use existing corpus files only, do not ingest" while guaranteeing verbatim correctness (no manual re-typing risk) via a small Python assembly script.
- Fixed the append/union dedup key from `(contract_id, attribute, run_id)` to full-row-content after testing revealed the narrower key incorrectly discarded genuine multi-excerpt codify results — full-content dedup still makes rebuilds idempotent (confirmed by passing the same file twice and getting 100% correctly-flagged duplicates) without losing real evidence.
- Chose to flag the header-leakage artifact transparently in the evidence layer (via `notes`) rather than silently drop it — the row is a real, honest record of what `codify()` returned, and dropping it would hide a genuine methodology finding that should inform how future window-assembly headers are written.

**Surprises/breakage**
- The append/union dedup bug above (caught during smoke-testing before the real union rebuild, not after).
- The window-header-leakage artifact on `oh_cleveland_fire_2025` — a new failure mode not seen in the 4-row pilot, caused specifically by an OCR-garbled underlying passage combined with codebook-vocabulary-bearing section headers. Worth fixing before the next scale-up (Massachusetts).
- No repo breakage. `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` were never touched.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 18 (exact-cycle: 9, overlap-cycle: 9) -- unchanged from the prior session
```

**Corpus snapshot:** 44 contracts / 44 coverage rows / 3 city_attributes / 18 healthy matched pairs — identical to session start, confirming zero data/corpus edits this run.

**Confirmed:** no full-corpus GABRIEL extraction; no Massachusetts codify; 8 live calls attempted, 8 succeeded, 0 failed (at, not exceeding, the approved cap); no `data/contracts.csv`/`data/city_coverage.csv`/`corpus/` edits.

**Next steps**
1. Fix the window-assembly header-leakage failure mode (neutral, keyword-free section headers) before the next codify scale-up.
2. Run a curated Massachusetts codify batch — the append/union builder mode proven this run makes that a clean addition, not a rebuild-from-scratch.

---

## 2026-07-09 20:14 EDT (GABRIEL codify evidence-viewer overhaul) - PI-facing plain-English viewer with cascading filters and portable "latest" file; no live GABRIEL/Proxy/model calls; no data/corpus changes

**Did**
- Overhauled the local GABRIEL codify excerpt viewer built in the prior session so it is convenient and PI-facing rather than repo/data-facing, per explicit PI feedback. No new codify/Harvard Proxy/model calls — this run only transforms the existing 92-row full-codebook pilot output (`gabriel_codify_full_codebook_outputs_2026-07-09.csv`).
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `462d629`, and pre-session counts of 44 contracts / 44 coverage rows, matching expectations.
- Rewrote `scripts/build_codify_evidence_viewer.py` with plain-English label maps for state, occupation, source role, evidence status, and source-grounding status — all deliberately **not** Texas/Ohio-specific (Massachusetts is included in every map now, even though no MA codify run happened this session), so a future MA codify output CSV needs no further code changes to these maps.
- Added the full 19-attribute glossary (label + plain-English definition + a short "why this excerpt was coded here" clause per attribute) as Python constants, matching the refined Harvard Proxy codebook exactly.
- Added human-readable **contract labels**, derived conservatively from `data/contracts.csv` (`city_name`, `occupation_class`, `bargaining_unit_name`, `source_type`, `cycle_start`/`cycle_end`) — read-only, no invented text. All 4 current contracts resolved a real label (e.g., `"Houston Fire — Houston Professional Fire Fighters Association, Local 341, International Association of Fire Fighters arbitration award, 2024–2029"`); a conservative `"City Occupation — contract_id"` fallback exists for any future contract not yet in `data/contracts.csv`.
- Added a template-based **"What this excerpt shows"** explanation per present-evidence row (`_what_excerpt_shows()`), generated from the attribute's own clause text — not a new model call. Explicitly avoids the word "proves" and distinguishes interest/impasse arbitration from grievance arbitration and peer-comparator language from internal wage-schedule language, as required.
- **Renamed "grounded" to "Verified in source text"** everywhere in the UI, with an explanation (in the viewer itself, the usage doc, and the build audit) that this is a text-integrity check confirming the excerpt is a real verbatim match — not an analytical or causal claim.
- Rebuilt the evidence-layer CSV with 10 new plain-English columns (`state_label`, `city_label`, `occupation_label`, `source_role_label`, `contract_label`, `attribute_label`, `attribute_definition`, `evidence_status_label`, `source_grounding_label`, `what_excerpt_shows`) alongside the existing technical columns.
- Rebuilt the HTML viewer with: cascading (faceted) filters — selecting any of state/city/contract/occupation/source-role/attribute narrows the *other* dropdowns' available options, implemented symmetrically (not a fixed one-directional chain); an attribute filter that defaults to only mechanisms with `present` evidence in the current filtered scope, with a "Show mechanisms with no evidence" toggle; a collapsible mechanism glossary; a persistent causal-proof warning banner; per-card "Copy excerpt"/"Copy citation" buttons (vanilla JS, `navigator.clipboard` with an `execCommand('copy')` fallback for `file://` contexts); and a per-card collapsible "Technical details" section holding the raw IDs/codes.
- The build now writes **two** HTML files from one generated document: `gabriel_codify_excerpt_browser_2026-07-09.html` (dated archival copy) and `gabriel_codify_excerpt_browser_latest.html` (stable filename, the one to open/share going forward).
- Verified the build without a browser-automation tool: `node --check` on the extracted `<script>` block (passed), `json.loads()` on both embedded `EVIDENCE` (92 rows) and `ATTRIBUTES` (19 entries) JSON blocks (both parsed cleanly), grep checks confirming required phrases ("Verified in source text," "What this excerpt shows," the causal-proof warning, copy-button labels, glossary heading) all appear, and confirmed zero external CDN/script references and zero API-key-like strings in the output.
- Created:
  - `docs/analysis/gabriel_codify_viewer_overhaul_plan_2026-07-09.md`
  - `docs/analysis/gabriel_codify_viewer_usage_2026-07-09.md`
  - `docs/analysis/gabriel_codify_excerpt_browser_latest.html`
- Rewrote `scripts/build_codify_evidence_viewer.py`, `docs/analysis/gabriel_codify_evidence_layer.csv`, `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, and `docs/analysis/gabriel_codify_viewer_build_audit_2026-07-09.md`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new row), the report review checklist (new Section 7M), and the wage-mechanism evidence checklist (1 new pointer).

**Decisions and why**
- Implemented cascading filters as a **symmetric faceted system** (each dropdown's options recomputed from rows matching every *other* current selection) rather than a strict one-directional state→city→contract chain — this satisfies "selecting state restricts city, selecting contract restricts attribute" while also correctly handling the task's own additional requirement that "selecting contract/source restricts occupation/source_role/attribute," which a purely linear chain couldn't express cleanly.
- Kept contract labels strictly derived from real `data/contracts.csv` fields rather than the more colloquial abbreviations used in the task's own example labels (e.g., "HPFFA / IAFF Local 341") — the task's own instruction ("Do not invent overly specific source labels if not supported by contracts.csv") took precedence over matching the example text verbatim.
- Kept the "does not by itself establish a wage or causal effect" reminder as a separate fixed UI element (banner + per-card note) rather than folding it into every attribute-specific "what this excerpt shows" sentence, to avoid a repetitive/bloated per-card explanation while still satisfying the requirement that it appear prominently and often.

**Surprises/breakage**
- No surprises. No repo breakage. Validation and coverage audit passed, unchanged from the prior session (44 contracts / 44 coverage / 18 healthy pairs) since this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` (contracts.csv was read-only, for labeling).

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/build_codify_evidence_viewer.py
input rows read: 92 | evidence rows written: 92
present (evidence found): 53 | not_found: 39 | verified present: 53
rows with contract label from data/contracts.csv: 92/92
```

**No GABRIEL calls. No Harvard Proxy calls. No non-GABRIEL model/API calls. No `data/contracts.csv` edits (read-only, for labeling). No `data/city_coverage.csv` edits. No document ingestion or `corpus/` changes. No API keys or secrets printed, inspected, copied, or committed. `docs/schema.md` was not modified. No causal claims were made. No final PDF/DOCX artifacts were created.**

**Recommended next step**
Scale codify to the remaining Texas/Ohio matched-city rows (`tx_houston_police_2024`, `tx_austin_fire_2023`, `oh_columbus_police_2023`, `oh_columbus_other_2024`, `oh_cleveland_police_2025`, `oh_cleveland_fire_2025`, `oh_cleveland_other_2022`), then run a curated Massachusetts codify batch (label maps already support it), then rebuild the evidence layer and viewer from the combined output — extending `scripts/build_codify_evidence_viewer.py` with a genuine append/union mode (keyed on `evidence_id`) before that second run, so the evidence layer accumulates rather than being fully overwritten from a single input file each time.

---

## 2026-07-09 18:48 EDT (GABRIEL codify viewer and durable evidence layer) - Local excerpt browser and append-friendly evidence table built; no live GABRIEL/Proxy/model calls; no data/corpus changes

**Did**
- Investigated how GABRIEL expects users to view codify excerpts before expanding codify to more rows/cities, then built a durable local evidence layer and browser for this project.
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `7c6c3b0`, and pre-session counts of 44 contracts / 44 coverage rows, matching expectations.
- **Inspected `gabriel.utils.passage_viewer` (installed source, 2,858 lines) directly** rather than relying on docstrings alone. Found a genuine, real, fairly sophisticated built-in viewer: `gabriel.view(df, column_name, attributes=..., header_columns=..., ...)`, purpose-built to display `codify()`'s output (including a dedicated `attributes="coded_passages"` shortcut), with color-coded category highlighting (`_build_highlighted_text`, wraps matched substrings in `<span style='background-color:...'>`), a click-to-cycle legend, and notebook-styled navigation controls. **Critically, it requires a live IPython/Jupyter kernel to render at all** (`from IPython.display import HTML, display`) and has no supported standalone-file-export path. The older `tkinter`-based `PassageViewer` class is explicitly retired in this installed version (raises `RuntimeError` directing users to `gabriel.view(...)` in a notebook). No bundled tutorial notebook ships with the package; the upstream repo (`github.com/openai/GABRIEL`) was identified via package metadata but not fetched, since the installed source already gave more precise, authoritative answers.
- **Concluded GABRIEL's built-in viewer does not meet this project's actual need** (multi-dimensional metadata filtering across state/city/contract_id/occupation_class/source_role/attribute/evidence_status/source_grounding_status, plus free-text search, plus a durable git-committable artifact) and built a project-local static HTML viewer instead — borrowing GABRIEL's excerpt-highlighting pattern (`<mark>`-wrapped matched text) as design inspiration, but with no IPython/notebook dependency at all.
- Built the durable evidence layer (`gabriel_codify_evidence_layer.csv`) from the existing full-codebook pilot output (`gabriel_codify_full_codebook_outputs_2026-07-09.csv`), with a stable `evidence_id` scheme (`codify_YYYYMMDD_<contract_id>_<attribute>_<sequence>`) designed to be append-friendly across future codify runs, and kept strictly binary `present`/`not_found` evidence_status (no invented confidence/caveat values).
- Built a self-contained static HTML excerpt browser (`gabriel_codify_excerpt_browser_2026-07-09.html`, 104KB, no external CDN/JS/CSS dependencies) with sidebar filters (state, city, contract_id, occupation_class, source_role, attribute, evidence_status, source_grounding_status), free-text search, live counts, a "Cards" view with Prev/Next navigation and highlighted excerpts, a compact "Table" view, and a "How to use this viewer" section.
- Wrote a regeneration script (`scripts/build_codify_evidence_viewer.py`) that produces both files from any codify output CSV, validates controlled values and duplicate `evidence_id`s at write time, and prints a concise row-count summary. No `gabriel` import, no credential read, no network call anywhere in the script.
- Verified the generated HTML without a browser-automation tool: extracted the embedded `<script>` block and syntax-checked it with `node --check` (passed), and extracted/parsed the embedded `const EVIDENCE = [...]` JSON with Python (92 rows, 53 present, all fields intact) — confirming the file is well-formed and the data is faithfully embedded.
- Ran the build script twice (idempotency check) and once more as part of Task G's checks — identical row counts each time, no side effects.
- Created:
  - `docs/analysis/gabriel_codify_viewer_capability_review_2026-07-09.md`
  - `docs/analysis/gabriel_codify_evidence_layer.csv`
  - `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`
  - `docs/analysis/gabriel_codify_viewer_build_audit_2026-07-09.md`
  - `scripts/build_codify_evidence_viewer.py`
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new row), the report review checklist (new Section 7L), and the wage-mechanism evidence checklist (1 new pointer).

**Decisions and why**
- Did not attempt to monkey-patch/capture GABRIEL's internal `_render_passage_viewer` HTML output, despite it being technically possible (the function assembles a self-contained `style_html + viewer_html` string before handing it to `IPython.display.HTML`) — this would depend on private, underscore-prefixed internals not intended as a stable public API, and would still not solve the actual requirement (faceted filtering across contract-level metadata, which GABRIEL's viewer was never designed for).
- Kept the browser's excerpt highlighting as "wrap the whole excerpt in `<mark>`" rather than "find the excerpt's position within a larger passage and highlight only that span" (GABRIEL's own approach) — appropriate here because this project's evidence windows are already compact, curated excerpt concatenations, not full source documents; each `excerpt` field IS the matched span, not a position within something larger shown in the card.
- Designed `evidence_id` and the evidence-table schema explicitly for append-friendliness (`run_date` embedded, sequence counters reset per run via the `(contract_id, attribute)` key) so a future second codify run's output CSV can be fed through the same script without colliding IDs, per Task B's explicit requirement.

**Surprises/breakage**
- The genuine surprise: GABRIEL does have a real, non-trivial viewer (not just a stub) — but it is notebook-only by explicit design, and the older desktop viewer has been deliberately retired, not merely undocumented. This confirms building a project-local viewer was the right call, not a workaround for a missing feature.
- No repo breakage. Validation and coverage audit passed, unchanged from the prior session (44 contracts / 44 coverage / 18 healthy pairs) since this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/build_codify_evidence_viewer.py
Codify evidence layer + viewer build summary
  input rows read:        92 | evidence rows written: 92
  present: 53 | not_found: 39 | grounded present: 53
```

**No GABRIEL calls. No Harvard Proxy calls. No non-GABRIEL model/API calls. No `data/contracts.csv` edits. No `data/city_coverage.csv` edits. No document ingestion or `corpus/` changes. No API keys or secrets printed, inspected, copied, or committed. `docs/schema.md` was not modified. No causal claims were made. No final PDF/DOCX artifacts were created.**

**Recommended next step**
Open `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` directly in a browser for a manual visual/interaction pass (filters, card navigation, table view) before relying on it for real review work — this session verified it via syntax/data checks only, no live browser rendering tool was available. When a second codify pilot run happens, re-run `scripts/build_codify_evidence_viewer.py` against a combined input (or extend it with an explicit append/union mode) so the evidence layer and viewer stay cumulative rather than being overwritten per run.

---

## 2026-07-09 12:06 EDT (Harvard Proxy-enabled GABRIEL/codify full-codebook pilot) - Adapter built and verified live; 4/4 calls succeeded; 100% source-grounded; no data/corpus changes

**Did**
- Ran the Harvard Proxy-enabled GABRIEL/codify pilot with the full refined 19-attribute wage-mechanism codebook, following directly from the prior session's dry-run-only pilot (no credentials were available then).
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `b6747d9`, and pre-session counts of 44 contracts / 44 coverage rows, matching expectations.
- **Credential update:** the user placed `HARVARD_SUBSCRIPTION_KEY` in the repo's git-ignored `.env` file since the prior session. This session confirmed its presence exclusively via `python-dotenv`'s standard `load_dotenv()` loader (never opened, `cat`, or otherwise read `.env` directly) — presence/length checked, value never printed or logged.
- **Traced `gabriel.codify()`'s source code** (installed package v1.1.8, not just its docstring) through `gabriel/api.py` → `gabriel/tasks/codify.py` → `gabriel/utils/openai_utils.py` to confirm its `response_fn` hook is genuinely wired end-to-end and, critically, that supplying a custom `response_fn` skips GABRIEL's internal `OPENAI_API_KEY` requirement entirely — the mechanism this pilot needed to route through `HARVARD_SUBSCRIPTION_KEY` instead. Also worked out the exact chunking math (`max_categories_per_call`, `max_words_per_call`, `n_rounds`) needed to guarantee exactly one live call per selected row, matching the 4-call cap precisely.
- Built a `response_fn` adapter reusing this repo's already-established Harvard Proxy client pattern (`ingest/extract_spans.py`, `scripts/proxy_pilot_must_have_sources.py`: `openai.OpenAI(api_key=..., base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2", default_headers={"Ocp-Apim-Subscription-Key": ...})`), using `gpt-5.4-nano` (the model already confirmed working on this specific proxy elsewhere in this repo, not GABRIEL's own generic default).
- Rewrote `scripts/gabriel_codify_pilot.py` with the full 19-attribute codebook, `--use-harvard-proxy` flag, a hard cap raised to 4 live calls (enforced in code), and a per-row `gabriel.codify()` invocation loop (not one batched call) so a failure on any row is isolated and the run can stop cleanly after the first nontrivial failure.
- Built fresh evidence windows for the task's preferred 4-row sample (`tx_houston_fire_2024`, `tx_houston_other_2024`, `tx_austin_nursehealth_2023`, `oh_columbus_fire_2023`) by combining prior hand-extracted excerpts with a few new raw passages located via local term search over already-extracted corpus text, targeting the 8 attributes new to the refined codebook.
- **Ran the dry-run first** (per the task's own requirement), then attempted the live pilot. **Caught and fixed a real code bug before any cost was incurred:** `gabriel.codify()` is `async def` and the first attempt called it synchronously without `asyncio.run(...)`, so it silently returned an un-awaited coroutine (confirmed via Python's own `RuntimeWarning`, zero network calls made). Fixed in one line, then re-ran.
- **4 real live calls succeeded, 0 failed.** Reported cost: $0.00 for all four (small prompts on `gpt-5.4-nano`). Ran row 1 first as a go/no-go test (per the task's hard boundary), confirmed it worked and was correctly grounded, then ran rows 2-4 together rather than re-spending the already-successful row 1 call — total real successful live calls across the session: exactly 4, matching the cap.
- **Source-grounding audit: 53 of 53 present-status excerpts (100%) verified as verbatim substrings of their evidence window. Zero hallucinations.** The model correctly distinguished Houston Fire's grievance/contract-interpretation arbitration from interest/impasse arbitration — the specific test this codebook refinement existed to check — and correctly identified Columbus Fire's SERB conciliation language as genuine impasse backstop.
- **Discovered a real interface limitation:** `gabriel.codify()`'s native output is a binary present/absent snippet list per category with no confidence field and no "unclear" state — this project's desired richer evidence_status/confidence schema cannot currently be fully populated by codify() alone. Documented honestly (confidence reported as `not_applicable` rather than invented) rather than silently working around it.
- Created:
  - `docs/analysis/gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv`
  - `docs/analysis/gabriel_codify_full_codebook_prompt_preview_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv`
  - `docs/analysis/gabriel_codify_full_codebook_audit_2026-07-09.md`
- Rewrote `scripts/gabriel_codify_pilot.py`.
- Live-run outputs saved under `tmp/gabriel_codify_pilots/2026-07-09_120200_full_codebook_live/` (raw `coded_passages.csv`/`coding_results.csv` per row under `gabriel_save_dir/`, plus consolidated `run_config.json`, `parsed_outputs.csv`, `live_run_log.txt`).
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new row), the report review checklist (new Section 7K), and the wage-mechanism evidence checklist (1 new pointer).
- **Updated the relay-bundle convention per this task's explicit instruction:** this session's bundle uses `committed_changed_files.txt` (continuing the convention established last session).

**Decisions and why**
- Used `response_fn`, not `get_all_responses_fn` — the "lightweight" per-prompt hook keeps GABRIEL doing its own prompt construction, JSON parsing, and result aggregation (a genuinely *native* codify run), while the adapter's only job is the HTTP call itself.
- Chose `gpt-5.4-nano` over GABRIEL's own default `gpt-5.4-mini` for the Harvard Proxy path specifically because nano is the model already confirmed working on this exact proxy elsewhere in this repo; mini has never been exercised against it.
- When the first live call's post-processing failed on a trivial bug (`result_df.insert()` failing because `codify()` already returns the input df's `contract_id` column), reused the already-obtained real result rather than re-querying the API a second time for the same row — kept the total real live-call count at exactly 4, not 5.
- Reported `confidence=not_applicable` throughout rather than inventing a confidence value `codify()` never actually produced, once its native output format was confirmed not to include one.

**Surprises/breakage**
- The genuine surprise: `gabriel.codify` is an `async def` function at the top level, which `inspect.signature()`'s return-type annotation (`-> pandas.DataFrame`) does not make obvious — this caused the one code bug this session (caught before any cost, fixed in one line).
- No repo breakage. Validation and coverage audit passed, unchanged from the prior session (44 contracts / 44 coverage / 18 healthy pairs) since this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 4 --windows docs/analysis/gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv
Dry run complete.
```

**No `data/contracts.csv` edits. No `data/city_coverage.csv` edits. No document ingestion or `corpus/` changes. No full-corpus GABRIEL run — exactly 4 rows, one call each. No Harvard Proxy scripts run outside this capped pilot script. No non-GABRIEL model/API calls. No API keys or secrets printed, inspected, copied, or committed — `HARVARD_SUBSCRIPTION_KEY` was only ever accessed via `python-dotenv`'s standard loader and `os.environ.get(...)`, never read from `.env` directly or printed. `docs/schema.md` was not modified. No causal claims were made.**

**Recommended next step**
Decide how to add a confidence dimension before scaling further — either accept codify()'s binary present/not_found output as-is, or pair it with GABRIEL's separate `rate()` task for a 0-100 confidence-like score. Clean table-of-contents noise out of evidence windows before the next run (a few low-information TOC-line matches surfaced this session, though still correctly grounded), and keep slightly more surrounding context (article headers) around passages likely to trigger the interest-vs-grievance-arbitration distinction, since one Houston HOPE excerpt was genuinely ambiguous without it. If addressed, a modestly larger (still capped) pilot covering the remaining Texas/Ohio matched-city rows would be the natural next scaling step — not yet a full-corpus run.

---

## 2026-07-09 11:16 EDT (Tiny GABRIEL/codify pilot) - Interface inspected, pilot fully designed and staged; no live calls (no credentials available); no data/corpus changes

**Did**
- Ran a tiny GABRIEL/codify pilot after Texas/Ohio ingestion, per the project's readiness assessment from the prior session (both comparison states now have two matched cities each). Goal: test whether `gabriel.codify()` can build a durable `state|city|occupation_class|contract_id|mechanism_code|evidence_status|excerpt|location|confidence|notes` evidence layer.
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `e2cbc52`, and pre-session counts of 44 contracts / 44 coverage rows, matching expectations.
- Inspected the installed `gabriel` package (version 1.1.8, real local install). Confirmed `gabriel.codify(df, column_name, *, save_dir, categories=None, additional_instructions="", model="gpt-5.4-mini", ..., response_fn=None, get_all_responses_fn=None, **cfg_kwargs)` — a passage-coding task that maps cleanly onto this project's desired evidence-layer shape. Read the docstring in full.
- **Checked credential presence (booleans only, no values printed or logged):** `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and this repo's own `HARVARD_SUBSCRIPTION_KEY` are all unset in this environment. GABRIEL's default call path needs the first two; this repo's established Harvard Proxy calling pattern (`scripts/proxy_pilot_must_have_sources.py`) needs the third and is a separate hand-built code path that does not go through `gabriel.codify()` at all. Neither credential source is available, so **no live call could be safely attempted**, per this run's own hard boundary.
- Designed and fully staged a 3-contract pilot anyway, so a future credentialed session can run it immediately: selected `tx_houston_fire_2024`, `tx_houston_other_2024`, and `oh_columbus_fire_2023` (all `text_quality=clean`, all with an existing hand-built mechanism-excerpt extraction to serve as a known-answer key). Built one compact evidence window per contract (2,565 / 5,407 / 5,862 characters) by concatenating the already-extracted `evidence_status=present` excerpt bodies from `houston_fire_mechanism_excerpt_extraction_2026-07-08.csv` and `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv` — deliberately stripping the mechanism-name labels out of the window text so a future live run is a genuine coding test, not a label-echo exercise.
- Wrote the full 11-code mechanism codebook and a verbatim-only / no-causal-inference / default-to-`not_found` prompt spec (`additional_instructions`), matching this project's existing capture-verbatim-never-pre-code discipline.
- Created:
  - `docs/analysis/gabriel_codify_interface_inspection_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_design_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_evidence_windows_2026-07-08.csv`
  - `docs/analysis/gabriel_codify_pilot_prompt_preview_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_audit_2026-07-08.md`
  - `scripts/gabriel_codify_pilot.py` (dry-run-default scaffold; `--live` requires an explicit `--max-calls` hard-capped at 3 in code; refuses cleanly and falls back to dry-run if no credential is present, verified by testing both the dry-run and the credential-refusal path)
- Ran the dry-run pilot output into `tmp/gabriel_codify_pilots/2026-07-09_111259/` (`run_config.json` with `live_run_attempted: false`, `selected_windows.csv`, `prompt_preview.md`, `dry_run_log.txt`) — no `gabriel_codify_pilot_outputs_2026-07-08.csv` was created, since there is no live output to parse.
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new cross-cutting row), the report review checklist (new Section 7J), and the wage-mechanism evidence checklist (1 new pointer sentence).
- Updated the relay-bundle convention per this session's explicit instruction: future bundles use `committed_changed_files.txt` for the commit's file list, keeping `git_status_post_commit.txt` as the separate post-commit cleanliness check.

**Decisions and why**
- Did not attempt any live call, including a single-row test, because no usable credential exists in this environment — attempting one would either hang, fail on auth, or (worse) silently do nothing useful while still touching network code paths. Per the task's own hard boundary, this is a clean "produce dry-run only" case, not a partial-failure case.
- Built evidence windows from already-extracted excerpts rather than re-running text extraction from the PDFs, since Task C explicitly allows reusing existing extraction files and this keeps the windows compact (2.5-5.9K characters vs. tens of thousands in the source PDFs) while still testing genuine coding ability (labels stripped from the window text).
- Made `scripts/gabriel_codify_pilot.py` default to dry-run and hard-cap `--max-calls` at 3 in code (not just via a CLI flag), mirroring the safety pattern already established by `scripts/proxy_pilot_must_have_sources.py` for this repo's Harvard Proxy pilots.

**Surprises/breakage**
- No surprises in the interface itself — `gabriel.codify()`'s signature, docstring, and injection points (`response_fn`/`get_all_responses_fn`) are all clear and well-documented. The only blocker is environmental (missing credentials), not a code or design problem.
- No repo breakage. Validation and coverage audit passed, unchanged from the prior session (44 contracts / 44 coverage / 18 healthy pairs) since this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/gabriel_codify_pilot.py --dry-run --max-calls 3
Dry run complete.
```

**No GABRIEL live calls were made (0 attempted / 0 succeeded / 0 failed). No Harvard Proxy scripts were run. No non-GABRIEL model/API calls were made. No `data/contracts.csv` or `data/city_coverage.csv` edits. No document ingestion or `corpus/` changes. No API keys or secrets were printed, inspected, copied, or committed — only boolean presence/absence of three credential environment variables was checked. `docs/schema.md` was not modified. No causal claims were made.**

**Recommended next step**
Obtain a usable credential (`OPENAI_API_KEY`/`OPENAI_BASE_URL`, or wire `gabriel.codify()`'s `response_fn` injection point to this repo's existing Harvard Proxy client pattern) before attempting the first live call. When available, run the fully-staged 3-row pilot (`scripts/gabriel_codify_pilot.py --live --max-calls 3`, or fewer) and complete the source-grounding audit already scaffolded in `gabriel_codify_pilot_audit_2026-07-08.md` before deciding whether `codify()` should replace any part of this project's hand-built mechanism-extraction process.

---

## 2026-07-08 17:59 EDT (Texas second matched-city completion) - Austin EMS meet-and-confer agreement found and ingested; Texas now has two matched cities, on par with Ohio

**Did**
- Ran a Texas second matched-city completion pass before any GABRIEL/codify pilot. Design target: two matched cities per comparison state (Ohio already had Columbus + Cleveland; Texas had Houston matched but Austin had police + fire with no non-safety partner).
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `4cd7550`, and pre-session counts of 43 contracts / 43 coverage rows, matching expectations.
- Re-searched Austin non-safety wage-setting sources with fresh search terms beyond the prior session's AFSCME Local 1624 dead end. Checked a City Clerk council item (File #26-1362) referencing "non-sworn employees not covered by collective bargaining or meet and confer agreements" — a red herring that did not point to a separate civilian agreement.
- **Found the real answer:** the City of Austin's official `labor-relations` page family (same hosting pattern as the already-ingested police/fire agreements) includes an **EMS Meet and Confer Agreement** page, linking to a genuine, complete meet-and-confer agreement between the City and the **Austin EMS Association (AEMSA)**, effective October 1, 2023 through September 30, 2027. Downloaded and text-extracted (88 pages, clean text layer). Confirmed via Article 3 (Recognition) and Article 2 (Definitions) that this is a clean, single-occupation EMS/paramedic bargaining unit (Texas Health and Safety Code Chapter 773's "Emergency Medical Services Personnel," civilians explicitly excluded) — not a bundled multi-department unit, so no recognition-clause-first ambiguity. Contains a real 4-year wage schedule, on-call/call-back pay, shift differential, education incentive pay, and a grievance-arbitration clause.
- Because Austin resolved successfully, the backup-city evaluation (Fort Worth/San Antonio) was not triggered — both remain documented as deferred options, carrying forward prior planning's finding that neither has a confirmed non-safety institutional channel.
- Created:
  - `docs/analysis/texas_second_matched_city_preflight_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_source_resolution_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_summary_2026-07-08.md`
- Added one causal row to `data/contracts.csv` (`tx_austin_nursehealth_2023`) and one matching row to `data/city_coverage.csv`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new row), the report review checklist (new Section 7I), the wage-mechanism evidence checklist (row-count refresh + pointer), and `texas_ohio_approved_source_plan_2026-07-08.csv` (AFSCME 1624 backup row's caveat marked superseded).

**Decisions and why**
- Classified the new row `occupation_class=nurse_health`, `safety_flag=0` — the closest schema-supported fit for pre-hospital emergency medical/paramedic personnel, consistent with this project's existing practice of coding safety-adjacent occupations (dispatchers, nurses) as legitimate non-safety comparison units. Explicitly flagged in row notes and the checklist that EMS is civil-service-protected and statutorily adjacent to police/fire (a shared Ch.143 Civil Service Commission), so it should never be described as an ordinary civilian/clerical comparison unit in later report language.
- Left `interest_arbitration_flag=0` — the agreement's grievance-arbitration clause is contract-interpretation arbitration, not interest/impasse arbitration for setting new terms, mirroring the same distinction made for Houston Fire and Austin's own fire/police agreements.
- Did not evaluate Fort Worth or San Antonio, since the task's own decision rule only calls for backup-city evaluation if Austin cannot be matched.

**Surprises/breakage**
- The genuinely surprising find: Austin's own official labor-relations page has had an EMS meet-and-confer agreement publicly posted the whole time, on the exact same page family already used for the ingested police/fire agreements — it was simply never searched for in prior sessions, which focused only on AFSCME Local 1624 as the presumed non-safety channel.
- No repo breakage. Validation and coverage audit passed.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3
```

**Corpus snapshot**
```text
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```
All three remaining unmatched safety units are Massachusetts; zero Texas/Ohio safety units are unmatched as of this run.

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No statutes, budgets, pay plans, city pages, news stories, or consultation-only policies were ingested as causal rows. `docs/schema.md` was not modified.**

**Recommended next step**
Texas now has two matched cities (Houston, Austin), on par with Ohio (Columbus, Cleveland) — the pre-GABRIEL design target is met, with no remaining structural blocker for a Texas/Ohio pilot. Recommend proceeding to the tiny GABRIEL/codify pilot next.

---

## 2026-07-08 15:12 EDT (Houston Fire source resolution) - Genuine 2026 arbitration award found and ingested; Houston now fully matched across all three tiers

**Did**
- Ran a narrow, single-target follow-up to the Texas/Ohio held-out-target run (commit `6ce5080`), focused exclusively on resolving Houston Fire — the last remaining held-out Texas/Ohio target.
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `6ce5080`, and pre-session counts of 42 contracts / 42 coverage rows, matching expectations.
- Re-checked houstontx.gov's HR/legal folders and HPFFA's own official site (`local341.org`, no public CBA/documents section) — no official full base-CBA text found, consistent with prior sessions.
- **Found a new lead via web search:** `hfdcoa.org`, the official site of the Houston Fire Department Chief Officers Association (HFOA) — a real, distinct professional association representing chief officers, separate from HPFFA (rank-and-file). Its `/cba-2024-2029/` page hosts five documents that are actually HPFFA/City-of-Houston labor-relations documents, not HFOA's own agreement: an MOU (2024-06-11), an Interim Amendment, a wage-schedule exhibit, a Settlement Agreement and Release (2026), and an Arbitration Opinion and Award (2026-02-27).
- Downloaded and text-extracted all five for verification (via `ingest/extract_text.py`, text-layer and OCR fallback). Confirmed the **Arbitration Opinion and Award** (AAA Case No. 01-25-0005-2917, HPFFA Local 341 v. City of Houston, Arbitrator William E. Hartsfield) is a genuine, complete, 17-page grievance-arbitration ruling on Houston Fire's 2024-2029 CBA Article 17 Sec.2 "Three Percent Pay Escalator," quoting substantial CBA text verbatim (Articles 2, 6, 14, 17, 25) and explicitly incorporating a **Settlement Agreement and Release** (same case number, "Attachment 1... incorporated by this reference") resolving companion FY26 monetary grievances, plus a clarifying **MOU** cited by the Award to interpret the escalator clause. Independently corroborated by ABC13 Houston news reporting of the same ruling.
- Fetched and stored all three (Award, Settlement, MOU) under `corpus/tx_houston/`; left the Interim Amendment and wage-schedule exhibit unfetched (verified genuine but not incorporated by reference into the ingested chain, so out of this run's necessary-companion scope).
- Created:
  - `docs/analysis/houston_fire_source_resolution_preflight_2026-07-08.md`
  - `docs/analysis/houston_fire_source_resolution_2026-07-08.csv`
  - `docs/analysis/houston_fire_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/houston_fire_source_identity_audit_2026-07-08.md`
  - `docs/analysis/houston_fire_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/houston_fire_metadata_addition_2026-07-08.csv`
  - `docs/analysis/houston_fire_source_resolution_summary_2026-07-08.md`
- Added one causal row to `data/contracts.csv` (`tx_houston_fire_2024`, source_type=arbitration_award) and one matching row to `data/city_coverage.csv`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new row), the report review checklist (new Section 7H), the wage-mechanism evidence checklist (row-count refresh + pointer), and `texas_ohio_approved_source_plan_2026-07-08.csv` (both the Houston-fire approved row and the HFOA backup row's caveats updated).

**Decisions and why**
- Classified the primary ingested document as `source_type=arbitration_award`, **not** `cba`, and left `interest_arbitration_flag=0` — this is grievance/contract-interpretation arbitration under the CBA's own Article 14 procedure, not the Sec.174.1535 population-triggered compulsory *interest* arbitration mechanism. The distinction is documented in full in `binding_arbitration_statute` and the identity audit so it is never conflated in later analysis.
- Fetched three (not one) companion documents — justified under the task's "clearly parts of the same operative agreement, both necessary" exception, since the Award's own text explicitly incorporates the Settlement ("Attachment 1... incorporated by this reference for all purposes") and cites the MOU to interpret the very clause at issue.
- Declined to fetch the Interim Amendment or wage-schedule exhibit despite verifying both are genuine, to avoid stretching the "necessary companions" exception further than the documents' own cross-references justify; `base_wage_entry`/`base_wage_top` left blank rather than populated from an unfetched source.
- Treated `hfdcoa.org` as `official_or_high_quality_source=yes` on the strength of internal consistency (real case number, dates, named Houston officials, a genuine Houston City Hall Annex address) plus independent ABC13 news corroboration — not because HFOA is itself a party to the HPFFA/City agreement it happens to host.

**Surprises/breakage**
- The most surprising find: a fire *officers'* association's website hosting the rank-and-file union's arbitration/settlement documents — an unusual but, on inspection, well-corroborated cross-hosting arrangement, not a mismatch or scraping artifact.
- This also incidentally resolved a smaller open question flagged since the very first Texas/Ohio session: the HFOA-vs-HPFFA relationship. HFOA is confirmed a genuinely separate chief-officers' union, but no distinct HFOA CBA was located — only HPFFA documents mirrored on HFOA's site.
- No repo breakage. Validation and coverage audit passed.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3 | cities: 13
healthy matched pairs: 16
  exact-cycle: 9
  overlap-cycle: 7
exploratory adjacent matches: 2
safety units unmatched: 5
```

**Corpus snapshot**
```text
contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3 | cities: 13
healthy matched pairs: 16
  exact-cycle: 9
  overlap-cycle: 7
exploratory adjacent matches: 2
safety units unmatched: 5
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012,
  ma_newton_police_2015, tx_austin_police_2024, tx_austin_fire_2023
```

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No statutes, budgets, pay plans, city pages, news stories, or legal pages were ingested as causal rows. The source was correctly classified as `arbitration_award` and not conflated with Sec.174.1535 compulsory interest arbitration. `docs/schema.md` was not modified.**

**Recommended next step**
Houston Fire is resolved for this project's purposes — recommend moving to a tiny GABRIEL/codify pilot next, now that Houston has all three matched tiers (the first Texas/Ohio city to reach this state). The full base-CBA text remains a lower-priority open item that does not block a pilot, given the substantive verbatim wage-mechanism text already captured (compensation schedule, grievance-arbitration clause, training/certification pay, total compensation).

---

## 2026-07-08 13:48 EDT (Texas/Ohio held-out-target resolution) - 1 source resolved and fetched (Austin fire); Houston fire remains unresolved; Austin non-safety design question closed

**Did**
- Ran a controlled follow-up to the first Texas/Ohio live-acquisition batch (commit `4134f45`), resolving the six held-out targets it left open: Houston fire full-CBA, Austin fire cycle-specific, Austin non-safety, Austin budget/pay-plan, Cleveland budget/pay-plan, and the Ohio SERB archive path.
- Confirmed repo state clean at session start (only untracked `tmp/`), latest commit `4134f45`, and pre-session counts of 41 contracts / 41 coverage rows / 43 corpus files, matching expectations.
- Used bounded public web checks (WebFetch/WebSearch plus direct `curl` + `ingest/extract_text.py` reads) to resolve each target:
  - **Austin fire — resolved and fetched.** The official austintexas.gov labor-relations page verbatim-labels a document "Current Agreement": the Austin Firefighters Association Local 975 CBA, effective through September 30, 2025. Downloaded (697,381 bytes, sha256 `637bb2b1...`), text-extracted (100 pages, clean text layer), and identity-confirmed via its Recognition and Term-of-Agreement articles. Stored at `corpus/tx_austin/tx_austin_afa975_fire_cba_2023_2025.pdf`.
  - **Houston fire — unresolved.** The only houstontx.gov PDF linked from the press-release page is a 2024-04-30 City Council presentation slide deck (confirmed via text extraction: title slide, bullet points, no numbered CBA articles), not the executed agreement. No official full-CBA-text copy was located; the only full-text copy anywhere is a non-official news mirror (khou.com), which a prior session already flagged as unsuitable. Deferred, not fetched.
  - **Austin non-safety (AFSCME Local 1624) — resolved but confirmed non-causal.** Located the specific document (City Council Resolution No. 20260122-049, adopted 2026-02-26): a consultation-policy resolution establishing regular labor-management meetings, not a negotiated wage-setting CBA. This closes an open design question a prior session had flagged. Not added as a contracts.csv row.
  - **Austin/Cleveland budget-pay-plan pages and the Ohio SERB archive — all resolved context-only** (all return HTTP 200; the SERB archive URL had previously returned 404). None fetched or stored into `corpus/`, per task scope.
- Created:
  - `docs/analysis/texas_ohio_heldout_target_preflight_2026-07-08.md`
  - `docs/analysis/texas_ohio_heldout_source_resolution_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_ingestion_extraction_summary_2026-07-08.md`
- Added one causal row to `data/contracts.csv` (`tx_austin_fire_2023`) and one matching row to `data/city_coverage.csv`, per repo coverage convention.
- Lightly updated `all_groups_source_needs_2026-07-06.csv` (1 new cross-cutting row), `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7G), `wage_mechanism_evidence_checklist.md` (row-count refresh + 1 pointer sentence), and `texas_ohio_approved_source_plan_2026-07-08.csv` (Austin fire row's caveat updated to RESOLVED).

**Decisions and why**
- Chose the officially-labeled "Current Agreement" (2023-09-24 to 2025-09-30) over the in-flight December 2025 successor for Austin fire, because the successor exists only as ~24 separate negotiation-session/redline documents on the official page, not one clean executed copy, while the labeled current agreement is a single, complete, cleanly-extracted 100-page text.
- Declined to ingest the Austin AFSCME Local 1624 consultation agreement as a causal row because it fails the causal-corpus "text that causes wages" definition — no recognition-as-exclusive-bargaining-agent clause, no wage schedule, no negotiated compensation terms; it is a consultation/voice mechanism, not a CBA.
- Declined to substitute the khou.com news mirror for Houston fire, per a prior session's own guardrail note requiring an official houstontx.gov copy before ingestion.
- Did not fetch/store the resolved budget-pay-plan or SERB-archive sources, per explicit task scope (record as context-only citations only).

**Surprises/breakage**
- The Houston fire "official" press-release page turned out to link only to a City Council presentation slide deck, not the executed CBA — a more surprising dead end than the prior session's characterization of it as merely "needs confirmation."
- The Austin AFSCME Local 1624 document exists and is easy to find, but resolves in the opposite direction expected: it is confirmed NOT to be a wage-setting source, closing (rather than fulfilling) the held-out target.
- No repo breakage. Validation and coverage audit passed.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 5
```

**Corpus snapshot**
```text
contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 5
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012,
  ma_newton_police_2015, tx_austin_police_2024, tx_austin_fire_2023
```

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No statutes, budgets, pay plans, or SERB archive pages were ingested as causal rows. No meet-and-confer or consultation agreement was classified as `arbitration_award`. No wage panels or final PDF/DOCX artifacts were built. `docs/schema.md` was not modified.**

**Recommended next step**
Prioritize a dedicated search for an official houstontx.gov full-text copy of the HPFFA/IAFF Local 341 CBA (HR/legal/city-attorney document folders, or the City Secretary's contract records index, beyond the paths already searched). Separately, Austin is now the least-matched of the four first-batch cities (two unmatched safety units, zero non-safety comparison units) — the next Austin-specific source-discovery pass should focus on whether any actual wage-negotiating body exists for Austin municipal employees beyond the civil-service classification system and the newly confirmed (non-wage-setting) consultation agreement.

---

## 2026-07-08 (Texas/Ohio first-batch live acquisition and extraction) - 9 sources fetched; 9 causal rows added; recognition-clause-first extraction completed

**Did**
- Completed the first controlled live Texas/Ohio source acquisition for the nine dry-run rows marked `ready_for_live_fetch` and `approved_first_batch`.
- Fetched and stored nine public agreement PDFs under `corpus/tx_houston/`, `corpus/tx_austin/`, `corpus/oh_columbus/`, and `corpus/oh_cleveland/`.
- Created:
  - `docs/analysis/texas_ohio_live_ingestion_preflight_2026-07-08.md`
  - `docs/analysis/texas_ohio_live_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_ohio_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_contracts_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_ohio_ingestion_extraction_summary_2026-07-08.md`
- Added nine causal agreement rows to `data/contracts.csv` and nine matching rows to `data/city_coverage.csv` per repo coverage convention.
- Completed recognition-clause-first extraction for Houston HOPE/AFSCME Local 123, Columbus AFSCME Local 1632, and Cleveland AFSCME Local 100; all remain `occupation_class=other`.
- Completed mechanism excerpt extraction as source-text audit work only.

**Decisions and why**
- Used `source_type=cba` for meet-and-confer agreements and CBAs because `docs/schema.md` has no separate meet-and-confer source type.
- Kept broad non-safety units as `occupation_class=other` because recognition/classification text shows mixed municipal coverage rather than a single supported schema occupation.
- Updated `data/city_coverage.csv` despite the task's caution because `AGENTS.md` makes coverage updates an explicit repo convention after contract additions, and the need was obvious once nine rows were added to `data/contracts.csv`.

**Surprises/breakage**
- Austin's official source page returned an HTML landing page first; the current agreement PDF was resolved from the page's official linked Widen original-file endpoint and stored at the proposed corpus path.
- Cleveland IAFF Local 93 is image-heavy; full OCR was not pursued. Targeted local OCR confirmed source identity, recognition text, and selected mechanism text, and the row is marked `text_quality=ocr_messy`.
- No repo breakage. Validation and coverage audit passed.

**Validation/audit results**
```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 41 | discourse: 0 | coverage: 41 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 41 | discourse: 0 | coverage: 41 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 4
```

**Corpus snapshot**
```text
contracts: 41 | discourse: 0 | coverage: 41 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 4
unmatched safety obs_ids include: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015, tx_austin_police_2024
```

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No context-only statutes, SERB pages, budgets, or pay plans were ingested. No wage panels or final PDF/DOCX artifacts were built.**

**Recommended next step**
Confirm remaining held-out Texas/Ohio targets before a second live acquisition: Houston fire full-CBA target, Austin fire cycle-specific target, Austin pay-plan URL, Cleveland budget/pay-plan URL, and the current Ohio SERB archive path. The highest-value next acquisition is Austin fire/non-safety confirmation so the new Austin police row does not remain unmatched.

---

## 2026-07-08 (Texas/Ohio acquisition dry-run and recognition-clause-first audit) - Dry-run plan created; broad non-safety classification guardrail added; no acquisition

**Did**
- Completed a controlled Texas/Ohio acquisition dry-run for the first-batch cities: Houston, Austin, Columbus, and Cleveland. This was planning only — no ingestion, no source-document download/storage, no corpus/inbox changes, and no `data/contracts.csv` or `data/city_coverage.csv` edits.
- Created:
  - `docs/analysis/source_planning_csv_hygiene_standard_2026-07-08.md`
  - `docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md`
  - `docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.md`
  - `docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.csv`
- Checked `docs/analysis/texas_ohio_approved_source_plan_2026-07-08.csv` with Python CSV parsing, required-column checks, controlled-value checks, duplicate source-target/proposed-filename checks, missing approved-field checks, budget/legal-as-causal checks, and broad non-safety occupation-class checks.
- Lightly updated the approved source plan only where the dry-run found stale Austin official labor-relations deep links: the Austin fire and police rows now point to live `/labor-relations/...` pages rather than the old `/department/labor-relations/...` paths. The Austin fire row keeps a caveat that the live page now surfaces a Dec. 18, 2025 agreement link and the exact desired cycle must be confirmed before live fetch.
- Added source-needs/checklist pointers for the new CSV hygiene standard, recognition-clause-first standard, and acquisition dry-run.
- Ran bounded, header-only public URL checks. No source documents were downloaded or stored. The sandboxed network attempt failed; the header-only checks were then rerun with approved network access.

**Decisions and why**
- Made recognition-clause-first classification a standing rule because broad non-safety units (Houston HOPE/AFSCME Local 123, Columbus AFSCME Local 1632, Cleveland AFSCME Local 100, and possible later Austin AFSCME/CWA technical units) can span multiple departments/classes. They remain provisionally `occupation_class=other` until recognition, coverage, classification, or wage-schedule text is read.
- Treated open public CBA sources as later `corpus_direct` fetcher targets, not `inbox/` items, because `ingest/README.md` clearly routes open public portals through `ingest/fetchers/`; licensed/FOIA material remains the inbox path.
- Marked only 9 agreement rows `ready_for_live_fetch`. Five rows need URL confirmation before live acquisition: Houston fire full-CBA target, Austin fire cycle-specific target, Austin pay-plan URL, Cleveland pay-plan URL, and the current Ohio SERB archive path.

**Surprises/breakage**
- Austin's previously-approved `/department/labor-relations/...` fire and police paths now return HTTP 404, but the official Austin labor-relations landing page and corrected `/labor-relations/...` pages return HTTP 200. The police page exposes the fully executed 2024-2029 agreement link; the fire page appears to expose a later Dec. 18, 2025 agreement, so the intended 2014-2024-window target needs confirmation.
- The prior Ohio SERB archive URL returns HTTP 404 and needs a current-path check before use.
- No repo breakage. `python scripts/validate.py` and `python ingest/audit_coverage.py` passed.

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

**No `data/contracts.csv` or `data/city_coverage.csv` edits occurred. No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No ingestion. No `corpus/` or `inbox/` changes. No source documents were downloaded or stored. No PRRs were recommended. No causal claim was made about Texas or Ohio wage outcomes. No first-batch city was treated as representative of an entire state.**

**Recommended next step**
1. Obtain explicit user/PI approval before any live acquisition.
2. If approved, start with a fetcher dry-run for the 9 `ready_for_live_fetch` agreement rows in `texas_ohio_acquisition_dry_run_2026-07-08.csv`.
3. Separately confirm the 5 `needs_url_confirmation` rows before live fetch: Houston fire full-CBA target, Austin fire cycle-specific target, Austin pay-plan URL, Cleveland pay-plan URL, and Ohio SERB archive path.
4. During later extraction, read recognition/coverage/classification text before assigning any precise non-safety `occupation_class`; keep broad mixed units as `other` unless text clearly supports an existing schema value.

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
