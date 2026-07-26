# Limited qualitative usage-layer QA stress test

The QA system registers 40 adversarial failure modes covering authorization, immutable hashes, schema and identity drift, exact-span evidence, provenance, historical/current QA, restrictions, contamination, lane separation, conflict preservation, readiness, prompts, relays, checkpoints, reruns, and output boundaries.

The new suite passed 65/65 tests. Six predecessor suites passed 295/295, yielding 360/360 focused passes. The first reporting pass found one orchestration defect: the generated future prompt grouped extraction and selection restrictions while the validator required the standalone phrases `Do not run extraction` and `Do not select new documents`. The generator and tests now assert both exact restrictions. No guardrail was weakened, and the incomplete attempt could not pass completion validation.
