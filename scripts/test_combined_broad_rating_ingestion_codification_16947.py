#!/usr/bin/env python3
"""Invariant tests for 16,947-record rating ingestion/codification."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28"
RATING = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
RUNNER = ROOT / "scripts/run_combined_broad_rating_ingestion_codification_16947.py"

BUCKETS = {
    "global_descriptive_ready", "global_descriptive_ready_with_caveats",
    "quant_needs_normalization", "mechanism_summary_ready",
    "source_navigation_only", "local_context_only", "weak_or_not_supported",
    "directional_hint_only", "provisional_causal_hint_only",
}
LAYERS = {
    "quantitative_compensation_availability", "quantitative_needs_normalization",
    "direct_base_wage_value", "non_base_compensation", "mechanism_summary",
    "implementation_timing", "automatic_raise_cola_percentage",
    "bargaining_dispute_resolution", "market_comparability", "fiscal_constraint",
    "safety_non_safety_directional_hint", "source_navigation",
    "local_context_only", "weak_or_not_supported", "provisional_causal_hint",
}
BOXES = {
    "quantitative_compensation_evidence", "direct_base_wage_value_evidence",
    "non_base_compensation_evidence", "contract_timing_implementation_evidence",
    "automatic_raise_cola_percentage_evidence",
    "bargaining_dispute_resolution_evidence", "market_comparability_evidence",
    "fiscal_constraint_evidence", "safety_non_safety_directional_hints",
    "source_navigation_references", "weak_context_not_supported_material",
    "quarantined_excluded_material",
}

REQUIRED = [
    "combined_broad_rating_ingestion_codification_16947_decision.json",
    "combined_broad_rating_ingestion_codification_16947_summary.md",
    "combined_broad_rating_ingestion_codification_16947_preflight_report.md",
    "combined_broad_rating_ingestion_codification_16947_preflight_checks.json",
    "combined_broad_rating_ingestion_codification_16947_locked_queue.csv",
    "combined_broad_rating_ingestion_codification_16947_locked_queue_summary.json",
    "combined_broad_rating_ingestion_codification_16947_lock.json",
    "combined_broad_rating_ingestion_codification_16947_codified_records.csv",
    "combined_broad_rating_ingestion_codification_16947_codified_records_summary.json",
    "combined_broad_rating_ingestion_codification_16947_ingested_records.csv",
    "combined_broad_rating_ingestion_codification_16947_ingested_records_summary.json",
    "combined_broad_rating_ingestion_codification_16947_excluded_quarantines_reference.csv",
    "combined_broad_rating_ingestion_codification_16947_excluded_quarantines_reference_summary.json",
    "combined_broad_rating_ingestion_codification_16947_analysis_layer_summary.json",
    "combined_broad_rating_ingestion_codification_16947_claim_readiness_summary.json",
    "combined_broad_rating_ingestion_codification_16947_dashboard_evidence_box_summary.json",
    "combined_broad_rating_ingestion_codification_16947_quant_normalization_need_summary.json",
    "combined_broad_rating_ingestion_codification_16947_mechanism_summary_ready_summary.json",
    "combined_broad_rating_ingestion_codification_16947_directional_hint_summary.json",
    "combined_broad_rating_ingestion_codification_16947_global_descriptive_candidate_summary.json",
    "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_input_manifest.csv",
    "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_input_summary.json",
    "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_inputs.md",
    "combined_broad_rating_ingestion_codification_16947_global_readiness_blockers.md",
    "combined_broad_rating_ingestion_codification_16947_global_readiness_candidate_flags.json",
    "combined_broad_rating_ingestion_codification_16947_dashboard_update_summary.json",
    "dashboard_overview_metric_sync_after_ingestion_codification.json",
    "dashboard_stale_overview_guard_after_ingestion_codification.json",
    "combined_broad_rating_ingestion_codification_16947_invariant_checks.json",
    "combined_broad_rating_ingestion_codification_16947_validation_2026-07-28.md",
    "combined_broad_rating_ingestion_codification_16947_stress_test_report.md",
    "combined_broad_rating_ingestion_codification_16947_regression_test_inventory.json",
    "next_global_analysis_readiness_gate_prompt.md", "next_task.md",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    checks: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    check("required outputs", all((OUT / name).is_file() for name in REQUIRED))
    for number, expected in enumerate([4237, 4237, 4237, 4236], 1):
        check(f"lane {number} queue files", all((OUT / name).is_file() for name in [
            f"combined_broad_rating_ingestion_codification_lane_{number:03d}_locked_queue.csv",
            f"combined_broad_rating_ingestion_codification_lane_{number:03d}_locked_queue_summary.json",
            f"combined_broad_rating_ingestion_codification_lane_{number:03d}_lock.json",
            f"lanes/ingestion_lane_{number:03d}/lane_{number:03d}_codified_records.csv",
            f"lanes/ingestion_lane_{number:03d}/lane_{number:03d}_codified_records_summary.json",
            f"lanes/ingestion_lane_{number:03d}/lane_{number:03d}_checkpoint.json",
            f"lanes/ingestion_lane_{number:03d}/lane_{number:03d}_errors.csv",
            f"lanes/ingestion_lane_{number:03d}/lane_{number:03d}_resume_state.json",
        ]))
        check(f"lane {number} count", len(read_csv(OUT / f"combined_broad_rating_ingestion_codification_lane_{number:03d}_locked_queue.csv")) == expected)

    decision = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_decision.json")
    preflight = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_preflight_checks.json")
    invariants = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_invariant_checks.json")
    readiness = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_claim_readiness_summary.json")
    boxes = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_dashboard_evidence_box_summary.json")
    layers = read_json(OUT / "combined_broad_rating_ingestion_codification_16947_analysis_layer_summary.json")
    queue = read_csv(OUT / "combined_broad_rating_ingestion_codification_16947_locked_queue.csv")
    records = read_csv(OUT / "combined_broad_rating_ingestion_codification_16947_codified_records.csv")
    ingested = read_csv(OUT / "combined_broad_rating_ingestion_codification_16947_ingested_records.csv")
    excluded = read_csv(OUT / "combined_broad_rating_ingestion_codification_16947_excluded_quarantines_reference.csv")
    quarantine = read_csv(RATING / "combined_broad_exact_span_rating_17259_quarantine.csv")
    check("decision", decision["decision"] == "combined_broad_rating_ingestion_codification_16947_completed_global_gate_ready")
    check("preflight", preflight["passed"] is True)
    check("counts", len(queue) == len(records) == len(ingested) == 16947 and len(excluded) == len(quarantine) == 312)
    check("reconciliation", 16947 + 312 == 17259)
    check("queue identities", len({row["span_rating_id"] for row in queue}) == 16947)
    check("master lane union", {row["span_rating_id"] for row in queue} == {
        row["span_rating_id"] for number in range(1, 5)
        for row in read_csv(OUT / f"combined_broad_rating_ingestion_codification_lane_{number:03d}_locked_queue.csv")
    })
    check("no quarantine leakage", not ({row["span_extraction_id"] for row in records} & {row["span_extraction_id"] for row in quarantine}))
    check("controlled buckets", {row["claim_readiness_bucket"] for row in records} <= BUCKETS and sum(readiness["counts"].values()) == 16947)
    check("controlled layers", {row["analysis_layer"] for row in records} <= LAYERS and set(layers["controlled_values"]) == LAYERS)
    check("controlled boxes", {row["dashboard_evidence_box"] for row in records} <= BOXES and set(boxes["counts"]) == BOXES and sum(boxes["counts"].values()) == 16947)
    check("dashboard excluded box", sum(boxes["dashboard_display_counts"].values()) == 17259 and boxes["dashboard_display_counts"]["quarantined_excluded_material"] == 312)
    check("durable statuses", all(row["ingestion_status"] == "ingested" and row["codification_status"] == "codified" for row in records))
    check("claim boundaries", all(row["no_wage_gap_claim"] == row["no_final_causal_claim"] == "true" and row["global_analysis_readiness"] == "false" and row["causal_status"] == "not_causal_evidence" for row in records))
    check("quant boundary", all(row["normalization_status"] == "not_normalized" for row in records if row["needs_quant_normalization"] == "true"))
    check("source-navigation boundary", all(row["analysis_layer"] == "source_navigation" and row["global_descriptive_candidate"] == "false" for row in records if row["source_navigation_only_flag"] == "true"))
    check("direction boundary", all(row["global_descriptive_candidate"] == "false" for row in records if row["directional_hint_only_flag"] == "true"))
    check("all invariants", invariants["all_invariants_passed"] is True and invariants["global_analysis_readiness_false"] is True)

    runner_source = RUNNER.read_text(encoding="utf-8").lower()
    check("no model or network imports", all(term not in runner_source for term in ["import openai", "import requests", "urllib", "gabriel.codify"]))
    check("no retained or extracted full-text access", all(term not in runner_source for term in ["local_extracted_text", "local_retained_sources", "retained_file_path"]))
    check("future prompt boundaries", all(term in (OUT / "next_global_analysis_readiness_gate_prompt.md").read_text(encoding="utf-8") for term in ["16,947", "312", "Do not normalize", "total-scout-coverage-only map", "reconstruct it deterministically"]))

    dashboard = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    check("dashboard current operation", dashboard["current_phase"].startswith("Combined broad rating ingestion/codification complete"))
    check("dashboard codification metrics", dashboard["rating_ingestion_queue_count"] == dashboard["rating_ingested_record_count"] == dashboard["rating_codified_record_count"] == 16947)
    check("dashboard gate", dashboard["global_readiness_gate_status"] == "ready_for_dedicated_diagnostic_gate")
    check("dashboard map stable", dashboard["current_scout_covered"] == 6919 and dashboard["map_data_date"] == "2026-07-27")

    with tempfile.TemporaryDirectory(prefix="rating-codification-16947-") as temporary:
        rebuilt = Path(temporary) / "rebuilt"
        subprocess.run([sys.executable, str(RUNNER), "--output-dir", str(rebuilt)], cwd=ROOT, check=True, capture_output=True, text=True)
        for name in [
            "combined_broad_rating_ingestion_codification_16947_decision.json",
            "combined_broad_rating_ingestion_codification_16947_locked_queue.csv",
            "combined_broad_rating_ingestion_codification_16947_codified_records.csv",
            "combined_broad_rating_ingestion_codification_16947_invariant_checks.json",
        ]:
            check(f"idempotent {name}", (rebuilt / name).read_bytes() == (OUT / name).read_bytes())

    print(f"combined broad rating ingestion/codification 16947 tests: {len(checks)}/{len(checks)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
