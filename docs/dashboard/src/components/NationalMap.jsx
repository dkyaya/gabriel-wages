import { useMemo, useState } from "react";
import { StateTileGrid } from "./StateTileGrid.jsx";
import { USChoroplethMap } from "./USChoroplethMap.jsx";
import { MAP_METRICS, metricForKey, metricMaximum } from "./mapMetrics.js";

export function NationalMap({ states, selectedCode, onSelect }) {
  const [metricKey, setMetricKey] = useState("scout_coverage_rate");
  const [mapMode, setMapMode] = useState("geographic");
  const metric = metricForKey(metricKey);
  const max = useMemo(() => metricMaximum(states, metricKey), [states, metricKey]);

  return (
    <article className="panel map-panel no-print" aria-labelledby="national-map-title">
      <div className="section-heading map-heading">
        <div>
          <p className="eyebrow">National scout coverage</p>
          <h2 id="national-map-title">State choropleth</h2>
        </div>
        <div className="map-controls">
          <div className="map-mode-toggle" role="group" aria-label="Map view">
            <button
              type="button"
              className={mapMode === "geographic" ? "active" : ""}
              aria-pressed={mapMode === "geographic"}
              onClick={() => setMapMode("geographic")}
            >
              Geographic Map
            </button>
            <button
              type="button"
              className={mapMode === "tile" ? "active" : ""}
              aria-pressed={mapMode === "tile"}
              onClick={() => setMapMode("tile")}
            >
              Tile Grid
            </button>
          </div>
          <label className="metric-select">
            <span>Color by</span>
            <select value={metricKey} onChange={(event) => setMetricKey(event.target.value)}>
              {MAP_METRICS.map((item) => (
                <option key={item.key} value={item.key}>{item.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="map-status-note" role="note">
        <strong>Preliminary discovery view.</strong> Scout coverage is preliminary, candidate rows are unverified, and wage-gap conclusions are not displayed.
      </div>

      {mapMode === "geographic" ? (
        <USChoroplethMap
          states={states}
          selectedCode={selectedCode}
          onSelect={onSelect}
          metric={metric}
          metricKey={metricKey}
          max={max}
        />
      ) : (
        <StateTileGrid
          states={states}
          selectedCode={selectedCode}
          onSelect={onSelect}
          metric={metric}
          metricKey={metricKey}
          max={max}
        />
      )}

      <div className="map-legend" aria-label="Map color scale">
        <span>Zero / no current value</span>
        {[1, 2, 3, 4].map((band) => <i className={`metric-band-${band}`} key={band} aria-hidden="true" />)}
        <span>Higher current value</span>
      </div>
      <p className="panel-note">
        {metric.caveat} Colors are scaled to the current maximum, so use the labels for exact comparisons. The geographic map uses a committed local boundary asset; the tile grid is a compact schematic alternate.
      </p>

      <details className="map-table-fallback">
        <summary>View accessible state values</summary>
        <div className="table-wrap compact-table-wrap">
          <table>
            <thead><tr><th scope="col">State</th><th scope="col">{metric.label}</th><th scope="col">Stage</th></tr></thead>
            <tbody>
              {states.map((state) => (
                <tr key={state.state}>
                  <th scope="row"><button className="table-state-button" onClick={() => onSelect(state.state)}>{state.state_name}</button></th>
                  <td>{metric.format(state[metricKey] ?? 0)}</td>
                  <td>{state.scout_coverage_count ? "Scout coverage recorded" : "Not yet scouted"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </article>
  );
}
