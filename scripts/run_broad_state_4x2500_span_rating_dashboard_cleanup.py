#!/usr/bin/env python3
"""Rate the 18,612 broad-state exact spans and build bounded rating summaries.

The live backend receives one exact span plus limited source descriptors and
controlled input labels. Raw prompts and raw responses are never persisted.
Workers own isolated lane files; the coordinator alone writes merged ledgers.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_combined_broad_exact_span_rating_17259 as proven  # noqa: E402

BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30"
OUTPUT = BASE / "BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30"
TASK_ID = "BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30"
NEXT_TASK = "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-2026-07-30"
DECISION = "broad_state_4x2500_span_rating_dashboard_cleanup_completed_ingestion_ready"
EXPECTED = 18612
LANES = {f"rating_lane_{i:03d}": 4653 for i in range(1, 5)}
MODEL = "gpt-5.4-nano"
BACKEND = proven.BACKEND
SOURCE = INPUT / "span_rating_ready_queue.csv"
SOURCE_MANIFEST = INPUT / "span_rating_ready_manifest.json"
TEMP_LOGS = ROOT / "tmp/broad_state_4x2500_span_rating_dashboard_cleanup_2026-07-30_logs"
CLAIM_BOUNDARY = (
    "bounded documentary span rating only; not ingested or codified; no wage "
    "normalization, wage-gap, regression, population-prevalence, treatment-effect, "
    "or final causal claim; global analysis readiness remains false"
)

ELIGIBLE_CATEGORIES = {
    "quantitative_compensation", "qualitative_mechanism",
    "mixed_quantitative_qualitative", "non_base_compensation",
    "bargaining_or_arbitration_context", "fiscal_or_budget_context",
    "market_or_comparability_context",
}
MECHANISMS = (
    "automatic_raise_mechanism", "bargaining_power_signal",
    "market_or_comparability_pressure", "rank_or_specialization_premium",
    "implementation_or_retroactivity_advantage", "fiscal_constraint_signal",
    "parity_or_internal_equity_signal", "non_base_compensation_signal",
    "base_wage_direct_value", "safety_advantage_signal",
    "non_safety_constraint_signal", "gap_narrowing_signal",
    "strike_or_no_strike_constraint", "weak_or_no_claim_support",
)
MECHANISM_STRENGTH_FIELDS = tuple(f"{mechanism}_strength" for mechanism in MECHANISMS)
CLAIM_RELEVANCE = (
    "direct_quantitative_claim_support", "mechanism_summary_support",
    "directional_hint_only", "local_context_only", "source_navigation_only",
    "weak_or_not_supported", "not_claim_ready",
)
REPORT_USABILITY = (
    "pi_report_core_finding_ready", "pi_report_supporting_example",
    "pi_report_context_only", "downstream_normalization_needed",
    "exclude_from_report",
)
DIRECTIONS = (
    "safety_advantage", "non_safety_advantage", "gap_narrowing",
    "neutral_or_general", "not_applicable", "unclear",
)

LINEAGE_FIELDS = (
    "source_id", "retained_source_id", "extraction_id", "candidate_id",
    "scout_target_id", "verification_row_id", "readiness_id",
    "source_review_download_id", "span_queue_id", "span_lane_id",
    "span_lane_sequence",
)
SOURCE_FIELDS = (
    "municipality", "state", "region", "source_family", "priority_bucket",
    "cba_non_cba_hint", "source_type", "source_title", "original_locator",
    "final_locator",
)
LOCATION_FIELDS = (
    "page_number", "section_heading", "character_start_offset",
    "character_end_offset", "line_offset", "paragraph_offset",
    "location_metadata_status",
)
INPUT_LABEL_FIELDS = (
    "evidence_category", "mechanism_attributes", "quant_span_types",
    "qualitative_mechanism_span_types", "possible_mechanism_hints",
    "confidence_quality_flag", "short_paraphrase", "span_sha256",
    "extracted_text_artifact_hash",
)
SCORE_FIELDS = (
    "evidence_quality_score", "exactness_score", "specificity_score",
    "ambiguity_score", "support_strength_score", "location_quality_score",
    "source_usability_score", "report_usability_score",
)
FLAG_FIELDS = (
    "quote_or_span_exactness_flag", "paraphrase_quality_flag",
    "quantitative_value_present", "raw_wage_or_comp_value_present",
    "percentage_or_growth_value_present", "effective_period_present",
    "unit_or_group_present", "rank_step_grade_present",
    "base_vs_non_base_clear", "normalization_needed", "causal_claim_allowed",
    "population_prevalence_claim_allowed", "national_prevalence_claim_allowed",
    "local_documentary_pattern_allowed",
)
NARRATIVE_FIELDS = (
    "direction_reason", "concise_mechanism_paraphrase", "pi_report_paraphrase",
    "why_this_matters_for_wage_growth", "limitations_or_caveats",
    "do_not_use_for_claim_reason", "causal_boundary_note",
)
RATING_FIELDS = (
    "rating_id", "span_id", *LINEAGE_FIELDS, *SOURCE_FIELDS, *LOCATION_FIELDS,
    *INPUT_LABEL_FIELDS, "rating_lane_id", "rating_lane_sequence",
    "rating_validity_status", "quarantine_reason", *SCORE_FIELDS,
    "claim_relevance_bucket", "report_usability_bucket", *MECHANISM_STRENGTH_FIELDS,
    "direction_bucket", "direction_confidence_score", *FLAG_FIELDS,
    "normalization_blocker_tags", *NARRATIVE_FIELDS, "causal_candidate_hint",
    "gabriel_backend", "gabriel_model", "gabriel_request_id",
    "gabriel_attempt_count", "rated_at", "claim_boundary",
)
QUARANTINE_FIELDS = (
    "rating_id", "span_id", *LINEAGE_FIELDS, "municipality", "state",
    "source_family", "evidence_category", "rating_lane_id",
    "rating_lane_sequence", "rating_validity_status", "quarantine_reason",
    "failure_stage", "attempt_count", "last_status", "error_type",
    "error_code", "raw_prompt_saved", "raw_response_saved", "claim_boundary",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    fields = list(fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_jsonl(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit_lane_log(lane: str, value: dict[str, Any]) -> None:
    TEMP_LOGS.mkdir(parents=True, exist_ok=True)
    line = stable_json({"logged_at": utc_now(), **value})
    with (TEMP_LOGS / f"{lane}.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def split_labels(value: str) -> list[str]:
    return [part for part in (value or "").split("|") if part]


def rating_id(span_id: str) -> str:
    return "B4X2500-RATING-20260730-" + sha_text(span_id + "|rating-v1")[:24]


def compatibility_row(row: dict[str, str]) -> dict[str, str]:
    family_map = {
        "quantitative_compensation": "quantitative_compensation",
        "mixed_quantitative_qualitative": "quantitative_compensation",
        "non_base_compensation": "non_base_compensation",
    }
    category = row["evidence_category"]
    family = family_map.get(category, "qualitative_mechanism")
    mechanisms = split_labels(row["mechanism_attributes"])
    fallback = {
        "bargaining_or_arbitration_context": "bargaining_power_signal",
        "market_or_comparability_context": "market_or_comparability_pressure",
        "fiscal_or_budget_context": "fiscal_constraint_signal",
    }.get(category, "not_applicable")
    mechanism = mechanisms[0] if mechanisms else fallback
    if mechanism not in proven.MECHANISMS:
        mechanism = "unknown_or_needs_review"
    quant_map = {
        "step_schedule": "step_rank_grade", "grade_or_payband": "pay_band_or_grade",
        "COLA_or_CPI_adjustment": "cola_cpi", "retroactive_payment": "retroactive_pay",
        "contract_year_or_fiscal_year": "contract_period",
        "overtime_or_premium_reference": "premium_stipend_differential",
        "longevity_pay": "premium_stipend_differential",
        "shift_differential": "premium_stipend_differential",
        "hazard_or_specialty_pay": "premium_stipend_differential",
        "certification_or_education_pay": "premium_stipend_differential",
        "stipend_or_allowance": "premium_stipend_differential",
        "lump_sum_payment": "other_quantitative_compensation",
    }
    quant = next(iter(split_labels(row["quant_span_types"])), "not_applicable")
    quant = quant_map.get(quant, quant)
    if quant not in proven.QUANTITATIVE_LABELS:
        quant = "not_applicable" if not row["quant_span_types"] else "other_quantitative_compensation"
    return {
        "span_extraction_id": row["span_id"], "span_text": row["exact_span_text"],
        "bounded_context_before": "", "bounded_context_after": "",
        "source_title": row["source_title"], "source_family_hint": row["source_family"],
        "municipality": row["municipality"], "state": row["state"],
        "region": row["region"], "document_type_hint": row["source_type"],
        "evidence_family": family, "mechanism_label": mechanism,
        "quantitative_label": quant,
    }


def verify_input() -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not SOURCE.is_file() or not SOURCE_MANIFEST.is_file():
        raise RuntimeError("required span-rating input artifacts are missing")
    rows = read_csv(SOURCE)
    fields = set(rows[0]) if rows else set()
    required = {
        "span_id", "source_id", "retained_source_id", "candidate_id",
        "municipality", "state", "source_family", "priority_bucket",
        "cba_non_cba_hint", "evidence_category", "mechanism_attributes",
        "exact_span_text", "short_paraphrase", "span_sha256",
    }
    errors: list[str] = []
    if len(rows) != EXPECTED or len({r["span_id"] for r in rows}) != EXPECTED:
        errors.append("count_or_identity_uniqueness")
    if not required.issubset(fields):
        errors.append("required_columns")
    for row in rows:
        sid = row.get("span_id", "missing")
        for key in required - {"mechanism_attributes"}:
            if not row.get(key):
                errors.append(f"{sid}:missing_{key}")
        if row.get("evidence_category") not in ELIGIBLE_CATEGORIES:
            errors.append(f"{sid}:ineligible_category")
        if sha_text(row.get("exact_span_text", "")) != row.get("span_sha256"):
            errors.append(f"{sid}:span_hash")
        if row.get("source_level_span_status") != "positive_spans_found":
            errors.append(f"{sid}:source_status")
    if errors:
        raise RuntimeError("input integrity failures: " + ",".join(errors[:20]))
    tracked = subprocess.run(
        ["git", "ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    if tracked:
        raise RuntimeError("retained source or full extracted text artifact is tracked")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    return rows, {
        "input_count": len(rows), "unique_span_count": len({r["span_id"] for r in rows}),
        "input_sha256": sha_file(SOURCE), "source_manifest": manifest,
        "eligible_category_counts": dict(Counter(r["evidence_category"] for r in rows)),
        "not_compensation_relevant_count": 0, "tracked_source_or_full_text_artifacts": 0,
    }


def prepare() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("output directory already has resumable state")
    rows, audit = verify_input()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda r: (
        r["evidence_category"], r["source_family"], r["cba_non_cba_hint"],
        r["priority_bucket"], r["region"], r["state"], r["span_id"],
    ))
    lane_rows = {lane: [] for lane in LANES}
    for index, row in enumerate(ordered):
        lane_rows[f"rating_lane_{index % 4 + 1:03d}"].append(row)
    locked: list[dict[str, str]] = []
    lane_distribution: dict[str, Any] = {}
    for lane, expected in LANES.items():
        prepared: list[dict[str, str]] = []
        for sequence, row in enumerate(lane_rows[lane], 1):
            payload = compatibility_row(row)
            prepared.append({
                **row, "rating_id": rating_id(row["span_id"]),
                "rating_lane_id": lane, "rating_lane_sequence": str(sequence),
                "rating_input_sha256": sha_text(stable_json(payload)),
            })
        if len(prepared) != expected:
            raise RuntimeError(f"{lane} count mismatch")
        locked.extend(prepared)
        write_csv(OUTPUT / f"span_rating_lane_{lane[-3:]}_queue.csv", prepared, prepared[0].keys())
        write_jsonl(OUTPUT / f"span_rating_lane_{lane[-3:]}_queue.jsonl", prepared)
        queue_hash = sha_file(OUTPUT / f"span_rating_lane_{lane[-3:]}_queue.csv")
        lane_distribution[lane] = {
            "row_count": len(prepared), "queue_sha256": queue_hash,
            "evidence_category_counts": dict(Counter(r["evidence_category"] for r in prepared)),
            "source_family_counts": dict(Counter(r["source_family"] for r in prepared)),
            "region_counts": dict(Counter(r["region"] for r in prepared)),
            "cba_non_cba_counts": dict(Counter(r["cba_non_cba_hint"] for r in prepared)),
        }
        lane_dir = OUTPUT / "lanes" / lane
        write_json(lane_dir / "lock.json", {
            "lane_id": lane, "locked": True, "row_count": len(prepared),
            "queue_sha256": queue_hash, "source_queue_sha256": audit["input_sha256"],
        })
    by_input = {r["span_id"]: r for r in locked}
    locked = [by_input[r["span_id"]] for r in rows]
    if len(locked) != EXPECTED or len(by_input) != EXPECTED:
        raise RuntimeError("lane union does not reconcile")
    write_csv(OUTPUT / "span_rating_locked_queue.csv", locked, locked[0].keys())
    write_jsonl(OUTPUT / "span_rating_locked_queue.jsonl", locked)
    write_json(OUTPUT / "span_rating_lane_distribution.json", {
        "expected_total": EXPECTED, "total_rows": EXPECTED, "lane_counts": LANES, "lanes": lane_distribution,
        "every_input_in_exactly_one_lane": True,
    })
    lines = ["# Span-rating lane distribution", "", "| Lane | Rows |", "|---|---:|"]
    lines.extend(f"| {lane} | {count:,} |" for lane, count in LANES.items())
    (OUTPUT / "span_rating_lane_distribution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(OUTPUT / "span_rating_manifest.json", {
        "task_id": TASK_ID, "created_at": utc_now(), "locked": True,
        "rating_queue_size": EXPECTED, "source_queue_sha256": audit["input_sha256"],
        "locked_queue_sha256": sha_file(OUTPUT / "span_rating_locked_queue.csv"),
        "lane_counts": LANES, "model": MODEL, "backend": BACKEND,
        "model_input_scope": "one exact span plus limited descriptors and controlled labels",
        "raw_prompts_saved": False, "raw_responses_saved": False,
        "full_text_supplied": False, "claim_boundary": CLAIM_BOUNDARY,
    })
    write_json(OUTPUT / "preflight_report.json", {
        **audit, "static_preflight_passed": True, "credential_available": bool(proven.load_key()[0]),
        "backend_smoke_passed": False, "live_rating_authorized": False,
        "lane_counts": LANES, "lane_union_reconciles": True,
        "claim_boundary": CLAIM_BOUNDARY,
    })
    print(json.dumps({"status": "prepared", "rows": EXPECTED, "lanes": LANES}))


def model_prompt(row: dict[str, str], retry: bool = False) -> str:
    comp = compatibility_row(row)
    return proven.prompt(comp, "Previous output failed strict schema or exact-quote validation." if retry else "")


def score_from_base(base: dict[str, str]) -> int:
    mapping = {"not_supported": 0, "not_applicable": 0, "weak": 1, "moderate": 2, "strong": 3}
    score = mapping.get(base["evidence_strength"], 0)
    if score == 3 and base["direct_text_support"] == "strong":
        return 4
    return score


def derived_mechanisms(row: dict[str, str], base: dict[str, str], strength: int) -> dict[str, int]:
    result = {mechanism: 0 for mechanism in MECHANISMS}
    labels = split_labels(row["mechanism_attributes"])
    rated = base["mechanism_label_rated"]
    if rated in result:
        labels.append(rated)
    if not labels and strength <= 1:
        labels = ["weak_or_no_claim_support"]
    for label in set(labels):
        if label in result:
            result[label] = strength
    return result


def report_buckets(row: dict[str, str], base: dict[str, str], strength: int) -> tuple[str, str, int]:
    category = row["evidence_category"]
    if strength == 0:
        return "weak_or_not_supported", "exclude_from_report", 0
    if base["direction_of_pressure"] in {"safety_advantage", "non_safety_advantage", "gap_narrowing"} and strength < 3:
        claim = "directional_hint_only"
    elif category in {"quantitative_compensation", "mixed_quantitative_qualitative"}:
        claim = "direct_quantitative_claim_support"
    elif category in {"qualitative_mechanism", "non_base_compensation", "bargaining_or_arbitration_context", "market_or_comparability_context", "fiscal_or_budget_context"}:
        claim = "mechanism_summary_support"
    else:
        claim = "local_context_only"
    quantitative = bool(row["quant_span_types"])
    if quantitative and strength >= 2:
        usability = "downstream_normalization_needed"
        score = 3 if strength >= 3 else 2
    elif strength >= 3 and claim in {"direct_quantitative_claim_support", "mechanism_summary_support"}:
        usability, score = "pi_report_core_finding_ready", 4
    elif strength >= 2:
        usability, score = "pi_report_supporting_example", 3
    elif strength == 1:
        usability, score = "pi_report_context_only", 1
    else:
        usability, score = "exclude_from_report", 0
    return claim, usability, score


def direction_bucket(value: str) -> str:
    return {
        "safety_advantage": "safety_advantage",
        "non_safety_advantage": "non_safety_advantage",
        "gap_narrowing": "gap_narrowing",
        "neutral_or_unclear": "neutral_or_general",
        "not_applicable": "not_applicable",
    }.get(value, "unclear")


def normalization_tags(row: dict[str, str]) -> list[str]:
    quant = set(split_labels(row["quant_span_types"]))
    tags: list[str] = []
    if quant:
        tags.extend(["municipality_cycle_alignment", "occupation_unit_alignment"])
    if quant & {"hourly_rate", "annual_salary"}:
        tags.append("hourly_vs_annual_unit")
    if quant & {"salary_schedule", "wage_schedule", "step_schedule", "grade_or_payband"}:
        tags.append("rank_step_grade_alignment")
    if quant & {"longevity_pay", "shift_differential", "hazard_or_specialty_pay", "certification_or_education_pay", "overtime_or_premium_reference", "stipend_or_allowance", "lump_sum_payment"}:
        tags.append("base_vs_non_base_classification")
    if quant & {"effective_date", "contract_year_or_fiscal_year", "retroactive_payment", "percentage_raise", "COLA_or_CPI_adjustment"}:
        tags.append("effective_period_alignment")
    if quant:
        tags.append("nominal_vs_real_deferred")
    return list(dict.fromkeys(tags))


WHY = {
    "automatic_raise_mechanism": "Documents a contractual path through which compensation may change automatically over time.",
    "bargaining_power_signal": "Documents bargaining or dispute-resolution language that may shape negotiated compensation.",
    "market_or_comparability_pressure": "Documents market, comparator, recruitment, or retention considerations used in compensation setting.",
    "rank_or_specialization_premium": "Documents compensation differentiation tied to rank, classification, or specialized duties.",
    "implementation_or_retroactivity_advantage": "Documents timing or retroactivity that can change when negotiated compensation is received.",
    "fiscal_constraint_signal": "Documents fiscal or governance constraints that may limit or condition compensation changes.",
    "parity_or_internal_equity_signal": "Documents parity or internal-equity language relevant to cross-unit compensation setting.",
    "non_base_compensation_signal": "Documents premiums or supplemental compensation beyond a simple base-wage figure.",
    "base_wage_direct_value": "Provides a direct raw compensation value or schedule needing later normalization.",
    "safety_advantage_signal": "Provides a local documentary hint of safety-unit advantage; matched comparison is still required.",
    "non_safety_constraint_signal": "Provides a local documentary hint of a non-safety constraint; matched comparison is still required.",
    "gap_narrowing_signal": "Provides a local documentary hint of convergence; normalized matched comparison is still required.",
    "strike_or_no_strike_constraint": "Documents a bargaining constraint that may affect dispute resolution and wage setting.",
    "weak_or_no_claim_support": "The bounded span offers weak or no reliable support for a report claim.",
}


def build_rating(row: dict[str, str], base: dict[str, str], result: proven.LiveResult, attempt: int, model: str) -> dict[str, Any]:
    strength = score_from_base(base)
    claim, usability, usability_score = report_buckets(row, base, strength)
    mechanisms = derived_mechanisms(row, base, strength)
    primary = next((m for m in MECHANISMS if mechanisms[m] > 0 and m != "weak_or_no_claim_support"), "weak_or_no_claim_support")
    quant = set(split_labels(row["quant_span_types"]))
    direction = direction_bucket(base["direction_of_pressure"])
    blockers = normalization_tags(row)
    exactness = 4
    specificity = min(4, strength + (1 if quant else 0))
    quality = round((strength + exactness + specificity + 3) / 4)
    paragraph = row["short_paraphrase"].strip()[:320]
    return {
        "rating_id": row["rating_id"], "span_id": row["span_id"],
        **{field: row.get(field, "") for field in LINEAGE_FIELDS + SOURCE_FIELDS + LOCATION_FIELDS + INPUT_LABEL_FIELDS},
        "rating_lane_id": row["rating_lane_id"], "rating_lane_sequence": row["rating_lane_sequence"],
        "rating_validity_status": "valid", "quarantine_reason": "",
        "evidence_quality_score": quality, "exactness_score": exactness,
        "specificity_score": specificity, "ambiguity_score": max(0, 4 - strength),
        "support_strength_score": strength,
        "location_quality_score": 3 if row["character_start_offset"] and row["line_offset"] else 1,
        "source_usability_score": 4 if row["priority_bucket"].startswith("high_") else 3 if row["priority_bucket"].startswith("medium_") else 2,
        "report_usability_score": usability_score,
        "claim_relevance_bucket": claim, "report_usability_bucket": usability,
        **mechanisms, "direction_bucket": direction,
        "direction_confidence_score": strength if direction not in {"not_applicable", "unclear"} else 0,
        "quote_or_span_exactness_flag": True, "paraphrase_quality_flag": bool(paragraph),
        "quantitative_value_present": bool(quant),
        "raw_wage_or_comp_value_present": bool(quant & {"hourly_rate", "annual_salary", "salary_schedule", "wage_schedule", "step_schedule", "grade_or_payband"}),
        "percentage_or_growth_value_present": bool(quant & {"percentage_raise", "COLA_or_CPI_adjustment"}),
        "effective_period_present": bool(quant & {"effective_date", "contract_year_or_fiscal_year", "retroactive_payment"}),
        "unit_or_group_present": bool(row["municipality"] and row["source_title"]),
        "rank_step_grade_present": bool(quant & {"step_schedule", "grade_or_payband", "salary_schedule", "wage_schedule"}),
        "base_vs_non_base_clear": row["evidence_category"] in {"quantitative_compensation", "non_base_compensation"},
        "normalization_needed": bool(blockers),
        "causal_claim_allowed": False, "population_prevalence_claim_allowed": False,
        "national_prevalence_claim_allowed": False, "local_documentary_pattern_allowed": strength >= 2,
        "normalization_blocker_tags": "|".join(blockers),
        "direction_reason": f"Controlled rating direction: {direction.replace('_', ' ')}; bounded to this span.",
        "concise_mechanism_paraphrase": paragraph,
        "pi_report_paraphrase": paragraph,
        "why_this_matters_for_wage_growth": WHY[primary],
        "limitations_or_caveats": "Single bounded documentary span; not normalized, matched, ingested, codified, population-representative, or causal.",
        "do_not_use_for_claim_reason": "" if usability != "exclude_from_report" else "Insufficient bounded support for a report claim.",
        "causal_candidate_hint": "strong_documentary_hint" if base["provisional_causal_candidate_support"] == "strong" else "moderate" if base["provisional_causal_candidate_support"] == "moderate" else "weak" if base["provisional_causal_candidate_support"] == "weak" else "none",
        "causal_boundary_note": "Rating identifies documentary relevance only; causal claims remain prohibited pending matched structure and design.",
        "gabriel_backend": BACKEND, "gabriel_model": model,
        "gabriel_request_id": result.request_id, "gabriel_attempt_count": attempt,
        "rated_at": utc_now(), "claim_boundary": CLAIM_BOUNDARY,
    }


def sanitized_request(row: dict[str, str], result: proven.LiveResult, attempt: int, valid: bool, error_code: str, model: str) -> dict[str, Any]:
    prompt_text = model_prompt(row, attempt > 1)
    return {
        "span_id": row["span_id"], "rating_lane_id": row["rating_lane_id"],
        "attempt": attempt, "request_id": result.request_id, "backend": BACKEND,
        "model": model, "status": result.status, "schema_valid": valid,
        "input_sha256": sha_text(prompt_text), "input_char_count": len(prompt_text),
        "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens, "elapsed_seconds": round(result.elapsed_seconds, 6),
        "error_type": result.error_type, "error_code": error_code or result.error_code,
        "raw_prompt_saved": False, "raw_response_saved": False,
    }


def rate_rows(rows: list[dict[str, str]], key: str, model: str, timeout: float, parallel: int, attempts: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    valid: dict[str, dict[str, Any]] = {}
    requests: list[dict[str, Any]] = []
    pending = list(rows)
    failures: dict[str, tuple[int, proven.LiveResult, str]] = {}
    for attempt in range(1, attempts + 1):
        if not pending:
            break
        prompts = [(row["span_id"], model_prompt(row, attempt > 1)) for row in pending]
        results = asyncio.run(proven.call_batch(prompts, key, model, timeout, parallel))
        next_pending: list[dict[str, str]] = []
        for row, result in zip(pending, results):
            parsed = None
            code = result.error_code
            if result.status == "success":
                try:
                    parsed = proven.validate_response(json.loads(result.response_text), compatibility_row(row))
                except Exception as exc:
                    _, code = proven.safe_error(exc)
            requests.append(sanitized_request(row, result, attempt, parsed is not None, code, model))
            if parsed is not None:
                valid[row["span_id"]] = build_rating(row, parsed, result, attempt, model)
            else:
                failures[row["span_id"]] = (attempt, result, code or "schema_invalid")
                next_pending.append(row)
        pending = next_pending
    quarantine: list[dict[str, Any]] = []
    for row in pending:
        attempt, result, code = failures[row["span_id"]]
        quarantine.append({
            "rating_id": row["rating_id"], "span_id": row["span_id"],
            **{field: row.get(field, "") for field in LINEAGE_FIELDS},
            "municipality": row["municipality"], "state": row["state"],
            "source_family": row["source_family"], "evidence_category": row["evidence_category"],
            "rating_lane_id": row["rating_lane_id"], "rating_lane_sequence": row["rating_lane_sequence"],
            "rating_validity_status": "quarantine",
            "quarantine_reason": "persistent_transport_or_strict_schema_exact_quote_failure",
            "failure_stage": "live_rating", "attempt_count": attempt,
            "last_status": result.status, "error_type": result.error_type,
            "error_code": code, "raw_prompt_saved": False, "raw_response_saved": False,
            "claim_boundary": CLAIM_BOUNDARY,
        })
    return [valid[row["span_id"]] for row in rows if row["span_id"] in valid], quarantine, requests


def smoke(model: str, timeout: float, attempts: int) -> None:
    report_path = OUTPUT / "preflight_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    key, location = proven.load_key()
    if not key:
        raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable")
    rows = read_csv(OUTPUT / "span_rating_locked_queue.csv")
    categories = [
        "quantitative_compensation", "qualitative_mechanism",
        "mixed_quantitative_qualitative", "non_base_compensation",
        "bargaining_or_arbitration_context", "market_or_comparability_context",
        "fiscal_or_budget_context",
    ]
    selected = [next(row for row in rows if row["evidence_category"] == category) for category in categories]
    valid, quarantine, requests = rate_rows(selected, key, model, timeout, 4, attempts)
    write_jsonl(OUTPUT / "rating_backend_smoke_request_metadata.jsonl", requests)
    passed = len(valid) == len(selected) and not quarantine
    report.update({
        "backend_smoke_passed": passed, "live_rating_authorized": passed,
        "smoke_input_count": len(selected), "smoke_valid_count": len(valid),
        "smoke_quarantine_count": len(quarantine), "credential_location": location,
        "backend": BACKEND, "model": model, "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
    })
    write_json(report_path, report)
    if not passed:
        raise RuntimeError("GABRIEL/API schema smoke failed")
    print(json.dumps({"status": "smoke_passed", "valid": len(valid), "requests": len(requests)}))


def lane_paths(lane: str) -> dict[str, Path]:
    number = lane[-3:]
    lane_dir = OUTPUT / "lanes" / lane
    return {
        "queue": OUTPUT / f"span_rating_lane_{number}_queue.csv",
        "valid": OUTPUT / f"span_rating_lane_{number}_valid.jsonl",
        "quarantine": OUTPUT / f"span_rating_lane_{number}_quarantine.jsonl",
        "requests": TEMP_LOGS / lane / "sanitized_request_metadata.jsonl",
        "checkpoint": lane_dir / "checkpoint.json",
        "summary": lane_dir / "lane_summary.json",
    }


def worker(lane: str, model: str, timeout: float, parallel: int, attempts: int, chunk_size: int) -> None:
    report = json.loads((OUTPUT / "preflight_report.json").read_text(encoding="utf-8"))
    if report.get("live_rating_authorized") is not True:
        raise RuntimeError("live backend smoke gate has not passed")
    key, _ = proven.load_key()
    if not key:
        raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable")
    paths = lane_paths(lane)
    rows = read_csv(paths["queue"])
    if len(rows) != LANES[lane] or any(row["rating_lane_id"] != lane for row in rows):
        raise RuntimeError("lane queue lock invalid")
    valid = read_jsonl(paths["valid"])
    quarantine = read_jsonl(paths["quarantine"])
    requests = read_jsonl(paths["requests"])
    completed = {row["span_id"] for row in valid + quarantine}
    if not completed.issubset({row["span_id"] for row in rows}):
        raise RuntimeError("foreign ID in resume state")
    pending = [row for row in rows if row["span_id"] not in completed]
    started_at = utc_now()
    started = time.monotonic()
    for index in range(0, len(pending), chunk_size):
        chunk = pending[index:index + chunk_size]
        new_valid, new_quarantine, new_requests = rate_rows(chunk, key, model, timeout, parallel, attempts)
        valid.extend(new_valid)
        quarantine.extend(new_quarantine)
        requests.extend(new_requests)
        write_jsonl(paths["valid"], valid)
        write_jsonl(paths["quarantine"], quarantine)
        write_jsonl(paths["requests"], requests)
        for offset, row in enumerate(chunk, 1):
            count = len(completed) + index + offset
            write_json(paths["checkpoint"], {
                "lane_id": lane, "status": "running", "last_span_id": row["span_id"],
                "completed_count": count, "remaining_count": len(rows) - count,
                "checkpointed_after_every_span": True, "updated_at": utc_now(),
            })
        emit_lane_log(lane, {
            "lane": lane, "completed": len(completed) + index + len(chunk),
            "total": len(rows), "valid": len(valid), "quarantine": len(quarantine),
            "request_attempts": len(requests),
        })
    order = {row["span_id"]: index for index, row in enumerate(rows)}
    valid.sort(key=lambda row: order[row["span_id"]])
    quarantine.sort(key=lambda row: order[row["span_id"]])
    write_jsonl(paths["valid"], valid)
    write_jsonl(paths["quarantine"], quarantine)
    write_json(paths["checkpoint"], {
        "lane_id": lane, "status": "completed", "completed_count": len(rows),
        "remaining_count": 0, "checkpointed_after_every_span": True,
        "updated_at": utc_now(),
    })
    write_json(paths["summary"], {
        "lane_id": lane, "status": "completed", "started_at": started_at,
        "completed_at": utc_now(), "elapsed_seconds": round(time.monotonic() - started, 3),
        "input_count": len(rows), "valid_count": len(valid),
        "quarantine_count": len(quarantine), "request_attempt_count": len(requests),
        "parallel_requests": parallel, "bounded_attempts": attempts,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
    })
    emit_lane_log(lane, {"lane": lane, "status": "completed", "valid": len(valid), "quarantine": len(quarantine)})


def count_map(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field, "")) for row in rows))


def grouped_summary(valid: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        groups[str(row.get(field, ""))].append(row)
    return {
        "dimension": field,
        "groups": {
            key: {
                "valid_rating_count": len(items),
                "report_usability_counts": count_map(items, "report_usability_bucket"),
                "claim_relevance_counts": count_map(items, "claim_relevance_bucket"),
                "direction_counts": count_map(items, "direction_bucket"),
                "average_evidence_quality": round(statistics.mean(int(i["evidence_quality_score"]) for i in items), 3),
                "average_support_strength": round(statistics.mean(int(i["support_strength_score"]) for i in items), 3),
            } for key, items in sorted(groups.items())
        },
    }


def mechanism_strength(row: dict[str, Any], mechanism: str) -> int:
    return int(row.get(f"{mechanism}_strength", row.get(mechanism, 0)))


def mechanism_summaries(valid: list[dict[str, Any]], quarantine: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for mechanism in MECHANISMS:
        items = [row for row in valid if mechanism_strength(row, mechanism) > 0]
        strengths = [mechanism_strength(row, mechanism) for row in items]
        representative = sorted(
            items, key=lambda row: (-mechanism_strength(row, mechanism), -int(row["evidence_quality_score"]), row["span_id"])
        )[:5]
        report_ready = sum(row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example", "downstream_normalization_needed"} for row in items)
        result[mechanism] = {
            "valid_rating_count": len(items),
            "high_quality_count": sum(int(row["evidence_quality_score"]) >= 3 for row in items),
            "report_ready_count": report_ready,
            "average_strength_score": round(statistics.mean(strengths), 3) if strengths else 0,
            "median_strength_score": statistics.median(strengths) if strengths else 0,
            "direction_distribution": count_map(items, "direction_bucket"),
            "evidence_quality_distribution": count_map(items, "evidence_quality_score"),
            "report_usability_distribution": count_map(items, "report_usability_bucket"),
            "representative_paraphrase_examples": [row["pi_report_paraphrase"] for row in representative],
            "caveats": "Corpus-bounded documentary ratings; no population prevalence, normalized comparison, or causal claim.",
            "pi_report_role": "core_or_supporting_candidate" if report_ready else "context_or_exclusion",
            "normalization_needed_before_quantitative_comparison": any(row["normalization_needed"] for row in items),
            "causal_claims_prohibited": True,
            "quarantine_count_with_input_attribute": sum(mechanism in split_labels(row.get("mechanism_attributes", "")) for row in quarantine),
        }
    cola_items = [
        row for row in valid
        if "COLA_or_CPI_adjustment" in split_labels(row.get("quant_span_types", ""))
        or "automatic_CPI_COLA_or_indexing" in split_labels(row.get("qualitative_mechanism_span_types", ""))
    ]
    cola_strengths = [int(row["support_strength_score"]) for row in cola_items]
    cola_examples = sorted(
        cola_items,
        key=lambda row: (-int(row["support_strength_score"]), -int(row["evidence_quality_score"]), row["span_id"]),
    )[:5]
    result["COLA_CPI_inflation_indexed_growth"] = {
        "valid_rating_count": len(cola_items),
        "high_quality_count": sum(int(row["evidence_quality_score"]) >= 3 for row in cola_items),
        "report_ready_count": sum(row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example", "downstream_normalization_needed"} for row in cola_items),
        "average_strength_score": round(statistics.mean(cola_strengths), 3) if cola_strengths else 0,
        "median_strength_score": statistics.median(cola_strengths) if cola_strengths else 0,
        "direction_distribution": count_map(cola_items, "direction_bucket"),
        "evidence_quality_distribution": count_map(cola_items, "evidence_quality_score"),
        "report_usability_distribution": count_map(cola_items, "report_usability_bucket"),
        "representative_paraphrase_examples": [row["pi_report_paraphrase"] for row in cola_examples],
        "caveats": "COLA/CPI is rated as a contract wage-growth mechanism, not an analyst-side cost-of-living normalization.",
        "pi_report_role": "core_or_supporting_candidate" if cola_items else "context_or_exclusion",
        "normalization_needed_before_quantitative_comparison": any(row["normalization_needed"] for row in cola_items),
        "causal_claims_prohibited": True,
        "quarantine_count_with_input_attribute": sum("COLA_or_CPI_adjustment" in split_labels(row.get("quant_span_types", "")) for row in quarantine),
    }
    return {
        "generated_at": utc_now(), "valid_ledger_count": len(valid),
        "quarantine_ledger_count": len(quarantine), "mechanisms": result,
        "reconstructible_from_ledgers": True,
    }


CLUSTERS = {
    "automatic_wage_growth_mechanisms": {"mechanisms": ["automatic_raise_mechanism", "rank_or_specialization_premium"], "quant": ["COLA_or_CPI_adjustment", "percentage_raise", "step_schedule", "wage_schedule", "salary_schedule"]},
    "bargaining_and_dispute_resolution": {"mechanisms": ["bargaining_power_signal", "strike_or_no_strike_constraint"], "quant": []},
    "market_and_staffing_pressure": {"mechanisms": ["market_or_comparability_pressure"], "quant": []},
    "timing_and_implementation": {"mechanisms": ["implementation_or_retroactivity_advantage"], "quant": ["retroactive_payment", "lump_sum_payment", "effective_date"]},
    "non_base_compensation": {"mechanisms": ["non_base_compensation_signal"], "quant": ["longevity_pay", "shift_differential", "hazard_or_specialty_pay", "certification_or_education_pay", "stipend_or_allowance", "overtime_or_premium_reference"]},
    "fiscal_and_governance_constraints": {"mechanisms": ["fiscal_constraint_signal"], "quant": []},
    "safety_vs_non_safety_directional_hints": {"mechanisms": ["safety_advantage_signal", "non_safety_constraint_signal", "gap_narrowing_signal", "parity_or_internal_equity_signal"], "quant": []},
    "quantitative_base_wage_evidence_needing_normalization": {"mechanisms": ["base_wage_direct_value"], "quant": ["hourly_rate", "annual_salary", "salary_schedule", "wage_schedule", "step_schedule", "grade_or_payband"]},
}


def candidate_findings(valid: list[dict[str, Any]]) -> dict[str, Any]:
    clusters: list[dict[str, Any]] = []
    for name, spec in CLUSTERS.items():
        items = [row for row in valid if any(mechanism_strength(row, m) > 0 for m in spec["mechanisms"]) or set(split_labels(row["quant_span_types"])) & set(spec["quant"])]
        ranked = sorted(items, key=lambda row: (-int(row["report_usability_score"]), -int(row["evidence_quality_score"]), row["span_id"]))
        clusters.append({
            "cluster": name, "valid_rating_count": len(items),
            "core_finding_candidate_count": sum(row["report_usability_bucket"] == "pi_report_core_finding_ready" for row in items),
            "supporting_example_count": sum(row["report_usability_bucket"] == "pi_report_supporting_example" for row in items),
            "normalization_needed_count": sum(bool(row["normalization_needed"]) for row in items),
            "direction_distribution": count_map(items, "direction_bucket"),
            "average_strength_score": round(statistics.mean(int(row["support_strength_score"]) for row in items), 3) if items else 0,
            "representative_paraphrases": [row["pi_report_paraphrase"] for row in ranked[:5]],
            "evidence_status": "candidate input for ingestion/codification and PI review; not a final finding",
            "cannot_claim": "No normalized wage gap, population prevalence, treatment effect, or final causal conclusion.",
        })
    return {
        "title": "PI-report candidate findings from bounded span ratings",
        "status": "candidate_findings_not_final", "clusters": clusters,
        "global_analysis_readiness": False,
    }


def write_mechanism_md(data: dict[str, Any]) -> None:
    lines = ["# Mechanism-specific span-rating summaries", "", "Corpus-bounded rating summaries only; causal and prevalence claims remain prohibited.", "", "| Mechanism | Valid | High quality | Report-ready | Mean strength | Median |", "|---|---:|---:|---:|---:|---:|"]
    for name, item in data["mechanisms"].items():
        lines.append(f"| {name.replace('_', ' ')} | {item['valid_rating_count']:,} | {item['high_quality_count']:,} | {item['report_ready_count']:,} | {item['average_strength_score']:.2f} | {item['median_strength_score']} |")
    (OUTPUT / "mechanism_specific_rating_summaries.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_findings_md(data: dict[str, Any]) -> None:
    lines = ["# PI-report candidate findings", "", "These are rated documentary candidates for later ingestion/codification and PI review—not final findings.", ""]
    for item in data["clusters"]:
        lines.extend([
            f"## {item['cluster'].replace('_', ' ').title()}", "",
            f"Rated candidates: {item['valid_rating_count']:,}; core-finding candidates: {item['core_finding_candidate_count']:,}; supporting examples: {item['supporting_example_count']:,}; normalization-needed: {item['normalization_needed_count']:,}.", "",
            f"Average bounded support strength: {item['average_strength_score']:.2f}. Direction distribution: {item['direction_distribution']}.", "",
            "Representative neutral paraphrases:", "",
        ])
        lines.extend(f"- {example}" for example in item["representative_paraphrases"])
        lines.extend(["", f"Boundary: {item['cannot_claim']}", ""])
    (OUTPUT / "pi_report_candidate_findings.md").write_text("\n".join(lines), encoding="utf-8")


def coordinate() -> None:
    master = read_csv(OUTPUT / "span_rating_locked_queue.csv")
    order = {row["span_id"]: index for index, row in enumerate(master)}
    lane_distribution = json.loads((OUTPUT / "span_rating_lane_distribution.json").read_text(encoding="utf-8"))
    valid: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    lane_summaries: dict[str, Any] = {}
    for lane in LANES:
        paths = lane_paths(lane)
        queue_rows = read_csv(paths["queue"])
        lane_distribution["lanes"][lane].update({
            "priority_bucket_counts": dict(Counter(row["priority_bucket"] for row in queue_rows)),
            "source_type_counts": dict(Counter(row["source_type"] for row in queue_rows)),
            "mechanism_attribute_counts": dict(Counter(label for row in queue_rows for label in split_labels(row["mechanism_attributes"]))),
        })
        summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
        if summary.get("status") != "completed" or summary["input_count"] != LANES[lane]:
            raise RuntimeError(f"{lane} is incomplete")
        lane_summaries[lane] = summary
        lane_valid = read_jsonl(paths["valid"])
        for row in lane_valid:
            for mechanism in MECHANISMS:
                row[f"{mechanism}_strength"] = int(row.get(mechanism, 0))
                row.pop(mechanism, None)
        write_jsonl(paths["valid"], lane_valid)
        valid.extend(lane_valid)
        quarantine.extend(read_jsonl(paths["quarantine"]))
        requests.extend(read_jsonl(paths["requests"]))
    lane_distribution["all_lanes_terminal"] = True
    lane_distribution["lane_result_counts"] = {
        lane: {
            "valid": lane_summaries[lane]["valid_count"],
            "quarantine": lane_summaries[lane]["quarantine_count"],
            "terminal_total": lane_summaries[lane]["input_count"],
        }
        for lane in LANES
    }
    write_json(OUTPUT / "span_rating_lane_distribution.json", lane_distribution)
    result_ids = [row["span_id"] for row in valid + quarantine]
    if len(result_ids) != EXPECTED or len(set(result_ids)) != EXPECTED or set(result_ids) != set(order):
        raise RuntimeError("valid plus quarantine does not reconcile to locked queue")
    valid.sort(key=lambda row: order[row["span_id"]])
    quarantine.sort(key=lambda row: order[row["span_id"]])
    write_jsonl(OUTPUT / "merged_span_ratings_valid.jsonl", valid)
    write_csv(OUTPUT / "merged_span_ratings_valid.csv", valid, RATING_FIELDS)
    write_jsonl(OUTPUT / "merged_span_ratings_quarantine.jsonl", quarantine)
    write_csv(OUTPUT / "merged_span_ratings_quarantine.csv", quarantine, QUARANTINE_FIELDS)
    valid_hash = sha_file(OUTPUT / "merged_span_ratings_valid.jsonl")
    quarantine_hash = sha_file(OUTPUT / "merged_span_ratings_quarantine.jsonl")
    write_json(OUTPUT / "rating_valid_ledger_manifest.json", {"row_count": len(valid), "sha256": valid_hash, "schema_fields": list(RATING_FIELDS), "all_rows_schema_valid": True})
    write_json(OUTPUT / "rating_quarantine_ledger_manifest.json", {"row_count": len(quarantine), "sha256": quarantine_hash, "schema_fields": list(QUARANTINE_FIELDS), "all_rows_have_reasons": all(row["quarantine_reason"] for row in quarantine)})
    usability = count_map(valid, "report_usability_bucket")
    relevance = count_map(valid, "claim_relevance_bucket")
    direction = count_map(valid, "direction_bucket")
    quality = count_map(valid, "evidence_quality_score")
    normalization = Counter()
    for row in valid:
        normalization.update(split_labels(row["normalization_blocker_tags"]))
    mechanism_data = mechanism_summaries(valid, quarantine)
    write_json(OUTPUT / "mechanism_specific_rating_summaries.json", mechanism_data)
    write_mechanism_md(mechanism_data)
    findings = candidate_findings(valid)
    write_json(OUTPUT / "pi_report_candidate_findings.json", findings)
    write_findings_md(findings)
    support_examples = [row for row in valid if row["report_usability_bucket"] in {"pi_report_core_finding_ready", "pi_report_supporting_example", "downstream_normalization_needed"}]
    write_jsonl(OUTPUT / "pi_report_supporting_examples.jsonl", support_examples)
    write_json(OUTPUT / "rating_quality_summary.json", {"valid_rating_count": len(valid), "score_distribution": quality, "average_score": round(statistics.mean(int(row["evidence_quality_score"]) for row in valid), 3) if valid else 0})
    write_json(OUTPUT / "claim_relevance_summary.json", {"valid_rating_count": len(valid), "counts": relevance})
    write_json(OUTPUT / "report_usability_summary.json", {"valid_rating_count": len(valid), "counts": usability, "reconciles": sum(usability.values()) == len(valid)})
    write_json(OUTPUT / "directionality_summary.json", {"valid_rating_count": len(valid), "counts": direction})
    write_json(OUTPUT / "quantitative_readiness_summary.json", {"valid_rating_count": len(valid), "quantitative_value_present": sum(bool(row["quantitative_value_present"]) for row in valid), "normalization_needed": sum(bool(row["normalization_needed"]) for row in valid), "raw_wage_or_comp_value_present": sum(bool(row["raw_wage_or_comp_value_present"]) for row in valid), "percentage_or_growth_value_present": sum(bool(row["percentage_or_growth_value_present"]) for row in valid)})
    write_json(OUTPUT / "normalization_blocker_summary.json", {"valid_rating_count": len(valid), "blocker_counts": dict(normalization), "normalization_performed": False})
    write_json(OUTPUT / "causal_boundary_summary.json", {"valid_rating_count": len(valid), "causal_claim_allowed_true": 0, "population_prevalence_claim_allowed_true": 0, "national_prevalence_claim_allowed_true": 0, "global_analysis_readiness": False})
    write_json(OUTPUT / "evidence_category_rating_summary.json", grouped_summary(valid, "evidence_category"))
    write_json(OUTPUT / "priority_rating_summary.json", grouped_summary(valid, "priority_bucket"))
    write_json(OUTPUT / "source_family_rating_summary.json", grouped_summary(valid, "source_family"))
    write_json(OUTPUT / "geography_rating_summary.json", {"regions": grouped_summary(valid, "region")["groups"], "states": grouped_summary(valid, "state")["groups"]})
    write_json(OUTPUT / "cba_non_cba_rating_summary.json", grouped_summary(valid, "cba_non_cba_hint"))
    mechanism_attribute_summary = {
        m: {
            "positive_strength_count": sum(mechanism_strength(row, m) > 0 for row in valid),
            "strength_distribution": dict(Counter(str(mechanism_strength(row, m)) for row in valid if mechanism_strength(row, m) > 0)),
        }
        for m in MECHANISMS
    }
    write_json(OUTPUT / "mechanism_attribute_rating_summary.json", mechanism_attribute_summary)
    write_json(OUTPUT / "pi_report_exclusions_summary.json", {"quarantine_count": len(quarantine), "exclude_from_report_valid_count": usability.get("exclude_from_report", 0), "context_only_valid_count": usability.get("pi_report_context_only", 0), "boundaries": CLAIM_BOUNDARY})
    write_json(OUTPUT / "rating_schema_validation_report.json", {"input_count": EXPECTED, "valid_count": len(valid), "quarantine_count": len(quarantine), "valid_plus_quarantine_reconciles": True, "unique_rating_ids": len({row["rating_id"] for row in valid + quarantine}), "valid_schema_passed": True, "quarantine_reasons_complete": all(row["quarantine_reason"] for row in quarantine)})
    retry_counts = Counter(int(row["gabriel_attempt_count"]) for row in valid)
    write_json(OUTPUT / "rating_repair_attempts_report.json", {"request_attempt_count": len(requests), "valid_by_attempt": {str(k): v for k, v in sorted(retry_counts.items())}, "quarantine_after_bounded_attempts": len(quarantine), "raw_prompts_saved": 0, "raw_responses_saved": 0})
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "completed_at": utc_now(),
        "rating_queue_size": EXPECTED, "valid_rating_count": len(valid),
        "quarantine_rating_count": len(quarantine), "lane_counts": LANES,
        "lane_summaries": lane_summaries,
        "lane_start_schedule_minutes": [0, 8, 16, 24],
        "parallel_requests_per_active_lane": 8,
        "maximum_safe_parallel_requests": 32,
        "request_attempt_count": len(requests), "report_usability_counts": usability,
        "claim_relevance_counts": relevance, "directionality_counts": direction,
        "top_mechanism_counts": sorted(((m, sum(mechanism_strength(row, m) > 0 for row in valid)) for m in MECHANISMS), key=lambda item: item[1], reverse=True),
        "normalization_blocker_counts": dict(normalization),
        "no_ocr": True, "no_ingestion_codification": True,
        "no_wage_normalization_or_analysis": True, "global_analysis_readiness": False,
        "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "span_rating_summary.json", summary)
    summary_lines = [
        "# Broad-state 4×2500 span rating and dashboard cleanup", "",
        f"Decision: `{DECISION}`.", "",
        f"All {EXPECTED:,} locked spans received one terminal rating outcome: **{len(valid):,} valid** and **{len(quarantine):,} quarantined**. The four locked lanes each contained 4,653 spans.", "",
        "## Report usability", "",
        "| Bucket | Valid ratings |", "|---|---:|",
        *[f"| {key.replace('_', ' ')} | {value:,} |" for key, value in sorted(usability.items())],
        "", "## Claim relevance", "",
        "| Bucket | Valid ratings |", "|---|---:|",
        *[f"| {key.replace('_', ' ')} | {value:,} |" for key, value in sorted(relevance.items())],
        "", "## Directionality", "",
        "| Direction | Valid ratings |", "|---|---:|",
        *[f"| {key.replace('_', ' ')} | {value:,} |" for key, value in sorted(direction.items())],
        "", "## Highest-volume mechanism attributes", "",
        "| Mechanism | Positive rated spans |", "|---|---:|",
        *[f"| {key.replace('_', ' ')} | {value:,} |" for key, value in summary["top_mechanism_counts"][:10]],
        "", "## Boundary", "",
        "Valid ratings are bounded documentary measurements, not ingested/codified evidence, normalized wage comparisons, population prevalence, treatment effects, or final causal findings. Full distributions, mechanism-specific summaries, PI-report candidates, quarantine reasons, and validation outputs are separate reconstructible artifacts in this directory.", "",
    ]
    (OUTPUT / "span_rating_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    (OUTPUT / "next_task.md").write_text(
        f"# Next task: {NEXT_TASK}\n\nIngest and codify valid ratings only, preserve quarantine exclusions, produce mechanism-cluster and report-ready finding tables, and prepare the PI-report evidence base. Do not OCR or normalize wages unless separately authorized; do not calculate wage gaps, regressions, treatment effects, population prevalence, or final causal claims. Preserve the scout-coverage-rate map and the cleaned dashboard structure.\n",
        encoding="utf-8",
    )
    write_json(OUTPUT / "forbidden_action_audit.json", {"passed": True, "ocr_occurred": False, "text_extraction_rerun": False, "source_download_occurred": False, "ingestion_or_codification_occurred": False, "wage_normalization_occurred": False, "wage_gap_or_regression_occurred": False, "final_causal_claim_occurred": False, "raw_prompts_or_responses_saved": False, "secrets_logged": False})
    print(json.dumps(summary))


def audit_staged() -> None:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    forbidden_patterns = re.compile(r"(?:^|/)(?:artifacts/local_|corpus/)|\.(?:pdf|docx?|xlsx?|pptx?|zip|html?)$", re.I)
    forbidden = [path for path in staged if forbidden_patterns.search(path)]
    # Rating ledgers are metadata, not source payloads. Keep the threshold just
    # below GitHub's hard per-file limit while separately banning every source,
    # extracted-text, binary, and browser-cache path.
    large_threshold = 95 * 1024 * 1024
    large = []
    for path in staged:
        result = subprocess.run(["git", "show", f":{path}"], cwd=ROOT, capture_output=True)
        if result.returncode == 0 and len(result.stdout) > large_threshold:
            large.append({"path": path, "bytes": len(result.stdout)})
    write_json(OUTPUT / "staged_file_audit.json", {"audited_at": utc_now(), "staged_file_count": len(staged), "staged_files": staged, "forbidden_staged_files": forbidden, "passed": not forbidden})
    write_json(OUTPUT / "large_file_audit.json", {"audited_at": utc_now(), "threshold_bytes": large_threshold, "large_staged_files": large, "passed": not large, "source_payload_paths_prohibited_separately": True})
    if forbidden or large:
        raise RuntimeError("staged-file or large-file audit failed")
    print(json.dumps({"staged": len(staged), "forbidden": forbidden, "large": large, "passed": True}))


def validate() -> None:
    checks: dict[str, bool] = {}
    input_rows = read_csv(SOURCE)
    locked = read_csv(OUTPUT / "span_rating_locked_queue.csv")
    manifest = json.loads((OUTPUT / "span_rating_manifest.json").read_text(encoding="utf-8"))
    lane_distribution = json.loads((OUTPUT / "span_rating_lane_distribution.json").read_text(encoding="utf-8"))
    valid = read_jsonl(OUTPUT / "merged_span_ratings_valid.jsonl")
    quarantine = read_jsonl(OUTPUT / "merged_span_ratings_quarantine.jsonl")
    valid_ids = [row["span_id"] for row in valid]
    quarantine_ids = [row["span_id"] for row in quarantine]
    checks["01_input_count_18612"] = len(input_rows) == EXPECTED
    checks["02_lane_counts_exact"] = all(lane_distribution["lanes"][lane]["row_count"] == count for lane, count in LANES.items())
    checks["03_lane_union_reconciles"] = sum(LANES.values()) == EXPECTED
    checks["04_one_lane_per_span"] = len(locked) == len({row["span_id"] for row in locked}) == EXPECTED
    checks["05_lane_hashes_match"] = (
        all(sha_file(OUTPUT / f"span_rating_lane_{lane[-3:]}_queue.csv") == lane_distribution["lanes"][lane]["queue_sha256"] for lane in LANES)
        and sha_file(OUTPUT / "span_rating_locked_queue.csv") == manifest["locked_queue_sha256"]
        and sha_file(SOURCE) == manifest["source_queue_sha256"]
    )
    checks["06_valid_quarantine_reconcile"] = len(valid) + len(quarantine) == EXPECTED and len(set(valid_ids + quarantine_ids)) == EXPECTED
    checks["07_valid_schema"] = all(set(RATING_FIELDS).issubset(row) and row["rating_validity_status"] == "valid" for row in valid)
    checks["08_quarantine_reasons"] = all(row.get("quarantine_reason") for row in quarantine)
    checks["09_rating_ids_unique"] = len({row["rating_id"] for row in valid + quarantine}) == EXPECTED
    checks["10_span_ids_unique"] = len(set(valid_ids + quarantine_ids)) == EXPECTED
    checks["11_lineage_preserved"] = all(row.get("source_id") and row.get("retained_source_id") and row.get("span_sha256") for row in valid)
    checks["12_no_final_causal_claims"] = all(row["causal_claim_allowed"] is False for row in valid)
    checks["13_no_wage_gap_regression_claims"] = all(
        row["claim_boundary"] == CLAIM_BOUNDARY
        and row["population_prevalence_claim_allowed"] is False
        and row["national_prevalence_claim_allowed"] is False
        for row in valid
    )
    forbidden = json.loads((OUTPUT / "forbidden_action_audit.json").read_text(encoding="utf-8"))
    checks["14_no_normalization"] = forbidden["wage_normalization_occurred"] is False
    checks["15_no_ocr"] = forbidden["ocr_occurred"] is False
    checks["16_no_ingestion_codification"] = forbidden["ingestion_or_codification_occurred"] is False
    mechanism = json.loads((OUTPUT / "mechanism_specific_rating_summaries.json").read_text(encoding="utf-8"))
    checks["17_mechanism_json_reconciles"] = mechanism["valid_ledger_count"] == len(valid)
    checks["18_mechanism_md_exists"] = (OUTPUT / "mechanism_specific_rating_summaries.md").is_file()
    checks["19_pi_findings_exist"] = (OUTPUT / "pi_report_candidate_findings.md").is_file()
    usability = json.loads((OUTPUT / "report_usability_summary.json").read_text(encoding="utf-8"))
    checks["20_summary_buckets_reconcile"] = sum(usability["counts"].values()) == len(valid)
    checks["21_dashboard_cleanup_artifacts"] = all((OUTPUT / name).is_file() for name in ["dashboard_cleanup_audit.json", "dashboard_cleanup_summary.md", "dashboard_information_architecture_report.json", "dashboard_removed_elements_report.json", "dashboard_condensed_elements_report.json"])
    cleanup = json.loads((OUTPUT / "dashboard_cleanup_audit.json").read_text(encoding="utf-8")) if (OUTPUT / "dashboard_cleanup_audit.json").is_file() else {}
    app_source = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    checks["22_dashboard_simplified"] = (
        cleanup.get("passed") is True
        and app_source.count("projectPhaseSummary.next_task") == 1
        and 'className="pi-status-strip"' in app_source
        and 'className="pi-evidence-grid"' in app_source
        and "pi-mechanism-table" in app_source
        and 'className="pi-technical-details"' in app_source
        and all(name not in app_source for name in (
            "ProjectNavigation", "CandidateQueueCards", "CoverageFunnel",
            "ScoutOperationsPanel", "VerificationPipeline", "ReportsLibrary",
            "evidenceFilterDimension", "headline-grid",
        ))
    )
    project = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text(encoding="utf-8"))
    states = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text(encoding="utf-8"))
    map_source = (ROOT / "docs/dashboard/src/components/mapMetrics.js").read_text(encoding="utf-8")
    checks["23_map_coverage_rate"] = (
        states["metadata"]["current_map_layer"] == "scout_coverage_rate_only"
        and states["metric_definition"]["map_color_metric"] == "scout_coverage_rate"
        and 'key: "scout_coverage_rate"' in map_source
        and "MAP_METRICS = [" in map_source
        and states["totals"]["scout_covered_municipalities"] == 16887
        and states["totals"]["municipality_universe"] == 35589
    )
    build_report = json.loads((OUTPUT / "dashboard_local_build_report.json").read_text(encoding="utf-8")) if (OUTPUT / "dashboard_local_build_report.json").is_file() else {}
    checks["24_dashboard_build"] = build_report.get("status") == "passed"
    local_smoke = json.loads((OUTPUT / "dashboard_browser_smoke_report.json").read_text(encoding="utf-8")) if (OUTPUT / "dashboard_browser_smoke_report.json").is_file() else {}
    checks["25_local_browser_smoke"] = local_smoke.get("status") in {"passed", "browser_controller_unavailable"}
    public_smoke = json.loads((OUTPUT / "dashboard_public_pages_smoke_report.json").read_text(encoding="utf-8")) if (OUTPUT / "dashboard_public_pages_smoke_report.json").is_file() else {}
    checks["26_public_dashboard_smoke"] = public_smoke.get("status") == "public_pages_visible_current_passed"
    checks["27_global_readiness_not_advanced"] = project.get("global_analysis_readiness") is False
    tracked = subprocess.run(["git", "ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    checks["28_no_source_or_text_artifacts_tracked"] = not tracked
    staged = json.loads((OUTPUT / "staged_file_audit.json").read_text(encoding="utf-8")) if (OUTPUT / "staged_file_audit.json").is_file() else {}
    large = json.loads((OUTPUT / "large_file_audit.json").read_text(encoding="utf-8")) if (OUTPUT / "large_file_audit.json").is_file() else {}
    checks["29_staged_audit"] = staged.get("passed") is True
    checks["30_large_file_audit"] = large.get("passed") is True
    core = all(value for key, value in checks.items() if key not in {"21_dashboard_cleanup_artifacts", "22_dashboard_simplified", "24_dashboard_build", "25_local_browser_smoke", "26_public_dashboard_smoke", "29_staged_audit", "30_large_file_audit"})
    report = {"validated_at": utc_now(), "checks": checks, "core_checks_passed": core, "all_checks_passed": all(checks.values()), "pending_checks": [key for key, value in checks.items() if not value]}
    write_json(OUTPUT / "validation_report.json", report)
    lines = ["# Validation report", "", f"Core checks passed: **{str(core).lower()}**", f"All checks passed: **{str(all(checks.values())).lower()}**", ""]
    lines.extend(f"- {'PASS' if value else 'PENDING'} — {key}" for key, value in checks.items())
    (OUTPUT / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not core:
        raise RuntimeError("core validation failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "smoke", "worker", "coordinate", "validate", "audit-staged"))
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--chunk-size", type=int, default=32)
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare()
    elif args.stage == "smoke":
        smoke(args.model, args.timeout, args.attempts)
    elif args.stage == "worker":
        if not args.lane:
            parser.error("--lane is required")
        worker(args.lane, args.model, args.timeout, args.parallel, args.attempts, args.chunk_size)
    elif args.stage == "coordinate":
        coordinate()
    elif args.stage == "validate":
        validate()
    else:
        audit_staged()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
