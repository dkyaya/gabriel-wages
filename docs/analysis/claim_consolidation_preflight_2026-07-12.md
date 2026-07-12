# Claim Consolidation Preflight — 2026-07-12

## Repository State

- Working directory confirmed: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
- Git status at start of run: `?? .claude/
?? tmp/`.
- Latest commit at start of run: `1cf2df6 Plan claim-centered corpus expansion`.
- Expected baseline confirmed: `data/contracts.csv` has 53 rows and `data/city_coverage.csv` has 53 rows.

## Input Files Found

All required input files were present before drafting claim artifacts:

- `AGENTS.md` — found (96 lines, 7825 bytes)
- `PROGRESS.md` — found (5751 lines, 535871 bytes)
- `docs/analysis/chatgpt_handoff_latest.md` — found (4390 lines, 361831 bytes)
- `docs/schema.md` — found (126 lines, 6824 bytes)
- `docs/analysis/claim_centered_corpus_expansion_strategy_2026-07-10.md` — found (102 lines, 10656 bytes)
- `docs/analysis/claim_register_template_2026-07-10.csv` — found (5 lines, 7083 bytes)
- `docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md` — found (145 lines, 24287 bytes)
- `docs/analysis/report_appendix_tables_2026-07-10.md` — found (117 lines, 13246 bytes)
- `docs/analysis/report_graph_audit_2026-07-10.md` — found (83 lines, 7742 bytes)
- `docs/analysis/report_evidence_layer_audit_2026-07-10.md` — found (133 lines, 6803 bytes)
- `docs/analysis/gabriel_codify_evidence_layer.csv` — found (1154 lines, 906806 bytes)
- `docs/analysis/gabriel_codify_excerpt_browser_latest.html` — found (588 lines, 1392924 bytes)
- `docs/analysis/report_assets/source_inventory_for_report_2026-07-10.csv` — found (38 lines, 8808 bytes)
- `docs/analysis/report_assets/city_mechanism_matrix_2026-07-10.csv` — found (704 lines, 208010 bytes)
- `docs/analysis/report_assets/mechanism_presence_by_state_2026-07-10.csv` — found (58 lines, 6342 bytes)
- `docs/analysis/report_assets/mechanism_presence_by_occupation_2026-07-10.csv` — found (153 lines, 20435 bytes)
- `docs/analysis/report_assets/mechanism_presence_by_state_occupation_2026-07-10.csv` — found (267 lines, 37674 bytes)
- `docs/analysis/report_assets/top_mechanisms_by_group_2026-07-10.csv` — found (57 lines, 12711 bytes)
- `docs/analysis/gabriel_codify_full_codebook_audit_2026-07-09.md` — found (55 lines, 10762 bytes)
- `docs/analysis/gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md` — found (65 lines, 10996 bytes)
- `docs/analysis/gabriel_codify_massachusetts_audit_2026-07-09.md` — found (61 lines, 11368 bytes)
- `docs/analysis/gabriel_codify_seekonk_wayland_audit_2026-07-10.md` — found (63 lines, 9644 bytes)
- `docs/analysis/gabriel_codify_expanded_texas_ohio_audit_2026-07-10.md` — found (98 lines, 8842 bytes)
- `docs/analysis/texas_ohio_expansion_ingestion_summary_2026-07-10.md` — found (107 lines, 10637 bytes)
- `docs/analysis/texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` — found (16 lines, 9629 bytes)
- `docs/analysis/san_antonio_police_bounded_ocr_recovery_2026-07-10.md` — found (54 lines, 7352 bytes)
- `docs/analysis/all_groups_wage_mechanism_audit_2026-07-06.md` — found (161 lines, 50448 bytes)
- `docs/analysis/pre_report_must_have_evidence_review_2026-07-06.md` — found (127 lines, 27174 bytes)
- `docs/analysis/wage_mechanism_evidence_checklist.md` — found (296 lines, 151556 bytes)
- `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md` — found (197 lines, 39893 bytes)
- `docs/analysis/all_groups_source_needs_2026-07-06.csv` — found (67 lines, 33215 bytes)
- `docs/analysis/source_planning_csv_hygiene_standard_2026-07-08.md` — found (28 lines, 2558 bytes)
- `docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md` — found (32 lines, 3486 bytes)

## Evidence-Layer Counts

- Evidence-layer file: `docs/analysis/gabriel_codify_evidence_layer.csv`.
- Total evidence rows: 781.
- Present rows: 293.
- Not-found rows: 488.
- Verified-present rows used for primary support: 284 (`evidence_status=present` and `viewer_verified=1`).
- Flagged/unverified present rows excluded from primary support: 9.
- Codified contracts in source inventory: 37.
- States represented in codified evidence: MA, OH, TX.
- Cities represented in codified evidence: Austin, Boston, Cincinnati, Cleveland, Columbus, Franklin, Georgetown, Houston, San Antonio, Seekonk, Somerville, Toledo, Wayland.

## Report Asset Availability

- `docs/analysis/report_assets/source_inventory_for_report_2026-07-10.csv` — parses cleanly (37 rows).
- `docs/analysis/report_assets/city_mechanism_matrix_2026-07-10.csv` — parses cleanly (703 rows).
- `docs/analysis/report_assets/mechanism_presence_by_state_2026-07-10.csv` — parses cleanly (57 rows).
- `docs/analysis/report_assets/mechanism_presence_by_occupation_2026-07-10.csv` — parses cleanly (152 rows).
- `docs/analysis/report_assets/mechanism_presence_by_state_occupation_2026-07-10.csv` — parses cleanly (266 rows).
- `docs/analysis/report_assets/top_mechanisms_by_group_2026-07-10.csv` — parses cleanly (56 rows).

The existing excerpt viewer is present at `docs/analysis/gabriel_codify_excerpt_browser_latest.html`; this run does not modify it.

## Claim Standards Applied

- Each claim must be bounded to the current corpus and its codified subset.
- Primary support can use only verified-present evidence-layer rows unless the claim itself is about a gap or false negative.
- `not_found` rows are treated as limitations or gap indicators, not proof of true absence.
- GABRIEL/codify evidence is binary presence evidence, not an effect-size estimate and not causal proof.
- Claims must include explicit reasoning, counterevidence or limitations, what would change our mind, source needs, and report-readiness status.

## Explicit Run Constraints

- No git push.
- No remote inspection, validation, creation, or configuration.
- No GABRIEL/codify calls, model calls, API calls, or Harvard Proxy calls.
- No new source collection, downloads, FOIA, or PRR.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final report DOCX/PDF artifacts.
