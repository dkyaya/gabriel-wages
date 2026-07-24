# Verification Scale Round 1 3×750 Live Readiness Audit

Date: 2026-07-24
Starting commit: `ee7041a47a047d40bbc83469e3aaea0cb1cb8000`
Disposition: **PASS — authorized bounded live collection may proceed after fresh dry runs**

## Repository gate

- Work is confined to the main coordinator repository.
- The tracked worktree was clean at start.
- The unrelated untracked root `package-lock.json` was reported and left
  untouched.
- The bounded-verifier implementation commit `ee7041a` is HEAD.
- No remote was inspected and no push, fetch, or pull occurred.

## Locked input gate

| Lane | Rows | SHA-256 |
|---|---:|---|
| 1 | 750 | `c03701be02afaa6c64cb63a8bb46cf9cae59f8665c3b2969e693b41a31cbfa65` |
| 2 | 750 | `ac9ee0b048f331df295ead483305d72c587ce8962b89426f84b5f42d96d048ca` |
| 3 | 750 | `a9192b47724dcc39eb09ac2760325a9fccd98fadc0b16452518fe4538ec9994a` |

The combined input contains 2,250 unique verification IDs and 2,250 unique
candidate queue identities. Every row is scheduled, high priority, and has
complete verification, queue, municipality, Census-government, state,
municipality, government-name, URL, and duplicate-group identity. There is
zero cross-lane verification-ID overlap and zero exact-URL group split across
lanes.

The manifest records six exact-URL duplicate groups covering fourteen rows;
eight rows are eligible for in-lane representative-fetch reuse.

## Fresh-output and control gate

The following did not exist at the gate:

- `lane_1_dry_run_live_attempt1` and `lane_1_live_attempt1`;
- `lane_2_dry_run_live_attempt1` and `lane_2_live_attempt1`; and
- `lane_3_dry_run_live_attempt1` and `lane_3_live_attempt1`.

The authorized live controls are concurrency eight per lane, total/connect/read
limits 20/8/15 seconds, five redirects, 10,485,760 bytes, disabled content
samples, no environment proxy/auth inheritance, incremental ledger
checkpoints, and lane-local candidate artifacts.

## Stage boundary

This task may open only the 2,250 locked candidate locators and may create
lane-local verification artifacts. It does not authorize a durable
verified-ledger merge, candidate-queue or scout-coverage changes, contract
ingestion, corpus downloads, `gabriel.codify`, wage extraction, wage-gap
calculation or claims, causal claims, or regressions.
