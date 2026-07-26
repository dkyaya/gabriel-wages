# Next task: targeted scouting Lane 1 live run

Authorize only Lane 1 after independently confirming this preparation commit, queue hash, lockfile, credentials, and bounded preflight. Do not start Lanes 2–4.

## Scope

- Input: `targeted_scouting_lane_1_queue_500.csv` with exactly 500 locked candidate targets.
- Primary mechanism: `non_safety_constraint_signal`.
- Secondary mechanisms: `gap_narrowing_signal|parity_or_internal_equity_signal|fiscal_constraint_signal|safety_advantage_signal`.
- Source family target: `collective_bargaining_agreement_or_moa_or_wage_schedule`.
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
