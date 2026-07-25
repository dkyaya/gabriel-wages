# Provisional 1,000-document extraction QA report

## Outcome

QA stopped before live extraction because the six-case representative
GABRIEL preflight did not pass. Five responses satisfied the strict semantic
schema. The conflict-prone sixth response used `mixed_ready` without returning
both required quantitative and qualitative sub-record types, so the validator
rejected it as `schema_invalid`.

The failure is evidence that the strict fail-closed control worked. It is not a
case-level extraction result and must not be converted into a heuristic-only
or partially live 1,000-document ledger.

## Completed controls

- Frozen identities: 1,000 unique retained documents.
- Corrected seed: all prior 500 identities preserved, with zero new GABRIEL
  calls against the seed.
- New expansion: 500 unique retained local identities.
- Units: 363 police, 237 fire, and 400 non-safety.
- States/DC: 40.
- Source families: six.
- Packet rows: 5,767.
- Caps: at most six pages, 1,500 characters per page, and 6,000 characters per
  case.
- Representative preflight: 5/6 schema-valid (83.3333%).
- Live new-case attempts: zero.

## Not computed

No live cumulative lane ledgers were created. Therefore quantitative,
qualitative, mixed, non-base-wage, reference/exclusion, duplicate, page-pointer,
conflict, and contamination results for the 1,000-document layer are not
available. The header-only conflict-review file records that the review stage
did not start; it contains no invented observations.

The corrected 500-document shadow ledgers remain the latest valid provisional
extraction layer. Scaling beyond 1,000 is blocked. A separately authorized
retry must first repair or further constrain mixed-disposition schema
consistency and then pass the unchanged six-path preflight.

No URL access, hosted search, download, OCR, scout, source review, verification,
ingestion, codification, final merge, wage-gap calculation, regression, raw
prompt/response retention, full-text/table retention, or secret retention
occurred.
