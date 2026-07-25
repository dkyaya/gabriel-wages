# Targeted QA result: provisional 500-document compensation extraction

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-AND-DASHBOARD-PUSH-2026-07-25`

## Result

Targeted QA processed all 187 frozen review-queue rows without selecting new
documents or running a new extraction. Integrity QA remains a pass, the
recomputed scale QA passes, and the provisional layer now supports a future
1,000-document extraction run. This is an authorization for a separately run,
provisional extraction stage—not a final merge, ingestion, codification, or
analysis decision.

GABRIEL/API was not used. The resolver used existing structured fields and
bounded local evidence pointers only; it did not open URLs, download documents,
run OCR, or save full page/table text.

## Queue resolution

- Review rows: 187 / 187.
- Exact structured-content duplicate groups: two.
- Duplicate observations canonicalized: three (two quantitative and one
  non-base-wage). Every original row remains in its shadow ledger; inactive
  duplicates carry `duplicate_of` and `canonical_observation_id`.
- Quantitative conflict groups: 83.
  - 27 `non_base_wage_misroute`;
  - 26 `distinct_schedule_cell`;
  - 11 `distinct_classification_or_rank`;
  - five `distinct_effective_period`;
  - 14 `insufficient_evidence_needs_review`.
- Resolved conflict groups: 69.
- Explicitly unresolved conflict groups: 14.
- Revised unresolved conflict rate: 14 / 920 = 1.5217%.
- Queued possible base/non-base records resolved: 102 / 102, all routed to the
  explicit non-base-wage shadow lane.
- Total quantitative records rerouted: 151. This includes the 102 individually
  queued records and 49 additional records belonging to the 27 non-base-wage
  conflict groups.
- Unresolved base/non-base contamination: zero.

No observation was silently discarded, promoted, or demoted. The resolution
ledger records each action and the corrected shadow ledgers preserve original
IDs, original QA status, stable canonical IDs, routing provenance, and active
lane status.

## Corrected provisional layer

- Active quantitative observations: 920; source rows retained: 1,073.
- Active qualitative-mechanism observations: 1,181.
- Active mixed-case joins: 177; source mixed rows retained: 182.
- Active non-base-wage observations: 1,477; source rows retained: 1,478.
- Active reference/exclusion cases: 90.
- Invalid bounded page pointers: zero.
- Duplicate observation IDs: zero.
- Frozen identities: 500.
- Unit representation: 180 police, 120 fire, 200 non-safety.
- Stable matched non-safety comparison IDs: 200.

The five inactive corrected mixed rows are retained because rerouting removed
their last active quantitative member; their qualitative sub-records remain in
the qualitative ledger. Mixed evidence is still represented by separate
quantitative and qualitative records linked through stable join keys.

## Recomputed decision

Decision: `recommend_1000_document_extraction`.

The rule passes because integrity QA remains green, observation IDs and page
pointers are valid, the unresolved quantitative conflict rate is below 2%, no
base/non-base contamination remains unresolved, the matched police/fire/non-
safety design is intact, and corrected outputs remain separate provisional
shadow ledgers. Analysis readiness remains false.

The future 1,000-document run must remain bounded, resumable, and provisional;
reuse the corrected routing rules; preserve city × unit × negotiation-cycle
identity and matched non-safety opportunities; and stop before final merge.
OCR, URL access, downloads, ingestion, `gabriel.codify`, wage-gap analysis, and
regression remain prohibited unless separately authorized later.

## Key artifacts

- Resolution ledger: `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25/compensation_extraction_500_targeted_qa_resolutions.csv`
- Summary: `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25/compensation_extraction_500_targeted_qa_summary.json`
- Recomputed decision: `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25/compensation_extraction_500_recomputed_decision.json`
- QA report: `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25/compensation_extraction_500_targeted_qa_report.md`
