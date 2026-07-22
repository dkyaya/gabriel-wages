# Tier 1 Worker Batch Split Design Audit

Date: 2026-07-22

Two deterministic designs were applied to the same locked 150-row priority order. Severe concentration is defined as more than 20 rows or more than 60% of a worker batch from one state.

## A. Rank-sliced

### Worker 1

- Rank range: 1–50; average 25.5
- Score min/median/max: 76.100 / 76.703 / 78.002
- States: AL 2, AZ 4, CO 4, DC 1, FL 4, GA 1, HI 1, IA 1, IN 1, KS 1, KY 2, LA 2, MD 1, MI 1, MN 1, MO 2, MS 1, NC 4, NE 1, NM 1, NV 2, OK 2, OR 2, SC 2, SD 1, TN 2, VA 1, WA 1, WI 1
- Confidence: low 50
- Population min/median/max: 142,416 / 469,109.500 / 1,650,070; missing 0
- Largest single-state count: AZ 4 (8.0%)
- Operational concern: priority strength differs intentionally by worker slice.

### Worker 2

- Rank range: 51–100; average 75.5
- Score min/median/max: 75.516 / 75.801 / 76.073
- States: AK 1, AL 2, AR 1, AZ 4, CO 3, FL 5, GA 3, ID 1, IN 1, KS 1, LA 1, MA 1, MI 2, MN 1, MO 3, NC 4, NE 1, NM 1, NV 2, OH 1, OK 1, SC 1, TN 1, UT 1, VA 3, WA 3, WI 1
- Confidence: low 50
- Population min/median/max: 91,706 / 214,661 / 303,820; missing 0
- Largest single-state count: FL 5 (10.0%)
- Operational concern: priority strength differs intentionally by worker slice.

### Worker 3

- Rank range: 101–150; average 125.5
- Score min/median/max: 75.071 / 75.261 / 75.511
- States: AL 2, AR 1, AZ 3, CO 2, CT 3, FL 6, GA 3, IA 3, KS 2, MA 8, MI 1, MN 2, OH 1, OR 1, RI 1, TN 4, VA 3, WA 2, WI 2
- Confidence: low 50
- Population min/median/max: 70,542 / 136,876.500 / 190,792; missing 0
- Largest single-state count: MA 8 (16.0%)
- Operational concern: priority strength differs intentionally by worker slice.

## B. Round-robin

### Worker 1

- Rank range: 1–148 (every third rank); average 74.5
- Score min/median/max: 75.078 / 75.807 / 78.002
- States: AK 1, AL 1, AR 1, AZ 6, CO 4, DC 1, FL 5, GA 3, IA 2, IN 2, KS 2, LA 1, MA 4, MN 2, MO 1, NC 3, NE 1, OK 2, SC 1, TN 2, VA 4, WI 1
- Confidence: low 50
- Population min/median/max: 71,013 / 202,859.500 / 879,293; missing 0
- Largest single-state count: AZ 6 (12.0%)
- Operational concern: noncontiguous rank lineage is slightly less direct to audit.

### Worker 2

- Rank range: 2–149 (every third rank); average 75.5
- Score min/median/max: 75.074 / 75.803 / 77.973
- States: AL 3, AR 1, AZ 3, CO 4, FL 3, GA 3, HI 1, IA 1, KS 1, KY 2, LA 1, MA 5, MD 1, MI 3, MN 1, MO 1, MS 1, NC 4, NV 3, OH 1, OR 1, SC 1, UT 1, VA 2, WI 2
- Confidence: low 50
- Population min/median/max: 70,542 / 186,478 / 1,650,070; missing 0
- Largest single-state count: MA 5 (10.0%)
- Operational concern: noncontiguous rank lineage is slightly less direct to audit.

### Worker 3

- Rank range: 3–150 (every third rank); average 76.5
- Score min/median/max: 75.071 / 75.778 / 77.877
- States: AL 2, AZ 2, CO 1, CT 3, FL 7, GA 1, IA 1, ID 1, KS 1, LA 1, MI 1, MN 1, MO 3, NC 1, NE 1, NM 2, NV 1, OH 1, OK 1, OR 2, RI 1, SC 1, SD 1, TN 5, VA 1, WA 6, WI 1
- Confidence: low 50
- Population min/median/max: 73,337 / 196,543 / 985,843; missing 0
- Largest single-state count: FL 7 (14.0%)
- Operational concern: noncontiguous rank lineage is slightly less direct to audit.

## Decision

Use **rank-sliced contiguous batches**. No worker approaches the severe threshold: the maxima are four, five, and eight rows from a single state. The split preserves the clearest lineage (ranks 1–50, 51–100, 101–150), keeps Worker 1 as the strongest slice, and still spans 29, 27, 19 states. Round-robin marginally equalizes score/population profiles but does not solve a concentration problem that exists here.
