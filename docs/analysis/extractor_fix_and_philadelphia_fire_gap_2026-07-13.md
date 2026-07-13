# Extractor Fix, Full-Corpus Regression, DC47 Packet Breakdown, and Philadelphia Fire-Gap Closure — 2026-07-13

Claim-driven memo, per `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md`. Follow-up to `docs/analysis/philadelphia_nonsafety_rescan_and_nj_extraction_fix_plan_2026-07-13.md`, which diagnosed the extraction bug and proposed a fix but implemented nothing. This session implements the fix, regression-tests it against the whole corpus, corrects production data, gives a document-level breakdown of the DC47/Local 2187 packet, and closes the Philadelphia fire-window gap.

## 1. Current question

Can the documented NJ/PA arbitration/comparability false positives be fixed at the extractor level so they stop recurring, without breaking any genuine positive elsewhere in the corpus? Is the DC47/Local 2187 packet's execution status more precisely characterizable than "compiled packet, unclear"? Can Philadelphia's remaining fire-window (2017-2020) gap be closed with a real, provenance-clean source?

## 2. Evidence found

### Task 1-2: extractor fix, implemented and regression-tested

`ingest/extract_spans.py` changed in three ways:
- **Dropped the bare `binding arbitration` trigger** for `interest_arbitration` entirely. A wage-vocabulary-gated "weak trigger" version was tried first (require `binding arbitration` to co-occur with wage/impasse/statute vocabulary) but was retired after a full-corpus regression run found it produced a *new* false positive: an Ohio Cleveland AFSCME clause resolving a subcontracting/privatization dispute ("final and binding arbitration" over whether an outsourcing "competitive alternative" meets cost/quality standards) happened to also mention "the payment of a living wage," satisfying the wage-vocabulary gate. This is a mechanism this project's own codify codebook already tracks separately (`subcontracting_outsourcing_or_volunteer_substitution`), not interest arbitration. Given a second real false-positive mode surfaced on the first attempt, the trigger was retired rather than further special-cased — under-flagging (leaving a row `unresolved` for future review) is safer than over-flagging (silently contaminating a primary-evidence field).
- **Added a negation/exclusion guard** (`_is_negated`, sentence-scoped) before accepting any `interest_arbitration` match. First implementation used bare newlines as a sentence boundary, which broke on a real case (a PDF line-wrap split "not\n        including" across the boundary, causing the guard to miss it); fixed by dropping newlines as boundaries and scoping only on `.`/`;`.
- **Required both a peer-jurisdiction referent and co-occurring wage vocabulary** before accepting a `comparability` match. A referent-only requirement (Task 1's first pass) still let through a Texas Austin recruiting-vendor clause ("the vendor's demonstrated ability to produce diverse pools of successful firefighters in other major or comparable metropolitan cities") because it structurally matches a peer-city referent pattern despite being about vendor evaluation, not wages.

15 new regression tests were added to `ingest/test_pipeline.py` (54 total, 0 failures), covering all 7 originally-documented false positives/inversions (checklist items 8-14) plus the 2 additional false positives found and fixed during this session's regression testing (the Cleveland subcontracting clause and the Austin vendor clause).

A full-corpus regression check (re-extract all 64 `data/contracts.csv` source PDFs, re-run through the fixed extractor, diff against production) found 19 rows needing correction. All were resolved except one deliberately out-of-scope item:
- **7 documented false positives/inversions (items 8-14):** all confirmed suppressed; flags corrected to `0`, text fields cleared.
- **2 rows with non-verbatim (fabricated) text** (`oh_columbus_police_2023`, `oh_columbus_fire_2023`): a data-integrity issue discovered as a side effect of the regression check, not caused by this fix. A direct substring check confirmed neither row's `arbitration_clause_text` appears verbatim anywhere in its source PDF — a violation of `AGENTS.md`'s verbatim-capture rule, of unknown provenance. Corrected to match what the fixed deterministic extractor actually produces (`0`, cleared) rather than hand-inserting a replacement span, consistent with the project's verbatim-only, no-RA-discretion discipline.
- **2 genuine new true positives found and added:** `oh_toledo_police_2024`'s `interest_arbitration_flag` (a verbatim "shall be subject to an interest arbitration" clause, previously missed inside a long Cost Containment Committee article) and `oh_cincinnati_fire_2023`'s `me_too_clause_flag` (a verbatim "'Me-too' with FOP on wages..." clause, previously blank).
- **8 blank→`0` normalizations** (`comparability_clause_flag`/`me_too_clause_flag` on several TX/OH rows) — cosmetic only, no semantic change.
- **8 rows' `no_strike_clause_flag` differ** between the stored value and today's re-extraction (`ma_newton_police_2015` and 7 TX/OH rows). This is **not** attributable to this fix — the `no_strike` trigger list and handling were never touched — and is left uncorrected, flagged in `wage_mechanism_evidence_checklist.md` item 16 as a likely OCR-non-determinism issue for a future, separate investigation.

A final verification regression run confirms the repo is clean with respect to this fix's scope: the *only* remaining diffs between stored data and a fresh re-extraction are exactly those 8 out-of-scope `no_strike` rows.

### Task 3: DC47/Local 2187 packet breakdown

Re-extracted and structurally mapped `pa_philadelphia_other_dc47_local2187_termsheet_2025_2028.pdf` (82,652 characters). It is a "Contract Library" compilation of five distinct documents, not one instrument:
1. **Main "Term Sheet Agreement"** (City and DC47 Locals 2186/2187, July 1 2025 - June 30 2028) — Term/Wages/Bonus/RGI/Most-Favored-Nation provisions.
2. **"City and AFSCME DC47 H&W Side Letter"** (dated July 15, 2025) — Medicare Part B reimbursement, legal services fund, essential employees, sick leave, bereavement, parental leave, sick leave transfer, vacation sellback, life insurance, working out of class. Body text retains a `[signature page to follow]` template placeholder, but the immediately following PDF page shows apparent genuine trailing signature/date content (July 15, 2025, OCR-garbled).
3. **A second, Local-2186-specific side letter** (pilot mediation) — same placeholder-then-apparent-signature pattern.
4. **A wholly separate, earlier "Tentative Extension Agreement"** between the City and DC47 Locals 2186/2187 for the *prior* (2024-2025) cycle. This carries the packet's one clearly-legible bilateral signature block ("FOR THE CITY OF PHILADELPHIA: / FOR AFSCME DISTRICT COUNCIL 47:", dated on or around 8/1) — **this signature block belongs to the 2024-2025 extension, not the 2025-2028 term sheet**, correcting an imprecise claim in the row's original ingestion note (written in the prior session), which had attributed it to the main term sheet's Exhibit-A clause.
5. **The full text of Pennsylvania's Act 195** (Public Employe Relations Act), appended as legal reference material, not a contract.

No single, unambiguous signature page was located specifically for the main 2025-2028 term sheet's own Term/Wages/Bonus provisions. The row's `total_comp_note` was corrected in `data/contracts.csv` to reflect this precise breakdown (see Section 3 below for the sourcing judgment this rests on).

### Task 4: Philadelphia fire-gap scan

AFSCME Local 2186's own official "Contracts" archive page (`afscme2186.org/contracts`) lists 47 documents; extracting the page's link labels (not just URLs, which are opaque hashes on this Wix-hosted site) found one titled **"City Contract & 2186 Memo Agreement 2017-2020."** Downloaded and verified: a genuine "MEMORANDUM OF AGREEMENT BETWEEN CITY OF PHILADELPHIA AND DC47 LOCAL 2186," Item 1: "The Agreement shall be for a three (3) year period from July 1, 2017 through June 30, 2020" — an **exact match** to the already-ingested Philadelphia fire row's cycle (2017-2020). A signature block ("City of Philadelphia: District Council 47, Local 2186:") with visible, if OCR-garbled, signature marks appears at the end. Ingested as `pa_philadelphia_other_2017`. `ingest/audit_coverage.py` now reports Philadelphia fire vs. this row as a healthy **exact-cycle** matched pair — Philadelphia's design is now complete on both legs (police: overlap-cycle vs. the 2025-2028 term sheet; fire: exact-cycle vs. this 2017-2020 MOA).

Rejected/not pursued: a 2011 DC33-v-City legal complaint (no attached CBA, wrong era); a dead `afscme2187.org/wp-content/...2017...` link (404, site migrated); `dc33_contract.pdf` (404).

## 3. Reasoning

The extractor fix directly serves `CLM-2026-07-12-01`/`CLM-2026-07-12-06`/`H2` (the arbitration-distinction and safety-conversion-channel claims), which depend on `interest_arbitration_flag` being trustworthy across states — the fix specifically targets the failure mode that made NJ/PA rows unreliable. The two genuine new positives found (Toledo, Cincinnati) directly strengthen `CLM-2026-07-12-01` (Ohio matched triads) with real, previously-missed evidence.

Philadelphia's fire-gap closure completes a genuinely matched two-leg design (not just occupation-class presence) using the exact same document-level, primary-source-first method that worked for the police leg and for Trenton NJ: browse a union local's own persistent document archive directly, not search-engine snippets.

## 4. Counterevidence / limits

- The weak-trigger retirement means some genuine "binding arbitration + wage context" cases will now go **undetected** (flagged `unresolved`, not `0`) rather than auto-flagged. This is a deliberate precision-over-recall tradeoff, consistent with the project's stated preference that `not_found`/`unresolved` is a weaker, more honest claim than a false positive.
- The two Columbus rows' non-verbatim text is now understood to be a genuine, pre-existing data-integrity issue of unknown origin — not explained, only corrected. A wider audit of `data/contracts.csv` for other non-verbatim fields was **not** performed this session (scoped to the 20 rows already flagged by the regression check); this is a real, open question about the rest of the corpus.
- The 8-row `no_strike_clause_flag` discrepancy is documented but not investigated or corrected. If it reflects genuine OCR non-determinism, it raises a broader reproducibility question for every OCR-quality row in the corpus, not just these 8.
- The DC47/Local 2187 2025-2028 term sheet's own execution remains a totality-of-evidence judgment (persistent hosting + news corroboration + same-round side letters' apparent signatures), not a single unambiguous signature — this was true before this session and remains true after the more precise breakdown; the breakdown corrects *which* document the one clean signature belongs to, it does not add new evidence for the main term sheet's own execution.
- The Philadelphia fire-gap MOA is a short amendment incorporating a 2009-2017 base CBA by reference; the base contract itself is not in the corpus, limiting what classification/reclassification/workload language this row alone can support (same limitation as Worcester's MOA-style rows, checklist item 7).

## 5. What would change our mind

- Finding that the two Columbus rows' fabricated text also affected their `occupation_class` or cycle dates (not just mechanism flags) would elevate this from a mechanism-flag correction to a full row re-verification.
- A reproducibility test showing the `no_strike` discrepancies persist across multiple independent re-extractions of the same PDF (ruling out simple OCR run-to-run noise) would indicate the underlying document text itself is unstable, a more serious pipeline concern.
- Locating a cleaner, unambiguously-executed copy of the DC47 2025-2028 main term sheet (not the compiled packet) would remove the current judgment call entirely.

## 6. Source needs

- A genuine, non-fabricated verbatim source for Columbus's ORC 4117.14(G) impasse/conciliation content, if this claim is to be restored with real evidence (manual grep found the language exists in the source PDF; no safe, general regex trigger for it was added this session — see checklist item 15).
- A cleaner execution record for the DC47/Local 2187 2025-2028 term sheet specifically (as opposed to the compiled packet), if a future session wants to remove the current totality-of-evidence judgment call.

## 7. Recommended next move

**A narrow, already-completed ingestion (the fire-gap MOA, documented above) plus a completed audit-and-correct pass — not a further sourcing run, and not yet a first analytical/codify run.** Specifically:
1. Philadelphia and Trenton NJ are both now design-ready (genuinely matched on both/all legs) for a first controlled GABRIEL/codify wave — not run this session, not authorized.
2. Before that codify wave, consider a dedicated investigation into the `no_strike_clause_flag` OCR-non-determinism question (checklist item 16) and a broader non-verbatim-text audit beyond the 20 rows checked this session, so codify scores a corpus that has been checked as thoroughly as this session checked the arbitration/comparability fields specifically.
