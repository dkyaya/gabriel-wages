# State/City Claim Map Summary — 2026-07-12

## 1. Purpose

`docs/analysis/state_city_claim_map_2026-07-12.csv` (26 rows) is a bridge document between source expansion and future claim-centered reports. It puts every state/city currently touched by this project — 16 codified MA/TX/OH cities and 10 scanned-but-uningested PA/NJ cities — on one sheet, with an explicit distinction between **codified evidence** (`evidence_status=codified_evidence`) and **source-availability hypotheses** (`evidence_status=source_availability_hypothesis`). No PA/NJ row in that CSV is marked `codified=yes`; this is enforced by a parse-back check in the build script. This document is not itself a report — it is a working index to consult before drafting one, and it should be updated after every scan/ingestion/codify wave per `docs/analysis/claim_testing_source_wave_methodology_2026-07-12.md`.

## 2. Current codified states/cities

### Massachusetts (9 cities)

- **Report-ready or close:** Franklin and Seekonk (`matched_triad`, 5-6 occupation classes each) are the corpus's densest cross-occupation anchors, supporting `CLM-2026-07-12-03/04/05`. Somerville (`safety_only`) holds the corpus's single strongest source (a 9-attribute police arbitration award) and its only verified peer-comparator row, but is unmatched and flagged dead weight per `AGENTS.md` coverage discipline.
- **Maybe-ready / needs more evidence:** Wayland (`matched_triad`, but its fire arbitration award returned 0 verified-present attributes and should be reviewed), Boston and Georgetown (`matched_pair`, both missing a fire leg), Newton (`safety_only`, unmatched).
- **Not yet codified:** Worcester and Arlington are ingested (real contracts.csv rows: fire + 2 non-safety classes each) but were never run through codify — 0 evidence-layer rows. These are the cheapest possible next step: no new sourcing required, just a codify wave.

### Ohio (4 cities)

- **Report-ready:** Columbus, Cleveland, Cincinnati, Toledo are all `matched_triad` and jointly anchor `CLM-2026-07-12-01` (report_ready=yes at the state level). Toledo additionally anchors `CLM-2026-07-12-06` (arbitration distinction).
- **Caveats:** Cincinnati is the weakest single city on a per-contract basis — its fire and police-supervisor windows returned zero verified-present attributes. Cleveland's fire interest-arbitration row is flagged/unverified and excluded from primary support.

### Texas (3 cities)

- **Report-ready as a design/source claim, not a wage-gap claim:** Houston (`matched_triad`, the only genuinely matched Texas city) and Austin (`matched_triad`, but its third leg is EMS/safety-adjacent, not an ordinary civilian comparator — treat as exploratory) jointly anchor `CLM-2026-07-12-02`.
- **Not report-ready:** San Antonio (`safety_only`) is the corpus's clearest single-document arbitration-distinction test case (`CLM-2026-07-12-06`) but was deliberately added unmatched for institutional contrast and carries a documented comparator false negative (`CLM-2026-07-12-07`). Its missing non-safety comparator is explicitly `urgent` priority under `CLM-2026-07-12-08`.

## 3. PA/NJ source-availability claims

None of the following are coded evidence. All are candidate-source patterns from `pa_nj_candidate_sources_2026-07-12.csv` and `pa_nj_candidate_sources_followup_2026-07-12.csv`.

**Most promising, in order:**

1. **Philadelphia, PA** (`matched_triad` candidate shape) — police and fire are both document-level with city-hosted provenance (a city-hosted Act 111/interest-arbitration award is unusually strong for this stage); non-safety (AFSCME DC33/DC47) is confirmed to exist and dated but not yet document-level. Would test `H1`/`H2`/`H7` (safety pressure-conversion channels and Ohio-triad-design generalizability) in a second large non-Ohio city.
2. **Newark, NJ** (`matched_pair` candidate shape) — the strongest confirmed non-safety evidence of any PA/NJ city (two distinct direct-PDF unions), with police/fire units unambiguously active and well-documented via PERC decisions, but neither safety CBA resolved to a document yet. Would test `H1`/`H2`/`H5`/`H7`.
3. **Trenton, NJ** (`matched_triad` candidate shape) — this round's biggest single upgrade: an in-window (2019), direct-PDF non-safety CBA appeared where the pilot scan had found nothing at all; police and fire are now precisely named.
4. **Jersey City, NJ** (`matched_triad` candidate shape, dated) — the only city with a document-level candidate for all three roles simultaneously (plus two distinct non-safety unions), but every document found is ~2009-2015, mostly outside the project's 2014-2024 window. A "vintage problem," not a "sources don't exist" problem.

**Weak because non-safety is missing or unresolved:**

- **Pittsburgh** and **Erie, PA** and **Paterson, NJ** all have confirmed, named safety unions but a genuinely unresolved (Pittsburgh/Erie) or hard-gap (Paterson) non-safety leg.
- **Allentown, PA** — all three unions are now correctly identified (a follow-up-round correction: the non-safety union is SEIU Local 668, not AFSCME as originally searched), but no leg reached document level.
- **Reading, PA** — the reverse problem: non-safety is Pennsylvania's strongest confirmed evidence (a directly downloadable library CBA), but police is a total, still-unresolved gap even after identifying the specific lodge (FOP #9).

**Weakest overall:**

- **Elizabeth, NJ** — after two search rounds, still has no named non-safety or fire local at all, and only a generic reference for police. Deprioritized; hold further search effort here.

## 4. Recommended next ingestion batch (not yet executed)

Per `pa_nj_source_scan_summary_2026-07-12.md` and `pa_nj_state_city_claim_notes_2026-07-12.md`, the recommended first batch (max 6-12 sources, prioritizing matched-triad completion) is:

| # | State | City | Role | Source | Status |
|---|-------|------|------|--------|--------|
| 1 | PA | Philadelphia | police | FOP Lodge 5 contracts page / Act 111 award | ingest_next |
| 2 | PA | Philadelphia | fire | City-hosted IAFF Local 22 interest-arbitration award | ingest_next |
| 3 | PA | Philadelphia | non_safety | AFSCME DC33 or DC47 signed CBA | needs one more confirmation step (locate signed PDF, not proposal) |
| 4 | PA | Reading | non_safety | Reading Public Library CBA | ingest_next |
| 5 | NJ | Newark | non_safety | City of Newark and IBT Local 97 CBA (2020) | ingest_next |
| 6 | NJ | Trenton | non_safety | City of Trenton and AFSCME Local 2281 CBA (2019) | ingest_next |
| 7 | NJ | Newark | police | PBA/Superior Officers CBA via PERC index | needs PERC-index lookup |
| 8 | NJ | Newark | fire | Firefighters Union/Fire Officers Local 1860 CBA via PERC index | needs PERC-index lookup |

This batch would complete a Philadelphia triad and a near-complete Newark triad, plus bank two additional standalone non-safety documents (Reading, Trenton) against future safety-leg discoveries. It deliberately excludes Jersey City (document vintage needs resolving first) and Elizabeth/Paterson (non-safety gaps unresolved).

## 5. How to use this going forward

- Update `state_city_claim_map_2026-07-12.csv` after every scan, ingestion, or codify wave — a city's `evidence_status`, `codified`, and `matched_design_status` should move as evidence accumulates. A PA/NJ row moves from `source_availability_hypothesis`/`candidate_only`/`codified=no` to `codified_evidence`/`ingested`/`codified=yes` only after it has actually gone through Steps 6-9 of `claim_testing_source_wave_methodology_2026-07-12.md` — never mark a row codified based on a source being merely found.
- Cross-reference `claim_ids_supported_or_relevant` against `claim_register_2026-07-12.csv` before citing any city in a report; the register, not this map, is the authoritative claim text and evidence strength.
- Use the `recommended_next_action` column (`codify_more` / `ingest_next` / `scan_more` / `hold` / `revise_claim` / `report_ready`) as a lightweight per-city to-do list when deciding what a future session should work on next, alongside `hypothesis_tracker_2026-07-12.csv` for what a wave should be testing.
- When a city's status changes, also check whether it changes a claim's `evidence_strength` or `report_ready` field in `claim_register_2026-07-12.csv` — a claim update should follow the rules in Section 5 of the methodology doc, not happen silently.
