import { formatNumber, formatPercent } from "./ui.jsx";

export const MAP_METRICS = [
  {
    key: "tier_c_retained_source_count",
    label: "Tier C retained sources",
    shortLabel: "retained sources",
    format: formatNumber,
    caveat: "Retained Tier C files represented in the bounded readiness queue; not evidence or representativeness.",
  },
  {
    key: "tier_c_text_extraction_ready_count",
    label: "Tier C text-ready sources",
    shortLabel: "text-ready sources",
    format: formatNumber,
    caveat: "Files approved only for a later bounded text-layer extraction; not yet extracted or rated.",
  },
  {
    key: "tier_c_deferred_or_review_count",
    label: "Tier C deferred/review sources",
    shortLabel: "deferred/review sources",
    format: formatNumber,
    caveat: "Retained files held outside the later text-extraction queue.",
  },
  {
    key: "scout_coverage_rate",
    label: "Historical scout coverage rate",
    shortLabel: "coverage rate",
    format: formatPercent,
    caveat: "Share of each state's municipal universe with a parseable scout outcome.",
  },
  {
    key: "scout_coverage_count",
    label: "Historical scout-covered municipalities",
    shortLabel: "covered municipalities",
    format: formatNumber,
    caveat: "Parseable candidate-positive or empty scout outcomes; not verification.",
  },
  {
    key: "candidate_rows",
    label: "Candidate rows",
    shortLabel: "candidate rows",
    format: formatNumber,
    caveat: "Unverified source-discovery rows currently represented in the queue.",
  },
  {
    key: "high_priority_queue_count",
    label: "High-priority later-review rows",
    shortLabel: "high-priority rows",
    format: formatNumber,
    caveat: "A scheduling priority for later verification, not evidence quality.",
  },
  {
    key: "evidence_readiness_score",
    label: "Operational readiness score",
    shortLabel: "readiness score",
    format: (value) => `${formatNumber(value)}/100`,
    caveat: "A workflow-triage score only; it is not evidence strength or a wage result.",
  },
];

export function metricForKey(metricKey) {
  return MAP_METRICS.find((item) => item.key === metricKey) ?? MAP_METRICS[0];
}

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
