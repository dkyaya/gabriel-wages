# Tier 1 Wave 2 Coordinator 150-Row Live Input Audit

Date: 2026-07-22

Disposition: **PASS — exact Worker 1 → Worker 2 → Worker 3 locked input, currently eligible for coordinator dry/preflight gates.**

## Identity and order

- Rows: 150.
- Worker order/counts: `worker_1=50`, then `worker_2=50`, then `worker_3=50`.
- Wave ranks: exactly 151–300 with no gaps or reorder.
- Municipality IDs: 150 unique, none missing.
- Census government IDs: 150 unique, none missing.
- Queue ID: one value, `COORD-TIER1-WAVE2-SERIAL150-2026-07-22`.
- Employer identity: 150 `municipal` / `place` governments; no prohibited employer category.
- Search hints: all five deterministic hints attached for 150/150 rows.
- Locked coordinator CSV SHA-256: `f530932c487cef73aae6d18f19e477697c2b2cfbd85dfd8226e608723d7e750e`.

## Current operational eligibility

Exact municipality-ID reconciliation against current `national_scout_coverage_municipality_2026-07-20.csv`, `national_scout_candidate_queue_2026-07-20.csv`, the prior Tier 1 Wave 1 input, and the current/older failure ledgers passed:

- Tier 1: 150/150.
- Current ordinary future-scout eligible: 150/150.
- `retry_flag=false`: 150/150.
- `failure_only_flag=false`: 150/150.
- Current `not_scouted`: 150/150.
- Already canonical/in corpus: 0.
- Current candidate-queue overlap: 0.
- Prior Tier 1 Wave 1 selected overlap: 0.
- Current 18-row failure-only overlap: 0, including all eight prior Tier 1 timeout rows.
- Older ten-row retry-ledger overlap: 0.
- No row was substituted.

Current accounting before this run remains 646 successfully scout-covered municipalities—490 candidate-positive and 156 parseable-empty—plus 18 failure-only municipalities and 1,277 candidate-queue rows.

## Distribution

- States: AL 3, AR 2, AZ 5, CO 6, CT 4, FL 16, GA 3, IA 2, ID 3, IN 4, KS 3, LA 2, MA 9, MD 1, MI 7, MN 4, MO 4, MS 1, MT 1, NC 12, ND 1, NH 2, NM 2, NV 1, OH 6, OK 3, OR 6, PA 3, SC 3, TN 4, UT 11, VA 3, WA 10, WI 2, WV 1.
- Score min/median/max: 74.436 / 74.7055 / 75.067.
- Priority confidence: low 147, medium 3.

The file is locked for this coordinator run. Any identity, order, eligibility, hint, or hash change requires stopping rather than substituting a row.
