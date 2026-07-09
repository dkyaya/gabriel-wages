# GABRIEL Codify Full-Codebook Audit — 2026-07-09

## Whether native codify or codify-compatible adapter was used

**Native `gabriel.codify()`**, via a `response_fn` injection routed through the Harvard Proxy (`https://go.apis.huit.harvard.edu/ais-openai-direct/v2`, model `gpt-5.4-nano`). GABRIEL's own prompt template, snippet-boundary-marking system, JSON parsing, and DataFrame assembly all ran unmodified — the adapter's only job was the HTTP call itself. See `gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md` for the source-level trace confirming this hook is genuinely wired end-to-end in the installed package (v1.1.8).

## Calls attempted / succeeded / failed

**4 real live calls attempted, 4 succeeded, 0 failed** (matching the hard cap exactly). One earlier attempt on row 1 (`tx_houston_fire_2024`) made **zero** network calls — `gabriel.codify()` is `async def` and was mistakenly invoked without `asyncio.run(...)`, so it returned an un-awaited coroutine object (confirmed by Python's own `RuntimeWarning: coroutine 'codify' was never awaited`). This was a code bug caught before any request left the machine, fixed in one line, and does not count as a live call attempt. After the fix, row 1 succeeded on retry, and rows 2-4 (`tx_houston_other_2024`, `tx_austin_nursehealth_2023`, `oh_columbus_fire_2023`) succeeded together in a second script invocation (to avoid re-spending the already-successful row 1 call). Reported cost for all 4 real calls: **$0.00** (small prompts/responses on `gpt-5.4-nano`). See `tmp/gabriel_codify_pilots/2026-07-09_120200_full_codebook_live/live_run_log.txt` for the full consolidated log.

## Parse status

All 4 rows parsed cleanly into `docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv` (92 rows: 4 contracts × 19 attributes, with multi-snippet attributes contributing more than one row). Zero `parse_status=failed` rows.

## Source-grounding status

**53 of 53 `present`-status excerpts (100%) verified as verbatim substrings of their row's evidence window** (checked programmatically, after whitespace normalization). **Zero hallucinated or unsupported excerpts.** This is a strong, clean result — the model never invented text that wasn't literally in the window it was given.

## Attribute-level observations

- **The headline test passed.** For `tx_houston_fire_2024`, the model marked `grievance_or_contract_interpretation_arbitration=present` (with a correct verbatim excerpt: "the decision of the arbitrator shall be final and binding on the parties...") and `interest_arbitration_or_formal_impasse_backstop=not_found` — correctly keeping the two distinct, exactly as this project's own prior hand-analysis established (Houston Fire's arbitration award is grievance/contract-interpretation arbitration under CBA Article 14, not Sec.174.1535 compulsory interest arbitration).
- **Good judgment on Columbus Fire's SERB conciliation clause.** `oh_columbus_fire_2023`'s `interest_arbitration_or_formal_impasse_backstop=present` excerpt ("...select a single arbitrator from the list by alternate striking of names to serve as the **conciliator**...") correctly identifies genuine Ohio SERB conciliation language (an explicit positive example in the codebook), distinguishing it from the same document's separate, correctly-tagged `grievance_or_contract_interpretation_arbitration` excerpt (a reference to "Article 9, Grievance Procedure").
- **One plausible over-coding (false positive candidate).** `tx_houston_other_2024`'s `civil_service_or_statutory_employment_channel=present` excerpt is layoff/re-employment classification-preference language with no explicit "civil service," "Chapter," "meet and confer," or "SERB" trigger phrase — a real match against the window text (grounded), but a weak conceptual fit against the attribute's own definition and exclusion criteria ("Exclude generic city authority without a statutory/legal channel"). Flagged for human review, not automatically trusted.
- **One ambiguous case worth flagging.** `tx_houston_other_2024`'s `interest_arbitration_or_formal_impasse_backstop=present` excerpt ("HOPE and the City shall select a mediator...Should HOPE elect to proceed directly to arbitration...") plausibly describes either a genuine successor-contract impasse process or an ordinary grievance-dispute mediation/arbitration ladder — the compact evidence window (built by concatenating short excerpts) did not preserve the article header needed to disambiguate confidently. This is a **window-construction limitation**, not necessarily a model error: a future run should keep more surrounding context (article titles) around ambiguous-mechanism passages.
- **A few low-information (but still grounded) matches.** `oh_columbus_fire_2023`'s `classification_reclassification_or_grade_structure` and `subcontracting_outsourcing_or_volunteer_substitution` excerpts are table-of-contents lines (e.g., "SECTION 12.5. TITLES USED AND PAY RANGES APPLIED TO CLASSES. ......................... 22") rather than substantive clause body text. These are technically verbatim/grounded (the TOC line really is in the window), but thin evidence — a symptom of the window itself containing some TOC noise carried over from the prior deterministic extraction's raw excerpt text, not a model fabrication.
- **No over-coding of generic "competitive wages" as comparability.** `peer_comparator_wage_comparability` was `not_found` for all 4 rows — consistent with this project's own prior hand-extraction finding that none of these four documents contain explicit peer-city/external-comparator language.

## Whether the model confused interest/impasse arbitration with grievance arbitration

**No confusion on the clearest test case** (Houston Fire, described above). One borderline case (Houston HOPE) is flagged above as ambiguous due to a window-construction gap, not a clear model error — the excerpt itself is genuinely ambiguous even to a human reader without more surrounding context.

## Whether the model over-coded generic wage schedules as comparability

**No.** `peer_comparator_wage_comparability` was correctly `not_found` everywhere; the model did not conflate internal wage schedules (present under `classification_reclassification_or_grade_structure` for `tx_austin_nursehealth_2023` and referenced via TOC lines for `oh_columbus_fire_2023`) with external peer-comparator language.

## Whether excerpts were short and usable

Yes — all 53 present-status excerpts are short (well under the 40-word guidance in most cases; a few multi-sentence excerpts run slightly longer but remain single, coherent clauses, not long copied passages).

## Comparison with deterministic extraction files

The live codify run substantially reproduces this project's prior hand-built mechanism findings for these same 4 documents (Houston Fire's grievance-arbitration clause, wage schedule, EMT certification pay, uniform allowance; Houston HOPE's management-rights and privatization-notice language; Austin EMS's on-call/call-back pay, education incentive pay, shift differential; Columbus Fire's no-strike clause and SERB conciliation language) — all previously identified by hand in `houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`, `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`, and `texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.csv`. The live run also surfaced genuinely new, correctly-grounded findings the smaller 11-code pilot never tested for, most notably the civil-service/statutory-channel and union-security/institutional-power attributes.

**Important interface-level limitation discovered this session:** `gabriel.codify()`'s native output format is a **binary present/absent snippet list per category** (a category column is either `[]` or a list of verbatim matched spans) — it has **no native `confidence` field and no native `unclear` state**. This project's desired output schema (`evidence_status` ∈ {present, not_found, unclear}, plus a separate `confidence` and `caveat`) does not map cleanly onto codify()'s built-in snippet-boundary-marking architecture, even though `additional_instructions` explicitly requested confidence/caveat reporting — the underlying system prompt (visible in this run's own stdout) has a fixed output contract that does not include those fields, and the model's actual JSON response followed that fixed contract, not the `additional_instructions` request. This run reports `confidence=not_applicable` and an explanatory `caveat` for every row honestly, rather than inventing a confidence value codify never produced. Achieving true confidence scoring would likely require pairing `codify()` with GABRIEL's separate `rate()` task (0-100 scoring) or a custom prompt/parsing path outside codify()'s built-in template.

## Whether full-codebook approach is viable

**Yes, with caveats.** The core mechanics work: the Harvard Proxy adapter is real and functioning, source-grounding is excellent (100% verbatim, zero hallucination across 53 present-status findings), the codebook's most important discrimination (grievance vs. interest arbitration) held up correctly, and the output is a genuine tidy `state/city/occupation_class/contract_id/attribute/evidence_status/excerpt` table exactly matching this project's target evidence-layer shape. Two real limitations should be addressed before scaling: (1) codify()'s native output has no confidence/unclear state, so this project's richer 3-state evidence_status and confidence fields cannot currently be populated by codify() alone; (2) compact, concatenated evidence windows can strip context needed for a small number of genuinely ambiguous mechanism calls (the Houston HOPE impasse-arbitration case) and can carry over low-information TOC-line noise from prior extractions.

## Recommended next step

1. Before any larger run, decide whether to (a) accept codify()'s binary present/not_found output as-is (dropping the unclear/confidence ambition), or (b) layer a second GABRIEL task (e.g. `rate()`) on top of codify's `present` hits to add a confidence dimension.
2. Build evidence windows from cleaner, TOC-free body text in future runs (a light regex filter to drop lines that are mostly leader-dots/page-number table-of-contents artifacts before window assembly).
3. For ambiguous mechanism types specifically (interest vs. grievance arbitration), consider keeping a slightly larger window that preserves the article/section header immediately preceding a clause, not just the clause body.
4. If these are addressed, a modestly larger pilot (still capped, e.g. 8-10 rows) covering the remaining Texas/Ohio matched-city rows would be the natural next scaling step — not yet a full-corpus run.
