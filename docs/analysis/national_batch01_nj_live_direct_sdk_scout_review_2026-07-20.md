# National Batch 01 New Jersey Direct-SDK Live Scout Review

Date: 2026-07-20

Stage: live source-scout output only. All candidate rows are `unverified_scout_candidate`; no URL was independently opened or verified, no source was ingested, no document was codified, no canonical coverage changed, and no candidate is claim-supporting evidence.

## Plain-English result

The mandatory direct-SDK smoke preflight succeeded, so the locked New Jersey scout was allowed to run. Connectivity then held for all three municipal prompts. Newark, Jersey City, and Camden each returned a nonempty model response with a response ID and positive output tokens. All three responses parsed, producing eight unverified candidate rows and zero parser failures. No retry was needed or attempted.

The scout materially improved the queue but did not by itself close every design gap. Newark returned one fire-related 2017-2023 Legistar metadata lead that overlaps the existing 2020-2023 police/non-safety window, but the model itself classified it as context only and did not expose an inspected executed CBA. Jersey City returned a candidate-stage police/fire/ordinary-civilian successor set with an apparent shared 2021-2022 window, although the fire dates and binding/completeness status need direct verification. Camden returned strong-looking city-hosted fire and civilian leads plus a fire arbitration/consent-award lead, but no police candidate, so it did not produce a police/fire/non-safety triad.

## Mandatory direct-SDK smoke preflight

The preflight used exactly one synthetic prompt, `Reply with OK.`, with `gpt-5.4-nano`, base `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`, effective resource `/responses`, no tools or web search, one parallel request, zero retries, and a 30-second timeout.

It passed every release gate:

- response text: `OK`;
- response ID: present;
- `Connection error.`: absent;
- output tokens: 5;
- input/reasoning tokens: 10 / 0;
- `success=true` and `model_response_succeeded=true`;
- request count: 1.

Artifacts are under `tmp/direct_sdk_scout_backend_preflight/NJ/national_batch01_nj_2026-07-20/`. No credential value or `.env` content was logged.

## Locked live command

The input was checked immediately before the call and resolved to exactly three rows, in this order: Newark (`nj_newark`), Jersey City (`nj_jersey`), and Camden (`nj_camden`). All rows were NJ rows. The scout used the full-context CSV.

```bash
python scripts/gabriel_state_source_scout.py \
  --state NJ \
  --municipalities-csv docs/analysis/national_batch01_nj_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/NJ/national_batch01_nj_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 3 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

No GABRIEL wrapper call ran. The runner also contained a stop gate that would have suppressed any remaining prompt after two consecutive connection errors with no response ID, output tokens, or response text. That stop condition did not trigger.

## Connectivity, parsing, and usage

| Municipality | Response | Response ID | Input tokens | Reasoning tokens | Output tokens | Candidates | Parse failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Newark | Nonempty | Present | 31,271 | 1,608 | 2,190 | 1 | No |
| Jersey City | Nonempty | Present | 35,638 | 1,226 | 2,770 | 3 | No |
| Camden | Nonempty | Present | 30,552 | 1,057 | 2,704 | 4 | No |
| **Total** | **3/3** | **3/3** | **97,461** | **3,891** | **7,664** | **8** | **0** |

Average successful model-request time was 35.277 seconds. The Responses API exposed usage but not billed dollar cost, so `cost_available=false` and no dollar amount is reported or inferred.

## Candidate counts

| Municipality | Police | Fire | Non-safety | Total |
|---|---:|---:|---:|---:|
| Newark | 0 | 1 | 0 | 1 |
| Jersey City | 1 | 1 | 1 | 3 |
| Camden | 0 | 3 | 1 | 4 |
| **Total** | **1** | **5** | **2** | **8** |

Seven rows are model-labeled `qualifying_candidate`; the Newark row is `context_only_candidate`. Five are labeled full documents, two partial documents, and one index/landing page. These are model assertions awaiting verification, not established source facts.

## Municipality findings

### Newark

The scout returned one IAFF Local 1860 fire-related Legistar record with a stated January 2017-December 2023 period. That period would overlap the shared 2020-2023 portion of Newark's existing police 2018-2023 and ordinary non-safety 2020-2023 rows.

This does **not** yet supply a qualifying current full fire leg. The row is model-labeled `context_only_candidate`, `index_or_landing_page`, and `context_only_flag=yes`; the model says the executed agreement and binding wage terms were not inspected. The same union/cycle was already mentioned in local planning context, so this is a more specific locator for a previously surfaced trace rather than a clean new full-document result. Verification must locate any attachment/full executed instrument and establish the exact fire unit, operative dates, binding wage terms, and whether the source is distinct from prior planning material.

### Jersey City

Jersey City produced one candidate in each requested unit class:

- police: a model-described POBA successor MOA for 2021-2024, hosted on a third-party PDF domain;
- fire: a city-hosted Local 1066 MOA/resolution context extending or modifying an agreement through December 2024, but with the full start/end term unclear in the returned description;
- ordinary non-safety: a city-hosted Local 246 MOA for 2019-2022.

At scout stage, these form a plausible current-cycle successor set with an apparent mutual 2021-2022 overlap, replacing rather than simply repeating the known 2009-2015 vintage set. The result is still conditional: the police source needs official provenance/execution and sworn-unit confirmation; the fire source needs binding/executed status, complete operative dates, and full-versus-partial review; and Local 246 needs confirmation as an ordinary municipal civilian unit with wage-setting terms. The Local 246 row correctly carries `duplicate_risk=possible` because related Local 245/246 material was known from 2015, although the returned cycle is different.

### Camden

Camden produced:

- a city-hosted model-described IAFF Local 788 fire CBA for 2017-2020;
- a city-hosted model-described IAFF Local 788 fire CBA for 2021-2024;
- a city-hosted model-described CWA Local 1014 non-supervisory agreement for 2022-2025;
- a city-hosted model-described IAFF Local 2578 consent arbitration award for a 2021-2024 successor term.

The 2021-2024 fire lead and 2022-2025 civilian lead would overlap in 2022-2024 if their model-reported dates and unit identities are verified. Camden did **not** return a police source, so it did not produce the requested mutually overlapping police/fire/ordinary non-safety set. It did produce a potentially useful same-period mechanism lead through the consent award. Verification must reconcile the award's Local 2578 with the Local 788 fire agreements and determine whether it represents a distinct unit, a related instrument, or a unit-label problem.

## Leakage and labeling review

### Duplicate leakage

No row is labeled `exact_known_source`, and none of the three exact canonical Newark URLs supplied to the prompt was returned. Six rows are labeled `duplicate_risk=none`; two are `possible` (Jersey City Local 246 and the Camden consent award).

One softer known-source issue is visible: Newark returned the IAFF Local 1860 2017-2023 planning trace already described in the prompt's known-source context. It was appropriately returned as context rather than as a qualifying full agreement, but its `duplicate_risk=none` label understates that it was previously surfaced locally. This is planning-trace repetition, not exact canonical-source leakage.

### Wrong-employer leakage

No clear wrong-employer substitution is visible in the returned fields: every employer is labeled City of Newark, City of Jersey City, or City of Camden, and no county, school district, transit authority, hospital district, regional authority, special district, or private provider was presented as the target employer.

However, six of eight rows carry `wrong_employer_risk=possible`; only the Jersey City fire and Local 246 rows carry `none`. The possible labels are appropriate verification warnings, especially for the third-party-hosted Jersey City police PDF and for confirming Camden municipality rather than another Camden government. These are unresolved risks, not observed substitutions.

### Wrong-unit and safety-as-non-safety leakage

No explicit wrong-unit substitution or safety-as-non-safety leakage is visible. The two non-safety rows are Jersey City Local 246 and Camden CWA Local 1014 non-supervisory employees; neither is described as a police/fire/safety agreement. No EMS, county corrections, school police, transit police, or other excluded unit was labeled non-safety.

Two unit questions remain for verification: whether Jersey City Local 246 is the intended ordinary civilian comparator, and why the Camden consent award names IAFF Local 2578 while the fire CBAs name Local 788. The latter may be a distinct fire unit or a source/model identity problem, but it is not enough at scout stage to call the row wrong-unit leakage.

### Blocked versus dead labeling

No returned row is labeled blocked/unreadable or dead/unreachable. All eight have `blocked_or_unreadable_flag=no`; no 404/410/DNS claim appears. The Newark Legistar result is labeled an index/landing page and context only rather than incorrectly called dead. Therefore no blocked-versus-dead labeling error is visible from the scout output alone.

### Parser failures and retries

There were zero parser failures. `failed_parses.csv` is a header-only failure ledger. No row retry was justified, and none occurred. There were no connection-error rows, missing response IDs, or zero-output responses.

## Strongest unverified leads

The highest-value verification queue is:

1. Jersey City Local 1066 fire MOA/resolution context: official-city provenance, but incomplete operative dates and binding/executed status need confirmation.
2. Jersey City Local 246 2019-2022 civilian MOA: potentially the ordinary comparison leg overlapping both safety successors.
3. Jersey City POBA 2021-2024 police MOA: potentially completes the candidate-stage triad, but it is third-party hosted and needs official provenance and execution review.
4. Camden IAFF Local 788 2021-2024 fire agreement plus CWA Local 1014 2022-2025 non-supervisory agreement: potentially a strong same-city overlapping safety/non-safety pair.
5. Camden Local 2578 consent award: potentially useful mechanism evidence, but the unit identity must be reconciled against Local 788.
6. Newark Local 1860 2017-2023 Legistar record: useful as a locator for the missing fire repair, but not itself an inspected full CBA in the scout output.

## Verification next step

The next task should be a bounded source-verification pass over exactly these eight returned URLs, with no new scouting. For each row, establish reachability/access, official or union provenance, exact city employer, exact bargaining unit, executed/binding status, document completeness, visible operative dates, wage-setting content, duplicate/planning-trace status, and within-city cycle overlap. Particular priorities are the Jersey City three-leg 2021-2022 overlap, the Camden Local 788/Local 2578 identity question, the Camden civilian unit's safety exclusion, and whether Newark's Legistar record attaches the full executed 2017-2023 fire instrument.

Do not ingest, codify, update canonical coverage, or use any candidate as claim evidence until that separate verification is complete.

## Validation and unchanged canonical coverage

All four requested `py_compile` commands passed. The direct-backend regression test passed six checks, including the repeated-connection-error stop gate. The prompt contract passed six checks. `scripts/validate.py` passed with 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows. `ingest/test_pipeline.py` passed 60/60. The coverage audit remains 28 healthy pairs across 19 cities (10 exact-cycle and 18 overlap-cycle), 2 exploratory adjacent matches, and 6 unmatched safety units. Scout output did not alter canonical coverage; Newark's existing fire 2013-2015 row remains unmatched in the canonical audit because the new 2017-2023 item is unverified scout-stage context only.

## Artifacts

- Smoke preflight: `tmp/direct_sdk_scout_backend_preflight/NJ/national_batch01_nj_2026-07-20/`
- Live run: `tmp/gabriel_state_source_scout/NJ/national_batch01_nj_live_direct_sdk_2026-07-20/`
- Staged runner CSV: `docs/analysis/gabriel_state_source_scout_candidates_nj_2026-07-20_165402.csv`
- Review handoff CSV: `docs/analysis/national_batch01_nj_live_direct_sdk_scout_candidates_2026-07-20.csv`
- Validation transcripts: `tmp/national_batch01_nj_live_direct_sdk_validation_2026-07-20/`
