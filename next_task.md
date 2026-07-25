# Next task: repair and rerun the 1,000-document representative preflight

The cumulative 1,000-document selection is already frozen and must remain
unchanged. The corrected 500-case seed must remain untouched and must not be
sent to GABRIEL again.

Before any live extraction:

1. Add a focused regression fixture for a response that declares
   `mixed_ready` but omits either the quantitative or qualitative sub-record
   array.
2. Strengthen the strict response schema or prompt so disposition and array
   requirements are internally consistent without post-hoc fabrication.
3. Run all offline extraction tests.
4. Reconstruct and hash-check the existing frozen packets; do not select new
   identities.
5. Rerun the same six-path preflight only. It must achieve 6/6 strict semantic
   validity before `live_lanes_1000` is allowed.
6. If it passes, run only the 500 new cases resumably, then materialize the
   cumulative provisional ledgers and compute duplicate, page-pointer,
   conflict, and base/non-base contamination QA.

Continue to prohibit URLs, hosted search, downloads, OCR, scouts, source
review, verification, ingestion, `gabriel.codify`, final analysis merge,
wage-gap work, regressions, raw prompt/response retention, and durable-ledger
mutation.
