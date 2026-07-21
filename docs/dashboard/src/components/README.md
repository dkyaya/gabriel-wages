# Component Plan

The first draft keeps components in `App.jsx` so the information hierarchy can be reviewed before a larger component API is frozen. Split them once the map asset and routing behavior are approved.

Recommended component boundaries:

- `NationalMap`: token-free Leaflet choropleth using committed state GeoJSON; emits state selection.
- `StateDetailPanel`: headline counts, narrative, stage badges, queue composition, and failure accounting.
- `PrintableStateReport`: print-only state evidence-status brief using the same state object.
- `MetricCard`: labeled value plus a one-line interpretation.
- `StatusPill`: controlled scout/calibration/verified/ingested/codified/future vocabulary.
- `CoverageFunnel`: current discovery stages plus null future stages.
- `CandidateQueueExplorer`: filters and aggregate table; no raw URLs by default.
- `ClaimEvidencePanel`: claim, evidence, reasoning, counterevidence, limitations, and source needs.
- `AnalysisReadinessPanel`: explicit available/blocked input matrix.
- `RegressionResultsPanel`: disabled until a versioned regression JSON exists.

Component rules:

1. Never infer verification, ingestion, codification, or claim support from a scout field.
2. Render `null` as “Not available,” never as zero.
3. Use queue priority only as later-verification scheduling language.
4. Put technical provenance inside `<details>` unless it is essential to interpretation.
5. Every chart or map needs a text/table equivalent for accessibility and printing.
6. The printable state report must derive from the same state JSON as the interactive panel.
