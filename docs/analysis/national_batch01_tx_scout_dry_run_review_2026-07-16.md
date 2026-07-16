# National Batch 01 Texas Scout Dry-Run Review — 2026-07-16

## Outcome

The Texas slice of national batch 01 contains exactly three authoritative manifest rows, in national priority order:

1. San Antonio (`priority_rank=1`, `municipality_id=tx_san_antonio`, Census government ID `175988`, `CITY OF SAN ANTONIO`)
2. Austin (`priority_rank=4`, `municipality_id=tx_austin`, Census government ID `176394`, `CITY OF AUSTIN`)
3. Houston (`priority_rank=13`, `municipality_id=tx_houston`, Census government ID `176169`, `CITY OF HOUSTON`)

The full input is an exact 22-field projection of rows satisfying both `wave_id=NWMS-2026-07-16-01` and `state=TX` in `next_wave_municipality_scout_manifest_2026-07-16.csv`. The minimal input is an exact, order-preserving projection of `municipality_id`, `municipality`, and `state`, the three columns required by `gabriel_state_source_scout.py`.

No live GABRIEL scout, model/API call, URL search, source verification, ingestion, or codification was performed. No scout result exists to promote. Scout-positive, verified, ingested, and codified statuses remain separate.

## Inputs

- Full planning/context input: `docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv`
- Minimal runner input: `docs/analysis/national_batch01_tx_scout_input_runner_minimal_2026-07-16.csv`
- Authoritative source: `docs/analysis/next_wave_municipality_scout_manifest_2026-07-16.csv`

The full CSV retains all manifest fields, including the requested identifiers, geography, county context, selection logic, claim/source-need connection, expected units, verification notes, and workflow-status fields. The minimal file intentionally contains only the three columns consumed by the current runner.

## Exact dry-run command and result

Command executed:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state TX \
  --municipalities-csv docs/analysis/national_batch01_tx_scout_input_runner_minimal_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/TX/national_batch01_tx_dry_run_2026-07-16 \
  --prompt-mode minimal
```

Runner output:

```text
DRY RUN — 3 municipality prompts built for state=TX
prompt_preview=tmp/gabriel_state_source_scout/TX/national_batch01_tx_dry_run_2026-07-16/prompt_preview.md
run_metadata=tmp/gabriel_state_source_scout/TX/national_batch01_tx_dry_run_2026-07-16/run_metadata.json
```

The metadata confirms:

```text
mode=dry_run
state=TX
municipalities_requested=3
prompt_mode=minimal
live_attempted=false
live_succeeded=false
live_failure_reason=null
```

Only `prompt_preview.md` and `run_metadata.json` were created in the temporary run directory. The dry-run path returned before importing GABRIEL/pandas, reading credentials, or entering the live-call function.

## Exact prompt previews

### San Antonio

Identifier: `gabriel_state_source_scout_tx_2026-07-16_161125_tx_san_antonio`

```text
Find public URLs for municipal labor source documents for San Antonio, TX.

Return JSON only. No prose.

Find up to 2 candidates each for:
- police
- fire
- non_safety/general municipal

Prefer official city, state labor-board, or union sources.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "confidence": "high | medium | low"
    }
  ]
}

Do not invent URLs. If none found, return an empty candidates list.
```

### Austin

Identifier: `gabriel_state_source_scout_tx_2026-07-16_161125_tx_austin`

```text
Find public URLs for municipal labor source documents for Austin, TX.

Return JSON only. No prose.

Find up to 2 candidates each for:
- police
- fire
- non_safety/general municipal

Prefer official city, state labor-board, or union sources.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "confidence": "high | medium | low"
    }
  ]
}

Do not invent URLs. If none found, return an empty candidates list.
```

### Houston

Identifier: `gabriel_state_source_scout_tx_2026-07-16_161125_tx_houston`

```text
Find public URLs for municipal labor source documents for Houston, TX.

Return JSON only. No prose.

Find up to 2 candidates each for:
- police
- fire
- non_safety/general municipal

Prefer official city, state labor-board, or union sources.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unknown",
      "document_title": "...",
      "union_name": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | pay_plan | index_page | context_only | unknown",
      "confidence": "high | medium | low"
    }
  ]
}

Do not invent URLs. If none found, return an empty candidates list.
```

## Cross-cutting prompt review

### Municipality identity and state

All three preview headings, prompt bodies, identifiers, and input rows contain the correct municipality name and `TX`. The authoritative full input also preserves the exact Census municipal-government identity and all county relationships.

The prompt itself does **not** carry `government_name`, `census_gov_id`, `government_type`, or `county_context_summary`. “Municipal labor source documents” is a useful general cue, but it does not definitively identify `CITY OF SAN ANTONIO`, `CITY OF AUSTIN`, or `CITY OF HOUSTON` as the only target employer.

### Separation of unit searches

The prompt visibly requests police, fire, and non-safety/general-municipal candidates as three separate categories and caps each at two. That supports category separation better than one undifferentiated source request.

However, the runner uses only the minimal CSV's three columns and ignores the full input's `expected_units_to_search`, `selection_reason`, and `verification_notes`. Consequently, every municipality receives the same three-category prompt even when the national manifest specifies a narrower repair.

### Employer-confusion risk

The current prompt does not expressly exclude county governments, independent school districts, transit authorities, hospital/health districts, regional authorities, or private EMS/fire providers. These are potential false-positive classes, not claims that any specific source exists. The risk is material because all three municipalities are large, multi-county places and the prompt supplies neither exact employer name nor county context.

An ordinary non-safety comparison must be an employee unit or wage-setting pathway of the same city employer. A county, school district, transit authority, hospital/health district, or private provider cannot silently substitute for that within-city comparator.

### Unverified-status discipline

The minimal prompt does not say that returned URLs are unverified leads, and its requested JSON does not include verification/promotion status. The runner's parser independently and correctly hard-codes every eventual live candidate row to `verification_status=unverified` and `promotion_status=raw_model_output`. Thus the code preserves status separation, but the prompt does not communicate it to the model. No live output was generated in this task.

### Minimal-output scoring mismatch

The candidate parser and provenance scorer accept/use `employer`, `contract_years`, and `why_relevant`, but the minimal prompt does not request those fields. A future minimal-mode live response will therefore usually leave them blank, weakening exact-employer review, date-window review, relevance review, and provenance scoring.

## Municipality-specific findings

### San Antonio — material target mismatch

The authoritative purpose is an urgent **ordinary civilian comparison repair**: find a City of San Antonio general-municipal non-safety unit or authoritative civilian wage-setting pathway, including clerical/administrative, public works, or sanitation material. The manifest explicitly says not to spend this wave rediscovering existing safety contracts.

The dry-run prompt nevertheless asks equally for police, fire, and non-safety candidates. It does not mention the civilian-only priority, comparator/wage-study material, the 2014-2024 window, or `CITY OF SAN ANTONIO` as the exact employer. It could therefore consume candidate slots on already-represented safety material or return non-city material associated with Bexar/Comal/Medina counties, school systems, transit, hospital/health entities, or private providers.

**Assessment:** identity/state correct; unit-target alignment inadequate for live use; employer-confusion risk high without a row-aware prompt.

### Austin — material target mismatch

The authoritative purpose is to replace the current safety-adjacent EMS comparison with an **ordinary City of Austin non-safety comparator distinct from EMS**, such as clerical/administrative, public works, or sanitation.

The dry-run prompt asks for all three generic categories and does not say “distinct from EMS.” It also does not identify `CITY OF AUSTIN` as the exact employer or exclude county, school, transit, hospital/health, regional, or private providers. That creates a direct risk of returning another EMS or safety-adjacent source—the exact design problem this rank-4 target is meant to repair—or material tied to Travis/Bastrop/Hays/Williamson county geography rather than the city employer.

**Assessment:** identity/state correct; explicit non-EMS requirement lost; employer-confusion risk high; current prompt should not be used live for the stated repair.

### Houston — broad category alignment but repeat-cycle detail missing

The authoritative purpose is a **repeat-cycle claim anchor**: locate police, fire, and at least one ordinary City of Houston non-safety unit, plus public impasse/arbitration/factfinding material when available, prioritizing cycles not already represented.

The generic police/fire/non-safety categories broadly align with Houston's three-unit target. The prompt does not ask for `contract_years`, a repeat cycle, impasse/arbitration/factfinding material, the 2014-2024 window, or `CITY OF HOUSTON` as the exact employer. It also does not exclude Harris/Fort Bend/Montgomery/Waller county governments, school systems, transit, hospital/health entities, regional authorities, or private providers.

**Assessment:** identity/state correct; broad unit coverage aligned; insufficient cycle and exact-employer detail for an efficient repeat-cycle search.

## Recommended prompt/input change before any live scout

Do **not** run these three prompts live in their current generic minimal form. First make the runner's prompt construction row-aware while keeping the bounded minimal-output approach:

1. Continue supplying the full contextual CSV, and make `load_municipalities`/`build_prompt` use optional `government_name`, `census_gov_id`, `expected_units_to_search`, `selection_reason`, and `verification_notes`. The current loader already retains extra columns; only prompt construction discards them.
2. Add an exact-employer instruction such as: `Target employer only: CITY OF AUSTIN municipal government (Census government ID 176394).`
3. State the row-specific unit target. San Antonio should prioritize only the ordinary civilian comparator pathway; Austin should prioritize a non-EMS ordinary municipal comparator; Houston should search the full triad with repeat-cycle emphasis.
4. Add a common exclusion: do not return county-government, school-district, transit-authority, hospital/health-district, regional-authority, or private-provider material as if it were the target city's bargaining unit. A non-target entity may appear only as clearly labeled contextual evidence, not as the municipal comparison unit.
5. Add `employer`, `contract_years`, and `why_relevant` to minimal-mode output because the existing parser/scorer already expects those fields.
6. Tell the model that every return is an unverified candidate lead and cannot be described as verified, ingested, or codified.
7. Preserve the established live reliability settings if a later live run is separately authorized: `n_parallels=1`, `prompt_mode=minimal`, `sleep_between_prompts=15`, one bounded invocation, and one bounded retry only if needed. The dry-run metadata's default `n_parallels=3` and `sleep_between_prompts=0` had no effect because no live path ran; they should not be copied into a future live command.

After implementing the row-aware prompt, rerun dry-run for the same three-row slice and inspect the exact preview again. Only then should a separately authorized live scout be considered. Every future return must remain scout-stage, unverified lead data pending exact-employer, URL, document, date, and matched-cycle verification.
