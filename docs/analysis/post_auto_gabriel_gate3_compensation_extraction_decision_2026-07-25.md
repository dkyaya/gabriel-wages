# Post-Gate 3 compensation extraction decision

Gate: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`

Decision: `500_doc_compensation_extraction_allowed`

## Authorization

- Future combined quantitative + qualitative compensation extraction scale:
  up to 500 bounded document/page packets.
- Smaller pilot restriction: not applicable; Gate 3 passes the 500-document
  authorization rule.
- Wage extraction performed in Gate 3: none.
- Qualitative final extraction performed in Gate 3: none.

## Rationale

Seventy of 80 original likely/p1 cases (87.50%) are high/medium-confidence
ready under the compensation-evidence category and recommendation rule. The
GABRIEL schema-valid rate is 100%. The 108-case ready set represents police,
fire, and non-safety units and six source families. Only one row is reference-
only, none requires second review, and no final row is an error. Every encoded
500-document criterion passes.

The decision is for compensation evidence, not classic wage tables alone. A
future extraction must preserve separate paths for clean/compact/narrative
quantitative evidence, qualitative compensation-setting mechanisms, mixed
evidence, and non-base-wage compensation.

## High-level selection criteria for 500 documents

1. Use retained local artifacts already accepted by durable PDF readiness and
   text/table detection. Do not use URLs, downloads, or OCR.
2. Prioritize bounded pages whose Gate 3-like evidence supports quantitative,
   qualitative, or mixed extraction with high/medium confidence.
3. Stratify across police, fire, and non-safety units; source families; states;
   and quantitative/qualitative/mixed evidence types.
4. Keep reference-only, low-confidence, benefits-only, and irrelevant pages in
   separate follow-up or exclusion lanes rather than silently promoting them.
5. Retain city × occupation × negotiation-cycle identities so public-safety
   units can later be matched to non-safety units; do not collapse units or
   cycles.

## Execution controls for the future run

- Use independent, resumable lanes with immutable inputs and unique outputs.
- Persist only provisional structured fields, evidence locations, short
  reason codes, and QA metadata; do not save full page/document text or full
  tables.
- Enforce quantitative and qualitative schemas separately, plus a mixed join
  key. Stop before final merge until lane QA and cross-lane consistency pass.
- Audit exact page provenance, duplicate identities, schema validity,
  confidence, missingness, unit/source representation, and protected-file
  immutability.
- Use no OCR. Perform no ingestion or `gabriel.codify` until extraction QA is
  stable and a separate authorization is given.
- Do not calculate wage gaps, run regressions, or make causal claims.
