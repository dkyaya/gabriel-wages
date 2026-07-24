# Content-Triage Round Input Audit — CONTENT-TRIAGE-ROUND1-1000-2026-07-24

## Result

- Total durable routing rows: 4,726
- Reachable or successfully reused rows: 3,750
- Routing-eligible rows including duplicate-pending: 3,778
- Eligible rows in requested scope before duplicate policy: 2,391
- Eligible rows after duplicate policy: 2,382
- Selected rows: 1,000
- Lanes: 2
- Lane row counts: `{"lane_1": 500, "lane_2": 500}`
- Selected states: `{"CA": 206, "CT": 30, "DC": 3, "HI": 2, "IL": 66, "MA": 58, "MT": 16, "NH": 13, "NV": 18, "OH": 454, "OR": 54, "RI": 13, "WA": 67}`
- Selected source types: `{"cba": 1000}`
- Selected content types: `{"application/pdf": 1000}`
- Selected dispositions: `{"scheduled": 1000}`

## Deferred and duplicate boundaries

- Routing-eligible duplicate groups: 78
- Linked duplicate rows in those groups: 93
- Duplicate rows selected: 0
- Lower-disposition routing-eligible rows: 756
- Lower-disposition rows selected: 0
- `too_large` rows deferred: 261
- Other blocked/not-found/error/transport rows deferred: 687

The round is deterministic, metadata-first planning. No URL was opened, no
document was downloaded or parsed, no PDF/OCR operation ran, and no routing
outcome was promoted into source evidence or wage data.
