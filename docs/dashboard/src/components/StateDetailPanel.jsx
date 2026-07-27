import { formatNumber, formatPercent, StatusPill } from "./ui.jsx";

export function StateDetailPanel({ state, queue, onOpenReport }) {
  const hasCoverage = state.total_scout_coverage_count > 0;

  return (
    <aside className="panel state-panel" aria-live="polite" aria-labelledby="state-panel-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Selected state · total scout coverage</p>
          <h2 id="state-panel-title">{state.state_name}</h2>
        </div>
        <button className="report-button no-print" onClick={onOpenReport}>Open historical state report</button>
      </div>

      <div className="status-row">
        <StatusPill tone={hasCoverage ? "scout" : "future"}>
          {hasCoverage ? "Scout coverage recorded" : "No scout coverage recorded"}
        </StatusPill>
        <StatusPill tone="calibration">Readiness metadata only</StatusPill>
        <StatusPill tone="future">Not analysis-ready</StatusPill>
      </div>

      <div className="state-metrics">
        <div><span>Scout-covered</span><strong>{formatNumber(state.total_scout_coverage_count)}</strong></div>
        <div><span>Municipal universe</span><strong>{formatNumber(state.municipality_universe)}</strong></div>
        <div><span>Scout coverage rate</span><strong>{formatPercent(state.scout_coverage_rate)}</strong></div>
        <div><span>Candidate-positive</span><strong>{formatNumber(state.candidate_positive_count)}</strong></div>
      </div>

      <p className="state-narrative">These counts locate scout activity only; they do not establish national representativeness, wage differences, or causation.</p>
      <dl className="state-detail-list">
        <div><dt>Scout covered</dt><dd>{formatNumber(state.total_scout_coverage_count)}</dd></div>
        <div><dt>Candidate rows</dt><dd>{formatNumber(state.candidate_rows)}</dd></div>
        <div><dt>High-priority later review</dt><dd>{formatNumber(state.high_priority_queue_count)}</dd></div>
        <div><dt>Likely matched-set groups</dt><dd>{formatNumber(state.likely_matched_set_count)}</dd></div>
        <div><dt>Parseable empty outcomes</dt><dd>{formatNumber(state.no_candidate_count)}</dd></div>
        <div><dt>Failure-only municipalities</dt><dd>{formatNumber(state.failed_scout_municipality_count)}</dd></div>
      </dl>

      <details className="queue-mini-summary">
        <summary>Tier C and extraction detail for this state</summary>
        <p>{formatNumber(state.tier_c_retained_source_count)} retained Tier C sources; {formatNumber(state.tier_c_text_extraction_ready_count)} were readiness-approved. These operational details do not control the map.</p>
      </details>

      <div className="queue-mini-summary">
        <p className="eyebrow">Historical discovery queue</p>
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
