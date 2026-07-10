# GABRIEL Codify Seekonk/Wayland — Prompt Preview — 2026-07-10

## Selected rows (6, dry-run verified)

1. `ma_seekonk_public_works_2023` — MA, Seekonk, public_works
2. `ma_seekonk_library_2023` — MA, Seekonk, library
3. `ma_seekonk_police_2022` — MA, Seekonk, police
4. `ma_seekonk_fire_2022` — MA, Seekonk, fire
5. `ma_seekonk_teacher_2021` — MA, Seekonk, teacher
6. `ma_wayland_other_2021` — MA, Wayland, other (dispatch + Community Health Nurse), OCR-recovered

Full rationale: `gabriel_codify_seekonk_wayland_sample_selection_2026-07-10.md`. Windows: `gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv`. Only 6 of the 8 available calls are used — see the selection memo for why no further Seekonk/Wayland rows were added.

## Full codebook reference (unchanged)

19 attributes, defined in `scripts/gabriel_codify_pilot.py`'s `CATEGORIES` dict, verbatim identical to `docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md` Section 4. No codebook changes this run. Binary semantics preserved: `evidence_status` is `present` or `not_found` (this run's controlled vocabulary omits `unclear` from `evidence_status`, per this run's own task instructions — `unclear` is used only for `source_grounding_status`, not `evidence_status`, matching the exact schema Task I specifies).

## Output schema (per attribute, per row)

`evidence_status` (present/not_found), `excerpt` (verbatim, <40 words, blank if not_found), `excerpt_location` (if identifiable), `confidence` (fixed `not_applicable`), `caveat` (blank), plus `source_grounding_status` (grounded/unsupported/unclear/not_applicable) and `notes` computed by this session's new post-parse validation logic in `scripts/gabriel_codify_pilot.py`.

## Representative window (full text) — `ma_wayland_other_2021`

```
--- Excerpt 1 [Article 2] ---
2-1. The Town hereby recognizes the Union as the sole and exclusive collective bargaining
representative for all employees within the bargaining unit... By mutual agreement, effective July 1, 2005, the Town and the
Union hereby recognize the positions of Community Health Nurses as members of this
bargaining unit... In addition, this Town hereby recognizes all regular full and part-time clerical
employees... Such clerical employees shall
include those employed in the Town Office, the Department of Public Works (DPW) and the
Joint Communications Center, including all regular full-time dispatch personnel.

--- Excerpt 2 [Article 3] ---
Newly hired Dispatchers shall be required to serve a probationary period of
three months... a lateral dispatcher... will serve a probationary period of six months...

[... 5 more excerpts: dispatcher/nurse-specific holiday pay rules, a CPR-training stipend clause
naming "Joint Communication Dispatcher" explicitly, the FY2023 wage-grade table (G-3 JCC
Dispatcher, G-4 JCC Dispatcher Coordinator, G-7A Public Health Nurse, G-15 Community
Health Nurse, with dollar-figure step tables), and a union dues-deduction clause -- 5,037
characters / ~789 words total, well under the 1,500-word max_words_per_call cap]
```

This window recovers this project's first-ever dispatch/nurse_health mechanism evidence source — see `wayland_bounded_ocr_recovery_2026-07-10.md` for how the underlying text was recovered from a 48-page image-scan PDF via a bounded, single-pass OCR run this session.

## Exact dry-run command used

```
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_seekonk_wayland_evidence_windows_2026-07-10.csv
```

Matches this run's task instructions exactly. Output: `tmp/gabriel_codify_pilots/2026-07-10_114636/` — `run_config.json` confirms `max_calls_allowed: 8`, `max_calls_requested: 8`, `use_harvard_proxy: true`, `n_attributes: 19`, `live_run_attempted: false`, all 6 `selected_contract_ids`. `dry_run_log.txt` confirms no network call and no credential read.

## Confirmation: source-window body headers are neutral and separator-safe

Every one of the 6 windows was built with strictly `--- Excerpt N [location] ---` separators (a bare sequence number and, where available, a genuine `Article`/`Section`/`Appendix` marker actually present in the source text) and passed the input-side mechanism-label contamination check (`_check_window_contamination()` in `scripts/gabriel_codify_pilot.py`) before this dry run ran successfully — a contamination hit would have caused `sys.exit(1)` before reaching this point.

**Separator-safety fix this session:** `scripts/gabriel_codify_pilot.py` now also validates every *returned* excerpt (post-live-call, before it is trusted as grounded) for boundary-leakage fragments of this project's own separator syntax, and cleans/downgrades any that are found — see `reshape_and_validate_outputs()`, added specifically to prevent the recurrence seen in the 2026-07-09 Massachusetts scale-up (4 of 70 present excerpts there had leaked separator fragments). Verified via unit tests against all 4 of those real historical leaked excerpts (all clean correctly) before this dry run.
