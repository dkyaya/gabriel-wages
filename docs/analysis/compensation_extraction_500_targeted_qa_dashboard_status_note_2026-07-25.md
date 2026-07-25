# Dashboard status note: targeted QA of provisional 500-document extraction

The dashboard phase is now
`compensation_extraction_500_targeted_qa_completed`.

The calibration card reports that all 187 targeted QA rows were processed,
three duplicate observations were canonicalized, 151 quantitative records were
rerouted to the non-base-wage shadow lane, and the unresolved conflict rate is
1.5217%. Corrected active counts are 920 quantitative, 1,181 qualitative-
mechanism, 177 mixed, 1,477 non-base-wage, and 90 reference/exclusion records.

The recomputed QA status is `pass`; `scale_1000_allowed` is true and the next
recommendation is `recommend_1000_document_extraction`. The dashboard also
states that the corrected ledgers remain provisional and are not analysis-
ready. No new extraction, GABRIEL/API call, OCR, ingestion, codification, wage-
gap calculation, or regression occurred in this QA task.

After the local commit, a plain `git push` is required by this task so the
GitHub Pages dashboard can receive the updated generated JSON and frontend.
The push outcome is recorded separately in the relay and final response.
