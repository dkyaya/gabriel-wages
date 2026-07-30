# Dashboard local browser smoke report

Status: **passed**

The production dashboard build was served from `docs/dashboard/dist` at the repository Pages base path and inspected through Playwright MCP after the in-app Browser runtime reported that no browser was available. The page loaded without console errors.

Visible UI checks passed for the 2,795-source span-extraction queue, 2,268 positive sources, 19,118 bounded candidates, 18,612 rating-ready candidates, and the exact next task `BROAD-STATE-4X2500-SPAN-RATING-2026-07-30`. The current-report link targets this wave's span-extraction summary.

The map's primary metric and color scale visibly use scout coverage rate. Its explanatory text defines the rate as scout-covered municipalities divided by the eligible/known municipal universe; the raw 16,887 covered count and 35,589 denominator remain contextual. Candidate, source-family, evidence, mechanism, and readiness controls remain outside the map.

Global analysis readiness remains false. Wage-gap readiness remains blocked pending normalization, and causal readiness remains blocked pending matched structure.
