# National Batch 01 Massachusetts Live Scout Rerun Review

Date: 2026-07-20
Run ID: `ma_2026-07-20_150025`
Scope: the authorized eight-municipality Massachusetts slice only
Status: unverified scout-stage output; not source verification, ingestion, codification, or claim evidence

## Plain-English result

The locked Massachusetts rerun completed successfully. It sent one minimal, web-search-enabled GABRIEL source-discovery prompt for each of the eight authorized municipalities—Somerville, Newton, Boston, Worcester, Arlington, Georgetown, Franklin, and Seekonk—using the full-context national input CSV. Connectivity held for all eight calls: every returned a nonempty, parseable response and there were no connection-error rows, no parser failures, and no retry.

The run returned 24 staged candidates. The most useful unverified leads are Boston's city-hosted fire CBA, the two Arlington police interest-arbitration awards, Franklin's five city-hosted police/fire/DPW/library agreements, and Seekonk's city-hosted repeat-cycle police/fire/library agreements. Somerville and Newton both surfaced ordinary non-safety leads, but those leads remain weak until direct source review resolves inaccessible, partial, or memorandum-only material. Georgetown surfaced authoritative minutes showing firefighter agreements/renewal activity, but not the actual fire agreement.

Nothing in this output has been verified, ingested, codified, or treated as claim-supporting. No URL was opened or verified beyond the scout's own returned material.

## Authorized run and completion

```bash
python scripts/gabriel_state_source_scout.py \
  --state MA \
  --municipalities-csv docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 8 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live
```

Before launch, the input resolved to exactly eight MA rows in the locked order: Somerville, Newton, Boston, Worcester, Arlington, Georgetown, Franklin, and Seekonk. The run metadata records 8 requested municipalities, 8 GABRIEL-successful rows, 8 nonempty responses, 8 parseable outputs, 0 failed parses, and 24 candidate rows.

| Measure | Result |
|---|---:|
| Total cost | `$0.0895092` |
| Input / reasoning / output tokens | 236,971 / 12,919 / 20,773 |
| Mean model-response time | 33.04 seconds |
| Candidate rows | 24 |
| Qualifying / context-only / insufficient stages | 14 / 4 / 6 |
| Connection errors | 0 |
| Parser failures | 0 |

## Candidate counts

| Municipality | Police | Fire | Ordinary non-safety | Total |
|---|---:|---:|---:|---:|
| Somerville | 0 | 0 | 2 | 2 |
| Newton | 0 | 0 | 2 | 2 |
| Boston | 0 | 2 | 0 | 2 |
| Worcester | 2 | 0 | 1 | 3 |
| Arlington | 2 | 0 | 0 | 2 |
| Georgetown | 0 | 2 | 0 | 2 |
| Franklin | 2 | 1 | 2 | 5 |
| Seekonk | 2 | 2 | 2 | 6 |

## Municipality review

- **Somerville:** Two City/Legistar SMEA Unit B/D memorandum leads point to ordinary civilian/clerical or related municipal units. Both are context-only, inaccessible in the scout, and tagged possible wrong-employer risk. They are promising locators for the missing comparator but do not establish an ordinary non-safety CBA or overlap yet.
- **Newton:** Two ordinary non-safety leads surfaced: Teamsters Local 25 FY20–24 (DPW/PRC/Public Buildings) and AFSCME 3092/3092B FY20–24 (inspectors/city-hall associates). The first was inaccessible and the second partial; both need direct confirmation of City of Newton parties, unit scope, binding status, and cycle overlap. These are leads, not confirmed comparators.
- **Boston:** The scout found a city-hosted IAFF Local 718 fire CBA for 2014–2017 and a 2021–2024 IAFF Local 718 MOA. This answers the fire-source search positively at the scout stage; the base CBA is the stronger lead, while the MOA must be screened for amendment-only limitations and pairing overlap.
- **Worcester:** No police base CBA was found. The police results are a 2021 Local 504 JLMC arbitration decision and a 2017–2020 Local 911 MOA/index lead; each is weaker than the requested base agreement. A Local 495 non-safety CBA lead is city-hosted but appears to cover 2010–2013, outside the requested window, so it is context/locator material rather than a usable in-window base comparator.
- **Arlington:** Two Massachusetts JLMC police interest-arbitration awards surfaced, dated 2021 and 2024. They are the requested formal impasse/arbitration material and are promising, but require direct confirmation of the Town of Arlington employer, unit, award coverage, and exact terms before any use.
- **Georgetown:** The scout found only 2016 and 2024 Board of Selectmen minutes referring to firefighter CBA ratification/renewal. These are useful municipal context showing that a fire agreement existed or was renewed, but neither is the fire agreement itself. Treat as context-only, not a positive CBA find.
- **Franklin:** Five strong city-hosted, full-document leads surfaced for the 2022–2025 cycle: police association, police sergeants, firefighters, DPW (AFSCME 1298), and library staff. The police/fire/DPW/library set is the clearest repeat-cycle and matched-comparison discovery result in this slice, but all remain unverified until employer, unit, dates, signatures, and wage sections are directly checked.
- **Seekonk:** Six repeat-cycle leads surfaced: police 2019–2022 and 2022–2025, fire 2016–2019 and 2022–2025, and library 2014–2017 and 2020–2023. The 2022–2025 police/fire and 2020–2023 library documents are stronger full-document leads. The older police/library leads have unclear or inaccessible content and need direct review. This is a useful repeat-cycle queue, not verified cycle continuity.

## Leakage and failure review

- **Wrong-employer leakage:** No candidate was explicitly labeled high wrong-employer risk or obviously named a different government. Twelve rows carry `possible` risk, chiefly because inaccessible/partial documents or town-name ambiguity prevent confirmation. This is uncertainty to resolve, not evidence that those rows are usable.
- **Wrong-unit leakage:** No returned row was labeled `unclear` or `unknown` unit type; all 24 use the requested police, fire, or non-safety labels. Several require direct confirmation of unit scope (for example, Somerville Units B/D, Newton Teamsters/AFSCME, and Seekonk library) before they can be treated as correctly classified.
- **Safety-as-non-safety leakage:** None observed. Every `non_safety` row names a civilian-facing municipal unit (Somerville municipal employees, Newton Teamsters/AFSCME, Worcester Local 495, Franklin DPW/library, or Seekonk library), rather than police/fire material. This remains a scout label pending verification.
- **Context-only leakage:** Six rows are correctly marked context-only: both Somerville leads, Worcester Local 911 MOA/index, both Georgetown minutes, and Seekonk's older inaccessible library link. The review preserves them as trace material and does not count them as agreements.
- **Parser failures:** None. `failed_parses.csv` contains only its header, and the metadata reports zero failures in every failure category.

## Verification queue—still unverified

1. **High priority:** Franklin 2022–2025 police/fire/DPW/library and Seekonk 2022–2025 police/fire plus 2020–2023 library. Open the city/town-hosted documents and establish exact party, unit, effective/expiration dates, complete wage-setting content, and overlap before considering any future ingestion.
2. **High priority:** Boston's 2014–2017 IAFF Local 718 base CBA. Confirm full document identity and its match to the existing Boston comparison cycle.
3. **Medium priority:** Arlington's two JLMC police awards. Confirm the town/unit/term and whether each award contains wage-setting terms needed for the impasse mechanism question.
4. **Medium priority:** Newton's AFSCME FY20–24 and Teamsters FY20–24 leads; confirm municipal civilian coverage and binding document status. Then seek a full, overlapping ordinary non-safety agreement if these are only memoranda.
5. **Trace-only priority:** Somerville Legistar MOA attachments, Georgetown minutes, Worcester's police/non-safety leads, and Seekonk older/unclear files. They may guide a targeted official-record search but cannot be promoted as documents on their current evidence.

## Artifacts

- Run directory: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-20/`
- [Staged candidate review CSV](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/national_batch01_ma_live_scout_candidates_2026-07-20.csv)
- [Run metadata](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-20/run_metadata.json)
- [Cost summary](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-20/cost_summary.json)

The next step is controlled direct-source verification of this queue, starting with the high-priority full-document leads. Do not open another live state slice until this Massachusetts output has been reviewed and resolved.
