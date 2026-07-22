import { formatNumber, humanize, StatusPill } from "./ui.jsx";

const STAGE_LABELS = {
  scout_stage: "Source discovery",
  verification_stage: "Source verification",
  ingestion_stage: "Ingestion",
  codified_stage: "Codified evidence",
  wage_extraction_stage: "Wage extraction",
  regression_stage: "Regression results",
};

export function AnalysisReadinessPanel({ data }) {
  return (
    <section className="panel readiness-panel" aria-labelledby="readiness-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Analysis readiness</p>
          <h2 id="readiness-title">What the current evidence supports</h2>
        </div>
        <StatusPill tone="scout">Discovery reporting ready</StatusPill>
      </div>

      <div className="stage-grid">
        {Object.entries(data.stage_availability).map(([key, stage]) => {
          const current = key === "scout_stage";
          const priorContext = key === "codified_stage" && stage.available;
          return (
            <article className={`stage-card ${current ? "stage-current" : "stage-future"}`} key={key}>
              <span>{STAGE_LABELS[key] ?? humanize(key)}</span>
              <StatusPill tone={current ? "scout" : priorContext ? "calibration" : "future"}>
                {current ? "Current" : priorContext ? "Prior context only" : "Not integrated"}
              </StatusPill>
            </article>
          );
        })}
      </div>

      <div className="readiness-columns">
        <div>
          <h3>Available now</h3>
          <ul>{data.analyses_available_now.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <h3>Not yet supported</h3>
          <ul>{data.analyses_not_yet_supported.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>

      <div className="regression-lock" role="note">
        <div>
          <p className="eyebrow">Wage-gap panel</p>
          <h3>Unavailable by design</h3>
        </div>
        <p>{data.promotion_gate}</p>
      </div>

      <details>
        <summary>Prior claim inventory context</summary>
        <p>
          The repository currently provides {formatNumber(data.claim_inventory_context.claim_count)} prior claim-register rows and {formatNumber(data.claim_inventory_context.state_city_claim_map_rows)} state-city mappings.
        </p>
        <p>{data.claim_inventory_context.caveat}</p>
      </details>
    </section>
  );
}
