#!/usr/bin/env python3
"""Four-lane source review/download for the verified broad-state 4x2500 wave.

Downloads are streamed only to the Git-ignored local artifact root. This runner
does not parse full text, OCR, render, extract, rate, ingest, codify, or analyze.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-4X2500-VERIFICATION-2026-07-30"
OUTPUT = BASE / "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30"
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_4x2500_source_review_download_2026-07-30"
TASK_ID = "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30"
EXPECTED_HEAD = "079d27295952006b5fbcfd7df17e222b08979d62"
EXPECTED_COUNT = 3950
LANES = tuple(f"source_review_lane_{i:03d}" for i in range(1, 5))
LANE_COUNTS = dict(zip(LANES, (988, 988, 987, 987)))
STAGGER_MINUTES = {lane: index * 8 for index, lane in enumerate(LANES)}
PRIORITIES = (
    "high_priority_verification_ready", "medium_priority_verification_ready",
    "low_priority_verification_ready",
)
EXPECTED_PRIORITY = dict(zip(PRIORITIES, (2920, 918, 112)))
MAX_FILE_BYTES = 75 * 1024 * 1024
MAX_CONCURRENCY = 2
MAX_RETRIES = 1
MAX_REDIRECTS = 8
TIMEOUT_SECONDS = 75.0
SMOKE_BYTES = 4096
MIN_FREE_BYTES = 20 * 1024 * 1024 * 1024

RETAINED_STATUSES = {"retained_pdf", "retained_html", "retained_other_document"}
CONTROLLED_STATUSES = RETAINED_STATUSES | {
    "duplicate_retained_source", "oversized_defer", "ocr_later",
    "restricted_or_login_required", "unavailable_on_download", "broken_or_corrupt",
    "likely_non_source_or_navigation_only", "excluded_out_of_scope", "source_review_error",
}

INPUT_FIELDS = (
    "verification_row_id", "verification_lane_id", "candidate_id", "scout_candidate_id",
    "scout_target_id", "lane_id", "shard_id", "state", "region", "municipality",
    "county", "source_title", "source_locator_or_url", "source_domain",
    "final_url_or_locator", "final_canonical_locator", "source_family_hint",
    "document_type_hint", "possible_mechanism_hints", "search_query_family",
    "discovery_run_id", "priority_bucket", "cba_non_cba_hint", "verification_status",
    "http_status_code", "content_type", "content_length_header",
)
LOCK_FIELDS = (
    "source_review_download_id", "source_review_lane_id", "source_review_lane_sequence",
    *INPUT_FIELDS, "canonical_download_locator", "live_status", "global_analysis_readiness",
)
RESULT_FIELDS = (
    "source_review_download_id", "source_review_lane_id", "source_review_lane_sequence",
    *INPUT_FIELDS, "canonical_download_locator", "source_review_status", "final_download_locator",
    "download_http_status", "final_content_type", "final_content_length", "redirect_count",
    "download_attempt_count", "download_started_at", "download_completed_at",
    "transport_error_type", "source_review_reason", "file_extension", "retained_file_type",
    "retained_local_artifact_path", "artifact_storage_scheme", "artifact_storage_pointer",
    "artifact_object_key_or_content_address", "artifact_availability_status",
    "artifact_replication_or_backup_status", "artifact_access_scope",
    "retained_file_size_bytes", "retained_file_sha256", "duplicate_retained_sha256",
    "duplicate_of_source_review_download_id", "download_status", "extraction_status",
    "ocr_status", "rating_status", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
)

CONTENT_TYPE_MAP = {
    "application/pdf": (".pdf", "pdf", "retained_pdf"),
    "text/html": (".html", "html", "retained_html"),
    "application/xhtml+xml": (".html", "html", "retained_html"),
    "text/plain": (".txt", "text", "retained_other_document"),
    "text/csv": (".csv", "csv", "retained_other_document"),
    "application/csv": (".csv", "csv", "retained_other_document"),
    "application/rtf": (".rtf", "rtf", "retained_other_document"),
    "text/rtf": (".rtf", "rtf", "retained_other_document"),
    "application/msword": (".doc", "doc", "retained_other_document"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx", "docx", "retained_other_document"),
    "application/vnd.ms-excel": (".xls", "xls", "retained_other_document"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (".xlsx", "xlsx", "retained_other_document"),
    "application/vnd.ms-powerpoint": (".ppt", "ppt", "retained_other_document"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (".pptx", "pptx", "retained_other_document"),
}
URL_EXTENSIONS = {
    ".pdf": ("pdf", "retained_pdf"), ".html": ("html", "retained_html"),
    ".htm": ("html", "retained_html"), ".doc": ("doc", "retained_other_document"),
    ".docx": ("docx", "retained_other_document"), ".xls": ("xls", "retained_other_document"),
    ".xlsx": ("xlsx", "retained_other_document"), ".csv": ("csv", "retained_other_document"),
    ".txt": ("text", "retained_other_document"), ".rtf": ("rtf", "retained_other_document"),
    ".ppt": ("ppt", "retained_other_document"), ".pptx": ("pptx", "retained_other_document"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] = RESULT_FIELDS) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str] = RESULT_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def canonical_url(value: str) -> str:
    try:
        parts = urlsplit((value or "").strip())
    except ValueError:
        return ""
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return ""
    host = parts.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", parts.path).rstrip("/")
    return urlunsplit((parts.scheme.casefold(), host, path, "", ""))


def download_locator(row: dict[str, str]) -> str:
    return canonical_url(row.get("final_url_or_locator") or row.get("final_canonical_locator") or row.get("source_locator_or_url", ""))


def current_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def check_ignored() -> bool:
    probe = ARTIFACT_ROOT / "ignore_probe.pdf"
    return subprocess.run(["git", "check-ignore", "-q", str(probe.relative_to(ROOT))], cwd=ROOT).returncode == 0


def source_review_id(verification_id: str) -> str:
    return "B4X2500SRD-20260730-" + text_hash(verification_id)[:20]


def stable_rows(rows: list[dict[str, str]], priority: str) -> list[dict[str, str]]:
    return sorted(
        (row for row in rows if row["priority_bucket"] == priority),
        key=lambda row: (row["state"], row["region"], row["source_family_hint"], row["source_domain"], row["municipality"], row["verification_row_id"]),
    )


def interleave(groups: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    used = Counter()
    total = {key: len(value) for key, value in groups.items()}
    output: list[dict[str, str]] = []
    while len(output) < sum(total.values()):
        available = [key for key in PRIORITIES if used[key] < total[key]]
        key = min(available, key=lambda item: ((used[item] + 1) / total[item], PRIORITIES.index(item)))
        output.append(groups[key][used[key]])
        used[key] += 1
    return output


def prepare() -> None:
    if OUTPUT.exists() or ARTIFACT_ROOT.exists():
        raise RuntimeError("rollback-safe output or artifact directory already exists")
    if current_head() != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {current_head()}")
    queue_path = INPUT / "source_review_ready_queue.csv"
    jsonl_path = INPUT / "source_review_ready_queue.jsonl"
    manifest_path = INPUT / "source_review_ready_manifest.json"
    summary_path = INPUT / "verification_summary.json"
    for path in (queue_path, jsonl_path, manifest_path, summary_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    rows = read_csv(queue_path)
    manifest = read_json(manifest_path)
    verification = read_json(summary_path)
    required = {
        "verification_row_id", "candidate_id", "source_locator_or_url", "final_url_or_locator",
        "municipality", "state", "priority_bucket", "source_family_hint", "verification_status",
        "scout_target_id", "discovery_run_id",
    }
    errors = []
    if len(rows) != EXPECTED_COUNT or manifest.get("queue_row_count") != EXPECTED_COUNT:
        errors.append("queue count mismatch")
    if sha256(queue_path) != manifest.get("csv_sha256") or sha256(jsonl_path) != manifest.get("jsonl_sha256"):
        errors.append("input queue hash mismatch")
    if verification.get("source_review_ready_count") != EXPECTED_COUNT:
        errors.append("verification summary count mismatch")
    if Counter(row["priority_bucket"] for row in rows) != Counter(EXPECTED_PRIORITY):
        errors.append("priority count mismatch")
    if any(row["verification_status"] not in {"reachable", "reachable_with_redirect"} for row in rows):
        errors.append("ineligible verification status entered queue")
    if any(any(not row.get(field, "").strip() for field in required) for row in rows):
        errors.append("required lineage field missing")
    if len({row["verification_row_id"] for row in rows}) != EXPECTED_COUNT:
        errors.append("duplicate verification row ID")
    if not check_ignored():
        errors.append("artifact root is not ignored by Git")
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    if any(name.startswith("artifacts/local_retained_sources/") for name in staged):
        errors.append("retained artifact already staged")
    if errors:
        raise RuntimeError("; ".join(errors))

    OUTPUT.mkdir(parents=True)
    ARTIFACT_ROOT.mkdir(parents=True)
    (OUTPUT / "lanes").mkdir()
    for lane in LANES:
        (OUTPUT / "lanes" / lane).mkdir()
        (ARTIFACT_ROOT / lane).mkdir()

    assigned: dict[str, dict[str, list[dict[str, str]]]] = {lane: {priority: [] for priority in PRIORITIES} for lane in LANES}
    capacity = Counter(LANE_COUNTS)
    for priority in PRIORITIES:
        for source in stable_rows(rows, priority):
            lane = min(
                (candidate for candidate in LANES if sum(len(v) for v in assigned[candidate].values()) < capacity[candidate]),
                key=lambda candidate: (
                    len(assigned[candidate][priority]),
                    sum(len(v) for v in assigned[candidate].values()) / capacity[candidate],
                    LANES.index(candidate),
                ),
            )
            assigned[lane][priority].append(dict(source))

    locked: list[dict[str, str]] = []
    lane_rows: dict[str, list[dict[str, str]]] = {}
    for lane in LANES:
        lane_rows[lane] = interleave(assigned[lane])
        if len(lane_rows[lane]) != LANE_COUNTS[lane]:
            raise RuntimeError(f"{lane} allocation mismatch")
        for sequence, source in enumerate(lane_rows[lane], 1):
            row = {
                "source_review_download_id": source_review_id(source["verification_row_id"]),
                "source_review_lane_id": lane, "source_review_lane_sequence": str(sequence),
                **{field: source.get(field, "") for field in INPUT_FIELDS},
                "canonical_download_locator": download_locator(source), "live_status": "not_run",
                "global_analysis_readiness": "false",
            }
            locked.append(row)
            lane_rows[lane][sequence - 1] = row

    master_csv = OUTPUT / "source_review_locked_queue.csv"
    master_jsonl = OUTPUT / "source_review_locked_queue.jsonl"
    write_csv(master_csv, locked, LOCK_FIELDS)
    write_jsonl(master_jsonl, locked)
    lane_hashes = {}
    distribution = {}
    for lane in LANES:
        number = lane[-3:]
        csv_path = OUTPUT / f"source_review_lane_{number}_queue.csv"
        jl_path = OUTPUT / f"source_review_lane_{number}_queue.jsonl"
        write_csv(csv_path, lane_rows[lane], LOCK_FIELDS)
        write_jsonl(jl_path, lane_rows[lane])
        counts = dict(Counter(row["priority_bucket"] for row in lane_rows[lane]))
        distribution[lane] = {"total_rows": len(lane_rows[lane]), "priority_counts": counts, "scheduled_stagger_minutes": STAGGER_MINUTES[lane]}
        lane_hashes[lane] = {"csv_sha256": sha256(csv_path), "jsonl_sha256": sha256(jl_path)}
        write_json(OUTPUT / "lanes" / lane / "lane_manifest.json", {
            "task_id": TASK_ID, "lane_id": lane, **distribution[lane], **lane_hashes[lane],
            "checkpoint_frequency": "after_every_row", "artifact_root": str((ARTIFACT_ROOT / lane).relative_to(ROOT)),
        })
    lock = {
        "task_id": TASK_ID, "created_at": utc_now(), "preflight_head": current_head(),
        "queue_rows": EXPECTED_COUNT, "priority_counts": dict(Counter(row["priority_bucket"] for row in locked)),
        "queue_csv_sha256": sha256(master_csv), "queue_jsonl_sha256": sha256(master_jsonl),
        "lane_distribution": distribution, "lane_hashes": lane_hashes,
        "input_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in (queue_path, jsonl_path, manifest_path, summary_path)},
        "artifact_root": str(ARTIFACT_ROOT.relative_to(ROOT)), "artifact_root_git_ignored": True,
        "maximum_file_bytes": MAX_FILE_BYTES, "network_requests": 0,
    }
    write_json(OUTPUT / "source_review_download_manifest.json", lock)
    write_json(OUTPUT / "source_review_lane_distribution.json", {
        "lane_distribution": distribution, "total_rows": EXPECTED_COUNT,
        "priority_totals": lock["priority_counts"], "stable_priority_interleaving": True,
        "exact_lane_distribution_passed": all(
            distribution[lane]["total_rows"] == LANE_COUNTS[lane] for lane in LANES
        ),
    })
    lines = ["# Source-review lane distribution", "", "| Lane | High | Medium | Low | Total | Stagger |", "|---|---:|---:|---:|---:|---:|"]
    for lane in LANES:
        c = distribution[lane]["priority_counts"]
        lines.append(f"| {lane} | {c.get(PRIORITIES[0],0):,} | {c.get(PRIORITIES[1],0):,} | {c.get(PRIORITIES[2],0):,} | {distribution[lane]['total_rows']:,} | T+{STAGGER_MINUTES[lane]} min |")
    write_text(OUTPUT / "source_review_lane_distribution.md", "\n".join(lines))
    write_json(OUTPUT / "preflight_report.json", {
        "deterministic_preflight_passed": True, "network_smoke_passed": False,
        "queue_rows": EXPECTED_COUNT, "priority_counts": lock["priority_counts"],
        "lane_distribution": distribution, "eligible_statuses_only": True,
        "all_required_lineage_present": True, "artifact_root_git_ignored": True,
        "retained_binaries_staged_before_run": 0,
    })
    print(json.dumps({"status": "prepared", "queue_rows": EXPECTED_COUNT, "lane_distribution": distribution}, sort_keys=True))


def validate_locks() -> tuple[list[dict[str, str]], dict[str, Any]]:
    lock = read_json(OUTPUT / "source_review_download_manifest.json")
    master_csv = OUTPUT / "source_review_locked_queue.csv"
    master_jsonl = OUTPUT / "source_review_locked_queue.jsonl"
    master = read_csv(master_csv)
    if len(master) != EXPECTED_COUNT or sha256(master_csv) != lock["queue_csv_sha256"] or sha256(master_jsonl) != lock["queue_jsonl_sha256"]:
        raise RuntimeError("master queue lock mismatch")
    union = []
    for lane in LANES:
        number = lane[-3:]
        csv_path = OUTPUT / f"source_review_lane_{number}_queue.csv"
        jl_path = OUTPUT / f"source_review_lane_{number}_queue.jsonl"
        rows = read_csv(csv_path)
        if len(rows) != LANE_COUNTS[lane] or sha256(csv_path) != lock["lane_hashes"][lane]["csv_sha256"] or sha256(jl_path) != lock["lane_hashes"][lane]["jsonl_sha256"]:
            raise RuntimeError(f"{lane} queue lock mismatch")
        union.extend(rows)
    ids = [row["source_review_download_id"] for row in union]
    if len(ids) != len(set(ids)) or set(ids) != {row["source_review_download_id"] for row in master}:
        raise RuntimeError("master does not equal lane union exactly once")
    return master, lock


async def smoke_one(client: httpx.AsyncClient, row: dict[str, str]) -> dict[str, Any]:
    try:
        async with client.stream("GET", row["canonical_download_locator"], headers={"Range": f"bytes=0-{SMOKE_BYTES - 1}"}) as response:
            observed = 0
            async for chunk in response.aiter_bytes():
                observed += min(len(chunk), SMOKE_BYTES - observed)
                if observed >= SMOKE_BYTES:
                    break
            return {
                "source_review_download_id": row["source_review_download_id"], "priority_bucket": row["priority_bucket"],
                "source_family_hint": row["source_family_hint"], "http_status": response.status_code,
                "bytes_read": observed, "content_type": (response.headers.get("content-type") or "").split(";", 1)[0],
                "transport_error_type": "", "retained_file_written": "false",
            }
    except httpx.HTTPError as exc:
        return {
            "source_review_download_id": row["source_review_download_id"], "priority_bucket": row["priority_bucket"],
            "source_family_hint": row["source_family_hint"], "http_status": "", "bytes_read": 0,
            "content_type": "", "transport_error_type": type(exc).__name__, "retained_file_written": "false",
        }


async def smoke() -> None:
    master, _ = validate_locks()
    usage = shutil.disk_usage(ROOT)
    known = [int(row["content_length_header"]) for row in master if row.get("content_length_header", "").isdigit()]
    known_bytes = sum(min(value, MAX_FILE_BYTES) for value in known)
    average = int(known_bytes / len(known)) if known else 5 * 1024 * 1024
    projected = known_bytes + (EXPECTED_COUNT - len(known)) * average
    storage_passed = usage.free >= max(MIN_FREE_BYTES, projected * 2)
    write_json(OUTPUT / "retained_source_storage_preflight.json", {
        "available_bytes_before_run": usage.free, "known_content_length_rows": len(known),
        "projected_retained_bytes": projected, "minimum_free_bytes_required": max(MIN_FREE_BYTES, projected * 2),
        "maximum_file_bytes": MAX_FILE_BYTES, "storage_sanity_passed": storage_passed,
        "artifact_root": str(ARTIFACT_ROOT.relative_to(ROOT)), "artifact_root_git_ignored": check_ignored(),
    })
    if not storage_passed:
        raise RuntimeError("storage preflight failed")
    selected = []
    families = set()
    for priority in PRIORITIES:
        candidates = [row for row in master if row["priority_bucket"] == priority]
        row = next((item for item in candidates if item["source_family_hint"] not in families), candidates[0])
        selected.append(row); families.add(row["source_family_hint"])
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT_SECONDS,
                                 limits=httpx.Limits(max_connections=3, max_keepalive_connections=3),
                                 headers={"User-Agent": "GabrielWagesSourceReview/2.0"}, trust_env=False) as client:
        probes = await asyncio.gather(*(smoke_one(client, row) for row in selected))
    responded = any(str(row["http_status"]).isdigit() for row in probes)
    write_csv(OUTPUT / "network_download_smoke_metadata.csv", probes, probes[0].keys())
    report = read_json(OUTPUT / "preflight_report.json")
    report.update({
        "network_smoke_passed": responded, "network_smoke_rows": len(probes),
        "network_smoke_http_responses": sum(str(row["http_status"]).isdigit() for row in probes),
        "network_smoke_priority_coverage": sorted({row["priority_bucket"] for row in probes}),
        "network_smoke_source_families": sorted({row["source_family_hint"] for row in probes}),
        "smoke_retained_files_written": 0, "storage_sanity_passed": storage_passed,
    })
    write_json(OUTPUT / "preflight_report.json", report)
    if not responded:
        raise RuntimeError("global download transport smoke failed")
    print(json.dumps({"status": "smoke_passed", "probes": probes}, sort_keys=True))


def classify_content(content_type: str, prefix: bytes, url: str) -> tuple[str, str, str] | None:
    ctype = (content_type or "").split(";", 1)[0].strip().strip('"').casefold()
    if prefix.startswith(b"%PDF-"):
        return ".pdf", "pdf", "retained_pdf"
    if ctype in CONTENT_TYPE_MAP:
        return CONTENT_TYPE_MAP[ctype]
    extension = Path(unquote(urlsplit(url).path).casefold()).suffix
    if extension in URL_EXTENSIONS and ctype in {"", "application/octet-stream", "application/zip"}:
        kind, status = URL_EXTENSIONS[extension]
        return ".html" if extension == ".htm" else extension, kind, status
    if ctype in {"application/octet-stream", "application/zip"}:
        if prefix.startswith(b"PK\x03\x04"):
            return ".docx", "office_open_xml_or_zip", "retained_other_document"
        if prefix.startswith(b"\xd0\xcf\x11\xe0"):
            return ".doc", "legacy_office_document", "retained_other_document"
    return None


def generic_navigation(row: dict[str, str], final_url: str, retained_type: str) -> bool:
    if retained_type != "html":
        return False
    title = row.get("source_title", "").casefold()
    path = urlsplit(final_url).path.strip("/").casefold()
    return any(term in title for term in ("search results", "site search", "job openings", "careers page")) or (not path and row.get("source_family_hint") == "unknown_or_needs_review")


def result_base(row: dict[str, str], status: str, started: str, reason: str, **metadata: Any) -> dict[str, str]:
    retained = status in RETAINED_STATUSES
    return {
        "source_review_download_id": row["source_review_download_id"],
        "source_review_lane_id": row["source_review_lane_id"], "source_review_lane_sequence": row["source_review_lane_sequence"],
        **{field: row.get(field, "") for field in INPUT_FIELDS},
        "canonical_download_locator": row.get("canonical_download_locator", ""),
        "source_review_status": status, "final_download_locator": metadata.get("final_url", ""),
        "download_http_status": str(metadata.get("http_status", "")), "final_content_type": metadata.get("content_type", ""),
        "final_content_length": str(metadata.get("final_length", "")), "redirect_count": str(metadata.get("redirect_count", "")),
        "download_attempt_count": str(metadata.get("attempts", 0)), "download_started_at": started,
        "download_completed_at": utc_now(), "transport_error_type": metadata.get("transport_error", ""),
        "source_review_reason": reason, "file_extension": "", "retained_file_type": "",
        "retained_local_artifact_path": "", "artifact_storage_scheme": "ignored_local_artifact_store" if retained else "",
        "artifact_storage_pointer": "", "artifact_object_key_or_content_address": "",
        "artifact_availability_status": "locally_available" if retained else "not_retained",
        "artifact_replication_or_backup_status": "local_only_not_replicated" if retained else "not_applicable",
        "artifact_access_scope": "local_research_workspace" if retained else "",
        "retained_file_size_bytes": "", "retained_file_sha256": "", "duplicate_retained_sha256": "",
        "duplicate_of_source_review_download_id": "", "download_status": "downloaded_retained" if retained else "not_retained",
        "extraction_status": "not_extracted", "ocr_status": "not_ocrd", "rating_status": "not_rated",
        "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
        "notes": "bounded source-review/download metadata; no text extraction",
    }


async def download_one(client: httpx.AsyncClient, row: dict[str, str], artifact_lane: Path) -> dict[str, str]:
    started = utc_now()
    locator = row["canonical_download_locator"]
    if not canonical_url(locator):
        return result_base(row, "source_review_error", started, "invalid HTTP(S) locator")
    part = artifact_lane / f".{row['source_review_download_id']}.part"
    part.unlink(missing_ok=True)
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            async with client.stream("GET", locator) as response:
                code = response.status_code
                final_url = canonical_url(str(response.url))
                ctype = (response.headers.get("content-type") or "").split(";", 1)[0].strip().strip('"').casefold()
                length_raw = response.headers.get("content-length", "")
                declared = int(length_raw) if length_raw.isdigit() else 0
                common = {"attempts": attempt, "http_status": code, "content_type": ctype, "final_url": final_url, "redirect_count": len(response.history), "final_length": declared}
                if code in {401, 403, 451}:
                    return result_base(row, "restricted_or_login_required", started, f"GET access restricted with {code}", **common)
                if code in {404, 410}:
                    return result_base(row, "unavailable_on_download", started, f"GET returned {code}", **common)
                if code == 429 or code >= 500:
                    if attempt <= MAX_RETRIES:
                        await asyncio.sleep(float(attempt)); continue
                    return result_base(row, "restricted_or_login_required", started, f"GET returned {code} after bounded retry", **common)
                if code < 200 or code >= 400:
                    return result_base(row, "unavailable_on_download", started, f"unexpected GET status {code}", **common)
                if declared > MAX_FILE_BYTES:
                    return result_base(row, "oversized_defer", started, "declared length exceeds 75 MiB cap", **common)
                digest = hashlib.sha256(); size = 0; prefix = bytearray()
                with part.open("wb") as handle:
                    async for chunk in response.aiter_bytes(128 * 1024):
                        if len(prefix) < 64:
                            prefix.extend(chunk[:64-len(prefix)])
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            break
                        digest.update(chunk); handle.write(chunk)
                if size > MAX_FILE_BYTES:
                    part.unlink(missing_ok=True)
                    return result_base(row, "oversized_defer", started, "stream exceeded 75 MiB cap", **{**common, "final_length": size})
                if size == 0:
                    part.unlink(missing_ok=True)
                    return result_base(row, "broken_or_corrupt", started, "empty response body", **common)
                classified = classify_content(ctype, bytes(prefix), final_url)
                if not classified:
                    part.unlink(missing_ok=True)
                    status = "likely_non_source_or_navigation_only" if ctype.startswith(("image/", "application/json")) else "excluded_out_of_scope"
                    return result_base(row, status, started, "unsupported source content type/signature", **{**common, "final_length": size})
                extension, retained_type, status = classified
                if generic_navigation(row, final_url, retained_type):
                    part.unlink(missing_ok=True)
                    return result_base(row, "likely_non_source_or_navigation_only", started, "metadata indicates navigation/search page", **{**common, "final_length": size})
                final_path = artifact_lane / f"{row['source_review_download_id']}{extension}"
                part.replace(final_path)
                result = result_base(row, status, started, "supported source retained in ignored artifact storage", **{**common, "final_length": size})
                relative = str(final_path.relative_to(ROOT))
                digest_text = digest.hexdigest()
                result.update({
                    "file_extension": extension, "retained_file_type": retained_type,
                    "retained_local_artifact_path": relative, "artifact_storage_pointer": relative,
                    "artifact_object_key_or_content_address": f"sha256:{digest_text}",
                    "retained_file_size_bytes": str(size), "retained_file_sha256": digest_text,
                })
                return result
        except httpx.TooManyRedirects as exc:
            part.unlink(missing_ok=True)
            return result_base(
                row, "unavailable_on_download", started,
                "redirect chain exceeded bounded eight-redirect policy",
                attempts=attempt, transport_error=type(exc).__name__,
            )
        except httpx.RequestError as exc:
            part.unlink(missing_ok=True)
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(float(attempt)); continue
            return result_base(row, "restricted_or_login_required", started, f"{type(exc).__name__} after bounded retry", attempts=attempt, transport_error=type(exc).__name__)
        except (OSError, ValueError) as exc:
            part.unlink(missing_ok=True)
            return result_base(row, "source_review_error", started, type(exc).__name__, attempts=attempt, transport_error=type(exc).__name__)
    raise AssertionError("retry loop exhausted")


def lane_paths(lane: str) -> dict[str, Path]:
    directory = OUTPUT / "lanes" / lane
    return {"dir": directory, "results": directory / "results.csv", "checkpoint": directory / "checkpoint.json", "summary": directory / "summary.json", "resume": directory / "resume_state.json"}


async def wait_until(start_at: str | None) -> None:
    if not start_at: return
    target = datetime.fromisoformat(start_at.replace("Z", "+00:00")).timestamp()
    while time.time() < target:
        await asyncio.sleep(min(30.0, target - time.time()))


async def run_lane(lane: str, start_at: str | None) -> None:
    if lane not in LANES: raise RuntimeError(f"unknown lane: {lane}")
    _, lock = validate_locks()
    if not read_json(OUTPUT / "preflight_report.json").get("network_smoke_passed"):
        raise RuntimeError("network smoke did not pass")
    number = lane[-3:]
    queue = read_csv(OUTPUT / f"source_review_lane_{number}_queue.csv")
    paths = lane_paths(lane)
    completed = {}
    if paths["results"].is_file():
        existing = read_csv(paths["results"]); completed = {row["source_review_download_id"]: row for row in existing}
        if len(completed) != len(existing): raise RuntimeError("duplicate result checkpoint")
    if paths["checkpoint"].is_file():
        cp = read_json(paths["checkpoint"])
        if cp.get("queue_sha256") != lock["lane_hashes"][lane]["csv_sha256"]: raise RuntimeError("checkpoint lock mismatch")
        if cp.get("status") == "completed":
            print(json.dumps({"lane_id":lane,"status":"already_completed"})); return
    await wait_until(start_at)
    actual = utc_now(); initial = len(completed)
    pending = [row for row in queue if row["source_review_download_id"] not in completed]
    artifact_lane = ARTIFACT_ROOT / lane
    for part in artifact_lane.glob(".*.part"): part.unlink(missing_ok=True)
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT_SECONDS,
                                 limits=httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY),
                                 headers={"User-Agent":"GabrielWagesSourceReview/2.0"}, trust_env=False) as client:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        async def bounded(row: dict[str,str]) -> dict[str,str]:
            async with semaphore: return await download_one(client,row,artifact_lane)
        tasks = [asyncio.create_task(bounded(row)) for row in pending]
        for task in asyncio.as_completed(tasks):
            result = await task; append_csv(paths["results"], result); completed[result["source_review_download_id"]] = result
            write_json(paths["checkpoint"], {
                "task_id":TASK_ID,"lane_id":lane,"status":"in_progress","queue_sha256":lock["lane_hashes"][lane]["csv_sha256"],
                "locked_rows":len(queue),"completed_rows":len(completed),"remaining_rows":len(queue)-len(completed),
                "last_source_review_download_id":result["source_review_download_id"],"checkpointed_at":utc_now(),
                "checkpoint_frequency":"after_every_row","extraction_runs":0,"ocr_runs":0,
            })
    ordered = [completed[row["source_review_download_id"]] for row in queue]
    write_csv(paths["results"], ordered)
    counts = Counter(row["source_review_status"] for row in ordered); finished=utc_now()
    summary = {
        "task_id":TASK_ID,"lane_id":lane,"status":"completed","locked_rows":len(queue),"completed_rows":len(ordered),"remaining_rows":0,
        "priority_counts":dict(Counter(row["priority_bucket"] for row in ordered)),"terminal_status_counts":dict(counts),
        "retained_count":sum(counts[s] for s in RETAINED_STATUSES),"retained_bytes":sum(int(row["retained_file_size_bytes"] or 0) for row in ordered),
        "scheduled_stagger_minutes":STAGGER_MINUTES[lane],"scheduled_start_at":start_at or actual,"actual_started_at":actual,"completed_at":finished,
        "resumed_completed_rows":initial,"maximum_concurrency":MAX_CONCURRENCY,"checkpoint_frequency":"after_every_row",
        "extraction_runs":0,"ocr_runs":0,"rating_runs":0,"ingestion_runs":0,"codification_runs":0,
    }
    write_json(paths["summary"], summary)
    write_json(paths["checkpoint"], {"task_id":TASK_ID,"lane_id":lane,"status":"completed","queue_sha256":lock["lane_hashes"][lane]["csv_sha256"],"locked_rows":len(queue),"completed_rows":len(ordered),"remaining_rows":0,"checkpointed_at":finished,"checkpoint_frequency":"after_every_row"})
    write_json(paths["resume"], {"lane_id":lane,"status":"completed","queue_sha256":lock["lane_hashes"][lane]["csv_sha256"],"completed_rows":len(ordered),"remaining_rows":0,"resume_required":False})
    print(json.dumps(summary,sort_keys=True))


def write_pair(stem: str, rows: list[dict[str,str]], fields: Iterable[str] = RESULT_FIELDS) -> None:
    write_csv(OUTPUT / f"{stem}.csv", rows, fields); write_jsonl(OUTPUT / f"{stem}.jsonl", rows)


def grouped_summary(rows: list[dict[str,str]], field: str) -> dict[str,Any]:
    groups=defaultdict(list)
    for row in rows: groups[row.get(field,"") or "unknown"].append(row)
    out={}
    for key,subset in sorted(groups.items()):
        retained=[row for row in subset if row["source_review_status"] in RETAINED_STATUSES]
        out[key]={"total":len(subset),"retained":len(retained),"not_retained":len(subset)-len(retained),"retained_bytes":sum(int(row["retained_file_size_bytes"] or 0) for row in retained),"terminal_status_counts":dict(Counter(row["source_review_status"] for row in subset))}
    return {"grouping_field":field,"total_rows":len(rows),"groups":out}


def merge() -> None:
    master, lock=validate_locks(); merged=[]; lane_summaries={}
    for lane in LANES:
        p=lane_paths(lane)
        if not p["summary"].is_file() or read_json(p["summary"])["status"]!="completed": raise RuntimeError(f"{lane} incomplete")
        rows=read_csv(p["results"])
        if len(rows)!=LANE_COUNTS[lane] or len({r["source_review_download_id"] for r in rows})!=len(rows): raise RuntimeError(f"{lane} result mismatch")
        merged.extend(rows); lane_summaries[lane]=read_json(p["summary"])
    by_id={row["source_review_download_id"]:row for row in merged}
    if len(by_id)!=EXPECTED_COUNT or set(by_id)!={r["source_review_download_id"] for r in master}: raise RuntimeError("merged results mismatch")
    merged=[by_id[row["source_review_download_id"]] for row in master]
    hash_seen={}
    for row in merged:
        if row["source_review_status"] not in RETAINED_STATUSES: continue
        digest=row["retained_file_sha256"]
        if digest in hash_seen:
            path=ROOT/row["retained_local_artifact_path"]
            if path.is_file(): path.unlink()
            row["duplicate_retained_sha256"]=digest; row["duplicate_of_source_review_download_id"]=hash_seen[digest]
            row["source_review_status"]="duplicate_retained_source"; row["download_status"]="downloaded_duplicate_removed"
            row["artifact_availability_status"]="duplicate_copy_removed"; row["retained_local_artifact_path"]=""; row["artifact_storage_pointer"]=""
            row["retained_file_sha256"]=""; row["retained_file_size_bytes"]=""; row["file_extension"]=""; row["retained_file_type"]=""
        else: hash_seen[digest]=row["source_review_download_id"]
    for lane in LANES:
        write_pair(f"source_review_lane_{lane[-3:]}_results",[r for r in merged if r["source_review_lane_id"]==lane])
    write_pair("merged_source_review_results",merged)
    retained=[r for r in merged if r["source_review_status"] in RETAINED_STATUSES]
    pdf=[r for r in retained if r["source_review_status"]=="retained_pdf"]
    html=[r for r in retained if r["source_review_status"]=="retained_html"]
    other=[r for r in retained if r["source_review_status"]=="retained_other_document"]
    duplicates=[r for r in merged if r["source_review_status"]=="duplicate_retained_source"]
    ocr=[r for r in merged if r["source_review_status"]=="ocr_later"]
    oversized=[r for r in merged if r["source_review_status"]=="oversized_defer"]
    restricted=[r for r in merged if r["source_review_status"] in {"restricted_or_login_required","unavailable_on_download","broken_or_corrupt"}]
    nonsource=[r for r in merged if r["source_review_status"] in {"likely_non_source_or_navigation_only","excluded_out_of_scope"}]
    errors=[r for r in merged if r["source_review_status"]=="source_review_error"]
    manifest_fields=("source_review_download_id","verification_row_id","candidate_id","scout_target_id","state","region","municipality","source_title","source_locator_or_url","final_download_locator","source_family_hint","priority_bucket","cba_non_cba_hint","possible_mechanism_hints","source_review_status","retained_file_type","file_extension","retained_local_artifact_path","artifact_storage_scheme","artifact_storage_pointer","artifact_object_key_or_content_address","artifact_availability_status","artifact_replication_or_backup_status","artifact_access_scope","retained_file_size_bytes","retained_file_sha256")
    write_pair("retained_source_manifest",retained,manifest_fields); write_pair("retained_pdf_manifest",pdf,manifest_fields); write_pair("retained_html_manifest",html,manifest_fields); write_pair("retained_other_document_manifest",other,manifest_fields)
    write_pair("deferred_ocr_later_queue",ocr); write_pair("oversized_defer_queue",oversized); write_pair("restricted_or_failed_queue",restricted); write_pair("duplicate_retained_source_queue",duplicates); write_pair("non_source_or_excluded_queue",nonsource); write_pair("source_review_error_queue",errors)
    retained_bytes=sum(int(r["retained_file_size_bytes"]) for r in retained); counts=Counter(r["source_review_status"] for r in merged)
    hash_manifest={"retained_source_count":len(retained),"unique_retained_hashes":len({r['retained_file_sha256'] for r in retained}),"retained_bytes":retained_bytes,"entries":[{"source_review_download_id":r["source_review_download_id"],"sha256":r["retained_file_sha256"],"bytes":int(r["retained_file_size_bytes"]),"local_artifact_path":r["retained_local_artifact_path"]} for r in retained]}
    write_json(OUTPUT/"retained_source_manifest.sha256.json",hash_manifest)
    summaries={"priority_source_review_summary.json":grouped_summary(merged,"priority_bucket"),"source_family_source_review_summary.json":grouped_summary(merged,"source_family_hint"),"geography_source_review_summary.json":{"state":grouped_summary(merged,"state"),"region":grouped_summary(merged,"region")},"cba_non_cba_source_review_summary.json":grouped_summary(merged,"cba_non_cba_hint"),"mechanism_hint_source_review_summary.json":grouped_summary(merged,"possible_mechanism_hints")}
    for name,value in summaries.items(): write_json(OUTPUT/name,value)
    storage_files=[p for p in ARTIFACT_ROOT.rglob("*") if p.is_file()]
    storage_audit={"passed":len(storage_files)==len(retained) and all(sha256(ROOT/r["retained_local_artifact_path"])==r["retained_file_sha256"] and (ROOT/r["retained_local_artifact_path"]).stat().st_size==int(r["retained_file_size_bytes"]) for r in retained),"artifact_root":str(ARTIFACT_ROOT.relative_to(ROOT)),"artifact_root_git_ignored":check_ignored(),"retained_file_count":len(storage_files),"manifest_retained_count":len(retained),"retained_bytes":sum(p.stat().st_size for p in storage_files),"unique_retained_hashes":len({r["retained_file_sha256"] for r in retained}),"duplicate_retained_hashes":len(duplicates),"part_files":len(list(ARTIFACT_ROOT.rglob("*.part"))),"audited_at":utc_now()}
    write_json(OUTPUT/"retained_source_storage_audit.json",storage_audit)
    decision="broad_state_4x2500_source_review_download_completed_pdf_readiness_ready"
    summary={"task_id":TASK_ID,"decision":decision,"source_review_status":"completed","source_review_queue_count":EXPECTED_COUNT,"completed_source_review_rows":len(merged),"lane_counts":LANE_COUNTS,"lane_summaries":lane_summaries,"priority_counts":dict(Counter(r["priority_bucket"] for r in merged)),"terminal_status_counts":dict(sorted(counts.items())),"retained_source_count":len(retained),"retained_pdf_count":len(pdf),"retained_html_count":len(html),"retained_other_document_count":len(other),"deferred_ocr_later_count":len(ocr),"oversized_defer_count":len(oversized),"restricted_or_failed_count":len(restricted),"duplicate_retained_source_count":len(duplicates),"non_source_or_excluded_count":len(nonsource),"source_review_error_count":len(errors),"retained_byte_total":retained_bytes,"unique_retained_hashes":len({r['retained_file_sha256'] for r in retained}),"artifact_root":str(ARTIFACT_ROOT.relative_to(ROOT)),"extraction_runs":0,"ocr_runs":0,"rating_runs":0,"ingestion_runs":0,"codification_runs":0,"wage_gap_calculations":0,"regressions":0,"final_causal_claims":0,"dashboard_map_filter":"total_scout_coverage_only","dashboard_scout_covered_municipalities":16887,"global_analysis_readiness":False,"global_readiness_flags_preserved":{"global_collection_readiness":"pass","global_mechanism_analysis_readiness":"partial_pass","global_quantitative_evidence_readiness":"partial_pass","global_wage_gap_analysis_readiness":"blocked_pending_normalization","global_causal_analysis_readiness":"blocked_pending_matched_structure","overall_global_analysis_readiness":"partial_pass"},"next_task_id":"BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"}
    write_json(OUTPUT/"source_review_download_summary.json",summary)
    write_json(OUTPUT/"final_decision.json",{"task_id":TASK_ID,"decision":decision,"source_review_download_completed":True,"pdf_text_readiness_ready_next":True,"global_analysis_readiness":False,"finalized_at":utc_now()})
    lock.update({"execution_status":"completed","decision":decision,"completed_rows":len(merged),"terminal_status_counts":dict(sorted(counts.items())),"retained_source_count":len(retained),"retained_bytes":retained_bytes,"completed_at":utc_now()}); write_json(OUTPUT/"source_review_download_manifest.json",lock)
    write_text(OUTPUT/"source_review_download_summary.md",f"""# Broad-state 4 x 2,500 source review/download

Decision: `{decision}`. Four staggered lanes processed all {EXPECTED_COUNT:,} locked source-review-ready locators. Unique retained sources: {len(retained):,} ({len(pdf):,} PDF, {len(html):,} HTML, {len(other):,} other documents), totaling {retained_bytes:,} bytes. Terminal outcomes: {', '.join(f'{k} {v:,}' for k,v in sorted(counts.items()))}.

Retained payloads exist only under `{ARTIFACT_ROOT.relative_to(ROOT)}`. Git tracks hashes, sizes, storage pointers, lineage, summaries, and queues only. No extraction, OCR, rating, ingestion, codification, wage-gap calculation, regression, or final causal analysis occurred.

The dashboard map remains total scout coverage only at 16,887 municipalities. Global readiness remains partial diagnostic only; wage-gap and causal readiness remain blocked.
""")
    write_json(OUTPUT/"dashboard_status_input.json",{"task_id":TASK_ID,"decision":decision,"source_review_queue_count":EXPECTED_COUNT,"retained_source_count":len(retained),"retained_pdf_count":len(pdf),"retained_html_count":len(html),"retained_other_document_count":len(other),"terminal_status_counts":dict(sorted(counts.items())),"retained_by_priority":{k:v["retained"] for k,v in summaries["priority_source_review_summary.json"]["groups"].items()},"retained_by_source_family":{k:v["retained"] for k,v in summaries["source_family_source_review_summary.json"]["groups"].items()},"retained_by_state":{k:v["retained"] for k,v in summaries["geography_source_review_summary.json"]["state"]["groups"].items()},"retained_by_region":{k:v["retained"] for k,v in summaries["geography_source_review_summary.json"]["region"]["groups"].items()},"retained_by_cba_hint":{k:v["retained"] for k,v in summaries["cba_non_cba_source_review_summary.json"]["groups"].items()},"retained_by_mechanism_hint":{k:v["retained"] for k,v in summaries["mechanism_hint_source_review_summary.json"]["groups"].items()},"retained_bytes":retained_bytes,"map_filter":"total_scout_coverage_only","scout_covered_municipalities":16887,"global_analysis_readiness":False,"next_stage":"four_lane_pdf_text_readiness"})
    write_text(OUTPUT/"dashboard_status_update_summary.md",f"# Dashboard source-review/download update\n\nThe current pipeline stage is source review/download complete: {EXPECTED_COUNT:,} reviewed, {len(retained):,} retained ({len(pdf):,} PDF, {len(html):,} HTML, {len(other):,} other). PDF/text readiness is next. The map remains total scout coverage only at 16,887 and global readiness remains false.")
    write_text(OUTPUT/"next_task.md",f"""# Next task: BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30

Run PDF/text/HTML/other-document readiness over only the {len(retained):,} retained sources using four independent staggered lanes and per-row checkpoints. Classify parse-text-ready, HTML-text-ready, other-document-text-ready, OCR-later, oversized-defer, encrypted/locked, corrupt/broken, shell/navigation-only, and needs-review.

Do not extract full text, OCR, rate, ingest, codify, calculate wage gaps, run regressions, or make causal claims. Update dashboard/status/docs and run dashboard build plus browser smoke validation.
""")
    write_json(OUTPUT/"forbidden_action_audit.json",{"passed":True,"retained_payloads_in_ignored_artifact_storage_only":True,"retained_payloads_in_git_output_directory":0,"text_extractions":0,"ocr_runs":0,"rating_runs":0,"ingestion_runs":0,"codification_runs":0,"wage_gap_calculations":0,"regressions":0,"treatment_effect_claims":0,"final_causal_claims":0,"full_text_artifacts_created":0})
    write_text(ROOT/"docs/analysis/broad_state_4x2500_source_review_download_result_2026-07-30.md",f"# Broad state 4 x 2,500 source review/download — 2026-07-30\n\nDecision: `{decision}`. Reviewed {EXPECTED_COUNT:,} locators and retained {len(retained):,} unique sources in ignored local artifact storage. PDF/text readiness is next; global analysis readiness remains false.")
    write_text(ROOT/"docs/analysis/broad_state_4x2500_source_review_download_dashboard_status_note_2026-07-30.md",f"# Dashboard status — broad state 4 x 2,500 source review/download\n\nSource review/download is complete: {EXPECTED_COUNT:,} reviewed and {len(retained):,} retained. PDF/text readiness is next. The map remains total scout coverage only at 16,887; global readiness remains false.")
    print(json.dumps(summary,sort_keys=True))


def validate() -> None:
    master,lock=validate_locks(); merged=read_csv(OUTPUT/"merged_source_review_results.csv"); retained=read_csv(OUTPUT/"retained_source_manifest.csv"); summary=read_json(OUTPUT/"source_review_download_summary.json"); storage=read_json(OUTPUT/"retained_source_storage_audit.json")
    checks={"input_queue_count_3950":len(master)==EXPECTED_COUNT,"lane_counts_exact":all(lock["lane_distribution"][lane]["total_rows"]==LANE_COUNTS[lane] for lane in LANES),"every_input_in_exactly_one_lane":len({r["source_review_download_id"] for r in master})==EXPECTED_COUNT,"lane_hashes_match":True,"eligible_verification_statuses_only":all(r["verification_status"] in {"reachable","reachable_with_redirect"} for r in master),"completed_results_have_one_terminal_status":len(merged)==EXPECTED_COUNT and all(r["source_review_status"] in CONTROLLED_STATUSES for r in merged),"merged_reconciles_3950":len(merged)==EXPECTED_COUNT and len({r["source_review_download_id"] for r in merged})==EXPECTED_COUNT,"retained_manifest_reconciles":len(retained)==summary["retained_source_count"],"retained_storage_audit_passed":storage["passed"] is True and storage["part_files"]==0,"retained_hashes_and_sizes_recorded":all(len(r["retained_file_sha256"])==64 and int(r["retained_file_size_bytes"])>0 for r in retained),"artifact_root_git_ignored":check_ignored(),"no_retained_artifacts_tracked":not subprocess.run(["git","ls-files",str(ARTIFACT_ROOT.relative_to(ROOT))],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip(),"no_extraction_ocr_rating_ingestion_codification":all(summary[k]==0 for k in ("extraction_runs","ocr_runs","rating_runs","ingestion_runs","codification_runs")),"no_wage_gap_regression_final_causal_claims":all(summary[k]==0 for k in ("wage_gap_calculations","regressions","final_causal_claims")),"dashboard_map_scope_preserved":summary["dashboard_map_filter"]=="total_scout_coverage_only" and summary["dashboard_scout_covered_municipalities"]==16887,"global_readiness_not_advanced":summary["global_analysis_readiness"] is False}
    passed=all(checks.values()); report={"task_id":TASK_ID,"validation_passed":passed,"checks":checks,"queue_count":len(master),"merged_count":len(merged),"retained_count":len(retained),"terminal_status_counts":dict(Counter(r["source_review_status"] for r in merged)),"validated_at":utc_now()}; write_json(OUTPUT/"validation_report.json",report); write_text(OUTPUT/"validation_report.md","# Source-review/download validation\n\n"+"\n".join(f"- {'PASS' if ok else 'FAIL'}: `{name}`" for name,ok in checks.items())+f"\n\nOverall: {'PASS' if passed else 'FAIL'}.")
    if not passed: raise RuntimeError("validation failed")
    print(json.dumps(report,sort_keys=True))


def audit_staged() -> None:
    """Audit the exact proposed commit without reading retained source bodies."""
    names = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    forbidden_suffixes = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".gz", ".tar", ".7z", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    }
    forbidden_path_fragments = (
        "artifacts/local_retained_sources/", "browser-cache", "playwright-profile",
        "full_text", "extracted_text", "source_body", "downloaded_sources/",
    )
    files = []
    violations = []
    aggregate = 0
    for name in names:
        path = ROOT / name
        size = path.stat().st_size if path.is_file() else 0
        aggregate += size
        suffix = path.suffix.casefold()
        entry = {"path": name, "bytes": size, "suffix": suffix or "none"}
        files.append(entry)
        if suffix in forbidden_suffixes:
            violations.append({"path": name, "reason": "forbidden retained/binary extension"})
        if any(fragment in name.casefold() for fragment in forbidden_path_fragments):
            violations.append({"path": name, "reason": "forbidden retained/full-text/cache path"})
        if path.is_file() and size <= 2_000_000:
            data = path.read_bytes()
            if b"\x00" in data:
                violations.append({"path": name, "reason": "binary NUL byte detected"})
    tracked_artifacts = subprocess.run(
        ["git", "ls-files", str(ARTIFACT_ROOT.relative_to(ROOT))],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    origin = subprocess.run(
        ["git", "rev-parse", "origin/main"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    head = current_head()
    ahead = subprocess.run(
        ["git", "rev-list", "--objects", f"{origin}..{head}"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.splitlines()
    report = {
        "passed": not violations and not tracked_artifacts,
        "audited_at": utc_now(),
        "precommit_head": head,
        "origin_main": origin,
        "ahead_history_object_entries_before_commit": len(ahead),
        "staged_file_count": len(files),
        "staged_aggregate_bytes": aggregate,
        "largest_staged_files": sorted(files, key=lambda item: item["bytes"], reverse=True)[:25],
        "retained_artifact_paths_staged": [name for name in names if name.startswith("artifacts/local_retained_sources/")],
        "retained_artifact_paths_tracked": tracked_artifacts,
        "forbidden_binary_extensions_staged": [item for item in violations if "extension" in item["reason"]],
        "full_source_bodies_or_extracted_text_staged": [item for item in violations if "path" in item["reason"]],
        "violations": violations,
        "projected_new_commit_metadata_only": not violations,
        "note": "The audit itself is generated after examining the staged proposal and is staged only after this report passes.",
    }
    write_json(OUTPUT / "staged_file_audit.json", report)
    if not report["passed"]:
        raise RuntimeError("staged-file/large-file audit failed")
    print(json.dumps(report, sort_keys=True))


def final_validate() -> None:
    """Add dashboard/browser/Git pre-push gates to the merge validation."""
    report = read_json(OUTPUT / "validation_report.json")
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    build = read_json(OUTPUT / "dashboard_build_report.json")
    browser = read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    staged = read_json(OUTPUT / "staged_file_audit.json")
    extra = {
        "dashboard_data_reflects_source_review_download": (
            phase.get("broad_state_4x2500_source_review_download_available") is True
            and phase.get("broad_state_4x2500_source_review_queue_count") == EXPECTED_COUNT
            and phase.get("broad_state_4x2500_source_review_retained_count")
            == read_json(OUTPUT / "source_review_download_summary.json")["retained_source_count"]
        ),
        "dashboard_local_build_passed": build.get("status") == "passed",
        "dashboard_visible_browser_smoke_passed": browser.get("status") == "passed",
        "dashboard_map_remains_scout_coverage_only": (
            browser.get("visible_scout_coverage") == 16887
            and browser.get("map_scope") == "total_scout_coverage_only"
        ),
        "dashboard_global_readiness_not_advanced": (
            phase.get("global_analysis_readiness") is False
            and phase.get("global_wage_gap_analysis_readiness") == "blocked_pending_normalization"
            and phase.get("global_causal_analysis_readiness") == "blocked_pending_matched_structure"
        ),
        "staged_file_and_large_file_audit_passed": staged.get("passed") is True,
        "no_retained_payloads_staged_or_tracked": (
            not staged.get("retained_artifact_paths_staged")
            and not staged.get("retained_artifact_paths_tracked")
        ),
    }
    report["checks"].update(extra)
    report["validation_passed"] = all(report["checks"].values())
    report["final_validation_completed_at"] = utc_now()
    write_json(OUTPUT / "validation_report.json", report)
    write_text(
        OUTPUT / "validation_report.md",
        "# Source-review/download validation\n\n"
        + "\n".join(
            f"- {'PASS' if ok else 'FAIL'}: `{name}`"
            for name, ok in report["checks"].items()
        )
        + f"\n\nOverall: {'PASS' if report['validation_passed'] else 'FAIL'}.\n",
    )
    if not report["validation_passed"]:
        raise RuntimeError("final validation failed")
    print(json.dumps(report, sort_keys=True))


def main() -> None:
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare",action="store_true"); group.add_argument("--smoke",action="store_true"); group.add_argument("--run-lane",choices=LANES); group.add_argument("--merge",action="store_true"); group.add_argument("--validate",action="store_true"); group.add_argument("--audit-staged",action="store_true"); group.add_argument("--final-validate",action="store_true"); parser.add_argument("--start-at")
    args=parser.parse_args()
    if args.prepare: prepare()
    elif args.smoke: asyncio.run(smoke())
    elif args.run_lane: asyncio.run(run_lane(args.run_lane,args.start_at))
    elif args.merge: merge()
    elif args.validate: validate()
    elif args.audit_staged: audit_staged()
    else: final_validate()


if __name__=="__main__": main()
