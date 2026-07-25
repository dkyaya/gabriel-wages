# Next task: resolve one frozen longevity-routing case and finish cumulative 1,000-case QA

The cumulative 1,000-document identity and packet selection remains frozen.
The repaired representative preflight passed 6/6, and 499 of the 500 new
cases now have strict semantic-schema-valid structured results. The corrected
500-case seed received zero model calls and must remain untouched.

The only live blocker is extraction case
`cex1000_150f3ac41a7919533b202cc2`. Ten bounded attempts were rejected because
longevity evidence was placed in the base quantitative array. Do not fabricate
or silently recode a response.

Next:

1. Preserve the selection SHA-256
   `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`
   and the existing 499-case resumable checkpoint.
2. Add a one-case, non-base-family response contract that requires any
   longevity-only evidence to appear in `non_base_wage_observations` with empty
   base quantitative and qualitative arrays. Validate this contract offline.
3. Run a single bounded preflight on the frozen longevity case. If it fails,
   stop again; do not coerce or fabricate data.
4. If it passes, request exactly that one case once under the validated
   contract. Do not resend any seed case or any of the 499 stored new cases.
5. After the checkpoint reaches 500/500, materialize cumulative provisional
   ledgers from the corrected 500-case shadow ledgers plus the 500 new results.
6. Compute duplicate-ID, bounded-page-pointer, quantitative-conflict, and
   base/non-base contamination QA before authorizing any further scale.

Keep the remaining readable parse-text pool closed until cumulative QA passes.
Continue to prohibit URLs, hosted search, downloads, OCR, scouts, source
review, verification, ingestion, `gabriel.codify`, final analysis merge,
wage-gap work, regressions, raw prompt/response retention, and durable-ledger
mutation.
