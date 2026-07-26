#!/usr/bin/env python3
"""Read-only schema and join audit for the final provisional package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
)

LANES = {
    "quantitative": PACKAGE / "ledgers/quantitative/final_provisional_quantitative_ledger.csv",
    "qualitative": PACKAGE / "ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv",
    "mixed": PACKAGE / "ledgers/mixed/final_provisional_mixed_join_ledger.csv",
    "non_base_wage": PACKAGE / "ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv",
    "reference_and_exclusion": PACKAGE
    / "ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv",
}

ID_FIELDS = {
    "quantitative": "quantitative_observation_id",
    "qualitative": "qualitative_observation_id",
    "mixed": "mixed_join_key",
    "non_base_wage": "non_base_wage_observation_id",
    "reference_and_exclusion": "extraction_case_id",
}

COMMON_IDENTIFIERS = (
    "extraction_case_id",
    "document_identity_id",
    "text_table_detection_id",
    "source_review_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
)

ANALYSIS_REQUIRED_MISSING_FIELDS = (
    "retained_content_hash",
    "matched_set_id",
    "negotiation_cycle_id",
    "occupation_class",
)


@dataclass
class Table:
    path: Path
    header: list[str]
    rows: list[list[str]]

    @classmethod
    def read(cls, path: Path) -> "Table":
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            rows = list(reader)
        bad = [index + 2 for index, row in enumerate(rows) if len(row) != len(header)]
        if bad:
            raise RuntimeError(f"Malformed CSV record widths in {path}: {bad[:10]}")
        return cls(path=path, header=header, rows=rows)

    def indexes(self, field: str) -> list[int]:
        return [index for index, name in enumerate(self.header) if name == field]

    def value(self, row: list[str], field: str, occurrence: int = -1) -> str:
        indexes = self.indexes(field)
        if not indexes:
            return ""
        return row[indexes[occurrence]].strip()

    def active(self, row: list[str]) -> bool:
        return self.value(row, "active_in_readable_conflict_qa_lane").lower() == "true"

    def active_rows(self) -> list[list[str]]:
        return [row for row in self.rows if self.active(row)]

    def duplicate_headers(self) -> dict[str, int]:
        return {
            name: count
            for name, count in Counter(self.header).items()
            if count > 1
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_hash_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        values[name.strip()] = digest
    return values


def fill_counts(table: Table, fields: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    rows = table.active_rows()
    total = len(rows)
    result: dict[str, dict[str, Any]] = {}
    for field in fields:
        count = sum(bool(table.value(row, field)) for row in rows)
        result[field] = {
            "present_in_schema": field in table.header,
            "nonblank_active_rows": count,
            "active_row_count": total,
            "nonblank_rate": round(count / total, 6) if total else None,
        }
    return result


def distribution(table: Table, field: str, *, active_only: bool = True) -> dict[str, int]:
    rows = table.active_rows() if active_only else table.rows
    return dict(sorted(Counter(table.value(row, field) or "<blank>" for row in rows).items()))


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def audit() -> dict[str, Any]:
    manifest_path = PACKAGE / "final_provisional_merge_manifest.json"
    decision_path = PACKAGE / "final_provisional_decision.json"
    conflict_path = PACKAGE / "final_provisional_conflict_register.csv"
    case_index_path = PACKAGE / "final_provisional_case_index.csv"
    required = [manifest_path, decision_path, conflict_path, case_index_path, *LANES.values()]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required package artifacts missing: {missing}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    input_hashes = parse_hash_file(PACKAGE / "final_provisional_input_sha256.txt")
    output_hashes = parse_hash_file(PACKAGE / "final_provisional_output_sha256.txt")
    tables = {lane: Table.read(path) for lane, path in LANES.items()}

    computed_hashes = {
        str(path.relative_to(PACKAGE)): sha256(path) for path in LANES.values()
    }
    hash_checks = {
        lane: {
            "computed": computed_hashes[str(path.relative_to(PACKAGE))],
            "recorded_output": output_hashes[str(path.relative_to(PACKAGE))],
            "recorded_manifest": manifest["output_sha256"][str(path.relative_to(PACKAGE))],
        }
        for lane, path in LANES.items()
    }
    for lane, values in hash_checks.items():
        values["pass"] = len(set(values.values())) == 1
    input_output_hash_sets_match = sorted(input_hashes.values()) == sorted(output_hashes.values())

    counts = {
        lane: {
            "source_rows": len(table.rows),
            "active_rows": len(table.active_rows()),
            "inactive_rows": len(table.rows) - len(table.active_rows()),
            "recorded_source_rows": manifest["source_row_counts"][lane],
            "recorded_active_rows": manifest["active_row_counts"][lane],
        }
        for lane, table in tables.items()
    }
    for values in counts.values():
        values["pass"] = (
            values["source_rows"] == values["recorded_source_rows"]
            and values["active_rows"] == values["recorded_active_rows"]
        )

    schema_fields = {lane: table.header for lane, table in tables.items()}
    duplicate_headers = {
        lane: table.duplicate_headers() for lane, table in tables.items()
    }
    missing_analysis_fields = {
        lane: [field for field in ANALYSIS_REQUIRED_MISSING_FIELDS if field not in table.header]
        for lane, table in tables.items()
    }
    identifier_completeness = {
        lane: fill_counts(table, (ID_FIELDS[lane], *COMMON_IDENTIFIERS, "bounded_evidence_pointer"))
        for lane, table in tables.items()
    }

    quantitative = tables["quantitative"]
    quant_fields = (
        "contract_period_start",
        "contract_period_end",
        "compensation_type",
        "occupation_unit_classification_rank",
        "rate_value",
        "salary_value",
        "hourly_rate",
        "annual_salary",
        "pay_band",
        "step",
        "grade",
        "percentage_increase",
        "effective_date",
        "currency_or_unit",
        "confidence",
        "qa_status",
    )
    quantitative_fill = fill_counts(quantitative, quant_fields)
    amount_fields = ("rate_value", "salary_value", "hourly_rate", "annual_salary")
    quant_active = quantitative.active_rows()
    quantitative_fill["any_amount_field"] = {
        "nonblank_active_rows": sum(
            any(quantitative.value(row, field) for field in amount_fields) for row in quant_active
        ),
        "active_row_count": len(quant_active),
    }
    quantitative_fill["any_amount_or_percentage"] = {
        "nonblank_active_rows": sum(
            any(quantitative.value(row, field) for field in (*amount_fields, "percentage_increase"))
            for row in quant_active
        ),
        "active_row_count": len(quant_active),
    }

    qualitative = tables["qualitative"]
    qual_detail_fields = (
        "bargaining_logic",
        "indexing_formula",
        "comparability_basis",
        "parity_logic",
        "step_progression_rule",
        "eligibility_rule",
        "implementation_rule",
        "fiscal_constraint",
        "reopener_clause",
        "differentiation_logic",
    )
    qualitative_fill = fill_counts(
        qualitative,
        (
            "contract_period_start",
            "contract_period_end",
            "mechanism_type",
            *qual_detail_fields,
            "confidence",
            "qa_status",
        ),
    )
    qual_active = qualitative.active_rows()
    qualitative_fill["any_mechanism_detail"] = {
        "nonblank_active_rows": sum(
            any(qualitative.value(row, field) for field in qual_detail_fields)
            for row in qual_active
        ),
        "active_row_count": len(qual_active),
    }
    qualitative_fill["verbatim_evidence_span"] = {
        "present_in_schema": "verbatim_evidence_span" in qualitative.header,
        "nonblank_active_rows": 0,
        "active_row_count": len(qual_active),
    }

    non_base = tables["non_base_wage"]
    non_base_fill = fill_counts(
        non_base,
        (
            "contract_period_start",
            "contract_period_end",
            "non_base_wage_type",
            "value_text",
            "effective_date",
            "eligibility_or_implementation_rule",
            "confidence",
            "qa_status",
            "source_quantitative_observation_id",
            "source_mixed_join_key",
        ),
    )
    non_base_duplicate_header_values: dict[str, dict[str, int]] = {}
    for field in ("source_quantitative_observation_id", "source_mixed_join_key"):
        indexes = non_base.indexes(field)
        if len(indexes) != 2:
            raise RuntimeError(f"Expected two non-base occurrences of {field}")
        first, second = indexes
        non_base_duplicate_header_values[field] = {
            "first_nonblank_rows": sum(bool(row[first].strip()) for row in non_base.rows),
            "second_nonblank_rows": sum(bool(row[second].strip()) for row in non_base.rows),
            "value_disagreement_rows": sum(
                row[first].strip() != row[second].strip() for row in non_base.rows
            ),
        }

    id_sets = {
        lane: {table.value(row, ID_FIELDS[lane]) for row in table.rows}
        for lane, table in tables.items()
    }
    active_id_sets = {
        lane: {table.value(row, ID_FIELDS[lane]) for row in table.active_rows()}
        for lane, table in tables.items()
    }
    id_to_row = {
        lane: {table.value(row, ID_FIELDS[lane]): row for row in table.rows}
        for lane, table in tables.items()
    }
    mixed = tables["mixed"]
    mixed_issues = Counter()
    for row in mixed.active_rows():
        key = mixed.value(row, "mixed_join_key")
        case = mixed.value(row, "extraction_case_id")
        quant_ids = split_ids(mixed.value(row, "quantitative_observation_ids"))
        qual_ids = split_ids(mixed.value(row, "qualitative_observation_ids"))
        if len(quant_ids) != int(mixed.value(row, "quantitative_observation_count") or -1):
            mixed_issues["quantitative_declared_count_mismatch"] += 1
        if len(qual_ids) != int(mixed.value(row, "qualitative_observation_count") or -1):
            mixed_issues["qualitative_declared_count_mismatch"] += 1
        for lane, member_ids in (("quantitative", quant_ids), ("qualitative", qual_ids)):
            table = tables[lane]
            for member_id in member_ids:
                if member_id not in id_sets[lane]:
                    mixed_issues[f"missing_{lane}_member"] += 1
                    continue
                member = id_to_row[lane][member_id]
                if member_id not in active_id_sets[lane]:
                    mixed_issues[f"inactive_{lane}_member"] += 1
                if table.value(member, "extraction_case_id") != case:
                    mixed_issues[f"{lane}_case_mismatch"] += 1
                if table.value(member, "mixed_join_key") != key:
                    mixed_issues[f"{lane}_join_key_mismatch"] += 1

    active_qual_references_inactive_mixed = sum(
        bool(qualitative.value(row, "mixed_join_key"))
        and qualitative.value(row, "mixed_join_key") in id_sets["mixed"]
        and qualitative.value(row, "mixed_join_key") not in active_id_sets["mixed"]
        for row in qualitative.active_rows()
    )
    active_quant_references_inactive_mixed = sum(
        bool(quantitative.value(row, "mixed_join_key"))
        and quantitative.value(row, "mixed_join_key") in id_sets["mixed"]
        and quantitative.value(row, "mixed_join_key") not in active_id_sets["mixed"]
        for row in quantitative.active_rows()
    )
    active_qual_references_missing_mixed = sum(
        bool(qualitative.value(row, "mixed_join_key"))
        and qualitative.value(row, "mixed_join_key") not in id_sets["mixed"]
        for row in qualitative.active_rows()
    )
    active_quant_references_missing_mixed = sum(
        bool(quantitative.value(row, "mixed_join_key"))
        and quantitative.value(row, "mixed_join_key") not in id_sets["mixed"]
        for row in quantitative.active_rows()
    )
    active_qual_missing_mixed_keys = {
        qualitative.value(row, "mixed_join_key")
        for row in qualitative.active_rows()
        if qualitative.value(row, "mixed_join_key")
        and qualitative.value(row, "mixed_join_key") not in id_sets["mixed"]
    }

    duplicate_id_counts = {
        lane: sum(count - 1 for count in Counter(
            table.value(row, ID_FIELDS[lane]) for row in table.rows
        ).values() if count > 1)
        for lane, table in tables.items()
    }
    duplicate_provenance_rows = sum(
        bool(table.value(row, "duplicate_of"))
        for table in tables.values()
        for row in table.rows
    )

    metadata_by_document: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    case_to_documents: dict[str, set[str]] = defaultdict(set)
    for table in tables.values():
        for row in table.rows:
            document = table.value(row, "document_identity_id")
            case = table.value(row, "extraction_case_id")
            metadata_by_document[document].add(
                tuple(table.value(row, field) for field in COMMON_IDENTIFIERS[1:])
            )
            case_to_documents[case].add(document)
    metadata_inconsistent_documents = sum(len(values) > 1 for values in metadata_by_document.values())
    cases_with_multiple_documents = sum(len(values) > 1 for values in case_to_documents.values())

    conflict_table = Table.read(conflict_path)
    unresolved_ids = [conflict_table.value(row, "resolution_id") for row in conflict_table.rows]
    unresolved_observation_ids = sorted(
        member
        for row in conflict_table.rows
        for member in split_ids(conflict_table.value(row, "quantitative_observation_ids"))
    )
    unresolved_active = all(member in active_id_sets["quantitative"] for member in unresolved_observation_ids)

    case_index = Table.read(case_index_path)
    case_index_has_raw_hash = "retained_content_hash" in case_index.header
    case_index_opaque_identity_count = sum(
        case_index.value(row, "retained_content_hash_status")
        == "opaque_sha256_derived_identity_from_frozen_selection"
        for row in case_index.rows
    )

    blockers = [
        {
            "blocker_id": "B01",
            "severity": "critical",
            "issue": "duplicate_non_base_provenance_headers",
            "observed": duplicate_headers["non_base_wage"],
        },
        {
            "blocker_id": "B02",
            "severity": "critical",
            "issue": "raw_retained_content_hash_absent_from_lanes_and_case_index",
            "observed": not case_index_has_raw_hash,
        },
        {
            "blocker_id": "B03",
            "severity": "critical",
            "issue": "matched_set_negotiation_cycle_and_controlled_occupation_identifiers_absent",
            "observed": True,
        },
        {
            "blocker_id": "B04",
            "severity": "critical",
            "issue": "analysis_value_and_time_fields_are_not_complete_enough_for_unrestricted_wage_analysis",
            "observed": True,
        },
        {
            "blocker_id": "B05",
            "severity": "major",
            "issue": "authoritative_active_semantics_require_a_derived_view_over_layer_specific_flags",
            "observed": True,
        },
        {
            "blocker_id": "B06",
            "severity": "major",
            "issue": "qualitative_rows_lack_a_dedicated_verbatim_evidence_span_field",
            "observed": "verbatim_evidence_span" not in qualitative.header,
        },
        {
            "blocker_id": "B07",
            "severity": "major",
            "issue": "active_qualitative_records_carry_non_active_or_missing_historical_mixed_keys",
            "observed": {
                "references_to_inactive_mixed_rows": active_qual_references_inactive_mixed,
                "rows_referencing_missing_historical_mixed_keys": active_qual_references_missing_mixed,
                "unique_missing_historical_mixed_keys": len(active_qual_missing_mixed_keys),
            },
        },
        {
            "blocker_id": "B08",
            "severity": "quarantine",
            "issue": "two_quantitative_conflict_groups_remain_explicitly_unresolved",
            "observed": len(unresolved_ids),
        },
        {
            "blocker_id": "B09",
            "severity": "major",
            "issue": "non_base_other_category_requires_reason_coded_subtyping_before_analysis",
            "observed": distribution(non_base, "non_base_wage_type").get("other", 0),
        },
        {
            "blocker_id": "B10",
            "severity": "critical",
            "issue": "analysis_provenance_fields_are_not_self_contained_in_lane_schemas",
            "observed": True,
        },
        {
            "blocker_id": "B11",
            "severity": "major",
            "issue": "reference_and_exclusion_rows_are_control_records_not_outcomes",
            "observed": len(tables["reference_and_exclusion"].active_rows()),
        },
    ]

    result = {
        "task_id": "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-PACKAGE-SCHEMA-READINESS-REVIEW-2026-07-25",
        "review_mode": "read_only_schema_join_provenance_audit",
        "package_path": str(PACKAGE.relative_to(ROOT)),
        "package_decision": decision["decision"],
        "schema_readiness_decision": "schema_readiness_hold_schema_repairs_required",
        "final_analysis_ready": False,
        "future_prompt": "next_schema_repair_prompt.md",
        "hash_checks": hash_checks,
        "all_five_hash_checks_pass": all(value["pass"] for value in hash_checks.values()),
        "input_output_hash_sets_match": input_output_hash_sets_match,
        "counts": counts,
        "schemas_remain_separate": manifest["schemas_remain_separate"] is True,
        "schema_fields": schema_fields,
        "duplicate_headers": duplicate_headers,
        "missing_analysis_fields": missing_analysis_fields,
        "identifier_completeness": identifier_completeness,
        "quantitative_field_completeness": quantitative_fill,
        "quantitative_confidence_counts": distribution(quantitative, "confidence"),
        "quantitative_qa_status_counts": distribution(quantitative, "qa_status"),
        "qualitative_field_completeness": qualitative_fill,
        "qualitative_mechanism_type_counts": distribution(qualitative, "mechanism_type"),
        "qualitative_confidence_counts": distribution(qualitative, "confidence"),
        "qualitative_qa_status_counts": distribution(qualitative, "qa_status"),
        "non_base_field_completeness": non_base_fill,
        "non_base_type_counts": distribution(non_base, "non_base_wage_type"),
        "non_base_confidence_counts": distribution(non_base, "confidence"),
        "non_base_duplicate_header_value_audit": non_base_duplicate_header_values,
        "mixed_join_audit": {
            "active_mixed_rows": len(mixed.active_rows()),
            "issue_counts": dict(sorted(mixed_issues.items())),
            "active_quantitative_references_to_inactive_mixed": active_quant_references_inactive_mixed,
            "active_qualitative_references_to_inactive_mixed": active_qual_references_inactive_mixed,
            "active_quantitative_references_to_missing_mixed": active_quant_references_missing_mixed,
            "active_qualitative_references_to_missing_mixed": active_qual_references_missing_mixed,
            "active_qualitative_unique_missing_mixed_keys": len(active_qual_missing_mixed_keys),
            "recorded_historical_missing_mixed_key_count": manifest[
                "historical_mixed_key_provenance_count"
            ],
        },
        "duplicate_provenance_audit": {
            "duplicate_observation_id_counts": duplicate_id_counts,
            "duplicate_provenance_rows": duplicate_provenance_rows,
            "recorded_duplicate_provenance_rows": manifest["duplicate_provenance_row_count"],
            "newly_canonicalized_duplicate_count": manifest["newly_canonicalized_duplicate_count"],
        },
        "case_identity_audit": {
            "unique_document_identity_count": len(metadata_by_document),
            "case_index_rows": len(case_index.rows),
            "case_index_has_raw_retained_content_hash": case_index_has_raw_hash,
            "case_index_opaque_identity_count": case_index_opaque_identity_count,
            "metadata_inconsistent_document_count": metadata_inconsistent_documents,
            "cases_with_multiple_document_identities": cases_with_multiple_documents,
        },
        "unresolved_conflict_audit": {
            "group_count": len(conflict_table.rows),
            "resolution_ids": unresolved_ids,
            "observation_ids": unresolved_observation_ids,
            "all_observations_remain_active": unresolved_active,
            "recommended_treatment": "quarantine_from_analysis_views_without_mutating_provisional_rows",
        },
        "non_base_recommended_treatment": "retain_as_separate_companion_dataset_not_base_wage_input",
        "blockers": blockers,
        "package_ledgers_modified": False,
        "ocr_later_documents_included": False,
        "ingestion_or_codification_performed": False,
        "analysis_dataset_created": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete audit as JSON")
    args = parser.parse_args()
    result = audit()
    if not result["all_five_hash_checks_pass"]:
        raise RuntimeError("One or more package ledger hashes do not match")
    if not all(value["pass"] for value in result["counts"].values()):
        raise RuntimeError("One or more package ledger counts do not match")
    if result["unresolved_conflict_audit"]["group_count"] != 2:
        raise RuntimeError("Expected exactly two unresolved conflict groups")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["schema_readiness_decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
