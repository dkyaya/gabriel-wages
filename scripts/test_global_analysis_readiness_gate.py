#!/usr/bin/env python3
"""Invariant tests for the post-codification global readiness gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/GLOBAL-ANALYSIS-READINESS-GATE-AFTER-BROAD-INGESTION-2026-07-28"
RUNNER = ROOT / "scripts/run_global_analysis_readiness_gate.py"

REQUIRED = [
    "global_analysis_readiness_gate_decision.json", "global_analysis_readiness_gate_summary.md",
    "global_analysis_readiness_gate_input_reconciliation.csv", "global_analysis_readiness_gate_input_reconciliation_summary.json",
    "global_analysis_readiness_gate_quarantine_exclusion_note.md", "global_analysis_readiness_gate_flags.json",
    "global_analysis_readiness_gate_flags.csv", "global_collection_readiness_review.md",
    "global_mechanism_analysis_readiness_review.md", "global_quantitative_evidence_readiness_review.md",
    "global_wage_gap_analysis_readiness_review.md", "global_causal_analysis_readiness_review.md",
    "overall_global_analysis_readiness_review.md", "global_analysis_readiness_gate_blockers.md",
    "global_analysis_readiness_gate_blockers.json", "global_analysis_readiness_gate_caveats.md",
    "global_analysis_readiness_gate_claims_allowed_later.md", "global_analysis_readiness_gate_claims_still_prohibited.md",
    "global_analysis_readiness_gate_next_requirements.md", "global_analysis_readiness_gate_collection_summary.json",
    "global_analysis_readiness_gate_mechanism_summary.json", "global_analysis_readiness_gate_quantitative_summary.json",
    "global_analysis_readiness_gate_directional_hint_summary.json", "global_analysis_readiness_gate_source_navigation_summary.json",
    "global_analysis_readiness_gate_weak_context_summary.json", "global_analysis_readiness_gate_source_family_summary.json",
    "global_analysis_readiness_gate_geography_summary.json", "global_analysis_readiness_gate_dashboard_update_summary.md",
    "global_analysis_readiness_gate_dashboard_update_summary.json", "dashboard_overview_metric_sync_after_global_readiness_gate.md",
    "dashboard_overview_metric_sync_after_global_readiness_gate.json", "dashboard_stale_overview_guard_after_global_readiness_gate.md",
    "dashboard_stale_overview_guard_after_global_readiness_gate.json", "next_broad_state_4x2500_scout_infrastructure_prep_prompt.md",
    "global_analysis_readiness_gate_to_next_scouting_rhythm_note.md", "future_broad_4x2500_scout_standard.md",
    "future_broad_4x2500_scout_standard.json", "global_analysis_readiness_gate_validation_2026-07-28.md",
    "global_analysis_readiness_gate_invariant_checks.json", "global_analysis_readiness_gate_stress_test_report.md",
    "global_analysis_readiness_gate_regression_test_inventory.json", "next_task.md",
]

def j(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))

def c(name: str):
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def main() -> int:
    passed: list[str] = []
    def check(name: str, value: bool) -> None:
        if not value:
            raise AssertionError(name)
        passed.append(name)

    check("required outputs", all((OUT / name).is_file() for name in REQUIRED))
    decision = j("global_analysis_readiness_gate_decision.json")
    flags = j("global_analysis_readiness_gate_flags.json")
    reconciliation = j("global_analysis_readiness_gate_input_reconciliation_summary.json")
    invariants = j("global_analysis_readiness_gate_invariant_checks.json")
    standard = j("future_broad_4x2500_scout_standard.json")
    expected = {
        "global_collection_readiness": "pass",
        "global_mechanism_analysis_readiness": "partial_pass",
        "global_quantitative_evidence_readiness": "partial_pass",
        "global_wage_gap_analysis_readiness": "blocked_pending_normalization",
        "global_causal_analysis_readiness": "blocked_pending_matched_structure",
        "overall_global_analysis_readiness": "partial_pass",
    }
    controlled = {"pass", "partial_pass", "fail", "not_applicable", "blocked_pending_normalization", "blocked_pending_matched_structure", "blocked_pending_more_data", "blocked_pending_quality_repair"}
    check("decision", decision["decision"] == "global_analysis_readiness_gate_completed_with_partial_readiness_next_scout_prep_ready")
    check("counts", reconciliation["codified_record_count"] == 16947 and reconciliation["quarantine_excluded_count"] == 312 and reconciliation["input_total"] == 17259)
    check("quarantine exclusion", reconciliation["reconciles"] is True and reconciliation["quarantine_leakage_count"] == 0)
    check("flags exact", decision["subflag_results"] == expected)
    check("flags controlled", set(expected.values()) <= controlled and set(flags["controlled_values"]) == controlled)
    check("overall unambiguous", decision["overall_global_analysis_readiness_bool"] is False and decision["global_analysis_readiness"] is False)
    check("wage and causal blocked", expected["global_wage_gap_analysis_readiness"].startswith("blocked") and expected["global_causal_analysis_readiness"].startswith("blocked"))
    check("all invariants", invariants["all_invariants_passed"] is True and invariants["model_api_calls"] == invariants["source_or_full_text_access"] == invariants["normalization_or_comparison_runs"] == 0)
    check("scout standard", standard["lane_count"] == 4 and standard["targets_per_lane"] == 2500 and standard["target_ceiling"] == 10000 and standard["stagger_minutes"] == [0, 8, 16, 24] and standard["checkpoint_after_every_target"] is True)
    prompt = (OUT / "next_broad_state_4x2500_scout_infrastructure_prep_prompt.md").read_text(encoding="utf-8")
    check("future prompt boundaries", all(term in prompt for term in ["four independent lanes", "2,500 targets", "10,000-target ceiling", "T+0/T+8/T+16/T+24", "checkpoint/resume after every target", "source-family diversification", "municipality coverage accounting", "total scout coverage only", "may not perform candidate review", "future rating task must verify downstream summary artifacts"]))
    source = RUNNER.read_text(encoding="utf-8").lower()
    check("no model/network/source imports", all(term not in source for term in ["import openai", "import requests", "urllib", "local_extracted_text", "local_retained_sources", "gabriel.codify"]))
    dashboard = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text(encoding="utf-8"))
    check("dashboard current", dashboard["current_phase"].startswith((
        "Global analysis readiness gate complete",
        "Broad state 4 × 2,500 scout infrastructure prep complete",
        "Broad state 4 × 2,500 live scout complete",
        "Broad state 4 × 2,500 candidate review complete",
        "Broad state 4 × 2,500 verification complete",
        "Broad state 4 × 2,500 source review/download complete",
        "Broad state 4 × 2,500 PDF/text readiness complete",
    )))
    check("dashboard flags", dashboard["global_readiness_gate_flags"] == expected and dashboard["global_analysis_readiness"] is False)
    check("dashboard next", ("2,500-target" in dashboard["next_task"] or "BROAD-STATE-4X2500-" in dashboard["next_task"]) and dashboard["next_phase"] in {
        "broad 4 × 2,500 scouting infrastructure preparation",
        "live broad state 4 × 2,500 scouting",
        "deterministic combined broad candidate review",
        "four-lane broad-state 4 × 2,500 candidate verification",
        "four-lane broad-state 4 × 2,500 source review/download",
        "four-lane broad-state 4 × 2,500 PDF/text readiness",
        "four-lane broad-state 4 × 2,500 text extraction",
    })
    expected_coverage = 16887 if dashboard.get("broad_state_4x2500_candidate_review_available") else 6919
    check("map stable", dashboard["current_scout_covered"] == expected_coverage and dashboard["dashboard_map_filter"] == "total_scout_coverage_only" and dashboard["map_data_date"] == "2026-07-27")
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    check("readiness outside map", all(term in app for term in ["Collection readiness", "Mechanism readiness", "Wage-gap readiness", "Causal readiness", "Next planned stage"]))
    with tempfile.TemporaryDirectory(prefix="global-gate-") as temp:
        rebuilt = Path(temp) / "out"
        subprocess.run([sys.executable, str(RUNNER), "--output-dir", str(rebuilt)], cwd=ROOT, check=True, capture_output=True, text=True)
        for name in ["global_analysis_readiness_gate_decision.json", "global_analysis_readiness_gate_flags.json", "global_analysis_readiness_gate_input_reconciliation_summary.json"]:
            check(f"idempotent {name}", (rebuilt / name).read_bytes() == (OUT / name).read_bytes())
    print(f"global analysis readiness gate tests: {len(passed)}/{len(passed)} passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
