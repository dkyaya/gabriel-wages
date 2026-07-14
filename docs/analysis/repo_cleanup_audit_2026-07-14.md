# Repo Cleanup and Reorganization Audit — 2026-07-14

**Purpose:** a full-repo cleanup pass ahead of national-scale expansion, executed in one session. This document records what was inventoried, what was deleted, what was moved, what was deliberately retained despite looking old, and the retention policy this establishes going forward. A prior planning-only pass (`docs/archive/legacy_gabriel_pilot_2026-06/repo_declutter_plan_2026-07-01.md`) proposed a similar structure in 2026-07-01 but was never executed ("do not delete, move, or rename files yet" — that plan's own words); this session executed the equivalent work under this session's explicit authorization.

## 1. Starting state

- Repo root size: ~1.9GB. Breakdown: `.claude/` 595M (git worktrees — out of scope, see §2), `.venv/` 566M (gitignored Python env, untouched), `.git/` 243M (history, untouched), `tmp/` 232M, `corpus/` 207M, `inbox/` 95M, `docs/` 20M, top-level `analysis/` 7.5M, top-level `reports/` 3.0M.
- `docs/analysis/` alone held 240 files spanning 2026-06-16 through 2026-07-14 — the project's entire working-notebook history in one flat directory.
- `tmp/` held 57 old relay-bundle directories, 61 old relay-bundle zips, and several large scratch/OCR working directories (largest: a 74MB raw San Antonio OCR page-image cache, explicitly self-documented as "not committed — working scratch only" in its own referencing memo).
- A prior, never-executed declutter plan (`repo_declutter_plan_2026-07-01.md`) existed in `docs/analysis/`, confirming this cleanup had been correctly identified as needed weeks earlier.

## 2. Explicitly out of scope (not touched)

- **`.claude/`** (595M) — contains two live, git-registered worktrees (`git worktree list` confirms `remote-diagnosis`, locked, and `tx-oh-expansion-recovery`). This is Claude Code session infrastructure, not project analytical content; removing or restructuring it risks corrupting git's worktree metadata and is unrelated to this task's "research pipeline" scope. Left entirely alone.
- **`.venv/`** (566M) — a Python virtual environment, already gitignored, needed to run every script in this repo. Left alone.
- **`.git/`** (243M) — normal history overhead; no `git gc`/history-rewriting was performed (out of scope, and rewriting history would break every prior session's cited commit hashes).
- **`corpus/`** — inspected for non-canonical junk; found none (only PDFs, a small number of legitimate PA/NJ `.meta.json` sidecar files, and a `README.txt`). Untouched, per the task's explicit "do not edit corpus contents" instruction.
- **`inbox/`** — the active two-intake-path staging area (`AGENTS.md`'s ingest rules). Untouched except one explicitly-labeled orphan (see §4).

## 3. Reference/dependency check (Task 2)

Before moving or deleting anything: (a) grepped every candidate directory/file against the currently-active canonical docs (`state_city_claims_ledger.md`, `claim_testing_source_wave_methodology_2026-07-12.md`, `wage_mechanism_evidence_checklist.md`, `claim_register_2026-07-12.csv`, `hypothesis_tracker_2026-07-12.csv`, `docs/schema.md`, `AGENTS.md`) and against every active script's imports/CLI usage; (b) cross-checked every `--input` path used by `scripts/build_codify_evidence_viewer.py`'s 7-wave evidence-layer rebuild; (c) checked `raw_output_ref` pointers in `gabriel_codify_evidence_layer.csv` against `tmp/gabriel_codify_pilots/`.

This surfaced two genuine active dependencies that would have broken silently if not caught:

- **`docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.{md,csv}`** is directly cross-referenced by the currently-kept `gabriel_codify_seekonk_wayland_audit_2026-07-10.md` ("Cross-checking `ma_seekonk_public_works_2023`'s codify results against the prior sanitation-scan memo"). **Not archived** — left in `docs/analysis/` despite being from the same 2026-07-06 batch as ~40 other now-archived occupation-scoping memos.
- **`ingest/test_pipeline.py` imported `_is_clearly_irrelevant`/`_is_clearly_relevant` directly from `analysis/gabriel_pilot/run_gabriel.py`** — a genuine, still-load-bearing dependency from the current active test suite (`test_gabriel_relevance_boundaries`) into the legacy v7/v8 GABRIEL pilot script. This is exactly the kind of breakage Task 2 exists to catch. **Resolved, not just avoided** — see §5.

`tmp/gabriel_codify_pilots/` (2.8M, 20 run subdirectories) is directly referenced by the `raw_output_ref` column for every one of the 1039 rows in `gabriel_codify_evidence_layer.csv` — **kept in full**, not touched, despite living in `tmp/`.

## 4. Deletions (Task 3)

| What | Where | Why safe |
|---|---|---|
| 57 old relay-bundle directories + 61 old relay-bundle zips | `tmp/agent_relay_bundle_*`, `tmp/chatgpt_handoff_bundle_*`, `tmp/handoff_bundle_*` | Every bundle's content is already absorbed into current `PROGRESS.md`/`chatgpt_handoff_latest.md`/ledger entries; a fresh bundle is created at the end of every session including this one. Never git-tracked. |
| `tmp/san_antonio_ocr/` (74M: 218 page PNGs + 219 txt files) | `tmp/` | Self-documented as scratch-only in `san_antonio_police_bounded_ocr_recovery_2026-07-10.md` ("not committed — working scratch only"); the durable output already lives at `docs/analysis/san_antonio_police_bounded_ocr_extract_2026-07-10.txt` (kept). |
| `tmp/proxy_pilots/`, `tmp/report_build/`, `tmp/tx_oh_expansion_text/`, `tmp/final_report_pdf_render_2026-07-10/`, `tmp/build_windows.py`, `tmp/_viewer_script_check.js` | `tmp/` | Scratch outputs from already-archived or already-superseded process docs; no active script or canonical doc references any of them. |
| `inbox/foia/DISCARD_arlington_heights_IL_police_2020_2022.pdf` | `inbox/foia/` | Explicitly labeled `DISCARD_` by a prior session (an Arlington Heights, IL / Arlington, MA jurisdiction mismatch — the same false-positive-city pattern documented elsewhere in this project, e.g. Erie County NY). Confirmed not referenced in `inbox/manifest.csv` or `inbox/processed_manifest.csv` before removal. |
| `inbox/foia/statereference_georgetown/` (empty directory) | `inbox/foia/` | Empty; no content. |
| All `.DS_Store` (11) and `__pycache__/` (3) | repo-wide, excluding `.venv/.git/.claude` | Already gitignored; filesystem clutter only. |

**tmp/ result: 232M → 5.6M.** `.gitignore` updated to add `tmp/` (it was never formally ignored before, only conventionally left untracked) — see §7.

## 5. Reorganization and moves (Task 4)

### The one real breakage found and fixed

`ingest/test_pipeline.py` imported two rule-based relevance-classification functions (`_is_clearly_relevant`, `_is_clearly_irrelevant`) from `analysis/gabriel_pilot/run_gabriel.py` — a legacy v7/v8 GABRIEL pilot script otherwise fully superseded by the current codify pipeline. Rather than leave active test code reaching into an archived directory (or duplicate logic), the two functions plus their five supporting constant lists were **extracted verbatim** (no logic changes) into a new module, `ingest/relevance_filters.py`, with a docstring explaining the provenance. `test_pipeline.py`'s import was updated accordingly. Verified via `python ingest/test_pipeline.py` (60/60 pass) before and after.

### Directory moves (`git mv`, full history preserved)

| From | To | Rationale |
|---|---|---|
| `analysis/` (top-level, 84 tracked files: `gabriel_pilot/` v2-v10 code + outputs) | `docs/archive/legacy_gabriel_pilot_2026-06/` | Entirely superseded by the current codify pipeline (`scripts/gabriel_codify_pilot.py`, Harvard Proxy adapter, 19-attribute codebook). The one still-load-bearing piece was extracted first (see above). |
| `reports/` (top-level: `reports/6_25/` — the GABRIEL v9 preliminary report deliverable, 2 versions) | `docs/archive/legacy_reports_2026-06/` | A real historical deliverable, superseded by the current, more mature `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.{docx,pdf}` (kept in place, untouched). |
| `docs/acquisition/`, `docs/records_requests/`, `docs/session_snapshots/`, `docs/ma_source_inventory.md`, `docs/hypotheses_public_source_strategy_2026-06-24.md` | `docs/archive/acquisition_recon_2026-06/`, `docs/archive/records_requests_2026-06/`, `docs/archive/session_snapshots_2026-06/` | Provenance-heavy 2026-06 research-process records, superseded by the current claim-driven methodology and ledger. Preserved (not deleted) per AGENTS.md's provenance discipline. |
| `data/ma_award_inventory.csv` | `docs/archive/acquisition_recon_2026-06/ma_award_inventory_2026-06.csv` | Not one of `docs/schema.md`'s 4 canonical tables; an early candidate-source list superseded by actual ingested corpus rows. `data/` now holds exactly `contracts.csv`, `city_coverage.csv`, `discourse.csv`, `city_attributes.csv` — the canonical set. |

### `docs/analysis/` file moves (240 → 89 files remaining)

Six new themed archive folders under `docs/archive/`, populated after individual reference checks:

- **`early_occupation_scoping_2026-07/`** (43 files) — the 2026-07-02 through 07-06 per-occupation scoping/gap memos (teacher, DPW, library, sanitation, transit, clerical_admin), the original police/fire wage-mechanism hypothesis/context/synthesis docs, `all_groups_*`, and the superseded `hypothesis_disposition_audit_2026-07-06.csv` (an entirely different, earlier H1-H8 numbering scheme than the current `hypothesis_tracker_2026-07-12.csv`). **`seekonk_public_works_sanitation_language_scan_2026-07-06.*` deliberately excluded** — still actively referenced (§3).
- **`texas_ohio_ingestion_provenance_2026-07/`** (54 files) — the full granular fetch-manifest/source-resolution/recognition-clause-extraction/metadata-addition audit trail for the Texas/Ohio ingestion wave (3 batches), plus the Houston-fire-specific source-identity files. Real provenance, already summarized into `texas_ohio_expansion_ingestion_summary_2026-07-10.md` (also archived here) and the current corpus rows themselves.
- **`final_report_production_2026-07/`** (14 files) — the drafting-process artifacts (outline, draft, production plan, review checklist, scaffold, preflights, graph/evidence-layer audits, appendix tables, export audit) for the report whose actual deliverable already lives untouched in `docs/final_reports/`.
- **`harvard_proxy_early_design_2026-07/`** (3 files) — early Harvard Proxy integration docs, superseded by `gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md` (kept — it's the doc actually cited in `scripts/gabriel_codify_pilot.py`'s docstring).
- **`gabriel_codify_viewer_history_2026-07/`** (3 files) — the viewer's overhaul-plan/capability-review/build-audit design history, superseded by `gabriel_codify_viewer_usage_2026-07-09.md` (kept — the current usage reference).
- **`misc_diagnostics_2026-07/`** (1 file) — `git_remote_diagnosis_2026-07-10.md`, a one-off diagnostic unrelated to any current workflow.
- **`legacy_gabriel_pilot_2026-06/`** also absorbed 32 `docs/analysis/` files from the same v9/v10/websearch/comparator-network era (`gabriel_v9_*`, `gabriel_v10_*`, `gabriel_websearch_*`, `gabriel_builtin_web_*`, `comparator_*`, the prior declutter-planning docs themselves, and 6 of the 8 dated archival HTML viewer snapshots — `_2026-07-14_philadelphia_trenton.html`/`_worcester_arlington.html` stayed, being from this same day).

**Total: 262 files moved via `git mv` (full rename history preserved), 1 file deleted from git tracking (the DISCARD FOIA orphan).**

## 6. Retained despite looking old, with reason

- All 7 codify waves' `*_preflight_*.md`, `*_audit_*.md`, `*_prompt_preview_*.md`, `*_sample_selection_*.md`, `*_evidence_windows_*.csv`, `*_outputs_*.csv` (pilot, texas_ohio_scaleup, massachusetts, expanded_texas_ohio, seekonk_wayland, worcester_arlington, philadelphia_trenton) — every one of the `*_outputs_*.csv` files is an active `--input` to `scripts/build_codify_evidence_viewer.py`; the `*_audit_*.md` files are the methodology/data-integrity audit trail cited by name in the ledger, checklist, and PROGRESS.md (e.g., the Columbus fabrication finding, the Trenton exclusion-clause finding).
- `metadata_cleanup_audit_2026-07-05.md`, `metadata_cleanup_application_2026-07-05.md`, `metadata_cleanup_proposed_edits_2026-07-05.csv`, `metadata_cleanup_applied_edits_2026-07-05.csv` — **actively cited by `docs/schema.md` itself** ("Clarified 2026-07-05 per `metadata_cleanup_audit_2026-07-05.md` MC06").
- `somerville_police_metadata_audit_2026-07-05.md` + edits CSV — documents a metadata correction on `ma_somerville_police_spsoa_2012`, the corpus's single richest source; genuine provenance for a currently-active row.
- `san_antonio_police_bounded_ocr_recovery_2026-07-10.md` / `wayland_bounded_ocr_recovery_2026-07-10.md` + their `.txt` extract siblings — document the OCR-recovery methodology used again this project (Worcester/Arlington wave) and referenced from that wave's own audit doc.
- `recognition_clause_first_classification_standard_2026-07-08.md`, `source_planning_csv_hygiene_standard_2026-07-08.md` — durable standards cited by name in `claim_testing_source_wave_methodology_2026-07-12.md`.
- All `pa_nj_*`, `pennsylvania_source_scan_2026-07-12.md`, `new_jersey_source_scan_2026-07-12.md`, `national_corpus_*`, `national_source_targets_2026-07-12.csv`, `national_state_priority_rubric_2026-07-12.csv`, `claim_consolidation_*`, `claim_centered_corpus_expansion_strategy_2026-07-10.md`, `state_city_claim_map_2026-07-12.csv` + summary, `two_week_claim_driven_expansion_plan_2026-07-12.md`, `next_prompt_national_source_scan_2026-07-12.md` — the direct evidentiary/methodological basis for the current ledger's National Claims and every PA/NJ municipal section; explicitly cited by `claim_testing_source_wave_methodology_2026-07-12.md`.
- `extractor_fix_and_philadelphia_fire_gap_2026-07-13.md`, `philadelphia_nonsafety_rescan_and_nj_extraction_fix_plan_2026-07-13.md` — cited directly in the checklist and ledger for specific, still-relevant data-integrity findings.
- `claim_register_template_2026-07-10.csv`, `claim_viewer_integration_notes_2026-07-12.md` — small, current-format reference docs for extending the claim register going forward.

## 7. `.gitignore` updated

Added `tmp/` (previously conventionally-untracked but not formally ignored). Every relay bundle, codify-pilot raw-output directory, and scratch working file now lives somewhere git will never accidentally pick up — matching this task's target end-state ("tmp/ for ignored/noncanonical working outputs only"). `tmp/gabriel_codify_pilots/` was never git-tracked even before this change (confirmed via `git ls-files tmp/` returning 0 rows), so this is a pure formalization, not a behavior change.

## 8. Files marked uncertain/needs-review

None outright uncertain after the reference check — every candidate resolved cleanly to either "keep" (actively referenced or canonical) or "archive" (real historical value, no active reference). The closest call was `seekonk_public_works_sanitation_language_scan_2026-07-06.*`, resolved to "keep" only because the reference check caught it (§3) — a reminder that this category exists and the check step is not optional in future cleanup passes.

## 9. Validation results (Task 5)

```text
python scripts/validate.py
VALIDATION PASSED — contracts: 64 | discourse: 0 | coverage: 64 | city_attributes: 3

python ingest/test_pipeline.py
60 passed, 0 failed (fixed the run_gabriel.py import break; see §5)

python ingest/audit_coverage.py
healthy matched pairs: 28 | safety units unmatched: 6 | cities: 19 (all unchanged)

python -m py_compile on all 13 active scripts: all OK

Evidence-layer rebuild (all 7 --input waves) re-run and diffed against the
committed docs/analysis/gabriel_codify_evidence_layer.csv: BYTE-IDENTICAL
(1039 rows, 388 present, 368 verified present) — cleanup did not touch any
functional data.

Every data/contracts.csv full_text_path resolves: confirmed, 0 missing.
Every canonical doc/data file (AGENTS.md, PROGRESS.md, docs/schema.md, the
ledger, claim register/tracker/evidence-matrix/readiness/source-needs, the
checklist, the methodology doc, the evidence layer, all 4 data/ tables):
confirmed present.
```

## 10. Remaining clutter intentionally preserved

- `docs/archive/` itself is now ~262 files / several tens of MB — intentionally NOT deleted (this cleanup's whole premise is archive-before-delete for anything with real provenance value). It is expected to grow slowly over time as more waves complete; a future session could apply a similar consolidation pass to it once it accumulates its own clutter.
- The 6 remaining dated archival HTML viewer snapshots that predate today were archived, but the convention of writing a new dated archival copy on every `build_codify_evidence_viewer.py` run continues — a future session may want to decide whether to keep doing this or rely on git history for that record instead (not decided here; flagged as a genuine open question, not resolved unilaterally).
- `tmp/texas_ohio_extracted_text_2026-07-08/` (2.8M) was left in place rather than deleted — small, genuinely non-canonical extraction cache, exactly the kind of thing `tmp/` should hold; no action needed.

## 11. Recommended future repo-retention policy

1. **`docs/analysis/` is for current, actively-referenced analytical artifacts only** — the moment a wave's preflight/design/sample-selection docs are fully superseded by a later wave's summary (or by the ledger absorbing their findings) and nothing else references them, move them to a themed `docs/archive/<theme>_<period>/` folder rather than letting them accumulate indefinitely.
2. **Before archiving or deleting anything, run the same two-step check this session used**: (a) grep the currently-canonical docs and active scripts for the candidate filename, (b) grep the candidate's own content for anything that would make it load-bearing (e.g., a script `import`, a `--input` CLI reference, a `raw_output_ref`/`full_text_path` pointer). Skipping this step is exactly how `ingest/test_pipeline.py`'s `run_gabriel.py` dependency would have silently broken.
3. **`tmp/` is genuinely disposable** — now formally gitignored. Old relay bundles and codify-pilot scratch runs should be pruned at the start of a new cleanup pass without ceremony; the only exception is `tmp/gabriel_codify_pilots/`, which must stay as long as `gabriel_codify_evidence_layer.csv`'s `raw_output_ref` column points into it (if that ever changes — e.g., raw outputs get copied into a durable location instead — this exception can be dropped).
4. **Never edit past `PROGRESS.md`/`chatgpt_handoff_latest.md` entries to "fix" a stale file-path mention** after an archive move — those are historical logs, accurate as of when they were written; a reader encountering a `docs/analysis/<file>` mention that's no longer there should know to check `docs/archive/` first (this document is the pointer).
5. **As the corpus scales nationally**, consider splitting `docs/analysis/`'s remaining ~90 files into subfolders by theme (e.g., `docs/analysis/codify_waves/`, `docs/analysis/claims/`) once the flat directory itself becomes unwieldy again — not done this session (would require updating every `--input`/cross-reference path, higher risk than the archive-only moves made here, and 90 files is not yet unwieldy).
