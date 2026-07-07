# Harvard Proxy Evidence-Window Scaffold Revision — 2026-07-07

**Type:** dated revision memo. Documents why the original pilot scaffold's snippet source was insufficient and what changed in this revision. **No live API/model/proxy call was made in producing this memo or the revised script.**

## 1. What the old scaffold did

The original `scripts/proxy_pilot_must_have_sources.py` (created 2026-07-06/07) selected a small, hardcoded set of `contract_id` rows tied to open "must-have" items in `docs/analysis/all_groups_source_needs_2026-07-06.csv`, then built its dry-run and live prompts entirely from a single `data/contracts.csv` metadata field — specifically `total_comp_note` — for each selected row. `selected_rows.csv` recorded a 200-character preview of that field, and `prompt_preview.md` embedded the full field value directly into the rendered prompt. No corpus PDF was read at any point; the scaffold's own docstring and usage doc explicitly described this as a deliberate scope choice ("keeps the pilot's scope narrow and avoids re-implementing this project's PDF-extraction pipeline inside a pilot script").

## 2. Why snippet_field from contracts.csv was insufficient

`total_comp_note` (and every other free-text field in `data/contracts.csv`) is a short, RA-written administrative summary of a row's source and content — a pointer describing what the underlying document is and confirms, not a substitute for the document's own text. For the three source-need questions this scaffold was built to help evaluate — whether a CBA contains dispatcher staffing rules, custodial/facilities wage classifications, or sanitation/transfer-station language — the actual answer lives in the corpus PDF's own body text (recognition clauses, classification tables, wage schedules, side letters), not in a one- or two-sentence administrative note about the document. Sending only `total_comp_note` to a future live call would have asked the model to answer a source-need question using a summary that was never designed to contain that level of detail, risking a confidently wrong or falsely "inconclusive" answer regardless of what the underlying document actually says. This is the same category of problem this project's own ingestion pipeline (`ingest/extract_spans.py`) is built to avoid: verbatim capture from the source, not RA paraphrase or summary, is the standard this project holds every other stage of its work to, and the original scaffold did not meet that standard for its own pilot prompts.

## 3. Why dry-run selected_rows.csv correctly has no model answer

`selected_rows.csv`, in both the original and revised scaffold, is a pre-call artifact: it records what would be sent to the model, not what the model said. It correctly has no `answer`, `evidence_classification`, or similar model-output column, because dry-run mode never calls the proxy — there is no model output to record. This is intentional and should not be "fixed" in a future revision by adding a placeholder or synthetic answer column; doing so would blur the distinction this project's tone and evidentiary discipline depend on between "what we sent" and "what a model said," and could make a future reviewer mistake a dry-run artifact for a live result.

## 4. What evidence-window mode changes

The revised scaffold replaces the single-metadata-field snippet with a **corpus evidence-window** builder:

- For each selected pilot row, the script resolves the row's `full_text_path` from `data/contracts.csv` and confirms the file exists on disk (never modifying it).
- It extracts text from the actual corpus file using this project's own existing extraction utility (`ingest/extract_text.py`'s `extract()` function), which already implements the project's standard text-layer-first, OCR-fallback strategy — no new extraction logic was written for this scaffold; the existing, already-reviewed component is reused directly.
- It then searches the extracted text for a small, curated list of target terms specific to each pilot row's source-need question (for example, "Community Safety Dispatcher," "minimum coverage," and "EMD" for the Arlington dispatcher row; "sanitation," "transfer station," and "CDL" for the Seekonk row).
- For each match, it builds a bounded evidence window (a fixed number of characters before and after the match) rather than sending the full document, keeping the prompt scoped to the specific passages a future live call would actually need to reason about.
- These evidence windows, not any `data/contracts.csv` metadata field, are now what `prompt_preview.md` renders into the user-facing prompt, and they are separately recorded in a new `evidence_windows.csv` file for direct inspection before any live call is considered.
- Where no target term is found anywhere in a document's extracted text, the scaffold records that explicitly (an `evidence_window_count` of 0 and a clear note), rather than silently sending an empty or near-empty prompt.

## 5. Safety protections retained

Every safety property of the original scaffold is unchanged in this revision:
- Dry-run remains the default; no flag is required to stay in dry-run mode.
- Live calls still require an explicit `--live` flag plus an explicit `--limit` of 1-3; a missing or out-of-range limit still refuses before any output directory is created.
- The subscription key is still read only inside the live-call code path, never at import time or during evidence-window construction (evidence-window building is pure local text processing — reading a PDF already on disk and running local text-extraction code — and requires no network access or credential).
- No new corpus files are created, and no existing corpus file is modified — evidence-window construction is read-only against already-collected files.
- `data/contracts.csv` and `data/city_coverage.csv` remain untouched.
- Output directories remain timestamped and non-overwriting.
- OCR, where it is invoked at all (only for the one already-known `ocr_messy` pilot row, Wayland's contract), happens through the project's existing local `ingest/extract_text.py` utility, which the project's own `ingest/README.md` already documents as a no-network-call, local-only tool.

## 6. Remaining limitations

- **Target-term lists are hand-curated per pilot row, not automatically derived.** A future pilot row added to this scaffold would need its own reviewed term list; the scaffold does not attempt to infer relevant search terms from a source-need question automatically.
- **Evidence windows are built by simple substring/term search, not semantic matching.** A document that discusses the same substantive content using different wording than the curated term list would not surface a match. This is a precision-over-recall design choice appropriate for a pre-live-call safety preview, but it means an empty `evidence_windows.csv` for a given row is not proof the underlying document lacks relevant content — only that the specific curated terms were not found verbatim.
- **Window boundaries are character-based, not sentence- or clause-aware.** A window may begin or end mid-sentence. This is acceptable for a human-reviewed dry-run preview but would need refinement before any evidence window is treated as a clean, citation-ready excerpt.
- **The Wayland row (`ma_wayland_other_2021`) requires OCR** (confirmed `ocr_messy` in `data/contracts.csv`), which is slower than text-layer extraction for the other pilot rows; this scaffold accepts that cost for evidence-window construction in dry-run mode but this remains worth noting for anyone extending the pilot set.
- **This scaffold still does not attempt live response parsing beyond what the original scaffold implemented** (a simple verbatim-verification check against the sent evidence, not the full structured schema — `evidence_classification`, `confidence`, `cautions`, etc. — described in the prompt itself). Live-mode parsing logic should be reviewed and likely extended before any live pilot is run, not assumed to already match the prompt's requested output schema in full.

## 7. Recommended next step before live calls

Before any `--live` run is considered:
1. A user/PI should directly inspect the newest dry-run's `evidence_windows.csv` and `prompt_preview.md` for each pilot set of interest, confirming the evidence windows actually contain the passages relevant to the source-need question (not just that a term matched somewhere).
2. If `evidence_windows.csv` is empty or contains only irrelevant matches for a given row, that row should not be sent to a live call yet — either the term list needs revision, or the underlying document genuinely lacks the sought content (in which case a live call would not help and should not be run).
3. Once evidence windows are confirmed relevant, a live pilot should proceed at the smallest possible scale (1-2 calls, not the full 3-call ceiling) until the prompt's requested structured-output schema and this scaffold's response-parsing logic are reviewed together and confirmed to match.
