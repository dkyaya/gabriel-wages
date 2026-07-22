# Tier 1 Wave 2 Worker Batch Split Design Audit

Date: 2026-07-22

Both designs use the same locked Wave 2 order. Severe concentration means more than 20 rows or more than 60% of one worker from one state.

## A. Rank-sliced

### Worker 1

- Rank range: 151–200; average 175.5
- Score min/median/max: 74.816 / 74.916 / 75.067
- State counts: AL 3, AZ 2, CO 2, CT 2, FL 6, GA 2, ID 3, IN 1, KS 1, LA 1, MI 2, MN 1, MO 1, MT 1, NC 6, ND 1, NH 1, NM 1, OH 2, OK 1, OR 2, TN 3, UT 3, WA 2
- Confidence: low 50
- Population min/median/max: 54,245 / 113,943.5 / 134,906; missing 0
- Largest state: FL 6 (12.0%)
- Complete hints: 50/50
- Operational concern: workers intentionally differ in priority slice.

### Worker 2

- Rank range: 201–250; average 225.5
- Score min/median/max: 74.619 / 74.706 / 74.813
- State counts: AR 1, AZ 2, CO 2, FL 7, GA 1, IA 1, IN 3, KS 2, MA 4, MI 2, MO 1, MS 1, NC 1, NV 1, OH 2, OK 1, OR 3, PA 1, SC 1, UT 3, VA 3, WA 5, WI 2
- Confidence: low 49, medium 1
- Population min/median/max: 39,643 / 98,157 / 110,323; missing 0
- Largest state: FL 7 (14.0%)
- Complete hints: 50/50
- Operational concern: workers intentionally differ in priority slice.

### Worker 3

- Rank range: 251–300; average 275.5
- Score min/median/max: 74.436 / 74.516 / 74.615
- State counts: AR 1, AZ 1, CO 2, CT 2, FL 3, IA 1, LA 1, MA 5, MD 1, MI 3, MN 3, MO 2, NC 5, NH 1, NM 1, OH 2, OK 1, OR 1, PA 2, SC 2, TN 1, UT 5, WA 3, WV 1
- Confidence: low 48, medium 2
- Population min/median/max: 32,398 / 85,958.5 / 95,232; missing 0
- Largest state: MA 5 (10.0%)
- Complete hints: 50/50
- Operational concern: workers intentionally differ in priority slice.

## B. Round-robin balanced

### Worker 1

- Rank range: 151–298 (every third rank); average 224.5
- Score min/median/max: 74.443 / 74.714 / 75.067
- State counts: AL 1, AZ 3, CO 1, CT 1, FL 7, GA 2, ID 1, IN 2, MA 1, MI 2, MN 1, NC 3, NH 1, NM 2, NV 1, OH 1, OK 1, OR 1, SC 2, TN 2, UT 5, VA 2, WA 5, WI 1, WV 1
- Confidence: low 50
- Population min/median/max: 42,663 / 96,678 / 134,906; missing 0
- Largest state: FL 7 (14.0%)
- Complete hints: 50/50
- Operational concern: noncontiguous lineage is less direct to audit.

### Worker 2

- Rank range: 152–299 (every third rank); average 225.5
- Score min/median/max: 74.439 / 74.706 / 75.066
- State counts: AL 2, AR 1, CO 1, CT 2, FL 2, GA 1, ID 2, IN 1, KS 1, LA 1, MA 4, MI 3, MN 2, MO 3, MS 1, NC 5, OH 4, OK 1, OR 5, PA 2, SC 1, TN 1, UT 1, VA 1, WA 2
- Confidence: low 48, medium 2
- Population min/median/max: 32,398 / 89,493.5 / 134,801; missing 0
- Largest state: NC 5 (10.0%)
- Complete hints: 50/50
- Operational concern: noncontiguous lineage is less direct to audit.

### Worker 3

- Rank range: 153–300 (every third rank); average 226.5
- Score min/median/max: 74.436 / 74.699 / 75.063
- State counts: AR 1, AZ 2, CO 4, CT 1, FL 7, IA 2, IN 1, KS 2, LA 1, MA 4, MD 1, MI 2, MN 1, MO 1, MT 1, NC 4, ND 1, NH 1, OH 1, OK 1, PA 1, TN 1, UT 5, WA 3, WI 1
- Confidence: low 49, medium 1
- Population min/median/max: 39,643 / 91,689.5 / 134,470; missing 0
- Largest state: FL 7 (14.0%)
- Complete hints: 50/50
- Operational concern: noncontiguous lineage is less direct to audit.

## Decision

Use **rank-sliced contiguous batches**. The largest within-worker state counts are Worker 1=6, Worker 2=7, Worker 3=5, all far below the severe threshold. Contiguous ranks 151–200, 201–250, and 251–300 preserve priority strength and make relay reconstruction simplest; round-robin adds complexity without curing a material concentration problem.
