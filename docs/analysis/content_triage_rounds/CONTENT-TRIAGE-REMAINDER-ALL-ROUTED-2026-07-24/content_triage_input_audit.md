# Content-Triage Round Input Audit — CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24

## Result

- Total durable routing rows: 4,726
- Reachable or successfully reused rows: 3,750
- Routing-eligible rows including duplicate-pending: 3,778
- Eligible rows in requested scope before duplicate policy: 3,726
- Eligible rows after duplicate policy: 3,726
- Selected rows: 3,726
- Excluded prior metadata-triage rows: 1,000
- Selected plus excluded: 4,726
- Unselected routed rows after this plan: 0
- Lanes: 4
- Lane row counts: `{"lane_1": 932, "lane_2": 932, "lane_3": 931, "lane_4": 931}`
- Selected states: `{"AK": 29, "AL": 14, "AR": 16, "AZ": 29, "CA": 568, "CO": 25, "CT": 32, "DC": 2, "DE": 17, "FL": 241, "GA": 7, "HI": 1, "IA": 75, "ID": 20, "IL": 232, "IN": 58, "KS": 41, "KY": 18, "LA": 22, "MA": 103, "MD": 57, "ME": 46, "MI": 166, "MN": 131, "MO": 56, "MS": 12, "MT": 37, "NC": 17, "ND": 12, "NE": 31, "NH": 24, "NJ": 94, "NM": 41, "NV": 16, "NY": 139, "OH": 364, "OK": 21, "OR": 126, "PA": 102, "RI": 14, "SC": 3, "SD": 37, "TN": 28, "TX": 113, "UT": 37, "VA": 27, "VT": 15, "WA": 170, "WI": 214, "WV": 10, "WY": 16}`
- Selected source types: `{"agenda_cover_sheet": 28, "arbitration_award": 151, "blocked_or_unreadable": 6, "cba": 2000, "context_only": 50, "factfinding": 77, "index_page": 10, "insufficient_source": 5, "meeting_minutes": 11, "memorandum_or_settlement": 355, "ordinance_or_policy": 206, "pay_plan": 3, "unknown": 21, "wage_schedule_or_compensation_plan": 803}`
- Selected content types: `{"application/json": 1, "application/octet-stream": 1, "application/pdf": 2855, "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 4, "application/xml": 5, "image/jpeg": 1, "text/html": 728, "text/plain": 2, "text/xml": 2, "unknown": 127}`
- Selected dispositions: `{"already_canonical": 8, "calibration_rejected": 2, "context_hold": 523, "duplicate_hold": 291, "insufficient_hold": 302, "scheduled": 2600}`

## Deferred and duplicate boundaries

- Routing-eligible duplicate groups: 94
- Linked duplicate rows in those groups: 117
- Duplicate rows selected: 117
- Lower-disposition routing-eligible rows: 1,126
- Lower-disposition rows selected: 1,126
- `too_large` rows selected: 261
- `too_large` rows deferred: 0
- Other blocked/not-found/error/transport rows deferred: 0

The round is deterministic, metadata-first planning. No URL was opened, no
document was downloaded or parsed, no PDF/OCR operation ran, and no routing
outcome was promoted into source evidence or wage data.
