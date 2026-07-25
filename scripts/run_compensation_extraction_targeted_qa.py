#!/usr/bin/env python3
"""Resolve the frozen 500-document compensation extraction QA queue.

This is an offline, deterministic QA pass.  It never opens URLs, performs OCR,
calls GABRIEL, or mutates the provisional extraction ledgers.  Every source row
is retained in a corrected shadow ledger; inactive duplicates and reroutes are
marked explicitly so provenance remains recoverable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = (
    "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-"
    "TARGETED-QA-AND-DASHBOARD-PUSH-2026-07-25"
)
SOURCE_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25"
)

REVIEW = "compensation_extraction_500_conflict_review.csv"
PACKET = "compensation_extraction_500_packet_manifest.csv"
SELECTION = "compensation_extraction_500_selection_manifest.csv"
DECISION = "compensation_extraction_500_decision_report.json"
QUANT = "lanes/quantitative/quantitative_extraction_ledger.csv"
QUAL = "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv"
MIXED = "lanes/mixed/mixed_extraction_ledger.csv"
NONBASE = "lanes/non_base_wage/non_base_wage_compensation_ledger.csv"
REFERENCE = "lanes/reference_and_exclusion/reference_exclusion_ledger.csv"

QA_COLUMNS = [
    "qa_original_status",
    "qa_resolution_id",
    "qa_resolution_classification",
    "qa_resolution_status",
    "canonical_observation_id",
    "duplicate_of",
    "active_in_corrected_lane",
]

RESOLUTION_FIELDS = [
    "qa_resolution_id",
    "review_queue_row_number",
    "review_type",
    "extraction_case_id",
    "page_number",
    "lane",
    "source_observation_ids",
    "source_observation_count",
    "resolution_classification",
    "resolution_status",
    "canonical_observation_id",
    "duplicate_observation_ids",
    "affected_quantitative_observation_ids",
    "affected_non_base_wage_observation_ids",
    "corrected_quantitative_action",
    "corrected_non_base_wage_action",
    "local_evidence_inspected",
    "bounded_evidence_pointer",
    "structured_basis",
    "confidence",
    "unresolved_flag",
    "notes",
]

CONFLICT_CLASSES = {
    "true_conflict_unresolved",
    "distinct_schedule_cell",
    "distinct_effective_period",
    "distinct_classification_or_rank",
    "duplicate_or_same_observation",
    "non_base_wage_misroute",
    "insufficient_evidence_needs_review",
}
NONBASE_REVIEW_CLASSES = {
    "retain_quantitative_base_wage",
    "route_to_non_base_wage",
    "split_quant_and_non_base_components",
    "reference_only",
    "insufficient_evidence_needs_review",
}

NONBASE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("overtime", re.compile(r"\b(overtime|double[ -]?time|time and (?:one[- ]half|a half)|time-and-one-half|callback|call[- ]?back|standby|on[- ]?call|compensatory)\b", re.I)),
    ("stipend", re.compile(r"\b(stipend|incentive payment|bonus|premium|differential|allowance|hazard pay|acting pay|out[- ]of[- ]class)\b", re.I)),
    ("longevity", re.compile(r"\blongevity\b|\byears? of service\b", re.I)),
    ("education_or_certification", re.compile(r"\b(certif(?:ication|ied)?|education pay|degree pay|training pay)\b", re.I)),
    ("healthcare_contributions", re.compile(r"\b(health(?:care)?|medical|insurance contribution)\b", re.I)),
    ("pension", re.compile(r"\b(pension\w*|retirement contribution)\b", re.I)),
    ("leave", re.compile(r"\b(leave|vacation|sick pay|holiday pay|funeral leave|jury duty)\b", re.I)),
    ("reimbursements", re.compile(r"\b(reimburse|mileage|travel|meal)\w*\b", re.I)),
    ("uniform_or_equipment", re.compile(r"\b(uniform|equipment|clothing)\w*\b", re.I)),
    ("benefits", re.compile(r"\b(benefit|insurance)\w*\b", re.I)),
)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_fields(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return next(reader)


def write_csv(
    path: Path, fields: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *values: str) -> str:
    payload = "\x1f".join(values).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:24]}"


def truth(value: bool) -> str:
    return "true" if value else "false"


def row_diagnostic(row: dict[str, str]) -> str:
    keys = (
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
    # Reason codes conventionally use underscores. Treat them as separators so
    # word-boundary QA rules behave the same for codes and visible values.
    return " ".join(row.get(key, "") for key in keys).replace("_", " ")


def nonbase_type(row: dict[str, str]) -> str | None:
    diagnostic = row_diagnostic(row)
    for label, pattern in NONBASE_PATTERNS:
        if pattern.search(diagnostic):
            return label
    return None


def conflict_resolution(rows: list[dict[str, str]]) -> tuple[str, str]:
    """Classify a same-key/different-value group using only structured fields."""
    if not rows:
        raise ValueError("Conflict group is empty")
    detected_nonbase = sorted({nonbase_type(row) for row in rows} - {None})
    if detected_nonbase:
        return (
            "non_base_wage_misroute",
            "Structured values/reason codes identify non-base compensation: "
            + ", ".join(detected_nonbase),
        )

    compensation_type = rows[0]["compensation_type"]
    reasons = [row["reason_code"] for row in rows]
    all_reasons_distinct = len(set(reasons)) == len(reasons)

    if compensation_type == "percentage_increase":
        year_sets = [
            tuple(
                sorted(
                    set(
                        YEAR_RE.findall(
                            " ".join(
                                (
                                    row["reason_code"],
                                    row["percentage_increase"],
                                    row["salary_value"],
                                )
                            ).replace("_", " ")
                        )
                    )
                )
            )
            for row in rows
        ]
        if any(year_sets) and len(set(year_sets)) > 1:
            return (
                "distinct_effective_period",
                "Different year tokens identify distinct effective periods.",
            )
        if all_reasons_distinct:
            return (
                "distinct_schedule_cell",
                "Distinct reason codes identify separate percentage components/cells.",
            )
        if any(
            re.search(r"NAMED|RANK|CLASS|STEP|GRADE|MARKET|EQUITY", reason, re.I)
            for reason in reasons
        ):
            return (
                "distinct_classification_or_rank",
                "Reason codes distinguish named/classified/market pay components.",
            )
        return (
            "insufficient_evidence_needs_review",
            "Different percentage values share the same structured period and reason code.",
        )

    if compensation_type in {
        "hourly_rate",
        "annual_salary",
        "rate",
        "salary",
    }:
        if all_reasons_distinct:
            return (
                "distinct_classification_or_rank",
                "Distinct structured reason codes identify separate schedule rows/cells.",
            )
        return (
            "insufficient_evidence_needs_review",
            "Different rate/salary values lack a captured rank, step, grade, or distinct reason.",
        )

    if all_reasons_distinct:
        return (
            "distinct_schedule_cell",
            "Distinct reason codes identify separate structured values on the page.",
        )
    return (
        "insufficient_evidence_needs_review",
        "Different values share an under-specified structured key and reason code.",
    )


def possible_nonbase_resolution(row: dict[str, str]) -> tuple[str, str, str]:
    detected = nonbase_type(row)
    if detected:
        return (
            "route_to_non_base_wage",
            detected,
            f"Explicit {detected} signal occurs in the structured value or reason code.",
        )
    return (
        "insufficient_evidence_needs_review",
        "other",
        "The original queue flag is not reproducible from the structured fields.",
    )


def bounded_value(row: dict[str, str]) -> str:
    parts: list[str] = []
    for field in (
        "rate_value",
        "salary_value",
        "hourly_rate",
        "annual_salary",
        "percentage_increase",
    ):
        value = row.get(field, "").strip()
        if value and value not in parts:
            parts.append(value)
    return " | ".join(parts)[:240]


def make_nonbase_from_quant(
    row: dict[str, str], detected_type: str, resolution_id: str
) -> dict[str, str]:
    source_id = row["quantitative_observation_id"]
    target_id = stable_id("nobsqa", source_id, detected_type)
    implementation = " | ".join(
        f"{field}={row[field]}"
        for field in (
            "occupation_unit_classification_rank",
            "pay_band",
            "step",
            "grade",
        )
        if row.get(field)
    )[:240]
    return {
        "non_base_wage_observation_id": target_id,
        "extraction_case_id": row["extraction_case_id"],
        "document_identity_id": row["document_identity_id"],
        "text_table_detection_id": row["text_table_detection_id"],
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "state": row["state"],
        "municipality": row["municipality"],
        "government_name": row["government_name"],
        "unit_type": row["unit_type"],
        "candidate_source_type": row["candidate_source_type"],
        "contract_period_start": row["contract_period_start"],
        "contract_period_end": row["contract_period_end"],
        "page_number": row["page_number"],
        "non_base_wage_type": detected_type,
        "value_text": bounded_value(row),
        "effective_date": row["effective_date"],
        "eligibility_or_implementation_rule": implementation,
        "bounded_evidence_pointer": row["bounded_evidence_pointer"],
        "confidence": row["confidence"],
        "reason_code": f"QA_REROUTED_{detected_type.upper()}"[:40],
        "qa_status": "qa_corrected_routed_from_quantitative",
        "source_quantitative_observation_id": source_id,
        "qa_original_status": row.get("qa_status", ""),
        "qa_resolution_id": resolution_id,
        "qa_resolution_classification": "route_to_non_base_wage",
        "qa_resolution_status": "resolved",
        "canonical_observation_id": target_id,
        "duplicate_of": "",
        "active_in_corrected_lane": "true",
    }


def append_qa_defaults(
    row: dict[str, str], observation_id: str = ""
) -> dict[str, str]:
    result = dict(row)
    result.update(
        {
            "qa_original_status": row.get("qa_status", ""),
            "qa_resolution_id": "",
            "qa_resolution_classification": "not_in_targeted_queue",
            "qa_resolution_status": "not_applicable",
            "canonical_observation_id": observation_id,
            "duplicate_of": "",
            "active_in_corrected_lane": "true",
        }
    )
    return result


def resolve(
    source_dir: Path, output_dir: Path, *, write_outputs: bool = True
) -> dict[str, Any]:
    required = [
        REVIEW,
        PACKET,
        SELECTION,
        DECISION,
        QUANT,
        QUAL,
        MIXED,
        NONBASE,
        REFERENCE,
    ]
    missing = [name for name in required if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing required inputs: " + ", ".join(missing))

    input_hashes = {name: sha_file(source_dir / name) for name in required}
    review = read_csv(source_dir / REVIEW)
    if len(review) != 187:
        raise ValueError(f"Expected 187 review rows, found {len(review)}")
    review_counts = Counter(row["review_type"] for row in review)
    expected_review = {
        "exact_content_duplicate": 2,
        "potential_quantitative_conflict": 83,
        "possible_non_base_wage_in_quantitative_lane": 102,
    }
    if dict(review_counts) != expected_review:
        raise ValueError(f"Unexpected review queue composition: {review_counts}")

    quant_source = read_csv(source_dir / QUANT)
    qual_source = read_csv(source_dir / QUAL)
    mixed_source = read_csv(source_dir / MIXED)
    nonbase_source = read_csv(source_dir / NONBASE)
    reference_source = read_csv(source_dir / REFERENCE)
    selection = read_csv(source_dir / SELECTION)
    packet = read_csv(source_dir / PACKET)
    original_decision = json.loads((source_dir / DECISION).read_text(encoding="utf-8"))

    quant_fields = read_fields(source_dir / QUANT)
    qual_fields = read_fields(source_dir / QUAL)
    mixed_fields = read_fields(source_dir / MIXED)
    nonbase_fields = read_fields(source_dir / NONBASE)
    reference_fields = read_fields(source_dir / REFERENCE)

    quant = {
        row["quantitative_observation_id"]: append_qa_defaults(
            row, row["quantitative_observation_id"]
        )
        for row in quant_source
    }
    nonbase = {
        row["non_base_wage_observation_id"]: append_qa_defaults(
            row, row["non_base_wage_observation_id"]
        )
        for row in nonbase_source
    }
    qualitative = [
        append_qa_defaults(row, row["qualitative_observation_id"])
        for row in qual_source
    ]
    references = [append_qa_defaults(row) for row in reference_source]

    resolutions: list[dict[str, str]] = []
    duplicate_map: dict[str, str] = {}
    routed_quant: dict[str, tuple[str, str]] = {}
    conflict_classes: Counter[str] = Counter()
    nonbase_classes: Counter[str] = Counter()

    for queue_number, queued in enumerate(review, 1):
        ids = [value for value in queued["observation_ids"].split("|") if value]
        resolution_id = stable_id(
            "qares",
            str(queue_number),
            queued["review_type"],
            queued["extraction_case_id"],
            queued["page_number"],
            queued["observation_ids"],
        )
        resolution_class = ""
        resolution_status = "resolved"
        canonical = ""
        duplicates: list[str] = []
        affected_quant: list[str] = []
        affected_nonbase: list[str] = []
        quant_action = "no_change"
        nonbase_action = "no_change"
        basis = ""
        confidence = "high"
        unresolved = False
        notes = ""

        if queued["review_type"] == "exact_content_duplicate":
            lane = queued["lane"]
            source_order = quant_source if lane == "quantitative" else nonbase_source
            id_field = (
                "quantitative_observation_id"
                if lane == "quantitative"
                else "non_base_wage_observation_id"
            )
            order = {row[id_field]: index for index, row in enumerate(source_order)}
            ids.sort(key=order.__getitem__)
            canonical, duplicates = ids[0], ids[1:]
            resolution_class = "duplicate_or_same_observation"
            basis = "Exact structured content repeats; earliest source-ledger row is canonical."
            if lane == "quantitative":
                affected_quant = ids
                quant_action = "canonicalize_preserve_all_rows"
                target = quant
            else:
                affected_nonbase = ids
                nonbase_action = "canonicalize_preserve_all_rows"
                target = nonbase
            for observation_id in ids:
                target[observation_id].update(
                    {
                        "qa_resolution_id": resolution_id,
                        "qa_resolution_classification": resolution_class,
                        "qa_resolution_status": "resolved",
                        "canonical_observation_id": canonical,
                        "duplicate_of": "" if observation_id == canonical else canonical,
                        "active_in_corrected_lane": truth(observation_id == canonical),
                        "qa_status": (
                            "qa_corrected_canonical"
                            if observation_id == canonical
                            else "qa_corrected_duplicate_inactive"
                        ),
                    }
                )
                if observation_id != canonical:
                    duplicate_map[observation_id] = canonical

        elif queued["review_type"] == "potential_quantitative_conflict":
            rows = [quant[observation_id] for observation_id in ids]
            resolution_class, basis = conflict_resolution(rows)
            if resolution_class not in CONFLICT_CLASSES:
                raise AssertionError(resolution_class)
            conflict_classes[resolution_class] += 1
            affected_quant = ids
            quant_action = "retain_distinct_active_records"
            if resolution_class == "non_base_wage_misroute":
                quant_action = "deactivate_and_route_to_non_base_wage"
                nonbase_action = "create_corrected_non_base_records"
                for observation_id, row in zip(ids, rows):
                    detected = nonbase_type(row) or "other"
                    routed_quant[observation_id] = (detected, resolution_id)
            elif resolution_class in {
                "true_conflict_unresolved",
                "insufficient_evidence_needs_review",
            }:
                unresolved = True
                resolution_status = "unresolved"
                confidence = "low"
                quant_action = "retain_active_flag_unresolved"
            else:
                confidence = "medium"
            for observation_id in ids:
                quant[observation_id].update(
                    {
                        "qa_resolution_id": resolution_id,
                        "qa_resolution_classification": resolution_class,
                        "qa_resolution_status": resolution_status,
                        "qa_status": (
                            "targeted_qa_unresolved"
                            if unresolved
                            else "qa_corrected_pending_reroute"
                            if resolution_class == "non_base_wage_misroute"
                            else "qa_corrected_distinct_structured_value"
                        ),
                    }
                )

        elif queued["review_type"] == "possible_non_base_wage_in_quantitative_lane":
            if len(ids) != 1:
                raise ValueError("Non-base review row must contain exactly one observation")
            observation_id = ids[0]
            row = quant[observation_id]
            resolution_class, detected, basis = possible_nonbase_resolution(row)
            if resolution_class not in NONBASE_REVIEW_CLASSES:
                raise AssertionError(resolution_class)
            nonbase_classes[resolution_class] += 1
            affected_quant = ids
            if resolution_class == "route_to_non_base_wage":
                quant_action = "deactivate_and_route_to_non_base_wage"
                nonbase_action = "create_corrected_non_base_record"
                routed_quant[observation_id] = (detected, resolution_id)
                row.update(
                    {
                        "qa_resolution_id": resolution_id,
                        "qa_resolution_classification": resolution_class,
                        "qa_resolution_status": "resolved",
                        "qa_status": "qa_corrected_pending_reroute",
                    }
                )
            else:
                unresolved = resolution_class == "insufficient_evidence_needs_review"
                resolution_status = "unresolved" if unresolved else "resolved"
                confidence = "low" if unresolved else "medium"
                quant_action = "retain_active_flag_unresolved" if unresolved else "retain_active"
                row.update(
                    {
                        "qa_resolution_id": resolution_id,
                        "qa_resolution_classification": resolution_class,
                        "qa_resolution_status": resolution_status,
                        "qa_status": "targeted_qa_unresolved" if unresolved else "qa_corrected_retained",
                    }
                )
        else:
            raise ValueError(f"Unsupported review type: {queued['review_type']}")

        pointers = sorted(
            {
                quant[observation_id]["bounded_evidence_pointer"]
                for observation_id in affected_quant
                if observation_id in quant
            }
            | {
                nonbase[observation_id]["bounded_evidence_pointer"]
                for observation_id in affected_nonbase
                if observation_id in nonbase
            }
        )
        resolutions.append(
            {
                "qa_resolution_id": resolution_id,
                "review_queue_row_number": str(queue_number),
                "review_type": queued["review_type"],
                "extraction_case_id": queued["extraction_case_id"],
                "page_number": queued["page_number"],
                "lane": queued["lane"],
                "source_observation_ids": "|".join(ids),
                "source_observation_count": queued["observation_count"],
                "resolution_classification": resolution_class,
                "resolution_status": resolution_status,
                "canonical_observation_id": canonical,
                "duplicate_observation_ids": "|".join(duplicates),
                "affected_quantitative_observation_ids": "|".join(affected_quant),
                "affected_non_base_wage_observation_ids": "|".join(affected_nonbase),
                "corrected_quantitative_action": quant_action,
                "corrected_non_base_wage_action": nonbase_action,
                "local_evidence_inspected": "structured_fields_and_bounded_pointer_only",
                "bounded_evidence_pointer": "|".join(pointers),
                "structured_basis": basis[:500],
                "confidence": confidence,
                "unresolved_flag": truth(unresolved),
                "notes": notes,
            }
        )

    # Materialize reroutes after all queue rows so overlapping conflict and
    # non-base reviews produce one deterministic non-base record per source ID.
    rerouted_nonbase_by_quant: dict[str, str] = {}
    for observation_id, (detected, resolution_id) in sorted(routed_quant.items()):
        row = quant[observation_id]
        row.update(
            {
                "qa_resolution_id": resolution_id,
                "qa_resolution_classification": "route_to_non_base_wage",
                "qa_resolution_status": "resolved",
                "qa_status": "qa_corrected_routed_to_non_base_wage",
                "active_in_corrected_lane": "false",
            }
        )
        created = make_nonbase_from_quant(row, detected, resolution_id)
        nonbase[created["non_base_wage_observation_id"]] = created
        rerouted_nonbase_by_quant[observation_id] = created[
            "non_base_wage_observation_id"
        ]

    for resolution in resolutions:
        source_quant_ids = [
            item
            for item in resolution["affected_quantitative_observation_ids"].split("|")
            if item
        ]
        created_ids = [
            rerouted_nonbase_by_quant[item]
            for item in source_quant_ids
            if item in rerouted_nonbase_by_quant
        ]
        if created_ids:
            resolution["affected_non_base_wage_observation_ids"] = "|".join(
                created_ids
            )

    mixed_corrected: list[dict[str, str]] = []
    for source_row in mixed_source:
        row = append_qa_defaults(source_row, source_row["mixed_join_key"])
        source_quant_ids = [
            item for item in source_row["quantitative_observation_ids"].split("|") if item
        ]
        corrected_quant_ids: list[str] = []
        for observation_id in source_quant_ids:
            canonical = duplicate_map.get(observation_id, observation_id)
            if quant[canonical]["active_in_corrected_lane"] == "true" and canonical not in corrected_quant_ids:
                corrected_quant_ids.append(canonical)
        qualitative_ids = [
            item for item in source_row["qualitative_observation_ids"].split("|") if item
        ]
        active = bool(corrected_quant_ids and qualitative_ids)
        row.update(
            {
                "quantitative_observation_ids": "|".join(corrected_quant_ids),
                "quantitative_observation_count": str(len(corrected_quant_ids)),
                "qualitative_observation_count": str(len(qualitative_ids)),
                "qa_original_status": source_row.get("qa_status", ""),
                "qa_resolution_classification": (
                    "mixed_membership_corrected"
                    if corrected_quant_ids != source_quant_ids
                    else "not_in_targeted_queue"
                ),
                "qa_resolution_status": "resolved" if corrected_quant_ids != source_quant_ids else "not_applicable",
                "qa_status": "qa_corrected_mixed_membership" if corrected_quant_ids != source_quant_ids else source_row.get("qa_status", ""),
                "active_in_corrected_lane": truth(active),
            }
        )
        mixed_corrected.append(row)

    quant_rows = list(quant.values())
    nonbase_rows = list(nonbase.values())
    active_quant = [row for row in quant_rows if row["active_in_corrected_lane"] == "true"]
    active_qual = [row for row in qualitative if row["active_in_corrected_lane"] == "true"]
    active_mixed = [row for row in mixed_corrected if row["active_in_corrected_lane"] == "true"]
    active_nonbase = [row for row in nonbase_rows if row["active_in_corrected_lane"] == "true"]
    active_reference = [row for row in references if row["active_in_corrected_lane"] == "true"]

    packet_pages: dict[str, set[int]] = defaultdict(set)
    for row in packet:
        packet_pages[row["extraction_case_id"]].add(int(row["page_number"]))
    invalid_pages = sum(
        int(row["page_number"]) not in packet_pages[row["extraction_case_id"]]
        for row in active_quant + active_qual + active_nonbase
    )
    observation_ids = (
        [row["quantitative_observation_id"] for row in quant_rows]
        + [row["qualitative_observation_id"] for row in qualitative]
        + [row["non_base_wage_observation_id"] for row in nonbase_rows]
    )
    duplicate_observation_ids = len(observation_ids) - len(set(observation_ids))
    unresolved_conflicts = sum(
        conflict_classes[label]
        for label in ("true_conflict_unresolved", "insufficient_evidence_needs_review")
    )
    unresolved_conflict_rate = unresolved_conflicts / max(1, len(active_quant))
    unresolved_contamination = nonbase_classes["insufficient_evidence_needs_review"]

    unit_counts = Counter(row["unit_type"] for row in selection)
    # The frozen selection records the normalized matched comparison directly;
    # municipality strings can vary across related government names. Preserve
    # the selection's stable comparison IDs instead of re-normalizing names.
    matched_ids = {
        row["matched_non_safety_case_id"]
        for row in selection
        if row.get("matched_non_safety_case_id")
    }
    matched_municipalities = len(matched_ids)
    representation_intact = (
        len(selection) == 500
        and unit_counts == {"police": 180, "fire": 120, "non_safety": 200}
        and matched_municipalities == 200
        and all(row.get("matched_non_safety_selected") == "yes" for row in selection)
    )
    corrected_ledgers_provisional = True
    integrity_pass = (
        original_decision.get("integrity_qa_pass") is True
        and duplicate_observation_ids == 0
        and invalid_pages == 0
        and len(resolutions) == 187
    )
    scale_pass = (
        integrity_pass
        and unresolved_conflict_rate <= 0.02
        and unresolved_contamination == 0
        and representation_intact
        and corrected_ledgers_provisional
    )
    recommendation = (
        "recommend_1000_document_extraction"
        if scale_pass
        else "premature_pending_additional_targeted_qa"
        if integrity_pass
        else "blocked_by_qa_failure"
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at": now(),
        "gabriel_api_used": False,
        "review_rows_processed": len(resolutions),
        "review_type_counts": dict(sorted(review_counts.items())),
        "duplicate_groups_resolved": review_counts["exact_content_duplicate"],
        "duplicate_observations_canonicalized": len(duplicate_map),
        "conflict_group_count": review_counts["potential_quantitative_conflict"],
        "conflict_resolution_counts": dict(sorted(conflict_classes.items())),
        "resolved_conflict_group_count": 83 - unresolved_conflicts,
        "unresolved_conflict_group_count": unresolved_conflicts,
        "unresolved_quantitative_conflict_rate": round(unresolved_conflict_rate, 6),
        "base_non_base_review_counts": dict(sorted(nonbase_classes.items())),
        "quantitative_records_routed_to_non_base_wage": len(routed_quant),
        "unresolved_base_non_base_contamination_count": unresolved_contamination,
        "corrected_quantitative_active_observation_count": len(active_quant),
        "corrected_quantitative_source_row_count": len(quant_rows),
        "corrected_qualitative_active_observation_count": len(active_qual),
        "corrected_mixed_active_case_count": len(active_mixed),
        "corrected_mixed_source_row_count": len(mixed_corrected),
        "corrected_non_base_wage_active_observation_count": len(active_nonbase),
        "corrected_non_base_wage_source_row_count": len(nonbase_rows),
        "corrected_reference_exclusion_active_case_count": len(active_reference),
        "invalid_observation_page_count": invalid_pages,
        "duplicate_observation_id_count": duplicate_observation_ids,
        "selection_count": len(selection),
        "unit_type_counts": dict(sorted(unit_counts.items())),
        "matched_municipality_count": matched_municipalities,
        "matched_representation_intact": representation_intact,
        "corrected_ledgers_provisional_and_separate": corrected_ledgers_provisional,
        "input_sha256": input_hashes,
    }
    decision = {
        **summary,
        "integrity_qa_pass": integrity_pass,
        "scale_qa_pass": scale_pass,
        "qa_status": "pass" if scale_pass else "integrity_pass_scale_hold" if integrity_pass else "fail",
        "decision": recommendation,
        "scale_1000_recommendation": recommendation,
        "scale_1000_allowed": scale_pass,
        "final_analysis_merge_allowed": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "dashboard_status_required": "compensation_extraction_500_targeted_qa_completed",
    }

    if write_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(
            output_dir / "compensation_extraction_500_targeted_qa_resolutions.csv",
            RESOLUTION_FIELDS,
            resolutions,
        )
        write_csv(
            output_dir / "quantitative_extraction_ledger_qa_corrected.csv",
            quant_fields + QA_COLUMNS,
            quant_rows,
        )
        write_csv(
            output_dir / "qualitative_mechanism_extraction_ledger_qa_corrected.csv",
            qual_fields + QA_COLUMNS,
            qualitative,
        )
        write_csv(
            output_dir / "mixed_extraction_ledger_qa_corrected.csv",
            mixed_fields + QA_COLUMNS,
            mixed_corrected,
        )
        write_csv(
            output_dir / "non_base_wage_compensation_ledger_qa_corrected.csv",
            nonbase_fields + ["source_quantitative_observation_id"] + QA_COLUMNS,
            nonbase_rows,
        )
        write_csv(
            output_dir / "reference_exclusion_ledger_qa_corrected.csv",
            reference_fields + QA_COLUMNS,
            references,
        )
        write_json(
            output_dir / "compensation_extraction_500_targeted_qa_summary.json",
            summary,
        )
        write_json(
            output_dir / "compensation_extraction_500_recomputed_decision.json",
            decision,
        )
        report = f"""# Targeted QA report: provisional 500-document compensation extraction

- Review queue rows processed: {len(resolutions)} / 187
- GABRIEL/API used: `false`
- Exact duplicate groups resolved: {review_counts['exact_content_duplicate']}
- Duplicate observations canonicalized: {len(duplicate_map)}
- Quantitative conflict groups: 83
- Conflict resolution counts: `{json.dumps(dict(sorted(conflict_classes.items())), sort_keys=True)}`
- Unresolved conflict groups: {unresolved_conflicts}
- Revised unresolved conflict rate: {unresolved_conflict_rate:.2%}
- Quantitative records rerouted to non-base wage: {len(routed_quant)}
- Unresolved base/non-base contamination: {unresolved_contamination}
- Active corrected quantitative observations: {len(active_quant)}
- Active corrected qualitative observations: {len(active_qual)}
- Active corrected mixed cases: {len(active_mixed)}
- Active corrected non-base-wage observations: {len(active_nonbase)}
- Active corrected reference/exclusion cases: {len(active_reference)}
- Invalid bounded page pointers: {invalid_pages}
- Duplicate observation IDs: {duplicate_observation_ids}
- Matched representation intact: `{truth(representation_intact)}`
- Integrity QA: `{'pass' if integrity_pass else 'fail'}`
- Recomputed scale QA: `{'pass' if scale_pass else 'hold'}`
- 1,000-document recommendation: `{recommendation}`

Every original source row remains present in a shadow ledger. Canonicalization
and rerouting are represented with explicit provenance fields and active-lane
flags; the original provisional extraction ledgers are unchanged. The
corrected ledgers remain provisional and are not final analysis inputs.

No new extraction, GABRIEL/API call, URL access, download, OCR, ingestion,
codification, wage-gap calculation, regression, or final merge occurred.
"""
        (output_dir / "compensation_extraction_500_targeted_qa_report.md").write_text(
            report, encoding="utf-8"
        )
        validation = f"""# Targeted QA structural validation — 2026-07-25

- Required review rows processed: `{'pass' if len(resolutions) == 187 else 'fail'}` ({len(resolutions)})
- Corrected shadow ledgers written separately: `pass`
- Original input hashes recorded: `pass`
- Duplicate observation IDs: `{'pass' if duplicate_observation_ids == 0 else 'fail'}` ({duplicate_observation_ids})
- Invalid bounded page pointers: `{'pass' if invalid_pages == 0 else 'fail'}` ({invalid_pages})
- Unresolved conflict rate at most 2%: `{'pass' if unresolved_conflict_rate <= .02 else 'fail'}` ({unresolved_conflict_rate:.4%})
- Unresolved base/non-base contamination: `{'pass' if unresolved_contamination == 0 else 'fail'}` ({unresolved_contamination})
- Matched unit representation: `{'pass' if representation_intact else 'fail'}`
- GABRIEL/API used: `false`
- Full text/table/raw prompts/raw responses saved: `false`

Repository-wide command validation is recorded in the task result and relay
after all required commands run.
"""
        (
            output_dir
            / "compensation_extraction_500_targeted_qa_validation_2026-07-25.md"
        ).write_text(validation, encoding="utf-8")

    return {
        "summary": summary,
        "decision": decision,
        "resolutions": resolutions,
        "rows": {
            "quantitative": quant_rows,
            "qualitative": qualitative,
            "mixed": mixed_corrected,
            "nonbase": nonbase_rows,
            "reference": references,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = resolve(
        args.source_dir.resolve(),
        args.output_dir.resolve(),
        write_outputs=not args.dry_run,
    )
    print(
        json.dumps(
            {
                "status": "dry_run_valid" if args.dry_run else "targeted_qa_completed",
                "review_rows_processed": result["summary"]["review_rows_processed"],
                "scale_1000_recommendation": result["decision"]["scale_1000_recommendation"],
                "gabriel_api_used": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
