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
| Baseline vs population_heavier | 335 | 67.0% |
| Baseline vs state_yield_heavier | 350 | 70.0% |

## Largest rank changes within the union of variant top-500 pools

Ranks are baseline / population-heavier / state-yield-heavier.

| Municipality | State | Population | Ranks | Largest absolute change |
|---|---|---:|---:|---:|
| Thomasville | NC | 27,435 | 1464/413/4459 | 2,995 |
| Mint Hill | NC | 27,815 | 1315/326/4302 | 2,987 |
| Kernersville | NC | 28,016 | 1603/476/4578 | 2,975 |
| Clayton | NC | 30,216 | 1430/370/4376 | 2,946 |
| Sanford | NC | 32,064 | 1678/487/4555 | 2,877 |
| New Bern | NC | 32,226 | 1673/484/4541 | 2,868 |
| Goldsboro | NC | 33,469 | 1623/456/4486 | 2,863 |
| Monroe | NC | 37,797 | 1494/371/4298 | 2,804 |
| Indian Trail | NC | 42,854 | 1386/286/4097 | 2,711 |
| Wilson | NC | 47,833 | 1289/240/3927 | 2,638 |
| Mooresville | NC | 53,721 | 1187/194/3759 | 2,572 |
| Helena | AL | 22,117 | 1312/417/3801 | 2,489 |
| Huntersville | NC | 64,688 | 1201/187/3667 | 2,466 |
| Clemson | SC | 17,838 | 898/257/3343 | 2,445 |
| Jacksonville | NC | 72,879 | 947/101/3377 | 2,430 |
| Apex | NC | 72,225 | 1507/280/3921 | 2,414 |
| North Myrtle Beach | SC | 20,303 | 1314/455/3628 | 2,314 |
| Greenwood | SC | 22,498 | 1199/373/3473 | 2,274 |
| Daphne | AL | 30,321 | 1322/351/3593 | 2,271 |
| Northport | AL | 31,111 | 1478/441/3732 | 2,254 |

## State composition of each top 500

| State | Baseline | Population-heavy | State-yield-heavy |
|---|---:|---:|---:|
| AL | 0 | 5 | 0 |
| AR | 1 | 5 | 0 |
| AZ | 11 | 21 | 1 |
| CA | 77 | 29 | 142 |
| CO | 1 | 11 | 0 |
| CT | 19 | 14 | 1 |
| FL | 0 | 1 | 0 |
| GA | 23 | 69 | 0 |
| IA | 15 | 12 | 1 |
| IL | 155 | 105 | 188 |
| IN | 54 | 62 | 2 |
| KS | 0 | 8 | 0 |
| KY | 0 | 11 | 0 |
| MA | 3 | 3 | 1 |
| MI | 69 | 47 | 62 |
| MO | 2 | 2 | 0 |
| NC | 0 | 14 | 0 |
| NE | 13 | 12 | 0 |
| NV | 3 | 1 | 1 |
| NY | 0 | 3 | 0 |
| OH | 3 | 3 | 3 |
| OK | 1 | 21 | 0 |
| OR | 25 | 4 | 50 |
| RI | 4 | 5 | 0 |
| SC | 0 | 17 | 0 |
| TN | 0 | 2 | 0 |
| VA | 0 | 4 | 0 |
| WA | 21 | 9 | 48 |

## Interpretation

The baseline retains 67.0% of its top 500 under the population-heavy variant and 70.0% under the state-yield-heavy variant. Population is the largest single baseline component at 30 points, but it is below one-third of the score and cannot by itself determine a tier. State yield and research-design evidence jointly contribute 40 points but are empirically Bayes-smoothed with a 25-municipality national prior, preventing zero- or tiny-sample states from receiving extreme scores.

The baseline is suitable for operational use if top-500 overlap remains substantial in both variants; rank movement should be treated as expected uncertainty near cutoffs rather than factual disagreement. This analysis does not establish that any municipality has a union, safety department, civilian bargaining unit, source portal, or wage gap.
