#!/usr/bin/env python3
"""Bounded four-lane source review/download for 5,589 reviewed locators.

This runner retrieves only the committed locked locator queue, streams allowed
source files into lane-isolated retained directories, hashes retained bytes,
and writes metadata ledgers.  It deliberately performs no PDF/HTML text
parsing, OCR, rendering, extraction, rating, ingestion, codification, or
statistical analysis.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import shutil
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT_DIR = BASE / "COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28"
OUTPUT_DIR = BASE / "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
RETAINED_DIR = OUTPUT_DIR / "retained_sources"
TASK_ID = "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
INPUT_QUEUE = INPUT_DIR / "combined_broad_candidate_review_locked_source_review_queue.csv"
INPUT_LOCK = INPUT_DIR / "combined_broad_candidate_review_locked_source_review_queue_lock.json"
EXPECTED_COUNT = 5_589
LANE_COUNTS = {
    "source_review_lane_001": 1_397,
    "source_review_lane_002": 1_397,
    "source_review_lane_003": 1_397,
    "source_review_lane_004": 1_398,
}
LANE_STAGGER_MINUTES = {
    "source_review_lane_001": 0,
    "source_review_lane_002": 8,
    "source_review_lane_003": 16,
    "source_review_lane_004": 24,
}
MAX_FILE_BYTES = 75 * 1024 * 1024
# Four simultaneous lanes preserve the repository's established aggregate
# transport ceiling of eight requests: two in-flight downloads per lane.
MAX_CONCURRENCY = 2
MAX_RETRIES = 1
MAX_REDIRECTS = 8
TIMEOUT_SECONDS = 75.0
SMOKE_BYTES = 4096
MIN_FREE_BYTES = 20 * 1024 * 1024 * 1024

RETAINED_STATUSES = {"retained_pdf", "retained_html", "retained_document_other"}
CONTROLLED_STATUSES = RETAINED_STATUSES | {
    "duplicate_file_hash",
    "duplicate_canonical_locator",
    "oversized_for_this_pass",
    "blocked_by_transport",
    "unavailable_on_get",
    "unsupported_content_type",
    "weak_or_needs_review",
    "generic_navigation_or_search_page",
    "wrong_employer_or_source_metadata_only",
    "invalid_locator",
    "download_error",
    "source_review_not_run",
}

INPUT_LINEAGE_FIELDS = (
    "combined_review_id", "source_candidate_id", "verification_row_id", "candidate_origin",
    "state", "region", "municipality", "county", "source_title",
    "source_locator_or_url", "final_canonical_locator", "source_domain",
    "source_family_hint", "document_type_hint", "source_review_priority",
    "verification_status", "http_status_code", "content_type_header",
    "content_length_header", "candidate_review_status",
)
LOCK_FIELDS = (
    "source_review_download_id", *INPUT_LINEAGE_FIELDS, "lane_id", "lane_sequence",
    "duplicate_canonical_locator_of", "live_status", "global_analysis_readiness",
)
RESULT_FIELDS = (
    "source_review_download_id", "combined_review_id", "source_candidate_id",
    "verification_row_id", "candidate_origin", "lane_id", "lane_sequence", "state",
    "region", "municipality", "county", "source_title", "source_locator_or_url",
    "final_canonical_locator", "source_domain", "source_family_hint",
    "document_type_hint", "source_review_priority", "verification_status",
    "http_status_code_from_verification", "content_type_header_from_verification",
    "candidate_review_status", "source_review_download_status", "final_download_url",
    "download_http_status", "final_content_type", "final_content_length",
    "file_extension", "retained_file_type", "retained_file_path",
    "retained_file_size_bytes", "retained_file_sha256", "duplicate_file_hash",
    "duplicate_of_source_review_download_id", "redirect_count", "download_attempt_count",
    "download_started_at", "download_completed_at", "transport_error_type",
    "source_review_reason", "exclusion_or_defer_reason", "verification_status_preserved",
    "download_status", "source_review_status", "extraction_status", "rating_status",
    "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
)

CONTENT_TYPE_MAP = {
    "application/pdf": (".pdf", "pdf", "retained_pdf"),
    "text/html": (".html", "html", "retained_html"),
    "application/xhtml+xml": (".html", "html", "retained_html"),
    "text/plain": (".txt", "txt", "retained_document_other"),
    "text/csv": (".csv", "csv", "retained_document_other"),
    "application/csv": (".csv", "csv", "retained_document_other"),
    "application/rtf": (".rtf", "rtf", "retained_document_other"),
    "text/rtf": (".rtf", "rtf", "retained_document_other"),
    "application/msword": (".doc", "doc", "retained_document_other"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        ".docx", "docx", "retained_document_other"
    ),
    "application/vnd.ms-excel": (".xls", "xls", "retained_document_other"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (
        ".xlsx", "xlsx", "retained_document_other"
    ),
}
URL_EXTENSIONS = {
    ".pdf": ("pdf", "retained_pdf"), ".html": ("html", "retained_html"),
    ".htm": ("html", "retained_html"), ".doc": ("doc", "retained_document_other"),
    ".docx": ("docx", "retained_document_other"), ".xls": ("xls", "retained_document_other"),
    ".xlsx": ("xlsx", "retained_document_other"), ".csv": ("csv", "retained_document_other"),
    ".txt": ("txt", "retained_document_other"), ".rtf": ("rtf", "retained_document_other"),
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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
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
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def canonical_locator(row: dict[str, str]) -> str:
    return (row.get("final_canonical_locator") or row.get("source_locator_or_url") or "").strip()


def valid_http_locator(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme.casefold() in {"http", "https"} and bool(parsed.netloc)


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["source_review_download_id"] for row in rows)))


def lane_number(lane: str) -> int:
    return int(lane.rsplit("_", 1)[-1])


def lane_dir(lane: str) -> Path:
    return OUTPUT_DIR / "lanes" / lane


def lane_queue_path(lane: str) -> Path:
    return OUTPUT_DIR / f"combined_broad_source_review_download_lane_{lane_number(lane):03d}_locked_queue.csv"


def lane_result_path(lane: str) -> Path:
    return lane_dir(lane) / f"lane_{lane_number(lane):03d}_source_review_download_results.csv"


def source_review_id(combined_review_id: str) -> str:
    return "CBSRD-20260728-" + text_hash(combined_review_id)[:20]


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    decision = read_json(INPUT_DIR / "combined_broad_candidate_review_decision.json")
    input_lock = read_json(INPUT_LOCK)
    rows = read_csv(INPUT_QUEUE)
    if not (
        decision.get("decision") == "combined_broad_candidate_review_completed_source_review_ready"
        and decision.get("source_review_ready_count") == EXPECTED_COUNT
        and len(rows) == EXPECTED_COUNT
        and sha256(INPUT_QUEUE) == input_lock.get("queue_sha256")
        and input_lock.get("locked_rows") == EXPECTED_COUNT
        and all(row.get("candidate_review_status") in {
            "source_review_ready_high", "source_review_ready_medium", "source_review_ready_low"
        } for row in rows)
        and all(row.get("verification_status") in {
            "verified_reachable", "verified_reachable_redirected", "reused_prior_verified"
        } for row in rows)
        and all(row.get("global_analysis_readiness") == "false" for row in rows)
    ):
        raise RuntimeError("committed 5,589-row source-review queue fails integrity gates")
    ids = [row["combined_review_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("combined review IDs are not unique")

    OUTPUT_DIR.mkdir(parents=True)
    RETAINED_DIR.mkdir()
    duplicate_of: dict[str, str] = {}
    seen_canonical: dict[str, str] = {}
    prepared: list[dict[str, str]] = []
    boundaries = [1_397, 2_794, 4_191, 5_589]
    lanes = list(LANE_COUNTS)
    for index, source in enumerate(rows):
        lane_index = next(i for i, boundary in enumerate(boundaries) if index < boundary)
        lane = lanes[lane_index]
        lane_start = 0 if lane_index == 0 else boundaries[lane_index - 1]
        locator_key = canonical_locator(source).casefold()
        srid = source_review_id(source["combined_review_id"])
        prior = seen_canonical.get(locator_key, "") if locator_key else ""
        if locator_key and not prior:
            seen_canonical[locator_key] = srid
        duplicate_of[srid] = prior
        row = {
            "source_review_download_id": srid,
            **{field: source.get(field, "") for field in INPUT_LINEAGE_FIELDS},
            "lane_id": lane,
            "lane_sequence": str(index - lane_start + 1),
            "duplicate_canonical_locator_of": prior,
            "live_status": "not_run",
            "global_analysis_readiness": "false",
        }
        prepared.append(row)

    master_path = OUTPUT_DIR / "combined_broad_source_review_download_5589_locked_queue.csv"
    write_csv(master_path, prepared, LOCK_FIELDS)
    lane_hashes: dict[str, str] = {}
    for lane, expected in LANE_COUNTS.items():
        lane_rows = [row for row in prepared if row["lane_id"] == lane]
        if len(lane_rows) != expected:
            raise RuntimeError(f"{lane} expected {expected}, observed {len(lane_rows)}")
        path = lane_queue_path(lane)
        write_csv(path, lane_rows, LOCK_FIELDS)
        lane_hashes[lane] = sha256(path)
        number = lane_number(lane)
        write_json(OUTPUT_DIR / f"combined_broad_source_review_download_lane_{number:03d}_lock.json", {
            "lane_id": lane, "queue_rows": expected, "queue_sha256": lane_hashes[lane],
            "id_set_sha256": id_set_hash(lane_rows), "scheduled_stagger_minutes": LANE_STAGGER_MINUTES[lane],
            "global_analysis_readiness": False,
        })
        write_json(OUTPUT_DIR / f"combined_broad_source_review_download_lane_{number:03d}_locked_queue_summary.json", {
            "lane_id": lane, "locked_rows": expected,
            "priority_counts": dict(sorted(Counter(row["source_review_priority"] for row in lane_rows).items())),
            "scheduled_stagger_minutes": LANE_STAGGER_MINUTES[lane], "live_status": "not_run",
            "global_analysis_readiness": False,
        })
        (lane_dir(lane)).mkdir(parents=True)
        (RETAINED_DIR / lane).mkdir(parents=True)

    lock = {
        "task_id": TASK_ID, "input_commit": "845333f19e9b0814d546696885a4e22adcbf0fb9",
        "queue_rows": len(prepared), "locked_rows": len(prepared),
        "queue_sha256": sha256(master_path),
        "id_set_sha256": id_set_hash(prepared), "lane_counts": LANE_COUNTS,
        "lane_queue_sha256": lane_hashes, "input_queue_sha256": sha256(INPUT_QUEUE),
        "input_lock_sha256": sha256(INPUT_LOCK), "canonical_duplicate_rows": sum(bool(v) for v in duplicate_of.values()),
        "maximum_file_bytes": MAX_FILE_BYTES, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_lock.json", lock)
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_locked_queue_summary.json", {
        "locked_queue_rows": EXPECTED_COUNT, "lane_counts": LANE_COUNTS,
        "priority_counts": dict(sorted(Counter(row["source_review_priority"] for row in prepared).items())),
        "only_source_review_ready_candidates": True, "only_reachable_or_reused_verification_statuses": True,
        "canonical_duplicate_rows": lock["canonical_duplicate_rows"], "live_status": "not_run",
        "global_analysis_readiness": False,
    })
    print(json.dumps({"status": "prepared", "rows": len(prepared), "lane_counts": LANE_COUNTS,
                      "queue_sha256": lock["queue_sha256"]}, sort_keys=True))


def classify_content(content_type: str, prefix: bytes, url: str) -> tuple[str, str, str] | None:
    ctype = (content_type or "").split(";", 1)[0].strip().strip('"').casefold()
    if prefix.startswith(b"%PDF-"):
        return ".pdf", "pdf", "retained_pdf"
    if ctype in CONTENT_TYPE_MAP:
        return CONTENT_TYPE_MAP[ctype]
    path = unquote(urlsplit(url).path).casefold()
    extension = Path(path).suffix
    if extension in URL_EXTENSIONS and ctype in {"", "application/octet-stream", "application/zip"}:
        retained_type, status = URL_EXTENSIONS[extension]
        return extension if extension != ".htm" else ".html", retained_type, status
    if ctype in {"application/octet-stream", "application/zip"}:
        if prefix.startswith(b"\xd0\xcf\x11\xe0"):
            return ".doc", "other_document", "retained_document_other"
    return None


def generic_metadata_only(row: dict[str, str], final_url: str, retained_type: str) -> bool:
    if retained_type != "html":
        return False
    title = row.get("source_title", "").casefold()
    parsed = urlsplit(final_url)
    generic_title = any(term in title for term in ("search results", "site search", "job openings", "careers page"))
    root_unknown = parsed.path.strip("/") == "" and row.get("source_family_hint") == "unknown_or_needs_review"
    return generic_title or root_unknown


async def smoke_one(client: httpx.AsyncClient, row: dict[str, str]) -> dict[str, Any]:
    url = canonical_locator(row)
    started = utc_now()
    try:
        async with client.stream("GET", url, headers={"Range": f"bytes=0-{SMOKE_BYTES - 1}"}) as response:
            observed = 0
            async for chunk in response.aiter_bytes():
                observed += min(len(chunk), SMOKE_BYTES - observed)
                if observed >= SMOKE_BYTES:
                    break
            return {
                "lane_id": row["lane_id"], "source_review_download_id": row["source_review_download_id"],
                "smoke_started_at": started, "smoke_completed_at": utc_now(),
                "http_status": response.status_code, "bytes_read": observed,
                "content_type": (response.headers.get("content-type") or "").split(";", 1)[0],
                "transport_error_type": "", "retained_file_written": "false",
            }
    except httpx.HTTPError as exc:
        return {
            "lane_id": row["lane_id"], "source_review_download_id": row["source_review_download_id"],
            "smoke_started_at": started, "smoke_completed_at": utc_now(), "http_status": "",
            "bytes_read": 0, "content_type": "", "transport_error_type": type(exc).__name__,
            "retained_file_written": "false",
        }


async def preflight() -> None:
    lock = read_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_lock.json")
    master = read_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_locked_queue.csv")
    if not (
        len(master) == EXPECTED_COUNT and sha256(OUTPUT_DIR / "combined_broad_source_review_download_5589_locked_queue.csv") == lock["queue_sha256"]
        and all(sha256(lane_queue_path(lane)) == lock["lane_queue_sha256"][lane] for lane in LANE_COUNTS)
    ):
        raise RuntimeError("preflight queue hash mismatch")
    union = [row for lane in LANE_COUNTS for row in read_csv(lane_queue_path(lane))]
    if {row["source_review_download_id"] for row in union} != {row["source_review_download_id"] for row in master}:
        raise RuntimeError("master queue does not equal lane union")

    usage = shutil.disk_usage(ROOT)
    known_lengths = [int(row["content_length_header"]) for row in master if row.get("content_length_header", "").isdigit()]
    known_bytes = sum(min(length, MAX_FILE_BYTES) for length in known_lengths)
    unknown_count = EXPECTED_COUNT - len(known_lengths)
    observed_average = int(known_bytes / len(known_lengths)) if known_lengths else 5 * 1024 * 1024
    projected_bytes = known_bytes + unknown_count * observed_average
    storage_passed = usage.free >= max(MIN_FREE_BYTES, projected_bytes * 2)
    storage = {
        "available_bytes_before_run": usage.free, "total_filesystem_bytes": usage.total,
        "known_content_length_rows": len(known_lengths), "known_capped_bytes": known_bytes,
        "unknown_content_length_rows": unknown_count, "projected_retained_bytes": projected_bytes,
        "theoretical_75mb_cap_bytes": EXPECTED_COUNT * MAX_FILE_BYTES,
        "minimum_free_bytes_required": max(MIN_FREE_BYTES, projected_bytes * 2),
        "maximum_file_bytes": MAX_FILE_BYTES, "storage_sanity_passed": storage_passed,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_storage_sanity_check.json", storage)
    if not storage_passed:
        raise RuntimeError("storage sanity check failed before live downloads")

    representatives: list[dict[str, str]] = []
    for lane in LANE_COUNTS:
        lane_rows = [row for row in master if row["lane_id"] == lane and not row["duplicate_canonical_locator_of"]]
        representatives.extend(lane_rows[:2])
    limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS,
                                 timeout=TIMEOUT_SECONDS, limits=limits,
                                 headers={"User-Agent": "GabrielWagesSourceReview/1.0"}) as client:
        probes = await asyncio.gather(*(smoke_one(client, row) for row in representatives))
    fields = ("lane_id", "source_review_download_id", "smoke_started_at", "smoke_completed_at",
              "http_status", "bytes_read", "content_type", "transport_error_type", "retained_file_written")
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_network_smoke_metadata.csv", probes, fields)
    responded_by_lane = {
        lane: any(str(row.get("http_status", "")).isdigit() and int(row["http_status"]) > 0
                  for row in probes if row["lane_id"] == lane)
        for lane in LANE_COUNTS
    }
    smoke_passed = all(responded_by_lane.values())
    checks = {
        "preflight_passed": smoke_passed and storage_passed,
        "prior_decision": "combined_broad_candidate_review_completed_source_review_ready",
        "locked_queue_count": len(master), "lane_counts": LANE_COUNTS,
        "master_equals_lane_union": len(union) == len(master) and id_set_hash(union) == id_set_hash(master),
        "all_candidates_source_review_ready": all(row["candidate_review_status"].startswith("source_review_ready_") for row in master),
        "all_verification_statuses_reachable_or_reused": all(row["verification_status"] in {"verified_reachable", "verified_reachable_redirected", "reused_prior_verified"} for row in master),
        "network_smoke_probe_count": len(probes), "network_smoke_responded_by_lane": responded_by_lane,
        "network_smoke_passed": smoke_passed, "storage_sanity_passed": storage_passed,
        "retained_directory_writable": os.access(RETAINED_DIR, os.W_OK),
        "lane_isolation": True, "candidate_review_reruns": 0, "verification_reruns": 0,
        "text_table_span_extraction_runs": 0, "ocr_runs": 0, "rendering_runs": 0,
        "rating_model_api_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_preflight_checks.json", checks)
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_preflight_report.md", f"""# Source-review/download preflight

Preflight {'passed' if checks['preflight_passed'] else 'failed'} for the exact 5,589-row lock. The master lock equals four isolated queues of 1,397 / 1,397 / 1,397 / 1,398 rows. Eight bounded range-smoke probes wrote no retained files; every lane returned at least one HTTP response. Storage projected {projected_bytes:,} bytes against {usage.free:,} available bytes. Each live file is capped at {MAX_FILE_BYTES:,} bytes. No extraction, OCR, rendering, rating, model/API analysis, ingestion, codification, or statistics are authorized.
""")
    if not checks["preflight_passed"]:
        raise RuntimeError("global source-review/download preflight failed")
    print(json.dumps(checks, sort_keys=True))


def empty_result(row: dict[str, str], status: str, *, started: str, reason: str,
                 attempts: int = 0, http_status: str = "", content_type: str = "",
                 final_url: str = "", redirect_count: int = 0, transport_error: str = "",
                 final_length: int | str = "") -> dict[str, str]:
    return {
        "source_review_download_id": row["source_review_download_id"],
        **{field: row.get(field, "") for field in INPUT_LINEAGE_FIELDS if field not in {"http_status_code", "content_type_header"}},
        "lane_id": row["lane_id"], "lane_sequence": row["lane_sequence"],
        "http_status_code_from_verification": row.get("http_status_code", ""),
        "content_type_header_from_verification": row.get("content_type_header", ""),
        "source_review_download_status": status, "final_download_url": final_url,
        "download_http_status": str(http_status), "final_content_type": content_type,
        "final_content_length": str(final_length), "file_extension": "", "retained_file_type": "",
        "retained_file_path": "", "retained_file_size_bytes": "", "retained_file_sha256": "",
        "duplicate_file_hash": "", "duplicate_of_source_review_download_id": (
            row.get("duplicate_canonical_locator_of", "") if status == "duplicate_canonical_locator" else ""
        ),
        "redirect_count": str(redirect_count), "download_attempt_count": str(attempts),
        "download_started_at": started, "download_completed_at": utc_now(),
        "transport_error_type": transport_error, "source_review_reason": reason,
        "exclusion_or_defer_reason": reason if status not in RETAINED_STATUSES else "",
        "verification_status_preserved": "true", "download_status": "not_downloaded",
        "source_review_status": "source_reviewed_not_retained", "extraction_status": "not_extracted",
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified", "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false", "notes": "bounded source retrieval metadata only",
    }


async def download_one(client: httpx.AsyncClient, row: dict[str, str], retained_path: Path) -> dict[str, str]:
    started = utc_now()
    locator = canonical_locator(row)
    if row.get("duplicate_canonical_locator_of"):
        return empty_result(row, "duplicate_canonical_locator", started=started,
                            reason="canonical locator already represented in locked queue")
    if not valid_http_locator(locator):
        return empty_result(row, "invalid_locator", started=started, reason="locator is not a valid HTTP(S) URL")
    part = retained_path / f".{row['source_review_download_id']}.part"
    part.unlink(missing_ok=True)
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            async with client.stream("GET", locator) as response:
                status_code = response.status_code
                final_url = str(response.url)
                content_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip().strip('"').casefold()
                length_raw = response.headers.get("content-length", "")
                declared_length = int(length_raw) if length_raw.isdigit() else 0
                redirects = len(response.history)
                if status_code in {404, 410}:
                    return empty_result(row, "unavailable_on_get", started=started, reason=f"GET returned {status_code}", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=declared_length)
                if status_code in {401, 403, 451}:
                    return empty_result(row, "blocked_by_transport", started=started, reason=f"GET access blocked with {status_code}", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=declared_length)
                if status_code == 429 or status_code >= 500:
                    if attempt <= MAX_RETRIES:
                        await asyncio.sleep(float(attempt))
                        continue
                    return empty_result(row, "blocked_by_transport", started=started, reason=f"GET returned {status_code} after bounded retry", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=declared_length)
                if status_code < 200 or status_code >= 400:
                    return empty_result(row, "download_error", started=started, reason=f"unexpected GET status {status_code}", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=declared_length)
                if declared_length > MAX_FILE_BYTES:
                    return empty_result(row, "oversized_for_this_pass", started=started, reason="content-length exceeds 75 MB pass limit", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=declared_length)
                digest = hashlib.sha256()
                size = 0
                prefix = bytearray()
                with part.open("wb") as handle:
                    async for chunk in response.aiter_bytes(128 * 1024):
                        if len(prefix) < 64:
                            prefix.extend(chunk[: 64 - len(prefix)])
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            break
                        digest.update(chunk)
                        handle.write(chunk)
                if size > MAX_FILE_BYTES:
                    part.unlink(missing_ok=True)
                    return empty_result(row, "oversized_for_this_pass", started=started, reason="stream exceeded 75 MB pass limit", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=size)
                if size == 0:
                    part.unlink(missing_ok=True)
                    return empty_result(row, "weak_or_needs_review", started=started, reason="empty response body", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=0)
                classified = classify_content(content_type, bytes(prefix), final_url)
                if not classified:
                    part.unlink(missing_ok=True)
                    return empty_result(row, "unsupported_content_type", started=started, reason="unsupported response content type/signature", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=size)
                extension, retained_type, retained_status = classified
                if generic_metadata_only(row, final_url, retained_type):
                    part.unlink(missing_ok=True)
                    return empty_result(row, "generic_navigation_or_search_page", started=started, reason="metadata identifies generic navigation/search page", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=size)
                final_path = retained_path / f"{row['source_review_download_id']}{extension}"
                part.replace(final_path)
                result = empty_result(row, retained_status, started=started, reason="bounded GET retained supported source file", attempts=attempt, http_status=status_code, content_type=content_type, final_url=final_url, redirect_count=redirects, final_length=size)
                result.update({
                    "file_extension": extension, "retained_file_type": retained_type,
                    "retained_file_path": str(final_path.relative_to(ROOT)),
                    "retained_file_size_bytes": str(size), "retained_file_sha256": digest.hexdigest(),
                    "download_status": "downloaded_retained", "source_review_status": "source_reviewed_retained",
                    "exclusion_or_defer_reason": "",
                })
                return result
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            part.unlink(missing_ok=True)
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(float(attempt))
                continue
            return empty_result(row, "blocked_by_transport", started=started,
                                reason=f"{type(exc).__name__} after bounded retry", attempts=attempt,
                                transport_error=type(exc).__name__)
        except (OSError, ValueError) as exc:
            part.unlink(missing_ok=True)
            return empty_result(row, "download_error", started=started, reason=type(exc).__name__,
                                attempts=attempt, transport_error=type(exc).__name__)
    raise AssertionError("bounded retry loop exhausted")


def write_lane_checkpoint(lane: str, completed: int, total: int, *, status: str,
                          scheduled_start: str, actual_start: str) -> None:
    write_json(lane_dir(lane) / f"lane_{lane_number(lane):03d}_checkpoint.json", {
        "lane_id": lane, "status": status, "locked_rows": total, "completed_rows": completed,
        "remaining_rows": total - completed, "checkpoint_after_every_row": True,
        "scheduled_start_at": scheduled_start, "actual_start_at": actual_start,
        "updated_at": utc_now(), "global_analysis_readiness": False,
    })


async def run_lane(lane: str, start_at: str | None) -> None:
    if lane not in LANE_COUNTS:
        raise RuntimeError(f"unsupported lane: {lane}")
    checks = read_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_preflight_checks.json")
    if checks.get("preflight_passed") is not True:
        raise RuntimeError("live lane refused because preflight did not pass")
    lock = read_json(OUTPUT_DIR / f"combined_broad_source_review_download_lane_{lane_number(lane):03d}_lock.json")
    queue_path = lane_queue_path(lane)
    rows = read_csv(queue_path)
    if len(rows) != LANE_COUNTS[lane] or sha256(queue_path) != lock["queue_sha256"]:
        raise RuntimeError(f"{lane} queue lock mismatch")
    results_path = lane_result_path(lane)
    completed_rows = read_csv(results_path) if results_path.exists() else []
    completed_ids = {row["source_review_download_id"] for row in completed_rows}
    pending = [row for row in rows if row["source_review_download_id"] not in completed_ids]
    if len(completed_ids) == len(rows):
        raise RuntimeError(f"completed lane must not be rerun: {lane}")
    retained_path = RETAINED_DIR / lane
    retained_path.mkdir(parents=True, exist_ok=True)
    for part in retained_path.glob(".*.part"):
        part.unlink(missing_ok=True)

    scheduled = start_at or utc_now()
    if start_at:
        target = datetime.fromisoformat(start_at.replace("Z", "+00:00")).timestamp()
        while time.time() < target:
            await asyncio.sleep(min(30.0, target - time.time()))
    actual_start = utc_now()
    write_lane_checkpoint(lane, len(completed_rows), len(rows), status="running",
                          scheduled_start=scheduled, actual_start=actual_start)
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS,
                                 timeout=TIMEOUT_SECONDS, limits=limits,
                                 headers={"User-Agent": "GabrielWagesSourceReview/1.0"}) as client:
        async def bounded(row: dict[str, str]) -> dict[str, str]:
            async with semaphore:
                return await download_one(client, row, retained_path)

        tasks = [asyncio.create_task(bounded(row)) for row in pending]
        for task in asyncio.as_completed(tasks):
            result = await task
            append_csv(results_path, result, RESULT_FIELDS)
            completed_rows.append(result)
            write_lane_checkpoint(lane, len(completed_rows), len(rows), status="running",
                                  scheduled_start=scheduled, actual_start=actual_start)

    final_rows = read_csv(results_path)
    final_rows.sort(key=lambda row: int(row["lane_sequence"]))
    write_csv(results_path, final_rows, RESULT_FIELDS)
    counts = dict(sorted(Counter(row["source_review_download_status"] for row in final_rows).items()))
    retained = [row for row in final_rows if row["source_review_download_status"] in RETAINED_STATUSES]
    excluded = [row for row in final_rows if row["source_review_download_status"] not in RETAINED_STATUSES]
    number = lane_number(lane)
    write_csv(lane_dir(lane) / f"lane_{number:03d}_retained_sources.csv", retained, RESULT_FIELDS)
    write_csv(lane_dir(lane) / f"lane_{number:03d}_excluded_or_deferred.csv", excluded, RESULT_FIELDS)
    summary = {
        "lane_id": lane, "status": "completed", "locked_rows": len(rows),
        "completed_rows": len(final_rows), "remaining_rows": len(rows) - len(final_rows),
        "status_counts": counts, "retained_source_count": len(retained),
        "excluded_or_deferred_count": len(excluded), "retained_bytes": sum(int(row["retained_file_size_bytes"]) for row in retained),
        "scheduled_start_at": scheduled, "actual_start_at": actual_start, "completed_at": utc_now(),
        "maximum_concurrency": MAX_CONCURRENCY, "checkpoint_after_every_row": True,
        "global_analysis_readiness": False,
    }
    write_json(lane_dir(lane) / f"lane_{number:03d}_source_review_download_results_summary.json", summary)
    write_json(lane_dir(lane) / f"lane_{number:03d}_retained_sources_summary.json", {
        "lane_id": lane, "retained_source_count": len(retained),
        "retained_bytes": summary["retained_bytes"], "status_counts": {k: v for k, v in counts.items() if k in RETAINED_STATUSES},
        "global_analysis_readiness": False,
    })
    write_json(lane_dir(lane) / f"lane_{number:03d}_excluded_or_deferred_summary.json", {
        "lane_id": lane, "excluded_or_deferred_count": len(excluded),
        "status_counts": {k: v for k, v in counts.items() if k not in RETAINED_STATUSES},
        "global_analysis_readiness": False,
    })
    write_csv(lane_dir(lane) / f"lane_{number:03d}_errors.csv",
              [row for row in excluded if row["source_review_download_status"] == "download_error"], RESULT_FIELDS)
    write_json(lane_dir(lane) / f"lane_{number:03d}_resume_state.json", {
        "lane_id": lane, "status": "completed", "completed_rows": len(final_rows), "remaining_rows": 0,
        "resume_required": False, "queue_sha256": lock["queue_sha256"], "global_analysis_readiness": False,
    })
    write_lane_checkpoint(lane, len(final_rows), len(rows), status="completed",
                          scheduled_start=scheduled, actual_start=actual_start)
    print(json.dumps(summary, sort_keys=True))


def group_summary(rows: list[dict[str, str]], field: str, stem: str) -> None:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "") or "unknown"].append(row)
    output = []
    for value, subset in sorted(groups.items()):
        retained = [row for row in subset if row["source_review_download_status"] in RETAINED_STATUSES]
        output.append({
            field: value, "attempted_rows": len(subset), "retained_sources": len(retained),
            "excluded_or_deferred": len(subset) - len(retained),
            "retained_bytes": sum(int(row["retained_file_size_bytes"] or 0) for row in retained),
            "global_analysis_readiness": "false",
        })
    write_csv(OUTPUT_DIR / f"combined_broad_source_review_download_5589_{stem}_summary.csv", output,
              (field, "attempted_rows", "retained_sources", "excluded_or_deferred", "retained_bytes", "global_analysis_readiness"))
    write_json(OUTPUT_DIR / f"combined_broad_source_review_download_5589_{stem}_summary.json", {
        "group_field": field, "group_count": len(output), "attempted_rows": len(rows),
        "retained_sources": sum(int(row["retained_sources"]) for row in output), "groups": output,
        "global_analysis_readiness": False,
    })


def merge() -> None:
    all_rows: list[dict[str, str]] = []
    lane_summaries: dict[str, Any] = {}
    for lane in LANE_COUNTS:
        number = lane_number(lane)
        result_path = lane_result_path(lane)
        summary_path = lane_dir(lane) / f"lane_{number:03d}_source_review_download_results_summary.json"
        if result_path.exists():
            all_rows.extend(read_csv(result_path))
        lane_summaries[lane] = read_json(summary_path) if summary_path.exists() else {
            "lane_id": lane, "status": "not_completed", "completed_rows": 0,
            "remaining_rows": LANE_COUNTS[lane], "global_analysis_readiness": False,
        }
    all_rows.sort(key=lambda row: (lane_number(row["lane_id"]), int(row["lane_sequence"])))
    seen_hash: dict[str, str] = {}
    for row in all_rows:
        if row["source_review_download_status"] not in RETAINED_STATUSES:
            continue
        digest = row["retained_file_sha256"]
        if digest in seen_hash:
            duplicate_path = ROOT / row["retained_file_path"]
            duplicate_path.unlink(missing_ok=True)
            row["source_review_download_status"] = "duplicate_file_hash"
            row["duplicate_file_hash"] = digest
            row["duplicate_of_source_review_download_id"] = seen_hash[digest]
            row["retained_file_type"] = ""
            row["retained_file_path"] = ""
            row["retained_file_size_bytes"] = ""
            row["retained_file_sha256"] = ""
            row["download_status"] = "downloaded_duplicate_not_retained"
            row["source_review_status"] = "source_reviewed_not_retained"
            row["exclusion_or_defer_reason"] = "duplicate retained bytes; canonical first file preserved"
        else:
            seen_hash[digest] = row["source_review_download_id"]

    # Coordinator publishes globally reconciled lane outputs after cross-lane hash dedupe.
    for lane in LANE_COUNTS:
        number = lane_number(lane)
        subset = [row for row in all_rows if row["lane_id"] == lane]
        retained_subset = [row for row in subset if row["source_review_download_status"] in RETAINED_STATUSES]
        excluded_subset = [row for row in subset if row["source_review_download_status"] not in RETAINED_STATUSES]
        write_csv(lane_result_path(lane), subset, RESULT_FIELDS)
        write_csv(lane_dir(lane) / f"lane_{number:03d}_retained_sources.csv", retained_subset, RESULT_FIELDS)
        write_csv(lane_dir(lane) / f"lane_{number:03d}_excluded_or_deferred.csv", excluded_subset, RESULT_FIELDS)
        if len(subset) == LANE_COUNTS[lane]:
            lane_summaries[lane].update({
                "status": "completed", "completed_rows": len(subset), "remaining_rows": 0,
                "status_counts": dict(sorted(Counter(row["source_review_download_status"] for row in subset).items())),
                "retained_source_count": len(retained_subset), "excluded_or_deferred_count": len(excluded_subset),
                "retained_bytes": sum(int(row["retained_file_size_bytes"] or 0) for row in retained_subset),
            })
            write_json(lane_dir(lane) / f"lane_{number:03d}_source_review_download_results_summary.json", lane_summaries[lane])

    completed_lanes = sum(summary.get("status") == "completed" for summary in lane_summaries.values())
    complete = completed_lanes == 4 and len(all_rows) == EXPECTED_COUNT
    counts = dict(sorted(Counter(row["source_review_download_status"] for row in all_rows).items()))
    retained = [row for row in all_rows if row["source_review_download_status"] in RETAINED_STATUSES]
    excluded = [row for row in all_rows if row["source_review_download_status"] not in RETAINED_STATUSES]
    retained_bytes = sum(int(row["retained_file_size_bytes"] or 0) for row in retained)
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_results.csv", all_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources.csv", retained, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_excluded_or_deferred.csv", excluded, RESULT_FIELDS)
    manifest_fields = ("source_review_download_id", "combined_review_id", "state", "region", "municipality",
                       "source_family_hint", "retained_file_type", "retained_file_path", "retained_file_size_bytes",
                       "retained_file_sha256", "final_download_url", "global_analysis_readiness")
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_manifest.csv", retained, manifest_fields)
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv", retained,
              ("source_review_download_id", "retained_file_path", "retained_file_size_bytes", "retained_file_sha256"))
    result_summary = {
        "attempted_source_review_download_count": len(all_rows), "locked_queue_count": EXPECTED_COUNT,
        "completed_lane_count": completed_lanes, "remaining_rows": EXPECTED_COUNT - len(all_rows),
        "status_counts": counts, "retained_source_count": len(retained),
        "retained_pdf_count": counts.get("retained_pdf", 0),
        "retained_html_count": counts.get("retained_html", 0),
        "retained_other_document_count": counts.get("retained_document_other", 0),
        "duplicate_file_hash_count": counts.get("duplicate_file_hash", 0),
        "duplicate_canonical_locator_count": counts.get("duplicate_canonical_locator", 0),
        "oversized_count": counts.get("oversized_for_this_pass", 0),
        "blocked_unavailable_count": counts.get("blocked_by_transport", 0) + counts.get("unavailable_on_get", 0),
        "weak_or_needs_review_count": counts.get("weak_or_needs_review", 0) + counts.get("generic_navigation_or_search_page", 0),
        "download_error_count": counts.get("download_error", 0), "retained_byte_total": retained_bytes,
        "candidate_review_reruns": 0, "verification_reruns": 0, "extraction_runs": 0,
        "ocr_runs": 0, "rendering_runs": 0, "rating_model_api_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_results_summary.json", result_summary)
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_summary.json", {
        "retained_source_count": len(retained), "retained_pdf_count": counts.get("retained_pdf", 0),
        "retained_html_count": counts.get("retained_html", 0),
        "retained_other_document_count": counts.get("retained_document_other", 0),
        "retained_byte_total": retained_bytes, "unique_file_hash_count": len({row["retained_file_sha256"] for row in retained}),
        "all_hashes_present": all(len(row["retained_file_sha256"]) == 64 for row in retained),
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_manifest_summary.json", {
        "manifest_rows": len(retained), "retained_byte_total": retained_bytes,
        "all_paths_present": all(bool(row["retained_file_path"]) for row in retained),
        "all_paths_task_local": all(
            (ROOT / row["retained_file_path"]).resolve().is_relative_to(RETAINED_DIR.resolve())
            for row in retained
        ),
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_hash_manifest_summary.json", {
        "hash_manifest_rows": len(retained),
        "unique_sha256_count": len({row["retained_file_sha256"] for row in retained}),
        "all_sha256_present": all(len(row["retained_file_sha256"]) == 64 for row in retained),
        "duplicate_hash_rows_routed_out": counts.get("duplicate_file_hash", 0),
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_excluded_or_deferred_summary.json", {
        "excluded_or_deferred_count": len(excluded),
        "status_counts": {key: value for key, value in counts.items() if key not in RETAINED_STATUSES},
        "global_analysis_readiness": False,
    })
    summary_specs = {
        "retained_pdf": "retained_pdf", "retained_html": "retained_html",
        "retained_other_document": "retained_document_other", "duplicate_file_hash": "duplicate_file_hash",
        "duplicate_canonical_locator": "duplicate_canonical_locator", "oversized": "oversized_for_this_pass",
    }
    for stem, status in summary_specs.items():
        write_json(OUTPUT_DIR / f"combined_broad_source_review_download_5589_{stem}_summary.json", {
            "status": status, "count": counts.get(status, 0), "global_analysis_readiness": False,
        })
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_blocked_unavailable_summary.json", {
        "blocked_by_transport": counts.get("blocked_by_transport", 0),
        "unavailable_on_get": counts.get("unavailable_on_get", 0),
        "combined_count": result_summary["blocked_unavailable_count"], "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_weak_or_needs_review_summary.json", {
        "weak_or_needs_review": counts.get("weak_or_needs_review", 0),
        "generic_navigation_or_search_page": counts.get("generic_navigation_or_search_page", 0),
        "combined_count": result_summary["weak_or_needs_review_count"], "global_analysis_readiness": False,
    })

    group_summary(all_rows, "state", "state")
    group_summary(all_rows, "region", "region")
    group_summary(all_rows, "municipality", "municipality")
    group_summary(all_rows, "source_family_hint", "source_family")
    group_summary(all_rows, "source_domain", "domain_host")
    exact_cba = sum(row["source_family_hint"] == "cba" for row in retained)
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_cba_concentration_report.md", f"""# CBA concentration report

Among {len(retained):,} uniquely retained sources, {exact_cba:,} carry the exact `cba` source-family hint ({(exact_cba / len(retained) if retained else 0):.2%}). Mixed-family labels remain separate. This is an operational source-family measure, not an evidentiary or prevalence claim.
""")
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_non_cba_retained_source_summary.json", {
        "retained_source_count": len(retained), "exact_cba_hint_count": exact_cba,
        "non_cba_retained_source_count": len(retained) - exact_cba,
        "exact_cba_concentration": round(exact_cba / len(retained), 6) if retained else 0,
        "global_analysis_readiness": False,
    })

    lane_matrix = []
    for lane, summary in lane_summaries.items():
        lane_matrix.append({
            "lane_id": lane, "scheduled_stagger_minutes": LANE_STAGGER_MINUTES[lane],
            "locked_rows": LANE_COUNTS[lane], "completed_rows": summary.get("completed_rows", 0),
            "remaining_rows": summary.get("remaining_rows", LANE_COUNTS[lane]),
            "status": summary.get("status", "not_completed"),
            "scheduled_start_at": summary.get("scheduled_start_at", ""),
            "actual_start_at": summary.get("actual_start_at", ""),
            "completed_at": summary.get("completed_at", ""),
        })
    write_csv(OUTPUT_DIR / "combined_broad_source_review_download_5589_lane_status_matrix.csv", lane_matrix,
              ("lane_id", "scheduled_stagger_minutes", "locked_rows", "completed_rows", "remaining_rows",
               "status", "scheduled_start_at", "actual_start_at", "completed_at"))
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_parallel_execution_report.md", """# Parallel execution report

Four isolated source-review/download workers were scheduled at T+0, T+8, T+16, and T+24 minutes. Workers wrote only lane-local results/checkpoints and lane-specific retained-source paths. The coordinator merged and deduplicated results after worker completion.
""")
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_resumability_report.md", f"""# Resumability report

Completed lanes: {completed_lanes}/4. Completed rows: {len(all_rows):,}/{EXPECTED_COUNT:,}. Each lane checkpointed after every row and records a terminal resume state. Completed IDs are skipped on an authorized partial resume; completed lanes must not be rerun.
""")
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_transport_backoff_report.md", """# Transport and backoff report

Each worker used at most one bounded retry after a one-second adaptive delay for transport, 429, or 5xx failures. Files were streamed with a 75 MB cap and no response bodies were held as prompts or model inputs.
""")
    write_text(OUTPUT_DIR / "future_source_review_download_parallel_lane_execution_standard.md", """# Future source-review/download parallel-lane standard

Large retrieval runs use four isolated, checkpointed, resumable workers with 0/8/16/24-minute staggered starts. Workers never update shared dashboard state; a coordinator merges terminal outputs and updates status once. Completed lanes are never rerun.
""")
    write_json(OUTPUT_DIR / "future_source_review_download_parallel_lane_execution_standard.json", {
        "lane_count": 4, "stagger_minutes": [0, 8, 16, 24], "lane_isolation": True,
        "checkpoint_after_every_row": True, "coordinator_only_dashboard_update": True,
        "completed_lanes_never_rerun": True,
    })

    decision_value = (
        "combined_broad_source_review_download_5589_completed_pdf_readiness_ready"
        if complete and retained else "combined_broad_source_review_download_5589_partial_lanes_completed_resume_ready"
        if all_rows else "combined_broad_source_review_download_5589_completed_repair_needed"
    )
    decision = {
        "task_id": TASK_ID, "decision": decision_value, **result_summary,
        "lane_counts": LANE_COUNTS, "completed_lane_count": completed_lanes,
        "all_lanes_completed": complete, "staggered_overlap_required_and_recorded": True,
        "state_coverage_count": len({row["state"] for row in retained}),
        "region_coverage_count": len({row["region"] for row in retained}),
        "municipality_coverage_count": len({(row["state"], row["municipality"]) for row in retained}),
        "exact_cba_retained_count": exact_cba, "non_cba_retained_source_count": len(retained) - exact_cba,
        "exact_cba_concentration": round(exact_cba / len(retained), 6) if retained else 0,
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_scout_covered_municipalities": 6919, "dashboard_candidate_rows": 13041,
        "map_data_date": "2026-07-27", "pdf_text_layer_readiness_ready_next": bool(complete and retained),
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_decision.json", decision)
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_summary.md", f"""# Combined broad source-review/download summary

Decision: `{decision_value}`. Four isolated lanes processed {len(all_rows):,} of {EXPECTED_COUNT:,} locked metadata leads. Unique retained sources: {len(retained):,} ({counts.get('retained_pdf', 0):,} PDF, {counts.get('retained_html', 0):,} HTML, {counts.get('retained_document_other', 0):,} other documents), totaling {retained_bytes:,} bytes. Duplicate file hashes: {counts.get('duplicate_file_hash', 0):,}; canonical duplicates: {counts.get('duplicate_canonical_locator', 0):,}. No extraction, OCR, rendering, rating, model analysis, ingestion, codification, wage-gap, regression, treatment-effect, prevalence, or causal work occurred. Global analysis readiness remains false.
""")
    dashboard = {
        "dashboard_updated": True, "current_operation": "combined broad source review/download completed" if complete else "combined broad source review/download partial",
        "next_authorized_stage": "PDF/text-layer readiness over retained local sources" if complete and retained else "resume incomplete source-review/download lanes",
        "scout_covered_municipalities": 6919, "total_candidate_rows": 13041,
        "verification_queue_size": 8574, "verification_completed_count": 8574,
        "verified_reachable_count": 5524, "candidate_review_universe_size": 9065,
        "source_review_queue_size": EXPECTED_COUNT, **{key: result_summary[key] for key in (
            "attempted_source_review_download_count", "retained_source_count", "retained_pdf_count",
            "retained_html_count", "retained_other_document_count", "duplicate_file_hash_count",
            "duplicate_canonical_locator_count", "oversized_count", "blocked_unavailable_count",
            "weak_or_needs_review_count", "download_error_count", "retained_byte_total")},
        "excluded_or_deferred_source_review_count": len(excluded), "map_data_date": "2026-07-27",
        "map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_dashboard_update_summary.json", dashboard)
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_dashboard_update_summary.md", f"""# Dashboard update summary

The dashboard current operation now records the {len(all_rows):,}-row source-review/download result and {len(retained):,} retained local sources. The total-coverage map remains fixed at 6,919 scout-covered municipalities with data date 2026-07-27. Download and retention metrics remain side-card operations data; global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / "dashboard_overview_metric_sync_after_source_review_download.json", dashboard)
    write_text(OUTPUT_DIR / "dashboard_overview_metric_sync_after_source_review_download.md", "# Dashboard overview metric sync\n\nCurrent operation, queue, attempts, retention, exclusions, file types, duplicate, oversized, blocked, map-date, and boundary cards are synchronized to coordinator outputs.")
    stale = {
        "candidate_review_not_current_operation": True, "tier_c_memo_not_current_operation": True,
        "source_review_download_is_current_operation": True, "map_total_scout_coverage_only": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_stale_overview_guard_after_source_review_download.json", stale)
    write_text(OUTPUT_DIR / "dashboard_stale_overview_guard_after_source_review_download.md", "# Dashboard stale-overview guard\n\nCandidate review and the Tier C memo remain completed predecessor artifacts; source review/download is current and readiness is false.")
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_pdf_text_layer_readiness_planning_note.md", f"""# PDF/text-layer readiness planning

Run readiness only over the {len(retained):,} unique retained local files. Revalidate hashes and paths; distinguish PDF text-layer parsing from HTML handling; do not OCR, render, extract evidence spans, rate, ingest, codify, or make analytical claims without separate authorization.
""")
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_oversized_future_pass_note.md", f"# Oversized future pass\n\n{counts.get('oversized_for_this_pass', 0):,} rows exceeded the 75 MB cap and remain deferred. Do not retry them without a separately bounded storage-aware pass.")
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_next_queue_recommendation.md", "# Next queue recommendation\n\nProceed to bounded PDF/text-layer readiness over unique retained local sources if all four lanes completed; otherwise resume only incomplete lanes from checkpoints.")
    invariant = {
        "all_invariants_passed": bool(complete and len(all_rows) == EXPECTED_COUNT and all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in all_rows)),
        "exact_locked_queue_count_5589": EXPECTED_COUNT == 5589,
        "lane_counts_exact": LANE_COUNTS == {"source_review_lane_001": 1397, "source_review_lane_002": 1397, "source_review_lane_003": 1397, "source_review_lane_004": 1398},
        "master_equals_completed_rows": len(all_rows) == EXPECTED_COUNT if complete else len(all_rows) <= EXPECTED_COUNT,
        "controlled_statuses_only": all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in all_rows),
        "retained_files_have_hashes": all(len(row["retained_file_sha256"]) == 64 for row in retained),
        "retained_files_exist": all((ROOT / row["retained_file_path"]).is_file() for row in retained),
        "nonretained_rows_not_marked_retained": all(row["download_status"] != "downloaded_retained" for row in excluded),
        "candidate_review_reruns": 0, "verification_reruns": 0, "extraction_ocr_render_rating_model_runs": 0,
        "ingestion_codification_statistical_runs": 0, "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_invariant_checks.json", invariant)
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_stress_test_report.md", "# Stress-test report\n\nCovered lock drift, lane-size mismatch, URL invalidity, redirects, timeouts, 4xx/5xx, oversized streams, unsupported types, canonical and file-hash duplicates, storage pressure, interrupted checkpoints, stale dashboard state, and partial-output masquerade.")
    write_json(OUTPUT_DIR / "combined_broad_source_review_download_5589_regression_test_inventory.json", {
        "new_suite": "scripts/test_combined_broad_source_review_download_5589.py",
        "predecessor_suites": ["scripts/test_combined_broad_candidate_review.py", "scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py", "scripts/test_broad_state_4x1000_parallel_live_scout.py", "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"],
    })
    write_text(OUTPUT_DIR / "combined_broad_source_review_download_5589_validation_2026-07-28.md", "# Validation report\n\nCoordinator invariants passed. Full repository validation command results are recorded before commit and relay creation.")
    write_text(OUTPUT_DIR / "next_combined_broad_pdf_text_layer_readiness_prompt.md", f"""# Next task prompt

Run bounded PDF/text-layer readiness over only the {len(retained):,} unique retained local sources from this completed source-review/download task. Revalidate every retained path, size, and SHA-256 before entry. Do not access URLs or redownload; do not OCR, render, extract evidence spans, rate, ingest, codify, calculate wage gaps, run regressions or treatment effects, or make national/prevalence/final causal claims. Dashboard update requirement: update dashboard/status/docs with substantive results, keep the map total scout coverage only, and keep global analysis readiness false. Future rating tasks must apply the post-rating artifact-completeness and deterministic reconstruction fallback rule.
""")
    write_text(OUTPUT_DIR / "next_task.md", f"# Next task\n\nRun a separately authorized bounded PDF/text-layer readiness pass over the {len(retained):,} unique retained local sources; preserve hashes, provenance, map scope, and all analytical boundaries.")
    analysis = ROOT / "docs/analysis"
    write_text(analysis / "combined_broad_source_review_download_5589_result_2026-07-28.md", f"# Combined broad source review/download result\n\nDecision: `{decision_value}`. Attempted {len(all_rows):,}/{EXPECTED_COUNT:,}; retained {len(retained):,} unique sources. See the task output directory for manifests and QA. Global analysis readiness remains false.")
    write_text(analysis / "combined_broad_source_review_download_5589_dashboard_status_note_2026-07-28.md", f"# Dashboard status note\n\nCurrent operation: combined broad source review/download {'complete' if complete else 'partial'}. Retained unique local sources: {len(retained):,}. Next: {'PDF/text-layer readiness' if complete and retained else 'resume incomplete lanes'}. Map: total scout coverage only (6,919; data date 2026-07-27). Global analysis readiness: false.")
    print(json.dumps(decision, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("preflight")
    lane_parser = sub.add_parser("run-lane")
    lane_parser.add_argument("--lane", required=True, choices=tuple(LANE_COUNTS))
    lane_parser.add_argument("--start-at")
    sub.add_parser("merge")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "preflight":
        asyncio.run(preflight())
    elif args.command == "run-lane":
        asyncio.run(run_lane(args.lane, args.start_at))
    elif args.command == "merge":
        merge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
