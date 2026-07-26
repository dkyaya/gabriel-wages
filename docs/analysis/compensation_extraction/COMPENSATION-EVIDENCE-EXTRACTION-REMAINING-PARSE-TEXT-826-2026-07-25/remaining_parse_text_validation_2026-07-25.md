# Remaining readable parse-text extraction validation

## Gate result

- Selection: pass — 826 unique retained readable hashes from 827 remaining durable rows.
- Duplicate-hash handling: pass — one representative selected and both identities preserved in provenance.
- Packet caps: pass — 4,610 page rows; maxima of 6 pages/case, 1,499 text characters/page, and 5,999/case.
- Preflight: pass — 7/7 strict semantic-schema valid.
- Seed isolation: pass — zero corrected 1,000-case seed calls.
- Live completeness: fail — 825/826 strict-valid after 861 attempts.
- Cumulative materialization: not run.
- Cumulative integrity QA: not run.
- Final merge: prohibited.

The single unresolved case is `cexrem_4a267735daf6729f5c4e4835`. All ten attempts were rejected because education/certification compensation appeared in the base quantitative array. The checkpoint remains fail-closed and resumable.

## Repository validation

Repository compiles, regression tests, dashboard build, repository validation, ingestion regression tests, coverage audit, protected-state checks, metadata safety checks, and diff hygiene are recorded in the task relay. All passed except the intentional live-completeness gate above.

## Safety checks

- Raw prompts/responses saved: false.
- Full document/page text saved: false.
- Full tables saved: false.
- Encoded images saved: false.
- Credentials or authorization headers saved: false.
- URLs opened or files downloaded: false.
- OCR used: false.
- Ingestion or codification run: false.
- Durable or prior extraction/QA ledgers mutated: false.
