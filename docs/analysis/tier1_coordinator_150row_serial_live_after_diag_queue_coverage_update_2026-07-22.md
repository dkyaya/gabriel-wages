# Tier 1 after-diagnostic queue and coverage update

Date: 2026-07-22
Run: `all_2026-07-22_164144`
Disposition: **complete — the merge-eligible Tier 1 outcomes were added once to national accounting and dashboard JSON was refreshed.**

## Candidate queue

- Queue rows: 1,009 → 1,277 (**+268**).
- New URL-bearing Tier 1 rows: 268.
- Rows queued for later verification: 828 → 1,053 (**+225**).
- Held/rejected/context-only rows: 181 → 224 (**+43**).
- New triage composition: 192 high-priority, 22 medium-priority, and 11 low-priority later-verification rows; 2 context-only holds, 26 insufficient holds, and 15 likely-duplicate holds.

All rows are unverified discovery leads. Queue inclusion is not source verification, evidence quality, ingestion readiness, canonical coverage, or claim support.

## Municipality accounting

- Successful scout-covered municipalities: 504 → 646 (**+142**).
- Candidate-positive municipalities: 391 → 490 (**+99**).
- Parseable-empty municipalities: 113 → 156 (**+43**).
- Failure-only municipalities: 10 → 18 (**+8**).
- Retained failed connection/timeout attempts: 26 → 34 (**+8**).
- Operational remaining unscouted, including retryable failure-only rows: 35,085 → 34,943.

Phoenix AZ, Kansas City MO, Indianapolis city (balance) IN, Las Vegas NV, Tampa FL, Fort Wayne IN, Little Rock AR, and Vancouver WA are timeout-only. They are excluded from successful discovery coverage and retained for later retry planning. The earlier stopped parent/retry and diagnostic Oklahoma City probe remain excluded from accounting.

## State deltas

| State | Covered | Candidate-positive | Empty | Failure-only | Candidate rows |
|---|---:|---:|---:|---:|---:|
| AK | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| AL | 0→6 (+6) | 0→3 (+3) | 0→3 (+3) | 0→0 | 0→4 (+4) |
| AR | 0→1 (+1) | 0→0 | 0→1 (+1) | 0→1 (+1) | 0→0 |
| AZ | 0→10 (+10) | 0→5 (+5) | 0→5 (+5) | 0→1 (+1) | 0→12 (+12) |
| CO | 0→9 (+9) | 0→5 (+5) | 0→4 (+4) | 0→0 | 0→11 (+11) |
| CT | 0→3 (+3) | 0→3 (+3) | 0→0 | 0→0 | 0→10 (+10) |
| DC | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→5 (+5) |
| FL | 0→14 (+14) | 0→14 (+14) | 0→0 | 0→1 (+1) | 0→38 (+38) |
| GA | 0→7 (+7) | 0→2 (+2) | 0→5 (+5) | 0→0 | 0→2 (+2) |
| HI | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| IA | 0→4 (+4) | 0→3 (+3) | 0→1 (+1) | 0→0 | 0→11 (+11) |
| ID | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→2 (+2) |
| IN | 0→0 | 0→0 | 0→0 | 0→2 (+2) | 0→0 |
| KS | 0→4 (+4) | 0→2 (+2) | 0→2 (+2) | 0→0 | 0→3 (+3) |
| KY | 0→2 (+2) | 0→2 (+2) | 0→0 | 0→0 | 0→5 (+5) |
| LA | 0→3 (+3) | 0→2 (+2) | 0→1 (+1) | 0→0 | 0→5 (+5) |
| MA | 8→17 (+9) | 8→16 (+8) | 0→1 (+1) | 0→0 | 24→46 (+22) |
| MD | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| MI | 0→4 (+4) | 0→4 (+4) | 0→0 | 0→0 | 0→8 (+8) |
| MN | 0→4 (+4) | 0→3 (+3) | 0→1 (+1) | 0→0 | 0→10 (+10) |
| MO | 0→4 (+4) | 0→3 (+3) | 0→1 (+1) | 0→1 (+1) | 0→6 (+6) |
| MS | 0→1 (+1) | 0→0 | 0→1 (+1) | 0→0 | 0→0 |
| NC | 0→8 (+8) | 0→1 (+1) | 0→7 (+7) | 0→0 | 0→3 (+3) |
| NE | 0→2 (+2) | 0→2 (+2) | 0→0 | 0→0 | 0→7 (+7) |
| NM | 0→2 (+2) | 0→2 (+2) | 0→0 | 0→0 | 0→6 (+6) |
| NV | 0→3 (+3) | 0→3 (+3) | 0→0 | 0→1 (+1) | 0→12 (+12) |
| OH | 0→2 (+2) | 0→2 (+2) | 0→0 | 0→0 | 0→7 (+7) |
| OK | 0→3 (+3) | 0→3 (+3) | 0→0 | 0→0 | 0→8 (+8) |
| OR | 0→3 (+3) | 0→3 (+3) | 0→0 | 0→0 | 0→11 (+11) |
| RI | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| SC | 0→3 (+3) | 0→1 (+1) | 0→2 (+2) | 0→0 | 0→1 (+1) |
| SD | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| TN | 0→7 (+7) | 0→4 (+4) | 0→3 (+3) | 0→0 | 0→9 (+9) |
| UT | 0→1 (+1) | 0→1 (+1) | 0→0 | 0→0 | 0→3 (+3) |
| VA | 0→7 (+7) | 0→3 (+3) | 0→4 (+4) | 0→0 | 0→7 (+7) |
| WA | 0→5 (+5) | 0→4 (+4) | 0→1 (+1) | 0→1 (+1) | 0→14 (+14) |
| WI | 0→4 (+4) | 0→4 (+4) | 0→0 | 0→0 | 0→11 (+11) |

## Builders and dashboard

The canonical builders ran in the required order:

1. `python scripts/build_national_scout_candidate_queue.py`
2. `python scripts/build_national_scout_coverage_status.py`
3. `python scripts/build_scout_coverage.py`

The top-level scout-coverage builder refreshed the authoritative universe/crosswalk from local caches and reproduced the same 646-municipality current-status outputs. This was one substantive accounting promotion; the delegated rewrite was deterministic and did not introduce a second outcome set.

`python scripts/build_dashboard_data.py` then completed at 51 states/DC, 35,589 municipalities, 646 scout-covered municipalities, and 1,277 candidate rows. The current dashboard discovery JSON reflects those totals. Priority-specific JSON was regenerated from the unchanged pre-wave priority CSVs and therefore intentionally remains at its older 504-covered/10-failure vintage until the next priority-tier rebuild. Dashboard frontend code was not edited.

No candidate URL was independently opened or downloaded. No source was verified, ingested, codified, promoted into canonical data, or used as claim evidence. `data/contracts.csv`, `data/city_coverage.csv`, and corpus files were not edited.
