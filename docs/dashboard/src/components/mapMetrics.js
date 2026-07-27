import { formatNumber } from "./ui.jsx";

// The public map has one deliberately narrow contract: where local scouting ran.
// Mechanism, source-family, readiness, extraction, and rating details belong in
// reports and secondary panels, never in competing map filters.
export const MAP_METRICS = [
  {
    key: "total_scout_coverage_count",
    label: "Total scout coverage",
    shortLabel: "scout-covered municipalities",
    format: formatNumber,
    caveat: "Count of municipalities with a parseable local scout outcome; not national representativeness or evidence strength.",
  },
];

export function metricForKey() { return MAP_METRICS[0]; }

export function metricMaximum(states, metricKey) {
  return Math.max(0, ...states.map((state) => state[metricKey] ?? 0));
}

export function valueBand(value, max) {
  if (!value || !max) return 0;
  const share = value / max;
  if (share <= 0.25) return 1;
  if (share <= 0.5) return 2;
  if (share <= 0.75) return 3;
  return 4;
}
