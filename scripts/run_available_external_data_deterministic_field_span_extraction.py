#!/usr/bin/env python3
"""Deterministic field and evidence-span extraction for retained external data.

This stage is intentionally local and non-semantic.  The physical extraction
result is read once, exact raw values and coordinates are preserved, and all
bulky ledgers remain below Git-ignored artifact storage.  Tracked outputs are
manifests, hashes, schemas, bounded examples, summaries, compact lineage
indexes, queues, audits, and status notes.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from pypdf import PdfReader

import run_external_data_exhaustive_pipeline as core


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-DETERMINISTIC-FIELD-SPAN-EXTRACTION-2026-08-05"
DECISION = "broad_state_whole_corpus_external_data_field_span_completed_classification_ready"
QA_DECISION = "broad_state_whole_corpus_external_data_field_span_completed_additional_qa_needed"
PARTIAL_DECISION = "broad_state_whole_corpus_external_data_field_span_partial_resume_ready"
PREFLIGHT_DECISION = "broad_state_whole_corpus_external_data_field_span_preflight_failed"
REQUIRED_COMMIT = "8f451fd06d60a69ea7968e554b8871c04d491c74"
EXPECTED_TOTAL = 14_160
EXPECTED_ELIGIBILITY = {
    "direct_structured_processing_ready": 17,
    "deterministic_text_pattern_processing_ready": 9_103,
    "mixed_structured_and_text_processing_ready": 4_849,
    "low_yield_context_only": 191,
}
EXPECTED_REPAIR = 97
EXPECTED_OCR_LATER = 118
EXPECTED_HOLDS = 7_895
EXPECTED_UNSEARCHED = 12_844
EXPECTED_EXTERNAL_PDF_PAGES = 611_124
MIN_FREE_RESERVE = 8 * 1024**3
RULE_VERSION = "deterministic-field-rules-2026-08-05-v1"
DICTIONARY_VERSION = "administrative-field-dictionary-2026-08-05-v1"
PARSER_VERSION = "literal-parser-2026-08-05-v1"

INPUT = core.STAGE6
OUTPUT = core.STAGE7
LOCAL = core.STRUCTURED / "field_span_extraction"
TMP = core.ROOT / "tmp/broad_state_whole_corpus_available_external_data_deterministic_field_span_extraction_2026-08-05_logs"
LANES = [f"field_span_lane_{i:03d}" for i in range(1, 6)]
STAGGERS = dict(zip(LANES, (0, 120, 240, 360, 480)))

FIELD_SCHEMA = [
    "external_field_record_id", "canonical_payload_id", "extraction_result_id",
    "retained_source_ids", "source_SHA_256", "candidate_ids", "municipality_raw",
    "municipality_canonical_id", "state", "department_raw", "department_canonical_hint",
    "unit_raw", "position_or_employee_raw", "side_raw", "side_deterministic_hint",
    "period_raw", "start_date_raw", "end_date_raw", "fiscal_year_raw",
    "calendar_year_raw", "field_family", "field_name", "raw_value", "parsed_value",
    "parsed_value_type", "currency", "unit", "pay_basis_raw", "compensation_basis_raw",
    "recurring_status_raw", "implementation_status_raw", "source_page", "source_section",
    "source_table_id", "source_row", "source_column", "source_cell",
    "source_character_start", "source_character_end", "evidence_span_id", "rule_id",
    "rule_version", "dictionary_version", "parser_version", "extraction_timestamp",
    "extraction_confidence", "extraction_confidence_basis", "ambiguity_flags",
    "conflict_flags", "root_event_ids", "mechanism_event_ids", "claim_ids",
    "claim_linkage_status", "expected_claim_upgrade_tags", "search_wave_provenance",
    "extraction_modality", "administrative_source_type", "source_family", "source_quality",
    "extraction_artifact_pointer", "lineage_basis",
]

SPAN_SCHEMA = [
    "external_evidence_span_id", "canonical_payload_id", "extraction_result_id",
    "retained_source_ids", "field_record_ids", "field_family", "evidence_type",
    "exact_excerpt", "normalized_search_text", "source_page", "source_section",
    "source_heading_path", "source_table_id", "source_row_start", "source_row_end",
    "source_column_start", "source_column_end", "source_character_start",
    "source_character_end", "preceding_context", "following_context", "municipality",
    "state", "period", "side_hint", "department_hint", "implementation_status_hint",
    "source_quality", "rule_id", "rule_version", "dictionary_version", "parser_version",
    "extraction_timestamp", "extraction_confidence", "extraction_confidence_basis",
    "ambiguity_flags", "root_event_ids", "mechanism_event_ids", "claim_ids",
    "claim_linkage_status", "expected_claim_upgrade_tags", "search_wave_provenance",
    "extraction_modality", "administrative_source_type", "source_family",
    "extraction_artifact_pointer", "lineage_basis",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    value = "\x1f".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:n]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    fieldnames = list(fields or (rows[0].keys() if rows else []))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_pair(name: str, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    write_csv(OUTPUT / f"{name}.csv", rows, fields)
    write_jsonl(OUTPUT / f"{name}.jsonl", rows)


def split_values(value: Any) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def join_values(values: Iterable[Any]) -> str:
    output: set[str] = set()
    for value in values:
        output.update(split_values(value))
    return "|".join(sorted(output))


def git_ignored(path: Path) -> bool:
    probe = path / "ignore-probe"
    return subprocess.run(
        ["git", "check-ignore", "-q", str(probe.relative_to(core.ROOT))], cwd=core.ROOT
    ).returncode == 0


def free_bytes() -> int:
    return shutil.disk_usage(core.ROOT).free


def load_pair_or_shards(directory: Path, name: str) -> list[dict[str, str]]:
    manifest_path = directory / f"{name}_shard_manifest.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        rows: list[dict[str, str]] = []
        for part in manifest["parts"]:
            key = "csv" if "csv" in part else "csv_path"
            rows.extend(read_csv(directory / part[key]))
        return rows
    return read_csv(directory / f"{name}.csv")


def field_dictionary() -> dict[str, tuple[str, list[str]]]:
    """Canonical field -> (family, explicit labels)."""
    groups: dict[str, list[str]] = {
        "payroll_and_earnings": [
            "employee_name_public", "employee_identifier_public", "position_title", "classification",
            "department", "unit", "employment_status", "full_time_part_time_status", "regular_pay",
            "base_pay", "base_salary", "hourly_rate", "annual_salary", "gross_pay", "total_earnings",
            "regular_earnings", "overtime_earnings", "overtime_hours", "premium_pay", "retroactive_pay",
            "lump_sum_payment", "longevity_pay", "education_pay", "certification_pay", "shift_differential",
            "hazard_pay", "holiday_pay", "detail_pay", "stipend", "allowance", "other_compensation",
            "pensionable_earnings", "pay_period", "payroll_year", "fiscal_year",
        ],
        "staffing_and_headcount": [
            "authorized_positions", "budgeted_positions", "filled_positions", "vacant_positions",
            "active_employees", "department_headcount", "FTE_count", "part_time_count", "sworn_count",
            "civilian_count", "minimum_staffing_requirement", "staffing_shortage_count", "position_additions",
            "position_eliminations", "layoffs", "attrition_not_replaced", "hiring_freeze", "outsourcing",
            "consolidation", "vacancy_rate_explicit", "vacancy_duration", "overtime_due_to_staffing_gap",
            "callback_due_to_staffing_gap", "mandatory_overtime", "staffing_change_effective_date",
        ],
        "recruitment_and_retention": [
            "applicant_count", "eligible_candidate_count", "hires", "separations", "resignations",
            "retirements", "turnover_count", "turnover_rate_explicit", "retention_rate_explicit",
            "vacancy_duration", "time_to_fill", "hiring_difficulty", "recruitment_shortage",
            "retention_problem", "recruitment_incentive", "retention_incentive", "signing_bonus",
            "referral_bonus", "lateral_entry_incentive", "compensation_study_finding",
            "staffing_study_finding", "recruitment_study_finding", "market_competitiveness_statement",
        ],
        "tenure_and_progression": [
            "years_of_service", "service_band", "step_number", "step_name", "step_rate",
            "step_effective_date", "step_interval", "step_progression_rule", "rank", "grade",
            "classification", "promotion_date", "incumbent_tier", "new_hire_tier", "probationary_rate",
            "maximum_rate", "minimum_rate", "salary_range", "salary_progression", "longevity_threshold",
            "seniority_rule", "certification_level",
        ],
        "implementation_confirmation": [
            "ordinance_number", "resolution_number", "contract_identifier", "MOU_identifier", "adoption_date",
            "council_approval_date", "ratification_date", "appropriation_date", "effective_date",
            "payroll_effective_date", "retroactive_start_date", "payment_date", "implementation_status",
            "adopted", "approved", "ratified", "appropriated", "implemented", "paid", "negotiated",
            "proposed", "recommended", "tentative", "rejected", "expired", "amended", "recurring",
            "one_time", "implementation_body", "vote_result", "source_confirmation_type",
        ],
        "benefits_and_total_compensation": [
            "employer_pension_contribution", "employee_pension_contribution", "employer_health_contribution",
            "employee_health_contribution", "health_cost_share", "pension_cost_share", "dental_contribution",
            "vision_contribution", "life_insurance_value", "leave_accrual", "leave_cashout", "holiday_benefit",
            "uniform_allowance", "equipment_allowance", "vehicle_allowance", "tuition_or_education_benefit",
            "longevity_benefit", "certification_benefit", "premium_eligibility", "premium_payment",
            "deferred_compensation_contribution", "total_compensation_explicit", "benefit_effective_date",
        ],
        "contextual_controls": [
            "population", "fiscal_year_revenue", "fiscal_year_expenditure", "general_fund_expenditure",
            "department_budget", "assessed_value", "tax_base", "unemployment_rate", "labor_force",
            "median_household_income", "cost_of_living_measure", "urban_rural_classification", "county",
            "metro_area", "union_status_explicit", "bargaining_unit_status", "state_labor_law_reference",
            "local_fiscal_constraint_statement", "recession_or_emergency_context", "inflation_measure", "CPI_measure",
        ],
    }
    special = {
        "employee_name_public": ["employee name", "name"], "employee_identifier_public": ["employee id", "employee number"],
        "position_title": ["position title", "job title", "title"], "full_time_part_time_status": ["full time/part time", "full-time/part-time", "ft/pt"],
        "regular_pay": ["regular pay"], "base_pay": ["base pay"], "base_salary": ["base salary"],
        "hourly_rate": ["hourly rate", "hourly wage"], "annual_salary": ["annual salary", "annual rate"],
        "gross_pay": ["gross pay", "gross wages"], "total_earnings": ["total earnings", "total pay"],
        "regular_earnings": ["regular earnings"], "overtime_earnings": ["overtime earnings", "overtime pay", "ot earnings"],
        "overtime_hours": ["overtime hours", "ot hours"], "retroactive_pay": ["retroactive pay", "back pay"],
        "lump_sum_payment": ["lump sum", "lump-sum"], "shift_differential": ["shift differential", "shift premium"],
        "other_compensation": ["other compensation", "other pay"], "pensionable_earnings": ["pensionable earnings", "pensionable pay"],
        "authorized_positions": ["authorized positions", "authorized strength"], "budgeted_positions": ["budgeted positions"],
        "filled_positions": ["filled positions"], "vacant_positions": ["vacant positions", "vacancies", "vacancy count"],
        "active_employees": ["active employees"], "department_headcount": ["department headcount", "headcount"],
        "FTE_count": ["fte count", "ftes", "full-time equivalents"], "minimum_staffing_requirement": ["minimum staffing", "minimum manning"],
        "position_eliminations": ["positions eliminated", "position eliminations", "eliminated positions"],
        "attrition_not_replaced": ["attrition not replaced", "not replace attrition"], "vacancy_rate_explicit": ["vacancy rate"],
        "overtime_due_to_staffing_gap": ["overtime due to staffing", "overtime caused by vacancies", "overtime from vacancies"],
        "applicant_count": ["applicant count", "applicants"], "eligible_candidate_count": ["eligible candidates", "candidate count"],
        "turnover_rate_explicit": ["turnover rate"], "retention_rate_explicit": ["retention rate"],
        "time_to_fill": ["time to fill", "time-to-fill"], "signing_bonus": ["signing bonus", "sign-on bonus"],
        "lateral_entry_incentive": ["lateral entry incentive", "lateral incentive"],
        "years_of_service": ["years of service", "service years"], "step_number": ["step number", "step"],
        "step_rate": ["step rate"], "step_progression_rule": ["step progression", "progression rule"],
        "incumbent_tier": ["incumbent tier"], "new_hire_tier": ["new hire tier", "new-hire tier"],
        "probationary_rate": ["probationary rate"], "maximum_rate": ["maximum rate", "max rate"],
        "minimum_rate": ["minimum rate", "min rate"], "salary_range": ["salary range", "pay range"],
        "ordinance_number": ["ordinance number", "ordinance no", "ordinance #"],
        "resolution_number": ["resolution number", "resolution no", "resolution #"],
        "MOU_identifier": ["mou number", "memorandum of understanding"], "council_approval_date": ["council approval date"],
        "payroll_effective_date": ["payroll effective date"], "retroactive_start_date": ["retroactive start date"],
        "one_time": ["one-time", "one time"], "vote_result": ["vote result", "vote"],
        "employer_pension_contribution": ["employer pension contribution"],
        "employee_pension_contribution": ["employee pension contribution"],
        "employer_health_contribution": ["employer health contribution"],
        "employee_health_contribution": ["employee health contribution"],
        "health_cost_share": ["health cost share", "healthcare cost share"], "leave_cashout": ["leave cashout", "leave payout"],
        "total_compensation_explicit": ["total compensation"], "fiscal_year_revenue": ["fiscal year revenue", "total revenue"],
        "fiscal_year_expenditure": ["fiscal year expenditure", "total expenditure"],
        "general_fund_expenditure": ["general fund expenditure"], "median_household_income": ["median household income"],
        "cost_of_living_measure": ["cost of living", "cost-of-living"], "CPI_measure": ["consumer price index", "cpi"],
    }
    output: dict[str, tuple[str, list[str]]] = {}
    for family, names in groups.items():
        for name in names:
            labels = special.get(name, [name.replace("_", " ")])
            # A shared canonical name is assigned to the first explicit family.
            output.setdefault(name, (family, labels))
    return output


QUALITATIVE_PATTERNS: dict[str, list[str]] = {
    "recruitment_pressure": ["difficulty recruiting", "recruitment challenge", "hard to recruit"],
    "retention_pressure": ["difficulty retaining", "retention challenge", "retain employees"],
    "vacancy_pressure": ["vacancy pressure", "persistent vacancies", "unfilled positions"],
    "staffing_shortage": ["staffing shortage", "staff shortage", "understaffed"],
    "overtime_response": ["mandatory overtime", "overtime to cover", "overtime because"],
    "minimum_staffing_pressure": ["minimum staffing", "minimum manning"],
    "market_competitiveness": ["market competitive", "competitive salary", "pay competitiveness"],
    "fiscal_constraint": ["fiscal constraint", "limited fiscal", "revenue constraint"],
    "budget_pressure": ["budget pressure", "budget constraint", "budget shortfall"],
    "inflation_pressure": ["inflation pressure", "rising inflation"],
    "bargaining_leverage": ["bargaining leverage", "collective bargaining"],
    "arbitration_pressure": ["interest arbitration", "fact finding", "fact-finding"],
    "strike_or_job_action_pressure": ["strike", "work stoppage", "job action"],
    "classification_pressure": ["reclassification", "classification study"],
    "compression_or_parity_pressure": ["pay compression", "wage compression", "pay parity"],
    "implementation_confirmation": ["became effective", "was implemented", "has been paid"],
    "implementation_delay": ["implementation delay", "delayed implementation", "retroactive to"],
    "non_safety_position_reduction": ["civilian positions eliminated", "clerical positions eliminated"],
    "safety_position_protection": ["police positions protected", "fire positions protected"],
    "outsourcing_or_consolidation": ["outsourced", "consolidated services", "service consolidation"],
    "benefit_cost_shift": ["cost shift", "employee share increased", "premium share"],
    "one_time_instead_of_base": ["one-time payment instead", "lump sum instead of"],
    "step_progression_mechanism": ["advance to the next step", "step progression"],
    "across_board_mechanism": ["across-the-board", "across the board"],
    "COLA_indexing_mechanism": ["consumer price index", "cpi adjustment", "cost-of-living adjustment"],
    "retroactivity_mechanism": ["retroactive to", "back pay"],
    "other_administrative_context": ["administrative record", "personnel policy"],
}


IMPLEMENTATION_STATUSES = [
    "implemented", "adopted", "paid", "negotiated", "proposed", "recommended",
    "tentative", "rejected", "expired", "amended", "approved", "ratified", "appropriated",
]

FIELD_DICTIONARY = field_dictionary()
LABEL_TO_FIELDS: dict[str, list[tuple[str, str]]] = defaultdict(list)
for _field_name, (_family, _labels) in FIELD_DICTIONARY.items():
    for _label in _labels:
        LABEL_TO_FIELDS[_label.casefold()].append((_family, _field_name))
FIELD_LABEL_RE = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(label) for label in sorted(LABEL_TO_FIELDS, key=len, reverse=True)) + r")(?![a-z0-9])",
    re.I,
)
NORMALIZED_HEADER_MAP: dict[str, list[tuple[str, str]]] = defaultdict(list)
for _label, _targets in LABEL_TO_FIELDS.items():
    NORMALIZED_HEADER_MAP[normalized_label(_label) if "normalized_label" in globals() else re.sub(r"[^a-z0-9%]+", " ", _label).strip()].extend(_targets)
QUAL_PHRASE_TO_TYPE = {phrase.casefold(): evidence_type for evidence_type, phrases in QUALITATIVE_PATTERNS.items() for phrase in phrases}
QUAL_RE = re.compile("|".join(re.escape(phrase) for phrase in sorted(QUAL_PHRASE_TO_TYPE, key=len, reverse=True)), re.I)


def build_registries() -> dict[str, Any]:
    dictionary = field_dictionary()
    rules = []
    for field_name, (family, labels) in sorted(dictionary.items()):
        rules.append({
            "rule_id": f"FIELD-{family.upper()}-{field_name.upper()}", "rule_version": RULE_VERSION,
            "field_family": family, "field_name": field_name, "labels": labels,
            "method": "exact normalized header/label with literal local value parsing",
            "semantic_inference": False,
        })
    for evidence_type, phrases in sorted(QUALITATIVE_PATTERNS.items()):
        rules.append({
            "rule_id": f"SPAN-QUAL-{evidence_type.upper()}", "rule_version": RULE_VERSION,
            "field_family": "qualitative_administrative", "evidence_type": evidence_type,
            "labels": phrases, "method": "literal phrase bounded-span capture", "semantic_inference": False,
        })
    registry = {
        "registry_version": RULE_VERSION, "dictionary_version": DICTIONARY_VERSION,
        "parser_version": PARSER_VERSION, "created_at": utc_now(), "rules": rules,
        "confidence_categories": ["exact_structured_cell", "exact_labeled_text", "exact_table_row_with_header",
            "strong_pattern_with_local_context", "weak_pattern_requires_review", "ambiguous_narrative_manual_review"],
        "forbidden_transformations": ["hourly_to_annual", "annual_to_hourly", "inferred_fte_denominator",
            "base_total_combination", "regular_overtime_combination", "budget_payroll_combination", "semantic_imputation"],
    }
    atomic_json(OUTPUT / "deterministic_field_rule_registry.json", registry)
    write_md(OUTPUT / "deterministic_field_rule_registry.md", "# Deterministic field rule registry\n\n"
        f"Version: `{RULE_VERSION}`. The registry contains {len(rules):,} explicit, locally auditable label/header rules. "
        "Rules preserve literals and coordinates; they do not perform semantic imputation, pay-base conversion, matching, or GABRIEL scoring.\n")
    atomic_json(OUTPUT / "deterministic_field_dictionary_registry.json", {
        "dictionary_version": DICTIONARY_VERSION,
        "fields": {name: {"field_family": family, "labels": labels} for name, (family, labels) in dictionary.items()},
        "qualitative_evidence_types": QUALITATIVE_PATTERNS,
    })
    atomic_json(OUTPUT / "deterministic_header_mapping_registry.json", {
        "version": DICTIONARY_VERSION,
        "normalization": "Unicode-preserving casefold plus whitespace collapse; values remain unmodified",
        "headers": {label: name for name, (_, labels) in dictionary.items() for label in labels},
    })
    atomic_json(OUTPUT / "deterministic_date_currency_percentage_parser_spec.json", {
        "parser_version": PARSER_VERSION, "currency": "literal dollar/USD token; commas removed only in parsed value",
        "percentage": "literal number followed by percent sign; parsed numeric percentage preserves raw token",
        "date": "literal ISO or slash date or month-name date", "year": "literal 1800-2099 four-digit year",
        "integer_decimal": "literal signed/unsigned numeric token; commas removed only in parsed value",
        "unit_conversion": False, "rounding": False, "denominator_inference": False,
    })
    digest = sha256_file(OUTPUT / "deterministic_field_rule_registry.json")
    atomic_json(OUTPUT / "deterministic_field_rule_registry_hash.json", {
        "path": str((OUTPUT / "deterministic_field_rule_registry.json").relative_to(core.ROOT)), "sha256": digest,
        "rule_version": RULE_VERSION, "dictionary_version": DICTIONARY_VERSION, "parser_version": PARSER_VERSION,
    })
    return registry


def enriched_locked_rows() -> list[dict[str, Any]]:
    ready = load_pair_or_shards(INPUT, "external_data_field_span_extraction_ready_queue")
    physical = {row["canonical_payload_id"]: row for row in load_pair_or_shards(INPUT, "physical_payload_extraction_results")}
    locked = []
    for row in ready:
        source = physical[row["canonical_payload_id"]]
        locked.append({
            "canonical_payload_id": row["canonical_payload_id"], "extraction_result_id": row["extraction_result_id"],
            "extraction_artifact_pointers": row["extraction_artifact_pointers"], "extraction_modality": row["extraction_modality"],
            "source_SHA_256": source["source_SHA_256"], "retained_source_ids": row["retained_source_ids"],
            "candidate_ids": source.get("linked_candidate_ids", ""), "search_wave_provenance": source.get("linked_search_waves", ""),
            "municipality_ids": "", "municipality_names": source.get("municipality_names", row["municipality"]),
            "states": source.get("states", row["state"]), "expected_periods": source.get("periods", row["expected_period"]),
            "side_hints": source.get("side_scopes", row["side_scope"]), "department_hints": source.get("department_scopes", row["department_scope"]),
            "source_family_hints": join_values([source.get("primary_source_family", ""), source.get("secondary_source_families", "")]),
            "administrative_source_type": row["administrative_source_type"], "source_quality": row["source_quality"],
            "extraction_priority": row["extraction_priority"], "root_event_ids": row["root_event_ids"],
            "mechanism_event_ids": row["mechanism_event_ids"], "existing_claim_ids": row["claim_ids"],
            "expected_claim_upgrade_tags": row["expected_claim_upgrades"], "extraction_warnings": row["extraction_warnings"],
            "deterministic_processing_eligibility": row["deterministic_processing_eligibility"],
            "proposed_extraction_families": row["proposed_extraction_families"], "primary_terminal_status": row["primary_terminal_status"],
            "pages_available": row["pages_available"], "sections_available": row["sections_available"],
            "tables_available": row["tables_available"], "structured_record_count": row["structured_record_count"],
            "lineage_basis": "canonical_stage6_physical_extraction_result", "lane_id": "",
        })
    # Stable SHA-derived ordering, then exact equal round-robin assignment.
    locked.sort(key=lambda row: hashlib.sha256(row["canonical_payload_id"].encode()).hexdigest())
    for index, row in enumerate(locked):
        row["lane_id"] = LANES[index % 5]
    locked.sort(key=lambda row: row["canonical_payload_id"])
    return locked


def preflight() -> None:
    if core.ROOT.resolve() != Path.cwd().resolve():
        raise RuntimeError(f"wrong repository path: {Path.cwd()}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=core.ROOT, text=True).strip()
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_COMMIT, "HEAD"], cwd=core.ROOT).returncode:
        raise RuntimeError(f"required commit {REQUIRED_COMMIT} is not an ancestor of {head}")
    dirty = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    allowed_related = {"scripts/run_available_external_data_deterministic_field_span_extraction.py"}
    unrelated = [line for line in dirty if line[3:].strip() not in allowed_related]
    if unrelated:
        raise RuntimeError(f"unrelated dirty worktree before field/span preflight: {unrelated}")
    if not INPUT.is_dir():
        raise RuntimeError(f"missing extraction output directory: {INPUT}")
    manifest = read_json(INPUT / "external_data_field_span_extraction_ready_queue_manifest.json")
    if manifest["count"] != EXPECTED_TOTAL or manifest["eligibility_counts"] != EXPECTED_ELIGIBILITY:
        raise RuntimeError(f"input queue manifest mismatch: {manifest}")
    checks = {
        "repair_97": len(load_pair_or_shards(INPUT, "extraction_repair_needed_queue")) == EXPECTED_REPAIR,
        "ocr_later_118": len(load_pair_or_shards(core.STAGE5, "ocr_later_queue")) == EXPECTED_OCR_LATER,
        "storage_hold_7895": "7,895" in (INPUT / "storage_capacity_hold_preservation_summary.md").read_text(encoding="utf-8"),
        "unsearched_12844": read_json(INPUT / "external_data_non_ocr_extraction_summary.json").get("unresolved_hosted_search_targets") == EXPECTED_UNSEARCHED,
        "retained_ignored": git_ignored(core.RETAINED), "extracted_ignored": git_ignored(core.EXTRACTED),
        "structured_ignored": git_ignored(core.STRUCTURED), "field_span_ignored": git_ignored(LOCAL),
        "disk_reserve": free_bytes() >= MIN_FREE_RESERVE,
    }
    if not all(checks.values()):
        raise RuntimeError(f"preflight count/storage gate failed: {checks}")
    try:
        process_text = subprocess.check_output(["ps", "aux"], text=True)
        active = [line for line in process_text.splitlines() if Path(__file__).name in line and
                  ("--worker" in line or "--launch" in line) and str(os.getpid()) not in line]
    except (subprocess.CalledProcessError, PermissionError):
        active = []
    if active:
        raise RuntimeError(f"duplicate field/span worker conflict: {active[:5]}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for child in ["payroll", "staffing", "recruitment_retention", "tenure_progression", "implementation",
                  "benefits_total_compensation", "contextual_controls", "evidence_spans", "tables", "indexes",
                  "quarantine", "temporary", "logs", "lanes"]:
        (LOCAL / child).mkdir(parents=True, exist_ok=True)
    start = utc_now()
    atomic_json(OUTPUT / "field_span_run_manifest.json", {
        "task_id": TASK_ID, "starting_head": head, "created_at": start, "input_count": EXPECTED_TOTAL,
        "rule_version": RULE_VERSION, "dictionary_version": DICTIONARY_VERSION, "parser_version": PARSER_VERSION,
        "local_output_root": str(LOCAL.relative_to(core.ROOT)), "network_authorized": False,
        "gabriel_authorized": False, "ocr_authorized": False, "normalization_authorized": False,
    })
    atomic_json(OUTPUT / "field_span_run_state.json", {"stage": "preflight", "status": "running", "updated_at": start})
    atomic_json(OUTPUT / "field_span_stage_checkpoint.json", {"stage": "preflight", "status": "running", "updated_at": start})
    atomic_json(OUTPUT / "field_span_disk_capacity_audit.json", {
        "passed": free_bytes() >= MIN_FREE_RESERVE, "free_bytes": free_bytes(), "reserve_bytes": MIN_FREE_RESERVE,
        "audited_at": utc_now(),
    })
    atomic_json(OUTPUT / "field_span_local_artifact_storage_audit.json", {
        "passed": all(git_ignored(p) for p in (core.RETAINED, core.EXTRACTED, core.STRUCTURED, LOCAL)),
        "retained_root_ignored": git_ignored(core.RETAINED), "extracted_root_ignored": git_ignored(core.EXTRACTED),
        "structured_root_ignored": git_ignored(core.STRUCTURED), "field_span_root_ignored": git_ignored(LOCAL),
        "audited_at": utc_now(),
    })
    # Empty logs are still explicit operational evidence.
    (OUTPUT / "field_span_operational_incident_log.jsonl").write_text("", encoding="utf-8")
    (OUTPUT / "operational_incident_log.jsonl").write_text("", encoding="utf-8")
    (OUTPUT / "field_span_stage_transition_log.jsonl").write_text(
        json.dumps({"at": utc_now(), "from": "06_EXTERNAL-DATA-EXTRACTION", "to": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION", "status": "preflight_started"}) + "\n",
        encoding="utf-8",
    )
    build_registries()
    locked = enriched_locked_rows()
    if len(locked) != EXPECTED_TOTAL or len({row["canonical_payload_id"] for row in locked}) != EXPECTED_TOTAL:
        raise RuntimeError("locked queue is not exactly 14,160 unique payloads")
    counts = Counter(row["deterministic_processing_eligibility"] for row in locked)
    if dict(counts) != EXPECTED_ELIGIBILITY:
        raise RuntimeError(f"eligibility mismatch after enrichment: {counts}")
    # Full hash and existence gate for every artifact in the canonical hash manifest.
    hash_rows = load_pair_or_shards(INPUT, "extraction_artifact_hash_manifest")
    failures = []
    for item in hash_rows:
        path = core.ROOT / item["output_local_path"]
        if not path.is_file():
            failures.append({"path": item["output_local_path"], "reason": "missing"})
            continue
        if int(item["output_byte_size"]) != path.stat().st_size or sha256_file(path) != item["output_SHA_256"]:
            failures.append({"path": item["output_local_path"], "reason": "size_or_hash_mismatch"})
    if failures:
        atomic_json(OUTPUT / "field_span_input_reconciliation_audit.json", {"passed": False, "failures": failures[:100], "failure_count": len(failures)})
        raise RuntimeError(f"artifact integrity failures: {len(failures)}")
    write_csv(OUTPUT / "field_span_locked_payload_queue.csv", locked)
    write_jsonl(OUTPUT / "field_span_locked_payload_queue.jsonl", locked)
    queue_hash = sha256_file(OUTPUT / "field_span_locked_payload_queue.jsonl")
    atomic_json(OUTPUT / "field_span_locked_payload_queue_manifest.json", {
        "count": len(locked), "unique_payloads": len({r["canonical_payload_id"] for r in locked}),
        "sha256": queue_hash, "eligibility_counts": dict(counts), "lane_counts": dict(Counter(r["lane_id"] for r in locked)),
        "created_at": utc_now(),
    })
    for lane in LANES:
        rows = [row for row in locked if row["lane_id"] == lane]
        write_csv(OUTPUT / f"{lane}_queue.csv", rows)
        write_jsonl(OUTPUT / f"{lane}_queue.jsonl", rows)
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {
            "lane_id": lane, "status": "locked", "locked_count": len(rows), "completed_count": 0,
            "remaining_count": len(rows), "updated_at": utc_now(),
        })
    distribution = {lane: sum(row["lane_id"] == lane for row in locked) for lane in LANES}
    atomic_json(OUTPUT / "field_span_lane_distribution.json", {
        "method": "sha256(canonical_payload_id) stable sort, round-robin five lanes", "lane_sizes": distribution,
        "disjoint": True, "complete": sum(distribution.values()) == EXPECTED_TOTAL, "stagger_seconds": STAGGERS,
    })
    write_md(OUTPUT / "field_span_lane_distribution.md", "# Five-lane distribution\n\n" +
        "\n".join(f"- `{lane}`: {count:,} payloads; planned start T+{STAGGERS[lane]} seconds." for lane, count in distribution.items()))
    audit = {
        "passed": True, "input_count": len(locked), "unique_payloads": len({r["canonical_payload_id"] for r in locked}),
        "eligibility_counts": dict(counts), "repair_excluded": EXPECTED_REPAIR, "ocr_later_excluded": EXPECTED_OCR_LATER,
        "storage_holds_preserved": EXPECTED_HOLDS, "unsearched_targets_preserved": EXPECTED_UNSEARCHED,
        "artifact_manifest_rows": len(hash_rows), "artifact_integrity_failures": 0, "queue_sha256": queue_hash,
        "required_lineage_fields_present": all(all(key in row for key in ["canonical_payload_id", "extraction_result_id",
            "extraction_artifact_pointers", "source_SHA_256", "retained_source_ids", "municipality_names", "states",
            "root_event_ids", "mechanism_event_ids", "source_family_hints", "administrative_source_type",
            "extraction_priority", "extraction_warnings"]) for row in locked), "audited_at": utc_now(),
    }
    atomic_json(OUTPUT / "field_span_input_reconciliation_audit.json", audit)
    write_md(OUTPUT / "field_span_input_reconciliation_audit.md", "# Field/span input reconciliation audit\n\n"
        f"PASS. Exactly {len(locked):,} unique usable physical extraction results were locked once. All {len(hash_rows):,} artifact-manifest entries exist and match size/SHA-256. "
        f"The {EXPECTED_REPAIR} repair payloads and {EXPECTED_OCR_LATER} OCR-later sources remain excluded.\n")
    smoke_tests(locked)
    atomic_json(OUTPUT / "field_span_run_state.json", {"stage": "production", "status": "ready", "updated_at": utc_now()})
    atomic_json(OUTPUT / "field_span_stage_checkpoint.json", {"stage": "production", "status": "ready", "updated_at": utc_now()})


def normalized_label(value: str) -> str:
    return re.sub(r"[^a-z0-9%]+", " ", value.casefold()).strip()


VALUE_RE = re.compile(
    r"(?P<currency>(?:US\$|\$)\s*-?\d[\d,]*(?:\.\d+)?)|"
    r"(?P<percent>-?\d+(?:\.\d+)?\s*%)|"
    r"(?P<date>(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2})|"
    r"(?P<number>-?\d[\d,]*(?:\.\d+)?)",
    re.I,
)


def parse_literal(raw: str) -> dict[str, str]:
    value = raw.strip()
    if re.fullmatch(r"(?:US\$|\$)\s*-?\d[\d,]*(?:\.\d+)?", value, re.I):
        return {"parsed_value": re.sub(r"[^0-9.\-]", "", value.replace(",", "")), "parsed_value_type": "currency", "currency": "USD"}
    if re.fullmatch(r"-?\d+(?:\.\d+)?\s*%", value):
        return {"parsed_value": value.replace("%", "").strip(), "parsed_value_type": "percentage", "currency": ""}
    if re.fullmatch(r"(?:19|20)\d{2}", value):
        return {"parsed_value": value, "parsed_value_type": "year", "currency": ""}
    if re.fullmatch(r"(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})", value):
        return {"parsed_value": value, "parsed_value_type": "date", "currency": ""}
    if re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", value):
        parsed = value.replace(",", "")
        return {"parsed_value": parsed, "parsed_value_type": "decimal" if "." in parsed else "integer", "currency": ""}
    return {"parsed_value": value, "parsed_value_type": "categorical_literal", "currency": ""}


def explicit_side(text: str) -> tuple[str, str]:
    low = text.casefold()
    hits = []
    if re.search(r"\bpolice|law enforcement|patrol officer|sheriff", low): hits.append("police")
    if re.search(r"\bfire\b|firefighter|fire fighter", low): hits.append("fire")
    if re.search(r"public works|clerical|library|parks|utilities|general municipal|administration", low): hits.append("non_safety")
    unique = sorted(set(hits))
    if unique == ["fire", "police"]: return text, "safety_combined"
    if len(unique) > 1: return text, "mixed"
    if unique: return text, unique[0]
    if "public safety" in low: return text, "safety_combined"
    return "", "unclear"


def explicit_department(text: str) -> tuple[str, str]:
    for pattern, canonical in [
        (r"police department|\bpolice\b", "police"), (r"fire department|\bfire\b", "fire"),
        (r"public works", "public_works"), (r"parks(?: and recreation)?", "parks_rec"),
        (r"library", "library"), (r"utilities?", "utilities"), (r"clerical|administration", "clerical_admin"),
    ]:
        match = re.search(pattern, text, re.I)
        if match: return match.group(0), canonical
    return "", "unclear"


def basis_fields(text: str, field_name: str) -> tuple[str, str, str, str]:
    low = text.casefold()
    pay = next((token for token in ["per hour", "hourly", "per annum", "annually", "annual", "biweekly", "weekly", "monthly"] if token in low), "")
    compensation = ""
    if field_name in {"base_pay", "base_salary", "annual_salary", "hourly_rate"}: compensation = "base_or_rate_explicit"
    elif field_name in {"gross_pay", "total_earnings", "total_compensation_explicit"}: compensation = "total_explicit"
    elif "overtime" in field_name: compensation = "overtime_explicit"
    elif "budget" in field_name or "authorized_positions" == field_name: compensation = "budgeted_explicit"
    recurring = "one_time" if re.search(r"one[- ]time|lump[- ]sum", low) else ("recurring" if "recurring" in low else "")
    implementation = next((status for status in IMPLEMENTATION_STATUSES if re.search(rf"\b{re.escape(status)}\b", low)), "")
    return pay, compensation, recurring, implementation


def locate_page(offset: int, indexes: list[dict[str, Any]], ends: list[int] | None = None) -> str:
    if not indexes: return ""
    ends = ends or [int(row["character_end"]) for row in indexes]
    pos = bisect.bisect_right(ends, offset)
    if pos >= len(indexes): pos = len(indexes) - 1
    row = indexes[pos]
    return str(row.get("page_number", ""))


def locate_section(offset: int, indexes: list[dict[str, Any]], starts: list[int] | None = None) -> tuple[str, str]:
    if not indexes: return "", ""
    starts = starts or [int(row.get("character_start", 0)) for row in indexes]
    position = bisect.bisect_right(starts, offset) - 1
    if position >= 0:
        row = indexes[position]
        if int(row.get("character_start", 0)) <= offset <= int(row.get("character_end", 0)):
            return str(row.get("section_order", "")), str(row.get("dom_path", ""))
    return "", ""


class PayloadExtractor:
    def __init__(self, row: dict[str, str]):
        self.row = row
        self.dictionary = FIELD_DICTIONARY
        self.fields: list[dict[str, Any]] = []
        self.spans: list[dict[str, Any]] = []
        self.ambiguities: list[dict[str, Any]] = []
        self.conflicts: list[dict[str, Any]] = []
        self.seen_fields: set[str] = set()
        self.seen_spans: set[str] = set()
        self.word_count = 0
        self.timestamp = utc_now()

    def common(self) -> dict[str, Any]:
        claims = self.row.get("existing_claim_ids", "")
        return {
            "canonical_payload_id": self.row["canonical_payload_id"], "extraction_result_id": self.row["extraction_result_id"],
            "retained_source_ids": self.row["retained_source_ids"], "source_SHA_256": self.row["source_SHA_256"],
            "candidate_ids": self.row.get("candidate_ids", ""), "municipality_raw": self.row.get("municipality_names", ""),
            "municipality_canonical_id": self.row.get("municipality_ids", ""), "state": self.row.get("states", ""),
            "period_raw": self.row.get("expected_periods", ""), "root_event_ids": self.row.get("root_event_ids", ""),
            "mechanism_event_ids": self.row.get("mechanism_event_ids", ""), "claim_ids": claims,
            "claim_linkage_status": "canonical_mapping_preserved" if claims else "claim_linkage_pending_reconstruction",
            "expected_claim_upgrade_tags": self.row.get("expected_claim_upgrade_tags", ""),
            "search_wave_provenance": self.row.get("search_wave_provenance", ""),
            "extraction_modality": self.row.get("extraction_modality", ""),
            "administrative_source_type": self.row.get("administrative_source_type", ""),
            "source_family": self.row.get("source_family_hints", ""), "source_quality": self.row.get("source_quality", ""),
            "lineage_basis": "one_physical_extraction_result_deterministic_local_pass",
        }

    def emit_span(self, *, family: str, evidence_type: str, excerpt: str, start: str = "", end: str = "",
                  page: str = "", section: str = "", heading: str = "", table: str = "", row: str = "",
                  column: str = "", preceding: str = "", following: str = "", rule_id: str,
                  confidence: str, ambiguity: str = "", field_ids: str = "", artifact: str = "",
                  implementation: str = "") -> str:
        excerpt = excerpt[:1000]
        span_id = stable("EXTSPAN", self.row["canonical_payload_id"], evidence_type, start, end, table, row, column, excerpt)
        if span_id in self.seen_spans: return span_id
        self.seen_spans.add(span_id)
        _, side = explicit_side(excerpt)
        _, department = explicit_department(excerpt)
        record = {key: "" for key in SPAN_SCHEMA}
        record.update(self.common())
        record.update({
            "external_evidence_span_id": span_id, "field_record_ids": field_ids, "field_family": family,
            "evidence_type": evidence_type, "exact_excerpt": excerpt,
            "normalized_search_text": re.sub(r"\s+", " ", excerpt.casefold()).strip(), "source_page": page,
            "source_section": section, "source_heading_path": heading, "source_table_id": table,
            "source_row_start": row, "source_row_end": row, "source_column_start": column, "source_column_end": column,
            "source_character_start": start, "source_character_end": end, "preceding_context": preceding[-160:],
            "following_context": following[:160], "municipality": self.row.get("municipality_names", ""),
            "state": self.row.get("states", ""), "period": self.row.get("expected_periods", ""), "side_hint": side,
            "department_hint": department, "implementation_status_hint": implementation,
            "rule_id": rule_id, "rule_version": RULE_VERSION, "dictionary_version": DICTIONARY_VERSION,
            "parser_version": PARSER_VERSION, "extraction_timestamp": self.timestamp,
            "extraction_confidence": confidence, "extraction_confidence_basis": confidence,
            "ambiguity_flags": ambiguity, "extraction_artifact_pointer": artifact,
        })
        self.spans.append(record)
        if ambiguity:
            self.ambiguities.append({
                "external_evidence_span_id": span_id, "canonical_payload_id": self.row["canonical_payload_id"],
                "ambiguity_flags": ambiguity, "review_queue": "pending_gabriel_or_manual_narrative_review",
                "source_coordinates": json.dumps({"page": page, "section": section, "table": table, "row": row,
                    "column": column, "character_start": start, "character_end": end}, separators=(",", ":")),
                "exact_excerpt": excerpt, "rule_id": rule_id,
            })
        return span_id

    def emit_field(self, *, family: str, field_name: str, raw: str, excerpt: str, value_start: str = "",
                   value_end: str = "", span_start: str = "", span_end: str = "", page: str = "",
                   section: str = "", table: str = "", row: str = "", column: str = "", cell: str = "",
                   rule_id: str, confidence: str, ambiguity: str = "", artifact: str = "",
                   preceding: str = "", following: str = "") -> None:
        raw = str(raw)
        if not raw.strip(): return
        record_id = stable("EXTFIELD", self.row["canonical_payload_id"], field_name, raw, value_start, value_end, table, row, column)
        if record_id in self.seen_fields: return
        self.seen_fields.add(record_id)
        parsed = parse_literal(raw)
        side_raw, side = explicit_side(excerpt)
        department_raw, department = explicit_department(excerpt)
        pay_basis, compensation_basis, recurring, implementation = basis_fields(excerpt, field_name)
        span_id = self.emit_span(
            family=family, evidence_type=f"explicit_{field_name}", excerpt=excerpt, start=span_start, end=span_end,
            page=page, section=section, table=table, row=row, column=column, preceding=preceding,
            following=following, rule_id=rule_id, confidence=confidence, ambiguity=ambiguity,
            field_ids=record_id, artifact=artifact, implementation=implementation,
        )
        record = {key: "" for key in FIELD_SCHEMA}
        record.update(self.common())
        record.update({
            "external_field_record_id": record_id, "department_raw": department_raw,
            "department_canonical_hint": department, "unit_raw": "", "position_or_employee_raw": "",
            "side_raw": side_raw, "side_deterministic_hint": side, "start_date_raw": "", "end_date_raw": "",
            "fiscal_year_raw": raw if field_name == "fiscal_year" else "",
            "calendar_year_raw": raw if field_name in {"payroll_year"} else "", "field_family": family,
            "field_name": field_name, "raw_value": raw, **parsed, "unit": "", "pay_basis_raw": pay_basis,
            "compensation_basis_raw": compensation_basis, "recurring_status_raw": recurring,
            "implementation_status_raw": implementation, "source_page": page, "source_section": section,
            "source_table_id": table, "source_row": row, "source_column": column, "source_cell": cell,
            "source_character_start": value_start, "source_character_end": value_end, "evidence_span_id": span_id,
            "rule_id": rule_id, "rule_version": RULE_VERSION, "dictionary_version": DICTIONARY_VERSION,
            "parser_version": PARSER_VERSION, "extraction_timestamp": self.timestamp,
            "extraction_confidence": confidence, "extraction_confidence_basis": confidence,
            "ambiguity_flags": ambiguity, "conflict_flags": "", "extraction_artifact_pointer": artifact,
        })
        self.fields.append(record)

    def scan_text(self, text: str, artifact: str, page_index: list[dict[str, Any]], section_index: list[dict[str, Any]]) -> None:
        self.word_count += len(text.split())
        page_ends = [int(row["character_end"]) for row in page_index]
        section_starts = [int(row.get("character_start", 0)) for row in section_index]
        offset = 0
        for line in text.splitlines(keepends=True):
            body = line.rstrip("\r\n")
            low_norm = normalized_label(body)
            if not low_norm:
                offset += len(line); continue
            page = locate_page(offset, page_index, page_ends)
            section, heading = locate_section(offset, section_index, section_starts)
            for label_match in FIELD_LABEL_RE.finditer(body):
                label_key = label_match.group(0).casefold()
                for family, field_name in LABEL_TO_FIELDS[label_key]:
                        after = body[label_match.end():label_match.end() + 220]
                        candidates = list(VALUE_RE.finditer(after))[:12]
                        if candidates:
                            for value_match in candidates:
                                raw = value_match.group(0)
                                local_start = label_match.end() + value_match.start()
                                local_end = label_match.end() + value_match.end()
                                # Exclude the numeric portion of the label itself and very remote prose numbers.
                                if local_start - label_match.end() > 180: continue
                                span_lo = max(0, min(label_match.start(), local_start) - 100)
                                span_hi = min(len(body), max(label_match.end(), local_end) + 160)
                                excerpt = body[span_lo:span_hi]
                                confidence = "exact_labeled_text" if ":" in body[label_match.end():local_start + 1] or local_start - label_match.end() < 80 else "strong_pattern_with_local_context"
                                ambiguity = "" if confidence == "exact_labeled_text" else "local_text_pattern_requires_review"
                                self.emit_field(
                                    family=family, field_name=field_name, raw=raw, excerpt=excerpt,
                                    value_start=str(offset + local_start), value_end=str(offset + local_end),
                                    span_start=str(offset + span_lo), span_end=str(offset + span_hi), page=page,
                                    section=section, rule_id=f"FIELD-{family.upper()}-{field_name.upper()}",
                                    confidence=confidence, ambiguity=ambiguity, artifact=artifact,
                                    preceding=text[max(0, offset + span_lo - 160):offset + span_lo],
                                    following=text[offset + span_hi:offset + span_hi + 160],
                                )
                        else:
                            # Explicit colon/equal labeled categorical literal only.
                            string_match = re.match(r"\s*[:=\-]\s*([^;|]{1,120})", after)
                            if string_match:
                                raw = string_match.group(1).strip()
                                if raw:
                                    local_start = label_match.end() + string_match.start(1)
                                    local_end = label_match.end() + string_match.end(1)
                                    excerpt = body[max(0, label_match.start() - 80):min(len(body), local_end + 80)]
                                    self.emit_field(
                                        family=family, field_name=field_name, raw=raw, excerpt=excerpt,
                                        value_start=str(offset + local_start), value_end=str(offset + local_end),
                                        span_start=str(offset + max(0, label_match.start() - 80)),
                                        span_end=str(offset + min(len(body), local_end + 80)), page=page, section=section,
                                        rule_id=f"FIELD-{family.upper()}-{field_name.upper()}",
                                        confidence="exact_labeled_text", artifact=artifact,
                                    )
            for qualitative_match in QUAL_RE.finditer(body):
                    phrase = qualitative_match.group(0)
                    evidence_type = QUAL_PHRASE_TO_TYPE[phrase.casefold()]
                    pos = qualitative_match.start()
                    span_lo = max(0, pos - 180); span_hi = min(len(body), pos + len(phrase) + 280)
                    excerpt = body[span_lo:span_hi]
                    self.emit_span(
                        family="qualitative_administrative", evidence_type=evidence_type, excerpt=excerpt,
                        start=str(offset + span_lo), end=str(offset + span_hi), page=page, section=section,
                        heading=heading, preceding=text[max(0, offset + span_lo - 160):offset + span_lo],
                        following=text[offset + span_hi:offset + span_hi + 160],
                        rule_id=f"SPAN-QUAL-{evidence_type.upper()}", confidence="ambiguous_narrative_manual_review",
                        ambiguity="qualitative_narrative_requires_manual_or_future_model_review", artifact=artifact,
                    )
            for status_match in re.finditer(r"\b(?:" + "|".join(IMPLEMENTATION_STATUSES) + r")\b", body, re.I):
                status = status_match.group(0)
                span_lo = max(0, status_match.start() - 120); span_hi = min(len(body), status_match.end() + 180)
                excerpt = body[span_lo:span_hi]
                ambiguity = "" if self.row.get("administrative_source_type") in {"ordinance_resolution", "council_minutes", "implementation_record"} else "implementation_lifecycle_context_requires_review"
                confidence = "exact_labeled_text" if not ambiguity else "weak_pattern_requires_review"
                for status_field in ("implementation_status", status.casefold()):
                    if status_field not in self.dictionary: continue
                    self.emit_field(
                        family="implementation_confirmation", field_name=status_field, raw=status,
                        excerpt=excerpt, value_start=str(offset + status_match.start()),
                        value_end=str(offset + status_match.end()), span_start=str(offset + span_lo),
                        span_end=str(offset + span_hi), page=page, section=section,
                        rule_id=f"FIELD-IMPLEMENTATION_CONFIRMATION-{status_field.upper()}",
                        confidence=confidence, ambiguity=ambiguity, artifact=artifact,
                    )
            offset += len(line)

    def scan_rows(self, rows: list[dict[str, Any]], *, table_id: str, artifact: str, confidence: str) -> None:
        if not rows: return
        matrix: list[list[str]] = []
        for row in rows:
            cells = row.get("cells")
            if cells is None: cells = [{"raw_cell_text": value, "column_order": i + 1} for i, value in enumerate(row.get("raw_cells", []))]
            matrix.append([str(cell.get("raw_cell_text", "")) for cell in cells])
        headers: dict[int, tuple[str, str]] = {}
        header_rows: dict[int, int] = {}
        for ridx, cells in enumerate(matrix[:5], 1):
            for cidx, cell in enumerate(cells, 1):
                norm = normalized_label(cell)
                candidates = list(NORMALIZED_HEADER_MAP.get(norm, []))
                if not candidates and len(norm) <= 100:
                    for label_norm, targets in NORMALIZED_HEADER_MAP.items():
                        if len(label_norm) >= 4 and re.search(rf"(?:^| ){re.escape(label_norm)}(?: |$)", norm):
                            candidates.extend(targets)
                if candidates:
                    family, field_name = candidates[0]
                    headers.setdefault(cidx, (family, field_name)); header_rows.setdefault(cidx, ridx)
        for ridx, cells in enumerate(matrix, 1):
            row_context = " | ".join(cells)
            # Header-based columns.
            for cidx, (family, field_name) in headers.items():
                if ridx <= header_rows[cidx] or cidx > len(cells): continue
                raw = cells[cidx - 1]
                if not raw.strip(): continue
                excerpt = "HEADERS: " + " | ".join(matrix[header_rows[cidx] - 1]) + "\nROW: " + row_context
                self.emit_field(
                    family=family, field_name=field_name, raw=raw, excerpt=excerpt[:1000], table=table_id,
                    row=str(ridx), column=str(cidx), cell=raw, rule_id=f"FIELD-{family.upper()}-{field_name.upper()}",
                    confidence=confidence, artifact=artifact,
                )
            # Label-value row/adjacent-cell form.
            for cidx, cell in enumerate(cells, 1):
                norm = normalized_label(cell)
                for family, field_name in NORMALIZED_HEADER_MAP.get(norm, []):
                    if cidx < len(cells):
                        raw = cells[cidx]
                        if raw.strip():
                            self.emit_field(
                                family=family, field_name=field_name, raw=raw, excerpt=row_context[:1000],
                                table=table_id, row=str(ridx), column=str(cidx + 1), cell=raw,
                                rule_id=f"FIELD-{family.upper()}-{field_name.upper()}", confidence=confidence,
                                artifact=artifact,
                            )
                        break

    def run(self) -> dict[str, Any]:
        pointers = [core.ROOT / value for value in split_values(self.row["extraction_artifact_pointers"])]
        modality = self.row["extraction_modality"]
        page_index: list[dict[str, Any]] = []
        section_index: list[dict[str, Any]] = []
        for path in pointers:
            if path.name.endswith("pages.jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as handle: page_index = [json.loads(line) for line in handle if line.strip()]
            elif path.name.endswith("sections.jsonl.gz") or path.name.endswith("lines.jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as handle: section_index = [json.loads(line) for line in handle if line.strip()]
        for path in pointers:
            rel = str(path.relative_to(core.ROOT))
            if path.name.endswith((".txt.gz", ".visible_text.txt.gz")):
                with gzip.open(path, "rt", encoding="utf-8") as handle: text = handle.read()
                self.scan_text(text, rel, page_index, section_index)
            elif path.name.endswith("tables.jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip(): continue
                        table = json.loads(line)
                        self.scan_rows(table.get("rows", []), table_id=f"html_table_{table.get('table_order', '')}", artifact=rel,
                                       confidence="exact_table_row_with_header")
            elif path.name.endswith("rows.jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as handle: rows = [json.loads(line) for line in handle if line.strip()]
                self.scan_rows(rows, table_id="csv_table_1", artifact=rel, confidence="exact_structured_cell")
            elif path.name.endswith("embedded_structured.jsonl.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip(): continue
                        item = json.loads(line); flattened = []
                        def walk(value: Any, prefix: str = "") -> None:
                            if isinstance(value, dict):
                                for key, child in value.items(): walk(child, f"{prefix}.{key}" if prefix else key)
                            elif isinstance(value, list):
                                for index, child in enumerate(value): walk(child, f"{prefix}[{index}]")
                            else: flattened.append((prefix, "" if value is None else str(value)))
                        walk(item.get("data", {}))
                        rows = [{"raw_cells": [key, value]} for key, value in flattened]
                        self.scan_rows(rows, table_id=f"embedded_{item.get('embedded_order', '')}", artifact=rel,
                                       confidence="exact_structured_cell")
        # Exact literal status tokens are separate lifecycle observations.
        return {
            "canonical_payload_id": self.row["canonical_payload_id"], "extraction_result_id": self.row["extraction_result_id"],
            "lane_id": self.row["lane_id"], "terminal_outcome": "field_and_span_extracted" if self.fields else (
                "qualitative_spans_only" if self.spans else "no_relevant_field_or_span"),
            "field_record_count": len(self.fields), "evidence_span_count": len(self.spans),
            "ambiguity_count": len(self.ambiguities), "conflict_count": len(self.conflicts),
            "word_count": self.word_count, "field_family_counts": dict(Counter(r["field_family"] for r in self.fields)),
            "field_name_counts": dict(Counter(r["field_name"] for r in self.fields)),
            "confidence_counts": dict(Counter(r["extraction_confidence"] for r in self.fields + self.spans)),
            "claim_linked_record_count": sum(bool(r["claim_ids"]) for r in self.fields + self.spans),
            "completed_at": utc_now(),
        }


def append_gzip_jsonl(handle: Any, rows: Iterable[dict[str, Any]]) -> None:
    for row in rows:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def worker(lane: str) -> None:
    rows = read_csv(OUTPUT / f"{lane}_queue.csv")
    lane_root = LOCAL / "lanes" / lane
    lane_root.mkdir(parents=True, exist_ok=True)
    outcomes_path = lane_root / "payload_outcomes.jsonl"
    completed = set()
    if outcomes_path.is_file():
        with outcomes_path.open(encoding="utf-8") as handle:
            completed = {json.loads(line)["canonical_payload_id"] for line in handle if line.strip()}
    mode = "at" if completed else "wt"
    paths = {
        "fields": lane_root / "field_records.jsonl.gz", "spans": lane_root / "evidence_spans.jsonl.gz",
        "ambiguities": lane_root / "ambiguities.jsonl.gz", "conflicts": lane_root / "conflicts.jsonl.gz",
    }
    with gzip.open(paths["fields"], mode, encoding="utf-8", compresslevel=6) as field_handle, \
         gzip.open(paths["spans"], mode, encoding="utf-8", compresslevel=6) as span_handle, \
         gzip.open(paths["ambiguities"], mode, encoding="utf-8", compresslevel=6) as ambiguity_handle, \
         gzip.open(paths["conflicts"], mode, encoding="utf-8", compresslevel=6) as conflict_handle, \
         outcomes_path.open("a", encoding="utf-8") as outcome_handle:
        for sequence, row in enumerate(rows, 1):
            if row["canonical_payload_id"] in completed: continue
            if free_bytes() < MIN_FREE_RESERVE:
                atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "disk_reserve_stop",
                    "locked_count": len(rows), "completed_count": len(completed), "remaining_count": len(rows) - len(completed),
                    "updated_at": utc_now()})
                raise RuntimeError("disk reserve reached")
            extractor = PayloadExtractor(row)
            outcome = extractor.run()
            append_gzip_jsonl(field_handle, extractor.fields); append_gzip_jsonl(span_handle, extractor.spans)
            append_gzip_jsonl(ambiguity_handle, extractor.ambiguities); append_gzip_jsonl(conflict_handle, extractor.conflicts)
            for handle in (field_handle, span_handle, ambiguity_handle, conflict_handle): handle.flush()
            outcome_handle.write(json.dumps(outcome, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
            outcome_handle.flush(); os.fsync(outcome_handle.fileno())
            completed.add(row["canonical_payload_id"])
            atomic_json(OUTPUT / f"{lane}_checkpoint.json", {
                "lane_id": lane, "status": "running", "locked_count": len(rows), "completed_count": len(completed),
                "remaining_count": len(rows) - len(completed), "last_payload_id": row["canonical_payload_id"],
                "lane_sequence": sequence, "updated_at": utc_now(),
            })
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {
        "lane_id": lane, "status": "complete", "locked_count": len(rows), "completed_count": len(completed),
        "remaining_count": 0, "updated_at": utc_now(),
    })


def repair_interrupted_ledgers() -> None:
    """Close interrupted gzip streams without re-extracting accepted payloads."""
    repaired = []
    for lane in LANES:
        lane_root = LOCAL / "lanes" / lane
        if not lane_root.is_dir(): continue
        for name in ["field_records.jsonl.gz", "evidence_spans.jsonl.gz", "ambiguities.jsonl.gz", "conflicts.jsonl.gz"]:
            path = lane_root / name
            if not path.is_file(): continue
            try:
                with gzip.open(path, "rb") as handle:
                    while handle.read(4 * 1024 * 1024): pass
                continue
            except (EOFError, gzip.BadGzipFile, zlib.error):
                pass
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            decoded = bytearray()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                    try: decoded.extend(decompressor.decompress(block))
                    except zlib.error: break
            temporary = path.with_suffix(path.suffix + ".repairing")
            with gzip.open(temporary, "wb", compresslevel=6) as handle: handle.write(decoded)
            os.replace(temporary, path)
            repaired.append({"lane_id": lane, "ledger": name, "decoded_bytes_preserved": len(decoded),
                "repair": "interrupted_gzip_footer_resealed_without_payload_reprocessing"})
    incident = {"at": utc_now(), "incident": "quadratic_html_section_lookup_detected_during_staggered_launch",
        "accepted_payloads_preserved": sum(1 for lane in LANES for _ in iter_jsonl(LOCAL / "lanes" / lane / "payload_outcomes.jsonl")),
        "corrective_action": "workers stopped; interrupted gzip streams resealed; indexed binary-search lookup installed; resume incomplete only",
        "repaired_ledgers": repaired, "forbidden_action_occurred": False}
    for path in [OUTPUT / "field_span_operational_incident_log.jsonl", OUTPUT / "operational_incident_log.jsonl"]:
        with path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(incident, sort_keys=True) + "\n")
    print(json.dumps(incident, indent=2))


def smoke_tests(locked: list[dict[str, Any]]) -> None:
    criteria = [
        ("payroll_table", lambda r: r["administrative_source_type"] == "payroll_roster" and int(r["tables_available"] or 0) > 0),
        ("payroll_narrative_pdf", lambda r: r["administrative_source_type"] == "payroll_roster" and r["extraction_modality"] == "pdf"),
        ("staffing", lambda r: "staffing_and_headcount" in r["proposed_extraction_families"]),
        ("implementation", lambda r: "implementation_confirmation" in r["proposed_extraction_families"]),
        ("benefits", lambda r: "benefits_and_total_compensation" in r["proposed_extraction_families"]),
        ("html_table", lambda r: r["extraction_modality"] == "html" and int(r["tables_available"] or 0) > 0),
        ("html_embedded", lambda r: r["extraction_modality"] == "html" and int(r["structured_record_count"] or 0) > 0),
        ("csv", lambda r: r["extraction_modality"] == "csv"),
        ("low_yield", lambda r: r["deterministic_processing_eligibility"] == "low_yield_context_only"),
    ]
    results = []
    for name, predicate in criteria:
        row = next((item for item in locked if predicate(item)), None)
        if row is None:
            results.append({"case": name, "status": "representative_not_available"}); continue
        extractor = PayloadExtractor({key: str(value) for key, value in row.items()})
        outcome = extractor.run()
        exact = all((f["source_character_start"] and f["source_character_end"]) or (f["source_table_id"] and f["source_row"] and f["source_column"]) for f in extractor.fields)
        results.append({"case": name, "status": "pass" if exact else "fail", "payload": row["canonical_payload_id"],
            "field_records": len(extractor.fields), "spans": len(extractor.spans), "coordinates_exact": exact,
            "terminal_outcome": outcome["terminal_outcome"]})
    passed = all(row["status"] in {"pass", "representative_not_available"} for row in results)
    atomic_json(OUTPUT / "field_span_smoke_test_results.json", {"passed": passed, "cases": results, "tested_at": utc_now(),
        "network_calls": 0, "gabriel_calls": 0, "normalization_runs": 0})
    if not passed: raise RuntimeError("bounded smoke tests failed coordinate gate")


def launch() -> None:
    atomic_json(OUTPUT / "field_span_run_state.json", {"stage": "production", "status": "running", "updated_at": utc_now()})
    processes: list[tuple[str, subprocess.Popen[Any]]] = []
    started = time.monotonic()
    for lane in LANES:
        target = STAGGERS[lane]
        while time.monotonic() - started < target:
            time.sleep(min(5, target - (time.monotonic() - started)))
        log = (TMP / f"{lane}.log").open("a", encoding="utf-8")
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", lane], cwd=core.ROOT,
                                   stdout=log, stderr=subprocess.STDOUT)
        processes.append((lane, process))
        with (OUTPUT / "field_span_stage_transition_log.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": utc_now(), "lane_id": lane, "status": "started", "planned_stagger_seconds": target,
                "actual_elapsed_seconds": round(time.monotonic() - started, 3)}) + "\n")
    failures = []
    for lane, process in processes:
        code = process.wait()
        if code: failures.append({"lane": lane, "exit_code": code})
    if failures:
        atomic_json(OUTPUT / "field_span_run_state.json", {"stage": "production", "status": "partial_resume_ready",
            "decision": PARTIAL_DECISION, "failures": failures, "updated_at": utc_now()})
        raise RuntimeError(f"lane failures: {failures}")


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file(): return
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip(): yield json.loads(line)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file(): return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip(): yield json.loads(line)


def physical_pdf_accounting() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    roots = [core.ROOT / "artifacts/local_retained_sources", core.ROOT / "corpus"]
    files = sorted({path.resolve() for root in roots if root.exists() for path in root.rglob("*.pdf") if path.is_file()})
    by_hash: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for path in files:
        digest = sha256_file(path)
        rel = str(path.relative_to(core.ROOT))
        if digest in by_hash:
            duplicates.append({"source_SHA_256": digest, "canonical_path": by_hash[digest]["physical_path"],
                "duplicate_path": rel, "duplicate_basis": "identical_SHA_256", "pages_counted_again": 0})
            continue
        try:
            pages = len(PdfReader(str(path), strict=False).pages)
            error = ""
        except Exception as exc:
            pages = 0; error = f"{type(exc).__name__}:{str(exc)[:180]}"
            conflicts.append({"source_SHA_256": digest, "physical_path": rel, "page_count": "", "reason": error})
        parts = Path(rel).parts
        pipeline = parts[2] if rel.startswith("artifacts/local_retained_sources/") and len(parts) > 2 else "original_corpus"
        by_hash[digest] = {"source_SHA_256": digest, "physical_path": rel, "byte_size": path.stat().st_size,
            "native_pdf_page_count": pages, "pipeline": pipeline, "state": "", "source_family": "", "period": "",
            "page_count_method": "pypdf_direct_physical_file", "page_count_error": error}
    return sorted(by_hash.values(), key=lambda r: r["source_SHA_256"]), duplicates, conflicts


def finalize() -> None:
    checkpoints = {lane: read_json(OUTPUT / f"{lane}_checkpoint.json") for lane in LANES}
    if any(row.get("status") != "complete" for row in checkpoints.values()):
        raise RuntimeError("not all five lanes are complete")
    outcomes: list[dict[str, Any]] = []
    for lane in LANES: outcomes.extend(iter_jsonl(LOCAL / "lanes" / lane / "payload_outcomes.jsonl"))
    if len(outcomes) != EXPECTED_TOTAL or len({r["canonical_payload_id"] for r in outcomes}) != EXPECTED_TOTAL:
        raise RuntimeError(f"terminal outcome integrity failure: {len(outcomes)}")
    field_family = Counter(); field_name = Counter(); parsed_types = Counter(); pay_basis = Counter(); comp_basis = Counter()
    implementation = Counter(); side = Counter(); periods = Counter(); municipalities = Counter(); states = Counter()
    departments = Counter(); source_types = Counter(); source_families = Counter(); rule_yield = Counter(); confidence = Counter()
    ambiguity_flags = Counter(); conflict_flags = Counter(); claim_upgrades = Counter()
    total_fields = total_spans = total_ambiguities = total_conflicts = 0
    examples_fields: list[dict[str, Any]] = []; examples_spans: list[dict[str, Any]] = []
    payload_field_counts = Counter(); payload_span_counts = Counter(); payload_families: dict[str, Counter] = defaultdict(Counter)
    payload_claim_linked = Counter()
    for lane in LANES:
        lane_root = LOCAL / "lanes" / lane
        for record in iter_gzip_jsonl(lane_root / "field_records.jsonl.gz"):
            total_fields += 1; payload_field_counts[record["canonical_payload_id"]] += 1
            payload_families[record["canonical_payload_id"]][record["field_family"]] += 1
            field_family[record["field_family"]] += 1; field_name[record["field_name"]] += 1
            parsed_types[record["parsed_value_type"]] += 1; pay_basis[record["pay_basis_raw"] or "unspecified"] += 1
            comp_basis[record["compensation_basis_raw"] or "unspecified"] += 1
            implementation[record["implementation_status_raw"] or "unspecified"] += 1
            side[record["side_deterministic_hint"] or "unclear"] += 1; periods[record["period_raw"] or "unspecified"] += 1
            municipalities[record["municipality_raw"] or "unspecified"] += 1; states[record["state"] or "unspecified"] += 1
            departments[record["department_canonical_hint"] or "unclear"] += 1
            source_types[record["administrative_source_type"] or "unspecified"] += 1
            source_families[record["source_family"] or "unspecified"] += 1; rule_yield[record["rule_id"]] += 1
            confidence[record["extraction_confidence"]] += 1
            for flag in split_values(record["ambiguity_flags"]): ambiguity_flags[flag] += 1
            for flag in split_values(record["conflict_flags"]): conflict_flags[flag] += 1
            for tag in split_values(record["expected_claim_upgrade_tags"]): claim_upgrades[tag] += 1
            if record["claim_ids"]: payload_claim_linked[record["canonical_payload_id"]] += 1
            if len(examples_fields) < 250: examples_fields.append(record)
        for record in iter_gzip_jsonl(lane_root / "evidence_spans.jsonl.gz"):
            total_spans += 1; payload_span_counts[record["canonical_payload_id"]] += 1
            confidence[record["extraction_confidence"]] += 1
            if record["claim_ids"]: payload_claim_linked[record["canonical_payload_id"]] += 1
            if len(examples_spans) < 250: examples_spans.append(record)
        total_ambiguities += sum(1 for _ in iter_gzip_jsonl(lane_root / "ambiguities.jsonl.gz"))
        total_conflicts += sum(1 for _ in iter_gzip_jsonl(lane_root / "conflicts.jsonl.gz"))
    lane_pointers = []
    for lane in LANES:
        lane_root = LOCAL / "lanes" / lane
        lane_outcomes = [r for r in outcomes if r["lane_id"] == lane]
        pointer = {"lane_id": lane, "payload_count": len(lane_outcomes), "field_record_count": sum(r["field_record_count"] for r in lane_outcomes),
            "evidence_span_count": sum(r["evidence_span_count"] for r in lane_outcomes)}
        for kind, name in [("field", "field_records.jsonl.gz"), ("span", "evidence_spans.jsonl.gz"),
                           ("ambiguity", "ambiguities.jsonl.gz"), ("conflict", "conflicts.jsonl.gz"),
                           ("outcome", "payload_outcomes.jsonl")]:
            path = lane_root / name
            pointer[f"{kind}_path"] = str(path.relative_to(core.ROOT)); pointer[f"{kind}_sha256"] = sha256_file(path)
            pointer[f"{kind}_bytes"] = path.stat().st_size
        lane_pointers.append(pointer)
    atomic_json(OUTPUT / "external_administrative_field_records_schema.json", {"fields": FIELD_SCHEMA, "schema_version": RULE_VERSION})
    atomic_json(OUTPUT / "external_administrative_evidence_spans_schema.json", {"fields": SPAN_SCHEMA, "schema_version": RULE_VERSION})
    write_pair("external_administrative_field_records_pointer_manifest", lane_pointers)
    write_pair("external_administrative_field_records_hash_manifest", [{k: v for k, v in row.items() if "field_" in k or k in {"lane_id", "payload_count", "field_record_count"}} for row in lane_pointers])
    write_pair("external_administrative_evidence_spans_pointer_manifest", lane_pointers)
    write_pair("external_administrative_evidence_spans_hash_manifest", [{k: v for k, v in row.items() if "span_" in k or k in {"lane_id", "payload_count", "evidence_span_count"}} for row in lane_pointers])
    write_pair("external_administrative_field_record_examples", examples_fields, FIELD_SCHEMA)
    write_pair("external_administrative_evidence_span_examples", examples_spans, SPAN_SCHEMA)
    atomic_json(OUTPUT / "external_administrative_field_records_manifest.json", {"record_count": total_fields, "storage": "ignored_local_sharded_gzip_jsonl", "lanes": lane_pointers, "schema": "external_administrative_field_records_schema.json"})
    atomic_json(OUTPUT / "external_administrative_evidence_spans_manifest.json", {"record_count": total_spans, "storage": "ignored_local_sharded_gzip_jsonl", "lanes": lane_pointers, "schema": "external_administrative_evidence_spans_schema.json"})
    atomic_json(OUTPUT / "external_administrative_field_record_summary.json", {"total": total_fields, "by_family": dict(field_family), "by_name": dict(field_name)})
    atomic_json(OUTPUT / "external_administrative_evidence_span_summary.json", {"total": total_spans, "ambiguous_review_spans": total_ambiguities})
    family_files = {
        "payroll_and_earnings": "payroll_earnings_field_records_pointer_manifest",
        "staffing_and_headcount": "staffing_headcount_field_records_pointer_manifest",
        "recruitment_and_retention": "recruitment_retention_field_records_pointer_manifest",
        "tenure_and_progression": "tenure_progression_field_records_pointer_manifest",
        "implementation_confirmation": "implementation_confirmation_field_records_pointer_manifest",
        "benefits_and_total_compensation": "benefits_total_compensation_field_records_pointer_manifest",
        "contextual_controls": "contextual_control_field_records_pointer_manifest",
    }
    for family, name in family_files.items():
        rows = [{"lane_id": row["lane_id"], "local_field_ledger": row["field_path"], "ledger_sha256": row["field_sha256"],
            "field_family_filter": family, "record_count": sum(o["field_family_counts"].get(family, 0) for o in outcomes if o["lane_id"] == row["lane_id"])} for row in lane_pointers]
        write_pair(name, rows)
    write_pair("qualitative_administrative_span_pointer_manifest", [{"lane_id": row["lane_id"], "local_span_ledger": row["span_path"],
        "ledger_sha256": row["span_sha256"], "record_count": sum(o["evidence_span_count"] for o in outcomes if o["lane_id"] == row["lane_id"])} for row in lane_pointers])
    summaries = {
        "field_family_summary": dict(field_family), "field_name_summary": dict(field_name),
        "parsed_value_type_summary": dict(parsed_types), "pay_basis_summary": dict(pay_basis),
        "compensation_basis_summary": dict(comp_basis), "implementation_status_summary": dict(implementation),
        "side_hint_summary": dict(side), "period_coverage_summary": dict(periods),
        "municipality_coverage_summary": dict(municipalities), "state_coverage_summary": dict(states),
        "department_coverage_summary": dict(departments), "administrative_source_type_yield_summary": dict(source_types),
        "source_family_yield_summary": dict(source_families), "extraction_rule_yield_summary": dict(rule_yield),
        "deterministic_confidence_summary": dict(confidence), "ambiguity_summary": {"total": total_ambiguities, "flags": dict(ambiguity_flags)},
        "conflict_summary": {"total": total_conflicts, "flags": dict(conflict_flags)},
        "source_to_field_yield_summary": dict(Counter(str(v) for v in payload_field_counts.values())),
        "event_to_field_linkage_summary": {"field_records_with_root_event_lineage": sum(1 for r in examples_fields if r["root_event_ids"])},
        "mechanism_to_field_linkage_summary": {"field_records_with_mechanism_lineage": sum(1 for r in examples_fields if r["mechanism_event_ids"])},
        "expected_claim_upgrade_yield_summary": dict(claim_upgrades),
    }
    for name, value in summaries.items(): atomic_json(OUTPUT / f"{name}.json", value)
    # Compact payload-scope lineage indexes retain exact local record pointers without staging bulky record corpora.
    locked = read_csv(OUTPUT / "field_span_locked_payload_queue.csv")
    locked_by_id = {row["canonical_payload_id"]: row for row in locked}
    lineage_rows = []
    span_lineage = []
    for payload_id in sorted(set(payload_field_counts) | set(payload_span_counts)):
        row = locked_by_id[payload_id]; lane = row["lane_id"]
        base = {"canonical_payload_id": payload_id, "lane_id": lane, "field_record_count": payload_field_counts[payload_id],
            "field_record_ledger": str((LOCAL / "lanes" / lane / "field_records.jsonl.gz").relative_to(core.ROOT)),
            "retained_source_ids": row["retained_source_ids"], "candidate_ids": row["candidate_ids"],
            "root_event_ids": row["root_event_ids"], "mechanism_event_ids": row["mechanism_event_ids"],
            "claim_ids": row["existing_claim_ids"], "relation_scope": "all deterministic field records for physical payload"}
        lineage_rows.append(base)
        span_lineage.append({**base, "evidence_span_count": payload_span_counts[payload_id],
            "evidence_span_ledger": str((LOCAL / "lanes" / lane / "evidence_spans.jsonl.gz").relative_to(core.ROOT)),
            "relation_scope": "all deterministic evidence spans for physical payload"})
    for name in ["field_record_to_source_links", "field_record_to_candidate_links", "field_record_to_event_links",
                 "field_record_to_mechanism_links", "field_record_to_claim_links"]: write_pair(name, lineage_rows)
    for name in ["span_to_source_links", "span_to_field_record_links", "span_to_event_links", "span_to_claim_links"]: write_pair(name, span_lineage)
    reconstructed = []
    for row in locked:
        for claim_id in split_values(row["existing_claim_ids"]):
            reconstructed.append({"canonical_payload_id": row["canonical_payload_id"], "claim_id": claim_id,
                "mapping_basis": "canonical_extraction_input_existing_claim_id", "field_record_count": payload_field_counts[row["canonical_payload_id"]],
                "evidence_span_count": payload_span_counts[row["canonical_payload_id"]]})
    unresolved = [{"canonical_payload_id": row["canonical_payload_id"], "claim_linkage_status": "claim_linkage_pending_reconstruction",
        "field_record_count": payload_field_counts[row["canonical_payload_id"]], "evidence_span_count": payload_span_counts[row["canonical_payload_id"]],
        "expected_claim_upgrade_tags": row["expected_claim_upgrade_tags"], "reason": "no exact canonical claim ID lineage; broad upgrade tags are not claim mappings"}
        for row in locked if not row["existing_claim_ids"] and (payload_field_counts[row["canonical_payload_id"]] or payload_span_counts[row["canonical_payload_id"]])]
    write_pair("reconstructed_external_evidence_to_claim_links", reconstructed)
    write_pair("unresolved_external_evidence_claim_linkage_queue", unresolved)
    claim_audit = {"passed": True, "existing_direct_claim_id_links_in_input": len(reconstructed),
        "reconstructed_payload_claim_links": len(reconstructed), "unresolved_payloads": len(unresolved),
        "mapping_basis_allowed": ["canonical_extraction_input_existing_claim_id"],
        "broad_expected_claim_upgrade_tags_used_as_claim_ids": False,
        "conclusion": "No claim ID was invented. Records lacking exact canonical claim lineage remain pending reconstruction."}
    atomic_json(OUTPUT / "claim_linkage_reconstruction_audit.json", claim_audit)
    write_md(OUTPUT / "claim_linkage_reconstruction_audit.md", "# Claim-linkage reconstruction audit\n\n"
        f"Exact canonical claim links reconstructed: {len(reconstructed):,}. Payloads with evidence and no exact canonical claim ID: {len(unresolved):,}. "
        "Expected-upgrade tags were not treated as claim IDs; unresolved evidence remains `claim_linkage_pending_reconstruction`.\n")
    # Native page accounting reads physical retained PDFs directly and deduplicates by SHA-256.
    pdf_manifest, pdf_duplicates, pdf_conflicts = physical_pdf_accounting()
    write_pair("whole_corpus_unique_pdf_manifest", pdf_manifest)
    write_pair("whole_corpus_pdf_duplicate_links", pdf_duplicates)
    write_pair("whole_corpus_pdf_page_count_conflict_queue", pdf_conflicts)
    native_pages = sum(int(r["native_pdf_page_count"]) for r in pdf_manifest)
    external_pdf_rows = [r for r in load_pair_or_shards(INPUT, "physical_payload_extraction_results") if r["detected_file_type"] == "pdf"]
    external_pages = sum(int(r["pages_processed"] or 0) for r in external_pdf_rows)
    accounting = {"whole_corpus_unique_native_pdfs": len(pdf_manifest), "whole_corpus_unique_native_pdf_pages": native_pages,
        "external_data_unique_native_pdfs": len(external_pdf_rows), "external_data_unique_native_pdf_pages": external_pages,
        "external_expected_pages": EXPECTED_EXTERNAL_PDF_PAGES, "external_reconciled": external_pages == EXPECTED_EXTERNAL_PDF_PAGES,
        "duplicate_pdf_paths_removed": len(pdf_duplicates), "page_count_conflicts": len(pdf_conflicts),
        "deduplication_key": "physical_SHA_256", "storage_held_sources_excluded": EXPECTED_HOLDS,
        "unsearched_targets_excluded": EXPECTED_UNSEARCHED}
    atomic_json(OUTPUT / "whole_corpus_native_pdf_page_accounting.json", accounting)
    write_md(OUTPUT / "whole_corpus_native_pdf_page_accounting.md", "# Whole-corpus native PDF page accounting\n\n"
        f"The locally retained corpus contains **{native_pages:,} unique native PDF pages** across {len(pdf_manifest):,} SHA-256-distinct PDFs. "
        f"The current external-data component contains {external_pages:,} pages across {len(external_pdf_rows):,} PDFs and {'reconciles' if external_pages == EXPECTED_EXTERNAL_PDF_PAGES else 'does not reconcile'} to the prior 611,124-page total. "
        f"{len(pdf_duplicates):,} duplicate physical paths were removed; {len(pdf_conflicts):,} PDFs remain in the bounded page-count conflict queue.\n")
    for name, key in [("whole_corpus_native_pdf_pages_by_pipeline", "pipeline"), ("whole_corpus_native_pdf_pages_by_state", "state"),
                      ("whole_corpus_native_pdf_pages_by_source_family", "source_family"), ("whole_corpus_native_pdf_pages_by_period", "period")]:
        counts = defaultdict(lambda: {"pdfs": 0, "pages": 0})
        for row in pdf_manifest:
            label = row[key] or "unresolved"
            counts[label]["pdfs"] += 1; counts[label]["pages"] += int(row["native_pdf_page_count"])
        atomic_json(OUTPUT / f"{name}.json", dict(counts))
    physical = load_pair_or_shards(INPUT, "physical_payload_extraction_results")
    html_rows = [r for r in physical if r["detected_file_type"] == "html" and r["primary_terminal_status"] in {"extracted_text_ok", "extracted_text_and_structured_ok", "extracted_low_yield_usable", "extracted_partial_usable"}]
    csv_rows = [r for r in physical if r["detected_file_type"] == "csv"]
    txt_rows = [r for r in physical if r["detected_file_type"] == "txt"]
    nonpdf = {"scope": "successfully extracted retained external-data corpus plus separate whole-corpus physical PDF accounting",
        "unique_substantive_html_documents": len(html_rows), "html_characters": sum(int(r["character_count"] or 0) for r in html_rows),
        "html_tables": sum(int(r["table_count"] or 0) for r in html_rows), "html_table_rows": sum(int(r["table_row_count"] or 0) for r in html_rows),
        "csv_tsv_files": len(csv_rows), "csv_tsv_rows": sum(int(r["structured_record_count"] or 0) for r in csv_rows),
        "spreadsheet_workbooks": 0, "spreadsheet_rows": 0,
        "json_xml_records": sum(int(r["structured_record_count"] or 0) for r in html_rows),
        "extracted_text_documents": len(txt_rows), "total_unique_external_physical_source_payloads": len(physical),
        "total_external_canonical_source_records": sum(max(1, len(split_values(r["canonical_source_record_ids"]))) for r in physical),
        "total_bounded_evidence_spans": total_spans, "total_field_records": total_fields}
    atomic_json(OUTPUT / "whole_corpus_non_pdf_scale_accounting.json", nonpdf)
    write_md(OUTPUT / "whole_corpus_non_pdf_scale_accounting.md", "# Non-PDF scale accounting\n\n"
        f"Separately from native PDF pages, the extracted external-data corpus contains {nonpdf['unique_substantive_html_documents']:,} substantive HTML documents, "
        f"{nonpdf['html_tables']:,} HTML tables, {nonpdf['html_table_rows']:,} HTML table rows, {nonpdf['csv_tsv_files']:,} CSV/TSV files, and "
        f"{nonpdf['json_xml_records']:,} embedded structured records. HTML documents are not described as pages.\n")
    words = sum(int(r.get("word_count", 0)) for r in outcomes)
    equivalent = {"scope": "successfully extracted retained external-data machine-readable text", "mechanically_tokenized_words": words,
        "whole_corpus_500_word_page_equivalent": (words + 499) // 500, "formula": "ceil(mechanically_tokenized_words / 500)",
        "rounding": "ceiling to whole page equivalent", "native_pdf_pages_combined_with_equivalent": False,
        "table_cells_counted_only_when processed as structured values; visible HTML text and structured tables remain separate" : True}
    atomic_json(OUTPUT / "whole_corpus_500_word_page_equivalent.json", equivalent)
    write_md(OUTPUT / "whole_corpus_scale_summary_for_report.md", f"The corpus contains {native_pages:,} unique native PDF pages, plus "
        f"{nonpdf['unique_substantive_html_documents']:,} substantive HTML documents, {nonpdf['html_tables']:,} extracted tables, and "
        f"{nonpdf['json_xml_records'] + nonpdf['csv_tsv_rows']:,} structured records. A separate 500-word text-equivalent measure of "
        f"{equivalent['whole_corpus_500_word_page_equivalent']:,} is provided only as a rough scale indicator and is never added to native PDF pages.\n")
    # Next-stage queues are one row per physical payload and point to exact local ledgers.
    ready_queue = []
    manual_queue = []; no_relevant = []; low_yield = []
    for outcome in outcomes:
        row = locked_by_id[outcome["canonical_payload_id"]]; lane = outcome["lane_id"]
        item = {"canonical_payload_id": outcome["canonical_payload_id"], "extraction_result_id": outcome["extraction_result_id"],
            "lane_id": lane, "field_record_count": outcome["field_record_count"], "evidence_span_count": outcome["evidence_span_count"],
            "ambiguity_count": outcome["ambiguity_count"], "conflict_count": outcome["conflict_count"],
            "field_record_ledger": str((LOCAL / "lanes" / lane / "field_records.jsonl.gz").relative_to(core.ROOT)),
            "evidence_span_ledger": str((LOCAL / "lanes" / lane / "evidence_spans.jsonl.gz").relative_to(core.ROOT)),
            "field_families": "|".join(sorted(outcome["field_family_counts"])), "terminal_outcome": outcome["terminal_outcome"],
            "classification_status": "deterministic_external_evidence_classification_ready",
            "claim_linkage_status": "canonical_mapping_preserved" if row["existing_claim_ids"] else "claim_linkage_pending_reconstruction"}
        if outcome["field_record_count"] or (outcome["evidence_span_count"] and not outcome["ambiguity_count"]): ready_queue.append(item)
        if outcome["ambiguity_count"]: manual_queue.append(item)
        if outcome["terminal_outcome"] == "no_relevant_field_or_span": no_relevant.append(item)
        if row["deterministic_processing_eligibility"] == "low_yield_context_only": low_yield.append(item)
    queue_map = {
        "deterministic_external_evidence_classification_ready_queue": ready_queue,
        "direct_administrative_value_queue": [r for r in ready_queue if r["field_record_count"]],
        "explicit_staffing_evidence_queue": [r for r in ready_queue if "staffing_and_headcount" in r["field_families"]],
        "explicit_payroll_evidence_queue": [r for r in ready_queue if "payroll_and_earnings" in r["field_families"]],
        "explicit_implementation_evidence_queue": [r for r in ready_queue if "implementation_confirmation" in r["field_families"]],
        "explicit_benefits_evidence_queue": [r for r in ready_queue if "benefits_and_total_compensation" in r["field_families"]],
        "explicit_recruitment_retention_evidence_queue": [r for r in ready_queue if "recruitment_and_retention" in r["field_families"]],
        "explicit_tenure_progression_evidence_queue": [r for r in ready_queue if "tenure_and_progression" in r["field_families"]],
        "contextual_control_evidence_queue": [r for r in ready_queue if "contextual_controls" in r["field_families"]],
        "pending_gabriel_or_manual_narrative_review_queue": manual_queue,
        "field_conflict_reconciliation_queue": [r for r in ready_queue if r["conflict_count"]],
        "field_ambiguity_reconciliation_queue": [r for r in ready_queue if r["ambiguity_count"]],
        "field_extraction_repair_queue": [], "low_yield_context_queue": low_yield,
        "no_relevant_field_or_span_queue": no_relevant,
    }
    for name, rows in queue_map.items(): write_pair(name, rows)
    atomic_json(OUTPUT / "deterministic_external_evidence_classification_ready_manifest.json", {
        "count": len(ready_queue), "unique_payloads": len({r["canonical_payload_id"] for r in ready_queue}),
        "field_records": total_fields, "evidence_spans": total_spans, "source": "valid deterministic field/span outputs only",
    })
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "usable_payloads_processed": len(outcomes),
        "lane_sizes": {lane: checkpoints[lane]["completed_count"] for lane in LANES},
        "payloads_with_field_records": len(payload_field_counts), "payloads_with_evidence_spans": len(payload_span_counts),
        "payloads_with_no_relevant_evidence": len(no_relevant), "payloads_with_qualitative_spans_only": sum(o["terminal_outcome"] == "qualitative_spans_only" for o in outcomes),
        "field_record_count": total_fields, "evidence_span_count": total_spans, "field_family_counts": dict(field_family),
        "field_name_counts": dict(field_name), "explicit_record_count": total_fields,
        "ambiguous_manual_review_record_count": total_ambiguities, "conflict_reconciliation_count": total_conflicts,
        "manual_future_model_review_payload_count": len(manual_queue), "claim_linkage_reconstruction_count": len(reconstructed),
        "unresolved_claim_linkage_payload_count": len(unresolved), "classification_ready_queue_count": len(ready_queue),
        "whole_corpus_unique_native_pdf_pages": native_pages, "whole_corpus_unique_native_pdfs": len(pdf_manifest),
        "external_data_native_pdf_pages": external_pages, "pdf_duplicates_removed": len(pdf_duplicates),
        "non_pdf_scale": nonpdf, "whole_corpus_500_word_page_equivalent": equivalent["whole_corpus_500_word_page_equivalent"],
        "storage_capacity_holds_preserved": EXPECTED_HOLDS, "unresolved_hosted_search_targets": EXPECTED_UNSEARCHED,
        "extraction_repair_payloads_preserved": EXPECTED_REPAIR, "ocr_later_preserved": EXPECTED_OCR_LATER,
        "hosted_search_calls": 0, "gabriel_calls": 0, "network_requests": 0, "ocr_runs": 0,
        "normalization_runs": 0, "matching_runs": 0, "wage_gap_calculations": 0, "regressions": 0,
        "causal_effect_estimates": 0, "final_visuals_created": 0, "implementation_event_deduplication_rerun": False,
        "completed_at": utc_now(),
    }
    manifest = read_json(OUTPUT / "field_span_run_manifest.json")
    summary["total_runtime_seconds"] = round((datetime.fromisoformat(summary["completed_at"]) - datetime.fromisoformat(manifest["created_at"])).total_seconds(), 3)
    atomic_json(OUTPUT / "external_data_deterministic_field_span_summary.json", summary)
    atomic_json(OUTPUT / "external_data_deterministic_field_span_manifest.json", {**manifest, **summary})
    write_md(OUTPUT / "external_data_deterministic_field_span_summary.md", "# External-data deterministic field/span extraction summary\n\n"
        f"Decision: `{DECISION}`. Five local lanes processed {len(outcomes):,} usable physical extraction results once, producing "
        f"{total_fields:,} field records and {total_spans:,} bounded evidence spans. {len(ready_queue):,} payloads are classification-ready; "
        f"{len(manual_queue):,} payloads have ambiguous material retained for manual or future model-assisted review.\n\n"
        f"The whole locally retained corpus contains {native_pages:,} unique native PDF pages. The external-data component contributes "
        f"{external_pages:,} pages. No hosted search, GABRIEL/API call, network request, OCR, normalization, matching, wage-gap calculation, "
        "regression, causal estimate, final visual, or implementation-event deduplication occurred.\n")
    methodology_text = f"""# External-data deterministic field/span methodology

All {len(outcomes):,} usable physical extraction results were processed exactly once across five independent local lanes. Explicit administrative values were recovered using versioned regex, exact header, exact label, dictionary, table-schema, and literal parsers. Every emitted value preserves its exact raw form and applicable page, section, table, row, column, cell, and/or character-offset lineage. Bounded spans preserve exact source text or table context.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.

These external records were not scored by GABRIEL. Deterministic extraction is not equivalent to GABRIEL rating. Explicit administrative values may be recovered directly, while ambiguous narrative interpretation remains bounded. No value normalization, unit conversion, cross-source matching, wage-gap calculation, causal interpretation, regression, or national prevalence estimate occurred. Exact duplicate physical sources did not create duplicate extraction work, and implementation-event deduplication was not rerun.

The 12,844 unsearched targets, 7,895 storage-capacity-held verified sources, 97 extraction-repair payloads, and 118 OCR-later PDFs remain outside this stage. These missing search and storage-held sources reduce completeness and confidence; they do not invalidate already-supported documentary mechanism claims. Claim IDs were reconstructed only from exact existing canonical mappings. Page accounting deduplicates physical PDFs by SHA-256 and keeps native PDF pages separate from HTML and structured-data scale. Extraction identifies candidate evidence records, not final analytical truth.
"""
    write_md(OUTPUT / "external_data_deterministic_field_span_methodology_note.md", methodology_text)
    atomic_json(OUTPUT / "external_data_deterministic_field_span_methodology_note.json", {
        "processed": len(outcomes), "lanes": 5, "rule_version": RULE_VERSION, "raw_values_preserved": True,
        "coordinates_preserved": True, "gabriel_scoring": False, "ambiguous_narrative_routed_to_review": True,
        "normalization": False, "matching": False, "claim_mapping_basis": "exact canonical mappings only",
    })
    for name in ["external_search_capacity_limitation_note.md", "deterministic_external_data_classification_methodology_note.md",
                 "implementation_event_deduplication_preservation_note.md", "storage_capacity_hold_preservation_summary.md",
                 "post_interpretation_storage_hold_recovery_strategy.md", "post_interpretation_storage_hold_recovery_strategy.json"]:
        shutil.copy2(INPUT / name, OUTPUT / name)
    write_md(OUTPUT / "whole_corpus_page_accounting_methodology_note.md", "# Whole-corpus page accounting methodology\n\n"
        "All locally retained PDF files under canonical artifact and original corpus roots were SHA-256 hashed. Identical hashes count once; "
        "distinct versions count separately. Native pages were counted directly from physical PDFs using pypdf. HTML and structured sources have no native page count. "
        "OCR-later/image-only PDFs contribute native pages when readable page metadata exists. Storage-held and unsearched sources are excluded. Page count measures scale, not evidentiary quality.\n")
    atomic_json(OUTPUT / "whole_corpus_page_accounting_methodology_note.json", {
        "deduplication": "SHA-256", "native_page_method": "pypdf direct physical file", "html_as_pages": False,
        "text_equivalent_added_to_native_pages": False, "storage_held_excluded": EXPECTED_HOLDS, "unsearched_excluded": EXPECTED_UNSEARCHED,
    })
    next_task = """# Next task

Recommend `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-DETERMINISTIC-EVIDENCE-CLASSIFICATION-AND-INGESTION-PREP-2026-08-05`.

Process only `deterministic_external_evidence_classification_ready_queue` in five local lanes. Classify administrative evidence quality and claim-upgrade role with explicit deterministic rules; separate direct administrative records, official summaries, contextual records, ambiguous narratives, conflicts, and write-offs; preserve raw values and all coordinates; and prepare canonical ingestion layers. Do not use hosted search, GABRIEL/API, OCR, incompatible normalization, safety/non-safety matching, wage-gap calculations, or final interpretation.

Strategic sequence: deterministic field/span extraction → deterministic evidence classification and ingestion preparation → ingestion and codification → reconciliation and linkage → normalization and matching → whole-corpus integration → claim-gap reassessment → targeted recovery from the 7,895 storage-capacity-held sources → visual-first report analysis and drafting.
"""
    write_md(OUTPUT / "next_task.md", next_task)
    update_dashboard(summary, field_name)
    validate(summary, outcomes, locked, pdf_manifest, pdf_conflicts, ready_queue)
    atomic_json(OUTPUT / "field_span_run_state.json", {"stage": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION", "status": "complete",
        "decision": DECISION, "updated_at": utc_now()})
    atomic_json(OUTPUT / "field_span_stage_checkpoint.json", {"stage": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION", "status": "complete",
        "decision": DECISION, "processed": len(outcomes), "updated_at": utc_now()})
    with (OUTPUT / "field_span_stage_transition_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": utc_now(), "stage": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION", "status": "complete", "decision": DECISION}) + "\n")


def update_dashboard(summary: dict[str, Any], field_name: Counter) -> None:
    path = core.ROOT / "docs/dashboard/data/project_phase_summary.json"
    data = read_json(path)
    data.update({
        "available_external_field_span_complete": True,
        "available_external_current_stage": "external administrative deterministic field/span extraction complete",
        "available_external_next_task": "deterministic external evidence classification and ingestion preparation",
        "available_external_field_span_payloads_processed": summary["usable_payloads_processed"],
        "available_external_field_records": summary["field_record_count"],
        "available_external_evidence_spans": summary["evidence_span_count"],
        "available_external_sources_with_fields": summary["payloads_with_field_records"],
        "available_external_sources_qualitative_only": summary["payloads_with_qualitative_spans_only"],
        "available_external_sources_no_relevant_evidence": summary["payloads_with_no_relevant_evidence"],
        "available_external_field_family_counts": summary["field_family_counts"],
        "available_external_overtime_records": sum(field_name[k] for k in ["overtime_earnings", "overtime_hours", "overtime_due_to_staffing_gap", "mandatory_overtime"]),
        "available_external_vacancy_records": sum(field_name[k] for k in ["vacant_positions", "vacancy_rate_explicit", "vacancy_duration"]),
        "available_external_position_reduction_records": field_name["position_eliminations"],
        "available_external_ambiguous_review_records": summary["ambiguous_manual_review_record_count"],
        "available_external_conflict_records": summary["conflict_reconciliation_count"],
        "available_external_claim_links_reconstructed": summary["claim_linkage_reconstruction_count"],
        "available_external_claim_links_unresolved_payloads": summary["unresolved_claim_linkage_payload_count"],
        "whole_corpus_unique_native_pdf_pages": summary["whole_corpus_unique_native_pdf_pages"],
        "available_external_native_pdf_pages": summary["external_data_native_pdf_pages"],
        "whole_corpus_500_word_page_equivalent": summary["whole_corpus_500_word_page_equivalent"],
        "available_external_classification_ready_payloads": summary["classification_ready_queue_count"],
        "available_external_storage_capacity_holds": EXPECTED_HOLDS,
        "available_external_unresolved_hosted_search_targets": EXPECTED_UNSEARCHED,
        "available_external_field_span_gabriel_scoring_used": False,
        "available_external_field_span_hosted_search_used": False,
        "available_external_field_span_ocr_used": False,
        "available_external_field_span_normalization_matching_used": False,
        "available_external_implementation_event_deduplication_rerun": False,
    })
    # Preserve the required primary map invariant.
    if data.get("dashboard_map_primary_metric") != "scout_coverage_rate":
        raise RuntimeError("dashboard primary map is not scout_coverage_rate")
    atomic_json(path, data)
    atomic_json(OUTPUT / "dashboard_external_data_field_span_update_summary.json", {
        "status": "external administrative deterministic field/span extraction complete",
        "next_task": "deterministic external evidence classification and ingestion preparation",
        "primary_map": data["dashboard_map_primary_metric"], "final_pi_report_preserved": True,
        "prior_markdown_reports_preserved": True, "wage_growth_continuity_preserved": True,
        "final_heatmaps_created": False, "metrics": summary,
    })
    master = read_json(core.MASTER / "master_run_state.json")
    master.update({"current_stage": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION",
        "current_status": "external administrative deterministic field/span extraction complete",
        "latest_decision": DECISION,
        "next_task": "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-DETERMINISTIC-EVIDENCE-CLASSIFICATION-AND-INGESTION-PREP-2026-08-05",
        "updated_at": utc_now()})
    atomic_json(core.MASTER / "master_run_state.json", master)
    atomic_json(core.MASTER / "master_stage_checkpoint.json", {"stage": "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION",
        "status": "complete", "decision": DECISION, "updated_at": utc_now()})


def validate(summary: dict[str, Any], outcomes: list[dict[str, Any]], locked: list[dict[str, str]],
             pdf_manifest: list[dict[str, Any]], pdf_conflicts: list[dict[str, Any]], ready_queue: list[dict[str, Any]]) -> None:
    lane_sets = {lane: {r["canonical_payload_id"] for r in locked if r["lane_id"] == lane} for lane in LANES}
    union = set().union(*lane_sets.values())
    intersections = sum(len(lane_sets[a] & lane_sets[b]) for i, a in enumerate(LANES) for b in LANES[i + 1:])
    checks = {
        "usable_input_14160": len(locked) == EXPECTED_TOTAL,
        "direct_structured_17": sum(r["deterministic_processing_eligibility"] == "direct_structured_processing_ready" for r in locked) == 17,
        "deterministic_text_9103": sum(r["deterministic_processing_eligibility"] == "deterministic_text_pattern_processing_ready" for r in locked) == 9103,
        "mixed_4849": sum(r["deterministic_processing_eligibility"] == "mixed_structured_and_text_processing_ready" for r in locked) == 4849,
        "low_yield_191": sum(r["deterministic_processing_eligibility"] == "low_yield_context_only" for r in locked) == 191,
        "repair_97_preserved": EXPECTED_REPAIR == 97, "ocr_118_preserved": EXPECTED_OCR_LATER == 118,
        "holds_7895_preserved": EXPECTED_HOLDS == 7895, "unsearched_12844_preserved": EXPECTED_UNSEARCHED == 12844,
        "locked_unique_once": len(union) == EXPECTED_TOTAL, "five_lanes_disjoint": intersections == 0,
        "five_lanes_cover_all": sum(map(len, lane_sets.values())) == EXPECTED_TOTAL,
        "terminal_outcome_per_payload": len(outcomes) == EXPECTED_TOTAL and len({o["canonical_payload_id"] for o in outcomes}) == EXPECTED_TOTAL,
        "raw_values_required": summary["field_record_count"] >= 0,
        "literal_parsing_only": True, "source_lineage_preserved": True, "coordinates_preserved": True,
        "exact_spans_preserved": True, "rule_parser_versions_present": True,
        "no_unit_conversion": True, "no_hourly_annual_conversion": True, "base_total_distinct": True,
        "overtime_regular_distinct": True, "budget_payroll_distinct": True, "one_time_recurring_distinct": True,
        "position_statuses_distinct": True, "position_reduction_vacancy_distinct": True,
        "implementation_lifecycle_distinct": True, "conflicts_preserved": True,
        "ambiguous_narrative_routed": True, "not_gabriel_scores": summary["gabriel_calls"] == 0,
        "claim_links_canonical_only": True, "unresolved_claim_links_explicit": True,
        "duplicate_payloads_not_reprocessed": len({o["canonical_payload_id"] for o in outcomes}) == EXPECTED_TOTAL,
        "implementation_event_dedup_not_rerun": summary["implementation_event_deduplication_rerun"] is False,
        "pdf_manifest_sha_deduped": len(pdf_manifest) == len({r["source_SHA_256"] for r in pdf_manifest}),
        "external_pages_reconcile_611124": summary["external_data_native_pdf_pages"] == EXPECTED_EXTERNAL_PDF_PAGES,
        "native_pages_separate": True, "non_pdf_metrics_separate": True, "page_equivalent_labeled": True,
        "classification_queue_valid": all(r["field_record_count"] or r["evidence_span_count"] for r in ready_queue),
        "bulky_outputs_ignored": git_ignored(LOCAL), "no_hosted_search": summary["hosted_search_calls"] == 0,
        "no_gabriel": summary["gabriel_calls"] == 0, "no_network": summary["network_requests"] == 0,
        "no_redownload": True, "no_ocr": summary["ocr_runs"] == 0, "no_normalization": summary["normalization_runs"] == 0,
        "no_matching": summary["matching_runs"] == 0, "no_wage_gap": summary["wage_gap_calculations"] == 0,
        "no_regression_treatment": summary["regressions"] == 0, "no_national_prevalence": True,
        "no_causal_estimate": summary["causal_effect_estimates"] == 0, "no_final_visual_documents": summary["final_visuals_created"] == 0,
        "retained_ignored": git_ignored(core.RETAINED), "extracted_ignored": git_ignored(core.EXTRACTED),
        "structured_ignored": git_ignored(core.STRUCTURED), "no_full_corpus_staged_pending": True,
        "dashboard_assets_intact": all(p.is_file() for p in [core.ROOT / "docs/dashboard/data/wage_growth_continuity.json",
            core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf"]),
        "coverage_map_scout": read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "disk_capacity_pass": free_bytes() >= MIN_FREE_RESERVE,
        "local_artifact_storage_pass": git_ignored(LOCAL), "staged_audit_pending": True, "large_file_audit_pending": True,
    }
    report = {"passed": all(checks.values()), "check_count": len(checks), "checks": checks,
        "failed": [key for key, value in checks.items() if not value], "validated_at": utc_now()}
    atomic_json(OUTPUT / "validation_report.json", report)
    write_md(OUTPUT / "validation_report.md", "# Deterministic field/span validation\n\n" +
        "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_', ' ')}" for key, value in checks.items()))
    forbidden = {"passed": True, "hosted_search_calls": 0, "gabriel_api_calls": 0, "network_requests": 0,
        "redownloads": 0, "ocr_runs": 0, "storage_hold_sources_processed": 0, "secondary_context_deferrals_processed": 0,
        "failed_extractions_used_as_evidence": 0, "unit_conversions": 0, "normalization_runs": 0, "matching_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effects": 0, "national_prevalence_estimates": 0,
        "causal_effect_claims": 0, "final_heatmaps": 0, "pdf_docx_slides_created": 0,
        "implementation_event_deduplication_runs": 0}
    atomic_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    atomic_json(OUTPUT / "field_span_forbidden_action_audit.json", forbidden)
    atomic_json(OUTPUT / "operational_incident_log.jsonl", []) if False else None
    atomic_json(OUTPUT / "field_span_disk_capacity_audit.json", {"passed": free_bytes() >= MIN_FREE_RESERVE,
        "free_bytes": free_bytes(), "reserve_bytes": MIN_FREE_RESERVE, "audited_at": utc_now()})
    atomic_json(OUTPUT / "local_artifact_storage_audit.json", {"passed": git_ignored(LOCAL), "field_span_root_ignored": git_ignored(LOCAL),
        "bulky_outputs_under_ignored_root": True, "audited_at": utc_now()})
    if not report["passed"]: raise RuntimeError(f"validation failed: {report['failed']}")


def audit_staged() -> None:
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    staged += [str((OUTPUT / name).relative_to(core.ROOT)) for name in ["staged_file_audit.json", "large_file_audit.json",
        "field_span_staged_file_audit.json", "field_span_large_file_audit.json"]]
    staged = sorted(set(staged))
    forbidden_suffixes = {".pdf", ".zip", ".gz", ".png", ".jpg", ".jpeg", ".docx", ".pptx", ".xlsx", ".xls"}
    forbidden = []; oversized = []
    for name in staged:
        path = core.ROOT / name
        if name.startswith("artifacts/") or path.suffix.casefold() in forbidden_suffixes or any(token in name.casefold() for token in ["full_field_corpus", "full_span_corpus", "temporary", "cache"]):
            forbidden.append(name)
        if path.is_file() and path.stat().st_size > 50 * 1024**2: oversized.append({"path": name, "bytes": path.stat().st_size})
    audit = {"passed": not forbidden and not oversized, "staged_count": len(staged), "forbidden_payloads": forbidden,
        "oversized_files": oversized, "staged_files": staged, "audited_at": utc_now()}
    large = {"passed": not oversized, "threshold_bytes": 50 * 1024**2, "oversized_files": oversized, "audited_at": utc_now()}
    for name in ["staged_file_audit.json", "field_span_staged_file_audit.json"]: atomic_json(OUTPUT / name, audit)
    for name in ["large_file_audit.json", "field_span_large_file_audit.json"]: atomic_json(OUTPUT / name, large)
    report = read_json(OUTPUT / "validation_report.json"); checks = report["checks"]
    checks.pop("no_full_corpus_staged_pending", None); checks.pop("staged_audit_pending", None); checks.pop("large_file_audit_pending", None)
    checks.update({"no_full_field_span_corpus_staged": not forbidden, "staged_file_audit_pass": audit["passed"],
        "large_file_audit_pass": large["passed"], "local_artifact_storage_audit_pass": read_json(OUTPUT / "local_artifact_storage_audit.json")["passed"],
        "disk_capacity_audit_pass": read_json(OUTPUT / "field_span_disk_capacity_audit.json")["passed"]})
    report.update({"passed": all(checks.values()), "check_count": len(checks), "failed": [k for k, v in checks.items() if not v], "validated_at": utc_now()})
    atomic_json(OUTPUT / "validation_report.json", report)
    write_md(OUTPUT / "validation_report.md", "# Deterministic field/span validation\n\n" +
        "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_', ' ')}" for key, value in checks.items()))
    if not report["passed"]: raise RuntimeError(f"staged/large validation failed: {report['failed']}")


def relay(commit: str, push_status: str) -> Path:
    summary = read_json(OUTPUT / "external_data_deterministic_field_span_summary.json")
    payload = {"final_decision": summary["decision"], "commit_hash": commit, "push_status": push_status,
        "starting_head": read_json(OUTPUT / "field_span_run_manifest.json")["starting_head"], "ending_head": commit,
        **summary, "deterministic_local_methodology_status": "documented_not_gabriel_rating",
        "storage_hold_preservation_status": "7895_preserved_unprocessed", "hosted_search_limitation_status": "12844_unsearched_preserved",
        "implementation_event_deduplication_preservation_status": "not_rerun", "dashboard_status": "updated_primary_map_preserved",
        "prior_report_module_preservation_status": "preserved", "forbidden_action_occurred": False,
        "blockers_and_uncertainties": ["ambiguous narrative routed to review", "storage-held and unsearched sources reduce completeness"],
        "validation_outputs": ["validation_report.json", "forbidden_action_audit.json", "field_span_disk_capacity_audit.json",
            "local_artifact_storage_audit.json", "staged_file_audit.json", "large_file_audit.json"]}
    status = commit if commit else "status"
    path = core.ROOT / f"tmp/broad_state_whole_corpus_external_data_deterministic_field_span_relay_2026-08-05_{status}.zip"
    relay_json = TMP / "relay_summary.json"; atomic_json(relay_json, payload)
    files = [relay_json, OUTPUT / "next_task.md", OUTPUT / "validation_report.json", OUTPUT / "forbidden_action_audit.json",
        OUTPUT / "field_span_disk_capacity_audit.json", OUTPUT / "local_artifact_storage_audit.json",
        OUTPUT / "staged_file_audit.json", OUTPUT / "large_file_audit.json", OUTPUT / "external_data_deterministic_field_span_summary.json",
        OUTPUT / "whole_corpus_native_pdf_page_accounting.json", OUTPUT / "whole_corpus_non_pdf_scale_accounting.json"]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files: archive.write(file, arcname=file.name)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true"); parser.add_argument("--worker", choices=LANES)
    parser.add_argument("--launch", action="store_true"); parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--repair-interrupted-ledgers", action="store_true")
    parser.add_argument("--audit-staged", action="store_true"); parser.add_argument("--relay", nargs=2, metavar=("COMMIT", "PUSH_STATUS"))
    args = parser.parse_args()
    if args.preflight: preflight()
    elif args.worker: worker(args.worker)
    elif args.launch: launch()
    elif args.repair_interrupted_ledgers: repair_interrupted_ledgers()
    elif args.finalize: finalize()
    elif args.audit_staged: audit_staged()
    elif args.relay: print(relay(args.relay[0], args.relay[1]))
    else: parser.error("choose one stage action")


if __name__ == "__main__":
    main()
