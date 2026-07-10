# GABRIEL Codify Viewer Build Audit — 2026-07-09 (updated 2026-07-10: Seekonk/Wayland append/union rebuild)

This memo supersedes the four same-named memos from earlier (repo/data-facing build, PI-facing overhaul of the 4-row pilot output, Texas/Ohio scale-up append/union rebuild, Massachusetts append/union rebuild). This update audits the rebuild that unions all four codify output files — the original pilot, the Texas/Ohio scale-up, the Massachusetts batch, and this run's new Seekonk/Wayland batch.

## Builder command

```text
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_seekonk_wayland.html
```

Run exactly as given in this run's task instructions (no CLI adjustment needed — the builder's append/union mode and `--archive-html` alias, both already built in prior sessions, handled a 4th input file without any code change). Both earlier archival copies (`..._2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html`) are confirmed untouched via `git status`.

## Input files included

1. `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` — original 4-row pilot output (92 rows).
2. `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — Texas/Ohio scale-up output (173 rows).
3. `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — Massachusetts scale-up output (214 rows).
4. `docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv` — this run's new Seekonk/Wayland output (124 rows).

## Evidence-layer row counts after this rebuild

- Input rows read (total, across all four files): **603** (92 + 173 + 214 + 124).
- Duplicate rows skipped: **0** (all four input files cover entirely disjoint contract_ids).
- Evidence rows written: **603**.
- `present` (evidence found): **261**.
- `not_found`: **342**.
- `evidence_id` duplicates: **0**.
- `contract_label` resolved from `data/contracts.csv` for **603/603** rows.
- **Verified present (viewer default): 252.** **Unverified/unsupported present (hidden by default): 9.**

## Verified vs. unsupported/unverified count

`present` (261) splits into:
- **252 verified** — evidence found, confirmed grounded, no reviewer flag. Shown by default.
- **9 unverified/flagged** — hidden by default, shown only via the "Show unverified / unsupported evidence" toggle, rendered with an on-card warning:
  - `oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop` (Texas/Ohio scale-up's window-header-leakage artifact).
  - `ma_franklin_fire_2022`, `ma_franklin_public_works_2022`, `ma_franklin_library_2022`, `ma_boston_clerical_admin_2023` (Massachusetts scale-up's excerpt-boundary-leakage recurrence, 4 rows).
  - `ma_seekonk_public_works_2023`, `ma_seekonk_library_2023`, `ma_seekonk_police_2022`, `ma_seekonk_teacher_2021` (this run's boundary-leakage cases, all now automatically detected and cleaned inline by the live-run pipeline itself — see `gabriel_codify_seekonk_wayland_audit_2026-07-10.md`).

All 9 have `notes_flag=1` (a `METHODOLOGY FLAG` note) and `viewer_verified=0`, confirmed programmatically on the rebuilt evidence layer.

## Viewer paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` — 1,096,717 bytes.
- **Dated archival copy for this run:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_seekonk_wayland.html` — 1,096,717 bytes, byte-identical to latest.
- **Untouched, still present:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html` — all three confirmed unmodified via `git status`.

## Whether Seekonk/Wayland now appear

**Yes.** The parsed `EVIDENCE` data's Massachusetts cities now include **Seekonk** for the first time (`public_works`, `library`, `police`, `fire`, `teacher` — a fully matched city, 5 occupation classes), alongside the existing Boston, Franklin, Georgetown, Somerville, and Wayland. Wayland now also has an `other` occupation class (dispatch/nurse content, OCR-recovered) in addition to its prior `fire` (JLMC award) row.

## Whether flagged rows remain hidden by default

**Yes**, confirmed programmatically: all 9 flagged rows across all three codify batches (Texas/Ohio: 1, Massachusetts: 4, Seekonk/Wayland: 4) have `viewer_verified: "0"` in the rebuilt evidence data and will not appear in the viewer's default filtered view.

## Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` — passed.
- `json.loads()` on both embedded `EVIDENCE` (603 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- All 9 flagged rows confirmed present in the parsed `EVIDENCE` data with `notes_flag: "1"` and `viewer_verified: "0"`.
- No code changes to `scripts/build_codify_evidence_viewer.py` were needed this session — Task C's requirements (default-verified-only view, toggle, warning banner, "Verified in source text" / "Not verified in source text" labels) were all already implemented in the prior session and re-verified as still correct against this run's new data.

## Manual testing recommendations

1. Open `docs/analysis/gabriel_codify_excerpt_browser_latest.html` directly in a browser.
2. Confirm the state → city cascading filter now offers Seekonk under Massachusetts, and that selecting it shows all 5 occupation classes.
3. With default filters, confirm none of the 9 flagged rows appear — filter to `ma_seekonk_teacher_2021` and confirm `no_strike_or_work_stoppage_constraint` does not show as a present card by default.
4. Toggle "Show unverified / unsupported evidence" and confirm all 9 flagged rows now appear, each with the on-card warning banner.
5. Confirm the sidebar's "Unverified / unsupported" count reads 9 and "Verified present" reads 252.
6. Filter to `ma_wayland_other_2021` and confirm the dispatch/nurse-relevant cards (training/certification, civil service, union security) render with plain-English labels correctly.
7. Copy-excerpt/copy-citation buttons — still not interactively tested in a real browser this session; same standing limitation as every prior audit.
