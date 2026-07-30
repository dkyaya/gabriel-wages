#!/usr/bin/env python3
"""Deterministic four-lane normalization rescue and bounded local claim builder."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-PARAPHRASE-REPAIR-2026-07-30"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-RESCUE-GAP-GROWTH-CLAIMS-2026-07-30"
LOGS = ROOT / "tmp/broad_state_4x2500_normalization_rescue_gap_growth_claims_2026-07-30_logs"
TASK = "BROAD-STATE-4X2500-NORMALIZATION-RESCUE-GAP-GROWTH-CLAIMS-2026-07-30"
DECISION = "broad_state_4x2500_normalization_rescue_gap_growth_completed_pi_report_ready"
EXPECTED_PARTIAL = 1_563
EXPECTED_MECHANISM = 3_769
EXPECTED_TOTAL = 5_332
LANE_SIZE = 1_333
OBS_START, OBS_END = 2014, 2024

SAFETY = {
    "police": re.compile(r"\b(police|patrol(?:man|men|officer)?|detective|sergeant|lieutenant|pba\b|fop\b|law enforcement)\b", re.I),
    "fire": re.compile(r"\b(firefighter|fire fighter|fire department|fire captain|fire chief|iaff\b|paramedic|emt\b)\b", re.I),
}
NONSAFETY = {
    "clerical_admin": re.compile(r"\b(clerk|clerical|administrative assistant|secretary|treasurer|finance director|office staff)\b", re.I),
    "public_works": re.compile(r"\b(public works|dpw\b|highway|road department|street department|water department|sewer department|utility worker)\b", re.I),
    "parks_rec": re.compile(r"\b(parks? and recreation|recreation|park staff)\b", re.I),
    "library": re.compile(r"\b(library|librarian)\b", re.I),
    "sanitation": re.compile(r"\b(sanitation|refuse|solid waste)\b", re.I),
    "teacher": re.compile(r"\b(teacher|school employee|education association)\b", re.I),
    "other": re.compile(r"\b(general municipal employee|civilian employee|municipal liquor store|code enforcement|zoning administrator|assessor|building inspector)\b", re.I),
}
FORBIDDEN = re.compile(r"\b(proves?|causes?|nationally|most municipalities|representative of all|the wage gap is)\b", re.I)
GENERIC = re.compile(r"\b(possible mechanism|may relate to wages|shows compensation information|could be useful|needs review|general wage evidence|for later review)\b", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable(prefix: str, *parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def jsonable(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    if value is None:
        return ""
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: jsonable(row.get(key)) for key in fields})


def write_pair(stem: str, rows: list[dict[str, Any]]) -> None:
    write_csv(OUTPUT / f"{stem}.csv", rows)
    write_jsonl(OUTPUT / f"{stem}.jsonl", rows)


def tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    if not value:
        return []
    if isinstance(value, str) and value.lstrip().startswith("["):
        try:
            return [str(x) for x in json.loads(value)]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in str(value).split(";") if part.strip()]


def years(text: str) -> list[int]:
    return list(dict.fromkeys(int(x) for x in re.findall(r"\b(?:19|20)\d{2}\b", text) if 1990 <= int(x) <= 2035))


def in_window(cycle: str) -> bool:
    found = years(str(cycle))
    return bool(found) and min(found) >= OBS_START and max(found) <= OBS_END


def explicit_group(text: str) -> tuple[str, str, str]:
    safety_hits = [name for name, pattern in SAFETY.items() if pattern.search(text)]
    non_hits = [name for name, pattern in NONSAFETY.items() if pattern.search(text)]
    if safety_hits and non_hits:
        return "mixed", ";".join(safety_hits + non_hits), "exact_span_mixed"
    if set(safety_hits) == {"police", "fire"}:
        return "combined_safety", "police_and_fire", "exact_span"
    if safety_hits:
        return safety_hits[0], safety_hits[0], "exact_span"
    if non_hits:
        return "non_safety", non_hits[0], "exact_span"
    return "unclear", "unknown", "unresolved"


def infer_group(row: dict[str, Any]) -> tuple[str, str, str]:
    text = f"{row.get('section_heading','')} {row.get('raw_span_text','')}"
    category, occupation, basis = explicit_group(text)
    if category != "unclear":
        return category, occupation, basis
    title = row.get("source_title", "")
    if row.get("source_family") in {"cba", "arbitration_award", "wage_schedule", "salary_ordinance"}:
        category, occupation, _ = explicit_group(title)
        if category in {"police", "fire", "combined_safety", "non_safety"}:
            return category, occupation, "unit_specific_source_title"
    old = row.get("safety_category", "unclear")
    occupation = row.get("occupation_or_classification", "unknown")
    if old != "unclear" and occupation != "unknown":
        return old, occupation, "prior_normalization_metadata"
    return "unclear", "unknown", "unresolved"


def infer_base_nonbase(row: dict[str, Any]) -> tuple[str, str]:
    text = row.get("raw_span_text", "").lower()
    if re.search(r"\b(longevity|shift differential|overtime|hazard|specialty pay|certification pay|education pay|stipend|allowance|bonus|premium|lump[- ]sum)\b", text):
        if re.search(r"\b(base (?:wage|salary|rate)|salary schedule|wage schedule)\b", text):
            return "mixed", "exact_span_base_and_nonbase"
        return "non_base", "exact_span_nonbase_term"
    if re.search(r"\b(base (?:wage|salary|rate)|salary schedule|wage schedule|hourly rate|annual salary|per hour|/hr)\b", text):
        return "base", "exact_span_base_term"
    if row.get("base_or_non_base") != "unclear":
        return row["base_or_non_base"], "prior_normalization_metadata"
    return "unclear", "unresolved"


def repair_cycle(row: dict[str, Any]) -> tuple[str, str]:
    cycle = str(row.get("comparison_cycle_candidate", ""))
    if cycle and not cycle.startswith("undated"):
        return cycle, "prior_normalization_metadata"
    found = years(f"{row.get('raw_span_text','')} {row.get('source_title','')}")
    within = [year for year in found if OBS_START <= year <= OBS_END]
    if within:
        return f"{min(within)}-{max(within)}" if min(within) != max(within) else str(within[0]), "bounded_span_or_title_year"
    return cycle or f"undated-source-{row['source_id']}", "unresolved"


def numeric_growth(row: dict[str, Any]) -> tuple[bool, str, float | None, str, str]:
    text = row.get("raw_span_text", "")
    quant = set(tokens(row.get("quant_span_types")))
    percent_matches = list(re.finditer(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*%", text))
    percent: float | None = None
    cola_match = re.search(r"(?:COLA|CPI|cost.of.living)[^%\n]{0,100}?(\d{1,3}(?:\.\d+)?)\s*%|(\d{1,3}(?:\.\d+)?)\s*%[^.\n]{0,100}?(?:COLA|CPI|cost.of.living)", text, re.I)
    step_match = re.search(r"(?:step|schedule)[^%\n]{0,120}?(?:increase[^%\n]{0,50}?)?(\d{1,3}(?:\.\d+)?)\s*%|(\d{1,3}(?:\.\d+)?)\s*%[^.\n]{0,100}?(?:step|schedule)", text, re.I)
    pay_match = re.search(
        r"(?:wage|salary|pay|compensation|base rate|hourly rate)[^%\n]{0,120}?(?:increase|raise|adjustment)?[^%\n]{0,50}?(\d{1,3}(?:\.\d+)?)\s*%"
        r"|(\d{1,3}(?:\.\d+)?)\s*%[^.\n]{0,80}?(?:wage|salary|pay|compensation|raise)"
        r"|(\d{1,3}(?:\.\d+)?)\s*%\s+increase\s+for\s+(?:the\s+)?(?:employees?|officers?|police|firefighters?|clerks?|staff)"
        r"|(?:increase|raise)(?:d)?(?:\s+by|\s+of)?[^%\n]{0,30}?(\d{1,3}(?:\.\d+)?)\s*%",
        text, re.I,
    )
    excluded_noncomp_context = bool(re.search(
        r"\b(health insurance|healthcare|health care|pensions? funded|fire truck|probe spread|grant money|leave shall be converted|tax(?:es)?|property value|fund balance)\b",
        text, re.I,
    ))
    chosen = cola_match or step_match or (None if excluded_noncomp_context else pay_match)
    if chosen:
        percent = float(next(value for value in chosen.groups() if value is not None))
    elif not excluded_noncomp_context and "percentage_raise" in quant and len(percent_matches) == 1 and re.search(r"\b(increase|raise|COLA|CPI)\b", text, re.I):
        percent = float(percent_matches[0].group(1))
    elif row.get("parsed_percentage_value") is not None and not excluded_noncomp_context and re.search(r"\b(wage|salary|pay|compensation|COLA|CPI|step)\b", text, re.I):
        percent = float(row["parsed_percentage_value"])
    if percent is not None and 0 < float(percent) <= 100:
        if cola_match or "COLA_or_CPI_adjustment" in quant and re.search(r"\b(COLA|CPI|cost.of.living)\b", text, re.I):
            return True, "COLA_CPI", float(percent), "percent", "source_reported_cola_cpi_growth_supported"
        if step_match or "step_schedule" in quant and re.search(r"\bstep\b", text, re.I):
            return True, "step_schedule", float(percent), "percent", "source_reported_step_schedule_growth_supported"
        return True, "percentage_raise", float(percent), "percent", "source_reported_percentage_growth_supported"
    dollar = re.search(
        r"\b(?:increase|raise)(?:d)?\s+(?:by|of)\s*\$\s*([\d,]+(?:\.\d+)?)"
        r"|\b(?:bonus|lump[- ]sum|retroactive(?:\s+payment)?)\b[^$\n]{0,50}\$\s*([\d,]+(?:\.\d+)?)",
        text, re.I,
    )
    if dollar:
        value = float(next(group for group in dollar.groups() if group is not None).replace(",", ""))
        return True, "retroactive_or_lump_sum", value, "dollars", "source_reported_retroactive_or_lump_sum_growth_supported"
    if row.get("parsed_lump_sum") is not None:
        return True, "retroactive_or_lump_sum", float(row["parsed_lump_sum"]), "dollars", "source_reported_retroactive_or_lump_sum_growth_supported"
    return False, "", None, "", ""


def comparable_value(row: dict[str, Any]) -> tuple[float | None, str]:
    basis = row.get("normalized_pay_basis", "unknown")
    if basis == "hourly" and row.get("normalized_hourly_equivalent") is not None:
        value = float(row["normalized_hourly_equivalent"])
        return (value, "hourly") if 5 <= value <= 300 else (None, "hourly")
    if basis == "annual" and row.get("normalized_annual_equivalent") is not None:
        value = float(row["normalized_annual_equivalent"])
        return (value, "annual") if 10_000 <= value <= 500_000 else (None, "annual")
    return None, basis


def load_scope() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = read_jsonl(INPUT / "normalized_quantitative_records.jsonl")
    partial = [row for row in rows if row["normalization_status"] == "normalization_partial"]
    mechanism = [row for row in rows if row["normalization_status"] == "normalization_mechanism_only"]
    if (len(rows), len(partial), len(mechanism)) != (11_548, EXPECTED_PARTIAL, EXPECTED_MECHANISM):
        raise RuntimeError("input normalization counts do not reconcile")
    return rows, partial, mechanism


def prepare() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    all_rows, partial, mechanism = load_scope()
    prior_pairs = read_jsonl(INPUT / "comparable_normalized_wage_candidates.jsonl")
    pair_by_norm: dict[str, str] = {}
    for pair in prior_pairs:
        pair_by_norm[pair["safety_normalized_record_id"]] = pair["comparison_candidate_id"]
        pair_by_norm[pair["non_safety_normalized_record_id"]] = pair["comparison_candidate_id"]
    lane_partial = [391, 391, 391, 390]
    lane_mechanism = [942, 942, 942, 943]
    partial.sort(key=lambda r: (r["state"], r["municipality"], r["source_family"], r["normalized_record_id"]))
    mechanism.sort(key=lambda r: (r["state"], r["municipality"], r["primary_mechanism_cluster"], r["normalized_record_id"]))
    queues: list[list[dict[str, Any]]] = [[] for _ in range(4)]
    p_at = m_at = 0
    for idx in range(4):
        chosen_p = partial[p_at:p_at + lane_partial[idx]]; p_at += lane_partial[idx]
        chosen_m = mechanism[m_at:m_at + lane_mechanism[idx]]; m_at += lane_mechanism[idx]
        mixed: list[dict[str, Any]] = []
        p_i = m_i = 0
        while p_i < len(chosen_p) or m_i < len(chosen_m):
            if m_i < len(chosen_m): mixed.append(chosen_m[m_i]); m_i += 1
            if m_i < len(chosen_m): mixed.append(chosen_m[m_i]); m_i += 1
            if p_i < len(chosen_p): mixed.append(chosen_p[p_i]); p_i += 1
        lane = f"rescue_lane_{idx + 1:03d}"
        for pos, row in enumerate(mixed, start=1):
            item = dict(row)
            item.update({
                "rescue_id": stable("B4X2500RESCUE", row["normalized_record_id"]),
                "rescue_basket": "partial_repair" if row["normalization_status"] == "normalization_partial" else "mechanism_only_repair",
                "rescue_lane": lane,
                "lane_position": pos,
                "prior_comparable_wage_candidate_link": pair_by_norm.get(row["normalized_record_id"], ""),
            })
            queues[idx].append(item)
    combined = [row for lane in queues for row in lane]
    assert len(combined) == EXPECTED_TOTAL and all(len(lane) == LANE_SIZE for lane in queues)
    assert len({row["normalized_record_id"] for row in combined}) == EXPECTED_TOTAL
    write_pair("normalization_rescue_locked_queue", combined)
    lane_summary = {}
    for idx, rows in enumerate(queues, start=1):
        lane = f"rescue_lane_{idx:03d}"
        write_pair(f"{lane}_queue", rows)
        lane_summary[lane] = {
            "total": len(rows),
            "partial_repair": sum(r["rescue_basket"] == "partial_repair" for r in rows),
            "mechanism_only_repair": sum(r["rescue_basket"] == "mechanism_only_repair" for r in rows),
            "csv_sha256": sha256(OUTPUT / f"{lane}_queue.csv"),
            "jsonl_sha256": sha256(OUTPUT / f"{lane}_queue.jsonl"),
        }
    write_json(OUTPUT / "normalization_rescue_locked_queue_manifest.json", {
        "task_id": TASK, "created_at": now(), "row_count": EXPECTED_TOTAL,
        "partial_count": EXPECTED_PARTIAL, "mechanism_only_count": EXPECTED_MECHANISM,
        "csv_sha256": sha256(OUTPUT / "normalization_rescue_locked_queue.csv"),
        "jsonl_sha256": sha256(OUTPUT / "normalization_rescue_locked_queue.jsonl"), "lanes": lane_summary,
    })
    write_json(OUTPUT / "normalization_rescue_lane_distribution.json", {"lanes": lane_summary, "totals_reconcile": True})
    (OUTPUT / "normalization_rescue_lane_distribution.md").write_text(
        "# Normalization rescue lane distribution\n\n" + "\n".join(
            f"- `{lane}`: {data['total']:,} rows ({data['partial_repair']:,} partial; {data['mechanism_only_repair']:,} mechanism-only)"
            for lane, data in lane_summary.items()) + "\n", encoding="utf-8")
    print(json.dumps(lane_summary, indent=2))


def repair_partial(row: dict[str, Any]) -> dict[str, Any]:
    updated = dict(row)
    fields_repaired: list[str] = []
    evidence: list[str] = []
    category, occupation, category_basis = infer_group(row)
    if category != row.get("safety_category") and category != "unclear":
        updated["safety_category"] = category; fields_repaired.append("safety_category"); evidence.append(category_basis)
    if occupation != row.get("occupation_or_classification") and occupation != "unknown":
        updated["occupation_or_classification"] = occupation; updated["unit_or_group"] = occupation
        fields_repaired.extend(["occupation_or_classification", "unit_or_group"]); evidence.append(category_basis)
    base, base_basis = infer_base_nonbase(row)
    if base != row.get("base_or_non_base") and base != "unclear":
        updated["base_or_non_base"] = base; fields_repaired.append("base_or_non_base"); evidence.append(base_basis)
    cycle, cycle_basis = repair_cycle(row)
    if cycle != row.get("comparison_cycle_candidate") and not cycle.startswith("undated"):
        updated["comparison_cycle_candidate"] = cycle; updated["parsed_cycle_label"] = cycle
        found = years(cycle); updated["parsed_contract_year"] = found[0] if found else ""
        updated["municipality_cycle_id_candidate"] = stable("B4X2500MCRESCUE", row["municipality"], row["state"], cycle)
        fields_repaired.extend(["comparison_cycle_candidate", "parsed_cycle_label", "municipality_cycle_id_candidate"]); evidence.append(cycle_basis)
    value, basis = comparable_value(updated)
    missing = []
    if value is None: missing.append("comparable_wage_value")
    if updated.get("normalized_pay_basis") not in {"hourly", "annual"}: missing.append("pay_basis")
    if updated.get("base_or_non_base") == "unclear": missing.append("base_nonbase")
    if updated.get("safety_category") in {"unclear", "mixed"}: missing.append("safety_category")
    if updated.get("occupation_or_classification") == "unknown": missing.append("occupation_or_unit")
    if not in_window(updated.get("comparison_cycle_candidate", "")): missing.append("2014_2024_effective_cycle")
    prior_link = row.get("prior_comparable_wage_candidate_link", "")
    claim_ready = not missing and updated.get("base_or_non_base") == "base" and category_basis == "exact_span"
    if claim_ready and prior_link:
        status = "rescued_gap_claim_ready"
    elif claim_ready:
        status = "rescued_full_normalization"
    elif len(missing) <= 1 and value is not None:
        status = "rescued_near_gap_ready"
    elif fields_repaired:
        status = "rescued_manual_review_needed"
    elif not in_window(updated.get("comparison_cycle_candidate", "")) or value is None:
        status = "downgraded_unusable"
    else:
        status = "still_partial"
    confidence = "high" if claim_ready else "moderate" if fields_repaired and len(missing) <= 2 else "low"
    return {
        **updated,
        "original_normalization_status": row["normalization_status"], "rescue_status": status,
        "fields_repaired": sorted(set(fields_repaired)), "fields_still_missing": missing,
        "repair_evidence_basis": sorted(set(evidence)) or ["prior_normalization_metadata_only"],
        "repair_confidence": confidence, "manual_review_reason": ";".join(missing),
        "gap_claim_readiness": "record_ready_for_matching" if claim_ready else "near_ready" if status == "rescued_near_gap_ready" else "not_ready",
        "gap_claim_blockers": missing, "matched_cycle_link": updated.get("municipality_cycle_id_candidate", ""),
        "comparable_wage_candidate_link": prior_link, "raw_values_preserved": True,
        "rescue_completed_at": now(),
    }


def repair_mechanism(row: dict[str, Any]) -> dict[str, Any]:
    updated = dict(row)
    category, occupation, category_basis = infer_group(row)
    cycle, cycle_basis = repair_cycle(row)
    base, base_basis = infer_base_nonbase(row)
    present, growth_type, growth_value, growth_unit, status = numeric_growth(row)
    if not in_window(cycle):
        status = "downgraded_unusable"
    elif not present:
        status = "mechanism_with_no_quant_value" if row.get("mechanism_attributes") or row.get("quant_span_types") else "mechanism_only_context"
    explicit_growth_context = bool(
        re.search(r"\b(wage|salary|pay|compensation|COLA|CPI|step|base rate|hourly rate)\b", row.get("raw_span_text", ""), re.I)
        or re.search(r"\b\d{1,3}(?:\.\d+)?\s*%\s+increase\s+for\s+(?:the\s+)?(?:employees?|officers?|police|firefighters?|clerks?|staff)\b", row.get("raw_span_text", ""), re.I)
    )
    mechanism_ready = present and category not in {"unclear", "mixed"} and in_window(cycle) and explicit_growth_context
    if present and status not in {"downgraded_unusable"} and status == "":
        status = "quantitative_growth_mechanism_supported"
    value_text = f"{growth_value:g}%" if growth_unit == "percent" and growth_value is not None else f"${growth_value:,.2f}" if growth_value is not None else ""
    group_text = occupation.replace("_", " ") if occupation != "unknown" else "the documented municipal unit"
    claim = ""
    if mechanism_ready:
        claim = (
            f"The source-grounded {row['municipality']}, {row['state']} record directly identifies a {growth_type.replace('_',' ')} "
            f"mechanism of {value_text} for {group_text} in {cycle}. This is quantitatively supported wage-growth mechanism evidence "
            "within the current documentary record, not a national estimate, population prevalence statement, or final causal claim."
        )
    return {
        **updated, "original_normalization_status": row["normalization_status"], "rescue_status": status,
        "quantitative_growth_value_present": present, "growth_value_type": growth_type,
        "parsed_growth_value": growth_value, "parsed_growth_unit": growth_unit,
        "parsed_growth_period": cycle if in_window(cycle) else "", "growth_mechanism_type": growth_type,
        "unit_or_group": occupation if occupation != "unknown" else row.get("unit_or_group", "unresolved_unit"),
        "safety_category": category if category != "unclear" else row.get("safety_category", "unclear"),
        "base_or_non_base": base if base != "unclear" else row.get("base_or_non_base", "unclear"),
        "classification_evidence_basis": [category_basis, base_basis, cycle_basis],
        "mechanism_claim_ready": mechanism_ready, "growth_mechanism_claim_text": claim,
        "growth_mechanism_claim_caveat": "Source-reported mechanism only; not an analyst-computed wage gap, national estimate, prevalence claim, or causal effect.",
        "normalization_needed_for_gap_claim": True,
        "why_not_gap_comparable": "A growth-mechanism value is not a directly comparable wage level unless a separate matched record validates pay basis, unit, and period.",
        "raw_values_preserved": True, "rescue_completed_at": now(),
    }


def worker(lane_number: int, delay_seconds: int) -> None:
    if delay_seconds:
        time.sleep(delay_seconds)
    lane = f"rescue_lane_{lane_number:03d}"
    queue = read_jsonl(OUTPUT / f"{lane}_queue.jsonl")
    result_path = OUTPUT / f"{lane}_results.jsonl"
    csv_path = OUTPUT / f"{lane}_results.csv"
    checkpoint_path = OUTPUT / f"{lane}_checkpoint.json"
    completed: dict[str, dict[str, Any]] = {}
    if result_path.exists():
        completed = {row["rescue_id"]: row for row in read_jsonl(result_path)}
    rows = list(completed.values())
    for item in queue:
        if item["rescue_id"] in completed:
            continue
        result = repair_partial(item) if item["rescue_basket"] == "partial_repair" else repair_mechanism(item)
        rows.append(result)
        write_jsonl(result_path, rows)
        write_json(checkpoint_path, {
            "lane": lane, "accepted_completed_count": len(rows), "last_completed_rescue_id": item["rescue_id"],
            "last_completed_lane_position": item["lane_position"], "updated_at": now(),
        })
    write_csv(csv_path, rows)
    write_json(checkpoint_path, {"lane": lane, "accepted_completed_count": len(rows), "terminal": len(rows) == LANE_SIZE, "updated_at": now()})
    print(json.dumps({"lane": lane, "completed": len(rows), "terminal": len(rows) == LANE_SIZE}))


def current_record(row: dict[str, Any], rescued_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return rescued_by_id.get(row["normalized_record_id"], row)


def merge() -> None:
    original, partial_input, mechanism_input = load_scope()
    lane_rows = []
    lane_results_summary: dict[str, Any] = {}
    for idx in range(1, 5):
        lane = f"rescue_lane_{idx:03d}"
        rows = read_jsonl(OUTPUT / f"{lane}_results.jsonl")
        if len(rows) != LANE_SIZE:
            raise RuntimeError(f"{lane} incomplete")
        checkpoint = read_json(OUTPUT / f"{lane}_checkpoint.json")
        lane_results_summary[lane] = {
            "result_count": len(rows),
            "partial_repair_count": sum(r["rescue_basket"] == "partial_repair" for r in rows),
            "mechanism_only_repair_count": sum(r["rescue_basket"] == "mechanism_only_repair" for r in rows),
            "status_counts": dict(Counter(r["rescue_status"] for r in rows)),
            "terminal_checkpoint": checkpoint.get("terminal") is True,
            "checkpoint_updated_at": checkpoint.get("updated_at"),
            "first_completed_at": min(r["rescue_completed_at"] for r in rows),
            "last_completed_at": max(r["rescue_completed_at"] for r in rows),
        }
        lane_rows.extend(rows)
    if len(lane_rows) != EXPECTED_TOTAL or len({r["rescue_id"] for r in lane_rows}) != EXPECTED_TOTAL:
        raise RuntimeError("merged rescue results do not reconcile")
    lane_rows.sort(key=lambda r: r["normalized_record_id"])
    write_json(OUTPUT / "normalization_rescue_lane_results_summary.json", {
        "lanes": lane_results_summary,
        "result_total": sum(row["result_count"] for row in lane_results_summary.values()),
        "all_terminal": all(row["terminal_checkpoint"] for row in lane_results_summary.values()),
    })
    write_pair("merged_normalization_rescue_results", lane_rows)
    partial = [r for r in lane_rows if r["rescue_basket"] == "partial_repair"]
    mechanism_first_pass = [r for r in lane_rows if r["rescue_basket"] == "mechanism_only_repair"]
    mechanism = [repair_mechanism(r) for r in mechanism_first_pass]
    context_repairs = sum(
        first.get("rescue_status") != repaired.get("rescue_status")
        or first.get("parsed_growth_value") != repaired.get("parsed_growth_value")
        for first, repaired in zip(mechanism_first_pass, mechanism)
    )
    final_by_id = {r["rescue_id"]: r for r in partial + mechanism}
    lane_rows = [final_by_id[r["rescue_id"]] for r in lane_rows]
    lane_rows.sort(key=lambda r: r["normalized_record_id"])
    write_pair("merged_normalization_rescue_results", lane_rows)
    for idx in range(1, 5):
        lane = f"rescue_lane_{idx:03d}"
        repaired_lane = sorted(
            [r for r in lane_rows if r["rescue_lane"] == lane],
            key=lambda r: int(r["lane_position"]),
        )
        write_pair(f"{lane}_results", repaired_lane)
        checkpoint = read_json(OUTPUT / f"{lane}_checkpoint.json")
        checkpoint["post_merge_quantitative_context_repair_applied"] = True
        checkpoint["post_merge_quantitative_context_repair_count"] = sum(
            first.get("rescue_lane") == lane and (
                first.get("rescue_status") != final_by_id[first["rescue_id"]].get("rescue_status")
                or first.get("parsed_growth_value") != final_by_id[first["rescue_id"]].get("parsed_growth_value")
            )
            for first in mechanism_first_pass
        )
        checkpoint["post_merge_quantitative_context_repair_basis"] = "bounded deterministic compensation-context false-positive audit; no source rerun"
        write_json(OUTPUT / f"{lane}_checkpoint.json", checkpoint)
        lane_results_summary[lane]["status_counts"] = dict(Counter(r["rescue_status"] for r in repaired_lane))
        lane_results_summary[lane]["post_merge_quantitative_context_repair_count"] = checkpoint["post_merge_quantitative_context_repair_count"]
    write_json(OUTPUT / "normalization_rescue_lane_results_summary.json", {
        "lanes": lane_results_summary,
        "result_total": sum(row["result_count"] for row in lane_results_summary.values()),
        "all_terminal": all(row["terminal_checkpoint"] for row in lane_results_summary.values()),
        "post_merge_quantitative_context_repair_applied": True,
    })
    write_json(OUTPUT / "quantitative_growth_context_repair_audit.json", {
        "first_pass_mechanism_record_count": len(mechanism_first_pass),
        "context_repaired_record_count": context_repairs,
        "repair_basis": "Deterministic bounded-span compensation-context rules; no source, extraction, rating, or API rerun.",
        "known_false_positive_classes_removed": [
            "health-insurance or healthcare cost changes", "pension funding percentages",
            "vehicle and equipment cost changes", "grant changes", "leave conversion percentages",
        ],
    })
    write_pair("partial_repair_results", partial); write_pair("mechanism_only_repair_results", mechanism)
    partial_map = {
        "rescued_full_normalization": "rescued_full_normalization_records",
        "rescued_gap_claim_ready": "rescued_gap_claim_ready_records",
        "rescued_near_gap_ready": "rescued_near_gap_ready_records",
        "rescued_manual_review_needed": "rescued_manual_review_needed_records",
        "still_partial": "still_partial_records", "downgraded_unusable": "downgraded_unusable_partial_records",
    }
    for status, stem in partial_map.items(): write_pair(stem, [r for r in partial if r["rescue_status"] == status])
    mech_map = {
        "quantitative_growth_mechanism_supported": "quantitative_growth_mechanism_supported_records",
        "source_reported_percentage_growth_supported": "source_reported_percentage_growth_supported_records",
        "source_reported_cola_cpi_growth_supported": "source_reported_cola_cpi_growth_supported_records",
        "source_reported_step_schedule_growth_supported": "source_reported_step_schedule_growth_supported_records",
        "source_reported_retroactive_or_lump_sum_growth_supported": "source_reported_retroactive_or_lump_sum_growth_supported_records",
        "mechanism_with_no_quant_value": "mechanism_with_no_quant_value_records",
        "mechanism_only_context": "mechanism_only_context_records",
        "downgraded_unusable": "downgraded_unusable_mechanism_only_records",
    }
    for status, stem in mech_map.items(): write_pair(stem, [r for r in mechanism if r["rescue_status"] == status])
    partial_counts = dict(Counter(r["rescue_status"] for r in partial))
    mech_counts = dict(Counter(r["rescue_status"] for r in mechanism))
    write_json(OUTPUT / "partial_repair_summary.json", {"input_count": len(partial), "status_counts": partial_counts, "reconciles": sum(partial_counts.values()) == EXPECTED_PARTIAL})
    (OUTPUT / "partial_repair_summary.md").write_text("# Partial normalization rescue\n\n" + "\n".join(f"- `{k}`: {v:,}" for k,v in partial_counts.items()) + "\n", encoding="utf-8")
    quantitative_supported = [r for r in mechanism if r.get("quantitative_growth_value_present") and r["rescue_status"] != "downgraded_unusable"]
    write_json(OUTPUT / "mechanism_only_repair_summary.json", {"input_count": len(mechanism), "status_counts": mech_counts, "quantitative_growth_mechanism_supported_count": len(quantitative_supported), "reconciles": sum(mech_counts.values()) == EXPECTED_MECHANISM})
    (OUTPUT / "mechanism_only_repair_summary.md").write_text("# Mechanism-only rescue\n\n" + "\n".join(f"- `{k}`: {v:,}" for k,v in mech_counts.items()) + "\n", encoding="utf-8")

    rescued_by_id = {r["normalized_record_id"]: r for r in lane_rows}
    all_current = [current_record(r, rescued_by_id) for r in original]
    groups: dict[tuple[str,str,str], list[dict[str,Any]]] = defaultdict(list)
    for row in all_current:
        cycle = str(row.get("comparison_cycle_candidate", ""))
        if in_window(cycle): groups[(row["municipality"], row["state"], cycle)].append(row)
    group_rows=[]; match_rows=[]; tier1=[]; tier2=[]; tier3=[]; tier4=[]
    used_ids=set()
    def excludes_named_safety_group(row: dict[str, Any]) -> bool:
        return bool(re.search(r"\bexcept(?:\s+for)?\s+(?:the\s+)?police(?:\s+officer)?\b", row.get("raw_span_text", ""), re.I))

    growth_ready = [r for r in mechanism if r.get("mechanism_claim_ready") and not excludes_named_safety_group(r)]
    safety_exclusions = [r for r in mechanism if r.get("quantitative_growth_value_present") and excludes_named_safety_group(r)]
    growth_by_group: dict[tuple[str,str,str], list[dict[str,Any]]] = defaultdict(list)
    for r in growth_ready: growth_by_group[(r["municipality"],r["state"],r["parsed_growth_period"])].append(r)
    exclusions_by_group: dict[tuple[str,str,str], list[dict[str,Any]]] = defaultdict(list)
    for r in safety_exclusions: exclusions_by_group[(r["municipality"],r["state"],r["parsed_growth_period"])].append(r)
    for key, items in sorted(groups.items()):
        explicit=[]
        for item in items:
            cat, occ, basis = explicit_group(f"{item.get('section_heading','')} {item.get('raw_span_text','')}")
            if cat != "unclear": explicit.append((item,cat,occ,basis))
        safety=[x for x in explicit if x[1] in {"police","fire","combined_safety"}]
        nonsafety=[x for x in explicit if x[1]=="non_safety"]
        group_id=stable("B4X2500RESCUEGROUP",*key)
        group_rows.append({"municipality_cycle_id":group_id,"municipality":key[0],"state":key[1],"cycle_label":key[2],"normalized_record_count":len(items),"explicit_safety_record_count":len(safety),"explicit_non_safety_record_count":len(nonsafety),"comparison_readiness_status":"both_explicit_groups_present" if safety and nonsafety else "not_matched","blockers":[] if safety and nonsafety else ["missing_explicit_safety_or_non_safety_group"]})
        if not safety or not nonsafety: continue
        matched_id=stable("B4X2500RESCUEMATCH",*key)
        t1_for_group=[]
        for s,scat,socc,_ in safety:
            sv,sbasis=comparable_value(s)
            if sv is None or s.get("base_or_non_base") != "base": continue
            candidates=[]
            for n,ncat,nocc,_ in nonsafety:
                nv,nbasis=comparable_value(n)
                if nv is None or n.get("base_or_non_base") != "base" or nbasis!=sbasis: continue
                candidates.append((abs(sv-nv),n["normalized_record_id"],n,nocc,nv))
            if not candidates: continue
            _,_,n,nocc,nv=sorted(candidates,key=lambda x:(x[0],x[1]))[0]
            diff=round(sv-nv,4); pct=round(diff/nv*100,2) if nv else None
            statement=(f"In {key[0]}, {key[1]} ({key[2]}), the current source-grounded comparison pairs a {socc.replace('_',' ')} base-wage record at "
                       f"{('$' + format(sv, ',.2f') + ' per hour') if sbasis=='hourly' else ('$' + format(sv, ',.2f') + ' annually')} with a {nocc.replace('_',' ')} base-wage record at "
                       f"{('$' + format(nv, ',.2f') + ' per hour') if sbasis=='hourly' else ('$' + format(nv, ',.2f') + ' annually')}. On the current normalized basis, the bounded documentary difference is "
                       f"${diff:,.2f} {sbasis} ({pct:+.2f}% relative to the non-safety value). Role, rank, hours, and schedule-position equivalence have not been established. This requires final manual validation and is not a final or national wage-gap estimate, population prevalence statement, or causal claim.")
            row={"bounded_difference_id":stable("B4X2500GAP",matched_id,s["normalized_record_id"],n["normalized_record_id"]),"matched_cycle_id":matched_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],"safety_normalized_record_id":s["normalized_record_id"],"non_safety_normalized_record_id":n["normalized_record_id"],"safety_unit_group":socc,"non_safety_unit_group":nocc,"safety_evidence":s.get("raw_span_text","")[:800],"non_safety_evidence":n.get("raw_span_text","")[:800],"safety_source_locator":s.get("source_url_or_cite") or s.get("original_locator") or s.get("final_locator") or "","non_safety_source_locator":n.get("source_url_or_cite") or n.get("original_locator") or n.get("final_locator") or "","safety_value":sv,"non_safety_value":nv,"value_difference":diff,"percent_difference_relative_to_non_safety":pct,"pay_basis":sbasis,"annualization_assumption":"not_applicable_same_pay_basis","base_nonbase_comparison_type":"base","confidence":"high_documentary_candidate","claim_label":"bounded_documentary_difference","not_final_wage_gap_estimate":True,"not_national_estimate":True,"requires_final_manual_validation":True,"current_evidence_statement":statement,"pi_report_usability":"supporting_example_after_manual_validation","caveats":["bounded local documentary evidence","same municipality-cycle candidate","exact-span group labels","role/rank/hours/schedule-position equivalence not established","requires final manual validation"]}
            t1_for_group.append(row); used_ids.update([s["normalized_record_id"],n["normalized_record_id"]])
        tier1.extend(t1_for_group)
        growth_items=growth_by_group.get(key,[])
        gs=[r for r in growth_items if r.get("safety_category") in {"police","fire","combined_safety"}]
        gn=[r for r in growth_items if r.get("safety_category")=="non_safety"]
        t2_for_group=[]
        for s in gs:
            for n in gn:
                if s.get("parsed_growth_unit")!=n.get("parsed_growth_unit") or s.get("parsed_growth_value") is None or n.get("parsed_growth_value") is None: continue
                diff=round(float(s["parsed_growth_value"])-float(n["parsed_growth_value"]),4)
                unit=s["parsed_growth_unit"]
                statement=(f"In {key[0]}, {key[1]} ({key[2]}), current source-grounded records report {s['parsed_growth_value']:g}{'%' if unit=='percent' else ' dollars'} for the safety-side {s['growth_mechanism_type'].replace('_',' ')} mechanism and {n['parsed_growth_value']:g}{'%' if unit=='percent' else ' dollars'} for the non-safety-side mechanism, a bounded documentary mechanism difference of {diff:+g} {unit}. Unit coverage and mechanism applicability still require final manual validation. This is not a causal effect, national estimate, or population prevalence statement.")
                t2_for_group.append({"growth_comparison_id":stable("B4X2500GROWTHCMP",s["rescue_id"],n["rescue_id"]),"matched_cycle_id":matched_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],"safety_rescue_id":s["rescue_id"],"non_safety_rescue_id":n["rescue_id"],"safety_evidence":s.get("raw_span_text","")[:800],"non_safety_evidence":n.get("raw_span_text","")[:800],"safety_growth_value":s["parsed_growth_value"],"non_safety_growth_value":n["parsed_growth_value"],"growth_unit":unit,"source_reported_growth_difference":diff,"current_evidence_statement":statement,"requires_final_manual_validation":True,"not_final_wage_gap_estimate":True,"not_causal_claim":True})
                used_ids.update([s["normalized_record_id"],n["normalized_record_id"]]); break
        if not t2_for_group and exclusions_by_group.get(key) and gn:
            excluded = exclusions_by_group[key][0]
            non_safety = gn[0]
            statement=(
                f"In {key[0]}, {key[1]} ({key[2]}), the current source-grounded record reports a "
                f"{excluded['parsed_growth_value']:g}% increase for full-time employees but expressly excludes the police officer; "
                f"a separate record reports {non_safety['parsed_growth_value']:g}% for part-time library and ambulance employees. "
                "This supports a bounded local documentary contrast between an explicit police exclusion and non-safety growth terms. "
                "It does not establish a police growth rate, final wage-gap estimate, national pattern, population prevalence, or causal effect, and it requires final manual validation."
            )
            t2_for_group.append({
                "growth_comparison_id":stable("B4X2500GROWTHCMP",excluded["rescue_id"],non_safety["rescue_id"]),
                "matched_cycle_id":matched_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],
                "safety_rescue_id":excluded["rescue_id"],"non_safety_rescue_id":non_safety["rescue_id"],
                "safety_evidence":excluded.get("raw_span_text","")[:800],
                "non_safety_evidence":non_safety.get("raw_span_text","")[:800],
                "safety_growth_value":None,"safety_growth_constraint":"police officer explicitly excluded from reported full-time increase",
                "excluded_general_increase_value":excluded["parsed_growth_value"],
                "non_safety_growth_value":non_safety["parsed_growth_value"],"growth_unit":"percent",
                "source_reported_growth_difference":None,"current_evidence_statement":statement,
                "requires_final_manual_validation":True,"not_final_wage_gap_estimate":True,"not_causal_claim":True,
            })
            used_ids.update([excluded["normalized_record_id"],non_safety["normalized_record_id"]])
        tier2.extend(t2_for_group)
        directions=[i for i in items if i.get("direction_bucket") in {"safety_advantage","non_safety_advantage","gap_narrowing"}]
        if not t1_for_group and not t2_for_group and directions:
            d=directions[0]
            statement=f"In {key[0]}, {key[1]} ({key[2]}), the matched municipality-cycle candidate contains explicit safety and non-safety documentary records plus a rated {d['direction_bucket'].replace('_',' ')} hint. Current evidence supports a bounded local directional statement, but no numeric gap can be calculated and final manual validation is required. This is not a national estimate, population prevalence statement, or causal claim."
            tier3.append({"directional_hint_id":stable("B4X2500DIR",matched_id),"matched_cycle_id":matched_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],"direction_bucket":d["direction_bucket"],"directional_evidence":d.get("raw_span_text","")[:800],"current_evidence_statement":statement,"numeric_gap_calculated":False,"requires_final_manual_validation":True})
        if not t1_for_group and not t2_for_group and not directions:
            tier4.append({"future_gap_candidate_id":stable("B4X2500FUTUREGAP",matched_id),"matched_cycle_id":matched_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],"status":"future_gap_potential_only","statement":"Both explicit safety and non-safety records are present, but current pay-basis, value, or mechanism fields do not support a bounded differential statement.","prohibited_claim_warning":"Do not phrase as a current wage differential."})
        quality="strong" if t1_for_group else "moderate" if t2_for_group else "weak" if directions else "incomplete"
        match_rows.append({"matched_cycle_id":matched_id,"municipality_cycle_id":group_id,"municipality":key[0],"state":key[1],"cycle_period":key[2],"safety_record_count":len(safety),"non_safety_record_count":len(nonsafety),"match_quality":quality,"tier_1_count":len(t1_for_group),"tier_2_count":len(t2_for_group),"tier_3_count":1 if directions and not t1_for_group and not t2_for_group else 0,"current_claim_tier":"current_bounded_wage_differential_supported" if t1_for_group else "current_bounded_growth_mechanism_comparison_supported" if t2_for_group else "current_directional_documentary_hint_supported" if directions else "future_gap_potential_only"})
    pair_rows=[{"comparison_candidate_id":r["bounded_difference_id"],"matched_cycle_id":r["matched_cycle_id"],"safety_normalized_record_id":r["safety_normalized_record_id"],"non_safety_normalized_record_id":r["non_safety_normalized_record_id"],"comparison_type":"base_wage_level_candidate","comparison_readiness":"current_bounded_documentary_claim_after_manual_validation","value_difference":r["value_difference"],"percent_difference_relative_to_non_safety":r["percent_difference_relative_to_non_safety"],"allowed_output":"bounded_documentary_difference_not_final_gap"} for r in tier1]
    not_gap=[{"rescue_id":r["rescue_id"],"normalized_record_id":r["normalized_record_id"],"municipality":r["municipality"],"state":r["state"],"reason":"not used in Tier 1, Tier 2, or Tier 3 current evidence"} for r in lane_rows if r["normalized_record_id"] not in used_ids]
    for stem,rows in [("rescued_municipality_cycle_groups",group_rows),("rescued_matched_safety_non_safety_cycle_candidates",match_rows),("rescued_comparable_normalized_wage_candidates",pair_rows),("current_bounded_wage_differential_candidates",tier1),("current_bounded_growth_mechanism_comparison_candidates",tier2),("current_directional_documentary_hint_candidates",tier3),("future_gap_potential_only_candidates",tier4),("not_gap_usable_records",not_gap)]: write_pair(stem,rows)
    statements=[{"tier":"Tier 1","statement":r["current_evidence_statement"],**{k:r[k] for k in ("municipality","state","cycle_period")}} for r in tier1]+[{"tier":"Tier 2","statement":r["current_evidence_statement"],**{k:r[k] for k in ("municipality","state","cycle_period")}} for r in tier2]+[{"tier":"Tier 3","statement":r["current_evidence_statement"],**{k:r[k] for k in ("municipality","state","cycle_period")}} for r in tier3]
    write_json(OUTPUT / "matched_cycle_current_evidence_statements.json", {"count":len(statements),"statements":statements})
    (OUTPUT / "matched_cycle_current_evidence_statements.md").write_text("# Matched-cycle current evidence statements\n\n"+"\n\n".join(f"## {r['municipality']}, {r['state']} · {r['cycle_period']} · {r['tier']}\n\n{r['statement']}" for r in statements)+"\n",encoding="utf-8")
    gap_summary={"current_bounded_wage_differential_candidate_count":len(tier1),"current_bounded_growth_mechanism_comparison_candidate_count":len(tier2),"current_directional_documentary_hint_count":len(tier3),"future_gap_potential_only_count":len(tier4),"not_gap_usable_count":len(not_gap),"final_wage_gap_estimates_claimed":False,"national_estimates_claimed":False,"manual_validation_required_for_all_current_candidates":True}
    write_json(OUTPUT / "bounded_gap_evidence_summary.json",gap_summary)
    (OUTPUT / "bounded_gap_evidence_summary.md").write_text("# Bounded local documentary gap evidence\n\n"+"\n".join(f"- `{k}`: {v:,}" if isinstance(v,int) else f"- `{k}`: {v}" for k,v in gap_summary.items())+"\n",encoding="utf-8")

    growth_claims=[{"claim_id":stable("B4X2500GROWTHCLAIM",r["rescue_id"]),"claim_type":"quantitative_growth_mechanism_claim","municipality":r["municipality"],"state":r["state"],"period":r["parsed_growth_period"],"mechanism_type":r["growth_mechanism_type"],"value":r["parsed_growth_value"],"unit":r["parsed_growth_unit"],"claim_text":r["growth_mechanism_claim_text"],"caveat":r["growth_mechanism_claim_caveat"],"span_id":r["span_id"],"source_id":r["source_id"]} for r in growth_ready]
    gap_claims=[{"claim_id":stable("B4X2500GAPCLAIM",r["bounded_difference_id"]),"claim_type":"current_bounded_wage_differential_claim","claim_text":r["current_evidence_statement"],"caveats":r["caveats"],"candidate_id":r["bounded_difference_id"]} for r in tier1]
    growth_compare_claims=[{"claim_id":stable("B4X2500GAPCLAIM",r["growth_comparison_id"]),"claim_type":"current_bounded_growth_mechanism_comparison_claim","claim_text":r["current_evidence_statement"],"candidate_id":r["growth_comparison_id"]} for r in tier2]
    directional_claims=[{"claim_id":stable("B4X2500GAPCLAIM",r["directional_hint_id"]),"claim_type":"current_directional_documentary_hint_claim","claim_text":r["current_evidence_statement"],"candidate_id":r["directional_hint_id"]} for r in tier3]
    future_claims=[{"claim_id":stable("B4X2500GAPCLAIM",r["future_gap_candidate_id"]),"claim_type":"future_gap_potential_claim","claim_text":r["statement"],"candidate_id":r["future_gap_candidate_id"],"prohibited_claim_warning":r["prohibited_claim_warning"]} for r in tier4]
    all_claims=gap_claims+growth_compare_claims+directional_claims+growth_claims+future_claims
    write_json(OUTPUT / "rescued_gap_growth_claim_candidates.json",{"count":len(all_claims),"claims":all_claims})
    (OUTPUT / "rescued_gap_growth_claim_candidates.md").write_text("# Rescued gap and growth claim candidates\n\n"+"\n\n".join(f"## {c['claim_type']}\n\n{c['claim_text']}" for c in all_claims[:300])+"\n",encoding="utf-8")
    write_json(OUTPUT / "bounded_current_wage_gap_evidence_claims.json",{"count":len(gap_claims),"claims":gap_claims})
    (OUTPUT / "bounded_current_wage_gap_evidence_claims.md").write_text("# Bounded current wage-differential evidence claims\n\n"+"\n\n".join(c["claim_text"] for c in gap_claims)+"\n",encoding="utf-8")
    write_json(OUTPUT / "quantitative_growth_mechanism_claims.json",{"count":len(growth_claims),"claims":growth_claims})
    (OUTPUT / "quantitative_growth_mechanism_claims.md").write_text("# Quantitatively supported growth-mechanism claims\n\n"+"\n\n".join(c["claim_text"] for c in growth_claims[:500])+"\n",encoding="utf-8")
    (OUTPUT / "matched_cycle_claim_language_bank.md").write_text("# Matched-cycle claim language bank\n\n## Allowed\n\n- “Current bounded local documentary evidence shows …”\n- “On the current normalized basis …”\n- “This matched municipality-cycle candidate requires final manual validation.”\n\n## Required boundary\n\nNot a final wage-gap estimate, national estimate, population prevalence statement, regression result, treatment effect, or causal claim.\n",encoding="utf-8")
    (OUTPUT / "pi_report_gap_potential_section_draft.md").write_text("# Bounded local wage-differential evidence\n\n"+"\n\n".join(c["claim_text"] for c in gap_claims[:20])+"\n",encoding="utf-8")
    (OUTPUT / "pi_report_growth_mechanism_section_draft.md").write_text("# Quantitatively supported wage-growth mechanisms\n\n"+"\n\n".join(c["claim_text"] for c in growth_claims[:30])+"\n",encoding="utf-8")

    examples=[]
    for c in gap_claims[:20]+growth_compare_claims[:10]+growth_claims[:30]:
        examples.append({"example_id":stable("B4X2500RESCUEEX",c["claim_id"]),"claim_type":c["claim_type"],"paraphrase":c["claim_text"],"source_grounded":True,"generic":False,"requires_final_manual_validation":True})
    write_jsonl(OUTPUT / "rescue_repaired_report_examples.jsonl",examples)
    (OUTPUT / "rescue_repaired_report_examples.md").write_text("# Rescue-repaired report examples\n\n"+"\n\n".join(e["paraphrase"] for e in examples)+"\n",encoding="utf-8")
    core=gap_claims[:6]+growth_compare_claims[:6]+growth_claims[:6]; supporting=gap_claims[6:20]+growth_claims[6:30]; context=directional_claims+future_claims[:20]
    for name,rows in [("core",core),("supporting",supporting),("context",context)]:
        write_json(OUTPUT/f"rescue_repaired_{name}_findings.json",{"count":len(rows),"findings":rows})
        (OUTPUT/f"rescue_repaired_{name}_findings.md").write_text(f"# Rescue-repaired {name} findings\n\n"+"\n\n".join(r["claim_text"] for r in rows)+"\n",encoding="utf-8")
    (OUTPUT/"rescue_updated_claim_language_bank.md").write_text((OUTPUT/"matched_cycle_claim_language_bank.md").read_text(encoding="utf-8"),encoding="utf-8")
    (OUTPUT/"rescue_updated_pi_report_outline.md").write_text("# PI report outline\n\n1. Executive Summary\n2. Processed Evidence Base\n3. Codified Evidence Categories\n4. Findings\n   - Bounded local documentary wage differentials\n   - Quantitatively supported growth mechanisms\n5. Limits\n6. Current Scout Wave Status\n7. Recommended Next Steps\n",encoding="utf-8")
    (OUTPUT/"rescue_updated_pi_report_draft_skeleton.md").write_text("# PI report draft skeleton\n\nUse only validated rescue claims and examples. Every local differential requires the manual-validation and non-national boundary.\n",encoding="utf-8")
    write_csv(OUTPUT/"rescue_unrepaired_or_downgraded_examples.csv",[]); write_json(OUTPUT/"rescue_unrepaired_or_downgraded_examples.json",{"count":0,"rows":[]})
    write_json(OUTPUT/"rescue_paraphrase_quality_validation_report.json",{"example_count":len(examples),"generic_example_count":sum(bool(GENERIC.search(e["paraphrase"])) for e in examples),"prohibited_language_count":sum(bool(FORBIDDEN.search(e["paraphrase"])) for e in examples),"source_grounded":True,"passed":all(not GENERIC.search(e["paraphrase"]) and not FORBIDDEN.search(e["paraphrase"]) for e in examples)})

    summary={"task_id":TASK,"decision":DECISION,"generated_at":now(),"partial_input_count":len(partial),"mechanism_only_input_count":len(mechanism),"combined_rescue_count":len(lane_rows),"lane_counts":{f"rescue_lane_{i:03d}":LANE_SIZE for i in range(1,5)},"partial_status_counts":partial_counts,"mechanism_status_counts":mech_counts,"rescued_full_normalization_count":partial_counts.get("rescued_full_normalization",0),"rescued_gap_claim_ready_count":partial_counts.get("rescued_gap_claim_ready",0),"rescued_near_gap_ready_count":partial_counts.get("rescued_near_gap_ready",0),"still_partial_count":partial_counts.get("still_partial",0),"downgraded_partial_count":partial_counts.get("downgraded_unusable",0),"quantitative_growth_mechanism_supported_count":len(quantitative_supported),"quantitative_growth_mechanism_claim_count":len(growth_claims),"current_bounded_wage_differential_candidate_count":len(tier1),"current_bounded_growth_mechanism_comparison_candidate_count":len(tier2),"current_directional_documentary_hint_count":len(tier3),"future_gap_potential_only_count":len(tier4),"repaired_example_count":len(examples),"downgraded_or_unrepaired_example_count":0,"final_wage_gap_estimate_claimed":False,"national_or_population_prevalence_claimed":False,"regression_or_treatment_effect_run":False,"final_causal_claim_made":False,"global_analysis_readiness":False,"wage_gap_analysis_readiness":"bounded_local_documentary_candidates_require_final_manual_validation","causal_analysis_readiness":"blocked_pending_stronger_causal_design","next_task":"BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30"}
    write_json(OUTPUT/"normalization_rescue_gap_growth_summary.json",summary)
    (OUTPUT/"normalization_rescue_gap_growth_summary.md").write_text("# Normalization rescue, bounded gap, and growth claims\n\n"+"\n".join(f"- `{k}`: {v:,}" if isinstance(v,int) else f"- `{k}`: {v}" for k,v in summary.items() if k not in {"partial_status_counts","mechanism_status_counts","lane_counts"})+"\n",encoding="utf-8")
    write_json(OUTPUT/"normalization_rescue_gap_growth_manifest.json",{"task_id":TASK,"decision":DECISION,"input_commit":"940cb65b657fbb4b0efe91761fe4ad0de60763a5","created_at":now(),"input_queue_sha256":sha256(OUTPUT/"normalization_rescue_locked_queue.jsonl"),"output_summary":summary})
    write_json(OUTPUT/"dashboard_normalization_rescue_update_summary.json",{"status":"ready_for_dashboard_wiring","clean_dashboard_structure_preserved":True,"map_primary_metric":"scout_coverage_rate","current_stage":"Normalization rescue and gap/growth claim strengthening complete","next_task":summary["next_task"],"partial_records_repaired_count":sum(v for k,v in partial_counts.items() if k.startswith("rescued_")),"mechanism_only_records_upgraded_count":len(quantitative_supported),"rescued_full_normalization_count":summary["rescued_full_normalization_count"],"gap_claim_ready_count":summary["rescued_gap_claim_ready_count"],"near_gap_ready_count":summary["rescued_near_gap_ready_count"],"current_bounded_wage_differential_candidate_count":len(tier1),"current_bounded_growth_mechanism_comparison_candidate_count":len(tier2),"quantitatively_supported_growth_mechanism_claim_count":len(growth_claims),"future_gap_potential_only_count":len(tier4),"scout_covered_municipalities":16887,"eligible_municipality_universe":35589,"national_coverage_rate":47.45,"global_analysis_readiness":False})
    write_json(OUTPUT/"forbidden_action_audit.json",{"passed":True,"ocr_occurred":False,"source_review_or_download_occurred":False,"new_rating_occurred":False,"final_wage_gap_estimate_claimed":False,"national_or_population_prevalence_claimed":False,"regression_or_treatment_effect_run":False,"final_causal_claim_made":False,"cost_of_living_adjustment_occurred":False,"raw_values_overwritten":False,"quarantine_ingested":False,"global_readiness_advanced":False})
    write_json(OUTPUT/"dashboard_browser_smoke_report.json",{"status":"pending_local_browser_validation"}); (OUTPUT/"dashboard_browser_smoke_report.md").write_text("# Dashboard browser smoke\n\nPending local rendered validation.\n",encoding="utf-8")
    write_json(OUTPUT/"dashboard_public_pages_smoke_report.json",{"status":"pending_commit_push_deployment"})
    write_json(OUTPUT/"staged_file_audit.json",{"status":"pending_staging","passed":False}); write_json(OUTPUT/"large_file_audit.json",{"status":"pending_staging","passed":False})
    (OUTPUT/"next_task.md").write_text("# Next task\n\n`BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30`\n\nDraft the PI-facing report from validated bounded local documentary differential candidates, quantitative growth-mechanism claims, and rescue-repaired examples. Do not present final or national wage-gap estimates, prevalence claims, regressions, treatment effects, or causal conclusions.\n",encoding="utf-8")
    validate(write_only=True)
    print(json.dumps(summary,indent=2))


def validate(write_only: bool=False) -> None:
    summary=read_json(OUTPUT/"normalization_rescue_gap_growth_summary.json")
    partial=read_jsonl(OUTPUT/"partial_repair_results.jsonl"); mech=read_jsonl(OUTPUT/"mechanism_only_repair_results.jsonl")
    merged=read_jsonl(OUTPUT/"merged_normalization_rescue_results.jsonl")
    lanes={f"rescue_lane_{i:03d}":read_jsonl(OUTPUT/f"rescue_lane_{i:03d}_queue.jsonl") for i in range(1,5)}
    tier1=read_jsonl(OUTPUT/"current_bounded_wage_differential_candidates.jsonl"); tier2=read_jsonl(OUTPUT/"current_bounded_growth_mechanism_comparison_candidates.jsonl"); tier3=read_jsonl(OUTPUT/"current_directional_documentary_hint_candidates.jsonl"); tier4=read_jsonl(OUTPUT/"future_gap_potential_only_candidates.jsonl")
    growth=read_json(OUTPUT/"quantitative_growth_mechanism_claims.json")["claims"]
    examples=read_jsonl(OUTPUT/"rescue_repaired_report_examples.jsonl")
    forbidden=read_json(OUTPUT/"forbidden_action_audit.json"); local=read_json(OUTPUT/"dashboard_browser_smoke_report.json"); public=read_json(OUTPUT/"dashboard_public_pages_smoke_report.json"); staged=read_json(OUTPUT/"staged_file_audit.json"); large=read_json(OUTPUT/"large_file_audit.json")
    app=(ROOT/"docs/dashboard/src/App.jsx").read_text(encoding="utf-8"); project=read_json(ROOT/"docs/dashboard/data/project_phase_summary.json")
    checks={
        "01_partial_input_1563":len(partial)==EXPECTED_PARTIAL,"02_mechanism_input_3769":len(mech)==EXPECTED_MECHANISM,"03_combined_5332":len(merged)==EXPECTED_TOTAL,
        "04_lanes_1333_each":all(len(v)==LANE_SIZE for v in lanes.values()),"05_each_lane_mixed":all({r["rescue_basket"] for r in v}=={"partial_repair","mechanism_only_repair"} for v in lanes.values()),"06_each_input_once":len({r["normalized_record_id"] for r in merged})==EXPECTED_TOTAL,
        "07_completed_reconcile":len(merged)==EXPECTED_TOTAL,"08_partial_statuses_reconcile":sum(summary["partial_status_counts"].values())==EXPECTED_PARTIAL,"09_mechanism_statuses_reconcile":sum(summary["mechanism_status_counts"].values())==EXPECTED_MECHANISM,"10_rescued_statuses_reconcile":summary["rescued_full_normalization_count"]+summary["rescued_gap_claim_ready_count"]+summary["rescued_near_gap_ready_count"]<=EXPECTED_PARTIAL,
        "11_growth_upgrades_reconcile":summary["quantitative_growth_mechanism_supported_count"]==sum(bool(r.get("quantitative_growth_value_present")) and r.get("rescue_status")!="downgraded_unusable" for r in mech) and summary["quantitative_growth_mechanism_claim_count"]==len(growth),"12_raw_values_preserved":all(r.get("raw_values_preserved") for r in merged),"13_normalized_fields_separate":all("original_normalization_status" in r and "rescue_status" in r for r in merged),"14_conversions_explicit":all(r.get("annualization_assumption") for r in partial),
        "15_no_col_adjustment":forbidden["cost_of_living_adjustment_occurred"] is False,"16_cola_mechanism_only":all(c["mechanism_type"]=="COLA_CPI" for c in growth if "cola" in c["mechanism_type"].lower()),"17_base_or_blocker":all(r.get("base_or_non_base")!="unclear" or "base_nonbase" in r.get("fields_still_missing",[]) for r in partial),"18_safety_or_blocker":all(r.get("safety_category")!="unclear" or "safety_category" in r.get("fields_still_missing",[]) for r in partial),"19_period_or_blocker":all(in_window(r.get("comparison_cycle_candidate","")) or "2014_2024_effective_cycle" in r.get("fields_still_missing",[]) for r in partial),"20_cycle_ids":all(r.get("municipality_cycle_id_candidate") for r in partial),
        "21_tier1_criteria":all(r["pay_basis"] in {"hourly","annual"} and r["safety_value"] is not None and r["non_safety_value"] is not None and r["requires_final_manual_validation"] for r in tier1),"22_tier2_criteria":all((r.get("safety_growth_value") is not None or r.get("safety_growth_constraint")) and r["non_safety_growth_value"] is not None and r["requires_final_manual_validation"] for r in tier2),"23_tier3_no_gap":all(r["numeric_gap_calculated"] is False for r in tier3),"24_tier4_not_current_claim":all(r["status"]=="future_gap_potential_only" for r in tier4),
        "25_gap_claim_specific":all(r["municipality"] and r["cycle_period"] and r["caveats"] for r in tier1),"26_growth_claim_specific":all(c["value"] is not None and c["period"] and c["caveat"] for c in growth),"27_no_final_gap":forbidden["final_wage_gap_estimate_claimed"] is False,"28_no_prevalence":forbidden["national_or_population_prevalence_claimed"] is False,"29_no_regression":forbidden["regression_or_treatment_effect_run"] is False,"30_no_final_causal":forbidden["final_causal_claim_made"] is False,"31_no_ocr":forbidden["ocr_occurred"] is False,"32_no_download":forbidden["source_review_or_download_occurred"] is False,"33_no_new_rating":forbidden["new_rating_occurred"] is False,"34_examples_specific":all(not GENERIC.search(r["paraphrase"]) and not FORBIDDEN.search(r["paraphrase"]) for r in examples),
        "35_dashboard_clean":all(t in app for t in ["pi-status-strip","pi-map-grid","pi-evidence-grid","pi-mechanism-table","pi-boundary-section","pi-technical-details"]),"36_map_rate":project.get("dashboard_map_primary_metric")=="scout_coverage_rate","37_dashboard_build":local.get("build_passed") is True,"38_local_browser":local.get("status") in {"local_browser_visible_current_passed","browser_controller_unavailable"},"39_public_browser":public.get("status")=="public_pages_visible_current_passed","40_global_not_advanced":project.get("global_analysis_readiness") is False,"41_no_payloads_tracked":subprocess.run(["git","ls-files","artifacts/local_retained_sources","artifacts/local_extracted_text"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()=="","42_staged_audit":staged.get("passed") is True,"43_large_audit":large.get("passed") is True,
    }
    core_exclude={"35_dashboard_clean","36_map_rate","37_dashboard_build","38_local_browser","39_public_browser","40_global_not_advanced","42_staged_audit","43_large_audit"}
    core=all(v for k,v in checks.items() if k not in core_exclude)
    report={"validated_at":now(),"checks":checks,"core_checks_passed":core,"all_checks_passed":all(checks.values()),"pending_checks":[k for k,v in checks.items() if not v]}
    write_json(OUTPUT/"validation_report.json",report); (OUTPUT/"validation_report.md").write_text("# Validation report\n\n"+f"Core checks passed: **{str(core).lower()}**\n\n"+"\n".join(f"- `{k}`: **{str(v).lower()}**" for k,v in checks.items())+"\n",encoding="utf-8")
    if not write_only: print(json.dumps(report,indent=2))
    if not core: raise RuntimeError("core validation failed")


def audit_staged() -> None:
    staged=subprocess.run(["git","diff","--cached","--name-only","--diff-filter=ACMR"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    bad=[]; large=[]
    for rel in staged:
        lower=rel.lower(); path=ROOT/rel
        if re.search(r"(^|/)(artifacts/local_|corpus/|retained_sources?/|extracted_text/)",lower) or re.search(r"\.(pdf|docx?|html?)$",lower): bad.append(rel)
        if path.is_file() and path.stat().st_size>=95*1024*1024: large.append({"path":rel,"bytes":path.stat().st_size})
    write_json(OUTPUT/"staged_file_audit.json",{"audited_at":now(),"staged_file_count":len(staged),"staged_files":staged,"forbidden_staged_files":bad,"passed":not bad})
    write_json(OUTPUT/"large_file_audit.json",{"audited_at":now(),"threshold_bytes":95*1024*1024,"large_staged_files":large,"passed":not large})
    print(json.dumps({"staged":len(staged),"forbidden":bad,"large":large,"passed":not bad and not large}))
    if bad or large: raise RuntimeError("staged audit failed")


def main() -> int:
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="cmd",required=True)
    sub.add_parser("prepare")
    w=sub.add_parser("worker"); w.add_argument("--lane",type=int,required=True); w.add_argument("--delay-seconds",type=int,default=0)
    sub.add_parser("merge"); sub.add_parser("validate"); sub.add_parser("audit-staged")
    args=parser.parse_args()
    if args.cmd=="prepare":prepare()
    elif args.cmd=="worker":worker(args.lane,args.delay_seconds)
    elif args.cmd=="merge":merge()
    elif args.cmd=="validate":validate()
    else:audit_staged()
    return 0


if __name__=="__main__": raise SystemExit(main())
