# Validation report

All 49 required validation claims pass.

- External wage matches, growth pairs/series, vacancy rates, overtime shares, and total-compensation sums remain zero; matching rules were not rerun or loosened.
- Staffing input is 18,358; implementation input is 1,268 sequences with 38 math-ready.
- The 1,876,183 mechanism-linkage rows are never used as prevalence. Defensive summaries use 13,526 unique sources, 1,314 municipalities, 2,616 root events, and 11,692 mechanism-exposure events.
- All rates and proportions store explicit denominators. The 432-record documentary growth module and four named bounded local examples are preserved.
- Regression readiness failed; no regression, causal estimate, national wage gap, prevalence estimate, final claim adjudication, or rendered visual was produced.
- All 12 mathematical QA gates pass. Seventy-two JSON and 125 JSONL files parse cleanly; headline formulas reproduce; all cross-file totals reconcile.
- `python scripts/validate.py` passed; `python ingest/test_pipeline.py` passed 60/60; the dashboard production build passed with only the pre-existing non-blocking bundle-size warning.
- The fixed EPSG:5070 event layer remains based on 2,998 deduplicated implementation events. The primary dashboard map remains `scout_coverage_rate`.
- Free disk remains above the 8 GiB reserve; bulky analytical outputs are ignored and no full analytical corpus is staged.

One bounded analytical-module incident was repaired: lane 003 initially summed unresolved-side rows across mechanism-family fanout. It was rescanned from the same immutable inputs and now reports 1,523,558 unresolved-side observations exactly once each. Unique source, municipality, root-event, mechanism-event, and claim counts were unaffected.
