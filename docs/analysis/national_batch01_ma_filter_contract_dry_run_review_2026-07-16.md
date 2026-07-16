# National Batch 01 Massachusetts Filtering-Contract Dry-Run Review

Date: 2026-07-16  
Wave: `NWMS-2026-07-16-01`  
Scope: Massachusetts rows only  
Mode: `minimal`, dry run; no GABRIEL, model, API, source search, ingestion, or codification call

## Result in plain English

The Massachusetts slice contains eight municipalities: Somerville, Newton, Boston, Worcester, Arlington, Georgetown, Franklin, and Seekonk. The full-context input is an exact, 22-column projection of the authoritative national manifest filter; no rows were added, re-ranked, or transformed.

The dry run succeeded and produced one prompt per municipality. Every prompt names the exact manifest employer and Census government ID, retains its claim-driven search target, applies the Texas-calibrated filtering contract, permits an empty candidate list, and keeps all output at the unverified scout stage. Metadata confirms that no live call was attempted.

The prompts are acceptable for a separately authorized live Massachusetts scout, provided that verification capacity is reserved for all eight rows before execution and no later state slice is released until the Massachusetts output is reviewed.

## Exact dry-run command

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state MA \
  --municipalities-csv docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/MA/national_batch01_ma_filter_contract_dry_run_2026-07-16 \
  --prompt-mode minimal
```

The command exited 0 and reported eight municipality prompts.

## Metadata and artifacts

- Run ID: `ma_2026-07-16_182108`
- State: `MA`
- Mode: `dry_run`
- Prompt mode: `minimal`
- Municipalities requested: 8
- Model recorded for any future live equivalent: `gpt-5.4-nano`
- Search context recorded for any future live equivalent: `low`
- Live attempted: `false`
- Live succeeded: `false`
- Full-context input: `docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv`
- Prompt preview: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_filter_contract_dry_run_2026-07-16/prompt_preview.md`
- Run metadata: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_filter_contract_dry_run_2026-07-16/run_metadata.json`

The prompt preview contains the exact prompt text the current runner would submit if a live Massachusetts run were separately authorized.

## Exact municipalities and targets

| National rank | Municipality | Municipality ID | Exact target employer | Census government ID | Manifest search target |
|---:|---|---|---|---:|---|
| 2 | Somerville | `ma_somerville` | `CITY OF SOMERVILLE` | `166453` | Ordinary non-safety unit in an overlapping cycle; comparator or impasse material |
| 3 | Newton | `ma_newton` | `CITY OF NEWTON` | `166452` | Ordinary non-safety unit in an overlapping cycle |
| 6 | Boston | `ma_boston` | `CITY OF BOSTON` | `128108` | Fire CBA or impasse/arbitration source overlapping the existing pair |
| 7 | Worcester | `ma_worcester` | `CITY OF WORCESTER` | `106079` | Police base CBA in an overlapping cycle; full non-safety base CBA if available |
| 8 | Arlington | `ma_arlington` | `TOWN OF ARLINGTON` | `166519` | Police CBA or formal impasse source overlapping the exact-cycle pair |
| 9 | Georgetown | `ma_georgetown` | `TOWN OF GEORGETOWN` | `166487` | Fire agreement or authoritative evidence that no municipal fire agreement exists |
| 11 | Franklin | `ma_franklin` | `CITY OF FRANKLIN TOWN` | `194918` | Police, fire, ordinary non-safety, mechanism material, and a repeat cycle |
| 12 | Seekonk | `ma_seekonk` | `TOWN OF SEEKONK` | `166481` | Police, fire, ordinary non-safety, mechanism material, and a repeat cycle |

Arlington, Georgetown, and Seekonk are Census county-subdivision/town-government rows. Their prompts retain the manifest cautions against substituting a same-name city, county, school district, or statistical place. Franklin is a municipal/place row whose exact Census government name is the unusual `CITY OF FRANKLIN TOWN`; the prompt preserves it rather than silently rewriting the employer.

## Prompt-review checklist by municipality

| Check | Somerville | Newton | Boston | Worcester | Arlington | Georgetown | Franklin | Seekonk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Exact `CITY OF ...` or `TOWN OF ...` employer | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Correct Census government ID | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Exact manifest search target retained | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| `non_safety` restricted to ordinary municipal/civilian material | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Safety CBA barred as a non-safety comparator | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| EMS and safety-adjacent exclusions present | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| County/school/transit/health/regional/special/private substitutes barred | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Agenda/summary/memo/minutes context-only rule present | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Dead/unreachable/insufficient source class present | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Empty candidates list explicitly allowed | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Six new filtering fields present | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| Output explicitly unverified and not ingested/codified/claim-supporting | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |

The six new fields present in every prompt are `candidate_stage`, `document_completeness`, `comparator_role`, `wrong_employer_risk`, `context_only_flag`, and `needs_verification_reason`.

## Municipality-specific prompt findings and risks

- **Somerville:** The prompt correctly asks only for an overlapping ordinary non-safety comparator or relevant impasse material. The principal risk is that teacher or other school-district agreements may look like easy non-safety matches; the wrong-employer rule correctly excludes them. Verification must establish an ordinary City unit and overlap with the existing police cycles.
- **Newton:** The prompt similarly focuses on the missing ordinary civilian leg. School agreements and safety documents are likely high-volume distractions. A candidate must be a City of Newton civilian unit, not Newton Public Schools or another same-name employer, and must overlap the 2015–2018 safety cycle.
- **Boston:** The prompt stays narrow: fire CBA or fire impasse/arbitration material overlapping the existing pair. Boston is likely to produce many amendments, ratification summaries, union pages, and later cycles. Verification should prefer the full base agreement or qualifying award and confirm the precise Boston fire unit and cycle.
- **Worcester:** The prompt explicitly favors a police base CBA over another amendment-only source and permits a full non-safety base agreement. The main burden will be distinguishing a full agreement from amendments, memoranda, and agenda records and reconciling the chosen cycle with the existing fire/non-safety pair.
- **Arlington:** The exact `TOWN OF ARLINGTON` employer and Census ID are present, and the county-subdivision caution is retained. Name collision with Arlington governments outside Massachusetts and school-district material remains a meaningful risk. The requested police or formal impasse source must overlap the known fire/public-works exact-cycle pair.
- **Georgetown:** The prompt correctly targets the municipal fire leg and recognizes that a paid or call department may lack a written agreement. An empty scout result cannot prove institutional non-existence. Any positive lead must establish the Town of Georgetown, Massachusetts employer and the actual fire unit; any claimed absence remains unverified unless an authoritative source says so.
- **Franklin:** The exact manifest name `CITY OF FRANKLIN TOWN` and Census ID are present, but that Census label is atypical and may not match how official or union pages title the employer. Verification must accept only sources demonstrably tied to the Franklin, Massachusetts municipal government while guarding against other Franklins. The repeat-cycle, three-unit, and mechanism target may generate the largest candidate set.
- **Seekonk:** The prompt retains the exact town government, county-subdivision caution, three unit types, and repeat-cycle/mechanism purpose. Verification should expect multiple unit documents and amendments and must keep school sources or nonmunicipal fire/EMS providers out of the comparator set.

## Prompt length

The prompt bodies contain:

- Somerville: 518 words
- Newton: 505 words
- Boston: 508 words
- Worcester: 515 words
- Arlington: 544 words
- Georgetown: 549 words
- Franklin: 562 words
- Seekonk: 576 words

The longer prompts are the town/county-subdivision and repeat-cycle rows because their manifest verification cautions and source targets are more detailed. All remain JSON-only, retain the two-leads-per-requested-unit-or-source-type cap, and are within the range established by the Texas filtering preview.

## Expected verification burden

The live slice would be small in call count but moderate-to-high in review burden. Somerville and Newton require careful comparator and cycle matching; Boston and Worcester require full-document-versus-amendment screening; Arlington and Seekonk require exact town-government disambiguation; Georgetown requires a cautious distinction between no lead and authoritative evidence of no agreement; and Franklin/Seekonk may each return police, fire, non-safety, and mechanism leads.

Reserve one complete verification pass for all eight municipality outputs, including raw trace review when a row returns no parsed candidate. A reasonable planning assumption is roughly 12–24 structured leads if the model returns one to three useful rows per municipality, with a higher ceiling because Franklin and Seekonk request several source types. Verification should triage official city/town, Massachusetts labor-board, and official union full documents first. Do not open another state slice until all Massachusetts candidates and material trace-only leads have controlled outcomes.

## Recommendation

The Massachusetts slice is acceptable for a future, separately authorized live scout of exactly these eight rows using the full-context input. A future authorization should bind the state, CSV path, `max-prompts=8`, and output directory; retain the filtering-contract prompt; preserve every raw/parsed/failure/cost artifact; and stop on material wrong-employer, wrong-unit, context-only, or parser leakage.

This dry run is not live authorization. No scout output was generated, verified, ingested, codified, or used for claims. The recommended next move is to review this preview, reserve verification capacity, and—only if separately authorized—run this exact Massachusetts input before preparing another state.
