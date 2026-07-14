# MA School Committee Meeting Materials Recon

**Date:** 2026-06-24  
**Scope:** narrow public-only reconnaissance of school committee materials, bargaining exhibits, and agenda-packet routes; no ingestion, no PRRs, and no corpus placement changes.

## Purpose

This memo tests whether public school committee materials can supply non-safety wage-comparability reasoning without PRRs.

These materials are best treated as proxy reasoning evidence, not automatic contract evidence. In most cases they belong in the discourse corpus or a separate acquisition queue unless they directly cause or adopt wage terms in a document with clear provenance.

## Source-status table

| municipality | source_route | years_checked | bargaining_unit_focus | materials_found | comparability_or_wage_exhibit_signal | document_type | likely_corpus_destination | access_status | confidence | recommended_next_action | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Somerville | `somerville.k12.ma.us/district-leadership/somerville-school-committee/school-committee-meetings`; `somervillema.gov/event-documents` | live page plus route relevant to 2012-2018 and current archive structure | school committee materials near SMEA/SEU teacher-side bargaining context | agendas, minutes links, public Google Drive for meeting documents, archived presentation route, YouTube recordings | moderate signal; public materials route exists, but the checked page did not itself expose explicit peer-city wage exhibits | agendas, presentations, meeting materials drive, minutes | discourse_candidate | public_packet_found | medium | targeted manual review of archived presentations and meeting-material folders for bargaining slides near the Somerville police-award period | Best overlap case for H1 because Somerville police awards are already the strongest safety-side mechanism evidence |
| Newton | `newton.k12.ma.us/school-committee/screports` | 2009-2025 archive structure plus 2023-2024 negotiations route | NTA 2023-2024 and related school-side bargaining materials | meeting-materials archive, budget materials, fiscal/operations folder, explicit `Negotiations 2023-2024` archive button | strongest signal in this pass; public negotiations archive suggests bargaining presentations or settlement materials may be recoverable | meeting materials, archived reports, budget materials, negotiations archive | discourse_candidate | public_index_found | high | test Newton first with one tightly scoped packet/archive review centered on the `Negotiations 2023-2024` materials | Best public-only non-safety proxy lead found in this pass |
| Boston | `bostonpublicschools.org/school-committee`; `.../meeting-archives`; `.../btu-contract-negotiations` | 2012 archive route observed; 2017-present especially relevant | BTU and other school-side non-safety materials such as paraprofessionals, librarians, nurses, centrally employed staff | long meeting archive, current presentations/materials posts, public BTU negotiations updates | moderate signal; explicit wage proposals and bargaining updates are public, but no peer-city comparability exhibit was confirmed in this pass | meeting posts, presentations/materials posts, negotiation updates | discourse_candidate | public_packet_found | medium | targeted review of one or two recent BTU negotiation material posts before any broader Boston portal work | Promising but fragmented; likely useful for bargaining narrative before it yields clean comparability exhibits |
| Georgetown | `georgetown.k12.ma.us/school-committee/`; linked town route; budget portal | 2020-2023 only, checked cheaply | school-side context for the existing Georgetown matched pair | school committee page, recordings link, budget route | weak signal; archives were reportedly lost during a town website change | school committee page, recordings, budget link | acquisition_lead_only | blocked_or_unreliable | medium | do not prioritize; revisit only if a restored packet archive appears | Existing Georgetown matched pair remains useful, but this route does not currently add strong reasoning evidence |
| Seekonk | official school committee route attempted at `seekonk.k12.ma.us/page/school-committee` | quick current-route check only | optional school-side lead if route is public | none confirmed in this pass | no signal confirmed | none confirmed | acquisition_lead_only | needs_manual_browser_review | low | leave out of the next packet test unless a browser-visible public archive is confirmed manually | TLS handshake failure blocked reliable automated checking, so this is not a good immediate target |

## Municipality-specific checks

### Somerville

- The official Somerville Public Schools school-committee meetings page is public and currently exposes agendas, a public Google Drive for meeting documents, archived presentations, and minutes routes.
- That structure is materially better than a minutes-only archive because it suggests packet-like material and slide decks exist in one place.
- The narrow check did not confirm an explicit wage-comparison exhibit on the inspected page itself.
- Somerville remains high value because any school-side bargaining presentation near the 2012-2018 police-award period would directly improve the H1 comparison design.

### Newton

- Newton Public Schools exposes a durable school-committee materials page with meeting-material folders, archived materials back to 2009, budget folders, and an explicit archived-reports link labeled `Negotiations 2023-2024`.
- That is the cleanest public school-side route found in this pass because it suggests the district itself preserved bargaining-era materials rather than only final contract files.
- The narrow check did not open the negotiations folder contents, so explicit comparability tables are not yet confirmed.
- Even without that confirmation, Newton is the best candidate for one tightly scoped next-step review because the public route is stable, deep, and directly tied to the target dispute cycle.

### Boston

- Boston Public Schools exposes a public school-committee landing page, a long meeting archive, current presentations/materials posts, and a dedicated BTU contract-negotiations page.
- The BTU negotiations page publicly discusses wage proposals, low-wage worker increases, work-year issues, and tentative agreements.
- That is useful bargaining-process evidence, but the checked material looked more like narrative updates than explicit peer-community comparability exhibits.
- Boston is still promising for proxy evidence, but it is operationally heavier than Newton because the portal is larger and the unit structure is more fragmented.

### Georgetown

- Georgetown Public Schools exposes a public school-committee page and related links.
- The page itself states that agendas and minutes were lost during a town-website change and are being rebuilt.
- That makes Georgetown a weak packet route despite its already-useful StateReference matched pair.
- Georgetown should stay secondary unless the packet archive is visibly restored.

### Seekonk

- A quick official-route check was attempted only because the user allowed it if time remained.
- The route did not complete reliably because of a TLS handshake failure.
- That is enough to mark Seekonk for manual browser review rather than additional automated reconnaissance in this task.

#### Seekonk follow-up: official contract archive

- Follow-up RA review identified an official Seekonk Archive Center contract route that is more valuable than the earlier school-committee meeting-agenda route.
- The meeting-agenda route was not pursued further because it appeared to contain ordinary agendas rather than wage-comparison exhibits or contract materials.
- The official contract archive route exposed public CBAs for police, fire, administrative secretaries, educators, public works, and library employees, so Seekonk is now treated as a public CBA/MOA matched-pair ingestion candidate rather than a meeting-packet lead.
- In the 2026-06-24 ingestion pass, six official archive PDFs were downloaded through the provided public routes and ingested as causal CBA rows; no agenda or minutes files were ingested.

## How to classify meeting materials

- A final signed CBA/MOA or officially adopted agreement can be a `causal_candidate` if full document provenance is available.
- School committee presentations, bargaining updates, minutes, and budget narratives usually do not replace a causal contract row.
- If they explain or justify wages, they are better treated as `discourse_candidate` materials or `acquisition_lead_only` evidence.
- If they include wage-comparison exhibits used during bargaining or adoption, flag them as high-value proxy mechanism evidence, but do not ingest until the team decides corpus placement.
- Meeting minutes are not equivalent to factfinding reports or arbitration awards and should not be coded as such.

## Candidate meeting-materials evidence

| candidate_id | municipality | unit | approximate_date | source_route | title_or_description | why_relevant_to_H1 | public_access_status | likely_corpus_destination | next_action | priority |
|---|---|---|---|---|---|---|---|---|---|---|
| scm_newton_negotiations_2023_2024 | Newton | NTA / school-side non-safety bargaining materials | 2023-2024 | `newton.k12.ma.us/school-committee/screports` -> `Negotiations 2023-2024` | archived school-committee negotiations materials | Most plausible route to public non-safety bargaining reasoning or exhibits in this pass | public_index_found | discourse_candidate | targeted packet/download review of only the negotiations archive contents | P1 |
| scm_somerville_presentations_police_overlap | Somerville | school committee presentations near SMEA/SEU era | roughly 2012-2018 | `somerville.k12.ma.us/.../school-committee-meetings` and archived presentations route | archived school committee presentations and meeting-materials drive | Highest conceptual value because it could create a same-municipality safety-award vs school-side proxy comparison | public_packet_found | discourse_candidate | targeted archive review focused on bargaining or salary-related slide decks | P1 |
| scm_boston_btu_negotiations_updates | Boston | BTU and related school-side staff | 2024-2025 | `bostonpublicschools.org/school-committee/btu-contract-negotiations` | public negotiations updates discussing wage proposals and work-year terms | Strong bargaining-process visibility, even if comparables are not yet explicit | public_packet_found | discourse_candidate | inspect one or two linked materials posts for attached presentations or wage tables | P2 |
| scm_boston_meeting_materials_archive | Boston | school committee presentations/materials | 2012-present | `bostonpublicschools.org/school-committee/meeting-archives` | meeting archive with dated presentations/materials posts | Could surface salary-study or bargaining exhibits attached to school committee meetings | public_packet_found | discourse_candidate | narrow archive check on bargaining-relevant meeting dates only | P2 |
| scm_georgetown_rebuilt_archive | Georgetown | school-side materials for matched-pair context | 2020-2023 | `georgetown.k12.ma.us/school-committee/` | rebuilt agendas/minutes archive if it reappears | Could add context to the Georgetown proof-of-concept pair, but current signal is weak | blocked_or_unreliable | acquisition_lead_only | wait for visible archive restoration before any download work | P3 |
| scm_seekonk_school_committee_route | Seekonk | unknown school-side unit | unknown | attempted official school-committee route | school committee archive existence check only | Low-value fallback lead if a public archive becomes visible | needs_manual_browser_review | acquisition_lead_only | manual browser confirmation only; no further automated work now | defer |

## Recommendation

### 1. Is the school-committee packet route promising enough for one targeted download/ingestion-or-discourse pass?

Yes, but only as a tightly scoped proxy-evidence pass. The route looks promising enough to justify one targeted packet review because Newton, Somerville, and Boston all expose public school-committee material routes that are richer than ordinary contract pages. The likely payoff is discourse or proxy mechanism evidence, not immediate causal-corpus ingestion.

### 2. Which municipality should be tested first?

Newton should be tested first.

It has the clearest public archive structure, the most explicit negotiations-era route, and the least fragmentation relative to Boston. Somerville remains the highest-value conceptual comparison, but Newton is the cleaner operational test of whether this route produces usable non-safety reasoning evidence.

### 3. Should the next step be targeted packet download, more StateReference CBA/MOA ingestion, large-city portal work, or pivot-hypothesis development?

The next step should be a `targeted packet download` pass centered on Newton school-committee negotiations materials.

- Do not resume broad StateReference ingestion yet.
- Do not jump to broader Boston portal work before testing the narrower Newton route.
- Do not pivot yet, because this packet route still looks materially more promising than the already-failing candidate-by-candidate StateReference follow-ons for finding non-safety reasoning evidence.
