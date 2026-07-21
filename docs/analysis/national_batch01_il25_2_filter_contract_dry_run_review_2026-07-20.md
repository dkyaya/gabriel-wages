# Illinois National Batch 01 IL25.2 Filter-Contract Dry-Run Review

Date: 2026-07-20

Stage: dry-run prompt construction and review only. No model/API call, hosted search, source URL opening, document download, source verification, ingestion, codification, canonical-data edit, or claim promotion occurred.

## Plain-English result

IL25.2 is acceptable for a future separately authorized direct-SDK live scout, but only after a fresh successful synthetic no-search smoke preflight. The dry run built exactly 25 full-context prompts for distinct Illinois city/village governments. No successfully covered IL25 municipality is present, Bloomington is excluded, and every selected row was `not_scouted` with zero prior failed attempts before this dry run.

The prompt contract remains intact: exact employer/Census identity, categorical wrong-employer exclusions, ordinary-civilian comparator rules, safety-not-non-safety prohibition, context/insufficient separation, blocked-versus-dead access labels, visible-year evidence, duplicate controls, matched/repeat-cycle logic, allowed empty output, and unverified scout-stage status all appear in the saved preview.

## Exact dry-run command

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_2_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_2_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

The project virtual-environment interpreter was used because the shell's `python` and `python3` shims have been unusable in the recent state-scale tasks.

## Metadata summary

- Run ID: `il_2026-07-20_204520`
- State: `IL`
- Mode: `dry_run`
- Municipalities requested: 25
- Model recorded for eventual execution: `gpt-5.4-nano`
- Prompt mode: `minimal`
- Live hard cap: 25
- `live_attempted=false`
- `live_succeeded=false`
- `model_response_succeeded=false`
- Files written: `prompt_preview.md` and `run_metadata.json` only

The false live/model fields are the expected safe dry-run state, not a failed API call.

## Exact municipality input

| Rank | Municipality | Exact employer | Census ID | Population | County context | Selection bucket |
|---:|---|---|---:|---:|---|---|
| 1 | Arlington Heights | VILLAGE OF ARLINGTON HEIGHTS | 162229 | 74,495 | Cook | `large_city_state_anchor` |
| 2 | Oak Lawn | VILLAGE OF OAK LAWN | 124891 | 55,734 | Cook | `large_city_state_anchor` |
| 3 | Berwyn | CITY OF BERWYN | 207777 | 54,414 | Cook | `large_city_state_anchor` |
| 4 | Mount Prospect | VILLAGE OF MOUNT PROSPECT | 162258 | 54,298 | Cook | `large_city_state_anchor` |
| 5 | Wheaton | CITY OF WHEATON | 124909 | 52,938 | DuPage | `large_city_state_anchor` |
| 6 | Oak Park | VILLAGE OF OAK PARK | 124892 | 52,055 | Cook | `mid_city_comparison_candidate` |
| 7 | Hoffman Estates | VILLAGE OF HOFFMAN ESTATES | 162277 | 50,179 | Cook / Kane | `mid_city_comparison_candidate` |
| 8 | Downers Grove | VILLAGE OF DOWNERS GROVE | 162295 | 49,706 | DuPage | `mid_city_comparison_candidate` |
| 9 | Plainfield | VILLAGE OF PLAINFIELD | 194711 | 47,448 | Kendall / Will | `mid_city_comparison_candidate` |
| 10 | Glenview | VILLAGE OF GLENVIEW | 204271 | 46,904 | Cook | `mid_city_comparison_candidate` |
| 11 | Elmhurst | CITY OF ELMHURST | 162296 | 45,336 | Cook / DuPage | `mid_city_comparison_candidate` |
| 12 | Romeoville | VILLAGE OF ROMEOVILLE | 102873 | 40,955 | Will | `mid_city_comparison_candidate` |
| 13 | Crystal Lake | CITY OF CRYSTAL LAKE | 162474 | 40,861 | McHenry | `regional_diversity_candidate` |
| 14 | DeKalb | CITY OF DE KALB | 102649 | 40,211 | DeKalb | `regional_diversity_candidate` |
| 15 | Carpentersville | VILLAGE OF CARPENTERSVILLE | 162404 | 37,099 | Kane | `regional_diversity_candidate` |
| 16 | Oswego | VILLAGE OF OSWEGO | 194718 | 37,074 | Kendall / Will | `regional_diversity_candidate` |
| 17 | Pekin | CITY OF PEKIN | 162651 | 31,126 | Peoria / Tazewell | `regional_diversity_candidate` |
| 18 | Danville | CITY OF DANVILLE | 102859 | 28,206 | Vermilion | `regional_diversity_candidate` |
| 19 | Granite City | CITY OF GRANITE CITY | 125005 | 26,908 | Madison | `regional_diversity_candidate` |
| 20 | Urbana | CITY OF URBANA | 124874 | 38,209 | Champaign | `continuity_with_il25_candidate` |
| 21 | Rock Island | CITY OF ROCK ISLAND | 162602 | 36,132 | Rock Island | `continuity_with_il25_candidate` |
| 22 | O'Fallon | CITY OF O FALLON | 162610 | 31,968 | St. Clair | `continuity_with_il25_candidate` |
| 23 | Loves Park | CITY OF LOVES PARK | 162707 | 23,335 | Boone / Winnebago | `continuity_with_il25_candidate` |
| 24 | Galesburg | CITY OF GALESBURG | 162420 | 29,130 | Knox | `clean_municipal_employer_candidate` |
| 25 | Freeport | CITY OF FREEPORT | 102850 | 23,136 | Stephenson | `clean_municipal_employer_candidate` |

## Selection-bucket counts

| Bucket | Rows |
|---|---:|
| `large_city_state_anchor` | 5 |
| `mid_city_comparison_candidate` | 7 |
| `regional_diversity_candidate` | 7 |
| `continuity_with_il25_candidate` | 4 |
| `clean_municipal_employer_candidate` | 2 |
| **Total** | **25** |

## IL25 and Bloomington exclusion

The first IL25 input contains 25 unique IDs. Current coverage classifies 23 as `scouted_with_candidates`, Champaign as `scouted_no_candidates`, and Bloomington as `scout_attempt_failed_connection`. The IL25.2 builder rejects every prior IL25 ID regardless of which of those statuses applies. It also independently requires `scout_coverage_status=not_scouted` and `failed_connection_attempt_count=0` for every new row.

The selected/prior ID intersection is empty. Bloomington is absent by name and ID. No other successfully covered municipality from PA, TX, MA, NJ, IL, or NY can pass the same coverage gate.

## Prompt-review checklist

- [x] Exactly 25 input rows and exactly 25 municipality prompt sections are present.
- [x] Every prompt includes the exact city/village employer and Census government ID.
- [x] No successful IL25 municipality is selected.
- [x] Bloomington is not selected.
- [x] County geography is labeled context only, not an alternate employer.
- [x] County and township governments, school districts, transit authorities/agencies, housing authorities, park districts, special districts, regional bodies, universities, and private providers are excluded as substitutes.
- [x] `non_safety` is restricted to ordinary municipal/civilian employees or authoritative civilian wage-setting material.
- [x] Police, fire, or other safety agreements cannot satisfy a non-safety request.
- [x] Ambiguous units must remain `unclear`; they cannot be forced into non-safety.
- [x] Context-only and insufficient items are labeled separately and do not count as qualifying agreements/comparators.
- [x] `blocked_or_unreadable` is distinct from `dead_or_unreachable`, which requires observed 404/410/DNS-equivalent evidence.
- [x] `visible_year_evidence`, `overlap_with_anchor_cycle`, `cycle_match_notes`, and `duplicate_risk` are requested.
- [x] Matched-cycle repair and repeat-cycle behavior are both explained.
- [x] An empty candidates list is explicitly permitted.
- [x] Every future return is explicitly unverified scout-stage lead data, not verified, ingested, codified, or claim-supporting.

## Future live runtime, usage, and cost planning

The first Illinois batch used 1,028,386 input, 49,032 reasoning, and 79,974 output tokens, with 24 successful responses plus one timeout and roughly 28 minutes elapsed. NY25 used 955,600 input, 43,749 reasoning, and 68,985 output tokens, with 25 successful responses and roughly 24 minutes elapsed.

Their midpoint is approximately 992,000 input, 46,000 reasoning, and 74,000 output tokens. For a serial IL25.2 live run with 15-second spacing, a prudent envelope is:

- runtime: roughly 24-32 minutes;
- input tokens: about 0.95-1.10 million;
- reasoning tokens: about 43,000-52,000;
- output tokens: about 68,000-85,000.

The direct SDK did not expose billed dollar cost for IL25 or NY25. A prior `$0.27-$0.30` GABRIEL-priced comparison is only a rough historical proxy and must not be represented as direct-SDK cost. Future artifacts should report actual exposed usage and leave billed dollars unavailable if the proxy still omits them.

## Expected queue and coverage behavior after a future live run

After separate authorization, a fresh successful smoke, and one locked IL25.2 live run:

1. Preserve raw, parsed, failed, prompt, metadata, log, and usage/cost artifacts.
2. Normalize every returned candidate as `unverified_scout_candidate`.
3. Add candidate rows to the national queue without opening every URL.
4. Count each municipality with a parseable candidate response or parseable empty response as successfully scout-covered.
5. Keep any connection-only or zero-response failure outside successful discovery coverage and record it separately.
6. Rebuild municipality/state/county coverage and reconcile the 35,589-government denominator.
7. Do not create verification, ingestion, canonical, codified, or claim-stage status from scout output.

## Readiness and next step

IL25.2 is prompt-ready for a future separately authorized live scout. It is not live-authorized by this dry-run task. Before any future live call, run exactly one fresh synthetic direct-SDK no-search preflight and require nonempty `OK` text, a response ID, positive output tokens, explicit success metadata, zero retries, and no connection error. Only after that gate should the exact locked 25-row CSV run through `--live-backend direct-sdk`, serially, with zero SDK retries and preserved artifacts.
