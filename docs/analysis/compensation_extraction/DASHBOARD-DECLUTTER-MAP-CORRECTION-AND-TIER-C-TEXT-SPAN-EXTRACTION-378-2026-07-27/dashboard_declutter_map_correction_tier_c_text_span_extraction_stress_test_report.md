# Stress-test report

- Immutable input, path, size, or SHA drift fails before local extraction.
- Non-ready, prior-excluded, non-retained, and Tier A/B/D rows cannot enter the text queue.
- PDF extraction is local non-OCR `pdftotext`; HTML extraction reads bounded local bytes and suppresses scripts/styles.
- Empty, low-density, bad-layer, noisy/shell, and error rows cannot enter the span queue.
- Exact spans are bounded, non-paraphrased, and validated against task-local artifact bytes.
- Dashboard tests reject any map metric selector beyond total scout coverage and require visible current report, next task, map date, and global closure.
- Completed resume validates without writing; missing required outputs fail closed.
