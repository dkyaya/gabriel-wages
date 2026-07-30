# Gabriel Wages dashboard

Public dashboard: <https://dkyaya.github.io/gabriel-wages/>

This directory contains a static, PI-facing view of the project’s current documentary evidence state. It has no backend, database, API key, mapping token, or runtime model connection. Low-level pipeline reconciliation belongs in linked reports, not on the main page.

## Current dashboard contract — 2026-07-30

The main page answers six questions:

1. What is the current project stage?
2. How much geographic scout coverage exists, measured as a rate?
3. How much valid rated evidence is available, and how much is quarantined?
4. Which documentary wage-growth mechanisms are most prominent after rating?
5. What descriptive claims are allowed, and what analyses remain blocked?
6. What is the one next task?

The current stage is broad-state exact-span rating. The next task is `BROAD-STATE-4X2500-RATING-INGEST-CODIFY-2026-07-30`. Rated spans remain documentary measurements until downstream ingestion/codification. Wage-gap estimates remain blocked pending normalization; causal analysis remains blocked pending matched city-cycle structure; corpus frequencies are not national prevalence.

The main information architecture is deliberately narrow:

- one status strip;
- one scout-coverage-rate map;
- four current rating-state figures;
- one compact mechanism preview;
- one claim-boundary panel; and
- one collapsed technical-audit disclosure.

Historical discovery, source-review, readiness, extraction, lane, validation, and file counters remain available in linked reports and the collapsed audit. They do not receive equal visual weight on the main page.

## Map contract

The map has one metric:

```text
scout coverage rate = scout-covered municipalities / eligible or known municipality universe
```

The denominator comes from `docs/analysis/national_municipality_universe.csv`. Raw covered and denominator counts appear only as context in headings, tooltips, selected-state context, and the accessible table. If a denominator is missing, the geography is marked `coverage_rate_unavailable`; no denominator is fabricated.

Candidate, source-family, evidence, mechanism, readiness, extraction, and rating dimensions are not map filters. They may appear only in non-map summaries or reports. The geographic map and tile grid are presentation alternatives for the same coverage-rate metric.

## Claim boundaries

- Allowed: bounded descriptive summaries of documentary mechanisms such as raises, COLA/CPI clauses, bargaining, comparability, timing, and non-base compensation.
- Not yet allowed: normalized wage comparisons or wage-gap estimates.
- Not yet allowed: regressions, treatment effects, national prevalence, or final causal claims.
- COLA/CPI may be discussed as a contract mechanism. Analyst-side cost-of-living normalization has not been performed.

## Routes

- `/` shows the PI-facing national view.
- `#/state/CA` selects California on the coverage-rate map.
- `#/state/CA/report` opens the historical printable state detail.

## Data and build flow

```text
committed project artifacts
          |
          v
scripts/build_dashboard_data.py
          |
          v
docs/dashboard/data/*.json
          |
          v
React/Vite static dashboard
          |
          v
GitHub Actions Pages artifact
```

From the repository root:

```bash
python scripts/test_dashboard_github_pages_deployment_repair.py
python scripts/build_dashboard_data.py
cd docs/dashboard
npm ci
npm run build
npm run preview -- --host 127.0.0.1
```

The GitHub Pages workflow is `.github/workflows/deploy-dashboard.yml`. It regenerates committed dashboard JSON, builds `docs/dashboard/dist`, uploads the build as a Pages artifact, and deploys it. `dist` is not committed.

## Source files

- App layout: `src/App.jsx`
- Map contract: `src/components/NationalMap.jsx` and `src/components/mapMetrics.js`
- Styles: `src/styles.css`
- Generated dashboard data: `data/*.json`
- Data builder: `../../scripts/build_dashboard_data.py`

The builder does not open source locators, download documents, extract text, OCR, rate spans, ingest/codify evidence, normalize wages, or run analysis. Those are separate authorized stages with their own durable artifacts and gates.
