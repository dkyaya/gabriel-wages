# Harvard Proxy Pilot Usage Guide — 2026-07-06

**Type:** usage doc for `scripts/proxy_pilot_must_have_sources.py`. Read this alongside `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md` and `docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md` before running anything.

## Evidence-window mode (2026-07-07 revision)

As of 2026-07-07, this script no longer builds its prompts from a single `data/contracts.csv` metadata field (e.g. `total_comp_note`). Instead, for each selected pilot row it:
1. Resolves the row's `full_text_path` from `data/contracts.csv` and confirms the corpus file exists (read-only — never modifies the file).
2. Extracts the file's text using this project's own existing `ingest/extract_text.py` utility (text-layer-first, local OCR fallback if needed — no network access, no new extraction logic).
3. Searches the extracted text for a curated list of target terms specific to that row's source-need question.
4. Builds a short, bounded evidence window (roughly 200 characters before and after each match, capped at a small number of matches per term and windows per row) around each match.
5. Writes those evidence windows — not a metadata snippet — into `evidence_windows.csv` and into the rendered prompt in `prompt_preview.md`.

If no target term matches anywhere in a document's extracted text, the row's `evidence_window_count` is 0 and both `selected_rows.csv` and `prompt_preview.md` say so explicitly — this is not an error, but it is a strong signal that a live call for that row would not be useful yet (see the rule below).

Named pilot sets available via `--pilot-set` (see `PILOT_SETS` in the script for the exact rows and terms each uses):
- `must_have` (default) — all four currently-tracked must-have rows: Arlington dispatchers, Franklin custodial, Seekonk sanitation, Wayland nurse_health/dispatch.
- `dispatch_custodial` — Arlington dispatcher row plus Franklin custodial row.
- `sanitation_seekonk` — the Seekonk public-works/sanitation row only.
- `custodial_only` — Franklin and Georgetown custodial rows, for comparing two cities' custodial wage-classification evidence side by side.

## Dry-run command examples

Dry-run is the default. No network call is made, no subscription key is read, and nothing outside `tmp/proxy_pilots/` is written. Evidence-window construction (reading an already-collected corpus PDF and running local text extraction) happens in dry-run mode too — it requires no network access or credential.

```bash
# Default pilot set (must_have, 4 rows), explicit --dry-run flag
python scripts/proxy_pilot_must_have_sources.py --dry-run

# Named pilot set: Arlington dispatcher + Franklin custodial
python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set dispatch_custodial --limit 2

# Named pilot set: Seekonk sanitation only
python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set sanitation_seekonk --limit 1

# Named pilot set: compare two cities' custodial evidence
python scripts/proxy_pilot_must_have_sources.py --dry-run --pilot-set custodial_only

# Same as above with no flags at all — dry-run is the default behavior
python scripts/proxy_pilot_must_have_sources.py

# Select specific already-collected contract_id values instead of a named pilot set
python scripts/proxy_pilot_must_have_sources.py --dry-run --rows ma_seekonk_public_works_2023,ma_arlington_public_works_2015

# Explicit single-row selection with custom search terms
python scripts/proxy_pilot_must_have_sources.py --dry-run --contract-id ma_georgetown_other_2020 --terms "licensed,unlicensed,custodian,maintenance"
```

Each dry-run creates a new timestamped directory under `tmp/proxy_pilots/` and writes `run_config.json`, `selected_rows.csv`, `evidence_windows.csv`, `prompt_preview.md`, and `dry_run_log.txt`. **Inspect `evidence_windows.csv` and `prompt_preview.md` before ever considering a live run** — see the rule below.

## Live command examples — do not run unless explicitly approved

**Do not run any of the following without separate, explicit PI/user approval for that specific run.** Live mode makes real, billed calls to the Harvard HUIT OpenAI proxy. **A live pilot should remain at 1-2 calls, not the full 3-call ceiling, until the prompt's requested structured-output schema and this scaffold's response-parsing logic have been reviewed together following an initial small live run** (see `docs/analysis/harvard_proxy_evidence_window_scaffold_revision_2026-07-07.md` §7).

```bash
# Live run, single row, explicit limit — the smallest possible live pilot
python scripts/proxy_pilot_must_have_sources.py --live --limit 1 --pilot-set sanitation_seekonk

# Live run, two rows from the dispatch/custodial set
python scripts/proxy_pilot_must_have_sources.py --live --limit 2 --pilot-set dispatch_custodial

# Live run against one specific, explicitly named row
python scripts/proxy_pilot_must_have_sources.py --live --limit 1 --rows ma_seekonk_public_works_2023
```

Live mode will refuse to run if `--limit` is missing or greater than 3, and will refuse to run if `HARVARD_SUBSCRIPTION_KEY` is not set in the environment at the moment the live call is attempted. Live mode also skips (does not call the proxy for) any selected row whose evidence-window count is zero, logging that row as `skipped_no_evidence` rather than sending an empty or near-empty prompt. Neither the script nor this doc can substitute for actual PI/user approval — the `--live` flag documents intent, it does not grant permission.

## Rule: do not run live if evidence_windows.csv is empty or irrelevant

Before any `--live` run, open the newest dry-run's `evidence_windows.csv` for every row you intend to include:
- If a row has **zero rows** in `evidence_windows.csv` (an `evidence_window_count` of 0 in `selected_rows.csv`), do not include that row in a live run. Either revise its target-term list and re-run dry-run first, or treat the zero-match result itself as the finding (the document likely does not contain the sought content in the form searched for) and skip the live call entirely.
- If a row's evidence windows are all boilerplate matches (e.g. a table-of-contents line, a generic recognition-clause listing) rather than substantive content, review `prompt_preview.md` closely — some target terms (single common words especially) can be consumed by early, low-value matches before richer content later in the document is reached. Prefer rows where at least one window clearly contains the substantive answer to the source-need question before proceeding to a live call for that row.

## Expected outputs

Every run (dry or live) writes to `tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/`:

| File | Dry-run | Live | Contents |
| --- | --- | --- | --- |
| `run_config.json` | yes | yes | Mode, model, pilot set/row-selection method, limit, evidence-window construction parameters, row count, timestamp. No secrets. |
| `selected_rows.csv` | yes | yes | Which contract_id rows were selected, city/occupation_class, unit title, corpus file path, whether it exists, the source-need question, the target-term list used, and the evidence-window count found. |
| `evidence_windows.csv` | yes | yes | One row per matched evidence window (or one explicit "no match" row per row with zero matches): contract_id, corpus file, file type, extraction method, search term, match index, character offsets, and the verbatim window text. |
| `prompt_preview.md` | yes | yes | The exact system and user prompt text that would be (or was) sent, per selected row, with actual corpus evidence windows embedded (not a metadata snippet). |
| `dry_run_log.txt` | yes | no | Plain-text confirmation that no network call was made, listing selected rows and their evidence-window counts. |
| `live_run_log.txt` | no | yes | Plain-text per-row result summary (answer, whether the returned key-evidence span was verified against the sent evidence windows, or `skipped_no_evidence` for zero-match rows). |
| `responses.jsonl` | no | yes | One JSON line per row: `contract_id` plus the raw model response text. |
| `parsed_outputs.csv` | no | yes | Structured columns: `contract_id`, `answer`, `key_evidence`, `verbatim_verified`, `notes`. |

## Safety checklist before a live run

- [ ] The specific run (row count, which rows, why) has been explicitly approved by the user/PI, not just inferred from a prior conversation.
- [ ] `--limit` is set and is 1, 2, or 3 — never omitted, never higher.
- [ ] The rows being targeted are either the reviewed hardcoded pilot set or a small, explicitly named `--rows` list — never an unbounded selection.
- [ ] `HARVARD_SUBSCRIPTION_KEY` is set in the current shell's environment (or in a `.env` file the script will find) — the script will refuse to run live without it, but confirm you are not about to be prompted to paste a key into a command line or a file this session shouldn't touch.
- [ ] You are prepared to review `logs/api_spend_log.csv` afterward for the estimated cost of the run (see `scripts/log_api_spend.py`'s own caveat: figures are estimates based on public list pricing, not Harvard's actual billed rate).
- [ ] You understand this pilot's outputs are not production data — nothing it writes should be treated as a corpus row, a validated finding, or grounds for editing `data/contracts.csv` without further review.

## How to inspect outputs

```bash
# Find the most recent pilot run
ls -t tmp/proxy_pilots/ | head -1

# Inspect what was configured
cat tmp/proxy_pilots/<timestamp>/run_config.json

# Inspect exactly which rows were selected and how many evidence windows each found
cat tmp/proxy_pilots/<timestamp>/selected_rows.csv

# Inspect the actual corpus evidence windows before trusting any prompt
cat tmp/proxy_pilots/<timestamp>/evidence_windows.csv

# Inspect the exact rendered prompts (including the evidence windows above)
cat tmp/proxy_pilots/<timestamp>/prompt_preview.md

# For a live run, inspect the parsed results and raw responses
cat tmp/proxy_pilots/<timestamp>/parsed_outputs.csv
cat tmp/proxy_pilots/<timestamp>/responses.jsonl
```

Never `cat` or otherwise print `.env` or any file expected to contain `HARVARD_SUBSCRIPTION_KEY`. This script never writes the key to any output file, but a general safety habit is to avoid printing environment-variable dumps (`env`, `printenv`) in any session where the key might be set.

## How not to commit tmp outputs unless separately approved

`tmp/` is not tracked by git in this project's normal workflow (every prior session in this repository's history has excluded `tmp/` from commits). Pilot outputs under `tmp/proxy_pilots/` should be treated the same way:
- Do not `git add tmp/` or otherwise stage pilot output directories as part of a routine commit.
- If a specific pilot run's outputs are valuable enough to preserve permanently (e.g., to document a finding that will inform a future source-acquisition decision), copy the specific files you want to keep into `docs/analysis/` under a new, dated filename, and get explicit approval before committing them — do not commit the raw `tmp/proxy_pilots/` directory itself.
- Relay bundles created for a session (per this project's standing `tmp/agent_relay_bundle_*` convention) may reference or include small dry-run logs for auditability, but should not bundle raw `responses.jsonl` files from a live run without confirming there is nothing sensitive in them first.

## How to choose pilot rows

The named pilot sets (`PILOT_SETS` in `scripts/proxy_pilot_must_have_sources.py`) are deliberately narrow and tied to specific, already-identified "must-have" items in `docs/analysis/all_groups_source_needs_2026-07-06.csv` — as of this revision, the clearest still-open item is the Seekonk sanitation Appendix/job-description confirmation (`sanitation_seekonk`); the dispatcher and custodial/facilities rows (`dispatch_custodial`, `custodial_only`) illustrate the same evidence-window pattern for source needs that are largely already resolved by direct human review, included here mainly as calibration examples; the Wayland nurse_health/dispatch row (part of `must_have` only, since its content spans both groups) requires an OCR fallback and is the slowest row to build evidence windows for.

To choose different pilot rows:
- Prefer `contract_id` values that already exist in `data/contracts.csv` — the script will refuse to run if a requested `--rows` or `--contract-id` value is not found.
- Prefer rows whose `full_text_path` corpus file already exists on disk and has a `text_quality` of `clean` or `ocr_messy` in `data/contracts.csv` — a `partial` extraction may yield too little text to search reliably.
- When adding a new named pilot-set entry, write a curated target-term list mixing a few generic single words (e.g. "wage," "overtime") with several specific multi-word phrases (e.g. "Community Safety Dispatcher," "transfer station") — generic single-word terms are more likely to be consumed by early, low-value matches (e.g. a table of contents) before the match cap per term is reached, while specific phrases are more likely to land directly on the substantive passage.
- Use `--contract-id` with a custom `--terms` list for a one-off exploratory dry-run against a row not yet part of a named pilot set, before deciding whether it deserves its own permanent entry in `PILOT_SETS`.
- Do not select more than 3 rows for a live run under any circumstances with this scaffold; if a larger pilot is genuinely needed, that is a new scaffold decision requiring its own review, not an argument for raising this script's ceiling.
