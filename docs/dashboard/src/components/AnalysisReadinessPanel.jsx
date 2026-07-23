import { formatNumber, humanize, StatusPill } from "./ui.jsx";

const STAGE_LABELS = {
  scout_stage: "Source discovery",
  verification_stage: "Source verification",
  ingestion_stage: "Ingestion",
  codified_stage: "Codified evidence",
  wage_extraction_stage: "Wage extraction",
  regression_stage: "Regression results",
};

export function AnalysisReadinessPanel({ data, phase }) {
  return (
    <section className="panel readiness-panel hub-section" id="descriptive-analysis" aria-labelledby="readiness-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Future analysis capability</p>
          <h2 id="readiness-title">Descriptive Wage-Gap Analysis, Planned</h2>
        </div>
        <StatusPill tone="future">Available after verification and extraction</StatusPill>
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
          <p className="eyebrow">Planned dashboard capability</p>
          <h3>Wage-growth gap percentage</h3>
        </div>
        <div>
          <ul>
            <li>Calculate safety wage growth minus matched non-safety wage growth within comparable municipality/time windows.</li>
            <li>Add a map layer and filtering by wage-growth gap percentage.</li>
            <li>Document mechanisms correlated with higher or lower descriptive gaps.</li>
            <li>Keep regressions deferred until much later.</li>
          </ul>
          <p>{data.promotion_gate}</p>
        </div>
      </div>

      <p className="panel-note">
        No wage-growth gaps have been calculated and no mechanism relationship has been analyzed.
        This work begins only after the approximately {formatNumber(phase.checkpoint_target_scout_covered)}-covered
        checkpoint and validated source verification/extraction.
      </p>

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
