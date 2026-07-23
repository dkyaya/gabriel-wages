# Post-PI Wave 1 Coordinator 150-Row Serial Live Dry-Run Review

Date: 2026-07-23

Disposition: **PASS — the fresh coordinator dry-run gate authorizes the single serialized live scout, subject to a final protected-file/output-directory check.**

- Locked input: `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`
- Output: `tmp/post_pi_wave1_coordinator_150row_serial_live_dry_run_2026-07-23_attempt1`
- Prompt blocks: 150.
- Timing rows: 150.

## Metadata and lifecycle

- PASS — 150 input rows.
- PASS — 150 prompt blocks.
- PASS — 150 row-timing records.
- PASS — compact prompt mode.
- PASS — search hints matched 150/150.
- PASS — input states match locked input.
- PASS — mixed-state mode enabled.
- PASS — live hard cap is 150.
- PASS — fixed fallback sleep is 5.0.
- PASS — adaptive sleep enabled.
- PASS — adaptive min/base/max/backoff is 3/5/15/10.
- PASS — adaptive stability/failure windows are 25/2.
- PASS — no live lifecycle.
- PASS — timing identities match locked input in order.
- PASS — all timing rows are dry-planned.
- Input states: CT, FL, IA, MA, MI, NV, OH, OR, WA, WI.
- Total planned sleep: 522.0 seconds; actual sleep is zero because this was a dry run.

## Prompt-by-prompt review

All 150 prompt blocks match their same-position locked input rows. Every prompt contains:

- municipality name and state;
- locked internal municipality ID, exact government name, and Census government ID;
- county context and the exact expected-unit search plan;
- all five attached deterministic query hints;
- the row-specific verification cautions;
- exact-employer and excluded-employer controls;
- safety/non-safety unit separation and authoritative-source guidance;
- valid no-candidate guidance;
- blocked-versus-dead separation;
- duplicate suppression and exact-known-source handling;
- unverified scout-stage handling;
- public-records-request prohibition; and
- the complete compact JSON output schema.

Prompt audit result: **150/150 PASS**.

No live/API/model/backend/hosted-search call, source verification, URL opening, ingestion, codification, queue/coverage mutation, wage-gap calculation, regression, remote action, or push occurred in this dry run.
