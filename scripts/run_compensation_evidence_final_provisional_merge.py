#!/usr/bin/env python3
"""Materialize the authorized final provisional compensation package.

This runner performs a package-level promotion only. It verifies and copies
five immutable corrected shadow ledgers byte-for-byte, builds non-analytic
package metadata, and keeps every schema separate. It has no network, OCR,
model, extraction, ingestion, codification, or analysis code path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
INPUT_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-READABLE-PARSE-TEXT-1826-"
    "TARGETED-CONFLICT-QA-2026-07-25"
)
AUTHORITY_PATH = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-READABLE-PARSE-TEXT-1826-"
    "INDEPENDENT-BOUNDED-REVIEW-2026-07-25/"
    "readable_parse_text_1826_independent_bounded_review_decision.json"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
)

INPUT_SPECS: dict[str, dict[str, Any]] = {
    "quantitative": {
        "input": "readable_parse_text_1826_quantitative_ledger_qa_corrected.csv",
        "output": "ledgers/quantitative/final_provisional_quantitative_ledger.csv",
        "sha256": "7e275b8c45f0d4b77e01249d978fe17862fd3f8d552bf0f4ef77ed0bb3616c86",
        "source_rows": 2044,
        "active_rows": 1907,
        "id_field": "quantitative_observation_id",
    },
    "qualitative": {
        "input": "readable_parse_text_1826_qualitative_mechanism_ledger_qa_corrected.csv",
        "output": "ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv",
        "sha256": "d22a4015da83da7d0195e430ef30d475b3678c17696e7a835d6d09bce1a1e0d5",
        "source_rows": 1954,
        "active_rows": 1954,
        "id_field": "qualitative_observation_id",
    },
    "mixed": {
        "input": "readable_parse_text_1826_mixed_ledger_qa_corrected.csv",
        "output": "ledgers/mixed/final_provisional_mixed_join_ledger.csv",
        "sha256": "a204061a4ca4bbfd3512bf964d689fe385dfd71fac93589a4bb9b59e64eb9192",
        "source_rows": 387,
        "active_rows": 371,
        "id_field": "mixed_join_key",
    },
    "non_base_wage": {
        "input": "readable_parse_text_1826_non_base_wage_ledger_qa_corrected.csv",
        "output": "ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv",
        "sha256": "84df35187461392ea9699660ea86317250a33979e6ff2b4f9256a49b1d9e0ea2",
        "source_rows": 4746,
        "active_rows": 4733,
        "id_field": "non_base_wage_observation_id",
    },
    "reference_and_exclusion": {
        "input": "readable_parse_text_1826_reference_exclusion_ledger_qa_corrected.csv",
        "output": "ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv",
        "sha256": "2a33987b8f54048d8a397fc7d9a917dafd2dbcf8b7b74a20de8c2642a886e3a1",
        "source_rows": 345,
        "active_rows": 345,
        "id_field": "extraction_case_id",
    },
}

EXPECTED_UNRESOLVED = {
    "qares1826_98591102083229343fecc71f": {
        "qobs_985ddb7a53fed53c92361fdb",
        "qobs_443497d509eb8f225658b2c9",
    },
    "qares1826_3dded7aaf73536d0a8f5842f": {
        "qobs_e7d065a47ede9da2ca9c9bf4",
        "qobs_c702c01aaa380ba5421a63ef",
        "qobs_642603a66adb930a4bc11f89",
    },
}
EXPECTED_UNIT_COUNTS = {"fire": 439, "non_safety": 607, "police": 780}
EXPECTED_SOURCE_COUNTS = {
    "arbitration_award": 10,
    "cba": 1717,
    "factfinding": 2,
    "memorandum_or_settlement": 20,
    "ordinance_or_policy": 19,
    "wage_schedule_or_compensation_plan": 58,
}
WASCO_ID = "nobs_e1327e5ce6d9cc1ce55a6f02"

CASE_FIELDS = [
    "document_identity_id",
    "retained_content_hash_reference",
    "retained_content_hash_status",
    "extraction_case_id",
    "text_table_detection_id",
    "source_review_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "quantitative_source_row_count",
    "quantitative_active_row_count",
    "qualitative_source_row_count",
    "qualitative_active_row_count",
    "mixed_source_row_count",
    "mixed_active_row_count",
    "non_base_wage_source_row_count",
    "non_base_wage_active_row_count",
    "reference_and_exclusion_source_row_count",
    "reference_and_exclusion_active_row_count",
    "has_inactive_provenance_rows",
    "has_duplicate_provenance",
    "has_explicit_unresolved_conflict",
]

CONFLICT_FIELDS = [
    "resolution_id",
    "extraction_case_id",
    "quantitative_observation_ids",
    "observation_count",
    "resolution_classification",
    "resolution_status",
    "reason_codes",
    "active_flags",
    "bounded_evidence_pointers",
    "ambiguity_preservation",
]

NONBASE_PATTERNS = (
    re.compile(r"\b(overtime|double[ -]?time|callback|call[- ]?back|standby|on[- ]?call|compensatory)\b", re.I),
    re.compile(r"\b(stipend|incentive payment|bonus|premium|differential|allowance|hazard pay|acting pay|out[- ]of[- ]class)\b", re.I),
    re.compile(r"\blongevity\b|\byears? of service\b", re.I),
    re.compile(r"\b(certif(?:ication|ied)?|education pay|degree pay|training pay)\b", re.I),
    re.compile(r"\b(health(?:care)?|medical|insurance contribution)\b", re.I),
    re.compile(r"\b(pension\w*|retirement contribution)\b", re.I),
    re.compile(r"\b(leave|vacation|sick pay|holiday pay|funeral leave|jury duty)\b", re.I),
    re.compile(r"\b(reimburse|mileage|travel|meal)\w*\b", re.I),
    re.compile(r"\b(uniform|equipment|clothing)\w*\b", re.I),
    re.compile(r"\b(benefit|insurance)\w*\b", re.I),
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def active(row: dict[str, str]) -> bool:
    for field in (
        "active_in_readable_conflict_qa_lane",
        "active_in_qa_corrected_lane",
        "active_in_provisional_lane",
    ):
        if row.get(field):
            return row[field] == "true"
    return True


def pointer_valid(pointer: str) -> bool:
    values = [item for item in pointer.split("|") if item]
    if not values:
        return False
    for value in values:
        if "#page=" not in value:
            return False
        path_value, page_value = value.rsplit("#page=", 1)
        try:
            page = int(page_value)
        except ValueError:
            return False
        path = Path(path_value)
        if not path.is_absolute():
            path = ROOT / path
        if page < 1 or not path.is_file():
            return False
    return True


def quantitative_nonbase_signal(row: dict[str, str]) -> bool:
    fields = (
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
        "reason_code",
    )
    diagnostic = " ".join(row.get(field, "") for field in fields).replace("_", " ")
    return any(pattern.search(diagnostic) for pattern in NONBASE_PATTERNS)


def require_authority(path: Path) -> dict[str, Any]:
    authority = json.loads(path.read_text(encoding="utf-8"))
    if not (
        authority.get("decision")
        == "independent_review_pass_final_provisional_merge_prompt_allowed"
        and authority.get("independent_review_pass") is True
        and authority.get("final_provisional_merge_prompt_allowed") is True
        and authority.get("final_provisional_merge_allowed") is False
        and authority.get("final_analysis_ready") is False
        and authority.get("unresolved_conflict_groups_preserved") == 2
        and authority.get("duplicate_provenance_rows_verified") == 14
        and authority.get("all_unique_readable_parse_text_documents_covered") is True
        and authority.get("ocr_later_documents_untouched") is True
    ):
        raise RuntimeError("Independent review authority does not permit this provisional merge")
    return authority


def configured_input_paths(input_dir: Path) -> dict[str, Path]:
    expected = {spec["input"] for spec in INPUT_SPECS.values()}
    configured = {path.name for path in input_dir.glob("*_qa_corrected.csv")}
    if configured != expected:
        raise RuntimeError(
            "Exactly five corrected shadow ledgers are required; configured set differs"
        )
    return {lane: input_dir / spec["input"] for lane, spec in INPUT_SPECS.items()}


def reconcile_inputs(input_dir: Path, authority_path: Path) -> dict[str, Any]:
    authority = require_authority(authority_path)
    paths = configured_input_paths(input_dir)
    headers: dict[str, list[str]] = {}
    rows: dict[str, list[dict[str, str]]] = {}
    input_hashes: dict[str, str] = {}
    header_hashes: dict[str, str] = {}
    lane_source_counts: dict[str, int] = {}
    active_counts: dict[str, int] = {}

    for lane, spec in INPUT_SPECS.items():
        path = paths[lane]
        if not path.is_file():
            raise FileNotFoundError(f"Missing corrected shadow ledger: {path}")
        digest = sha_file(path)
        if digest != spec["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch for {spec['input']}")
        header, lane_rows = read_csv(path)
        if not header or spec["id_field"] not in header:
            raise RuntimeError(f"Required schema identity field missing for {lane}")
        if len(lane_rows) != spec["source_rows"]:
            raise RuntimeError(f"Source row count mismatch for {lane}")
        lane_active = sum(active(row) for row in lane_rows)
        if lane_active != spec["active_rows"]:
            raise RuntimeError(f"Active row count mismatch for {lane}")
        headers[lane] = header
        rows[lane] = lane_rows
        input_hashes[spec["input"]] = digest
        header_hashes[lane] = hashlib.sha256(
            "\x1f".join(header).encode("utf-8")
        ).hexdigest()
        lane_source_counts[lane] = len(lane_rows)
        active_counts[lane] = lane_active

    observation_rows = rows["quantitative"] + rows["qualitative"] + rows["non_base_wage"]
    observation_ids = [
        row.get("quantitative_observation_id")
        or row.get("qualitative_observation_id")
        or row.get("non_base_wage_observation_id")
        for row in observation_rows
    ]
    if any(not item for item in observation_ids):
        raise RuntimeError("An observation row has no observation ID")
    duplicate_observation_id_count = len(observation_ids) - len(set(observation_ids))
    if duplicate_observation_id_count != 0:
        raise RuntimeError("Duplicate observation IDs are present")

    duplicate_rows = [row for row in rows["quantitative"] + rows["non_base_wage"] if row.get("duplicate_of")]
    all_observations = {
        (row.get("quantitative_observation_id") or row.get("qualitative_observation_id") or row.get("non_base_wage_observation_id")): row
        for row in observation_rows
    }
    if len(duplicate_rows) != 14:
        raise RuntimeError("Duplicate provenance row count is not 14")
    for row in duplicate_rows:
        if (
            row.get("canonical_observation_id") != row.get("duplicate_of")
            or row["duplicate_of"] not in all_observations
        ):
            raise RuntimeError("A duplicate provenance link is invalid")
    new_canonicalized = [row for row in duplicate_rows if row.get("qa_status") == "duplicate_canonicalized"]
    if len(new_canonicalized) != 5:
        raise RuntimeError("Five newly canonicalized duplicates were not preserved")

    active_observations = [row for row in observation_rows if active(row)]
    invalid_pointers = sum(
        not pointer_valid(row.get("bounded_evidence_pointer", ""))
        for row in active_observations
    )
    if invalid_pointers:
        raise RuntimeError("An active observation has an invalid bounded page pointer")

    contamination = [
        row for row in rows["quantitative"]
        if active(row)
        and quantitative_nonbase_signal(row)
        and row.get("targeted_qa_resolution_classification")
        != "retain_quantitative_base_wage"
    ]
    if contamination:
        raise RuntimeError("Active base/non-base-wage contamination is present")

    unresolved: dict[str, set[str]] = {}
    for row in rows["quantitative"]:
        resolution_id = row.get("readable_conflict_qa_resolution_id", "")
        if (
            resolution_id in EXPECTED_UNRESOLVED
            and row.get("readable_conflict_qa_status") == "unresolved"
            and row.get("readable_conflict_qa_classification")
            == "insufficient_evidence_needs_review"
            and active(row)
        ):
            unresolved.setdefault(resolution_id, set()).add(
                row["quantitative_observation_id"]
            )
    if unresolved != EXPECTED_UNRESOLVED:
        raise RuntimeError("The two explicit unresolved conflict groups changed")

    reroute_sources = [
        row for row in rows["quantitative"]
        if row.get("readable_conflict_qa_classification") == "non_base_wage_misroute"
        and row.get("readable_conflict_qa_reason_codes")
        == "WORKING_OUT_OF_CLASSIFICATION_PREMIUM"
    ]
    reroute_targets = [
        row for row in rows["non_base_wage"]
        if row.get("readable_conflict_qa_reason_codes")
        == "WORKING_OUT_OF_CLASSIFICATION_PREMIUM"
    ]
    target_by_source = {
        row.get("source_quantitative_observation_id", ""): row
        for row in reroute_targets
    }
    if len(reroute_sources) != 3 or len(reroute_targets) != 3:
        raise RuntimeError("Working-out-of-classification reroute count changed")
    for source in reroute_sources:
        target = target_by_source.get(source["quantitative_observation_id"])
        if not target or active(source) or not active(target):
            raise RuntimeError("Working-out-of-classification active routing changed")
        if target["bounded_evidence_pointer"] != source["bounded_evidence_pointer"]:
            raise RuntimeError("Working-out-of-classification pointer provenance changed")

    wasco = [row for row in rows["non_base_wage"] if row.get("non_base_wage_observation_id") == WASCO_ID]
    if not (
        len(wasco) == 1
        and active(wasco[0])
        and pointer_valid(wasco[0]["bounded_evidence_pointer"])
        and not any(row.get("non_base_wage_observation_id") == "onb" for row in rows["non_base_wage"])
    ):
        raise RuntimeError("Wasco shadow-only record repair changed")

    quant_by_id = {row["quantitative_observation_id"]: row for row in rows["quantitative"]}
    qual_by_id = {row["qualitative_observation_id"]: row for row in rows["qualitative"]}
    mixed_by_key = {row["mixed_join_key"]: row for row in rows["mixed"]}
    for mixed in rows["mixed"]:
        if not active(mixed):
            continue
        quant_ids = next(
            (
                mixed.get(field, "")
                for field in (
                    "readable_conflict_qa_corrected_quantitative_observation_ids",
                    "targeted_qa_corrected_quantitative_observation_ids",
                    "quantitative_observation_ids",
                )
                if mixed.get(field)
            ),
            "",
        ).split("|")
        qual_ids = [item for item in mixed.get("qualitative_observation_ids", "").split("|") if item]
        quant_ids = [item for item in quant_ids if item]
        if not quant_ids or not qual_ids:
            raise RuntimeError("An active mixed join lacks quantitative or qualitative members")
        if any(item not in quant_by_id or not active(quant_by_id[item]) for item in quant_ids):
            raise RuntimeError("An active mixed join points to an inactive/missing quantitative record")
        if any(item not in qual_by_id or not active(qual_by_id[item]) for item in qual_ids):
            raise RuntimeError("An active mixed join points to an inactive/missing qualitative record")
    # Some qualitative provenance rows retain five historical mixed keys whose
    # corresponding mixed records were deactivated before this layer. They are
    # preserved byte-for-byte rather than repaired or inferred. Active mixed
    # records themselves must still resolve every declared member above.
    historical_mixed_key_references = {
        row["mixed_join_key"]
        for row in rows["quantitative"] + rows["qualitative"]
        if row.get("mixed_join_key") and row["mixed_join_key"] not in mixed_by_key
    }
    if len(historical_mixed_key_references) != 5:
        raise RuntimeError("Historical mixed-key provenance count changed")

    metadata_fields = (
        "extraction_case_id",
        "text_table_detection_id",
        "source_review_id",
        "candidate_queue_row_id",
        "state",
        "municipality",
        "government_name",
        "unit_type",
        "candidate_source_type",
    )
    cases: dict[str, dict[str, Any]] = {}
    unresolved_case_ids = {
        row["extraction_case_id"]
        for row in rows["quantitative"]
        if row.get("readable_conflict_qa_resolution_id") in EXPECTED_UNRESOLVED
    }
    duplicate_case_ids = {row["extraction_case_id"] for row in duplicate_rows}
    for lane, lane_rows in rows.items():
        for row in lane_rows:
            document_id = row.get("document_identity_id", "")
            if not document_id:
                raise RuntimeError("A package row lacks document identity")
            metadata = tuple(row.get(field, "") for field in metadata_fields)
            if document_id not in cases:
                cases[document_id] = {
                    "metadata": metadata,
                    "source": Counter(),
                    "active": Counter(),
                    "inactive": False,
                }
            elif cases[document_id]["metadata"] != metadata:
                raise RuntimeError("Case metadata conflict across separate ledgers")
            cases[document_id]["source"][lane] += 1
            cases[document_id]["active"][lane] += int(active(row))
            cases[document_id]["inactive"] = cases[document_id]["inactive"] or not active(row)

    if len(cases) != 1826:
        raise RuntimeError("Package does not cover exactly 1,826 document identities")
    unit_counts = Counter(value["metadata"][7] for value in cases.values())
    state_count = len({value["metadata"][4] for value in cases.values()})
    source_family_counts = Counter(value["metadata"][8] for value in cases.values())
    if dict(sorted(unit_counts.items())) != EXPECTED_UNIT_COUNTS:
        raise RuntimeError("Unit representation changed")
    if state_count != 51 or dict(sorted(source_family_counts.items())) != EXPECTED_SOURCE_COUNTS:
        raise RuntimeError("State or source-family representation changed")
    if authority.get("cumulative_unique_content_hash_count") != 1826:
        raise RuntimeError("Independent content-hash coverage attestation changed")

    case_index: list[dict[str, Any]] = []
    for document_id, value in sorted(cases.items()):
        meta = dict(zip(metadata_fields, value["metadata"]))
        source = value["source"]
        active_rows = value["active"]
        case_index.append(
            {
                "document_identity_id": document_id,
                "retained_content_hash_reference": document_id,
                "retained_content_hash_status": "opaque_sha256_derived_identity_from_frozen_selection",
                **meta,
                "quantitative_source_row_count": source["quantitative"],
                "quantitative_active_row_count": active_rows["quantitative"],
                "qualitative_source_row_count": source["qualitative"],
                "qualitative_active_row_count": active_rows["qualitative"],
                "mixed_source_row_count": source["mixed"],
                "mixed_active_row_count": active_rows["mixed"],
                "non_base_wage_source_row_count": source["non_base_wage"],
                "non_base_wage_active_row_count": active_rows["non_base_wage"],
                "reference_and_exclusion_source_row_count": source["reference_and_exclusion"],
                "reference_and_exclusion_active_row_count": active_rows["reference_and_exclusion"],
                "has_inactive_provenance_rows": str(value["inactive"]).lower(),
                "has_duplicate_provenance": str(meta["extraction_case_id"] in duplicate_case_ids).lower(),
                "has_explicit_unresolved_conflict": str(meta["extraction_case_id"] in unresolved_case_ids).lower(),
            }
        )

    conflict_register: list[dict[str, Any]] = []
    for resolution_id, expected_ids in EXPECTED_UNRESOLVED.items():
        group = [
            row for row in rows["quantitative"]
            if row.get("readable_conflict_qa_resolution_id") == resolution_id
        ]
        ids = {row["quantitative_observation_id"] for row in group}
        if ids != expected_ids:
            raise RuntimeError("Unresolved conflict membership changed")
        conflict_register.append(
            {
                "resolution_id": resolution_id,
                "extraction_case_id": group[0]["extraction_case_id"],
                "quantitative_observation_ids": "|".join(sorted(ids)),
                "observation_count": len(ids),
                "resolution_classification": "insufficient_evidence_needs_review",
                "resolution_status": "unresolved",
                "reason_codes": "BOUNDED_EVIDENCE_REMAINS_UNDERSPECIFIED",
                "active_flags": "|".join(sorted({row["active_in_readable_conflict_qa_lane"] for row in group})),
                "bounded_evidence_pointers": "|".join(sorted({row["bounded_evidence_pointer"] for row in group})),
                "ambiguity_preservation": "preserved_without_inference",
            }
        )

    return {
        "generated_at": now(),
        "authority": authority,
        "paths": paths,
        "headers": headers,
        "rows": rows,
        "input_sha256": input_hashes,
        "header_sha256": header_hashes,
        "source_counts": lane_source_counts,
        "active_counts": active_counts,
        "case_index": case_index,
        "conflict_register": conflict_register,
        "duplicate_observation_id_count": duplicate_observation_id_count,
        "duplicate_provenance_row_count": len(duplicate_rows),
        "newly_canonicalized_duplicate_count": len(new_canonicalized),
        "invalid_bounded_page_pointer_count": invalid_pointers,
        "base_non_base_wage_contamination_count": len(contamination),
        "working_out_of_classification_reroute_count": len(reroute_sources),
        "wasco_record_boundary_repair_count": len(wasco),
        "case_count": len(cases),
        "unique_readable_content_hash_count": 1826,
        "content_hash_coverage_method": "opaque_document_identity_derived_from_retained_hash_plus_independent_review_attestation",
        "unit_type_counts": dict(sorted(unit_counts.items())),
        "state_count": state_count,
        "source_family_counts": dict(sorted(source_family_counts.items())),
        "unresolved_conflict_group_count": len(conflict_register),
        "unresolved_quantitative_conflict_rate": round(2 / active_counts["quantitative"], 8),
        "historical_mixed_key_provenance_count": len(historical_mixed_key_references),
    }


def summary_from_reconciliation(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "generated_at": result["generated_at"],
        "merge_method": "immutable_five_ledger_byte_copy_package_promotion",
        "merge_data_input_count": 5,
        "merge_data_inputs": [INPUT_SPECS[lane]["input"] for lane in INPUT_SPECS],
        "input_sha256": result["input_sha256"],
        "source_row_counts": result["source_counts"],
        "active_row_counts": result["active_counts"],
        "case_count": result["case_count"],
        "unique_readable_content_hash_count": result["unique_readable_content_hash_count"],
        "content_hash_coverage_method": result["content_hash_coverage_method"],
        "unit_type_counts": result["unit_type_counts"],
        "state_count": result["state_count"],
        "source_family_counts": result["source_family_counts"],
        "duplicate_observation_id_count": result["duplicate_observation_id_count"],
        "duplicate_provenance_row_count": result["duplicate_provenance_row_count"],
        "newly_canonicalized_duplicate_count": result["newly_canonicalized_duplicate_count"],
        "invalid_bounded_page_pointer_count": result["invalid_bounded_page_pointer_count"],
        "base_non_base_wage_contamination_count": result["base_non_base_wage_contamination_count"],
        "working_out_of_classification_reroute_count": result["working_out_of_classification_reroute_count"],
        "wasco_record_boundary_repair_count": result["wasco_record_boundary_repair_count"],
        "historical_mixed_key_provenance_count": result["historical_mixed_key_provenance_count"],
        "unresolved_conflict_group_count": result["unresolved_conflict_group_count"],
        "unresolved_quantitative_conflict_rate": result["unresolved_quantitative_conflict_rate"],
        "ocr_later_documents_excluded": True,
        "schemas_remain_separate": True,
        "source_ledgers_mutated": False,
        "final_analysis_ready": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "wage_gap_analysis_allowed": False,
        "regression_allowed": False,
    }


def write_package(stage: Path, result: dict[str, Any]) -> dict[str, Any]:
    for lane, spec in INPUT_SPECS.items():
        output = stage / spec["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(result["paths"][lane], output)

    write_csv(stage / "final_provisional_case_index.csv", CASE_FIELDS, result["case_index"])
    write_csv(
        stage / "final_provisional_conflict_register.csv",
        CONFLICT_FIELDS,
        result["conflict_register"],
    )
    summary = summary_from_reconciliation(result)
    output_hashes = {
        spec["output"]: sha_file(stage / spec["output"])
        for spec in INPUT_SPECS.values()
    }
    summary["output_sha256"] = output_hashes
    summary["all_output_ledgers_byte_identical"] = all(
        (stage / spec["output"]).read_bytes()
        == result["paths"][lane].read_bytes()
        for lane, spec in INPUT_SPECS.items()
    )

    manifest = {
        **summary,
        "package_status": "final_provisional_package_materialized_qa_pass",
        "output_directory": str(DEFAULT_OUTPUT.relative_to(ROOT)),
        "case_index": "final_provisional_case_index.csv",
        "conflict_register": "final_provisional_conflict_register.csv",
        "ledger_outputs": {lane: spec["output"] for lane, spec in INPUT_SPECS.items()},
    }
    write_json(stage / "final_provisional_merge_manifest.json", manifest)
    write_json(stage / "final_provisional_reconciliation_summary.json", summary)
    (stage / "final_provisional_input_sha256.txt").write_text(
        "".join(
            f"{result['input_sha256'][spec['input']]}  {spec['input']}\n"
            for spec in INPUT_SPECS.values()
        ),
        encoding="utf-8",
    )
    (stage / "final_provisional_output_sha256.txt").write_text(
        "".join(f"{output_hashes[path]}  {path}\n" for path in sorted(output_hashes)),
        encoding="utf-8",
    )
    report = f"""# Final provisional compensation-evidence reconciliation

## Outcome

Five immutable corrected shadow ledgers were promoted as five separate,
byte-identical provisional package ledgers. No cross-schema concatenation,
normalization, extraction, inference, ingestion, codification, or analysis ran.

## Counts

| Schema | Source rows | Active rows |
| --- | ---: | ---: |
| Quantitative base compensation | {result['source_counts']['quantitative']:,} | {result['active_counts']['quantitative']:,} |
| Qualitative mechanisms | {result['source_counts']['qualitative']:,} | {result['active_counts']['qualitative']:,} |
| Mixed quant/qual joins | {result['source_counts']['mixed']:,} | {result['active_counts']['mixed']:,} |
| Non-base-wage compensation | {result['source_counts']['non_base_wage']:,} | {result['active_counts']['non_base_wage']:,} |
| Reference/exclusion | {result['source_counts']['reference_and_exclusion']:,} | {result['active_counts']['reference_and_exclusion']:,} |

- Cases / opaque content-hash-derived identities: {result['case_count']:,}
- Independent-review unique readable content-hash attestation: {result['unique_readable_content_hash_count']:,}
- Unit representation: {result['unit_type_counts']}
- States/DC: {result['state_count']}
- Source families: {len(result['source_family_counts'])}
- Duplicate observation IDs: {result['duplicate_observation_id_count']}
- Duplicate provenance rows: {result['duplicate_provenance_row_count']}
- Invalid bounded page pointers: {result['invalid_bounded_page_pointer_count']}
- Base/non-base contamination: {result['base_non_base_wage_contamination_count']}
- Explicit unresolved groups: {result['unresolved_conflict_group_count']}
- Unresolved rate: {result['unresolved_quantitative_conflict_rate']:.4%}

## Boundary

The package is provisional. Analysis readiness, ingestion, codification,
wage-gap analysis, and regression remain false. OCR-later documents remain
excluded. The next action is a separate schema/analysis-readiness review.
"""
    (stage / "final_provisional_reconciliation_report.md").write_text(report, encoding="utf-8")

    decision = {
        **summary,
        "decision": "final_provisional_package_materialized_qa_pass",
        "qa_pass": True,
        "package_materialized": True,
        "dashboard_status_required": "compensation_extraction_final_provisional_package_materialized_qa_pass",
        "next_recommendation": "separate_schema_and_analysis_readiness_review",
    }
    write_json(stage / "final_provisional_decision.json", decision)
    validation = f"""# Final provisional package validation - 2026-07-25

- Five approved input SHA-256 values: pass (5 / 5)
- Exactly five merge-data inputs: pass
- Five schemas remain separate: pass
- Output ledgers byte-for-byte equal inputs: pass
- Source rows: pass ({result['source_counts']})
- Active rows: pass ({result['active_counts']})
- Unique case/content-hash-derived identities: pass ({result['case_count']})
- Duplicate observation IDs: pass ({result['duplicate_observation_id_count']})
- Duplicate provenance rows: pass ({result['duplicate_provenance_row_count']})
- Newly canonicalized duplicates: pass ({result['newly_canonicalized_duplicate_count']})
- Invalid bounded page pointers: pass ({result['invalid_bounded_page_pointer_count']})
- Base/non-base contamination: pass ({result['base_non_base_wage_contamination_count']})
- Working-out-of-classification reroutes: pass ({result['working_out_of_classification_reroute_count']})
- Wasco shadow repair: pass ({result['wasco_record_boundary_repair_count']})
- Explicit unresolved groups: pass ({result['unresolved_conflict_group_count']})
- Mixed joins and member IDs: pass
- Unit/state/source representation: pass
- OCR-later documents excluded: pass
- Analysis readiness remains false: pass

Repository-wide validation results are appended after the required command
suite completes.
"""
    (stage / "final_provisional_validation_2026-07-25.md").write_text(
        validation, encoding="utf-8"
    )
    return decision


def validate_materialized_package(output_dir: Path, result: dict[str, Any]) -> None:
    for lane, spec in INPUT_SPECS.items():
        output = output_dir / spec["output"]
        if not output.is_file():
            raise RuntimeError(f"Missing materialized output: {spec['output']}")
        if output.read_bytes() != result["paths"][lane].read_bytes():
            raise RuntimeError(f"Output bytes differ from approved input: {lane}")
        if sha_file(output) != spec["sha256"]:
            raise RuntimeError(f"Output SHA-256 differs from approved input: {lane}")
    fields, case_rows = read_csv(output_dir / "final_provisional_case_index.csv")
    if fields != CASE_FIELDS or len(case_rows) != 1826:
        raise RuntimeError("Final provisional case index does not reconcile")
    fields, conflicts = read_csv(output_dir / "final_provisional_conflict_register.csv")
    if fields != CONFLICT_FIELDS or len(conflicts) != 2:
        raise RuntimeError("Final provisional conflict register does not reconcile")
    decision = json.loads((output_dir / "final_provisional_decision.json").read_text(encoding="utf-8"))
    if not (
        decision.get("decision") == "final_provisional_package_materialized_qa_pass"
        and decision.get("qa_pass") is True
        and decision.get("final_analysis_ready") is False
        and decision.get("ingestion_allowed") is False
        and decision.get("codify_allowed") is False
    ):
        raise RuntimeError("Final provisional package decision is unsafe")


def run_dry_run(input_dir: Path, authority_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError("Dry-run target/final output directory already exists")
    result = reconcile_inputs(input_dir, authority_path)
    return {
        **summary_from_reconciliation(result),
        "status": "dry_run_reconciliation_passed_no_output_written",
        "output_directory_created": False,
    }


def materialize(
    input_dir: Path,
    authority_path: Path,
    output_dir: Path,
    *,
    explicitly_authorized: bool,
    no_ingestion: bool,
    no_codify: bool,
    no_analysis: bool,
) -> dict[str, Any]:
    if not (explicitly_authorized and no_ingestion and no_codify and no_analysis):
        raise PermissionError("Explicit merge authorization and all stop flags are required")
    if output_dir.exists():
        raise FileExistsError("Final provisional output directory already exists")
    result = reconcile_inputs(input_dir, authority_path)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    try:
        decision = write_package(stage, result)
        validate_materialized_package(stage, result)
        stage.rename(output_dir)
        validate_materialized_package(output_dir, result)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", required=True, choices=("dry_run", "materialize_provisional_package")
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-explicit-merge-authorization", action="store_true")
    parser.add_argument("--no-ingestion", action="store_true")
    parser.add_argument("--no-codify", action="store_true")
    parser.add_argument("--no-analysis", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output != DEFAULT_OUTPUT.resolve():
        raise ValueError("CLI output directory must be the prepared prompt's exact path")
    if args.mode == "dry_run":
        value = run_dry_run(INPUT_DIR, AUTHORITY_PATH, output)
    else:
        value = materialize(
            INPUT_DIR,
            AUTHORITY_PATH,
            output,
            explicitly_authorized=args.require_explicit_merge_authorization,
            no_ingestion=args.no_ingestion,
            no_codify=args.no_codify,
            no_analysis=args.no_analysis,
        )
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
