# Prior lane 004 ConnectError audit

The prior lane 004 worker ran without escalated network permission. All 2,144 `ConnectError` rows remain preserved in the predecessor quarantine and are excluded from the resume queue, final merge, verification counts, and dashboard counts. The unchanged locked queue therefore begins this resume with zero valid completed rows.
