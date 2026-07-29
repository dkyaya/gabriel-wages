#!/usr/bin/env python3
"""Fail-closed checks for the 378-file Tier C text/span and dashboard phase."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/DASHBOARD-DECLUTTER-MAP-CORRECTION-AND-TIER-C-TEXT-SPAN-EXTRACTION-378-2026-07-27"


def load_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def load_csv(name: str):
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    decision = load_json("dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json")
    invariants = load_json("dashboard_declutter_map_correction_tier_c_text_span_extraction_invariant_checks.json")
    text_rows = load_csv("tier_c_text_layer_extraction_378_results.csv")
    span_sources = load_csv("tier_c_evidence_span_extraction_results.csv")
    spans = load_csv("tier_c_evidence_span_records.csv")
    rating = load_csv("tier_c_evidence_span_rating_candidate_manifest.csv")
    preserved = load_csv("tier_c_text_span_extraction_preserved_readiness_exclusions.csv")

    assert decision["decision"] == "dashboard_declutter_map_correction_tier_c_text_span_completed_rating_ready"
    assert len(text_rows) == 378 == len({row["retained_source_id"] for row in text_rows})
    assert sum(row["readiness_status"] == "parse_text_layer_later" for row in text_rows) == 317
    assert sum(row["readiness_status"] == "html_text_later" for row in text_rows) == 61
    assert {row["extraction_status"] for row in text_rows} == {"extracted_ok"}
    assert all(row["priority_tier"] == "tier_c" for row in text_rows)
    assert len(preserved) == 178
    assert not ({row["retained_source_id"] for row in text_rows} & {row.get("retained_source_id", "") for row in preserved})
    for row in text_rows:
        artifact = ROOT / row["extracted_text_path"]
        assert artifact.is_file() and artifact.resolve().is_relative_to((OUT / "extracted_text").resolve())
        assert artifact.stat().st_size == int(row["extracted_text_size_bytes"])
        assert sha256(artifact) == row["extracted_text_sha256"]
        assert row["rating_status"] == "not_rated"
        assert row["ingestion_status"] == "not_ingested"
        assert row["codification_status"] == "not_codified"
        assert row["causal_status"] == "not_causal_evidence"
        assert row["global_analysis_readiness"] == "false"

    assert len(span_sources) == 378
    assert sum(row["span_status"] == "span_extracted" for row in span_sources) == 52
    assert sum(row["span_status"] == "ambiguous_span" for row in span_sources) == 225
    assert sum(row["span_status"] == "no_span_or_weak" for row in span_sources) == 101
    positive = [row for row in spans if row["span_status"] == "span_extracted"]
    ambiguous = [row for row in spans if row["span_status"] == "ambiguous_span"]
    assert len(spans) == 384 and len(positive) == 159 and len(ambiguous) == 225
    span_key = lambda row: (row["retained_source_id"], row["span_start_offset"], row["span_end_offset"], row["span_sha256"])
    assert len(rating) == 159 and {span_key(row) for row in rating} == {span_key(row) for row in positive}
    text_by_id = {row["retained_source_id"]: (ROOT / row["extracted_text_path"]).read_text(encoding="utf-8") for row in text_rows}
    for row in spans:
        text = text_by_id[row["retained_source_id"]]
        start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
        assert text[start:end] == row["span_text"]
        assert hashlib.sha256(row["span_text"].encode()).hexdigest() == row["span_sha256"]
        assert row["rating_status"] == "not_rated" and row["global_analysis_readiness"] == "false"

    assert decision["positive_span_counts_by_mechanism"] == {
        "fiscal_constraint_signal": 2,
        "market_or_comparability_pressure": 54,
        "non_safety_constraint_signal": 12,
        "strike_or_no_strike_constraint": 91,
    }
    assert invariants["all_invariants_passed"] is True

    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metadata"]["map_data_date"] == "2026-07-27"
    assert state["metric_definition"]["map_color_metric"] == "total_scout_coverage_count"
    broad_decision_path = (
        ROOT
        / "docs/analysis/compensation_extraction/"
        "BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/"
        "broad_state_by_state_source_scout_wave_decision.json"
    )
    broad_completed = broad_decision_path.is_file()
    broad_decision = json.loads(broad_decision_path.read_text()) if broad_completed else {}
    live_decision_path = (
        ROOT
        / "docs/analysis/compensation_extraction/"
        "BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27/"
        "broad_state_4x1000_parallel_live_scout_decision.json"
    )
    live_decision = json.loads(live_decision_path.read_text()) if live_decision_path.is_file() else {}
    expected_scout_coverage = 2436 + (
        broad_decision["parseable_target_count"] if broad_completed else 0
    ) + live_decision.get("new_scout_covered_municipalities", 0)
    assert sum(row["total_scout_coverage_count"] for row in state["states"]) == expected_scout_coverage
    assert phase["current_phase_code"] in {
        decision["decision"],
        "tier_c_evidence_span_rating_159_completed_summary_ready",
        "tier_c_evidence_span_rating_159_completed_with_quarantine",
        "tier_c_evidence_span_rating_summary_140_completed_memo_supplement_ready",
        "bounded_tier_c_evidence_memo_supplement_completed_broad_scouting_ready",
        "broad_state_by_state_source_scout_completed_candidate_review_ready",
        "broad_state_4x1000_scout_dry_run_prep_completed_live_ready",
        "broad_state_4x1000_parallel_live_scout_completed_combined_candidate_review_ready",
        "broad_candidate_verification_4x3000_completed_review_ready",
        "broad_candidate_verification_4x3000_partial_lanes_completed_resume_ready",
        "broad_candidate_verification_4x3000_resume_lane_004_completed_review_ready",
        "combined_broad_candidate_review_completed_source_review_ready",
        "combined_broad_source_review_download_5589_completed_pdf_readiness_ready",
        "combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready",
        "combined_broad_text_extraction_4051_completed_span_extraction_ready",
        "combined_broad_span_extraction_3815_completed_rating_ready",
        "combined_broad_exact_span_rating_17259_completed_summary_ready",
        "combined_broad_exact_span_rating_17259_completed_with_quarantine_summary_ready",
        "combined_broad_exact_span_rating_summary_16947_completed_ingestion_ready",
    }
    assert phase["tier_c_text_extracted_ok_count"] == 378
    assert phase["tier_c_positive_exact_span_count"] == 159
    assert phase["global_analysis_readiness"] is False

    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text()
    map_ui = (ROOT / "docs/dashboard/src/components/NationalMap.jsx").read_text()
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text()
    assert map_source.count('key: "') == 1 and 'key: "total_scout_coverage_count"' in map_source
    assert "<select" not in map_ui and "metric-select" not in map_ui
    assert "Map data date:" in map_ui
    for forbidden in ("tier_c_retained_source_count", "mechanism", "source family", "readiness only"):
        assert forbidden not in map_source
    assert 'id="historical-archive"' in app and "Open current evidence memo" in app
    assert "Tier C memo remains a completed historical" in app
    assert "Current operation:" in app
    assert "Global analysis readiness" in app
    for policy in (
        OUT / "future_prompt_dashboard_update_requirement.md",
        ROOT / "docs/prompts/dashboard_update_requirement.md",
        ROOT / "docs/analysis/future_prompt_dashboard_update_requirement_2026-07-27.md",
    ):
        text = policy.read_text()
        assert "After every task" in text and "global analysis readiness false" in text

    runner = (ROOT / "scripts/run_dashboard_declutter_map_correction_tier_c_text_span_extraction.py").read_text()
    for forbidden in ("requests.", "curl ", "tesseract", "pdf2image", "gabriel.codify", "openai"):
        assert forbidden not in runner.lower()
    completed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/run_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"), "--resume"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in completed.stdout
    print("dashboard declutter/map correction and Tier C text/span tests passed")


if __name__ == "__main__":
    main()
