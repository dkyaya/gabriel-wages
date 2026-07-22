import { useEffect, useMemo, useState } from "react";
import stateSummary from "../data/state_summary.json";
import candidateSummary from "../data/candidate_queue_summary.json";
import coverageFunnel from "../data/coverage_funnel.json";
import analysisReadiness from "../data/analysis_readiness.json";
import { AnalysisReadinessPanel } from "./components/AnalysisReadinessPanel.jsx";
import { CandidateQueueCards } from "./components/CandidateQueueCards.jsx";
import { CoverageFunnel } from "./components/CoverageFunnel.jsx";
import { DataLimitations } from "./components/DataLimitations.jsx";
import { NationalMap } from "./components/NationalMap.jsx";
import { PrintableStateReport } from "./components/PrintableStateReport.jsx";
import { StateDetailPanel } from "./components/StateDetailPanel.jsx";
import { MetricCard, StatusPill, formatNumber, formatPercent } from "./components/ui.jsx";

const DEFAULT_STATE = "CA";

function routeFromHash() {
  const match = window.location.hash.match(/^#\/state\/([A-Z]{2})(\/report)?$/);
  return {
    state: match?.[1] ?? DEFAULT_STATE,
    view: match?.[2] ? "report" : "dashboard",
  };
}

function QueueTable({ rows, onSelect }) {
  return (
    <section className="panel queue-table-panel no-print" aria-labelledby="queue-table-title">
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

  function chooseState(code) {
    window.location.hash = `/state/${code}`;
    setRoute({ state: code, view: "dashboard" });
  }

  function openReport() {
    window.location.hash = `/state/${selected.state}/report`;
    setRoute({ state: selected.state, view: "report" });
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
    <div className="app-shell">
      <header className="site-header no-print">
        <div>
          <p className="eyebrow">HBS municipal labor evidence project</p>
          <h1>National evidence dashboard</h1>
          <p className="header-deck">
            A current view of source-discovery coverage, unverified leads, and readiness for the next evidence stage.
            This dashboard does not yet report wage gaps.
          </p>
        </div>
        <div className="header-status">
          <StatusPill tone="scout">Scout-stage MVP</StatusPill>
          <span>Data vintage {stateSummary.metadata.data_vintage}</span>
        </div>
      </header>

      <main>
        <section className="headline-grid" aria-label="National headline metrics">
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
            label="Likely matched-set groups"
            value={formatNumber(totals.likely_matched_set_groups)}
            note="Unit-label leads; cycles not yet checked"
          />
        </section>

        <section className="map-and-panel">
          <NationalMap states={stateSummary.states} selectedCode={selected.state} onSelect={chooseState} />
          <StateDetailPanel
            state={selected}
            queue={selectedQueue}
            onOpenReport={openReport}
          />
        </section>

        <section className="two-column">
          <CoverageFunnel data={coverageFunnel} />
          <CandidateQueueCards data={candidateSummary} />
        </section>

        <QueueTable rows={candidateSummary.by_state} onSelect={chooseState} />

        <AnalysisReadinessPanel data={analysisReadiness} />

        <DataLimitations
          metadata={stateSummary.metadata}
          metricDefinition={stateSummary.metric_definition.evidence_readiness_score}
        />
      </main>

      <footer>
        <p>Generated {stateSummary.metadata.generated_at}. Discovery data vintage {stateSummary.metadata.data_vintage}.</p>
        <p>Scout candidates are not yet verified, ingested, or claim-supporting evidence.</p>
      </footer>
    </div>
  );
}

export default App;
