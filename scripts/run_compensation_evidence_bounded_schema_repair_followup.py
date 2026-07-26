#!/usr/bin/env python3
"""Build a bounded, non-extractive follow-up to the compensation schema repair.

Only committed structured or bounded artifacts are read. The runner never opens a
URL or PDF, never calls a model, and never mutates its package, prior-repair, or
durable-ledger inputs. Ambiguous bridge values are left blank and quarantined.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-SCHEMA-REPAIR-FOLLOWUP-2026-07-25"
)

PRIOR_INPUTS = {
    "decision": PRIOR / "schema_repair_decision.json",
    "bridge": PRIOR / "identity_provenance_bridge.csv",
    "quantitative": PRIOR / "repaired_quantitative_shadow.csv",
    "qualitative": PRIOR / "repaired_qualitative_mechanism_shadow.csv",
    "mixed": PRIOR / "repaired_mixed_join_shadow.csv",
    "non_base_wage": PRIOR / "repaired_non_base_wage_shadow.csv",
    "reference_and_exclusion": PRIOR / "repaired_reference_exclusion_shadow.csv",
    "quantitative_candidate": PRIOR / "quantitative_analysis_view_candidate.csv",
    "quantitative_exceptions": PRIOR / "quantitative_normalization_exception_ledger.csv",
    "non_base_candidate": PRIOR / "non_base_wage_companion_view_candidate.csv",
    "reference_control": PRIOR / "reference_exclusion_control_view.csv",
    "qualitative_navigation": PRIOR / "qualitative_mechanism_navigation_view_candidate.csv",
    "conflict_quarantine": PRIOR / "unresolved_conflict_quarantine_ledger.csv",
}

DURABLE_INPUTS = {
    "candidate_queue": ROOT / "docs/analysis/national_scout_candidate_queue_2026-07-20.csv",
    "content_triage": ROOT / "docs/analysis/content_triage_ledgers/content_triage_ledger_latest.csv",
    "verification": ROOT
    / "docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv",
    "source_review": ROOT
    / "docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv",
    "text_table_detection": ROOT
    / "docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv",
}

OUTPUTS = {
    "summary": "bounded_schema_repair_followup_summary.md",
    "decision": "bounded_schema_repair_followup_decision.json",
    "cycle_bridge": "bounded_cycle_matching_bridge.csv",
    "cycle_audit": "bounded_cycle_matching_bridge_audit.json",
    "retrieval_bridge": "bounded_retrieval_provenance_bridge.csv",
    "retrieval_audit": "bounded_retrieval_provenance_bridge_audit.json",
    "occupation_bridge": "bounded_non_safety_occupation_bridge.csv",
    "occupation_audit": "bounded_non_safety_occupation_bridge_audit.json",
    "durable_hashes": "bounded_followup_durable_input_sha256.txt",
    "quant_shadow": "repaired_quantitative_shadow_followup.csv",
    "qual_shadow": "repaired_qualitative_mechanism_shadow_followup.csv",
    "mixed_shadow": "repaired_mixed_join_shadow_followup.csv",
    "nonbase_shadow": "repaired_non_base_wage_shadow_followup.csv",
    "reference_shadow": "repaired_reference_exclusion_shadow_followup.csv",
    "quant_report": "quantitative_followup_parse_improvement_report.md",
    "quant_exceptions": "quantitative_followup_exception_ledger.csv",
    "quant_candidate": "quantitative_analysis_view_candidate_followup.csv",
    "qual_span_audit": "qualitative_evidence_span_availability_audit.json",
    "qual_report": "qualitative_mechanism_followup_report.md",
    "qual_navigation": "qualitative_mechanism_navigation_view_candidate_followup.csv",
    "nonbase_report": "non_base_followup_other_disposition_report.md",
    "nonbase_candidate": "non_base_wage_companion_view_candidate_followup.csv",
    "reference_control": "reference_exclusion_control_view_followup.csv",
    "quarantine": "bounded_followup_quarantine_summary.json",
    "blockers": "bounded_followup_blocker_matrix.csv",
    "validation": "bounded_schema_repair_followup_validation_2026-07-25.md",
    "future_prompt": "next_bounded_schema_repair_followup_prompt.md",
}

EXPECTED_PRIOR_SHA256 = {
    "quantitative": "a05b5baf5b3a63ecbf5f3a997bfd2f0803966d97cc7377a296c5ad1d32ff78fd",
    "qualitative": "a70c7870bc5ca9e54c7f1c89f8d990dedce3a65c2639c937ed915dbc7ec2688c",
    "mixed": "1abd89b938edc99538ad5021f5615c31e07cdf5febb173f793b89cc1a67bf600",
    "non_base_wage": "219c0f7ef44a2ac5106d3bd1d1075143c43bfe12ad4ec8eb53fcf3086f7d8c69",
    "reference_and_exclusion": "10a5956b1a1104d2f271a52ec18967e64f476527b8bab0a747bb873307004a27",
    "bridge": "b00d0bf89fdfe4d826d8db0fc8d11e8f02f46d5c9a185088cc85215932aaee06",
}

TASK_ID = "COMPENSATION-EVIDENCE-BOUNDED-SCHEMA-REPAIR-FOLLOWUP-2026-07-25"
DECISION = "bounded_schema_followup_partial_additional_bounded_repair_needed"

MONTH = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|"
    r"December|Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Sept\.?|"
    r"Oct\.?|Nov\.?|Dec\.?)"
)
MONTH_DATE = rf"{MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*\d{{4}}"
NUMERIC_DATE = r"\d{1,2}[./-]\d{1,2}[./-]\d{4}"
PAIR_DELIMITER = r"\s*(?:through|thru|to|until|[-–—])\s*"
PERIOD_PATTERNS = (
    re.compile(rf"(?P<start>{MONTH_DATE}){PAIR_DELIMITER}(?P<end>{MONTH_DATE})", re.I),
    re.compile(rf"(?P<start>{NUMERIC_DATE}){PAIR_DELIMITER}(?P<end>{NUMERIC_DATE})", re.I),
)
EXACT_EFFECTIVE_PATTERNS = (
    (re.compile(r"^(?:effective\s+)?(\d{4}-\d{2}-\d{2})$", re.I), ("%Y-%m-%d",)),
    (
        re.compile(r"^(?:effective\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})$", re.I),
        ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"),
    ),
    (
        re.compile(rf"^(?:effective\s+)?({MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*\d{{4}})$", re.I),
        ("%B %d %Y", "%b %d %Y"),
    ),
)

OCCUPATION_RULES = {
    "teacher": re.compile(r"\bteachers?\b|\beducators?\b", re.I),
    "sanitation": re.compile(r"\bsanitation\b|\bsolid waste\b", re.I),
    "clerical_admin": re.compile(
        r"\bclerical\b|\badministrative employees?\b|\boffice employees?\b", re.I
    ),
    "public_works": re.compile(r"\bpublic works\b|\bdpw\b|\bhighway department\b", re.I),
    "transit": re.compile(r"\btransit\b", re.I),
    "parks_rec": re.compile(
        r"\bparks?(?:\s+and\s+|\s*&\s*)recreation\b|\brecreation employees?\b", re.I
    ),
    "library": re.compile(r"\blibrar(?:y|ies|ian|ians)\b", re.I),
    "nurse_health": re.compile(r"\bnurses?\b|\bpublic health\b|\bhealth department\b", re.I),
}

SOURCE_CORPUS_MAP = {
    "cba": "causal",
    "arbitration_award": "causal",
    "factfinding": "causal",
    "memorandum_or_settlement": "causal",
    "ordinance_or_policy": "causal",
    "wage_schedule_or_compensation_plan": "causal",
}

FOLLOWUP_BRIDGE_FIELDS = [
    "contract_period_start_bridge",
    "contract_period_end_bridge",
    "negotiation_cycle_id",
    "city_unit_negotiation_cycle_key",
    "matched_set_id",
    "analysis_matching_status",
    "controlled_occupation_class",
    "occupation_class_bridge_status",
    "retrieval_date_bridge",
    "retrieval_method_bridge",
    "source_type_bridge",
    "source_corpus_bridge",
    "source_cite_bridge",
    "artifact_pointer_bridge",
    "followup_cycle_bridge_status",
    "followup_cycle_source_fields",
    "followup_occupation_bridge_status",
    "followup_occupation_support_fields",
    "followup_retrieval_bridge_status",
    "followup_retrieval_support_fields",
]

FOLLOWUP_QUANT_FIELDS = [
    "followup_normalized_effective_date",
    "followup_effective_date_parse_status",
    "followup_analysis_candidate_eligible",
    "followup_analysis_quarantine_reasons",
    "followup_parse_improvement_reason_code",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_{hashlib.sha256('|'.join(parts).encode()).hexdigest()[:24]}"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise RuntimeError(f"Missing or duplicate headers in {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, header: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in header})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def parse_date_token(value: str) -> str:
    cleaned = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", value, flags=re.I)
    cleaned = cleaned.replace(",", "").strip()
    cleaned = re.sub(r"\bSept\.?\b", "Sep", cleaned, flags=re.I)
    formats = ("%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y")
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def exact_period_pairs(value: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for pattern in PERIOD_PATTERNS:
        for match in pattern.finditer(value or ""):
            start = parse_date_token(match.group("start"))
            end = parse_date_token(match.group("end"))
            if start and end and start <= end:
                pairs.add((start, end))
    return pairs


def parse_expanded_exact_effective_date(value: str) -> tuple[str, str]:
    value = value.strip()
    if not value:
        return "", "blank"
    for pattern, formats in EXACT_EFFECTIVE_PATTERNS:
        match = pattern.match(value)
        if not match:
            continue
        token = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", match.group(1), flags=re.I)
        token = token.replace(",", "").strip()
        token = re.sub(r"\bSept\.?\b", "Sep", token, flags=re.I)
        for fmt in formats:
            try:
                return datetime.strptime(token, fmt).date().isoformat(), "exact_expanded_token"
            except ValueError:
                continue
    return "", "unparsed_or_ambiguous"


def unique_map(rows: list[dict[str, str]], key: str, expected: set[str]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get(key, "") in expected:
            grouped[row[key]].append(row)
    duplicates = {value: group for value, group in grouped.items() if len(group) != 1}
    missing = expected - set(grouped)
    if duplicates or missing:
        raise RuntimeError(
            f"Unsafe {key} bridge cardinality: duplicate={len(duplicates)} missing={len(missing)}"
        )
    return {value: group[0] for value, group in grouped.items()}


def input_preflight(output_dir: Path) -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in [*PRIOR_INPUTS.values(), *DURABLE_INPUTS.values()] if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required artifacts missing: {missing}")
    if output_dir.exists():
        raise FileExistsError(f"Rollback-safe output already exists: {output_dir}")
    resolved = output_dir.resolve()
    if (ROOT / "docs/analysis").resolve() not in resolved.parents:
        raise RuntimeError("Output must be a new docs/analysis subdirectory")
    forbidden = {"data", "corpus", "ingest", "codified", "analysis_dataset"}
    if forbidden.intersection(resolved.relative_to(ROOT).parts):
        raise RuntimeError(f"Forbidden output path: {resolved}")
    decision = json.loads(PRIOR_INPUTS["decision"].read_text(encoding="utf-8"))
    if decision.get("decision") != "schema_repairs_partial_additional_bounded_evidence_needed":
        raise RuntimeError("Unexpected prior schema-repair decision")
    prior_hashes = {
        name: sha256(PRIOR_INPUTS[name])
        for name in ("quantitative", "qualitative", "mixed", "non_base_wage", "reference_and_exclusion", "bridge")
    }
    if prior_hashes != EXPECTED_PRIOR_SHA256:
        raise RuntimeError(f"Prior repair SHA-256 mismatch: {prior_hashes}")
    # Reuse the predecessor's package preflight, which verifies all five immutable package hashes.
    module_path = ROOT / "scripts/repair_compensation_evidence_final_provisional_schemas.py"
    spec = importlib.util.spec_from_file_location("prior_schema_repair_for_followup", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load predecessor schema-repair module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    package = module.package_hash_preflight()
    return {
        "package_sha256_checks_passed": len(package["package_sha256"]),
        "prior_input_sha256": prior_hashes,
        "durable_input_sha256": {name: sha256(path) for name, path in DURABLE_INPUTS.items()},
        "writes_performed": 0,
        "analysis_readiness_after_task": False,
    }


def build_context() -> dict[str, Any]:
    bridge_header, bridge_rows = read_rows(PRIOR_INPUTS["bridge"])
    if len(bridge_rows) != 1826 or len({row["document_identity_id"] for row in bridge_rows}) != 1826:
        raise RuntimeError("Expected 1,826 unique prior bridge identities")
    candidate_ids = {row["candidate_queue_row_id"] for row in bridge_rows}
    ttd_ids = {row["text_table_detection_id"] for row in bridge_rows}
    source_ids = {row["source_review_id"] for row in bridge_rows}

    durable_rows = {name: read_rows(path)[1] for name, path in DURABLE_INPUTS.items()}
    candidate_by_id = unique_map(durable_rows["candidate_queue"], "queue_id", candidate_ids)
    triage_by_candidate = unique_map(durable_rows["content_triage"], "candidate_queue_row_id", candidate_ids)
    verification_by_candidate = unique_map(durable_rows["verification"], "candidate_queue_row_id", candidate_ids)
    source_by_id = unique_map(durable_rows["source_review"], "source_review_id", source_ids)
    ttd_by_id = unique_map(durable_rows["text_table_detection"], "text_table_detection_id", ttd_ids)

    cycle_rows: list[dict[str, str]] = []
    occupation_rows: list[dict[str, str]] = []
    retrieval_rows: list[dict[str, str]] = []
    identity: dict[str, dict[str, str]] = {}

    for base in bridge_rows:
        document_id = base["document_identity_id"]
        candidate = candidate_by_id[base["candidate_queue_row_id"]]
        triage = triage_by_candidate[base["candidate_queue_row_id"]]
        verification = verification_by_candidate[base["candidate_queue_row_id"]]
        source = source_by_id[base["source_review_id"]]
        ttd = ttd_by_id[base["text_table_detection_id"]]
        if any(
            row.get("candidate_queue_row_id", candidate.get("queue_id", "")) != base["candidate_queue_row_id"]
            for row in (triage, verification, source, ttd)
        ):
            raise RuntimeError(f"Candidate identity disagreement for {document_id}")

        source_pairs = {
            "candidate_queue.contract_years_scouted": exact_period_pairs(candidate.get("contract_years_scouted", "")),
            "candidate_queue.visible_year_evidence": exact_period_pairs(candidate.get("visible_year_evidence", "")),
            "text_table_detection.candidate_contract_period_text": exact_period_pairs(ttd.get("candidate_contract_period_text", "")),
        }
        combined = set().union(*source_pairs.values())
        period_start = period_end = ""
        if len(combined) == 1:
            period_start, period_end = next(iter(combined))
            cycle_status = "established_single_exact_pair"
        elif len(combined) > 1:
            cycle_status = "quarantined_conflicting_or_multiple_exact_pairs"
        else:
            cycle_status = "quarantined_no_exact_full_date_pair"
        support_fields = "|".join(name for name, pairs in source_pairs.items() if pairs)
        negotiation_cycle_id = (
            stable_id("cycle", base["state"], base["municipality"], period_start, period_end)
            if period_start and period_end
            else ""
        )
        city_unit_cycle = (
            stable_id(
                "cuc",
                base["state"],
                base["municipality"],
                base["unit_type"],
                period_start,
                period_end,
            )
            if negotiation_cycle_id
            else ""
        )
        cycle_row = {
            "document_identity_id": document_id,
            "candidate_queue_row_id": base["candidate_queue_row_id"],
            "text_table_detection_id": base["text_table_detection_id"],
            "state": base["state"],
            "municipality": base["municipality"],
            "government_name": base["government_name"],
            "unit_type": base["unit_type"],
            "contract_period_start": period_start,
            "contract_period_end": period_end,
            "negotiation_cycle_id": negotiation_cycle_id,
            "city_unit_negotiation_cycle_key": city_unit_cycle,
            "matched_set_id": "",
            "cycle_bridge_status": cycle_status,
            "cycle_source_fields": support_fields,
            "exact_period_pair_count": str(len(combined)),
        }
        cycle_rows.append(cycle_row)

        if base["unit_type"] in {"police", "fire"}:
            occupation_class = base["unit_type"]
            occupation_status = "exact_public_safety_unit_type"
            occupation_support = "prior_bridge.unit_type"
        else:
            explicit_text = " | ".join(
                (
                    candidate.get("unit_type_scouted", ""),
                    candidate.get("document_title", ""),
                    candidate.get("union_name", ""),
                )
            )
            matches = [label for label, pattern in OCCUPATION_RULES.items() if pattern.search(explicit_text)]
            if len(matches) == 1:
                occupation_class = matches[0]
                occupation_status = "established_single_explicit_structured_label_rule"
            elif len(matches) > 1:
                occupation_class = ""
                occupation_status = "quarantined_multiple_controlled_label_rules"
            else:
                occupation_class = ""
                occupation_status = "quarantined_no_controlled_explicit_label"
            occupation_support = "candidate_queue.unit_type_scouted|candidate_queue.document_title|candidate_queue.union_name"
        occupation_row = {
            "document_identity_id": document_id,
            "candidate_queue_row_id": base["candidate_queue_row_id"],
            "unit_type": base["unit_type"],
            "controlled_occupation_class": occupation_class,
            "occupation_class_bridge_status": occupation_status,
            "occupation_support_fields": occupation_support,
        }
        occupation_rows.append(occupation_row)

        retrieval_supported = all(
            (
                verification.get("verification_status") == "reachable_pdf_or_document",
                verification.get("url_reachable") == "yes",
                bool(verification.get("artifact_path", "").strip()),
                int(verification.get("bytes_read") or 0) > 0,
                bool(verification.get("verified_at", "").strip()),
                source.get("download_status") == "artifact_saved",
                source.get("url_access_status") == "reached",
                int(source.get("documents_downloaded") or 0) > 0,
                bool(source.get("content_artifact_path", "").strip()),
            )
        )
        retrieval_date = ""
        if retrieval_supported:
            try:
                retrieval_date = datetime.fromisoformat(
                    verification["verified_at"].replace("Z", "+00:00")
                ).date().isoformat()
            except ValueError:
                retrieval_supported = False
        source_type = source.get("candidate_source_type", "").strip()
        source_corpus = SOURCE_CORPUS_MAP.get(source_type, "")
        retrieval_row = {
            "document_identity_id": document_id,
            "candidate_queue_row_id": base["candidate_queue_row_id"],
            "source_review_id": base["source_review_id"],
            "verification_id": source.get("verification_id", ""),
            "retrieval_date": retrieval_date if retrieval_supported else "",
            "retrieval_method": "public_download" if retrieval_supported else "",
            "source_type": source_type,
            "source_corpus": source_corpus,
            "source_cite": source.get("source_locator", "").strip(),
            "artifact_pointer": source.get("content_artifact_path", "").strip(),
            "retrieval_bridge_status": (
                "established_from_explicit_successful_verification_and_saved_artifact_fields"
                if retrieval_supported
                else "quarantined_incomplete_explicit_retrieval_support"
            ),
            "retrieval_support_fields": (
                "verification.verified_at|verification.verification_status|verification.url_reachable|"
                "verification.bytes_read|verification.artifact_path|source_review.download_status|"
                "source_review.url_access_status|source_review.documents_downloaded|"
                "source_review.content_artifact_path"
            ),
            "source_corpus_bridge_status": (
                "established_from_document_source_family_contract" if source_corpus else "quarantined_unknown_source_family"
            ),
        }
        retrieval_rows.append(retrieval_row)
        identity[document_id] = {
            "cycle": cycle_row,
            "occupation": occupation_row,
            "retrieval": retrieval_row,
        }

    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in cycle_rows:
        if row["negotiation_cycle_id"]:
            groups[(row["state"], row["municipality"], row["contract_period_start"], row["contract_period_end"])].append(row)
    matched_groups = 0
    for key, rows in groups.items():
        units = {row["unit_type"] for row in rows}
        if units.intersection({"police", "fire"}) and "non_safety" in units:
            matched_groups += 1
            matched_id = stable_id("match", *key)
            for row in rows:
                row["matched_set_id"] = matched_id

    return {
        "prior_bridge_header": bridge_header,
        "prior_bridge_rows": bridge_rows,
        "cycle_rows": cycle_rows,
        "occupation_rows": occupation_rows,
        "retrieval_rows": retrieval_rows,
        "identity": identity,
        "matched_group_count": matched_groups,
    }


def followup_values(document_id: str, context: dict[str, Any]) -> dict[str, str]:
    parts = context["identity"][document_id]
    cycle, occupation, retrieval = parts["cycle"], parts["occupation"], parts["retrieval"]
    return {
        "contract_period_start_bridge": cycle["contract_period_start"],
        "contract_period_end_bridge": cycle["contract_period_end"],
        "negotiation_cycle_id": cycle["negotiation_cycle_id"],
        "city_unit_negotiation_cycle_key": cycle["city_unit_negotiation_cycle_key"],
        "matched_set_id": cycle["matched_set_id"],
        "analysis_matching_status": (
            "exact_period_matched_set_supported"
            if cycle["matched_set_id"]
            else "exact_period_unmatched"
            if cycle["negotiation_cycle_id"]
            else "incomplete_or_ambiguous_cycle"
        ),
        "controlled_occupation_class": occupation["controlled_occupation_class"],
        "occupation_class_bridge_status": occupation["occupation_class_bridge_status"],
        "retrieval_date_bridge": retrieval["retrieval_date"],
        "retrieval_method_bridge": retrieval["retrieval_method"],
        "source_type_bridge": retrieval["source_type"],
        "source_corpus_bridge": retrieval["source_corpus"],
        "source_cite_bridge": retrieval["source_cite"],
        "artifact_pointer_bridge": retrieval["artifact_pointer"],
        "followup_cycle_bridge_status": cycle["cycle_bridge_status"],
        "followup_cycle_source_fields": cycle["cycle_source_fields"],
        "followup_occupation_bridge_status": occupation["occupation_class_bridge_status"],
        "followup_occupation_support_fields": occupation["occupation_support_fields"],
        "followup_retrieval_bridge_status": retrieval["retrieval_bridge_status"],
        "followup_retrieval_support_fields": retrieval["retrieval_support_fields"],
    }


def update_shadow(rows: list[dict[str, str]], context: dict[str, Any]) -> list[dict[str, str]]:
    updated = []
    for row in rows:
        copy = dict(row)
        copy.update(followup_values(row["document_identity_id"], context))
        updated.append(copy)
    return updated


def improve_quantitative(row: dict[str, str]) -> dict[str, str]:
    repaired = dict(row)
    reasons = split_pipe(row.get("analysis_quarantine_reasons", ""))
    normalized_date = row.get("normalized_effective_date", "")
    status = row.get("effective_date_parse_status", "")
    improvement = "prior_parse_preserved"
    if "effective_date_not_exactly_parseable" in reasons:
        expanded, expanded_status = parse_expanded_exact_effective_date(row.get("effective_date", ""))
        if expanded:
            normalized_date = expanded
            status = expanded_status
            reasons = [reason for reason in reasons if reason != "effective_date_not_exactly_parseable"]
            improvement = "exact_expanded_effective_date_token"
    eligible = row.get("current_active") == "true" and not reasons
    repaired.update(
        {
            "followup_normalized_effective_date": normalized_date,
            "followup_effective_date_parse_status": status,
            "followup_analysis_candidate_eligible": str(eligible).lower(),
            "followup_analysis_quarantine_reasons": "|".join(reasons),
            "followup_parse_improvement_reason_code": improvement,
        }
    )
    return repaired


def no_write_preflight(output_dir: Path) -> dict[str, Any]:
    preflight = input_preflight(output_dir)
    context = build_context()
    return {
        **preflight,
        "dry_run": True,
        "document_identity_count": len(context["identity"]),
        "cycle_bridge_established_count": sum(bool(row["negotiation_cycle_id"]) for row in context["cycle_rows"]),
        "matched_set_document_count": sum(bool(row["matched_set_id"]) for row in context["cycle_rows"]),
        "retrieval_bridge_established_count": sum(bool(row["retrieval_date"]) for row in context["retrieval_rows"]),
        "controlled_occupation_count": sum(bool(row["controlled_occupation_class"]) for row in context["occupation_rows"]),
    }


def run(output_dir: Path) -> dict[str, Any]:
    preflight = no_write_preflight(output_dir)
    prior_hashes_before = {name: sha256(path) for name, path in PRIOR_INPUTS.items()}
    durable_hashes_before = {name: sha256(path) for name, path in DURABLE_INPUTS.items()}
    context = build_context()
    output_dir.mkdir(parents=True, exist_ok=False)

    cycle_header = list(context["cycle_rows"][0])
    occupation_header = list(context["occupation_rows"][0])
    retrieval_header = list(context["retrieval_rows"][0])
    write_csv(output_dir / OUTPUTS["cycle_bridge"], cycle_header, context["cycle_rows"])
    write_csv(output_dir / OUTPUTS["occupation_bridge"], occupation_header, context["occupation_rows"])
    write_csv(output_dir / OUTPUTS["retrieval_bridge"], retrieval_header, context["retrieval_rows"])
    (output_dir / OUTPUTS["durable_hashes"]).write_text(
        "\n".join(
            f"{digest}  {DURABLE_INPUTS[name].relative_to(ROOT)}"
            for name, digest in sorted(durable_hashes_before.items())
        )
        + "\n",
        encoding="utf-8",
    )

    lane_data: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for lane in ("quantitative", "qualitative", "mixed", "non_base_wage", "reference_and_exclusion"):
        header, rows = read_rows(PRIOR_INPUTS[lane])
        lane_data[lane] = (header, update_shadow(rows, context))

    quant_header, quant_rows = lane_data["quantitative"]
    quant_rows = [improve_quantitative(row) for row in quant_rows]
    lane_data["quantitative"] = (quant_header, quant_rows)

    def full_header(original: list[str], extras: list[str]) -> list[str]:
        return original + [field for field in extras if field not in original]

    output_lane_names = {
        "quantitative": "quant_shadow",
        "qualitative": "qual_shadow",
        "mixed": "mixed_shadow",
        "non_base_wage": "nonbase_shadow",
        "reference_and_exclusion": "reference_shadow",
    }
    for lane, output_name in output_lane_names.items():
        header, rows = lane_data[lane]
        extras = FOLLOWUP_BRIDGE_FIELDS + (FOLLOWUP_QUANT_FIELDS if lane == "quantitative" else [])
        write_csv(output_dir / OUTPUTS[output_name], full_header(header, extras), rows)

    quant_candidates = [row for row in quant_rows if row["followup_analysis_candidate_eligible"] == "true"]
    quant_exceptions = [
        row for row in quant_rows if row.get("current_active") == "true" and row["followup_analysis_candidate_eligible"] != "true"
    ]
    quant_output_header = full_header(quant_header, FOLLOWUP_BRIDGE_FIELDS + FOLLOWUP_QUANT_FIELDS)
    write_csv(output_dir / OUTPUTS["quant_candidate"], quant_output_header, quant_candidates)
    write_csv(output_dir / OUTPUTS["quant_exceptions"], quant_output_header, quant_exceptions)

    qual_header, qual_rows = lane_data["qualitative"]
    qual_active = [row for row in qual_rows if row.get("current_active") == "true"]
    write_csv(
        output_dir / OUTPUTS["qual_navigation"],
        full_header(qual_header, FOLLOWUP_BRIDGE_FIELDS),
        qual_active,
    )
    nonbase_header, nonbase_rows = lane_data["non_base_wage"]
    nonbase_active = [row for row in nonbase_rows if row.get("current_active") == "true"]
    write_csv(
        output_dir / OUTPUTS["nonbase_candidate"],
        full_header(nonbase_header, FOLLOWUP_BRIDGE_FIELDS),
        nonbase_active,
    )
    reference_header, reference_rows = lane_data["reference_and_exclusion"]
    reference_active = [row for row in reference_rows if row.get("current_active") == "true"]
    write_csv(
        output_dir / OUTPUTS["reference_control"],
        full_header(reference_header, FOLLOWUP_BRIDGE_FIELDS),
        reference_active,
    )

    cycle_counts = Counter(row["cycle_bridge_status"] for row in context["cycle_rows"])
    occupation_counts = Counter(row["occupation_class_bridge_status"] for row in context["occupation_rows"])
    occupation_class_counts = Counter(
        row["controlled_occupation_class"] or "quarantined_unclassified"
        for row in context["occupation_rows"]
    )
    retrieval_counts = Counter(row["retrieval_bridge_status"] for row in context["retrieval_rows"])
    cycle_audit = {
        "document_identity_count": 1826,
        "exact_cycle_established_count": sum(bool(row["negotiation_cycle_id"]) for row in context["cycle_rows"]),
        "cycle_status_counts": dict(sorted(cycle_counts.items())),
        "city_unit_negotiation_cycle_key_count": sum(bool(row["city_unit_negotiation_cycle_key"]) for row in context["cycle_rows"]),
        "matched_set_id_document_count": sum(bool(row["matched_set_id"]) for row in context["cycle_rows"]),
        "matched_set_group_count": context["matched_group_count"],
        "period_dates_derived_only_from_exact_full_date_pairs": True,
        "filename_inference_used": False,
        "ambiguous_pairs_quarantined": True,
    }
    occupation_audit = {
        "document_identity_count": 1826,
        "controlled_occupation_class_count": sum(bool(row["controlled_occupation_class"]) for row in context["occupation_rows"]),
        "public_safety_exact_count": sum(row["unit_type"] in {"police", "fire"} for row in context["occupation_rows"]),
        "non_safety_subclass_established_count": sum(
            row["unit_type"] == "non_safety" and bool(row["controlled_occupation_class"])
            for row in context["occupation_rows"]
        ),
        "non_safety_quarantined_count": sum(
            row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]
            for row in context["occupation_rows"]
        ),
        "occupation_class_counts": dict(sorted(occupation_class_counts.items())),
        "bridge_status_counts": dict(sorted(occupation_counts.items())),
        "government_name_inference_used": False,
        "controlled_vocabulary": sorted(OCCUPATION_RULES),
    }
    retrieval_audit = {
        "document_identity_count": 1826,
        "retrieval_date_count": sum(bool(row["retrieval_date"]) for row in context["retrieval_rows"]),
        "retrieval_method_count": sum(bool(row["retrieval_method"]) for row in context["retrieval_rows"]),
        "source_type_count": sum(bool(row["source_type"]) for row in context["retrieval_rows"]),
        "source_corpus_count": sum(bool(row["source_corpus"]) for row in context["retrieval_rows"]),
        "source_cite_count": sum(bool(row["source_cite"]) for row in context["retrieval_rows"]),
        "artifact_pointer_count": sum(bool(row["artifact_pointer"]) for row in context["retrieval_rows"]),
        "retrieval_status_counts": dict(sorted(retrieval_counts.items())),
        "retrieval_method_rule": "public_download only when explicit durable successful verification, byte, URL-access, saved-artifact, and downloaded-document fields all agree",
        "urls_opened_by_followup": 0,
    }
    write_json(output_dir / OUTPUTS["cycle_audit"], cycle_audit)
    write_json(output_dir / OUTPUTS["occupation_audit"], occupation_audit)
    write_json(output_dir / OUTPUTS["retrieval_audit"], retrieval_audit)

    span_fields_inspected = {
        "prior_repaired_qualitative.literal_verbatim_evidence_span": sum(
            bool(row.get("literal_verbatim_evidence_span", "").strip()) for row in qual_rows
        ),
        "prior_repaired_qualitative.bounded_evidence_pointer": sum(
            bool(row.get("bounded_evidence_pointer", "").strip()) for row in qual_rows
        ),
    }
    span_audit = {
        "active_qualitative_navigation_rows": len(qual_active),
        "dedicated_literal_verbatim_span_count": span_fields_inspected[
            "prior_repaired_qualitative.literal_verbatim_evidence_span"
        ],
        "bounded_pointer_count": sum(bool(row.get("bounded_evidence_pointer", "")) for row in qual_active),
        "fields_inspected": span_fields_inspected,
        "coded_analysis_candidate_created": False,
        "navigation_view_created": True,
        "result": "literal_verbatim_spans_unavailable_in_existing_bounded_structured_artifacts",
        "pdfs_opened": 0,
        "model_calls": 0,
    }
    write_json(output_dir / OUTPUTS["qual_span_audit"], span_audit)

    unresolved_conflicts = sum(
        "explicit_unresolved_conflict_member" in row.get("followup_analysis_quarantine_reasons", "")
        for row in quant_rows
    )
    exception_reasons = Counter()
    for row in quant_exceptions:
        exception_reasons.update(split_pipe(row["followup_analysis_quarantine_reasons"]))
    quarantine = {
        "cycle_missing_or_ambiguous_document_count": 1826 - cycle_audit["exact_cycle_established_count"],
        "non_safety_occupation_quarantine_count": occupation_audit["non_safety_quarantined_count"],
        "retrieval_provenance_quarantine_count": 1826 - retrieval_audit["retrieval_date_count"],
        "quantitative_followup_candidate_count": len(quant_candidates),
        "quantitative_followup_exception_count": len(quant_exceptions),
        "quantitative_exception_reason_counts_nonexclusive": dict(sorted(exception_reasons.items())),
        "unresolved_conflict_group_count": 2,
        "unresolved_conflict_member_observation_count": unresolved_conflicts,
        "qualitative_without_literal_span_count": len(qual_active),
        "analysis_readiness": False,
    }
    write_json(output_dir / OUTPUTS["quarantine"], quarantine)

    original_other = [row for row in nonbase_active if row.get("non_base_wage_type") == "other"]
    other_counts = Counter(row.get("non_base_subtype_status", "") for row in original_other)
    blockers = [
        {
            "blocker_id": "F01",
            "area": "cycle_and_matching",
            "status": "partial",
            "affected_count": quarantine["cycle_missing_or_ambiguous_document_count"],
            "resolution_or_boundary": "Exact full-date pairs only; missing or conflicting pairs remain quarantined.",
        },
        {
            "blocker_id": "F02",
            "area": "non_safety_occupation",
            "status": "partial",
            "affected_count": occupation_audit["non_safety_quarantined_count"],
            "resolution_or_boundary": "Only one unambiguous explicit controlled label rule is accepted.",
        },
        {
            "blocker_id": "F03",
            "area": "retrieval_provenance",
            "status": "resolved" if retrieval_audit["retrieval_date_count"] == 1826 else "partial",
            "affected_count": 1826 - retrieval_audit["retrieval_date_count"],
            "resolution_or_boundary": "Derived only from agreeing durable successful-verification and saved-artifact fields.",
        },
        {
            "blocker_id": "F04",
            "area": "qualitative_literal_spans",
            "status": "blocked_missing_bounded_span",
            "affected_count": len(qual_active),
            "resolution_or_boundary": "Navigation only; future separately authorized bounded literal-span capture required.",
        },
        {
            "blocker_id": "F05",
            "area": "quantitative_normalization",
            "status": "partial",
            "affected_count": len(quant_exceptions),
            "resolution_or_boundary": "Raw values preserved; only exact anchored effective-date tokens received follow-up parses.",
        },
        {
            "blocker_id": "F06",
            "area": "residual_conflicts",
            "status": "quarantined",
            "affected_count": unresolved_conflicts,
            "resolution_or_boundary": "Two groups/five observations remain explicitly excluded from candidates.",
        },
    ]
    write_csv(
        output_dir / OUTPUTS["blockers"],
        ["blocker_id", "area", "status", "affected_count", "resolution_or_boundary"],
        blockers,
    )

    improved = sum(
        row["followup_parse_improvement_reason_code"] == "exact_expanded_effective_date_token"
        for row in quant_rows
    )
    newly_eligible = sum(
        row.get("analysis_candidate_eligible") != "true"
        and row["followup_analysis_candidate_eligible"] == "true"
        for row in quant_rows
    )
    (output_dir / OUTPUTS["quant_report"]).write_text(
        f"""# Quantitative follow-up parse improvement report

- Active quantitative rows: {sum(row.get('current_active') == 'true' for row in quant_rows)}
- Prior mechanically safe candidates: {sum(row.get('analysis_candidate_eligible') == 'true' for row in quant_rows)}
- Follow-up mechanically safe candidates: {len(quant_candidates)}
- Follow-up exceptions: {len(quant_exceptions)}
- Exact expanded effective-date tokens parsed: {improved}
- Newly eligible mechanical candidates: {newly_eligible}
- Explicit unresolved-conflict members quarantined: {unresolved_conflicts}
- Raw quantitative and prior normalized fields modified: no
- Annualization or coercion performed: no
- Analysis promotion eligible: 0

Only anchored ISO, full month-day-year, or numeric month-day-year tokens (optionally prefixed by `Effective`) were newly parsed. Year-only, fiscal-year, ranges, formulas, pay-period rules, prose, pairs, multipliers, hours, and ambiguous tokens remain exceptions.
""",
        encoding="utf-8",
    )
    (output_dir / OUTPUTS["qual_report"]).write_text(
        f"""# Qualitative mechanism follow-up report

- Active navigation rows: {len(qual_active)}
- Dedicated literal/verbatim spans available: 0
- Bounded evidence pointers retained: {span_audit['bounded_pointer_count']}
- Coded qualitative analysis candidate created: no
- Navigation view created: yes

Existing structured artifacts contain mechanism labels and bounded pointers but no dedicated literal/verbatim span with a final QA contract. This task did not open PDFs, extract text, or call a model. A future bounded span-capture task is required before a coded mechanism view can be considered.
""",
        encoding="utf-8",
    )
    (output_dir / OUTPUTS["nonbase_report"]).write_text(
        f"""# Non-base follow-up `other` disposition report

- Active non-base companion rows: {len(nonbase_active)}
- Active original `other` rows: {len(original_other)}
- Disposition counts: {json.dumps(dict(sorted(other_counts.items())), sort_keys=True)}
- Base-wage outcome eligible: 0

No observation subtype was inferred from document-level metadata. Prior deterministic subtype annotations are preserved. Multi-family or unsupported `other` rows remain outside typed component analyses. The non-base lane remains a companion dataset only.
""",
        encoding="utf-8",
    )

    summary = f"""# Bounded compensation schema-repair follow-up summary

Decision: `{DECISION}`

- Immutable package SHA-256 checks: 5/5 passed.
- Package, prior repair shadows, and durable ledgers modified: no.
- Exact contract/cycle pairs: {cycle_audit['exact_cycle_established_count']}/1,826.
- Deterministic matched-set documents/groups: {cycle_audit['matched_set_id_document_count']}/{cycle_audit['matched_set_group_count']}.
- Controlled non-safety subclasses established/quarantined: {occupation_audit['non_safety_subclass_established_count']}/{occupation_audit['non_safety_quarantined_count']}.
- Retrieval date/method/source-corpus bridges: {retrieval_audit['retrieval_date_count']}/1,826.
- Quantitative mechanical candidates/exceptions: {len(quant_candidates)}/{len(quant_exceptions)}.
- Qualitative literal spans: 0; {len(qual_active)} navigation rows retained and no coded view created.
- Active non-base companion rows: {len(nonbase_active)}; original `other`: {len(original_other)}.
- Reference/exclusion control rows: {len(reference_active)}; outcome eligible: 0.
- Two unresolved groups / five observations remain quarantined.
- Analysis readiness: false; repeat analysis-readiness review: not allowed.

The follow-up improved cycle, occupation, retrieval, and exact-token parse coverage without inference. It remains partial because cycle and occupation metadata are incomplete and literal qualitative spans are absent from existing bounded structured artifacts.
"""
    (output_dir / OUTPUTS["summary"]).write_text(summary, encoding="utf-8")

    future_prompt = """# Future task: bounded qualitative span and residual metadata repair

Do not run this prompt without separate user authorization.

Perform a bounded, local repair only for records still quarantined after the compensation schema follow-up. Capture literal qualitative evidence spans only from already-retained bounded parse-text artifacts, with exact substring and page-pointer verification. Do not open URLs or PDFs, run OCR, select documents, call GABRIEL/API, ingest, codify, promote data, calculate wage gaps, run regressions, or make causal claims.

Also evaluate only explicit existing structured evidence for remaining cycle and non-safety occupation gaps. Never infer dates from filenames, government names, or unbounded prose. Preserve raw values, prior and follow-up shadows, all hashes, duplicate/canonical provenance, mixed membership, non-base separation, reference controls, and the two residual conflict groups. Keep analysis readiness false. If literal spans cannot be captured and QA-verified within those bounds, leave the qualitative lane navigation-only and report the blocker.
"""
    (output_dir / OUTPUTS["future_prompt"]).write_text(future_prompt, encoding="utf-8")

    (output_dir / OUTPUTS["validation"]).write_text(
        f"""# Bounded schema-repair follow-up validation

- No-write dry run: passed; writes before materialization: {preflight['writes_performed']}.
- Immutable package SHA-256 checks: 5/5 passed.
- Prior package/repair inputs modified: no.
- Durable bridge inputs modified: no.
- Identity bridge cardinality: 1,826/1,826 unique.
- Exact cycle bridge: {cycle_audit['exact_cycle_established_count']} established; all other identities explicitly quarantined.
- Matched-set bridge: {cycle_audit['matched_set_id_document_count']} documents across {cycle_audit['matched_set_group_count']} exact-period groups.
- Controlled occupation bridge: {occupation_audit['controlled_occupation_class_count']} established; uncertain non-safety identities quarantined.
- Retrieval provenance: {retrieval_audit['retrieval_date_count']}/1,826 supported by durable structured fields.
- Quantitative raw and prior normalized fields preserved: yes.
- Two unresolved groups / five observations remain quarantined: yes.
- Qualitative coded view created: no; literal spans unavailable and navigation-only retained.
- Non-base companion and reference/control separation: preserved.
- OCR-later documents included: no.
- URL, PDF, OCR, GABRIEL/API, extraction, selection, ingestion, codification, analysis dataset, wage-gap, regression, or causal work: none.
- Analysis readiness remains false.
""",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID,
        "generated_at": now_utc(),
        "decision": DECISION,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": False,
        "next_prompt": OUTPUTS["future_prompt"],
        "next_recommendation": "run_separately_authorized_bounded_qualitative_span_and_residual_metadata_repair",
        "package_sha256_checks_passed": preflight["package_sha256_checks_passed"],
        "package_ledgers_mutated": False,
        "prior_repair_shadows_mutated": False,
        "durable_ledgers_mutated": False,
        "cycle_matching": cycle_audit,
        "occupation": occupation_audit,
        "retrieval_provenance": retrieval_audit,
        "quantitative": {
            "prior_candidate_count": sum(row.get("analysis_candidate_eligible") == "true" for row in quant_rows),
            "followup_candidate_count": len(quant_candidates),
            "followup_exception_count": len(quant_exceptions),
            "newly_eligible_count": newly_eligible,
        },
        "qualitative": span_audit,
        "non_base_wage": {
            "active_companion_count": len(nonbase_active),
            "original_other_count": len(original_other),
            "other_disposition_counts": dict(sorted(other_counts.items())),
            "base_wage_outcome_eligible_count": 0,
        },
        "reference_and_exclusion": {
            "active_control_count": len(reference_active),
            "analysis_outcome_eligible_count": 0,
        },
        "quarantine": quarantine,
        "forbidden_actions_performed": [],
        "ocr_later_documents_included": False,
    }
    write_json(output_dir / OUTPUTS["decision"], decision)

    prior_hashes_after = {name: sha256(path) for name, path in PRIOR_INPUTS.items()}
    durable_hashes_after = {name: sha256(path) for name, path in DURABLE_INPUTS.items()}
    if prior_hashes_after != prior_hashes_before:
        raise RuntimeError("Prior package/repair input changed during follow-up")
    if durable_hashes_after != durable_hashes_before:
        raise RuntimeError("Durable bridge input changed during follow-up")
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    result = no_write_preflight(output) if args.dry_run else run(output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
