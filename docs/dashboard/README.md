# National Municipal Labor Evidence Dashboard

This directory contains a static, PI-facing dashboard for national municipal-labor source-discovery coverage and evidence readiness. It has no backend, database, secret key, Mapbox token, or runtime connection to a model service. The browser reads only committed dashboard JSON plus the committed local state-boundary GeoJSON.

The MVP is intentionally about the research pipeline. It does **not** report wage gaps, causal estimates, verified-source totals, or regression results because the repository does not yet provide a validated, dashboard-ready wage and verification panel.

## Frozen PI checkpoint — 2026-07-22

The current committed data layer reflects the post–Tier 1 Wave 2 checkpoint:

- 35,589 municipal/township governments in the authoritative universe;
- 794 successfully scout-covered municipalities;
- 612 candidate-positive and 182 parseable-empty municipalities;
- 20 failure-only municipalities retained outside successful coverage;
- 1,602 URL-bearing, unverified candidate queue rows;
- 34,789 future-scout-eligible municipalities, including 1,227 Tier 1 and 3,478 Tier 2;
- latest-wave runtime 5,738.638 seconds and throughput 94.099 attempted rows/hour.

A candidate row is a possible source URL or document lead, not a verified source or ingested contract. The checkpoint is documented in `docs/analysis/pi_progress_report_source_discovery_2026-07-22.md`.

## What the MVP includes

- national headline counts for the municipal universe, scout coverage, candidate rows, and likely matched-set leads;
- a token-free geographic US state choropleth plus a tile-grid alternate, with shared state selection and five safe color metrics;
- a detailed state side panel with coverage, queue, failure, and stage labels;
- a national source-discovery funnel with future stages rendered as unavailable;
- candidate queue priority cards, unit-label composition, and a state workload table;
- an analysis-readiness panel that separates discovery reporting from verification, ingestion, wage extraction, and regression;
- a dedicated printable state report at `#/state/<CODE>/report`;
- a status legend, limitations, source-file metadata, and an accessible state-value table; and
- print-friendly CSS for short state appendices.

## Map status

The dashboard defaults to a true **geographic state choropleth** rendered from a committed local GeoJSON asset. Alaska and Hawaii use labeled insets, and DC has an enlarged selection marker. The prior **tile-grid choropleth** remains available from the map-mode toggle as a compact schematic alternate and accessibility fallback. Both views use the same generated `state_summary.json`, safe metric selector, hash-routed state selection, detail panel, and state-value table.

The geographic view does not use a basemap, mapping SDK, API token, secret, or remote runtime URL. Vite emits the committed GeoJSON as a same-origin static asset during the GitHub Pages build. If that local asset cannot load, the UI reports the problem and directs the reader to the tile grid.

The map can color states by these current, display-safe fields only:

1. scout coverage rate;
2. scout-covered municipality count;
3. candidate row count;
4. high-priority later-verification row count; or
5. operational evidence-readiness score.

The readiness score is workflow triage, not evidence strength. Wage gaps are not an available map metric.

Boundary provenance, checksums, display choices, and the offline update procedure are documented in [map_data_notes.md](map_data_notes.md). The source is the Census Bureau's 2025 1:20,000,000 state cartographic-boundary file, identified by the federal catalog as CC0 1.0. Only the 50 states and District of Columbia are retained.

## Data flow

```text
committed national queue / coverage / universe CSVs
                      |
                      v
       scripts/build_dashboard_data.py
                      |
                      v
          docs/dashboard/data/*.json
                      |
                      v
       static React/Vite browser bundle
```

The builder reads committed coordinator outputs and writes only dashboard JSON. It does not change national queue/coverage inputs, canonical contracts, city coverage, or corpus files. It does not open candidate URLs, verify sources, ingest documents, codify text, or call an API/model.

## Regenerate the JSON

Run from the repository root:

```bash
python -m py_compile scripts/build_dashboard_data.py
python scripts/build_dashboard_data.py
```

The builder regenerates:

- `docs/dashboard/data/state_summary.json`
- `docs/dashboard/data/candidate_queue_summary.json`
- `docs/dashboard/data/coverage_funnel.json`
- `docs/dashboard/data/analysis_readiness.json`
- `docs/dashboard/data/priority_summary.json`
- `docs/dashboard/data/state_priority_summary.json`
- `docs/dashboard/data/top_priority_targets.json`
- `docs/dashboard/data/scout_operations_summary.json`
- `docs/dashboard/data/scout_yield_by_state.json`
- `docs/dashboard/data/scout_runtime_trends.json`

The first four files drive the current core dashboard views. The priority and operations files provide a committed, static data layer for present reporting and later low-risk UI additions; not every field is necessarily rendered by the current frontend.

To refresh state/wave yield inputs before rebuilding the dashboard, run:

```bash
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

Review the printed totals and JSON diffs before committing. In particular, confirm that candidate-positive plus parseable-empty municipalities equals scout-covered municipalities and that connection failures remain outside coverage.

## Update after queue or coverage changes

Dashboard data should be refreshed only after a coordinator has completed and validated an atomic national queue/coverage rebuild. Do not build from one parallel worker's isolated output.

1. Confirm the coordinator's national queue, municipality coverage, and state coverage outputs are complete.
2. Run `python scripts/build_dashboard_data.py` from the repository root.
3. Inspect all four JSON diffs, metadata timestamps, warnings, funnel identities, and state totals.
4. Run the repository validations listed below.
5. If frontend dependencies are already installed, run the production build and review the main dashboard plus at least one `#/state/<CODE>/report` route.
6. Commit the coordinated queue/coverage change and JSON refresh together, or cross-reference the commits clearly.

## Run locally

The dashboard requires Node.js 20.19 or newer. Install or refresh dependencies from the committed package manifest and lockfile:

```bash
cd docs/dashboard
npm install
npm run dev
```

Use `npm ci` instead of `npm install` for a clean lockfile-exact installation, including CI. The default Vite base is `/gabriel-wages/`, so Vite normally serves the local dashboard at `http://localhost:5173/gabriel-wages/`. To use the root path locally, run `npm run dev -- --base /`.

State selection uses hash routes, so direct state views work without server-side rewrites:

- `#/state/CA` selects California in the dashboard;
- `#/state/CA/report` opens California's printable report.

The dependency surface is minimal: React, React DOM, Vite, and the Vite React plugin. No map library is installed; the geographic component renders the local GeoJSON directly as accessible SVG paths. `node_modules/` and `dist/` are local/generated and ignored by Git; `package-lock.json` is committed for reproducible installs.

## Build for GitHub Pages

The dashboard is configured for the future `dkyaya/gabriel-wages` project site:

```text
https://dkyaya.github.io/gabriel-wages/
```

The default production base is `/gabriel-wages/`. After dependencies have been installed:

```bash
cd docs/dashboard
npm run build
npm run preview
```

The production output is `docs/dashboard/dist/`. Hash routes avoid server-side rewrite requirements. `npm run build:relative` remains available when a portable `./` asset base is preferable for local static previews.

The committed `.github/workflows/deploy-dashboard.yml` workflow regenerates dashboard JSON, installs locked frontend dependencies, builds under `/gabriel-wages/`, uploads the static artifact, and deploys through GitHub's official Pages actions. It runs on relevant pushes to `main` and by manual dispatch. No user-defined secret is required.

See [DEPLOYMENT.md](DEPLOYMENT.md) for Pages enablement, exact triggers, base-path overrides, public/private Actions cost caveats, and publication safety rules. Creating the workflow does not publish the site until the future repository enables Pages with GitHub Actions and receives the commit.

## Repository checks

From the repository root:

```bash
python -m py_compile scripts/build_dashboard_data.py
python scripts/build_dashboard_data.py
python scripts/validate.py
python ingest/test_pipeline.py
python ingest/audit_coverage.py
```

Also run the locked frontend build:

```bash
cd docs/dashboard
npm ci
npm run build
```

## Component layout

```text
src/
  App.jsx
  main.jsx
  styles.css
  components/
    AnalysisReadinessPanel.jsx
    CandidateQueueCards.jsx
    CoverageFunnel.jsx
    DataLimitations.jsx
    NationalMap.jsx
    PrintableStateReport.jsx
    StateTileGrid.jsx
    StateDetailPanel.jsx
    USChoroplethMap.jsx
    mapMetrics.js
    ui.jsx
  assets/
    us-states-2025-20m.geojson
```

All components consume the four generated JSON imports in `App.jsx`. No component fetches remote data.

## MVP versus future

Current MVP:

- aggregate static queue/coverage/readiness data;
- 50 states plus DC;
- safe metric selection shared by a geographic state map and schematic tile-grid alternate;
- state detail and print views;
- explicit scout, calibration, verification, ingestion, and unavailable-stage language; and
- accessible text/table alternatives and responsive/print CSS.

Future work, gated by dedicated inputs or provenance review:

- optional automated geographic-asset schema/geometry regression tests;
- automated JSON-contract, accessibility, browser, and print-render tests;
- municipality-level exploration with county context;
- a claim/evidence bridge that keeps scout leads under source needs;
- project-wide verification and ingestion ledgers;
- structured matched-cycle wage extracts; and
- versioned regression results with frozen inputs and specification metadata.

## Interpretation rules

- A scout lead is not a verified source.
- A high-priority row is a scheduling choice, not a source-quality judgment.
- A likely matched-set group is based on unit labels and still needs employer, document, and cycle checks.
- A parseable empty result is a completed scout outcome, not proof that no source exists.
- `null` means the dashboard lacks a validated input; it must never be displayed as zero.
- Candidate volume must not be used as evidence of a wage gap, bargaining strength, mechanism, or substantive claim.
