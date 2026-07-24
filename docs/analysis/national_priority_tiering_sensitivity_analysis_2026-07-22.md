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
| Baseline vs population_heavier | 341 | 68.2% |
| Baseline vs state_yield_heavier | 257 | 51.4% |

## Largest rank changes within the union of variant top-500 pools

Ranks are baseline / population-heavier / state-yield-heavier.

| Municipality | State | Population | Ranks | Largest absolute change |
|---|---|---:|---:|---:|
| North Augusta | SC | 25,891 | 937/320/3631 | 2,694 |
| Easley | SC | 26,386 | 923/305/3588 | 2,665 |
| Peachtree Corners | GA | 42,136 | 1507/483/4165 | 2,658 |
| Newnan | GA | 44,940 | 1430/432/4075 | 2,645 |
| Coal Grove | OH | 1,827 | 2040/4671/495 | 2,631 |
| Gainesville | GA | 47,265 | 1378/394/3992 | 2,614 |
| Manchester | OH | 1,842 | 1891/4496/475 | 2,605 |
| Plymouth | OH | 1,692 | 1524/4129/443 | 2,605 |
| Elida | OH | 1,900 | 2039/4630/490 | 2,591 |
| St. Paris | OH | 1,885 | 1970/4543/479 | 2,573 |
| Edgerton | OH | 1,866 | 1862/4434/465 | 2,572 |
| Caldwell | OH | 1,869 | 1856/4428/462 | 2,572 |
| Valdosta | GA | 55,025 | 1212/294/3779 | 2,567 |
| South Zanesville | OH | 1,902 | 1874/4430/458 | 2,556 |
| Dunwoody | GA | 51,713 | 1445/409/3998 | 2,553 |
| Dalton | OH | 1,924 | 1922/4472/468 | 2,550 |
| Woodville | OH | 1,985 | 1894/4410/450 | 2,516 |
| Roseville | OH | 1,740 | 1335/3846/403 | 2,511 |
| Jamestown | OH | 2,073 | 2132/4641/476 | 2,509 |
| Elmwood Place | OH | 2,055 | 2110/4615/474 | 2,505 |

## State composition of each top 500

| State | Baseline | Population-heavy | State-yield-heavy |
|---|---:|---:|---:|
| AK | 6 | 2 | 0 |
| AL | 4 | 13 | 0 |
| AR | 1 | 14 | 0 |
| AZ | 1 | 11 | 1 |
| CA | 90 | 66 | 189 |
| CO | 0 | 8 | 0 |
| DE | 4 | 4 | 0 |
| GA | 0 | 13 | 0 |
| IA | 2 | 4 | 1 |
| ID | 3 | 5 | 0 |
| IL | 3 | 3 | 3 |
| IN | 2 | 5 | 2 |
| KS | 7 | 16 | 0 |
| LA | 8 | 13 | 0 |
| MA | 3 | 2 | 4 |
| MD | 16 | 13 | 9 |
| ME | 13 | 10 | 5 |
| MN | 27 | 37 | 0 |
| MO | 19 | 35 | 1 |
| MS | 21 | 21 | 0 |
| MT | 10 | 5 | 4 |
| ND | 3 | 3 | 0 |
| NE | 2 | 2 | 0 |
| NH | 8 | 8 | 5 |
| NM | 12 | 7 | 2 |
| NV | 5 | 4 | 2 |
| NY | 20 | 26 | 0 |
| OH | 103 | 11 | 245 |
| PA | 15 | 14 | 0 |
| RI | 2 | 2 | 2 |
| SC | 0 | 12 | 0 |
| SD | 14 | 11 | 7 |
| TN | 7 | 17 | 0 |
| UT | 11 | 32 | 0 |
| VA | 8 | 17 | 0 |
| VT | 3 | 3 | 0 |
| WA | 1 | 1 | 2 |
| WI | 30 | 15 | 15 |
| WV | 8 | 9 | 0 |
| WY | 8 | 6 | 1 |

## Interpretation

The baseline retains 68.2% of its top 500 under the population-heavy variant and 51.4% under the state-yield-heavy variant. Population is the largest single baseline component at 30 points, but it is below one-third of the score and cannot by itself determine a tier. State yield and research-design evidence jointly contribute 40 points but are empirically Bayes-smoothed with a 25-municipality national prior, preventing zero- or tiny-sample states from receiving extreme scores.

The baseline is suitable for operational use if top-500 overlap remains substantial in both variants; rank movement should be treated as expected uncertainty near cutoffs rather than factual disagreement. This analysis does not establish that any municipality has a union, safety department, civilian bargaining unit, source portal, or wage gap.
