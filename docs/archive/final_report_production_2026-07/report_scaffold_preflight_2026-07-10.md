# Report Scaffold Preflight — 2026-07-10

## Purpose

This run drafts a first serious report scaffold — Markdown, CSV tables, and charts, no final PDF/DOCX — from the current GABRIEL/codify evidence layer and source corpus. **No GABRIEL/codify calls, no Harvard Proxy/model/API calls, and no new source collection occur in this run.**

## Repo state at start of this run

- `git status`: clean except untracked `.claude/` and `tmp/` (harness scratch dirs). No unexpected uncommitted changes.
- Latest commit: `20a0f26` — "Codify expanded Texas and Ohio sources", stacked on `9c42999` — "Expand Texas and Ohio sources".
- `data/contracts.csv`: **53 data rows** (MA 32, OH 13, TX 8).
- `data/city_coverage.csv`: **53 data rows**, 1:1 matched to contracts.
- Distinct cities: **16**.
- Healthy matched pairs (`ingest/audit_coverage.py`): **23** (exact-cycle: 9, overlap-cycle: 14).

All counts match this run's expected starting state exactly.

## Evidence-layer state

`docs/analysis/gabriel_codify_evidence_layer.csv`: **781 rows**.

- `present`: 293. `not_found`: 488.
- `viewer_verified=1` (verified present, shown by default in the viewer): **284**.
- `viewer_verified=0` (unverified/flagged present, hidden by default): **9**.
- `source_grounding_status`: `grounded` 289, `unclear` 4 (the 4 unclear rows are among the 9 unverified — pre-existing boundary-leakage flags from the Massachusetts and Seekonk/Wayland batches), `not_applicable` 488 (all `not_found` rows).
- **37 of 53 contracts have been codified** (all 8 Texas contracts, all 13 Ohio contracts, 16 of 32 Massachusetts contracts). 16 Massachusetts contracts remain uncodified (e.g., Newton, Worcester, Arlington, additional Somerville rows, Boston police) — this report scaffold covers only the codified subset, consistent with using verified GABRIEL evidence rather than inferring from uncodified source text.

## States/cities represented in the evidence layer

| state | cities codified | contracts codified |
|---|---|---|
| MA | Boston, Franklin, Georgetown, Seekonk, Somerville, Wayland (6 of ~9 MA cities in corpus) | 16 |
| TX | Austin, Houston, San Antonio (3 of 3 TX cities in corpus) | 8 |
| OH | Cincinnati, Cleveland, Columbus, Toledo (4 of 4 OH cities in corpus) | 13 |

## Codify output files included in the current evidence layer (5-file union)

1. `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` — original 4-row pilot (Houston fire/other, Austin nurse_health, Columbus fire).
2. `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — Houston police, Austin police/fire, Columbus police/other, Cleveland police/fire/other (8 rows).
3. `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — Somerville police, Wayland fire, Franklin (police/fire/public_works/library/other), Boston clerical_admin, Georgetown (police/other) (10 rows).
4. `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv` — Seekonk (public_works/library/police/fire/teacher), Wayland other (6 rows).
5. `docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv` — San Antonio (police/fire), Cincinnati (police/police_sup/fire/other), Toledo (police/fire/other) (9 rows).

Total: 37 codified contract rows, unioned via `scripts/build_codify_evidence_viewer.py` into the 781-row evidence layer, 0 duplicate `evidence_id`s.

## Known limitations (carried into every report section)

- **Codify is binary present/not_found** (plus a rare `unclear` from boundary-leakage cleanup) — it records whether a mechanism's language was found in a curated source window, not a strength, frequency, or dollar-value measurement.
- **Evidence patterns do not prove causality.** A mechanism being coded `present` in a contract's text says nothing about how much it actually moved that contract's wages relative to a counterfactual without it.
- **9 rows are flagged/unverified** (`viewer_verified=0`) and are hidden by default in the viewer and excluded from this report's headline counts — they remain in the underlying evidence layer, not deleted, but are not used for graph claims unless a figure explicitly says otherwise.
- **Texas non-safety coverage remains uneven.** Only Houston has a genuine non-safety codified row (`tx_houston_other_2024`, HOPE/AFSCME Local 123). Austin has no non-safety row at all. San Antonio has no non-safety row at all.
- **San Antonio is police/fire only, not fully matched** — it was deliberately added for institutional-contrast value (full Chapter 174 bargaining without Houston's population-triggered compulsory-arbitration exception), not as a third matched Texas city.
- **Austin's comparison is safety-adjacent through EMS/nurse-health**, not an ordinary civilian/clerical comparison — Austin EMS is civil-service-protected and statutorily adjacent to police/fire (shared Ch.143 Civil Service Commission), a caveat that must travel with any Austin finding.
- **Ohio is strongest for matched city triads** — all four codified Ohio cities (Columbus, Cleveland, Cincinnati, Toledo) have police, fire, and a non-safety row, making Ohio the cleanest state for direct safety-vs-non-safety, same-city, same-cycle-window comparisons in this evidence layer.

## Scope boundaries for this run

- No GABRIEL/codify, Harvard Proxy, or model/API calls of any kind.
- No new source collection, no web search, no FOIA/PRR.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`.
- No final report PDF/DOCX artifacts — Markdown, CSV, and PNG/SVG only, for human review before any formatting run.
- No causal claims stronger than the evidence supports — every table and graph in this scaffold is framed as a coded-evidence pattern, not a causal estimate.
