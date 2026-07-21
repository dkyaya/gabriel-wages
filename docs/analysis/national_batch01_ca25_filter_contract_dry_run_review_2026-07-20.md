# California CA25 Filter-Contract Dry-Run Review

File/batch date: 2026-07-20

Execution/review date: 2026-07-21

Stage: prompt-only dry-run review. No model/API request, hosted web search, source opening, PDF download, public-records request, source verification, ingestion, codification, canonical-data edit, queue rebuild, coverage promotion, or claim use occurred.

## Gate result

**PASS.** Run `ca_2026-07-21_100843` built exactly 25 minimal prompts from `national_batch01_ca25_scout_input_2026-07-20.csv`. Metadata records `mode=dry_run`, `municipalities_requested=25`, and `live_attempted=false`. The output directory contains only `prompt_preview.md` and `run_metadata.json`.

The project `.venv/bin/python` interpreter was used because the latest relay records the shell `python` and `python3` shims as unusable.

## Locked municipality order

Los Angeles; Sacramento; San Diego; San Francisco; Fresno; San Jose; Long Beach; Oakland; Bakersfield; Anaheim; Riverside; Stockton; Chula Vista; Fremont; Modesto; Oxnard; Santa Rosa; Salinas; Vallejo; Redding; Chico; Visalia; Santa Barbara; Berkeley; Palo Alto.

## Required checklist

| Required check | Result | Evidence from locked input and rendered preview |
|---|---|---|
| Exactly 25 municipalities are included | PASS | Input parse-back and preview section count are both 25; municipality and Census IDs are each unique. |
| No already scout-covered rows are included | PASS | Every row has `coverage_status_before_run=not_scouted`, `already_scouted_status=no`, and zero failed-connection attempts; pre-run California coverage was 0 of 483. |
| No prohibited government types are included | PASS | All 25 rows are authoritative `government_type=municipal`, `geography_type=place` employers. San Francisco is the universe's California-specific consolidated `CITY AND COUNTY OF SAN FRANCISCO` municipal-place employer, not a substitute county row. |
| Exact municipal employer and Census government ID appear for every row | PASS | Every prompt contains `Target employer only: <government_name> municipal government, Census government ID <census_gov_id>` matching its input row. |
| Wrong-employer exclusions appear | PASS | Every prompt excludes counties, townships, schools, transit, housing, port/airport, park/recreation, fire/water/utility and other special districts, regional/state/federal bodies, universities, and private providers. County context is expressly non-employer context. |
| Non-safety means ordinary municipal/civilian material | PASS | Every prompt defines `non_safety` as ordinary municipal/civilian employees or authoritative civilian wage-setting material and asks for clerical, public works, library, citywide civilian, or comparable material. |
| Safety CBAs cannot satisfy non-safety requests | PASS | Every prompt states verbatim that a police, fire, or other safety CBA can never satisfy a non-safety comparator request; EMS, corrections, dispatch, and other safety substitutions are also excluded in row context. |
| Context-only sources are labeled separately | PASS | Every prompt requires separate `candidate_stage` and `context_only_flag` labels; agenda covers, summaries, memos, minutes, and sources outside the target can appear only as clearly labeled context unless they include a binding underlying document. |
| `blocked_or_unreadable` is separate from `dead_or_unreachable` | PASS | Every prompt reserves dead/unreachable for observed 404/410/DNS/equivalent failure and uses blocked/unreadable for a live source whose contents cannot be inspected. Both appear as distinct schema values. |
| Visible cycle-year evidence is requested | PASS | Every prompt requires years from a cover/title, duration clause, award period, or other operative text, preserves `visible_year_evidence`, and labels index/snippet/model-only years unclear or uncertain. |
| Duplicate/known-source risk is addressed where context exists | PASS | Local context says no canonical or queued city source is known before the run, while every prompt still requires `duplicate_risk`, prevents exact known sources from becoming new qualifying rows, and directs within-run source duplication to later review. |
| Empty candidate lists are allowed | PASS | Every prompt says it is acceptable to find no qualifying source and to return an empty `candidates` list rather than invent a URL. |
| Output remains unverified scout-stage lead data | PASS | Every prompt states that returned items remain unverified scout-stage data and must not be described as verified, ingested, codified, or claim-supporting. |

Additional hard boundary: every row tells the scout to search only public material and not make or recommend a CPRA/PRA or another public-records request.

## Reconciliation checks

The authoritative municipality universe, current coverage ledger, county crosswalk, manifest, and queue reconcile for all 25 rows. All five California manifest anchors are included. No selected municipality ID appears in the pre-run national queue or canonical corpus. The batch spans 20 counties and contains only exact municipal employers. Likely source availability and matched-cycle value remain unverified planning hypotheses.

## Gate decision

The dry-run gate passes every required item, so one synthetic direct-SDK smoke preflight is permitted. That smoke must use exactly `Reply with OK.`, `gpt-5.4-nano`, the Harvard HUIT `/v2` base, no tools/search, one request, at most 30 seconds, and zero retries. The live CA25 scout remains prohibited unless that smoke returns nonempty text, a response ID when exposed, positive output tokens, explicit model-response success, and no connection error.
