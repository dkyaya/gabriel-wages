#!/usr/bin/env python3
"""Invariant tests for the deterministic 16,947-valid-rating summary."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-SUMMARY-16947-VALID-RATINGS-2026-07-28"
RATING = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
RUNNER = ROOT / "scripts/run_combined_broad_exact_span_rating_summary_16947.py"

BUCKETS = {
    "global_descriptive_ready", "global_descriptive_ready_with_caveats",
    "quant_needs_normalization", "mechanism_summary_ready",
    "source_navigation_only", "local_context_only", "weak_or_not_supported",
    "directional_hint_only", "provisional_causal_hint_only",
}
BOXES = {
    "quantitative_compensation_evidence", "direct_base_wage_value_evidence",
    "non_base_compensation_evidence", "contract_timing_implementation_evidence",
    "automatic_raise_cola_percentage_increase_evidence",
    "bargaining_dispute_resolution_evidence", "market_comparability_evidence",
    "fiscal_constraint_evidence", "safety_non_safety_directional_hints",
    "source_navigation_references", "weak_context_not_supported_material",
    "quarantined_excluded_material",
}

REQUIRED = [
    "combined_broad_exact_span_rating_summary_16947_decision.json",
    "combined_broad_exact_span_rating_summary_16947_summary.md",
    "combined_broad_exact_span_rating_summary_16947_input_reconciliation.csv",
    "combined_broad_exact_span_rating_summary_16947_input_reconciliation_summary.json",
    "combined_broad_exact_span_rating_summary_16947_quarantine_exclusion_note.md",
    "combined_broad_exact_span_rating_summary_16947_by_evidence_family.csv",
    "combined_broad_exact_span_rating_summary_16947_by_evidence_family_summary.json",
    "combined_broad_exact_span_rating_summary_16947_by_mechanism.csv",
    "combined_broad_exact_span_rating_summary_16947_by_mechanism_summary.json",
    "combined_broad_exact_span_rating_summary_16947_by_quantitative_label.csv",
    "combined_broad_exact_span_rating_summary_16947_by_quantitative_label_summary.json",
    "combined_broad_exact_span_rating_summary_16947_claim_relevance.csv",
    "combined_broad_exact_span_rating_summary_16947_claim_relevance_summary.json",
    "combined_broad_exact_span_rating_summary_16947_evidence_strength.csv",
    "combined_broad_exact_span_rating_summary_16947_evidence_strength_summary.json",
    "combined_broad_exact_span_rating_summary_16947_direction_of_pressure.csv",
    "combined_broad_exact_span_rating_summary_16947_direction_of_pressure_summary.json",
    "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets.csv",
    "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets_summary.json",
    "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.md",
    "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.json",
    "combined_broad_exact_span_rating_summary_16947_global_claim_candidate_table.csv",
    "combined_broad_exact_span_rating_summary_16947_dashboard_filter_plan.json",
    "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments.csv",
    "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments_summary.json",
    "combined_broad_exact_span_rating_summary_16947_dashboard_metric_contract.json",
    "combined_broad_exact_span_rating_summary_16947_dashboard_claim_boundary_contract.json",
    "combined_broad_exact_span_rating_summary_16947_state_summary.json",
    "combined_broad_exact_span_rating_summary_16947_region_summary.json",
    "combined_broad_exact_span_rating_summary_16947_municipality_summary.json",
    "combined_broad_exact_span_rating_summary_16947_source_family_summary.json",
    "combined_broad_exact_span_rating_summary_16947_invariant_checks.json",
    "combined_broad_exact_span_rating_summary_16947_validation_2026-07-28.md",
    "next_combined_broad_ingestion_codification_prompt.md",
    "next_task.md",
]
for bucket in BUCKETS:
    REQUIRED.extend([
        f"combined_broad_exact_span_rating_summary_16947_{bucket}.csv",
        f"combined_broad_exact_span_rating_summary_16947_{bucket}_summary.json",
    ])


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    checks = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    check("required outputs", all((OUT / name).is_file() for name in REQUIRED))
    decision = read_json(OUT / "combined_broad_exact_span_rating_summary_16947_decision.json")
    reconciliation = read_json(OUT / "combined_broad_exact_span_rating_summary_16947_input_reconciliation_summary.json")
    bucket_summary = read_json(OUT / "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets_summary.json")
    box_summary = read_json(OUT / "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments_summary.json")
    invariants = read_json(OUT / "combined_broad_exact_span_rating_summary_16947_invariant_checks.json")
    rows = read_csv(OUT / "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets.csv")
    assignments = read_csv(OUT / "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments.csv")
    valid = read_csv(RATING / "combined_broad_exact_span_rating_17259_valid_ratings.csv")
    quarantine = read_csv(RATING / "combined_broad_exact_span_rating_17259_quarantine.csv")

    check("decision", decision["decision"] == "combined_broad_exact_span_rating_summary_16947_completed_ingestion_ready")
    check("valid input count", len(valid) == len(rows) == 16947)
    check("quarantine count", len(quarantine) == 312)
    check("input reconciliation", reconciliation["reconciles"] is True and 16947 + 312 == 17259)
    check("quarantine excluded", reconciliation["quarantine_excluded_from_valid_statistics"] is True)
    valid_ids = {row["span_rating_id"] for row in valid}
    summary_ids = {row["span_rating_id"] for row in rows}
    quarantine_span_ids = {row["span_extraction_id"] for row in quarantine}
    check("valid scope identity", valid_ids == summary_ids and len(summary_ids) == 16947)
    check("no quarantine leakage", not ({row["span_extraction_id"] for row in rows} & quarantine_span_ids))
    check("controlled buckets", {row["claim_readiness_bucket"] for row in rows} <= BUCKETS)
    check("bucket union", sum(bucket_summary["counts"].values()) == 16947)
    for bucket in BUCKETS:
        subset = read_csv(OUT / f"combined_broad_exact_span_rating_summary_16947_{bucket}.csv")
        check(f"bucket subset {bucket}", len(subset) == bucket_summary["counts"].get(bucket, 0) and all(row["claim_readiness_bucket"] == bucket for row in subset))
    check("dashboard assignment reconciliation", len(assignments) == 17259 and box_summary["valid_assignment_count"] == 16947 and box_summary["quarantine_assignment_count"] == 312)
    check("controlled boxes", set(box_summary["all_box_counts"]) == BOXES and sum(box_summary["valid_box_counts"].values()) == 16947)
    check("quarantine box", box_summary["all_box_counts"]["quarantined_excluded_material"] == 312)
    check("quant normalization boundary", all(row["needs_normalization"] == "true" for row in rows if row["claim_readiness_bucket"] == "quant_needs_normalization"))
    check("direction boundary", all(row["direction_of_pressure"] in {"safety_advantage", "non_safety_advantage", "gap_narrowing"} for row in rows if row["claim_readiness_bucket"] == "directional_hint_only"))
    check("global readiness false", decision["global_analysis_readiness"] is False and invariants["global_analysis_readiness_false"] is True and all(row["global_analysis_readiness"] == "false" for row in rows))
    source = RUNNER.read_text(encoding="utf-8")
    check("no model/network implementation", "import openai" not in source.lower() and "import requests" not in source.lower() and "urllib" not in source.lower())
    check("no source/full-text paths", "local_extracted_text" not in source and "local_retained_sources" not in source and "retained_file_path" not in source)
    prompt = (OUT / "next_combined_broad_ingestion_codification_prompt.md").read_text(encoding="utf-8")
    check("future prompt boundaries", all(term in prompt for term in ["Exclude all 312 quarantines", "Do not normalize", "global analysis readiness true", "total-scout-coverage-only map", "reconstruct any fully derivable missing artifact"]))
    dashboard = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    check("dashboard current operation", dashboard["current_phase"].startswith((
        "Combined broad exact-span rating summary complete",
        "Combined broad rating ingestion/codification complete",
    )))
    check("dashboard metrics", dashboard["rating_summary_valid_count"] == 16947 and dashboard["rating_summary_quarantine_excluded_count"] == 312)
    check("dashboard map count stable", dashboard["current_scout_covered"] == 6919 and dashboard["map_data_date"] == "2026-07-27")

    with tempfile.TemporaryDirectory(prefix="rating-summary-16947-") as temporary:
        rebuilt = Path(temporary) / "rebuilt"
        subprocess.run([sys.executable, str(RUNNER), "--output-dir", str(rebuilt)], cwd=ROOT, check=True, capture_output=True, text=True)
        for name in [
            "combined_broad_exact_span_rating_summary_16947_decision.json",
            "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets_summary.json",
            "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments_summary.json",
            "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.json",
        ]:
            check(f"idempotent {name}", (rebuilt / name).read_bytes() == (OUT / name).read_bytes())

    print(f"combined broad exact-span rating summary 16947 tests: {len(checks)}/{len(checks)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
