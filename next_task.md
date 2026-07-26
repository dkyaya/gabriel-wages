# Next task: independent bounded review before any final provisional merge

The deterministic 1,826-case targeted conflict QA passed. It resolved 35 of 37
queued groups, retained two as explicitly unresolved, reduced the unresolved
rate to 0.1049%, and produced separate corrected provisional shadow ledgers
with zero duplicate IDs, invalid page pointers, or base/non-base contamination.

The next run should be a bounded independent review, not extraction. It should:

1. inspect the two remaining unresolved conflict groups using only their stored
   structured fields and bounded local page pointers;
2. verify the provenance-preserving reroute of the three temporary
   working-out-of-classification premium observations;
3. verify the one logical Wasco non-base-wage record reconstructed in the
   shadow ledger from a pre-existing embedded-newline CSV record split;
4. confirm all five newly canonicalized duplicate observations and all prior
   duplicate provenance remain intact;
5. compare shadow-ledger counts and hashes to the targeted-QA decision;
6. leave any unresolved ambiguity explicit rather than inventing schedule-cell,
   rank, step, pay-band, or effective-date distinctions; and
7. produce a separate authorization decision before any final provisional
   merge, ingestion, or codification.

Do not select documents, run extraction, call GABRIEL/API by default, or touch
OCR-later documents. Continue to prohibit URLs, hosted search, downloads, OCR,
scouts, source review, verification, ingestion, `gabriel.codify`, final
analysis merge, wage-gap work, regressions, causal analysis, and durable
upstream-ledger mutation.
