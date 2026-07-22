import { formatNumber, formatPercent, StatusPill } from "./ui.jsx";

export function PrintableStateReport({ state, queue, metadata, limitations, onBack }) {
  return (
    <div className="report-shell">
      <nav className="report-actions no-print" aria-label="State report actions">
        <button onClick={onBack}>← Back to dashboard</button>
        <button className="primary-action" onClick={() => window.print()}>Print / save PDF</button>
      </nav>

      <article className="state-report">
        <header className="report-header">
          <div>
            <p className="eyebrow">Municipal labor evidence status brief</p>
            <h1>{state.state_name}</h1>
            <p>Discovery data vintage {metadata.data_vintage} · Generated {metadata.generated_at}</p>
          </div>
          <div className="report-status">
            <StatusPill tone={state.scout_coverage_count ? "scout" : "future"}>
              {state.scout_coverage_count ? "Scout stage" : "Not yet scouted"}
            </StatusPill>
            <StatusPill tone="future">Not yet verified</StatusPill>
            <StatusPill tone="future">Not yet ingested</StatusPill>
          </div>
        </header>

        <section className="report-metric-grid" aria-label="State headline metrics">
          <div><span>Municipality universe</span><strong>{formatNumber(state.municipality_universe)}</strong></div>
          <div><span>Scout covered</span><strong>{formatNumber(state.scout_coverage_count)}</strong></div>
          <div><span>Coverage rate</span><strong>{formatPercent(state.scout_coverage_rate)}</strong></div>
          <div><span>Candidate-positive</span><strong>{formatNumber(state.candidate_positive_count)}</strong></div>
        </section>

        <section className="report-section">
          <h2>Current status</h2>
          <p>{state.printable_report_data.narrative}</p>
          <p className="report-caveat"><strong>Status boundary:</strong> {state.printable_report_data.status_caveat}</p>
        </section>

        <section className="report-section">
          <h2>Candidate queue</h2>
          <table className="report-table">
            <thead><tr><th scope="col">Measure</th><th scope="col">Current count</th><th scope="col">Interpretation</th></tr></thead>
            <tbody>
              <tr><th scope="row">Candidate rows</th><td>{formatNumber(state.candidate_rows)}</td><td>Unverified scout leads</td></tr>
              <tr><th scope="row">High priority</th><td>{formatNumber(queue?.high_priority_rows ?? state.high_priority_queue_count)}</td><td>Later-verification scheduling</td></tr>
              <tr><th scope="row">Medium priority</th><td>{formatNumber(queue?.medium_priority_rows ?? state.medium_priority_queue_count)}</td><td>Later-verification scheduling</td></tr>
              <tr><th scope="row">Low priority</th><td>{formatNumber(queue?.low_priority_rows ?? state.low_priority_queue_count)}</td><td>Later-verification scheduling</td></tr>
              <tr><th scope="row">Hold or rejected</th><td>{formatNumber(queue?.hold_or_rejected_rows ?? state.hold_or_rejected_queue_count)}</td><td>Not in the later-verification schedule</td></tr>
              <tr><th scope="row">Likely matched-set groups</th><td>{formatNumber(state.likely_matched_set_count)}</td><td>Unit-label leads; employer, documents, and cycle overlap not yet checked</td></tr>
            </tbody>
          </table>
        </section>

        <section className="report-section report-two-column">
          <div>
            <h2>Coverage accounting</h2>
            <dl className="report-definition-list">
              <div><dt>Parseable empty outcomes</dt><dd>{formatNumber(state.no_candidate_count)}</dd></div>
              <div><dt>Failure-only municipalities</dt><dd>{formatNumber(state.failed_scout_municipality_count)}</dd></div>
              <div><dt>Failed attempts excluded</dt><dd>{formatNumber(state.failed_scout_attempt_count)}</dd></div>
              <div><dt>Prior claim-map cities</dt><dd>{formatNumber(state.claim_mapped_city_count)}</dd></div>
            </dl>
          </div>
          <div>
            <h2>Evidence stages</h2>
            <ul className="report-stage-list">
              <li><strong>Scout:</strong> {state.scout_coverage_count ? "current discovery output available" : "not started in current national coverage"}</li>
              <li><strong>Verification:</strong> not yet available project-wide</li>
              <li><strong>Ingestion:</strong> not yet available in dashboard data</li>
              <li><strong>Wage analysis:</strong> unavailable pending verified, extracted matched-cycle data</li>
            </ul>
          </div>
        </section>

        <section className="report-section report-limitations">
          <h2>Current limitations</h2>
          <ul>{limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
        </section>

        <footer className="report-footer">
          This state brief is a reproducible pipeline-status appendix. It is not a source-verification memorandum or a wage-gap result.
        </footer>
      </article>
    </div>
  );
}
