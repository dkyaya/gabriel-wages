import { formatNumber, formatPercent, StageValue } from "./ui.jsx";

export function CoverageFunnel({ data }) {
  const universe = data.current_funnel[0]?.value ?? 0;

  return (
    <article className="panel" aria-labelledby="funnel-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Coverage funnel</p>
          <h2 id="funnel-title">From universe to likely sets</h2>
        </div>
      </div>

      <ol className="funnel-list">
        {data.current_funnel.map((stage, index) => (
          <li className="funnel-stage" key={stage.stage} style={{ width: `${100 - index * 7}%` }}>
            <div>
              <span>{stage.label}</span>
              <small>{index === 0 ? "Starting universe" : `${formatPercent((100 * stage.value) / universe)} of universe`}</small>
            </div>
            <strong>{formatNumber(stage.value)}</strong>
          </li>
        ))}
      </ol>

      <div className="failure-callout">
        <strong>{formatNumber(data.separate_failure_accounting.connection_failed_attempts_excluded_from_coverage)}</strong>
        <span>connection-failed attempts tracked outside the funnel</span>
      </div>

      <details>
        <summary>Future evidence stages</summary>
        <dl className="future-stage-list">
          {data.future_funnel.map((stage) => (
            <div key={stage.stage}><dt>{stage.label}</dt><dd><StageValue value={stage.value} /></dd></div>
          ))}
        </dl>
      </details>
    </article>
  );
}
