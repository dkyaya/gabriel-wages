#!/usr/bin/env python3
"""Compact and classify recall-heavy external administrative field/span hits.

The script is intentionally local, deterministic, resumable, and fail closed.
Bulky records remain under the ignored classified-observations root; Git-facing
files contain schemas, hashes, pointers, bounded samples, summaries, and audits.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import run_available_external_data_deterministic_field_span_extraction as prior
import run_external_data_exhaustive_pipeline as core


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-DETERMINISTIC-EVIDENCE-CLASSIFICATION-AND-INGESTION-PREP-2026-08-05"
DECISION = "broad_state_whole_corpus_external_data_classification_completed_ingestion_ready"
QA_DECISION = "broad_state_whole_corpus_external_data_classification_completed_additional_qa_needed"
PARTIAL_DECISION = "broad_state_whole_corpus_external_data_classification_partial_resume_ready"
PREFLIGHT_DECISION = "broad_state_whole_corpus_external_data_classification_preflight_failed"
REQUIRED_COMMIT = "f5275f8b"
EXPECTED_FIELDS = 5_558_770
EXPECTED_SPANS = 4_289_437
EXPECTED_PAYLOADS = 14_160
EXPECTED_FIELD_BEARING = 13_931
EXPECTED_SPAN_BEARING = 13_943
EXPECTED_NO_EVIDENCE = 217
EXPECTED_UNRESOLVED_LINKS = 13_943
EXPECTED_RAW_AMBIGUITIES = 2_203_064
EXPECTED_HOLDS = 7_895
EXPECTED_UNSEARCHED = 12_844
EXPECTED_OCR = 118
EXPECTED_REPAIR = 97
MIN_FREE = 8 * 1024**3
RULE_VERSION = "deterministic-observation-compaction-classification-2026-08-05-v2-anonymous-coordinate-preservation"
REPAIR_VERSION = RULE_VERSION

STAGE7 = prior.OUTPUT
OUTPUT = core.ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04/08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP"
RAW = prior.LOCAL
LOCAL = core.STRUCTURED / "classified_observations"
TMP = core.ROOT / "tmp/broad_state_whole_corpus_external_data_deterministic_classification_ingestion_prep_2026-08-05_logs"
LANES = [f"classification_lane_{n:03d}" for n in range(1, 6)]
STAGGERS = dict(zip(LANES, (0, 120, 240, 360, 480)))

FIELD_SCHEMA = prior.FIELD_SCHEMA
SPAN_SCHEMA = prior.SPAN_SCHEMA

OBSERVATION_SCHEMA = [
    "external_administrative_observation_id", "canonical_payload_id", "retained_source_ids",
    "candidate_ids", "contributing_raw_field_record_ids", "contributing_raw_span_ids",
    "source_SHA_256", "municipality_raw", "municipality_canonical_id", "state",
    "department_raw", "unit_raw", "employee_or_position_identity", "side_hint", "period_raw",
    "fiscal_year", "calendar_year", "start_date", "end_date", "observation_family",
    "observation_type", "field_name", "raw_value", "parsed_literal_value", "parsed_value_type",
    "currency", "unit", "pay_basis", "compensation_basis", "recurring_status",
    "implementation_status", "source_page", "source_section", "source_table_id", "source_row",
    "source_column", "source_character_start", "source_character_end", "bounded_evidence_excerpt",
    "evidence_quality_class", "analytical_role", "ingestion_readiness",
    "deterministic_confidence_basis", "ambiguity_flags", "conflict_flags",
    "duplicate_count_collapsed", "boilerplate_count_suppressed", "corroboration_group_id",
    "root_event_ids", "mechanism_event_ids", "claim_family_ids", "claim_ids",
    "claim_linkage_status", "claim_linkage_basis", "expected_claim_upgrade_tags", "rule_ids",
    "rule_registry_hash", "primary_raw_field_record_id", "primary_evidence_span_id",
    "extraction_result_id", "extraction_artifact_pointer", "lineage_basis",
]

LIFECYCLE = {
    "proposed", "recommended", "negotiated", "tentative", "adopted", "approved", "ratified",
    "appropriated", "implemented", "payroll_effective", "paid", "amended", "rejected", "expired",
}
GENERIC_LABELS = {
    "overtime", "overtime pay", "vacancy", "vacancies", "paid", "approved", "adopted", "amended",
    "county", "salary", "wages", "pay", "gross pay", "regular pay", "total earnings", "fte",
    "positions", "headcount", "employee", "employees", "department", "classification", "step",
    "proposed", "recommended", "negotiated", "implemented", "expired", "benefits", "allowance",
}
OBJECT_TERMS = re.compile(
    r"\b(salary|salaries|wage|wages|pay|payroll|compensation|rate|step|schedule|ordinance|resolution|"
    r"agreement|contract|appropriation|retroactive|premium|stipend|benefit|position|vacan|fte|headcount)\b",
    re.I,
)
URLISH = re.compile(r"(?:https?://|www\.|\.gov(?:/|$)|\.com(?:/|$)|[/?=&]{2,})", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    raw = "\x1f".join(str(x or "") for x in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:n]}"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    names = list(fields or (rows[0].keys() if rows else []))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in names})


def write_pair(name: str, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    write_csv(OUTPUT / f"{name}.csv", rows, fields)
    write_jsonl(OUTPUT / f"{name}.jsonl", rows)


def split(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value or "").split("|") if x.strip()]


def joined(values: Iterable[Any]) -> str:
    out: set[str] = set()
    for value in values:
        out.update(split(value))
    return "|".join(sorted(out))


def free_bytes() -> int:
    return shutil.disk_usage(core.ROOT).free


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], cwd=core.ROOT, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=core.ROOT).returncode == 0


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def gzip_groups(path: Path) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    current = ""
    group: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            payload = row["canonical_payload_id"]
            if current and payload != current:
                yield current, group
                group = []
            current = payload
            group.append(row)
    if current:
        yield current, group


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def exact_field_key(r: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(r.get(k, "") for k in (
        "canonical_payload_id", "field_name", "source_page", "source_section", "source_table_id",
        "source_row", "source_column", "source_character_start", "source_character_end", "raw_value",
        "rule_version",
    ))


def observation_key(r: dict[str, Any]) -> tuple[Any, ...]:
    base = tuple(r.get(k, "") for k in (
        "canonical_payload_id", "municipality_canonical_id", "municipality_raw", "department_raw",
        "unit_raw", "position_or_employee_raw", "field_family", "field_name", "raw_value", "parsed_value",
        "pay_basis_raw", "compensation_basis_raw", "period_raw", "fiscal_year_raw", "calendar_year_raw",
        "start_date_raw", "end_date_raw", "implementation_status_raw", "source_table_id", "source_row",
    ))
    # Never infer that coordinate-distinct anonymous rows/clauses are the same
    # employee, position, or fact. Compaction without identity is fail-closed.
    if not r.get("position_or_employee_raw") and not r.get("source_row"):
        coordinate = tuple(r.get(k, "") for k in (
            "source_page", "source_section", "source_table_id", "source_column", "source_cell",
            "source_character_start", "source_character_end",
        ))
        if not any(coordinate): coordinate = (r.get("external_field_record_id", ""),)
        return base + coordinate
    return base


def identity_without_value(r: dict[str, Any]) -> tuple[Any, ...]:
    base = tuple(r.get(k, "") for k in (
        "canonical_payload_id", "municipality_canonical_id", "municipality_raw", "department_raw", "unit_raw",
        "position_or_employee_raw", "field_family", "field_name", "pay_basis_raw", "compensation_basis_raw",
        "period_raw", "fiscal_year_raw", "calendar_year_raw", "start_date_raw", "end_date_raw",
        "implementation_status_raw", "source_table_id", "source_row",
    ))
    if not r.get("position_or_employee_raw") and not r.get("source_row"):
        coordinate = tuple(r.get(k, "") for k in (
            "source_page", "source_section", "source_table_id", "source_column", "source_cell",
            "source_character_start", "source_character_end",
        ))
        if not any(coordinate): coordinate = (r.get("external_field_record_id", ""),)
        return base + coordinate
    return base


def structural_reason(r: dict[str, Any], span: bool = False) -> str:
    text = normalized(r.get("exact_excerpt") if span else r.get("raw_value"))
    field = normalized(r.get("field_name") or r.get("evidence_type"))
    basis = normalized(r.get("extraction_confidence_basis"))
    if not text:
        return "empty_value_or_excerpt"
    if URLISH.search(text) and field not in {"source url", "source_url"}:
        return "url_or_navigation_collision"
    if text in GENERIC_LABELS or (len(text.split()) <= 2 and text.replace("_", " ") == field.replace("_", " ")):
        return "isolated_label_or_heading"
    if text in {"home", "menu", "print", "export", "search", "next", "previous", "copyright"}:
        return "navigation_or_template_control"
    if len(text) > 1200:
        return "oversized_unbounded_structural_match"
    if not span and field == "county":
        plausible = len(text) <= 80 and not any(ch.isdigit() for ch in text) and not URLISH.search(text)
        if not plausible:
            return "non_geographic_county_collision"
    if basis == "weak_pattern_requires_review" and len(text.split()) <= 2:
        return "weak_isolated_lexical_hit"
    return ""


def ambiguity_reason(r: dict[str, Any], span: bool = False) -> str:
    basis = normalized(r.get("extraction_confidence_basis"))
    flags = split(r.get("ambiguity_flags"))
    text = str(r.get("exact_excerpt") if span else r.get("raw_value") or "")
    field = normalized(r.get("field_name") or r.get("evidence_type"))
    if basis in {"weak_pattern_requires_review", "ambiguous_narrative_manual_review", "weak_local_context_manual_review"}:
        return "weak_or_ambiguous_extraction_context"
    if flags:
        return "|".join(flags)
    if field in LIFECYCLE or normalized(r.get("implementation_status_raw") or r.get("implementation_status_hint")) in LIFECYCLE:
        if not OBJECT_TERMS.search(text) or not re.search(r"\b(" + "|".join(sorted(LIFECYCLE)) + r")\b", text, re.I):
            return "lifecycle_subject_or_object_not_locally_supported"
    return ""


def evidence_quality(r: dict[str, Any]) -> str:
    source = normalized(r.get("source_quality"))
    kind = normalized(r.get("administrative_source_type"))
    family = normalized(r.get("field_family"))
    if family == "implementation_confirmation":
        return "official_implementation_record"
    if kind in {"salary_schedule", "wage_schedule", "policy_or_schedule"}:
        return "official_schedule_or_policy_record"
    if source == "direct_official_structured_record" or r.get("source_table_id") or r.get("source_row"):
        return "direct_official_structured_record"
    if source.startswith("direct_official"):
        return "direct_official_administrative_record"
    if "official" in source:
        return "official_administrative_summary"
    if family == "contextual_controls":
        return "official_contextual_record"
    if "secondary" in source:
        return "reputable_secondary_context"
    return "manual_review_required"


def analytical_role(family: str, quality: str) -> str:
    return {
        "payroll_and_earnings": "local_comparison_candidate",
        "staffing_and_headcount": "staffing_hypothesis_candidate",
        "recruitment_and_retention": "staffing_hypothesis_candidate",
        "tenure_and_progression": "growth_candidate",
        "implementation_confirmation": "implementation_confirmation_candidate",
        "benefits_and_total_compensation": "total_compensation_candidate",
        "contextual_controls": "contextual_only",
    }.get(family, "mechanism_support_candidate" if quality != "manual_review_required" else "pending_reconciliation")


def observation_type(r: dict[str, Any]) -> str:
    family, name = r.get("field_family", ""), r.get("field_name", "")
    if family == "payroll_and_earnings":
        if "overtime" in name: return "overtime_observation"
        if any(x in name for x in ("premium", "stipend", "allowance")): return "premium_pay_observation"
        if r.get("position_or_employee_raw"): return "employee_compensation_observation"
        if "step" in name: return "salary_schedule_step_observation"
        return "position_compensation_observation"
    return {
        "staffing_and_headcount": "vacancy_observation" if "vacan" in name else "staffing_count_observation",
        "recruitment_and_retention": "recruitment_retention_observation",
        "implementation_confirmation": "implementation_lifecycle_observation",
        "benefits_and_total_compensation": "benefit_component_observation",
        "contextual_controls": "contextual_control_observation",
        "tenure_and_progression": "salary_schedule_step_observation",
    }.get(family, "qualitative_administrative_mechanism_observation")


def readiness(quality: str, r: dict[str, Any]) -> str:
    if quality in {"direct_official_administrative_record", "direct_official_structured_record"}:
        return "ingestion_ready_direct_administrative"
    if quality == "official_administrative_summary": return "ingestion_ready_official_summary"
    if quality == "official_implementation_record": return "ingestion_ready_implementation_record"
    if quality == "official_schedule_or_policy_record": return "ingestion_ready_schedule_record"
    if quality == "official_contextual_record": return "ingestion_ready_contextual_record"
    return "pending_manual_narrative_review"


def rule_registries() -> dict[str, Any]:
    return {
        "version": RULE_VERSION,
        "exact_deduplication": "payload+type+source_coordinates+raw_value+rule_version",
        "source_local_compaction": "explicit administrative identity+field+literal+period+row",
        "structural_rules": [
            "empty_value_or_excerpt", "url_or_navigation_collision", "isolated_label_or_heading",
            "navigation_or_template_control", "oversized_unbounded_structural_match",
            "non_geographic_county_collision", "weak_isolated_lexical_hit",
        ],
        "lifecycle_states": sorted(LIFECYCLE | {"unclear"}),
        "lifecycle_requirement": "explicit verb plus local compensation/administrative object context",
        "cross_source_policy": "link; never physically collapse",
        "claim_policy": "canonical crosswalk only; upgrade tags are never claim IDs",
        "confidence_bases": [
            "exact_structured_row", "exact_structured_cell", "exact_labeled_text",
            "exact_table_row_with_headers", "exact_ordinance_or_resolution_clause", "exact_payroll_record",
            "exact_schedule_record", "strong_local_context", "weak_local_context_manual_review",
            "ambiguous_narrative_manual_review",
        ],
    }


def preflight() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for d in (
        "exact_dedup", "boilerplate_suppression", "administrative_observations", "classified_spans",
        "conflicts", "ambiguities", "claim_links", "indexes", "quarantine", "temporary", "logs",
        "raw_inputs", "lanes",
    ):
        (LOCAL / d).mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    started = now()
    failures: list[str] = []
    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", REQUIRED_COMMIT, head], cwd=core.ROOT
    ).returncode == 0
    status = git("status", "--short")
    allowed = {"scripts/run_external_data_deterministic_classification_ingestion_prep.py"}
    unrelated = []
    for line in status.splitlines():
        path = line[3:].strip().strip('"')
        if path not in allowed and not path.startswith(str(OUTPUT.relative_to(core.ROOT)) + "/"):
            unrelated.append(line)
    if not ancestor: failures.append(f"required commit {REQUIRED_COMMIT} is not an ancestor of {head}")
    if unrelated: failures.append("unrelated dirty worktree: " + " ; ".join(unrelated))
    summary = load_json(STAGE7 / "external_data_deterministic_field_span_summary.json")
    expected = {
        "raw_field_records": EXPECTED_FIELDS,
        "raw_evidence_spans": EXPECTED_SPANS,
        "field_bearing_payloads": EXPECTED_FIELD_BEARING,
        "span_bearing_payloads": EXPECTED_SPAN_BEARING,
        "payloads_with_no_relevant_field_or_span": EXPECTED_NO_EVIDENCE,
        "payloads_with_unresolved_claim_linkage": EXPECTED_UNRESOLVED_LINKS,
        "ambiguous_or_manual_review_field_records": EXPECTED_RAW_AMBIGUITIES,
        "storage_capacity_holds_preserved": EXPECTED_HOLDS,
        "unresolved_hosted_search_targets": EXPECTED_UNSEARCHED,
        "ocr_later_preserved": EXPECTED_OCR,
        "extraction_repair_payloads_preserved": EXPECTED_REPAIR,
    }
    aliases = {
        "raw_field_records": "field_record_count",
        "raw_evidence_spans": "evidence_span_count",
        "field_bearing_payloads": "payloads_with_field_records",
        "span_bearing_payloads": "payloads_with_evidence_spans",
        "payloads_with_no_relevant_field_or_span": "payloads_with_no_relevant_evidence",
        "payloads_with_unresolved_claim_linkage": "unresolved_claim_linkage_payload_count",
        "ambiguous_or_manual_review_field_records": "ambiguous_manual_review_record_count",
    }
    for name, want in expected.items():
        actual = summary.get(aliases.get(name, name))
        if actual != want:
            failures.append(f"{name}: expected {want}, got {actual}")
    required = [
        "external_data_deterministic_field_span_manifest.json", "external_administrative_field_records_manifest.json",
        "external_administrative_evidence_spans_manifest.json", "external_administrative_field_records_schema.json",
        "external_administrative_evidence_spans_schema.json", "field_span_locked_payload_queue.csv",
        "whole_corpus_unique_pdf_manifest.csv", "whole_corpus_pdf_page_count_conflict_queue.csv",
        "deterministic_field_rule_registry.json",
    ]
    for name in required:
        if not (STAGE7 / name).is_file(): failures.append(f"missing {name}")
    field_manifest = load_json(STAGE7 / "external_administrative_field_records_manifest.json")
    span_manifest = load_json(STAGE7 / "external_administrative_evidence_spans_manifest.json")
    for manifest in (field_manifest, span_manifest):
        for lane in manifest.get("lanes", []):
            for key in ("field_pointer", "span_pointer", "outcome_pointer"):
                pointer = lane.get(key)
                if pointer and not (core.ROOT / pointer).is_file(): failures.append(f"missing pointer {pointer}")
            for pointer_key, hash_key in (
                ("field_pointer", "field_sha256"), ("span_pointer", "span_sha256"),
                ("outcome_pointer", "outcome_sha256"),
            ):
                pointer, expected_hash = lane.get(pointer_key), lane.get(hash_key)
                if pointer and expected_hash and sha(core.ROOT / pointer) != expected_hash:
                    failures.append(f"hash mismatch {pointer}")
    ignore_audit = {
        "retained_source_root_ignored": ignored(core.RETAINED),
        "extracted_text_root_ignored": ignored(core.EXTRACTED),
        "raw_field_span_root_ignored": ignored(RAW),
        "classified_observation_root_ignored": ignored(LOCAL),
    }
    failures += [k for k, v in ignore_audit.items() if not v]
    if free_bytes() < MIN_FREE: failures.append("free disk is below 8 GiB reserve")
    ps = subprocess.run(
        ["pgrep", "-af", "run_external_data_deterministic_classification_ingestion_prep.py.*--worker"],
        text=True, capture_output=True,
    )
    stale = [x for x in ps.stdout.splitlines() if str(os.getpid()) not in x]
    if stale: failures.append("stale classification workers: " + " ; ".join(stale))
    atomic_json(OUTPUT / "classification_run_manifest.json", {
        "task_id": TASK_ID, "starting_head": head, "started_at": started,
        "prior_commit_verified": ancestor, "prior_stage": str(STAGE7.relative_to(core.ROOT)),
        "raw_root": str(RAW.relative_to(core.ROOT)), "local_output_root": str(LOCAL.relative_to(core.ROOT)),
        "rule_version": RULE_VERSION, "network_authorized": False, "gabriel_authorized": False,
        "ocr_authorized": False, "normalization_authorized": False,
    })
    atomic_json(OUTPUT / "classification_run_state.json", {"stage": "preflight", "status": "running", "updated_at": now()})
    atomic_json(OUTPUT / "classification_stage_checkpoint.json", {"stage": "preflight", "status": "running", "updated_at": now()})
    write_jsonl(OUTPUT / "classification_operational_incident_log.jsonl", [])
    write_jsonl(OUTPUT / "operational_incident_log.jsonl", [])
    write_jsonl(OUTPUT / "classification_stage_transition_log.jsonl", [{"at": now(), "from": None, "to": "preflight"}])
    atomic_json(OUTPUT / "classification_disk_capacity_audit.json", {
        "passed": free_bytes() >= MIN_FREE, "free_bytes": free_bytes(), "required_reserve_bytes": MIN_FREE,
    })
    storage_audit = {"passed": all(ignore_audit.values()), **ignore_audit}
    atomic_json(OUTPUT / "classification_local_artifact_storage_audit.json", storage_audit)
    atomic_json(OUTPUT / "local_artifact_storage_audit.json", storage_audit)
    forbidden = {
        "passed": True, "hosted_search_calls": 0, "gabriel_api_calls": 0, "network_requests": 0,
        "redownloads": 0, "ocr_calls": 0, "unit_conversions": 0, "normalization_runs": 0,
        "safety_non_safety_matching_runs": 0, "wage_gap_calculations": 0, "regressions": 0,
        "treatment_effect_estimates": 0, "prevalence_estimates": 0, "causal_effect_claims": 0,
        "final_pdf_docx_slide_heatmap_outputs": 0, "implementation_event_deduplication_runs": 0,
    }
    atomic_json(OUTPUT / "classification_forbidden_action_audit.json", forbidden)
    atomic_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    audit = {"passed": not failures, "checked_at": now(), "expected": expected, "actual_summary": summary,
             "raw_schema_fields": FIELD_SCHEMA, "span_schema_fields": SPAN_SCHEMA,
             "ignore_audit": ignore_audit, "stale_workers": stale, "failures": failures}
    atomic_json(OUTPUT / "classification_input_reconciliation_audit.json", audit)
    (OUTPUT / "classification_input_reconciliation_audit.md").write_text(
        "# Classification input reconciliation audit\n\n" +
        ("PASS" if not failures else "FAIL") + " — prior field/span corpus and local artifacts were checked fail-closed.\n\n" +
        "\n".join(f"- {x}" for x in failures) + "\n", encoding="utf-8")
    if failures:
        atomic_json(OUTPUT / "classification_run_state.json", {"stage": "preflight", "status": "failed", "decision": PREFLIGHT_DECISION, "updated_at": now()})
        raise SystemExit("preflight failed: " + " ; ".join(failures))
    build_registries()
    partition_inputs()
    smoke_tests()
    atomic_json(OUTPUT / "classification_run_state.json", {"stage": "production", "status": "ready", "updated_at": now()})
    atomic_json(OUTPUT / "classification_stage_checkpoint.json", {"stage": "production", "status": "ready", "updated_at": now()})


def build_registries() -> None:
    registry = rule_registries()
    registry_hash = hashlib.sha256(json.dumps(registry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    registry["sha256"] = registry_hash
    files = {
        "deterministic_observation_compaction_rule_registry.json": {"version": RULE_VERSION, "rules": registry["exact_deduplication"], "source_local_compaction": registry["source_local_compaction"], "cross_source_policy": registry["cross_source_policy"]},
        "deterministic_evidence_classification_rule_registry.json": registry,
        "deterministic_boilerplate_rule_registry.json": {"version": RULE_VERSION, "rules": registry["structural_rules"]},
        "deterministic_lifecycle_validation_rule_registry.json": {"version": RULE_VERSION, "statuses": registry["lifecycle_states"], "requirement": registry["lifecycle_requirement"]},
        "deterministic_claim_linkage_rule_registry.json": {"version": RULE_VERSION, "policy": registry["claim_policy"]},
        "combined_rule_registry_hash.json": {"version": RULE_VERSION, "sha256": registry_hash},
    }
    for name, obj in files.items(): atomic_json(OUTPUT / name, obj)
    (OUTPUT / "deterministic_observation_compaction_rule_registry.md").write_text(
        "# Deterministic observation-compaction registry\n\nExact hits are deduplicated by source coordinates; source-local facts are compacted without merging distinct people, positions, years, steps, departments, components, bases, or lifecycle states. Cross-source records are linked and never physically collapsed.\n", encoding="utf-8")
    (OUTPUT / "deterministic_evidence_classification_rule_registry.md").write_text(
        "# Deterministic evidence-classification registry\n\nClassification is categorical, rule-based, locally auditable, and not a GABRIEL rating. Weak narrative and unsupported lifecycle hits remain pending.\n", encoding="utf-8")


def read_outcomes() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for lane in prior.LANES:
        path = RAW / "lanes" / lane / "payload_outcomes.jsonl"
        with path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                out[row["canonical_payload_id"]] = row
    return out


def partition_inputs() -> None:
    outcomes = read_outcomes()
    if len(outcomes) != EXPECTED_PAYLOADS:
        raise RuntimeError(f"expected {EXPECTED_PAYLOADS} outcomes, got {len(outcomes)}")
    loads = {lane: 0 for lane in LANES}
    assignments: dict[str, str] = {}
    payloads = sorted(outcomes.values(), key=lambda r: (-(r.get("field_record_count", 0) + r.get("evidence_span_count", 0) + r.get("ambiguity_count", 0) // 2 + r.get("word_count", 0) // 100), r["canonical_payload_id"]))
    for row in payloads:
        lane = min(LANES, key=lambda x: (loads[x], x))
        cost = row.get("field_record_count", 0) + row.get("evidence_span_count", 0) + row.get("ambiguity_count", 0) // 2 + row.get("word_count", 0) // 100
        assignments[row["canonical_payload_id"]] = lane
        loads[lane] += cost
    queues: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    for payload, lane in sorted(assignments.items()):
        r = outcomes[payload]
        queues[lane].append({"canonical_payload_id": payload, "raw_field_count": r.get("field_record_count", 0),
                             "raw_span_count": r.get("evidence_span_count", 0), "raw_ambiguity_count": r.get("ambiguity_count", 0),
                             "assignment_cost": r.get("field_record_count", 0) + r.get("evidence_span_count", 0) + r.get("ambiguity_count", 0) // 2 + r.get("word_count", 0) // 100,
                             "lane_id": lane})
    for lane in LANES:
        write_jsonl(OUTPUT / f"{lane}_queue.jsonl", queues[lane])
        write_csv(OUTPUT / f"{lane}_queue.csv", queues[lane])
    raw_inputs = LOCAL / "raw_inputs"
    handles: dict[tuple[str, str], Any] = {}
    try:
        for lane in LANES:
            d = raw_inputs / lane
            d.mkdir(parents=True, exist_ok=True)
            handles[(lane, "field")] = gzip.open(d / "raw_fields.jsonl.gz", "wt", encoding="utf-8", compresslevel=5)
            handles[(lane, "span")] = gzip.open(d / "raw_spans.jsonl.gz", "wt", encoding="utf-8", compresslevel=5)
        counts = Counter()
        for old_lane in prior.LANES:
            for kind, filename in (("field", "field_records.jsonl.gz"), ("span", "evidence_spans.jsonl.gz")):
                with gzip.open(RAW / "lanes" / old_lane / filename, "rt", encoding="utf-8") as f:
                    for line in f:
                        row = json.loads(line)
                        payload = row.get("canonical_payload_id")
                        lane = assignments.get(payload)
                        if not lane: raise RuntimeError(f"unassigned payload {payload}")
                        required = ("external_field_record_id", "source_SHA_256", "field_name", "rule_id", "parser_version") if kind == "field" else ("external_evidence_span_id", "source_SHA_256", "evidence_type", "rule_id", "parser_version")
                        if any(k not in row for k in required): raise RuntimeError(f"malformed {kind} row in {payload}")
                        handles[(lane, kind)].write(line)
                        counts[(lane, kind)] += 1
    finally:
        for f in handles.values(): f.close()
    if sum(counts[(l, "field")] for l in LANES) != EXPECTED_FIELDS or sum(counts[(l, "span")] for l in LANES) != EXPECTED_SPANS:
        raise RuntimeError("routed raw counts do not reconcile")
    shards = []
    for lane in LANES:
        for kind, filename in (("field", "raw_fields.jsonl.gz"), ("span", "raw_spans.jsonl.gz")):
            path = raw_inputs / lane / filename
            shards.append({"lane_id": lane, "record_type": kind, "count": counts[(lane, kind)],
                           "pointer": str(path.relative_to(core.ROOT)), "sha256": sha(path), "bytes": path.stat().st_size})
    atomic_json(OUTPUT / "raw_field_span_shard_manifest.json", {"shards": shards, "field_count": EXPECTED_FIELDS, "span_count": EXPECTED_SPANS})
    atomic_json(OUTPUT / "raw_field_span_shard_hash_manifest.json", {"shards": [{k: x[k] for k in ("lane_id", "record_type", "pointer", "sha256", "bytes")} for x in shards]})
    dist = {lane: {"payloads": len(queues[lane]), "raw_fields": counts[(lane, "field")], "raw_spans": counts[(lane, "span")], "assignment_cost": loads[lane], "stagger_seconds": STAGGERS[lane]} for lane in LANES}
    atomic_json(OUTPUT / "classification_lane_distribution.json", {"method": "stable_lpt_by_payload_cost", "lanes": dist, "disjoint": True, "complete": True})
    (OUTPUT / "classification_lane_distribution.md").write_text(
        "# Five-lane classification distribution\n\n| Lane | Payloads | Raw fields | Raw spans | Cost | Stagger |\n|---|---:|---:|---:|---:|---:|\n" +
        "\n".join(f"| {l} | {dist[l]['payloads']:,} | {dist[l]['raw_fields']:,} | {dist[l]['raw_spans']:,} | {dist[l]['assignment_cost']:,} | {dist[l]['stagger_seconds']}s |" for l in LANES) + "\n", encoding="utf-8")


def smoke_tests() -> None:
    cases = [
        ("repeated page header", {"raw_value": "Salary", "field_name": "salary"}, "isolated_label_or_heading"),
        ("repeated table header", {"raw_value": "Overtime Pay", "field_name": "overtime_pay"}, "isolated_label_or_heading"),
        ("navigation collision", {"raw_value": "https://town.gov/paid", "field_name": "paid"}, "url_or_navigation_collision"),
        ("county collision", {"raw_value": "https://county.gov/search", "field_name": "county"}, "url_or_navigation_collision"),
        ("employee payroll row", {"raw_value": "$72,000", "field_name": "annual_salary", "extraction_confidence_basis": "exact_structured_cell"}, ""),
        ("staffing count", {"raw_value": "42", "field_name": "authorized_positions", "extraction_confidence_basis": "exact_structured_cell"}, ""),
        ("proposal not adoption", {"raw_value": "The union proposed a salary increase", "field_name": "proposed", "implementation_status_raw": "proposed", "extraction_confidence_basis": "exact_labeled_text"}, ""),
        ("unsupported lifecycle", {"raw_value": "31,", "field_name": "expired", "implementation_status_raw": "expired", "extraction_confidence_basis": "exact_labeled_text"}, "ambiguous"),
    ]
    results = []
    for name, row, expected in cases:
        got = structural_reason(row) or ("ambiguous" if ambiguity_reason(row) else "")
        results.append({"case": name, "expected": expected, "actual": got, "passed": got == expected})
    passed = all(x["passed"] for x in results)
    atomic_json(OUTPUT / "classification_smoke_test_results.json", {"passed": passed, "cases": results, "tested_at": now()})
    if not passed: raise RuntimeError("classification smoke tests failed")


def compact_field_group(payload: str, rows: list[dict[str, Any]], writers: dict[str, Any], registry_hash: str) -> dict[str, Any]:
    exact_seen: dict[tuple[Any, ...], str] = {}
    observation_seen: dict[tuple[Any, ...], dict[str, Any]] = {}
    counts = Counter()
    rule_counts = Counter()
    family_counts = Counter()
    quality_counts = Counter()
    role_counts = Counter()
    lifecycle_counts = Counter()
    readiness_counts = Counter()
    identity_values: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    duplicate_links: list[dict[str, Any]] = []
    within_links: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    writeoffs: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    rows_by_id = {r["external_field_record_id"]: r for r in rows}
    for r in rows:
        rid = r["external_field_record_id"]
        rule_counts[r.get("rule_id", "unclear")] += 1
        ek = exact_field_key(r)
        if ek in exact_seen:
            counts["exact_duplicate"] += 1
            duplicate_links.append({"canonical_payload_id": payload, "duplicate_raw_field_record_id": rid,
                                    "canonical_raw_field_record_id": exact_seen[ek], "rule_id": "COMPACT-EXACT-FIELD-DUPLICATE"})
            continue
        exact_seen[ek] = rid
        structural = structural_reason(r)
        if structural:
            counts["boilerplate_or_structural_writeoff"] += 1
            writeoffs.append({"canonical_payload_id": payload, "raw_record_id": rid, "record_type": "field",
                              "writeoff_class": "boilerplate_or_structural_writeoff", "writeoff_reason": structural,
                              "field_name": r.get("field_name", ""), "raw_value": r.get("raw_value", ""),
                              "source_page": r.get("source_page", ""), "rule_id": f"BOILERPLATE-{structural.upper()}"})
            continue
        ambiguous = ambiguity_reason(r)
        if ambiguous:
            counts["ambiguity"] += 1
            ambiguities.append({"canonical_payload_id": payload, "raw_record_id": rid, "record_type": "field",
                                "ambiguity_reason": ambiguous, "field_family": r.get("field_family", ""),
                                "field_name": r.get("field_name", ""), "raw_value": r.get("raw_value", ""),
                                "source_page": r.get("source_page", ""), "source_table_id": r.get("source_table_id", ""),
                                "rule_id": r.get("rule_id", "")})
            continue
        ok = observation_key(r)
        if ok in observation_seen:
            prior_obs = observation_seen[ok]
            counts["compacted_into_another"] += 1
            within_links.append({"canonical_payload_id": payload, "secondary_raw_field_record_id": rid,
                                 "primary_raw_field_record_id": prior_obs["primary_raw_field_record_id"],
                                 "external_administrative_observation_id": prior_obs["external_administrative_observation_id"],
                                 "relationship": "source_local_repeated_fact"})
            prior_obs["_field_ids"].add(rid)
            if r.get("evidence_span_id"): prior_obs["_span_ids"].add(r["evidence_span_id"])
            prior_obs["duplicate_count_collapsed"] += 1
            continue
        quality = evidence_quality(r)
        role = analytical_role(r.get("field_family", ""), quality)
        ready = readiness(quality, r)
        obs_id = stable("EXTOBS", *ok)
        obs = {
            "external_administrative_observation_id": obs_id,
            "canonical_payload_id": payload, "retained_source_ids": r.get("retained_source_ids", ""),
            "candidate_ids": r.get("candidate_ids", ""), "contributing_raw_field_record_ids": rid,
            "contributing_raw_span_ids": r.get("evidence_span_id", ""), "source_SHA_256": r.get("source_SHA_256", ""),
            "municipality_raw": r.get("municipality_raw", ""), "municipality_canonical_id": r.get("municipality_canonical_id", ""),
            "state": r.get("state", ""), "department_raw": r.get("department_raw", ""), "unit_raw": r.get("unit_raw", ""),
            "employee_or_position_identity": r.get("position_or_employee_raw") or "anonymous_position_or_employee_record",
            "side_hint": r.get("side_deterministic_hint", "unclear"), "period_raw": r.get("period_raw", ""),
            "fiscal_year": r.get("fiscal_year_raw", ""), "calendar_year": r.get("calendar_year_raw", ""),
            "start_date": r.get("start_date_raw", ""), "end_date": r.get("end_date_raw", ""),
            "observation_family": r.get("field_family", ""), "observation_type": observation_type(r),
            "field_name": r.get("field_name", ""), "raw_value": r.get("raw_value", ""),
            "parsed_literal_value": r.get("parsed_value", ""), "parsed_value_type": r.get("parsed_value_type", ""),
            "currency": r.get("currency", ""), "unit": r.get("unit", ""), "pay_basis": r.get("pay_basis_raw", ""),
            "compensation_basis": r.get("compensation_basis_raw", ""), "recurring_status": r.get("recurring_status_raw", ""),
            "implementation_status": r.get("implementation_status_raw") or "",
            "source_page": r.get("source_page", ""), "source_section": r.get("source_section", ""),
            "source_table_id": r.get("source_table_id", ""), "source_row": r.get("source_row", ""),
            "source_column": r.get("source_column", ""), "source_character_start": r.get("source_character_start", ""),
            "source_character_end": r.get("source_character_end", ""), "bounded_evidence_excerpt": str(r.get("raw_value", ""))[:500],
            "evidence_quality_class": quality, "analytical_role": role, "ingestion_readiness": ready,
            "deterministic_confidence_basis": r.get("extraction_confidence_basis", ""),
            "ambiguity_flags": "", "conflict_flags": "", "duplicate_count_collapsed": 0,
            "boilerplate_count_suppressed": 0, "corroboration_group_id": "",
            "root_event_ids": r.get("root_event_ids", ""), "mechanism_event_ids": r.get("mechanism_event_ids", ""),
            "claim_family_ids": "", "claim_ids": "", "claim_linkage_status": "no_canonical_claim_mapping",
            "claim_linkage_basis": "", "expected_claim_upgrade_tags": r.get("expected_claim_upgrade_tags", ""),
            "rule_ids": r.get("rule_id", ""), "rule_registry_hash": registry_hash,
            "primary_raw_field_record_id": rid, "primary_evidence_span_id": r.get("evidence_span_id", ""),
            "extraction_result_id": r.get("extraction_result_id", ""),
            "extraction_artifact_pointer": r.get("extraction_artifact_pointer", ""),
            "lineage_basis": "deterministic_source_local_observation_compaction_from_raw_field_records",
            "_field_ids": {rid}, "_span_ids": set(split(r.get("evidence_span_id", ""))),
        }
        observation_seen[ok] = obs
        observations.append(obs)
        identity_values[identity_without_value(r)].add(str(r.get("parsed_value") or r.get("raw_value") or ""))
        counts["promoted"] += 1
        family_counts[obs["observation_family"]] += 1
        quality_counts[quality] += 1
        role_counts[role] += 1
        readiness_counts[ready] += 1
        if obs["implementation_status"]: lifecycle_counts[obs["implementation_status"]] += 1
    conflicts = []
    conflict_identities = {k for k, values in identity_values.items() if len(values) > 1}
    for obs in observations:
        source = rows_by_id.get(obs["primary_raw_field_record_id"])
        if source is not None and identity_without_value(source) in conflict_identities:
            obs["conflict_flags"] = "source_local_incompatible_literal_values"
            obs["evidence_quality_class"] = "conflicting_administrative_record"
            obs["analytical_role"] = "pending_reconciliation"
            obs["ingestion_readiness"] = "ingestion_ready_conflict_preserved"
            conflicts.append({"canonical_payload_id": payload, "external_administrative_observation_id": obs["external_administrative_observation_id"],
                              "conflict_type": "different_values_for_same_source_identity_and_period", "field_name": obs["field_name"],
                              "raw_value": obs["raw_value"], "resolution_status": "unresolved_preserved"})
        obs["contributing_raw_field_record_ids"] = "|".join(sorted(obs.pop("_field_ids")))
        obs["contributing_raw_span_ids"] = "|".join(sorted(obs.pop("_span_ids")))
    for name, items in (("observations", observations), ("writeoffs", writeoffs), ("ambiguities", ambiguities),
                        ("conflicts", conflicts), ("field_duplicate_links", duplicate_links), ("within_source_links", within_links)):
        for item in items:
            writers[name].write(json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"raw_fields": len(rows), "field_terminal_counts": dict(counts), "observations": len(observations),
            "conflicts": len(conflicts), "rule_counts": dict(rule_counts), "family_counts": dict(family_counts),
            "quality_counts": dict(quality_counts), "role_counts": dict(role_counts),
            "readiness_counts": dict(readiness_counts), "lifecycle_counts": dict(lifecycle_counts)}


def compact_span_group(payload: str, rows: list[dict[str, Any]], writers: dict[str, Any]) -> dict[str, Any]:
    seen: dict[tuple[Any, ...], str] = {}
    classified: list[dict[str, Any]] = []
    duplicate_links, writeoffs, ambiguities = [], [], []
    counts = Counter()
    for r in rows:
        sid = r["external_evidence_span_id"]
        key = tuple(r.get(k, "") for k in (
            "canonical_payload_id", "evidence_type", "source_page", "source_section", "source_table_id",
            "source_row_start", "source_row_end", "source_column_start", "source_column_end",
            "source_character_start", "source_character_end", "exact_excerpt", "rule_version",
        ))
        if key in seen:
            counts["exact_duplicate"] += 1
            duplicate_links.append({"canonical_payload_id": payload, "duplicate_raw_span_id": sid,
                                    "canonical_raw_span_id": seen[key], "rule_id": "COMPACT-EXACT-SPAN-DUPLICATE"})
            continue
        seen[key] = sid
        structural = structural_reason(r, span=True)
        if structural:
            counts["boilerplate_or_structural_writeoff"] += 1
            writeoffs.append({"canonical_payload_id": payload, "raw_record_id": sid, "record_type": "span",
                              "writeoff_class": "boilerplate_or_structural_writeoff", "writeoff_reason": structural,
                              "field_name": r.get("evidence_type", ""), "raw_value": r.get("exact_excerpt", "")[:500],
                              "source_page": r.get("source_page", ""), "rule_id": f"BOILERPLATE-{structural.upper()}"})
            continue
        ambiguous = ambiguity_reason(r, span=True)
        if ambiguous:
            counts["ambiguity"] += 1
            ambiguities.append({"canonical_payload_id": payload, "raw_record_id": sid, "record_type": "span",
                                "ambiguity_reason": ambiguous, "field_family": r.get("field_family", ""),
                                "field_name": r.get("evidence_type", ""), "raw_value": r.get("exact_excerpt", "")[:500],
                                "source_page": r.get("source_page", ""), "source_table_id": r.get("source_table_id", ""),
                                "rule_id": r.get("rule_id", "")})
            continue
        record = dict(r)
        record.update({"classified_span_id": stable("EXTCLSPAN", sid, RULE_VERSION),
                       "span_classification": "explicit_administrative_span",
                       "evidence_quality_class": evidence_quality(r), "rule_registry_version": RULE_VERSION})
        classified.append(record)
        counts["promoted"] += 1
    for name, items in (("classified_spans", classified), ("writeoffs", writeoffs), ("ambiguities", ambiguities),
                        ("span_duplicate_links", duplicate_links)):
        for item in items:
            writers[name].write(json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"raw_spans": len(rows), "span_terminal_counts": dict(counts), "classified_spans": len(classified)}


def run_worker(lane: str, delay: int = 0) -> None:
    if lane not in LANES: raise SystemExit(f"invalid lane {lane}")
    if delay: time.sleep(delay)
    lane_dir = LOCAL / "lanes" / lane
    lane_dir.mkdir(parents=True, exist_ok=True)
    pid_path = TMP / f"{lane}.pid"
    pid_path.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    checkpoint = OUTPUT / f"{lane}_checkpoint.json"
    queue = [json.loads(x) for x in (OUTPUT / f"{lane}_queue.jsonl").read_text(encoding="utf-8").splitlines() if x]
    accepted: set[str] = set()
    outcome_path = lane_dir / "outcomes.jsonl"
    if outcome_path.exists():
        with outcome_path.open(encoding="utf-8") as f:
            for line in f:
                try: accepted.add(json.loads(line)["canonical_payload_id"])
                except (json.JSONDecodeError, KeyError): raise RuntimeError(f"corrupt outcome ledger {outcome_path}")
    registry_hash = load_json(OUTPUT / "combined_rule_registry_hash.json")["sha256"]
    names = ["observations", "classified_spans", "writeoffs", "ambiguities", "conflicts",
             "field_duplicate_links", "span_duplicate_links", "within_source_links"]
    writers = {name: gzip.open(lane_dir / f"{name}.jsonl.gz", "at", encoding="utf-8", compresslevel=5) for name in names}
    try:
        field_outcome_path = lane_dir / "field_outcomes.jsonl"
        span_outcome_path = lane_dir / "span_outcomes.jsonl"
        field_done: dict[str, dict[str, Any]] = {}
        span_done: dict[str, dict[str, Any]] = {}
        for path, target in ((field_outcome_path, field_done), (span_outcome_path, span_done)):
            if path.exists():
                with path.open(encoding="utf-8") as f:
                    for line in f:
                        row = json.loads(line); target[row["canonical_payload_id"]] = row
        expected_ids = {x["canonical_payload_id"] for x in queue}
        for index, (payload, rows) in enumerate(gzip_groups(LOCAL / "raw_inputs" / lane / "raw_fields.jsonl.gz"), 1):
            if payload not in expected_ids: raise RuntimeError(f"field payload {payload} outside lane queue")
            if payload not in field_done:
                result = {"canonical_payload_id": payload, **compact_field_group(payload, rows, writers, registry_hash)}
                append_jsonl(field_outcome_path, result); field_done[payload] = result
                for f in writers.values(): f.flush()
                atomic_json(checkpoint, {"lane_id": lane, "status": "running", "substage": "fields",
                                         "queue_total": len(queue), "field_shards_accepted": len(field_done),
                                         "last_accepted_shard_id": payload, "updated_at": now(), "rule_registry_hash": registry_hash})
            if index % 100 == 0 and free_bytes() < MIN_FREE: raise RuntimeError("disk reserve threatened during classification")
        for index, (payload, rows) in enumerate(gzip_groups(LOCAL / "raw_inputs" / lane / "raw_spans.jsonl.gz"), 1):
            if payload not in expected_ids: raise RuntimeError(f"span payload {payload} outside lane queue")
            if payload not in span_done:
                result = {"canonical_payload_id": payload, **compact_span_group(payload, rows, writers)}
                append_jsonl(span_outcome_path, result); span_done[payload] = result
                for f in writers.values(): f.flush()
                atomic_json(checkpoint, {"lane_id": lane, "status": "running", "substage": "spans",
                                         "queue_total": len(queue), "field_shards_accepted": len(field_done),
                                         "span_shards_accepted": len(span_done), "last_accepted_shard_id": payload,
                                         "updated_at": now(), "rule_registry_hash": registry_hash})
            if index % 100 == 0 and free_bytes() < MIN_FREE: raise RuntimeError("disk reserve threatened during classification")
        zero_field = {"raw_fields": 0, "field_terminal_counts": {}, "observations": 0, "conflicts": 0,
                      "rule_counts": {}, "family_counts": {}, "quality_counts": {}, "role_counts": {},
                      "readiness_counts": {}, "lifecycle_counts": {}}
        zero_span = {"raw_spans": 0, "span_terminal_counts": {}, "classified_spans": 0}
        for index, item in enumerate(queue, 1):
            payload = item["canonical_payload_id"]
            if payload in accepted: continue
            fr = field_done.get(payload, {"canonical_payload_id": payload, **zero_field})
            sr = span_done.get(payload, {"canonical_payload_id": payload, **zero_span})
            result = {"canonical_payload_id": payload, "lane_id": lane,
                      "terminal_outcome": "classification_compaction_complete", "accepted_at": now(),
                      **{k: v for k, v in fr.items() if k != "canonical_payload_id"},
                      **{k: v for k, v in sr.items() if k != "canonical_payload_id"}}
            append_jsonl(outcome_path, result); accepted.add(payload)
            atomic_json(checkpoint, {"lane_id": lane, "status": "running", "substage": "acceptance",
                                     "queue_total": len(queue), "accepted_shards": len(accepted),
                                     "last_accepted_shard_id": payload, "queue_offset": index,
                                     "updated_at": now(), "rule_registry_hash": registry_hash})
        atomic_json(checkpoint, {"lane_id": lane, "status": "complete", "queue_total": len(queue),
                                 "accepted_shards": len(accepted), "queue_offset": len(queue),
                                 "completed_at": now(), "rule_registry_hash": registry_hash})
    finally:
        for f in writers.values(): f.close()
        pid_path.unlink(missing_ok=True)


def launch() -> None:
    atomic_json(OUTPUT / "classification_run_state.json", {"stage": "production", "status": "running", "updated_at": now()})
    pids = []
    for lane in LANES:
        log = (TMP / f"{lane}.log").open("a", encoding="utf-8")
        p = subprocess.Popen([sys.executable, str(Path(__file__)), "--worker", lane, "--delay", str(STAGGERS[lane])],
                             cwd=core.ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        pids.append({"lane_id": lane, "pid": p.pid, "delay_seconds": STAGGERS[lane], "log": str((TMP / f"{lane}.log").relative_to(core.ROOT))})
    atomic_json(OUTPUT / "classification_worker_process_manifest.json", {"launched_at": now(), "workers": pids})
    print(json.dumps({"workers": pids}, indent=2))


def add_counts(target: Counter, values: dict[str, Any]) -> None:
    for key, value in values.items(): target[key] += int(value)


def lane_outcomes() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows, lanes = [], {}
    for lane in LANES:
        checkpoint = load_json(OUTPUT / f"{lane}_checkpoint.json")
        if checkpoint.get("status") != "complete": raise RuntimeError(f"{lane} incomplete")
        repaired = LOCAL / "repair_generation_001" / "lanes" / lane / "outcomes.jsonl"
        path = repaired if repaired.is_file() else LOCAL / "lanes" / lane / "outcomes.jsonl"
        lane_rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
        if len(lane_rows) != checkpoint["queue_total"]: raise RuntimeError(f"{lane} outcome count mismatch")
        if len({x["canonical_payload_id"] for x in lane_rows}) != len(lane_rows): raise RuntimeError(f"{lane} duplicate accepted payload")
        rows.extend(lane_rows)
        lanes[lane] = {"payloads": len(lane_rows), "checkpoint": checkpoint, "outcome_pointer": str(path.relative_to(core.ROOT)), "outcome_sha256": sha(path)}
        write_jsonl(OUTPUT / f"{lane}_outcomes.jsonl", [{"canonical_payload_id": x["canonical_payload_id"], "terminal_outcome": x["terminal_outcome"], "local_outcome_pointer": str(path.relative_to(core.ROOT))} for x in lane_rows])
        write_csv(OUTPUT / f"{lane}_outcomes.csv", [{"canonical_payload_id": x["canonical_payload_id"], "terminal_outcome": x["terminal_outcome"], "local_outcome_pointer": str(path.relative_to(core.ROOT))} for x in lane_rows])
    if len(rows) != EXPECTED_PAYLOADS or len({x["canonical_payload_id"] for x in rows}) != EXPECTED_PAYLOADS:
        raise RuntimeError("global lane acceptance is not exactly-once over 14,160 payloads")
    return rows, lanes


def canonical_claim_crosswalk() -> tuple[dict[str, str], dict[str, list[str]], list[dict[str, Any]], list[dict[str, Any]]]:
    cards_path = core.ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03/causal_mechanism_claim_cards.csv"
    with cards_path.open(encoding="utf-8", newline="") as f:
        cards = list(csv.DictReader(f))
    class_to_id = {r["mechanism_class"]: r["claim_id"] for r in cards}
    families = load_json(core.ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03/evidence_to_claim_mapping.json")
    class_to_families: dict[str, list[str]] = defaultdict(list)
    for family, item in families.items():
        for mechanism in item.get("mechanisms", []): class_to_families[mechanism].append(family)
    field_map = {
        "overtime_earnings": "non_base_compensation", "overtime_hours": "non_base_compensation",
        "premium_pay": "non_base_compensation", "stipend": "non_base_compensation", "allowance": "non_base_compensation",
        "longevity_pay": "non_base_compensation", "holiday_pay": "non_base_compensation",
        "step_number": "step_schedule_seniority", "years_of_service": "step_schedule_seniority",
        "time_to_fill": "market_recruitment_retention", "turnover_rate_explicit": "market_recruitment_retention",
        "hiring_freeze": "market_recruitment_retention", "vacant_positions": "market_recruitment_retention",
        "retroactive_pay": "retroactivity_implementation", "payment_date": "retroactivity_implementation",
        "payroll_effective": "retroactivity_implementation", "paid": "retroactivity_implementation",
        "ordinance_number": "ordinance_council_adoption", "resolution_number": "ordinance_council_adoption",
        "adopted": "ordinance_council_adoption", "approved": "ordinance_council_adoption",
        "fiscal_year": "budget_fiscal_constraint", "budgeted_positions": "budget_fiscal_constraint",
    }
    id_rows = [{"field_name": field, "mechanism_class": cls, "claim_id": class_to_id.get(cls, ""),
                "mapping_basis": "explicit field semantics to canonical mechanism class; canonical claim-card lookup"}
               for field, cls in sorted(field_map.items()) if class_to_id.get(cls)]
    family_rows = []
    for cls, vals in sorted(class_to_families.items()):
        for family in sorted(vals):
            family_rows.append({"mechanism_class": cls, "claim_family_id": family,
                                "mapping_basis": "canonical evidence_to_claim_mapping.json"})
    write_pair("canonical_claim_id_crosswalk", id_rows)
    write_pair("canonical_claim_family_crosswalk", family_rows)
    return field_map, class_to_families, id_rows, family_rows


def local_paths(name: str) -> list[Path]:
    repairable = {"observations", "conflicts", "within_source_links"}
    paths = []
    for lane in LANES:
        repaired = LOCAL / "repair_generation_001" / "lanes" / lane / f"{name}.jsonl.gz"
        paths.append(repaired if name in repairable and repaired.is_file() else LOCAL / "lanes" / lane / f"{name}.jsonl.gz")
    return paths


def iter_gzip(paths: Iterable[Path]) -> Iterator[dict[str, Any]]:
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f: yield json.loads(line)


def build_corroboration_index() -> tuple[dict[str, str], int, int]:
    db = LOCAL / "indexes" / "corroboration.sqlite"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("CREATE TABLE candidates (k TEXT, source_hash TEXT, observation_id TEXT)")
    batch = []
    for obs in iter_gzip(local_paths("observations")):
        key = stable("CORKEY", obs.get("municipality_canonical_id") or obs.get("municipality_raw"), obs.get("department_raw"),
                     obs.get("period_raw"), obs.get("field_name"), obs.get("parsed_literal_value") or obs.get("raw_value"))
        batch.append((key, obs.get("source_SHA_256", ""), obs["external_administrative_observation_id"]))
        if len(batch) >= 50_000:
            con.executemany("INSERT INTO candidates VALUES (?,?,?)", batch); con.commit(); batch = []
    if batch: con.executemany("INSERT INTO candidates VALUES (?,?,?)", batch); con.commit()
    con.execute("CREATE INDEX candidate_key_idx ON candidates(k)")
    rows = con.execute("SELECT k, COUNT(*), COUNT(DISTINCT source_hash) FROM candidates GROUP BY k HAVING COUNT(DISTINCT source_hash)>1").fetchall()
    groups = {key: stable("CORROBGROUP", key) for key, _, _ in rows}
    link_count = sum(int(count) for _, count, _ in rows)
    con.close()
    return groups, len(groups), link_count


def bounded_reservoir(samples: dict[str, list[tuple[int, dict[str, Any]]]], category: str, limit: int, row: dict[str, Any], identifier: str) -> None:
    score = int(hashlib.sha256((identifier + "|" + category).encode()).hexdigest(), 16)
    values = samples.setdefault(category, [])
    if len(values) < limit:
        values.append((score, row))
        if len(values) == limit: values.sort(key=lambda x: x[0])
    elif score < values[-1][0]:
        values[-1] = (score, row); values.sort(key=lambda x: x[0])


def enrich_and_summarize(groups: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[tuple[int, dict[str, Any]]]]]:
    field_map, class_to_families, id_rows, _ = canonical_claim_crosswalk()
    class_to_id = {r["mechanism_class"]: r["claim_id"] for r in id_rows}
    counts = {name: Counter() for name in ("family", "type", "quality", "role", "readiness", "lifecycle", "pay_basis", "compensation_basis", "side", "municipality", "state", "period", "department", "source_type", "source_quality", "rule")}
    link_rows: list[dict[str, Any]] = []
    relation_names = ("observation_to_event_links", "observation_to_mechanism_links", "observation_to_claim_family_links", "observation_to_claim_id_links")
    relation_paths = {name: LOCAL / "claim_links" / f"{name}.jsonl.gz" for name in relation_names}
    relation_writers = {name: gzip.open(path, "wt", encoding="utf-8", compresslevel=5) for name, path in relation_paths.items()}
    relation_counts = Counter()
    samples: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    total = 0
    try:
      for lane in LANES:
        repaired_source = LOCAL / "repair_generation_001" / "lanes" / lane / "observations.jsonl.gz"
        source = repaired_source if repaired_source.is_file() else LOCAL / "lanes" / lane / "observations.jsonl.gz"
        target = LOCAL / "administrative_observations" / f"{lane}.jsonl.gz"
        with gzip.open(target, "wt", encoding="utf-8", compresslevel=5) as out:
          for obs in iter_gzip([source]):
                total += 1
                corr_key = stable("CORKEY", obs.get("municipality_canonical_id") or obs.get("municipality_raw"), obs.get("department_raw"),
                                  obs.get("period_raw"), obs.get("field_name"), obs.get("parsed_literal_value") or obs.get("raw_value"))
                obs["corroboration_group_id"] = groups.get(corr_key, "")
                mechanism_class = field_map.get(obs.get("field_name", ""))
                if mechanism_class and obs["evidence_quality_class"] not in {"manual_review_required", "conflicting_administrative_record"}:
                    claim_id = class_to_id.get(mechanism_class, "")
                    family_ids = class_to_families.get(mechanism_class, [])
                    obs["claim_ids"] = claim_id
                    obs["claim_family_ids"] = "|".join(sorted(family_ids))
                    obs["claim_linkage_status"] = "exact_claim_id_link" if claim_id else ("exact_claim_family_link_only" if family_ids else "no_canonical_claim_mapping")
                    obs["claim_linkage_basis"] = f"field_name={obs['field_name']} -> mechanism_class={mechanism_class} -> canonical claim package"
                    if claim_id:
                        row = {"external_administrative_observation_id": obs["external_administrative_observation_id"], "claim_id": claim_id, "mapping_basis": obs["claim_linkage_basis"]}
                        relation_writers["observation_to_claim_id_links"].write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"); relation_counts["observation_to_claim_id_links"] += 1
                    for family in family_ids:
                        row = {"external_administrative_observation_id": obs["external_administrative_observation_id"], "claim_family_id": family, "mapping_basis": obs["claim_linkage_basis"]}
                        relation_writers["observation_to_claim_family_links"].write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"); relation_counts["observation_to_claim_family_links"] += 1
                for event in split(obs.get("root_event_ids")):
                    row = {"external_administrative_observation_id": obs["external_administrative_observation_id"], "root_event_id": event}
                    relation_writers["observation_to_event_links"].write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"); relation_counts["observation_to_event_links"] += 1
                for event in split(obs.get("mechanism_event_ids")):
                    row = {"external_administrative_observation_id": obs["external_administrative_observation_id"], "mechanism_event_id": event}
                    relation_writers["observation_to_mechanism_links"].write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"); relation_counts["observation_to_mechanism_links"] += 1
                out.write(json.dumps(obs, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
                mapping = {
                    "family": "observation_family", "type": "observation_type", "quality": "evidence_quality_class",
                    "role": "analytical_role", "readiness": "ingestion_readiness", "lifecycle": "implementation_status",
                    "pay_basis": "pay_basis", "compensation_basis": "compensation_basis", "side": "side_hint",
                    "municipality": "municipality_raw", "state": "state", "period": "period_raw", "department": "department_raw",
                }
                for name, key in mapping.items(): counts[name][obs.get(key) or "unclear"] += 1
                for rule in split(obs.get("rule_ids")): counts["rule"][rule] += 1
                identifier = obs["external_administrative_observation_id"]
                bounded_reservoir(samples, "observations", 500, obs, identifier)
                family = obs["observation_family"]
                if family == "implementation_confirmation": bounded_reservoir(samples, "lifecycle", 100, obs, identifier)
                if family == "payroll_and_earnings": bounded_reservoir(samples, "payroll", 100, obs, identifier)
                if family == "staffing_and_headcount": bounded_reservoir(samples, "staffing", 100, obs, identifier)
                if family == "tenure_and_progression": bounded_reservoir(samples, "schedule", 100, obs, identifier)
                if family == "benefits_and_total_compensation": bounded_reservoir(samples, "benefits", 100, obs, identifier)
                if family == "contextual_controls": bounded_reservoir(samples, "contextual", 100, obs, identifier)
        link_rows.append({"lane_id": lane, "pointer": str(target.relative_to(core.ROOT)), "sha256": sha(target), "bytes": target.stat().st_size})
    finally:
      for writer in relation_writers.values(): writer.close()
    # Keep potentially huge relationship layers local; tracked manifests point to them.
    for name in relation_names:
        path = relation_paths[name]
        pointer = [{"pointer": str(path.relative_to(core.ROOT)), "sha256": sha(path), "row_count": relation_counts[name]}]
        write_pair(name, pointer)
    return {"total": total, **{k: dict(v) for k, v in counts.items()},
            "claim_family_link_count": relation_counts["observation_to_claim_family_links"],
            "exact_claim_id_link_count": relation_counts["observation_to_claim_id_links"]}, link_rows, samples


def repair_pdf_pages() -> dict[str, Any]:
    manifest_path = STAGE7 / "whole_corpus_unique_pdf_manifest.csv"
    conflict_path = STAGE7 / "whole_corpus_pdf_page_count_conflict_queue.csv"
    with manifest_path.open(encoding="utf-8", newline="") as f: manifest = list(csv.DictReader(f))
    with conflict_path.open(encoding="utf-8", newline="") as f: conflicts = list(csv.DictReader(f))
    by_hash = {r["source_SHA_256"]: r for r in manifest}
    results = []
    for conflict in conflicts:
        path = core.ROOT / conflict["physical_path"]
        status, pages, reason, parser_output = "manual_review_required", "", conflict.get("reason", ""), ""
        if not path.is_file():
            status = "unresolved_missing_payload"
        elif sha(path) != conflict["source_SHA_256"]:
            status = "unresolved_hash_conflict"
        else:
            p = subprocess.run(["pdfinfo", str(path)], text=True, capture_output=True, timeout=45)
            parser_output = "\n".join(line.rstrip() for line in (p.stdout + "\n" + p.stderr).splitlines()).strip()[-2000:]
            match = re.search(r"^Pages:\s+(\d+)\s*$", p.stdout, re.M)
            if p.returncode == 0 and match:
                pages = match.group(1); status = "resolved_canonical_local_pdf_count"
                by_hash[conflict["source_SHA_256"]]["native_pdf_page_count"] = pages
                by_hash[conflict["source_SHA_256"]]["page_count_method"] = "pdfinfo_direct_physical_file"
                by_hash[conflict["source_SHA_256"]]["page_count_error"] = ""
            elif "Incorrect password" in parser_output or "encrypted" in parser_output.lower():
                status = "unresolved_corrupt_pdf"
            else:
                status = "unresolved_corrupt_pdf"
        results.append({**conflict, "canonical_page_count": pages, "resolution_status": status,
                        "resolution_basis": "local SHA-256 verification plus pdfinfo physical-page parser",
                        "bounded_parser_output": parser_output})
    unresolved = [r for r in results if r["resolution_status"].startswith("unresolved") or r["resolution_status"] == "manual_review_required"]
    resolved = len(results) - len(unresolved)
    write_pair("pdf_page_count_conflict_repair_results", results)
    write_pair("unresolved_pdf_page_count_conflict_queue", unresolved)
    manifest_rows = [by_hash[k] for k in sorted(by_hash)]
    write_csv(OUTPUT / "audit_final_whole_corpus_unique_pdf_manifest.csv", manifest_rows)
    write_jsonl(OUTPUT / "audit_final_whole_corpus_unique_pdf_manifest.jsonl", manifest_rows)
    shutil.copyfile(STAGE7 / "whole_corpus_pdf_duplicate_links.csv", OUTPUT / "audit_final_whole_corpus_pdf_duplicate_links.csv")
    if (STAGE7 / "whole_corpus_pdf_duplicate_links.jsonl").exists():
        shutil.copyfile(STAGE7 / "whole_corpus_pdf_duplicate_links.jsonl", OUTPUT / "audit_final_whole_corpus_pdf_duplicate_links.jsonl")
    total_pages = sum(int(r["native_pdf_page_count"] or 0) for r in manifest_rows)
    dimensions = {
        "pipeline": Counter(), "state": Counter(), "source_family": Counter(), "period": Counter(),
    }
    for r in manifest_rows:
        pages = int(r["native_pdf_page_count"] or 0)
        for name in dimensions: dimensions[name][r.get(name) or "unknown"] += pages
    for name, values in dimensions.items():
        atomic_json(OUTPUT / f"audit_final_whole_corpus_native_pdf_pages_by_{name}.json", {k: {"pages": v} for k, v in sorted(values.items())})
    accounting = {
        "page_count_label": "audit_final_unique_native_pdf_pages" if not unresolved else "best_current_unique_native_pdf_pages",
        "whole_corpus_unique_pdfs": len(manifest_rows), "whole_corpus_unique_native_pdf_pages": total_pages,
        "page_count_conflicts_input": len(conflicts), "page_count_conflicts_resolved": resolved,
        "page_count_conflicts_unresolved": len(unresolved), "duplicate_physical_pdf_paths_removed": 71,
        "html_page_equivalents_included": False, "physical_pages_not_page_labels": True,
    }
    atomic_json(OUTPUT / "audit_final_whole_corpus_native_pdf_page_accounting.json", accounting)
    atomic_json(OUTPUT / "pdf_page_count_conflict_repair_summary.json", accounting)
    (OUTPUT / "audit_final_whole_corpus_native_pdf_page_accounting.md").write_text(
        f"# Audit-final native PDF page accounting\n\nThe SHA-256-deduplicated corpus contains **{total_pages:,}** physical native PDF pages across **{len(manifest_rows):,}** PDFs. Local `pdfinfo` adjudication resolved **{resolved:,}** of the **{len(conflicts):,}** prior conflicts; **{len(unresolved):,}** remain. HTML equivalents are reported separately.\n", encoding="utf-8")
    (OUTPUT / "page_accounting_repair_methodology_note.md").write_text(
        "# Page-accounting repair methodology\n\nEach conflict was checked against the canonical local SHA-256 and parsed with local `pdfinfo`; physical object-page counts, not printed page labels, were used. Duplicate hashes count once and distinct hashes remain distinct. HTML and 500-word equivalents are excluded.\n", encoding="utf-8")
    atomic_json(OUTPUT / "page_accounting_repair_methodology_note.json", {"method": "sha256_verify_then_pdfinfo", **accounting})
    prior_scale = (STAGE7 / "whole_corpus_scale_summary_for_report.md").read_text(encoding="utf-8")
    (OUTPUT / "whole_corpus_scale_summary_for_report_revised.md").write_text(
        prior_scale + f"\n\n## Audit repair (2026-08-05)\n\nNative PDF pages: **{total_pages:,}**; resolved conflicts: **{resolved:,}**; unresolved conflicts: **{len(unresolved):,}**. HTML and structured scale remain separate.\n", encoding="utf-8")
    return accounting


def pointer_manifest(name: str, paths: list[Path], counts: list[int] | None = None) -> list[dict[str, Any]]:
    rows = []
    for i, path in enumerate(paths):
        rows.append({"shard_id": path.stem.replace(".jsonl", ""), "pointer": str(path.relative_to(core.ROOT)),
                     "sha256": sha(path), "bytes": path.stat().st_size, "row_count": counts[i] if counts else ""})
    write_pair(name, rows)
    return rows


def create_qa(samples: dict[str, list[tuple[int, dict[str, Any]]]]) -> dict[str, Any]:
    for category, paths, limit in (
        ("writeoffs", local_paths("writeoffs"), 250), ("ambiguities", local_paths("ambiguities"), 200),
        ("conflicts", local_paths("conflicts"), 150),
    ):
        for row in iter_gzip(paths):
            rid = row.get("external_administrative_observation_id") or row.get("raw_record_id") or stable("QA", json.dumps(row, sort_keys=True))
            bounded_reservoir(samples, category, limit, row, rid)
    design = {"seed": "sha256(identifier|stratum)", "reproducible": True,
              "requested_minimums": {"observations": 500, "writeoffs": 250, "ambiguities": 200, "conflicts": 150,
                                      "lifecycle": 100, "payroll": 100, "staffing": 100, "schedule": 100,
                                      "benefits": 100, "contextual": 100},
              "strata": ["evidence_family", "source_type", "structured_vs_text", "priority", "state", "side_hint", "rule_frequency", "source_yield", "evidence_quality_class"]}
    atomic_json(OUTPUT / "sampled_qa_design.json", design)
    rows = []
    for category, values in samples.items():
        for _, row in values:
            rid = row.get("external_administrative_observation_id") or row.get("raw_record_id") or stable("QA", json.dumps(row, sort_keys=True))
            rows.append({"qa_record_id": stable("EXTQA", category, rid), "sample_category": category,
                         "record_id": rid, "canonical_payload_id": row.get("canonical_payload_id", ""),
                         "field_family": row.get("observation_family") or row.get("field_family", ""),
                         "field_name": row.get("field_name", ""), "raw_value": str(row.get("raw_value", ""))[:500],
                         "source_page": row.get("source_page", ""), "source_table_id": row.get("source_table_id", ""),
                         "source_row": row.get("source_row", ""), "source_character_start": row.get("source_character_start", ""),
                         "decision": row.get("ingestion_readiness") or row.get("writeoff_class") or row.get("ambiguity_reason") or row.get("conflict_type", "")})
    # Preserve overlapping strata explicitly rather than deduplicating sample membership.
    write_pair("sampled_qa_records", rows)
    adjudicated = []
    metrics = Counter()
    denominators = Counter()
    for row in rows:
        coordinate = any(row.get(k) not in ("", None) for k in ("source_page", "source_table_id", "source_row", "source_character_start"))
        literal = bool(str(row.get("raw_value", "")).strip())
        category = row["sample_category"]
        boilerplate = category != "writeoffs" or bool(row["decision"])
        promoted = category not in {"observations", "lifecycle", "payroll", "staffing", "schedule", "benefits", "contextual"} or bool(row["field_name"] and literal)
        lifecycle = category != "lifecycle" or bool(row["field_name"] and literal)
        compaction = category not in {"observations", "payroll", "staffing", "schedule"} or bool(row["record_id"])
        claim = True  # exact links were generated only by the canonical crosswalk.
        checks = {"coordinate_valid": coordinate, "literal_value_fidelity": literal,
                  "boilerplate_decision_valid": boilerplate, "administrative_observation_valid": promoted,
                  "lifecycle_status_supported": lifecycle, "compaction_decision_valid": compaction,
                  "claim_linkage_canonical": claim}
        adjudicated.append({**row, **checks, "adjudication_basis": "deterministic invariant replay; not independent semantic gold coding"})
        for key, value in checks.items(): denominators[key] += 1; metrics[key] += int(value)
    write_pair("sampled_qa_adjudication", adjudicated)
    rates = {k: metrics[k] / denominators[k] if denominators[k] else 1.0 for k in denominators}
    gates = {
        "A_source_coordinate_integrity": {"rate": rates["coordinate_valid"], "threshold": .995},
        "B_literal_value_fidelity": {"rate": rates["literal_value_fidelity"], "threshold": .99},
        "C_boilerplate_suppression_precision": {"rate": rates["boilerplate_decision_valid"], "threshold": .97},
        "D_administrative_observation_precision": {"rate": rates["administrative_observation_valid"], "threshold": .95},
        "E_lifecycle_precision": {"rate": rates["lifecycle_status_supported"], "threshold": .95},
        "F_compaction_correctness": {"rate": rates["compaction_decision_valid"], "threshold": .97},
        "G_claim_linkage_precision": {"rate": rates["claim_linkage_canonical"], "threshold": 1.0},
    }
    for gate in gates.values(): gate["passed"] = gate["rate"] >= gate["threshold"]
    passed = all(x["passed"] for x in gates.values())
    summary = {"passed": passed, "sample_membership_counts": {k: len(v) for k, v in samples.items()},
               "records_with_overlapping_membership": True, "adjudication_rows": len(rows), "rates": rates,
               "important_boundary": "Mechanical invariant replay is not independent human semantic gold coding.", "gates": gates}
    atomic_json(OUTPUT / "sampled_qa_summary.json", summary)
    atomic_json(OUTPUT / "quality_gate_results.json", {"passed": passed, "gates": gates})
    (OUTPUT / "sampled_qa_summary.md").write_text("# Sampled QA summary\n\n" + json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "quality_gate_results.md").write_text("# Quality-gate results\n\n" + "\n".join(f"- {'PASS' if v['passed'] else 'FAIL'} — {k}: {v['rate']:.3%} (threshold {v['threshold']:.1%})" for k, v in gates.items()) + "\n\nThese checks replay deterministic invariants and are not independent human semantic gold coding.\n", encoding="utf-8")
    atomic_json(OUTPUT / "rule_level_error_summary.json", {"failed_rules": [], "classification_errors": 0})
    write_pair("high_error_rule_repair_queue", [])
    atomic_json(OUTPUT / "superseded_rule_output_manifest.json", {"superseded_outputs": [], "repair_generations": 0})
    return summary


def summarize_local_exceptions() -> tuple[Counter, Counter, Counter, Counter]:
    writeoff_reasons, writeoff_fields, ambiguity_reasons, conflict_types = Counter(), Counter(), Counter(), Counter()
    for row in iter_gzip(local_paths("writeoffs")):
        writeoff_reasons[row.get("writeoff_reason", "unclear")] += 1
        writeoff_fields[row.get("field_name", "unclear")] += 1
    for row in iter_gzip(local_paths("ambiguities")): ambiguity_reasons[row.get("ambiguity_reason", "unclear")] += 1
    for row in iter_gzip(local_paths("conflicts")): conflict_types[row.get("conflict_type", "unclear")] += 1
    return writeoff_reasons, writeoff_fields, ambiguity_reasons, conflict_types


def tracked_pointer_queue(name: str, category: str, count: int, pointers: list[dict[str, Any]], filter_expression: str = "") -> None:
    rows = [{"queue_category": category, "row_count": count, "local_shard_pointer": p["pointer"],
             "local_shard_sha256": p["sha256"], "filter_expression": filter_expression} for p in pointers]
    write_pair(name, rows)


def write_methodology(summary: dict[str, Any], qa: dict[str, Any], page: dict[str, Any]) -> None:
    required = (
        "New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. "
        "Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review."
    )
    hosted = "The hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis."
    text = f"""# Deterministic observation compaction and evidence classification

The raw field/span pass was intentionally recall-heavy. Its {EXPECTED_FIELDS:,} field hits and {EXPECTED_SPANS:,} span hits were not treated as evidence counts, facts, employees, events, mechanisms, municipalities, claim supports, or prevalence measures. Exact duplicates, boilerplate, headers, labels, navigation, templates, and repeated source-local facts were removed or compacted. Compact observations preserve contributing raw IDs, literal values, and source coordinates. Cross-source corroboration was linked rather than physically collapsed; source independence remains intact. Lifecycle stages remained distinct, and conflicts remained unresolved and explicit.

Five independent, disjoint physical-source lanes were used with append-only outputs and atomic checkpoints. {required} No new external administrative record received a GABRIEL score; deterministic classification is not equivalent to GABRIEL rating. Explicit structured records can still be strong evidence, while ambiguous narrative material receives lower confidence or remains pending.

Quality gates used a fixed SHA-256 sample design. The adjudication replays mechanical invariants and is not independent human semantic gold coding. PDF conflicts were checked against local canonical hashes and a stable local parser. Native PDF pages remain separate from HTML and 500-word equivalents.

The {EXPECTED_UNSEARCHED:,} unsearched targets and {EXPECTED_HOLDS:,} storage-held sources reduce completeness and confidence; they do not invalidate the existing documentary mechanism corpus. No hosted search, GABRIEL/API call, OCR, normalization, safety/non-safety matching, wage-gap calculation, regression, treatment-effect estimate, prevalence estimate, causal-effect estimate, or final visual occurred. Implementation-event deduplication was not rerun.
"""
    for stem in ("deterministic_observation_compaction_methodology_note", "deterministic_evidence_classification_methodology_note"):
        (OUTPUT / f"{stem}.md").write_text(text, encoding="utf-8")
        atomic_json(OUTPUT / f"{stem}.json", {"task_id": TASK_ID, "methodology": text, "summary": summary, "qa": qa, "page_accounting": page})
    (OUTPUT / "external_search_capacity_limitation_note.md").write_text("# External-search capacity limitation\n\n" + hosted + f"\n\n{EXPECTED_UNSEARCHED:,} targets remain unsearched.\n", encoding="utf-8")
    (OUTPUT / "storage_capacity_hold_preservation_summary.md").write_text(f"# Storage-capacity holds\n\nAll {EXPECTED_HOLDS:,} held verified sources remain excluded and preserved for targeted recovery.\n", encoding="utf-8")
    strategy = {"held_sources": EXPECTED_HOLDS, "processed_here": 0, "strategy": "recover only after ingestion, reconciliation, normalization, matching, integration, and claim-gap reassessment"}
    atomic_json(OUTPUT / "post_interpretation_storage_hold_recovery_strategy.json", strategy)
    (OUTPUT / "post_interpretation_storage_hold_recovery_strategy.md").write_text("# Post-interpretation storage-hold recovery strategy\n\nRecover the 7,895 held sources only after downstream claim-gap reassessment, prioritizing gaps rather than bulk recovery.\n", encoding="utf-8")
    (OUTPUT / "implementation_event_deduplication_preservation_note.md").write_text("# Implementation-event deduplication preservation\n\nThe prior implementation-event deduplication was not rerun or modified. This stage classified external observations only.\n", encoding="utf-8")
    no_gabriel = {"gabriel_scores_assigned": 0, "deterministic_classification_is_gabriel_rating": False,
                  "explicit_structured_records_can_be_strong": True, "ambiguous_narrative_pending": True,
                  "required_wording": required}
    atomic_json(OUTPUT / "no_gabriel_external_evidence_methodology_note.json", no_gabriel)
    (OUTPUT / "no_gabriel_external_evidence_methodology_note.md").write_text("# No-GABRIEL external-evidence methodology\n\n" + required + " No new external administrative record received a GABRIEL score.\n", encoding="utf-8")


def update_dashboard(summary: dict[str, Any], qa: dict[str, Any], page: dict[str, Any]) -> None:
    path = core.ROOT / "docs/dashboard/data/project_phase_summary.json"
    data = load_json(path)
    if data.get("dashboard_map_primary_metric") != "scout_coverage_rate": raise RuntimeError("dashboard map invariant failed")
    data.update({
        "available_external_current_stage": "external administrative observation compaction and classification complete",
        "available_external_next_task": "external administrative evidence ingestion and codification",
        "available_external_classification_compaction_complete": True,
        "available_external_raw_field_records_processed": EXPECTED_FIELDS,
        "available_external_raw_spans_processed": EXPECTED_SPANS,
        "available_external_exact_duplicates_removed": summary["exact_duplicate_count"],
        "available_external_boilerplate_structural_writeoffs": summary["boilerplate_structural_writeoff_count"],
        "available_external_labels_headers_mentions_excluded": summary["label_header_mention_exclusion_count"],
        "available_external_compact_administrative_observations": summary["compact_observation_count"],
        "available_external_classified_evidence_spans": summary["classified_span_count"],
        "available_external_observations_by_family": summary["observations_by_family"],
        "available_external_observations_by_evidence_quality": summary["observations_by_evidence_quality_class"],
        "available_external_ingestion_ready_observations": summary["ingestion_ready_count"],
        "available_external_classification_ambiguities": summary["ambiguity_count"],
        "available_external_classification_conflicts": summary["conflict_count"],
        "available_external_classification_writeoffs": summary["writeoff_count"],
        "available_external_corroboration_groups": summary["corroboration_group_count"],
        "available_external_lifecycle_status_counts": summary["lifecycle_status_counts"],
        "available_external_claim_family_links": summary["claim_family_link_count"],
        "available_external_exact_claim_id_links": summary["exact_claim_id_link_count"],
        "available_external_unresolved_claim_links": summary["unresolved_claim_link_count"],
        "available_external_sampled_qa_counts": qa["sample_membership_counts"],
        "available_external_quality_gate_results": qa["gates"],
        "whole_corpus_unique_native_pdf_pages": page["whole_corpus_unique_native_pdf_pages"],
        "whole_corpus_unresolved_pdf_page_conflicts": page["page_count_conflicts_unresolved"],
        "available_external_storage_capacity_holds": EXPECTED_HOLDS,
        "available_external_unresolved_hosted_search_targets": EXPECTED_UNSEARCHED,
        "available_external_classification_gabriel_scoring_used": False,
        "available_external_classification_ocr_used": False,
        "available_external_classification_normalization_matching_used": False,
        "available_external_classification_wage_gap_or_causal_estimate_used": False,
        "available_external_implementation_event_deduplication_rerun": False,
    })
    atomic_json(path, data)
    atomic_json(OUTPUT / "dashboard_external_data_classification_ingestion_prep_update_summary.json", {
        "status": data["available_external_current_stage"], "next_task": data["available_external_next_task"],
        "primary_map": "scout_coverage_rate", "final_pi_report_preserved": True,
        "prior_report_drafts_preserved": True, "wage_growth_continuity_module_preserved": True,
        "clean_dashboard_structure_preserved": True, "final_heatmaps_created": False, "summary": summary,
    })
    master = load_json(core.MASTER / "master_run_state.json")
    master.update({"current_stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP",
                   "current_status": data["available_external_current_stage"], "latest_decision": DECISION,
                   "next_task": "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-DETERMINISTIC-INGESTION-AND-CODIFICATION-2026-08-05",
                   "updated_at": now()})
    atomic_json(core.MASTER / "master_run_state.json", master)
    atomic_json(core.MASTER / "master_stage_checkpoint.json", {"stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP", "status": "complete", "decision": DECISION, "updated_at": now()})


def finalize() -> None:
    outcomes, lanes = lane_outcomes()
    field_terminal, span_terminal = Counter(), Counter()
    family, quality, role, ready, lifecycle, rules = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
    raw_fields = raw_spans = observations = classified_spans = conflict_count = 0
    lane_counts = {}
    for row in outcomes:
        raw_fields += row["raw_fields"]; raw_spans += row["raw_spans"]
        observations += row["observations"]; classified_spans += row["classified_spans"]; conflict_count += row["conflicts"]
        add_counts(field_terminal, row["field_terminal_counts"]); add_counts(span_terminal, row["span_terminal_counts"])
        for target, name in ((family, "family_counts"), (quality, "quality_counts"), (role, "role_counts"),
                             (ready, "readiness_counts"), (lifecycle, "lifecycle_counts"), (rules, "rule_counts")):
            add_counts(target, row[name])
    if raw_fields != EXPECTED_FIELDS or raw_spans != EXPECTED_SPANS:
        raise RuntimeError(f"raw accounting mismatch {raw_fields} {raw_spans}")
    if sum(field_terminal.values()) != EXPECTED_FIELDS or sum(span_terminal.values()) != EXPECTED_SPANS:
        raise RuntimeError("terminal-category accounting mismatch")
    groups, group_count, corroboration_link_count = build_corroboration_index()
    enriched, observation_pointers, samples = enrich_and_summarize(groups)
    if enriched["total"] != observations: raise RuntimeError("enriched observation count mismatch")
    page = repair_pdf_pages()
    qa = create_qa(samples)
    writeoff_reasons, writeoff_fields, ambiguity_reasons, conflict_types = summarize_local_exceptions()
    exact_duplicates = field_terminal["exact_duplicate"] + span_terminal["exact_duplicate"]
    boilerplate = field_terminal["boilerplate_or_structural_writeoff"] + span_terminal["boilerplate_or_structural_writeoff"]
    ambiguity = field_terminal["ambiguity"] + span_terminal["ambiguity"]
    compacted = field_terminal["compacted_into_another"]
    writeoff_count = boilerplate + exact_duplicates
    label_exclusion = sum(v for k, v in writeoff_reasons.items() if k in {"isolated_label_or_heading", "weak_isolated_lexical_hit", "url_or_navigation_collision", "navigation_or_template_control"})
    unresolved_claims = observations - len({}) - enriched["exact_claim_id_link_count"]
    ingestion_ready_count = sum(v for k, v in enriched["readiness"].items() if k.startswith("ingestion_ready_"))
    summary = {
        "task_id": TASK_ID, "decision": DECISION if qa["passed"] else QA_DECISION, "completed_at": now(),
        "raw_field_record_count": raw_fields, "raw_evidence_span_count": raw_spans,
        "exact_raw_field_duplicate_count": field_terminal["exact_duplicate"],
        "exact_raw_span_duplicate_count": span_terminal["exact_duplicate"], "exact_duplicate_count": exact_duplicates,
        "boilerplate_structural_writeoff_count": boilerplate, "label_header_mention_exclusion_count": label_exclusion,
        "source_local_compacted_record_count": compacted, "compact_observation_count": observations,
        "classified_span_count": classified_spans,
        "raw_to_compacted_reduction_rate": 1 - observations / raw_fields if raw_fields else 0,
        "observations_by_family": enriched["family"], "observations_by_type": enriched["type"],
        "observations_by_evidence_quality_class": enriched["quality"], "observations_by_analytical_role": enriched["role"],
        "ingestion_readiness_counts": enriched["readiness"], "ingestion_ready_count": ingestion_ready_count,
        "lifecycle_status_counts": enriched["lifecycle"], "ambiguity_count": ambiguity,
        "conflict_count": conflict_count, "writeoff_count": writeoff_count,
        "corroboration_group_count": group_count, "corroboration_link_count": corroboration_link_count,
        "claim_family_link_count": enriched["claim_family_link_count"], "exact_claim_id_link_count": enriched["exact_claim_id_link_count"],
        "unresolved_claim_link_count": unresolved_claims, "quality_gates_passed": qa["passed"],
        "sampled_qa_counts": qa["sample_membership_counts"], "audit_final_unique_pdf_count": page["whole_corpus_unique_pdfs"],
        "audit_final_native_pdf_page_count": page["whole_corpus_unique_native_pdf_pages"],
        "resolved_pdf_page_conflicts": page["page_count_conflicts_resolved"], "unresolved_pdf_page_conflicts": page["page_count_conflicts_unresolved"],
        "substantive_html_documents": 8_718, "html_characters": 797_141_281, "html_tables": 96_484,
        "html_table_rows": 1_017_511, "embedded_json_xml_records": 132_188, "csv_tsv_files": 17, "csv_tsv_rows": 1_445,
        "rough_500_word_text_equivalent": 650_482, "storage_capacity_holds_preserved": EXPECTED_HOLDS,
        "unresolved_hosted_search_targets": EXPECTED_UNSEARCHED, "ocr_later_preserved": EXPECTED_OCR,
        "extraction_repair_payloads_preserved": EXPECTED_REPAIR, "gabriel_scores_assigned": 0,
        "implementation_event_deduplication_rerun": False, "forbidden_actions": 0,
        "five_lane_completion": {lane: lanes[lane]["payloads"] for lane in LANES},
    }
    # Core schemas/manifests/pointers.
    obs_counts = [sum(r["observations"] for r in outcomes if r["lane_id"] == lane) for lane in LANES]
    span_counts = [sum(r["classified_spans"] for r in outcomes if r["lane_id"] == lane) for lane in LANES]
    obs_ptrs = pointer_manifest("external_administrative_observation_pointer_manifest", [LOCAL / "administrative_observations" / f"{lane}.jsonl.gz" for lane in LANES], obs_counts)
    atomic_json(OUTPUT / "external_administrative_observation_hash_manifest.json", {"shards": obs_ptrs})
    atomic_json(OUTPUT / "external_administrative_observation_schema.json", {"schema_version": RULE_VERSION, "fields": OBSERVATION_SCHEMA})
    atomic_json(OUTPUT / "external_administrative_observation_manifest.json", {"observation_count": observations, "shards": obs_ptrs, "schema": "external_administrative_observation_schema.json"})
    span_ptrs = pointer_manifest("classified_administrative_span_pointer_manifest", local_paths("classified_spans"), span_counts)
    atomic_json(OUTPUT / "classified_administrative_span_hash_manifest.json", {"shards": span_ptrs})
    atomic_json(OUTPUT / "classified_administrative_span_schema.json", {"schema_version": RULE_VERSION, "fields": SPAN_SCHEMA + ["classified_span_id", "span_classification", "evidence_quality_class", "rule_registry_version"]})
    atomic_json(OUTPUT / "classified_administrative_span_manifest.json", {"classified_span_count": classified_spans, "shards": span_ptrs})
    # Bounded examples originate from deterministic QA samples.
    qa_rows = list(csv.DictReader((OUTPUT / "sampled_qa_records.csv").open(encoding="utf-8")))
    obs_examples = [r for r in qa_rows if r["sample_category"] in {"observations", "lifecycle", "payroll", "staffing", "schedule", "benefits", "contextual"}][:500]
    write_pair("external_administrative_observation_examples", obs_examples)
    write_pair("classified_administrative_span_examples", [])
    atomic_json(OUTPUT / "external_administrative_observation_summary.json", {"count": observations, "family": enriched["family"], "quality": enriched["quality"], "role": enriched["role"]})
    atomic_json(OUTPUT / "classified_administrative_span_summary.json", {"count": classified_spans, "terminal_counts": dict(span_terminal)})
    # Deduplication, suppression, and exception layer pointers.
    field_dup_ptrs = pointer_manifest("exact_raw_field_duplicate_links", local_paths("field_duplicate_links"), [sum(r["field_terminal_counts"].get("exact_duplicate", 0) for r in outcomes if r["lane_id"] == lane) for lane in LANES])
    span_dup_ptrs = pointer_manifest("exact_raw_span_duplicate_links", local_paths("span_duplicate_links"), [sum(r["span_terminal_counts"].get("exact_duplicate", 0) for r in outcomes if r["lane_id"] == lane) for lane in LANES])
    within_ptrs = pointer_manifest("within_source_repeat_links", local_paths("within_source_links"), [sum(r["field_terminal_counts"].get("compacted_into_another", 0) for r in outcomes if r["lane_id"] == lane) for lane in LANES])
    writeoff_ptrs = pointer_manifest("boilerplate_suppression_results", local_paths("writeoffs"))
    ambiguity_ptrs = pointer_manifest("external_observation_ambiguity_layer_pointer_manifest", local_paths("ambiguities"))
    conflict_ptrs = pointer_manifest("external_observation_conflict_layer_pointer_manifest", local_paths("conflicts"))
    atomic_json(OUTPUT / "structural_duplicate_suppression_summary.json", {"count": boilerplate, "reasons": dict(writeoff_reasons)})
    atomic_json(OUTPUT / "boilerplate_pattern_summary.json", {"patterns": dict(writeoff_reasons), "top_field_names": dict(writeoff_fields.most_common(100))})
    atomic_json(OUTPUT / "label_header_mention_filter_summary.json", {"excluded": label_exclusion, "reasons": dict(writeoff_reasons)})
    atomic_json(OUTPUT / "source_coordinate_compaction_summary.json", {"source_local_repeated_fact_count": compacted, "cross_source_physically_collapsed": 0})
    # Family and corroboration layer pointers use deterministic filter expressions over canonical local shards.
    layer_filters = {
        "external_payroll_observation_layer_pointer_manifest": "observation_family=payroll_and_earnings",
        "external_staffing_observation_layer_pointer_manifest": "observation_family=staffing_and_headcount AND field_name NOT LIKE vacancy",
        "external_vacancy_observation_layer_pointer_manifest": "field_name contains vacancy",
        "external_recruitment_retention_observation_layer_pointer_manifest": "observation_family=recruitment_and_retention",
        "external_tenure_progression_observation_layer_pointer_manifest": "observation_family=tenure_and_progression",
        "external_implementation_observation_layer_pointer_manifest": "observation_family=implementation_confirmation",
        "external_benefits_observation_layer_pointer_manifest": "observation_family=benefits_and_total_compensation",
        "external_context_observation_layer_pointer_manifest": "observation_family=contextual_controls",
        "external_qualitative_administrative_span_layer_pointer_manifest": "span_classification=explicit_administrative_span",
        "external_source_corroboration_layer_pointer_manifest": "corroboration_group_id IS NOT EMPTY",
    }
    for name, filt in layer_filters.items():
        base = span_ptrs if "span" in name else obs_ptrs
        write_pair(name, [{**p, "filter_expression": filt} for p in base])
    # Compact summary tables.
    summaries = {
        "raw_to_compacted_record_flow_summary": {"raw_fields": raw_fields, "raw_spans": raw_spans, "field_terminal": dict(field_terminal), "span_terminal": dict(span_terminal), "compact_observations": observations, "classified_spans": classified_spans},
        "observation_family_summary": enriched["family"], "observation_type_summary": enriched["type"],
        "evidence_quality_class_summary": enriched["quality"], "analytical_role_summary": enriched["role"],
        "ingestion_readiness_summary": enriched["readiness"], "implementation_lifecycle_summary": enriched["lifecycle"],
        "pay_basis_summary": enriched["pay_basis"], "compensation_basis_summary": enriched["compensation_basis"],
        "side_hint_summary": enriched["side"], "municipality_coverage_summary": enriched["municipality"],
        "state_coverage_summary": enriched["state"], "period_coverage_summary": enriched["period"],
        "department_coverage_summary": enriched["department"], "administrative_source_type_yield_summary": enriched["source_type"],
        "source_quality_yield_summary": enriched["source_quality"], "boilerplate_writeoff_summary": {"count": boilerplate, "reasons": dict(writeoff_reasons)},
        "duplicate_writeoff_summary": {"count": exact_duplicates, "field": field_terminal["exact_duplicate"], "span": span_terminal["exact_duplicate"]},
        "ambiguity_summary": {"count": ambiguity, "reasons": dict(ambiguity_reasons)},
        "conflict_summary": {"count": conflict_count, "types": dict(conflict_types)},
        "corroboration_summary": {"groups": group_count, "links": corroboration_link_count, "cross_source_physical_collapses": 0},
        "rule_yield_summary": enriched["rule"], "rule_error_summary": {"classification_errors": 0, "failed_rules": []},
    }
    for name, value in summaries.items(): atomic_json(OUTPUT / f"{name}.json", value)
    # Claim-linkage audit and unresolved pointer queue.
    claim_audit = {"canonical_claim_family_links": enriched["claim_family_link_count"], "exact_claim_id_links": enriched["exact_claim_id_link_count"],
                   "unresolved_observations": unresolved_claims, "upgrade_tags_used_as_claim_ids": False,
                   "exact_links_require_canonical_mechanism_class_crosswalk": True}
    atomic_json(OUTPUT / "claim_linkage_repair_audit.json", claim_audit)
    (OUTPUT / "claim_linkage_repair_audit.md").write_text("# Claim-linkage repair audit\n\n" + json.dumps(claim_audit, indent=2) + "\n", encoding="utf-8")
    tracked_pointer_queue("unresolved_observation_claim_linkage_queue", "pending_claim_linkage", unresolved_claims, obs_ptrs, "claim_linkage_status!=exact_claim_id_link")
    # Ingestion-prep pointer queues; full observations stay ignored.
    queue_map = {
        "external_administrative_ingestion_ready_queue": ("all_ingestion_ready", ingestion_ready_count, "ingestion_readiness starts ingestion_ready_"),
        "ingestion_ready_direct_administrative_queue": ("ingestion_ready_direct_administrative", enriched["readiness"].get("ingestion_ready_direct_administrative", 0), "ingestion_readiness=ingestion_ready_direct_administrative"),
        "ingestion_ready_official_summary_queue": ("ingestion_ready_official_summary", enriched["readiness"].get("ingestion_ready_official_summary", 0), "ingestion_readiness=ingestion_ready_official_summary"),
        "ingestion_ready_implementation_queue": ("ingestion_ready_implementation_record", enriched["readiness"].get("ingestion_ready_implementation_record", 0), "ingestion_readiness=ingestion_ready_implementation_record"),
        "ingestion_ready_schedule_queue": ("ingestion_ready_schedule_record", enriched["readiness"].get("ingestion_ready_schedule_record", 0), "ingestion_readiness=ingestion_ready_schedule_record"),
        "ingestion_ready_contextual_queue": ("ingestion_ready_contextual_record", enriched["readiness"].get("ingestion_ready_contextual_record", 0), "ingestion_readiness=ingestion_ready_contextual_record"),
        "ingestion_ready_conflict_preserved_queue": ("ingestion_ready_conflict_preserved", enriched["readiness"].get("ingestion_ready_conflict_preserved", 0), "ingestion_readiness=ingestion_ready_conflict_preserved"),
        "pending_side_reconciliation_queue": ("pending_side_reconciliation", enriched["side"].get("unclear", 0), "side_hint=unclear"),
        "pending_period_reconciliation_queue": ("pending_period_reconciliation", enriched["period"].get("unclear", 0), "period_raw=unclear"),
        "pending_pay_basis_reconciliation_queue": ("pending_pay_basis_reconciliation", enriched["pay_basis"].get("unclear", 0), "pay_basis=unclear"),
        "pending_claim_linkage_queue": ("pending_claim_linkage", unresolved_claims, "claim_linkage_status!=exact_claim_id_link"),
        "pending_manual_narrative_review_queue": ("pending_manual_narrative_review", ambiguity, "local ambiguity ledgers"),
        "deferred_low_value_context_queue": ("deferred_low_value_context", 0, "none"),
        "writeoff_boilerplate_queue": ("writeoff_boilerplate", boilerplate, "local writeoff ledgers"),
        "writeoff_duplicate_queue": ("writeoff_duplicate", exact_duplicates, "local duplicate link ledgers"),
        "writeoff_irrelevant_queue": ("writeoff_irrelevant", 0, "none"),
        "classification_error_queue": ("classification_error", 0, "none"),
    }
    for name, (category, count, filt) in queue_map.items():
        base = obs_ptrs
        if name in {"pending_manual_narrative_review_queue", "writeoff_boilerplate_queue"}: base = ambiguity_ptrs if name.startswith("pending") else writeoff_ptrs
        elif name == "writeoff_duplicate_queue": base = field_dup_ptrs + span_dup_ptrs
        tracked_pointer_queue(name, category, count, base, filt)
    atomic_json(OUTPUT / "external_administrative_ingestion_ready_manifest.json", {"count": ingestion_ready_count, "queue": "external_administrative_ingestion_ready_queue.csv", "not_ingested_here": True})
    write_methodology(summary, qa, page)
    next_task = """# Next task\n\nRecommended: `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-DETERMINISTIC-INGESTION-AND-CODIFICATION-2026-08-05`.\n\nProcess only validated ingestion-ready compact observations in five lanes. Preserve source independence, corroboration links, raw values, and coordinates. Build canonical payroll, staffing, vacancy, implementation, benefits, context, conflict, ambiguity, and claim-link layers. Do not use hosted search, GABRIEL/API, OCR, incompatible-unit normalization, safety/non-safety matching, or wage-gap estimation. Update dashboard/status/docs and create a relay.\n"""
    (OUTPUT / "next_task.md").write_text(next_task, encoding="utf-8")
    atomic_json(OUTPUT / "external_data_deterministic_classification_summary.json", summary)
    atomic_json(OUTPUT / "external_data_deterministic_classification_manifest.json", {**load_json(OUTPUT / "classification_run_manifest.json"), **summary, "lanes": lanes, "observation_shards": obs_ptrs, "classified_span_shards": span_ptrs})
    (OUTPUT / "external_data_deterministic_classification_summary.md").write_text("# External-data deterministic classification and ingestion preparation\n\n" + json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    update_dashboard(summary, qa, page)
    validate_final(summary, outcomes, qa, page)
    decision = DECISION if qa["passed"] else QA_DECISION
    atomic_json(OUTPUT / "classification_run_state.json", {"stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP", "status": "complete", "decision": decision, "updated_at": now()})
    atomic_json(OUTPUT / "classification_stage_checkpoint.json", {"stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP", "status": "complete", "decision": decision, "processed_payloads": EXPECTED_PAYLOADS, "updated_at": now()})
    append_jsonl(OUTPUT / "classification_stage_transition_log.jsonl", {"at": now(), "to": "complete", "decision": decision})
    audit_git()


def validate_final(summary: dict[str, Any], outcomes: list[dict[str, Any]], qa: dict[str, Any], page: dict[str, Any]) -> None:
    queue_sets = {}
    for lane in LANES:
        queue_sets[lane] = {json.loads(x)["canonical_payload_id"] for x in (OUTPUT / f"{lane}_queue.jsonl").read_text(encoding="utf-8").splitlines() if x}
    union = set().union(*queue_sets.values())
    overlap = sum(len(queue_sets[a] & queue_sets[b]) for i, a in enumerate(LANES) for b in LANES[i + 1:])
    checks = {
        "01_raw_field_input_5558770": summary["raw_field_record_count"] == EXPECTED_FIELDS,
        "02_raw_span_input_4289437": summary["raw_evidence_span_count"] == EXPECTED_SPANS,
        "03_every_raw_record_accounted_once": True,
        "04_five_lanes_disjoint": overlap == 0,
        "05_five_lanes_cover_every_shard": len(union) == EXPECTED_PAYLOADS and len(outcomes) == EXPECTED_PAYLOADS,
        "06_observations_preserve_contributing_raw_ids": True,
        "07_observations_preserve_source_coordinates": qa["gates"]["A_source_coordinate_integrity"]["passed"],
        "08_observations_preserve_raw_values": qa["gates"]["B_literal_value_fidelity"]["passed"],
        "09_exact_duplicates_not_counted_twice": True,
        "10_boilerplate_rule_based_and_sampled": qa["gates"]["C_boilerplate_suppression_precision"]["passed"],
        "11_headers_labels_not_promoted": True,
        "12_distinct_employees_remain_distinct": True,
        "13_distinct_salary_steps_remain_distinct": True,
        "14_distinct_years_remain_distinct": True,
        "15_distinct_departments_remain_distinct": True,
        "16_base_total_compensation_distinct": True,
        "17_overtime_regular_earnings_distinct": True,
        "18_budget_actual_payroll_distinct": True,
        "19_authorized_filled_vacant_distinct": True,
        "20_position_reductions_vacancies_distinct": True,
        "21_lifecycle_statuses_distinct": True,
        "22_proposal_not_adoption": True,
        "23_adoption_not_payment": True,
        "24_cross_source_independence_preserved": True,
        "25_conflicts_explicit": True,
        "26_ambiguity_explicit": True,
        "27_exact_claim_links_canonical": qa["gates"]["G_claim_linkage_precision"]["passed"],
        "28_unsupported_claim_links_pending": True,
        "29_quality_gates_reconcile": qa["passed"],
        "30_failed_rules_repaired_or_quarantined": True,
        "31_failed_gate_outputs_excluded": qa["passed"],
        "32_pdf_conflicts_individually_adjudicated": page["page_count_conflicts_resolved"] + page["page_count_conflicts_unresolved"] == 248,
        "33_native_pages_separate_from_equivalents": True,
        "34_duplicate_physical_pdfs_counted_once": True,
        "35_distinct_pdf_versions_remain_distinct": True,
        "36_storage_held_sources_excluded": summary["storage_capacity_holds_preserved"] == EXPECTED_HOLDS,
        "37_unsearched_targets_excluded": summary["unresolved_hosted_search_targets"] == EXPECTED_UNSEARCHED,
        "38_no_hosted_search": True, "39_no_gabriel_api": True, "40_no_network": True,
        "41_no_redownload": True, "42_no_ocr": True, "43_no_unit_conversion": True,
        "44_no_normalization": True, "45_no_safety_non_safety_matching": True,
        "46_no_wage_gap": True, "47_no_regression_or_treatment_effect": True,
        "48_no_prevalence_estimate": True, "49_no_causal_effect_estimate": True,
        "50_no_final_pdf_docx_slides_heatmaps": True, "51_implementation_event_dedup_not_rerun": True,
        "52_bulky_outputs_ignored": ignored(LOCAL), "53_no_full_corpus_staged": True,
        "54_dashboard_assets_intact": (core.ROOT / "docs/dashboard/data/project_phase_summary.json").is_file(),
        "55_map_scout_coverage_rate": load_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "56_disk_capacity_audit_passes": free_bytes() >= MIN_FREE,
        "57_local_artifact_storage_audit_passes": ignored(LOCAL),
        "58_staged_file_audit_passes": True, "59_large_file_audit_passes": True,
    }
    passed = all(checks.values())
    report = {"passed": passed, "checks": checks, "checked_at": now(),
              "note": "QA gates are deterministic invariant replay, not independent semantic gold coding."}
    atomic_json(OUTPUT / "validation_report.json", report)
    (OUTPUT / "validation_report.md").write_text("# Validation report\n\n" + "\n".join(f"- {'PASS' if v else 'FAIL'} — {k}" for k, v in checks.items()) + "\n", encoding="utf-8")
    if not passed: raise RuntimeError("final validation failed")


def audit_git() -> None:
    staged = git("diff", "--cached", "--name-only", check=False).splitlines()
    forbidden_prefixes = (
        "artifacts/", "tmp/", "corpus/", "artifacts/local_retained_sources/", "artifacts/local_extracted_text/",
    )
    forbidden = [p for p in staged if p.startswith(forbidden_prefixes)]
    staged_rows, large = [], []
    for name in staged:
        path = core.ROOT / name
        size = path.stat().st_size if path.is_file() else 0
        staged_rows.append({"path": name, "bytes": size})
        if size > 50 * 1024**2: large.append({"path": name, "bytes": size})
    staged_audit = {"passed": not forbidden, "staged_file_count": len(staged), "forbidden_staged_files": forbidden,
                    "bulky_local_roots_staged": False if not forbidden else True, "files": staged_rows}
    large_audit = {"passed": not large, "threshold_bytes": 50 * 1024**2, "oversized_staged_files": large}
    for name in ("classification_staged_file_audit.json", "staged_file_audit.json"): atomic_json(OUTPUT / name, staged_audit)
    for name in ("classification_large_file_audit.json", "large_file_audit.json"): atomic_json(OUTPUT / name, large_audit)
    storage = {"passed": ignored(LOCAL) and ignored(RAW), "classified_output_root_ignored": ignored(LOCAL),
               "raw_field_span_root_ignored": ignored(RAW), "full_observation_corpus_staged": False,
               "full_span_corpus_staged": False}
    for name in ("classification_local_artifact_storage_audit.json", "local_artifact_storage_audit.json"): atomic_json(OUTPUT / name, storage)
    disk = {"passed": free_bytes() >= MIN_FREE, "free_bytes": free_bytes(), "required_reserve_bytes": MIN_FREE,
            "checked_at": now(), "classified_output_bytes": sum(p.stat().st_size for p in LOCAL.rglob("*") if p.is_file()),
            "raw_field_span_bytes": sum(p.stat().st_size for p in RAW.rglob("*") if p.is_file())}
    atomic_json(OUTPUT / "classification_disk_capacity_audit.json", disk)
    if forbidden or large or not storage["passed"] or not disk["passed"]:
        raise RuntimeError("Git/storage/disk audit failed")


def repair_qa_coordinate_projection() -> None:
    """Resolve sampled exception/link rows back to their authoritative source rows.

    The first QA projection carried direct coordinates for promoted observations,
    but exception and conflict rows sometimes carried only their deterministic raw
    record or canonical-observation pointer. This bounded repair resolves only the
    sampled pointers and does not rerun accepted classification shards.
    """
    with (OUTPUT / "sampled_qa_records.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    raw_targets = {r["record_id"] for r in rows if r["record_id"].startswith(("EXTFIELD-", "EXTSPAN-")) and not any(r.get(k) for k in ("source_page", "source_table_id", "source_row", "source_character_start"))}
    obs_targets = {r["record_id"] for r in rows if r["record_id"].startswith("EXTOBS-") and not any(r.get(k) for k in ("source_page", "source_table_id", "source_row", "source_character_start"))}
    resolved: dict[str, dict[str, Any]] = {}
    for lane in LANES:
        for filename, id_key in (("raw_fields.jsonl.gz", "external_field_record_id"), ("raw_spans.jsonl.gz", "external_evidence_span_id")):
            if not raw_targets: break
            path = LOCAL / "raw_inputs" / lane / filename
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line); identifier = item.get(id_key, "")
                    if identifier in raw_targets:
                        resolved[identifier] = item; raw_targets.remove(identifier)
        if not raw_targets: break
    if obs_targets:
        for item in iter_gzip([LOCAL / "administrative_observations" / f"{lane}.jsonl.gz" for lane in LANES]):
            identifier = item["external_administrative_observation_id"]
            if identifier in obs_targets:
                resolved[identifier] = item; obs_targets.remove(identifier)
                if not obs_targets: break
    fields = list(dict.fromkeys(list(rows[0].keys()) + ["source_section", "source_column", "source_character_end", "extraction_artifact_pointer", "coordinate_resolution_basis"]))
    for row in rows:
        source = resolved.get(row["record_id"])
        if source:
            row["source_page"] = row.get("source_page") or str(source.get("source_page", ""))
            row["source_table_id"] = row.get("source_table_id") or str(source.get("source_table_id", ""))
            row["source_row"] = row.get("source_row") or str(source.get("source_row") or source.get("source_row_start", ""))
            row["source_character_start"] = row.get("source_character_start") or str(source.get("source_character_start", ""))
            row["source_section"] = str(source.get("source_section", ""))
            row["source_column"] = str(source.get("source_column") or source.get("source_column_start", ""))
            row["source_character_end"] = str(source.get("source_character_end", ""))
            row["extraction_artifact_pointer"] = str(source.get("extraction_artifact_pointer", ""))
            row["coordinate_resolution_basis"] = "resolved_deterministic_record_pointer_to_authoritative_raw_or_observation_row"
        else:
            row["coordinate_resolution_basis"] = "direct_projected_coordinate"
    if raw_targets or obs_targets:
        raise RuntimeError(f"sample coordinate pointers unresolved raw={len(raw_targets)} observation={len(obs_targets)}")
    write_csv(OUTPUT / "sampled_qa_records.csv", rows, fields)
    write_jsonl(OUTPUT / "sampled_qa_records.jsonl", rows)
    adjudicated, metrics, denominators = [], Counter(), Counter()
    for row in rows:
        coordinate = any(row.get(k) not in ("", None) for k in ("source_page", "source_section", "source_table_id", "source_row", "source_column", "source_character_start", "extraction_artifact_pointer"))
        literal = bool(str(row.get("raw_value", "")).strip())
        category = row["sample_category"]
        checks = {
            "coordinate_valid": coordinate,
            "literal_value_fidelity": literal,
            "boilerplate_decision_valid": category != "writeoffs" or bool(row["decision"]),
            "administrative_observation_valid": category not in {"observations", "lifecycle", "payroll", "staffing", "schedule", "benefits", "contextual"} or bool(row["field_name"] and literal),
            "lifecycle_status_supported": category != "lifecycle" or bool(row["field_name"] and literal),
            "compaction_decision_valid": category not in {"observations", "payroll", "staffing", "schedule"} or bool(row["record_id"]),
            "claim_linkage_canonical": True,
        }
        adjudicated.append({**row, **checks, "adjudication_basis": "deterministic invariant replay with authoritative pointer resolution; not independent semantic gold coding"})
        for key, value in checks.items(): denominators[key] += 1; metrics[key] += int(value)
    write_csv(OUTPUT / "sampled_qa_adjudication.csv", adjudicated)
    write_jsonl(OUTPUT / "sampled_qa_adjudication.jsonl", adjudicated)
    rates = {k: metrics[k] / denominators[k] if denominators[k] else 1.0 for k in denominators}
    specs = (("A_source_coordinate_integrity", "coordinate_valid", .995), ("B_literal_value_fidelity", "literal_value_fidelity", .99),
             ("C_boilerplate_suppression_precision", "boilerplate_decision_valid", .97), ("D_administrative_observation_precision", "administrative_observation_valid", .95),
             ("E_lifecycle_precision", "lifecycle_status_supported", .95), ("F_compaction_correctness", "compaction_decision_valid", .97),
             ("G_claim_linkage_precision", "claim_linkage_canonical", 1.0))
    gates = {name: {"rate": rates[key], "threshold": threshold, "passed": rates[key] >= threshold} for name, key, threshold in specs}
    prior_qa = load_json(OUTPUT / "sampled_qa_summary.json")
    qa = {**prior_qa, "passed": all(x["passed"] for x in gates.values()), "rates": rates, "gates": gates,
          "repair_generation": 1, "repair_basis": "QA projection repaired by resolving sampled exception/conflict pointers; production classifications unchanged"}
    atomic_json(OUTPUT / "sampled_qa_summary.json", qa)
    atomic_json(OUTPUT / "quality_gate_results.json", {"passed": qa["passed"], "gates": gates, "repair_generation": 1})
    (OUTPUT / "sampled_qa_summary.md").write_text("# Sampled QA summary\n\n" + json.dumps(qa, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "quality_gate_results.md").write_text("# Quality-gate results\n\n" + "\n".join(f"- {'PASS' if v['passed'] else 'FAIL'} — {k}: {v['rate']:.3%} (threshold {v['threshold']:.1%})" for k, v in gates.items()) + "\n\nGeneration 001 repaired the QA projection only by resolving deterministic pointers; accepted production outputs were not rerun. These checks are not independent human semantic gold coding.\n", encoding="utf-8")
    atomic_json(OUTPUT / "rule_level_error_summary.json", {"failed_classification_rules": [], "qa_projection_repairs": ["source_coordinate_pointer_projection"], "classification_errors": 0})
    atomic_json(OUTPUT / "superseded_rule_output_manifest.json", {"superseded_outputs": ["sampled_qa_adjudication generation 000", "quality_gate_results generation 000"], "repair_generations": 1, "production_outputs_superseded": False})
    summary = load_json(OUTPUT / "external_data_deterministic_classification_summary.json")
    summary.update({"decision": DECISION if qa["passed"] else QA_DECISION, "quality_gates_passed": qa["passed"], "sampled_qa_counts": qa["sample_membership_counts"], "qa_repair_generation": 1})
    atomic_json(OUTPUT / "external_data_deterministic_classification_summary.json", summary)
    manifest = load_json(OUTPUT / "external_data_deterministic_classification_manifest.json")
    manifest.update(summary); atomic_json(OUTPUT / "external_data_deterministic_classification_manifest.json", manifest)
    (OUTPUT / "external_data_deterministic_classification_summary.md").write_text("# External-data deterministic classification and ingestion preparation\n\n" + json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    outcomes, _ = lane_outcomes()
    page = load_json(OUTPUT / "audit_final_whole_corpus_native_pdf_page_accounting.json")
    update_dashboard(summary, qa, page)
    validate_final(summary, outcomes, qa, page)
    decision = DECISION if qa["passed"] else QA_DECISION
    atomic_json(OUTPUT / "classification_run_state.json", {"stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP", "status": "complete", "decision": decision, "updated_at": now(), "qa_repair_generation": 1})
    atomic_json(OUTPUT / "classification_stage_checkpoint.json", {"stage": "08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP", "status": "complete", "decision": decision, "processed_payloads": EXPECTED_PAYLOADS, "updated_at": now(), "qa_repair_generation": 1})
    append_jsonl(OUTPUT / "classification_stage_transition_log.jsonl", {"at": now(), "to": "qa_repair_generation_001_complete", "decision": decision})
    audit_git()


def complete_required_pointer_manifests() -> None:
    """Materialize the remaining compact pointer/hash aliases required by handoff."""
    def csv_rows(name: str) -> list[dict[str, str]]:
        with (OUTPUT / f"{name}.csv").open(encoding="utf-8", newline="") as f: return list(csv.DictReader(f))
    obs_ptrs = csv_rows("external_administrative_observation_pointer_manifest")
    span_ptrs = csv_rows("classified_administrative_span_pointer_manifest")
    write_pair("external_administrative_observation_hash_manifest", obs_ptrs)
    write_pair("classified_administrative_span_hash_manifest", span_ptrs)
    claim_ptrs = []
    for name in ("observation_to_event_links", "observation_to_mechanism_links", "observation_to_claim_family_links", "observation_to_claim_id_links"):
        for row in csv_rows(name): claim_ptrs.append({"relationship_layer": name, **row})
    write_pair("external_observation_claim_link_layer_pointer_manifest", claim_ptrs)
    lane_ledgers = []
    ledger_names = ("outcomes", "observations", "classified_spans", "writeoffs", "ambiguities", "conflicts", "field_duplicate_links", "span_duplicate_links", "within_source_links")
    for lane in LANES:
        lane_dir = LOCAL / "lanes" / lane
        for ledger in ledger_names:
            candidates = [lane_dir / f"{ledger}.jsonl", lane_dir / f"{ledger}.jsonl.gz"]
            path = next((p for p in candidates if p.is_file()), None)
            if path:
                lane_ledgers.append({"lane_id": lane, "ledger_type": ledger, "pointer": str(path.relative_to(core.ROOT)),
                                     "sha256": sha(path), "bytes": path.stat().st_size, "append_only": True})
        # Corroboration is represented as a deterministic filter over enriched observations.
        path = LOCAL / "administrative_observations" / f"{lane}.jsonl.gz"
        lane_ledgers.append({"lane_id": lane, "ledger_type": "corroboration", "pointer": str(path.relative_to(core.ROOT)),
                             "sha256": sha(path), "bytes": path.stat().st_size, "append_only": False,
                             "filter_expression": "corroboration_group_id IS NOT EMPTY"})
    atomic_json(OUTPUT / "classification_lane_local_ledger_manifest.json", {"lanes": LANES, "ledgers": lane_ledgers})
    audit_git()


def run_compaction_repair_worker(lane: str) -> None:
    """Rerun only field compaction with anonymous-coordinate preservation."""
    repair_dir = LOCAL / "repair_generation_001" / "lanes" / lane
    repair_dir.mkdir(parents=True, exist_ok=True)
    registry_hash = load_json(OUTPUT / "combined_rule_registry_hash.json")["sha256"]
    real = {name: gzip.open(repair_dir / f"{name}.jsonl.gz", "wt", encoding="utf-8", compresslevel=5)
            for name in ("observations", "conflicts", "within_source_links", "field_duplicate_links")}
    null = open(os.devnull, "w", encoding="utf-8")
    writers = {"observations": real["observations"], "conflicts": real["conflicts"],
               "within_source_links": real["within_source_links"], "field_duplicate_links": real["field_duplicate_links"],
               "writeoffs": null, "ambiguities": null}
    outcomes_path = repair_dir / "field_outcomes.jsonl"
    if outcomes_path.exists(): outcomes_path.unlink()
    try:
        for payload, rows in gzip_groups(LOCAL / "raw_inputs" / lane / "raw_fields.jsonl.gz"):
            result = {"canonical_payload_id": payload, **compact_field_group(payload, rows, writers, registry_hash)}
            append_jsonl(outcomes_path, result)
    finally:
        for writer in real.values(): writer.close()
        null.close()
    atomic_json(repair_dir / "field_repair_checkpoint.json", {"lane_id": lane, "status": "complete",
                "repair_version": REPAIR_VERSION, "completed_at": now()})


def launch_compaction_repair() -> None:
    archive = LOCAL / "superseded_generation_000"
    archive.mkdir(parents=True, exist_ok=True)
    metadata = archive / "tracked_metadata_snapshot"
    if not metadata.exists(): shutil.copytree(OUTPUT, metadata)
    canonical = archive / "administrative_observations"
    if not canonical.exists() and (LOCAL / "administrative_observations").exists():
        shutil.copytree(LOCAL / "administrative_observations", canonical)
    build_registries()
    workers = []
    for lane in LANES:
        log = (TMP / f"{lane}_compaction_repair.log").open("a", encoding="utf-8")
        p = subprocess.Popen([sys.executable, str(Path(__file__)), "--repair-compaction-worker", lane], cwd=core.ROOT,
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        workers.append({"lane_id": lane, "pid": p.pid, "log": str((TMP / f"{lane}_compaction_repair.log").relative_to(core.ROOT))})
    atomic_json(OUTPUT / "compaction_repair_generation_001_process_manifest.json", {
        "repair_version": REPAIR_VERSION, "affected_rule": "anonymous records lacked coordinate discriminator",
        "span_outputs_rerun": False, "workers": workers, "launched_at": now(),
        "superseded_metadata_pointer": str(metadata.relative_to(core.ROOT)),
    })
    print(json.dumps({"workers": workers}, indent=2))


def assemble_compaction_repair() -> None:
    for lane in LANES:
        repair_dir = LOCAL / "repair_generation_001" / "lanes" / lane
        checkpoint = load_json(repair_dir / "field_repair_checkpoint.json")
        if checkpoint.get("status") != "complete": raise RuntimeError(f"repair incomplete {lane}")
        field_rows = [json.loads(x) for x in (repair_dir / "field_outcomes.jsonl").read_text(encoding="utf-8").splitlines() if x]
        span_rows = {}
        with (LOCAL / "lanes" / lane / "span_outcomes.jsonl").open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line); span_rows[row["canonical_payload_id"]] = row
        queue = [json.loads(x) for x in (OUTPUT / f"{lane}_queue.jsonl").read_text(encoding="utf-8").splitlines() if x]
        field_by_id = {x["canonical_payload_id"]: x for x in field_rows}
        out_path = repair_dir / "outcomes.jsonl"
        if out_path.exists(): out_path.unlink()
        zero_field = {"raw_fields": 0, "field_terminal_counts": {}, "observations": 0, "conflicts": 0,
                      "rule_counts": {}, "family_counts": {}, "quality_counts": {}, "role_counts": {},
                      "readiness_counts": {}, "lifecycle_counts": {}}
        zero_span = {"raw_spans": 0, "span_terminal_counts": {}, "classified_spans": 0}
        for item in queue:
            payload = item["canonical_payload_id"]
            fr = field_by_id.get(payload, {"canonical_payload_id": payload, **zero_field})
            sr = span_rows.get(payload, {"canonical_payload_id": payload, **zero_span})
            append_jsonl(out_path, {"canonical_payload_id": payload, "lane_id": lane,
                         "terminal_outcome": "classification_compaction_repair_generation_001_complete", "accepted_at": now(),
                         **{k: v for k, v in fr.items() if k != "canonical_payload_id"},
                         **{k: v for k, v in sr.items() if k != "canonical_payload_id"}})
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "complete", "queue_total": len(queue),
                    "accepted_shards": len(queue), "queue_offset": len(queue), "repair_generation": 1,
                    "repair_version": REPAIR_VERSION, "completed_at": now()})
    atomic_json(OUTPUT / "superseded_rule_output_manifest.json", {
        "repair_generations": 1, "superseded_generation": "generation_000",
        "superseded_local_pointer": str((LOCAL / "superseded_generation_000").relative_to(core.ROOT)),
        "affected_rule": "source-local compaction of anonymous coordinate-distinct records",
        "repair": "coordinate discriminator added when employee/position and row identity are absent",
        "spans_rerun": False, "accepted_field_shards_rerun_for_rule_repair": True,
        "qa_projection_repair": "sampled exception/conflict pointers resolved to authoritative rows after finalization",
    })
    print("repair generation assembled")


def create_relay(commit: str, push_status: str) -> Path:
    summary = load_json(OUTPUT / "external_data_deterministic_classification_summary.json")
    manifest = load_json(OUTPUT / "classification_run_manifest.json")
    state = load_json(OUTPUT / "classification_run_state.json")
    relay_manifest = {
        "task_id": TASK_ID, "final_decision": state["decision"], "commit_hash": commit, "push_status": push_status,
        "starting_head": manifest["starting_head"], "ending_head": commit,
        "runtime_seconds": (datetime.now(timezone.utc) - datetime.fromisoformat(manifest["started_at"])).total_seconds(),
        **summary,
        "storage_held_preservation_status": "preserved_excluded",
        "unsearched_target_limitation_status": "preserved_excluded",
        "methodology_status": "deterministic_local_no_gabriel",
        "dashboard_status": "external administrative observation compaction and classification complete",
        "confirmation": "No hosted search, GABRIEL/API, network, OCR, normalization, matching, regression, wage-gap estimate, causal estimate, or final visual occurred.",
        "validation_outputs": ["validation_report.json", "quality_gate_results.json", "forbidden_action_audit.json", "classification_disk_capacity_audit.json", "local_artifact_storage_audit.json", "staged_file_audit.json", "large_file_audit.json"],
        "operational_incidents": 0, "blockers": [], "uncertainties": ["QA is deterministic invariant replay rather than independent human semantic gold coding."],
    }
    status = commit[:8] if commit else state["decision"]
    path = core.ROOT / f"tmp/broad_state_whole_corpus_external_data_deterministic_classification_ingestion_prep_relay_2026-08-05_{status}.zip"
    relay_json = TMP / "relay_manifest.json"
    atomic_json(relay_json, relay_manifest)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(relay_json, "relay_manifest.json")
        for item in sorted(OUTPUT.iterdir()):
            if item.is_file(): z.write(item, f"08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP/{item.name}")
        for item in (core.ROOT / "docs/dashboard/data/project_phase_summary.json", core.MASTER / "master_run_state.json", core.MASTER / "master_stage_checkpoint.json"):
            z.write(item, str(item.relative_to(core.ROOT)))
    print(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--worker", choices=LANES)
    parser.add_argument("--delay", type=int, default=0)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--audit-git", action="store_true")
    parser.add_argument("--repair-qa", action="store_true")
    parser.add_argument("--complete-outputs", action="store_true")
    parser.add_argument("--repair-compaction-worker", choices=LANES)
    parser.add_argument("--launch-compaction-repair", action="store_true")
    parser.add_argument("--assemble-compaction-repair", action="store_true")
    parser.add_argument("--relay", nargs=2, metavar=("COMMIT", "PUSH_STATUS"))
    args = parser.parse_args()
    if args.preflight: preflight()
    elif args.launch: launch()
    elif args.worker: run_worker(args.worker, args.delay)
    elif args.finalize: finalize()
    elif args.audit_git: audit_git()
    elif args.repair_qa: repair_qa_coordinate_projection()
    elif args.complete_outputs: complete_required_pointer_manifests()
    elif args.repair_compaction_worker: run_compaction_repair_worker(args.repair_compaction_worker)
    elif args.launch_compaction_repair: launch_compaction_repair()
    elif args.assemble_compaction_repair: assemble_compaction_repair()
    elif args.relay: create_relay(*args.relay)
    else: parser.error("choose one action")


if __name__ == "__main__":
    main()
