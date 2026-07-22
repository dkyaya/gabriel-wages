import { formatNumber } from "./ui.jsx";
import { valueBand } from "./mapMetrics.js";

const TILE_POSITIONS = {
  AK: [1, 1], ME: [1, 12],
  WI: [2, 7], MI: [2, 9], VT: [2, 10], NH: [2, 11],
  WA: [3, 2], ID: [3, 4], MT: [3, 5], ND: [3, 6], MN: [3, 7], IL: [3, 8], NY: [3, 9], MA: [3, 10],
  OR: [4, 2], NV: [4, 3], WY: [4, 5], SD: [4, 6], IA: [4, 7], IN: [4, 8], OH: [4, 9], PA: [4, 10], NJ: [4, 11], CT: [4, 12], RI: [4, 13],
  CA: [5, 2], UT: [5, 4], CO: [5, 5], NE: [5, 6], MO: [5, 7], KY: [5, 8], WV: [5, 9], VA: [5, 10], MD: [5, 11], DE: [5, 12],
  AZ: [6, 3], NM: [6, 4], KS: [6, 6], AR: [6, 7], TN: [6, 8], NC: [6, 10], DC: [6, 11],
  HI: [7, 1], TX: [7, 5], OK: [7, 6], LA: [7, 7], MS: [7, 8], AL: [7, 9], SC: [7, 10],
  FL: [8, 10], GA: [8, 9],
};

export function StateTileGrid({ states, selectedCode, onSelect, metric, metricKey, max }) {
  return (
    <div className="tile-map" aria-label={`US state tile-grid choropleth colored by ${metric.label}`}>
      {states.map((state) => {
        const [row, column] = TILE_POSITIONS[state.state] ?? [9, 1];
        const value = state[metricKey] ?? 0;
        return (
          <button
            className={`state-tile metric-band-${valueBand(value, max)} ${state.state === selectedCode ? "selected" : ""}`}
            key={state.state}
            onClick={() => onSelect(state.state)}
            style={{ gridRow: row, gridColumn: column }}
            aria-pressed={state.state === selectedCode}
            aria-label={`${state.state_name}: ${metric.label} ${metric.format(value)}`}
            title={`${state.state_name}\n${metric.label}: ${metric.format(value)}\nScout covered: ${formatNumber(state.scout_coverage_count)}\nCandidate rows: ${formatNumber(state.candidate_rows)}`}
          >
            <span>{state.state}</span>
            <small>{metric.format(value)}</small>
          </button>
        );
      })}
    </div>
  );
}
