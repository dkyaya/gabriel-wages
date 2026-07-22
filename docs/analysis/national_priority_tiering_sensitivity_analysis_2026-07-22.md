# National Priority Tiering Sensitivity Analysis

Date: 2026-07-22

All variants use the same authoritative rows, status exclusions, smoothed state evidence, and stable tie-breaks. Only component weights change. Rankings below are among future-scout-eligible municipalities.

## Weight settings

| Setting | Population | Government type | State yield | Research design | Geographic | Completeness | Existing evidence |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 30 | 10 | 20 | 20 | 10 | 5 | 5 |
| population_heavier | 40 | 10 | 15 | 15 | 10 | 5 | 5 |
| state_yield_heavier | 25 | 10 | 30 | 20 | 5 | 5 | 5 |

## Top-500 overlap

| Comparison | Shared top 500 | Overlap |
|---|---:|---:|
| Baseline vs population_heavier | 480 | 96.0% |
| Baseline vs state_yield_heavier | 257 | 51.4% |

## Largest rank changes within the union of variant top-500 pools

Ranks are baseline / population-heavier / state-yield-heavier.

| Municipality | State | Population | Ranks | Largest absolute change |
|---|---|---:|---:|---:|
| Grand Terrace | CA | 12,939 | 3189/3600/483 | 2,706 |
| La Palma | CA | 15,029 | 2988/3368/409 | 2,579 |
| Albany | CA | 19,097 | 2869/3166/348 | 2,521 |
| Signal Hill | CA | 11,249 | 2965/3496/477 | 2,488 |
| Lindsay | CA | 12,496 | 2914/3406/436 | 2,478 |
| Commerce | CA | 11,672 | 2891/3419/452 | 2,439 |
| Laguna Woods | CA | 16,998 | 2765/3144/353 | 2,412 |
| San Marino | CA | 11,977 | 2841/3364/432 | 2,409 |
| Coronado | CA | 18,437 | 2688/3050/337 | 2,351 |
| Palos Verdes Estates | CA | 12,646 | 2736/3259/402 | 2,334 |
| Orange Cove | CA | 9,497 | 2797/3465/485 | 2,312 |
| Galt | CA | 25,767 | 2573/2809/274 | 2,299 |
| Hillsborough | CA | 10,883 | 2704/3305/427 | 2,277 |
| Auburn | CA | 13,658 | 2641/3150/368 | 2,273 |
| Scotts Valley | CA | 11,879 | 2671/3238/405 | 2,266 |
| Hawaiian Gardens | CA | 13,396 | 2630/3152/373 | 2,257 |
| Half Moon Bay | CA | 11,105 | 2664/3271/420 | 2,244 |
| Morro Bay | CA | 10,589 | 2613/3249/421 | 2,192 |
| Carpinteria | CA | 12,828 | 2545/3096/366 | 2,179 |
| Newman | CA | 12,207 | 2559/3135/381 | 2,178 |

## State composition of each top 500

| State | Baseline | Population-heavy | State-yield-heavy |
|---|---:|---:|---:|
| AK | 1 | 1 | 1 |
| AL | 14 | 13 | 7 |
| AR | 9 | 9 | 3 |
| AZ | 21 | 21 | 14 |
| CA | 9 | 6 | 223 |
| CO | 24 | 24 | 13 |
| CT | 10 | 11 | 5 |
| DC | 1 | 1 | 1 |
| DE | 1 | 1 | 0 |
| FL | 56 | 59 | 27 |
| GA | 17 | 19 | 10 |
| HI | 1 | 1 | 1 |
| IA | 12 | 12 | 5 |
| ID | 6 | 8 | 3 |
| IL | 1 | 1 | 3 |
| IN | 16 | 18 | 6 |
| KS | 9 | 9 | 5 |
| KY | 4 | 4 | 2 |
| LA | 8 | 8 | 4 |
| MA | 33 | 24 | 36 |
| MD | 5 | 5 | 1 |
| ME | 1 | 1 | 0 |
| MI | 25 | 26 | 7 |
| MN | 17 | 19 | 5 |
| MO | 14 | 14 | 6 |
| MS | 3 | 4 | 1 |
| MT | 4 | 4 | 1 |
| NC | 24 | 24 | 10 |
| ND | 3 | 3 | 1 |
| NE | 3 | 3 | 2 |
| NH | 2 | 2 | 1 |
| NM | 4 | 4 | 3 |
| NV | 6 | 6 | 5 |
| OH | 15 | 15 | 2 |
| OK | 11 | 10 | 5 |
| OR | 12 | 13 | 7 |
| PA | 5 | 1 | 29 |
| RI | 4 | 4 | 1 |
| SC | 8 | 8 | 3 |
| SD | 2 | 2 | 1 |
| TN | 15 | 15 | 7 |
| UT | 15 | 17 | 5 |
| VA | 11 | 11 | 10 |
| WA | 24 | 25 | 12 |
| WI | 11 | 11 | 6 |
| WV | 1 | 1 | 0 |
| WY | 2 | 2 | 0 |

## Interpretation

The baseline retains 96.0% of its top 500 under the population-heavy variant and 51.4% under the state-yield-heavy variant. Population is the largest single baseline component at 30 points, but it is below one-third of the score and cannot by itself determine a tier. State yield and research-design evidence jointly contribute 40 points but are empirically Bayes-smoothed with a 25-municipality national prior, preventing zero- or tiny-sample states from receiving extreme scores.

The baseline is suitable for operational use if top-500 overlap remains substantial in both variants; rank movement should be treated as expected uncertainty near cutoffs rather than factual disagreement. This analysis does not establish that any municipality has a union, safety department, civilian bargaining unit, source portal, or wage gap.
