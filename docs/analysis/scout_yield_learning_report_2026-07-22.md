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
| Aggressive 3x300 Attempt 3 compact/adaptive (3 serialized lanes) | 899 | 591 | 308 | 1 | 1389 | 9422.628 | 343.853 | 530.680 | 1.545 |

## State-yield learning

States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.

| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| NV | 11 | 100.0% | 3.091 | 0.0% | 8.3% | medium | strong_yield_consider_next_wave |
| NH | 13 | 84.6% | 2.846 | 15.4% | 0.0% | medium | strong_yield_consider_next_wave |
| MA | 60 | 91.7% | 2.683 | 8.3% | 1.6% | high | strong_yield_consider_next_wave |
| WA | 90 | 97.8% | 2.633 | 2.2% | 2.2% | high | strong_yield_consider_next_wave |
| OR | 69 | 97.1% | 2.609 | 2.9% | 0.0% | high | strong_yield_consider_next_wave |
| CT | 24 | 91.7% | 2.583 | 8.3% | 0.0% | medium | strong_yield_consider_next_wave |
| CA | 304 | 95.4% | 2.546 | 4.6% | 2.3% | high | strong_yield_consider_next_wave |
| MT | 21 | 85.7% | 2.524 | 14.3% | 0.0% | medium | strong_yield_consider_next_wave |
| OH | 328 | 82.0% | 2.494 | 18.0% | 0.9% | high | strong_yield_consider_next_wave |
| IL | 123 | 86.2% | 2.423 | 13.8% | 2.4% | high | strong_yield_consider_next_wave |
| ME | 20 | 85.0% | 2.300 | 15.0% | 0.0% | medium | strong_yield_consider_next_wave |
| MI | 73 | 87.7% | 2.274 | 12.3% | 0.0% | high | strong_yield_consider_next_wave |
| AK | 13 | 92.3% | 2.231 | 7.7% | 0.0% | medium | strong_yield_consider_next_wave |
| IA | 36 | 75.0% | 2.083 | 25.0% | 2.7% | high | strong_yield_consider_next_wave |
| NE | 15 | 93.3% | 2.067 | 6.7% | 0.0% | medium | strong_yield_consider_next_wave |

## Operating recommendation

Across the four reviewed 150-row waves and three audited parallel rounds, mean candidate density was 1.940 rows per parseable municipality. The project has crossed the approximately 2,000-covered checkpoint, so pause broad scouting and use state-yield patterns to select the first bounded verification batch rather than another ordinary discovery wave.

State sample confidence counts: high=22, medium=22, low=7.

The unchanged priority methodology is refreshed after Aggressive Attempt 3 because 899 successful scouts materially changed coverage and crossed the workflow checkpoint. Priority remains an operational layer; do not use it to authorize another discovery wave while broad scouting is paused.

No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.
