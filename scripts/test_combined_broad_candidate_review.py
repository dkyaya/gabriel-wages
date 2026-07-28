#!/usr/bin/env python3
"""Invariant tests for metadata-only combined broad candidate review."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28"
SCRIPT = ROOT / "scripts/run_combined_broad_candidate_review.py"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    decision = read_json(OUTPUT / "combined_broad_candidate_review_decision.json")
    results = read_csv(OUTPUT / "combined_broad_candidate_review_results.csv")
    universe = read_csv(OUTPUT / "combined_broad_candidate_review_universe.csv")
    locked_path = OUTPUT / "combined_broad_candidate_review_locked_queue.csv"
    locked = read_csv(locked_path)
    lock = read_json(OUTPUT / "combined_broad_candidate_review_lock.json")

    assert decision["decision"] == "combined_broad_candidate_review_completed_source_review_ready"
    assert len(results) == len(universe) == len(locked) == 9065
    assert decision["broad_review_subtotal"] == 7642
    assert decision["supplementary_verification_row_count"] == 1423
    assert sha256(locked_path) == lock["queue_sha256"]
    assert lock["locked_rows"] == 9065
    assert len({row["combined_review_id"] for row in results}) == 9065

    lane_union: list[dict[str, str]] = []
    for number, expected in ((1, 2267), (2, 2266), (3, 2266), (4, 2266)):
        lane = f"review_lane_{number:03d}"
        queue_path = OUTPUT / f"combined_broad_candidate_review_lane_{number:03d}_locked_queue.csv"
        queue = read_csv(queue_path)
        lane_lock = read_json(OUTPUT / f"combined_broad_candidate_review_lane_{number:03d}_lock.json")
        lane_results = read_csv(OUTPUT / f"lane_{number:03d}_candidate_review_results.csv")
        checkpoint = read_json(OUTPUT / f"lane_{number:03d}_checkpoint.json")
        assert len(queue) == len(lane_results) == expected
        assert sha256(queue_path) == lane_lock["queue_sha256"]
        assert checkpoint["status"] == "completed"
        assert checkpoint["remaining_rows"] == 0
        assert all(row["review_lane_id"] == lane for row in lane_results)
        lane_union.extend(lane_results)
    assert {row["combined_review_id"] for row in lane_union} == {
        row["combined_review_id"] for row in results
    }

    controlled = {
        "source_review_ready_high", "source_review_ready_medium", "source_review_ready_low",
        "repair_or_needs_review", "defer_unreachable_or_unavailable",
        "defer_blocked_or_timeout", "deprioritize_for_now",
        "exclude_duplicate_or_prior_seen", "exclude_out_of_scope",
        "exclude_wrong_employer_or_source", "exclude_insufficient_locator",
        "exclude_unusable_metadata", "exclude_not_reachable",
    }
    assert {row["candidate_review_status"] for row in results} <= controlled
    assert Counter(row["candidate_review_status"] for row in results) == Counter(
        decision["candidate_review_status_counts"]
    )
    for row in results:
        assert row["verification_status_preserved"] == "true"
        assert row["download_status"] == "not_downloaded"
        assert row["source_review_status"] == "not_source_reviewed"
        assert row["extraction_status"] == "not_extracted"
        assert row["rating_status"] == "not_rated"
        assert row["ingestion_status"] == "not_ingested"
        assert row["codification_status"] == "not_codified"
        assert row["causal_status"] == "not_causal_evidence"
        assert row["global_analysis_readiness"] == "false"

    ready_path = OUTPUT / "combined_broad_candidate_review_locked_source_review_queue.csv"
    ready = read_csv(ready_path)
    ready_lock = read_json(OUTPUT / "combined_broad_candidate_review_locked_source_review_queue_lock.json")
    assert len(ready) == decision["source_review_ready_count"] == 5589
    assert sha256(ready_path) == ready_lock["queue_sha256"]
    assert Counter(row["source_review_priority"] for row in ready) == {
        "high": 2884, "medium": 2562, "low": 143
    }
    assert {row["verification_status"] for row in ready} <= {
        "verified_reachable", "verified_reachable_redirected", "reused_prior_verified"
    }
    assert not any(row["verification_status"] in {
        "unavailable_404_410", "unavailable_other_status", "blocked_transport",
        "timeout", "invalid_locator", "unsupported_locator"
    } for row in ready)

    assert decision["repair_or_needs_review_count"] == 2
    assert decision["deferred_unreachable_or_unavailable_count"] == 2927
    assert decision["deferred_blocked_or_timeout_count"] == 176
    assert decision["deprioritized_count"] == 342
    assert decision["excluded_count"] == 29
    assert decision["url_opens"] == decision["verification_runs"] == 0
    assert decision["downloads"] == decision["source_review_runs"] == 0
    assert decision["source_document_content_accesses"] == 0
    assert decision["extraction_runs"] == decision["rating_runs"] == 0
    assert decision["ingestion_runs"] == decision["codification_runs"] == 0
    assert decision["global_analysis_readiness"] is False

    source = SCRIPT.read_text(encoding="utf-8").casefold()
    assert "import requests" not in source and "import httpx" not in source
    assert "urllib.request" not in source and "urlopen" not in source

    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    assert map_source.count('key: "total_scout_coverage_count"') == 1
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    assert phase["current_scout_covered"] == 6919
    assert phase["current_candidate_queue_rows"] == 13041
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["global_analysis_readiness"] is False
    assert phase["candidate_review_universe_size"] == 9065
    assert phase["source_review_ready_count"] == 5589
    assert phase["source_review_ready_high_count"] == 2884
    assert phase["source_review_ready_medium_count"] == 2562
    assert phase["source_review_ready_low_count"] == 143
    assert "candidate review complete" in phase["current_phase"].casefold()
    assert "source-review/download" in phase["next_task"].casefold()
    assert "tier c memo supplement" not in phase["current_phase"].casefold()
    reports = read_json(ROOT / "docs/dashboard/data/reports_index.json")["reports"]
    current_reports = [report for report in reports if report["current"]]
    assert len(current_reports) == 1
    assert current_reports[0]["id"] == "combined-broad-candidate-review-2026-07-28"
    frontend = (ROOT / "docs/dashboard/src/components/ProjectHubSections.jsx").read_text(encoding="utf-8")
    assert "Combined broad candidate review complete" in frontend
    assert "Broad candidate locator verification</h2>" not in frontend
    assert "Run one combined candidate review" not in frontend
    assert "source_review_ready_high_count" in frontend and "map_data_date" in frontend

    prompt = (OUTPUT / "next_broad_source_review_download_prompt.md").read_text(encoding="utf-8").casefold()
    assert "dashboard update requirement" in prompt
    assert "global analysis readiness" in prompt
    assert "post-rating artifact completeness" in prompt
    assert "do not" in prompt and "wage gap" in prompt.replace("wage-gap", "wage gap") and "final causal" in prompt
    print("PASS: combined broad candidate-review invariants")


if __name__ == "__main__":
    main()
