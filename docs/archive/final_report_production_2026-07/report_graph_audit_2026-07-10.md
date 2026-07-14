# Report Graph Audit — 2026-07-10

## 1. Purpose

This memo documents the graph and table inputs used in `docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md` and its appendix (`docs/analysis/report_appendix_tables_2026-07-10.md`): what evidence filter produced them, exact counts behind them, a full inventory of the underlying asset files, caveats specific to each figure, and a file-reference check confirming every graph the report cites actually exists. It was requested by the original report-scaffold task but not created before that run's commit; this run (a report review/polish pass) creates it as a deterministic documentation task — no new analysis, no GABRIEL/model calls.

## 2. Evidence filter

Every headline graph and every headline count in the report scaffold uses **only** evidence rows meeting both conditions:

- `evidence_status = present`
- `viewer_verified = 1` (which itself requires `source_grounding_status = grounded` and no reviewer flag)

Flagged/unverified `present` rows (9 rows — see Section 3) are **excluded** from every headline graph, table, and count in the report scaffold and appendix. They are not deleted: they remain in the full 781-row evidence layer and are visible in the viewer (`gabriel_codify_excerpt_browser_latest.html`) via its "Show unverified / unsupported evidence" toggle. Unless a figure or table is explicitly labeled otherwise, "present" anywhere in the report scaffold, appendix, or this audit means verified present under this filter — not the raw 293-row `present` count.

## 3. Evidence-layer counts

From `docs/analysis/gabriel_codify_evidence_layer.csv`, as of this run:

- **Total rows: 781.**
- `evidence_status=present`: **293**. `not_found`: **488**.
- `source_grounding_status=grounded`: **289** (grounding is only meaningful for a returned excerpt; all 488 `not_found` rows are `not_applicable`).
- **Verified grounded present (headline-graph evidence): 284.**
- **Flagged/unverified present (excluded from headline graphs): 9** — `oh_cleveland_fire_2025` (window-header-leakage artifact, Texas/Ohio scale-up batch); `ma_franklin_fire_2022`, `ma_franklin_public_works_2022`, `ma_franklin_library_2022`, `ma_boston_clerical_admin_2023` (excerpt-boundary-leakage recurrence, Massachusetts batch); `ma_seekonk_public_works_2023`, `ma_seekonk_library_2023`, `ma_seekonk_police_2022`, `ma_seekonk_teacher_2021` (boundary-leakage cases, Seekonk/Wayland batch). Full detail in `report_evidence_layer_audit_2026-07-10.md`.
- **Codified contracts: 37** of 53 total `data/contracts.csv` rows (16 Massachusetts contracts remain uncodified).
- **States/cities covered:** Massachusetts (Boston, Franklin, Georgetown, Seekonk, Somerville, Wayland — 6 cities), Texas (Austin, Houston, San Antonio — 3 cities), Ohio (Cincinnati, Cleveland, Columbus, Toledo — 4 cities). 13 distinct cities with evidence-layer rows.

## 4. Asset inventory

### CSVs (`docs/analysis/report_assets/`)

- `city_mechanism_matrix_2026-07-10.csv`
- `mechanism_presence_by_occupation_2026-07-10.csv`
- `mechanism_presence_by_state_2026-07-10.csv`
- `mechanism_presence_by_state_occupation_2026-07-10.csv`
- `source_inventory_for_report_2026-07-10.csv`
- `top_mechanisms_by_group_2026-07-10.csv`

All 6 confirmed present and parse cleanly (Python `csv` module, no width mismatches, no blank rows).

### Graph PNG/SVG files (`docs/analysis/report_assets/`)

- `mechanism_presence_overall_by_safety_group_2026-07-10` (.png + .svg)
- `mechanism_presence_by_state_2026-07-10` (.png + .svg)
- `arbitration_distinction_by_state_occupation_2026-07-10` (.png + .svg)
- `pressure_conversion_mechanisms_by_occupation_2026-07-10` (.png + .svg)
- `ohio_matched_triad_mechanism_matrix_2026-07-10` (.png + .svg)
- `massachusetts_cross_occupation_matrix_2026-07-10` (.png + .svg)
- `texas_institutional_contrast_2026-07-10` (.png + .svg)

All 7 figures confirmed present with a matching PNG and SVG pair — no exceptions this run.

Six of the seven figures are embedded inline in the report scaffold (see Section 6). `mechanism_presence_by_state_2026-07-10` is generated but not embedded inline — it is referenced as an appendix-only figure (`report_appendix_tables_2026-07-10.md`, Section C), paired with `mechanism_presence_by_state_2026-07-10.csv`.

## 5. Graph-specific caveats

- **Texas graph (`texas_institutional_contrast_2026-07-10`) is institutionally uneven, not a like-for-like state comparison.** San Antonio contributes police/fire only (no confirmed non-safety bargaining channel — deliberately unmatched, added for institutional-contrast value). Austin's non-safety comparison runs through EMS/nurse-health, which is safety-adjacent (civil-service-protected, statutorily linked to police/fire via Chapter 143) rather than an ordinary civilian/clerical unit. Only Houston has a genuine non-safety codified row. Several Texas bars in this figure represent a single source each — read any 0%/100% value as a small-sample artifact, not a robust state-level finding.
- **Ohio graph (`ohio_matched_triad_mechanism_matrix_2026-07-10`) is this corpus's strongest matched-triad case.** All four codified Ohio cities (Columbus, Cleveland, Cincinnati, Toledo) have a codified police, fire, and non-safety ("other") row under the same statewide statutory framework (ORC Chapter 4117/SERB) — the cleanest same-city, same-cycle-window safety-vs-non-safety comparison available in this evidence layer.
- **Massachusetts graph (`massachusetts_cross_occupation_matrix_2026-07-10`) is the densest cross-occupation comparison but not a uniform grid.** Not every Massachusetts town/city in the corpus has every occupation class codified — Franklin and Seekonk each span five occupation classes in one city and cycle window, but Boston, Georgetown, Somerville, and Wayland each contribute a narrower slice (1-2 occupation classes). Treat the Massachusetts figure as an aggregation across cities of uneven depth, not a single city's full occupational picture.
- **Binary codify cannot measure intensity, frequency, or causal weight.** Every count behind every figure in this report answers "was this mechanism's language coded present in a curated excerpt window," not "how much did this mechanism matter" or "how strong is this clause." A higher bar for one group over another is a higher rate of coded presence, not a larger dollar or causal effect.

## 6. File-reference checks

### 6a. Every graph referenced in the report scaffold exists

| inline reference (scaffold line) | file | exists |
|---|---|---|
| line 44 | `report_assets/mechanism_presence_overall_by_safety_group_2026-07-10.png` | yes |
| line 54 | `report_assets/arbitration_distinction_by_state_occupation_2026-07-10.png` | yes |
| line 68 | `report_assets/pressure_conversion_mechanisms_by_occupation_2026-07-10.png` | yes |
| line 76 | `report_assets/massachusetts_cross_occupation_matrix_2026-07-10.png` | yes |
| line 82 | `report_assets/texas_institutional_contrast_2026-07-10.png` | yes |
| line 88 | `report_assets/ohio_matched_triad_mechanism_matrix_2026-07-10.png` | yes |

All 6 inline `![...]()` image references in the report scaffold resolve to an existing file, path relative to `docs/analysis/`. 0 broken references found.

### 6b. Every graph file has a matching PNG and SVG

All 7 figures listed in Section 4 have both a `.png` and a `.svg` file present — 0 unpaired files found. No exceptions to document this run.

### 6c. This audit lists every generated asset

Cross-checked this document's Section 4 against a full directory listing of `docs/analysis/report_assets/` (20 files: 6 CSV + 7 PNG + 7 SVG) — every file is accounted for above, and no file in the directory is undocumented.
