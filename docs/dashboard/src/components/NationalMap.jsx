import { useMemo, useState } from "react";
import { StateTileGrid } from "./StateTileGrid.jsx";
import { USChoroplethMap } from "./USChoroplethMap.jsx";
import { MAP_METRICS, metricMaximum } from "./mapMetrics.js";

export function NationalMap({ states, selectedCode, onSelect, mapDataDate }) {
  const [mapMode, setMapMode] = useState("geographic");
  const metric = MAP_METRICS[0];
  const metricKey = metric.key;
  const max = useMemo(() => metricMaximum(states, metricKey), [states, metricKey]);
  const map = mapMode === "geographic"
    ? <USChoroplethMap states={states} selectedCode={selectedCode} onSelect={onSelect} metric={metric} metricKey={metricKey} max={max} />
    : <StateTileGrid states={states} selectedCode={selectedCode} onSelect={onSelect} metric={metric} metricKey={metricKey} max={max} />;

  return (
    <article className="panel map-panel no-print" aria-labelledby="national-map-title">
      <div className="section-heading map-heading">
        <div>
          <p className="eyebrow">Scout coverage rate · only map layer</p>
          <h2 id="national-map-title">Where local source scouting has run</h2>
          <p className="quiet-label">Map data date: {mapDataDate}</p>
        </div>
        <div className="map-mode-toggle" role="group" aria-label="Map presentation">
          <button type="button" className={mapMode === "geographic" ? "active" : ""} aria-pressed={mapMode === "geographic"} onClick={() => setMapMode("geographic")}>Geographic map</button>
          <button type="button" className={mapMode === "tile" ? "active" : ""} aria-pressed={mapMode === "tile"} onClick={() => setMapMode("tile")}>Tile grid</button>
        </div>
      </div>
      <div className="map-status-note" role="note"><strong>Scout-coverage map only.</strong> Color shows scout-covered municipalities divided by the eligible/known municipality universe. Raw covered and denominator counts remain context only. Mechanism, source-family, readiness, extraction, and rating details stay outside the map.</div>
      {map}
      <div className="map-legend" aria-label="Map color scale">
        <span>No scout coverage</span>
        {[1, 2, 3, 4].map((band) => <i className={`metric-band-${band}`} key={band} aria-hidden="true" />)}
        <span>Higher scout coverage rate</span>
      </div>
      <p className="panel-note">{metric.caveat} Rate = scout-covered municipalities ÷ eligible/known municipality universe. Missing denominators are shown as unavailable; no denominator is fabricated.</p>
      <details className="map-table-fallback">
        <summary>View accessible scout-coverage-rate table</summary>
        <div className="table-wrap compact-table-wrap"><table>
          <thead><tr><th scope="col">State</th><th scope="col">Coverage rate</th><th scope="col">Scout covered / eligible-known</th><th scope="col">Coverage status</th></tr></thead>
          <tbody>{states.map((state) => <tr key={state.state}>
            <th scope="row"><button className="table-state-button" onClick={() => onSelect(state.state)}>{state.state_name}</button></th>
            <td>{metric.format(state[metricKey])}</td>
            <td>{state.municipality_universe ? `${state.total_scout_coverage_count.toLocaleString()} / ${state.municipality_universe.toLocaleString()}` : "Denominator unavailable"}</td>
            <td>{state.coverage_rate_status === "coverage_rate_unavailable" ? "Coverage rate unavailable" : state.total_scout_coverage_count ? "Scout coverage recorded" : "No scout coverage recorded"}</td>
          </tr>)}</tbody>
        </table></div>
      </details>
    </article>
  );
}
