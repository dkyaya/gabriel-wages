# GABRIEL Codify Viewer Build Audit — 2026-07-09 (updated 2026-07-10: expanded Texas/Ohio append/union rebuild)

This memo supersedes the five same-named memos from earlier (repo/data-facing build, PI-facing overhaul of the 4-row pilot output, Texas/Ohio scale-up append/union rebuild, Massachusetts append/union rebuild, Seekonk/Wayland append/union rebuild). This update audits the rebuild that unions all five codify output files — the original pilot, the Texas/Ohio scale-up, the Massachusetts batch, the Seekonk/Wayland batch, and this run's new expanded Texas/Ohio batch (San Antonio, Cincinnati, Toledo).

## Builder command

```text
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv \
  --input docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_expanded_texas_ohio.html
```

Run exactly as given in this run's task instructions (no CLI adjustment needed — the builder's append/union mode and `--archive-html` alias handled a 5th input file without any code change). All four earlier archival copies (`..._2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html`, `..._2026-07-10_seekonk_wayland.html`) are confirmed untouched via `git status`.

## Input files included

1. `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` — original 4-row pilot output (92 rows).
2. `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — Texas/Ohio scale-up output (173 rows).
3. `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — Massachusetts scale-up output (214 rows).
4. `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv` — Seekonk/Wayland output (124 rows).
5. `docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv` — this run's new San Antonio/Cincinnati/Toledo output (178 rows).

## Evidence-layer row counts after this rebuild

- Input rows read (total, across all five files): **781** (92 + 173 + 214 + 124 + 178).
- Duplicate rows skipped: **0** (all five input files cover entirely disjoint contract_ids).
- Evidence rows written: **781**.
- `present` (evidence found): **293**.
- `not_found`: **488**.
- `evidence_id` duplicates: **0**.
- `contract_label` resolved from `data/contracts.csv` for **781/781** rows.
- **Verified present (viewer default): 284.** **Unverified/unsupported present (hidden by default): 9** (unchanged from before this run — this run's batch added 0 new flagged rows; see below).

## Verified vs. unsupported/unverified count

`present` (293) splits into:
- **284 verified** — evidence found, confirmed grounded, no reviewer flag. Shown by default. (252 carried over from before this run + 32 new, 100% verified, from this run's batch.)
- **9 unverified/flagged** — all pre-existing from earlier batches; this run's 32 new `present` rows are all clean (0 boundary-leak flags, 0 mechanism-label-leak flags — see `gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md`):
  - `oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop` (Texas/Ohio scale-up's window-header-leakage artifact).
  - `ma_franklin_fire_2022`, `ma_franklin_public_works_2022`, `ma_franklin_library_2022`, `ma_boston_clerical_admin_2023` (Massachusetts scale-up's excerpt-boundary-leakage recurrence, 4 rows).
  - `ma_seekonk_public_works_2023`, `ma_seekonk_library_2023`, `ma_seekonk_police_2022`, `ma_seekonk_teacher_2021` (Seekonk/Wayland boundary-leakage cases).

All 9 have `notes_flag=1` (a `METHODOLOGY FLAG` note) and `viewer_verified=0`, confirmed programmatically on the rebuilt evidence layer.

## Viewer paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html`.
- **Dated archival copy for this run:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_expanded_texas_ohio.html`, byte-identical to latest.
- **Untouched, still present:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html`, `..._2026-07-10_seekonk_wayland.html` — all four confirmed unmodified via `git status`.

## Whether San Antonio, Cincinnati, and Toledo now appear

**Yes.** The parsed `EVIDENCE` data now includes San Antonio (TX — police, fire, both newly OCR-recovered/clean), Cincinnati (OH — police ×2 rank-split rows, fire, other), and Toledo (OH — police, fire, other) for the first time. Confirmed via `json.loads()` on the embedded `EVIDENCE` array: `'San Antonio' in cities`, `'Cincinnati' in cities`, `'Toledo' in cities` all `True`. Ohio's state filter now spans four cities with evidence (Columbus, Cleveland, Cincinnati, Toledo); Texas now spans three (Houston, Austin, San Antonio).

## Whether flagged rows remain hidden by default

**Yes**, confirmed programmatically: all 9 flagged rows across the three batches that produced them have `viewer_verified: "0"` in the rebuilt evidence data and will not appear in the viewer's default filtered view. This run's batch contributed 0 new flagged rows.

## Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` — passed.
- `json.loads()` on both embedded `EVIDENCE` (781 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- All 9 flagged rows confirmed present in the parsed `EVIDENCE` data with `notes_flag: "1"` and `viewer_verified: "0"`.
- No code changes to `scripts/build_codify_evidence_viewer.py` were needed this session — the append/union mode and verified-evidence gating (built in prior sessions) handled the 5th input file without modification.

## Manual testing recommendations

1. Open `docs/analysis/gabriel_codify_excerpt_browser_latest.html` directly in a browser.
2. Confirm the state → city cascading filter now offers San Antonio under Texas and Cincinnati/Toledo under Ohio.
3. Filter to `tx_san_antonio_police_2022` and confirm the interest-arbitration-vs-grievance-arbitration distinction renders as two separate mechanism cards (not merged).
4. With default filters, confirm all 9 pre-existing flagged rows still do not appear; toggle "Show unverified / unsupported evidence" and confirm they still render with the warning banner.
5. Confirm the sidebar's "Verified present" count reads 284 and "Unverified / unsupported" reads 9.
6. Filter to `oh_cincinnati_other_2025` or `oh_toledo_other_2024` and confirm the grievance/mediation and no-strike cards render with plain-English labels correctly.
7. Copy-excerpt/copy-citation buttons — still not interactively tested in a real browser this session; same standing limitation as every prior audit.
