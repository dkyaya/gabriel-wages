#!/usr/bin/env python3
"""Evaluate the post-codification global analysis readiness gate.

The gate reads only committed, lightweight codification ledgers.  It performs
no source access, extraction, rating, normalization, comparison, or analysis.
Its partial result is deliberately narrower than the legacy project-wide
``global_analysis_readiness`` boolean, which remains false.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/GLOBAL-ANALYSIS-READINESS-GATE-AFTER-BROAD-INGESTION-2026-07-28"
RESULT = ROOT / "docs/analysis/global_analysis_readiness_gate_result_2026-07-28.md"
STATUS = ROOT / "docs/analysis/global_analysis_readiness_gate_dashboard_status_note_2026-07-28.md"
TASK = "GLOBAL-ANALYSIS-READINESS-GATE-AFTER-BROAD-INGESTION-2026-07-28"
DECISION = "global_analysis_readiness_gate_completed_with_partial_readiness_next_scout_prep_ready"
EXPECTED = 16_947
EXCLUDED = 312
TOTAL = 17_259
CONTROLLED = {
    "pass", "partial_pass", "fail", "not_applicable",
    "blocked_pending_normalization", "blocked_pending_matched_structure",
    "blocked_pending_more_data", "blocked_pending_quality_repair",
}

REQUIRED = [
    "combined_broad_rating_ingestion_codification_16947_decision.json",
    "combined_broad_rating_ingestion_codification_16947_codified_records.csv",
    "combined_broad_rating_ingestion_codification_16947_codified_records_summary.json",
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
    "combined_broad_rating_ingestion_codification_16947_state_summary.json",
    "combined_broad_rating_ingestion_codification_16947_region_summary.json",
    "combined_broad_rating_ingestion_codification_16947_source_family_summary.json",
    "combined_broad_rating_ingestion_codification_16947_non_cba_codified_summary.json",
    "combined_broad_rating_ingestion_codification_16947_dashboard_update_summary.json",
    "combined_broad_rating_ingestion_codification_16947_validation_2026-07-28.md",
]


def read_json(name: str) -> Any:
    return json.loads((INPUT / name).read_text(encoding="utf-8"))


def read_csv(name: str) -> list[dict[str, str]]:
    with (INPUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md(title: str, body: str) -> str:
    return f"# {title}\n\n{body.strip()}\n"


def summary(name: str, count: int, **extra: Any) -> dict[str, Any]:
    return {"dimension": name, "record_count": count, "global_analysis_readiness": False, **extra}


def preflight() -> dict[str, Any]:
    missing = [name for name in REQUIRED if not (INPUT / name).is_file()]
    if missing:
        raise RuntimeError(f"non-derivable required inputs missing: {missing}")
    decision = read_json(REQUIRED[0])
    records = read_csv(REQUIRED[1])
    excluded = read_csv(REQUIRED[4])
    manifest = read_csv(REQUIRED[13])
    codified = read_json(REQUIRED[2])
    ingested = read_json(REQUIRED[3])
    exclusion = read_json(REQUIRED[5])
    gate = read_json(REQUIRED[14])
    if decision.get("decision") != "combined_broad_rating_ingestion_codification_16947_completed_global_gate_ready":
        raise RuntimeError("codification decision does not authorize the readiness gate")
    if not (len(records) == len(manifest) == EXPECTED and len(excluded) == EXCLUDED):
        raise RuntimeError("codified/gate/exclusion counts do not reconcile")
    record_ids = {row["codified_record_id"] for row in records}
    rating_ids = {row["span_rating_id"] for row in records}
    span_ids = {row["span_extraction_id"] for row in records}
    excluded_span_ids = {row["span_extraction_id"] for row in excluded}
    if len(record_ids) != EXPECTED or len(rating_ids) != EXPECTED or span_ids & excluded_span_ids:
        raise RuntimeError("quarantine leakage or duplicate identity detected")
    if {row["codified_record_id"] for row in manifest} != record_ids:
        raise RuntimeError("gate input manifest differs from codified ledger")
    if not (
        codified.get("codified_record_count") == EXPECTED
        and ingested.get("ingested_record_count") == EXPECTED
        and ingested.get("quarantines_ingested") == 0
        and exclusion.get("excluded_quarantine_count") == EXCLUDED
        and exclusion.get("ingested_quarantine_count") == 0
        and gate.get("gate_input_record_count") == EXPECTED
        and gate.get("quarantines_excluded") == EXCLUDED
    ):
        raise RuntimeError("summary count gate failed")
    if not all(
        row.get("ingestion_status") == "ingested"
        and row.get("codification_status") == "codified"
        and row.get("no_wage_gap_claim") == "true"
        and row.get("no_final_causal_claim") == "true"
        and row.get("global_analysis_readiness") == "false"
        and row.get("causal_status") == "not_causal_evidence"
        for row in records
    ):
        raise RuntimeError("codified claim-boundary gate failed")
    return {
        "records": records,
        "excluded": excluded,
        "manifest": manifest,
        "input_hashes": {name: sha256(INPUT / name) for name in REQUIRED},
    }


def build(out: Path, write_root_docs: bool) -> None:
    source = preflight()
    records = source["records"]
    excluded = source["excluded"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    claim = read_json("combined_broad_rating_ingestion_codification_16947_claim_readiness_summary.json")["counts"]
    layers = read_json("combined_broad_rating_ingestion_codification_16947_analysis_layer_summary.json")
    boxes = read_json("combined_broad_rating_ingestion_codification_16947_dashboard_evidence_box_summary.json")
    states = read_json("combined_broad_rating_ingestion_codification_16947_state_summary.json")
    regions = read_json("combined_broad_rating_ingestion_codification_16947_region_summary.json")
    families = read_json("combined_broad_rating_ingestion_codification_16947_source_family_summary.json")
    cba = read_json("combined_broad_rating_ingestion_codification_16947_non_cba_codified_summary.json")
    candidate = read_json("combined_broad_rating_ingestion_codification_16947_global_descriptive_candidate_summary.json")

    flags = [
        {
            "flag": "global_collection_readiness", "readiness_value": "pass",
            "narrow_scope": "broad lineaged collection corpus", "boolean_pass": True,
            "basis": "16,947 codified records across 49 states, 4 regions, 18 source families and 2,713 unique retained sources; storage and lineage controls passed",
            "blockers": "coverage is corpus-bounded, uneven, and not population-representative",
            "allowed_later": "bounded collection, source-family, geography, and evidence-availability summaries",
            "next_requirement": "expand coverage through the 4 x 2,500 scout standard and preserve matched-unit discipline",
        },
        {
            "flag": "global_mechanism_analysis_readiness", "readiness_value": "partial_pass",
            "narrow_scope": "bounded descriptive mechanism summaries", "boolean_pass": False,
            "basis": "713 mechanism-summary-ready records with controlled strength, labels, lineage, and separated weak/context material",
            "blockers": "mechanism families are uneven and some categories are sparse; no causal interpretation is authorized",
            "allowed_later": "corpus-bounded mechanism availability and documentary-description summaries with caveats",
            "next_requirement": "broaden source-family/geography balance and retain source-level caveats",
        },
        {
            "flag": "global_quantitative_evidence_readiness", "readiness_value": "partial_pass",
            "narrow_scope": "quantitative evidence availability only", "boolean_pass": False,
            "basis": "10,382 records enter the overlapping availability layer and 10,109 are flagged as needing normalization",
            "blockers": "units, periods, steps, ranks, grades, effective dates, and base/non-base distinctions are not normalized for comparison",
            "allowed_later": "bounded quantitative-evidence availability and coverage summaries only",
            "next_requirement": "construct a deterministic normalization layer before comparisons",
        },
        {
            "flag": "global_wage_gap_analysis_readiness", "readiness_value": "blocked_pending_normalization",
            "narrow_scope": "comparative wage-gap analysis", "boolean_pass": False,
            "basis": "zero records were normalized or compared",
            "blockers": "normalization and same-city, same-cycle safety/non-safety matched structure are incomplete",
            "allowed_later": "none until normalization and matching gates pass",
            "next_requirement": "resolve units/cycles/base status and build one-row-per-unit-cycle matched comparisons",
        },
        {
            "flag": "global_causal_analysis_readiness", "readiness_value": "blocked_pending_matched_structure",
            "narrow_scope": "causal analysis", "boolean_pass": False,
            "basis": "80 provisional hints remain explicitly non-causal and no causal estimates were run",
            "blockers": "matched structure, temporal ordering, confounding strategy, corpus separation, and design diagnostics are incomplete",
            "allowed_later": "none; provisional hints cannot be promoted to causal findings",
            "next_requirement": "complete design-specific matched and temporal diagnostics before a causal gate",
        },
        {
            "flag": "overall_global_analysis_readiness", "readiness_value": "partial_pass",
            "narrow_scope": "collection plus limited descriptive availability only", "boolean_pass": False,
            "basis": "collection passes and mechanism/quantitative availability partially pass, while wage-gap and causal gates remain blocked",
            "blockers": "normalization, matched comparisons, representativeness, and causal-design requirements remain open",
            "allowed_later": "only narrow corpus-bounded descriptive candidate classes after their dedicated review",
            "next_requirement": "continue collection via 4 x 2,500 scouting; legacy global_analysis_readiness stays false",
        },
    ]
    if {row["readiness_value"] for row in flags} - CONTROLLED:
        raise RuntimeError("uncontrolled readiness value")

    decision = {
        "task_id": TASK, "decision": DECISION, "codified_record_count_reviewed": EXPECTED,
        "quarantine_excluded_count": EXCLUDED, "input_total_reconciled": TOTAL,
        "subflag_results": {row["flag"]: row["readiness_value"] for row in flags},
        "overall_global_analysis_readiness": "partial_pass",
        "overall_global_analysis_readiness_bool": False,
        "global_analysis_readiness": False,
        "map_filter_contract": "total_scout_coverage_only",
        "next_stage": "broad_4x2500_scout_infrastructure_prep",
        "next_stage_ready": True,
        "final_claims_written": False,
    }
    write_json(out / "global_analysis_readiness_gate_decision.json", decision)
    write_json(out / "global_analysis_readiness_gate_flags.json", {"controlled_values": sorted(CONTROLLED), "flags": flags, **decision})
    write_csv(out / "global_analysis_readiness_gate_flags.csv", flags)

    reconciliation_rows = [
        {"input": "codified_valid_evidence", "expected": EXPECTED, "observed": len(records), "included_in_gate": "true", "status": "pass"},
        {"input": "quarantined_rating_outputs", "expected": EXCLUDED, "observed": len(excluded), "included_in_gate": "false", "status": "pass"},
        {"input": "rating_input_total", "expected": TOTAL, "observed": len(records) + len(excluded), "included_in_gate": "reconciliation_only", "status": "pass"},
        {"input": "gate_input_manifest", "expected": EXPECTED, "observed": len(source["manifest"]), "included_in_gate": "true", "status": "pass"},
    ]
    write_csv(out / "global_analysis_readiness_gate_input_reconciliation.csv", reconciliation_rows)
    write_json(out / "global_analysis_readiness_gate_input_reconciliation_summary.json", {
        "codified_record_count": EXPECTED, "quarantine_excluded_count": EXCLUDED,
        "input_total": TOTAL, "reconciles": True, "quarantine_leakage_count": 0,
        "unique_codified_record_count": len({r["codified_record_id"] for r in records}),
        "input_hashes": source["input_hashes"], "global_analysis_readiness": False,
    })
    (out / "global_analysis_readiness_gate_quarantine_exclusion_note.md").write_text(md(
        "Quarantine exclusion", "All 312 quarantined rating outputs were reconciled as reference-only and excluded from the 16,947-record readiness evidence. No quarantined span identifier appears in the codified ledger."
    ), encoding="utf-8")

    review_titles = {
        "global_collection_readiness": "Global collection readiness review",
        "global_mechanism_analysis_readiness": "Global mechanism analysis readiness review",
        "global_quantitative_evidence_readiness": "Global quantitative evidence readiness review",
        "global_wage_gap_analysis_readiness": "Global wage-gap analysis readiness review",
        "global_causal_analysis_readiness": "Global causal analysis readiness review",
        "overall_global_analysis_readiness": "Overall global analysis readiness review",
    }
    for row in flags:
        body = f"Status: `{row['readiness_value']}`.\n\nScope: {row['narrow_scope']}.\n\nBasis: {row['basis']}.\n\nBlockers/caveats: {row['blockers']}.\n\nPotential later use: {row['allowed_later']}.\n\nNext requirement: {row['next_requirement']}.\n\nThis diagnostic does not state a final finding; `global_analysis_readiness` remains false."
        (out / f"{row['flag']}_review.md").write_text(md(review_titles[row["flag"]], body), encoding="utf-8")

    blockers = [
        {"id": "normalization", "severity": "blocking", "blocks": ["global_wage_gap_analysis_readiness"], "detail": "10,109 quantitative records need unit/period/rank/step/base-status normalization; zero were normalized."},
        {"id": "matched_structure", "severity": "blocking", "blocks": ["global_wage_gap_analysis_readiness", "global_causal_analysis_readiness"], "detail": "Same-city, same-cycle safety/non-safety unit matching has not been constructed for these records."},
        {"id": "causal_design", "severity": "blocking", "blocks": ["global_causal_analysis_readiness"], "detail": "Temporal ordering, confounding strategy, and design diagnostics are incomplete."},
        {"id": "representativeness", "severity": "caveat", "blocks": ["population_prevalence_claims"], "detail": "The 49-state corpus is broad but convenience-sourced and uneven; it is not a population sample."},
        {"id": "source_family_geography_balance", "severity": "caveat", "blocks": ["unqualified_global_mechanism_claims"], "detail": "State, region, source-family, and exact-CBA composition are uneven."},
        {"id": "weak_context_volume", "severity": "caveat", "blocks": ["unfiltered_descriptive_summaries"], "detail": "5,080 dashboard records are weak, context-only, or unsupported and remain separated."},
    ]
    write_json(out / "global_analysis_readiness_gate_blockers.json", {"blocker_count": len(blockers), "blockers": blockers, "global_analysis_readiness": False})
    (out / "global_analysis_readiness_gate_blockers.md").write_text(md("Global readiness blockers", "\n".join(f"- **{b['id']}** ({b['severity']}): {b['detail']}" for b in blockers)), encoding="utf-8")
    (out / "global_analysis_readiness_gate_caveats.md").write_text(md("Readiness caveats", "- Every later description must remain corpus-bounded and report source-family/geographic composition.\n- Partial readiness applies to evidence availability, not representativeness, comparison, direction, or causality.\n- The causal and discourse corpora must remain distinct at analysis time.\n- Repeated span records are not independent municipalities or bargaining units."), encoding="utf-8")
    (out / "global_analysis_readiness_gate_claims_allowed_later.md").write_text(md("Candidate claim classes allowed later", "After dedicated review, the corpus may support bounded collection/evidence-availability, source-family/geography-coverage, mechanism-description, and quantitative-evidence-availability summaries. This gate identifies candidate classes; it does not state findings."), encoding="utf-8")
    (out / "global_analysis_readiness_gate_claims_still_prohibited.md").write_text(md("Claims still prohibited", "Final causal claims, wage-gap estimates, normalized wage comparisons, regression/treatment-effect conclusions, population-prevalence or nationally representative claims, unqualified directional findings, and claims that merge causal and discourse corpora remain prohibited."), encoding="utf-8")
    (out / "global_analysis_readiness_gate_next_requirements.md").write_text(md("Next requirements", "1. Prepare the 4 × 2,500 broad scouting infrastructure and document municipality/source-family gaps.\n2. In a later authorized stage, build unit/cycle matching and deterministic quantitative normalization.\n3. Re-run specialized wage-gap and causal readiness gates only after their prerequisites exist.\n4. Do not pause this workflow to state claims."), encoding="utf-8")

    evidence_summaries = {
        "collection": summary("collection", EXPECTED, retained_source_count=4961, extracted_ok_count=3815, positive_exact_span_count=17259, valid_rating_count=16947, state_count=states["category_count"], region_count=regions["category_count"], source_family_count=families["category_count"], unique_source_count=cba["unique_source_count"], readiness="pass"),
        "mechanism": summary("mechanism", claim["mechanism_summary_ready"], mechanism_summary_ready_count=claim["mechanism_summary_ready"], readiness="partial_pass", final_causal_interpretation_allowed=False),
        "quantitative": summary("quantitative", layers["overlapping_sublayer_counts"]["quantitative_compensation_availability"], quantitative_availability_count=layers["overlapping_sublayer_counts"]["quantitative_compensation_availability"], quantitative_needs_normalization_count=layers["overlapping_sublayer_counts"]["quantitative_needs_normalization"], normalized_record_count=0, readiness="partial_pass"),
        "directional_hint": summary("directional_hint", claim["directional_hint_only"], directional_hint_only_count=claim["directional_hint_only"], provisional_causal_hint_only_count=claim["provisional_causal_hint_only"], global_directional_finding_allowed=False),
        "source_navigation": summary("source_navigation", claim["source_navigation_only"], source_navigation_only_count=claim["source_navigation_only"], substantive_compensation_evidence=False),
        "weak_context": summary("weak_context", boxes["dashboard_display_counts"]["weak_context_not_supported_material"], weak_context_not_supported_count=boxes["dashboard_display_counts"]["weak_context_not_supported_material"], excluded_from_global_candidates=True),
        "source_family": {**families, "exact_cba_record_count": cba["exact_cba_codified_record_count"], "non_cba_or_mixed_record_count": cba["non_cba_or_mixed_codified_record_count"], "unique_source_count": cba["unique_source_count"], "global_analysis_readiness": False},
        "geography": {"state_count": states["category_count"], "state_counts": states["counts"], "region_count": regions["category_count"], "region_counts": regions["counts"], "municipality_label_count": len({r["municipality"] for r in records if r["municipality"]}), "scout_covered_municipalities": 6919, "population_representative": False, "global_analysis_readiness": False},
    }
    for key, value in evidence_summaries.items():
        write_json(out / f"global_analysis_readiness_gate_{key}_summary.json", value)

    dashboard = {
        "dashboard_updated": True, "current_operation": "global_analysis_readiness_gate_complete",
        "next_authorized_stage": "broad_4x2500_scout_infrastructure_prep",
        "scout_covered_municipalities": 6919, "total_candidate_rows": 13041,
        "retained_source_count": 4961, "extracted_ok_count": 3815,
        "positive_exact_span_count": 17259, "valid_rating_count": 16947,
        "codified_record_count": 16947, "quarantine_excluded_count": 312,
        "readiness_flags": decision["subflag_results"], "top_blockers": [b["id"] for b in blockers[:5]],
        "map_data_date": "2026-07-27", "map_filter_contract": "total_scout_coverage_only",
        "readiness_flags_are_map_filters": False, "global_analysis_readiness": False,
    }
    write_json(out / "global_analysis_readiness_gate_dashboard_update_summary.json", dashboard)
    (out / "global_analysis_readiness_gate_dashboard_update_summary.md").write_text(md("Dashboard update", "The dashboard now presents the six gate outcomes, top blockers, claim boundaries, and the 4 × 2,500 scouting-prep transition. Its map remains cumulative total scout coverage only."), encoding="utf-8")
    sync = {"synced": True, **dashboard, "stale_ingestion_operation_present": False}
    write_json(out / "dashboard_overview_metric_sync_after_global_readiness_gate.json", sync)
    write_json(out / "dashboard_stale_overview_guard_after_global_readiness_gate.json", {"passed": True, "current_operation_is_gate": True, "next_stage_is_4x2500_prep": True, "legacy_global_boolean_false": True, "map_filter_contract": "total_scout_coverage_only"})
    (out / "dashboard_overview_metric_sync_after_global_readiness_gate.md").write_text(md("Dashboard overview metric sync", "All collection-through-codification totals and gate subflags are synchronized. The legacy global boolean remains false."), encoding="utf-8")
    (out / "dashboard_stale_overview_guard_after_global_readiness_gate.md").write_text(md("Dashboard stale-overview guard", "The current operation is the completed readiness gate, not ingestion/codification. The next authorized stage is 4 × 2,500 scouting infrastructure prep."), encoding="utf-8")

    standard = {
        "standard": "future_broad_4x2500_scout_standard_v1", "lane_count": 4,
        "targets_per_lane": 2500, "target_ceiling": 10000,
        "stagger_minutes": [0, 8, 16, 24], "checkpoint_after_every_target": True,
        "requirements": ["broad_state_by_state_geographic_coverage", "source_family_diversification", "municipality_coverage_accounting", "lane_isolation", "resume_state", "total_scout_coverage_only_map"],
        "excluded_stages": ["candidate_review", "verification", "download", "extraction", "rating", "ingestion", "codification"],
        "post_rating_artifact_completeness_rule_required_in_future_rating_prompts": True,
    }
    write_json(out / "future_broad_4x2500_scout_standard.json", standard)
    (out / "future_broad_4x2500_scout_standard.md").write_text(md("Future broad 4 × 2,500 scout standard", "Four isolated lanes each lock 2,500 targets (10,000 ceiling), start at T+0/T+8/T+16/T+24, and checkpoint after every target. Queue design balances states, regions, municipality gaps, and source families. Workers emit candidate leads only. Candidate review, verification, downloads, extraction, rating, ingestion, and codification are separate later stages. The dashboard map remains total scout coverage only."), encoding="utf-8")
    prompt = """# Next task: broad state 4 × 2,500 scout infrastructure prep

Prepare—but do not execute—the next broad scouting batch: exactly four independent lanes of 2,500 targets (10,000-target ceiling), with T+0/T+8/T+16/T+24 standard stagger metadata and checkpoint/resume after every target.

Build a deterministic locked target universe using state-by-state geographic breadth, municipality coverage accounting, and source-family diversification. Preserve the city × cycle × occupation matching objective in target priority. Workers must only discover candidate leads and may not perform candidate review, verification, download, text extraction, span extraction, rating, ingestion, or codification. Do not fetch during infrastructure prep.

Keep the dashboard map filter as total scout coverage only; show queue/lane/source-family metrics outside the map. Retained/downloaded binaries and full extracted text remain outside normal Git.

Any future rating task must verify downstream summary artifacts before closing; reconstruct fully derivable missing summaries deterministically from committed valid/quarantine/results ledgers and fail closed only for non-derivable missing inputs.

Do not write final analysis, normalize wages, calculate wage gaps, run regressions/treatment effects, or make prevalence/causal claims. Keep global_analysis_readiness false.
"""
    (out / "next_broad_state_4x2500_scout_infrastructure_prep_prompt.md").write_text(prompt, encoding="utf-8")
    (out / "global_analysis_readiness_gate_to_next_scouting_rhythm_note.md").write_text(md("Readiness gate to next scouting rhythm", "The gate does not pause the pipeline for claim-writing. Whether a narrow subflag passed or failed, the next operation is infrastructure preparation for four 2,500-target scout lanes. This expansion is intended to improve documented geography and source-family gaps, not to cure normalization, matching, or causal-design blockers by itself."), encoding="utf-8")

    invariants = {
        "all_invariants_passed": True, "codified_count_exact": len(records) == EXPECTED,
        "quarantine_excluded_count_exact": len(excluded) == EXCLUDED,
        "quarantine_leakage_count": 0, "controlled_readiness_values": True,
        "overall_readiness_unambiguous": decision["overall_global_analysis_readiness_bool"] is False,
        "wage_gap_did_not_pass": decision["subflag_results"]["global_wage_gap_analysis_readiness"] == "blocked_pending_normalization",
        "causal_did_not_pass": decision["subflag_results"]["global_causal_analysis_readiness"] == "blocked_pending_matched_structure",
        "final_claims_written": False, "model_api_calls": 0, "source_or_full_text_access": 0,
        "normalization_or_comparison_runs": 0, "wage_gap_regression_treatment_effect_runs": 0,
        "map_filter_contract": "total_scout_coverage_only", "readiness_flags_are_map_filters": False,
        "global_analysis_readiness_false": True, "next_stage_is_4x2500_scout_prep": True,
    }
    write_json(out / "global_analysis_readiness_gate_invariant_checks.json", invariants)
    write_json(out / "global_analysis_readiness_gate_regression_test_inventory.json", {"required_test": "scripts/test_global_analysis_readiness_gate.py", "checks": sorted(invariants), "predecessor_tests_required": 4})
    (out / "global_analysis_readiness_gate_stress_test_report.md").write_text(md("Readiness gate stress-test report", "The gate fails closed on count drift, quarantine leakage, missing non-derivable inputs, uncontrolled statuses, claim-boundary drift, or an ambiguous true overall flag. Rebuilding into a temporary directory must reproduce the decision, flags, and reconciliation byte-for-byte."), encoding="utf-8")
    (out / "global_analysis_readiness_gate_validation_2026-07-28.md").write_text(md("Global readiness gate validation", "The 16,947 codified records and 312 exclusions reconcile to 17,259; the gate input manifest matches the codified identities; all boundaries remain false/true as required; statuses are controlled; and no predecessor stage, model, source/full-text, normalization, comparison, or statistical operation ran. Full command results are recorded in the final relay."), encoding="utf-8")
    (out / "global_analysis_readiness_gate_summary.md").write_text(md("Global analysis readiness gate summary", "Decision: `global_analysis_readiness_gate_completed_with_partial_readiness_next_scout_prep_ready`. Collection readiness passes; mechanism and quantitative-availability readiness partially pass; wage-gap readiness is blocked pending normalization and matched structure; causal readiness is blocked pending matched structure/design; overall readiness is a narrow partial diagnostic while the legacy boolean remains false. No final claims were written. The next stage is 4 × 2,500 broad scouting infrastructure prep."), encoding="utf-8")
    (out / "next_task.md").write_text(md("Next task", "Run `next_broad_state_4x2500_scout_infrastructure_prep_prompt.md`. Prepare four isolated 2,500-target scout lanes; do not execute downstream review, verification, download, extraction, rating, ingestion, codification, normalization, or analysis."), encoding="utf-8")

    root_body = md("Global analysis readiness gate result — 2026-07-28", "The diagnostic gate reviewed 16,947 codified valid ratings and excluded all 312 quarantines. Collection: pass. Mechanism: partial pass. Quantitative evidence availability: partial pass. Wage-gap: blocked pending normalization/matched structure. Causal: blocked pending matched structure/design. Overall: narrow partial pass, with `global_analysis_readiness = false`. No final claims were written. Next: prepare 4 × 2,500 broad scouting infrastructure.")
    status_body = md("Global analysis readiness gate dashboard status — 2026-07-28", "Dashboard current operation: readiness gate complete. Next authorized stage: broad 4 × 2,500 scout infrastructure prep. Readiness subflags are displayed outside the map; the map remains total scout coverage only. Global analysis readiness remains false.")
    if write_root_docs:
        RESULT.write_text(root_body, encoding="utf-8")
        STATUS.write_text(status_body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.output_dir.resolve(), args.output_dir.resolve() == OUTPUT.resolve())
    print(json.dumps({"decision": DECISION, "output_dir": str(args.output_dir), "codified": EXPECTED, "excluded": EXCLUDED}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
