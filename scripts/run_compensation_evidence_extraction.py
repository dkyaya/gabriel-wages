#!/usr/bin/env python3
"""Freeze and run bounded provisional compensation-evidence extraction lanes."""

from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader

from run_compensation_extraction_targeted_qa import (
    conflict_resolution as targeted_conflict_resolution,
    nonbase_type as targeted_nonbase_type,
)


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25"
OUTPUT_ID = "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25"
TASK_1000_ID = "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-PROVISIONAL-SCALE-2026-07-25"
OUTPUT_1000_ID = "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
BACKEND = "huit_openai_responses_direct_sdk"
MODEL = "gpt-5.4-nano"
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"

DETECTION = ROOT / "docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv"
READINESS = ROOT / "docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv"
SOURCE_REVIEW = ROOT / "docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv"
GATE3 = ROOT / "docs/analysis/text_table_calibration/TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25/auto_gabriel_compensation_adjudication_ledger.csv"
BLINDED = ROOT / "docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/independent_adjudication_blinded_review_input.csv"
RENDER_MANIFEST = ROOT / "docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/independent_adjudication_render_manifest.csv"
EXTRACTION_500_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25"
TARGETED_QA_500_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25"

SELECTION_FIELDS = [
    "selection_rank", "extraction_case_id", "document_identity_id",
    "text_table_detection_id", "pdf_readiness_id", "source_review_id",
    "candidate_queue_row_id", "triage_id", "verification_id", "state",
    "municipality", "government_name", "unit_type", "candidate_source_type",
    "contract_period_start", "contract_period_end", "content_artifact_path",
    "content_hash", "pdf_page_count", "text_layer_status", "wage_table_signal",
    "extraction_pilot_priority", "candidate_wage_pages", "selection_score",
    "selection_reason_codes", "matched_group_id", "matched_non_safety_selected",
    "matched_non_safety_case_id", "planned_lane", "gate3_category",
    "gate3_confidence", "existing_rendered_page_count", "selection_status",
]
SELECTION_1000_FIELDS = SELECTION_FIELDS + [
    "cumulative_cohort", "requires_gabriel", "seed_selection_rank",
]

PACKET_FIELDS = [
    "extraction_case_id", "document_identity_id", "text_table_detection_id",
    "page_number", "page_role", "bounded_evidence_pointer", "text_chars",
    "wage_term_count", "numeric_token_count", "table_like_line_count",
    "qualitative_mechanism_term_count", "non_base_wage_term_count",
    "reference_signal", "rendered_image_available", "rendered_image_path",
    "packet_page_count", "packet_text_chars", "packet_status",
]
PACKET_1000_FIELDS = PACKET_FIELDS + ["cumulative_cohort"]

CUMULATIVE_QA_FIELDS = [
    "cumulative_cohort", "source_seed_observation_id", "qa_original_status",
    "qa_resolution_classification", "qa_resolution_status",
    "canonical_observation_id", "duplicate_of", "active_in_provisional_lane",
]

METADATA_FIELDS = [
    "request_phase", "extraction_case_id", "gabriel_request_id",
    "gabriel_backend", "gabriel_model", "request_status", "schema_valid",
    "prompt_sha256", "prompt_chars", "input_page_count", "input_text_chars",
    "input_image_count", "input_image_bytes", "raw_prompt_saved",
    "raw_response_saved", "encoded_image_saved", "response_sha256",
    "response_chars", "input_tokens", "output_tokens", "total_tokens",
    "elapsed_seconds", "error_type", "error_message", "credential_value_saved",
    "authorization_header_saved",
]

TIMING_FIELDS = [
    "request_phase", "extraction_case_id", "started_at", "finished_at",
    "local_packet_seconds", "gabriel_elapsed_seconds", "request_status",
]

QUANT_FIELDS = [
    "quantitative_observation_id", "extraction_case_id", "mixed_join_key",
    "document_identity_id", "text_table_detection_id", "source_review_id",
    "candidate_queue_row_id", "state", "municipality", "government_name",
    "unit_type", "candidate_source_type", "contract_period_start",
    "contract_period_end", "page_number", "compensation_type",
    "occupation_unit_classification_rank", "rate_value", "salary_value",
    "hourly_rate", "annual_salary", "pay_band", "step", "grade",
    "percentage_increase", "effective_date", "currency_or_unit",
    "bounded_evidence_pointer", "confidence", "reason_code", "qa_status",
]

QUAL_FIELDS = [
    "qualitative_observation_id", "extraction_case_id", "mixed_join_key",
    "document_identity_id", "text_table_detection_id", "source_review_id",
    "candidate_queue_row_id", "state", "municipality", "government_name",
    "unit_type", "candidate_source_type", "contract_period_start",
    "contract_period_end", "page_number", "mechanism_type",
    "bargaining_logic", "indexing_formula", "comparability_basis",
    "parity_logic", "step_progression_rule", "eligibility_rule",
    "implementation_rule", "fiscal_constraint", "reopener_clause",
    "differentiation_logic", "bounded_evidence_pointer", "confidence",
    "reason_code", "qa_status",
]

MIXED_FIELDS = [
    "mixed_join_key", "extraction_case_id", "document_identity_id",
    "text_table_detection_id", "source_review_id", "candidate_queue_row_id",
    "state", "municipality", "government_name", "unit_type",
    "candidate_source_type", "quantitative_observation_ids",
    "qualitative_observation_ids", "quantitative_observation_count",
    "qualitative_observation_count", "confidence", "reason_codes", "qa_status",
]

NONBASE_FIELDS = [
    "non_base_wage_observation_id", "extraction_case_id", "document_identity_id",
    "text_table_detection_id", "source_review_id", "candidate_queue_row_id",
    "state", "municipality", "government_name", "unit_type",
    "candidate_source_type", "contract_period_start", "contract_period_end",
    "page_number", "non_base_wage_type", "value_text", "effective_date",
    "eligibility_or_implementation_rule", "bounded_evidence_pointer",
    "confidence", "reason_code", "qa_status",
]

REFERENCE_FIELDS = [
    "extraction_case_id", "document_identity_id", "text_table_detection_id",
    "source_review_id", "candidate_queue_row_id", "state", "municipality",
    "government_name", "unit_type", "candidate_source_type", "disposition",
    "page_relationship", "bounded_evidence_pointer", "confidence",
    "reason_codes", "short_rationale", "qa_status",
]

CONFLICT_REVIEW_FIELDS = [
    "review_type", "extraction_case_id", "page_number", "lane",
    "observation_ids", "observation_count", "qa_reason",
]
CONFLICT_1000_FIELDS = CONFLICT_REVIEW_FIELDS + [
    "resolution_classification", "resolution_status", "unresolved_flag",
    "structured_basis", "canonical_observation_id", "duplicate_observation_ids",
]

DISPOSITIONS = {
    "quantitative_ready", "qualitative_ready", "mixed_ready", "non_base_wage",
    "reference_only", "exclude", "second_review",
}
CONFIDENCE = {"high", "medium", "low", "unknown"}
COMP_TYPES = {
    "rate", "salary", "hourly_rate", "annual_salary", "pay_band", "step",
    "grade", "percentage_increase", "other",
}
MECHANISM_TYPES = {
    "collective_bargaining_agreement_terms", "memorandum_or_settlement_terms",
    "arbitration_or_factfinding_reasoning", "CPI_or_COLA_indexing",
    "comparability_or_market_study", "parity_or_internal_equity",
    "step_movement_or_seniority", "rank_or_classification_differentiation",
    "certification_or_education_incentive", "longevity_or_service_based_pay",
    "fiscal_constraint_or_budget_logic", "wage_reopener_or_future_negotiation",
    "implementation_or_effective_date_logic", "other",
}
NONBASE_TYPES = {
    "overtime", "stipend", "longevity", "education_or_certification",
    "healthcare_contributions", "pension", "leave", "reimbursements",
    "uniform_or_equipment", "benefits", "other",
}
RELATIONSHIPS = {
    "exact_evidence_page", "adjacent_to_evidence", "points_to_later_evidence",
    "wrong_page", "no_candidate_page", "unknown",
}
CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,39}$")

WAGE_RE = re.compile(r"\b(wage|salary|pay|rate|step|grade|compensation|hourly|annual|increase)\b", re.I)
NUM_RE = re.compile(r"(?:\$\s*)?\d[\d,]*(?:\.\d+)?\s*%?")
TABLE_RE = re.compile(r"\b(step|grade|rank|classification|salary|hourly|annual|rate)\b.*\d", re.I)
QUAL_RE = re.compile(r"\b(CPI|COLA|comparab|parity|equity|seniority|progression|negotiat|bargain|arbitrat|fact.?find|market|reopener|effective|implement|fiscal|budget)\w*\b", re.I)
NONBASE_RE = re.compile(r"\b(overtime|stipend|longevity|certification|education pay|health|pension|leave|reimburse|uniform|equipment|benefit|insurance)\w*\b", re.I)
REFERENCE_RE = re.compile(r"\b(table of contents|contents|index|appendix|schedule [A-Z]|see exhibit|refer to)\b", re.I)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}_{sha_bytes('|'.join(values).encode())[:24]}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_pages(value: str, page_count: int) -> list[int]:
    result: list[int] = []
    for token in re.findall(r"\d+", value or ""):
        page = int(token)
        if 1 <= page <= page_count and page not in result:
            result.append(page)
    return result


def round_robin(rows: list[dict[str, Any]], count: int, key: str = "state") -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row[key])].append(row)
    for values in buckets.values():
        values.sort(key=lambda r: (-float(r["_score"]), str(r.get("content_hash", ""))))
    picked: list[dict[str, Any]] = []
    while len(picked) < count and any(buckets.values()):
        for bucket in sorted(buckets):
            if buckets[bucket] and len(picked) < count:
                picked.append(buckets[bucket].pop(0))
    return picked


def load_inputs(gate3_path: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    detection = read_csv(DETECTION)
    readiness = {r["pdf_readiness_id"]: r for r in read_csv(READINESS)}
    source = {r["source_review_id"]: r for r in read_csv(SOURCE_REVIEW)}
    gate3 = {r["content_artifact_path"]: r for r in read_csv(gate3_path)}
    eligible: list[dict[str, Any]] = []
    for row in detection:
        ready = readiness.get(row["pdf_readiness_id"])
        review = source.get(row["source_review_id"])
        artifact = Path(row["content_artifact_path"])
        if not artifact.is_absolute():
            artifact = ROOT / artifact
        if not ready or not review:
            continue
        if not (
            row["detection_status"] == "detection_checked"
            and row["text_layer_status"] in {"present", "partial"}
            and ready["readiness_status"] == "readiness_checked"
            and ready["artifact_exists"] == "yes"
            and ready["artifact_hash_verified"] == "yes"
            and ready["pdf_signature_valid"] == "yes"
            and ready["ocr_needed_signal"] == "no"
            and artifact.is_file()
        ):
            continue
        g3 = gate3.get(row["content_artifact_path"], {})
        score = 0.0
        score += {"likely": 20, "possible": 8, "unlikely": 0}.get(row["wage_table_signal"], 0)
        score += {"p1": 10, "p2": 4, "p3": 0}.get(row["extraction_pilot_priority"], 0)
        score += 4 * sum(row.get(field) == "yes" for field in (
            "pay_schedule_signal", "salary_schedule_signal", "hourly_rate_signal",
            "step_grade_signal", "rank_position_signal", "effective_date_signal",
            "table_like_structure_signal",
        ))
        if g3.get("compensation_evidence_category") in {
            "quant_table_ready", "quant_compact_ready", "quant_prose_ready",
            "qual_mechanism_ready", "mixed_quant_qual_ready",
        } and g3.get("gate3_confidence") in {"high", "medium"}:
            score += 50
        if row["candidate_source_type"] != "cba":
            score += 12
        item: dict[str, Any] = {**row, "_ready": ready, "_source": review, "_gate3": g3, "_artifact": artifact, "_score": score}
        eligible.append(item)
    by_hash: dict[str, dict[str, Any]] = {}
    for row in sorted(eligible, key=lambda r: (-r["_score"], r["text_table_detection_id"])):
        by_hash.setdefault(row["content_hash"], row)
    return list(by_hash.values()), source


def freeze_selection(gate3_path: Path, output: Path, limit: int) -> list[dict[str, str]]:
    eligible, _ = load_inputs(gate3_path)
    groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in eligible:
        groups[(row["state"], row["municipality"])][row["unit_type"]].append(row)
    matched = {k: v for k, v in groups.items() if v["non_safety"] and (v["police"] or v["fire"])}
    group_rows: list[dict[str, Any]] = []
    for (state, municipality), units in matched.items():
        group_rows.append({
            "state": state, "municipality": municipality,
            "_score": max(r["_score"] for values in units.values() for r in values) + 2 * (len(units["police"]) + len(units["fire"])),
            "_units": units,
        })
    seeds = round_robin(group_rows, 200)
    selected: list[dict[str, Any]] = []
    seed_groups = {(r["state"], r["municipality"]): r["_units"] for r in seeds}
    for seed in seeds:
        selected.append(sorted(seed["_units"]["non_safety"], key=lambda r: (-r["_score"], r["content_hash"]))[0])
    for unit, target in (("police", 180), ("fire", 120)):
        candidates = [r for units in seed_groups.values() for r in units[unit]]
        candidates = [r for r in candidates if r["content_hash"] not in {x["content_hash"] for x in selected}]
        picked = round_robin(candidates, target)
        if len(picked) < target:
            raise RuntimeError(f"matched selection cannot satisfy {unit} quota")
        selected.extend(picked)
    if len(selected) != limit or len({r["content_hash"] for r in selected}) != limit:
        raise RuntimeError("selection did not freeze exactly 500 unique content hashes")
    selected_non_safety: dict[tuple[str, str], dict[str, Any]] = {
        (r["state"], r["municipality"]): r for r in selected if r["unit_type"] == "non_safety"
    }
    output_rows: list[dict[str, str]] = []
    for rank, row in enumerate(sorted(selected, key=lambda r: (r["state"], r["municipality"], r["unit_type"], -r["_score"], r["content_hash"])), 1):
        review = row["_source"]
        g3 = row["_gate3"]
        case_id = stable_id("cex", TASK_ID, row["text_table_detection_id"])
        partner = selected_non_safety.get((row["state"], row["municipality"]))
        reasons = ["LOCAL_RETAINED_VERIFIED", "TEXT_LAYER_READABLE", "MATCHED_MUNICIPALITY"]
        if row["wage_table_signal"] == "likely": reasons.append("LIKELY_P1_PRIORITY")
        if g3: reasons.append("GATE3_CALIBRATION_CASE")
        if row["candidate_source_type"] != "cba": reasons.append("SOURCE_DIVERSITY")
        output_rows.append({
            "selection_rank": str(rank), "extraction_case_id": case_id,
            "document_identity_id": stable_id("doc", row["content_hash"]),
            "text_table_detection_id": row["text_table_detection_id"],
            "pdf_readiness_id": row["pdf_readiness_id"], "source_review_id": row["source_review_id"],
            "candidate_queue_row_id": row["candidate_queue_row_id"], "triage_id": row["triage_id"],
            "verification_id": row["verification_id"], "state": row["state"],
            "municipality": row["municipality"], "government_name": row["government_name"],
            "unit_type": row["unit_type"], "candidate_source_type": row["candidate_source_type"],
            "contract_period_start": review.get("contract_or_document_period_start", ""),
            "contract_period_end": review.get("contract_or_document_period_end", ""),
            "content_artifact_path": row["content_artifact_path"], "content_hash": row["content_hash"],
            "pdf_page_count": row["pdf_page_count"], "text_layer_status": row["text_layer_status"],
            "wage_table_signal": row["wage_table_signal"], "extraction_pilot_priority": row["extraction_pilot_priority"],
            "candidate_wage_pages": row["candidate_wage_pages"], "selection_score": f"{row['_score']:.3f}",
            "selection_reason_codes": "|".join(reasons),
            "matched_group_id": stable_id("match", row["state"], row["municipality"]),
            "matched_non_safety_selected": "yes",
            "matched_non_safety_case_id": stable_id("cex", TASK_ID, partner["text_table_detection_id"]) if partner else "",
            "planned_lane": "pending_packet_features",
            "gate3_category": g3.get("compensation_evidence_category", ""),
            "gate3_confidence": g3.get("gate3_confidence", ""),
            "existing_rendered_page_count": "0", "selection_status": "frozen",
        })
    write_csv(output / "compensation_extraction_500_selection_manifest.csv", SELECTION_FIELDS, output_rows)
    return output_rows


def render_lookup() -> dict[str, dict[int, str]]:
    if not BLINDED.is_file() or not RENDER_MANIFEST.is_file():
        return {}
    path_by_case = {r["adjudication_case_id"]: r["content_artifact_path"] for r in read_csv(BLINDED)}
    result: dict[str, dict[int, str]] = defaultdict(dict)
    for row in read_csv(RENDER_MANIFEST):
        path = path_by_case.get(row["adjudication_case_id"])
        image = Path(row["rendered_image_path"])
        if not image.is_absolute():
            image = RENDER_MANIFEST.parent / image
        if path and row["render_status"] == "rendered" and image.is_file():
            result[path][int(row["page_number"])] = str(image.resolve())
    return result


@dataclass
class PagePacket:
    page: int
    role: str
    text: str
    image: str
    wage: int
    numeric: int
    table: int
    qual: int
    nonbase: int
    reference: bool


def select_text(text: str, maximum: int) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    scored = sorted(enumerate(lines), key=lambda x: (-(4 * bool(WAGE_RE.search(x[1])) + 3 * bool(QUAL_RE.search(x[1])) + 2 * bool(NONBASE_RE.search(x[1])) + bool(NUM_RE.search(x[1]))), x[0]))
    chosen: list[tuple[int, str]] = []
    used = 0
    for index, line in scored:
        piece = line[:400]
        if used + len(piece) + 1 > maximum:
            continue
        chosen.append((index, piece)); used += len(piece) + 1
    return "\n".join(text for _, text in sorted(chosen))[:maximum]


def build_packet(row: dict[str, str], renders: dict[str, dict[int, str]]) -> list[PagePacket]:
    artifact = Path(row["content_artifact_path"])
    if not artifact.is_absolute(): artifact = ROOT / artifact
    with artifact.open("rb") as f:
        if f.read(5) != b"%PDF-": raise ValueError("invalid local PDF signature")
    reader = PdfReader(str(artifact))
    page_count = int(row["pdf_page_count"])
    candidates = parse_pages(row["candidate_wage_pages"], page_count)
    choices: list[tuple[int, str]] = []
    for page in candidates[:3]:
        choices.append((page, "candidate"))
        for nearby in (page - 1, page + 1):
            if 1 <= nearby <= page_count: choices.append((nearby, "nearby"))
    if not choices: choices.append((1, "fallback_front"))
    if 1 not in [p for p, _ in choices]: choices.append((1, "context_front"))
    unique: list[tuple[int, str]] = []
    for page, role in choices:
        if page not in [p for p, _ in unique] and len(unique) < 6: unique.append((page, role))
    packets: list[PagePacket] = []
    remaining = 6000
    for page, role in unique:
        maximum = min(1500, remaining)
        raw = reader.pages[page - 1].extract_text() or ""
        text = select_text(raw, maximum)
        remaining -= len(text)
        packets.append(PagePacket(
            page, role, text, renders.get(row["content_artifact_path"], {}).get(page, ""),
            len(WAGE_RE.findall(text)), len(NUM_RE.findall(text)),
            sum(bool(TABLE_RE.search(line)) for line in text.splitlines()),
            len(QUAL_RE.findall(text)), len(NONBASE_RE.findall(text)),
            bool(REFERENCE_RE.search(text)),
        ))
    return packets


def planned_lane(pages: list[PagePacket]) -> str:
    quant = sum(p.wage + p.numeric + 3 * p.table for p in pages)
    qual = sum(p.qual for p in pages)
    nonbase = sum(p.nonbase for p in pages)
    if quant >= 12 and qual >= 3: return "mixed"
    if quant >= 12: return "quantitative"
    if qual >= 3: return "qualitative"
    if nonbase >= 2: return "non_base_wage"
    return "reference_and_exclusion"


def freeze_packets(output: Path, rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, list[PagePacket]]]:
    renders = render_lookup()
    packet_rows: list[dict[str, str]] = []
    packet_map: dict[str, list[PagePacket]] = {}
    for row in rows:
        pages = build_packet(row, renders)
        packet_map[row["extraction_case_id"]] = pages
        row["planned_lane"] = planned_lane(pages)
        row["existing_rendered_page_count"] = str(sum(bool(p.image) for p in pages))
        total = sum(len(p.text) for p in pages)
        for page in pages:
            packet_rows.append({
                "extraction_case_id": row["extraction_case_id"], "document_identity_id": row["document_identity_id"],
                "text_table_detection_id": row["text_table_detection_id"], "page_number": str(page.page),
                "page_role": page.role, "bounded_evidence_pointer": f"{row['content_artifact_path']}#page={page.page}",
                "text_chars": str(len(page.text)), "wage_term_count": str(page.wage),
                "numeric_token_count": str(page.numeric), "table_like_line_count": str(page.table),
                "qualitative_mechanism_term_count": str(page.qual), "non_base_wage_term_count": str(page.nonbase),
                "reference_signal": "yes" if page.reference else "no",
                "rendered_image_available": "yes" if page.image else "no", "rendered_image_path": page.image,
                "packet_page_count": str(len(pages)), "packet_text_chars": str(total), "packet_status": "bounded_valid",
            })
    write_csv(output / "compensation_extraction_500_selection_manifest.csv", SELECTION_FIELDS, rows)
    write_csv(output / "compensation_extraction_500_packet_manifest.csv", PACKET_FIELDS, packet_rows)
    return packet_rows, packet_map


QUANT_OBS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["page_number", "compensation_type", "occupation_unit_classification_rank", "rate_value", "salary_value", "hourly_rate", "annual_salary", "pay_band", "step", "grade", "percentage_increase", "effective_date", "currency_or_unit", "confidence", "reason_code"],
    "properties": {
        "page_number": {"type": "integer"}, "compensation_type": {"type": "string", "enum": sorted(COMP_TYPES)},
        "occupation_unit_classification_rank": {"type": "string", "maxLength": 160},
        "rate_value": {"type": "string", "maxLength": 80},
        "salary_value": {"type": "string", "maxLength": 80},
        "hourly_rate": {"type": "string", "maxLength": 80},
        "annual_salary": {"type": "string", "maxLength": 80},
        "pay_band": {"type": "string", "maxLength": 80},
        "step": {"type": "string", "maxLength": 80},
        "grade": {"type": "string", "maxLength": 80},
        "percentage_increase": {"type": "string", "maxLength": 80},
        "effective_date": {"type": "string", "maxLength": 80},
        "currency_or_unit": {"type": "string", "maxLength": 80},
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
        "reason_code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{0,39}$"},
    },
}

QUAL_OBS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["page_number", "mechanism_type", "bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic", "step_progression_rule", "eligibility_rule", "implementation_rule", "fiscal_constraint", "reopener_clause", "differentiation_logic", "confidence", "reason_code"],
    "properties": {
        "page_number": {"type": "integer"}, "mechanism_type": {"type": "string", "enum": sorted(MECHANISM_TYPES)},
        **{field: {"type": "string", "maxLength": 240} for field in ("bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic", "step_progression_rule", "eligibility_rule", "implementation_rule", "fiscal_constraint", "reopener_clause", "differentiation_logic")},
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
        "reason_code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{0,39}$"},
    },
}

NONBASE_OBS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["page_number", "non_base_wage_type", "value_text", "effective_date", "eligibility_or_implementation_rule", "confidence", "reason_code"],
    "properties": {
        "page_number": {"type": "integer"}, "non_base_wage_type": {"type": "string", "enum": sorted(NONBASE_TYPES)},
        "value_text": {"type": "string", "maxLength": 120},
        "effective_date": {"type": "string", "maxLength": 80},
        "eligibility_or_implementation_rule": {"type": "string", "maxLength": 240},
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
        "reason_code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{0,39}$"},
    },
}

RESPONSE_KEYS = {"case_disposition", "page_relationship", "quantitative_observations", "qualitative_observations", "non_base_wage_observations", "confidence", "reason_codes", "short_rationale"}
RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": sorted(RESPONSE_KEYS),
    "properties": {
        "case_disposition": {"type": "string", "enum": sorted(DISPOSITIONS)},
        "page_relationship": {"type": "string", "enum": sorted(RELATIONSHIPS)},
        "quantitative_observations": {"type": "array", "maxItems": 5, "items": QUANT_OBS_SCHEMA},
        "qualitative_observations": {"type": "array", "maxItems": 5, "items": QUAL_OBS_SCHEMA},
        "non_base_wage_observations": {"type": "array", "maxItems": 5, "items": NONBASE_OBS_SCHEMA},
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
        "reason_codes": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{0,39}$"}},
        "short_rationale": {"type": "string", "minLength": 1, "maxLength": 300},
    },
}


def prompt(row: dict[str, str], pages: list[PagePacket]) -> str:
    packet = {
        "case": {k: row[k] for k in ("extraction_case_id", "state", "municipality", "government_name", "unit_type", "candidate_source_type", "contract_period_start", "contract_period_end")},
        "pages": [{"page_number": p.page, "page_role": p.role, "bounded_text": p.text, "local_features": {"wage_terms": p.wage, "numeric_tokens": p.numeric, "table_lines": p.table, "mechanism_terms": p.qual, "non_base_terms": p.nonbase, "reference_signal": p.reference}, "image_attached": bool(p.image)} for p in pages],
    }
    return (
        "Extract provisional compensation evidence only from this bounded local page packet. "
        "Return separate quantitative, qualitative-mechanism, and non-base-wage observation arrays. "
        "For mixed evidence populate both quantitative and qualitative arrays; never collapse them. "
        "Copy only the specific visible value tokens needed for structured fields; do not reproduce rows, tables, or long passages. "
        "Do not calculate, normalize, annualize, infer unseen values, or create final observations. Empty strings mean absent fields. "
        "The quantitative array is BASE WAGE ONLY. Overtime, premium or differential pay, leave, healthcare contributions, pension, stipends, bonuses, longevity, certification or education incentives, reimbursements, uniform or equipment allowances, benefits, and every other non-base component belong only in non_base_wage_observations. If base and non-base evidence coexist, create separate observations in their respective arrays. "
        "Do not use compensation_type=other as a dump bucket: it is permitted only for an explicit base-pay calculation or regular base-rate formula, with a specific reason code. "
        "A reference page without its target is reference_only. All page numbers must be among supplied pages. Summaries must be concise paraphrases, not quotations. Return strict JSON only.\n"
        f"BOUNDED_PACKET={json.dumps(packet, separators=(',', ':'))}"
    )


def validate_response(raw: str, allowed_pages: set[int]) -> dict[str, Any]:
    if len(raw) > 16_000:
        raise ValueError("response exceeds bounded structured-output cap")
    value = json.loads(raw.strip())
    if not isinstance(value, dict) or set(value) != RESPONSE_KEYS: raise ValueError("strict response keys mismatch")
    if value["case_disposition"] not in DISPOSITIONS or value["page_relationship"] not in RELATIONSHIPS or value["confidence"] not in CONFIDENCE: raise ValueError("invalid controlled response value")
    codes = value["reason_codes"]
    if not isinstance(codes, list) or not 1 <= len(codes) <= 8 or any(not isinstance(c, str) or not CODE_RE.fullmatch(c) for c in codes): raise ValueError("invalid reason_codes")
    if not isinstance(value["short_rationale"], str) or not 1 <= len(value["short_rationale"]) <= 300: raise ValueError("invalid rationale")
    for field, allowed_types in (("quantitative_observations", COMP_TYPES), ("qualitative_observations", MECHANISM_TYPES), ("non_base_wage_observations", NONBASE_TYPES)):
        obs = value[field]
        if not isinstance(obs, list) or len(obs) > 5: raise ValueError(f"invalid {field}")
        for item in obs:
            if not isinstance(item, dict) or item.get("page_number") not in allowed_pages or item.get("confidence") not in CONFIDENCE or not CODE_RE.fullmatch(str(item.get("reason_code", ""))): raise ValueError(f"invalid observation in {field}")
            schema = QUANT_OBS_SCHEMA if field.startswith("quant") else QUAL_OBS_SCHEMA if field.startswith("qual") else NONBASE_OBS_SCHEMA
            if set(item) != set(schema["required"]): raise ValueError(f"strict observation keys mismatch in {field}")
            for name, rule in schema["properties"].items():
                if rule.get("type") == "string" and (not isinstance(item[name], str) or len(item[name]) > rule.get("maxLength", 10_000)):
                    raise ValueError(f"invalid bounded string in {field}.{name}")
            type_field = "compensation_type" if field.startswith("quant") else "mechanism_type" if field.startswith("qual") else "non_base_wage_type"
            if item.get(type_field) not in allowed_types: raise ValueError(f"invalid {type_field}")
            if field == "quantitative_observations":
                if targeted_nonbase_type({k: str(v) for k, v in item.items()}):
                    raise ValueError("non-base compensation is in quantitative array")
                if item["compensation_type"] == "other":
                    diagnostic = " ".join(str(v) for v in item.values()).replace("_", " ")
                    if not re.search(r"\b(base|regular rate|wage formula|salary calculation|basic rate)\b", diagnostic, re.I):
                        raise ValueError("quantitative other lacks explicit base-pay reason")
    if value["case_disposition"] == "quantitative_ready" and not value["quantitative_observations"]: raise ValueError("quantitative disposition without observation")
    if value["case_disposition"] == "qualitative_ready" and not value["qualitative_observations"]: raise ValueError("qualitative disposition without observation")
    if value["case_disposition"] == "mixed_ready" and (not value["quantitative_observations"] or not value["qualitative_observations"]): raise ValueError("mixed disposition missing sub-records")
    if value["case_disposition"] == "non_base_wage" and not value["non_base_wage_observations"]: raise ValueError("non-base disposition without observation")
    return value


@dataclass
class Request:
    row: dict[str, str]
    pages: list[PagePacket]
    phase: str


@dataclass
class Result:
    case_id: str
    status: str
    request_id: str
    raw: str
    parsed: dict[str, Any] | None
    elapsed: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error_type: str
    error_message: str
    prompt_hash: str
    prompt_chars: int
    image_count: int
    image_bytes: int


def load_key() -> str | None:
    from dotenv import dotenv_values, load_dotenv
    env = ROOT / ".env"
    values = dotenv_values(env) if env.is_file() else {}
    if env.is_file(): load_dotenv(env, override=False)
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY") or values.get("HARVARD_SUBSCRIPTION_KEY")
    return str(key) if key else None


def safe_error(exc: Exception, key: str) -> str:
    text = str(exc).replace(key, "[REDACTED]")
    return re.sub(r"(?i)(authorization|api[-_ ]?key|token|cookie)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)[:240]


async def _call(requests: list[Request], key: str, parallel: int, timeout: float) -> list[Result]:
    import httpx
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=key, base_url=BASE_URL, default_headers={"Ocp-Apim-Subscription-Key": key}, timeout=httpx.Timeout(timeout), max_retries=0)
    semaphore = asyncio.Semaphore(parallel)
    async def one(req: Request) -> Result:
        started = time.monotonic(); text_prompt = prompt(req.row, req.pages)
        async with semaphore:
            try:
                content: list[dict[str, str]] = [{"type": "input_text", "text": text_prompt}]
                image_bytes = 0; image_count = 0
                for page in req.pages:
                    if not page.image or image_count >= 6: continue
                    path = Path(page.image); data = path.read_bytes()
                    if image_bytes + len(data) > 2_000_000: continue
                    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
                    content.append({"type": "input_image", "image_url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}", "detail": "low"})
                    image_bytes += len(data); image_count += 1
                response = await asyncio.wait_for(client.responses.create(model=MODEL, input=[{"role": "user", "content": content}], reasoning={"effort": "low"}, text={"format": {"type": "json_schema", "name": "bounded_compensation_extraction", "strict": True, "schema": RESPONSE_SCHEMA}}), timeout=timeout)
                raw = str(getattr(response, "output_text", "") or ""); usage = getattr(response, "usage", None)
                try: parsed = validate_response(raw, {p.page for p in req.pages}); status = "success"; et = ""; em = ""
                except Exception as exc: parsed = None; status = "schema_invalid"; et = type(exc).__name__; em = safe_error(exc, key)
                return Result(req.row["extraction_case_id"], status, str(getattr(response, "id", "") or ""), raw, parsed, time.monotonic()-started, int(getattr(usage, "input_tokens", 0) or 0), int(getattr(usage, "output_tokens", 0) or 0), int(getattr(usage, "total_tokens", 0) or 0), et, em, sha_bytes(text_prompt.encode()), len(text_prompt), image_count, image_bytes)
            except Exception as exc:
                return Result(req.row["extraction_case_id"], "request_failed", "", "", None, time.monotonic()-started, 0, 0, 0, type(exc).__name__, safe_error(exc, key), sha_bytes(text_prompt.encode()), len(text_prompt), 0, 0)
    try: return list(await asyncio.gather(*(one(r) for r in requests)))
    finally: await client.close()


def call_gabriel(requests: list[Request], key: str, parallel: int = 2, timeout: float = 90) -> list[Result]:
    return asyncio.run(_call(requests, key, parallel, timeout))


def result_metadata(result: Result, req: Request) -> dict[str, Any]:
    return {
        "request_phase": req.phase, "extraction_case_id": result.case_id, "gabriel_request_id": result.request_id,
        "gabriel_backend": BACKEND, "gabriel_model": MODEL, "request_status": result.status,
        "schema_valid": "true" if result.status == "success" else "false", "prompt_sha256": result.prompt_hash,
        "prompt_chars": result.prompt_chars, "input_page_count": len(req.pages), "input_text_chars": sum(len(p.text) for p in req.pages),
        "input_image_count": result.image_count, "input_image_bytes": result.image_bytes, "raw_prompt_saved": "false",
        "raw_response_saved": "false", "encoded_image_saved": "false", "response_sha256": sha_bytes(result.raw.encode()) if result.raw else "",
        "response_chars": len(result.raw), "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens, "elapsed_seconds": f"{result.elapsed:.6f}", "error_type": result.error_type,
        "error_message": result.error_message, "credential_value_saved": "false", "authorization_header_saved": "false",
    }


def identity(row: dict[str, str]) -> dict[str, str]:
    return {k: row[k] for k in ("extraction_case_id", "document_identity_id", "text_table_detection_id", "source_review_id", "candidate_queue_row_id", "state", "municipality", "government_name", "unit_type", "candidate_source_type", "contract_period_start", "contract_period_end")}


def materialize_lanes(output: Path, selection: list[dict[str, str]], results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    quant: list[dict[str, str]] = []; qual: list[dict[str, str]] = []; mixed: list[dict[str, str]] = []; nonbase: list[dict[str, str]] = []; refs: list[dict[str, str]] = []
    selection_by_id = {r["extraction_case_id"]: r for r in selection}
    for case_id in [r["extraction_case_id"] for r in selection]:
        row = selection_by_id[case_id]; value = results[case_id]; join = stable_id("mix", case_id)
        qids: list[str] = []; lids: list[str] = []
        for index, obs in enumerate(value["quantitative_observations"], 1):
            oid = stable_id("qobs", case_id, str(index)); qids.append(oid)
            quant.append({**identity(row), "quantitative_observation_id": oid, "mixed_join_key": join if value["case_disposition"] == "mixed_ready" else "", **{k: str(obs[k]) for k in ("page_number", "compensation_type", "occupation_unit_classification_rank", "rate_value", "salary_value", "hourly_rate", "annual_salary", "pay_band", "step", "grade", "percentage_increase", "effective_date", "currency_or_unit", "confidence", "reason_code")}, "bounded_evidence_pointer": f"{row['content_artifact_path']}#page={obs['page_number']}", "qa_status": "provisional_unverified" if obs["confidence"] in {"high", "medium"} else "needs_review"})
        for index, obs in enumerate(value["qualitative_observations"], 1):
            oid = stable_id("lobs", case_id, str(index)); lids.append(oid)
            qual.append({**identity(row), "qualitative_observation_id": oid, "mixed_join_key": join if value["case_disposition"] == "mixed_ready" else "", **{k: str(obs[k]) for k in ("page_number", "mechanism_type", "bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic", "step_progression_rule", "eligibility_rule", "implementation_rule", "fiscal_constraint", "reopener_clause", "differentiation_logic", "confidence", "reason_code")}, "bounded_evidence_pointer": f"{row['content_artifact_path']}#page={obs['page_number']}", "qa_status": "provisional_unverified" if obs["confidence"] in {"high", "medium"} else "needs_review"})
        for index, obs in enumerate(value["non_base_wage_observations"], 1):
            oid = stable_id("nobs", case_id, str(index))
            nonbase.append({**identity(row), "non_base_wage_observation_id": oid, **{k: str(obs[k]) for k in ("page_number", "non_base_wage_type", "value_text", "effective_date", "eligibility_or_implementation_rule", "confidence", "reason_code")}, "bounded_evidence_pointer": f"{row['content_artifact_path']}#page={obs['page_number']}", "qa_status": "provisional_unverified" if obs["confidence"] in {"high", "medium"} else "needs_review"})
        if value["case_disposition"] == "mixed_ready":
            mixed.append({**{k: row[k] for k in ("extraction_case_id", "document_identity_id", "text_table_detection_id", "source_review_id", "candidate_queue_row_id", "state", "municipality", "government_name", "unit_type", "candidate_source_type")}, "mixed_join_key": join, "quantitative_observation_ids": "|".join(qids), "qualitative_observation_ids": "|".join(lids), "quantitative_observation_count": str(len(qids)), "qualitative_observation_count": str(len(lids)), "confidence": value["confidence"], "reason_codes": "|".join(value["reason_codes"]), "qa_status": "provisional_unverified" if value["confidence"] in {"high", "medium"} else "needs_review"})
        if value["case_disposition"] in {"reference_only", "exclude", "second_review"}:
            pointers = "|".join(f"{row['content_artifact_path']}#page={p}" for p in parse_pages(row["candidate_wage_pages"], int(row["pdf_page_count"])))
            refs.append({**{k: row[k] for k in ("extraction_case_id", "document_identity_id", "text_table_detection_id", "source_review_id", "candidate_queue_row_id", "state", "municipality", "government_name", "unit_type", "candidate_source_type")}, "disposition": value["case_disposition"], "page_relationship": value["page_relationship"], "bounded_evidence_pointer": pointers, "confidence": value["confidence"], "reason_codes": "|".join(value["reason_codes"]), "short_rationale": value["short_rationale"], "qa_status": "excluded_provisional" if value["case_disposition"] == "exclude" else "needs_review"})
    paths = {
        "quant": output / "lanes/quantitative/quantitative_extraction_ledger.csv",
        "qual": output / "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv",
        "mixed": output / "lanes/mixed/mixed_extraction_ledger.csv",
        "nonbase": output / "lanes/non_base_wage/non_base_wage_compensation_ledger.csv",
        "refs": output / "lanes/reference_and_exclusion/reference_exclusion_ledger.csv",
    }
    for key, fields, rows in (("quant", QUANT_FIELDS, quant), ("qual", QUAL_FIELDS, qual), ("mixed", MIXED_FIELDS, mixed), ("nonbase", NONBASE_FIELDS, nonbase), ("refs", REFERENCE_FIELDS, refs)): write_csv(paths[key], fields, rows)
    summaries = {
        "quantitative": {"observation_count": len(quant), "case_count": len({r["extraction_case_id"] for r in quant}), "confidence_counts": dict(Counter(r["confidence"] for r in quant))},
        "qualitative": {"observation_count": len(qual), "case_count": len({r["extraction_case_id"] for r in qual}), "confidence_counts": dict(Counter(r["confidence"] for r in qual))},
        "mixed": {"case_count": len(mixed), "quantitative_subrecord_count": sum(int(r["quantitative_observation_count"]) for r in mixed), "qualitative_subrecord_count": sum(int(r["qualitative_observation_count"]) for r in mixed)},
        "non_base_wage": {"observation_count": len(nonbase), "case_count": len({r["extraction_case_id"] for r in nonbase}), "type_counts": dict(Counter(r["non_base_wage_type"] for r in nonbase))},
        "reference_and_exclusion": {"case_count": len(refs), "disposition_counts": dict(Counter(r["disposition"] for r in refs))},
    }
    write_json(output / "lanes/quantitative/quantitative_extraction_summary.json", summaries["quantitative"])
    write_json(output / "lanes/qualitative/qualitative_mechanism_extraction_summary.json", summaries["qualitative"])
    write_json(output / "lanes/mixed/mixed_extraction_summary.json", summaries["mixed"])
    write_json(output / "lanes/non_base_wage/non_base_wage_compensation_summary.json", summaries["non_base_wage"])
    write_json(output / "lanes/reference_and_exclusion/reference_exclusion_summary.json", summaries["reference_and_exclusion"])
    return {"summaries": summaries, "rows": {"quant": quant, "qual": qual, "mixed": mixed, "nonbase": nonbase, "refs": refs}}


def qa_and_decision(output: Path, selection: list[dict[str, str]], packet_rows: list[dict[str, str]], results: dict[str, dict[str, Any]], lanes: dict[str, Any]) -> dict[str, Any]:
    pages_by_case: dict[str, set[int]] = defaultdict(set)
    for row in packet_rows: pages_by_case[row["extraction_case_id"]].add(int(row["page_number"]))
    observation_rows = lanes["rows"]["quant"] + lanes["rows"]["qual"] + lanes["rows"]["nonbase"]
    invalid_pages = sum(int(r["page_number"]) not in pages_by_case[r["extraction_case_id"]] for r in observation_rows)
    ids = [r.get("quantitative_observation_id") or r.get("qualitative_observation_id") or r.get("non_base_wage_observation_id") for r in observation_rows]
    duplicate_obs = len(ids) - len(set(ids))
    duplicate_review: list[dict[str, str]] = []
    duplicate_counts: dict[str, int] = {}
    lane_specs = (
        ("quantitative", lanes["rows"]["quant"], "quantitative_observation_id", tuple(field for field in QUANT_FIELDS if field not in {"quantitative_observation_id", "qa_status"})),
        ("qualitative", lanes["rows"]["qual"], "qualitative_observation_id", tuple(field for field in QUAL_FIELDS if field not in {"qualitative_observation_id", "qa_status"})),
        ("non_base_wage", lanes["rows"]["nonbase"], "non_base_wage_observation_id", tuple(field for field in NONBASE_FIELDS if field not in {"non_base_wage_observation_id", "qa_status"})),
    )
    for lane_name, rows, id_field, canonical_fields in lane_specs:
        groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row[field] for field in canonical_fields)].append(row)
        duplicates = [values for values in groups.values() if len(values) > 1]
        duplicate_counts[lane_name] = sum(len(values) - 1 for values in duplicates)
        for values in duplicates:
            for row in values: row["qa_status"] = "needs_duplicate_review"
            duplicate_review.append({
                "review_type": "exact_content_duplicate", "extraction_case_id": values[0]["extraction_case_id"],
                "page_number": values[0]["page_number"], "lane": lane_name,
                "observation_ids": "|".join(row[id_field] for row in values),
                "observation_count": str(len(values)), "qa_reason": "EXACT_STRUCTURED_CONTENT_REPEATED",
            })
    conflict_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for r in lanes["rows"]["quant"]:
        key = tuple(r[k] for k in (
            "extraction_case_id", "page_number", "compensation_type",
            "occupation_unit_classification_rank", "pay_band", "step", "grade",
            "effective_date", "currency_or_unit",
        ))
        conflict_groups[key].append(r)
    conflicts: list[list[dict[str, str]]] = []
    for rows in conflict_groups.values():
        signatures = {tuple(r[k] for k in ("rate_value", "salary_value", "hourly_rate", "annual_salary", "percentage_increase")) for r in rows}
        if len(signatures) > 1: conflicts.append(rows)
    conflict_review: list[dict[str, str]] = []
    for rows in conflicts:
        for row in rows: row["qa_status"] = "needs_conflict_review"
        conflict_review.append({
            "review_type": "potential_quantitative_conflict", "extraction_case_id": rows[0]["extraction_case_id"],
            "page_number": rows[0]["page_number"], "lane": "quantitative",
            "observation_ids": "|".join(row["quantitative_observation_id"] for row in rows),
            "observation_count": str(len(rows)), "qa_reason": "SAME_EVIDENCE_KEY_DIFFERENT_VALUES",
        })
    nonbase_quant_rows: list[dict[str, str]] = []
    for row in lanes["rows"]["quant"]:
        diagnostic = " ".join(row[k] for k in (
            "compensation_type", "occupation_unit_classification_rank", "rate_value",
            "salary_value", "hourly_rate", "annual_salary", "pay_band",
            "percentage_increase", "currency_or_unit", "reason_code",
        ))
        if NONBASE_RE.search(diagnostic):
            row["qa_status"] = "needs_non_base_wage_review"
            nonbase_quant_rows.append(row)
            conflict_review.append({
                "review_type": "possible_non_base_wage_in_quantitative_lane",
                "extraction_case_id": row["extraction_case_id"], "page_number": row["page_number"],
                "lane": "quantitative", "observation_ids": row["quantitative_observation_id"],
                "observation_count": "1", "qa_reason": "NON_BASE_WAGE_TERM_IN_QUANT_RECORD",
            })
    write_csv(
        output / "lanes/quantitative/quantitative_extraction_ledger.csv",
        QUANT_FIELDS, lanes["rows"]["quant"],
    )
    write_csv(
        output / "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv",
        QUAL_FIELDS, lanes["rows"]["qual"],
    )
    write_csv(
        output / "lanes/non_base_wage/non_base_wage_compensation_ledger.csv",
        NONBASE_FIELDS, lanes["rows"]["nonbase"],
    )
    write_csv(
        output / "compensation_extraction_500_conflict_review.csv",
        CONFLICT_REVIEW_FIELDS, duplicate_review + conflict_review,
    )
    disposition_counts = dict(Counter(v["case_disposition"] for v in results.values()))
    evidence_cases = sum(v in {"quantitative_ready", "qualitative_ready", "mixed_ready", "non_base_wage"} for v in (x["case_disposition"] for x in results.values()))
    packet_compliant = len(packet_rows) <= 3000 and all(int(r["packet_page_count"]) <= 6 and int(r["packet_text_chars"]) <= 6000 and int(r["text_chars"]) <= 1500 for r in packet_rows)
    qa_pass = len(selection) == 500 and len(results) == 500 and packet_compliant and invalid_pages == 0 and duplicate_obs == 0
    conflict_count = len(conflicts)
    conflict_rate = conflict_count / max(1, len(lanes["rows"]["quant"]))
    scale_qa_pass = (
        qa_pass and evidence_cases >= 350 and conflict_rate <= 0.02
        and not nonbase_quant_rows and sum(duplicate_counts.values()) == 0
        and disposition_counts.get("second_review", 0) <= 25
    )
    scale = "recommend_1000_document_extraction" if scale_qa_pass else "premature_pending_targeted_qa" if qa_pass else "blocked_by_qa_failure"
    qa = {
        "qa_pass": qa_pass, "integrity_qa_pass": qa_pass,
        "scale_qa_pass": scale_qa_pass,
        "qa_status": "pass" if scale_qa_pass else "integrity_pass_scale_hold" if qa_pass else "fail",
        "selection_count": len(selection), "result_count": len(results),
        "packet_compliant": packet_compliant, "packet_rows": len(packet_rows), "invalid_observation_page_count": invalid_pages,
        "duplicate_observation_id_count": duplicate_obs,
        "duplicate_structured_content_counts": duplicate_counts,
        "conflicting_quantitative_group_count": conflict_count,
        "quantitative_records_flagged_possible_non_base_wage": len(nonbase_quant_rows),
        "conflict_review_row_count": len(duplicate_review) + len(conflict_review),
        "conflict_rate": round(conflict_rate, 6), "disposition_counts": disposition_counts,
        "evidence_bearing_case_count": evidence_cases, "scale_1000_recommendation": scale,
    }
    report = f"""# Provisional 500-document extraction QA report

- Integrity QA pass: `{str(qa_pass).lower()}`
- Scale QA pass: `{str(scale_qa_pass).lower()}`
- QA status: `{qa['qa_status']}`
- Frozen unique cases: {len(selection)}
- Successful structured results: {len(results)}
- Packet compliance: `{str(packet_compliant).lower()}`
- Invalid observation pages: {invalid_pages}
- Duplicate observation IDs: {duplicate_obs}
- Exact structured-content duplicates: {sum(duplicate_counts.values())}
- Potential quantitative conflict groups: {conflict_count}
- Quantitative records flagged as possible non-base wage: {len(nonbase_quant_rows)}
- Evidence-bearing cases: {evidence_cases}
- Dispositions: `{json.dumps(disposition_counts, sort_keys=True)}`
- 1,000-document recommendation: `{scale}`

This is a provisional extraction QA gate. No final merge, ingestion,
codification, wage-gap analysis, or regression occurred.
"""
    (output / "compensation_extraction_500_qa_report.md").write_text(report, encoding="utf-8")
    decision = {**qa, "task_id": TASK_ID, "decision": scale, "generated_at": now(), "final_merge_allowed": False, "ingestion_allowed": False}
    write_json(output / "compensation_extraction_500_decision_report.json", decision)
    return decision


def write_freeze_outputs(output: Path, selection: list[dict[str, str]], packet_rows: list[dict[str, str]], gate3_path: Path) -> None:
    manifest = output / "compensation_extraction_500_selection_manifest.csv"
    digest = sha_file(manifest)
    (output / "compensation_extraction_500_selection_sha256.txt").write_text(f"{digest}  {manifest.name}\n", encoding="utf-8")
    summary = {
        "task_id": TASK_ID, "status": "frozen_no_gabriel_calls", "selection_count": len(selection),
        "unique_document_identity_count": len({r["document_identity_id"] for r in selection}),
        "unique_content_hash_count": len({r["content_hash"] for r in selection}),
        "unit_type_counts": dict(Counter(r["unit_type"] for r in selection)),
        "source_type_counts": dict(Counter(r["candidate_source_type"] for r in selection)),
        "state_counts": dict(Counter(r["state"] for r in selection)),
        "wage_signal_counts": dict(Counter(r["wage_table_signal"] for r in selection)),
        "planned_lane_counts": dict(Counter(r["planned_lane"] for r in selection)),
        "matched_non_safety_selected_count": sum(r["matched_non_safety_selected"] == "yes" for r in selection),
        "manifest_sha256": digest, "gate3_input_sha256": sha_file(gate3_path), "gabriel_calls": 0,
    }
    write_json(output / "compensation_extraction_500_selection_summary.json", summary)
    packet_summary = {
        "case_count": len({r["extraction_case_id"] for r in packet_rows}), "packet_page_rows": len(packet_rows),
        "max_pages_per_case": max(int(r["packet_page_count"]) for r in packet_rows),
        "max_text_chars_per_page": max(int(r["text_chars"]) for r in packet_rows),
        "max_text_chars_per_case": max(int(r["packet_text_chars"]) for r in packet_rows),
        "rendered_page_available_count": sum(r["rendered_image_available"] == "yes" for r in packet_rows),
        "cases_with_rendered_pages": len({r["extraction_case_id"] for r in packet_rows if r["rendered_image_available"] == "yes"}),
        "full_text_saved": False, "full_tables_saved": False, "raw_prompts_saved": False, "raw_responses_saved": False,
    }
    write_json(output / "compensation_extraction_500_packet_summary.json", packet_summary)
    audit = f"""# Frozen 500-document selection audit

- Exact unique document identities: {summary['unique_document_identity_count']}
- Unit counts: `{json.dumps(summary['unit_type_counts'], sort_keys=True)}`
- Source counts: `{json.dumps(summary['source_type_counts'], sort_keys=True)}`
- States/DC represented: {len(summary['state_counts'])}
- Planned lanes: `{json.dumps(summary['planned_lane_counts'], sort_keys=True)}`
- Safety rows with a selected same-municipality non-safety opportunity: all.
- Packet pages: {packet_summary['packet_page_rows']}; maximum six per case.
- Text caps: 1,500 per page and 6,000 per case.
- Selection SHA-256: `{digest}`

The freeze made zero GABRIEL/API calls. It used only local retained, hash-
verified, PDF-signature-valid, OCR-free artifacts. No full text/table or page
snippet was saved in the manifests.
"""
    (output / "compensation_extraction_500_selection_audit.md").write_text(audit, encoding="utf-8")


def load_selection(output: Path) -> list[dict[str, str]]:
    path = output / "compensation_extraction_500_selection_manifest.csv"
    rows = read_csv(path)
    digest_line = (output / "compensation_extraction_500_selection_sha256.txt").read_text().split()[0]
    if len(rows) != 500 or len({r["document_identity_id"] for r in rows}) != 500 or sha_file(path) != digest_line: raise RuntimeError("frozen selection integrity failure")
    return rows


def packet_rows_and_map(output: Path, selection: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, list[PagePacket]]]:
    existing = read_csv(output / "compensation_extraction_500_packet_manifest.csv")
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in existing: by_case[r["extraction_case_id"]].append(r)
    renders = render_lookup(); packet_map: dict[str, list[PagePacket]] = {}
    for row in selection:
        pages = build_packet(row, renders)
        expected = {(int(r["page_number"]), r["text_chars"]) for r in by_case[row["extraction_case_id"]]}
        if {(p.page, str(len(p.text))) for p in pages} != expected: raise RuntimeError("packet reconstruction differs from frozen manifest")
        packet_map[row["extraction_case_id"]] = pages
    return existing, packet_map


def preflight(output: Path, selection: list[dict[str, str]], packet_map: dict[str, list[PagePacket]], key: str) -> int:
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selection: by_lane[row["planned_lane"]].append(row)
    wanted = ["quantitative", "qualitative", "mixed"]
    fourth = "non_base_wage" if by_lane["non_base_wage"] else "reference_and_exclusion"
    chosen = [by_lane[lane][0] for lane in wanted + [fourth] if by_lane[lane]]
    if len(chosen) < 4: raise RuntimeError("representative preflight paths unavailable")
    requests = [Request(r, packet_map[r["extraction_case_id"]], "preflight") for r in chosen]
    results = call_gabriel(requests, key, parallel=1)
    metadata = [result_metadata(result, req) for result, req in zip(results, requests)]
    write_csv(output / "compensation_extraction_request_metadata.csv", METADATA_FIELDS, metadata)
    timing = [{"request_phase": "preflight", "extraction_case_id": result.case_id, "started_at": "", "finished_at": now(), "local_packet_seconds": "0.000000", "gabriel_elapsed_seconds": f"{result.elapsed:.6f}", "request_status": result.status} for result in results]
    write_csv(output / "compensation_extraction_timing.csv", TIMING_FIELDS, timing)
    passed = len(results) == 4 and all(r.status == "success" for r in results)
    report = "# Compensation extraction preflight\n\n" + "\n".join(f"- `{r.case_id}`: `{r.status}`" for r in results) + f"\n\nOverall: `{'pass' if passed else 'fail'}`.\n"
    (output / "compensation_extraction_preflight_report.md").write_text(report, encoding="utf-8")
    write_json(output / ".preflight_passed.json", {"passed": passed, "case_count": len(results), "schema_valid_count": sum(r.status == "success" for r in results), "completed_at": now()})
    return 0 if passed else 2


def live(output: Path, selection: list[dict[str, str]], packet_rows: list[dict[str, str]], packet_map: dict[str, list[PagePacket]], key: str, resume: bool) -> int:
    marker = read_json(output / ".preflight_passed.json")
    if marker.get("passed") is not True: raise RuntimeError("live lanes require successful preflight")
    checkpoint = output / "compensation_extraction_case_results.jsonl"
    stored: dict[str, dict[str, Any]] = {}
    if resume and checkpoint.is_file():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            item = json.loads(line); stored[item["extraction_case_id"]] = item["result"]
    metadata = read_csv(output / "compensation_extraction_request_metadata.csv") if (output / "compensation_extraction_request_metadata.csv").is_file() else []
    timing = read_csv(output / "compensation_extraction_timing.csv") if (output / "compensation_extraction_timing.csv").is_file() else []
    pending = [r for r in selection if r["extraction_case_id"] not in stored]
    for start in range(0, len(pending), 25):
        batch_rows = pending[start:start+25]; requests = [Request(r, packet_map[r["extraction_case_id"]], "live") for r in batch_rows]
        results = call_gabriel(requests, key, parallel=2)
        for result, req in zip(results, requests):
            metadata.append(result_metadata(result, req)); timing.append({"request_phase": "live", "extraction_case_id": result.case_id, "started_at": "", "finished_at": now(), "local_packet_seconds": "0.000000", "gabriel_elapsed_seconds": f"{result.elapsed:.6f}", "request_status": result.status})
            if result.status == "success" and result.parsed is not None: stored[result.case_id] = result.parsed
        checkpoint.write_text("\n".join(json.dumps({"extraction_case_id": k, "result": stored[k]}, sort_keys=True) for k in sorted(stored)) + ("\n" if stored else ""), encoding="utf-8")
        write_csv(output / "compensation_extraction_request_metadata.csv", METADATA_FIELDS, metadata)
        write_csv(output / "compensation_extraction_timing.csv", TIMING_FIELDS, timing)
        print(json.dumps({
            "phase": "live_lanes",
            "attempted": min(start + len(batch_rows), len(pending)),
            "pending_at_start": len(pending),
            "schema_valid_results_stored": len(stored),
            "batch_success": sum(result.status == "success" for result in results),
            "batch_failed": sum(result.status != "success" for result in results),
        }, sort_keys=True), flush=True)
    if len(stored) != 500:
        return 2
    lanes = materialize_lanes(output, selection, stored)
    decision = qa_and_decision(output, selection, packet_rows, stored, lanes)
    return 0 if decision["qa_pass"] else 2


def freeze_selection_1000(
    gate3_path: Path, targeted_qa_dir: Path, output: Path, limit: int
) -> list[dict[str, str]]:
    if limit != 1000:
        raise ValueError("cumulative scale requires exactly 1,000 cases")
    decision_path = targeted_qa_dir / "compensation_extraction_500_recomputed_decision.json"
    decision = read_json(decision_path)
    if not (
        decision.get("scale_1000_allowed") is True
        and decision.get("decision") == "recommend_1000_document_extraction"
        and decision.get("integrity_qa_pass") is True
        and decision.get("unresolved_base_non_base_contamination_count") == 0
    ):
        raise RuntimeError("targeted-QA authority does not permit 1,000-document scale")
    seed_path = EXTRACTION_500_DIR / "compensation_extraction_500_selection_manifest.csv"
    seed = read_csv(seed_path)
    if len(seed) != 500 or len({row["document_identity_id"] for row in seed}) != 500:
        raise RuntimeError("corrected 500-document seed selection is invalid")
    seed_hashes = {row["content_hash"] for row in seed}
    eligible, _ = load_inputs(gate3_path)
    available = [row for row in eligible if row["content_hash"] not in seed_hashes]

    groups: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in available:
        groups[(row["state"], row["municipality"])][row["unit_type"]].append(row)
    matched = {
        key: units
        for key, units in groups.items()
        if units["non_safety"] and (units["police"] or units["fire"])
    }
    group_rows: list[dict[str, Any]] = []
    for (state, municipality), units in matched.items():
        group_rows.append(
            {
                "state": state,
                "municipality": municipality,
                "_score": max(
                    row["_score"] for values in units.values() for row in values
                )
                + 2 * (len(units["police"]) + len(units["fire"])),
                "_units": units,
            }
        )
    fire_groups = [row for row in group_rows if row["_units"]["fire"]]
    other_groups = [row for row in group_rows if not row["_units"]["fire"]]
    if len(fire_groups) > 200:
        fire_groups = round_robin(fire_groups, 200)
    selected_groups = round_robin(fire_groups, len(fire_groups))
    selected_groups += round_robin(other_groups, 200 - len(selected_groups))
    if len(selected_groups) != 200:
        raise RuntimeError("new matched non-safety group quota cannot be satisfied")

    new_selected: list[dict[str, Any]] = []
    for group in selected_groups:
        new_selected.append(
            sorted(
                group["_units"]["non_safety"],
                key=lambda row: (-row["_score"], row["content_hash"]),
            )[0]
        )
    seed_non_safety_groups = {
        (row["state"], row["municipality"])
        for row in seed
        if row["unit_type"] == "non_safety"
    }
    cumulative_partner_groups = seed_non_safety_groups | {
        (row["state"], row["municipality"]) for row in new_selected
    }
    safety_candidates = {
        unit: [
            row
            for row in available
            if row["unit_type"] == unit
            and (row["state"], row["municipality"]) in cumulative_partner_groups
        ]
        for unit in ("police", "fire")
    }
    additive_targets = {"police": 183, "fire": 117}
    for unit, target in additive_targets.items():
        picked = round_robin(safety_candidates[unit], target)
        if len(picked) != target:
            raise RuntimeError(f"cumulative matched selection cannot satisfy {unit} quota")
        new_selected.extend(picked)
    if len(new_selected) != 500 or len({row["content_hash"] for row in new_selected}) != 500:
        raise RuntimeError("additive selection did not freeze 500 unique new hashes")

    seed_rows: list[dict[str, str]] = []
    for row in seed:
        copied = {field: row.get(field, "") for field in SELECTION_FIELDS}
        copied.update(
            {
                "cumulative_cohort": "corrected_500_seed",
                "requires_gabriel": "no",
                "seed_selection_rank": row["selection_rank"],
                "selection_status": "frozen_seed_reused_no_api",
            }
        )
        seed_rows.append(copied)

    new_case_ids = {
        row["content_hash"]: stable_id(
            "cex1000", TASK_1000_ID, row["text_table_detection_id"]
        )
        for row in new_selected
    }
    partner_by_group: dict[tuple[str, str], str] = {
        (row["state"], row["municipality"]): row["extraction_case_id"]
        for row in seed_rows
        if row["unit_type"] == "non_safety"
    }
    for row in new_selected:
        if row["unit_type"] == "non_safety":
            partner_by_group[(row["state"], row["municipality"])] = new_case_ids[
                row["content_hash"]
            ]

    new_rows: list[dict[str, str]] = []
    ordered_new = sorted(
        new_selected,
        key=lambda row: (
            row["state"],
            row["municipality"],
            row["unit_type"],
            -row["_score"],
            row["content_hash"],
        ),
    )
    for rank, row in enumerate(ordered_new, 501):
        review = row["_source"]
        g3 = row["_gate3"]
        group = (row["state"], row["municipality"])
        reasons = [
            "LOCAL_RETAINED_VERIFIED",
            "TEXT_LAYER_READABLE",
            "CUMULATIVE_MATCHED_MUNICIPALITY",
            "TARGETED_QA_ROUTING_V1",
            "ADDITIVE_500_NEW",
        ]
        if row["wage_table_signal"] == "likely":
            reasons.append("LIKELY_P1_PRIORITY")
        if row["candidate_source_type"] != "cba":
            reasons.append("SOURCE_DIVERSITY")
        new_rows.append(
            {
                "selection_rank": str(rank),
                "extraction_case_id": new_case_ids[row["content_hash"]],
                "document_identity_id": stable_id("doc", row["content_hash"]),
                "text_table_detection_id": row["text_table_detection_id"],
                "pdf_readiness_id": row["pdf_readiness_id"],
                "source_review_id": row["source_review_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "triage_id": row["triage_id"],
                "verification_id": row["verification_id"],
                "state": row["state"],
                "municipality": row["municipality"],
                "government_name": row["government_name"],
                "unit_type": row["unit_type"],
                "candidate_source_type": row["candidate_source_type"],
                "contract_period_start": review.get(
                    "contract_or_document_period_start", ""
                ),
                "contract_period_end": review.get(
                    "contract_or_document_period_end", ""
                ),
                "content_artifact_path": row["content_artifact_path"],
                "content_hash": row["content_hash"],
                "pdf_page_count": row["pdf_page_count"],
                "text_layer_status": row["text_layer_status"],
                "wage_table_signal": row["wage_table_signal"],
                "extraction_pilot_priority": row["extraction_pilot_priority"],
                "candidate_wage_pages": row["candidate_wage_pages"],
                "selection_score": f"{row['_score']:.3f}",
                "selection_reason_codes": "|".join(reasons),
                "matched_group_id": stable_id(
                    "match", row["state"], row["municipality"]
                ),
                "matched_non_safety_selected": "yes",
                "matched_non_safety_case_id": partner_by_group.get(group, ""),
                "planned_lane": "pending_packet_features",
                "gate3_category": g3.get("compensation_evidence_category", ""),
                "gate3_confidence": g3.get("gate3_confidence", ""),
                "existing_rendered_page_count": "0",
                "selection_status": "frozen_new_requires_api",
                "cumulative_cohort": "new_500_scale",
                "requires_gabriel": "yes",
                "seed_selection_rank": "",
            }
        )
    rows = seed_rows + new_rows
    if (
        len(rows) != 1000
        or len({row["document_identity_id"] for row in rows}) != 1000
        or len({row["content_hash"] for row in rows}) != 1000
        or any(not row["matched_non_safety_case_id"] for row in rows)
    ):
        raise RuntimeError("cumulative selection identity/matching gate failed")
    write_csv(
        output / "compensation_extraction_1000_selection_manifest.csv",
        SELECTION_1000_FIELDS,
        rows,
    )
    return rows


def freeze_packets_1000(
    output: Path, rows: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[PagePacket]]]:
    seed_packets = read_csv(
        EXTRACTION_500_DIR / "compensation_extraction_500_packet_manifest.csv"
    )
    seed_case_ids = {
        row["extraction_case_id"]
        for row in rows
        if row["cumulative_cohort"] == "corrected_500_seed"
    }
    if len(seed_case_ids) != 500 or {
        row["extraction_case_id"] for row in seed_packets
    } != seed_case_ids:
        raise RuntimeError("seed packet manifest does not match seed selection")
    packet_rows = [
        {**{field: row.get(field, "") for field in PACKET_FIELDS},
         "cumulative_cohort": "corrected_500_seed"}
        for row in seed_packets
    ]
    renders = render_lookup()
    packet_map: dict[str, list[PagePacket]] = {}
    for row in rows:
        if row["requires_gabriel"] != "yes":
            continue
        pages = build_packet(row, renders)
        packet_map[row["extraction_case_id"]] = pages
        row["planned_lane"] = planned_lane(pages)
        row["existing_rendered_page_count"] = str(sum(bool(page.image) for page in pages))
        total = sum(len(page.text) for page in pages)
        for page in pages:
            packet_rows.append(
                {
                    "extraction_case_id": row["extraction_case_id"],
                    "document_identity_id": row["document_identity_id"],
                    "text_table_detection_id": row["text_table_detection_id"],
                    "page_number": str(page.page),
                    "page_role": page.role,
                    "bounded_evidence_pointer": f"{row['content_artifact_path']}#page={page.page}",
                    "text_chars": str(len(page.text)),
                    "wage_term_count": str(page.wage),
                    "numeric_token_count": str(page.numeric),
                    "table_like_line_count": str(page.table),
                    "qualitative_mechanism_term_count": str(page.qual),
                    "non_base_wage_term_count": str(page.nonbase),
                    "reference_signal": "yes" if page.reference else "no",
                    "rendered_image_available": "yes" if page.image else "no",
                    "rendered_image_path": page.image,
                    "packet_page_count": str(len(pages)),
                    "packet_text_chars": str(total),
                    "packet_status": "bounded_valid",
                    "cumulative_cohort": "new_500_scale",
                }
            )
    write_csv(
        output / "compensation_extraction_1000_selection_manifest.csv",
        SELECTION_1000_FIELDS,
        rows,
    )
    write_csv(
        output / "compensation_extraction_1000_packet_manifest.csv",
        PACKET_1000_FIELDS,
        packet_rows,
    )
    return packet_rows, packet_map


def write_freeze_outputs_1000(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    gate3_path: Path,
    targeted_qa_dir: Path,
) -> None:
    manifest = output / "compensation_extraction_1000_selection_manifest.csv"
    digest = sha_file(manifest)
    (output / "compensation_extraction_1000_selection_sha256.txt").write_text(
        f"{digest}  {manifest.name}\n", encoding="utf-8"
    )
    seed = [row for row in selection if row["cumulative_cohort"] == "corrected_500_seed"]
    new = [row for row in selection if row["cumulative_cohort"] == "new_500_scale"]
    summary = {
        "task_id": TASK_1000_ID,
        "status": "frozen_no_gabriel_calls",
        "selection_count": len(selection),
        "unique_document_identity_count": len({row["document_identity_id"] for row in selection}),
        "unique_content_hash_count": len({row["content_hash"] for row in selection}),
        "corrected_500_seed_count": len(seed),
        "new_document_count": len(new),
        "seed_rerun_required_count": sum(row["requires_gabriel"] == "yes" for row in seed),
        "new_gabriel_required_count": sum(row["requires_gabriel"] == "yes" for row in new),
        "unit_type_counts": dict(Counter(row["unit_type"] for row in selection)),
        "new_unit_type_counts": dict(Counter(row["unit_type"] for row in new)),
        "source_type_counts": dict(Counter(row["candidate_source_type"] for row in selection)),
        "state_counts": dict(Counter(row["state"] for row in selection)),
        "planned_lane_counts": dict(Counter(row["planned_lane"] for row in selection)),
        "manifest_sha256": digest,
        "gate3_input_sha256": sha_file(gate3_path),
        "targeted_qa_decision_sha256": sha_file(targeted_qa_dir / "compensation_extraction_500_recomputed_decision.json"),
        "seed_selection_sha256": sha_file(EXTRACTION_500_DIR / "compensation_extraction_500_selection_manifest.csv"),
        "gabriel_calls": 0,
    }
    write_json(output / "compensation_extraction_1000_selection_summary.json", summary)
    packet_summary = {
        "case_count": len({row["extraction_case_id"] for row in packet_rows}),
        "seed_case_count": len({row["extraction_case_id"] for row in packet_rows if row["cumulative_cohort"] == "corrected_500_seed"}),
        "new_case_count": len({row["extraction_case_id"] for row in packet_rows if row["cumulative_cohort"] == "new_500_scale"}),
        "packet_page_rows": len(packet_rows),
        "max_pages_per_case": max(int(row["packet_page_count"]) for row in packet_rows),
        "max_text_chars_per_page": max(int(row["text_chars"]) for row in packet_rows),
        "max_text_chars_per_case": max(int(row["packet_text_chars"]) for row in packet_rows),
        "rendered_page_available_count": sum(row["rendered_image_available"] == "yes" for row in packet_rows),
        "full_text_saved": False,
        "full_tables_saved": False,
        "raw_prompts_saved": False,
        "raw_responses_saved": False,
        "encoded_images_saved": False,
    }
    write_json(output / "compensation_extraction_1000_packet_summary.json", packet_summary)
    audit = f"""# Frozen cumulative 1,000-document selection audit

- Exact unique identities: {summary['unique_document_identity_count']}
- Corrected 500-document seed reused without GABRIEL: {summary['corrected_500_seed_count']}
- New retained identities: {summary['new_document_count']}
- Cumulative units: `{json.dumps(summary['unit_type_counts'], sort_keys=True)}`
- New units: `{json.dumps(summary['new_unit_type_counts'], sort_keys=True)}`
- States/DC represented: {len(summary['state_counts'])}
- Source families: `{json.dumps(summary['source_type_counts'], sort_keys=True)}`
- Packet rows: {packet_summary['packet_page_rows']}; maximum six pages per case.
- Text caps: 1,500 characters per page and 6,000 per case.
- Selection SHA-256: `{digest}`

The additive quotas are 183 police, 117 fire, and 200 non-safety because the
retained local pool has only 117 new fire identities with an explicit selected
non-safety partner across the cumulative seed. This preserves matching rather
than forcing three unmatched fire cases. The cumulative totals are 363 police,
237 fire, and 400 non-safety.

The freeze made zero GABRIEL/API calls and saved no full document/page text,
full table, raw prompt/response, or encoded image copy.
"""
    (output / "compensation_extraction_1000_selection_audit.md").write_text(
        audit, encoding="utf-8"
    )


def load_selection_1000(output: Path) -> list[dict[str, str]]:
    path = output / "compensation_extraction_1000_selection_manifest.csv"
    rows = read_csv(path)
    digest = (output / "compensation_extraction_1000_selection_sha256.txt").read_text(encoding="utf-8").split()[0]
    if (
        len(rows) != 1000
        or len({row["document_identity_id"] for row in rows}) != 1000
        or sha_file(path) != digest
        or sum(row["requires_gabriel"] == "yes" for row in rows) != 500
    ):
        raise RuntimeError("frozen cumulative selection integrity failure")
    return rows


def packet_rows_and_map_1000(
    output: Path, selection: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[PagePacket]]]:
    existing = read_csv(output / "compensation_extraction_1000_packet_manifest.csv")
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in existing:
        by_case[row["extraction_case_id"]].append(row)
    renders = render_lookup()
    packet_map: dict[str, list[PagePacket]] = {}
    for row in selection:
        if row["requires_gabriel"] != "yes":
            continue
        pages = build_packet(row, renders)
        expected = {
            (int(item["page_number"]), item["text_chars"])
            for item in by_case[row["extraction_case_id"]]
        }
        if {(page.page, str(len(page.text))) for page in pages} != expected:
            raise RuntimeError("new packet reconstruction differs from frozen manifest")
        packet_map[row["extraction_case_id"]] = pages
    if len(packet_map) != 500:
        raise RuntimeError("new packet reconstruction did not yield 500 cases")
    return existing, packet_map


def preflight_1000(
    output: Path,
    selection: list[dict[str, str]],
    packet_map: dict[str, list[PagePacket]],
    key: str,
) -> int:
    new = [row for row in selection if row["requires_gabriel"] == "yes"]
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in new:
        by_lane[row["planned_lane"]].append(row)
    def score(row: dict[str, str], role: str) -> tuple[int, str]:
        pages = packet_map[row["extraction_case_id"]]
        values = {
            "quantitative_base_wage": sum(
                page.table * 4 + page.numeric * 2 + page.wage * 3
                for page in pages
            ),
            "qualitative_mechanism": sum(
                page.qual * 5 + page.wage - page.table for page in pages
            ),
            "mixed_quant_qual": sum(
                page.qual * 3 + page.table * 3 + page.numeric + page.wage
                for page in pages
            ),
            "non_base_wage": sum(
                page.nonbase * 6 + page.numeric for page in pages
            ),
            "reference_exclusion": sum(
                int(page.reference) * 8 - page.table for page in pages
            ),
            "effective_date_or_classification_conflict": sum(
                page.table * 3 + page.numeric * 3 + page.wage * 2
                for page in pages
            ),
        }
        return values[role], row["extraction_case_id"]

    roles = [
        "quantitative_base_wage",
        "qualitative_mechanism",
        "mixed_quant_qual",
        "non_base_wage",
        "reference_exclusion",
        "effective_date_or_classification_conflict",
    ]
    chosen: list[tuple[str, dict[str, str]]] = []
    used: set[str] = set()
    preferred_lanes = {
        "quantitative_base_wage": ("quantitative", "mixed"),
        "qualitative_mechanism": ("qualitative", "mixed"),
        "mixed_quant_qual": ("mixed",),
        "non_base_wage": ("non_base_wage", "mixed", "quantitative"),
        "reference_exclusion": ("reference_and_exclusion", "mixed"),
        "effective_date_or_classification_conflict": ("quantitative", "mixed"),
    }
    primary_lane = {
        "quantitative_base_wage": "quantitative",
        "qualitative_mechanism": "qualitative",
        "mixed_quant_qual": "mixed",
        "non_base_wage": "non_base_wage",
        "reference_exclusion": "reference_and_exclusion",
        "effective_date_or_classification_conflict": "quantitative",
    }
    for role in roles:
        candidates = [
            row
            for row in by_lane[primary_lane[role]]
            if row["extraction_case_id"] not in used
        ]
        if not candidates:
            candidates = [
            row
            for lane in preferred_lanes[role]
            for row in by_lane[lane]
            if row["extraction_case_id"] not in used
            ]
        if not candidates:
            raise RuntimeError(f"representative preflight evidence unavailable: {role}")
        row = max(candidates, key=lambda item: score(item, role))
        chosen.append((role, row))
        used.add(row["extraction_case_id"])
    requests = [
        Request(row, packet_map[row["extraction_case_id"]], f"preflight_1000_{role}")
        for role, row in chosen
    ]
    results = call_gabriel(requests, key, parallel=1)
    metadata = [result_metadata(result, request) for result, request in zip(results, requests)]
    timing = [
        {
            "request_phase": request.phase,
            "extraction_case_id": result.case_id,
            "started_at": "",
            "finished_at": now(),
            "local_packet_seconds": "0.000000",
            "gabriel_elapsed_seconds": f"{result.elapsed:.6f}",
            "request_status": result.status,
        }
        for result, request in zip(results, requests)
    ]
    write_csv(output / "compensation_extraction_1000_request_metadata.csv", METADATA_FIELDS, metadata)
    write_csv(output / "compensation_extraction_1000_timing.csv", TIMING_FIELDS, timing)
    passed = len(results) == 6 and all(result.status == "success" for result in results)
    report = "# Cumulative 1,000-document extraction preflight\n\n"
    report += "\n".join(
        f"- `{role}` / `{result.case_id}`: `{result.status}`"
        for (role, _), result in zip(chosen, results)
    )
    report += f"\n\nOverall: `{'pass' if passed else 'fail'}`.\n"
    report += "\nThe corrected 500-document seed was not sent to GABRIEL.\n"
    (output / "compensation_extraction_1000_preflight_report.md").write_text(
        report, encoding="utf-8"
    )
    write_json(
        output / ".preflight_1000_passed.json",
        {
            "passed": passed,
            "case_count": len(results),
            "schema_valid_count": sum(result.status == "success" for result in results),
            "roles": [role for role, _ in chosen],
            "seed_case_calls": 0,
            "completed_at": now(),
        },
    )
    return 0 if passed else 2


def cumulative_row(
    row: dict[str, str], id_field: str, cohort: str, *, seed: bool
) -> dict[str, str]:
    observation_id = row.get(id_field, "")
    result = dict(row)
    result.update(
        {
            "cumulative_cohort": cohort,
            "source_seed_observation_id": observation_id if seed else "",
            "qa_original_status": row.get("qa_original_status", row.get("qa_status", "")),
            "qa_resolution_classification": row.get(
                "qa_resolution_classification",
                "targeted_qa_carried_forward" if seed else "pending_1000_qa",
            ),
            "qa_resolution_status": row.get(
                "qa_resolution_status", "resolved" if seed else "pending"
            ),
            "canonical_observation_id": row.get(
                "canonical_observation_id", observation_id
            ),
            "duplicate_of": row.get("duplicate_of", ""),
            "active_in_provisional_lane": "true",
        }
    )
    return result


def materialize_cumulative_1000(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    new_results: dict[str, dict[str, Any]],
    targeted_qa_dir: Path,
) -> dict[str, Any]:
    new_selection = [row for row in selection if row["requires_gabriel"] == "yes"]
    with tempfile.TemporaryDirectory(prefix="compensation_1000_new_") as temp:
        new_lanes = materialize_lanes(Path(temp), new_selection, new_results)["rows"]

    seed_paths = {
        "quant": targeted_qa_dir / "quantitative_extraction_ledger_qa_corrected.csv",
        "qual": targeted_qa_dir / "qualitative_mechanism_extraction_ledger_qa_corrected.csv",
        "mixed": targeted_qa_dir / "mixed_extraction_ledger_qa_corrected.csv",
        "nonbase": targeted_qa_dir / "non_base_wage_compensation_ledger_qa_corrected.csv",
        "refs": targeted_qa_dir / "reference_exclusion_ledger_qa_corrected.csv",
    }
    id_fields = {
        "quant": "quantitative_observation_id",
        "qual": "qualitative_observation_id",
        "mixed": "mixed_join_key",
        "nonbase": "non_base_wage_observation_id",
        "refs": "",
    }
    seed_rows: dict[str, list[dict[str, str]]] = {}
    for key_name, path in seed_paths.items():
        rows = read_csv(path)
        rows = [row for row in rows if row.get("active_in_corrected_lane") == "true"]
        seed_rows[key_name] = [
            cumulative_row(
                row,
                id_fields[key_name],
                "corrected_500_seed",
                seed=True,
            )
            for row in rows
        ]
    cumulative = {
        key_name: seed_rows[key_name]
        + [
            cumulative_row(
                row,
                id_fields[key_name],
                "new_500_scale",
                seed=False,
            )
            for row in new_lanes[key_name]
        ]
        for key_name in ("quant", "qual", "mixed", "nonbase", "refs")
    }

    review_rows: list[dict[str, str]] = []
    duplicate_map: dict[str, str] = {}
    duplicate_counts: Counter[str] = Counter()
    lane_specs = (
        ("quantitative", "quant", "quantitative_observation_id", QUANT_FIELDS),
        ("qualitative", "qual", "qualitative_observation_id", QUAL_FIELDS),
        ("non_base_wage", "nonbase", "non_base_wage_observation_id", NONBASE_FIELDS),
    )
    for lane_name, key_name, id_field, base_fields in lane_specs:
        groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        canonical_fields = [
            field for field in base_fields if field not in {id_field, "qa_status"}
        ]
        for row in cumulative[key_name]:
            groups[tuple(row.get(field, "") for field in canonical_fields)].append(row)
        for values in groups.values():
            if len(values) <= 1:
                continue
            canonical = values[0][id_field]
            duplicates = [row[id_field] for row in values[1:]]
            duplicate_counts[lane_name] += len(duplicates)
            for row in values:
                row["canonical_observation_id"] = canonical
                row["duplicate_of"] = "" if row[id_field] == canonical else canonical
                row["active_in_provisional_lane"] = "true" if row[id_field] == canonical else "false"
                row["qa_resolution_classification"] = "duplicate_or_same_observation"
                row["qa_resolution_status"] = "resolved"
                row["qa_status"] = "qa_canonical" if row[id_field] == canonical else "qa_duplicate_inactive"
            duplicate_map.update({duplicate: canonical for duplicate in duplicates})
            review_rows.append(
                {
                    "review_type": "exact_content_duplicate",
                    "extraction_case_id": values[0]["extraction_case_id"],
                    "page_number": values[0].get("page_number", ""),
                    "lane": lane_name,
                    "observation_ids": "|".join(row[id_field] for row in values),
                    "observation_count": str(len(values)),
                    "qa_reason": "EXACT_STRUCTURED_CONTENT_REPEATED",
                    "resolution_classification": "duplicate_or_same_observation",
                    "resolution_status": "resolved",
                    "unresolved_flag": "false",
                    "structured_basis": "Exact structured content; earliest cumulative row is canonical.",
                    "canonical_observation_id": canonical,
                    "duplicate_observation_ids": "|".join(duplicates),
                }
            )

    active_quant = [
        row for row in cumulative["quant"] if row["active_in_provisional_lane"] == "true"
    ]
    conflict_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in active_quant:
        key = tuple(
            row[field]
            for field in (
                "extraction_case_id", "page_number", "compensation_type",
                "occupation_unit_classification_rank", "pay_band", "step",
                "grade", "effective_date", "currency_or_unit",
            )
        )
        conflict_groups[key].append(row)
    conflict_counts: Counter[str] = Counter()
    unresolved_groups = 0
    for values in conflict_groups.values():
        signatures = {
            tuple(
                row[field]
                for field in (
                    "rate_value", "salary_value", "hourly_rate",
                    "annual_salary", "percentage_increase",
                )
            )
            for row in values
        }
        if len(signatures) <= 1:
            continue
        classification, basis = targeted_conflict_resolution(values)
        conflict_counts[classification] += 1
        unresolved = classification in {
            "true_conflict_unresolved", "insufficient_evidence_needs_review"
        }
        unresolved_groups += int(unresolved)
        for row in values:
            row["qa_resolution_classification"] = classification
            row["qa_resolution_status"] = "unresolved" if unresolved else "resolved"
            row["qa_status"] = "needs_conflict_review" if unresolved else "qa_structural_conflict_resolved"
        review_rows.append(
            {
                "review_type": "potential_quantitative_conflict",
                "extraction_case_id": values[0]["extraction_case_id"],
                "page_number": values[0]["page_number"],
                "lane": "quantitative",
                "observation_ids": "|".join(row["quantitative_observation_id"] for row in values),
                "observation_count": str(len(values)),
                "qa_reason": "SAME_EVIDENCE_KEY_DIFFERENT_VALUES",
                "resolution_classification": classification,
                "resolution_status": "unresolved" if unresolved else "resolved",
                "unresolved_flag": "true" if unresolved else "false",
                "structured_basis": basis,
                "canonical_observation_id": "",
                "duplicate_observation_ids": "",
            }
        )

    active_ids = {
        row["quantitative_observation_id"]
        for row in cumulative["quant"]
        if row["active_in_provisional_lane"] == "true"
    }
    active_qual_ids = {
        row["qualitative_observation_id"]
        for row in cumulative["qual"]
        if row["active_in_provisional_lane"] == "true"
    }
    for row in cumulative["mixed"]:
        quant_ids: list[str] = []
        for source_id in row["quantitative_observation_ids"].split("|"):
            if not source_id:
                continue
            canonical = duplicate_map.get(source_id, source_id)
            if canonical in active_ids and canonical not in quant_ids:
                quant_ids.append(canonical)
        qual_ids: list[str] = []
        for source_id in row["qualitative_observation_ids"].split("|"):
            if not source_id:
                continue
            canonical = duplicate_map.get(source_id, source_id)
            if canonical in active_qual_ids and canonical not in qual_ids:
                qual_ids.append(canonical)
        row["quantitative_observation_ids"] = "|".join(quant_ids)
        row["qualitative_observation_ids"] = "|".join(qual_ids)
        row["quantitative_observation_count"] = str(len(quant_ids))
        row["qualitative_observation_count"] = str(len(qual_ids))
        row["active_in_provisional_lane"] = "true" if quant_ids and qual_ids else "false"

    paths = {
        "quant": output / "lanes/quantitative/quantitative_extraction_ledger.csv",
        "qual": output / "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv",
        "mixed": output / "lanes/mixed/mixed_extraction_ledger.csv",
        "nonbase": output / "lanes/non_base_wage/non_base_wage_compensation_ledger.csv",
        "refs": output / "lanes/reference_and_exclusion/reference_exclusion_ledger.csv",
    }
    fields = {
        "quant": QUANT_FIELDS + CUMULATIVE_QA_FIELDS,
        "qual": QUAL_FIELDS + CUMULATIVE_QA_FIELDS,
        "mixed": MIXED_FIELDS + CUMULATIVE_QA_FIELDS,
        "nonbase": NONBASE_FIELDS + CUMULATIVE_QA_FIELDS,
        "refs": REFERENCE_FIELDS + CUMULATIVE_QA_FIELDS,
    }
    for key_name in paths:
        write_csv(paths[key_name], fields[key_name], cumulative[key_name])
    write_csv(
        output / "compensation_extraction_1000_conflict_review.csv",
        CONFLICT_1000_FIELDS,
        review_rows,
    )

    active = {
        key_name: [
            row
            for row in rows
            if row.get("active_in_provisional_lane") == "true"
        ]
        for key_name, rows in cumulative.items()
    }
    summaries = {
        "quantitative": {
            "observation_count": len(active["quant"]),
            "source_row_count": len(cumulative["quant"]),
            "case_count": len({row["extraction_case_id"] for row in active["quant"]}),
            "cohort_counts": dict(Counter(row["cumulative_cohort"] for row in active["quant"])),
            "confidence_counts": dict(Counter(row["confidence"] for row in active["quant"])),
        },
        "qualitative": {
            "observation_count": len(active["qual"]),
            "source_row_count": len(cumulative["qual"]),
            "case_count": len({row["extraction_case_id"] for row in active["qual"]}),
            "cohort_counts": dict(Counter(row["cumulative_cohort"] for row in active["qual"])),
            "confidence_counts": dict(Counter(row["confidence"] for row in active["qual"])),
        },
        "mixed": {
            "case_count": len(active["mixed"]),
            "source_row_count": len(cumulative["mixed"]),
            "quantitative_subrecord_count": sum(int(row["quantitative_observation_count"]) for row in active["mixed"]),
            "qualitative_subrecord_count": sum(int(row["qualitative_observation_count"]) for row in active["mixed"]),
            "cohort_counts": dict(Counter(row["cumulative_cohort"] for row in active["mixed"])),
        },
        "non_base_wage": {
            "observation_count": len(active["nonbase"]),
            "source_row_count": len(cumulative["nonbase"]),
            "case_count": len({row["extraction_case_id"] for row in active["nonbase"]}),
            "cohort_counts": dict(Counter(row["cumulative_cohort"] for row in active["nonbase"])),
            "type_counts": dict(Counter(row["non_base_wage_type"] for row in active["nonbase"])),
        },
        "reference_and_exclusion": {
            "case_count": len(active["refs"]),
            "source_row_count": len(cumulative["refs"]),
            "cohort_counts": dict(Counter(row["cumulative_cohort"] for row in active["refs"])),
            "disposition_counts": dict(Counter(row["disposition"] for row in active["refs"])),
        },
    }
    write_json(output / "lanes/quantitative/quantitative_extraction_summary.json", summaries["quantitative"])
    write_json(output / "lanes/qualitative/qualitative_mechanism_extraction_summary.json", summaries["qualitative"])
    write_json(output / "lanes/mixed/mixed_extraction_summary.json", summaries["mixed"])
    write_json(output / "lanes/non_base_wage/non_base_wage_compensation_summary.json", summaries["non_base_wage"])
    write_json(output / "lanes/reference_and_exclusion/reference_exclusion_summary.json", summaries["reference_and_exclusion"])

    pages_by_case: dict[str, set[int]] = defaultdict(set)
    for row in packet_rows:
        pages_by_case[row["extraction_case_id"]].add(int(row["page_number"]))
    observation_rows = active["quant"] + active["qual"] + active["nonbase"]
    invalid_pages = sum(
        int(row["page_number"]) not in pages_by_case[row["extraction_case_id"]]
        for row in observation_rows
    )
    all_ids = (
        [row["quantitative_observation_id"] for row in cumulative["quant"]]
        + [row["qualitative_observation_id"] for row in cumulative["qual"]]
        + [row["non_base_wage_observation_id"] for row in cumulative["nonbase"]]
    )
    duplicate_ids = len(all_ids) - len(set(all_ids))
    contamination = sum(targeted_nonbase_type(row) is not None for row in active["quant"])
    conflict_rate = unresolved_groups / max(1, len(active["quant"]))
    packet_compliant = (
        len({row["extraction_case_id"] for row in packet_rows}) == 1000
        and all(
            int(row["packet_page_count"]) <= 6
            and int(row["packet_text_chars"]) <= 6000
            and int(row["text_chars"]) <= 1500
            for row in packet_rows
        )
    )
    unit_counts = Counter(row["unit_type"] for row in selection)
    matching_intact = (
        unit_counts == {"police": 363, "fire": 237, "non_safety": 400}
        and all(row["matched_non_safety_case_id"] for row in selection)
    )
    integrity_pass = (
        len(selection) == 1000
        and len(new_results) == 500
        and packet_compliant
        and invalid_pages == 0
        and duplicate_ids == 0
        and contamination == 0
        and matching_intact
    )
    another_targeted_qa = unresolved_groups > 0 or sum(duplicate_counts.values()) > 0
    if not integrity_pass:
        scale = "blocked_by_integrity_qa_failure"
    elif conflict_rate > 0.02 or contamination:
        scale = "blocked_pending_targeted_qa"
    elif another_targeted_qa:
        scale = "premature_pending_targeted_qa"
    else:
        scale = "eligible_for_further_provisional_scale"

    seed_case_sets = {
        key_name: {row["extraction_case_id"] for row in active[key_name] if row["cumulative_cohort"] == "corrected_500_seed"}
        for key_name in active
    }
    seed_dispositions: dict[str, str] = {}
    seed_selection = [row for row in selection if row["requires_gabriel"] == "no"]
    refs_by_case = {
        row["extraction_case_id"]: row["disposition"]
        for row in active["refs"]
        if row["cumulative_cohort"] == "corrected_500_seed"
    }
    for row in seed_selection:
        case_id = row["extraction_case_id"]
        if case_id in seed_case_sets["mixed"] or (
            case_id in seed_case_sets["quant"] and case_id in seed_case_sets["qual"]
        ):
            disposition = "mixed_ready"
        elif case_id in seed_case_sets["quant"]:
            disposition = "quantitative_ready"
        elif case_id in seed_case_sets["qual"]:
            disposition = "qualitative_ready"
        elif case_id in seed_case_sets["nonbase"]:
            disposition = "non_base_wage"
        else:
            disposition = refs_by_case.get(case_id, "exclude")
        seed_dispositions[case_id] = disposition
    disposition_counts = Counter(seed_dispositions.values())
    disposition_counts.update(value["case_disposition"] for value in new_results.values())

    metadata_rows = read_csv(output / "compensation_extraction_1000_request_metadata.csv")
    live_attempts = [row for row in metadata_rows if row["request_phase"] == "live_1000"]
    successful_live_ids = {
        row["extraction_case_id"]
        for row in live_attempts
        if row["schema_valid"] == "true"
    }
    decision = {
        "task_id": TASK_1000_ID,
        "generated_at": now(),
        "decision": scale,
        "qa_status": "pass" if integrity_pass else "fail",
        "qa_pass": integrity_pass,
        "integrity_qa_pass": integrity_pass,
        "selection_count": len(selection),
        "corrected_seed_case_count": 500,
        "new_case_count": len(new_results),
        "case_level_schema_valid_count": 500 + len(new_results),
        "case_level_schema_valid_rate": round((500 + len(new_results)) / 1000, 6),
        "new_case_schema_valid_count": len(successful_live_ids),
        "new_case_schema_valid_rate": round(len(successful_live_ids) / 500, 6),
        "packet_compliant": packet_compliant,
        "packet_rows": len(packet_rows),
        "invalid_observation_page_count": invalid_pages,
        "duplicate_observation_id_count": duplicate_ids,
        "duplicate_structured_content_counts": dict(duplicate_counts),
        "conflicting_quantitative_group_count": sum(conflict_counts.values()),
        "conflict_resolution_counts": dict(conflict_counts),
        "unresolved_quantitative_conflict_group_count": unresolved_groups,
        "unresolved_quantitative_conflict_rate": round(conflict_rate, 6),
        "base_non_base_wage_contamination_count": contamination,
        "another_targeted_qa_required": another_targeted_qa,
        "scale_beyond_1000_recommendation": scale,
        "matched_representation_intact": matching_intact,
        "unit_type_counts": dict(unit_counts),
        "state_count": len({row["state"] for row in selection}),
        "source_type_counts": dict(Counter(row["candidate_source_type"] for row in selection)),
        "disposition_counts": dict(disposition_counts),
        "quantitative_observation_count": len(active["quant"]),
        "qualitative_mechanism_observation_count": len(active["qual"]),
        "mixed_case_count": len(active["mixed"]),
        "non_base_wage_observation_count": len(active["nonbase"]),
        "reference_exclusion_case_count": len(active["refs"]),
        "seed_gabriel_calls": 0,
        "raw_prompts_saved": False,
        "raw_responses_saved": False,
        "full_text_saved": False,
        "full_tables_saved": False,
        "encoded_images_saved": False,
        "final_merge_allowed": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
    }
    write_json(output / "compensation_extraction_1000_decision_report.json", decision)
    report = f"""# Provisional cumulative 1,000-document extraction QA report

- Integrity QA: `{'pass' if integrity_pass else 'fail'}`
- Corrected 500-document seed reused without GABRIEL: 500
- New schema-valid cases: {len(new_results)} / 500
- Cumulative schema-valid cases: {500 + len(new_results)} / 1,000
- Packet compliance: `{str(packet_compliant).lower()}`
- Invalid observation pages: {invalid_pages}
- Duplicate observation IDs: {duplicate_ids}
- Exact structured-content duplicates canonicalized: {sum(duplicate_counts.values())}
- Quantitative conflict groups: {sum(conflict_counts.values())}
- Unresolved quantitative conflict groups: {unresolved_groups}
- Unresolved conflict rate: {conflict_rate:.4%}
- Base/non-base contamination: {contamination}
- Active quantitative observations: {len(active['quant'])}
- Active qualitative-mechanism observations: {len(active['qual'])}
- Active mixed cases: {len(active['mixed'])}
- Active non-base-wage observations: {len(active['nonbase'])}
- Reference/exclusion cases: {len(active['refs'])}
- Another targeted QA required: `{str(another_targeted_qa).lower()}`
- Beyond-1,000 recommendation: `{scale}`

The outputs are provisional and separate from final analysis inputs. No final
merge, ingestion, codification, wage-gap analysis, regression, URL access,
download, or OCR occurred.
"""
    (output / "compensation_extraction_1000_qa_report.md").write_text(
        report, encoding="utf-8"
    )
    validation = f"""# Provisional 1,000-document extraction validation — 2026-07-25

- Exact cumulative identities: `{'pass' if len(selection) == 1000 else 'fail'}`
- Corrected seed preserved without API: `pass` (500)
- New strict-schema cases: `{'pass' if len(new_results) == 500 else 'fail'}` ({len(new_results)})
- Packet limits: `{'pass' if packet_compliant else 'fail'}`
- Invalid bounded pointers: `{'pass' if invalid_pages == 0 else 'fail'}` ({invalid_pages})
- Duplicate observation IDs: `{'pass' if duplicate_ids == 0 else 'fail'}` ({duplicate_ids})
- Base/non-base contamination: `{'pass' if contamination == 0 else 'fail'}` ({contamination})
- Matched representation: `{'pass' if matching_intact else 'fail'}`
- Raw prompts/responses, full text/tables, encoded images saved: `false`

Repository-wide validation commands are appended after the required test suite.
"""
    (output / "compensation_extraction_1000_validation_2026-07-25.md").write_text(
        validation, encoding="utf-8"
    )
    return {"decision": decision, "summaries": summaries, "rows": cumulative}


def live_1000(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    packet_map: dict[str, list[PagePacket]],
    targeted_qa_dir: Path,
    key: str,
    resume: bool,
) -> int:
    marker = read_json(output / ".preflight_1000_passed.json")
    if marker.get("passed") is not True or int(marker.get("schema_valid_count", 0)) != 6:
        raise RuntimeError("live 1,000 lanes require successful six-path preflight")
    checkpoint = output / "compensation_extraction_1000_new_case_results.jsonl"
    stored: dict[str, dict[str, Any]] = {}
    if resume and checkpoint.is_file():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            stored[item["extraction_case_id"]] = item["result"]
    metadata_path = output / "compensation_extraction_1000_request_metadata.csv"
    timing_path = output / "compensation_extraction_1000_timing.csv"
    metadata = read_csv(metadata_path) if metadata_path.is_file() else []
    timing = read_csv(timing_path) if timing_path.is_file() else []
    new_selection = [row for row in selection if row["requires_gabriel"] == "yes"]
    pending = [row for row in new_selection if row["extraction_case_id"] not in stored]
    for start in range(0, len(pending), 25):
        batch_rows = pending[start : start + 25]
        requests = [
            Request(row, packet_map[row["extraction_case_id"]], "live_1000")
            for row in batch_rows
        ]
        results = call_gabriel(requests, key, parallel=2)
        for result, request in zip(results, requests):
            metadata.append(result_metadata(result, request))
            timing.append(
                {
                    "request_phase": "live_1000",
                    "extraction_case_id": result.case_id,
                    "started_at": "",
                    "finished_at": now(),
                    "local_packet_seconds": "0.000000",
                    "gabriel_elapsed_seconds": f"{result.elapsed:.6f}",
                    "request_status": result.status,
                }
            )
            if result.status == "success" and result.parsed is not None:
                stored[result.case_id] = result.parsed
        checkpoint.write_text(
            "\n".join(
                json.dumps(
                    {"extraction_case_id": case_id, "result": stored[case_id]},
                    sort_keys=True,
                )
                for case_id in sorted(stored)
            )
            + ("\n" if stored else ""),
            encoding="utf-8",
        )
        write_csv(metadata_path, METADATA_FIELDS, metadata)
        write_csv(timing_path, TIMING_FIELDS, timing)
        print(
            json.dumps(
                {
                    "phase": "live_lanes_1000",
                    "attempted": min(start + len(batch_rows), len(pending)),
                    "pending_at_start": len(pending),
                    "schema_valid_new_results_stored": len(stored),
                    "batch_success": sum(result.status == "success" for result in results),
                    "batch_failed": sum(result.status != "success" for result in results),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    if len(stored) != 500:
        return 2
    materialized = materialize_cumulative_1000(
        output, selection, packet_rows, stored, targeted_qa_dir
    )
    return 0 if materialized["decision"]["qa_pass"] else 2


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--mode",
        choices=(
            "freeze_500_selection",
            "preflight",
            "live_lanes",
            "freeze_1000_selection",
            "preflight_1000",
            "live_lanes_1000",
        ),
        required=True,
    )
    p.add_argument("--gate3-ledger", type=Path, default=GATE3)
    p.add_argument("--targeted-qa-dir", type=Path, default=TARGETED_QA_500_DIR)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--case-limit", type=int, default=500)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--preflight-representative-cases", action="store_true")
    p.add_argument("--allow-gabriel", action="store_true")
    p.add_argument("--resume", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output_dir.resolve()
    gate3 = args.gate3_ledger.resolve()
    targeted_qa_dir = args.targeted_qa_dir.resolve()
    is_1000 = args.mode in {
        "freeze_1000_selection",
        "preflight_1000",
        "live_lanes_1000",
    }
    expected_limit = 1000 if is_1000 else 500
    if args.case_limit != expected_limit:
        raise ValueError(f"{args.mode} requires exactly {expected_limit} cases")
    if args.mode == "freeze_1000_selection":
        if not args.dry_run or args.allow_gabriel:
            raise ValueError("1,000 selection freeze must be a no-call dry run")
        output.mkdir(parents=True, exist_ok=True)
        selection = freeze_selection_1000(
            gate3, targeted_qa_dir, output, args.case_limit
        )
        packet_rows, _ = freeze_packets_1000(output, selection)
        write_freeze_outputs_1000(
            output, selection, packet_rows, gate3, targeted_qa_dir
        )
        print(
            json.dumps(
                {
                    "status": "frozen",
                    "selection_count": len(selection),
                    "corrected_seed_count": sum(
                        row["cumulative_cohort"] == "corrected_500_seed"
                        for row in selection
                    ),
                    "new_case_count": sum(
                        row["cumulative_cohort"] == "new_500_scale"
                        for row in selection
                    ),
                    "packet_rows": len(packet_rows),
                    "gabriel_calls": 0,
                },
                sort_keys=True,
            )
        )
        return 0
    if args.mode == "freeze_500_selection":
        if not args.dry_run or args.allow_gabriel: raise ValueError("selection freeze must be a no-call dry run")
        output.mkdir(parents=True, exist_ok=True)
        selection = freeze_selection(gate3, output, args.case_limit)
        packet_rows, _ = freeze_packets(output, selection)
        write_freeze_outputs(output, selection, packet_rows, gate3)
        print(json.dumps({"status": "frozen", "selection_count": len(selection), "packet_rows": len(packet_rows), "gabriel_calls": 0}, sort_keys=True)); return 0
    if is_1000:
        selection = load_selection_1000(output)
        packet_rows, packet_map = packet_rows_and_map_1000(output, selection)
    else:
        selection = load_selection(output)
        packet_rows, packet_map = packet_rows_and_map(output, selection)
    if not args.allow_gabriel: raise ValueError("live GABRIEL modes require --allow-gabriel")
    key = load_key()
    if not key: raise RuntimeError("GABRIEL credential unavailable")
    if args.mode == "preflight":
        if not args.preflight_representative_cases: raise ValueError("representative preflight flag required")
        return preflight(output, selection, packet_map, key)
    if args.mode == "preflight_1000":
        if not args.preflight_representative_cases:
            raise ValueError("representative 1,000-document preflight flag required")
        return preflight_1000(output, selection, packet_map, key)
    if not args.resume: raise ValueError("live lanes require --resume")
    if args.mode == "live_lanes_1000":
        return live_1000(
            output,
            selection,
            packet_rows,
            packet_map,
            targeted_qa_dir,
            key,
            args.resume,
        )
    return live(output, selection, packet_rows, packet_map, key, args.resume)


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {str(exc)[:300]}", file=sys.stderr); raise SystemExit(1)
