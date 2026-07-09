"""
gabriel_codify_pilot.py — bounded, auditable GABRIEL codify() pilot scaffold.

Purpose: a safe, repeatable harness for small, explicitly-approved pilots that ask
gabriel.codify() to code short evidence-window excerpts (already built from this
project's own corpus text) against the project's 11-code wage-mechanism codebook.
See docs/analysis/gabriel_codify_pilot_design_2026-07-08.md for the full design
and docs/analysis/gabriel_codify_interface_inspection_2026-07-08.md for the
gabriel.codify() interface this script relies on.

SAFETY MODEL — read before use:
  - Defaults to dry-run. No network call, no gabriel.codify() invocation, no key read.
  - Live calls require --live AND an explicit --max-calls (capped at 3 in code;
    raising the cap requires a deliberate code change, not a CLI flag).
  - Credentials are read from the environment ONLY inside the live-call code path,
    are checked for presence only (never printed, logged, or written to any
    output file), and a missing credential causes a clean refusal, not a crash.
  - Every run writes to a fresh, timestamped directory under
    tmp/gabriel_codify_pilots/YYYY-MM-DD_HHMMSS/ and never overwrites a prior run.
  - Never modifies data/contracts.csv, data/city_coverage.csv, corpus/, or inbox/.
    Reads a pre-built evidence-window CSV only; does not ingest or fetch documents.
  - Does not import gabriel, or read any credential, on the dry-run path.

Usage (safe, no network call):
  python scripts/gabriel_codify_pilot.py --dry-run
  python scripts/gabriel_codify_pilot.py --dry-run --max-calls 3

Usage (live, requires an available credential -- OPENAI_API_KEY or equivalent):
  python scripts/gabriel_codify_pilot.py --live --max-calls 3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WINDOWS_CSV = ROOT / "docs" / "analysis" / "gabriel_codify_pilot_evidence_windows_2026-07-08.csv"
PILOT_OUTPUT_ROOT = ROOT / "tmp" / "gabriel_codify_pilots"

# Hard ceiling. --max-calls above this is refused outright, regardless of what
# the caller passes -- raising this requires a deliberate code edit, not a flag.
HARD_MAX_CALLS = 3

MODEL = "gpt-5.4-mini"
REASONING_EFFORT = "low"
N_ROUNDS = 1

CATEGORIES = {
    "peer_comparator_wage_comparability": (
        "Language pegging this unit's wages to another city, employer, or "
        "peer-community rate -- a comparability clause."
    ),
    "arbitration_impasse_backstop": (
        "Any arbitration, mediation, or impasse-resolution clause (grievance or "
        "interest arbitration) -- capture regardless of type, but note which kind."
    ),
    "staffing_recruitment_retention": (
        "Language about recruiting, hiring processes, staffing levels, or "
        "retention incentives."
    ),
    "overtime_callback_minimum_staffing": (
        "Overtime pay rules, call-back pay, on-call pay, or minimum-staffing "
        "requirements."
    ),
    "classification_reclassification_wage_schedule": (
        "Wage/pay schedules, step plans, job classification or reclassification "
        "rules."
    ),
    "training_certification_education": (
        "Training requirements, certification pay, or education incentive pay."
    ),
    "premium_pay_differentials": (
        "Shift differentials, special-duty pay, or other premium pay categories."
    ),
    "subcontracting_outsourcing": (
        "Language permitting or restricting subcontracting or outsourcing of "
        "bargaining-unit work."
    ),
    "total_compensation_benefits": (
        "Health insurance, pension, or other non-wage benefit language."
    ),
    "safety_risk_public_safety": (
        "Language framing the work as hazardous or invoking public-safety risk."
    ),
    "other": "Any other clearly mechanism-relevant excerpt not covered above.",
}

ADDITIONAL_INSTRUCTIONS = """\
You are coding short excerpts from public-sector labor agreements (collective
bargaining agreements, meet-and-confer agreements, or arbitration awards) for
the presence of specific wage-setting mechanisms. For EACH mechanism code:

1. Decide evidence_status: "present" only if the excerpt text itself contains
   language matching the code's description; "not_found" if no such language
   appears anywhere in the excerpt; "unclear" only if language is ambiguous
   or borderline.
2. If present or unclear, quote a SHORT VERBATIM SPAN (under 40 words) copied
   EXACTLY from the excerpt text -- do not paraphrase, summarize, or combine
   non-adjacent sentences. Never invent or infer text that is not literally
   present in the excerpt.
3. Do NOT infer, generalize, or make any causal claim about wages, mechanism
   strength, or effect. You are locating text, not evaluating what it means
   or whether it works.
4. Default to "not_found" whenever you are not certain the language is
   present. Do not guess or extrapolate from institutional context outside
   the excerpt.
5. Report a confidence level (high/medium/low) for your own judgment, and a
   one-sentence caveat/note if anything about the match is uncertain,
   partial, or drawn from a fragment.

This excerpt window is a compact reassembly of previously-identified passages
from one bargaining document. It is NOT the full document -- do not assume
missing context implies absence; code only what is visible in the given text.
"""


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Default mode. No network call.")
    mode.add_argument("--live", action="store_true", help="Make real gabriel.codify() calls. Requires --max-calls.")
    p.add_argument(
        "--max-calls", type=int, default=None,
        help=f"Number of rows to code. Required with --live. Hard-capped at {HARD_MAX_CALLS}.",
    )
    p.add_argument(
        "--windows-csv", type=Path, default=DEFAULT_WINDOWS_CSV,
        help="Evidence-window CSV to read (see gabriel_codify_pilot_evidence_windows_2026-07-08.csv).",
    )
    p.add_argument("--contract-id", type=str, default=None, help="Optional: restrict to one contract_id.")
    return p.parse_args()


def _read_windows(path: Path, contract_id: str | None) -> list[dict]:
    if not path.exists():
        print(f"ERROR: windows CSV not found: {path}")
        sys.exit(1)
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if contract_id:
        rows = [r for r in rows if r["contract_id"] == contract_id]
    return rows


def _make_output_dir() -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = PILOT_OUTPUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=False)
    return out_dir


def _write_run_config(out_dir: Path, args: argparse.Namespace, selected: list[dict],
                       live_attempted: bool, reason_not_attempted: str | None) -> None:
    config = {
        "run_timestamp": datetime.now().isoformat(),
        "function": "gabriel.codify",
        "column_name": "window_text",
        "save_dir": str(out_dir / "gabriel_save_dir"),
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "n_rounds": N_ROUNDS,
        "max_calls_allowed": HARD_MAX_CALLS,
        "max_calls_requested": args.max_calls,
        "selected_contract_ids": [r["contract_id"] for r in selected],
        "categories": CATEGORIES,
        "live_run_attempted": live_attempted,
        "live_run_reason_not_attempted": reason_not_attempted,
    }
    with (out_dir / "run_config.json").open("w") as f:
        json.dump(config, f, indent=2)
    with (out_dir / "run_config.json").open() as f:
        json.load(f)  # parse back immediately


def _write_selected_windows(out_dir: Path, selected: list[dict]) -> None:
    if not selected:
        return
    fieldnames = list(selected[0].keys())
    path = out_dir / "selected_windows.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in selected:
            w.writerow(r)
    with path.open(newline="") as f:
        list(csv.DictReader(f))  # parse back immediately


def _write_prompt_preview(out_dir: Path, selected: list[dict]) -> None:
    lines = [
        "# GABRIEL Codify Pilot Prompt Preview (script-generated)",
        "",
        "## Categories",
        "```python",
        json.dumps(CATEGORIES, indent=2),
        "```",
        "",
        "## additional_instructions",
        "```text",
        ADDITIONAL_INSTRUCTIONS,
        "```",
        "",
        "## Selected windows",
        "",
    ]
    for r in selected:
        lines.append(f"### {r['contract_id']} ({r.get('window_id', '')})")
        lines.append(f"- state/city/occupation_class: {r.get('state')}/{r.get('city')}/{r.get('occupation_class')}")
        lines.append(f"- source_file: {r.get('source_file')}")
        lines.append(f"- chars: {r.get('window_token_or_char_count')}")
        lines.append("")
    (out_dir / "prompt_preview.md").write_text("\n".join(lines))


def _credential_status() -> dict:
    import os
    return {
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "OPENAI_BASE_URL": bool(os.environ.get("OPENAI_BASE_URL")),
        "HARVARD_SUBSCRIPTION_KEY": bool(os.environ.get("HARVARD_SUBSCRIPTION_KEY")),
    }


def _run_dry(out_dir: Path, selected: list[dict]) -> None:
    _write_selected_windows(out_dir, selected)
    _write_prompt_preview(out_dir, selected)
    _write_run_config(out_dir, args=_LAST_ARGS, selected=selected,
                       live_attempted=False, reason_not_attempted="--dry-run passed (or --live not requested).")
    log = [
        "GABRIEL codify pilot -- dry run log",
        f"Run timestamp: {datetime.now().isoformat()}",
        f"Rows selected: {len(selected)}",
        "NO NETWORK CALL WAS MADE. NO CREDENTIAL WAS READ.",
        f"Outputs written to: {out_dir}",
    ]
    (out_dir / "dry_run_log.txt").write_text("\n".join(log) + "\n")
    print("Dry run complete. See", out_dir)


def _run_live(out_dir: Path, selected: list[dict], max_calls: int) -> None:
    creds = _credential_status()
    if not (creds["OPENAI_API_KEY"] or creds["HARVARD_SUBSCRIPTION_KEY"]):
        reason = (
            "No usable credential present (checked OPENAI_API_KEY and "
            "HARVARD_SUBSCRIPTION_KEY presence only, no values read). Refusing "
            "live call; falling back to dry-run outputs."
        )
        print("ERROR:", reason)
        _run_dry(out_dir, selected)
        return

    try:
        import gabriel
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"ERROR: failed to import gabriel: {e}")
        _write_run_config(out_dir, args=_LAST_ARGS, selected=selected,
                           live_attempted=False, reason_not_attempted=f"gabriel import failed: {e}")
        return

    import pandas as pd

    rows = selected[:max_calls]
    df = pd.DataFrame(rows)

    _write_selected_windows(out_dir, rows)
    errors = []
    try:
        result_df = gabriel.codify(
            df=df,
            column_name="window_text",
            save_dir=str(out_dir / "gabriel_save_dir"),
            categories=CATEGORIES,
            additional_instructions=ADDITIONAL_INSTRUCTIONS,
            model=MODEL,
            reasoning_effort=REASONING_EFFORT,
            n_rounds=N_ROUNDS,
        )
    except Exception as e:
        errors.append({"error": str(e), "type": type(e).__name__})
        with (out_dir / "errors.jsonl").open("w") as f:
            for err in errors:
                f.write(json.dumps(err) + "\n")
        _write_run_config(out_dir, args=_LAST_ARGS, selected=selected,
                           live_attempted=True, reason_not_attempted=None)
        (out_dir / "live_run_log.txt").write_text(
            f"Live call FAILED on first attempt: {e}\nStopping per no-retry policy.\n"
        )
        print("ERROR: live call failed:", e)
        return

    result_df.to_csv(out_dir / "parsed_outputs.csv", index=False)
    with (out_dir / "raw_outputs.jsonl").open("w") as f:
        for _, row in result_df.iterrows():
            f.write(json.dumps(row.to_dict(), default=str) + "\n")

    _write_run_config(out_dir, args=_LAST_ARGS, selected=selected, live_attempted=True, reason_not_attempted=None)
    (out_dir / "live_run_log.txt").write_text(
        f"Live call(s) completed: {len(rows)} row(s) coded.\nOutputs: parsed_outputs.csv, raw_outputs.jsonl\n"
    )
    print("Live run complete. See", out_dir)


_LAST_ARGS: argparse.Namespace | None = None


def main() -> None:
    global _LAST_ARGS
    args = _parse_args()
    _LAST_ARGS = args

    if args.live:
        if args.max_calls is None:
            print("ERROR: --live requires an explicit --max-calls.")
            sys.exit(1)
        if args.max_calls > HARD_MAX_CALLS:
            print(f"ERROR: --max-calls {args.max_calls} exceeds the hard cap of {HARD_MAX_CALLS}.")
            sys.exit(1)

    selected = _read_windows(args.windows_csv, args.contract_id)
    if not selected:
        print("ERROR: no rows selected from", args.windows_csv)
        sys.exit(1)

    out_dir = _make_output_dir()

    if args.live:
        _run_live(out_dir, selected, max_calls=args.max_calls)
    else:
        _run_dry(out_dir, selected)


if __name__ == "__main__":
    main()
