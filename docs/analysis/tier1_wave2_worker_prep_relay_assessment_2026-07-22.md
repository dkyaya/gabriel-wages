# Tier 1 Wave 2 Worker Prep Relay Assessment

Date: 2026-07-22

Disposition: **PASS — all three offline worker relays are eligible for one coordinator-controlled live queue after the remaining coordinator gates pass.**

## Worker 1 — ranks 151–200

- Relay: `tmp/tier1_wave2_worker_1_prep_relay_2026-07-22_9395a4c.zip`; relay SHA-256 `ae58747e2e9d0452590690e91d9f6c10a2d4db306e881946c6c5a126bfab476a`.
- Worker commit: `9395a4c` (`Prepare Tier 1 Wave 2 Worker 1 offline dry run`). Post-commit tracked status and protected-file comparison are clean.
- Input: 50 rows, `worker_id=worker_1`, exact ranks 151–200, 50 unique municipality IDs, 50 unique Census IDs, one queue ID `COORD-TIER1-WAVE2-SERIAL150-2026-07-22`, and SHA-256 `f9cd191ca00e6e965cde83879a1383f23d1750b8e90d0a5812697c98aa19b20f`. The relay copy is byte-identical to main.
- Eligibility: 50/50 Tier 1, current ordinary future eligible, nonretry, non-failure-only, `not_scouted`, noncanonical, and exact municipal/place employer rows; all five hints are attached.
- Dry run `all_2026-07-22_193826`: `prompt_mode=compact`, `search_hints_matched_count=50`, mixed states, cap 50, fixed fallback 5.0 seconds, adaptive mode enabled with min/base/max/backoff `3/5/15/10` and stability/failure windows `25/2`; `live_attempted=false`, `backend_call_returned=false`, lifecycle `dry_run_completed`.
- `row_timing.csv`: 50 locked-order `dry_run_planned` rows with no response IDs or token use. Prompt review passed every required identity/hint/guardrail/schema control 50/50. No-network validation compiled the runner/tests, passed all 12 prompt tests, and passed `git diff --check`.
- States: AL 3, AZ 2, CO 2, CT 2, FL 6, GA 2, ID 3, IN 1, KS 1, LA 1, MI 2, MN 1, MO 1, MT 1, NC 6, ND 1, NH 1, NM 1, OH 2, OK 1, OR 2, TN 3, UT 3, WA 2.

## Worker 2 — ranks 201–250

- Relay: `tmp/tier1_wave2_worker_2_prep_relay_2026-07-22_37125c7.zip`; relay SHA-256 `5e5db9b6ea9dcbd03b2985e766b6c6def4acee1ab3f1b2e189e1602f8f4d3a61`.
- Worker commit: `37125c7` (`Prepare Tier 1 Wave 2 Worker 2 offline dry run`). Post-commit tracked status and protected-file comparison are clean.
- Input: 50 rows, `worker_id=worker_2`, exact ranks 201–250, 50 unique municipality IDs, 50 unique Census IDs, one expected queue ID, and SHA-256 `78ee47781e959867cd1a315228ab63ad2cbfabaf72e9e56cf06baf99db35b508`. The relay copy is byte-identical to main.
- Eligibility: 50/50 Tier 1, current ordinary future eligible, nonretry, non-failure-only, `not_scouted`, noncanonical, and exact municipal/place employer rows; all five hints are attached.
- Dry run `all_2026-07-22_193821`: compact mode, 50 matched hints, mixed states, cap 50, fixed fallback 5.0 seconds, adaptive `3/5/15/10` with `25/2`; no live attempt or backend return; lifecycle completed.
- Timing/review/validation: 50 locked-order dry-planned rows; all required prompt checks passed 50/50; runner/test compiles, all 12 prompt tests, protected comparison, and `git diff --check` passed without network/backend use.
- States: AR 1, AZ 2, CO 2, FL 7, GA 1, IA 1, IN 3, KS 2, MA 4, MI 2, MO 1, MS 1, NC 1, NV 1, OH 2, OK 1, OR 3, PA 1, SC 1, UT 3, VA 3, WA 5, WI 2.

## Worker 3 — ranks 251–300

- Relay: `tmp/tier1_wave2_worker_3_prep_relay_2026-07-22_6ae1267.zip`; relay SHA-256 `e83e3ef74e8319bf3d760dcd5ebe648554f6a5827fd21bf6dc4bb2cb07e2f249`.
- Worker commit: `6ae1267` (`Prepare Tier 1 Wave 2 Worker 3 offline dry run`). Post-commit tracked status and protected-file comparison are clean.
- Input: 50 rows, `worker_id=worker_3`, exact ranks 251–300, 50 unique municipality IDs, 50 unique Census IDs, one expected queue ID, and SHA-256 `825b6bb7d31f6e1cdbe9fd00963096a39baf25ebbc89972fc5a84f32aba99ca1`. The relay copy is byte-identical to main.
- Eligibility: 50/50 Tier 1, current ordinary future eligible, nonretry, non-failure-only, `not_scouted`, noncanonical, and exact municipal/place employer rows; all five hints are attached.
- Dry run `all_2026-07-22_193811`: compact mode, 50 matched hints, mixed states, cap 50, fixed fallback 5.0 seconds, adaptive `3/5/15/10` with `25/2`; no live attempt or backend return; lifecycle completed.
- Timing/review/validation: 50 locked-order dry-planned rows; all required prompt checks passed 50/50; runner/test compiles, all 12 prompt tests, protected comparison, and `git diff --check` passed without network/backend use.
- States: AR 1, AZ 1, CO 2, CT 2, FL 3, IA 1, LA 1, MA 5, MD 1, MI 3, MN 3, MO 2, NC 5, NH 1, NM 1, OH 2, OK 1, OR 1, PA 2, SC 2, TN 1, UT 5, WA 3, WV 1.

## Coordinator disposition

The three relay inputs concatenate exactly as Worker 1 → Worker 2 → Worker 3, cover ranks 151–300 without gaps, and contain no duplicate municipality or Census IDs. All relays are **coordinator-live eligible**, conditional on the fresh locked-input audit, composite preflight gate, and coordinator 150-prompt dry review. The worker outputs remain preparation evidence only and contain no official scout outcomes.
