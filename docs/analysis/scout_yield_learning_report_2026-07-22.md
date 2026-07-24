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
| Parallel Round 2 compact/adaptive (3 serialized lanes) | 446 | 383 | 63 | 4 | 985 | 5615.561 | 288.484 | 631.460 | 2.209 |

## State-yield learning

States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.

| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| OH | 179 | 96.6% | 3.207 | 3.4% | 1.1% | high | strong_yield_consider_next_wave |
| MD | 11 | 100.0% | 2.818 | 0.0% | 0.0% | medium | strong_yield_consider_next_wave |
| MA | 57 | 93.0% | 2.719 | 7.0% | 1.7% | high | strong_yield_consider_next_wave |
| PA | 28 | 85.7% | 2.714 | 14.3% | 0.0% | high | strong_yield_consider_next_wave |
| CT | 21 | 95.2% | 2.667 | 4.8% | 0.0% | medium | strong_yield_consider_next_wave |
| WA | 90 | 97.8% | 2.633 | 2.2% | 2.2% | high | strong_yield_consider_next_wave |
| OR | 69 | 97.1% | 2.609 | 2.9% | 0.0% | high | strong_yield_consider_next_wave |
| CA | 158 | 94.3% | 2.462 | 5.7% | 4.2% | high | strong_yield_consider_next_wave |
| IL | 122 | 86.1% | 2.418 | 13.9% | 2.4% | high | strong_yield_consider_next_wave |
| NM | 12 | 100.0% | 2.417 | 0.0% | 0.0% | medium | strong_yield_consider_next_wave |
| WI | 49 | 98.0% | 2.327 | 2.0% | 0.0% | high | strong_yield_consider_next_wave |
| MI | 70 | 88.6% | 2.300 | 11.4% | 0.0% | high | strong_yield_consider_next_wave |
| NY | 27 | 85.2% | 2.259 | 14.8% | 0.0% | high | strong_yield_consider_next_wave |
| IA | 27 | 77.8% | 2.185 | 22.2% | 3.6% | high | strong_yield_consider_next_wave |
| MN | 25 | 88.0% | 2.000 | 12.0% | 0.0% | high | strong_yield_consider_next_wave |

## Operating recommendation

Across the four reviewed 150-row waves and two audited parallel rounds, mean candidate density was 2.005 rows per parseable municipality. Use the refreshed priority layer as the primary selector, then blend states with medium/high sample confidence and strong observed yield with under-sampled states needed for calibration and geographic coverage.

State sample confidence counts: high=16, medium=12, low=23.

Refresh this learning report after each wave and rebuild the unchanged priority methodology after 300–600 additional successful scouts. Parallel Rounds 1 and 2 add 743 successful scouts since the Tier 1 Wave 2 refresh, so the Round 2 serial merge refreshes the unchanged priority methodology. Do not let sparse-state extremes dominate selection.

No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.
