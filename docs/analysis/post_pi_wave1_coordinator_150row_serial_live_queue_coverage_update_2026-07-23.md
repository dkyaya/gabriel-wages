# Post-PI Wave 1 Queue and Coverage Update

Date: 2026-07-23

Disposition: **WITHHELD — the stopped live run is not merge-eligible.**

The national candidate-queue and coverage builders were not run. The sole live process returned no completed or parseable municipality outcome, so incorporating it would violate the merge gate and the diagnostic-quarantine boundary.

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| URL-bearing candidate queue rows | 1,602 | 1,602 | 0 |
| Scout-covered municipalities | 794 | 794 | 0 |
| Candidate-positive municipalities | 612 | 612 | 0 |
| Parseable-empty municipalities | 182 | 182 | 0 |
| Failure-only municipalities | 20 | 20 | 0 |
| Remaining to 2,000 checkpoint | 1,206 | 1,206 | 0 |

- New URL-bearing candidate rows added: 0.
- Rows newly queued for later verification: 0.
- Rows newly held/rejected/context-only: 0.
- State coverage deltas: CT 0, FL 0, IA 0, MA 0, MI 0, NV 0, OH 0, OR 0, WA 0, WI 0.
- The parseable one-row preflight probe and its leads remain quarantined under its diagnostic output directory and were not supplied to any national builder.

No source verification, extraction, ingestion, rating, `gabriel.codify`, canonical promotion, wage-gap calculation, causal claim, or regression occurred.
