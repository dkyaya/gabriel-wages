# Harvard Proxy Pilot Usage Guide — 2026-07-06

**Type:** usage doc for `scripts/proxy_pilot_must_have_sources.py`. Read this alongside `docs/analysis/harvard_proxy_calling_scaffold_review_2026-07-06.md` before running anything.

## Dry-run command examples

Dry-run is the default. No network call is made, no subscription key is read, and nothing outside `tmp/proxy_pilots/` is written.

```bash
# Default hardcoded pilot set (3 rows), explicit --dry-run flag
python scripts/proxy_pilot_must_have_sources.py --dry-run

# Limit to the first 2 rows of the hardcoded pilot set
python scripts/proxy_pilot_must_have_sources.py --dry-run --limit 2

# Same as above with no flags at all — dry-run is the default behavior
python scripts/proxy_pilot_must_have_sources.py

# Select specific already-collected contract_id values instead of the hardcoded set
python scripts/proxy_pilot_must_have_sources.py --dry-run --rows ma_seekonk_public_works_2023,ma_arlington_public_works_2015
```

Each dry-run creates a new timestamped directory under `tmp/proxy_pilots/` and writes `run_config.json`, `selected_rows.csv`, `prompt_preview.md`, and `dry_run_log.txt`. Inspect these before ever considering a live run.

## Live command examples — do not run unless explicitly approved

**Do not run any of the following without separate, explicit PI/user approval for that specific run.** Live mode makes real, billed calls to the Harvard HUIT OpenAI proxy.

```bash
# Live run, single row, explicit limit — the smallest possible live pilot
python scripts/proxy_pilot_must_have_sources.py --live --limit 1

# Live run, all 3 hardcoded pilot rows (the maximum this scaffold permits)
python scripts/proxy_pilot_must_have_sources.py --live --limit 3

# Live run against one specific, explicitly named row
python scripts/proxy_pilot_must_have_sources.py --live --limit 1 --rows ma_seekonk_public_works_2023
```

Live mode will refuse to run if `--limit` is missing or greater than 3, and will refuse to run if `HARVARD_SUBSCRIPTION_KEY` is not set in the environment at the moment the live call is attempted. Neither the script nor this doc can substitute for actual PI/user approval — the `--live` flag documents intent, it does not grant permission.

## Expected outputs

Every run (dry or live) writes to `tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/`:

| File | Dry-run | Live | Contents |
| --- | --- | --- | --- |
| `run_config.json` | yes | yes | Mode, model, limit, row-selection method, row count, timestamp. No secrets. |
| `selected_rows.csv` | yes | yes | Which contract_id rows were selected, their city/occupation_class, the source-need question, and a short (200-char) snippet preview. |
| `prompt_preview.md` | yes | yes | The exact system and user prompt text that would be (or was) sent, per selected row. |
| `dry_run_log.txt` | yes | no | Plain-text confirmation that no network call was made, listing selected rows. |
| `live_run_log.txt` | no | yes | Plain-text per-row result summary (answer, whether the returned verbatim span was verified against the source snippet). |
| `responses.jsonl` | no | yes | One JSON line per row: `contract_id` plus the raw model response text. |
| `parsed_outputs.csv` | no | yes | Structured columns: `contract_id`, `answer`, `verbatim_support`, `verbatim_verified`, `notes`. |

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

# Inspect exactly which rows and prompts were used
cat tmp/proxy_pilots/<timestamp>/selected_rows.csv
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

The hardcoded `PILOT_ROWS` list in `scripts/proxy_pilot_must_have_sources.py` is deliberately narrow and tied to specific, already-identified "must-have" items in `docs/analysis/all_groups_source_needs_2026-07-06.csv` (as of this scaffold's creation, the clearest still-open item is the Seekonk sanitation Appendix/job-description confirmation; the other two hardcoded rows illustrate the same pattern for dispatcher and nurse_health source needs, most of which are already resolved by direct human review and are included here mainly as calibration examples for this scaffold, not as live-call priorities).

To choose different pilot rows:
- Prefer `contract_id` values that already exist in `data/contracts.csv` — the script will refuse to run if a requested `--rows` value is not found.
- Prefer rows where the source-need question can be answered from a field already in `data/contracts.csv` (e.g., `total_comp_note`, `arbitration_clause_text`) rather than requiring a full corpus PDF read — this keeps the pilot's scope narrow and avoids re-implementing this project's PDF-extraction pipeline inside a pilot script.
- Do not select more than 3 rows for a live run under any circumstances with this scaffold; if a larger pilot is genuinely needed, that is a new scaffold decision requiring its own review, not an argument for raising this script's ceiling.
