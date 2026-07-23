#!/usr/bin/env python3
"""Audit isolated scout lane artifacts and recommend a later serial merge.

The auditor is read-only with respect to lane artifacts and shared project
accounting. It writes only three audit/recommendation files to ``--output-dir``.
It never invokes queue, coverage, yield, dashboard, priority, verification,
ingestion, or codification code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_OUTPUT_NAMES = {
    "parallel_lane_audit_summary.json",
    "parallel_lane_audit_report.md",
    "merge_recommendation.md",
}
TERMINAL_METADATA_STATUSES = {"completed", "completed_no_parseable_outcome"}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def as_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def resolve_manifest_reference(value: str) -> Path:
    return resolve_path(value)


def validate_manifest_inputs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    lanes = manifest.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise ValueError("Manifest must contain at least one lane")
    declared_count = int(manifest.get("num_lanes", 0))
    if declared_count != len(lanes):
        raise ValueError("Manifest lane count does not match lanes list")

    all_municipality_ids: list[str] = []
    all_census_ids: list[str] = []
    normalized: list[dict[str, Any]] = []
    for lane in lanes:
        lane_id = str(lane.get("lane_id", ""))
        if not lane_id:
            raise ValueError("Every manifest lane requires a lane_id")
        input_path = resolve_manifest_reference(str(lane.get("input_csv", "")))
        if not input_path.is_file():
            raise ValueError(f"{lane_id} input is missing: {input_path}")
        actual_hash = sha256(input_path)
        expected_hash = str(lane.get("input_sha256", ""))
        if actual_hash != expected_hash:
            raise ValueError(
                f"{lane_id} input hash mismatch: expected {expected_hash}, got {actual_hash}"
            )
        rows = read_csv(input_path)
        expected_count = int(lane.get("row_count", 0))
        if len(rows) != expected_count:
            raise ValueError(
                f"{lane_id} input row count mismatch: expected {expected_count}, "
                f"got {len(rows)}"
            )
        municipality_ids = [row.get("municipality_id", "") for row in rows]
        census_ids = [row.get("census_gov_id", "") for row in rows]
        if not all(municipality_ids):
            raise ValueError(f"{lane_id} input contains blank municipality IDs")
        if len(municipality_ids) != len(set(municipality_ids)):
            raise ValueError(f"{lane_id} input contains duplicate municipality IDs")
        nonblank_census = [value for value in census_ids if value]
        if len(nonblank_census) != len(set(nonblank_census)):
            raise ValueError(f"{lane_id} input contains duplicate nonblank Census IDs")
        all_municipality_ids.extend(municipality_ids)
        all_census_ids.extend(nonblank_census)
        normalized.append(
            {
                **lane,
                "_input_path": input_path,
                "_input_rows": rows,
                "_municipality_ids": municipality_ids,
                "_census_ids": nonblank_census,
            }
        )

    duplicate_municipality_ids = sorted(
        value for value, count in Counter(all_municipality_ids).items() if count > 1
    )
    duplicate_census_ids = sorted(
        value for value, count in Counter(all_census_ids).items() if count > 1
    )
    if duplicate_municipality_ids:
        raise ValueError(
            "Duplicate municipality IDs across lanes: "
            + ", ".join(duplicate_municipality_ids[:10])
        )
    if duplicate_census_ids:
        raise ValueError(
            "Duplicate nonblank Census IDs across lanes: "
            + ", ".join(duplicate_census_ids[:10])
        )
    return normalized


def candidate_count(path: Path) -> int:
    return len(read_csv(path)) if path.is_file() else 0


def inspect_lane(lane: dict[str, Any]) -> dict[str, Any]:
    lane_id = str(lane["lane_id"])
    output_dir = resolve_manifest_reference(str(lane["live_output_dir"]))
    input_path: Path = lane["_input_path"]
    expected_hash = str(lane["input_sha256"])
    expected_rows = int(lane["row_count"])
    base = {
        "lane_id": lane_id,
        "input_csv": relative(input_path),
        "expected_input_sha256": expected_hash,
        "actual_input_sha256": sha256(input_path),
        "expected_rows": expected_rows,
        "output_dir": relative(output_dir),
        "classification": "",
        "execution_status": None,
        "parseable_rows": 0,
        "failure_rows": 0,
        "stopped_before_request_rows": 0,
        "pending_rows": 0,
        "candidate_rows": 0,
        "attempted_rows": 0,
        "outer_timeout_rows": 0,
        "adaptive_backoff_events": 0,
        "adaptive_step_down_events": 0,
        "total_elapsed_seconds": 0.0,
        "effective_rows_per_hour": 0.0,
        "first_prompt_started_at": None,
        "last_prompt_finished_at": None,
        "candidate_export_dir": lane.get("candidate_export_dir"),
        "candidate_export_files": [],
        "candidate_export_matches_parsed_candidates": None,
        "completed_municipality_ids": [],
        "artifact_errors": [],
        "merge_eligible": False,
    }
    if not output_dir.exists():
        base["classification"] = "not_started"
        return base
    if not output_dir.is_dir():
        base["classification"] = "missing_artifacts"
        base["artifact_errors"] = ["configured output path is not a directory"]
        return base

    metadata_path = output_dir / "run_metadata.json"
    timing_path = output_dir / "row_timing.csv"
    candidates_path = output_dir / "parsed_candidates.csv"
    failed_path = output_dir / "failed_parses.csv"
    required = [metadata_path, timing_path, candidates_path, failed_path]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        base["classification"] = "missing_artifacts"
        base["artifact_errors"] = ["missing " + name for name in missing]
        return base

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        timing_rows = read_csv(timing_path)
        base["candidate_rows"] = candidate_count(candidates_path)
        failed_rows = read_csv(failed_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        base["classification"] = "missing_artifacts"
        base["artifact_errors"] = [f"artifact parse error: {type(exc).__name__}: {exc}"]
        return base

    base["execution_status"] = metadata.get("execution_status")
    base["parseable_rows"] = sum(
        row.get("parse_status") == "parseable" for row in timing_rows
    )
    base["failure_rows"] = sum(
        row.get("parse_status") == "failed" for row in timing_rows
    )
    base["stopped_before_request_rows"] = sum(
        row.get("success_status") == "stopped_before_request"
        or row.get("failure_type") == "stopped_before_request"
        for row in timing_rows
    )
    base["pending_rows"] = sum(
        row.get("parse_status") in {"", "pending"}
        or row.get("success_status") in {"", "pending_live_attempt"}
        for row in timing_rows
    )
    base["attempted_rows"] = sum(
        row.get("live_attempted") == "yes" for row in timing_rows
    )
    base["failed_parse_artifact_rows"] = len(failed_rows)
    base["timing_rows"] = len(timing_rows)
    started_values = [
        row.get("prompt_started_at")
        for row in timing_rows
        if as_datetime(row.get("prompt_started_at")) is not None
    ]
    finished_values = [
        row.get("prompt_finished_at")
        for row in timing_rows
        if as_datetime(row.get("prompt_finished_at")) is not None
    ]
    if started_values:
        base["first_prompt_started_at"] = min(
            started_values, key=lambda value: as_datetime(value)  # type: ignore[arg-type]
        )
    if finished_values:
        base["last_prompt_finished_at"] = max(
            finished_values, key=lambda value: as_datetime(value)  # type: ignore[arg-type]
        )
    base["outer_timeout_rows"] = sum(
        row.get("failure_type") == "outer_timeout" for row in timing_rows
    )
    base["adaptive_backoff_events"] = sum(
        row.get("adaptive_sleep_event") in {"backoff", "backoff_held"}
        for row in timing_rows
    )
    base["adaptive_step_down_events"] = sum(
        row.get("adaptive_sleep_event") == "stable_step_down"
        for row in timing_rows
    )
    elapsed = as_float(metadata.get("total_elapsed_seconds"))
    if elapsed <= 0:
        elapsed = sum(
            as_float(row.get("elapsed_seconds"))
            + as_float(row.get("sleep_before_seconds"))
            + as_float(row.get("sleep_after_seconds"))
            for row in timing_rows
        )
    base["total_elapsed_seconds"] = round(elapsed, 6)
    if elapsed > 0:
        base["effective_rows_per_hour"] = round(
            base["attempted_rows"] * 3600 / elapsed, 6
        )
    base["completed_municipality_ids"] = [
        row.get("municipality_id", "")
        for row in timing_rows
        if row.get("municipality_id")
        and row.get("success_status")
        in {"completed_parseable", "failed"}
    ]

    artifact_errors: list[str] = []
    if metadata.get("input_csv_sha256") != expected_hash:
        artifact_errors.append("run metadata input hash does not match manifest")
    if base["actual_input_sha256"] != expected_hash:
        artifact_errors.append("current input hash does not match manifest")
    if len(timing_rows) != expected_rows:
        artifact_errors.append(
            f"timing row count {len(timing_rows)} does not equal {expected_rows}"
        )
    timing_ids = [row.get("municipality_id", "") for row in timing_rows]
    if timing_ids and timing_ids != lane["_municipality_ids"]:
        artifact_errors.append("timing municipality identities/order differ from input")
    candidate_export_dir_value = lane.get("candidate_export_dir")
    if candidate_export_dir_value:
        candidate_export_dir = resolve_manifest_reference(
            str(candidate_export_dir_value)
        )
        export_files = (
            sorted(
                candidate_export_dir.glob(
                    "gabriel_state_source_scout_candidates_*.csv"
                )
            )
            if candidate_export_dir.is_dir()
            else []
        )
        base["candidate_export_files"] = [relative(path) for path in export_files]
        if base["parseable_rows"] > 0:
            if len(export_files) != 1:
                artifact_errors.append(
                    "lane-local candidate export missing or ambiguous"
                )
                base["candidate_export_matches_parsed_candidates"] = False
            else:
                export_matches = (
                    export_files[0].read_bytes() == candidates_path.read_bytes()
                )
                base["candidate_export_matches_parsed_candidates"] = export_matches
                if not export_matches:
                    artifact_errors.append(
                        "lane-local candidate export differs from parsed_candidates.csv"
                    )
        elif export_files:
            artifact_errors.append(
                "lane-local candidate export exists despite zero parseable rows"
            )
            base["candidate_export_matches_parsed_candidates"] = False
        metadata_export_dir = metadata.get("candidate_export_dir")
        if metadata_export_dir and (
            resolve_manifest_reference(str(metadata_export_dir))
            != candidate_export_dir
        ):
            artifact_errors.append(
                "run metadata candidate export directory differs from manifest"
            )
    base["artifact_errors"] = artifact_errors

    process_terminal = metadata.get("execution_status") in TERMINAL_METADATA_STATUSES
    process_completed = as_bool(metadata.get("live_process_completed"))
    coherent_terminal_rows = (
        base["parseable_rows"] + base["failure_rows"] == expected_rows
        and base["stopped_before_request_rows"] == 0
        and base["pending_rows"] == 0
    )
    if (
        not artifact_errors
        and metadata.get("execution_status") == "completed"
        and process_completed
        and coherent_terminal_rows
        and base["parseable_rows"] > 0
    ):
        base["classification"] = "completed_merge_eligible"
        base["merge_eligible"] = True
    elif base["parseable_rows"] > 0 and (
        not process_terminal
        or not process_completed
        or not coherent_terminal_rows
        or bool(artifact_errors)
    ):
        base["classification"] = "partial_parseable"
    elif base["parseable_rows"] == 0 and (
        base["attempted_rows"] > 0
        or base["failure_rows"] > 0
        or base["stopped_before_request_rows"] > 0
        or metadata.get("execution_status") == "completed_no_parseable_outcome"
    ):
        base["classification"] = "failed_zero_parseable"
    else:
        base["classification"] = "completed_not_merge_eligible"
    return base


def determine_recommendation(lanes: list[dict[str, Any]]) -> str:
    classifications = [lane["classification"] for lane in lanes]
    if all(value == "completed_merge_eligible" for value in classifications):
        return "merge_all_lanes"
    completed = classifications.count("completed_merge_eligible")
    if completed > 0 and all(
        value in {"completed_merge_eligible", "failed_zero_parseable"}
        for value in classifications
    ):
        return "merge_completed_lanes_only_with_user_approval"
    return "do_not_merge_until_resume_or_review"


def validate_completed_overlap(lanes: list[dict[str, Any]]) -> list[str]:
    completed: list[str] = []
    for lane in lanes:
        completed.extend(lane["completed_municipality_ids"])
    return sorted(value for value, count in Counter(completed).items() if count > 1)


def report_text(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['round_id']} — Parallel Lane Audit Report",
        "",
        f"Recommendation: **`{summary['merge_recommendation']}`**",
        "",
        "This is an offline recommendation only. No national builder was run.",
        "",
        "## Lane results",
        "",
        "| Lane | Classification | Parseable | Failures | Stopped | Pending | Outer timeout | Candidates | Rows/hour | Export match | Merge eligible |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for lane in summary["lanes"]:
        lines.append(
            f"| {lane['lane_id']} | `{lane['classification']}` | "
            f"{lane['parseable_rows']} | {lane['failure_rows']} | "
            f"{lane['stopped_before_request_rows']} | {lane['pending_rows']} | "
            f"{lane['outer_timeout_rows']} | {lane['candidate_rows']} | "
            f"{lane['effective_rows_per_hour']:.3f} | "
            f"{lane['candidate_export_matches_parsed_candidates']} | "
            f"{'yes' if lane['merge_eligible'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Combined checks",
            "",
            f"- Candidate rows across lanes: {summary['totals']['candidate_rows']}",
            f"- Parseable rows across lanes: {summary['totals']['parseable_rows']}",
            f"- Failure rows across lanes: {summary['totals']['failure_rows']}",
            (
                "- Stopped-before-request rows across lanes: "
                f"{summary['totals']['stopped_before_request_rows']}"
            ),
            (
                "- Outer-timeout rows across lanes: "
                f"{summary['totals']['outer_timeout_rows']}"
            ),
            (
                "- Adaptive backoff events across lanes: "
                f"{summary['totals']['adaptive_backoff_events']}"
            ),
            (
                "- Adaptive step-down events across lanes: "
                f"{summary['totals']['adaptive_step_down_events']}"
            ),
            (
                "- Parallel effective attempted rows/hour: "
                f"{summary['totals']['effective_attempted_rows_per_hour']:.3f}"
            ),
            f"- Completed municipality-ID overlap: {len(summary['completed_id_overlap'])}",
            f"- Input hashes valid: {'yes' if summary['input_hashes_valid'] else 'no'}",
            "",
            "## Boundary",
            "",
            "No queue, coverage, yield, dashboard, priority, verification, ingestion, "
            "codification, canonical, or corpus file was written. A separately "
            "authorized coordinator owns any later serial accounting merge.",
        ]
    )
    return "\n".join(lines) + "\n"


def recommendation_text(summary: dict[str, Any]) -> str:
    recommendation = summary["merge_recommendation"]
    explanations = {
        "merge_all_lanes": (
            "All lanes are terminal and independently merge-eligible, and completed "
            "municipality IDs do not overlap. A later coordinator may propose one "
            "serial accounting rebuild, but this audit does not authorize or run it."
        ),
        "merge_completed_lanes_only_with_user_approval": (
            "At least one lane is complete and merge-eligible while every other lane "
            "failed with zero parseable rows. Merging only completed lanes changes the "
            "planned round scope and requires explicit user approval."
        ),
        "do_not_merge_until_resume_or_review": (
            "The round contains a partial, missing, not-started, inconsistent, or "
            "otherwise non-mergeable lane. Preserve all artifacts and resolve resume "
            "or disposition before any shared accounting change."
        ),
    }
    return f"""# Merge Recommendation

## `{recommendation}`

{explanations[recommendation]}

The queue/coverage/dashboard merge remains a separate coordinator-controlled task.
Do not run builders from a lane process.
"""


def run_audit(manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lanes = validate_manifest_inputs(manifest)
    inspected = [inspect_lane(lane) for lane in lanes]
    completed_overlap = validate_completed_overlap(inspected)
    recommendation = determine_recommendation(inspected)
    if completed_overlap:
        recommendation = "do_not_merge_until_resume_or_review"
        for lane in inspected:
            lane["merge_eligible"] = False
            if lane["classification"] == "completed_merge_eligible":
                lane["classification"] = "completed_not_merge_eligible"
            lane["artifact_errors"].append(
                "completed municipality ID overlaps another lane"
            )

    attempted_total = sum(lane["attempted_rows"] for lane in inspected)
    actual_starts = [
        as_datetime(lane["first_prompt_started_at"])
        for lane in inspected
        if as_datetime(lane["first_prompt_started_at"]) is not None
    ]
    actual_finishes = [
        as_datetime(lane["last_prompt_finished_at"])
        for lane in inspected
        if as_datetime(lane["last_prompt_finished_at"]) is not None
    ]
    if len(actual_starts) == len(inspected) and len(actual_finishes) == len(inspected):
        parallel_wall_clock_seconds = (
            max(actual_finishes) - min(actual_starts)  # type: ignore[type-var]
        ).total_seconds()
        parallel_wall_clock_source = "row_timing_actual_timestamps"
    else:
        lane_elapsed = [
            lane["total_elapsed_seconds"]
            + as_float(lanes[index].get("planned_start_offset_seconds"))
            for index, lane in enumerate(inspected)
            if lane["total_elapsed_seconds"] > 0
        ]
        parallel_wall_clock_seconds = max(lane_elapsed, default=0.0)
        parallel_wall_clock_source = "elapsed_plus_manifest_planned_offsets"
    effective_attempted_rows_per_hour = (
        attempted_total * 3600 / parallel_wall_clock_seconds
        if parallel_wall_clock_seconds > 0
        else 0.0
    )
    summary = {
        "schema_version": "2.0.0",
        "round_id": manifest["round_id"],
        "manifest": relative(manifest_path),
        "audit_mode": "offline_read_only_recommendation",
        "shared_accounting_writes_performed": 0,
        "lanes": inspected,
        "totals": {
            "parseable_rows": sum(lane["parseable_rows"] for lane in inspected),
            "failure_rows": sum(lane["failure_rows"] for lane in inspected),
            "stopped_before_request_rows": sum(
                lane["stopped_before_request_rows"] for lane in inspected
            ),
            "candidate_rows": sum(lane["candidate_rows"] for lane in inspected),
            "attempted_rows": attempted_total,
            "outer_timeout_rows": sum(
                lane["outer_timeout_rows"] for lane in inspected
            ),
            "adaptive_backoff_events": sum(
                lane["adaptive_backoff_events"] for lane in inspected
            ),
            "adaptive_step_down_events": sum(
                lane["adaptive_step_down_events"] for lane in inspected
            ),
            "parallel_wall_clock_seconds": round(
                parallel_wall_clock_seconds, 6
            ),
            "parallel_wall_clock_source": parallel_wall_clock_source,
            "effective_attempted_rows_per_hour": round(
                effective_attempted_rows_per_hour, 6
            ),
        },
        "completed_id_overlap": completed_overlap,
        "input_hashes_valid": all(
            lane["actual_input_sha256"] == lane["expected_input_sha256"]
            for lane in inspected
        ),
        "merge_recommendation": recommendation,
        "accounting_policy": "serial_merge_after_lane_audit",
        "caveat": "The auditor does not rebuild shared accounting.",
    }

    if output_dir.exists():
        unexpected = sorted(
            path.name
            for path in output_dir.iterdir()
            if path.name not in AUDIT_OUTPUT_NAMES
        )
        if unexpected:
            raise ValueError(
                "Audit output contains unexpected files: " + ", ".join(unexpected)
            )
    else:
        output_dir.mkdir(parents=True)
    (output_dir / "parallel_lane_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "parallel_lane_audit_report.md").write_text(
        report_text(summary), encoding="utf-8"
    )
    (output_dir / "merge_recommendation.md").write_text(
        recommendation_text(summary), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        summary = run_audit(resolve_path(args.manifest), resolve_path(args.output_dir))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"PARALLEL LANE AUDIT FAILED: {exc}")
        return 2
    print(
        f"Parallel lane audit: round={summary['round_id']} "
        f"recommendation={summary['merge_recommendation']} "
        f"candidate_rows={summary['totals']['candidate_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
