#!/usr/bin/env python3
"""Fail-closed tests for the staggered four-lane 4x1000 live scout."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_broad_state_4x1000_live_scout as worker  # noqa: E402
import run_broad_state_4x1000_parallel_live_scout as coordinator  # noqa: E402


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def data(name: str):
    return json.loads((coordinator.OUTPUT / name).read_text(encoding="utf-8"))


def main() -> None:
    locks = worker.validate_locks()
    assert locks["master_count"] == 4000
    assert set(locks["shard_counts"].values()) == {1000}
    decision = data("broad_state_4x1000_parallel_live_scout_decision.json")
    assert decision["decision"] == coordinator.DECISION_COMPLETE
    assert decision["completed_lane_count"] == 4
    assert decision["completed_lanes"] == coordinator.LANES
    assert decision["standard_stagger_offsets_minutes"] == {
        "lane_001": 0, "lane_002": 8, "lane_003": 16, "lane_004": 24,
    }

    master = rows(coordinator.OUTPUT / "broad_state_4x1000_parallel_live_scout_master_results.csv")
    assert len(master) == 4000
    assert len({row["scout_target_id"] for row in master}) == 4000
    assert {row["lane_id"] for row in master} == set(coordinator.LANES)
    assert {row["shard_id"] for row in master} == set(coordinator.SHARDS)

    intervals: list[tuple[datetime, datetime]] = []
    lane_union: set[str] = set()
    for number, lane_id in enumerate(coordinator.LANES, start=1):
        root = coordinator.lane_root(number)
        checkpoint = json.loads((root / f"lane_{number:03d}_checkpoint.json").read_text())
        assert checkpoint["shard_status"] == "completed"
        assert checkpoint["completed_outcome_count"] == 1000
        assert checkpoint["lane_id"] == lane_id
        assert checkpoint["shard_id"] == coordinator.SHARDS[number - 1]
        assert checkpoint["scheduled_start_offset_minutes"] == (number - 1) * 8
        lane_results = rows(root / f"lane_{number:03d}_results.csv")
        assert len(lane_results) == 1000
        assert {row["lane_id"] for row in lane_results} == {lane_id}
        lane_union.update(row["scout_target_id"] for row in lane_results)
        resume = json.loads((root / f"lane_{number:03d}_resume_state.json").read_text())
        assert resume["resume_required"] is False
        assert resume["completed_lane_must_not_be_rerun"] is True
        intervals.append((datetime.fromisoformat(checkpoint["actual_started_at"]), datetime.fromisoformat(checkpoint["completed_at"])))
    assert lane_union == {row["scout_target_id"] for row in master}
    assert max(start for start, _ in intervals) < min(end for _, end in intervals)

    parseable = [row for row in master if row["parse_status"] == "parseable"]
    failed = [row for row in master if row["parse_status"] != "parseable"]
    assert len(parseable) == 3997 == decision["new_scout_covered_municipalities"]
    assert len(failed) == 3 == decision["failed_or_stopped_parses"]
    assert decision["cumulative_scout_covered_municipalities"] == 6919

    candidates = rows(coordinator.OUTPUT / "broad_state_4x1000_parallel_live_scout_candidates.csv")
    deduped = rows(coordinator.OUTPUT / "broad_state_4x1000_parallel_live_scout_deduped_candidates.csv")
    assert len(candidates) == decision["candidate_count"] == 7014
    assert len(deduped) == decision["deduped_candidate_count"] == 6437
    assert decision["preserved_prior_candidate_count"] == 1205
    assert decision["combined_future_review_eligible_candidate_count"] == 7642
    assert len(rows(worker.PRIOR_REVIEW)) == 1205
    assert all(row["verification_status"] == "not_verified" for row in candidates)
    assert all(row["download_status"] == "not_downloaded" for row in candidates)
    assert all(row["extraction_status"] == "not_extracted" for row in candidates)
    assert all(row["rating_status"] == "not_rated" for row in candidates)
    assert all(row["ingestion_status"] == "not_ingested" for row in candidates)
    assert all(row["codification_status"] == "not_codified" for row in candidates)
    assert all(row["causal_status"] == "not_causal_evidence" for row in candidates)
    assert all(row["global_analysis_readiness"] == "false" for row in candidates)

    audit = data("broad_state_4x1000_parallel_live_interrupted_attempt_audit.json")
    assert audit["terminal_outcome_count"] == 69
    assert audit["complete_shard_reusable"] is False
    assert audit["excluded_from_candidate_accounting"] is True
    assert audit["excluded_from_coverage_accounting"] is True
    invariants = data("broad_state_4x1000_parallel_live_scout_invariant_checks.json")
    assert all(value is True for value in invariants.values())
    for forbidden in ("raw_prompt", "raw_response"):
        assert not [p for p in coordinator.OUTPUT.rglob("*") if forbidden in p.name.casefold()]

    dashboard_spec = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard_data.py")
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    recognized, live = dashboard.broad_state_4x1000_live_scout_status()
    assert recognized and live["completed_lane_count"] == 4
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    parallel = json.loads((ROOT / "docs/dashboard/data/parallel_scout_status.json").read_text())
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["totals"]["scout_covered_municipalities"] == 6919
    assert phase["current_scout_covered"] == 6919
    assert phase["global_analysis_readiness"] is False
    assert (
        "combined candidate review" in phase["current_phase"].casefold()
        or "verification" in phase["current_phase"].casefold()
        or "candidate review complete" in phase["current_phase"].casefold()
    )
    assert parallel["completed_live_shard_count"] == 4
    assert "staggered" in parallel["current_parallel_mode"]
    print("Broad state 4x1000 staggered parallel live scout tests passed")


if __name__ == "__main__":
    main()
