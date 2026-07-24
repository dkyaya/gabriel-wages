# Full Verification Backlog Plan

- Total URL-bearing candidate rows: 4,726
- Scheduled verification rows: 3,600
- Held/context/duplicate/canonical/rejected rows: 1,126
- Scheduled-only at 3×750 (2,250/round): 2 rounds
- All URL-bearing rows at 3×750: 3 rounds
- All URL-bearing rows at 3×1,000: 2 rounds
- Candidate priorities: `{"held": 1126, "high": 2825, "low": 285, "medium": 490}`
- Candidate dispositions: `{"already_canonical": 8, "calibration_rejected": 2, "context_hold": 523, "duplicate_hold": 291, "insufficient_hold": 302, "scheduled": 3600}`
- State distribution: `{"AK": 29, "AL": 14, "AR": 16, "AZ": 29, "CA": 774, "CO": 25, "CT": 62, "DC": 5, "DE": 17, "FL": 241, "GA": 7, "HI": 3, "IA": 75, "ID": 20, "IL": 298, "IN": 58, "KS": 41, "KY": 18, "LA": 22, "MA": 161, "MD": 57, "ME": 46, "MI": 166, "MN": 131, "MO": 56, "MS": 12, "MT": 53, "NC": 17, "ND": 12, "NE": 31, "NH": 37, "NJ": 94, "NM": 41, "NV": 34, "NY": 139, "OH": 818, "OK": 21, "OR": 180, "PA": 102, "RI": 27, "SC": 3, "SD": 37, "TN": 28, "TX": 113, "UT": 37, "VA": 27, "VT": 15, "WA": 237, "WI": 214, "WV": 10, "WY": 16}`

Every original candidate identity remains represented. Exact URL duplicates
share deterministic duplicate-group IDs so later live verification can open a
source once and link all original queue rows without losing provenance.

This is planning only: zero URLs opened, zero network/API/model calls, and zero
verification, ingestion, codification, extraction, or wage analysis.
