# GABRIEL Codify Massachusetts — Parse & Source-Grounding Audit — 2026-07-09 (run date 2026-07-10)

## Selected rows/windows

10 rows, all confirmed present in `data/contracts.csv` with a corresponding corpus file on disk: `ma_somerville_police_spsoa_2012`, `ma_wayland_fire_jlmc_2020`, `ma_franklin_police_2022`, `ma_franklin_fire_2022`, `ma_franklin_public_works_2022`, `ma_franklin_library_2022`, `ma_franklin_other_2022`, `ma_boston_clerical_admin_2023`, `ma_georgetown_other_2020`, `ma_georgetown_police_2020`. Full rationale: `gabriel_codify_massachusetts_sample_selection_2026-07-09.md`. Windows: `gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv`, built fresh this session from the actual corpus PDFs (`pdftotext -layout`), with strictly neutral `--- Excerpt N [location] ---` separators.

## Calls attempted/succeeded/failed

- Dry run first: `tmp/gabriel_codify_pilots/2026-07-10_102543/` — no network call, no credential read, contamination check passed on all 10 windows.
- Live run: `tmp/gabriel_codify_pilots/2026-07-10_102644/` — **10 calls attempted, 10 succeeded, 0 failed.** No `errors.jsonl` written. One `gabriel.codify()` invocation per row, at the approved 10-call cap, not exceeded.
- Rows completed: 10/10. Rows skipped: 0.

## Output parse status

`docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv` — **214 rows total: 70 present, 144 not_found.** 0 rows failed to parse (every attribute cell across all 10 contracts was valid Python-list syntax). 2 of 10 contracts (`ma_wayland_fire_jlmc_2020`, `ma_georgetown_other_2020`) returned `not_found` for all 19 attributes — see "Attribute-level observations" below for why this is a plausible, not a broken, result.

## Source-grounding audit status

For every `present` row, the excerpt was checked as a verbatim (whitespace-normalized) substring of that row's `window_text`.

- **70/70 present excerpts pass the substring grounding check (`source_grounding_status=grounded`). 0 `unsupported`.** No evidence of the model inventing text absent from its input window.
- **However, a recurrence check specifically added this session (scanning every returned excerpt for this project's own scaffolding vocabulary — the 18 multi-word codebook attribute keys, plus `"Excerpt 1"`/`"Excerpt 2"`/`"---"`) flagged 4 of 70 present excerpts (5.7%):**

| contract_id | attribute | excerpt (verbatim) |
|---|---|---|
| `ma_franklin_fire_2022` | training_certification_credential_premiums | `'The stipend for Emergency Medical Techni\n\n--- Excerpt 7 [Section 10.2'` |
| `ma_franklin_public_works_2022` | premium_pay_differentials | `'Section 14.2] ---\na part\nof this agreement.\n\nSection 14.2\nEmployees who are assigned...'` |
| `ma_franklin_library_2022` | benefits_total_compensation_or_pension | `'ARTICLE 26] ---\nARTICLE 26\n HEALTH AND LIFE INSURANCE\nSECTION 26.1\n...'` |
| `ma_boston_clerical_admin_2023` | premium_pay_differentials | `'...workers compens\n\n--- Excerpt 8 ---\nurs between 12:01 am on Saturday...'` |

**This is a real, if milder, recurrence of the Texas/Ohio failure mode's underlying cause — not the same failure mode itself.** In every one of the 4 cases, the excerpt contains genuine source-document text on both sides of the leaked separator (unlike `oh_cleveland_fire_2025`, where the *entire* excerpt was fabricated from a header because the underlying passage was unreadable garbage). Here, the model captured a real verbatim span that happened to cross the boundary between two adjacent excerpt blocks in `window_text`, incidentally including a few characters of this project's own `--- Excerpt N [location] ---` separator syntax at the seam. **Root cause: adjacent excerpts in the assembled window are separated only by `\n\n--- Excerpt N [location] ---\n`, with no larger buffer or hard break, so when two nearby regions of the same source document (pulled by independent keyword searches) abut or nearly abut, the model perceives one continuous passage and copies straight through the separator.**

Each of these 4 rows was written to the outputs CSV with a `METHODOLOGY FLAG` note (matching the exact convention established for the Texas/Ohio artifact), which — via `scripts/build_codify_evidence_viewer.py`'s new `notes_flag`/`viewer_verified` columns (Task C, this session) — automatically excludes them from the viewer's default "verified evidence" view even though their raw `source_grounding_status` is `grounded`. **This is the defense-in-depth design working as intended**: the window-construction fix eliminated full-fabrication artifacts (0 recurrences), and the viewer-level notes-flag safety net caught the milder boundary-leakage variant that the window-construction fix alone did not fully prevent.

**Recommended fix before the next codify batch:** insert a larger, unambiguous break between adjacent excerpts (e.g. a blank marker line with no source-adjacent text, or trim each excerpt to end at a clean sentence/clause boundary rather than mid-word) so a verbatim-copying model has nothing continuous to span across.

## Attribute-level observations

- **`peer_comparator_wage_comparability`: present for exactly 1 of 10 rows** (`ma_somerville_police_spsoa_2012`) — genuine, strong peer-comparator language: the excerpt names the specific Massachusetts communities (Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, Waltham, plus Medford "as an appropriate comparable") used in a Collins Center for Public Management classification-and-compensation study. This is exactly the kind of explicit, named-comparator language the attribute definition requires — **no over-coding**; the other 9 rows correctly returned `not_found` rather than treating generic "competitive"/internal-comparison language as a peer-comparator hit.
- **Most-coded attributes:** `classification_reclassification_or_grade_structure` (14), `grievance_or_contract_interpretation_arbitration` (11), `overtime_callback_holdover_mandatory_extra_work` (11), `premium_pay_differentials` (8) — these track the content the windows were built to surface (classification/wage-schedule and grievance-procedure text were prominent in nearly every Massachusetts CBA sampled), not a general base rate.
- **Least-coded (1 present row each):** `budget_capacity_or_fiscal_constraint`, `non_safety_wage_restraint_or_admin_channel`, `minimum_staffing_or_continuous_coverage`, `civil_service_or_statutory_employment_channel`, `union_security_or_institutional_power`, `interest_arbitration_or_formal_impasse_backstop` — expected, since the 10 windows were built primarily around grievance-arbitration, wage-structure, and premium-pay keyword hits, not these attributes specifically.
- **Excerpt length:** min 3 words, max 67 words, average 28.5 words — noticeably tighter than the Texas/Ohio scale-up's average (31.4 words, 27% over the 40-word guidance); this run had fewer excerpts exceed the "under 40 words" instruction.
- **Two contracts returned all-`not_found`:** `ma_wayland_fire_jlmc_2020` (a genuinely short, 160-word stipulated-award document consisting mostly of numeric wage-step and call-back amendments — a plausible, conservative null result, not a bug) and `ma_georgetown_other_2020` (the assembled window was dominated by table-of-contents dot-leader text and signature-page boilerplate, with only one substantive clause — the arbitrator-selection procedure — captured; also plausible given the window's actual content, not evidence of a systemic problem).

## Interest vs. grievance arbitration: did the codebook's split hold up?

**Yes, cleanly, including on the same document.** `ma_somerville_police_spsoa_2012` produced both an `interest_arbitration_or_formal_impasse_backstop=present` row (the genuine "Interest Arbitration process is utilized when..." analysis text from the JLMC award opinion) **and** two separate `grievance_or_contract_interpretation_arbitration=present` rows (ordinary grievance-procedure clauses from the base CBA the award amends) — the model correctly distinguished the two mechanisms within one window. Every other arbitration hit across the remaining 9 rows was `grievance_or_contract_interpretation_arbitration` only (Franklin police/fire/public works, Boston clerical, Georgetown police) — all genuinely grievance-procedure text (Article/Section grievance steps, "Union shall have the exclusive right to initiate arbitration of a grievance," etc.), correctly never coded as interest/impasse arbitration. `ma_wayland_fire_jlmc_2020`, despite being a JLMC docket document, contains no arbitration-*process* language in this specific short amendment text and correctly returned `not_found` for both arbitration attributes rather than inferring the institutional fact from outside knowledge.

## Comparison with deterministic Massachusetts extraction/source-scan files

No dedicated Massachusetts excerpt-extraction CSV existed prior to this session (unlike Texas/Ohio, which reused `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`). This run's windows were instead built directly from fresh `pdftotext` extraction of the underlying corpus PDFs. Cross-checking against `data/contracts.csv`'s own captured verbatim fields: `ma_somerville_police_spsoa_2012`'s `comparability_text`/`comparability_referent` fields (captured in an earlier session) already recorded "comparable towns (statutory interest-arbitration criterion...)" — a different passage from the same document than this run's Collins-Center peer-comparator excerpt, but consistent in kind (both are genuine peer/comparator references). `ma_arlington_public_works_2015`'s `arbitration_clause_text` field (grievance arbitration under civil service law) matches the same grievance-not-interest pattern this run found for Franklin/Boston/Georgetown. No contradictions found between this run's codify output and this project's prior hand-captured Massachusetts fields.

## Is this run safe to append to the evidence layer/viewer?

**Yes, with the 4 flagged rows carried forward transparently**, exactly as the Texas/Ohio scale-up's one flagged row was. 214/214 rows parsed cleanly, 70/70 present excerpts pass the automated grounding check, 0 excerpts are fully fabricated (the Texas/Ohio full-fabrication failure mode did not recur), and the 4 milder boundary-leakage rows are labeled in their `notes` field and will not display as verified evidence in the viewer by default (confirmed via `scripts/build_codify_evidence_viewer.py`'s `viewer_verified` computation — see Task I).

## Recommended next step

1. Fix the excerpt-boundary-leakage issue identified above (larger break between adjacent excerpts, or trim to clean sentence boundaries) before the next codify batch.
2. Manual viewer QA — open `gabriel_codify_excerpt_browser_latest.html` and confirm Massachusetts now filters correctly alongside Texas/Ohio, and that the 5 flagged rows (1 from Texas/Ohio, 4 from this run) render with the "Not verified in source text" warning rather than as ordinary evidence.
3. A future, small follow-up batch specifically targeting Massachusetts dispatch/nurse_health content (`ma_wayland_other_2021`) would require a bounded OCR pass first (`pdftotext` currently extracts ~0 usable characters from that file) — not attempted this session; flagged as a known gap in the sample-selection memo.
