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
  const source = projectPhaseSummary.broad_state_4x2500_mechanism_summaries ?? {};
  return Object.entries(source)
    .filter(([name]) => !["weak_or_no_claim_support", "weak_or_no_claim_support_strength"].includes(name))
    .map(([name, item]) => ({ name, ...item }))
    .sort((a, b) => (b.report_ready_count ?? 0) - (a.report_ready_count ?? 0))
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
            Open current evidence report
          </a>
        </header>

        <main>
          <section className="pi-status-strip" id="current-status" aria-label="Current project status">
            <div><span>Current stage</span><strong>{projectPhaseSummary.current_phase}</strong></div>
            <div><span>Next task</span><strong>{projectPhaseSummary.next_task}</strong></div>
            <div><span>Claim boundary</span><strong>Descriptive evidence only · wage-gap and causal analysis blocked</strong></div>
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
                <p className="eyebrow">Current rated evidence</p>
                <h2 id="evidence-title">One validated rating outcome per exact span</h2>
              </div>
              <p>Ratings support evidence triage and report preparation. They are not yet ingested or codified findings.</p>
            </div>
            <div className="pi-evidence-grid">
              <article><span>Valid ratings</span><strong>{formatNumber(countFor("rating_valid_count"))}</strong><p>Schema-valid documentary ratings</p></article>
              <article><span>Quarantine</span><strong>{formatNumber(countFor("rating_quarantine_count"))}</strong><p>Excluded from downstream use pending repair</p></article>
              <article><span>Core + supporting</span><strong>{formatNumber(countFor("rating_report_ready_count") + countFor("rating_supporting_count"))}</strong><p>{formatNumber(countFor("rating_report_ready_count"))} core · {formatNumber(countFor("rating_supporting_count"))} supporting</p></article>
              <article><span>Context + excluded</span><strong>{formatNumber(countFor("rating_context_count") + countFor("rating_excluded_count"))}</strong><p>{formatNumber(countFor("rating_context_count"))} context · {formatNumber(countFor("rating_excluded_count"))} excluded</p></article>
            </div>
            {countFor("rating_normalization_needed_count") > 0 && (
              <p className="pi-inline-note"><strong>{formatNumber(countFor("rating_normalization_needed_count"))}</strong> valid ratings are routed to downstream normalization before quantitative comparison.</p>
            )}
          </section>

          <section className="pi-section" aria-labelledby="mechanisms-title">
            <div className="pi-section-heading">
              <div>
                <p className="eyebrow">Mechanism findings preview</p>
                <h2 id="mechanisms-title">Strongest rated documentary signals</h2>
              </div>
              <p>Ranked for PI review; counts describe this processed corpus, not national prevalence.</p>
            </div>
            {mechanisms.length ? (
              <div className="table-wrap pi-mechanism-table"><table>
                <thead><tr><th scope="col">Mechanism</th><th scope="col">Report-ready</th><th scope="col">Mean / median strength</th><th scope="col">Dominant direction</th><th scope="col">Boundary</th></tr></thead>
                <tbody>{mechanisms.map((item) => <tr key={item.name}>
                  <th scope="row">{label(item.name.replace(/_strength$/, ""))}</th>
                  <td>{formatNumber(item.report_ready_count)}</td>
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
              <h2 id="boundary-title">Mechanism descriptions, with explicit limits</h2>
            </div>
            <div className="pi-boundary-grid">
              <article><StatusPill tone="scout">Allowed</StatusPill><h3>Descriptive documentary summaries</h3><p>Discuss how contracts and local documents describe raises, bargaining, timing, market pressure, and non-base compensation.</p></article>
              <article><StatusPill tone="future">Blocked</StatusPill><h3>Wage-gap estimates</h3><p>Blocked pending normalization across pay units, ranks, effective dates, cycles, and base versus premium compensation.</p></article>
              <article><StatusPill tone="future">Blocked</StatusPill><h3>Causal and prevalence claims</h3><p>Blocked pending matched city-cycle structure; corpus frequencies are not population prevalence.</p></article>
            </div>
            <p className="pi-cola-note">COLA/CPI language may be discussed as a contract mechanism. Analyst-side cost-of-living adjustment has not been performed.</p>
          </section>

          <details className="pi-technical-details">
            <summary>Technical audit and stage history</summary>
            <div className="pi-technical-grid">
              <div><span>Rating queue</span><strong>{formatNumber(countFor("broad_state_4x2500_span_rating_queue_count"))}</strong></div>
              <div><span>Rating lanes</span><strong>4 × 4,653</strong></div>
              <div><span>Span candidates rated</span><strong>{formatNumber(countFor("broad_state_4x2500_span_rating_queue_count"))}</strong></div>
              <div><span>Source texts entering span extraction</span><strong>{formatNumber(projectPhaseSummary.broad_state_4x2500_span_extraction_queue_count ?? 0)}</strong></div>
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
