# GABRIEL Codify Massachusetts Preflight — 2026-07-09 (run date 2026-07-10)

## Purpose

This run has two parts: (1) fix the evidence-window construction defect the Texas/Ohio scale-up audit surfaced (a window-assembly header containing mechanism/codebook vocabulary was echoed back by the model as if it were source text), and (2) only once that fix is verified, run a curated, capped Massachusetts codify batch and append it to the durable evidence layer built so far.

## Repo state at start of this run

- `git status`: clean except the pre-existing, untracked `tmp/` scratch directory. No unexpected uncommitted changes.
- Latest commit: `cd9c70f` — "Scale codify across Texas and Ohio".
- `data/contracts.csv`: **44 data rows** (unchanged).
- `data/city_coverage.csv`: **44 data rows** (unchanged).
- `docs/analysis/gabriel_codify_evidence_layer.csv`: **265 data rows** (148 present, 117 not_found — the pilot + Texas/Ohio scale-up combined).

All counts match this run's expected starting state exactly.

## Texas/Ohio evidence already represented

12 contract_ids across 4 matched cities (Houston, Austin, Columbus, Cleveland), each with a safety and non-safety comparison occupation: `tx_houston_fire_2024`, `tx_houston_other_2024`, `tx_austin_nursehealth_2023`, `oh_columbus_fire_2023` (4-row pilot); `tx_houston_police_2024`, `tx_austin_police_2024`, `tx_austin_fire_2023`, `oh_columbus_police_2023`, `oh_columbus_other_2024`, `oh_cleveland_police_2025`, `oh_cleveland_fire_2025`, `oh_cleveland_other_2022` (scale-up). Massachusetts has zero rows in the evidence layer before this run.

## The Cleveland Fire header artifact and why it matters

`oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`'s "present" excerpt is this project's own injected window-section header text (`"Arbitration / impasse backstop (legacy code -- may be interest OR grievance arbitration; distinguish from text) [char 1792] --- sseces 45 ..."`), not genuine source-document text. The underlying corpus passage under that heading was unreadable OCR table-of-contents garbage; with nothing usable to extract, the model echoed the header back, and a naive "is this excerpt a substring of window_text" grounding check passed trivially, because the header IS literally in window_text — this project put it there. This matters because:
1. It is a **systematic** risk, not a one-off: any window section whose underlying text is unusable creates the same opening for the model to fall back on this project's own scaffolding.
2. It **passes** the existing grounding check, so it does not surface as "unsupported" — only a human review of `notes` caught it. A future run without repair could accumulate more of these, undetected by the automated check alone.
3. It directly threatens the two things this evidence layer exists to protect: verbatim-only excerpts, and a viewer that never promotes non-genuine text as confirmed evidence.

## Neutral-header repair strategy

1. **Window construction** (this run's evidence-windows CSV, built fresh from real corpus PDF text via `pdftotext`): every added separator is strictly `--- Excerpt N [location if known] ---` — a bare sequence number and, where available, a genuine `Article`/`Section` marker found immediately preceding the excerpt in the source text. No mechanism name, codebook label, or analytical hint (e.g. "Arbitration / impasse backstop", "Mechanism") appears anywhere in a separator.
2. **`scripts/gabriel_codify_pilot.py`** gained a read-time mechanism-label contamination check (`_check_window_contamination`): before dry-run OR live calls, every row's `window_text` is scanned for the codebook's own 19 attribute keys (`CATEGORIES.keys()`, excluding the bare word `"other"`, which is a common English word and would false-positive constantly) plus the generic tells `"Mechanism"` and `"Arbitration / impasse"`. Any hit is a hard failure (`sys.exit(1)`), not a warning — this is a bright-line safety check, the same posture as `HARD_MAX_CALLS`. Verified against both a clean run (passes) and a deliberately re-contaminated copy of the same windows CSV (fails loudly, naming the offending contract_id and matched string).
3. **`scripts/build_codify_evidence_viewer.py`** gained a `notes_flag`/`viewer_verified` pair of columns so that even if a future artifact slips past both the contamination check and the automated grounding check, a human-added `notes` flag (marker string `METHODOLOGY FLAG`) is enough to keep the row out of the viewer's default "verified evidence" view — without deleting it from the durable CSV. See Task C for detail; this is a second, independent layer of defense on top of the window-construction fix.

## Massachusetts selection criteria

Up to 10 contract_ids from `data/contracts.csv`, chosen to collectively cover: police/fire safety sources; at least one arbitration/impasse-heavy source (Somerville's JLMC interest-arbitration award, explicitly requested even though unmatched); public works/DPW; clerical/admin; library; custodial/mixed-municipal; at least two matched Massachusetts cities/towns; clean text quality preferred. Full selection and rationale in Task D's deliverable, `gabriel_codify_massachusetts_sample_selection_2026-07-09.md`.

## Live-call cap

- **Hard cap for this run: 10 live calls**, one per selected row.
- `scripts/gabriel_codify_pilot.py`'s in-code `HARD_MAX_CALLS` is raised from `8` to `10` as a deliberate, documented code change for this run only. `--max-calls` above 10 is still refused.
- One `gabriel.codify()` invocation per row (not batched).

## Credential / adapter safety check (presence only, no values read)

- `HARVARD_SUBSCRIPTION_KEY` is **not** set in the ambient shell environment.
- Loading the repo's git-ignored `.env` file via `python-dotenv`'s `load_dotenv()` makes it available (checked as a boolean only — never printed, logged, or written to any file). Live calls are expected to be possible, contingent on the dry run and the first live call succeeding.

## Stop rules

- Fix the header-leakage defect and verify the contamination check BEFORE building any Massachusetts window or making any live call.
- Dry run first, always; the contamination check must pass on the dry run before `--live` is attempted.
- If credentials are unavailable at live-run time, do not live-run; dry-run outputs only.
- If the first live call fails for a nontrivial adapter/API reason, stop all live calls immediately — do not retry.
- If a later row fails for a row-specific text/window reason, skip that row, record why, and continue only if the failure is clearly row-specific.
- Never exceed 10 live calls in this run.
- Do not run the full corpus.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md` at any point.
