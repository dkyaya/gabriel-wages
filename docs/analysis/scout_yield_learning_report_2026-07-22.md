# Scout Yield Learning Report — 2026-07-22

This deterministic offline report compares discovery-stage operational yield. Candidate rows remain unverified and are not evidence of source validity or wage effects.

## Wave comparison

| Wave | Parseable | Positive | Empty | Failures | Candidates | Runtime s | Rows/hour | Candidates/hour | Candidates/parseable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Coordinator Wave 1 CA/NJ/TX | 149 | 112 | 37 | 1 | 246 | 6937.000 | 77.843 | 127.663 | 1.651 |
| Coordinator Wave 2 CA/TX/IL | 148 | 98 | 50 | 2 | 223 | 6149.884 | 87.807 | 130.539 | 1.507 |
| Tier 1 Wave 1 cross-state | 142 | 99 | 43 | 8 | 268 | 6723.519 | 80.315 | 143.496 | 1.887 |
| Tier 1 Wave 2 compact/adaptive cross-state | 148 | 122 | 26 | 2 | 327 | 5738.638 | 94.099 | 205.136 | 2.209 |

## State-yield learning

States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.

| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| WA | 15 | 93.3% | 3.133 | 6.7% | 6.2% | medium | strong_yield_consider_next_wave |
| MA | 25 | 92.0% | 2.720 | 8.0% | 3.8% | high | strong_yield_consider_next_wave |
| PA | 28 | 85.7% | 2.714 | 14.3% | 0.0% | high | strong_yield_consider_next_wave |
| FL | 30 | 93.3% | 2.567 | 6.7% | 3.2% | high | strong_yield_consider_next_wave |
| MI | 11 | 90.9% | 2.455 | 9.1% | 0.0% | medium | strong_yield_consider_next_wave |
| CA | 144 | 93.8% | 2.438 | 6.2% | 4.0% | high | strong_yield_consider_next_wave |
| IL | 122 | 86.1% | 2.418 | 13.9% | 2.4% | high | strong_yield_consider_next_wave |
| NY | 25 | 84.0% | 2.280 | 16.0% | 0.0% | high | strong_yield_consider_next_wave |
| UT | 12 | 66.7% | 1.500 | 33.3% | 0.0% | medium | moderate_yield_use_priority_targets |
| AZ | 15 | 66.7% | 1.400 | 33.3% | 6.2% | medium | moderate_yield_use_priority_targets |
| CO | 15 | 66.7% | 1.400 | 33.3% | 0.0% | medium | moderate_yield_use_priority_targets |
| TN | 11 | 63.6% | 1.364 | 36.4% | 0.0% | medium | moderate_yield_use_priority_targets |
| VA | 10 | 60.0% | 1.300 | 40.0% | 0.0% | medium | moderate_yield_use_priority_targets |
| NJ | 77 | 59.7% | 1.221 | 40.3% | 1.3% | high | moderate_yield_use_priority_targets |
| TX | 103 | 51.5% | 1.097 | 48.5% | 0.0% | high | moderate_yield_use_priority_targets |

## Operating recommendation

Across the four reviewed 150-row waves, mean candidate density was 1.813 rows per parseable municipality. Use Tier 1 rank as the primary selector, then blend states with medium/high sample confidence and strong observed yield with under-sampled states needed for calibration and geographic coverage.

State sample confidence counts: high=8, medium=9, low=34.

Refresh this learning report after each wave and rebuild the unchanged priority methodology after 300–600 additional successful scouts. Tier 1 Wave 2 reached the task's 135-parseable refresh gate, so the current priority layer is rebuilt after this accounting update. Do not let sparse-state extremes dominate selection.

No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.
