# Massachusetts non-safety award acquisition queue

## Purpose

This memo identifies Massachusetts non-safety factfinding reports or interest-arbitration-style wage documents that could make the current GABRIEL pilot less dependent on a safety-versus-non-safety document-type contrast. It is an acquisition queue, not an ingestion manifest. No row below should be added to `data/contracts.csv` until a genuine source PDF is locally present, source type is verified, and metadata can be filled without inference.

## Current corpus gap

The current Massachusetts corpus has two healthy matched pairs, both comparing fire contracts or wage memoranda against non-safety CBAs/MOAs. Four safety observations have no same-cycle non-safety comparator. The sharpest problem for H1 is that the highest-scoring safety observations are police/fire award-style documents, while the currently available non-safety comparators are mostly CBAs or MOAs. The next acquisition target should therefore be non-safety `factfinding` first, then any true non-safety wage-setting arbitration award if available.

Validation and coverage audit snapshot before this memo:

```text
contracts: 12
discourse: 0
coverage: 12
city_attributes: 3
healthy matched pairs: 2
safety units without same-cycle comparison unit: 4
```

## Targeted recon follow-up

Follow-up memo: `docs/acquisition/ma_non_safety_factfinding_recon_2026-06-23.md`.

Bottom line: targeted reconnaissance found better request routes and docket leads, but no final non-safety factfinding report or non-safety interest-arbitration award is ready for ingestion. The top concrete leads are Boston Teachers Union / Boston School Committee `PS-17-5987`; Newton Public Schools Custodians Association / Newton School Committee `PS-16-5177`; Newton Teachers Association / Newton School Committee `SI-23-10203` and `SI-23-10230`; and Somerville non-safety 2012-2018 units as a no-docket-yet but highest-priority public-records target.

Petitions, ULP decisions, strike rulings, representation decisions, docket sheets, and closing letters are acquisition leads. They are not `source_type = factfinding` corpus rows unless the returned document is a final factfinding report; they are not `source_type = arbitration_award` unless the returned document is a final interest/contract-impasse award.

Priority order after the recon pass:

1. Somerville DLR plus city/school public-records requests for 2012-2018 non-safety impasse/factfinding records.
2. DLR exact-case request for Boston BTU `PS-17-5987`.
3. DLR exact-case request for Newton custodians `PS-16-5177` and Newton NTA 2023-2024 verification records tied to `SI-23-10203` / `SI-23-10230`.

## Priority gap table

| priority | city_id | city_name | target safety obs_id(s) | target cycle overlap | preferred non-safety occupation_class | acceptable non-safety units | desired source_type | search/source route | access status | why this target matters | notes |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ma_somerville | Somerville, MA | `ma_somerville_police_spsoa_2012`; `ma_somerville_police_spea_2012` | 2012-2015 and 2012-2018 | `teacher`; `clerical_admin` | Somerville Teachers Association / SEU Unit A; Somerville Municipal Employees Association; Somerville clerical/admin units | `factfinding` | Mass.gov DLR search and DLR annual reports; Somerville schools; city HR; union archives | `needs_review` | Somerville has two unmatched police observations and is central to separating safety-unit language from award-document language. | Official search produced a low-confidence Somerville Teachers fact-finding lead in FY2015 DLR search results, but no underlying report was found or verified. |
| 2 | ma_newton | Newton, MA | `ma_newton_police_2015` | 2015-2018 | `clerical_admin`; `public_works`; `teacher` if cycle repeats | AFSCME municipal units; Teamsters/DPW; Newton Teachers Association only if the cycle overlaps or a future Newton police award is ingested | `factfinding` | Newton HR and school committee archives; Mass.gov DLR/CERB search; DLR annual reports | `not_found` for 2015-2018; `needs_review` for 2023-2024 teacher lead | Newton currently has an unmatched police observation, but the strongest public non-safety impasse trail appears later than the current police row. | Newton Teachers Association 2023-2024 is a future acquisition lead for the Newton 2025 police award in the inventory, not a comparator for the current 2015-2018 police row. |
| 3 | ma_boston | Boston, MA | `ma_boston_police_2020` | 2020-2025 | `clerical_admin`; `teacher` | SENA Local 9158; BTU/BASAS; AFSCME or SEIU city units with clear wage-cycle documents | `factfinding` | Boston Office of Labor Relations; Mass.gov DLR decisions/search; union pages | `needs_review` | Boston has the largest unmatched police award-style observation. A true non-safety factfinding document would be a high-value document-type control. | Public DLR hits for SENA and BTU/BASAS were representation, prohibited-practice, or hearing-officer decisions, not wage impasse factfinding. |
| 4 | ma_arlington | Arlington, MA | `ma_arlington_fire_2021`; future police award targets `JLM-19-7773`, `JLMC-22-9174` | 2021-2024 and 2018-2021 | `public_works`; `teacher` | AFSCME Local 680; Arlington Education Association Unit A | `factfinding` | Town HR/labor contracts; AEA/AFSCME pages; Mass.gov DLR search | `not_found` | Arlington already has a same-cycle public works CBA comparator, but a non-safety factfinding report would reduce document-type imbalance. | Lower priority than Somerville/Boston/Newton because there is already a basic same-cycle comparator. |
| 5 | ma_worcester | Worcester, MA | `ma_worcester_fire_2017` | 2017-2020 | `public_works`; `clerical_admin`; `teacher` | Teamsters Local 170; NAGE Local 490; EAW if a repeatable public source exists | `factfinding` | Worcester HR/labor contracts; Mass.gov DLR annual reports/search; union archives | `not_found` | Worcester has a healthy pair, but it is still CBA/MOA-heavy. A true factfinding report would improve mechanism checks if more safety awards are added. | Lower priority because current Worcester coverage already includes multiple non-safety comparators. |
| 6 | ma_newton | Newton, MA | future police award target `JLMC-23-10055` | likely 2023-2025 | `teacher` | Newton Teachers Association / Newton School Committee | `factfinding`; `arbitration_award` if a binding successor-CBA wage award exists | Mass.gov CERB strike-petition records; FY2024 DLR annual report; Newton School Committee; court record trail | `needs_review` | This is the strongest public trail for a non-safety wage impasse, but it belongs to a future Newton safety-pair build. | Do not use for the current 2015-2018 Newton police row unless a separate overlapping non-safety document is found. |

## Candidate document and search-lead table

Rows below are acquisition leads only. None has passed local first-page/entity/source-type verification as an ingestible non-safety factfinding or arbitration PDF.

| candidate_id | city_id | city_name | bargaining_unit_name | occupation_class | estimated cycle_start | estimated cycle_end | source_type | source_url_or_cite | retrieval_route | access_status | confidence | first-page/entity check status | match rationale | next action |
|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|
| `cand-ma-somerville-teachers-factfinding-2014` | ma_somerville | Somerville, MA | Somerville Teachers Association / Somerville School Committee | `teacher` | unknown | unknown | `factfinding` | Mass.gov search lead tied to FY2015 DLR Annual Report; annual report URL checked: `https://www.mass.gov/doc/fy-2015-dlr-annual-report/download` | Official Mass.gov search API, then annual-report text check | `needs_review` | low | `not_checked_no_source_document` | If the underlying factfinding report covers 2012-2015, it would be the best comparator for both Somerville police rows. | Search/request DLR records by party name and any PS docket number; do not ingest the annual report itself. |
| `cand-ma-newton-teachers-2023` | ma_newton | Newton, MA | Newton Teachers Association / Newton School Committee | `teacher` | 2023 | 2024 | `factfinding` or `arbitration_award` if produced by successor-CBA process | FY2024 DLR Annual Report; Mass.gov CERB strike-petition records `SI-23-10203` and `SI-24-10951` | Official Mass.gov DLR/CERB search and FY2024 annual-report text check | `needs_review` | medium for impasse trail; low for target source document | `not_checked_source_not_downloaded` | Strong future comparator for Newton police 2025 award, but not an overlap match for `ma_newton_police_2015`. | Manually locate/request any fact-finder report or binding-arbitration wage output from DLR, Newton School Committee, or court-related records. |
| `cand-ma-boston-sena-2020` | ma_boston | Boston, MA | SENA Local 9158 / City of Boston | `clerical_admin` | 2020 | 2025 | `factfinding` | Mass.gov DLR decisions/search hits involving SENA Local 9158, including representation/prohibited-practice matters rather than impasse awards | Official Mass.gov DLR search | `needs_review` | low | `not_checked_no_target_document` | A Boston clerical/admin factfinding report would be an important comparator for the 2020-2025 Boston police award. | Search DLR interest-mediation/factfinding dockets by party name; check Boston Office of Labor Relations archives; avoid MUP/MCR-only decisions. |
| `cand-ma-somerville-smea-2023` | ma_somerville | Somerville, MA | Somerville Municipal Employees Association / City of Somerville | `clerical_admin` | 2023 | 2024 | `factfinding` | FY2024 DLR Annual Report mentions Somerville Municipal Employees Association CERB decisions, not wage factfinding | Official Mass.gov DLR annual-report text check | `not_found` | low | `not_checked_no_target_document` | Useful party-name route for future Somerville non-safety searching, but no wage-setting document was found. | Use party names for manual DLR record search; do not ingest CERB representation/accretion decisions as wage comparators. |
| `cand-ma-arlington-aea-afscme-2018-2024` | ma_arlington | Arlington, MA | Arlington Education Association or AFSCME Local 680 | `teacher` or `public_works` | 2018 | 2024 | `factfinding` | No direct official hit from targeted Mass.gov searches | Mass.gov DLR search; town/union route still manual | `not_found` | low | `not_checked_no_document` | Would improve Arlington document-type balance for fire 2021 and future police awards. | Search town meeting/labor records and DLR by party names; request records if no public PDF exists. |
| `cand-ma-worcester-nage-teamsters-2017-2020` | ma_worcester | Worcester, MA | NAGE Local 490 or Teamsters Local 170 / City of Worcester | `clerical_admin` or `public_works` | 2017 | 2020 | `factfinding` | No direct official hit from targeted Mass.gov searches | Mass.gov DLR search; Worcester HR/manual records route | `not_found` | low | `not_checked_no_document` | Would improve Worcester mechanism checks, but Worcester already has same-cycle non-safety comparators. | Lower-priority manual search after Somerville, Boston, and Newton leads. |

## Source-route notes

Mass.gov JLMC interest-arbitration decisions are police/fire only and should not be used as the non-safety acquisition source. They are useful for confirming safety-award targets, including future inventory items, but they do not solve the non-safety comparator gap.

DLR annual reports are useful for procedural context and party-name leads. FY2015, FY2016, and FY2024 reports repeat the relevant distinction: non-police/fire public-sector impasse proceeds to factfinding, while police/fire impasse proceeds through JLMC arbitration. Annual reports should not be ingested as contract/award observations unless the study later creates a separate institutional-context corpus.

## Manual-download instructions

Save manually downloaded public PDFs or public-records returns under the existing inbox convention:

- Use `inbox/foia/` for manually downloaded public PDFs, agency responses, and public-records/FOIA returns.
- Use `inbox/licensed/` only for genuinely licensed or restricted materials.
- Record every acquired file in `inbox/manifest.csv` before processing.

For manifest and later contract metadata, record at minimum:

- proposed `obs_id`
- `city_id`, `city_name`, and `state`
- `bargaining_unit_name`
- `occupation_class`
- `cycle_start` and `cycle_end`
- `source_type`
- `source_corpus`
- `source_url_or_cite`
- `retrieval_date`
- `retrieval_method` (`public_download` for direct public browser downloads; `foia` for public-records returns)
- local file path and intended corpus destination
- first-page/entity verification notes
- wage and cycle notes
- `text_quality` if known

Do not add rows to `data/contracts.csv` until the PDF is locally present, the first page and parties have been checked, the source type is verified as the desired wage-setting document, and the file has been processed through the ingestion pipeline. Do not fabricate cycle dates, parties, URLs, or source type from search snippets. If a direct download is blocked, mark the lead `found_blocked_manual` or `needs_review`; do not bypass access controls.
