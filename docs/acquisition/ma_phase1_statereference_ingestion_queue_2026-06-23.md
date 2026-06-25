# MA StateReference Phase 1 Ingestion Queue

**Date:** 2026-06-23
**Scope:** narrow StateReference DLR Contracts pilot seeded by `ma_statereference_phase1_seed_2026-06-23.md`.

## Attempted

Georgetown was attempted first, per the seed memo and current acquisition constraints. I opened the three StateReference item pages, confirmed each page is in the Massachusetts Department of Labor Relations Contracts collection, and downloaded the public attachments without bypassing access controls.

Downloaded locally:

| Candidate | StateReference status | Local files | Entity and cycle check | Decision |
|---|---|---|---|---|
| Georgetown Police Command Staff 2020-2023 | DLR Contracts collection; employer route `Georgetown, Town of` | `inbox/foia/ma_georgetown_police_command_staff_2020_2023.pdf`; `inbox/foia/ma_georgetown_police_command_staff_2020_2023_ocr.pdf` | OCR text confirms Town of Georgetown, police command staff unit including Lieutenant, Sergeant, and Detective Sergeant, term 2020-07-01 to 2023-06-30 | Ingested |
| Georgetown AFSCME DPW/Clerical 2020-2023 | DLR Contracts collection; employer route `Georgetown, Town of` | `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023.pdf`; `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023_ocr.pdf` | OCR text confirms Town of Georgetown and 2020-2023 term, but recognition combines Fire or Police Signal Operators, highway/DPW titles, and clerical/admin titles | Not ingested; `needs_manual_verification` for occupation coding |
| Georgetown School Committee AFSCME Custodians 2020-2023 | DLR Contracts collection; employer route `Georgetown School Committee` | `inbox/foia/ma_georgetown_afscme_custodians_2020_2023.pdf`; `inbox/foia/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf` | OCR text confirms Georgetown School Department custodians, matrons, and maintenance employees, term 2020-07-01 to 2023-06-30 | Ingested |

The original StateReference PDFs are image-only for these Georgetown records. The StateReference OCR PDFs were downloaded and used for pipeline text extraction. The original PDFs remain staged locally for provenance review.

## Ingested

Rows added through `python ingest/process_inbox.py`:

| obs_id | city | occupation_class | source_type | retrieval_method | full_text_path |
|---|---|---|---|---|---|
| `ma_georgetown_police_2020` | Georgetown, MA | `police` | `cba` | `public_download` | `corpus/ma_georgetown/ma_georgetown_police_command_staff_2020_2023_ocr.pdf` |
| `ma_georgetown_other_2020` | Georgetown, MA | `other` | `cba` | `public_download` | `corpus/ma_georgetown/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf` |

The Georgetown pair creates one new same-city, same-cycle safety/non-safety matched pair for 2020-2023. The school custodians row is coded `other` because the current controlled vocabulary has no custodial or school maintenance class.

## Failed or Deferred

- Georgetown DPW/clerical was verified as public and locally staged but not ingested because the recognition clause is not a clean single occupation class. It may be usable later if the project adopts a stable rule for mixed municipal units containing signal operators plus DPW and clerical titles.
- Seekonk was not attempted in this pass. Georgetown succeeded cleanly enough to create a healthy matched pair, and the seed prompt said to stop unless adding Seekonk was trivial within the cap.
- No PRR-only targets were pursued, drafted, or submitted.
- GABRIEL was not run, and no v9 output was created.

## Staged but not ingested PDFs

The repo already has a one-off `DISCARD_` prefix for a confirmed wrong-jurisdiction file, but there is no broader scratch/review folder convention for StateReference staging. These PDFs were therefore left in `inbox/foia/` and are documented here only.

| filename | municipality | candidate unit | reason not ingested | recommended disposition | manifest row | future ingestion? |
|---|---|---|---|---|---|---|
| `ma_hanover_firefighters_local_2726_2020_2023.pdf` | Hanover | Professional Firefighters of Hanover Local 2726 | Valid Massachusetts safety-side fire agreement, but the staged counterpart in this batch is a New Hampshire school-district contract, so no same-municipality matched pair exists from the batch. | `keep_for_manual_review` | no | yes, if a clean Hanover MA non-safety comparator is later verified |
| `ma_hanover_firefighters_local_2726_2020_2023_ocr.pdf` | Hanover | Professional Firefighters of Hanover Local 2726 | Same reason as the original PDF; safety side is usable in principle, but the batch failed on the non-safety jurisdiction check. | `keep_for_manual_review` | no | yes, if a clean Hanover MA non-safety comparator is later verified |
| `ma_hanover_afscme_service_employees_2021_2023.pdf` | Hanover | Service Employees / Dresden School District / Hanover School District | Wrong jurisdiction for this Massachusetts corpus: the document is for the Dresden and Hanover School Districts in New Hampshire, not Hanover, Massachusetts. | `discard_after_confirmation` | no | no |
| `ma_hanover_afscme_service_employees_2021_2023_ocr.pdf` | Hanover | Service Employees / Dresden School District / Hanover School District | Wrong jurisdiction for this Massachusetts corpus: the OCR confirms the New Hampshire district employer. | `discard_after_confirmation` | no | no |
| `ma_peabody_police_benevolent_assoc_2018_2021.pdf` | Peabody | Peabody Police Benevolent Association | Police side looks clean, but the staged non-safety comparators from this batch are mixed or ambiguous, so no clean same-cycle matched pair was ready to ingest. | `keep_for_manual_review` | no | yes, if a clean Peabody non-safety comparator is later verified |
| `ma_peabody_afscme_local_364_moa_2018_2021.pdf` | Peabody | AFSCME Local 364 city-side MOA | The saved notes do not yet pin this file to a clean controlled occupation class, and the batch already failed to produce a clearly classifiable non-safety comparator. | `move_to_scratch_later` | no | needs manual verification before reuse |
| `ma_peabody_afscme_local_364_moa_2018_2021_ocr.pdf` | Peabody | AFSCME Local 364 city-side MOA | OCR confirms a Peabody city-side MOA, but not a clean occupation class from the saved notes; keep out of ingestion until entity/class verification is done manually. | `move_to_scratch_later` | no | needs manual verification before reuse |
| `ma_peabody_afscme_local_365_school_2018_2021.pdf` | Peabody | AFSCME Local 365 school non-teaching employees | Mixed school-side unit; OCR indicates all non-teaching employees except some excluded units, which is not a clean preferred occupation class. | `keep_for_manual_review` | no | maybe, only if the project later accepts a mixed `other` school comparator |
| `ma_peabody_afscme_local_365_school_2018_2021_ocr.pdf` | Peabody | AFSCME Local 365 school non-teaching employees | Same mixed-unit problem as the original PDF; not a clean `teacher`, `clerical_admin`, or `public_works` comparator. | `keep_for_manual_review` | no | maybe, only if the project later accepts a mixed `other` school comparator |

## Next 10 StateReference Candidates

1. Hanover: fire 2020-2023 plus school service employees 2021-2023.
2. Peabody: police 2018-2021 plus AFSCME 2021-2022; search for cleaner non-safety overlap.
3. Reading: DPW 2021-2024 plus targeted search for Reading police/fire 2021-2024.
4. Marlborough: police 2021-2024 plus targeted search for AFSCME, clerical, DPW, or school counterpart.
5. Danvers: school admin, cafeteria, and teacher aides 2021-2024 plus targeted police/fire search.
6. Lexington: AFSCME 2022-2025 plus targeted police/fire search; dispatchers are not a police/fire substitute.
7. Springfield: AFSCME 2021-2024 plus targeted public-safety search; note possible `.docx` handling issue.
8. Woburn: police 2018-2021 plus targeted non-safety counterpart search.
9. Manchester: DPW/clerical sequence plus targeted safety search, watching for Manchester-by-the-Sea naming.
10. Great Barrington: DPW sequence plus targeted safety search.

## Warnings

- Police command staff can be coded `police` only after recognition confirms sworn command positions. Georgetown passed this check.
- Public safety dispatchers and signal operators are not `police` or `fire` under the current schema.
- School committee comparators remain usable only if consistently treated as non-safety comparators. Georgetown custodians were coded `other`, not teacher or public works.
- StateReference item titles can contain typos, including union-name and date typos. Document text controls over title text.
- MOAs and full CBAs should not be conflated. The two Georgetown ingested records were treated as CBAs because the downloaded OCR text contains full agreements with recognition, grievance/arbitration, wages, no-strike, and duration provisions.

## This Wave

Attempted in priority order after Georgetown:

| Municipality | Safety target | Non-safety target | Cycle | StateReference/source route | Status | Occupation-class decision | Reason | Next action |
|---|---|---|---|---|---|---|---|---|
| Hanover | Hanover Firefighters Local 2726 | AFSCME Local 1348 service employees | 2020-2023 vs 2021-2023 | StateReference DLR item pages plus DLR Public Information Search routes | `not_matched` | fire / not ingested | The school-side agreement is for the Dresden and Hanover School Districts in New Hampshire, so it is not a clean same-Massachusetts-municipality comparator. | Defer. Do not ingest under this MA corpus. |
| Peabody | Peabody Police Benevolent Assn. / Assn. | AFSCME Local 364 school employees; AFSCME Local 365 school employees | 2018-2021 | StateReference DLR item pages plus DLR Public Information Search routes | `deferred_ambiguous` | police is clean; non-safety side remains ambiguous | The police contract is clean, but the available non-safety school-side record is a mixed school-unit CBA spanning cafeteria, clerks, and transportation. It is valid public text, but not a clean occupation-class comparator. | Hold for possible manual review; do not ingest unless the project accepts a mixed `other` school comparator. |
| Reading | AFSCME Local 1703 DPW | Search for police/fire counterpart | 2021-2024 | StateReference targeted item pages plus DLR original route | `not_matched` | not ingested | Clean DPW record exists, but targeted Reading police/fire searches did not surface a same-cycle public contract for the town. | Continue only if a town police/fire contract is found later. |
| Marlborough | Marlborough police patrol officer | Search for AFSCME/clerical/DPW/school counterpart | 2021-2024 | StateReference item page plus targeted search pages | `not_matched` | police clean; no comparator | Clean police contract exists, but no same-cycle non-safety counterpart surfaced in the targeted search. | Continue only if a same-cycle town AFSCME/clerical/DPW or school comparator is found later. |
| Danvers | Danvers police/fire search | AFSCME Unit A/C/D/E, dispatchers | 2020-2024 | StateReference targeted search pages | `not_matched` | not ingested | The targeted search surfaced AFSCME units and dispatchers, but no police/fire contract. Dispatchers are not a police/fire substitute under the schema. | Continue only if a town police/fire contract is found later. |

## Classification Lessons

Where a clean `clerical_admin`, `public_works`, or `teacher` comparator exists, prefer it over `other`. `other` remains acceptable as a fallback, but the next batch should avoid using it unless the recognition clause is genuinely clean and no better category fits. The Peabody school-side record is the current borderline case: public and same-city, but too mixed to promote as a preferred comparator without relaxing that standard.
