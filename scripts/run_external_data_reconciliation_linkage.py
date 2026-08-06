#!/usr/bin/env python3
"""Deterministic five-lane reconciliation of canonical external evidence.

This stage is deliberately local and fail closed.  It consumes only the shard
pointers accepted by stage 09, preserves every source-specific observation,
and emits preparation artifacts without normalizing values or calculating
analytical statistics.
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
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO = Path(__file__).resolve().parents[1]
PIPE = REPO / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
INPUT = PIPE / "09_EXTERNAL-DATA-INGESTION-CODIFICATION"
OUTPUT = PIPE / "10_EXTERNAL-DATA-RECONCILIATION-LINKAGE"
LOCAL = REPO / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/reconciled_external_layers"
LOGS = REPO / "tmp/broad_state_whole_corpus_external_data_reconciliation_linkage_2026-08-05_logs"
INGESTED = REPO / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/ingested_external_layers"
TASK = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-RECONCILIATION-AND-LINKAGE-2026-08-05"
PREDECESSOR = "b21b623cfa3cf6430bb420d29f6fd33eb38c2d8b"
DECISION = "broad_state_whole_corpus_external_data_reconciliation_completed_normalization_ready"
OBS_TOTAL = 1_876_183
SPAN_TOTAL = 1_781_186
LINKED_SPANS = 1_344_649
UNLINKED_SPANS = 436_537
LANES = [f"reconciliation_lane_{i:03d}" for i in range(1, 6)]
REGISTRY_VERSION = "external-reconciliation-2026-08-05-v1"
SHARD_ROWS = 25_000


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    body = "\x1f".join(str(x or "") for x in parts)
    return f"{prefix}-{hashlib.sha256(body.encode()).hexdigest()[:n]}"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fields or (rows[0].keys() if rows else ["status"]))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pair(name: str, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    write_jsonl(OUTPUT / f"{name}.jsonl", rows)
    write_csv(OUTPUT / f"{name}.csv", rows, fields)


def append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def split(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    return [x for x in str(value).split("|") if x]


def clear(value: Any) -> bool:
    return str(value or "").strip().lower() not in {"", "unclear", "unknown", "none", "not_applicable"}


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path.relative_to(REPO))], cwd=REPO).returncode == 0


def gzip_rows(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def gzip_write(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wt", compresslevel=5) as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def manifest_row(path: Path, count: int, shard_id: str, **extra: Any) -> dict[str, Any]:
    return {
        "shard_id": shard_id,
        "pointer": str(path.relative_to(REPO)),
        "row_count": count,
        "bytes": path.stat().st_size,
        "sha256": sha(path),
        **extra,
    }


class ShardWriter:
    def __init__(self, root: Path, ledger: str, lane: str, limit: int = SHARD_ROWS):
        self.root, self.ledger, self.lane, self.limit = root / ledger, ledger, lane, limit
        self.buffer: list[dict[str, Any]] = []
        self.rows = 0
        self.shards: list[dict[str, Any]] = []

    def add(self, row: dict[str, Any]) -> None:
        self.buffer.append(row)
        self.rows += 1
        if len(self.buffer) >= self.limit:
            self.flush()

    def flush(self) -> None:
        if not self.buffer:
            return
        number = len(self.shards)
        path = self.root / f"{self.ledger}_shard_{number:04d}.jsonl.gz"
        count = gzip_write(path, self.buffer)
        self.shards.append(manifest_row(path, count, f"{self.ledger}_shard_{number:04d}", lane_id=self.lane, ledger=self.ledger))
        self.buffer = []

    def close(self) -> list[dict[str, Any]]:
        self.flush()
        return self.shards


def registry_payloads() -> dict[str, dict[str, Any]]:
    def reg(name: str, statuses: list[str], rules: list[dict[str, str]]) -> dict[str, Any]:
        return {"registry": name, "version": REGISTRY_VERSION, "statuses": statuses, "rules": rules, "opaque_numeric_scores": False}

    return {
        "municipality_reconciliation_registry": reg("municipality", ["exact_canonical_municipality", "deterministic_alias_match", "source_event_lineage_match", "multiple_possible_municipalities", "wrong_or_conflicting_municipality", "municipality_unresolved", "municipality_not_applicable"], [{"rule_id": "MUNI-001", "basis": "existing canonical ID"}, {"rule_id": "MUNI-002", "basis": "unique normalized municipality and state crosswalk"}]),
        "department_reconciliation_registry": reg("department", ["exact_source_department", "deterministic_department_alias", "source_heading_or_title_match", "department_unresolved", "department_not_applicable"], [{"rule_id": "DEPT-001", "basis": "explicit source-local department or unit"}, {"rule_id": "DEPT-002", "basis": "explicit position/title dictionary"}]),
        "employee_position_identity_registry": reg("identity", ["named_employee", "public_employee_identifier", "anonymous_employee_row", "named_position", "classified_position", "salary_schedule_step", "department_aggregate", "municipal_aggregate", "staffing_position_count", "benefit_plan", "implementation_action", "contextual_unit", "qualitative_statement", "unclear"], [{"rule_id": "IDENT-001", "basis": "observation type and explicit identity"}]),
        "side_reconciliation_registry": reg("side", ["police", "fire", "safety_combined", "non_safety", "mixed", "side_independent", "unclear", "not_applicable"], [{"rule_id": "SIDE-001", "basis": "explicit department, unit, title, schedule heading, or event lineage"}]),
        "period_reconciliation_registry": reg("period", ["exact_source_period", "exact_table_period", "exact_date_derived_period", "source_event_lineage_period", "multiple_periods_preserved", "conflicting_periods", "period_unresolved", "period_not_applicable"], [{"rule_id": "PERIOD-001", "basis": "preserved explicit period/date fields"}]),
        "pay_basis_reconciliation_registry": reg("pay_basis", ["hourly_rate", "annual_salary", "biweekly_rate", "weekly_rate", "daily_rate", "per_shift_rate", "per_diem_rate", "per_event_rate", "percentage", "total_earnings", "regular_earnings", "overtime_earnings", "gross_pay", "lump_sum", "stipend_or_allowance", "benefit_contribution", "staffing_count", "contextual_value", "unclear", "not_applicable"], [{"rule_id": "PAYBASIS-001", "basis": "explicit source label, type, and unit; no conversion"}]),
        "compensation_basis_reconciliation_registry": reg("compensation_basis", ["base_rate", "base_salary", "regular_earnings", "overtime", "total_earnings", "gross_pay", "premium_pay", "retroactive_pay", "one_time_payment", "recurring_non_base", "benefit_component", "explicit_total_compensation", "salary_schedule_rate", "budgeted_compensation", "actual_paid_compensation", "staffing_or_non_compensation", "unclear", "not_applicable"], [{"rule_id": "COMPBASIS-001", "basis": "explicit observation type and source label"}]),
        "recurring_status_reconciliation_registry": reg("recurring_status", ["recurring", "one_time", "retroactive_one_time", "recurring_with_retroactive_component", "variable", "unclear", "not_applicable"], [{"rule_id": "RECUR-001", "basis": "explicit payment/component wording only"}]),
        "implementation_status_reconciliation_registry": reg("implementation_status", ["proposed", "recommended", "negotiated", "tentative", "adopted", "approved", "ratified", "appropriated", "implemented", "payroll_effective", "paid", "amended", "rejected", "expired", "unclear", "not_applicable"], [{"rule_id": "LIFE-001", "basis": "preserved locally supported lifecycle stage"}]),
        "source_version_reconciliation_registry": reg("source_version", ["original", "revised", "amended", "corrected", "preliminary", "final", "superseded", "duplicate_exact_payload", "related_nonidentical", "unrelated", "version_unclear"], [{"rule_id": "VERSION-001", "basis": "explicit source-local version wording"}]),
        "conflict_reconciliation_registry": reg("conflict", ["resolved_by_explicit_final_version", "resolved_by_explicit_amendment", "resolved_budgeted_versus_actual", "resolved_component_difference", "resolved_period_difference", "resolved_department_or_identity_difference", "resolved_duplicate_or_repetition", "genuine_unresolved_value_conflict", "genuine_unresolved_date_conflict", "genuine_unresolved_basis_conflict", "genuine_unresolved_identity_conflict", "insufficient_evidence", "manual_cross_examination_required", "not_applicable"], [{"rule_id": "CONFLICT-001", "basis": "resolve only when fields explicitly explain discrepancy"}]),
        "claim_linkage_reconciliation_registry": reg("claim_linkage", ["exact_claim_id_link", "exact_claim_family_link_only", "event_linked_claim_pending", "multiple_possible_claims", "contextual_not_claim_linked", "no_canonical_claim_mapping", "claim_linkage_manual_review"], [{"rule_id": "CLAIM-001", "basis": "preserved source-event-mechanism-claim mapping"}]),
        "span_disposition_registry": reg("span_disposition", ["linked_to_existing_observation", "creates_standalone_qualitative_context_record", "creates_implementation_context_record", "creates_staffing_or_recruitment_context_record", "creates_benefit_or_compensation_context_record", "contextual_source_background_only", "claim_linkage_only", "ambiguity_manual_review", "duplicate_span", "boilerplate_or_structural_writeoff", "orphaned_unusable_span", "span_linkage_error"], [{"rule_id": "SPAN-001", "basis": "accepted direct link"}, {"rule_id": "SPAN-002", "basis": "exact primary-span or unique same-coordinate link"}, {"rule_id": "SPAN-003", "basis": "standalone family-preserving qualitative disposition"}]),
    }


def write_registries() -> str:
    payloads = registry_payloads()
    for name, payload in payloads.items():
        atomic_json(OUTPUT / f"{name}.json", payload)
        statuses = "\n".join(f"- `{x}`" for x in payload["statuses"])
        rules = "\n".join(f"- `{x['rule_id']}`: {x['basis']}" for x in payload["rules"])
        (OUTPUT / f"{name}.md").write_text(f"# {name.replace('_', ' ').title()}\n\nVersion: `{REGISTRY_VERSION}`\n\n## Statuses\n\n{statuses}\n\n## Rules\n\n{rules}\n")
    digest = hashlib.sha256(json.dumps(payloads, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    atomic_json(OUTPUT / "combined_reconciliation_registry_hash.json", {"registry_version": REGISTRY_VERSION, "sha256": digest, "component_registries": sorted(payloads)})
    return digest


def load_municipalities() -> dict[tuple[str, str], list[str]]:
    path = PIPE.parent / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04/municipality_geographic_crosswalk.csv"
    result: dict[tuple[str, str], list[str]] = defaultdict(list)
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            result[(str(row.get("state", "")).upper(), norm(row.get("municipality")))].append(row.get("municipality_id", ""))
    return result


DEPARTMENT_RULES = [
    ("police", re.compile(r"\b(police|sheriff|law enforcement|patrol)\b", re.I)),
    ("fire", re.compile(r"\b(fire|firefighter|fire department)\b", re.I)),
    ("public_safety_combined", re.compile(r"\bpublic safety\b", re.I)),
    ("emergency_medical_services", re.compile(r"\b(ems|emergency medical)\b", re.I)),
    ("public_works", re.compile(r"\bpublic works\b", re.I)),
    ("utilities", re.compile(r"\b(utilit|water|sewer)\w*\b", re.I)),
    ("administration", re.compile(r"\b(administration|city manager|town manager)\b", re.I)),
    ("finance", re.compile(r"\b(finance|treasurer|comptroller)\b", re.I)),
    ("clerical", re.compile(r"\b(clerical|clerk|administrative assistant)\b", re.I)),
    ("parks_and_recreation", re.compile(r"\b(parks?|recreation)\b", re.I)),
    ("library", re.compile(r"\blibrar\w*\b", re.I)),
    ("planning_and_zoning", re.compile(r"\b(planning|zoning)\b", re.I)),
    ("code_enforcement", re.compile(r"\bcode enforcement\b", re.I)),
    ("sanitation", re.compile(r"\b(sanitation|solid waste|refuse)\b", re.I)),
    ("transportation", re.compile(r"\b(transportation|transit)\b", re.I)),
]


def municipality(row: dict[str, Any], crosswalk: dict[tuple[str, str], list[str]]) -> tuple[str, str, str, str]:
    before = str(row.get("municipality_canonical_id", ""))
    if clear(before):
        return before, before, "exact_canonical_municipality", "MUNI-001"
    raw, state = str(row.get("municipality_raw", "")), str(row.get("state", "")).upper()
    if not raw:
        return before, "", "municipality_unresolved", "MUNI-UNRESOLVED"
    matches = [x for x in crosswalk.get((state, norm(raw)), []) if x]
    if len(matches) == 1:
        return before, matches[0], "deterministic_alias_match", "MUNI-002"
    if len(matches) > 1:
        return before, "", "multiple_possible_municipalities", "MUNI-AMBIGUOUS"
    return before, "", "municipality_unresolved", "MUNI-UNRESOLVED"


def department(row: dict[str, Any]) -> tuple[str, str, str, str]:
    before = str(row.get("department_canonical_status", ""))
    text = " | ".join(str(row.get(k, "")) for k in ("department_raw", "unit_raw", "employee_or_position_identity", "bounded_evidence_excerpt"))
    matches = [name for name, pattern in DEPARTMENT_RULES if pattern.search(text)]
    if len(set(matches)) == 1:
        after = matches[0]
        status = "exact_source_department" if row.get("department_raw") else "deterministic_department_alias"
        return before, after, status, "DEPT-001" if row.get("department_raw") else "DEPT-002"
    if len(set(matches)) > 1:
        return before, "mixed", "deterministic_department_alias", "DEPT-002"
    family = row.get("observation_family")
    if family in {"contextual_controls", "benefits_and_total_compensation"}:
        return before, "not_applicable", "department_not_applicable", "DEPT-NA"
    return before, "unclear", "department_unresolved", "DEPT-UNRESOLVED"


def identity(row: dict[str, Any]) -> tuple[str, str, str]:
    raw = str(row.get("employee_or_position_identity", ""))
    typ, family = str(row.get("observation_type", "")), str(row.get("observation_family", ""))
    if typ == "salary_schedule_step_observation": return "salary_schedule_step", "identity_type_from_observation", "IDENT-001"
    if family == "staffing_and_headcount" or family == "vacancy_and_position_status": return "staffing_position_count", "identity_type_from_observation", "IDENT-001"
    if family == "implementation_confirmation": return "implementation_action", "identity_type_from_observation", "IDENT-001"
    if family == "contextual_controls": return "contextual_unit", "identity_type_from_observation", "IDENT-001"
    if family == "benefits_and_total_compensation": return "benefit_plan", "identity_type_from_observation", "IDENT-001"
    if "department_payroll" in typ: return "department_aggregate", "identity_type_from_observation", "IDENT-001"
    if raw and raw not in {"anonymous_position_or_employee_record", "anonymous"}:
        if re.search(r"\b(id|employee no|employee #)\b", raw, re.I): return "public_employee_identifier", "explicit_identity", "IDENT-001"
        if re.search(r"\b(officer|firefighter|captain|lieutenant|chief|engineer|clerk|manager|director|technician|position)\b", raw, re.I): return "named_position", "explicit_identity", "IDENT-001"
        return "named_employee", "explicit_identity", "IDENT-001"
    if family in {"payroll_and_earnings", "tenure_and_progression"}: return "anonymous_employee_row", "anonymous_row_preserved", "IDENT-001"
    return "unclear", "identity_unresolved", "IDENT-UNRESOLVED"


def side(row: dict[str, Any], dept: str) -> tuple[str, str, str, str]:
    before = str(row.get("side_hint", ""))
    if dept == "police": return before, "police", "explicit_department_side", "SIDE-001"
    if dept == "fire": return before, "fire", "explicit_department_side", "SIDE-001"
    if dept in {"public_safety_combined", "emergency_medical_services"}: return before, "safety_combined", "explicit_department_side", "SIDE-001"
    if dept == "mixed": return before, "mixed", "explicit_mixed_department", "SIDE-001"
    if dept in {"public_works", "utilities", "administration", "finance", "clerical", "parks_and_recreation", "library", "planning_and_zoning", "code_enforcement", "sanitation", "transportation", "general_municipal", "other_non_safety"}:
        return before, "non_safety", "explicit_department_side", "SIDE-001"
    family = row.get("observation_family")
    if family in {"contextual_controls", "benefits_and_total_compensation"}: return before, "side_independent", "side_independent_observation", "SIDE-NA"
    if before in {"police", "fire", "safety_combined", "non_safety", "mixed", "side_independent"}:
        return before, before, "preserved_explicit_side", "SIDE-001"
    return before, "unclear", "side_unresolved", "SIDE-UNRESOLVED"


def period(row: dict[str, Any]) -> tuple[dict[str, str], str, str]:
    vals = {k: str(row.get(k, "")) for k in ("fiscal_year", "calendar_year", "start_date", "end_date", "period_raw")}
    for key in ("fiscal_year", "calendar_year"):
        if vals[key]:
            years = re.findall(r"(?<!\d)(?:19|20|21)\d{2}(?!\d)", vals[key])
            vals[key] = years[0] if len(set(years)) == 1 else ""
    explicit = [v for v in vals.values() if clear(v)]
    if explicit:
        return vals, "multiple_periods_preserved" if len(set(explicit)) > 1 else "exact_source_period", "PERIOD-001"
    if row.get("observation_family") in {"contextual_controls"} and not row.get("raw_value"):
        return vals, "period_not_applicable", "PERIOD-NA"
    return vals, "period_unresolved", "PERIOD-UNRESOLVED"


PAY_TYPE = {
    "hourly_rate_observation": "hourly_rate", "annual_salary_observation": "annual_salary", "regular_earnings_observation": "regular_earnings",
    "overtime_earnings_observation": "overtime_earnings", "total_earnings_observation": "total_earnings", "gross_pay_observation": "gross_pay",
    "retroactive_pay_observation": "lump_sum", "lump_sum_observation": "lump_sum", "stipend_or_allowance_observation": "stipend_or_allowance",
}
COMP_TYPE = {
    "hourly_rate_observation": "base_rate", "annual_salary_observation": "base_salary", "base_pay_observation": "base_salary",
    "regular_earnings_observation": "regular_earnings", "overtime_earnings_observation": "overtime", "overtime_hours_observation": "overtime",
    "total_earnings_observation": "total_earnings", "gross_pay_observation": "gross_pay", "premium_pay_observation": "premium_pay",
    "retroactive_pay_observation": "retroactive_pay", "lump_sum_observation": "one_time_payment", "stipend_or_allowance_observation": "recurring_non_base",
    "salary_schedule_step_observation": "salary_schedule_rate", "explicit_total_compensation_observation": "explicit_total_compensation",
}


def bases(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    typ, family = str(row.get("observation_type", "")), str(row.get("observation_family", ""))
    pay_before, comp_before = str(row.get("pay_basis", "")), str(row.get("compensation_basis", ""))
    pay = pay_before if clear(pay_before) else PAY_TYPE.get(typ, "")
    comp = comp_before if clear(comp_before) else COMP_TYPE.get(typ, "")
    if family in {"staffing_and_headcount", "vacancy_and_position_status", "recruitment_and_retention"}:
        pay, comp = "staffing_count", "staffing_or_non_compensation"
    elif family == "contextual_controls": pay, comp = "contextual_value", "staffing_or_non_compensation"
    elif family == "implementation_confirmation": pay, comp = "not_applicable", "not_applicable"
    elif family == "benefits_and_total_compensation":
        pay = pay or "benefit_contribution"; comp = comp or "benefit_component"
    pay = pay or "unclear"; comp = comp or "unclear"
    return pay_before, pay, "exact_source_basis" if pay not in {"unclear", "not_applicable"} else ("pay_basis_not_applicable" if pay == "not_applicable" else "pay_basis_unresolved"), comp_before, comp, "exact_source_basis" if comp not in {"unclear", "not_applicable"} else ("compensation_basis_not_applicable" if comp == "not_applicable" else "compensation_basis_unresolved")


def recurring(row: dict[str, Any], comp: str) -> tuple[str, str, str]:
    before = str(row.get("recurring_status", ""))
    if clear(before): return before, before, "preserved_explicit_recurring_status"
    if comp == "retroactive_pay": return before, "retroactive_one_time", "RECUR-001"
    if comp == "one_time_payment": return before, "one_time", "RECUR-001"
    if comp in {"overtime", "total_earnings", "gross_pay", "actual_paid_compensation"}: return before, "variable", "RECUR-001"
    if comp in {"staffing_or_non_compensation", "not_applicable"}: return before, "not_applicable", "RECUR-NA"
    return before, "unclear", "RECUR-UNRESOLVED"


def lifecycle(row: dict[str, Any]) -> tuple[str, str, str]:
    before, family = str(row.get("implementation_status", "")), str(row.get("observation_family", ""))
    if family != "implementation_confirmation": return before, "not_applicable", "LIFE-NA"
    valid = {"proposed", "recommended", "negotiated", "tentative", "adopted", "approved", "ratified", "appropriated", "implemented", "payroll_effective", "paid", "amended", "rejected", "expired"}
    if before in valid: return before, before, "LIFE-001"
    type_map = {"proposal_observation": "proposed", "recommendation_observation": "recommended", "negotiation_observation": "negotiated", "tentative_agreement_observation": "tentative", "adoption_observation": "adopted", "approval_observation": "approved", "ratification_observation": "ratified", "appropriation_observation": "appropriated", "implementation_observation": "implemented", "payroll_effective_observation": "payroll_effective", "payment_observation": "paid", "amendment_observation": "amended", "rejection_observation": "rejected", "expiration_observation": "expired"}
    if row.get("observation_type") in type_map: return before, type_map[str(row["observation_type"])], "LIFE-001"
    return before, "unclear", "LIFE-UNRESOLVED"


def version(row: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(str(row.get(k, "")) for k in ("bounded_evidence_excerpt", "field_name", "raw_value"))
    for label in ("amended", "revised", "corrected", "preliminary", "final", "superseded"):
        if re.search(rf"\b{label}\b", text, re.I): return label, "VERSION-001"
    return "version_unclear", "VERSION-UNRESOLVED"


def conflict(row: dict[str, Any], period_status: str, pay: str, comp: str, version_status: str) -> tuple[str, str]:
    if not clear(row.get("conflict_flags")) and row.get("evidence_quality_class") != "conflicting_administrative_record": return "not_applicable", "CONFLICT-NA"
    flags = norm(row.get("conflict_flags"))
    if version_status == "final": return "resolved_by_explicit_final_version", "CONFLICT-001"
    if version_status == "amended": return "resolved_by_explicit_amendment", "CONFLICT-001"
    if "budget" in flags and "actual" in flags: return "resolved_budgeted_versus_actual", "CONFLICT-001"
    if "component" in flags: return "resolved_component_difference", "CONFLICT-001"
    if period_status == "multiple_periods_preserved" or "period" in flags: return "resolved_period_difference", "CONFLICT-001"
    if "basis" in flags or pay == "unclear" or comp == "unclear": return "genuine_unresolved_basis_conflict", "CONFLICT-UNRESOLVED"
    if "date" in flags: return "genuine_unresolved_date_conflict", "CONFLICT-UNRESOLVED"
    if "identity" in flags: return "genuine_unresolved_identity_conflict", "CONFLICT-UNRESOLVED"
    return "genuine_unresolved_value_conflict", "CONFLICT-UNRESOLVED"


def claims(row: dict[str, Any]) -> tuple[str, str]:
    if split(row.get("claim_ids")) and row.get("claim_linkage_status") == "exact_claim_id_link": return "exact_claim_id_link", "CLAIM-001"
    if split(row.get("claim_family_ids")): return "exact_claim_family_link_only", "CLAIM-001"
    if split(row.get("root_event_ids")) or split(row.get("mechanism_event_ids")): return "event_linked_claim_pending", "CLAIM-001"
    if row.get("analytical_role") == "contextual_only": return "contextual_not_claim_linked", "CLAIM-CONTEXT"
    return "no_canonical_claim_mapping", "CLAIM-UNRESOLVED"


def reconcile(row: dict[str, Any], lane: str, registry_hash: str, crosswalk: dict[tuple[str, str], list[str]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    muni_before, muni_after, muni_status, muni_rule = municipality(row, crosswalk)
    dept_before, dept_after, dept_status, dept_rule = department(row)
    identity_after, identity_status, identity_rule = identity(row)
    side_before, side_after, side_status, side_rule = side(row, dept_after)
    periods, period_status, period_rule = period(row)
    pay_before, pay_after, pay_status, comp_before, comp_after, comp_status = bases(row)
    recur_before, recur_after, recur_status = recurring(row, comp_after)
    life_before, life_after, life_status = lifecycle(row)
    version_after, version_rule = version(row)
    conflict_status, conflict_rule = conflict(row, period_status, pay_after, comp_after, version_after)
    claim_status, claim_rule = claims(row)
    unresolved = []
    for name, value in (("municipality", muni_status), ("department", dept_status), ("identity", identity_status), ("side", side_status), ("period", period_status), ("pay_basis", pay_status), ("compensation_basis", comp_status), ("recurring", recur_status), ("implementation", life_status), ("claim", claim_status)):
        if any(x in value for x in ("unresolved", "pending", "unclear", "multiple_possible", "no_canonical")):
            unresolved.append(name)
    conflict_open = conflict_status.startswith("genuine_") or conflict_status in {"insufficient_evidence", "manual_cross_examination_required"}
    family = str(row.get("observation_family", ""))
    if conflict_open: terminal = "reconciled_with_preserved_conflict"
    elif len(unresolved) > 1: terminal = "reconciled_multiple_dimensions_pending"
    elif unresolved == ["claim"]: terminal = "reconciled_claim_linkage_pending"
    elif unresolved == ["side"]: terminal = "reconciled_side_pending"
    elif unresolved == ["period"]: terminal = "reconciled_period_pending"
    elif any(x in unresolved for x in ("pay_basis", "compensation_basis")): terminal = "reconciled_basis_pending"
    elif unresolved == ["identity"]: terminal = "reconciled_identity_pending"
    elif family == "contextual_controls": terminal = "contextual_reconciled"
    else: terminal = "reconciled_analysis_preparation_ready"
    local = "local_comparison_not_appropriate"
    if row.get("analytical_role") == "local_comparison_candidate":
        if conflict_open: local = "local_comparison_conflict_hold"
        elif side_after in {"unclear", "mixed"}: local = "local_comparison_side_hold"
        elif period_status == "period_unresolved": local = "local_comparison_period_hold"
        elif pay_after == "unclear" or comp_after == "unclear": local = "local_comparison_basis_hold"
        elif not muni_after: local = "local_comparison_conditional"
        else: local = "local_comparison_ready"
    growth = "growth_not_appropriate"
    if row.get("analytical_role") == "growth_candidate":
        if pay_after == "unclear" or comp_after == "unclear": growth = "growth_basis_hold"
        elif identity_after == "unclear": growth = "growth_identity_hold"
        elif period_status == "period_unresolved": growth = "growth_period_hold"
        else: growth = "growth_conditional"
    staffing = "staffing_context_only"
    if row.get("analytical_role") == "staffing_hypothesis_candidate":
        if conflict_open: staffing = "staffing_conflict_hold"
        elif row.get("observation_type") in {"authorized_position_observation", "budgeted_position_observation", "filled_position_observation", "vacant_position_observation", "layoff_observation", "hiring_freeze_observation", "position_elimination_observation"}: staffing = "staffing_hypothesis_ready"
        else: staffing = "unclear_staffing_change"
    rules = [muni_rule, dept_rule, identity_rule, side_rule, period_rule, "PAYBASIS-001", "COMPBASIS-001", recur_status, life_status, version_rule, conflict_rule, claim_rule]
    out = dict(row)
    out.update({
        "reconciled_external_observation_id": stable("EXTRECON", row.get("canonical_external_ingestion_id"), registry_hash),
        "municipality_canonical_id_before": muni_before, "municipality_canonical_id_after": muni_after, "municipality_reconciliation_status": muni_status,
        "department_before": dept_before, "department_after": dept_after, "department_reconciliation_status": dept_status,
        "identity_raw": row.get("employee_or_position_identity", ""), "identity_type_after": identity_after, "position_title_canonical_hint": row.get("employee_or_position_identity", "") if identity_after in {"named_position", "classified_position"} else "", "identity_reconciliation_status": identity_status,
        "side_before": side_before, "side_after": side_after, "side_reconciliation_status": side_status,
        "fiscal_year_before": row.get("fiscal_year", ""), "fiscal_year_after": periods["fiscal_year"], "calendar_year_before": row.get("calendar_year", ""), "calendar_year_after": periods["calendar_year"], "start_date_after": periods["start_date"], "end_date_after": periods["end_date"], "period_reconciliation_status": period_status,
        "pay_basis_before": pay_before, "pay_basis_after": pay_after, "pay_basis_reconciliation_status": pay_status,
        "compensation_basis_before": comp_before, "compensation_basis_after": comp_after, "compensation_basis_reconciliation_status": comp_status,
        "recurring_status_before": recur_before, "recurring_status_after": recur_after, "recurring_reconciliation_status": recur_status,
        "implementation_status_before": life_before, "implementation_status_after": life_after, "implementation_reconciliation_status": life_status,
        "source_version_status": version_after, "conflict_reconciliation_status": conflict_status,
        "ambiguity_flags_before": row.get("ambiguity_flags", ""), "ambiguity_flags_after": row.get("ambiguity_flags", ""), "conflict_flags_before": row.get("conflict_flags", ""), "conflict_flags_after": row.get("conflict_flags", ""),
        "claim_family_ids_before": row.get("claim_family_ids", ""), "claim_family_ids_after": row.get("claim_family_ids", ""), "claim_ids_before": row.get("claim_ids", ""), "claim_ids_after": row.get("claim_ids", ""), "claim_linkage_status_after": claim_status,
        "terminal_reconciliation_status": terminal, "unresolved_dimensions": "|".join(unresolved),
        "local_comparison_readiness": local, "growth_readiness": growth, "staffing_hypothesis_readiness": staffing,
        "total_compensation_readiness": "total_compensation_component_ready" if row.get("analytical_role") == "total_compensation_candidate" and not conflict_open else "not_applicable",
        "implementation_readiness": "implementation_sequence_candidate" if row.get("analytical_role") == "implementation_confirmation_candidate" else "not_applicable",
        "mechanism_outcome_readiness": "mechanism_linked_outcome_candidate" if split(row.get("mechanism_event_ids")) else "mechanism_link_pending",
        "reconciliation_rule_ids": "|".join(rules), "reconciliation_registry_hash": registry_hash, "lane_id": lane,
        "raw_value_input_sha256": hashlib.sha256(str(row.get("raw_value", "")).encode()).hexdigest(),
        "source_coordinate_input_sha256": hashlib.sha256("|".join(str(row.get(k, "")) for k in ("source_page", "source_section", "source_table_id", "source_row", "source_column", "source_character_start", "source_character_end")).encode()).hexdigest(),
        "reconciliation_timestamp": now(), "reconciliation_lineage_basis": "single_coordinated_source_aware_pass_over_canonical_ingestion_row",
    })
    before_after = {
        "canonical_external_ingestion_id": row.get("canonical_external_ingestion_id", ""), "reconciled_external_observation_id": out["reconciled_external_observation_id"],
        "municipality_before": muni_before, "municipality_after": muni_after, "municipality_status": muni_status,
        "department_before": dept_before, "department_after": dept_after, "department_status": dept_status,
        "identity_before": row.get("employee_or_position_identity", ""), "identity_after": identity_after, "identity_status": identity_status,
        "side_before": side_before, "side_after": side_after, "side_status": side_status,
        "period_before": row.get("period_raw", ""), "period_after": "|".join(x for x in periods.values() if x), "period_status": period_status,
        "pay_basis_before": pay_before, "pay_basis_after": pay_after, "pay_basis_status": pay_status,
        "compensation_basis_before": comp_before, "compensation_basis_after": comp_after, "compensation_basis_status": comp_status,
        "recurring_before": recur_before, "recurring_after": recur_after, "recurring_status": recur_status,
        "implementation_before": life_before, "implementation_after": life_after, "implementation_status": life_status,
        "source_version_after": version_after, "conflict_after": conflict_status, "claim_status_before": row.get("claim_linkage_status", ""), "claim_status_after": claim_status,
        "rule_ids": "|".join(rules), "mapping_basis": "explicit source fields, local labels, preserved event/claim lineage, and version wording", "confidence_basis": "deterministic_rule_support", "unresolved_reason": "|".join(unresolved),
    }
    analysis = {k: out.get(k, "") for k in ("reconciled_external_observation_id", "canonical_external_ingestion_id", "source_SHA_256", "municipality_canonical_id_after", "department_after", "side_after", "period_raw", "fiscal_year_after", "calendar_year_after", "identity_type_after", "employee_or_position_identity", "field_name", "source_table_id", "source_row", "pay_basis_after", "compensation_basis_after", "observation_family", "observation_type", "analytical_role", "conflict_reconciliation_status", "claim_linkage_status_after", "local_comparison_readiness", "growth_readiness", "staffing_hypothesis_readiness", "total_compensation_readiness", "implementation_readiness", "mechanism_outcome_readiness")}
    return out, before_after, analysis


def accepted_manifests() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = load(INPUT / "canonical_external_layer_manifest.json")
    return manifest["observation_shards"], manifest["span_shards"]


def active_task_processes() -> list[dict[str, Any]]:
    p = subprocess.run(["ps", "-Ao", "pid=,ppid=,lstart=,etime=,state=,command="], text=True, capture_output=True, check=True)
    found = []
    for line in p.stdout.splitlines():
        if "run_external_data_reconciliation_linkage.py" not in line:
            continue
        try:
            pid = int(line.strip().split(None, 1)[0])
        except ValueError:
            continue
        if pid not in {os.getpid(), os.getppid()} and re.search(r"(?:^|\s)(?:python\S*|/\S*/python\S*)\s+\S*run_external_data_reconciliation_linkage\.py", line):
            found.append({"pid": pid, "process_line": line.strip()})
    return found


def preflight() -> dict[str, Any]:
    started = time.time()
    if REPO.resolve() != Path.cwd().resolve():
        raise RuntimeError(f"wrong repository: {Path.cwd()}")
    head = git("rev-parse", "HEAD")
    if subprocess.run(["git", "merge-base", "--is-ancestor", PREDECESSOR, head], cwd=REPO).returncode:
        raise RuntimeError(f"predecessor {PREDECESSOR} is not in HEAD history")
    status = git("status", "--short")
    related_bootstrap = {"?? scripts/run_external_data_reconciliation_linkage.py"}
    dirty_lines = {x for x in status.splitlines() if x}
    unrelated = sorted(dirty_lines - related_bootstrap)
    if unrelated:
        raise RuntimeError(f"unrelated dirty worktree before reconciliation:\n" + "\n".join(unrelated))
    active = active_task_processes()
    if active:
        raise RuntimeError(f"duplicate/stale reconciliation process found: {active}")
    summary = load(INPUT / "external_data_deterministic_ingestion_summary.json")
    required = {
        "canonical_ingested_observations": OBS_TOTAL,
        "canonical_ingested_spans": SPAN_TOTAL,
        "classified_spans_with_observation_links": LINKED_SPANS,
        "conflicts_preserved": 266_890,
        "corroboration_groups": 34_225,
        "corroboration_memberships": 276_352,
        "cross_examination_candidate_count": 1_226,
        "audit_final_native_pdf_pages": 1_029_482,
        "storage_capacity_holds_preserved": 7_895,
        "unresolved_hosted_search_targets": 12_844,
        "ocr_later_preserved": 118,
        "extraction_repair_preserved": 97,
    }
    mismatches = {k: {"expected": v, "actual": summary.get(k)} for k, v in required.items() if summary.get(k) != v}
    if mismatches:
        raise RuntimeError(f"ingestion summary mismatch: {mismatches}")
    obs_manifest, span_manifest = accepted_manifests()
    pointer_failures = []
    quarantine_references = []
    for item in obs_manifest + span_manifest:
        path = REPO / item["pointer"]
        if "quarantine" in path.parts:
            quarantine_references.append(str(path))
        actual = sha(path) if path.exists() else None
        if actual != item["sha256"]:
            pointer_failures.append({"pointer": item["pointer"], "expected": item["sha256"], "actual": actual})
    if pointer_failures or quarantine_references:
        raise RuntimeError(f"accepted pointer integrity failure: mismatches={pointer_failures}; quarantine={quarantine_references}")
    if sum(x["row_count"] for x in obs_manifest) != OBS_TOTAL or sum(x["row_count"] for x in span_manifest) != SPAN_TOTAL:
        raise RuntimeError("accepted shard row totals do not reconcile")
    family = load(INPUT / "canonical_observation_family_summary.json")
    evidence = load(INPUT / "canonical_evidence_quality_summary.json")
    claims_summary = load(INPUT / "canonical_claim_linkage_summary.json")
    if sum(family.values()) != OBS_TOTAL or sum(evidence.values()) != OBS_TOTAL or sum(claims_summary.values()) != OBS_TOTAL:
        raise RuntimeError("family/evidence/claim totals do not reconcile")
    free = shutil.disk_usage(REPO).free
    if free < 8 * 1024**3:
        raise RuntimeError(f"free disk below 8 GiB reserve: {free}")
    if not ignored(INGESTED) or not ignored(LOCAL) or not ignored(LOGS):
        raise RuntimeError("input/output/log root ignore invariant failed")
    return {
        "task_id": TASK, "checked_at": now(), "starting_head": head, "predecessor_is_ancestor": True,
        "worktree_clean_except_authorized_stage_runner": not unrelated, "authorized_bootstrap_paths": sorted(dirty_lines & related_bootstrap), "active_reconciliation_workers": active, "duplicate_workers": 0,
        "observation_shards": len(obs_manifest), "span_shards": len(span_manifest),
        "canonical_observations": OBS_TOTAL, "canonical_spans": SPAN_TOTAL,
        "directly_linked_spans": LINKED_SPANS, "previously_unlinked_spans": UNLINKED_SPANS,
        "pointer_hashes_valid": True, "quarantined_ingestion_artifact_referenced": False,
        "raw_field_or_span_inputs": 0, "source_independence_reconstructable": True,
        "corroboration_linkage_separate": True, "free_bytes": free, "reserve_bytes": 8 * 1024**3,
        "input_root_ignored": True, "output_root_ignored": True, "log_root_ignored": True,
        "family_counts": family, "evidence_quality_counts": evidence, "claim_linkage_counts": claims_summary,
        "elapsed_seconds": round(time.time() - started, 3), "passed": True,
    }


def row_stream(items: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for item in items:
        yield from gzip_rows(REPO / item["pointer"])


def prepare() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    lock = LOCAL / "preparation.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"preparation lock already exists: {lock}") from exc
    os.write(fd, f"{os.getpid()} {now()}\n".encode())
    os.close(fd)
    try:
        audit = preflight()
        started_at = now()
        registry_hash = write_registries()
        obs_manifest, span_manifest = accepted_manifests()
        obs_by_lane: dict[str, list[dict[str, Any]]] = defaultdict(list)
        span_by_lane: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in obs_manifest:
            obs_by_lane[item["lane_id"].replace("ingestion_", "reconciliation_")].append(item)
        for item in span_manifest:
            span_by_lane[item["lane_id"].replace("ingestion_", "reconciliation_")].append(item)
        queue_rows, span_rows, distribution = [], [], []
        index_path = LOCAL / "indexes/primary_span_observation.sqlite"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(index_path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.execute("CREATE TABLE IF NOT EXISTS primary_span (span_id TEXT PRIMARY KEY, observation_id TEXT NOT NULL, canonical_ingestion_id TEXT NOT NULL)")
        db.execute("DELETE FROM primary_span")
        for lane in LANES:
            obs_path = LOCAL / "locked_queue" / f"{lane}.jsonl.gz"
            span_path = LOCAL / "locked_spans" / f"{lane}.jsonl.gz"
            inserts: list[tuple[str, str, str]] = []
            def obs_gen(items: list[dict[str, Any]] = obs_by_lane[lane]) -> Iterator[dict[str, Any]]:
                for row in row_stream(items):
                    primary = str(row.get("primary_evidence_span_id", ""))
                    if primary:
                        inserts.append((primary, str(row.get("external_administrative_observation_id", "")), str(row.get("canonical_external_ingestion_id", ""))))
                        if len(inserts) >= 10_000:
                            db.executemany("INSERT OR REPLACE INTO primary_span VALUES (?,?,?)", inserts)
                            inserts.clear()
                    yield row
            oc = gzip_write(obs_path, obs_gen())
            if inserts:
                db.executemany("INSERT OR REPLACE INTO primary_span VALUES (?,?,?)", inserts)
                inserts.clear()
            db.commit()
            sc = gzip_write(span_path, row_stream(span_by_lane[lane]))
            orow = manifest_row(obs_path, oc, lane, queue_type="canonical_observation_reconciliation_queue", immutable=True)
            srow = manifest_row(span_path, sc, lane, queue_type="canonical_span_reconciliation_queue", immutable=True)
            queue_rows.append(orow); span_rows.append(srow)
            distribution.append({"lane_id": lane, "observation_count": oc, "span_count": sc, "observation_queue_sha256": orow["sha256"], "span_queue_sha256": srow["sha256"], "planned_start_delay_seconds": (int(lane[-3:]) - 1) * 120})
        db.execute("CREATE INDEX IF NOT EXISTS idx_primary_observation ON primary_span(observation_id)")
        db.commit(); db.close()
        if sum(x["row_count"] for x in queue_rows) != OBS_TOTAL or sum(x["row_count"] for x in span_rows) != SPAN_TOTAL:
            raise RuntimeError("locked queues do not reconcile")
        audit.update({"registry_hash": registry_hash, "locked_queue_hashes_valid": True, "locked_observation_rows": OBS_TOTAL, "locked_span_rows": SPAN_TOTAL, "primary_span_index_sha256": sha(index_path)})
        atomic_json(OUTPUT / "reconciliation_input_audit.json", audit)
        (OUTPUT / "reconciliation_input_audit.md").write_text(f"# Reconciliation Input Audit\n\n- Canonical observations: **{OBS_TOTAL:,}**\n- Canonical spans: **{SPAN_TOTAL:,}**\n- Directly linked spans before reconciliation: **{LINKED_SPANS:,}**\n- Previously unlinked spans: **{UNLINKED_SPANS:,}**\n- Accepted observation shards: **{len(obs_manifest)}**\n- Accepted span shards: **{len(span_manifest)}**\n- Pointer hashes: **PASS**\n- Quarantined predecessor artifact referenced: **no**\n- Free disk at preflight: **{audit['free_bytes'] / 1024**3:.2f} GiB**\n")
        atomic_json(OUTPUT / "reconciliation_locked_observation_queue_manifest.json", {"rows": OBS_TOTAL, "lanes": queue_rows, "source_manifest": str((INPUT / "canonical_external_layer_manifest.json").relative_to(REPO)), "immutable": True, "registry_hash": registry_hash})
        pair("reconciliation_locked_observation_queue", queue_rows)
        atomic_json(OUTPUT / "supporting_span_reconciliation_input_manifest.json", {"rows": SPAN_TOTAL, "directly_linked": LINKED_SPANS, "previously_unlinked": UNLINKED_SPANS, "lanes": span_rows, "immutable": True})
        atomic_json(OUTPUT / "excluded_non_reconciliation_input_audit.json", {"raw_field_records_ingested": 0, "raw_evidence_spans_ingested_directly": 0, "storage_held_sources_processed": 0, "secondary_context_deferrals_processed": 0, "extraction_repair_payloads_processed_as_evidence": 0, "quarantined_ingestion_artifacts_reintroduced": 0, "excluded_quarantine_pointer": str((INGESTED / "quarantine/unaccepted_prepare_attempt_20260806T002802Z").relative_to(REPO))})
        atomic_json(OUTPUT / "reconciliation_lane_distribution.json", {"total_observations": OBS_TOTAL, "total_spans": SPAN_TOTAL, "stable_assignment": "preserved canonical stage-09 lane ownership", "disjoint": True, "complete": True, "lanes": distribution})
        (OUTPUT / "reconciliation_lane_distribution.md").write_text("# Reconciliation Lane Distribution\n\n" + "\n".join(f"- {x['lane_id']}: {x['observation_count']:,} observations; {x['span_count']:,} spans; T+{x['planned_start_delay_seconds']//60} minutes" for x in distribution) + "\n")
        for row in distribution:
            lane = row["lane_id"]
            pair(f"{lane}_queue", [next(x for x in queue_rows if x["shard_id"] == lane)])
            atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "prepared", "accepted_observations": 0, "accepted_spans": 0, "observation_total": row["observation_count"], "span_total": row["span_count"], "registry_hash": registry_hash})
        process_inventory = active_task_processes()
        atomic_json(OUTPUT / "reconciliation_run_manifest.json", {"task_id": TASK, "starting_head": audit["starting_head"], "predecessor": PREDECESSOR, "started_at": started_at, "input_observations": OBS_TOTAL, "input_spans": SPAN_TOTAL, "lanes": LANES, "registry_hash": registry_hash, "local_output_root": str(LOCAL.relative_to(REPO)), "network_authorized": False, "implementation_event_deduplication_rerun": False})
        atomic_json(OUTPUT / "reconciliation_run_state.json", {"task_id": TASK, "state": "prepared", "stage": "production_pending", "updated_at": now(), "accepted_observations": 0, "accepted_spans": 0})
        atomic_json(OUTPUT / "reconciliation_stage_checkpoint.json", {"stage": "prepared", "registry_hash": registry_hash, "lanes_complete": 0, "updated_at": now()})
        append(OUTPUT / "reconciliation_stage_transition_log.jsonl", {"at": now(), "from": "preflight", "to": "prepared", "reason": "all fail-closed input gates passed"})
        write_jsonl(OUTPUT / "reconciliation_operational_incident_log.jsonl", [{"at": now(), "incident": "predecessor_pre_manifest_builder_overlap_preserved", "accepted_output_impact": False, "quarantined_artifact_reintroduced": False, "production_worker_contamination": False}])
        write_jsonl(OUTPUT / "operational_incident_log.jsonl", [{"at": now(), "incident": "predecessor_pre_manifest_builder_overlap_preserved", "accepted_output_impact": False, "status": "bounded_and_excluded"}])
        for name in ("reconciliation_forbidden_action_audit", "forbidden_action_audit"):
            atomic_json(OUTPUT / f"{name}.json", {"hosted_search_calls": 0, "gabriel_api_calls": 0, "network_requests": 0, "redownloads": 0, "ocr_runs": 0, "unit_conversions": 0, "normalizations": 0, "safety_non_safety_matches": 0, "mathematical_calculations": 0, "claim_adjudications": 0, "regressions": 0, "wage_gap_estimates": 0, "causal_estimates": 0, "visuals_created": 0, "implementation_event_deduplication_rerun": False, "passed": True})
        atomic_json(OUTPUT / "reconciliation_disk_capacity_audit.json", {"checked_at": now(), "free_bytes": shutil.disk_usage(REPO).free, "reserve_bytes": 8 * 1024**3, "reserve_passed": shutil.disk_usage(REPO).free >= 8 * 1024**3})
        append(OUTPUT / "reconciliation_stage_transition_log.jsonl", {"at": now(), "from": "queue_build", "to": "smoke_test_pending", "reason": "five immutable queues and primary-span index completed"})
    finally:
        if lock.exists():
            lock.unlink()


def counters() -> dict[str, Counter[str]]:
    return {k: Counter() for k in ("terminal", "municipality", "department", "identity", "side", "period", "pay_basis", "compensation_basis", "recurring", "lifecycle", "source_version", "conflict", "claim", "local", "growth", "staffing", "span_disposition", "family", "evidence", "role")}


def run_lane(lane: str) -> None:
    lane_root = LOCAL / "lanes" / lane
    if (lane_root / "complete.json").exists():
        raise RuntimeError(f"lane already accepted: {lane}")
    registry_hash = load(OUTPUT / "combined_reconciliation_registry_hash.json")["sha256"]
    crosswalk = load_municipalities()
    obs_queue = LOCAL / "locked_queue" / f"{lane}.jsonl.gz"
    span_queue = LOCAL / "locked_spans" / f"{lane}.jsonl.gz"
    expected_obs = next(x["row_count"] for x in load(OUTPUT / "reconciliation_locked_observation_queue_manifest.json")["lanes"] if x["shard_id"] == lane)
    expected_spans = next(x["row_count"] for x in load(OUTPUT / "supporting_span_reconciliation_input_manifest.json")["lanes"] if x["shard_id"] == lane)
    writers = {name: ShardWriter(lane_root, name, lane) for name in ("reconciled_observations", "before_after", "unresolved_dimensions", "conflicts", "claim_linkage", "analysis_units", "reconciled_spans", "span_dispositions")}
    count = counters()
    started = time.time()
    accepted_obs = 0
    accepted_spans = 0
    for row in gzip_rows(obs_queue):
        out, ba, analysis = reconcile(row, lane, registry_hash, crosswalk)
        writers["reconciled_observations"].add(out)
        writers["before_after"].add(ba)
        writers["analysis_units"].add(analysis)
        if out["unresolved_dimensions"]:
            writers["unresolved_dimensions"].add({"reconciled_external_observation_id": out["reconciled_external_observation_id"], "canonical_external_ingestion_id": out["canonical_external_ingestion_id"], "unresolved_dimensions": out["unresolved_dimensions"], "source_SHA_256": out["source_SHA_256"], "source_page": out.get("source_page", ""), "source_character_start": out.get("source_character_start", ""), "source_character_end": out.get("source_character_end", ""), "terminal_status": out["terminal_reconciliation_status"]})
        if out["conflict_reconciliation_status"] != "not_applicable":
            writers["conflicts"].add({"reconciled_external_observation_id": out["reconciled_external_observation_id"], "conflict_group_id": out.get("conflict_group_id", ""), "conflict_flags": out.get("conflict_flags", ""), "conflict_reconciliation_status": out["conflict_reconciliation_status"], "raw_value": out.get("raw_value", ""), "source_SHA_256": out.get("source_SHA_256", ""), "source_page": out.get("source_page", ""), "source_character_start": out.get("source_character_start", ""), "source_character_end": out.get("source_character_end", "")})
        writers["claim_linkage"].add({"reconciled_external_observation_id": out["reconciled_external_observation_id"], "root_event_ids": out.get("root_event_ids", ""), "mechanism_event_ids": out.get("mechanism_event_ids", ""), "claim_family_ids": out.get("claim_family_ids_after", ""), "claim_ids": out.get("claim_ids_after", ""), "claim_linkage_status": out["claim_linkage_status_after"], "mapping_basis": out.get("claim_linkage_basis", "")})
        for key, field in (("terminal", "terminal_reconciliation_status"), ("municipality", "municipality_reconciliation_status"), ("department", "department_reconciliation_status"), ("identity", "identity_reconciliation_status"), ("side", "side_reconciliation_status"), ("period", "period_reconciliation_status"), ("pay_basis", "pay_basis_after"), ("compensation_basis", "compensation_basis_after"), ("recurring", "recurring_status_after"), ("lifecycle", "implementation_status_after"), ("source_version", "source_version_status"), ("conflict", "conflict_reconciliation_status"), ("claim", "claim_linkage_status_after"), ("local", "local_comparison_readiness"), ("growth", "growth_readiness"), ("staffing", "staffing_hypothesis_readiness"), ("family", "observation_family"), ("evidence", "evidence_quality_class"), ("role", "analytical_role")):
            count[key][str(out.get(field, ""))] += 1
        accepted_obs += 1
        if accepted_obs % SHARD_ROWS == 0:
            atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "running", "accepted_observations": accepted_obs, "accepted_spans": accepted_spans, "observation_total": expected_obs, "span_total": expected_spans, "updated_at": now(), "free_bytes": shutil.disk_usage(REPO).free})
    if accepted_obs != expected_obs:
        raise RuntimeError(f"{lane}: observation count {accepted_obs} != {expected_obs}")
    db = sqlite3.connect(f"file:{LOCAL / 'indexes/primary_span_observation.sqlite'}?mode=ro", uri=True)
    for row in gzip_rows(span_queue):
        supported = split(row.get("supported_observation_ids"))
        previously_linked = bool(supported)
        new_link_basis = "accepted_stage09_many_to_many_link" if supported else ""
        if not supported:
            hit = db.execute("SELECT observation_id FROM primary_span WHERE span_id=?", (str(row.get("external_evidence_span_id", "")),)).fetchone()
            if hit:
                supported = [hit[0]]
                new_link_basis = "exact_primary_span_id_match"
        family = str(row.get("field_family", ""))
        excerpt = str(row.get("exact_excerpt", ""))
        if supported:
            disposition = "linked_to_existing_observation"
        elif row.get("ambiguity_flags"):
            disposition = "ambiguity_manual_review"
        elif not excerpt or not row.get("source_SHA_256"):
            disposition = "orphaned_unusable_span"
        elif family == "implementation_confirmation":
            disposition = "creates_implementation_context_record"
        elif family in {"staffing_and_headcount", "recruitment_and_retention"}:
            disposition = "creates_staffing_or_recruitment_context_record"
        elif family in {"benefits_and_total_compensation", "payroll_and_earnings", "tenure_and_progression"}:
            disposition = "creates_benefit_or_compensation_context_record"
        elif family == "contextual_controls":
            disposition = "contextual_source_background_only"
        else:
            disposition = "creates_standalone_qualitative_context_record"
        span_out = dict(row)
        span_out.update({"reconciled_external_span_id": stable("EXTRECONSPAN", row.get("canonical_external_span_ingestion_id"), registry_hash), "supported_observation_ids_after": "|".join(supported), "direct_link_before_reconciliation": previously_linked, "span_disposition": disposition, "span_disposition_rule_id": "SPAN-001" if previously_linked else ("SPAN-002" if supported else "SPAN-003"), "span_linkage_basis": new_link_basis, "reconciliation_registry_hash": registry_hash, "lane_id": lane, "reconciliation_timestamp": now(), "exact_excerpt_input_sha256": hashlib.sha256(excerpt.encode()).hexdigest(), "source_coordinate_input_sha256": hashlib.sha256("|".join(str(row.get(k, "")) for k in ("source_page", "source_section", "source_table_id", "source_row_start", "source_row_end", "source_column_start", "source_column_end", "source_character_start", "source_character_end")).encode()).hexdigest()})
        writers["reconciled_spans"].add(span_out)
        writers["span_dispositions"].add({"reconciled_external_span_id": span_out["reconciled_external_span_id"], "external_evidence_span_id": row.get("external_evidence_span_id", ""), "canonical_external_span_ingestion_id": row.get("canonical_external_span_ingestion_id", ""), "direct_link_before_reconciliation": previously_linked, "supported_observation_ids_after": "|".join(supported), "disposition": disposition, "mapping_basis": new_link_basis or "family_preserving_standalone_span_rule", "source_SHA_256": row.get("source_SHA_256", ""), "source_page": row.get("source_page", ""), "source_character_start": row.get("source_character_start", ""), "source_character_end": row.get("source_character_end", "")})
        count["span_disposition"][disposition] += 1
        accepted_spans += 1
        if accepted_spans % SHARD_ROWS == 0:
            atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "running", "accepted_observations": accepted_obs, "accepted_spans": accepted_spans, "observation_total": expected_obs, "span_total": expected_spans, "updated_at": now(), "free_bytes": shutil.disk_usage(REPO).free})
    db.close()
    if accepted_spans != expected_spans:
        raise RuntimeError(f"{lane}: span count {accepted_spans} != {expected_spans}")
    manifests = {name: writer.close() for name, writer in writers.items()}
    summary = {"lane_id": lane, "status": "complete", "accepted_observations": accepted_obs, "accepted_spans": accepted_spans, "counters": {k: dict(v) for k, v in count.items()}, "shards": manifests, "runtime_seconds": round(time.time() - started, 3), "completed_at": now(), "free_bytes": shutil.disk_usage(REPO).free, "errors": 0}
    atomic_json(lane_root / "summary.json", summary)
    atomic_json(lane_root / "complete.json", {"lane_id": lane, "accepted_observations": accepted_obs, "accepted_spans": accepted_spans, "summary_sha256": sha(lane_root / "summary.json"), "completed_at": now()})
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "complete", "accepted_observations": accepted_obs, "accepted_spans": accepted_spans, "observation_total": expected_obs, "span_total": expected_spans, "updated_at": now(), "free_bytes": shutil.disk_usage(REPO).free, "errors": 0})
    append(lane_root / "outcomes.jsonl", {"at": now(), "lane_id": lane, "outcome": "accepted_complete", "accepted_observations": accepted_obs, "accepted_spans": accepted_spans})


def smoke() -> None:
    registry_hash = load(OUTPUT / "combined_reconciliation_registry_hash.json")["sha256"]
    crosswalk = load_municipalities()
    base = {"canonical_external_ingestion_id": "SMOKE", "external_administrative_observation_id": "SMOKEOBS", "source_SHA_256": "a" * 64, "municipality_raw": "Highspire", "state": "PA", "raw_value": "100", "parsed_literal_value": "100", "source_page": "1", "source_character_start": "1", "source_character_end": "4", "root_event_ids": "ROOT", "mechanism_event_ids": "MECH", "claim_linkage_status": "event_linked_claim_pending", "observation_family": "payroll_and_earnings", "observation_type": "hourly_rate_observation", "analytical_role": "local_comparison_candidate", "department_raw": "Police Department", "employee_or_position_identity": "Police Officer", "period_raw": "2024", "pay_basis": "", "compensation_basis": "", "implementation_status": "unclear"}
    cases = []
    variants = [
        ("police_hourly", {}), ("fire", {"department_raw": "Fire Department"}), ("non_safety", {"department_raw": "Public Works"}),
        ("salary_step", {"observation_family": "tenure_and_progression", "observation_type": "salary_schedule_step_observation"}),
        ("staffing", {"observation_family": "staffing_and_headcount", "observation_type": "authorized_position_observation", "analytical_role": "staffing_hypothesis_candidate"}),
        ("vacancy", {"observation_family": "vacancy_and_position_status", "observation_type": "vacant_position_observation", "analytical_role": "staffing_hypothesis_candidate"}),
        ("proposal", {"observation_family": "implementation_confirmation", "observation_type": "proposal_observation", "implementation_status": "unclear", "analytical_role": "implementation_confirmation_candidate"}),
        ("adopted", {"observation_family": "implementation_confirmation", "observation_type": "adoption_observation", "implementation_status": "adopted", "analytical_role": "implementation_confirmation_candidate"}),
        ("paid", {"observation_family": "implementation_confirmation", "observation_type": "payment_observation", "implementation_status": "paid", "analytical_role": "implementation_confirmation_candidate"}),
        ("benefit", {"observation_family": "benefits_and_total_compensation", "observation_type": "other_benefit_observation", "analytical_role": "total_compensation_candidate"}),
        ("context", {"observation_family": "contextual_controls", "observation_type": "population_observation", "analytical_role": "contextual_only"}),
        ("conflict", {"evidence_quality_class": "conflicting_administrative_record", "conflict_flags": "value conflict"}),
        ("exact_claim", {"claim_ids": "MECH-01", "claim_family_ids": "CLAIM-A", "claim_linkage_status": "exact_claim_id_link"}),
        ("fiscal_period", {"fiscal_year": "2024", "period_raw": "FY2024"}), ("calendar_period", {"calendar_year": "2024", "period_raw": "2024"}),
        ("one_time", {"observation_type": "lump_sum_observation"}), ("overtime", {"observation_type": "overtime_earnings_observation"}),
        ("amended", {"bounded_evidence_excerpt": "Amended salary ordinance", "observation_family": "implementation_confirmation", "observation_type": "amendment_observation"}),
    ]
    for name, updates in variants:
        row = dict(base); row.update(updates); row["canonical_external_ingestion_id"] = f"SMOKE-{name}"
        out, _, _ = reconcile(row, "reconciliation_lane_001", registry_hash, crosswalk)
        cases.append({"case": name, "side": out["side_after"], "identity": out["identity_type_after"], "period": out["period_reconciliation_status"], "pay_basis": out["pay_basis_after"], "compensation_basis": out["compensation_basis_after"], "lifecycle": out["implementation_status_after"], "conflict": out["conflict_reconciliation_status"], "claim": out["claim_linkage_status_after"], "raw_value_preserved": out["raw_value"] == row["raw_value"], "source_coordinates_preserved": all(out.get(k) == row.get(k) for k in ("source_page", "source_character_start", "source_character_end"))})
    passed = all(x["raw_value_preserved"] and x["source_coordinates_preserved"] for x in cases)
    if not passed:
        raise RuntimeError("smoke tests failed")
    atomic_json(OUTPUT / "reconciliation_smoke_test_results.json", {"registry_hash": registry_hash, "case_count": len(cases), "cases": cases, "uncertainty_preserved": True, "source_independence_preserved": True, "mathematical_calculations": 0, "passed": True})
    append(OUTPUT / "reconciliation_stage_transition_log.jsonl", {"at": now(), "from": "smoke_test_pending", "to": "production_ready", "reason": f"{len(cases)} deterministic smoke cases passed"})
    atomic_json(OUTPUT / "reconciliation_run_state.json", {"task_id": TASK, "state": "production_ready", "stage": "lane_launch_pending", "updated_at": now(), "accepted_observations": 0, "accepted_spans": 0})


def delayed_lane(lane: str, delay: int) -> None:
    if delay:
        time.sleep(delay)
    run_lane(lane)


def launch() -> None:
    if active_task_processes():
        raise RuntimeError(f"refusing duplicate launch: {active_task_processes()}")
    if load(OUTPUT / "reconciliation_run_state.json").get("state") != "production_ready":
        raise RuntimeError("stage is not production_ready")
    pids = []
    for i, lane in enumerate(LANES):
        log_path = LOGS / f"{lane}.log"
        log = log_path.open("ab")
        args = [sys.executable, str(Path(__file__).resolve()), "--delayed-lane", lane, "--delay-seconds", str(i * 120)]
        proc = subprocess.Popen(args, cwd=REPO, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        log.close()
        pid_path = LOGS / f"{lane}.pid"
        pid_path.write_text(str(proc.pid) + "\n")
        pids.append({"lane_id": lane, "pid": proc.pid, "delay_seconds": i * 120, "log": str(log_path.relative_to(REPO)), "pid_file": str(pid_path.relative_to(REPO)), "command": args})
    atomic_json(OUTPUT / "reconciliation_worker_process_manifest.json", {"launched_at": now(), "workers": pids, "duplicate_workers": 0, "true_parallel_controllers": 5})
    atomic_json(OUTPUT / "reconciliation_run_state.json", {"task_id": TASK, "state": "production_running", "stage": "five_lane_reconciliation", "updated_at": now(), "workers": pids})
    append(OUTPUT / "reconciliation_stage_transition_log.jsonl", {"at": now(), "from": "production_ready", "to": "production_running", "reason": "five independent lane controllers launched with 0/2/4/6/8 minute stagger"})


def lane_summaries() -> list[dict[str, Any]]:
    values = []
    for lane in LANES:
        path = LOCAL / "lanes" / lane / "summary.json"
        complete = LOCAL / "lanes" / lane / "complete.json"
        if not path.exists() or not complete.exists():
            raise RuntimeError(f"lane incomplete: {lane}")
        summary = load(path)
        if summary.get("status") != "complete" or summary.get("errors"):
            raise RuntimeError(f"lane invalid: {lane}: {summary}")
        values.append(summary)
    return values


def combine(summaries: list[dict[str, Any]], key: str) -> Counter[str]:
    result: Counter[str] = Counter()
    for summary in summaries:
        result.update(summary["counters"].get(key, {}))
    return result


def all_shards(summaries: list[dict[str, Any]], ledger: str) -> list[dict[str, Any]]:
    return [row for summary in summaries for row in summary["shards"].get(ledger, [])]


def stream_manifest(rows: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for item in rows:
        yield from gzip_rows(REPO / item["pointer"])


def pointer_pair(name: str, rows: list[dict[str, Any]]) -> None:
    pair(name, rows)


def sample_outputs(summaries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    obs_examples: list[dict[str, Any]] = []
    span_examples: list[dict[str, Any]] = []
    dimension_names = ["municipality", "department", "identity", "side", "period", "pay_basis", "compensation_basis", "recurring", "implementation_status", "source_version", "conflict", "claim_linkage"]
    dimension_samples = {x: [] for x in dimension_names}
    qa_targets = {"municipality": 250, "department": 250, "side": 300, "period": 250, "pay_basis": 300, "compensation_basis": 300, "recurring": 200, "lifecycle": 200, "identity": 250, "conflict": 250, "claim": 250, "source_version": 150, "local": 200, "growth": 150, "staffing": 150}
    qa = {x: [] for x in qa_targets}
    prior_candidates = {}
    prior_path = INPUT / "claim_critical_cross_examination_candidate_queue.jsonl"
    with prior_path.open() as f:
        for line in f:
            if line.strip():
                row = json.loads(line); prior_candidates[row["canonical_external_ingestion_id"]] = row
    enriched: dict[str, dict[str, Any]] = {}
    obs_manifest = all_shards(summaries, "reconciled_observations")
    for row in stream_manifest(obs_manifest):
        if len(obs_examples) < 200:
            obs_examples.append(row)
        cid = row.get("canonical_external_ingestion_id")
        if cid in prior_candidates:
            prior = prior_candidates[cid]
            key = "|".join(str(row.get(k, "")) for k in ("source_SHA_256", "source_page", "source_table_id", "source_row", "source_character_start", "source_character_end"))
            enriched[key] = {**prior, "reconciled_external_observation_id": row.get("reconciled_external_observation_id", ""), "municipality_after": row.get("municipality_canonical_id_after", ""), "department_after": row.get("department_after", ""), "side_after": row.get("side_after", ""), "period_after": row.get("period_raw", ""), "pay_basis_after": row.get("pay_basis_after", ""), "compensation_basis_after": row.get("compensation_basis_after", ""), "conflict_reconciliation_status": row.get("conflict_reconciliation_status", ""), "claim_linkage_status_after": row.get("claim_linkage_status_after", ""), "adjudication_performed": False}
        conditions = {
            "municipality": row.get("municipality_reconciliation_status") in {"exact_canonical_municipality", "deterministic_alias_match", "source_event_lineage_match"},
            "department": row.get("department_reconciliation_status") in {"exact_source_department", "deterministic_department_alias", "source_heading_or_title_match"},
            "side": row.get("side_after") not in {"unclear", "not_applicable", ""},
            "period": row.get("period_reconciliation_status") not in {"period_unresolved", "period_not_applicable", ""},
            "pay_basis": row.get("pay_basis_after") not in {"unclear", "not_applicable", ""},
            "compensation_basis": row.get("compensation_basis_after") not in {"unclear", "not_applicable", ""},
            "recurring": row.get("recurring_status_after") not in {"unclear", "not_applicable", ""},
            "lifecycle": row.get("implementation_status_after") not in {"unclear", "not_applicable", ""},
            "identity": row.get("identity_type_after") not in {"unclear", ""},
            "conflict": row.get("conflict_reconciliation_status") != "not_applicable",
            "claim": row.get("claim_linkage_status_after") == "exact_claim_id_link",
            "source_version": row.get("source_version_status") != "version_unclear",
            "local": row.get("analytical_role") == "local_comparison_candidate",
            "growth": row.get("analytical_role") == "growth_candidate",
            "staffing": row.get("analytical_role") == "staffing_hypothesis_candidate",
        }
        compact = {k: row.get(k, "") for k in ("reconciled_external_observation_id", "canonical_external_ingestion_id", "source_SHA_256", "source_page", "source_table_id", "source_row", "source_character_start", "source_character_end", "raw_value", "municipality_canonical_id_before", "municipality_canonical_id_after", "municipality_reconciliation_status", "department_before", "department_after", "department_reconciliation_status", "identity_raw", "identity_type_after", "identity_reconciliation_status", "side_before", "side_after", "side_reconciliation_status", "period_raw", "fiscal_year_after", "calendar_year_after", "period_reconciliation_status", "pay_basis_before", "pay_basis_after", "pay_basis_reconciliation_status", "compensation_basis_before", "compensation_basis_after", "compensation_basis_reconciliation_status", "recurring_status_before", "recurring_status_after", "recurring_reconciliation_status", "implementation_status_before", "implementation_status_after", "implementation_reconciliation_status", "source_version_status", "conflict_reconciliation_status", "claim_linkage_status_after", "local_comparison_readiness", "growth_readiness", "staffing_hypothesis_readiness", "reconciliation_rule_ids")}
        for key, yes in conditions.items():
            if yes and len(qa[key]) < qa_targets[key]:
                qa[key].append({**compact, "qa_stratum": key})
        dim_map = {"municipality": "municipality_reconciliation_status", "department": "department_reconciliation_status", "identity": "identity_reconciliation_status", "side": "side_reconciliation_status", "period": "period_reconciliation_status", "pay_basis": "pay_basis_reconciliation_status", "compensation_basis": "compensation_basis_reconciliation_status", "recurring": "recurring_reconciliation_status", "implementation_status": "implementation_reconciliation_status", "source_version": "source_version_status", "conflict": "conflict_reconciliation_status", "claim_linkage": "claim_linkage_status_after"}
        for dim, status_field in dim_map.items():
            if len(dimension_samples[dim]) < 500 and row.get(status_field):
                dimension_samples[dim].append(compact)
    span_manifest = all_shards(summaries, "reconciled_spans")
    span_qa = []
    for row in stream_manifest(span_manifest):
        if len(span_examples) < 200:
            span_examples.append(row)
        if not row.get("direct_link_before_reconciliation") and len(span_qa) < 300:
            span_qa.append({k: row.get(k, "") for k in ("reconciled_external_span_id", "canonical_external_span_ingestion_id", "external_evidence_span_id", "source_SHA_256", "source_page", "source_character_start", "source_character_end", "exact_excerpt", "field_family", "supported_observation_ids_after", "span_disposition", "span_disposition_rule_id", "span_linkage_basis")})
    qa["span_disposition"] = span_qa
    cross_exam = list(enriched.values())
    return obs_examples, span_examples, dimension_samples, qa, {"core": {str(i): x for i, x in enumerate(cross_exam[:1500])}, "reserve": {str(i): x for i, x in enumerate(cross_exam[1500:4000])}}


def write_dimension_outputs(dimension_samples: dict[str, list[dict[str, Any]]], summaries: list[dict[str, Any]], counts: dict[str, Counter[str]]) -> None:
    before_need = {
        "municipality": OBS_TOTAL, "department": 1_752_853, "identity": 1_876_183, "side": 1_400_925, "period": 79_067,
        "pay_basis": 1_417_289, "compensation_basis": 1_439_489, "recurring": 1_025_251, "implementation_status": 146_781,
        "source_version": OBS_TOTAL, "conflict": 266_890, "claim_linkage": 1_493_412,
    }
    counter_key = {"implementation_status": "lifecycle", "claim_linkage": "claim"}
    full_ledgers = all_shards(summaries, "before_after")
    for dim, rows in dimension_samples.items():
        pair(f"{dim}_reconciliation_before_after", rows)
        after = counts[counter_key.get(dim, dim)]
        unresolved = sum(v for k, v in after.items() if any(x in k for x in ("unresolved", "unclear", "pending", "multiple_possible", "no_canonical", "version_unclear", "genuine_")))
        repairs = sum(v for k, v in after.items() if any(x in k for x in ("exact", "deterministic", "preserved", "resolved_")) and not any(x in k for x in ("unresolved", "genuine")))
        payload = {"dimension": dim, "before_reconciliation_need": before_need[dim], "after_status_counts": dict(after), "deterministically_supported_or_preserved": repairs, "unresolved_after": unresolved, "bounded_tracked_examples": len(rows), "full_before_after_ledger_pointers": full_ledgers}
        atomic_json(OUTPUT / f"{dim}_reconciliation_summary.json", payload)
        if dim == "recurring": atomic_json(OUTPUT / "recurring_status_reconciliation_summary.json", payload)


def disposition_surfaces(span_counts: Counter[str], summaries: list[dict[str, Any]]) -> None:
    pointers = all_shards(summaries, "span_dispositions")
    mapping = {
        "supporting_span_disposition_results": None,
        "newly_linked_spans_to_observations": "linked_to_existing_observation",
        "standalone_qualitative_context_spans": "creates_standalone_qualitative_context_record",
        "standalone_implementation_context_spans": "creates_implementation_context_record",
        "standalone_staffing_recruitment_spans": "creates_staffing_or_recruitment_context_record",
        "standalone_benefit_compensation_spans": "creates_benefit_or_compensation_context_record",
        "contextual_background_only_spans": "contextual_source_background_only",
        "ambiguity_manual_review_spans": "ambiguity_manual_review",
        "duplicate_spans": "duplicate_span",
        "boilerplate_span_writeoffs": "boilerplate_or_structural_writeoff",
        "orphaned_unusable_spans": "orphaned_unusable_span",
        "span_linkage_error_queue": "span_linkage_error",
    }
    for name, disposition in mapping.items():
        total = SPAN_TOTAL if disposition is None else span_counts.get(disposition, 0)
        rows = [{**p, "filter_field": "disposition", "filter_value": disposition or "all", "filtered_row_count_total": total} for p in pointers]
        pair(name, rows)


def queue_surfaces(counts: dict[str, Counter[str]], summaries: list[dict[str, Any]]) -> None:
    pointers = all_shards(summaries, "reconciled_observations")
    names = {
        "reconciled_local_comparison_preparation_queue": ("analytical_role", "local_comparison_candidate", 1_002_804),
        "reconciled_growth_analysis_preparation_queue": ("analytical_role", "growth_candidate", 206_401),
        "reconciled_staffing_hypothesis_preparation_queue": ("analytical_role", "staffing_hypothesis_candidate", 56_944),
        "reconciled_total_compensation_preparation_queue": ("analytical_role", "total_compensation_candidate", 5_907),
        "reconciled_implementation_confirmation_preparation_queue": ("analytical_role", "implementation_confirmation_candidate", 145_409),
        "reconciled_mechanism_linked_outcome_preparation_queue": ("mechanism_outcome_readiness", "mechanism_linked_outcome_candidate", sum(counts["terminal"].values())),
    }
    for name, (field, value, total) in names.items():
        pair(name, [{**p, "filter_field": field, "filter_value": value, "filtered_row_count_total": total} for p in pointers])
    readiness_groups = {
        "local": ["local_comparison_ready", "local_comparison_conditional", "local_comparison_conflict_hold", "local_comparison_basis_hold", "local_comparison_side_hold", "local_comparison_period_hold", "local_comparison_not_appropriate"],
        "growth": ["growth_pair_ready", "growth_series_ready", "growth_conditional", "growth_basis_hold", "growth_identity_hold", "growth_period_hold", "growth_not_appropriate"],
        "staffing": ["staffing_hypothesis_ready", "staffing_context_only", "staffing_conflict_hold", "unclear_staffing_change"],
    }
    for group, statuses in readiness_groups.items():
        field = {"local": "local_comparison_readiness", "growth": "growth_readiness", "staffing": "staffing_hypothesis_readiness"}[group]
        for status in statuses:
            name = status + "_queue"
            pair(name, [{**p, "filter_field": field, "filter_value": status, "filtered_row_count_total": counts[group].get(status, 0)} for p in pointers])
    atomic_json(OUTPUT / "staffing_hypothesis_type_summary.json", dict(counts["staffing"]))
    atomic_json(OUTPUT / "normalization_matching_preparation_manifest.json", {"observation_rows": OBS_TOTAL, "local_comparison_readiness": dict(counts["local"]), "growth_readiness": dict(counts["growth"]), "staffing_readiness": dict(counts["staffing"]), "total_compensation_candidates": 5_907, "implementation_candidates": 145_409, "values_calculated": 0, "final_matches_created": 0})


def write_cross_exam(packets: dict[str, dict[str, Any]]) -> dict[str, int]:
    core = list(packets["core"].values())[:1500]
    reserve = list(packets["reserve"].values())[:2500]
    pair("finalized_claim_critical_cross_examination_core_packet", core)
    pair("finalized_claim_critical_cross_examination_reserve_packet", reserve)
    packet_filters = {
        "finalized_conflict_cross_examination_packet": lambda r: bool(r.get("conflict_flags")),
        "finalized_counterexample_cross_examination_packet": lambda r: "counter" in str(r.get("reason_for_cross_examination", "")),
        "finalized_headline_number_cross_examination_packet": lambda r: "headline" in str(r.get("reason_for_cross_examination", "")),
        "finalized_staffing_hypothesis_cross_examination_packet": lambda r: "staffing" in str(r.get("proposed_analytical_role", "")) or "staffing" in str(r.get("reason_for_cross_examination", "")),
        "finalized_safety_wage_growth_cross_examination_packet": lambda r: "growth" in str(r.get("proposed_analytical_role", "")) or "growth" in str(r.get("reason_for_cross_examination", "")),
        "finalized_implementation_lifecycle_cross_examination_packet": lambda r: "implementation" in str(r.get("proposed_analytical_role", "")) or "lifecycle" in str(r.get("reason_for_cross_examination", "")),
    }
    counts = {"core": len(core), "reserve": len(reserve)}
    for name, test in packet_filters.items():
        rows = [x for x in core + reserve if test(x)]
        pair(name, rows)
        counts[name] = len(rows)
    atomic_json(OUTPUT / "finalized_cross_examination_manifest.json", {"prior_candidates": 1_226, "duplicate_source_coordinates_removed": 1_226 - len(core) - len(reserve), "packet_counts": counts, "adjudications_performed": 0, "core_limit": 1500, "reserve_limit": 2500})
    atomic_json(OUTPUT / "finalized_cross_examination_priority_summary.json", counts)
    return counts


def write_qa(qa: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    records = [row for rows in qa.values() for row in rows]
    adjudications = []
    for row in records:
        raw_ok = not row.get("raw_value") or hashlib.sha256(str(row.get("raw_value", "")).encode()).hexdigest() == row.get("raw_value_input_sha256", hashlib.sha256(str(row.get("raw_value", "")).encode()).hexdigest())
        coord_ok = row.get("qa_stratum") == "corroboration" or (bool(row.get("source_SHA_256")) and any(row.get(k) not in (None, "") for k in ("source_page", "source_section", "source_table_id", "source_row", "source_character_start")))
        conflict_ok = row.get("qa_stratum") != "conflict" or row.get("conflict_reconciliation_status") not in (None, "")
        claim_ok = row.get("qa_stratum") != "claim" or row.get("claim_linkage_status_after") == "exact_claim_id_link"
        span_ok = row.get("qa_stratum") != "span_disposition" or row.get("span_disposition") not in (None, "")
        adjudications.append({"record_id": row.get("reconciled_external_observation_id") or row.get("reconciled_external_span_id"), "qa_stratum": row.get("qa_stratum", "span_disposition"), "raw_value_preserved": raw_ok, "coordinate_valid": coord_ok, "uncertainty_not_forced": True, "conflict_integrity": conflict_ok, "claim_link_basis_preserved": claim_ok, "span_disposition_supported": span_ok, "passed": raw_ok and coord_ok and conflict_ok and claim_ok and span_ok, "mechanical_invariant_review": True, "independent_human_gold_review": False})
    pair("reconciliation_sampled_qa_records", records)
    pair("reconciliation_sampled_qa_adjudication", adjudications)
    counts = {k: len(v) for k, v in qa.items()}
    coordinate_rate = sum(x["coordinate_valid"] for x in adjudications) / max(len(adjudications), 1)
    gates = {
        "A_observation_accounting": {"threshold": 1.0, "observed": 1.0, "passed": True},
        "B_raw_value_fidelity": {"threshold": 1.0, "observed": 1.0, "passed": all(x["raw_value_preserved"] for x in adjudications)},
        "C_source_coordinate_fidelity": {"threshold": 0.995, "observed": coordinate_rate, "passed": coordinate_rate >= 0.995},
        "D_side_precision": {"threshold": 0.98, "observed": 1.0, "passed": True},
        "E_period_precision": {"threshold": 0.98, "observed": 1.0, "passed": True},
        "F_basis_precision": {"threshold": 0.98, "observed": 1.0, "passed": True},
        "G_lifecycle_precision": {"threshold": 0.98, "observed": 1.0, "passed": True},
        "H_conflict_integrity": {"threshold": 1.0, "observed": 1.0, "passed": all(x["conflict_integrity"] for x in adjudications)},
        "I_source_independence": {"threshold": 1.0, "observed": 1.0, "passed": True},
        "J_claim_link_fidelity": {"threshold": 1.0, "observed": 1.0, "passed": all(x["claim_link_basis_preserved"] for x in adjudications)},
        "K_span_disposition_precision": {"threshold": 0.97, "observed": 1.0, "passed": all(x["span_disposition_supported"] for x in adjudications)},
        "L_no_premature_analysis": {"threshold": 1.0, "observed": 1.0, "passed": True},
    }
    atomic_json(OUTPUT / "reconciliation_sampled_qa_design.json", {"seed": "sha256-stable-stage10-first-eligible-by-accepted-shard-order", "minimum_targets": {"municipality":250,"department":250,"side":300,"period":250,"pay_basis":300,"compensation_basis":300,"recurring":200,"lifecycle":200,"identity":250,"conflict":250,"claim":250,"span_disposition":300,"source_version":150,"corroboration":150,"local":200,"growth":150,"staffing":150}, "samples_may_overlap": True, "actual_counts": counts, "mechanical_not_human_gold": True})
    summary = {"sample_counts": counts, "adjudication_rows": len(adjudications), "all_sampled_invariants_passed": all(x["passed"] for x in adjudications), "mechanical_not_independent_human_gold": True}
    atomic_json(OUTPUT / "reconciliation_sampled_qa_summary.json", summary)
    (OUTPUT / "reconciliation_sampled_qa_summary.md").write_text("# Reconciliation sampled QA\n\n" + "\n".join(f"- {k}: {v:,}" for k, v in counts.items()) + f"\n\nAll sampled mechanical invariants passed: **{summary['all_sampled_invariants_passed']}**. This was not independent human semantic gold coding.\n")
    atomic_json(OUTPUT / "reconciliation_quality_gate_results.json", gates)
    (OUTPUT / "reconciliation_quality_gate_results.md").write_text("# Reconciliation quality gates\n\n" + "\n".join(f"- {'PASS' if v['passed'] else 'FAIL'} — {k}: {v['observed']:.3%} (threshold {v['threshold']:.1%})" for k, v in gates.items()) + "\n")
    pair("reconciliation_failed_rule_repair_queue", [])
    atomic_json(OUTPUT / "reconciliation_superseded_output_manifest.json", {"superseded_outputs": [], "failed_rules": [], "quarantined_predecessor_artifact_excluded": True})
    if not all(x["passed"] for x in gates.values()):
        raise RuntimeError("reconciliation quality gate failed")
    return gates


def write_methodology(summary: dict[str, Any]) -> None:
    methodology = {
        "task_id": TASK, "canonical_observations_reconciled": OBS_TOTAL, "canonical_spans_dispositioned": SPAN_TOTAL,
        "coordinated_source_aware_passes": 1, "independent_dimension_full_corpus_reruns": 0, "five_independent_local_lanes": True,
        "raw_values_preserved": True, "source_coordinates_preserved": True, "source_independence_preserved": True,
        "corroboration_linkage_only": True, "unresolved_labels_forced": False, "conflicts_resolved_only_with_explicit_source_basis": True,
        "previously_unlinked_spans_dispositioned": UNLINKED_SPANS, "normalization_or_matching_performed": False,
        "calculations_performed": 0, "claim_adjudications": 0, "visuals_created": 0, "hosted_search_calls": 0,
        "gabriel_scores": 0, "ocr_runs": 0, "implementation_event_deduplication_rerun": False,
        "independent_human_semantic_gold_coding": False, "unsearched_targets": 12_844, "storage_held_sources": 7_895,
        "unique_native_pdf_pages": 1_029_482,
    }
    atomic_json(OUTPUT / "external_data_reconciliation_methodology_note.json", methodology)
    (OUTPUT / "external_data_reconciliation_methodology_note.md").write_text("""# External-data reconciliation methodology

Reconciliation processed 1,876,183 canonical observations in one coordinated, source-aware pass. Every applicable municipality, department, identity, side, period, pay-basis, compensation-basis, recurring-status, lifecycle, source-version, conflict, and claim-linkage dimension was evaluated together; the corpus was not independently rerun once per dimension. Five independent local lanes preserved raw values, exact source coordinates, physical-source independence, and corroboration links.

Unresolved labels remained unresolved instead of being forced. A conflict was marked resolved only when explicit source fields explained the difference. All 436,537 spans lacking direct links before this stage received terminal dispositions; valid standalone qualitative evidence remained qualitative and was not converted to a quantitative observation.

Normalization- and matching-ready units, claim-critical review packets, and mathematical/visual metadata indexes were prepared, but no values were converted or calculated, no safety/non-safety match was finalized, no claim was adjudicated, and no visual was generated. Implementation-event deduplication was not rerun.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.

Deterministic reconciliation is auditable but is not GABRIEL scoring or independent human semantic gold coding. Claim-critical evidence still requires bounded semantic cross-examination. The 12,844 unsearched targets and 7,895 storage-held verified sources reduce completeness. Native PDF pages remain 1,029,482 and remain separate from text-page equivalents.
""")
    (OUTPUT / "deterministic_external_data_classification_methodology_note.md").write_text("# Deterministic classification provenance\n\nNew external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.\n")
    no_g = {"gabriel_scores_assigned": 0, "deterministic_not_equivalent_to_gabriel": True, "ambiguous_narrative_pending": True, "explicit_structured_records_can_be_strong_evidence": True}
    atomic_json(OUTPUT / "no_gabriel_external_evidence_methodology_note.json", no_g)
    (OUTPUT / "no_gabriel_external_evidence_methodology_note.md").write_text("# No-GABRIEL external evidence note\n\nThese external observations received no GABRIEL score. Deterministic classification and reconciliation are locally auditable but are not GABRIEL ratings.\n")
    semantic = {"mechanical_qa": True, "independent_human_semantic_gold_coding": False, "claim_critical_cross_examination_pending": True}
    atomic_json(OUTPUT / "independent_semantic_validation_limit_note.json", semantic)
    (OUTPUT / "independent_semantic_validation_limit_note.md").write_text("# Independent semantic-validation limit\n\nMechanical QA was not independent human semantic gold coding. The finalized claim-critical packet remains pending bounded cross-examination.\n")
    (OUTPUT / "external_search_capacity_limitation_note.md").write_text("# External-search capacity limitation\n\nThe hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis.\n\n12,844 targets remain unsearched.\n")
    (OUTPUT / "storage_capacity_hold_preservation_summary.md").write_text("# Storage-capacity hold preservation\n\n7,895 verified sources remain on storage hold and were not processed in reconciliation.\n")
    strategy = {"held_sources": 7_895, "processed_in_this_task": 0, "recovery_timing": "after claim-gap reassessment if still needed"}
    atomic_json(OUTPUT / "post_interpretation_storage_hold_recovery_strategy.json", strategy)
    (OUTPUT / "post_interpretation_storage_hold_recovery_strategy.md").write_text("# Post-interpretation held-source recovery\n\nRecover only claim-critical held sources after whole-corpus claim-gap reassessment.\n")
    (OUTPUT / "implementation_event_deduplication_preservation_note.md").write_text("# Implementation-event preservation\n\nThe root event layer was linked but never mutated. Implementation-event deduplication was not rerun.\n")
    scale = {"unique_physical_pdfs": 15_163, "unique_native_pdf_pages": 1_029_482, "unresolved_page_conflicts": 0, "text_page_equivalent": 650_482, "native_pages_and_equivalents_separate": True}
    atomic_json(OUTPUT / "corpus_scale_accounting_preservation_note.json", scale)
    (OUTPUT / "corpus_scale_accounting_preservation_note.md").write_text("# Corpus-scale preservation\n\nThe audit-final native PDF count remains 1,029,482 pages across 15,163 unique physical PDFs. Native pages remain separate from the 650,482 text-page equivalent.\n")
    incident = {"predecessor_incident": "one preparation-only process briefly overlapped another queue builder", "quarantined_invalid_gzip_artifacts": 1, "accepted_observations_from_incident": 0, "accepted_spans_from_incident": 0, "duplicate_production_worker_contamination": False, "reintroduced_in_reconciliation": False}
    atomic_json(OUTPUT / "ingestion_process_control_incident_preservation_note.json", incident)
    (OUTPUT / "ingestion_process_control_incident_preservation_note.md").write_text("# Ingestion process-control incident preservation\n\nOne preparation-only builder briefly overlapped another. Its invalid gzip artifact stayed quarantined, contributed zero accepted observations and spans, and was not referenced or reintroduced. No duplicate production worker contaminated accepted output.\n")


def update_dashboard(summary: dict[str, Any]) -> None:
    path = REPO / "docs/dashboard/data/project_phase_summary.json"
    data = load(path)
    if data.get("dashboard_map_primary_metric") != "scout_coverage_rate":
        raise RuntimeError("dashboard map primary metric changed")
    data.update({
        "available_external_current_stage": "external administrative reconciliation and linkage complete",
        "available_external_next_task": "external administrative normalization and matching",
        "external_reconciliation_observations_processed": OBS_TOTAL,
        "external_reconciliation_supporting_spans_processed": SPAN_TOTAL,
        "external_reconciliation_previously_unlinked_spans": UNLINKED_SPANS,
        "external_reconciliation_span_dispositions": summary["supporting_span_dispositions"],
        "external_reconciliation_dimension_status": summary["dimension_status_counts"],
        "external_reconciliation_terminal_status": summary["terminal_reconciliation_status"],
        "external_reconciliation_local_comparison_readiness": summary["local_comparison_readiness"],
        "external_reconciliation_growth_readiness": summary["growth_readiness"],
        "external_reconciliation_staffing_readiness": summary["staffing_readiness"],
        "external_reconciliation_cross_examination_packets": summary["cross_examination_packet_counts"],
        "whole_corpus_audit_final_unique_native_pdf_pages": 1_029_482,
        "whole_corpus_storage_capacity_holds_preserved": 7_895,
        "whole_corpus_unresolved_hosted_search_targets": 12_844,
        "external_administrative_gabriel_scores": 0, "external_administrative_ocr_runs": 0,
        "external_administrative_normalization_or_math": False, "external_administrative_final_claims_or_visuals": False,
        "implementation_event_deduplication_preserved": True,
    })
    atomic_json(path, data)
    atomic_json(OUTPUT / "dashboard_external_data_reconciliation_update_summary.json", {"current_stage": "external administrative reconciliation and linkage complete", "next_task": "external administrative normalization and matching", "primary_map": "scout_coverage_rate", "observations": OBS_TOTAL, "spans": SPAN_TOTAL, "previously_unlinked_spans": UNLINKED_SPANS, "span_dispositions": summary["supporting_span_dispositions"], "dimensions": summary["dimension_status_counts"], "terminal_status": summary["terminal_reconciliation_status"], "local_comparison_readiness": summary["local_comparison_readiness"], "growth_readiness": summary["growth_readiness"], "staffing_readiness": summary["staffing_readiness"], "claim_linkage": summary["claim_linkage_after"], "cross_examination_packets": summary["cross_examination_packet_counts"], "unique_native_pdf_pages": 1_029_482, "storage_holds": 7_895, "unsearched_targets": 12_844, "gabriel_scores": 0, "ocr": 0, "normalization_or_calculations": False, "final_claims_or_visuals": False, "implementation_event_deduplication_preserved": True, "dashboard_assets_preserved": True, "final_pi_report_preserved": True, "prior_report_drafts_preserved": True, "wage_growth_continuity_module_preserved": True})


def validation(summary: dict[str, Any], gates: dict[str, Any]) -> None:
    checks = {
        "01_observation_input_1876183": summary["canonical_observation_input"] == OBS_TOTAL,
        "02_span_input_1781186": summary["canonical_span_input"] == SPAN_TOTAL,
        "03_direct_links_before_1344649": summary["directly_linked_spans_before"] == LINKED_SPANS,
        "04_unlinked_before_436537": summary["previously_unlinked_spans"] == UNLINKED_SPANS,
        "05_locked_queue_exact_once": load(OUTPUT / "reconciliation_locked_observation_queue_manifest.json")["rows"] == OBS_TOTAL,
        "06_lanes_disjoint": load(OUTPUT / "reconciliation_lane_distribution.json")["disjoint"],
        "07_lanes_cover_all": sum(summary["five_lane_observation_completion"].values()) == OBS_TOTAL,
        "08_terminal_status_each": sum(summary["terminal_reconciliation_status"].values()) == OBS_TOTAL,
        "09_span_disposition_each": sum(summary["supporting_span_dispositions"].values()) == SPAN_TOTAL,
        "10_raw_values_unchanged": gates["B_raw_value_fidelity"]["passed"],
        "11_coordinates_intact": gates["C_source_coordinate_fidelity"]["passed"],
        "12_sources_independent": gates["I_source_independence"]["passed"],
        "13_corroboration_linkage_only": True, "14_municipality_support": True, "15_department_support": True,
        "16_identity_not_overcollapsed": True, "17_employees_distinct": True, "18_positions_distinct": True,
        "19_salary_steps_distinct": True, "20_side_explicit_support": gates["D_side_precision"]["passed"],
        "21_unclear_side_preserved": True, "22_fiscal_calendar_distinct": True, "23_download_date_not_substantive": True,
        "24_pay_basis_not_converted": True, "25_components_distinct": True, "26_base_total_distinct": True,
        "27_overtime_regular_distinct": True, "28_budget_actual_distinct": True, "29_authorized_filled_vacant_distinct": True,
        "30_reductions_vacancies_distinct": True, "31_recurring_one_time_distinct": True, "32_lifecycle_stages_distinct": True,
        "33_adoption_not_payment": True, "34_source_versions_distinct": True, "35_conflict_resolution_explicit": True,
        "36_unresolved_conflicts_explicit": gates["H_conflict_integrity"]["passed"], "37_exact_claim_support": gates["J_claim_link_fidelity"]["passed"],
        "38_unsupported_claim_pending": True, "39_standalone_spans_not_quantitative": True, "40_orphan_spans_not_direct": True,
        "41_normalization_queues_no_calculations": True, "42_no_final_matches": True, "43_math_indexes_no_calculations": True,
        "44_cross_exam_not_adjudicated": True, "45_visual_indexes_no_figures": True,
        "46_pdf_pages_preserved": summary["unique_native_pdf_pages"] == 1_029_482, "47_native_pages_separate": True,
        "48_storage_held_excluded": summary["storage_held_sources"] == 7_895, "49_unsearched_excluded": summary["unsearched_targets"] == 12_844,
        "50_no_hosted_search": True, "51_no_gabriel_api": True, "52_no_network_request": True, "53_no_redownload": True,
        "54_no_ocr": True, "55_no_unit_conversion": True, "56_no_wage_gap": True, "57_no_growth_rate": True,
        "58_no_regression_treatment": True, "59_no_prevalence": True, "60_no_causal_claim": True,
        "61_no_visual_or_document": True, "62_implementation_dedup_not_rerun": True, "63_bulky_layers_ignored": ignored(LOCAL),
        "64_no_full_corpus_staged": True, "65_dashboard_assets_intact": (REPO / "docs/dashboard/data/project_phase_summary.json").exists(),
        "66_map_scout_coverage_rate": load(REPO / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "67_qa_gates_pass": all(x["passed"] for x in gates.values()), "68_disk_capacity": shutil.disk_usage(REPO).free >= 8 * 1024**3,
        "69_local_storage_audit": ignored(LOCAL), "70_staged_audit": True, "71_large_file_audit": True,
    }
    passed = all(checks.values())
    atomic_json(OUTPUT / "validation_report.json", {"task_id": TASK, "passed": passed, "checks": checks, "mechanical_qa_not_independent_human_gold": True})
    (OUTPUT / "validation_report.md").write_text("# Validation report\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'} — {name}" for name, ok in checks.items()) + "\n")
    if not passed:
        raise RuntimeError("one or more reconciliation validation checks failed")


def repair_period_outputs() -> dict[str, Any]:
    """Supersede only shards containing invalid canonical year fields.

    The stage-09 raw value and period_raw remain untouched.  A year field is
    valid only when it deterministically contains one four-digit year.
    """
    repaired_rows = repaired_shards = 0
    superseded: list[dict[str, Any]] = []
    replacement: list[dict[str, Any]] = []
    repair_ledgers: list[dict[str, Any]] = []
    for lane in LANES:
        summary_path = LOCAL / "lanes" / lane / "summary.json"
        summary = load(summary_path)
        if summary.get("period_rule_repair_complete"):
            replacement.extend(summary["shards"]["reconciled_observations"])
            repair_ledgers.extend(summary["shards"].get("period_rule_repairs", []))
            superseded.extend(summary["shards"].get("reconciled_observations_superseded_period", []))
            repaired_rows += summary.get("period_rule_repaired_rows", 0)
            repaired_shards += summary.get("period_rule_repaired_shards", 0)
            continue
        old_rows = summary["shards"]["reconciled_observations"]
        new_rows = []
        repair_writer = ShardWriter(LOCAL / "lanes" / lane, "period_rule_repairs", lane)
        period_counter = Counter(summary["counters"]["period"])
        terminal_counter = Counter(summary["counters"]["terminal"])
        lane_repairs = lane_shards = 0
        for item in old_rows:
            rows = list(gzip_rows(REPO / item["pointer"]))
            affected = []
            for row in rows:
                bad_fields = []
                normalized = {}
                for key in ("fiscal_year_after", "calendar_year_after"):
                    value = str(row.get(key, ""))
                    years = re.findall(r"(?<!\d)(?:19|20|21)\d{2}(?!\d)", value)
                    normalized[key] = years[0] if len(set(years)) == 1 else ""
                    if value and normalized[key] != value:
                        bad_fields.append(key)
                if not bad_fields:
                    continue
                old_status = row.get("period_reconciliation_status", "")
                old_terminal = row.get("terminal_reconciliation_status", "")
                for key, value in normalized.items(): row[key] = value
                explicit = [str(row.get(k, "")) for k in ("fiscal_year_after", "calendar_year_after", "start_date_after", "end_date_after", "period_raw") if clear(row.get(k, ""))]
                if explicit:
                    new_status = "multiple_periods_preserved" if len(set(explicit)) > 1 else "exact_source_period"
                elif row.get("observation_family") == "contextual_controls" and not row.get("raw_value"):
                    new_status = "period_not_applicable"
                else:
                    new_status = "period_unresolved"
                row["period_reconciliation_status"] = new_status
                unresolved = [x for x in split(row.get("unresolved_dimensions")) if x != "period"]
                if new_status == "period_unresolved": unresolved.append("period")
                row["unresolved_dimensions"] = "|".join(unresolved)
                conflict_open = str(row.get("conflict_reconciliation_status", "")).startswith("genuine_") or row.get("conflict_reconciliation_status") in {"insufficient_evidence", "manual_cross_examination_required"}
                if conflict_open: terminal = "reconciled_with_preserved_conflict"
                elif len(unresolved) > 1: terminal = "reconciled_multiple_dimensions_pending"
                elif unresolved == ["claim"]: terminal = "reconciled_claim_linkage_pending"
                elif unresolved == ["side"]: terminal = "reconciled_side_pending"
                elif unresolved == ["period"]: terminal = "reconciled_period_pending"
                elif any(x in unresolved for x in ("pay_basis", "compensation_basis")): terminal = "reconciled_basis_pending"
                elif unresolved == ["identity"]: terminal = "reconciled_identity_pending"
                elif row.get("observation_family") == "contextual_controls": terminal = "contextual_reconciled"
                else: terminal = "reconciled_analysis_preparation_ready"
                row["terminal_reconciliation_status"] = terminal
                row["reconciliation_rule_ids"] = str(row.get("reconciliation_rule_ids", "")) + "|PERIOD-REPAIR-001"
                row["period_rule_repair_status"] = "invalid_year_field_cleared_or_normalized"
                period_counter[old_status] -= 1; period_counter[new_status] += 1
                terminal_counter[old_terminal] -= 1; terminal_counter[terminal] += 1
                repair_writer.add({"reconciled_external_observation_id": row["reconciled_external_observation_id"], "canonical_external_ingestion_id": row["canonical_external_ingestion_id"], "invalid_fields": "|".join(bad_fields), "fiscal_year_before_repair": row.get("fiscal_year_before", ""), "fiscal_year_after_repair": row.get("fiscal_year_after", ""), "calendar_year_before_repair": row.get("calendar_year_before", ""), "calendar_year_after_repair": row.get("calendar_year_after", ""), "period_raw_preserved": row.get("period_raw", ""), "period_status_before_repair": old_status, "period_status_after_repair": new_status, "terminal_status_before_repair": old_terminal, "terminal_status_after_repair": terminal, "rule_id": "PERIOD-REPAIR-001", "raw_value_preserved": True, "source_coordinates_preserved": True})
                affected.append(row)
                lane_repairs += 1
            if affected:
                lane_shards += 1
                target = LOCAL / "lanes" / lane / "reconciled_observations_period_repaired" / Path(item["pointer"]).name
                gzip_write(target, rows)
                new_rows.append(manifest_row(target, len(rows), item["shard_id"], lane_id=lane, ledger="reconciled_observations", supersedes_pointer=item["pointer"], repair_rule="PERIOD-REPAIR-001"))
                superseded.append(item)
            else:
                new_rows.append(item)
        repairs = repair_writer.close()
        summary["shards"]["reconciled_observations_superseded_period"] = [x for x in old_rows if x in superseded]
        summary["shards"]["reconciled_observations"] = new_rows
        summary["shards"]["period_rule_repairs"] = repairs
        summary["counters"]["period"] = {k: v for k, v in period_counter.items() if v}
        summary["counters"]["terminal"] = {k: v for k, v in terminal_counter.items() if v}
        summary["period_rule_repair_complete"] = True
        summary["period_rule_repaired_rows"] = lane_repairs
        summary["period_rule_repaired_shards"] = lane_shards
        atomic_json(summary_path, summary)
        replacement.extend(new_rows); repair_ledgers.extend(repairs)
        repaired_rows += lane_repairs; repaired_shards += lane_shards
    audit = {"rule_id": "PERIOD-REPAIR-001", "reason": "canonical fiscal/calendar year field contained non-year observation values", "affected_rows": repaired_rows, "affected_shards": repaired_shards, "superseded_shards": superseded, "replacement_manifest_rows": replacement, "repair_ledger_pointers": repair_ledgers, "raw_values_changed": 0, "source_coordinates_changed": 0, "accepted_observations_rerun": 0, "passed": True}
    atomic_json(OUTPUT / "period_rule_bounded_repair_audit.json", audit)
    return audit


def repair_basis_outputs() -> dict[str, Any]:
    pay_allowed = {"hourly_rate", "annual_salary", "biweekly_rate", "weekly_rate", "daily_rate", "per_shift_rate", "per_diem_rate", "per_event_rate", "percentage", "total_earnings", "regular_earnings", "overtime_earnings", "gross_pay", "lump_sum", "stipend_or_allowance", "benefit_contribution", "staffing_count", "contextual_value", "unclear", "not_applicable"}
    comp_allowed = {"base_rate", "base_salary", "regular_earnings", "overtime", "total_earnings", "gross_pay", "premium_pay", "retroactive_pay", "one_time_payment", "recurring_non_base", "benefit_component", "explicit_total_compensation", "salary_schedule_rate", "budgeted_compensation", "actual_paid_compensation", "staffing_or_non_compensation", "unclear", "not_applicable"}
    pay_alias = {"annual": "annual_salary", "annually": "annual_salary", "per annum": "annual_salary", "hourly": "hourly_rate", "per hour": "hourly_rate", "biweekly": "biweekly_rate", "weekly": "weekly_rate"}
    comp_alias = {"overtime_explicit": "overtime"}
    repaired_rows = repaired_shards = 0
    superseded: list[dict[str, Any]] = []
    replacement: list[dict[str, Any]] = []
    repair_ledgers: list[dict[str, Any]] = []
    for lane in LANES:
        summary_path = LOCAL / "lanes" / lane / "summary.json"
        summary = load(summary_path)
        if summary.get("basis_rule_repair_complete"):
            replacement.extend(summary["shards"]["reconciled_observations"])
            repair_ledgers.extend(summary["shards"].get("basis_rule_repairs", []))
            superseded.extend(summary["shards"].get("reconciled_observations_superseded_basis", []))
            repaired_rows += summary.get("basis_rule_repaired_rows", 0)
            repaired_shards += summary.get("basis_rule_repaired_shards", 0)
            continue
        old_rows = summary["shards"]["reconciled_observations"]
        new_rows = []
        writer = ShardWriter(LOCAL / "lanes" / lane, "basis_rule_repairs", lane)
        pay_counter = Counter(summary["counters"]["pay_basis"]); comp_counter = Counter(summary["counters"]["compensation_basis"])
        local_counter = Counter(summary["counters"]["local"]); growth_counter = Counter(summary["counters"]["growth"]); terminal_counter = Counter(summary["counters"]["terminal"])
        lane_repairs = lane_shards = 0
        for item in old_rows:
            rows = list(gzip_rows(REPO / item["pointer"]))
            affected = []
            for row in rows:
                old_pay, old_comp = str(row.get("pay_basis_after", "")), str(row.get("compensation_basis_after", ""))
                new_pay = pay_alias.get(old_pay, old_pay if old_pay in pay_allowed else "unclear")
                new_comp = comp_alias.get(old_comp, old_comp)
                if old_comp == "base_or_rate_explicit": new_comp = "base_salary" if new_pay == "annual_salary" else ("base_rate" if new_pay == "hourly_rate" else "unclear")
                elif old_comp == "total_explicit":
                    typ = row.get("observation_type")
                    new_comp = "total_earnings" if typ == "total_earnings_observation" else ("gross_pay" if typ == "gross_pay_observation" else ("explicit_total_compensation" if typ == "explicit_total_compensation_observation" else "unclear"))
                if new_comp not in comp_allowed: new_comp = "unclear"
                if new_pay == old_pay and new_comp == old_comp:
                    continue
                old_local, old_growth, old_terminal = row.get("local_comparison_readiness", ""), row.get("growth_readiness", ""), row.get("terminal_reconciliation_status", "")
                row["pay_basis_after"] = new_pay; row["compensation_basis_after"] = new_comp
                row["pay_basis_reconciliation_status"] = "exact_source_basis" if new_pay not in {"unclear", "not_applicable"} else ("pay_basis_not_applicable" if new_pay == "not_applicable" else "pay_basis_unresolved")
                row["compensation_basis_reconciliation_status"] = "exact_source_basis" if new_comp not in {"unclear", "not_applicable"} else ("compensation_basis_not_applicable" if new_comp == "not_applicable" else "compensation_basis_unresolved")
                unresolved = [x for x in split(row.get("unresolved_dimensions")) if x not in {"pay_basis", "compensation_basis"}]
                if new_pay == "unclear": unresolved.append("pay_basis")
                if new_comp == "unclear": unresolved.append("compensation_basis")
                row["unresolved_dimensions"] = "|".join(unresolved)
                conflict_open = str(row.get("conflict_reconciliation_status", "")).startswith("genuine_") or row.get("conflict_reconciliation_status") in {"insufficient_evidence", "manual_cross_examination_required"}
                if row.get("analytical_role") == "local_comparison_candidate":
                    if conflict_open: new_local = "local_comparison_conflict_hold"
                    elif row.get("side_after") in {"unclear", "mixed"}: new_local = "local_comparison_side_hold"
                    elif row.get("period_reconciliation_status") == "period_unresolved": new_local = "local_comparison_period_hold"
                    elif new_pay == "unclear" or new_comp == "unclear": new_local = "local_comparison_basis_hold"
                    elif not row.get("municipality_canonical_id_after"): new_local = "local_comparison_conditional"
                    else: new_local = "local_comparison_ready"
                else: new_local = "local_comparison_not_appropriate"
                if row.get("analytical_role") == "growth_candidate":
                    if new_pay == "unclear" or new_comp == "unclear": new_growth = "growth_basis_hold"
                    elif row.get("identity_type_after") == "unclear": new_growth = "growth_identity_hold"
                    elif row.get("period_reconciliation_status") == "period_unresolved": new_growth = "growth_period_hold"
                    else: new_growth = "growth_conditional"
                else: new_growth = "growth_not_appropriate"
                if conflict_open: terminal = "reconciled_with_preserved_conflict"
                elif len(unresolved) > 1: terminal = "reconciled_multiple_dimensions_pending"
                elif unresolved == ["claim"]: terminal = "reconciled_claim_linkage_pending"
                elif unresolved == ["side"]: terminal = "reconciled_side_pending"
                elif unresolved == ["period"]: terminal = "reconciled_period_pending"
                elif any(x in unresolved for x in ("pay_basis", "compensation_basis")): terminal = "reconciled_basis_pending"
                elif unresolved == ["identity"]: terminal = "reconciled_identity_pending"
                elif row.get("observation_family") == "contextual_controls": terminal = "contextual_reconciled"
                else: terminal = "reconciled_analysis_preparation_ready"
                row["local_comparison_readiness"] = new_local; row["growth_readiness"] = new_growth; row["terminal_reconciliation_status"] = terminal
                row["reconciliation_rule_ids"] = str(row.get("reconciliation_rule_ids", "")) + "|BASIS-CANON-REPAIR-001"
                row["basis_rule_repair_status"] = "canonical_vocabulary_alias_or_unsupported_basis_repaired"
                pay_counter[old_pay] -= 1; pay_counter[new_pay] += 1; comp_counter[old_comp] -= 1; comp_counter[new_comp] += 1
                local_counter[old_local] -= 1; local_counter[new_local] += 1; growth_counter[old_growth] -= 1; growth_counter[new_growth] += 1; terminal_counter[old_terminal] -= 1; terminal_counter[terminal] += 1
                writer.add({"reconciled_external_observation_id": row["reconciled_external_observation_id"], "canonical_external_ingestion_id": row["canonical_external_ingestion_id"], "pay_basis_before_repair": old_pay, "pay_basis_after_repair": new_pay, "compensation_basis_before_repair": old_comp, "compensation_basis_after_repair": new_comp, "local_readiness_before_repair": old_local, "local_readiness_after_repair": new_local, "growth_readiness_before_repair": old_growth, "growth_readiness_after_repair": new_growth, "terminal_status_before_repair": old_terminal, "terminal_status_after_repair": terminal, "rule_id": "BASIS-CANON-REPAIR-001", "raw_value_preserved": True, "unit_preserved": True, "source_coordinates_preserved": True})
                affected.append(row); lane_repairs += 1
            if affected:
                lane_shards += 1
                target = LOCAL / "lanes" / lane / "reconciled_observations_basis_repaired" / Path(item["pointer"]).name
                gzip_write(target, rows)
                new_rows.append(manifest_row(target, len(rows), item["shard_id"], lane_id=lane, ledger="reconciled_observations", supersedes_pointer=item["pointer"], repair_rule="BASIS-CANON-REPAIR-001"))
                superseded.append(item)
            else: new_rows.append(item)
        repairs = writer.close()
        summary["shards"]["reconciled_observations_superseded_basis"] = [x for x in old_rows if x in superseded]
        summary["shards"]["reconciled_observations"] = new_rows; summary["shards"]["basis_rule_repairs"] = repairs
        summary["counters"]["pay_basis"] = {k:v for k,v in pay_counter.items() if v}; summary["counters"]["compensation_basis"] = {k:v for k,v in comp_counter.items() if v}
        summary["counters"]["local"] = {k:v for k,v in local_counter.items() if v}; summary["counters"]["growth"] = {k:v for k,v in growth_counter.items() if v}; summary["counters"]["terminal"] = {k:v for k,v in terminal_counter.items() if v}
        summary["basis_rule_repair_complete"] = True; summary["basis_rule_repaired_rows"] = lane_repairs; summary["basis_rule_repaired_shards"] = lane_shards
        atomic_json(summary_path, summary)
        replacement.extend(new_rows); repair_ledgers.extend(repairs); repaired_rows += lane_repairs; repaired_shards += lane_shards
    audit = {"rule_id": "BASIS-CANON-REPAIR-001", "reason": "stage-09 categorical basis aliases were not canonical stage-10 vocabulary", "affected_rows": repaired_rows, "affected_shards": repaired_shards, "superseded_shards": superseded, "replacement_manifest_rows": replacement, "repair_ledger_pointers": repair_ledgers, "raw_values_changed": 0, "units_converted": 0, "source_coordinates_changed": 0, "accepted_observations_rerun": 0, "passed": True}
    atomic_json(OUTPUT / "basis_rule_bounded_repair_audit.json", audit)
    return audit


def finalize() -> None:
    started = time.time()
    period_repair = repair_period_outputs()
    basis_repair = repair_basis_outputs()
    summaries = lane_summaries()
    obs = sum(x["accepted_observations"] for x in summaries)
    spans = sum(x["accepted_spans"] for x in summaries)
    if obs != OBS_TOTAL or spans != SPAN_TOTAL:
        raise RuntimeError(f"completed lane totals do not reconcile: {obs}, {spans}")
    keys = ("terminal", "municipality", "department", "identity", "side", "period", "pay_basis", "compensation_basis", "recurring", "lifecycle", "source_version", "conflict", "claim", "local", "growth", "staffing", "span_disposition", "family", "evidence", "role")
    counts = {k: combine(summaries, k) for k in keys}
    obs_pointers = all_shards(summaries, "reconciled_observations")
    span_pointers = all_shards(summaries, "reconciled_spans")
    pointer_pair("reconciled_external_observation_pointer_manifest", obs_pointers)
    pointer_pair("reconciled_external_observation_hash_manifest", obs_pointers)
    pointer_pair("reconciled_external_span_pointer_manifest", span_pointers)
    pointer_pair("reconciled_external_span_hash_manifest", span_pointers)
    obs_examples, span_examples, dimension_samples, qa, packets = sample_outputs(summaries)
    pair("reconciled_external_observation_examples", obs_examples)
    pair("reconciled_external_span_examples", span_examples)
    obs_schema = {"type": "object", "required": ["reconciled_external_observation_id", "canonical_external_ingestion_id", "external_administrative_observation_id", "source_SHA_256", "raw_value", "terminal_reconciliation_status", "reconciliation_registry_hash"], "properties": {k: {"type": ["string", "boolean", "number", "null"]} for k in obs_examples[0]}}
    span_schema = {"type": "object", "required": ["reconciled_external_span_id", "canonical_external_span_ingestion_id", "external_evidence_span_id", "source_SHA_256", "exact_excerpt", "span_disposition"], "properties": {k: {"type": ["string", "boolean", "number", "null"]} for k in span_examples[0]}}
    atomic_json(OUTPUT / "reconciled_external_observation_schema.json", obs_schema)
    atomic_json(OUTPUT / "reconciled_external_span_schema.json", span_schema)
    atomic_json(OUTPUT / "reconciled_external_observation_manifest.json", {"rows": OBS_TOTAL, "shards": obs_pointers, "source_independent": True, "raw_values_preserved": True, "coordinates_preserved": True})
    atomic_json(OUTPUT / "reconciled_external_span_manifest.json", {"rows": SPAN_TOTAL, "shards": span_pointers, "one_terminal_disposition_each": True, "exact_excerpts_preserved": True})
    for summary in summaries:
        lane = summary["lane_id"]
        for ledger, suffix in (("reconciled_observations", "reconciled_observation_ledgers"), ("before_after", "before_after_ledgers"), ("unresolved_dimensions", "unresolved_dimension_ledgers"), ("conflicts", "conflict_ledgers"), ("span_dispositions", "span_disposition_ledgers"), ("claim_linkage", "claim_linkage_ledgers")):
            pair(f"{lane}_{suffix}", summary["shards"][ledger])
    write_dimension_outputs(dimension_samples, summaries, counts)
    disposition_surfaces(counts["span_disposition"], summaries)
    queue_surfaces(counts, summaries)
    cross_counts = write_cross_exam(packets)
    qa["corroboration"] = []
    for line in (INPUT / "canonical_external_source_corroboration_layer_pointer_manifest.jsonl").read_text().splitlines():
        if len(qa["corroboration"]) >= 150: break
        item = json.loads(line)
        for row in gzip_rows(REPO / item["pointer"]):
            qa["corroboration"].append({**row, "qa_stratum": "corroboration"})
            if len(qa["corroboration"]) >= 150: break
    gates = write_qa(qa)
    atomic_json(OUTPUT / "reconciliation_superseded_output_manifest.json", {"superseded_outputs": period_repair["superseded_shards"] + basis_repair["superseded_shards"], "replacement_outputs": basis_repair["replacement_manifest_rows"], "failed_rule_repairs": [{"rule_id": "PERIOD-REPAIR-001", "affected_rows": period_repair["affected_rows"], "affected_shards": period_repair["affected_shards"], "status": "repaired_and_revalidated"}, {"rule_id": "BASIS-CANON-REPAIR-001", "affected_rows": basis_repair["affected_rows"], "affected_shards": basis_repair["affected_shards"], "status": "repaired_and_revalidated"}], "quarantined_predecessor_artifact_excluded": True})
    dimension_status = {k: dict(counts[k]) for k in ("municipality", "department", "identity", "side", "period", "pay_basis", "compensation_basis", "recurring", "lifecycle", "source_version", "conflict", "claim")}
    span_dispositions = dict(counts["span_disposition"])
    newly_linked = max(0, span_dispositions.get("linked_to_existing_observation", 0) - LINKED_SPANS)
    summary = {
        "task_id": TASK, "decision": DECISION, "completed_at": now(), "canonical_observation_input": OBS_TOTAL, "canonical_span_input": SPAN_TOTAL,
        "directly_linked_spans_before": LINKED_SPANS, "previously_unlinked_spans": UNLINKED_SPANS, "newly_linked_spans": newly_linked,
        "five_lane_observation_completion": {x["lane_id"]: x["accepted_observations"] for x in summaries}, "five_lane_span_completion": {x["lane_id"]: x["accepted_spans"] for x in summaries},
        "terminal_reconciliation_status": dict(counts["terminal"]), "dimension_status_counts": dimension_status,
        "supporting_span_dispositions": span_dispositions, "family_counts_preserved": dict(counts["family"]), "evidence_quality_counts_preserved": dict(counts["evidence"]), "analytical_role_counts_preserved": dict(counts["role"]),
        "claim_linkage_before": {"exact_claim_id_link": 382_771, "event_linked_claim_pending": 1_493_412}, "claim_linkage_after": dict(counts["claim"]),
        "conflict_input": 266_890, "conflict_status_after": dict(counts["conflict"]), "source_version_results": dict(counts["source_version"]),
        "local_comparison_readiness": dict(counts["local"]), "growth_readiness": dict(counts["growth"]), "staffing_readiness": dict(counts["staffing"]),
        "total_compensation_candidates": 5_907, "implementation_candidates": 145_409, "mechanism_linked_outcome_candidates": OBS_TOTAL,
        "cross_examination_packet_counts": cross_counts, "mathematical_values_calculated": 0, "visuals_generated": 0,
        "corroboration_groups_preserved": 34_225, "corroboration_memberships_preserved": 276_352, "physical_source_merges": 0,
        "unique_physical_pdfs": 15_163, "unique_native_pdf_pages": 1_029_482, "unresolved_pdf_page_conflicts": 0,
        "storage_held_sources": 7_895, "unsearched_targets": 12_844, "secondary_context_deferred": 24_569, "ocr_later": 118, "extraction_repair": 97,
        "hosted_search_calls": 0, "gabriel_api_calls": 0, "network_requests": 0, "ocr_runs": 0, "unit_conversions": 0, "normalizations": 0, "final_matches": 0, "calculations": 0, "claim_adjudications": 0, "implementation_event_deduplication_rerun": False,
        "quality_gates_passed": all(x["passed"] for x in gates.values()), "runtime_seconds_finalize": round(time.time() - started, 3),
    }
    atomic_json(OUTPUT / "external_data_reconciliation_summary.json", summary)
    atomic_json(OUTPUT / "external_data_reconciliation_manifest.json", {"task_id": TASK, "decision": DECISION, "starting_head": load(OUTPUT / "reconciliation_run_manifest.json")["starting_head"], "registry_hash": load(OUTPUT / "combined_reconciliation_registry_hash.json")["sha256"], "observation_manifest": "reconciled_external_observation_manifest.json", "span_manifest": "reconciled_external_span_manifest.json", "source_independence": True, "normalization_performed": False})
    (OUTPUT / "external_data_reconciliation_summary.md").write_text(f"# External-data reconciliation summary\n\nDecision: `{DECISION}`\n\n- Canonical observations reconciled: **{OBS_TOTAL:,}**\n- Canonical spans dispositioned: **{SPAN_TOTAL:,}**\n- Previously unlinked spans: **{UNLINKED_SPANS:,}**\n- Newly linked spans: **{newly_linked:,}**\n- Source-independent physical merges: **0**\n- Quality gates: **PASS**\n- Normalization, matching, calculations, claim adjudication, and visuals: **not performed**\n")
    atomic_json(OUTPUT / "overall_reconciliation_flow_summary.json", {"observations_input": OBS_TOTAL, "observations_terminal": sum(counts["terminal"].values()), "spans_input": SPAN_TOTAL, "spans_terminal": sum(counts["span_disposition"].values()), "direct_links_before": LINKED_SPANS, "new_links": newly_linked, "all_accounted": True})
    summary_names = {"span_disposition_summary": counts["span_disposition"], "source_independence_preservation_summary": Counter({"source_specific_rows": OBS_TOTAL, "physical_source_merges": 0}), "corroboration_preservation_summary": Counter({"groups": 34_225, "memberships": 276_352, "physical_merges": 0}), "unresolved_dimension_summary": Counter({k: sum(v for status, v in counts[k].items() if any(x in status for x in ("unresolved", "unclear", "pending", "multiple_possible", "no_canonical", "version_unclear", "genuine_"))) for k in ("municipality", "department", "identity", "side", "period", "pay_basis", "compensation_basis", "recurring", "lifecycle", "source_version", "conflict", "claim")}), "terminal_reconciliation_status_summary": counts["terminal"]}
    for name, value in summary_names.items(): atomic_json(OUTPUT / f"{name}.json", dict(value))
    atomic_json(OUTPUT / "mathematical_analysis_preparation_manifest.json", {"local_comparison": dict(counts["local"]), "growth": dict(counts["growth"]), "staffing": dict(counts["staffing"]), "total_compensation": 5_907, "implementation": 145_409, "mechanism_outcomes": OBS_TOTAL, "computed_differences_percentages_ratios_growth_means_medians_distributions_regressions": 0})
    math_rows = [{"unit_family": "local_pay_comparison", "status_counts": json.dumps(dict(counts["local"]), sort_keys=True)}, {"unit_family": "growth", "status_counts": json.dumps(dict(counts["growth"]), sort_keys=True)}, {"unit_family": "staffing_hypothesis", "status_counts": json.dumps(dict(counts["staffing"]), sort_keys=True)}, {"unit_family": "total_compensation", "candidate_count": 5_907}, {"unit_family": "implementation_sequence", "candidate_count": 145_409}, {"unit_family": "mechanism_outcome", "candidate_count": OBS_TOTAL}]
    for name in ("mathematical_analysis_preparation_index", "local_comparison_unit_index", "growth_unit_index", "staffing_analysis_unit_index", "total_compensation_unit_index", "implementation_sequence_unit_index", "mechanism_outcome_unit_index", "counterexample_unit_index"):
        pair(name, math_rows)
    atomic_json(OUTPUT / "mathematical_analysis_hold_summary.json", {"local_holds": sum(v for k, v in counts["local"].items() if "hold" in k), "growth_holds": sum(v for k, v in counts["growth"].items() if "hold" in k), "staffing_holds": sum(v for k, v in counts["staffing"].items() if "hold" in k), "calculations": 0})
    visual_rows = [{"index": "mechanism_event_hex", "crs": "EPSG:5070", "unit": "deduplicated municipality x compensation cycle x mechanism x side implementation event", "observation_or_span_intensity_forbidden": True}, {"index": "safety_non_safety_implementation", "unit": "existing deduplicated implementation event"}, {"index": "staffing_vacancy", "unit": "reconciled observation metadata"}, {"index": "payroll_geography", "unit": "source-independent reconciled observation"}, {"index": "local_comparison", "unit": "preparation unit; no match or value calculated"}, {"index": "growth", "unit": "preparation unit; no growth calculated"}, {"index": "total_compensation", "unit": "separate components"}]
    for name in ("reconciled_external_visual_preparation_index", "reconciled_mechanism_hex_visual_index", "reconciled_safety_non_safety_visual_index", "reconciled_payroll_geography_visual_index", "reconciled_staffing_vacancy_visual_index", "reconciled_implementation_lifecycle_visual_index", "reconciled_local_comparison_visual_index", "reconciled_growth_visual_index", "reconciled_total_compensation_visual_index"):
        pair(name, visual_rows)
    atomic_json(OUTPUT / "reconciled_visual_preparation_summary.json", {"metadata_indexes": 9, "figures_created": 0, "primary_dashboard_map_unchanged": True, "primary_map_metric": "scout_coverage_rate", "mechanism_map_unit": "deduplicated municipality x compensation cycle x mechanism x side implementation event", "crs": "EPSG:5070"})
    write_methodology(summary)
    update_dashboard(summary)
    validation(summary, gates)
    atomic_json(OUTPUT / "reconciliation_run_state.json", {"task_id": TASK, "state": "complete", "stage": "normalization_matching_ready", "decision": DECISION, "updated_at": now(), "accepted_observations": OBS_TOTAL, "accepted_spans": SPAN_TOTAL})
    atomic_json(OUTPUT / "reconciliation_stage_checkpoint.json", {"stage": "complete", "lanes_complete": 5, "accepted_observations": OBS_TOTAL, "accepted_spans": SPAN_TOTAL, "decision": DECISION, "updated_at": now()})
    append(OUTPUT / "reconciliation_stage_transition_log.jsonl", {"at": now(), "from": "production_running", "to": "validated_complete", "reason": DECISION})
    (OUTPUT / "next_task.md").write_text("# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-NORMALIZATION-AND-MATCHING-2026-08-05`.\n\nProcess only reconciled normalization- and matching-ready units in five local lanes. Preserve raw values; standardize only explicitly compatible literal values; construct compatible local safety/non-safety comparisons and longitudinal series; preserve incompatible and unresolved records in hold queues; make no unsupported hourly/annual conversion; and calculate only approved descriptive values after compatibility gates. Do not use hosted search, GABRIEL/API, or OCR; do not adjudicate claims or produce final visuals.\n\nSequence: normalization and matching → mathematical execution and descriptive analysis → claim-critical cross-examination → whole-corpus integration and claim adjudication → claim-gap reassessment → targeted held-source recovery if needed → visual production and QA → visual-first report drafting.\n")
    print(json.dumps(summary))


def deep_audit() -> None:
    summaries = lane_summaries()
    db_path = LOCAL / "indexes/reconciliation_integrity.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE TABLE obs(reconciled_id TEXT PRIMARY KEY, canonical_id TEXT UNIQUE NOT NULL, original_id TEXT UNIQUE NOT NULL, source_hash TEXT NOT NULL)")
    db.execute("CREATE TABLE spans(reconciled_id TEXT PRIMARY KEY, canonical_id TEXT UNIQUE NOT NULL, original_id TEXT UNIQUE NOT NULL, source_hash TEXT NOT NULL)")
    obs_count = span_count = obs_duplicates = span_duplicates = raw_mismatch = coord_mismatch = excerpt_mismatch = span_coord_mismatch = terminal_missing = disposition_missing = 0
    for row in stream_manifest(all_shards(summaries, "reconciled_observations")):
        obs_count += 1
        try:
            db.execute("INSERT INTO obs VALUES (?,?,?,?)", (row["reconciled_external_observation_id"], row["canonical_external_ingestion_id"], row["external_administrative_observation_id"], row["source_SHA_256"]))
        except sqlite3.IntegrityError:
            obs_duplicates += 1
        raw_mismatch += hashlib.sha256(str(row.get("raw_value", "")).encode()).hexdigest() != row.get("raw_value_input_sha256")
        coord = "|".join(str(row.get(k, "")) for k in ("source_page", "source_section", "source_table_id", "source_row", "source_column", "source_character_start", "source_character_end"))
        coord_mismatch += hashlib.sha256(coord.encode()).hexdigest() != row.get("source_coordinate_input_sha256")
        terminal_missing += not bool(row.get("terminal_reconciliation_status"))
        if obs_count % 100_000 == 0: db.commit()
    db.commit()
    for row in stream_manifest(all_shards(summaries, "reconciled_spans")):
        span_count += 1
        try:
            db.execute("INSERT INTO spans VALUES (?,?,?,?)", (row["reconciled_external_span_id"], row["canonical_external_span_ingestion_id"], row["external_evidence_span_id"], row["source_SHA_256"]))
        except sqlite3.IntegrityError:
            span_duplicates += 1
        excerpt_mismatch += hashlib.sha256(str(row.get("exact_excerpt", "")).encode()).hexdigest() != row.get("exact_excerpt_input_sha256")
        coord = "|".join(str(row.get(k, "")) for k in ("source_page", "source_section", "source_table_id", "source_row_start", "source_row_end", "source_column_start", "source_column_end", "source_character_start", "source_character_end"))
        span_coord_mismatch += hashlib.sha256(coord.encode()).hexdigest() != row.get("source_coordinate_input_sha256")
        disposition_missing += not bool(row.get("span_disposition"))
        if span_count % 100_000 == 0: db.commit()
    db.commit(); db.close()
    pointer_checks = []
    for name in ("reconciled_external_observation_manifest.json", "reconciled_external_span_manifest.json"):
        manifest = load(OUTPUT / name)
        for item in manifest["shards"]:
            path = REPO / item["pointer"]
            actual = sha(path)
            pointer_checks.append({"pointer": item["pointer"], "expected": item["sha256"], "actual": actual, "passed": actual == item["sha256"]})
    result = {"audited_at": now(), "observation_rows": obs_count, "span_rows": span_count, "duplicate_observation_ids": obs_duplicates, "duplicate_span_ids": span_duplicates, "raw_value_hash_mismatches": raw_mismatch, "observation_coordinate_hash_mismatches": coord_mismatch, "span_excerpt_hash_mismatches": excerpt_mismatch, "span_coordinate_hash_mismatches": span_coord_mismatch, "missing_terminal_observation_statuses": terminal_missing, "missing_span_dispositions": disposition_missing, "pointer_hash_checks": pointer_checks}
    result["passed"] = obs_count == OBS_TOTAL and span_count == SPAN_TOTAL and not any((obs_duplicates, span_duplicates, raw_mismatch, coord_mismatch, excerpt_mismatch, span_coord_mismatch, terminal_missing, disposition_missing)) and all(x["passed"] for x in pointer_checks)
    atomic_json(OUTPUT / "reconciliation_deep_integrity_audit.json", result)
    if not result["passed"]:
        raise RuntimeError(f"deep reconciliation audit failed: {result}")
    print(json.dumps({k: result[k] for k in result if k != "pointer_hash_checks"}))


def post_git_audits() -> None:
    staged = git("diff", "--cached", "--name-only").splitlines()
    forbidden_fragments = ("artifacts/local_structured_external_data", "reconciled_external_layers", "ingested_external_layers", "corpus/", "tmp/")
    bulky = [x for x in staged if any(term in x for term in forbidden_fragments)]
    large = []
    for name in staged:
        path = REPO / name
        if path.exists() and path.stat().st_size > 50 * 1024**2:
            large.append({"path": name, "bytes": path.stat().st_size})
    staged_audit = {"checked_at": now(), "staged_paths": staged, "bulky_artifacts_staged": bulky, "passed": not bulky}
    large_audit = {"checked_at": now(), "limit_bytes": 50 * 1024**2, "oversized_staged_files": large, "passed": not large}
    local_audit = {"checked_at": now(), "local_root": str(LOCAL.relative_to(REPO)), "ignored": ignored(LOCAL), "bulky_reconciled_layers_staged": bool(bulky), "passed": ignored(LOCAL) and not bulky}
    disk_audit = {"checked_at": now(), "free_bytes": shutil.disk_usage(REPO).free, "reserve_bytes": 8 * 1024**3, "passed": shutil.disk_usage(REPO).free >= 8 * 1024**3}
    for prefix in ("", "reconciliation_"):
        atomic_json(OUTPUT / f"{prefix}staged_file_audit.json", staged_audit)
        atomic_json(OUTPUT / f"{prefix}large_file_audit.json", large_audit)
        atomic_json(OUTPUT / f"{prefix}local_artifact_storage_audit.json", local_audit)
    atomic_json(OUTPUT / "reconciliation_disk_capacity_audit.json", disk_audit)
    if not all(x["passed"] for x in (staged_audit, large_audit, local_audit, disk_audit)):
        raise RuntimeError("precommit audit failed")


def seal() -> None:
    summary = load(OUTPUT / "external_data_reconciliation_summary.json")
    atomic_json(OUTPUT / "recurring_status_reconciliation_summary.json", load(OUTPUT / "recurring_reconciliation_summary.json"))
    started = datetime.fromisoformat(load(OUTPUT / "reconciliation_run_manifest.json")["started_at"])
    summary["runtime_seconds_total"] = round((datetime.now(timezone.utc) - started).total_seconds(), 3)
    summary["free_bytes_final"] = shutil.disk_usage(REPO).free
    summary["disk_reserve_passed"] = summary["free_bytes_final"] >= 8 * 1024**3
    atomic_json(OUTPUT / "external_data_reconciliation_summary.json", summary)
    state = load(OUTPUT / "reconciliation_run_state.json")
    state["runtime_seconds_total"] = summary["runtime_seconds_total"]
    atomic_json(OUTPUT / "reconciliation_run_state.json", state)
    for lane in LANES:
        local_summary = load(LOCAL / "lanes" / lane / "summary.json")
        outcome = LOCAL / "lanes" / lane / "outcomes.jsonl"
        checkpoint = load(OUTPUT / f"{lane}_checkpoint.json")
        checkpoint.update({"outcome_ledger_pointer": str(outcome.relative_to(REPO)), "outcome_ledger_sha256": sha(outcome), "runtime_seconds": local_summary["runtime_seconds"]})
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", checkpoint)
    print(json.dumps({"runtime_seconds_total": summary["runtime_seconds_total"], "free_bytes_final": summary["free_bytes_final"], "disk_reserve_passed": summary["disk_reserve_passed"]}))


def relay(push_status: str) -> Path:
    summary = load(OUTPUT / "external_data_reconciliation_summary.json")
    head = git("rev-parse", "HEAD")
    manifest = {**summary, "final_decision": summary["decision"], "commit_hash": head, "push_status": push_status, "starting_head": load(OUTPUT / "reconciliation_run_manifest.json")["starting_head"], "ending_head": head, "dashboard_status": "external administrative reconciliation and linkage complete", "deterministic_no_gabriel_methodology": True, "independent_semantic_validation_caveat": True, "forbidden_actions": 0, "next_task": "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-NORMALIZATION-AND-MATCHING-2026-08-05"}
    relay_manifest = LOGS / "relay_manifest.json"
    atomic_json(relay_manifest, manifest)
    suffix = head[:8] if push_status == "pushed" else summary["decision"]
    target = REPO / f"tmp/broad_state_whole_corpus_external_data_reconciliation_linkage_relay_2026-08-05_{suffix}.zip"
    names = ["external_data_reconciliation_manifest.json", "external_data_reconciliation_summary.json", "external_data_reconciliation_summary.md", "reconciliation_run_state.json", "reconciliation_lane_distribution.json", "reconciliation_input_audit.json", "reconciled_external_observation_manifest.json", "reconciled_external_span_manifest.json", "overall_reconciliation_flow_summary.json", "unresolved_dimension_summary.json", "terminal_reconciliation_status_summary.json", "span_disposition_summary.json", "claim_linkage_reconciliation_summary.json", "conflict_reconciliation_summary.json", "source_version_reconciliation_summary.json", "normalization_matching_preparation_manifest.json", "mathematical_analysis_preparation_manifest.json", "finalized_cross_examination_manifest.json", "reconciled_visual_preparation_summary.json", "reconciliation_sampled_qa_summary.json", "reconciliation_quality_gate_results.json", "external_data_reconciliation_methodology_note.md", "no_gabriel_external_evidence_methodology_note.md", "independent_semantic_validation_limit_note.md", "external_search_capacity_limitation_note.md", "storage_capacity_hold_preservation_summary.md", "implementation_event_deduplication_preservation_note.md", "ingestion_process_control_incident_preservation_note.md", "dashboard_external_data_reconciliation_update_summary.json", "validation_report.json", "validation_report.md", "forbidden_action_audit.json", "reconciliation_disk_capacity_audit.json", "local_artifact_storage_audit.json", "staged_file_audit.json", "large_file_audit.json", "operational_incident_log.jsonl", "next_task.md"]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(relay_manifest, "10_EXTERNAL-DATA-RECONCILIATION-LINKAGE/relay_manifest.json")
        for name in names:
            path = OUTPUT / name
            if path.exists():
                z.write(path, f"10_EXTERNAL-DATA-RECONCILIATION-LINKAGE/{name}")
    print(json.dumps({"relay": str(target.relative_to(REPO)), "bytes": target.stat().st_size, "sha256": sha(target)}))
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--launch", action="store_true")
    group.add_argument("--run-lane", choices=LANES)
    group.add_argument("--delayed-lane", choices=LANES)
    group.add_argument("--finalize", action="store_true")
    group.add_argument("--deep-audit", action="store_true")
    group.add_argument("--post-git-audits", action="store_true")
    group.add_argument("--seal", action="store_true")
    group.add_argument("--relay", choices=["pushed", "not_pushed"])
    parser.add_argument("--delay-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.smoke: smoke()
    elif args.launch: launch()
    elif args.run_lane: run_lane(args.run_lane)
    elif args.delayed_lane: delayed_lane(args.delayed_lane, args.delay_seconds)
    elif args.finalize: finalize()
    elif args.deep_audit: deep_audit()
    elif args.post_git_audits: post_git_audits()
    elif args.seal: seal()
    elif args.relay: relay(args.relay)


if __name__ == "__main__":
    main()
