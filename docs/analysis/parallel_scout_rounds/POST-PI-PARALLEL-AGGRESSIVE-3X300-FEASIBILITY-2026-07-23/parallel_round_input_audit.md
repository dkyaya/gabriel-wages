# POST-PI-PARALLEL-AGGRESSIVE-3X300-FEASIBILITY-2026-07-23 — Parallel Round Input Audit

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
- Combined states: AK 2, AR 15, CA 103, CT 2, DE 6, FL 92, IA 22, ID 8, IN 41, KS 8, KY 24, LA 5, MA 15, MD 15, ME 10, MI 65, MN 41, MO 7, MS 6, MT 4, ND 7, NE 9, NH 7, NM 10, NV 4, NY 13, OH 134, OK 17, OR 40, PA 9, RI 4, SD 7, UT 1, VA 1, VT 2, WA 60, WI 75, WV 3, WY 6

## Locked lane files

- `lane_1`: 300 rows; SHA-256 `2a19781c3cc6d1a10c03174b494f60c8df6c1414261e509e948977b620e040e9`; states AK 2, AR 4, CA 7, CT 1, DE 1, FL 49, IA 9, ID 2, IN 15, KY 4, MA 10, MD 4, ME 1, MI 23, MN 10, MT 3, ND 3, NE 2, NH 3, NM 2, NV 2, NY 1, OH 59, OK 5, OR 22, RI 2, VT 1, WA 24, WI 27, WY 2.
- `lane_2`: 300 rows; SHA-256 `ed36a0876216fe7084bc54b1008c4b176ffe6b3953d904fe9d1cef5ff43b9ec0`; states AR 4, CA 32, CT 1, DE 2, FL 22, IA 10, ID 5, IN 17, KS 4, KY 11, LA 2, MA 4, MD 4, ME 3, MI 18, MN 15, MO 2, MS 3, MT 1, ND 1, NE 6, NH 2, NM 5, NY 5, OH 48, OK 6, OR 10, PA 2, RI 1, SD 4, WA 27, WI 19, WV 2, WY 2.
- `lane_3`: 300 rows; SHA-256 `c13d587a3d70aa19f4ae27fe5a84890e9a5420242dd2199413c7c0990c7942c2`; states AR 7, CA 64, DE 3, FL 21, IA 3, ID 1, IN 9, KS 4, KY 9, LA 3, MA 1, MD 7, ME 6, MI 24, MN 16, MO 5, MS 3, ND 3, NE 1, NH 2, NM 3, NV 2, NY 7, OH 27, OK 6, OR 8, PA 7, RI 1, SD 3, UT 1, VA 1, VT 1, WA 9, WI 29, WV 1, WY 2.


All lanes were selected in one deterministic pass. Additional lane rows are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage, canonical,
failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
