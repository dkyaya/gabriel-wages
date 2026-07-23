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
        <h2>Verification before findings</h2>
        <p>
          The recommended next gate is a 50–100-row verification pilot. No project-wide verified or
          analysis-ready scout evidence exists yet.
        </p>
      </article>
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
          <h2 id="priority-tier-title">Where ordinary discovery should go next</h2>
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

export function ScoutOperationsPanel({ operations, runtime }) {
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
          <h3>Four-wave runtime trend</h3>
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
            <li>One serialized coordinator process; no concurrent live workers.</li>
            <li>Stronger no-search, hosted-search, and one-row preflight gate.</li>
            <li>Compact prompts with exact identity and source-stage guardrails.</li>
            <li>Five deterministic municipality-specific query hints.</li>
            <li>Adaptive sleep/backoff, terminal artifacts, and fresh-directory resume lineage.</li>
          </ul>
          <p className="panel-note">{operations.disclaimer}</p>
        </div>
      </div>
    </section>
  );
}

export function VerificationPipeline({ candidateSummary, readiness }) {
  const candidateRows = candidateSummary.totals.candidate_rows;
  const stages = [
    ["Candidate lead", formatNumber(candidateRows), "Collected", "scout"],
    ["Verified source", "Not started project-wide", "Next gate", "future"],
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
        <StatusPill tone="future">Verification pilot planned</StatusPill>
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
          <p className="eyebrow">Recommended next gate</p>
          <h3>Verify a stratified 50–100-row candidate sample</h3>
        </div>
        <p>
          Confirm exact employer and unit, source owner, document type, dates, completeness, duplicate status,
          wage-field extractability, and matched-cycle potential before ingestion or empirical use.
        </p>
      </div>
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

export function NextStepsPanel({ priority }) {
  return (
    <section className="panel hub-section next-steps-panel" id="next-steps" aria-labelledby="next-steps-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Next steps</p>
          <h2 id="next-steps-title">The immediate decision is breadth versus verification</h2>
        </div>
        <StatusPill tone="calibration">PI decision point</StatusPill>
      </div>
      <div className="next-step-grid">
        <article className="recommended-step">
          <span>Recommended</span>
          <h3>Approve a 50–100-row verification pilot</h3>
          <p>Measure lead conversion and matched-cycle potential before substantially expanding the queue.</p>
        </article>
        <article>
          <span>Optional breadth</span>
          <h3>Continue ordinary Tier 1 scouting</h3>
          <p>{formatNumber(priority.totals.tier_1_eligible)} eligible Tier 1 municipalities remain after the current checkpoint.</p>
        </article>
        <article>
          <span>Separate retry lane</span>
          <h3>Retry failure-only municipalities later</h3>
          <p>Keep {formatNumber(priority.totals.failure_only_retry_targets)} transport/empty-response targets outside ordinary discovery.</p>
        </article>
      </div>
    </section>
  );
}
