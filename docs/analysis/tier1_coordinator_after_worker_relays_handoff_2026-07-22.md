# Tier 1 Coordinator Handoff After Worker Relays

Date: 2026-07-22

Disposition: **future coordinator procedure only; no smoke or live scout is authorized by this handoff.**

## Required evidence gate

1. Locate all three sanitized worker ZIPs copied into the main coordinator repo `tmp/` with basenames `tier1_worker_<N>_prep_relay_2026-07-22_<commit>.zip`.
2. Inspect each ZIP without copying secrets. Confirm its locked worker input SHA-256 matches the coordinator audit, its exact 50 rows/IDs/order remain unchanged, `run_metadata.json` is a completed mixed-state dry run with no backend call, `row_timing.csv` has 50 dry-planned rows, the prompt review passes 50/50, no-network validation passes, and protected files are unchanged.
3. Stop if any relay, artifact, identity, hash, lifecycle field, prompt control, or validation result is missing or inconsistent. Do not substitute a municipality ad hoc.

## Future locked coordinator input

Combine Worker 1, then Worker 2, then Worker 3 in exact worker-row order. Require 150 unique municipality IDs and Census IDs, one queue ID `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`, all Tier 1/eligible/non-retry/non-failure/not-scouted/noncanonical rows, and an exact SHA-256 recorded before any later run.

Run a coordinator mixed-state 150-prompt dry review first. A separately authorized live task must then use exactly one no-search direct-SDK smoke and, only after all gates pass, one coordinator-controlled serialized direct-SDK lane with `--state ALL --allow-mixed-states --live-hard-cap 150 --max-prompts 150 --n-parallels 1 --sleep-between-prompts 5 --direct-sdk-max-retries 0`. Concurrent live workers remain prohibited.

Stop on connection collapse, repeated transport failure, systematic parse/schema failure, artifact/lifecycle loss, protected-file mutation, or secret exposure. If a complete post-patch parent permits resume, use the same locked input hash, skip completed IDs or select authorized failure types, preserve lineage, and write to a fresh resume output directory—never the parent directory.

Only a complete merge-eligible parent/resume lineage may rebuild national queue/coverage once and then refresh dashboard JSON. Source discovery remains unverified. No verification, ingestion, codification, canonical promotion, or claim use is part of scouting.
