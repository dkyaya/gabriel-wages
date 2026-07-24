# Gabriel Wages Project Hub

The public project hub is published at:

<https://dkyaya.github.io/gabriel-wages/>

This directory contains a static, PI-facing research-status dashboard. It summarizes committed source-discovery, operational, prioritization, and planning artifacts. It has no backend, database, secret key, mapping token, or runtime model connection.

> Candidate rows are unverified source leads. Scout coverage is not verified-source coverage, priority tiers are operational work-order heuristics, and the dashboard does not report wage gaps or causal findings.

## Active phase and checkpoint — 2026-07-23

The current data layer reflects the serially merged Aggressive 3 × 300
Attempt 3 accounting checkpoint and the transition from broad discovery to
verification planning:

- 35,589 municipal and township governments in the authoritative universe;
- 2,436 successfully scout-covered municipalities;
- the approximately 2,000-covered workflow checkpoint exceeded by 436;
- 1,858 candidate-positive and 578 parseable-empty municipalities;
- 28 failure-only municipalities retained outside successful coverage;
- 4,726 URL-bearing, unverified candidate queue rows;
- 33,147 future-scout-eligible municipalities, including 245 Tier 1 and 2,906 Tier 2; and
- latest-round wall time of 9,422.628 seconds, or 343.853 attempted rows per
  hour across the three completed Attempt 3 lanes.

The user-approved three-lane aggressive round completed and passed a separate
serial accounting merge. Its intentional checkpoint overshoot is now official.
The earlier 3 × 160 checkpoint-targeted plan remains preserved but superseded.
Broad scouting is paused. The next phase is candidate verification, wage
extraction, ingestion, source quality/extractability rating, descriptive
wage-growth-gap analysis, mechanism-correlation documentation, and a future
gap-percentage map/filter. Regressions are deferred.

The scaled verification framework now maps all 4,726 URL-bearing candidate
rows. Its first offline-prepared round contains 750 scheduled candidates in
three 250-row lanes; five nominal rounds cover all 3,600 scheduled rows and
seven cover the full queue, including explicitly held and duplicate/canonical
dispositions. All three first-round dry runs passed without opening a URL.
Live verification remains `not_started`.

The current PI checkpoint report is available in the dashboard’s Reports Library and directly here:

- [PI Source-Discovery Progress Report PDF](reports/pi_progress_report_source_discovery_2026-07-22.pdf)

## Hub sections

The dashboard is organized around what has been collected, what is current, and what is forthcoming:

1. **Overview** — national coverage, queue, failure, and checkpoint metrics with the project caveat.
2. **Project phase** — the 2,436-municipality checkpoint result, active broad-scouting pause, and downstream sequence.
3. **Coverage and geography** — the existing token-free state choropleth, tile-grid alternate, state selection, and printable state view.
4. **Scouting priority tiers** — remaining Tier 1–Tier 5 pools, retry lane, and state-level high-priority workload.
5. **Scout operations** — wave runtimes, throughput, candidate rows per hour, failure rates, and current preflight/compact/adaptive controls.
6. **Candidate queue** — the source-discovery funnel, queue composition, and distinction between municipality and candidate-row counts.
7. **Verification pipeline** — the post-checkpoint progression from candidate lead through verification, extraction, ingestion, rating, and analysis readiness.
8. **State yield and learning** — observed discovery yield with minimum-sample and confidence warnings.
9. **Reports library** — current PI reports and durable checkpoint metadata, plus space for future verification reports.
10. **Methodology and definitions** — source-stage definitions that keep operational counts from being mistaken for evidence.
11. **Descriptive analysis plan** — future wage-growth gap percentage, map/filter, and mechanism-correlation capabilities that require verified/extracted data.
12. **Next steps** — first verification-batch planning, extraction/ingestion preparation, and the checkpoint pause.

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
- `verification_status_summary.json`
- `reports_index.json`

Review the printed totals and diffs before committing. In particular, candidate-positive plus parseable-empty municipalities must equal scout-covered municipalities, and transport/failure-only results must remain outside successful coverage.

`parallel_scout_status.json` is an operations layer, not source evidence. Its
current status is `aggressive_3x300_completed_accounting_merged`. Attempt 3
produced 899 parseable outcomes from 900 attempts and raised official coverage
to 2,436. Every lane remained internally serialized, wrote to a unique output
directory, and redirected its candidate handoff to a lane-local export
directory. Shared accounting was merged once, serially, after the combined
audit. All candidate leads remain unverified, and broad scouting is paused.

The priority JSON layers reflect the unchanged canonical methodology refreshed
after the Aggressive Attempt 3 merge added 899 successful scouts and crossed
the workflow checkpoint. They are retained as current operational state, but
must not be used to schedule another ordinary discovery wave while broad
scouting is paused.

The verification operations layer is now `round1_3x750_merged`. The bounded
live round `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23` produced and serially
merged 2,250 terminal URL-routing outcomes: 1,888 (83.911%) were reachable or
successfully reused. The durable routing ledger preserves every queue identity
and every terminal status. This is availability/response-metadata routing, not
content relevance, ingestion, employer/unit confirmation, wage extraction, or
analysis-ready evidence. An estimated 1,350 scheduled rows and 2,476 total
URL-bearing rows remain. Ingestion, codification, wage extraction, and
wage-gap analysis remain not started.

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
