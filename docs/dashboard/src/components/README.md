# Dashboard components

The MVP uses explicit component boundaries while keeping all data loading in `App.jsx`.

- `NationalMap.jsx` — shared map shell, five safe metrics, geographic/tile mode toggle, legend, interpretation note, and table fallback.
- `USChoroplethMap.jsx` — token-free geographic US choropleth rendered from the committed Census GeoJSON, with hover/focus labels and state selection.
- `StateTileGrid.jsx` — preserved schematic tile-grid alternate using the same metrics and selection callback.
- `mapMetrics.js` — the only map-metric allowlist, formatting rules, and shared color-band calculation.
- `StateDetailPanel.jsx` — selected-state coverage, queue, failure, likely-set, and stage summary.
- `PrintableStateReport.jsx` — dedicated hash-routed print view derived from the same state data.
- `CoverageFunnel.jsx` — current discovery stages, separate failures, and null future stages.
- `CandidateQueueCards.jsx` — priority workload and scout unit-label composition.
- `AnalysisReadinessPanel.jsx` — current versus unavailable evidence/analysis stages and wage-analysis gate.
- `DataLimitations.jsx` — status vocabulary, interpretation limits, builder metadata, and source paths.
- `ui.jsx` — controlled pills, metric cards, null-safe formatting, and shared labels.

Component rules:

1. Never infer verification, ingestion, codification, matched cycles, wage outcomes, or claim support from scout fields.
2. Render `null` as “Not yet available,” never as zero.
3. Describe queue priority only as later-verification scheduling.
4. Put technical provenance and field definitions inside `<details>` unless essential to interpretation.
5. Give every chart/map a text or table equivalent.
6. Derive the printable state report from the same generated JSON as the interactive state panel.
7. Do not fetch remote data or require runtime credentials.
8. Keep boundary assets local and provenance-documented; never add runtime map-provider requests or token-dependent basemaps.
