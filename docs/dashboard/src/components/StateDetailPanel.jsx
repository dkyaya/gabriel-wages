import { formatNumber, formatPercent, StatusPill } from "./ui.jsx";

export function StateDetailPanel({ state, queue, onOpenReport }) {
  const hasCoverage = state.scout_coverage_count > 0;

  return (
    <aside className="panel state-panel" aria-live="polite" aria-labelledby="state-panel-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Selected state</p>
          <h2 id="state-panel-title">{state.state_name}</h2>
        </div>
        <button className="report-button no-print" onClick={onOpenReport}>Open report</button>
      </div>

      <div className="status-row">
        <StatusPill tone={hasCoverage ? "scout" : "future"}>
          {hasCoverage ? "Scout coverage recorded" : "Scout not started"}
        </StatusPill>
        <StatusPill tone="future">Not yet verified</StatusPill>
        <StatusPill tone="future">Not yet ingested</StatusPill>
      </div>

      <div className="state-metrics">
        <div><span>Municipal universe</span><strong>{formatNumber(state.municipality_universe)}</strong></div>
        <div><span>Scout covered</span><strong>{formatNumber(state.scout_coverage_count)}</strong></div>
        <div><span>Coverage rate</span><strong>{formatPercent(state.scout_coverage_rate)}</strong></div>
        <div><span>Candidate-positive</span><strong>{formatNumber(state.candidate_positive_count)}</strong></div>
      </div>

      <p className="state-narrative">{state.short_state_narrative}</p>
      <dl className="state-detail-list">
        <div><dt>Candidate rows</dt><dd>{formatNumber(state.candidate_rows)}</dd></div>
        <div><dt>High-priority later review</dt><dd>{formatNumber(state.high_priority_queue_count)}</dd></div>
        <div><dt>Likely matched-set groups</dt><dd>{formatNumber(state.likely_matched_set_count)}</dd></div>
        <div><dt>Parseable empty outcomes</dt><dd>{formatNumber(state.no_candidate_count)}</dd></div>
        <div><dt>Failure-only municipalities</dt><dd>{formatNumber(state.failed_scout_municipality_count)}</dd></div>
      </dl>

      <div className="queue-mini-summary">
        <p className="eyebrow">Queue composition</p>
        {queue ? (
          <p>
            {formatNumber(queue.high_priority_rows)} high, {formatNumber(queue.medium_priority_rows)} medium,
            {" "}{formatNumber(queue.low_priority_rows)} low, and {formatNumber(queue.hold_or_rejected_rows)} held or rejected rows.
          </p>
        ) : (
          <p>No candidate queue rows are recorded for this state.</p>
        )}
      </div>

      <div className="print-caveat">{state.printable_report_data.status_caveat}</div>
    </aside>
  );
}
