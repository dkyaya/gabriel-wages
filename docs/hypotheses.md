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

**Measurement boundaries (updated 2026-06-19):**

*CPI/BACPI (added after v4):* Cost-of-living index adjustments (CPI, BACPI, or similar)
are **not** comparability language — they reference a price index, not other workers'
wages. Only explicit comparisons to wages or compensation of other employees, bargaining
units, or jurisdictions score above 0. Arlington DPW 2015/2018 cited BACPI as their
sole external benchmark and correctly score near-zero.

*Verbatim ≠ Relevant (added after v6):* Verbatim verification confirms that a quote is
**real** (the words appear in the document), but NOT that it is **relevant** (that it
constitutes genuine wage comparability evidence). Two failure modes were found in v6:
(1) "Market adjustment" language — e.g. "market adjustment of $0.35 to the top step of
AFSCME: MC" — passes verbatim check but describes an internal salary table correction,
not a comparison to peer employers' wages; (2) Award-outcome sentences — e.g. "The
Panel awards FY2013 – 2.5%, FY2014 – 2%" — and ruling conclusions — e.g. "there is
insufficient justification to change the current longevity payments" — pass verbatim
check but state results rather than comparability reasoning. Relevance must be checked
separately from verbatim-ness. Starting in v7, verified excerpts are additionally
screened for relevance; those that pass verbatim but fail relevance are flagged
`verbatim_but_irrelevant` in the output rather than silently discarded.

*Wage-specific quote boundary (added after v8, 2026-06-23):* Supporting excerpts for
`comparability_emphasis` must be both verbatim and relevant to wage/compensation
comparability. Peer wage, salary, pay, total compensation, benefits, and longevity-pay
comparisons across other communities can count when the passage actually discusses
compensation levels or economic packages. Generic charts/tables comparing non-wage
contract provisions across communities, or charts that merely show cross-community
variation without wage reasoning, are audit evidence only and are excluded from
`supporting_quotes` and verified-support counts.

*Cycle matching tiers (added 2026-06-24):* Exact-cycle matches remain the best design
for wage-outcome comparisons because the bargaining periods are identical. Overlapping
cycle matches are still valid for H1 text/mechanism comparison because city and period
are approximately fixed even when contract windows differ. Adjacent-cycle matches
within roughly one to two years are exploratory only and should be labeled as such.
Low comparability language in CBAs/MOAs should not be interpreted as proof that
comparability did not influence bargaining; these documents may record outcomes rather
than the reasoning behind them. Arbitration awards and factfinding reports are better
reasoning documents, while meeting packets and bargaining exhibits may provide proxy
reasoning evidence when final reports are unavailable.

**Evidence so far:** GABRIEL pilot v3 (PROGRESS.md, 2026-06-18 session 5;
`analysis/gabriel_pilot/report_v3.md`) found safety mean=28.8 vs. non-safety mean=3.3
on `comparability_emphasis`, but this is **confounded** — the only two arbitration
awards in the n=12 sample are both safety units (Somerville police). The true driver
may be document type (award vs. CBA), not occupation. Document-type-controlled test
still needed: requires non-safety arbitration awards in the corpus.

---
