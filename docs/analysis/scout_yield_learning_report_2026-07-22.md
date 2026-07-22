# Scout Yield Learning Report — 2026-07-22

This deterministic offline report compares discovery-stage operational yield. Candidate rows remain unverified and are not evidence of source validity or wage effects.

## Wave comparison

| Wave | Parseable | Positive | Empty | Failures | Candidates | Runtime s | Rows/hour | Candidates/hour | Candidates/parseable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Coordinator Wave 1 CA/NJ/TX | 149 | 112 | 37 | 1 | 246 | 6937.000 | 77.843 | 127.663 | 1.651 |
| Coordinator Wave 2 CA/TX/IL | 148 | 98 | 50 | 2 | 223 | 6149.884 | 87.807 | 130.539 | 1.507 |
| Tier 1 Wave 1 cross-state | 142 | 99 | 43 | 8 | 268 | 6723.519 | 80.315 | 143.496 | 1.887 |

## State-yield learning

States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.

| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| PA | 25 | 92.0% | 3.000 | 8.0% | 0.0% | high | strong_yield_consider_next_wave |
| FL | 14 | 100.0% | 2.714 | 0.0% | 6.7% | medium | strong_yield_consider_next_wave |
| MA | 17 | 94.1% | 2.706 | 5.9% | 0.0% | medium | strong_yield_consider_next_wave |
| CA | 144 | 93.8% | 2.438 | 6.2% | 4.0% | high | strong_yield_consider_next_wave |
| IL | 122 | 86.1% | 2.418 | 13.9% | 2.4% | high | strong_yield_consider_next_wave |
| NY | 25 | 84.0% | 2.280 | 16.0% | 0.0% | high | strong_yield_consider_next_wave |
| NJ | 77 | 59.7% | 1.221 | 40.3% | 1.3% | high | moderate_yield_use_priority_targets |
| AZ | 10 | 50.0% | 1.200 | 50.0% | 9.1% | medium | moderate_yield_use_priority_targets |
| TX | 103 | 51.5% | 1.097 | 48.5% | 0.0% | high | moderate_yield_use_priority_targets |

## Operating recommendation

Across the three reviewed 150-row waves, mean candidate density was 1.682 rows per parseable municipality. Use Tier 1 rank as the primary selector, then blend states with medium/high sample confidence and strong observed yield with under-sampled states needed for calibration and geographic coverage.

State sample confidence counts: high=6, medium=3, low=42.

Refresh this learning report after each wave and rebuild the unchanged priority methodology after 300–600 additional successful scouts (current checkpoint: 646 covered; next refresh window: 804–1,104 covered). Do not let sparse-state extremes dominate selection.

No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.
