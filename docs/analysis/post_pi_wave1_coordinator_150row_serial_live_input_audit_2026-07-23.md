# Post-PI Wave 1 Coordinator 150-Row Serialized Live Input Audit

Date: 2026-07-23

Disposition: **PASS — locked for the coordinator evidence gates.**

- File: `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`
- SHA-256: `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Source order: Worker 1 ranks 1–50, Worker 2 ranks 51–100, Worker 3 ranks 101–150.

## Structural and exclusion gates

- PASS — exactly 150 rows.
- PASS — ranks exactly 1–150 in order with no gaps.
- PASS — worker counts exactly 50/50/50.
- PASS — ordinary future-scout eligible.
- PASS — no retry rows.
- PASS — no failure-only rows.
- PASS — no current successful coverage.
- PASS — no current canonical municipalities.
- PASS — no known failure/retry municipality.
- PASS — no prior officially covered/scouted row.
- PASS — unique nonblank municipality IDs.
- PASS — unique nonblank Census government IDs.
- PASS — one exact future live queue ID.
- PASS — five attached deterministic hints for every row.
- PASS — exact prepared top-150 identity/order preserved.
- PASS — exact Worker 1 → Worker 2 → Worker 3 file order.

The current committed coverage table, failure-only priority file, prepared top-150 file, four prior official Tier 1 input artifacts, and deterministic hints file were all reconciled by municipality ID. No ad hoc row substitution occurred.

## Composition

- State distribution: CT 11, FL 27, IA 1, MA 3, MI 17, NV 1, OH 44, OR 22, WA 21, WI 3.
- Priority tier distribution: Tier 1 150.
- Priority score min/median/max: 75.280 / 75.881 / 77.268.
- Confidence distribution: low 99, medium 51.
- Future live queue ID: `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23` on all 150 rows.
- Search hints: all five attached and exact for 150/150 rows.

## Checkpoint projection

If all 150 rows become parseable official coverage, the checkpoint would move from 794/2,000 to 944/2,000, leaving 1,056. That is approximately 8–9 additional 150-row waves, depending on parseable yield.

This audit is offline preparation only. It does not call a model or hosted search, verify sources, alter queue/coverage accounting, ingest contracts, run `gabriel.codify`, calculate wage gaps, or make causal claims.
