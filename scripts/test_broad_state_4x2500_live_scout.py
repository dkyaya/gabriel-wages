#!/usr/bin/env python3
"""Fail-closed checks for the broad-state 4 x 2,500 live scout."""

from __future__ import annotations

import ast
import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_broad_state_4x2500_live_scout.py"
SPEC = importlib.util.spec_from_file_location("live_4x2500", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_locks() -> None:
    locks = mod.validate_locks()
    assert locks["master_count"] == 10_000
    assert locks["shard_counts"] == {f"broad_4x2500_shard_{n:03d}": 2_500 for n in range(1, 5)}
    assert locks["unique_target_ids"] == locks["unique_municipality_ids"] == 10_000
    assert len(locks["source_family_query_counts"]) == 12
    assert locks["all_live_status_not_run"] and locks["all_prior_covered_excluded"]


def test_worker_contract() -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert {"validate_locks", "prepare", "run_lane", "finalize", "candidate_rows"} <= functions
    text = RUNNER.read_text(encoding="utf-8")
    assert "time.sleep(pacing.planned_sleep())" in text
    assert "atomic_json(checkpoint_file, checkpoint)" in text
    assert "two_consecutive_transport_failures_after_bounded_retries" in text
    assert "candidate_review_performed\": False" in text
    assert "global_analysis_readiness\": False" in text


def test_generated_outputs_if_present() -> None:
    decision_path = mod.OUTPUT / "broad_state_4x2500_live_scout_decision.json"
    if not decision_path.is_file():
        return
    decision = data(decision_path)
    assert decision["decision"] in {mod.DECISION_COMPLETE, mod.DECISION_PARTIAL}
    assert decision["candidate_review_performed"] is False
    assert decision["verification_performed"] is False
    assert decision["global_analysis_readiness"] is False
    assert decision["dashboard_map_filter"] == "total_scout_coverage_only"
    result_rows = rows(mod.OUTPUT / "broad_state_4x2500_live_scout_results.csv")
    complete_lanes = decision["completed_lane_count"]
    assert len(result_rows) == complete_lanes * 2_500
    assert len({row["scout_target_id"] for row in result_rows}) == len(result_rows)
    parseable = sum(row["parse_status"] == "parseable" for row in result_rows)
    coverage = data(mod.OUTPUT / "broad_state_4x2500_live_scout_municipality_coverage_summary.json")
    assert coverage["new_scout_covered_municipalities"] == parseable
    assert coverage["cumulative_scout_covered_municipalities_after_committed_outcomes"] == 6_919 + parseable
    for number in range(1, 5):
        resume = data(mod.lane_root(number) / f"lane_{number:03d}_resume_state.json")
        assert resume["resume_required"] is (mod.LANES[number - 1] not in decision["completed_lanes"])
    candidates = rows(mod.OUTPUT / "broad_state_4x2500_live_scout_candidate_review_queue.csv")
    assert all(row["verification_status"] == "not_verified" for row in candidates)
    assert all(row["download_status"] == "not_downloaded" for row in candidates)
    assert all(row["global_analysis_readiness"] == "false" for row in candidates)


def main() -> None:
    test_locks()
    test_worker_contract()
    test_generated_outputs_if_present()
    print("Broad state 4x2500 live scout tests passed")


if __name__ == "__main__":
    main()
