#!/usr/bin/env python3
"""Fail-closed tests for the 140-valid-rating Tier C summary."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_tier_c_evidence_span_rating_summary_140.py"
SPEC = importlib.util.spec_from_file_location("tier_c_summary_140", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load(name: str):
    return json.loads((runner.OUTPUT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    valid, quarantine, context = runner.validate_inputs()
    assert len(valid) == 140 and len(quarantine) == 19 and len(valid) + len(quarantine) == 159
    valid_ids = {row["span_extraction_id"] for row in valid}
    quarantine_ids = {row["span_extraction_id"] for row in quarantine}
    assert not valid_ids & quarantine_ids
    assert len(context["claim_candidates"]) == 115
    assert runner.controlled_counts(valid, "target_mechanism_family", runner.MECHANISMS) == runner.EXPECTED_MECHANISMS
    assert runner.controlled_counts(valid, "claim_relevance", runner.RELEVANCE) == runner.EXPECTED_RELEVANCE
    assert runner.controlled_counts(valid, "evidence_strength", runner.STRENGTHS) == runner.EXPECTED_STRENGTH
    assert runner.controlled_counts(valid, "direction_of_pressure", runner.DIRECTIONS) == runner.EXPECTED_DIRECTION
    assert runner.controlled_counts(valid, "provisional_causal_candidate_support", runner.STRENGTHS) == runner.EXPECTED_CAUSAL_SUPPORT

    runner.validate_complete(runner.OUTPUT_DIR)
    decision = load(f"{runner.PREFIX}_decision.json")
    reconciliation = load(f"{runner.PREFIX}_input_reconciliation_summary.json")
    mechanism = load(f"{runner.PREFIX}_by_mechanism_summary.json")
    claim = load(f"{runner.PREFIX}_claim_relevance_summary.json")
    direction = load(f"{runner.PREFIX}_direction_of_pressure_summary.json")
    strength = load(f"{runner.PREFIX}_evidence_strength_summary.json")
    support = load(f"{runner.PREFIX}_support_matrix_summary.json")
    invariants = load(f"{runner.PREFIX}_invariant_checks.json")
    assert decision["decision"] == "tier_c_evidence_span_rating_summary_140_completed_memo_supplement_ready"
    assert decision["valid_rating_summary_count"] == 140
    assert decision["quarantine_excluded_count"] == 19
    assert reconciliation["valid_plus_quarantine_reconciles"] is True
    assert reconciliation["valid_quarantine_ids_disjoint"] is True
    assert mechanism["valid_rating_count"] == 140 and mechanism["quarantines_excluded"] == 19
    assert claim["counts"] == runner.EXPECTED_RELEVANCE and claim["counts_reconcile"] is True
    assert direction["counts"] == runner.EXPECTED_DIRECTION and direction["directional_inference_allowed"] is False
    assert strength["counts"] == runner.EXPECTED_STRENGTH and strength["counts_reconcile"] is True
    assert support["provisional_causal_candidate_hints"] == runner.EXPECTED_CAUSAL_SUPPORT
    assert support["weak_support_is_not_a_claim"] is True
    assert invariants["all_invariants_passed"] is True
    assert decision["gabriel_api_model_calls"] == decision["rerating_runs"] == 0
    assert decision["url_opens"] == decision["downloads"] == decision["pdf_page_accesses"] == 0
    assert decision["retained_source_accesses"] == decision["full_extracted_text_accesses"] == 0
    assert decision["global_analysis_readiness"] is False
    assert decision["dashboard_map_filter"] == "total_scout_coverage_only"

    dashboard_spec = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard_data.py")
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    complete, dashboard_decision = dashboard.tier_c_evidence_span_rating_summary_140_status()
    assert complete and dashboard_decision["valid_rating_summary_count"] == 140
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    assert phase["current_phase_code"] in {
        decision["decision"],
        "bounded_tier_c_evidence_memo_supplement_completed_broad_scouting_ready",
        "broad_state_by_state_source_scout_completed_candidate_review_ready",
    }
    assert phase["tier_c_rating_summary_valid_count"] == 140
    assert phase["tier_c_rating_summary_quarantine_excluded_count"] == 19
    assert phase["next_task"].startswith(
        ("bounded Tier C memo supplement", "broad state-by-state scouting", "bounded candidate review")
    )
    assert phase["global_analysis_readiness"] is False
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metric_definition"]["map_color_metric"] == "scout_coverage_rate"

    future = (runner.OUTPUT_DIR / "next_tier_c_memo_supplement_prompt.md").read_text().casefold()
    for phrase in (
        "broad geographic/state-by-state scouting",
        "source-family diversification",
        "mechanism-targeted scouting is secondary",
        "dashboard update requirement",
        "global analysis readiness true",
    ):
        assert phrase in future
    source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in ("openai", "requests.get", "httpx", "urllib.request", "pytesseract", "pdf2image", "pdftotext"):
        assert forbidden not in source
    resumed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(RUNNER_PATH), "--resume"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in resumed.stdout
    print("Tier C evidence-span rating summary 140 tests passed")


if __name__ == "__main__":
    main()
