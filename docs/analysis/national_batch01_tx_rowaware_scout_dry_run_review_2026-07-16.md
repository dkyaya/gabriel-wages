# National Batch 01 Texas Row-Aware Scout Dry-Run Review — 2026-07-16

## Outcome

The row-aware minimal prompt path passes the requested dry-run review for all three Texas targets: San Antonio, Austin, and Houston. The prompts now use the full contextual input's exact city employer, Census government ID, expected units/source types, selection purpose, verification cautions, and county context. They remain bounded at up to two candidates for each requested unit or source type.

No live GABRIEL scout, model/API call, URL search, source verification, ingestion, or codification was performed. No candidate output exists. Scout-positive, verified, ingested, and codified statuses remain separate.

The prompts are acceptable for a **future, separately authorized** three-municipality live Texas scout, subject to the reliability settings and remaining risks below. This review is not live authorization.

## Prompt-code change reviewed

`scripts/gabriel_state_source_scout.py` now:

- passes each complete municipality row into `build_prompt` as optional context;
- keeps `municipality_id`, `municipality`, and `state` as the only required input columns;
- uses `government_name`, `census_gov_id`, `expected_units_to_search`, `selection_reason`, `verification_notes`, and `county_context_summary` when present;
- falls back to a generic municipal-employer and police/fire/non-safety target when those optional fields are absent;
- adds exact-employer and wrong-employer exclusion instructions;
- applies a strict row-specific search target, including an explicit EMS exclusion when the target says it must be distinct from EMS;
- adds `employer`, `contract_years`, and `why_relevant` to the minimal JSON candidate schema; and
- tells the model that every item is an unverified scout-stage candidate lead and cannot be described as verified, ingested, or codified.

The pre-existing full-prompt template and full-prompt output remain unchanged.

## Backward-compatibility check

The legacy three-column input remains valid:

```text
municipality_id
municipality
state
```

An integration-level check loaded `national_batch01_tx_scout_input_runner_minimal_2026-07-16.csv` through `load_municipalities` and built all three minimal prompts successfully. Without optional context, each prompt falls back to:

```text
Target employer only: the municipal government of <municipality>, <state>.
Search target: police; fire; non_safety/general municipal.
```

Thus existing three-column batches do not need to be rebuilt. They gain the common wrong-employer exclusion, expanded JSON fields, and unverified-lead language, but do not require new columns.

## Exact dry-run command

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state TX \
  --municipalities-csv docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/TX/national_batch01_tx_rowaware_dry_run_2026-07-16 \
  --prompt-mode minimal
```

Runner output:

```text
DRY RUN — 3 municipality prompts built for state=TX
prompt_preview=tmp/gabriel_state_source_scout/TX/national_batch01_tx_rowaware_dry_run_2026-07-16/prompt_preview.md
run_metadata=tmp/gabriel_state_source_scout/TX/national_batch01_tx_rowaware_dry_run_2026-07-16/run_metadata.json
```

## Metadata summary

```text
run_id=tx_2026-07-16_163045
state=TX
mode=dry_run
municipalities_requested=3
prompt_mode=minimal
live_attempted=false
live_succeeded=false
live_failure_reason=null
```

The temporary output directory contains exactly `prompt_preview.md` and `run_metadata.json`. The dry-run path returned before importing GABRIEL/pandas, reading credentials, or entering the live-call function. The metadata's model, concurrency, timeout, and sleep values are inert dry-run configuration values, not evidence of a model call.

## Exact prompt previews

### San Antonio

Identifier: `gabriel_state_source_scout_tx_2026-07-16_163045_tx_san_antonio`

```text
Find public URLs for municipal labor source documents for San Antonio, TX.

Target employer only: CITY OF SAN ANTONIO municipal government, Census government ID 175988.
Search target: ordinary general-municipal non-safety unit or authoritative civilian wage-setting pathway (clerical_admin/public_works/sanitation); comparator or wage-study material.
Selection purpose: Urgent named gap: find an ordinary civilian comparison pathway or document its institutional non-availability; do not spend the wave rediscovering the existing safety contracts.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Retain every county relationship shown in county_context_summary; do not use a primary-county shortcut. High-burden large-city review: cap verification to the strongest official/union triad leads before expanding.
County geography context only (not alternate employers): Bexar County [48029; county; government-units-primary=yes; basis=2020_place_by_county] | Comal County [48091; county; government-units-primary=no; basis=2020_place_by_county] | Medina County [48325; county; government-units-primary=no; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item is an unverified scout-stage candidate lead and must not be described as verified, ingested, or codified.
Do not invent URLs. If none found, return an empty candidates list.
```

### Austin

Identifier: `gabriel_state_source_scout_tx_2026-07-16_163045_tx_austin`

```text
Find public URLs for municipal labor source documents for Austin, TX.

Target employer only: CITY OF AUSTIN municipal government, Census government ID 176394.
Search target: ordinary general-municipal non-safety unit distinct from EMS (clerical_admin/public_works/sanitation).
Comparator exclusion: EMS is explicitly excluded and may not count as the requested ordinary general-municipal non-safety comparator.
Selection purpose: Replace the current safety-adjacent EMS comparison with an ordinary general-municipal comparator.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Retain every county relationship shown in county_context_summary; do not use a primary-county shortcut.
County geography context only (not alternate employers): Bastrop County [48021; county; government-units-primary=no; basis=2020_place_by_county] | Hays County [48209; county; government-units-primary=no; basis=2020_place_by_county] | Travis County [48453; county; government-units-primary=yes; basis=2020_place_by_county] | Williamson County [48491; county; government-units-primary=no; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item is an unverified scout-stage candidate lead and must not be described as verified, ingested, or codified.
Do not invent URLs. If none found, return an empty candidates list.
```

### Houston

Identifier: `gabriel_state_source_scout_tx_2026-07-16_163045_tx_houston`

```text
Find public URLs for municipal labor source documents for Houston, TX.

Target employer only: CITY OF HOUSTON municipal government, Census government ID 176169.
Search target: police; fire; at least one ordinary general-municipal non-safety unit (clerical_admin/public_works/sanitation/library); public impasse/arbitration/factfinding material when available; prioritize a repeat cycle for the already represented units.
Cycle evidence emphasis: identify contract years for every candidate and prioritize repeat-cycle sources plus public impasse/arbitration/factfinding evidence.
Selection purpose: Add a repeat cycle for the existing Houston matched-design anchor instead of accumulating a new safety-only city.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Retain every county relationship shown in county_context_summary; do not use a primary-county shortcut. High-burden large-city review: cap verification to the strongest official/union triad leads before expanding.
County geography context only (not alternate employers): Fort Bend County [48157; county; government-units-primary=no; basis=2020_place_by_county] | Harris County [48201; county; government-units-primary=yes; basis=2020_place_by_county] | Montgomery County [48339; county; government-units-primary=no; basis=2020_place_by_county] | Waller County [48473; county; government-units-primary=no; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item is an unverified scout-stage candidate lead and must not be described as verified, ingested, or codified.
Do not invent URLs. If none found, return an empty candidates list.
```

## Pass/fail checklist

### San Antonio

| Requirement | Result | Status |
|---|---|---|
| Exact city employer and Census ID | `CITY OF SAN ANTONIO`, `175988` | PASS |
| Civilian/non-safety comparator emphasis | Ordinary general-municipal non-safety or authoritative civilian wage-setting pathway; comparator/wage-study material | PASS |
| Avoid safety rediscovery | Selection purpose says not to rediscover existing safety contracts; strict-target rule makes out-of-target safety sources context only | PASS |
| Wrong-employer exclusions | County, school, transit, hospital/health, regional, special-district, and private-provider substitution prohibited | PASS |
| Added JSON fields | `employer`, `contract_years`, `why_relevant` present | PASS |
| Unverified-stage language | Explicitly unverified; not verified, ingested, or codified | PASS |

### Austin

| Requirement | Result | Status |
|---|---|---|
| Exact city employer and Census ID | `CITY OF AUSTIN`, `176394` | PASS |
| Ordinary general-municipal comparator | Explicit clerical/public-works/sanitation target | PASS |
| EMS excluded as comparator | Separate sentence says EMS is explicitly excluded and may not count as the requested comparator | PASS |
| Wrong-employer exclusions | County, school, transit, hospital/health, regional, special-district, and private-provider substitution prohibited | PASS |
| Added JSON fields | `employer`, `contract_years`, `why_relevant` present | PASS |
| Unverified-stage language | Explicitly unverified; not verified, ingested, or codified | PASS |

### Houston

| Requirement | Result | Status |
|---|---|---|
| Exact city employer and Census ID | `CITY OF HOUSTON`, `176169` | PASS |
| Police, fire, ordinary non-safety | All three requested in the search target | PASS |
| Repeat-cycle emphasis | Search target and selection purpose both say repeat cycle | PASS |
| Contract-year emphasis | Separate cycle-evidence sentence requires contract years for every candidate; `contract_years` is also required in JSON | PASS |
| Impasse/arbitration/factfinding emphasis | Explicit in search target | PASS |
| Wrong-employer exclusions | County, school, transit, hospital/health, regional, special-district, and private-provider substitution prohibited | PASS |
| Added JSON fields | `employer`, `contract_years`, `why_relevant` present | PASS |
| Unverified-stage language | Explicitly unverified; not verified, ingested, or codified | PASS |

## Concision

The three full-context prompts are 323, 313, and 349 whitespace-delimited words for San Antonio, Austin, and Houston. Legacy three-column fallback prompts are approximately 207-209 words. This is longer than the previous generic minimal prompt because it restores the exact research target and verification safeguards, but it remains a single compact JSON request with at most two candidates per requested unit/source type.

## Remaining risks before a live scout

- A dry-run proves prompt construction and branch safety, not model compliance, web-search quality, URL reachability, or JSON parse success.
- The model may still return an excluded employer despite explicit instructions. Every candidate must be checked against the exact `CITY OF ...` employer before promotion.
- County context is clearly labeled as geography only, but it adds prompt length and county names that the model could still over-weight. If live output shows county leakage, remove county names from the live prompt while preserving them in the input/review ledger.
- `source_owner_type` does not have separate transit/hospital/private-provider values. Excluded sources may be mislabeled as `third_party` or `unknown`; exact employer is therefore more important than owner-type normalization.
- `contract_years` is model-returned text, not verified dates. Cycle overlap must be checked against the actual document.
- San Antonio or Austin may legitimately have no public ordinary municipal CBA. A no-source result is not evidence that no bargaining unit or wage-setting pathway exists.
- Houston may return already represented cycles despite the repeat-cycle instruction. Deduplicate against the corpus only during a later verification stage; do not treat a familiar URL as new evidence.
- The prompt includes the manifest's 2014-2024 verification window while some current agreements extend beyond 2024. Later verification must document whether a source overlaps the intended window and why a successor cycle is useful.
- The dry-run metadata shows default `n_parallels=3` and `sleep_between_prompts=0`; these values were inert because no live path ran and are not the recommended live settings.

## Recommendation

The prompts are now acceptable for a future live Texas scout **if the user separately authorizes that live call**. The recommended future configuration is:

```text
municipalities_csv=docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv
state=TX
max_prompts=3
prompt_mode=minimal
n_parallels=1
sleep_between_prompts=15
search_context_size=low
one bounded retry at most, only for a documented failure
```

Any future response must remain `verification_status=unverified` and `promotion_status=raw_model_output`. The next stage after a separately authorized live run would be candidate parsing and exact-employer/URL/document/date/matched-cycle verification—not ingestion, codification, or automatic coverage promotion.
