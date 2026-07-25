# Provisional 1,000-document compensation extraction: 499/500 new cases stored

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-PREFLIGHT-REPAIR-AND-LIVE-500NEW-2026-07-25`

## Result

The mixed-disposition repair succeeded at preflight: the exact same six
representative cases passed 6/6 strict semantic-schema validation, including
the previously failing conflict-prone case. Live extraction then ran only for
the frozen 500 new documents. The corrected 500-document seed was never sent
to GABRIEL.

Resumable passes produced 499 unique strict-schema-valid new-case results.
One case remained invalid after ten attempts because it repeatedly placed
longevity evidence in `quantitative_observations`. The validator rejected every
attempt. The runner therefore did not materialize cumulative lanes.

## Repair

- Added explicit strict-schema descriptions tying dispositions to required
  arrays.
- Added a prompt decision matrix for quantitative-only, qualitative-only,
  mixed, and non-base-only evidence.
- Added fail-closed semantic checks for both forms of incomplete `mixed_ready`.
- Added regression coverage for all four supported evidence-family outcomes.
- Added an explicit `--only-requires-gabriel yes` live guard.
- Added retry-only non-base routing hints derived solely from redacted
  validation errors; no raw response was read or retained.
- Preserved prior live request/timing metadata across preflight reruns.

## Frozen design and execution

- Selection: exactly 1,000 unique identities and content hashes.
- Seed: 500 corrected cases; GABRIEL calls zero.
- New cohort: 500.
- Units: 363 police, 237 fire, 400 non-safety.
- States/DC: 40; source families: six.
- Packet rows: 5,767.
- Packet maxima: six pages/case, 1,499 characters/page, 5,999/case.
- Selection SHA-256:
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.
- Final repaired preflight: 6/6.
- GABRIEL backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`.
- Live attempts: 551.
- Unique new cases stored: 499/500 (99.8%).
- Request outcomes: 499 success, 51 schema-invalid, one request failure.

## Decision

Decision: `live_incomplete_schema_invalid`.

No cumulative 1,000-document observation or QA counts exist because the
all-or-nothing materialization gate did not pass. The 499-case parsed
checkpoint remains resumable but is not a provisional cumulative lane. The
corrected 500-document targeted-QA layer remains the latest complete valid
provisional extraction evidence.

Targeted observation-level QA is not yet appropriate: the blocker is one
missing strict-schema case, not a populated cumulative conflict queue. The
remaining unique readable parse-text documents may not run next. First resolve
the single bounded longevity-routing case, reach 500/500, materialize the
cumulative ledgers, and compute duplicate, page-pointer, conflict, and
base/non-base contamination QA.

No URL access, download, OCR, scout, review, verification, ingestion,
codification, final merge, wage-gap work, regression, or causal claim occurred.
