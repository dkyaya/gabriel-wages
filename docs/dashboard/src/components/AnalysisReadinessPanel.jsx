import { formatNumber, humanize, StatusPill } from "./ui.jsx";

const STAGE_LABELS = {
  scout_stage: "Source discovery",
  verification_stage: "Source verification",
  ingestion_stage: "Ingestion",
  codified_stage: "Codified evidence",
  wage_extraction_stage: "Bounded evidence / text readiness",
  regression_stage: "Regression results",
};

export function AnalysisReadinessPanel({ data, phase }) {
  return (
    <section className="panel readiness-panel hub-section" id="descriptive-analysis" aria-labelledby="readiness-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Analysis boundary</p>
          <h2 id="readiness-title">Documentary evidence advanced; global analysis remains closed</h2>
        </div>
        <StatusPill tone="future">Global analysis readiness false</StatusPill>
      </div>

      <div className="stage-grid">
        {Object.entries(data.stage_availability).map(([key, stage]) => {
          const current = key === "wage_extraction_stage";
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
          <p className="eyebrow">Not yet available</p>
          <h3>Wage-growth gap analysis remains outside the current scope</h3>
        </div>
        <div>
          <ul>
            <li>The current memo reports bounded same-source co-location scaffolds only.</li>
            <li>The 463 retained Tier C sources have not been text-extracted or rated.</li>
            <li>No normalized wage comparison, descriptive wage gap, regression, or treatment effect is available.</li>
            <li>Final causal and national prevalence claims remain unavailable.</li>
          </ul>
          <p>{data.promotion_gate}</p>
        </div>
      </div>

      <p className="panel-note">
        The current operational next step is bounded PDF/text-layer readiness review over
        {" "}{formatNumber(phase.tier_c_retained_downloaded_source_count)} retained Tier C sources. Readiness is
        not extraction and will not make these files globally analysis-ready.
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
