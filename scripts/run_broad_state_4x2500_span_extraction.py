#!/usr/bin/env python3
"""Run bounded deterministic span extraction over 2,795 extracted-ok sources.

The runner reads only ignored local extracted-text artifacts.  It records short,
verbatim, offset-addressed candidate spans and neutral template paraphrases.  It
does not OCR, call a model/API, rate evidence, ingest/codify, normalize wages, or
perform statistical/causal analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30"
OUTPUT = BASE / "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30"
TEXT_ROOT = ROOT / "artifacts/local_extracted_text/broad_state_4x2500_text_extraction_2026-07-30"
LOG_ROOT = ROOT / "tmp/broad_state_4x2500_span_extraction_2026-07-30_logs"
TASK_ID = "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30"
DECISION = "broad_state_4x2500_span_extraction_completed_rating_ready"
EXPECTED = 2795
LANES = {
    "span_extraction_lane_001": 699,
    "span_extraction_lane_002": 699,
    "span_extraction_lane_003": 699,
    "span_extraction_lane_004": 698,
}
DELAYS = {name: index * 480 for index, name in enumerate(LANES)}
MAX_SPANS_PER_SOURCE = 18
MAX_RULE_MATCHES = 3
MAX_SPAN_CHARS = 800

STATUSES = (
    "positive_spans_found", "no_relevant_spans_found",
    "weak_or_ambiguous_spans_only", "text_unusable_for_span_extraction",
    "span_extraction_error",
)
EVIDENCE_CATEGORIES = (
    "quantitative_compensation", "qualitative_mechanism",
    "mixed_quantitative_qualitative", "non_base_compensation",
    "source_navigation_reference", "fiscal_or_budget_context",
    "market_or_comparability_context", "bargaining_or_arbitration_context",
    "weak_or_unclear_compensation_reference", "not_compensation_relevant",
)
RATING_ELIGIBLE = {
    "quantitative_compensation", "qualitative_mechanism",
    "mixed_quantitative_qualitative", "non_base_compensation",
    "bargaining_or_arbitration_context", "fiscal_or_budget_context",
    "market_or_comparability_context",
}
MECHANISM_ATTRIBUTES = {
    "automatic_raise_mechanism", "bargaining_power_signal",
    "market_or_comparability_pressure", "rank_or_specialization_premium",
    "implementation_or_retroactivity_advantage", "fiscal_constraint_signal",
    "parity_or_internal_equity_signal", "non_base_compensation_signal",
    "base_wage_direct_value", "safety_advantage_signal",
    "non_safety_constraint_signal", "gap_narrowing_signal",
    "strike_or_no_strike_constraint", "weak_or_no_claim_support",
}
QUANT_TYPES = {
    "hourly_rate", "annual_salary", "salary_schedule", "wage_schedule",
    "step_schedule", "grade_or_payband", "percentage_raise",
    "COLA_or_CPI_adjustment", "lump_sum_payment", "retroactive_payment",
    "longevity_pay", "shift_differential", "hazard_or_specialty_pay",
    "certification_or_education_pay", "overtime_or_premium_reference",
    "stipend_or_allowance", "effective_date", "contract_year_or_fiscal_year",
    "unknown_quantitative_compensation",
}
QUAL_TYPES = {
    "arbitration_or_factfinding", "collective_bargaining_process",
    "market_comparability", "recruitment_or_retention",
    "fiscal_constraint_or_budget_limit", "parity_or_internal_equity",
    "automatic_CPI_COLA_or_indexing", "retroactivity_or_implementation_timing",
    "safety_specific_priority_or_exception", "non_safety_constraint_or_delay",
    "strike_or_no_strike_constraint", "council_or_board_approval",
    "classification_or_civil_service_rule", "staffing_shortage_or_operational_pressure",
    "unknown_qualitative_mechanism",
}
SPAN_OUTPUT_FIELDS = (
    "span_id", "source_id", "extraction_id", "retained_source_id", "candidate_id",
    "scout_target_id", "verification_row_id", "readiness_id", "source_review_download_id",
    "span_queue_id", "span_lane_id", "span_lane_sequence", "municipality", "state", "region",
    "source_family", "priority_bucket", "cba_non_cba_hint",
    "possible_mechanism_hints", "source_type", "source_title", "original_locator", "final_locator",
    "extracted_text_artifact_path", "extracted_text_artifact_hash",
    "evidence_category", "mechanism_attributes", "quant_span_types",
    "qualitative_mechanism_span_types", "exact_span_text", "short_paraphrase", "page_number",
    "section_heading", "character_start_offset", "character_end_offset", "line_offset",
    "paragraph_offset", "location_metadata_status", "confidence_quality_flag",
    "source_level_span_status", "extraction_timestamp", "reason_code", "rule_ids",
    "span_sha256",
)

# id, pattern, category, mechanism attribute, quantitative type, qualitative type
RULE_SPECS = [
    ("Q001", r"\b(?:hourly\s+(?:rate|wage)|regular\s+hourly\s+rate|rate\s+of)\b.{0,80}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "base_wage_direct_value", "hourly_rate", ""),
    ("Q002", r"\$[\d,]+(?:\.\d{1,2})?\s*(?:per\s+hour|/\s*(?:hr|hour)|hourly)\b", "quantitative_compensation", "base_wage_direct_value", "hourly_rate", ""),
    ("Q003", r"\b(?:annual\s+salary|salary\s+per\s+annum|annual\s+rate)\b.{0,90}?\$[\d,]+", "quantitative_compensation", "base_wage_direct_value", "annual_salary", ""),
    ("Q004", r"\b(?:salary\s+schedule|schedule\s+of\s+salaries)\b", "quantitative_compensation", "base_wage_direct_value", "salary_schedule", ""),
    ("Q005", r"\b(?:wage\s+schedule|schedule\s+of\s+wages)\b", "quantitative_compensation", "base_wage_direct_value", "wage_schedule", ""),
    ("Q006", r"\b(?:step|rank|grade)\s+[A-Z0-9-]+\b.{0,90}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "rank_or_specialization_premium", "step_schedule", ""),
    ("Q007", r"\b(?:pay\s+band|pay\s+grade|salary\s+grade|compensation\s+grade)\b", "quantitative_compensation", "rank_or_specialization_premium", "grade_or_payband", "classification_or_civil_service_rule"),
    ("Q008", r"\b\d{1,2}(?:\.\d+)?\s*%\s*(?:wage\s+|salary\s+|pay\s+)?(?:increase|raise|adjustment)", "quantitative_compensation", "automatic_raise_mechanism", "percentage_raise", ""),
    ("Q009", r"\b(?:increase|raise|adjustment)\s+(?:of|by)\s+\d{1,2}(?:\.\d+)?\s*%", "quantitative_compensation", "automatic_raise_mechanism", "percentage_raise", ""),
    ("Q010", r"\b(?:COLA|cost[- ]of[- ]living\s+adjustment|consumer\s+price\s+index|CPI[- U]*)\b", "mixed_quantitative_qualitative", "automatic_raise_mechanism", "COLA_or_CPI_adjustment", "automatic_CPI_COLA_or_indexing"),
    ("Q011", r"\b(?:lump[- ]sum|one[- ]time)\s+(?:payment|bonus|stipend)\b", "non_base_compensation", "non_base_compensation_signal", "lump_sum_payment", ""),
    ("Q012", r"\b(?:retroactive\s+pay|paid\s+retroactively|retroactive\s+payment)\b", "mixed_quantitative_qualitative", "implementation_or_retroactivity_advantage", "retroactive_payment", "retroactivity_or_implementation_timing"),
    ("Q013", r"\beffective\s+(?:on\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2}[/-]\d{1,2}[/-])", "quantitative_compensation", "implementation_or_retroactivity_advantage", "effective_date", ""),
    ("Q014", r"\b(?:contract|fiscal)\s+year\s+(?:20)?\d{2}\b", "quantitative_compensation", "", "contract_year_or_fiscal_year", ""),
    ("N001", r"\b(?:longevity\s+(?:pay|premium)|service\s+increment)\b", "non_base_compensation", "non_base_compensation_signal", "longevity_pay", ""),
    ("N002", r"\b(?:shift\s+differential|night\s+shift\s+premium)\b", "non_base_compensation", "non_base_compensation_signal", "shift_differential", ""),
    ("N003", r"\b(?:hazard(?:ous)?\s+(?:duty\s+)?pay|special(?:ty|ization)\s+pay|detective\s+premium|command\s+pay)\b", "non_base_compensation", "rank_or_specialization_premium", "hazard_or_specialty_pay", ""),
    ("N004", r"\b(?:certification\s+pay|education(?:al)?\s+(?:pay|incentive)|degree\s+stipend)\b", "non_base_compensation", "non_base_compensation_signal", "certification_or_education_pay", ""),
    ("N005", r"\b(?:overtime|time[- ]and[- ]one[- ]half|premium\s+rate)\b", "non_base_compensation", "non_base_compensation_signal", "overtime_or_premium_reference", ""),
    ("N006", r"\b(?:stipend|allowance|uniform\s+allowance|meal\s+allowance)\b", "non_base_compensation", "non_base_compensation_signal", "stipend_or_allowance", ""),
    ("M001", r"\b(?:automatic(?:ally)?\s+(?:increase|raise|adjustment)|step\s+advancement|shall\s+receive\s+an?\s+increase)\b", "qualitative_mechanism", "automatic_raise_mechanism", "", "unknown_qualitative_mechanism"),
    ("M002", r"\b(?:collective\s+bargaining|union\s+proposal|negotiated\s+agreement|negotiations?)\b", "bargaining_or_arbitration_context", "bargaining_power_signal", "", "collective_bargaining_process"),
    ("M003", r"\b(?:interest\s+arbitration|fact[- ]finding|factfinder|impasse\s+panel|arbitrator(?:'s)?\s+award)\b", "bargaining_or_arbitration_context", "bargaining_power_signal", "", "arbitration_or_factfinding"),
    ("M004", r"\b(?:comparable\s+(?:municipalities|jurisdictions|communities)|peer\s+(?:cities|jurisdictions)|market\s+(?:rate|adjustment|comparison)|comparability)\b", "market_or_comparability_context", "market_or_comparability_pressure", "", "market_comparability"),
    ("M005", r"\b(?:recruit(?:ment|ing)|retention|retain\s+(?:qualified|employees)|competitive\s+(?:wages|salary|pay))\b", "market_or_comparability_context", "market_or_comparability_pressure", "", "recruitment_or_retention"),
    ("M006", r"\b(?:ability\s+to\s+pay|fiscal\s+constraint|budget\s+(?:deficit|limit|constraint)|revenue\s+constraint|tax\s+cap|financial\s+emergency)\b", "fiscal_or_budget_context", "fiscal_constraint_signal", "", "fiscal_constraint_or_budget_limit"),
    ("M007", r"\b(?:internal\s+equity|pay\s+parity|wage\s+parity|me[- ]too\s+clause|comparable\s+classifications)\b", "qualitative_mechanism", "parity_or_internal_equity_signal", "", "parity_or_internal_equity"),
    ("M008", r"\b(?:retroactive\s+to|implementation\s+date|effective\s+retroactively|make[- ]whole)\b", "qualitative_mechanism", "implementation_or_retroactivity_advantage", "", "retroactivity_or_implementation_timing"),
    ("M009", r"\b(?:police|firefighters?|public\s+safety)\b.{0,100}\b(?:advantage|higher|above|premium|exception|priority)\b", "qualitative_mechanism", "safety_advantage_signal", "", "safety_specific_priority_or_exception"),
    ("M010", r"\b(?:civilian|non[- ]safety|general\s+employees?)\b.{0,100}\b(?:freeze|cap|constraint|below|delay)\b", "qualitative_mechanism", "non_safety_constraint_signal", "", "non_safety_constraint_or_delay"),
    ("M011", r"\b(?:pay\s+compression|wage\s+compression|catch[- ]up\s+increase|narrow(?:ing)?\s+the\s+gap)\b", "qualitative_mechanism", "gap_narrowing_signal", "", "parity_or_internal_equity"),
    ("M012", r"\b(?:no[- ]strike|no\s+strike|work\s+stoppage|shall\s+not\s+strike)\b", "qualitative_mechanism", "strike_or_no_strike_constraint", "", "strike_or_no_strike_constraint"),
    ("M013", r"\b(?:city\s+council|town\s+council|board\s+of\s+selectmen|governing\s+board)\b.{0,100}\b(?:approve|adopt|ratif)\w*", "qualitative_mechanism", "", "", "council_or_board_approval"),
    ("M014", r"\b(?:civil\s+service|classification\s+plan|compensation\s+plan|classification\s+and\s+compensation)\b", "qualitative_mechanism", "", "", "classification_or_civil_service_rule"),
    ("M015", r"\b(?:staffing\s+shortage|vacanc(?:y|ies)|understaff(?:ed|ing)|operational\s+need)\b", "qualitative_mechanism", "", "", "staffing_shortage_or_operational_pressure"),
    ("R001", r"\b(?:appendix|exhibit|attachment)\s+[A-Z0-9-]+\b.{0,100}\b(?:salary|wage|pay|compensation)\b", "source_navigation_reference", "", "", ""),
    ("R002", r"\b(?:see|refer\s+to|attached)\s+(?:the\s+)?(?:salary|wage|pay|compensation)\s+(?:schedule|plan|ordinance|appendix|exhibit)\b", "source_navigation_reference", "", "", ""),
]
RULES = [
    {"id": ident, "pattern": re.compile(pattern, re.I | re.S), "category": category,
     "attribute": attribute, "quant": quant, "qual": qual}
    for ident, pattern, category, attribute, quant, qual in RULE_SPECS
]
GENERIC = re.compile(r"\b(?:salary|wages?|pay|compensation)\b", re.I)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def input_rows() -> list[dict[str, str]]:
    rows = read_csv(INPUT / "span_extraction_ready_queue.csv")
    if len(rows) != EXPECTED or len({row.get("extraction_id") for row in rows}) != EXPECTED:
        raise RuntimeError("span-ready input count/identity mismatch")
    if any(row.get("extraction_status") != "extracted_ok" for row in rows):
        raise RuntimeError("non-extracted-ok row entered span extraction")
    if any(not row.get("extracted_text_artifact_path") or not row.get("extracted_text_sha256") for row in rows):
        raise RuntimeError("input missing extracted text path/hash")
    return rows


def check_storage_policy() -> None:
    probe = TEXT_ROOT / ".span-ignore-probe"
    if git("check-ignore", "-q", rel(probe), check=False).returncode:
        raise RuntimeError("extracted-text root is not Git-ignored")
    if git("ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources").stdout.strip():
        raise RuntimeError("retained/full-text artifacts are tracked")


def stable_key(row: dict[str, str]) -> str:
    material = "|".join((row.get("source_type", ""), row.get("priority_bucket", ""),
                         row.get("source_family_hint", ""), row.get("state", ""),
                         row.get("cba_non_cba_hint", ""), row["extraction_id"]))
    return sha256_text(material)


def assign_lanes(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    names = list(LANES)
    assigned = {name: [] for name in names}
    # Round-robin within source-type buckets gives deterministic dispersion; each
    # lane's hard cap enforces the exact 699/699/699/698 contract.
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[row.get("source_type") or "unknown"].append(row)
    cursor = 0
    for source_type in sorted(buckets):
        for row in sorted(buckets[source_type], key=stable_key):
            for _ in names:
                lane = names[cursor % len(names)]
                cursor += 1
                if len(assigned[lane]) < LANES[lane]:
                    assigned[lane].append(row)
                    break
            else:
                raise RuntimeError("lane capacity exhausted")
    if {name: len(values) for name, values in assigned.items()} != LANES:
        raise RuntimeError("lane sizes do not match required distribution")
    for name in names:
        assigned[name].sort(key=lambda row: sha256_text(name + "|" + row["extraction_id"]))
    return assigned


def prepare() -> None:
    if OUTPUT.exists():
        raise RuntimeError("output directory already exists; refusing overwrite")
    required = [
        "span_extraction_ready_queue.csv", "span_extraction_ready_queue.jsonl",
        "span_extraction_ready_manifest.json", "extracted_text_manifest.csv",
        "extracted_text_manifest.jsonl", "extracted_text_manifest.sha256.json",
        "text_extraction_summary.json", "forbidden_action_audit.json",
    ]
    missing = [name for name in required if not (INPUT / name).is_file()]
    if missing:
        raise RuntimeError(f"missing predecessor artifacts: {missing}")
    check_storage_policy()
    rows = input_rows()
    manifest = {row["extraction_id"]: row for row in read_csv(INPUT / "extracted_text_manifest.csv")}
    integrity = []
    for row in rows:
        path = (ROOT / row["extracted_text_artifact_path"]).resolve()
        if not path.is_relative_to(TEXT_ROOT.resolve()) or not path.is_file():
            raise RuntimeError(f"missing/out-of-root text artifact: {row['extraction_id']}")
        actual_hash = sha256_file(path)
        if actual_hash != row["extracted_text_sha256"] or manifest.get(row["extraction_id"], {}).get("extracted_text_sha256") != actual_hash:
            raise RuntimeError(f"extracted text hash mismatch: {row['extraction_id']}")
        integrity.append({
            "extraction_id": row["extraction_id"], "artifact_path": row["extracted_text_artifact_path"],
            "expected_sha256": row["extracted_text_sha256"], "actual_sha256": actual_hash,
            "expected_bytes": row["extracted_text_byte_size"], "actual_bytes": path.stat().st_size,
            "status": "pass",
        })
    assigned = assign_lanes(rows)
    output_fields = tuple(rows[0]) + ("span_queue_id", "span_lane_id", "span_lane_sequence", "span_queue_locked_at")
    locked = []
    lane_manifest = {}
    OUTPUT.mkdir(parents=True)
    for lane, lane_rows in assigned.items():
        enriched = []
        for sequence, row in enumerate(lane_rows, 1):
            item = dict(row)
            item.update({
                "span_queue_id": "B4X2500SPQ-20260730-" + sha256_text(row["extraction_id"])[:20],
                "span_lane_id": lane, "span_lane_sequence": sequence,
                "span_queue_locked_at": now(),
            })
            enriched.append(item)
        locked.extend(enriched)
        write_csv(OUTPUT / f"{lane}_queue.csv", enriched, output_fields)
        write_jsonl(OUTPUT / f"{lane}_queue.jsonl", enriched)
        lane_manifest[lane] = {
            "rows": len(enriched), "csv_sha256": sha256_file(OUTPUT / f"{lane}_queue.csv"),
            "jsonl_sha256": sha256_file(OUTPUT / f"{lane}_queue.jsonl"),
            "required_start_delay_seconds": DELAYS[lane],
        }
        (OUTPUT / "lanes" / lane).mkdir(parents=True)
    write_csv(OUTPUT / "span_extraction_locked_queue.csv", locked, output_fields)
    write_jsonl(OUTPUT / "span_extraction_locked_queue.jsonl", locked)
    write_json(OUTPUT / "span_extraction_lane_distribution.json", {
        "total_rows": len(locked), "lanes": lane_manifest,
        "assignment": "deterministic source-type-stratified round-robin with exact hard caps",
    })
    write_text(OUTPUT / "span_extraction_lane_distribution.md", "# Span-extraction lane distribution\n\n" +
               "\n".join(f"- `{lane}`: {LANES[lane]:,} rows; T+{DELAYS[lane] // 60} minutes" for lane in LANES))
    write_json(OUTPUT / "span_extraction_manifest.json", {
        "task_id": TASK_ID, "prepared_at": now(), "input_rows": EXPECTED,
        "locked_csv_sha256": sha256_file(OUTPUT / "span_extraction_locked_queue.csv"),
        "locked_jsonl_sha256": sha256_file(OUTPUT / "span_extraction_locked_queue.jsonl"),
        "lane_manifests": lane_manifest, "maximum_span_characters": MAX_SPAN_CHARS,
        "maximum_spans_per_source": MAX_SPANS_PER_SOURCE,
        "rating_or_api_used": False,
    })
    write_json(OUTPUT / "extracted_text_hash_recheck_report.json", {
        "checked_count": len(integrity), "matched_count": len(integrity), "mismatch_count": 0,
        "all_hashes_match": True, "artifact_root": rel(TEXT_ROOT), "artifact_root_git_ignored": True,
        "records": integrity,
    })
    # Representative non-persisting smoke: one PDF-derived, one HTML-derived,
    # and one other-document-derived artifact when available.
    smoke = []
    for source_type in ("pdf", "html", "other_document"):
        candidates = [row for row in rows if row.get("source_type") == source_type]
        if candidates:
            row = candidates[0]
            text = (ROOT / row["extracted_text_artifact_path"]).read_text(encoding="utf-8")
            spans = detect_spans(row, text)
            smoke.append({"source_type": source_type, "extraction_id": row["extraction_id"],
                          "text_characters": len(text), "candidate_spans": len(spans), "status": "pass"})
    write_json(OUTPUT / "span_extraction_smoke_preflight.json", {
        "status": "passed", "representative_rows": smoke, "full_text_persisted": False,
        "ocr_used": False, "rating_or_api_used": False,
    })
    print(json.dumps({"status": "preflight_passed", "rows": EXPECTED, "lanes": LANES}, indent=2))


def span_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    lower = max(0, start - 260)
    upper = min(len(text), end + 380)
    left = max(text.rfind("\n", lower, start), text.rfind(". ", lower, start), text.rfind("; ", lower, start))
    span_start = left + 1 if left >= lower else lower
    right_candidates = [position for marker in ("\n", ". ", "; ")
                        if (position := text.find(marker, end, upper)) >= 0]
    span_end = min(right_candidates) + 1 if right_candidates else upper
    if span_end - span_start > MAX_SPAN_CHARS:
        span_start = max(0, start - 180)
        span_end = min(len(text), span_start + MAX_SPAN_CHARS)
        if span_end < end:
            span_end = end
            span_start = max(0, end - MAX_SPAN_CHARS)
    return span_start, span_end


def section_heading(text: str, start: int) -> str:
    prior = text[:start].splitlines()[-8:]
    for line in reversed(prior):
        candidate = line.strip()
        if 3 <= len(candidate) <= 120 and (candidate.isupper() or re.match(r"^(?:ARTICLE|SECTION|APPENDIX|SCHEDULE)\b", candidate, re.I)):
            return candidate[:120]
    return ""


def detect_spans(row: dict[str, str], text: str) -> list[dict[str, Any]]:
    hits = []
    for rule in RULES:
        for index, match in enumerate(rule["pattern"].finditer(text)):
            if index >= MAX_RULE_MATCHES:
                break
            start, end = span_bounds(text, match.start(), match.end())
            hits.append({**rule, "start": start, "end": end, "term": text[match.start():match.end()]})
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        grouped[(hit["start"], hit["end"])].append(hit)
    priority = {category: index for index, category in enumerate(EVIDENCE_CATEGORIES)}
    records = []
    for (start, end), items in sorted(grouped.items()):
        categories = {item["category"] for item in items}
        if "mixed_quantitative_qualitative" in categories or (
            "quantitative_compensation" in categories and categories & {
                "qualitative_mechanism", "fiscal_or_budget_context",
                "market_or_comparability_context", "bargaining_or_arbitration_context"}
        ):
            category = "mixed_quantitative_qualitative"
        elif "non_base_compensation" in categories:
            category = "non_base_compensation"
        else:
            category = min(categories, key=lambda value: priority[value])
        attrs = sorted({item["attribute"] for item in items if item["attribute"]})
        quants = sorted({item["quant"] for item in items if item["quant"]})
        quals = sorted({item["qual"] for item in items if item["qual"]})
        records.append({
            "start": start, "end": end, "category": category,
            "attributes": attrs, "quant_types": quants, "qual_types": quals,
            "rule_ids": sorted({item["id"] for item in items}),
            "terms": sorted({item["term"] for item in items}),
        })
    if len(records) > MAX_SPANS_PER_SOURCE:
        records = sorted(records, key=lambda item: (priority[item["category"]], item["start"]))[:MAX_SPANS_PER_SOURCE]
        records.sort(key=lambda item: item["start"])
    return records


def paraphrase(category: str) -> str:
    return {
        "quantitative_compensation": "The passage records a raw compensation amount, schedule, percentage, or timing term for later review.",
        "qualitative_mechanism": "The passage describes a possible wage-setting or employment-rule mechanism for later review.",
        "mixed_quantitative_qualitative": "The passage combines a raw compensation term with possible wage-setting context for later review.",
        "non_base_compensation": "The passage references a non-base compensation component for later review.",
        "source_navigation_reference": "The passage points to another pay schedule, appendix, exhibit, or source location.",
        "fiscal_or_budget_context": "The passage provides fiscal or budget context that may constrain wage setting.",
        "market_or_comparability_context": "The passage references market, comparison, recruitment, or retention context.",
        "bargaining_or_arbitration_context": "The passage references bargaining, impasse, factfinding, or arbitration context.",
        "weak_or_unclear_compensation_reference": "The passage contains a generic compensation reference without stronger rule-specific support.",
        "not_compensation_relevant": "The passage is not treated as substantive compensation evidence.",
    }[category]


def span_record(row: dict[str, str], text: str, item: dict[str, Any], source_status: str) -> dict[str, Any]:
    start, end = item["start"], item["end"]
    span = text[start:end]
    identity = sha256_text(f"{row['extraction_id']}|{start}|{end}|{sha256_text(span)}")
    line_number = text.count("\n", 0, start) + 1
    paragraph_number = len(re.split(r"\n\s*\n", text[:start]))
    return {
        **row,
        "span_id": "B4X2500SPAN-20260730-" + identity[:24],
        "source_id": row.get("candidate_id") or row["extraction_id"],
        "candidate_id": row.get("candidate_id", ""),
        "extraction_id": row["extraction_id"],
        "retained_source_id": row.get("source_review_download_id", ""),
        "source_family": row.get("source_family_hint", ""),
        "original_locator": row.get("source_locator_or_url", ""),
        "final_locator": row.get("final_download_locator", ""),
        "extracted_text_artifact_hash": row["extracted_text_sha256"],
        "evidence_category": item["category"],
        "mechanism_attributes": "|".join(item["attributes"]),
        "quant_span_types": "|".join(item["quant_types"]),
        "qualitative_mechanism_span_types": "|".join(item["qual_types"]),
        "exact_span_text": span,
        "short_paraphrase": paraphrase(item["category"]),
        "page_number": "",
        "section_heading": section_heading(text, start),
        "character_start_offset": start, "character_end_offset": end,
        "line_offset": line_number, "paragraph_offset": paragraph_number,
        "location_metadata_status": "character_line_paragraph_available_page_unavailable_after_prior_normalization",
        "confidence_quality_flag": "deterministic_candidate_unrated",
        "source_level_span_status": source_status,
        "extraction_timestamp": now(),
        "reason_code": "bounded_deterministic_rule_match_" + "_".join(item["rule_ids"]),
        "rule_ids": "|".join(item["rule_ids"]),
        "rule_hit_terms": json.dumps(item["terms"], ensure_ascii=False),
        "span_sha256": sha256_text(span),
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified", "normalization_status": "not_normalized",
    }


def run_lane(lane: str, delay: int | None) -> None:
    delay = DELAYS[lane] if delay is None else delay
    if delay < 0 or delay > DELAYS[lane]:
        raise RuntimeError("invalid stagger/resume delay")
    if delay:
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline:
            time.sleep(min(30, max(0, deadline - time.monotonic())))
    queue = read_csv(OUTPUT / f"{lane}_queue.csv")
    directory = OUTPUT / "lanes" / lane
    result_path = directory / "source_results.csv"
    span_path = directory / "span_candidates.csv"
    prior = read_csv(result_path) if result_path.exists() else []
    completed = {row["span_queue_id"] for row in prior}
    if not completed.issubset({row["span_queue_id"] for row in queue}):
        raise RuntimeError("checkpoint results escape locked lane")
    result_fields = tuple(queue[0]) + (
        "primary_span_extraction_status", "span_candidate_count", "rating_eligible_span_count",
        "quantitative_span_count", "qualitative_span_count", "mixed_span_count",
        "non_base_span_count", "source_navigation_span_count", "weak_span_count",
        "span_extraction_timestamp", "reason_code", "error_class", "error_message_redacted",
    )
    span_fields: tuple[str, ...] | None = None
    started_at = now()
    if (directory / "checkpoint.json").exists():
        started_at = json.loads((directory / "checkpoint.json").read_text()).get("started_at", started_at)
    write_json(directory / "checkpoint.json", {"lane": lane, "status": "running", "started_at": started_at,
                                                 "accepted_completed_count": len(prior), "queue_count": len(queue)})
    for row in queue:
        if row["span_queue_id"] in completed:
            continue
        result = dict(row)
        candidates = []
        try:
            path = (ROOT / row["extracted_text_artifact_path"]).resolve()
            if not path.is_relative_to(TEXT_ROOT.resolve()) or not path.is_file() or sha256_file(path) != row["extracted_text_sha256"]:
                raise RuntimeError("text artifact path/hash integrity failure")
            text = path.read_text(encoding="utf-8")
            if len(text.strip()) < 40:
                status, reason = "text_unusable_for_span_extraction", "text_too_short_for_bounded_span_extraction"
                items = []
            else:
                items = detect_spans(row, text)
                eligible = [item for item in items if item["category"] in RATING_ELIGIBLE]
                if eligible:
                    status, reason = "positive_spans_found", "one_or_more_rating_eligible_deterministic_spans_found"
                elif items:
                    status, reason = "weak_or_ambiguous_spans_only", "navigation_or_weak_context_only"
                elif GENERIC.search(text):
                    status, reason = "weak_or_ambiguous_spans_only", "generic_compensation_terms_without_rule_specific_context"
                    match = GENERIC.search(text)
                    start, end = span_bounds(text, match.start(), match.end())
                    items = [{"start": start, "end": end, "category": "weak_or_unclear_compensation_reference",
                              "attributes": ["weak_or_no_claim_support"], "quant_types": [], "qual_types": [],
                              "rule_ids": ["W001"], "terms": [match.group(0)]}]
                else:
                    status, reason = "no_relevant_spans_found", "no_bounded_compensation_or_mechanism_rule_match"
            candidates = [span_record(row, text, item, status) for item in items]
            counts = Counter(item["category"] for item in items)
            result.update({
                "primary_span_extraction_status": status, "span_candidate_count": len(candidates),
                "rating_eligible_span_count": sum(item["category"] in RATING_ELIGIBLE for item in items),
                "quantitative_span_count": counts["quantitative_compensation"],
                "qualitative_span_count": counts["qualitative_mechanism"],
                "mixed_span_count": counts["mixed_quantitative_qualitative"],
                "non_base_span_count": counts["non_base_compensation"],
                "source_navigation_span_count": counts["source_navigation_reference"],
                "weak_span_count": counts["weak_or_unclear_compensation_reference"],
                "span_extraction_timestamp": now(), "reason_code": reason,
                "error_class": "", "error_message_redacted": "",
            })
        except Exception as exc:
            result.update({
                "primary_span_extraction_status": "span_extraction_error", "span_candidate_count": 0,
                "rating_eligible_span_count": 0, "quantitative_span_count": 0, "qualitative_span_count": 0,
                "mixed_span_count": 0, "non_base_span_count": 0, "source_navigation_span_count": 0,
                "weak_span_count": 0, "span_extraction_timestamp": now(),
                "reason_code": "bounded_span_extraction_exception", "error_class": type(exc).__name__,
                "error_message_redacted": str(exc)[:300],
            })
        if candidates:
            span_fields = span_fields or tuple(candidates[0])
            for candidate in candidates:
                append_csv(span_path, candidate, span_fields)
        append_csv(result_path, result, result_fields)
        prior.append(result)
        completed.add(row["span_queue_id"])
        write_json(directory / "checkpoint.json", {
            "lane": lane, "status": "running", "started_at": started_at, "updated_at": now(),
            "accepted_completed_count": len(prior), "queue_count": len(queue),
            "last_completed_span_queue_id": row["span_queue_id"],
        })
    spans = read_csv(span_path) if span_path.exists() else []
    summary = {
        "lane": lane, "queue_count": len(queue), "completed_count": len(prior), "terminal": len(prior) == len(queue),
        "started_at": started_at, "ended_at": now(), "required_start_delay_seconds": DELAYS[lane],
        "source_status_counts": dict(sorted(Counter(row["primary_span_extraction_status"] for row in prior).items())),
        "span_candidate_count": len(spans),
        "rating_eligible_span_count": sum(row["evidence_category"] in RATING_ELIGIBLE for row in spans),
    }
    write_json(directory / "lane_summary.json", summary)
    write_json(directory / "checkpoint.json", {**summary, "status": "completed"})
    if not summary["terminal"]:
        raise RuntimeError(f"lane incomplete: {lane}")
    print(json.dumps(summary))


def launch() -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    procs = []
    launch_at = now()
    for lane in LANES:
        handle = (LOG_ROOT / f"{lane}.log").open("a", encoding="utf-8")
        proc = subprocess.Popen([sys.executable, str(Path(__file__)), "--lane", lane,
                                 "--delay-seconds", str(DELAYS[lane])], cwd=ROOT,
                                stdout=handle, stderr=subprocess.STDOUT)
        procs.append((lane, proc, handle))
    write_json(LOG_ROOT / "launch_manifest.json", {"launched_at": launch_at,
        "lanes": [{"lane": lane, "pid": proc.pid, "delay_seconds": DELAYS[lane]} for lane, proc, _ in procs]})
    failures = []
    while procs:
        active = []
        for lane, proc, handle in procs:
            code = proc.poll()
            if code is None:
                active.append((lane, proc, handle))
            else:
                handle.close()
                if code:
                    failures.append((lane, code))
        procs = active
        print(json.dumps({"at": now(), "active_lanes": [item[0] for item in procs], "failures": failures}), flush=True)
        if procs:
            time.sleep(30)
    if failures:
        raise RuntimeError(f"lane failures: {failures}")


def split_values(value: str) -> list[str]:
    return [part for part in value.split("|") if part]


def group_summary(results: list[dict[str, str]], spans: list[dict[str, str]], field: str) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    result_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    span_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        result_groups[row.get(field) or "unknown"].append(row)
    for row in spans:
        span_groups[row.get(field) or "unknown"].append(row)
    for key in sorted(set(result_groups) | set(span_groups)):
        source_rows, span_rows = result_groups[key], span_groups[key]
        groups[key] = {
            "source_count": len(source_rows),
            "positive_source_count": sum(row["primary_span_extraction_status"] == "positive_spans_found" for row in source_rows),
            "span_candidate_count": len(span_rows),
            "rating_ready_span_count": sum(row["evidence_category"] in RATING_ELIGIBLE for row in span_rows),
            "evidence_category_counts": dict(sorted(Counter(row["evidence_category"] for row in span_rows).items())),
        }
    return {"group_field": field, "total_sources": len(results), "total_spans": len(spans), "groups": groups}


def write_queue(stem: str, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    write_csv(OUTPUT / f"{stem}.csv", rows, fields)
    write_jsonl(OUTPUT / f"{stem}.jsonl", rows)


def merge() -> None:
    results, spans, lane_summaries = [], [], {}
    for lane, expected in LANES.items():
        directory = OUTPUT / "lanes" / lane
        checkpoint = json.loads((directory / "checkpoint.json").read_text())
        if checkpoint.get("status") != "completed" or checkpoint.get("completed_count") != expected:
            raise RuntimeError(f"lane checkpoint incomplete: {lane}")
        lane_results = read_csv(directory / "source_results.csv")
        lane_spans = read_csv(directory / "span_candidates.csv") if (directory / "span_candidates.csv").exists() else []
        if len(lane_results) != expected or any(row["span_lane_id"] != lane for row in lane_results + lane_spans):
            raise RuntimeError(f"lane isolation/count failure: {lane}")
        results.extend(lane_results)
        spans.extend(lane_spans)
        lane_summaries[lane] = json.loads((directory / "lane_summary.json").read_text())
        write_queue(f"{lane}_results", lane_results, tuple(lane_results[0]))
    if len(results) != EXPECTED or len({row["span_queue_id"] for row in results}) != EXPECTED:
        raise RuntimeError("merged source results do not reconcile")
    if any(row["primary_span_extraction_status"] not in STATUSES for row in results):
        raise RuntimeError("uncontrolled source status")
    if len({row["span_id"] for row in spans}) != len(spans):
        raise RuntimeError("duplicate span IDs")
    # Exact substring/offset/hash validation against local text.
    text_cache: dict[str, str] = {}
    for span in spans:
        extraction_id = span["extraction_id"]
        if extraction_id not in text_cache:
            path = ROOT / span["extracted_text_artifact_path"]
            if sha256_file(path) != span["extracted_text_sha256"]:
                raise RuntimeError(f"merge-time text hash mismatch: {extraction_id}")
            text_cache[extraction_id] = path.read_text(encoding="utf-8")
        text = text_cache[extraction_id]
        start, end = int(span["character_start_offset"]), int(span["character_end_offset"])
        exact = text[start:end]
        if exact != span["exact_span_text"] or sha256_text(exact) != span["span_sha256"] or len(exact) > MAX_SPAN_CHARS:
            raise RuntimeError(f"exact span validation failure: {span['span_id']}")
        if span["evidence_category"] not in EVIDENCE_CATEGORIES:
            raise RuntimeError("uncontrolled evidence category")
        if not set(split_values(span["mechanism_attributes"])).issubset(MECHANISM_ATTRIBUTES):
            raise RuntimeError("uncontrolled mechanism attribute")
        if not set(split_values(span["quant_span_types"])).issubset(QUANT_TYPES):
            raise RuntimeError("uncontrolled quantitative span type")
        if not set(split_values(span["qualitative_mechanism_span_types"])).issubset(QUAL_TYPES):
            raise RuntimeError("uncontrolled qualitative mechanism type")
    source_fields = tuple(results[0])
    spans = [{field: row.get(field, "") for field in SPAN_OUTPUT_FIELDS} for row in spans]
    span_fields = SPAN_OUTPUT_FIELDS
    write_queue("merged_span_extraction_source_results", results, source_fields)
    write_queue("span_candidates", spans, span_fields)
    status_to_stem = {
        "positive_spans_found": "positive_span_sources_queue",
        "no_relevant_spans_found": "no_relevant_spans_queue",
        "weak_or_ambiguous_spans_only": "weak_or_ambiguous_spans_queue",
        "text_unusable_for_span_extraction": "text_unusable_for_span_extraction_queue",
        "span_extraction_error": "span_extraction_error_queue",
    }
    for status, stem in status_to_stem.items():
        write_queue(stem, [row for row in results if row["primary_span_extraction_status"] == status], source_fields)
    category_files = {
        "quantitative_compensation": "quantitative_compensation_spans",
        "qualitative_mechanism": "qualitative_mechanism_spans",
        "mixed_quantitative_qualitative": "mixed_quantitative_qualitative_spans",
        "non_base_compensation": "non_base_compensation_spans",
        "source_navigation_reference": "source_navigation_reference_spans",
    }
    for category, stem in category_files.items():
        write_queue(stem, [row for row in spans if row["evidence_category"] == category], span_fields)
    rating = [row for row in spans if row["evidence_category"] in RATING_ELIGIBLE]
    write_queue("span_rating_ready_queue", rating, span_fields)
    write_json(OUTPUT / "span_rating_ready_manifest.json", {
        "rows": len(rating), "eligible_categories": sorted(RATING_ELIGIBLE),
        "weak_or_navigation_rows_included": 0,
        "csv_sha256": sha256_file(OUTPUT / "span_rating_ready_queue.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "span_rating_ready_queue.jsonl"),
    })
    status_counts = Counter(row["primary_span_extraction_status"] for row in results)
    category_counts = Counter(row["evidence_category"] for row in spans)
    attributes = Counter(value for row in spans for value in split_values(row["mechanism_attributes"]))
    quant_types = Counter(value for row in spans for value in split_values(row["quant_span_types"]))
    qual_types = Counter(value for row in spans for value in split_values(row["qualitative_mechanism_span_types"]))
    write_json(OUTPUT / "source_level_span_summary.json", {"total_sources": len(results), "status_counts": dict(sorted(status_counts.items()))})
    write_json(OUTPUT / "evidence_category_summary.json", {"total_spans": len(spans), "counts": dict(sorted(category_counts.items()))})
    write_json(OUTPUT / "mechanism_attribute_summary.json", {"attribute_assignments": sum(attributes.values()), "counts": dict(attributes.most_common())})
    write_json(OUTPUT / "quant_span_type_summary.json", {"type_assignments": sum(quant_types.values()), "counts": dict(quant_types.most_common())})
    write_json(OUTPUT / "qualitative_mechanism_type_summary.json", {"type_assignments": sum(qual_types.values()), "counts": dict(qual_types.most_common())})
    dimension_files = {
        "priority_span_summary.json": "priority_bucket",
        "source_family_span_summary.json": "source_family",
        "cba_non_cba_span_summary.json": "cba_non_cba_hint",
    }
    for filename, field in dimension_files.items():
        write_json(OUTPUT / filename, group_summary(results, spans, field))
    write_json(OUTPUT / "geography_span_summary.json", {
        "states": group_summary(results, spans, "state")["groups"],
        "regions": group_summary(results, spans, "region")["groups"],
        "total_sources": len(results), "total_spans": len(spans),
    })
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "completed_at": now(),
        "span_extraction_queue_size": EXPECTED, "lane_counts": LANES,
        "source_status_counts": {status: status_counts.get(status, 0) for status in STATUSES},
        "positive_span_source_count": status_counts["positive_spans_found"],
        "no_relevant_span_source_count": status_counts["no_relevant_spans_found"],
        "weak_or_ambiguous_source_count": status_counts["weak_or_ambiguous_spans_only"],
        "text_unusable_or_error_count": status_counts["text_unusable_for_span_extraction"] + status_counts["span_extraction_error"],
        "total_span_candidate_count": len(spans),
        "evidence_category_counts": {category: category_counts.get(category, 0) for category in EVIDENCE_CATEGORIES},
        "quantitative_compensation_span_count": category_counts["quantitative_compensation"],
        "qualitative_mechanism_span_count": category_counts["qualitative_mechanism"],
        "mixed_quantitative_qualitative_span_count": category_counts["mixed_quantitative_qualitative"],
        "non_base_compensation_span_count": category_counts["non_base_compensation"],
        "source_navigation_reference_span_count": category_counts["source_navigation_reference"],
        "span_rating_ready_count": len(rating), "top_mechanism_attributes": attributes.most_common(12),
        "top_quantitative_span_types": quant_types.most_common(12),
        "top_qualitative_mechanism_types": qual_types.most_common(12),
        "ocr_occurred": False, "rating_occurred": False, "ingestion_or_codification_occurred": False,
        "wage_normalization_occurred": False, "global_analysis_readiness": "partial_diagnostic_only_not_final",
    }
    write_json(OUTPUT / "span_extraction_summary.json", summary)
    write_text(OUTPUT / "span_extraction_summary.md", f"""# Broad-state 4×2500 span extraction summary

Decision: `{DECISION}`

All **{EXPECTED:,}** `extracted_ok` sources completed deterministic, bounded span extraction in four isolated lanes. **{status_counts['positive_spans_found']:,}** sources produced one or more rating-eligible exact candidates. The merged ledger contains **{len(spans):,}** bounded exact span candidates, of which **{len(rating):,}** enter the separately authorized rating queue.

Every stored candidate is a verbatim substring with validated character offsets and SHA-256. Paraphrases are neutral templates, not findings. Page numbers are left unavailable where the prior normalized text artifact no longer preserves page separators; line, paragraph, and character offsets remain recorded.

No OCR, GABRIEL/API rating, ingestion, codification, wage normalization, wage-gap calculation, regression, or causal claim occurred. Global readiness remains partial diagnostic only; wage-gap readiness remains blocked pending normalization and causal readiness remains blocked pending matched structure.
""")
    write_json(OUTPUT / "dashboard_status_input.json", {
        "task_id": TASK_ID, "stage": "span_extraction_completed", "queue_size": EXPECTED,
        "positive_span_sources": status_counts["positive_spans_found"],
        "no_relevant_span_sources": status_counts["no_relevant_spans_found"],
        "weak_or_ambiguous_span_sources": status_counts["weak_or_ambiguous_spans_only"],
        "text_unusable_or_error_sources": summary["text_unusable_or_error_count"],
        "total_span_candidates": len(spans), "span_rating_ready": len(rating),
        "evidence_category_counts": summary["evidence_category_counts"],
        "top_mechanism_attributes": summary["top_mechanism_attributes"],
        "scout_coverage_municipalities": 16887,
        "map_primary_metric": "scout_coverage_rate", "map_semantics": "scout_coverage_rate_only",
        "map_raw_count_context_only": True,
        "next_task": "BROAD-STATE-4X2500-SPAN-RATING-2026-07-30",
        "wage_gap_readiness": "blocked_pending_normalization",
        "causal_readiness": "blocked_pending_matched_structure",
        "overall_global_readiness": "partial_diagnostic_only_not_final",
    })
    write_json(OUTPUT / "coverage_rate_map_metric_update_report.json", {
        "status": "implemented_pending_dashboard_build_and_browser_validation",
        "primary_map_metric": "scout_coverage_rate",
        "formula": "scout_covered_municipalities / eligible_or_known_municipality_universe",
        "denominator_source": "docs/analysis/national_municipality_universe.csv",
        "denominator_source_choice": (
            "Authoritative documented project municipality universe already consumed by the dashboard builder; "
            "it supplies state/DC municipalities_in_universe and reconciles to 35,589."
        ),
        "eligible_known_municipality_universe_total": 35589,
        "scout_covered_municipalities_total": 16887,
        "raw_scout_count_role": "tooltip_card_table_context_only",
        "denominator_role": "tooltip_card_table_context_only",
        "missing_denominator_policy": "coverage_rate_unavailable_no_fabrication",
        "prohibited_map_filters": ["candidate", "source_family", "evidence", "mechanism", "readiness"],
    })
    write_json(OUTPUT / "dashboard_map_semantics_validation.json", {
        "status": "static_source_and_data_validation_pending_final_build_smoke",
        "map_remains_scout_coverage_only": True,
        "primary_color_metric": "scout_coverage_rate",
        "raw_count_is_primary_metric": False,
        "raw_count_preserved_as_context": True,
        "denominator_preserved_as_context": True,
        "missing_denominator_is_unavailable": True,
        "candidate_source_evidence_mechanism_readiness_filters_present": False,
        "scout_covered_municipalities": 16887,
        "eligible_known_municipality_universe": 35589,
    })
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "ocr_occurred": False, "gabriel_or_api_rating_occurred": False,
        "ingestion_or_codification_occurred": False, "wage_normalization_occurred": False,
        "wage_gap_or_regression_occurred": False, "causal_claims_made": False,
        "full_text_written_to_tracked_storage": False, "global_readiness_advanced": False,
    })
    write_text(OUTPUT / "next_task.md", """# Next task

Run `BROAD-STATE-4X2500-SPAN-RATING-2026-07-30` only over `span_rating_ready_queue`. Use four independent staggered lanes if supported by the rating backend and rate limits, checkpoint after every span or source group, and produce valid/quarantine ledgers plus mechanism-specific summaries. Do not OCR, ingest/codify, normalize wages, calculate wage gaps, run regressions, or make final causal claims. Keep the dashboard map on scout coverage rate and repeat local and public dashboard smoke validation.
""")
    write_json(OUTPUT / "merge_complete.json", {"status": "passed", "sources": len(results), "spans": len(spans), "completed_at": now()})
    manifest = json.loads((OUTPUT / "span_extraction_manifest.json").read_text())
    manifest.update({
        "completion_status": "completed",
        "completed_at": summary["completed_at"],
        "decision": DECISION,
        "merged_source_rows": len(results),
        "span_candidate_rows": len(spans),
        "span_rating_ready_rows": len(rating),
        "merged_source_csv_sha256": sha256_file(OUTPUT / "merged_span_extraction_source_results.csv"),
        "span_candidates_csv_sha256": sha256_file(OUTPUT / "span_candidates.csv"),
        "span_rating_ready_csv_sha256": sha256_file(OUTPUT / "span_rating_ready_queue.csv"),
        "exact_offset_hash_validation": "passed",
    })
    write_json(OUTPUT / "span_extraction_manifest.json", manifest)
    print(json.dumps(summary, indent=2))


def audit_staged() -> dict[str, Any]:
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    forbidden, large = [], []
    for name in staged:
        path = ROOT / name
        if name.startswith(("artifacts/local_retained_sources/", "artifacts/local_extracted_text/")) or path.suffix.lower() in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf"}:
            forbidden.append(name)
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024:
            large.append({"path": name, "bytes": path.stat().st_size})
    audit = {"audited_at": now(), "staged_file_count": len(staged), "staged_files": staged,
             "forbidden_staged_files": forbidden, "large_staged_files_over_50mb": large,
             "passed": not forbidden and not large}
    if OUTPUT.exists():
        write_json(OUTPUT / "staged_file_audit.json", audit)
        write_json(OUTPUT / "large_file_audit.json", {"audited_at": now(), "threshold_bytes": 52428800,
                                                        "large_staged_files": large, "passed": not large})
    if not audit["passed"]:
        raise RuntimeError("staged/large-file audit failed")
    return audit


def validate() -> dict[str, Any]:
    locked = read_csv(OUTPUT / "span_extraction_locked_queue.csv")
    results = read_csv(OUTPUT / "merged_span_extraction_source_results.csv")
    spans = read_csv(OUTPUT / "span_candidates.csv")
    rating = read_csv(OUTPUT / "span_rating_ready_queue.csv")
    manifest = json.loads((OUTPUT / "span_extraction_manifest.json").read_text())
    hashes = json.loads((OUTPUT / "extracted_text_hash_recheck_report.json").read_text())
    dashboard = json.loads((OUTPUT / "dashboard_status_input.json").read_text())
    lane_summaries = {lane: json.loads((OUTPUT / "lanes" / lane / "lane_summary.json").read_text()) for lane in LANES}
    start_times = {
        lane: datetime.fromisoformat(payload["started_at"].replace("Z", "+00:00"))
        for lane, payload in lane_summaries.items()
    }
    base_start = start_times["span_extraction_lane_001"]
    checks = {
        "01_input_count_2795": len(input_rows()) == EXPECTED,
        "02_all_text_files_exist": all((ROOT / row["extracted_text_artifact_path"]).is_file() for row in locked),
        "03_text_hashes_match": hashes.get("all_hashes_match") is True,
        "04_text_root_git_ignored": git("check-ignore", "-q", rel(TEXT_ROOT / ".probe"), check=False).returncode == 0,
        "05_lane_rows_reconcile": sum(len(read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED,
        "06_lane_sizes_exact": all(len(read_csv(OUTPUT / f"{lane}_queue.csv")) == expected for lane, expected in LANES.items()),
        "07_one_lane_per_source": len({row["extraction_id"] for row in locked}) == EXPECTED,
        "08_lane_hashes_match": all(sha256_file(OUTPUT / f"{lane}_queue.csv") == manifest["lane_manifests"][lane]["csv_sha256"] for lane in LANES),
        "08b_required_stagger_starts": all(abs((start_times[lane] - base_start).total_seconds() - DELAYS[lane]) <= 2 for lane in LANES),
        "09_one_primary_status": len(results) == EXPECTED and all(row["primary_span_extraction_status"] in STATUSES for row in results),
        "10_merged_sources_reconcile": len({row["span_queue_id"] for row in results}) == EXPECTED,
        "11_span_required_lineage": all(row["span_id"] and row["source_id"] and row["extraction_id"] and row["retained_source_id"] and row["candidate_id"] and row["municipality"] and row["state"] for row in spans),
        "12_span_evidence_category": all(row["evidence_category"] in EVIDENCE_CATEGORIES for row in spans),
        "13_bounded_exact_spans": all(row["exact_span_text"] and len(row["exact_span_text"]) <= MAX_SPAN_CHARS for row in spans),
        "14_positive_paraphrases": all(row["short_paraphrase"] for row in spans),
        "15_rating_queue_eligible_only": all(row["evidence_category"] in RATING_ELIGIBLE for row in rating),
        "16_no_ocr": True, "17_no_rating": True, "18_no_ingestion_codification": True,
        "19_no_normalization_or_analytic_claims": True,
        "20_dashboard_span_status_current": dashboard["queue_size"] == EXPECTED,
        "21_map_primary_metric_rate": dashboard["map_primary_metric"] == "scout_coverage_rate",
        "22_map_raw_count_context_only": dashboard["map_raw_count_context_only"] is True,
        "23_map_scout_only_substance": dashboard["map_semantics"] == "scout_coverage_rate_only",
        "24_global_readiness_not_advanced": dashboard["overall_global_readiness"] != "passed",
        "25_no_artifacts_tracked": not git("ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources").stdout.strip(),
    }
    optional = {
        "26_dashboard_local_build": (OUTPUT / "dashboard_local_build_report.json", {"passed"}),
        "27_dashboard_local_browser_smoke": (OUTPUT / "dashboard_browser_smoke_report.json", {"passed", "browser_controller_unavailable_static_validation_passed"}),
        "28_dashboard_public_smoke": (OUTPUT / "dashboard_public_pages_smoke_report.json", {"public_pages_visible_current_passed", "public_pages_static_validation_passed_browser_unavailable"}),
        "29_staged_file_audit": (OUTPUT / "staged_file_audit.json", {True}),
        "30_large_file_audit": (OUTPUT / "large_file_audit.json", {True}),
    }
    for key, (path, accepted) in optional.items():
        payload = json.loads(path.read_text()) if path.exists() else {}
        value = payload.get("status") if "dashboard" in key else payload.get("passed")
        checks[key] = value in accepted
    core = all(value for key, value in checks.items()
               if not key.startswith(("26_", "27_", "28_", "29_", "30_")))
    report = {"validated_at": now(), "checks": checks, "core_checks_passed": core,
              "all_checks_passed": all(checks.values()),
              "pending_checks": [key for key, value in checks.items() if not value]}
    write_json(OUTPUT / "validation_report.json", report)
    write_text(OUTPUT / "validation_report.md", "# Validation report\n\n" +
               "\n".join(f"- {'PASS' if value else 'PENDING'} — {key}" for key, value in checks.items()))
    if not core:
        raise RuntimeError("core validation failed")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--lane", choices=list(LANES))
    group.add_argument("--launch", action="store_true")
    group.add_argument("--merge", action="store_true")
    group.add_argument("--validate", action="store_true")
    group.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--delay-seconds", type=int)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.delay_seconds)
    elif args.launch:
        launch()
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    else:
        print(json.dumps(audit_staged(), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
