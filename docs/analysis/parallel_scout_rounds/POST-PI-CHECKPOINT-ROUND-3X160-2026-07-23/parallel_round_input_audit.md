# POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23 — Parallel Round Input Audit

Disposition: **PASS — 3 offline lane inputs locked; no live or dry run executed.**

- Lanes: 3
- Rows per lane: 160
- Profile: `custom_explicit`
- Lane-start stagger: 240 seconds (4 minutes)
- Total planned rows: 480
- Unique municipality IDs: 480
- Municipality overlap: 0
- Unique nonblank Census IDs: 480
- Census-ID overlap: 0
- Missing Census IDs: 0
- Complete exact five-hint sets: 480/480
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Combined states: AK 6, AL 4, CA 83, DE 4, IA 1, ID 3, KS 7, LA 8, MA 2, MD 16, ME 13, MN 28, MO 17, MS 21, MT 10, ND 3, NE 2, NH 8, NM 12, NV 4, NY 20, OH 102, PA 15, RI 2, SD 14, TN 7, UT 11, VA 8, VT 3, WI 30, WV 8, WY 8
- Priority tiers: Tier 1 480
- Confidence: high 187, low 199, medium 94
- Priority score min/median/max: 72.526 / 73.114 / 76.212

## Checkpoint projection

- Current successful scout coverage: 1,537/2,000
- Remaining before this planned round: 463
- Maximum post-round coverage if all 480 rows parse: 2,017
- Recent reference parseable rate: 446/450 (99.111%)
- Expected parseable rows at that rate: approximately 476
- Expected post-round successful coverage after a later serial merge: approximately 2,013/2,000
- Expected checkpoint margin: +13

This projection is an operational planning estimate, not live evidence or a
guarantee. Official accounting remains unchanged until completed lane outputs
pass audit and a separately authorized serial merge runs.

## Locked lane files

- `lane_1`: 160 rows; SHA-256 `fb924eea0bee80d3073235815b475ac6a238287d49c70d7d028490802ee82a3c`; states AK 1, CA 3, DE 4, KS 2, LA 5, MA 1, MD 12, ME 9, MN 4, MO 7, MS 6, MT 5, NH 7, NM 5, NV 1, NY 4, OH 57, PA 2, RI 2, SD 11, VA 1, VT 2, WI 1, WV 5, WY 3.
- `lane_2`: 160 rows; SHA-256 `812204917afeac05fb0e433a8439a56fa9063ea0d09603c602345cd1713450ed`; states AK 3, AL 1, CA 40, ID 2, KS 2, LA 1, MA 1, MD 1, ME 1, MN 16, MO 3, MS 9, MT 3, NE 1, NH 1, NM 4, NV 3, NY 8, OH 30, PA 7, SD 2, TN 3, UT 1, VA 2, VT 1, WI 14.
- `lane_3`: 160 rows; SHA-256 `cac770459eda2a04b9e9410a8853432e75fa0d728adb06278264352fbe2adc1d`; states AK 2, AL 3, CA 40, IA 1, ID 1, KS 3, LA 2, MD 3, ME 3, MN 8, MO 7, MS 6, MT 2, ND 3, NE 1, NM 3, NY 8, OH 15, PA 6, SD 1, TN 4, UT 10, VA 5, WI 15, WV 3, WY 5.


All lanes were selected in one deterministic pass. Additional lane rows are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage, canonical,
failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
