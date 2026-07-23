#!/usr/bin/env python3
"""Offline synthetic tests for the parallel scout lane auditor."""

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


def make_round(root: Path) -> tuple[Path, list[dict[str, object]]]:
    lanes: list[dict[str, object]] = []
    for number, prefix in ((1, "a"), (2, "b")):
        input_path = root / f"lane_{number}_input.csv"
        write_csv(input_path, INPUT_FIELDS, input_rows(prefix))
        lanes.append(
            {
                "lane_id": f"lane_{number}",
                "input_csv": str(input_path),
                "input_sha256": file_hash(input_path),
                "row_count": 2,
                "live_output_dir": str(root / f"lane_{number}_output"),
            }
        )
    manifest = {
        "schema_version": "1.0.0",
        "round_id": "SYNTHETIC-ROUND",
        "num_lanes": 2,
        "lanes": lanes,
    }
    manifest_path = root / "parallel_round_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, lanes


def write_lane_artifacts(
    lane: dict[str, object],
    *,
    status: str,
    timing: list[dict[str, str]],
    candidate_rows: int,
    live_process_completed: bool,
) -> None:
    output = Path(str(lane["live_output_dir"]))
    output.mkdir(parents=True)
    metadata = {
        "execution_status": status,
        "live_process_completed": live_process_completed,
        "input_csv_sha256": lane["input_sha256"],
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
    write_csv(output / "parsed_candidates.csv", CANDIDATE_FIELDS, candidates)
    failures = [
        {
            "municipality_id": row["municipality_id"],
            "failure_type": row["failure_type"],
        }
        for row in timing
        if row["parse_status"] == "failed"
    ]
    write_csv(output / "failed_parses.csv", FAILED_FIELDS, failures)


def completed_timing(prefix: str) -> list[dict[str, str]]:
    return [
        {
            "municipality_id": f"{prefix}-001",
            "live_attempted": "yes",
            "success_status": "completed_parseable",
            "parse_status": "parseable",
            "failure_type": "",
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "yes",
            "success_status": "completed_parseable",
            "parse_status": "parseable",
            "failure_type": "",
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
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "yes",
            "success_status": "failed",
            "parse_status": "failed",
            "failure_type": "outer_timeout",
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
        },
        {
            "municipality_id": f"{prefix}-002",
            "live_attempted": "no",
            "success_status": "stopped_before_request",
            "parse_status": "not_attempted",
            "failure_type": "stopped_before_request",
        },
    ]


def check_two_completed_merge_all_and_counts() -> None:
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
        write_lane_artifacts(
            lanes[1],
            status="completed",
            timing=completed_timing("b"),
            candidate_rows=3,
            live_process_completed=True,
        )
        output = root / "audit"
        summary = auditor.run_audit(manifest, output)
        assert summary["merge_recommendation"] == "merge_all_lanes"
        assert [lane["classification"] for lane in summary["lanes"]] == [
            "completed_merge_eligible",
            "completed_merge_eligible",
        ]
        assert summary["totals"]["candidate_rows"] == 5
        assert summary["totals"]["parseable_rows"] == 4
        assert summary["completed_id_overlap"] == []
        assert {path.name for path in output.iterdir()} == auditor.AUDIT_OUTPUT_NAMES
        assert not any(
            token in path.name
            for path in output.iterdir()
            for token in ("queue", "coverage", "dashboard")
        )


def check_duplicate_ids_fail() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest, lanes = make_round(root)
        duplicate_rows = input_rows("a")
        lane_2_input = Path(str(lanes[1]["input_csv"]))
        write_csv(lane_2_input, INPUT_FIELDS, duplicate_rows)
        lanes[1]["input_sha256"] = file_hash(lane_2_input)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["lanes"][1]["input_sha256"] = lanes[1]["input_sha256"]
        manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        try:
            auditor.validate_manifest_inputs(payload)
        except ValueError as exc:
            assert "Duplicate municipality IDs across lanes" in str(exc)
        else:
            raise AssertionError("cross-lane duplicate municipality IDs did not fail")


def check_completed_plus_zero_parseable_requires_approval() -> None:
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
        write_lane_artifacts(
            lanes[1],
            status="completed_no_parseable_outcome",
            timing=failed_timing("b"),
            candidate_rows=0,
            live_process_completed=True,
        )
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "merge_completed_lanes_only_with_user_approval"
        )
        assert [lane["classification"] for lane in summary["lanes"]] == [
            "completed_merge_eligible",
            "failed_zero_parseable",
        ]


def check_partial_parseable_blocks_merge_and_counts_stopped() -> None:
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
        write_lane_artifacts(
            lanes[1],
            status="live_started",
            timing=partial_timing("b"),
            candidate_rows=1,
            live_process_completed=False,
        )
        summary = auditor.run_audit(manifest, root / "audit")
        assert (
            summary["merge_recommendation"]
            == "do_not_merge_until_resume_or_review"
        )
        assert summary["lanes"][1]["classification"] == "partial_parseable"
        assert summary["totals"]["candidate_rows"] == 3
        assert summary["totals"]["stopped_before_request_rows"] == 1


def check_missing_artifacts_blocks_merge() -> None:
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


def main() -> int:
    check_two_completed_merge_all_and_counts()
    check_duplicate_ids_fail()
    check_completed_plus_zero_parseable_requires_approval()
    check_partial_parseable_blocks_merge_and_counts_stopped()
    check_missing_artifacts_blocks_merge()
    print("PASS: two completed disjoint lanes recommend merge_all_lanes")
    print("PASS: cross-lane duplicate municipality IDs fail closed")
    print("PASS: completed plus zero-parseable lane requires user approval")
    print("PASS: parseable partial lane blocks merge")
    print("PASS: missing lane artifacts block merge")
    print("PASS: candidate and stopped-before-request totals are exact")
    print("PASS: auditor writes no queue, coverage, or dashboard file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
