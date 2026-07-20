# Illinois 25-Municipality State-Scaling Scout Batch — Dry-Run Review

Date: 2026-07-20

Stage: input preparation and dry prompt review only. No live scout, model/API call, hosted search, source URL opening, PDF download, deep verification, ingestion, codification, queue update, coverage rebuild, or canonical-data/corpus edit occurred.

## Result

The Illinois state-scaling input contains exactly 25 unscouted municipal employers and is suitable for a future separately authorized direct-SDK live scout only after a fresh successful synthetic smoke preflight. It replaces the prior three-city slice as the proposed first 25-row Illinois batch while preserving Chicago, Aurora, and Rockford as rows 1–3.

The shell's `python` and `python3` shims were non-executable, so the project virtual-environment interpreter was used for the otherwise requested command:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

It exited 0. `run_metadata.json` records `mode=dry_run`, `municipalities_requested=25`, `live_attempted=false`, `live_succeeded=false`, `live_process_completed=false`, and `model_response_succeeded=false`. Only the prompt preview and dry-run metadata were created in the run directory.

## Municipalities and selection buckets

The exact ordered input is: Chicago, Aurora, Rockford, Springfield, Naperville, Joliet, Elgin, Peoria, Champaign, Waukegan, Bloomington, Decatur, Evanston, Schaumburg, Bolingbrook, Palatine, Skokie, Des Plaines, Orland Park, Tinley Park, Normal, Belleville, Moline, Carbondale, and Quincy.

| Selection bucket | Count |
|---|---:|
| `claim_register_anchor` | 5 |
| `large_city_state_anchor` | 7 |
| `mid_city_comparison_candidate` | 6 |
| `regional_diversity_candidate` | 5 |
| `clean_municipal_employer_candidate` | 2 |
| **Total** | **25** |

All rows are Illinois `municipal` / `place` governments from the authoritative municipality universe, retain their Census government IDs and full county-crosswalk context, and have `already_scouted_status=no` plus `coverage_status_before_run=not_scouted`. No selected municipal employer has a current national queue candidate or canonical contract row. The batch includes no township government; `TOWN OF NORMAL` is retained because the Census classifies it as a municipal place government, not a township. Same-name or surrounding township governments remain excluded as substitutes.

## Prompt-review checklist

The regenerated preview contains exactly 25 prompt sections. A per-row assertion checked that every prompt includes that row's exact city/village/municipal employer and Census government ID. The following contract checks passed for all 25 prompts:

- County and township governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers are excluded as substitute employers; row-specific cautions additionally name relevant county, university, airport, or same-name-government risks.
- `non_safety` is limited to ordinary municipal/civilian employees or authoritative civilian wage-setting material; police, fire, and other safety CBAs cannot satisfy the non-safety request.
- Context-only and insufficient material must be separately staged; `blocked_or_unreadable` remains distinct from `dead_or_unreachable`.
- Visible cycle-year evidence is required, and the candidate schema requests `visible_year_evidence`, `overlap_with_anchor_cycle`, `duplicate_risk`, `blocked_or_unreadable_flag`, and `cycle_match_notes`.
- Known-source rules are present; the input records that no canonical or queued city/unit/cycle source is known locally rather than inventing an exclusion.
- The matched-cycle purpose is explicit: seek visibly supported police/fire/ordinary-non-safety overlap inside 2014–2024, label non-overlap or uncertainty, and do not call it a completed repair.
- An empty `candidates` list is allowed, and every result is explicitly unverified scout-stage lead data—not verification, ingestion, codification, or claim evidence.

The shared prompt template was narrowly strengthened to add `township governments` to its universal wrong-employer exclusion list. The no-network prompt and direct-SDK regression suites remain green.

## Expected live runtime, token envelope, and post-run accounting

This is an estimate, not an authorization or cost commitment. The successful eight-row Massachusetts serial run averaged about 33 seconds of model-response time per prompt; the successful three-row New Jersey direct-SDK run used roughly 32,500 input, 1,300 reasoning, and 2,550 output tokens per prompt. With one direct-SDK worker, zero retries, and 15-second inter-prompt spacing, 25 prompts imply roughly 20–25 minutes before overhead and an indicative envelope of about 0.74–0.81 million input tokens, 32,000–40,000 reasoning tokens, and 64,000–65,000 output tokens.

Prior GABRIEL-priced runs provide only a rough dollar proxy: the completed 25-row Pennsylvania batch recorded about `$0.2688`; scaling the successful Massachusetts and Texas batches linearly to 25 prompts gives about `$0.2797` and `$0.2890`. Those observations support a planning benchmark of roughly `$0.27–$0.30` for 25 similar prompts. They are not a direct-SDK price quote: HUIT direct-SDK Responses objects do not expose billed dollar cost, so a future IL25 run must report actual dollar cost as unavailable unless a separate billing source supplies it.

After a successful future live batch, preserve artifacts; add parsed candidate output to the durable national queue; then rebuild municipality/state/county discovery coverage. Successful parseable empty outputs count as scout coverage but not as evidence that no source exists; connection-only failures remain distinct and excluded from successful discovery coverage. All returned rows remain unverified scout-stage leads until a separately authorized coordinated verification wave.

## Next step

IL25 is acceptable for a separately authorized direct-SDK live scout only after a fresh synthetic no-search smoke preflight succeeds with the expected `OK` response, response ID, positive output tokens, exactly one request, and no web search. If separately authorized after that gate, run the locked IL25 input serially with `--live-backend direct-sdk`, `--n-parallels 1`, and `--direct-sdk-max-retries 0`; then queue and account for successful discovery output without opening every returned URL. Deep verification, ingestion, codification, and claim use remain separate later stages.
