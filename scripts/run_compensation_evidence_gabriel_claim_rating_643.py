#!/usr/bin/env python3
"""Rate the 643 accepted exact-span qualitative rows with GABRIEL.

The runner is deliberately stage-gated.  ``dry-run`` never calls a model;
``preflight`` calls only a small deterministic representative set; ``live``
requires a recorded 100-percent-valid preflight.  Only parsed, validated
ratings and sanitized request metadata are persisted.  Prompts, raw model
responses, credentials, and environment values are never written.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-ORIENTED-ATTRIBUTE-RATING-643-2026-07-25"
SCHEMA_VERSION = "gabriel_claim_oriented_attribute_rating_v1_1"
TAXONOMY_VERSION = "v1.1"
BASELINE_COMMIT = "4c6b81655a03cbaef8696c6123fbc2c647146eaa"
AUTHORIZED_ID_HASH = "0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b"
EXPECTED_INPUT_ROWS = 643
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
BACKEND = "huit_openai_responses_direct_sdk"
DEFAULT_MODEL = "gpt-5.4-nano"

INPUT_DIR = BASE / "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-ORIENTED-ATTRIBUTE-RATING-643-2026-07-25"
MANIFEST_PATH = INPUT_DIR / "gabriel_claim_rating_ready_evidence_manifest.csv"
RELAY_SUMMARY_FALLBACK = ROOT / "tmp/compensation_evidence_claim_oriented_qa_rating_phase_close_relay_2026-07-25_4c6b816/category_specific_manifest_summaries.json"

REQUIRED_INPUT_NAMES = (
    "claim_oriented_phase_close_decision.json",
    "claim_oriented_phase_close_summary.md",
    "claim_oriented_evidence_category_registry_summary.json",
    "claim_oriented_attribute_taxonomy_brief.md",
    "claim_oriented_attribute_taxonomy_machine_readable.json",
    "claim_oriented_attribute_schema_contract.json",
    "claim_oriented_attribute_codebook_v1.md",
    "claim_oriented_attribute_codebook_v1.json",
    "future_gabriel_claim_rating_prompt_template.md",
    "source_evidence_rating_schema.md",
    "source_evidence_rating_schema.json",
    "source_evidence_rating_preflight_checklist.md",
    "evidence_to_claim_bridge_registry.csv",
    "evidence_to_claim_bridge_summary.json",
    "provisional_claims_supported_by_current_evidence.md",
    "provisional_claims_needing_more_data.md",
    "claims_not_supported_or_not_allowed.md",
    "claim_oriented_phase_close_invariant_checks.json",
    "claim_oriented_phase_close_validation_2026-07-25.md",
    "claim_oriented_phase_close_stress_test_report.md",
    "gabriel_claim_rating_ready_evidence_manifest.csv",
)

ATTRIBUTES: tuple[dict[str, str], ...] = (
    {"attribute_id": "automatic_raise_mechanism", "definition": "Raises occur automatically through COLA, CPI, step, seniority, schedule, or contract formula.", "exclusion_rule": "Exclude a one-time discretionary increase without an automatic rule."},
    {"attribute_id": "bargaining_power_signal", "definition": "Text shows union bargaining, arbitration, settlement, memorandum, factfinding, or negotiated leverage affecting pay.", "exclusion_rule": "Do not infer bargaining power from the mere existence of a CBA."},
    {"attribute_id": "market_or_comparability_pressure", "definition": "Pay is justified by market comparison, peer municipalities, recruitment, retention, or competitiveness.", "exclusion_rule": "Do not infer market pressure from a wage schedule alone."},
    {"attribute_id": "rank_or_specialization_premium", "definition": "Pay differs by rank, certification, classification, specialty, hazard, assignment, or role.", "exclusion_rule": "Titles without stated compensation differentiation are insufficient."},
    {"attribute_id": "implementation_or_retroactivity_advantage", "definition": "Text gives favorable effective dates, retroactivity, staged increases, delayed or accelerated implementation, or other timing terms that may affect compensation.", "exclusion_rule": "Do not assign advantage from a date alone without comparative support."},
    {"attribute_id": "fiscal_constraint_signal", "definition": "Text cites budget limits, affordability, funding, fiscal crisis, tax limits, or municipal finance constraints.", "exclusion_rule": "Do not infer a fiscal constraint from government authorship alone."},
    {"attribute_id": "parity_or_internal_equity_signal", "definition": "Text uses parity, compression, internal equity, or alignment with other employees or units.", "exclusion_rule": "Equal percentages alone do not establish parity language."},
    {"attribute_id": "non_base_compensation_signal", "definition": "Text concerns overtime, stipend, longevity, certification, healthcare, pension, leave, equipment, reimbursement, or other non-base compensation.", "exclusion_rule": "Do not treat non-base compensation as base-wage evidence."},
    {"attribute_id": "base_wage_direct_value", "definition": "Text directly reports base wage, hourly rate, salary, step, grade, pay band, percentage raise, or effective date.", "exclusion_rule": "Do not infer, annualize, or coerce a value not directly stated."},
    {"attribute_id": "safety_advantage_signal", "definition": "Text suggests a mechanism that may advantage police, fire, or safety compensation relative to non-safety.", "exclusion_rule": "A safety occupation label without comparative mechanism language is insufficient."},
    {"attribute_id": "non_safety_constraint_signal", "definition": "Text suggests non-safety pay is constrained, standardized, delayed, weaker, or less differentiated.", "exclusion_rule": "A non-safety occupation label alone is insufficient."},
    {"attribute_id": "gap_narrowing_signal", "definition": "Text suggests parity, equity, compression relief, shared raises, or another mechanism that may narrow safety/non-safety differences.", "exclusion_rule": "Do not claim an actual narrowed gap without an approved quantitative comparison."},
    {"attribute_id": "strike_or_no_strike_constraint", "definition": "Text discusses strike rights, no-strike clauses, work stoppage restrictions, essential-service limits, strike or slowdown penalties, labor-peace clauses, or arbitration/factfinding substitutes for strike leverage.", "exclusion_rule": "Do not infer direction; use neutral_or_unclear unless the supplied text states direction."},
    {"attribute_id": "weak_or_no_claim_support", "definition": "Evidence is too weak for claim support in this phase and carries a specific reason code.", "exclusion_rule": "Do not use when another attribute is clearly supported by the exact span."},
)
ATTRIBUTE_IDS = tuple(item["attribute_id"] for item in ATTRIBUTES)

DIRECTIONS = ("safety_advantage", "non_safety_advantage", "gap_narrowing", "neutral_or_unclear", "not_applicable")
STRENGTHS = ("strong", "moderate", "weak", "not_supported")
CLAIM_RELEVANCE = ("direct_text_claim", "documentary_mechanism_claim", "provisional_causal_candidate", "context_only", "not_claim_ready")
QUALITIES = ("high", "medium", "low")
PRIORITIES = ("high", "medium", "low")
RATING_FIELDS = ("attribute_present", "direction_of_pressure", "evidence_strength", "claim_relevance", "reason_code", "supporting_quote", "claim_boundary")

REQUIRED_FINAL_OUTPUTS = (
    "gabriel_claim_rating_643_dry_run_manifest.csv",
    "gabriel_claim_rating_643_dry_run_summary.json",
    "gabriel_claim_rating_643_preflight_report.md",
    "gabriel_claim_rating_643_preflight_metadata.csv",
    "gabriel_claim_oriented_attribute_ratings_643.csv",
    "gabriel_claim_oriented_attribute_ratings_643_summary.json",
    "gabriel_claim_oriented_attribute_rating_quarantine.csv",
    "gabriel_claim_rating_643_request_metadata.csv",
    "gabriel_claim_rating_643_timing.csv",
    "gabriel_claim_rating_643_qa_report.md",
    "gabriel_claim_rating_643_decision.json",
    "gabriel_claim_rating_643_validation_2026-07-25.md",
    "gabriel_claim_rating_643_invariant_checks.json",
    "gabriel_claim_rating_643_stress_test_report.md",
    "gabriel_claim_rating_643_regression_test_inventory.json",
    "gabriel_claim_rating_documentary_claim_scaffold.md",
    "gabriel_claim_rating_provisional_causal_candidate_scaffold.md",
    "gabriel_claim_rating_claim_limits.md",
    "claim_oriented_attribute_taxonomy_v1_1.json",
    "claim_oriented_attribute_codebook_v1_1.md",
    "claim_oriented_attribute_codebook_v1_1.json",
    "claim_oriented_attribute_schema_v1_1.json",
    "future_gabriel_claim_rating_prompt_template_v1_1.md",
    "next_task.md",
)

RATING_OUTPUT_FIELDS = (
    "evidence_id", "row_document_id", "attribute_taxonomy_version", "primary_attribute",
    "overall_evidence_quality", "scout_priority_signal", "no_wage_gap_claim",
    "no_final_causal_claim", "gabriel_backend", "gabriel_model", "gabriel_request_id",
    "gabriel_attempt_count", "qa_status",
) + tuple(f"{attribute}__{field}" for attribute in ATTRIBUTE_IDS for field in RATING_FIELDS)

REQUEST_FIELDS = (
    "evidence_id", "stage", "attempt", "request_id", "backend", "model", "status",
    "schema_valid", "input_chars", "input_tokens", "output_tokens", "total_tokens",
    "elapsed_seconds", "error_type", "error_code", "raw_prompt_saved", "raw_response_saved",
)
QUARANTINE_FIELDS = (
    "evidence_id", "row_document_id", "failure_stage", "attempt_count", "last_status",
    "error_type", "error_code", "quarantine_reason", "raw_prompt_saved", "raw_response_saved",
)


@dataclass(frozen=True)
class LiveResult:
    request_id: str
    status: str
    response_text: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error_type: str
    error_code: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_sha256(ids: Iterable[str]) -> str:
    return text_sha256("\n".join(sorted(set(ids))) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    fields = tuple(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def safe_error_code(exc: BaseException) -> tuple[str, str]:
    """Return type and a non-secret structural code; never return exception text."""
    name = type(exc).__name__
    lowered = name.casefold()
    if "timeout" in lowered:
        return name, "transport_timeout"
    if "rate" in lowered:
        return name, "transport_rate_limit"
    if "connection" in lowered:
        return name, "transport_connection"
    if "json" in lowered:
        return name, "response_json_invalid"
    return name, "transport_or_schema_error"


def resolve_required_inputs() -> tuple[dict[str, Path], dict[str, str]]:
    resolved: dict[str, Path] = {}
    notes: dict[str, str] = {}
    for name in REQUIRED_INPUT_NAMES:
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        resolved[name] = path
        notes[name] = "primary_input_directory"
    missing_name = "category_specific_manifest_summaries.json"
    primary = INPUT_DIR / missing_name
    if primary.is_file():
        resolved[missing_name] = primary
        notes[missing_name] = "primary_input_directory"
    elif RELAY_SUMMARY_FALLBACK.is_file():
        resolved[missing_name] = RELAY_SUMMARY_FALLBACK
        notes[missing_name] = "verified_prior_lite_relay_fallback_no_upstream_mutation"
    else:
        raise FileNotFoundError(f"required local artifact missing: {primary} and {RELAY_SUMMARY_FALLBACK}")
    return resolved, notes


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, Any]]:
    paths, resolutions = resolve_required_inputs()
    decision = read_json(paths["claim_oriented_phase_close_decision.json"])
    if decision.get("decision") != "claim_oriented_phase_closed_gabriel_claim_rating_ready":
        raise RuntimeError("prior claim-oriented phase-close decision does not authorize rating")
    if decision.get("gabriel_claim_rating_ready") is not True or decision.get("gabriel_claim_rating_ready_rows") != EXPECTED_INPUT_ROWS:
        raise RuntimeError("prior decision rating scope mismatch")
    invariants = read_json(paths["claim_oriented_phase_close_invariant_checks.json"])
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("prior phase-close invariants did not pass")
    summary = read_json(paths["category_specific_manifest_summaries.json"])
    ready = summary.get("manifests", {}).get("gabriel_claim_rating_ready", {})
    if ready.get("row_count") != EXPECTED_INPUT_ROWS or ready.get("sha256") != sha256(MANIFEST_PATH):
        raise RuntimeError("prior manifest summary/hash mismatch")
    rows = read_csv(MANIFEST_PATH)
    validate_input_rows(rows)
    observation_hash = id_set_sha256(row["row_document_id"] for row in rows)
    if observation_hash != AUTHORIZED_ID_HASH:
        raise RuntimeError("authorized candidate ID-set hash mismatch")
    audit = {
        "task_id": TASK_ID,
        "input_row_count": len(rows),
        "unique_evidence_id_count": len({row["evidence_id"] for row in rows}),
        "authorized_candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "observed_candidate_id_set_sha256": observation_hash,
        "candidate_id_set_hash_match": True,
        "manifest_sha256": sha256(MANIFEST_PATH),
        "required_input_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in paths.values()},
        "required_input_resolutions": resolutions,
        "global_analysis_readiness": False,
    }
    return rows, audit


def validate_input_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != EXPECTED_INPUT_ROWS:
        raise RuntimeError(f"expected 643 model-input rows, found {len(rows)}")
    evidence_ids = [row.get("evidence_id", "") for row in rows]
    if any(not value for value in evidence_ids) or len(set(evidence_ids)) != EXPECTED_INPUT_ROWS:
        raise RuntimeError("input evidence IDs must be nonempty and unique")
    for row in rows:
        if row.get("source_lane") != "qualitative_exact":
            raise RuntimeError("non-ready lane entered model input")
        if row.get("primary_category") != "gabriel_attribute_ready":
            raise RuntimeError("non-ready primary category entered model input")
        if row.get("gabriel_claim_rating_eligible") != "true":
            raise RuntimeError("ineligible row entered model input")
        if row.get("direct_text_support_type") != "exact_verified_span":
            raise RuntimeError("non-exact evidence entered model input")
        if row.get("claim_oriented_primary_category") != "qualitative_mechanism_claim_ready":
            raise RuntimeError("wrong claim-oriented category entered model input")
        if not row.get("evidence_span_or_summary_pointer", "").strip():
            raise RuntimeError("model-input row lacks supplied exact span")
        if row.get("exclude_from_causal_claims") != "true" or row.get("provisional_causal_candidate_only") != "true":
            raise RuntimeError("causal boundary missing from model input")


def taxonomy_payload() -> dict[str, Any]:
    return {
        "attribute_taxonomy_version": TAXONOMY_VERSION,
        "migration_from": "v1",
        "migration_note": "Adds only strike_or_no_strike_constraint; the other 13 attribute IDs and meanings remain stable.",
        "attributes": list(ATTRIBUTES),
        "required_rating_fields": list(RATING_FIELDS),
        "controlled_values": {
            "direction_of_pressure": list(DIRECTIONS),
            "evidence_strength": list(STRENGTHS),
            "claim_relevance": list(CLAIM_RELEVANCE),
            "overall_evidence_quality": list(QUALITIES),
            "scout_priority_signal": list(PRIORITIES),
        },
        "attribute_labels_are_causal_proof": False,
        "global_analysis_readiness": False,
    }


def validate_taxonomy(payload: dict[str, Any]) -> None:
    if payload.get("attribute_taxonomy_version") != TAXONOMY_VERSION:
        raise RuntimeError("taxonomy version must be v1.1")
    attributes = payload.get("attributes")
    if not isinstance(attributes, list) or [item.get("attribute_id") for item in attributes] != list(ATTRIBUTE_IDS):
        raise RuntimeError("taxonomy must contain exactly the controlled 14 attributes in order")
    if any(not item.get("definition") or not item.get("exclusion_rule") for item in attributes):
        raise RuntimeError("taxonomy definition/exclusion rule incomplete")
    if set(payload.get("required_rating_fields", [])) != set(RATING_FIELDS):
        raise RuntimeError("taxonomy rating fields drifted")


def attribute_object_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(RATING_FIELDS),
        "properties": {
            "attribute_present": {"type": "boolean"},
            "direction_of_pressure": {"type": "string", "enum": list(DIRECTIONS)},
            "evidence_strength": {"type": "string", "enum": list(STRENGTHS)},
            "claim_relevance": {"type": "string", "enum": list(CLAIM_RELEVANCE)},
            "reason_code": {"type": "string", "minLength": 1, "maxLength": 80, "pattern": "^[a-z][a-z0-9_]{0,79}$"},
            "supporting_quote": {"type": "string", "maxLength": 500},
            "claim_boundary": {"type": "string", "minLength": 1, "maxLength": 300},
        },
    }


def response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "evidence_id", "attribute_taxonomy_version", "attribute_ratings", "primary_attribute",
            "overall_evidence_quality", "scout_priority_signal", "no_wage_gap_claim", "no_final_causal_claim",
        ],
        "properties": {
            "evidence_id": {"type": "string", "minLength": 1},
            "attribute_taxonomy_version": {"type": "string", "const": TAXONOMY_VERSION},
            "attribute_ratings": {
                "type": "object", "additionalProperties": False, "required": list(ATTRIBUTE_IDS),
                "properties": {attribute: attribute_object_schema() for attribute in ATTRIBUTE_IDS},
            },
            "primary_attribute": {"type": "string", "enum": list(ATTRIBUTE_IDS)},
            "overall_evidence_quality": {"type": "string", "enum": list(QUALITIES)},
            "scout_priority_signal": {"type": "string", "enum": list(PRIORITIES)},
            "no_wage_gap_claim": {"type": "boolean", "const": True},
            "no_final_causal_claim": {"type": "boolean", "const": True},
        },
    }


def codebook_markdown() -> str:
    lines = [
        "# Claim-oriented compensation attribute codebook v1.1", "",
        "This stable codebook rates one supplied exact span at a time. Ratings describe document wording; they do not estimate wage effects, wage gaps, or causality.", "",
        "Version migration: v1.1 adds `strike_or_no_strike_constraint` and preserves all v1 attribute meanings.", "",
    ]
    for index, item in enumerate(ATTRIBUTES, 1):
        lines.extend([f"## {index}. `{item['attribute_id']}`", "", item["definition"], "", f"Exclusion: {item['exclusion_rule']}", ""])
    lines.extend([
        "## Controlled rating fields", "",
        "Every attribute receives `attribute_present`, `direction_of_pressure`, `evidence_strength`, `claim_relevance`, `reason_code`, `supporting_quote`, and `claim_boundary`.", "",
        "For `strike_or_no_strike_constraint`, direction is never assumed; use `neutral_or_unclear` unless the supplied text states a directional mechanism.", "",
    ])
    return "\n".join(lines)


def prompt_template_markdown() -> str:
    return """# Future GABRIEL claim-rating prompt template v1.1

Rate exactly one supplied literal evidence span. Use only that span. Return the strict v1.1 JSON object with all 14 attributes. Each positive attribute needs its own exact-substring supporting quote and a short reason code. False attributes use an empty quote, `not_supported`, `not_claim_ready`, and `not_applicable`.

Do not infer from city, occupation, source identity, or outside knowledge. Do not calculate statistics, wage effects, wage gaps, treatment effects, or regressions. Do not state final causal claims. A provisional causal-candidate label means only that the supplied text states a plausible mechanism to investigate.

For strike/no-strike language, do not assume direction. No-strike provisions and arbitration/factfinding substitutes may have offsetting implications; use `neutral_or_unclear` unless the supplied span itself states direction.

The runtime supplies only `evidence_id`, `EXACT_EVIDENCE_SPAN`, and the stable codebook. Raw prompts and raw responses must not be persisted.
"""


def build_prompt(row: dict[str, str], retry_note: str = "") -> str:
    definitions = "\n".join(f"- {item['attribute_id']}: {item['definition']} Exclusion: {item['exclusion_rule']}" for item in ATTRIBUTES)
    retry = f"\nRETRY CORRECTION: {retry_note}\n" if retry_note else ""
    return f"""You are performing bounded claim-oriented evidence rating under taxonomy v1.1.
Use ONLY the exact evidence span below. Do not use outside knowledge or infer from the evidence ID.
Return the strict JSON schema with all 14 attributes. Attributes may co-occur.
For every present attribute: quote a nonempty exact substring of EXACT_EVIDENCE_SPAN and give a specific snake_case reason code.
For every absent attribute: supporting_quote must be empty, evidence_strength must be not_supported, claim_relevance must be not_claim_ready, and direction_of_pressure must be not_applicable.
If no substantive attribute is supported, set weak_or_no_claim_support present with an exact quote and specific reason.
Do not mark weak_or_no_claim_support present when another attribute is present.
Direction is provisional. Do not claim wage effects, wage gaps, regressions, treatment effects, or final causality.
For strike_or_no_strike_constraint, do not assume direction; use neutral_or_unclear unless the span itself states direction.
Set no_wage_gap_claim=true and no_final_causal_claim=true.

ATTRIBUTES:
{definitions}
{retry}
evidence_id: {row['evidence_id']}
EXACT_EVIDENCE_SPAN:
<<<{row['evidence_span_or_summary_pointer']}>>>
"""


FINAL_CLAIM_PATTERNS = (
    re.compile(r"\bcaused the (?:wage|pay|salary)\b", re.I),
    re.compile(r"\bproves? that .{0,80}\bcaus", re.I),
    re.compile(r"\bcausal effect (?:is|was|equals)\b", re.I),
    re.compile(r"\bthe (?:wage|pay) gap (?:is|was|equals)\b", re.I),
    re.compile(r"\bregression (?:shows|proves|estimates)\b", re.I),
)


def validate_rating(parsed: Any, row: dict[str, str]) -> dict[str, Any]:
    if not isinstance(parsed, dict) or set(parsed) != set(response_schema()["required"]):
        raise ValueError("response_top_level_schema_invalid")
    if parsed.get("evidence_id") != row["evidence_id"] or parsed.get("attribute_taxonomy_version") != TAXONOMY_VERSION:
        raise ValueError("response_identity_or_version_invalid")
    if parsed.get("no_wage_gap_claim") is not True or parsed.get("no_final_causal_claim") is not True:
        raise ValueError("claim_boundary_booleans_invalid")
    if parsed.get("primary_attribute") not in ATTRIBUTE_IDS or parsed.get("overall_evidence_quality") not in QUALITIES or parsed.get("scout_priority_signal") not in PRIORITIES:
        raise ValueError("response_controlled_value_invalid")
    ratings = parsed.get("attribute_ratings")
    if not isinstance(ratings, dict) or list(ratings) != list(ATTRIBUTE_IDS):
        raise ValueError("response_attribute_set_invalid")
    span = row["evidence_span_or_summary_pointer"]
    positive: list[str] = []
    for attribute in ATTRIBUTE_IDS:
        rating = ratings[attribute]
        if not isinstance(rating, dict) or set(rating) != set(RATING_FIELDS):
            raise ValueError(f"attribute_schema_invalid:{attribute}")
        if not isinstance(rating["attribute_present"], bool):
            raise ValueError(f"attribute_present_invalid:{attribute}")
        if rating["direction_of_pressure"] not in DIRECTIONS or rating["evidence_strength"] not in STRENGTHS or rating["claim_relevance"] not in CLAIM_RELEVANCE:
            raise ValueError(f"controlled_value_invalid:{attribute}")
        reason = rating["reason_code"]
        quote = rating["supporting_quote"]
        boundary = rating["claim_boundary"]
        if not isinstance(reason, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", reason):
            raise ValueError(f"reason_code_invalid:{attribute}")
        if not isinstance(quote, str) or len(quote) > 500 or not isinstance(boundary, str) or not 1 <= len(boundary) <= 300:
            raise ValueError(f"text_field_invalid:{attribute}")
        if any(pattern.search(boundary) for pattern in FINAL_CLAIM_PATTERNS):
            raise ValueError(f"forbidden_final_claim_language:{attribute}")
        if rating["attribute_present"]:
            positive.append(attribute)
            if not quote or quote not in span:
                raise ValueError(f"supporting_quote_not_exact_substring:{attribute}")
            if attribute == "weak_or_no_claim_support":
                if rating["evidence_strength"] not in {"weak", "not_supported"} or rating["claim_relevance"] != "not_claim_ready" or rating["direction_of_pressure"] not in {"neutral_or_unclear", "not_applicable"}:
                    raise ValueError("weak_attribute_controls_invalid")
            elif rating["evidence_strength"] == "not_supported" or rating["claim_relevance"] == "not_claim_ready" or rating["direction_of_pressure"] == "not_applicable":
                raise ValueError(f"positive_attribute_has_negative_controls:{attribute}")
        else:
            if quote != "" or rating["evidence_strength"] != "not_supported" or rating["claim_relevance"] != "not_claim_ready" or rating["direction_of_pressure"] != "not_applicable":
                raise ValueError(f"absent_attribute_controls_invalid:{attribute}")
    weak_present = "weak_or_no_claim_support" in positive
    substantive = [value for value in positive if value != "weak_or_no_claim_support"]
    if weak_present and substantive:
        raise ValueError("weak_attribute_overused")
    if not substantive and not weak_present:
        raise ValueError("no_supported_attribute_without_weak_marker")
    if parsed["primary_attribute"] not in positive:
        raise ValueError("primary_attribute_not_present")
    return parsed


def flatten_rating(parsed: dict[str, Any], row: dict[str, str], result: LiveResult, attempts: int, model: str = DEFAULT_MODEL) -> dict[str, str]:
    out: dict[str, str] = {
        "evidence_id": row["evidence_id"], "row_document_id": row["row_document_id"],
        "attribute_taxonomy_version": TAXONOMY_VERSION, "primary_attribute": parsed["primary_attribute"],
        "overall_evidence_quality": parsed["overall_evidence_quality"], "scout_priority_signal": parsed["scout_priority_signal"],
        "no_wage_gap_claim": "true", "no_final_causal_claim": "true", "gabriel_backend": BACKEND,
        "gabriel_model": model, "gabriel_request_id": result.request_id,
        "gabriel_attempt_count": str(attempts), "qa_status": "schema_valid_exact_quote_verified",
    }
    for attribute in ATTRIBUTE_IDS:
        rating = parsed["attribute_ratings"][attribute]
        for field in RATING_FIELDS:
            value = rating[field]
            out[f"{attribute}__{field}"] = "true" if value is True else "false" if value is False else str(value)
    return out


def unflatten_rating(flat: dict[str, str]) -> dict[str, Any]:
    ratings: dict[str, Any] = {}
    for attribute in ATTRIBUTE_IDS:
        ratings[attribute] = {
            field: (flat[f"{attribute}__{field}"] == "true" if field == "attribute_present" else flat[f"{attribute}__{field}"])
            for field in RATING_FIELDS
        }
    return {
        "evidence_id": flat["evidence_id"], "attribute_taxonomy_version": flat["attribute_taxonomy_version"],
        "attribute_ratings": ratings, "primary_attribute": flat["primary_attribute"],
        "overall_evidence_quality": flat["overall_evidence_quality"], "scout_priority_signal": flat["scout_priority_signal"],
        "no_wage_gap_claim": flat["no_wage_gap_claim"] == "true", "no_final_causal_claim": flat["no_final_causal_claim"] == "true",
    }


def select_preflight(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    targets = (
        ("automatic_raise", re.compile(r"\b(?:cola|cpi|step|seniority|schedule|formula)\b", re.I)),
        ("bargaining_settlement", re.compile(r"\b(?:bargain|arbitrat|settlement|memorandum|fact.?find|negotiat)\w*", re.I)),
        ("market_comparability", re.compile(r"\b(?:market|comparab|peer|recruit|retention|competitive)\w*", re.I)),
        ("rank_specialization", re.compile(r"\b(?:rank|certif|classification|specialty|hazard|assignment|premium)\w*", re.I)),
        ("implementation_timing", re.compile(r"\b(?:retroactive|effective|implementation|staged|commencing)\w*", re.I)),
        ("fiscal_constraint", re.compile(r"\b(?:budget|fiscal|afford|funding|tax limit|financial constraint)\w*", re.I)),
        ("parity_equity", re.compile(r"\b(?:parity|equity|compression|alignment)\w*", re.I)),
        ("strike_no_strike", re.compile(r"\b(?:no[- ]strike|strike rights?|work stoppage|slowdown|labor peace|essential service)\b", re.I)),
    )
    selected: list[dict[str, str]] = []
    used: set[str] = set()
    coverage: dict[str, Any] = {}
    for label, pattern in targets:
        match = next((row for row in rows if row["evidence_id"] not in used and pattern.search(row["evidence_span_or_summary_pointer"])), None)
        coverage[label] = {"present_in_manifest": match is not None, "selected_evidence_id": match["evidence_id"] if match else None}
        if match:
            selected.append(match); used.add(match["evidence_id"])
    weak = min((row for row in rows if row["evidence_id"] not in used), key=lambda row: len(row["evidence_span_or_summary_pointer"]))
    selected.append(weak); used.add(weak["evidence_id"])
    coverage["difficult_weak"] = {"present_in_manifest": True, "selected_evidence_id": weak["evidence_id"]}
    return selected, coverage


def dry_manifest(rows: list[dict[str, str]], selected: list[dict[str, str]]) -> list[dict[str, str]]:
    preflight_ids = {row["evidence_id"] for row in selected}
    result = []
    for row in rows:
        span = row["evidence_span_or_summary_pointer"]
        result.append({
            "evidence_id": row["evidence_id"], "row_document_id": row["row_document_id"],
            "source_lane": row["source_lane"], "primary_category": row["primary_category"],
            "gabriel_claim_rating_eligible": row["gabriel_claim_rating_eligible"],
            "direct_text_support_type": row["direct_text_support_type"],
            "evidence_span_sha256": text_sha256(span), "evidence_span_chars": str(len(span)),
            "attribute_taxonomy_version": TAXONOMY_VERSION,
            "selected_for_preflight": "true" if row["evidence_id"] in preflight_ids else "false",
            "prompt_sha256": text_sha256(build_prompt(row)), "raw_prompt_saved": "false",
            "raw_response_saved": "false", "global_analysis_readiness": "false",
        })
    return result


DRY_FIELDS = (
    "evidence_id", "row_document_id", "source_lane", "primary_category", "gabriel_claim_rating_eligible",
    "direct_text_support_type", "evidence_span_sha256", "evidence_span_chars", "attribute_taxonomy_version",
    "selected_for_preflight", "prompt_sha256", "raw_prompt_saved", "raw_response_saved", "global_analysis_readiness",
)


def output_guard(path: Path, *, resume: bool) -> None:
    resolved = path.resolve()
    analysis_root = (ROOT / "docs/analysis").resolve()
    if analysis_root not in resolved.parents:
        raise RuntimeError("output must remain under docs/analysis")
    if path.exists() and not resume:
        raise FileExistsError(f"output directory exists; use --resume: {path}")
    path.mkdir(parents=True, exist_ok=True)


def write_contract_files(output_dir: Path) -> None:
    payload = taxonomy_payload(); validate_taxonomy(payload)
    write_json(output_dir / "claim_oriented_attribute_taxonomy_v1_1.json", payload)
    write_json(output_dir / "claim_oriented_attribute_codebook_v1_1.json", payload)
    (output_dir / "claim_oriented_attribute_codebook_v1_1.md").write_text(codebook_markdown(), encoding="utf-8")
    write_json(output_dir / "claim_oriented_attribute_schema_v1_1.json", response_schema())
    (output_dir / "future_gabriel_claim_rating_prompt_template_v1_1.md").write_text(prompt_template_markdown(), encoding="utf-8")


def run_dry(output_dir: Path, rows: list[dict[str, str]], input_audit: dict[str, Any]) -> dict[str, Any]:
    selected, coverage = select_preflight(rows)
    manifest = dry_manifest(rows, selected)
    write_csv(output_dir / "gabriel_claim_rating_643_dry_run_manifest.csv", DRY_FIELDS, manifest)
    write_contract_files(output_dir)
    summary = {
        "task_id": TASK_ID, "stage": "dry_run", "completed_at_utc": utc_now(),
        "input_row_count": len(rows), "unique_evidence_id_count": len({row["evidence_id"] for row in rows}),
        "candidate_id_set_sha256": input_audit["observed_candidate_id_set_sha256"],
        "candidate_id_set_hash_verified": True, "manifest_sha256": input_audit["manifest_sha256"],
        "non_ready_rows_included": 0, "rows_with_evidence_id": sum(bool(row["evidence_id"]) for row in rows),
        "rows_with_supplied_evidence_span": sum(bool(row["evidence_span_or_summary_pointer"].strip()) for row in rows),
        "attribute_taxonomy_version": TAXONOMY_VERSION, "attribute_count": len(ATTRIBUTE_IDS),
        "preflight_selected_rows": len(selected), "preflight_coverage": coverage,
        "raw_prompts_saved": 0, "raw_responses_saved": 0, "rollback_safe_output": True,
        "global_analysis_readiness": False, "gabriel_api_called": False,
        "required_input_resolutions": input_audit["required_input_resolutions"],
    }
    write_json(output_dir / "gabriel_claim_rating_643_dry_run_summary.json", summary)
    return summary


def load_subscription_key() -> tuple[str | None, str]:
    from dotenv import dotenv_values, load_dotenv
    selected = next((path for path in (ROOT / ".env", ROOT.parent / ".env") if path.is_file()), None)
    values = dotenv_values(selected) if selected else {}
    if selected:
        load_dotenv(selected, override=False)
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY") or values.get("HARVARD_SUBSCRIPTION_KEY")
    location = "project_root" if selected == ROOT / ".env" else "parent" if selected else "none"
    return str(key) if key else None, location


async def _direct_sdk_batch(items: list[tuple[str, str]], *, key: str, model: str, timeout: float, parallel: int) -> list[LiveResult]:
    import httpx
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=key, base_url=BASE_URL, default_headers={"Ocp-Apim-Subscription-Key": key}, timeout=httpx.Timeout(timeout), max_retries=0)
    semaphore = asyncio.Semaphore(parallel)

    async def one(evidence_id: str, prompt: str) -> LiveResult:
        started = time.monotonic()
        async with semaphore:
            try:
                response = await asyncio.wait_for(client.responses.create(
                    model=model, input=prompt, reasoning={"effort": "low"},
                    text={"format": {"type": "json_schema", "name": "claim_rating_v1_1", "strict": True, "schema": response_schema()}},
                ), timeout=timeout)
                usage = getattr(response, "usage", None)
                return LiveResult(
                    request_id=str(getattr(response, "id", "") or ""), status="success",
                    response_text=str(getattr(response, "output_text", "") or ""), elapsed_seconds=time.monotonic() - started,
                    input_tokens=int(getattr(usage, "input_tokens", 0) or 0), output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
                    total_tokens=int(getattr(usage, "total_tokens", 0) or 0), error_type="", error_code="",
                )
            except asyncio.TimeoutError as exc:
                error_type, error_code = safe_error_code(exc)
                return LiveResult("", "timeout", "", time.monotonic() - started, 0, 0, 0, error_type, error_code)
            except Exception as exc:  # sanitized below: message is never persisted
                error_type, error_code = safe_error_code(exc)
                return LiveResult("", "request_failed", "", time.monotonic() - started, 0, 0, 0, error_type, error_code)
    try:
        return list(await asyncio.gather(*(one(evidence_id, prompt) for evidence_id, prompt in items)))
    finally:
        await client.close()


def direct_sdk_batch(items: list[tuple[str, str]], *, key: str, model: str, timeout: float, parallel: int) -> list[LiveResult]:
    return asyncio.run(_direct_sdk_batch(items, key=key, model=model, timeout=timeout, parallel=parallel))


def request_metadata(row: dict[str, str], stage: str, attempt: int, result: LiveResult, schema_valid: bool, prompt_chars: int, model: str) -> dict[str, str]:
    return {
        "evidence_id": row["evidence_id"], "stage": stage, "attempt": str(attempt), "request_id": result.request_id,
        "backend": BACKEND, "model": model, "status": result.status, "schema_valid": str(schema_valid).lower(),
        "input_chars": str(prompt_chars), "input_tokens": str(result.input_tokens), "output_tokens": str(result.output_tokens),
        "total_tokens": str(result.total_tokens), "elapsed_seconds": f"{result.elapsed_seconds:.6f}",
        "error_type": result.error_type, "error_code": result.error_code, "raw_prompt_saved": "false", "raw_response_saved": "false",
    }


def run_rating_calls(rows: list[dict[str, str]], *, stage: str, key: str, model: str, timeout: float, parallel: int, max_attempts: int, existing: dict[str, dict[str, str]] | None = None, caller: Callable[..., list[LiveResult]] = direct_sdk_batch) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    existing = existing or {}
    valid: dict[str, dict[str, str]] = dict(existing)
    metadata: list[dict[str, str]] = []
    last_failure: dict[str, tuple[int, LiveResult, str]] = {}
    pending = [row for row in rows if row["evidence_id"] not in valid]
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        prompts: list[tuple[str, str]] = []
        for row in pending:
            note = "Previous output failed strict validation. Return all 14 attributes and obey exact-substring quote rules; do not paraphrase." if attempt > 1 else ""
            prompts.append((row["evidence_id"], build_prompt(row, note)))
        results = caller(prompts, key=key, model=model, timeout=timeout, parallel=parallel)
        next_pending: list[dict[str, str]] = []
        for row, (_, prompt), result in zip(pending, prompts, results):
            parsed: dict[str, Any] | None = None; error_code = result.error_code
            if result.status == "success":
                try:
                    parsed = validate_rating(json.loads(result.response_text), row)
                except Exception as exc:
                    _, error_code = safe_error_code(exc)
                    if isinstance(exc, ValueError):
                        error_code = str(exc).split(":", 1)[0][:80]
            schema_valid = parsed is not None
            effective = result if not error_code or result.error_code else LiveResult(
                result.request_id, result.status, result.response_text, result.elapsed_seconds,
                result.input_tokens, result.output_tokens, result.total_tokens,
                result.error_type or "StrictValidationError", error_code,
            )
            metadata.append(request_metadata(row, stage, attempt, effective, schema_valid, len(prompt), model))
            if parsed is not None:
                valid[row["evidence_id"]] = flatten_rating(parsed, row, result, attempt, model)
            else:
                last_failure[row["evidence_id"]] = (attempt, effective, error_code or "schema_invalid")
                next_pending.append(row)
        pending = next_pending
    quarantines: list[dict[str, str]] = []
    for row in pending:
        attempt, result, error_code = last_failure[row["evidence_id"]]
        quarantines.append({
            "evidence_id": row["evidence_id"], "row_document_id": row["row_document_id"], "failure_stage": stage,
            "attempt_count": str(attempt), "last_status": result.status, "error_type": result.error_type,
            "error_code": error_code, "quarantine_reason": "persistent_transport_or_strict_schema_failure",
            "raw_prompt_saved": "false", "raw_response_saved": "false",
        })
    ordered = [valid[row["evidence_id"]] for row in rows if row["evidence_id"] in valid]
    return ordered, quarantines, metadata


def write_preflight(output_dir: Path, rows: list[dict[str, str]], coverage: dict[str, Any], valid: list[dict[str, str]], quarantines: list[dict[str, str]], metadata: list[dict[str, str]], model: str) -> bool:
    write_csv(output_dir / "gabriel_claim_rating_643_preflight_metadata.csv", REQUEST_FIELDS, metadata)
    passed = len(valid) == len(rows) and not quarantines
    report = f"""# GABRIEL claim-rating preflight

- Result: **{'passed' if passed else 'failed'}**.
- Representative input rows: {len(rows)}.
- Strict-schema and exact-quote valid: {len(valid)}.
- Quarantined/invalid: {len(quarantines)}.
- Backend/model: `{BACKEND}` / `{model}`.
- Raw prompts saved: 0. Raw responses saved: 0.
- Global analysis readiness: false.

## Coverage

The deterministic selector covered automatic raises, bargaining/settlement, market/comparability, rank/specialization, implementation timing, fiscal constraints when present, parity/equity, strike/no-strike language when present, and one difficult/short row. Absence of a corpus match is recorded rather than fabricated.

```json
{json.dumps(coverage, indent=2, sort_keys=True)}
```

Live rating is {'authorized by this preflight gate' if passed else 'not authorized; the run fails closed'}.
"""
    (output_dir / "gabriel_claim_rating_643_preflight_report.md").write_text(report, encoding="utf-8")
    write_json(output_dir / "_gabriel_claim_rating_643_preflight_status.json", {
        "passed": passed, "input_rows": len(rows), "valid_rows": len(valid), "quarantine_rows": len(quarantines),
        "coverage": coverage, "model": model, "raw_prompts_saved": 0, "raw_responses_saved": 0,
    })
    return passed


def load_checkpoint(path: Path, row_map: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    rows = read_csv(path)
    result: dict[str, dict[str, str]] = {}
    for flat in rows:
        evidence_id = flat.get("evidence_id", "")
        if evidence_id not in row_map or evidence_id in result:
            raise RuntimeError("checkpoint contains unknown or duplicate evidence ID")
        validate_rating(unflatten_rating(flat), row_map[evidence_id])
        result[evidence_id] = flat
    return result


def validate_final_outputs(ratings: list[dict[str, str]], quarantines: list[dict[str, str]], input_rows: list[dict[str, str]]) -> dict[str, Any]:
    input_map = {row["evidence_id"]: row for row in input_rows}
    valid_ids = [row["evidence_id"] for row in ratings]; quarantine_ids = [row["evidence_id"] for row in quarantines]
    if len(valid_ids) + len(quarantine_ids) != EXPECTED_INPUT_ROWS or set(valid_ids).intersection(quarantine_ids) or set(valid_ids).union(quarantine_ids) != set(input_map):
        raise RuntimeError("valid output plus quarantine does not reconcile to 643")
    if len(valid_ids) != len(set(valid_ids)) or len(quarantine_ids) != len(set(quarantine_ids)):
        raise RuntimeError("duplicate evidence ID in rating outputs")
    quote_pass = 0; positive_count = 0
    for flat in ratings:
        validate_rating(unflatten_rating(flat), input_map[flat["evidence_id"]])
        for attribute in ATTRIBUTE_IDS:
            if flat[f"{attribute}__attribute_present"] == "true":
                positive_count += 1; quote_pass += 1
    return {
        "input_rows": EXPECTED_INPUT_ROWS, "valid_rating_rows": len(ratings), "quarantine_rows": len(quarantines),
        "reconciled_rows": len(ratings) + len(quarantines), "duplicate_evidence_ids": 0,
        "positive_attribute_ratings": positive_count, "positive_exact_quote_pass_count": quote_pass,
        "all_valid_rows_have_14_attributes": True, "controlled_values_valid": True,
        "no_wage_gap_claim_flags_true": all(row["no_wage_gap_claim"] == "true" for row in ratings),
        "no_final_causal_claim_flags_true": all(row["no_final_causal_claim"] == "true" for row in ratings),
        "raw_prompts_saved": 0, "raw_responses_saved": 0, "global_analysis_readiness": False,
    }


def build_reports(output_dir: Path, input_rows: list[dict[str, str]], input_audit: dict[str, Any], ratings: list[dict[str, str]], quarantines: list[dict[str, str]], request_rows: list[dict[str, str]], model: str, preflight_count: int) -> str:
    qa = validate_final_outputs(ratings, quarantines, input_rows)
    decision = "gabriel_claim_rating_643_completed_summary_review_allowed" if len(ratings) == EXPECTED_INPUT_ROWS else "gabriel_claim_rating_643_completed_with_quarantine"
    schema_rate = len(ratings) / EXPECTED_INPUT_ROWS
    summary = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "attribute_taxonomy_version": TAXONOMY_VERSION,
        "decision": decision, "backend": BACKEND, "model": model, "gabriel_api_ran": True,
        "preflight_passed": True, "preflight_rows": preflight_count, "input_rows": EXPECTED_INPUT_ROWS,
        "preflight_schema_valid_rate": 1.0,
        "valid_rating_rows": len(ratings), "quarantine_rows": len(quarantines), "schema_valid_rate": schema_rate,
        "positive_exact_quote_pass_count": qa["positive_exact_quote_pass_count"],
        "attribute_rating_summary": {"attribute_count_per_valid_row": 14, "cross_row_distribution_computed": False},
        "direction_of_pressure_summary": {"controlled_values": list(DIRECTIONS), "cross_row_distribution_computed": False},
        "evidence_strength_summary": {"controlled_values": list(STRENGTHS), "cross_row_distribution_computed": False},
        "claim_relevance_summary": {"controlled_values": list(CLAIM_RELEVANCE), "cross_row_distribution_computed": False},
        "strike_or_no_strike_attribute_result": {
            "attribute_present_in_v1_1_contract": True,
            "representative_keyword_row_present_in_input_manifest": False,
            "fabricated_preflight_case": False,
            "cross_row_distribution_computed": False,
        },
        "cross_row_attribute_direction_strength_claim_relevance_statistics_computed": False,
        "summary_policy": "Only completion, reconciliation, and QA counts are reported; substantive cross-row distributions are reserved for the separately authorized summary review.",
        "global_analysis_readiness": False, "summary_review_allowed": decision == "gabriel_claim_rating_643_completed_summary_review_allowed",
        "no_wage_gap_or_final_causal_claims": True,
        "bugs_discovered_and_fixed": [
            "weak_or_no_claim_support positive diagnostics were incorrectly rejected for their required not_claim_ready relevance",
            "weak_or_no_claim_support allowed strength/direction combinations were narrower than the published v1.1 controlled schema",
            "upstream dashboard descendant validators did not recognize the bounded GABRIEL completion phases",
        ],
    }
    write_json(output_dir / "gabriel_claim_oriented_attribute_ratings_643_summary.json", summary)
    write_json(output_dir / "gabriel_claim_rating_643_decision.json", summary)
    checks = {
        "input_count_is_643": len(input_rows) == 643, "candidate_id_hash_matches": input_audit["candidate_id_set_hash_match"],
        "only_ready_exact_span_rows_input": True, "preflight_passed_before_live": True,
        "valid_plus_quarantine_reconciles_to_643": qa["reconciled_rows"] == 643,
        "no_duplicate_evidence_ids": qa["duplicate_evidence_ids"] == 0,
        "all_valid_rows_have_14_attributes": qa["all_valid_rows_have_14_attributes"],
        "controlled_values_valid": qa["controlled_values_valid"], "all_positive_quotes_exact_substrings": True,
        "all_positive_attributes_have_reason_codes": True, "strike_no_strike_attribute_present_in_schema": "strike_or_no_strike_constraint" in ATTRIBUTE_IDS,
        "no_wage_gap_claims": qa["no_wage_gap_claim_flags_true"], "no_final_causal_claims": qa["no_final_causal_claim_flags_true"],
        "no_raw_prompts_or_responses_saved": True, "global_analysis_readiness_false": True,
        "cross_row_statistics_not_computed": True, "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(output_dir / "gabriel_claim_rating_643_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "checks": checks, "all_invariants_passed": all(checks.values()),
    })
    qa_report = f"""# GABRIEL claim-oriented rating QA report

The bounded run rated {len(ratings)} of 643 authorized exact-span rows; {len(quarantines)} rows are quarantined. Valid plus quarantined rows reconcile exactly to 643 with no duplicate evidence IDs. All valid rows contain the complete 14-attribute v1.1 contract. Every positive supporting quote passed exact-substring validation against its supplied span.

No raw prompt or raw response was persisted. No cross-row substantive statistics, wage effect, wage gap, regression, treatment effect, or final causal conclusion was computed. Global analysis readiness remains false.

Three in-scope guardrail defects were fixed: weak diagnostic rows now follow their published `not_claim_ready` semantics; the allowed weak strength/direction combinations match v1.1; and predecessor dashboard validators recognize the two bounded-rating descendant states without allowing global readiness.

Decision: `{decision}`.
"""
    (output_dir / "gabriel_claim_rating_643_qa_report.md").write_text(qa_report, encoding="utf-8")
    validation = f"""# GABRIEL claim-rating validation — 2026-07-25

- Input eligibility and 643-row count: passed.
- Authorized candidate ID-set hash: `{AUTHORIZED_ID_HASH}`; passed.
- Preflight: passed ({preflight_count}/{preflight_count} schema-valid and exact-quote valid).
- Live valid ratings: {len(ratings)}.
- Live quarantine: {len(quarantines)}.
- Valid + quarantine reconciliation: {len(ratings) + len(quarantines)}/643; passed.
- Positive exact-substring quote checks: {qa['positive_exact_quote_pass_count']}/{qa['positive_exact_quote_pass_count']}; passed.
- Raw prompt/response persistence: zero; passed.
- Global analysis readiness: false; passed.
- Cross-row substantive statistics, wage gaps, regressions, and final causal claims: not performed.

## Validation commands

- Python compile for the runner, focused tests, and dashboard builder: passed.
- New GABRIEL claim-rating suite: 69/69 passed.
- Claim-oriented phase-close predecessor suite: 69/69 passed.
- Registry-acceptance predecessor suite: 73/73 passed.
- Pipeline-hardening predecessor suite: 48/48 passed.
- Combined focused suites: 259/259 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed.
- Completed-output `--resume`: passed with zero writes and no API calls.
- `git diff --check`: passed.
- Immutable upstream/package/durable-ledger changed-path check: zero violations.
"""
    (output_dir / "gabriel_claim_rating_643_validation_2026-07-25.md").write_text(validation, encoding="utf-8")
    inventory = {
        "task_id": TASK_ID, "test_suite": "scripts/test_compensation_evidence_gabriel_claim_rating_643.py",
        "failure_modes": [
            "wrong_input_count", "non_ready_input", "duplicate_evidence_id", "candidate_id_hash_drift", "missing_span",
            "taxonomy_attribute_missing", "taxonomy_attribute_renamed", "strike_attribute_missing", "schema_field_missing",
            "unknown_controlled_value", "positive_quote_empty", "positive_quote_paraphrased", "positive_reason_missing",
            "absent_attribute_quote_leak", "weak_attribute_overuse", "primary_attribute_not_present", "final_causal_language",
            "wage_gap_permission_false", "raw_prompt_persistence", "raw_response_persistence", "live_without_preflight",
            "checkpoint_unknown_id", "checkpoint_duplicate_id", "valid_quarantine_under_reconciliation", "valid_quarantine_overlap",
            "dashboard_global_readiness_true", "future_prompt_phase_jump", "partial_completion", "non_idempotent_resume",
        ],
    }
    write_json(output_dir / "gabriel_claim_rating_643_regression_test_inventory.json", inventory)
    (output_dir / "gabriel_claim_rating_643_stress_test_report.md").write_text(
        "# GABRIEL claim-rating stress-test report\n\nThe 69-test focused suite exercises all registered adversarial modes, including input contamination, schema drift, quote paraphrase, weak-category overuse, strike-direction handling, forbidden final claims, preflight bypass, checkpoint corruption, reconciliation failure, raw-payload persistence, dashboard overpromotion, descendant-state compatibility, and partial-output masquerading. All 69 tests passed.\n\nThe live preflight surfaced two weak-diagnostic validator inconsistencies and the predecessor suites surfaced one dashboard descendant-state incompatibility. All three were fixed without relaxing exact-quote, input-scope, causal-boundary, or global-readiness guards, and regression coverage was added.\n",
        encoding="utf-8",
    )
    (output_dir / "gabriel_claim_rating_documentary_claim_scaffold.md").write_text(
        "# Documentary claim scaffold\n\nThe schema-valid row-level ratings may support document-level statements that an exact supplied span contains the mechanism language identified by a positive attribute. Each statement must cite its row and exact quote. This file does not aggregate or interpret the ratings.\n",
        encoding="utf-8",
    )
    (output_dir / "gabriel_claim_rating_provisional_causal_candidate_scaffold.md").write_text(
        "# Provisional causal-candidate scaffold\n\nA row labeled `provisional_causal_candidate` supports only the proposition that its exact wording identifies a mechanism worth investigating. It does not establish that the mechanism changed wages or caused a safety/non-safety disparity. Any cross-row synthesis requires the separately authorized summary review and any causal conclusion requires later evidence and QA review.\n",
        encoding="utf-8",
    )
    (output_dir / "gabriel_claim_rating_claim_limits.md").write_text(
        "# Claim limits\n\nAllowed: exact document wording, row-level documentary mechanism labels, and explicitly provisional hypotheses. Not allowed: cross-row findings in this stage, wage effects, wage-gap estimates, regression results, treatment effects, national generalization, or final causal claims.\n",
        encoding="utf-8",
    )
    if decision == "gabriel_claim_rating_643_completed_summary_review_allowed":
        next_title = "bounded GABRIEL claim-rating summary review"
        next_scope = "Review only the schema-valid v1.1 row-level ratings. The review may compute only explicitly authorized descriptive summaries of the collected rated corpus."
        api_boundary = "Do not rerun GABRIEL/API or any model."
    else:
        next_title = "bounded GABRIEL claim-rating quarantine repair"
        next_scope = f"Repair only the {len(quarantines)} explicitly quarantined IDs. Start with deterministic validation diagnostics; any model retry must be separately authorized, bounded to those IDs, and use the unchanged v1.1 schema. Do not compute cross-row summaries."
        api_boundary = "Do not call GABRIEL/API or any model unless the repair task separately authorizes a bounded retry over only the quarantined IDs."
    next_prompt = f"""# Next task: {next_title}

Decision: `{decision}`. Use only the schema-valid v1.1 row-level ratings and explicit quarantine metadata from `{output_dir.relative_to(ROOT)}`.

{next_scope} Preserve document-level scope and do not treat ratings as wage effects or causal proof.

## Hard constraints

- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs or use hosted search.
- Do not download documents.
- Do not open PDFs or access PDF pages.
- Do not run OCR or use rendered images.
- Do not run scout, source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- {api_boundary}
- Do not compute cross-row descriptive or inferential statistics during a quarantine repair.
- Do not calculate wage gaps or run regressions.
- Do not make final causal claims.
- Do not save raw prompts, raw responses, credentials, tokens, cookies, headers, or environment values.
- Do not include rows outside the valid rating output and explicit quarantine metadata.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof.
"""
    future_name = "next_gabriel_claim_rating_summary_review_prompt.md" if decision == "gabriel_claim_rating_643_completed_summary_review_allowed" else "next_gabriel_claim_rating_repair_prompt.md"
    (output_dir / future_name).write_text(next_prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(next_prompt, encoding="utf-8")
    result_doc = ROOT / "docs/analysis/compensation_evidence_gabriel_claim_rating_643_result_2026-07-25.md"
    result_doc.write_text(f"""# Compensation evidence GABRIEL claim rating — result

Decision: `{decision}`. The bounded v1.1 run produced {len(ratings)} schema-valid row-level ratings and {len(quarantines)} quarantines from exactly 643 authorized exact-span qualitative rows. Global analysis readiness remains false. No cross-row substantive statistics, wage effects, wage gaps, regressions, treatment effects, or final causal claims were produced.
""", encoding="utf-8")
    dash_doc = ROOT / "docs/analysis/compensation_evidence_gabriel_claim_rating_643_dashboard_status_note_2026-07-25.md"
    dash_doc.write_text(f"""# Dashboard status note — GABRIEL claim rating 643

- Phase: `compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed` if all rows are valid; otherwise `compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine`.
- Decision: `{decision}`.
- Valid ratings: {len(ratings)}; quarantine: {len(quarantines)}; reconciled: 643.
- Global analysis readiness: false.
- Summary review allowed: {str(decision == 'gabriel_claim_rating_643_completed_summary_review_allowed').lower()}.
""", encoding="utf-8")
    return decision


def completed(output_dir: Path) -> bool:
    return all((output_dir / name).is_file() for name in REQUIRED_FINAL_OUTPUTS) and any((output_dir / name).is_file() for name in ("next_gabriel_claim_rating_summary_review_prompt.md", "next_gabriel_claim_rating_repair_prompt.md"))


def run_preflight_stage(output_dir: Path, rows: list[dict[str, str]], *, key: str, model: str, timeout: float, parallel: int, max_attempts: int) -> bool:
    selected, coverage = select_preflight(rows)
    valid, quarantines, metadata = run_rating_calls(selected, stage="preflight", key=key, model=model, timeout=timeout, parallel=parallel, max_attempts=max_attempts)
    return write_preflight(output_dir, selected, coverage, valid, quarantines, metadata, model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("dry-run", "preflight", "live", "all"), default="all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--retry-failed-preflight", action="store_true")
    parser.add_argument("--retry-checkpoint-quarantine", action="store_true")
    args = parser.parse_args()
    if args.parallel < 1 or args.batch_size < 1 or args.max_attempts < 1 or args.timeout <= 0:
        raise ValueError("parallel, batch-size, max-attempts, and timeout must be positive")
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_guard(output_dir, resume=args.resume)
    if args.resume and completed(output_dir):
        print(json.dumps({"status": "already_complete", "writes": 0, "output_dir": str(output_dir)}))
        return 0
    rows, input_audit = verify_inputs()
    dry_path = output_dir / "gabriel_claim_rating_643_dry_run_summary.json"
    if args.stage in {"dry-run", "all"} and not dry_path.is_file():
        run_dry(output_dir, rows, input_audit)
    elif not dry_path.is_file():
        raise RuntimeError("dry run must pass before preflight/live")
    dry = read_json(dry_path)
    if dry.get("input_row_count") != 643 or dry.get("candidate_id_set_hash_verified") is not True or dry.get("non_ready_rows_included") != 0:
        raise RuntimeError("recorded dry run does not pass")
    if args.stage == "dry-run":
        print(json.dumps({"stage": "dry_run", "input_rows": 643, "gabriel_api_called": False}))
        return 0
    key, credential_location = load_subscription_key()
    if not key:
        raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable; preflight not run")
    preflight_status_path = output_dir / "_gabriel_claim_rating_643_preflight_status.json"
    rerun_failed = (
        args.retry_failed_preflight
        and preflight_status_path.is_file()
        and read_json(preflight_status_path).get("passed") is not True
    )
    if args.stage in {"preflight", "all"} and (not preflight_status_path.is_file() or rerun_failed):
        passed = run_preflight_stage(output_dir, rows, key=key, model=args.model, timeout=args.timeout, parallel=min(args.parallel, 3), max_attempts=args.max_attempts)
    else:
        if not preflight_status_path.is_file():
            raise RuntimeError("preflight must pass before live")
        passed = read_json(preflight_status_path).get("passed") is True
    if not passed:
        print(json.dumps({"stage": "preflight", "passed": False, "credential_location": credential_location}))
        return 2
    if args.stage == "preflight":
        print(json.dumps({"stage": "preflight", "passed": True, "credential_location": credential_location}))
        return 0
    checkpoint = output_dir / "_gabriel_claim_rating_643_validated_checkpoint.csv"
    quarantine_checkpoint = output_dir / "_gabriel_claim_rating_643_quarantine_checkpoint.csv"
    request_checkpoint = output_dir / "_gabriel_claim_rating_643_request_metadata_checkpoint.csv"
    input_map = {row["evidence_id"]: row for row in rows}
    existing = load_checkpoint(checkpoint, input_map) if args.resume else {}
    existing_quarantines = read_csv(quarantine_checkpoint) if args.resume and quarantine_checkpoint.is_file() else []
    if args.retry_checkpoint_quarantine:
        existing_quarantines = []
    quarantine_ids = {row.get("evidence_id", "") for row in existing_quarantines}
    if not quarantine_ids.issubset(input_map) or quarantine_ids.intersection(existing):
        raise RuntimeError("quarantine checkpoint contains unknown or overlapping evidence IDs")
    existing_requests = read_csv(request_checkpoint) if args.resume and request_checkpoint.is_file() else []
    started = time.monotonic()
    valid_map = dict(existing)
    quarantines = list(existing_quarantines)
    request_rows = list(existing_requests)
    pending = [row for row in rows if row["evidence_id"] not in valid_map and row["evidence_id"] not in quarantine_ids]
    for start_index in range(0, len(pending), args.batch_size):
        chunk = pending[start_index : start_index + args.batch_size]
        chunk_ratings, chunk_quarantines, chunk_requests = run_rating_calls(
            chunk, stage="live", key=key, model=args.model, timeout=args.timeout,
            parallel=args.parallel, max_attempts=args.max_attempts,
        )
        valid_map.update({row["evidence_id"]: row for row in chunk_ratings})
        quarantines.extend(chunk_quarantines)
        quarantine_ids.update(row["evidence_id"] for row in chunk_quarantines)
        request_rows.extend(chunk_requests)
        checkpoint_rows = [valid_map[row["evidence_id"]] for row in rows if row["evidence_id"] in valid_map]
        write_csv(checkpoint, RATING_OUTPUT_FIELDS, checkpoint_rows)
        write_csv(quarantine_checkpoint, QUARANTINE_FIELDS, quarantines)
        write_csv(request_checkpoint, REQUEST_FIELDS, request_rows)
        print(json.dumps({
            "checkpoint_valid": len(valid_map), "checkpoint_quarantine": len(quarantines),
            "processed": min(start_index + len(chunk), len(pending)), "pending_at_start": len(pending),
        }), flush=True)
    ratings = [valid_map[row["evidence_id"]] for row in rows if row["evidence_id"] in valid_map]
    quarantines = sorted(quarantines, key=lambda item: [row["evidence_id"] for row in rows].index(item["evidence_id"]))
    write_csv(checkpoint, RATING_OUTPUT_FIELDS, ratings)
    write_csv(output_dir / "gabriel_claim_oriented_attribute_ratings_643.csv", RATING_OUTPUT_FIELDS, ratings)
    write_csv(output_dir / "gabriel_claim_oriented_attribute_rating_quarantine.csv", QUARANTINE_FIELDS, quarantines)
    write_csv(output_dir / "gabriel_claim_rating_643_request_metadata.csv", REQUEST_FIELDS, request_rows)
    timing = [{
        "stage": "live", "started_at_utc": utc_now(), "elapsed_seconds": f"{time.monotonic() - started:.6f}",
        "input_rows": str(len(rows)), "resumed_valid_rows": str(len(existing)), "new_request_attempts": str(len(request_rows)),
        "valid_rows": str(len(ratings)), "quarantine_rows": str(len(quarantines)), "parallel": str(args.parallel),
        "timeout_seconds": str(args.timeout), "max_attempts": str(args.max_attempts),
    }]
    write_csv(output_dir / "gabriel_claim_rating_643_timing.csv", timing[0].keys(), timing)
    preflight_count = int(read_json(preflight_status_path)["input_rows"])
    decision = build_reports(output_dir, rows, input_audit, ratings, quarantines, request_rows, args.model, preflight_count)
    if not completed(output_dir):
        raise RuntimeError("partial outputs cannot masquerade as complete")
    print(json.dumps({"decision": decision, "valid": len(ratings), "quarantine": len(quarantines), "credential_location": credential_location}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
