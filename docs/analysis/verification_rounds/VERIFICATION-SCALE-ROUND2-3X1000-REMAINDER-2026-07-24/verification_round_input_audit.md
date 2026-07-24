# Verification Round Input Audit — VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24

## Scope

- Canonical queue: `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
- Queue SHA-256: `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- Total URL-bearing queue rows before prior-ledger exclusion: 4,726
- Prior durable routing ledger: `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv`
- Prior ledger rows/queue IDs/verification IDs excluded: 2,250/2,250/2,250
- Exact URL-bearing rows remaining after exclusion: 2,476
- Requested scope: `remainder_all`
- Eligible rows in scope: 2,476
- Planned rows: 2,476
- Round capacity / under-capacity rows: 3,000 / 524
- Remaining URL-bearing rows left unselected: 0
- Profile: `max_1000`
- Lanes: 3
- Maximum rows per lane: 1000
- Actual lane rows: `[826, 825, 825]`
- Concurrency per lane: 8
- Bounded timeout: 20 seconds
- Maximum response bytes: 10,485,760
- Duplicate-aware lane assignment: True
- Expected lane runtime (2–8 second average response assumption): 3.5–13.9 minutes
- Timeout-heavy upper bound: 34.7 minutes
- Unique verification IDs across lanes: 2,476
- Duplicate verification IDs across lanes: 0
- Syntactically valid HTTP(S) URLs: 2,476/2,476
- Candidate priorities: `{"held": 1126, "high": 575, "low": 285, "medium": 490}`
- Candidate dispositions: `{"already_canonical": 8, "calibration_rejected": 2, "context_hold": 523, "duplicate_hold": 291, "insufficient_hold": 302, "scheduled": 1350}`
- Previously routed candidate queue ID overlap: 0
- Previously routed verification ID overlap: 0
- States: `{"AK": 11, "AL": 14, "AR": 16, "AZ": 29, "CA": 266, "CO": 25, "CT": 22, "DE": 9, "FL": 241, "GA": 7, "IA": 33, "ID": 20, "IL": 80, "IN": 58, "KS": 32, "KY": 18, "LA": 22, "MA": 74, "MD": 57, "ME": 32, "MI": 51, "MN": 131, "MO": 56, "MS": 12, "MT": 23, "NC": 17, "ND": 12, "NE": 9, "NH": 18, "NJ": 94, "NM": 41, "NV": 10, "NY": 64, "OH": 174, "OK": 21, "OR": 83, "PA": 102, "RI": 14, "SC": 3, "SD": 16, "TN": 28, "TX": 113, "UT": 37, "VA": 27, "VT": 9, "WA": 114, "WI": 105, "WV": 10, "WY": 16}`
- Candidate source types: `{"agenda_cover_sheet": 28, "arbitration_award": 105, "blocked_or_unreadable": 6, "cba": 1248, "context_only": 50, "factfinding": 22, "index_page": 10, "insufficient_source": 5, "meeting_minutes": 11, "memorandum_or_settlement": 192, "ordinance_or_policy": 181, "pay_plan": 3, "unknown": 18, "wage_schedule_or_compensation_plan": 597}`
- Exact normalized URL duplicate groups in full queue: 94
- Extra rows linked to exact duplicate URLs in full queue: 117
- Exact duplicate URL groups in selected round: 74
- Selected duplicate rows eligible for reuse: 90
- Selected duplicate groups split across lanes: 0

## Gate

**PASS.** Every selected row preserves its original queue identity and has a
unique deterministic verification ID, complete municipality/Census identity,
syntactically valid URL, stable duplicate group, and explicit candidate-stage
status. No URL was opened. No network/API/model call, live verification,
ingestion, codification, extraction, or wage analysis occurred.
