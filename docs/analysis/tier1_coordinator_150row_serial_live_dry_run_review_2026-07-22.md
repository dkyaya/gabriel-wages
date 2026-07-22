# Tier 1 Coordinator 150-Row Dry-Run Review

Date: 2026-07-22

Disposition: **PASS — the corrected coordinator prompt contract and offline lifecycle gates passed for all 150 locked rows.**

## Command and artifacts

The coordinator ran the required command with `--dry-run --state ALL --allow-mixed-states`, the locked 150-row input, minimal prompt mode, `--live-hard-cap 150`, and `--sleep-between-prompts 5`.

- Output: `tmp/tier1_coordinator_150row_serial_live_dry_run_2026-07-22/`
- Run ID: `all_2026-07-22_151940`
- Locked-input SHA-256 recorded by metadata: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`
- Prompts: 150.
- Timing rows: 150, all `dry_run_planned` / `not_attempted`, in exact locked-input order.
- Lifecycle: `live_attempted=false`, `backend_call_returned=false`, `live_process_completed=false`, and `execution_status=dry_run_completed`.

## Mixed-state and safety configuration

- `state=ALL`
- `allow_mixed_states=true`
- `live_hard_cap=150`
- `sleep_between_prompts=5.0`
- `n_parallels=1`
- Input states: AK, AL, AR, AZ, CO, CT, DC, FL, GA, HI, IA, ID, IN, KS, KY, LA, MA, MD, MI, MN, MO, MS, NC, NE, NM, NV, OH, OK, OR, RI, SC, SD, TN, UT, VA, WA, and WI. This matches the locked input exactly.

## Independent 150-prompt contract audit

All 150 prompt blocks were parsed and matched row-by-row to the locked CSV and timing ledger. Every prompt contains:

- the exact municipality and state;
- the locked internal `municipality_id`;
- exact `government_name` and Census government ID;
- county context;
- expected units to search and verification notes;
- strict exact-employer, unit, and source-document controls;
- empty-candidate guidance when no qualifying source is found;
- blocked/unreadable versus dead/unreachable separation;
- known-source and duplicate-risk controls;
- unverified scout-stage handling;
- the prohibition on making or recommending public-records requests.

Result: **150/150 PASS**. No live request, API/model call, hosted search, source verification, ingestion, or codification occurred in this dry run.
