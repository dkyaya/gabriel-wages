# National Batch 01 Massachusetts Live Scout Review

Date: 2026-07-16  
Wave: `NWMS-2026-07-16-01`  
Scope: exactly Somerville, Newton, Boston, Worcester, Arlington, Georgetown, Franklin, and Seekonk, Massachusetts  
Stage: scout-stage transport failure; no verification, ingestion, codification, or claim use

## Result in plain English

The live scout submitted the locked eight-row, full-context Massachusetts input with the minimal filtering prompt and low search context. GABRIEL recorded an API/proxy `Connection error.` for every primary-row call. Each response was empty, so no response parsed and no candidate was returned. The primary runner preserved its prompt preview, raw output, empty parsed-candidate file, eight-row failure ledger, metadata, and cost summaries.

The initial failures were diagnosed as empty responses with a recorded connection error and no response ID, output tokens, or web sources. One bounded retry was made for every failed row, split into Somerville/Newton/Boston and Worcester/Arlington/Georgetown/Franklin/Seekonk. All eight retries failed identically. No further call was made. This is an infrastructure failure, not a finding that sources do or do not exist.

No parsed candidates exist, so no quarantined task-level candidate summary CSV was created. The runner-created candidate CSVs contain headers only. Nothing was verified, ingested, codified, added to a claim, or used to change any canonical contract, coverage, corpus, claim, or codified-output file.

## What the live scout found

It found no usable source leads because it received no model content.

| Municipality | Target | Scout result |
|---|---|---|
| Somerville | ordinary non-safety comparator or impasse material | No candidates; primary call and one retry had empty connection-error responses. |
| Newton | ordinary non-safety comparator | No candidates; primary call and one retry had empty connection-error responses. |
| Boston | fire CBA or fire impasse/arbitration | No candidates; primary call and one retry had empty connection-error responses. |
| Worcester | police base CBA or useful non-safety base CBA | No candidates; primary call and one retry had empty connection-error responses. |
| Arlington | police CBA or formal impasse material | No candidates; primary call and one retry had empty connection-error responses. |
| Georgetown | fire agreement or authoritative absence evidence | No candidates; primary call and one retry had empty connection-error responses. |
| Franklin | repeat-cycle police/fire/ordinary non-safety/mechanism material | No candidates; primary call and one retry had empty connection-error responses. |
| Seekonk | repeat-cycle police/fire/ordinary non-safety/mechanism material | No candidates; primary call and one retry had empty connection-error responses. |

Therefore, the requested substantive questions cannot be answered from this run: Somerville and Newton did not find ordinary comparator leads; Boston did not find fire material; Worcester did not find police or civilian base material; Arlington did not find police or impasse material; Georgetown did not find a fire agreement or context; and Franklin and Seekonk did not find repeat-cycle, comparator, or mechanism material. These are **no-result transport outcomes**, not negative source findings.

## Leakage and parser assessment

- Wrong-employer leakage: none observed. There was no response content to classify.
- Wrong-unit leakage: none observed. There was no response content to classify.
- Safety-as-non-safety leakage: none observed. There was no response content to classify.
- Context-only leakage: none observed. There was no response content to classify.
- Parser failures: 8 of 8 primary rows failed as `empty_response_no_response_id`; all record `['Connection error.']` in GABRIEL's error field. The two retry runs add 8 more failures of the same type (3 + 5).

## Artifacts and cost

Primary run: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16/`

- Run ID: `ma_2026-07-16_183246`
- Primary rows: 8 attempted, 0 parseable, 0 candidates, 8 failed parses.
- Recorded primary cost: `$0.0012828`; input tokens: `6,414`; reasoning tokens: `0`; output tokens: `0`.
- Retry run: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16_retry_failed/` (Somerville/Newton/Boston): 0 parseable, 0 candidates, 3 failed parses; `$0.0004592`; 2,296 input tokens; 0 reasoning/output tokens.
- Retry run: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16_remaining_first_attempt/` (Worcester/Arlington/Georgetown/Franklin/Seekonk): 0 parseable, 0 candidates, 5 failed parses; `$0.0008236`; 4,118 input tokens; 0 reasoning/output tokens.

Known completed-run cost is `$0.0025656` across 16 charged failed calls: 12,828 input tokens and zero reasoning/output tokens. The main output also contains the prompt preview, raw responses, parsed-candidate header, failed-parses ledger, failure ledger prepared before retry, console log, and GABRIEL save metadata.

## Promising but unverified leads

None. An empty connection-error response cannot support a candidate, absence claim, or verification queue.

## Verification next step

Do not begin source verification from this run because it has no candidate URLs or traces. First restore/confirm GABRIEL proxy connectivity outside this bounded research batch. If a new live scout is authorized after that infrastructure check, start a fresh eight-row MA run from the locked full-context input; do not treat this run's emptiness as evidence of municipal source absence. Keep any future output at scout stage until direct-source verification establishes exact employer, unit, source ownership, document completeness, dates, and matched-cycle value.
