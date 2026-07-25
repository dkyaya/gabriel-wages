# Next task: targeted provisional-extraction QA before 1,000 documents

Start from the committed
`COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25` provisional layer.

1. Review only the 187 rows in
   `compensation_extraction_500_conflict_review.csv` against their bounded local
   page pointers.
2. Resolve two exact quantitative duplicates and one exact non-base-wage
   duplicate without deleting provenance.
3. Adjudicate the 83 potential same-key quantitative conflict groups as true
   conflicts versus distinct schedule cells/effective periods.
4. Adjudicate the 102 possible non-base-wage records currently in the
   quantitative lane; re-route rather than silently discard or promote them.
5. Recompute the 500-document QA decision without selecting new documents or
   running new extraction.
6. Authorize a 1,000-document run only if conflict rate is at most 2%, no
   unresolved base/non-base contamination remains, integrity QA stays green,
   and the matched police/fire/non-safety representation remains intact.

Keep URL access, downloads, OCR, ingestion, `gabriel.codify`, final merge,
wage-gap analysis, regression, remote inspection, and push closed.
