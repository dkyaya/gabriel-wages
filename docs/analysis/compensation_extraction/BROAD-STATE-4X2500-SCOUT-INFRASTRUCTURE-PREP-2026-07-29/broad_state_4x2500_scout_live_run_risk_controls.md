# Live-run risk controls

The future live run uses four controlled overlapping lanes at T+0/T+8/T+16/T+24. Workers cannot mutate shared dashboard/status files. They use bounded retries, preserve sanitized metadata, stop on repeated backend instability, and never verify URLs, download, inspect sources, review candidates, or run later research stages.
