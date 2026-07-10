# GABRIEL Codify Seekonk/Wayland Preflight — 2026-07-10

## Purpose

This run has three parts: (1) fix the Massachusetts scale-up's excerpt-boundary leakage defect at its root (in `scripts/gabriel_codify_pilot.py` itself, not a one-off downstream script), (2) attempt a bounded OCR/text-recovery pass on the one Wayland corpus file that previously extracted to ~0 usable characters, and (3) run a small, capped codify batch adding Seekonk and (if recovered) Wayland rows, then append the result to the durable evidence layer.

## Repo state at start of this run

- `git status`: clean except the pre-existing, untracked `tmp/` scratch directory. No unexpected uncommitted changes.
- Latest commit: `4f10a4f` — "Add Massachusetts to codify viewer".
- `data/contracts.csv`: **44 data rows** (unchanged).
- `data/city_coverage.csv`: **44 data rows** (unchanged).
- `docs/analysis/gabriel_codify_evidence_layer.csv`: **479 data rows** (218 present, 261 not_found — pilot + Texas/Ohio + Massachusetts combined).

All counts match this run's expected starting state exactly.

## States/cities currently represented in the viewer

- **MA:** Boston, Franklin, Georgetown, Somerville, Wayland (Wayland only via the `ma_wayland_fire_jlmc_2020` row so far — no other Wayland occupation class has been codified yet).
- **OH:** Cleveland, Columbus.
- **TX:** Austin, Houston.
- **Not yet represented:** Seekonk (any occupation class).

## The excerpt-boundary leakage issue

The Massachusetts scale-up run (2026-07-09) fixed the Texas/Ohio run's full-fabrication window-header-leakage defect (neutral `--- Excerpt N [location] ---` separators, plus a hard-fail input-side contamination check), but a milder recurrence appeared: 4 of 70 present excerpts had a few characters of this project's own separator syntax leak into an otherwise-genuine excerpt, because the model's verbatim-copied span crossed the boundary between two adjacent window sections (e.g. `'Section 14.2] ---\na part\nof this agreement...'`). These were caught by an ad-hoc downstream Python script and flagged via a `METHODOLOGY FLAG` note, but the fix was not built into the reusable pipeline — a future codify run using `scripts/gabriel_codify_pilot.py` directly (without remembering to also run a bespoke cleanup script afterward) would reproduce the same defect with no protection.

## Repair strategy

Moved the reshape-and-validate step (wide-format `gabriel.codify()` output → this project's long/tidy evidence-output schema, with grounding checks) **into `scripts/gabriel_codify_pilot.py` itself**, as a new `reshape_and_validate_outputs()` function called automatically at the end of every live run. It:
1. Detects a leaked separator fragment in each returned excerpt via three regex patterns (a leading/trailing "opener" fragment `--- Excerpt N [...`, a "closer" fragment `...] ---`, and any bare run of 3+ hyphens — genuine CBA prose essentially never contains a literal `---`).
2. If found, splits the excerpt at the fragment and keeps only the **longer** of the two remaining sides — this guarantees the cleaned excerpt is always an untouched, single contiguous substring of what the model actually returned (never fabricated or spliced from two different source locations).
3. Downgrades `source_grounding_status` to `unclear` (or `unsupported` if nothing usable survives) whenever leakage was detected, regardless of whether cleanup succeeded — contamination never silently upgrades back to `grounded`.
4. Separately checks every returned excerpt for the codebook's own mechanism vocabulary (a milder cousin of the existing input-side contamination check, now applied to outputs too) and flags similarly if found.
5. Writes a `validated_outputs.csv` directly into the run's `tmp/gabriel_codify_pilots/<timestamp>/` directory — this becomes the direct source for the durable `docs/analysis/*_outputs_*.csv` file (copy, not re-derive), removing the need for a bespoke one-off parsing script each session.

Verified via unit tests against the 4 real leaked excerpts from the Massachusetts run (all clean correctly) and a synthetic end-to-end pipeline test (a clean excerpt passes through unchanged; a deliberately-contaminated excerpt is cleaned, downgraded to `unclear`, and flagged) before any live call this session.

## Seekonk/Wayland candidate rows found in `data/contracts.csv`

| contract_id | occupation_class | text_quality |
|---|---|---|
| `ma_seekonk_police_2022` | police | clean |
| `ma_seekonk_fire_2022` | fire | clean |
| `ma_seekonk_clerical_admin_2021` | clerical_admin | ocr_messy |
| `ma_seekonk_teacher_2021` | teacher | clean |
| `ma_seekonk_public_works_2023` | public_works | clean |
| `ma_seekonk_library_2023` | library | clean |
| `ma_wayland_police_2020` | police | ocr_messy |
| `ma_wayland_fire_2020` | fire | ocr_messy |
| `ma_wayland_other_2021` | other | ocr_messy — **the dispatch/nurse_health target; prior session's `pdftotext` pass extracted ~0 usable characters** |
| `ma_wayland_public_works_2020` | public_works | ocr_messy |
| `ma_wayland_library_2020` | library | ocr_messy |
| `ma_wayland_fire_jlmc_2020` | fire | clean — **already codified in the Massachusetts scale-up** |

Full selection and rationale in Task D's deliverable, `gabriel_codify_seekonk_wayland_sample_selection_2026-07-10.md`. The Wayland OCR recovery attempt is documented separately in `wayland_bounded_ocr_recovery_2026-07-10.md`.

## Live-call cap

- **Hard cap for this run: 8 live calls**, one per selected row.
- `scripts/gabriel_codify_pilot.py`'s in-code `HARD_MAX_CALLS` is lowered from `10` (the Massachusetts run's cap) to `8` for this run, a deliberate, documented code change. `--max-calls` above 8 is still refused.

## Credential / adapter safety check (presence only, no values read)

- `HARVARD_SUBSCRIPTION_KEY` is **not** set in the ambient shell environment.
- Loading the repo's git-ignored `.env` file via `python-dotenv`'s `load_dotenv()` makes it available (checked as a boolean only). Live calls are expected to be possible, contingent on the dry run and the first live call succeeding.

## Stop rules

- Fix the excerpt-boundary leakage defect and verify it with unit tests BEFORE building any Seekonk/Wayland window or making any live call.
- Attempt Wayland OCR recovery within a bounded time/scope; if it remains unusable, exclude that specific row rather than force it in.
- Dry run first, always; both the input-side and (implicitly, via the fixed pipeline) output-side checks must be in place before `--live` is attempted.
- If credentials are unavailable at live-run time, do not live-run; dry-run outputs only.
- If the first live call fails for a nontrivial adapter/API reason, stop all live calls immediately — do not retry.
- If a later row fails for a row-specific text/window reason, skip that row, record why, and continue only if the failure is clearly row-specific.
- Never exceed 8 live calls in this run.
- Do not run the full corpus, do not download or ingest anything, do not use web search.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md` at any point.
