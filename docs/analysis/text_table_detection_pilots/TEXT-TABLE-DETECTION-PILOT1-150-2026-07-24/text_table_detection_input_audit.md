# Text/Table Detection Pilot Input Audit

## Result

**PASS.** The offline planner selected exactly 150 unique parse-text-layer candidates from 1828 eligible durable readiness rows.

- durable readiness rows: 2124
- parse-text candidates: 1828
- OCR-later candidates excluded: 296
- selected rows: 150
- lane rows: 50 / 50 / 50
- represented pages: 7309
- duplicate detection/readiness/source-review/candidate IDs: 0 / 0 / 0 / 0
- URLs opened: 0
- PDFs opened during planning: 0

## Selected distributions

### `source_review_pilot_id`

- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 35
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 85
- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 30

### `priority_for_content_review`

- `p1`: 67
- `p2`: 83

### `unit_type`

- `fire`: 44
- `non_safety`: 55
- `police`: 51

### `state`

- `AK`: 3
- `AL`: 2
- `AR`: 2
- `AZ`: 3
- `CA`: 3
- `CO`: 3
- `CT`: 3
- `DC`: 2
- `DE`: 4
- `FL`: 3
- `GA`: 4
- `HI`: 3
- `IA`: 3
- `ID`: 3
- `IL`: 3
- `IN`: 3
- `KS`: 3
- `KY`: 4
- `LA`: 3
- `MA`: 3
- `MD`: 4
- `ME`: 3
- `MI`: 3
- `MN`: 3
- `MO`: 4
- `MS`: 3
- `MT`: 5
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
- `TN`: 1
- `TX`: 3
- `UT`: 3
- `VA`: 3
- `VT`: 2
- `WA`: 3
- `WI`: 3
- `WV`: 1
- `WY`: 4

### `source_officialness_rating`

- `official_municipal`: 49
- `official_state_repository`: 24
- `official_union`: 18
- `uncertain`: 43
- `unknown`: 16

### `candidate_source_type`

- `arbitration_award`: 10
- `cba`: 76
- `factfinding`: 2
- `memorandum_or_settlement`: 17
- `ordinance_or_policy`: 17
- `wage_schedule_or_compensation_plan`: 28

### `document_type_rating`

- `cba_candidate`: 76
- `unknown`: 74

### `page_count_bin`

- `11_to_25`: 28
- `1_to_10`: 39
- `26_to_50`: 29
- `51_to_100`: 34
- `over_100`: 20

### `text_layer_status`

- `partial`: 43
- `present`: 107
