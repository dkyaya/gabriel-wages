# Verification Round Input Audit — VERIFICATION-SCALE-ROUND1-3X750-2026-07-23

## Scope

- Canonical queue: `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
- Queue SHA-256: `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- Total URL-bearing queue rows: 4,726
- Requested scope: `scheduled`
- Eligible rows in scope: 3,600
- Planned rows: 2,250
- Profile: `aggressive_750`
- Lanes: 3
- Rows per lane: 750
- Concurrency per lane: 8
- Bounded timeout: 20 seconds
- Maximum response bytes: 10,485,760
- Duplicate-aware lane assignment: True
- Expected lane runtime (2–8 second average response assumption): 3.1–12.5 minutes
- Timeout-heavy upper bound: 31.3 minutes
- Unique verification IDs across lanes: 2,250
- Duplicate verification IDs across lanes: 0
- Syntactically valid HTTP(S) URLs: 2,250/2,250
- Candidate priorities: `{"high": 2250}`
- Candidate dispositions: `{"scheduled": 2250}`
- States: `{"AK": 18, "CA": 508, "CT": 40, "DC": 5, "DE": 8, "HI": 3, "IA": 42, "IL": 218, "KS": 9, "MA": 87, "ME": 14, "MI": 115, "MT": 30, "NE": 22, "NH": 19, "NV": 24, "NY": 75, "OH": 644, "OR": 97, "RI": 13, "SD": 21, "VT": 6, "WA": 123, "WI": 109}`
- Candidate source types: `{"arbitration_award": 46, "cba": 1752, "factfinding": 55, "memorandum_or_settlement": 163, "ordinance_or_policy": 25, "unknown": 3, "wage_schedule_or_compensation_plan": 206}`
- Exact normalized URL duplicate groups in full queue: 94
- Extra rows linked to exact duplicate URLs in full queue: 117
- Exact duplicate URL groups in selected round: 6
- Selected duplicate rows eligible for reuse: 8
- Selected duplicate groups split across lanes: 0

## Gate

**PASS.** Every selected row preserves its original queue identity and has a
unique deterministic verification ID, complete municipality/Census identity,
syntactically valid URL, stable duplicate group, and explicit candidate-stage
status. No URL was opened. No network/API/model call, live verification,
ingestion, codification, extraction, or wage analysis occurred.
