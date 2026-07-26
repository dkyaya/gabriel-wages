# Targeted scouting lane_2 — future live worker prompt

This prompt is prepared but was not run. A separate future task must authorize live execution.

## Scope

- Input: `targeted_scouting_lane_2_queue_500.csv` with exactly 500 locked candidate targets.
- Primary mechanism: `strike_or_no_strike_constraint`.
- Secondary mechanisms: `bargaining_power_signal|safety_advantage_signal|non_safety_constraint_signal`.
- Source family target: `cba_or_arbitration_award_or_factfinding_or_impasse_record`.
- Output remains scout-stage candidate leads only; scouting is not verification.

## Required preflight

Recheck the lane lockfile and queue SHA-256, confirm 500 unique target IDs, confirm every `live_run_status` is `not_started`, and run a bounded no-call preflight before any hosted operation. Stop if another lane is active or the lock/hash differs.

## Hard constraints

- Do not fetch or pull repository state; do not inspect or configure remotes.
- Do not download documents, open PDFs, access PDF pages, run OCR, or use rendered images.
- Do not verify sources, run source review, extract text, select documents for extraction, rate evidence, ingest, or run `gabriel.codify`.
- Do not treat candidates as verified, analysis-ready, or causal evidence.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not save raw prompts, raw responses, credentials, secrets, tokens, cookies, auth headers, or environment values.
- Keep global analysis readiness false.
- Cap the lane at 500 targets and create a lane-specific relay.

Live hosted search/model use is not authorized by this preparation artifact; it requires the separate future task authorization and its successful preflight.
