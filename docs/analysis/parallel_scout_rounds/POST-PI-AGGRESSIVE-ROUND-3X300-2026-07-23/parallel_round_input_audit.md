# POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23 — Parallel Round Input Audit

Disposition: **PASS — 3 offline lane inputs locked; no live or dry run executed.**

- Lanes: 3
- Rows per lane: 300
- Profile: `aggressive_300`
- Lane-start stagger: 480 seconds (8 minutes)
- Total planned rows: 900
- Unique municipality IDs: 900
- Municipality overlap: 0
- Unique nonblank Census IDs: 900
- Census-ID overlap: 0
- Missing Census IDs: 0
- Complete exact five-hint sets: 900/900
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Combined states: AK 10, AL 8, AR 8, AZ 4, CA 146, CO 5, CT 3, DE 6, IA 9, ID 9, IL 1, IN 2, KS 16, LA 19, MA 3, MD 27, ME 18, MI 3, MN 57, MO 39, MS 31, MT 14, ND 4, NE 6, NH 8, NM 20, NV 4, NY 43, OH 150, PA 52, RI 2, SC 2, SD 15, TN 15, UT 27, VA 14, VT 7, WI 73, WV 10, WY 10
- Priority tiers: Tier 1 606, Tier 2 294
- Confidence: high 303, low 349, medium 248
- Priority score min/median/max: 71.710 / 72.602 / 76.212

## Checkpoint projection

- Current successful scout coverage: 1,537/2,000
- Remaining before this planned round: 463
- Maximum post-round coverage if all 900 rows parse: 2,437
- Recent reference parseable rate: 446/450 (99.111%)
- Expected parseable rows at that rate: approximately 892
- Expected post-round successful coverage after a later serial merge: approximately 2,429/2,000
- Expected checkpoint margin: +429

This projection is an operational planning estimate, not live evidence or a
guarantee. Official accounting remains unchanged until completed lane outputs
pass audit and a separately authorized serial merge runs.
The planned round is expected to overshoot the approximately 2,000-covered checkpoint; this is intentional only when the user has explicitly approved that overshoot.

## Locked lane files

- `lane_1`: 300 rows; SHA-256 `2965bd65a3f5c6fe816f52c3e9f2ce657cd9ff472db6733233bcaa4ad081fee1`; states AK 4, AL 1, CA 37, DE 4, ID 2, KS 4, LA 6, MA 2, MD 13, ME 9, MN 18, MO 10, MS 15, MT 8, NE 1, NH 8, NM 8, NV 4, NY 11, OH 83, PA 8, RI 2, SD 11, TN 3, UT 1, VA 3, VT 2, WI 14, WV 5, WY 3.
- `lane_2`: 300 rows; SHA-256 `6057e1c71b74e0342127cad32a183c2b310af704ea5ebab61e5eb7483b3896a7`; states AK 3, AL 4, AR 3, AZ 1, CA 68, CO 1, CT 1, IA 3, ID 1, KS 5, LA 6, MA 1, MD 6, ME 6, MN 18, MO 13, MS 6, MT 4, ND 3, NE 1, NM 6, NY 14, OH 30, PA 19, SC 1, SD 4, TN 6, UT 16, VA 6, VT 4, WI 31, WV 4, WY 5.
- `lane_3`: 300 rows; SHA-256 `9934026f076a978957de5ae5767eed2ff236646d384285585aeecbddcc50843a`; states AK 3, AL 3, AR 5, AZ 3, CA 41, CO 4, CT 2, DE 2, IA 6, ID 6, IL 1, IN 2, KS 7, LA 7, MD 8, ME 3, MI 3, MN 21, MO 16, MS 10, MT 2, ND 1, NE 4, NM 6, NY 18, OH 37, PA 25, SC 1, TN 6, UT 10, VA 5, VT 1, WI 28, WV 1, WY 2.


All lanes were selected in one deterministic pass. Additional lane rows are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage, canonical,
failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
