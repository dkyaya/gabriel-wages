#!/usr/bin/env python3
"""Fail-closed tests for bounded rating of 159 Tier C exact spans."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_tier_c_evidence_span_rating_159.py"
SPEC = importlib.util.spec_from_file_location("tier_c_rating_159", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    queue, audit = runner.verify_inputs()
    assert len(queue) == len({row["span_extraction_id"] for row in queue}) == 159
    assert runner.id_set_hash(queue) == runner.EXPECTED_ID_SET_HASH
    assert Counter(row["target_mechanism_family"] for row in queue) == Counter(runner.EXPECTED_MECHANISMS)
    assert all(row["priority_tier"] == "tier_c" and row["span_status"] == "span_extracted" for row in queue)
    assert all(row["rating_status"] == "not_rated" for row in queue)
    assert all(row["global_analysis_readiness"] == "false" for row in queue)
    assert audit["full_extracted_text_reopened"] is False
    for row in queue:
        start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
        assert end - start == len(row["span_text"])
        assert hashlib.sha256(row["span_text"].encode()).hexdigest() == row["span_sha256"]
        assert len(row["context_before"]) <= 160 and len(row["context_after"]) <= 160

    sentinel = dict(queue[0])
    sentinel.update({
        "source_url_or_locator": "SENTINEL_URL",
        "source_title": "SENTINEL_TITLE",
        "municipality": "SENTINEL_CITY",
        "bargaining_unit_name": "SENTINEL_UNIT",
    })
    prompt = runner.base.build_prompt(sentinel)
    assert sentinel["span_text"] in prompt
    assert sentinel["context_before"] in prompt and sentinel["context_after"] in prompt
    for value in ("SENTINEL_URL", "SENTINEL_TITLE", "SENTINEL_CITY", "SENTINEL_UNIT"):
        assert value not in prompt

    output = runner.OUTPUT_DIR
    decision = json.loads((output / f"{runner.PREFIX}_decision.json").read_text())
    valid = read_csv(output / f"{runner.PREFIX}_valid_ratings.csv")
    quarantine = read_csv(output / f"{runner.PREFIX}_quarantine.csv")
    requests = read_csv(output / f"{runner.PREFIX}_request_metadata.csv")
    assert decision["decision"] == "tier_c_evidence_span_rating_159_completed_with_quarantine"
    assert len(valid) == 140 and len(quarantine) == 19 and len(valid) + len(quarantine) == 159
    assert {row["span_extraction_id"] for row in valid}.isdisjoint({row["span_extraction_id"] for row in quarantine})
    source = {row["span_extraction_id"]: row for row in queue}
    for row in valid:
        assert row["span_rating_id"].startswith("SPANRTIERC159-")
        assert row["quote_used"] in source[row["span_extraction_id"]]["span_text"]
        assert row["quote_exact_substring"] == "true"
        assert row["no_wage_gap_claim"] == row["no_final_causal_claim"] == "true"
        assert (row["ingestion_status"], row["codification_status"], row["causal_status"], row["global_analysis_readiness"]) == (
            "not_ingested", "not_codified", "not_causal_evidence", "false"
        )
    assert all(row["error_code"] == "quote_not_exact_span_substring" for row in quarantine)
    assert all(row["raw_prompt_saved"] == row["raw_response_saved"] == "false" for row in requests)
    assert all("prompt" not in row and "response_text" not in row for row in requests)
    assert decision["gabriel_api_model_call_count"] == len(requests) == 199
    assert decision["global_analysis_readiness"] is False
    assert decision["dashboard_map_filter"] == "total_scout_coverage_only"

    dashboard_spec = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard_data.py")
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    complete, dashboard_decision = dashboard.tier_c_evidence_span_rating_159_status()
    assert complete and dashboard_decision["valid_rating_count"] == 140
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    assert phase["current_phase_code"] in {
        decision["decision"],
        "tier_c_evidence_span_rating_summary_140_completed_memo_supplement_ready",
    }
    assert phase["tier_c_rating_valid_count"] == 140
    assert phase["tier_c_rating_quarantine_count"] == 19
    assert phase["next_task"].startswith(("bounded summary review", "bounded Tier C memo supplement"))
    assert phase["global_analysis_readiness"] is False
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metric_definition"]["map_color_metric"] == "total_scout_coverage_count"

    future = (output / "next_tier_c_evidence_span_rating_summary_prompt.md").read_text().casefold()
    for phrase in ("explicitly exclude", "do not access urls", "rating is not causal proof", "dashboard update requirement", "global analysis readiness true"):
        assert phrase in future
    source_code = RUNNER_PATH.read_text().casefold()
    for forbidden in ("pytesseract", "ocrmypdf", "pdf2image", "pdftotext", "pdfinfo", "requests.get", "urllib.request"):
        assert forbidden not in source_code
    resumed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(RUNNER_PATH), "--resume"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in resumed.stdout
    print("Tier C evidence-span rating 159 tests passed")


if __name__ == "__main__":
    main()
