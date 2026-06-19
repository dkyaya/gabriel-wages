# Research Hypotheses

Running log of testable claims for the safety-vs-non-safety wage project.
Append new entries at the bottom in sequence (H2, H3, ...). Update **Status**
and **Evidence so far** in place as evidence accumulates — do not create a new
entry to record a status change, just edit the existing one and note the date.

Status vocabulary: `untested` | `supported` | `contradicted` | `inconclusive`

---

## H1 — Comparability channel

**Date added:** 2026-06-18
**Status:** untested (preliminary signal, not yet isolate
**Hypothesis:** Safety units' wage decisions (CBAs/awards) invoke peer-city/peer-unit
wage comparisons more frequently and more centrally than non-safety units' decisions.
This comparability emphasis functions as a ratcheting mechanism — each city's raise
becomes the new benchmark for peer cities — driving safety wages up faster than
non-safety wages, which are set with less reference to external comparators.

**What would support it:** Safety units score higher than matched non-safety units on
`comparability_emphasis` *within the same document type* (award-vs-award, CBA-vs-CBA)
— not confounded by safety units simply having more arbitration awards in the sample.
Additionally, higher `comparability_emphasis` scores should correlate with larger
subsequent wage increases at the city-cycle level.

**What would contradict it:** No score gap between safety and non-safety once document
type is controlled for, OR `comparability_emphasis` shows no correlation with actual
wage growth (meaning the language is rhetorical but not causal).

**Measurement boundary (added 2026-06-19):** Cost-of-living index adjustments (CPI,
BACPI, or similar) are **not** comparability language under this attribute — they
reference a price index, not other workers' wages. Only explicit comparisons to wages
or compensation of other employees, bargaining units, or jurisdictions score above 0.
This boundary was clarified after GABRIEL v4 revealed that Arlington DPW 2015/2018
cited BACPI as their sole external benchmark; the model correctly scored them low
(5/12) even before the clarification was explicit in the prompt.

**Evidence so far:** GABRIEL pilot v3 (PROGRESS.md, 2026-06-18 session 5;
`analysis/gabriel_pilot/report_v3.md`) found safety mean=28.8 vs. non-safety mean=3.3
on `comparability_emphasis`, but this is **confounded** — the only two arbitration
awards in the n=12 sample are both safety units (Somerville police). The true driver
may be document type (award vs. CBA), not occupation. Document-type-controlled test
still needed: requires non-safety arbitration awards in the corpus.

---
