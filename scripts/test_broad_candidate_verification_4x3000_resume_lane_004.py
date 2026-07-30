#!/usr/bin/env python3
"""Invariant tests for the isolated lane-004 verification resume."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-PARALLEL-LONG-RUN-2026-07-28"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-RESUME-LANE-004-2026-07-28"
SCRIPT = ROOT / "scripts/run_broad_candidate_verification_4x3000_resume_lane_004.py"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prior_decision = read_json(PRIOR / "broad_candidate_verification_4x3000_decision.json")
    assert prior_decision["decision"] == "broad_candidate_verification_4x3000_partial_lanes_completed_resume_ready"
    for number, count in ((1, 2144), (2, 2143), (3, 2143)):
        lane_dir = PRIOR / "lanes" / f"verify_lane_{number:03d}"
        summary = read_json(lane_dir / f"lane_{number:03d}_verification_results_summary.json")
        checkpoint = read_json(lane_dir / f"lane_{number:03d}_checkpoint.json")
        assert summary["status"] == checkpoint["status"] == "completed"
        assert summary["completed_rows"] == checkpoint["completed_rows"] == count
        assert checkpoint["remaining_rows"] == 0

    queue_path = PRIOR / "broad_candidate_verification_lane_004_locked_queue.csv"
    queue = read_csv(queue_path)
    lock = read_json(PRIOR / "broad_candidate_verification_lane_004_lock.json")
    assert len(queue) == lock["locked_rows"] == 2144
    assert sha256(queue_path) == lock["queue_sha256"]
    assert all(row["lane_id"] == "verify_lane_004" for row in queue)
    assert all(row["verification_status"] == "verification_not_run" for row in queue)

    preflight = read_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_checks.json")
    assert preflight["preflight_passed"] is True
    assert preflight["network_permission_escalated_for_smoke"] is True
    assert preflight["network_smoke_http_responses"] >= 2
    assert preflight["head_requests_only"] is True
    assert preflight["get_fallback_enabled"] is False
    audit = read_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_prior_connecterror_audit.json")
    assert audit["prior_attempt_rows"] == 2144
    assert audit["quarantined"] is True
    assert audit["counted_as_completed"] is False
    assert audit["counted_in_dashboard"] is False

    source = SCRIPT.read_text(encoding="utf-8")
    assert "for number in (1, 2, 3):" in source
    assert "prior_lane_paths(number)[\"results\"]" in source
    assert "base.probe(client, row)" in source
    assert 'client.stream("GET"' not in source
    assert "candidate_review_runs\": 0" in source

    lane_results = read_csv(OUTPUT / "lane_004_verification_results.csv")
    lane_summary = read_json(OUTPUT / "lane_004_verification_results_summary.json")
    assert len(lane_results) == lane_summary["completed_rows"]
    assert all(row["lane_id"] == "verify_lane_004" for row in lane_results)
    assert all(row["download_status"] == "not_downloaded" for row in lane_results)
    assert all(row["source_review_status"] == "not_source_reviewed" for row in lane_results)
    assert all(row["extraction_status"] == "not_extracted" for row in lane_results)
    assert all(row["rating_status"] == "not_rated" for row in lane_results)
    assert all(row["ingestion_status"] == "not_ingested" for row in lane_results)
    assert all(row["codification_status"] == "not_codified" for row in lane_results)
    assert all(row["causal_status"] == "not_causal_evidence" for row in lane_results)
    assert all(row["global_analysis_readiness"] == "false" for row in lane_results)

    decision = read_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_decision.json")
    final_results = read_csv(OUTPUT / "broad_candidate_verification_4x3000_final_results.csv")
    assert decision["prior_connecterror_rows_counted"] == 0
    assert decision["candidate_review_runs"] == 0
    assert decision["downloads"] == 0
    assert decision["source_review_runs"] == 0
    assert decision["source_document_content_accesses"] == 0
    assert decision["global_analysis_readiness"] is False
    assert len(final_results) == 6430 + len(lane_results)
    assert len({row["verification_row_id"] for row in final_results}) == len(final_results)
    assert {row["lane_id"] for row in final_results} <= {
        "verify_lane_001", "verify_lane_002", "verify_lane_003", "verify_lane_004"
    }
    if decision["decision"] == "broad_candidate_verification_4x3000_resume_lane_004_completed_review_ready":
        assert len(lane_results) == 2144
        assert len(final_results) == decision["completed_result_rows"] == 8574
        assert decision["all_lanes_completed"] is True
        assert decision["completed_lane_count"] == 4

    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    assert map_source.count('key: "scout_coverage_rate"') == 1
    assert "verification" not in map_source.casefold()
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["current_scout_covered"] == 6919
    assert phase["current_candidate_queue_rows"] == 13041
    assert phase["global_analysis_readiness"] is False
    assert phase["verification_completed_count"] == len(final_results)
    if decision["all_lanes_completed"]:
        assert phase["verification_all_lanes_completed"] is True
        assert phase["verification_remaining_count"] == 0
        assert (
            "combined broad candidate review" in phase["next_task"].casefold()
            or "source-review/download" in phase["next_task"].casefold()
            or "pdf/text-layer readiness" in phase["next_task"].casefold()
            or "text extraction" in phase["next_task"].casefold()
        )
        assert "resume incomplete" not in phase["next_task"].casefold()
    assert "tier c memo supplement" not in phase["current_phase"].casefold()

    next_prompt = next(OUTPUT.glob("next_*prompt.md")).read_text(encoding="utf-8").casefold()
    assert "dashboard" in next_prompt
    assert "global analysis readiness false" in next_prompt
    assert "rating" in next_prompt and "artifact completeness" in next_prompt
    print("PASS: lane 004 resume and final merge invariants")


if __name__ == "__main__":
    main()
