#!/usr/bin/env python3
"""Focused invariants for BROAD-STATE 4x2500 span extraction and rate map."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

import run_broad_state_4x2500_span_extraction as runner


ROOT = Path(__file__).resolve().parents[1]
OUT = runner.OUTPUT


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def data(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    locked = rows("span_extraction_locked_queue.csv")
    results = rows("merged_span_extraction_source_results.csv")
    spans = rows("span_candidates.csv")
    rating = rows("span_rating_ready_queue.csv")
    summary = data("span_extraction_summary.json")
    assert len(locked) == len(results) == 2795
    assert len({row["extraction_id"] for row in locked}) == 2795
    assert Counter(row["span_lane_id"] for row in locked) == Counter(runner.LANES)
    assert all(row["extraction_status"] == "extracted_ok" for row in locked)
    assert all(row["primary_span_extraction_status"] in runner.STATUSES for row in results)
    assert len({row["span_id"] for row in spans}) == len(spans)
    assert all(row["evidence_category"] in runner.EVIDENCE_CATEGORIES for row in spans)
    assert all(row["short_paraphrase"] and len(row["exact_span_text"]) <= runner.MAX_SPAN_CHARS for row in spans)
    assert all(row["evidence_category"] in runner.RATING_ELIGIBLE for row in rating)
    assert summary["decision"] == runner.DECISION
    assert summary["span_extraction_queue_size"] == 2795
    assert summary["total_span_candidate_count"] == len(spans)
    assert summary["span_rating_ready_count"] == len(rating)
    assert summary["ocr_occurred"] is False and summary["rating_occurred"] is False
    assert data("extracted_text_hash_recheck_report.json")["all_hashes_match"] is True
    assert data("forbidden_action_audit.json")["passed"] is True
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    assert state["metric_definition"]["map_color_metric"] == "scout_coverage_rate"
    assert state["totals"]["scout_covered_municipalities"] == 16887
    assert state["totals"]["municipality_universe"] == 35589
    assert all(
        row["coverage_rate_status"] == "coverage_rate_unavailable"
        if not row["municipality_universe"] else row["scout_coverage_rate"] is not None
        for row in state["states"]
    )
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text()
    assert 'key: "scout_coverage_rate"' in map_source
    assert 'key: "total_scout_coverage_count"' not in map_source
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    assert phase["broad_state_4x2500_span_extraction_available"] is True
    assert phase["next_phase"] == "four-lane broad-state 4 × 2,500 span rating"
    assert phase["dashboard_map_primary_metric"] == "scout_coverage_rate"
    assert phase["global_analysis_readiness"] is False
    subprocess.run([str(ROOT / ".venv/bin/python"), str(runner.__file__), "--validate"], cwd=ROOT, check=True)
    print("PASS: broad-state 4x2500 span extraction and coverage-rate map invariants")


if __name__ == "__main__":
    main()
