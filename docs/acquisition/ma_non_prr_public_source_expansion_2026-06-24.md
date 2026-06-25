# MA Non-PRR Public-Source Expansion Memo

**Date:** 2026-06-24  
**Scope:** public-source strategy only; no downloads, ingestion, or PRRs.

## Purpose

This project is still trying to test H1 with public materials only. The immediate problem is identification, not simple document count. The strongest comparability language currently comes from safety arbitration-award documents, especially the Somerville police awards, while most available non-safety comparators are ordinary CBAs or wage MOAs.

That means public-source expansion has to pursue two distinct goals at once:

1. more clean same-cycle public CBA/MOA pairs, so the project can at least scale a within-city contract panel; and
2. any publicly available non-safety factfinding, arbitration-like, or exhibit-heavy materials that contain actual wage-setting reasoning rather than just final terms.

StateReference remains the cheapest route for CBA/MOA expansion, but it does not by itself solve the non-safety reasoning-document gap. The next pass therefore has to look beyond StateReference before more ingestion attempts.

## School committee route update

- Follow-up recon memo: [ma_school_committee_meeting_materials_recon_2026-06-24.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/acquisition/ma_school_committee_meeting_materials_recon_2026-06-24.md)
- Current read: the route looks promising enough for one tightly scoped public packet review, mainly as proxy or discourse evidence rather than immediate causal-corpus ingestion.
- Top municipality/source to test next: Newton school committee materials, specifically the public `Negotiations 2023-2024` route under `newton.k12.ma.us/school-committee/screports`.
- No PRRs were used or recommended in that recon pass.

## Public-source universe

| source_family | examples / URL route | public availability | likely document types | likely occupations | H1 usefulness | expected bottleneck | recommended use | priority |
|---|---|---|---|---|---|---|---|---|
| StateReference DLR Contracts | `https://www.statereference.com/pages/dlr_contracts`; targeted item/search pages | high | CBA, MOA, OCR copy, attachment metadata | police, fire, clerical, DPW, teachers, school support, mixed AFSCME units | strong for matched CBA/MOA scaling; weak for reasoning-doc gap | wrong jurisdiction, mixed units, no same-cycle counterpart, dispatcher ambiguity | use as the main matched-pair discovery engine, but stop before download when the classification is not clean | P1 |
| DLR Public Information Search | `https://pubinfo.dlr.state.ma.us/` | high | case documents, public filings, contract records, possible indexes | all public-sector units if searchable | medium to high because it is the original state route and may surface non-safety impasse records | incomplete search coverage; many hits are petitions, ULPs, or representation decisions instead of final reports | use for exact docket and party-name checks before city-level searching; record when the route exists even if the final report is absent | P1 |
| Mass.gov JLMC awards | `https://www.mass.gov/lists/jlmc-arbitration-awards` | high | safety arbitration awards and related decisions | police, fire | very high for safety-side mechanism text; near-zero for non-safety comparators | safety-only by design | keep as the benchmark safety reasoning source, not as a non-safety solution | P1 |
| Mass.gov DLR decisions / factfinding pages | `https://www.mass.gov/info-details/dlr-hearing-officer-cerb-and-arbitration-decisions`; `https://www.mass.gov/info-details/fact-finding`; `https://www.mass.gov/info-details/faq-impasse` | high | hearing-officer decisions, CERB decisions, arbitration decisions, process pages, procedural guidance | all occupations, but often indirect | medium: useful for finding the impasse pipeline and filtering false positives | most records are not wage-setting factfinding reports; process pages explain the route but do not produce the report itself | use for source-family mapping, docket triage, and false-positive control | P1 |
| DLR annual reports / public decision indexes | FY2024 annual report route in recon memo; DLR org page links | medium | annual reports, workload summaries, party-name leads, institutional context | all occupations | medium: useful for lead generation and for understanding the safety/non-safety process split | annual reports name disputes but usually do not provide the underlying source document | use for party-name leads and institutional context, not as direct corpus sources | P2 |
| city/town HR or labor portals | Boston OLR, Worcester HR, Arlington HR, Newton city HR | mixed but often high | full CBAs, integrated copies, MOAs, occasional arbitration awards | police, fire, clerical_admin, public_works, library, other | high for clean matched CBA/MOA panels; sometimes moderate for awards or integrated copies | some portals are image-heavy, MOA-heavy, or bot-blocked; many lack non-safety reasoning documents | use for municipalities that already show both safety and non-safety contracts publicly | P1 |
| school committee / school district contract pages | Newton Public Schools HR contracts; district school-committee materials pages | medium to high | teacher CBAs, school support CBAs, meeting packets, budget slides | teacher, clerical_admin, other | medium: strong for non-safety contract coverage and possible meeting-exhibit proxies | different employer from city; many units are mixed; reasoning documents may be hidden in meeting materials rather than contract pages | use as the main public route for teacher and school-side non-safety comparators, with employer matching noted explicitly | P1 |
| MTA / local teacher union pages | `https://www.massteacher.org/`; local union contract pages when public | mixed to low | teacher contracts, bargaining updates, local links | teacher | low to medium: can provide teacher CBAs or leads, but rarely a complete reasoning-document archive | inconsistent public posting; statewide route checked here did not expose a stable public contracts index | use as a fallback lead source after district pages, not as primary provenance | P3 |
| Internet Archive | direct archived portal/download URLs such as the Arlington fire PDF route already used in corpus | medium to high | mirrored CBAs, OCRable PDFs, historical portal files | police, fire, public works, clerical, other | medium to high for recovering public contracts that disappeared from live portals | only useful when a public source once existed; weak for final non-safety factfinding reports | use to recover stable copies of already-public contract files when live portals break or rotate | P2 |
| MuckRock public releases | public Somerville police release page already used in corpus | medium | released CBAs, attached awards, agency response packets | often police/fire; sometimes broader | medium to high when the release is already public and document-rich | coverage is opportunistic and selection-biased; not a systematic statewide source | use only where a release is already public and directly relevant; do not treat it as a next-step request workflow | P2 |
| municipal association / public-sector labor contract archives | LRIS public-facing labor-contract library route; similar public archives if directly accessible | medium | public contract copies, archive-style contract libraries | often police/fire, some non-safety | medium for contract recovery; low for non-safety reasoning-document discovery | archive coverage may skew toward public safety or incomplete libraries | use as a backup archive family when official portals or StateReference are thin | P3 |
| search-engine lead discovery | targeted `site:` queries from the StateReference seed memo and exact title searches | high as a lead tool only | snippets, page titles, cached leads | all | low by itself; useful only for discovering candidate pages | snippets are not provenance and generate false positives fast | use only to find candidate pages, then stop and verify on the underlying public source | defer |

## H1 contribution by source type

| source_type | example source families | what it can tell us | what it cannot tell us | expected GABRIEL comparability signal | role in H1 |
|---|---|---|---|---|---|
| safety arbitration awards | JLMC awards; integrated public releases such as Somerville police | explicit reasoning, peer-city wage comparisons, arbitration framing, institutional backstop | whether safety differs from non-safety after controlling for source type | high | current strongest mechanism evidence; still confounded because the non-safety side is thin |
| non-safety factfinding reports | DLR factfinding route; school-committee impasse records if publicly posted | whether non-safety wage-setting also uses explicit comparability reasoning | whether all non-safety bargaining behaves this way when no impasse occurs | potentially high if found | best missing document type for a clean H1 mechanism test |
| non-safety arbitration awards, if any | DLR or other public impasse routes if a true non-safety award exists | direct award-vs-award comparison with safety | generalizability if only a few units arbitrate publicly | potentially high | ideal but likely rare in the current public universe |
| safety CBAs/MOAs | StateReference, city HR portals, Internet Archive | contract structure, no-strike clauses, arbitration backstops, comparability clauses if stated in the agreement | the reasoning that produced the settlement if the final document is a short MOA or silent CBA | low to medium | useful for scaling the safety side of a broad panel, but not enough alone to isolate H1 |
| non-safety CBAs/MOAs | StateReference, city/school portals, teacher pages | same as above for non-safety units; can reveal explicit comparability clauses or absence of them | why the parties settled, absent a reasoning document | low | essential for matched-pair scale, but weak as a stand-alone mechanism test |
| public meeting packets / minutes with wage-comparison exhibits | school committee meeting materials, city council packets, finance committee packets | public wage tables, peer-city comparisons, bargaining presentation exhibits, management rationale | final legal wage-setting document status unless linked back to bargaining outcome | medium if exhibits are explicit | viable public proxy if non-safety factfinding reports remain unavailable |
| budget narratives or discourse sources | budget books, mayoral narratives, union updates, news | public explanation, political framing, chronology | causal contract mechanism; these do not belong in `contracts.csv` | variable and not directly comparable | useful only in the discourse corpus; cannot replace causal documents for H1 |

## Non-PRR H1 viability assessment

Public sources can realistically do three things well.

First, they can build a much larger matched CBA/MOA panel through StateReference plus municipal and school portals. Second, they can preserve the safety-side mechanism benchmark through JLMC awards and already-public releases such as Somerville. Third, they can surface some proxy reasoning materials, especially school-committee meeting packets, budget exhibits, and occasional archived or integrated contract files.

Public sources probably cannot guarantee a clean statewide panel of non-safety factfinding or arbitration-like reasoning documents. The DLR factfinding route is real and public in principle, but the public web surface is thin, incomplete, and often dominated by petitions, CERB rulings, or procedural decisions rather than final wage-setting reports.

Evidence threshold that would justify continuing H1 in public-only mode:

- about `25-40` validated public CBA/MOA rows with several clean same-cycle matched pairs across municipalities; and
- at least one genuine non-safety factfinding or arbitration-like public document, or enough meeting packets/exhibits with explicit peer-community wage reasoning to serve as a disciplined non-safety proxy set.

Evidence threshold that should trigger a pivot:

- public expansion yields mostly more CBAs/MOAs while non-safety reasoning documents remain absent; and
- meeting packets/exhibits do not provide explicit comparability reasoning strong enough to compare against safety awards.

If that happens, H1 should be labeled plausible but underidentified in the public corpus, and the project should pivot toward a source-type/document-production or bargaining-friction hypothesis rather than force an occupation-only interpretation.

## Targeted search plan

| search_target | source_family | exact query pattern or route | expected useful hit | stop rule | risk / false positive | output to record |
|---|---|---|---|---|---|---|
| same-cycle CBA/MOA matched pairs | StateReference DLR Contracts | `https://www.statereference.com/items?collection=dlr_contracts&query={municipality}` plus targeted title checks from the seed memo | police/fire plus a clean `clerical_admin`, `public_works`, `teacher`, `library`, or clearly classifiable `other` comparator | stop after 10 candidate item pages for one municipality or 5 failed same-cycle match attempts | mixed units, wrong-state employers, dispatcher/public-safety-adjacent units | municipality, candidate titles, cycles, class guess, counterpart status, and next-action classification |
| exact original-route confirmation for a StateReference lead | DLR Public Information Search | `https://pubinfo.dlr.state.ma.us/`; exact employer name or known case number | confirmation that the public route exists, even if StateReference is easier to browse | stop after 3 employer-name variants or 3 case-number variants per lead | incomplete search coverage; procedural documents only | whether the original DLR route exists and what document category shows up |
| public non-safety factfinding reports | DLR Public Information Search; DLR decisions pages; DLR annual reports | exact case no. when known; otherwise party-name searches from recon memo | final factfinding report, final award, or clear case index | stop if results are only petitions, ULPs, representation rulings, or strike decisions for a target | easy to confuse procedural rulings with wage-setting reports | case number, party names, document type, whether a final report is publicly visible |
| public meeting packets with wage-comparison exhibits | school committee meeting materials; city council/finance/labor pages | meeting-material pages plus exact municipal/school search terms like `collective bargaining`, `salary study`, `comparables`, `settlement`, `fiscal impact` | packet, slide deck, or exhibit with peer-city wage tables | stop after 10 packet pages or 3 school years for one employer | budget materials may discuss finances without any labor comparables | employer, meeting date, packet type, and whether explicit wage comparables appear |
| school committee negotiation / factfinding records | school district HR pages and school committee materials | district HR contract page plus school committee meeting-materials archive and exact unit names | teacher or school-support contract page, impasse memo, or exhibit trail | stop after 5 years of archive pages with no bargaining material | school-side records may be current contracts only, not reasoning documents | employer, unit, cycle, whether the route yields only contracts or also exhibits/process records |
| MuckRock public releases | MuckRock | exact city + union + `collective bargaining agreement` or known request page | already-public release with attached CBA/award packet | stop after 5 request pages per municipality | request page may exist without a useful released attachment | request URL, agency, whether attachments are public and relevant |
| Internet Archive municipal contract portals | Internet Archive | exact historical portal file URL when known, or municipality + contract filename route | stable archived PDF mirror of a public contract document | stop after 5 archived-file attempts per municipality | archived file may be stale, incomplete, or not the target cycle | archived URL, file type, cycle in title, and whether it mirrors a public portal document |
| large-city labor portals | city/town HR or labor portals | direct portal routes first: Boston OLR, Worcester HR, Newton HR, school district HR | many unit contracts on one page, possible integrated copies or awards | stop after 10 unit links reviewed on one portal if no clean same-cycle plan emerges | MOA-heavy portals can create lots of rows with weak mechanism text | portal status, major units present, document mix (`cba` vs `moa` vs award), and likely matched-pair opportunities |
| teacher-local public pages | MTA/local teacher union pages | local union name + `contract` after district-page verification fails | posted teacher contract or bargaining update that points back to a public PDF | stop after 5 local-union pages for one municipality | public statewide index may be absent; updates may be narrative only | whether the local-union route provides a contract PDF, a lead, or nothing useful |
| archive-style contract libraries | LRIS or similar public contract archive pages | direct archive route, not broad browsing | archived public contract copy when official portal is gone | stop after one archive family per municipality if no clear hit | archive may skew toward police/fire or require deeper browsing than the stop rule allows | archive family checked, municipality, and whether it added anything beyond official/public routes |

## Current recommendation

Run one more structured public-source pass before any new ingestion wave.

That pass should prioritize:

1. `StateReference + DLR route confirmation` for the best remaining clean-pair leads, especially Seekonk.
2. `school committee meeting-materials and district contract pages` as the main public proxy route for non-safety reasoning evidence.
3. `large-city labor portals` where many contracts can be triaged quickly without broad crawling.

It should not assume that more StateReference downloads alone will solve H1.
