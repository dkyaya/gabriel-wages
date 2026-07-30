import { formatNumber, formatPercent, StatusPill } from "./ui.jsx";

function duration(seconds) {
  if (seconds === null || seconds === undefined) return "Not available";
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remainder = total % 60;
  return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(remainder).padStart(2, "0")}s`;
}

function decimal(value, digits = 1) {
  return value === null || value === undefined ? "Not available" : Number(value).toFixed(digits);
}

export function ProjectOrientation({ totals, priorityTotals, report, phase }) {
  const latestReadiness = phase.broad_state_4x2500_pdf_text_readiness_available;
  const latestSourceReview = phase.broad_state_4x2500_source_review_download_available;
  return (
    <section className="project-orientation" aria-label="Collected current and forthcoming project status">
      <article>
        <p className="eyebrow">Current operation</p>
        <h2>{latestReadiness ? "Broad state 4 × 2,500 PDF/text readiness complete" : latestSourceReview ? "Broad state 4 × 2,500 source review/download complete" : phase.combined_pdf_text_readiness_available ? "Combined broad PDF/text-layer readiness complete" : phase.combined_source_review_download_available ? "Combined broad source review/download complete" : "Combined broad candidate review complete"}</h2>
        {latestReadiness ? (
          <p>
            All {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_retained_count)} retained files received one
            technical-readiness status; {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} are approved for later non-OCR extraction.
          </p>
        ) : latestSourceReview ? (
          <p>
            All {formatNumber(phase.broad_state_4x2500_source_review_queue_count)} locked locators reached a terminal
            outcome; {formatNumber(phase.broad_state_4x2500_source_review_retained_count)} unique source files were retained and hashed outside Git.
          </p>
        ) : phase.combined_pdf_text_readiness_available ? (
          <p>
            All {formatNumber(phase.pdf_text_readiness_reviewed_count)} retained sources were reviewed across four
            staggered lanes; {formatNumber(phase.pdf_text_readiness_extraction_ready_count)} are technically approved
            for a later bounded text pass.
          </p>
        ) : phase.combined_source_review_download_available ? (
          <p>
            All {formatNumber(phase.source_review_download_attempted_count)} locked rows were processed in four
            lanes; {formatNumber(phase.source_review_download_retained_count)} unique source files were retained and hashed.
          </p>
        ) : (
          <p>
            {formatNumber(phase.candidate_review_universe_size)} local metadata rows were reviewed; a locked
            queue of {formatNumber(phase.source_review_ready_count)} candidates is ready for separately authorized source review.
          </p>
        )}
      </article>
      <article>
        <p className="eyebrow">Current evidence memo</p>
        <h2>Bounded Tier C evidence memo supplement</h2>
        <p>
          The bounded memo covers {formatNumber(phase.memo_scope.exact_same_source_linked_pair_count)} exact
          same-source pairs, {formatNumber(phase.memo_scope.linked_quantitative_row_count)} quantitative rows,
          and {formatNumber(phase.memo_scope.linked_qualitative_record_count)} qualitative records.
        </p>
      </article>
      <article>
        <p className="eyebrow">Next authorized stage</p>
        <h2>{phase.next_phase}</h2>
        <p>{latestReadiness
          ? "Use only the exact readiness-approved queue in four isolated text-extraction lanes; extracted text must remain outside Git, and OCR, rating, ingestion, codification, and analysis remain out of scope."
          : latestSourceReview
          ? "Use only this wave’s unique hashed retained local files in four PDF/text-readiness lanes; do not redownload, extract text, OCR, rate, ingest, codify, or treat retention as evidence."
          : phase.combined_pdf_text_readiness_available
          ? "Use only readiness-approved manifests in four isolated text-extraction lanes; do not admit deferred rows or treat extracted text as rated, ingested, causal, or globally analysis-ready."
          : phase.combined_source_review_download_available
          ? "Use only hashed retained local files in a separately authorized PDF/text-layer readiness pass; do not redownload or treat retention as evidence."
          : "Use only the locked reviewed queue in a separately authorized bounded source-review/download wave. Candidate review itself did not download, inspect, extract, rate, or ingest documents."}</p>
      </article>
    </section>
  );
}

export function ProjectPhasePanel({ phase }) {
  const progress = Math.min(100, Math.max(0, phase.progress_percentage));
  const latestReadiness = phase.broad_state_4x2500_pdf_text_readiness_available;
  const latestSourceReview = phase.broad_state_4x2500_source_review_download_available;
  return (
    <section className="panel hub-section phase-panel" id="project-phase" aria-labelledby="project-phase-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Project phase</p>
          <h2 id="project-phase-title">{phase.current_phase}</h2>
        </div>
        <StatusPill tone="verified">
          {latestReadiness
            ? `${formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} extraction-ready`
            : latestSourceReview
            ? `${formatNumber(phase.broad_state_4x2500_source_review_retained_count)} retained sources`
            : phase.combined_pdf_text_readiness_available
            ? `${formatNumber(phase.pdf_text_readiness_reviewed_count)} readiness-reviewed`
            : phase.combined_source_review_download_available
            ? `${formatNumber(phase.source_review_download_retained_count)} retained sources`
            : `${formatNumber(phase.source_review_ready_count)} source-review-ready`}
        </StatusPill>
      </div>

      <div className="phase-progress" aria-label="Historical scout-coverage checkpoint reached">
        <div className="phase-progress-label">
          <strong>Historical discovery checkpoint complete</strong>
          <span>{formatNumber(phase.current_scout_covered)} scout-covered; preserved as provenance rather than current-stage evidence</span>
        </div>
        <div className="phase-progress-track" aria-hidden="true">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="phase-metrics">
        {latestReadiness && <div><span>Current readiness reviewed / extraction-ready</span><strong>{formatNumber(phase.broad_state_4x2500_pdf_text_readiness_retained_count)} / {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)}</strong></div>}
        {latestReadiness && <div><span>Ready PDF / HTML / other</span><strong>{formatNumber(phase.broad_state_4x2500_pdf_text_readiness_parse_pdf_ready_count)} / {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_html_ready_count)} / {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_other_ready_count)}</strong></div>}
        {latestReadiness && <div><span>OCR later / oversized / locked</span><strong>{formatNumber(phase.broad_state_4x2500_pdf_text_readiness_ocr_later_count)} / {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_oversized_count)} / {formatNumber(phase.broad_state_4x2500_pdf_text_readiness_locked_count)}</strong></div>}
        {latestSourceReview && <div><span>Current source-review queue</span><strong>{formatNumber(phase.broad_state_4x2500_source_review_queue_count)}</strong></div>}
        {latestSourceReview && <div><span>Current retained PDF / HTML / other</span><strong>{formatNumber(phase.broad_state_4x2500_source_review_retained_pdf_count)} / {formatNumber(phase.broad_state_4x2500_source_review_retained_html_count)} / {formatNumber(phase.broad_state_4x2500_source_review_retained_other_count)}</strong></div>}
        <div><span>Scout-covered municipalities</span><strong>{formatNumber(phase.current_scout_covered)}</strong></div>
        <div><span>Total candidate rows</span><strong>{formatNumber(phase.current_candidate_queue_rows)}</strong></div>
        <div><span>Verification queue</span><strong>{formatNumber(phase.verification_queue_size)}</strong></div>
        <div><span>Completed outcomes</span><strong>{formatNumber(phase.verification_completed_count)}</strong></div>
        <div><span>Reachable locators</span><strong>{formatNumber(phase.verification_verified_reachable_count)}</strong></div>
        <div><span>Candidate review universe</span><strong>{formatNumber(phase.candidate_review_universe_size)}</strong></div>
        <div><span>Source-review ready</span><strong>{formatNumber(phase.source_review_ready_count)}</strong></div>
        <div><span>High / medium / low ready</span><strong>{formatNumber(phase.source_review_ready_high_count)} / {formatNumber(phase.source_review_ready_medium_count)} / {formatNumber(phase.source_review_ready_low_count)}</strong></div>
        <div><span>Source-review/download attempted</span><strong>{formatNumber(phase.source_review_download_attempted_count)}</strong></div>
        <div><span>Retained sources</span><strong>{formatNumber(phase.source_review_download_retained_count)}</strong></div>
        <div><span>Retained PDF / HTML / other</span><strong>{formatNumber(phase.source_review_download_retained_pdf_count)} / {formatNumber(phase.source_review_download_retained_html_count)} / {formatNumber(phase.source_review_download_retained_other_count)}</strong></div>
        <div><span>PDF/text readiness queue / reviewed</span><strong>{formatNumber(phase.pdf_text_readiness_queue_size)} / {formatNumber(phase.pdf_text_readiness_reviewed_count)}</strong></div>
        <div><span>Parse-layer / HTML / other ready</span><strong>{formatNumber(phase.pdf_text_readiness_parse_text_layer_ready_count)} / {formatNumber(phase.pdf_text_readiness_html_text_ready_count)} / {formatNumber(phase.pdf_text_readiness_other_document_text_ready_count)}</strong></div>
        <div><span>OCR-later / oversized defer</span><strong>{formatNumber(phase.pdf_text_readiness_ocr_later_defer_count)} / {formatNumber(phase.pdf_text_readiness_oversized_defer_count)}</strong></div>
        <div><span>Corrupt / locked / shell</span><strong>{formatNumber(phase.pdf_text_readiness_corrupt_unreadable_count)} / {formatNumber(phase.pdf_text_readiness_encrypted_locked_count)} / {formatNumber(phase.pdf_text_readiness_shell_navigation_count)}</strong></div>
        <div><span>Unsupported / needs review / errors</span><strong>{formatNumber(phase.pdf_text_readiness_unsupported_count)} / {formatNumber(phase.pdf_text_readiness_needs_review_count)} / {formatNumber(phase.pdf_text_readiness_error_count)}</strong></div>
        <div><span>Excluded / deferred source review</span><strong>{formatNumber(phase.source_review_download_excluded_deferred_count)}</strong></div>
        <div><span>Oversized / duplicate hashes</span><strong>{formatNumber(phase.source_review_download_oversized_count)} / {formatNumber(phase.source_review_download_duplicate_file_hash_count)}</strong></div>
        <div><span>Blocked / unavailable downloads</span><strong>{formatNumber(phase.source_review_download_blocked_unavailable_count)}</strong></div>
        <div><span>Unavailable</span><strong>{formatNumber(phase.verification_unavailable_count)}</strong></div>
        <div><span>Blocked / timeout</span><strong>{formatNumber(phase.verification_blocked_timeout_count)}</strong></div>
        <div><span>Deferred unavailable / blocked</span><strong>{formatNumber(phase.candidate_review_deferred_unavailable_count)} / {formatNumber(phase.candidate_review_deferred_blocked_timeout_count)}</strong></div>
        <div><span>Excluded / duplicate / out-of-scope</span><strong>{formatNumber(phase.candidate_review_excluded_count)}</strong></div>
        <div><span>Map data date</span><strong>{phase.map_data_date}</strong></div>
        <div><span>Wage-gap estimates</span><strong>None</strong></div>
        <div><span>Global readiness</span><strong>False</strong></div>
      </div>

      <div className="phase-next">
        <div>
          <p className="eyebrow">Current transition</p>
          <h3>{phase.next_phase}</h3>
        </div>
        {latestSourceReview ? (
          <ol>
            <li>Lock only the {formatNumber(phase.broad_state_4x2500_source_review_retained_count)} unique hashed retained files from this wave</li>
            <li>Use four independent PDF/text-readiness lanes with T+0/T+8/T+16/T+24 starts</li>
            <li>Classify PDF, HTML, and other-document readiness without extracting full text or running OCR</li>
            <li>Keep rating, ingestion, codification, wage analysis, and causal claims out of scope</li>
          </ol>
        ) : phase.combined_pdf_text_readiness_available ? (
          <ol>
            <li>Lock only parse-layer, HTML-text, and other-document-text approved identities</li>
            <li>Use four isolated extraction workers with T+0/T+8/T+16/T+24 starts</li>
            <li>Keep OCR/defer, oversized, corrupt, locked, shell, unsupported, review, and error rows excluded</li>
            <li>Keep extraction separate from rating, ingestion, codification, wage analysis, and causal claims</li>
          </ol>
        ) : phase.combined_source_review_download_available ? (
          <ol>
            <li>Use only the unique retained files and verify path, size, and SHA-256 lineage</li>
            <li>Separate PDF text-layer readiness from HTML/document handling</li>
            <li>Do not access URLs, redownload, OCR, render, extract evidence, or rate without authorization</li>
            <li>Keep every retained file non-causal and outside global analysis readiness</li>
          </ol>
        ) : (
          <ol>
            <li>Use only the locked {formatNumber(phase.source_review_ready_count)}-row reviewed queue</li>
            <li>Start with {formatNumber(phase.source_review_ready_high_count)} high-priority metadata leads</li>
            <li>Preserve geographic and non-CBA source-family diversity</li>
            <li>Keep downloading and source review separately authorized and bounded</li>
            <li>Do not treat a reviewed locator as retained, extracted, rated, or analysis-ready evidence</li>
          </ol>
        )}
        <StatusPill tone="future">{phase.combined_pdf_text_readiness_available ? "Four-lane bounded text extraction next" : phase.combined_source_review_download_available ? "PDF/text-layer readiness next" : "Source review/download next"}</StatusPill>
      </div>
      <p className="panel-note">
        Exact-span rating is not causal proof. The ratings and bounded memo remain documentary scaffolding only;
        global analysis readiness, wage-gap estimates, and final causal claims remain false.
      </p>
    </section>
  );
}

export function PriorityTiersPanel({ priority, statePriority }) {
  const totals = priority.totals;
  const tierCounts = [
    totals.tier_1_eligible,
    totals.tier_2_eligible,
    totals.tier_3_eligible,
    totals.tier_4_eligible,
    totals.tier_5_eligible,
  ];
  const leadingStates = [...statePriority.states]
    .sort((a, b) => b.tier_1_plus_2_remaining - a.tier_1_plus_2_remaining || a.state.localeCompare(b.state))
    .slice(0, 8);

  return (
    <section className="panel hub-section" id="priorities" aria-labelledby="priority-tier-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Historical scouting priority tiers</p>
          <h2 id="priority-tier-title">Archived discovery scheduling context</h2>
        </div>
        <StatusPill tone="calibration">Historical operational heuristic</StatusPill>
      </div>

      <div className="priority-summary-strip">
        <div><span>Future eligible</span><strong>{formatNumber(totals.future_scout_eligible)}</strong></div>
        <div><span>Tier 1 + 2</span><strong>{formatNumber(totals.tier_1_eligible + totals.tier_2_eligible)}</strong></div>
        <div><span>Failure retry lane</span><strong>{formatNumber(totals.failure_only_retry_targets)}</strong></div>
        <div><span>Priority checkpoint</span><strong>794 covered</strong></div>
      </div>

      <div className="tier-grid">
        {priority.tier_definitions.map((tier, index) => (
          <article className={`tier-card tier-${index + 1}`} key={tier.tier}>
            <span>{tier.tier}</span>
            <strong>{formatNumber(tierCounts[index])}</strong>
            <p>{tier.label}</p>
          </article>
        ))}
      </div>

      <div className="hub-split">
        <div>
          <h3>Largest Tier 1 + Tier 2 pools</h3>
          <div className="compact-table-wrap table-wrap">
            <table>
              <thead><tr><th scope="col">State</th><th scope="col">Tier 1</th><th scope="col">Tier 2</th><th scope="col">Confidence</th></tr></thead>
              <tbody>
                {leadingStates.map((state) => (
                  <tr key={state.state}>
                    <th scope="row">{state.state_name}</th>
                    <td>{formatNumber(state.tier_1_eligible)}</td>
                    <td>{formatNumber(state.tier_2_eligible)}</td>
                    <td><span className={`confidence-badge confidence-${state.state_score_confidence}`}>{state.state_score_confidence}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <aside className="interpretation-note">
          <p className="eyebrow">How to interpret tiers</p>
          <p>{priority.disclaimer}</p>
          <p>
            Scores combine employer scale, government type, smoothed state yield, research-design relevance,
            geography, and data completeness. They schedule work; they do not classify unionization or evidence quality.
          </p>
        </aside>
      </div>
    </section>
  );
}

export function ScoutOperationsPanel({ operations, runtime, parallelStatus }) {
  const latest = operations.latest_wave;
  const maxRowsPerHour = Math.max(...runtime.waves.map((wave) => wave.rows_per_hour ?? 0), 1);

  return (
    <section className="panel hub-section" id="operations" aria-labelledby="operations-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Historical scout operations</p>
          <h2 id="operations-title">Archived discovery-wave performance</h2>
        </div>
        <StatusPill tone="calibration">Historical context</StatusPill>
      </div>

      <div className="operations-metrics">
        <div><span>Latest runtime</span><strong>{duration(latest.runtime_seconds)}</strong></div>
        <div><span>Rows per hour</span><strong>{decimal(latest.rows_per_hour, 1)}</strong></div>
        <div><span>Candidate rows/hour</span><strong>{decimal(latest.candidate_rows_per_hour, 1)}</strong></div>
        <div><span>Rows per parseable</span><strong>{decimal(latest.candidate_rows_per_parseable_municipality, 3)}</strong></div>
        <div><span>Failure-only rows</span><strong>{formatNumber(latest.timeout_or_failure_rows)}</strong></div>
      </div>

      <div className="hub-split operations-layout">
        <div>
          <h3>{runtime.waves.length}-round runtime trend</h3>
          <div className="runtime-list">
            {runtime.waves.map((wave) => (
              <article key={wave.wave_id}>
                <div className="runtime-label">
                  <span>{wave.label}</span>
                  <strong>{decimal(wave.rows_per_hour, 1)} rows/hr</strong>
                </div>
                <div className="runtime-track" aria-hidden="true">
                  <span style={{ width: `${Math.max(4, (100 * wave.rows_per_hour) / maxRowsPerHour)}%` }} />
                </div>
                <small>
                  {formatNumber(wave.parseable_rows)}/{formatNumber(wave.attempted_rows)} parseable ·
                  {" "}{formatNumber(wave.candidate_rows)} parsed candidates · {duration(wave.runtime_seconds)}
                </small>
              </article>
            ))}
          </div>
        </div>
        <div>
          <h3>Current operating controls</h3>
          <ul className="check-list">
            <li>The three-lane 3 × 300 Attempt 3 completed with isolated lane outputs and was merged serially.</li>
            <li>Stronger no-search, hosted-search, and one-row preflight gate.</li>
            <li>Compact prompts with exact identity and source-stage guardrails.</li>
            <li>Five deterministic municipality-specific query hints.</li>
            <li>Adaptive sleep/backoff, outer timeout, terminal artifacts, and fresh-directory resume lineage.</li>
          </ul>
          <p className="panel-note">
            <strong>Parallel scout lane status:</strong>{" "}
            Attempt 3 completed and merged {parallelStatus.latest_round.lanes_completed_merge_eligible} lanes ×
            {" "}300 municipalities. Its {formatNumber(parallelStatus.latest_round.parseable_rows)} parseable outcomes
            raised official scout coverage above the approximately 2,000-covered checkpoint. Broad scouting is now
            paused; the earlier 3 × 160 plan remains superseded planning history. Accounting remained serial after
            the combined lane audit, and candidate exports remained lane-local.{" "}
            {parallelStatus.caveat}
          </p>
          <p className="panel-note">{operations.disclaimer}</p>
        </div>
      </div>
    </section>
  );
}

export function VerificationPipeline({
  candidateSummary,
  readiness,
  phase,
  verificationStatus,
  contentTriageStatus,
  sourceReviewStatus,
  pdfReadinessStatus,
  textTableDetectionStatus,
  textTableCalibrationStatus,
}) {
  const candidateRows = candidateSummary.totals.candidate_rows;
  const fullRouting =
    verificationStatus.verification_phase === "full_url_routing_merged";
  const routingMerged =
    fullRouting || verificationStatus.verification_phase === "round1_3x750_merged";
  const round2Collected =
    verificationStatus.live_verification_status ===
    "round2_3x1000_remainder_collected_not_merged";
  const stages = [
    ["Broad scout candidate rows", formatNumber(phase.current_candidate_queue_rows), "Discovery complete", "scout"],
    ["Locked verification locators", formatNumber(phase.verification_queue_size), "Four lanes", "verified"],
    ["Completed verification outcomes", formatNumber(phase.verification_completed_count), "HEAD-only", "verified"],
    ["Reachable locators", formatNumber(phase.verification_verified_reachable_count), "Metadata review complete", "verified"],
    ["Candidate review universe", formatNumber(phase.candidate_review_universe_size), "Metadata-only complete", "verified"],
    ["Source-review-ready queue", formatNumber(phase.source_review_ready_count), "Processed in four lanes", "verified"],
    ["Source-review/download outcomes", formatNumber(phase.source_review_download_attempted_count), phase.combined_source_review_download_available ? "Complete" : "Not started", "verified"],
    ["Unique retained sources", formatNumber(phase.source_review_download_retained_count), phase.combined_source_review_download_available ? "Hashed local files" : "None", "verified"],
    ["Readiness-reviewed sources", formatNumber(phase.pdf_text_readiness_reviewed_count), phase.combined_pdf_text_readiness_available ? "Four lanes complete" : "Not started", "verified"],
    ["Technically text-ready", formatNumber(phase.pdf_text_readiness_extraction_ready_count), phase.combined_pdf_text_readiness_available ? "Extraction queue eligible" : "Not classified", "verified"],
    ["Unavailable locators", formatNumber(phase.verification_unavailable_count), "Excluded from reachable", "future"],
    ["Blocked or timed out", formatNumber(phase.verification_blocked_timeout_count), "Deferred", "future"],
    ["Tier C memo supplement", formatNumber(phase.tier_c_memo_supplement_valid_scope), "Completed evidence artifact", "future"],
    ["Global analysis-ready evidence", "False", "Closed", "future"],
  ];

  return (
    <section className="panel hub-section" id="verification" aria-labelledby="verification-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Current operations pipeline</p>
          <h2 id="verification-title">From broad scout candidates to bounded locator verification</h2>
        </div>
        <StatusPill tone="verified">
          {phase.combined_pdf_text_readiness_available ? "Four-lane readiness complete; bounded text extraction next" : phase.combined_source_review_download_available ? "Four-lane source review/download complete; readiness next" : phase.combined_candidate_review_available ? "Combined candidate review complete; source review next" : phase.verification_all_lanes_completed ? "Four-lane verification complete; combined review next" : "Three lanes complete; lane 004 resume next"}
        </StatusPill>
      </div>

      <div className="verification-flow">
        {stages.map(([label, value, status, tone], index) => (
          <article key={label}>
            <span className="stage-number">{index + 1}</span>
            <h3>{label}</h3>
            <strong>{value}</strong>
            <StatusPill tone={tone}>{status}</StatusPill>
          </article>
        ))}
      </div>

      <div className="verification-callout">
        <div>
          <p className="eyebrow">Current operational handoff</p>
          <h3>{phase.combined_pdf_text_readiness_available ? "Readiness complete; approved retained files ready for bounded text extraction" : phase.combined_source_review_download_available ? "Source retrieval complete; retained files ready for bounded readiness review" : "Candidate metadata reviewed; locked source-review queue ready"}</h3>
        </div>
        {phase.combined_pdf_text_readiness_available ? <p>
          The four-lane local readiness review covered all {formatNumber(phase.pdf_text_readiness_reviewed_count)}
          {" "}retained files and approved {formatNumber(phase.pdf_text_readiness_extraction_ready_count)} for the later
          bounded extraction queue. Deferred and error categories remain excluded. This stage saved no source text,
          ran no OCR/rendering/rating/model/ingestion/codification or wage analysis, and left global readiness false.
        </p> : phase.combined_source_review_download_available ? <p>
          The four-lane source-review run processed {formatNumber(phase.source_review_download_attempted_count)} locked rows,
          retained {formatNumber(phase.source_review_download_retained_count)} unique hashed local files, and routed
          {" "}{formatNumber(phase.source_review_download_excluded_deferred_count)} rows to bounded exclusions or deferrals.
          No retained document was parsed, rendered, OCRed, extracted, rated, ingested, codified, or used for analytical claims.
        </p> : <p>
          The broad scout produced {formatNumber(phase.broad_state_4x1000_live_candidate_count)} new rows and
          {" "}{formatNumber(phase.broad_state_4x1000_live_deduped_candidate_count)} deduplicated candidates. The
          bounded verifier locked {formatNumber(phase.verification_queue_size)} defensible locators and completed
          {" "}{formatNumber(phase.verification_completed_count)} HEAD-only outcomes. The local combined review covered
          {" "}{formatNumber(phase.candidate_review_universe_size)} rows and retained {formatNumber(phase.source_review_ready_count)}
          for a later bounded source-review wave; download, source review, extraction, rating, ingestion, codification,
          wage-gap analysis, and causal analysis have not run on this reviewed scope.
        </p>}
      </div>
      <div className="verification-callout">
        <div>
          <p className="eyebrow">Content triage</p>
          <h3>
            {contentTriageStatus.content_triage_phase ===
            "metadata_only_full_universe_merged"
              ? "Full metadata-only triage ledger is merged"
              : contentTriageStatus.content_triage_phase ===
                "metadata_only_full_universe_collected_not_merged"
              ? "Full routed universe has metadata-only triage"
              : contentTriageStatus.content_triage_phase ===
                "metadata_only_round1_collected_not_merged"
              ? "First metadata-only triage round is collected"
              : "First metadata-first review round is prepared"}
          </h3>
        </div>
        <p>
          {contentTriageStatus.content_triage_phase ===
          "metadata_only_full_universe_merged" ? (
            <>
              The durable metadata-only ledger covers{" "}
              {formatNumber(contentTriageStatus.metadata_only_triage_rows_merged)}
              {" "}routed candidate identities:{" "}
              {formatNumber(contentTriageStatus.high_priority_content_review_rows)} p1,{" "}
              {formatNumber(contentTriageStatus.medium_priority_content_review_rows)} p2,{" "}
              {formatNumber(contentTriageStatus.low_priority_content_review_rows)} p3,{" "}
              {formatNumber(contentTriageStatus.metadata_only_priority_for_content_review_counts?.defer)} deferred,
              and{" "}
              {formatNumber(contentTriageStatus.metadata_only_priority_for_content_review_counts?.exclude)} excluded.
              These are preliminary metadata scheduling outcomes. Content downloads,
              source rating, ingestion, wage extraction, and wage-gap analysis have
              not started.
            </>
          ) : contentTriageStatus.content_triage_phase ===
            "metadata_only_full_universe_collected_not_merged" ? (
            <>
              Metadata-only triage produced {formatNumber(contentTriageStatus.metadata_only_triage_rows_collected)}
              {" "}terminal scheduling outcomes across the complete routed candidate universe.
              The durable triage merge has not run. No URL was reopened, no source
              was downloaded or parsed, and every relevance and extraction-readiness
              signal remains preliminary.
            </>
          ) : contentTriageStatus.content_triage_phase ===
            "metadata_only_round1_collected_not_merged" ? (
            <>
              Metadata-only triage produced {formatNumber(contentTriageStatus.metadata_only_triage_rows_collected)}
              {" "}terminal scheduling outcomes in {formatNumber(contentTriageStatus.initial_triage_lane_count)}
              {" "}lanes. The durable triage merge has not run. No URL was reopened,
              no source was downloaded or parsed, and every relevance and
              extraction-readiness signal remains preliminary.
            </>
          ) : (
            <>
              Content triage is planned for {formatNumber(contentTriageStatus.initial_triage_round_rows)}
              {" "}reachable/reused candidates in {formatNumber(contentTriageStatus.initial_triage_lane_count)}
              {" "}offline-prepared lanes. No URL has been reopened, no source has been downloaded,
              and source rating, extraction readiness, ingestion, codification, wage extraction,
              and wage-gap analysis have not started.
            </>
          )}
        </p>
      </div>
      <div className="verification-callout">
        <div>
          <p className="eyebrow">Source review</p>
          <h3>
            {sourceReviewStatus.source_review_phase === "combined_broad_4961_readiness_parallel_lanes_completed"
              ? "Combined broad PDF/text-layer readiness complete in four lanes"
              : sourceReviewStatus.source_review_phase === "combined_broad_5589_parallel_lanes_completed"
              ? "Combined broad source review/download complete in four lanes"
              : sourceReviewStatus.source_review_phase ===
            "batch3_3x500_merged"
              ? "Batch 3 merged: 2,150 cumulative source-review rows"
              : sourceReviewStatus.source_review_phase ===
            "batch3_3x500_collected_not_merged"
              ? "Batch 3 collected: 1,480 of 1,500 bounded artifacts; serial merge pending"
              : sourceReviewStatus.source_review_phase ===
            "batch2_500_merged"
              ? "Batch 2 merged: 650 cumulative source-review rows; plan Batch 3"
              : sourceReviewStatus.source_review_phase ===
            "batch2_500_collected_not_merged"
              ? "Batch 2 collected: 495 of 500 bounded artifacts; serial merge pending"
              : sourceReviewStatus.source_review_phase ===
            "pilot1_httpx_merged"
              ? "Pilot 1 HTTPX review merged; plan the bounded 500-row follow-on"
              : sourceReviewStatus.source_review_phase ===
            "pilot1_httpx_retry_collected_not_merged"
              ? "Pilot 1 HTTPX retry succeeded; serial merge pending"
              : sourceReviewStatus.source_review_phase ===
            "pilot1_connection_diagnosed_retry_not_started"
              ? "Pilot 1 transport fixed; bounded retry awaits authorization"
              : sourceReviewStatus.source_review_phase ===
            "pilot1_live_collected_not_merged"
              ? "Pilot 1 collected; terminal transport outcomes await merge"
              : sourceReviewStatus.source_review_phase ===
            "live_path_implemented_ready_for_pilot"
              ? "Bounded live path mock-tested; 150-row pilot ready"
              : "150-row p1 pilot prepared; no downloads yet"}
          </h3>
        </div>
        <p>
          {sourceReviewStatus.source_review_phase === "combined_broad_4961_readiness_parallel_lanes_completed" ? (
            <>
              The coordinator readiness-reviewed all {formatNumber(sourceReviewStatus.pdf_text_readiness_reviewed_count)}
              {" "}retained local sources: {formatNumber(sourceReviewStatus.pdf_text_readiness_pdf_reviewed_count)} PDFs,
              {" "}{formatNumber(sourceReviewStatus.pdf_text_readiness_html_reviewed_count)} HTML files, and
              {" "}{formatNumber(sourceReviewStatus.pdf_text_readiness_other_document_reviewed_count)} other documents.
              Later local text parsing is approved for {formatNumber(sourceReviewStatus.parse_text_layer_ready_count)}
              {" "}text-layer PDFs, {formatNumber(sourceReviewStatus.html_text_ready_count)} HTML files, and
              {" "}{formatNumber(sourceReviewStatus.other_document_text_ready_count)} other documents.
              Deferred boundaries remain visible: {formatNumber(sourceReviewStatus.ocr_later_or_defer_count)} OCR-later,
              {" "}{formatNumber(sourceReviewStatus.oversized_for_text_pass_count)} oversized,
              {" "}{formatNumber(sourceReviewStatus.corrupt_or_unreadable_count)} corrupt/unreadable,
              {" "}{formatNumber(sourceReviewStatus.encrypted_or_locked_count)} encrypted/locked,
              {" "}{formatNumber(sourceReviewStatus.shell_or_navigation_only_count)} shell/navigation-only,
              {" "}{formatNumber(sourceReviewStatus.unsupported_for_text_extraction_count)} unsupported,
              {" "}{formatNumber(sourceReviewStatus.needs_review_count)} needing review, and
              {" "}{formatNumber(sourceReviewStatus.readiness_error_count)} readiness errors. No full text, tables,
              spans, OCR, rendering, rating, model analysis, ingestion, codification, or wage/causal analysis occurred.
              Global analysis readiness remains false; four-lane bounded extraction is the next authorized stage.
            </>
          ) : sourceReviewStatus.source_review_phase === "combined_broad_5589_parallel_lanes_completed" ? (
            <>
              All {formatNumber(sourceReviewStatus.source_review_download_attempted_count)} locked rows reached
              terminal source-review/download outcomes. The coordinator retained {formatNumber(sourceReviewStatus.retained_source_count)}
              {" "}unique hashed local sources: {formatNumber(sourceReviewStatus.retained_pdf_count)} PDFs,
              {" "}{formatNumber(sourceReviewStatus.retained_html_count)} HTML files, and
              {" "}{formatNumber(sourceReviewStatus.retained_other_document_count)} other documents. The files remain
              unparsed, unrendered, un-OCRed, unextracted, unrated, uningested, uncodified, non-causal, and outside
              global analysis readiness. A separately authorized PDF/text-layer readiness pass is next.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "batch3_3x500_merged" ? (
            <>
              Batch 3 is durably merged:{" "}
              {formatNumber(sourceReviewStatus.batch3_3x500_artifact_saved_rows)}
              {" "}of {formatNumber(sourceReviewStatus.batch3_3x500_rows_merged)}
              {" "}Batch 3 rows retain bounded artifacts, 16 attempts timed
              out, four were forbidden, and connection errors remained zero.
              The cumulative source-review ledger now contains{" "}
              {formatNumber(sourceReviewStatus.cumulative_merged_source_review_rows)}
              {" "}rows and{" "}
              {formatNumber(sourceReviewStatus.cumulative_artifact_saved_rows)}
              {" "}saved artifacts. The next recommendation is a bounded
              text-layer/page-count readiness pilot. PDFs remain unparsed;
              ingestion, codification, wage extraction, and wage-gap analysis
              have not started.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "batch3_3x500_collected_not_merged" ? (
            <>
              Batch 3 completed all{" "}
              {formatNumber(sourceReviewStatus.batch3_3x500_rows_collected)}
              {" "}locked rows across three lanes and retained{" "}
              {formatNumber(sourceReviewStatus.batch3_3x500_content_artifact_count)}
              {" "}hashed PDF artifacts. Sixteen attempts timed out, four were
              forbidden, and connection errors remained zero. The durable
              source-review layer remains at{" "}
              {formatNumber(sourceReviewStatus.cumulative_merged_source_review_rows)}
              {" "}rows until a separate serial merge. PDFs remain unparsed;
              ingestion, codification, wage extraction, and wage-gap analysis
              have not started.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "batch2_500_merged" ? (
            <>
              Batch 2 is durably merged:{" "}
              {formatNumber(sourceReviewStatus.batch2_500_artifact_saved_rows)}
              {" "}of {formatNumber(sourceReviewStatus.batch2_500_rows_merged)}
              {" "}Batch 2 rows retain bounded artifacts, five attempts timed
              out, and the cumulative source-review ledger now contains{" "}
              {formatNumber(sourceReviewStatus.cumulative_merged_source_review_rows)}
              {" "}rows. The next recommendation is Batch 3 planning at 1,000
              rows after relay review. PDFs remain unparsed, and ingestion,
              codification, wage extraction, and wage-gap analysis have not
              started.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "batch2_500_collected_not_merged" ? (
            <>
              Batch 2 completed all{" "}
              {formatNumber(sourceReviewStatus.batch2_500_rows_collected)}
              {" "}locked rows and retained{" "}
              {formatNumber(sourceReviewStatus.batch2_500_content_artifact_count)}
              {" "}hashed PDF artifacts; five bounded attempts timed out and no
              connection errors occurred. The durable source-review layer remains
              at {formatNumber(sourceReviewStatus.cumulative_merged_source_review_rows)}
              {" "}Pilot 1 rows until a separate serial merge. PDFs remain unparsed,
              and ingestion, codification, wage extraction, and wage-gap analysis
              have not started.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "pilot1_httpx_merged" ? (
            <>
              The repaired Pilot 1 result is durably merged:{" "}
              {formatNumber(sourceReviewStatus.pilot1_artifact_saved_rows)}
              {" "}of {formatNumber(sourceReviewStatus.pilot1_rows_merged)}
              {" "}rows retain bounded artifacts, one row is forbidden, and
              the original transport-failed attempt remains superseded. The next
              recommendation is a separately reviewed 500-row plan. PDFs remain
              unparsed, and ingestion, codification, wage extraction, and wage-gap
              analysis have not started.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "pilot1_httpx_retry_collected_not_merged" ? (
            <>
              The repaired-client retry completed all{" "}
              {formatNumber(sourceReviewStatus.pilot1_httpx_retry_rows_collected)}
              {" "}locked rows and retained{" "}
              {formatNumber(sourceReviewStatus.pilot1_httpx_retry_content_artifact_count)}
              {" "}hashed PDF artifacts; one expected row remained forbidden and
              no connection errors recurred. The original transport-failed attempt
              remains preserved and unmerged. A separate serial merge is still
              required, and ingestion, codification, wage extraction, and wage-gap
              analysis remain unstarted.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "pilot1_connection_diagnosed_retry_not_started" ? (
            <>
              The original 150-row attempt remains unmerged after 149 connection
              errors. A verifier-compatible client then completed a locked{" "}
              {formatNumber(sourceReviewStatus.diagnostic_probe_rows)}-row
              diagnostic with{" "}
              {formatNumber(sourceReviewStatus.diagnostic_probe_content_artifact_count)}
              {" "}bounded PDF artifacts, one forbidden response, and zero connection
              errors. This proves the repaired access path but does not authorize a
              retry or scale-up; ingestion, codification, wage extraction, and
              wage-gap analysis remain unstarted.
            </>
          ) : sourceReviewStatus.source_review_phase ===
          "pilot1_live_collected_not_merged" ? (
            <>
              Bounded access was attempted for all{" "}
              {formatNumber(sourceReviewStatus.pilot1_live_rows_collected)}
              {" "}locked candidates. All rows are terminal, but{" "}
              {formatNumber(sourceReviewStatus.pilot1_source_review_status_counts?.download_connection_error)}
              {" "}ended in connection errors and{" "}
              {formatNumber(sourceReviewStatus.pilot1_source_review_status_counts?.download_forbidden)}
              {" "}was forbidden; no source body was retained. The durable source-review
              merge, ingestion, codification, wage extraction, and wage-gap analysis
              have not started.
            </>
          ) : (
            <>
          The offline source-review plan selects{" "}
          {formatNumber(sourceReviewStatus.initial_source_review_pilot_rows)}
          {" "}metadata-triaged candidates across{" "}
          {formatNumber(sourceReviewStatus.initial_source_review_lane_count)}
          {" "}balanced lanes and{" "}
          {formatNumber(sourceReviewStatus.initial_source_review_states)}
          {" "}states. {sourceReviewStatus.source_review_phase ===
          "live_path_implemented_ready_for_pilot"
            ? `The fail-closed runner is ready at concurrency ${formatNumber(sourceReviewStatus.recommended_initial_live_concurrency)} and a ${formatNumber(sourceReviewStatus.recommended_initial_max_bytes)}-byte cap after mocked transport tests. `
            : null}
          No real source content has been accessed, and final source
          rating, extraction readiness, ingestion, codification, wage extraction,
          and wage-gap analysis have not started.
            </>
          )}
        </p>
      </div>
      <div className="verification-callout">
        <div>
          <p className="eyebrow">PDF readiness</p>
          <h3>
            {pdfReadinessStatus.pdf_readiness_phase ===
            "broad_state_4x2500_3672_completed"
              ? "Broad state 4 × 2,500 readiness complete for all retained source types"
              : pdfReadinessStatus.pdf_readiness_phase ===
            "combined_broad_4961_completed"
              ? "Combined broad readiness complete for all retained source types"
              : pdfReadinessStatus.pdf_readiness_phase ===
            "full_retained_merged"
              ? "Full retained PDF readiness merged"
              : pdfReadinessStatus.pdf_readiness_phase ===
            "full_retained_collected_not_merged"
              ? "Full retained PDF readiness collected; merge pending"
              : pdfReadinessStatus.pdf_readiness_phase ===
            "pilot1_collected_not_merged"
              ? "Local PDF-readiness pilot collected; merge pending"
              : "Local PDF-readiness pilot not started"}
          </h3>
        </div>
        <p>
          {pdfReadinessStatus.pdf_readiness_phase ===
          "broad_state_4x2500_3672_completed" || pdfReadinessStatus.pdf_readiness_phase ===
          "combined_broad_4961_completed" ? (
            <>
              Four staggered lanes readiness-reviewed {formatNumber(pdfReadinessStatus.readiness_reviewed_count)}
              {" "}retained sources, including {formatNumber(pdfReadinessStatus.retained_pdf_artifacts_available)} PDFs,
              {" "}{formatNumber(pdfReadinessStatus.retained_html_artifacts_available)} HTML files, and
              {" "}{formatNumber(pdfReadinessStatus.retained_other_document_artifacts_available)} other documents.
              A total of {formatNumber(pdfReadinessStatus.extraction_ready_rows)} are technically ready for a later
              bounded text pass; all OCR-later, oversized, corrupt, locked, shell, unsupported, needs-review, and
              error rows remain excluded. No OCR or rendering occurred, and global analysis readiness remains false.
            </>
          ) : pdfReadinessStatus.pdf_readiness_phase ===
          "full_retained_merged" ? (
            <>
              The durable technical-readiness layer covers{" "}
              {formatNumber(pdfReadinessStatus.pdf_readiness_rows_merged)}
              {" "}of{" "}
              {formatNumber(pdfReadinessStatus.retained_pdf_artifacts_available)}
              {" "}retained PDFs:{" "}
              {formatNumber(pdfReadinessStatus.text_layer_present_rows)}
              {" "}have text on every sampled page,{" "}
              {formatNumber(pdfReadinessStatus.text_layer_partial_rows)}
              {" "}have partial sampled text, and{" "}
              {formatNumber(pdfReadinessStatus.text_layer_absent_rows)}
              {" "}have no sampled text. The layer represents{" "}
              {formatNumber(pdfReadinessStatus.total_pages_represented)}
              {" "}pages. Technical readiness is complete for retained PDFs;
              the next recommendation is a bounded text-layer/table-detection
              pilot. OCR, wage extraction, ingestion, and codification have
              not started.
            </>
          ) : pdfReadinessStatus.pdf_readiness_phase ===
          "full_retained_collected_not_merged" ? (
            <>
              Local technical readiness now covers{" "}
              {formatNumber(
                pdfReadinessStatus.full_retained_pdf_readiness_rows_collected,
              )}
              {" "}of{" "}
              {formatNumber(pdfReadinessStatus.retained_pdf_artifacts_available)}
              {" "}retained PDFs:{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.present)}
              {" "}have text on every sampled page,{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.partial)}
              {" "}have partial sampled text, and{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.absent)}
              {" "}have no sampled text. Every retained PDF yielded a page
              count; parser, hash, and missing-artifact failures were zero.
              Pilot 1 and the full remainder are collected but not durably
              merged. No URL, download, OCR, retained extracted text, wage
              extraction, ingestion, or codification occurred.
            </>
          ) : pdfReadinessStatus.pdf_readiness_phase ===
          "pilot1_collected_not_merged" ? (
            <>
              The bounded local pilot checked{" "}
              {formatNumber(pdfReadinessStatus.pilot_rows_collected)}
              {" "}already-retained PDFs:{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.present)}
              {" "}have text on every sampled page,{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.partial)}
              {" "}have partial sampled text, and{" "}
              {formatNumber(pdfReadinessStatus.text_layer_status_counts?.absent)}
              {" "}have no sampled text. All yielded page counts; parser,
              hash, and missing-artifact failures were zero. Results are
              collected but not durably merged. No URL, download, OCR,
              retained extracted text, wage extraction, ingestion, or
              codification occurred.
            </>
          ) : (
            <>
              The source-review layer retains{" "}
              {formatNumber(pdfReadinessStatus.retained_pdf_artifacts_available)}
              {" "}PDFs, but local page-count and text-layer readiness has not
              been sampled.
            </>
          )}
        </p>
      </div>
      <div className="verification-callout">
        <div>
          <p className="eyebrow">Text/table detection</p>
          <h3>
            {textTableDetectionStatus.text_table_detection_phase ===
            "full_parse_text_merged"
              ? "Full bounded local pass merged; calibration is next"
              : textTableDetectionStatus.text_table_detection_phase ===
            "full_parse_text_collected_not_merged"
              ? "Full bounded local pass collected; serial merge pending"
              : textTableDetectionStatus.text_table_detection_phase ===
            "pilot1_collected_not_merged"
              ? "Bounded local pilot collected; merge pending"
              : "Bounded local pilot not started"}
          </h3>
        </div>
        <p>
          {textTableDetectionStatus.text_table_detection_phase ===
          "full_parse_text_merged" ? (
            <>
              The durable detection ledger covers all{" "}
              {formatNumber(
                textTableDetectionStatus.full_parse_text_rows_merged,
              )}
              {" "}parse-text PDFs:{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.likely,
              )}
              {" "}likely,{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.possible,
              )}
              {" "}possible, and{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.unlikely,
              )}
              {" "}unlikely wage-table signals. Candidate pages are
              heuristic hints, not wage observations. Manual calibration is
              next; OCR, final wage extraction, ingestion, and codification
              have not started.
            </>
          ) : textTableDetectionStatus.text_table_detection_phase ===
          "full_parse_text_collected_not_merged" ? (
            <>
              All{" "}
              {formatNumber(
                textTableDetectionStatus.full_parse_text_rows_collected,
              )}
              {" "}durable parse-text PDFs produced terminal frozen-heuristic
              results:{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.likely,
              )}
              {" "}likely,{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.possible,
              )}
              {" "}possible, and{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.unlikely,
              )}
              {" "}unlikely wage-table signals. These are preliminary page
              hints, not wage observations. A separate serial merge and
              manual calibration are next; OCR, final wage extraction,
              ingestion, and codification have not started.
            </>
          ) : textTableDetectionStatus.text_table_detection_phase ===
          "pilot1_collected_not_merged" ? (
            <>
              All{" "}
              {formatNumber(textTableDetectionStatus.pilot_rows_collected)}
              {" "}locked retained PDFs produced terminal heuristic results:{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.likely,
              )}
              {" "}likely and{" "}
              {formatNumber(
                textTableDetectionStatus.wage_table_signal_counts?.possible,
              )}
              {" "}possible wage-table signals, with{" "}
              {formatNumber(textTableDetectionStatus.candidate_wage_page_hints)}
              {" "}candidate page hints. These are preliminary page-level
              signals, not wage observations. A full local detection pass is
              recommended after review; the pilot remains unmerged, and OCR,
              final wage extraction, ingestion, and codification have not
              started.
            </>
          ) : (
            <>
              The durable readiness layer has{" "}
              {formatNumber(
                textTableDetectionStatus.parse_text_layer_later_rows_available,
              )}
              {" "}parse-text candidates, but bounded table detection has not
              started.
            </>
          )}
        </p>
      </div>
      <div className="verification-callout">
        <div>
          <p className="eyebrow">Current downstream status</p>
          <h3>
            {textTableCalibrationStatus.calibration_phase ===
            "tier_c_readiness_dashboard_map_update_completed_text_extraction_ready"
              ? "Tier C text readiness complete; bounded extraction is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "dashboard_fix_and_tier_c_download_completed_pdf_readiness_ready_dashboard_fixed"
              ? "Dashboard fixed; Tier C sources retained; PDF/text-layer readiness is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_tier_c_verification_completed_source_review_ready_dashboard_visible"
              ? "Gap-directed Tier C verification complete; source review/download is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended"
              ? "Bounded internal mechanism-linkage memo complete; targeted Tier C verification is recommended"
              : textTableCalibrationStatus.calibration_phase ===
            "mechanism_linkage_claim_review_268_completed_claim_memo_allowed"
              ? "Exact-source mechanism-linkage claim review complete; bounded claim memo is allowed"
              : textTableCalibrationStatus.calibration_phase ===
            "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready"
              ? "Strict quantitative-to-mechanism linkage complete; bounded claim review is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready"
              ? "Quantitative direct-text triage complete; bounded mechanism linkage is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_evidence_span_rating_summary_173_completed_quantitative_triage_recommended"
              ? "Targeted exact-span summary complete; quantitative triage is recommended"
              : ["targeted_evidence_span_rating_201_completed_summary_ready",
              "targeted_evidence_span_rating_201_completed_with_quarantine"].includes(
              textTableCalibrationStatus.calibration_phase,
            )
              ? "Targeted exact-span rating complete; bounded summary review is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_evidence_span_extraction_321_completed_rating_ready"
              ? "Targeted exact evidence-span extraction complete; bounded span rating is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_text_layer_extraction_321_completed_evidence_extraction_ready"
              ? "Targeted local text-layer extraction complete; bounded evidence-span extraction review is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready"
              ? "Targeted PDF/text-layer readiness complete; bounded local extraction is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_source_review_download_429_completed_pdf_readiness_ready"
              ? "Targeted source review/download complete; bounded PDF and text-layer readiness is next"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_source_verification_tier_a_b_completed_source_review_ready"
              ? "Tier A+B targeted source verification complete; bounded source review/download is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_scouting_four_lane_candidate_review_completed_verification_ready"
              ? "Four-lane candidate review complete; targeted source verification is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready"
              ? "Four-lane fixed-stagger live scouting complete; candidate review is ready"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required"
              ? "Four-lane live preflight failed closed; scheduling contract repair is required"
              : textTableCalibrationStatus.calibration_phase ===
            "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready"
              ? "Four-lane targeted scouting dry prep complete; Lane 1 is ready for separate live authorization"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_provisional_claim_review_636_completed_targeted_scouting_restart_recommended"
              ? "Bounded provisional claim review complete; targeted scouting restart recommended"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed"
              ? "Bounded GABRIEL rating summary complete; provisional claim review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed"
              ? "Bounded GABRIEL quarantine repair complete; summary review may proceed with seven exclusions"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_gabriel_claim_rating_643_repaired_summary_review_allowed"
              ? "Bounded GABRIEL quarantine repair complete; all 643 ratings are valid"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine"
              ? "Bounded GABRIEL claim rating completed; 35 rows remain quarantined"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed"
              ? "Bounded GABRIEL claim rating completed; summary review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready"
              ? "Claim-oriented compensation phase closed; bounded GABRIEL claim rating may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready"
              ? "Compensation-evidence QA phase closed; bounded GABRIEL attribute analysis may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed"
              ? "Limited qualitative usage registry accepted; pipeline-stage strategy review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed"
              ? "Limited qualitative usage registry review passed; registry acceptance may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed"
              ? "Limited qualitative usage layer accepted and registered; registry review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_qualitative_usage_layer_qa_review_pass_acceptance_prompt_allowed"
              ? "Limited qualitative usage layer passed QA; acceptance registration may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_qualitative_usage_layer_materialized_qa_review_allowed"
              ? "Limited qualitative usage layer materialized; bounded QA review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_exact_span_qualitative_usage_review_completed_usage_layer_prompt_allowed"
              ? "Limited exact-span qualitative usage scope reviewed; a restricted usage-layer prompt may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_exact_span_qualitative_promotion_completed_usage_review_allowed"
              ? "Limited exact-span qualitative layer promoted with explicit restrictions; usage review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_pipeline_hardening_complete_limited_promotion_allowed"
              ? "Readiness pipeline hardened; limited qualitative promotion prompt may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_limited_exact_span_qualitative_readiness_review_completed_pass_with_blockers"
              ? "Limited exact-span qualitative readiness review passed with documented restrictions"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_qualitative_evidence_contract_limited_review_allowed_exact_span_only"
              ? "Qualitative evidence contract built; limited exact-span readiness review may proceed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_bounded_qualitative_span_disambiguation_partial_additional_repair_required"
              ? "Bounded qualitative span disambiguation improved exact QA; navigation-only blockers remain"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_bounded_pdf_text_span_capture_partial_additional_repair_required"
              ? "Bounded PDF text-layer capture hardened; literal spans remain partially QA-ready"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_bounded_span_residual_repair_blocked_missing_text_support"
              ? "Bounded residual repair improved metadata; literal spans remain blocked by missing retained text payloads"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_bounded_schema_followup_partial_additional_repair_required"
              ? "Bounded schema follow-up improved coverage; literal-span and residual repair still required"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_final_provisional_schema_repair_partial_followup_required"
              ? "Schema mechanics repaired; bounded metadata and evidence follow-up still required"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_final_provisional_schema_readiness_review_completed_hold"
              ? "Package integrity passed; schema repairs required before analysis promotion"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_final_provisional_package_materialized_qa_pass"
              ? "Final provisional package materialized; analysis remains closed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_final_provisional_merge_prompt_prepared"
              ? "Final provisional merge prompt prepared; merge remains authorization-gated"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_readable_parse_text_1826_independent_bounded_review_completed"
              ? "Independent bounded review passed; final merge prompt may be prepared"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_readable_parse_text_1826_targeted_conflict_qa_completed"
              ? "Readable parse-text targeted conflict QA passed; provisional layer remains analysis-closed"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_readable_parse_text_1826_materialized_qa_pass"
              ? "All readable parse-text evidence materialized; targeted conflict QA remains"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_remaining_parse_text_live_incomplete_825_of_826"
              ? "Remaining readable parse-text run stopped with one case unresolved"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_1000_targeted_qa_completed"
              ? "Cumulative 1,000-document targeted QA passed; remaining readable parse-text run authorized"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_1000_materialized_qa_blocked"
              ? "Provisional 1,000-document layer materialized; targeted QA required"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_1000_live_incomplete_499_of_500"
              ? "Provisional 1,000-document scale-up stopped with one new case unresolved"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_500_targeted_qa_completed"
              ? "Targeted QA passed; provisional 1,000-document scale-up authorized"
              : textTableCalibrationStatus.calibration_phase ===
            "compensation_extraction_500_provisional_completed"
              ? "Provisional 500-document compensation extraction complete; QA hold before 1,000"
              : textTableCalibrationStatus.calibration_phase ===
            "auto_gabriel_gate3_compensation_completed"
              ? "Compensation-evidence Gate 3 complete; future 500-doc extraction authorized"
              : textTableCalibrationStatus.calibration_phase ===
            "auto_gabriel_gate2_completed"
              ? "Automated GABRIEL Gate 2 complete; extraction remains closed"
              : textTableCalibrationStatus.calibration_phase ===
            "auto_gabriel_gate1_completed"
              ? "Automated visual + GABRIEL gate complete; extraction remains closed"
              : textTableCalibrationStatus.calibration_phase ===
            "independent_adjudication_packet_prepared"
              ? "Blinded independent adjudication packet prepared"
              : textTableCalibrationStatus.calibration_phase ===
            "refined_review2_completed"
              ? "Refined visual review complete; extraction remains closed"
              : textTableCalibrationStatus.calibration_phase ===
            "refinement_prepared_after_failed_review"
              ? "Visual table gate prepared; refined re-review is next"
              : textTableCalibrationStatus.calibration_phase ===
            "subset1_reviewed"
              ? textTableCalibrationStatus.calibration_pass_status === "fail"
                ? "Assisted calibration complete; extraction gate failed"
                : "Assisted calibration complete; extraction gate is cautionary"
              : textTableCalibrationStatus.calibration_phase ===
            "subset1_prepared_not_reviewed"
              ? "Stratified calibration packet prepared; review not started"
              : "Manual calibration packet not prepared"}
          </h3>
        </div>
        <p>
          {textTableCalibrationStatus.calibration_phase ===
          "tier_c_readiness_dashboard_map_update_completed_text_extraction_ready" ? (
            <>
              Local readiness review reconciled {formatNumber(
                textTableCalibrationStatus.tier_c_readiness_queue_count,
              )} retained Tier C files. The later extraction manifests contain {formatNumber(
                (textTableCalibrationStatus.tier_c_readiness_status_counts?.parse_text_layer_later || 0) +
                (textTableCalibrationStatus.tier_c_readiness_status_counts?.html_text_later || 0),
              )} files; all OCR-later, oversized, noisy, and review rows remain excluded.
              Map data date: {textTableCalibrationStatus.tier_c_dashboard_map_data_date}.
              No URL, download, OCR, rendering, saved document text, evidence extraction, rating,
              ingestion, or codification occurred; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "dashboard_fix_and_tier_c_download_completed_pdf_readiness_ready_dashboard_fixed" ? (
            <>
              Bounded source review processed {formatNumber(
                textTableCalibrationStatus.targeted_tier_c_source_review_download_queue_count,
              )} verified Tier C leads and retained {formatNumber(
                textTableCalibrationStatus.targeted_tier_c_retained_downloaded_source_count,
              )} source files for later PDF/text-layer readiness. Retained files remain not extracted,
              not rated, not ingested, not codified, and non-causal; global readiness remains closed.
              The dashboard now reads the current generated phase rather than the historical scout-phase
              fallback. Memo: {" "}<code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_path}</code>;
              {" "}dashboard metadata: <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata_path}</code>;
              {" "}geographic report: <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_report_path}</code>.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_tier_c_verification_completed_source_review_ready_dashboard_visible" ? (
            <>
              Gap-directed HTTP HEAD verification processed {formatNumber(
                textTableCalibrationStatus.targeted_tier_c_verification_queue_count,
              )} selected Tier C candidates and retained {formatNumber(
                textTableCalibrationStatus.targeted_tier_c_verified_source_lead_count,
              )} verified source leads. The bounded internal memo remains visible with {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.exact_same_source_linked_pair_count,
              )} exact same-source pairs, {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.linked_quantitative_row_count,
              )} quantitative rows, and {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.linked_qualitative_record_count,
              )} qualitative records. Verified Tier C leads remain not downloaded, not extracted,
              not rated, and non-causal. Global readiness remains closed. Memo: {" "}
              <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_path}</code>;
              {" "}dashboard metadata: <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata_path}</code>;
              {" "}geographic metadata: <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_metadata_path}</code>;
              {" "}geographic report: <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_report_path}</code>.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended" ? (
            <>
              The bounded internal memo covers {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.exact_same_source_linked_pair_count,
              )} exact same-source pairs, {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.linked_quantitative_row_count,
              )} quantitative rows, {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.linked_qualitative_record_count,
              )} qualitative records, and {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_scope?.shared_source_lineage_count,
              )} shared source lineages. Available local metadata covers {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_coverage?.state_count,
              )} states, {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_coverage?.city_state_pair_count,
              )} city-state pairs, and {formatNumber(
                textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_coverage?.city_cycle_unit_group_count,
              )} city-cycle-unit groups. This is bounded co-location and documentary-scaffold evidence only;
              global readiness, wage-gap estimates, effect estimates, and final causal claims remain closed.
              Detailed memo metadata is recorded at {" "}
              <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_path}</code>
              {" "}with dashboard metadata at {" "}
              <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata_path}</code>
              {" "}and geographic metadata at {" "}
              <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_metadata_path}</code>,
              {" "}with the geographic report at {" "}
              <code>{textTableCalibrationStatus.bounded_internal_mechanism_linkage_claim_memo_geographic_report_path}</code>.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "mechanism_linkage_claim_review_268_completed_claim_memo_allowed" ? (
            <>
              Deterministic review preserved all {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_pair_count,
              )} exact same-source pairs, covering {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_linked_quantitative_count,
              )} quantitative rows and {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_linked_qualitative_count,
              )} qualitative mechanism records. {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_claim_type_counts?.direct_text_colocation_claim,
              )} are direct co-location claims, {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_claim_type_counts?.documentary_mechanism_value_scaffold,
              )} are documentary scaffolds, and {formatNumber(
                textTableCalibrationStatus.mechanism_linkage_claim_review_claim_type_counts?.insufficient_for_claim,
              )} remain insufficient. No value transformation, outcome comparison, effect estimate,
              or causal inference occurred; global readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready" ? (
            <>
              Strict lineage linked {formatNumber(
                textTableCalibrationStatus.quantitative_to_qualitative_linked_pair_count,
              )} exact same-source quantitative/mechanism pairs, covering {formatNumber(
                textTableCalibrationStatus.quantitative_to_qualitative_linked_quantitative_count,
              )} quantitative rows. {formatNumber(
                textTableCalibrationStatus.quantitative_to_qualitative_no_link_count,
              )} quantitative candidates remain explicit no-link outcomes. No weak contextual
              match was manufactured; no value transformation, comparison, effect estimate,
              or causal inference occurred, and global readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready" ? (
            <>
              Deterministic triage preserved all {formatNumber(
                textTableCalibrationStatus.quantitative_direct_text_claim_triage_queue_count,
              )} raw quantitative rows. {formatNumber(
                textTableCalibrationStatus.quantitative_direct_text_claim_triage_readiness_counts?.direct_text_quantitative_claim_ready,
              )} are direct-text claim-ready and {formatNumber(
                textTableCalibrationStatus.quantitative_mechanism_linkage_candidate_count,
              )} have complete lineage for a later bounded mechanism-linkage stage.
              Values needing normalization remain separate; no comparison, model call,
              wage-gap estimate, or causal analysis occurred, and global readiness is closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_evidence_span_rating_summary_173_completed_quantitative_triage_recommended" ? (
            <>
              The deterministic review summarized {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_rating_summary_valid_count,
              )} valid exact-span ratings and preserved {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_rating_summary_excluded_count,
              )} quarantines as explicit exclusions. Strike/dispute-resolution and
              market/comparability documentary lanes are strengthened; direction remains
              predominantly neutral or unclear. Bounded triage of 862 preserved
              quantitative direct-text rows is recommended next. No model or source-file
              access occurred, and global analysis readiness remains closed.
            </>
          ) : ["targeted_evidence_span_rating_201_completed_summary_ready",
            "targeted_evidence_span_rating_201_completed_with_quarantine"].includes(
            textTableCalibrationStatus.calibration_phase,
          ) ? (
            <>
              The bounded GABRIEL run rated {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_rating_input_count,
              )}{" "}locked exact spans. {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_rating_valid_count,
              )}{" "}ratings are schema-valid and {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_rating_quarantine_count,
              )}{" "}remain explicit exclusions. Only exact supplied-span quotes
              passed; no URL, PDF/page, download, OCR, rendering, ingestion, or
              codification occurred. Ratings are documentary—not wage-gap or causal
              findings—and global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_evidence_span_extraction_321_completed_rating_ready" ? (
            <>
              The deterministic local review searched {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_extraction_queue_count,
              )}{" "}extracted-text sources and retained {formatNumber(
                textTableCalibrationStatus.targeted_evidence_span_record_count,
              )}{" "}exact documentary spans as separately reviewable rating candidates.
              Generic or uncertain matches remain ambiguous or no-span/weak. No URL,
              download, OCR, rendering, model call, rating, ingestion, or codification
              occurred; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_text_layer_extraction_321_completed_evidence_extraction_ready" ? (
            <>
              The bounded local extraction processed{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_text_layer_extraction_queue_count,
              )}
              {" "}readiness-approved files: {formatNumber(
                textTableCalibrationStatus.targeted_text_layer_extraction_pdf_count,
              )}{" "}PDFs and {formatNumber(
                textTableCalibrationStatus.targeted_text_layer_extraction_html_count,
              )}{" "}HTML artifacts. All {formatNumber(
                textTableCalibrationStatus.targeted_text_layer_extraction_status_counts?.extracted_ok || 0,
              )}{" "}produced task-local machine-readable text. No URL, download,
              OCR, rendering, model call, evidence rating, ingestion, or
              codification occurred. Exact evidence-span review requires a
              separate authorization; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready" ? (
            <>
              The local-only readiness review reconciled{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_pdf_text_layer_readiness_queue_count,
              )}
              {" "}retained files. The approved future extraction lanes contain{" "}
              {formatNumber(
                (textTableCalibrationStatus.targeted_pdf_text_layer_readiness_status_counts?.parse_text_layer_later || 0) +
                  (textTableCalibrationStatus.targeted_pdf_text_layer_readiness_status_counts?.html_text_later || 0),
              )}
              {" "}files; OCR-later, oversized, corrupt, and needs-review files remain
              explicitly excluded. No URL, download, OCR, rendering, saved
              document text, evidence extraction, rating, ingestion, or
              codification occurred. A separately authorized bounded text-layer
              extraction is next; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_source_review_download_429_completed_pdf_readiness_ready" ? (
            <>
              The bounded download stage reconciled{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_source_review_download_locked_count,
              )}
              {" "}locked verified leads and retained{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_source_review_download_retained_count,
              )}
              {" "}unique supported source files. Files were streamed and
              hashed without opening PDF pages, extracting text, running OCR,
              or rating evidence. They remain uningested, uncodified, and
              non-causal. A separately gated PDF/text-layer readiness review is
              next; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_source_verification_tier_a_b_completed_source_review_ready" ? (
            <>
              HEAD-only locator and metadata verification reconciled{ " "}
              {formatNumber(
                textTableCalibrationStatus.targeted_source_verification_queue_count,
              )}
              {" "}locked Tier A+B candidates and retained{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_source_verified_source_lead_count,
              )}
              {" "}verified source leads. No document body or PDF page was
              opened or downloaded; retained leads remain unextracted, unrated,
              and non-causal. A separately authorized bounded source-review and
              download stage is next; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_scouting_four_lane_candidate_review_completed_verification_ready" ? (
            <>
              Deterministic metadata review reconciled{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_scouting_four_lane_candidates_reviewed,
              )}
              {" "}candidate-only leads and placed{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_scouting_four_lane_verification_ready_candidates,
              )}
              {" "}in the separately gated verification queue. No locator was
              opened, no source was verified, and every lead remains
              unextracted, unrated, and non-causal. Targeted source verification
              is next; global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready" ? (
            <>
              All four immutable 500-target lanes completed with exact
              T+0/T+8/T+16/T+24 starts and explicitly authorized controlled
              overlap. The run produced{" "}
              {formatNumber(
                textTableCalibrationStatus.targeted_scouting_four_lane_candidate_sources,
              )}
              {" "}deduplicated candidate-only source leads. Candidates remain
              unverified, unextracted, unrated, and non-causal; candidate review
              is next and global analysis readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required" ? (
            <>
              All four immutable 500-target queues and lock hashes passed, but no
              hosted search started. Exact T+0/T+8/T+16/T+24 starts conflict with
              the simultaneous-lane prohibition for the established sequential
              one-request-per-target scout. The next authorization must choose
              either completion-gated sequential lanes or explicitly permitted
              staggered overlap. Candidate sources remain zero and global analysis
              readiness remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready" ? (
            <>
              Four candidate-only scouting lanes of 500 targets each passed
              deterministic no-call validation. Lane 1 prioritizes known safety
              contracts or scout-stage safety leads that need a same-city non-safety
              counterpart; Lanes 2–4 target previously unscouted municipalities for
              the sparse dispute-resolution, fiscal/equity, and market/safety-premium
              mechanism families. No live search or model/API call ran. Lane 1 requires
              a separate future authorization and preflight; global analysis readiness
              remains closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_provisional_claim_review_636_completed_targeted_scouting_restart_recommended" ? (
            <>
              The 636-row rating summaries now support 35 bounded claim records:
              nine documentary-mechanism claims, five direct-text claims, five
              explicitly provisional causal-candidate scaffolds, ten more-data
              claims, and six prohibited claim classes. Seven quarantine rows remain
              excluded and the 862-row quantitative lane remains unanalyzed. Targeted
              matched city-cycle scouting is recommended next; wage effects, wage
              gaps, regressions, treatment effects, final causal claims, and global
              analysis readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed" ? (
            <>
              The bounded review summarized exactly 636 schema-valid v1.1 ratings and
              preserved seven quarantine rows as explicit exclusions. Implementation
              timing, automatic raises, base-wage text, and non-base compensation are
              the strongest textual signals in this collected valid-rated corpus. Direct
              safety-advantage and non-safety-constraint support remains absent. A
              provisional claim review may proceed; wage effects, wage gaps, regressions,
              treatment effects, final causal claims, and global analysis readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed" ? (
            <>
              The bounded repair retried only the 35 explicit quarantine IDs and accepted
              28 additional schema-valid, exact-quote-verified ratings. The layer now has
              636 valid ratings and seven explicit exclusions, while the original 608
              accepted rows remain hash-identical. A bounded summary review may proceed
              over only the 636 valid rows. Wage effects, wage gaps, regressions, final
              causal claims, and global analysis readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_gabriel_claim_rating_643_repaired_summary_review_allowed" ? (
            <>
              The bounded repair resolved all prior quarantine rows without changing the
              original accepted ratings. All 643 rows are schema-valid and exact-quote
              verified. A bounded summary review may proceed; wage effects, wage gaps,
              regressions, final causal claims, and global analysis readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine" ? (
            <>
              The bounded v1.1 GABRIEL run processed exactly 643 authorized exact-span
              qualitative rows. It produced 608 schema-valid, exact-quote-verified ratings
              and retained 35 rows in explicit quarantine after bounded retries. No row was
              silently dropped. A bounded quarantine repair is next; cross-row statistics,
              wage effects, wage gaps, regressions, final causal claims, and global analysis
              readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed" ? (
            <>
              The bounded v1.1 GABRIEL run produced schema-valid, exact-quote-verified
              ratings for all 643 authorized rows. A separately authorized documentary
              summary review may proceed. Wage effects, wage gaps, regressions, final causal
              claims, and global analysis readiness remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready" ? (
            <>
              The claim-oriented QA/rating phase is closed with all 8,939 records assigned to
              exactly one primary category. The bounded claim-ready aggregate contains 1,505
              records: 862 accepted quantitative records with explicit structured values and
              643 exact-span qualitative mechanism records. The 643 exact-span rows are ready
              for a separately authorized GABRIEL claim-rating run under the stable v1 codebook.
              Causal-candidate support remains unrated and provisional; global readiness,
              cross-document statistics, wage gaps, regressions, and final causal claims remain
              closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready" ? (
            <>
              The QA/debugging/categorization phase is closed with 8,939 records assigned to
              exactly one category: 643 GABRIEL-ready exact-span rows, 862 limited documentary
              rows, 614 navigation-only rows, 5,078 companion/context rows, 121 quarantined
              rows, and 1,621 phase write-offs. The 13-attribute taxonomy is ready for a
              separately authorized bounded GABRIEL run over the 643-row manifest. Global
              analysis readiness, wage-gap analysis, regressions, and causal claims remain
              closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed" ? (
            <>
              The reviewed 643-row literal mechanism-language registry is accepted as valid
              metadata. Candidate-ID, layer-file, and schema hashes and every scope count
              reconcile; restricted, navigation, and external-lane contamination remain zero.
              The 56-row strict-primary manifest remains narrow and non-analytic. Acceptance
              created no evidence rows or analysis outputs. A separately authorized
              pipeline-stage strategy review may run next; all readiness and promotion gates
              remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed" ? (
            <>
              The accepted 643-row literal mechanism-language registry passed its
              metadata-only review. Candidate-ID, layer-file, and schema hashes and every
              registered scope count reconcile; restricted, navigation, and external-lane
              contamination remain zero. The 56-row strict-primary manifest remains narrow
              and non-analytic. Review created no evidence rows or analysis outputs. A
              separately authorized registry-acceptance step may run next; global and full
              qualitative readiness remain false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed" ? (
            <>
              The QA-passed 643-row literal mechanism-language layer is now accepted and
              registered as a bounded evidence layer. Its candidate, file, and schema hashes
              were reverified; restricted, navigation, and external-lane contamination remain
              zero. The 56-row strict primary subset remains a narrow non-analytic manifest.
              Registration created no evidence rows or analysis outputs. A separately
              authorized registry review is the next allowed step; global readiness remains
              false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_qualitative_usage_layer_qa_review_pass_acceptance_prompt_allowed" ? (
            <>
              The independent QA review verified all 643 authorized literal exact-span rows,
              their authorization, file and schema hashes, provenance, historical/current QA,
              restrictions, and closed causal status. Restricted and navigation contamination
              remain zero; the 56-row strict primary subset remains a narrow non-analytic
              manifest. Quantitative, non-base, reference/control, and conflict lanes remain
              separate. A separately authorized acceptance/registration record is the next
              allowed step; no analysis was performed and global readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_qualitative_usage_layer_materialized_qa_review_allowed" ? (
            <>
              The rollback-safe usage layer contains exactly 643 authorized, unique, literal
              exact-span mechanism rows. Its authorization ID-set hash matches, all rows remain
              explicitly non-analytic and non-causal, and the 56 strict primary matched
              city-cycle rows remain only a narrow manifest. The 116 restricted exact-span rows
              stay quarantined; all 614 ambiguous plus 581 unavailable rows stay navigation-only.
              Quantitative, non-base, reference/control, and residual-conflict lanes remain
              separate. A separately authorized layer QA review is the next allowed step; global
              analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_exact_span_qualitative_usage_review_completed_usage_layer_prompt_allowed" ? (
            <>
              The usage review preserves the 759-row promoted universe and authorizes a future,
              separately approved usage-layer prompt for 643 exact-span rows only. The 116
              restricted exact-span rows remain quarantined, and all 614 ambiguous plus 581
              unavailable rows remain navigation-only. Exact-cycle, controlled-occupation,
              exact-period matched-set, and strict primary subsets contain 453, 438, 77, and 56
              rows respectively. These are evidence-scope contracts, not analysis results;
              global analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_exact_span_qualitative_promotion_completed_usage_review_allowed" ? (
            <>
              The provisional promoted view preserves all 759 exact-span rows with row-level
              eligibility and quarantine fields: 643 rows support limited qualitative use,
              116 exact-span rows remain restricted, and 56 satisfy the complete strict matched
              city-cycle design. The 614 ambiguous and 581 unavailable rows remain separate and
              navigation-only. Quantitative, non-base, reference/control, and unresolved-conflict
              lanes remain separate. A separately authorized usage review is the next allowed
              step; global analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_pipeline_hardening_complete_limited_promotion_allowed" ? (
            <>
              The accelerator verified immutable package and repair hashes, consolidated the
              readiness blockers, and hardened failure, prompt, relay, checkpoint, lane, and
              dashboard guards. The simulation identifies 643 conservative limited-contract
              qualitative rows and 56 rows satisfying the full strict matched-design metadata
              intersection. The 614 ambiguous and 581 unavailable rows remain navigation-only;
              467 cycle, 368 occupation, 1,045 quantitative-exception, and five residual-conflict
              observations remain quarantined. A separately authorized limited promotion is the
              next allowed step; global analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_limited_exact_span_qualitative_readiness_review_completed_pass_with_blockers" ? (
            <>
              The 759-row exact-span tier passed literal-span, identity, and provenance checks,
              but it is not globally analysis-ready. A future, separately authorized promotion
              prompt may prepare only this tier with row-level restrictions: 93 needs-review
              rows, 226 cycle-missing or ambiguous rows, 239 rows without controlled occupation,
              and 16 historical mixed memberships remain restricted. Only 85 rows have exact
              matched-set support for the primary city-by-cycle design. The 614 ambiguous and
              581 unavailable rows remain navigation-only; analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_qualitative_evidence_contract_limited_review_allowed_exact_span_only" ? (
            <>
              The qualitative evidence contract reconciles all 1,954 mechanism rows into three
              disjoint provisional tiers: 759 exact-span coded candidates, 614 ambiguous-span
              navigation rows, and 581 unavailable-span navigation rows. Only the exact tier may
              enter a separately authorized limited readiness review; the other tiers remain
              navigation-only. No PDFs were reopened, all carried-forward lanes are byte-identical,
              and analysis readiness and promotion remain false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_bounded_qualitative_span_disambiguation_partial_additional_repair_required" ? (
            <>
              The exact-only follow-up preserved all 455 prior verified spans and reviewed 1,499
              ambiguous or unavailable rows on 1,011 approved pages across 700 retained PDFs.
              It resolved 277 ambiguous and 27 unavailable rows, raising unique exact QA spans to
              759. Another 614 rows remain ambiguous and 581 unavailable, so the qualitative lane
              remains navigation-only. OCR-later, rendered-image, non-target, and page-text
              persistence counts are zero; analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_bounded_pdf_text_span_capture_partial_additional_repair_required" ? (
            <>
              The hardened local text-layer run accessed exactly 1,223 approved pages across 788
              retained readable PDFs, with zero OCR-later, rendered-image, invalid-pointer, or
              non-target accesses. It captured 1,346 exact single-line literal substrings: 455
              unique-candidate QA passes and 891 explicitly ambiguous matches; 608 rows had no safe literal match.
              The qualitative lane therefore remains navigation-only. Cycle, occupation,
              quantitative, non-base, reference/control, and residual-conflict quarantines are
              unchanged, and analysis readiness remains false pending bounded follow-up.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_bounded_span_residual_repair_blocked_missing_text_support" ? (
            <>
              All 1,954 qualitative page pointers reconcile to retained bounded packet records,
              but those manifests contain no page-text payload, so zero literal spans were
              accepted and the qualitative lane remains navigation-only. Exact structured cycle
              notes raise supported cycles to 1,359 identities and matched coverage to 203
              documents in 91 groups; explicit controlled unit labels raise non-safety subclasses
              to 239. The 862 quantitative candidates, 1,045 exceptions, non-base companion lane,
              reference/control lane, and two residual conflict groups remain preserved. Analysis
              readiness and promotion remain closed pending separately authorized bounded local
              text-layer span capture.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_bounded_schema_followup_partial_additional_repair_required" ? (
            <>
              The bounded follow-up establishes exact cycles for 1,255 identities, 188 documents
              in 84 exact-period matched groups, 72 controlled non-safety subclasses, and durable
              retrieval provenance for all 1,826 identities. Exact-token parsing raises mechanical
              quantitative candidates to 862 while 1,045 rows remain explicit exceptions.
              Qualitative evidence remains navigation-only because dedicated literal spans are
              absent; both residual conflict groups remain quarantined. Analysis readiness,
              promotion, ingestion, codification, wage-gap work, and regression remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_final_provisional_schema_repair_partial_followup_required" ? (
            <>
              A rollback-safe repair layer now supplies one-to-one retained-hash bridges for all
              1,826 documents, lossless non-base lineage columns, deterministic current-active and
              QA semantics, strict quantitative parse statuses, and explicit active versus
              historical mixed membership. Only 387 quantitative rows meet the mechanical parse
              contract; 1,520 remain exceptions. Qualitative evidence remains navigation-only
              because literal evidence spans are absent. Cycle and matched-set metadata remain
              unavailable without inference, so analysis readiness, promotion, ingestion,
              codification, wage-gap work, and regression remain closed.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_final_provisional_schema_readiness_review_completed_hold" ? (
            <>
              The independent schema review preserved all five package ledgers and verified every
              hash, count, active mixed join, duplicate-provenance row, bounded pointer, and
              residual conflict. Analysis-facing promotion remains blocked: raw retained hashes,
              city-unit-cycle matching keys, normalized value/date semantics, unique non-base
              lineage headers, and self-contained provenance require a lossless schema repair.
              Non-base compensation remains a companion lane, both residual groups remain
              quarantined, and analysis readiness, ingestion, codification, wage-gap work, and
              regression remain false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_final_provisional_package_materialized_qa_pass" ? (
            <>
              The final provisional package now contains five separate ledgers copied
              byte-for-byte from the approved corrected shadows. All five input/output hashes,
              1,826 case identities, source and active counts, bounded pointers, duplicate
              provenance, mixed joins, reroutes, and the Wasco repair reconcile. Both residual
              conflict groups remain explicitly unresolved. This is a provisional package only:
              OCR-later documents remain excluded, and ingestion, codification, and analysis
              readiness remain false pending a separate schema/analysis-readiness review.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_final_provisional_merge_prompt_prepared" ? (
            <>
              A fail-closed future merge prompt now names the five corrected shadow ledgers and
              their immutable SHA-256 values. It requires a dry run, separate schemas, full
              provenance preservation, and retention of both explicitly unresolved conflict
              groups. No merge or merged package was created; all 1,826 readable hashes remain
              covered, OCR-later documents remain untouched, and analysis readiness remains false
              until a separately authorized task runs and validates the provisional merge.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_readable_parse_text_1826_independent_bounded_review_completed" ? (
            <>
              Independent bounded review passed {formatNumber(
                textTableCalibrationStatus.readable_parse_text_1826_independent_review_item_count,
              )} checks. Both residual conflict groups were reviewed and remain explicitly unresolved; the corrected provisional layer still contains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative observations, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative mechanisms, {formatNumber(
                textTableCalibrationStatus.mixed_case_count,
              )} mixed cases, {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage observations, and {formatNumber(
                textTableCalibrationStatus.reference_exclusion_case_count,
              )} reference/exclusion cases. Duplicate IDs, invalid page pointers, and base/non-base contamination remain zero. A final provisional merge prompt may be prepared, but no merge occurred and analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_readable_parse_text_1826_targeted_conflict_qa_completed" ? (
            <>
              Targeted QA processed {formatNumber(
                textTableCalibrationStatus.readable_parse_text_1826_targeted_conflict_qa_review_count,
              )} conflict groups, resolving {formatNumber(
                textTableCalibrationStatus.readable_parse_text_1826_targeted_conflict_resolved_count,
              )} and retaining {formatNumber(
                textTableCalibrationStatus.readable_parse_text_1826_targeted_conflict_unresolved_count,
              )} as explicitly unresolved. The corrected provisional layer contains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative observations, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative mechanisms, {formatNumber(
                textTableCalibrationStatus.mixed_case_count,
              )} mixed cases, {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage observations, and {formatNumber(
                textTableCalibrationStatus.reference_exclusion_case_count,
              )} reference/exclusion cases. The unresolved conflict rate is {formatPercent(
                100 * textTableCalibrationStatus.remaining_parse_text_unresolved_conflict_rate,
              )}; duplicate IDs, invalid page pointers, and base/non-base contamination remain zero. All 1,826 readable hashes remain covered, but no final provisional merge occurred and analysis readiness remains false.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_readable_parse_text_1826_materialized_qa_pass" ? (
            <>
              The provisional cumulative layer now covers {formatNumber(
                textTableCalibrationStatus.remaining_parse_text_cumulative_case_count,
              )} unique readable parse-text hashes at {formatPercent(
                100 * textTableCalibrationStatus.remaining_parse_text_live_schema_valid_rate,
              )} case-level schema validity. It contains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative observations, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative mechanisms, {formatNumber(
                textTableCalibrationStatus.mixed_case_count,
              )} mixed cases, {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage observations, and {formatNumber(
                textTableCalibrationStatus.reference_exclusion_case_count,
              )} reference/exclusion cases. Integrity QA passed with zero base/non-base contamination and an unresolved conflict rate of {formatPercent(
                100 * textTableCalibrationStatus.remaining_parse_text_unresolved_conflict_rate,
              )}. Targeted conflict QA is still required before any final provisional merge; this layer is not analysis-ready.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_remaining_parse_text_live_incomplete_825_of_826" ? (
            <>
              The final readable parse-text batch froze {formatNumber(
                textTableCalibrationStatus.remaining_parse_text_selection_count,
              )} unique retained hashes from 827 inventory rows, with one duplicate-hash row resolved deterministically. Its seven-path preflight passed at {formatPercent(
                100 * textTableCalibrationStatus.remaining_parse_text_preflight_schema_valid_rate,
              )}. Live extraction stored {formatNumber(
                textTableCalibrationStatus.remaining_parse_text_live_schema_valid_case_count,
              )} of 826 cases after {formatNumber(
                textTableCalibrationStatus.remaining_parse_text_live_attempt_count,
              )} bounded attempts; {formatNumber(
                textTableCalibrationStatus.remaining_parse_text_live_unresolved_case_count,
              )} education/certification-routing case remains strict-invalid. The corrected 1,000-case seed received zero model calls, and no cumulative 1,826-case ledger or QA result was materialized. A one-case routing repair is required before cumulative QA.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_1000_targeted_qa_completed" ? (
            <>
              Targeted QA processed {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_targeted_qa_review_count,
              )} unresolved routing records and conflict groups without a new extraction or model call. The corrected provisional shadow layer contains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative-mechanism, {formatNumber(
                textTableCalibrationStatus.mixed_case_count,
              )} mixed, {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage, and {formatNumber(
                textTableCalibrationStatus.reference_exclusion_case_count,
              )} reference/exclusion records. Base/non-base contamination is {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_base_nonbase_contamination_count,
              )}; the remaining unresolved conflict rate is {formatPercent(
                100 * textTableCalibrationStatus.compensation_extraction_1000_unresolved_conflict_rate,
              )}. QA passed, and a future provisional run over the remaining unique readable parse-text documents is authorized. These shadow ledgers are not analysis-ready data.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_1000_materialized_qa_blocked" ? (
            <>
              The one-case longevity contract completed the frozen new cohort at 500/500 strict-valid cases without resending the corrected seed or the 499 stored cases. The cumulative provisional layer now contains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative-mechanism, {formatNumber(
                textTableCalibrationStatus.mixed_case_count,
              )} mixed, and {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage records. Integrity QA is blocked by {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_base_nonbase_contamination_count,
              )} possible base/non-base routing records. The unresolved conflict rate is {formatPercent(
                100 * textTableCalibrationStatus.compensation_extraction_1000_unresolved_conflict_rate,
              )}; further scale remains {textTableCalibrationStatus.scale_beyond_1000_recommendation}. These are provisional QA ledgers, not analysis-ready data.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_1000_live_incomplete_499_of_500" ? (
            <>
              The cumulative selection froze {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_selection_count,
              )} retained identities, preserving {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_corrected_seed_count,
              )} corrected seed cases without new model calls and adding {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_new_document_count,
              )} new cases. The repaired six-path preflight achieved {formatPercent(
                100 * textTableCalibrationStatus.compensation_extraction_1000_preflight_schema_valid_rate,
              )} strict semantic-schema validity. Live extraction then stored {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_live_schema_valid_case_count,
              )} of 500 new cases after {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_live_attempt_count,
              )} bounded attempts; {formatNumber(
                textTableCalibrationStatus.compensation_extraction_1000_live_unresolved_case_count,
              )} longevity-routing case remains invalid. No cumulative 1,000-case lanes or QA metrics were materialized. The corrected 500-document QA layer remains the latest complete valid provisional evidence; scaling beyond 1,000 is {textTableCalibrationStatus.scale_beyond_1000_recommendation}.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_500_targeted_qa_completed" ? (
            <>
              Targeted QA processed {formatNumber(
                textTableCalibrationStatus.targeted_qa_review_rows_processed,
              )} review rows, canonicalized {formatNumber(
                textTableCalibrationStatus.targeted_qa_duplicate_observations_canonicalized,
              )} duplicate observations, and rerouted {formatNumber(
                textTableCalibrationStatus.targeted_qa_quantitative_reroutes,
              )} quantitative records to the non-base-wage shadow lane. The corrected provisional layer retains {formatNumber(
                textTableCalibrationStatus.quantitative_observation_count,
              )} active quantitative, {formatNumber(
                textTableCalibrationStatus.qualitative_mechanism_observation_count,
              )} qualitative-mechanism, and {formatNumber(
                textTableCalibrationStatus.non_base_wage_observation_count,
              )} non-base-wage observations. The unresolved conflict rate is {formatPercent(
                100 * textTableCalibrationStatus.targeted_qa_unresolved_conflict_rate,
              )}; scale QA passed and the recommendation is {textTableCalibrationStatus.scale_1000_recommendation}. These remain provisional QA ledgers, not analysis-ready data.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "compensation_extraction_500_provisional_completed" ? (
            <>
              The frozen run completed {formatNumber(
                textTableCalibrationStatus.compensation_extraction_case_count,
              )} documents with {formatPercent(
                100 * textTableCalibrationStatus.compensation_extraction_schema_valid_rate,
              )} final case-level schema validity. Its provisional ledgers contain{" "}
              {formatNumber(textTableCalibrationStatus.quantitative_observation_count)} quantitative,
              {" "}{formatNumber(textTableCalibrationStatus.qualitative_mechanism_observation_count)} qualitative-mechanism,
              and {formatNumber(textTableCalibrationStatus.non_base_wage_observation_count)} non-base-wage observations across{" "}
              {formatNumber(textTableCalibrationStatus.mixed_case_count)} mixed cases. Integrity QA passed, but{" "}
              {formatNumber(textTableCalibrationStatus.compensation_extraction_conflict_groups)} potential quantitative conflict groups require targeted review; scaling is{" "}
              {textTableCalibrationStatus.scale_1000_recommendation}. These are provisional QA ledgers, not an analysis-ready dataset.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "auto_gabriel_gate3_compensation_completed" ? (
            <>
              Gate 3 classified{" "}
              {formatNumber(textTableCalibrationStatus.auto_gate_case_count)}
              {" "}bounded cases with{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.gate3_schema_valid_rate,
              )}
              {" "}schema-valid image-assisted GABRIEL responses. It found{" "}
              {formatNumber(
                textTableCalibrationStatus
                  .gate3_compensation_evidence_category_counts
                  ?.mixed_quant_qual_ready,
              )}
              {" "}mixed, {formatNumber(
                textTableCalibrationStatus
                  .gate3_compensation_evidence_category_counts
                  ?.qual_mechanism_ready,
              )}{" "}qualitative-mechanism, and {formatNumber(
                textTableCalibrationStatus
                  .gate3_compensation_evidence_category_counts
                  ?.quant_table_ready,
              )}{" "}quantitative-table cases. The computed decision is{" "}
              {textTableCalibrationStatus.extraction_decision}; this authorizes
              a future 500-document compensation-evidence extraction design,
              not an extraction run in this task. No final observations, OCR,
              ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "auto_gabriel_gate2_completed" ? (
            <>
              Gate 2 completed{" "}
              {formatNumber(textTableCalibrationStatus.auto_gate_case_count)}
              {" "}bounded cases with{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.gate2_schema_valid_rate,
              )}
              {" "}schema-valid GABRIEL responses. It retained{" "}
              {formatNumber(
                textTableCalibrationStatus.gate2_auto_gate_label_counts
                  ?.extraction_ready_high_confidence,
              )}
              {" "}high-confidence and{" "}
              {formatNumber(
                textTableCalibrationStatus.gate2_auto_gate_label_counts
                  ?.extraction_ready_with_schema_update,
              )}
              {" "}schema-update-ready rows. Original likely/p1 readiness was{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.gate2_likely_p1_ready_rate,
              )}
              , and the candidate-bearing wrong-page rate was{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.gate2_wrong_page_rate,
              )}
              . The computed decision is{" "}
              {textTableCalibrationStatus.extraction_decision}: neither the
              500-document nor smaller extraction run is authorized. No final
              wage values, OCR, ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "auto_gabriel_gate1_completed" ? (
            <>
              The bounded automated gate completed{" "}
              {formatNumber(textTableCalibrationStatus.auto_gate_case_count)}
              {" "}cases with{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.gabriel_schema_valid_rate,
              )}
              {" "}schema-valid GABRIEL responses. It retained{" "}
              {formatNumber(
                textTableCalibrationStatus.auto_gate_label_counts
                  ?.extraction_ready_high_confidence,
              )}
              {" "}high-confidence and{" "}
              {formatNumber(
                textTableCalibrationStatus.auto_gate_label_counts
                  ?.extraction_ready_with_schema_update,
              )}
              {" "}schema-update-ready rows; the candidate-page wrong-page
              rate was{" "}
              {formatPercent(100 * textTableCalibrationStatus.wrong_page_rate)}
              . The computed decision is{" "}
              {textTableCalibrationStatus.extraction_decision}: neither the
              500-document nor smaller extraction run is authorized. No final
              wage values, OCR, ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "independent_adjudication_packet_prepared" ? (
            <>
              A blinded packet now covers{" "}
              {formatNumber(
                textTableCalibrationStatus.adjudication_cases_prepared,
              )}
              {" "}calibration cases with{" "}
              {formatNumber(
                textTableCalibrationStatus.adjudication_rendered_page_count,
              )}
              {" "}bounded local page aids. Human review has not started, and
              the packet excludes REVIEW1/REVIEW2 labels and prior extraction
              actions. REVIEW2 remains{" "}
              {textTableCalibrationStatus.prior_extraction_decision}; neither
              the 500-document nor smaller extraction run is authorized.
              Independent human adjudication is next. No OCR, wage extraction,
              ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "refined_review2_completed" ? (
            <>
              All{" "}
              {formatNumber(textTableCalibrationStatus.reviewed_rows)}
              {" "}rows completed the assisted refined visual gate, but the
              blinded rendered-page challenge agreed on only{" "}
              {formatPercent(
                100 * textTableCalibrationStatus.visual_qa_agreement_rate,
              )}
              {" "}of material decisions. The strict likely-signal visual
              confirmation rate was{" "}
              {formatPercent(
                100 *
                  textTableCalibrationStatus
                    .likely_signal_visual_confirmation_rate,
              )}
              {" "}and the candidate-page wrong-page rate was{" "}
              {formatPercent(100 * textTableCalibrationStatus.wrong_page_rate)}
              . The decision is{" "}
              {textTableCalibrationStatus.extraction_decision}: neither a
              500-document nor smaller extraction run is authorized.
              Independent human adjudication and navigation/table-rule
              refinement are next. No OCR, wage extraction, ingestion, or
              codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "refinement_prepared_after_failed_review" ? (
            <>
              The prior 150-row assisted review remains a failed extraction
              gate: its rendered-page challenge disagreed in all five checked
              cases. The refined schema now separates wage prose, pay-number
              language, visually supported table structure, non-wage tables,
              and contents/appendix navigation. The same 150 rows must be
              re-reviewed under the refined visual gate before extraction;
              the 500-document extraction run remains prohibited. No OCR,
              wage extraction, ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "subset1_reviewed" ? (
            <>
              All{" "}
              {formatNumber(textTableCalibrationStatus.reviewed_rows)}
              {" "}rows received bounded Codex-assisted local adjudication:{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_present_label_counts
                  ?.yes,
              )}
              {" "}yes,{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_present_label_counts
                  ?.maybe,
              )}
              {" "}maybe, and{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_present_label_counts
                  ?.no,
              )}
              {" "}no wage-table-presence labels. The gate is{" "}
              {textTableCalibrationStatus.calibration_pass_status};{" "}
              {formatNumber(
                textTableCalibrationStatus.calibration_status_counts
                  ?.needs_second_review,
              )}
              {" "}rows still need second review. This is not independent
              human precision or final wage extraction. A rendered-page
              challenge found material disagreement in all five checked
              cases, so detector/schema refinement is next. No OCR,
              ingestion, or codification occurred.
            </>
          ) : textTableCalibrationStatus.calibration_phase ===
          "subset1_prepared_not_reviewed" ? (
            <>
              The review packet contains{" "}
              {formatNumber(textTableCalibrationStatus.calibration_subset_rows)}
              {" "}unreviewed rows:{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_signal_counts?.likely,
              )}
              {" "}likely,{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_signal_counts?.possible,
              )}
              {" "}possible, and{" "}
              {formatNumber(
                textTableCalibrationStatus.wage_table_signal_counts?.unlikely,
              )}
              {" "}unlikely heuristic signals. It spans{" "}
              {formatNumber(textTableCalibrationStatus.unique_states)}
              {" "}states or districts and{" "}
              {formatNumber(
                textTableCalibrationStatus.unique_municipalities,
              )}
              {" "}municipalities. No PDFs were opened while preparing it;
              precision has not been measured, and no wage extraction, OCR,
              ingestion, or codification occurred.
            </>
          ) : (
            <>
              The durable heuristic detection layer still requires a
              stratified manual calibration subset before any wage-table
              extraction pilot.
            </>
          )}
        </p>
      </div>
      <p className="panel-note">
        <strong>Historical URL-routing context:</strong>{" "}
        {routingMerged
          ? fullRouting
            ? `No URL-bearing queue identities remain unrouted. The next step is content relevance and extraction-readiness triage, not another broad URL-routing round. The ${verificationStatus.future_bulk_verification_profile} profile is reserved for future queues with new unrouted identities.`
            : round2Collected
            ? "Round 2 selected every remaining URL-bearing queue identity; the durable ledger still contains only the 2,250 merged Round 1 rows until a separate serial merge."
            : `${formatNumber(verificationStatus.scheduled_verification_rows_remaining_estimate)} scheduled and ${formatNumber(verificationStatus.full_url_bearing_rows_remaining_estimate)} total URL-bearing rows remain.`
          : `${verificationStatus.scheduled_pool_estimated_rounds} nominal rounds cover the scheduled pool; ${verificationStatus.full_backlog_estimated_rounds} cover every URL-bearing candidate row.`}
      </p>
      <p className="panel-note">
        {phase.broad_state_4x2500_pdf_text_readiness_available
          ? `Current next task: BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30 over exactly ${formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} readiness-approved retained files in four staggered lanes; OCR remains excluded.`
          : readiness.promotion_gate}
      </p>
    </section>
  );
}

export function StateYieldPanel({ yieldData, operations }) {
  const leaders = yieldData.state_yield_leaderboard.slice(0, 10);
  return (
    <section className="panel hub-section" id="state-yield" aria-labelledby="state-yield-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Historical state yield and learning</p>
          <h2 id="state-yield-title">Archived discovery yield, with sample warnings</h2>
        </div>
        <span className="quiet-label">Minimum {yieldData.leaderboard_minimum_successful_scouts} successful scouts</span>
      </div>

      <div className="yield-grid">
        {leaders.map((state, index) => (
          <article key={state.state}>
            <span className="yield-rank">{index + 1}</span>
            <div>
              <h3>{state.state_name}</h3>
              <p>{formatNumber(state.successful_scout_count)} successful scouts · {state.sample_confidence} confidence</p>
            </div>
            <dl>
              <div><dt>Positive</dt><dd>{formatPercent(100 * state.candidate_positive_rate)}</dd></div>
              <div><dt>Rows / covered</dt><dd>{decimal(state.candidate_rows_per_covered_municipality, 2)}</dd></div>
            </dl>
          </article>
        ))}
      </div>
      <div className="learning-note">
        <p><strong>Learning rule:</strong> {operations.priority_refresh_recommendation}</p>
        <p>{yieldData.disclaimer} These rates describe discovery behavior, not source quality or wage outcomes.</p>
      </div>
    </section>
  );
}

export function ReportsLibrary({ reportsIndex, reportAssets }) {
  return (
    <section className="panel hub-section reports-library" id="reports" aria-labelledby="reports-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reports library</p>
          <h2 id="reports-title">PI reports and durable project checkpoints</h2>
        </div>
        <StatusPill tone="verified">Current report published</StatusPill>
      </div>

      <div className="report-library-grid">
        {reportsIndex.reports.map((report) => (
          <article className="report-card" key={report.id}>
            <div className="report-card-topline">
              <span>{report.current ? "Current · " : report.historical ? "Historical · " : ""}{report.report_type}</span>
              <time dateTime={report.date}>{report.date}</time>
            </div>
            <h3>{report.title}</h3>
            <p className="report-checkpoint">{report.checkpoint}</p>
            <p>{report.summary}</p>
            {report.scope_metrics ? (
              <div className="report-metrics">
                {report.scope_metrics.map((metric) => (
                  <span key={metric.label}><strong>{formatNumber(metric.value)}</strong> {metric.label}</span>
                ))}
              </div>
            ) : (
              <div className="report-metrics">
                <span><strong>{formatNumber(report.metrics_snapshot.scout_covered)}</strong> covered</span>
                <span><strong>{formatNumber(report.metrics_snapshot.candidate_queue_rows)}</strong> leads</span>
                <span><strong>{formatNumber(report.metrics_snapshot.tier1_eligible)}</strong> Tier 1</span>
              </div>
            )}
            <div className="tag-list">{report.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            <a className="primary-link" href={report.href ?? reportAssets[report.id]} target="_blank" rel="noreferrer">
              {report.link_label ?? "Open report PDF"}
            </a>
          </article>
        ))}
        <article className="report-card">
          <div className="report-card-topline"><span>Completed evidence artifact</span><span>2026-07-27</span></div>
          <h3>Bounded Tier C evidence memo supplement</h3>
          <p>
            The supplement integrates 140 valid aggregate ratings and excludes all 19 quarantines. It closes the
            targeted Tier C pass while keeping every finding documentary, bounded, and globally analysis-closed.
          </p>
          <a className="primary-link" href="https://github.com/dkyaya/gabriel-wages/blob/main/docs/analysis/compensation_extraction/BOUNDED-TIER-C-EVIDENCE-MEMO-SUPPLEMENT-140-RATING-SUMMARY-2026-07-27/bounded_tier_c_evidence_memo_supplement.md" target="_blank" rel="noreferrer">Open completed memo supplement</a>
        </article>
        <article className="report-card report-card-planned">
          <div className="report-card-topline"><span>Forthcoming</span><span>Next authorized stage</span></div>
          <h3>Combined broad PDF/text-layer readiness</h3>
          <p>Next bounded stage for checking only retained local source files by path, size, hash, file type, and text-layer eligibility without OCR, rendering, or evidence extraction.</p>
          <StatusPill tone="future">Readiness next</StatusPill>
        </article>
      </div>
      <p className="panel-note">{reportsIndex.disclaimer}</p>
    </section>
  );
}

export function MethodologyDefinitions() {
  const definitions = [
    ["Municipality searched", "A request returned a parseable candidate list or a valid empty result."],
    ["Scout-covered", "A successful parseable scout outcome; it does not mean a source was verified."],
    ["Candidate row", "One possible URL or document lead queued for later review. A municipality can have several."],
    ["Parseable-empty", "A completed scout response with no candidates; not proof that no source exists."],
    ["Failure-only", "A request without a usable result, retained outside successful coverage for possible retry."],
    ["Priority tier", "A deterministic research-operations ranking used to schedule future scouting."],
    ["Verified source", "A lead whose employer, unit, provenance, dates, type, access, and relevance have been checked."],
    ["Retained source", "A downloaded, hashed local file that has passed bounded source review. It is not extracted, rated, or analysis-ready."],
    ["Bounded co-location scaffold", "A same-source pairing of quantitative direct text and qualitative mechanism evidence; it does not establish causation or a wage gap."],
    ["Text-layer readiness", "A file-level eligibility review for a later extraction pass. It does not itself extract text or run OCR."],
    ["Analysis-ready", "Matched city-cycle safety/non-safety evidence with validated wage fields and provenance."],
  ];

  return (
    <section className="panel hub-section" id="methodology" aria-labelledby="methodology-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Methodology and definitions</p>
          <h2 id="methodology-title">Keep the evidence stages separate</h2>
        </div>
      </div>
      <dl className="definition-grid">
        {definitions.map(([term, definition]) => (
          <div key={term}><dt>{term}</dt><dd>{definition}</dd></div>
        ))}
      </dl>
      <p className="methodology-caveat">
        Scouting tiers and yield measures are operational. The dashboard does not report verified wage gaps,
        mechanism effects, state findings, or causal estimates.
      </p>
    </section>
  );
}

export function NextStepsPanel({ priority, phase }) {
  const readinessComplete = phase.broad_state_4x2500_pdf_text_readiness_available;
  const broadDownloadsComplete = phase.broad_state_4x2500_source_review_download_available;
  const downloadsComplete = broadDownloadsComplete || phase.combined_source_review_download_available;
  const retainedCount = broadDownloadsComplete
    ? phase.broad_state_4x2500_source_review_retained_count
    : phase.source_review_download_retained_count;
  const reviewedCount = broadDownloadsComplete
    ? phase.broad_state_4x2500_source_review_queue_count
    : phase.source_review_download_attempted_count;
  return (
    <section className="panel hub-section next-steps-panel" id="next-steps" aria-labelledby="next-steps-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Next steps</p>
          <h2 id="next-steps-title">{readinessComplete ? "Run four-lane text extraction over readiness-approved sources" : downloadsComplete ? "Run bounded PDF/text-layer readiness over retained local sources" : "Run bounded source review from the locked reviewed queue"}</h2>
        </div>
        <StatusPill tone="scout">PI-aligned strategy</StatusPill>
      </div>
      <div className="next-step-grid">
        <article className="recommended-step">
          <span>Immediate</span>
          <h3>{readinessComplete ? "Authorize the exact readiness-approved extraction queue" : downloadsComplete ? "Authorize a bounded retained-file readiness pass" : "Authorize a bounded source-review/download wave"}</h3>
          <p>{readinessComplete
            ? `Use only the ${formatNumber(phase.broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count)} approved files in four isolated lanes; extracted text stays in ignored local storage and OCR remains excluded.`
            : downloadsComplete
            ? `Use only the ${formatNumber(retainedCount)} unique retained hashed local sources; revalidate path, size, and SHA-256 and do not access URLs or redownload.`
            : `Use only the locked ${formatNumber(phase.source_review_ready_count)}-row queue, beginning with ${formatNumber(phase.source_review_ready_high_count)} high-priority candidates while preserving geography and source-family diversity.`}</p>
        </article>
        <article>
          <span>Completed verification scope</span>
          <h3>{formatNumber(phase.verification_completed_count)} locator outcomes</h3>
          <p>{formatNumber(phase.verification_verified_reachable_count)} locators are reachable metadata leads. They have not been downloaded, source-reviewed, extracted, rated, or ingested.</p>
        </article>
        <article>
          <span>{downloadsComplete ? "Completed source review/download" : "Completed candidate review"}</span>
          <h3>{formatNumber(downloadsComplete ? reviewedCount : phase.candidate_review_universe_size)} rows</h3>
          <p>{downloadsComplete
            ? `${formatNumber(retainedCount)} unique files were retained and hashed (${formatNumber(phase.broad_state_4x2500_source_review_retained_pdf_count)} PDF, ${formatNumber(phase.broad_state_4x2500_source_review_retained_html_count)} HTML, ${formatNumber(phase.broad_state_4x2500_source_review_retained_other_count)} other). No text, tables, spans, evidence, or analytical quantities were extracted.`
            : "The review used only committed snippets, candidate metadata, and verification results. No source URLs or document contents were opened."}</p>
        </article>
      </div>
      <p className="panel-note">
        Historical discovery, verification, and candidate-review stages remain available above for provenance only. The current next task is
        {readinessComplete ? " BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30 in four staggered lanes" : downloadsComplete ? " a separately authorized retained-file PDF/text-layer readiness pass" : " a separately authorized bounded source-review/download wave"}; global analysis readiness remains false.
      </p>
    </section>
  );
}
