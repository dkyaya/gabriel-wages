# California CA25 Direct-SDK Live Scout Review

Batch/file date: 2026-07-20

Execution/review date: 2026-07-21

Stage: scout-stage source discovery, light filtering, queueing, and discovery-coverage accounting only. Nothing in this note is source verification, ingestion approval, codified evidence, canonical coverage, or claim support.

## Plain-English result

The locked CA25 dry run and one-request direct-SDK smoke both passed, so the exact California batch ran once. Twenty-one of 25 municipalities returned nonempty responses with response IDs and positive tokens; all 21 parsed. Four separated requests—Oakland, Stockton, Oxnard, and Redding—timed out at the 90-second request ceiling with no response text, response ID, or tokens. They are infrastructure failures, not valid empty source results, and do not count as discovery coverage. No retry ran and the repeated-connection-error stop gate did not trip.

The 21 parseable responses produced 64 URL-bearing rows across 20 candidate-positive municipalities. San Jose returned a valid empty candidate list. The normalized handoff preserves every parsed row as `scout_stage_status=unverified_scout_candidate`. No source URL was independently opened, verified, downloaded, or ingested.

## Selection and gates

The selected order was Los Angeles, Sacramento, San Diego, San Francisco, Fresno, San Jose, Long Beach, Oakland, Bakersfield, Anaheim, Riverside, Stockton, Chula Vista, Fremont, Modesto, Oxnard, Santa Rosa, Salinas, Vallejo, Redding, Chico, Visalia, Santa Barbara, Berkeley, and Palo Alto.

All 25 rows came from the authoritative municipality universe, were `municipal` / `place` employers, preserved unique municipality and Census government IDs, had `not_scouted` pre-run status and zero prior failure attempts, and were absent from the pre-run queue and canonical corpus. The batch included all five California national-manifest anchors and spanned 20 counties. The City and County of San Francisco was retained only as the universe's California-specific consolidated municipal employer.

Dry run `ca_2026-07-21_100843` built 25 prompts and recorded `live_attempted=false`. Its rendered preview passed the exact-employer/ID, wrong-employer, ordinary-civilian comparator, safety-not-non-safety, context, blocked-versus-dead, visible-year, duplicate, empty-output, public-records-request, and unverified-stage checks for every municipality.

The synthetic preflight then used exactly `Reply with OK.`, `gpt-5.4-nano`, the Harvard HUIT `/v2` base, no tools or search, one request, a 30-second timeout, and zero retries. It returned `OK.`, a response ID, explicit success metadata, and 10 input / 0 reasoning / 6 output / 16 total tokens with no connection error. Its token-only estimated cost was USD 0.0000095, labeled estimate-only.

## Exact live execution

The project virtual-environment interpreter was used because the latest relay records the shell `python` and `python3` shims as unusable.

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state CA \
  --municipalities-csv docs/analysis/national_batch01_ca25_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/CA/national_batch01_ca25_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

Run `ca_2026-07-21_101012` completed the bounded 25-request process. Connectivity/result status is 21 backend-successful, nonempty and parseable responses; four non-consecutive API timeouts; zero malformed-JSON responses; zero retries; and 64 parsed candidate rows.

## Candidate counts

| Municipality | Police | Fire | Ordinary non-safety | Unclear | Total | Scout outcome |
|---|---:|---:|---:|---:|---:|---|
| Los Angeles | 1 | 1 | 1 | 1 | 4 | candidates |
| Sacramento | 1 | 1 | 1 | 0 | 3 | candidates |
| San Diego | 1 | 1 | 1 | 0 | 3 | candidates |
| San Francisco | 1 | 1 | 1 | 0 | 3 | candidates |
| Fresno | 1 | 1 | 1 | 0 | 3 | candidates |
| San Jose | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| Long Beach | 2 | 1 | 1 | 0 | 4 | candidates |
| Oakland | 0 | 0 | 0 | 0 | 0 | timeout; no model response |
| Bakersfield | 1 | 1 | 1 | 0 | 3 | candidates |
| Anaheim | 1 | 1 | 1 | 0 | 3 | candidates |
| Riverside | 2 | 1 | 2 | 0 | 5 | candidates |
| Stockton | 0 | 0 | 0 | 0 | 0 | timeout; no model response |
| Chula Vista | 1 | 1 | 1 | 0 | 3 | candidates |
| Fremont | 2 | 1 | 0 | 0 | 3 | candidates |
| Modesto | 1 | 1 | 1 | 0 | 3 | candidates |
| Oxnard | 0 | 0 | 0 | 0 | 0 | timeout; no model response |
| Santa Rosa | 1 | 1 | 1 | 1 | 4 | candidates |
| Salinas | 1 | 1 | 1 | 0 | 3 | candidates |
| Vallejo | 1 | 0 | 1 | 0 | 2 | candidates |
| Redding | 0 | 0 | 0 | 0 | 0 | timeout; no model response |
| Chico | 1 | 1 | 1 | 0 | 3 | candidates |
| Visalia | 0 | 0 | 1 | 0 | 1 | candidates |
| Santa Barbara | 1 | 1 | 1 | 0 | 3 | candidates |
| Berkeley | 1 | 1 | 1 | 0 | 3 | candidates |
| Palo Alto | 2 | 1 | 1 | 1 | 5 | candidates |
| **Total** | **23** | **18** | **20** | **3** | **64** | **21 parsed; 4 timeouts** |

## Strongest apparent leads, still unverified

The cleanest metadata-level matched-cycle groups are:

- San Diego: apparent police, fire, and municipal-employees agreements all labeled July 2013-June 2018, overlapping the project window during 2014-2018;
- Fresno: apparent police, fire, and white-collar/civilian material with common coverage from early 2022 through mid-2024, although the fire row is labeled partial;
- Long Beach: apparent police, fire, and SEIU agreements with common 2019-2022 coverage;
- Los Angeles: apparent police and fire agreements through June 2024 and clerical material beginning December 2023, yielding a narrow late-2023/2024 overlap;
- Chico: apparent police 2023-2026, fire 2021-2025, and trades/crafts civilian 2022-2024 material, with a possible common 2023-2024 period;
- Anaheim: apparent police, fire, and clerical agreements with a common period in 2015-2016;
- Palo Alto: apparent police/fire 2018-2021 and civilian management/professional material for 2019-2020, though the civilian row is labeled partial;
- Berkeley and Santa Barbara: apparent safety/civilian groups touching at the 2024 boundary and therefore requiring exact effective-date review.

Bakersfield has an apparent 2019-2022 triad shape, but its civilian row is partial/insufficient. Modesto appears to converge only around the 2024 boundary. Riverside has safety and civilian material across different periods, with one civilian cycle unclear. San Francisco's safety rows end in 2021 while the returned civilian row begins in 2022. Sacramento's returned material is largely 2025-2028 and therefore outside the 2014-2024 observation window. Salinas police material begins in 2026; Santa Rosa's returned cycles are adjacent rather than a clean triad; Fremont lacks a civilian row; Vallejo lacks fire; and Visalia returned only a civilian row. These are scheduling observations from model metadata, not verified source findings.

## Leakage, parser, and access review

- **Parser/failure accounting:** four `timeout_or_capacity` rows—Oakland, Stockton, Oxnard, and Redding—contain no response text, response ID, or tokens. They are not JSON parser failures and not empty candidate lists. The other 21 responses parsed, including San Jose's valid empty list.
- **Connectivity:** the four timeouts were separated by successful calls. There was no repeated connection-error sequence and no stop-gate truncation; all 25 authorized requests were attempted once.
- **Exact duplicates:** zero returned CA URLs exactly match another URL in this run, the pre-run queue, or canonical `contracts.csv`. Three rows self-label `duplicate_risk=possible`; they remain possible-duplicate holds. String comparison is not source verification.
- **Wrong employer:** no visible row substitutes a county, school, transit, authority, special district, or private provider. One Los Angeles mechanism row uses `CITY OF LOS ANGELES POLICE DEPARTMENT` rather than the exact city-employer string and carries `wrong_employer_risk=high`; it is already `unclear` / `insufficient_candidate`. Forty-seven other rows conservatively carry `possible`, 16 carry `none`.
- **Wrong unit:** the Chula Vista fire-titled row refers to “Non-Safety Local 2180, IAFF”; it remains fire-labeled and insufficient, but exact unit identity needs later review. Three mechanism rows are appropriately `unclear` rather than forced into a bargaining-unit class.
- **Safety as non-safety:** no returned `non_safety` row is visibly a police, fire, EMS, corrections, dispatcher, or other safety agreement. Sacramento's exempt/general-city row is already context/insufficient with an unclear comparator role rather than treated as a clean repair.
- **Context/insufficiency:** 56 rows are `qualifying_candidate`, six `insufficient_candidate`, and two `context_only_candidate`; three rows have `context_only_flag=yes`.
- **Blocked versus dead:** none of the 64 parsed source rows is marked blocked/unreadable or dead/unreachable. The four API timeouts are transport failures and must not be interpreted as dead source URLs.
- **Locators:** all 64 parsed rows contain a source URL. No URL was inferred or independently opened.

## Token usage and estimated cost

The direct SDK reported 933,502 input tokens, 45,418 reasoning tokens, 73,859 output tokens, and 1,007,361 total tokens. The SDK did not expose billed dollars, so `cost_available=false` and actual `total_cost=null` remain unchanged.

The configurable estimate uses `direct_sdk_pricing_config_2026-07-20.json`. Based on the standard public OpenAI text-token rates recorded there, the run's estimated input cost is USD 0.1867004, estimated output cost is USD 0.09232375, incremental reasoning cost is USD 0 because reasoning tokens are treated as already included within `output_tokens`, and estimated token-only total is USD 0.27902415. `estimate_only=true` and `pricing_missing_or_unconfirmed=true`: Harvard HUIT billing is unconfirmed, and the estimate excludes hosted web-search/tool fees, cached-input treatment, taxes, credits, discounts, and other adjustments. It must not be treated as actual cost.

## Queue and coverage update

The normalized handoff contains all 64 rows as `unverified_scout_candidate`, and all 64 have locators. The durable national queue now contains 451 rows: 355 scheduled for later verification and 96 holds/rejections. California contributes 64 rows: 53 high-priority, three medium-priority, two low-priority, three context-only holds, and three likely-duplicate holds; 58 are scheduled for later coordinated verification.

National discovery coverage now counts 159 municipalities: 145 candidate-positive and 14 parseable-empty. California contributes 21 successful discovery outcomes—20 candidate-positive and San Jose parseable-empty. Oakland, Stockton, Oxnard, and Redding remain four separate failure-only timeout rows and are excluded from coverage. Across all states, 21 failed attempts remain separately recorded and excluded. Queueing performed no source verification and changed no canonical contract, city-coverage, corpus, codified, or claim-stage file.

## Recommended next move

Do not retry the four California timeout rows without separate authorization, and do not open all 64 URLs one by one. Continue national scaling only through another separately prepared locked state batch with a fresh successful direct-SDK smoke, or begin a separately authorized coordinated verification wave built around coherent municipality bundles. If verification is selected later, start with San Diego, Fresno, Long Beach, Los Angeles, Chico, Anaheim, Palo Alto, Berkeley, and Santa Barbara; establish exact employer/unit identity, authoritative provenance, execution/completeness, visible operative dates, wage-setting content, duplicate status, access, and mutual cycle overlap before any ingestion decision.
