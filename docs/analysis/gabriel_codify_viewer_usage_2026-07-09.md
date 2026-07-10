# GABRIEL Codify Evidence Viewer — Usage Guide (2026-07-09)

## How to open the viewer locally

```bash
open docs/analysis/gabriel_codify_excerpt_browser_latest.html
```

(or double-click the file in Finder / your file manager). It opens directly in any modern browser — no server, no internet connection, and no additional software required.

## Which file to share

**Share `gabriel_codify_excerpt_browser_latest.html` only.** It is a single, self-contained file — evidence data, styling, and interactivity are all embedded directly in it — so sending that one file (email attachment, shared drive, etc.) is sufficient. Nothing else needs to travel with it.

The dated file (`gabriel_codify_excerpt_browser_2026-07-09.html`) is an **archival snapshot** of this specific build. It's kept in version control so a specific point-in-time viewer state can always be referenced later, but `..._latest.html` is the one to open, bookmark, or share going forward — it will be overwritten with the newest content each time the builder script runs, while the dated file accumulates one snapshot per build date.

## What files are needed for portability

Just the one HTML file. It does not read any other file at runtime, does not call out to the network, and does not depend on any CDN-hosted library — everything (CSS, JavaScript, and the evidence data itself) is inlined in the `<head>` and `<body>`. Anyone who receives the file can open it in a browser with no setup.

## What the viewer does and does not include

**Includes:**
- Every row currently in `docs/analysis/gabriel_codify_evidence_layer.csv` (as of the last build) — both `present` (evidence found) and `not_found` (no evidence found) rows, though `not_found` rows are hidden by default.
- Plain-English labels for state, city, contract, occupation, source role, mechanism (attribute), evidence status, and source-verification status.
- A full glossary of all 19 wage-mechanism attribute definitions.
- Short, template-generated ("what this excerpt shows") explanations for each piece of evidence — not new model output, just a fixed sentence keyed to which attribute the excerpt was coded under.

**Does not include:**
- The underlying source PDFs or any full document text — only short, already-verified excerpts.
- Any causal claim, statistical result, or wage-effect estimate. This is an excerpt browser, not an analysis or a report.
- Massachusetts evidence yet (see below).
- Any secret, API key, or credential.

## How to regenerate the viewer

```bash
python scripts/build_codify_evidence_viewer.py
```

By default this reads `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv`, rebuilds `docs/analysis/gabriel_codify_evidence_layer.csv` from it, and rewrites both `gabriel_codify_excerpt_browser_2026-07-09.html` and `gabriel_codify_excerpt_browser_latest.html`. Optional arguments: `--input <csv>`, `--evidence-out <csv>`, `--html-out <html>`, `--html-latest-out <html>`. The script makes no network calls and never edits `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` — it only *reads* `data/contracts.csv` to build human-readable contract labels.

## How future codify outputs (including Massachusetts) should be appended and rebuilt

The label maps in `scripts/build_codify_evidence_viewer.py` (state, occupation, source-role, and attribute labels) already include Massachusetts alongside Texas and Ohio — nothing in the builder is state-specific. **However, the builder currently reads exactly one `--input` CSV and fully rewrites the evidence layer from it**, so a future Massachusetts codify run's output CSV cannot simply be appended by re-running the script as-is; either:

1. Concatenate all codify output CSVs collected so far (Texas/Ohio + the new Massachusetts run) into one combined CSV before running the builder, or
2. Extend the script with an explicit append/union mode (planned, not yet built — see `gabriel_codify_viewer_overhaul_plan_2026-07-09.md`'s long-term roadmap) that unions new rows into the existing evidence layer, de-duplicating by `evidence_id` (which is already collision-resistant across different `run_date`s, since it's built from `run_date` + `contract_id` + `attribute` + a per-pair sequence number).

Either way, after adding new codify output, re-run the builder and re-share the freshly regenerated `..._latest.html`.

## What "Verified in source text" means

It means the excerpt text codify returned for that attribute was checked, character-for-character, against the actual evidence window it was drawn from, and really does appear there verbatim. **It is a text-integrity check, nothing more** — it confirms the model did not fabricate or paraphrase the quoted text. It does **not** mean the excerpt establishes, proves, or measures any wage effect, and it does not mean a human reviewer has independently confirmed the attribute assignment is the *correct* one for that passage (though in the current dataset, every `present` row happens to also be verified — see `gabriel_codify_full_codebook_audit_2026-07-09.md`'s source-grounding audit for the underlying check).

## Warning: not causal proof

**This viewer is an evidence browser, not an analysis.** Every excerpt shown is evidence that a specific wage-setting mechanism is *discussed in the source text* for that contract. None of this, by itself, proves that the mechanism *causes* any particular wage outcome — that is a separate analytical question this project has not yet addressed with this data. The viewer repeats this warning at the top of the page and on every evidence card specifically so it can't be missed or forgotten when skimming.

## Massachusetts: planned, not yet included

The evidence layer currently covers only the 4 Texas/Ohio contracts run through the Harvard Proxy-enabled codify pilot (`gabriel_codify_full_codebook_outputs_2026-07-09.csv`). Massachusetts has extensive existing corpus data and prior hand-built mechanism-excerpt work in this project, making it the natural next codify expansion target — but running MA through codify was explicitly out of scope for this session (see `gabriel_codify_viewer_overhaul_plan_2026-07-09.md`'s short-term roadmap: scale the remaining Texas/Ohio rows first, then a curated Massachusetts batch, then rebuild the evidence layer and viewer).
