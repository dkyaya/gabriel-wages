# Dashboard remote Pages diagnostics

Read-only diagnostics identify GitHub Actions as the Pages build type for the public repository `dkyaya/gabriel-wages`. The Pages URL is `https://dkyaya.github.io/gabriel-wages/`; the default branch is `main`.

The latest inspected workflow run was `30268663334` for commit `24615facf4d2efd18e9976d0ae0033946cf71715`. Its build and deploy jobs both completed successfully, and the latest GitHub Pages deployment `5622927443` reported `success` for that exact commit. The workflow regenerates dashboard JSON, builds Vite, uploads `docs/dashboard/dist`, and deploys the uploaded artifact.

The stale screen was therefore not caused by an old branch, a failed workflow, or an untriggered Pages deployment. The deployed current-header contract itself used two historical fields: `project_phase_summary.current_phase` was hardcoded to “Scaled verification routing and source triage,” and the header vintage came from the scout-state table’s 2026-07-23 `last_updated` value. Newer memo and Tier C metadata existed in other JSON but did not control the visible header.

No remote setting was changed. No fetch, pull, remote reconfiguration, token output, or Pages API mutation occurred.
