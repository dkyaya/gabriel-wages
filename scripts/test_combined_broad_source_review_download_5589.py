#!/usr/bin/env python3
"""Invariant tests for the four-lane 5,589-row source-review/download wave."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
RUNNER = ROOT / "scripts/run_combined_broad_source_review_download_5589.py"
EXPECTED_LANES = {
    "source_review_lane_001": 1397,
    "source_review_lane_002": 1397,
    "source_review_lane_003": 1397,
    "source_review_lane_004": 1398,
}
RETAINED = {"retained_pdf", "retained_html", "retained_document_other"}
CONTROLLED = RETAINED | {
    "duplicate_file_hash", "duplicate_canonical_locator", "oversized_for_this_pass",
    "blocked_by_transport", "unavailable_on_get", "unsupported_content_type",
    "weak_or_needs_review", "generic_navigation_or_search_page",
    "wrong_employer_or_source_metadata_only", "invalid_locator", "download_error",
    "source_review_not_run",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    prior = read_json(INPUT / "combined_broad_candidate_review_decision.json")
    assert prior["decision"] == "combined_broad_candidate_review_completed_source_review_ready"
    input_queue = read_csv(INPUT / "combined_broad_candidate_review_locked_source_review_queue.csv")
    queue_path = OUTPUT / "combined_broad_source_review_download_5589_locked_queue.csv"
    queue = read_csv(queue_path)
    lock = read_json(OUTPUT / "combined_broad_source_review_download_5589_lock.json")
    assert len(input_queue) == len(queue) == lock["locked_rows"] == 5589
    assert sha256(queue_path) == lock["queue_sha256"]
    assert {row["combined_review_id"] for row in queue} == {
        row["combined_review_id"] for row in input_queue
    }
    assert {row["candidate_review_status"] for row in queue} <= {
        "source_review_ready_high", "source_review_ready_medium", "source_review_ready_low"
    }

    lane_union = []
    for lane, expected in EXPECTED_LANES.items():
        number = int(lane.rsplit("_", 1)[-1])
        lane_queue_path = OUTPUT / f"combined_broad_source_review_download_lane_{number:03d}_locked_queue.csv"
        lane_queue = read_csv(lane_queue_path)
        lane_lock = read_json(OUTPUT / f"combined_broad_source_review_download_lane_{number:03d}_lock.json")
        lane_dir = OUTPUT / "lanes" / lane
        lane_results = read_csv(lane_dir / f"lane_{number:03d}_source_review_download_results.csv")
        checkpoint = read_json(lane_dir / f"lane_{number:03d}_checkpoint.json")
        resume = read_json(lane_dir / f"lane_{number:03d}_resume_state.json")
        assert len(lane_queue) == len(lane_results) == expected
        assert sha256(lane_queue_path) == lane_lock["queue_sha256"]
        assert checkpoint["status"] == resume["status"] == "completed"
        assert checkpoint["remaining_rows"] == resume["remaining_rows"] == 0
        assert all(row["lane_id"] == lane for row in lane_results)
        lane_union.extend(lane_results)
    assert len(lane_union) == 5589
    assert {row["source_review_download_id"] for row in lane_union} == {
        row["source_review_download_id"] for row in queue
    }

    decision = read_json(OUTPUT / "combined_broad_source_review_download_5589_decision.json")
    results = read_csv(OUTPUT / "combined_broad_source_review_download_5589_results.csv")
    retained = read_csv(OUTPUT / "combined_broad_source_review_download_5589_retained_sources.csv")
    excluded = read_csv(OUTPUT / "combined_broad_source_review_download_5589_excluded_or_deferred.csv")
    manifest = read_csv(OUTPUT / "combined_broad_source_review_download_5589_retained_sources_manifest.csv")
    assert decision["decision"] == "combined_broad_source_review_download_5589_completed_pdf_readiness_ready"
    assert decision["completed_lane_count"] == 4 and decision["all_lanes_completed"] is True
    assert len(results) == 5589
    assert len(retained) + len(excluded) == len(results)
    assert len(manifest) == len(retained) == decision["retained_source_count"]
    assert Counter(row["source_review_download_status"] for row in results) == Counter(decision["status_counts"])
    assert {row["source_review_download_status"] for row in results} <= CONTROLLED

    retained_root = (OUTPUT / "retained_sources").resolve()
    hashes = set()
    for row in retained:
        assert row["source_review_download_status"] in RETAINED
        path = (ROOT / row["retained_file_path"]).resolve()
        assert path.is_relative_to(retained_root) and path.is_file()
        assert path.stat().st_size == int(row["retained_file_size_bytes"])
        assert sha256(path) == row["retained_file_sha256"]
        assert row["retained_file_sha256"] not in hashes
        hashes.add(row["retained_file_sha256"])
    assert all(row["source_review_download_status"] not in RETAINED for row in excluded)
    assert all(not row["retained_file_path"] for row in excluded)
    assert not list((OUTPUT / "retained_sources").rglob("*.part"))
    for row in results:
        assert row["verification_status_preserved"] == "true"
        assert row["extraction_status"] == "not_extracted"
        assert row["rating_status"] == "not_rated"
        assert row["ingestion_status"] == "not_ingested"
        assert row["codification_status"] == "not_codified"
        assert row["causal_status"] == "not_causal_evidence"
        assert row["global_analysis_readiness"] == "false"

    assert decision["candidate_review_reruns"] == decision["verification_reruns"] == 0
    assert decision["extraction_runs"] == decision["ocr_runs"] == decision["rendering_runs"] == 0
    assert decision["rating_model_api_runs"] == decision["ingestion_runs"] == decision["codification_runs"] == 0
    assert decision["dashboard_map_filter"] == "total_scout_coverage_only"
    assert decision["dashboard_scout_covered_municipalities"] == 6919
    assert decision["dashboard_candidate_rows"] == 13041
    assert decision["global_analysis_readiness"] is False

    source = RUNNER.read_text(encoding="utf-8").casefold()
    for forbidden in ("pypdf", "pdfplumber", "pymupdf", "ocrmypdf", "pytesseract", "gabriel.codify"):
        assert forbidden not in source
    assert "checkpoint_after_every_row" in source
    assert "max_file_bytes = 75 * 1024 * 1024" in source

    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    assert phase["combined_source_review_download_available"] is True
    assert phase["current_scout_covered"] == 6919
    assert phase["current_candidate_queue_rows"] == 13041
    assert phase["source_review_download_attempted_count"] == 5589
    assert phase["source_review_download_retained_count"] == len(retained)
    assert (
        "source review/download complete" in phase["current_phase"].casefold()
        or "pdf/text-layer readiness complete" in phase["current_phase"].casefold()
    )
    assert (
        "pdf/text-layer readiness" in phase["next_phase"].casefold()
        or "text extraction" in phase["next_phase"].casefold()
    )
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["global_analysis_readiness"] is False
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    assert map_source.count('key: "total_scout_coverage_count"') == 1
    reports = read_json(ROOT / "docs/dashboard/data/reports_index.json")["reports"]
    current = [report for report in reports if report["current"]]
    assert len(current) == 1 and current[0]["id"] in {
        "combined-broad-source-review-download-5589-2026-07-28",
        "combined-broad-pdf-text-readiness-4961-2026-07-28",
    }
    frontend = (ROOT / "docs/dashboard/src/components/ProjectHubSections.jsx").read_text(encoding="utf-8")
    assert "Combined broad source review/download complete" in frontend
    assert "source_review_download_retained_count" in frontend

    prompt = (OUTPUT / "next_combined_broad_pdf_text_layer_readiness_prompt.md").read_text(encoding="utf-8").casefold()
    assert "dashboard update requirement" in prompt
    assert "post-rating artifact-completeness" in prompt
    assert "do not access urls" in prompt and "do not ocr" in prompt
    assert "global analysis readiness false" in prompt
    print("PASS: combined broad source-review/download 5,589 invariants")


if __name__ == "__main__":
    main()
