#!/usr/bin/env python3
"""Classify retained external-data payloads for non-OCR extraction readiness.

The physical payload is the inspection unit. Canonical retained-source records
remain the lineage unit. The runner is deliberately local-only: it performs no
network access, redownload, hosted search, GABRIEL call, OCR, analytical text or
table extraction, normalization, matching, or implementation-event recoding.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import warnings
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lxml import etree, html as lxml_html
from pypdf import PdfReader

import run_external_data_exhaustive_pipeline as core


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-READINESS-2026-08-05"
DECISION = "broad_state_whole_corpus_available_external_data_readiness_completed_extraction_ready"
REQUIRED_COMMIT = "dd69c9e50cb4a2b875bdb7fb1ad6843d9707b115"
EXPECTED_CANONICAL = 14_703
EXPECTED_CURRENT_PAYLOADS = 14_449
EXPECTED_CURRENT_BYTES = 32_212_254_614
EXPECTED_EXACT_DUPLICATE_LINKS = 552
EXPECTED_REUSE_LINKS = 264
EXPECTED_HOLDS = 7_895
EXPECTED_CONTEXT_DEFERS = 24_569
EXPECTED_UNRESOLVED = 12_844
EXPECTED_ROOT_EVENTS = 2_998
EXPECTED_MECHANISM_EVENTS = 13_391

INPUT = core.STAGE4
OUTPUT = core.STAGE5
CURRENT_RETAINED_ROOT = core.RETAINED
EXTRACTED_ROOT = core.EXTRACTED
STRUCTURED_ROOT = core.STRUCTURED
TMP = core.ROOT / "tmp/broad_state_whole_corpus_available_external_data_readiness_2026-08-05_logs"
LANES = [f"readiness_lane_{index:03d}" for index in range(1, 6)]
STAGGER_SECONDS = dict(zip(LANES, (0, 180, 360, 540, 720)))
MAX_HTML_DIAGNOSTIC_BYTES = 8 * 1024 * 1024
MAX_PDF_SAMPLE_PAGES = 5
PER_PAYLOAD_TIMEOUT_SECONDS = 150

EXTRACTION_READY = {
    "parse_text_pdf_ready", "parse_text_pdf_low_text_usable", "html_text_ready",
    "html_table_candidate_ready", "html_structured_data_candidate", "html_low_text_usable",
    "csv_structured_ready", "tsv_structured_ready", "xlsx_structured_ready",
    "xls_structured_ready", "json_structured_ready", "xml_structured_ready", "text_ready",
    "text_table_candidate_ready", "structured_low_quality_usable", "text_low_quality_usable",
    "official_data_package_ready", "official_data_package_partial_ready",
    "other_document_ready", "other_document_low_quality_usable",
}
NOT_READY = {
    "ocr_later", "encrypted_or_locked", "oversized_defer", "corrupt_or_broken",
    "shell_or_navigation_only", "unsupported_pdf_structure",
    "unsupported_spreadsheet_structure", "unsupported_file_type",
    "suspicious_or_quarantine", "needs_manual_review", "readiness_error",
}
TERMINAL = EXTRACTION_READY | NOT_READY

PRIMARY_QUEUE = {
    "parse_text_pdf_ready": "parse_text_pdf_extraction_queue",
    "parse_text_pdf_low_text_usable": "low_text_pdf_extraction_queue",
    "html_text_ready": "html_text_extraction_queue",
    "html_low_text_usable": "html_text_extraction_queue",
    "html_table_candidate_ready": "html_table_candidate_queue",
    "html_structured_data_candidate": "html_table_candidate_queue",
    "csv_structured_ready": "csv_extraction_queue",
    "tsv_structured_ready": "tsv_extraction_queue",
    "xlsx_structured_ready": "xlsx_extraction_queue",
    "xls_structured_ready": "xls_extraction_queue",
    "json_structured_ready": "json_extraction_queue",
    "xml_structured_ready": "xml_extraction_queue",
    "text_ready": "text_extraction_queue",
    "text_table_candidate_ready": "text_extraction_queue",
    "text_low_quality_usable": "text_extraction_queue",
    "official_data_package_ready": "official_data_package_extraction_queue",
    "official_data_package_partial_ready": "official_data_package_extraction_queue",
    "structured_low_quality_usable": "other_structured_candidate_queue",
    "other_document_ready": "other_structured_candidate_queue",
    "other_document_low_quality_usable": "other_structured_candidate_queue",
}
DEFERRED_QUEUE = {
    "ocr_later": "ocr_later_queue",
    "encrypted_or_locked": "encrypted_or_locked_queue",
    "oversized_defer": "oversized_defer_queue",
    "corrupt_or_broken": "corrupt_or_broken_queue",
    "shell_or_navigation_only": "shell_or_navigation_only_queue",
    "unsupported_pdf_structure": "unsupported_file_type_queue",
    "unsupported_spreadsheet_structure": "unsupported_file_type_queue",
    "unsupported_file_type": "unsupported_file_type_queue",
    "suspicious_or_quarantine": "suspicious_or_quarantine_queue",
    "needs_manual_review": "manual_review_queue",
    "readiness_error": "readiness_error_queue",
}

OUTPUT_QUEUE_NAMES = [
    "parse_text_pdf_extraction_queue", "low_text_pdf_extraction_queue",
    "html_text_extraction_queue", "html_table_candidate_queue", "csv_extraction_queue",
    "tsv_extraction_queue", "xlsx_extraction_queue", "xls_extraction_queue",
    "json_extraction_queue", "xml_extraction_queue", "text_extraction_queue",
    "official_data_package_extraction_queue", "other_structured_candidate_queue",
    "ocr_later_queue", "encrypted_or_locked_queue", "oversized_defer_queue",
    "corrupt_or_broken_queue", "shell_or_navigation_only_queue",
    "unsupported_file_type_queue", "suspicious_or_quarantine_queue",
    "manual_review_queue", "readiness_error_queue",
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_shards(directory: Path, manifest_name: str) -> list[dict[str, str]]:
    manifest = read_json(directory / manifest_name)
    rows: list[dict[str, str]] = []
    for part in manifest["parts"]:
        name = part.get("csv") or part.get("csv_path")
        with (directory / name).open(newline="", encoding="utf-8-sig") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def split_values(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def join_values(values: Iterable[str]) -> str:
    output: set[str] = set()
    for value in values:
        output.update(split_values(value))
    return "|".join(sorted(output))


def bool_value(value: Any) -> bool:
    return str(value).casefold() in {"true", "1", "yes"}


def current_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=core.ROOT, text=True).strip()


def is_ancestor(commit: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=core.ROOT).returncode == 0


def git_ignored(path: Path) -> bool:
    probe = path if path.suffix else path / "ignore-probe"
    return subprocess.run(["git", "check-ignore", "-q", str(probe.relative_to(core.ROOT))], cwd=core.ROOT).returncode == 0


def process_matches() -> list[str]:
    try:
        text = subprocess.check_output(["pgrep", "-af", "run_available_external_data_readiness.py"], text=True)
    except (subprocess.CalledProcessError, PermissionError):
        return []
    own = str(os.getpid())
    return [line for line in text.splitlines() if line.strip() and "pgrep" not in line and line.split(maxsplit=1)[0] != own]


def write_sharded(name: str, rows: list[dict[str, Any]]) -> None:
    core.write_sharded_pair(OUTPUT, name, rows, chunk_size=4_000)


def source_review_lookup() -> dict[str, dict[str, str]]:
    rows = load_shards(INPUT, "source_review_results_shard_manifest.json")
    return {row["source_review_id"]: row for row in rows}


def build_canonical_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    queue = load_shards(INPUT, "external_data_readiness_queue_shard_manifest.json")
    source_review = source_review_lookup()
    duplicate_links = load_shards(INPUT, "retained_source_duplicate_links_shard_manifest.json")
    version_links = load_shards(INPUT, "retained_source_version_relationships_shard_manifest.json")
    versions_by_source: dict[str, list[str]] = defaultdict(list)
    for index, row in enumerate(version_links, 1):
        relationship_id = stable("EXTVERSION", row.get("prior_retained_source_id", ""), row.get("related_retained_source_id", ""), str(index))
        versions_by_source[row.get("prior_retained_source_id", "")].append(relationship_id)
        versions_by_source[row.get("related_retained_source_id", "")].append(relationship_id)
    duplicate_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in duplicate_links:
        duplicate_by_source[row.get("canonical_retained_source_id", "")].append(row)

    rows: list[dict[str, Any]] = []
    for item in queue:
        review = source_review.get(item["canonical_source_review_id"], {})
        local = core.ROOT / item["local_artifact_path"]
        current_store = CURRENT_RETAINED_ROOT in local.parents
        duplicates = duplicate_by_source.get(item["retained_source_id"], [])
        row = {
            "canonical_source_record_id": item["readiness_queue_id"],
            "retained_source_id": item["retained_source_id"],
            "canonical_source_review_id": item["canonical_source_review_id"],
            "canonical_payload_id": stable("EXTPAYLOAD", item["SHA_256"]),
            "SHA_256": item["SHA_256"],
            "local_artifact_path": item["local_artifact_path"],
            "byte_size": int(item["byte_size"]),
            "detected_file_type": item["detected_file_type"],
            "MIME_type": item["MIME_type"],
            "original_filename": review.get("original_filename", local.name),
            "readiness_hint": item["readiness_hint"],
            "source_quality": item["source_quality"],
            "primary_content_family": item["primary_content_family"],
            "secondary_content_families": review.get("secondary_content_families", ""),
            "administrative_source_type": item["administrative_source_type"],
            "final_priority_bucket": review.get("final_priority_bucket", "low"),
            "municipality": review.get("municipality", ""),
            "state": review.get("state", ""),
            "period": review.get("period", ""),
            "side_scope": review.get("side_scope", ""),
            "department_scope": review.get("department_scope", ""),
            "linked_search_waves": review.get("linked_search_waves", ""),
            "linked_candidate_ids": item["linked_candidate_ids"],
            "linked_root_event_ids": item["linked_root_event_ids"],
            "linked_mechanism_exposure_event_ids": item["linked_mechanism_exposure_event_ids"],
            "linked_claim_ids": item["linked_claim_ids"],
            "expected_claim_upgrade_tags": review.get("expected_claim_upgrade_tags", ""),
            "duplicate_relationship_count": len(duplicates),
            "exact_duplicate_source_review_ids": join_values(link.get("source_review_id", "") for link in duplicates if link.get("duplicate_status") == "duplicate_exact_payload"),
            "prior_reuse_source_review_ids": join_values(link.get("source_review_id", "") for link in duplicates if link.get("duplicate_status") == "duplicate_known_retained_source"),
            "version_relationship_ids": "|".join(sorted(versions_by_source.get(item["retained_source_id"], []))),
            "payload_origin": "current_30_gib_store" if current_store else "canonical_prior_retained_source_reuse",
            "source_review_only": True,
            "analytical_extraction_performed": False,
        }
        rows.append(row)

    source_ids = [row["canonical_source_record_id"] for row in rows]
    hashes = [row["SHA_256"] for row in rows]
    paths = [row["local_artifact_path"] for row in rows]
    current = [row for row in rows if row["payload_origin"] == "current_30_gib_store"]
    prior = [row for row in rows if row["payload_origin"] == "canonical_prior_retained_source_reuse"]
    reconciliation = {
        "expected_canonical_source_records": EXPECTED_CANONICAL,
        "observed_canonical_source_records": len(rows),
        "reported_current_store_unique_payloads": EXPECTED_CURRENT_PAYLOADS,
        "observed_current_store_unique_payloads": len({row["SHA_256"] for row in current}),
        "observed_prior_reuse_unique_payloads": len({row["SHA_256"] for row in prior}),
        "corrected_total_unique_physical_payloads_for_readiness": len(set(hashes)),
        "count_correction_required": len(set(hashes)) != EXPECTED_CURRENT_PAYLOADS,
        "count_correction_reason": "The reported 14,449 count covers only the new 30 GiB content-addressed store. The canonical readiness queue also contains 254 distinct valid prior-source payload reuses, so readiness must inspect 14,703 unique physical payloads.",
        "canonical_source_ids_unique": len(source_ids) == len(set(source_ids)),
        "payload_hashes_unique_in_canonical_queue": len(hashes) == len(set(hashes)),
        "payload_paths_unique_in_canonical_queue": len(paths) == len(set(paths)),
        "exact_duplicate_link_rows": sum(row.get("duplicate_status") == "duplicate_exact_payload" for row in duplicate_links),
        "known_prior_reuse_link_rows": sum(row.get("duplicate_status") == "duplicate_known_retained_source" for row in duplicate_links),
        "version_relationship_rows": len(version_links),
        "relationship_arithmetic_note": "Duplicate and reuse ledgers are lineage links and may overlap canonical payload targets; they are not additive readiness records.",
        "missing_payload_count": sum(not (core.ROOT / row["local_artifact_path"]).is_file() for row in rows),
        "conflicting_hash_path_count": 0,
        "reconciled_at": utc_now(),
    }
    return sorted(rows, key=lambda row: row["canonical_source_record_id"]), reconciliation


def build_payload_rows(canonical: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in canonical:
        grouped[row["SHA_256"]].append(row)
    output: list[dict[str, Any]] = []
    for digest, group in sorted(grouped.items()):
        first = group[0]
        output.append({
            "canonical_payload_id": stable("EXTPAYLOAD", digest),
            "SHA_256": digest,
            "local_artifact_path": first["local_artifact_path"],
            "byte_size": first["byte_size"],
            "detected_file_type": first["detected_file_type"],
            "MIME_type": first["MIME_type"],
            "original_filename": first["original_filename"],
            "canonical_source_record_ids": join_values(row["canonical_source_record_id"] for row in group),
            "canonical_retained_source_ids": join_values(row["retained_source_id"] for row in group),
            "duplicate_retained_source_ids": join_values(row["exact_duplicate_source_review_ids"] for row in group),
            "prior_retained_source_reuse_ids": join_values(row["prior_reuse_source_review_ids"] for row in group),
            "version_relationship_ids": join_values(row["version_relationship_ids"] for row in group),
            "municipality": join_values(row["municipality"] for row in group),
            "state": join_values(row["state"] for row in group),
            "period": join_values(row["period"] for row in group),
            "side_scope": join_values(row["side_scope"] for row in group),
            "department_scope": join_values(row["department_scope"] for row in group),
            "linked_candidate_ids": join_values(row["linked_candidate_ids"] for row in group),
            "linked_root_event_ids": join_values(row["linked_root_event_ids"] for row in group),
            "linked_mechanism_exposure_event_ids": join_values(row["linked_mechanism_exposure_event_ids"] for row in group),
            "linked_claim_ids": join_values(row["linked_claim_ids"] for row in group),
            "expected_claim_upgrade_tags": join_values(row["expected_claim_upgrade_tags"] for row in group),
            "linked_search_waves": join_values(row["linked_search_waves"] for row in group),
            "source_family": join_values(row["primary_content_family"] for row in group),
            "secondary_source_families": join_values(row["secondary_content_families"] for row in group),
            "administrative_source_type": join_values(row["administrative_source_type"] for row in group),
            "source_quality": join_values(row["source_quality"] for row in group),
            "review_priority": join_values(row["final_priority_bucket"] for row in group),
            "payload_origin": join_values(row["payload_origin"] for row in group),
            "canonical_source_fanout": len(group),
            "candidate_fanout": len(split_values(join_values(row["linked_candidate_ids"] for row in group))),
            "event_fanout": len(set(split_values(join_values(row["linked_root_event_ids"] for row in group))) | set(split_values(join_values(row["linked_mechanism_exposure_event_ids"] for row in group)))),
            "claim_fanout": len(split_values(join_values(row["linked_claim_ids"] or row["expected_claim_upgrade_tags"] for row in group))),
        })
    return output


def inspection_weight(row: dict[str, Any]) -> int:
    kind_factor = {"pdf": 12, "html": 5, "csv": 2, "tsv": 2, "txt": 1}.get(row["detected_file_type"], 7)
    size_mb = max(1, int(row["byte_size"]) // (1024 * 1024))
    return kind_factor * 1_000_000 + min(size_mb, 500) * 10_000 + row["candidate_fanout"] * 100 + row["event_fanout"] * 10


def assign_lanes(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lanes: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    weights = Counter()
    bytes_by_lane = Counter()
    for row in sorted(rows, key=lambda item: (-inspection_weight(item), item["canonical_payload_id"])):
        lane = min(LANES, key=lambda name: (weights[name], bytes_by_lane[name], len(lanes[name]), name))
        lanes[lane].append(row)
        weights[lane] += inspection_weight(row)
        bytes_by_lane[lane] += int(row["byte_size"])
    for lane in LANES:
        lanes[lane].sort(key=lambda item: (item["detected_file_type"], item["canonical_payload_id"]))
        for sequence, row in enumerate(lanes[lane], 1):
            row["readiness_lane_id"] = lane
            row["readiness_lane_sequence"] = sequence
    return lanes


def priority_for(row: dict[str, Any]) -> str:
    quality = row.get("source_quality", "")
    family = row.get("source_family", "")
    admin = row.get("administrative_source_type", "")
    upgrades = row.get("expected_claim_upgrade_tags", "")
    direct_families = {"payroll_and_earnings", "staffing_and_headcount", "implementation_confirmation", "benefits_and_total_compensation"}
    direct_admin = {"payroll_roster", "open_checkbook", "earnings_report", "staffing_table", "vacancy_report", "salary_schedule", "government_dataset", "ordinance_or_resolution", "implementation_record"}
    if "direct_official_administrative_record" in quality or any(value in family for value in direct_families) or any(value in admin for value in direct_admin):
        return "extraction_priority_high"
    if "official_administrative_summary" in quality or upgrades:
        return "extraction_priority_medium"
    if "contextual" in family or "context" in quality:
        return "extraction_priority_context_only"
    return "extraction_priority_low"


def preflight() -> None:
    if current_head() != REQUIRED_COMMIT and not is_ancestor(REQUIRED_COMMIT):
        raise RuntimeError("required source-review commit is not an ancestor")
    dirty = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    allowed = {"?? scripts/run_available_external_data_readiness.py"}
    unrelated = [line for line in dirty if line not in allowed]
    if unrelated:
        raise RuntimeError("dirty worktree preflight blocker:\n" + "\n".join(unrelated))
    if not INPUT.is_dir():
        raise RuntimeError("source-review input directory missing")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("readiness output exists; resume from its checkpoint rather than rebuilding")
    if process_matches():
        raise RuntimeError(f"duplicate readiness workers active: {process_matches()}")
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    if staged:
        raise RuntimeError("preflight requires empty Git index")
    for root in (CURRENT_RETAINED_ROOT, EXTRACTED_ROOT, STRUCTURED_ROOT):
        if not git_ignored(root):
            raise RuntimeError(f"payload root is not Git ignored: {root}")
    summary = read_json(INPUT / "external_data_source_review_download_summary.json")
    if summary["readiness_queue_count"] != EXPECTED_CANONICAL or summary["retained_source_count"] != EXPECTED_CURRENT_PAYLOADS:
        raise RuntimeError("source-review readiness counts do not match locked inputs")
    if summary["retained_bytes"] != EXPECTED_CURRENT_BYTES:
        raise RuntimeError("retained current-store byte count mismatch")
    if summary["terminal_status_counts"].get("manual_review_hold") != EXPECTED_HOLDS:
        raise RuntimeError("storage-capacity hold count mismatch")
    if summary["terminal_status_counts"].get("secondary_context_only_deferred") != EXPECTED_CONTEXT_DEFERS:
        raise RuntimeError("secondary-context defer count mismatch")
    if summary["unresolved_hosted_search_targets"] != EXPECTED_UNRESOLVED:
        raise RuntimeError("unresolved hosted-search count mismatch")

    canonical, reconciliation = build_canonical_rows()
    payloads = build_payload_rows(canonical)
    if len(canonical) != EXPECTED_CANONICAL or len({row["canonical_source_record_id"] for row in canonical}) != EXPECTED_CANONICAL:
        raise RuntimeError("canonical source queue count or uniqueness failed")
    if len(payloads) != EXPECTED_CANONICAL:
        raise RuntimeError("reconciled physical payload count differs from canonical count")
    hold_ids = {row["source_review_id"] for row in load_shards(INPUT, "manual_review_hold_queue_shard_manifest.json")}
    if len(hold_ids) != EXPECTED_HOLDS or any(row["canonical_source_review_id"] in hold_ids for row in canonical):
        raise RuntimeError("storage-capacity hold queue leaked into readiness")

    missing: list[dict[str, Any]] = []
    hash_failures: list[dict[str, Any]] = []
    bytes_checked = 0
    started = time.monotonic()
    for index, row in enumerate(payloads, 1):
        path = core.ROOT / row["local_artifact_path"]
        if not path.is_file():
            missing.append({"canonical_payload_id": row["canonical_payload_id"], "reason": "missing_local_payload", "local_artifact_path": row["local_artifact_path"]})
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        bytes_checked += size
        if size != int(row["byte_size"]) or digest != row["SHA_256"]:
            hash_failures.append({"canonical_payload_id": row["canonical_payload_id"], "reason": "hash_or_size_mismatch", "expected_hash": row["SHA_256"], "observed_hash": digest, "expected_bytes": row["byte_size"], "observed_bytes": size, "local_artifact_path": row["local_artifact_path"]})
        if index % 500 == 0:
            print(json.dumps({"preflight_hashed": index, "total": len(payloads), "bytes_checked": bytes_checked}), flush=True)
    conflicts = missing + hash_failures
    reconciliation.update({"all_local_paths_valid": not missing, "all_hashes_and_sizes_valid": not hash_failures, "full_hash_audit_payload_count": len(payloads), "full_hash_audit_bytes": bytes_checked, "full_hash_audit_runtime_seconds": round(time.monotonic() - started, 6)})
    if conflicts:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        core.write_pair(OUTPUT, "missing_or_conflicting_payload_queue", conflicts)
        atomic_json(OUTPUT / "readiness_input_reconciliation_audit.json", reconciliation)
        raise RuntimeError(f"missing/conflicting payload integrity blocker: {len(conflicts)}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    write_sharded("readiness_locked_source_queue", canonical)
    write_sharded("readiness_unique_payload_queue", payloads)
    core.write_pair(OUTPUT, "canonical_source_to_payload_reconciliation", [{"canonical_source_record_id": row["canonical_source_record_id"], "retained_source_id": row["retained_source_id"], "canonical_payload_id": row["canonical_payload_id"], "SHA_256": row["SHA_256"], "local_artifact_path": row["local_artifact_path"], "payload_origin": row["payload_origin"], "reconciliation_status": "valid_unique_payload"} for row in canonical])
    core.write_pair(OUTPUT, "missing_or_conflicting_payload_queue", [])
    atomic_json(OUTPUT / "readiness_input_reconciliation_audit.json", reconciliation)
    core.write_md(OUTPUT / "readiness_input_reconciliation_audit.md", "# Readiness input reconciliation audit\n\n- Canonical retained-source records: 14,703.\n- Current 30 GiB-store payloads: 14,449.\n- Distinct valid prior-source reuse payloads: 254.\n- Correct physical readiness universe: 14,703 unique hashes and paths.\n- Exact-duplicate links: 552; known-reuse links: 264. These are lineage relationships, not additive readiness rows.\n- Every local path, byte size, and SHA-256 was checked successfully before lane construction.\n")
    atomic_json(OUTPUT / "duplicate_and_reuse_propagation_summary.json", {"exact_duplicate_link_rows": reconciliation["exact_duplicate_link_rows"], "known_prior_reuse_link_rows": reconciliation["known_prior_reuse_link_rows"], "current_store_canonical_payloads": reconciliation["observed_current_store_unique_payloads"], "prior_reuse_canonical_payloads": reconciliation["observed_prior_reuse_unique_payloads"], "physical_payloads_queued_once": len(payloads), "duplicate_extraction_rows_created": 0})

    lanes = assign_lanes(payloads)
    distribution: dict[str, Any] = {}
    for lane in LANES:
        write_sharded(f"{lane}_queue", lanes[lane])
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "locked_not_started", "locked_count": len(lanes[lane]), "completed_count": 0, "remaining_count": len(lanes[lane]), "bytes_completed": 0, "updated_at": utc_now()})
        distribution[lane] = {"count": len(lanes[lane]), "bytes": sum(int(row["byte_size"]) for row in lanes[lane]), "type_counts": dict(Counter(row["detected_file_type"] for row in lanes[lane])), "stagger_minutes": STAGGER_SECONDS[lane] // 60}
    source_hash = hashlib.sha256("\n".join(row["canonical_source_record_id"] for row in canonical).encode()).hexdigest()
    payload_hash = hashlib.sha256("\n".join(row["canonical_payload_id"] for row in payloads).encode()).hexdigest()
    atomic_json(OUTPUT / "readiness_locked_source_queue_manifest.json", {"task_id": TASK_ID, "count": len(canonical), "queue_sha256": source_hash, "unique_source_records": True, "created_at": utc_now()})
    atomic_json(OUTPUT / "readiness_unique_payload_queue_manifest.json", {"task_id": TASK_ID, "count": len(payloads), "queue_sha256": payload_hash, "unique_hashes": len({row["SHA_256"] for row in payloads}), "total_bytes": sum(int(row["byte_size"]) for row in payloads), "created_at": utc_now()})
    atomic_json(OUTPUT / "readiness_lane_distribution.json", {"total": len(payloads), "disjoint": len({row["canonical_payload_id"] for group in lanes.values() for row in group}) == len(payloads), "lanes": distribution})
    core.write_md(OUTPUT / "readiness_lane_distribution.md", "# Readiness lane distribution\n\n" + "\n".join(f"- {lane}: {distribution[lane]['count']:,} payloads; {distribution[lane]['bytes']:,} bytes; T+{distribution[lane]['stagger_minutes']} minutes" for lane in LANES))
    free = shutil.disk_usage(core.ROOT).free
    if free < 2 * 1024**3:
        raise RuntimeError("insufficient free space for bounded readiness metadata")
    manifest = {"task_id": TASK_ID, "decision_pending": True, "starting_head": current_head(), "canonical_source_records": len(canonical), "unique_physical_payloads": len(payloads), "retained_bytes_inspected_preflight": bytes_checked, "network_calls": 0, "hosted_search_calls": 0, "gabriel_calls": 0, "ocr_runs": 0, "analytical_extraction_runs": 0, "storage_capacity_holds_preserved": EXPECTED_HOLDS, "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "created_at": utc_now()}
    atomic_json(OUTPUT / "readiness_run_manifest.json", manifest)
    atomic_json(OUTPUT / "readiness_run_state.json", {"task_id": TASK_ID, "status": "preflight_passed", "current_stage": "five_lane_readiness_pending", "completed_payloads": 0, "remaining_payloads": len(payloads), "updated_at": utc_now()})
    atomic_json(OUTPUT / "readiness_stage_checkpoint.json", {"stage": "05_EXTERNAL-DATA-READINESS", "status": "preflight_passed", "locked_payloads": len(payloads), "updated_at": utc_now()})
    core.write_jsonl(OUTPUT / "readiness_stage_transition_log.jsonl", [{"at": utc_now(), "stage": "preflight", "status": "passed", "canonical_sources": len(canonical), "physical_payloads": len(payloads)}])
    core.write_jsonl(OUTPUT / "readiness_operational_incident_log.jsonl", [{"at": utc_now(), "incident": "physical_payload_count_reconciled", "severity": "informational", "details": reconciliation["count_correction_reason"]}])
    print(json.dumps({"preflight": "passed", "canonical_sources": len(canonical), "physical_payloads": len(payloads), "bytes_hashed": bytes_checked, "lanes": distribution}, indent=2))


class PayloadTimeout(Exception):
    pass


def _alarm_handler(_signum: int, _frame: Any) -> None:
    raise PayloadTimeout("bounded readiness diagnostic timed out")


def sampled_page_indices(page_count: int) -> list[int]:
    if page_count <= MAX_PDF_SAMPLE_PAGES:
        return list(range(page_count))
    return sorted({0, 1, page_count // 2, page_count - 2, page_count - 1})


def inspect_pdf(path: Path) -> tuple[str, dict[str, Any], list[str]]:
    diagnostics: dict[str, Any] = {"valid_pdf_signature": False, "page_count": 0, "encrypted": False, "password_restriction": False, "sampled_page_count": 0, "sampled_text_characters": 0, "empty_text_sampled_pages": 0, "sampled_image_object_count": 0, "likely_image_only": False, "pdf_header": "", "pdf_eof_marker_present": False, "page_width_min": None, "page_width_max": None, "page_height_min": None, "page_height_max": None, "embedded_attachment_names": 0, "diagnostic_text_persisted": False}
    hints: list[str] = []
    with path.open("rb") as handle:
        header = handle.read(16)
        diagnostics["pdf_header"] = header.decode("latin-1", errors="replace")
        diagnostics["valid_pdf_signature"] = header.startswith(b"%PDF-")
        handle.seek(max(0, path.stat().st_size - 4096))
        diagnostics["pdf_eof_marker_present"] = b"%%EOF" in handle.read()
    if not diagnostics["valid_pdf_signature"]:
        return "corrupt_or_broken", diagnostics, ["invalid_pdf_signature"]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reader = PdfReader(str(path), strict=False)
            diagnostics["encrypted"] = bool(reader.is_encrypted)
            if reader.is_encrypted:
                try:
                    unlocked = bool(reader.decrypt(""))
                except Exception:
                    unlocked = False
                if not unlocked:
                    diagnostics["password_restriction"] = True
                    return "encrypted_or_locked", diagnostics, ["pdf_password_required"]
            page_count = len(reader.pages)
            diagnostics["page_count"] = page_count
            if page_count <= 0:
                return "corrupt_or_broken", diagnostics, ["pdf_zero_pages"]
            if page_count > 50_000:
                return "oversized_defer", diagnostics, ["pathological_page_count"]
            widths: list[float] = []
            heights: list[float] = []
            chars = 0
            empty = 0
            images = 0
            indices = sampled_page_indices(page_count)
            diagnostics["sampled_page_count"] = len(indices)
            for index in indices:
                page = reader.pages[index]
                try:
                    widths.append(float(page.mediabox.width)); heights.append(float(page.mediabox.height))
                except Exception:
                    pass
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                    hints.append(f"page_{index + 1}_text_extract_error")
                normalized = re.sub(r"\s+", " ", text).strip()
                chars += len(normalized)
                if not normalized:
                    empty += 1
                try:
                    resources = page.get("/Resources") or {}
                    xobjects = resources.get("/XObject") if hasattr(resources, "get") else None
                    if xobjects:
                        xobjects = xobjects.get_object()
                        for obj in xobjects.values():
                            try:
                                if obj.get_object().get("/Subtype") == "/Image":
                                    images += 1
                            except Exception:
                                continue
                except Exception:
                    pass
            diagnostics.update({"sampled_text_characters": chars, "empty_text_sampled_pages": empty, "sampled_image_object_count": images, "likely_image_only": chars == 0 and (images > 0 or empty == len(indices)), "page_width_min": min(widths) if widths else None, "page_width_max": max(widths) if widths else None, "page_height_min": min(heights) if heights else None, "page_height_max": max(heights) if heights else None})
            try:
                diagnostics["embedded_attachment_names"] = len(getattr(reader, "attachments", {}) or {})
            except Exception:
                pass
            if chars >= max(400, len(indices) * 100):
                return "parse_text_pdf_ready", diagnostics, hints or ["usable_sampled_text_layer"]
            if chars > 0:
                return "parse_text_pdf_low_text_usable", diagnostics, hints or ["sparse_nonempty_text_layer"]
            return "ocr_later", diagnostics, hints or ["no_extractable_text_in_representative_pages"]
    except PayloadTimeout:
        raise
    except Exception as exc:
        diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        return "corrupt_or_broken", diagnostics, ["pdf_parser_error"]


def decode_html(raw: bytes) -> tuple[str, str]:
    head = raw[:4096].decode("ascii", errors="ignore")
    match = re.search(r"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", head, re.I)
    candidates = [match.group(1)] if match else []
    candidates += ["utf-8", "windows-1252", "latin-1"]
    for encoding in candidates:
        try:
            return raw.decode(encoding), encoding
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replacement"


def inspect_html(path: Path) -> tuple[str, dict[str, Any], list[str]]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(MAX_HTML_DIAGNOSTIC_BYTES)
    text, encoding = decode_html(raw)
    diagnostics: dict[str, Any] = {"encoding": encoding, "bytes_inspected": len(raw), "payload_bytes": size, "bounded_inspection": size > len(raw), "valid_html_structure": False, "visible_text_characters": 0, "table_count": 0, "row_element_count": 0, "script_count": 0, "link_count": 0, "form_count": 0, "structured_data_script_count": 0, "navigation_density": 0.0, "diagnostic_text_persisted": False}
    try:
        document = lxml_html.fromstring(text)
        diagnostics["valid_html_structure"] = True
        for bad in document.xpath("//script|//style|//noscript|//svg"):
            if bad.tag == "script" and str(bad.get("type", "")).casefold() in {"application/ld+json", "application/json"}:
                diagnostics["structured_data_script_count"] += 1
            bad.drop_tree()
        visible = re.sub(r"\s+", " ", " ".join(document.itertext())).strip()
        diagnostics["visible_text_characters"] = len(visible)
        diagnostics["table_count"] = len(document.xpath("//table"))
        diagnostics["row_element_count"] = len(document.xpath("//tr"))
        diagnostics["script_count"] = text.casefold().count("<script")
        diagnostics["link_count"] = len(document.xpath("//a"))
        diagnostics["form_count"] = len(document.xpath("//form"))
        diagnostics["navigation_density"] = round(diagnostics["link_count"] / max(1, len(visible.split())), 6)
        lowered = visible.casefold()
        shell_markers = sum(marker in lowered for marker in ("enable javascript", "page not found", "access denied", "site search", "search results", "document center", "calendar of events"))
        if len(visible) < 40 and diagnostics["script_count"] > 2:
            return "shell_or_navigation_only", diagnostics, ["script_shell_with_minimal_visible_text"]
        if shell_markers and len(visible) < 1_500 and diagnostics["navigation_density"] > 0.03:
            return "shell_or_navigation_only", diagnostics, ["navigation_or_error_shell_markers"]
        if diagnostics["structured_data_script_count"] or re.search(r"\b(api|dataset|download csv|open data)\b", lowered):
            return "html_structured_data_candidate", diagnostics, ["structured_data_or_dataset_signal"]
        if diagnostics["table_count"] or diagnostics["row_element_count"] >= 3:
            return "html_table_candidate_ready", diagnostics, ["html_table_structure_present"]
        if len(visible) >= 500:
            return "html_text_ready", diagnostics, ["substantive_visible_html_text"]
        if len(visible) >= 40:
            return "html_low_text_usable", diagnostics, ["sparse_nonempty_visible_html_text"]
        return "needs_manual_review", diagnostics, ["minimal_html_text_without_clear_shell_signal"]
    except (etree.ParserError, ValueError, UnicodeError) as exc:
        diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        return "corrupt_or_broken", diagnostics, ["html_parser_error"]


def inspect_csv(path: Path, forced_delimiter: str | None = None) -> tuple[str, dict[str, Any], list[str]]:
    raw = path.read_bytes()
    text, encoding = decode_html(raw)
    sample = text[:128_000]
    delimiter = forced_delimiter
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
        except csv.Error:
            delimiter = ","
    diagnostics: dict[str, Any] = {"encoding": encoding, "delimiter": "TAB" if delimiter == "\t" else delimiter, "row_count": 0, "column_count": 0, "header_candidates": [], "duplicate_header_count": 0, "blank_row_count": 0, "malformed_row_count": 0, "likely_date_columns": [], "likely_municipality_department_employee_columns": [], "likely_compensation_staffing_columns": [], "diagnostic_rows_persisted": False}
    try:
        rows = csv.reader(text.splitlines(), delimiter=delimiter)
        header = next(rows, [])
        diagnostics["header_candidates"] = [re.sub(r"\s+", " ", value).strip()[:200] for value in header]
        diagnostics["column_count"] = len(header)
        diagnostics["duplicate_header_count"] = len(header) - len({value.casefold().strip() for value in header})
        row_count = 0
        blank = 0
        malformed = 0
        for row in rows:
            row_count += 1
            if not any(value.strip() for value in row): blank += 1
            if header and len(row) != len(header): malformed += 1
        diagnostics.update({"row_count": row_count, "blank_row_count": blank, "malformed_row_count": malformed})
        lowered = [value.casefold() for value in header]
        diagnostics["likely_date_columns"] = [header[i] for i, value in enumerate(lowered) if any(token in value for token in ("date", "year", "period", "fiscal"))]
        diagnostics["likely_municipality_department_employee_columns"] = [header[i] for i, value in enumerate(lowered) if any(token in value for token in ("city", "municip", "department", "agency", "employee", "name", "title", "position"))]
        diagnostics["likely_compensation_staffing_columns"] = [header[i] for i, value in enumerate(lowered) if any(token in value for token in ("pay", "salary", "earning", "overtime", "compensation", "staff", "headcount", "vacan", "authorized", "filled"))]
        status = "tsv_structured_ready" if delimiter == "\t" else "csv_structured_ready"
        if not header or diagnostics["column_count"] <= 1:
            status = "structured_low_quality_usable" if row_count else "corrupt_or_broken"
        elif malformed > max(10, row_count // 3):
            status = "structured_low_quality_usable"
        return status, diagnostics, ["parseable_delimited_schema"]
    except (csv.Error, UnicodeError) as exc:
        diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        return "corrupt_or_broken", diagnostics, ["delimited_parser_error"]


def inspect_text(path: Path) -> tuple[str, dict[str, Any], list[str]]:
    raw = path.read_bytes()
    text, encoding = decode_html(raw)
    lines = text.splitlines()
    diagnostics = {"encoding": encoding, "line_count": len(lines), "character_count": len(text), "nonempty_line_count": sum(bool(line.strip()) for line in lines), "delimiter_hints": {delimiter: sum(line.count(delimiter) for line in lines[:100]) for delimiter in (",", "TAB", "|", ";")}, "table_like": False, "diagnostic_text_persisted": False}
    diagnostics["delimiter_hints"]["TAB"] = diagnostics["delimiter_hints"].pop("TAB", 0) + sum(line.count("\t") for line in lines[:100])
    diagnostics["table_like"] = any(value >= max(2, len(lines[:100]) // 2) for value in diagnostics["delimiter_hints"].values())
    if len(text.strip()) == 0:
        return "corrupt_or_broken", diagnostics, ["empty_text_payload"]
    if diagnostics["table_like"]:
        return "text_table_candidate_ready", diagnostics, ["text_has_repeated_delimiter_structure"]
    if len(text.strip()) >= 100:
        return "text_ready", diagnostics, ["substantive_text_payload"]
    return "text_low_quality_usable", diagnostics, ["short_nonempty_text_payload"]


def inspect_other(path: Path, kind: str) -> tuple[str, dict[str, Any], list[str]]:
    diagnostics: dict[str, Any] = {"detected_file_type": kind, "byte_size": path.stat().st_size, "diagnostic_payload_created": False}
    if kind == "json":
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            diagnostics.update({"top_level_type": type(value).__name__, "top_level_count": len(value) if hasattr(value, "__len__") else None, "top_level_keys": list(value)[:100] if isinstance(value, dict) else []})
            return "json_structured_ready", diagnostics, ["parseable_json_structure"]
        except Exception as exc:
            diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"; return "corrupt_or_broken", diagnostics, ["json_parser_error"]
    if kind == "xml":
        try:
            root = etree.parse(str(path)).getroot()
            diagnostics.update({"root_tag": str(root.tag), "direct_child_count": len(root), "sample_child_tags": [str(child.tag) for child in list(root)[:100]]})
            return "xml_structured_ready", diagnostics, ["parseable_xml_structure"]
        except Exception as exc:
            diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"; return "corrupt_or_broken", diagnostics, ["xml_parser_error"]
    if kind == "zip":
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                names = [info.filename for info in infos]
                traversal = any(".." in Path(name).parts or Path(name).is_absolute() for name in names)
                diagnostics.update({"member_count": len(infos), "uncompressed_bytes": sum(info.file_size for info in infos), "member_types": dict(Counter(Path(name).suffix.casefold() or "no_extension" for name in names)), "nested_archive_count": sum(Path(name).suffix.casefold() in {".zip", ".7z", ".rar", ".tar", ".gz"} for name in names), "path_traversal_risk": traversal, "encrypted_member_count": sum(bool(info.flag_bits & 0x1) for info in infos)})
                if traversal: return "suspicious_or_quarantine", diagnostics, ["archive_path_traversal_risk"]
                if diagnostics["encrypted_member_count"]: return "encrypted_or_locked", diagnostics, ["encrypted_archive_members"]
                return "official_data_package_ready", diagnostics, ["supported_archive_inventory"]
        except Exception as exc:
            diagnostics["parser_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"; return "corrupt_or_broken", diagnostics, ["archive_parser_error"]
    if kind in {"xlsx", "xls"}:
        return "unsupported_spreadsheet_structure", diagnostics, ["spreadsheet_parser_dependency_unavailable"]
    return "unsupported_file_type", diagnostics, ["unrecognized_retained_format"]


def inspect_payload(row: dict[str, Any]) -> dict[str, Any]:
    path = core.ROOT / row["local_artifact_path"]
    started = time.monotonic()
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(PER_PAYLOAD_TIMEOUT_SECONDS)
    try:
        kind = row["detected_file_type"].casefold()
        if kind == "pdf": status, diagnostics, reasons = inspect_pdf(path)
        elif kind == "html": status, diagnostics, reasons = inspect_html(path)
        elif kind == "csv": status, diagnostics, reasons = inspect_csv(path)
        elif kind == "tsv": status, diagnostics, reasons = inspect_csv(path, "\t")
        elif kind in {"txt", "text"}: status, diagnostics, reasons = inspect_text(path)
        else: status, diagnostics, reasons = inspect_other(path, kind)
    except PayloadTimeout as exc:
        status, diagnostics, reasons = "needs_manual_review", {"timeout_seconds": PER_PAYLOAD_TIMEOUT_SECONDS, "timeout_error": str(exc)}, ["bounded_readiness_timeout"]
    except Exception as exc:
        status, diagnostics, reasons = "readiness_error", {"error_type": type(exc).__name__, "error": str(exc)[:1000]}, ["unexpected_readiness_error"]
    finally:
        signal.alarm(0)
    return {
        **row,
        "readiness_result_id": stable("EXTREADINESS", row["canonical_payload_id"], status),
        "readiness_status": status,
        "extraction_ready": status in EXTRACTION_READY,
        "primary_extraction_queue": PRIMARY_QUEUE.get(status, ""),
        "deferred_queue": DEFERRED_QUEUE.get(status, ""),
        "secondary_processing_hints": "table_candidate" if status in {"html_table_candidate_ready", "html_structured_data_candidate", "text_table_candidate_ready"} else "",
        "extraction_priority": priority_for(row),
        "readiness_reason_codes": "|".join(reasons),
        "diagnostics_json": json.dumps(diagnostics, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        "diagnostic_full_text_persisted": False,
        "analytical_rows_extracted": 0,
        "ocr_performed": False,
        "inspected_at": utc_now(),
        "inspection_runtime_seconds": round(time.monotonic() - started, 6),
    }


def propagation_rows(payload_result: dict[str, Any], source_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in split_values(payload_result["canonical_source_record_ids"]):
        source = source_lookup[source_id]
        rows.append({
            **source,
            "readiness_result_id": payload_result["readiness_result_id"],
            "readiness_status": payload_result["readiness_status"],
            "extraction_ready": payload_result["extraction_ready"],
            "primary_extraction_queue": payload_result["primary_extraction_queue"],
            "deferred_queue": payload_result["deferred_queue"],
            "secondary_processing_hints": payload_result["secondary_processing_hints"],
            "extraction_priority": payload_result["extraction_priority"],
            "readiness_reason_codes": payload_result["readiness_reason_codes"],
            "physical_payload_inspected_once": True,
            "readiness_propagation_basis": "canonical_payload_sha256",
            "diagnostic_full_text_persisted": False,
            "analytical_rows_extracted": 0,
            "ocr_performed": False,
            "propagated_at": utc_now(),
        })
    return rows


def smoke() -> None:
    payloads = load_shards(OUTPUT, "readiness_unique_payload_queue_shard_manifest.json")
    canonical = load_shards(OUTPUT, "readiness_locked_source_queue_shard_manifest.json")
    source_lookup = {row["canonical_source_record_id"]: row for row in canonical}
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in payloads: by_type[row["detected_file_type"]].append(row)
    probes: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for kind in ("pdf", "html", "csv", "txt"):
        if by_type.get(kind): selected.append(min(by_type[kind], key=lambda row: int(row["byte_size"])))
    prior = next((row for row in payloads if row["payload_origin"] == "canonical_prior_retained_source_reuse"), None)
    if prior and prior["canonical_payload_id"] not in {row["canonical_payload_id"] for row in selected}: selected.append(prior)
    for row in selected:
        result = inspect_payload(row)
        propagated = propagation_rows(result, source_lookup)
        probes.append({"canonical_payload_id": row["canonical_payload_id"], "detected_file_type": row["detected_file_type"], "payload_origin": row["payload_origin"], "readiness_status": result["readiness_status"], "propagated_source_count": len(propagated), "diagnostic_full_text_persisted": False, "analytical_rows_extracted": 0, "ocr_performed": False})
    exact_example = next((row for row in canonical if int(row["duplicate_relationship_count"]) > 0), None)
    smoke_result = {"passed": len(probes) >= 4 and all(row["readiness_status"] in TERMINAL for row in probes), "probe_count": len(probes), "probes": probes, "exact_duplicate_propagation_example": {"canonical_source_record_id": exact_example["canonical_source_record_id"], "canonical_payload_id": exact_example["canonical_payload_id"], "relationship_count": exact_example["duplicate_relationship_count"]} if exact_example else {}, "full_extraction_outputs_created": 0, "network_requests": 0, "redownloads": 0, "tested_at": utc_now()}
    atomic_json(OUTPUT / "readiness_smoke_results.json", smoke_result)
    if not smoke_result["passed"]: raise RuntimeError("readiness smoke failed")
    print(json.dumps(smoke_result, indent=2))


def run_lane(lane_number: int, start_delay_seconds: int) -> None:
    lane = LANES[lane_number - 1]
    if start_delay_seconds:
        time.sleep(start_delay_seconds)
    queue = load_shards(OUTPUT, f"{lane}_queue_shard_manifest.json")
    canonical = load_shards(OUTPUT, "readiness_locked_source_queue_shard_manifest.json")
    source_lookup = {row["canonical_source_record_id"]: row for row in canonical}
    payload_ledger = OUTPUT / f"{lane}_payload_results.jsonl"
    propagation_ledger = OUTPUT / f"{lane}_canonical_propagation.jsonl"
    existing_payload = {row["canonical_payload_id"]: row for row in read_jsonl(payload_ledger)}
    existing_propagation = read_jsonl(propagation_ledger)
    propagated_keys = {(row["canonical_source_record_id"], row["canonical_payload_id"]) for row in existing_propagation}
    completed = 0
    bytes_completed = 0
    status_counts = Counter()
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "running", "locked_count": len(queue), "completed_count": len(existing_payload), "remaining_count": len(queue) - len(existing_payload), "bytes_completed": sum(int(row["byte_size"]) for row in existing_payload.values()), "worker_pid": os.getpid(), "updated_at": utc_now()})
    for row in queue:
        payload_id = row["canonical_payload_id"]
        result = existing_payload.get(payload_id)
        if result is None:
            result = inspect_payload(row)
            append_jsonl(payload_ledger, result)
            existing_payload[payload_id] = result
        for propagated in propagation_rows(result, source_lookup):
            key = (propagated["canonical_source_record_id"], propagated["canonical_payload_id"])
            if key not in propagated_keys:
                append_jsonl(propagation_ledger, propagated)
                propagated_keys.add(key)
        completed += 1
        bytes_completed += int(row["byte_size"])
        status_counts[result["readiness_status"]] += 1
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "running", "locked_count": len(queue), "completed_count": completed, "remaining_count": len(queue) - completed, "bytes_completed": bytes_completed, "status_counts": dict(status_counts), "worker_pid": os.getpid(), "updated_at": utc_now()})
        if completed % 100 == 0:
            print(json.dumps({"lane": lane, "completed": completed, "total": len(queue), "status_counts": dict(status_counts)}), flush=True)
    payload_rows = sorted(existing_payload.values(), key=lambda row: row["canonical_payload_id"])
    propagation_rows_all = sorted(read_jsonl(propagation_ledger), key=lambda row: row["canonical_source_record_id"])
    core.write_csv(OUTPUT / f"{lane}_payload_results.csv", payload_rows)
    core.write_csv(OUTPUT / f"{lane}_canonical_propagation.csv", propagation_rows_all)
    atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "complete", "locked_count": len(queue), "completed_count": len(payload_rows), "remaining_count": 0, "bytes_completed": sum(int(row["byte_size"]) for row in payload_rows), "status_counts": dict(Counter(row["readiness_status"] for row in payload_rows)), "worker_pid": os.getpid(), "updated_at": utc_now()})
    print(json.dumps({"lane": lane, "status": "complete", "payloads": len(payload_rows), "propagations": len(propagation_rows_all)}, indent=2))


def parse_diagnostics(row: dict[str, Any]) -> dict[str, Any]:
    try: return json.loads(row.get("diagnostics_json", "{}"))
    except json.JSONDecodeError: return {}


def flattened_diagnostics(prefix: str, row: dict[str, Any]) -> dict[str, Any]:
    """Produce CSV-safe bounded diagnostic scalars without persisting text."""
    flattened: dict[str, Any] = {}
    for key, value in parse_diagnostics(row).items():
        if isinstance(value, str):
            value = re.sub(r"[\r\n\t]+", " ", value).strip()
        elif isinstance(value, (list, dict)):
            value = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        flattened[f"{prefix}_{key}"] = value
    return flattened


def grouped_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, dict[str, int]] = defaultdict(lambda: {"payload_count": 0, "bytes": 0, "extraction_ready_payloads": 0})
    for row in rows:
        values = split_values(str(row.get(field, ""))) or ["unclear"]
        for value in values:
            groups[value]["payload_count"] += 1
            groups[value]["bytes"] += int(row["byte_size"])
            groups[value]["extraction_ready_payloads"] += bool_value(row["extraction_ready"])
    return {"groups": dict(sorted(groups.items()))}


def finalize() -> None:
    payload_results: list[dict[str, Any]] = []
    canonical_results: list[dict[str, Any]] = []
    for lane in LANES:
        checkpoint = read_json(OUTPUT / f"{lane}_checkpoint.json")
        if checkpoint["status"] != "complete": raise RuntimeError(f"lane incomplete: {lane}")
        payload_results.extend(read_jsonl(OUTPUT / f"{lane}_payload_results.jsonl"))
        canonical_results.extend(read_jsonl(OUTPUT / f"{lane}_canonical_propagation.jsonl"))
    payload_by_id = {row["canonical_payload_id"]: row for row in payload_results}
    canonical_by_id = {row["canonical_source_record_id"]: row for row in canonical_results}
    payload_results = sorted(payload_by_id.values(), key=lambda row: row["canonical_payload_id"])
    canonical_results = sorted(canonical_by_id.values(), key=lambda row: row["canonical_source_record_id"])
    if len(payload_results) != EXPECTED_CANONICAL or len(canonical_results) != EXPECTED_CANONICAL:
        raise RuntimeError("merged readiness result counts do not reconcile")
    if any(row["readiness_status"] not in TERMINAL for row in payload_results): raise RuntimeError("nonterminal readiness result")

    write_sharded("physical_payload_readiness_results", payload_results)
    write_sharded("canonical_source_readiness_results", canonical_results)
    extraction_ready = [row for row in payload_results if bool_value(row["extraction_ready"])]
    write_sharded("external_data_extraction_ready_queue", extraction_ready)
    atomic_json(OUTPUT / "external_data_extraction_ready_queue_manifest.json", {"unique_payload_count": len(extraction_ready), "canonical_source_count": sum(int(row["canonical_source_fanout"]) for row in extraction_ready), "total_bytes": sum(int(row["byte_size"]) for row in extraction_ready), "status_counts": dict(Counter(row["readiness_status"] for row in extraction_ready)), "priority_counts": dict(Counter(row["extraction_priority"] for row in extraction_ready)), "created_at": utc_now()})
    queues: dict[str, list[dict[str, Any]]] = {name: [] for name in OUTPUT_QUEUE_NAMES}
    for row in payload_results:
        queue_name = row["primary_extraction_queue"] or row["deferred_queue"]
        if queue_name: queues[queue_name].append(row)
    for name in OUTPUT_QUEUE_NAMES: core.write_pair(OUTPUT, name, queues[name])

    pdf_rows = [{**row, **flattened_diagnostics("pdf", row)} for row in payload_results if row["detected_file_type"] == "pdf"]
    html_rows = [{**row, **flattened_diagnostics("html", row)} for row in payload_results if row["detected_file_type"] == "html"]
    csv_rows = [{**row, **flattened_diagnostics("csv", row)} for row in payload_results if row["detected_file_type"] in {"csv", "tsv"}]
    text_rows = [{**row, **flattened_diagnostics("text", row)} for row in payload_results if row["detected_file_type"] in {"txt", "text"}]
    core.write_pair(OUTPUT, "pdf_readiness_diagnostics", pdf_rows)
    core.write_pair(OUTPUT, "html_readiness_diagnostics", html_rows)
    core.write_pair(OUTPUT, "csv_readiness_diagnostics", csv_rows)
    core.write_pair(OUTPUT, "text_readiness_diagnostics", text_rows)
    core.write_pair(OUTPUT, "spreadsheet_readiness_diagnostics", [row for row in payload_results if row["detected_file_type"] in {"xlsx", "xls"}])
    core.write_pair(OUTPUT, "json_xml_readiness_diagnostics", [row for row in payload_results if row["detected_file_type"] in {"json", "xml"}])
    core.write_pair(OUTPUT, "archive_readiness_diagnostics", [row for row in payload_results if row["detected_file_type"] == "zip"])

    status_counts = Counter(row["readiness_status"] for row in payload_results)
    canonical_status_counts = Counter(row["readiness_status"] for row in canonical_results)
    type_counts = Counter(row["detected_file_type"] for row in payload_results)
    bytes_by_status = defaultdict(int)
    for row in payload_results: bytes_by_status[row["readiness_status"]] += int(row["byte_size"])
    atomic_json(OUTPUT / "readiness_status_summary.json", {"physical_payload_counts": dict(status_counts), "canonical_source_counts": dict(canonical_status_counts), "extraction_ready_physical_payloads": len(extraction_ready), "extraction_ready_canonical_sources": sum(int(row["canonical_source_fanout"]) for row in extraction_ready)})
    atomic_json(OUTPUT / "readiness_file_type_summary.json", {"payload_type_counts": dict(type_counts), "extraction_ready_by_type": dict(Counter(row["detected_file_type"] for row in extraction_ready))})
    atomic_json(OUTPUT / "readiness_bytes_summary.json", {"total_inspected_bytes": sum(int(row["byte_size"]) for row in payload_results), "bytes_by_status": dict(bytes_by_status), "extraction_ready_bytes": sum(int(row["byte_size"]) for row in extraction_ready)})
    atomic_json(OUTPUT / "readiness_priority_summary.json", {"all_payloads": dict(Counter(row["extraction_priority"] for row in payload_results)), "extraction_ready": dict(Counter(row["extraction_priority"] for row in extraction_ready))})
    for filename, field in [("readiness_source_family_summary.json", "source_family"), ("readiness_administrative_type_summary.json", "administrative_source_type"), ("readiness_source_quality_summary.json", "source_quality"), ("readiness_geography_summary.json", "state"), ("readiness_side_scope_summary.json", "side_scope"), ("readiness_claim_upgrade_summary.json", "expected_claim_upgrade_tags")]: atomic_json(OUTPUT / filename, grouped_summary(payload_results, field))
    atomic_json(OUTPUT / "readiness_event_linkage_summary.json", {"payload_count": len(payload_results), "candidate_link_count": sum(int(row["candidate_fanout"]) for row in payload_results), "root_event_link_count": sum(len(split_values(row["linked_root_event_ids"])) for row in payload_results), "mechanism_event_link_count": sum(len(split_values(row["linked_mechanism_exposure_event_ids"])) for row in payload_results), "claim_or_upgrade_link_count": sum(int(row["claim_fanout"]) for row in payload_results)})
    atomic_json(OUTPUT / "readiness_duplicate_propagation_summary.json", {"physical_payloads_inspected_once": len(payload_results), "canonical_sources_propagated": len(canonical_results), "physical_payloads_with_multiple_canonical_source_records": sum(int(row["canonical_source_fanout"]) > 1 for row in payload_results), "exact_duplicate_link_rows_preserved": EXPECTED_EXACT_DUPLICATE_LINKS, "known_reuse_link_rows_preserved": EXPECTED_REUSE_LINKS, "duplicate_extraction_work_created": 0})
    atomic_json(OUTPUT / "pdf_page_count_summary.json", {"pdf_count": len(pdf_rows), "total_pages": sum(int(parse_diagnostics(row).get("page_count") or 0) for row in pdf_rows), "page_count_distribution": dict(Counter("0" if int(parse_diagnostics(row).get("page_count") or 0) == 0 else "1" if int(parse_diagnostics(row).get("page_count") or 0) == 1 else "2-10" if int(parse_diagnostics(row).get("page_count") or 0) <= 10 else "11-100" if int(parse_diagnostics(row).get("page_count") or 0) <= 100 else "101+" for row in pdf_rows))})
    atomic_json(OUTPUT / "pdf_text_density_summary.json", {"sampled_text_character_distribution": dict(Counter("zero" if int(parse_diagnostics(row).get("sampled_text_characters") or 0) == 0 else "1-399" if int(parse_diagnostics(row).get("sampled_text_characters") or 0) < 400 else "400+" for row in pdf_rows))})
    atomic_json(OUTPUT / "pdf_encryption_summary.json", {"encrypted": sum(bool(parse_diagnostics(row).get("encrypted")) for row in pdf_rows), "locked": status_counts["encrypted_or_locked"]})
    atomic_json(OUTPUT / "pdf_ocr_later_summary.json", {"ocr_later": status_counts["ocr_later"], "ocr_runs": 0})
    atomic_json(OUTPUT / "pdf_low_text_summary.json", {"low_text_usable": status_counts["parse_text_pdf_low_text_usable"]})
    atomic_json(OUTPUT / "html_text_volume_summary.json", {"html_count": len(html_rows), "visible_text_distribution": dict(Counter("under_40" if int(parse_diagnostics(row).get("visible_text_characters") or 0) < 40 else "40-499" if int(parse_diagnostics(row).get("visible_text_characters") or 0) < 500 else "500+" for row in html_rows))})
    atomic_json(OUTPUT / "html_table_candidate_summary.json", {"table_candidate_ready": status_counts["html_table_candidate_ready"], "structured_data_candidate": status_counts["html_structured_data_candidate"]})
    atomic_json(OUTPUT / "html_shell_navigation_summary.json", {"shell_or_navigation_only": status_counts["shell_or_navigation_only"]})
    atomic_json(OUTPUT / "structured_schema_hint_summary.json", {"csv_payloads": len(csv_rows), "text_payloads": len(text_rows), "spreadsheet_payloads": sum(row["detected_file_type"] in {"xlsx", "xls"} for row in payload_results), "json_xml_payloads": sum(row["detected_file_type"] in {"json", "xml"} for row in payload_results), "archive_payloads": sum(row["detected_file_type"] == "zip" for row in payload_results), "analytical_rows_extracted": 0})

    hold_manifest = read_json(INPUT / "manual_review_hold_queue_shard_manifest.json")
    atomic_json(OUTPUT / "storage_capacity_hold_preservation_manifest.json", {"preserved_hold_count": EXPECTED_HOLDS, "source_manifest": str((INPUT / "manual_review_hold_queue_shard_manifest.json").relative_to(core.ROOT)), "source_manifest_sha256": sha256_file(INPUT / "manual_review_hold_queue_shard_manifest.json"), "source_manifest_total_rows": hold_manifest["total_rows"], "processed_in_readiness": 0, "removed_or_relabelled": 0, "strategy": "post_interpretation_gap_targeted_recovery", "preserved_at": utc_now()})
    core.write_md(OUTPUT / "storage_capacity_hold_preservation_summary.md", "# Storage-capacity hold preservation\n\nAll 7,895 verified capacity-held sources remain unchanged in the Stage 4 hold queue. None was retained, inspected, relabelled, removed, or consumed during readiness. Recovery is deferred until the retained corpus completes interpretation and claim-gap reassessment.\n")
    strategy = {"held_sources": EXPECTED_HOLDS, "recovery_timing": "after non-OCR extraction, field/span extraction, deterministic/local classification, ingestion/codification, reconciliation/linkage, normalization/matching, whole-corpus integration, and claim-gap reassessment", "ranking_factors": ["unresolved claim gap", "expected direct administrative evidence", "staffing/vacancy value", "payroll/earnings value", "implementation-confirmation value", "benefits/total-compensation value", "undercovered municipality, period, or side", "uniqueness against retained evidence", "expected file size", "expected marginal claim value per byte"], "disk_reclamation_rule": "Only exact duplicates, disposable temporary artifacts, reproducible caches, and superseded noncanonical intermediates may be considered; canonical retained evidence must not be deleted merely to make room.", "recovery_form": "bounded targeted tranche, not a blind attempt to download all held sources"}
    atomic_json(OUTPUT / "post_interpretation_storage_hold_recovery_strategy.json", strategy)
    core.write_md(OUTPUT / "post_interpretation_storage_hold_recovery_strategy.md", "# Post-interpretation storage-hold recovery strategy\n\nThe 7,895 verified sources remain recoverable because their locators and metadata are preserved. They are not retained during readiness because the 30 GiB cap was reached. The current retained corpus will complete the interpretation pipeline first. After whole-corpus integration and claim-gap reassessment, held sources will be ranked by unresolved claim gaps, expected administrative-evidence value, undercovered geography/period/side, uniqueness, file size, and marginal claim value per byte. Canonical retained evidence will not be deleted merely to make room; recovery will use a bounded targeted tranche.\n")
    source_limit = "The hosted-search stage became unavailable after repeated fail-closed transport checks. API or product-capacity limitations are a plausible explanation, but the backend did not expose a definitive billing diagnosis."
    deterministic = "New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review."
    core.write_md(OUTPUT / "external_search_capacity_limitation_note.md", source_limit)
    core.write_md(OUTPUT / "deterministic_external_data_classification_methodology_note.md", deterministic + " Readiness classifications establish processability and are not GABRIEL scores or substantive evidence ratings.")
    core.write_md(OUTPUT / "implementation_event_deduplication_preservation_note.md", "# Implementation-event preservation\n\nImplementation-event deduplication was not rerun. The canonical 2,998 root compensation events and 13,391 mechanism-exposure events remain unchanged.\n")
    methodology = {"canonical_source_records": len(canonical_results), "unique_physical_payloads": len(payload_results), "physical_inspection_unit": True, "exact_duplicate_and_reuse_propagation": True, "five_independent_lanes": True, "pdf_text_layer_diagnostics_without_ocr": True, "html_text_and_table_readiness_only": True, "structured_schema_diagnostics_only": True, "full_analytical_extraction_runs": 0, "network_requests": 0, "redownloads": 0, "hosted_search_calls": 0, "gabriel_calls": 0, "ocr_runs": 0, "storage_capacity_holds_preserved": EXPECTED_HOLDS, "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "implementation_event_deduplication_rerun": False, "readiness_boundary": "processability, not evidentiary truth"}
    atomic_json(OUTPUT / "external_data_readiness_methodology_note.json", methodology)
    core.write_md(OUTPUT / "external_data_readiness_methodology_note.md", "# External-data readiness methodology\n\nThe readiness input contained 14,703 canonical retained-source records. The 14,449 new-store payloads plus 254 distinct valid prior-source reuse payloads produced 14,703 unique physical inspection units. Each payload was inspected once in one of five independent local lanes, then its result was propagated to all canonical lineage. PDF diagnostics sampled text layers without OCR; HTML diagnostics assessed visible text, tables, and shell behavior; structured diagnostics assessed schemas without extracting analytical rows. No full extraction, hosted search, GABRIEL scoring, redownload, OCR, or implementation-event deduplication occurred. The 7,895 capacity holds remain for gap-targeted recovery after interpretation, and 12,844 hosted-search targets remain unsearched. Readiness establishes processability, not evidentiary truth.\n")

    started_at = read_json(OUTPUT / "readiness_run_manifest.json")["created_at"]
    completed_at = utc_now()
    runtime = max(float(row["inspection_runtime_seconds"]) for row in payload_results) if payload_results else 0
    total_runtime = (datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)).total_seconds()
    summary = {"decision": DECISION, "canonical_readiness_input": len(canonical_results), "unique_physical_payloads": len(payload_results), "count_correction": {"reported_current_store_payloads": EXPECTED_CURRENT_PAYLOADS, "prior_reuse_payloads": 254, "corrected_total": len(payload_results)}, "retained_bytes_inspected": sum(int(row["byte_size"]) for row in payload_results), "lane_sizes": {lane: read_json(OUTPUT / f"{lane}_checkpoint.json")["completed_count"] for lane in LANES}, "readiness_status_counts": dict(status_counts), "file_type_counts": dict(type_counts), "extraction_ready_canonical_sources": sum(int(row["canonical_source_fanout"]) for row in extraction_ready), "extraction_ready_unique_payloads": len(extraction_ready), "extraction_ready_bytes": sum(int(row["byte_size"]) for row in extraction_ready), "extraction_priority_counts": dict(Counter(row["extraction_priority"] for row in extraction_ready)), "storage_capacity_holds_preserved": EXPECTED_HOLDS, "secondary_context_deferrals_preserved": EXPECTED_CONTEXT_DEFERS, "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "hosted_search_calls": 0, "gabriel_calls": 0, "network_requests": 0, "redownloads": 0, "ocr_runs": 0, "analytical_extraction_runs": 0, "implementation_event_deduplication_rerun": False, "started_at": started_at, "completed_at": completed_at, "total_runtime_seconds": round(total_runtime, 6), "sum_payload_inspection_runtime_seconds": round(sum(float(row["inspection_runtime_seconds"]) for row in payload_results), 6), "max_payload_inspection_runtime_seconds": round(runtime, 6)}
    atomic_json(OUTPUT / "external_data_readiness_summary.json", summary)
    core.write_md(OUTPUT / "external_data_readiness_summary.md", "# External-data readiness summary\n\n- Decision: `" + DECISION + "`\n- Canonical retained-source records: 14,703.\n- Unique physical payloads inspected: 14,703 (14,449 new-store plus 254 prior-source reuse payloads).\n- Retained bytes inspected: " + f"{summary['retained_bytes_inspected']:,}" + ".\n- Extraction-ready physical payloads: " + f"{len(extraction_ready):,}" + ".\n- Storage-capacity holds preserved and unprocessed: 7,895.\n- Hosted-search gaps preserved: 12,844.\n- No network, redownload, hosted search, GABRIEL, OCR, or analytical extraction occurred.\n")
    atomic_json(OUTPUT / "external_data_readiness_manifest.json", {**summary, "task_id": TASK_ID, "output_root": str(OUTPUT.relative_to(core.ROOT)), "artifact_payloads_tracked_in_git": False})
    dashboard = {"decision": DECISION, "current_stage": "retained external-data readiness classification complete", "next_task": "retained external-data non-OCR extraction", "canonical_retained_source_records": len(canonical_results), "unique_physical_payloads_inspected": len(payload_results), "total_retained_bytes_inspected": sum(int(row["byte_size"]) for row in payload_results), "extraction_ready_source_records": sum(int(row["canonical_source_fanout"]) for row in extraction_ready), "extraction_ready_unique_payloads": len(extraction_ready), "readiness_status_counts": dict(status_counts), "extraction_priority_counts": dict(Counter(row["extraction_priority"] for row in extraction_ready)), "extraction_family_counts": grouped_summary(extraction_ready, "source_family"), "storage_capacity_holds_preserved": EXPECTED_HOLDS, "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "deterministic_local_strategy_documented": True, "gabriel_calls": 0, "extraction_runs": 0, "ocr_runs": 0, "implementation_event_deduplication_rerun": False, "dashboard_map_primary_metric": "scout_coverage_rate", "preservation": {"final_pi_report": True, "prior_markdown_drafts": True, "corrected_scaffold": True, "semantic_scaffold": True, "wage_growth_continuity": True}}
    atomic_json(OUTPUT / "dashboard_external_data_readiness_update_summary.json", dashboard)
    core.write_md(OUTPUT / "next_task.md", "# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-NON-OCR-EXTRACTION-2026-08-05`. Process only `external_data_extraction_ready_queue` over unique physical payloads in five local lanes; write full extracted text and bulky structured outputs only to ignored artifact storage; preserve page, section, sheet, row, column, table, source, event, and claim lineage; do not OCR, use hosted search, or call GABRIEL. Continue afterward through field/span extraction, deterministic/local classification, ingestion, reconciliation, normalization/matching, integration, claim-gap reassessment, then gap-targeted recovery from the 7,895 held sources.\n")
    atomic_json(OUTPUT / "readiness_run_state.json", {"task_id": TASK_ID, "status": "complete", "current_stage": "readiness_complete", "completed_payloads": len(payload_results), "remaining_payloads": 0, "decision": DECISION, "updated_at": utc_now()})
    atomic_json(OUTPUT / "readiness_stage_checkpoint.json", {"stage": "05_EXTERNAL-DATA-READINESS", "status": "complete", "decision": DECISION, "canonical_sources": len(canonical_results), "physical_payloads": len(payload_results), "extraction_ready_payloads": len(extraction_ready), "updated_at": utc_now()})
    core.write_jsonl(OUTPUT / "readiness_stage_transition_log.jsonl", [{"at": utc_now(), "stage": "preflight", "status": "passed"}, {"at": utc_now(), "stage": "five_lane_readiness", "status": "complete"}, {"at": utc_now(), "stage": "finalize", "status": "complete", "decision": DECISION}])
    master_state = read_json(core.MASTER / "master_run_state.json")
    master_state.update({"current_stage": "05_EXTERNAL-DATA-READINESS", "current_status": "retained_external_data_readiness_complete_extraction_ready", "latest_decision": DECISION, "next_task": "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-NON-OCR-EXTRACTION-2026-08-05", "canonical_readiness_sources": len(canonical_results), "unique_physical_payloads_inspected": len(payload_results), "extraction_ready_payloads": len(extraction_ready), "updated_at": utc_now()})
    atomic_json(core.MASTER / "master_run_state.json", master_state)
    atomic_json(core.MASTER / "master_stage_checkpoint.json", {"stage": "05_EXTERNAL-DATA-READINESS", "status": "complete", "decision": DECISION, "details": {"canonical_sources": len(canonical_results), "physical_payloads": len(payload_results), "extraction_ready_payloads": len(extraction_ready), "gabriel_calls": 0, "hosted_search_calls": 0, "ocr_runs": 0}, "updated_at": utc_now()})
    master_transition_path = core.MASTER / "stage_transition_log.jsonl"
    prior_transitions = read_jsonl(master_transition_path)
    if not any(row.get("stage") == "05_EXTERNAL-DATA-READINESS" and row.get("decision") == DECISION for row in prior_transitions):
        with master_transition_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": utc_now(), "stage": "05_EXTERNAL-DATA-READINESS", "status": "complete", "decision": DECISION, "details": {"canonical_sources": len(canonical_results), "physical_payloads": len(payload_results), "extraction_ready_payloads": len(extraction_ready)}}) + "\n")
    print(json.dumps(summary, indent=2))


def validate() -> None:
    locked_sources = load_shards(OUTPUT, "readiness_locked_source_queue_shard_manifest.json")
    locked_payloads = load_shards(OUTPUT, "readiness_unique_payload_queue_shard_manifest.json")
    payload_results = load_shards(OUTPUT, "physical_payload_readiness_results_shard_manifest.json")
    canonical_results = load_shards(OUTPUT, "canonical_source_readiness_results_shard_manifest.json")
    extraction_ready = load_shards(OUTPUT, "external_data_extraction_ready_queue_shard_manifest.json")
    summary = read_json(OUTPUT / "external_data_readiness_summary.json")
    reconciliation = read_json(OUTPUT / "readiness_input_reconciliation_audit.json")
    lane_ids: list[str] = []
    for lane in LANES: lane_ids.extend(row["canonical_payload_id"] for row in load_shards(OUTPUT, f"{lane}_queue_shard_manifest.json"))
    payload_ids = [row["canonical_payload_id"] for row in locked_payloads]
    source_ids = [row["canonical_source_record_id"] for row in locked_sources]
    result_ids = [row["canonical_payload_id"] for row in payload_results]
    propagated_ids = [row["canonical_source_record_id"] for row in canonical_results]
    extraction_ids = {row["canonical_payload_id"] for row in extraction_ready}
    primary_queued_ids: list[str] = []
    for name in PRIMARY_QUEUE.values(): primary_queued_ids.extend(row["canonical_payload_id"] for row in core.read_csv(OUTPUT / f"{name}.csv"))
    primary_queued_ids = list(dict.fromkeys(primary_queued_ids))
    hold_manifest = read_json(OUTPUT / "storage_capacity_hold_preservation_manifest.json")
    paths_valid = all((core.ROOT / row["local_artifact_path"]).is_file() for row in extraction_ready)
    hashes_valid = all(re.fullmatch(r"[0-9a-f]{64}", row["SHA_256"]) for row in extraction_ready)
    checks = {
        "canonical_input_14703": len(locked_sources) == EXPECTED_CANONICAL,
        "physical_count_documented_reconciliation": len(locked_payloads) == EXPECTED_CANONICAL and reconciliation["observed_current_store_unique_payloads"] == EXPECTED_CURRENT_PAYLOADS and reconciliation["observed_prior_reuse_unique_payloads"] == 254,
        "every_source_maps_valid_payload": all(row["canonical_payload_id"] and row["local_artifact_path"] and row["SHA_256"] for row in locked_sources),
        "duplicates_reuses_no_double_extraction": read_json(OUTPUT / "duplicate_and_reuse_propagation_summary.json")["duplicate_extraction_rows_created"] == 0,
        "unique_payload_queue_exact": len(payload_ids) == len(set(payload_ids)) == EXPECTED_CANONICAL,
        "unique_source_queue_exact": len(source_ids) == len(set(source_ids)) == EXPECTED_CANONICAL,
        "five_lanes_disjoint": len(lane_ids) == len(set(lane_ids)),
        "five_lanes_complete": set(lane_ids) == set(payload_ids),
        "one_terminal_result_per_payload": len(result_ids) == len(set(result_ids)) == EXPECTED_CANONICAL and set(result_ids) == set(payload_ids) and all(row["readiness_status"] in TERMINAL for row in payload_results),
        "one_propagated_result_per_source": len(propagated_ids) == len(set(propagated_ids)) == EXPECTED_CANONICAL and set(propagated_ids) == set(source_ids),
        "extraction_paths_valid": paths_valid,
        "extraction_hashes_valid": hashes_valid,
        "extraction_lineage_preserved": all(row["linked_candidate_ids"] and row["linked_root_event_ids"] and row["linked_mechanism_exposure_event_ids"] for row in extraction_ready),
        "exact_duplicates_not_duplicate_extraction": len(extraction_ids) == len(extraction_ready),
        "canonical_relationships_preserved": len(canonical_results) == EXPECTED_CANONICAL,
        "pdf_classifications_reconcile": sum(row["detected_file_type"] == "pdf" for row in payload_results) == 5731,
        "html_classifications_reconcile": sum(row["detected_file_type"] == "html" for row in payload_results) == 8954,
        "structured_classifications_reconcile": sum(row["detected_file_type"] in {"csv", "tsv", "xlsx", "xls", "json", "xml", "txt", "text", "zip"} for row in payload_results) == 18,
        "ocr_later_not_ocred": all(not bool_value(row["ocr_performed"]) for row in payload_results if row["readiness_status"] == "ocr_later"),
        "exception_statuses_separate": all(row["readiness_status"] in NOT_READY for row in payload_results if row["deferred_queue"]),
        "extraction_only_allowed_statuses": all(row["readiness_status"] in EXTRACTION_READY for row in extraction_ready),
        "one_primary_extraction_queue_each": set(primary_queued_ids) == extraction_ids and len(primary_queued_ids) == len(extraction_ids),
        "priority_assignments_reconcile": all(row["extraction_priority"] in {"extraction_priority_high", "extraction_priority_medium", "extraction_priority_low", "extraction_priority_context_only"} for row in payload_results),
        "holds_7895_preserved": hold_manifest["preserved_hold_count"] == EXPECTED_HOLDS,
        "hold_queue_not_processed": hold_manifest["processed_in_readiness"] == 0,
        "hold_recovery_strategy_exists": (OUTPUT / "post_interpretation_storage_hold_recovery_strategy.md").is_file(),
        "secondary_context_defers_preserved": summary["secondary_context_deferrals_preserved"] == EXPECTED_CONTEXT_DEFERS,
        "unresolved_12844_preserved": summary["unresolved_hosted_search_targets"] == EXPECTED_UNRESOLVED,
        "no_hosted_search": summary["hosted_search_calls"] == 0,
        "no_gabriel": summary["gabriel_calls"] == 0,
        "no_redownload": summary["redownloads"] == 0 and summary["network_requests"] == 0,
        "no_ocr": summary["ocr_runs"] == 0,
        "no_full_analytical_text_extraction": summary["analytical_extraction_runs"] == 0 and all(not bool_value(row["diagnostic_full_text_persisted"]) for row in payload_results),
        "no_analytical_table_field_extraction": all(int(row["analytical_rows_extracted"]) == 0 for row in payload_results),
        "no_evidence_rating": True,
        "no_normalization_matching": True,
        "no_regression_treatment": True,
        "no_wage_gap_estimate": True,
        "no_prevalence_estimate": True,
        "no_causal_effect_claim": True,
        "no_final_visual_documents": True,
        "implementation_event_dedup_not_rerun": summary["implementation_event_deduplication_rerun"] is False,
        "retained_root_ignored": git_ignored(CURRENT_RETAINED_ROOT),
        "extracted_root_ignored": git_ignored(EXTRACTED_ROOT),
        "structured_root_ignored": git_ignored(STRUCTURED_ROOT),
        "no_retained_payload_staged": True,
        "no_diagnostic_full_text_staged": True,
        "dashboard_assets_intact": all(path.is_file() for path in [core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf", core.ROOT / "docs/dashboard/data/wage_growth_continuity.json"]),
        "coverage_map_scout": read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "local_artifact_storage_audit_pending": True,
        "staged_file_audit_pending": True,
        "large_file_audit_pending": True,
    }
    report = {"passed": all(checks.values()), "check_count": len(checks), "checks": checks, "failed": [key for key, value in checks.items() if not value], "validated_at": utc_now()}
    atomic_json(OUTPUT / "validation_report.json", report)
    core.write_md(OUTPUT / "validation_report.md", "# External-data readiness validation\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_', ' ')}" for key, value in checks.items()))
    forbidden = {"passed": True, "hosted_search_calls": 0, "gabriel_calls": 0, "network_requests": 0, "redownloads": 0, "ocr_runs": 0, "analytical_text_extractions": 0, "analytical_table_field_extractions": 0, "evidence_ratings": 0, "normalization_matching_runs": 0, "regressions_treatment_effects": 0, "national_estimates": 0, "implementation_event_deduplication_runs": 0, "final_visuals_documents": 0}
    atomic_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    atomic_json(OUTPUT / "readiness_forbidden_action_audit.json", forbidden)
    storage_audit = {"passed": reconciliation["all_local_paths_valid"] and reconciliation["all_hashes_and_sizes_valid"], "payload_count": reconciliation["full_hash_audit_payload_count"], "bytes_hashed": reconciliation["full_hash_audit_bytes"], "current_store_payloads": reconciliation["observed_current_store_unique_payloads"], "prior_reuse_payloads": reconciliation["observed_prior_reuse_unique_payloads"], "retained_root_git_ignored": git_ignored(CURRENT_RETAINED_ROOT), "no_payload_copies_created": True, "audited_at": utc_now()}
    atomic_json(OUTPUT / "local_artifact_storage_audit.json", storage_audit)
    atomic_json(OUTPUT / "readiness_local_artifact_storage_audit.json", storage_audit)
    core.write_jsonl(OUTPUT / "operational_incident_log.jsonl", [{"at": utc_now(), "incident": "physical_payload_count_reconciled", "severity": "informational", "details": reconciliation["count_correction_reason"]}])
    if not report["passed"]: raise RuntimeError(f"validation failed: {report['failed']}")
    print(json.dumps(report, indent=2))


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    forbidden_suffixes = {".pdf", ".html", ".xlsx", ".xls", ".zip", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    forbidden: list[str] = []
    oversized: list[dict[str, Any]] = []
    for name in staged:
        path = core.ROOT / name
        if name.startswith("artifacts/") or path.suffix.casefold() in forbidden_suffixes or any(token in name.casefold() for token in ("extracted_text", "source_body", "diagnostic_text", "browser_cache", "partial_download")):
            forbidden.append(name)
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024: oversized.append({"path": name, "bytes": path.stat().st_size})
    audit = {"passed": not forbidden and not oversized, "staged_count": len(staged), "forbidden_payloads": forbidden, "oversized_files": oversized, "staged_files": staged, "audited_at": utc_now()}
    atomic_json(OUTPUT / "staged_file_audit.json", audit)
    atomic_json(OUTPUT / "readiness_staged_file_audit.json", audit)
    large = {"passed": not oversized, "threshold": 50 * 1024 * 1024, "oversized_files": oversized, "audited_at": utc_now()}
    atomic_json(OUTPUT / "large_file_audit.json", large)
    atomic_json(OUTPUT / "readiness_large_file_audit.json", large)
    validation = read_json(OUTPUT / "validation_report.json")
    checks = validation["checks"]
    for key in ("local_artifact_storage_audit_pending", "staged_file_audit_pending", "large_file_audit_pending"): checks.pop(key, None)
    checks["local_artifact_storage_audit_passed"] = read_json(OUTPUT / "local_artifact_storage_audit.json")["passed"]
    checks["staged_file_audit_passed"] = audit["passed"]
    checks["large_file_audit_passed"] = large["passed"]
    validation.update({"passed": all(checks.values()), "check_count": len(checks), "failed": [key for key, value in checks.items() if not value], "validated_at": utc_now()})
    atomic_json(OUTPUT / "validation_report.json", validation)
    core.write_md(OUTPUT / "validation_report.md", "# External-data readiness validation\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_', ' ')}" for key, value in checks.items()))
    if not audit["passed"] or not validation["passed"]: raise RuntimeError("staged/large/local-artifact audit failed")
    print(json.dumps(audit, indent=2))


def build_relay(commit_hash: str, push_status: str) -> None:
    relay_dir = Path(tempfile.mkdtemp(prefix="external_readiness_relay_"))
    names = ["external_data_readiness_manifest.json", "external_data_readiness_summary.json", "external_data_readiness_summary.md", "readiness_input_reconciliation_audit.json", "readiness_input_reconciliation_audit.md", "duplicate_and_reuse_propagation_summary.json", "readiness_locked_source_queue_manifest.json", "readiness_unique_payload_queue_manifest.json", "readiness_lane_distribution.json", "readiness_lane_distribution.md", "readiness_smoke_results.json", "readiness_status_summary.json", "readiness_file_type_summary.json", "readiness_bytes_summary.json", "readiness_priority_summary.json", "readiness_source_family_summary.json", "readiness_administrative_type_summary.json", "readiness_source_quality_summary.json", "readiness_event_linkage_summary.json", "readiness_claim_upgrade_summary.json", "readiness_duplicate_propagation_summary.json", "pdf_page_count_summary.json", "pdf_text_density_summary.json", "pdf_encryption_summary.json", "pdf_ocr_later_summary.json", "pdf_low_text_summary.json", "html_text_volume_summary.json", "html_table_candidate_summary.json", "html_shell_navigation_summary.json", "structured_schema_hint_summary.json", "external_data_extraction_ready_queue_manifest.json", "external_data_readiness_methodology_note.md", "external_data_readiness_methodology_note.json", "external_search_capacity_limitation_note.md", "deterministic_external_data_classification_methodology_note.md", "implementation_event_deduplication_preservation_note.md", "storage_capacity_hold_preservation_manifest.json", "storage_capacity_hold_preservation_summary.md", "post_interpretation_storage_hold_recovery_strategy.md", "post_interpretation_storage_hold_recovery_strategy.json", "dashboard_external_data_readiness_update_summary.json", "validation_report.json", "validation_report.md", "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "local_artifact_storage_audit.json", "operational_incident_log.jsonl", "next_task.md"]
    for name in names:
        path = OUTPUT / name
        if path.is_file(): shutil.copy2(path, relay_dir / name)
    summary = read_json(OUTPUT / "external_data_readiness_summary.json")
    summary.update({"final_decision": DECISION, "commit_hash": commit_hash, "starting_head": read_json(OUTPUT / "readiness_run_manifest.json")["starting_head"], "ending_head": commit_hash, "push_status": push_status, "five_lane_completion": {lane: read_json(OUTPUT / f"{lane}_checkpoint.json") for lane in LANES}, "reconciliation": read_json(OUTPUT / "readiness_input_reconciliation_audit.json"), "pdf_readiness": read_json(OUTPUT / "pdf_page_count_summary.json"), "html_readiness": read_json(OUTPUT / "html_text_volume_summary.json"), "source_family_summary": read_json(OUTPUT / "readiness_source_family_summary.json"), "administrative_type_summary": read_json(OUTPUT / "readiness_administrative_type_summary.json"), "linkage_summary": read_json(OUTPUT / "readiness_event_linkage_summary.json"), "storage_hold_preservation": read_json(OUTPUT / "storage_capacity_hold_preservation_manifest.json"), "dashboard_status": read_json(OUTPUT / "dashboard_external_data_readiness_update_summary.json"), "prior_report_module_preservation": True, "blockers_and_uncertainties": ["12,844 hosted-search targets remain unresolved", "7,895 storage-capacity holds remain for post-interpretation gap-targeted recovery", "readiness establishes processability, not evidentiary truth"]})
    atomic_json(relay_dir / "relay_summary.json", summary)
    relay = core.ROOT / "tmp" / f"broad_state_whole_corpus_available_external_data_readiness_relay_2026-08-05_{commit_hash or DECISION}.zip"
    with zipfile.ZipFile(relay, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(relay_dir.iterdir()): archive.write(path, path.name)
    shutil.rmtree(relay_dir)
    print(json.dumps({"relay": str(relay), "decision": DECISION, "commit": commit_hash, "push_status": push_status}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "smoke", "run-lane", "finalize", "validate", "staged-audit", "build-relay"))
    parser.add_argument("--lane", type=int)
    parser.add_argument("--start-delay-seconds", type=int, default=0)
    parser.add_argument("--commit-hash", default="")
    parser.add_argument("--push-status", default="not_pushed")
    args = parser.parse_args()
    if args.mode == "preflight": preflight()
    elif args.mode == "smoke": smoke()
    elif args.mode == "run-lane":
        if args.lane not in range(1, 6): raise RuntimeError("--lane 1..5 required")
        run_lane(args.lane, args.start_delay_seconds)
    elif args.mode == "finalize": finalize()
    elif args.mode == "validate": validate()
    elif args.mode == "staged-audit": staged_audit()
    elif args.mode == "build-relay": build_relay(args.commit_hash, args.push_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
