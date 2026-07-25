# PDF-Readiness Pilot Input Audit

## Result

**PASS.** The offline planner selected exactly 150 unique retained PDFs from 2124 eligible artifacts.

- source ledger rows: 2150
- eligible retained PDFs: 2124
- selected rows: 150
- lane rows: 50 / 50 / 50
- selected artifact bytes: 334676242
- duplicate readiness/source-review/candidate IDs: 0 / 0 / 0
- nonblank paths/hashes: 150 / 150
- URLs opened: 0
- PDFs opened or parsed during planning: 0

## Selected distributions

### `source_review_pilot_id`

- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 32
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 87
- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 31

### `priority_for_content_review`

- `p1`: 66
- `p2`: 84

### `unit_type`

- `fire`: 45
- `non_safety`: 53
- `police`: 52

### `state`

- `AK`: 3
- `AL`: 2
- `AR`: 2
- `AZ`: 3
- `CA`: 3
- `CO`: 3
- `CT`: 3
- `DC`: 3
- `DE`: 3
- `FL`: 3
- `GA`: 3
- `HI`: 3
- `IA`: 3
- `ID`: 3
- `IL`: 3
- `IN`: 3
- `KS`: 3
- `KY`: 3
- `LA`: 3
- `MA`: 3
- `MD`: 3
- `ME`: 3
- `MI`: 3
- `MN`: 3
- `MO`: 3
- `MS`: 3
- `MT`: 4
- `NC`: 2
- `ND`: 2
- `NE`: 3
- `NH`: 3
- `NJ`: 3
- `NM`: 3
- `NV`: 3
- `NY`: 3
- `OH`: 3
- `OK`: 3
- `OR`: 3
- `PA`: 3
- `RI`: 3
- `SC`: 2
- `SD`: 3
- `TN`: 4
- `TX`: 3
- `UT`: 3
- `VA`: 3
- `VT`: 3
- `WA`: 3
- `WI`: 3
- `WV`: 2
- `WY`: 4

### `source_officialness_rating`

- `official_municipal`: 48
- `official_state_repository`: 23
- `official_union`: 17
- `uncertain`: 44
- `unknown`: 18

### `artifact_byte_size_bin`

- `large_2_to_5_mib`: 29
- `medium_512_kib_to_2_mib`: 45
- `small_le_512_kib`: 49
- `very_large_gt_5_mib`: 27

### `candidate_source_type`

- `arbitration_award`: 10
- `cba`: 75
- `factfinding`: 3
- `memorandum_or_settlement`: 17
- `ordinance_or_policy`: 15
- `pay_plan`: 1
- `wage_schedule_or_compensation_plan`: 29

### `document_type_rating`

- `cba_candidate`: 75
- `unknown`: 75
