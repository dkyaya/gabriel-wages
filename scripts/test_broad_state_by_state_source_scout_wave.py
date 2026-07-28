#!/usr/bin/env python3
"""Fail-closed tests for the broad state-by-state discovery wave."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_broad_state_by_state_source_scout_wave.py"
SPEC = importlib.util.spec_from_file_location("broad_scout", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def load(name: str):
    return json.loads((runner.OUTPUT_DIR / name).read_text(encoding="utf-8"))


def rows(name: str):
    with (runner.OUTPUT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    context = runner.validate_inputs()
    assert len(context["municipalities"]) == 35589
    queue = rows("broad_state_by_state_source_scout_locked_queue.csv")
    assert len(queue) == 490
    state_counts = Counter(row["state"] for row in queue)
    assert len(state_counts) == 49 and set(state_counts.values()) == {7, 10, 11}
    assert sum(value == 11 for value in state_counts.values()) == 3
    assert "DC" not in state_counts and "HI" not in state_counts
    assert len({row["municipality_id"] for row in queue}) == 490
    assert all(row["search_query_family"] == "broad_multi_source_family" for row in queue)
    assert all("compensation/classification studies" in row["expected_units_to_search"] for row in queue)
    assert all(row["global_analysis_readiness"] == "false" for row in queue)

    runner.validate_complete()
    decision = load("broad_state_by_state_source_scout_wave_decision.json")
    invariants = load("broad_state_by_state_source_scout_invariant_checks.json")
    candidates = rows("broad_state_by_state_source_scout_candidates.csv")
    deduped = rows("broad_state_by_state_source_scout_deduped_candidates.csv")
    assert decision["decision"] == runner.DECISION
    assert decision["locked_target_count"] == 490
    assert len(candidates) == decision["candidate_count"]
    assert len(deduped) == decision["deduped_candidate_count"]
    assert all(row["verification_status"] == "not_verified" for row in candidates)
    assert all(row["download_status"] == "not_downloaded" for row in candidates)
    assert all(row["extraction_status"] == "not_extracted" for row in candidates)
    assert all(row["rating_status"] == "not_rated" for row in candidates)
    assert all(row["ingestion_status"] == "not_ingested" for row in candidates)
    assert all(row["codification_status"] == "not_codified" for row in candidates)
    assert all(row["causal_status"] == "not_causal_evidence" for row in candidates)
    assert all(row["global_analysis_readiness"] == "false" for row in candidates)
    assert invariants["all_invariants_passed"] is True
    for key in (
        "raw_prompts_saved", "raw_responses_saved", "direct_url_opens",
        "verification_head_get_requests", "downloads", "source_document_accesses",
        "ocr_runs", "render_runs", "text_extractions", "span_extractions", "rating_runs",
        "ingestion_runs", "codification_runs", "wage_gap_calculations", "regressions",
        "treatment_effect_estimates", "national_or_population_prevalence_claims",
        "final_causal_claims",
    ):
        assert decision[key] == 0

    scout_source = (ROOT / "scripts/gabriel_state_source_scout.py").read_text(encoding="utf-8")
    assert "--sanitized-artifacts-only" in scout_source
    assert "not_saved_sanitized_artifacts_only" in scout_source
    runner_source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in ("requests.get", "httpx.get", "urllib.request", "pytesseract", "pdf2image", "gabriel.codify"):
        assert forbidden not in runner_source

    next_prompt = (runner.OUTPUT_DIR / "next_broad_state_candidate_review_prompt.md").read_text(encoding="utf-8").casefold()
    for phrase in (
        "dashboard update requirement", "total scout coverage only",
        "broad geographic balance", "source-family diversity",
        "future rating artifact-completeness requirement", "missing non-derivable artifacts still fail closed",
    ):
        assert phrase in next_prompt

    dashboard_spec = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard_data.py")
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    completed, dash_decision = dashboard.broad_state_source_scout_status()
    assert completed and dash_decision["decision"] == runner.DECISION
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    assert phase["current_phase_code"] in {
        runner.DECISION,
        "broad_state_4x1000_scout_dry_run_prep_completed_live_ready",
        "broad_state_4x1000_parallel_live_scout_completed_combined_candidate_review_ready",
    }
    assert phase["broad_state_source_scout_locked_target_count"] == 490
    assert phase["global_analysis_readiness"] is False
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metadata"]["broad_state_source_scout_included"] is True
    assert state["totals"]["scout_covered_municipalities"] in {
        2436 + decision["parseable_target_count"], 6919
    }

    resumed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(RUNNER_PATH), "--validate"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in resumed.stdout
    print("Broad state-by-state scout wave tests passed")


if __name__ == "__main__":
    main()
