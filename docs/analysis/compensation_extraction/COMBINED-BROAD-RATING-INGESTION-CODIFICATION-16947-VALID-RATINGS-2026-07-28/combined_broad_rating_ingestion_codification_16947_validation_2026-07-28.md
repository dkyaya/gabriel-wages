# Combined broad rating ingestion/codification validation

All deterministic package invariants passed: **16,947** valid ratings became durable ingested/codified records, lanes reconciled to **[4237, 4237, 4237, 4236]**, and **312** quarantines remained reference-only. Controlled schemas, layers, buckets, boxes, claim boundaries, map contract, and global-readiness=false passed. No model/API, source/full-text, extraction, OCR/rendering, normalization/comparison, statistical, prevalence, or causal operation ran.

## Command results

- Python compilation passed for the dashboard builder, runner, and new test.
- New ingestion/codification suite: 37/37 passed, including deterministic rebuild and excluded-box display reconciliation.
- Rating-summary suite: 35/35 passed; exact-span rating suite: 25/25 passed; span-extraction suite passed for 3,815 sources and 17,259 candidates.
- Dashboard declutter/map contract suite passed; dashboard data build passed with 6,919 scout-covered municipalities and 13,041 candidate rows.
- Dashboard Vite build passed with only its existing chunk-size advisory.
- Repository schema validation passed; ingestion pipeline tests passed 60/60.
- Git artifact checks found zero tracked retained-source or full-extracted-text paths and no staged blob over 50 MiB.
- `git diff --check` passed.
