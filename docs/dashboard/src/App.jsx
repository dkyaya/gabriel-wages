import { useEffect, useMemo, useState } from "react";
import stateSummary from "../data/state_summary.json";
import candidateSummary from "../data/candidate_queue_summary.json";
import projectPhaseSummary from "../data/project_phase_summary.json";
import reportsIndex from "../data/reports_index.json";
import { NationalMap } from "./components/NationalMap.jsx";
import { PrintableStateReport } from "./components/PrintableStateReport.jsx";
import { StatusPill, formatNumber, formatPercent } from "./components/ui.jsx";

const DEFAULT_STATE = "CA";

function routeFromHash() {
  const match = window.location.hash.match(/^#\/state\/([A-Z]{2})(\/report)?$/);
  return { state: match?.[1] ?? DEFAULT_STATE, view: match?.[2] ? "report" : "dashboard" };
}

function label(value) {
  return String(value ?? "").replaceAll("_", " ");
}

function countFor(key) {
  return projectPhaseSummary[key] ?? 0;
}

function dominantDirection(counts = {}) {
  const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return ranked[0] ? label(ranked[0][0]) : "No rated direction";
}

function mechanismRows() {
  const source = projectPhaseSummary.broad_state_4x2500_ingested_mechanism_clusters
    ?? projectPhaseSummary.broad_state_4x2500_mechanism_summaries
    ?? {};
  return Object.entries(source)
    .filter(
      ([name]) =>
        ![
          "weak_or_no_claim_support",
          "weak_or_no_claim_support_strength",
          "weak_context_exclusion",
        ].includes(name),
    )
    .map(([name, item]) => ({ name, ...item }))
    .sort((a, b) => (b.supported_record_count ?? b.report_ready_count ?? 0) - (a.supported_record_count ?? a.report_ready_count ?? 0))
    .slice(0, 6);
}

function CompactStateContext({ state, onOpenReport }) {
  const unavailable = state.coverage_rate_status === "coverage_rate_unavailable";
  return (
    <aside className="pi-state-context" aria-live="polite">
      <div>
        <p className="eyebrow">Selected geography</p>
        <h3>{state.state_name}</h3>
      </div>
      <dl>
        <div><dt>Scout coverage rate</dt><dd>{unavailable ? "Unavailable" : formatPercent(state.scout_coverage_rate)}</dd></div>
        <div><dt>Coverage context</dt><dd>{unavailable ? "Denominator unavailable" : `${formatNumber(state.total_scout_coverage_count)} / ${formatNumber(state.municipality_universe)}`}</dd></div>
      </dl>
      <p>Coverage describes where scouting ran. It does not measure evidence quality, wage differences, or causation.</p>
      <button className="text-button" type="button" onClick={onOpenReport}>Open historical state detail</button>
    </aside>
  );
}

function App() {
  const [route, setRoute] = useState(routeFromHash);

  useEffect(() => {
    const handleHashChange = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const selected = useMemo(
    () => stateSummary.states.find((item) => item.state === route.state) ?? stateSummary.states[0],
    [route.state],
  );
  const selectedQueue = candidateSummary.by_state.find((item) => item.state === selected.state);
  const currentReport = reportsIndex.reports.find((report) => report.current) ?? reportsIndex.reports[0];
  const mechanisms = mechanismRows();
  const totals = stateSummary.totals;
  const nationalRate = totals.municipality_universe
    ? (totals.scout_covered_municipalities / totals.municipality_universe) * 100
    : null;

  function chooseState(code) {
    window.location.hash = `/state/${code}`;
    setRoute({ state: code, view: "dashboard" });
  }

  if (route.view === "report") {
    return (
      <PrintableStateReport
        state={selected}
        queue={selectedQueue}
        metadata={stateSummary.metadata}
        limitations={stateSummary.metadata.limitations}
        onBack={() => chooseState(selected.state)}
      />
    );
  }

  return (
    <>
      <a className="skip-link" href="#current-status">Skip to current project status</a>
      <div className="app-shell pi-dashboard-shell">
        <header className="pi-header no-print">
          <div>
            <p className="eyebrow">Gabriel Wages · current evidence state</p>
            <h1>How municipal wages are set and changed</h1>
            <p className="pi-deck">A cross-occupation evidence project focused on documentary wage-growth mechanisms within cities and bargaining cycles.</p>
          </div>
          <a className="primary-report-link" href={currentReport?.href} target="_blank" rel="noreferrer">
            {currentReport?.link_label ?? "Open current evidence report"}
          </a>
        </header>

        <main>
          <section className="pi-status-strip" id="current-status" aria-label="Current project status">
            <div><span>Current stage</span><strong>{projectPhaseSummary.current_phase}</strong></div>
            <div><span>Next task</span><strong>{projectPhaseSummary.next_task}</strong></div>
            <div><span>Claim boundary</span><strong>Bounded local documentary evidence only · final, national, and causal claims blocked</strong></div>
            <div><span>Data current</span><strong>{projectPhaseSummary.data_vintage}</strong></div>
          </section>

          <section className="pi-section" aria-labelledby="coverage-title">
            <div className="pi-section-heading">
              <div>
                <p className="eyebrow">Geographic scout coverage</p>
                <h2 id="coverage-title">{nationalRate === null ? "Coverage rate unavailable" : `${formatPercent(nationalRate)} national coverage rate`}</h2>
              </div>
              <p><strong>{formatNumber(totals.scout_covered_municipalities)}</strong> scout-covered municipalities of <strong>{formatNumber(totals.municipality_universe)}</strong> eligible or known municipalities.</p>
            </div>
            <div className="pi-map-grid">
              <NationalMap states={stateSummary.states} selectedCode={selected.state} onSelect={chooseState} mapDataDate={projectPhaseSummary.map_data_date} />
              <CompactStateContext state={selected} onOpenReport={() => { window.location.hash = `/state/${selected.state}/report`; setRoute({ state: selected.state, view: "report" }); }} />
            </div>
          </section>

          <section className="pi-section" aria-labelledby="evidence-title">
            <div className="pi-section-heading">
              <div>
                <p className="eyebrow">Current bounded evidence</p>
                <h2 id="evidence-title">Source-grounded local comparisons after focused validation</h2>
              </div>
              <p>Raw values remain intact. Local documentary comparisons require final manual validation and are not final or national wage-gap estimates.</p>
            </div>
            <div className="pi-evidence-grid">
              <article><span>Partial records rescued</span><strong>{formatNumber(countFor("partial_records_repaired_count"))}</strong><p>{formatNumber(countFor("rescued_full_normalization_count"))} fully normalized · {formatNumber(countFor("rescued_gap_claim_ready_count"))} gap-claim ready · {formatNumber(countFor("rescued_near_gap_ready_count"))} near-ready</p></article>
              <article><span>Quantitative growth mechanisms</span><strong>{formatNumber(countFor("quantitatively_supported_growth_mechanism_claim_count"))}</strong><p>Source-reported percentages, COLA/CPI, schedules, or retroactive and lump-sum values</p></article>
              <article><span>Validated bounded comparisons</span><strong>{formatNumber(countFor("validated_bounded_wage_differential_candidate_count"))}</strong><p>{formatNumber(countFor("conditional_bounded_wage_differential_candidate_count"))} conditional · {formatNumber(countFor("rejected_bounded_wage_differential_candidate_count"))} rejected</p></article>
              <article><span>Source-grounded report examples</span><strong>{formatNumber(countFor("rescue_repaired_example_count"))}</strong><p>{formatNumber(countFor("future_gap_potential_only_count"))} matched cycles remain future-potential only</p></article>
            </div>
            {countFor("bounded_validation_input_candidate_count") > 0 && (
              <p className="pi-inline-note"><strong>{formatNumber(countFor("validated_bounded_wage_differential_candidate_count"))}</strong> candidate validates as a supporting bounded documentary comparison; <strong>{formatNumber(countFor("conditional_bounded_wage_differential_candidate_count"))}</strong> require candidate-specific manual review. None is a final, national, prevalence, policy-effect, or causal estimate.</p>
            )}
          </section>

          <section className="pi-section" aria-labelledby="mechanisms-title">
            <div className="pi-section-heading">
              <div>
                <p className="eyebrow">Mechanism findings preview</p>
                <h2 id="mechanisms-title">Strongest codified documentary clusters</h2>
              </div>
              <p>Ranked for PI review; counts describe this processed corpus, not national prevalence.</p>
            </div>
            {mechanisms.length ? (
              <div className="table-wrap pi-mechanism-table"><table>
                <thead><tr><th scope="col">Mechanism</th><th scope="col">Codified evidence</th><th scope="col">Mean / median strength</th><th scope="col">Dominant direction</th><th scope="col">Boundary</th></tr></thead>
                <tbody>{mechanisms.map((item) => <tr key={item.name}>
                  <th scope="row">{item.title ?? label(item.name.replace(/_strength$/, ""))}</th>
                  <td>{formatNumber(item.supported_record_count ?? item.report_ready_count)}</td>
                  <td>{Number(item.average_strength_score ?? 0).toFixed(2)} / {item.median_strength_score ?? 0} (0–4)</td>
                  <td>{dominantDirection(item.direction_distribution)}</td>
                  <td>Documentary pattern; no causal or prevalence claim</td>
                </tr>)}</tbody>
              </table></div>
            ) : <p className="pi-empty-state">Rating summaries are not available yet.</p>}
          </section>

          <section className="pi-section pi-boundary-section" aria-labelledby="boundary-title">
            <div>
              <p className="eyebrow">What can be said now</p>
              <h2 id="boundary-title">Careful mechanism claims, with explicit limits</h2>
            </div>
            <div className="pi-boundary-grid">
              <article><StatusPill tone="scout">Allowed</StatusPill><h3>Bounded local documentary claims</h3><p>State what validated same-city-cycle records currently show, with values, groups, periods, assumptions, and final-manual-validation caveats.</p></article>
              <article><StatusPill tone="future">Blocked</StatusPill><h3>Final or national wage-gap estimates</h3><p>Current candidates are source-grounded local comparisons—not final estimates, representative samples, or population prevalence.</p></article>
              <article><StatusPill tone="future">Blocked</StatusPill><h3>Causal and prevalence claims</h3><p>Matched documentary structures do not supply a causal design; corpus frequencies are not population prevalence.</p></article>
            </div>
            <p className="pi-cola-note">COLA/CPI language may be discussed as a contract mechanism. Analyst-side cost-of-living adjustment has not been performed.</p>
          </section>

          <details className="pi-technical-details">
            <summary>Technical audit and stage history</summary>
            <div className="pi-technical-grid">
              <div><span>Valid ratings</span><strong>{formatNumber(countFor("rating_valid_count"))}</strong></div>
              <div><span>Quarantine exclusions</span><strong>{formatNumber(countFor("rating_quarantine_count"))}</strong></div>
              <div><span>Codified records</span><strong>{formatNumber(countFor("codified_record_count"))}</strong></div>
              <div><span>Normalized records</span><strong>{formatNumber(countFor("normalized_quantitative_record_count"))}</strong></div>
              <div><span>Municipality-cycle groups</span><strong>{formatNumber(countFor("municipality_cycle_group_count"))}</strong></div>
              <div><span>Comparison candidates</span><strong>{formatNumber(countFor("comparable_normalized_wage_candidate_count"))}</strong></div>
              <div><span>Growth-readiness candidates</span><strong>{formatNumber(countFor("cycle_to_cycle_growth_readiness_candidate_count"))}</strong></div>
              <div><span>Scout-covered municipalities</span><strong>{formatNumber(totals.scout_covered_municipalities)}</strong></div>
              <div><span>Map denominator</span><strong>{formatNumber(totals.municipality_universe)}</strong></div>
            </div>
            <p>Detailed lane reconciliation, schemas, quarantine reasons, source-family summaries, and validation outputs are in the linked current report. Retained source files and full extracted text remain outside Git.</p>
          </details>
        </main>

        <footer>
          <div><p><strong>Gabriel Wages</strong></p><p>Collection readiness passed; mechanism and quantitative readiness remain partial.</p></div>
          <div className="footer-links"><a href="https://github.com/dkyaya/gabriel-wages" target="_blank" rel="noreferrer">Repository</a></div>
        </footer>
      </div>
    </>
  );
}

export default App;
