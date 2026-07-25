# PDF-Readiness Pilot Input Audit

## Result

**PASS.** The offline planner selected exactly 1974 unique retained PDFs from 2124 eligible artifacts.

- source ledger rows: 2150
- eligible retained PDFs: 2124
- terminal readiness rows excluded: 150
- retained PDFs remaining after exclusion: 1974
- selected rows: 1974
- lane rows: 494 / 494 / 493 / 493
- selected artifact bytes: 4165691340
- duplicate readiness/source-review/candidate IDs: 0 / 0 / 0
- nonblank paths/hashes: 1974 / 1974
- URLs opened: 0
- PDFs opened or parsed during planning: 0

## Selected distributions

### `source_review_pilot_id`

- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 463
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1393
- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 118

### `priority_for_content_review`

- `p1`: 1661
- `p2`: 313

### `unit_type`

- `fire`: 461
- `non_safety`: 651
- `police`: 862

### `state`

- `AK`: 11
- `CA`: 256
- `CO`: 11
- `CT`: 33
- `DC`: 2
- `DE`: 7
- `FL`: 115
- `GA`: 1
- `IA`: 29
- `ID`: 7
- `IL`: 196
- `IN`: 7
- `KS`: 10
- `KY`: 2
- `MA`: 70
- `MD`: 14
- `ME`: 21
- `MI`: 110
- `MN`: 56
- `MO`: 13
- `MT`: 20
- `NE`: 14
- `NH`: 20
- `NJ`: 25
- `NM`: 11
- `NV`: 19
- `NY`: 28
- `OH`: 534
- `OK`: 13
- `OR`: 66
- `PA`: 27
- `RI`: 10
- `SD`: 7
- `TX`: 36
- `VA`: 7
- `VT`: 3
- `WA`: 102
- `WI`: 61

### `source_officialness_rating`

- `official_municipal`: 737
- `official_state_repository`: 513
- `official_union`: 35
- `uncertain`: 633
- `unknown`: 56

### `artifact_byte_size_bin`

- `large_2_to_5_mib`: 463
- `medium_512_kib_to_2_mib`: 980
- `small_le_512_kib`: 341
- `very_large_gt_5_mib`: 190

### `candidate_source_type`

- `cba`: 1928
- `memorandum_or_settlement`: 6
- `ordinance_or_policy`: 5
- `wage_schedule_or_compensation_plan`: 35

### `document_type_rating`

- `cba_candidate`: 1928
- `unknown`: 46
