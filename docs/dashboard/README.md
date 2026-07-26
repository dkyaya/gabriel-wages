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

The verification-routing layer now covers all 4,726 URL-bearing candidate
rows. Two completed and serially merged rounds produced 4,726 durable routing
outcomes, including 3,750 reachable or successfully reused rows. No current
candidate URL remains unrouted.

The next offline layer is content triage. Metadata-only collection and its
single cumulative serial merge now cover all 4,726 routed candidates: the
preserved 1,000-row first round plus a 3,726-row, four-lane remainder round.
The durable metadata-only ledger records 1,760 p1, 1,232 p2, 360 p3, 1,372
deferred, and two excluded planning outcomes. All six source lanes and the
merge passed their gates without opening a URL, downloading content, parsing
a PDF, or running OCR. The dashboard records
`metadata_only_full_universe_merged`. Routing and metadata-triage outcomes
have not been upgraded into content-reviewed sources, final quality ratings,
content-supported extraction-ready documents, ingested records, or wage
evidence.

The current PI checkpoint report is available in the dashboard’s Reports Library and directly here:

- [PI Source-Discovery Progress Report PDF](reports/pi_progress_report_source_discovery_2026-07-22.pdf)

## Text/table calibration status — 2026-07-25

Automated visual + GABRIEL adjudication gate 1 completed all 150 blinded
calibration cases using 738 bounded local pages. All 150 GABRIEL responses
passed the strict JSON schema. The final auto gate contains 12
high-confidence-ready rows, 16 schema-update-ready rows, 19 second-review
rows, and 103 exclusions; its candidate-bearing wrong-page rate is 6.82%.
Only 27 of 80 original likely/p1 cases were ready, so the computed extraction
decision remains `continue_schema_refinement`. Neither the 500-document
extraction nor a smaller pilot is authorized. GABRIEL saw bounded page
packets only; no final wage values, URLs/downloads, OCR, extraction,
ingestion, codification, or wage-gap analysis occurred.

## Final provisional schema repair — 2026-07-26

The dashboard now reports the rollback-safe schema-repair layer as `compensation_extraction_final_provisional_schema_repair_partial_followup_required`. The five immutable package ledgers remain unchanged. The repair supplies 1,826 one-to-one retained-hash bridges, lossless unique non-base lineage columns, deterministic current-active/QA semantics, strict quantitative parsing with 387 candidates and 1,520 active exceptions, explicit historical mixed-membership statuses, a non-base companion view, and a reference/control view. Qualitative evidence remains navigation-only because literal evidence spans are absent; cycle/matched-set and controlled non-safety occupation metadata also remain incomplete. Analysis readiness and promotion remain false pending a separately authorized bounded follow-up.

## Bounded schema-repair follow-up — 2026-07-26

The bounded follow-up phase is `compensation_extraction_bounded_schema_followup_partial_additional_repair_required`. It establishes 1,255 exact full-date cycle bridges, 188 documents in 84 exact-period matched groups, 72 controlled non-safety subclasses, and retrieval provenance for all 1,826 identities. Exact-token parsing raises mechanically safe quantitative candidates to 862 while leaving 1,045 explicit exceptions. The immutable package and prior shadows remain unchanged. Qualitative evidence is still navigation-only because no dedicated literal spans exist, so analysis readiness and promotion remain false pending separately authorized bounded span/residual-metadata repair.

## Bounded qualitative-span and residual-metadata repair — 2026-07-26

The dashboard phase is `compensation_extraction_bounded_span_residual_repair_blocked_missing_text_support`. All 1,954 qualitative evidence pointers match retained packet-manifest page records, but those manifests retain metadata and counts rather than page-text payloads. Under the task's no-PDF/no-extraction boundary, zero literal spans could pass exact-substring QA, so no coded qualitative analysis view was created. Exact structured cycle notes raise supported cycle identities to 1,359 and matched coverage to 203 documents across 91 exact-period groups. Exact controlled unit-label rules raise established non-safety subclasses to 239; 467 cycle identities and 368 non-safety identities remain quarantined. The quantitative 862/1,045 candidate/exception split, non-base companion lane, reference/control lane, and two unresolved groups/five observations remain unchanged. Analysis readiness and promotion remain false pending separately authorized bounded local text-layer span capture.

The current phase is `compensation_extraction_bounded_pdf_text_span_capture_partial_additional_repair_required`. A hardened, page-scoped local PDF text-layer run hashed 788 retained readable PDFs and accessed exactly 1,223 approved pages for all 1,954 qualitative rows. It used no OCR, images, models, URLs, downloads, or non-target pages and saved no page text. The run captured 1,346 exact single-line literal substrings: 455 unique-candidate QA passes and 891 explicitly ambiguous matches; 608 rows had no safe literal match. Because 1,499 rows are not yet coded-analysis sufficient, no coded qualitative analysis view was created. The navigation view records span status, historical QA is preserved separately from span QA, and analysis readiness remains false.

## Bounded qualitative-span disambiguation follow-up — 2026-07-26

The current phase is `compensation_extraction_bounded_qualitative_span_disambiguation_partial_additional_repair_required`. The exact-only follow-up preserved all 455 prior verified spans without reaccessing their pages and reviewed the frozen 891 ambiguous plus 608 unavailable rows on 1,011 approved pages across 700 hash-verified PDFs. Deterministic structured-field and exact-token rules resolved 277 ambiguous and 27 unavailable rows, raising unique exact QA spans to 759. The remaining 614 ambiguous and 581 unavailable rows stay navigation-only, so no coded qualitative analysis view exists and analysis readiness remains false. All 32 focused tests pass; OCR-later, image, non-target, and page-text persistence counts remain zero.

## Final provisional schema readiness — 2026-07-26

The immutable five-ledger provisional package remains integrity-valid, but a
separate schema review held analysis-facing promotion. Five hashes and counts
still pass, all 371 active mixed joins validate, duplicate provenance remains
preserved, and the two residual groups remain explicit. Analysis readiness is
still false.

Critical repairs are needed before promotion: raw retained hashes,
city-unit-cycle/matched-set and controlled occupation keys, normalized
quantitative value/date semantics, unique non-base lineage headers, and
self-contained provenance. Fifty qualitative rows retain keys to inactive
mixed rows and 20 retain five missing historical keys; these must receive
explicit historical membership status. Non-base compensation remains a
separate companion lane. The next permitted action is a separately authorized
lossless schema-repair task, not ingestion, codification, or analysis.

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
- `content_triage_status_summary.json`
- `source_review_status_summary.json`
- `pdf_readiness_status_summary.json`
- `text_table_detection_status_summary.json`
- `text_table_calibration_status_summary.json`
- `reports_index.json`

The text/table calibration layer currently reports
`compensation_extraction_final_provisional_package_materialized_qa_pass`. The
authorized package-level merge verified and copied the five corrected shadow
ledgers byte-for-byte into five separate provisional lanes. The package
contains 1,907 active quantitative observations, 1,954 qualitative mechanism
observations, 371 mixed cases, 4,733 non-base-wage observations, and 345
reference/exclusion cases. Input/output SHA-256 values match; duplicate
observation IDs, invalid bounded pointers, and base/non-base contamination are
zero; all 14 duplicate-provenance rows and both explicitly unresolved groups
remain. All 1,826 readable content identities remain covered and OCR-later
documents remain untouched. The package is not a final analysis dataset:
analysis readiness remains false, and a separate schema/analysis-readiness
review is next. No GABRIEL/API call, new extraction, selection, URL access,
download, OCR, ingestion, codification, wage-gap calculation, or regression
occurred.

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

The verification operations layer is now `full_url_routing_merged`. Round 1
contributes 2,250 terminal rows and Round 2 contributes 2,476, yielding 4,726
/ 4,726 durably routed candidate URLs. Cumulatively, 3,750 (79.3483%) are
reachable or successfully reused. Round-specific ledgers remain preserved;
the cumulative and `latest` files retain both rounds rather than replacing
Round 1 with Round 2. These are availability/response-metadata routing
outcomes, not content relevance, ingestion, employer/unit confirmation, wage
extraction, or analysis-ready evidence. The next phase is content relevance
and extraction-readiness triage, not another broad URL-routing round.
Ingestion, codification, wage extraction, and wage-gap analysis remain not
started.

The offline planner also exposes `bulk_2x2000` for future candidate-queue
expansions: two routing-only lanes with at most 2,000 rows each, concurrency
eight per lane, 20/8/15-second total/connect/read limits, five redirects,
10 MiB, and content samples disabled. This is not a pending round for the
current queue. A capacity-only plan against the current cumulative ledger
selects zero rows and creates no lane input, while rerouting durable identities
requires explicit `--allow-reroute-already-verified` operator intent. Keep
3×1000 as the lower-risk routing fallback and use smaller lanes for content
triage, downloads, parsing, extraction, or rating.

The metadata-only content-triage layer is now durably merged for all 4,726
routed candidate identities. Its p1/p2/p3/defer/exclude values remain
preliminary scheduling outcomes, not source-content ratings. The 261
oversized routing outcomes remain deferred to a separately bounded strategy.

The durable source-review layer now has 2,150 cumulative rows: the repaired
150-row Pilot 1 HTTPX result, the 500-row Batch 2 result, and the 1,500-row
Batch 3 result. Across the three merged rounds, 2,124 retained PDF artifacts
have matching hashes and sizes. Retained PDF content totals approximately
4.500 GB; five rows are forbidden, 21 timed out, and repaired HTTPX
connection errors remain zero.

The dashboard phase is `batch3_3x500_merged`. Batch 3 contributes 1,480
retained PDFs, 16 timeout outcomes, four forbidden outcomes, and approximately
3.190 GB of PDF content.

Local PDF readiness is now durably merged for the complete
2,124-retained-PDF universe. The cumulative ledger combines exactly the
preserved 150-row Pilot 1 and the 1,974-row four-lane remainder. It has exact
source-review and candidate identity equality with the retained-PDF subset
of the cumulative source-review ledger. Every readiness row is terminal and
has a page count.

Cumulative sampled text-layer status is 1,608 present, 220 partial, and 296
absent; technical parseability is high, medium, and low for the same groups.
Page counts range from 1 to 463, have a median of 44, and represent 108,028
pages. Parser, hash, missing-artifact, and signature failures are zero.

The PDF-readiness phase remains `full_retained_merged`. The full bounded
local text/table-detection pass has now checked all 1,828
`parse_text_layer_later` artifacts in four 457-row lanes. It produced 1,067
likely, 749 possible, and 12 unlikely wage-table signals; 1,672 likely, 103
possible, and 53 unlikely contract-period signals; and 1,717 likely, 107
possible, and four unlikely table-structure signals. The runner retained
7,649 candidate page-number hints but no table cells, complete page text,
document text, or final wage values.

The text/table-detection phase is `full_parse_text_merged`. The durable
1,828-row ledger has exact PDF-readiness, source-review, and candidate
identity equality with the complete `parse_text_layer_later` authority. The
150 Pilot 1 identities were rerun under the same frozen heuristic and are
represented once through the uniform full-run result; the earlier pilot
outputs remain superseded diagnostic provenance. The next recommendation is
manual calibration of likely, possible, and unlikely page hints before any
wage-table extraction pilot. No URL was opened, nothing was downloaded, OCR
did not run, and ingestion, codification, final wage extraction, and
wage-gap analysis remain unperformed.

The first 150-row calibration packet has now completed bounded
Codex-assisted local adjudication. This was not independent human manual
review. Assisted labels are 112 yes, 22 maybe, 15 no, and one unknown for
wage-table presence; page hints are 118 correct, 14 partially correct, 17
not applicable, and one unknown. The extraction gate is `fail`: 55 rows need
second review, 59 are structurally hard, and detector/adjudicator concordance
is not ground-truth precision. A five-row rendered-page challenge materially
disagreed with all five assisted outcomes. Detector/review-schema refinement
and a new independent calibration are required before any extraction run.
The review opened only the 150 retained local PDFs and performed no URL
access, download, OCR, full-text retention, final wage extraction, ingestion,
or codification.

That failed review is now followed by a prepared—but not yet run—refined
visual table gate. The calibration phase is
`refinement_prepared_after_failed_review`. The refined schema records wage
language, pay-number language, actual table structure, wage-schedule
confirmation, candidate-page relationship, bounded contents/index/appendix
navigation, and confirmation method separately. It treats benefits tables,
classification lists without pay, non-wage tables, front matter, and prose
as distinct negative families. The original packet and REVIEW1 remain
unchanged; the next recommendation is `refined_re_review_before_extraction`.
The 500-document extraction remains prohibited, and OCR, wage extraction,
ingestion, and codification remain unstarted.

The refined 150-row re-review has now completed under
`refined_visual_gate_v1`, so the calibration phase is
`refined_review2_completed`. REVIEW2 separated wage language, pay-number
language, visual structure, wage-schedule confirmation, page relationship,
navigation, and extraction gate. Its assisted labels included 74
`pass_high_confidence`, 15 `pass_with_schema_update`, 29
`second_review_required`, and 32 `fail_exclude` rows. However, strict
likely-signal confirmation was 76.25%, the wrong-page rate was 31.82%, and
an 18-row blinded rendered-page challenge agreed on only 55.56% of material
decisions. The extraction decision is `continue_schema_refinement`: neither
the 500-document run nor a smaller extraction pilot is authorized.
Independent human adjudication and navigation/table-rule refinement are
next. No URL access, download, OCR, final wage extraction, ingestion, or
codification occurred.

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
