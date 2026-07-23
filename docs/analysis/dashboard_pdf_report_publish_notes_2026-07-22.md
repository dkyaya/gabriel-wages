# Dashboard PDF report publication notes — 2026-07-22

## Publication artifact

The dashboard-source copy of the PI report is:

`docs/dashboard/reports/pi_progress_report_source_discovery_2026-07-22.pdf`

The configured dashboard URL is:

`https://dkyaya.github.io/gabriel-wages/`

The committed PDF is imported by Vite from `docs/dashboard/src/App.jsx`. The production build emits it as a managed static asset under the configured `/gabriel-wages/` Pages base, avoiding a runtime fetch from an external domain.

## Frontend change

The dashboard frontend received one small, low-risk resource addition:

- the main dashboard footer now contains a link labeled **PI Source-Discovery Progress Report PDF**;
- the link opens the generated PDF in a new browser tab;
- two focused CSS rules reuse the dashboard's existing evergreen palette and do not affect the map, panels, state routing, or printable state reports.

The dashboard README also links directly to `reports/pi_progress_report_source_discovery_2026-07-22.pdf` within the source tree.

## Build and interpretation boundary

The PDF summarizes current source-discovery operations. It does not report verified source totals, ingested scout contracts, matched wage observations, wage gaps, mechanism estimates, or causal results. Candidate rows remain unverified leads.

Dashboard/yield JSON is regenerated only from existing committed national accounting. No scout, live/API/model/hosted-search call, candidate URL opening or verification, source ingestion, GABRIEL codification, candidate promotion, or queue/coverage change from new evidence occurs in publication.

After a successful push to the existing Pages source branch, the dashboard workflow may require a minute or two to rebuild and deploy the new asset and link.
