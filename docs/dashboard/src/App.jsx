import { useEffect, useMemo, useState } from "react";
import stateSummary from "../data/state_summary.json";
import candidateSummary from "../data/candidate_queue_summary.json";
import coverageFunnel from "../data/coverage_funnel.json";
import analysisReadiness from "../data/analysis_readiness.json";
import prioritySummary from "../data/priority_summary.json";
import statePrioritySummary from "../data/state_priority_summary.json";
import scoutOperations from "../data/scout_operations_summary.json";
import scoutRuntimeTrends from "../data/scout_runtime_trends.json";
import scoutYieldByState from "../data/scout_yield_by_state.json";
import projectPhaseSummary from "../data/project_phase_summary.json";
import parallelScoutStatus from "../data/parallel_scout_status.json";
import verificationStatus from "../data/verification_status_summary.json";
import contentTriageStatus from "../data/content_triage_status_summary.json";
import sourceReviewStatus from "../data/source_review_status_summary.json";
import pdfReadinessStatus from "../data/pdf_readiness_status_summary.json";
import textTableDetectionStatus from "../data/text_table_detection_status_summary.json";
import textTableCalibrationStatus from "../data/text_table_calibration_status_summary.json";
import reportsIndex from "../data/reports_index.json";
import piProgressReportPdf from "../reports/pi_progress_report_source_discovery_2026-07-22.pdf?url";
import { AnalysisReadinessPanel } from "./components/AnalysisReadinessPanel.jsx";
import { CandidateQueueCards } from "./components/CandidateQueueCards.jsx";
import { CoverageFunnel } from "./components/CoverageFunnel.jsx";
import { DataLimitations } from "./components/DataLimitations.jsx";
import { NationalMap } from "./components/NationalMap.jsx";
import { PrintableStateReport } from "./components/PrintableStateReport.jsx";
import { ProjectNavigation } from "./components/ProjectNavigation.jsx";
import {
  MethodologyDefinitions,
  NextStepsPanel,
  PriorityTiersPanel,
  ProjectPhasePanel,
  ProjectOrientation,
  ReportsLibrary,
  ScoutOperationsPanel,
  StateYieldPanel,
  VerificationPipeline,
} from "./components/ProjectHubSections.jsx";
import { StateDetailPanel } from "./components/StateDetailPanel.jsx";
import { MetricCard, StatusPill, formatNumber } from "./components/ui.jsx";

const DEFAULT_STATE = "CA";
const REPORT_ASSETS = {
  "pi-source-discovery-2026-07-22": piProgressReportPdf,
};

function routeFromHash() {
  const match = window.location.hash.match(/^#\/state\/([A-Z]{2})(\/report)?$/);
  return {
    state: match?.[1] ?? DEFAULT_STATE,
    view: match?.[2] ? "report" : "dashboard",
  };
}

function formatCountMap(value) {
  return Object.entries(value ?? {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([label, count]) => `${label.replaceAll("_", " ")} ${formatNumber(count)}`)
    .join(" · ") || "None";
}

function QueueTable({ rows, onSelect }) {
  return (
    <section className="panel queue-table-panel" aria-labelledby="queue-table-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Historical queue by state</p>
          <h2 id="queue-table-title">Where the archived discovery queue was concentrated</h2>
        </div>
        <span className="quiet-label">Scheduling workload, not source quality</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">State</th>
              <th scope="col">Candidate rows</th>
              <th scope="col">Municipalities</th>
              <th scope="col">High priority</th>
              <th scope="col">Likely sets</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((state) => (
              <tr key={state.state}>
                <th scope="row">
                  <button className="table-state-button" onClick={() => onSelect(state.state)}>
                    {state.state_name}
                  </button>
                </th>
                <td>{formatNumber(state.candidate_rows)}</td>
                <td>{formatNumber(state.municipalities_with_queue_rows)}</td>
                <td>{formatNumber(state.high_priority_rows)}</td>
                <td>{formatNumber(state.likely_matched_set_municipalities)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function App() {
  const [route, setRoute] = useState(routeFromHash);
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [evidenceFilterDimension, setEvidenceFilterDimension] = useState("claim_readiness_bucket");
  const [evidenceFilterValue, setEvidenceFilterValue] = useState("");

  useEffect(() => {
    const handleHashChange = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const selected = useMemo(
    () => stateSummary.states.find((item) => item.state === route.state) ?? stateSummary.states[0],
    [route.state],
  );
  const selectedQueue = candidateSummary.by_state.find((item) => item.state === selected.state);
  const currentReport = reportsIndex.reports.find((report) => report.current) ?? reportsIndex.reports[0];
  const currentReportHref = currentReport.href ?? REPORT_ASSETS[currentReport.id];
  const evidenceFilterCatalog = projectPhaseSummary.rating_summary_filter_catalog ?? {};
  const evidenceFilterOptions = evidenceFilterCatalog[evidenceFilterDimension] ?? {};
  const evidenceFilterCount = evidenceFilterValue
    ? evidenceFilterOptions[evidenceFilterValue] ?? 0
    : Object.values(evidenceFilterOptions).reduce((sum, count) => sum + count, 0);

  function chooseState(code) {
    window.location.hash = `/state/${code}`;
    setRoute({ state: code, view: "dashboard" });
  }

  function openReport() {
    window.location.hash = `/state/${selected.state}/report`;
    setRoute({ state: selected.state, view: "report" });
  }

  function navigateToSection(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setNavigationOpen(false);
  }

  if (route.view === "report") {
    return (
      <PrintableStateReport
        state={selected}
        queue={selectedQueue}
        metadata={stateSummary.metadata}
        limitations={stateSummary.metadata.limitations}
        onBack={() => chooseState(selected.state)}
      />
    );
  }

  const totals = stateSummary.totals;
  return (
    <>
      <a className="skip-link" href="#overview">Skip to project overview</a>
      <div className="app-shell">
        <header className="site-header no-print">
          <div>
            <p className="eyebrow">HBS municipal labor evidence project</p>
            <h1>Gabriel Wages project hub</h1>
            <p className="header-deck">
              Current operation: {projectPhaseSummary.current_phase}. The next authorized stage is
              {" "}{projectPhaseSummary.next_task}. Exact-span ratings remain bounded; no ingestion, wage gaps,
              regressions, treatment effects, population-prevalence estimates, or final causal findings are available.
            </p>
          </div>
          <div className="header-status">
            <StatusPill tone="scout">{projectPhaseSummary.current_phase}</StatusPill>
            <span>Data vintage {projectPhaseSummary.data_vintage}</span>
            <a href={currentReportHref} target="_blank" rel="noreferrer">
              {currentReport.link_label ?? "Open current evidence memo"}
            </a>
          </div>
        </header>

        <ProjectNavigation
          open={navigationOpen}
          onToggle={() => setNavigationOpen((value) => !value)}
          onNavigate={navigateToSection}
        />

        <main>
          <section className="overview-section" id="overview" aria-labelledby="overview-title">
            <div className="overview-heading">
              <div>
                <p className="eyebrow">Overview</p>
                <h2 id="overview-title">Current source-pipeline readiness status</h2>
              </div>
                <div className="checkpoint-label">
                  <span>Next authorized stage</span>
                  <strong>{projectPhaseSummary.next_phase}</strong>
                </div>
            </div>

            <div className="headline-grid" aria-label="National headline metrics">
              <MetricCard
                label="Scout-covered municipalities"
                value={formatNumber(projectPhaseSummary.current_scout_covered)}
                note={`Actual parseable scout outcomes only · map data date ${projectPhaseSummary.map_data_date}`}
              />
              <MetricCard
                label="Total candidate rows"
                value={formatNumber(projectPhaseSummary.current_candidate_queue_rows)}
                note={`${formatNumber(projectPhaseSummary.broad_state_4x1000_live_candidate_count)} new · ${formatNumber(projectPhaseSummary.broad_state_4x1000_live_deduped_candidate_count)} deduplicated in the 4x1000 wave`}
              />
              <MetricCard
                label="Readiness reviewed"
                value={formatNumber(projectPhaseSummary.pdf_text_readiness_reviewed_count)}
                note={`${formatNumber(projectPhaseSummary.pdf_text_readiness_extraction_ready_count)} technically ready of ${formatNumber(projectPhaseSummary.pdf_text_readiness_queue_size)} retained sources`}
              />
              <MetricCard
                label="Retained sources"
                value={formatNumber(projectPhaseSummary.source_review_download_retained_count)}
                note={`${formatNumber(projectPhaseSummary.pdf_text_readiness_extraction_ready_count)} extraction-ready · retained binaries remain outside Git`}
              />
              <MetricCard
                label="Text extraction attempted"
                value={formatNumber(projectPhaseSummary.text_extraction_attempted_count)}
                note={`${formatNumber(projectPhaseSummary.text_extracted_ok_count)} extracted OK · PDF ${formatNumber(projectPhaseSummary.text_extraction_pdf_extracted_ok_count)} · HTML ${formatNumber(projectPhaseSummary.text_extraction_html_extracted_ok_count)} · other ${formatNumber(projectPhaseSummary.text_extraction_other_document_extracted_ok_count)}`}
              />
              <MetricCard
                label="Extraction quality deferrals"
                value={formatNumber(
                  projectPhaseSummary.text_extraction_empty_too_short_count
                  + projectPhaseSummary.text_extraction_low_density_count
                  + projectPhaseSummary.text_extraction_bad_text_layer_count
                  + projectPhaseSummary.text_extraction_html_noisy_shell_count
                  + projectPhaseSummary.text_extraction_other_document_unsupported_count
                  + projectPhaseSummary.text_extraction_error_count
                )}
                note={
                  "Empty/short " + formatNumber(projectPhaseSummary.text_extraction_empty_too_short_count)
                  + " · low density " + formatNumber(projectPhaseSummary.text_extraction_low_density_count)
                  + " · bad layer " + formatNumber(projectPhaseSummary.text_extraction_bad_text_layer_count)
                  + " · HTML noisy " + formatNumber(projectPhaseSummary.text_extraction_html_noisy_shell_count)
                  + " · unsupported " + formatNumber(projectPhaseSummary.text_extraction_other_document_unsupported_count)
                  + " · errors " + formatNumber(projectPhaseSummary.text_extraction_error_count)
                }
              />
              <MetricCard
                label="Extracted text storage"
                value="Git-ignored"
                note={projectPhaseSummary.text_extraction_artifact_root}
              />
              <MetricCard
                label="Span extraction attempted"
                value={formatNumber(projectPhaseSummary.span_extraction_attempted_count)}
                note={`${formatNumber(projectPhaseSummary.span_extraction_queue_size)} extracted-ok sources in the locked queue`}
              />
              <MetricCard
                label="Positive exact spans"
                value={formatNumber(projectPhaseSummary.span_positive_exact_count)}
                note={`${formatNumber(projectPhaseSummary.span_sources_with_positive_count)} sources · candidates only, not rated`}
              />
              <MetricCard
                label="Span families"
                value={formatNumber(
                  projectPhaseSummary.span_quantitative_compensation_count
                  + projectPhaseSummary.span_qualitative_mechanism_count
                )}
                note={
                  "Quantitative " + formatNumber(projectPhaseSummary.span_quantitative_compensation_count)
                  + " · qualitative " + formatNumber(projectPhaseSummary.span_qualitative_mechanism_count)
                  + " · navigation " + formatNumber(projectPhaseSummary.span_source_navigation_count)
                  + " · non-base " + formatNumber(projectPhaseSummary.span_non_base_compensation_count)
                }
              />
              <MetricCard
                label="Span deferrals"
                value={formatNumber(
                  projectPhaseSummary.span_no_span_or_weak_count
                  + projectPhaseSummary.span_ambiguous_count
                  + projectPhaseSummary.span_extraction_error_count
                )}
                note={
                  "No span/weak " + formatNumber(projectPhaseSummary.span_no_span_or_weak_count)
                  + " · ambiguous " + formatNumber(projectPhaseSummary.span_ambiguous_count)
                  + " · errors " + formatNumber(projectPhaseSummary.span_extraction_error_count)
                }
              />
              <MetricCard
                label="Rating candidates"
                value={formatNumber(projectPhaseSummary.span_rating_candidate_count)}
                note={`${formatNumber(projectPhaseSummary.exact_span_rating_attempted_count)} attempted in live bounded rating`}
              />
              <MetricCard
                label="Valid exact-span ratings"
                value={formatNumber(projectPhaseSummary.exact_span_rating_valid_count)}
                note={`${formatNumber(projectPhaseSummary.exact_span_rating_queue_size)} queued · ${formatNumber(projectPhaseSummary.exact_span_rating_quarantine_count)} quarantined and excluded`}
              />
              <MetricCard
                label="Rating candidates by family"
                value={formatNumber(Object.values(projectPhaseSummary.exact_span_rating_candidate_evidence_family_counts ?? {}).reduce((sum, count) => sum + count, 0))}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_candidate_evidence_family_counts)}
              />
              <MetricCard
                label="Rated evidence families"
                value={formatNumber(Object.values(projectPhaseSummary.exact_span_rating_evidence_family_counts ?? {}).reduce((sum, count) => sum + count, 0))}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_evidence_family_counts)}
              />
              <MetricCard
                label="Rated mechanism labels"
                value={formatNumber(Object.keys(projectPhaseSummary.exact_span_rating_mechanism_counts ?? {}).length)}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_mechanism_counts)}
              />
              <MetricCard
                label="Rated quantitative labels"
                value={formatNumber(Object.keys(projectPhaseSummary.exact_span_rating_quantitative_label_counts ?? {}).length)}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_quantitative_label_counts)}
              />
              <MetricCard
                label="Claim relevance"
                value={formatNumber(Object.keys(projectPhaseSummary.exact_span_rating_claim_relevance_counts ?? {}).length)}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_claim_relevance_counts)}
              />
              <MetricCard
                label="Evidence strength"
                value={formatNumber(Object.values(projectPhaseSummary.exact_span_rating_evidence_strength_counts ?? {}).reduce((sum, count) => sum + count, 0))}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_evidence_strength_counts)}
              />
              <MetricCard
                label="Direction of pressure"
                value={formatNumber(Object.values(projectPhaseSummary.exact_span_rating_direction_counts ?? {}).reduce((sum, count) => sum + count, 0))}
                note={formatCountMap(projectPhaseSummary.exact_span_rating_direction_counts)}
              />
              <MetricCard
                label="Claim-summary candidates"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_candidate_count)}
                note={`${formatNumber(projectPhaseSummary.rating_summary_valid_count)} valid summarized · ${formatNumber(projectPhaseSummary.rating_summary_quarantine_excluded_count)} quarantines excluded`}
              />
              {projectPhaseSummary.combined_broad_rating_ingestion_codification_available && (
                <MetricCard
                  label="Ingestion / codification queue"
                  value={formatNumber(projectPhaseSummary.rating_ingestion_queue_count)}
                  note={`${formatNumber(projectPhaseSummary.rating_codification_quarantine_excluded_count)} quarantines excluded before ingestion`}
                />
              )}
              {projectPhaseSummary.combined_broad_rating_ingestion_codification_available && (
                <MetricCard
                  label="Ingested and codified records"
                  value={formatNumber(projectPhaseSummary.rating_codified_record_count)}
                  note={`${formatNumber(projectPhaseSummary.rating_ingested_record_count)} ingested · schema-stable bounded records`}
                />
              )}
              {projectPhaseSummary.combined_broad_rating_ingestion_codification_available && (
                <MetricCard
                  label="Global-readiness gate"
                  value={projectPhaseSummary.global_analysis_readiness_gate_available ? "Complete" : "Ready next"}
                  note={projectPhaseSummary.global_analysis_readiness_gate_available ? "Narrow partial diagnostic; legacy global readiness remains false" : "Diagnostic gate only; global analysis readiness remains false"}
                />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Collection readiness" value={projectPhaseSummary.global_collection_readiness} note="Broad lineaged corpus; corpus-bounded and not population-representative" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Mechanism readiness" value={projectPhaseSummary.global_mechanism_analysis_readiness} note="Bounded documentary description only; no causal interpretation" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Quantitative evidence readiness" value={projectPhaseSummary.global_quantitative_evidence_readiness} note="Availability only; values remain unnormalized" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Wage-gap readiness" value={projectPhaseSummary.global_wage_gap_analysis_readiness} note="Blocked until normalization and city × cycle × occupation matching pass" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Causal readiness" value={projectPhaseSummary.global_causal_analysis_readiness} note="Blocked until matched structure and causal-design requirements pass" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Overall readiness" value={projectPhaseSummary.overall_global_analysis_readiness} note="Narrow diagnostic status; global_analysis_readiness remains false" />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Top readiness blockers" value={formatNumber(projectPhaseSummary.global_readiness_top_blockers?.length)} note={(projectPhaseSummary.global_readiness_top_blockers ?? []).join(" · ")} />
              )}
              {projectPhaseSummary.global_analysis_readiness_gate_available && (
                <MetricCard label="Next planned stage" value="4 × 2,500 prep" note="10,000-target ceiling; scouting infrastructure only" />
              )}
              <MetricCard
                label="Globally usable descriptive evidence"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_readiness_counts?.global_descriptive_ready)}
                note="Corpus-bounded candidates only; ingestion/codification still required"
              />
              <MetricCard
                label="Usable with caveats"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_readiness_counts?.global_descriptive_ready_with_caveats)}
                note="Label, strength, direction, or corpus-composition caveats apply"
              />
              <MetricCard
                label="Quantitative needs normalization"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_readiness_counts?.quant_needs_normalization)}
                note="Not wage-gap or cross-record comparison evidence"
              />
              <MetricCard
                label="Mechanism-summary ready"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_readiness_counts?.mechanism_summary_ready)}
                note="Strong/moderate documentary mechanism wording; not causal evidence"
              />
              <MetricCard
                label="Source-navigation only"
                value={formatNumber(projectPhaseSummary.rating_summary_claim_readiness_counts?.source_navigation_only)}
                note="Useful for finding schedules or attachments; not standalone evidence"
              />
              <MetricCard
                label="Weak, context, or unsupported"
                value={formatNumber(
                  (projectPhaseSummary.rating_summary_claim_readiness_counts?.weak_or_not_supported ?? 0)
                  + (projectPhaseSummary.rating_summary_claim_readiness_counts?.local_context_only ?? 0)
                )}
                note="Excluded from bounded global descriptive candidates"
              />
              <MetricCard
                label="Directional and provisional hints"
                value={formatNumber(
                  (projectPhaseSummary.rating_summary_claim_readiness_counts?.directional_hint_only ?? 0)
                  + (projectPhaseSummary.rating_summary_claim_readiness_counts?.provisional_causal_hint_only ?? 0)
                )}
                note="Hints only; no global directional or causal finding"
              />
              <MetricCard
                label="Dashboard evidence organization"
                value={`${formatNumber(projectPhaseSummary.rating_summary_dashboard_evidence_box_count)} boxes`}
                note={`${formatNumber(projectPhaseSummary.rating_summary_dashboard_filter_count)} controlled evidence filters outside the map`}
              />
              <MetricCard
                label="Global analysis readiness"
                value="False"
                note={projectPhaseSummary.rating_summary_diagnostic_status ?? "No wage-gap, regression, treatment-effect, or final causal result"}
              />
            </div>

            {projectPhaseSummary.combined_exact_span_rating_summary_available && (
              <div className="hub-caveat" role="note" aria-label="Rated evidence boxes and filters">
                <strong>Rated evidence boxes and filters.</strong>
                <span>{formatCountMap(
                  projectPhaseSummary.rating_codification_evidence_box_counts
                  ?? projectPhaseSummary.rating_summary_evidence_box_counts
                )}</span>
                <div className="evidence-filter-controls" aria-label="Aggregate rated-evidence filter controls">
                  <label>
                    Evidence dimension
                    <select
                      value={evidenceFilterDimension}
                      onChange={(event) => {
                        setEvidenceFilterDimension(event.target.value);
                        setEvidenceFilterValue("");
                      }}
                    >
                      {Object.keys(evidenceFilterCatalog).map((dimension) => (
                        <option key={dimension} value={dimension}>{dimension.replaceAll("_", " ")}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Category
                    <select value={evidenceFilterValue} onChange={(event) => setEvidenceFilterValue(event.target.value)}>
                      <option value="">All categories</option>
                      {Object.entries(evidenceFilterOptions)
                        .sort((a, b) => b[1] - a[1])
                        .map(([label, count]) => (
                          <option key={label} value={label}>{label.replaceAll("_", " ")} · {formatNumber(count)}</option>
                        ))}
                    </select>
                  </label>
                  <div className="evidence-filter-result" aria-live="polite">
                    <span>Selected corpus-bounded records</span>
                    <strong>{formatNumber(evidenceFilterCount)}</strong>
                  </div>
                </div>
                <div className="tag-list" aria-label="Evidence filters outside the map">
                  {(projectPhaseSummary.rating_summary_dashboard_filter_names ?? []).map((filterName) => (
                    <span key={filterName}>{filterName.replaceAll("_", " ")}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="hub-caveat" role="note">
              <strong>Bounded evidence status only.</strong>
              <span>
                Extracted text remains a local, Git-ignored artifact. Rating-summary buckets are bounded documentary classifications—not
                ingestion, codification, quantitative normalization/comparison, population evidence, directional findings, or causal conclusions.
                The Tier C memo remains a completed historical evidence artifact, not the current operation.
              </span>
            </div>

            <ProjectOrientation
              totals={totals}
              priorityTotals={prioritySummary.totals}
              report={currentReport}
              phase={projectPhaseSummary}
            />
          </section>

          <section className="hub-section-group" id="geography" aria-label="Coverage map and state status">
            <div className="hub-section-intro">
              <p className="eyebrow">Total scout coverage</p>
              <h2>A simple answer to “where have we scouted?”</h2>
              <p>This is the dashboard’s only map layer. Tier C, mechanism, source-family, readiness, extraction, and rating details live in pipeline cards and reports below.</p>
            </div>
            <div className="map-and-panel">
              <NationalMap states={stateSummary.states} selectedCode={selected.state} onSelect={chooseState} mapDataDate={stateSummary.metadata.map_data_date} />
              <StateDetailPanel state={selected} queue={selectedQueue} onOpenReport={openReport} />
            </div>
          </section>

          <ProjectPhasePanel phase={projectPhaseSummary} />

          <VerificationPipeline
            candidateSummary={candidateSummary}
            readiness={analysisReadiness}
            phase={projectPhaseSummary}
            verificationStatus={verificationStatus}
            contentTriageStatus={contentTriageStatus}
            sourceReviewStatus={sourceReviewStatus}
            pdfReadinessStatus={pdfReadinessStatus}
            textTableDetectionStatus={textTableDetectionStatus}
            textTableCalibrationStatus={textTableCalibrationStatus}
          />

          <ReportsLibrary reportsIndex={reportsIndex} reportAssets={REPORT_ASSETS} />

          <AnalysisReadinessPanel data={analysisReadiness} phase={projectPhaseSummary} />

          <NextStepsPanel priority={prioritySummary} phase={projectPhaseSummary} />

          <details className="historical-archive" id="historical-archive">
            <summary>
              <span>Historical pipeline archive</span>
              <small>Priority tiers, scouting operations, archived candidate queue, and state yield</small>
            </summary>
            <div className="historical-archive-content">
              <PriorityTiersPanel priority={prioritySummary} statePriority={statePrioritySummary} />
              <ScoutOperationsPanel operations={scoutOperations} runtime={scoutRuntimeTrends} parallelStatus={parallelScoutStatus} />
              <section className="hub-section-group" id="candidate-queue" aria-labelledby="candidate-queue-title">
                <div className="hub-section-intro">
                  <p className="eyebrow">Historical candidate queue</p>
                  <h2 id="candidate-queue-title">Archived source-discovery inventory</h2>
                  <p>These counts document the earlier discovery pipeline; they are not the current text/span scope.</p>
                </div>
                <div className="two-column"><CoverageFunnel data={coverageFunnel} /><CandidateQueueCards data={candidateSummary} /></div>
                <QueueTable rows={candidateSummary.by_state} onSelect={chooseState} />
              </section>
              <StateYieldPanel yieldData={scoutYieldByState} operations={scoutOperations} />
            </div>
          </details>

          <MethodologyDefinitions />

          <DataLimitations
            metadata={{
              ...stateSummary.metadata,
              generated_at: projectPhaseSummary.generated_at,
              data_vintage: projectPhaseSummary.data_vintage,
            }}
            metricDefinition={stateSummary.metric_definition.evidence_readiness_score}
          />
        </main>

        <footer>
          <div>
            <p>Generated {projectPhaseSummary.generated_at}. Current project data vintage {projectPhaseSummary.data_vintage}.</p>
            <p>{projectPhaseSummary.current_phase}. Global analysis readiness remains false.</p>
          </div>
          <div className="footer-links">
            <button type="button" onClick={() => navigateToSection("overview")}>Back to overview</button>
            <a href={currentReportHref} target="_blank" rel="noreferrer">
              {currentReport.link_label ?? currentReport.title}
            </a>
          </div>
        </footer>
      </div>
    </>
  );
}

export default App;
