# GABRIEL Codify Texas/Ohio Scale-Up — Parse & Source-Grounding Audit — 2026-07-09

## Run summary

- Command: `python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 8 --windows docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv`
- Run directory: `tmp/gabriel_codify_pilots/2026-07-09_205815/`
- Model: `gpt-5.4-nano` via Harvard Proxy (same adapter as the 4-row pilot).
- **Calls attempted: 8 | succeeded: 8 | failed: 0.** No `errors.jsonl` was written (no errors occurred). Each row was its own `gabriel.codify()` invocation, so this is 8 rows × 1 call each = 8 total live calls, at the hard cap, not exceeded.
- Cost: `logs/api_spend_log.csv` recorded 8 new rows for `gabriel_codify_pilot.py (harvard_proxy)` / `gpt-5.4-nano`; per-call cost ranged ~$0.0026–$0.0045, all effectively negligible.
- Rows completed: 8/8. Rows skipped: 0.

## Output parse status

`gabriel.codify()`'s native output is wide-format (one row per input row, one column per attribute, each cell a Python-list-repr of extracted verbatim excerpt strings; empty list = no evidence for that attribute). This differs from the long/tidy shape used elsewhere in this project's evidence pipeline, so a parsing step reshapes it — same convention already established by the 4-row pilot's `gabriel_codify_full_codebook_outputs_2026-07-09.csv` (one row per excerpt, `confidence` always `not_applicable` with a caveat explaining `codify()` has no native confidence field, `excerpt_location` derived heuristically by searching for an Article/Section marker near the excerpt in the window text).

- Parsed CSV: `docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv`
- **173 rows total: 95 `present`, 78 `not_found`.** 0 rows failed to parse (`parse_status` is `parsed` for all 173 rows — every attribute cell across all 8 contracts was valid Python-list syntax).
- 74 of the 152 (contract × attribute) slots had at least one excerpt; 19 of those slots returned more than one distinct excerpt (codify sometimes finds multiple non-contiguous spans for one attribute), which is why 74 present-slots produced 95 present-rows.

## Source-grounding audit status

For every `present` row, the excerpt was checked as a verbatim (whitespace-normalized) substring of that row's `window_text` — same method as the 4-row pilot.

- **94 of 95 present excerpts are genuinely grounded** in their source window (real contract text this project's own prior hand-extraction had already pulled from the underlying PDF).
- **1 row requires a flag, not just a grounding label — a header-leakage artifact, not a hallucination:**
  - `oh_cleveland_fire_2025` / `interest_arbitration_or_formal_impasse_backstop`: the "excerpt" the model returned is this run's own window-assembly section header (`"Arbitration / impasse backstop (legacy code -- may be interest OR grievance arbitration; distinguish from text) [char 1792] --- sseces 45 ..."`), not text from the underlying Cleveland Fire CBA. The underlying source passage for that window section is pure OCR table-of-contents garbage (confirmed against `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`'s original `arbitration_impasse_backstop` excerpt for this contract, which is itself unreadable TOC dot-leader noise). With nothing usable to extract, the model appears to have echoed the section header text back — which technically passes a naive "is this excerpt a substring of window_text" check, because this project's own header literally is in `window_text`. This row has been labeled with an explicit `notes` flag in the output CSV rather than silently passed through, and should **not** be read as evidence that Cleveland Fire's CBA references interest arbitration (a separate genuinely-grounded excerpt for `oh_cleveland_police_2025` — the WITNESSETH clause — does support interest-arbitration language for the *police* contract, which is a real, distinct finding).
  - **Root cause and fix for future runs:** this project's window-assembly convention (`--- {mechanism label} [{location}] ---`) embeds codebook vocabulary (e.g. "impasse", "interest OR grievance arbitration") directly in the text sent to the model. When the underlying passage under that heading is unusable (heavy OCR garbling), the label itself becomes the most category-relevant text in that section, and a low-effort/low-reasoning model can grab it. **Recommendation:** before the next codify scale-up (Massachusetts or further Texas/Ohio rows), switch to neutral, keyword-free window-section headers (e.g. `--- Excerpt 1 [page 48] ---` instead of `--- Arbitration / impasse backstop ... ---`), or drop headers entirely and rely on `window_id`/ordering alone.
- Excluding that one artifact: **94/95 (99%) of present excerpts are genuine, source-grounded contract text.** 0 excerpts were flagged `unsupported` (a excerpt/claim not found anywhere in the window) — there is no evidence of the model inventing text not present in its input.

## Attribute-level observations

- **`peer_comparator_wage_comparability`: not_found for all 8 rows.** No over-coding — if anything, this matches this project's established finding from the 4-row pilot and the deterministic hand-extraction that explicit peer/comparator wage language is rare across this Texas/Ohio sample. This is a substantively important null result for the project's cross-occupation design, not a coding gap: none of these 8 windows contained genuine external-comparator language for the model to find.
- **Most-coded attributes:** `benefits_total_compensation_or_pension` (14 present rows), `management_rights_or_service_flexibility` (11), `classification_reclassification_or_grade_structure` (10), `premium_pay_differentials` (9), `overtime_callback_holdover_mandatory_extra_work` (8). These track the content of the windows themselves (assembled specifically to surface these mechanisms from the prior hand-extraction), not a general base rate.
- **Least-coded:** `minimum_staffing_or_continuous_coverage` and `no_strike_or_work_stoppage_constraint` (1 present row each) — expected, since the windows were not specifically assembled to surface these two attributes (no matching deterministic-extraction category existed to draw from).
- **Excerpt length:** min 9 words, max 108 words, average 31.4 words. 26 of 95 (27%) exceed the "under 40 words" instruction in `ADDITIONAL_INSTRUCTIONS`. All are still short, single-clause verbatim spans (not full paragraphs), and all but the one flagged artifact are genuinely grounded — this is a soft instruction-adherence gap (worth tightening in a future prompt revision), not a correctness or fabrication problem.

## Interest vs. grievance arbitration: did the codebook's split hold up?

Yes, in 6 of 7 cases (the 7th being the flagged header-leakage artifact, which is not real evidence either way):

| contract_id | attribute coded present | excerpt gist | correct? |
|---|---|---|---|
| `tx_houston_police_2024` | grievance_or_contract_interpretation_arbitration | AAA/FMCS labor panel for officer appeals | ✅ grievance-type process, correctly not coded as interest arbitration |
| `tx_austin_fire_2023` | interest_arbitration_or_formal_impasse_backstop | "effective as of the date of the award in the interest arbitration proceeding" | ✅ explicit interest-arbitration language |
| `oh_columbus_police_2023` | interest_arbitration_or_formal_impasse_backstop | "2026 negotiations for a contract to succeed this Contract shall be conducted in accordance with the dispute settlement procedure" (ORC 4117 fact-finding/conciliation/arbitration) | ✅ successor-contract impasse process, correctly coded as interest/impasse, not grievance |
| `oh_columbus_other_2024` | grievance_or_contract_interpretation_arbitration | "Specific Types of Grievances... Use of Mediation" (Article 11) | ✅ grievance procedure article |
| `oh_cleveland_police_2025` | interest_arbitration_or_formal_impasse_backstop | WITNESSETH clause: "negotiations and/or interest arbitration which resulted in this Contract" | ✅ explicit interest-arbitration language |
| `oh_cleveland_other_2022` | grievance_or_contract_interpretation_arbitration | "agree upon an arbitrator... notify the AAA or FMCS... intent to arbitrate the grievance" | ✅ grievance-arbitration process |
| `oh_cleveland_fire_2025` | interest_arbitration_or_formal_impasse_backstop | **flagged artifact — see Source-grounding audit status above** | ⚠️ not real evidence either way |

This is the same distinction the 4-row pilot's design specifically set out to test (Houston Fire's arbitration being grievance/contract-interpretation, not interest/impasse). The scale-up run continues to show the refined 19-attribute codebook correctly separating the two arbitration types on genuinely-worded text, and correctly reflects Chapter 174/4117 institutional context (Texas Local Government Code Ch. 174 for the TX rows; Ohio Revised Code Ch. 4117 for the OH rows) without needing that context spelled out in the window.

## Comparison with deterministic extraction

Every one of the 94 genuinely-grounded present excerpts is either identical to, or a sub-span of, a passage this project's own prior hand-extraction (`texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv` / `texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`) had already independently identified and labeled with a legacy 11-code mechanism tag — since the windows were assembled entirely from that prior extraction's own `present`/`unclear` excerpts. This is expected (the model was working from a curated subset of already-identified evidence, not raw document text), and it means this run is best read as a test of **codify's classification accuracy against the refined 19-attribute codebook**, not a test of codify's ability to find evidence in raw, unreviewed source text. That broader test (raw-document extraction) remains future work.

## Is this run safe to append to the evidence layer/viewer?

**Yes, with the one flagged row carried forward transparently.** 173/173 rows parsed cleanly, 94/95 present excerpts are genuinely source-grounded, 0 hallucinated (invented, not-in-window) excerpts, and the one artifact row is labeled in its `notes` field rather than silently included as if it were ordinary evidence. Task G proceeds to union this output with the 4-row pilot's output into the durable evidence layer.

## Recommended next step

1. Rebuild the evidence layer and viewer from the union of both output CSVs (Task G).
2. Before the next codify scale-up, fix the window-assembly header format (drop codebook-vocabulary from section headers) to eliminate the header-leakage failure mode identified here.
3. Per this run's own scope, the next scale-up should be a **curated Massachusetts codify batch** (not further Texas/Ohio rows) — Texas/Ohio now has all 4 matched cities represented (Houston, Austin, Columbus, Cleveland) across both codify batches.
