# Provisional cumulative 1,000-document compensation extraction result

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-ONECASE-LONGEVITY-RESOLUTION-2026-07-25`

## Result

The frozen longevity case was resolved without changing the selected identity
or packet. A single one-case preflight and one live request both passed the
strict non-base-wage contract. The live result contains no quantitative or
qualitative sub-record, and its two longevity observations appear only in the
non-base-wage array.

The checkpoint now contains 500/500 unique strict-valid new cases. Joined with
the corrected 500-case seed, the cumulative provisional ledgers cover all
1,000 frozen document identities at a 100% case-level schema-valid rate.

## One-case controls

- Resolved case: `cex1000_150f3ac41a7919533b202cc2`.
- GABRIEL backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`.
- One-case preflight: 1/1 strict-valid.
- One-case live: 1/1 strict-valid.
- Total one-case requests: two.
- Other new cases resent: zero.
- Corrected seed calls: zero.
- Frozen selection SHA-256 preserved:
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.
- Packet: six pages and 5,999 bounded text characters.
- Raw prompts/responses, encoded images, full text, and full tables saved: zero.

## Cumulative provisional ledgers

- Cases: 1,000 / 1,000 schema-valid.
- Active quantitative observations: 1,347.
- Active qualitative-mechanism observations: 1,464.
- Active mixed cases: 272.
- Active non-base-wage observations: 2,758.
- Reference/exclusion cases: 173.
- Duplicate observation IDs: zero.
- Invalid bounded page pointers: zero.
- Exact structured-content duplicates canonicalized: nine observations across
  seven groups; provenance rows remain present and inactive duplicates point to
  canonical IDs.
- Quantitative conflict groups: 82.
- Structurally resolved conflict groups: 57.
- Unresolved quantitative conflict groups: 25.
- Unresolved quantitative conflict rate: 25 / 1,347 = 1.8560%.
- Matched representation: intact at 363 police / 237 fire / 400 non-safety.

## Integrity QA result

Decision: `blocked_by_integrity_qa_failure`.

The conflict rate is below the 2% scale threshold, but a stricter cumulative
scan identified 126 active quantitative records with possible non-base-wage
signals. All 126 are from the corrected 500-case seed, not the new 500 cases.
They consist of 48 overtime, 37 stipend/premium, 19 leave, seven
education/certification, five reimbursement, five longevity, three healthcare,
and two benefits signals.

The cumulative review ledger contains 215 rows: seven exact-duplicate groups,
82 quantitative-conflict groups, and 126 possible non-base quantitative
records. A total of 151 rows/groups remain unresolved: the 126 routing records
and 25 under-specified conflict groups.

The stricter cumulative scan is deliberately conservative. These records are
not silently rerouted because some may contain a genuine base-rate component
alongside non-base terminology. Targeted bounded QA must distinguish retention,
rerouting, splitting, reference-only evidence, and insufficient evidence.

## Scale decision

The cumulative layer is complete and provisional, but integrity QA fails.
Further readable parse-text extraction is not authorized. The next task is a
targeted, no-new-extraction QA pass over the 151 unresolved cumulative review
items, with special focus on the 126 base/non-base routing records. Final merge,
ingestion, codification, wage-gap analysis, and regression remain prohibited.

No URL access, hosted search, download, OCR, scout, source review, verification,
ingestion, codification, final merge, wage-gap work, regression, or causal claim
occurred.
