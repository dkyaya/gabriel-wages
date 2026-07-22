# Tier 1 Coordinator Retry Dry-Run Review

Date: 2026-07-22

Disposition: **PASS — all 150 locked rows passed the fresh offline retry prompt and lifecycle audit.**

## Run

- Output: `tmp/tier1_coordinator_150row_serial_live_retry_dry_run_2026-07-22_attempt1`.
- Run ID: `all_2026-07-22_155821`.
- Locked-input SHA-256: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`.
- Prompts / timing rows: 150 / 150, in exact rank and worker order.
- Timing lifecycle: all 150 `dry_run_planned` / `not_attempted`.
- `state=ALL`; `allow_mixed_states=true`; `live_hard_cap=150`; `sleep_between_prompts=5.0`; `n_parallels=1`.
- `live_attempted=false`; `backend_call_returned=false`; `execution_status=dry_run_completed`.

Input states are AK, AL, AR, AZ, CO, CT, DC, FL, GA, HI, IA, ID, IN, KS, KY, LA, MA, MD, MI, MN, MO, MS, NC, NE, NM, NV, OH, OK, OR, RI, SC, SD, TN, UT, VA, WA, and WI, exactly matching the locked CSV.

## Independent 150-prompt review

Every prompt was parsed and checked against its exact locked row. All 150 contain:

- municipality and state;
- locked internal municipality ID;
- exact government name and Census government ID;
- county context;
- expected units and verification notes;
- strict exact-employer, unit, and qualifying-source controls;
- empty-candidate guidance;
- blocked/unreadable versus dead/unreachable separation;
- known-source and duplicate-risk controls;
- unverified scout-stage handling; and
- the prohibition on making or recommending public-records requests.

Result: **150/150 PASS**. No API/model/backend request, hosted search, URL review, verification, ingestion, or codification occurred.
