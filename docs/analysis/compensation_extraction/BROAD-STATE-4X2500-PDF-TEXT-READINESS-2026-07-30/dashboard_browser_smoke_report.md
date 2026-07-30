# Dashboard browser smoke report

Status: **passed**

The production dashboard built successfully and was served locally at `http://127.0.0.1:4173/gabriel-wages/?smoke=final2`. The preferred in-app Browser runtime was unavailable (`No browser is available`, with an empty browser inventory), so the authorized Playwright MCP fallback performed the rendered-UI smoke check.

Playwright confirmed that the dashboard loaded as **Municipal Labor Evidence Dashboard** with zero console errors and zero console warnings. The visible map remained total scout coverage only and showed **16,887** scout-covered municipalities.

The rendered current stage showed PDF/text readiness complete, **3,672** retained sources (**3,248 PDF**, **350 HTML**, **74 other**), and **2,940** text-extraction-ready sources (**2,577 PDF**, **291 HTML**, **72 other**). It also exposed **601 OCR-later**, **53 oversized/defer**, **17 encrypted/locked**, **0 corrupt/broken**, **45 shell/navigation-only**, **16 needs-review**, and zero unsupported/error rows.

The next task was visibly `BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30`. Global readiness was not shown as fully passed: wage-gap readiness remained blocked pending normalization and causal readiness remained blocked pending matched structure. The current report link targeted this wave's `pdf_text_readiness_summary.md` rather than stale PI content.

Two stale lower-page strings discovered in the first browser pass were repaired before the final pass: the prior statement that PDF/text readiness was still next and the old 378-file Tier C extraction queue. Neither appeared in the final rendered page.

Screenshot: `tmp/broad_state_4x2500_pdf_text_readiness_2026-07-30_logs/dashboard-pdf-text-readiness-smoke.png` (138 KiB viewport capture).
