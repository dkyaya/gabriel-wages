# New York National Batch 01 NY25 Direct-SDK Live Scout Review

Date: 2026-07-20

Stage: live source discovery and light triage only. Every returned row remains an unverified scout candidate. No source URL was independently opened, no PDF was downloaded, and no source was verified, ingested, codified, added to canonical coverage, or used as claim evidence.

## Plain-English result

The mandatory synthetic direct-SDK preflight passed, so the locked 25-city New York batch ran once through the direct-SDK backend. Connectivity held across all 25 prompts: every response was nonempty, carried a response ID, and parsed successfully. Twenty-one municipalities produced 57 candidate rows; Yonkers, Schenectady, Mount Vernon, and Newburgh returned valid empty candidate lists. There were no connection failures, parser failures, or retries.

The output contains useful-looking apparent matched sets for Rochester, Syracuse, Ithaca, and Saratoga Springs. Poughkeepsie has a model-described older set with a blocked police locator. New York City's rows only form a narrow legacy overlap around 2017, and Auburn's safety and ordinary-civilian rows are adjacent rather than mutually overlapping. These are model-returned leads, not verified source facts.

## Source-of-truth reconciliation

The supplied relay `tmp/national_batch01_ny25_filter_contract_dry_run_2026-07-20_relay_a393f60.zip` passed ZIP integrity inspection. Every requested shared relay/repository file, including the saved dry-run prompt and metadata, matched byte-for-byte. Local `HEAD` before work was `a393f60c92f7137c46536cc6ab724e7a04dacaa9`, the same checkpoint represented by the relay. There was no discrepancy to resolve, and no Git remote was inspected.

## Preflight gate

Artifacts: `tmp/direct_sdk_scout_backend_preflight/NY/national_batch01_ny25_2026-07-20/`

- Prompt: exactly `Reply with OK.`
- Backend/resource: OpenAI Responses API through the direct-SDK backend and Harvard `/v2` base
- Model: `gpt-5.4-nano`
- Tools/search: omitted; `web_search=false`
- Requests/retries/timeout: one request, zero retries, 30 seconds
- Result: `OK`, with a response ID; 10 input, 0 reasoning, and 5 output tokens
- Gate: `success=true` and `model_response_succeeded=true`; no connection error

The live batch proceeded only after all required gate conditions passed.

## Locked live execution

The input resolved before execution to exactly this ordered list: Buffalo, Rochester, Syracuse, Yonkers, Albany, New York, Utica, Schenectady, White Plains, New Rochelle, Mount Vernon, Troy, Niagara Falls, Binghamton, Poughkeepsie, Newburgh, Middletown, Ithaca, Saratoga Springs, Watertown, Kingston, Jamestown, Elmira, Rome, and Auburn.

Exact command used:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state NY \
  --municipalities-csv docs/analysis/national_batch01_ny25_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/NY/national_batch01_ny25_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

The project virtual-environment interpreter was used because the shell's `python` and `python3` shims were not usable in the preceding dry-run work. Run ID was `ny_2026-07-20_200033`. The batch completed normally in roughly 24 minutes. It recorded 955,600 input, 43,749 reasoning, and 68,985 output tokens. Average model-response time was about 42.38 seconds. The direct SDK exposed usage but not billed dollars, so cost remains unavailable rather than estimated.

## Municipality and unit results

| Municipality | Police | Fire | Non-safety | Unclear | Total | Scout outcome |
|---|---:|---:|---:|---:|---:|---|
| Buffalo | 1 | 1 | 0 | 0 | 2 | candidates |
| Rochester | 2 | 1 | 1 | 0 | 4 | candidates |
| Syracuse | 2 | 1 | 1 | 0 | 4 | candidates |
| Yonkers | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| Albany | 2 | 0 | 0 | 0 | 2 | candidates |
| New York | 1 | 1 | 1 | 1 | 4 | candidates |
| Utica | 0 | 1 | 1 | 0 | 2 | candidates |
| Schenectady | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| White Plains | 1 | 1 | 0 | 0 | 2 | candidates |
| New Rochelle | 1 | 1 | 0 | 0 | 2 | candidates |
| Mount Vernon | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| Troy | 1 | 0 | 0 | 0 | 1 | candidates |
| Niagara Falls | 1 | 0 | 0 | 0 | 1 | candidates |
| Binghamton | 2 | 0 | 0 | 0 | 2 | candidates |
| Poughkeepsie | 1 | 1 | 1 | 0 | 3 | candidates |
| Newburgh | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| Middletown | 1 | 1 | 0 | 0 | 2 | candidates |
| Ithaca | 1 | 1 | 1 | 0 | 3 | candidates |
| Saratoga Springs | 2 | 1 | 2 | 0 | 5 | candidates |
| Watertown | 1 | 1 | 1 | 0 | 3 | candidates |
| Kingston | 2 | 1 | 1 | 0 | 4 | candidates |
| Jamestown | 1 | 1 | 0 | 0 | 2 | candidates |
| Elmira | 1 | 1 | 0 | 0 | 2 | candidates |
| Rome | 1 | 1 | 0 | 0 | 2 | candidates |
| Auburn | 1 | 1 | 1 | 2 | 5 | candidates |
| **Total** | **26** | **17** | **11** | **3** | **57** | **25 parsed responses** |

## Claim anchors and useful-looking sets

- **Buffalo:** one apparent fire agreement covering 2017-2025 and one police tentative-agreement board record for 2021-2025 were returned. The police item is minutes/context and there is no ordinary-civilian leg.
- **Rochester:** apparent police 2019-2024 and 2024-2028 agreements, fire 2021-2026, and AFSCME 2022-2027 material form a promising repeat-cycle set, with a model-described 2022-2024 mutual overlap among the earlier police, fire, and civilian rows.
- **Syracuse:** the model returned police award/MOA material and full fire/CSEA agreements with a shared 2018-2019 period. This is a mechanism-plus-base-agreement set, not yet proof of a police base CBA.
- **Yonkers:** the response parsed but returned no candidates. This counts as scout coverage, not proof that no contract source exists.
- **Albany:** two police mechanism rows were returned, with no fire or ordinary-civilian comparator.
- **New York City:** the police 2012-2017, fire 2011-2018, and DC 37 2017-2021 rows have at most a narrow 2017 legacy overlap. The extra PBA award is labeled `unclear` despite visible police identity. This is not a current matched set.
- **Other strongest apparent sets:** Ithaca has model-described police/fire/civilian overlap during 2021-2024. Saratoga Springs has a possible 2019-2021 police/fire/civilian overlap. Poughkeepsie's older safety/civilian material overlaps inside the observation window around 2014-2016 but the police locator is blocked. Kingston has police/fire overlap but its only civilian row is an insufficient multi-union premium MOA. Auburn's police/fire rows end in 2022 while the civilian row begins in 2023, so it is a repeat-cycle lead rather than a mutually overlapping triad.

All date, completeness, employer, unit, and source descriptions above are scout output only and require later verification.

## Filtering and leakage review

- **Canonical/queue duplicates:** there is no exact URL overlap within the NY run, with the pre-NY national queue, or with canonical `contracts.csv`. One Rochester successor police row has `duplicate_risk=possible`; it is retained as a possible-duplicate hold even though its model-described 2024-2028 term follows the 2019-2024 row rather than exactly duplicating it.
- **Wrong employer:** every employer field visibly names the intended municipal government. No county, school, transit, park, housing, township, authority, or other special-district substitute is visible. Fifty-five rows retain model-level `possible` wrong-employer risk, which is a verification warning rather than evidence of 55 substitutions.
- **Wrong unit:** three rows labeled `unclear` are visibly PBA/police arbitration material—one New York City and two Auburn rows. That is unit-label leakage, so they cannot count toward a matched set until relabeled through verification. New Rochelle's police agenda record is correctly context-only.
- **Safety as non-safety:** no ordinary police/fire CBA is directly labeled non-safety. Kingston's non-safety row is a one-time premium MOA listing CSEA together with police and fire unions; it is already insufficient, but its multi-unit scope means it must not serve as an ordinary-civilian comparator without later unit-specific confirmation.
- **Context and insufficiency:** 46 rows are marked qualifying, 10 insufficient, and one context-only. Five rows have `context_only_flag=yes`. Awards, MOAs, minutes, agenda material, and summary/partial documents remain mechanism or locator leads rather than automatic base-CBA substitutes.
- **Blocked versus dead:** three rows have `blocked_or_unreadable_flag=yes`; none is labeled dead. Middletown is consistently insufficient/blocked. Poughkeepsie's police row is still called qualifying despite blocked access, and Watertown's fire row is insufficient with unclear completeness. Queue precedence holds all blocked rows as insufficient until later access review.
- **Parser/failure accounting:** all 25 responses parsed, including four valid empty candidate lists. There were no JSON/parser failures, connection errors, zero-response rows, or retries.

## Queue and coverage update

The normalized handoff contains 57 rows, all with `scout_stage_status=unverified_scout_candidate`. The national queue now has 246 rows: PA 75, TX 6, MA 24, NJ 8, IL 76, and NY 57. New York triage assigns 33 high, 11 medium, and 4 low rows to later verification; 5 context, 3 insufficient, and 1 possible-duplicate row remain holds. Thus 48 NY rows are queued for later verification. These scores schedule later work; they do not verify a source.

National successful scout coverage rises from 63 to 88 municipalities. All 25 New York prompts count as successful discovery coverage: 21 with candidates and four with parseable empty output. The New York denominator is 1,523 governments, leaving 1,498 not scouted. NY has no connection-failed attempt, calibration-verified municipality, later-ingest approval, exact canonical candidate overlap, codified output, or claim-supporting row from this run.

## What should happen next

Do not open all 57 URLs or ingest any result automatically. Continue national state-scale scouting only under separate authorization and after a fresh direct-SDK smoke preflight. Later coordinated verification should select coherent municipality-level bundles—starting with Rochester, Ithaca, Saratoga Springs, and the Syracuse mechanism/base-agreement group—and establish exact employer and unit, authoritative provenance, executed/binding and complete-document status, visible dates, wage-setting content, duplicate status, and mutual cycle overlap. Poughkeepsie access, the three `unclear` police awards, and Kingston's multi-union comparator need explicit resolution before matched-set use.
