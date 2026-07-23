# POST-PI-PARALLEL-ROUND2-3X150-2026-07-23 — Parallel Round Input Audit

Disposition: **PASS — 3 offline lane inputs locked; no live or dry run executed.**

- Lanes: 3
- Rows per lane: 150
- Profile: `standard_150`
- Lane-start stagger: 240 seconds (4 minutes)
- Total planned rows: 450
- Unique municipality IDs: 450
- Municipality overlap: 0
- Unique nonblank Census IDs: 450
- Census-ID overlap: 0
- Missing Census IDs: 0
- Complete exact five-hint sets: 450/450
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Combined states: AK 2, AR 5, CA 15, CT 2, DE 2, FL 60, IA 16, ID 5, IN 26, KS 1, KY 13, MA 12, MD 6, ME 2, MI 34, MN 17, MS 1, MT 4, ND 4, NE 6, NH 3, NM 2, NV 2, NY 2, OH 89, OK 9, OR 29, RI 2, SD 1, VT 1, WA 41, WI 33, WY 3

## Locked lane files

- `lane_1`: 150 rows; SHA-256 `320f4915a1aa487e791f67a31826572ac275edf5d4b87ecb99eec4b26279d86a`; states CA 2, CT 1, DE 1, FL 24, IA 3, IN 9, KY 1, MA 7, MD 2, ME 1, MI 13, MN 3, MT 1, ND 1, NE 1, NH 1, NV 1, OH 31, OK 2, OR 13, WA 16, WI 14, WY 2.
- `lane_2`: 150 rows; SHA-256 `e06f9706d69bce72cabac6f57c8581d16651d0b00ecec5752787edda5fc5500a`; states AK 2, AR 4, CA 5, FL 25, IA 6, ID 2, IN 6, KY 3, MA 3, MD 2, MI 10, MN 7, MT 2, ND 2, NE 1, NH 2, NM 2, NV 1, NY 1, OH 28, OK 3, OR 9, RI 2, VT 1, WA 8, WI 13.
- `lane_3`: 150 rows; SHA-256 `501e36ff504ec2d5e3a1126eb1315db6fb31bbe5852c2be2590794661dd50665`; states AR 1, CA 8, CT 1, DE 1, FL 11, IA 7, ID 3, IN 11, KS 1, KY 9, MA 2, MD 2, ME 1, MI 11, MN 7, MS 1, MT 1, ND 1, NE 4, NY 1, OH 30, OK 4, OR 7, SD 1, WA 17, WI 6, WY 1.


All lanes were selected in one deterministic pass. Additional lane rows are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage, canonical,
failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
