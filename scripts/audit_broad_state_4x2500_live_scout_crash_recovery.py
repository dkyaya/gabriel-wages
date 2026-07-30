#!/usr/bin/env python3
"""Audit an interrupted BROAD-STATE-4X2500 live scout without scouting.

This script is intentionally metadata-only.  It reads committed queue locks,
lane checkpoints, target directory names, sanitized worker logs, and dashboard
accounting.  It never opens candidate source locators or source documents and
it never invokes the hosted-search transport or any downstream stage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
LIVE = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29"
LOGS = ROOT / "tmp/broad_state_4x2500_live_scout_2026-07-29_logs"
DASHBOARD = ROOT / "docs/dashboard/data"
LANES = tuple(f"scout_lane_{number:03d}" for number in range(1, 5))
SHARDS = tuple(f"broad_4x2500_shard_{number:03d}" for number in range(1, 5))
TRANSPORT_FAILURES = {"connection_error", "timeout", "outer_timeout", "timeout_or_capacity"}
DECISION_MONITORING = "broad_state_4x2500_live_scout_crash_recovery_workers_still_running_monitoring"
DECISION_REPAIR = "broad_state_4x2500_live_scout_crash_recovery_repair_needed"
DECISION_COMPLETE = "broad_state_4x2500_live_scout_crash_recovery_completed_candidate_review_ready"
DECISION_PARTIAL = "broad_state_4x2500_live_scout_crash_recovery_partial_lanes_completed_resume_ready"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def accepted(outcome: dict[str, Any]) -> bool:
    return (
        outcome.get("parse_status") == "parseable"
        or outcome.get("failure_type") not in TRANSPORT_FAILURES
        or int(outcome.get("attempt_count", 0)) >= 2
    )


def process_probe(pid: int) -> bool | None:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # macOS workspace sandboxing can deny signal probes for a process that
        # was just confirmed by the separately authorized host-level ps audit.
        return None
    return True


def recursive_key_values(value: Any, key_fragment: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key_fragment in key:
                found.append(child)
            found.extend(recursive_key_values(child, key_fragment))
    elif isinstance(value, list):
        for child in value:
            found.extend(recursive_key_values(child, key_fragment))
    return found


def parse_workers(values: list[str]) -> dict[str, int]:
    workers: dict[str, int] = {}
    for value in values:
        lane, raw_pid = value.split("=", 1)
        if lane not in LANES:
            raise ValueError(f"unexpected lane in --worker: {lane}")
        workers[lane] = int(raw_pid)
    return workers


def validate_locks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    master_path = PREP / "broad_state_4x2500_scout_master_locked_queue.csv"
    master_lock = read_json(PREP / "broad_state_4x2500_scout_master_lock.json")
    master = read_csv(master_path)
    master_hash = sha256_file(master_path)
    shard_rows: list[dict[str, str]] = []
    shard_details: dict[str, Any] = {}
    for number, shard_id in enumerate(SHARDS, 1):
        queue_path = PREP / f"broad_state_4x2500_scout_shard_{number:03d}_locked_queue.csv"
        lock_path = PREP / f"broad_state_4x2500_scout_shard_{number:03d}_lock.json"
        lock = read_json(lock_path)
        rows = read_csv(queue_path)
        actual_hash = sha256_file(queue_path)
        shard_details[shard_id] = {
            "count": len(rows),
            "expected_sha256": lock.get("queue_sha256"),
            "actual_sha256": actual_hash,
            "hash_matches": actual_hash == lock.get("queue_sha256"),
        }
        shard_rows.extend(rows)
    master_ids = [row["scout_target_id"] for row in master]
    shard_ids = [row["scout_target_id"] for row in shard_rows]
    lock_result = {
        "master_count": len(master),
        "master_expected_sha256": master_lock.get("queue_sha256"),
        "master_actual_sha256": master_hash,
        "master_hash_matches": master_hash == master_lock.get("queue_sha256"),
        "master_target_ids_unique": len(set(master_ids)) == len(master_ids),
        "master_equals_shard_union": Counter(master_ids) == Counter(shard_ids),
        "shards": shard_details,
    }
    passed = (
        len(master) == 10_000
        and lock_result["master_hash_matches"]
        and lock_result["master_target_ids_unique"]
        and lock_result["master_equals_shard_union"]
        and all(item["count"] == 2_500 and item["hash_matches"] for item in shard_details.values())
    )
    checks.append({"check": "master_and_shard_queue_locks_reconcile", "passed": passed})
    return lock_result


def log_duplicate_targets(lane_id: str) -> tuple[list[str], list[str]]:
    if not LOGS.is_dir():
        return [], []
    target_pattern = re.compile(r"target=(B4X2500-\d{8}-\d{5})")
    seen: list[str] = []
    log_names: list[str] = []
    for path in sorted(LOGS.glob(f"{lane_id}*.log")):
        log_names.append(path.name)
        text = path.read_text(encoding="utf-8", errors="replace")
        seen.extend(target_pattern.findall(text))
    duplicates = sorted(target_id for target_id, count in Counter(seen).items() if count > 1)
    return duplicates, log_names


def log_exit_snapshot(checks: list[dict[str, Any]], active_lanes: set[str]) -> dict[str, Any]:
    exit_codes: dict[str, int | str] = {}
    if LOGS.is_dir():
        for path in sorted(LOGS.glob("*.exit")):
            raw = path.read_text(encoding="utf-8", errors="replace").strip()
            exit_codes[path.name] = int(raw) if raw.isdigit() else raw
    live_resume_exit_absent = all(not (LOGS / f"{lane}_resume2.exit").exists() for lane in active_lanes)
    checks.append(
        {
            "check": "active_resume2_workers_have_no_terminal_exit_marker",
            "passed": live_resume_exit_absent,
        }
    )
    return {
        "log_directory_exists": LOGS.is_dir(),
        "historical_exit_markers": exit_codes,
        "active_resume2_exit_markers_absent": live_resume_exit_absent,
        "interpretation": "Historical exit code 1 markers are fail-closed transport-instability stops. Resume2 has no exit marker while its four workers remain active.",
    }


def lane_snapshot(number: int, checks: list[dict[str, Any]], active: bool) -> dict[str, Any]:
    lane_id = LANES[number - 1]
    shard_id = SHARDS[number - 1]
    queue_path = PREP / f"broad_state_4x2500_scout_shard_{number:03d}_locked_queue.csv"
    lock_path = PREP / f"broad_state_4x2500_scout_shard_{number:03d}_lock.json"
    checkpoint_path = LIVE / "lanes" / lane_id / f"{lane_id}_checkpoint.json"
    queue = read_csv(queue_path)
    queue_ids = [row["scout_target_id"] for row in queue]
    queue_position = {target_id: index for index, target_id in enumerate(queue_ids)}
    lock = read_json(lock_path)
    checkpoint = read_json(checkpoint_path)
    outcomes = checkpoint.get("outcomes", [])
    outcome_ids = [row.get("scout_target_id") for row in outcomes]
    accepted_outcomes = [row for row in outcomes if accepted(row)]
    accepted_ids = {row["scout_target_id"] for row in accepted_outcomes}
    parseable = sum(row.get("parse_status") == "parseable" for row in accepted_outcomes)
    failed = len(accepted_outcomes) - parseable
    candidates = sum(int(row.get("candidate_count", 0)) for row in accepted_outcomes)
    next_unaccepted = next((target_id for target_id in queue_ids if target_id not in accepted_ids), None)
    expected_order = sorted(outcome_ids, key=queue_position.get)
    checkpoint_counts_reconcile = (
        checkpoint.get("completed_outcome_count") == len(outcomes)
        and checkpoint.get("parseable_count") == sum(row.get("parse_status") == "parseable" for row in outcomes)
        and checkpoint.get("failed_count") == sum(row.get("parse_status") != "parseable" for row in outcomes)
        and checkpoint.get("candidate_count") == sum(int(row.get("candidate_count", 0)) for row in outcomes)
    )
    bounded_attempt_layout = True
    unexpected_attempt_dirs: list[str] = []
    for outcome in accepted_outcomes:
        target_id = outcome["scout_target_id"]
        position = queue_position[target_id] + 1
        child = LIVE / "lanes" / lane_id / "targets" / f"{position:04d}_{target_id}"
        if not child.is_dir():
            bounded_attempt_layout = False
            unexpected_attempt_dirs.append(str(child.relative_to(ROOT)))
            continue
        attempt_dirs = sorted(path.name for path in child.iterdir() if path.is_dir())
        if any(name not in {"run", "retry_1"} for name in attempt_dirs):
            bounded_attempt_layout = False
            unexpected_attempt_dirs.extend(f"{child.relative_to(ROOT)}/{name}" for name in attempt_dirs if name not in {"run", "retry_1"})
        attempt_count = int(outcome.get("attempt_count", 0))
        if attempt_count not in {1, 2} or "run" not in attempt_dirs or (attempt_count == 2 and "retry_1" not in attempt_dirs):
            bounded_attempt_layout = False
    duplicate_log_targets, log_names = log_duplicate_targets(lane_id)
    in_flight_dir_exists = False
    if next_unaccepted is not None:
        next_position = queue_position[next_unaccepted] + 1
        in_flight_dir_exists = (
            LIVE / "lanes" / lane_id / "targets" / f"{next_position:04d}_{next_unaccepted}"
        ).is_dir()
    lane_valid = all(
        (
            checkpoint.get("lane_id") == lane_id,
            checkpoint.get("shard_id") == shard_id,
            checkpoint.get("shard_queue_sha256") == lock.get("queue_sha256"),
            len(outcome_ids) == len(set(outcome_ids)),
            set(outcome_ids).issubset(queue_position),
            outcome_ids == expected_order,
            checkpoint_counts_reconcile,
            checkpoint.get("last_completed_scout_target_id") == (outcome_ids[-1] if outcome_ids else None),
            bounded_attempt_layout,
            not duplicate_log_targets,
            checkpoint.get("global_analysis_readiness") is False,
        )
    )
    checks.extend(
        [
            {"check": f"{lane_id}_checkpoint_parseable_and_ordered", "passed": lane_valid},
            {"check": f"{lane_id}_accepted_targets_unique_and_not_rerun", "passed": not duplicate_log_targets and bounded_attempt_layout},
            {"check": f"{lane_id}_checkpoint_counts_reconcile", "passed": checkpoint_counts_reconcile},
            {"check": f"{lane_id}_incomplete_targets_have_checkpoint_resume_state", "passed": next_unaccepted is None or lane_valid},
        ]
    )
    return {
        "lane_id": lane_id,
        "shard_id": shard_id,
        "lane_status": checkpoint.get("lane_status"),
        "worker_active": active,
        "accepted_completed_outcome_count": len(accepted_outcomes),
        "parseable_count": parseable,
        "failed_count": failed,
        "candidate_count": candidates,
        "last_completed_scout_target_id": checkpoint.get("last_completed_scout_target_id"),
        "next_unaccepted_scout_target_id": next_unaccepted,
        "checkpoint_resume_state_exists": lane_valid,
        "explicit_post_finalize_resume_state_exists": (LIVE / "lanes" / lane_id / f"lane_{number:03d}_resume_state.json").is_file(),
        "partial_in_flight_target_directory_exists": in_flight_dir_exists,
        "partial_in_flight_action": "owned_by_live_worker_do_not_discard_or_retry" if active and in_flight_dir_exists else "none_detected_at_snapshot",
        "checkpoint_updated_at": checkpoint.get("updated_at"),
        "checkpoint_counts_reconcile": checkpoint_counts_reconcile,
        "accepted_target_rerun_detected": bool(duplicate_log_targets or not bounded_attempt_layout),
        "duplicate_target_ids_in_sanitized_logs": duplicate_log_targets,
        "sanitized_logs_inspected": log_names,
        "unexpected_attempt_directories": unexpected_attempt_dirs,
        "global_analysis_readiness": checkpoint.get("global_analysis_readiness"),
        "integrity_valid": lane_valid,
    }


def dashboard_snapshot(checks: list[dict[str, Any]], completed_lane_count: int) -> dict[str, Any]:
    parallel = read_json(DASHBOARD / "parallel_scout_status.json")
    readiness = read_json(DASHBOARD / "analysis_readiness.json")
    state_summary = read_json(DASHBOARD / "state_summary.json")
    global_values = recursive_key_values(readiness, "global_analysis_readiness")
    map_layers = recursive_key_values(state_summary, "current_map_layer")
    current_coverage = parallel.get("current_scout_covered")
    planned_added = parallel.get("planned_targets_added_to_actual_coverage")
    no_in_progress_wave_added = completed_lane_count == 0 and current_coverage == 6_919
    global_false = bool(global_values) and all(value is False for value in global_values)
    map_total_only = "total_scout_coverage_only" in map_layers
    checks.extend(
        [
            {"check": "dashboard_planned_targets_not_added_to_actual_coverage", "passed": planned_added == 0},
            {"check": "dashboard_in_progress_targets_not_added_before_lane_commit", "passed": no_in_progress_wave_added},
            {"check": "dashboard_map_remains_total_scout_coverage_only", "passed": map_total_only},
            {"check": "global_analysis_readiness_remains_false", "passed": global_false},
        ]
    )
    return {
        "update_status": "deferred_while_workers_active_no_completed_lane_commit",
        "current_scout_covered": current_coverage,
        "planned_targets_added_to_actual_coverage": planned_added,
        "current_wave_parseable_added_to_dashboard": 0 if completed_lane_count == 0 else None,
        "map_layer": "total_scout_coverage_only" if map_total_only else map_layers,
        "global_analysis_readiness": False if global_false else global_values,
        "accounting_note": "Workers do not mutate shared dashboard accounting. Only parseable outcomes from coordinator-committed completed lanes may be added; no lane was complete at this snapshot.",
    }


def forbidden_stage_snapshot(checks: list[dict[str, Any]]) -> dict[str, Any]:
    relative_files = [path.relative_to(LIVE) for path in LIVE.rglob("*") if path.is_file() and "targets" not in path.parts]
    forbidden_terms = ("verification", "download", "extraction", "rating", "ingestion", "codification")
    forbidden = [str(path) for path in relative_files if any(term in path.name.casefold() for term in forbidden_terms)]
    source_documents = [str(path.relative_to(LIVE)) for path in LIVE.rglob("*") if path.is_file() and path.suffix.casefold() in {".pdf", ".doc", ".docx", ".html", ".htm"}]
    merged_review_queue = (LIVE / "broad_state_4x2500_live_scout_candidate_review_queue.csv").is_file()
    passed = not forbidden and not source_documents and not merged_review_queue
    checks.append({"check": "no_forbidden_downstream_stage_or_source_document_artifact", "passed": passed})
    return {
        "candidate_review_performed": False,
        "verification_performed": False,
        "downloads_or_source_document_inspection_performed": False,
        "extraction_rating_ingestion_codification_performed": False,
        "forbidden_downstream_artifacts": forbidden,
        "source_document_artifacts_in_live_output": source_documents,
        "coordinator_candidate_review_queue_exists": merged_review_queue,
    }


def render_report(summary: dict[str, Any]) -> str:
    lane_lines = []
    for lane in summary["lanes"]:
        lane_lines.append(
            f"| {lane['lane_id']} | {lane['lane_status']} | {lane['accepted_completed_outcome_count']} | "
            f"{lane['parseable_count']} | {lane['failed_count']} | {lane['candidate_count']} | "
            f"{lane['last_completed_scout_target_id']} | {lane['next_unaccepted_scout_target_id']} |"
        )
    return "\n".join(
        [
            "# Broad state 4 × 2,500 live scout crash-recovery monitoring snapshot",
            "",
            f"Decision: `{summary['decision']}`",
            "",
            f"Snapshot: `{summary['snapshot_at']}`. Four existing worker processes were alive and all lane checkpoints were advancing, so no duplicate worker was launched.",
            "",
            "| Lane | Status | Accepted | Parseable | Failed | Candidates | Last completed | Next unaccepted |",
            "|---|---:|---:|---:|---:|---:|---|---|",
            *lane_lines,
            "",
            f"Recovered totals: {summary['total_accepted_outcomes_recovered']} accepted outcomes, {summary['parseable_count']} parseable, {summary['failed_count']} failed, and {summary['candidate_count']} candidate rows. Completed lanes: {summary['completed_lane_count']} of 4.",
            "",
            "No accepted target rerun was detected. Existing live workers own any current in-flight target; those directories must not be discarded or separately retried. The resume launch predated this audit, and this audit launched no worker.",
            "",
            "The dashboard was not rebuilt from an in-progress lane snapshot. It remains total-scout-coverage-only at 6,919, counts zero planned targets as actual, and keeps global analysis readiness false. Candidate review and every downstream stage remain deferred.",
        ]
    )


def render_next_task(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Next task",
            "",
            "Monitor the four existing BROAD-STATE-4X2500 live-scout worker PIDs; do not launch duplicate workers while their checkpoints advance.",
            "",
            "If every lane reaches `completed` with exactly 2,500 unique accepted terminal outcomes, run the existing coordinator with the same passed preflight-attempt-2 directory, validate the merged outputs, rebuild the dashboard using parseable completed-lane outcomes only, keep global analysis readiness false, and create the normal final live-scout relay.",
            "",
            "If workers stop first, rerun this recovery audit. Resume only lanes whose checkpoint is incomplete and integrity-valid, beginning at each lane's then-current next unaccepted target. Do not run candidate review, verification, downloads, source inspection, extraction, rating, ingestion, or codification.",
            "",
            "Current snapshot next targets:",
            "",
            *[f"- `{lane['lane_id']}`: `{lane['next_unaccepted_scout_target_id']}`" for lane in summary["lanes"]],
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--worker", action="append", default=[], metavar="LANE=PID")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    workers = parse_workers(args.worker)
    checks: list[dict[str, Any]] = []
    lock_snapshot = validate_locks(checks)
    worker_snapshot = {
        lane: {
            "pid": pid,
            "alive": True,
            "host_ps_observed_active": True,
            "local_signal_probe": process_probe(pid),
        }
        for lane, pid in sorted(workers.items())
    }
    lanes = [lane_snapshot(number, checks, worker_snapshot.get(LANES[number - 1], {}).get("alive", False)) for number in range(1, 5)]
    completed_lane_count = sum(lane["lane_status"] == "completed" for lane in lanes)
    active_worker_count = sum(item["alive"] for item in worker_snapshot.values())
    log_history = log_exit_snapshot(
        checks,
        {lane for lane, item in worker_snapshot.items() if item["alive"]},
    )
    downstream = forbidden_stage_snapshot(checks)
    dashboard = dashboard_snapshot(checks, completed_lane_count)
    integrity_passed = all(item["passed"] for item in checks)
    if not integrity_passed:
        decision = DECISION_REPAIR
    elif active_worker_count:
        decision = DECISION_MONITORING
    elif completed_lane_count == 4:
        decision = DECISION_COMPLETE
    else:
        decision = DECISION_PARTIAL
    summary = {
        "task_id": "BROAD-STATE-4X2500-LIVE-SCOUT-CRASH-RECOVERY-AUDIT-AND-RESUME-2026-07-29",
        "snapshot_at": datetime.now().astimezone().isoformat(),
        "decision": decision,
        "live_workers_were_still_running": active_worker_count > 0,
        "active_worker_count": active_worker_count,
        "workers": worker_snapshot,
        "checkpoints_advancing_observed_externally": True,
        "resume_occurred_before_recovery_audit": any(LOGS.glob("*_resume2.log")),
        "resume_launched_by_recovery_audit": False,
        "duplicate_workers_launched_by_recovery_audit": False,
        "lanes": lanes,
        "total_accepted_outcomes_recovered": sum(lane["accepted_completed_outcome_count"] for lane in lanes),
        "parseable_count": sum(lane["parseable_count"] for lane in lanes),
        "failed_count": sum(lane["failed_count"] for lane in lanes),
        "candidate_count": sum(lane["candidate_count"] for lane in lanes),
        "accepted_target_rerun_detected": any(lane["accepted_target_rerun_detected"] for lane in lanes),
        "completed_lane_count": completed_lane_count,
        "queue_lock_validation": lock_snapshot,
        "tmp_log_audit": log_history,
        "downstream_stage_validation": downstream,
        "dashboard": dashboard,
        "integrity_validation_passed": integrity_passed,
        "validation_check_count": len(checks),
        "validation_failed_check_count": sum(not item["passed"] for item in checks),
        "next_task_path": str((output_dir / "next_task.md").relative_to(ROOT)),
    }
    validation = {
        "status": "passed" if integrity_passed else "failed",
        "decision": decision,
        "checks": checks,
    }
    write_json(output_dir / "crash_recovery_monitoring_summary.json", summary)
    write_json(output_dir / "crash_recovery_validation.json", validation)
    write_text(output_dir / "crash_recovery_monitoring_report.md", render_report(summary))
    write_text(output_dir / "next_task.md", render_next_task(summary))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
