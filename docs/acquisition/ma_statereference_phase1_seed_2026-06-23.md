# StateReference Phase 1 Seed Memo - MA public municipal wage corpus

**Date:** 2026-06-23  
**Prepared for repo path:** `docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md`  
**Purpose:** seed a low-cost Phase 1 Codex run using StateReference's public Massachusetts DLR contract records, instead of asking Codex to broad-search Massachusetts from scratch.

---

## Executive bottom line

StateReference is a strong Phase 1 source for **public CBA/MOA collection**, not for solving the non-safety factfinding gap. It aggregates the Massachusetts DLR Contracts collection and exposes many record pages with a title, employer, document link, OCR link, and instructions for finding the original DLR record.

The best immediate use is a **public CBA/MOA matched-pair expansion**:

1. **Georgetown** looks like the cleanest first pilot: same town, same 2020-2023 cycle, public-safety-adjacent police command staff and AFSCME DPW/clerical/custodial comparators.
2. **Seekonk** is a strong second pilot: police 2019-2022 and clerical/school admin records overlapping 2018-2022/2020-2022.
3. **Peabody** is worth verification: police 2018-2021 plus AFSCME 2021-2022 gives at least an overlap seam; may need another non-safety record for a cleaner cycle.
4. **Hanover** is promising: firefighters 2020-2023 and school service employees 2021-2023.
5. **Reading / Marlborough / Lexington / Northbridge / Peabody / Danvers / Springfield** are good second-wave municipalities, but several currently have one-side leads and need counterpart verification.

This memo is a seed list, **not a final ingestion decision**. Every candidate must still pass first-page/entity checks, city/state verification, source-type classification, and repo provenance rules before any row is added. The project design requires city x cycle matched safety/non-safety observations; unsupported one-sided rows remain acquisition leads, not analytic observations.

---

## Source facts used

StateReference says its Department of Labor Relations Contracts collection contains **3,594 items / 3,594 documents** and describes the collection as union contracts between labor and municipalities/other organizations. It states that municipalities and other organizations submit CBAs to DLR, which makes them public through DLR Public Information Search; StateReference downloaded those contracts and makes them available in its database.

Collection page: <https://www.statereference.com/pages/dlr_contracts>

Important StateReference pattern visible on item pages:

- record title, e.g. `Woburn Police Patrol Assoc. 7-1-18 to 6-30-21 (Woburn, City of)`;
- document attachment;
- usually both `Original` and `OCR` links;
- original-source instructions, e.g. enter the employer name in DLR Public Information Search.

This makes StateReference useful as a **discovery and staging source**, but DLR is still the original public source route.

---

## Search method

I used targeted StateReference/web searches rather than broad crawling:

- `site:statereference.com/items/dlr_contracts "Police" "7-1-21"`
- `site:statereference.com/items/dlr_contracts "Firefighters" "7-1-20"`
- `site:statereference.com/items/dlr_contracts "AFSCME" "7-1-20"`
- municipality-specific searches around promising results: Georgetown, Seekonk, Peabody, Hanover, Reading, Marlborough, Lexington, Northbridge, Danvers, Springfield, Woburn, Manchester, Great Barrington, Ipswich, Millis, Hamilton, Gloucester, Newburyport, Littleton, Boxford.

I did **not** attempt to exhaust all 3,594 records. The goal was to produce a high-yield seed list for Codex verification.

---

## Priority matched-pair candidates

### Tier 1 - strongest first-pass candidates

| Rank | Municipality | Safety / safety-adjacent lead | Non-safety lead | Cycle alignment | StateReference links | Why prioritize | Caveats |
|---:|---|---|---|---|---|---|---|
| 1 | Georgetown | `ASCME, Local 939 (Police Command Staff) 7-1-20 to 6-30-23 (Georgetown, Town of)` | `AFSCME, Local 939 (DPW, Clerical) 7-1-20 to 6-30-23`; also school custodians 2020-2023 | Exact 2020-2023 match | Police command: <https://www.statereference.com/items/dlr_contracts/20210818_ascme_local_939_police_command_staff_7_1_20_to_6_30_23_georgetown_town_of> ; DPW/clerical: <https://www.statereference.com/items/dlr_contracts/20210709_afscme_local_939_dpw_clerical_7_1_20_to_6_30_23_georgetown_town_of> ; custodians: <https://www.statereference.com/items/dlr_contracts/20200716_afscme_local_939_custodians_7_1_20_to_6_30_23_georgetown_school_committee> | Cleanest StateReference candidate found: same town, same dates, safety-adjacent police command and non-safety DPW/clerical. | Need verify whether `Police Command Staff` should be coded `police` under repo schema despite `ASCME/AFSCME` typo. Need confirm document is full CBA vs MOA. |
| 2 | Seekonk | `Fraternal Order of Police MCOP Local 215 7-1-19 to 6-30-22 (Seekonk, Town of)` | `U.S.W. Local 9517-10 (Clerical Unit) 7-1-20 to 6-30-22`; `AFSCME Local 1701 Admin. Secretaries 7-1-18 to 6-30-21` | Good overlap: 2019-2022 police with 2020-2022 clerical and 2018-2021 school admin | Police: <https://www.statereference.com/items/dlr_contracts/20220223_fraternal_order_of_police_mcop_local_215_7_1_19_to_6_30_22_seekonk_town_of> ; clerical: <https://www.statereference.com/items/dlr_contracts/20220223_u_s_w_local_9517_10_clerical_unit_7_1_20_to_6_30_22_seekonk_town_of> ; school admin: <https://www.statereference.com/items/dlr_contracts/20181217_afscme_local_1701_admin_secretaries_7_1_18_to_6_30_21_seekonk_school_committee> | Strong city x cycle overlap and multiple non-safety options. | Need verify same municipality/employer relation for town vs school committee; still likely usable because project allows school/teacher comparators if consistent. |
| 3 | Hanover | `Hanover Firefighters Local 2726 7-1-20 to 6-30-23 (Hanover, Town of)` | `AFSCME, Local 1348 (Service Employees) 7-1-21 to 6-30-23 (Hanover School Committee)` | Overlap 2021-2023 | Fire: <https://www.statereference.com/items/dlr_contracts/20200928_hanover_firefighters_local_2726_7_1_20_to_6_30_23_hanover_town_of> ; school service: <https://www.statereference.com/items/dlr_contracts/20210514_afscme_local_1348_service_employees_7_1_21_to_6_30_23_hanover_school_committee> | Safety/fire plus non-safety service employees in a tight overlap window. | Need verify occupation_class for school service employees; likely `other`, `clerical_admin`, or `public_works` depending recognition clause. |
| 4 | Peabody | `Peabody Police Benevolent Assoc. 7-1-18 to 6-30-21` / older long police record | `AFSCME and Town of Peabody 7-1-2021 to 6-30-2022`; `Peabody School Committee AFSCME MOA` | Some overlap/seam around 2021; may require additional query for cleaner match | Police 2018-2021-ish: <https://www.statereference.com/items/dlr_contracts/20210422_peabody_police_benevolent_assoc_7_1_8_to_6_30_21_peabody_city_of> ; AFSCME 2021-2022: <https://www.statereference.com/items/dlr_contracts/20221003_afscme_and_town_of_peabody_7_1_2021_to_6_30_2022_peabody_city_of> | Larger municipality; likely has multiple records. | Title typo `7-1-8` may mean 2018 or 2008; entity/date must be verified from document. |
| 5 | Reading | Need safety counterpart | `AFSCME Local 1703 DPW 7-1-21 to 6-30-24`; `AFSCME Local 1703 DPW Supervisors 7-1-21 to 6-30-24` | Non-safety side exact 2021-2024 | DPW: <https://www.statereference.com/items/dlr_contracts/20220126_afscme_local_1703_dpw_7_1_21_to_6_30_24_reading_town_of> ; supervisors: <https://www.statereference.com/items/dlr_contracts/20211019_afscme_local_1703_dpw_suprvisors_7_1_21_to_6_30_24_reading_town_of> | If a police/fire 2021-2024 record exists, Reading could be a clean pair. | Currently single-sided; search DLR/StateReference for Reading police/fire before ingestion. |

### Tier 2 - good one-sided or partial candidates

| Municipality | Lead(s) found | Source links | Why useful | Caveat / next check |
|---|---|---|---|---|
| Marlborough | Police Patrol Officer NEPBA 2021-2024 | <https://www.statereference.com/items/dlr_contracts/20220110_marlborough_police_patrol_officer_nepba_7_1_21_to_6_30_24_marlborough_city_of> | Strong safety seed in a city; cycle 2021-2024. | Need AFSCME/clerical/DPW/teacher counterpart. Search employer `Marlborough, City of` and school committee. |
| Lexington | AFSCME 2022-2025; AFSCME public safety dispatchers 2018-2021 | AFSCME: <https://www.statereference.com/items/dlr_contracts/20221003_afscme_and_town_of_lexington_7_1_22_to_6_30_25_lexington_town_of> ; dispatchers: <https://www.statereference.com/items/dlr_contracts/20190107_afscme_public_safety_dispatchers_7_1_18_to_6_30_21_lexington_town_of> | Good non-safety/adjacent records; Lexington likely has public labor docs elsewhere too. | Dispatchers are not police/fire under schema; need true police/fire safety row. |
| Northbridge | Police Association Local 129 2021-2024 | Search page result in Aug. 2021 StateReference month page: <https://www.statereference.com/items?collection=dlr_contracts&date_from=2021-08-01&date_to=2021-08-31&query=&sort=oldest_first> | Good safety seed. | Need non-safety counterpart. |
| Danvers | Multiple AFSCME school units 2021-2024; town AFSCME Unit D 2020-2021 | StateReference Aug. 2021 page lists cafeteria workers, teacher aides, school admin assistants; town AFSCME Unit D: <https://www.statereference.com/items/dlr_contracts/20201020_afscme_local_1098_unit_d_7_1_20_to_6_30_21_danvers_town_of> | Strong non-safety cluster. | Need police/fire match; current search did not surface it. |
| Springfield | AFSCME Local 3065 2021-2024 | <https://www.statereference.com/items/dlr_contracts/20220126_afscme_local_3065_7_1_21_to_6_30_24_springfield_city_of> | Large city, likely useful if safety contracts are available elsewhere. | The StateReference item is a `.docx`, not PDF; ingestion path must handle docx or convert safely. Need safety match. |
| Woburn | Police Patrol Assoc. 2018-2021 | <https://www.statereference.com/items/dlr_contracts/20200820_woburn_police_patrol_assoc_7_1_18_to_6_30_21_woburn_city_of> | Good safety seed. | Need non-safety match. |
| Manchester | AFSCME DPW 2017-2020; AFSCME clerical MOA 2020-2023 | DPW: <https://www.statereference.com/items/dlr_contracts/20170822_afscme_local_687_dpw_7_1_17_to_6_30_20_manchester_town_of> ; clerical MOA: <https://www.statereference.com/items/dlr_contracts/20200810_moa_afscme_local_687_clerical_7_1_20_to_6_30_23_manchester_town_of> | Good non-safety sequence. | Need safety counterpart; likely `Manchester-by-the-Sea` naming may complicate search. |
| Great Barrington | AFSCME DPW 2014-2017 and 2020-2023 | 2020-2023: <https://www.statereference.com/items/dlr_contracts/20201014_afscme_local_204_dpw_7_1_20_to_6_30_23_great_barrington_town_of> ; 2014-2017: <https://www.statereference.com/items/dlr_contracts/20160412_afscme_local_204_dpw_7_1_14_to_6_30_17_great_barrington_town_of> | Non-safety side available over multiple cycles. | Need police/fire counterpart. |
| Ipswich | Schools clerical 2021-2024 | <https://www.statereference.com/items/dlr_contracts/20230330_town_of_ipswich_7_1_2021_and_6_30_2024_schools_clerical_ipswich_town_of> | Useful non-safety lead. | Need safety match. |
| Millis | School food services 2020-2023; operations 2022-2025 | Food services: <https://www.statereference.com/items/dlr_contracts/20210222_millis_association_of_food_services_7_1_20_to_6_30_23_millis_school_committee> ; operations: <https://www.statereference.com/items/dlr_contracts/20230331_millis_s_c_and_millis_teachers_assoc_operations_9_1_2022_to_8_31_2025_millis_town_of> | School non-safety cluster. | Need safety match; school employer may be less clean if no town-side record. |
| Hamilton | AFSCME DPW 2021-2024 | <https://www.statereference.com/items/dlr_contracts/20210823_afscme_local_2905_dpw_7_1_21_to_6_30_24_hamilton_town_of> | Good non-safety lead. | Need safety match; may pair with Wenham/Hamilton school district only if city logic is carefully handled. |
| Gloucester | City AFSCME 2022-2025 | <https://www.statereference.com/items/dlr_contracts/20230324_city_of_gloucester_afscme_7_1_2022_to_6_30_2025_gloucester_city_of> | Large municipality and direct non-safety lead. | Need safety match. |
| Newburyport | Schools AFSCME 2022-2025 | <https://www.statereference.com/items/dlr_contracts/20230426_afscme_city_of_newburyport_schools_7_1_2022_to_6_30_2025_newburyport_city_of> | Good school non-safety lead. | Need police/fire match. |
| Littleton | AFSCME 2022-2024 | <https://www.statereference.com/items/dlr_contracts/20221003_afscme_and_town_of_littleton_7_1_2022_to_6_30_2024_littleton_town_of> | Good town non-safety lead. | Need police/fire match. |
| Boxford | AFSCME clerical/library 2021-2023 | <https://www.statereference.com/items/dlr_contracts/20220606_afscme_local_939_clerical_library_employees_7_1_21_to_6_30_23_boxford_town_of> | Good non-safety lead. | Need police/fire match. |

---

## Do-not-ingest-yet warnings

1. **Public safety dispatchers are not police/fire** under the repo schema unless the team explicitly adds new occupation logic. Current controlled vocabulary derives `safety_flag = 1` only for `police` or `fire`.
2. **Police command staff** likely counts as `occupation_class = police`, but Codex must verify the first page/recognition clause before accepting it.
3. **School committee records** can be valid non-safety comparators only if the project consistently treats school-side units as non-safety comparators. Teachers were previously judged conditionally acceptable; custodians, cafeteria, administrative assistants, and service units may be acceptable if consistently coded.
4. **MOAs vs full CBAs:** a wage MOA is valid for wage outcomes but may lack mechanism clauses. That is analytically useful but should not be mistaken for a full mechanism-rich CBA.
5. **Source titles can contain typos.** Examples found include `ASCME`, `Wilmimgton`, and date typos such as `7-1-8`. Always verify from document text.

---

## Recommended Phase 1 ingestion pilot

If using StateReference first, I recommend Codex verify and, if safe, ingest **at most the following 3-6 documents** in the first pilot.

### Pilot Set A - Georgetown exact-cycle pair

1. Georgetown Police Command Staff, 2020-2023  
   <https://www.statereference.com/items/dlr_contracts/20210818_ascme_local_939_police_command_staff_7_1_20_to_6_30_23_georgetown_town_of>

2. Georgetown AFSCME DPW/Clerical, 2020-2023  
   <https://www.statereference.com/items/dlr_contracts/20210709_afscme_local_939_dpw_clerical_7_1_20_to_6_30_23_georgetown_town_of>

3. Georgetown School Committee AFSCME Custodians, 2020-2023  
   <https://www.statereference.com/items/dlr_contracts/20200716_afscme_local_939_custodians_7_1_20_to_6_30_23_georgetown_school_committee>

This would test: same municipality, same cycle, one safety/police-adjacent row and two non-safety rows.

### Pilot Set B - Seekonk overlap pair

4. Seekonk MCOP/FOP police, 2019-2022  
   <https://www.statereference.com/items/dlr_contracts/20220223_fraternal_order_of_police_mcop_local_215_7_1_19_to_6_30_22_seekonk_town_of>

5. Seekonk USW clerical, 2020-2022  
   <https://www.statereference.com/items/dlr_contracts/20220223_u_s_w_local_9517_10_clerical_unit_7_1_20_to_6_30_22_seekonk_town_of>

6. Seekonk School Committee AFSCME admin secretaries, 2018-2021  
   <https://www.statereference.com/items/dlr_contracts/20181217_afscme_local_1701_admin_secretaries_7_1_18_to_6_30_21_seekonk_school_committee>

Use B only if A passes smoothly or if Georgetown police command staff proves unsuitable.

---

## Narrow Codex prompt

Paste this after saving this memo into the repo as `docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md`.

```text
# Recommended launch
codex --profile heavy

You are working in the gabriel-wages repo. Read AGENTS.md first, then PROGRESS.md, docs/schema.md, docs/hypotheses.md, docs/acquisition/ma_public_records_availability_recon_2026-06-23.md if present, and docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md before editing anything.

Goal:
Run a narrow Phase 1 StateReference pilot using the seed memo. Verify a small number of public CBA/MOA candidates and ingest only if they pass entity/source/cycle/provenance checks. Do not broad-search Massachusetts.

Context:
- StateReference DLR Contracts appears to be the strongest public source for public CBA/MOA expansion.
- This task should focus on the memo's Tier 1 candidates, especially Georgetown and Seekonk.
- The project design requires city/town x cycle matched safety/non-safety observations.
- Existing repo rows must not be rewritten.
- GABRIEL v9 is not justified by this task unless at least one clean new matched pair is ingested and validated, and even then do not run it unless asked.

Hard boundaries:
- Do NOT scrape blindly.
- Do NOT broad-crawl StateReference.
- Do NOT bypass anti-bot, login, JavaScript, 403, or licensed-source barriers.
- Do NOT use Westlaw/Lexis/Bloomberg/Factiva/NewsBank.
- Do NOT run GABRIEL or create v9 output.
- Do NOT edit GABRIEL scoring code.
- Do NOT manually edit contracts.csv.
- Do NOT paste full documents into CSVs or markdown.
- If a source is uncertain, mark it `needs_manual_verification`.

Task A - Preserve and summarize the seed memo
1. Confirm `docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md` exists.
2. Add no substantive claims to it unless you are correcting obvious formatting/typos.
3. In your working notes, identify the top pilot set:
   - Georgetown exact-cycle set first.
   - Seekonk overlap set second if Georgetown fails or is too small.

Task B - Verify StateReference candidates manually/locally
For each candidate you attempt, open the StateReference item page and verify:
1. It is in the DLR Contracts collection.
2. The employer is a Massachusetts municipality/school committee, not another state or non-municipal employer.
3. The document attachment exists.
4. The cycle dates can be read from the title and then confirmed from the document itself after download.
5. The bargaining unit maps cleanly to the repo's `occupation_class`.
6. `source_type` is `cba` or `arbitration_award` or `factfinding`; for these seed candidates it should usually be `cba` or possibly wage `moa`.
7. Full document can be locally downloaded without bypassing access controls.

Task C - Pilot ingestion, maximum 6 documents
Try Pilot Set A first:
- Georgetown Police Command Staff 2020-2023
- Georgetown AFSCME DPW/Clerical 2020-2023
- Georgetown AFSCME Custodians 2020-2023

If those pass, ingest them and stop unless adding Seekonk is trivial and still within the 6-document cap.

If Georgetown safety classification fails, try Pilot Set B:
- Seekonk police 2019-2022
- Seekonk clerical 2020-2022
- Seekonk school admin secretaries 2018-2021

Use the established inbox/process pipeline:
1. Stage files under an appropriate inbox public-download folder.
2. Add manifest rows with stable obs_ids.
3. Use `retrieval_method = public_download`.
4. Use `source_corpus = causal`.
5. Use `source_url_or_cite` as the StateReference item URL plus, where available, DLR Public Information Search route in notes.
6. Do not hand-edit contracts.csv.
7. Run `python ingest/process_inbox.py`.

If file download or verification fails, do not force ingestion. Instead create/update a queue note and mark status.

Task D - Validation
After any ingestion:
- python scripts/validate.py
- python ingest/audit_coverage.py
- python ingest/test_pipeline.py

If no ingestion occurs:
- python scripts/validate.py
- python ingest/audit_coverage.py

Task E - Documentation
Create or update:
- `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md`

Include:
- what was attempted;
- what passed first-page/entity checks;
- what was ingested;
- what failed and why;
- next 10 StateReference candidates from the seed memo;
- warnings about police command staff, dispatchers, school committee comparators, title typos, and MOA-vs-CBA classification.

Task F - PROGRESS.md
Append a concise PROGRESS.md entry at the top using the existing template.

Include:
- Did
- Decisions and why
- Surprises/breakage
- Corpus snapshot from audit_coverage.py
- Next steps

Next steps should distinguish:
1. more public StateReference candidates ready for targeted verification;
2. candidates needing manual verification;
3. PRR-only targets that should remain deferred;
4. whether v9 GABRIEL remains premature.

Task G - Final report
Report:
1. Files created/edited.
2. Documents downloaded/staged.
3. Rows ingested.
4. Validation/test/audit results.
5. Whether a new healthy matched pair was created.
6. Top 5 next StateReference candidates.
7. Confirmation that GABRIEL was not run.
8. Git status.

Do not commit unless explicitly asked.
```

---

## Recommended next 10 StateReference candidates after the first pilot

1. **Hanover:** fire 2020-2023 + school service 2021-2023.
2. **Peabody:** police 2018-2021 + AFSCME 2021-2022; search for cleaner non-safety overlap.
3. **Reading:** DPW 2021-2024 + search for Reading police/fire 2021-2024.
4. **Marlborough:** police 2021-2024 + search for AFSCME/clerical/DPW counterpart.
5. **Danvers:** school admin/cafeteria/teacher aides 2021-2024 + search for police/fire.
6. **Lexington:** AFSCME 2022-2025 + search for police/fire 2022-2025.
7. **Springfield:** AFSCME 2021-2024 + search for public safety.
8. **Woburn:** police 2018-2021 + search for non-safety counterpart.
9. **Manchester:** DPW/clerical sequence + search for safety.
10. **Great Barrington:** DPW sequence + search for safety.

---

## Final note

This Phase 1 public-source route will likely build a much larger **CBA/MOA panel** quickly. It will not, by itself, solve the non-safety factfinding/interest-arbitration gap. The empirical program should therefore separate:

- **Phase 1 public CBA/MOA matched panel**: scalable, public, cheap, strong for wage outcomes and basic mechanism language.
- **Phase 2 targeted PRR award/factfinding panel**: smaller, more costly, necessary for the cleanest H1 award-vs-award comparison.
