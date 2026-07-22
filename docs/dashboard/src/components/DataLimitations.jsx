import { StatusPill } from "./ui.jsx";

export function DataLimitations({ metadata, metricDefinition }) {
  return (
    <section className="panel limitations-panel" aria-labelledby="limitations-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">How to read this dashboard</p>
          <h2 id="limitations-title">Status legend and limitations</h2>
        </div>
      </div>

      <div className="status-legend">
        <div><StatusPill tone="scout">Scout</StatusPill><span>Parseable discovery output; leads remain unverified.</span></div>
        <div><StatusPill tone="calibration">Calibration</StatusPill><span>Bounded prior review; not project-wide verification.</span></div>
        <div><StatusPill tone="verified">Verified</StatusPill><span>Reserved for a future dedicated verification ledger.</span></div>
        <div><StatusPill tone="ingested">Ingested</StatusPill><span>Reserved for sources that pass canonical provenance gates.</span></div>
        <div><StatusPill tone="future">Unavailable</StatusPill><span>No validated dashboard input exists for this stage.</span></div>
        <div><StatusPill tone="failure">Failed attempt</StatusPill><span>Infrastructure outcome tracked outside scout coverage.</span></div>
      </div>

      <ul className="limitation-list">
        {metadata.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
      </ul>

      <details>
        <summary>Technical data status</summary>
        <p><strong>Schema:</strong> {metadata.schema_version} · <strong>Generated:</strong> {metadata.generated_at} · <strong>Vintage:</strong> {metadata.data_vintage}</p>
        <p><strong>Operational readiness score:</strong> {metricDefinition}</p>
        <p><strong>Generated from:</strong></p>
        <ul>{metadata.source_files.map((source) => <li key={source}><code>{source}</code></li>)}</ul>
        {metadata.warnings.length ? (
          <><p><strong>Build warnings:</strong></p><ul>{metadata.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></>
        ) : <p><strong>Build warnings:</strong> none.</p>}
      </details>
    </section>
  );
}
