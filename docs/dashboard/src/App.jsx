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
              The four-lane broad scout is complete and the current operation is bounded locator verification:
              {" "}{formatNumber(projectPhaseSummary.verification_completed_count)} of {formatNumber(projectPhaseSummary.verification_queue_size)}
              {" "}locked outcomes completed. No document review, wage gaps, or causal findings are available.
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
                <h2 id="overview-title">Current broad-scout and verification status</h2>
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
                note="Actual parseable scout outcomes only · map data date 2026-07-27"
              />
              <MetricCard
                label="Total candidate rows"
                value={formatNumber(projectPhaseSummary.current_candidate_queue_rows)}
                note={`${formatNumber(projectPhaseSummary.broad_state_4x1000_live_candidate_count)} new · ${formatNumber(projectPhaseSummary.broad_state_4x1000_live_deduped_candidate_count)} deduplicated in the 4x1000 wave`}
              />
              <MetricCard
                label="Verification completed"
                value={formatNumber(projectPhaseSummary.verification_completed_count)}
                note={`${formatNumber(projectPhaseSummary.verification_verified_reachable_count)} reachable of ${formatNumber(projectPhaseSummary.verification_queue_size)} locked locators`}
              />
              <MetricCard
                label="Global analysis readiness"
                value="False"
                note="No wage-gap, regression, treatment-effect, or final causal result"
              />
            </div>

            <div className="hub-caveat" role="note">
              <strong>Bounded evidence status only.</strong>
              <span>
                Locator verification is reachability metadata only. The Tier C memo remains a completed historical
                evidence artifact; neither stage supplies normalized comparisons or causal conclusions.
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
