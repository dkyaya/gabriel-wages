# Scout Yield Learning Report — 2026-07-22

This deterministic offline report compares discovery-stage operational yield. Candidate rows remain unverified and are not evidence of source validity or wage effects.

## Wave comparison

| Wave | Parseable | Positive | Empty | Failures | Candidates | Runtime s | Rows/hour | Candidates/hour | Candidates/parseable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Coordinator Wave 1 CA/NJ/TX | 149 | 112 | 37 | 1 | 246 | 6937.000 | 77.843 | 127.663 | 1.651 |
| Coordinator Wave 2 CA/TX/IL | 148 | 98 | 50 | 2 | 223 | 6149.884 | 87.807 | 130.539 | 1.507 |
| Tier 1 Wave 1 cross-state | 142 | 99 | 43 | 8 | 268 | 6723.519 | 80.315 | 143.496 | 1.887 |
| Tier 1 Wave 2 compact/adaptive cross-state | 148 | 122 | 26 | 2 | 327 | 5738.638 | 94.099 | 205.136 | 2.209 |
| Parallel Round 1 compact/adaptive (2 serialized lanes) | 297 | 272 | 25 | 3 | 763 | 6530.000 | 165.391 | 420.643 | 2.569 |

## State-yield learning

States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.

| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| OH | 91 | 97.8% | 3.220 | 2.2% | 1.1% | high | strong_yield_consider_next_wave |
| IA | 11 | 90.9% | 2.909 | 9.1% | 8.3% | medium | strong_yield_consider_next_wave |
| WA | 50 | 98.0% | 2.860 | 2.0% | 2.0% | high | strong_yield_consider_next_wave |
| WI | 16 | 100.0% | 2.750 | 0.0% | 0.0% | medium | strong_yield_consider_next_wave |
| CT | 19 | 94.7% | 2.737 | 5.3% | 0.0% | medium | strong_yield_consider_next_wave |
| PA | 28 | 85.7% | 2.714 | 14.3% | 0.0% | high | strong_yield_consider_next_wave |
| OR | 40 | 95.0% | 2.700 | 5.0% | 0.0% | high | strong_yield_consider_next_wave |
| MA | 45 | 93.3% | 2.689 | 6.7% | 2.2% | high | strong_yield_consider_next_wave |
| NM | 10 | 100.0% | 2.500 | 0.0% | 0.0% | medium | strong_yield_consider_next_wave |
| CA | 144 | 93.8% | 2.438 | 6.2% | 4.0% | high | strong_yield_consider_next_wave |
| IL | 122 | 86.1% | 2.418 | 13.9% | 2.4% | high | strong_yield_consider_next_wave |
| MI | 36 | 91.7% | 2.417 | 8.3% | 0.0% | high | strong_yield_consider_next_wave |
| NY | 25 | 84.0% | 2.280 | 16.0% | 0.0% | high | strong_yield_consider_next_wave |
| FL | 86 | 77.9% | 1.942 | 22.1% | 2.3% | high | strong_yield_consider_next_wave |
| UT | 12 | 66.7% | 1.500 | 33.3% | 0.0% | medium | moderate_yield_use_priority_targets |

## Operating recommendation

Across the four reviewed 150-row waves and the first 300-row two-lane parallel round, mean candidate density was 1.965 rows per parseable municipality. Use Tier 1 rank as the primary selector, then blend states with medium/high sample confidence and strong observed yield with under-sampled states needed for calibration and geographic coverage.

State sample confidence counts: high=12, medium=11, low=28.

Refresh this learning report after each wave and rebuild the unchanged priority methodology after 300–600 additional successful scouts. Parallel Round 1 adds 297 successful scouts since the Tier 1 Wave 2 refresh, just below the 300-success lower trigger, so priority refresh remains deferred in this merge. Do not let sparse-state extremes dominate selection.

No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.
