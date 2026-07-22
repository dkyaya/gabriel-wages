const numberFormatter = new Intl.NumberFormat("en-US");
const percentFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});

export function formatNumber(value) {
  return value === null || value === undefined ? "Not available" : numberFormatter.format(value);
}

export function formatPercent(value) {
  return value === null || value === undefined ? "Not available" : `${percentFormatter.format(value)}%`;
}

export function humanize(value) {
  return String(value ?? "not available")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function MetricCard({ label, value, note, compact = false }) {
  return (
    <article className={`metric-card${compact ? " metric-card-compact" : ""}`}>
      <p className="eyebrow">{label}</p>
      <p className="metric-value">{value}</p>
      {note ? <p className="metric-note">{note}</p> : null}
    </article>
  );
}

export function StatusPill({ tone = "future", children }) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}

export function StageValue({ value }) {
  return value === null || value === undefined ? (
    <span className="not-available">Not yet available</span>
  ) : (
    <strong>{formatNumber(value)}</strong>
  );
}
