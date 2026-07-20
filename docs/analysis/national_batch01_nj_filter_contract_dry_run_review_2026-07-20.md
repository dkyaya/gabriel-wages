# National Batch 01 New Jersey Filter-Contract Dry-Run Review

Date: 2026-07-20

Stage: dry-run prompt preview only. No GABRIEL wrapper, model/API call, web search, source verification, ingestion, codification, canonical-data change, or claim promotion occurred.

## Result

The manifest filter produced exactly the expected three-row New Jersey slice: Newark, Jersey City, and Camden. The full-context input parsed successfully, and dry-run mode generated three minimal prompts plus metadata without importing the live GABRIEL path or reading credentials. Every prompt contains the exact city employer, Census government ID, wrong-employer exclusions, strict unit definitions, cycle/duplicate refinements, new output fields, empty-candidate permission, and explicit unverified-stage language.

New Jersey is acceptable for a future, separately authorized three-prompt live scout only after a fresh successful synthetic wrapper smoke preflight. The established smoke helper makes a model/API call, so it was correctly not run during this no-model dry-run task.

## Exact command

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state NJ \
  --municipalities-csv docs/analysis/national_batch01_nj_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/NJ/national_batch01_nj_filter_contract_dry_run_2026-07-20 \
  --prompt-mode minimal
```

## Metadata summary

| Field | Value |
|---|---|
| Run ID | `nj_2026-07-20_160655` |
| Mode | `dry_run` |
| State | `NJ` |
| Municipalities requested | 3 |
| Prompt mode | `minimal` |
| Model recorded for a possible future run | `gpt-5.4-nano` |
| Search-context setting recorded | `low` |
| Live attempted | `false` |
| Live process completed | `false` |
| Model response succeeded | `false` (expected for dry-run; no model was called) |
| Prompt preview | `tmp/gabriel_state_source_scout/NJ/national_batch01_nj_filter_contract_dry_run_2026-07-20/prompt_preview.md` |
| Metadata | `tmp/gabriel_state_source_scout/NJ/national_batch01_nj_filter_contract_dry_run_2026-07-20/run_metadata.json` |

## Exact municipalities and local known-source context

### Newark — Census government ID 130835

Purpose: repair the fire leg against the canonical police 2018-2023 and ordinary non-safety 2020-2023 rows, preferably in their shared 2020-2023 window. The prompt excludes the exact canonical FOP Lodge 12 police 2018-2023, IBT Local 97 municipal-attorney 2020-2023, and Newark Firefighters Union 2013-2015 sources from being returned as new candidates. It also tells the scout that the locally mentioned IAFF Local 1860 2017-2023 term is only a planning trace until a full document and visible operative dates are verified.

Expected burden: medium. Newark has unusually specific canonical exclusions, so duplicate review should be lighter, but any new fire lead must still be checked for exact unit, full-document status, operative dates, and overlap.

### Jersey City — Census government ID 193734

Purpose: replace the known vintage candidate set with current-cycle successors that overlap one another within 2018-2024. The prompt excludes the candidate-stage PSOA 2009-2012 police document, IAFF Local 1066 2009-2015 fire material, and 2015 Public Employees Local 245/246 material from being presented as new current-cycle candidates. It states that these legacy items were not ingested or codified.

Expected burden: medium to high. There is no canonical current anchor, so source verification must establish not only each document's identity but whether a mutually overlapping police/fire/ordinary-civilian set actually exists.

### Camden — Census government ID 170146

Purpose: scout a mutually overlapping police/fire/ordinary non-safety set within 2014-2024, plus formal mechanism material when available. The repository has no canonical or verification-stage Camden source set to exclude. The prompt explicitly distinguishes `CITY OF CAMDEN` from Camden County and other same-named governments.

Expected burden: high. Camden is locally recorded as an unscouted planning target, so any future output will need full employer, unit, source-owner, years, completeness, wage-content, and overlap verification from scratch.

## Prompt-review checklist

| Check | Newark | Jersey City | Camden |
|---|---|---|---|
| Exact `CITY OF ...` employer included | Yes | Yes | Yes |
| Census government ID included | 130835 | 193734 | 170146 |
| County/school/transit/health/regional/special/private exclusions | Present | Present | Present |
| Non-safety restricted to ordinary municipal/civilian material | Present | Present | Present |
| Safety CBA barred from satisfying non-safety request | Present | Present | Present |
| Context-only sources separated | Present | Present | Present |
| `blocked_or_unreadable` separate from `dead_or_unreachable` | Present | Present | Present |
| 404/410/DNS evidence required for dead label | Present | Present | Present |
| Complete executed scanned MOA protection | Present | Present | Present |
| Visible operative year evidence requested | Present | Present | Present |
| Anchor/mutual-overlap purpose explicit | 2020-2023 shared target | 2018-2024 successor overlap | Mutual overlap within 2014-2024 |
| Known-source/duplicate handling | Three exact canonical URLs/cycles | Four legacy unit/cycle exclusions | Explicitly none known |
| Repeat-cycle purpose clear where relevant | Yes, police/non-safety | Yes, current successors | Not applicable; first local slice |
| Empty `candidates` list allowed | Yes | Yes | Yes |
| Five new filtering fields present | Yes | Yes | Yes |
| Output explicitly remains unverified scout-stage data | Yes | Yes | Yes |

## Readiness and next step

The dry-run contract is acceptable for a future separately authorized New Jersey live scout. This judgment covers prompt construction only; it says nothing about source availability or expected model accuracy.

Immediately before that future live run:

1. Run the mandatory one-prompt, no-search synthetic GABRIEL wrapper smoke test in the same wrapper/model/base/auth/network context.
2. Require nonempty response text, a response ID when exposed, no `Connection error.`, positive output tokens, and `model_response_succeeded` or equivalent success metadata.
3. If the smoke test fails, do not run New Jersey. Preserve sanitized failure artifacts.
4. If separately authorized after a successful preflight, keep the live slice to these exact three rows and verify every returned URL before considering another state.
5. Keep all outputs at scout stage until the separate source-verification gate is complete; do not ingest, codify, or use them as claim evidence automatically.
