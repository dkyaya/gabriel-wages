# Lane 004 invalid-transport audit

`verify_lane_004` started at its authorized T+24 stagger while lanes 001–003 were active, but its command ran without escalated network permission. Every one of its 2,144 attempts ended as `ConnectError`; this differs categorically from the mixed live HTTP outcomes in lanes 001–003.

The 2,144 sandbox-denied rows are quarantined and excluded from verification, coverage, and dashboard accounting. They are not valid blocked-source findings. Lane 004 therefore has zero valid completed rows and remains resume-required against its unchanged locked queue hash.

No candidate review, download, source review, response-body retention, raw-header retention, document-content inspection, extraction, rating, ingestion, codification, statistical work, or causal analysis occurred. Global analysis readiness remains false.
