# Tier 1 Wave 2 Worker 2 Locked Input Audit

Date: 2026-07-22

Disposition: **PASS — exact 50-row offline compact-prompt dry-run input.**

- Rows / Tier 1 / current ordinary eligible: 50 / 50/50 / 50/50
- Retry / failure-only / covered / canonical: 0 / 0 / 0 / 0
- Unique municipality IDs / Census IDs: 50 / 50; missing Census IDs 0
- Complete attached hints: 50/50
- Worker / scope / assignment: `worker_2` / `CROSS_STATE_TIER1_WAVE2` / `rank_sliced_contiguous`
- Wave rank range: 201–250
- Score range: 74.619–74.813
- Confidence: high 0, medium 1, low 49
- States: AR 1, AZ 2, CO 2, FL 7, GA 1, IA 1, IN 3, KS 2, MA 4, MI 2, MO 1, MS 1, NC 1, NV 1, OH 2, OK 1, OR 3, PA 1, SC 1, UT 3, VA 3, WA 5, WI 2
- CSV SHA-256: `78ee47781e959867cd1a315228ab63ad2cbfabaf72e9e56cf06baf99db35b508`

No prior-Wave-1, retry/failure-only, covered, canonical, duplicate, or prohibited-employer row is present. All five deterministic hints are attached. This remains unverified scout-stage preparation only.

## Top ten municipalities

| Wave rank | Source rank | Municipality | State | Population | Score |
|---:|---:|---|---|---:|---:|
| 201 | 207 | Penn Hills | PA | 39,643 | 74.813 |
| 202 | 208 | Sparks | NV | 110,323 | 74.810 |
| 203 | 209 | Concord | NC | 110,119 | 74.808 |
| 204 | 210 | Manhattan | KS | 53,682 | 74.801 |
| 205 | 211 | Buckeye | AZ | 108,909 | 74.793 |
| 206 | 212 | Joplin | MO | 53,095 | 74.785 |
| 207 | 213 | Spokane Valley | WA | 108,235 | 74.784 |
| 208 | 214 | Davie | FL | 107,799 | 74.779 |
| 209 | 215 | Hillsboro | OR | 107,730 | 74.778 |
| 210 | 216 | Framingham | MA | 71,875 | 74.778 |

## State distribution

| State | Rows |
|---|---:|
| AR | 1 |
| AZ | 2 |
| CO | 2 |
| FL | 7 |
| GA | 1 |
| IA | 1 |
| IN | 3 |
| KS | 2 |
| MA | 4 |
| MI | 2 |
| MO | 1 |
| MS | 1 |
| NC | 1 |
| NV | 1 |
| OH | 2 |
| OK | 1 |
| OR | 3 |
| PA | 1 |
| SC | 1 |
| UT | 3 |
| VA | 3 |
| WA | 5 |
| WI | 2 |
