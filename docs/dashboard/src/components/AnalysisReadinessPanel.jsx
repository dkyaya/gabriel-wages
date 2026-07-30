import { formatNumber, humanize, StatusPill } from "./ui.jsx";

const STAGE_LABELS = {
  scout_stage: "Source discovery",
  verification_stage: "Source verification",
  ingestion_stage: "Ingestion",
  codified_stage: "Codified evidence",
  wage_extraction_stage: "Bounded evidence / Tier C memo supplement",
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
            <li>The parent memo and Tier C supplement report bounded documentary and same-source co-location scaffolds only.</li>
            <li>{formatNumber(phase.tier_c_text_extracted_ok_count)} Tier C text artifacts were processed into exact spans; {formatNumber(phase.tier_c_rating_summary_valid_count)} valid ratings were summarized and {formatNumber(phase.tier_c_rating_summary_quarantine_excluded_count)} quarantines remain excluded.</li>
            <li>No normalized wage comparison, descriptive wage gap, regression, or treatment effect is available.</li>
            <li>Wage-gap readiness remains blocked pending normalization.</li>
            <li>Causal readiness remains blocked pending matched structure.</li>
            <li>Final causal and national prevalence claims remain unavailable.</li>
          </ul>
          <p>{phase.broad_state_4x2500_text_extraction_available
            ? `The next authorized task is BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30 over exactly ${formatNumber(phase.broad_state_4x2500_text_extraction_span_ready_count)} extracted_ok sources in four staggered lanes. OCR and rating remain excluded.`
            : phase.broad_state_4x2500_pdf_text_readiness_available
            ? `The next authorized task is BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30 over exactly ${formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} readiness-approved files in four staggered lanes. OCR remains excluded.`
            : data.promotion_gate}</p>
        </div>
      </div>

      <p className="panel-note">
        {phase.broad_state_4x2500_text_extraction_available ? (
          <>The four-lane broad state scout, verification, source-review/download, readiness, and non-OCR text-extraction waves are complete. Extraction processed {formatNumber(phase.broad_state_4x2500_text_extraction_queue_count)} approved files and placed {formatNumber(phase.broad_state_4x2500_text_extraction_span_ready_count)} extracted_ok outputs in the next exact-span queue. Full text remains outside Git; no OCR, span extraction, rating, ingestion, codification, wage-gap analysis, or causal analysis occurred.</>
        ) : phase.broad_state_4x2500_pdf_text_readiness_available ? (
          <>The four-lane broad state scout, verification, source-review/download, and PDF/text-readiness waves are complete. Readiness classified {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_retained_count)} retained files and approved {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} for later non-OCR text extraction. No full text was persisted during readiness, and no OCR, rating, ingestion, codification, wage-gap analysis, or causal analysis occurred.</>
        ) : (
          <>The four-lane broad state scout and 5,768-row verification wave are complete. The current 4 × 2,500 source-review/download wave reviewed {formatNumber(phase.broad_state_4x2500_source_review_queue_count)} locators and retained {formatNumber(phase.broad_state_4x2500_source_review_retained_count)} unique hashed files in ignored local storage. PDF/text readiness is next; no text extraction, OCR, rating, ingestion, codification, wage-gap analysis, or causal analysis occurred.</>
        )}
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
