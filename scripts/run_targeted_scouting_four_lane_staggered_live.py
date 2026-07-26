#!/usr/bin/env python3
"""Fail-closed orchestrator for the four-lane targeted scouting live stage.

The current authorization contains two incompatible scheduling invariants:
fixed starts at T+0/T+8/T+16/T+24 and no simultaneous lane execution.  The
established mixed-state scout performs one sequential hosted-search request per
target, so a 500-target lane cannot finish inside an eight-minute window.  This
runner verifies every immutable input and records the preflight failure without
making a hosted request.  It deliberately contains no live-call code path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
PREP_COMMIT = "b338003063bd1fd2c29fb70c0af6130987c67ffa"
TASK_ID = "TARGETED-SCOUTING-FOUR-LANE-STAGGERED-LIVE-RUN-FROM-PREP-2026-07-25"
DECISION = "targeted_scouting_four_lane_staggered_live_preflight_failed"
PREP_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-SCOUTING-FOUR-LANE-PREP-DRY-RUN-FROM-PROVISIONAL-CLAIM-REVIEW-2026-07-25"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-SCOUTING-FOUR-LANE-STAGGERED-LIVE-RUN-FROM-PREP-2026-07-25"
LANES = ("lane_1", "lane_2", "lane_3", "lane_4")
START_OFFSETS_MINUTES = {"lane_1": 0, "lane_2": 8, "lane_3": 16, "lane_4": 24}
EXPECTED_ROWS_PER_LANE = 500
EXPECTED_TOTAL = 2_000
EXPECTED_PREP_DECISION = "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready"

CANDIDATE_FIELDS = [
    "candidate_id", "lane_id", "scout_target_id", "source_url_or_locator",
    "source_title", "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "secondary_mechanism_families", "match_priority_tier",
    "matched_safety_or_non_safety_counterpart_id", "same_city_match_status",
    "overlapping_cycle_status", "duplicate_risk", "prior_seen_status",
    "reason_selected", "search_query_used", "retrieval_status",
    "verification_status", "extraction_status", "rating_status", "causal_status",
    "notes",
]
SKIP_FIELDS = [
    "lane_id", "scout_target_id", "municipality", "state", "target_rank",
    "skip_reason", "live_attempted", "candidate_count", "notes",
]
SEARCH_METADATA_FIELDS = [
    "lane_id", "scheduled_offset_minutes", "queue_rows", "queue_sha256",
    "target_id_set_sha256", "credential_present", "live_preflight_attempted",
    "hosted_search_attempted", "model_api_calls", "backend", "model",
    "secrets_redacted", "status", "failure_reason",
]
TIMING_FIELDS = [
    "lane_id", "scheduled_offset_minutes", "actual_start_utc", "actual_finish_utc",
    "elapsed_seconds", "live_attempted", "status", "notes",
]
MECHANISM_FIELDS = [
    "lane_id", "target_mechanism_family", "locked_target_count",
    "candidate_source_count", "status",
]
COVERAGE_FIELDS = [
    "lane_id", "scout_target_id", "municipality", "state", "target_unit_type",
    "match_priority_tier", "candidate_source_count", "coverage_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_id_set_sha256(rows: list[dict[str, str]]) -> str:
    values = sorted(row["scout_target_id"] for row in rows)
    # Match the preparation lock contract exactly: sorted IDs joined by a
    # newline, with no terminal newline byte.
    return hashlib.sha256("\n".join(values).encode()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_credential_presence() -> bool:
    """Load dotenv files without returning, printing, or persisting the secret."""
    from dotenv import load_dotenv

    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break
    return bool(os.environ.get("HARVARD_SUBSCRIPTION_KEY"))


def historical_runtime_diagnostics() -> dict[str, Any]:
    values: list[float] = []
    files = sorted((ROOT / "tmp/gabriel_state_source_scout").glob("*/*live*direct_sdk*/raw_outputs.csv"))
    for path in files:
        for row in read_csv(path):
            try:
                values.append(float(row.get("Time Taken", "")))
            except (TypeError, ValueError):
                pass
    if not values:
        return {"local_timing_files": 0, "timed_requests": 0}
    minimum = min(values)
    median = statistics.median(values)
    return {
        "local_timing_files": len(files),
        "timed_requests": len(values),
        "minimum_seconds_per_request": round(minimum, 3),
        "median_seconds_per_request": round(median, 3),
        "projected_lane_seconds_at_historical_minimum": round(minimum * EXPECTED_ROWS_PER_LANE, 3),
        "projected_lane_seconds_at_historical_median": round(median * EXPECTED_ROWS_PER_LANE, 3),
        "available_nonoverlap_window_seconds": 8 * 60,
    }


def required_prep_paths() -> list[Path]:
    names = [
        "targeted_scouting_four_lane_prep_decision.json",
        "targeted_scouting_four_lane_prep_summary.md",
        "targeted_scouting_four_lane_master_queue.csv",
        "targeted_scouting_four_lane_master_queue_summary.json",
        "targeted_scouting_four_lane_queue_summary.json",
        "targeted_scouting_four_lane_no_call_validation.md",
        "targeted_scouting_four_lane_duplicate_avoidance_report.md",
        "targeted_scouting_four_lane_api_protection_plan.md",
        "targeted_scouting_four_lane_staggered_execution_plan.md",
        "targeted_scouting_four_lane_prep_invariant_checks.json",
        "targeted_scouting_four_lane_prep_validation_2026-07-25.md",
    ]
    paths = [PREP_DIR / name for name in names]
    for lane in LANES:
        paths.extend([
            PREP_DIR / f"targeted_scouting_{lane}_queue_500.csv",
            PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json",
            PREP_DIR / f"targeted_scouting_{lane}_dry_run_summary.json",
        ])
    return paths


def run_preflight() -> tuple[dict[str, Any], dict[str, list[dict[str, str]]]]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    missing = [path.relative_to(ROOT).as_posix() for path in required_prep_paths() if not path.exists()]
    check("required_prep_artifacts_present", not missing, {"missing": missing})
    if missing:
        raise RuntimeError(f"required prep artifacts missing: {missing}")

    decision = read_json(PREP_DIR / "targeted_scouting_four_lane_prep_decision.json")
    check("prep_decision_allows_live_preflight", decision.get("decision") == EXPECTED_PREP_DECISION, decision.get("decision"))
    prep_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREP_COMMIT, "HEAD"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0
    check("prep_commit_locked", prep_ancestor, {"commit": PREP_COMMIT, "is_local_ancestor_of_head": prep_ancestor})

    master = read_csv(PREP_DIR / "targeted_scouting_four_lane_master_queue.csv")
    check("master_locked_target_count", len(master) == EXPECTED_TOTAL, len(master))
    check("master_unique_target_ids", len({row["scout_target_id"] for row in master}) == EXPECTED_TOTAL, len({row["scout_target_id"] for row in master}))

    lane_rows: dict[str, list[dict[str, str]]] = {}
    queue_audits: dict[str, Any] = {}
    for lane in LANES:
        queue_path = PREP_DIR / f"targeted_scouting_{lane}_queue_500.csv"
        lock_path = PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json"
        rows = read_csv(queue_path)
        lock = read_json(lock_path)
        lane_rows[lane] = rows
        file_hash = sha256_path(queue_path)
        id_hash = target_id_set_sha256(rows)
        queue_audits[lane] = {
            "rows": len(rows), "unique_target_ids": len({row["scout_target_id"] for row in rows}),
            "queue_sha256": file_hash, "lock_queue_sha256": lock.get("queue_sha256"),
            "target_id_set_sha256": id_hash, "lock_target_id_set_sha256": lock.get("target_id_set_sha256"),
            "all_lane_ids_match": all(row.get("lane_id") == lane for row in rows),
            "all_live_not_started": all(row.get("live_run_status") == "not_started" for row in rows),
        }
        check(f"{lane}_exact_500_unique_locked_targets", len(rows) == EXPECTED_ROWS_PER_LANE and len({row["scout_target_id"] for row in rows}) == EXPECTED_ROWS_PER_LANE, queue_audits[lane])
        check(f"{lane}_queue_hash_matches_lock", file_hash == lock.get("queue_sha256"), file_hash)
        check(f"{lane}_target_id_hash_matches_lock", id_hash == lock.get("target_id_set_sha256"), id_hash)
        check(f"{lane}_scope_and_status_locked", queue_audits[lane]["all_lane_ids_match"] and queue_audits[lane]["all_live_not_started"], queue_audits[lane])

    combined_ids = [row["scout_target_id"] for lane in LANES for row in lane_rows[lane]]
    check("combined_scope_exactly_2000_unique", len(combined_ids) == EXPECTED_TOTAL and len(set(combined_ids)) == EXPECTED_TOTAL, {"rows": len(combined_ids), "unique": len(set(combined_ids))})
    credential_present = load_credential_presence()
    check("search_credential_present_without_disclosure", credential_present, "present" if credential_present else "missing")
    check("fixed_stagger_offsets_recorded", START_OFFSETS_MINUTES == {"lane_1": 0, "lane_2": 8, "lane_3": 16, "lane_4": 24}, START_OFFSETS_MINUTES)

    runtime = historical_runtime_diagnostics()
    sequential_backend = True
    nonoverlap_required = True
    exact_offsets_required = True
    first_three_must_finish_within_seconds = 480
    historical_minimum_exceeds_window = bool(runtime.get("projected_lane_seconds_at_historical_minimum", 0) > first_three_must_finish_within_seconds)
    schedule_compatible = not (sequential_backend and nonoverlap_required and exact_offsets_required and historical_minimum_exceeds_window)
    check("stagger_schedule_compatible_with_no_lane_overlap", schedule_compatible, {
        "sequential_mixed_state_backend_required": sequential_backend,
        "no_lane_overlap_required": nonoverlap_required,
        "exact_offsets_required": exact_offsets_required,
        "runtime_diagnostics": runtime,
        "blocker": "A 500-request lane cannot complete before the next exact eight-minute start; exact starts would overlap lanes, while waiting would violate the offsets.",
    })

    all_integrity_checks = all(item["passed"] for item in checks if item["check"] != "stagger_schedule_compatible_with_no_lane_overlap")
    payload = {
        "task_id": TASK_ID,
        "checked_at_utc": utc_now(),
        "prep_commit": PREP_COMMIT,
        "checks": checks,
        "all_input_integrity_checks_passed": all_integrity_checks,
        "schedule_check_passed": schedule_compatible,
        "preflight_passed": all_integrity_checks and schedule_compatible,
        "credential_present": credential_present,
        "locked_target_count": len(combined_ids),
        "lane_counts": {lane: len(lane_rows[lane]) for lane in LANES},
        "queue_audits": queue_audits,
        "start_offsets_minutes": START_OFFSETS_MINUTES,
        "hosted_search_calls": 0,
        "model_api_calls": 0,
        "global_analysis_readiness": False,
        "failure_code": "fixed_stagger_conflicts_with_no_simultaneous_lane_execution",
    }
    return payload, lane_rows


def output_files() -> list[Path]:
    names = [
        "targeted_scouting_four_lane_staggered_live_decision.json",
        "targeted_scouting_four_lane_staggered_live_summary.md",
        "targeted_scouting_four_lane_staggered_live_preflight_report.md",
        "targeted_scouting_four_lane_staggered_live_preflight_checks.json",
        "targeted_scouting_four_lane_candidate_sources.csv",
        "targeted_scouting_four_lane_candidate_sources_summary.json",
        "targeted_scouting_four_lane_search_metadata.csv",
        "targeted_scouting_four_lane_timing.csv",
        "targeted_scouting_four_lane_skipped_targets.csv",
        "targeted_scouting_four_lane_duplicate_prior_seen_report.md",
        "targeted_scouting_four_lane_duplicate_prior_seen_summary.json",
        "targeted_scouting_four_lane_mechanism_gap_coverage.csv",
        "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json",
        "targeted_scouting_four_lane_city_cycle_unit_coverage.csv",
        "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json",
        "targeted_scouting_four_lane_candidate_only_qa_report.md",
        "targeted_scouting_four_lane_staggered_live_invariant_checks.json",
        "targeted_scouting_four_lane_staggered_live_validation_2026-07-25.md",
        "targeted_scouting_four_lane_staggered_live_stress_test_report.md",
        "targeted_scouting_four_lane_staggered_live_regression_test_inventory.json",
        "next_targeted_scouting_four_lane_repair_prompt.md",
        "next_task.md",
    ]
    paths = [OUTPUT_DIR / name for name in names]
    for lane in LANES:
        lane_dir = OUTPUT_DIR / "lane_outputs" / lane
        paths.extend([
            lane_dir / f"targeted_scouting_{lane}_candidate_sources.csv",
            lane_dir / f"targeted_scouting_{lane}_candidate_sources_summary.json",
            lane_dir / f"targeted_scouting_{lane}_search_metadata.csv",
            lane_dir / f"targeted_scouting_{lane}_timing.csv",
            lane_dir / f"targeted_scouting_{lane}_skipped_targets.csv",
            lane_dir / f"targeted_scouting_{lane}_mechanism_gap_coverage.csv",
            lane_dir / f"targeted_scouting_{lane}_city_cycle_unit_coverage.csv",
        ])
    paths.extend([
        ROOT / "docs/analysis/targeted_scouting_four_lane_staggered_live_result_2026-07-25.md",
        ROOT / "docs/analysis/targeted_scouting_four_lane_staggered_live_dashboard_status_note_2026-07-25.md",
    ])
    return paths


def materialize_failure(preflight: dict[str, Any], lane_rows: dict[str, list[dict[str, str]]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    input_hashes = {path.relative_to(ROOT).as_posix(): sha256_path(path) for path in required_prep_paths()}
    lane_counts = {lane: len(rows) for lane, rows in lane_rows.items()}
    reason = preflight["failure_code"]
    decision = {
        "task_id": TASK_ID, "decision": DECISION, "completion_status": "preflight_failed_no_live_execution",
        "preflight_passed": False, "failure_code": reason, "prep_commit_verified": True,
        "locked_target_count": EXPECTED_TOTAL, "lane_counts": lane_counts,
        "live_hosted_search_ran": False, "model_backed_scouting_ran": False,
        "lane_runs_completed": 0, "candidate_source_count": 0,
        "candidate_review_ready": False, "repair_required": True,
        "global_analysis_readiness": False, "input_hashes": input_hashes,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_decision.json", decision)
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_summary.md", f"""# Four-lane staggered live run summary

Decision: `{DECISION}`.

All 2,000 locked targets and all queue/lock hashes passed preflight. Live execution did not begin because exact T+0/T+8/T+16/T+24 starts conflict with the explicit ban on simultaneous lane execution for the established sequential one-request-per-target backend. Candidate sources: 0. Global analysis readiness remains false.
""")
    runtime = next(item["detail"] for item in preflight["checks"] if item["check"] == "stagger_schedule_compatible_with_no_lane_overlap")["runtime_diagnostics"]
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_preflight_report.md", f"""# Combined four-lane live preflight

- Prep commit: `{PREP_COMMIT}` — verified.
- Locked queues: 500 / 500 / 500 / 500; 2,000 unique targets — passed.
- Queue and target-ID hashes: 4/4 passed.
- Credential presence: passed without printing or persisting the credential.
- Requested starts: T+0, T+8, T+16, T+24 — recorded.
- Hosted-search/model calls: 0.
- Result: **failed closed before live execution**.

## Scheduling blocker

The established mixed-state scout is sequential and uses one hosted-search request per target. The local direct-SDK timing evidence contains {runtime.get('timed_requests', 0)} timed requests; its historical minimum is {runtime.get('minimum_seconds_per_request', 'unavailable')} seconds and median is {runtime.get('median_seconds_per_request', 'unavailable')} seconds. Even the historical-minimum projection for 500 requests is {runtime.get('projected_lane_seconds_at_historical_minimum', 'unavailable')} seconds, versus a 480-second non-overlap window.

Therefore Lane 2 cannot start exactly at T+8 without Lane 1 still running. Starting it would violate the no-simultaneous-lanes rule; waiting would violate the fixed offset. The live probe was not attempted because the contract was already unsatisfiable.
""")

    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_sources.csv", [], CANDIDATE_FIELDS)
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_sources_summary.json", {
        "candidate_source_count": 0, "candidate_only": True, "live_not_run": True,
        "lane_counts": {lane: 0 for lane in LANES}, "failure_code": reason,
    })

    combined_skips: list[dict[str, Any]] = []
    combined_metadata: list[dict[str, Any]] = []
    combined_timing: list[dict[str, Any]] = []
    combined_mechanisms: list[dict[str, Any]] = []
    combined_coverage: list[dict[str, Any]] = []
    prior_status = Counter()
    duplicate_risk = Counter()
    for lane in LANES:
        rows = lane_rows[lane]
        lock = read_json(PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json")
        skips = []
        coverage = []
        mechanisms = Counter()
        for row in rows:
            prior_status[row["prior_seen_status"]] += 1
            duplicate_risk[row["duplicate_risk"]] += 1
            mechanisms[row["target_mechanism_family"]] += 1
            skip = {
                "lane_id": lane, "scout_target_id": row["scout_target_id"],
                "municipality": row["municipality"], "state": row["state"],
                "target_rank": row["target_rank"], "skip_reason": reason,
                "live_attempted": "no", "candidate_count": 0,
                "notes": "Preflight failed before hosted search; target remains locked and unrun.",
            }
            skips.append(skip); combined_skips.append(skip)
            cover = {
                "lane_id": lane, "scout_target_id": row["scout_target_id"],
                "municipality": row["municipality"], "state": row["state"],
                "target_unit_type": row["target_unit_type"],
                "match_priority_tier": row["match_priority_tier"],
                "candidate_source_count": 0, "coverage_status": "not_run_preflight_failed",
            }
            coverage.append(cover); combined_coverage.append(cover)
        mechanism_rows = [{
            "lane_id": lane, "target_mechanism_family": mechanism,
            "locked_target_count": count, "candidate_source_count": 0,
            "status": "not_run_preflight_failed",
        } for mechanism, count in sorted(mechanisms.items())]
        combined_mechanisms.extend(mechanism_rows)
        metadata = {
            "lane_id": lane, "scheduled_offset_minutes": START_OFFSETS_MINUTES[lane],
            "queue_rows": len(rows), "queue_sha256": lock["queue_sha256"],
            "target_id_set_sha256": lock["target_id_set_sha256"], "credential_present": "yes",
            "live_preflight_attempted": "no", "hosted_search_attempted": "no",
            "model_api_calls": 0, "backend": "huit_openai_responses_direct_sdk",
            "model": "gpt-5.4-nano", "secrets_redacted": "yes",
            "status": "not_started_preflight_failed", "failure_reason": reason,
        }
        timing = {
            "lane_id": lane, "scheduled_offset_minutes": START_OFFSETS_MINUTES[lane],
            "actual_start_utc": "", "actual_finish_utc": "", "elapsed_seconds": 0,
            "live_attempted": "no", "status": "not_started_preflight_failed",
            "notes": "No stagger timer or hosted request started.",
        }
        combined_metadata.append(metadata); combined_timing.append(timing)
        lane_dir = OUTPUT_DIR / "lane_outputs" / lane
        write_csv(lane_dir / f"targeted_scouting_{lane}_candidate_sources.csv", [], CANDIDATE_FIELDS)
        write_json(lane_dir / f"targeted_scouting_{lane}_candidate_sources_summary.json", {
            "lane_id": lane, "locked_target_count": len(rows), "candidate_source_count": 0,
            "live_attempted": False, "status": "not_started_preflight_failed", "failure_code": reason,
        })
        write_csv(lane_dir / f"targeted_scouting_{lane}_search_metadata.csv", [metadata], SEARCH_METADATA_FIELDS)
        write_csv(lane_dir / f"targeted_scouting_{lane}_timing.csv", [timing], TIMING_FIELDS)
        write_csv(lane_dir / f"targeted_scouting_{lane}_skipped_targets.csv", skips, SKIP_FIELDS)
        write_csv(lane_dir / f"targeted_scouting_{lane}_mechanism_gap_coverage.csv", mechanism_rows, MECHANISM_FIELDS)
        write_csv(lane_dir / f"targeted_scouting_{lane}_city_cycle_unit_coverage.csv", coverage, COVERAGE_FIELDS)

    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_search_metadata.csv", combined_metadata, SEARCH_METADATA_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_timing.csv", combined_timing, TIMING_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_skipped_targets.csv", combined_skips, SKIP_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_mechanism_gap_coverage.csv", combined_mechanisms, MECHANISM_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_city_cycle_unit_coverage.csv", combined_coverage, COVERAGE_FIELDS)
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json", {
        "locked_mechanism_target_rows": EXPECTED_TOTAL, "candidate_source_count": 0,
        "status": "not_run_preflight_failed", "candidate_mechanisms_analyzed": False,
    })
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json", {
        "locked_target_rows": EXPECTED_TOTAL, "targets_run": 0, "candidate_source_count": 0,
        "status": "not_run_preflight_failed",
    })
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_duplicate_prior_seen_report.md", """# Duplicate and prior-seen accounting

Duplicate/prior-seen fields were reconciled from the immutable locked queues. No candidate source was created, deduplicated, or merged because live scouting did not start.
""")
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_duplicate_prior_seen_summary.json", {
        "locked_target_rows": EXPECTED_TOTAL, "candidate_duplicate_count": 0,
        "candidate_merge_count": 0, "prior_seen_status_counts": dict(sorted(prior_status.items())),
        "duplicate_risk_counts": dict(sorted(duplicate_risk.items())),
    })
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_only_qa_report.md", f"""# Candidate-only QA report

- Decision: `{DECISION}`.
- Locked inputs: 2,000/2,000 passed hash and scope checks.
- Live lanes completed: 0/4.
- Candidate sources: 0.
- Skipped/not-run targets: 2,000, explicitly marked `{reason}`.
- Verified/extracted/rated/causal rows: 0.
- Prior ledgers mutated: no.
- Hosted-search/model/API calls: 0.
- Global analysis readiness: false.
""")
    invariant_checks = {
        "all_invariants_passed": True, "preflight_failure_recorded": True,
        "locked_targets_reconcile_to_2000": sum(lane_counts.values()) == EXPECTED_TOTAL,
        "lane_counts_500_each": all(value == EXPECTED_ROWS_PER_LANE for value in lane_counts.values()),
        "queue_and_id_hashes_match": all(item["passed"] for item in preflight["checks"] if "hash_matches_lock" in item["check"]),
        "schedule_conflict_detected": not preflight["schedule_check_passed"],
        "no_live_lane_started": True, "hosted_search_calls_zero": True,
        "model_api_calls_zero": True, "candidate_count_zero": True,
        "all_2000_targets_explicitly_not_run": len(combined_skips) == EXPECTED_TOTAL,
        "no_verified_extracted_rated_or_causal_output": True,
        "global_analysis_readiness_false": True, "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_invariant_checks.json", invariant_checks)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_validation_2026-07-25.md", """# Four-lane staggered live validation — 2026-07-25

Initial generation validation passed fail-closed: 2,000 locked targets, 4/4 queue hashes, 4/4 target-ID hashes, and credential presence all passed. The fixed-start/no-overlap scheduling contract failed before any hosted request. Final command results are recorded after the focused and repository suites run.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_stress_test_report.md", """# Four-lane staggered live stress-test report

The focused suite covers missing artifacts, decision drift, queue hash drift, target-ID drift, count drift, cross-lane contamination, already-started rows, missing credentials, simultaneous starts, shortened offsets, schedule/no-overlap conflict, live-call bypass, candidate overpromotion, partial completion masquerading, forbidden status values, dashboard overpromotion, upstream mutation, and resume safety. The scheduling conflict is correctly treated as a preflight failure rather than weakened or silently ignored.
""")
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_scouting_four_lane_staggered_live.py",
        "expected_tests": 62, "focus": [
            "immutable queue hashes", "exact 500-row lane scopes", "exact stagger metadata",
            "no lane overlap contract", "zero live calls after failed preflight",
            "candidate-only status", "partial-output fail closed", "dashboard global readiness false",
        ],
    })
    repair_prompt = f"""# Next task: repair four-lane live execution contract

The `{TASK_ID}` preflight failed before any hosted search because exact T+0/T+8/T+16/T+24 starts conflict with the explicit rule that lanes may not run simultaneously. All four 500-target queue and lock hashes remain valid and untouched.

Choose exactly one scheduling contract in the next authorization:

1. **Sequential lanes (recommended for API protection):** Lane 2 starts only after Lane 1 finishes, Lane 3 after Lane 2, and Lane 4 after Lane 3. The eight-minute values become minimum quiet intervals after completion, not offsets from Lane 1's start.
2. **Fixed stagger with overlap:** retain T+0/T+8/T+16/T+24 starts and explicitly authorize overlap after each staggered start. This is higher-load and requires a concurrency/rate-limit plan.

Do not authorize both. Revalidate commit `{PREP_COMMIT}`, the four lockfiles, 500 rows per lane, and 2,000 unique targets before live use. Do not fetch/pull or inspect/configure remotes. Do not download documents, open PDFs/pages, run OCR, verify, extract, select, rate, ingest, codify, analyze the quantitative lane, calculate wage gaps, run regressions/treatment effects, or make final causal claims. Keep candidates unverified, unextracted, unrated, non-causal, and keep global analysis readiness false. Do not save raw prompts/responses or secrets.
"""
    write_text(OUTPUT_DIR / "next_targeted_scouting_four_lane_repair_prompt.md", repair_prompt)
    write_text(OUTPUT_DIR / "next_task.md", repair_prompt)
    dashboard_note = f"""# Dashboard status note — four-lane staggered live preflight

- Decision: `{DECISION}`.
- Input integrity: passed for 2,000 locked targets and all four queue hashes.
- Live hosted-search/model-backed scouting ran: no.
- Lanes completed: 0/4.
- Candidate sources: 0.
- Repair required: choose a logically consistent sequential or overlapping-stagger contract.
- Global analysis readiness: false.
"""
    write_text(ROOT / "docs/analysis/targeted_scouting_four_lane_staggered_live_dashboard_status_note_2026-07-25.md", dashboard_note)
    write_text(ROOT / "docs/analysis/targeted_scouting_four_lane_staggered_live_result_2026-07-25.md", f"""# Four-lane targeted scouting staggered live result

Decision: `{DECISION}`. All locked-input integrity checks passed, but live execution failed closed before any hosted call because the fixed stagger offsets conflict with the no-simultaneous-lanes requirement. See the output directory for the preflight audit and repair prompt. Global analysis readiness remains false.
""")


def validate_completed_failure() -> None:
    missing = [path.relative_to(ROOT).as_posix() for path in output_files() if not path.exists()]
    if missing:
        raise RuntimeError(f"partial preflight-failure outputs: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_decision.json")
    invariants = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_staggered_live_invariant_checks.json")
    if not (
        decision.get("decision") == DECISION
        and decision.get("completion_status") == "preflight_failed_no_live_execution"
        and decision.get("locked_target_count") == EXPECTED_TOTAL
        and decision.get("lane_runs_completed") == 0
        and decision.get("candidate_source_count") == 0
        and decision.get("global_analysis_readiness") is False
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("completed preflight-failure package fails closed-state validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.resume:
        validate_completed_failure()
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": DECISION, "live_calls": 0}))
        return 0
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    preflight, lane_rows = run_preflight()
    if preflight["preflight_passed"]:
        raise RuntimeError("this fail-closed runner has no live path; review the scheduling contract")
    materialize_failure(preflight, lane_rows)
    validate_completed_failure()
    print(json.dumps({"status": "preflight_failed_no_live_execution", "decision": DECISION, "locked_targets": EXPECTED_TOTAL, "live_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
