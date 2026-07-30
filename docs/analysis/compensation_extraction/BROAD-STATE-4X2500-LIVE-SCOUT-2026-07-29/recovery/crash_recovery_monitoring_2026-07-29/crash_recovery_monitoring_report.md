# Broad state 4 × 2,500 live scout crash-recovery monitoring snapshot

Decision: `broad_state_4x2500_live_scout_crash_recovery_workers_still_running_monitoring`

Snapshot: `2026-07-29T21:51:08.828652-04:00`. Four existing worker processes were alive and all lane checkpoints were advancing, so no duplicate worker was launched.

| Lane | Status | Accepted | Parseable | Failed | Candidates | Last completed | Next unaccepted |
|---|---:|---:|---:|---:|---:|---|---|
| scout_lane_001 | in_progress | 1992 | 1983 | 9 | 2047 | B4X2500-20260729-01992 | B4X2500-20260729-01993 |
| scout_lane_002 | in_progress | 1951 | 1943 | 8 | 1962 | B4X2500-20260729-04451 | B4X2500-20260729-04452 |
| scout_lane_003 | in_progress | 1972 | 1964 | 8 | 2049 | B4X2500-20260729-06972 | B4X2500-20260729-06973 |
| scout_lane_004 | in_progress | 1949 | 1942 | 7 | 2038 | B4X2500-20260729-09449 | B4X2500-20260729-09450 |

Recovered totals: 7864 accepted outcomes, 7832 parseable, 32 failed, and 8096 candidate rows. Completed lanes: 0 of 4.

No accepted target rerun was detected. Existing live workers own any current in-flight target; those directories must not be discarded or separately retried. The resume launch predated this audit, and this audit launched no worker.

The dashboard was not rebuilt from an in-progress lane snapshot. It remains total-scout-coverage-only at 6,919, counts zero planned targets as actual, and keeps global analysis readiness false. Candidate review and every downstream stage remain deferred.
