# Tier 1 Worker Prep Relay Assessment

Date: 2026-07-22

Disposition: **PASS — all three offline worker relays are eligible for the coordinator evidence gate.** This assessment authorizes neither a worker live run nor a coordinator live run by itself.

## Coordinator starting state

- Starting main-repo commit: `364fd9d90f799bfe44c2d73d395a2c415f808ce0` (`Prepare Tier 1 worker scout batches`).
- Required ancestors: `bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714` and `364fd9d` are both present in the current local history.
- Tracked worktree at the gate: clean. The unrelated untracked root `package-lock.json` was reported and left untouched.
- No remote operation was performed.

## Worker results

| Worker | Scope and ranks | Relay commit | Locked-input SHA-256 | State count | Dry-run metadata | Timing | Review / validation | Result |
|---|---|---|---|---:|---|---|---|---|
| Worker 1 | Cross-state Tier 1, ranks 1–50 | `d0b24ca` | `2828934d7185a437cbd961d16363812f81889f63a20ff77b4c332da463abf606` | 29 | 50 prompts; sleep 5.0; `live_attempted=false`; `backend_call_returned=false`; `execution_status=dry_run_completed` | 50 `dry_run_planned` rows in exact input order | 50/50 prompt contract PASS; no-network validation PASS; post-commit tracked status clean | PASS |
| Worker 2 | Cross-state Tier 1, ranks 51–100 | `9ab705e` | `02c3e5ea8529a079d3a8286dfba371a55a94041a050e5b49941b1297767ae62a` | 27 | 50 prompts; sleep 5.0; `live_attempted=false`; `backend_call_returned=false`; `execution_status=dry_run_completed` | 50 `dry_run_planned` rows in exact input order | 50/50 prompt contract PASS; no-network validation PASS; post-commit tracked status clean | PASS |
| Worker 3 | Cross-state Tier 1, ranks 101–150 | `80f808a` | `8761ef52affd9fa0dd2cd5af88433c4e2c8725a384b7ffb9cae26388dcd60c6d` | 19 | 50 prompts; sleep 5.0; `live_attempted=false`; `backend_call_returned=false`; `execution_status=dry_run_completed` | 50 `dry_run_planned` rows in exact input order | 50/50 prompt contract PASS; no-network validation PASS; post-commit tracked status clean | PASS |

The input copy inside each relay is byte-identical to its coordinator copy. Independent inspection of all 150 prompt blocks confirmed the locked municipality name, state, internal municipality ID, government name, Census government ID, county context, expected units, verification notes, strict employer/unit/source rules, no-candidate guidance, blocked/dead distinction, duplicate controls, unverified-stage handling, and public-records prohibition.

## Eligibility checks

Every relay contains exactly 50 rows with one expected worker ID, one queue ID `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`, unique municipality and Census IDs, the required continuous rank slice, `Tier 1`, future-scout eligibility, non-retry status, non-failure status, `not_scouted`, noncanonical status, and municipal/place government type. None contains Stockton CA, Redding CA, Oakland CA, Moreno Valley CA, Oxnard CA, Fairfield CA, Bloomington IL, Huntley IL, Roselle IL, or Princeton NJ.

Current coordinator accounting was checked again after relay review: all 150 IDs still have `not_scouted` coverage, none occurs in the current 1,009-row candidate queue, and all have `not_already_ingested_canonical` coverage status. No row became ineligible.

## State distributions

- Worker 1: AL 2; AZ 4; CO 4; DC 1; FL 4; GA 1; HI 1; IA 1; IN 1; KS 1; KY 2; LA 2; MD 1; MI 1; MN 1; MO 2; MS 1; NC 4; NE 1; NM 1; NV 2; OK 2; OR 2; SC 2; SD 1; TN 2; VA 1; WA 1; WI 1.
- Worker 2: AK 1; AL 2; AR 1; AZ 4; CO 3; FL 5; GA 3; ID 1; IN 1; KS 1; LA 1; MA 1; MI 2; MN 1; MO 3; NC 4; NE 1; NM 1; NV 2; OH 1; OK 1; SC 1; TN 1; UT 1; VA 3; WA 3; WI 1.
- Worker 3: AL 2; AR 1; AZ 3; CO 2; CT 3; FL 6; GA 3; IA 3; KS 2; MA 8; MI 1; MN 2; OH 1; OR 1; RI 1; TN 4; VA 3; WA 2; WI 2.

All three workers are therefore coordinator-live eligible, subject to the separate locked-input audit, coordinator 150-prompt dry run, and one-request direct-SDK smoke gate.
