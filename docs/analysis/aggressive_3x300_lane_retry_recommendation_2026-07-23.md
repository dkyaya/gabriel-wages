# Aggressive 3×300 Fresh-Lane Retry Recommendation

Date: 2026-07-23/24  
Status: recommendation only; no retry authorized or executed

The `attempt1` collection is non-mergeable. All of its artifacts must remain immutable.

## Recommended lineage

| Lane | Attempt 1 state | Recommended later action |
|---|---|---|
| Lane 1 | two connection failures, zero parseable, 298 stopped | re-run the entire unchanged 300-row input in fresh `lane_1_live_direct_sdk_attempt2` |
| Lane 2 | not launched | run the unchanged 300-row input in fresh `lane_2_live_direct_sdk_attempt2` |
| Lane 3 | not launched | run the unchanged 300-row input in fresh `lane_3_live_direct_sdk_attempt2` |

This is a fresh-round retry, not a skip-completed resume. Lane 1 has no parseable completed municipality to preserve, and Lanes 2–3 made no request.

Before any future live attempt:

1. obtain separate explicit authorization;
2. revalidate all three locked hashes and current ordinary eligibility;
3. run a fresh plan-only preflight and one separately authorized stronger live gate with a quarantined probe;
4. run fresh dry runs or re-audit them as the future authorization requires;
5. refuse any existing/nonempty `attempt2` output;
6. launch Lane 1 first and require healthy parseable progress before launching Lane 2;
7. repeat the health gate before Lane 3; and
8. audit all outputs and stop before accounting.

Do not use `--resume-from-output-dir` against Lane 1 `attempt1`, do not merge the two failed rows, and do not treat either stopped-before-request rows or the diagnostic Newport probe as official coverage.

