# Independent adjudication PREP1 packet result

Date: 2026-07-25
Adjudication prep ID:
`TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`

## Result

**PASS — packet prepared; human adjudication not yet performed.**

- Cases prepared: 150/150.
- Human-facing CSV rows: 150 plus header.
- Human-facing fields: 28 total—15 identity/page fields and 13 human-review
  fields.
- Render manifest rows: 785.
- Rendered local pages: 785.
- Render failures: 0.
- Rendered image bytes: 106,889,932 (about 101.94 MiB).
- Full local packet disk size: about 104 MiB.
- Non-image packet files: 418,344 bytes.

The 785 page-level JPEG aids are readable at the configured 110 DPI and are
stored under the packet's `rendered_pages/` directory. Because the image set
is bulky, it will be kept in the local coordinator packet and excluded from
the lite relay. The relay will carry the render manifest, per-image hashes and
sizes, case index, instructions, and all other non-image packet files.

## Blinded human input

The human-facing file is:

`docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/independent_adjudication_blinded_review_input.csv`

It includes the required case/calibration/source/readiness/candidate
identities, place/unit/source metadata, page count, blinded candidate/nearby/
navigation page lists, local artifact path, and initialized human-review
fields.

It deliberately excludes:

- REVIEW1 and REVIEW2 labels;
- `wage_table_signal` and related detector judgments;
- `extraction_gate_label`;
- prior recommended extraction actions;
- prior reviewer identities, notes, and decisions;
- detector snippets and contract-period text;
- complete document/page text;
- complete tables and structured wage values.

REVIEW2 was read only to confirm exact calibration-identity equality. Its
labels were not used to populate the human file or packet strata.

## Bounded page and navigation rules

- Candidate page window: ±1 page.
- Navigation-page budget: at most four pages per case.
- Render cap: at most six pages per case.
- Render priority: a bounded spread of candidate pages, then nearby context,
  then front/end navigation context.
- Contents/index/appendix pages are pointers, not wage schedules.
- `points_to_later_table` is allowed only if the named target is within the
  listed budget, visually checked, and satisfies the row/column or compact
  compensation-sheet rule.
- Targets outside the bounded packet require second review; their contents
  cannot be inferred from a title.

The detailed rule plan is in
`docs/analysis/text_table_navigation_table_rule_refinement_plan_2026-07-24.md`.
The packet-specific instructions are in
`independent_adjudication_instructions.md`.

## Immutability and boundary

The original calibration input, every REVIEW1 output, and every REVIEW2 output
remained unchanged during planning and generation. The generator's audit
records identical before/after hashes for the original calibration input and
REVIEW2 reviewed CSV.

No URL was opened. No network/API/model/hosted-search call, download,
redownload, OCR, wage extraction, extraction pilot, ingestion, or
`gabriel.codify` occurred. No complete text or table was saved, and no final
wage value was created. Durable routing, metadata-triage, source-review,
PDF-readiness, and text/table-detection ledgers were not mutated.

REVIEW2 remains `continue_schema_refinement`; no extraction is authorized.
