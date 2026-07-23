#!/usr/bin/env python3
"""Offline synthetic tests for scalable parallel scout lane auditing."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path

import audit_parallel_scout_lanes as auditor


INPUT_FIELDS = ["municipality_id", "census_gov_id", "municipality", "state"]
TIMING_FIELDS = [
    "municipality_id",
    "live_attempted",
    "success_status",
    "parse_status",
    "failure_type",
    "elapsed_seconds",
    "sleep_before_seconds",
    "sleep_after_seconds",
    "adaptive_sleep_event",
]
CANDIDATE_FIELDS = ["municipality_id", "source_url"]
FAILED_FIELDS = ["municipality_id", "failure_type"]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_rows(prefix: str) -> list[dict[str, str]]:
    return [
        {
            "municipality_id": f"{prefix}-001",
            "census_gov_id": f"{prefix}001",
            "municipality": f"{prefix} One",
            "state": "PA",
        },
        {
            "municipality_id": f"{prefix}-002",
            "census_gov_id": f"{prefix}002",
            "municipality": f"{prefix} Two",
            "state": "PA",
        },
    ]


def make_round(
    root: Path, num_lanes: int = 3
) -> tuple[Path, list[dict[str, object]]]:
    lanes: list[dict[str, object]] = []
    for number in range(1, num_lanes + 1):
        prefix = chr(ord("a") + number - 1)
        input_path = root / f"lane_{number}_input.csv"
        output_dir = root / f"lane_{number}_output"
        write_csv(input_path, INPUT_FIELDS, input_rows(prefix))
        lanes.append(
            {
                "lane_id": f"lane_{number}",
                "input_csv": str(input_path),
                "input_sha256": file_hash(input_path),
                "row_count": 2,
                "live_output_dir": str(output_dir),
                "candidate_export_dir": str(output_dir / "candidate_exports"),
                "candidate_export_policy": "lane_local_required_when_parseable",
                "planned_start_offset_seconds": (number - 1) * 240,
            }
        )
    manifest = {
        "schema_version": "2.0.0",
        "round_id": "SYNTHETIC-ROUND",
        "num_lanes": num_lanes,
        "lanes": lanes,
    }
    manifest_path = root / "parallel_round_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, lanes


def completed_timing(prefix: str) -> list[dict[str, str]]:
    return [
        {
            "municipality_id": f"{prefix}-001",
            "live_attempted": "yes",
            "success_status": "completed_parseable",
            "parse_status": "parseable",
            "failure_type": "",
            "elapsed_seconds": "50",
            "sleep_before_seconds": "0",
            "sleep_after_seconds": "5",
            "adaptive_sleep_event": "stable_step_down",
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "yes",
            "success_status": "completed_parseable",
            "parse_status": "parseable",
            "failure_type": "",
            "elapsed_seconds": "50",
            "sleep_before_seconds": "5",
            "sleep_after_seconds": "0",
            "adaptive_sleep_event": "stable_at_min",
        },
    ]


def failed_timing(prefix: str) -> list[dict[str, str]]:
    return [
        {
            "municipality_id": f"{prefix}-001",
            "live_attempted": "yes",
            "success_status": "failed",
            "parse_status": "failed",
            "failure_type": "outer_timeout",
            "elapsed_seconds": "50",
            "sleep_before_seconds": "0",
            "sleep_after_seconds": "10",
            "adaptive_sleep_event": "backoff",
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "yes",
            "success_status": "failed",
            "parse_status": "failed",
            "failure_type": "outer_timeout",
            "elapsed_seconds": "50",
            "sleep_before_seconds": "10",
            "sleep_after_seconds": "0",
            "adaptive_sleep_event": "backoff_held",
        },
    ]


def partial_timing(prefix: str) -> list[dict[str, str]]:
    return [
        {
            "municipality_id": f"{prefix}-001",
            "live_attempted": "yes",
            "success_status": "completed_parseable",
            "parse_status": "parseable",
            "failure_type": "",
            "elapsed_seconds": "50",
            "sleep_before_seconds": "0",
            "sleep_after_seconds": "0",
            "adaptive_sleep_event": "",
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "no",
            "success_status": "stopped_before_request",
            "parse_status": "not_attempted",
            "failure_type": "stopped_before_request",
            "elapsed_seconds": "0",
            "sleep_before_seconds": "0",
            "sleep_after_seconds": "0",
            "adaptive_sleep_event": "stopped_before_request",
        },
    ]


def write_lane_artifacts(
    lane: dict[str, object],
    *,
    status: str,
    timing: list[dict[str, str]],
    candidate_rows: int,
    live_process_completed: bool,
    export_mode: str = "matching",
    elapsed_seconds: float = 120,
) -> None:
    output = Path(str(lane["live_output_dir"]))
    output.mkdir(parents=True)
    metadata = {
        "execution_status": status,
        "live_process_completed": live_process_completed,
        "input_csv_sha256": lane["input_sha256"],
        "candidate_export_dir": lane["candidate_export_dir"],
        "candidate_export_policy": "configured_directory",
        "total_elapsed_seconds": elapsed_seconds,
    }
    (output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(output / "row_timing.csv", TIMING_FIELDS, timing)
    candidates = [
        {
            "municipality_id": timing[index % len(timing)]["municipality_id"],
            "source_url": f"https://invalid.test/{index}",
        }
        for index in range(candidate_rows)
    ]
    parsed_path = output / "parsed_candidates.csv"
    write_csv(parsed_path, CANDIDATE_FIELDS, candidates)
    failures = [
        {
            "municipality_id": row["municipality_id"],
            "failure_type": row["failure_type"],
        }
        for row in timing
        if row["parse_status"] == "failed"
    ]
    write_csv(output / "failed_parses.csv", FAILED_FIELDS, failures)
    if any(row["parse_status"] == "parseable" for row in timing):
        export_path = (
            Path(str(lane["candidate_export_dir"]))
            / "gabriel_state_source_scout_candidates_fixture.csv"
        )
        if export_mode == "matching":
            export_path.parent.mkdir(parents=True)
            export_path.write_bytes(parsed_path.read_bytes())
        elif export_mode == "mismatch":
            write_csv(
                export_path,
                CANDIDATE_FIELDS,
                [{"municipality_id": "wrong", "source_url": "https://invalid.test/wrong"}],
            )
        elif export_mode != "missing":
            raise ValueError(export_mode)


def test_three_completed_merge_all_and_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        for number, lane in enumerate(lanes, start=1):
            write_lane_artifacts(
                lane,
                status="completed",
                timing=completed_timing(chr(ord("a") + number - 1)),
                candidate_rows=number,
                live_process_completed=True,
            )
        output = root / "audit"
        summary = auditor.run_audit(manifest, output)
        assert summary["merge_recommendation"] == "merge_all_lanes"
        assert all(
            lane["classification"] == "completed_merge_eligible"
            for lane in summary["lanes"]
        )
        assert summary["totals"]["candidate_rows"] == 6
        assert summary["totals"]["parseable_rows"] == 6
        assert summary["totals"]["adaptive_step_down_events"] == 3
        assert summary["totals"]["parallel_wall_clock_seconds"] == 600
        assert summary["totals"]["effective_attempted_rows_per_hour"] == 36
        assert summary["completed_id_overlap"] == []
        assert {path.name for path in output.iterdir()} == auditor.AUDIT_OUTPUT_NAMES


def test_duplicate_input_ids_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        lane_3_input = Path(str(lanes[2]["input_csv"]))
        write_csv(lane_3_input, INPUT_FIELDS, input_rows("a"))
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["lanes"][2]["input_sha256"] = file_hash(lane_3_input)
        try:
            auditor.validate_manifest_inputs(payload)
        except ValueError as exc:
            assert "Duplicate municipality IDs across lanes" in str(exc)
        else:
            raise AssertionError("cross-lane duplicate input IDs did not fail")


def test_duplicate_completed_ids_block_merge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        for number, lane in enumerate(lanes, start=1):
            prefix = "a" if number == 3 else chr(ord("a") + number - 1)
            write_lane_artifacts(
                lane,
                status="completed",
                timing=completed_timing(prefix),
                candidate_rows=1,
                live_process_completed=True,
            )
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "do_not_merge_until_resume_or_review"
        )
        assert summary["completed_id_overlap"] == ["a-001", "a-002"]


def test_two_complete_one_zero_requires_approval_and_counts_timeouts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        for index in (0, 1):
            write_lane_artifacts(
                lanes[index],
                status="completed",
                timing=completed_timing(chr(ord("a") + index)),
                candidate_rows=2,
                live_process_completed=True,
            )
        write_lane_artifacts(
            lanes[2],
            status="completed_no_parseable_outcome",
            timing=failed_timing("c"),
            candidate_rows=0,
            live_process_completed=True,
        )
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "merge_completed_lanes_only_with_user_approval"
        )
        assert summary["lanes"][2]["classification"] == "failed_zero_parseable"
        assert summary["totals"]["outer_timeout_rows"] == 2
        assert summary["totals"]["adaptive_backoff_events"] == 2


def test_one_complete_two_partial_blocks_merge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        write_lane_artifacts(
            lanes[0],
            status="completed",
            timing=completed_timing("a"),
            candidate_rows=2,
            live_process_completed=True,
        )
        for index in (1, 2):
            write_lane_artifacts(
                lanes[index],
                status="live_started",
                timing=partial_timing(chr(ord("a") + index)),
                candidate_rows=1,
                live_process_completed=False,
            )
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "do_not_merge_until_resume_or_review"
        )
        assert summary["totals"]["stopped_before_request_rows"] == 2


def test_lane_local_export_missing_or_mismatched_blocks_merge() -> None:
    for mode in ("missing", "mismatch"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, lanes = make_round(root)
            for index, lane in enumerate(lanes):
                write_lane_artifacts(
                    lane,
                    status="completed",
                    timing=completed_timing(chr(ord("a") + index)),
                    candidate_rows=1,
                    live_process_completed=True,
                    export_mode=mode if index == 2 else "matching",
                )
            summary = auditor.run_audit(manifest, root / "audit")
            assert (
                summary["merge_recommendation"]
                == "do_not_merge_until_resume_or_review"
            )
            assert summary["lanes"][2]["classification"] == "partial_parseable"
            assert summary["lanes"][2]["candidate_export_matches_parsed_candidates"] is False


def test_missing_artifacts_and_no_accounting_writes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        write_lane_artifacts(
            lanes[0],
            status="completed",
            timing=completed_timing("a"),
            candidate_rows=2,
            live_process_completed=True,
        )
        Path(str(lanes[1]["live_output_dir"])).mkdir()
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "do_not_merge_until_resume_or_review"
        )
        assert summary["lanes"][1]["classification"] == "missing_artifacts"
        assert not any(
            token in path.name
            for path in (root / "audit").iterdir()
            for token in ("queue", "coverage", "dashboard")
        )
        assert summary["shared_accounting_writes_performed"] == 0


def main() -> int:
    test_three_completed_merge_all_and_metrics()
    test_duplicate_input_ids_fail_closed()
    test_duplicate_completed_ids_block_merge()
    test_two_complete_one_zero_requires_approval_and_counts_timeouts()
    test_one_complete_two_partial_blocks_merge()
    test_lane_local_export_missing_or_mismatched_blocks_merge()
    test_missing_artifacts_and_no_accounting_writes()
    print("PASS: three completed disjoint lanes recommend merge_all_lanes")
    print("PASS: duplicate input or completed municipality IDs fail closed")
    print("PASS: two complete plus zero-parseable lane requires user approval")
    print("PASS: parseable partial lanes block merge")
    print("PASS: lane-local candidate exports are required and byte-checked")
    print("PASS: three-lane throughput, timeout, backoff, and step-down totals are exact")
    print("PASS: missing artifacts block merge and auditor writes no accounting files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
