# Gabriel Wages Project Hub

The public project hub is published at:

<https://dkyaya.github.io/gabriel-wages/>

This directory contains a static, PI-facing research-status dashboard. It summarizes committed source-discovery, operational, prioritization, and planning artifacts. It has no backend, database, secret key, mapping token, or runtime model connection.

> Candidate rows are unverified source leads. Scout coverage is not verified-source coverage, priority tiers are operational work-order heuristics, and the dashboard does not report wage gaps or causal findings.

## Active phase and checkpoint — 2026-07-23

The current data layer reflects the serially merged Parallel Round 2 accounting
checkpoint and the PI-aligned **Source Discovery Scale-Up** strategy:

- 35,589 municipal and township governments in the authoritative universe;
- 1,537 successfully scout-covered municipalities;
- an approximately 2,000-covered workflow checkpoint, with 463 remaining;
- 1,267 candidate-positive and 270 parseable-empty municipalities;
- 27 failure-only municipalities retained outside successful coverage;
- 3,347 URL-bearing, unverified candidate queue rows;
- 34,046 future-scout-eligible municipalities, including 628 Tier 1 and 3,420 Tier 2; and
- latest-round wall time of 5,615.561 seconds, or 288.484 attempted rows per hour
  across the three completed Round 2 lanes.

The user-approved next plan is three internally serialized lanes × 300 ordinary
Tier-prioritized municipalities, with starts at minute 0/8/16. The earlier 3 ×
160 checkpoint-targeted plan is preserved but superseded. The aggressive round
is expected to overshoot 2,000; that overshoot is intentional, but it is only a
planning projection until a later live collection passes lane audit and a
separate serial merge updates accounting. Failure-only rows remain in a separate
retry lane. After that merge, broad scouting pauses for verification, wage
extraction, ingestion, source quality/extractability rating, descriptive
wage-growth-gap analysis, mechanism-correlation documentation, and a future
gap-percentage map/filter. Regressions are deferred.

The current PI checkpoint report is available in the dashboard’s Reports Library and directly here:

- [PI Source-Discovery Progress Report PDF](reports/pi_progress_report_source_discovery_2026-07-22.pdf)

## Hub sections

The dashboard is organized around what has been collected, what is current, and what is forthcoming:

1. **Overview** — national coverage, queue, failure, and checkpoint metrics with the project caveat.
2. **Project phase** — progress from 1,537 to approximately 2,000 covered, the user-approved aggressive round, and the post-checkpoint downstream sequence.
3. **Coverage and geography** — the existing token-free state choropleth, tile-grid alternate, state selection, and printable state view.
4. **Scouting priority tiers** — remaining Tier 1–Tier 5 pools, retry lane, and state-level high-priority workload.
5. **Scout operations** — wave runtimes, throughput, candidate rows per hour, failure rates, and current preflight/compact/adaptive controls.
6. **Candidate queue** — the source-discovery funnel, queue composition, and distinction between municipality and candidate-row counts.
7. **Verification pipeline** — the post-checkpoint progression from candidate lead through verification, extraction, ingestion, rating, and analysis readiness.
8. **State yield and learning** — observed discovery yield with minimum-sample and confidence warnings.
9. **Reports library** — current PI reports and durable checkpoint metadata, plus space for future verification reports.
10. **Methodology and definitions** — source-stage definitions that keep operational counts from being mistaken for evidence.
11. **Descriptive analysis plan** — future wage-growth gap percentage, map/filter, and mechanism-correlation capabilities that require verified/extracted data.
12. **Next steps** — the planned 3 × 300 collection, separate failure retries, serial accounting, and the checkpoint pause.

The sticky section navigation becomes a collapsible menu on smaller screens. Hash routes remain reserved for state selection and printable state reports:

- `#/state/CA` selects California;
- `#/state/CA/report` opens California’s printable state report.

## What the terms mean

- **Scout-covered municipality:** a municipality with a successful, parseable scout result. This does not mean a source was verified.
- **Candidate row:** one possible source URL or document lead queued for later review. A municipality can produce multiple rows.
- **Candidate-positive municipality:** a successfully scouted municipality with one or more candidate rows, not a verified matched evidence set.
- **Parseable-empty:** a completed scout result with no candidates. It is not proof that no source exists.
- **Failure-only:** a request without a usable result, held outside successful coverage for possible retry.
- **Priority tier:** a deterministic operational ranking used to schedule future discovery work. It is not a finding about unionization, source quality, or wages.
- **Verified source:** a lead whose employer, unit, provenance, dates, document type, access, and relevance have been checked.
- **Analysis-ready evidence:** matched safety and non-safety city-cycle evidence with validated wage fields and provenance. This stage is not yet available project-wide.

## Report library

Dashboard-accessible report metadata lives in:

```text
docs/dashboard/reports/reports_index.json
```

`scripts/build_dashboard_data.py` validates that source index and writes the dashboard data copy:

```text
docs/dashboard/data/reports_index.json
```

Each report record includes identity, checkpoint, source/PDF paths, tags, current status, producing commit, and a metrics snapshot. Exactly one report must be marked `current`.

To add a future report:

1. Commit the PDF below `docs/dashboard/reports/`.
2. Keep the Markdown source under `docs/analysis/`.
3. Add one validated record to `docs/dashboard/reports/reports_index.json`.
4. Mark the prior report non-current if the new report supersedes it.
5. Run `python scripts/build_dashboard_data.py`.
6. Build the frontend and test the report link.

## Map status

The default map is a geographic state choropleth rendered from a committed local GeoJSON asset. Alaska and Hawaii use labeled insets, and DC has an enlarged selection marker. A tile-grid choropleth remains available as a schematic alternate and accessibility fallback.

The map has no basemap, mapping SDK, API token, secret, or remote runtime URL. Both views use the same generated `state_summary.json`, state selection, detail panel, and accessible table.

Safe display metrics are:

1. scout coverage rate;
2. scout-covered municipality count;
3. candidate row count;
4. high-priority later-verification row count; and
5. operational evidence-readiness score.

The readiness score is workflow triage, not evidence strength. Wage gaps are not
a current map metric. A wage-growth-gap percentage layer and range filter are
planned only after verified/extracted matched wage data exist. Boundary
provenance and checksums are documented in [map_data_notes.md](map_data_notes.md).

## Data flow

```text
committed queue / coverage / universe / priority / wave summaries
                              |
                              v
             scripts/build_dashboard_data.py
                              |
                              v
                 docs/dashboard/data/*.json
                              |
                              v
                 static React/Vite project hub
```

The builder reads committed coordinator outputs and writes dashboard JSON only. It does not change national queue/coverage inputs, canonical contracts, city coverage, or corpus files. It does not open candidate URLs, verify sources, ingest documents, codify text, or call an API or model.

## Rebuild data

From the repository root:

```bash
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

The dashboard builder writes:

- `state_summary.json`
- `candidate_queue_summary.json`
- `coverage_funnel.json`
- `analysis_readiness.json`
- `priority_summary.json`
- `state_priority_summary.json`
- `top_priority_targets.json`
- `scout_operations_summary.json`
- `scout_yield_by_state.json`
- `scout_runtime_trends.json`
- `project_phase_summary.json`
- `parallel_scout_status.json`
- `reports_index.json`

Review the printed totals and diffs before committing. In particular, candidate-positive plus parseable-empty municipalities must equal scout-covered municipalities, and transport/failure-only results must remain outside successful coverage.

`parallel_scout_status.json` is an operations layer, not source evidence. Its
current status is `aggressive_3x300_planned_not_run`: the successful Round 2
3 × 150 merge remains the latest completed work, while three fresh 300-row lanes
are locked as the user-approved next collection. The earlier 3 × 160 plan is
marked `superseded_preserved_not_active`. Every active lane remains internally
serialized, writes to a unique output directory, and redirects its timestamped
candidate handoff to a lane-local export directory. Shared accounting remains
serial. At the recent 446/450 parseable rate, the 900 planned attempts project
about 892 newly covered municipalities and about 2,429 after a later successful
merge—an intentional, user-approved overshoot of roughly 429. This is an
operational projection, not live evidence. All candidate leads remain
unverified.

The priority JSON layers reflect the unchanged canonical methodology refreshed
after the Parallel Round 2 merge. The refresh followed 743 successful scouts
since the prior Tier 1 Wave 2 build, exceeding the documented 300–600-success
cadence. Any next target selection must still reconcile ranks against current
coverage and failure-only status.

## Run and build locally

The dashboard requires Node.js 20.19 or newer. With the existing locked dependencies:

```bash
cd docs/dashboard
npm ci
npm run dev
```

The default Vite base is `/gabriel-wages/`, so the local route is normally `http://localhost:5173/gabriel-wages/`. For a root-local route, use `npm run dev -- --base /`.

Build the production bundle with:

```bash
cd docs/dashboard
npm run build
npm run preview
```

Output is written to `docs/dashboard/dist/`. The production base is `/gabriel-wages/`.

The GitHub Pages workflow at `.github/workflows/deploy-dashboard.yml` regenerates dashboard JSON, installs locked dependencies, builds the site, and deploys on relevant pushes to `main`. See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

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
    ProjectHubSections.jsx
    ProjectNavigation.jsx
    StateDetailPanel.jsx
    StateTileGrid.jsx
    USChoroplethMap.jsx
    mapMetrics.js
    ui.jsx
  assets/
    us-states-2025-20m.geojson
```

All components consume committed local JSON and assets. No component fetches remote data.

## Validation

From the repository root:

```bash
python -m py_compile scripts/build_dashboard_data.py
python -m py_compile scripts/build_scout_yield_learning_report.py
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
python scripts/validate.py
python ingest/test_pipeline.py
python ingest/audit_coverage.py
git diff --check
```

Then:

```bash
cd docs/dashboard
npm run build
```

Review the production dashboard at desktop and mobile widths, test the map, section navigation, report link, and at least one printable state route.

## Interpretation rules

- A scout lead is not a verified source.
- A high-priority row or tier is a scheduling choice, not a source-quality judgment.
- A likely matched-set group still requires employer, document, unit, and cycle checks.
- A parseable-empty result is a completed scout outcome, not proof that no source exists.
- `null` means the dashboard lacks a validated input and must never be displayed as zero.
- Candidate volume must not be used as evidence of a wage gap, bargaining strength, mechanism, or causal effect.
