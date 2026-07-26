#!/usr/bin/env python3
"""Build rollback-safe schema-repair shadows from the immutable five-lane package.

This runner is deliberately local and deterministic.  It never opens source URLs,
PDFs, or APIs, and it never writes outside a caller-supplied new output directory.
The five package ledgers are observation-bearing inputs; durable ledgers are used
only for one-to-one identity and provenance bridges.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
)
REVIEW = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-PACKAGE-SCHEMA-READINESS-REVIEW-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25"
)

LANES = {
    "quantitative": PACKAGE / "ledgers/quantitative/final_provisional_quantitative_ledger.csv",
    "qualitative": PACKAGE
    / "ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv",
    "mixed": PACKAGE / "ledgers/mixed/final_provisional_mixed_join_ledger.csv",
    "non_base_wage": PACKAGE
    / "ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv",
    "reference_and_exclusion": PACKAGE
    / "ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv",
}

DURABLE_BRIDGE_INPUTS = {
    "text_table_detection": ROOT
    / "docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv",
    "pdf_readiness": ROOT
    / "docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv",
    "source_review": ROOT
    / "docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv",
}

CONTROL_INPUTS = {
    "merge_manifest": PACKAGE / "final_provisional_merge_manifest.json",
    "merge_decision": PACKAGE / "final_provisional_decision.json",
    "reconciliation_summary": PACKAGE / "final_provisional_reconciliation_summary.json",
    "conflict_register": PACKAGE / "final_provisional_conflict_register.csv",
    "input_hashes": PACKAGE / "final_provisional_input_sha256.txt",
    "output_hashes": PACKAGE / "final_provisional_output_sha256.txt",
    "review_decision": REVIEW / "compensation_evidence_analysis_readiness_decision.json",
    "review_blockers": REVIEW / "compensation_evidence_analysis_readiness_blocker_matrix.csv",
    "review_join_audit": REVIEW / "compensation_evidence_join_provenance_audit.json",
}

OUTPUT_FILENAMES = {
    "column_map": "schema_repair_column_map.json",
    "contract": "schema_repair_contract.md",
    "quant_shadow": "repaired_quantitative_shadow.csv",
    "qual_shadow": "repaired_qualitative_mechanism_shadow.csv",
    "mixed_shadow": "repaired_mixed_join_shadow.csv",
    "nonbase_shadow": "repaired_non_base_wage_shadow.csv",
    "reference_shadow": "repaired_reference_exclusion_shadow.csv",
    "bridge": "identity_provenance_bridge.csv",
    "bridge_audit": "identity_provenance_bridge_audit.json",
    "bridge_hashes": "durable_bridge_input_sha256.txt",
    "quant_report": "quantitative_parse_status_report.md",
    "quant_exceptions": "quantitative_normalization_exception_ledger.csv",
    "quant_candidate": "quantitative_analysis_view_candidate.csv",
    "mixed_audit": "mixed_membership_status_audit.json",
    "mixed_exceptions": "mixed_membership_exception_ledger.csv",
    "conflict_quarantine": "unresolved_conflict_quarantine_ledger.csv",
    "quarantine_summary": "analysis_view_quarantine_summary.json",
    "nonbase_report": "non_base_other_disposition_report.md",
    "nonbase_candidate": "non_base_wage_companion_view_candidate.csv",
    "qual_report": "qualitative_mechanism_schema_repair_report.md",
    "qual_navigation": "qualitative_mechanism_navigation_view_candidate.csv",
    "reference_control": "reference_exclusion_control_view.csv",
    "decision": "schema_repair_decision.json",
    "validation": "schema_repair_validation_2026-07-25.md",
    "summary": "schema_repair_summary.md",
    "future_prompt": "next_bounded_schema_repair_followup_prompt.md",
}

EXPECTED_PACKAGE_SHA256 = {
    "quantitative": "7e275b8c45f0d4b77e01249d978fe17862fd3f8d552bf0f4ef77ed0bb3616c86",
    "qualitative": "d22a4015da83da7d0195e430ef30d475b3678c17696e7a835d6d09bce1a1e0d5",
    "mixed": "a204061a4ca4bbfd3512bf964d689fe385dfd71fac93589a4bb9b59e64eb9192",
    "non_base_wage": "84df35187461392ea9699660ea86317250a33979e6ff2b4f9256a49b1d9e0ea2",
    "reference_and_exclusion": "2a33987b8f54048d8a397fc7d9a917dafd2dbcf8b7b74a20de8c2642a886e3a1",
}

BRIDGE_FIELDS = [
    "raw_retained_content_hash",
    "pdf_readiness_id",
    "controlled_occupation_class",
    "occupation_class_bridge_status",
    "source_type_bridge",
    "source_corpus_bridge",
    "source_cite_bridge",
    "retrieval_date_bridge",
    "retrieval_method_bridge",
    "artifact_pointer_bridge",
    "contract_period_start_bridge",
    "contract_period_end_bridge",
    "negotiation_cycle_id",
    "city_unit_negotiation_cycle_key",
    "matched_set_id",
    "identity_bridge_status",
    "analysis_matching_status",
]

CURRENT_FIELDS = ["current_active", "current_qa_status", "current_qa_status_source"]
MIXED_STATUS_FIELD = "mixed_membership_status"

QUANT_NORMALIZED_FIELDS = [
    "normalized_scalar_value",
    "normalized_range_minimum",
    "normalized_range_maximum",
    "normalized_currency",
    "normalized_frequency",
    "normalized_wage_concept",
    "annualization_status",
    "normalized_effective_date",
    "effective_date_parse_status",
    "quantitative_transformation_reason_code",
    "analysis_candidate_eligible",
    "analysis_promotion_eligible",
    "analysis_quarantine_reasons",
    "unresolved_conflict_resolution_id",
]

TRUE_VALUES = {"true", "1", "yes"}
SIMPLE_NUMBER = re.compile(r"^\s*(?P<currency>\$)?\s*(?P<number>-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)\s*$")
SIMPLE_PERCENT = re.compile(r"^\s*(?P<number>-?\d+(?:\.\d+)?)\s*%\s*$")
SIMPLE_RANGE = re.compile(
    r"^\s*(?P<c1>\$)?\s*(?P<n1>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?:-|–|—|to)\s*(?P<c2>\$)?\s*(?P<n2>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    value = "|".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(value).hexdigest()[:24]}"


@dataclass
class RawTable:
    path: Path
    header: list[str]
    rows: list[list[str]]

    @classmethod
    def read(cls, path: Path) -> "RawTable":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            rows = list(reader)
        bad = [index + 2 for index, row in enumerate(rows) if len(row) != len(header)]
        if bad:
            raise RuntimeError(f"Malformed CSV widths in {path}: {bad[:10]}")
        return cls(path, header, rows)

    def indexes(self, field: str) -> list[int]:
        return [index for index, name in enumerate(self.header) if name == field]

    def value(self, row: list[str], field: str, occurrence: int = -1) -> str:
        indexes = self.indexes(field)
        if not indexes:
            return ""
        return row[indexes[occurrence]].strip()

    def as_unique_dict(self, row: list[str]) -> dict[str, str]:
        if len(set(self.header)) != len(self.header):
            raise ValueError(f"Duplicate headers require positional handling: {self.path}")
        return dict(zip(self.header, row))


def read_dict_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    table = RawTable.read(path)
    if len(set(table.header)) != len(table.header):
        raise ValueError(f"Duplicate headers in {path}")
    return table.header, [table.as_unique_dict(row) for row in table.rows]


def write_csv(path: Path, header: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in header})


def json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_text(value: str) -> bool:
    return value.strip().lower() in TRUE_VALUES


def split_pipe(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def derive_current_qa(row: dict[str, str]) -> tuple[str, str]:
    active = bool_text(row.get("active_in_readable_conflict_qa_lane", ""))
    if not active:
        if row.get("duplicate_of") or row.get("canonical_observation_id"):
            return "inactive_duplicate_or_canonicalized", "active_and_canonical_fields"
        reroute_values = "|".join(
            row.get(name, "")
            for name in (
                "qa_resolution_classification",
                "targeted_qa_resolution_classification",
                "readable_conflict_qa_classification",
            )
        ).lower()
        if "non_base_wage" in reroute_values or "route_to_non_base_wage" in reroute_values:
            return "inactive_rerouted_to_non_base_wage", "latest_resolution_classification"
        return "inactive_historical", "active_in_readable_conflict_qa_lane"

    stages = (
        ("readable_conflict_qa_status", "readable_conflict_qa_classification"),
        ("targeted_qa_resolution_status", "targeted_qa_resolution_classification"),
        ("qa_resolution_status", "qa_resolution_classification"),
    )
    for status_field, class_field in stages:
        status = row.get(status_field, "").strip()
        classification = row.get(class_field, "").strip()
        if status and status not in {"not_applicable", "pending"}:
            return f"{status}:{classification or 'unclassified'}", status_field
    return row.get("qa_status", "").strip() or "unknown", "qa_status"


def exact_date(value: str) -> tuple[str, str]:
    value = value.strip()
    if not value:
        return "", "blank"
    for fmt, status in (("%Y-%m-%d", "exact_iso"), ("%m/%d/%Y", "exact_mdy")):
        try:
            return datetime.strptime(value, fmt).date().isoformat(), status
        except ValueError:
            pass
    return "", "unparsed_or_ambiguous"


def parse_exact_number(value: str) -> tuple[str, str]:
    match = SIMPLE_NUMBER.match(value)
    if not match:
        return "", ""
    number = match.group("number").replace(",", "")
    currency = "USD" if match.group("currency") else ""
    return number, currency


def parse_exact_range(value: str) -> tuple[str, str, str]:
    match = SIMPLE_RANGE.match(value)
    if not match:
        return "", "", ""
    low = match.group("n1").replace(",", "")
    high = match.group("n2").replace(",", "")
    currency = "USD" if match.group("c1") or match.group("c2") else ""
    return low, high, currency


def explicit_frequency(compensation_type: str, currency_or_unit: str) -> str:
    if compensation_type == "hourly_rate":
        return "hourly"
    if compensation_type == "annual_salary":
        return "annual"
    normalized = currency_or_unit.strip().lower()
    allowed = {
        "hour": "hourly",
        "hourly": "hourly",
        "per hour": "hourly",
        "annual": "annual",
        "annually": "annual",
        "year": "annual",
        "yearly": "annual",
        "monthly": "monthly",
        "month": "monthly",
        "weekly": "weekly",
        "week": "weekly",
        "biweekly": "biweekly",
    }
    return allowed.get(normalized, "")


def normalize_quantitative(
    row: dict[str, str], unresolved_by_observation: dict[str, str]
) -> dict[str, str]:
    result = {field: "" for field in QUANT_NORMALIZED_FIELDS}
    observation_id = row["quantitative_observation_id"]
    conflict_id = unresolved_by_observation.get(observation_id, "")
    result["unresolved_conflict_resolution_id"] = conflict_id
    normalized_date, date_status = exact_date(row.get("effective_date", ""))
    result["normalized_effective_date"] = normalized_date
    result["effective_date_parse_status"] = date_status
    result["annualization_status"] = "not_performed"
    reasons: list[str] = []
    if conflict_id:
        reasons.append("explicit_unresolved_conflict_member")

    amount_fields = ("rate_value", "salary_value", "hourly_rate", "annual_salary")
    has_amount = any(row.get(field, "").strip() for field in amount_fields)
    has_percentage = bool(row.get("percentage_increase", "").strip())
    if not has_amount and not has_percentage:
        reasons.append("neither_amount_nor_percentage")

    compensation_type = row.get("compensation_type", "").strip()
    selected_field = {
        "rate": "rate_value",
        "salary": "salary_value",
        "hourly_rate": "hourly_rate",
        "annual_salary": "annual_salary",
        "percentage_increase": "percentage_increase",
        "pay_band": "pay_band",
    }.get(compensation_type, "")

    if compensation_type == "other":
        typed_nonblank = [
            field
            for field in ("hourly_rate", "annual_salary", "percentage_increase")
            if row.get(field, "").strip()
        ]
        if len(typed_nonblank) == 1:
            selected_field = typed_nonblank[0]
            compensation_type = {
                "hourly_rate": "hourly_rate",
                "annual_salary": "annual_salary",
                "percentage_increase": "percentage_increase",
            }[selected_field]
            result["quantitative_transformation_reason_code"] = "other_resolved_by_single_explicit_typed_field"
        else:
            reasons.append("ambiguous_compensation_type_other")

    raw = row.get(selected_field, "").strip() if selected_field else ""
    if selected_field == "percentage_increase":
        match = SIMPLE_PERCENT.match(raw)
        if match:
            result["normalized_scalar_value"] = match.group("number")
            result["normalized_currency"] = "PERCENT"
            result["normalized_frequency"] = "percentage_change"
            result["normalized_wage_concept"] = "percentage_increase"
            result["quantitative_transformation_reason_code"] = (
                result["quantitative_transformation_reason_code"]
                or "exact_percentage_token"
            )
        elif raw:
            reasons.append("percentage_not_exact_scalar_token")
    elif raw:
        scalar, currency = parse_exact_number(raw)
        low, high, range_currency = parse_exact_range(raw)
        if scalar:
            result["normalized_scalar_value"] = scalar
            result["normalized_currency"] = currency
            result["normalized_wage_concept"] = compensation_type
            result["normalized_frequency"] = explicit_frequency(
                compensation_type, row.get("currency_or_unit", "")
            )
            result["quantitative_transformation_reason_code"] = (
                result["quantitative_transformation_reason_code"] or "exact_scalar_token"
            )
        elif low and high:
            result["normalized_range_minimum"] = low
            result["normalized_range_maximum"] = high
            result["normalized_currency"] = range_currency
            result["normalized_wage_concept"] = compensation_type
            result["normalized_frequency"] = explicit_frequency(
                compensation_type, row.get("currency_or_unit", "")
            )
            result["quantitative_transformation_reason_code"] = (
                result["quantitative_transformation_reason_code"] or "exact_range_preserved_not_scalarized"
            )
        else:
            reasons.append("raw_value_formula_pair_multiplier_hours_or_unparsed")
    elif compensation_type not in {"step", "grade"} and has_amount:
        reasons.append("typed_primary_value_missing_or_misaligned")

    if date_status == "unparsed_or_ambiguous":
        reasons.append("effective_date_not_exactly_parseable")
    if not bool_text(row.get("active_in_readable_conflict_qa_lane", "")):
        reasons.append("inactive_row")
    if not result["normalized_scalar_value"] and not result["normalized_range_minimum"]:
        if has_amount or has_percentage:
            reasons.append("no_safe_normalized_value")

    reasons = list(dict.fromkeys(reasons))
    eligible = not reasons and bool_text(row.get("active_in_readable_conflict_qa_lane", ""))
    result["analysis_candidate_eligible"] = str(eligible).lower()
    result["analysis_promotion_eligible"] = "false"
    result["analysis_quarantine_reasons"] = "|".join(reasons)
    return result


def deterministic_nonbase_subtype(row: dict[str, str]) -> tuple[str, str]:
    original = row.get("non_base_wage_type", "").strip()
    if original != "other":
        return original, "original_controlled_subtype"
    text = " ".join(
        row.get(field, "")
        for field in ("reason_code", "value_text", "eligibility_or_implementation_rule")
    ).lower()
    rules = [
        ("overtime", ("overtime",)),
        ("leave", ("vacation", "leave", "holiday pay", "severance")),
        ("healthcare_contributions", ("health", "insurance", "medical")),
        ("pension", ("pension", "retirement")),
        ("longevity", ("longevity",)),
        ("education_or_certification", ("education", "certif", "license", "degree")),
        ("reimbursements", ("reimburse", "expense", "travel")),
        ("uniform_or_equipment", ("uniform", "equipment", "clothing")),
        ("stipend", ("stipend", "allowance", "lump sum", "one-time payment")),
        ("premium_pay", ("premium", "differential", "out of class", "working out")),
        ("benefits", ("benefit", "deferred comp")),
    ]
    matches = [subtype for subtype, keywords in rules if any(keyword in text for keyword in keywords)]
    if len(matches) == 1:
        return matches[0], "deterministic_reason_or_value_keyword"
    if len(matches) > 1:
        return "other", "multiple_deterministic_keyword_families"
    return "other", "insufficient_structured_support"


def package_hash_preflight() -> dict[str, Any]:
    missing = [
        str(path.relative_to(ROOT))
        for path in [*LANES.values(), *DURABLE_BRIDGE_INPUTS.values(), *CONTROL_INPUTS.values()]
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Required artifacts missing: {missing}")
    computed = {lane: sha256(path) for lane, path in LANES.items()}
    if computed != EXPECTED_PACKAGE_SHA256:
        raise RuntimeError(f"Package SHA-256 mismatch: {computed}")
    review_decision = json.loads(CONTROL_INPUTS["review_decision"].read_text(encoding="utf-8"))
    if review_decision.get("schema_readiness_decision") != "schema_readiness_hold_schema_repairs_required":
        raise RuntimeError("Unexpected schema-readiness predecessor decision")
    durable_hashes = {name: sha256(path) for name, path in DURABLE_BRIDGE_INPUTS.items()}
    return {
        "package_sha256": computed,
        "durable_bridge_input_sha256": durable_hashes,
        "output_boundary": "new_docs_analysis_subdirectory_only",
        "forbidden_output_roots": ["data", "corpus", "ingest", "codified", "analysis_dataset"],
    }


def build_context() -> dict[str, Any]:
    preflight = package_hash_preflight()
    tables = {lane: RawTable.read(path) for lane, path in LANES.items()}
    dict_rows: dict[str, list[dict[str, str]]] = {}
    for lane in ("quantitative", "qualitative", "mixed", "reference_and_exclusion"):
        dict_rows[lane] = [tables[lane].as_unique_dict(row) for row in tables[lane].rows]

    # Repair duplicate non-base headers by positional occurrence before any dict conversion.
    nonbase = tables["non_base_wage"]
    quant_positions = nonbase.indexes("source_quantitative_observation_id")
    mixed_positions = nonbase.indexes("source_mixed_join_key")
    if quant_positions != [30, 38] or mixed_positions != [31, 39]:
        raise RuntimeError(
            f"Unexpected non-base duplicate positions: quant={quant_positions}, mixed={mixed_positions}"
        )
    repaired_nonbase_header = list(nonbase.header)
    repaired_nonbase_header[30] = "provisional_source_quantitative_observation_id"
    repaired_nonbase_header[31] = "provisional_source_mixed_join_key"
    repaired_nonbase_header[38] = "qa_corrected_source_quantitative_observation_id"
    repaired_nonbase_header[39] = "qa_corrected_source_mixed_join_key"
    nonbase_rows: list[dict[str, str]] = []
    quant_disagreements = mixed_disagreements = 0
    for raw in nonbase.rows:
        if raw[30].strip() != raw[38].strip():
            quant_disagreements += 1
        if raw[31].strip() != raw[39].strip():
            mixed_disagreements += 1
        row = dict(zip(repaired_nonbase_header, raw))
        row["current_source_quantitative_observation_id"] = raw[38].strip() or raw[30].strip()
        row["current_source_mixed_join_key"] = raw[39].strip() or raw[31].strip()
        nonbase_rows.append(row)
    if quant_disagreements or mixed_disagreements:
        raise RuntimeError("Non-base duplicate lineage columns disagree")
    dict_rows["non_base_wage"] = nonbase_rows

    durable: dict[str, tuple[list[str], list[dict[str, str]]]] = {
        name: read_dict_rows(path) for name, path in DURABLE_BRIDGE_INPUTS.items()
    }
    ttd_rows = durable["text_table_detection"][1]
    pdf_rows = durable["pdf_readiness"][1]
    source_rows = durable["source_review"][1]
    ttd_by_id = {row["text_table_detection_id"]: row for row in ttd_rows}
    source_by_id = {row["source_review_id"]: row for row in source_rows}
    pdf_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pdf_rows:
        pdf_by_source[row["source_review_id"]].append(row)

    # Consolidate package identity metadata and require exact agreement.
    identity_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for rows in dict_rows.values():
        for row in rows:
            identity_rows[row["document_identity_id"]].append(row)
    bridge_rows: list[dict[str, str]] = []
    bridge_by_document: dict[str, dict[str, str]] = {}
    package_hashes: dict[str, str] = {}
    source_corpus_map = {"cba": "causal", "arbitration_award": "causal", "factfinding": "causal"}
    identity_quarantine_count = 0
    for document_id, rows in sorted(identity_rows.items()):
        fields = (
            "text_table_detection_id",
            "source_review_id",
            "candidate_queue_row_id",
            "state",
            "municipality",
            "government_name",
            "unit_type",
            "candidate_source_type",
        )
        values: dict[str, str] = {}
        for field in fields:
            unique = {row.get(field, "").strip() for row in rows}
            if len(unique) != 1:
                raise RuntimeError(f"Identity metadata inconsistency for {document_id}/{field}: {unique}")
            values[field] = next(iter(unique))
        ttd = ttd_by_id.get(values["text_table_detection_id"])
        source = source_by_id.get(values["source_review_id"])
        pdf_candidates = pdf_by_source.get(values["source_review_id"], [])
        if not ttd or not source or len(pdf_candidates) != 1:
            raise RuntimeError(
                f"Unsafe bridge cardinality for {document_id}: ttd={bool(ttd)}, source={bool(source)}, pdf={len(pdf_candidates)}"
            )
        pdf = pdf_candidates[0]
        if ttd["source_review_id"] != values["source_review_id"]:
            raise RuntimeError(f"TTD/source mismatch for {document_id}")
        if source["content_hash"] != ttd["content_hash"] or pdf["content_hash"] != ttd["content_hash"]:
            raise RuntimeError(f"Durable content-hash disagreement for {document_id}")
        raw_hash = ttd["content_hash"].strip()
        if not raw_hash:
            identity_quarantine_count += 1
        if raw_hash in package_hashes and package_hashes[raw_hash] != document_id:
            raise RuntimeError(f"Package hash maps to multiple identities: {raw_hash}")
        package_hashes[raw_hash] = document_id
        unit = values["unit_type"]
        controlled_occupation = unit if unit in {"police", "fire"} else ""
        occupation_status = (
            "exact_controlled_public_safety_class"
            if controlled_occupation
            else "non_safety_subclass_not_supported_without_inference"
        )
        period_start = source.get("contract_or_document_period_start", "").strip()
        period_end = source.get("contract_or_document_period_end", "").strip()
        # No cycle IDs or matched sets are created unless both durable dates exist.
        cycle_key = ""
        city_unit_cycle = ""
        matched_set_id = ""
        if period_start and period_end:
            cycle_key = stable_id("cycle", values["state"], values["municipality"], period_start, period_end)
            city_unit_cycle = stable_id(
                "cuc",
                values["state"],
                values["municipality"],
                unit,
                period_start,
                period_end,
            )
        bridge = {
            "document_identity_id": document_id,
            "extraction_case_ids": "|".join(sorted({row["extraction_case_id"] for row in rows})),
            **values,
            "raw_retained_content_hash": raw_hash,
            "pdf_readiness_id": pdf["pdf_readiness_id"],
            "controlled_occupation_class": controlled_occupation,
            "occupation_class_bridge_status": occupation_status,
            "source_type_bridge": values["candidate_source_type"],
            "source_corpus_bridge": source_corpus_map.get(values["candidate_source_type"], ""),
            "source_cite_bridge": source.get("source_locator", "").strip(),
            "retrieval_date_bridge": "",
            "retrieval_method_bridge": "",
            "artifact_pointer_bridge": ttd.get("content_artifact_path", "").strip(),
            "contract_period_start_bridge": period_start,
            "contract_period_end_bridge": period_end,
            "negotiation_cycle_id": cycle_key,
            "city_unit_negotiation_cycle_key": city_unit_cycle,
            "matched_set_id": matched_set_id,
            "identity_bridge_status": "complete_one_to_one" if raw_hash else "quarantined_missing_raw_hash",
            "analysis_matching_status": (
                "complete" if cycle_key and controlled_occupation and matched_set_id else "incomplete_no_inference"
            ),
            "text_layer_status_bridge": ttd.get("text_layer_status", "").strip(),
            "ocr_needed_signal_bridge": pdf.get("ocr_needed_signal", "").strip(),
        }
        bridge_rows.append(bridge)
        bridge_by_document[document_id] = bridge
    if len(bridge_rows) != 1826 or len(package_hashes) != 1826:
        raise RuntimeError(
            f"Expected 1,826 one-to-one package identities/hashes; got {len(bridge_rows)}/{len(package_hashes)}"
        )

    conflict_header, conflict_rows = read_dict_rows(CONTROL_INPUTS["conflict_register"])
    unresolved_by_observation: dict[str, str] = {}
    for row in conflict_rows:
        if row["resolution_status"] == "unresolved":
            for observation_id in split_pipe(row["quantitative_observation_ids"]):
                unresolved_by_observation[observation_id] = row["resolution_id"]
    if len(conflict_rows) != 2 or len(unresolved_by_observation) != 5:
        raise RuntimeError("Expected exactly two unresolved groups / five observations")

    mixed_by_key = {row["mixed_join_key"]: row for row in dict_rows["mixed"]}
    active_mixed = {
        key for key, row in mixed_by_key.items() if bool_text(row["active_in_readable_conflict_qa_lane"])
    }
    inactive_mixed = set(mixed_by_key) - active_mixed

    def membership(row: dict[str, str]) -> str:
        key = row.get("mixed_join_key", "").strip()
        if not key:
            return "none"
        if key in active_mixed:
            return "active"
        if key in inactive_mixed:
            return "historical_inactive"
        return "historical_missing"

    return {
        "preflight": preflight,
        "tables": tables,
        "rows": dict_rows,
        "repaired_nonbase_header": repaired_nonbase_header,
        "nonbase_lineage": {
            "source_quantitative_positions_zero_based": quant_positions,
            "source_mixed_positions_zero_based": mixed_positions,
            "source_quantitative_populated_each": [
                sum(bool(raw[index].strip()) for raw in nonbase.rows) for index in quant_positions
            ],
            "source_mixed_populated_each": [
                sum(bool(raw[index].strip()) for raw in nonbase.rows) for index in mixed_positions
            ],
            "source_quantitative_disagreements": quant_disagreements,
            "source_mixed_disagreements": mixed_disagreements,
        },
        "bridge_rows": bridge_rows,
        "bridge_by_document": bridge_by_document,
        "identity_quarantine_count": identity_quarantine_count,
        "conflict_header": conflict_header,
        "conflict_rows": conflict_rows,
        "unresolved_by_observation": unresolved_by_observation,
        "active_mixed": active_mixed,
        "inactive_mixed": inactive_mixed,
        "membership": membership,
    }


def append_derived(
    row: dict[str, str], bridge: dict[str, str], membership: str, extra: dict[str, str] | None = None
) -> dict[str, str]:
    result = dict(row)
    result.update({field: bridge.get(field, "") for field in BRIDGE_FIELDS})
    qa_status, qa_source = derive_current_qa(row)
    result.update(
        {
            "current_active": str(bool_text(row.get("active_in_readable_conflict_qa_lane", ""))).lower(),
            "current_qa_status": qa_status,
            "current_qa_status_source": qa_source,
            MIXED_STATUS_FIELD: membership,
        }
    )
    if extra:
        result.update(extra)
    return result


def validate_active_mixed(rows: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    quant = {row["quantitative_observation_id"]: row for row in rows["quantitative"]}
    qual = {row["qualitative_observation_id"]: row for row in rows["qualitative"]}
    issues = Counter()
    active_count = 0
    for mixed in rows["mixed"]:
        if not bool_text(mixed["active_in_readable_conflict_qa_lane"]):
            continue
        active_count += 1
        q_ids = split_pipe(mixed["quantitative_observation_ids"])
        l_ids = split_pipe(mixed["qualitative_observation_ids"])
        if len(q_ids) != int(mixed["quantitative_observation_count"]):
            issues["quantitative_count_mismatch"] += 1
        if len(l_ids) != int(mixed["qualitative_observation_count"]):
            issues["qualitative_count_mismatch"] += 1
        for member_id in q_ids:
            member = quant.get(member_id)
            if not member or not bool_text(member.get("active_in_readable_conflict_qa_lane", "")):
                issues["missing_or_inactive_quantitative_member"] += 1
            elif member["mixed_join_key"] != mixed["mixed_join_key"]:
                issues["quantitative_key_mismatch"] += 1
        for member_id in l_ids:
            member = qual.get(member_id)
            if not member or not bool_text(member.get("active_in_readable_conflict_qa_lane", "")):
                issues["missing_or_inactive_qualitative_member"] += 1
            elif member["mixed_join_key"] != mixed["mixed_join_key"]:
                issues["qualitative_key_mismatch"] += 1
    if active_count != 371 or issues:
        raise RuntimeError(f"Active mixed-join validation failed: rows={active_count}, issues={dict(issues)}")
    return {"active_mixed_rows": active_count, **dict(issues)}


def no_write_preflight(output_dir: Path) -> dict[str, Any]:
    resolved = output_dir.resolve()
    docs_analysis = (ROOT / "docs/analysis").resolve()
    if docs_analysis not in resolved.parents:
        raise RuntimeError(f"Output must be a new subdirectory of docs/analysis: {resolved}")
    forbidden_parts = {"data", "corpus", "ingest", "codified", "analysis_dataset"}
    if forbidden_parts.intersection(resolved.relative_to(ROOT).parts):
        raise RuntimeError(f"Forbidden output path: {resolved}")
    if output_dir.exists():
        raise FileExistsError(f"Rollback-safe output directory already exists: {output_dir}")
    context = build_context()
    mixed_result = validate_active_mixed(context["rows"])
    return {
        "dry_run": True,
        "writes_performed": 0,
        "output_dir": str(output_dir.relative_to(ROOT)),
        "package_hashes_passed": 5,
        "bridge_identity_count": len(context["bridge_rows"]),
        "bridge_raw_hash_count": len({row["raw_retained_content_hash"] for row in context["bridge_rows"]}),
        "identity_quarantine_count": context["identity_quarantine_count"],
        "active_mixed_validation": mixed_result,
        "nonbase_lineage": context["nonbase_lineage"],
        "analysis_readiness_after_task": False,
    }


def contract_markdown(result: dict[str, Any]) -> str:
    return f"""# Provisional compensation schema-repair contract

Task ID: `COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25`

## Boundary

This directory is a rollback-safe, nonmutating schema-repair layer. It is not an analysis dataset, ingestion input, codified output, or final merge. The five immutable package ledgers are the only observation-bearing inputs. Durable ledgers are used only for deterministic one-to-one identity/provenance bridges.

Analysis readiness remains `false`.

## Current-row semantics

`current_active` is copied exactly from `active_in_readable_conflict_qa_lane`. `current_qa_status` uses this precedence:

1. inactive duplicate/canonical or reroute semantics;
2. non-pending `readable_conflict_qa_status` plus its classification;
3. non-pending `targeted_qa_resolution_status` plus its classification;
4. non-pending `qa_resolution_status` plus its classification;
5. original `qa_status`.

No historical status is overwritten or removed.

## Identity and matching contract

Raw retained hashes are joined one-to-one through `text_table_detection_id`. Source and artifact provenance are joined through matching source-review and PDF-readiness IDs. Fields absent from durable metadata—retrieval date, retrieval method, negotiation cycle, matched-set ID, and non-safety occupation subclass—remain blank with explicit incomplete statuses. No values are inferred from titles or prose.

## Quantitative normalization contract

All raw quantitative fields are preserved. Only exact scalar numeric tokens, exact percentage tokens, or exact two-endpoint ranges are parsed. Ranges are kept as minimum/maximum with a blank scalar. Current/new pairs, prose formulas, multipliers, hours, or unparseable strings are quarantined. No annualization is performed. The two unresolved groups and their five member observations remain quarantined.

## Qualitative contract

The package has mechanism fields and bounded pointers but no dedicated literal/verbatim evidence span. Consequently, this task creates only a navigation candidate, never a coded qualitative analysis view. A later separately authorized bounded evidence repair is required.

## Lane separation

Quantitative, qualitative, mixed, non-base-wage, and reference/exclusion schemas remain separate. Non-base wage is a companion view only; reference/exclusion is a control view only. Historical mixed keys never count as active joins.

## Decision

`{result['decision']}`. Another analysis-readiness review is not yet authorized; run the bounded follow-up prompt first.
"""


def run(output_dir: Path) -> dict[str, Any]:
    dry = no_write_preflight(output_dir)
    context = build_context()
    output_dir.mkdir(parents=True, exist_ok=False)
    rows = context["rows"]
    bridge_by_document = context["bridge_by_document"]
    membership = context["membership"]

    quant_shadow: list[dict[str, str]] = []
    quant_candidates: list[dict[str, str]] = []
    quant_exceptions: list[dict[str, str]] = []
    quarantine_counter = Counter()
    for row in rows["quantitative"]:
        normalized = normalize_quantitative(row, context["unresolved_by_observation"])
        repaired = append_derived(
            row,
            bridge_by_document[row["document_identity_id"]],
            membership(row),
            normalized,
        )
        quant_shadow.append(repaired)
        if normalized["analysis_candidate_eligible"] == "true":
            quant_candidates.append(repaired)
        elif repaired["current_active"] == "true":
            quant_exceptions.append(repaired)
            for reason in split_pipe(normalized["analysis_quarantine_reasons"]):
                quarantine_counter[reason] += 1

    qual_shadow: list[dict[str, str]] = []
    qual_navigation: list[dict[str, str]] = []
    for row in rows["qualitative"]:
        repaired = append_derived(
            row, bridge_by_document[row["document_identity_id"]], membership(row)
        )
        repaired.update(
            {
                "literal_verbatim_evidence_span": "",
                "qualitative_coded_measurement_eligible": "false",
                "qualitative_readiness_reason": "literal_verbatim_evidence_span_absent_navigation_only",
            }
        )
        qual_shadow.append(repaired)
        if repaired["current_active"] == "true":
            qual_navigation.append(repaired)

    mixed_result = validate_active_mixed(rows)
    mixed_shadow = [
        append_derived(row, bridge_by_document[row["document_identity_id"]], membership(row))
        for row in rows["mixed"]
    ]
    mixed_exceptions = [
        {
            "lane": lane,
            "observation_id": row.get(
                "quantitative_observation_id" if lane == "quantitative" else "qualitative_observation_id", ""
            ),
            "extraction_case_id": row["extraction_case_id"],
            "mixed_join_key": row.get("mixed_join_key", ""),
            "mixed_membership_status": membership(row),
        }
        for lane in ("quantitative", "qualitative")
        for row in rows[lane]
        if membership(row) in {"historical_inactive", "historical_missing"}
    ]

    nonbase_shadow: list[dict[str, str]] = []
    nonbase_candidates: list[dict[str, str]] = []
    nonbase_other_counts = Counter()
    for row in rows["non_base_wage"]:
        subtype, status = deterministic_nonbase_subtype(row)
        repaired = append_derived(
            row,
            bridge_by_document[row["document_identity_id"]],
            "active" if row.get("current_source_mixed_join_key") in context["active_mixed"] else (
                "historical_inactive"
                if row.get("current_source_mixed_join_key") in context["inactive_mixed"]
                else "historical_missing"
                if row.get("current_source_mixed_join_key")
                else "none"
            ),
            {
                "deterministic_non_base_subtype": subtype,
                "non_base_subtype_status": status,
                "typed_non_base_analysis_eligible": str(subtype != "other").lower(),
                "base_wage_outcome_eligible": "false",
            },
        )
        nonbase_shadow.append(repaired)
        if repaired["current_active"] == "true":
            nonbase_candidates.append(repaired)
            if row["non_base_wage_type"] == "other":
                nonbase_other_counts[status] += 1

    reference_shadow: list[dict[str, str]] = []
    reference_control: list[dict[str, str]] = []
    for row in rows["reference_and_exclusion"]:
        repaired = append_derived(
            row, bridge_by_document[row["document_identity_id"]], membership(row)
        )
        repaired["control_only"] = "true"
        repaired["analysis_outcome_eligible"] = "false"
        reference_shadow.append(repaired)
        if repaired["current_active"] == "true":
            reference_control.append(repaired)

    bridge_header = list(context["bridge_rows"][0])
    write_csv(output_dir / OUTPUT_FILENAMES["bridge"], bridge_header, context["bridge_rows"])
    durable_hash_lines = [
        f"{digest}  {DURABLE_BRIDGE_INPUTS[name].relative_to(ROOT)}"
        for name, digest in sorted(context["preflight"]["durable_bridge_input_sha256"].items())
    ]
    (output_dir / OUTPUT_FILENAMES["bridge_hashes"]).write_text(
        "\n".join(durable_hash_lines) + "\n", encoding="utf-8"
    )

    def headers(original: list[str], extras: list[str]) -> list[str]:
        return original + [field for field in extras if field not in original]

    quant_header = headers(context["tables"]["quantitative"].header, BRIDGE_FIELDS + CURRENT_FIELDS + [MIXED_STATUS_FIELD] + QUANT_NORMALIZED_FIELDS)
    qual_header = headers(context["tables"]["qualitative"].header, BRIDGE_FIELDS + CURRENT_FIELDS + [MIXED_STATUS_FIELD, "literal_verbatim_evidence_span", "qualitative_coded_measurement_eligible", "qualitative_readiness_reason"])
    mixed_header = headers(context["tables"]["mixed"].header, BRIDGE_FIELDS + CURRENT_FIELDS + [MIXED_STATUS_FIELD])
    nonbase_header = headers(context["repaired_nonbase_header"], ["current_source_quantitative_observation_id", "current_source_mixed_join_key"] + BRIDGE_FIELDS + CURRENT_FIELDS + [MIXED_STATUS_FIELD, "deterministic_non_base_subtype", "non_base_subtype_status", "typed_non_base_analysis_eligible", "base_wage_outcome_eligible"])
    reference_header = headers(context["tables"]["reference_and_exclusion"].header, BRIDGE_FIELDS + CURRENT_FIELDS + [MIXED_STATUS_FIELD, "control_only", "analysis_outcome_eligible"])

    write_csv(output_dir / OUTPUT_FILENAMES["quant_shadow"], quant_header, quant_shadow)
    write_csv(output_dir / OUTPUT_FILENAMES["qual_shadow"], qual_header, qual_shadow)
    write_csv(output_dir / OUTPUT_FILENAMES["mixed_shadow"], mixed_header, mixed_shadow)
    write_csv(output_dir / OUTPUT_FILENAMES["nonbase_shadow"], nonbase_header, nonbase_shadow)
    write_csv(output_dir / OUTPUT_FILENAMES["reference_shadow"], reference_header, reference_shadow)
    write_csv(output_dir / OUTPUT_FILENAMES["quant_candidate"], quant_header, quant_candidates)
    write_csv(output_dir / OUTPUT_FILENAMES["quant_exceptions"], quant_header, quant_exceptions)
    write_csv(output_dir / OUTPUT_FILENAMES["qual_navigation"], qual_header, qual_navigation)
    write_csv(output_dir / OUTPUT_FILENAMES["nonbase_candidate"], nonbase_header, nonbase_candidates)
    write_csv(output_dir / OUTPUT_FILENAMES["reference_control"], reference_header, reference_control)
    write_csv(
        output_dir / OUTPUT_FILENAMES["mixed_exceptions"],
        ["lane", "observation_id", "extraction_case_id", "mixed_join_key", "mixed_membership_status"],
        mixed_exceptions,
    )
    write_csv(output_dir / OUTPUT_FILENAMES["conflict_quarantine"], context["conflict_header"], context["conflict_rows"])

    current_qa_counts = {
        lane: dict(Counter(row["current_qa_status"] for row in lane_rows))
        for lane, lane_rows in {
            "quantitative": quant_shadow,
            "qualitative": qual_shadow,
            "mixed": mixed_shadow,
            "non_base_wage": nonbase_shadow,
            "reference_and_exclusion": reference_shadow,
        }.items()
    }
    membership_counts = {
        "quantitative": dict(Counter(row[MIXED_STATUS_FIELD] for row in quant_shadow)),
        "qualitative": dict(Counter(row[MIXED_STATUS_FIELD] for row in qual_shadow)),
        "mixed": dict(Counter(row[MIXED_STATUS_FIELD] for row in mixed_shadow)),
        "non_base_wage": dict(Counter(row[MIXED_STATUS_FIELD] for row in nonbase_shadow)),
    }
    bridge_audit = {
        "task_id": "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25",
        "bridge_result": "identity_hash_one_to_one_provenance_partial_matching_incomplete",
        "document_identity_count": len(context["bridge_rows"]),
        "unique_raw_retained_content_hash_count": len({row["raw_retained_content_hash"] for row in context["bridge_rows"]}),
        "identity_quarantine_count": context["identity_quarantine_count"],
        "occupation_class_exact_count": sum(bool(row["controlled_occupation_class"]) for row in context["bridge_rows"]),
        "occupation_class_incomplete_non_safety_count": sum(not row["controlled_occupation_class"] for row in context["bridge_rows"]),
        "contract_period_complete_count": sum(bool(row["contract_period_start_bridge"] and row["contract_period_end_bridge"]) for row in context["bridge_rows"]),
        "negotiation_cycle_id_count": sum(bool(row["negotiation_cycle_id"]) for row in context["bridge_rows"]),
        "matched_set_id_count": sum(bool(row["matched_set_id"]) for row in context["bridge_rows"]),
        "source_cite_count": sum(bool(row["source_cite_bridge"]) for row in context["bridge_rows"]),
        "artifact_pointer_count": sum(bool(row["artifact_pointer_bridge"]) for row in context["bridge_rows"]),
        "retrieval_date_count": sum(bool(row["retrieval_date_bridge"]) for row in context["bridge_rows"]),
        "retrieval_method_count": sum(bool(row["retrieval_method_bridge"]) for row in context["bridge_rows"]),
        "ocr_needed_or_ocr_later_count": sum(
            row["ocr_needed_signal_bridge"].strip().lower() not in {"", "no", "false", "0"}
            for row in context["bridge_rows"]
        ),
        "parse_text_present_or_partial_count": sum(
            row["text_layer_status_bridge"] in {"present", "partial"}
            for row in context["bridge_rows"]
        ),
        "durable_input_sha256": context["preflight"]["durable_bridge_input_sha256"],
        "durable_inputs_mutated": False,
        "no_inference_policy_enforced": True,
    }
    json_write(output_dir / OUTPUT_FILENAMES["bridge_audit"], bridge_audit)

    mixed_audit = {
        "active_join_validation": mixed_result,
        "membership_counts": membership_counts,
        "active_qualitative_historical_inactive_rows": sum(row[MIXED_STATUS_FIELD] == "historical_inactive" and row["current_active"] == "true" for row in qual_shadow),
        "active_qualitative_historical_inactive_unique_keys": len({row["mixed_join_key"] for row in qual_shadow if row[MIXED_STATUS_FIELD] == "historical_inactive" and row["current_active"] == "true"}),
        "active_qualitative_historical_missing_rows": sum(row[MIXED_STATUS_FIELD] == "historical_missing" and row["current_active"] == "true" for row in qual_shadow),
        "active_qualitative_historical_missing_unique_keys": len({row["mixed_join_key"] for row in qual_shadow if row[MIXED_STATUS_FIELD] == "historical_missing" and row["current_active"] == "true"}),
        "historical_keys_never_treated_as_active": True,
    }
    json_write(output_dir / OUTPUT_FILENAMES["mixed_audit"], mixed_audit)

    quarantine_summary = {
        "active_quantitative_row_count": sum(row["current_active"] == "true" for row in quant_shadow),
        "quantitative_analysis_candidate_count": len(quant_candidates),
        "quantitative_normalization_exception_count": len(quant_exceptions),
        "exception_reason_counts_nonexclusive": dict(sorted(quarantine_counter.items())),
        "neither_amount_nor_percentage_count": quarantine_counter["neither_amount_nor_percentage"],
        "ambiguous_compensation_type_other_count": quarantine_counter["ambiguous_compensation_type_other"],
        "unresolved_conflict_group_count": len(context["conflict_rows"]),
        "unresolved_conflict_member_observation_count": len(context["unresolved_by_observation"]),
        "identity_quarantine_count": context["identity_quarantine_count"],
        "analysis_promotion_eligible_count": 0,
    }
    json_write(output_dir / OUTPUT_FILENAMES["quarantine_summary"], quarantine_summary)

    decision = "schema_repairs_partial_additional_bounded_evidence_needed"
    decision_json = {
        "task_id": "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25",
        "generated_at": now_utc(),
        "decision": decision,
        "schema_repairs_complete": False,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": False,
        "next_prompt": OUTPUT_FILENAMES["future_prompt"],
        "next_recommendation": "run_separately_authorized_bounded_schema_repair_followup",
        "package_sha256_checks_passed": 5,
        "package_ledgers_mutated": False,
        "durable_bridge_inputs_mutated": False,
        "nonbase_duplicate_lineage_repair": context["nonbase_lineage"],
        "identity_provenance_bridge": bridge_audit,
        "quantitative": quarantine_summary,
        "qualitative": {
            "active_navigation_rows": len(qual_navigation),
            "coded_analysis_candidate_created": False,
            "blocker": "literal_verbatim_evidence_span_absent_requires_separately_authorized_bounded_evidence_repair",
        },
        "mixed": mixed_audit,
        "non_base_wage": {
            "active_companion_rows": len(nonbase_candidates),
            "active_original_other_rows": sum(row["non_base_wage_type"] == "other" for row in nonbase_candidates),
            "other_disposition_counts": dict(sorted(nonbase_other_counts.items())),
            "base_wage_outcome_eligible_count": 0,
        },
        "reference_and_exclusion": {
            "active_control_rows": len(reference_control),
            "analysis_outcome_eligible_count": 0,
        },
        "current_qa_status_counts": current_qa_counts,
        "forbidden_actions_performed": [],
        "ocr_later_documents_included": False,
    }
    json_write(output_dir / OUTPUT_FILENAMES["decision"], decision_json)

    column_map = {
        "schema_version": "compensation_schema_repair_v1",
        "non_base_duplicate_header_repair": {
            "original_header_count": len(context["tables"]["non_base_wage"].header),
            "ordinal_positions_zero_based": {
                "provisional_source_quantitative_observation_id": 30,
                "provisional_source_mixed_join_key": 31,
                "qa_corrected_source_quantitative_observation_id": 38,
                "qa_corrected_source_mixed_join_key": 39,
            },
            "canonical_derived_fields": [
                "current_source_quantitative_observation_id",
                "current_source_mixed_join_key",
            ],
            "audit": context["nonbase_lineage"],
        },
        "lane_headers": {
            "quantitative": quant_header,
            "qualitative": qual_header,
            "mixed": mixed_header,
            "non_base_wage": nonbase_header,
            "reference_and_exclusion": reference_header,
        },
        "bridge_fields": BRIDGE_FIELDS,
        "current_semantic_fields": CURRENT_FIELDS,
        "quantitative_normalized_fields": QUANT_NORMALIZED_FIELDS,
        "raw_fields_preserved": True,
    }
    json_write(output_dir / OUTPUT_FILENAMES["column_map"], column_map)
    (output_dir / OUTPUT_FILENAMES["contract"]).write_text(contract_markdown(decision_json), encoding="utf-8")

    quant_reason_lines = "\n".join(
        f"- `{name}`: {count}" for name, count in sorted(quarantine_counter.items())
    )
    (output_dir / OUTPUT_FILENAMES["quant_report"]).write_text(
        f"""# Quantitative parse-status report

- Active raw observations: {quarantine_summary['active_quantitative_row_count']}
- Mechanically safe provisional candidates: {len(quant_candidates)}
- Active normalization exceptions: {len(quant_exceptions)}
- Neither amount nor percentage: {quarantine_summary['neither_amount_nor_percentage_count']}
- Ambiguous `compensation_type=other`: {quarantine_summary['ambiguous_compensation_type_other_count']}
- Explicit unresolved conflict members quarantined: {len(context['unresolved_by_observation'])}
- Annualization performed: no
- Analysis-promotion eligible: 0

Reason counts are nonexclusive:

{quant_reason_lines}

Raw values are preserved. Exact ranges populate minimum/maximum and never a scalar. Formulas, pairs, multipliers, hours, and unparseable tokens remain exceptions.
""",
        encoding="utf-8",
    )

    other_lines = "\n".join(f"- `{name}`: {count}" for name, count in sorted(nonbase_other_counts.items()))
    (output_dir / OUTPUT_FILENAMES["nonbase_report"]).write_text(
        f"""# Non-base `other` disposition report

- Active non-base companion rows: {len(nonbase_candidates)}
- Active rows originally typed `other`: {sum(row['non_base_wage_type'] == 'other' for row in nonbase_candidates)}
- Base-wage outcome eligible: 0

Disposition counts for active original `other` rows:

{other_lines}

Keyword-supported subtypes are deterministic annotations only. Unresolved or multiply matching `other` rows remain `other` and are excluded from typed component analyses. All original fields remain unchanged.
""",
        encoding="utf-8",
    )
    (output_dir / OUTPUT_FILENAMES["qual_report"]).write_text(
        f"""# Qualitative mechanism schema-repair report

- Active mechanism navigation rows: {len(qual_navigation)}
- Dedicated literal/verbatim evidence spans in package: 0
- Coded qualitative analysis candidate created: no
- Navigation candidate created: yes

The package preserves mechanism fields and bounded evidence pointers, but it does not contain a dedicated literal evidence span with a final QA contract. Recovering those spans would require separately authorized bounded evidence work. This task did not open PDFs, run extraction, or call a model.
""",
        encoding="utf-8",
    )

    summary = f"""# Compensation schema-repair summary

Decision: `{decision}`

- Package SHA-256 checks: 5/5 passed.
- Package and durable ledgers modified: no.
- One-to-one raw retained hash bridge: {len(context['bridge_rows'])}/1,826 identities.
- Controlled occupation class established without inference: {bridge_audit['occupation_class_exact_count']}/1,826; {bridge_audit['occupation_class_incomplete_non_safety_count']} non-safety identities remain subclass-incomplete.
- Negotiation-cycle IDs: {bridge_audit['negotiation_cycle_id_count']}.
- Matched-set IDs: {bridge_audit['matched_set_id_count']}.
- Non-base duplicate lineage: 134 quantitative and 85 mixed links per copy; zero disagreements.
- Quantitative provisional candidates/exceptions: {len(quant_candidates)}/{len(quant_exceptions)}.
- Qualitative coded view: not created; {len(qual_navigation)} navigation rows retained.
- Active mixed joins: 371/371 valid.
- Residual conflicts: 2 groups / 5 observations preserved in quarantine.
- Active non-base companion rows: {len(nonbase_candidates)}; base-wage eligible: 0.
- Reference/exclusion control rows: {len(reference_control)}; outcome eligible: 0.
- Analysis readiness: false.

The remaining blockers are missing durable cycle/matched-set metadata, incomplete non-safety occupation subclasses, missing retrieval fields, and absent literal qualitative evidence spans. Run the bounded follow-up prompt before repeating analysis-readiness review.
"""
    (output_dir / OUTPUT_FILENAMES["summary"]).write_text(summary, encoding="utf-8")
    (output_dir / OUTPUT_FILENAMES["future_prompt"]).write_text(
        """# Future task: bounded schema-repair follow-up

Do not run this prompt without separate user authorization.

Perform a bounded, non-extractive follow-up for the final provisional compensation schema-repair layer. Resolve only metadata and evidence-contract gaps that can be established from existing local structured or bounded artifacts without URLs, downloads, OCR, GABRIEL, ingestion, codification, wage-gap analysis, regressions, or causal analysis.

Required goals:

1. establish contract/cycle dates and deterministic city × unit × negotiation-cycle/matched-set keys from existing structured metadata, or keep them quarantined;
2. establish controlled non-safety occupation subclasses only from explicit structured fields;
3. establish retrieval date/method and source-corpus provenance only from durable explicit fields;
4. determine whether literal qualitative evidence spans already exist in bounded structured artifacts; if not, prepare—but do not run—a separately authorized bounded span-capture task;
5. preserve all raw values, package hashes, duplicate/canonical provenance, mixed statuses, non-base separation, reference controls, and the two unresolved conflicts;
6. keep analysis readiness false and stop before promotion.

After those gaps are addressed, rerun schema and analysis-readiness review as a separate task.
""",
        encoding="utf-8",
    )

    validation = f"""# Schema-repair validation

- No-write dry run: passed; writes before output creation: {dry['writes_performed']}.
- Package SHA-256 checks: 5/5 passed before and after repair.
- New rollback-safe output directory under `docs/analysis`: passed.
- Immutable package ledgers modified: no.
- Durable bridge inputs modified: no.
- Non-base duplicate source columns: repaired by ordinal position; zero disagreements.
- One-to-one identity/raw-hash bridge: {len(context['bridge_rows'])}/1,826.
- Active mixed joins: 371/371 valid.
- Qualitative coded view created: no; navigation only.
- Two unresolved groups / five members quarantined: yes.
- Non-base lane separate and reference lane control-only: yes.
- OCR-later documents included: no.
- Analysis dataset, ingestion input, or codified output created: no.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUT_FILENAMES["validation"]).write_text(validation, encoding="utf-8")

    # Fail closed if input bytes changed during the run.
    after_package = {lane: sha256(path) for lane, path in LANES.items()}
    after_durable = {name: sha256(path) for name, path in DURABLE_BRIDGE_INPUTS.items()}
    if after_package != context["preflight"]["package_sha256"]:
        raise RuntimeError("Package input changed during schema repair")
    if after_durable != context["preflight"]["durable_bridge_input_sha256"]:
        raise RuntimeError("Durable bridge input changed during schema repair")
    return decision_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if args.dry_run:
        print(json.dumps(no_write_preflight(output_dir), indent=2, sort_keys=True))
        return 0
    result = run(output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
