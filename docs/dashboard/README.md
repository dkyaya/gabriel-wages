# National Municipal Labor Evidence Dashboard

This directory is the first static-data dashboard scaffold. It is designed for GitHub Pages, has no backend, and requires no API key. The current data describe source discovery and queue/coverage accounting only.

## Current status

The repository has Node and npm available, but it did not have an existing Vite project or installed frontend dependencies when this scaffold was created. No packages were installed and no frontend build was run. The files here are a reviewable React/Vite draft that can become runnable in a separately authorized frontend task.

The MVP source includes:

- national source-discovery headline cards;
- a token-free national map shell/state grid pending a provenance-documented state GeoJSON;
- a right-side state detail panel;
- hash-routed printable state briefs;
- a source-discovery funnel;
- a state-level candidate queue explorer;
- a claim/evidence status panel; and
- a deliberately unavailable regression panel.

## Regenerate data

From the repository root:

```bash
python scripts/build_dashboard_data.py
```

The command writes:

- `data/state_summary.json`
- `data/candidate_queue_summary.json`
- `data/coverage_funnel.json`
- `data/analysis_readiness.json`

Run it after a coordinator queue/coverage rebuild, not from an isolated scout worker. The builder does not modify canonical data and does not require a frontend build.

## Run or build later

After frontend dependency installation is separately approved:

```bash
cd docs/dashboard
npm install
npm run dev
```

For a production build:

```bash
npm run build
npm run preview
```

`vite.config.js` uses a relative base so the output can live under a GitHub Pages project path. The hash route `#/state/CA` avoids server rewrite requirements.

## GitHub Pages deployment

A later deployment task can add a GitHub Actions workflow that:

1. checks out a fixed commit;
2. runs the dashboard data builder or verifies committed JSON;
3. installs locked frontend dependencies with `npm ci`;
4. runs `npm run build`; and
5. publishes `docs/dashboard/dist/` to GitHub Pages.

No deployment workflow is included here, and this scaffold has not inspected or changed any git remote.

## Map architecture

The intended map is Leaflet with a committed simplified state GeoJSON and no basemap tiles. That keeps the map printable, token-free, and reproducible. This task did not download a boundary asset. Until a public-domain file is selected and its provenance documented, the app uses an accessible state grid as the national-map shell.

## MVP versus future

MVP:

- aggregate queue/coverage JSON;
- 51 state/DC status objects;
- state detail and print layout;
- discovery funnel and queue composition;
- explicit missing/future analysis stages.

Future:

- reviewed state GeoJSON and Leaflet choropleth;
- municipality-level explorer with county context;
- claim/evidence/reasoning cards backed by a dedicated evidence bridge;
- project-wide verification and ingestion summaries;
- structured wage extracts and matched-set tables;
- versioned regression results; and
- automated accessibility, print, and visual regression checks.

## Interpretation rule

Scout leads are unverified. A candidate-positive municipality, high-priority row, or likely matched set does not establish source validity, a matched bargaining cycle, a wage gap, a mechanism, or claim support. The interface must retain that wording even as more data are added.
