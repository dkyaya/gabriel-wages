# Next Prompt - National Source Availability Scan

You are working in the gabriel-wages repo.

Confirm you are in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.

Use Codex. Treat repo files as source of truth. Do not assume prior chat context.

Goal: perform source-availability scans for tier-1 national expansion states from `docs/analysis/national_state_priority_rubric_2026-07-12.csv`, starting with Pennsylvania, New Jersey, Illinois, and New York. This is a source scan, not ingestion and not codify.

Rules:
- Do not use FOIA/PRR.
- Do not run GABRIEL/codify, Harvard Proxy, model, or API calls.
- Do not download or ingest sources unless bounded criteria are explicitly met by the task or reviewed in-session.
- Do not edit `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final report DOCX/PDF artifacts.
- Do not prepare a new report draft.
- Commit locally only. Do not push. Do not inspect/configure/remediate remotes.

Read first:
- `AGENTS.md`
- `docs/schema.md`
- `docs/analysis/national_corpus_expansion_preflight_2026-07-12.md`
- `docs/analysis/national_corpus_current_coverage_gap_audit_2026-07-12.md`
- `docs/analysis/national_state_priority_rubric_2026-07-12.csv`
- `docs/analysis/two_week_claim_driven_expansion_plan_2026-07-12.md`
- `docs/analysis/national_source_targets_2026-07-12.csv`
- `docs/analysis/hypothesis_tracker_2026-07-12.csv`
- `docs/analysis/claim_driven_source_needs_2026-07-12.csv`
- `docs/analysis/source_planning_csv_hygiene_standard_2026-07-08.md`
- `docs/analysis/recognition_clause_first_classification_standard_2026-07-08.md`

Tasks:
1. For each tier-1 state, scan public source availability for 3-5 target cities from `national_source_targets_2026-07-12.csv`.
2. Prioritize matched triads: police CBA, fire CBA, and at least one genuine non-safety/general municipal CBA in an overlapping cycle.
3. Record candidate URLs, source portal names, source family, expected source type, expected text quality, and recognition-clause/classification caveats.
4. Flag non-safety bottlenecks first. A city with safety sources but no plausible non-safety source should be marked as safety-only/institutional-contrast only.
5. Track whether public arbitration, factfinding, impasse, wage-study, or comparator sources are findable.
6. Produce one scan CSV and one scan memo per state.
7. Do not ingest until selection is reviewed or until the prompt gives bounded criteria for ingestion.
8. Do not run codify yet.
9. Run `python scripts/validate.py` and `python ingest/audit_coverage.py` to confirm data remains unchanged.
10. Update `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md`, then commit locally.

Expected outputs:
- `docs/analysis/national_source_scan_<state>_2026-07-12.csv`
- `docs/analysis/national_source_scan_<state>_2026-07-12.md`
- updated source-needs guidance if needed
- local commit only
