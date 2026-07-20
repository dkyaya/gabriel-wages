# New York 25-Municipality State-Scaling Scout Batch — Dry-Run Review

Date: 2026-07-20

Stage: input preparation and dry prompt review only. No live scout, model/API call, hosted search, source URL opening, PDF download, verification, ingestion, codification, queue/coverage rebuild, canonical-data/corpus edit, or Bloomington retry occurred.

## Result

The New York input contains exactly 25 untouched city governments and passed the minimal prompt-contract dry run. New York is the best next state because it contains the next five untouched high-priority national manifest targets at ranks 19–23 plus five additional manifest replication cities, while supporting a geographically broad 25-city sample without towns/townships or special districts.

The shell's `python` and `python3` shims remained unusable, so the project virtual-environment interpreter was used for the requested local-only command:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state NY \
  --municipalities-csv docs/analysis/national_batch01_ny25_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/NY/national_batch01_ny25_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

The command exited 0. `run_metadata.json` records run ID `ny_2026-07-20_194038`, `mode=dry_run`, `municipalities_requested=25`, `live_attempted=false`, `live_succeeded=false`, `live_process_completed=false`, and `model_response_succeeded=false`. The output directory contains only `prompt_preview.md` and `run_metadata.json`.

## Locked municipalities

The exact ordered input is:

1. Buffalo
2. Rochester
3. Syracuse
4. Yonkers
5. Albany
6. New York
7. Utica
8. Schenectady
9. White Plains
10. New Rochelle
11. Mount Vernon
12. Troy
13. Niagara Falls
14. Binghamton
15. Poughkeepsie
16. Newburgh
17. Middletown
18. Ithaca
19. Saratoga Springs
20. Watertown
21. Kingston
22. Jamestown
23. Elmira
24. Rome
25. Auburn

| Selection bucket | Count |
|---|---:|
| `claim_register_anchor` | 5 |
| `large_city_state_anchor` | 3 |
| `mid_city_comparison_candidate` | 6 |
| `regional_diversity_candidate` | 7 |
| `clean_municipal_employer_candidate` | 4 |
| **Total** | **25** |

All 25 are authoritative Census `municipal` / `place` records whose government names begin `CITY OF`. All have `already_scouted_status=no`, `coverage_status_before_run=not_scouted`, zero prior failed attempts, no national queue row, and no canonical-corpus overlap. New York City preserves all five county relationships; the other 24 rows are single-county cities. No selected row is Bloomington IL or any town/township, village, county, authority, district, school, or private employer.

## Prompt-review checklist

The preview contains exactly 25 municipality sections in the input order. A row-by-row assertion confirmed that every section contains the exact `CITY OF ...` employer name, Census government ID, and full county-context string. The following checks passed in all 25 prompts:

- County and township governments, school districts, transit authorities, housing authorities, park districts, regional authorities, special districts, and private providers cannot substitute for the target city employer. Row-level cautions also exclude the State of New York, MTA/transit agencies, universities, and fire/water districts.
- `non_safety` is limited to ordinary municipal/civilian employees or authoritative civilian wage-setting material. Police, fire, or any other safety CBA cannot satisfy the non-safety request.
- Context-only and insufficient leads have separate candidate stages and do not count as qualifying agreements or comparators.
- `blocked_or_unreadable` remains separate from `dead_or_unreachable`; dead is reserved for observed 404/410/DNS or equivalent evidence.
- Contract cycles require visible support through `visible_year_evidence`; snippet/model inference must remain uncertain.
- Known-source and duplicate rules require `duplicate_risk=exact_known_source` when applicable. The input accurately says that no canonical or queued source-cycle context is known locally rather than inventing exclusions.
- The matched-cycle purpose is explicit: seek police/fire/ordinary-non-safety overlap during 2014–2024 and label non-overlap or uncertainty rather than calling it a completed repair.
- An empty `candidates` list is allowed.
- Every returned item remains unverified scout-stage lead data and cannot be described as verified, ingested, codified, or claim-supporting.

Dry-run behavior is unchanged: no live backend was selected, credentials were not needed, and no research request was issued.

## Expected future live envelope

This is planning information, not live authorization or a billing quote. The Illinois 25-row direct-SDK run took about 28 minutes, with 24 successful responses averaging roughly 50 seconds and 15-second serial spacing. It used 1,028,386 input, 49,032 reasoning, and 79,974 output tokens. New York contains a more complex flagship employer and a wide city-size range, so a prudent 25-row serial estimate is approximately 28–35 minutes, 0.9–1.2 million input tokens, 40,000–60,000 reasoning tokens, and 70,000–95,000 output tokens, assuming no retries.

Prior GABRIEL-priced 25-prompt comparisons suggested roughly `$0.27–$0.30`, but that is only a historical planning proxy. The HUIT direct-SDK Responses objects used for current scouting do not expose billed dollar cost, so any future NY25 run must report actual direct-SDK dollar cost as unavailable unless an independent billing source supplies it.

## Queue and coverage behavior after a future live run

If a separately authorized run later succeeds:

1. preserve prompt, metadata, raw response, parsed candidates, failed parses, failure ledger, and usage/cost artifacts;
2. create the task-level unverified candidate handoff without opening every URL;
3. add returned rows to the national queue and apply only scout metadata for light triage;
4. count each parseable candidate or parseable empty municipality as successful discovery coverage;
5. retain connection/timeout-only rows separately and exclude them from successful coverage;
6. rebuild municipality/state/county scout accounting while leaving verification, ingestion, canonical, codified, and claim fields separate.

No queue or coverage output changed during this dry-run task.

## Readiness and next step

NY25 is acceptable for a future separately authorized direct-SDK live scout. Before any live execution, a fresh one-request direct-SDK no-search smoke preflight remains mandatory and must return expected `OK` text, a response ID, positive output tokens, explicit success, and no connection error. Only after that gate and separate live authorization should the exact locked 25-row input run serially with `--live-backend direct-sdk`, `--n-parallels 1`, 15-second spacing, and zero retries.

Do not launch it automatically. Do not verify Illinois links, retry Bloomington, open New York source URLs, ingest, codify, or promote any scout-stage lead during preparation.
