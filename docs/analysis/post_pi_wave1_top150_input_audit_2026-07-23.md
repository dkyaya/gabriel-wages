# Post-PI Scale-Up Wave 1 Locked Top-150 Input Audit

Date: 2026-07-23

Disposition: **PASS — exactly 150 ordinary, current-eligible Tier 1 targets locked for worker dry-run preparation.**

## Eligibility and identity gates

- Rows: 150.
- Priority tiers: Tier 1 150.
- Tier 2 rows: 0; 1,208 ordinary Tier 1 rows were available after exact current exclusions, so no Tier 2 continuation was needed.
- Ordinary future-scout eligible: 150/150.
- Retry / failure-only: 0 / 0.
- Currently scout-covered / already canonical: 0 / 0.
- Prior official Tier 1 Wave 1 or Wave 2 inputs selected: 0.
- Unique municipality IDs: 150/150.
- Unique nonblank Census government IDs: 150/150; duplicate or missing Census IDs: 0.
- Allowed government categories: 150/150 municipal/place or intentionally eligible township/county-subdivision.
- Complete five-hint attachment: 150/150.

Selection used the canonical top-500 priority target file joined by exact municipality ID to the full current priority, coverage, failure-retry, prior-wave, canonical-status, and deterministic-hint files. It applied the required Tier → score → population → state → municipality-ID ordering. No row was substituted.

## Distribution

- Confidence: low 99, medium 51.
- Population min/median/max: 18,317 / 47,847.5 / 82,574; missing 0.
- Total priority score min/median/max: 75.280 / 75.881 / 77.268.
- Locked CSV SHA-256: `cf3287ddc831fd268b81334180fe35e11ffe472841f0a971dff09acbf9528079`.

| State | Rows |
|---|---:|
| CT | 11 |
| FL | 27 |
| IA | 1 |
| MA | 3 |
| MI | 17 |
| NV | 1 |
| OH | 44 |
| OR | 22 |
| WA | 21 |
| WI | 3 |

## Checkpoint projection

- Current: 794 / 2,000 (39.7%).
- If all 150 become parseable coverage: 944 / 2,000 (47.2%); 1,056 remain.
- At the latest wave's 148/150 parseable rate: approximately 942 / 2,000 (47.1%); 1,058 remain.
- From the current checkpoint, approximately 8–9 coordinated 150-row waves are needed; nine full waves are required to reach or exceed 2,000 arithmetically.

No scout, dry-run, live/API/model call, hosted search, preflight, URL verification, ingestion, codification, accounting mutation, wage-gap calculation, or causal analysis occurred.
