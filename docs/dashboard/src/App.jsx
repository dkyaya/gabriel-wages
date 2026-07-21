import { useMemo, useState } from "react";
import stateSummary from "../data/state_summary.json";
import candidateSummary from "../data/candidate_queue_summary.json";
import coverageFunnel from "../data/coverage_funnel.json";
import analysisReadiness from "../data/analysis_readiness.json";

const formatNumber = new Intl.NumberFormat("en-US");

function stateFromHash() {
  const match = window.location.hash.match(/^#\/state\/([A-Z]{2})/);
  return match?.[1] ?? "CA";
}

function scoreBand(score) {
  if (score >= 75) return "score-strong";
  if (score >= 45) return "score-growing";
  if (score > 0) return "score-early";
  return "score-none";
}

function MetricCard({ label, value, note }) {
  return (
    <article className="metric-card">
      <p className="eyebrow">{label}</p>
      <p className="metric-value">{value}</p>
      {note ? <p className="metric-note">{note}</p> : null}
    </article>
  );
}

function StatusPill({ tone, children }) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}

function App() {
  const [selectedCode, setSelectedCode] = useState(stateFromHash);
  const selected = useMemo(
    () =>
      stateSummary.states.find((item) => item.state === selectedCode) ??
      stateSummary.states[0],
    [selectedCode],
  );
  const selectedQueue = candidateSummary.by_state.find(
    (item) => item.state === selected.state,
  );

  function chooseState(code) {
    setSelectedCode(code);
    window.location.hash = `/state/${code}`;
  }

  const totals = stateSummary.totals;

  return (
    <div className="app-shell">
      <header className="site-header no-print">
        <div>
          <p className="eyebrow">HBS municipal labor evidence project</p>
          <h1>National evidence dashboard</h1>
          <p className="header-deck">
            Source-discovery coverage, candidate leads, and analysis readiness.
            Wage-gap results are not yet available.
          </p>
        </div>
        <div className="header-status">
          <StatusPill tone="scout">Scout data current</StatusPill>
          <span>Vintage {stateSummary.metadata.data_vintage}</span>
        </div>
      </header>

      <main>
        <section className="headline-grid" aria-label="National headline metrics">
          <MetricCard
            label="Municipal universe"
            value={formatNumber.format(totals.municipality_universe)}
            note="Census municipal and township governments"
          />
          <MetricCard
            label="Scout covered"
            value={formatNumber.format(totals.scout_covered_municipalities)}
            note="Parseable candidate or empty outcomes"
          />
          <MetricCard
            label="Candidate rows"
            value={formatNumber.format(totals.candidate_rows)}
            note="Unverified source leads"
          />
          <MetricCard
            label="Likely matched sets"
            value={formatNumber.format(totals.likely_matched_set_groups)}
            note="Scheduling leads; cycles not verified"
          />
        </section>

        <section className="map-and-panel">
          <article className="panel map-panel no-print">
            <div className="section-heading">
              <div>
                <p className="eyebrow">National map</p>
                <h2>Discovery readiness by state</h2>
              </div>
              <span className="quiet-label">Operational score, not evidence strength</span>
            </div>
            <div className="map-placeholder" role="img" aria-label="State discovery-readiness grid">
              {stateSummary.states.map((state) => (
                <button
                  className={`state-cell ${scoreBand(state.evidence_readiness_score)} ${
                    state.state === selected.state ? "selected" : ""
                  }`}
                  key={state.state}
                  onClick={() => chooseState(state.state)}
                  title={`${state.state_name}: ${state.scout_coverage_count} scout covered; readiness score ${state.evidence_readiness_score}`}
                >
                  <span>{state.state}</span>
                  <small>{state.scout_coverage_count}</small>
                </button>
              ))}
            </div>
            <p className="panel-note">
              This first scaffold uses an accessible state grid. A token-free Leaflet
              choropleth will replace it after a simplified public-domain state GeoJSON
              is selected and documented.
            </p>
          </article>

          <aside className="panel state-panel" aria-live="polite">
            <div className="section-heading">
              <div>
                <p className="eyebrow">State brief</p>
                <h2>{selected.state_name}</h2>
              </div>
              <button className="print-button no-print" onClick={() => window.print()}>
                Print state brief
              </button>
            </div>
            <div className="status-row">
              <StatusPill tone="scout">Scout</StatusPill>
              <StatusPill tone="future">Verification pending</StatusPill>
              <StatusPill tone="future">Wage analysis unavailable</StatusPill>
            </div>
            <div className="state-metrics">
              <div><span>Universe</span><strong>{formatNumber.format(selected.municipality_universe)}</strong></div>
              <div><span>Scout covered</span><strong>{formatNumber.format(selected.scout_coverage_count)}</strong></div>
              <div><span>Candidate positive</span><strong>{formatNumber.format(selected.candidate_positive_count)}</strong></div>
              <div><span>Likely matched sets</span><strong>{formatNumber.format(selected.likely_matched_set_count)}</strong></div>
            </div>
            <p className="state-narrative">{selected.short_state_narrative}</p>
            <dl className="state-detail-list">
              <div><dt>High-priority leads</dt><dd>{formatNumber.format(selected.high_priority_queue_count)}</dd></div>
              <div><dt>Parseable empty outcomes</dt><dd>{formatNumber.format(selected.no_candidate_count)}</dd></div>
              <div><dt>Failure-only municipalities</dt><dd>{formatNumber.format(selected.failed_scout_municipality_count)}</dd></div>
              <div><dt>Readiness score</dt><dd>{selected.evidence_readiness_score}/100</dd></div>
            </dl>
            {selectedQueue ? (
              <p className="panel-note">
                Queue: {selectedQueue.high_priority_rows} high, {selectedQueue.medium_priority_rows} medium,
                {" "}{selectedQueue.low_priority_rows} low, and {selectedQueue.hold_or_rejected_rows} held/rejected rows.
              </p>
            ) : (
              <p className="panel-note">No national candidate queue rows are recorded for this state.</p>
            )}
            <div className="print-caveat">
              {selected.printable_report_data.status_caveat}
            </div>
          </aside>
        </section>

        <section className="two-column">
          <article className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Coverage funnel</p>
                <h2>From universe to matched-set leads</h2>
              </div>
            </div>
            <div className="funnel-list">
              {coverageFunnel.current_funnel.map((stage, index) => {
                const max = coverageFunnel.current_funnel[0].value;
                const visualWidth = index === 0 ? 100 : Math.max(12, (stage.value / max) * 100);
                return (
                  <div className="funnel-stage" key={stage.stage}>
                    <div className="funnel-label"><span>{stage.label}</span><strong>{formatNumber.format(stage.value)}</strong></div>
                    <div className="funnel-track"><div style={{ width: `${visualWidth}%` }} /></div>
                  </div>
                );
              })}
            </div>
            <p className="panel-note">
              {coverageFunnel.separate_failure_accounting.connection_failed_attempts_excluded_from_coverage} connection-failed attempts are tracked separately and excluded from coverage.
            </p>
          </article>

          <article className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Candidate queue</p>
                <h2>Later-verification workload</h2>
              </div>
            </div>
            <div className="priority-stack">
              <div className="priority high"><span>High priority</span><strong>{candidateSummary.totals.high_priority_rows}</strong></div>
              <div className="priority medium"><span>Medium priority</span><strong>{candidateSummary.totals.medium_priority_rows}</strong></div>
              <div className="priority low"><span>Low priority</span><strong>{candidateSummary.totals.low_priority_rows}</strong></div>
              <div className="priority hold"><span>Hold / rejected</span><strong>{candidateSummary.totals.hold_or_rejected_rows}</strong></div>
            </div>
            <details>
              <summary>Technical queue definitions</summary>
              <p>{candidateSummary.interpretation}</p>
            </details>
          </article>
        </section>

        <section className="panel queue-table-panel no-print">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Queue explorer</p>
              <h2>State workload overview</h2>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>State</th><th>Rows</th><th>Municipalities</th><th>High</th><th>Likely sets</th></tr></thead>
              <tbody>
                {candidateSummary.by_state.map((state) => (
                  <tr key={state.state} onClick={() => chooseState(state.state)}>
                    <th>{state.state_name}</th>
                    <td>{state.candidate_rows}</td>
                    <td>{state.municipalities_with_queue_rows}</td>
                    <td>{state.high_priority_rows}</td>
                    <td>{state.likely_matched_set_municipalities}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="two-column">
          <article className="panel">
            <p className="eyebrow">Claims and evidence</p>
            <h2>Prior structured claim context</h2>
            <p>
              The repository currently exposes {analysisReadiness.claim_inventory_context.claim_count} claim-register rows and {analysisReadiness.claim_inventory_context.state_city_claim_map_rows} state-city mappings. New scout leads remain source needs until verified.
            </p>
            <div className="status-row">
              <StatusPill tone="calibration">Prior claim context</StatusPill>
              <StatusPill tone="scout">National scout leads</StatusPill>
            </div>
            <details>
              <summary>Why these are separate</summary>
              <p>{analysisReadiness.claim_inventory_context.caveat}</p>
            </details>
          </article>

          <article className="panel regression-locked">
            <p className="eyebrow">Later analysis</p>
            <h2>Wage-gap regressions</h2>
            <p>
              Not available. A validated matched city × cycle × bargaining-unit wage table is required before this panel can show estimates.
            </p>
            <StatusPill tone="future">Future input required</StatusPill>
          </article>
        </section>
      </main>

      <footer>
        <p>Generated {stateSummary.metadata.generated_at}. Discovery data vintage {stateSummary.metadata.data_vintage}.</p>
        <p>Scout candidates are unverified and are not claim-supporting evidence.</p>
      </footer>
    </div>
  );
}

export default App;
