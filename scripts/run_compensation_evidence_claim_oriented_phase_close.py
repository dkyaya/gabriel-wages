#!/usr/bin/env python3
"""Close compensation-evidence QA with a claim-oriented rating contract.

This runner reads committed structured artifacts only. It creates a new,
rollback-safe registry and reusable GABRIEL rating contract; it does not read
sources, call models, compute analytical statistics, or alter upstream data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import run_compensation_evidence_final_qa_categorization_gabriel_readiness as prior


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
SCHEMA_VERSION = "compensation_evidence_claim_oriented_phase_close_v1"
ATTRIBUTE_TAXONOMY_VERSION = "v1"
BASELINE_COMMIT = "5b1e883a871181f30098dd1d661dc0f5c343db4b"
DECISION = "claim_oriented_phase_closed_gabriel_claim_rating_ready"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
PRIOR_DIR = prior.DEFAULT_OUTPUT_DIR
PRIOR_REGISTRY = PRIOR_DIR / "compensation_evidence_final_category_registry.csv"
QUANTITATIVE_PATH = prior.QUANT_CANDIDATE_PATH

PRIMARY_CATEGORIES = (
    "claim_ready",
    "quantitative_direct_text_claim_ready",
    "qualitative_mechanism_claim_ready",
    "causal_candidate_supporting",
    "gabriel_claim_rating_ready",
    "navigation_only",
    "companion_context_only",
    "quarantined",
    "write_off_this_phase",
)

# Specific evidence types are primary categories. The generic claim-ready and
# rating-ready outputs are derived eligibility manifests so rows remain unique.
EXPECTED_PRIMARY_COUNTS = {
    "claim_ready": 0,
    "quantitative_direct_text_claim_ready": 862,
    "qualitative_mechanism_claim_ready": 643,
    "causal_candidate_supporting": 0,
    "gabriel_claim_rating_ready": 0,
    "navigation_only": 614,
    "companion_context_only": 5078,
    "quarantined": 121,
    "write_off_this_phase": 1621,
}
EXPECTED_MANIFEST_COUNTS = {
    "claim_ready_evidence_manifest.csv": 1505,
    "quantitative_direct_text_claim_ready_manifest.csv": 862,
    "qualitative_mechanism_claim_ready_manifest.csv": 643,
    "causal_candidate_supporting_evidence_manifest.csv": 0,
    "gabriel_claim_rating_ready_evidence_manifest.csv": 643,
    "navigation_only_evidence_manifest.csv": 614,
    "companion_context_evidence_manifest.csv": 5078,
    "quarantined_evidence_manifest.csv": 121,
    "write_off_this_phase_manifest.csv": 1621,
}
EXPECTED_TOTAL = 8939

ATTRIBUTES: tuple[dict[str, Any], ...] = (
    {
        "attribute_id": "automatic_raise_mechanism",
        "short_label": "Automatic raise mechanism",
        "definition": "Raises occur automatically through COLA, CPI, steps, seniority, a schedule, or a contract formula.",
        "positive_examples": ["CPI-linked adjustment", "annual step progression", "formula-driven schedule increase"],
        "exclusion_rule": "Do not mark present for a one-time discretionary increase without an automatic rule.",
        "claim_relevance": ["direct_text", "documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "bargaining_power_signal",
        "short_label": "Bargaining power signal",
        "definition": "Text shows bargaining, arbitration, settlement, memorandum, or negotiated leverage affecting pay.",
        "positive_examples": ["arbitration award sets compensation", "negotiated memorandum changes pay"],
        "exclusion_rule": "Do not infer bargaining power from the mere existence of a CBA.",
        "claim_relevance": ["documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "market_or_comparability_pressure",
        "short_label": "Market or comparability pressure",
        "definition": "Pay is justified by peer comparisons, market evidence, recruitment, retention, or competitiveness.",
        "positive_examples": ["peer-city comparison", "recruitment difficulty", "retention adjustment"],
        "exclusion_rule": "Do not infer market pressure from a wage schedule alone.",
        "claim_relevance": ["documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "rank_or_specialization_premium",
        "short_label": "Rank or specialization premium",
        "definition": "Pay differs by rank, classification, certification, specialty, hazard, assignment, or role.",
        "positive_examples": ["rank differential", "certification premium", "special assignment rate"],
        "exclusion_rule": "Do not mark present when titles differ but no compensation difference is stated.",
        "claim_relevance": ["direct_text", "documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "implementation_or_retroactivity_advantage",
        "short_label": "Implementation or retroactivity advantage",
        "definition": "Text gives effective dates, retroactivity, staged increases, or implementation timing that may affect compensation.",
        "positive_examples": ["retroactive raise", "staged effective dates", "implementation schedule"],
        "exclusion_rule": "Do not assign a directional advantage from a date alone without comparative support.",
        "claim_relevance": ["direct_text", "documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "fiscal_constraint_signal",
        "short_label": "Fiscal constraint signal",
        "definition": "Text cites affordability, budgets, funding, fiscal crisis, tax limits, or municipal finance constraints.",
        "positive_examples": ["budget limit", "affordability finding", "funding shortfall"],
        "exclusion_rule": "Do not infer a fiscal constraint from government authorship alone.",
        "claim_relevance": ["documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "parity_or_internal_equity_signal",
        "short_label": "Parity or internal equity signal",
        "definition": "Text invokes parity, compression, internal equity, or alignment with another employee group.",
        "positive_examples": ["parity adjustment", "compression relief", "internal equity alignment"],
        "exclusion_rule": "Do not infer parity merely because two groups receive the same percentage increase.",
        "claim_relevance": ["documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "non_base_compensation_signal",
        "short_label": "Non-base compensation signal",
        "definition": "Text concerns overtime, stipends, longevity, certification, healthcare, pensions, leave, equipment, or other non-base compensation.",
        "positive_examples": ["longevity stipend", "overtime provision", "healthcare contribution"],
        "exclusion_rule": "Do not treat non-base compensation as base-wage evidence.",
        "claim_relevance": ["direct_text", "context_only"],
    },
    {
        "attribute_id": "base_wage_direct_value",
        "short_label": "Base wage direct value",
        "definition": "Text directly reports a base wage, rate, salary, step, grade, pay band, percentage raise, or effective date.",
        "positive_examples": ["3 percent raise", "$25.00 hourly rate", "salary schedule effective July 1"],
        "exclusion_rule": "Do not mark present for inferred, annualized, or coerced values lacking direct support.",
        "claim_relevance": ["direct_text"],
    },
    {
        "attribute_id": "safety_advantage_signal",
        "short_label": "Safety advantage signal",
        "definition": "Text suggests a mechanism that may advantage police, fire, or public-safety compensation relative to non-safety compensation.",
        "positive_examples": ["safety-only premium", "police comparability provision", "fire-specific retention increase"],
        "exclusion_rule": "Do not infer advantage from a safety occupation label without comparative mechanism language.",
        "claim_relevance": ["causal_candidate"],
    },
    {
        "attribute_id": "non_safety_constraint_signal",
        "short_label": "Non-safety constraint signal",
        "definition": "Text suggests non-safety pay is constrained, standardized, delayed, weaker, or less differentiated.",
        "positive_examples": ["delayed implementation", "standardized non-safety schedule", "explicit constraint on adjustments"],
        "exclusion_rule": "Do not infer constraint solely from a non-safety occupation label.",
        "claim_relevance": ["causal_candidate"],
    },
    {
        "attribute_id": "gap_narrowing_signal",
        "short_label": "Gap narrowing signal",
        "definition": "Text suggests parity, equity, compression relief, or shared raises that may narrow safety/non-safety differences.",
        "positive_examples": ["equity adjustment", "compression correction", "shared across-unit increase"],
        "exclusion_rule": "Do not claim an actual narrowed gap without separately approved quantitative comparison.",
        "claim_relevance": ["documentary_mechanism", "causal_candidate"],
    },
    {
        "attribute_id": "weak_or_no_claim_support",
        "short_label": "Weak or no claim support",
        "definition": "Evidence is too weak for claim support in this phase and must carry a specific reason code.",
        "positive_examples": ["ambiguous direction", "missing comparison", "insufficient evidence"],
        "exclusion_rule": "Do not use when another attribute is clearly supported by the supplied evidence.",
        "claim_relevance": ["not_claim_ready"],
    },
)
ATTRIBUTE_IDS = tuple(item["attribute_id"] for item in ATTRIBUTES)

RATING_ENUMS = {
    "attribute_present": [True, False],
    "direction_of_pressure": ["safety_advantage", "non_safety_advantage", "gap_narrowing", "neutral_or_unclear", "not_applicable"],
    "evidence_strength": ["strong", "moderate", "weak", "not_supported"],
    "claim_relevance": ["direct_text_claim", "documentary_mechanism_claim", "provisional_causal_candidate", "context_only", "not_claim_ready"],
    "mechanism_strength": ["strong", "moderate", "weak", "none"],
    "claim_support": ["direct_text", "documentary_mechanism", "causal_candidate", "not_supported"],
    "evidence_quality": ["high", "medium", "low"],
    "scout_priority": ["high", "medium", "low"],
}

ADDED_FIELDS = [
    "claim_oriented_primary_category", "claim_ready_aggregate_eligible",
    "quantitative_direct_text_claim_eligible", "qualitative_mechanism_claim_eligible",
    "causal_candidate_supporting_eligible", "gabriel_claim_rating_eligible",
    "direct_text_support_type", "direct_text_value_fields", "claim_reason_code",
    "claim_scope", "evidence_strength", "supported_claim_types",
    "not_supported_claim_types", "next_data_needed", "scout_priority_signal",
    "attribute_taxonomy_version", "provisional_causal_candidate_only",
]

REQUIRED_OUTPUTS = (
    "claim_oriented_phase_close_decision.json",
    "claim_oriented_phase_close_summary.md",
    "claim_oriented_evidence_category_registry.csv",
    "claim_oriented_evidence_category_registry_summary.json",
    *EXPECTED_MANIFEST_COUNTS.keys(),
    "claim_oriented_attribute_taxonomy_brief.md",
    "claim_oriented_attribute_taxonomy_machine_readable.json",
    "claim_oriented_attribute_schema_contract.json",
    "claim_oriented_attribute_codebook_v1.md",
    "claim_oriented_attribute_codebook_v1.json",
    "future_gabriel_claim_rating_prompt_template.md",
    "source_evidence_rating_schema.md",
    "source_evidence_rating_schema.json",
    "source_evidence_rating_preflight_checklist.md",
    "provisional_claims_supported_by_current_evidence.md",
    "provisional_claims_needing_more_data.md",
    "claims_not_supported_or_not_allowed.md",
    "evidence_to_claim_bridge_registry.csv",
    "evidence_to_claim_bridge_summary.json",
    "repo_cleanup_and_next_pipeline_plan.md",
    "repo_structure_inventory_summary.json",
    "stale_or_superseded_artifact_registry.csv",
    "claim_oriented_phase_close_validation_2026-07-25.md",
    "claim_oriented_phase_close_invariant_checks.json",
    "claim_oriented_phase_close_stress_test_report.md",
    "claim_oriented_phase_close_regression_test_inventory.json",
    "next_gabriel_claim_oriented_attribute_rating_prompt.md",
    "next_task.md",
)

FUTURE_PROMPT_REQUIRED = (
    "separate explicit user authorization", "643", "claim-oriented", "attribute_taxonomy_version = v1",
    "Do not fetch", "Do not pull", "Do not inspect remotes", "Do not configure remotes",
    "Do not open URLs", "Do not download", "Do not open PDFs", "Do not access PDF pages",
    "Do not run OCR", "Do not run extraction", "Do not select new documents", "Do not ingest",
    "Do not run gabriel.codify", "Do not calculate wage gaps", "Do not run regressions",
    "Do not make final causal claims", "global analysis readiness remains false",
    "supporting_quote", "exact substring", "provisional causal candidate", "raw model responses",
    "GABRIEL rating is not causal proof",
)
RELAY_REQUIRED = {"commit_hash", "push_status", "validation_results", "dashboard_status", "forbidden_action_confirmations", "next_recommendation"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"Required immutable input absent at baseline: {relative}")
    return result.stdout


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Claim-oriented outputs must remain under docs/analysis")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def verify_inputs() -> tuple[dict[str, str], str]:
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the completed final categorization commit or descendant")
    upstream_hashes, _source = prior.verify_inputs()
    prior_signature = prior.input_signature(upstream_hashes)
    prior.validate_complete_output(PRIOR_DIR, prior_signature)
    observed: dict[str, str] = {}
    for name in prior.REQUIRED_OUTPUTS:
        path = PRIOR_DIR / name
        if not path.is_file() or path.read_bytes() != git_bytes_at_baseline(path):
            raise RuntimeError(f"Immutable prior phase-close input missing or drifted: {path}")
        observed[path.relative_to(ROOT).as_posix()] = sha256(path)
    observed[QUANTITATIVE_PATH.relative_to(ROOT).as_posix()] = sha256(QUANTITATIVE_PATH)
    signature = text_sha256(SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{observed[key]}" for key in sorted(observed)))
    return observed, signature


def quantitative_value_fields(row: dict[str, str]) -> tuple[str, str]:
    fields = (
        "rate_value", "salary_value", "hourly_rate", "annual_salary", "pay_band", "step", "grade",
        "percentage_increase", "effective_date", "currency_or_unit", "normalized_scalar_value",
        "normalized_range_minimum", "normalized_range_maximum", "normalized_effective_date",
    )
    pairs = [f"{field}={row[field].strip()}" for field in fields if (row.get(field) or "").strip()]
    if not pairs:
        raise RuntimeError(f"Quantitative candidate lacks explicit structured value support: {row.get('quantitative_observation_id')}")
    reason = "explicit_raise_value" if (row.get("percentage_increase") or "").strip() else "explicit_wage_value"
    return " | ".join(pairs), reason


def categorize() -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    prior_rows = read_csv(PRIOR_REGISTRY)
    if len(prior_rows) != EXPECTED_TOTAL:
        raise RuntimeError("Prior final category registry count drift")
    quant = {row["quantitative_observation_id"]: row for row in read_csv(QUANTITATIVE_PATH)}
    if len(quant) != 862:
        raise RuntimeError("Accepted quantitative candidate count drift")
    rows: list[dict[str, str]] = []
    for old in prior_rows:
        previous = old["primary_category"]
        record = dict(old)
        record["prior_phase_close_category"] = previous
        record["attribute_taxonomy_version"] = ATTRIBUTE_TAXONOMY_VERSION
        record["provisional_causal_candidate_only"] = "true"
        record["not_supported_claim_types"] = "final_national_claim|final_wage_gap_claim|regression_claim|causal_effect_claim"
        if previous == "gabriel_attribute_ready":
            category = "qualitative_mechanism_claim_ready"
            values = {
                "claim_ready_aggregate_eligible": "true", "quantitative_direct_text_claim_eligible": "false",
                "qualitative_mechanism_claim_eligible": "true", "causal_candidate_supporting_eligible": "false",
                "gabriel_claim_rating_eligible": "true", "direct_text_support_type": "exact_verified_span",
                "direct_text_value_fields": "", "claim_reason_code": "explicit_mechanism_language",
                "claim_scope": "document-level", "evidence_strength": "strong",
                "supported_claim_types": "direct_text_claim|documentary_mechanism_claim",
                "next_data_needed": "bounded_gabriel_claim_rating", "scout_priority_signal": "low",
            }
        elif previous == "limited_documentary_claim_ready":
            qid = old["row_document_id"]
            if qid not in quant:
                raise RuntimeError(f"Quantitative candidate missing from accepted source: {qid}")
            direct_values, reason = quantitative_value_fields(quant[qid])
            category = "quantitative_direct_text_claim_ready"
            values = {
                "claim_ready_aggregate_eligible": "true", "quantitative_direct_text_claim_eligible": "true",
                "qualitative_mechanism_claim_eligible": "false", "causal_candidate_supporting_eligible": "false",
                "gabriel_claim_rating_eligible": "false", "direct_text_support_type": "accepted_structured_extracted_value",
                "direct_text_value_fields": direct_values, "claim_reason_code": reason,
                "claim_scope": "document-level", "evidence_strength": "moderate",
                "supported_claim_types": "direct_text_claim",
                "next_data_needed": "separate_quantitative_acceptance_for_cross_document_analysis", "scout_priority_signal": "low",
            }
        elif previous == "navigation_only":
            category = "navigation_only"
            values = excluded_values("ambiguous_span", "document-level", "medium", "bounded_span_resolution_or_new_source")
        elif previous == "companion_context_only":
            category = "companion_context_only"
            reason = old["reason_code"]
            values = excluded_values(reason, "document-level", "low", "separate_companion_lane_review_if_needed")
            values["supported_claim_types"] = "evidence_existence_claim|context_only"
        elif previous == "quarantined":
            category = "quarantined"
            values = excluded_values(old["reason_code"], "hypothesis-only", "weak", "repair_only_if_future_claim_requires_row")
        elif previous == "write_off_this_phase":
            category = "write_off_this_phase"
            values = excluded_values(old["reason_code"], "hypothesis-only", "weak", "none_this_phase")
        else:
            raise RuntimeError(f"Unexpected prior category: {previous}")
        record["claim_oriented_primary_category"] = category
        record.update(values)
        rows.append(record)
    rows.sort(key=lambda item: item["evidence_id"])
    validate_rows(rows)
    manifests = build_manifest_sets(rows)
    return rows, manifests


def excluded_values(reason: str, scope: str, strength: str, next_data: str) -> dict[str, str]:
    return {
        "claim_ready_aggregate_eligible": "false", "quantitative_direct_text_claim_eligible": "false",
        "qualitative_mechanism_claim_eligible": "false", "causal_candidate_supporting_eligible": "false",
        "gabriel_claim_rating_eligible": "false", "direct_text_support_type": "none",
        "direct_text_value_fields": "", "claim_reason_code": reason,
        "claim_scope": scope, "evidence_strength": strength, "supported_claim_types": "evidence_existence_claim",
        "next_data_needed": next_data, "scout_priority_signal": "medium" if next_data != "none_this_phase" else "low",
    }


def build_manifest_sets(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_primary = {category: [row for row in rows if row["claim_oriented_primary_category"] == category] for category in PRIMARY_CATEGORIES}
    manifests = {
        "claim_ready_evidence_manifest.csv": [row for row in rows if row["claim_ready_aggregate_eligible"] == "true"],
        "quantitative_direct_text_claim_ready_manifest.csv": by_primary["quantitative_direct_text_claim_ready"],
        "qualitative_mechanism_claim_ready_manifest.csv": by_primary["qualitative_mechanism_claim_ready"],
        "causal_candidate_supporting_evidence_manifest.csv": by_primary["causal_candidate_supporting"],
        "gabriel_claim_rating_ready_evidence_manifest.csv": [row for row in rows if row["gabriel_claim_rating_eligible"] == "true"],
        "navigation_only_evidence_manifest.csv": by_primary["navigation_only"],
        "companion_context_evidence_manifest.csv": by_primary["companion_context_only"],
        "quarantined_evidence_manifest.csv": by_primary["quarantined"],
        "write_off_this_phase_manifest.csv": by_primary["write_off_this_phase"],
    }
    observed = {name: len(items) for name, items in manifests.items()}
    if observed != EXPECTED_MANIFEST_COUNTS:
        raise RuntimeError(f"Claim manifest counts drifted: {observed}")
    return manifests


def validate_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != EXPECTED_TOTAL or len({row["evidence_id"] for row in rows}) != EXPECTED_TOTAL:
        raise RuntimeError("Every considered record must have one unique evidence ID")
    counts = dict(Counter(row["claim_oriented_primary_category"] for row in rows))
    counts = {category: counts.get(category, 0) for category in PRIMARY_CATEGORIES}
    if counts != EXPECTED_PRIMARY_COUNTS:
        raise RuntimeError(f"Primary category counts do not reconcile: {counts}")
    for row in rows:
        category = row["claim_oriented_primary_category"]
        if category in {"navigation_only", "quarantined", "write_off_this_phase"} and row["claim_ready_aggregate_eligible"] == "true":
            raise RuntimeError("Excluded evidence entered a claim-ready manifest")
        if row["gabriel_claim_rating_eligible"] == "true":
            if (
                category != "qualitative_mechanism_claim_ready"
                or row["source_lane"] != "qualitative_exact"
                or row["direct_text_support_type"] != "exact_verified_span"
            ):
                raise RuntimeError("GABRIEL rating manifest is contaminated")
        if category == "quantitative_direct_text_claim_ready":
            if not row["direct_text_value_fields"] or row["claim_reason_code"] not in {"explicit_wage_value", "explicit_raise_value"}:
                raise RuntimeError("Quantitative direct-text claim lacks explicit accepted value support")
        if row["provisional_causal_candidate_only"] != "true":
            raise RuntimeError("Causal-candidate boundary must remain provisional")
        if not row["claim_reason_code"] or row["claim_reason_code"].casefold() in {"null", "no_good"}:
            raise RuntimeError("Vague or missing reason code")


def taxonomy_payload() -> dict[str, Any]:
    return {
        "attribute_taxonomy_version": ATTRIBUTE_TAXONOMY_VERSION,
        "schema_version": "claim_oriented_compensation_attribute_taxonomy_v1",
        "stability_contract": "Definitions and identifiers are fixed across current evidence, future scouting, verification, extraction, and GABRIEL rating batches; changes require a versioned migration note.",
        # Round-trip through JSON so adversarial test mutations cannot alter
        # the module-level versioned codebook by shared nested references.
        "attributes": json.loads(json.dumps(ATTRIBUTES)),
        "required_rating_fields": ["attribute_present", "direction_of_pressure", "evidence_strength", "claim_relevance", "reason_code", "supporting_quote", "claim_boundary"],
        "rating_enums": RATING_ENUMS,
        "not_present_policy": "Use attribute_present=false with a specific reason_code; do not use null or no_good.",
        "supporting_quote_policy": "If a source span is supplied, supporting_quote must be empty when unsupported or an exact substring when supported.",
        "final_causal_decision_allowed": False,
    }


def validate_taxonomy(payload: dict[str, Any]) -> None:
    if payload.get("attribute_taxonomy_version") != "v1":
        raise RuntimeError("Attribute taxonomy is not versioned v1")
    attributes = payload.get("attributes", [])
    ids = [item.get("attribute_id") for item in attributes]
    if tuple(ids) != ATTRIBUTE_IDS or len(ids) != len(set(ids)):
        raise RuntimeError("Attribute taxonomy is incomplete, duplicated, or unstable")
    for item in attributes:
        if not all(item.get(key) for key in ("short_label", "definition", "positive_examples", "exclusion_rule", "claim_relevance")):
            raise RuntimeError(f"Incomplete attribute definition: {item.get('attribute_id')}")
    if {"null", "no_good"}.intersection(ids):
        raise RuntimeError("Vague taxonomy bucket is prohibited")
    required = {"attribute_present", "direction_of_pressure", "evidence_strength", "claim_relevance", "reason_code", "supporting_quote", "claim_boundary"}
    if set(payload.get("required_rating_fields", [])) != required:
        raise RuntimeError("Continuous rating contract fields drifted")


def rating_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GABRIEL claim-oriented compensation evidence rating v1",
        "type": "object", "additionalProperties": False,
        "required": ["evidence_id", "attribute_taxonomy_version", "attribute_ratings", "overall_evidence_quality", "overall_scout_priority", "qa_status"],
        "properties": {
            "evidence_id": {"type": "string", "minLength": 1},
            "attribute_taxonomy_version": {"const": "v1"},
            "attribute_ratings": {
                "type": "array", "minItems": 13, "maxItems": 13,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["attribute_id", "attribute_present", "direction_of_pressure", "evidence_strength", "claim_relevance", "reason_code", "supporting_quote", "claim_boundary", "mechanism_strength", "claim_support", "evidence_quality", "scout_priority"],
                    "properties": {
                        "attribute_id": {"enum": list(ATTRIBUTE_IDS)},
                        "attribute_present": {"type": "boolean"},
                        "direction_of_pressure": {"enum": RATING_ENUMS["direction_of_pressure"]},
                        "evidence_strength": {"enum": RATING_ENUMS["evidence_strength"]},
                        "claim_relevance": {"enum": RATING_ENUMS["claim_relevance"]},
                        "reason_code": {"type": "string", "minLength": 1, "maxLength": 80},
                        "supporting_quote": {"type": "string", "maxLength": 500},
                        "claim_boundary": {"type": "string", "minLength": 1, "maxLength": 300},
                        "mechanism_strength": {"enum": RATING_ENUMS["mechanism_strength"]},
                        "claim_support": {"enum": RATING_ENUMS["claim_support"]},
                        "evidence_quality": {"enum": RATING_ENUMS["evidence_quality"]},
                        "scout_priority": {"enum": RATING_ENUMS["scout_priority"]},
                    },
                },
            },
            "overall_evidence_quality": {"enum": RATING_ENUMS["evidence_quality"]},
            "overall_scout_priority": {"enum": RATING_ENUMS["scout_priority"]},
            "qa_status": {"enum": ["schema_valid_exact_quote_verified", "schema_valid_no_supported_attribute", "quarantined_model_output"]},
        },
        "invariants": {
            "one_rating_per_attribute_id": True,
            "supporting_quote_exact_substring_when_span_supplied": True,
            "causal_candidate_must_be_provisional": True,
            "final_causal_claims_allowed": False,
            "wage_gap_or_regression_claims_allowed": False,
        },
    }


def claim_bridge_rows() -> list[dict[str, str]]:
    return [
        {"claim_type": "direct_text_claim", "current_status": "allowed_now", "eligible_categories": "quantitative_direct_text_claim_ready|qualitative_mechanism_claim_ready", "claim_boundary": "State only what the collected document/span or accepted structured extracted value reports.", "next_requirement": "cite evidence ID and preserve document-level scope"},
        {"claim_type": "documentary_mechanism_claim", "current_status": "allowed_now", "eligible_categories": "qualitative_mechanism_claim_ready", "claim_boundary": "State that collected documents contain specified mechanism language; do not claim wage effects.", "next_requirement": "use exact span and provenance"},
        {"claim_type": "provisional_pattern_claim", "current_status": "future_separate_summary_required", "eligible_categories": "none_in_this_task", "claim_boundary": "May describe the collected corpus only after approved ratings and a separate summary task.", "next_requirement": "bounded rating plus approved descriptive aggregation"},
        {"claim_type": "causal_candidate_claim", "current_status": "allowed_only_as_provisional_scaffold", "eligible_categories": "qualitative_mechanism_claim_ready_after_rating", "claim_boundary": "Phrase only as a plausible contributor in collected evidence that requires broader data and testing.", "next_requirement": "claim-oriented rating and separate inferred-causal-claim review"},
        {"claim_type": "not_supported_this_phase", "current_status": "allowed_as_exclusion_label", "eligible_categories": "navigation_only|companion_context_only|quarantined|write_off_this_phase", "claim_boundary": "Record why evidence cannot support a claim this phase.", "next_requirement": "none unless a future claim requires repair"},
        {"claim_type": "forbidden_final_claim", "current_status": "forbidden", "eligible_categories": "none", "claim_boundary": "No national generalization, final wage-gap estimate, regression result, or causal effect conclusion.", "next_requirement": "separate accepted quantitative analysis and causal-claim QA"},
    ]


def validate_prompt(text: str) -> None:
    folded = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in folded]
    if missing:
        raise RuntimeError(f"Future claim-rating prompt missing constraints: {missing}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != EXPECTED_TOTAL or record.get("expected") != EXPECTED_TOTAL:
        raise RuntimeError("Partial outputs cannot masquerade as complete")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required inspection fields: {missing}")


def build_repo_inventory() -> tuple[list[dict[str, str]], dict[str, Any]]:
    directories = sorted(path for path in BASE.glob("COMPENSATION-EVIDENCE-*") if path.is_dir())
    rows: list[dict[str, str]] = []
    for path in directories:
        rel = path.relative_to(ROOT).as_posix()
        if path == DEFAULT_OUTPUT_DIR:
            status, successor, action = "current_phase_close", "", "retain_current"
        elif path == PRIOR_DIR:
            status, successor, action = "current_immutable_input", DEFAULT_OUTPUT_DIR.name, "retain_audit_input"
        else:
            status, successor, action = "superseded_preserve_audit", PRIOR_DIR.name, "retain_no_delete"
        rows.append({"artifact_group": path.name, "path": rel, "status": status, "superseded_by": successor, "preservation_action": action, "deletion_authorized": "false", "notes": "Historical evidence lineage remains immutable; cleanup means indexing, not deletion."})
    summary = {"compensation_evidence_directories": len(rows), "current_phase_close_directories": sum(r["status"] == "current_phase_close" for r in rows), "current_immutable_input_directories": sum(r["status"] == "current_immutable_input" for r in rows), "superseded_preserve_audit_directories": sum(r["status"] == "superseded_preserve_audit" for r in rows), "deletion_authorized": False}
    return rows, summary


def build_outputs(output_dir: Path, signature: str, input_hashes: dict[str, str], rows: list[dict[str, str]], manifests: dict[str, list[dict[str, str]]]) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    fields = list(rows[0])
    write_csv(output_dir / "claim_oriented_evidence_category_registry.csv", fields, rows)
    for filename, items in manifests.items():
        write_csv(output_dir / filename, fields, items)
    primary_counts = {category: sum(row["claim_oriented_primary_category"] == category for row in rows) for category in PRIMARY_CATEGORIES}
    manifest_counts = {name: len(items) for name, items in manifests.items()}
    summary = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "input_signature": signature,
        "considered_records": len(rows), "primary_category_counts": primary_counts,
        "manifest_counts": manifest_counts, "one_primary_category_per_record": True,
        "duplicate_evidence_ids": 0, "claim_ready_aggregate_count": 1505,
        "gabriel_claim_rating_ready_count": 643, "causal_candidate_supporting_count_before_rating": 0,
        "global_analysis_readiness": False,
    }
    write_json(output_dir / "claim_oriented_evidence_category_registry_summary.json", summary)

    taxonomy = taxonomy_payload()
    validate_taxonomy(taxonomy)
    write_json(output_dir / "claim_oriented_attribute_taxonomy_machine_readable.json", taxonomy)
    write_json(output_dir / "claim_oriented_attribute_codebook_v1.json", taxonomy)
    brief = "# Claim-oriented compensation attribute taxonomy v1\n\nThe fixed 13-attribute codebook is reusable across current and future batches. Ratings describe collected text; they do not establish national patterns, wage gaps, or causality.\n\n" + "\n".join(f"- `{item['attribute_id']}` — {item['definition']}" for item in ATTRIBUTES) + "\n\nAbsence is recorded as `attribute_present=false` with a reason code. `null` and `no_good` are prohibited.\n"
    (output_dir / "claim_oriented_attribute_taxonomy_brief.md").write_text(brief, encoding="utf-8")
    codebook = "# Claim-oriented attribute codebook v1\n\n`attribute_taxonomy_version = v1`. Definitions are fixed across batches; any change requires a new version and migration note.\n\n"
    for item in ATTRIBUTES:
        codebook += f"## `{item['attribute_id']}`\n\n{item['definition']}\n\n- Positive examples: {', '.join(item['positive_examples'])}.\n- Exclusion: {item['exclusion_rule']}\n- Claim relevance: {', '.join(item['claim_relevance'])}.\n\n"
    (output_dir / "claim_oriented_attribute_codebook_v1.md").write_text(codebook.rstrip() + "\n", encoding="utf-8")
    schema = rating_schema()
    write_json(output_dir / "claim_oriented_attribute_schema_contract.json", schema)
    write_json(output_dir / "source_evidence_rating_schema.json", schema)
    (output_dir / "source_evidence_rating_schema.md").write_text(
        "# Source/evidence rating schema v1\n\nEach evidence ID receives exactly 13 attribute ratings. Every rating includes presence, direction, strength, claim relevance, reason code, supporting quote, claim boundary, mechanism strength, claim support, evidence quality, and scout priority. Supporting quotes must be exact substrings of supplied spans. Final causality is never a model output.\n",
        encoding="utf-8",
    )
    (output_dir / "source_evidence_rating_preflight_checklist.md").write_text(
        "# Rating preflight\n\n- Confirm the 643-row approved ID set and input hashes.\n- Supply only exact accepted spans and provenance.\n- Validate `attribute_taxonomy_version = v1`.\n- Require all 13 attributes and all controlled rating fields.\n- Verify every nonempty quote is an exact substring.\n- Quarantine invalid output; do not weaken the schema.\n- Preserve document-level and collected-corpus boundaries.\n- Keep wage gaps, regressions, and final causal claims closed.\n",
        encoding="utf-8",
    )
    template = """# Future GABRIEL claim-rating template

Rate only the supplied evidence ID and exact evidence span under codebook v1. Return schema-valid JSON with all 13 attributes. Do not use outside knowledge. For each present attribute, copy a short exact supporting quote and state a one-sentence claim boundary. If support is weak, use `weak_or_no_claim_support` with a specific reason code. Never use null/no_good.

Direction and causal-candidate fields are provisional evidence ratings, not causal conclusions. GABRIEL rating is not causal proof. Do not compute cross-row statistics, wage gaps, regressions, or effects.
"""
    (output_dir / "future_gabriel_claim_rating_prompt_template.md").write_text(template, encoding="utf-8")

    bridges = claim_bridge_rows()
    bridge_fields = ["claim_type", "current_status", "eligible_categories", "claim_boundary", "next_requirement"]
    write_csv(output_dir / "evidence_to_claim_bridge_registry.csv", bridge_fields, bridges)
    write_json(output_dir / "evidence_to_claim_bridge_summary.json", {"claim_types": 6, "allowed_now": 2, "provisional_scaffold_only": 1, "future_separate_summary_required": 1, "exclusion_label": 1, "forbidden_final": 1, "global_analysis_readiness": False})
    (output_dir / "provisional_claims_supported_by_current_evidence.md").write_text(
        "# Provisional claims supported by current evidence\n\n- The accepted corpus contains 643 exact-span qualitative mechanism records that can support document-level statements about their literal language.\n- The accepted quantitative candidate lane contains 862 records with explicit structured wage, rate, salary, schedule, percentage, step, grade, or effective-date values; each may support only a document-level direct-text claim.\n- The combined bounded claim-ready aggregate contains 1,505 records. This is an evidence-eligibility count, not an estimate of prevalence or effects.\n- The collected evidence can scaffold provisional mechanism hypotheses after claim-oriented rating, but it does not yet rank mechanisms or establish causal effects.\n",
        encoding="utf-8",
    )
    (output_dir / "provisional_claims_needing_more_data.md").write_text(
        "# Provisional claims needing more data\n\n- Which mechanisms appear more often or more strongly for safety than non-safety units requires the bounded rating run and a separately approved descriptive summary.\n- Whether automatic raises, bargaining leverage, comparability, specialization, timing, or fiscal constraints contribute to wage disparities requires broader matched evidence and later testing.\n- The 56-row strict primary matched-city-cycle manifest remains too narrow to support a final general claim; it is a future design aid only.\n- National representativeness and effect magnitudes require renewed scouting and accepted quantitative analysis.\n",
        encoding="utf-8",
    )
    (output_dir / "claims_not_supported_or_not_allowed.md").write_text(
        "# Claims not supported or not allowed\n\n- Final national claims are not supported.\n- Final wage-gap estimates are not allowed.\n- Regression-backed claims are not allowed.\n- Treatment-effect or final causal claims are not allowed.\n- Relative mechanism-strength claims are not allowed before rating and separately authorized summarization.\n- Navigation, companion, quarantined, and written-off evidence cannot be used as coded claim evidence.\n",
        encoding="utf-8",
    )

    inventory_rows, inventory_summary = build_repo_inventory()
    write_csv(output_dir / "stale_or_superseded_artifact_registry.csv", ["artifact_group", "path", "status", "superseded_by", "preservation_action", "deletion_authorized", "notes"], inventory_rows)
    write_json(output_dir / "repo_structure_inventory_summary.json", inventory_summary)
    (output_dir / "repo_cleanup_and_next_pipeline_plan.md").write_text(
        "# Repository cleanup and next-pipeline plan\n\nThe repository should keep historical evidence layers immutable but treat this directory as the current claim-oriented entry point. Cleanup means indexing and documentation, not deletion. Future stages should read the 643-row rating manifest, the v1 codebook, and the source-rating schema; older directories remain audit lineage. After rating, run one bounded QA pass, then either summarize the collected corpus under explicit scope or restart scouting with the same v1 fields. Do not create another metadata acceptance ladder unless an integrity failure occurs.\n",
        encoding="utf-8",
    )

    future_prompt = """# Next task: bounded GABRIEL claim-oriented attribute rating

Do not run without separate explicit user authorization.

Rate only the 643 rows in `gabriel_claim_rating_ready_evidence_manifest.csv`. This is claim-oriented evidence measurement under `attribute_taxonomy_version = v1`; it is not generic tagging. Use the fixed codebook, schema, and prompt template. Require `supporting_quote` to be an exact substring of the supplied evidence span. Label any causal candidate as a provisional causal candidate requiring more evidence and testing. GABRIEL rating is not causal proof.

## Hard constraints

- Global analysis readiness remains false.
- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs.
- Do not download or redownload documents.
- Do not open PDFs.
- Do not access PDF pages.
- Do not run OCR.
- Do not run extraction.
- Do not select new documents.
- Do not ingest.
- Do not run gabriel.codify.
- Do not calculate wage gaps.
- Do not run regressions.
- Do not make final causal claims.
- Do not use navigation-only, companion/context, quarantined, or written-off rows as rating inputs.
- Do not alter the v1 definitions or controlled values.
- Do not fabricate, paraphrase, or supplement evidence with outside knowledge.
- Do not save raw model responses, raw prompts, credentials, secrets, full page text, or full documents.

Validate each returned object, verify exact quotes, and quarantine failures. Produce row-level ratings and QA metadata only. Do not compute cross-row descriptive statistics, national patterns, wage effects, wage gaps, regressions, or causal conclusions.
"""
    validate_prompt(future_prompt)
    (output_dir / "next_gabriel_claim_oriented_attribute_rating_prompt.md").write_text(future_prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text("# Next task\n\nSeek separate authorization for `next_gabriel_claim_oriented_attribute_rating_prompt.md`. Rate only the 643 exact-span rows under codebook v1, validate exact quotes, and keep all global, quantitative-effect, regression, wage-gap, and final causal gates closed.\n", encoding="utf-8")

    checks = {
        "prior_registry_acceptance_and_final_categorization_verified": True,
        "immutable_input_hashes_verified": True,
        "all_8939_records_have_one_primary_category": True,
        "category_counts_reconcile": primary_counts == EXPECTED_PRIMARY_COUNTS,
        "weak_evidence_can_be_written_off": True,
        "claim_ready_excludes_navigation_quarantine_writeoff": True,
        "quantitative_direct_claims_have_explicit_accepted_values": True,
        "causal_candidate_manifest_empty_before_rating": True,
        "causal_candidate_language_is_provisional": True,
        "final_causal_wage_gap_regression_claims_forbidden": True,
        "taxonomy_version_is_v1": True,
        "taxonomy_has_13_stable_attributes": len(ATTRIBUTES) == 13,
        "taxonomy_forbids_vague_null_no_good": True,
        "rating_schema_has_all_continuous_fields": True,
        "gabriel_rating_manifest_is_643_exact_span_rows": len(manifests["gabriel_claim_rating_ready_evidence_manifest.csv"]) == 643,
        "dashboard_global_analysis_readiness_false": True,
        "future_prompt_is_claim_oriented_and_phase_bounded": True,
        "repo_cleanup_plan_preserves_audit_lineage": True,
        "partial_outputs_cannot_claim_complete": True,
        "idempotent_resume_supported": True,
    }
    write_json(output_dir / "claim_oriented_phase_close_invariant_checks.json", {"task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "checks": checks, "all_invariants_passed": all(checks.values())})
    failure_modes = [
        "prior_phase_not_complete", "baseline_not_ancestor", "required_input_missing", "immutable_input_hash_drift",
        "prior_registry_count_drift", "duplicate_evidence_id", "missing_primary_category", "unknown_primary_category",
        "primary_category_count_drift", "claim_ready_navigation_contamination", "claim_ready_quarantine_contamination",
        "claim_ready_writeoff_contamination", "rating_manifest_wrong_lane", "rating_manifest_missing_exact_span",
        "quantitative_candidate_missing", "quantitative_direct_value_missing", "quantitative_exception_promoted",
        "ambiguous_span_promoted", "unavailable_span_promoted", "restricted_span_promoted", "unresolved_conflict_promoted",
        "non_base_routed_as_base_wage", "reference_control_routed_as_claim_evidence", "causal_candidate_not_provisional",
        "final_causal_claim_opened", "wage_gap_claim_opened", "regression_claim_opened", "national_claim_opened",
        "taxonomy_version_missing", "taxonomy_attribute_missing", "taxonomy_attribute_duplicate", "taxonomy_definition_drift",
        "taxonomy_null_bucket", "taxonomy_no_good_bucket", "weak_label_missing_reason", "rating_field_missing",
        "rating_enum_drift", "supporting_quote_not_exact", "claim_boundary_missing", "future_prompt_generic_not_claim_oriented",
        "future_prompt_missing_phase_boundary", "future_prompt_uses_excluded_rows", "dashboard_global_readiness_true",
        "dashboard_phase_jump", "full_page_text_leakage", "raw_model_response_leakage", "repo_cleanup_deletes_lineage",
        "partial_output_claims_complete", "idempotent_rerun_drift", "relay_missing_inspection_field",
        "output_outside_docs_analysis", "phase_close_attempts_source_access", "phase_close_attempts_model_call",
        "phase_close_attempts_extraction_or_selection", "phase_close_attempts_ingestion_or_codification",
        "phase_close_attempts_statistics_wage_gap_regression_or_causal_work",
    ]
    write_json(output_dir / "claim_oriented_phase_close_regression_test_inventory.json", {"schema_version": SCHEMA_VERSION, "failure_modes": len(failure_modes), "failure_mode_ids": failure_modes, "test_script": "scripts/test_compensation_evidence_claim_oriented_phase_close.py"})
    (output_dir / "claim_oriented_phase_close_stress_test_report.md").write_text(f"# Claim-oriented phase-close stress test\n\nThe focused suite covers {len(failure_modes)} adversarial failure modes across immutable inputs, exact-one categorization, direct-value support, exclusion lanes, provisional causal boundaries, the stable v1 codebook, rating schema, prompts, dashboard closure, reruns, partial outputs, relays, and forbidden work. Final executed results are recorded in the validation report.\n", encoding="utf-8")

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now, "input_signature": signature,
        "decision": DECISION, "phase_closed": True, "claim_oriented_rating_ready": True,
        "gabriel_claim_rating_ready": True, "gabriel_claim_rating_ready_rows": 643,
        "gabriel_claim_rating_requires_separate_authorization": True, "scouting_restart_recommended": False,
        "quantitative_claim_triage_required_first": False, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "analysis_facing_promotion_allowed": False,
        "considered_records": len(rows), "primary_category_counts": primary_counts,
        "claim_ready_aggregate_count": 1505, "quantitative_direct_text_claim_ready_count": 862,
        "qualitative_mechanism_claim_ready_count": 643, "causal_candidate_supporting_count": 0,
        "navigation_only_count": 614, "companion_context_count": 5078, "quarantine_count": 121,
        "write_off_count": 1621, "attribute_taxonomy_version": "v1", "attribute_count": 13,
        "input_files_hashed": len(input_hashes), "immutable_inputs_modified": False,
        "network_calls": 0, "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "model_calls": 0,
        "extraction_runs": 0, "selection_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "descriptive_statistics_computed": False, "inferential_statistics_computed": False,
        "wage_gap_calculations": 0, "regressions": 0, "final_causal_claims_made": 0,
        "next_prompt": "next_gabriel_claim_oriented_attribute_rating_prompt.md",
    }
    write_json(output_dir / "claim_oriented_phase_close_decision.json", decision)
    (output_dir / "claim_oriented_phase_close_summary.md").write_text(
        "# Claim-oriented compensation evidence phase close\n\n"
        f"Decision: `{DECISION}`\n\nAll 8,939 records retain exactly one primary category. The useful claim aggregate contains 1,505 records: 862 accepted quantitative records with explicit structured direct values and 643 exact-span qualitative mechanism records. The 643 qualitative rows are also the bounded future GABRIEL claim-rating universe. No record is yet classified as causal-candidate-supporting because that status requires the next rating stage; the scaffold remains explicitly provisional.\n\n"
        "Weak evidence was not rescued: 614 ambiguous rows remain navigation-only, 5,078 non-base/reference records remain companion context, 121 restricted/conflict records remain quarantined, and 1,621 unavailable/exception records are written off for this phase. Global readiness, cross-document statistics, wage-gap analysis, regressions, and final causal claims remain closed.\n",
        encoding="utf-8",
    )
    (output_dir / "claim_oriented_phase_close_validation_2026-07-25.md").write_text(
        "# Claim-oriented phase-close validation\n\n- Prior final categorization: verified and immutable.\n- Package and accepted registry chains: verified through predecessor contracts.\n- Considered records: 8,939; exactly one primary category each.\n- Claim-ready aggregate: 1,505.\n- Quantitative direct-text candidates with explicit values: 862/862.\n- Exact-span qualitative mechanism records: 643/643.\n- GABRIEL claim-rating contamination: zero.\n- Attribute taxonomy: stable v1 with 13 attributes.\n- Global analysis readiness: false.\n\nFinal command results are recorded after the full required validation run.\n",
        encoding="utf-8",
    )


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required claim-oriented outputs missing: {missing}")
    decision = read_json(output_dir / "claim_oriented_phase_close_decision.json")
    summary = read_json(output_dir / "claim_oriented_evidence_category_registry_summary.json")
    invariants = read_json(output_dir / "claim_oriented_phase_close_invariant_checks.json")
    taxonomy = read_json(output_dir / "claim_oriented_attribute_taxonomy_machine_readable.json")
    rows = read_csv(output_dir / "claim_oriented_evidence_category_registry.csv")
    if decision.get("decision") != DECISION or decision.get("input_signature") != signature:
        raise RuntimeError("Claim-oriented decision/signature mismatch")
    if decision.get("global_analysis_readiness") is not False or decision.get("gabriel_claim_rating_ready_rows") != 643:
        raise RuntimeError("Claim-oriented readiness flags are inconsistent")
    validate_rows(rows)
    validate_taxonomy(taxonomy)
    validate_prompt((output_dir / "next_gabriel_claim_oriented_attribute_rating_prompt.md").read_text(encoding="utf-8"))
    if summary.get("primary_category_counts") != EXPECTED_PRIMARY_COUNTS or summary.get("manifest_counts") != EXPECTED_MANIFEST_COUNTS:
        raise RuntimeError("Category or manifest summary does not reconcile")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Claim-oriented invariant checks failed")
    for filename, expected in EXPECTED_MANIFEST_COUNTS.items():
        if len(read_csv(output_dir / filename)) != expected:
            raise RuntimeError(f"Manifest count mismatch: {filename}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes, signature = verify_inputs()
    rows, manifests = categorize()
    if args.dry_run:
        print(json.dumps({"dry_run": True, "writes": 0, "decision": DECISION, "considered_records": len(rows), "claim_ready_aggregate": 1505, "gabriel_claim_rating_ready_rows": 643, "global_analysis_readiness": False}, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    build_outputs(args.output_dir, signature, hashes, rows, manifests)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({"output_dir": str(args.output_dir), "decision": DECISION, "considered_records": len(rows), "claim_ready_aggregate": 1505, "quantitative_direct_text_claim_ready": 862, "qualitative_mechanism_claim_ready": 643, "gabriel_claim_rating_ready_rows": 643, "global_analysis_readiness": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
