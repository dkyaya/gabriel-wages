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

export function ProjectOrientation({ totals, priorityTotals, report }) {
  return (
    <section className="project-orientation" aria-label="Collected current and forthcoming project status">
      <article>
        <p className="eyebrow">Collected</p>
        <h2>National discovery infrastructure</h2>
        <p>
          {formatNumber(totals.scout_covered_municipalities)} municipalities have a successful parseable scout
          outcome and {formatNumber(totals.candidate_rows)} URL-bearing candidate leads are queued.
        </p>
      </article>
      <article>
        <p className="eyebrow">Current</p>
        <h2>{report.checkpoint}</h2>
        <p>
          The dashboard is frozen at the latest merged checkpoint. Priority tiers cover the full
          {` ${formatNumber(priorityTotals.municipality_universe)}-government`} universe.
        </p>
      </article>
      <article>
        <p className="eyebrow">Forthcoming</p>
        <h2>Verify, extract, and build matched evidence</h2>
        <p>
          The approximately 2,000-covered checkpoint is exceeded. Broad scouting is paused while
          the project begins the downstream verification and extraction cycle.
        </p>
      </article>
    </section>
  );
}

export function ProjectPhasePanel({ phase }) {
  const progress = Math.min(100, Math.max(0, phase.progress_percentage));
  return (
    <section className="panel hub-section phase-panel" id="project-phase" aria-labelledby="project-phase-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Project phase</p>
          <h2 id="project-phase-title">Post-Checkpoint Verification Routing</h2>
        </div>
        <StatusPill tone="scout">
          {formatNumber(phase.current_scout_covered)} of {formatNumber(phase.checkpoint_target_scout_covered)}
        </StatusPill>
      </div>

      <div className="phase-progress" aria-label={`${progress}% of the scout-coverage checkpoint reached`}>
        <div className="phase-progress-label">
          <strong>{formatNumber(phase.current_scout_covered)} scout-covered</strong>
          <span>{phase.progress_percentage}% of the approximately {formatNumber(phase.checkpoint_target_scout_covered)} checkpoint; target exceeded by {formatNumber(phase.checkpoint_margin)}</span>
        </div>
        <div className="phase-progress-track" aria-hidden="true">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="phase-metrics">
        <div><span>Checkpoint margin</span><strong>+{formatNumber(phase.checkpoint_margin)}</strong></div>
        <div><span>Broad scouting</span><strong>Paused</strong></div>
        <div><span>Candidate leads</span><strong>{formatNumber(phase.current_candidate_queue_rows)}</strong></div>
        <div><span>Candidate-positive</span><strong>{formatNumber(phase.current_candidate_positive_municipalities)}</strong></div>
        <div><span>Failure-only lane</span><strong>{formatNumber(phase.current_failure_only_municipalities)}</strong></div>
      </div>

      <div className="phase-next">
        <div>
          <p className="eyebrow">Current transition</p>
          <h3>Begin the downstream evidence cycle</h3>
        </div>
        <ol>
          <li>Verification</li>
          <li>Extraction</li>
          <li>Ingestion</li>
          <li>Source rating</li>
          <li>Descriptive analysis</li>
        </ol>
        <StatusPill tone="future">Regressions deferred</StatusPill>
      </div>
      <p className="panel-note">
        Candidate rows remain unverified, the checkpoint is a workflow pause point rather than an
        evidentiary threshold, and ordinary discovery remains separate from failure-only retries.
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
          <p className="eyebrow">Scouting priority tiers</p>
          <h2 id="priority-tier-title">Current priorities while discovery is paused</h2>
        </div>
        <StatusPill tone="calibration">Operational heuristic</StatusPill>
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
          <p className="eyebrow">Scout operations</p>
          <h2 id="operations-title">A faster, bounded, auditable workflow</h2>
        </div>
        <StatusPill tone="scout">Latest wave complete</StatusPill>
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
    ["Candidate lead", formatNumber(candidateRows), "Collected", "scout"],
    [
      "Verified-source routing",
      routingMerged ? formatNumber(verificationStatus.rows_verified_routing_total) : "Not started project-wide",
      fullRouting ? "Full queue routed" : routingMerged ? "Round 1 merged" : "Next gate",
      routingMerged ? "scout" : "future",
    ],
    ["Ingested source", "Not integrated", "Future", "future"],
    ["Codified evidence", "Prior corpus separate", "Future", "calibration"],
    ["Analysis-ready evidence", "Not available", "Future", "future"],
  ];

  return (
    <section className="panel hub-section" id="verification" aria-labelledby="verification-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Verification pipeline</p>
          <h2 id="verification-title">From discovered lead to analysis-ready evidence</h2>
        </div>
        <StatusPill tone={routingMerged ? "scout" : "future"}>
          {round2Collected
            ? "Round 2 remainder collected; merge pending"
            : fullRouting
              ? "Full candidate URL routing merged"
            : routingMerged
              ? "Round 1 3×750 routing merged"
              : "Live path ready; verification not started"}
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
          <p className="eyebrow">Next phase after scale-up</p>
          <h3>Verify, extract, ingest, rate, and analyze descriptively</h3>
        </div>
        <p>
          {routingMerged ? (
            <>
              {fullRouting ? (
                <>
                  Round 1 routed {formatNumber(verificationStatus.round1_rows_verified_routing_total)}
                  {" "}rows and Round 2 routed {formatNumber(verificationStatus.round2_rows_verified_routing_total)}
                  {" "}rows. Together they cover {formatNumber(verificationStatus.rows_verified_routing_total)}
                  {" "}/ {formatNumber(verificationStatus.total_url_bearing_candidate_rows)} candidate URLs;
                  {" "}{formatPercent(verificationStatus.cumulative_reachable_or_reused_rate)}
                  {" "}were reachable or reused.
                </>
              ) : (
                <>
                  Round 1 routed {formatNumber(verificationStatus.rows_verified_routing_total)} candidate rows:
                  {" "}{formatPercent(verificationStatus.reachable_or_reused_rate)} were reachable or reused.
                </>
              )}
              {round2Collected ? (
                <>
                  {" "}Round 2 has {formatNumber(verificationStatus.round2_terminal_rows)} terminal,
                  audited outcomes ({formatPercent(verificationStatus.round2_reachable_or_reused_rate)}
                  reachable or reused), but those outcomes are not yet in the durable routing ledger.
                </>
              ) : null}
              Ingestion, employer/unit content review, wage extraction, and wage-gap analysis have not started.
            </>
          ) : (
            <>
              Live verification is implemented behind bounded fetch limits. The complete{" "}
              {formatNumber(verificationStatus.total_url_bearing_candidate_rows)}-row backlog is mapped,
              but no candidate URL has been opened yet.
            </>
          )}
        </p>
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
            {sourceReviewStatus.source_review_phase ===
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
          {sourceReviewStatus.source_review_phase ===
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
      <p className="panel-note">
        <strong>{routingMerged ? "Remaining routing estimate:" : "Coverage plan:"}</strong>{" "}
        {routingMerged
          ? fullRouting
            ? `No URL-bearing queue identities remain unrouted. The next step is content relevance and extraction-readiness triage, not another broad URL-routing round. The ${verificationStatus.future_bulk_verification_profile} profile is reserved for future queues with new unrouted identities.`
            : round2Collected
            ? "Round 2 selected every remaining URL-bearing queue identity; the durable ledger still contains only the 2,250 merged Round 1 rows until a separate serial merge."
            : `${formatNumber(verificationStatus.scheduled_verification_rows_remaining_estimate)} scheduled and ${formatNumber(verificationStatus.full_url_bearing_rows_remaining_estimate)} total URL-bearing rows remain.`
          : `${verificationStatus.scheduled_pool_estimated_rounds} nominal rounds cover the scheduled pool; ${verificationStatus.full_backlog_estimated_rounds} cover every URL-bearing candidate row.`}
      </p>
      <p className="panel-note">{readiness.promotion_gate}</p>
    </section>
  );
}

export function StateYieldPanel({ yieldData, operations }) {
  const leaders = yieldData.state_yield_leaderboard.slice(0, 10);
  return (
    <section className="panel hub-section" id="state-yield" aria-labelledby="state-yield-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">State yield and learning</p>
          <h2 id="state-yield-title">Observed discovery yield, with sample warnings</h2>
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
              <span>{report.report_type}</span>
              <time dateTime={report.date}>{report.date}</time>
            </div>
            <h3>{report.title}</h3>
            <p className="report-checkpoint">{report.checkpoint}</p>
            <p>{report.summary}</p>
            <div className="report-metrics">
              <span><strong>{formatNumber(report.metrics_snapshot.scout_covered)}</strong> covered</span>
              <span><strong>{formatNumber(report.metrics_snapshot.candidate_queue_rows)}</strong> leads</span>
              <span><strong>{formatNumber(report.metrics_snapshot.tier1_eligible)}</strong> Tier 1</span>
            </div>
            <div className="tag-list">{report.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            <a className="primary-link" href={reportAssets[report.id]} target="_blank" rel="noreferrer">
              Open report PDF
            </a>
          </article>
        ))}
        <article className="report-card report-card-planned">
          <div className="report-card-topline"><span>Forthcoming</span><span>After PI decision</span></div>
          <h3>Verification pilot report</h3>
          <p>
            Planned reporting home for verified-source conversion, provenance, unit/source classification,
            matched-cycle potential, and ingestion readiness.
          </p>
          <StatusPill tone="future">Not yet available</StatusPill>
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
  return (
    <section className="panel hub-section next-steps-panel" id="next-steps" aria-labelledby="next-steps-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Next steps</p>
          <h2 id="next-steps-title">Transition from discovery to verified evidence</h2>
        </div>
        <StatusPill tone="scout">PI-aligned strategy</StatusPill>
      </div>
      <div className="next-step-grid">
        <article className="recommended-step">
          <span>Immediate</span>
          <h3>Authorize the first scaled verification round</h3>
          <p>The first 750 candidate rows are locked across three 250-row lanes. Run live verification only under separate authorization, then audit before any serial ledger merge.</p>
        </article>
        <article>
          <span>Checkpoint reached</span>
          <h3>{formatNumber(phase.current_scout_covered)} scout-covered municipalities</h3>
          <p>The target is exceeded by {formatNumber(phase.checkpoint_margin)}. Do not run another broad discovery wave without explicit authorization.</p>
        </article>
        <article>
          <span>Downstream cycle</span>
          <h3>Run the downstream cycle</h3>
          <p>Verify, extract, ingest, rate sources, calculate descriptive gaps only from validated matched data, and document mechanism correlations. Regressions come later.</p>
        </article>
      </div>
      <p className="panel-note">
        {formatNumber(priority.totals.tier_1_eligible)} ordinary Tier 1 municipalities remain eligible;
        {" "}{formatNumber(priority.totals.failure_only_retry_targets)} failure-only targets remain in a separate lane.
      </p>
    </section>
  );
}
