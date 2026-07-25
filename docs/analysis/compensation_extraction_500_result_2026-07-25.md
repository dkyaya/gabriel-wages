# Provisional 500-document compensation-evidence extraction result

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25`

## Outcome

The first serious extraction run completed against exactly 500 frozen local
document identities. GABRIEL produced a final strict-schema-valid result for
all 500 cases after a successful four-case preflight and bounded resumable
retries. The output is a provisional, separate-lane QA layer—not a final
analysis dataset. Integrity QA passed; scale QA did not. Scaling to 1,000 is
premature pending targeted conflict, duplicate, and base/non-base-wage review.

## Selection and matching

- Documents: 500 unique identities and 500 unique retained content hashes.
- Municipal groups: 200, each with a selected non-safety comparison
  opportunity.
- Units: 180 police, 120 fire, and 200 non-safety.
- Geography: 40 states/DC.
- Sources: 452 CBAs, 23 wage schedules or compensation plans, 10 memoranda or
  settlements, nine ordinances or policies, five arbitration awards, and one
  factfinding source.
- Signals: 350 likely, 146 possible, and four unlikely wage-table signals.
- Frozen selection SHA-256:
  `2341e68426e5e62bdf406817fed17c703ee116d7c31af81f9e73b8b96ad583fb`.

All selected artifacts were already retained, hash-verified, PDF-signature
valid, text-layer readable, and marked as not requiring OCR by the durable
readiness layer. The source-review, readiness, detection, triage, and other
durable ledgers were read only.

## Bounded packets and GABRIEL execution

- Packet records: 2,843 local pages.
- Bounded text: 2,841,259 characters in the final 500 successful requests.
- Limits observed: six pages per case; 1,500 characters per page; 6,000 per
  case. Actual maxima were six, 1,499, and 5,999.
- Existing rendered evidence: 108 images used across 42 selected calibration
  cases. No image was copied or encoded into a saved artifact.
- Preflight: four representative cases, four successes, four schema-valid
  responses.
- Live attempts: 528 total—500 successes, 26 locally rejected semantic-schema
  results, and two request timeouts. The first pass stored 476 cases; bounded
  retries recovered 21, two, and one cases, respectively.
- Final case-level schema-valid rate: 500 / 500 (100%). Request-attempt success
  rate, including rejected attempts and retries: 500 / 528 (94.70%).
- Backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`.
- No raw prompts or raw responses were saved. Request metadata contains hashes,
  counts, timing, redacted errors, and explicit false sensitive-retention flags.

## Provisional lane outputs

- Quantitative: 1,073 observations across 283 cases.
- Qualitative mechanism: 1,181 observations across 387 cases.
- Mixed: 182 cases linked to 686 quantitative and 572 qualitative sub-records
  through stable mixed join keys. The sub-records remain in their respective
  ledgers rather than being collapsed into a vague mixed field.
- Non-base wage: 1,327 observations across 395 cases, including 222 overtime,
  75 healthcare-contribution, 59 benefits, 52 education/certification, 45
  longevity, 43 uniform/equipment, 39 pension, 30 reimbursement, 29 stipend,
  432 leave, and 301 other provisional records.
- Reference/exclusion: 90 cases—43 excluded, 41 reference-only, and six second
  review.

Quantitative types include 337 percentage increases, 123 hourly rates, 74
annual salaries, 63 rates, 52 steps, 35 salaries, 12 grades, three pay bands,
and 374 `other` provisional records. Qualitative observations include 603
implementation/effective-date, 140 CBA-term, 69 step/seniority, 56
arbitration/factfinding, 42 longevity/service, 36 certification/education, 25
fiscal-constraint, 21 rank/classification, 19 comparability, 19 settlement,
18 CPI/COLA, eight reopener, five parity, and 120 `other` mechanisms.

## QA result

Integrity QA passed: 500 identities and results, zero invalid page pointers,
zero duplicate IDs, exact packet compliance, and separate lane provenance.
Scale QA is on hold:

- 83 potential same-evidence-key quantitative conflict groups;
- two exact quantitative duplicates and one exact non-base-wage duplicate;
- 102 quantitative records flagged as possible non-base-wage evidence;
- 187 explicit rows in the targeted review queue.

The detailed decision is
[compensation_extraction_500_decision_report.md](compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25/compensation_extraction_500_decision_report.md).
The computed 1,000-document recommendation is
`premature_pending_targeted_qa`; final merge and ingestion remain false.

## Boundary confirmation

No URL was opened, no hosted search or source discovery/review/verification ran,
and no document was downloaded or redownloaded. No OCR, ingestion,
`gabriel.codify`, final dataset merge, wage-gap calculation, regression, or
causal analysis occurred. No full document/page text, full table, raw prompt,
raw response, encoded image, credential, cookie, token, or authorization header
was saved. The provisional structured fields are QA observations only.
