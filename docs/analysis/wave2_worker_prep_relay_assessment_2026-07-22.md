# Wave 2 Worker Preparation Relay Assessment

Date: 2026-07-22

Disposition: **PASS — all three offline worker-preparation relays are complete, internally consistent, byte-aligned with the main coordinator inputs, and eligible for the coordinator dry/smoke/live gates.**

## Repository gate

The coordinator started at `1265366025c008b071a650d779d2492030563130` (`Prepare wave2 3x50 scout batches`). It contains `943a458` (post-Wave-1 dashboard consolidation), `67c2c5d` (five-second pacing, row timing, and resume safeguards), and `1265366` (Wave 2 batch preparation). Tracked state was clean. The unrelated pre-existing root `package-lock.json` remained untracked and untouched.

All three exact ZIPs exist in coordinator `tmp/` and pass `unzip -t`. Their required CSV, review, validation, metadata, and timing artifacts were read directly from the ZIPs. Each relay input is byte-for-byte identical to its corresponding main-repository locked input.

## Worker results

| Worker | State | Prep commit | Relay SHA-256 | Input SHA-256 | Rows / IDs | Dry metadata | Timing | Review / validation | Result |
|---|---|---|---|---|---|---|---|---|---|
| Worker 1 | CA | `eaef3c1321d8a3efe4467b64ba8a00d557cc5f1c` | `a70a852c5d9f98b8e2d12e70ed3980ae93eb18524f94db7fda9e166e2dbf9848` | `f8b0e99e0a7343d3efacf3829325cb86db7b775814e933af21dacbbc0069f123` | 50; 50 municipality IDs; 50 Census IDs | `dry_run_completed`; sleep 5.0; no live/backend return | 50 `dry_run_planned` rows | 50/50 PASS; no-network PASS | PASS |
| Worker 2 | TX | `a985f1b630e13c9e75ecdadc0f802cb52bfad603` | `2e9fa0b7fed00f9c6e2bc4e75dc3449f6c40c5b76378d55a27c4f701aabe97f7` | `d393601295ea86ab9a52e712bff0c7cc9cf7e0977e97793c134a6b1c02af4c6f` | 50; 50 municipality IDs; 50 Census IDs | `dry_run_completed`; sleep 5.0; no live/backend return | 50 `dry_run_planned` rows | 50/50 PASS; no-network PASS | PASS |
| Worker 3 | IL | `5a19082c8f977e85dd8ba2c73a2fda08e0991217` | `7726fb6d0e7e26117c7f88703e200fe98c35a5659f9ffe255633d53da0902699` | `2257832562c87f76cdcbb6ec7efb5793034bc9d6484d39fd90bde05b7bb1c28b` | 50; 50 municipality IDs; 50 Census IDs | `dry_run_completed`; sleep 5.0; no live/backend return | 50 `dry_run_planned` rows | 50/50 PASS; no-network PASS | PASS |

Every input has exactly one expected `worker_id`, exactly one `COORD-SERIAL150-WAVE2-2026-07-22` future queue ID, and its required single state. All timing rows have `backend=dry-run`, `live_attempted=no`, and `success_status=dry_run_planned`. All metadata files record `live_attempted=false` and `backend_call_returned=false`.

Worker 2's ZIP contains an extra archive member named `-`; it is irrelevant packaging residue. All named required artifacts exist, parse, and pass exact checks, so it does not affect eligibility or source evidence.

## Coordinator eligibility decision

All three workers are **coordinator-live eligible**, subject to the remaining independent gates: current eligibility reconciliation, one locked CA→TX→IL input, a corrected-code 150-row dry review, and exactly one passing direct-SDK no-search smoke. Worker relays authorize no worker live process and no accounting mutation.
