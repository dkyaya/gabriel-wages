#!/usr/bin/env python3
"""Fail-closed invariants for the 4,051-source text-extraction task."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-TEXT-EXTRACTION-4051-PARALLEL-LANES-2026-07-28"
READY = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_text_extraction_4051"
LANES = {
    "extraction_lane_001": 1013,
    "extraction_lane_002": 1013,
    "extraction_lane_003": 1013,
    "extraction_lane_004": 1012,
}
APPROVED = {"parse_text_layer_later", "html_text_later", "other_document_text_later"}
EXCLUDED = {
    "ocr_later_or_defer", "oversized_for_text_pass", "encrypted_or_locked",
    "needs_review", "shell_or_navigation_only", "corrupt_or_unreadable",
    "unsupported_for_text_extraction", "readiness_error",
}
CONTROLLED = {
    "extracted_ok", "empty_or_too_short", "low_text_density",
    "suspected_bad_text_layer", "html_noisy_or_shell",
    "other_document_extraction_unsupported", "extraction_error",
    "skipped_not_in_queue",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    required = {
        f"{PREFIX}_decision.json", f"{PREFIX}_summary.md",
        f"{PREFIX}_preflight_report.md", f"{PREFIX}_preflight_checks.json",
        f"{PREFIX}_file_integrity_preflight.csv",
        f"{PREFIX}_file_integrity_preflight_summary.json",
        f"{PREFIX}_artifact_storage_preflight.json",
        f"{PREFIX}_locked_queue.csv", f"{PREFIX}_locked_queue_summary.json",
        f"{PREFIX}_lock.json", f"{PREFIX}_results.csv",
        f"{PREFIX}_results_summary.json", f"{PREFIX}_pdf_results.csv",
        f"{PREFIX}_html_results.csv", f"{PREFIX}_other_document_results.csv",
        f"{PREFIX}_extracted_ok.csv", f"{PREFIX}_extracted_ok_summary.json",
        f"{PREFIX}_extracted_text_manifest.csv",
        f"{PREFIX}_extracted_text_manifest_summary.json",
        f"{PREFIX}_extracted_text_hash_manifest.csv",
        f"{PREFIX}_extracted_text_hash_manifest_summary.json",
        f"{PREFIX}_no_tracked_text_artifacts_validation.json",
        f"{PREFIX}_quality_summary.json", f"{PREFIX}_lane_status_matrix.csv",
        f"{PREFIX}_parallel_execution_report.md", f"{PREFIX}_resumability_report.md",
        f"{PREFIX}_dashboard_update_summary.json",
        "dashboard_overview_metric_sync_after_text_extraction.json",
        "dashboard_stale_overview_guard_after_text_extraction.json",
        f"{PREFIX}_invariant_checks.json", f"{PREFIX}_validation_2026-07-28.md",
        "next_combined_broad_span_extraction_prompt.md", "next_task.md",
    }
    assert not [name for name in sorted(required) if not (OUT / name).is_file()]
    decision = load_json(OUT / f"{PREFIX}_decision.json")
    summary = load_json(OUT / f"{PREFIX}_results_summary.json")
    invariants = load_json(OUT / f"{PREFIX}_invariant_checks.json")
    queue = load_csv(OUT / f"{PREFIX}_locked_queue.csv")
    results = load_csv(OUT / f"{PREFIX}_results.csv")
    extracted_ok = load_csv(OUT / f"{PREFIX}_extracted_ok.csv")
    integrity = load_csv(OUT / f"{PREFIX}_file_integrity_preflight.csv")

    assert decision["decision"] == "combined_broad_text_extraction_4051_completed_span_extraction_ready"
    assert len(queue) == len(results) == len(integrity) == 4051
    assert Counter(row["lane_id"] for row in queue) == LANES
    queue_ids = {row["extraction_id"] for row in queue}
    result_ids = {row["extraction_id"] for row in results}
    assert len(queue_ids) == len(result_ids) == 4051 and queue_ids == result_ids
    assert all(row["readiness_status"] in APPROVED for row in queue)
    assert not any(row["readiness_status"] in EXCLUDED for row in queue)
    assert all(row["integrity_status"] == "integrity_pass" for row in integrity)
    assert all(row["extraction_status"] in CONTROLLED for row in results)
    assert all(row["rating_status"] == "not_rated" for row in results)
    assert all(row["ingestion_status"] == "not_ingested" for row in results)
    assert all(row["codification_status"] == "not_codified" for row in results)
    assert all(row["causal_status"] == "not_causal_evidence" for row in results)
    assert all(row["global_analysis_readiness"] == "false" for row in results)

    lane_union: set[str] = set()
    for lane, expected in LANES.items():
        number = lane[-3:]
        lane_queue = load_csv(OUT / f"combined_broad_text_extraction_lane_{number}_locked_queue.csv")
        lane_results = load_csv(OUT / "lanes" / lane / f"lane_{number}_text_extraction_results.csv")
        checkpoint = load_json(OUT / "lanes" / lane / f"lane_{number}_checkpoint.json")
        resume = load_json(OUT / "lanes" / lane / f"lane_{number}_resume_state.json")
        assert len(lane_queue) == len(lane_results) == expected
        assert checkpoint["status"] == "completed"
        assert checkpoint["complete"] is True
        assert resume["resume_required"] is False
        ids = {row["extraction_id"] for row in lane_queue}
        assert not lane_union.intersection(ids)
        lane_union.update(ids)
    assert lane_union == queue_ids

    counts = Counter(row["extraction_status"] for row in results)
    assert summary["extraction_attempted_count"] == 4051
    assert summary["pdf_extraction_attempted_count"] == 3177
    assert summary["html_extraction_attempted_count"] == 834
    assert summary["other_document_extraction_attempted_count"] == 40
    assert summary["extracted_ok_count"] == counts["extracted_ok"] == len(extracted_ok)
    assert all(row["extraction_status"] == "extracted_ok" for row in extracted_ok)
    assert all(
        row["extracted_text_artifact_path"]
        and int(row["extracted_text_size_bytes"]) > 0
        and len(row["extracted_text_sha256"]) == 64
        for row in extracted_ok
    )
    excluded_from_span = {
        row["extraction_id"] for row in results
        if row["extraction_status"] != "extracted_ok"
    }
    assert not excluded_from_span.intersection({row["extraction_id"] for row in extracted_ok})

    tracked_text = subprocess.run(
        ["git", "ls-files", "artifacts/local_extracted_text"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    tracked_retained = subprocess.run(
        ["git", "ls-files", "artifacts/local_retained_sources"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert not tracked_text and not tracked_retained
    probe = ROOT / summary["artifact_root"] / ".test-ignore-probe"
    assert subprocess.run(["git", "check-ignore", "-q", str(probe.relative_to(ROOT))], cwd=ROOT).returncode == 0
    assert summary["full_extracted_text_tracked_in_git"] is False
    assert summary["retained_source_binaries_tracked_in_git"] is False

    assert all(invariants[key] is True for key in (
        "queue_count_exact", "lane_counts_exact", "master_equals_lane_union",
        "approved_readiness_only", "controlled_extraction_statuses",
        "extracted_ok_has_hashes", "four_lanes_completed",
        "staggered_overlap_achieved", "standard_stagger_offsets_achieved",
    ))
    assert invariants["excluded_readiness_status_count"] == 0
    assert invariants["forbidden_actions_performed"] == []
    assert decision["global_analysis_readiness"] is False

    phase = load_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    source = load_json(ROOT / "docs/dashboard/data/source_review_status_summary.json")
    state = load_json(ROOT / "docs/dashboard/data/state_summary.json")
    assert phase["current_phase_code"] in {
        decision["decision"],
        "combined_broad_span_extraction_3815_completed_rating_ready",
        "combined_broad_exact_span_rating_17259_completed_summary_ready",
        "combined_broad_exact_span_rating_17259_completed_with_quarantine_summary_ready",
        "combined_broad_exact_span_rating_summary_16947_completed_ingestion_ready",
    }
    assert phase["text_extraction_queue_size"] == 4051
    assert phase["text_extraction_attempted_count"] == 4051
    assert phase["text_extracted_ok_count"] == len(extracted_ok)
    assert source["stage"] in {
        "combined_broad_text_extraction_complete",
        "combined_broad_span_extraction_complete",
        "combined_broad_exact_span_rating_complete",
        "combined_broad_exact_span_rating_summary_complete",
    }
    assert source["text_extraction_attempted_count"] == 4051
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metric_definition"]["map_color_metric"] == "scout_coverage_rate"
    assert phase["dashboard_map_filter"] == "total_scout_coverage_only"
    assert phase["global_analysis_readiness"] is False
    map_metrics = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    map_ui = (ROOT / "docs/dashboard/src/components/NationalMap.jsx").read_text(encoding="utf-8")
    assert map_metrics.count('key: "') == 1
    assert 'key: "scout_coverage_rate"' in map_metrics
    assert "<select" not in map_ui and "metric-select" not in map_ui
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    assert "Text extraction attempted" in app
    assert "PDF/text-layer readiness complete; four-lane bounded text extraction ready next" not in phase["current_phase"]

    prompt = (OUT / "next_combined_broad_span_extraction_prompt.md").read_text(encoding="utf-8").casefold()
    for boundary in (
        "t+0, t+8, t+16", "verbatim", "no ocr", "do not paraphrase",
        "map remains total scout coverage only", "global analysis readiness remains false",
        "before any future rating task closes",
    ):
        assert boundary in prompt
    runner = (ROOT / "scripts/run_combined_broad_text_extraction_4051.py").read_text(encoding="utf-8").casefold()
    for forbidden in (
        "import requests", "import httpx", "urllib.request", "tesseract",
        "ocrmypdf", "pdf2image", "pytesseract", "gabriel.codify", "openai",
    ):
        assert forbidden not in runner
    readiness_results = load_csv(READY / "combined_broad_pdf_text_layer_readiness_4961_results.csv")
    assert len(readiness_results) == 4961
    completed = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/run_combined_broad_text_extraction_4051.py"),
            "--validate",
        ],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in completed.stdout
    print("combined broad text extraction 4051 tests passed")


if __name__ == "__main__":
    main()
