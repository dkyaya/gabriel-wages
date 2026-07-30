# Next task

After the repaired Pages deployment visibly passes, run `BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30` over the exact 2,940-row `text_extraction_ready_queue`. Use four independent staggered lanes, checkpoint every source, and write full extracted text only to ignored local artifact storage. Do not OCR, rate, ingest, or codify. Update dashboard/status/docs and repeat local plus public browser smoke validation.
