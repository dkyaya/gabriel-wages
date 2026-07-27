# Live dashboard content audit

## Outcome

The public HTML shell and deployed JavaScript bundle were inspected read-only. Before this fix, the bundle already contained the corrected 2026-07-27 header facts, but it also contained current-facing discovery-era language and an old PI-report link. This explains why the date looked correct while the dashboard still felt stale.

The in-app browser backend did not expose a usable browser, so a rendered accessibility tree and screenshots could not be obtained. The audit instead covered the public HTML, its referenced deployed JavaScript asset, the local React component tree, generated JSON, and the local Vite production bundle.

## Corrected content contract

- Current phase: Tier C source review/download complete; PDF/text-layer readiness ready next.
- Current evidence status: bounded documentary/co-location scaffold only.
- Current counts: 463 retained sources, 556 verified Tier C leads, and memo scope 268/208/90.
- Global analysis readiness: false.
- Wage-gap, regression, treatment-effect, national-prevalence, and final causal results: unavailable.
- Historical coverage, priority, operations, candidate-queue, and state-yield sections remain available but are labeled historical.
- The current report link now opens the bounded internal mechanism-linkage claim memo; the July 22 PI report is historical.

Post-push public-bundle verification is recorded separately in the visibility check and push-status output.
