# Automated GABRIEL Gate 2 readiness audit

Date: 2026-07-25
Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25`

## Readiness result

**PASS FOR LOCAL DIAGNOSIS, IMPLEMENTATION, DRY RUN, AND A ONE-CASE
PREFLIGHT.** The 150-case live Gate 2 run remains conditional on a successful
strict-schema preflight with `--allow-gabriel`.

The latest local commit before work was
`6b10da8615e91454864667689563d23a23d10d0e`. The tracked worktree was clean.
The only unrelated untracked items were the expected 785 local render aids
under the independent packet and the root `package-lock.json`; neither is a
Gate 2 output and both remain outside the tracked task scope.

Exact local ancestry checks passed for `6b10da8`, `51f709a`, `c3580a4`,
`0e9430b`, `7438f1a`, `610f5e8`, `32ae355`, `827917b`, `11e689a`,
`b45876e`, `74a843a`, `985d581`, `46923a2`, `12b3f10`, `ed042c1`,
`79df80c`, and `e028432`. No remote was inspected.

## Gate 1 authority and diagnosis

Gate 1 is complete and immutable:

- cases: 150;
- schema-valid GABRIEL responses: 150/150 (100%);
- high-confidence ready: 12;
- schema-update ready: 16;
- total ready: 28;
- likely/p1 ready: 27/80 (33.75%);
- wrong pages among 132 candidate-bearing cases: 9 (6.82%);
- second review: 19;
- no candidate page: 71;
- ready unit representation: police 5, fire 7, non-safety 16;
- ready source representation: arbitration award 1, CBA 10,
  ordinance/policy 5, wage schedule/compensation plan 12.

Gate 1 passed schema validity, wrong-page precision, and negative-family
control. It failed likely/p1 coverage and representative-ready-set gates. The
working diagnosis is upstream page discovery: 53 likely/p1 cases were not
ready, including 40 exclusions and 13 second-review cases; 71 rows were called
`no_candidate_page`, although 53 of those had a candidate page in the blinded
input. This distinction indicates that a supplied page can lack a plausible
table without being materially unrelated, and it motivates explicit Gate 2
no-candidate versus wrong-page rules.

## Gate 2 target cases

Gate 2 still adjudicates all 150 blinded cases under identical hard caps. Its
diagnostic focus is:

1. the 53 original likely/p1 rows that were not ready;
2. all 19 `second_review_required` rows;
3. the 71 no-candidate relationships, especially the 53 with supplied
   candidate hints;
4. the 10 unknown relationships;
5. contents/index pointers and any safely inferred printed-page offsets;
6. compact role-to-pay layouts that Gate 1's aggregate compact score could not
   distinguish reliably from wage prose.

Gate 1 labels are used only to define these post-hoc diagnostic groups. They
must not enter a primary Gate 2 GABRIEL prompt.

## Configuration and preflight gate

A secret-safe presence check found the existing project dotenv and configured
credential without printing or hashing its value. Gate 2 retains:

- backend: `huit_openai_responses_direct_sdk`;
- model: `gpt-5.4-nano`;
- strict API JSON Schema plus local response validation;
- 60-second SDK and outer timeout;
- parallelism one;
- hosted tools/search disabled;
- explicit `--allow-gabriel` required for any live request.

The complete 150-case dry run must make zero calls. One bounded case must then
return schema-valid strict JSON. A missing credential, request failure,
timeout, invalid schema, prior-label prompt marker, or bounds violation stops
the task before the live 150-case run. There is no heuristic-only fallback.

## Permitted local artifact scope

Only the same 150 PDF artifacts named by the independent blinded input and
their existing bounded render aids may be opened. Gate 2 may inspect at most
six pages per case, including no more than four navigation pages. Each page
contributes at most 1,500 redacted text characters and each case at most 6,000.
Printed-page offset inference must be derived only from footer/header evidence
on pages already inside this budget; it cannot scan a whole document.

Starting SHA-256 values were recorded for the original calibration input,
REVIEW1, REVIEW2, the blinded input and render manifest, all three Gate 1
outputs, durable detection/readiness/source-review ledgers, protected CSVs,
and the corpus inventory. Gate 2 writes only to a new output directory.

## Explicit boundary

- no URLs, hosted search, source review, or URL verification;
- no downloads or redownloads;
- no OCR;
- no wage extraction, 500-document prompt, or smaller pilot;
- no full text, complete tables, or structured wage observations;
- no ingestion or `gabriel.codify`;
- no wage-gap calculation, claim, causal claim, or regression;
- no mutation of routing, metadata-triage, source-review, PDF-readiness, or
  text/table-detection ledgers;
- no mutation of original calibration, REVIEW1, REVIEW2, independent packet,
  or Gate 1 outputs;
- no remote inspection, fetch, pull, push, or remote mutation.

Extraction remains prohibited unless the completed Gate 2 ledger passes every
predeclared authorization criterion.
