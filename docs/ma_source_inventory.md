# MA Source Inventory — for Claude Code verification + extraction

Compiled via claude.ai web search, 2026-06-17. Purpose: hand to Claude Code to
verify each link resolves, download into `inbox/foia/` (or `inbox/licensed/`
if paywalled), build `inbox/manifest.csv` rows, and run
`python ingest/process_inbox.py`. Prioritize public sources; FOIA only where
flagged.

**Known systemic issue (see Worcester precedent):** many city portals post
successor wage **MOAs**, not full base CBAs. MOAs lack the mechanism clauses
(arbitration, comparability, no-strike) GABRIEL needs. Check each downloaded
doc's length/content — a 1-3 page wage-only doc is an MOA, not a base CBA.

---

## Boston — VERIFIED (template city)
- **Portal:** https://www.boston.gov/departments/labor-relations#collective-bargaining-agreements
- **Legacy archive:** cityofboston.gov/images_documents/ (older CBAs)
- **Safety:** BPPA (police) CBAs present.
- **Non-safety:** SENA Local 9158, SEIU Local 888, AFSCME (clerical) — same portal, overlapping cycles.
- **Caveat:** 2020+ BPPA cycle SETTLED after entering JLMC jurisdiction (no award) — flag as `settled_or_awarded=settled`.
- **Action:** download safety + 1 clerical CBA from portal, in 2014-2024 window.

## Worcester — PARTIALLY COLLECTED (MOA gap, c.66 in flight)
- **Portal:** Worcester city HR portal (already used).
- **Status:** Fire (Local 1009), NAGE 490 (clerical), Teamsters 170 (DPW) wage
  MOAs for 2017-2020 already ingested into `contracts.csv`. No mechanism
  clauses — base CBAs requested via c.66 (submitted, response pending).
- **Action:** none until FOIA response arrives. Do not re-collect.

## Newton — VERIFIED, public, no FOIA needed
- **City portal (non-school):** https://www.newtonma.gov/government/human-resources/union-contracts
  — hosts police + other municipal CBAs.
- **Schools (teachers, NTA):** https://www.newton.k12.ma.us/human-resources/collective-bargaining-agreements
  — separate employer (School Committee), so a different portal.
- **Safety:** Newton Police Association CBA should be on the city HR portal.
- **Non-safety:** NTA (teachers) on schools portal — note this is a *different
  employer* than the city, worth flagging in `bargaining_unit_name`/notes.
  Prefer a same-employer comparison (clerical/DPW) on the city HR portal if present.
- **Action:** fetch police CBA from city portal; fetch a same-employer
  clerical/DPW CBA from the same portal if listed; only use NTA if no
  same-employer comparison exists.

## Quincy — VERIFIED, public, no FOIA needed
- **HR directory (lists unions, may link docs):** https://www.quincyma.gov/departments/human_resources/employee_information.php
- **Units confirmed to exist:** Quincy Police Patrol Officers Association (safety);
  Quincy Public Employees Association (QPEA) — clerical/technical/maintenance/engineering (non-safety, same employer — good match).
- **Caveat:** this HR page lists union reps/names; it's not confirmed yet
  whether actual CBA PDFs are attached here or require a separate request.
  Cleanest safety text so far is the JLMC award (already in
  `ma_award_inventory.csv`), not necessarily a signed CBA.
- **Action:** check the HR page (and city Clerk's office page) for attached
  CBA PDFs for QPPOA + QPEA. If only the award exists publicly for police,
  use the award text for mechanism clauses and flag CBA-proper as a
  potential future FOIA target — don't file FOIA yet, search further first.

## Arlington — VERIFIED, public, no FOIA needed
- **HR page:** https://www.arlingtonma.gov/departments/human-resources
  — explicitly states CBAs are attached as downloadable documents on this page.
- **Non-safety confirmed:** AFSCME Council 93 CBA exists (likely clerical/DPW) — same employer as police, good match.
- **Safety:** Arlington Police — check same HR page; cleanest mechanism text
  may again be the JLMC award (already in inventory) if no full CBA posted.
- **Caveat:** prior verification (last session) flagged 403 to automated
  fetchers — likely need manual browser download.
- **Action:** manually browse the HR page, download Police CBA/award + AFSCME CBA, in-window cycle.

## Somerville — VERIFIED, public release already exists (no new FOIA needed)
- **City HR (general; no direct CBA list found):** https://www.somervillema.gov/departments/human-resources
- **Best safety source — already-public MuckRock release:**
  https://www.muckrock.com/foi/somerville-8/police-union-contractcollective-bargaining-agreement-somerville-police-department-101228/
  — released 2020, contains the **integrated base CBAs for SPEA and SPSOA
  WITH subsequent settlements/arbitration awards attached**. This is exactly
  the mechanism-clause-rich document type we need — better than an MOA.
  Note: as released, SPEA contract expired June 30 2015, SPSOA expired June
  30 2018 — check these fall in/near the 2014-2024 window; may need the
  successor contract too (check city news releases, e.g. the 2025 SPSOA/SPEA
  agreements mentioned in city press releases for FY22-24).
- **Non-safety:** SMEA/SMEU (DPW, library, clerical — multiple units, same
  employer) — check somervillema.gov news/HR for posted CBA text; recent
  news covers a SMEU Unit B contract (FY23-25) in detail but full PDF
  location not yet confirmed.
- **Action:** download the MuckRock release directly (no FOIA needed — already
  public). Search city HR/Clerk site for SMEA/SMEU full CBA PDF; if not found, low-cost FOIA may still beat Worcester's wait since it's a smaller ask.

---

## Summary table

| City | Safety source | Non-safety source | FOIA needed? |
|---|---|---|---|
| Boston | boston.gov OLR portal | same portal (clerical) | No |
| Worcester | already ingested (MOA) | already ingested (MOA) | Yes — submitted, pending |
| Newton | city HR portal | city HR portal (prefer over NTA) | No |
| Quincy | HR page / JLMC award fallback | QPEA via HR page | Maybe (CBA-proper TBD) |
| Arlington | HR page (manual dl) / JLMC award fallback | AFSCME CBA via HR page | No (manual download only) |
| Somerville | MuckRock release (already public) | SMEA/SMEU (TBD location) | No (or minor, smaller ask) |

## Next steps for Claude Code
1. Verify each URL resolves; flag any dead links back to me.
2. Download PDFs to `inbox/foia/` with descriptive filenames.
3. For each, check: is this a full base CBA (has arbitration/comparability/
   no-strike articles) or just a wage MOA? Note in manifest.
4. Build `inbox/manifest.csv` rows with full provenance per
   `docs/schema.md` / `CLAUDE.md` standard.
5. Run `python ingest/process_inbox.py`, then `audit_coverage.py` and
   `validate.py`.
6. Report back: which cities yielded full base CBAs vs MOA-only, and which
   need a FOIA follow-up (Quincy CBA-proper, Somerville SMEA if not found).
