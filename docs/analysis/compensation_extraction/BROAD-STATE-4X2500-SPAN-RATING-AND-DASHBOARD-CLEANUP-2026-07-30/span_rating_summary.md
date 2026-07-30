# Broad-state 4×2500 span rating and dashboard cleanup

Decision: `broad_state_4x2500_span_rating_dashboard_cleanup_completed_ingestion_ready`.

All 18,612 locked spans received one terminal rating outcome: **18,554 valid** and **58 quarantined**. The four locked lanes each contained 4,653 spans.

## Report usability

| Bucket | Valid ratings |
|---|---:|
| downstream normalization needed | 5,533 |
| exclude from report | 5,161 |
| pi report context only | 6,860 |
| pi report core finding ready | 472 |
| pi report supporting example | 528 |

## Claim relevance

| Bucket | Valid ratings |
|---|---:|
| direct quantitative claim support | 6,454 |
| directional hint only | 430 |
| mechanism summary support | 6,509 |
| weak or not supported | 5,161 |

## Directionality

| Direction | Valid ratings |
|---|---:|
| gap narrowing | 45 |
| neutral or general | 6,830 |
| non safety advantage | 637 |
| not applicable | 10,964 |
| safety advantage | 78 |

## Highest-volume mechanism attributes

| Mechanism | Positive rated spans |
|---|---:|
| non base compensation signal | 3,718 |
| base wage direct value | 2,687 |
| implementation or retroactivity advantage | 2,230 |
| weak or no claim support | 1,479 |
| automatic raise mechanism | 1,431 |
| bargaining power signal | 1,135 |
| rank or specialization premium | 763 |
| strike or no strike constraint | 587 |
| market or comparability pressure | 398 |
| safety advantage signal | 192 |

## Boundary

Valid ratings are bounded documentary measurements, not ingested/codified evidence, normalized wage comparisons, population prevalence, treatment effects, or final causal findings. Full distributions, mechanism-specific summaries, PI-report candidates, quarantine reasons, and validation outputs are separate reconstructible artifacts in this directory.
