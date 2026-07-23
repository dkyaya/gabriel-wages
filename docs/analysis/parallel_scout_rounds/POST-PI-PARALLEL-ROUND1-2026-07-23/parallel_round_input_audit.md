# POST-PI-PARALLEL-ROUND1-2026-07-23 — Parallel Round Input Audit

Disposition: **PASS — 2 offline lane inputs locked; no live or dry run executed.**

- Lanes: 2
- Rows per lane: 150
- Total planned rows: 300
- Unique municipality IDs: 300
- Municipality overlap: 0
- Unique nonblank Census IDs: 300
- Census-ID overlap: 0
- Missing Census IDs: 0
- Complete exact five-hint sets: 300/300
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Combined states: CT 12, FL 57, IA 6, IN 2, KY 1, MA 20, MD 3, MI 25, MT 2, NE 1, NM 6, NV 1, OH 84, OR 31, RI 3, SD 1, WA 35, WI 10

## Locked lane files

- `lane_1`: 150 rows; SHA-256 `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`; states CT 11, FL 27, IA 1, MA 3, MI 17, NV 1, OH 44, OR 22, WA 21, WI 3.
- `lane_2`: 150 rows; SHA-256 `f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`; states CT 1, FL 30, IA 5, IN 2, KY 1, MA 17, MD 3, MI 8, MT 2, NE 1, NM 6, OH 40, OR 9, RI 3, SD 1, WA 14, WI 7.


Lane 1 is the existing Post-PI Wave 1 coordinator input copied byte-for-byte.
Additional lanes are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage,
canonical, failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
