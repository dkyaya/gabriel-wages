import { useEffect, useMemo, useState } from "react";
import stateBoundariesUrl from "../assets/us-states-2025-20m.geojson?url";
import { formatNumber } from "./ui.jsx";
import { valueBand } from "./mapMetrics.js";

const REGIONS = {
  contiguous: { bounds: [-125, -66, 24, 50], frame: [42, 24, 876, 406] },
  AK: { bounds: [-190, -129, 50, 72], frame: [48, 447, 250, 126] },
  HI: { bounds: [-161, -154, 18, 23], frame: [338, 477, 177, 86] },
};

function regionForState(code) {
  return code === "AK" || code === "HI" ? REGIONS[code] : REGIONS.contiguous;
}

function normalizeLongitude(longitude, code) {
  return code === "AK" && longitude > 0 ? longitude - 360 : longitude;
}

function projectPoint([longitude, latitude], code) {
  const { bounds: [minLongitude, maxLongitude, minLatitude, maxLatitude], frame: [x, y, width, height] } = regionForState(code);
  const adjustedLongitude = normalizeLongitude(longitude, code);
  return [
    x + ((adjustedLongitude - minLongitude) / (maxLongitude - minLongitude)) * width,
    y + ((maxLatitude - latitude) / (maxLatitude - minLatitude)) * height,
  ];
}

function ringPath(ring, code) {
  return ring.map((point, index) => {
    const [x, y] = projectPoint(point, code);
    return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ") + " Z";
}

function geometryPath(geometry, code) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons.flatMap((polygon) => polygon.map((ring) => ringPath(ring, code))).join(" ");
}

function stateLabel(state, metric, metricKey) {
  if (!state) return "No dashboard data available";
  return `${state.state_name}: ${metric.label} ${metric.format(state[metricKey] ?? 0)}`;
}

export function USChoroplethMap({ states, selectedCode, onSelect, metric, metricKey, max }) {
  const [stateBoundaries, setStateBoundaries] = useState(null);
  const [boundaryError, setBoundaryError] = useState(false);
  const [hoveredCode, setHoveredCode] = useState(null);
  const stateByCode = useMemo(() => new Map(states.map((state) => [state.state, state])), [states]);

  useEffect(() => {
    let active = true;
    fetch(stateBoundariesUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`Boundary request failed with ${response.status}`);
        return response.json();
      })
      .then((data) => {
        if (active) setStateBoundaries(data);
      })
      .catch(() => {
        if (active) setBoundaryError(true);
      });
    return () => { active = false; };
  }, []);

  const pathByCode = useMemo(
    () => new Map((stateBoundaries?.features ?? []).map((feature) => [
      feature.properties.STUSPS,
      geometryPath(feature.geometry, feature.properties.STUSPS),
    ])),
    [stateBoundaries],
  );
  const activeCode = hoveredCode ?? selectedCode;
  const activeState = stateByCode.get(activeCode);

  function activateFromKeyboard(event, code, hasData) {
    if (!hasData || (event.key !== "Enter" && event.key !== " ")) return;
    event.preventDefault();
    onSelect(code);
  }

  if (boundaryError) {
    return (
      <div className="geographic-map-message" role="alert">
        The local geographic boundary asset could not be loaded. Choose Tile Grid to continue exploring state values.
      </div>
    );
  }

  if (!stateBoundaries) {
    return <div className="geographic-map-message" role="status">Loading local Census state boundaries…</div>;
  }

  return (
    <div className="geographic-map-wrap">
      <div className="map-hover-label" aria-live="polite">
        <strong>{activeState?.state_name ?? activeCode}</strong>
        <span>{activeState ? `${metric.label}: ${metric.format(activeState[metricKey] ?? 0)}` : "No dashboard data available"}</span>
      </div>
      <svg
        className="geographic-map"
        viewBox="0 0 960 600"
        role="img"
        aria-labelledby="geographic-map-title geographic-map-description"
      >
        <title id="geographic-map-title">United States geographic state choropleth</title>
        <desc id="geographic-map-description">
          Census state boundaries colored by {metric.label}. Alaska and Hawaii are shown as labeled insets. Select a state to update the shared state detail panel.
        </desc>
        <rect className="map-inset-frame" x="35" y="438" width="276" height="145" rx="10" />
        <rect className="map-inset-frame" x="325" y="466" width="205" height="108" rx="10" />
        {stateBoundaries.features.map((feature) => {
          const code = feature.properties.STUSPS;
          const state = stateByCode.get(code);
          const hasData = Boolean(state);
          const value = state?.[metricKey] ?? 0;
          return (
            <path
              key={code}
              d={pathByCode.get(code)}
              className={`geo-state metric-band-${hasData ? valueBand(value, max) : 0} ${code === selectedCode ? "selected" : ""} ${hasData ? "" : "missing-data"}`}
              role="button"
              tabIndex={hasData ? 0 : -1}
              aria-pressed={hasData ? code === selectedCode : undefined}
              aria-label={stateLabel(state, metric, metricKey)}
              onClick={() => hasData && onSelect(code)}
              onKeyDown={(event) => activateFromKeyboard(event, code, hasData)}
              onMouseEnter={() => setHoveredCode(code)}
              onMouseLeave={() => setHoveredCode(null)}
              onFocus={() => setHoveredCode(code)}
              onBlur={() => setHoveredCode(null)}
            >
              <title>{stateLabel(state, metric, metricKey)}</title>
            </path>
          );
        })}
        <text className="map-inset-label" x="48" y="460">ALASKA</text>
        <text className="map-inset-label" x="338" y="488">HAWAII</text>
        <circle
          className={`dc-map-marker metric-band-${valueBand(stateByCode.get("DC")?.[metricKey] ?? 0, max)} ${selectedCode === "DC" ? "selected" : ""}`}
          cx="755"
          cy="197"
          r="5"
          role="button"
          tabIndex="0"
          aria-pressed={selectedCode === "DC"}
          aria-label={stateLabel(stateByCode.get("DC"), metric, metricKey)}
          onClick={() => onSelect("DC")}
          onKeyDown={(event) => activateFromKeyboard(event, "DC", true)}
          onMouseEnter={() => setHoveredCode("DC")}
          onMouseLeave={() => setHoveredCode(null)}
          onFocus={() => setHoveredCode("DC")}
          onBlur={() => setHoveredCode(null)}
        >
          <title>{stateLabel(stateByCode.get("DC"), metric, metricKey)}</title>
        </circle>
        <path className="dc-leader" d="M760 194 L779 179" aria-hidden="true" />
        <text className="dc-label" x="783" y="181" aria-hidden="true">DC</text>
      </svg>
      <p className="geographic-map-caption">
        Local Census boundaries; Alaska and Hawaii use insets. Hover or focus a state for its exact value. Scout covered: {formatNumber(activeState?.scout_coverage_count)}.
      </p>
    </div>
  );
}
