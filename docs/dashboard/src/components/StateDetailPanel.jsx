import { formatNumber, StatusPill } from "./ui.jsx";

export function StateDetailPanel({ state, queue, onOpenReport }) {
  const hasCoverage = state.tier_c_retained_source_count > 0;

  return (
    <aside className="panel state-panel" aria-live="polite" aria-labelledby="state-panel-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Selected state · current Tier C operations</p>
          <h2 id="state-panel-title">{state.state_name}</h2>
        </div>
        <button className="report-button no-print" onClick={onOpenReport}>Open historical state report</button>
      </div>

      <div className="status-row">
        <StatusPill tone={hasCoverage ? "scout" : "future"}>
          {hasCoverage ? "Tier C retained sources represented" : "No retained Tier C source"}
        </StatusPill>
        <StatusPill tone="calibration">Readiness metadata only</StatusPill>
        <StatusPill tone="future">Not analysis-ready</StatusPill>
      </div>

      <div className="state-metrics">
        <div><span>Tier C retained</span><strong>{formatNumber(state.tier_c_retained_source_count)}</strong></div>
        <div><span>Text-extraction ready</span><strong>{formatNumber(state.tier_c_text_extraction_ready_count)}</strong></div>
        <div><span>PDF / HTML</span><strong>{formatNumber(state.tier_c_pdf_count)} / {formatNumber(state.tier_c_html_count)}</strong></div>
        <div><span>Deferred / review</span><strong>{formatNumber(state.tier_c_deferred_or_review_count)}</strong></div>
      </div>

      <p className="state-narrative">These counts locate retained/readiness workflow coverage only; they do not establish representativeness, wage differences, or causation.</p>
      <dl className="state-detail-list">
        <div><dt>Region</dt><dd>{state.tier_c_region ?? "No current Tier C row"}</dd></div>
        <div><dt>Parse-text-layer later</dt><dd>{formatNumber(state.tier_c_parse_text_layer_later_count)}</dd></div>
        <div><dt>HTML-text later</dt><dd>{formatNumber(state.tier_c_html_text_later_count)}</dd></div>
        <div><dt>Historical scout covered</dt><dd>{formatNumber(state.scout_coverage_count)}</dd></div>
        <div><dt>Candidate rows</dt><dd>{formatNumber(state.candidate_rows)}</dd></div>
        <div><dt>High-priority later review</dt><dd>{formatNumber(state.high_priority_queue_count)}</dd></div>
        <div><dt>Likely matched-set groups</dt><dd>{formatNumber(state.likely_matched_set_count)}</dd></div>
        <div><dt>Parseable empty outcomes</dt><dd>{formatNumber(state.no_candidate_count)}</dd></div>
        <div><dt>Failure-only municipalities</dt><dd>{formatNumber(state.failed_scout_municipality_count)}</dd></div>
      </dl>

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
