# Local dashboard browser smoke

Status: **passed**.

The in-app browser connection exposed no available browser, so the required visible check used the available Playwright controller against the locally served production build. The page loaded as **Municipal Labor Evidence Dashboard** with no application console errors.

Visible UI checks confirmed 16,887 scout-covered municipalities and the scout-coverage-only map; the retained/readiness history (3,672 retained, 3,248 PDF, 350 HTML, 74 other, 2,940 extraction-ready, 601 OCR later); the current 2,940-row text-extraction stage; 2,795 extracted OK; 145 bounded quality exceptions; 2,795 span-extraction-ready; and `BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30` as the next task. Wage-gap readiness remains blocked pending normalization, causal readiness remains blocked pending matched structure, and global readiness is not fully passed.

The current report link points to this wave's `text_extraction_summary.md`. A stale readiness-only transition found during the first smoke was repaired; the final smoke shows the four-lane exact-span transition and no longer shows the obsolete 3,672-file readiness instruction as current.
