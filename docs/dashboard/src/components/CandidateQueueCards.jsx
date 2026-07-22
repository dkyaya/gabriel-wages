import { formatNumber } from "./ui.jsx";

const PRIORITIES = [
  ["High priority", "high_priority_rows", "high"],
  ["Medium priority", "medium_priority_rows", "medium"],
  ["Low priority", "low_priority_rows", "low"],
  ["Hold / rejected", "hold_or_rejected_rows", "hold"],
];

export function CandidateQueueCards({ data }) {
  return (
    <article className="panel" aria-labelledby="queue-cards-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Candidate queue</p>
          <h2 id="queue-cards-title">Later-verification workload</h2>
        </div>
        <span className="quiet-label">{formatNumber(data.totals.candidate_rows)} total rows</span>
      </div>

      <div className="priority-grid">
        {PRIORITIES.map(([label, field, tone]) => (
          <div className={`priority-card priority-${tone}`} key={field}>
            <span>{label}</span>
            <strong>{formatNumber(data.totals[field])}</strong>
          </div>
        ))}
      </div>

      <div className="unit-composition" aria-label="Queue rows by unit type">
        <p className="eyebrow">Unit labels in scout metadata</p>
        <div>
          <span>Police <strong>{formatNumber(data.by_unit_type.police)}</strong></span>
          <span>Fire <strong>{formatNumber(data.by_unit_type.fire)}</strong></span>
          <span>Non-safety <strong>{formatNumber(data.by_unit_type.non_safety)}</strong></span>
          <span>Unclear <strong>{formatNumber(data.by_unit_type.unclear)}</strong></span>
        </div>
      </div>

      <details>
        <summary>Technical queue definitions</summary>
        <p>{data.interpretation}</p>
        <p>Scout confidence and queue priority are metadata used for workflow planning. Neither field verifies a source.</p>
      </details>
    </article>
  );
}
