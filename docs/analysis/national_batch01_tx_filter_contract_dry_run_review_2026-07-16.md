# National Batch 01 Texas Filtering-Contract Dry-Run Review

Date: 2026-07-16  
Scope: San Antonio, Austin, and Houston only  
Mode: `minimal`, dry run; no GABRIEL, model, API, ingestion, or codification call

## Result in plain English

The stricter minimal prompt passed the Texas preview review. All three prompts still identify the exact `CITY OF ...` employer and Census government ID, retain the city-specific research purpose, exclude alternate government and private-provider employers, and label every output as unverified scout-stage lead data. The revised contract now prevents a safety agreement from filling a non-safety request, makes agenda/summary material context-only unless the binding source is attached, permits an empty result, and asks the model to expose completeness, comparator role, wrong-employer risk, and the reason verification is needed.

This was prompt generation only. It produced no candidate sources and did not test whether a live model will obey the new distinctions.

## Exact dry-run command

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state TX \
  --municipalities-csv docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/TX/national_batch01_tx_filter_contract_dry_run_2026-07-16 \
  --prompt-mode minimal
```

The command exited 0 and reported three municipality prompts.

## Metadata and artifacts

- Run ID: `tx_2026-07-16_180400`
- State: `TX`
- Mode: `dry_run`
- Prompt mode: `minimal`
- Municipalities requested: 3
- Cities, in input order: San Antonio, Austin, Houston
- Live attempted: `false`
- Live succeeded: `false`
- Prompt preview: `tmp/gabriel_state_source_scout/TX/national_batch01_tx_filter_contract_dry_run_2026-07-16/prompt_preview.md`
- Metadata: `tmp/gabriel_state_source_scout/TX/national_batch01_tx_filter_contract_dry_run_2026-07-16/run_metadata.json`

The saved prompt preview is the exact prompt text that the current runner would submit in a separately authorized live run.

## Filtering-contract checklist

| Check | San Antonio | Austin | Houston |
|---|---:|---:|---:|
| Exact `CITY OF ...` employer | Pass | Pass | Pass |
| Census government ID | Pass: `175988` | Pass: `176394` | Pass: `176169` |
| Row-aware research target retained | Pass: civilian wage-setting/comparator only | Pass: ordinary comparator distinct from EMS | Pass: police, fire, ordinary non-safety, repeat cycle, mechanism evidence |
| `non_safety` restricted to ordinary civilian employees/material | Pass | Pass | Pass |
| Safety CBA explicitly barred as non-safety comparator | Pass | Pass | Pass |
| EMS and other safety-adjacent exclusions present | Pass | Pass | Pass |
| County/school/transit/health/regional/special/private substitutes barred | Pass | Pass | Pass |
| Agenda covers/summaries/memos/minutes labeled context-only unless binding document attached | Pass | Pass | Pass |
| Dead/unreachable/insufficient sources distinguished | Pass | Pass | Pass |
| Empty candidates list explicitly allowed | Pass | Pass | Pass |
| Six new filtering fields in JSON schema | Pass | Pass | Pass |
| Output explicitly unverified and not ingested/codified/claim-supporting | Pass | Pass | Pass |

City-specific findings:

- **San Antonio:** The prompt asks for an ordinary general-municipal non-safety unit or authoritative civilian wage-setting pathway and says not to spend the wave rediscovering existing safety contracts. The new universal rule explicitly prevents the prior fire-CBA leakage from satisfying this request.
- **Austin:** The prompt preserves the separate instruction that EMS cannot count as the requested ordinary general-municipal comparator. It also permits an empty result, matching the prior verification finding that no bounded in-window ordinary comparator was established.
- **Houston:** The prompt retains police, fire, ordinary non-safety, repeat-cycle, contract-year, and public impasse/arbitration/factfinding priorities. The new document rules separate a full agreement from the agenda cover and settlement-summary memo types observed in verification.

## Prompt length

The exact prompt bodies are 565 words for San Antonio, 555 for Austin, and 591 for Houston. The earlier row-aware previews were 323, 313, and 349 words. Most of the increase is the explicit controlled output schema and two compact filtering paragraphs. Each prompt still caps results at two per requested unit/source type, requests JSON only, and remains a single bounded discovery instruction. This is considered reasonable for `prompt_mode=minimal`, but the next live run should compare token/cost and parse behavior against the Texas baseline.

## Lightweight checks

`scripts/test_gabriel_state_source_scout_prompt.py` passed all no-network checks:

```text
PASS: row-aware prompt retains contextual fields
PASS: three-column input fallback remains valid
PASS: strict unit/document/no-candidate guidance is present
PASS: new candidate-stage fields survive parsing and remain unverified
```

The parser preserves `unclear` instead of coercing ambiguity to `non_safety`, retains all six new fields, and leaves stage separation at `verification_status=unverified` and `promotion_status=raw_model_output`. Context-only, incomplete, dead, and wrong-employer-risk leads receive deterministic priority penalties but remain visible for audit.

## Remaining risks before another live scout

- A live model can still misclassify a unit or document despite clear instructions; direct verification remains mandatory.
- Source-owner and employer names remain model assertions until the linked source is opened.
- A full-looking PDF can still be partial, superseded, outside 2014–2024, or irrelevant to the required matched cycle.
- The expanded schema may increase output tokens or reduce parse reliability. The next small live slice should monitor failures, token cost, and empty-result behavior.
- Deterministic priority is triage only. It does not verify a source and must not promote a row into ingestion or claims.

## Recommendation

The filtering contract is ready for bounded national scaling, not bulk release. The next move should be one small, separately authorized state slice from the existing national manifest, followed immediately by source verification before another slice is released. Do not re-scout Texas merely to test this contract, do not start a blind 100-city run, and stop if the next slice shows material wrong-unit, wrong-employer, context-only, or parse leakage.
