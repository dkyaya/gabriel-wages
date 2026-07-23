# Post-PI Wave 1 Worker Prep Relay Assessment

Date: 2026-07-23

Disposition: **PASS — all three worker relays are eligible for the coordinator live gates.**

## Coordinator assessment method

The coordinator tested each ZIP for archive integrity, extracted it into a fresh temporary inspection directory, compared the relayed input byte-for-byte with the corresponding committed main-repository worker input, recalculated the CSV hash, inspected the validation and dry-run review, parsed `run_metadata.json`, audited all 50 `row_timing.csv` records, and checked every prompt block for the locked identity and scout guardrails.

Current committed coverage, failure-only, canonical, prior-wave, and search-hint evidence was then reconciled again while building the combined coordinator input. No source URL was opened or verified during this assessment.

## Worker 1

- Relay: `tmp/post_pi_wave1_worker_1_prep_relay_2026-07-23_11fa202.zip`; archive integrity passed.
- Relay commit: `11fa202` (`Prepare post-PI Wave 1 Worker 1 offline dry run`).
- Input: 50 rows, exact ranks 1–50, all `worker_id=worker_1`.
- Input SHA-256: `ac1cfad98cf21b97c5845b7b06b48718383668a57ee18a605d50b089fe20b9fc`; expected hash and main-repository byte comparison passed.
- Identity/exclusion gate: 50 unique nonblank municipality IDs; 50 unique nonblank Census IDs; all ordinary future eligible; zero retry, failure-only, current successful-coverage, canonical, or prior official-wave overlaps.
- Queue ID: `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23` on all rows.
- State distribution: CT 9, FL 5, MI 2, OH 15, OR 12, WA 7.
- Dry-run evidence: 50/50 compact prompt blocks passed; 50/50 deterministic hints matched; all five hints are attached to each input row.
- Lifecycle: `live_attempted=false`, `backend_call_returned=false`, `attempted_row_count=0`.
- Adaptive metadata: enabled; min/base/max/backoff `3/5/15/10`; stability/failure windows `25/2`.
- Timing: `row_timing.csv` has 50 exact identities, all `backend=dry-run`, `success_status=dry_run_planned`, and `parse_status=not_attempted`.
- Validation report: PASS.
- Coordinator-live eligibility: **PASS**.

## Worker 2

- Relay: `tmp/post_pi_wave1_worker_2_prep_relay_2026-07-23_d11015c.zip`; archive integrity passed.
- Relay commit: `d11015c` (`Prepare post-PI Wave 1 Worker 2 offline dry run`).
- Input: 50 rows, exact ranks 51–100, all `worker_id=worker_2`.
- Input SHA-256: `2c45d7ceff4b619b7dfa8d65bf7ce7b7d3846f2ff8a328e76faeec24f10e80a7`; expected hash and main-repository byte comparison passed.
- Identity/exclusion gate: 50 unique nonblank municipality IDs; 50 unique nonblank Census IDs; all ordinary future eligible; zero retry, failure-only, current successful-coverage, canonical, or prior official-wave overlaps.
- Queue ID: `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23` on all rows.
- State distribution: CT 2, FL 12, MI 8, OH 13, OR 6, WA 9.
- Dry-run evidence: 50/50 compact prompt blocks passed; 50/50 deterministic hints matched; all five hints are attached to each input row.
- Lifecycle: `live_attempted=false`, `backend_call_returned=false`, `attempted_row_count=0`.
- Adaptive metadata: enabled; min/base/max/backoff `3/5/15/10`; stability/failure windows `25/2`.
- Timing: `row_timing.csv` has 50 exact identities, all `backend=dry-run`, `success_status=dry_run_planned`, and `parse_status=not_attempted`.
- Validation report: PASS.
- Coordinator-live eligibility: **PASS**.

## Worker 3

- Relay: `tmp/post_pi_wave1_worker_3_prep_relay_2026-07-23_5212d6d.zip`; archive integrity passed.
- Relay commit: `5212d6d` (`Prepare post-PI Wave 1 Worker 3 offline dry run`).
- Input: 50 rows, exact ranks 101–150, all `worker_id=worker_3`.
- Input SHA-256: `574507500387ccbfb162504086b9463811b6906f765a2066d3a7d928ae17941d`; expected hash and main-repository byte comparison passed.
- Identity/exclusion gate: 50 unique nonblank municipality IDs; 50 unique nonblank Census IDs; all ordinary future eligible; zero retry, failure-only, current successful-coverage, canonical, or prior official-wave overlaps.
- Queue ID: `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23` on all rows.
- State distribution: FL 10, IA 1, MA 3, MI 7, NV 1, OH 16, OR 4, WA 5, WI 3.
- Dry-run evidence: 50/50 compact prompt blocks passed; 50/50 deterministic hints matched; all five hints are attached to each input row.
- Lifecycle: `live_attempted=false`, `backend_call_returned=false`, `attempted_row_count=0`.
- Adaptive metadata: enabled; min/base/max/backoff `3/5/15/10`; stability/failure windows `25/2`.
- Timing: `row_timing.csv` has 50 exact identities, all `backend=dry-run`, `success_status=dry_run_planned`, and `parse_status=not_attempted`.
- Validation report: PASS.
- Coordinator-live eligibility: **PASS**.

## Combined disposition

All three relays contain the required locked inputs, dry-run metadata, prompt previews, row timing, validation evidence, and local commit lineage. Across the relays there are 150 distinct municipality IDs and 150 distinct Census government IDs in exact ranks 1–150. Compact prompts, deterministic search hints, and adaptive sleep metadata are consistent across workers.

The three relays therefore pass the worker evidence gate. This pass authorizes only the subsequent coordinator input, stronger-preflight, and fresh 150-row dry-run gates. The official 150-row live scout remains conditional on all later gates passing.

No worker live scout, API/model/backend call, hosted search, source verification, ingestion, `gabriel.codify`, accounting rebuild, wage-gap calculation, causal analysis, remote inspection, or push occurred in this assessment.
