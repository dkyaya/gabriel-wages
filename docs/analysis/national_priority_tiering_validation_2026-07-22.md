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

- Minimum score: 37.142
- Maximum score: 82.873
- Scores outside 0–100: 0
- Invalid tier labels: 0

| Tier | Rows | Eligible |
|---|---:|---:|
| Tier 1 | 1,780 | 1,471 |
| Tier 2 | 3,559 | 3,528 |
| Tier 3 | 7,118 | 6,999 |
| Tier 4 | 10,676 | 10,625 |
| Tier 5 | 12,456 | 12,456 |

## Operational checks

- Future-scout eligible rows: 35,079
- Already-covered rows incorrectly eligible: 0
- Failure-only retry rows: 10
- Failure-only rows retained as eligible: 10
- Canonical rows excluded: 19

## Confidence

- High: 4,990
- Medium: 4,080
- Low: 26,519

## Spot-check logic

- Population is monotonic within otherwise identical synthetic test rows.
- Township status reduces, but does not zero, government-type value.
- Missing population produces a bounded score and low confidence rather than an invented value.
- Zero- and tiny-sample states receive pooled smoothed rates and low confidence.
- Existing candidate evidence never makes an already-covered municipality future-scout eligible.
- The builder imports no network, OpenAI, GABRIEL, requests, or URL-fetching module.

Top-target identity spot checks:

- 1: Oklahoma City, OK — CITY OF OKLAHOMA CITY; population 702,767; score 78.002; Tier 1; confidence low.
- 2: Phoenix, AZ — CITY OF PHOENIX; population 1,650,070; score 77.973; Tier 1; confidence low.
- 3: Portland, OR — CITY OF PORTLAND; population 630,498; score 77.877; Tier 1; confidence low.
- 4: Milwaukee, WI — CITY OF MILWAUKEE; population 561,385; score 77.745; Tier 1; confidence low.
- 5: Atlanta, GA — CITY OF ATLANTA; population 510,823; score 77.636; Tier 1; confidence low.

Failure-retry spot checks: Stockton CA (Tier 1, high); Redding CA (Tier 1, high); Oakland CA (Tier 1, high); Moreno Valley CA (Tier 1, high); Oxnard CA (Tier 1, high).

## Output hashes

| Output | SHA-256 |
|---|---|
| `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` | `2b156d63b65a51e5e74c58fb7f03ebbabcf539d18cfe2cbd301236d046299eeb` |
| `docs/analysis/national_municipality_priority_tier_summary_2026-07-22.csv` | `eab31cfb943cea8ec0099f01d6b11ce989b4e3f4142d5574298042cb2938bcee` |
| `docs/analysis/state_priority_summary_2026-07-22.csv` | `84c90247de3d3113ccfd8846e9e57a332cfa39a8d77245fd4e3f4111999e72d1` |
| `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` | `4f8f92de6e6a54f1ecb3a396ff21395cca592234ed90113122ce21db435ccb98` |
| `docs/analysis/national_failure_retry_priority_2026-07-22.csv` | `e641f25b3d7373c5ca787713466093fb024d1e09b54cb8992b3935cebf8c9e9a` |

## Sensitivity and limitations

The separate sensitivity report compares baseline, population-heavy, and state-yield-heavy top-500 rankings. Rank changes near cutoffs are expected because the empirical state evidence covers only seven states. The score should be rebuilt after each additional 300–600 successful municipality scouts and should never be interpreted as a substantive labor-market estimate.
