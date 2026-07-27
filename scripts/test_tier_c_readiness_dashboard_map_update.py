#!/usr/bin/env python3
"""Fail-closed tests for the 463-file Tier C readiness/map update."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/TIER-C-READINESS-AND-DASHBOARD-MAP-UPDATE-WITH-BROAD-SCOUTING-STRATEGY-2026-07-27"
DASHBOARD_DATA = ROOT / "docs/dashboard/data"


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    queue = read_csv("tier_c_pdf_text_layer_readiness_463_locked_queue.csv")
    results = read_csv("tier_c_pdf_text_layer_readiness_463_results.csv")
    pdf_rows = read_csv("tier_c_pdf_text_layer_readiness_463_pdf_results.csv")
    html_rows = read_csv("tier_c_pdf_text_layer_readiness_463_html_results.csv")
    preserved = read_csv("tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions.csv")
    decision = read_json("tier_c_readiness_dashboard_map_update_decision.json")
    invariants = read_json("tier_c_readiness_dashboard_map_update_invariant_checks.json")
    lock = read_json("tier_c_pdf_text_layer_readiness_463_lock.json")
    map_summary = read_json("dashboard_map_update_with_tier_c_sources_summary.json")
    map_date = read_json("dashboard_map_data_date.json")
    strategy = read_json("future_broad_geographic_scouting_strategy.json")
    source_ids = {row["retained_source_id"] for row in results}
    candidate_ids = {row["candidate_id"] for row in results}
    preserved_ids = {row["candidate_id"] for row in preserved}
    types = Counter(row["content_type_hint"] for row in results)
    statuses = Counter(row["readiness_status"] for row in results)

    assert len(queue) == len(results) == len(source_ids) == 463
    assert types == Counter({"application/pdf": 397, "text/html": 65, "application/octet-stream": 1})
    assert len(pdf_rows) == 397 and len(html_rows) == 65
    assert all(row["priority_tier"] == "tier_c" for row in queue)
    assert all(row["source_review_download_status"] == "retained_downloaded_source" for row in queue)
    assert len(preserved) == 93 and not (candidate_ids & preserved_ids)
    assert all(row["file_integrity_status"] == "integrity_pass" for row in results)
    assert lock["retained_file_integrity_pass_count"] == 463
    assert all(row["readiness_status"] != "html_text_later" for row in pdf_rows)
    assert all(row["readiness_status"] != "parse_text_layer_later" for row in html_rows)
    octet = [row for row in results if row["content_type_hint"] == "application/octet-stream"]
    assert len(octet) == 1 and octet[0]["readiness_reason"].startswith("octet_")
    assert all(
        row["extraction_status"] == "not_extracted"
        and row["rating_status"] == "not_rated"
        and row["ingestion_status"] == "not_ingested"
        and row["codification_status"] == "not_codified"
        and row["causal_status"] == "not_causal_evidence"
        and row["global_analysis_readiness"] == "false"
        for row in results
    )
    assert decision["decision"] == "tier_c_readiness_dashboard_map_update_completed_text_extraction_ready"
    assert statuses == Counter(decision["readiness_status_counts"])
    assert statuses["parse_text_layer_later"] + statuses["html_text_later"] == 378
    assert decision["url_opens"] == decision["downloads"] == decision["ocr_runs"] == 0
    assert decision["pdf_render_runs"] == decision["full_text_extraction_runs"] == 0
    assert decision["evidence_span_extraction_runs"] == decision["model_api_calls"] == 0
    assert decision["global_analysis_readiness"] is False
    assert invariants["all_invariants_passed"] is True
    assert map_summary["retained_source_count"] == 463
    assert map_summary["map_data_date"] == map_date["map_data_date"] == "2026-07-27"
    assert sum(map_summary["regions"].values()) == 463
    assert sum(map_summary["source_families"].values()) == 463
    assert sum(map_summary["mechanisms"].values()) == 463
    assert strategy["default_future_scout_mode"] == "broad_geographic_state_by_state"
    assert strategy["mechanism_targeted_scouting_role"] == "secondary_gap_filling_after_broad_scans"

    runner = (ROOT / "scripts/run_tier_c_readiness_dashboard_map_update.py").read_text(encoding="utf-8")
    forbidden_runner_tokens = ("requests.", "httpx.", "curl ", "tesseract", "pdftoppm", "convert ")
    assert not any(token in runner for token in forbidden_runner_tokens)
    assert "MAX_PDF_PROBE_PAGES = 3" in runner and "MAX_HTML_PROBE_BYTES = 256 * 1024" in runner
    assert "pdftotext" in runner and 'str(path), "-"' in runner

    phase = json.loads((DASHBOARD_DATA / "project_phase_summary.json").read_text(encoding="utf-8"))
    state_summary = json.loads((DASHBOARD_DATA / "state_summary.json").read_text(encoding="utf-8"))
    dashboard_map = json.loads((DASHBOARD_DATA / "tier_c_map_summary.json").read_text(encoding="utf-8"))
    assert phase["current_phase_code"] in {
        decision["decision"],
        "dashboard_declutter_map_correction_tier_c_text_span_completed_rating_ready",
    }
    assert phase["tier_c_text_extraction_ready_count"] == 378
    assert phase["future_scout_default"] == "broad_state_by_state_geographic_and_source_family_diverse"
    assert phase["global_analysis_readiness"] is False
    assert state_summary["metadata"]["map_data_date"] == "2026-07-27"
    assert state_summary["totals"]["tier_c_retained_sources"] == 463
    assert state_summary["totals"]["tier_c_text_extraction_ready_sources"] == 378
    assert dashboard_map["retained_source_count"] == 463
    ui = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in (
            "docs/dashboard/src/App.jsx",
            "docs/dashboard/src/components/NationalMap.jsx",
            "docs/dashboard/src/components/mapMetrics.js",
            "docs/dashboard/src/components/ProjectHubSections.jsx",
        )
    )
    assert "Map data date:" in ui
    assert "total_scout_coverage_count" in ui
    assert "Total scout coverage" in ui
    assert "<select" not in (ROOT / "docs/dashboard/src/components/NationalMap.jsx").read_text(encoding="utf-8")
    assert "Return to broad state-by-state scouting" in ui

    before = {path: path.stat().st_mtime_ns for path in OUT.iterdir() if path.is_file()}
    subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/run_tier_c_readiness_dashboard_map_update.py"), "--resume"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    after = {path: path.stat().st_mtime_ns for path in OUT.iterdir() if path.is_file()}
    assert before == after
    assert not any("raw_prompt" in path.name or "raw_response" in path.name for path in OUT.rglob("*"))
    print("PASS: Tier C readiness/dashboard map update invariants")


if __name__ == "__main__":
    main()
