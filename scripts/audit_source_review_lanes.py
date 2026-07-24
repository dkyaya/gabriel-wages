#!/usr/bin/env python3
"""Audit source-review pilot lane outputs without mutating project layers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


LIVE_TERMINAL_STATUSES = {
    "reviewed_relevant",
    "reviewed_context_only",
    "reviewed_not_relevant",
    "duplicate_of_reviewed_source",
    "download_failed",
    "needs_manual_review",
    "oversized_deferred",
    "excluded",
}
SAFETY_COUNTER_FIELDS = [
    "urls_opened",
    "network_calls",
    "documents_downloaded",
    "documents_parsed",
    "pdfs_parsed",
    "ocr_runs",
    "content_artifacts_written",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_lane(lane: dict[str, object]) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(str(lane["dry_run_output_dir"]))
    live_dir = Path(str(lane["future_live_output_dir"]))
    expected = int(lane["expected_rows"])
    result: dict[str, object] = {
        "lane_id": lane["lane_id"],
        "expected_rows": expected,
        "classification": "not_started",
        "mode": "",
        "ledger_rows": 0,
        "terminal_rows": 0,
        "duplicate_source_review_ids": 0,
        "duplicate_candidate_queue_ids": 0,
        "missing_rows": expected,
        "unexpected_rows": 0,
        "source_review_status_counts": {},
    }
    if not input_path.exists():
        return {**result, "classification": "missing_artifacts", "detail": "input_missing"}
    if sha256_file(input_path) != lane["input_sha256"]:
        return {**result, "classification": "failed", "detail": "input_hash_mismatch"}
    input_rows = read_csv(input_path)
    if len(input_rows) != expected:
        return {
            **result,
            "classification": "failed",
            "detail": "input_row_count_mismatch",
        }
    input_review_ids = [row["source_review_id"] for row in input_rows]
    input_queue_ids = [row["candidate_queue_row_id"] for row in input_rows]
    if len(input_review_ids) != len(set(input_review_ids)) or len(
        input_queue_ids
    ) != len(set(input_queue_ids)):
        return {
            **result,
            "classification": "failed",
            "detail": "duplicate_input_identity",
        }
    output_dir: Path | None = None
    mode = ""
    if live_dir.exists():
        output_dir, mode = live_dir, "live"
    elif dry_dir.exists():
        output_dir, mode = dry_dir, "dry_run"
    if output_dir is None:
        return result
    ledger_path = output_dir / "source_review_ledger.csv"
    summary_path = output_dir / "source_review_summary.json"
    timing_path = output_dir / "source_review_timing.csv"
    if not all(path.exists() for path in (ledger_path, summary_path, timing_path)):
        return {
            **result,
            "classification": "missing_artifacts",
            "detail": "ledger_summary_or_timing_missing",
            "mode": mode,
        }
    ledger = read_csv(ledger_path)
    summary = read_json(summary_path)
    review_ids = [row.get("source_review_id", "") for row in ledger]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in ledger]
    statuses = Counter(row.get("source_review_status", "") for row in ledger)
    missing = len(set(input_review_ids) - set(review_ids))
    unexpected = len(set(review_ids) - set(input_review_ids))
    terminal = (
        statuses["planned_not_reviewed"]
        if mode == "dry_run"
        else sum(statuses[status] for status in LIVE_TERMINAL_STATUSES)
    )
    result.update(
        {
            "mode": mode,
            "ledger_rows": len(ledger),
            "terminal_rows": terminal,
            "duplicate_source_review_ids": len(review_ids) - len(set(review_ids)),
            "duplicate_candidate_queue_ids": len(queue_ids) - len(set(queue_ids)),
            "missing_rows": missing,
            "unexpected_rows": unexpected,
            "source_review_status_counts": dict(sorted(statuses.items())),
            "url_access_status_counts": dict(
                sorted(Counter(row.get("url_access_status", "") for row in ledger).items())
            ),
            "download_status_counts": dict(
                sorted(Counter(row.get("download_status", "") for row in ledger).items())
            ),
            **{
                field: int(summary.get(field, 0))
                for field in SAFETY_COUNTER_FIELDS
            },
        }
    )
    identity_failure = (
        result["duplicate_source_review_ids"]
        or result["duplicate_candidate_queue_ids"]
        or missing
        or unexpected
    )
    if identity_failure:
        result.update(classification="failed", detail="identity_coverage_failure")
    elif (
        mode == "dry_run"
        and summary.get("status") == "dry_run_passed"
        and terminal == expected
        and not any(int(summary.get(field, 0)) for field in SAFETY_COUNTER_FIELDS)
    ):
        result.update(
            classification="dry_run_passed",
            detail="complete_offline_schema_plan",
        )
    elif (
        mode == "live"
        and summary.get("status") == "completed"
        and terminal == expected
    ):
        result.update(
            classification="completed_merge_eligible",
            detail="all_rows_terminal_and_audited",
        )
    elif terminal:
        result.update(classification="partial", detail="some_terminal_rows")
    else:
        result.update(classification="failed", detail="incomplete_or_unsafe_output")
    return result


def aggregate_counts(
    lanes: list[dict[str, object]], field: str
) -> dict[str, int]:
    combined: Counter[str] = Counter()
    for lane in lanes:
        combined.update(lane.get(field, {}))
    return dict(sorted(combined.items()))


def audit(manifest_path: Path, output_dir: Path) -> dict[str, object]:
    manifest = read_json(manifest_path)
    lanes = [classify_lane(lane) for lane in manifest["lanes"]]
    all_review_ids: list[str] = []
    all_queue_ids: list[str] = []
    for lane in manifest["lanes"]:
        rows = read_csv(Path(str(lane["input_csv"])))
        all_review_ids.extend(row["source_review_id"] for row in rows)
        all_queue_ids.extend(row["candidate_queue_row_id"] for row in rows)
    classifications = Counter(str(lane["classification"]) for lane in lanes)
    if lanes and classifications["completed_merge_eligible"] == len(lanes):
        recommendation = "merge_all_source_review_lanes"
    elif classifications["completed_merge_eligible"]:
        recommendation = "merge_completed_source_review_lanes_with_user_approval"
    elif lanes and classifications["dry_run_passed"] == len(lanes):
        recommendation = "dry_run_complete_no_live_source_review"
    else:
        recommendation = "do_not_merge_until_resume_or_review"
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "pilot_id": manifest["pilot_id"],
        "manifest": manifest_path.as_posix(),
        "planned_rows": int(manifest["selected_rows"]),
        "lane_count": len(lanes),
        "ledger_rows": sum(int(lane["ledger_rows"]) for lane in lanes),
        "terminal_rows": sum(int(lane["terminal_rows"]) for lane in lanes),
        "cross_lane_duplicate_source_review_ids": len(all_review_ids)
        - len(set(all_review_ids)),
        "cross_lane_duplicate_candidate_queue_ids": len(all_queue_ids)
        - len(set(all_queue_ids)),
        "classification_counts": dict(sorted(classifications.items())),
        "source_review_status_counts": aggregate_counts(
            lanes, "source_review_status_counts"
        ),
        "url_access_status_counts": aggregate_counts(
            lanes, "url_access_status_counts"
        ),
        "download_status_counts": aggregate_counts(
            lanes, "download_status_counts"
        ),
        **{
            field: sum(int(lane.get(field, 0)) for lane in lanes)
            for field in SAFETY_COUNTER_FIELDS
        },
        "merge_recommendation": recommendation,
        "lanes": lanes,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "source_review_lane_audit_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_lines = [
        "# Source-Review Lane Audit Report",
        "",
        f"- Pilot: `{manifest['pilot_id']}`",
        f"- Planned rows: {payload['planned_rows']}",
        f"- Ledger rows: {payload['ledger_rows']}",
        f"- Terminal/planned rows: {payload['terminal_rows']}",
        f"- Recommendation: `{recommendation}`",
        f"- URL opens: {payload['urls_opened']}",
        f"- Downloads: {payload['documents_downloaded']}",
        f"- Parses/OCR: {payload['documents_parsed']} / {payload['ocr_runs']}",
        "",
        "## Lanes",
        "",
    ]
    for lane in lanes:
        report_lines.append(
            f"- `{lane['lane_id']}`: `{lane['classification']}`; "
            f"{lane['ledger_rows']}/{lane['expected_rows']} rows."
        )
    report_lines.extend(
        [
            "",
            "This audit does not open URLs or mutate candidate, routing, triage, "
            "ingestion, codification, or contract layers.",
        ]
    )
    (output_dir / "source_review_lane_audit_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    (output_dir / "source_review_merge_recommendation.md").write_text(
        "# Source-Review Merge Recommendation\n\n"
        f"`{recommendation}`\n\n"
        "Dry-run outputs are schema plans, not source ratings and not mergeable "
        "live review evidence.\n",
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
    result = audit(Path(args.manifest), Path(args.output_dir))
    print(
        f"Source-review lane audit: {result['ledger_rows']}/"
        f"{result['planned_rows']} rows; {result['merge_recommendation']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
