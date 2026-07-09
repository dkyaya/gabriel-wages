# GABRIEL Codify Pilot Audit — 2026-07-08

## Whether live calls ran

**No.** Zero live `gabriel.codify()` calls were attempted this session. Per this run's own hard boundary ("if credentials are missing... do not make live calls, produce dry-run only"), the pilot stopped after confirming no usable API credential is present in this environment (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, and this repo's own `HARVARD_SUBSCRIPTION_KEY` are all unset — checked as booleans only, no values printed). See `gabriel_codify_interface_inspection_2026-07-08.md` for the full credential finding and `tmp/gabriel_codify_pilots/2026-07-09_111259/run_config.json` (`live_run_attempted: false`) and `dry_run_log.txt` for the run record.

## Calls attempted / succeeded / failed

0 attempted / 0 succeeded / 0 failed. No `gabriel_codify_pilot_outputs_2026-07-08.csv` was created, since there is no live output to parse.

## Whether outputs were parseable

Not applicable — no outputs exist to parse this session.

## Whether excerpts were source-grounded

Not directly testable this session (no live output). However, the pilot's **design itself** was built specifically to make this testable in a future run with credentials: the three evidence windows were assembled by concatenating excerpt bodies from this project's own prior, hand-verified extraction (`houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`, `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`), with mechanism-name labels deliberately stripped out of the window text. This means a future live run's `codify()` output can be directly diffed against a known-correct answer key (which mechanisms are genuinely present, and their exact verbatim text) without needing a separate ground-truth pass — see Task C's evidence-window design in `gabriel_codify_pilot_design_2026-07-08.md` Section 3.

## Any hallucination/overreach observed

Not applicable — no live output was generated.

## Comparison with deterministic excerpts already extracted

Not directly run this session (no live output), but the comparison baseline is fully prepared: for each of the 3 selected contracts, `evidence_status=present` mechanism counts from the prior hand extraction are 8 (Houston fire), 10 (Houston non-safety), and 11 (Columbus fire) out of 11 possible codes. A future live run should report, per contract: how many of these already-known-present mechanisms `codify()` also marks present; whether any excerpt it returns is NOT a verbatim substring of the window text sent (a hallucination signal); and whether it marks anything `present` that the hand extraction marked `not_found` (a false-positive/overreach signal).

## Whether codify seems useful for a future state/city/mechanism evidence layer

**Interface-level assessment (no live evidence yet):** the interface is well-suited in principle. `gabriel.codify(df, column_name, categories={...}, additional_instructions=...)` maps cleanly onto exactly the tabular evidence-layer shape this project wants (`state | city | occupation_class | contract_id | mechanism_code | evidence_status | excerpt | location | confidence | notes`) — a DataFrame in, a coded DataFrame out, with an explicit fixed codebook rather than model-invented categories. The `response_fn`/`get_all_responses_fn` injection points also mean this project's existing Harvard Proxy calling pattern could in principle be wired in later without forking `codify()` itself. **This is a promising-but-unverified assessment** — it should not be treated as confirmed usefulness until at least one live run's outputs pass the source-grounding audit above.

## Recommended next step

1. **Obtain a usable credential** (either `OPENAI_API_KEY`/`OPENAI_BASE_URL`, or wire `gabriel.codify()`'s `response_fn` to this repo's existing Harvard Proxy client pattern from `scripts/proxy_pilot_must_have_sources.py`) before attempting the first live call.
2. Once credentialed, run exactly the 3-row pilot already fully designed and staged in `docs/analysis/gabriel_codify_pilot_evidence_windows_2026-07-08.csv` / `gabriel_codify_pilot_prompt_preview_2026-07-08.md` / `scripts/gabriel_codify_pilot.py` (if created — see Task G), respecting the same 3-call cap.
3. On the first live run, complete this audit's still-open sections (source-grounding, hallucination check, deterministic-comparison) before deciding whether to scale `codify()` beyond this pilot.
