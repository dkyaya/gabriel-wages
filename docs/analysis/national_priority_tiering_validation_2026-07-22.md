# National Priority Tiering Validation

Date: 2026-07-22

Disposition: **PASS — identity, schema, score, tier, operational-status, sensitivity, and deterministic-output checks passed.**

## Schema and identity

- Authoritative rows preserved: 35,589
- Unique municipality IDs: 35,589
- Unique Census government IDs: 35,589
- Population missing: 0
- County context missing: 0
- Prohibited employer/geography pairs eligible: 0

## Score and tier bounds

- Minimum score: 37.170
- Maximum score: 85.371
- Scores outside 0–100: 0
- Invalid tier labels: 0

| Tier | Rows | Eligible |
|---|---:|---:|
| Tier 1 | 1,780 | 1,227 |
| Tier 2 | 3,559 | 3,478 |
| Tier 3 | 7,118 | 7,008 |
| Tier 4 | 10,676 | 10,620 |
| Tier 5 | 12,456 | 12,456 |

## Operational checks

- Future-scout eligible rows: 34,789
- Already-covered rows incorrectly eligible: 0
- Failure-only retry rows: 20
- Failure-only rows retained as eligible: 20
- Canonical rows excluded: 19

## Confidence

- High: 4,990
- Medium: 6,035
- Low: 24,564

## Spot-check logic

- Population is monotonic within otherwise identical synthetic test rows.
- Township status reduces, but does not zero, government-type value.
- Missing population produces a bounded score and low confidence rather than an invented value.
- Zero- and tiny-sample states receive pooled smoothed rates and low confidence.
- Existing candidate evidence never makes an already-covered municipality future-scout eligible.
- The builder imports no network, OpenAI, GABRIEL, requests, or URL-fetching module.

Top-target identity spot checks:

- 1: Tampa, FL — CITY OF TAMPA; population 403,364; score 79.264; Tier 1; confidence medium.
- 2: Vancouver, WA — CITY OF VANCOUVER; population 196,442; score 79.076; Tier 1; confidence medium.
- 3: Indianapolis city (balance), IN — CITY OF INDIANAPOLIS; population 879,293; score 78.490; Tier 1; confidence low.
- 4: Las Vegas, NV — CITY OF LAS VEGAS; population 660,929; score 78.283; Tier 1; confidence low.
- 5: Lake Oswego, OR — CITY OF LAKE OSWEGO; population 39,924; score 77.268; Tier 1; confidence low.

Failure-retry spot checks: Tampa FL (Tier 1, high); Vancouver WA (Tier 1, high); Indianapolis city (balance) IN (Tier 1, high); Las Vegas NV (Tier 1, high); Fort Wayne IN (Tier 1, high).

## Output hashes

| Output | SHA-256 |
|---|---|
| `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` | `45226a6773561c3e8ac62795bd997fa40ac5a5fe6b02ad0d950f2aedb7685dd8` |
| `docs/analysis/national_municipality_priority_tier_summary_2026-07-22.csv` | `d658b8832619500dbb5d0fc0c0e76a95a9e1897752ad4ac566792b1fd589665e` |
| `docs/analysis/state_priority_summary_2026-07-22.csv` | `e2d1097ba19871e8a1255d3ba050123ba99824c314768e64eef64e4485b0e753` |
| `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` | `1fbeb97f1f1d3860e75c7db5b65491a33a27f03a16c9046885317c84e81bc414` |
| `docs/analysis/national_failure_retry_priority_2026-07-22.csv` | `45e672c4d052a18ddfdc48611b1e501c590e13f13fd34610f09928f09fdd2b13` |

## Sensitivity and limitations

The separate sensitivity report compares baseline, population-heavy, and state-yield-heavy top-500 rankings. Rank changes near cutoffs are expected because the empirical state evidence covers only seven states. The score should be rebuilt after each additional 300–600 successful municipality scouts and should never be interpreted as a substantive labor-market estimate.
