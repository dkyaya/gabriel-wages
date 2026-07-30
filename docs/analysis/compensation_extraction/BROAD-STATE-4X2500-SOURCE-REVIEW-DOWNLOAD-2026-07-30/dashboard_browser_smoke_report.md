# Dashboard browser smoke report

Status: **PASS**.

The built Vite dashboard was served locally at `http://127.0.0.1:4173/gabriel-wages/` and inspected with the available Playwright controller. The in-app browser-client runtime was unavailable, so the report records that fallback rather than claiming it was used.

Visible checks passed:

- the page loaded with zero console errors after repairing a missing-favicon 404;
- the map remains total scout coverage only and shows 16,887 scout-covered municipalities;
- the current stage is broad-state 4 × 2,500 source review/download complete;
- the queue shows 3,950 rows and 3,672 retained sources (3,248 PDF, 350 HTML, 74 other);
- four-lane PDF/text readiness is visibly next;
- global analysis readiness remains false;
- wage-gap readiness remains blocked pending normalization;
- causal readiness remains blocked pending matched structure;
- the current report link points to this source-review/download summary, while verification is historical;
- no stale verification-only state is presented as current.

The final regression also confirmed that legacy combined-readiness branches no longer render text-extraction instructions under the current PDF/text-readiness heading.

Playwright captured a full-page screenshot at `tmp/broad_state_4x2500_source_review_download_2026-07-30_logs/dashboard-smoke.png`; it remains a lightweight relay-only artifact and is not staged in Git.
