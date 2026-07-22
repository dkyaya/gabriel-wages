# Tier 1 Worker 2 Locked Input Audit

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
- Worker ID / scope: `worker_2` / `CROSS_STATE_TIER1`
- Rank range: 51–100
- Score range: 75.516–76.073
- Confidence: high 0, medium 0, low 50
- State distribution: AK 1, AL 2, AR 1, AZ 4, CO 3, FL 5, GA 3, ID 1, IN 1, KS 1, LA 1, MA 1, MI 2, MN 1, MO 3, NC 4, NE 1, NM 1, NV 2, OH 1, OK 1, SC 1, TN 1, UT 1, VA 3, WA 3, WI 1
- Assignment: `rank_sliced_contiguous`
- CSV SHA-256: `02c3e5ea8529a079d3a8286dfba371a55a94041a050e5b49941b1297767ae62a`

Every row is an authoritative municipal/place identity; no prohibited employer category or known failure-only municipality is present. The input is locked for prompt dry-run review and remains scout-stage only.

## Top ten

| Tier 1 rank | Municipality | State | Population | Score |
|---:|---|---|---:|---:|
| 51 | Dayton | OH | 135,512 | 76.073 |
| 52 | St. Paul | MN | 303,820 | 76.038 |
| 53 | Greensboro | NC | 302,296 | 76.032 |
| 54 | Lincoln | NE | 294,757 | 76.003 |
| 55 | Anchorage | AK | 286,075 | 75.968 |
| 56 | North Las Vegas | NV | 284,771 | 75.962 |
| 57 | St. Louis | MO | 281,754 | 75.950 |
| 58 | Springfield | MA | 153,672 | 75.945 |
| 59 | Madison | WI | 280,305 | 75.944 |
| 60 | Chandler | AZ | 280,167 | 75.943 |

## State counts

| State | Rows |
|---|---:|
| AK | 1 |
| AL | 2 |
| AR | 1 |
| AZ | 4 |
| CO | 3 |
| FL | 5 |
| GA | 3 |
| ID | 1 |
| IN | 1 |
| KS | 1 |
| LA | 1 |
| MA | 1 |
| MI | 2 |
| MN | 1 |
| MO | 3 |
| NC | 4 |
| NE | 1 |
| NM | 1 |
| NV | 2 |
| OH | 1 |
| OK | 1 |
| SC | 1 |
| TN | 1 |
| UT | 1 |
| VA | 3 |
| WA | 3 |
| WI | 1 |
