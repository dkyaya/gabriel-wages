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
  ProjectOrientation,
  ReportsLibrary,
  ScoutOperationsPanel,
  StateYieldPanel,
  VerificationPipeline,
} from "./components/ProjectHubSections.jsx";
import { StateDetailPanel } from "./components/StateDetailPanel.jsx";
import { MetricCard, StatusPill, formatNumber, formatPercent } from "./components/ui.jsx";

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
          <p className="eyebrow">Queue by active state</p>
          <h2 id="queue-table-title">Where later review is concentrated</h2>
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
  const nationalCoverageRate = (100 * totals.scout_covered_municipalities) / totals.municipality_universe;

  return (
    <>
      <a className="skip-link" href="#overview">Skip to project overview</a>
      <div className="app-shell">
        <header className="site-header no-print">
          <div>
            <p className="eyebrow">HBS municipal labor evidence project</p>
            <h1>Gabriel Wages project hub</h1>
            <p className="header-deck">
              A permanent view of what has been collected, what the current evidence supports, and what must happen
              next. Candidate rows remain unverified source leads; this hub does not report wage gaps or causal findings.
            </p>
          </div>
          <div className="header-status">
            <StatusPill tone="scout">Post-Tier 1 Wave 2</StatusPill>
            <span>Data vintage {stateSummary.metadata.data_vintage}</span>
            <a href={piProgressReportPdf} target="_blank" rel="noreferrer">Open current PI report</a>
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
                <h2 id="overview-title">National source-discovery status</h2>
              </div>
              <div className="checkpoint-label">
                <span>Latest checkpoint</span>
                <strong>{currentReport.checkpoint}</strong>
              </div>
            </div>

            <div className="headline-grid" aria-label="National headline metrics">
              <MetricCard
                label="Municipal universe"
                value={formatNumber(totals.municipality_universe)}
                note="Municipal and township governments in scope"
              />
              <MetricCard
                label="Scout covered"
                value={formatNumber(totals.scout_covered_municipalities)}
                note={`${formatPercent(nationalCoverageRate)} of the national universe`}
              />
              <MetricCard
                label="Candidate rows"
                value={formatNumber(totals.candidate_rows)}
                note="Unverified source-discovery leads"
              />
              <MetricCard
                label="Failure-only"
                value={formatNumber(totals.failed_scout_municipalities)}
                note="Outside successful coverage; separate retry lane"
              />
            </div>

            <div className="hub-caveat" role="note">
              <strong>Source-discovery status only.</strong>
              <span>
                Candidate rows are unverified source leads. Municipality coverage is not verified-source coverage,
                scouting tiers are operational priorities, and no wage-gap or causal claim is displayed.
              </span>
            </div>

            <ProjectOrientation
              totals={totals}
              priorityTotals={prioritySummary.totals}
              report={currentReport}
            />
          </section>

          <section className="hub-section-group" id="geography" aria-label="Coverage map and state status">
            <div className="hub-section-intro">
              <p className="eyebrow">Coverage and geography</p>
              <h2>Explore state-level discovery progress</h2>
              <p>Use the map to compare operational coverage, queue volume, and readiness—not substantive outcomes.</p>
            </div>
            <div className="map-and-panel">
              <NationalMap states={stateSummary.states} selectedCode={selected.state} onSelect={chooseState} />
              <StateDetailPanel state={selected} queue={selectedQueue} onOpenReport={openReport} />
            </div>
          </section>

          <PriorityTiersPanel priority={prioritySummary} statePriority={statePrioritySummary} />

          <ScoutOperationsPanel operations={scoutOperations} runtime={scoutRuntimeTrends} />

          <section className="hub-section-group" id="candidate-queue" aria-labelledby="candidate-queue-title">
            <div className="hub-section-intro">
              <p className="eyebrow">Candidate queue</p>
              <h2 id="candidate-queue-title">Unverified leads awaiting coordinated review</h2>
              <p>
                The queue counts candidate rows, not municipalities or usable contracts. One municipality can contribute
                several possible documents, pages, duplicates, or context-only leads.
              </p>
            </div>
            <div className="two-column">
              <CoverageFunnel data={coverageFunnel} />
              <CandidateQueueCards data={candidateSummary} />
            </div>
            <QueueTable rows={candidateSummary.by_state} onSelect={chooseState} />
          </section>

          <VerificationPipeline candidateSummary={candidateSummary} readiness={analysisReadiness} />

          <StateYieldPanel yieldData={scoutYieldByState} operations={scoutOperations} />

          <ReportsLibrary reportsIndex={reportsIndex} reportAssets={REPORT_ASSETS} />

          <MethodologyDefinitions />

          <AnalysisReadinessPanel data={analysisReadiness} />

          <NextStepsPanel priority={prioritySummary} />

          <DataLimitations
            metadata={stateSummary.metadata}
            metricDefinition={stateSummary.metric_definition.evidence_readiness_score}
          />
        </main>

        <footer>
          <div>
            <p>Generated {stateSummary.metadata.generated_at}. Discovery data vintage {stateSummary.metadata.data_vintage}.</p>
            <p>Scout candidates are not yet verified, ingested, or claim-supporting evidence.</p>
          </div>
          <div className="footer-links">
            <button type="button" onClick={() => navigateToSection("overview")}>Back to overview</button>
            <a href={piProgressReportPdf} target="_blank" rel="noreferrer">
              PI Source-Discovery Progress Report PDF
            </a>
          </div>
        </footer>
      </div>
    </>
  );
}

export default App;
