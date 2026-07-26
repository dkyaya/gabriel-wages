# Provisional cumulative 1,000-document extraction QA report

- Integrity QA: `fail`
- Corrected 500-document seed reused without GABRIEL: 500
- New schema-valid cases: 500 / 500
- Cumulative schema-valid cases: 1000 / 1,000
- Packet compliance: `true`
- Invalid observation pages: 0
- Duplicate observation IDs: 0
- Exact structured-content duplicates canonicalized: 9
- Quantitative conflict groups: 82
- Unresolved quantitative conflict groups: 25
- Unresolved conflict rate: 1.8560%
- Base/non-base contamination: 126
- Cumulative review rows: 215
- Unresolved cumulative review rows/groups: 151
- Active quantitative observations: 1347
- Active qualitative-mechanism observations: 1464
- Active mixed cases: 272
- Active non-base-wage observations: 2758
- Reference/exclusion cases: 173
- Another targeted QA required: `true`
- Beyond-1,000 recommendation: `blocked_by_integrity_qa_failure`

The 126 possible contamination records are active corrected-seed quantitative
records: 48 overtime, 37 stipend/premium, 19 leave, seven
education/certification, five reimbursement, five longevity, three healthcare,
and two benefits signals. They were not silently rerouted because bounded QA
must determine whether each record is non-base only, contains separable base
and non-base components, or is a terminology false positive.

The review ledger has seven resolved exact-duplicate groups, 82 quantitative
conflict groups, and 126 possible non-base quantitative rows. Twenty-five
conflict groups and all 126 routing rows remain unresolved. Nine duplicate
observations were canonicalized without deleting provenance.

The outputs are provisional and separate from final analysis inputs. No final
merge, ingestion, codification, wage-gap analysis, regression, URL access,
download, or OCR occurred.
