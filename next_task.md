# Next task: targeted QA for the cumulative 1,826-case readable parse-text layer

All 1,826 unique durable readable parse-text hashes are covered in a cumulative provisional layer. Integrity QA passes, but 37 under-specified quantitative conflict groups remain explicit at a 1.9372% rate. Perform targeted QA before any final provisional merge.

The next run should:

1. use `remaining_parse_text_conflict_review.csv` as the frozen review source;
2. review exactly the 37 `insufficient_evidence_needs_review` conflict groups using existing structured fields and bounded local evidence pointers only;
3. classify each as a distinct schedule cell, distinct effective period, distinct classification/rank, duplicate/same observation, non-base-wage misroute, true unresolved conflict, or insufficient evidence;
4. preserve all observation IDs, canonical duplicate provenance, case identities, mixed join keys, and page pointers;
5. write corrected cumulative shadow ledgers without overwriting the current provisional ledgers;
6. recompute duplicate-ID, page-pointer, conflict-rate, base/non-base, representation, and provenance QA;
7. keep unresolved groups explicit when bounded evidence cannot resolve them;
8. stop before final merge and require a separate authorization decision for any downstream ingestion or codification.

Do not select documents or run extraction. Default to no GABRIEL/API calls. Continue to prohibit URLs, hosted search, downloads, OCR, scouts, source review, verification, ingestion, `gabriel.codify`, final analysis merge, wage-gap work, regressions, and durable upstream-ledger mutation. OCR-later documents remain outside this layer.
