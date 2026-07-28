#!/usr/bin/env python3
"""Fail-closed tests for the aggregate-only Tier C memo supplement."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_bounded_tier_c_evidence_memo_supplement.py"
SPEC = importlib.util.spec_from_file_location("tier_c_memo_supplement", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def load(name: str):
    return json.loads((runner.OUTPUT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    context = runner.validate_inputs()
    assert context["decision"]["valid_rating_summary_count"] == 140
    assert context["decision"]["quarantine_excluded_count"] == 19
    assert context["decision"]["total_reconciliation"] == 159
    assert context["decision"]["mechanism_summary"] == runner.EXPECTED_MECHANISMS
    assert context["relevance"]["counts"] == runner.EXPECTED_RELEVANCE
    assert context["strength"]["counts"] == runner.EXPECTED_STRENGTH
    assert context["direction"]["counts"] == runner.EXPECTED_DIRECTION
    assert context["support"]["provisional_causal_candidate_hints"] == runner.EXPECTED_CAUSAL_HINTS

    runner.validate_complete()
    decision = load("bounded_tier_c_evidence_memo_supplement_decision.json")
    invariants = load("bounded_tier_c_evidence_memo_supplement_invariant_checks.json")
    policy = load("future_rating_artifact_completeness_policy.json")
    fallback = load("future_rating_summary_artifact_reconstruction_fallback.json")
    scouting = load("post_tier_c_scouting_strategy_decision.json")
    assert decision["decision"] == runner.DECISION
    assert decision["valid_rating_summary_scope"] == 140
    assert decision["quarantines_excluded"] == 19
    assert decision["quarantines_used_as_evidence"] == 0
    assert decision["predecessor_scope_reconciled"] == 159
    assert decision["gabriel_api_model_calls"] == decision["rerating_runs"] == 0
    assert decision["url_opens"] == decision["downloads"] == decision["pdf_page_accesses"] == 0
    assert decision["retained_source_accesses"] == decision["full_extracted_text_accesses"] == 0
    assert decision["global_analysis_readiness"] is False
    assert invariants["all_invariants_passed"] is True
    assert invariants["only_140_valid_rating_summary_used"] is True
    assert invariants["all_19_quarantines_excluded_as_evidence"] is True
    assert policy["reconstruct_derivable_missing_artifacts"] is True
    assert policy["missing_non_derivable_artifacts_fail_closed"] is True
    assert fallback["allowed_only_if_fully_derivable_from_committed_ledgers"] is True
    assert fallback["repair_commit_required"] is fallback["repair_push_required"] is True
    assert scouting["decision"] == "broad_state_by_state_source_family_diverse_scouting_is_default_next"
    assert scouting["dashboard_map_filter"] == "total_scout_coverage_only"

    memo = (runner.OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement.md").read_text(encoding="utf-8").casefold()
    for phrase in (
        "seventy-six valid ratings", "fifty-one valid ratings", "11 valid ratings",
        "only 2 valid ratings", "neutral or unclear for 108", "nineteen quarantined outputs",
        "broad geographic/state-by-state scouting", "global analysis readiness remains false",
    ):
        assert phrase in memo
    for prohibited_claim in (
        "caused the wage gap", "statistically significant", "nationally, safety workers",
        "the treatment effect is", "safety workers earn more because",
    ):
        assert prohibited_claim not in memo

    prompt = (runner.OUTPUT_DIR / "next_broad_state_by_state_scout_prompt.md").read_text(encoding="utf-8").casefold()
    for phrase in (
        "dashboard update requirement", "post-rating artifact-completeness requirement",
        "reconstruct it deterministically", "missing non-derivable artifacts still fail closed",
        "source-family balance", "mechanism-targeted scouting is secondary",
        "global analysis readiness true",
    ):
        assert phrase in prompt

    dashboard_spec = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard_data.py")
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    complete, dashboard_decision = dashboard.bounded_tier_c_evidence_memo_supplement_status()
    assert complete and dashboard_decision["decision"] == runner.DECISION
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    assert phase["current_phase_code"] in {
        runner.DECISION,
        "broad_state_by_state_source_scout_completed_candidate_review_ready",
        "broad_state_4x1000_scout_dry_run_prep_completed_live_ready",
        "broad_state_4x1000_parallel_live_scout_completed_combined_candidate_review_ready",
    }
    assert phase["tier_c_memo_supplement_valid_scope"] == 140
    assert phase["tier_c_memo_supplement_quarantines_excluded"] == 19
    assert phase["next_task"].startswith(
        ("broad state-by-state scouting", "bounded candidate review", "run broad state 4x1000 live scout", "run one combined candidate review")
    )
    assert phase["global_analysis_readiness"] is False
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metric_definition"]["map_color_metric"] == "total_scout_coverage_count"

    source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in ("requests.get", "httpx", "urllib.request", "pytesseract", "pdf2image", "gabriel.codify"):
        assert forbidden not in source
    for forbidden_path in (
        "valid_ratings.csv", "quarantine.csv", "evidence_span_records.csv",
        "extracted_text/", "retained_sources/",
    ):
        assert forbidden_path not in source

    resumed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(RUNNER_PATH), "--resume"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "completed_outputs_valid_zero_writes" in resumed.stdout
    print("Bounded Tier C evidence memo supplement tests passed")


if __name__ == "__main__":
    main()
