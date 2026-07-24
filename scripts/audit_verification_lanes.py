#!/usr/bin/env python3
"""Audit verification lanes without mutating queue, coverage, or evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


TERMINAL_LIVE_STATUSES = {
    "reachable_http",
    "reachable_pdf_or_document",
    "reachable_html",
    "blocked_or_forbidden",
    "not_found",
    "timeout",
    "connection_error",
    "too_large",
    "unsupported_scheme",
    "invalid_url",
    "ssl_error",
    "error",
    "duplicate_of_verified_source",
    "duplicate_same_url_pending",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def byte_bucket(value: str) -> str:
    try:
        size = int(value or 0)
    except ValueError:
        return "invalid"
    if size == 0:
        return "0"
    if size <= 65_536:
        return "1_to_64KiB"
    if size <= 1_048_576:
        return "64KiB_to_1MiB"
    if size <= 10_485_760:
        return "1MiB_to_10MiB"
    return "over_10MiB"


def classify_lane(lane: dict[str, object]) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(str(lane["dry_run_output_dir"]))
    live_dir = Path(str(lane["live_output_dir"]))
    base: dict[str, Any] = {
        "lane_id": lane["lane_id"],
        "input_csv": input_path.as_posix(),
        "expected_rows": int(lane["expected_rows"]),
        "classification": "not_started",
        "ledger_rows": 0,
        "terminal_rows": 0,
        "duplicate_verification_ids": 0,
        "missing_candidate_rows": int(lane["expected_rows"]),
        "unexpected_candidate_rows": 0,
        "duplicate_group_count": 0,
        "duplicate_reuse_rows": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "verification_status_counts": {},
        "content_type_distribution": {},
        "bytes_read_distribution": {},
    }
    if not input_path.exists():
        base.update(classification="missing_artifacts", detail="input_csv_missing")
        return base
    if sha256_file(input_path) != lane["input_sha256"]:
        base.update(classification="failed", detail="input_hash_mismatch")
        return base
    input_rows = read_csv(input_path)
    input_ids = [row["verification_id"] for row in input_rows]
    if len(input_ids) != len(set(input_ids)):
        base.update(
            classification="failed",
            detail="duplicate_verification_ids_in_input",
            duplicate_verification_ids=len(input_ids) - len(set(input_ids)),
        )
        return base
    input_group_by_id = {
        row["verification_id"]: row.get("duplicate_source_group_id", "")
        for row in input_rows
    }

    output_dir: Path | None = None
    mode = ""
    if live_dir.exists():
        output_dir, mode = live_dir, "live"
    elif dry_dir.exists():
        output_dir, mode = dry_dir, "dry_run"
    if output_dir is None:
        return base
    ledger_path = output_dir / "verification_ledger.csv"
    summary_path = output_dir / "verification_summary.json"
    if not ledger_path.exists() or not summary_path.exists():
        base.update(
            classification="missing_artifacts",
            detail="ledger_or_summary_missing",
            mode=mode,
        )
        return base

    ledger_rows = read_csv(ledger_path)
    ledger_ids = [row["verification_id"] for row in ledger_rows]
    duplicate_ids = len(ledger_ids) - len(set(ledger_ids))
    missing = len(set(input_ids) - set(ledger_ids))
    extra = len(set(ledger_ids) - set(input_ids))
    group_mismatches = sum(
        row["verification_id"] in input_group_by_id
        and row.get("duplicate_source_group_id", "")
        != input_group_by_id[row["verification_id"]]
        for row in ledger_rows
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    statuses = Counter(row.get("verification_status", "") for row in ledger_rows)
    terminal = (
        statuses["dry_run_planned"]
        if mode == "dry_run"
        else sum(statuses[status] for status in TERMINAL_LIVE_STATUSES)
    )
    content_types = Counter(
        (row.get("content_type", "").split(";", 1)[0].strip().lower() or "unknown")
        for row in ledger_rows
    )
    byte_sizes = Counter(byte_bucket(row.get("bytes_read", "")) for row in ledger_rows)
    base.update(
        {
            "mode": mode,
            "ledger_rows": len(ledger_rows),
            "terminal_rows": terminal,
            "duplicate_verification_ids": duplicate_ids,
            "missing_candidate_rows": missing,
            "unexpected_candidate_rows": extra,
            "duplicate_group_mismatches": group_mismatches,
            "duplicate_group_count": len(
                {
                    row.get("duplicate_source_group_id", "")
                    for row in ledger_rows
                    if row.get("duplicate_source_group_id", "")
                }
            ),
            "duplicate_reuse_rows": (
                statuses["duplicate_of_verified_source"]
                + statuses["duplicate_same_url_pending"]
            ),
            "urls_opened": int(summary.get("urls_opened", 0)),
            "network_calls": int(summary.get("network_calls", 0)),
            "verification_status_counts": dict(sorted(statuses.items())),
            "content_type_distribution": dict(sorted(content_types.items())),
            "bytes_read_distribution": dict(sorted(byte_sizes.items())),
        }
    )
    if duplicate_ids or missing or extra or group_mismatches:
        base.update(classification="failed", detail="identity_or_group_coverage_failure")
    elif mode == "dry_run" and summary.get("status") == "dry_run_passed":
        base.update(
            classification="dry_run_passed",
            detail="complete_offline_plan_artifacts",
        )
    elif mode == "live" and terminal == len(input_rows):
        base.update(
            classification="completed_merge_eligible",
            detail="all_rows_terminal",
        )
    elif mode == "live" and terminal:
        base.update(classification="partial", detail="some_terminal_rows")
    elif mode == "live":
        base.update(classification="failed", detail="no_terminal_rows")
    else:
        base.update(classification="failed", detail="unrecognized_summary_status")
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

    complete_count = classes["completed_merge_eligible"]
    noncomplete = [
        lane for lane in lanes if lane["classification"] != "completed_merge_eligible"
    ]
    if complete_count == len(lanes) and not cross_lane_duplicates:
        recommendation = "merge_all_verification_lanes"
    elif (
        complete_count > 0
        and not cross_lane_duplicates
        and all(
            lane["classification"] in {"not_started", "failed", "missing_artifacts"}
            and int(lane["terminal_rows"]) == 0
            for lane in noncomplete
        )
    ):
        recommendation = "merge_completed_lanes_only_with_user_approval"
    else:
        recommendation = "do_not_merge_until_resume_or_review"

    combined_statuses: Counter[str] = Counter()
    combined_content_types: Counter[str] = Counter()
    combined_bytes: Counter[str] = Counter()
    for lane in lanes:
        combined_statuses.update(lane["verification_status_counts"])
        combined_content_types.update(lane["content_type_distribution"])
        combined_bytes.update(lane["bytes_read_distribution"])
    payload: dict[str, object] = {
        "schema_version": "2.0.0",
        "round_id": manifest["round_id"],
        "manifest": manifest_path.as_posix(),
        "lane_count": len(lanes),
        "lane_classification_counts": dict(sorted(classes.items())),
        "cross_lane_duplicate_verification_ids": cross_lane_duplicates,
        "planned_candidate_rows": sum(int(lane["expected_rows"]) for lane in lanes),
        "ledger_rows": sum(int(lane["ledger_rows"]) for lane in lanes),
        "terminal_rows": sum(int(lane["terminal_rows"]) for lane in lanes),
        "urls_opened": sum(int(lane["urls_opened"]) for lane in lanes),
        "network_calls": sum(int(lane["network_calls"]) for lane in lanes),
        "duplicate_reuse_rows": sum(
            int(lane["duplicate_reuse_rows"]) for lane in lanes
        ),
        "verification_status_counts": dict(sorted(combined_statuses.items())),
        "content_type_distribution": dict(sorted(combined_content_types.items())),
        "bytes_read_distribution": dict(sorted(combined_bytes.items())),
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
        f"- Terminal rows: {payload['terminal_rows']}",
        f"- Cross-lane duplicate verification IDs: {cross_lane_duplicates}",
        f"- URLs opened according to summaries: {payload['urls_opened']}",
        f"- Network calls according to summaries: {payload['network_calls']}",
        f"- Duplicate rows reusing in-lane fetches: {payload['duplicate_reuse_rows']}",
        f"- Status counts: `{json.dumps(payload['verification_status_counts'], sort_keys=True)}`",
        f"- Content types: `{json.dumps(payload['content_type_distribution'], sort_keys=True)}`",
        f"- Bytes read: `{json.dumps(payload['bytes_read_distribution'], sort_keys=True)}`",
        f"- Recommendation: `{recommendation}`",
        "",
        "| Lane | Classification | Expected | Ledger | Terminal | Missing |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for lane in lanes:
        report_lines.append(
            f"| {lane['lane_id']} | `{lane['classification']}` | "
            f"{lane['expected_rows']} | {lane['ledger_rows']} | "
            f"{lane['terminal_rows']} | {lane['missing_candidate_rows']} |"
        )
    report_lines.extend(
        [
            "",
            "This auditor does not update the candidate queue, coverage, contracts,",
            "ingestion, codification, extraction, or any analysis-ready evidence.",
            "",
        ]
    )
    (output_dir / "verification_lane_audit_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    (output_dir / "verification_merge_recommendation.md").write_text(
        f"# Verification Merge Recommendation\n\n`{recommendation}`\n\n"
        "Dry-run completion is never authority to open URLs or merge a live "
        "verified-source ledger. Use a separately authorized serial merge task.\n",
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
