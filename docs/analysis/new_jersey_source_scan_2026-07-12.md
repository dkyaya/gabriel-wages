# New Jersey Source Scan — 2026-07-12

Scope: bounded, public-web source-availability scan. No downloads, no ingestion, no codify. See `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md` for constraints and `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` for the full candidate list (19 New Jersey rows, plus 3 statewide institutional-index rows filed under `state=New Jersey, city=statewide`).

## Cities scanned

Newark, Jersey City, Paterson, Elizabeth, Trenton.

## The single most important finding: a statewide institutional index

New Jersey's Public Employment Relations Commission (PERC) maintains a state-mandated, centralized, public index of essentially all New Jersey public-sector collective negotiations agreements (`nj.gov/perc/conciliation/contracts/` and the underlying `perc.state.nj.us/publicsectorcontracts.nsf` database — reported at roughly 700+ police/fire contracts alone) **and** a separate, dedicated Police and Fire Interest Arbitration Awards database (`perc.state.nj.us/IAAwards.nsf`). Employers are statutorily required to file both. This is a fundamentally different search environment than Pennsylvania, where no equivalent centralized award/CBA index was found in this scan. These two portals are recorded as `selection_priority=ingest_next` `context_only` rows because they are indexes, not documents — the recommended next step is to browse them by employer name for each target city, not to treat the portal page itself as a source.

## Strongest candidate matched cities

**Newark is the clear NJ leader** and currently the single strongest matched-triad lead across both states:
- Police: a PERC decision (No. 2022-34) confirms an active Newark Police Superior Officers' Association bargaining unit; the underlying CBA is expected to be retrievable via the PERC contracts index.
- Fire: a PERC contracts-index entry for the Newark Firefighters Union, plus a separately identified Newark Fire Officers Union (IAFF Local 1860).
- Non-safety: a **directly retrievable PDF**, the City of Newark and IBT (Teamsters) Local 97 CBA (2020), hosted on the PERC domain itself — the strongest confirmed non-safety document found in this entire scan (PA or NJ). Per the recognition-clause-first standard, its `occupation_class_candidate` is recorded as `other` pending a read of the recognition/coverage clause — do not infer sanitation/public-works coverage from the "Teamsters" name alone.

Jersey City, Paterson, and Elizabeth all have confirmed active police (PBA/Superior Officers) and fire (FMBA/TFOA-equivalent) bargaining units via PERC decision/synopsis references, but no city produced a directly retrievable document in this web-search-only pass — all are routed to the PERC index for follow-up. Paterson additionally surfaced a live staffing-level grievance involving its fire-officer unit (TFOA), which is directly relevant to the minimum-staffing hypothesis (H4) if the underlying document can be retrieved later. Trenton produced the least distinct evidence of the five NJ cities scanned.

A jurisdiction-mismatch risk was also documented and excluded: Passaic County's own CBA page is a *county*, not City of Paterson, source, and is recorded as `reject` so it is not mistaken for a Paterson municipal document later.

## Non-safety availability

Better than Pennsylvania in this scan, but concentrated in one city: only Newark produced a confirmed direct non-safety document (IBT Local 97). Jersey City, Paterson, Elizabeth, and Trenton have no non-safety candidate yet — all are expected to be resolvable via the PERC index rather than being genuinely unavailable, unlike some PA cities where no lead of any kind existed.

## Arbitration / factfinding availability

Strong and structurally superior to Pennsylvania for this scan's purposes: NJ's interest-arbitration awards are centrally indexed by PERC, in addition to the general contracts index. This directly serves the arbitration-distinction claim (`CLM-2026-07-12-06`) and the under-evidenced comparator hypothesis (`H5`), which the national claim-driven plan flagged as `urgent` source-need priority.

## Source-owner / provenance notes

Nearly every New Jersey candidate in this scan traces back to a single official domain (`nj.gov`/`perc.state.nj.us`), which is a meaningfully cleaner provenance picture than Pennsylvania's mix of city sites, union sites, and one third-party document host. The main caveat: the PERC contracts database uses a legacy Lotus Notes (`.nsf`) interface, which may complicate systematic browsing/automation in a later ingestion pass even though it is fully public.

## Likely ingestion burden

- **Newark: low-medium.** One non-safety document is already in hand; police and fire legs need one more targeted PERC-index lookup each, not open-ended web searching.
- **Jersey City, Paterson, Elizabeth: medium.** Bargaining units are confirmed to exist for all three; the remaining work is retrieving specific documents from the PERC index rather than discovering whether sources exist at all.
- **Trenton: medium-high.** No city-specific lead of any kind surfaced in this scan beyond the general PERC portals.

## Recommended next action

1. In a follow-up (still non-ingestion) pass, browse the PERC public-sector-contracts index and interest-arbitration-awards index by employer name for Newark, Jersey City, Paterson, and Elizabeth to convert `needs_review` context rows into confirmed document-level candidates.
2. Newark is closest to ingestion-ready of any city in either state; prioritize confirming its police and fire CBA text via the PERC index next.
3. Read the Newark/IBT Local 97 recognition clause before assigning a specific non-safety `occupation_class`, per the recognition-clause-first standard.

## Promote for ingestion?

**Yes, conditionally — New Jersey should be promoted ahead of Pennsylvania for the first reviewed ingestion pass**, on the strength of the PERC centralized index (which lowers future search burden across all five target cities, not just Newark) and the one confirmed non-safety document already in hand. See `docs/analysis/pa_nj_source_scan_summary_2026-07-12.md` for the full cross-state comparison and recommended batch.
