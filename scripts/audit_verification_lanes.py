#!/usr/bin/env python3
"""Audit verification lanes without modifying queue, coverage, or evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_lane(lane: dict[str, object]) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(str(lane["dry_run_output_dir"]))
    live_dir = Path(str(lane["live_output_dir"]))
    base = {
        "lane_id": lane["lane_id"],
        "input_csv": input_path.as_posix(),
        "expected_rows": int(lane["expected_rows"]),
        "classification": "not_started",
        "ledger_rows": 0,
        "duplicate_verification_ids": 0,
        "missing_candidate_rows": int(lane["expected_rows"]),
        "duplicate_group_count": 0,
        "urls_opened": 0,
        "network_calls": 0,
    }
    if not input_path.exists():
        base["classification"] = "missing_artifacts"
        base["detail"] = "input_csv_missing"
        return base
    if sha256_file(input_path) != lane["input_sha256"]:
        base["classification"] = "failed"
        base["detail"] = "input_hash_mismatch"
        return base
    input_rows = read_csv(input_path)
    input_ids = [row["verification_id"] for row in input_rows]
    if len(input_ids) != len(set(input_ids)):
        base["classification"] = "failed"
        base["detail"] = "duplicate_verification_ids_in_input"
        base["duplicate_verification_ids"] = len(input_ids) - len(set(input_ids))
        return base

    output_dir: Path | None = None
    mode = ""
    if live_dir.exists():
        output_dir = live_dir
        mode = "live"
    elif dry_dir.exists():
        output_dir = dry_dir
        mode = "dry_run"
    if output_dir is None:
        return base
    ledger_path = output_dir / "verification_ledger.csv"
    summary_path = output_dir / "verification_summary.json"
    if not ledger_path.exists() or not summary_path.exists():
        base["classification"] = "missing_artifacts"
        base["detail"] = "ledger_or_summary_missing"
        return base
    ledger_rows = read_csv(ledger_path)
    ledger_ids = [row["verification_id"] for row in ledger_rows]
    duplicate_ids = len(ledger_ids) - len(set(ledger_ids))
    missing = len(set(input_ids) - set(ledger_ids))
    extra = len(set(ledger_ids) - set(input_ids))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    base.update(
        {
            "mode": mode,
            "ledger_rows": len(ledger_rows),
            "duplicate_verification_ids": duplicate_ids,
            "missing_candidate_rows": missing,
            "unexpected_candidate_rows": extra,
            "duplicate_group_count": len(
                {row.get("duplicate_source_group_id", "") for row in ledger_rows}
            ),
            "urls_opened": int(summary.get("urls_opened", 0)),
            "network_calls": int(summary.get("network_calls", 0)),
        }
    )
    if duplicate_ids or missing or extra:
        base["classification"] = "failed"
        base["detail"] = "identity_coverage_failure"
    elif mode == "dry_run" and summary.get("status") == "dry_run_passed":
        base["classification"] = "dry_run_passed"
        base["detail"] = "complete_offline_plan_artifacts"
    elif mode == "live":
        statuses = Counter(row.get("verification_status", "") for row in ledger_rows)
        terminal = sum(
            count
            for status, count in statuses.items()
            if status and status not in {"planned_not_verified", "pending"}
        )
        if terminal == len(input_rows):
            base["classification"] = "completed_merge_eligible"
            base["detail"] = "all_rows_terminal"
        elif terminal:
            base["classification"] = "partial"
            base["detail"] = "some_terminal_rows"
        else:
            base["classification"] = "failed"
            base["detail"] = "no_terminal_rows"
    else:
        base["classification"] = "failed"
        base["detail"] = "unrecognized_summary_status"
    return base


def audit(manifest_path: Path, output_dir: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lanes = [classify_lane(lane) for lane in manifest["lanes"]]
    classes = Counter(str(lane["classification"]) for lane in lanes)
    all_ids: list[str] = []
    for lane in manifest["lanes"]:
        path = Path(str(lane["input_csv"]))
        if path.exists():
            all_ids.extend(row["verification_id"] for row in read_csv(path))
    cross_lane_duplicates = len(all_ids) - len(set(all_ids))
    if classes["completed_merge_eligible"] == len(lanes) and not cross_lane_duplicates:
        recommendation = "merge_all_verification_lanes"
    elif classes["dry_run_passed"] == len(lanes) and not cross_lane_duplicates:
        recommendation = "dry_run_complete_do_not_merge_live_ledger"
    else:
        recommendation = "do_not_merge_until_resume_or_review"
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "round_id": manifest["round_id"],
        "manifest": manifest_path.as_posix(),
        "lane_count": len(lanes),
        "lane_classification_counts": dict(sorted(classes.items())),
        "cross_lane_duplicate_verification_ids": cross_lane_duplicates,
        "planned_candidate_rows": sum(int(lane["expected_rows"]) for lane in lanes),
        "ledger_rows": sum(int(lane["ledger_rows"]) for lane in lanes),
        "urls_opened": sum(int(lane["urls_opened"]) for lane in lanes),
        "network_calls": sum(int(lane["network_calls"]) for lane in lanes),
        "lanes": lanes,
        "merge_recommendation": recommendation,
        "accounting_mutations": 0,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "verification_lane_audit_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    report_lines = [
        f"# Verification Lane Audit — {manifest['round_id']}",
        "",
        f"- Lanes: {len(lanes)}",
        f"- Planned candidate rows: {payload['planned_candidate_rows']}",
        f"- Ledger rows inspected: {payload['ledger_rows']}",
        f"- Cross-lane duplicate verification IDs: {cross_lane_duplicates}",
        f"- URLs opened according to summaries: {payload['urls_opened']}",
        f"- Network calls according to summaries: {payload['network_calls']}",
        f"- Recommendation: `{recommendation}`",
        "",
        "| Lane | Classification | Expected | Ledger | Missing |",
        "|---|---|---:|---:|---:|",
    ]
    for lane in lanes:
        report_lines.append(
            f"| {lane['lane_id']} | `{lane['classification']}` | "
            f"{lane['expected_rows']} | {lane['ledger_rows']} | "
            f"{lane['missing_candidate_rows']} |"
        )
    report_lines.extend(
        [
            "",
            "This auditor does not update the candidate queue, coverage, contracts,",
            "ingestion, codification, or any analysis-ready evidence layer.",
            "",
        ]
    )
    (output_dir / "verification_lane_audit_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    (output_dir / "verification_merge_recommendation.md").write_text(
        f"# Verification Merge Recommendation\n\n`{recommendation}`\n\n"
        "A dry-run recommendation is not authority to open URLs or merge a live "
        "verified-source ledger. Use a separate explicitly authorized task.\n",
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = audit(Path(args.manifest), Path(args.output_dir))
    print(
        f"Verification lane audit: {payload['merge_recommendation']}; "
        f"rows={payload['ledger_rows']}; URLs opened={payload['urls_opened']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
