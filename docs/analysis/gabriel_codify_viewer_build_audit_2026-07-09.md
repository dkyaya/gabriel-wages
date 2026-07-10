# GABRIEL Codify Viewer Build Audit — 2026-07-09 (updated: Massachusetts append/union rebuild)

This memo supersedes the three same-named memos from earlier (repo/data-facing build, PI-facing overhaul of the 4-row pilot output, then the Texas/Ohio scale-up append/union rebuild). This update audits the rebuild that unions all three codify output files — the original pilot, the Texas/Ohio scale-up, and this run's new Massachusetts batch — plus the viewer's new unverified/unsupported-evidence gating (Task C, this session).

## Builder command

```text
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html
```

Run exactly as given in this run's task instructions. Because `--html-out` and `--archive-html` are aliases for the same destination (last one wins, by design — see the Texas/Ohio build audit), and `--html-latest-out` was left at its default, the actual effect is: dated archival copy → `gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html`, stable/shareable copy → `gabriel_codify_excerpt_browser_latest.html` (the default). Both earlier same-day archival copies (`..._2026-07-09.html`, `..._2026-07-09_scaleup.html`) are confirmed untouched via `git status`.

## Input files included

1. `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` — original 4-row pilot output (92 rows).
2. `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv` — Texas/Ohio scale-up output (173 rows).
3. `docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — this run's new Massachusetts output (214 rows).

## Evidence-layer row counts after this rebuild

- Input rows read (total, across all three files): **479** (92 + 173 + 214).
- Duplicate rows skipped: **0** (the three input files cover entirely disjoint contract_ids).
- Evidence rows written: **479**.
- `present` (evidence found): **218**.
- `not_found`: **261**.
- `evidence_id` duplicates: **0**.
- `contract_label` resolved from `data/contracts.csv` for **479/479** rows (all 22 distinct contract_ids across all three batches are present in `data/contracts.csv`).
- **Verified present (viewer default): 213.** **Unverified/unsupported present (hidden by default): 5.** This is the first rebuild to use the new `viewer_verified` field (Task C) rather than treating all `source_grounding_status=grounded` present rows as equally trustworthy — see below.

## Verified vs. unsupported/unverified count (Task C)

`present` (218) splits into:
- **213 verified** — evidence found, confirmed grounded, no reviewer flag. Shown by default.
- **5 unverified/flagged** — hidden by default, shown only via the new "Show unverified / unsupported evidence" toggle, and rendered with an explicit on-card warning:
  - `oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop` (Texas/Ohio scale-up's original window-header-leakage artifact).
  - `ma_franklin_fire_2022` / `training_certification_credential_premiums`, `ma_franklin_public_works_2022` / `premium_pay_differentials`, `ma_franklin_library_2022` / `benefits_total_compensation_or_pension`, `ma_boston_clerical_admin_2023` / `premium_pay_differentials` (this run's milder excerpt-boundary-leakage recurrence — see `gabriel_codify_massachusetts_audit_2026-07-09.md`).

All 5 have `source_grounding_status=grounded` (they are literal substrings of their window_text) but `notes_flag=1` (a human/automated reviewer note begins with `METHODOLOGY FLAG`), so `viewer_verified=0` for all 5 — confirmed programmatically on the rebuilt evidence layer.

## Viewer paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` — 877,790 bytes.
- **Dated archival copy for this run:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html` — 877,790 bytes, byte-identical to latest.
- **Untouched, still present:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` (92-row, from the viewer overhaul) and `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html` (265-row, from the Texas/Ohio scale-up) — both confirmed unmodified via `git status`.

## Whether cascading filters and plain-English labels remain intact

Yes — the cascading-filter and label-rendering logic (`rowsMatchingExcept()`, `rebuildSelectOptions()`, `rebuildAttributeOptions()`, label maps) is unchanged this session; only the verified-evidence gating (`viewer_verified`/`notes_flag`, the new "Show unverified / unsupported evidence" checkbox, and the per-card/per-table-row warning) was added on top. Verified directly on the rebuilt `_latest.html`:
- `node --check` on the extracted `<script>` block — **passed**.
- `json.loads()` on both embedded `const EVIDENCE = [...]` (479 rows) and `const ATTRIBUTES = [...]` (19 entries) — both parsed cleanly.
- All 5 flagged rows confirmed present in the parsed `EVIDENCE` data with `notes_flag: "1"` and `viewer_verified: "0"`.

## Whether Massachusetts now appears in the state filter

**Yes.** The parsed `EVIDENCE` data's distinct `state` values are now `['MA', 'OH', 'TX']` (previously `['OH', 'TX']`). Massachusetts contributes 214 rows across 5 cities: Franklin (fire, library, other, police, public_works — a fully matched city, 5 occupation classes), Georgetown (other, police — matched), Somerville (police only, unmatched in this sample by design), Boston (clerical_admin only, unmatched in this sample by design), Wayland (fire only, unmatched in this sample by design).

## Manual testing recommendations

1. Open `docs/analysis/gabriel_codify_excerpt_browser_latest.html` directly in a browser.
2. Confirm the state dropdown now offers Massachusetts alongside Texas and Ohio, and that selecting it narrows the city dropdown to the 5 Massachusetts cities above.
3. With default filters (nothing toggled), confirm none of the 5 flagged rows appear — filter to `ma_franklin_library_2022` and confirm `benefits_total_compensation_or_pension` does not show as a present card by default.
4. Toggle "Show unverified / unsupported evidence" and confirm all 5 flagged rows now appear, each with the on-card warning banner and a "Not verified in source text" badge (not the ordinary "Verified in source text" badge).
5. Confirm the sidebar's "Unverified / unsupported" count reads 5 and "Verified present" reads 213.
6. Copy-excerpt/copy-citation buttons — still not interactively tested in a real browser this session; same standing limitation as every prior audit.

## Next step before scaling further

Fix the excerpt-boundary-leakage issue identified in `gabriel_codify_massachusetts_audit_2026-07-09.md` (a larger break between adjacent window excerpts, or trimming to clean sentence boundaries) before the next codify batch. After that, either a manual PI-facing viewer QA pass, or a further state/city acquisition batch (a larger Massachusetts sample — Seekonk is a strong, fully-matched candidate not used this run — or a new state), are both reasonable next steps.
