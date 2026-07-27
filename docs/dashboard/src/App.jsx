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
              Tier C source review retained {formatNumber(projectPhaseSummary.tier_c_retained_downloaded_source_count)}
              {" "}sources from {formatNumber(projectPhaseSummary.tier_c_verified_source_lead_count)} verified leads.
              The evidence remains a bounded documentary/co-location scaffold; no wage gaps or causal findings are available.
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
                <h2 id="overview-title">Current bounded evidence and retained-source status</h2>
              </div>
              <div className="checkpoint-label">
                <span>Next authorized stage</span>
                <strong>Bounded Tier C PDF/text-layer readiness review</strong>
              </div>
            </div>

            <div className="headline-grid" aria-label="National headline metrics">
              <MetricCard
                label="Retained Tier C sources"
                value={formatNumber(projectPhaseSummary.tier_c_retained_downloaded_source_count)}
                note="Downloaded and reviewed; not extracted or rated"
              />
              <MetricCard
                label="Verified Tier C leads"
                value={formatNumber(projectPhaseSummary.tier_c_verified_source_lead_count)}
                note="The locked source-review queue"
              />
              <MetricCard
                label="Same-source linked pairs"
                value={formatNumber(projectPhaseSummary.memo_scope.exact_same_source_linked_pair_count)}
                note={`${formatNumber(projectPhaseSummary.memo_scope.linked_quantitative_row_count)} quantitative rows · ${formatNumber(projectPhaseSummary.memo_scope.linked_qualitative_record_count)} qualitative records`}
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
                Retained files are not extracted, rated, ingested, codified, causal, or analysis-ready. The memo
                supports documentary co-location scaffolds, not normalized comparisons or causal conclusions.
              </span>
            </div>

            <ProjectOrientation
              totals={totals}
              priorityTotals={prioritySummary.totals}
              report={currentReport}
              phase={projectPhaseSummary}
            />
          </section>

          <ProjectPhasePanel phase={projectPhaseSummary} />

          <section className="hub-section-group" id="geography" aria-label="Coverage map and state status">
            <div className="hub-section-intro">
              <p className="eyebrow">Historical discovery coverage</p>
              <h2>Archived state-level source-discovery context</h2>
              <p>This map preserves the July discovery inventory for provenance. It is historical operational context, not the current evidence phase or a substantive outcome.</p>
            </div>
            <div className="map-and-panel">
              <NationalMap states={stateSummary.states} selectedCode={selected.state} onSelect={chooseState} />
              <StateDetailPanel state={selected} queue={selectedQueue} onOpenReport={openReport} />
            </div>
          </section>

          <PriorityTiersPanel priority={prioritySummary} statePriority={statePrioritySummary} />

          <ScoutOperationsPanel
            operations={scoutOperations}
            runtime={scoutRuntimeTrends}
            parallelStatus={parallelScoutStatus}
          />

          <section className="hub-section-group" id="candidate-queue" aria-labelledby="candidate-queue-title">
            <div className="hub-section-intro">
              <p className="eyebrow">Historical candidate queue</p>
              <h2 id="candidate-queue-title">Archived source-discovery inventory</h2>
              <p>
                These counts document the earlier discovery pipeline. They are not the current Tier C retained-source
                scope and do not override the 463-source readiness queue shown above.
              </p>
            </div>
            <div className="two-column">
              <CoverageFunnel data={coverageFunnel} />
              <CandidateQueueCards data={candidateSummary} />
            </div>
            <QueueTable rows={candidateSummary.by_state} onSelect={chooseState} />
          </section>

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

          <StateYieldPanel yieldData={scoutYieldByState} operations={scoutOperations} />

          <ReportsLibrary reportsIndex={reportsIndex} reportAssets={REPORT_ASSETS} />

          <MethodologyDefinitions />

          <AnalysisReadinessPanel data={analysisReadiness} phase={projectPhaseSummary} />

          <NextStepsPanel priority={prioritySummary} phase={projectPhaseSummary} />

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
