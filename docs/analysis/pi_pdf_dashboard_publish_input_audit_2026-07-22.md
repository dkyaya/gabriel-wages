# PI PDF and dashboard publication input audit — 2026-07-22

## Decision

PASS. Work began at `b9d698f9b44a38b68531bc808140ea6e5017c4c6` (`Prepare PI progress report and dashboard update`) on branch `main`. The tracked worktree was clean. The unrelated pre-existing untracked root `package-lock.json` was reported and will remain untouched and excluded from the commit and relay.

Exact ancestry checks passed for `b9d698f`, `3f2f815`, and `bef5077`.

## Report source

The sole content source for the PDF is:

- `docs/analysis/pi_progress_report_source_discovery_2026-07-22.md`

Supporting context was read from:

- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `docs/analysis/pi_progress_memo_short_2026-07-22.md`
- `docs/analysis/pi_meeting_talking_points_2026-07-22.md`
- `docs/analysis/post_pi_verification_plan_2026-07-22.md`
- `docs/analysis/dashboard_final_update_for_pi_2026-07-22.md`
- `docs/dashboard/README.md`

The PDF will not add new research claims or silently promote candidate-stage material. Candidate rows remain unverified source leads.

## Dashboard inputs

The existing-data rebuild uses only:

- `scripts/build_scout_yield_learning_report.py`
- `scripts/build_dashboard_data.py`
- the committed national municipality universe, scout queue, scout coverage, priority, and four-wave summary outputs referenced by those builders;
- the ten JSON outputs under `docs/dashboard/data/`.

The configured dashboard URL is:

`https://dkyaya.github.io/gabriel-wages/`

The committed Pages workflow builds the Vite application from `docs/dashboard/` when relevant files are pushed to `main`.

## Frozen metrics

| Measure | Current value |
|---|---:|
| Municipality/township universe | 35,589 |
| Successfully scout-covered municipalities | 794 |
| Candidate-positive municipalities | 612 |
| Parseable-empty municipalities | 182 |
| Failure-only municipalities | 20 |
| URL-bearing candidate queue rows | 1,602 |
| Future-scout eligible | 34,789 |
| Tier 1 eligible | 1,227 |
| Tier 2 eligible | 3,478 |

## Planned PDF outputs

- `docs/analysis/pi_progress_report_source_discovery_2026-07-22.pdf`
- `docs/dashboard/reports/pi_progress_report_source_discovery_2026-07-22.pdf`

The source copy will be the archival analysis artifact. The dashboard copy will be imported by the Vite frontend and linked in the dashboard footer as **PI Source-Discovery Progress Report PDF**.

## Local toolchain

- ReportLab 5.0.0 is available for deterministic local PDF generation.
- Poppler `pdfinfo` and `pdftoppm` are available for page, metadata, and full visual rendering checks.
- `pypdf` is available for page-count and text-presence validation.
- No package installation or network access is required.

## Boundary confirmation

This is reporting, PDF generation, dashboard publication, validation, commit, and authorized push only. No scout, worker run, live/API/model/hosted-search call, candidate URL opening or verification, source ingestion, GABRIEL codification, queue/coverage rebuild from new scout results, priority-methodology change, candidate promotion, wage-gap finding, or causal claim occurs.
