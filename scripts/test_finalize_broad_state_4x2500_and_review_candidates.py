#!/usr/bin/env python3
"""Independent fail-closed checks for 4x2500 finalization and review outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
FINAL = BASE / "BROAD-STATE-4X2500-LIVE-SCOUT-FINALIZED-2026-07-30"
REVIEW = BASE / "BROAD-STATE-4X2500-CANDIDATE-REVIEW-2026-07-30"
EXPECTED_DECISION = "broad_state_4x2500_live_scout_finalized_candidate_review_completed_verification_ready"
READY = {
    "high_priority_verification_ready",
    "medium_priority_verification_ready",
    "low_priority_verification_ready",
}


def data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    final = data(FINAL / "finalized_live_scout_summary.json")
    lane = data(FINAL / "lane_reconciliation_report.json")
    dedupe = data(FINAL / "candidate_deduplication_summary.json")
    review = data(REVIEW / "candidate_review_summary.json")
    buckets = data(REVIEW / "candidate_review_bucket_counts.json")
    queue_manifest = data(REVIEW / "verification_ready_queue_manifest.json")
    decision = data(REVIEW / "final_decision.json")
    validation = data(REVIEW / "candidate_review_validation.json")
    phase = data(ROOT / "docs/dashboard/data/project_phase_summary.json")
    state = data(ROOT / "docs/dashboard/data/state_summary.json")
    readiness = data(ROOT / "docs/dashboard/data/analysis_readiness.json")
    reports = data(ROOT / "docs/dashboard/data/reports_index.json")
    candidates = rows(FINAL / "finalized_candidate_rows.csv")
    reviewed = rows(REVIEW / "candidate_review_results.csv")
    ready = rows(REVIEW / "verification_ready_queue.csv")

    assert decision["decision"] == EXPECTED_DECISION
    assert validation["all_validation_gates_passed"] is True
    assert final["accepted_outcomes"] == 10_000
    assert final["parseable_outcomes"] == 9_968
    assert final["failed_or_unparseable_outcomes"] == 32
    assert final["raw_candidate_rows"] == 9_977
    assert final["deduped_candidate_rows"] == len(candidates) == 9_072
    assert dedupe["raw_candidate_rows"] - dedupe["total_excluded"] == len(candidates)
    assert lane["workers_running"] is False
    assert set(lane["lanes"]) == {f"scout_lane_{n:03d}" for n in range(1, 5)}
    assert sum(item["accepted_outcomes"] for item in lane["lanes"].values()) == 10_000
    assert sum(item["raw_candidate_rows_from_durable_files"] for item in lane["lanes"].values()) == 9_977
    assert all(item["terminal_endpoint_reached"] for item in lane["lanes"].values())
    assert all("source_family_hints" in item for item in lane["lanes"].values())

    candidate_ids = {row["scout_candidate_id"] for row in candidates}
    reviewed_ids = [row["candidate_id"] for row in reviewed]
    assert len(reviewed) == len(candidates) == len(set(reviewed_ids))
    assert set(reviewed_ids) == candidate_ids
    assert sum(buckets["bucket_counts"].values()) == len(reviewed)
    assert all(row["primary_bucket"] in READY for row in ready)
    assert {row["candidate_id"] for row in ready} <= candidate_ids
    assert queue_manifest["queue_row_count"] == review["verification_ready_queue_count"] == len(ready)
    assert sum(queue_manifest["priority_counts"].values()) == len(ready)
    required = queue_manifest["required_fields"]
    assert all(all(row.get(field, "").strip() for field in required) for row in ready)
    assert all(row["verification_status"] == "not_verified" for row in ready)
    assert all(row["download_status"] == "not_downloaded" for row in ready)
    assert all(row["extraction_status"] == "not_extracted" for row in ready)
    assert all(row["rating_status"] == "not_rated" for row in ready)
    assert all(row["ingestion_status"] == "not_ingested" for row in ready)
    assert all(row["global_analysis_readiness"] == "false" for row in ready)
    assert review["dashboard_map_filter"] == "total_scout_coverage_only"
    assert review["global_analysis_readiness"] is False
    assert phase["data_vintage"] == "2026-07-30"
    assert phase["broad_state_4x2500_candidate_review_available"] is True
    assert phase["broad_state_4x2500_verification_ready_queue_count"] == len(ready)
    assert phase["current_scout_covered"] == 16_887
    assert phase["global_collection_readiness"] == "pass"
    assert phase["global_mechanism_analysis_readiness"] == "partial_pass"
    assert phase["global_quantitative_evidence_readiness"] == "partial_pass"
    assert phase["global_wage_gap_analysis_readiness"] == "blocked_pending_normalization"
    assert phase["global_causal_analysis_readiness"] == "blocked_pending_matched_structure"
    assert phase["overall_global_analysis_readiness"] == "partial_pass"
    assert phase["global_analysis_readiness"] is False
    assert state["totals"]["scout_covered_municipalities"] == 16_887
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metadata"]["broad_state_4x2500_live_parseable_municipalities_added_to_map"] == 9_968
    assert readiness["source_discovery_readiness"]["municipalities_scout_covered"] == 16_887
    assert reports["reports"][0]["id"] == "broad-state-4x2500-candidate-review-2026-07-30"
    for key in (
        "urls_opened", "network_requests", "documents_downloaded", "source_documents_inspected",
        "text_extractions", "rating_runs", "ingestion_runs", "codification_runs",
        "wage_gap_calculations", "regressions", "final_causal_claims",
    ):
        assert review[key] == 0
    print("Broad state 4x2500 finalization and candidate-review tests passed")


if __name__ == "__main__":
    main()
