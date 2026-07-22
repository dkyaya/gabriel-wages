# Tier 1 Worker 1 Locked Input Audit

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
- Worker ID / scope: `worker_1` / `CROSS_STATE_TIER1`
- Rank range: 1–50
- Score range: 76.100–78.002
- Confidence: high 0, medium 0, low 50
- State distribution: AL 2, AZ 4, CO 4, DC 1, FL 4, GA 1, HI 1, IA 1, IN 1, KS 1, KY 2, LA 2, MD 1, MI 1, MN 1, MO 2, MS 1, NC 4, NE 1, NM 1, NV 2, OK 2, OR 2, SC 2, SD 1, TN 2, VA 1, WA 1, WI 1
- Assignment: `rank_sliced_contiguous`
- CSV SHA-256: `2828934d7185a437cbd961d16363812f81889f63a20ff77b4c332da463abf606`

Every row is an authoritative municipal/place identity; no prohibited employer category or known failure-only municipality is present. The input is locked for prompt dry-run review and remains scout-stage only.

## Top ten

| Tier 1 rank | Municipality | State | Population | Score |
|---:|---|---|---:|---:|
| 1 | Oklahoma City | OK | 702,767 | 78.002 |
| 2 | Phoenix | AZ | 1,650,070 | 77.973 |
| 3 | Portland | OR | 630,498 | 77.877 |
| 4 | Milwaukee | WI | 561,385 | 77.745 |
| 5 | Atlanta | GA | 510,823 | 77.636 |
| 6 | Kansas City | MO | 510,704 | 77.636 |
| 7 | Raleigh | NC | 482,295 | 77.570 |
| 8 | Honolulu | HI | 989,408 | 77.393 |
| 9 | Jacksonville | FL | 985,843 | 77.389 |
| 10 | Tulsa | OK | 411,894 | 77.389 |

## State counts

| State | Rows |
|---|---:|
| AL | 2 |
| AZ | 4 |
| CO | 4 |
| DC | 1 |
| FL | 4 |
| GA | 1 |
| HI | 1 |
| IA | 1 |
| IN | 1 |
| KS | 1 |
| KY | 2 |
| LA | 2 |
| MD | 1 |
| MI | 1 |
| MN | 1 |
| MO | 2 |
| MS | 1 |
| NC | 4 |
| NE | 1 |
| NM | 1 |
| NV | 2 |
| OK | 2 |
| OR | 2 |
| SC | 2 |
| SD | 1 |
| TN | 2 |
| VA | 1 |
| WA | 1 |
| WI | 1 |
