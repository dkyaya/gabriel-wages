# Dashboard full project hub design

Date: 2026-07-22

## Objective

Upgrade the static dashboard from a compact discovery MVP into a permanent project/research status hub while preserving its current map, state selection, printable state reports, deterministic data flow, and source-stage boundaries.

The hub must answer three different questions without conflating them:

1. **Collected:** what infrastructure and discovery outputs exist now?
2. **Current:** what is the active project checkpoint and what do the data support?
3. **Forthcoming:** what work remains before verified evidence and empirical analysis?

## Information architecture

### 1. Overview

- Frozen post–Tier 1 Wave 2 checkpoint.
- National universe, successful scout coverage, candidate queue, and failure count.
- Prominent source-discovery caveat.
- Three-part `Collected / Current / Forthcoming` orientation strip.
- Latest report and PI decision point.

### 2. Coverage map / geography

- Preserve the existing geographic US choropleth and tile-grid alternate.
- Preserve state selection, metric selector, state panel, and accessible values table.
- Keep candidate-positive, parseable-empty, and failure-only status explicit.

### 3. Scouting priority tiers

- Render Tier 1–Tier 5 future-eligible counts.
- Show future-scout eligible total and failure-retry targets.
- Show the latest priority checkpoint and refresh cadence.
- Provide a compact state-priority table for Tier 1 + Tier 2 remaining.
- Label tiers as deterministic operational scheduling, not findings.

### 4. Scout operations

- Latest wave runtime, rows/hour, candidate rows/hour, density, and failures.
- Four-wave trend view using simple accessible bars and exact labels.
- Current operating controls: serialized lane, compact prompts, deterministic hints, adaptive sleep, stronger preflight.
- Avoid implying that faster or higher-yield waves produce higher-quality evidence.

### 5. Candidate queue

- Queue total, municipalities represented, later-verification rows, and held/rejected rows.
- Unit-label composition and triage buckets.
- State workload table.
- Explicitly distinguish municipality counts from candidate-row counts.

### 6. Verification pipeline

- Five stages: candidate lead → verified source → ingested source → codified evidence → analysis-ready evidence.
- Candidate-lead count shown as collected.
- Downstream stages shown as planned/not project-wide rather than zero.
- Highlight the proposed 50–100-row verification pilot.

### 7. State yield / learning

- Show the state-yield leaderboard only for states meeting the ten-successful-scout minimum.
- Include candidate-positive rate, candidate rows per covered municipality, successful sample, and confidence.
- Display the small-sample warning and 300–600-scout priority-refresh recommendation.

### 8. Reports library / PI reports

- Current PI report highlighted with title, checkpoint, summary, tags, metrics snapshot, and PDF link.
- Metadata comes from a versioned `reports_index.json`.
- Provide visible planned slots for future verification and evidence reports without inventing outputs.

### 9. Methodology / definitions

- Define municipality searched, scout-covered, candidate row, parseable-empty, failure-only, priority tier, verified source, and analysis-ready evidence.
- Keep terms concise and stage-specific.

### 10. Next steps

- PI breadth-versus-verification decision.
- Recommended 50–100-row verification pilot.
- Optional continued Tier 1 discovery.
- Separate bounded retry lane for 20 failure-only municipalities.

## Navigation

- Use a sticky horizontal section navigator on desktop.
- Use an accessible menu button and collapsible list on smaller screens.
- Navigation uses `scrollIntoView` rather than URL fragments so it does not interfere with the existing `#/state/<CODE>` hash routing.
- The active implementation is a clean first-pass section navigator; automatic scroll-position highlighting is deferred.

## Visual system

- Preserve the dashboard's evergreen/scout-blue palette for operational status.
- Add Harvard crimson sparingly for report-library and decision accents, providing continuity with PI reports.
- Use Georgia for major headings and numerals, system sans serif for interface labels/body.
- Reduce gratuitous card density by grouping related material into larger panels.
- Use whitespace, rules, simple grids, and compact bars rather than decorative charts.

## Data contract

Existing static JSON remains authoritative:

- `state_summary.json`
- `candidate_queue_summary.json`
- `coverage_funnel.json`
- `analysis_readiness.json`
- `priority_summary.json`
- `state_priority_summary.json`
- `top_priority_targets.json`
- `scout_operations_summary.json`
- `scout_yield_by_state.json`
- `scout_runtime_trends.json`

New report metadata:

- source: `docs/dashboard/reports/reports_index.json`
- generated dashboard copy: `docs/dashboard/data/reports_index.json`

The dashboard builder validates the report index and copies it into the generated data layer. It does not inspect report contents or access the network.

## Accessibility and responsive behavior

- Semantic sections with stable IDs and labeled headings.
- Keyboard-operable menu, state map, tables, and report links.
- Accessible textual alternatives for maps and trend bars.
- Tables remain horizontally scrollable on narrow screens.
- Hub grids collapse to one column on mobile.
- Reduced-motion preference disables transitions.

## Interpretation controls

Every major stage includes at least one of these boundaries:

- source discovery only;
- candidate rows are unverified;
- tiers are operational;
- downstream stages are not yet project-wide;
- no wage-gap or causal findings are displayed.

## Deferred enhancements

- Automatic active-section tracking in the navigation.
- Search/filter across a future multi-report library.
- Municipality-level exploration.
- Dedicated verified-source and ingestion dashboards once those ledgers exist.
- Automated browser accessibility and visual-regression tests.

These are deferred because the current data layer does not yet support them or because they are not needed for a safe, permanent first-pass hub.
