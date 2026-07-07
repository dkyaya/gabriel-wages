"""
proxy_pilot_must_have_sources.py — bounded, auditable Harvard Proxy pilot scaffold.

Purpose: a safe harness for future small, explicitly-approved pilots that ask the
Harvard HUIT OpenAI proxy to help evaluate this project's "must-have" source-needs
questions (see docs/analysis/all_groups_source_needs_2026-07-06.csv), using short,
already-collected text snippets already present in data/contracts.csv fields.

SAFETY MODEL — read before use:
  - Defaults to dry-run. No network call, no proxy import side effects, no key read.
  - Live calls require --live AND an explicit --limit (missing or >3 is refused).
  - The subscription key is read from the environment ONLY inside the live-call
    code path, and is never printed, logged, or written to any output file.
  - Every run writes to a fresh, timestamped directory under
    tmp/proxy_pilots/YYYY-MM-DD_HHMMSS/ and never overwrites a prior run.
  - Never modifies data/contracts.csv, data/city_coverage.csv, corpus/, or inbox/.
  - Does not ingest documents. Does not run GABRIEL. Does not call any model API
    unless --live is explicitly passed.

Usage (safe, no network call):
  python scripts/proxy_pilot_must_have_sources.py --dry-run --limit 2

Usage (live, requires explicit approval — see docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md):
  python scripts/proxy_pilot_must_have_sources.py --live --limit 1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "data" / "contracts.csv"
PILOT_OUTPUT_ROOT = ROOT / "tmp" / "proxy_pilots"

SCRIPT_NAME = "proxy_pilot_must_have_sources.py"
PROMPT_TEMPLATE_VERSION = "must_have_sources_pilot_v1_2026-07-07"
MODEL = "gpt-5.4-nano"
REASONING_EFFORT = "low"
LIVE_ROW_CEILING = 3

# ---------------------------------------------------------------------------
# Hardcoded pilot set — tied directly to open "must-have" items in
# docs/analysis/all_groups_source_needs_2026-07-06.csv. Each entry names a
# real, already-collected contract_id and a specific, narrow source-need
# question, plus which already-collected data/contracts.csv field holds the
# short text snippet this pilot would evaluate. No full corpus PDF is read by
# this script — only fields already present in data/contracts.csv.
# ---------------------------------------------------------------------------
PILOT_ROWS = [
    {
        "contract_id": "ma_seekonk_public_works_2023",
        "source_need_question": (
            "Does this already-collected snippet describe sanitation, refuse, or "
            "collection-duty content, or only general public-works/DPW content? "
            "(open must-have item: Seekonk CBA Appendix/job-description confirmation)"
        ),
        "snippet_field": "total_comp_note",
    },
    {
        "contract_id": "ma_arlington_public_works_2015",
        "source_need_question": (
            "Does this already-collected snippet name a distinct base-wage figure "
            "or classification grade for the dispatcher title, or only a general "
            "unit description? (open must-have item: Arlington dispatcher wage-tier "
            "detail)"
        ),
        "snippet_field": "total_comp_note",
    },
    {
        "contract_id": "ma_wayland_other_2021",
        "source_need_question": (
            "Does this already-collected snippet name a specific credential or "
            "degree requirement tied to a pay consequence for nurse or public-health "
            "titles, or only a general recognition-clause description? (open "
            "must-have item: Wayland nurse_health credential-to-pay detail)"
        ),
        "snippet_field": "total_comp_note",
    },
]

SYSTEM_PROMPT = """\
You are a careful research assistant helping audit whether a short, already-collected
text snippet answers a specific, narrow evidentiary question for a labor-economics
research project. You must not invent or infer content that is not literally present
in the snippet. Return a JSON object with exactly these keys:
  "answer": one of "yes", "no", or "inconclusive"
  "verbatim_support": a short verbatim span copied EXACTLY from the snippet that
                      supports your answer, or an empty string if none exists
  "notes": one concise sentence explaining the answer (max 30 words)

Do not paraphrase the verbatim_support field. Copy it character-for-character from
the snippet, or leave it empty. If the snippet does not contain enough information,
answer "inconclusive" and explain why in notes.
"""

PROMPT_TEMPLATE = """\
Source-need question:
{question}

Contract identifier: {contract_id}
City: {city_name}
Occupation class: {occupation_class}
Snippet field: {snippet_field}

Already-collected snippet (verbatim from data/contracts.csv, not a full document):
---
{snippet}
---

Return only the JSON object described in the system prompt.
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded, auditable Harvard Proxy pilot scaffold. Defaults to dry-run; "
            "live calls require --live and an explicit --limit of 1-3."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry-run confirmation (this is also the default with no flags).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Make real Harvard Proxy calls. Requires --limit (1-3). Off by default.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of pilot rows to process. Required for --live (max 3).",
    )
    parser.add_argument(
        "--rows",
        type=str,
        default=None,
        help=(
            "Comma-separated contract_id values to select instead of the hardcoded "
            "pilot set. Each must exist in data/contracts.csv."
        ),
    )
    return parser.parse_args()


def _read_contracts() -> dict[str, dict]:
    """Read data/contracts.csv read-only. Never writes to this file."""
    csv.field_size_limit(10_000_000)
    with open(CONTRACTS, newline="", encoding="utf-8") as f:
        return {row["obs_id"]: row for row in csv.DictReader(f)}


def _select_rows(args: argparse.Namespace, contracts: dict[str, dict]) -> list[dict]:
    if args.rows:
        requested_ids = [r.strip() for r in args.rows.split(",") if r.strip()]
        selected = []
        for contract_id in requested_ids:
            if contract_id not in contracts:
                print(f"ERROR: contract_id '{contract_id}' not found in data/contracts.csv.")
                sys.exit(1)
            selected.append({
                "contract_id": contract_id,
                "source_need_question": (
                    "Custom row selection — no pre-defined source-need question. "
                    "Review manually before any live use."
                ),
                "snippet_field": "total_comp_note",
            })
    else:
        selected = list(PILOT_ROWS)

    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


def _build_prompt(pilot_row: dict, contract: dict) -> str:
    snippet = contract.get(pilot_row["snippet_field"], "") or "(field is empty in data/contracts.csv)"
    return PROMPT_TEMPLATE.format(
        question=pilot_row["source_need_question"],
        contract_id=pilot_row["contract_id"],
        city_name=contract.get("city_name", ""),
        occupation_class=contract.get("occupation_class", ""),
        snippet_field=pilot_row["snippet_field"],
        snippet=snippet,
    )


def _make_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = PILOT_OUTPUT_ROOT / timestamp
    if out_dir.exists():
        print(f"ERROR: output directory {out_dir} already exists. Refusing to overwrite.")
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=False)
    return out_dir


def _write_run_config(out_dir: Path, args: argparse.Namespace, selected: list[dict]) -> None:
    config = {
        "script_name": SCRIPT_NAME,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "mode": "live" if args.live else "dry_run",
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "requested_limit": args.limit,
        "row_selection": "custom_rows" if args.rows else "hardcoded_pilot_set",
        "requested_row_count": len(selected),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(out_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _write_selected_rows(out_dir: Path, selected: list[dict], contracts: dict[str, dict]) -> None:
    fieldnames = [
        "contract_id", "city_name", "occupation_class", "source_need_question",
        "snippet_field", "snippet_preview",
    ]
    with open(out_dir / "selected_rows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pilot_row in selected:
            contract = contracts.get(pilot_row["contract_id"], {})
            snippet = contract.get(pilot_row["snippet_field"], "") or ""
            w.writerow({
                "contract_id": pilot_row["contract_id"],
                "city_name": contract.get("city_name", ""),
                "occupation_class": contract.get("occupation_class", ""),
                "source_need_question": pilot_row["source_need_question"],
                "snippet_field": pilot_row["snippet_field"],
                "snippet_preview": snippet[:200],
            })


def _write_prompt_preview(out_dir: Path, selected: list[dict], contracts: dict[str, dict]) -> list[str]:
    prompts = []
    lines = ["# Prompt Preview", "", f"Template version: `{PROMPT_TEMPLATE_VERSION}`", ""]
    for i, pilot_row in enumerate(selected, 1):
        contract = contracts.get(pilot_row["contract_id"])
        if contract is None:
            lines.append(f"## Row {i}: {pilot_row['contract_id']} — NOT FOUND in data/contracts.csv, skipped")
            lines.append("")
            continue
        prompt = _build_prompt(pilot_row, contract)
        prompts.append(prompt)
        lines.append(f"## Row {i}: {pilot_row['contract_id']}")
        lines.append("")
        lines.append("**System prompt:**")
        lines.append("```")
        lines.append(SYSTEM_PROMPT.strip())
        lines.append("```")
        lines.append("")
        lines.append("**User prompt:**")
        lines.append("```")
        lines.append(prompt.strip())
        lines.append("```")
        lines.append("")
    with open(out_dir / "prompt_preview.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return prompts


def _run_dry(out_dir: Path, selected: list[dict], args: argparse.Namespace) -> None:
    lines = [
        f"Dry-run at {datetime.now().isoformat(timespec='seconds')}",
        "",
        "NO NETWORK CALL WAS MADE. NO SUBSCRIPTION KEY WAS READ.",
        "",
        f"Rows selected: {len(selected)}",
    ]
    for i, pilot_row in enumerate(selected, 1):
        lines.append(f"  [{i}] {pilot_row['contract_id']}")
    lines.append("")
    lines.append(
        "Exact rows and prompt templates that WOULD be used are recorded in "
        "selected_rows.csv and prompt_preview.md in this same directory."
    )
    lines.append("")
    lines.append(
        "To make a real call, re-run with --live and an explicit --limit of 1-3, "
        "only after separate PI/user approval. See "
        "docs/analysis/harvard_proxy_pilot_usage_2026-07-06.md."
    )
    with open(out_dir / "dry_run_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


def _run_live(out_dir: Path, selected: list[dict], contracts: dict[str, dict], prompts: list[str]) -> None:
    # This code path is reached ONLY after the --live + --limit safety gate in
    # main() has already passed. The subscription key is read here, and only
    # here, so a dry-run (or an import of this module) never touches it.
    import os

    subscription_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("ERROR: HARVARD_SUBSCRIPTION_KEY not set in environment. Live call refused.")
        sys.exit(1)

    from openai import OpenAI  # imported only in the live path, never in dry-run

    client = OpenAI(
        api_key=subscription_key,
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
    )

    HERE = ROOT / "scripts"
    sys.path.insert(0, str(HERE))
    from log_api_spend import log_usage, print_totals  # noqa: E402

    log_lines = [f"Live run at {datetime.now().isoformat(timespec='seconds')}", ""]
    responses_path = out_dir / "responses.jsonl"
    parsed_rows = []

    with open(responses_path, "w", encoding="utf-8") as resp_f:
        for i, (pilot_row, prompt) in enumerate(zip(selected, prompts), 1):
            contract_id = pilot_row["contract_id"]
            print(f"  [{i}/{len(selected)}] {contract_id}: calling proxy ...")
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    reasoning_effort=REASONING_EFFORT,
                    response_format={"type": "json_object"},
                    max_completion_tokens=500,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                log_usage(response, SCRIPT_NAME, MODEL)
                content = response.choices[0].message.content or "{}"
                resp_f.write(json.dumps({"contract_id": contract_id, "raw_response": content}) + "\n")

                parsed = json.loads(content)
                verbatim = parsed.get("verbatim_support", "") or ""
                snippet = contracts.get(contract_id, {}).get(pilot_row["snippet_field"], "") or ""
                verified = bool(verbatim) and verbatim.strip() in snippet
                parsed_rows.append({
                    "contract_id": contract_id,
                    "answer": parsed.get("answer", ""),
                    "verbatim_support": verbatim,
                    "verbatim_verified": str(verified).lower(),
                    "notes": parsed.get("notes", ""),
                })
                log_lines.append(f"[{i}] {contract_id}: answer={parsed.get('answer', '')} "
                                  f"verbatim_verified={verified}")
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"[{i}] {contract_id}: ERROR — {e}")
                parsed_rows.append({
                    "contract_id": contract_id, "answer": "error",
                    "verbatim_support": "", "verbatim_verified": "false",
                    "notes": f"error: {e}",
                })

    with open(out_dir / "parsed_outputs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["contract_id", "answer", "verbatim_support",
                                          "verbatim_verified", "notes"])
        w.writeheader()
        w.writerows(parsed_rows)

    with open(out_dir / "live_run_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print("\n".join(log_lines))
    print_totals(SCRIPT_NAME)
    print(f"\nWrote responses to {responses_path}")
    print(f"Wrote parsed outputs to {out_dir / 'parsed_outputs.csv'}")


def main() -> None:
    args = _parse_args()

    if args.live:
        if args.limit is None:
            print("ERROR: --live requires an explicit --limit (1-3). Refusing to run.")
            sys.exit(1)
        if args.limit < 1 or args.limit > LIVE_ROW_CEILING:
            print(f"ERROR: --limit must be between 1 and {LIVE_ROW_CEILING} for --live. "
                  f"Got {args.limit}. Refusing to run.")
            sys.exit(1)

    contracts = _read_contracts()
    selected = _select_rows(args, contracts)
    if not selected:
        print("No rows selected. Nothing to do.")
        sys.exit(0)

    out_dir = _make_output_dir()
    _write_run_config(out_dir, args, selected)
    _write_selected_rows(out_dir, selected, contracts)
    prompts = _write_prompt_preview(out_dir, selected, contracts)

    print(f"Output directory: {out_dir}")

    if args.live:
        confirm_selected = [pilot_row for pilot_row in selected if pilot_row["contract_id"] in contracts]
        confirm_prompts = prompts[: len(confirm_selected)]
        _run_live(out_dir, confirm_selected, contracts, confirm_prompts)
    else:
        _run_dry(out_dir, selected, args)


if __name__ == "__main__":
    main()
