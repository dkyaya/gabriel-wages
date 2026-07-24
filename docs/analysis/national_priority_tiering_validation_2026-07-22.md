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

- Minimum score: 37.578
- Maximum score: 84.259
- Scores outside 0–100: 0
- Invalid tier labels: 0

| Tier | Rows | Eligible |
|---|---:|---:|
| Tier 1 | 1,780 | 628 |
| Tier 2 | 3,559 | 3,420 |
| Tier 3 | 7,118 | 6,934 |
| Tier 4 | 10,676 | 10,608 |
| Tier 5 | 12,456 | 12,456 |

## Operational checks

- Future-scout eligible rows: 34,046
- Already-covered rows incorrectly eligible: 0
- Failure-only retry rows: 27
- Failure-only rows retained as eligible: 27
- Canonical rows excluded: 19

## Confidence

- High: 10,279
- Medium: 13,159
- Low: 12,151

## Spot-check logic

- Population is monotonic within otherwise identical synthetic test rows.
- Township status reduces, but does not zero, government-type value.
- Missing population produces a bounded score and low confidence rather than an invented value.
- Zero- and tiny-sample states receive pooled smoothed rates and low confidence.
- Existing candidate evidence never makes an already-covered municipality future-scout eligible.
- The builder imports no network, OpenAI, GABRIEL, requests, or URL-fetching module.

Top-target identity spot checks:

- 1: Las Vegas, NV — CITY OF LAS VEGAS; population 660,929; score 79.537; Tier 1; confidence low.
- 2: Newark, OH — CITY OF NEWARK; population 51,046; score 78.911; Tier 1; confidence high.
- 3: Kansas City, MO — CITY OF KANSAS CITY; population 510,704; score 78.378; Tier 1; confidence low.
- 4: Indianapolis city (balance), IN — CITY OF INDIANAPOLIS; population 879,293; score 77.359; Tier 1; confidence medium.
- 5: Framingham, MA — CITY OF FRAMINGHAM; population 71,875; score 77.299; Tier 1; confidence high.

Failure-retry spot checks: Las Vegas NV (Tier 1, high); Newark OH (Tier 1, high); Kansas City MO (Tier 1, high); Indianapolis city (balance) IN (Tier 1, high); Framingham MA (Tier 1, high).

## Output hashes

| Output | SHA-256 |
|---|---|
| `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` | `504a1301f6f6670c35e835d47057cc8a035f5499bac444cf8db147401e3855fc` |
| `docs/analysis/national_municipality_priority_tier_summary_2026-07-22.csv` | `ea414889cb7651e0394e634a2d8f403c41d76ef264a7c818daa00c31a2e16ef3` |
| `docs/analysis/state_priority_summary_2026-07-22.csv` | `b08869a16264eaaef05893c3b449744c49907f0433f39ae26902e13e63ea1cd7` |
| `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` | `b8b3c5f427373dff9438ac32c6ea93ff6b25b4ebbcf7e201446a5662bb5bd71f` |
| `docs/analysis/national_failure_retry_priority_2026-07-22.csv` | `19c1e7b296472a6f4d494c0dc098da3d9ac589d92cb5302e87d93fb6cb314d94` |

## Sensitivity and limitations

The separate sensitivity report compares baseline, population-heavy, and state-yield-heavy top-500 rankings. Rank changes near cutoffs are expected because the empirical state evidence covers only seven states. The score should be rebuilt after each additional 300–600 successful municipality scouts and should never be interpreted as a substantive labor-market estimate.
