#!/usr/bin/env python3
"""Regression tests for the broad 4-lane candidate verification run."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-PARALLEL-LONG-RUN-2026-07-28"
SCRIPT = ROOT / "scripts/run_broad_candidate_verification_4x3000.py"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("broad_verify", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


async def probe_smoke(module) -> None:
    request_methods = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_methods.append(request.method)
        return httpx.Response(200, headers={"content-type": "application/pdf", "content-length": "123"}, request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, follow_redirects=True) as client:
        outcome = await module.probe(client, {
            "source_locator_or_url": "https://example.gov/pay-plan.pdf",
            "canonical_locator_before_verification": "https://example.gov/pay-plan.pdf",
        })
    assert outcome["verification_status"] == "verified_reachable"
    assert outcome["content_type_header"] == "application/pdf"
    assert request_methods == ["HEAD"]


def main() -> None:
    module = load_module()
    lock = read_json(OUTPUT / "broad_candidate_verification_4x3000_lock.json")
    summary = read_json(OUTPUT / "broad_candidate_verification_4x3000_locked_queue_summary.json")
    master_path = OUTPUT / "broad_candidate_verification_4x3000_locked_queue.csv"
    master = read_csv(master_path)
    assert len(master) == summary["locked_queue_rows"] == lock["queue_rows"]
    assert len(master) < 12_000
    assert summary["largest_defensible_queue_locked"] is True
    assert sha256(master_path) == lock["queue_sha256"]
    assert all(row["verification_status"] == "verification_not_run" for row in master)
    assert all(row["download_status"] == "not_downloaded" for row in master)
    assert all(row["source_review_status"] == "not_source_reviewed" for row in master)
    assert all(row["extraction_status"] == "not_extracted" for row in master)
    assert all(row["rating_status"] == "not_rated" for row in master)
    assert all(row["ingestion_status"] == "not_ingested" for row in master)
    assert all(row["codification_status"] == "not_codified" for row in master)
    assert all(row["causal_status"] == "not_causal_evidence" for row in master)
    assert all(row["global_analysis_readiness"] == "false" for row in master)
    union = []
    for number in range(1, 5):
        lane = f"verify_lane_{number:03d}"
        path = OUTPUT / f"broad_candidate_verification_lane_{number:03d}_locked_queue.csv"
        rows = read_csv(path)
        assert len(rows) == lock["lane_counts"][lane] <= 3_000
        assert sha256(path) == lock["lane_queue_sha256"][lane]
        assert all(row["lane_id"] == lane for row in rows)
        union.extend(rows)
    assert {row["verification_row_id"] for row in union} == {row["verification_row_id"] for row in master}
    assert len({row["canonical_locator_before_verification"] for row in master}) == len(master)
    universe = read_json(OUTPUT / "broad_candidate_verification_4x3000_universe_summary.json")
    assert universe["input_candidate_rows"] == 11_116
    assert universe["excluded_rows"] + universe["eligible_unique_locator_rows"] == 11_116
    assert universe["candidate_review_performed"] is False
    checks = read_json(OUTPUT / "broad_candidate_verification_4x3000_preflight_checks.json")
    assert checks["head_requests_only"] is True
    assert checks["get_fallback_enabled"] is False
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'client.stream("HEAD"' in source
    assert 'client.stream("GET"' not in source
    assert "response.aread" not in source
    assert "response.content" not in source
    asyncio.run(probe_smoke(module))
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    assert map_source.count('key: "total_scout_coverage_count"') == 1
    assert "verification" not in map_source.casefold()
    decision_path = OUTPUT / "broad_candidate_verification_4x3000_decision.json"
    if decision_path.is_file():
        decision = read_json(decision_path)
        results = read_csv(OUTPUT / "broad_candidate_verification_4x3000_results.csv")
        assert len(results) == decision["completed_result_rows"]
        assert decision["candidate_review_runs"] == 0
        assert decision["downloads"] == 0
        assert decision["source_review_runs"] == 0
        assert decision["source_document_content_accesses"] == 0
        assert decision["global_analysis_readiness"] is False
        assert decision["completed_lane_count"] == 3
        assert decision["completed_result_rows"] == 6430
        assert decision["decision"] == "broad_candidate_verification_4x3000_partial_lanes_completed_resume_ready"
        assert all(row["global_analysis_readiness"] == "false" for row in results)
        assert not any(row["lane_id"] == "verify_lane_004" for row in results)
        audit = read_json(OUTPUT / "broad_candidate_verification_4x3000_lane_004_invalid_transport_audit.json")
        assert audit["invalid_attempt_rows"] == 2144
        assert audit["counted_in_merged_verification"] is False
        assert audit["counted_in_dashboard_verification"] is False
        assert audit["network_permission_escalated"] is False
        phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
        assert "verification" in phase["current_phase"].casefold()
        assert phase["global_analysis_readiness"] is False
        assert phase["current_scout_covered"] == 6919
        assert phase["current_candidate_queue_rows"] == 13041
        assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
        assert phase["verification_all_lanes_completed"] is False
        assert phase["verification_completed_lane_count"] == 3
        assert phase["verification_remaining_count"] == 2144
        assert "tier c memo supplement" not in phase["current_phase"].casefold()
    print("PASS: broad candidate verification 4x3000 invariants")


if __name__ == "__main__":
    main()
