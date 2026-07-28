#!/usr/bin/env python3
"""Fail-closed invariants for the 4,961-source readiness review."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
INPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_pdf_text_layer_readiness_4961"
LANES = {
    "readiness_lane_001": 1240,
    "readiness_lane_002": 1240,
    "readiness_lane_003": 1240,
    "readiness_lane_004": 1241,
}
CONTROLLED = {
    "parse_text_layer_later", "html_text_later", "other_document_text_later",
    "ocr_later_or_defer", "oversized_for_text_pass", "corrupt_or_unreadable",
    "encrypted_or_locked", "shell_or_navigation_only",
    "unsupported_for_text_extraction", "needs_review", "readiness_error",
}
READY = {"parse_text_layer_later", "html_text_later", "other_document_text_later"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    required = {
        f"{PREFIX}_decision.json", f"{PREFIX}_summary.md",
        f"{PREFIX}_preflight_report.md", f"{PREFIX}_preflight_checks.json",
        f"{PREFIX}_file_integrity_preflight.csv", f"{PREFIX}_file_integrity_preflight_summary.json",
        f"{PREFIX}_locked_queue.csv", f"{PREFIX}_locked_queue_summary.json", f"{PREFIX}_lock.json",
        f"{PREFIX}_results.csv", f"{PREFIX}_results_summary.json",
        f"{PREFIX}_pdf_results.csv", f"{PREFIX}_html_results.csv", f"{PREFIX}_other_document_results.csv",
        f"{PREFIX}_file_integrity.csv", f"{PREFIX}_file_integrity_summary.json",
        f"{PREFIX}_hash_reconciliation.json", f"{PREFIX}_lane_status_matrix.csv",
        f"{PREFIX}_parallel_execution_report.md", f"{PREFIX}_resumability_report.md",
        f"{PREFIX}_dashboard_update_summary.md", f"{PREFIX}_dashboard_update_summary.json",
        f"{PREFIX}_text_extraction_planning_note.md", f"{PREFIX}_ocr_future_pass_note.md",
        f"{PREFIX}_validation_2026-07-28.md", f"{PREFIX}_invariant_checks.json",
        "next_combined_broad_text_extraction_prompt.md", "next_task.md",
    }
    required.update(f"{PREFIX}_{stem}_summary.{extension}" for stem in ("state", "region", "municipality", "source_family") for extension in ("csv", "json"))
    required.update(f"{PREFIX}_{status if status != 'readiness_error' else 'readiness_errors'}.csv" for status in CONTROLLED)
    required.update(f"combined_broad_pdf_text_layer_readiness_lane_{number}_{suffix}" for number in ("001", "002", "003", "004") for suffix in ("locked_queue.csv", "locked_queue_summary.json", "lock.json"))
    assert not [name for name in sorted(required) if not (OUT / name).is_file()]
    decision = load_json(OUT / f"{PREFIX}_decision.json")
    summary = load_json(OUT / f"{PREFIX}_results_summary.json")
    lock = load_json(OUT / f"{PREFIX}_lock.json")
    invariants = load_json(OUT / f"{PREFIX}_invariant_checks.json")
    queue = load_csv(OUT / f"{PREFIX}_locked_queue.csv")
    results = load_csv(OUT / f"{PREFIX}_results.csv")
    input_rows = load_csv(INPUT / "combined_broad_source_review_download_5589_retained_sources.csv")
    input_hashes = load_csv(INPUT / "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv")

    assert decision["decision"] == "combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready"
    assert len(queue) == len(results) == len(input_rows) == len(input_hashes) == 4961
    assert lock["lane_counts"] == LANES
    assert Counter(row["lane_id"] for row in queue) == LANES
    queue_ids = {row["source_review_download_id"] for row in queue}
    result_ids = {row["source_review_download_id"] for row in results}
    input_ids = {row["source_review_download_id"] for row in input_rows}
    hash_ids = {row["source_review_download_id"] for row in input_hashes}
    assert len(queue_ids) == 4961 and queue_ids == result_ids == input_ids == hash_ids
    lane_union = set()
    for lane_id, expected in LANES.items():
        number = lane_id[-3:]
        lane_queue = load_csv(OUT / f"combined_broad_pdf_text_layer_readiness_lane_{number}_locked_queue.csv")
        lane_results = load_csv(OUT / "lanes" / lane_id / f"lane_{number}_readiness_results.csv")
        lane_summary = load_json(OUT / "lanes" / lane_id / f"lane_{number}_readiness_results_summary.json")
        checkpoint = load_json(OUT / "lanes" / lane_id / f"lane_{number}_checkpoint.json")
        resume = load_json(OUT / "lanes" / lane_id / f"lane_{number}_resume_state.json")
        assert len(lane_queue) == len(lane_results) == expected
        assert lane_summary["status"] == checkpoint["status"] == resume["status"] == "completed"
        assert checkpoint["checkpoint_after_every_source"] is True
        assert lane_summary["shared_output_mutations"] == 0
        lane_ids = {row["source_review_download_id"] for row in lane_queue}
        assert not (lane_union & lane_ids)
        lane_union.update(lane_ids)
    assert lane_union == queue_ids

    counts = Counter(row["readiness_status"] for row in results)
    assert set(counts).issubset(CONTROLLED) and sum(counts.values()) == 4961
    assert summary["readiness_status_counts"] == dict(sorted(counts.items()))
    assert summary["pdf_reviewed_count"] == 3980
    assert summary["html_reviewed_count"] == 941
    assert summary["other_document_reviewed_count"] == 40
    assert all(row["file_integrity_status"] == "integrity_pass" for row in results)
    assert all(row["extraction_status"] == "not_extracted" for row in results)
    assert all(row["rating_status"] == "not_rated" for row in results)
    assert all(row["ingestion_status"] == "not_ingested" for row in results)
    assert all(row["codification_status"] == "not_codified" for row in results)
    assert all(row["causal_status"] == "not_causal_evidence" for row in results)
    assert all(row["global_analysis_readiness"] == "false" for row in results)
    for status in CONTROLLED:
        suffix = "readiness_errors" if status == "readiness_error" else status
        manifest = load_csv(OUT / f"{PREFIX}_{suffix}.csv")
        assert len(manifest) == counts[status]
        assert all(row["readiness_status"] == status for row in manifest)
        if status not in READY:
            assert not ({row["source_review_download_id"] for row in manifest} & {
                row["source_review_download_id"]
                for ready_status in READY
                for row in load_csv(OUT / f"{PREFIX}_{ready_status}.csv")
            })

    assert sha256(OUT / f"{PREFIX}_locked_queue.csv") == lock["queue_sha256"]
    assert invariants["all_invariants_passed"] is True
    assert invariants["dashboard_map_filter"] == "total_scout_coverage_only"
    assert decision["global_analysis_readiness"] is False
    assert all(summary[field] == 0 for field in (
        "source_review_download_reruns", "redownloads", "text_extraction_runs",
        "table_extraction_runs", "span_extraction_runs", "ocr_runs",
        "pdf_render_runs", "rating_model_api_runs", "ingestion_runs",
        "codification_runs", "statistical_analysis_runs",
    ))

    phase = load_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    source = load_json(ROOT / "docs/dashboard/data/source_review_status_summary.json")
    state = load_json(ROOT / "docs/dashboard/data/state_summary.json")
    assert phase["current_phase_code"] == decision["decision"]
    assert phase["pdf_text_readiness_queue_size"] == 4961
    assert phase["pdf_text_readiness_reviewed_count"] == 4961
    assert phase["pdf_text_readiness_extraction_ready_count"] == summary["extraction_ready_count"]
    assert source["source_review_phase"] == "combined_broad_4961_readiness_parallel_lanes_completed"
    assert source["pdf_text_readiness_reviewed_count"] == 4961
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metric_definition"]["map_color_metric"] == "total_scout_coverage_count"
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["global_analysis_readiness"] is False
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    map_ui = (ROOT / "docs/dashboard/src/components/NationalMap.jsx").read_text(encoding="utf-8")
    assert map_source.count('key: "') == 1
    assert 'key: "total_scout_coverage_count"' in map_source
    assert "<select" not in map_ui and "metric-select" not in map_ui
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    assert "Current operation:" in app and "Readiness reviewed" in app
    assert "current operation is bounded locator verification" not in app

    prompt = (OUT / "next_combined_broad_text_extraction_prompt.md").read_text(encoding="utf-8")
    for boundary in ("T+0/T+8/T+16/T+24", "global analysis readiness false", "map"):
        assert boundary.casefold() in prompt.casefold()
    assert "Before closing any future rating task" in prompt
    runner = (ROOT / "scripts/run_combined_broad_pdf_text_layer_readiness_4961.py").read_text(encoding="utf-8").casefold()
    for forbidden in ("requests.", "httpx", "curl ", "tesseract", "pdf2image", "gabriel.codify", "openai"):
        assert forbidden not in runner
    completed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/run_combined_broad_pdf_text_layer_readiness_4961.py"), "--validate"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in completed.stdout
    print("combined broad PDF/text-layer readiness 4961 tests passed")


if __name__ == "__main__":
    main()
