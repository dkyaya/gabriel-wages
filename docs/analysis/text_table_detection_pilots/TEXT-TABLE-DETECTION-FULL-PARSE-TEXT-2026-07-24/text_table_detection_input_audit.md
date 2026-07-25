# Text/Table Detection Pilot Input Audit

## Result

**PASS.** The offline planner selected exactly 1828 unique parse-text-layer candidates from 1828 eligible durable readiness rows.

- durable readiness rows: 2124
- parse-text candidates: 1828
- OCR-later candidates excluded: 296
- selected rows: 1828
- lane rows: 457 / 457 / 457 / 457
- represented pages: 94200
- duplicate detection/readiness/source-review/candidate IDs: 0 / 0 / 0 / 0
- URLs opened: 0
- PDFs opened during planning: 0

## Selected distributions

### `source_review_pilot_id`

- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 404
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1297
- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 127

### `priority_for_content_review`

- `p1`: 1501
- `p2`: 327

### `unit_type`

- `fire`: 439
- `non_safety`: 607
- `police`: 782

### `state`

- `AK`: 14
- `AL`: 2
- `AR`: 2
- `AZ`: 3
- `CA`: 238
- `CO`: 13
- `CT`: 23
- `DC`: 2
- `DE`: 9
- `FL`: 102
- `GA`: 4
- `HI`: 3
- `IA`: 29
- `ID`: 9
- `IL`: 131
- `IN`: 8
- `KS`: 11
- `KY`: 5
- `LA`: 3
- `MA`: 54
- `MD`: 11
- `ME`: 13
- `MI`: 94
- `MN`: 50
- `MO`: 13
- `MS`: 3
- `MT`: 20
- `NC`: 2
- `ND`: 2
- `NE`: 17
- `NH`: 17
- `NJ`: 7
- `NM`: 14
- `NV`: 21
- `NY`: 26
- `OH`: 528
- `OK`: 14
- `OR`: 67
- `PA`: 19
- `RI`: 7
- `SC`: 2
- `SD`: 10
- `TN`: 1
- `TX`: 34
- `UT`: 3
- `VA`: 9
- `VT`: 2
- `WA`: 95
- `WI`: 57
- `WV`: 1
- `WY`: 4

### `source_officialness_rating`

- `official_municipal`: 648
- `official_state_repository`: 525
- `official_union`: 42
- `uncertain`: 546
- `unknown`: 67

### `candidate_source_type`

- `arbitration_award`: 10
- `cba`: 1719
- `factfinding`: 2
- `memorandum_or_settlement`: 20
- `ordinance_or_policy`: 19
- `wage_schedule_or_compensation_plan`: 58

### `document_type_rating`

- `cba_candidate`: 1719
- `unknown`: 109

### `page_count_bin`

- `11_to_25`: 174
- `1_to_10`: 76
- `26_to_50`: 846
- `51_to_100`: 617
- `over_100`: 115

### `text_layer_status`

- `partial`: 220
- `present`: 1608
