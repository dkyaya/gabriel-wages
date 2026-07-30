# Dashboard browser smoke report

Status: **local browser visible/current passed**.

The production dashboard build loaded through a local Vite preview with zero console errors. The rendered main view retained four evidence cards, kept technical details collapsed, and visibly showed:

- current stage: normalization and matched structure complete;
- next task: `BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30`;
- scout coverage rate: 47.45% (16,887 / 35,589 as context);
- 11,548 normalized quantitative records;
- 65 matched safety/non-safety municipality-cycle candidates;
- 48 source-grounded repaired examples and 12 downgraded examples; and
- blocked final wage-gap, causal, and prevalence claims.

The in-app Browser runtime was checked first and exposed no browser instance. The user-authorized Playwright controller was therefore used for the visible local smoke. A lightweight full-page screenshot is stored as `dashboard_local_smoke.png`.
