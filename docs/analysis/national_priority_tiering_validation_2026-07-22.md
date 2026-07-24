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

- Minimum score: 36.565
- Maximum score: 81.960
- Scores outside 0–100: 0
- Invalid tier labels: 0

| Tier | Rows | Eligible |
|---|---:|---:|
| Tier 1 | 1,780 | 245 |
| Tier 2 | 3,559 | 2,906 |
| Tier 3 | 7,118 | 6,889 |
| Tier 4 | 10,676 | 10,651 |
| Tier 5 | 12,456 | 12,456 |

## Operational checks

- Future-scout eligible rows: 33,147
- Already-covered rows incorrectly eligible: 0
- Failure-only retry rows: 28
- Failure-only rows retained as eligible: 28
- Canonical rows excluded: 19

## Confidence

- High: 18,838
- Medium: 13,180
- Low: 3,571

## Spot-check logic

- Population is monotonic within otherwise identical synthetic test rows.
- Township status reduces, but does not zero, government-type value.
- Missing population produces a bounded score and low confidence rather than an invented value.
- Zero- and tiny-sample states receive pooled smoothed rates and low confidence.
- Existing candidate evidence never makes an already-covered municipality future-scout eligible.
- The builder imports no network, OpenAI, GABRIEL, requests, or URL-fetching module.

Top-target identity spot checks:

- 1: Las Vegas, NV — CITY OF LAS VEGAS; population 660,929; score 76.668; Tier 1; confidence low.
- 2: Indianapolis city (balance), IN — CITY OF INDIANAPOLIS; population 879,293; score 76.112; Tier 1; confidence medium.
- 3: Framingham, MA — CITY OF FRAMINGHAM; population 71,875; score 76.038; Tier 1; confidence high.
- 4: Redding, CA — CITY OF REDDING; population 92,727; score 75.249; Tier 1; confidence high.
- 5: Oakland, CA — CITY OF OAKLAND; population 436,504; score 74.982; Tier 1; confidence high.

Failure-retry spot checks: Las Vegas NV (Tier 1, high); Indianapolis city (balance) IN (Tier 1, high); Framingham MA (Tier 1, high); Redding CA (Tier 1, high); Oakland CA (Tier 1, high).

## Output hashes

| Output | SHA-256 |
|---|---|
| `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` | `3aa0903987c909e36a23ce4654667ffc3e1083f67aa44657f86a36ba670aa3c0` |
| `docs/analysis/national_municipality_priority_tier_summary_2026-07-22.csv` | `da4716783132ab6a5b28a5221303d16c6ee1d98412aa32947999aeb985040e9a` |
| `docs/analysis/state_priority_summary_2026-07-22.csv` | `319662435c09b8ad67db8ca2597d5febefb0fc25a076585e1fa83a11607d4ee5` |
| `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` | `41ee3206f29478420a69a3b26cc73f3cb9431e531fe3df75a01f86a8e061d8b2` |
| `docs/analysis/national_failure_retry_priority_2026-07-22.csv` | `e192b69b55b3006e05c785965c03e5bd74488d49c02c654944e47e900de626db` |

## Sensitivity and limitations

The separate sensitivity report compares baseline, population-heavy, and state-yield-heavy top-500 rankings. Rank changes near cutoffs are expected because the empirical state evidence covers only seven states. The score should be rebuilt after each additional 300–600 successful municipality scouts and should never be interpreted as a substantive labor-market estimate.
