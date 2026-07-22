#!/usr/bin/env python3
"""Run a fail-closed direct-SDK preflight gate before a large scout run.

Plan-only mode never loads credentials or calls a backend. Executed mode first
runs the existing bounded three-call transport diagnostic and may then run one
explicit one-row production-runner probe. Probe output remains quarantined.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "scripts" / "diagnose_direct_sdk_hosted_search_transport.py"
SCOUT = ROOT / "scripts" / "gabriel_state_source_scout.py"
ABSOLUTE_MAX_CALLS = 4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.4-nano")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--search-context-size", choices=("low", "medium", "high"), default="low"
    )
    parser.add_argument("--include-one-row-probe", action="store_true")
    parser.add_argument("--probe-input-csv", type=Path)
    parser.add_argument("--probe-output-dir", type=Path)
    parser.add_argument("--max-calls", type=int, default=4)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Write a sanitized plan without loading credentials or making calls.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not 3 <= args.max_calls <= ABSOLUTE_MAX_CALLS:
        raise SystemExit("ERROR: --max-calls must be between 3 and 4")
    if not 0 < args.timeout <= 30:
        raise SystemExit("ERROR: --timeout must be greater than 0 and at most 30")
    if args.include_one_row_probe:
        if args.max_calls < 4:
            raise SystemExit("ERROR: one-row probe requires --max-calls 4")
        if args.probe_input_csv is None or args.probe_output_dir is None:
            raise SystemExit(
                "ERROR: --include-one-row-probe requires --probe-input-csv and --probe-output-dir"
            )
        if not args.probe_input_csv.is_file():
            raise SystemExit(f"ERROR: probe input missing: {args.probe_input_csv}")
        with args.probe_input_csv.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 1:
            raise SystemExit("ERROR: probe input must contain exactly one data row")
    elif args.probe_input_csv is not None or args.probe_output_dir is not None:
        raise SystemExit("ERROR: probe paths require --include-one-row-probe")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"ERROR: output directory is nonempty: {args.output_dir}")
    if args.probe_output_dir and args.probe_output_dir.exists() and any(args.probe_output_dir.iterdir()):
        raise SystemExit(f"ERROR: probe output directory is nonempty: {args.probe_output_dir}")


def plan(args: argparse.Namespace) -> dict[str, Any]:
    calls = [
        {"call": 1, "name": "no_search_control", "search": False, "prompt": "Reply with OK."},
        {"call": 2, "name": "hosted_search_trivial_public_query", "search": True},
        {"call": 3, "name": "hosted_search_municipality_style_query", "search": True},
    ]
    if args.include_one_row_probe:
        calls.append(
            {
                "call": 4,
                "name": "one_row_production_scout_probe",
                "search": True,
                "input_csv": str(args.probe_input_csv),
                "output_dir": str(args.probe_output_dir),
            }
        )
    return {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "plan_only": args.plan_only,
        "model": args.model,
        "timeout_seconds": args.timeout,
        "search_context_size": args.search_context_size,
        "max_calls": args.max_calls,
        "planned_call_count": len(calls),
        "external_calls_attempted": 0,
        "calls": calls,
        "pass_criteria": [
            "no-search returns response ID, nonempty OK text, and positive token usage",
            "both hosted-search diagnostics return response IDs, nonempty text, and positive token usage",
            "optional one-row probe completes parseably",
            "no secret exposure",
            "no two consecutive transport failures",
        ],
        "stage_boundary": "Preflight artifacts never enter queue, coverage, dashboard, corpus, or claims.",
    }


def command_preview(args: argparse.Namespace) -> list[list[str]]:
    diagnostic_dir = args.output_dir / "transport_diagnostic"
    commands = [[
        sys.executable,
        str(DIAGNOSTIC),
        "--output-dir", str(diagnostic_dir),
        "--model", args.model,
        "--timeout", str(args.timeout),
        "--search-context-size", args.search_context_size,
        "--max-calls", "3",
    ]]
    if args.include_one_row_probe:
        commands.append([
            sys.executable, str(SCOUT), "--live", "--live-backend", "direct-sdk",
            "--state", "ALL", "--allow-mixed-states",
            "--municipalities-csv", str(args.probe_input_csv),
            "--output-dir", str(args.probe_output_dir), "--prompt-mode", "compact",
            "--model", args.model, "--search-context-size", args.search_context_size,
            "--max-prompts", "1", "--live-hard-cap", "1", "--n-parallels", "1",
            "--sleep-between-prompts", "5", "--timeout", "90",
            "--direct-sdk-max-retries", "0",
            "--cost-log-path", str(args.probe_output_dir / "batch_cost_log.csv"),
        ])
    return commands


def write_artifacts(args: argparse.Namespace, payload: dict[str, Any], report_lines: list[str]) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "preflight_plan.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    commands = command_preview(args)
    (args.output_dir / "sanitized_command_preview.txt").write_text(
        "\n".join(shlex.join(command) for command in commands) + "\n", encoding="utf-8"
    )
    (args.output_dir / "preflight_gate_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )


def quarantine_probe_candidate(metadata: dict[str, Any], probe_dir: Path) -> str | None:
    candidate = metadata.get("candidates_csv_path")
    if not candidate:
        return None
    candidate_path = Path(str(candidate))
    if not candidate_path.is_absolute():
        candidate_path = ROOT / candidate_path
    if not candidate_path.is_file():
        raise RuntimeError("probe candidate handoff path is missing")
    destination = probe_dir / "quarantined_candidate_handoff.csv"
    shutil.move(str(candidate_path), destination)
    return str(destination)


def main() -> int:
    args = parse_args()
    validate_args(args)
    payload = plan(args)
    report = [
        "# Scout Preflight Gate",
        "",
        f"- Mode: `{'plan_only' if args.plan_only else 'executed'}`",
        f"- Planned calls: `{payload['planned_call_count']}` (hard cap `{args.max_calls}`)",
        "- Credential values written: `false`",
        "- Scout accounting changed: `false`",
        "",
        "## Pass criteria",
        "",
        *[f"- {criterion}." for criterion in payload["pass_criteria"]],
    ]
    if args.plan_only:
        payload["gate_status"] = "plan_only_not_executed"
        report.extend(["", "Gate status: **PLAN ONLY — no external calls made.**"])
        write_artifacts(args, payload, report)
        print(
            f"preflight_plan_only=true planned_calls={payload['planned_call_count']} "
            "external_calls_attempted=0"
        )
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    commands = command_preview(args)
    diagnostic = subprocess.run(commands[0], cwd=ROOT, text=True, capture_output=True)
    diagnostic_summary_path = args.output_dir / "transport_diagnostic" / "diagnostic_summary.json"
    if not diagnostic_summary_path.is_file():
        raise RuntimeError("transport diagnostic did not preserve diagnostic_summary.json")
    diagnostic_summary = json.loads(diagnostic_summary_path.read_text(encoding="utf-8"))
    payload["external_calls_attempted"] = int(diagnostic_summary.get("external_calls_attempted", 0))
    passed = diagnostic.returncode == 0 and diagnostic_summary.get("diagnosis_category") == "A"
    payload["transport_diagnostic"] = diagnostic_summary
    if passed and args.include_one_row_probe:
        probe = subprocess.run(commands[1], cwd=ROOT, text=True, capture_output=True)
        payload["external_calls_attempted"] += 1
        metadata_path = args.probe_output_dir / "run_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
        probe_passed = probe.returncode == 0 and int(metadata.get("n_parseable", 0)) == 1
        payload["one_row_probe"] = {
            "passed": probe_passed,
            "parseable_rows": metadata.get("n_parseable"),
            "candidate_rows": metadata.get("n_candidate_rows"),
            "quarantined_candidate_handoff": quarantine_probe_candidate(metadata, args.probe_output_dir) if probe_passed else None,
        }
        passed = passed and probe_passed
    payload["gate_status"] = "passed" if passed else "failed"
    report.extend(["", f"Gate status: **{payload['gate_status'].upper()}**."])
    write_artifacts(args, payload, report)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
