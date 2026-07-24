# Verification Round Input Audit — VERIFICATION-SCALE-ROUND1-2026-07-23

## Scope

- Canonical queue: `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
- Queue SHA-256: `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- Total URL-bearing queue rows: 4,726
- Requested scope: `scheduled`
- Eligible rows in scope: 3,600
- Planned rows: 750
- Lanes: 3
- Rows per lane: 250
- Unique verification IDs across lanes: 750
- Duplicate verification IDs across lanes: 0
- Syntactically valid HTTP(S) URLs: 750/750
- Candidate priorities: `{"high": 750}`
- Candidate dispositions: `{"scheduled": 750}`
- States: `{"CA": 339, "CT": 40, "DC": 5, "HI": 3, "MA": 87, "NH": 19, "NV": 24, "OR": 97, "RI": 13, "WA": 123}`
- Candidate source types: `{"arbitration_award": 2, "cba": 588, "factfinding": 2, "memorandum_or_settlement": 90, "ordinance_or_policy": 4, "wage_schedule_or_compensation_plan": 64}`
- Exact normalized URL duplicate groups in full queue: 94
- Extra rows linked to exact duplicate URLs in full queue: 117

## Gate

**PASS.** Every selected row preserves its original queue identity and has a
unique deterministic verification ID, complete municipality/Census identity,
syntactically valid URL, stable duplicate group, and explicit candidate-stage
status. No URL was opened. No network/API/model call, live verification,
ingestion, codification, extraction, or wage analysis occurred.
