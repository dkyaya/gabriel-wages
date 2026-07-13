# PA/NJ State-City Claim Notes — 2026-07-12

**These are source-availability-informed hypotheses, not coded evidence.** Nothing in this memo has been ingested or codified. Every statement below is bounded to "sources appear to exist" or "sources are confirmed to exist," never "the corpus shows." See `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` (pilot scan, 40 rows) and `docs/analysis/pa_nj_candidate_sources_followup_2026-07-12.csv` (this follow-up, 39 rows) for the underlying candidate records.

## Pennsylvania

### Philadelphia — recommended status: **ingest_next**

- **Sources appear available:** FOP Lodge 5 (police, direct contract page) and a city-hosted IAFF Local 22 interest-arbitration award (fire) are both confirmed document-level candidates with high provenance. AFSCME DC33 (blue-collar) and DC47 (white-collar) both have confirmed signed contracts (with dates and terms) as of this follow-up, though neither has a located signed-CBA PDF yet.
- **Claim/hypothesis it could test:** Philadelphia's dual Act 111 (police/fire) plus AFSCME/PERA (non-safety) framework is a strong candidate to test whether the safety-side interest-arbitration/conversion-channel pattern seen in Ohio (`CLM-2026-07-12-01`, `H1`, `H2`, `H7`) travels to a large non-Ohio city, and to test the arbitration-distinction guardrail (`CLM-2026-07-12-06`) against a second state's interest-arbitration awards.
- **Matched-triad support:** Yes, plausible — police + fire legs are document-level already; non-safety leg is one confirmation step away (locate the signed DC33 or DC47 PDF rather than the proposal/announcement).
- **Non-safety availability:** Not yet fully confirmed as a document, but confirmed as a real, dated, signed agreement (two unions, in fact) — the strongest non-safety situation of any PA city scanned.
- **Public-safety arbitration/factfinding availability:** Yes — Philadelphia is the only PA city in this scan with a city-government-hosted (not just union-hosted) Act 111 interest-arbitration award for fire, directly useful for `H5`/`CLM-2026-07-12-07` (peer/comparator wage evidence, currently `urgent` priority).

### Pittsburgh — recommended status: **scan_more**

- **Sources appear available:** Police (FOP Fort Pitt Lodge 1) is only found third-party-hosted (Scribd) and needs an official-source replacement. Fire (IAFF Local 1) has produced no document lead across two search rounds. Non-safety (AFSCME Local 2719) is now confirmed as a real, recently-signed (2025-12-22) 3-year CBA with a specific union-hosted contracts page — a meaningful upgrade from the pilot scan's budget-appendix inference.
- **Claim/hypothesis it could test:** If confirmed, Pittsburgh would be a second large-city Pennsylvania test of `H1`/`H2`/`H7`, complementing Philadelphia.
- **Matched-triad support:** Plausible but not yet actionable — the non-safety leg is closest to confirmed, but police needs an official-source replacement and fire has no lead at all.
- **Non-safety availability:** Strongest single upgrade of this follow-up round for Pittsburgh — a named, dated, union-hosted contracts page now exists.
- **Public-safety arbitration/factfinding availability:** Not established either round; Pittsburgh has had FOP arbitration litigation historically (case law found in the pilot scan) but no award document located.

### Allentown — recommended status: **scan_more**

- **Sources appear available:** Exactly three unions confirmed to exist (FOP, IAFF Local 302, and — corrected this round — **SEIU Local 668**, not AFSCME as the pilot scan's search terms had assumed). No document-level source found for any of the three across two search rounds; IAFF Local 302's "Contract Documents" page may be member-login-gated.
- **Claim/hypothesis it could test:** Same institutional-contrast value as Philadelphia/Pittsburgh in principle, but currently the weakest-evidenced of the three larger PA cities.
- **Matched-triad support:** Unknown — no leg is document-level yet.
- **Non-safety availability:** Corrected but not resolved: the union is now correctly identified (SEIU, not AFSCME), which should make the next search round more productive, but no document exists yet.
- **Public-safety arbitration/factfinding availability:** Not established.

### Erie — recommended status: **scan_more**

- **Sources appear available:** Police (FOP Lodge 7 / Haas Memorial Lodge) has only ever produced a 2001 case-law reference confirming an Act 111 award existed, not a document. Fire (IAFF Local 293) has produced no document lead. Non-safety (AFSCME Local 2206, clerical/office/maintenance/technical) is a new and meaningful lead this round — a real, recently ratified (2026-03-04) contract, though no PDF was located.
- **Claim/hypothesis it could test:** Erie remains useful mainly as a lower-priority contrast case; it is not currently a strong claim-testing candidate given how little is document-level.
- **Matched-triad support:** No — currently the weakest PA city of the five scanned on a document-availability basis, despite the new non-safety union lead.
- **Non-safety availability:** Improved (union identified, contract confirmed to exist) but still not document-level.
- **Public-safety arbitration/factfinding availability:** Only historical case-law evidence that an award existed in 2001; nothing current.
- **Caveat carried forward:** "Erie" web searches repeatedly surface Erie County, **New York** documents (a different state and jurisdiction) under a similarly generic domain pattern — reconfirmed as an exclusion in the follow-up round.

### Reading — recommended status: **hold** (for police) / **scan_more** (overall)

- **Sources appear available:** Non-safety is Pennsylvania's strongest confirmed document: a directly retrievable Reading Public Library CBA PDF on the city's own domain, plus a confirmed (dated, 2023-2026) AFSCME Local 2763 general-employee agreement referenced in city council minutes (document itself still unlocated). Police is now at least identified by name — FOP Lodge #9 — but has zero document or award evidence across two rounds. Fire (IAFF Local 1803) likewise has no document lead.
- **Claim/hypothesis it could test:** If a police source is eventually found, Reading could test the non-safety classification/admin-channel claim (`CLM-2026-07-12-05`) using the confirmed library CBA as one leg, but currently cannot support a matched triad because the police leg is entirely missing.
- **Matched-triad support:** No — the police leg is a genuine, still-unresolved gap after two search rounds. Recommend holding Reading out of the first ingestion batch specifically because of this gap, even though its non-safety evidence is the strongest in the state.
- **Non-safety availability:** Strongest in Pennsylvania (one confirmed direct PDF, one confirmed-to-exist-but-unlocated document).
- **Public-safety arbitration/factfinding availability:** Not established.

## New Jersey

New Jersey's structural advantage — PERC's centralized public-sector-contracts index and interest-arbitration-awards database — was reconfirmed and materially exploited in this follow-up round: `site:perc.state.nj.us` searches surfaced direct contract PDFs for three of the five NJ target cities (Newark, Jersey City, Trenton) that pure keyword search had missed in the pilot scan.

### Newark — recommended status: **ingest_next**

- **Sources appear available:** Non-safety is now doubly confirmed: the previously-found IBT Local 97 CBA (2020, in-window) plus a newly found AFSCME Local 2297 (Supervisory) CBA (2010, out-of-window but same clean PERC provenance). Police (PBA / Superior Officers Association) and fire (Firefighters Union / Fire Officers Local 1860) are both confirmed as very active, well-documented bargaining units via a substantial PERC decision history (at least 6 distinct decisions for the police/SOA units alone since 2019), but a direct current-cycle CBA PDF was not located for either safety union in either search round.
- **Claim/hypothesis it could test:** Newark is the strongest available test of whether NJ's PERC-documented interest-arbitration environment (`H2`, `H5`, `CLM-2026-07-12-06`, `CLM-2026-07-12-07`) produces a genuine matched triad outside Ohio.
- **Matched-triad support:** Plausible and closest to actionable in NJ — non-safety is document-level (twice over); police and fire units are unambiguously identified and active, needing only a direct PERC public-sector-contracts index browse (by employer name) rather than search-engine indexing to surface the actual CBA PDFs.
- **Non-safety availability:** Confirmed, in-window, and redundant (two distinct unions/documents).
- **Public-safety arbitration/factfinding availability:** Strong circumstantial evidence (extensive PERC decision history for both police and fire units) but not yet a located award document.

### Jersey City — recommended status: **scan_more** (strong lead, dated documents)

- **Sources appear available:** This follow-up round's single biggest structural finding — a genuine three-legged set of direct PERC PDFs: police (Jersey City PSOA, 2009-2012), fire (IAFF Local 1066, 2009-2015), and **two** distinct non-safety unions (Jersey City Public Employees Local 245 and Local 246, both ~2015). All four/five documents are real, on the state PERC domain, high provenance.
- **Claim/hypothesis it could test:** The clearest matched-triad-shape candidate found in either state this round for `H1`/`H2`/`H7` — if a current-cycle successor to each of these ~2009-2015 documents can be located.
- **Matched-triad support:** Yes, structurally — but every leg found is dated to roughly 2009-2015, mostly outside or at the edge of this project's 2014-2024 observation window. This is a "the design exists, the vintage needs updating" case, not a "no sources exist" case.
- **Non-safety availability:** Confirmed and redundant (two unions/documents), though dated.
- **Public-safety arbitration/factfinding availability:** Not directly found this round, but the PERC decision on Jersey City POBA (case law found in the pilot scan) suggests award history exists.
- **Recommended next step before ingestion:** A short, targeted follow-up specifically to find each of these four documents' current-cycle successor (2020s dates) rather than a general re-scan.

### Paterson — recommended status: **hold**

- **Sources appear available:** Police (PBA Local 1, confirmed by name via a 2021 PERC interim-relief decision) and fire (FMBA Local 2 / Tactical Fire Officers Association, confirmed by name via a 2012 PERC decision, including a live staffing-level grievance directly relevant to `H4`) are both real, active, and now precisely named — but neither has a document-level CBA. Non-safety remains a complete gap: the only Paterson-domain PERC documents found in either round are for the *school district*, a different employer entirely from the municipal government.
- **Claim/hypothesis it could test:** The TFOA staffing-level grievance is a specific, concrete lead for `H4` (minimum-staffing centrality) if the underlying document can ever be located.
- **Matched-triad support:** No — non-safety is a hard, repeated gap (two rounds, zero leads), which is disqualifying for the matched-triad design regardless of how well-documented the safety units are.
- **Non-safety availability:** Confirmed absent from search results twice; genuinely the weakest non-safety leg among the five NJ cities.
- **Public-safety arbitration/factfinding availability:** Circumstantial (grievance/dispute history) but no award document.

### Elizabeth — recommended status: **reject_for_now**

- **Sources appear available:** Police (Superior Officers Association) is confirmed only via a general PERC synopsis reference, unchanged since the pilot scan. Fire and non-safety produced literally zero hits — not even a named local — in either search round, including a follow-up round where a targeted `site:perc.state.nj.us "City of Elizabeth"` search returned no Elizabeth-specific results at all.
- **Claim/hypothesis it could test:** None currently supportable — there is not enough named-unit information, let alone document-level evidence, to scope a claim.
- **Matched-triad support:** No.
- **Non-safety availability:** None found across two rounds.
- **Public-safety arbitration/factfinding availability:** Not established.
- **Recommendation:** Elizabeth is now the weakest-evidenced city across both states after this follow-up round. Deprioritize relative to the other four NJ cities; do not spend further search effort here until Newark, Jersey City, and Trenton are resolved.

### Trenton — recommended status: **scan_more** (biggest single upgrade of this follow-up round)

- **Sources appear available:** Non-safety went from a complete pilot-scan gap to a confirmed, in-window (2019), direct PDF: City of Trenton and AFSCME Local 2281 (White Collar/Blue Collar). Police (PBA Local 11, named via a 2014 PERC decision) and fire (Trenton Fire Officers Association / FMBA Local 206, named via a 2012 PERC decision referencing a 2006-2013 cycle) are both now precisely identified, though neither has a located current-cycle CBA PDF.
- **Claim/hypothesis it could test:** If police/fire documents can be located, Trenton becomes a strong second NJ matched-triad candidate alongside Newark, testing the same `H1`/`H2`/`H7` pattern with genuinely in-window non-safety evidence already in hand.
- **Matched-triad support:** Plausible — non-safety is document-level and in-window (the single best-dated non-safety find of this entire follow-up round, PA or NJ); police and fire need one more PERC-index lookup each.
- **Non-safety availability:** Confirmed, in-window, high provenance — the standout finding of this follow-up round.
- **Public-safety arbitration/factfinding availability:** Named units exist with a documented historical CBA date range (fire, 2006-2013) but no current award located.

## Cross-cutting observations

- **New Jersey's PERC-index advantage, reconfirmed and sharpened:** direct `site:perc.state.nj.us` queries (rather than generic keyword search) surfaced document-level PDFs for Newark, Jersey City, and Trenton in this follow-up round that generic search missed in the pilot scan. This is now a specific, repeatable technique worth recording: **for NJ cities, search `site:perc.state.nj.us "<City Name>" <union type> pdf` directly, not just `<city> <union> collective bargaining agreement`.**
- **Pennsylvania has no equivalent centralized index.** Every PA confirmation this round came from a city-specific or union-specific lead (an AFSCME Council 13 press release, a Facebook page, a union's own "contract agreements" subpage) rather than a single institutional source. This structurally caps how fast PA search can proceed relative to NJ.
- **The single most consequential correction this round:** Allentown's non-safety union is SEIU Local 668, not AFSCME — the pilot scan's AFSCME-only search terms explain why Allentown's non-safety leg initially looked like a hard gap. Future PA city scans should search for FOP + IAFF + AFSCME **and** SEIU/CWA/Teamsters by default, not assume AFSCME is the only non-safety union family.
