#!/usr/bin/env python3
"""Invariant tests for the no-call broad 4 x 2,500 scout prep."""

from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
RUNNER = ROOT / "scripts/run_broad_state_4x2500_scout_infrastructure_prep.py"
SHARDS = [f"broad_4x2500_shard_{i:03d}" for i in range(1, 5)]
ALLOWED_TIERS = {"strong_broad_geographic_target", "strong_source_family_diversification_target", "matched_safety_non_safety_target", "acceptable_broad_target"}

REQUIRED = [
    "broad_state_4x2500_scout_infrastructure_prep_decision.json",
    "broad_state_4x2500_scout_infrastructure_prep_summary.md",
    "broad_state_4x2500_scout_master_locked_queue.csv",
    "broad_state_4x2500_scout_master_locked_queue_summary.json",
    "broad_state_4x2500_scout_master_lock.json",
    "broad_state_4x2500_scout_queue_design.md", "broad_state_4x2500_scout_shard_design.md",
    "broad_state_4x2500_scout_geographic_balance_plan.md", "broad_state_4x2500_scout_source_family_balance_plan.md",
    "broad_state_4x2500_scout_municipality_coverage_plan.md", "broad_state_4x2500_scout_matched_safety_non_safety_plan.md",
    "broad_state_4x2500_scout_dry_run_preview_master.csv", "broad_state_4x2500_scout_dry_run_preview_summary.json",
    "broad_state_4x2500_scout_dry_run_checklist.md", "broad_state_4x2500_scout_municipality_coverage_plan.csv",
    "broad_state_4x2500_scout_municipality_coverage_plan_summary.json", "broad_state_4x2500_scout_state_coverage_plan.csv",
    "broad_state_4x2500_scout_state_coverage_plan_summary.json", "broad_state_4x2500_scout_region_coverage_plan.csv",
    "broad_state_4x2500_scout_region_coverage_plan_summary.json", "broad_state_4x2500_scout_shard_municipality_coverage_summary.json",
    "broad_state_4x2500_scout_source_family_query_plan.csv", "broad_state_4x2500_scout_source_family_query_plan_summary.json",
    "broad_state_4x2500_scout_non_cba_source_family_plan.csv", "broad_state_4x2500_scout_non_cba_source_family_plan_summary.json",
    "broad_state_4x2500_scout_cba_concentration_risk_note.md", "broad_state_4x2500_scout_global_readiness_gate_context.md",
    "broad_state_4x2500_scout_no_claim_staking_rhythm_note.md", "broad_state_4x2500_scout_future_combined_candidate_review_plan.md",
    "broad_state_4x2500_scout_no_call_preflight_report.md", "broad_state_4x2500_scout_no_call_preflight_checks.json",
    "broad_state_4x2500_scout_resumability_plan.md", "broad_state_4x2500_scout_live_run_risk_controls.md",
    "broad_state_4x2500_scout_live_run_dashboard_accounting_plan.md",
    "broad_state_4x2500_scout_infrastructure_prep_dashboard_update_summary.md",
    "broad_state_4x2500_scout_infrastructure_prep_dashboard_update_summary.json",
    "broad_state_4x2500_scout_infrastructure_prep_validation_2026-07-29.md",
    "broad_state_4x2500_scout_infrastructure_prep_invariant_checks.json",
    "broad_state_4x2500_scout_infrastructure_prep_stress_test_report.md",
    "broad_state_4x2500_scout_infrastructure_prep_regression_test_inventory.json",
    "next_broad_state_4x2500_live_scout_prompt.md", "next_task.md",
]

def read_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))

def read_csv(name: str):
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def main() -> int:
    checks: list[str] = []
    def check(name: str, value: bool) -> None:
        if not value:
            raise AssertionError(name)
        checks.append(name)

    check("required outputs", all((OUT / name).is_file() for name in REQUIRED))
    for i in range(1, 5):
        check(f"shard {i} artifacts", all((OUT / name).is_file() for name in [
            f"broad_state_4x2500_scout_shard_{i:03d}_locked_queue.csv",
            f"broad_state_4x2500_scout_shard_{i:03d}_locked_queue_summary.json",
            f"broad_state_4x2500_scout_shard_{i:03d}_lock.json",
            f"broad_state_4x2500_scout_dry_run_preview_shard_{i:03d}.csv",
        ]))
    decision = read_json("broad_state_4x2500_scout_infrastructure_prep_decision.json")
    master = read_csv("broad_state_4x2500_scout_master_locked_queue.csv")
    summary = read_json("broad_state_4x2500_scout_master_locked_queue_summary.json")
    preflight = read_json("broad_state_4x2500_scout_no_call_preflight_checks.json")
    invariants = read_json("broad_state_4x2500_scout_infrastructure_prep_invariant_checks.json")
    municipality = read_json("broad_state_4x2500_scout_municipality_coverage_plan_summary.json")
    check("decision", decision["decision"] == "broad_state_4x2500_scout_infrastructure_prep_completed_live_ready")
    check("master count", len(master) == summary["locked_scout_target_count"] == 10000)
    check("unique targets", len({r["scout_target_id"] for r in master}) == 10000)
    check("unique municipalities", len({r["municipality_id"] for r in master}) == municipality["unique_municipalities_targeted_count"] == 10000)
    shard_rows = {}
    for i, shard in enumerate(SHARDS, 1):
        shard_rows[shard] = read_csv(f"broad_state_4x2500_scout_shard_{i:03d}_locked_queue.csv")
        check(f"shard {i} count", len(shard_rows[shard]) == 2500)
        lock = read_json(f"broad_state_4x2500_scout_shard_{i:03d}_lock.json")
        check(f"shard {i} runnable", lock["independently_runnable"] is True and lock["independently_resumable"] is True and lock["checkpoint_after_every_target"] is True)
    check("master shard union", {r["scout_target_id"] for r in master} == {r["scout_target_id"] for rows in shard_rows.values() for r in rows})
    check("controlled shards", {r["shard_id"] for r in master} == set(SHARDS))
    check("controlled tiers", {r["target_quality_tier"] for r in master} <= ALLOWED_TIERS)
    check("no excluded tiers", not ({"weak_do_not_include", "duplicate_do_not_include", "needs_review_do_not_include"} & {r["target_quality_tier"] for r in master}))
    check("planning statuses", all(r["dry_run_status"] == "prepared_no_call" and r["live_status"] == "not_run" and r["verification_status"] == "not_verified" for r in master))
    check("downstream statuses", all(r["download_status"] == "not_downloaded" and r["extraction_status"] == "not_extracted" and r["rating_status"] == "not_rated" and r["ingestion_status"] == "not_ingested" and r["codification_status"] == "not_codified" for r in master))
    check("claim boundary", all(r["causal_status"] == "not_causal_evidence" and r["global_analysis_readiness"] == "false" for r in master))
    check("coverage separate", municipality["locked_scout_target_count"] == 10000 and municipality["new_unique_municipalities_planned_count"] == 10000 and municipality["unique_municipalities_previously_scout_covered_count"] == 0)
    check("actual coverage stable", municipality["cumulative_scout_covered_municipalities_before_wave"] == 6919 and municipality["planned_rows_added_to_actual_map"] == 0 and municipality["projected_cumulative_scout_covered_municipalities_after_wave_if_all_parseable"] == 16919)
    check("no calls", all(preflight[key] == 0 for key in ["hosted_search_calls", "direct_sdk_calls", "external_smoke_calls", "url_opens", "verification_or_download_runs", "source_document_accesses", "candidate_review_runs", "extraction_rating_ingestion_codification_runs"]))
    check("invariants", invariants["all_invariants_passed"] is True and invariants["actual_coverage_before"] == invariants["actual_coverage_after_prep"] == 6919)
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    check("no live libraries", not ({"openai", "requests", "httpx", "urllib", "gabriel"} & imported))
    prompt = (OUT / "next_broad_state_4x2500_live_scout_prompt.md").read_text(encoding="utf-8")
    prompt_lower = prompt.lower()
    check("live prompt lanes", all(term.lower() in prompt_lower for term in ["2,500 targets, T+0", "2,500 targets, T+8", "2,500 targets, T+16", "2,500 targets, T+24", "checkpoints after every target", "candidate review remains deferred"]))
    check("future rating completeness", "Future rating tasks must verify all downstream summary inputs" in prompt)
    dashboard = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text(encoding="utf-8"))
    check("dashboard current", dashboard["current_phase"].startswith("Broad state 4 × 2,500 scout infrastructure prep complete"))
    check("dashboard planning", dashboard["planned_scout_target_ceiling"] == 10000 and dashboard["planned_scout_shard_count"] == 4 and dashboard["planned_scout_per_shard_ceiling"] == 2500)
    check("dashboard coverage stable", dashboard["current_scout_covered"] == 6919 and dashboard["current_candidate_queue_rows"] == 13041 and dashboard["dashboard_map_filter"] == "total_scout_coverage_only")
    check("dashboard readiness false", dashboard["global_analysis_readiness"] is False)
    with tempfile.TemporaryDirectory(prefix="broad-4x2500-prep-") as temp:
        rebuilt = Path(temp) / "rebuilt"
        subprocess.run([sys.executable, str(RUNNER), "--output-dir", str(rebuilt)], cwd=ROOT, check=True, capture_output=True, text=True)
        for name in ["broad_state_4x2500_scout_infrastructure_prep_decision.json", "broad_state_4x2500_scout_master_locked_queue.csv", "broad_state_4x2500_scout_master_lock.json"]:
            check(f"idempotent {name}", (rebuilt / name).read_bytes() == (OUT / name).read_bytes())
    print(f"broad state 4x2500 scout infrastructure prep tests: {len(checks)}/{len(checks)} passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
