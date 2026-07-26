# Next task: repair four-lane live execution contract

The `TARGETED-SCOUTING-FOUR-LANE-STAGGERED-LIVE-RUN-FROM-PREP-2026-07-25` preflight failed before any hosted search because exact T+0/T+8/T+16/T+24 starts conflict with the explicit rule that lanes may not run simultaneously. All four 500-target queue and lock hashes remain valid and untouched.

Choose exactly one scheduling contract in the next authorization:

1. **Sequential lanes (recommended for API protection):** Lane 2 starts only after Lane 1 finishes, Lane 3 after Lane 2, and Lane 4 after Lane 3. The eight-minute values become minimum quiet intervals after completion, not offsets from Lane 1's start.
2. **Fixed stagger with overlap:** retain T+0/T+8/T+16/T+24 starts and explicitly authorize overlap after each staggered start. This is higher-load and requires a concurrency/rate-limit plan.

Do not authorize both. Revalidate commit `b338003063bd1fd2c29fb70c0af6130987c67ffa`, the four lockfiles, 500 rows per lane, and 2,000 unique targets before live use. Do not fetch/pull or inspect/configure remotes. Do not download documents, open PDFs/pages, run OCR, verify, extract, select, rate, ingest, codify, analyze the quantitative lane, calculate wage gaps, run regressions/treatment effects, or make final causal claims. Keep candidates unverified, unextracted, unrated, non-causal, and keep global analysis readiness false. Do not save raw prompts/responses or secrets.
