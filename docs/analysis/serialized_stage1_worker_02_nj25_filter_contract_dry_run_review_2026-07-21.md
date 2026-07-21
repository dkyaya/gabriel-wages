# Serialized Stage 1 Worker 02 NJ25 Dry-Run Review

Date: 2026-07-21

Disposition: **pass; synthetic direct-SDK smoke preflight is permitted**

## Result

The fresh dry run completed with exit code 0 and built exactly 25 minimal-mode prompts from the unchanged locked input `parallel_worker_02_nj25_scout_input_2026-07-21.csv`. Metadata records `mode=dry_run`, `execution_status=dry_run_completed`, `municipalities_requested=25`, and `live_attempted=false`. No model, API, web-search, or source request occurred.

The locked input contains 25 distinct New Jersey municipality IDs and 25 distinct Census government IDs. Every row is an authoritative `municipal` / `place` employer, has `worker_id=parallel_worker_02`, remains `not_scouted` in the pre-run national coverage snapshot, has no recorded connection-only failure, and has no current national queue row. The accepted city, town, borough, or municipality form never substitutes a township or other prohibited government.

## Prompt-contract checklist

All 25 rendered prompts passed every required check:

- the exact municipal employer and Census government ID appear;
- county, township, school, transit, port/airport, housing, park, special-district, regional, state/federal, university, and private-provider substitutions are excluded where applicable;
- `non_safety` means ordinary municipal/civilian employees or authoritative civilian wage-setting material;
- police, fire, EMS, and other safety material cannot satisfy the non-safety request;
- context-only sources are labeled separately and do not count as qualifying agreements or comparators;
- `blocked_or_unreadable` is distinct from an observed `dead_or_unreachable` location;
- contract years require visible cover/title, duration-clause, award-period, or equivalent operative evidence;
- known-source and duplicate risk must be labeled, including `exact_known_source` when applicable;
- an empty `candidates` list is explicitly permitted;
- public-records requests are prohibited; and
- every returned row remains unverified scout-stage lead data, not verified, ingested, codified, or claim-supporting evidence.

Artifacts:

- `tmp/serialized_stage1_worker_02_nj25_dry_run_2026-07-21/prompt_preview.md`
- `tmp/serialized_stage1_worker_02_nj25_dry_run_2026-07-21/run_metadata.json`

This review authorizes only the separately approved one-request synthetic no-search smoke. The NJ25 live scout remains conditional on smoke success.
