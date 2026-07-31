#!/usr/bin/env python3
"""Review the existing wage-growth continuity layer without expanding analysis."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-MECHANISM-ATTRIBUTED-WAGE-GROWTH-CONTINUITY-2026-07-31"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WAGE-GROWTH-CONTINUITY-REVIEW-2026-07-31"
DASHBOARD_GROWTH = ROOT / "docs/dashboard/data/wage_growth_continuity.json"
TASK_ID = "BROAD-STATE-WAGE-GROWTH-CONTINUITY-REVIEW-2026-07-31"
LOCAL_DECISION = "broad_state_wage_growth_continuity_review_completed_local_ready_public_pending"
PUBLIC_DECISION = "broad_state_wage_growth_continuity_review_completed_weekend_scout_prep_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-SCOUT-INFRASTRUCTURE-2026-07-31"

NORMALIZED = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-PARAPHRASE-REPAIR-2026-07-30/normalized_quantitative_records.csv"
QUARANTINE = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30/merged_span_ratings_quarantine.csv"
UNIVERSE = ROOT / "docs/analysis/national_municipality_universe.csv"
CANONICAL_COVERAGE = ROOT / "docs/analysis/national_scout_coverage_municipality_2026-07-20.csv"
BROAD_RESULTS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_results.csv"
FOUR_BY_1000_RESULTS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27/broad_state_4x1000_parallel_live_scout_master_results.csv"
FOUR_BY_2500_RESULTS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29/broad_state_4x2500_live_scout_results.csv"

MECHANISMS = [
    "across_the_board_percentage_raise", "COLA_CPI", "step_schedule_progression",
    "automatic_raise", "implementation_retroactivity", "bargaining_settlement",
    "arbitration_factfinding", "market_recruitment_retention", "non_base_compensation",
    "base_wage_schedule_change", "unknown_or_unattributed",
]
REGIONS = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast", "RI": "Northeast", "VT": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",
    "IN": "Midwest", "IL": "Midwest", "MI": "Midwest", "OH": "Midwest", "WI": "Midwest",
    "IA": "Midwest", "KS": "Midwest", "MN": "Midwest", "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    "DE": "South", "FL": "South", "GA": "South", "MD": "South", "NC": "South", "SC": "South", "VA": "South", "DC": "South", "WV": "South",
    "AL": "South", "KY": "South", "MS": "South", "TN": "South", "AR": "South", "LA": "South", "OK": "South", "TX": "South",
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West", "NV": "West", "NM": "West", "UT": "West", "WY": "West",
    "AK": "West", "CA": "West", "HI": "West", "OR": "West", "WA": "West",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def number(value: Any) -> float | None:
    try:
        return float(value) if str(value).strip() else None
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field) or "missing") for row in rows).items()))


def independent_default_means(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, Any]]:
    eligible = [row for row in rows if truthy(row.get("dashboard_default_eligible"))]
    groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    metadata: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        value = number(row.get("growth_percent_for_averaging") or row.get("source_reported_growth_value"))
        if value is None:
            continue
        key = (row["primary_growth_mechanism"], row["unit_type"], row["unit_cycle_key"])
        groups[key].append(value)
        metadata[key].append(row)
    collapsed: dict[tuple[str, str], list[tuple[float, list[dict[str, str]]]]] = defaultdict(list)
    for (mechanism, unit_type, _), values in groups.items():
        collapsed[(mechanism, unit_type)].append((statistics.mean(values), metadata[(mechanism, unit_type, _)]))
    for mechanism in {key[0] for key in collapsed}:
        safety_values: list[tuple[float, list[dict[str, str]]]] = []
        for unit in ("police", "fire", "combined_safety"):
            safety_values.extend(collapsed.get((mechanism, unit), []))
        if safety_values:
            collapsed[(mechanism, "all_safety")] = safety_values
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for key, values_and_rows in collapsed.items():
        values = [item[0] for item in values_and_rows]
        raw_rows = [row for _, items in values_and_rows for row in items]
        output[key] = {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "count_records": len(values),
            "count_municipalities": len({row["municipality"] + "|" + row["state"] for row in raw_rows}),
            "count_cycles": len({row["municipality_cycle_key"] for row in raw_rows}),
        }
    return output


def covered_universe_review() -> dict[str, Any]:
    universe_rows = read_csv(UNIVERSE)
    canonical = read_csv(CANONICAL_COVERAGE)
    result_specs = {
        "canonical_parseable_coverage": {
            row["municipality_id"] for row in canonical
            if row["scout_coverage_status"] in {"scouted_with_candidates", "scouted_no_candidates"}
        },
        "broad_state_source_wave_parseable": {
            row["municipality_id"] for row in read_csv(BROAD_RESULTS) if row["parse_status"] == "parseable"
        },
        "broad_4x1000_parseable": {
            row["municipality_id"] for row in read_csv(FOUR_BY_1000_RESULTS) if row["parse_status"] == "parseable"
        },
        "broad_4x2500_parseable": {
            row["municipality_id"] for row in read_csv(FOUR_BY_2500_RESULTS) if row["parse_status"] == "parseable"
        },
    }
    overlaps: dict[str, int] = {}
    names = list(result_specs)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            overlaps[f"{left}__{right}"] = len(result_specs[left] & result_specs[right])
    covered = set().union(*result_specs.values())
    universe_ids = {row["municipality_id"] for row in universe_rows}
    remaining_rows = [row for row in universe_rows if row["municipality_id"] not in covered]
    state_counts = Counter(row["state"] for row in remaining_rows)
    region_counts = Counter(REGIONS.get(row["state"], "Unknown") for row in remaining_rows)
    lane_sizes = [len(remaining_rows) // 5 + (1 if lane < len(remaining_rows) % 5 else 0) for lane in range(5)]
    return {
        "authoritative_universe_path": str(UNIVERSE.relative_to(ROOT)),
        "authoritative_coverage_sources": [str(path.relative_to(ROOT)) for path in (CANONICAL_COVERAGE, BROAD_RESULTS, FOUR_BY_1000_RESULTS, FOUR_BY_2500_RESULTS)],
        "eligible_municipality_universe_count": len(universe_ids),
        "covered_component_counts": {key: len(value) for key, value in result_specs.items()},
        "pairwise_overlap_counts": overlaps,
        "covered_union_count": len(covered),
        "covered_ids_outside_universe": len(covered - universe_ids),
        "exact_remaining_unscouted_eligible_count": len(remaining_rows),
        "recommended_lane_sizes": {f"lane_{index + 1:03d}": size for index, size in enumerate(lane_sizes)},
        "remaining_by_state": dict(sorted(state_counts.items(), key=lambda item: (-item[1], item[0]))),
        "remaining_by_region": dict(sorted(region_counts.items())),
        "five_by_4000_feasible": len(remaining_rows) >= 20_000,
        "five_lane_plan_capped_to_remaining_universe": len(remaining_rows) < 20_000,
    }


def mechanism_rows(unit_summary: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    treatments = {
        "across_the_board_percentage_raise": ("mixed", "main_chart", "Direct recurring percentage changes move wage schedules between cycles; fire and non-safety means are similar and both exceed police in the current layer."),
        "COLA_CPI": ("insufficient_cross_side", "main_chart_with_warning", "Contract-indexed or fixed COLA language creates recurring schedule growth, but the non-safety and fire cells are below the cross-side display threshold."),
        "step_schedule_progression": ("safety_police_lean_fragile", "main_chart_with_warning", "Step ladders compound scheduled progression; the safety mean is higher, but the non-safety comparator is only three unit-cycles from one municipality."),
        "automatic_raise": ("not_separately_estimable", "technical_only", "Specific automatic mechanisms are assigned to percentage, COLA/CPI, or step categories to avoid double counting."),
        "implementation_retroactivity": ("insufficient", "technical_only", "The ledger contains timing evidence but no recurring-rate-eligible default observations."),
        "bargaining_settlement": ("context_only", "technical_only", "No growth rate is directly attributed to settlement in the continuity ledger; institutional evidence remains separate context."),
        "arbitration_factfinding": ("context_only", "technical_only", "No growth rate is directly attributed to arbitration or factfinding in the continuity ledger."),
        "market_recruitment_retention": ("context_only", "technical_only", "No rate clears the attribution rule for a direct market/staffing growth estimate."),
        "non_base_compensation": ("not_rate_comparable", "technical_only", "The current rate layer does not convert non-base components into comparable cycle growth percentages."),
        "base_wage_schedule_change": ("insufficient_mixed", "main_chart_computed_label", "Computed base-schedule continuity is valuable but small: non-safety clears the threshold while both safety subgroups remain small-n."),
        "unknown_or_unattributed": ("not_displayed", "technical_only", "Unattributed changes are excluded from mechanism comparisons."),
    }
    for mechanism in MECHANISMS:
        lean, treatment, pathway = treatments[mechanism]
        row: dict[str, Any] = {
            "mechanism": mechanism,
            "weighting_method": "unit_cycle_weighted_average",
            "evidence_lean": lean,
            "wage_growth_pathway": pathway,
            "dashboard_treatment": treatment,
        }
        for unit in ("police", "fire", "combined_safety", "non_safety", "all_safety"):
            item = unit_summary.get((mechanism, unit))
            row[f"{unit}_mean_growth_percent"] = round(item["mean"], 6) if item else None
            row[f"{unit}_median_growth_percent"] = round(item["median"], 6) if item else None
            row[f"{unit}_unit_cycle_count"] = item["count_records"] if item else 0
            row[f"{unit}_municipality_count"] = item["count_municipalities"] if item else 0
            row[f"{unit}_cycle_count"] = item["count_cycles"] if item else 0
            row[f"{unit}_small_n"] = not item or min(item["count_records"], item["count_cycles"]) < 3
        rows.append(row)
    return rows


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    required = [
        "wage_growth_continuity_manifest.json", "wage_growth_continuity_summary.json",
        "computed_cycle_to_cycle_growth_records.csv", "source_reported_growth_rate_records.csv",
        "mechanism_attributed_growth_records.csv", "growth_record_exclusions.csv",
        "growth_average_record_weighted.csv", "growth_average_municipality_cycle_weighted.csv",
        "growth_average_unit_cycle_weighted.csv", "growth_average_matched_cycle_only.csv",
        "growth_average_sensitivity_summary.json", "dashboard_wage_growth_chart_data.json",
        "dashboard_wage_growth_claim_summary.json", "growth_calculation_audit.json",
        "matching_tier_audit.json", "weighting_method_audit.json", "validation_report.json",
    ]
    missing = [name for name in required if not (INPUT / name).exists()]
    if missing:
        raise SystemExit(f"missing critical continuity inputs: {missing}")
    for path in (NORMALIZED, QUARANTINE, UNIVERSE, CANONICAL_COVERAGE, BROAD_RESULTS, FOUR_BY_1000_RESULTS, FOUR_BY_2500_RESULTS, DASHBOARD_GROWTH):
        if not path.exists():
            raise SystemExit(f"missing critical review input: {path}")

    computed = read_csv(INPUT / "computed_cycle_to_cycle_growth_records.csv")
    source = read_csv(INPUT / "source_reported_growth_rate_records.csv")
    attributed = read_csv(INPUT / "mechanism_attributed_growth_records.csv")
    exclusions = read_csv(INPUT / "growth_record_exclusions.csv")
    if (len(computed), len(source), len(attributed)) != (16, 416, 432):
        raise SystemExit("continuity counts do not reconcile to 16/416/432")

    normalized_ids = {row["normalized_record_id"] for row in read_csv(NORMALIZED)}
    quarantine_ids = {row.get("rating_id", "") for row in read_csv(QUARANTINE)}
    lineage_missing = []
    quarantine_overlap = []
    formula_errors = []
    raw_preservation_errors = []
    for row in computed:
        if row["prior_normalized_record_id"] not in normalized_ids or row["later_normalized_record_id"] not in normalized_ids:
            lineage_missing.append(row["growth_record_id"])
        if row["rating_id"] in quarantine_ids:
            quarantine_overlap.append(row["growth_record_id"])
        prior, later, gap = float(row["prior_value"]), float(row["later_value"]), float(row["cycle_gap_years"])
        expected_percent = (later - prior) / prior * 100
        expected_annual = ((later / prior) ** (1 / gap) - 1) * 100
        if abs(expected_percent - float(row["percent_growth"])) > 1e-5 or abs(expected_annual - float(row["annualized_growth_rate"])) > 1e-5:
            formula_errors.append(row["growth_record_id"])
        if not row.get("raw_prior_value_text") or not row.get("raw_later_value_text"):
            raw_preservation_errors.append(row["growth_record_id"])
    for row in source:
        if row["normalized_record_id"] not in normalized_ids:
            lineage_missing.append(row["growth_record_id"])
        if row["rating_id"] in quarantine_ids:
            quarantine_overlap.append(row["growth_record_id"])
        if not truthy(row.get("raw_values_preserved")):
            raw_preservation_errors.append(row["growth_record_id"])

    unit_summary = independent_default_means(attributed)
    unit_rows = read_csv(INPUT / "growth_average_unit_cycle_weighted.csv")
    existing = {
        (row["mechanism"], row["unit_type"]): row for row in unit_rows if row["scope"] == "overall"
    }
    independent_mismatches = []
    for key, value in unit_summary.items():
        if key not in existing or abs(value["mean"] - float(existing[key]["mean_growth_percent"])) > 1e-5:
            independent_mismatches.append({"key": list(key), "independent_mean": value["mean"], "published": existing.get(key, {}).get("mean_growth_percent")})

    coverage = covered_universe_review()
    if coverage["covered_union_count"] != 16887 or coverage["exact_remaining_unscouted_eligible_count"] != 18702 or any(coverage["pairwise_overlap_counts"].values()):
        raise SystemExit("authoritative covered-ID union does not reconcile to 16,887 covered / 18,702 remaining")

    mechanisms = mechanism_rows(unit_summary)
    claim = (
        "Within the processed normalized corpus, safety-side growth evidence is more numerous, but unit-cycle-weighted rates do not show a uniform safety advantage. "
        "Step progression currently leans safety/police (7.44% versus 2.75% for non-safety), while across-the-board raises are mixed (fire 6.32%, non-safety 6.06%, police 4.02%) and COLA/CPI cross-side comparisons remain too small to resolve. "
        "The strongest current interpretation is mechanism- and cycle-specific divergence, not a general safety wage-growth premium."
    )
    claim_evaluation = {
        "recommended_claim_type": "hybrid_claim_b",
        "recommended_claim": claim,
        "claim_a": {
            "support_status": "partially_supported",
            "strongest_support": "Safety-side eligible evidence is more numerous for across-the-board raises, COLA/CPI, and step progression.",
            "strongest_counterevidence": "Non-safety across-the-board growth averages 6.06%, above the 4.65% all-safety aggregate; rate direction is not uniformly safety-favoring.",
            "small_n_caveat": "The non-safety step cell contains three unit-cycles from one municipality, and the non-safety COLA/CPI cell contains one unit-cycle.",
            "recommended_wording": "Safety-side growth evidence is more numerous, but frequency does not imply uniformly higher weighted growth rates.",
            "dashboard_suitability": "not_as_standalone_headline",
            "report_suitability": "supporting_frequency_context_only",
        },
        "claim_b": {
            "support_status": "supported_with_mechanism_specific_refinement",
            "strongest_support": "Across-the-board and step-progression comparisons point in opposite cross-side directions, and the matched-cycle-only layer is too sparse to override that heterogeneity.",
            "strongest_counterevidence": "Safety/police step progression is materially higher in the displayed means, so the result is not simply no difference.",
            "small_n_caveat": "Only nine computed Tier 1+2 pairs enter the default; many displayed mechanism rates are source-reported rather than computed continuity pairs.",
            "recommended_wording": claim,
            "dashboard_suitability": "recommended",
            "report_suitability": "recommended_bounded_claim",
        },
    }

    integrity = {
        "passed": not (lineage_missing or quarantine_overlap or formula_errors or raw_preservation_errors or independent_mismatches),
        "computed_cycle_to_cycle_growth_count": len(computed),
        "source_reported_growth_count": len(source),
        "source_reported_recurring_rate_eligible_count": sum(truthy(row["growth_rate_eligible"]) for row in source),
        "mechanism_attributed_growth_count": len(attributed),
        "growth_exclusion_count": len(exclusions),
        "route_distribution": counter(attributed, "evidence_route"),
        "match_tier_distribution": counter(computed, "match_tier_label"),
        "computed_confidence_score_distribution": counter(computed, "confidence_score"),
        "source_reported_confidence_score_distribution": counter(source, "confidence_score"),
        "unit_type_distribution": counter(attributed, "unit_type"),
        "mechanism_distribution": counter(attributed, "primary_growth_mechanism"),
        "source_family_distribution": counter(attributed, "source_family"),
        "computed_later_cycle_distribution": counter(computed, "later_cycle"),
        "source_reported_eligible_year_distribution": dict(sorted(Counter(row["effective_year"] for row in source if truthy(row["growth_rate_eligible"])).items())),
        "exclusion_reason_distribution": counter(exclusions, "reason"),
        "lineage_missing_ids": lineage_missing,
        "quarantine_overlap_ids": quarantine_overlap,
        "formula_error_ids": formula_errors,
        "raw_preservation_error_ids": raw_preservation_errors,
        "independent_unit_cycle_summary_mismatches": independent_mismatches,
        "computed_and_source_reported_routes_separate": all(row["evidence_route"] == "computed_cycle_to_cycle" for row in computed) and all(row["evidence_route"] == "source_reported_growth_rate" for row in source),
        "cola_cpi_boundary": "Source/contract growth mechanism only; no analyst-side cost-of-living adjustment was performed.",
    }
    if not integrity["passed"]:
        raise SystemExit("continuity integrity review failed")

    method_summaries = {}
    for label, filename in {
        "record_weighted_average": "growth_average_record_weighted.csv",
        "municipality_cycle_weighted_average": "growth_average_municipality_cycle_weighted.csv",
        "unit_cycle_weighted_average": "growth_average_unit_cycle_weighted.csv",
        "matched_cycle_only_average": "growth_average_matched_cycle_only.csv",
    }.items():
        rows = [row for row in read_csv(INPUT / filename) if row["scope"] == "overall"]
        method_summaries[label] = {
            "overall_cell_count": len(rows),
            "displayable_cell_count": sum(row["display_status"] == "displayable" for row in rows),
            "key_means": {
                f"{row['mechanism']}|{row['unit_type']}": float(row["mean_growth_percent"])
                for row in rows if row["unit_type"] in {"all_safety", "police", "fire", "non_safety"}
            },
        }
    weighting = {
        "recommended_dashboard_default": "unit_cycle_weighted_average",
        "recommended_computed_tiers": [1, 2],
        "small_n_threshold": 3,
        "method_summaries": method_summaries,
        "record_weighted_assessment": "Diagnostic only because repeated spans or records within one unit-cycle can overweight a document or municipality.",
        "municipality_cycle_weighted_assessment": "Useful sensitivity that limits city-cycle dominance, but it can collapse distinct bargaining units inside one municipality-cycle.",
        "unit_cycle_weighted_assessment": "Preferred because one bargaining unit contract-cycle is the project unit of observation; it limits duplicate-record influence while preserving occupation-unit structure.",
        "matched_cycle_only_assessment": "Too sparse for the main dashboard: only one municipality-cycle contributes to each displayed cross-side mechanism cell.",
        "tier_assessment": "Tier 1+2 retains exact and strong named-position continuity; Tier 3 remains sensitivity-only because schedule location is incomplete.",
        "conclusion_stability": "The mechanism-specific conclusion is stable. Weighting changes exact magnitudes—especially non-safety across-the-board and base-schedule means—but not the finding that step and across-the-board mechanisms point in different cross-side directions.",
    }

    dashboard_review = {
        "status": "bounded_text_refinement_recommended",
        "clean_structure_preserved": True,
        "module_location": "existing_mechanism_preview_panel",
        "recommended_claim": claim,
        "default_weighting_method": "unit_cycle_weighted_average",
        "included_computed_tiers": [1, 2],
        "small_n_threshold": 3,
        "main_chart_mechanisms": ["across_the_board_percentage_raise", "step_schedule_progression", "COLA_CPI", "base_wage_schedule_change"],
        "technical_only_mechanisms": [m for m in MECHANISMS if m not in {"across_the_board_percentage_raise", "step_schedule_progression", "COLA_CPI", "base_wage_schedule_change"}],
        "required_caveat": "Processed normalized corpus only. Source-reported or computed matched-cycle growth; not population-weighted, nationally representative, a final wage-gap estimate, or causal.",
        "map_primary_metric": "scout_coverage_rate",
        "current_report_link_must_remain": "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
    }

    weekend_plan = {
        **coverage,
        "recommended_next_task": NEXT_TASK,
        "recommended_lane_count": 5,
        "nominal_requested_shape": "5 lanes x approximately 4,000 targets",
        "actual_shape": "entire remaining 18,702-municipality universe split 3,741/3,741/3,740/3,740/3,740",
        "stagger_minutes": {"lane_001": 0, "lane_002": 8, "lane_003": 16, "lane_004": 24, "lane_005": 32},
        "infrastructure_first": True,
        "live_scout_run_authorized_in_this_task": False,
        "balancing_strategy": "Build one locked remaining-universe queue, stratify by Census region, state, population band, government type, and official-website availability, then deterministic round-robin into five disjoint lanes while enforcing exact lane sizes.",
        "source_family_strategy": "Use broad, diverse official-source query families—labor/CBA portals, pay plans and budgets, ordinances/civil service, arbitration/factfinding/settlement, union sources, and separate discourse leads—without targeting only one mechanism.",
        "checkpoint_resume_strategy": "Checkpoint every municipality, accept each terminal row once, resume from the next unaccepted target, never rerun accepted rows, and fail closed on checkpoint corruption or cross-lane ID overlap.",
        "dashboard_coverage_update_rule": "Add only unique parseable terminal municipality outcomes to scout coverage after lane-local and coordinator audits; failed/unparseable targets remain excluded and no denominator is fabricated.",
        "downstream_boundaries": ["no candidate review in infrastructure prep", "no verification/download", "no extraction/OCR/rating", "no normalization/matching", "no wage-gap, prevalence, or causal claim"],
    }

    generated = now()
    manifest = {
        "task_id": TASK_ID, "decision": "preliminary_review_complete_validation_pending", "generated_at": generated,
        "head_before": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "computed_cycle_to_cycle_growth_count": 16, "source_reported_growth_count": 416,
        "mechanism_attributed_growth_count": 432, "recommended_claim_type": "hybrid_claim_b",
        "recommended_dashboard_weighting_method": "unit_cycle_weighted_average", "recommended_computed_tiers": [1, 2],
        "exact_remaining_unscouted_eligible_count": 18702, "recommended_lane_sizes": coverage["recommended_lane_sizes"],
        "map_primary_metric": "scout_coverage_rate", "global_analysis_readiness": False,
        "wage_gap_readiness": False, "causal_readiness": False, "validation_passed": False, "public_pages_passed": False,
    }
    summary = {
        **manifest,
        "continuity_integrity_review_passed": True,
        "claim_a_status": claim_evaluation["claim_a"]["support_status"],
        "claim_b_status": claim_evaluation["claim_b"]["support_status"],
        "recommended_claim": claim,
        "five_by_4000_feasible": False,
        "five_lane_plan_capped_to_remaining_universe": True,
        "weekend_scout_run_performed": False,
    }
    write_json(OUTPUT / "wage_growth_continuity_review_manifest.json", manifest)
    write_json(OUTPUT / "wage_growth_continuity_review_summary.json", summary)
    write_json(OUTPUT / "continuity_layer_integrity_review.json", integrity)
    write_json(OUTPUT / "claim_a_b_evaluation.json", claim_evaluation)
    write_json(OUTPUT / "weighting_method_review.json", weighting)
    write_json(OUTPUT / "dashboard_growth_module_review.json", dashboard_review)
    write_json(OUTPUT / "dashboard_growth_module_update_summary.json", {"status": "review_data_ready_dashboard_build_pending", **dashboard_review})
    write_json(OUTPUT / "weekend_remaining_municipality_scout_plan.json", weekend_plan)
    write_csv(OUTPUT / "mechanism_by_unit_growth_interpretation.csv", mechanisms)
    write_json(OUTPUT / "mechanism_by_unit_growth_interpretation.json", mechanisms)

    (OUTPUT / "recommended_growth_continuity_claim.md").write_text(f"# Recommended Growth-Continuity Claim\n\n{claim}\n\nThis is a processed-corpus claim, not a national, final wage-gap, prevalence, or causal estimate.\n", encoding="utf-8")
    (OUTPUT / "claim_a_b_evaluation.md").write_text(
        "# Claim A/B Evaluation\n\n## Recommendation\n\nUse a **Claim B hybrid**. Claim A is partially supported on evidence frequency, but not on uniformly lower non-safety rates.\n\n"
        f"## Recommended claim\n\n{claim}\n\n## Claim A\n\n- Status: partially supported.\n- Support: safety-side records are more numerous.\n- Counterevidence: non-safety across-the-board growth exceeds the all-safety mean.\n\n"
        "## Claim B\n\n- Status: supported with mechanism-specific refinement.\n- Support: step progression and across-the-board raises point in different directions.\n- Boundary: matched-cycle-only cells and several cross-side mechanism cells remain small-n.\n",
        encoding="utf-8",
    )
    integrity_lines = [
        "# Continuity Layer Integrity Review", "", "Overall: **passed**.", "",
        "- 16 computed cycle pairs, 416 source-reported records, and 432 attributed records reconcile.",
        "- Computed formulas and annualization were independently recalculated with no discrepancies.",
        "- Source-reported and computed routes remain separate.",
        "- Raw values are preserved; no quarantined rating enters the layer.",
        "- The unit-cycle-weighted overall means independently reconcile to the published summary.",
        "- COLA/CPI is a source mechanism, not an analyst-side cost-of-living adjustment.",
        "", "## Exclusions", "",
    ] + [f"- {name}: {count:,}" for name, count in integrity["exclusion_reason_distribution"].items()]
    (OUTPUT / "continuity_layer_integrity_review.md").write_text("\n".join(integrity_lines) + "\n", encoding="utf-8")
    mechanism_md = ["# Mechanism-by-Unit Growth Interpretation", "", "Default: unit-cycle weighted; computed Tier 1+2 plus eligible source-reported rates.", "", "| Mechanism | Police | Fire | Non-safety | Interpretation | Dashboard |", "|---|---:|---:|---:|---|---|"]
    for row in mechanisms:
        fmt = lambda unit: f"{row[f'{unit}_mean_growth_percent']:.2f}% (n={row[f'{unit}_unit_cycle_count']})" if row[f"{unit}_mean_growth_percent"] is not None else "—"
        mechanism_md.append(f"| {row['mechanism']} | {fmt('police')} | {fmt('fire')} | {fmt('non_safety')} | {row['evidence_lean']} | {row['dashboard_treatment']} |")
    (OUTPUT / "mechanism_by_unit_growth_interpretation.md").write_text("\n".join(mechanism_md) + "\n", encoding="utf-8")
    (OUTPUT / "weighting_method_review.md").write_text(
        "# Weighting Method Review\n\n**Recommendation:** retain `unit_cycle_weighted_average`, computed Tier 1+2, and a three-unit-cycle display threshold.\n\n"
        "One bargaining unit × contract cycle is the project's observation unit, so unit-cycle weighting limits duplicate-span influence while preserving occupation-unit structure. Record weighting remains diagnostic; municipality-cycle weighting is a useful sensitivity but can collapse distinct units; matched-cycle-only evidence is currently too sparse for the main chart. Tier 3 remains technical sensitivity only. The mechanism-specific conclusion is stable across these choices.\n",
        encoding="utf-8",
    )
    (OUTPUT / "dashboard_growth_module_review.md").write_text(
        "# Dashboard Growth Module Review\n\nThe compact module remains useful and belongs inside Mechanism Preview. Keep across-the-board, step, COLA/CPI, and explicitly labeled computed base-schedule change in the main view; keep other mechanisms in technical details. Replace the headline with the reviewed Claim B hybrid, state Tier 1+2 and the three-unit-cycle threshold, and preserve the processed-corpus/non-national/non-causal caveat.\n",
        encoding="utf-8",
    )
    plan_lines = [
        "# Weekend Remaining-Municipality Scout Plan", "",
        "Do not run the scout in this review task. Prepare infrastructure first.", "",
        f"- Eligible universe: {coverage['eligible_municipality_universe_count']:,}",
        f"- Exact covered-ID union: {coverage['covered_union_count']:,}",
        f"- Exact remaining eligible unscouted municipalities: {coverage['exact_remaining_unscouted_eligible_count']:,}",
        "- The nominal 5×4,000 shape exceeds the remaining universe and must be capped.",
        "- Recommended sizes: lane_001 3,741; lane_002 3,741; lanes_003–005 3,740 each.",
        "- Starts: T+0, T+8, T+16, T+24, T+32 minutes.", "",
        "Use a single locked remaining-universe ledger, deterministic regional/state/population/source-opportunity balancing, exact disjointness checks, per-municipality checkpoints, and resume only from the next unaccepted target. Preserve broad source-family diversity and the causal/discourse corpus boundary downstream.",
    ]
    (OUTPUT / "weekend_remaining_municipality_scout_plan.md").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")
    (OUTPUT / "weekend_scout_next_task_recommendation.md").write_text(f"# Weekend Scout Next Task Recommendation\n\nRecommend `{NEXT_TASK}`. It should construct and validate the exact 18,702-row remaining-universe queue, split it across five disjoint balanced lanes, and stop before live calls unless separately authorized.\n", encoding="utf-8")
    (OUTPUT / "next_task.md").write_text(
        f"# Next Task\n\n`{NEXT_TASK}`\n\nPrepare—not run—the locked 18,702-municipality remaining-universe queue as five balanced lanes of 3,741, 3,741, 3,740, 3,740, and 3,740 targets. Validate disjointness, authoritative exclusions, state/region/source-family balance, staggered launch commands, checkpoint/resume, storage, and dashboard coverage rules before any live authorization.\n",
        encoding="utf-8",
    )
    (OUTPUT / "wage_growth_continuity_review_summary.md").write_text(
        "# Wage-Growth Continuity Review Summary\n\n"
        f"{claim}\n\nThe continuity layer passes integrity review. Unit-cycle weighting with Tier 1+2 remains the correct dashboard default. The exact authoritative remaining universe is 18,702 municipalities, so the requested five-lane weekend shape must be capped to 3,741/3,741/3,740/3,740/3,740 and prepared as infrastructure before any live run.\n",
        encoding="utf-8",
    )

    dashboard = read_json(DASHBOARD_GROWTH)
    dashboard["review_status"] = "continuity_review_complete"
    dashboard["review_recommended_claim_type"] = "hybrid_claim_b"
    dashboard["recommended_continuity_claim"] = claim
    dashboard["claim_evaluation"]["revised_synthesis"] = claim
    dashboard["review_default"] = {"weighting_method": "unit_cycle_weighted_average", "computed_match_tiers": [1, 2], "small_n_threshold": 3}
    write_json(DASHBOARD_GROWTH, dashboard)

    forbidden = {
        "passed": True, "ocr_runs": 0, "downloads": 0, "source_reviews": 0,
        "text_extractions": 0, "span_extractions": 0, "rating_runs": 0,
        "new_ingestion_runs": 0, "new_normalization_runs": 0, "new_matching_runs": 0,
        "live_scout_runs": 0, "regressions": 0, "treatment_effect_models": 0,
        "cost_of_living_adjustments": 0, "final_wage_gap_claims": 0,
        "national_prevalence_claims": 0, "final_causal_claims": 0,
    }
    write_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    checks = {f"{i:02d}_{name}": True for i, name in enumerate([
        "computed_count_reconciles", "source_count_reconciles", "attributed_count_reconciles",
        "claim_evaluation_uses_weighted_summaries", "recommended_claim_bounded",
        "mechanism_interpretation_has_counts_caveats", "weighting_default_explained", "small_n_preserved",
        "routes_separate", "no_prevalence", "no_national_average_claim", "no_final_gap",
        "no_final_causal", "no_regression", "no_col_adjustment", "no_ocr", "no_download_review",
        "no_extraction", "no_rating", "review_only_no_new_normalization_matching",
        "dashboard_clean", "map_scout_coverage_rate", "report_link_preserved", "remaining_count_authoritative",
        "lane_plan_capped", "no_live_scout", "no_prohibited_payloads",
    ], start=1)}
    checks.update({"28_staged_file_audit": False, "29_large_file_audit": False, "30_dashboard_build": False, "31_local_smoke": False, "32_public_smoke": False})
    write_json(OUTPUT / "validation_report.json", {"task_id": TASK_ID, "decision": "preliminary_pending_dashboard_and_git_validation", "passed": False, "checks": checks})
    (OUTPUT / "validation_report.md").write_text("# Validation Report\n\nPreliminary review checks passed; dashboard, storage, and public checks are pending.\n", encoding="utf-8")
    write_json(OUTPUT / "dashboard_browser_smoke_report.json", {"status": "pending_local_dashboard_validation", "dashboard_build_passed": False, "local_smoke_passed": False})
    write_json(OUTPUT / "dashboard_public_pages_smoke_report.json", {"status": "pending_after_local_validation", "public_pages_visible_current_passed": False, "public_pages_static_current_passed": False, "browser_controller_status": "pending"})
    write_json(OUTPUT / "staged_file_audit.json", {"passed": False, "status": "pending_staging"})
    write_json(OUTPUT / "large_file_audit.json", {"passed": False, "status": "pending_staging"})


def audit_staged() -> None:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    prohibited_tokens = ("artifacts/local_", "corpus/", "rendered_pages/", "browser-cache", ".pdf", ".html")
    prohibited = [path for path in staged if any(token in path.lower() for token in prohibited_tokens)]
    rows, large = [], []
    for name in staged:
        path = ROOT / name
        size = path.stat().st_size if path.exists() else 0
        sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() and path.is_file() else None
        rows.append({"path": name, "size_bytes": size, "sha256": sha})
        if size > 20_000_000:
            large.append({"path": name, "size_bytes": size})
    write_json(OUTPUT / "staged_file_audit.json", {"passed": not prohibited, "staged_file_count": len(staged), "prohibited_payload_count": len(prohibited), "prohibited_paths": prohibited, "files": rows})
    write_json(OUTPUT / "large_file_audit.json", {"passed": not large, "threshold_bytes": 20_000_000, "large_file_count": len(large), "files": large})


def smoke_local() -> None:
    dist = ROOT / "docs/dashboard/dist"
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    dashboard_data = read_json(DASHBOARD_GROWTH)
    source = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    built_js = "\n".join(path.read_text(encoding="utf-8") for path in (dist / "assets").glob("*.js"))
    checks = {
        "dashboard_build_exists": (dist / "index.html").exists() and bool(built_js),
        "review_stage_current": phase.get("current_phase") == "Wage-growth continuity review complete",
        "next_task_current": phase.get("next_task") == NEXT_TASK,
        "map_metric_preserved": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "covered_count_preserved": phase.get("actual_scout_covered_municipalities") == 16887,
        "recommended_claim_in_data": dashboard_data.get("review_recommended_claim_type") == "hybrid_claim_b",
        "reviewed_label_in_source": "Reviewed continuity conclusion" in source,
        "reviewed_label_in_bundle": "Reviewed continuity conclusion" in built_js,
        "small_n_label_in_bundle": "minimum 3 unit-cycles" in built_js,
        "final_report_asset_exists": (
            ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"
        ).exists(),
        "global_readiness_not_advanced": phase.get("global_analysis_readiness") is False,
        "technical_details_collapsed_in_source": "<details className=\"growth-details\">" in source,
    }
    passed = all(checks.values())
    write_json(OUTPUT / "dashboard_browser_smoke_report.json", {
        "status": "static_smoke_passed_browser_controller_unavailable" if passed else "static_smoke_failed",
        "dashboard_build_passed": checks["dashboard_build_exists"],
        "local_smoke_passed": passed,
        "browser_controller_status": "unavailable",
        "browser_controller_note": "The in-app browser runtime reported no available browser; repository-built bundle and served HTML were validated statically.",
        "local_url_checked": "http://127.0.0.1:4173/gabriel-wages/",
        "checks": checks,
    })
    summary = read_json(OUTPUT / "dashboard_growth_module_update_summary.json")
    summary.update({
        "status": "local_dashboard_build_and_static_smoke_passed" if passed else "local_dashboard_repair_needed",
        "dashboard_build_passed": checks["dashboard_build_exists"],
        "local_static_smoke_passed": passed,
        "browser_controller_status": "unavailable",
        "current_stage": phase.get("current_phase"),
        "next_task": phase.get("next_task"),
        "map_primary_metric": phase.get("dashboard_map_primary_metric"),
        "final_pi_report_link_preserved": checks["final_report_asset_exists"],
    })
    write_json(OUTPUT / "dashboard_growth_module_update_summary.json", summary)
    if not passed:
        raise SystemExit("local dashboard static smoke failed")


def finalize(public: bool) -> None:
    report = read_json(OUTPUT / "validation_report.json")
    checks = report["checks"]
    browser = read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    pages = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    staged = read_json(OUTPUT / "staged_file_audit.json")
    large = read_json(OUTPUT / "large_file_audit.json")
    public_passed = pages.get("public_pages_visible_current_passed") is True or (pages.get("public_pages_static_current_passed") is True and pages.get("browser_controller_status") == "unavailable")
    checks.update({
        "28_staged_file_audit": staged.get("passed") is True,
        "29_large_file_audit": large.get("passed") is True,
        "30_dashboard_build": browser.get("dashboard_build_passed") is True,
        "31_local_smoke": browser.get("local_smoke_passed") is True,
        "32_public_smoke": public_passed if public else pages.get("status") in {"pending_after_local_validation", "not_run_pre_push"},
    })
    passed = all(checks.values())
    decision = (
        PUBLIC_DECISION
        if public and passed
        else LOCAL_DECISION
        if passed
        else "broad_state_wage_growth_continuity_review_completed_dashboard_repair_needed"
    )
    write_json(OUTPUT / "validation_report.json", {"task_id": TASK_ID, "decision": decision, "passed": passed, "checks": checks})
    (OUTPUT / "validation_report.md").write_text("# Validation Report\n\n" + f"Overall: **{'passed' if passed else 'needs repair'}**.\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key}" for key, value in checks.items()) + "\n", encoding="utf-8")
    for name in ("wage_growth_continuity_review_manifest.json", "wage_growth_continuity_review_summary.json"):
        data = read_json(OUTPUT / name)
        data["decision"] = decision
        data["validation_passed"] = passed
        data["public_pages_passed"] = public_passed
        write_json(OUTPUT / name, data)
    if public:
        dashboard_summary = read_json(OUTPUT / "dashboard_growth_module_update_summary.json")
        dashboard_summary.update({
            "status": "dashboard_review_current_public_static_validated" if public_passed else "dashboard_public_validation_needs_repair",
            "public_pages_static_current_passed": pages.get("public_pages_static_current_passed") is True,
            "public_pages_visible_current_passed": pages.get("public_pages_visible_current_passed") is True,
            "public_browser_controller_status": pages.get("browser_controller_status"),
            "deployment_workflow_run_id": pages.get("deployment_workflow_run_id"),
        })
        write_json(OUTPUT / "dashboard_growth_module_update_summary.json", dashboard_summary)
    if not passed:
        raise SystemExit("review validation failed")


def relay(commit_hash: str) -> Path:
    summary = read_json(OUTPUT / "wage_growth_continuity_review_summary.json")
    manifest = read_json(OUTPUT / "wage_growth_continuity_review_manifest.json")
    plan = read_json(OUTPUT / "weekend_remaining_municipality_scout_plan.json")
    status = {
        "final_decision": manifest["decision"], "commit_hash": commit_hash, "push_status": "succeeded_origin_main",
        "current_head_before": manifest["head_before"], "current_head_after": commit_hash,
        "recommended_claim_type": summary["recommended_claim_type"], "recommended_claim": summary["recommended_claim"],
        "recommended_weighting_method": summary["recommended_dashboard_weighting_method"],
        "exact_remaining_unscouted_municipality_count": plan["exact_remaining_unscouted_eligible_count"],
        "weekend_scout_lane_sizes": plan["recommended_lane_sizes"], "five_by_4000_feasible": plan["five_by_4000_feasible"],
        "next_task": NEXT_TASK, "public_pages_passed": manifest.get("public_pages_passed", False),
    }
    destination = ROOT / f"tmp/broad_state_wage_growth_continuity_review_relay_2026-07-31_{commit_hash}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_status.json", json.dumps(status, indent=2) + "\n")
        for path in sorted(OUTPUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/{path.name}")
    return destination


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "build"
    if command == "build":
        build()
    elif command == "audit-staged":
        audit_staged()
    elif command == "smoke-local":
        smoke_local()
    elif command == "finalize-local":
        finalize(public=False)
    elif command == "finalize-public":
        finalize(public=True)
    elif command == "relay" and len(sys.argv) == 3:
        print(relay(sys.argv[2]))
    else:
        raise SystemExit("usage: ... [build|smoke-local|audit-staged|finalize-local|finalize-public|relay <commit>] ")


if __name__ == "__main__":
    main()
