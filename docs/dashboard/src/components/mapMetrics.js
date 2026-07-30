function formatCoverageRate(value) {
  return value == null ? "Coverage rate unavailable" : `${Number(value).toFixed(1)}%`;
}

// The public map has one deliberately narrow contract: where local scouting ran.
// Mechanism, source-family, readiness, extraction, and rating details belong in
// reports and secondary panels, never in competing map filters.
export const MAP_METRICS = [
  {
    key: "scout_coverage_rate",
    label: "Scout coverage rate",
    shortLabel: "municipality scout coverage rate",
    format: formatCoverageRate,
    caveat: "Rate of eligible/known municipal governments with a parseable local scout outcome; not evidence strength or analytical readiness.",
  },
];

export function metricForKey() { return MAP_METRICS[0]; }

export function metricMaximum(states, metricKey) {
  return Math.max(0, ...states.map((state) => state[metricKey]).filter((value) => value != null));
}

export function valueBand(value, max) {
  if (value == null || !value || !max) return 0;
  const share = value / max;
  if (share <= 0.25) return 1;
  if (share <= 0.5) return 2;
  if (share <= 0.75) return 3;
  return 4;
}
