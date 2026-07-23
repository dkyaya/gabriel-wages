# Tier 1 Wave 2 coordinator 150-row dry-run review — 2026-07-22

## Decision

PASS. The fresh coordinator dry run generated and audited all 150 prompts without making an API, model, hosted-search, or backend call. Together with the passing worker-relay assessment, locked-input audit, and stronger preflight gate, this satisfies the final offline gate for the single authorized full live run.

## Run identity

- Output directory: `tmp/tier1_wave2_coordinator_150row_serial_live_dry_run_2026-07-22_attempt1/`
- Run ID: `all_2026-07-22_195051`
- Locked input SHA-256: `f530932c487cef73aae6d18f19e477697c2b2cfbd85dfd8226e608723d7e750e`
- Prompts generated: 150
- Input rows loaded/requested: 150/150
- Input states: AL, AR, AZ, CO, CT, FL, GA, IA, ID, IN, KS, LA, MA, MD, MI, MN, MO, MS, MT, NC, ND, NH, NM, NV, OH, OK, OR, PA, SC, TN, UT, VA, WA, WI, WV
- Mixed-state authorization: true
- Live hard cap: 150

## Speed/stability settings

- Prompt mode: `compact`
- Search-hints file: `docs/analysis/municipality_search_hints_2026-07-22.csv`
- Search-hints file SHA-256: `888583fa7d4d55111f47424eec9d9af8a2c3e3c1b49533d09fdea6fb8a613be3`
- Search hints matched: 150/150
- Fixed fallback sleep: 5.0 seconds
- Adaptive sleep enabled: true
- Adaptive min/base/max/backoff: 3.0/5.0/15.0/10.0 seconds
- Adaptive stability/failure windows: 25/2
- Planned aggregate sleep: 522.0 seconds
- Dry-plan observed sleep-level range: 3.0–5.0 seconds

## Lifecycle and timing artifacts

- `live_attempted=false`
- `backend_call_returned=false`
- `execution_status=dry_run_completed`
- `row_timing.csv` exists with exactly 150 rows.
- Every timing row has `success_status=dry_run_planned`, `parse_status=not_attempted`, `live_attempted=no`, and `pacing_mode=adaptive`.
- Timing-row municipality IDs exactly preserve locked input order.

## Prompt contract audit

All 150 prompts passed every identity, hint, and contract check. Each prompt contains:

- municipality name and state;
- locked internal `municipality_id`;
- exact `government_name`;
- Census government ID;
- county geography/context, explicitly not an alternate employer;
- requested safety and ordinary non-safety units and authoritative wage-setting materials;
- all five deterministic query hints from the locked input/search-hints file;
- verification cautions;
- exact-employer, unit-type, source-type, year-evidence, overlap, and comparator-role controls;
- explicit permission to return no candidates when none qualify;
- separate blocked/unreadable and dead/unreachable treatment;
- exact-known-source and possible-duplicate controls;
- unverified scout-stage handling and prohibition on verified/ingested/codified/canonical/claim-supporting labels;
- prohibition on making or recommending public-records requests;
- the unchanged structured JSON output schema and enumerated output values.

Programmatic counts were 150/150 for locked identity, five-hint inclusion, strict guardrails, no-candidate guidance, blocked/dead distinction, duplicate controls, unverified-stage handling, public-records prohibition, and schema presence.

## Authorization state

The dry-run gate passes. The coordinator may run the one authorized serialized direct-SDK live process into the fresh Wave 2 output directory, using the exact compact/search-hints/adaptive settings recorded above. The preflight probe remains quarantined and excluded from official accounting.
