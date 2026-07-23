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
| Baseline vs population_heavier | 426 | 85.2% |
| Baseline vs state_yield_heavier | 344 | 68.8% |

## Largest rank changes within the union of variant top-500 pools

Ranks are baseline / population-heavier / state-yield-heavier.

| Municipality | State | Population | Ranks | Largest absolute change |
|---|---|---:|---:|---:|
| Imperial Beach | CA | 25,458 | 1794/2007/493 | 1,301 |
| Lemon Grove | CA | 27,569 | 1689/1909/460 | 1,229 |
| Barstow | CA | 24,964 | 1705/1952/481 | 1,224 |
| Loma Linda | CA | 25,111 | 1693/1936/478 | 1,215 |
| Laguna Hills | CA | 30,243 | 1564/1738/412 | 1,152 |
| Twentynine Palms | CA | 28,734 | 1563/1758/420 | 1,143 |
| Santa Fe Springs | CA | 20,174 | 1612/1928/494 | 1,118 |
| Dana Point | CA | 32,567 | 1492/1640/375 | 1,117 |
| Dixon | CA | 19,309 | 1604/1941/500 | 1,104 |
| Cape Girardeau | MO | 40,508 | 833/466/1931 | 1,098 |
| Norco | CA | 25,398 | 1514/1740/426 | 1,088 |
| Cudahy | CA | 21,723 | 1547/1823/463 | 1,084 |
| Calabasas | CA | 22,227 | 1526/1798/451 | 1,075 |
| San Juan Capistrano | CA | 34,754 | 1421/1566/348 | 1,073 |
| Newark | CA | 46,929 | 1345/1422/281 | 1,064 |
| Lafayette | CA | 25,048 | 1480/1724/422 | 1,058 |
| Duarte | CA | 23,131 | 1478/1743/436 | 1,042 |
| El Cerrito | CA | 25,552 | 1450/1700/413 | 1,037 |
| Dinuba | CA | 25,863 | 1447/1692/411 | 1,036 |
| Mountain House | CA | 25,909 | 1444/1688/409 | 1,035 |

## State composition of each top 500

| State | Baseline | Population-heavy | State-yield-heavy |
|---|---:|---:|---:|
| AK | 0 | 2 | 0 |
| AR | 2 | 6 | 1 |
| AZ | 1 | 1 | 0 |
| CA | 9 | 8 | 158 |
| CT | 13 | 12 | 12 |
| DE | 1 | 2 | 0 |
| FL | 89 | 72 | 95 |
| IA | 9 | 12 | 1 |
| ID | 0 | 5 | 0 |
| IL | 1 | 1 | 2 |
| IN | 15 | 26 | 2 |
| KS | 0 | 2 | 0 |
| KY | 2 | 8 | 0 |
| LA | 0 | 2 | 0 |
| MA | 28 | 27 | 28 |
| MD | 5 | 7 | 0 |
| ME | 1 | 2 | 0 |
| MI | 42 | 38 | 21 |
| MN | 5 | 16 | 0 |
| MO | 2 | 5 | 1 |
| MS | 0 | 2 | 0 |
| MT | 3 | 5 | 0 |
| ND | 1 | 4 | 0 |
| NE | 2 | 3 | 0 |
| NH | 1 | 3 | 0 |
| NM | 6 | 6 | 2 |
| NV | 3 | 3 | 2 |
| NY | 0 | 1 | 0 |
| OH | 122 | 101 | 81 |
| OK | 2 | 7 | 0 |
| OR | 46 | 30 | 40 |
| RI | 4 | 5 | 0 |
| SD | 1 | 1 | 0 |
| VT | 0 | 1 | 0 |
| WA | 54 | 44 | 50 |
| WI | 28 | 28 | 4 |
| WY | 2 | 2 | 0 |

## Interpretation

The baseline retains 85.2% of its top 500 under the population-heavy variant and 68.8% under the state-yield-heavy variant. Population is the largest single baseline component at 30 points, but it is below one-third of the score and cannot by itself determine a tier. State yield and research-design evidence jointly contribute 40 points but are empirically Bayes-smoothed with a 25-municipality national prior, preventing zero- or tiny-sample states from receiving extreme scores.

The baseline is suitable for operational use if top-500 overlap remains substantial in both variants; rank movement should be treated as expected uncertainty near cutoffs rather than factual disagreement. This analysis does not establish that any municipality has a union, safety department, civilian bargaining unit, source portal, or wage gap.
