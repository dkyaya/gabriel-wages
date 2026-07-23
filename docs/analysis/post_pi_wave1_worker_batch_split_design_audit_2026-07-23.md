# Post-PI Scale-Up Wave 1 Worker Batch Split Design Audit

Date: 2026-07-23

Both designs use the same locked 150-row order. Severe concentration means more than 20 rows from one state in one worker or more than 60% of one worker from one state.

## A. Rank-sliced split

### Worker 1

- Rank range: 1–50; average 25.5
- Score min/median/max: 76.059 / 76.428 / 77.268
- State counts: CT 9, FL 5, MI 2, OH 15, OR 12, WA 7
- Priority tiers: Tier 1 50
- Confidence counts: low 38, medium 12
- Population min/median/max: 21,594 / 53,953.5 / 82,528; missing 0
- Largest state: OH 15 (30.0%)
- Complete hints: 50/50
- Operational concern: Workers intentionally differ by contiguous priority slice; lineage is direct.

### Worker 2

- Rank range: 51–100; average 75.5
- Score min/median/max: 75.682 / 75.881 / 76.056
- State counts: CT 2, FL 12, MI 8, OH 13, OR 6, WA 9
- Priority tiers: Tier 1 50
- Confidence counts: low 29, medium 21
- Population min/median/max: 21,525 / 43,887.5 / 82,574; missing 0
- Largest state: OH 13 (26.0%)
- Complete hints: 50/50
- Operational concern: Workers intentionally differ by contiguous priority slice; lineage is direct.

### Worker 3

- Rank range: 101–150; average 125.5
- Score min/median/max: 75.280 / 75.475 / 75.660
- State counts: FL 10, IA 1, MA 3, MI 7, NV 1, OH 16, OR 4, WA 5, WI 3
- Priority tiers: Tier 1 50
- Confidence counts: low 32, medium 18
- Population min/median/max: 18,317 / 42,153.5 / 76,602; missing 0
- Largest state: OH 16 (32.0%)
- Complete hints: 50/50
- Operational concern: Workers intentionally differ by contiguous priority slice; lineage is direct.

## B. Round-robin balanced split

### Worker 1

- Rank range: 1–148; average 74.5
- Score min/median/max: 75.283 / 75.883 / 77.268
- State counts: CT 3, FL 7, IA 1, MA 1, MI 4, NV 1, OH 18, OR 7, WA 6, WI 2
- Priority tiers: Tier 1 50
- Confidence counts: low 36, medium 14
- Population min/median/max: 19,475 / 48,416.5 / 82,574; missing 0
- Largest state: OH 18 (36.0%)
- Complete hints: 50/50
- Operational concern: Ranks are noncontiguous, which adds relay reconstruction complexity.

### Worker 2

- Rank range: 2–149; average 75.5
- Score min/median/max: 75.281 / 75.874 / 77.186
- State counts: CT 2, FL 14, MI 5, OH 11, OR 8, WA 10
- Priority tiers: Tier 1 50
- Confidence counts: low 26, medium 24
- Population min/median/max: 18,317 / 47,502.5 / 82,528; missing 0
- Largest state: FL 14 (28.0%)
- Complete hints: 50/50
- Operational concern: Ranks are noncontiguous, which adds relay reconstruction complexity.

### Worker 3

- Rank range: 3–150; average 76.5
- Score min/median/max: 75.280 / 75.870 / 77.166
- State counts: CT 6, FL 6, MA 2, MI 8, OH 15, OR 7, WA 5, WI 1
- Priority tiers: Tier 1 50
- Confidence counts: low 37, medium 13
- Population min/median/max: 21,061 / 46,932 / 82,485; missing 0
- Largest state: OH 15 (30.0%)
- Complete hints: 50/50
- Operational concern: Ranks are noncontiguous, which adds relay reconstruction complexity.

## Decision

Use **rank-sliced contiguous batches**. The largest state count in Workers 1–3 is below both severe-concentration thresholds, so round-robin balancing is unnecessary. Deterministic assignment is ranks 1–50 to Worker 1, 51–100 to Worker 2, and 101–150 to Worker 3.
