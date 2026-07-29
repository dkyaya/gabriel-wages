#!/usr/bin/env python3
"""Deterministic four-lane exact-span extraction over 3,815 local texts.

The runner performs no network access, model/API calls, rating, OCR, rendering,
ingestion, codification, wage normalization/comparison, or causal/statistical
analysis. Full text remains in ignored local artifact storage. Tracked outputs
contain exact bounded spans, short contexts, offsets, hashes, and lineage only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "COMBINED-BROAD-TEXT-EXTRACTION-4051-PARALLEL-LANES-2026-07-28"
OUTPUT = BASE / "COMBINED-BROAD-SPAN-EVIDENCE-EXTRACTION-3815-PARALLEL-LANES-2026-07-28"
ARTIFACT_ROOT = ROOT / "artifacts/local_extracted_text/combined_broad_text_extraction_4051_2026-07-28"
TASK_ID = "COMBINED-BROAD-SPAN-EVIDENCE-EXTRACTION-3815-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_span_extraction_3815"
EXPECTED = 3815
LANES = {
    "span_lane_001": 954,
    "span_lane_002": 954,
    "span_lane_003": 954,
    "span_lane_004": 953,
}
DELAYS = {
    "span_lane_001": 0,
    "span_lane_002": 480,
    "span_lane_003": 960,
    "span_lane_004": 1440,
}
MIN_ROW_SECONDS = 0.55
MAX_SPANS_PER_SOURCE = 16
MAX_MATCHES_PER_RULE = 2
MAX_SPAN_CHARS = 600
MAX_CONTEXT_SIDE = 250
CLAIM_BOUNDARY = (
    "candidate exact span only; not rated; not ingested; not codified; "
    "not causal; not globally analysis-ready"
)

SPAN_STATUSES = {"span_extracted", "no_span_or_weak", "ambiguous_span", "extraction_error"}
EVIDENCE_FAMILIES = {
    "quantitative_compensation", "qualitative_mechanism",
    "source_navigation_reference", "non_base_compensation",
    "weak_or_not_compensation_relevant",
}
MECHANISMS = (
    "automatic_raise_mechanism", "bargaining_power_signal",
    "market_or_comparability_pressure", "rank_or_specialization_premium",
    "implementation_or_retroactivity_advantage", "fiscal_constraint_signal",
    "parity_or_internal_equity_signal", "non_base_compensation_signal",
    "base_wage_direct_value", "safety_advantage_signal",
    "non_safety_constraint_signal", "gap_narrowing_signal",
    "strike_or_no_strike_constraint", "weak_or_no_claim_support",
    "unknown_or_needs_rating",
)
QUANTITATIVE_LABELS = (
    "hourly_rate", "annual_salary", "salary_schedule", "wage_schedule",
    "step_rank_grade", "percentage_raise", "cola_cpi", "retroactive_pay",
    "effective_date", "contract_period", "pay_band_or_grade",
    "premium_stipend_differential", "classification_compensation_plan",
    "other_quantitative_compensation", "unknown_quantitative_compensation",
)

LINEAGE_FIELDS = (
    "extraction_id", "readiness_id", "source_review_download_id",
    "combined_review_id", "source_candidate_id", "verification_row_id",
    "candidate_origin", "state", "region", "municipality", "county",
    "source_title", "source_locator_or_url", "final_canonical_locator",
    "source_domain", "source_family_hint", "document_type_hint",
    "source_review_priority", "retained_file_sha256",
    "retained_file_path_resolved", "retained_file_type",
    "extracted_text_artifact_path", "extracted_text_size_bytes",
    "extracted_text_sha256", "extraction_status", "artifact_root_lineage",
)
LOCK_FIELDS = (
    "span_queue_id", *LINEAGE_FIELDS[:7], "lane_id", "lane_sequence",
    "source_extraction_lane_id", *LINEAGE_FIELDS[7:],
    "source_review_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness",
    "claim_boundary", "notes",
)
RESULT_FIELDS = LOCK_FIELDS + (
    "span_status", "positive_span_count", "ambiguous_span_count",
    "quantitative_span_count", "qualitative_span_count",
    "source_navigation_span_count", "non_base_span_count",
    "raw_rule_hit_count", "deduplicated_rule_hit_count",
    "no_span_or_weak_reason", "span_extraction_error_type",
    "span_extraction_reason",
)
SPAN_FIELDS = (
    "span_extraction_id", "span_queue_id", "extracted_text_id",
    *LINEAGE_FIELDS[:7], "lane_id", "lane_sequence", *LINEAGE_FIELDS[7:],
    "evidence_family", "mechanism_label", "quantitative_label",
    "span_status", "span_text", "span_start_offset", "span_end_offset",
    "span_sha256", "extraction_rule_family", "extraction_rule_id",
    "rule_hit_terms", "all_evidence_family_hits",
    "all_mechanism_label_hits", "all_quantitative_label_hits",
    "all_extraction_rule_ids", "bounded_context_before",
    "bounded_context_after", "context_total_char_count",
    "duplicate_span_group_id", "source_review_status",
    "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness",
    "claim_boundary", "notes",
)


def make_rules() -> list[dict[str, Any]]:
    specs = [
        ("Q001", r"\b(?:hourly\s+(?:rate|wage)|rate\s+of)\b.{0,50}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "", "hourly_rate"),
        ("Q002", r"\$[\d,]+(?:\.\d{1,2})?\s*(?:per\s+hour|/\s*hour|hourly)\b", "quantitative_compensation", "", "hourly_rate"),
        ("Q003", r"\b(?:annual\s+salary|salary\s+per\s+annum)\b.{0,60}?\$[\d,]+", "quantitative_compensation", "", "annual_salary"),
        ("Q004", r"\b(?:salary\s+schedule|schedule\s+of\s+salaries)\b", "quantitative_compensation", "", "salary_schedule"),
        ("Q005", r"\b(?:wage\s+schedule|schedule\s+of\s+wages)\b", "quantitative_compensation", "", "wage_schedule"),
        ("Q006", r"\b(?:step|rank|grade)\s+[A-Z0-9-]+\b.{0,60}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "", "step_rank_grade"),
        ("Q007", r"\b\d{1,2}(?:\.\d+)?\s*%\s*(?:wage\s+|salary\s+|pay\s+)?(?:increase|raise|adjustment)", "quantitative_compensation", "", "percentage_raise"),
        ("Q008", r"\b(?:increase|raise|adjustment)\s+of\s+\d{1,2}(?:\.\d+)?\s*%", "quantitative_compensation", "", "percentage_raise"),
        ("Q009", r"\b(?:COLA|cost[- ]of[- ]living|consumer\s+price\s+index|CPI)\b", "quantitative_compensation", "", "cola_cpi"),
        ("Q010", r"\b(?:retroactive\s+pay|retroactivity|paid\s+retroactively|retroactive\s+to)\b", "quantitative_compensation", "", "retroactive_pay"),
        ("Q011", r"\beffective\s+(?:on\s+)?(?:date\s+of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2}[/-]\d{1,2}[/-])", "quantitative_compensation", "", "effective_date"),
        ("Q012", r"\b(?:term|period)\s+of\s+(?:this\s+)?(?:agreement|contract)\b", "quantitative_compensation", "", "contract_period"),
        ("Q013", r"\b(?:pay\s+band|pay\s+grade|salary\s+grade|compensation\s+grade)\b", "quantitative_compensation", "", "pay_band_or_grade"),
        ("Q014", r"\b(?:classification\s+plan|compensation\s+plan|classification\s+and\s+compensation)\b", "quantitative_compensation", "", "classification_compensation_plan"),
        ("N001", r"\b(?:longevity\s+pay|premium\s+pay|shift\s+differential|stipend|hazard\s+pay|specialty\s+pay)\b", "non_base_compensation", "non_base_compensation_signal", "premium_stipend_differential"),
        ("M001", r"\b(?:automatic(?:ally)?\s+(?:increase|raise|adjustment)|step\s+advancement|shall\s+receive\s+an?\s+increase)\b", "qualitative_mechanism", "automatic_raise_mechanism", ""),
        ("M002", r"\b(?:collective\s+bargaining|union\s+proposal|impasse|interest\s+arbitration|negotiated\s+agreement)\b", "qualitative_mechanism", "bargaining_power_signal", ""),
        ("M003", r"\b(?:comparable\s+(?:municipalities|jurisdictions|communities)|peer\s+(?:cities|jurisdictions)|market\s+(?:rate|adjustment|comparison)|comparability)\b", "qualitative_mechanism", "market_or_comparability_pressure", ""),
        ("M004", r"\b(?:rank\s+differential|special(?:ty|ization)\s+pay|detective\s+premium|command\s+pay)\b", "qualitative_mechanism", "rank_or_specialization_premium", ""),
        ("M005", r"\b(?:retroactive\s+to|implementation\s+date|effective\s+retroactively|make[- ]whole)\b", "qualitative_mechanism", "implementation_or_retroactivity_advantage", ""),
        ("M006", r"\b(?:ability\s+to\s+pay|fiscal\s+constraint|budget\s+deficit|revenue\s+constraint|tax\s+cap|financial\s+emergency)\b", "qualitative_mechanism", "fiscal_constraint_signal", ""),
        ("M007", r"\b(?:internal\s+equity|pay\s+parity|wage\s+parity|me[- ]too\s+clause|comparable\s+classifications)\b", "qualitative_mechanism", "parity_or_internal_equity_signal", ""),
        ("M008", r"\b(?:base\s+wage|base\s+salary|regular\s+hourly\s+rate)\b", "qualitative_mechanism", "base_wage_direct_value", ""),
        ("M009", r"\b(?:police|firefighters?|public\s+safety)\b.{0,80}\b(?:advantage|higher|above|premium)\b", "qualitative_mechanism", "safety_advantage_signal", ""),
        ("M010", r"\b(?:civilian|non[- ]safety|general\s+employees?)\b.{0,80}\b(?:freeze|cap|constraint|below)\b", "qualitative_mechanism", "non_safety_constraint_signal", ""),
        ("M011", r"\b(?:pay\s+compression|wage\s+compression|catch[- ]up\s+increase|narrow(?:ing)?\s+the\s+gap)\b", "qualitative_mechanism", "gap_narrowing_signal", ""),
        ("M012", r"\b(?:no[- ]strike|no\s+strike|work\s+stoppage|shall\s+not\s+strike)\b", "qualitative_mechanism", "strike_or_no_strike_constraint", ""),
        ("R001", r"\b(?:appendix|exhibit|attachment)\s+[A-Z0-9-]+\b.{0,80}\b(?:salary|wage|pay|compensation)\b", "source_navigation_reference", "unknown_or_needs_rating", ""),
        ("R002", r"\b(?:see|refer\s+to|attached)\s+(?:the\s+)?(?:salary|wage|pay|compensation)\s+(?:schedule|plan|ordinance|appendix|exhibit)\b", "source_navigation_reference", "unknown_or_needs_rating", ""),
        ("R003", r"\b(?:salary|wage|pay)\s+(?:schedule|plan)\s+(?:attached|below|following|appendix|exhibit)\b", "source_navigation_reference", "unknown_or_needs_rating", ""),
    ]
    return [{
        "id": rule_id, "pattern": re.compile(pattern, re.IGNORECASE | re.DOTALL),
        "family": family, "mechanism": mechanism,
        "quantitative": quantitative,
        "rule_family": rule_id[0],
    } for rule_id, pattern, family, mechanism, quantitative in specs]


RULES = make_rules()
GENERIC_AMBIGUOUS = re.compile(
    r"\b(?:salary|wages?|pay|compensation|labor|budget|contract|agreement)\b",
    re.IGNORECASE,
)


def utc_now() -> str:
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
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
    temporary.replace(path)


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def assert_storage_policy() -> None:
    probe = ARTIFACT_ROOT / ".span-ignore-probe"
    if subprocess.run(["git", "check-ignore", "-q", rel(probe)], cwd=ROOT).returncode:
        raise RuntimeError("full-text artifact root is not ignored")
    if git_output("ls-files", "artifacts/local_extracted_text"):
        raise RuntimeError("full extracted text is tracked")
    if git_output("ls-files", "artifacts/local_retained_sources"):
        raise RuntimeError("retained source binaries are tracked")


def queue_id(extraction_id: str) -> str:
    return "CBSPQ-20260728-" + hashlib.sha256(extraction_id.encode()).hexdigest()[:20]


def prepare() -> None:
    if OUTPUT.exists():
        raise RuntimeError("output directory already exists; fail closed instead of overwriting")
    required = [
        "combined_broad_text_extraction_4051_decision.json",
        "combined_broad_text_extraction_4051_summary.md",
        "combined_broad_text_extraction_4051_results.csv",
        "combined_broad_text_extraction_4051_results_summary.json",
        "combined_broad_text_extraction_4051_extracted_ok.csv",
        "combined_broad_text_extraction_4051_extracted_ok_summary.json",
        "combined_broad_text_extraction_4051_extracted_text_manifest.csv",
        "combined_broad_text_extraction_4051_extracted_text_manifest_summary.json",
        "combined_broad_text_extraction_4051_extracted_text_hash_manifest.csv",
        "combined_broad_text_extraction_4051_extracted_text_artifact_root.json",
        "combined_broad_text_extraction_4051_no_tracked_text_artifacts_validation.json",
        "combined_broad_text_extraction_4051_quality_summary.json",
        "combined_broad_text_extraction_4051_dashboard_update_summary.json",
        "combined_broad_text_extraction_4051_validation_2026-07-28.md",
    ]
    missing = [name for name in required if not (INPUT / name).is_file()]
    if missing:
        raise RuntimeError(f"required non-derivable artifacts missing: {missing}")
    decision = read_json(INPUT / "combined_broad_text_extraction_4051_decision.json")
    summary = read_json(INPUT / "combined_broad_text_extraction_4051_results_summary.json")
    if decision.get("decision") != "combined_broad_text_extraction_4051_completed_span_extraction_ready":
        raise RuntimeError("predecessor decision does not authorize span extraction")
    if summary.get("extracted_ok_count") != EXPECTED:
        raise RuntimeError("predecessor extracted-ok summary does not reconcile to 3,815")
    assert_storage_policy()
    extracted_ok = read_csv(INPUT / "combined_broad_text_extraction_4051_extracted_ok.csv")
    hashes = read_csv(INPUT / "combined_broad_text_extraction_4051_extracted_text_hash_manifest.csv")
    hash_map = {row["extraction_id"]: row for row in hashes}
    if len(extracted_ok) != EXPECTED or len({row["extraction_id"] for row in extracted_ok}) != EXPECTED:
        raise RuntimeError("extracted-ok ledger count or uniqueness failure")
    if any(row["extraction_status"] != "extracted_ok" for row in extracted_ok):
        raise RuntimeError("non-extracted-ok row entered span queue")
    OUTPUT.mkdir(parents=True)
    integrity: list[dict[str, Any]] = []
    locked: list[dict[str, Any]] = []
    boundaries = (954, 1908, 2862, 3815)
    for index, row in enumerate(extracted_ok, 1):
        manifest = hash_map.get(row["extraction_id"])
        if not manifest:
            raise RuntimeError(f"missing text hash manifest row: {row['extraction_id']}")
        path = ROOT / row["extracted_text_artifact_path"]
        expected_size = int(row["extracted_text_size_bytes"])
        expected_hash = row["extracted_text_sha256"]
        if not path.is_file() or path.stat().st_size != expected_size:
            raise RuntimeError(f"text artifact path/size failure: {row['extraction_id']}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash or manifest["extracted_text_sha256"] != expected_hash:
            raise RuntimeError(f"text artifact hash failure: {row['extraction_id']}")
        lane = next(name for name, upper in zip(LANES, boundaries) if index <= upper)
        previous = sum(LANES[name] for name in LANES if name < lane)
        lock = {
            "span_queue_id": queue_id(row["extraction_id"]),
            **{field: row.get(field, "") for field in LINEAGE_FIELDS},
            "lane_id": lane,
            "lane_sequence": index - previous,
            "source_extraction_lane_id": row["lane_id"],
            "source_review_status": "retained",
            "rating_status": "not_rated",
            "ingestion_status": "not_ingested",
            "codification_status": "not_codified",
            "causal_status": "not_causal_evidence",
            "global_analysis_readiness": "false",
            "claim_boundary": CLAIM_BOUNDARY,
            "notes": "Locked deterministic span candidate source; no rating or analytic judgment.",
        }
        locked.append(lock)
        integrity.append({
            "span_queue_id": lock["span_queue_id"],
            "extraction_id": row["extraction_id"],
            "extracted_text_artifact_path": row["extracted_text_artifact_path"],
            "expected_size_bytes": expected_size,
            "actual_size_bytes": path.stat().st_size,
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "artifact_root_ignored": "true",
            "tracked_in_git": "false",
            "integrity_status": "integrity_pass",
        })
    if len(locked) != EXPECTED or len({row["span_queue_id"] for row in locked}) != EXPECTED:
        raise RuntimeError("locked queue reconciliation failure")
    lock_digest = sha256_text("\n".join(row["span_queue_id"] for row in locked))
    write_csv(OUTPUT / f"{PREFIX}_text_artifact_integrity_preflight.csv", integrity, integrity[0].keys())
    write_json(OUTPUT / f"{PREFIX}_text_artifact_integrity_preflight_summary.json", {
        "checked_count": EXPECTED, "integrity_pass_count": EXPECTED,
        "missing_count": 0, "size_mismatch_count": 0, "hash_mismatch_count": 0,
        "tracked_full_text_count": 0, "tracked_retained_binary_count": 0,
    })
    write_csv(OUTPUT / f"{PREFIX}_locked_queue.csv", locked, LOCK_FIELDS)
    write_json(OUTPUT / f"{PREFIX}_locked_queue_summary.json", {
        "queue_count": EXPECTED, "lane_counts": LANES,
        "queue_identity_sha256": lock_digest, "only_extracted_ok": True,
    })
    write_json(OUTPUT / f"{PREFIX}_lock.json", {
        "task_id": TASK_ID, "locked_at": utc_now(), "queue_count": EXPECTED,
        "lane_counts": LANES, "queue_identity_sha256": lock_digest,
        "predecessor_ledgers_immutable": True,
    })
    offset = 0
    for lane, count in LANES.items():
        part = locked[offset:offset + count]
        offset += count
        number = lane[-3:]
        write_csv(OUTPUT / f"combined_broad_span_extraction_lane_{number}_locked_queue.csv", part, LOCK_FIELDS)
        write_json(OUTPUT / f"combined_broad_span_extraction_lane_{number}_locked_queue_summary.json", {
            "lane_id": lane, "queue_count": count, "sequence_min": 1,
            "sequence_max": count, "standard_delay_seconds": DELAYS[lane],
        })
        write_json(OUTPUT / f"combined_broad_span_extraction_lane_{number}_lock.json", {
            "lane_id": lane, "queue_count": count,
            "queue_identity_sha256": sha256_text("\n".join(row["span_queue_id"] for row in part)),
            "lane_output_isolated": True,
        })
        (OUTPUT / "lanes" / lane).mkdir(parents=True)
    preflight = {
        "preflight_passed": True, "predecessor_decision_confirmed": True,
        "extracted_ok_count": EXPECTED, "artifact_hashes_valid": True,
        "artifact_root_ignored": True, "tracked_full_text_count": 0,
        "tracked_retained_binary_count": 0, "queue_count": EXPECTED,
        "lane_counts": LANES, "master_equals_lane_union": True,
        "rows_outside_extracted_ok": 0, "lane_isolation": True,
        "no_source_review_download_rerun": True, "no_redownload": True,
        "no_readiness_rerun": True, "no_text_extraction_rerun": True,
        "no_ocr_rendering_rating_model_ingestion_or_analysis": True,
        "bounded_context_max_each_side": MAX_CONTEXT_SIDE,
        "maximum_spans_per_source": MAX_SPANS_PER_SOURCE,
        "dashboard_map_contract": "total_scout_coverage_only",
        "global_analysis_readiness": False, "secrets_saved": False,
        "rollback_safe": True,
    }
    write_json(OUTPUT / f"{PREFIX}_preflight_checks.json", preflight)
    write_text(OUTPUT / f"{PREFIX}_preflight_report.md",
        "# Combined broad span-extraction preflight\n\n"
        "PASS. Exactly 3,815 extracted-ok text artifacts passed local path, size, and SHA-256 "
        "validation and were locked into four isolated queues of 954 / 954 / 954 / 953. "
        "Full text remains ignored and untracked. The run is deterministic span extraction only; "
        "rating, models, ingestion, codification, normalization, statistical analysis, and causal "
        "or prevalence claims are prohibited.")
    print(json.dumps({"status": "preflight_passed", "queue": EXPECTED, "lanes": LANES}))


def span_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    lower = max(0, start - 220)
    upper = min(len(text), end + 320)
    left_candidates = [text.rfind(marker, lower, start) for marker in ("\n", ". ", "; ")]
    left = max(left_candidates)
    span_start = left + 1 if left >= lower else lower
    right_candidates = []
    for marker in ("\n", ". ", "; "):
        found = text.find(marker, end, upper)
        if found >= 0:
            right_candidates.append(found + (1 if marker == "\n" else len(marker)))
    span_end = min(right_candidates) if right_candidates else upper
    if span_end - span_start > MAX_SPAN_CHARS:
        span_start = max(0, start - 120)
        span_end = min(len(text), span_start + MAX_SPAN_CHARS)
        if span_end < end:
            span_end = end
            span_start = max(0, span_end - MAX_SPAN_CHARS)
    return span_start, span_end


def hit_payload(rule: dict[str, Any], match: re.Match[str], text: str) -> dict[str, Any]:
    start, end = span_bounds(text, match.start(), match.end())
    term = text[match.start():match.end()]
    return {
        "start": start, "end": end, "family": rule["family"],
        "mechanism": rule["mechanism"], "quantitative": rule["quantitative"],
        "rule_id": rule["id"], "rule_family": rule["rule_family"],
        "term": term,
    }


def canonical_spans(text: str) -> tuple[list[dict[str, Any]], int, int]:
    hits: list[dict[str, Any]] = []
    for rule in RULES:
        for match_index, match in enumerate(rule["pattern"].finditer(text)):
            if match_index >= MAX_MATCHES_PER_RULE:
                break
            hits.append(hit_payload(rule, match, text))
    raw_count = len(hits)
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        grouped[(hit["start"], hit["end"])].append(hit)
    canonical: list[dict[str, Any]] = []
    family_priority = {
        "quantitative_compensation": 0, "non_base_compensation": 1,
        "qualitative_mechanism": 2, "source_navigation_reference": 3,
    }
    for (start, end), same in sorted(grouped.items()):
        primary = min(same, key=lambda item: (
            family_priority[item["family"]], item["rule_id"]
        ))
        canonical.append({
            "start": start, "end": end,
            "family": primary["family"],
            "mechanism": primary["mechanism"] or "unknown_or_needs_rating",
            "quantitative": primary["quantitative"] or "unknown_quantitative_compensation",
            "rule_family": primary["rule_family"],
            "rule_id": primary["rule_id"],
            "terms": sorted({item["term"] for item in same}),
            "families": sorted({item["family"] for item in same}),
            "mechanisms": sorted({item["mechanism"] for item in same if item["mechanism"]}),
            "quantitative_labels": sorted({item["quantitative"] for item in same if item["quantitative"]}),
            "rule_ids": sorted({item["rule_id"] for item in same}),
        })
    if len(canonical) > MAX_SPANS_PER_SOURCE:
        canonical = sorted(
            canonical,
            key=lambda item: (
                family_priority[item["family"]], item["rule_id"], item["start"]
            ),
        )[:MAX_SPANS_PER_SOURCE]
        canonical.sort(key=lambda item: item["start"])
    return canonical, raw_count, raw_count - len(grouped)


def span_record(row: dict[str, str], text: str, item: dict[str, Any], status: str) -> dict[str, Any]:
    start, end = item["start"], item["end"]
    span = text[start:end]
    span_hash = sha256_text(span)
    before = text[max(0, start - MAX_CONTEXT_SIDE):start]
    after = text[end:min(len(text), end + MAX_CONTEXT_SIDE)]
    identity = sha256_text(
        f"{row['extraction_id']}|{start}|{end}|{span_hash}"
    )
    return {
        "span_extraction_id": "CBSPAN-20260728-" + identity[:24],
        "span_queue_id": row["span_queue_id"],
        "extracted_text_id": row["extraction_id"],
        **{field: row.get(field, "") for field in LINEAGE_FIELDS[:7]},
        "lane_id": row["lane_id"], "lane_sequence": row["lane_sequence"],
        **{field: row.get(field, "") for field in LINEAGE_FIELDS[7:]},
        "evidence_family": item["family"],
        "mechanism_label": item["mechanism"],
        "quantitative_label": item["quantitative"],
        "span_status": status,
        "span_text": span, "span_start_offset": start, "span_end_offset": end,
        "span_sha256": span_hash,
        "extraction_rule_family": item["rule_family"],
        "extraction_rule_id": item["rule_id"],
        "rule_hit_terms": json.dumps(item["terms"], ensure_ascii=False),
        "all_evidence_family_hits": json.dumps(item["families"]),
        "all_mechanism_label_hits": json.dumps(item["mechanisms"]),
        "all_quantitative_label_hits": json.dumps(item["quantitative_labels"]),
        "all_extraction_rule_ids": json.dumps(item["rule_ids"]),
        "bounded_context_before": before, "bounded_context_after": after,
        "context_total_char_count": len(before) + len(after),
        "duplicate_span_group_id": "CBDUP-" + sha256_text(
            f"{row['extraction_id']}|{start}|{end}|{span_hash}"
        )[:20],
        "source_review_status": "retained", "extraction_status": "extracted_ok",
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified",
        "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false",
        "claim_boundary": CLAIM_BOUNDARY,
        "notes": "Deterministic exact candidate span; label requires later rating.",
    }


def ambiguous_record(row: dict[str, str], text: str) -> dict[str, Any] | None:
    match = GENERIC_AMBIGUOUS.search(text)
    if not match:
        return None
    start, end = span_bounds(text, match.start(), match.end())
    item = {
        "start": start, "end": end,
        "family": "weak_or_not_compensation_relevant",
        "mechanism": "weak_or_no_claim_support",
        "quantitative": "unknown_quantitative_compensation",
        "rule_family": "W", "rule_id": "W001",
        "terms": [text[match.start():match.end()]],
        "families": ["weak_or_not_compensation_relevant"],
        "mechanisms": ["weak_or_no_claim_support"],
        "quantitative_labels": ["unknown_quantitative_compensation"],
        "rule_ids": ["W001"],
    }
    return span_record(row, text, item, "ambiguous_span")


def bounded_delay(seconds: int) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        time.sleep(min(30, max(0, deadline - time.monotonic())))


def lane_paths(lane: str) -> tuple[Path, Path]:
    number = lane[-3:]
    return (
        OUTPUT / f"combined_broad_span_extraction_lane_{number}_locked_queue.csv",
        OUTPUT / "lanes" / lane,
    )


def run_lane(lane: str, delay_seconds: int) -> None:
    if delay_seconds < 0 or delay_seconds > DELAYS[lane]:
        raise RuntimeError("resume delay exceeds standard lane delay")
    bounded_delay(delay_seconds)
    queue_path, directory = lane_paths(lane)
    queue = read_csv(queue_path)
    if len(queue) != LANES[lane]:
        raise RuntimeError("lane queue count mismatch")
    number = lane[-3:]
    results_path = directory / f"lane_{number}_span_extraction_results.csv"
    positives_path = directory / f"lane_{number}_positive_spans.csv"
    ambiguous_path = directory / f"lane_{number}_ambiguous_spans.csv"
    prior_results = read_csv(results_path) if results_path.exists() else []
    completed_ids = {row["span_queue_id"] for row in prior_results}
    queue_ids = {row["span_queue_id"] for row in queue}
    if not completed_ids.issubset(queue_ids):
        raise RuntimeError("resume results contain rows outside lane lock")
    for path in (positives_path, ambiguous_path):
        if path.exists():
            existing = read_csv(path)
            write_csv(path, [row for row in existing if row["span_queue_id"] in completed_ids], SPAN_FIELDS)
    checkpoint_path = directory / f"lane_{number}_checkpoint.json"
    old_checkpoint = read_json(checkpoint_path) if checkpoint_path.exists() else {}
    started_at = old_checkpoint.get("started_at") or utc_now()
    write_json(checkpoint_path, {
        "lane_id": lane, "status": "running", "started_at": started_at,
        "completed_count": len(prior_results), "queue_count": len(queue),
        "standard_delay_seconds": DELAYS[lane],
        "resume_relative_delay_seconds": delay_seconds,
    })
    consecutive_errors = 0
    for row in queue:
        if row["span_queue_id"] in completed_ids:
            continue
        row_started = time.monotonic()
        result = {field: row.get(field, "") for field in LOCK_FIELDS}
        positives: list[dict[str, Any]] = []
        ambiguities: list[dict[str, Any]] = []
        try:
            path = ROOT / row["extracted_text_artifact_path"]
            if not path.is_file() or path.stat().st_size != int(row["extracted_text_size_bytes"]):
                raise RuntimeError("text artifact path/size mismatch")
            if sha256_file(path) != row["extracted_text_sha256"]:
                raise RuntimeError("text artifact SHA-256 mismatch")
            text_value = path.read_text(encoding="utf-8")
            canonical, raw_hits, deduped_hits = canonical_spans(text_value)
            positives = [
                span_record(row, text_value, item, "span_extracted")
                for item in canonical
            ]
            if positives:
                status = "span_extracted"
                reason = "one or more deterministic exact candidate spans found"
                no_span_reason = ""
            else:
                weak = ambiguous_record(row, text_value)
                if weak:
                    ambiguities = [weak]
                    status = "ambiguous_span"
                    reason = "generic compensation/labor term found without a positive deterministic rule"
                    no_span_reason = "generic_term_without_rule_specific_compensation_or_mechanism_context"
                else:
                    status = "no_span_or_weak"
                    reason = "no deterministic compensation, mechanism, or navigation rule matched"
                    no_span_reason = "no_bounded_rule_match"
            counts = Counter(item["evidence_family"] for item in positives)
            result.update({
                "span_status": status,
                "positive_span_count": len(positives),
                "ambiguous_span_count": len(ambiguities),
                "quantitative_span_count": counts["quantitative_compensation"],
                "qualitative_span_count": counts["qualitative_mechanism"],
                "source_navigation_span_count": counts["source_navigation_reference"],
                "non_base_span_count": counts["non_base_compensation"],
                "raw_rule_hit_count": raw_hits,
                "deduplicated_rule_hit_count": deduped_hits,
                "no_span_or_weak_reason": no_span_reason,
                "span_extraction_error_type": "",
                "span_extraction_reason": reason,
            })
            consecutive_errors = 0
        except Exception as exc:
            result.update({
                "span_status": "extraction_error", "positive_span_count": 0,
                "ambiguous_span_count": 0, "quantitative_span_count": 0,
                "qualitative_span_count": 0, "source_navigation_span_count": 0,
                "non_base_span_count": 0, "raw_rule_hit_count": 0,
                "deduplicated_rule_hit_count": 0,
                "no_span_or_weak_reason": "",
                "span_extraction_error_type": type(exc).__name__,
                "span_extraction_reason": str(exc)[:500],
            })
            consecutive_errors += 1
        for span in positives:
            append_csv(positives_path, span, SPAN_FIELDS)
        for span in ambiguities:
            append_csv(ambiguous_path, span, SPAN_FIELDS)
        append_csv(results_path, result, RESULT_FIELDS)
        prior_results.append(result)
        write_json(checkpoint_path, {
            "lane_id": lane, "status": "running", "started_at": started_at,
            "updated_at": utc_now(), "completed_count": len(prior_results),
            "queue_count": len(queue), "last_span_queue_id": row["span_queue_id"],
            "standard_delay_seconds": DELAYS[lane],
            "resume_relative_delay_seconds": delay_seconds,
        })
        remaining = MIN_ROW_SECONDS - (time.monotonic() - row_started)
        if remaining > 0:
            time.sleep(remaining)
        if consecutive_errors >= 25:
            break
    complete = len(prior_results) == len(queue)
    positive_rows = read_csv(positives_path) if positives_path.exists() else []
    ambiguous_rows = read_csv(ambiguous_path) if ambiguous_path.exists() else []
    errors = [row for row in prior_results if row["span_status"] == "extraction_error"]
    no_spans = [row for row in prior_results if row["span_status"] == "no_span_or_weak"]
    write_csv(directory / f"lane_{number}_positive_spans.csv", positive_rows, SPAN_FIELDS)
    write_csv(directory / f"lane_{number}_ambiguous_spans.csv", ambiguous_rows, SPAN_FIELDS)
    write_csv(directory / f"lane_{number}_no_span_or_weak.csv", no_spans, RESULT_FIELDS)
    write_csv(directory / f"lane_{number}_errors.csv", errors, RESULT_FIELDS)
    statuses = Counter(row["span_status"] for row in prior_results)
    summary = {
        "lane_id": lane, "queue_count": len(queue),
        "completed_count": len(prior_results), "complete": complete,
        "source_status_counts": dict(sorted(statuses.items())),
        "positive_exact_span_count": len(positive_rows),
        "ambiguous_span_record_count": len(ambiguous_rows),
        "started_at": started_at, "ended_at": utc_now(),
        "standard_delay_seconds": DELAYS[lane],
        "resume_relative_delay_seconds": delay_seconds,
    }
    write_json(directory / f"lane_{number}_span_extraction_results_summary.json", summary)
    write_json(directory / f"lane_{number}_resume_state.json", {
        "lane_id": lane, "resume_required": not complete,
        "completed_count": len(prior_results),
        "remaining_count": len(queue) - len(prior_results),
        "next_lane_sequence": len(prior_results) + 1 if not complete else None,
    })
    write_json(checkpoint_path, {
        **summary, "status": "completed" if complete else "partial_stop",
    })
    if not complete:
        raise RuntimeError(f"{lane} partial stop after repeated errors")
    print(json.dumps(summary))


def launch(resume: bool = False) -> None:
    log_dir = ROOT / "tmp/combined_broad_span_extraction_3815_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    delays = dict(DELAYS)
    if resume:
        checkpoint = read_json(OUTPUT / "lanes/span_lane_001/lane_001_checkpoint.json")
        base = datetime.fromisoformat(checkpoint["started_at"].replace("Z", "+00:00")).timestamp()
        current = time.time()
        delays = {
            lane: max(0, int(base + DELAYS[lane] - current))
            for lane in LANES
        }
    processes: list[tuple[str, subprocess.Popen[bytes], Any]] = []
    for lane in LANES:
        handle = (log_dir / f"{lane}.log").open("wb")
        proc = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), str(Path(__file__).resolve()),
             "--lane", lane, "--stagger-seconds", str(delays[lane])],
            cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
        )
        processes.append((lane, proc, handle))
    failures = []
    for lane, proc, handle in processes:
        code = proc.wait()
        handle.close()
        if code:
            failures.append((lane, code))
    if failures:
        raise RuntimeError(f"span lane failures: {failures}")
    print(json.dumps({
        "status": "all_span_lanes_completed", "lanes": list(LANES),
        "resume_launch": resume, "relative_delays_used": delays,
    }))


def coordinate() -> None:
    from span_extraction_3815_coordinator import coordinate as run_coordinator
    run_coordinator()


def validate_complete() -> None:
    from span_extraction_3815_coordinator import validate_complete as run_validation
    run_validation()


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--lane", choices=tuple(LANES))
    action.add_argument("--launch", action="store_true")
    action.add_argument("--resume-launch", action="store_true")
    action.add_argument("--coordinate", action="store_true")
    action.add_argument("--validate", action="store_true")
    parser.add_argument("--stagger-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.stagger_seconds)
    elif args.launch:
        launch()
    elif args.resume_launch:
        launch(resume=True)
    elif args.coordinate:
        coordinate()
    else:
        validate_complete()


if __name__ == "__main__":
    main()
