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
    "reviewed_metadata_and_artifact_saved",
    "reviewed_metadata_only_no_download",
    "download_too_large",
    "download_forbidden",
    "download_not_found",
    "download_timeout",
    "download_connection_error",
    "download_ssl_error",
    "unsupported_content_type",
    "parse_not_attempted",
    "needs_manual_review",
    "error",
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
FORBIDDEN_LIVE_COUNTERS = ["documents_parsed", "pdfs_parsed", "ocr_runs"]
DISTRIBUTION_FIELDS = [
    "source_review_status",
    "url_access_status",
    "download_status",
    "content_type_observed",
    "source_officialness_rating",
    "source_relevance_rating",
    "municipality_match_rating",
    "employer_match_rating",
    "bargaining_unit_match_rating",
    "document_type_rating",
    "extraction_readiness_rating",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def bytes_distribution(rows: list[dict[str, str]]) -> dict[str, int]:
    result: Counter[str] = Counter()
    for row in rows:
        try:
            value = int(row.get("content_byte_size") or 0)
        except ValueError:
            value = 0
        if value == 0:
            bucket = "0"
        elif value <= 64 * 1024:
            bucket = "1_to_64_kib"
        elif value <= 1024 * 1024:
            bucket = "64_kib_to_1_mib"
        elif value <= 10 * 1024 * 1024:
            bucket = "1_to_10_mib"
        elif value <= 25 * 1024 * 1024:
            bucket = "10_to_25_mib"
        else:
            bucket = "over_25_mib"
        result[bucket] += 1
    return dict(sorted(result.items()))


def count_distribution(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") for row in rows).items()))


def audit_artifacts(
    rows: list[dict[str, str]], output_dir: Path, *, mode: str
) -> dict[str, object]:
    content_paths = [
        Path(row["content_artifact_path"])
        for row in rows
        if row.get("content_artifact_path")
    ]
    metadata_paths = [
        Path(row["response_metadata_path"])
        for row in rows
        if row.get("response_metadata_path")
    ]
    sample_paths = [
        Path(row["content_sample_path"])
        for row in rows
        if row.get("content_sample_path")
    ]
    all_paths = content_paths + metadata_paths + sample_paths
    lane_local = all(is_within(path, output_dir) for path in all_paths)
    all_exist = all(path.is_file() for path in all_paths)
    hash_failures = 0
    size_failures = 0
    for row in rows:
        raw = row.get("content_artifact_path", "")
        if not raw:
            if row.get("content_hash"):
                hash_failures += 1
            continue
        path = Path(raw)
        if not path.is_file():
            continue
        expected_hash = row.get("content_hash", "")
        if not expected_hash or sha256_file(path) != expected_hash:
            hash_failures += 1
        try:
            expected_size = int(row.get("content_byte_size") or -1)
        except ValueError:
            expected_size = -1
        if expected_size != path.stat().st_size:
            size_failures += 1
    metadata_expected = len(rows) if mode == "live" else 0
    metadata_complete = len(metadata_paths) == metadata_expected
    passed = (
        lane_local
        and all_exist
        and hash_failures == 0
        and size_failures == 0
        and metadata_complete
    )
    if mode == "dry_run":
        passed = not all_paths
    return {
        "artifact_integrity_passed": passed,
        "artifact_paths_lane_local": lane_local,
        "artifact_paths_exist": all_exist,
        "content_artifact_files": len(content_paths),
        "metadata_artifact_files": len(metadata_paths),
        "content_sample_files": len(sample_paths),
        "content_hash_failures": hash_failures,
        "content_size_failures": size_failures,
    }


def classify_lane(lane: dict[str, object]) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(
        str(
            lane.get(
                "implementation_dry_run_output_dir",
                lane["dry_run_output_dir"],
            )
        )
    )
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
        "artifact_integrity_passed": False,
    }
    if not input_path.exists():
        return {
            **result,
            "classification": "missing_artifacts",
            "detail": "input_missing",
        }
    if sha256_file(input_path) != lane["input_sha256"]:
        return {
            **result,
            "classification": "failed",
            "detail": "input_hash_mismatch",
        }
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
    artifacts = audit_artifacts(ledger, output_dir, mode=mode)
    result.update(
        {
            "mode": mode,
            "output_dir": output_dir.as_posix(),
            "ledger_rows": len(ledger),
            "terminal_rows": terminal,
            "duplicate_source_review_ids": len(review_ids) - len(set(review_ids)),
            "duplicate_candidate_queue_ids": len(queue_ids) - len(set(queue_ids)),
            "missing_rows": missing,
            "unexpected_rows": unexpected,
            **{
                f"{field}_counts": count_distribution(ledger, field)
                for field in DISTRIBUTION_FIELDS
            },
            "content_byte_size_distribution": bytes_distribution(ledger),
            "rows_with_content_hash": sum(
                bool(row.get("content_hash")) for row in ledger
            ),
            "rows_with_pdf_page_count": sum(
                row.get("pdf_page_count", "") not in {"", "unknown"}
                for row in ledger
            ),
            "rows_with_known_text_layer": sum(
                row.get("text_layer_status", "") not in {"", "unknown"}
                for row in ledger
            ),
            **{
                field: int(summary.get(field, 0))
                for field in SAFETY_COUNTER_FIELDS
            },
            **artifacts,
        }
    )
    identity_failure = (
        result["duplicate_source_review_ids"]
        or result["duplicate_candidate_queue_ids"]
        or missing
        or unexpected
        or len(ledger) != expected
    )
    summary_unsafe = (
        int(summary.get("protected_writes", 0)) != 0
        or bool(summary.get("ingestion_attempted"))
        or bool(summary.get("codify_attempted"))
        or bool(summary.get("wage_extraction_attempted"))
    )
    forbidden_activity = any(
        int(summary.get(field, 0)) for field in FORBIDDEN_LIVE_COUNTERS
    )
    if identity_failure:
        result.update(classification="failed", detail="identity_coverage_failure")
    elif (
        mode == "dry_run"
        and summary.get("status") == "dry_run_passed"
        and terminal == expected
        and not any(
            int(summary.get(field, 0)) for field in SAFETY_COUNTER_FIELDS
        )
        and artifacts["artifact_integrity_passed"]
    ):
        result.update(
            classification="dry_run_passed",
            detail="complete_offline_schema_plan",
        )
    elif (
        mode == "live"
        and summary.get("status") == "completed"
        and terminal == expected
        and artifacts["artifact_integrity_passed"]
        and not summary_unsafe
        and not forbidden_activity
    ):
        result.update(
            classification="completed_merge_eligible",
            detail="all_rows_terminal_artifacts_local_and_safety_gates_passed",
        )
    elif mode == "live" and terminal and not summary_unsafe:
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
        recommendation = "merge_completed_lanes_only_with_user_approval"
    elif lanes and classifications["dry_run_passed"] == len(lanes):
        recommendation = "dry_run_complete_no_live_source_review"
    else:
        recommendation = "do_not_merge_until_resume_or_review"
    payload: dict[str, object] = {
        "schema_version": "1.1.0",
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
        **{
            f"{field}_counts": aggregate_counts(lanes, f"{field}_counts")
            for field in DISTRIBUTION_FIELDS
        },
        "content_byte_size_distribution": aggregate_counts(
            lanes, "content_byte_size_distribution"
        ),
        **{
            field: sum(int(lane.get(field, 0)) for lane in lanes)
            for field in SAFETY_COUNTER_FIELDS
        },
        "content_artifact_files": sum(
            int(lane.get("content_artifact_files", 0)) for lane in lanes
        ),
        "metadata_artifact_files": sum(
            int(lane.get("metadata_artifact_files", 0)) for lane in lanes
        ),
        "content_sample_files": sum(
            int(lane.get("content_sample_files", 0)) for lane in lanes
        ),
        "rows_with_content_hash": sum(
            int(lane.get("rows_with_content_hash", 0)) for lane in lanes
        ),
        "artifact_integrity_passed": all(
            bool(lane.get("artifact_integrity_passed")) for lane in lanes
        ),
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
        f"- Artifact integrity: {payload['artifact_integrity_passed']}",
        "",
        "## Lanes",
        "",
    ]
    for lane in lanes:
        report_lines.append(
            f"- `{lane['lane_id']}`: `{lane['classification']}`; "
            f"{lane['ledger_rows']}/{lane['expected_rows']} rows; "
            f"artifact integrity `{lane['artifact_integrity_passed']}`."
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
        "live review evidence. Live eligibility requires complete identities, "
        "terminal rows, lane-local artifacts, matching hashes, and clean safety "
        "markers.\n",
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
