# Illinois IL25.3 Filter-Contract Dry-Run Review

Date: 2026-07-20

Stage: prompt construction and review only. No model/API call, hosted search, source URL opening, document download, verification, ingestion, codification, canonical-data edit, or claim promotion occurred.

## Result

IL25.3 passed the full-context dry run. The runner built exactly 25 prompts in the locked input order and wrote only the prompt preview and run metadata. Metadata records `mode=dry_run` and `live_attempted=false`. The preview retains the established exact-employer, wrong-employer, unit, document, cycle, duplicate, access-status, empty-output, and unverified-stage contract in every prompt.

IL25.3 is prompt-ready for a future separately authorized direct-SDK live scout, but it is not authorized or executed here. A fresh one-request no-search direct-SDK smoke preflight remains mandatory immediately before any future live run.

## Exact dry-run command

The repository virtual-environment interpreter was used because the shell `python` and `python3` shims remain unusable:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_3_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_3_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

## Metadata summary

- Run ID: `il_2026-07-20_214419`
- State: IL
- Mode: `dry_run`
- Municipalities requested: 25
- Prompt mode: `minimal`
- Model recorded for a possible future run: `gpt-5.4-nano`
- Search context recorded for a possible future run: `low`
- Live attempted: false
- Live succeeded: false
- Model-response success: false, as expected for dry-run mode
- Files written: `prompt_preview.md` and `run_metadata.json` only

## Exact municipality order

1. Lombard
2. Buffalo Grove
3. Park Ridge
4. Streamwood
5. Wheeling
6. Calumet City
7. Northbrook
8. St. Charles
9. Mundelein
10. Elk Grove Village
11. North Chicago
12. Highland Park
13. Batavia
14. Edwardsville
15. Belvidere
16. Kankakee
17. Ottawa
18. Jacksonville
19. Marion
20. East Peoria
21. East Moline
22. Sycamore
23. Alton
24. Rolling Meadows
25. Mattoon

## Selection buckets

| Selection bucket | Rows |
|---|---:|
| `large_city_state_anchor` | 5 |
| `mid_city_comparison_candidate` | 7 |
| `regional_diversity_candidate` | 7 |
| `continuity_with_il25_candidate` | 2 |
| `continuity_with_il25_2_candidate` | 2 |
| `clean_municipal_employer_candidate` | 2 |
| **Total** | **25** |

## Prior-batch and failure exclusions

The local builder joined every row by municipality ID against current coverage and both prior Illinois inputs.

- IL25 is preserved as 23 candidate-positive municipalities, parseable-empty Champaign, and failure-only Bloomington. None of its 25 IDs is in IL25.3.
- IL25.2 is preserved as 22 candidate-positive municipalities plus parseable-empty Granite City, O'Fallon, and Freeport. None of its 25 IDs is in IL25.3.
- Bloomington remains `scout_attempt_failed_connection`, is excluded from IL25.3, and was not retried.
- All 25 IL25.3 rows are `not_scouted`, have zero failed attempts, are absent from the queue, and have no canonical corpus row.

## Rendered prompt-review checklist

The preview contains 25 headings in exact input order. For each of the 25 prompts:

- **Exact target:** exact `CITY OF` or `VILLAGE OF` employer and Census government ID are included.
- **Wrong-employer exclusions:** counties, town/township governments, school districts, transit agencies, housing authorities, park districts, hospital/health districts, regional authorities, fire/water and other special districts, federal installations, universities, and private providers cannot substitute for the target municipality.
- **Ordinary non-safety boundary:** `non_safety` is restricted to ordinary municipal/civilian employees or authoritative civilian wage-setting material.
- **Safety cannot fill non-safety:** police, fire, and other safety CBAs cannot satisfy the ordinary non-safety request.
- **Ambiguous units:** ambiguous material must be labeled `unclear`; the model is told not to force `non_safety`.
- **Context and insufficiency:** context-only and insufficient leads have separate `candidate_stage` and `context_only_flag` values and cannot count as qualifying agreements or comparators.
- **Blocked versus dead:** `dead_or_unreachable` is reserved for observed 404/410/DNS-equivalent evidence; live but inaccessible material is `blocked_or_unreadable`.
- **Visible cycle evidence:** years must be supported by a cover/title, duration clause, award period, or equivalent operative text; snippet/index/model-only years are weak or unclear.
- **Duplicate control:** exact known sources must be context-only with `duplicate_risk=exact_known_source`; the field remains present even though no local source exclusion exists for these untouched municipalities.
- **Matched-cycle purpose:** every prompt asks for visibly supported overlapping 2014-2024 police/fire/ordinary-non-safety cycles and labels non-overlap or uncertainty.
- **Empty result allowed:** an empty candidates list is explicitly allowed when no qualifying source is found.
- **Stage quarantine:** every returned item must remain unverified scout-stage lead data and cannot be described as verified, ingested, codified, or claim-supporting.

Programmatic preview checks found exactly 25 occurrences of every required common clause, 25 exact employer/ID matches, 25 unique municipality IDs, and 25 unique Census IDs.

## Expected future live runtime and usage

Observed 25-row direct-SDK state runs provide the planning envelope:

| Run | Successful responses | Approximate elapsed time | Input tokens | Reasoning tokens | Output tokens | Direct billed cost |
|---|---:|---:|---:|---:|---:|---|
| IL25 | 24 plus one timeout | about 28 minutes | 1,028,386 | 49,032 | 79,974 | unavailable |
| IL25.2 | 25 | about 25 minutes from response-time plus spacing | 950,865 | 48,614 | 78,927 | unavailable |
| NY25 | 25 | about 24 minutes | 955,600 | 43,749 | 68,985 | unavailable |

A future IL25.3 live run should therefore be planned for roughly 24-30 minutes, approximately 0.95-1.05 million input tokens, 44,000-50,000 reasoning tokens, and 69,000-80,000 output tokens, assuming the established serial worker, low search context, and 15-second inter-prompt spacing. Direct-SDK/HUIT billed dollar cost remains unavailable; an actual dollar amount should not be invented. The older roughly `$0.27-$0.30` GABRIEL-priced 25-row comparison is only a non-comparable historical proxy, not an IL25.3 direct-SDK cost estimate.

## Expected queue and coverage behavior after a future live run

This dry run changes neither the 318-row national queue nor the 113 successfully covered municipalities. After a separately authorized live run:

1. Preserve raw responses, prompt, metadata, parsed candidates, failed parses, failure ledger, and usage/cost artifacts.
2. Normalize all parsed candidates as `unverified_scout_candidate` and add them to the durable national queue without source verification.
3. Count every municipality with a parseable candidate or parseable empty response as successful source-discovery coverage.
4. Keep any connection-only/zero-response failure separate and excluded from successful coverage.
5. If all 25 rows return parseable responses, national coverage would rise from 113 to 138 and Illinois coverage from 49 to 74; the candidate queue would rise by the actual number of returned candidates.
6. Keep verification, ingestion, canonical, codified, and claim statuses unchanged.

## Disposition and next step

IL25.3 is acceptable for a future separately authorized direct-SDK live scout. Do not run it automatically. First require a fresh synthetic no-search direct-SDK preflight with exact `Reply with OK.`, one request, no tools/search, no retries, a response ID, positive output tokens, explicit success metadata, and no connection error. Only after that gate and separate authorization should the exact locked 25-row input run serially. Verification and ingestion must remain deferred.
