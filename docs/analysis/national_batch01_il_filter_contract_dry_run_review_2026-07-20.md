# Illinois National Batch 01 — Scout Filter-Contract Dry-Run Review

Date: 2026-07-20

Stage: input preparation and dry prompt review only. No live scout, model/API call, source verification, URL opening, PDF download, ingestion, codification, queue update, coverage rebuild, or canonical-data/corpus edit occurred.

## Result

The Illinois slice is ready for a separately authorized live scout only after a fresh successful direct-SDK synthetic smoke preflight. The prepared slice contains exactly the next three untouched `ready_for_scout` Illinois claim-register targets in wave `NWMS-2026-07-16-01`: Chicago, Aurora, and Rockford. All three are currently `not_scouted` in national municipality coverage, and none has an existing national queue candidate or canonical contract row.

The standard `python`/`python3` shims were not executable in this shell, so the project virtual-environment interpreter was used; it is otherwise the requested dry-run invocation:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

It exited 0 and created only `prompt_preview.md` and `run_metadata.json`. Metadata records `mode=dry_run`, `municipalities_requested=3`, `live_attempted=false`, `live_succeeded=false`, `live_process_completed=false`, and `model_response_succeeded=false`.

## Included municipalities and context

| Priority | Municipality | Exact target employer | Census government ID | Existing scout coverage | Existing canonical/queue context |
|---:|---|---|---:|---|---|
| 14 | Chicago | CITY OF CHICAGO | 162236 | `not_scouted` | None found |
| 15 | Aurora | CITY OF AURORA | 189929 | `not_scouted` | None found; Aurora Township (185079) excluded |
| 16 | Rockford | CITY OF ROCKFORD | 102882 | `not_scouted` | None found; Rockford Township (204332) excluded |

Each row preserves the requested manifest identity, geography, population, county context, selection/claim rationale, expected-unit request, verification note, and recommended scout status. It also adds a matched-set discovery purpose: locate police, fire, and ordinary municipal/civilian non-safety material whose visibly supported operative cycles overlap within 2014–2024. There is no canonical anchor cycle, so the prompt expressly requires non-overlap or unclear evidence to remain labeled rather than treated as a completed repair.

No city has a source/cycle exclusion because no exact canonical or queued source was found in the local canonical contract table or national queue. The input instead records that absence as context, so future results cannot be mistaken for previously verified, ingested, or claim-supporting material.

## Prompt-review checklist

All checks passed for Chicago, Aurora, and Rockford:

| Check | Chicago | Aurora | Rockford |
|---|---|---|---|
| Exact CITY employer and Census ID shown | Yes | Yes | Yes |
| Wrong-employer exclusions remain explicit | Yes | Yes, including Aurora Township | Yes, including Rockford Township |
| Non-safety limited to ordinary municipal/civilian material | Yes | Yes | Yes |
| Safety CBA prohibited as non-safety comparator | Yes | Yes | Yes |
| Context-only material separately labeled | Yes | Yes | Yes |
| `blocked_or_unreadable` distinct from `dead_or_unreachable` | Yes | Yes | Yes |
| Visible cycle-year evidence requested | Yes | Yes | Yes |
| Known-source/duplicate treatment present | Yes; no known source exists | Yes; no known source exists | Yes; no known source exists |
| Matched-cycle purpose clear | Yes | Yes | Yes |
| Empty `candidates` list allowed | Yes | Yes | Yes |
| New filtering fields present | Yes | Yes | Yes |
| Output labeled unverified scout-stage lead data | Yes | Yes | Yes |

The prompt also continues to prohibit county, school, transit, hospital/health-district, regional, special-district, private EMS/fire, airport-police, transit-police, sheriff, corrections, and other safety substitutions. The candidate schema includes `visible_year_evidence`, `overlap_with_anchor_cycle`, `duplicate_risk`, `blocked_or_unreadable_flag`, and `cycle_match_notes`.

## Expected verification burden and next action

The manifest assigns each city a medium expected verification burden. Chicago is nevertheless a large-city bounded-review case: if a future live scout returns leads, later verification should cap work to the strongest official/union matched-set candidates rather than expand source-by-source. Aurora and Rockford require particular government-identity checks because each has a same-name township in the national universe.

Illinois is acceptable for a future separately authorized live scout, but not yet authorized or executed. First run a fresh direct-SDK synthetic no-search smoke preflight in a new output directory. Proceed only if it returns the expected successful `OK` response, response ID, positive output tokens, one request, and no web search. A subsequently authorized live scout should use the locked full-context input, the direct-SDK backend, serial execution, zero retries, and preserved run artifacts. Afterwards, add only successful scout outputs to the candidate queue and rebuild scout coverage; defer deep verification, ingestion, codification, and claim use to their separate coordinated stages.
