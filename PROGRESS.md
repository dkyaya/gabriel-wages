# Progress Log

Reverse-chronological session log. Newest entry on top. Records **decisions, surprises, and next steps** — not keystroke-level changes (git has those). Pair each entry with the git commits from that session.

Convention per entry: what we did, decisions made (and why), surprises/breakage, corpus snapshot (from `python ingest/audit_coverage.py`), next steps.

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
