# Tier 1 Worker 3 Locked Input Audit

Date: 2026-07-22

Disposition: **PASS — exact 50-row offline dry-run input.**

- Rows: 50
- Tier 1: 50/50
- Future eligible: 50/50
- Retry rows: 0
- Failure-only rows: 0
- Covered rows: 0
- Canonical rows: 0
- Unique municipality IDs: 50
- Unique Census IDs: 50; missing: 0
- Worker ID / scope: `worker_3` / `CROSS_STATE_TIER1`
- Rank range: 101–150
- Score range: 75.071–75.511
- Confidence: high 0, medium 0, low 50
- State distribution: AL 2, AR 1, AZ 3, CO 2, CT 3, FL 6, GA 3, IA 3, KS 2, MA 8, MI 1, MN 2, OH 1, OR 1, RI 1, TN 4, VA 3, WA 2, WI 2
- Assignment: `rank_sliced_contiguous`
- CSV SHA-256: `8761ef52affd9fa0dd2cd5af88433c4e2c8725a384b7ffb9cae26388dcd60c6d`

Every row is an authoritative municipal/place identity; no prohibited employer category or known failure-only municipality is present. The input is locked for prompt dry-run review and remains scout-stage only.

## Top ten

| Tier 1 rank | Municipality | State | Population | Score |
|---:|---|---|---:|---:|
| 101 | Springdale | AR | 88,224 | 75.511 |
| 102 | Providence | RI | 190,792 | 75.489 |
| 103 | Tempe | AZ | 189,834 | 75.482 |
| 104 | Akron | OH | 188,701 | 75.475 |
| 105 | Sioux City | IA | 85,727 | 75.471 |
| 106 | Chattanooga | TN | 187,030 | 75.465 |
| 107 | Brockton | MA | 104,890 | 75.459 |
| 108 | Warner Robins | GA | 84,537 | 75.452 |
| 109 | Cambridge | MA | 118,214 | 75.451 |
| 110 | Fort Lauderdale | FL | 184,255 | 75.447 |

## State counts

| State | Rows |
|---|---:|
| AL | 2 |
| AR | 1 |
| AZ | 3 |
| CO | 2 |
| CT | 3 |
| FL | 6 |
| GA | 3 |
| IA | 3 |
| KS | 2 |
| MA | 8 |
| MI | 1 |
| MN | 2 |
| OH | 1 |
| OR | 1 |
| RI | 1 |
| TN | 4 |
| VA | 3 |
| WA | 2 |
| WI | 2 |
