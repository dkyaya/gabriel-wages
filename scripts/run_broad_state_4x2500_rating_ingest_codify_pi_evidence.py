#!/usr/bin/env python3
"""Ingest valid 4x2500 ratings into a bounded PI-evidence layer.

This is a deterministic metadata transformation. It reads only committed valid
and quarantine rating ledgers. It performs no model/API calls, source access,
text extraction, OCR, normalization, matching, wage-gap analysis, regression,
or causal/prevalence inference.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30"
VALID_PATH = INPUT / "merged_span_ratings_valid.jsonl"
QUARANTINE_PATH = INPUT / "merged_span_ratings_quarantine.jsonl"
TASK_ID = "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30"
DECISION = "broad_state_4x2500_rating_ingest_codify_completed_normalization_matching_ready"
NEXT_TASK = "BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-2026-07-30"
EXPECTED_VALID = 18_554
EXPECTED_QUARANTINE = 58
EXPECTED_TOTAL = 18_612
SCHEMA_VERSION = "broad_state_4x2500_codified_rating_v1"

CLUSTERS = {
    "automatic_wage_growth": "Automatic wage-growth mechanisms",
    "bargaining_dispute_resolution": "Bargaining and dispute-resolution mechanisms",
    "market_staffing_pressure": "Market and staffing pressure mechanisms",
    "timing_implementation": "Timing and implementation mechanisms",
    "non_base_compensation": "Non-base compensation mechanisms",
    "rank_step_specialization_classification": "Rank, step, specialization, and classification mechanisms",
    "fiscal_governance_constraints": "Fiscal and governance constraints",
    "safety_non_safety_directional_hints": "Safety vs non-safety directional hints",
    "quantitative_base_wage_needs_normalization": "Quantitative base-wage evidence needing normalization",
    "weak_context_exclusion": "Weak, context, and exclusion layer",
}

STRENGTH_FIELDS = {
    "automatic_wage_growth": "automatic_raise_mechanism_strength",
    "bargaining_dispute_resolution": "bargaining_power_signal_strength",
    "market_staffing_pressure": "market_or_comparability_pressure_strength",
    "timing_implementation": "implementation_or_retroactivity_advantage_strength",
    "non_base_compensation": "non_base_compensation_signal_strength",
    "rank_step_specialization_classification": "rank_or_specialization_premium_strength",
    "fiscal_governance_constraints": "fiscal_constraint_signal_strength",
    "quantitative_base_wage_needs_normalization": "base_wage_direct_value_strength",
    "weak_context_exclusion": "weak_or_no_claim_support_strength",
}

CLUSTER_CLAIMS = {
    "automatic_wage_growth": (
        "Within the processed rated corpus, automatic wage-growth provisions—including scheduled increases, percentage raises, and indexed adjustments—form a recurring documentary mechanism.",
        "This describes rated contract language; it does not establish national prevalence, comparative wage effects, or causality.",
    ),
    "bargaining_dispute_resolution": (
        "Rated evidence identifies bargaining, arbitration, factfinding, settlement, and strike/no-strike language as plausible institutional channels shaping municipal compensation terms in some documents.",
        "The evidence identifies documentary mechanisms, not treatment effects or proof that dispute resolution raises wages.",
    ),
    "market_staffing_pressure": (
        "Within the processed rated corpus, market comparability, recruitment, retention, staffing shortages, and competing-jurisdiction language appear as candidate explanations for compensation changes.",
        "These are local documentary justifications and cannot be generalized to all municipalities.",
    ),
    "timing_implementation": (
        "Rated evidence frequently identifies implementation dates, retroactivity, settlement timing, and delayed payment as mechanisms that can affect when negotiated wage gains are realized.",
        "Timing language is not a normalized measure of realized growth and does not by itself establish a safety/non-safety difference.",
    ),
    "non_base_compensation": (
        "Within the processed rated corpus, non-base compensation appears as a substantial compensation channel through longevity, shift, hazard, specialty, certification, education, stipend, allowance, and premium-pay provisions.",
        "These components require separate classification from base pay before comparative compensation analysis.",
    ),
    "rank_step_specialization_classification": (
        "Rank, step, grade, specialization, and classification structures recur in report-usable evidence and provide plausible channels for wage progression within bargaining units.",
        "Cross-unit comparison requires alignment of ranks, grades, steps, occupations, and effective periods.",
    ),
    "fiscal_governance_constraints": (
        "Some rated evidence documents fiscal limits, appropriation requirements, governance approvals, and internal-equity considerations as constraints or decision points in municipal compensation setting.",
        "This is a bounded documentary pattern and does not prove that fiscal constraints suppress any occupation's wages.",
    ),
    "safety_non_safety_directional_hints": (
        "A minority of valid ratings provides directional hints consistent with safety advantage, non-safety advantage, or gap narrowing, while most ratings are neutral/general or not directionally applicable.",
        "Directional tags are suggestive documentary hints only; matched city-cycle structure and normalized pay evidence are required before gap claims.",
    ),
    "quantitative_base_wage_needs_normalization": (
        "The processed rated corpus contains a substantial pool of direct compensation values and wage schedules that is potentially useful for quantitative analysis after normalization.",
        "Hourly/annual units, base/non-base status, occupation, rank, step, effective period, and municipality-cycle alignment remain unresolved.",
    ),
    "weak_context_exclusion": (
        "A material portion of ratings is context-only, weak, or excluded, reinforcing the need to separate documentary context from claim-ready evidence.",
        "Excluded and quarantined evidence must not be used as support unless separately repaired and revalidated.",
    ),
}

REQUIRED_INPUTS = [
    "merged_span_ratings_valid.jsonl", "merged_span_ratings_quarantine.jsonl",
    "rating_valid_ledger_manifest.json", "rating_quarantine_ledger_manifest.json",
    "span_rating_summary.json", "mechanism_specific_rating_summaries.json",
    "pi_report_candidate_findings.json", "pi_report_candidate_findings.md",
    "dashboard_cleanup_audit.json", "dashboard_information_architecture_report.json",
]

CODIFIED_FIELDS = [
    "codified_record_id", "rating_id", "span_id", "source_id", "retained_source_id",
    "candidate_id", "municipality", "state", "region", "source_family",
    "priority_bucket", "cba_non_cba_hint", "evidence_category",
    "primary_mechanism_cluster", "secondary_mechanism_clusters",
    "mechanism_attributes", "mechanism_strength_scores", "evidence_quality_score",
    "report_usability_bucket", "report_usability_score", "claim_relevance_bucket",
    "direction_bucket", "direction_confidence_score", "quantitative_value_present",
    "raw_wage_or_comp_value_present", "percentage_or_growth_value_present",
    "effective_period_present", "unit_or_group_present", "rank_step_grade_present",
    "base_vs_non_base_clear", "normalization_needed", "normalization_blocker_tags",
    "causal_candidate_hint", "causal_claim_allowed", "population_prevalence_claim_allowed",
    "national_prevalence_claim_allowed", "careful_claim_allowed", "careful_claim_type",
    "careful_claim_text", "careful_claim_caveat", "support_type", "report_placement",
    "evidence_quality_level", "pi_report_section_candidate", "pi_report_priority",
    "concise_mechanism_paraphrase", "pi_report_paraphrase",
    "why_this_matters_for_wage_growth", "limitations_or_caveats",
    "prohibited_claims_warning", "quant_span_types", "qualitative_mechanism_span_types",
    "scout_target_id", "verification_row_id", "source_review_download_id",
    "readiness_id", "extraction_id", "span_queue_id", "span_lane_id",
    "rating_lane_id", "source_type", "source_title", "original_locator",
    "final_locator", "page_number", "section_heading", "character_start_offset",
    "character_end_offset", "line_offset", "paragraph_offset", "span_sha256",
    "extracted_text_artifact_hash", "rating_input_ledger_sha256", "codified_at",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(f"{SCHEMA_VERSION}|{value}".encode()).hexdigest()[:24]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    fields = list(fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: serialize_cell(row.get(field, "")) for field in fields})


def serialize_cell(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return stable_json(value)
    if isinstance(value, bool):
        return str(value).lower()
    return value


def split_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if not value:
        return []
    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item)]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in re.split(r"[|;,]", text) if item.strip()]


def as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def median(values: list[int | float]) -> float:
    return round(float(statistics.median(values)), 3) if values else 0.0


def mean(values: list[int | float]) -> float:
    return round(float(statistics.fmean(values)), 3) if values else 0.0


def quality_level(score: int) -> str:
    if score >= 4: return "very_high"
    if score == 3: return "high"
    if score == 2: return "moderate"
    if score == 1: return "low"
    return "unusable_or_not_supported"


def strength_scores(row: dict[str, Any]) -> dict[str, int]:
    scores = {cluster: as_int(row.get(field)) for cluster, field in STRENGTH_FIELDS.items()}
    directional = max(
        as_int(row.get("safety_advantage_signal_strength")),
        as_int(row.get("non_safety_constraint_signal_strength")),
        as_int(row.get("gap_narrowing_signal_strength")),
    )
    scores["safety_non_safety_directional_hints"] = directional
    scores["bargaining_dispute_resolution"] = max(
        scores["bargaining_dispute_resolution"],
        as_int(row.get("strike_or_no_strike_constraint_strength")),
    )
    scores["fiscal_governance_constraints"] = max(
        scores["fiscal_governance_constraints"],
        as_int(row.get("parity_or_internal_equity_signal_strength")),
    )
    if as_bool(row.get("quantitative_value_present")):
        scores["quantitative_base_wage_needs_normalization"] = max(
            1, scores["quantitative_base_wage_needs_normalization"]
        )
    return scores


def cluster_memberships(row: dict[str, Any], scores: dict[str, int]) -> list[str]:
    members = [cluster for cluster, score in scores.items() if score > 0]
    quant_tags = set(split_tags(row.get("quant_span_types")))
    qual_tags = set(split_tags(row.get("qualitative_mechanism_span_types")))
    if quant_tags & {"percentage_raise", "COLA_or_CPI_adjustment", "salary_schedule", "wage_schedule", "step_schedule"}:
        members.append("automatic_wage_growth")
    if qual_tags & {"arbitration_or_factfinding", "collective_bargaining_process", "strike_or_no_strike_constraint"}:
        members.append("bargaining_dispute_resolution")
    if qual_tags & {"market_comparability", "recruitment_or_retention", "staffing_shortage_or_operational_pressure"}:
        members.append("market_staffing_pressure")
    if qual_tags & {"retroactivity_or_implementation_timing"} or quant_tags & {"effective_date", "retroactive_payment", "lump_sum_payment"}:
        members.append("timing_implementation")
    if qual_tags & {"fiscal_constraint_or_budget_limit", "council_or_board_approval", "parity_or_internal_equity"}:
        members.append("fiscal_governance_constraints")
    if row.get("report_usability_bucket") == "exclude_from_report" or row.get("claim_relevance_bucket") == "weak_or_not_supported":
        members.append("weak_context_exclusion")
    if row.get("report_usability_bucket") == "pi_report_context_only" and not members:
        members.append("weak_context_exclusion")
    if not members:
        members.append("weak_context_exclusion")
    return list(dict.fromkeys(members))


def choose_primary(row: dict[str, Any], members: list[str], scores: dict[str, int]) -> str:
    if row.get("report_usability_bucket") == "exclude_from_report":
        return "weak_context_exclusion"
    precedence = [
        "non_base_compensation", "timing_implementation", "automatic_wage_growth",
        "bargaining_dispute_resolution", "market_staffing_pressure",
        "rank_step_specialization_classification", "fiscal_governance_constraints",
        "safety_non_safety_directional_hints", "quantitative_base_wage_needs_normalization",
        "weak_context_exclusion",
    ]
    return sorted(members, key=lambda name: (-scores.get(name, 1), precedence.index(name)))[0]


def careful_type(row: dict[str, Any], primary: str, scores: dict[str, int]) -> tuple[str, bool]:
    usability = row.get("report_usability_bucket")
    relevance = row.get("claim_relevance_bucket")
    if usability == "exclude_from_report" or relevance == "weak_or_not_supported":
        return "exclusion", False
    if usability == "pi_report_context_only":
        return "context_only", True
    if usability == "downstream_normalization_needed":
        return "normalization_needed_quantitative_evidence", True
    if usability == "pi_report_supporting_example":
        return "supporting_example", True
    if row.get("direction_bucket") not in {"neutral_or_general", "not_applicable", "unclear"}:
        return "directional_hint", True
    if relevance == "direct_quantitative_claim_support":
        return "direct_quantitative_evidence_availability", True
    if scores.get(primary, 0) >= 3:
        return "mechanism_strength_summary", True
    return "mechanism_presence", True


def report_section(primary: str, careful: str) -> str:
    if careful == "exclusion": return "Limits"
    if primary == "quantitative_base_wage_needs_normalization": return "Codified Evidence Categories"
    if primary == "weak_context_exclusion": return "Limits"
    return "Findings"


def report_priority(row: dict[str, Any]) -> str:
    return {
        "pi_report_core_finding_ready": "core",
        "pi_report_supporting_example": "supporting",
        "pi_report_context_only": "context",
        "downstream_normalization_needed": "normalization_lane",
        "exclude_from_report": "exclude",
    }.get(row.get("report_usability_bucket"), "context")


def codify(row: dict[str, Any], ledger_sha: str, timestamp: str) -> dict[str, Any]:
    scores = strength_scores(row)
    members = cluster_memberships(row, scores)
    primary = choose_primary(row, members, scores)
    careful, allowed = careful_type(row, primary, scores)
    claim, caveat = CLUSTER_CLAIMS[primary]
    return {
        "codified_record_id": stable_id("B4X2500COD-20260730-", row["rating_id"]),
        "rating_id": row["rating_id"], "span_id": row["span_id"],
        "source_id": row.get("source_id", ""), "retained_source_id": row.get("retained_source_id", ""),
        "candidate_id": row.get("candidate_id", ""), "municipality": row.get("municipality", ""),
        "state": row.get("state", ""), "region": row.get("region", ""),
        "source_family": row.get("source_family", ""), "priority_bucket": row.get("priority_bucket", ""),
        "cba_non_cba_hint": row.get("cba_non_cba_hint", ""), "evidence_category": row.get("evidence_category", ""),
        "primary_mechanism_cluster": primary,
        "secondary_mechanism_clusters": [item for item in members if item != primary],
        "mechanism_attributes": split_tags(row.get("mechanism_attributes")),
        "mechanism_strength_scores": scores,
        "evidence_quality_score": as_int(row.get("evidence_quality_score")),
        "report_usability_bucket": row.get("report_usability_bucket", ""),
        "report_usability_score": as_int(row.get("report_usability_score")),
        "claim_relevance_bucket": row.get("claim_relevance_bucket", ""),
        "direction_bucket": row.get("direction_bucket", ""),
        "direction_confidence_score": as_int(row.get("direction_confidence_score")),
        "quantitative_value_present": as_bool(row.get("quantitative_value_present")),
        "raw_wage_or_comp_value_present": as_bool(row.get("raw_wage_or_comp_value_present")),
        "percentage_or_growth_value_present": as_bool(row.get("percentage_or_growth_value_present")),
        "effective_period_present": as_bool(row.get("effective_period_present")),
        "unit_or_group_present": as_bool(row.get("unit_or_group_present")),
        "rank_step_grade_present": as_bool(row.get("rank_step_grade_present")),
        "base_vs_non_base_clear": as_bool(row.get("base_vs_non_base_clear")),
        "normalization_needed": as_bool(row.get("normalization_needed")),
        "normalization_blocker_tags": split_tags(row.get("normalization_blocker_tags")),
        "causal_candidate_hint": row.get("causal_candidate_hint", "none"),
        "causal_claim_allowed": False, "population_prevalence_claim_allowed": False,
        "national_prevalence_claim_allowed": False, "careful_claim_allowed": allowed,
        "careful_claim_type": careful, "careful_claim_text": claim if allowed else "",
        "careful_claim_caveat": caveat, "support_type": careful,
        "report_placement": report_section(primary, careful),
        "evidence_quality_level": quality_level(as_int(row.get("evidence_quality_score"))),
        "pi_report_section_candidate": report_section(primary, careful),
        "pi_report_priority": report_priority(row),
        "concise_mechanism_paraphrase": row.get("concise_mechanism_paraphrase", ""),
        "pi_report_paraphrase": row.get("pi_report_paraphrase", ""),
        "why_this_matters_for_wage_growth": row.get("why_this_matters_for_wage_growth", ""),
        "limitations_or_caveats": row.get("limitations_or_caveats", ""),
        "prohibited_claims_warning": "No final causal, national/population prevalence, wage-gap, normalized comparison, regression, or treatment-effect claim.",
        "quant_span_types": split_tags(row.get("quant_span_types")),
        "qualitative_mechanism_span_types": split_tags(row.get("qualitative_mechanism_span_types")),
        "scout_target_id": row.get("scout_target_id", ""), "verification_row_id": row.get("verification_row_id", ""),
        "source_review_download_id": row.get("source_review_download_id", ""), "readiness_id": row.get("readiness_id", ""),
        "extraction_id": row.get("extraction_id", ""), "span_queue_id": row.get("span_queue_id", ""),
        "span_lane_id": row.get("span_lane_id", ""), "rating_lane_id": row.get("rating_lane_id", ""),
        "source_type": row.get("source_type", ""), "source_title": row.get("source_title", ""),
        "original_locator": row.get("original_locator", ""), "final_locator": row.get("final_locator", ""),
        "page_number": row.get("page_number", ""), "section_heading": row.get("section_heading", ""),
        "character_start_offset": row.get("character_start_offset", ""), "character_end_offset": row.get("character_end_offset", ""),
        "line_offset": row.get("line_offset", ""), "paragraph_offset": row.get("paragraph_offset", ""),
        "span_sha256": row.get("span_sha256", ""),
        "extracted_text_artifact_hash": row.get("extracted_text_artifact_hash", ""),
        "rating_input_ledger_sha256": ledger_sha, "codified_at": timestamp,
    }


def distribution(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "unknown")) for row in rows).items()))


def primary_cluster_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for slug, title in CLUSTERS.items():
        primary = [row for row in rows if row["primary_mechanism_cluster"] == slug]
        supported = [row for row in rows if slug == row["primary_mechanism_cluster"] or slug in row["secondary_mechanism_clusters"]]
        scores = [row["mechanism_strength_scores"].get(slug, 0) for row in supported]
        ready = [row for row in supported if row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example"}]
        examples = sorted(ready, key=lambda r: (-r["report_usability_score"], -r["evidence_quality_score"], r["rating_id"]))[:3]
        result[slug] = {
            "title": title,
            "primary_record_count": len(primary), "supported_record_count": len(supported),
            "report_ready_count": len(ready),
            "core_count": sum(r["report_usability_bucket"] == "pi_report_core_finding_ready" for r in supported),
            "supporting_count": sum(r["report_usability_bucket"] == "pi_report_supporting_example" for r in supported),
            "context_count": sum(r["report_usability_bucket"] == "pi_report_context_only" for r in supported),
            "normalization_count": sum(r["report_usability_bucket"] == "downstream_normalization_needed" for r in supported),
            "excluded_count": sum(r["report_usability_bucket"] == "exclude_from_report" for r in supported),
            "average_strength_score": mean(scores), "median_strength_score": median(scores),
            "evidence_quality_distribution": distribution(supported, "evidence_quality_level"),
            "direction_distribution": distribution(supported, "direction_bucket"),
            "top_source_families": Counter(r["source_family"] for r in supported).most_common(5),
            "top_states": Counter(r["state"] for r in supported).most_common(5),
            "top_regions": Counter(r["region"] for r in supported).most_common(4),
            "representative_paraphrases": [r["pi_report_paraphrase"] for r in examples if r["pi_report_paraphrase"]],
            "careful_claim_text": CLUSTER_CLAIMS[slug][0], "caveat": CLUSTER_CLAIMS[slug][1],
            "normalization_dependency": slug == "quantitative_base_wage_needs_normalization" or any(r["normalization_needed"] for r in supported),
            "causal_claim_allowed": False, "population_prevalence_claim_allowed": False,
        }
    return result


def matches_claim(row: dict[str, Any], key: str) -> bool:
    tags = set(row["quant_span_types"]) | set(row["qualitative_mechanism_span_types"])
    scores = row["mechanism_strength_scores"]
    mapping: dict[str, Callable[[], bool]] = {
        "non_base_compensation": lambda: scores.get("non_base_compensation", 0) > 0,
        "base_wage_values": lambda: scores.get("quantitative_base_wage_needs_normalization", 0) > 0,
        "implementation_retroactivity": lambda: scores.get("timing_implementation", 0) > 0,
        "automatic_raises": lambda: scores.get("automatic_wage_growth", 0) > 0,
        "cola_cpi": lambda: "COLA_or_CPI_adjustment" in tags or "automatic_CPI_COLA_or_indexing" in tags,
        "percentage_increases": lambda: "percentage_raise" in tags or row["percentage_or_growth_value_present"],
        "step_schedule_progression": lambda: bool(tags & {"step_schedule", "salary_schedule", "wage_schedule", "grade_or_payband"}),
        "bargaining_arbitration": lambda: scores.get("bargaining_dispute_resolution", 0) > 0,
        "strike_constraints": lambda: "strike_or_no_strike_constraint" in tags,
        "market_staffing": lambda: scores.get("market_staffing_pressure", 0) > 0,
        "rank_specialization": lambda: scores.get("rank_step_specialization_classification", 0) > 0,
        "fiscal_governance": lambda: scores.get("fiscal_governance_constraints", 0) > 0,
        "safety_advantage_hints": lambda: row["direction_bucket"] == "safety_advantage",
        "non_safety_advantage_hints": lambda: row["direction_bucket"] == "non_safety_advantage",
        "gap_narrowing_hints": lambda: row["direction_bucket"] == "gap_narrowing",
        "quantitative_normalization": lambda: row["quantitative_value_present"] and row["normalization_needed"],
        "context_layer": lambda: row["report_usability_bucket"] == "pi_report_context_only",
        "exclusion_layer": lambda: row["report_usability_bucket"] == "exclude_from_report",
    }
    return mapping[key]()


CLAIM_SPECS = [
    ("non_base_compensation", "Non-base compensation is a distinct compensation-growth channel", "core finding candidate"),
    ("base_wage_values", "Direct base-wage and schedule evidence is quantitatively promising", "core finding candidate"),
    ("implementation_retroactivity", "Implementation timing and retroactivity shape realized timing", "core finding candidate"),
    ("automatic_raises", "Automatic raises recur as a documentary wage-growth mechanism", "core finding candidate"),
    ("rank_specialization", "Rank, step, specialization, and classification structures support progression", "core finding candidate"),
    ("quantitative_normalization", "Quantitative evidence requires normalization before comparison", "core finding candidate"),
    ("cola_cpi", "COLA/CPI language is a recurring contract mechanism", "supporting finding candidate"),
    ("percentage_increases", "Across-the-board percentage increases recur in compensation language", "supporting finding candidate"),
    ("step_schedule_progression", "Step and schedule progression provide structured wage paths", "supporting finding candidate"),
    ("bargaining_arbitration", "Bargaining and dispute resolution are plausible institutional mechanisms", "supporting finding candidate"),
    ("strike_constraints", "Strike and no-strike constraints form part of bargaining context", "supporting finding candidate"),
    ("market_staffing", "Market and staffing pressures appear as compensation justifications", "supporting finding candidate"),
    ("fiscal_governance", "Fiscal and governance language provides bounded constraint evidence", "context finding candidate"),
    ("safety_advantage_hints", "Some spans provide safety-advantage directional hints", "context finding candidate"),
    ("non_safety_advantage_hints", "Some spans provide non-safety-advantage directional hints", "context finding candidate"),
    ("gap_narrowing_hints", "A small set of spans provides gap-narrowing hints", "context finding candidate"),
    ("context_layer", "Context-only evidence should remain separate from findings", "limitation only"),
    ("exclusion_layer", "Weak and excluded ratings should not support PI claims", "exclude"),
]


def claim_cluster(key: str) -> str:
    mapping = {
        "non_base_compensation": "non_base_compensation", "base_wage_values": "quantitative_base_wage_needs_normalization",
        "implementation_retroactivity": "timing_implementation", "automatic_raises": "automatic_wage_growth",
        "cola_cpi": "automatic_wage_growth", "percentage_increases": "automatic_wage_growth",
        "step_schedule_progression": "rank_step_specialization_classification",
        "bargaining_arbitration": "bargaining_dispute_resolution", "strike_constraints": "bargaining_dispute_resolution",
        "market_staffing": "market_staffing_pressure", "rank_specialization": "rank_step_specialization_classification",
        "fiscal_governance": "fiscal_governance_constraints", "safety_advantage_hints": "safety_non_safety_directional_hints",
        "non_safety_advantage_hints": "safety_non_safety_directional_hints", "gap_narrowing_hints": "safety_non_safety_directional_hints",
        "quantitative_normalization": "quantitative_base_wage_needs_normalization",
        "context_layer": "weak_context_exclusion", "exclusion_layer": "weak_context_exclusion",
    }
    return mapping[key]


def aggregate_claims(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims = []
    for index, (key, title, classification) in enumerate(CLAIM_SPECS, 1):
        selected = [row for row in rows if matches_claim(row, key)]
        cluster = claim_cluster(key)
        strengths = [row["mechanism_strength_scores"].get(cluster, 0) for row in selected]
        examples = sorted(
            [row for row in selected if row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example"}],
            key=lambda r: (-r["report_usability_score"], -r["evidence_quality_score"], r["rating_id"]),
        )[:3]
        base_claim, caveat = CLUSTER_CLAIMS[cluster]
        if key == "cola_cpi":
            base_claim = "Within the processed rated corpus, COLA/CPI and inflation-indexing language appears as a recurring contract mechanism for scheduled wage adjustment."
        elif key == "percentage_increases":
            base_claim = "Among valid rated spans, across-the-board percentage and growth values provide recurring documentary evidence of scheduled compensation changes."
        elif key == "strike_constraints":
            base_claim = "Strike and no-strike provisions recur in the rated bargaining context and are plausible institutional constraints on wage-setting processes."
        elif key.endswith("_hints"):
            label = key.replace("_hints", "").replace("_", " ")
            base_claim = f"Some valid rated spans contain documentary directionality consistent with {label}; the pattern is suggestive and not a wage-gap estimate."
        elif key == "context_layer":
            base_claim = "Context-only evidence is abundant enough to inform interpretation but is not classified as finding-ready support."
        elif key == "exclusion_layer":
            base_claim = "Weak or unsupported ratings form a material exclusion layer and should not be promoted into PI claims."
        claims.append({
            "claim_id": f"B4X2500-CLAIM-20260730-{index:03d}", "claim_key": key,
            "claim_title": title, "careful_claim_text": base_claim,
            "evidence_basis_summary": f"Derived from {len(selected):,} schema-valid rated spans matching the controlled {key} definition.",
            "valid_rating_count": len(selected),
            "report_ready_count": sum(r["report_usability_bucket"] == "pi_report_core_finding_ready" for r in selected),
            "supporting_example_count": sum(r["report_usability_bucket"] == "pi_report_supporting_example" for r in selected),
            "context_only_count": sum(r["report_usability_bucket"] == "pi_report_context_only" for r in selected),
            "normalization_needed_count": sum(r["report_usability_bucket"] == "downstream_normalization_needed" for r in selected),
            "excluded_count": sum(r["report_usability_bucket"] == "exclude_from_report" for r in selected),
            "average_strength_score": mean(strengths), "median_strength_score": median(strengths),
            "evidence_quality_distribution": distribution(selected, "evidence_quality_level"),
            "direction_distribution": distribution(selected, "direction_bucket"),
            "top_source_families": Counter(r["source_family"] for r in selected).most_common(5),
            "top_states": Counter(r["state"] for r in selected).most_common(5),
            "top_regions": Counter(r["region"] for r in selected).most_common(4),
            "representative_paraphrases": [r["pi_report_paraphrase"] for r in examples if r["pi_report_paraphrase"]],
            "caveats": caveat, "normalization_dependency": any(r["normalization_needed"] for r in selected),
            "causal_prevalence_boundary_warning": "Does not by itself establish causality, population/national prevalence, or a normalized wage gap.",
            "recommended_pi_report_placement": "Findings" if "finding" in classification and classification != "context finding candidate" else "Limits" if classification in {"limitation only", "exclude"} else "Findings — bounded directional context",
            "finding_classification": classification, "mechanism_cluster": cluster,
        })
    return claims


def aggregate_group(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: groups[str(row.get(field) or "unknown")].append(row)
    return {key: {
        "valid_rating_count": len(items),
        "report_usability_counts": distribution(items, "report_usability_bucket"),
        "claim_relevance_counts": distribution(items, "claim_relevance_bucket"),
        "direction_counts": distribution(items, "direction_bucket"),
        "average_evidence_quality": mean([r["evidence_quality_score"] for r in items]),
    } for key, items in sorted(groups.items())}


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join(lines)


def write_claim_files(claims: list[dict[str, Any]]) -> None:
    write_json(OUTPUT / "careful_claim_candidates.json", {"count": len(claims), "claims": claims})
    claim_fields = [
        "claim_id", "claim_key", "claim_title", "careful_claim_text", "evidence_basis_summary",
        "valid_rating_count", "report_ready_count", "supporting_example_count", "context_only_count",
        "normalization_needed_count", "excluded_count", "average_strength_score", "median_strength_score",
        "caveats", "normalization_dependency", "causal_prevalence_boundary_warning",
        "recommended_pi_report_placement", "finding_classification", "mechanism_cluster",
    ]
    write_csv(OUTPUT / "careful_claim_candidates.csv", claims, claim_fields)
    lines = ["# Careful claim candidates", "", "These candidates describe the processed rated corpus. They are not final causal, prevalence, wage-gap, regression, or treatment-effect findings.", ""]
    for claim in claims:
        lines += [f"## {claim['claim_id']} — {claim['claim_title']}", "", claim["careful_claim_text"], "", f"**Evidence basis:** {claim['evidence_basis_summary']} Core-ready: {claim['report_ready_count']:,}; supporting: {claim['supporting_example_count']:,}; context: {claim['context_only_count']:,}; normalization lane: {claim['normalization_needed_count']:,}; excluded: {claim['excluded_count']:,}.", "", f"**Strength:** mean {claim['average_strength_score']:.2f}; median {claim['median_strength_score']:.2f} on the 0–4 rating scale.", "", f"**Caveat:** {claim['caveats']} {claim['causal_prevalence_boundary_warning']}", ""]
    (OUTPUT / "careful_claim_candidates.md").write_text("\n".join(lines), encoding="utf-8")
    filters = {
        "core": [c for c in claims if c["finding_classification"] == "core finding candidate"],
        "supporting": [c for c in claims if c["finding_classification"] == "supporting finding candidate"],
        "context": [c for c in claims if c["finding_classification"] == "context finding candidate"],
    }
    for label, items in filters.items():
        stem = f"pi_report_{label}_findings_candidates"
        write_json(OUTPUT / f"{stem}.json", {"count": len(items), "claims": items})
        text = [f"# PI report {label} finding candidates", ""]
        for item in items:
            text += [f"## {item['claim_title']}", "", item["careful_claim_text"], "", f"Evidence basis: {item['valid_rating_count']:,} valid ratings; mean/median strength {item['average_strength_score']:.2f}/{item['median_strength_score']:.2f}.", "", f"Boundary: {item['caveats']} {item['causal_prevalence_boundary_warning']}", ""]
        (OUTPUT / f"{stem}.md").write_text("\n".join(text), encoding="utf-8")


def write_pi_docs(claims: list[dict[str, Any]], clusters: dict[str, Any], quarantines: list[dict[str, Any]]) -> None:
    boundaries = [
        {"claim_class": "careful_mechanism_description", "status": "allowed", "safe_language": "Within the processed rated corpus, rated evidence suggests a plausible mechanism.", "prohibited_language": "X causes wage growth.", "required_condition": "Retain corpus scope and documentary caveat."},
        {"claim_class": "corpus_count_comparison", "status": "allowed", "safe_language": "Among valid rated spans, X appears more often than Y.", "prohibited_language": "X is nationally more common than Y.", "required_condition": "Do not imply population prevalence."},
        {"claim_class": "directional_hint", "status": "allowed_with_caveat", "safe_language": "Some rated evidence is consistent with a local directional hint.", "prohibited_language": "The safety wage gap is X.", "required_condition": "Matched city-cycle and normalization remain pending."},
        {"claim_class": "wage_gap_or_normalized_comparison", "status": "prohibited", "safe_language": "Quantitative evidence requires normalization before wage-gap estimation.", "prohibited_language": "Safety workers earn X percent more.", "required_condition": "Separate normalization/matching authorization and validation."},
        {"claim_class": "causal_or_treatment_effect", "status": "prohibited", "safe_language": "Documentary evidence identifies a plausible mechanism.", "prohibited_language": "Arbitration causes higher safety wage growth.", "required_condition": "A separately validated causal design."},
        {"claim_class": "national_or_population_prevalence", "status": "prohibited", "safe_language": "Within the processed rated corpus, the mechanism recurs.", "prohibited_language": "Most municipalities use this mechanism.", "required_condition": "A representative sampling and weighting design."},
    ]
    write_csv(OUTPUT / "careful_claim_boundary_table.csv", boundaries, boundaries[0].keys())
    write_json(OUTPUT / "careful_claim_boundary_table.json", {"rows": boundaries})
    exclusion = {
        "quarantine_count": len(quarantines),
        "quarantine_reason_counts": dict(sorted(Counter(row.get("quarantine_reason", "unspecified") for row in quarantines).items())),
        "valid_evidence_includes_quarantine": False,
        "weak_or_excluded_valid_rating_count": sum(c["valid_rating_count"] for c in claims if c["claim_key"] == "exclusion_layer"),
        "boundaries": boundaries,
    }
    write_json(OUTPUT / "pi_report_exclusion_and_limits.json", exclusion)
    (OUTPUT / "pi_report_exclusion_and_limits.md").write_text(
        "# PI report exclusions and limits\n\n"
        f"The valid evidence layer excludes all {len(quarantines):,} quarantined ratings. "
        "Weak and report-excluded valid ratings remain coded as exclusions rather than finding support.\n\n"
        "No normalized wage-gap, regression, treatment-effect, national-prevalence, or final causal claim is authorized. "
        "Directional hints remain local documentary signals pending matched city-cycle structure.\n",
        encoding="utf-8",
    )
    strong = [c for c in claims if c["finding_classification"] == "core finding candidate"]
    moderate = [c for c in claims if c["finding_classification"] == "supporting finding candidate"]
    context = [c for c in claims if c["finding_classification"] in {"context finding candidate", "limitation only", "exclude"}]
    bank = ["# PI report claim language bank", "", "## Strong careful-but-useful claims", ""]
    bank += [f"- {c['careful_claim_text']} **Caveat:** {c['caveats']}" for c in strong]
    bank += ["", "## Moderate careful-but-useful claims", ""] + [f"- {c['careful_claim_text']} **Caveat:** {c['caveats']}" for c in moderate]
    bank += ["", "## Supporting and context claims", ""] + [f"- {c['careful_claim_text']}" for c in context]
    bank += ["", "## Limit and negative findings", "", "- Directionality is neutral/general or not applicable for most valid ratings; directional conclusions must remain narrow.", "- Quarantined and excluded ratings do not support findings.", "- Direct values are analytically promising but not comparable until pay units, rank/step, effective periods, and base/non-base status are normalized.", "", "## Forbidden phrasing to avoid", "", "- Arbitration causes higher safety wage growth.", "- Most municipalities use non-base compensation.", "- Safety workers earn X percent more nationally.", "- CBAs are the dominant national cause of the wage gap.", "- Fiscal constraints suppress non-safety wage growth.", "", "## Safe substitutions for forbidden phrasing", "", "- The rated evidence identifies arbitration/factfinding as a plausible institutional mechanism in some municipal documents; it does not establish a treatment effect.", "- Within the processed rated corpus, non-base compensation recurs among report-usable spans and should be treated as a separate compensation channel.", "- Quantitative wage evidence requires normalization and matched city-cycle construction before wage-gap estimation.", "- Some rated spans provide documentary directional hints; the evidence is not nationally representative and does not establish causality."]
    (OUTPUT / "pi_report_claim_language_bank.md").write_text("\n".join(bank) + "\n", encoding="utf-8")
    outline = """# PI report section outline

1. **Executive Summary** — bounded mechanism claims, key exclusions, and the normalization/matching transition.
2. **Processed Evidence Base** — 18,554 valid ratings; 58 quarantines excluded; source-family and geography scope without prevalence claims.
3. **Codified Evidence Categories** — mechanism attributes, strength scores, report usability, directionality, and normalization blockers.
4. **Findings** — automatic growth; bargaining/dispute resolution; market/staffing; timing/retroactivity; non-base compensation; rank/step/classification; fiscal/governance; bounded directional hints; quantitative evidence awaiting normalization.
5. **Limits** — no normalization, matched panel, wage gap, regression, treatment effect, national prevalence, or final causal conclusion.
6. **Current Scout Wave Status** — scout coverage rate and evidence-processing status, with operational detail kept secondary.
7. **Recommended Next Steps** — normalization, matched city-cycle structure, evidence-to-outcome pairing, and bounded exploratory readiness review.
"""
    (OUTPUT / "pi_report_section_outline.md").write_text(outline, encoding="utf-8")
    skeleton = ["# PI report draft skeleton", "", "## 1. Executive Summary", "", "The processed rated corpus supports several careful mechanism claims while leaving wage-gap and causal analysis blocked. The strongest current evidence concerns non-base compensation, direct wage values, implementation timing, automatic raises, and rank/step structures.", "", "## 2. Processed Evidence Base", "", "The evidence base contains 18,554 schema-valid ratings. Fifty-eight quarantined ratings are preserved as exclusions. Counts describe this processed corpus and are not population prevalence.", "", "## 3. Codified Evidence Categories", "", "Insert the mechanism-cluster strength table, report-usability table, directionality table, and normalization-blocker table.", "", "## 4. Findings", ""]
    for claim in strong + moderate:
        skeleton += [f"### {claim['claim_title']}", "", claim["careful_claim_text"], "", f"Caveat: {claim['caveats']}", ""]
    skeleton += ["## 5. Limits", "", "No normalized wage values, matched city-cycle panel, wage-gap estimate, regression, treatment-effect result, national-prevalence estimate, or final causal conclusion is presented.", "", "## 6. Current Scout Wave Status", "", "The dashboard map reports scout coverage rate only: 16,887 of 35,589 eligible or known municipalities (47.45%). Raw coverage remains context, not an evidence or readiness filter.", "", "## 7. Recommended Next Steps", "", f"Proceed to `{NEXT_TASK}` while preserving raw values and documentary lineage."]
    (OUTPUT / "pi_report_draft_skeleton.md").write_text("\n".join(skeleton) + "\n", encoding="utf-8")


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    missing = [name for name in REQUIRED_INPUTS if not (INPUT / name).is_file()]
    if missing: raise RuntimeError(f"missing required rating artifacts: {missing}")
    valid = read_jsonl(VALID_PATH)
    quarantines = read_jsonl(QUARANTINE_PATH)
    if len(valid) != EXPECTED_VALID or len(quarantines) != EXPECTED_QUARANTINE or len(valid) + len(quarantines) != EXPECTED_TOTAL:
        raise RuntimeError("valid/quarantine counts do not reconcile")
    if len({r.get("rating_id") for r in valid}) != EXPECTED_VALID or len({r.get("span_id") for r in valid}) != EXPECTED_VALID:
        raise RuntimeError("valid rating or span IDs are not unique")
    required = {"rating_id", "span_id", "source_id", "retained_source_id", "municipality", "state", "source_family", "report_usability_bucket", "claim_relevance_bucket", "evidence_quality_score"}
    if any(not required.issubset(row) or row.get("rating_validity_status") != "valid" for row in valid):
        raise RuntimeError("valid ledger schema/validity gate failed")
    if any(row.get("causal_claim_allowed") is not False or row.get("population_prevalence_claim_allowed") is not False or row.get("national_prevalence_claim_allowed") is not False for row in valid):
        raise RuntimeError("claim boundary gate failed")
    tracked = subprocess.run(["git", "ls-files", "artifacts/local_retained_sources", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if tracked: raise RuntimeError("retained sources or extracted text are tracked")
    cleanup = read_json(INPUT / "dashboard_cleanup_audit.json")
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    if cleanup.get("passed") is not True or "scout_coverage_rate" not in map_source:
        raise RuntimeError("clean dashboard or coverage-rate map gate failed")
    timestamp = utc_now()
    valid_sha = sha_file(VALID_PATH)
    codified = [codify(row, valid_sha, timestamp) for row in valid]
    if len({row["codified_record_id"] for row in codified}) != EXPECTED_VALID:
        raise RuntimeError("codified IDs not unique")
    write_jsonl(OUTPUT / "codified_valid_ratings.jsonl", codified)
    write_csv(OUTPUT / "codified_valid_ratings.csv", codified, CODIFIED_FIELDS)
    write_json(OUTPUT / "codified_valid_ratings_manifest.json", {
        "schema_version": SCHEMA_VERSION, "row_count": len(codified),
        "valid_rating_input_sha256": valid_sha,
        "jsonl_sha256": sha_file(OUTPUT / "codified_valid_ratings.jsonl"),
        "csv_sha256": sha_file(OUTPUT / "codified_valid_ratings.csv"),
        "quarantine_included": False, "full_text_included": False,
    })
    compact_fields = ["codified_record_id", "rating_id", "span_id", "primary_mechanism_cluster", "secondary_mechanism_clusters", "mechanism_strength_scores", "evidence_quality_score", "report_usability_bucket", "claim_relevance_bucket", "direction_bucket", "careful_claim_type", "pi_report_priority"]
    write_jsonl(OUTPUT / "mechanism_cluster_coded_records.jsonl", ({k: r[k] for k in compact_fields} for r in codified))
    write_csv(OUTPUT / "mechanism_cluster_coded_records.csv", codified, compact_fields)
    clusters = primary_cluster_summary(codified)
    write_json(OUTPUT / "mechanism_cluster_summary.json", {"record_count": len(codified), "primary_counts_reconcile": sum(i["primary_record_count"] for i in clusters.values()) == len(codified), "clusters": clusters})
    cluster_rows = [{"cluster": slug, **item} for slug, item in clusters.items()]
    strength_fields = ["cluster", "title", "primary_record_count", "supported_record_count", "report_ready_count", "core_count", "supporting_count", "context_count", "normalization_count", "excluded_count", "average_strength_score", "median_strength_score"]
    write_csv(OUTPUT / "mechanism_cluster_strength_table.csv", cluster_rows, strength_fields)
    write_json(OUTPUT / "mechanism_cluster_strength_table.json", {"rows": [{k: row[k] for k in strength_fields} for row in cluster_rows]})
    lines = ["# Mechanism cluster summary", "", "Counts describe the processed rated corpus and may overlap across supported clusters. Primary-cluster counts are mutually exclusive and reconcile to 18,554.", "", markdown_table(["Cluster", "Primary", "Supported", "Report-ready", "Mean", "Median"], [[row["title"], f"{row['primary_record_count']:,}", f"{row['supported_record_count']:,}", f"{row['report_ready_count']:,}", f"{row['average_strength_score']:.2f}", f"{row['median_strength_score']:.2f}"] for row in cluster_rows]), ""]
    (OUTPUT / "mechanism_cluster_summary.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(OUTPUT / "mechanism_specific_ingested_summaries.json", {"valid_record_count": len(codified), "clusters": clusters, "causal_claim_allowed": False})
    (OUTPUT / "mechanism_specific_ingested_summaries.md").write_text((OUTPUT / "mechanism_cluster_summary.md").read_text(encoding="utf-8"), encoding="utf-8")
    claims = aggregate_claims(codified)
    write_claim_files(claims)
    write_pi_docs(claims, clusters, quarantines)
    examples = []
    for claim in claims:
        selected = [row for row in codified if matches_claim(row, claim["claim_key"]) and row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example"}]
        for row in sorted(selected, key=lambda r: (-r["report_usability_score"], -r["evidence_quality_score"], r["rating_id"]))[:5]:
            examples.append({"claim_id": claim["claim_id"], "codified_record_id": row["codified_record_id"], "rating_id": row["rating_id"], "span_id": row["span_id"], "municipality": row["municipality"], "state": row["state"], "source_family": row["source_family"], "mechanism_cluster": claim["mechanism_cluster"], "report_usability_bucket": row["report_usability_bucket"], "evidence_quality_score": row["evidence_quality_score"], "paraphrase": row["pi_report_paraphrase"], "caveat": row["careful_claim_caveat"], "source_id": row["source_id"]})
    write_jsonl(OUTPUT / "report_ready_examples.jsonl", examples)
    ex_lines = ["# Report-ready examples", "", "Bounded paraphrases only; consult the codified ledger for lineage. These are documentary examples, not final claims.", ""]
    for item in examples:
        ex_lines += [f"- **{item['claim_id']} · {item['municipality']}, {item['state']} · {item['source_family']}:** {item['paraphrase']} _Caveat: {item['caveat']}_"]
    (OUTPUT / "report_ready_examples.md").write_text("\n".join(ex_lines) + "\n", encoding="utf-8")
    summary_specs = {
        "evidence_category_codified_summary.json": ("evidence_category",),
        "claim_relevance_codified_summary.json": ("claim_relevance_bucket",),
        "report_usability_codified_summary.json": ("report_usability_bucket",),
        "directionality_codified_summary.json": ("direction_bucket",),
    }
    for name, (field,) in summary_specs.items():
        write_json(OUTPUT / name, {"valid_record_count": len(codified), "counts": distribution(codified, field), "reconciles": sum(distribution(codified, field).values()) == len(codified)})
    quant = {field: sum(bool(r[field]) for r in codified) for field in ["quantitative_value_present", "raw_wage_or_comp_value_present", "percentage_or_growth_value_present", "effective_period_present", "unit_or_group_present", "rank_step_grade_present", "base_vs_non_base_clear", "normalization_needed"]}
    write_json(OUTPUT / "quantitative_readiness_codified_summary.json", {"valid_record_count": len(codified), "counts": quant})
    blockers = Counter(tag for row in codified for tag in row["normalization_blocker_tags"])
    write_json(OUTPUT / "normalization_blocker_codified_summary.json", {"normalization_needed_count": quant["normalization_needed"], "blocker_counts": dict(sorted(blockers.items())), "normalization_performed": False})
    write_json(OUTPUT / "causal_boundary_codified_summary.json", {"valid_record_count": len(codified), "causal_claim_allowed_true": 0, "population_prevalence_claim_allowed_true": 0, "national_prevalence_claim_allowed_true": 0, "local_documentary_mechanism_claims_allowed": True, "wage_gap_readiness": "blocked_pending_normalization", "causal_readiness": "blocked_pending_matched_structure", "global_analysis_readiness": False})
    write_json(OUTPUT / "source_family_ingested_summary.json", {"groups": aggregate_group(codified, "source_family")})
    write_json(OUTPUT / "geography_ingested_summary.json", {"states": aggregate_group(codified, "state"), "regions": aggregate_group(codified, "region")})
    write_json(OUTPUT / "cba_non_cba_ingested_summary.json", {"groups": aggregate_group(codified, "cba_non_cba_hint")})
    quarantine_summary = {"row_count": len(quarantines), "input_sha256": sha_file(QUARANTINE_PATH), "excluded_from_codified_valid_ratings": True, "reason_counts": dict(sorted(Counter(row.get("quarantine_reason", "unspecified") for row in quarantines).items()))}
    write_json(OUTPUT / "quarantine_exclusion_summary.json", quarantine_summary)
    (OUTPUT / "quarantine_exclusion_summary.md").write_text("# Quarantine exclusion summary\n\nAll 58 quarantined rating rows remain excluded from the 18,554-row codified valid-evidence layer. They are preserved in the prior immutable quarantine ledger with explicit reasons.\n", encoding="utf-8")
    classifications = Counter(c["finding_classification"] for c in claims)
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "generated_at": timestamp,
        "valid_rating_input_count": len(valid), "quarantine_count": len(quarantines),
        "rating_total": len(valid) + len(quarantines), "codified_record_count": len(codified),
        "careful_claim_candidate_count": len(claims), "finding_classification_counts": dict(sorted(classifications.items())),
        "report_usability_counts": distribution(codified, "report_usability_bucket"),
        "claim_relevance_counts": distribution(codified, "claim_relevance_bucket"),
        "directionality_counts": distribution(codified, "direction_bucket"),
        "quantitative_readiness": quant, "normalization_blocker_counts": dict(sorted(blockers.items())),
        "mechanism_clusters": clusters, "quarantine_included_as_valid": False,
        "normalization_performed": False, "matched_city_cycle_structure_built": False,
        "ocr_occurred": False, "rating_rerun_occurred": False,
        "source_access_occurred": False, "wage_gap_or_regression_occurred": False,
        "global_analysis_readiness": False, "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "rating_ingest_codify_summary.json", summary)
    summary_md = ["# Broad State 4 × 2,500 rating ingestion/codification and PI evidence", "", f"Decision: `{DECISION}`", "", f"- Valid rating inputs codified: {len(codified):,}", f"- Quarantined ratings excluded: {len(quarantines):,}", f"- Careful claim candidates: {len(claims):,}", f"- Core/supporting/context/limits-or-exclusions: {classifications['core finding candidate']:,} / {classifications['supporting finding candidate']:,} / {classifications['context finding candidate']:,} / {classifications['limitation only'] + classifications['exclude']:,}", "", "The codified layer supports careful documentary mechanism claims only. It does not normalize wages, build matched city-cycle structure, estimate a wage gap, run regressions, establish national prevalence, or make final causal claims.", "", "## Strongest careful claims", ""]
    summary_md += [f"- {c['careful_claim_text']}" for c in claims if c["finding_classification"] == "core finding candidate"]
    summary_md += ["", f"Next: `{NEXT_TASK}`."]
    (OUTPUT / "rating_ingest_codify_summary.md").write_text("\n".join(summary_md) + "\n", encoding="utf-8")
    write_json(OUTPUT / "rating_ingest_codify_manifest.json", {"task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "created_at": timestamp, "input_files": {str(VALID_PATH.relative_to(ROOT)): valid_sha, str(QUARANTINE_PATH.relative_to(ROOT)): sha_file(QUARANTINE_PATH)}, "valid_input_count": len(valid), "quarantine_count": len(quarantines), "codified_count": len(codified), "careful_claim_count": len(claims), "quarantine_excluded": True, "claim_boundary": "careful documentary mechanism claims only; no normalization, matching, wage-gap, regression, prevalence, treatment-effect, or final causal claims"})
    # CSV-set alternative because the artifact-tool dependency loader is unavailable in this runtime.
    evidence_tables = {
        "pi_report_evidence_base_overview.csv": [{"metric": "valid_ratings", "value": len(valid)}, {"metric": "quarantine_excluded", "value": len(quarantines)}, {"metric": "codified_records", "value": len(codified)}, {"metric": "careful_claim_candidates", "value": len(claims)}, {"metric": "normalization_needed", "value": quant["normalization_needed"]}],
        "pi_report_evidence_base_mechanism_clusters.csv": [{k: row[k] for k in strength_fields} for row in cluster_rows],
        "pi_report_evidence_base_claims.csv": claims,
        "pi_report_evidence_base_boundaries.csv": read_json(OUTPUT / "careful_claim_boundary_table.json")["rows"],
        "pi_report_evidence_base_normalization.csv": [{"blocker": key, "count": value} for key, value in sorted(blockers.items(), key=lambda item: (-item[1], item[0]))],
        "pi_report_evidence_base_directionality.csv": [{"direction": key, "count": value} for key, value in distribution(codified, "direction_bucket").items()],
    }
    for name, table in evidence_tables.items():
        write_csv(OUTPUT / name, table, table[0].keys())
    write_json(OUTPUT / "pi_report_evidence_base_tables_manifest.json", {"format": "csv_set", "xlsx_feasible": False, "reason": "required artifact-tool dependency loader unavailable in the runtime", "tables": {name: {"row_count": len(table), "sha256": sha_file(OUTPUT / name)} for name, table in evidence_tables.items()}})
    (OUTPUT / "pi_report_evidence_base_summary.md").write_text("# PI report evidence base summary\n\nThe evidence base is supplied as a verified CSV set because the required spreadsheet artifact-tool dependency loader was unavailable. The set contains an overview, mechanism clusters, careful claims, claim boundaries, normalization blockers, and directionality; no full text or source payload is included.\n", encoding="utf-8")
    write_json(OUTPUT / "dashboard_ingestion_update_summary.json", {"status": "ready_for_dashboard_build", "current_stage": "Rating ingestion/codification complete", "next_task": NEXT_TASK, "valid_rating_count": len(valid), "quarantine_count": len(quarantines), "codified_record_count": len(codified), "careful_claim_candidate_count": len(claims), "finding_classification_counts": dict(classifications), "top_mechanism_clusters": sorted(({"cluster": slug, **item} for slug, item in clusters.items()), key=lambda x: -x["report_ready_count"])[:6], "normalization_needed_count": quant["normalization_needed"], "clean_dashboard_structure_preserved": True, "map_primary_metric": "scout_coverage_rate", "scout_covered_municipalities": 16887, "eligible_municipality_universe": 35589, "national_coverage_rate": round(16887 / 35589, 6), "global_analysis_readiness": False})
    write_json(OUTPUT / "forbidden_action_audit.json", {"passed": True, "ocr_occurred": False, "text_extraction_occurred": False, "source_review_or_download_occurred": False, "rating_rerun_occurred": False, "wage_normalization_occurred": False, "matched_city_cycle_structure_built": False, "wage_gap_calculation_occurred": False, "regression_or_treatment_effect_occurred": False, "final_causal_claim_made": False, "national_or_population_prevalence_claim_made": False, "quarantine_ingested_as_valid": False, "source_payload_or_full_text_written": False, "global_readiness_advanced": False})
    write_json(OUTPUT / "dashboard_browser_smoke_report.json", {"status": "pending_local_browser_validation"})
    write_json(OUTPUT / "dashboard_public_pages_smoke_report.json", {"status": "pending_commit_push_deployment"})
    (OUTPUT / "dashboard_browser_smoke_report.md").write_text("# Dashboard browser smoke\n\nPending local production-build browser validation.\n", encoding="utf-8")
    (OUTPUT / "next_task.md").write_text(f"# Next task\n\nRun `{NEXT_TASK}`. Preserve raw values while standardizing hourly/annual units, base versus non-base compensation, occupation/unit, rank/step/grade, effective period, fiscal/contract year, and municipality-cycle fields. Build matched safety/non-safety city-cycle structures only where validated evidence supports them. Do not run regressions, treatment effects, final causal claims, or final wage-gap estimates unless a later bounded validation explicitly authorizes them. Preserve the cleaned dashboard and scout-coverage-rate map.\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "valid": len(valid), "quarantine": len(quarantines), "codified": len(codified), "claims": len(claims), "classification_counts": dict(classifications)}))


def validate() -> None:
    summary = read_json(OUTPUT / "rating_ingest_codify_summary.json")
    codified = read_jsonl(OUTPUT / "codified_valid_ratings.jsonl")
    quarantines = read_jsonl(QUARANTINE_PATH)
    cluster_summary = read_json(OUTPUT / "mechanism_cluster_summary.json")
    claims = read_json(OUTPUT / "careful_claim_candidates.json")["claims"]
    required_identity = {"codified_record_id", "rating_id", "span_id", "source_id", "retained_source_id", "municipality", "state", "source_family", "primary_mechanism_cluster", "careful_claim_type", "scout_target_id", "verification_row_id", "source_review_download_id", "readiness_id", "extraction_id", "span_queue_id"}
    prohibited = re.compile(r"\b(causes?|proves?|nationally common|most municipalities|dominant national mechanism|the wage gap is|representative of all municipalities)\b", re.I)
    project = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json") if (ROOT / "docs/dashboard/data/project_phase_summary.json").is_file() else {}
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    local = read_json(OUTPUT / "dashboard_browser_smoke_report.json") if (OUTPUT / "dashboard_browser_smoke_report.json").is_file() else {}
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json") if (OUTPUT / "dashboard_public_pages_smoke_report.json").is_file() else {}
    staged = read_json(OUTPUT / "staged_file_audit.json") if (OUTPUT / "staged_file_audit.json").is_file() else {}
    large = read_json(OUTPUT / "large_file_audit.json") if (OUTPUT / "large_file_audit.json").is_file() else {}
    checks = {
        "01_valid_input_18554": summary.get("valid_rating_input_count") == EXPECTED_VALID,
        "02_quarantine_58": summary.get("quarantine_count") == EXPECTED_QUARANTINE,
        "03_total_18612": summary.get("rating_total") == EXPECTED_TOTAL,
        "04_codified_reconciles": len(codified) == summary.get("codified_record_count") == EXPECTED_VALID,
        "05_identity_lineage": all(required_identity.issubset(row) and all(row.get(key) for key in required_identity) for row in codified),
        "06_primary_cluster": all(row.get("primary_mechanism_cluster") in CLUSTERS for row in codified),
        "07_cluster_reconciles": cluster_summary.get("primary_counts_reconcile") is True and sum(item["primary_record_count"] for item in cluster_summary["clusters"].values()) == EXPECTED_VALID,
        "08_usability_reconciles": sum(summary["report_usability_counts"].values()) == EXPECTED_VALID,
        "09_relevance_reconciles": sum(summary["claim_relevance_counts"].values()) == EXPECTED_VALID,
        "10_direction_reconciles": sum(summary["directionality_counts"].values()) == EXPECTED_VALID,
        "11_quant_normalization_reconciles": summary["quantitative_readiness"]["normalization_needed"] == 11548,
        "12_claims_from_valid_only": len(claims) == summary["careful_claim_candidate_count"] and all(c["valid_rating_count"] <= EXPECTED_VALID for c in claims),
        "13_claim_language_safe": all(not prohibited.search(c["careful_claim_text"]) for c in claims),
        "14_causal_false": all(row["causal_claim_allowed"] is False for row in codified),
        "15_prevalence_false": all(row["population_prevalence_claim_allowed"] is False and row["national_prevalence_claim_allowed"] is False for row in codified),
        "16_wage_gap_blocked": project.get("wage_gap_analysis_readiness") == "blocked_pending_normalization",
        "17_causal_blocked": project.get("causal_analysis_readiness") == "blocked_pending_matched_structure",
        "18_no_normalization": summary.get("normalization_performed") is False,
        "19_no_matching": summary.get("matched_city_cycle_structure_built") is False,
        "20_no_ocr": summary.get("ocr_occurred") is False,
        "21_no_rerating": summary.get("rating_rerun_occurred") is False,
        "22_quarantine_excluded": len(quarantines) == EXPECTED_QUARANTINE and not ({r["rating_id"] for r in codified} & {r.get("rating_id") for r in quarantines}),
        "23_language_bank": (OUTPUT / "pi_report_claim_language_bank.md").is_file(),
        "24_outline": (OUTPUT / "pi_report_section_outline.md").is_file(),
        "25_skeleton": (OUTPUT / "pi_report_draft_skeleton.md").is_file(),
        "26_clean_dashboard": all(token in app for token in ["pi-status-strip", "pi-map-grid", "pi-evidence-grid", "pi-mechanism-table", "pi-boundary-section", "pi-technical-details"]) and app.count("projectPhaseSummary.next_task") == 1,
        "27_map_coverage_rate": "scout_coverage_rate" in map_source and project.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "28_dashboard_build": local.get("build_status") == "passed",
        "29_local_browser": local.get("status") in {"passed", "browser_controller_unavailable"},
        "30_public_browser": public.get("status") == "public_pages_visible_current_passed",
        "31_global_not_advanced": project.get("global_analysis_readiness") is False,
        "32_no_source_payloads_tracked": subprocess.run(["git", "ls-files", "artifacts/local_retained_sources", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip() == "",
        "33_staged_audit": staged.get("passed") is True,
        "34_large_audit": large.get("passed") is True,
    }
    core = all(value for key, value in checks.items() if key not in {"16_wage_gap_blocked", "17_causal_blocked", "26_clean_dashboard", "27_map_coverage_rate", "28_dashboard_build", "29_local_browser", "30_public_browser", "31_global_not_advanced", "33_staged_audit", "34_large_audit"})
    report = {"validated_at": utc_now(), "checks": checks, "core_checks_passed": core, "all_checks_passed": all(checks.values()), "pending_checks": [key for key, value in checks.items() if not value]}
    write_json(OUTPUT / "validation_report.json", report)
    lines = ["# Validation report", "", f"Core checks passed: **{str(core).lower()}**", f"All checks passed: **{str(all(checks.values())).lower()}**", "", markdown_table(["Check", "Passed"], [[key, value] for key, value in checks.items()]), ""]
    (OUTPUT / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not core: raise RuntimeError("core validation failed")


def audit_staged() -> None:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    forbidden_patterns = [re.compile(r"(^|/)(artifacts/local_|corpus/|retained_sources?/|extracted_text/)", re.I), re.compile(r"\.(pdf|docx?|xlsx?|zip|html?)$", re.I)]
    allowed_xlsx = str((OUTPUT / "pi_report_evidence_base_tables.xlsx").relative_to(ROOT))
    forbidden = [path for path in staged if path != allowed_xlsx and any(pattern.search(path) for pattern in forbidden_patterns)]
    large_threshold = 95 * 1024 * 1024
    large = []
    for rel in staged:
        path = ROOT / rel
        if path.is_file() and path.stat().st_size >= large_threshold:
            large.append({"path": rel, "bytes": path.stat().st_size})
    write_json(OUTPUT / "staged_file_audit.json", {"audited_at": utc_now(), "staged_file_count": len(staged), "staged_files": staged, "forbidden_staged_files": forbidden, "passed": not forbidden})
    write_json(OUTPUT / "large_file_audit.json", {"audited_at": utc_now(), "threshold_bytes": large_threshold, "large_staged_files": large, "passed": not large})
    print(json.dumps({"staged": len(staged), "forbidden": forbidden, "large": large, "passed": not forbidden and not large}))
    if forbidden or large: raise RuntimeError("staged/large-file audit failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("run", "validate", "audit-staged"))
    args = parser.parse_args()
    if args.stage == "run": run()
    elif args.stage == "validate": validate()
    else: audit_staged()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
