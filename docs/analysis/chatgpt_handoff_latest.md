# ChatGPT Handoff Log

Reverse-chronological handoff for ChatGPT/Codex planning. Unlike `PROGRESS.md`, this file is more explicit about current interpretation, artifact paths, open decisions, and the recommended next run.

Last updated: `2026-07-13T10:45:00-04:00`

---

## 2026-07-13T10:45:00-04:00 - Claim-testing methodology saved; PA/NJ follow-up digging and state/city claim map completed

**Commit target:** `Save source-wave methodology and PA NJ claim map`

### Current State After This Entry

- The repeatable 13-step source-wave lifecycle is now a durable standard: `claim_testing_source_wave_methodology_2026-07-12.md`. `AGENTS.md` has a new concise section ("Claim-driven expansion and reporting") pointing future agents at it and restating the claim-centered report standard.
- A targeted PA/NJ follow-up scan (public web only, no downloads/ingestion) produced `pa_nj_candidate_sources_followup_2026-07-12.csv` (39 rows). Biggest upgrades: **Trenton NJ** went from zero leads to a confirmed, in-window (2019) non-safety CBA (AFSCME Local 2281); **Allentown PA**'s non-safety union was corrected from an assumed AFSCME to the actual SEIU Local 668; **Jersey City NJ** resolved to a document-level candidate for all three roles (police/fire/non-safety) via direct PERC PDFs, but every document is dated ~2009-2015 and needs a current-cycle successor before it clears the project's 2014-2024 window; **Newark NJ** gained a second non-safety document and an extensive PERC decision history for its police/fire units; **Elizabeth NJ** remains the weakest-evidenced city in either state.
- `pa_nj_state_city_claim_notes_2026-07-12.md` gives each of the 10 scanned PA/NJ cities an explicit source-availability-informed hypothesis and recommended status (`ingest_next`: Philadelphia, Newark; `scan_more`: Pittsburgh, Allentown, Erie, Reading, Jersey City, Trenton; `hold`: Paterson, Elizabeth).
- `state_city_claim_map_2026-07-12.csv` (26 rows) now indexes every state/city in the project — 16 codified MA/TX/OH cities plus the 10 scanned-but-uningested PA/NJ cities — with a build-script-enforced rule that no PA/NJ row can be marked codified or anything other than `source_availability_hypothesis`. `state_city_claim_map_summary_2026-07-12.md` synthesizes this into a recommended 8-source first ingestion batch (Philadelphia triad-in-progress + Reading library CBA + Newark IBT-97 + Trenton AFSCME-2281 + Newark police/fire pending PERC-index lookup).
- PA/NJ-relevant rows in `national_source_targets_2026-07-12.csv` (8), `claim_driven_source_needs_2026-07-12.csv` (5), and `hypothesis_tracker_2026-07-12.csv` (6) were updated with follow-up notes; no other states'/claims'/hypotheses' rows touched. Light pointers added to `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `all_groups_source_needs_2026-07-06.csv`.
- This run did not call GABRIEL/codify, Harvard Proxy, models, or APIs; did not download or ingest any source; did not add rows to `data/contracts.csv` or `data/city_coverage.csv`; did not use FOIA/OPRA/RTKL/PRR; did not prepare a new report draft; did not inspect/configure remotes; did not push.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (unchanged)
safety units unmatched: 5 (unchanged)
```

Custom checks passed: `pa_nj_candidate_sources_followup_2026-07-12.csv` (39 rows) and `state_city_claim_map_2026-07-12.csv` (26 rows) both `csv.writer`-built and parse-back validated (row-width, controlled-vocabulary, claim-ID-resolution, and — for the claim map — a PA/NJ-cannot-be-codified check); `national_source_targets`/`claim_driven_source_needs`/`hypothesis_tracker`/`all_groups_source_needs` all parse cleanly after their targeted updates; `data/contracts.csv`, `data/city_coverage.csv`, `docs/schema.md`, `corpus/`, and `docs/final_reports/` all confirmed unchanged (empty diffs).

### Recommended next run

1. Execute the recommended first ingestion batch (Philadelphia PA + Newark NJ + Trenton NJ + Reading PA library CBA) from `state_city_claim_map_summary_2026-07-12.md`, resolving the remaining `needs_review` items (signed Philadelphia AFSCME CBA; Newark/Trenton police/fire via direct PERC-index browsing) first.
2. Do not ingest Jersey City NJ until current-cycle (2020s) successors to its ~2009-2015 PERC documents are located.
3. After ingestion, follow Steps 7-13 of `claim_testing_source_wave_methodology_2026-07-12.md` (validate → extract → codify → audit → viewer → claim register → next gap) before starting an Illinois/New York scan.

---

## 2026-07-12T10:51:00-04:00 - PA/NJ bounded source-availability scan completed

**Commit target:** `Scan Pennsylvania and New Jersey source availability`

### Current State After This Entry

- Completed a bounded, non-ingestion source-availability scan of Pennsylvania and New Jersey, the two tier-1 states from `national_state_priority_rubric_2026-07-12.csv`, per Week-1 of `two_week_claim_driven_expansion_plan_2026-07-12.md`.
- Scanned 10 cities via public web search only: Philadelphia, Pittsburgh, Allentown, Erie, Reading (PA); Newark, Jersey City, Paterson, Elizabeth, Trenton (NJ). No downloads, no ingestion, no GABRIEL/codify, no data/corpus edits.
- New artifacts:
  - `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md`
  - `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` — 40 candidate rows (21 PA, 19 NJ), `csv.writer`-built and parse-back validated
  - `docs/analysis/pennsylvania_source_scan_2026-07-12.md`
  - `docs/analysis/new_jersey_source_scan_2026-07-12.md`
  - `docs/analysis/pa_nj_source_scan_summary_2026-07-12.md`
- Updated `docs/analysis/national_source_targets_2026-07-12.csv` — only the 10 PA/NJ rows' `target_status`/`notes` changed; Scranton and Camden (in the original planning targets but not in this task's fixed city list) marked `not_scanned_this_pass`, noting Reading and Elizabeth were scanned in their place.
- **Strongest finding: New Jersey's PERC (Public Employment Relations Commission) maintains a centralized, statutorily-mandated public index of nearly all municipal CBAs plus a separate police/fire interest-arbitration-awards database** — a structural search-burden advantage Pennsylvania does not have. At the city level, **Philadelphia** produced the most complete single-city document set of the scan (FOP Lodge 5, IAFF Local 22, two city-hosted Act 111/interest-arbitration awards); **Newark** produced the only directly-retrievable non-safety document found anywhere in this scan (City of Newark and IBT Local 97 CBA, 2020).
- Recommended (not yet executed) first ingestion batch: 8 sources completing a Philadelphia triad and a near-complete Newark triad — see `pa_nj_source_scan_summary_2026-07-12.md` for the exact list and which rows still need confirmation before moving from `needs_review` to `ingest_next`.
- This run did not call GABRIEL/codify, Harvard Proxy, models, or APIs; did not download any source into `corpus/`; did not add rows to `data/contracts.csv` or `data/city_coverage.csv`; did not use FOIA/OPRA/RTKL/PRR; did not inspect/configure remotes; did not push.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (unchanged)
safety units unmatched: 5 (unchanged)
```

Custom checks passed: candidate-sources CSV (40 rows) and updated national-source-targets CSV (29 rows) both parse cleanly with `csv.writer`-based row-width/controlled-vocabulary/required-field checks; `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` unchanged (empty diffs).

### Recommended next run

1. Short, still non-ingestion, follow-up: browse the NJ PERC contracts and interest-arbitration-awards indexes by employer name for Newark, Jersey City, Paterson, Elizabeth, and Trenton; confirm whether a signed Philadelphia AFSCME DC33/DC47 CBA is directly retrievable.
2. Then run a reviewed ingestion pass on the 8-source PA/NJ batch above, followed by `python ingest/audit_coverage.py`.
3. Defer Illinois/New York scanning until after this batch is ingested — both PA and NJ already clear the two-week plan's matched-triad promotion bar pending the confirmations above.

---

## 2026-07-12T10:36:00-04:00 - National claim-driven corpus expansion plan

**Commit target:** `Plan national claim-driven corpus expansion`

### Current State After This Entry

- Created a two-week national source-expansion plan. This is not a report run; the next phase should expand source coverage, test claims, and track hypotheses before any full claim-centered report is drafted.
- New planning artifacts:
  - `docs/analysis/national_corpus_expansion_preflight_2026-07-12.md`
  - `docs/analysis/national_corpus_current_coverage_gap_audit_2026-07-12.md`
  - `docs/analysis/national_state_priority_rubric_2026-07-12.csv` — 20 candidate states
  - `docs/analysis/two_week_claim_driven_expansion_plan_2026-07-12.md`
  - `docs/analysis/national_source_targets_2026-07-12.csv` — 29 initial source targets
  - `docs/analysis/hypothesis_tracker_2026-07-12.csv` — 8 leading hypotheses
  - `docs/analysis/claim_driven_source_needs_2026-07-12.csv` — all 8 current claims mapped to source needs
  - `docs/analysis/next_prompt_national_source_scan_2026-07-12.md`
- Light guidance updates were made to `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `all_groups_source_needs_2026-07-06.csv`: next two weeks prioritize claim-driven national corpus expansion, matched non-safety bottlenecks, and source scans rather than another full report.
- Tier-1 source-scan states: Pennsylvania, New Jersey, Illinois, New York. Each has 5 initial target cities in `national_source_targets_2026-07-12.csv`.
- Tier-2 states: California, Washington, Oregon, Michigan, Minnesota, Wisconsin, Connecticut, Rhode Island, Maryland, Colorado. Tier-3/hold states are retained for later contrast or selective scans.
- This run did not call GABRIEL/codify, Harvard Proxy, models, or APIs; did not search/download/collect sources; did not edit `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final DOCX/PDF artifacts; did not inspect/configure remotes; did not push.

### Current Evidence Baseline

- `data/contracts.csv`: 53 rows.
- `data/city_coverage.csv`: 53 rows.
- `docs/analysis/gabriel_codify_evidence_layer.csv`: 781 rows; 293 present; 488 not_found; 284 verified-present rows.
- Current state coverage remains MA/TX/OH only.
- Known expansion bottlenecks: peer/comparator evidence, factfinding sources, Texas non-safety outside Houston, and national matched non-safety units.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5
```

Custom checks passed: state rubric/source targets/hypothesis tracker/claim-driven source-needs CSVs parse cleanly; controlled values are valid; claim IDs and hypothesis IDs resolve; prohibited data/corpus/schema/final-report paths unchanged.

### Recommended next run

Use `docs/analysis/next_prompt_national_source_scan_2026-07-12.md` to perform source-availability scans for tier-1 states. Do not ingest or codify in that scan unless bounded criteria are explicitly met. Prioritize matched triads and non-safety source availability; record source provenance and candidate URLs; commit locally only.

---

## 2026-07-12T10:10:00-04:00 - Claim-centered evidence register consolidated

**Commit target:** `Consolidate claim-centered evidence register`

### Current State After This Entry

- Created a real claim-centered evidence register from the current durable GABRIEL/codify evidence layer, report assets, source inventory, audits, and report scaffold. The prior `claim_register_template_2026-07-10.csv` remains a template; the analytic register is the new dated file.
- New claim artifacts:
  - `docs/analysis/claim_consolidation_preflight_2026-07-12.md`
  - `docs/analysis/claim_register_2026-07-12.csv` — 8 bounded candidate claims
  - `docs/analysis/claim_evidence_matrix_2026-07-12.csv` — 59 rows
  - `docs/analysis/claim_consolidation_summary_2026-07-12.md`
  - `docs/analysis/claim_readiness_table_2026-07-12.csv` — 8 rows
  - `docs/analysis/claim_viewer_integration_notes_2026-07-12.md`
- Light guidance updates were made to `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `all_groups_source_needs_2026-07-06.csv`: future reports should be claim-centered by default, and future source expansion should be claim-driven.
- Strongest current claims: arbitration distinction (`CLM-2026-07-12-06`), Ohio matched triads (`CLM-2026-07-12-01`), and Texas institutional unevenness (`CLM-2026-07-12-02`).
- Claims needing more evidence: peer/comparator wage evidence (`CLM-2026-07-12-07`) and Texas non-safety outside Houston (`CLM-2026-07-12-08`).
- This run did not call GABRIEL/codify, Harvard Proxy, models, or APIs; did not collect/download sources; did not edit `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final DOCX/PDF artifacts; did not inspect/configure remotes; did not push.

### Evidence Base

- `docs/analysis/gabriel_codify_evidence_layer.csv`: 781 rows; 293 present; 488 not_found; 284 verified-present primary-support-eligible rows; 9 flagged/unverified present rows excluded from primary support.
- `docs/analysis/report_assets/source_inventory_for_report_2026-07-10.csv`: 37 codified contracts across MA/TX/OH.
- Baseline data unchanged: 53 contracts, 53 coverage rows.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
exploratory adjacent matches: 2
safety units unmatched: 5
```

Custom checks passed: claim CSVs parse cleanly; controlled values valid; matrix evidence IDs exist in the evidence layer when nonblank; matrix/readiness claim IDs exist in the register; primary-support rows are verified, grounded, present evidence; prohibited data/corpus/schema/final-report paths unchanged.

### Recommended next run

Review and revise the claim register for PI-facing wording. Then use `claim_consolidation_summary_2026-07-12.md` as the structure for the next claim-centered report revision. If source expansion is authorized later, prioritize claim tests: Texas non-safety gaps, additional matched triads, impasse/arbitration contrast states, repeat cycles, and comparator-specific awards/factfinding.

---

## 2026-07-12T09:22:00-04:00 - Git remote diagnosis (remote NOT configured) + claim-centered project-direction reset

**Commit target:** `Plan claim-centered corpus expansion`

### Current State After This Entry

- **Remote: still not configured, by design.** This repo has never had an `origin` remote. `git remote -v`, `remote.origin.url`, and `git config --list --local` all confirm zero `remote.*` keys; `git branch -vv` shows no upstream. `gh` is not installed. No project-specific remote URL exists anywhere in local config or repo docs (the only `github.com` references found in `PROGRESS.md`/`docs/analysis/*.md` are to the unrelated upstream GABRIEL package repo). None of the three safe-configuration cases in this task's instructions applied, so **no remote was added and no push was attempted.** Full diagnosis + exact commands: `docs/analysis/git_remote_diagnosis_2026-07-10.md`.
- **Project direction**: a new memo, `docs/analysis/claim_centered_corpus_expansion_strategy_2026-07-10.md`, argues the project is ready to move from mechanism-inventory reporting (what the 2026-07-10 final report did) to claim-centered reporting (claim / evidence / reasoning / counterevidence / what-would-change-our-mind / source-needs), and lays out a 5-stage corpus-expansion design plus provisional next-state candidates (Pennsylvania and New Jersey rank highest for institutional contrast).
- **Claim register template** created at `docs/analysis/claim_register_template_2026-07-10.csv` with 4 conservative draft/provisional example rows, built from real obs_ids and evidence_ids already in the corpus (not invented).
- This was a diagnosis/planning session only: no GABRIEL/codify, Harvard Proxy, model, API, or web-search calls; no new source collection; `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, and all `docs/final_reports/` artifacts remain unchanged.

### New Artifacts

- Remote diagnosis: `docs/analysis/git_remote_diagnosis_2026-07-10.md`
- Project-direction memo: `docs/analysis/claim_centered_corpus_expansion_strategy_2026-07-10.md`
- Claim register template: `docs/analysis/claim_register_template_2026-07-10.csv`

### Remote — exact status and what the user needs to do

No `<REMOTE_URL>` was fabricated or guessed, per instructions. To fix the push failure, the user needs to run, with their own actual repo URL:

```
git remote add origin <REMOTE_URL>
git push -u origin main
```

If a remote repo does not yet exist, the user should create one first (GitHub/GitLab web UI, or `gh repo create` after installing/authenticating `gh`), then run the two commands above. See `docs/analysis/git_remote_diagnosis_2026-07-10.md` for full detail.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged
safety units unmatched: 5 -- unchanged (Somerville x2, Newton, San Antonio police, San Antonio fire)
```

`git status --porcelain` shows only the three new `docs/analysis/` files (plus this update to `PROGRESS.md`/this file) as changed; `git diff --stat -- data/contracts.csv data/city_coverage.csv docs/schema.md` is empty; no changes under `corpus/` or `docs/final_reports/`.

### Recommended next run

1. **User action required first**: configure the remote per the diagnosis memo, then push.
2. **Content**: run the claim-consolidation prompt from Section 8 of `claim_centered_corpus_expansion_strategy_2026-07-10.md` — turn the 781-row evidence layer into 5-8 real claim-register rows before any new-state source-availability scan.

---

## 2026-07-10T23:10:00-04:00 - Final integrated report export: Markdown + DOCX + PDF, appendix included at end

**Commit target:** `Export final mechanism evidence report`

### Current State After This Entry

- The reviewed/polished scaffold and appendix have been merged into one final integrated report. The appendix is not a separate final artifact; it starts at the end of the same report under `# Appendix`.
- This was an export/formatting session only: no GABRIEL/codify, Harvard Proxy, model, API, web search, FOIA/PRR, or new source collection. `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, and `logs/api_spend_log.csv` remain unchanged.

### New Artifacts

- Preflight: `docs/analysis/final_report_export_preflight_2026-07-10.md`
- Integrated Markdown: `docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md`
- Export audit: `docs/analysis/final_report_export_audit_2026-07-10.md`
- DOCX: `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.docx` (797,087 bytes)
- PDF: `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf` (1,012,886 bytes; 15 letter-size pages)
- Export helper: `scripts/export_final_report.py`

### Export Method

- `pandoc` and LibreOffice/`soffice` were unavailable.
- DOCX was generated with `python-docx`; PDF was generated with ReportLab.
- PDF QA used Poppler (`pdfinfo`, `pdftoppm`) to render all pages to PNG. No obvious graph/table clipping or page-boundary overflow was observed.
- DOCX visual render QA could not be completed without LibreOffice; structural checks passed (6 embedded images, 5 tables).

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23
  exact-cycle: 9
  overlap-cycle: 14
safety units unmatched: 5
```

Additional checks: final Markdown/DOCX/PDF/audit files exist and are non-empty; 6/6 inline graph references resolve from `docs/analysis/`; DOCX embeds 6 images; `all_groups_source_needs_2026-07-06.csv` parses with consistent 11-column width; `git diff -- data/contracts.csv data/city_coverage.csv` is empty.

### Recommended next run

Human review and revision pass only. Review the title page/title block, Executive Summary, graph readability, state sections, "What appears to drive the wage gap?" framing, appendix start/formatting, page numbering, and PDF rendering. Preserve the evidence-pattern framing; do not rerun codify/model/API or collect new sources unless a separate task explicitly authorizes it.

---

## 2026-07-10T22:49:00-04:00 - Report scaffold polish: graph audit created, appendix typo fixed, prose tightened for PI readability

**Commit:** pending in current session (`Polish mechanism evidence report scaffold`)

### Current State After This Entry

- The report scaffold committed at `74836f7` ("Commit report scaffold: safety/non-safety wage-mechanism evidence patterns") has been reviewed and polished. This was a documentation/prose-editing session only — no GABRIEL/codify, Harvard Proxy, model, or API calls; no new source collection; `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, and `docs/schema.md` all unchanged.
- The evidence layer is unchanged from the prior entry: 781 rows (293 present, 488 not_found, 284 verified present, 9 flagged/unverified). 37 of 53 contracts codified across Massachusetts, Texas, Ohio.

### Work completed this run

1. **Preflight memo**: `docs/analysis/report_polish_preflight_2026-07-10.md` — repo state, files found, known issues, checks to run, explicit no-GABRIEL/no-new-sources confirmation.
2. **Created the missing graph audit** (`docs/analysis/report_graph_audit_2026-07-10.md`), requested by the original report-scaffold run but never produced. Documents: the evidence filter (`evidence_status=present AND viewer_verified=1`); exact evidence-layer counts; a full asset inventory (6 CSVs, 7 PNG/SVG figure pairs); per-figure caveats (Texas institutionally uneven — San Antonio police/fire-only, Austin safety-adjacent via EMS; Ohio strongest matched triads; Massachusetts dense but uneven per-city depth; binary codify cannot measure intensity/causal weight); and a file-reference check confirming all 6 inline image references resolve and all 7 figures have matching PNG+SVG pairs.
3. **Fixed the appendix miscount**: `report_appendix_tables_2026-07-10.md` said "Two rows" while listing four zero-verified-present contract IDs (`oh_cincinnati_fire_2023`, `oh_cincinnati_police_sup_2024`, `ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) — corrected to "Four rows." Rest of appendix reviewed (file names, viewer path, evidence terminology, no causal overstatement, glossary readability) and found already clean.
4. **Polished report scaffold prose** (`report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`): Executive Summary trimmed 8 -> 6 bullets, still leading with "GABRIEL-coded evidence patterns, not causal estimates"; Method restructured to lead with a plain-language explanation of `codify()` and "verified present" before technical detail, with the 19-attribute list moved to a pointer at Appendix A; Massachusetts and Texas state-findings paragraphs tightened while preserving every caveat. Headline Finding, "What Appears to Drive the Wage Gap?", Counterpoints, and Next-State Strategy reviewed against this run's framing requirements and found already compliant from the prior session — left largely as-is.
5. **Verification**: wrote and ran a deterministic Python check (no model calls) confirming all image references resolve, all asset CSVs parse clean, all figure PNG/SVG pairs complete, graph audit documents every asset file, evidence-layer CSV parses clean, `data/contracts.csv`/`data/city_coverage.csv` unchanged since `74836f7`, and the appendix fix is present. **All checks passed.**
6. Light updates to `wage_mechanism_evidence_checklist.md`, `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7S), and `all_groups_source_needs_2026-07-06.csv` (1 new row) recording the polish pass and the final-export next step.

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14) -- unchanged
```

Custom graph-reference check: 6/6 scaffold image references resolve; 6/6 report-asset CSVs parse clean; 7/7 figures have matching PNG+SVG; graph audit documents all 20 asset files; evidence-layer CSV parses clean (781 rows); `data/contracts.csv`/`data/city_coverage.csv` byte-identical to `74836f7`. Overall: **PASS**.

### Confirmed

No GABRIEL/codify, Harvard Proxy, or model/API calls this session (no new `logs/api_spend_log.csv` rows, no new codify output files). No new source collection, no web search, no FOIA/PRR. No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`. No final PDF/DOCX artifact produced — the scaffold remains explicitly labeled "DRAFT SCAFFOLD for human review."

### Recommended next run

**Final report export (DOCX/PDF) after human/PI review.** The scaffold, appendix, and graph audit are now polished and internally consistent; the evidence-pattern (not causal-proof) framing must be preserved through any formatting pass. Secondary, non-blocking: 16 Massachusetts contracts remain uncodified — a future GABRIEL/codify batch could broaden the evidence layer before a later report revision.

---

## 2026-07-10T20:49:00-04:00 - Merge recovery branch + San Antonio OCR + expanded Texas/Ohio codify + viewer rebuild: 9/9 live calls, 100% grounded, 0 contamination

**Commit:** pending in current session (`Codify expanded Texas and Ohio sources`)

### Current State After This Entry

- Merged the recovery branch (`worktree-tx-oh-expansion-recovery`, commit `9c42999`) into `main` via clean fast-forward. The main checkout's working tree held an untouched, byte-identical copy of the pre-interruption uncommitted state (SHA-256-verified against the merge target); stashed as a safety backup before merging, confirmed identical after, left in the stash list (not dropped -- classifier denied the drop as an irreversible-action guard; harmless, fully redundant with the merged commit).
- Recovered San Antonio police's 218-page image-scan source via a bounded single-pass OCR (~4 minutes total), then codified all 9 newly expanded Texas/Ohio sources (San Antonio, Cincinnati, Toledo) in one capped live run. This was a codify/OCR/viewer session -- no new source acquisition, no `data/contracts.csv` row additions (one existing row's `text_quality`/`cycle_start`/`total_comp_note` fields were corrected in place based on the OCR recovery, not a new row).

### Exact commands run

```text
# OCR (San Antonio police)
pdftoppm -r 150 -png corpus/tx_san_antonio/tx_san_antonio_sapoa_police_cba_2022_2026.pdf tmp/san_antonio_ocr/page
tesseract tmp/san_antonio_ocr/page-NNN.png tmp/san_antonio_ocr/page-NNN --psm 6   # x218 pages

# Codify dry run then live
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 9 \
  --windows docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv

python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 9 \
  --windows docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv

# Viewer rebuild (5-file union)
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

Dry-run output: `tmp/gabriel_codify_pilots/2026-07-10_204044/`. Live-run output: `tmp/gabriel_codify_pilots/2026-07-10_204149/` -- `live_run_log.txt` confirms `Calls attempted: 9 | succeeded: 9 | failed: 0`, `present=32 grounded=32 boundary_leak_flagged=0 mechanism_label_leak_flagged=0`.

### Code changes this session

- `scripts/gabriel_codify_pilot.py`: `HARD_MAX_CALLS` raised `8 -> 9` (deliberate code edit, in-code comment explains why, per this script's own established per-batch-cap-adjustment pattern).
- `data/contracts.csv`: single-row edit to `tx_san_antonio_police_2022` (`text_quality` partial -> ocr_messy; `cycle_start` corrected 2022-10-01 -> 2022-05-12, document-confirmed via title page and Article 1 Duration; `total_comp_note` updated). Applied via a surgical single-line byte splice (not a full `csv.writer` rewrite) after an initial rewrite attempt was caught normalizing 12 unrelated rows' legacy `\r\n` line endings.
- `docs/analysis/texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv`: fixed a pre-existing row-width bug (unquoted comma in a `notes` field, left over from the prior recovery session) and appended 7 new San Antonio police excerpts.

### San Antonio police bounded OCR (Task C)

Target: `corpus/tx_san_antonio/tx_san_antonio_sapoa_police_cba_2022_2026.pdf` -- 218-page image scan (Xerox WorkCentre 7855, 270° rotation), `pdftotext` yielding 218 characters total (essentially 0) at session start. Method: `pdftoppm -r 150 -png` (all 218 pages, 74s) -> `tesseract --psm 6` (all 218 pages, ~2.5 min) -- a full-document pass chosen over page-targeting because there was no way to locate a table of contents without OCR'ing a reconnaissance batch first, and page 1's immediately clean output gave high confidence in the rest. **Total: ~4 minutes, single bounded pass.** Recovery quality: ~2,217 chars/page average, full legible article structure (Recognition, No Strike, Management Rights, Grievance/Arbitration, Wages/Step Schedule, Impasse Procedure), plus a genuine Attachment 3 factfinding peer/comparator wage-comparability clause -- the first confirmed comparator-wage language found for San Antonio in this project's corpus. Full writeup: `san_antonio_police_bounded_ocr_recovery_2026-07-10.md`. Curated, marker-sliced excerpt cache (9 sections, verbatim-verified): `san_antonio_police_bounded_ocr_extract_2026-07-10.txt`. Raw OCR cache (483,412 chars, not committed): `tmp/san_antonio_ocr/full_cache.txt`.

### Evidence windows (Task E)

`docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv` -- 9 rows, all marker-sliced (`.index()`-based or line-range) verbatim substrings of `pdftotext -layout` extractions (8 rows) or the San Antonio OCR cache (1 row), 203-835 words each (well under the 1500-word cap), neutral `--- Excerpt N [Article X] ---` separators throughout. `_check_window_contamination()` found 0 violations across all 9 windows.

### Live run results (Task G/H)

**9/9 calls succeeded.** 178 output rows (32 present, 146 not_found), 0 parse failures. **32/32 present excerpts grounded (100%)** -- 0 boundary-leakage flags, 0 mechanism-label-contamination flags. Cleanest single-batch Texas/Ohio result to date (compare: the original scale-up run had 1 flagged row of 95 present).

San Antonio police correctly distinguished `interest_arbitration_or_formal_impasse_backstop` (the Chapter 174 ordinance-defined impasse procedure) from `grievance_or_contract_interpretation_arbitration` (the separate Article 15 mechanism) within the same document -- the strongest single test yet of this codebook's key distinction. Toledo police also correctly coded a narrow-issue health-benefits interest-arbitration clause under the same attribute, distinct from its (absent from this window) grievance procedure.

**One observed false negative, documented not corrected:** `peer_comparator_wage_comparability` was `not_found` for San Antonio police despite the window containing genuine, on-point comparability language (Attachment 3's factfinding guidelines explicitly compare San Antonio police/fire wages to "comparable cities in the State of Texas"). Per this project's rule against RA discretion contaminating GABRIEL's own coding, this was **not** manually added to the codify output -- flagged in `gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md` for a future re-run or codebook refinement instead. The same clause is separately captured as a deterministic (non-model) fact in the mechanism-excerpt CSV, independent of codify's judgment.

Full detail: `gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md`.

### Evidence Layer (union rebuild, now 5 files)

`docs/analysis/gabriel_codify_evidence_layer.csv` -- now **781 rows** (293 present: 284 verified + 9 pre-existing flagged, none new this run; 488 not_found; 0 duplicate `evidence_id`s). All 781 rows resolved a `contract_label`. San Antonio, Cincinnati, and Toledo appear in the viewer for the first time.

### Viewer Paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html`.
- **New dated archival copy:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_expanded_texas_ohio.html` (byte-identical to latest).
- **Untouched:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html`, `..._2026-07-10_seekonk_wayland.html` -- confirmed via `git status` not modified this run.

### Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` -- passed.
- `json.loads()` on both embedded `EVIDENCE` (781 rows) and `ATTRIBUTES` (19 entries) JSON blocks -- both parsed cleanly; confirmed San Antonio/Cincinnati/Toledo present in the parsed city list.
- `python scripts/validate.py` -- PASSED (53 contracts / 53 coverage / 3 city_attributes, unchanged from the prior recovery session).
- `python ingest/audit_coverage.py` -- 23 healthy matched pairs, unchanged.
- `python ingest/test_pipeline.py` -- 40 passed, 0 failed.
- Custom CSV audit: 0 width mismatches, 0 duplicate IDs, 0 invalid controlled-vocabulary values across `data/contracts.csv`, the new codify output CSV, and the evidence layer; 0 duplicate `evidence_id`s across all 781 rows.
- No live browser rendering/screenshot was performed (same standing limitation -- no browser-automation tool available).

### Recommended next run

**Report scaffolding with GABRIEL-coded mechanism-evidence graphs.** The evidence layer's Texas/Ohio coverage is now materially broader than at any prior point (4 Ohio matched cities: Columbus, Cleveland, Cincinnati, Toledo; 3 Texas cities with contracts: Houston, Austin, San Antonio). Report language should present coded findings as evidence patterns (what was found present/not-found, and how consistently), not as proof of a causal wage effect. A future session could also re-run San Antonio police through a refined codebook or manually flag the observed peer-comparator-wage-comparability miss for reviewer attention.

---

## 2026-07-10T19:20:00-04:00 - Texas/Ohio source-expansion interrupted-run recovery: Task G confirmed already-clean, mechanism excerpts + ingestion summary completed, guidance docs updated, full validation passed

**Commit:** pending in current session (`Expand Texas and Ohio sources`)

### Current State After This Entry

- The prior Texas/Ohio source-expansion session's terminal was accidentally closed mid-run, likely around Task G (writing new rows to `data/contracts.csv`/`data/city_coverage.csv`). This entry is written by the recovery/completion run, which treated the working tree's actual file state as ground truth rather than re-running the original prompt from the top.
- **Task G was already complete and clean before the interruption.** `data/contracts.csv` and `data/city_coverage.csv` each already had all 9 new rows appended (44 -> 53), 1:1 matched, no duplicates, no malformed rows. Nine source PDFs were already downloaded to `corpus/tx_san_antonio/`, `corpus/oh_cincinnati/`, `corpus/oh_toledo/`. Four `docs/analysis/texas_ohio_expansion_*` planning/selection/text-quality files (Tasks A-D, F) were already complete on disk. The interruption occurred after Task G but before Task H (mechanism-excerpt extraction), which had not been started — no partial/corrupted state was found anywhere.
- This run completed the remaining deterministic work only: mechanism-excerpt extraction, an ingestion summary, light guidance-doc updates, and a full validation/audit pass. No sources were re-downloaded, re-searched, or broadened beyond the already-selected 9.

### Recovery audit performed

1. `git status` — modified: `data/contracts.csv`, `data/city_coverage.csv`; untracked: 3 new `corpus/` city directories (9 PDFs), 4 `docs/analysis/texas_ohio_expansion_*` files, plus the pre-existing scratch `tmp/`.
2. Diffed both CSVs against HEAD — confirmed exactly 9 new rows in each, matched 1:1 by `obs_id`, no orphans in either direction.
3. Read all four existing `texas_ohio_expansion_*` docs (preflight, source plan 22 candidates, selection 9 sources, text quality 10 rows) — all internally consistent with the 9 rows actually in `contracts.csv`.
4. Custom Python audit: row widths (0 mismatches), duplicate `obs_id` (0), controlled-vocabulary conformance for `occupation_class`/`source_type`/`source_corpus`/`retrieval_method`/`text_quality` (0 violations), `safety_flag` derivation consistency (0 violations), `full_text_path` existence for all 53 rows (0 missing), and zero `retrieval_method=foia` rows anywhere in the file.
5. **Conclusion: Task G had already completed cleanly.** No repair work was needed — only the still-missing downstream tasks (mechanism excerpts, ingestion summary, guidance updates) were completed.

### Work completed this run

- `docs/analysis/texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` — 8 excerpt rows across 6 of the 9 new contracts (recognition clauses for Cincinnati police non-supervisors/CODE, Toledo police/fire/AFSCME 2058; grievance-arbitration text for San Antonio fire and Cincinnati police non-supervisors; one narrow-issue health-insurance-reopener arbitration clause for Toledo AFSCME 2058), built entirely from verbatim clause text already captured in `contracts.csv`/`texas_ohio_expansion_text_quality_2026-07-10.csv` during the pre-interruption session. No new PDF reading, no GABRIEL/codify, no model calls. 3 of 9 contracts contributed zero excerpts (San Antonio police — no extractable text layer; Cincinnati police-supervisors and fire — recognition confirmed present but not separately quoted verbatim) — documented as a gap, not fabricated.
- `docs/analysis/texas_ohio_expansion_ingestion_summary_2026-07-10.md` — full summary: sources searched/selected/rejected, new contract_ids, new matched cities, text-quality summary, deterministic mechanism families observed, next codify batch sizing, limitations.
- Lightly updated `wage_mechanism_evidence_checklist.md` (revised the Texas/Ohio track pointer sentence to reflect it now has contributed corpus rows, not just planning), `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7Q), and `all_groups_source_needs_2026-07-06.csv` (1 new cross-cutting row).

### Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 53 | discourse: 0 | coverage: 53 | city_attributes: 3

python ingest/audit_coverage.py
healthy matched pairs: 23 (exact-cycle: 9, overlap-cycle: 14)
safety units unmatched: 5 (Somerville x2, Newton, San Antonio police, San Antonio fire)

python ingest/test_pipeline.py
40 passed, 0 failed
```

### New sources / cities / contract_ids

- **San Antonio, TX** (unmatched, retained for institutional-contrast value only — no confirmed non-safety bargaining channel found): `tx_san_antonio_police_2022` (partial text quality, image-scan PDF, cycle/union identity from portal metadata), `tx_san_antonio_fire_2024` (clean).
- **Cincinnati, OH** (new healthy matched triad, overlap-cycle): `oh_cincinnati_police_2024`, `oh_cincinnati_police_sup_2024` (rank-split bonus row), `oh_cincinnati_fire_2023`, `oh_cincinnati_other_2025` (CODE, recognition-clause-first `other`).
- **Toledo, OH** (new healthy matched triad, overlap-cycle): `oh_toledo_police_2024`, `oh_toledo_fire_2024`, `oh_toledo_other_2024` (AFSCME Local 2058, recognition-clause-first `other`).
- Ohio now has 4 healthy matched cities (Columbus, Cleveland, Cincinnati, Toledo). Texas remains at 1 fully matched city (Houston) plus Austin (EMS, safety-adjacent) and San Antonio (deliberately unmatched).

### Isolation note

All edits in this recovery run were made inside a git worktree (`worktree-tx-oh-expansion-recovery`) per this session's background-job isolation policy. Because a fresh worktree only carries committed history (not working-directory changes), the pre-interruption uncommitted diff (`data/contracts.csv`, `data/city_coverage.csv`) and untracked files (`corpus/tx_san_antonio/`, `corpus/oh_cincinnati/`, `corpus/oh_toledo/`, the four existing `texas_ohio_expansion_*` docs) were copied into the worktree before any further edits, so the recovery builds on the actual pre-interruption state rather than reverting to the last commit.

### Confirmed

No GABRIEL/codify calls, no Harvard Proxy calls, no model/API calls of any kind, and no FOIA/PRR retrieval — in this recovery run or in the recovered prior run (verified: all 53 `contracts.csv` rows use `retrieval_method=public_download`).

### Recommended next run

Codify the 9 newly expanded Texas/Ohio sources (San Antonio, Cincinnati, Toledo) via `scripts/gabriel_codify_pilot.py` and rebuild the evidence layer/viewer via `scripts/build_codify_evidence_viewer.py`'s append/union mode, then resume report scaffolding once the evidence layer reflects the expanded coverage.

---

## 2026-07-10T11:54:00-04:00 - GABRIEL codify excerpt-boundary repair (pipeline-level) + Seekonk/Wayland expansion: 6 capped live calls, bounded Wayland OCR recovery

**Commit:** pending in current session (`Add Seekonk and Wayland to codify viewer`)

### Current State After This Entry

- Confirmed the prior Massachusetts scale-up session's changes (`4f10a4f`, "Add Massachusetts to codify viewer") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage / 479 evidence-layer rows) matched expectations.
- Fixed the Massachusetts run's excerpt-boundary-leakage defect at the pipeline level (not a one-off script) and expanded the evidence layer to include Seekonk (new city) and Wayland's dispatch/nurse content (recovered via bounded OCR, previously unusable). Massachusetts was again the only state touched — no other state, no full-corpus run.

### Exact commands run

```text
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv

python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv

python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_seekonk_wayland.html
```

Dry-run output: `tmp/gabriel_codify_pilots/2026-07-10_114636/`. Live-run output: `tmp/gabriel_codify_pilots/2026-07-10_114713/` — `live_run_log.txt` confirms `Calls attempted: 6 | succeeded: 6 | failed: 0`; no `errors.jsonl`. Only 6 of the 8 available calls used.

### Code changes this session

- `scripts/gabriel_codify_pilot.py`: `HARD_MAX_CALLS` lowered `10 -> 8`. Added `import ast`, `import re`. New functions: `_find_boundary_leak()`, `_clean_boundary_leak()`, `_has_mechanism_label_leakage()`, `_normalize_ws()`, `_find_excerpt_location()`, `_grounding_status()`, `reshape_and_validate_outputs()`, `_write_validated_outputs()`. `_run_live()` now calls `reshape_and_validate_outputs()` automatically after every live run, writing `validated_outputs.csv` directly into the run's `tmp/gabriel_codify_pilots/<timestamp>/` directory — **this is now the direct source for `docs/analysis/*_outputs_*.csv`, no separate one-off downstream parsing script needed** (a deliberate architectural change from every prior session, where this logic lived in scratch scripts).
- `scripts/build_codify_evidence_viewer.py`: **no changes this session** — Task C's requirements (default-verified-only view, unverified-evidence toggle, warning banner, correct labels) were already fully implemented in the prior (Massachusetts) session and re-verified as correct against this run's new data without modification.

### Boundary-leakage cleanup design (read before extending further)

`_clean_boundary_leak(excerpt)` is a two-stage process:
1. **Stage 1 (multi-boundary):** split the raw excerpt on every COMPLETE `--- Excerpt N [location] ---` instance (`LEAK_FULL_SEPARATOR_RE`, using `re.split()` with a **non-capturing** group — a capturing group here causes `re.split()` to intersperse `None`/captured-group values into the result list, a real bug caught during testing) and keep the single longest resulting segment.
2. **Stage 2 (single-boundary trim):** re-run the original partial-fragment detection (`LEAK_OPENER_RE`/`LEAK_CLOSER_RE`/`LEAK_BARE_DASH_RE`) on the Stage-1 result, in case its own edges still carry a partial separator fragment left over from the raw excerpt's boundary.

Both stages together guarantee: the cleaned excerpt is ALWAYS a genuine, untouched, single contiguous substring of what the model actually returned — never fabricated, never spliced from two different source locations. `source_grounding_status` is downgraded to `unclear` (or `unsupported` if nothing usable survives) whenever ANY leakage is detected, regardless of whether cleanup succeeded, and a `METHODOLOGY FLAG`-prefixed note explains exactly what was found (including how many window-sections the raw excerpt spanned and the full raw excerpt for audit purposes).

**This design was validated against a real multi-boundary case found live this session** (`ma_seekonk_teacher_2021` / `no_strike_or_work_stoppage_constraint` — the raw excerpt spanned 6 separator instances). The original single-split-only logic (deployed for the live run) left embedded separator fragments in its "cleaned" output; the two-stage fix was applied and `validated_outputs.csv` was regenerated by **locally reprocessing `tmp/gabriel_codify_pilots/2026-07-10_114713/parsed_outputs.csv`** (the wide-format raw result, already on disk from the completed live run) through the corrected function — zero new `gabriel.codify()` calls. `tmp/.../live_run_log.txt` has a "POST-RUN REPROCESSING NOTE" appended documenting this for audit-trail completeness.

### Bounded Wayland OCR recovery (Task E)

Target: `corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf` (`ma_wayland_other_2021`), a pure image-scan PDF (48 pages, 270° rotation, no text layer — `pdftotext` extracts ~48-52 bytes regardless of flags). Method: `pdftoppm -r 150 -png` (all 48 pages, ~16s) → `tesseract --psm 6` (all 48 pages, ~35s) → grep-search the 48 resulting `.txt` files for `dispatch|nurse|JCC|...` and wage-grade markers to identify the ~9 relevant pages, then read those directly. Total: **~51 seconds, single pass, no re-runs.** Result quality was substantially better than expected: clean, coherent text including a full FY2022/FY2023 wage-grade table (`G-3 JCC Dispatcher`, `G-4 JCC Dispatcher Coordinator`, `G-7A Public Health Nurse`, `G-15 Community Health Nurse`, with dollar-figure step tables) and multiple genuinely dispatcher/nurse-specific clauses. A 9-page, 21,433-character cache was saved to `docs/analysis/wayland_other_bounded_ocr_extract_2026-07-10.txt` (original PDF never modified). Full writeup: `wayland_bounded_ocr_recovery_2026-07-10.md`.

**Window-construction bug found and fixed while building the Wayland window:** the OCR cache file's own `--- OCR page N ---` page-boundary labels (added when caching the extract) leaked into two hand-selected excerpts, because a genuine source sentence spanned a page break in the original document and the marker-slice extraction captured everything between its start/end markers, including the intervening cache label. Fixed by stripping `--- OCR page N ---` labels from the cache text before slicing (`re.sub(r"\n*--- OCR page \d+ ---\n*", "\n", ...)`), which correctly restores the natural, continuous source sentence. A separate transcription bug (a hand-typed excerpt included a fabricated ellipsis not present in the source) was caught by a verbatim-substring assertion and fixed by switching to exact `.index()`-based marker-slicing for all 8 Wayland excerpts.

### Seekonk/Wayland sample selection (Task D)

6 rows (of 8 available): `ma_seekonk_public_works_2023`, `ma_seekonk_library_2023`, `ma_seekonk_police_2022`, `ma_seekonk_fire_2022`, `ma_seekonk_teacher_2021` (all clean plain-text extraction — Seekonk is now a fully matched city, 5 occupation classes), `ma_wayland_other_2021` (OCR-recovered). **Not selected:** `ma_seekonk_clerical_admin_2021` (scan, OCR out of this session's authorized scope — only Wayland's dispatch/nurse target was authorized for OCR), all other Wayland occupation classes except `other` (all scans, ~0 usable text, not authorized for OCR this session), `ma_wayland_fire_jlmc_2020` (already codified in the Massachusetts batch).

### Source-grounding audit finding

39/43 present excerpts pass the grounding check outright. 4/43 (9.3%) triggered the new boundary-leakage detection and were downgraded to `unclear` with a full explanatory note (not fabrication — genuine source text on the kept side in every case). 0 mechanism-label contamination (the input-side and output-side checks both report zero hits). Full detail, including the multi-boundary discovery and fix, in `gabriel_codify_seekonk_wayland_audit_2026-07-10.md`.

### Evidence Layer (union rebuild, now 4 files)

`docs/analysis/gabriel_codify_evidence_layer.csv` — now **603 rows** (261 present: 252 verified + 9 flagged; 342 not_found; 0 duplicate `evidence_id`s). All 603 rows resolved a `contract_label`. Seekonk appears in the viewer's Massachusetts city list for the first time; Wayland gained an `other` occupation class alongside its existing `fire` (JLMC award) row.

### Viewer Paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (1,096,717 bytes).
- **New dated archival copy:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-10_seekonk_wayland.html` (byte-identical to latest).
- **Untouched:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, `..._2026-07-09_scaleup.html`, `..._2026-07-09_massachusetts.html` — confirmed via `git status` not modified this run.

### Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` — passed.
- `json.loads()` on both embedded `EVIDENCE` (603 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- Rebuild re-run a second time with identical arguments produced byte-identical `gabriel_codify_evidence_layer.csv` and `_latest.html` (checksummed) — confirms idempotency.
- All 9 flagged rows (1 Texas/Ohio + 4 Massachusetts + 4 Seekonk/Wayland) confirmed `notes_flag: "1"` and `viewer_verified: "0"` in the rebuilt evidence data.
- `python scripts/validate.py` — PASSED (44 contracts / 44 coverage / 3 city_attributes, unchanged).
- `python ingest/audit_coverage.py` — 18 healthy matched pairs, unchanged.
- No live browser rendering/screenshot was performed (same standing limitation — no browser-automation tool available).

### Recommended next run

Per this run's own task instructions: plan a Texas/Ohio source-expansion batch (Texas/Ohio currently has fewer matched cities/occupation classes than Massachusetts), then begin report scaffolding once evidence-layer coverage is judged sufficient for a first PI-facing draft.

---

## 2026-07-10T10:35:00-04:00 - GABRIEL codify neutral-header repair + Massachusetts scale-up: 10 capped live calls, viewer-level verified-evidence gating

**Commit:** pending in current session (`Add Massachusetts to codify viewer`)

### Current State After This Entry

- Confirmed the prior scale-up session's changes (`cd9c70f`, "Scale codify across Texas and Ohio") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage / 265 evidence-layer rows) matched expectations.
- Fixed the Texas/Ohio scale-up's window-header-leakage defect, then ran a curated 10-row Massachusetts codify batch and unioned it into the evidence layer. Massachusetts was explicitly the only new state added — no full-corpus run, no other state.

### Exact commands run

```text
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 10 \
  --windows docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv

python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 10 \
  --windows docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv

python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html
```

Dry-run output: `tmp/gabriel_codify_pilots/2026-07-10_102543/`. Live-run output: `tmp/gabriel_codify_pilots/2026-07-10_102644/` — `run_config.json` confirms `max_calls_allowed: 10`, `use_harvard_proxy: true`; `live_run_log.txt` confirms `Calls attempted: 10 | succeeded: 10 | failed: 0`; no `errors.jsonl`.

### Code changes this session

- `scripts/gabriel_codify_pilot.py`: `HARD_MAX_CALLS` raised `8 -> 10`. Added `_check_window_contamination()` / `_contamination_patterns()` / `_is_notes_flagged`-equivalent read-time guardrail: before any dry-run or live call, every row's `window_text` is scanned against `list(CATEGORIES.keys())` (minus `"other"`, deliberately excluded — see below) plus `["Mechanism", "Arbitration / impasse"]`; any hit is `sys.exit(1)`, not a warning. Called from `_read_windows()`.
- `scripts/build_codify_evidence_viewer.py`: `EVIDENCE_FIELDNAMES` gained `notes_flag`, `viewer_verified`. New constants `METHODOLOGY_FLAG_MARKER = "METHODOLOGY FLAG"`, `_is_notes_flagged(notes)`, `_viewer_verified(evidence_status, grounding, notes)` — a row is "verified" only if `present` AND `grounded` AND not flagged. `write_evidence_csv()` now re-validates `viewer_verified` matches a fresh recomputation on every write (raises if not). `build_html_doc()`'s `verified_present`/new `unverified_present` counts now use `viewer_verified` instead of raw `source_grounding_status`. JS: new `#f-showunverified` checkbox wired into `currentSelections()`/`applyFilters()` (present rows with `viewer_verified !== "1"` are hidden unless the toggle is checked); `renderCards()`/`renderTable()` show a `card-unverified`/`row-unverified` style, an on-card warning block, and override the badge text to "Not verified in source text" for such rows.

### Bug found and fixed mid-session: `"other"` false-positive in the contamination check

First version of the contamination check used all 19 raw `CATEGORIES` keys as substrings, including the bare word `"other"` (one of the 19 attributes). Since `"other"` is also an ordinary English word, the very first dry-run against the clean Massachusetts windows failed, flagging `"other"` inside phrases like "another Municipality," "other conditions of employment." Fixed by excluding `"other"` specifically (documented inline in code) — the other 18 keys are all multi-word/underscore-joined and would never occur in genuine prose by coincidence, so this exclusion doesn't meaningfully weaken the check. Re-verified clean-pass and contaminated-fail behavior after the fix.

### Massachusetts evidence-windows assembly (Task E) — built from scratch, not reused

Unlike Texas/Ohio (which reused an existing hand-extraction CSV), no Massachusetts deterministic-extraction CSV existed. Windows were built this session directly from the underlying corpus PDFs via `pdftotext -layout` (all 10 target PDFs; no ingestion), then a keyword-search helper script (`SEARCH_PATTERNS`, one-off, not committed) located up to 9 short passages per contract around mechanism-relevant terms (arbitration, staffing, overtime, classification, training, hazard, premium, benefits, subcontracting, management rights, no-strike, civil service, union security, budget, peer-comparator). Separators are strictly `--- Excerpt N [location] ---`, with `location` pulled via regex for a genuine `Article`/`Section` marker preceding the excerpt in the source text — never a mechanism name. A `check_contamination()` function in the same builder script hard-fails on any of the 19 codebook keys (again excluding `"other"`) or `"Mechanism"`/`"Arbitration / impasse"` before writing the CSV, and again on round-trip parse — 0 hits across all 10 windows.

### Massachusetts sample selection (Task D)

10 rows: `ma_somerville_police_spsoa_2012` (JLMC interest-arbitration award, unmatched but explicitly requested), `ma_wayland_fire_jlmc_2020` (JLMC stipulated award, unmatched), `ma_franklin_police_2022`/`fire_2022`/`public_works_2022`/`library_2022`/`other_2022` (fully matched city, 5 occupation classes), `ma_boston_clerical_admin_2023` (unmatched, rich grievance-arbitration text), `ma_georgetown_other_2020`/`police_2020` (matched city, 2 occupation classes). **Known gap, documented not silently dropped:** Massachusetts dispatch/nurse_health content exists only in `ma_wayland_other_2021`, whose `pdftotext` extraction yields ~0 usable characters (48-page, 270°-rotated scan needing a bounded OCR pass not attempted this session).

### Source-grounding audit finding (important — read before trusting 4 specific Massachusetts rows)

70/70 present excerpts pass the automated substring-grounding check; **the Texas/Ohio full-fabrication failure mode did not recur (0 fully-fabricated excerpts).** However, a new recurrence check (scanning every *returned excerpt*, not just the input window, for this project's scaffolding vocabulary) caught a **milder** variant in 4/70 present rows: `ma_franklin_fire_2022`/`training_certification_credential_premiums`, `ma_franklin_public_works_2022`/`premium_pay_differentials`, `ma_franklin_library_2022`/`benefits_total_compensation_or_pension`, `ma_boston_clerical_admin_2023`/`premium_pay_differentials`. In each case the model's verbatim-copied span crossed the boundary between two adjacent excerpt blocks in `window_text` and picked up a few characters of the `--- Excerpt N [location] ---` separator syntax mid-span — genuine source content surrounds the leaked fragment on both sides in every case (unlike Cleveland Fire, where the *entire* excerpt was the header). **Root cause: adjacent excerpts are separated only by `\n\n--- Excerpt N [location] ---\n` with no larger buffer**, so when two nearby regions of the same document (found by independent keyword searches) abut, the model perceives one continuous passage. **Fix for next batch:** larger break between adjacent excerpts, or trim each excerpt to a clean sentence/clause boundary. All 4 rows carry a `METHODOLOGY FLAG` note and are correctly excluded from `viewer_verified` (confirmed programmatically).

### Evidence Layer (union rebuild, now 3 files)

`docs/analysis/gabriel_codify_evidence_layer.csv` — now **479 rows** (218 present: 213 verified + 5 flagged/unverified; 261 not_found; 0 duplicate `evidence_id`s). All 479 rows resolved a `contract_label` from `data/contracts.csv`. Massachusetts now appears in the parsed `EVIDENCE` data's `state` values (`['MA', 'OH', 'TX']`), across 5 cities.

### Viewer Paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (877,790 bytes).
- **New dated archival copy:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_massachusetts.html` (byte-identical to latest).
- **Untouched:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` and `..._2026-07-09_scaleup.html` — confirmed via `git status` not modified this run.

### Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` — passed.
- `json.loads()` on both embedded `EVIDENCE` (479 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- Rebuild re-run a second time with identical arguments produced byte-identical `gabriel_codify_evidence_layer.csv` and `_latest.html` (checksummed) — confirms idempotency.
- Programmatically confirmed all 5 flagged rows (1 Texas/Ohio + 4 Massachusetts) have `notes_flag: "1"` and `viewer_verified: "0"` in the rebuilt evidence data.
- `python scripts/validate.py` — PASSED (44 contracts / 44 coverage / 3 city_attributes, unchanged).
- `python ingest/audit_coverage.py` — 18 healthy matched pairs, unchanged.
- No live browser rendering/screenshot was performed (same limitation as every prior session — no browser-automation tool available).

### Recommended next run

1. Fix the excerpt-boundary-leakage recurrence (larger break between adjacent window excerpts, or trim to clean sentence boundaries) before the next codify batch.
2. Manual PI-facing viewer QA in a real browser — exercise the new "Show unverified / unsupported evidence" toggle and the Massachusetts filters.
3. A further acquisition batch (Seekonk is a strong, fully-matched Massachusetts candidate not used this run) or a new state.

---

## 2026-07-09T21:07:00-04:00 - GABRIEL codify Texas/Ohio scale-up: 8 capped live calls, append/union evidence layer rebuild

**Commit:** pending in current session (`Scale codify across Texas and Ohio`)

### Current State After This Entry

- Confirmed the prior viewer-overhaul session's changes (`632a4a5`, "Overhaul codify excerpt viewer") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage / 92 evidence-layer rows) matched expectations.
- Scaled `gabriel.codify()` from the 4-row pilot to the 8 remaining Texas/Ohio matched-city rows: `tx_houston_police_2024`, `tx_austin_police_2024`, `tx_austin_fire_2023`, `oh_columbus_police_2023`, `oh_columbus_other_2024`, `oh_cleveland_police_2025`, `oh_cleveland_fire_2025`, `oh_cleveland_other_2022`. Massachusetts was explicitly NOT run.

### Exact commands run

```text
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv

python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv

python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-latest-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html
```

Dry-run output: `tmp/gabriel_codify_pilots/2026-07-09_205718/`. Live-run output: `tmp/gabriel_codify_pilots/2026-07-09_205815/` — `run_config.json` confirms `max_calls_allowed: 8`, `use_harvard_proxy: true`; `live_run_log.txt` confirms `Calls attempted: 8 | succeeded: 8 | failed: 0`; no `errors.jsonl` written.

### Code changes this session

- `scripts/gabriel_codify_pilot.py`: `HARD_MAX_CALLS` raised `4 -> 8` (deliberate, documented, in-code — not a CLI-only change).
- `scripts/build_codify_evidence_viewer.py`: `_parse_args()` changed `--input` from a single `type=Path` argument to `action="append"` with post-parse comma-splitting (repeatable and/or comma-separated, defaults to the original single pilot CSV if omitted — default no-arg invocation unchanged). Added `--archive-html` as a synonym for `--html-out` (same `dest`). `build_evidence_rows()` signature changed from `(input_rows: list[dict], ...)` to `(input_rows_with_origin: list[tuple[dict, str]], ...)` — each row now carries its own origin `--input` file path (written per-row into `source_output_file`, replacing the old single-`rel_input`-for-all-rows approach in `write_evidence_csv()`). Dedup logic added: `seen_row_signatures: set[tuple]` keyed on `tuple(sorted(row.items()))` (full raw-row content) — **not** `(contract_id, attribute, run_id)`, which was tried first and found (via smoke test) to incorrectly collapse legitimate multi-excerpt codify results (e.g. `tx_houston_fire_2024` / `grievance_or_contract_interpretation_arbitration` genuinely has 2 distinct excerpts in one run).

### Evidence-windows assembly (Task C)

`docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv` (8 rows) was built by a one-off Python script (not committed) that reads `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv` and `texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`, selects each contract's `present`/`unclear` mechanism rows in a fixed order (arbitration first, to surface interest-vs-grievance distinctions), and joins them with `--- {label} [{location}] ---` section headers into one `window_text` per contract. All under the 1,500-word `max_words_per_call` cap (396–766 words each).

### Output parsing (Task F)

`gabriel.codify()`'s native output is wide-format: one row per input row, one column per attribute, each cell a Python-list-repr of extracted verbatim strings (empty list = `not_found`). A one-off parsing script (`ast.literal_eval` per cell) reshaped this into the project's long/tidy schema: `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv`, 173 rows (95 present, 78 not_found). `excerpt_location` is derived heuristically (regex search for `Article \d+`/`Section \d+` markers in the ~200 chars preceding the excerpt's match position in `window_text`). `confidence` is fixed to `not_applicable` for every row (codify has no native confidence field), matching the same convention used by the 4-row pilot's output CSV.

### Source-grounding audit finding (important — read before trusting `oh_cleveland_fire_2025`'s interest-arbitration row)

94/95 present excerpts are genuinely verbatim-grounded. **1 row is a header-leakage artifact, not a hallucination and not genuine evidence:** `oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`'s "excerpt" is literally this project's own injected window-section header text (`"Arbitration / impasse backstop (legacy code -- may be interest OR grievance arbitration; distinguish from text) [char 1792] --- sseces 45 ..."`), echoed back because the underlying corpus passage for that section was unreadable OCR table-of-contents noise. It passes a naive substring-of-`window_text` grounding check (trivially — the header IS in `window_text`, because this project put it there), but is **not** text from the underlying Cleveland Fire CBA. Flagged explicitly in that row's `notes` field in both the outputs CSV and the durable evidence layer. **Do not cite this row as evidence that Cleveland Fire's CBA references interest arbitration** — the separate, genuinely-grounded `oh_cleveland_police_2025` WITNESSETH-clause excerpt does support that for the *police* contract. **Fix before next scale-up:** switch window-assembly section headers to neutral, keyword-free text (e.g. `--- Excerpt 1 [page 48] ---`) so codebook vocabulary can't leak into the model's evidence.

### Evidence Layer (union rebuild)

`docs/analysis/gabriel_codify_evidence_layer.csv` — now **265 rows** (148 present, 117 not_found, 0 duplicate `evidence_id`s, 0 rows skipped as duplicates on this rebuild since the two input files don't overlap). All 265 rows resolved a `contract_label` from `data/contracts.csv`. All 4 Texas/Ohio matched cities (Houston, Austin, Columbus, Cleveland) now have both a safety (`police`/`fire`) and a non-safety comparison `occupation_class` represented.

### Viewer Paths

- **Latest (open/share this one):** `docs/analysis/gabriel_codify_excerpt_browser_latest.html` (494,551 bytes) — `open docs/analysis/gabriel_codify_excerpt_browser_latest.html`.
- **New dated archival copy:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09_scaleup.html` (byte-identical to latest).
- **Untouched:** `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` (the earlier same-day 92-row archival copy) — confirmed via `git status` not modified by this rebuild.

### Verification performed

- `node --check` on the extracted `<script>` block from the rebuilt `_latest.html` — passed.
- `json.loads()` on both embedded `EVIDENCE` (265 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- Rebuild re-run a second time with identical arguments produced byte-identical `gabriel_codify_evidence_layer.csv` and `_latest.html` (checksummed) — confirms idempotency.
- `python scripts/validate.py` — PASSED (44 contracts / 44 coverage / 3 city_attributes, unchanged).
- `python ingest/audit_coverage.py` — 18 healthy matched pairs, unchanged.
- No live browser rendering/screenshot was performed (same limitation as every prior session — no browser-automation tool available).

### Recommended next run

1. Fix the window-assembly header-leakage failure mode (neutral section headers) in whatever script builds the next evidence-windows CSV.
2. Run a curated Massachusetts codify batch — `scripts/build_codify_evidence_viewer.py`'s label maps already cover `ma`, and the append/union mode built this session (see Code changes above) makes this a clean `--input` addition rather than a full rebuild.

---

## 2026-07-09T20:14:00-04:00 - GABRIEL codify evidence-viewer overhaul: PI-facing plain-English viewer, cascading filters, portable "latest" file

**Commit:** pending in current session (`Overhaul codify excerpt viewer`)

### Current State After This Entry

- Confirmed the prior viewer-build session's changes (`462d629`, "Build GABRIEL codify excerpt viewer") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage) matched expectations.
- Overhauled the viewer built last session for usability/portability per explicit PI feedback: plain-English labels, attribute glossary, cascading filters, evidence-present defaults, "Verified in source text" terminology, per-card explanations, copy buttons, and a stable shareable filename. **No new codify/Harvard Proxy/model calls** — this run only transforms the existing 92-row pilot output.
- Created:
  - `docs/analysis/gabriel_codify_viewer_overhaul_plan_2026-07-09.md`
  - `docs/analysis/gabriel_codify_viewer_usage_2026-07-09.md`
  - `docs/analysis/gabriel_codify_excerpt_browser_latest.html`
- Rewrote `scripts/build_codify_evidence_viewer.py`, `docs/analysis/gabriel_codify_evidence_layer.csv`, `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`, and `docs/analysis/gabriel_codify_viewer_build_audit_2026-07-09.md`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7M), and the wage-mechanism evidence checklist.

### Plain-English Labels and Definitions

Added Python label maps (state, occupation, source role, evidence status, source-grounding status) and a full 19-attribute glossary (label + definition + a short "why this excerpt was coded here" clause), all embedded in `scripts/build_codify_evidence_viewer.py` and matched exactly to the refined Harvard Proxy codebook. **Deliberately not Texas/Ohio-specific** — every map already includes `ma` alongside `tx`/`oh`, so a future Massachusetts codify run needs no further label-map changes. Added human-readable **contract labels**, derived read-only from `data/contracts.csv` (`city_name`, `occupation_class`, `bargaining_unit_name`, `source_type`, `cycle_start`/`cycle_end`) — no invented text; all 4 current contracts resolved a real label (e.g., `"Houston Fire — Houston Professional Fire Fighters Association, Local 341, International Association of Fire Fighters arbitration award, 2024–2029"`). A generic `"City Occupation — contract_id"` fallback exists for any future contract not yet cross-referenced there.

### Cascading Filters

Implemented as a **symmetric faceted system**, not a fixed linear chain: `rowsMatchingExcept(sel, key)` computes the rows matching every filter *except* the one being recomputed, and `rebuildSelectOptions()`/`rebuildAttributeOptions()` repopulate each dropdown's options from that subset — so selecting a state narrows city/contract/attribute options, selecting a contract narrows occupation/source-role/attribute options, and so on, symmetrically, in any order. The attribute (mechanism) dropdown additionally defaults to only mechanisms with `present` evidence in the current filtered scope, with a "Show mechanisms with no evidence" toggle to see the full 19.

### "Grounded" → "Verified in Source Text"

Every UI instance, the usage doc, and the build audit now use **"Verified in source text"** instead of "grounded," with an explicit, repeated explanation: this confirms the excerpt is a real, character-for-character match against its source window — a text-integrity check only, **not** an analytical or causal claim. A persistent warning banner ("These excerpts show evidence that a wage-setting mechanism is discussed in the source text. They do not, by themselves, prove any wage or causal effect.") appears at the page top, in the how-to section, and as a one-line reminder on every present-evidence card.

### Evidence Layer

`docs/analysis/gabriel_codify_evidence_layer.csv` — still **92 rows** (53 present, 39 not_found, 0 duplicate `evidence_id`s), now with **10 additional plain-English columns**: `state_label`, `city_label`, `occupation_label`, `source_role_label`, `contract_label`, `attribute_label`, `attribute_definition`, `evidence_status_label`, `source_grounding_label`, `what_excerpt_shows`.

### Latest Portable Viewer

`docs/analysis/gabriel_codify_excerpt_browser_latest.html` (194,714 bytes, byte-identical to the same-day dated archival copy `gabriel_codify_excerpt_browser_2026-07-09.html` this build). **Share/open this `_latest.html` file** — `open docs/analysis/gabriel_codify_excerpt_browser_latest.html`. Fully self-contained (no external CDN/JS/CSS), no server required.

### Verification (no browser-automation tool available)

- `node --check` on the extracted `<script>` block — passed.
- `json.loads()` on both embedded `EVIDENCE` (92 rows) and `ATTRIBUTES` (19 entries) JSON blocks — both parsed cleanly.
- Grep-confirmed required phrases present: "Verified in source text," "What this excerpt shows," the causal-proof warning, "Copy excerpt"/"Copy citation," "Mechanism glossary," "Show mechanisms with no evidence."
- Confirmed zero external CDN/script references and zero API-key-like strings in the output.
- No live browser rendering/screenshot was performed; recommend the user open the file directly for a final visual/interaction pass (see the build audit's manual-testing checklist).

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/build_codify_evidence_viewer.py
input rows read: 92 | evidence rows written: 92 | present: 53 | not_found: 39 | verified present: 53
rows with contract label from data/contracts.csv: 92/92
```
Unchanged from the prior session in every data/coverage count — this run made zero edits to `data/contracts.csv` (read-only, for labeling), `data/city_coverage.csv`, or `corpus/`.

### Boundaries Observed

- No live GABRIEL calls.
- No Harvard Proxy calls.
- No non-GABRIEL model/API calls.
- No `data/contracts.csv` edits (read-only).
- No `data/city_coverage.csv` edits.
- No document ingestion or `corpus/` changes.
- No API keys or secrets printed, inspected, copied, or committed.
- No schema changes.
- No causal claims made.
- No final PDF/DOCX artifacts created.

### Recommended Next Step

Scale codify to the remaining Texas/Ohio matched-city rows, then run a curated Massachusetts batch (label maps already support it), then extend `scripts/build_codify_evidence_viewer.py` with a genuine append/union mode (keyed on `evidence_id`) before rebuilding, so the evidence layer accumulates across runs instead of being fully overwritten from a single input file each time.

---

## 2026-07-09T18:48:00-04:00 - GABRIEL codify viewer and durable evidence layer built; no live GABRIEL/Proxy/model calls

**Commit:** pending in current session (`Build GABRIEL codify excerpt viewer`)

### Current State After This Entry

- Confirmed the prior Harvard Proxy pilot session's changes (`7c6c3b0`, "Run Harvard Proxy codify pilot") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage) matched expectations.
- Investigated how GABRIEL expects users to view codify excerpts, then built a durable local evidence layer and browser for this project, ahead of expanding codify to more rows/cities.
- Created:
  - `docs/analysis/gabriel_codify_viewer_capability_review_2026-07-09.md`
  - `docs/analysis/gabriel_codify_evidence_layer.csv`
  - `docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html`
  - `docs/analysis/gabriel_codify_viewer_build_audit_2026-07-09.md`
  - `scripts/build_codify_evidence_viewer.py`
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7L), and the wage-mechanism evidence checklist.

### GABRIEL Built-In Viewer Finding

**Real, but notebook-only — not usable as a standalone project artifact.** Inspected `gabriel.utils.passage_viewer` (installed source, 2,858 lines) directly, not just its docstring. `gabriel.view(df, column_name, attributes=..., ...)` is a genuine, fairly sophisticated viewer purpose-built for codify output (`attributes="coded_passages"` shortcut), with color-coded category highlighting (matched substrings wrapped in `<span style='background-color:...'>`), a click-to-cycle legend, and notebook-styled nav controls. It requires a live IPython/Jupyter kernel (`from IPython.display import HTML, display`) to render anything and has no supported file-export path. **The older `tkinter` desktop `PassageViewer` is explicitly retired** in this installed version (raises `RuntimeError` telling users to use `gabriel.view(...)` in a notebook instead). No bundled tutorial notebook ships with the package; the upstream repo (`github.com/openai/GABRIEL`, found via package metadata) was not fetched since the installed source already answered every question definitively.

**Decision:** build a project-local static HTML viewer instead — GABRIEL's viewer was never designed for the multi-dimensional metadata filtering (state/city/contract_id/occupation_class/source_role/attribute/evidence_status/source_grounding_status) this project actually needs, and a notebook-bound display can't be a durable, git-committable artifact anyway. GABRIEL's excerpt-highlighting pattern (`<mark>`-wrapped matched text) was reused as design inspiration.

### Durable Evidence Layer

`docs/analysis/gabriel_codify_evidence_layer.csv` — built from `gabriel_codify_full_codebook_outputs_2026-07-09.csv`, **92 rows** (53 `present`, 39 `not_found`, 0 duplicate `evidence_id`s). Stable ID scheme: `codify_YYYYMMDD_<contract_id>_<attribute>_<sequence>`, designed to be append-friendly across future codify runs. Strictly binary `evidence_status` (present/not_found only, matching codify's actual native output — no invented confidence/caveat values). `source_file` resolved for all 92 rows via lookup against existing `*evidence_windows*.csv` files.

### Local HTML Excerpt Browser

`docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html` (104,453 bytes). Fully self-contained — no external CDN/JS/CSS, no server required, opens by double-click. Sidebar filters for all 8 required dimensions (state, city, contract_id, occupation_class, source_role, attribute, evidence_status, source_grounding_status) plus free-text search (excerpt + notes) and a present-only-by-default "show not_found" toggle. Live counts panel (total/present/not_found/grounded present/selected). Two view modes: **Cards** (one evidence item at a time, `<mark>`-highlighted excerpt, full metadata grid, Prev/Next navigation) and **Table** (compact, all filtered rows). A "How to use this viewer" `<details>` section at the top.

### Verification (no browser-automation tool available)

- Extracted the embedded `<script>` block and syntax-checked with `node --check` — **passed**.
- Extracted and parsed the embedded `const EVIDENCE = [...]` JSON with Python — **92 rows, 53 present, all 17 fields intact**.
- Ran the build script twice (idempotency) plus once more in Task G's checks — identical output each time.
- No live browser rendering/screenshot was performed; recommend the user open the file directly for a final visual pass.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3

python scripts/build_codify_evidence_viewer.py
input rows read: 92 | evidence rows written: 92 | present: 53 | not_found: 39 | grounded present: 53
```
Unchanged from the prior session in every data/coverage count — this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

### Boundaries Observed

- No live GABRIEL calls.
- No Harvard Proxy calls.
- No non-GABRIEL model/API calls.
- No `data/contracts.csv` or `data/city_coverage.csv` edits.
- No document ingestion or `corpus/` changes.
- No API keys or secrets printed, inspected, copied, or committed.
- No schema changes.
- No causal claims made.
- No final PDF/DOCX artifacts created.

### Recommended Next Step

Open the HTML browser directly for a manual visual/interaction pass before relying on it for real review work. When a second codify pilot run happens, re-run `scripts/build_codify_evidence_viewer.py` against a combined input (or add an explicit append/union mode) so the evidence layer and viewer accumulate across runs rather than being overwritten each time.

---

## 2026-07-09T12:06:00-04:00 - Harvard Proxy-enabled GABRIEL/codify full-codebook pilot: adapter built and verified live, 4/4 calls succeeded, 100% source-grounded

**Commit:** pending in current session (`Run Harvard Proxy codify pilot`)

### Current State After This Entry

- Confirmed the prior tiny-pilot session's changes (`b6747d9`, "Pilot GABRIEL codify mechanism extraction") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage) matched expectations.
- **The prior session's blocker (no credentials) is resolved:** the user placed `HARVARD_SUBSCRIPTION_KEY` in the repo's git-ignored `.env` since then. This session confirmed presence exclusively via `python-dotenv`'s `load_dotenv()` (never opened/`cat` `.env` directly; value never printed).
- Ran the first genuinely live GABRIEL/codify calls in this repo's history, via a Harvard Proxy `response_fn` adapter, using the full refined 19-attribute wage-mechanism codebook (not the smaller 11-code set from the prior dry-run).
- Created:
  - `docs/analysis/gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv`
  - `docs/analysis/gabriel_codify_full_codebook_prompt_preview_2026-07-09.md`
  - `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv`
  - `docs/analysis/gabriel_codify_full_codebook_audit_2026-07-09.md`
- Rewrote `scripts/gabriel_codify_pilot.py` (full codebook, `--use-harvard-proxy`, hard cap raised to 4, per-row invocation loop for isolated failure handling).
- Live-run outputs: `tmp/gabriel_codify_pilots/2026-07-09_120200_full_codebook_live/`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7K), and the wage-mechanism evidence checklist.
- Relay-bundle convention: continues using `committed_changed_files.txt` alongside `git_status_post_commit.txt`, per this task's explicit instruction (matching the convention already established last session).

### Adapter Route and Why

**`response_fn` injection** (not `get_all_responses_fn`, not a hand-rolled bypass). Traced `gabriel.codify()`'s actual source (v1.1.8: `api.py` → `tasks/codify.py` → `utils/openai_utils.py`) to confirm the hook is genuinely wired end-to-end, and — critically — that supplying a custom `response_fn` **skips GABRIEL's internal `OPENAI_API_KEY` requirement entirely**, exactly the mechanism needed to route through `HARVARD_SUBSCRIPTION_KEY` instead. The adapter reuses this repo's already-established Harvard Proxy client pattern (`ingest/extract_spans.py`, `scripts/proxy_pilot_must_have_sources.py`) with `gpt-5.4-nano` (confirmed working on this specific proxy elsewhere in the repo; GABRIEL's own default `gpt-5.4-mini` was never tested against it).

**Call-count math worked out in advance:** codify() splits each row into word-chunks (`max_words_per_call`) and the codebook into category-batches (`max_categories_per_call`); with 19 attributes and default settings this would have produced up to 24 calls for 4 rows. Set `max_categories_per_call=19`, `max_words_per_call=1500`, `n_rounds=1` so each selected row produces exactly one live call — 4 rows, 4 calls, matching the cap precisely.

### What Happened

1. Dry run succeeded first (per the task's requirement).
2. First live attempt on row 1 (`tx_houston_fire_2024`) made **zero** network calls — `gabriel.codify` is `async def` and was called without `asyncio.run(...)`, silently returning an un-awaited coroutine (confirmed by Python's own `RuntimeWarning`). Fixed in one line.
3. Retried row 1: **real live call succeeded**, $0.00 cost, correctly distinguished grievance arbitration (present, verbatim excerpt) from interest/impasse arbitration (not_found) — the specific test this codebook refinement exists to check.
4. A second, cosmetic bug (`result_df.insert()` failing since `codify()` already returns the input df's `contract_id` column) was fixed; row 1's already-obtained real result was kept rather than re-querying the API.
5. Rows 2-4 (`tx_houston_other_2024`, `tx_austin_nursehealth_2023`, `oh_columbus_fire_2023`) ran together and all succeeded, $0.00 each.

**Total real live GABRIEL/codify calls this session: 4 attempted, 4 succeeded, 0 failed** — exactly matching the hard cap.

### Source-Grounding Audit

**53 of 53 present-status excerpts (100%) verified as verbatim substrings of their evidence window. Zero hallucinations.** Two findings for human review, both documented with full context in the audit memo: (1) one plausible over-coding (`tx_houston_other_2024`'s `civil_service_or_statutory_employment_channel` matched layoff/classification language with no explicit statutory trigger phrase); (2) one ambiguous arbitration call (`tx_houston_other_2024`'s `interest_arbitration_or_formal_impasse_backstop` excerpt could plausibly be grievance-dispute mediation rather than successor-contract impasse — the compact window lacked the article header needed to disambiguate). A few low-information but still-grounded table-of-contents-line matches also surfaced, a window-construction quality issue, not a hallucination.

### Interface Limitation Discovered

`gabriel.codify()`'s native output is a **binary present/absent snippet list per category** — no confidence field, no explicit "unclear" state. This project's desired richer `evidence_status`/`confidence` schema cannot currently be fully populated by codify() alone, despite `additional_instructions` requesting it (codify's own fixed system-prompt/output-contract does not have a slot for it). This run reports `confidence=not_applicable` honestly rather than inventing a value. See the audit memo's "Recommended next step" for options (pairing with GABRIEL's `rate()` task, or accepting the binary output as-is).

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3
```
Unchanged from the prior session in every count — this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

### Boundaries Observed

- Exactly 4 live GABRIEL/codify calls (not more).
- No full-corpus GABRIEL run.
- No Harvard Proxy scripts run outside this capped pilot script.
- No non-GABRIEL model/API calls.
- No `data/contracts.csv` or `data/city_coverage.csv` edits.
- No document ingestion or `corpus/` changes.
- No API keys or secrets printed, inspected, copied, or committed.
- No schema changes.
- No causal claims made.

### Recommended Next Step

Decide how to add a confidence dimension (codify() alone cannot supply one) before scaling. Clean TOC-line noise from evidence windows and preserve more article-header context around ambiguous arbitration passages in the next run. If addressed, a modestly larger (still capped) pilot covering the remaining Texas/Ohio matched-city rows is the natural next step — not yet full-corpus extraction.

---

## 2026-07-09T11:16:00-04:00 - Tiny GABRIEL/codify pilot: interface inspected, pilot fully designed and staged, but no live calls (no credentials available in this environment)

**Commit:** pending in current session (`Pilot GABRIEL codify mechanism extraction`)

### Current State After This Entry

- Confirmed the prior Texas second matched-city session's changes (`e2cbc52`, "Complete second Texas matched city") were already committed, with only `tmp/` left untracked at session start; pre-session counts (44 contracts / 44 coverage) matched expectations.
- Ran the first GABRIEL/codify pilot attempt in this repo's history. **Result: interface inspection and full pilot design succeeded; live calls did not run because no usable API credential exists in this environment.**
- Created:
  - `docs/analysis/gabriel_codify_interface_inspection_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_design_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_evidence_windows_2026-07-08.csv`
  - `docs/analysis/gabriel_codify_pilot_prompt_preview_2026-07-08.md`
  - `docs/analysis/gabriel_codify_pilot_audit_2026-07-08.md`
  - `scripts/gabriel_codify_pilot.py`
- Ran `tmp/gabriel_codify_pilots/2026-07-09_111259/` (dry-run outputs: `run_config.json`, `selected_windows.csv`, `prompt_preview.md`, `dry_run_log.txt`).
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7J), and the wage-mechanism evidence checklist.
- **Per this session's explicit instruction, updated the relay-bundle convention going forward:** bundles now include `committed_changed_files.txt` (the list of files the commit actually touched) in addition to `git_status_post_commit.txt` (the post-commit cleanliness check) — see this entry's own relay bundle for the first instance of the new convention.

### GABRIEL Interface Findings

`gabriel` is installed and importable (version 1.1.8, real local package, not a stub). `gabriel.codify(df, column_name, *, save_dir, categories=None, additional_instructions="", model="gpt-5.4-mini", n_parallels=650, max_words_per_call=1000, reasoning_effort=None, n_rounds=2, response_fn=None, get_all_responses_fn=None, **cfg_kwargs) -> pandas.DataFrame` — a passage-coding task, docstring: "highlights snippets in text that match qualitative codes." `categories` is exactly the `{code_name: description}` shape needed for this project's 11-code mechanism codebook. `response_fn`/`get_all_responses_fn` are explicit injection points that could in principle route calls through this repo's existing Harvard Proxy client (from `scripts/proxy_pilot_must_have_sources.py`) — not attempted this session, since that wiring doesn't yet exist in repo conventions.

**Credential check (presence/absence only, no values printed):** `OPENAI_API_KEY` NOT SET, `OPENAI_BASE_URL` NOT SET, `HARVARD_SUBSCRIPTION_KEY` NOT SET. GABRIEL's default call path needs the first two; this repo's Harvard Proxy pattern needs the third (and is a separate hand-built code path, not integrated with `codify()`). Neither is available, so **zero live calls were attempted** (0/0/0 attempted/succeeded/failed) — this is the clean "credentials missing, dry-run only" case the task's own hard boundary anticipates, not a partial failure.

### Pilot Design (fully staged, ready for the first credentialed run)

Selected 3 contracts (all `text_quality=clean`, all with an existing hand-built mechanism-excerpt answer key to audit against): `tx_houston_fire_2024` (8/11 mechanisms present in the prior extraction), `tx_houston_other_2024` (10/11), `oh_columbus_fire_2023` (11/11). Built one evidence window per contract by concatenating the already-extracted `evidence_status=present` excerpt bodies — 2,565 / 5,407 / 5,862 characters — with mechanism-name labels deliberately stripped from the window text so a future live run is a genuine coding test, not a label-echo exercise. Wrote the full codebook and a verbatim-only / no-causal-inference / default-to-`not_found` prompt spec (`additional_instructions`).

`scripts/gabriel_codify_pilot.py`: defaults to dry-run; `--live` requires an explicit `--max-calls` hard-capped at 3 in code (not just a CLI flag); refuses cleanly and falls back to dry-run output if no credential is present (tested and confirmed both paths this session — dry-run succeeds normally, `--live` without a credential prints a clear refusal and produces dry-run output instead of crashing or hanging).

### Boundaries Observed

- No GABRIEL calls (0 live calls made).
- No Harvard Proxy scripts run.
- No non-GABRIEL model/API calls.
- No `data/contracts.csv` or `data/city_coverage.csv` edits.
- No document ingestion or `corpus/` changes.
- No API keys or secrets printed, inspected, copied, or committed.
- No schema changes.
- No causal claims made.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3
```
Unchanged from the prior session in every count — this run made zero edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`.

### Recommended Next Step

Obtain a usable credential (`OPENAI_API_KEY`/`OPENAI_BASE_URL`, or wire `gabriel.codify()`'s `response_fn` injection point to the existing Harvard Proxy client) before attempting the first live call. When available, run `python scripts/gabriel_codify_pilot.py --live --max-calls 3` (or fewer) against the already-staged 3-row sample, then complete the source-grounding audit already scaffolded in `gabriel_codify_pilot_audit_2026-07-08.md` — check whether every returned excerpt is a verbatim substring of its window text, whether any mechanism is marked `present` without a real quoted match, and how the output compares to the known hand-extraction answer key — before deciding whether `codify()` should scale beyond this pilot.

---

## 2026-07-08T17:59:00-04:00 - Texas second matched city complete: Austin EMS meet-and-confer agreement found and ingested; Texas now on par with Ohio (two matched cities each)

**Commit:** pending in current session (`Complete second Texas matched city`)

### Current State After This Entry

- Confirmed the prior Houston Fire session's changes (`4cd7550`, "Resolve Houston fire source") were already committed, with only `tmp/` left untracked at session start; pre-session counts (43 contracts / 43 coverage) matched expectations.
- Ran a Texas second matched-city completion pass before any GABRIEL/codify pilot. Design target: two matched cities per comparison state. Ohio already had Columbus + Cleveland; Texas had Houston fully matched but Austin had police + fire with no non-safety partner (the AFSCME Local 1624 document was previously confirmed a non-wage-setting consultation policy).
- Created:
  - `docs/analysis/texas_second_matched_city_preflight_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_source_resolution_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_second_matched_city_summary_2026-07-08.md`
- Added one public document under `corpus/tx_austin/`: `tx_austin_aemsa_ems_meet_confer_2023_2027.pdf`.
- Added one causal row to `data/contracts.csv` (`tx_austin_nursehealth_2023`) and one matching row to `data/city_coverage.csv`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7I), the wage-mechanism evidence checklist, and `texas_ohio_approved_source_plan_2026-07-08.csv` (AFSCME 1624 backup row's caveat marked superseded).

### What Was Found

Fresh search terms surfaced a genuine lead beyond AFSCME Local 1624: the City of Austin's official `austintexas.gov/labor-relations` page family (the same hosting pattern already used for the ingested police and fire agreements) has an **EMS Meet and Confer Agreement** page linking to a complete meet-and-confer agreement between the City and the **Austin EMS Association (AEMSA)**, effective October 1, 2023 through September 30, 2027. Downloaded and text-extracted (88 pages, clean text layer via `ingest/extract_text.py`). Article 2's own definition restricts the bargaining unit to "Emergency Medical Services Personnel" per Texas Health and Safety Code Chapter 773, requiring "substantial knowledge of Emergency Prehospital Care," and explicitly excludes civilian employees — a clean, single-occupation unit with no recognition-clause-first bundling ambiguity. Contains a real 4-year fiscal-year wage schedule, on-call/call-back pay, shift differential, education incentive pay, and a grievance-arbitration clause (contract-interpretation only, not interest arbitration).

A City Clerk council item (File #26-1362) referencing "non-sworn employees not covered by collective bargaining or meet and confer agreements" was checked and confirmed to be a red herring — boilerplate distinguishing civilian employees from the three groups (police/fire/EMS) that DO have negotiated agreements, not a pointer to a fourth agreement.

### Row Added To `data/contracts.csv`

- `tx_austin_nursehealth_2023` — Austin EMS Association, `occupation_class=nurse_health`, `safety_flag=0`, `source_type=cba`, cycle 2023-10-01 to 2027-09-30. `interest_arbitration_flag=0` (grievance/contract-interpretation arbitration only). **Flagged explicitly in row notes and the checklist:** EMS is civil-service-protected and statutorily adjacent to police/fire (shares a joint Firefighters'/Police Officers'/EMS Civil Service Commission under Chapter 143; bargains under Chapter 142 Subchapter D, the same chapter as Austin police) — this should never be described as an ordinary civilian/clerical comparison unit in later report language.

### Backup City Evaluation

**Not triggered.** Because Austin resolved successfully, Fort Worth and San Antonio were not evaluated for fetch/ingestion. Both remain documented as `deferred` in `texas_second_matched_city_source_resolution_2026-07-08.csv`, carrying forward prior planning's finding that neither city has a confirmed non-safety institutional channel (Fort Worth: a unilateral "Pay for Performance Program," not a negotiated agreement; San Antonio: none identified).

### Coverage Impact

**Texas now has two fully matched cities, on par with Ohio:**
- Texas: Houston (police+fire vs. HOPE, other) and Austin (police+fire vs. EMS, nurse_health) — both healthy overlap-cycle matches.
- Ohio: Columbus (healthy overlap-cycle) and Cleveland (exploratory-adjacent, not healthy — cycle-timing gap, unchanged this session).

Zero Texas/Ohio safety units are unmatched as of this run; the three remaining unmatched safety units in the corpus are all Massachusetts rows (Somerville x2, Newton), unrelated to this run.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 44 | discourse: 0 | coverage: 44 | city_attributes: 3 | cities: 13
healthy matched pairs: 18
  exact-cycle: 9
  overlap-cycle: 9
exploratory adjacent matches: 2
safety units unmatched: 3
```

### Boundaries Observed

- No GABRIEL calls.
- No Harvard Proxy calls.
- No model/API calls from project scripts.
- No PRRs/FOIA.
- No statutes, budgets, pay plans, city pages, news stories, or consultation-only policies were ingested as causal rows.
- No schema changes.

### Recommended Next Step

**The pre-GABRIEL design target is met** — both comparison states now have two matched cities each. Recommend proceeding to the tiny GABRIEL/codify pilot next; no remaining structural blocker for a Texas/Ohio pilot.

---

## 2026-07-08T15:12:00-04:00 - Houston Fire resolved: genuine 2026 arbitration award found and ingested; Houston now fully matched across all three tiers

**Commit:** pending in current session (`Resolve Houston fire source`)

### Current State After This Entry

- Confirmed the prior Texas/Ohio held-out-target session's changes (`6ce5080`, "Resolve Texas and Ohio held-out sources") were already committed, with only `tmp/` left untracked at session start; pre-session counts (42 contracts / 42 coverage) matched expectations.
- Ran a narrow, single-target search focused exclusively on Houston Fire, the last remaining held-out Texas/Ohio target.
- Created:
  - `docs/analysis/houston_fire_source_resolution_preflight_2026-07-08.md`
  - `docs/analysis/houston_fire_source_resolution_2026-07-08.csv`
  - `docs/analysis/houston_fire_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/houston_fire_source_identity_audit_2026-07-08.md`
  - `docs/analysis/houston_fire_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/houston_fire_metadata_addition_2026-07-08.csv`
  - `docs/analysis/houston_fire_source_resolution_summary_2026-07-08.md`
- Added three public documents under `corpus/tx_houston/`: `tx_houston_hpffa_fire_arbitration_award_2026.pdf` (primary), `tx_houston_hpffa_fire_settlement_agreement_2026.pdf` and `tx_houston_hpffa_fire_mou_2024.pdf` (companions).
- Added one causal row to `data/contracts.csv` (`tx_houston_fire_2024`) and one matching row to `data/city_coverage.csv`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7H), the wage-mechanism evidence checklist, and `texas_ohio_approved_source_plan_2026-07-08.csv` (both the Houston-fire approved row and the HFOA backup row's caveats updated).

### What Was Found

No official City-of-Houston-hosted copy of the full base 2024-2029 CBA text exists at any URL checked (press release page, HR/legal folders, HPFFA's own `local341.org` site — no public CBA section). Web search surfaced a new lead: `hfdcoa.org`, the official site of the Houston Fire Department **Chief Officers Association (HFOA)** — a real, distinct union from HPFFA (rank-and-file), representing chief officers. Its `/cba-2024-2029/` page hosts five HPFFA/City-of-Houston documents (not HFOA's own agreement): an MOU (2024-06-11), an Interim Amendment, a wage-schedule exhibit, a Settlement Agreement and Release (2026), and an **Arbitration Opinion and Award** (2026-02-27, AAA Case No. 01-25-0005-2917, Arbitrator William E. Hartsfield).

All five were downloaded and text-extracted (`ingest/extract_text.py`, text-layer/OCR) for verification. The Arbitration Award is a genuine, complete, 17-page grievance-arbitration ruling on Houston Fire's 2024-2029 CBA Article 17 Sec.2 "Three Percent Pay Escalator," quoting substantial CBA text verbatim (Articles 2, 6, 14, 17, 25) and explicitly incorporating the Settlement Agreement ("Attachment 1... incorporated by this reference for all purposes as if fully set out in this Award") and citing the MOU to interpret the escalator clause at issue. Independently corroborated by ABC13 Houston news reporting of the identical ruling (S.B. 916 new-revenue dispute).

### Row Added To `data/contracts.csv`

- `tx_houston_fire_2024` — Houston Professional Fire Fighters Association, Local 341 (IAFF), `occupation_class=fire`, cycle 2024-07-01 to 2029-06-30, `source_type=arbitration_award`. `interest_arbitration_flag=0` — **this is grievance/contract-interpretation arbitration under CBA Article 14, explicitly NOT the Sec.174.1535 population-triggered compulsory interest-arbitration mechanism.** `binding_arbitration_statute` documents this distinction explicitly so it is never conflated in later analysis. `arbitration_clause_text` captures Article 14's "final and binding...no authority to establish provisions of a new agreement" language verbatim. `total_comp_note` captures the full FY25-29 escalator wage schedule and Settlement/MOU monetary terms as free text (the schedule's own FY29 date range reads "7/1/29 to 6/30/30," an apparent internal inconsistency in the source document, flagged rather than silently corrected).

### Multi-Document Fetch Justification

Fetched three (not one) documents under the task's "clearly parts of the same operative agreement, both necessary" exception: the Award's own text explicitly incorporates the Settlement by reference, and cites the MOU to interpret the very clause under dispute. The Interim Amendment and wage-schedule exhibit were verified genuine but deliberately left unfetched (not incorporated by reference into the ingested chain) — `base_wage_entry`/`base_wage_top` were left blank rather than populated from an unstored source.

### Coverage Impact

**Houston is now the first Texas/Ohio city with all three institutional tiers matched:** police and fire both show a healthy overlap-cycle match against the non-safety HOPE/AFSCME Local 123 row (2024-2027).

### Mechanism/Identity Findings

- Confirmed as a byproduct: the long-open "HFOA-vs-HPFFA relationship" question is resolved — HFOA is a genuinely distinct chief-officers' union, but no separate HFOA CBA was located; `hfdcoa.org` simply hosts HPFFA/City documents.
- Mechanism excerpts present: arbitration/impasse backstop (Article 14), wage schedule (Article 17 Sec.2's 5-year escalator table), training/certification pay (EMT certification, MOU Sec.4), total compensation (Settlement's uniform allowance/holiday buy-back, MOU's Special/Incentive Pay cap), safety/public-safety framing (escalator tied to new public-safety revenue). Not found: peer-wage comparability, staffing/recruitment/retention, subcontracting.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3 | cities: 13
healthy matched pairs: 16
  exact-cycle: 9
  overlap-cycle: 7
exploratory adjacent matches: 2
safety units unmatched: 5
```

### Boundaries Observed

- No GABRIEL calls.
- No Harvard Proxy calls.
- No model/API calls from project scripts.
- No PRRs/FOIA.
- No statutes, budgets, pay plans, city pages, news stories, or legal pages were ingested as causal rows.
- The source was correctly classified `arbitration_award` (a real award) and not conflated with Sec.174.1535 compulsory interest arbitration.
- No schema changes.

### Recommended Next Step

Houston Fire is resolved for this project's purposes. Recommend moving to a tiny GABRIEL/codify pilot next, now that Houston has reached full three-tier matching — the first Texas/Ohio city to do so. The full base-CBA text remains a lower-priority, non-blocking open item for a future session.

---

## 2026-07-08T13:48:00-04:00 - Texas/Ohio held-out-target resolution; Austin fire added; Houston fire remains unresolved; Austin non-safety design question closed

**Commit:** pending in current session (`Resolve Texas and Ohio held-out sources`)

### Current State After This Entry

- Confirmed the prior Texas/Ohio first-batch live-acquisition session's changes (`4134f45`, "Ingest Texas and Ohio first batch") were already committed, with only `tmp/` left untracked at session start; pre-session counts (41 contracts / 41 coverage / 43 corpus files) matched expectations.
- Resolved 5 of 6 held-out targets from the prior dry-run via bounded public web checks; fetched and ingested exactly 1 new causal source (Austin fire).
- Created:
  - `docs/analysis/texas_ohio_heldout_target_preflight_2026-07-08.md`
  - `docs/analysis/texas_ohio_heldout_source_resolution_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_ohio_second_batch_ingestion_extraction_summary_2026-07-08.md`
- Added one public agreement PDF under `corpus/tx_austin/tx_austin_afa975_fire_cba_2023_2025.pdf`.
- Added one causal row to `data/contracts.csv` (`tx_austin_fire_2023`) and one matching row to `data/city_coverage.csv`.
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist (new Section 7G), the wage-mechanism evidence checklist, and `texas_ohio_approved_source_plan_2026-07-08.csv` (Austin fire caveat marked RESOLVED).

### Held-Out Target Resolution (All Six)

1. **Houston fire full-CBA — unresolved.** The houstontx.gov press-release page links only to a 2024-04-30 City Council presentation slide deck (confirmed via `ingest/extract_text.py`: title slide, bullet points, no numbered CBA articles), not the executed agreement. No official full-text copy located; the only full-text copy anywhere is a non-official news mirror (khou.com), previously flagged as unsuitable. Deferred.
2. **Austin fire — resolved and ingested.** Official austintexas.gov page verbatim-labels a document "Current Agreement" (Austin Firefighters Association Local 975 CBA, term through 2025-09-30); a still-in-flight Dec.2025 successor exists only as ~24 separate negotiation-session/redline documents, not a single clean copy. Fetched, 100-page clean text layer, identity confirmed via Recognition (Article 3) and Term (Article 30) articles.
3. **Austin non-safety (AFSCME Local 1624) — resolved, confirmed non-causal.** Located City Council Resolution No. 20260122-049 (adopted 2026-02-26): a consultation-policy resolution (regular labor-management meetings on employment policy, reorganization, AI/automation), not a negotiated wage-setting CBA. Not added as a contracts.csv row. This closes a design question flagged by a prior session.
4. **Austin budget/pay-plan — resolved, context-only.** `austintexas.gov/department/compensation-division` and `services.austintexas.gov/hr/jobdesc/job_title_pay.cfm` both return HTTP 200. Not fetched/stored (context-only per task scope).
5. **Cleveland budget/pay-plan — resolved, context-only.** Official 2025 City of Cleveland Budget Book PDF returns HTTP 200 (10.4MB). Not fetched/stored.
6. **Ohio SERB archive — resolved, context-only.** `serb.ohio.gov/view-document-archive` now returns HTTP 200 (previously 404 in the prior dry-run session).

### Row Added To `data/contracts.csv`

- `tx_austin_fire_2023` — Austin Firefighters Association Local 975 (IAFF), `occupation_class=fire`, cycle 2023-09-24 to 2025-09-30. `interest_arbitration_flag=1` (Article 30 ties the Agreement's effective date to an interest-arbitration award; successor impasse extends the Agreement pending mutually-agreed mediation/interest arbitration — Texas Chapter 174's general non-compulsory model, distinct from Houston Fire's population-triggered compulsory arbitration under §174.1535). `no_strike_clause_flag=1`. `longevity_pay_flag=1` ($100/year per year of service, max 25 years).

### Mechanism/Recognition Findings

- Recognition-clause-first rule was scoped as not applicable to a single-occupation fire unit (no bundled multi-department ambiguity); recognition clause still read and captured verbatim for identity confirmation.
- Mechanism excerpts present: arbitration/impasse backstop, staffing/recruitment, overtime tied to staffing levels, wage schedule, training/certification pay, premium-pay differentials, total-compensation (health insurance reference), safety-risk (hazardous-duty and Line-of-Duty-Death language). Not found: peer-wage comparability, subcontracting/outsourcing.

### Coverage Impact

Austin now has **two unmatched safety units** (police, fire) and **zero** matched non-safety comparison units — the least-matched of the four first-batch cities. Houston, Columbus, Cleveland matching status unchanged from the first batch.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 5
```

### Boundaries Observed

- No GABRIEL calls.
- No Harvard Proxy calls.
- No model/API calls from project scripts.
- No PRRs/FOIA.
- No budgets, pay plans, statutes, legal pages, or SERB archive pages were ingested as causal CBA rows.
- No meet-and-confer or consultation agreement was classified as `arbitration_award`.
- No wage panels, OEWS/BLS data builds, or final PDF/DOCX artifacts.
- No schema changes.

### Recommended Next Step

Prioritize a dedicated search for an official houstontx.gov full-text copy of the HPFFA/IAFF Local 341 CBA before any further Texas/Ohio acquisition. Separately, treat Austin's non-safety comparison gap as the more consequential near-term target: confirm whether any actual wage-negotiating body exists for Austin municipal employees beyond the civil-service classification system and the now-confirmed (non-wage-setting) AFSCME consultation agreement.

---

## 2026-07-08T22:00:00-04:00 - Texas/Ohio first-batch live acquisition; 9 agreement rows added; recognition-clause-first extraction complete

**Commit:** pending in current session (`Ingest Texas and Ohio first batch`)

### Current State After This Entry

- The prior acquisition dry-run commit was confirmed at session start (`71bb26c Prepare Texas and Ohio acquisition dry run`), with only `tmp/` untracked before edits.
- Fetched exactly the nine rows from `texas_ohio_acquisition_dry_run_2026-07-08.csv` where `dry_run_status=ready_for_live_fetch`, `approval_status=approved_first_batch`, `store_now=no`, and `ingest_now=no`.
- Added nine public agreement PDFs under:
  - `corpus/tx_houston/`
  - `corpus/tx_austin/`
  - `corpus/oh_columbus/`
  - `corpus/oh_cleveland/`
- Added nine causal agreement rows to `data/contracts.csv` and nine matching rows to `data/city_coverage.csv`.
- Created the live acquisition/extraction audit package:
  - `docs/analysis/texas_ohio_live_ingestion_preflight_2026-07-08.md`
  - `docs/analysis/texas_ohio_live_fetch_manifest_2026-07-08.csv`
  - `docs/analysis/texas_ohio_source_identity_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_recognition_clause_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_recognition_clause_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_mechanism_excerpt_extraction_2026-07-08.md`
  - `docs/analysis/texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`
  - `docs/analysis/texas_ohio_contracts_metadata_additions_2026-07-08.csv`
  - `docs/analysis/texas_ohio_ingestion_extraction_summary_2026-07-08.md`
- Lightly updated `all_groups_source_needs_2026-07-06.csv`, the report review checklist, and the wage-mechanism evidence checklist with pointers to the completed live run.

### Rows Added To `data/contracts.csv`

- `tx_houston_police_2024` — Houston Police Officers' Union, `occupation_class=police`, cycle 2024-07-01 to 2025-06-30.
- `tx_houston_other_2024` — HOPE/AFSCME Local 123, `occupation_class=other`, cycle 2024-11-01 to 2027-06-30.
- `tx_austin_police_2024` — Austin Police Association, `occupation_class=police`, cycle 2024-10-29 to 2029-09-30.
- `oh_columbus_police_2023` — FOP Capital City Lodge No. 9, `occupation_class=police`, cycle 2023-12-09 to 2026-12-08.
- `oh_columbus_fire_2023` — IAFF Local 67, `occupation_class=fire`, cycle 2023-11-01 to 2026-10-31.
- `oh_columbus_other_2024` — AFSCME Ohio Council 8 Local 1632, `occupation_class=other`, cycle 2024-04-01 to 2027-03-31.
- `oh_cleveland_police_2025` — CPPA Patrol Officer Bargaining Unit, `occupation_class=police`, cycle 2025-04-01 to 2028-03-31.
- `oh_cleveland_fire_2025` — Cleveland Fire Fighters Local 93, `occupation_class=fire`, cycle 2025-04-01 to 2028-03-31.
- `oh_cleveland_other_2022` — AFSCME Ohio Council 8 Local 100, `occupation_class=other`, cycle 2022-04-01 to 2025-03-31.

### Recognition-Clause-First Findings

- Houston HOPE/AFSCME Local 123: bargaining unit consists of municipal employees excluding department directors, elected officials, and classified police/fire; keep `occupation_class=other`.
- Columbus AFSCME Local 1632: recognition clause covers employees in Appendix A class titles and excludes uniformed police/fire, HR, civil-service, confidential, part-time, seasonal, and temporary categories; keep `occupation_class=other`.
- Cleveland AFSCME Local 100: recognition/classification list spans administrative, building/housing, public health, public utilities, dispatcher/radio, airport/ARFF-adjacent, and other titles; keep `occupation_class=other`.

### Source/Text Quality Notes

- Austin police was resolved from the official Austin labor-relations page to the linked Widen original-file endpoint; stored file is the agreement PDF, not the page HTML.
- Cleveland IAFF Local 93 is image-heavy. Full OCR was not pursued; targeted local OCR confirmed identity, recognition, and selected mechanism text. Metadata uses `text_quality=ocr_messy`.
- All other fetched PDFs had usable text layers and are marked `text_quality=clean`.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 41 | discourse: 0 | coverage: 41 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 41 | discourse: 0 | coverage: 41 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 4
```

Austin police is now an unmatched safety row. Cleveland police/fire have adjacent, not healthy, non-safety matches because the Local 100 cycle ends in 2025 while the safety cycles start in 2025.

### Boundaries Observed

- No GABRIEL calls.
- No Harvard Proxy calls.
- No model/API calls from project scripts.
- No PRRs/FOIA.
- No budgets, pay plans, statutes, legal pages, or SERB archive pages were ingested as causal CBA rows.
- No wage panels, OEWS/BLS data builds, or final PDF/DOCX artifacts.
- No schema changes.

### Recommended Next Step

Before any second live acquisition, confirm the remaining held-out Texas/Ohio targets: Houston fire full-CBA target, Austin fire cycle-specific target, Austin pay-plan URL, Cleveland budget/pay-plan URL, and the current Ohio SERB archive path. Prioritize Austin fire/non-safety confirmation if the goal is to keep the new Austin police row from remaining unmatched.

---

## 2026-07-08T21:00:00-04:00 - Texas/Ohio acquisition dry-run; recognition-clause-first standard; no acquisition or data edits

**Commit:** pending in current session (`Prepare Texas and Ohio acquisition dry run`)

### Current State After This Entry

- Completed a controlled Texas/Ohio acquisition dry-run for the first-batch cities: Houston, Austin, Columbus, and Cleveland.
- Created:
  - `docs/analysis/source_planning_csv_hygiene_standard_2026-07-08.md`
  - `docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md`
  - `docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.md`
  - `docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.csv`
- Updated:
  - `docs/analysis/texas_ohio_approved_source_plan_2026-07-08.csv` (only stale Austin fire/police URL paths and associated fetch/caveat text)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv`
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/wage_mechanism_evidence_checklist.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were not touched. No source document was downloaded or stored. No ingestion occurred. No GABRIEL calls, Harvard Proxy calls, model/API calls from project scripts, PRRs, OEWS/BLS build, wage panel, or final PDF/DOCX artifact occurred.

### Source-Plan and CSV Hygiene Status

- `texas_ohio_approved_source_plan_2026-07-08.csv` parses cleanly with Python `csv`.
- Required columns are present.
- Controlled values are clean.
- No duplicate `source_target` or `proposed_filename` values were found.
- No `approved_first_batch` row is missing `source_url_or_lookup_path`, `proposed_filename`, `proposed_contract_id`, `proposed_occupation_class`, `proposed_source_type`, `proposed_corpus`, or `fetch_instruction`.
- No budget/pay-plan row is incorrectly marked causal.
- No legal/statutory row is incorrectly marked causal.
- Broad non-safety rows remain provisionally `occupation_class=other`, not `clerical_admin`, `public_works`, or another precise value.
- New dry-run CSV was written with `csv.DictWriter` and passed controlled-value checks. All rows have `store_now=no` and `ingest_now=no`.

### Recognition-Clause-First Rule

Broad non-safety agreements must not receive a precise `occupation_class` until the later extraction pass reads the recognition clause, bargaining-unit description, coverage article, appendix/classification list, or wage-schedule classification list. This applies to Houston HOPE/AFSCME Local 123, Columbus AFSCME Local 1632, Cleveland AFSCME Local 100, Austin AFSCME Local 1624 if later promoted, and CWA/technical units if later promoted. The conservative default is `other` for mixed municipal units unless the document text clearly supports an existing schema value.

No schema change is authorized by this dry-run.

### Acquisition Dry-Run Results

`docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.csv` has 20 rows:

```text
dry_run_status counts:
ready_for_live_fetch: 9
needs_url_confirmation: 5
context_only: 6
```

Rows marked `ready_for_live_fetch`:
- Houston police — HPOU Meet & Confer Agreement
- Houston non-safety — HOPE/AFSCME Local 123 meet-and-confer agreement
- Austin police — Austin Police Association meet-and-confer agreement
- Columbus police — FOP Capital City Lodge No. 9 CBA
- Columbus fire — IAFF Local 67 CBA
- Columbus non-safety — AFSCME Local 1632 CBA
- Cleveland police — CPPA CBA
- Cleveland fire — IAFF Local 93 CBA
- Cleveland non-safety — AFSCME Ohio Council 8 Local 100 CBA

Rows marked `needs_url_confirmation`:
- Houston fire — official page live, but confirm full executed HPFFA/IAFF Local 341 CBA target rather than only settlement/summary material.
- Austin fire — corrected official page live, but exact 2014-2024-window cycle target needs confirmation because the live page now surfaces a Dec. 18, 2025 agreement link.
- Austin budget/pay plan — specific compensation/pay-plan URL still not confirmed.
- Cleveland budget/pay plan — specific budget/pay-plan URL still not confirmed.
- Ohio SERB archive — prior archive URL returned HTTP 404; current path needs confirmation.

Rows marked `context_only` include Houston and Columbus budget/pay-plan context plus Texas Chapters 174/146/142 and Ohio ORC Chapter 4117. These are not CBA rows and should not enter `data/contracts.csv`.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

Get explicit user/PI approval before any live acquisition. If approved, Codex should first run a fetcher dry-run for the 9 `ready_for_live_fetch` agreement rows and keep the 5 `needs_url_confirmation` rows out of live fetch until their exact source paths are confirmed. During later extraction, read recognition/coverage/classification text before assigning any precise non-safety `occupation_class`.

---

## 2026-07-08T20:00:00-04:00 - Texas/Ohio final pre-ingestion approval audit; CSV hygiene defects found and fixed; 15-source approved batch; no acquisition, no data edits

**Commit:** pending in current session (`Approve Texas and Ohio source plan`)

### Current State After This Entry

- Confirmed the prior Texas/Ohio multi-city scan session's changes (`a3217b2`, "Compare Texas and Ohio candidate cities") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Converted three prior Texas/Ohio sessions' work into a small, exact, reviewable ingestion plan.
- Created:
  - `docs/analysis/texas_ohio_final_pre_ingestion_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_approved_source_plan_2026-07-08.csv`
- Updated (light-to-moderate touches):
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv` (hygiene-repaired + cross-referenced)
  - `docs/analysis/texas_ohio_multicity_source_targets_2026-07-08.csv` (hygiene-repaired + cross-referenced)
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (hygiene-repaired)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (hygiene-repaired)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv`
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7D)
  - `docs/analysis/wage_mechanism_evidence_checklist.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** touched. No GABRIEL calls, model/API calls, or Harvard Proxy calls were made. No document was downloaded or stored as project data. No ingestion occurred. No PRR was recommended. No causal claim was made about Texas or Ohio wage outcomes.

### What This New Package Does — and the Key Finding

- **CSV hygiene check (Task A) found real, mechanically-verifiable defects, not cosmetic ones.** 19 of 75 data rows across three prior-session CSVs (`texas_ohio_source_ingestion_audit_2026-07-08.csv`, `texas_ohio_multicity_source_targets_2026-07-08.csv`, `texas_ohio_candidate_source_targets_2026-07-07.csv`) had column-count mismatches from unescaped commas in free-text cells — a defect any future automated ingestion script would break on, since it would also parse these files with Python's `csv` module. One row in `texas_ohio_legal_source_audit_2026-07-07.csv` had the same issue (a Ballotpedia URL with literal commas). Two files also had controlled-vocabulary drift (long descriptive text in columns meant to hold only `high`/`medium`/`low`). **All defects were found, repaired, and re-verified — all five reviewed CSVs are now parse-clean, duplicate-free, and controlled-value-clean.**
- **Approved source plan** (`texas_ohio_approved_source_plan_2026-07-08.csv`, 38 rows, built directly as structured Python data with `csv.writer` to guarantee correct quoting): 15 rows marked `approved_first_batch` (Houston: fire/police/non-safety/budget; Austin: fire/police/budget; Columbus: police/fire/non-safety/budget; Cleveland: police/fire/non-safety/budget) — within the requested 12-16 range. 5 rows `context_only` (TX Ch.174/146/142+Ch.617, OH ORC 4117, OH SERB archive). 14 `backup` rows (Fort Worth, San Antonio, Cincinnati, Toledo, plus Houston's HFOA and Austin's AFSCME 1624 consultation agreement, plus Columbus's CWA and Cleveland's FOP Lodge 8 as within-city backups). 4 `defer` rows (Dallas, El Paso, Akron, Dayton).
- **Final pre-ingestion audit memo** (`texas_ohio_final_pre_ingestion_audit_2026-07-08.md`): confirms Houston/Austin/Columbus/Cleveland as the right first-batch cities; documents the CSV hygiene findings in detail; specifies metadata conventions for later ingestion (proposed `contract_id` pattern, `occupation_class` — most non-safety unions provisionally `other`, pending a recognition-clause read, paralleling the Wayland precedent — `source_type=cba` for all meet-and-confer/CBA sources since the schema has no separate value, `retrieval_method=public_download`, `text_quality=unknown` pre-fetch); and states explicit ingestion guardrails (never ingest statutes as CBAs, never treat budgets as causal corpus, never invent contract terms).
- **Austin's non-safety consultation agreement (AFSCME Local 1624) was deliberately NOT approved for the first batch** — its specific document URL was never located, so per the hard boundary against approving vaguely-described targets, it is marked `backup` and Austin's civil-service pay-plan pages serve as the approved-batch's non-safety fallback instead.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route the final pre-ingestion audit memo and approved source plan CSV to the PI for explicit authorization to begin fetching.
2. If approved: `--dry-run` through `ingest/fetchers/` against the 15 approved-plan URLs before any live fetch.
3. Resolve smaller remaining items (HFOA-vs-HPFFA relationship; non-safety unions' occupation-class composition; Cleveland's/Austin's not-yet-located budget-page URLs) alongside the dry-run.
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state.

### Notes For ChatGPT Review

- **Any future session that edits a Texas/Ohio (or other state-comparison) planning CSV via the Write/Edit tools should immediately spot-check it with Python's `csv` module** — this session found that two full prior sessions of in-place edits to these files never caught real parsing defects, because a rendered/visual read of the table does not expose an unescaped-comma column shift.
- Do not re-introduce descriptive sentences into `source_availability`/`expected_design_value`/`expected_comparison_value`-type columns — keep those to the declared short controlled values and put explanatory detail in `rationale`/`notes` instead.
- Treat `texas_ohio_approved_source_plan_2026-07-08.csv` as the single authoritative reference for "what to fetch first" going forward; the older `texas_ohio_source_ingestion_audit_2026-07-08.csv` and `texas_ohio_multicity_source_targets_2026-07-08.csv` remain useful for narrative detail but now cross-reference the approved plan rather than duplicating its authority.
- No document was downloaded or stored as project data this session.

---

## 2026-07-08T16:00:00-04:00 - Texas/Ohio multi-city pre-ingestion scan; first ingestion batch recommended (Houston+Austin, Columbus+Cleveland); no acquisition, no data edits

**Commit:** pending in current session (`Compare Texas and Ohio candidate cities`)

### Current State After This Entry

- Confirmed the prior Texas/Ohio legal-followup session's changes (`9aee8fd`, "Audit Texas and Ohio source targets") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Broadened the prior Houston/Columbus-focused assessment across 5 additional Texas cities (San Antonio, Dallas, Austin, Fort Worth, El Paso) and 5 additional Ohio cities (Cleveland, Cincinnati, Toledo, Akron, Dayton), specifically to test whether the earlier recommendation was overfit to two population-exceptional cities.
- Created:
  - `docs/analysis/texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md`
  - `docs/analysis/texas_ohio_multicity_source_targets_2026-07-08.csv`
- Updated (light-to-moderate touches):
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv` (first_batch/backup designations added; 6 new rows for Austin/Cleveland/Toledo)
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (Austin/Cleveland upgraded to must_have)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (4 rows resolved, 3 new rows added)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (2 rows revised, 1 added)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7C)
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** touched. No GABRIEL calls, model/API calls, or Harvard Proxy calls were made. No document was downloaded or stored as project data — every source is a citation/URL. No ingestion occurred. No PRR was recommended. No causal claim was made about Texas or Ohio wage outcomes, and no single city was treated as representative of its state.

### What This New Package Does

- **Multi-city scan memo** (`texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md`): the headline finding is that **the Houston fire-full-bargaining(Ch.174)/police-meet-and-confer(Ch.142) split is NOT Houston-specific** — Austin and Fort Worth both show the identical split, confirmed via each city's own official labor-relations pages, meaning the general institutional pattern generalizes across a population range from ~980,000 to ~2.4 million. What remains genuinely Houston-only (confirmed via the prior session's direct statute reads) is the *compulsory* nature of its fire arbitration (§174.1535, population-gated ≥1.9M) and the *existence* of a statutory non-safety channel (Ch.146, population-gated ≥1.5M). Dallas shows a third pattern (joint police+fire meet-and-confer, no Ch.174 adoption). Austin separately codified a first-of-its-kind non-statutory AFSCME Local 1624 "consultation agreement" in February 2026 — the closest non-safety analogue to Houston's HOPE found among sub-threshold cities. On the Ohio side: Cleveland and Cincinnati were both found to have all four institutional tiers (police, fire, 1-2 non-safety unions) fully documented on official portals, with Cleveland's structure arguably more complete than Columbus's own; Toledo shows the richest non-safety union variety (3 AFSCME locals + Teamsters + UAW) of any city in either state; Akron remains the weakest-documented Ohio city; Dayton is moderately confirmed, correcting the prior session's overly pessimistic "no portal found" assessment.
- **Multi-city source-target CSV** (`texas_ohio_multicity_source_targets_2026-07-08.csv`): 12 rows (6 TX cities, 6 OH cities) with controlled `ingestion_recommendation` (first_batch/backup/context_only/defer/reject) and `priority` ratings.
- **Bottom-line recommendation:** first ingestion batch = **Houston + Austin (Texas), Columbus + Cleveland (Ohio)** — pairing one population-exceptional city with one representative-size city in each state. Backups: Fort Worth then San Antonio (TX); Cincinnati then Toledo (OH). Deferred, not rejected: Dallas, El Paso, Akron, Dayton.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route the multi-city scan memo and source-target table, plus all revised tables, to the PI for review.
2. If approved, begin acquisition with the recommended first batch (Houston+Austin, Columbus+Cleveland), CBAs/agreements first, budget/pay-plan documents second, impasse/award documents third.
3. Resolve smaller pre-ingestion follow-ups already flagged (HFOA-vs-HPFFA relationship; non-safety unions' occupation-class composition in Columbus/Cleveland/Cincinnati; current-version confirmation for Austin/Fort Worth/Dallas agreements) before ingestion begins.
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state.

### Notes For ChatGPT Review

- The fire/police institutional split (Ch.174 fire + Ch.142 police) recurring in Houston, Austin, AND Fort Worth is the single most important finding of this session for the project's design — it means the earlier Houston-only recommendation was not an overfitting risk in the way the task worried it might be, at least for the police/fire side; the non-safety side remains genuinely harder to generalize (Houston's Ch.146 channel is still population-unique).
- Do not treat El Paso's institutional status as independently verified — it rests on a secondary bill-analysis source only, and was added purely for breadth, not as a near-term acquisition target.
- Austin's AFSCME Local 1624 consultation agreement (Feb. 2026) is very new and not yet confirmed to produce negotiated wage text — treat it as a design question (does it even qualify as a matched non-safety source under this project's CBA verification standard?) before treating it as a confirmed acquisition target.
- No document was downloaded or stored as project data this session; every source in the new memo and CSV is a citation/URL.

---

## 2026-07-08T12:00:00-04:00 - Texas/Ohio legal follow-up resolved; Houston and Columbus confirmed as top targets; no acquisition, no data edits

**Commit:** pending in current session (`Audit Texas and Ohio source targets`)

### Current State After This Entry

- Confirmed the prior Texas/Ohio state-comparison scoping session's changes (`88e573d`, "Scope Texas and Ohio comparison") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Resolved both Texas legal follow-ups flagged in the prior session via a direct statute fetch-and-read, and reassessed Houston and Columbus as source-acquisition targets in light of what that resolution revealed.
- Created:
  - `docs/analysis/texas_ohio_legal_followup_source_audit_2026-07-08.md`
  - `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv`
- Updated (light-to-moderate touches):
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv` (Houston/Columbus rows revised in place)
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv` (2 rows resolved, 6 rows added)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (3 rows revised in place)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7B)
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** touched. No GABRIEL calls, model/API calls, or Harvard Proxy calls were made. No document was downloaded or stored as project data — two official Houston PDFs were fetched transiently by the web-research tool (both failed to extract as readable text, a tooling limitation) but were not saved into this repository. No ingestion occurred. No PRR was recommended. No causal claim was made about Texas or Ohio wage outcomes.

### What This New Package Does

- **Legal follow-up memo** (`texas_ohio_legal_followup_source_audit_2026-07-08.md`): resolves both flagged Texas questions via direct statute reads. **§174.1535 "Mandatory Arbitration"** creates true compulsory binding arbitration, but only for a fire department in a municipality of ≥1.9 million population — Houston (~2.39M) is the only qualifying Texas city, making Houston Fire the closest Texas analogue to Massachusetts's JLMC found in this project to date, though far narrower (one city, one occupation). **Chapter 146** is confirmed NOT a general local-option chapter — §146.001(a) restricts it to municipalities of ≥1.5 million population, again Houston-only among Texas cities. This reverses a prior-session assumption: Houston's non-safety employees DO have an active bargaining channel — HOPE (AFSCME Local 123) has been Houston's Chapter 146 meet-and-confer agent since 2008, ~12,000+ members, most city departments, current 2024 agreement officially hosted on a City of Houston HR page. A further discovery: Houston Fire (HPFFA, IAFF Local 341) operates under full Chapter 174 bargaining (voter-adopted 2003), not Chapter 142 as the prior session's secondary-sourced city list assumed — Houston Police remains under Chapter 142. Houston therefore now shows three distinct institutional tiers within one city. Columbus's remaining gaps are also closed: IAFF Local 67 (fire) and two non-safety unions (AFSCME Local 1632, CWA) are specifically identified, all on the same official `columbus.gov` portal, cross-checkable against a SERB-filed fact-finding report.
- **Source ingestion audit CSV** (`texas_ohio_source_ingestion_audit_2026-07-08.csv`): 19 rows of exact source targets (not downloaded documents) across Texas/Ohio statutory context, Houston's three tiers, Columbus's four contracts, and second-choice San Antonio/Cincinnati rows, each with controlled `ingestion_decision`/`priority`/`followup_needed` ratings. No row is marked `ingest_now`; most are `fetch_later` or `context_only`.
- **Candidate-target and legal-source-audit CSV revisions:** Houston's and Columbus's rows revised in place (not duplicated) to reflect this session's findings; other cities' rows untouched.
- **Report checklist Section 7B:** documents the follow-up as completed, Houston/Columbus's ingestion-readiness (ready for a source-acquisition plan, not yet for ingestion), remaining pre-report decisions, and a reaffirmed caution that Houston's population-gated findings should not be generalized to "Texas" as a whole.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route the new follow-up memo, ingestion audit CSV, and revised tables to the PI for review.
2. If approved toward acquisition, resolve the remaining small pre-ingestion items first (HFOA-vs-HPFFA relationship; Columbus AFSCME 1632/CWA occupation composition; current-version confirmation for each Houston contract) rather than jumping directly to ingestion.
3. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state.

### Notes For ChatGPT Review

- Houston's §174.1535 and Chapter 146 findings are population-gated and, on current city populations, apply to Houston alone among Texas cities — do not generalize either finding to "Texas" broadly in any future report language.
- The prior session's classification of Houston Fire as a Chapter 142 meet-and-confer city was incorrect and is corrected this session (Houston Fire is actually under full Chapter 174 bargaining); if any future session finds language still describing Houston Fire as meet-and-confer, that language is stale and should be updated.
- None of the official Houston PDFs located this session extracted as readable text through this session's web-fetch tooling — this is a tooling limitation encountered during research, not a finding about the documents' quality; use `ingest/extract_text.py` at acquisition time instead.
- No document was downloaded or stored as project data this session; every source in the new memo and CSV is a citation/URL.

---

## 2026-07-07T16:00:00-04:00 - Texas/Ohio state-comparison scoping completed (PI request); no acquisition, no data edits

**Commit:** pending in current session (`Scope Texas and Ohio comparison`)

### Current State After This Entry

- Confirmed the prior Harvard Proxy evidence-window scaffold revision session's changes (`911648f`, "Revise Harvard Proxy pilot evidence windows") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Responded to an explicit PI request (quoted in full in the new institutional-scan memo) to look beyond Massachusetts, with Texas and Ohio suggested by name, to test whether this project's safety/non-safety wage-mechanism findings depend on Massachusetts's JLMC arbitration statute specifically.
- Created:
  - `docs/analysis/texas_ohio_state_comparison_institutional_scan_2026-07-07.md`
  - `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv`
  - `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv`
  - `docs/analysis/report_addendum_state_comparison_plan_2026-07-07.md`
- Updated (light touches):
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (4 new cross-cutting rows; no existing rows changed)
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` (new Section 7A)
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** touched. No GABRIEL calls, model/API calls, or Harvard Proxy calls were made. No document was downloaded or stored — every Texas/Ohio source recorded this session is a citation/URL in a memo or CSV, not a fetched full-text file. No ingestion occurred. No PRR was recommended. No causal claim was made about Texas or Ohio wage outcomes.

### What This New Package Does

- **Institutional scan** (`texas_ohio_state_comparison_institutional_scan_2026-07-07.md`): full institutional profiles for Massachusetts (baseline), Texas, and Ohio, a comparison table, and hypothesis implications. Key Texas finding: Gov't Code Ch. 617 prohibits public-sector collective bargaining generally; police/fire get a narrow, locally-adopted carve-out (Ch. 174 full bargaining, confirmed non-compulsory arbitration per §174.163/174.153; or Ch. 142 meet-and-confer, no duty to agree) that varies city-by-city (San Antonio: Ch. 174; Austin/Dallas/Fort Worth/Houston: Ch. 142); non-safety employees generally have no bargaining channel absent a separate Ch. 146 adoption (unconfirmed per city), with Houston's non-safety wages set via civil-service classification instead. Key Ohio finding: ORC Ch. 4117 is one statewide statute for all public employees; the safety/non-safety split is internal to it — ORC 4117.14(D)(1)'s no-strike list (police, fire, and several other safety-adjacent categories including some dispatchers/nurses) routes to compulsory binding conciliation, while other public employees retain a conditional strike right instead. SERB's centralized, publicly searchable CBA/fact-finding/conciliation archive (since 2012) is a stronger centralized-records resource than anything available for this project's Massachusetts cities.
- **Candidate source-target table** (`texas_ohio_candidate_source_targets_2026-07-07.csv`): 11 rows — 5 Texas cities (Houston, San Antonio, Austin, Dallas, Fort Worth), 5 Ohio cities (Columbus, Cincinnati, Cleveland, Dayton, Akron), plus a statewide Ohio SERB-archive row — each rated on data availability, comparison value, priority, and fetch-later status. Top picks: Houston and Columbus.
- **Legal/source citation audit** (`texas_ohio_legal_source_audit_2026-07-07.csv`): 20 rows auditing specific legal claims by source type (state statute, state agency, municipal source, legal secondary) and confidence, flagging two open Texas follow-ups (§174.1535 "Mandatory Arbitration" text; Ch. 146 non-safety-adoption status per candidate city) and one Houston sourcing note (the only located Fire CBA copy is news-hosted, not an official city page — needs replacement before acquisition).
- **Report addendum plan** (`report_addendum_state_comparison_plan_2026-07-07.md`): recommends a short, clearly-labeled main-text paragraph (proposed language included) plus an appendix pointer for the existing report draft — not a full new section or Evidence Map row, since Texas/Ohio have zero corpus rows to date. States explicitly that no group/mechanism conclusion in the existing report draft changes as a result of this session.
- **Source-needs and review-checklist updates:** `all_groups_source_needs_2026-07-06.csv` gained 4 new cross-cutting rows (no existing rows touched); `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` gained a new Section 7A summarizing the PI request, the incorporation decision needed, the acquisition/citation-audit prerequisite, and a caution against implying Massachusetts is nationally representative.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route all four new files and the updated checklist to the PI for review.
2. If approved, prioritize Houston (TX) and Columbus (OH) as first acquisition targets, each requiring a matched non-safety comparison unit before satisfying this project's CBA source-verification standard.
3. Resolve the two flagged Texas legal follow-ups (§174.1535 text; Ch. 146 adoption status per city) via a short, targeted citation-audit pass before acquisition.
4. Do not begin GABRIEL, Harvard Proxy live calls, ingestion, or any OEWS/BLS build from this state.

### Notes For ChatGPT Review

- This session is explicitly scoping/source-planning only — no Texas or Ohio document was collected, fetched in full, or stored; every source in the new CSVs is a citation/URL.
- Do not cite any Texas or Ohio institutional claim in this session's memos as more confident than the companion legal-source-audit CSV's own `current_confidence`/`needs_followup` columns indicate — several claims (Ch. 142/146 details, Dallas/Fort Worth meet-and-confer status, Cleveland's/Cincinnati's exact non-safety unit composition) rest on web-search synthesis, not a directly-fetched-and-read primary statute, and are flagged as such.
- Do not treat Texas and Ohio as representative states, and do not extend any Massachusetts-corpus-based report conclusion to either state based on this session's institutional-law work alone.
- The Houston Fire CBA copy located this session (interactive.khou.com) is news-hosted, not an official city source — replace with an official houstontx.gov copy before any future acquisition, per this project's preferred-source-family guidance.

---

## 2026-07-07T12:00:00-04:00 - Harvard Proxy pilot scaffold revised to use corpus evidence windows

**Commit:** pending in current session (`Revise Harvard Proxy pilot evidence windows`)

### Current State After This Entry

- Confirmed the prior Harvard Proxy calling-scaffold session's changes (`dd94c1b`, "Add Harvard Proxy pilot scaffold") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md`
- Rewrote:
  - `scripts/proxy_pilot_must_have_sources.py`
- Updated:
  - `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md`
  - `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified — evidence-window construction only reads already-collected corpus files. No GABRIEL calls, model/API calls, or Harvard-proxy calls were made. No secret, key, or `.env` content was printed, inspected, or committed.

### What This New Package Does

- **Diagnosed a genuine gap in the prior scaffold:** it built prompts from a single `data/contracts.csv` metadata field (`total_comp_note` — an RA-written administrative summary), not the corpus document's own text, which is insufficient for source-need questions that depend on a document's body content (dispatcher staffing rules, custodial wage classifications, sanitation/transfer-station language). See `harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md` for the full diagnosis.
- **Rewrote `scripts/proxy_pilot_must_have_sources.py`** to build dry-run (and any future live) prompts from bounded **corpus evidence windows**: for each selected row, the script resolves its `full_text_path`, extracts text via this project's existing `ingest/extract_text.py` utility (text-layer-first, local OCR fallback — no network access), searches for a curated list of target terms, and builds ~200-char-before/after windows around each match. A new `evidence_windows.csv` output records every window; `prompt_preview.md` now embeds these windows, not a metadata snippet.
- **Added named pilot sets** via `--pilot-set`: `must_have` (default, 4 rows — Arlington dispatcher, Franklin custodial, Seekonk sanitation, Wayland nurse_health/dispatch), `dispatch_custodial` (2 rows), `sanitation_seekonk` (1 row), `custodial_only` (Franklin + Georgetown, 2 rows). Added `--contract-id` plus optional `--terms` for one-off exploratory dry-runs against any row not yet in a named set.
- **Live mode now skips any row with zero evidence windows** (logged as `skipped_no_evidence`) rather than sending an empty or near-empty prompt to the proxy.
- **All safety properties from the prior session are unchanged:** dry-run remains the default; `--live` still requires an explicit `--limit` of 1-3 (refuses otherwise, before creating any output or reading any credential — re-tested and confirmed this session); the subscription key is still read only inside the live-call function.
- **Dry-run tests confirmed the fix works:** ran `--pilot-set dispatch_custodial --limit 2` (15 evidence windows each for Arlington/Franklin), `--pilot-set sanitation_seekonk --limit 1` (5 windows for Seekonk), `--pilot-set must_have --limit 4` (all 4 rows, including a successful local OCR fallback for Wayland's `ocr_messy` file — 15 windows found), and `--contract-id ma_georgetown_other_2020 --terms ...` (9 windows). Directly inspected the outputs and confirmed real, verbatim corpus text is embedded in `prompt_preview.md` — for Arlington, confirmed the specific multi-word terms ("Lead Dispatcher," "complement," "EMD") successfully surfaced the substantive Article XXI staffing-complement and EMD-stipend content, while noting (as a documented, not hidden, limitation) that a few generic single-word terms were consumed by earlier table-of-contents matches first.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. A user/PI should review the newest dry-run's `evidence_windows.csv` and `prompt_preview.md` for each pilot set of interest before any live pilot is considered.
2. If evidence windows are confirmed relevant, a live pilot should proceed at 1-2 calls (not the full 3-call ceiling) until the response-parsing logic is reviewed against the prompt's requested schema.
3. Do not run `--live` from any future session without explicit, out-of-band approval.

### Notes For ChatGPT Review

- Do not treat `selected_rows.csv`'s absence of a model-answer column as a bug — dry-run mode never calls the proxy, so there is no model output to record; this is intentional and documented in the revision memo §3.
- An empty `evidence_windows.csv` entry for a given row is a real, meaningful signal (the curated search terms found nothing), not proof the underlying document lacks relevant content — see the revision memo §6 for this precision-over-recall caveat before treating any zero-match row as a settled finding.
- The Wayland row (`ma_wayland_other_2021`) requires local OCR via `ingest/extract_text.py` and is the slowest row in the `must_have` pilot set to build evidence windows for; this is expected and was tested successfully this session.
- No secret, key, or `.env` content was printed, inspected, or committed at any point in this session.

---

## 2026-07-07T08:00:00-04:00 - Harvard Proxy calling-scaffold and dry-run safety review completed

**Commit:** pending in current session (`Add Harvard Proxy pilot scaffold`)

### Current State After This Entry

- Confirmed the prior PI-facing report planning session's changes (`aa13fa5`, "Draft safety and non-safety wage mechanisms report") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md`
  - `scripts/proxy_pilot_must_have_sources.py`
  - `docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. **No GABRIEL run occurred. No live model/API/Harvard-proxy call occurred — only a genuine dry-run (no-network-call) mode was exercised.** No secret, key, or `.env` content was printed, inspected, or committed at any point in this session.

### What This New Package Does

- **Calling-scaffold review** (`harvard_proxy_calling_scaffold_review_2026-07-06.md`): inventories every existing script/doc referencing the Harvard proxy, OpenAI, or GABRIEL (`analysis/gabriel_pilot/run_gabriel.py`, `run_gabriel_v9.py`, `run_gabriel_v10_gold_dryrun.py`, the built-in-web-search smoke/demo/diagnostic scripts, `ingest/extract_spans.py`'s `llm_pass()`, `scripts/log_api_spend.py`). Key finding: **no existing script has a genuine no-network-call dry-run mode**, and none enforces a row-count ceiling on live calls — one script's name (`run_gabriel_v10_gold_dryrun.py`) is misleading, since it still makes live calls despite the "dryrun" filename (it means "bounded to an 11-row gold set," not "no API call").
- **Pilot scaffold** (`scripts/proxy_pilot_must_have_sources.py`): a new, safety-first harness closing both gaps identified above. Defaults to dry-run with zero network calls and zero credential reads. Requires `--live` plus an explicit `--limit` of 1-3 for any real call (refuses immediately, before any output directory is created, if `--limit` is missing or exceeds 3). Reads `HARVARD_SUBSCRIPTION_KEY` only inside the live-call function, never at import time. Writes every run to a fresh, timestamped `tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/` directory (refusing to overwrite a prior run), with `run_config.json`, `selected_rows.csv`, and `prompt_preview.md` written in every mode, and `responses.jsonl`/`parsed_outputs.csv`/`live_run_log.txt` written only in live mode. The hardcoded pilot set ties directly to the still-open Seekonk sanitation Appendix/job-description "must-have" item from the prior all-groups source-needs audit, plus two calibration examples (Arlington dispatcher wage detail, Wayland nurse_health credential detail).
- **Usage doc** (`harvard_proxy_pilot_usage_2026-07-06.md`): dry-run command examples; live command examples explicitly marked "do not run unless explicitly approved"; an expected-outputs table; a pre-live-run safety checklist; how to inspect outputs without ever printing `.env`/secrets; how not to commit `tmp/` pilot outputs; how to choose future pilot rows.
- **Tested directly this session:** `python scripts/proxy_pilot_must_have_sources.py --dry-run --limit 2` ran successfully and confirmed (in its own log) that no network call was made and no key was read. Also directly confirmed `--live` with no `--limit`, and `--live --limit 5`, both refuse immediately with no output directory created — the safety gates were verified to work before any live call was ever attempted.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. If the user/PI wants to test this scaffold against a real Harvard Proxy call, the recommended next step is an explicitly approved live pilot of at most 1-3 calls, starting with the Seekonk sanitation Appendix/job-description confirmation.
2. Do not run `--live` from any future session without that explicit, out-of-band approval.
3. Do not begin any broader GABRIEL run, OEWS/municipal descriptive baseline build, or production extraction run from this state.

### Notes For ChatGPT Review

- This scaffold is deliberately narrow (3-row live ceiling, hardcoded pilot set drawing only from already-collected `data/contracts.csv` fields) — it is not a general-purpose GABRIEL replacement and should not be extended to a larger row count or a different attribute without a fresh review.
- Do not treat any output this scaffold produces (even from a future approved live run) as production data — its `parsed_outputs.csv` is explicitly a pilot artifact, not a validated corpus finding, and should not be used to edit `data/contracts.csv` directly.
- The subscription key is read only inside `_run_live()` in the new script — if extending this scaffold in the future, preserve that discipline rather than reading the key at module load time.
- No secret, key, or `.env` content was printed, inspected, or committed at any point in this session.

---

## 2026-07-07T04:00:00-04:00 - PI-facing report outline, draft, review checklist, and production plan created

**Commit:** pending in current session (`Draft safety and non-safety wage mechanisms report`)

### Current State After This Entry

- Confirmed the prior pre-report must-have evidence review session's changes (`016711c`, "Review must-have evidence before report") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/report_outline_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_draft_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`
  - `docs/analysis/report_production_plan_safety_non_safety_wage_mechanisms_2026-07-06.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added. **No PDF, DOCX, PPTX, or other final-formatted artifact was created** — this run produced a markdown draft and supporting planning files only, per the task's explicit scope boundary.

### What This New Package Does

- **Report outline and claims map** (`report_outline_...md`): a detailed pre-draft planning document covering the title block, intended audience/purpose, a section-by-section breakdown (purpose, key claims, evidence basis, caveats, tables/callouts, and what-not-to-overclaim for each of the report's 8 sections), a report-level claim hierarchy (central / supporting / caveats / source-design findings / deferred), recommended tables and callouts, and 5 explicitly flagged open decisions for the PI (custodial/facilities naming, dispatcher prominence, transit's space allocation, nurse_health's placement, appendix sizing).
- **Report draft** (`report_draft_...md`): the full PI-facing markdown draft, using the exact specified title/subtitle. Contains an Executive Summary (4 paragraphs), 8 Main Takeaways, an 11-row Evidence Map table, Group-by-Group Findings for all 11 groups (police, fire, teachers, DPW, clerical/admin, library, custodial/facilities, dispatchers, nurse_health, sanitation, transit — each with status/mechanisms/evidence-basis/MA-notes/national-caveat/source-needs), a Mechanism-by-Mechanism Synthesis across all 13 specified mechanisms, a Massachusetts and National Nuance section naming the three distinct MA wage-impasse regimes now identified (JLMC, ordinary Chapter 150E, and the MBTA's own M.G.L. c. 161A statute), a tiered (must-have/useful/optional-deferred) Source Needs section, and 4 appendix tables.
- **Central narrative preserved:** the draft states directly that the key distinction is not "safety is hard, non-safety is easy" but "police/fire combine real upward pressure with a stronger pressure-to-wage conversion institution (JLMC), while non-safety groups' real pressures translate through classification systems, buffering, outsourcing, governance distance, budget constraints, or a weaker impasse pathway."
- **Review checklist** (`report_review_checklist_...md`): flags claims needing PI review (the central-finding framing, group-retention labels, custodial/facilities completeness claim, the Iowa counterexample's prominence), claims needing source strengthening before a final version (the dispatcher wage-tier comparison, nurse_health's single-city generalizability, sanitation's unconfirmed signals, transit's single-data-point finding), open formatting decisions, tables that may be too large, sections that may need tightening, 5 suggested PI questions, and an artifact-generation readiness checklist.
- **Production plan** (`report_production_plan_...md`): recommends DOCX first, then PDF; explains how to apply the Georgia/11pt/charcoal-heading/Harvard-crimson-accent style guide; allocates which tables belong in main text vs. appendix; proposes filename conventions; explains how to preserve file-name citations for auditability; and states explicitly what not to do (no new corpus rows, no OEWS build, no PRRs, no GABRIEL restart) until source acquisition is separately approved.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Route the report draft and review checklist to the user/PI for review.
2. Once PI feedback is incorporated, proceed to a dedicated formatting run (DOCX first, then PDF) per the production plan.
3. Do not begin any new source-acquisition run, OEWS/municipal descriptive baseline build, or GABRIEL work from this state.

### Notes For ChatGPT Review

- This report draft is explicitly not a final, causal-evidence document — every claim in it is graded as current-corpus evidence, external/national context, or an identified source need, and the draft's own language ("current corpus shows," "evidence suggests," "requires additional sourcing") should be preserved in any future edit rather than tightened into unhedged assertions.
- Do not generate any PDF, DOCX, or PPTX from this draft without first routing it through PI review per the review checklist — the task explicitly deferred artifact generation to a later run.
- The group-retention frame used in this draft (central/strong comparison/public-safety-adjacent/secondary/source-design case/deferred) was supplied as a fixed input for this run; any future revision to that frame should originate from PI feedback, not from a future session's own re-derivation.
- Every claim in the draft traces to an already-existing session memo or CSV; no new corpus review or web research occurred this session.

---

## 2026-07-07T01:00:00-04:00 - Dispatchers, custodial/facilities, and nurse_health confirmed via direct corpus re-reads

**Commit:** pending in current session (`Review must-have evidence before report`)

### Current State After This Entry

- Confirmed the prior all-groups audit session's changes (`c111829`, "Audit wage mechanisms across groups") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.md`
  - `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.csv`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (Section 11 rows NH01/CF01/CF02/DP-D01/DP-D02/DP-D03 upgraded from `not searched`/assumed to `confirmed in current corpus`; intro and Section 14 updated)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv` (5 rows updated to `current_corpus`; no rows added/deleted)
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv` (4 new rows appended, H40-H43, previously missing from this table)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified — a bounded OCR pass on Wayland's already-collected CBA was performed entirely under `/tmp/`, never written back. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a verification/confirmation pass, not a new mechanism-development session — every finding traces to already-collected corpus text.

### What This New Package Does

- **Arlington dispatchers, confirmed.** Direct re-read of `ma_arlington_public_works_2015` found a dedicated Article XXI ("Community Safety Dispatchers"): 9-person complement plus Lead Dispatcher, minimum-coverage-of-two rule, EMD stipend, and a requirement that dispatcher vacations be approved by "the Chief of Fire or Police." No per-classification base-wage table exists in this CBA (only unit-wide % increases; actual rates live in an external Classification and Pay Plan document not in this project's corpus). `binding_arbitration_statute` confirmed as MA G.L. c. 150E, not JLMC.
- **Custodial/facilities, confirmed.** Georgetown's and Franklin's custodial CBAs both contain complete, multi-step salary schedules with genuine classification tiers — Georgetown's Licensed-vs-Unlicensed Maintenance pay differential (~11%) directly parallels DPW's CDL/hoisting-license findings. Arlington adds supplementary bundled evidence.
- **Wayland nurse_health/dispatch, confirmed via a bounded OCR pass.** A 48-page, previously cover-page-only-readable scan was fully OCR'd (2,186 lines). Found substantive, dollar-figure wage-grade tables for both Community Health Nurses/Public Health Nurse (G-15/G-7A) and JCC Dispatcher/Coordinator (G-3/G-4), a Masters-degree nursing stipend, and a documented wage-restraint finding (nurse wages excluded from a 2022 compensation study). No custodial content exists in this document. The unit spans at least 9 distinct professional fields — far more fragmented than its name suggests.
- **Group-retention recommendations upgraded:** dispatchers → `keep_public_safety_adjacent` (confirmed); custodial/facilities → `keep_strong_comparison` (confirmed, schema-blocked only administratively); nurse_health → `keep_secondary` (upgraded from `defer`; substantive but single-city/fragmented-unit).

### Checklist, Roadmap, Source-Needs, and Hypothesis-Disposition Updates

- `wage_mechanism_evidence_checklist.md` Section 11's six rows (NH01, CF01, CF02, DP-D01, DP-D02, DP-D03) all moved from `not searched`/assumed to `confirmed in current corpus`, with full evidentiary detail.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the confirmations and the recommended move to PI-facing report planning.
- `all_groups_source_needs_2026-07-06.csv`: 5 rows updated from `partial`/`absent` to `current_corpus` (Arlington dispatcher text, Wayland OCR ×2, Georgetown/Franklin custodial full-text, Arlington/Wayland `binding_arbitration_statute` check); no rows added or deleted.
- `hypothesis_disposition_audit_2026-07-06.csv`: H40-H43 appended (they existed in the hypothesis matrix since the prior session but had never been dispositioned in this table) — H41 (custodial outsourcing) and H42 (dispatch coverage pressure) now `keep_central`/`strong_current_corpus`; H40 (nurse_health) and H43 (dispatch civilian-status undertranslation) `keep_supporting`/`moderate_current_corpus`.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Move to PI-facing report outline/planning, using the updated group-retention table (`pre_report_must_have_evidence_review_2026-07-06.md` §6) as the current state of record.
2. Bring the `custodial`/`facilities` schema decision to the user/PI in parallel with report planning, not as a blocking prerequisite.
3. No further OCR or re-extraction pass is needed for any of the three documents reviewed this session.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Do not re-request an OCR pass on `ma_wayland_afscme_1_2_2020_2023.pdf` — this session's extraction is complete (2,186 lines) and sufficient; the temporary OCR files exist only under `/tmp/` and are not part of this repository.
- Do not treat Arlington's dispatcher evidence as including a base-wage comparison to police/fire — no per-classification dollar table exists in this specific CBA; that comparison remains open (see H43's evidence_status).
- Do not treat nurse_health as a strong, headline comparison group — the evidence is genuinely substantive but rests on one city inside an unusually fragmented, nine-profession bargaining unit; report it as a secondary finding with that composition caveat stated explicitly.
- The `custodial`/`facilities` occupation_class schema decision remains open and is a user/PI action item, not something this or any prior session has authority to resolve by editing `data/contracts.csv`.

---

## 2026-07-06T22:00:00-04:00 - All groups scoped and audited; next-stage synthesis inputs prepared

**Commit:** pending in current session (`Audit wage mechanisms across groups`)

### Current State After This Entry

- Confirmed the prior transit governance-fit session's changes (`cf6e32b`, "Scope transit governance and wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_remaining_groups_scope_2026-07-06.md`
  - `docs/analysis/non_safety_remaining_groups_source_gaps_2026-07-06.md`
  - `docs/analysis/all_groups_wage_mechanism_audit_2026-07-06.md`
  - `docs/analysis/all_groups_source_needs_2026-07-06.csv`
  - `docs/analysis/hypothesis_disposition_audit_2026-07-06.csv`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 11 for nurse_health/custodial/dispatchers, 7 rows; Sections 12-16 renumbered; Purpose section updated with pointers to the 3 new synthesis files; Section 14 gained 2 new corpus-evidence-summary bullets)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H40-H43)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (2 new forward-looking rows; 1 existing row's notes extended; no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- **This is not the final PI-facing report.** This session prepared the audit and recommendations (`all_groups_wage_mechanism_audit_2026-07-06.md`, `all_groups_source_needs_2026-07-06.csv`, `hypothesis_disposition_audit_2026-07-06.csv`) that will feed a later report whose format is decided separately.

### What This New Package Does

- **Scopes the three remaining ambiguous non-safety groups** (nurse_health/public health, custodial/facilities, dispatchers) with a full corpus-coverage check, Massachusetts/national context, and per-group recommendations. The most consequential finding: a direct re-read of already-collected corpus text (no new ingestion) found genuine hidden/bundled content for all three groups on the first scoping pass — `ma_wayland_other_2021` (coded `other`) names "nurses" and "dispatch" in its own metadata; a `pdftotext` re-read of Arlington's already-collected `public_works` CBA confirmed explicit "Community Safety Dispatchers" language (9-person complement, minimum-coverage-of-two rule); `ma_georgetown_other_2020`/`ma_franklin_other_2022` are confirmed custodial units mislabeled `other` for lack of a controlled-vocabulary value.
- **Recommendations:** nurse_health — defer (thinnest corpus foothold, sharpest population-mismatch risk vs. national hospital-nursing data); custodial/facilities — include, pending a `custodial`/`facilities` schema decision; dispatchers — include as a distinct **public-safety-adjacent** category (neither ordinary non-safety nor safety-equivalent), contingent on a full re-read of the Arlington text and independent verification of the dispatcher-bearing rows' `binding_arbitration_statute` field (not yet assumed by extension).
- **Audits all 11 groups examined to date** (police, fire, teachers, DPW, clerical/admin, library, sanitation, transit, nurse_health, custodial/facilities, dispatchers) across mechanism strength, evidence basis, design fit, source needs, and national/Massachusetts nuance, plus a 20-row mechanism-by-mechanism table.
- **Recommended narrative:** police/fire combine multiple genuine upward-pressure mechanisms (recruitment strain, overtime spirals, hazard/credentialing, political salience) with a strong, direct translation institution (JLMC). Every other group faces real pressures of its own — DPW's water/wastewater retirement wave, sanitation's fatal-injury-rate comparison, teachers' documented shortage, dispatchers' own 24/7 minimum-staffing rule — but these translate through classification/reclassification systems, staffing substitution, service buffering, contractor/governance distance (transit, sanitation for a majority of cities), or civilian-status classification (dispatchers), not through a comparable direct institutional backstop.
- **Dispositions all 39 hypothesis-matrix rows** (14 keep_central, 12 keep_supporting, 3 merge — H3/H12 as a compensating-differentials pair — 4 demote, 3 defer, 0 drop_for_now) in `hypothesis_disposition_audit_2026-07-06.csv`.
- **Structures 44 source-target rows** by priority (must_have/useful/optional/defer) across all groups in `all_groups_source_needs_2026-07-06.csv`, with no source fetched or ingested.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 11 ("Nurse_health, custodial/facilities, and dispatcher mechanisms checklist," 7 rows: NH01-NH02, CF01-CF02, DP-D01-DP-D03), with Sections 12-16 renumbered from the prior 11-15; the Purpose section now points to the 3 new all-groups synthesis files; Section 14 (corpus evidence summary) gained bullets for transit and for the 3 remaining groups.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the scoping/audit/source-needs work and its recommended next steps.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv`: 4 new rows appended (H40-H43: `nurse_health_professional_labor_market_pressure`, `custodial_facilities_outsourcing_and_service_buffering`, `dispatch_public_safety_adjacent_coverage_pressure`, `dispatch_civilian_status_undertranslation`), via the same surgical append-only technique validated in prior sessions. Existing 39 rows confirmed unchanged (`git diff --numstat`: 4 insertions, 0 deletions).
- `police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv`: 2 new forward-looking rows (`custodial_facilities` → Janitors and Cleaners SOC 37-2011; `dispatchers` → Public Safety Telecommunicators SOC 43-5031), both explicitly flagged as not-yet-controlled-vocabulary `project_occupation_class` values; 1 existing `nurse_health` row's notes extended. No OEWS data build.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Close the "must-have" zero-cost, already-in-corpus items: full re-read of Arlington's dispatcher text for wage/step data; OCR re-extraction of `ma_wayland_afscme_1_2_2020_2023.pdf`; full-text re-read of the two already-collected custodial CBAs (Georgetown, Franklin).
2. Bring the `custodial`/`facilities` controlled-vocabulary schema decision to the user/PI.
3. Prepare the PI-facing report next (format TBD, decided separately), using this session's audit/source-needs/hypothesis-disposition files as direct inputs — do not run a broader new source-acquisition plan first.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- This session is explicitly **not** the final PI-facing report — it prepares the audit and recommendations that will feed one; do not treat any file created this session as report-ready prose without further editorial work.
- Do not assume dispatchers are Chapter 150E-covered by extension the way sanitation's institutional finding was (SN09) — this was explicitly flagged as an open, not-yet-independently-verified question for the two dispatcher-bearing rows (Arlington, Wayland).
- Do not cite the nurse_health, custodial/facilities, or dispatcher findings as "confirmed in current corpus" beyond the specific already-collected-text findings described above (Arlington's dispatcher language; Georgetown's/Franklin's custodial metadata) — every other claim for these three groups is either external context or an unread/unOCR'd fragment.
- This project's corpus still holds zero `nurse_health` rows and no `custodial`/`dispatcher`-classified rows at all (schema gap); nothing in this session changed that.

---

## 2026-07-06T18:00:00-04:00 - Transit governance and wage mechanisms scoped; deferred as governance-mismatched

**Commit:** pending in current session (`Scope transit governance and wage mechanisms`)

### Current State After This Entry

- Confirmed the prior Seekonk public works sanitation-language scan (`7bc8776`, "Scan Seekonk public works sanitation language") was already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_transit_governance_mechanism_scope_2026-07-06.md`
  - `docs/analysis/non_safety_transit_governance_scan_2026-07-06.csv`
  - `docs/analysis/non_safety_transit_source_gaps_2026-07-06.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 10, "Transit mechanisms checklist," 9 rows TR01-TR09; Sections 11-15 renumbered; XC09 cross-referenced)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H36-H39)
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` (one small annotation to the existing `transit` row's `notes` field; no new row, no data build)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a governance-fit assessment and mechanism-scoping session, not a corpus-build, source-acquisition, or GABRIEL session — it resolves the transit scoping decision left open since `wage_mechanism_project_checkpoint_2026-07-05.md` §11 (item 2).

### What This New Package Does

- Confirms zero `transit` rows exist in `data/contracts.csv` or `data/city_coverage.csv`, and confirms (via a full-field keyword search) that no existing row contains genuine transit-, bus-, transport-, traffic-, or parking-related content.
- **Classifies all nine current project cities' transit governance via bounded web research:** four (Arlington, Boston, Newton, Somerville) fall under the MBTA (a Massachusetts state authority, M.G.L. c. 161A); five (Franklin, Georgetown, Seekonk, Wayland, Worcester) fall under a regional transit authority (GATRA, MeVa/MVRTA, MWRTA, WRTA respectively), with Seekonk uniquely also served by Rhode Island's RIPTA. **Zero `city_operated_transit` cases were found.**
- **Most consequential finding:** Massachusetts RTAs are required by M.G.L. c. 161B to contract actual operations to a private operating company — directly confirmed for Worcester, where WRTA's unionized (ATU Local 22) bus operators are employed by First Transit, Inc./Central Mass Transit Management (CMTM), not WRTA or the City of Worcester. This is a structurally deeper, state-law-mandated version of sanitation's private-hauler finding, applying uniformly across all five RTA-served cities rather than as a city-level choice.
- **A genuinely new institutional finding:** the MBTA has its own compulsory interest-arbitration statute (M.G.L. c. 161A §§19C-19G), distinct from both JLMC (police/fire) and Chapter 150E §9 (teachers/DPW/clerical-admin/library/sanitation-by-extension) — a third Massachusetts arbitration regime this project had not previously catalogued, though it governs the MBTA's own employees as a state authority, not any of this project's nine city governments.
- **Sharpest quantified wage-to-staffing finding in this project to date, for any occupation:** the MBTA's 2024 bus-operator starting-pay raise ($22.21 to $30/hour) was followed by a reported 365% surge in operator applications — a state-authority-specific data point, not yet shown to generalize to any RTA or a smaller wage adjustment.
- **Governance-fit conclusion:** transit does not fit this project's city-level matched-CBA design, for all nine current cities without exception. Recommends deferring transit indefinitely as governance-mismatched, rather than developing it as a fifth non-safety comparison group.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 10 ("Transit mechanisms checklist," 9 rows: TR01-TR09, explicitly marked as scoping-stage since zero corpus rows exist), with Sections 11-15 renumbered from the prior 10-14; XC09 (arbitration/impasse backstop) cross-referenced with the new MBTA c. 161A finding.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming transit's governance-fit scoping is complete and recommending deferral.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H36-H39: `transit_route_service_coverage_pressure`, `transit_operator_shortage_and_missed_service`, `transit_contracting_governance_distance`, `transit_service_cut_buffering`); the existing 35 rows were not touched (confirmed via `git diff --numstat`: 4 insertions, 0 deletions).
- `police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv` gained one small annotation to the existing `transit` row's `notes` field only (confirmed via `git diff --numstat`: 1 insertion, 1 deletion — a single-cell edit); no new row, no OEWS data build.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Defer transit indefinitely as governance-mismatched; do not pursue targeted transit source acquisition as this project's next comparison-group development step.
2. If a future, explicitly non-matched-city institutional case study is ever wanted, the MBTA's ATU Local 589 CBA/c. 161A arbitration history and WRTA's CMTM/ATU Local 22 arrangement are the two most information-rich targets identified — each requires its own explicit authorization before any acquisition.
3. Move to the checkpoint memo's other still-open scoping decisions (nurse_health's population mismatch; custodial/facilities and dispatcher schema questions) or a broader non-safety source-acquisition-gap review next, per user/PI direction.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Every transit finding in this session is bounded public-source desk research classifying governance *structure*, not a corpus-confirmed wage mechanism — do not cite any finding as "confirmed in current corpus" (this project's corpus holds zero `transit` rows).
- Do not conflate the MBTA's c. 161A compulsory-arbitration finding with this project's central JLMC-vs-Chapter-150E police/fire-vs-non-safety-municipal-employee finding — c. 161A governs a state authority's own employees, not any of this project's city governments, and does not change that central finding.
- Do not treat WRTA's CMTM/First Transit arrangement as evidence about GATRA, MeVa, or MWRTA specifically — the private-operator model was directly confirmed only for WRTA this session; its extension to the other three RTAs is a reasonable inference from the general M.G.L. c. 161B requirement, not an independently verified fact for each.
- Do not treat the MBTA's 2024 wage-raise-then-hiring-surge finding as evidence about any of this project's nine city governments — it describes the MBTA's own workforce as a state authority.
- This project's corpus still holds zero `transit` rows; nothing in this session changed that, and this session's governance-fit conclusion recommends against pursuing acquisition that would change it under the current design.

---

## 2026-07-06T15:30:00-04:00 - Seekonk public works CBA sanitation language scan completed

**Commit:** pending in current session (`Scan Seekonk public works sanitation language`)

### Current State After This Entry

- Confirmed the prior sanitation service-structure scan's changes (immediately prior, same date) were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.md`
  - `docs/analysis/seekonk_public_works_sanitation_language_scan_2026-07-06.csv`
- Updated:
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (light: 2026-07-06 update note to gap item 2)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (light: SN08 row update)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new 2026-07-06 update block)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a bounded, existing-corpus inspection session: read the already-collected Seekonk public works CBA in full (PDF text extraction, 675 lines), searched systematically for sanitation-related language, and classified the evidence.

### What This New Package Does

- Inspects the already-collected `ma_seekonk_public_works_2023` CBA full text for explicit and bundled sanitation/solid-waste language, the zero-cost next step recommended by the prior city-service-structure scan.
- **Finding: `sanitation_possible_but_unconfirmed`.** Zero explicit sanitation terminology found anywhere in the document. Two substantive-but-unconfirmed signals: (1) "Transfer Station" explicitly named in the hours-of-work section with different scheduling (any consecutive 5 days excluding Sunday), but no linked job title or duty description; (2) CDL training reimbursement mentioned for "eligible employees," consistent with truck-operation roles, but not explicitly sanitation-linked.
- **Remaining uncertainties:** whether the PDF's text extraction captured all Appendices and job-description Schedules (direct re-opening of the original PDF recommended); whether Seekonk's town operates its own curbside collection or contracts it out (marked "mixed/unclear" in the prior city-service-structure scan); and whether Transfer Station/CDL language together suffice to classify sanitation work as present in the unit.
- **Recommended integration:** combine this contract-inspection finding with Seekonk's service-delivery-structure verification to reach a final determination on whether Seekonk should be treated as a `sanitation_dpw_bundled` site (if municipal-staffed and Appendix-confirmed) or remain unresolved.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Confirm whether the original Seekonk public works PDF contains a job-description Appendix/Schedule that text-extraction may have missed.
2. If Appendix exists, integrate with Seekonk's service-structure determination to classify the row as sanitation-relevant or not.
3. Do not authorize Worcester or Somerville acquisition efforts as immediate follow-ons.

### Notes For ChatGPT Review

- This is an existing-corpus inspection only; no new document was acquired or ingested.
- `data/contracts.csv` was **not** edited — the Seekonk row remains as-is, classified as "possible but unconfirmed."
- Do not cite Transfer Station or CDL language as confirmed sanitation work until Appendix/service-structure questions are resolved.

---

## 2026-07-06T14:00:00-04:00 - Sanitation service structure mapped across current project cities

**Commit:** pending in current session (`Map sanitation service structure`)

### Current State After This Entry

- Confirmed the prior sanitation-scoping session's changes (`136fc29`, "Scope sanitation wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.md`
  - `docs/analysis/sanitation_city_service_structure_scan_2026-07-06.csv`
- Updated:
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md` (light: scan-completed note; gap item 2 closed)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (light: Section 9 scan-completed note)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (surgical single-cell extensions to H33 and H35 only; 35 rows/12 columns otherwise unchanged)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` and `data/city_coverage.csv` were NOT edited.** `corpus/` and `inbox/` were **not** modified. No GABRIEL calls, model/API calls, or Harvard proxy calls were made. No OEWS/BLS data was downloaded or processed. No ingestion happened, and no new corpus row was added.
- This was a bounded, public-source desk-research session classifying residential sanitation service structure (municipal / private-contractor / regional / mixed / DPW-bundled) for this project's 9 current cities — not a corpus-build, ingestion, or GABRIEL session.

### What This New Package Does

- Classifies all 9 current project cities (Arlington, Boston, Franklin, Georgetown, Newton, Seekonk, Somerville, Wayland, Worcester) into a controlled `preliminary_service_structure` vocabulary using each city's own trash/DPW/procurement web pages and (for Newton) regional news coverage.
- **5 of 9 cities (Arlington, Boston, Franklin, Georgetown, Newton) show clear private-hauler contracting** for residential collection — meaning sanitation workers there are structurally unlikely to appear in any municipal CBA this project could collect.
- **Seekonk, Wayland, and Worcester show a DPW-bundled/mixed structure**, where collection duties are plausibly folded into existing `public_works` job descriptions rather than organized as a distinct title.
- **Somerville is `dpw_bundled_unclear`** (lower confidence) — it has zero `public_works` rows in this project's corpus and is independently one of the three cities on this project's longstanding unmatched-safety-unit list.
- **Most consequential new finding:** a July 2025 Republic Services/Teamsters strike hit Newton and 13 other Boston-area suburbs simultaneously, confirming that private-hauler workforces can be unionized, but typically as multi-city, private-sector bargaining units — a genuine design-fit problem for this project's one-city-one-municipal-bargaining-unit comparison logic, not merely a data-availability inconvenience.
- **Two concrete, ranked future source targets:** (1) Seekonk — a zero-cost re-read of the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content, since the town's Pay-As-You-Throw program is run by the same DPW; (2) Worcester — a higher-effort new-source-identification target, since the existing `ma_worcester_public_works_2017` row is confirmed clerical-only ("DPW Clerks"), leaving Worcester's actual field/operations DPW workforce entirely unrepresented. Somerville is a third, lower-confidence lead. The other 5 cities are explicitly **not** recommended as near-term acquisition targets.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` Section 9 gained one scan-completed note pointing to SN08/H35 (`sanitation_dpw_bundling`) and SN06/H33 (`sanitation_contractor_substitution`). Not rewritten.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block summarizing the scan and its recommended next steps.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv`: H33 (`sanitation_contractor_substitution`) and H35 (`sanitation_dpw_bundling`) had their `non_safety_relevance_or_counterpoint` fields extended with this session's city-specific findings, via exact-string surgical edits (not a full-file rewrite, to preserve the file's legacy quoting convention). No new rows; 35 rows/12 columns confirmed unchanged.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Re-read the already-collected `ma_seekonk_public_works_2023` CBA's job-description text (not just titles) for collection-duty content — zero-cost, no new ingestion required.
2. Treat a Worcester field/operations-DPW source-identification effort, and a broader Somerville DPW/general-government source-acquisition effort, as separate future tasks requiring their own explicit authorization — not a default next step from this state.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a five-city web pilot as the immediate next step from this state.

### Notes For ChatGPT Review

- Every finding in this scan is bounded public-source desk research classifying service *structure*, not a corpus-confirmed wage mechanism — do not cite any city's classification as "confirmed in current corpus."
- Do not treat Worcester's or Somerville's source-identification leads as authorized acquisition tasks; both are flagged as needing a separate, explicit go-ahead given their higher effort/lower-confidence profile relative to Seekonk's zero-cost re-read.
- Do not treat the Newton/Republic-Services private-hauler strike finding as evidence of a wage *mechanism* result — it is a design-fit observation (multi-city bargaining units do not fit this project's one-city-one-unit comparison logic), not a measured wage outcome.
- This project's corpus still holds zero `sanitation` rows; nothing in this session changed that.

---

## 2026-07-06T10:00:00-04:00 - Sanitation / solid waste wage mechanisms scoped

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior library-mechanism-and-corpus-scan session's changes (`6397378`, "Inspect library wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_sanitation_solid_waste_mechanism_scope_2026-07-05.md`
  - `docs/analysis/non_safety_sanitation_solid_waste_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 9, "Sanitation / solid waste mechanisms checklist," 9 rows; Sections 10-14 renumbered; XC09 extended by structural inference to a sixth non-safety group)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H32-H35)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was NOT edited** — zero `sanitation` rows exist, and no correction was identified in any `public_works`/`other` row's metadata.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. No new corpus row was added. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was a **scoping and source-planning session**, not a corpus-scan session — this project's corpus holds zero `sanitation` rows, a materially different starting point than teachers, DPW, clerical/admin, or library, all of which had at least some corpus text to work from.

### What This New Package Does

- Confirms zero `sanitation` rows exist in `data/contracts.csv`, and confirms — via direct field inspection plus cross-reference against the prior DPW full-corpus-scan session — that none of the seven already-collected `public_works` documents contains any sanitation-, refuse-, or recycling-specific title or duty language.
- **Sharpest quantified finding in this project to date:** national trade-press reporting citing BLS Census of Fatal Occupational Injuries data now places refuse/recycling collection's fatality rate (37.4-41.4 per 100,000 workers) above police's own, described directly as "considerably higher than in law enforcement." This sharpens, with hard numbers, the qualitative "sanitation hazard may exceed police's" claim already flagged in the original police/fire workforce-refinement memo.
- **Confirms real, complete (not merely supplemental) private-hauler contracting as a Massachusetts practice**, via four towns' own municipal web pages (Dedham, Andover, Marshfield, Brookline) — a materially different, more substitution-capable contractor profile than DPW's largely seasonal contractor use, and a plausible explanation for why this project's five DPW-collecting cities show no distinct sanitation title.
- **Confirms ~70% of Massachusetts communities have a consolidated DPW**, with solid waste frequently organized as a named division within it (not a free-standing department) — directly explaining sanitation's organizational "invisibility" inside this project's existing `public_works` corpus.
- **Extends the project's central institutional finding (no JLMC access) to sanitation by direct structural inference**, not independent re-verification — JLMC's eligibility rule (already verified four times: police/fire only, no essential-service exception for teachers, DPW, clerical/admin, or library) provides no basis to expect a sanitation-specific exception, and no source encountered this session suggests one.
- Treats contractor/private-hauler substitution as having **both** an upward-pressure reading (genuine private-sector wage competition) and a downward-pressure reading (wage-restraining substitution) explicitly, rather than assuming either direction — consistent with genuinely mixed academic privatization-cost research reviewed this session.
- Flags `sanitation_dirty_work_compensating_differential` explicitly as a hypothesis requiring evidence, not an assumed mechanism, mirroring the discipline already applied to gendered-occupational-valuation hypotheses elsewhere.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 9 ("Sanitation / solid waste mechanisms checklist," 9 rows: SN01-SN09, explicitly marked as scoping-stage since zero corpus rows exist), with Sections 10-14 renumbered from the prior 9-13; XC09 (arbitration/impasse backstop) extended to note sanitation's structurally-inferred (not independently re-verified) sixth-group status.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming sanitation's scoping completion and restating the recommended next step (source-acquisition planning, not a new mechanism-development group).
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H32-H35: `sanitation_route_coverage_pressure`, `sanitation_contractor_substitution`, `sanitation_mechanization_route_restructuring`, `sanitation_dpw_bundling`); the existing 31 rows were not touched.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Sanitation source-acquisition planning: confirm whether any of this project's current nine cities directly employs collection workers versus contracting the function entirely, and re-read the five already-collected `public_works` CBAs' job-description language (not just title language) for collection-duty content — no new ingestion required for the latter.
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Every sanitation finding in this session is either bounded external desk research or a structural extension of an already-verified fact — **none is corpus-confirmed**, since zero sanitation rows exist. Do not cite any sanitation mechanism as "confirmed in current corpus."
- Do not cite the sanitation fatal-injury-rate comparison to police as a causal or Massachusetts-specific claim — it is national data, cited via trade press, not this project's own corpus or a Massachusetts-specific source.
- Do not assume contractor/private-hauler substitution is wage-restraining by default — this session explicitly found the mechanism can run in either direction, and academic cost research does not settle which effect dominates.
- The central open question for any future sanitation work is whether this project's own nine cities employ sanitation workers directly at all, or contract the function out entirely — this determines whether a corpus-scan-style session (like library's) or a source-acquisition-first session (unlike any prior non-safety group) is the right next step.

---

## 2026-07-05T20:30:00-04:00 - Library wage mechanisms and corpus scan completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior Somerville-metadata-audit-and-checkpoint session's changes (`fe99104`, "Audit Somerville metadata and checkpoint wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_library_wage_mechanism_and_corpus_scan_2026-07-05.md`
  - `docs/analysis/non_safety_library_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (new Section 8 library table, 8 rows; Sections 9-13 renumbered; XC09 updated)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (4 new rows, H28-H31)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- **`data/contracts.csv` was NOT edited** — all three `library` rows' existing metadata was directly verified against source documents and found already accurate.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was library's full deeper-inspection pass — the fourth non-safety comparison group, and the first one developed in a single combined session (mechanism refinement + institutional verification + corpus scan) rather than two separate memos, since it required no new source acquisition.

### What This New Package Does

- Reviews all three already-collected `library` corpus rows (Seekonk, Franklin, Wayland) in full, including an ad hoc, read-only OCR pass for Wayland's image-only scan.
- **Confirms library's part-time/page staffing model is structurally distinct from every other occupation class reviewed so far**: part-time employment is a permanent, core bargaining-unit category in all three documents (unlike teachers' separate substitute pool or DPW's seasonal-only part-time use), and pages are explicitly excluded from bargaining-unit coverage at Franklin — meaning this project's corpus has no wage data at all for the most page-like tier.
- **Directly contradicts, rather than confirms, the volunteer-substitution sub-hypothesis**: Franklin's Article 28 explicitly bars replacing bargaining-unit hours with volunteer labor without union agreement — the clearest on-point textual signal in this scan, running counter to a naive buffering story.
- **Confirms professional (MLS/MLIS) credentialing as a real but uneven, modest mechanism**: Franklin pays an explicit degree-tier stipend (up to $1,900/year for MLS/MLIS); Seekonk has no degree-linked pay at all; Wayland treats a Master's degree only as an education-leave benefit. This uneven pattern, even within this project's own three cities, is itself evidence against treating library credentialing as a guaranteed wage floor the way teacher licensure functions.
- **Confirms a fourth independent instance of the project's central institutional finding**: library employees follow the ordinary Chapter 150E Section 9 route with no JLMC access, per the MMA Select Board Handbook's own direct language ("it is common for clerical and library employees to be union members"). A library-specific budget-floor mechanism was also identified: the MBLC's Municipal Appropriation Requirement (municipal library appropriation generally may not fall below ~102.5% of the prior three years' average, subject to waiver) — a real but weaker/waivable analog to teachers' Chapter 70 floor.
- **Replicates, a fourth time, the peer-community-comparability absence** already documented for `public_works` and `clerical_admin` — no wage-comparator language was found in any of the three library documents.
- National context (ALA/PLA 2024 staff survey; BLS occupational wage data; a dated 2006 ALA-APA compression study, explicitly flagged as not current) is kept clearly separated from Massachusetts-specific and current-corpus evidence throughout.

### Checklist, Roadmap, and Hypothesis Matrix Updates

- `wage_mechanism_evidence_checklist.md` gained a new Section 8 ("Library mechanisms checklist," 8 rows: LB01-LB08), with Sections 9-13 renumbered from the prior 8-12 accordingly; XC09 (arbitration/impasse backstop) updated to reflect a fourth independent non-safety confirmation.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one update block confirming library's deeper-inspection completion and restating sanitation as the next-priority group.
- `police_fire_wage_hypothesis_matrix_2026-07-02.csv` gained 4 new rows (H28-H31: `library_professional_credentialing`, `library_classification_reclassification`, `library_part_time_volunteer_buffering`, `library_service_deferral`); the existing 27 rows were not touched.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-session baseline — no row was added, edited, or removed from `data/contracts.csv` or `data/city_coverage.csv` this session.

### Recommended Next Step

1. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo next (desk research only, since zero `sanitation` rows currently exist in this project's corpus).
2. Bring the checkpoint memo's remaining flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Library's volunteer-substitution sub-hypothesis is **contradicted**, not confirmed — do not cite "libraries use volunteers to buffer staffing costs" as a finding; Franklin's own contract explicitly prohibits it.
- Do not treat MLS/MLIS credentialing as a universal or guaranteed wage premium — it is confirmed present (as a stipend) at only one of this project's three library cities.
- Do not conflate the MBLC's Municipal Appropriation Requirement with Chapter 70's net-school-spending floor — the library mechanism is a weaker, waivable, rolling-local-baseline requirement, not a state-formula-driven legal mandate.
- Do not treat this memo's national ALA/PLA and BLS citations as Massachusetts-specific or as describing any of this project's three library cities directly — they are bounded national context only, per this project's standing discipline.

---

## 2026-07-05T19:00:00-04:00 - Somerville metadata audit closed and project mechanism checkpoint completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior authorized-cleanup session's changes (`47f8d25`, "Apply approved metadata cleanup") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/somerville_police_metadata_audit_2026-07-05.md`
  - `docs/analysis/somerville_police_metadata_audit_edits_2026-07-05.csv`
  - `docs/analysis/wage_mechanism_project_checkpoint_2026-07-05.md`
- Updated:
  - **`data/contracts.csv`** (2 rows, 1 field each: `binding_arbitration_statute`)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: two new notes; not rewritten)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (one new update block; not rewritten)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` was **not** updated — reviewed, no major missing/redundant hypothesis found.
- No live GABRIEL calls were run. No model/API calls, and no Harvard proxy calls, were made from project scripts. No OEWS/BLS data was downloaded or processed. No ingestion happened. `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This session had two parts: a narrow, fully-verified metadata correction (Somerville `binding_arbitration_statute`) and a broad strategic-synthesis checkpoint — neither is a data-build, GABRIEL, or ingestion session.

### What This New Package Does

**Part 1 — Somerville metadata audit, resolved with a direct edit:**
- Both `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012` had `binding_arbitration_statute` values (`ocr_messy`, `clean`) that were actually `text_quality` values — the same field-misplacement pattern already corrected for Boston's clerical/admin row, but never previously flagged for these two rows until discovered incidentally during the prior application session.
- Verified via direct `pdftotext` re-extraction of both source PDFs: both are genuine JLMC award-and-decision documents (dockets JLMC-17-6072 and JLMC-14-4174), and each row's own `total_comp_note` field already correctly states `"MA G.L. c. 1078 (JLMC)"` — a redundant, in-row confirmation that made this correction higher-confidence than the earlier Boston fix (which relied on an OCR/typo inference rather than a sibling field's direct statement).
- **Applied directly:** both rows' `binding_arbitration_statute` now reads `MA G.L. c. 1078 (JLMC)`, matching all 13 other police/fire rows' convention. A closing sweep (`binding_arbitration_statute` vs. the `text_quality` vocabulary, all 32 rows) found **zero** remaining instances of this pattern.

**Part 2 — project mechanism checkpoint, a synthesis-only stocktake:**
- Consolidated the full mechanism-development arc to date (original police/fire memos; teacher, DPW, and clerical/admin mechanism-refinement-plus-institutional-verification sequences; the national municipal workforce scan; the public-sector impasse/arbitration state-law citation audit) into one memo.
- Documents, per occupation group (police, fire, teachers, DPW, clerical/admin): main upward and restraint mechanisms, current corpus evidence, external/national evidence, Massachusetts-specific caveats, and unresolved gaps.
- Includes an 11-row evidence-strength table (peer wage comparability, arbitration/impasse backstop, overtime/staffing spiral, recruitment/retention, credential/licensing scarcity, classification/reclassification, service deferral/buffering, contractor substitution, public salience, budget capacity/fiscal constraint, source-document production effects) and a section on what the current CBA-heavy, discourse-empty corpus can and cannot show.
- **Key recommendation:** `library` is the highest-priority next non-safety group, since all three `library` corpus rows (Seekonk, Franklin, Wayland) already exist and are already coverage-matched to safety pairs — a full corpus-scan-plus-institutional-verification session can run with **no new source acquisition**. `sanitation` is next-priority for a mechanism-refinement/institutional-context memo (desk research only, since zero `sanitation` rows currently exist). Transit, nurse_health, custodial/facilities, and dispatchers each need a scoping/schema decision from the user/PI before further work (§11 of the checkpoint memo).
- **Notable new finding surfaced while assembling the checkpoint:** this project's own corpus already contains dispatchers ("Community Safety Dispatchers") embedded, unlabeled, inside a `public_works`-classified Arlington bargaining unit — a composition-fragmentation detail not previously flagged as its own issue.

### Checklist and Roadmap Updates

- `wage_mechanism_evidence_checklist.md` §11 gained two new notes: the Somerville resolution (with a pointer to the new audit memo/CSV) and a pointer to the checkpoint memo's next-priority recommendation. Not rewritten.
- `non_safety_comparison_roadmap_2026-07-04.md` gained one new update block summarizing current deeper-inspection status (teachers/DPW/clerical-admin) and the checkpoint's ordered next-group recommendation. Not rewritten.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-edit baseline.

### Recommended Next Step

1. Run a library corpus-scan-plus-institutional-verification session (mirroring the DPW/clerical/admin two-memo pattern) using the three already-collected `library` rows — no new ingestion needed.
2. Run a sanitation mechanism-refinement + national/Massachusetts institutional-context memo next (desk research only).
3. Bring the checkpoint memo's three flagged scoping decisions (transit governance fit; nurse_health population mismatch; custodial/dispatcher schema questions) to the user/PI before any further work on those specific groups.
4. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state.

### Notes For ChatGPT Review

- Both Somerville police rows' `binding_arbitration_statute` now correctly reads `MA G.L. c. 1078 (JLMC)` — do not cite the old `ocr_messy`/`clean` values, which were metadata artifacts, not evidence about anything substantive.
- The checkpoint memo (`wage_mechanism_project_checkpoint_2026-07-05.md`) is a synthesis of existing findings, not new research — cite the underlying occupation-specific memos for full citations and quoted contract text; the checkpoint is a fast-scan index and prioritization document.
- `library` is recommended as the next non-safety group specifically because it is already-collected, not because it is conceptually more important than sanitation or transit — do not read the priority order as a claim about which mechanism matters most.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is the library corpus scan.

---

## 2026-07-05T17:15:00-04:00 - Authorized production metadata cleanup applied

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior metadata cleanup audit session's changes (`2e0a808`, "Audit metadata cleanup candidates") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_application_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_applied_edits_2026-07-05.csv` (29 rows)
- Updated:
  - **`data/contracts.csv`** (9 rows, 22 field-level changes — the first production edit to this file since the metadata-cleanup arc began)
  - `docs/schema.md` (2 field-definition clarifications: `interest_arbitration_flag`, `comparability_clause_flag`)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (§11: one new note, 3 short "RESOLVED" annotations; not rewritten)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no new rows were added; no `occupation_class` value was changed.
- `data/city_coverage.csv`, `corpus/`, and `inbox/` were **not** modified.
- This was the authorized production-edit follow-up to the prior audit-only session — the first session in this cleanup arc to actually write to `data/contracts.csv`.

### What This New Package Does

- Applies the user's two explicit schema decisions: (1) `comparability_clause_flag` now means peer wage / peer-community / peer-employer wage comparability specifically — not health-insurance, workers'-comp, internal-classification, or discipline/fact-pattern "comparable" language; (2) `retrieval_method=public_download` describes this project's own access method (not a document's original legal provenance), so MuckRock-hosted-but-openly-downloaded Somerville rows correctly remain `public_download`.
- **Corrects 5 non-wage `comparability_clause_flag` false positives:** Arlington `public_works` x2, Seekonk fire, Wayland fire, Wayland other — flag flipped `1`→`0`, with the non-wage finding preserved in `comparability_referent` (a schema-existing field) rather than discarded.
- **Re-extracts the corpus's first two true-positive peer-wage-comparability rows:** both Somerville police JLMC-award rows had the genuine "wages and benefits of comparable towns" statutory-criteria text sitting in their own `arbitration_clause_text` field, uncaptured by `comparability_text`. This session extracted the exact verbatim span (same wording, same line breaks) into `comparability_text`, with `comparability_referent` naming the referent.
- **Corrects 4 `interest_arbitration_flag` false positives** (Boston clerical/admin, Arlington `public_works` x2, Seekonk `public_works`) — all four had clause text describing grievance or civil-service disciplinary arbitration, not wage-setting interest arbitration.
- **Corrects Boston clerical/admin's 3-field misalignment:** `longevity_detail` (held a general unit-description note) and `total_comp_note` (held a bare, misleading JLMC citation) were swapped; `binding_arbitration_statute` (held `"clean"`, a `text_quality` value) was corrected to `"MA G.L. c. 150E"` — but only after this session directly re-extracted `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` and independently confirmed the citation at 3 locations in the source text (lines 95, 485, 1047 of the extracted text), resolving the prior audit's "medium-high confidence, pending PDF re-verification" flag.
- **Records both schema decisions in `docs/schema.md`** so future ingestion does not repeat the same miscoding.
- **New finding, explicitly not corrected:** while verifying the Boston edit, this session discovered both Somerville police rows' `binding_arbitration_statute` fields also hold `text_quality` values (`ocr_messy`, `clean`) instead of a statute name — the same pattern as Boston's, but never previously audited or approved. Left untouched, per this session's boundary against unapproved edits, and flagged for a future audit-and-approval cycle rather than fixed opportunistically.

### Checklist Update

- `wage_mechanism_evidence_checklist.md` §11 gained one new top-of-section note (production cleanup applied, both schema decisions stated, pointer to the new memo/CSV, the new unresolved finding flagged) plus short "RESOLVED 2026-07-05" annotations appended to items 1, 2, and 6 (not rewritten). Items 3, 4, 5, and 7 remain as historical record (no edit was needed for those).

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```
Both outputs are identical, in every count, to the pre-edit baseline — expected, since no applied edit touches `occupation_class`, cycle dates, or `obs_id`.

### Recommended Next Step

1. Review the `data/contracts.csv` diff directly (this session verified it programmatically — before/after row count 32, column count 34, and exactly the 9 intended obs_ids and their intended fields changed, nothing else) before treating the cleanup as final.
2. Decide whether to authorize a short follow-up audit-and-approval cycle for the newly-discovered Somerville `binding_arbitration_statute` anomaly — do not correct it without going through the same audit-then-approve process, even though the likely correct value (`"MA G.L. c. 1078 (JLMC)"`) is fairly obvious from cross-corpus pattern matching.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is reviewing this cleanup's diff and deciding on the Somerville follow-up.

### Notes For ChatGPT Review

- `data/contracts.csv` now has real, applied edits — this is the first entry in this handoff log where that file's diff is nonzero. Prior "no production edits" language in earlier entries applied to those specific sessions only.
- Do not cite `ma_boston_clerical_admin_2023`'s `binding_arbitration_statute` as `"clean"` or its `total_comp_note` as a bare JLMC citation any longer — both are corrected as of this session.
- Do not treat `ma_somerville_police_spsoa_2012`/`_spea_2012`'s `binding_arbitration_statute` fields (`"ocr_messy"`/`"clean"`) as reliable — this is a newly-discovered, not-yet-corrected anomaly; do not silently "fix" it without a dedicated audit-and-approval step first.
- `comparability_clause_flag=1` now reliably means peer-wage comparability across the whole corpus (2 true positives: the two Somerville police rows); `comparability_clause_flag=0` rows that previously had non-wage "comparable" text still retain that text's nature documented in `comparability_referent`.

---

## 2026-07-05T15:30:00-04:00 - Metadata cleanup audit completed (audit-first; no production edits)

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior citation-audit session's changes (`b18d6bd`, "Audit public sector impasse arbitration sources") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/metadata_cleanup_audit_2026-07-05.md`
  - `docs/analysis/metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows)
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (one concise status note at the top of §11 only)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; **no production metadata edits were made to `data/contracts.csv` or any other production file.**
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded, audit-first metadata-cleanup review — the task queued at the end of every session since the national scan — not a data-build, GABRIEL, or ingestion session.

### What This New Package Does

- Verifies, row by row against `data/contracts.csv` (via direct `csv.DictReader` inspection, not memo paraphrase) and against underlying corpus PDFs where useful, the 7 metadata issues already tracked in `wage_mechanism_evidence_checklist.md` §11, plus 3 newly-scoped issues (a corpus-wide `comparability_clause_flag` audit, an `occupation_class`/unit-title spot check, and a light provenance-field consistency check).
- **Most consequential finding — `comparability_clause_flag` is unreliable corpus-wide, not just at Arlington.** All 7 currently-flagged rows capture non-wage "comparable" language (drug-testing standard, workers'-comp medical-provider continuation, health-insurance plan-contribution parity, work-group-realignment eligibility). For the two Somerville JLMC-award rows specifically, the genuine peer-wage-comparability text — the award's own "wages and benefits of comparable towns" statutory-criteria language — is demonstrably already present in the dataset, just in the wrong field (`arbitration_clause_text` instead of `comparability_text`). This means those two rows can be corrected by re-extraction alone, with no new source acquisition.
- **Boston `clerical_admin` row (`ma_boston_clerical_admin_2023`) — sharper than previously documented.** This is a three-field misplacement, not a single stray citation: `total_comp_note` holds a bare `"MA G.L. c. 1078 (JLMC)"` citation; `longevity_detail` holds general unit-description text that belongs in `total_comp_note`; and `binding_arbitration_statute` holds `"clean"` — a `text_quality`-vocabulary value that does not belong in that field at all (this specific sub-finding is new to this audit). The row's own `interest_arbitration_flag=1` also appears miscoded: the captured `arbitration_clause_text` is pure grievance-procedure definitional language with no interest-arbitration content, consistent with clerical/admin's externally-confirmed JLMC ineligibility.
- **`interest_arbitration_flag` scope confirmed and enumerated.** 4 of the 6 rows flagged `interest_arbitration_flag=1` (Boston clerical/admin; both Arlington `public_works` cycles; Seekonk `public_works`, whose own clause states verbatim "Final binding arbitration will prevail on grievances only") contain grievance/discipline arbitration text, not wage-setting interest arbitration. Only the two Somerville police rows genuinely contain interest-arbitration text.
- **3 of the 7 originally-tracked issues require no further action**, with concrete confirmation: Seekonk clerical/admin's school-committee affiliation, `public_works`' cross-municipality bundling variation, and Worcester's successor-MOA/incorporation-by-reference limitation are all already stated plainly in the affected rows' own `total_comp_note` fields.
- **Teacher-aide/paraprofessional merge risk not realized.** Direct `pdftotext` extraction of the sole current `teacher` row (Seekonk Educators Association) confirms the contract itself places teacher aides outside the bargaining unit, under School Committee determination — no wage or step-schedule content for aides exists inside this teacher-classified row.
- Produced `metadata_cleanup_proposed_edits_2026-07-05.csv` (20 rows): 16 marked `production_edit_needed=yes` (4 boolean/flag corrections, 3 value corrections/swaps on the Boston row, 4 re-extractions on the Somerville rows, 5 notes-only `comparability_referent` clarifications), 3 marked `needs_followup` (schema-scope decisions that should precede any row edit), and 1 a `docs/schema.md` definition-clarification suggestion (not a data edit).

### Living Checklist Update

- `wage_mechanism_evidence_checklist.md` §11 gained one concise status note at the top (audit completed, proposed edits in the new CSV, no production edits made, next step is approval). The 7 existing tracked-issue entries were not rewritten; this audit's findings live in the new dated memo and CSV, cross-referenced from the checklist.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Review `metadata_cleanup_proposed_edits_2026-07-05.csv` and resolve the 3 `needs_followup` schema-scope decisions (comparability-flag wage-specificity; FOIA-vs-public_download retrieval-method convention; the third `needs_followup` row is the comparability-flag decision applied to the Arlington rows specifically), then authorize a narrowly-scoped production-edit session limited to exactly the 16 flagged rows/fields.
2. That future production-edit session should re-verify the Boston `binding_arbitration_statute` proposed value ("MA G.L. c. 150E") directly against `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` before writing it — the audit's supporting evidence (an in-row OCR/typo clue plus cross-corpus pattern-matching) is medium-high, not full, confidence.
3. Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is resolving the metadata-cleanup follow-ups above.

### Notes For ChatGPT Review

- Do not treat `data/contracts.csv`'s `comparability_clause_flag`/`comparability_text` fields as reliable signals of peer-jurisdiction wage comparability as currently populated — this audit found 0 true positives among the 7 currently-flagged rows, and 2 false negatives (the Somerville rows, where the correct text exists but in the wrong field).
- Do not cite `ma_boston_clerical_admin_2023`'s `binding_arbitration_statute` field (currently `"clean"`) or `total_comp_note` field (currently a bare JLMC citation) at face value; both are confirmed data-quality anomalies pending approval of the proposed corrections in the new CSV.
- Do not treat `interest_arbitration_flag=1` as proof of wage-setting interest arbitration without reading `arbitration_clause_text` directly — 4 of 6 currently-flagged rows are grievance/discipline arbitration.
- No production metadata edits have been made as of this entry; all corrections above are proposals pending approval.

---

## 2026-07-05T13:56:32-04:00 - Public-sector impasse/arbitration state-law citation audit completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior national-scan session's changes (`41d10b1`, "Add national municipal workforce mechanism scan") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/public_sector_impasse_arbitration_state_law_citation_audit_2026-07-05.md`
  - `docs/analysis/public_sector_impasse_arbitration_state_law_table_2026-07-05.csv`
- Updated:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md` (small targeted patches only — see below)
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (concise additions to XC09, XC10 only)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H7, H17 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded citation-audit and state-law source-verification session, not a data-build or GABRIEL session.

### What This New Package Does

- Audits the national scan's public-sector impasse/arbitration claims against primary legal sources for 12 required states (MA, NJ, NY, MI, RI, PA, WY, OK, IA, NC, SC, VA) plus two contrast states (WI, IL), with every claim labeled by source type (primary statute/agency vs. secondary summary) and confidence level.
- **Confirmed with primary-source citations:** compulsory or state-invocable binding police/fire interest arbitration in NJ (N.J.S.A. 34:13A-14 to -21), NY (Civil Service Law §209.4), MI (Act 312 of 1969), RI (Gen. Laws Ch. 28-9.1/28-9.2/28-9.5), PA (Act 111 of 1968), OK (Title 11 §51-101), and IL (5 ILCS 315/14); North Carolina's total public-sector bargaining prohibition (G.S. 95-98, 1959); Virginia's 2020/2021 local-option reform (Va. Code §40.1-57.2).
- **Corrected:** Wyoming's statute (W.S. §§27-10-101 to -109) is confirmed **fire-only** — no comparable Wyoming police statute was found, correcting the national scan's more general phrasing.
- **Most consequential finding — Iowa:** Iowa Code §20.22 is confirmed via primary source as a **general, all-covered-public-employee** binding, final-offer-selection arbitration statute in place since the 1970s — not teacher-specific, as the prior session's framing implied. Iowa's 2017 reform (House File 291) did not remove this for non-safety units (including teachers); it instead narrowed their bargaining scope (mostly base wages) and arbitration criteria (removing ability-to-pay and past-contract consideration, adding a mandatory public/private wage comparison) for any unit under 30% Iowa-defined "public safety employees." Iowa is now both a confirmed counterexample to "non-safety never gets compulsory arbitration" *and* an example of a state building its own safety-favoring asymmetry through a different lever (scope/criteria, not availability) than anything in this project's Massachusetts corpus.
- **Flagged as weakest-sourced:** South Carolina's bargaining prohibition is affirmed by consistent secondary-source consensus (Ballotpedia, CEPR, multi-state legal trackers) but could not be traced to a single primary statute as clean as North Carolina's within this session's bounded search — explicitly not cited with the same confidence.
- **Flagged as legally unsettled:** Wisconsin's 2011 Act 10 exempted police/fire/state troopers from general public-employee bargaining restrictions, but a December 2024 Dane County ruling struck down that exemption as an equal-protection violation under the Wisconsin Constitution — sourced only from secondary/journalistic reporting, status unsettled, likely under appeal. This is directly relevant to this project's "public-safety institutional privilege" framing: it shows the safety/non-safety distinction is not treated as self-evidently constitutional everywhere it appears.
- A source-reliability discrepancy flagged in the prior national-scan session (a secondary source's inconsistent characterization of Massachusetts's own teacher-strike rules) was not the focus of new research this session but remains flagged in the scan memo, unresolved by further primary-source work this session.

### National Scan Patches (Task C — small corrections only, not a rewrite)

- Wyoming corrected to fire-only with the primary citation (W.S. §§27-10-101 to -109) added, in both the police section (§4) and fire section (§5).
- Iowa's description sharpened in §6 and in the claim table (§11) to state it is a general public-employee mechanism with its own 2017 safety-favoring asymmetry, not a simple teacher-specific exception.
- Citation-audit pointers added to the JLMC-pattern table row (§9) and the NC/SC/VA bargaining-rights paragraph (§7), distinguishing primary-confirmed (NC, VA) from secondary-only (SC) claims.

### Living Checklist and Hypothesis Matrix Changes

- `wage_mechanism_evidence_checklist.md`: concise additions to XC09 (arbitration/impasse backstop — full citation list and Iowa nuance) and XC10 (public salience — Wisconsin equal-protection finding). No heavy rewrite.
- Hypothesis matrix: small edits to H6 (arbitration_or_impasse_backstop — full citation list, WY/IA corrections), H7 (political_support_or_public_salience — Wisconsin finding), and H17 (non_safety_wage_restraint — Iowa's scope/criteria-restriction lever). No new rows.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Conduct the metadata-cleanup audit of the 7 issues tracked in the living checklist's Section 11 — audit-first, confirming each issue against its underlying source document before any direct edit to `data/contracts.csv`. This citation audit was a parallel task and does not change that sequencing.
2. If future capacity allows, close the follow-up items this audit flagged: South Carolina's primary statute, Wyoming's police-specific equivalent (if any), Rhode Island's possible teacher-specific chapter, Pennsylvania's non-safety strike-right claim, and Wisconsin's primary Act 10 text/court opinion.
3. Continue updating the living checklist in place after future work.

### Notes For ChatGPT Review

- Do not cite Wyoming as covering police arbitration; the confirmed statute is fire-only.
- Do not describe Iowa's arbitration mechanism as teacher-specific; it is a general public-employee statute, and Iowa's own 2017 reform actually adds a safety-favoring wrinkle within it.
- Do not cite South Carolina's bargaining prohibition with the same confidence as North Carolina's; SC lacks an equally clean primary citation in this project's research to date.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the metadata-cleanup audit.

---

## 2026-07-05T12:52:27-04:00 - National municipal workforce mechanism scan completed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior living-checklist session's changes (`7557e59`, "Create wage mechanism evidence checklist") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/national_municipal_workforce_mechanism_scan_2026-07-05.md`
- Updated:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (in-place edits to 11 mechanism rows: PD01, PD12, FD03, FD12, TC10, TC12, DP12, CA01, CA03, CA13, XC09)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H1, H6, H9, H11 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded national qualitative scan, conducted via public-source desk research, not a data-build or GABRIEL session.

### What This New Package Does

- `national_municipal_workforce_mechanism_scan_2026-07-05.md` scans national context across police, fire, teachers, DPW/public works, and clerical/admin, with the specific purpose of distinguishing general U.S. municipal mechanisms from Massachusetts-specific institutions this project's prior sessions verified.
- **Most consequential finding:** compulsory police/fire interest arbitration — the policy pattern underlying Massachusetts's JLMC — recurs in at least New Jersey, New York, Michigan, Rhode Island, Pennsylvania, Wyoming, and Oklahoma. The *pattern* (a no-strike-for-compulsory-arbitration trade specific to police/fire) generalizes; the *specific vehicle* (JLMC) is Massachusetts's own implementation, not a national template.
- **School finance:** the general foundation-formula architecture behind Chapter 70 (a state spending floor filled by state aid after a local-capacity-based required contribution) is confirmed as the dominant national school-finance model (Urban Institute), with structurally comparable formulas confirmed in New Jersey and Wisconsin. Chapter 70's specific 82.5% cap and net-school-spending definition remain Massachusetts-specific parameters.
- **Fire:** NFPA data quantifies the national volunteer-firefighter decline directly (897,750 in 1984 to 676,900 in 2020, a 25% decline against ~40% U.S. population growth), with IAFF documenting communities converting to all-career departments as the adaptation — now a quantified national trend, not only a qualitative framing.
- **Police:** MissionSquare/SLGE's 2024 survey confirms real national police staffing difficulty (68% hard-to-fill) but shows it is not the single hardest local-government occupation — mental health (83%), nursing (77%), and corrections (74%) all rank higher in the same survey.
- **Clerical/admin:** formal civil-service classification-and-reclassification-appeal architecture (the basis of Boston's mechanism) is confirmed as a national norm (NY, NJ, federal OPM, Massachusetts's own state Civil Service Commission all share it) — Boston's specific narrow "arbitrary or capricious" arbitration standard remains an untested-elsewhere local parameter within that general architecture.
- **Important counterexamples/caveats surfaced, not smoothed over:** at least Iowa is documented to extend compulsory, state-labor-board-ordered arbitration to teachers, unlike Massachusetts's voluntary-only route; and the entire "non-safety lacks JLMC access" finding for DPW and clerical/admin presumes public-sector bargaining rights exist at all, which is false in North Carolina and South Carolina and was false in Virginia before a 2020 local-option reform. A secondary source's inconsistent characterization of Massachusetts's own teacher-strike rules was flagged explicitly rather than silently resolved, with this project's own primary-source (Mass.gov DLR) verification treated as authoritative for Massachusetts.
- Grounded the gendered-occupational-valuation hypothesis further in credible academic literature (Paula England's research; IWPR occupational-segregation research; a CRS report noting comparable-worth policy has "made the most headway in state and local governments") while explicitly declining to upgrade its status for this project's own specific findings, per the task's explicit instruction to keep it a hypothesis requiring evidence.

### Living Checklist Update

- `wage_mechanism_evidence_checklist.md` updated in place across 11 mechanism rows (PD01, PD12, FD03, FD12, TC10, TC12, DP12, CA01, CA03, CA13, XC09), adding national-scan findings without overwriting the existing table structure. Verified every edited row retains exactly 13 pipe delimiters (12 columns). `confirmed in external sources` was added only where the scan found credible support; uncertain claims (e.g., the project-specific gendered-occupational-valuation claim) were explicitly kept at their prior, more cautious status.

### Hypothesis Matrix Changes

- H1 (`recruitment_retention_pressure`): added the MissionSquare/SLGE calibration finding (police staffing pressure real but not uniquely severe among local-government occupations).
- H6 (`arbitration_or_impasse_backstop`): added the multi-state compulsory-arbitration pattern and the Iowa/NC/SC/VA counterexamples.
- H9 (`fiscal_capacity_ability_to_pay`): added the national foundation-formula generalization finding.
- H11 (`public_safety_service_necessity`): added the NFPA quantified volunteer-decline figures.
- No new rows added, since no wholly new national mechanism family was identified — every finding sharpened or qualified an existing hypothesis. Verified 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Roadmap Update

- `non_safety_comparison_roadmap_2026-07-04.md` gained one closing note confirming the national scan is complete and the next planned step is the metadata-cleanup audit, restating that national-general and Massachusetts-specific evidence should stay explicitly distinguished in future work.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Conduct the metadata-cleanup audit of the 7 issues tracked in the living checklist's Section 11 — audit-first, confirming each issue against its underlying source document before any direct edit to `data/contracts.csv`.
2. Continue updating the living checklist in place after any future corpus scans, OEWS/DESE/BLS descriptive baseline, or GABRIEL extraction run.
3. Keep national-general and Massachusetts-specific evidence explicitly distinguished in any future PI-facing synthesis.

### Notes For ChatGPT Review

- Do not treat JLMC, Chapter 70, or Proposition 2½ as national institutions; they are Massachusetts's specific implementations of more general, but not universal, national patterns (compulsory police/fire arbitration; foundation-formula school finance; local property-tax levy limits).
- Do not treat the "non-safety lacks compulsory arbitration" finding as universal; Iowa is a documented counterexample for teachers, and the finding presumes bargaining rights exist at all, which is false in NC, SC, and pre-2020 VA.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the metadata-cleanup audit.

---

## 2026-07-05T12:32:37-04:00 - Living wage-mechanism evidence checklist created

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior clerical/admin corpus-scan and Massachusetts clerical/admin impasse-context session's changes (`41be1b3`, "Scan clerical admin corpus and clarify impasse context") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/wage_mechanism_evidence_checklist.md` (undated, living reference file — do not fork a dated copy; update in place)
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: one closing note)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No national web scan or five-city web pilot was run; no new broad web research was conducted (this was a synthesis session over existing memos, not a research session).
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened; no metadata edits were made to `data/contracts.csv` or any other production file.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a synthesis and repo-organization session, consolidating existing findings into one canonical reference rather than producing new mechanism research.

### What This New Package Does

- `wage_mechanism_evidence_checklist.md` consolidates every wage-mechanism hypothesis developed across all prior sessions — the 27-row hypothesis matrix plus additional cross-cutting mechanisms and source-family entries not previously tabulated together — into one working checklist covering police, fire, teachers, DPW/public works, clerical/admin, and cross-cutting categories.
- Defines and uses a fixed status vocabulary (`not searched`, `partially searched`, `confirmed in current corpus`, `confirmed in external sources`, `weak evidence`, `not found in current corpus`, `contradicted`, `needs metadata cleanup`, `not applicable`) and a 12-column table structure (mechanism_id, mechanism, occupation_group, wage_pressure_direction, plausible_channel, evidence_that_would_support, evidence_that_would_weaken_or_contradict, best_source/document_types, current_repo_evidence, verification_status, next_action, notes) applied consistently across ~80 mechanism rows.
- Includes a source/document-type inventory (17 families, from CBAs and arbitration awards through national association reports), a current-corpus-evidence summary contrasting the DPW/clerical-admin corpus-rich picture against the teacher external-sources-rich picture, a tracked (not corrected) list of 7 known metadata-cleanup issues, and an update protocol instructing future sessions to update rows in place rather than fork new dated files.
- Explicitly frames every substantive claim as a pointer back to the underlying occupation-specific memo, so the checklist stays a fast-scan working reference rather than a competing source of truth.
- Highlights, by putting all five occupation groups side by side for the first time, that the arbitration/impasse-backstop finding (JLMC compulsory interest arbitration confirmed unique to police/fire, with teachers, DPW, and clerical/admin all independently verified to share the same Chapter 150E Section 9 route) is now the single most thoroughly cross-verified finding in the project.

### Roadmap Update

- `non_safety_comparison_roadmap_2026-07-04.md` gained one closing note pointing to the new checklist, restating that the next planned step is the national qualitative scan across police, fire, teachers, DPW/public works, and clerical/admin, and that metadata cleanup should follow the national scan and be audit-first, not direct-edit-first.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Run the national qualitative scan across police, fire, teachers, DPW/public works, and clerical/admin.
2. After the national scan, conduct a metadata-cleanup audit of the issues tracked in the new checklist's Section 11 — audit-first, not direct-edit-first.
3. Update the checklist in place after the national scan, the metadata-cleanup audit, any future corpus scans, and any future OEWS/DESE/BLS descriptive baseline or GABRIEL extraction run.

### Notes For ChatGPT Review

- Do not treat `wage_mechanism_evidence_checklist.md` as a replacement for the occupation-specific memos it summarizes; it is a fast-scan index, and full citations/quoted contract text live in the memos it points to.
- Do not add a dated filename fork of the checklist in a future session; update the existing file in place per its own update protocol (Section 12).
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, ingestion, or a metadata edit as the immediate next step from this state; the recommended next step is the national qualitative scan, followed by a metadata-cleanup audit.

---

## 2026-07-05T12:01:59-04:00 - Clerical/admin existing-corpus scan and Massachusetts impasse context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior clerical/admin mechanism session's changes (`75b8c22`, "Refine clerical admin wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_existing_corpus_scan_2026-07-05.md`
  - `docs/analysis/ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md` (light edit: closed gaps 3 (partial), 4, 13, 15)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: second clerical/admin update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edits to H6, H23, H24 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional-verification and internal-corpus-review session, not a data-build or GABRIEL session.

### What This New Package Does

- **Existing corpus review:** identified all three `clerical_admin` occupation-class rows in `data/contracts.csv` (Worcester, Boston, Seekonk), confirmed all three corpus files exist, and read their actual text in full (native extraction for Worcester and Boston; a prior session's ad hoc, read-only OCR pass reused for Seekonk's image-only file). Findings: Boston's contract contains the most procedurally restrictive reclassification mechanism found anywhere in this project's corpus to date — a Compensation Grade Appeals process whose arbitration is explicitly limited to an "arbitrary or capricious" standard (not a full merits review), with an explicit, twice-stated contractual exclusion of workload/technology-driven duty changes as valid reclassification grounds; a CDL stipend embedded in a nominally clerical/admin unit; and a documented departmental-merger history (BCYF, Public Facilities/DND, Environment Department, Office of Historic Preservation) revealing the unit spans far more than clerical titles (Grants Manager, Network Administrator, Facilities Manager, Aquatics Manager, and others). Worcester's document remains a short successor MOA with no classification/reclassification content. Seekonk's is a school-based Administrative Secretaries unit with a simple longevity schedule and no reclassification apparatus. No peer-community wage-comparability, pay-compression, or workload/backlog language was found in any of the three documents.
- **Massachusetts clerical/admin impasse verification:** confirms, via the Massachusetts Municipal Association's Select Board Handbook, that "clerical and administrative employees do not qualify for JLMC services" — the most direct confirmation found yet for any of the three non-safety groups (naming the occupation class explicitly rather than requiring inference from a general non-police/fire rule). So clerical/admin bargaining follows the same general Chapter 150E Section 9 route already confirmed for teachers and DPW. A new institutional wrinkle: some administrative positions closest to municipal executive leadership are "confidential employees" excluded from collective bargaining entirely, meaning their pay is set unilaterally, not through any bargaining/impasse process at all.
- Flags and precisely corrects a `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row: a stray "MA G.L. c. 1078 (JLMC)" citation sits in the wrong field (`total_comp_note` instead of `binding_arbitration_statute`), which could be misread as evidence of JLMC coverage. Verified directly against the actual contract text that no JLMC reference exists in the document. Not corrected in `data/contracts.csv`, per this session's review-only scope; flagged for a future data-quality pass.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): one small, targeted addition adding the verified MA clerical/admin institutional corroboration (the explicit MMA Select Board Handbook naming, the narrower CGA arbitration standard, and the confidential-employee exclusion wrinkle) alongside the teacher- and DPW-specific verifications already present.
- H23 (`clerical_admin_classification_restraint`) and H24 (`clerical_admin_reclassification_pressure`): both sharpened with the full corpus-scan findings (the exclusive, narrow-remedy CGA procedure; the explicit workload/technology exclusion language).
- No new rows added; verified 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_clerical_admin_source_gaps_2026-07-05.md`: gaps 3 (reclassification requests, partially closed — process documented, outcome data remains hard), 4 (pay-grade/step structures), 13 (peer-community comparisons), and 15 (MA clerical/admin impasse-process verification) marked CLOSED with pointers to the new memos.
- `non_safety_comparison_roadmap_2026-07-04.md`: a second clerical/admin update note added confirming both open items from the prior session (institutional verification; corpus review) are now resolved, and that all three non-safety comparison groups have completed both stages.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Move to the national qualitative scan across police, fire, teachers, DPW, and clerical/admin per the existing roadmap, since both clerical/admin uncertainties from the prior session are now resolved.
2. If a clerical/admin-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in the new corpus-scan memo, and treat pay-compression, workload/backlog, and recruitment/retention framing as new-source-acquisition gaps, not further-review gaps.
3. Flag the `data/contracts.csv` field-alignment anomaly in the Boston clerical/admin row for a future data-quality pass; do not correct it outside a review-only session's scope.

### Notes For ChatGPT Review

- Do not restate the task brief's reference to "H10 arbitration_or_impasse_backstop" — in the current matrix, `arbitration_or_impasse_backstop` is H6; H10 is `credentialing_training_burden`. Both the corpus-scan and impasse memos note the correct current identifier.
- Do not read the stray "MA G.L. c. 1078 (JLMC)" text in Boston's `total_comp_note` field as evidence of JLMC coverage for that unit — it is a field-alignment artifact, and the actual contract text contains no JLMC reference.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is the national qualitative scan across all five occupation groups.

---

## 2026-07-05T11:17:24-04:00 - Clerical/admin wage mechanism refinement developed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior DPW corpus-scan and Massachusetts DPW impasse-context session's changes (`d1b4969`, "Scan DPW corpus and clarify impasse context") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_clerical_admin_wage_mechanism_refinement_2026-07-05.md`
  - `docs/analysis/non_safety_clerical_admin_source_gaps_2026-07-05.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: clerical/admin findings update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H23-H27; small extension to H17)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only light review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded context-building/hypothesis-refinement session focused on clerical/administrative municipal workers as the third non-safety comparison group, not a data-build or GABRIEL session.

### What This New Package Does

- Develops clerical/admin as the "plainest" non-safety comparison group: unlike teachers (credentialing/salience) and DPW (operational/licensing), clerical/admin generally lacks both kinds of ready-made justification, which isolates what pure wage-setting institutions can restrain on their own.
- Maps clerical/admin into distinct sub-titles (clerk/senior clerk/principal clerk, administrative/executive assistant, office manager, payroll/accounting staff, assessor/collector/treasurer staff, town/city clerk staff, school administrative assistants, department-nested clerical roles, supervisors) rather than treating it as one homogeneous occupation.
- Surfaces a concrete, corpus-grounded reclassification mechanism: Boston's clerical/admin CBA documents a formal "OHR Classification and Compensation Unit" review process for reclassification applications, with management rights explicitly reserved over reorganize/reclassify decisions — the basis for two new hypotheses distinguishing classification-system restraint from reclassification-as-the-visible-channel.
- Identifies that this project's Seekonk `clerical_admin` row (Administrative Secretaries) is a school-based unit, not a general municipal office unit, directly illustrating the composition caution already applied to teachers and DPW.
- Grounds the pay-compression mechanism in a directly quantified, multi-state estimate: The Century Foundation's analysis of the cost of raising local-government workers above a $15 minimum wage threshold across six jurisdictions **including Massachusetts**, ranging 0.2% (DC) to 1.0% (Illinois) of payroll per year, weighted average ~0.6%.
- Confirms a real Massachusetts shared-services mechanism via Mass.gov's Efficiency and Regionalization grant program, with concrete examples (shared Regional Sustainability Coordinator across Westford/Carlisle; shared Town Administrator across Berkshire Regional Planning Council/Savoy).
- Explicitly flags gendered occupational valuation ("comparable worth") as a hypothesis requiring dedicated evidence, not an established fact about this project's cities, per the task's explicit instruction to handle this carefully.
- Explicitly separates Massachusetts-specific findings (the three corpus examples, the Massachusetts-inclusive minimum-wage-compression estimate, the Massachusetts shared-services grant program) from purely national background (MissionSquare recruitment/retention reporting, general automation-vendor material) throughout.

### Hypothesis Matrix Changes

- Added H23 `clerical_admin_classification_restraint`, H24 `clerical_admin_reclassification_pressure`, H25 `clerical_admin_pay_compression`, H26 `clerical_admin_service_backlog_absorption`, H27 `clerical_admin_lower_public_salience` as new rows, all with police/fire relevance marked low, consistent with the existing schema (12 columns unchanged). Unlike the DPW session (where the analogous public-salience hypothesis was folded into H7), this session added `clerical_admin_lower_public_salience` as its own row, per this session's task brief explicitly listing it among the 5 recommended additions.
- Lightly extended H17 (`non_safety_wage_restraint`) counterpoint field to note the clerical/admin extension as the "plainest" test case.
- Verified: 28 total rows (27 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- 15 clerical/admin source gaps identified in `non_safety_clerical_admin_source_gaps_2026-07-05.md`, several partially closed this session via bounded web search and light corpus read (national recruitment/retention context, the Massachusetts-inclusive minimum-wage-compression estimate, Massachusetts shared-services examples, the Boston reclassification-process example) and others flagged as open (full corpus review of all three `clerical_admin` rows, Massachusetts-specific vacancy/turnover/backlog data, clerical/admin-specific impasse-process verification, and gendered-occupational-valuation evidence).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a concise clerical/admin findings update note under the existing Section 3, including the recommendation that a national qualitative scan across police, fire, teachers, DPW, and clerical/admin is the natural next major step now that all three non-safety comparison groups have an initial mechanism map.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Verify whether Massachusetts clerical/admin bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers and DPW.
2. Conduct a full document-by-document review of this project's three already-collected `clerical_admin` corpus rows, mirroring the dedicated DPW corpus-scan session.
3. Move to a national qualitative scan across police, fire, teachers, DPW, and clerical/admin, now that all three non-safety comparison groups have an initial mechanism map in place.

### Notes For ChatGPT Review

- Do not treat the gendered-occupational-valuation discussion as an established finding; it is explicitly flagged as a hypothesis requiring dedicated evidence not yet gathered.
- Do not treat this session's light, illustrative corpus read (three cities) as equivalent in depth to the dedicated DPW corpus-scan session; a fuller review remains a recommended next step.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is clerical/admin impasse verification, a fuller corpus review, and then the national qualitative scan.

---

## 2026-07-05T10:36:45-04:00 - DPW existing-corpus scan and Massachusetts DPW impasse context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior DPW mechanism session's changes (`3addd14`, "Refine DPW public works wage mechanisms") were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_existing_corpus_scan_2026-07-04.md`
  - `docs/analysis/ma_dpw_bargaining_impasse_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md` (light edit: closed gaps 9, 11, 12)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: second DPW update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (small targeted edit to H6 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened: no files were added to `corpus/`, and no rows were added to or edited in `data/contracts.csv` (read-only review only).
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional-verification and internal-corpus-review session, not a data-build or GABRIEL session.

### What This New Package Does

- **Existing corpus review:** identified all seven `public_works` occupation-class rows in `data/contracts.csv` (Worcester, Arlington x3 cycles, Seekonk, Franklin, Wayland), confirmed all seven corpus files exist, and read their actual text (native extraction for six files; an ad hoc, session-local, read-only OCR pass for two image-only Wayland files whose content was not otherwise legible — output not written back to the corpus). Findings: extensive, source-grounded classification-to-credential-pay linkage (Arlington's CDL-class-tied Motor Equipment Operator grades; Franklin's detailed biweekly stipend schedule covering CDL, hoisting, water/wastewater, pesticide, and ASE mechanic certifications); rich contractor-substitution/outsourcing language (Franklin's two side letters, including a clause where contractor mobilization during snow events triggers an in-house overtime premium; Wayland's emergency-only non-union-labor carve-out); and a genuine, notable absence of peer-community wage-comparability language and explicit recruitment/retention framing in every document reviewed.
- **Massachusetts DPW impasse verification:** confirms, via Mass.gov DLR/JLMC pages and M.G.L. c. 150E, that JLMC eligibility is limited to police and fire (with only a narrow, still police/fire-confined discretionary extension), so DPW/public works bargaining follows the same general Chapter 150E Section 9 route already confirmed for teachers (mediation, advisory factfinding, potential unilateral last-best-offer implementation, rarely-invoked voluntary arbitration). This external finding is directly corroborated by the project's own corpus: every `public_works` row's `binding_arbitration_statute` field cites MA G.L. c. 150E, never the JLMC statute used by every police/fire row, and every arbitration clause found is grievance/discipline-scoped (Seekonk's contract states this explicitly: "Final binding arbitration will prevail on grievances only").
- Flags one metadata-reading observation without acting on it: `data/contracts.csv`'s `comparability_clause_flag` is set to `1` for two Arlington `public_works` rows, but the flagged snippet is a health-insurance/workers'-compensation "comparable" usage, not peer-jurisdiction wage comparability — noted for future readers of the existing metadata, not corrected in this session since `data/contracts.csv` is not modified.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): one small, targeted addition to the counterpoint field, adding the verified MA public-works/DPW institutional and corpus corroboration alongside the teacher-specific verification already present from the prior session. No new rows added; no other DPW rows (H18-H22) required substantive changes based on this session's findings, though the corpus scan memo documents which of those hypotheses are now corpus-supported, corpus-silent, or corpus-untestable.
- Verified: 23 total rows (22 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_dpw_public_works_source_gaps_2026-07-04.md`: gaps 9 (classification/pay-grade structures), 11 (union bargaining language), and 12 (peer-community comparisons) marked CLOSED with pointers to the new corpus-scan and impasse-context memos.
- `non_safety_comparison_roadmap_2026-07-04.md`: a second DPW update note added confirming both open items from the prior DPW session (institutional verification; corpus review) are now resolved.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Move to the clerical/admin comparison group per the existing roadmap, since both DPW uncertainties flagged at the end of the prior DPW session are now resolved.
2. If a DPW-specific GABRIEL/source-extraction attribute is ever prototyped, use the corpus-confirmed textual-signal list in the new corpus-scan memo, and treat peer-comparability and recruitment/retention framing as new-source-acquisition gaps, not further-review gaps.
3. Do not begin GABRIEL/source-extraction prototyping, an OEWS/municipal descriptive baseline build, or ingestion from this state.

### Notes For ChatGPT Review

- Do not restate the task brief's reference to "H10 arbitration_or_impasse_backstop" — in the current matrix, `arbitration_or_impasse_backstop` is H6; H10 is `credentialing_training_burden`. The corpus-scan and impasse memos both use and note the correct current identifier.
- Do not treat the two Wayland files' content as coming from the project's stored corpus text; it was read via this session's ad hoc OCR pass only, which was not written back into `corpus/` or `data/contracts.csv`.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is scoping the clerical/admin comparison group.

---

## 2026-07-04T17:55:09-04:00 - DPW / public works wage mechanism refinement developed

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior non-safety teacher mechanism session's changes (`efbfb31`) and the Massachusetts teacher institutional clarification session's changes (`e409824`) were already committed, with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/non_safety_dpw_public_works_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_dpw_public_works_source_gaps_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: DPW findings update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H18-H22; refined H4 and H7)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded context-building/hypothesis-refinement session focused on public works/DPW as the second non-safety comparison group, not a data-build or GABRIEL session.

### What This New Package Does

- Develops DPW/public works as the strongest available *operational* non-safety comparison to police/fire (physical risk, licensure gating, short-notice emergency response), complementing teachers' *credentialing/salience* comparison already developed in prior sessions.
- Maps DPW into distinct sub-occupations (laborers, equipment operators, CDL drivers, water/wastewater operators, mechanics, foremen) rather than treating it as one homogeneous occupation, mirroring the teacher composition-effect discipline.
- Surfaces a genuine, well-sourced counterargument to the CDL-scarcity mechanism: BLS's own 2019 Monthly Labor Review analysis found no evidence of a secular truck-driver shortage, with real driver wages up only ~1.1% since 2010 — inconsistent with chronic scarcity and more consistent with a retention/wage-framing problem that industry associations (echoed by APWA's national workforce-shortage framing) have called a "shortage" since the late 1980s.
- Identifies water/wastewater operator certification, not CDL, as the strongest genuine DPW scarce-credential case, based on national and New England-regional (NEIWPCC) retirement-wave evidence (30-50% of the water workforce eligible to retire within 5-10 years).
- Surfaces a specific Massachusetts institutional wrinkle: Massachusetts prevailing wage law ties public-construction contractor wages to locally collectively bargained rates, so contracting out DPW-type work does not simply undercut the wage paid for that specific work the way outsourcing might without such a law (though routine service contracts may not always be covered).
- Compares DPW emergency work (snow/storm response, water-main breaks) to police/fire emergency response, concluding DPW emergency needs more plausibly convert into overtime and contractor spending (reported at roughly 3x normal rates during active events) than into recurring base-wage pressure, given routine pre-arranged contractor substitution unavailable to police/fire.
- Explicitly separates Massachusetts-specific findings (hoisting license, prevailing wage law, municipal classification/CBA structure) from national background context (CDL debate, national water-workforce statistics, APWA framing) throughout, per this session's scope instruction not to overgeneralize.

### Hypothesis Matrix Changes

- Added H18 `dpw_operational_essentiality`, H19 `dpw_cdl_equipment_operator_scarcity`, H20 `dpw_contractor_substitution`, H21 `dpw_service_deferral`, H22 `dpw_classification_fragmentation` as new rows, all with police/fire relevance marked low, consistent with the existing schema (12 columns unchanged).
- Refined H4 (`overtime_staffing_spiral`) and H7 (`political_support_or_public_salience`) counterpoint fields to fold in DPW-specific nuances (contractor-substitution availability changing the overtime-spiral comparison; DPW's likely-lower but event-dependent public salience) rather than adding separate rows for those two.
- `dpw_water_sewer_license_scarcity` and `dpw_overtime_emergency_response` and `dpw_lower_public_salience`, three of the eight hypotheses named in this session's task brief, were deliberately not given their own CSV rows; the first is folded into H19's counterpoint as its strongest sub-case, and the latter two are folded into the H4 and H7 refinements respectively, consistent with the preference for a small number of high-value additions.
- Verified: 23 total rows (22 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- 13 DPW/public-works source gaps identified in `non_safety_dpw_public_works_source_gaps_2026-07-04.md`, several partially closed this session via bounded web search (national CDL/BLS labor-market debate, national/NEIWPCC water-workforce context, MA hoisting-license and prevailing-wage mechanics) and others flagged as open (Massachusetts-city-specific vacancy/overtime/classification data, whether DPW bargaining follows the same Chapter 150E Section 9 process as teachers, and whether this project's already-collected `public_works` CBAs contain classification premiums or comparator language).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a concise DPW findings update note under the existing Section 2, without a full rewrite.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Review this project's already-collected `public_works` occupation-class CBAs for classification/pay-grade structure, credential-tied premiums, and comparator-district language, without new ingestion.
2. Verify whether Massachusetts DPW/public-works bargaining follows the same Chapter 150E Section 9 impasse process already confirmed for teachers.
3. Move to the clerical/admin comparison group per the existing roadmap, only after the DPW source gaps above are addressed.

### Notes For ChatGPT Review

- Do not restate the CDL "shortage" framing as an established scarcity fact; BLS's own analysis is the operative counter-evidence, and the correct framing is a live shortage-vs-retention-problem debate, not a settled shortage.
- Do not treat the national/NEIWPCC water-workforce statistics or APWA workforce-shortage framing as Massachusetts-city-specific findings; they are national/regional background context, not verified for this project's specific cities.
- Do not recommend a GABRIEL run, an OEWS/municipal descriptive baseline build, or ingestion as the immediate next step from this state; the recommended next step is reviewing already-collected corpus documents and verifying the DPW bargaining-impasse-process question.

---

## 2026-07-04T16:36:12-04:00 - Massachusetts teacher bargaining and school finance institutional context verified

**Commit:** pending in current session

### Current State After This Entry

- Confirmed the prior non-safety teacher mechanism session's changes were already committed as `efbfb31` ("Refine non-safety teacher wage mechanisms"), with only `tmp/` left untracked at session start; no recommit was needed or performed.
- Created:
  - `docs/analysis/ma_teacher_bargaining_school_finance_institutional_context_2026-07-04.md`
- Updated:
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md` (light edit: closed gap item 13)
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md` (light edit: added an update note)
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined H5, H6, H9 only; no new rows)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was a bounded institutional/source-verification session, not a data-build or GABRIEL session.

### What This New Package Does

- Verifies the two Massachusetts-specific institutional claims the prior teacher mechanism session flagged as unverified, using primary/near-primary sources: DESE's own Chapter 70 program pages, Mass.gov Department of Labor Relations impasse and JLMC pages, and Massachusetts General Laws Chapter 150E Section 9.
- **Chapter 70/school finance:** confirms the foundation budget -> required local contribution (capped at 82.5% of foundation budget locally) -> Chapter 70 aid -> net school spending chain, and establishes that schools face a two-sided budget constraint (a state-mandated spending floor plus the same municipal Proposition 2 1/2 levy-limit ceiling shared by other departments) that most other municipal departments, including police/fire, do not have on the floor side.
- **Teacher bargaining impasse process vs. JLMC:** corrects, rather than simply confirms, the prior hedge. The precise, verified finding is that JLMC *orders* police/fire into compulsory binding interest arbitration upon certified impasse, while teachers (and most other MA public employees) under Chapter 150E Section 9 have only mediation plus advisory (non-binding) factfinding, after which the school committee may unilaterally implement its last, best offer. A voluntary arbitration route exists on paper for non-police/fire units but requires mutual agreement and school-committee authorization and is not typical in practice — Mass.gov's own guidance states non-police/fire bargaining has "no arbitration process." This is a compulsory-vs-voluntary institutional-design difference, not a has-backstop-vs-has-no-process-at-all difference, and the new memo is explicit about that correction.
- Includes a claim/correction/evidence table covering all five required claims (JLMC-like backstop absence, Chapter 70/local-contribution constraint, shortage buffering, peer-district comparability outside JLMC-style awards, and school-finance-vs-ordinary-ability-to-pay), each marked with a verification status and source support.

### Hypothesis Matrix Changes

- H6 (`arbitration_or_impasse_backstop`): counterpoint, textual-signal, and quant-data fields updated to state the verified compulsory-vs-voluntary distinction precisely, with a new textual signal (advisory/recommendations language, last-best-offer unilateral-implementation language) as the signature of the weaker non-safety process.
- H9 (`fiscal_capacity_ability_to_pay`): counterpoint, textual-signal, source-type, quant-data, and confound fields updated to state the verified two-sided floor/ceiling school-finance structure (net school spending floor plus Proposition 2 1/2 ceiling) precisely.
- H5 (`comparator_ratchet`): counterpoint field lightly updated to note that JLMC comparator criteria are statutorily mandated while teacher-side comparator claims have no equivalent compulsory enforcement mechanism.
- No new rows were added; verified 18 total rows (17 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Updates

- `non_safety_teacher_source_gaps_2026-07-04.md` gap item 13 (Massachusetts teacher bargaining impasse process) is now marked CLOSED with a pointer to the new institutional memo and a note on the one remaining sub-gap (city-specific override/net-school-spending-compliance history, not yet reviewed).
- `non_safety_comparison_roadmap_2026-07-04.md` gained a short update note under the teachers section pointing to the new institutional memo, plus a reminder to check whether DPW bargaining (next in sequence) follows the same general Chapter 150E Section 9 process as teachers.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Cross-reference the new institutional memo from the existing PI-facing synthesis memo, so PI-facing material states the compulsory-vs-voluntary arbitration distinction and Chapter 70 floor/ceiling structure as verified facts rather than hedged hypotheses.
2. Move to the public works/DPW comparison group per the existing roadmap, checking whether DPW bargaining follows the same Chapter 150E Section 9 process as teachers.
3. Do not begin GABRIEL/source-extraction prototyping, the OEWS/DESE descriptive baseline build, or ingestion from this state.

### Notes For ChatGPT Review

- Do not restate "teachers have no arbitration backstop at all" without the compulsory-vs-voluntary nuance verified this session; the precise claim is that JLMC compels arbitration upon impasse while teacher bargaining does not, not that teachers have zero statutory arbitration access whatsoever.
- Do not treat this session's Chapter 70 findings as sufficient for any city-specific school-finance claim in this project's current corpus; no city-level override or net-school-spending-compliance history was reviewed this session.
- Do not recommend a GABRIEL run as the immediate next step; the recommended next step is the PI-synthesis cross-reference and the DPW comparison group.

---

## 2026-07-04T11:50:03-04:00 - Non-safety wage mechanism refinement started with teachers

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/non_safety_teacher_wage_mechanism_refinement_2026-07-04.md`
  - `docs/analysis/non_safety_teacher_source_gaps_2026-07-04.md`
  - `docs/analysis/non_safety_comparison_roadmap_2026-07-04.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (added H13-H17; refined H5 and H9 counterpoint fields)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was explicitly a context-building/hypothesis-refinement session focused on the non-safety side of the comparison, not a data-build or GABRIEL session.

### What This New Package Does

- Develops, for the first time in this project, the "other side" of the police/fire wage-gap comparison: the gap can grow because safety wages accelerate, because non-safety wages are restrained, or both, and prior memos only addressed the first term.
- Starts with teachers specifically, not "non-safety" generically, because teachers share the most features with the safety side (credentialing, unionization, political salience, public esteem) and are therefore the hardest, most informative test case.
- Grounds the teacher-supply, composition, salary-schedule, and budget-constraint sections in real cited sources found via bounded web search this session: NCES/IES School Pulse Panel (74% of U.S. public schools had difficulty filling at least one teaching vacancy entering 2024-25, down from 79%; special education and ESL/bilingual hardest to fill by grade band), Learning Policy Institute (special ed/science/math the most common statewide shortage areas; ~1 in 8 positions unfilled or non-fully-certified), NCTQ (roughly 3 in 4 sampled districts already offer hard-to-fill differentiated pay; step-and-lane schedule mechanics), Massachusetts DESE (Teacher Salaries Report methodology), and Mass.gov (Proposition 2 1/2 levy-limit/override mechanics).
- Develops a structural asymmetry hypothesis: teacher-side shortage buffering (substitutes, emergency certification, larger classes, program cuts) tends to substitute toward cheaper labor or degraded service rather than raising pay to existing staff, unlike police/fire overtime/callback buffering, which directly raises realized compensation to incumbent workers — a candidate structural reason non-safety wage growth could lag even under comparable measured staffing strain.
- Explicitly flags two claims as unverified this session rather than asserting them: Massachusetts's Chapter 70 state-aid formula mechanics, and whether Massachusetts teacher bargaining under M.G.L. c. 150E lacks a binding wage-arbitration backstop (unlike police/fire under JLMC). Both are routed to the new source-gap memo as priority items.
- Sets up, without deeply researching, the next two non-safety comparison groups (public works/DPW, then clerical/admin) and briefly notes later groups (sanitation, facilities/custodial, libraries/parks, transit, nurses/health) in a sequencing roadmap.

### Hypothesis Matrix Changes

- Added H13 `teacher_supply_pressure`, H14 `teacher_shortage_buffering`, H15 `teacher_composition_effect`, H16 `teacher_salary_schedule_rigidity`, H17 `non_safety_wage_restraint` as new rows, all with police/fire relevance marked low (H17 medium/medium as the general cross-occupation mirror hypothesis), consistent with the existing schema (12 columns unchanged).
- Refined H5 (`comparator_ratchet`) and H9 (`fiscal_capacity_ability_to_pay`) counterpoint fields to fold in `teacher_peer_district_comparability` and `school_budget_constraint` respectively, rather than adding separate rows for those two, per the standing preference to improve the existing map over proliferating new rows.
- `non_safety_service_deferral_or_substitution`, the eighth hypothesis discussed in the new memo, was deliberately not given its own CSV row this session; it is documented as a general framing concept motivating `teacher_shortage_buffering` and the DPW/clerical roadmap, pending evidence from those later comparison groups.
- Verified: 18 total rows (17 hypotheses + header), 12 columns, no CSV structure mismatches.

### Source-Gap and Roadmap Highlights

- 13 teacher/non-safety source gaps identified in `non_safety_teacher_source_gaps_2026-07-04.md`, several partially closed this session via bounded web search (teacher vacancy rates, under-certification shares, shortage-area subjects, hard-to-fill stipend base rates, Proposition 2 1/2 mechanics) and others flagged as still open (long-term substitute use, grade/subject composition for this project's specific cities, district-level peer salary comparisons, and the Massachusetts teacher bargaining impasse-process verification).
- `non_safety_comparison_roadmap_2026-07-04.md` sequences public works/DPW second (tests operational similarity without safety's institutional/political-salience advantages) and clerical/admin third (cleanest available budget-capacity baseline), with brief notes on sanitation, facilities/custodial, libraries/parks, transit, and nurses/health as later groups.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Verify the two claims flagged as unverified this session: Massachusetts Chapter 70 state-aid mechanics, and whether Massachusetts teacher bargaining lacks binding wage arbitration.
2. Review this project's existing city CBAs for teacher salary-schedule structure, hard-to-fill stipend/MOU language, and comparator-district language, where teacher units are already in the corpus.
3. Only after that, move to the public works/DPW comparison group per the new roadmap memo.

### Notes For ChatGPT Review

- Do not treat the Chapter 70 or Massachusetts teacher-arbitration claims as verified facts; they are explicitly flagged as background/analyst judgment pending direct verification.
- Do not recommend a GABRIEL run, an OEWS/DESE build, or ingestion as the immediate next step from this state; the recommended next step is closing source gaps and reviewing existing corpus CBAs for already-available teacher salary-schedule evidence.
- Do not merge teacher assistant/paraprofessional data or BLS categories into teacher-specific figures in any future work.

---

## 2026-07-04T10:41:22-04:00 - Police/fire workforce context refinement and source-gap list created

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_workforce_context_refinement_2026-07-03.md`
  - `docs/analysis/police_fire_workforce_context_source_gaps_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv` (refined H2, H6, H11 rows only; schema and row count unchanged; no new hypothesis rows added)
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No model/API calls, and no Harvard proxy calls, were made from project scripts.
- No OEWS/BLS data was downloaded or processed; no wage-trend panel or figures were built.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- This was explicitly a context-building/hypothesis-refinement session, not a data-build or GABRIEL session.

### What This New Package Does

- Deepens four areas the PI asked for more nuance on: (1) police applicant supply/recruitment/retention/morale, with an explicit disentangling of the George Floyd/BLM legitimacy channel from COVID-era labor disruption, pension-vintage retirement timing, and the broad 2021-2023 Great Resignation; (2) firefighter wage pressure vs. public esteem, the career/volunteer distinction, and why firefighter median pay can be lower than police despite EMT/training credentials, without implying anything about relative training quality; (3) non-safety counterexamples (nursing, transit, sanitation, public works, teachers) with an explicit statement of what plausibly still differs for public safety (zero-deferability at the moment of the call, the no-strike-for-interest-arbitration institutional trade-off); (4) the interest-vs-grievance arbitration distinction and the evidentiary logic (bunching/centering test, criteria-correlation test, conventional-vs-final-offer comparison) for telling split-the-difference behavior apart from criteria-applying behavior.
- Every claim not already backed by a citation in the existing mechanism memo/bibliography is explicitly flagged as "background/analyst judgment, not yet source-verified" rather than given an invented citation, and routed into the new source-gap list.
- Adds a claim/counterpoint/evidence-needed table and specific textual-signal guidance for future GABRIEL/source extraction, without prototyping or running any new attribute.

### Hypothesis Matrix Changes

- H2 (`post-2020 policing climate shock`): counterpoint and textual-signal fields now require the text to name a specific channel (legitimacy/scrutiny vs. COVID hiring disruption vs. retirement-eligibility timing vs. general labor-market competition) rather than scoring any post-2020 staffing mention as legitimacy-channel evidence.
- H6 (`arbitration or impasse backstop`): counterpoint field now names the no-strike/interest-arbitration statutory trade-off (e.g., MA JLMC) as the sharper, more checkable comparison to non-safety bargaining regimes, and adds award-level (offer/offer/award) capture guidance for a later bunching/centering test.
- H11 (`volunteer to career transition pressure`): now states the three-channel, lagged transmission mechanism explicitly (combination-department conversion, overtime/minimum-staffing substitution, full professionalization) so future evidence coding maps document type to the right channel.
- No new hypothesis rows were added; schema (12 columns, `hypothesis_id` through `priority`) is unchanged.

### Source-Gap List Highlights

Eight gaps identified, each with why-it-matters, likely source families, and a feasibility tag (`desk_research_feasible` / `data_build_feasible` / `likely_hard`): police applicant counts over time, police resignation/retirement series, firefighter applicant trend evidence, firefighter volunteer recruitment/retention evidence, training-cost/training-time evidence, overtime/vacancy budget reports with non-safety comparisons, arbitration award behavior/split-the-difference evidence, and the already-planned wage-trend baseline (listed for completeness only, not to be started from this session).

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Close the highest-value source gaps first: a direct (non-AP-summary) PERF/IACP staffing-survey citation with a multi-year applicant trend, an NFPA/FPRF or NVFC citation on volunteer-firefighter headcount trends, and one or two arbitration-behavior sources that speak directly to the split-the-difference-vs-criteria debate.
2. Only after that source base is stronger, revisit which sharpened hypotheses are worth a dedicated GABRIEL attribute.
3. Keep the OEWS/ASPEP descriptive wage-trend baseline as the next data-build step, separate from this mechanism-refinement lane.

### Notes For ChatGPT Review

- Do not treat the "background/analyst judgment, not yet source-verified" claims in the new refinement memo as sourced facts; they are flagged precisely because they still need a real citation.
- Do not recommend a GABRIEL run, an OEWS/ASPEP build, or ingestion as the immediate next step from this state; the recommended next step is closing source gaps first.
- Do not generalize the Massachusetts JLMC no-strike/interest-arbitration institutional case into a claim about national arbitration practice.

---

## 2026-07-03T15:55:58-04:00 - OEWS/ASPEP descriptive wage-trend baseline plan prepared

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_trend_baseline_implementation_plan_2026-07-03.md`
  - `docs/analysis/police_fire_wage_trend_occupation_crosswalk_2026-07-03.csv`
  - `docs/analysis/police_fire_wage_trend_baseline_note_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.
- The prior mechanism-synthesis work was already committed as `0cd3e91`, so no cleanup commit was needed before this run.

### What This New Package Does

- Turns the earlier trend-data concept memo into an implementation-ready OEWS/ASPEP baseline plan with exact official source entry points.
- Specifies the first-pass geography set: national, Massachusetts, and Boston-Cambridge-Newton, MA-NH.
- Specifies the first-pass occupation set and flags where the mapping is clean versus proxy-based.
- Makes explicit that OEWS and ASPEP are descriptive occupation/function sources, not bargaining-unit wage sources.

### Key Source Choices

- OEWS annual tables page: `https://www.bls.gov/oes/tables.htm`
- OEWS state estimates page: `https://www.bls.gov/oes/current/oessrcst.htm`
- OEWS metro/nonmetro page: `https://www.bls.gov/oes/current/oessrcma.htm`
- ASPEP tables page: `https://www.census.gov/data/tables/2025/econ/apes/annual-apes.html`
- ASPEP datasets page: `https://www.census.gov/data/datasets/2025/econ/apes/annual-apes.html`
- ASPEP methodology page: `https://www.census.gov/programs-surveys/apes/technical-documentation/methodology/annual/2025.html`
- ASPEP table IDs selected for the first pass:
  - `GOVSEMPTIMESERIES.GS00EMP01`
  - `GOVSEMPTIMESERIES.GS00EMP02`
  - `GOVSEMPTIMESERIES.GS00EMP03`

### Occupation Mapping Position

High-fit first-pass mappings:

- police -> `33-3051` Police and Sheriff's Patrol Officers
- fire -> `33-2011` Firefighters

Useful but imperfect comparison mappings:

- teacher -> elementary and secondary teachers
- clerical_admin -> Office Clerks, General
- public_works -> Maintenance and Repair Workers, General
- sanitation -> Refuse and Recyclable Material Collectors
- transit -> Bus Drivers, Transit and Intercity

The package is explicit that `clerical_admin` and especially `public_works` are proxy mappings rather than exact municipal-unit representations.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Implement the first descriptive OEWS panel for the selected occupations and geographies.
2. Add ASPEP function-based context for police protection, fire protection, education, and other relevant functions.
3. Keep the interpretation descriptive and reserve bargaining-unit wage construction for separate CBA/payroll work.

## 2026-07-03T15:14:25-04:00 - PI-facing synthesis and source-QC pass completed

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_mechanism_synthesis_for_pi_2026-07-03.md`
- Updated:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.

### Source-QC Findings

- The bibliography now distinguishes between authoritative federal/state references, institutional-context sources, and illustrative secondary sources.
- The AP article summarizing the PERF staffing survey is retained only as an illustrative source and should be replaced with the direct PERF release before formal citation.
- BLS and Census landing-page references are fine for planning, but some entries still need exact table/report links before external-facing use because the page year and underlying data year are not the same thing.
- The OOH and related entries are now annotated with access date and underlying data-year cautions.

### Analytical Position After This Entry

- The mechanism memo now reads more explicitly as a hypothesis map rather than an ordered explanation.
- Comparability remains important, but the PI-facing framing is now broader: police/fire wage growth may reflect multiple interacting mechanisms rather than a single comparator story.
- The synthesis memo explains why police and fire may differ from each other and why non-safety comparison is part of mechanism definition, not just a robustness check.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

1. Replace indirect or illustrative bibliography items with exact primary citations where available.
2. Build the first descriptive OEWS/ASPEP baseline.
3. Keep broader-state mechanism discovery small and curated before any new GABRIEL design or run decision.

## 2026-07-03T14:02:03-04:00 - Broader police/fire wage mechanism memo package created

**Commit:** pending in current session

### Current State After This Entry

- Created:
  - `docs/analysis/police_fire_wage_mechanism_context_2026-07-02.md`
  - `docs/analysis/police_fire_wage_mechanism_sources_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_hypothesis_matrix_2026-07-02.csv`
  - `docs/analysis/police_fire_wage_trend_data_plan_2026-07-02.md`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- The new memo explicitly steps back from implementation and develops competing police/fire wage mechanisms, counterarguments, and evidence requirements.
- No live GABRIEL calls were run.
- No ingestion happened.
- No production corpus files, `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `inbox/` were modified.

### Analytical Position After This Entry

- v9 remains a descriptive `comparability_emphasis` baseline with strong source-type confounding.
- v10 remains a useful institutional-pathway concept, but only one mechanism among several.
- The broader mechanism space now includes recruitment/retention pressure, post-2020 policing climate, hazard/work burden, overtime spirals, political salience, fiscal capacity, credentialing/training barriers, volunteer-to-career fire pressure, and union/institutional leverage.
- The memo now treats each mechanism with an explicit counterpoint and a note on what evidence would distinguish it from alternatives.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Step

Stay in mechanism-development mode:

1. build a first descriptive OEWS/ASPEP trend baseline;
2. add a small broader-state public snippet set for mechanism discovery;
3. only then revisit whether new GABRIEL attributes should be prototyped from this expanded mechanism map.

## 2026-07-01T23:33:27-04:00 - Thursday report package integrated around Boston bounded built-in web success

**Commit:** pending in current session

### Current State After This Entry

- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`
- Integrated the successful Boston graduated built-in GABRIEL web retry into the Thursday report package.
- The live finding is no longer framed as blocked.
- No additional live web-search or GABRIEL model/API calls were run in this integration session.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### Final Thursday Message

Built-in GABRIEL web mode works on a bounded Boston source-discovery query through the Harvard proxy, but larger structured extraction prompts need incremental tuning for stability.

### Integrated Result Summary

- `openai-gabriel` installed/imported: yes
- version: `1.1.8`
- built-in web path confirmed: `gabriel.whatever(web_search=True)`
- large Boston prompt: failed with connection errors
- minimal diagnostics: all succeeded
- graduated Boston retry:
  - attempt 1 failed
  - attempt 2 succeeded
  - attempt 3 skipped
- source rows: 1
- extraction rows: 1
- returned source: BPS `BTU Contract Negotiations` page
- URL preserved: yes
- Boston BTU/BPS material rediscovered: yes
- ingestion: no

### Recommended Next Step

Boston-only structured extraction tuning, one dimension at a time:

1. prompt size
2. output cap
3. source metadata handling
4. timeout behavior

### Notes For ChatGPT Review

- Do not recommend more live GABRIEL calls in the immediate next step beyond Boston-only structured tuning.
- Do not recommend a five-city pilot, all-32 v10, ingestion, PRRs, PDF generation, or slide generation from this state.
- Do not convert the one successful live retry into a numeric chart.

---

## 2026-07-01T18:42:30-04:00 - Boston graduated built-in GABRIEL web retry succeeded on attempt 2

**Commit:** pending in current session

### Current State After This Entry

- Created and ran:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py`
- Created graduated retry artifacts:
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_graduated_retry_2026-07-01/`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_sources_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_boston_graduated_retry_extractions_2026-07-01.csv`
  - `docs/analysis/gabriel_builtin_web_boston_graduated_retry_2026-07-01.md`
- Updated Thursday draft, PDF-ready report, and presentation outline.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.
- No five-city live pilot, all-32 v10 run, production dataset creation, PRR recommendation, or causal claim was made.

### Attempts Run

| Attempt | Result |
| --- | --- |
| 1 tiny Boston report | ran; failed with a connection error and no response |
| 2 source discovery only | ran; succeeded with non-empty response and a parseable source URL |
| 3 small attribute extraction | skipped after attempt 2 succeeded |

Returned source: BPS `BTU Contract Negotiations` page, `https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations`.

Counts:

- Source rows: 1.
- Working extraction rows: 1.
- URLs/citations preserved: yes, parseable URL in response text.
- Boston BTU/BPS material rediscovered: yes.
- Ingestion: no.

### Interpretation

Built-in GABRIEL web mode works on a small Boston source-discovery query through the Harvard proxy. The earlier larger Boston failure was not reproduced by the graduated retry, but attempt 1 still hit a connection error, so transient connection behavior remains possible. Larger structured extraction/output shape should be tuned incrementally before any broader pilot.

### Recommended Next Step

Keep the next run Boston-only and tune one dimension at a time: prompt size, output cap, source metadata handling, and timeout behavior. Do not run a five-city live pilot or ingestion until a small Boston structured-output path is stable.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_builtin_web_boston_graduated_retry.py
passed
```

---

## 2026-07-01T18:27:47-04:00 - GABRIEL/OpenAI proxy web-connectivity diagnostic completed

**Commit:** pending in current session

### Current State After This Entry

- Created a minimal diagnostic runner:
  - `analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py`
- Created diagnostic outputs:
  - `analysis/gabriel_pilot/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.csv`
  - `docs/analysis/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.md`
- Updated Thursday-facing reports with a short diagnostic note.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.
- No full Boston web-search prompt, five-city live pilot, all-32 v10 run, production dataset creation, PRR recommendation, or causal claim was made.

### Diagnostic Tests Run

All tests used tiny prompts and sanitized result logging only.

| Test | Result |
| --- | --- |
| Raw OpenAI proxy, no web tools | succeeded |
| GABRIEL non-web call | succeeded |
| GABRIEL `whatever(web_search=True, search_context_size="low")` | succeeded in final bounded diagnostic |
| Raw OpenAI Responses API `tools=[web_search]` | succeeded with status `completed` |

The final diagnostic result category is **unknown**. The earlier Boston smoke-test failure was not reproduced by the minimal proxy/non-web/web-tool checks, so the result no longer supports a persistent proxy wiring problem, ordinary `openai-gabriel` proxy compatibility problem, or raw hosted web-search-tool support problem.

### Recommended Question For Hemanth / Harvard Proxy Support

Can the Harvard HUIT OpenAI proxy support longer Responses API hosted web-search requests from `openai-gabriel`, including `include=["web_search_call.action.sources"]`, domain filters, and `extra_headers`, and are there proxy-side timeout/body-size/logging limits that could explain why the larger Boston `gabriel.whatever(web_search=True)` run produced repeated connection errors while the tiny diagnostic succeeds?

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/diagnose_gabriel_proxy_web_connectivity.py
passed
```

---

## 2026-07-01T12:09:13-04:00 - openai-gabriel installed; Boston built-in web call failed with connection errors

**Commit:** pending in current session

### Current State After This Entry

- `openai-gabriel` was installed into the active project virtual environment.
- `import gabriel` now succeeds.
- Built-in web mode is callable by signature through `gabriel.whatever(web_search=True, web_search_filters=..., search_context_size=...)`.
- A Boston-only built-in web smoke test was attempted through the native `gabriel.whatever(web_search=True)` path.
- The live call did not return a response: GABRIEL recorded `Successful=False` and three connection errors.
- No source URLs, citations, snippets, page text, or model web summary were returned.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### Install/Import Result

- Install command: `python -m pip install openai-gabriel`.
- First sandboxed install attempt failed due DNS resolution for `pypi.org`.
- Escalated install succeeded.
- Installed package/version: `openai-gabriel` 1.1.8.
- Imported module: `.venv/lib/python3.11/site-packages/gabriel/__init__.py`.
- Exposed functions: `whatever`, `extract`, `rate`, and `classify`.

### Signature Result

- `gabriel.whatever`: explicit `web_search`, `web_search_filters`, `search_context_size`, `save_dir`, `column_name`, `identifier_column`, `model`, `n_parallels`, and `reset_files`.
- `gabriel.extract`: explicit `modality`; `web_search`, `web_search_filters`, and `search_context_size` available via kwargs; `save_dir`, `column_name`, `model`, `n_parallels`, and `reset_files` explicit.
- `gabriel.rate` and `gabriel.classify`: explicit `modality` and `search_context_size`; web controls available via kwargs.

### Credential/Proxy Handling

- Only credential presence was checked; no values were printed.
- `HARVARD_SUBSCRIPTION_KEY` is present via `.env`.
- `OPENAI_API_KEY` and `OPENAI_BASE_URL` were not present before runtime mapping.
- The runner passed the Harvard key at runtime as GABRIEL `api_key`, the Harvard proxy base URL as `base_url`, and the Harvard subscription header through `extra_headers`.
- No key was written into code or committed.

### Boston Smoke-Test Result

- Runner created: `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`.
- Path used: `gabriel.whatever(web_search=True)`.
- Identifier: `gabriel_builtin_web_boston_btu_2026_07_01`.
- Model/search context: `gpt-5.4-nano`, `search_context_size="low"`.
- Scope: one Boston BPS/BTU public-source prompt.
- Result: failed API/web call; empty response.
- Raw GABRIEL result: `Successful=False`; `Error Log=["Connection error.", "Connection error.", "Connection error."]`; `Web Search Sources` empty.
- Source rows: 0.
- Extraction rows: 0.
- Boston BTU/BPS salary-comparison material rediscovered: no.
- URLs/citations preserved: no, none returned.

### Artifacts

- Created:
  - `analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_dataframe.csv`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/gabriel_whatever_raw.csv`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/gabriel_whatever_raw_run_metadata.json`
  - `analysis/gabriel_pilot/builtin_web_smoke_boston_2026-07-01/raw_response.txt`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_sources_2026-07-01.csv`
  - `analysis/gabriel_pilot/results_gabriel_builtin_web_smoke_boston_extractions_2026-07-01.csv`
- Updated:
  - `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Dependency Decision

`requirements.txt` was not modified. The package installed and imported, but the built-in web call did not successfully return a response; pinning `openai-gabriel` should wait until the Harvard proxy/web-mode issue is resolved.

### Recommended Next Step

Ask Hemanth/toolkit creator whether `openai-gabriel` built-in web mode is expected to work through the Harvard HUIT proxy with Responses API web-search tools and `extra_headers`, or whether the smoke test needs a standard OpenAI endpoint/key environment. Then rerun only the same Boston prompt.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_builtin_web_smoke_boston.py
passed
```

---

## 2026-07-01T13:30:00-04:00 - built-in GABRIEL web smoke test blocked locally by missing package

**Commit:** pending in current session

### Current State After This Entry

- A Boston-only built-in GABRIEL web smoke test was checked but not executed.
- Built-in GABRIEL web mode remains the primary live path conceptually.
- The local Python environment does not currently expose an importable `gabriel` package, so the built-in path could not be called here.
- No live web search was run.
- No ingestion happened.
- No production data, corpus, inbox, or coverage files were modified.

### What Was Checked

- `import gabriel`: failed; no module found.
- `python -m pip show gabriel GABRIEL gabriel-toolkit gabriel-ai`: no installed package found.
- Repo search: no vendored GABRIEL package and no local tutorial notebook found.
- `/mnt/data`: not present in this session, so no uploaded tutorial notebook was available there.
- Existing pilot code: current runners use direct OpenAI calls over local text; no built-in GABRIEL web invocation exists in the repo.

### Availability Result

- `gabriel.whatever`: unavailable here.
- `web_search=True`: could not be tested.
- `web_search_filters`: could not be tested.
- `search_context_size`: could not be tested.
- `modality="web"`: could not be tested.
- `gabriel.extract`: unavailable here.
- `gabriel.rate`: unavailable here.
- `gabriel.classify`: unavailable here.

### What Changed

- Created:
  - `docs/analysis/gabriel_builtin_web_smoke_test_status_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Status Counts

- Boston smoke test ran: no.
- GABRIEL web path used: none; package unavailable.
- Source rows created: 0.
- Extraction rows created: 0.
- Boston BTU rediscovered: no live test ran.
- URLs/citations preserved: none returned.
- Ingestion performed: no.
- Code added: no.

### Recommended Next Step

Ask Hemanth/toolkit creator for the installable/importable GABRIEL package version or the exact environment where the tutorial web-mode calls are available. Then rerun only the Boston smoke test, starting with `gabriel.whatever(..., web_search=True, search_context_size="low")` if available, otherwise the supported `gabriel.extract(..., modality="web")` route.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

---

## 2026-07-01T13:20:00-04:00 - all-repo declutter plan and manifest created

**Commit:** pending in current session

### Current State After This Entry

- An all-repo declutter audit was completed.
- The scope was the full repo, not only the GABRIEL web-search area.
- No files were moved, deleted, or renamed.
- A narrative repo-wide declutter plan was created.
- A candidate manifest CSV was created with path-level recommended actions, timing, risk, and dependency notes.

### What Changed

- Created:
  - `docs/analysis/repo_declutter_plan_2026-07-01.md`
  - `docs/analysis/repo_declutter_candidate_manifest_2026-07-01.csv`
- Updated:
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Main Recommendation

- Keep production data, corpus, inbox, ingestion code, validation scripts, and spend logs visible and untouched.
- Keep active v9 analysis code/results and current Thursday report-facing files visible.
- Archive Thursday-only support artifacts after the Thursday package is finalized.
- Archive v10 dry-run branch artifacts and legacy generated pilot outputs only after the v10/web-search branch stabilizes.
- Treat `docs/acquisition/`, comparator memos, session snapshots, and older report exports as provenance-preserving archive candidates rather than disposable clutter.

### Recommended Next Step

User review of the declutter categories and candidate archive layout before any actual archive operation.

### Status Checks

- Files deleted: no.
- Files moved: no.
- Files renamed: no.
- Live web search executed: no.
- Ingestion performed: no.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

---

## 2026-07-01T12:00:00-04:00 - tutorial clarified built-in web mode; report framework corrected

**Commit:** pending in current session

### Current State After This Entry

- The tutorial clarification changed the live-path framing materially.
- Built-in GABRIEL web mode is now treated as the primary live path.
- The custom `get_all_responses_fn` scaffold is now treated as a fallback and advanced schema-control path.
- The Thursday report draft, PDF-ready report, presentation outline, and custom-function memo were updated to reflect that change.
- A repo declutter/archive plan was created.
- No live web search was executed.
- No ingestion happened.

### What Changed

- Created:
  - `docs/analysis/gabriel_tutorial_web_mode_note_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_repo_declutter_plan_2026-07-01.md`
- Updated:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
  - `docs/analysis/chatgpt_handoff_latest.md`
  - `PROGRESS.md`

### Framework Correction

- Primary live path: built-in GABRIEL web mode.
- Report-first route: `gabriel.whatever(..., web_search=True)`.
- Extraction route: `gabriel.extract` or structured parsing on built-in web reports.
- Fallback route: custom `get_all_responses_fn` only if built-in outputs are not structured enough or if tighter schema control is needed.
- Project gap: the repo had not yet wired built-in web mode into the city-by-city source/extraction schema.

### Recommended Next Step

Run a Boston-only built-in GABRIEL web smoke test after confirming the exact invocation details and output structure in this project environment.

### Status Checks

- Files deleted: no.
- Files moved: no.
- Live web search executed: no.
- Ingestion performed: no.
- Seed counts unchanged: 5 city responses, 15 source rows, 34 extraction rows.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

---

## 2026-07-01T10:43:43-04:00 - live smoke test skipped; no safe backend available

**Commit:** pending in current session

### Current State After This Entry

- A bounded one-city Boston live smoke test was considered.
- The live smoke test was not executed because no safe repo-local search backend or approved search API client was available.
- Seed mode remains the current executable demonstration.
- No live result CSVs were created.
- No ingestion happened, and no production corpus files were modified.

### Backend Inspection Result

- `requirements.txt` has no search API dependency.
- Installed-package probes found no SerpAPI, Serper, Brave, Tavily, Exa, Google API client, DuckDuckGo wrapper, or similar search client.
- The active shell exposed no search-backend environment variable.
- The repo `.env` only advertised the Harvard HUIT OpenAI proxy key used by existing GABRIEL scoring and optional LLM span extraction.
- Session-level browser/search tools were not treated as a local callable backend for `custom_get_all_responses`.

### What Changed

- Created status memo:
  - `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- Added concise `Optional live smoke test` notes to:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated this handoff log and `PROGRESS.md`.

### Status Checks

- Live web search executed: no.
- Backend used: none; no safe backend locally available.
- Source rows created: 0.
- Extraction rows created: 0.
- Ingestion performed: no.
- Code added: no.

### Recommended Next Step

Ask the toolkit creator to confirm the actual backend adapter or provide an approved search API/client matching the proposed `web_search` contract before any live smoke test or five-city live pilot.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

---

## 2026-07-01T00:35:00-04:00 - Thursday report polish completed

**Commit:** pending in current session

### Current State After This Entry

- The main Thursday report draft has been polished for a toolkit-creator meeting.
- A shorter PDF-ready markdown companion now exists.
- The presentation outline now includes a worked JSON example and explicit Thursday decision points.
- No live web search was executed.
- No ingestion happened.

### What Changed

- Polished main report draft:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created PDF-ready abbreviated version:
  - `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Updated presentation outline:
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- Updated this handoff log and `PROGRESS.md`.

### Main Polish Changes

- Added a short `What we built` section near the top.
- Added a `What this is / what this is not` subsection.
- Added one short worked JSON payload example from the seed demo.
- Reframed the open integration section as `Adapter-fit points for Thursday`.
- Added a final `Thursday decision points` section.
- Tightened wording to sound less like an internal repo log and more like a meeting document.

### PDF-Ready Artifact

- Created: `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- Intended use: convert to PDF Wednesday night after final review.

### Status Checks

- Live web search executed: no.
- Ingestion performed: no.
- Seed counts unchanged: 5 city responses, 15 source rows, 34 extraction rows.

### Recommended Next Step

Convert the PDF-ready markdown to PDF Wednesday night after one final read for formatting and page length.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

---

## 2026-07-01T00:00:00-04:00 - Thursday report draft and presentation outline created

**Commit:** pending in current session

### Current State After This Entry

- The Thursday-facing report draft now exists and is presentation-ready in markdown.
- A short 9-slide presentation outline now exists as a separate markdown artifact.
- Report asset tables now exist under `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`.
- No live web search was executed.
- No ingestion happened.
- No production corpus tables or folders were modified.

### What Changed

- Created report draft:
  - `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- Created presentation outline:
  - `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- Created report asset tables:
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/city_seed_demo_summary.csv`
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/design_choices_table.csv`
  - `docs/analysis/gabriel_websearch_report_assets_2026-07-01/attribute_definitions_table.csv`
- Updated this handoff log and `PROGRESS.md`.

### Main Report Content

- Explains why city-by-city public-source discovery matters for the safety-wage project.
- States clearly that no built-in local GABRIEL web-search function was found.
- Documents the custom `get_all_responses_fn` scaffold and its callback signature.
- Explains the proposed live `web_search` backend contract and expected result keys.
- Summarizes the five-city seed demo, calibration examples, attribute definitions, guardrails, and bounded next-live-test plan.
- Frames the scaffold as acquisition/extraction assistance rather than production measurement.

### Seed Demo Snapshot Used In The Report

- Cities: Boston, Somerville, Newton, Wayland, Seekonk.
- City responses: 5.
- Source rows: 15.
- Extraction rows: 34.
- Live web search executed: no.
- Ingestion performed: no.

### Recommended Next Step

Review the Thursday report draft first, then convert it to PDF Wednesday night if the framing and level of technical detail look right.

### Validation/Audit Results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Corpus Snapshot

```text
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012, ma_newton_police_2015
```

### Recommended Next Codex Run

If the report framing is approved, do a presentation-polish pass only: tighten executive language, decide whether the callback section needs one worked JSON example, and prepare a PDF conversion artifact. Do not switch into live search or ingestion work unless separately authorized.

---

## 2026-06-30T22:05:00-04:00 - scaffold contract refined

**Commit:** pending in current session

### Current State After This Entry

- No live web search was executed.
- The scaffold still runs in seed/dry-run mode and now has a concrete proposed live backend contract.
- `Response` is always a parseable JSON string, regardless of `json_mode`.
- Streaming is explicitly unsupported for now.
- Extraction is conceptually inside `custom_get_all_responses`, but the current live path remains a discovery-only placeholder because no safe backend exists locally.

### What Changed

- Refined `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py` to assume:
  - `web_search(query: str, *, max_results: int = 5, domains: list[str] | None = None, city: str | None = None, state: str | None = None) -> list[dict]`
- Fixed the expected discovery result keys to:
  - `title`
  - `url`
  - `snippet`
  - `source_domain`
  - `published_date`
  - `retrieval_status`
- Added structured error fields in the JSON response:
  - `status`
  - `error_type`
  - `error_message`
  - `source_candidates`
  - `extractions`
  - `notes`
- Added evidence-origin helper fields to the JSON payload shape where feasible:
  - `search_snippet`
  - `page_text_excerpt`
  - `evidence_origin`
- Updated the prompt template and design memo to include domain filters and result caps.
- Re-ran the seed demo successfully.

### Seed Demo Snapshot

- Seed demo ran: yes.
- City responses written: 5.
- Parsed source rows written: 15.
- Parsed extraction rows written: 34.
- Row counts changed: no.
- Live web search executed: no.

### Default Domain Filters

- Boston: `bostonpublicschools.org`, `boston.gov`, `btu.org`, `mass.gov`
- Somerville: `somervillema.gov`, `somerville.k12.ma.us`, `mass.gov`, `somervilleeducators.com`
- Newton: `newton.k12.ma.us`, `newteach.org`, `mass.gov`
- Wayland: `wayland.ma.us`, `mass.gov`
- Seekonk: `seekonk-ma.gov`, `seekonkschools.org`

### Recommended Thursday Talking Points

- The contract is now concrete enough to discuss adapter fit with the toolkit creator.
- The intended design is two-stage and token-efficient:
  1. source discovery with URLs and snippets
  2. GABRIEL extraction only on retained candidates
- The hook returns a full dataframe only; no streaming or retry protocol is assumed.
- If the toolkit creator already has a different discovery object shape, the main question is whether to adapt the backend into this contract or revise the scaffold.

### Recommended Next Codex Run

If the toolkit creator confirms a backend callable, adapt only the live path in `custom_get_all_responses` and rerun the same five-city bounded pilot with domain filters and capped results. Otherwise, keep the current scaffold as the Thursday demonstration artifact and do not attempt live search.

---

## 2026-06-30T21:00:00-04:00 - custom GABRIEL web-search scaffold added

**Commit:** pending in current session

### Current State After This Entry

- The repo still has no built-in local GABRIEL web-search function.
- A custom `get_all_responses_fn` scaffold now exists for Thursday demonstration use.
- The scaffold defaults to seed/dry-run mode using the existing five-city pilot CSVs.
- No live web search was executed.
- No ingestion happened, and no production corpus files were modified.

### What Changed

- Created custom hook scaffold: `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py`.
- Created seed demo runner: `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`.
- Created design memo: `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`.
- Updated the pilot summary note in `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`.
- Ran the seed demo and wrote:
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
  - `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`

### Scaffold Status

- `custom_get_all_responses` implemented: yes.
- Required signature handled: `prompts`, `identifiers`, `json_mode`, `model`, `api_key`, `web_search`, `**kwargs`.
- Return shape: pandas dataframe with `Identifier` and `Response`.
- Default response mode: JSON payload string with `city`, `status`, `source_candidates`, `extractions`, and `notes`.
- Optional live path: placeholder only, bounded, off by default, and depends on a future callable `web_search` backend.

### Seed Demo Snapshot

- Seed demo ran: yes.
- City responses written: 5.
- Parsed source rows written: 15.
- Parsed extraction rows written: 34.
- Status: dry-run only; no live acquisition or search execution.

### Recommended Thursday Talking Points

- The local repo exposes direct model runners on local text, not a reusable web-search hook.
- The new scaffold shows the expected callback shape for city-by-city bounded source search plus extraction.
- The calibration harness is already attached through the 15 seeded source rows and 34 extraction rows.
- The toolkit creator still needs to specify the exact `web_search` callable contract, result schema, citation preservation behavior, and retry/rate-limit expectations.

### Recommended Next Codex Run

If the toolkit creator provides the real `web_search` backend shape, wire it into `custom_get_all_responses` and rerun only the same five-city pilot with strict result caps. If not, use the scaffold and memo as the Thursday integration discussion artifact and keep execution in seed mode only.

---

## 2026-06-30T18:55:45-04:00 - GABRIEL web-search extraction pilot seeded

**Commit:** pending in current session

### Current State After This Entry

- The v10 all-32 causal pilot is paused.
- The immediate priority shifted to a Thursday-facing GABRIEL web-search/source-extraction pilot.
- No local GABRIEL web-search function was found or executed.
- The repo contains GABRIEL scoring runners for local text inputs and ingestion fetcher scaffolding, but no safe city/query web-search interface that returns URLs, snippets, source classifications, or multi-attribute extractions.
- The pilot outputs are therefore design/seed artifacts from already known public leads and existing corpus metadata, not autonomous search results.
- No ingestion happened, and no production corpus files were modified.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Created source-discovery seed CSV: `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`.
- Created evidence-extraction seed CSV: `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`.
- Created presentation-ready summary memo: `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`.
- Created reusable city-search prompt template: `docs/acquisition/gabriel_websearch_city_prompt_template_2026-06-30.md`.
- Updated this handoff log and `PROGRESS.md`.

### Pilot Snapshot

- Pilot status: design/seed only; web-search function not executed.
- Cities covered: Boston, Somerville, Newton, Wayland, Seekonk.
- Source candidates retained: 15, with 3 per city.
- Extraction rows created: 34.
- Source families: BPS/BTU bargaining materials, Somerville police award packets, Newton teacher bargaining materials, Wayland JLMC/CBA sources, and Seekonk official archive CBAs.

### Calibration Status

- Boston BPS/BTU negotiations page was included as a seed calibration source, not rediscovered by local web search.
- Somerville police JLMC/arbitration materials were included as seed calibration sources, not rediscovered by local web search.
- Newton mechanism-proxy materials, Wayland fire JLMC, and Seekonk official CBA archive sources were included as seed checks for future live search.
- Boston BTU remains mechanism-proxy/discourse-lane evidence only; peer-wage comparison alone should not trigger `arbitration_or_impasse_backstop`.
- Ordinary grievance arbitration remains an exclusion boundary, illustrated with Wayland DPW and Seekonk DPW CBA rows.

### Open Decisions

- The toolkit creator needs to provide or expose the actual GABRIEL web-search invocation before this can become an executed acquisition assistant test.
- Future live runs should keep a hard cap by city and query, return source candidates before extraction, and preserve causal versus mechanism-proxy versus discourse lanes.
- Do not expand to ingestion until a separate ingestion task authorizes manual verification and pipeline processing.

### Recommended Next Codex Run

If the toolkit creator provides a callable GABRIEL web-search function, run the five-city pilot live using the template and compare returned sources against the seeded calibration rows. If no callable function is available, use the seed memo as the Thursday discussion artifact and ask for the missing web-search API shape: inputs, outputs, credentials, rate limits, and extraction schema.

---

## 2026-06-30T11:14:52-04:00 - v10 repaired gold retry completed

**Commit:** created by the session that added this entry; see latest `git log`

### Current State After This Entry

- The repaired v10 gold retry produced zero formal audit failures.
- Clean grievance-only traps stayed low.
- Clear positives stayed high.
- Boston BTU stayed at `0`, so peer-wage comparison alone still does not trigger v10.
- Arlington-style future reopener/impasse clauses scored `60`, which is an upper-middle result and remains an open construct-boundary issue.
- A small all-32 causal pilot is now reasonable, provided the run preserves source-type stratification and flags future reopener/impasse clauses for review.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Created repaired gold set: `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`.
- Created repair memo: `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`.
- Added path arguments to `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py` so repaired retries do not overwrite first-run files.
- Created repaired input: `analysis/gabriel_pilot/input_v10_gold_repaired_2026-06-30.csv`.
- Ran one bounded repaired retry.
- Created repaired retry results: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv`.
- Created repaired retry audit: `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_audit_2026-06-30.csv`.
- Created repaired retry report: `docs/analysis/gabriel_v10_gold_repaired_dryrun_report_2026-06-30.md`.
- Updated the v10 design memo, this handoff log, `PROGRESS.md`, and API spend log.

### Arlington Construct Decision

`ma_arlington_public_works_2018` is no longer coded as a `false_positive_trap`.

Final repaired coding:

- `gold_label = ambiguous`
- `expected_score_band = 26_50`
- `evidence_type = mediation_impasse`
- `boilerplate_grievance_arbitration_trap = no`
- `economic_terms_link = yes`

Reason: Article XXX is a future reopener clause that allows mediation/factfinding under Chapter 1078 if agreement cannot be reached and expressly references money issues. That is not grievance-arbitration boilerplate. It is also not a clean award-style positive because the text does not show that the process was invoked or that it resolved wages.

`ma_arlington_public_works_2015` was added as a second ambiguous future-reopener/impasse edge case with the same coding logic.

### Repaired Gold-Set Composition

- Total rows: 12
- Clear positives: 3
- Clear negatives: 3
- False-positive traps: 4
- Ambiguous / future-reopener edge cases: 2
- Mechanism-proxy rows: 1

Important repair:

- `ma_wayland_public_works_2020` was recoded from `clear_negative` to `false_positive_trap` because the full text has a grievance-and-arbitration procedure limited to interpretation/application of the agreement, with no successor-contract impasse signal.

### Repaired Retry Results

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | `100, 92, 78` | 90.0 | 78 | 100 |
| `clear_negative` | 3 | `10, 0, 0` | 3.3 | 0 | 10 |
| `false_positive_trap` | 4 | `5, 15, 10, 5` | 8.8 | 5 | 15 |
| `ambiguous` | 2 | `60, 60` | 60.0 | 60 | 60 |

Boundary results:

- Clean grievance-only traps stayed at or below `25`: yes.
- Clear positives stayed at or above `51`: yes.
- Clear negatives stayed at or below `25`: yes.
- Boston BTU mechanism-proxy negative stayed low: yes, score `0`.
- Future reopener/impasse cases landed in an upper-middle band: `60`, plausible but worth flagging.
- Formal audit failures: 0.
- Prompt revision recommended: no.

### Open Construct Boundary

The remaining design decision is whether future reopener clauses with mediation/factfinding and money-issue language should count as moderate v10 evidence even when the document does not show the process was invoked.

If the PI wants v10 to count only invoked backstops, add a stricter prompt rule before the all-32 run. Otherwise, keep the current prompt and flag these cases during review.

### Recommended Next Codex Run

Run a small all-32 causal pilot for `arbitration_or_impasse_backstop`, not a production dataset. Preserve the repaired prompt, write new v10-only outputs, stratify by `source_type`, and add a review flag for future reopener/impasse clauses.

---

## 2026-06-30T10:56:17-04:00 - v10 gold dry-run completed

**Commit:** `ed67ffa` (`Dry run v10 prompt on gold set`)

### Current State After This Entry

- Do **not** run the all-32 v10 causal pilot yet.
- The candidate `arbitration_or_impasse_backstop` prompt handled ordinary grievance-arbitration boilerplate reasonably well.
- The gold set needs repair around Arlington-style future reopener/impasse clauses before broader scoring.
- H1 remains plausible but underidentified; v9 and v10 both still require strong source-type caveats.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### What Changed

- Added bounded v10 gold-only runner: `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py`.
- Created gold-only input: `analysis/gabriel_pilot/input_v10_gold_2026-06-29.csv`.
- Ran one v10 dry-run on only the 11-row gold set.
- Created results: `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv`.
- Created audit: `analysis/gabriel_pilot/results_v10_gold_dryrun_audit_2026-06-29.csv`.
- Created report: `docs/analysis/gabriel_v10_gold_dryrun_report_2026-06-29.md`.
- Updated v10 design memo: `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`.
- Updated `PROGRESS.md` and `logs/api_spend_log.csv`.

### Dry-Run Design

- Scope: 11 hand-coded gold rows only.
- Not run on all 32 causal rows.
- Causal rows used existing local source text from `analysis/gabriel_pilot/input_v9.csv`.
- Boston BTU stayed in the separate mechanism-proxy lane and used only existing memo/locator context.
- No documents were ingested, downloaded, or added to `corpus/`.
- No v8/v9 outputs were modified.

### Results

| gold_label | n | scores | mean | min | max |
|---|---:|---|---:|---:|---:|
| `clear_positive` | 3 | `96, 96, 88` | 93.3 | 88 | 96 |
| `clear_negative` | 4 | `0, 10, 0, 0` | 2.5 | 0 | 10 |
| `false_positive_trap` | 4 | `20, 70, 10, 15` | 28.8 | 10 | 70 |

Boundary results:

- Clear positives all scored at or above `51`.
- Clear negatives all scored at or below `25`.
- Boston BTU mechanism-proxy negative scored `0`.
- Three of four false-positive traps stayed at or below `25`.
- Formal audit result: 10 of 11 rows passed.
- Retry run: no.

### Main Interpretation

The lone formal failure was `ma_arlington_public_works_2018`, which scored `70` despite being labeled as a false-positive trap. Manual inspection found that the full text contains an Article XXX duration/reopener clause referencing an impasse procedure with mediation/factfinding and money issues. That is not ordinary grievance-arbitration boilerplate.

This means the first dry-run did **not** clearly fail on the main feared prompt boundary. Instead, the Arlington row is probably a contaminated gold row or an unresolved construct-boundary case.

### Decisions Carried Forward

- Do not revise the grievance-arbitration exclusion based on this run; it worked on Boston SENA, Seekonk DPW, and Seekonk teachers.
- Do not proceed to an all-32 causal pilot yet.
- Resolve whether future reopener clauses with mediation/factfinding and money-issue language should count for v10.
- Improve the local v10 relevance screen before broader use; it over-filtered some JLMC/stipulated-award and impasse evidence.

### Checks

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3

python -m py_compile analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py
passed
```

### Recommended Next Codex Run

Repair the v10 gold set before any all-32 causal pass:

1. Inspect Arlington DPW Article XXX and decide whether future reopener/impasse clauses count.
2. Recode Arlington as ambiguous/weak-positive if those clauses count, or add a stricter prompt rule if only invoked backstops count.
3. Add at least one clean grievance-only DPW trap.
4. Add one or two future-reopener/impasse edge cases.
5. Run one bounded gold-set retry.

---

## 2026-06-29T22:13:16-04:00 - v10 gold set and first handoff created

**Commit:** `4ff2b57` (`Create v10 gold set and ChatGPT handoff`)

### State After This Entry

- The project had a reusable ChatGPT handoff for future planning.
- The immediate recommended next step was to dry-run the v10 prompt on the 11-row gold set before any broader `arbitration_or_impasse_backstop` pass.
- The main implementation risk was false positives from ordinary grievance-arbitration boilerplate in CBAs.

### Corpus Snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- City attributes rows: 3
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Exploratory adjacent matches: 0
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

### Research Interpretation

- H1 remained plausible but underidentified.
- GABRIEL v9 found its clearest `comparability_emphasis` signal in safety-side arbitration/award-style documents, especially the Somerville police awards.
- Ordinary CBAs and MOAs generally scored low on v9 comparability.
- The strongest non-safety peer-wage comparison found so far was the official Boston BTU bargaining page, but that evidence was mechanism-proxy/discourse-lane rather than causal-corpus reasoning text.
- The central caveat was source type and document production: explicit reasoning appears where institutions force it onto the page, not necessarily wherever it matters in bargaining.

### What Changed

- Created the first hand-coded v10 gold set: `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`.
- Created the gold-set memo: `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`.
- Created the first `docs/analysis/chatgpt_handoff_latest.md`.
- Added a gold-set pointer to `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`.
- Made a small filename-date cleanup in `docs/acquisition/ma_newton_somerville_boston_mechanism_source_plan_2026-06-26.md`.
- Updated `PROGRESS.md`.

### Gold-Set Composition

- Total rows: 11
- Clear positives: 3
- Clear negatives: 4
- False-positive traps: 4
- Ambiguous rows: 0
- Mechanism-proxy rows included: 1
- Main trap class: grievance-arbitration boilerplate in ordinary CBAs

Positive anchors:

- `ma_somerville_police_spsoa_2012`
- `ma_somerville_police_spea_2012`
- `ma_wayland_fire_jlmc_2020`

Negative/trap anchors:

- Wayland DPW and library ordinary CBAs
- Worcester fire safety-side negative
- Boston SENA, Arlington DPW, Seekonk DPW, and Seekonk teachers as arbitration-boilerplate traps
- Boston BTU bargaining page as a mechanism-proxy negative for peer-wage comparison alone

### Key Artifact Paths

- v9 preliminary report: `reports/6_25/v2/GABRIELv9_preliminary.pdf`
- Public-source strategy note: `docs/hypotheses_public_source_strategy_2026-06-24.md`
- Mechanism-source summary: `docs/analysis/mechanism_source_summary_2026-06-26.md`
- Boston BTU deep dive: `docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md`
- Comparator network design memo: `docs/analysis/comparator_network_design_2026-06-29.md`
- Comparator synthesis memo: `docs/analysis/comparator_edge_synthesis_2026-06-29.md`
- Comparator stub CSV: `docs/analysis/comparator_mentions_stub_2026-06-29.csv`
- v10 design memo: `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`
- v10 gold set CSV: `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- v10 gold set memo: `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`

### Open Decisions At This Point

- Whether the v10 attribute should stay causal-corpus-only for its first run, or whether a separate mechanism-proxy lane should be scored later.
- Whether the 11-row gold set was enough for prompt tuning, or whether a second-round set should add ambiguous edge cases.
- Whether the next empirical priority was a v10 pilot, more comparator extraction, or broader mechanism-source acquisition.

### Checks

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3 | cities: 9
healthy matched pairs: 12
  exact-cycle: 9
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

### Recommended Next Codex Run At This Point

Use the gold set to draft and test exact v10 prompt language against the 11 hand-coded rows, with special attention to keeping grievance-arbitration boilerplate near `0` to `1_25` and keeping Boston BTU negative despite its strong peer-wage content.
