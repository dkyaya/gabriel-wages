# Verification Scale Round 2 3×1000 Remainder — Dashboard Status Note

Date: 2026-07-24

The dashboard verification operations layer now distinguishes live collection
from durable ledger merge:

- `verification_phase`: `round1_3x750_merged`
- `live_verification_status`:
  `round2_3x1000_remainder_collected_not_merged`
- `latest_live_round_id`:
  `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`
- Round 2 selected/terminal rows: 2,476 / 2,476
- Round 2 URL opens: 2,386
- Round 2 reachable/reused: 1,862 (75.2019%)
- Round 2 duplicate reuse rows: 90
- Round 2 audit recommendation: `merge_all_verification_lanes`
- Round 2 merge status: `not_started`
- cumulative durable merged rows: 2,250

The frontend states that Round 2 is collected and awaiting a separate serial
merge. It does not include Round 2 in the durable merged count. The dashboard
does not change scout queue/coverage accounting and continues to label
ingestion, codification, wage extraction, and wage-gap analysis as not
started.

All availability and response-type counts are routing metadata. They do not
establish document relevance, employer/unit match, extractable wage data, or a
wage gap.
