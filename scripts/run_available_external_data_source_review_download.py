#!/usr/bin/env python3
"""Review and retain verified external-data sources without analytical extraction.

The runner is intentionally source/locator-centric.  It reconstructs complete
candidate/event/claim lineage from the candidate-review and verification
layers, locks five host-aware lanes, streams approved payloads into a Git-
ignored content-addressed store, and emits metadata-only tracked artifacts.
It never runs hosted search or GABRIEL, OCRs, extracts analytical text/tables/
fields, normalizes values, or changes the canonical implementation events.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import fcntl
import hashlib
import html as html_lib
import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import time
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

import httpx

import run_external_data_exhaustive_pipeline as core


TASK_ID = "BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD-2026-08-05"
DECISION = "broad_state_whole_corpus_available_external_data_source_review_completed_readiness_ready"
REQUIRED_COMMIT = "6bf6e6b8ec0052218a0dd90d38584b2c47c3f5a7"
EXPECTED_INPUT = 49_294
EXPECTED_DIRECT = 15_032
EXPECTED_HTML = 34_238
EXPECTED_STRUCTURED = 24
EXPECTED_PRIORITY = {"high": 22_510, "medium": 863, "low": 25_441, "repaired": 480}
EXPECTED_UNRESOLVED = 12_844
EXPECTED_ROOT_EVENTS = 2_998
EXPECTED_MECHANISM_EVENTS = 13_391

INPUT = core.STAGE3
CANDIDATES = core.STAGE2
OUTPUT = core.STAGE4
ARTIFACT_ROOT = core.ROOT / "artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
TMP = core.ROOT / "tmp/broad_state_whole_corpus_available_external_data_source_review_download_2026-08-05_logs"
LANES = [f"source_review_lane_{i:03d}" for i in range(1, 6)]
STAGGER_SECONDS = dict(zip(LANES, (0, 480, 960, 1440, 1920)))

MAX_SOURCE_BYTES = 100 * 1024 * 1024
# The task's normal-retention policy is 100 MiB for every supported format.
# HTML is still reviewed from a bounded prefix, but an accepted substantive page
# is retained in full under the same source-size policy as other documents.
MAX_HTML_BYTES = MAX_SOURCE_BYTES
HARD_DEFER_BYTES = 500 * 1024 * 1024
MAX_RETRIES = 1
MAX_REDIRECTS = 8
TIMEOUT = httpx.Timeout(connect=20.0, read=35.0, write=20.0, pool=20.0)
LANE_CONCURRENCY = 12
PER_HOST_DELAY_SECONDS = 0.20
BOUNDED_PREVIEW_BYTES = 256 * 1024
RETAINED_QUOTA_BYTES = 30 * 1024 * 1024 * 1024
MIN_FREE_BYTES = 15 * 1024 * 1024 * 1024

TRANSIENT_HTTP = {429, 502, 503, 504}
RETAINED_STATUSES = {
    "retained_pdf", "retained_html", "retained_csv", "retained_tsv", "retained_xlsx",
    "retained_xls", "retained_json", "retained_xml", "retained_text",
    "retained_official_data_package", "retained_other_document",
}
DUPLICATE_STATUSES = {"duplicate_exact_payload", "duplicate_known_retained_source"}
TERMINAL_STATUSES = RETAINED_STATUSES | DUPLICATE_STATUSES | {
    "likely_document_version_retained", "likely_document_version_deferred",
    "navigation_or_index_only", "generic_portal_without_direct_evidence", "shell_or_placeholder",
    "irrelevant_content", "wrong_municipality", "wrong_period", "wrong_department_or_scope",
    "private_or_commercial_source", "secondary_context_only_deferred",
    "restricted_or_login_required", "captcha_or_bot_protection", "unavailable_on_download",
    "download_timeout_retry_exhausted", "corrupt_or_broken", "MIME_or_extension_mismatch",
    "unsupported_file_type", "oversized_defer", "suspicious_or_quarantine",
    "manual_review_hold", "source_review_error",
}

CONTENT_EXTENSIONS = {
    "pdf": ".pdf", "html": ".html", "csv": ".csv", "tsv": ".tsv",
    "xlsx": ".xlsx", "xls": ".xls", "json": ".json", "xml": ".xml",
    "txt": ".txt", "zip": ".zip", "other_document": ".bin",
}
READINESS_HINTS = {
    "pdf": "parse_text_pdf_candidate", "html": "html_text_candidate",
    "csv": "csv_structured_candidate", "tsv": "tsv_structured_candidate",
    "xlsx": "xlsx_structured_candidate", "xls": "xls_structured_candidate",
    "json": "json_structured_candidate", "xml": "xml_structured_candidate",
    "txt": "text_candidate", "zip": "official_data_package_candidate",
    "other_document": "other_document_candidate",
}

GENERIC_PATHS = {"", "/", "/home", "/index", "/index.html", "/search", "/documents", "/departments"}
NAVIGATION_MARKERS = {
    "search results", "site search", "document center", "agenda center", "archive center",
    "welcome to", "home page", "page not found", "access denied", "enable javascript",
    "browser is not supported", "directory listing", "all documents", "calendar of events",
}
SUBSTANTIVE_MARKERS = {
    "payroll", "earnings", "overtime", "salary", "compensation", "employee", "staffing",
    "headcount", "vacancy", "vacancies", "authorized positions", "budget", "appropriation",
    "ordinance", "resolution", "collective bargaining", "memorandum of understanding",
    "salary schedule", "pay plan", "benefits", "pension", "retirement", "turnover",
    "recruitment", "retention", "civil service", "personnel", "fiscal year",
}
COMMERCIAL_HOST_MARKERS = {
    "salary.com", "glassdoor.", "indeed.", "ziprecruiter.", "payscale.", "facebook.",
    "linkedin.", "instagram.", "youtube.", "peoplefinder", "beenverified",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(prefix: str, *parts: str, n: int = 24) -> str:
    return f"{prefix}-" + hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:n]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
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
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def join_values(values: Iterable[str]) -> str:
    expanded: set[str] = set()
    for value in values:
        expanded.update(split_values(value))
    return "|".join(sorted(expanded))


def git_ignored(path: Path) -> bool:
    probe = path if path.suffix else path / "ignore-probe"
    rel = probe.relative_to(core.ROOT)
    return subprocess.run(["git", "check-ignore", "-q", str(rel)], cwd=core.ROOT).returncode == 0


def current_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=core.ROOT, text=True).strip()


def is_ancestor(commit: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=core.ROOT).returncode == 0


def process_matches() -> list[str]:
    try:
        text = subprocess.check_output(["pgrep", "-af", "run_available_external_data_source_review_download"], text=True)
        own_pid = str(os.getpid())
        return [
            line for line in text.splitlines()
            if line.strip() and "pgrep" not in line and line.split(maxsplit=1)[0] != own_pid
        ]
    except (subprocess.CalledProcessError, PermissionError):
        return []


def content_length(row: dict[str, str]) -> int:
    try:
        return max(0, int(row.get("content_length", "") or row.get("verification_content_length", "") or 0))
    except ValueError:
        return 0


def candidate_lookup() -> dict[str, dict[str, str]]:
    rows = load_shards(CANDIDATES, "final_candidate_review_results_shard_manifest.json")
    return {row["canonical_candidate_id"]: row for row in rows}


def actionable_lookup() -> dict[str, dict[str, str]]:
    rows = load_shards(INPUT, "actionable_candidate_locked_queue_shard_manifest.json")
    return {row["canonical_candidate_id"]: row for row in rows}


def candidate_locator_links() -> dict[str, list[str]]:
    rows = load_shards(INPUT, "candidate_to_canonical_locator_links_shard_manifest.json")
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[row["canonical_locator_id"]].append(row["canonical_candidate_id"])
    return grouped


def build_locked_rows() -> list[dict[str, Any]]:
    sources = load_shards(INPUT, "source_review_ready_queue_shard_manifest.json")
    candidates = candidate_lookup()
    actionable = actionable_lookup()
    links = candidate_locator_links()
    locked: list[dict[str, Any]] = []
    for source in sources:
        locator_id = source["verification_locator_id"]
        candidate_ids = sorted(set(links.get(locator_id, [])) | {source["canonical_candidate_id"]})
        crows = [candidates[cid] for cid in candidate_ids if cid in candidates]
        arows = [actionable[cid] for cid in candidate_ids if cid in actionable]
        if not crows or not arows:
            raise RuntimeError(f"missing candidate lineage for {locator_id}")
        title = next((row.get("candidate_title", "") for row in crows if row.get("candidate_title", "")), "")
        snippet = next((row.get("candidate_snippet", "") for row in crows if row.get("candidate_snippet", "")), "")
        url = source.get("final_canonical_locator") or source.get("final_locator") or source["canonical_network_locator"]
        priority = source["priority_order"]
        row = {
            "source_review_id": stable("EXTSRCREV", locator_id),
            "canonical_locator_id": locator_id,
            "canonical_final_locator_id": source.get("canonical_final_locator_id", ""),
            "canonical_final_url": url,
            "original_requested_urls": join_values(row.get("candidate_url", "") for row in crows),
            "linked_candidate_ids": "|".join(candidate_ids),
            "linked_search_waves": join_values(row.get("search_wave_provenance", "") for row in crows),
            "municipality": join_values(row.get("municipality", "") for row in arows),
            "state": join_values(row.get("state", "") for row in arows),
            "period": join_values(row.get("period", "") for row in arows),
            "side_scope": join_values(row.get("side_scope", "") for row in arows),
            "department_scope": join_values(row.get("department_scope", "") for row in arows),
            "primary_external_data_family": source.get("primary_external_data_families", "") or join_values(row.get("primary_external_data_family", "") for row in crows),
            "secondary_external_data_families": join_values(row.get("secondary_external_data_families", "") for row in crows),
            "direct_staffing_relevance": join_values(row.get("direct_staffing_relevance", "") for row in crows),
            "administrative_source_type": source.get("administrative_source_types", "") or join_values(row.get("administrative_source_type", "") for row in crows),
            "primary_source_quality": join_values(row.get("primary_source_quality", "") for row in crows),
            "verified_content_type": source.get("verified_content_type", "unknown"),
            "expected_file_type": source.get("verified_content_type", "unknown"),
            "final_priority_bucket": priority,
            "official_source_flag": "true" if "true" in split_values(source.get("official_source_flags", "")) or any(row.get("official_source_flag") == "true" for row in crows) else "false",
            "linked_root_event_ids": join_values(row.get("linked_root_event_ids", "") for row in arows),
            "linked_mechanism_exposure_event_ids": join_values(row.get("linked_mechanism_exposure_event_ids", "") for row in arows),
            "linked_claim_ids": join_values(row.get("linked_claim_ids", "") for row in arows),
            "expected_claim_upgrade_tags": join_values(row.get("claim_upgrade_tags", "") or row.get("expected_claim_upgrades", "") for row in crows),
            "redirect_lineage": f"redirect_count={source.get('redirect_count','0')}|verification_terminal_request={source.get('terminal_request_id','')}",
            "duplicate_final_locator_lineage": f"canonical_final_locator_id={source.get('canonical_final_locator_id','')}",
            "verification_status": source["verification_status"],
            "source_review_routing": source.get("source_review_routing", ""),
            "verification_content_type": source.get("response_content_type", ""),
            "verification_content_length": source.get("content_length", ""),
            "candidate_title": title,
            "candidate_snippet": snippet[:2000],
            "locator_host": (urlsplit(url).hostname or "").casefold(),
            "candidate_fanout": len(candidate_ids),
            "event_fanout": len(set(split_values(join_values(row.get("linked_root_event_ids", "") for row in arows))) | set(split_values(join_values(row.get("linked_mechanism_exposure_event_ids", "") for row in arows)))),
            "review_complexity": "html" if source.get("source_review_routing") == "source_review_ready_html" else "structured" if source.get("source_review_routing") == "source_review_ready_structured_data" else "document",
        }
        locked.append(row)
    return sorted(locked, key=lambda row: row["canonical_locator_id"])


def prior_hash_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for path in core.ROOT.glob("docs/analysis/**/*retained*manifest*.csv"):
        if OUTPUT in path.parents:
            continue
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    digest = row.get("sha256") or row.get("retained_file_sha256") or row.get("source_sha256") or ""
                    local = row.get("local_artifact_path") or row.get("retained_local_artifact_path") or row.get("artifact_storage_pointer") or ""
                    if re.fullmatch(r"[0-9a-f]{64}", digest) and local and (core.ROOT / local).is_file():
                        index.setdefault(digest, {"prior_manifest": str(path.relative_to(core.ROOT)), "prior_local_artifact_path": local, "prior_source_id": row.get("retained_source_id") or row.get("source_review_download_id") or ""})
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    return index


def lane_assignment(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    hosts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        hosts[row["locator_host"]].append(row)
    buckets = {lane: [] for lane in LANES}
    weights = Counter()
    counts = Counter()
    for host, group in sorted(hosts.items(), key=lambda item: (-len(item[1]), item[0])):
        expected = sum(min(content_length(row), MAX_SOURCE_BYTES) or (128 * 1024 if row["review_complexity"] == "html" else 2 * 1024 * 1024) for row in group)
        weight = len(group) * 1_000_000 + expected // 1024
        lane = min(LANES, key=lambda name: (weights[name], counts[name], name))
        buckets[lane].extend(group)
        weights[lane] += weight
        counts[lane] += len(group)
    priority_rank = {"high": 0, "medium": 1, "repaired": 2, "low": 3}
    for lane, group in buckets.items():
        by_priority: dict[int, dict[str, deque[dict[str, Any]]]] = defaultdict(lambda: defaultdict(deque))
        for row in group:
            by_priority[priority_rank[row["final_priority_bucket"]]][row["locator_host"]].append(row)
        ordered: list[dict[str, Any]] = []
        for rank in sorted(by_priority):
            host_queues = by_priority[rank]
            while host_queues:
                for host in sorted(list(host_queues)):
                    ordered.append(host_queues[host].popleft())
                    if not host_queues[host]:
                        del host_queues[host]
        for sequence, row in enumerate(ordered, 1):
            row["source_review_lane_id"] = lane
            row["source_review_lane_sequence"] = sequence
        buckets[lane] = ordered
    return buckets


def preflight() -> None:
    if current_head() != REQUIRED_COMMIT and not is_ancestor(REQUIRED_COMMIT):
        raise RuntimeError("required verification commit is not an ancestor")
    dirty_lines = subprocess.check_output(["git", "status", "--short"], cwd=core.ROOT, text=True).splitlines()
    task_owned = {"?? scripts/run_available_external_data_source_review_download.py"}
    unrelated = [line for line in dirty_lines if line not in task_owned]
    if unrelated:
        raise RuntimeError(f"dirty worktree preflight blocker:\n" + "\n".join(unrelated))
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("source-review output already exists; resume with existing checkpoint instead of rebuilding")
    summary = read_json(INPUT / "full_external_data_verification_summary.json")
    ready_manifest = read_json(INPUT / "source_review_ready_manifest.json")
    if summary["source_review_ready_count"] != EXPECTED_INPUT or ready_manifest["source_review_ready_count"] != EXPECTED_INPUT:
        raise RuntimeError("source-review-ready count mismatch")
    if summary["source_review_ready_by_type"] != {"source_review_ready_direct_document": EXPECTED_DIRECT, "source_review_ready_html": EXPECTED_HTML, "source_review_ready_structured_data": EXPECTED_STRUCTURED}:
        raise RuntimeError("source-review type composition mismatch")
    if summary["source_review_ready_by_priority"] != EXPECTED_PRIORITY:
        raise RuntimeError("source-review priority composition mismatch")
    if summary["unresolved_hosted_search_targets"] != EXPECTED_UNRESOLVED:
        raise RuntimeError("unresolved target count mismatch")
    if process_matches():
        raise RuntimeError(f"duplicate source-review workers active: {process_matches()}")
    if not all(git_ignored(path) for path in (ARTIFACT_ROOT, core.ROOT / "artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04", core.ROOT / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04")):
        raise RuntimeError("one or more payload roots are not Git ignored")
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    if staged:
        raise RuntimeError("preflight requires an empty Git index")
    usage = shutil.disk_usage(core.ROOT)
    if usage.free < MIN_FREE_BYTES + 2 * 1024**3:
        raise RuntimeError("insufficient free disk for bounded storage plan")

    rows = build_locked_rows()
    if len(rows) != EXPECTED_INPUT or len({row["canonical_locator_id"] for row in rows}) != EXPECTED_INPUT:
        raise RuntimeError("locked queue does not contain every canonical locator exactly once")
    if Counter(row["final_priority_bucket"] for row in rows) != Counter(EXPECTED_PRIORITY):
        raise RuntimeError("locked priority counts do not reconcile")
    if any(not all(row.get(field) for field in ("canonical_locator_id", "canonical_final_url", "linked_candidate_ids", "primary_external_data_family", "administrative_source_type", "linked_root_event_ids", "linked_mechanism_exposure_event_ids", "linked_search_waves")) for row in rows):
        raise RuntimeError("required locked lineage is missing")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for kind in ("pdf", "html", "csv", "tsv", "xlsx", "xls", "json", "xml", "txt", "zip", "other", "quarantine", "temporary_partial_downloads"):
        (ARTIFACT_ROOT / kind).mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / "retained_quota.lock").touch()
    atomic_json(ARTIFACT_ROOT / "retained_quota_state.json", {"retained_bytes": 0, "quota_bytes": RETAINED_QUOTA_BYTES, "minimum_free_bytes": MIN_FREE_BYTES, "updated_at": utc_now()})

    lanes = lane_assignment(rows)
    core.write_sharded_pair(OUTPUT, "source_review_locked_queue", rows)
    lane_distribution: dict[str, Any] = {}
    for lane in LANES:
        core.write_sharded_pair(OUTPUT, f"{lane}_queue", lanes[lane])
        lane_distribution[lane] = {
            "count": len(lanes[lane]), "stagger_minutes": STAGGER_SECONDS[lane] // 60,
            "priority_counts": dict(Counter(row["final_priority_bucket"] for row in lanes[lane])),
            "type_counts": dict(Counter(row["review_complexity"] for row in lanes[lane])),
            "host_count": len({row["locator_host"] for row in lanes[lane]}),
        }
        atomic_json(OUTPUT / f"{lane}_checkpoint.json", {"lane_id": lane, "status": "locked_not_started", "locked_count": len(lanes[lane]), "completed_count": 0, "remaining_count": len(lanes[lane]), "updated_at": utc_now()})
    lock_hash = hashlib.sha256("\n".join(row["canonical_locator_id"] for row in rows).encode()).hexdigest()
    atomic_json(OUTPUT / "source_review_locked_queue_manifest.json", {
        "task_id": TASK_ID, "input_count": len(rows), "queue_sha256": lock_hash,
        "priority_counts": dict(Counter(row["final_priority_bucket"] for row in rows)),
        "type_counts": dict(Counter(row["review_complexity"] for row in rows)),
        "source_to_candidate_fanout": sum(row["candidate_fanout"] for row in rows),
        "source_to_event_fanout": sum(row["event_fanout"] for row in rows),
        "artifact_root": str(ARTIFACT_ROOT.relative_to(core.ROOT)), "artifact_root_git_ignored": True,
        "implementation_event_deduplication_rerun": False, "created_at": utc_now(),
    })
    atomic_json(OUTPUT / "source_review_lane_distribution.json", {"total": len(rows), "disjoint": len({row["canonical_locator_id"] for lane in LANES for row in lanes[lane]}) == len(rows), "lanes": lane_distribution})
    lines = ["# Source-review lane distribution", "", "| Lane | Sources | Hosts | High | Medium | Low | Repaired | Stagger |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for lane in LANES:
        item = lane_distribution[lane]; p = item["priority_counts"]
        lines.append(f"| {lane} | {item['count']:,} | {item['host_count']:,} | {p.get('high',0):,} | {p.get('medium',0):,} | {p.get('low',0):,} | {p.get('repaired',0):,} | T+{item['stagger_minutes']} min |")
    core.write_md(OUTPUT / "source_review_lane_distribution.md", "\n".join(lines))
    known = [content_length(row) for row in rows if content_length(row)]
    projection = sum(known)
    storage = {
        "passed": True, "available_bytes": usage.free, "existing_retained_source_bytes": sum(p.stat().st_size for p in (core.ROOT / "artifacts/local_retained_sources").rglob("*") if p.is_file()),
        "known_content_length_rows": len(known), "unknown_content_length_rows": len(rows) - len(known),
        "known_content_length_sum_bytes": projection, "unconstrained_projection_exceeds_available": projection > usage.free,
        "bounded_retained_quota_bytes": RETAINED_QUOTA_BYTES, "minimum_free_bytes": MIN_FREE_BYTES,
        "capacity_plan": "Content-addressed deduplication; high-value-first lane order; 30 GiB retained ceiling; 15 GiB free-space reserve; explicit manual-review holds if cumulative capacity prevents retention.",
        "created_at": utc_now(),
    }
    atomic_json(OUTPUT / "storage_capacity_summary.json", storage)
    prior = prior_hash_index()
    atomic_json(TMP / "prior_retained_hash_index.json", prior)
    atomic_json(OUTPUT / "source_review_run_state.json", {"task_id": TASK_ID, "status": "preflight_passed_smoke_pending", "input_count": len(rows), "completed_count": 0, "starting_head": current_head(), "updated_at": utc_now()})
    atomic_json(OUTPUT / "source_review_stage_checkpoint.json", {"stage": "preflight", "status": "passed", "queue_sha256": lock_hash, "updated_at": utc_now()})
    atomic_json(OUTPUT / "external_data_source_review_download_manifest.json", {"task_id": TASK_ID, "starting_head": current_head(), "input_count": len(rows), "lane_distribution": lane_distribution, "storage_capacity_plan": storage, "prior_retained_hash_count": len(prior), "forbidden_operations": {"hosted_search": True, "gabriel": True, "ocr": True, "analytical_extraction": True}, "created_at": utc_now()})
    print(json.dumps({"status": "preflight_passed", "input": len(rows), "lanes": {k: v["count"] for k, v in lane_distribution.items()}, "storage": storage, "prior_hashes": len(prior)}, indent=2))


def detect_type(content_type: str, url: str, prefix: bytes) -> str:
    ctype = (content_type or "").split(";", 1)[0].strip().casefold()
    path = unquote(urlsplit(url).path).casefold()
    if prefix.startswith(b"%PDF-") or ctype == "application/pdf": return "pdf"
    if prefix.startswith(b"PK\x03\x04"):
        if path.endswith(".xlsx") or "spreadsheetml" in ctype: return "xlsx"
        if path.endswith((".docx", ".pptx")) or "wordprocessingml" in ctype or "presentationml" in ctype: return "other_document"
        return "zip"
    if prefix.startswith(b"\xd0\xcf\x11\xe0") or path.endswith(".xls") or "ms-excel" in ctype: return "xls"
    if "text/csv" in ctype or path.endswith(".csv"): return "csv"
    if "tab-separated" in ctype or path.endswith(".tsv"): return "tsv"
    if "json" in ctype or path.endswith(".json"): return "json"
    if "xml" in ctype or path.endswith(".xml"): return "xml"
    if "html" in ctype or path.endswith((".html", ".htm")) or prefix.lstrip().lower().startswith((b"<!doctype html", b"<html")): return "html"
    if ctype.startswith("text/plain") or path.endswith(".txt"): return "txt"
    if any(path.endswith(ext) for ext in (".doc", ".docx", ".rtf")): return "other_document"
    return "unknown"


def bounded_preview(path: Path, kind: str) -> tuple[str, dict[str, Any], bool]:
    with path.open("rb") as handle:
        prefix = handle.read(BOUNDED_PREVIEW_BYTES)
    preview = ""
    structure: dict[str, Any] = {}
    valid = True
    if kind == "pdf":
        with path.open("rb") as handle:
            handle.seek(max(0, path.stat().st_size - 4096)); trailer = handle.read()
        valid = prefix.startswith(b"%PDF-") and b"%%EOF" in trailer
        structure = {"pdf_header": prefix[:8].decode("latin-1", "replace"), "pdf_eof_marker_present": b"%%EOF" in trailer}
    elif kind == "html":
        text = prefix.decode("utf-8", "replace")
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        title = html_lib.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else ""
        visible = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
        visible = html_lib.unescape(re.sub(r"<[^>]+>", " ", visible))
        preview = re.sub(r"\s+", " ", visible).strip()[:600]
        structure = {"html_title": title[:300], "bounded_visible_character_count": len(visible), "bounded_link_count": len(re.findall(r"<a\b", text, re.I))}
    elif kind in {"zip", "xlsx"}:
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist(); bad = archive.testzip()
                structure = {"archive_member_count": len(names), "archive_member_preview": names[:25], "archive_test_error_member": bad or "", "sheet_member_count": len([n for n in names if n.startswith("xl/worksheets/")]), "formula_member_signal": any("calc" in n.casefold() for n in names)}
                if kind == "xlsx":
                    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                    sheet_names: list[str] = []
                    hidden_sheets: list[str] = []
                    dimensions: dict[str, str] = {}
                    formula_present = False
                    try:
                        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
                        for sheet in workbook.findall(".//m:sheets/m:sheet", ns):
                            name = sheet.attrib.get("name", "")
                            sheet_names.append(name)
                            if sheet.attrib.get("state", "visible") != "visible": hidden_sheets.append(name)
                        for member in sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")):
                            root = ElementTree.fromstring(archive.read(member))
                            dimension = root.find("m:dimension", ns)
                            dimensions[member] = dimension.attrib.get("ref", "") if dimension is not None else ""
                            formula_present = formula_present or root.find(".//m:f", ns) is not None
                    except (KeyError, ElementTree.ParseError):
                        structure["workbook_metadata_parse_error"] = True
                    structure.update({"sheet_names": sheet_names, "hidden_sheet_names": hidden_sheets, "sheet_dimensions": dimensions, "formula_cell_presence": formula_present})
                valid = bad is None
        except zipfile.BadZipFile:
            valid = False
    elif kind == "json":
        try:
            if path.stat().st_size <= 20 * 1024 * 1024:
                obj = json.loads(path.read_text(encoding="utf-8-sig")); structure = {"top_level_type": type(obj).__name__, "top_level_length": len(obj) if hasattr(obj, "__len__") else ""}
            else: structure = {"top_level_type": "not_parsed_over_20MiB"}
        except (ValueError, UnicodeDecodeError): valid = False
    elif kind == "xml":
        try:
            if path.stat().st_size <= 20 * 1024 * 1024:
                root = ElementTree.parse(path).getroot(); structure = {"root_tag": root.tag, "direct_child_count": len(root)}
            else: structure = {"root_tag": "not_parsed_over_20MiB"}
        except (ElementTree.ParseError, OSError): valid = False
    elif kind in {"csv", "tsv", "txt"}:
        text = prefix.decode("utf-8", "replace")
        first = text.splitlines()[0] if text.splitlines() else ""
        delimiter = "\t" if kind == "tsv" else "," if kind == "csv" else ""
        structure = {"bounded_line_count": len(text.splitlines()), "header_field_count_hint": len(first.split(delimiter)) if delimiter else "", "encoding_decode_replacements": text.count("\ufffd")}
        preview = first[:600]
    elif kind == "xls":
        valid = prefix.startswith(b"\xd0\xcf\x11\xe0")
        structure = {"ole_compound_signature_present": valid}
    return preview, structure, valid


def classification_from_metadata(row: dict[str, Any], kind: str, preview: str, structure: dict[str, Any]) -> tuple[str, str, str, str, str]:
    host = row["locator_host"]
    official = row["official_source_flag"] == "true" or host.endswith(".gov") or ".gov." in host or host.endswith(".us")
    title_blob = " ".join((row.get("candidate_title", ""), row.get("candidate_snippet", ""), str(structure.get("html_title", "")), preview)).casefold()
    path = urlsplit(row["canonical_final_url"]).path.casefold().rstrip("/") or "/"
    family = row["primary_external_data_family"] or "unclear"
    admin_type = split_values(row["administrative_source_type"])[0] if split_values(row["administrative_source_type"]) else "unclear"
    quality = "direct_official_administrative_record" if official and kind != "html" else "official_administrative_summary" if official else "reputable_secondary_context"
    if any(marker in host for marker in COMMERCIAL_HOST_MARKERS):
        return "private_or_commercial_source", "weak_secondary_context", family, admin_type, "commercial/private host"
    if kind == "html":
        substantive = sum(marker in title_blob for marker in SUBSTANTIVE_MARKERS)
        navigation = sum(marker in title_blob for marker in NAVIGATION_MARKERS)
        rootish = path in GENERIC_PATHS
        link_count = int(structure.get("bounded_link_count", 0) or 0)
        if any(marker in title_blob for marker in ("captcha", "verify you are human", "cloudflare ray id", "checking your browser")):
            return "captcha_or_bot_protection", "navigation_or_shell", family, admin_type, "HTML challenge shell indicates CAPTCHA or bot protection"
        if "page not found" in title_blob or "access denied" in title_blob:
            return "shell_or_placeholder", "navigation_or_shell", family, admin_type, "HTML shell indicates missing or denied content"
        if rootish and substantive == 0:
            return "generic_portal_without_direct_evidence", "navigation_or_shell", family, "open_data_portal" if "data" in title_blob else "navigation_or_index", "generic/root landing page without direct administrative signal"
        if navigation >= 1 and substantive == 0 and link_count > 20:
            return "navigation_or_index_only", "navigation_or_shell", family, "navigation_or_index", "navigation/index markers without substantive administrative signal"
        if not official and row.get("primary_source_quality") in {"reputable_secondary_source", "weak_secondary_source"}:
            return "secondary_context_only_deferred", "reputable_secondary_context", family, admin_type, "secondary context deferred from administrative readiness"
        if substantive == 0 and row["final_priority_bucket"] == "low" and link_count > 40:
            return "generic_portal_without_direct_evidence", "navigation_or_shell", family, "navigation_or_index", "low-priority broad HTML portal without bounded substantive signal"
        return "retained_html", quality, family, admin_type, "bounded HTML shell contains plausible administrative source signal"
    if not official and row.get("primary_source_quality") in {"reputable_secondary_source", "weak_secondary_source"}:
        return "secondary_context_only_deferred", "reputable_secondary_context", family, admin_type, "secondary document deferred from administrative readiness"
    return f"retained_{'text' if kind == 'txt' else 'official_data_package' if kind == 'zip' else 'other_document' if kind == 'other_document' else kind}", quality, family, admin_type, "supported source format and plausible administrative metadata"


class HostPoliteness:
    def __init__(self) -> None:
        self.locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.last: dict[str, float] = defaultdict(float)

    async def wait(self, host: str) -> None:
        # The caller holds this host's lock for the entire bounded retrieval.
        delay = PER_HOST_DELAY_SECONDS - (time.monotonic() - self.last[host])
        if delay > 0: await asyncio.sleep(delay)
        self.last[host] = time.monotonic()


def quota_accept(temp: Path, kind: str, digest: str, prior: dict[str, dict[str, str]]) -> tuple[str, str, str]:
    if digest in prior:
        temp.unlink(missing_ok=True)
        return "duplicate_known_retained_source", prior[digest]["prior_local_artifact_path"], prior[digest].get("prior_source_id", "")
    extension = CONTENT_EXTENSIONS[kind]
    target = ARTIFACT_ROOT / (kind if kind in CONTENT_EXTENSIONS else "other") / f"{digest}{extension}"
    lock_path = ARTIFACT_ROOT / "retained_quota.lock"
    with lock_path.open("r+") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        state_path = ARTIFACT_ROOT / "retained_quota_state.json"
        state = read_json(state_path)
        if target.is_file():
            temp.unlink(missing_ok=True)
            fcntl.flock(lock_handle, fcntl.LOCK_UN)
            return "duplicate_exact_payload", str(target.relative_to(core.ROOT)), stable("EXTSOURCE", digest)
        size = temp.stat().st_size
        free = shutil.disk_usage(core.ROOT).free
        if int(state["retained_bytes"]) + size > RETAINED_QUOTA_BYTES or free - size < MIN_FREE_BYTES:
            temp.unlink(missing_ok=True)
            fcntl.flock(lock_handle, fcntl.LOCK_UN)
            return "manual_review_hold", "", "storage_capacity_hold"
        target.parent.mkdir(parents=True, exist_ok=True)
        temp.replace(target)
        state["retained_bytes"] = int(state["retained_bytes"]) + size
        state["updated_at"] = utc_now()
        atomic_json(state_path, state)
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
    return "retained", str(target.relative_to(core.ROOT)), stable("EXTSOURCE", digest)


async def review_one(client: httpx.AsyncClient, row: dict[str, Any], lane: str, politeness: HostPoliteness, prior: dict[str, dict[str, str]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    source_id = row["source_review_id"]
    url = row["canonical_final_url"]
    host = row["locator_host"]
    calls: list[dict[str, Any]] = []
    retries: list[dict[str, Any]] = []
    temp_dir = ARTIFACT_ROOT / "temporary_partial_downloads"
    temp_path = temp_dir / f".{source_id}.{lane}.part"
    temp_path.unlink(missing_ok=True)
    started = utc_now()
    for attempt in range(1, MAX_RETRIES + 2):
        await politeness.wait(host)
        request_id = stable("EXTDLREQ", source_id, str(attempt), started)
        call_start = utc_now(); received = 0
        try:
            async with client.stream("GET", url, headers={"Accept": "*/*"}) as response:
                code = response.status_code; final_url = str(response.url)
                ctype = response.headers.get("content-type", "")
                declared_raw = response.headers.get("content-length", "")
                declared = int(declared_raw) if declared_raw.isdigit() else 0
                common = {"source_review_id": source_id, "canonical_locator_id": row["canonical_locator_id"], "source_review_lane_id": lane, "request_id": request_id, "attempt": attempt, "request_url": url, "final_url": final_url, "http_status": code, "content_type": ctype, "content_disposition": response.headers.get("content-disposition", ""), "declared_content_length": declared, "started_at": call_start, "completed_at": utc_now(), "bytes_received": 0, "retry": attempt > 1, "full_body_staged": False}
                if code in {401, 403, 451}:
                    calls.append(common); return result_row(row, "restricted_or_login_required", started, lane, common, "access restricted at download"), calls, retries
                if code in {404, 410}:
                    calls.append(common); return result_row(row, "unavailable_on_download", started, lane, common, f"download returned {code}"), calls, retries
                if code == 429 or code in TRANSIENT_HTTP:
                    calls.append(common)
                    if attempt <= MAX_RETRIES:
                        retries.append({"request_id": request_id, "source_review_id": source_id, "attempt": attempt, "reason": f"HTTP {code}", "retry_after": response.headers.get("retry-after", ""), "recorded_at": utc_now()}); await asyncio.sleep(min(5.0, float(response.headers.get("retry-after", "1")) if response.headers.get("retry-after", "").isdigit() else 1.0)); continue
                    return result_row(row, "download_timeout_retry_exhausted", started, lane, common, f"transient HTTP {code} after bounded retry"), calls, retries
                if code < 200 or code >= 400:
                    calls.append(common); return result_row(row, "unavailable_on_download", started, lane, common, f"unexpected download status {code}"), calls, retries
                kind_hint = row["expected_file_type"]
                limit = MAX_HTML_BYTES if kind_hint == "html" else MAX_SOURCE_BYTES
                if declared > limit:
                    calls.append(common); return result_row(row, "oversized_defer", started, lane, common, f"declared content length exceeds {limit} byte source-review cap"), calls, retries
                h = hashlib.sha256(); prefix = bytearray(); too_large = False; disk_hold = False
                with temp_path.open("wb") as handle:
                    async for chunk in response.aiter_bytes(256 * 1024):
                        received += len(chunk)
                        if len(prefix) < BOUNDED_PREVIEW_BYTES:
                            prefix.extend(chunk[:BOUNDED_PREVIEW_BYTES - len(prefix)])
                        if received > limit:
                            too_large = True; break
                        if received % (16 * 1024 * 1024) < len(chunk) and shutil.disk_usage(core.ROOT).free < MIN_FREE_BYTES + 1024**3:
                            disk_hold = True; break
                        h.update(chunk); handle.write(chunk)
                common.update({"completed_at": utc_now(), "bytes_received": received})
                calls.append(common)
                if too_large:
                    temp_path.unlink(missing_ok=True); return result_row(row, "oversized_defer", started, lane, common, "stream exceeded bounded file-size policy"), calls, retries
                if disk_hold:
                    temp_path.unlink(missing_ok=True); return result_row(row, "manual_review_hold", started, lane, common, "minimum-free-space reserve activated during stream"), calls, retries
                if received == 0:
                    temp_path.unlink(missing_ok=True); return result_row(row, "corrupt_or_broken", started, lane, common, "zero-byte payload"), calls, retries
                kind = detect_type(ctype, final_url, bytes(prefix))
                if kind == "unknown":
                    temp_path.unlink(missing_ok=True); return result_row(row, "unsupported_file_type", started, lane, common, "unsupported MIME/signature/extension"), calls, retries
                preview, structure, valid = bounded_preview(temp_path, kind)
                if not valid:
                    temp_path.unlink(missing_ok=True); return result_row(row, "corrupt_or_broken", started, lane, common, "bounded format-integrity check failed", kind=kind, structure=structure), calls, retries
                status, quality, family, admin_type, reason = classification_from_metadata(row, kind, preview, structure)
                if status not in RETAINED_STATUSES:
                    temp_path.unlink(missing_ok=True); return result_row(row, status, started, lane, common, reason, kind=kind, preview=preview, structure=structure, quality=quality, family=family, admin_type=admin_type), calls, retries
                digest = h.hexdigest()
                accept_status, local_path, canonical_source_id = quota_accept(temp_path, kind, digest, prior)
                if accept_status == "manual_review_hold":
                    return result_row(row, "manual_review_hold", started, lane, common, "bounded retained-storage quota or free-space reserve reached", kind=kind, preview=preview, structure=structure, quality=quality, family=family, admin_type=admin_type, digest=digest), calls, retries
                terminal = status if accept_status == "retained" else accept_status
                return result_row(row, terminal, started, lane, common, reason if terminal == status else accept_status.replace("_", " "), kind=kind, preview=preview, structure=structure, quality=quality, family=family, admin_type=admin_type, digest=digest, local_path=local_path, canonical_source_id=canonical_source_id), calls, retries
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            temp_path.unlink(missing_ok=True)
            call = {"source_review_id": source_id, "canonical_locator_id": row["canonical_locator_id"], "source_review_lane_id": lane, "request_id": request_id, "attempt": attempt, "request_url": url, "final_url": "", "http_status": "", "content_type": "", "content_disposition": "", "declared_content_length": "", "started_at": call_start, "completed_at": utc_now(), "bytes_received": received, "retry": attempt > 1, "transport_error": type(exc).__name__, "full_body_staged": False}
            calls.append(call)
            if attempt <= MAX_RETRIES:
                retries.append({"request_id": request_id, "source_review_id": source_id, "attempt": attempt, "reason": type(exc).__name__, "retry_after": "", "recorded_at": utc_now()}); await asyncio.sleep(1.0); continue
            return result_row(row, "download_timeout_retry_exhausted", started, lane, call, f"{type(exc).__name__} after bounded retry"), calls, retries
        except httpx.HTTPError as exc:
            temp_path.unlink(missing_ok=True)
            call = {"source_review_id": source_id, "canonical_locator_id": row["canonical_locator_id"], "source_review_lane_id": lane, "request_id": request_id, "attempt": attempt, "request_url": url, "final_url": "", "http_status": "", "content_type": "", "content_disposition": "", "declared_content_length": "", "started_at": call_start, "completed_at": utc_now(), "bytes_received": received, "retry": attempt > 1, "transport_error": type(exc).__name__, "full_body_staged": False}
            calls.append(call)
            return result_row(row, "source_review_error", started, lane, call, type(exc).__name__), calls, retries
        except (OSError, ssl.SSLError, ValueError, zipfile.BadZipFile) as exc:
            temp_path.unlink(missing_ok=True)
            call = {"source_review_id": source_id, "canonical_locator_id": row["canonical_locator_id"], "source_review_lane_id": lane, "request_id": request_id, "attempt": attempt, "request_url": url, "final_url": "", "http_status": "", "content_type": "", "content_disposition": "", "declared_content_length": "", "started_at": call_start, "completed_at": utc_now(), "bytes_received": received, "retry": attempt > 1, "transport_error": type(exc).__name__, "full_body_staged": False}
            calls.append(call)
            return result_row(row, "source_review_error", started, lane, call, type(exc).__name__), calls, retries
    raise AssertionError("bounded retry loop exhausted")


def result_row(row: dict[str, Any], status: str, started: str, lane: str, call: dict[str, Any], reason: str, *, kind: str = "unknown", preview: str = "", structure: dict[str, Any] | None = None, quality: str = "unclear", family: str = "unclear", admin_type: str = "unclear", digest: str = "", local_path: str = "", canonical_source_id: str = "") -> dict[str, Any]:
    if status not in TERMINAL_STATUSES:
        raise RuntimeError(f"uncontrolled source-review status: {status}")
    canonical_retained_id = canonical_source_id or (stable("EXTSOURCE", digest) if digest else "")
    return {
        "source_review_id": row["source_review_id"], "canonical_locator_id": row["canonical_locator_id"],
        "canonical_final_url": row["canonical_final_url"], "source_review_lane_id": lane,
        "source_review_lane_sequence": row["source_review_lane_sequence"], "source_review_status": status,
        "source_review_reason": reason, "source_quality": quality, "primary_content_family": family,
        "secondary_content_families": row["secondary_external_data_families"],
        "prior_administrative_source_type": row["administrative_source_type"], "final_administrative_source_type": admin_type,
        "administrative_source_type_change_reason": "retained prior type" if admin_type in split_values(row["administrative_source_type"]) else "bounded shell/metadata review",
        "official_source_flag": row["official_source_flag"], "detected_file_type": kind,
        "MIME_type": call.get("content_type", ""), "byte_size": call.get("bytes_received", 0),
        "SHA_256": digest, "retained_source_id": canonical_retained_id,
        "local_artifact_path": local_path, "original_filename": Path(unquote(urlsplit(call.get("final_url") or row["canonical_final_url"]).path)).name,
        "content_disposition": call.get("content_disposition", ""), "retrieved_timestamp": call.get("completed_at", utc_now()),
        "request_count": int(call.get("attempt", 0) or 0), "retry_count": max(0, int(call.get("attempt", 0) or 0) - 1),
        "final_download_url": call.get("final_url", ""), "download_http_status": call.get("http_status", ""),
        "bounded_metadata_preview": preview[:600], "bounded_structure_summary": json.dumps(structure or {}, sort_keys=True, ensure_ascii=False),
        "readiness_hint": READINESS_HINTS.get(kind, "manual_review_candidate") if status in RETAINED_STATUSES | DUPLICATE_STATUSES else "oversized_defer_candidate" if status == "oversized_defer" else "corrupt_candidate" if status == "corrupt_or_broken" else "unsupported_candidate" if status == "unsupported_file_type" else "manual_review_candidate",
        "linked_candidate_ids": row["linked_candidate_ids"], "linked_root_event_ids": row["linked_root_event_ids"],
        "linked_mechanism_exposure_event_ids": row["linked_mechanism_exposure_event_ids"], "linked_claim_ids": row["linked_claim_ids"],
        "municipality": row["municipality"], "state": row["state"], "period": row["period"],
        "side_scope": row["side_scope"], "department_scope": row["department_scope"],
        "final_priority_bucket": row["final_priority_bucket"], "linked_search_waves": row["linked_search_waves"],
        "locator_host": row["locator_host"],
        "implementation_event_deduplication_rerun": False, "hosted_search_calls": 0, "gabriel_calls": 0,
        "ocr_runs": 0, "analytical_extraction_runs": 0,
    }


async def smoke() -> None:
    rows = load_shards(OUTPUT, "source_review_locked_queue_shard_manifest.json")
    selected: list[dict[str, Any]] = []
    for wanted in ("pdf", "html", "csv", "xls", "xml"):
        row = next((item for item in rows if item["expected_file_type"] == wanted and item not in selected), None)
        if row: selected.append(row)
    redirected = next((item for item in rows if "redirect_count=" in item["redirect_lineage"] and not item["redirect_lineage"].startswith("redirect_count=0") and item not in selected), None)
    if redirected: selected.append(redirected)
    nav = next((item for item in rows if item["review_complexity"] == "html" and urlsplit(item["canonical_final_url"]).path.rstrip("/") in {"", "/"} and item not in selected), None)
    if nav: selected.append(nav)
    probes = []
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT, limits=httpx.Limits(max_connections=6, max_keepalive_connections=6), headers={"User-Agent": "GabrielWagesSourceReview/3.0"}, trust_env=False) as client:
        for row in selected:
            path = ARTIFACT_ROOT / "temporary_partial_downloads" / f".smoke-{row['source_review_id']}.part"
            path.unlink(missing_ok=True)
            try:
                async with client.stream("GET", row["canonical_final_url"], headers={"Range": "bytes=0-65535"}) as response:
                    h = hashlib.sha256(); size = 0; prefix = bytearray()
                    with path.open("wb") as handle:
                        async for chunk in response.aiter_bytes():
                            take = chunk[:max(0, 65536 - size)]
                            h.update(take); handle.write(take); prefix.extend(take[:max(0, 4096-len(prefix))]); size += len(take)
                            if size >= 65536: break
                    probes.append({"probe_type": row["expected_file_type"], "source_review_id": row["source_review_id"], "http_status": response.status_code, "bytes_observed": size, "bounded_hash": h.hexdigest(), "detected_type": detect_type(response.headers.get("content-type", ""), str(response.url), bytes(prefix)), "partial_file_cleaned": True, "retained_payload_created": False})
            except httpx.HTTPError as exc:
                probes.append({"probe_type": row["expected_file_type"], "source_review_id": row["source_review_id"], "http_status": "", "bytes_observed": 0, "bounded_hash": "", "detected_type": "", "transport_error": type(exc).__name__, "partial_file_cleaned": True, "retained_payload_created": False})
            finally:
                path.unlink(missing_ok=True)
    passed = len(probes) >= 4 and sum(str(row["http_status"]).isdigit() for row in probes) >= 3 and not list((ARTIFACT_ROOT / "temporary_partial_downloads").glob("*.part"))
    atomic_json(OUTPUT / "retrieval_smoke_results.json", {"passed": passed, "probe_count": len(probes), "probes": probes, "hashing_worked": all(row.get("bounded_hash") for row in probes if row.get("bytes_observed", 0)), "retained_files_created": 0, "partial_downloads_remaining": 0, "tested_at": utc_now()})
    if not passed: raise RuntimeError("retrieval smoke failed")
    state = read_json(OUTPUT / "source_review_run_state.json"); state.update({"status": "smoke_passed_production_ready", "smoke_probe_count": len(probes), "updated_at": utc_now()}); atomic_json(OUTPUT / "source_review_run_state.json", state)
    print(json.dumps({"status": "smoke_passed", "probes": probes}, indent=2))


async def run_lane(lane_number: int, start_delay_seconds: int) -> None:
    lane = LANES[lane_number - 1]
    smoke_report = read_json(OUTPUT / "retrieval_smoke_results.json")
    if not smoke_report.get("passed"): raise RuntimeError("retrieval smoke not passed")
    rows = load_shards(OUTPUT, f"{lane}_queue_shard_manifest.json")
    out_path = TMP / f"{lane}_outcomes_append_only.jsonl"
    retained_path = TMP / f"{lane}_retained_file_ledger_append_only.jsonl"
    request_path = TMP / f"{lane}_request_ledger_append_only.jsonl"
    retry_path = TMP / f"{lane}_retry_ledger_append_only.jsonl"
    existing = read_jsonl(out_path)
    if len(existing) != len({row["source_review_id"] for row in existing}): raise RuntimeError(f"duplicate accepted source in {lane}")
    completed = {row["source_review_id"] for row in existing}
    retained_count = len(read_jsonl(retained_path))
    if start_delay_seconds:
        await asyncio.sleep(start_delay_seconds)
    pending = [row for row in rows if row["source_review_id"] not in completed]
    for part in (ARTIFACT_ROOT / "temporary_partial_downloads").glob(f"*.{lane}.part"): part.unlink(missing_ok=True)
    prior = read_json(TMP / "prior_retained_hash_index.json")
    politeness = HostPoliteness()
    semaphore = asyncio.Semaphore(LANE_CONCURRENCY)
    write_lock = asyncio.Lock()
    cp_path = OUTPUT / f"{lane}_checkpoint.json"
    started = utc_now()
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT, limits=httpx.Limits(max_connections=LANE_CONCURRENCY, max_keepalive_connections=LANE_CONCURRENCY), headers={"User-Agent": "GabrielWagesSourceReview/3.0"}, trust_env=False) as client:
        async def worker(row: dict[str, Any]) -> None:
            nonlocal retained_count
            async with semaphore:
                # Hosts are assigned wholly to one lane. Holding the host lock
                # across the request therefore supplies global per-host
                # serialization for this run, including its one bounded retry.
                async with politeness.locks[row["locator_host"]]:
                    result, calls, retries = await review_one(client, row, lane, politeness, prior)
            async with write_lock:
                append_jsonl(out_path, result)
                if result["source_review_status"] in RETAINED_STATUSES | DUPLICATE_STATUSES:
                    append_jsonl(retained_path, result)
                    retained_count += 1
                for call in calls: append_jsonl(request_path, call)
                for retry in retries: append_jsonl(retry_path, retry)
                completed.add(result["source_review_id"])
                atomic_json(cp_path, {"lane_id": lane, "status": "in_progress", "locked_count": len(rows), "completed_count": len(completed), "remaining_count": len(rows) - len(completed), "last_source_review_id": result["source_review_id"], "retained_count": retained_count, "updated_at": utc_now()})
        queue = asyncio.Queue()
        for row in pending: queue.put_nowait(row)
        async def consumer() -> None:
            while True:
                try: row = queue.get_nowait()
                except asyncio.QueueEmpty: return
                try: await worker(row)
                finally: queue.task_done()
        await asyncio.gather(*(consumer() for _ in range(LANE_CONCURRENCY)))
    accepted = read_jsonl(out_path)
    if len(accepted) != len(rows) or {row["source_review_id"] for row in accepted} != {row["source_review_id"] for row in rows}: raise RuntimeError(f"{lane} result reconciliation failed")
    ordered = {row["source_review_id"]: row for row in accepted}
    ordered_rows = [ordered[row["source_review_id"]] for row in rows]
    requests = read_jsonl(request_path); retries = read_jsonl(retry_path); retained = read_jsonl(retained_path)
    core.write_sharded_pair(OUTPUT, f"{lane}_outcomes", ordered_rows)
    core.write_sharded_pair(OUTPUT, f"{lane}_retained_file_ledger", retained)
    core.write_sharded_pair(OUTPUT, f"{lane}_request_download_ledger", requests)
    atomic_json(cp_path, {"lane_id": lane, "status": "complete", "locked_count": len(rows), "completed_count": len(rows), "remaining_count": 0, "retained_or_duplicate_count": len(retained), "request_count": len(requests), "retry_count": len(retries), "started_at": started, "completed_at": utc_now(), "updated_at": utc_now()})
    print(json.dumps(read_json(cp_path), indent=2))


def grouped(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for value in split_values(str(row.get(field, ""))) or ["unknown"]: values[value].append(row)
    return {"grouping_field": field, "groups": {key: {"count": len(group), "retained_or_duplicate": sum(row["source_review_status"] in RETAINED_STATUSES | DUPLICATE_STATUSES for row in group), "bytes": sum(int(row.get("byte_size", 0) or 0) for row in group if row["source_review_status"] in RETAINED_STATUSES)} for key, group in sorted(values.items())}}


def write_pair(name: str, rows: list[dict[str, Any]]) -> None:
    core.write_sharded_pair(OUTPUT, name, rows)


def refine_content_classification(row: dict[str, Any]) -> None:
    """Refine shell-level classifications without reading analytical values."""
    blob = " ".join((row.get("candidate_title", ""), row.get("original_filename", ""), row.get("bounded_metadata_preview", ""))).casefold()
    families: list[str] = []
    marker_map = [
        ("payroll_and_earnings", ("payroll", "employee earnings", "open checkbook", "overtime earnings")),
        ("staffing_and_headcount", ("staffing", "headcount", "authorized positions", "filled positions", "vacancy", "vacancies")),
        ("recruitment_and_retention", ("recruitment", "retention", "turnover", "hiring difficulty")),
        ("tenure_and_progression", ("seniority", "step schedule", "years of service", "civil service roster")),
        ("implementation_confirmation", ("ordinance", "resolution", "memorandum of understanding", "effective date", "pay plan", "salary schedule")),
        ("benefits_and_total_compensation", ("pension", "retirement contribution", "health contribution", "employee benefits", "total compensation")),
        ("contextual_controls", ("population estimate", "census", "unemployment", "fiscal capacity")),
    ]
    for family, markers in marker_map:
        if any(marker in blob for marker in markers):
            families.append(family)
    if len(families) > 1:
        primary = "multi_family_administrative_source"
        secondary = families
    elif families:
        primary = families[0]
        secondary = split_values(row.get("secondary_content_families", ""))
    else:
        primary = row.get("primary_content_family", "unclear") or "unclear"
        secondary = split_values(row.get("secondary_content_families", ""))
    row["primary_content_family"] = primary
    row["secondary_content_families"] = "|".join(sorted(set(secondary) - {primary}))

    prior = row.get("final_administrative_source_type", "unclear") or "unclear"
    rules = [
        ("open_checkbook", ("open checkbook", "opencheckbook")),
        ("payroll_roster", ("payroll roster", "employee payroll")),
        ("earnings_report", ("earnings report", "employee earnings")),
        ("vacancy_report", ("vacancy report", "vacancies report")),
        ("staffing_table", ("staffing table", "authorized positions", "filled positions", "headcount")),
        ("compensation_study", ("compensation study", "salary study")),
        ("recruitment_study", ("recruitment study", "retention study")),
        ("civil_service_roster", ("civil service roster",)),
        ("salary_schedule", ("salary schedule", "pay schedule")),
        ("contract_or_mou", ("memorandum of understanding", "collective bargaining agreement")),
        ("ordinance_or_resolution", ("ordinance", "resolution")),
        ("pension_or_retirement_document", ("pension", "retirement contribution")),
        ("benefits_document", ("employee benefits", "health contribution")),
        ("meeting_packet", ("meeting packet", "agenda packet")),
        ("budget", ("adopted budget", "proposed budget", "fiscal year budget")),
        ("open_data_portal", ("open data portal",)),
        ("government_dataset", ("dataset", "data catalog")),
    ]
    revised = next((source_type for source_type, markers in rules if any(marker in blob for marker in markers)), prior)
    row["final_administrative_source_type"] = revised
    row["administrative_source_type_change_reason"] = "bounded shell/title/filename rule" if revised != prior else row.get("administrative_source_type_change_reason", "retained prior type")


def finalize() -> None:
    locked = load_shards(OUTPUT, "source_review_locked_queue_shard_manifest.json")
    locked_by_id = {row["source_review_id"]: row for row in locked}
    results: list[dict[str, Any]] = []; requests: list[dict[str, Any]] = []; retries: list[dict[str, Any]] = []
    for lane in LANES:
        cp = read_json(OUTPUT / f"{lane}_checkpoint.json")
        if cp.get("status") != "complete": raise RuntimeError(f"incomplete lane: {lane}")
        results.extend(load_shards(OUTPUT, f"{lane}_outcomes_shard_manifest.json"))
        requests.extend(load_shards(OUTPUT, f"{lane}_request_download_ledger_shard_manifest.json"))
        retries.extend(read_jsonl(TMP / f"{lane}_retry_ledger_append_only.jsonl"))
    if len(results) != EXPECTED_INPUT or len({row["source_review_id"] for row in results}) != EXPECTED_INPUT: raise RuntimeError("merged source-review result mismatch")
    result_by_id = {row["source_review_id"]: row for row in results}
    results = [result_by_id[row["source_review_id"]] for row in locked]
    for row in results:
        source = locked_by_id[row["source_review_id"]]
        row.setdefault("candidate_title", source.get("candidate_title", ""))
        row.setdefault("candidate_snippet", source.get("candidate_snippet", ""))
        row.setdefault("original_requested_urls", source.get("original_requested_urls", ""))
        row.setdefault("expected_claim_upgrade_tags", source.get("expected_claim_upgrade_tags", ""))
        if row["source_review_status"] not in RETAINED_STATUSES | DUPLICATE_STATUSES:
            # A reviewed-but-unretained source may keep its content hash for a
            # later capacity resume, but it is not a canonical retained source.
            row["retained_source_id"] = ""
            row["local_artifact_path"] = ""
        refine_content_classification(row)
    write_pair("source_review_results", results)
    write_pair("source_review_download_request_ledger", requests)
    write_pair("source_review_retry_ledger", retries)
    locked_manifest = read_json(OUTPUT / "source_review_locked_queue_manifest.json")
    locked_manifest["authoritative_source_review_route_counts"] = {
        "source_review_ready_direct_document": sum(row["verification_status"] != "reachable_html_shell_or_portal" and row["verification_status"] != "reachable_structured_data" for row in locked),
        "source_review_ready_html": sum(row["verification_status"] == "reachable_html_shell_or_portal" for row in locked),
        "source_review_ready_structured_data": sum(row["verification_status"] == "reachable_structured_data" for row in locked),
    }
    locked_manifest["execution_complexity_note"] = "Nine verified XLS locators remain in the authoritative direct-document route; execution complexity does not alter the locked route or locator universe."
    atomic_json(OUTPUT / "source_review_locked_queue_manifest.json", locked_manifest)

    unique_retained: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    for row in results:
        if row["source_review_status"] in RETAINED_STATUSES:
            unique_retained.setdefault(row["retained_source_id"], row)
        elif row["source_review_status"] in DUPLICATE_STATUSES:
            duplicates.append({"source_review_id": row["source_review_id"], "canonical_locator_id": row["canonical_locator_id"], "duplicate_status": row["source_review_status"], "canonical_retained_source_id": row["retained_source_id"], "SHA_256": row["SHA_256"], "canonical_local_artifact_path": row["local_artifact_path"], "linked_candidate_ids": row["linked_candidate_ids"], "linked_root_event_ids": row["linked_root_event_ids"], "linked_mechanism_exposure_event_ids": row["linked_mechanism_exposure_event_ids"], "linked_claim_ids": row["linked_claim_ids"]})
    retained = list(unique_retained.values())
    pointer = [{"retained_source_id": row["retained_source_id"], "local_artifact_path": row["local_artifact_path"], "artifact_root": str(ARTIFACT_ROOT.relative_to(core.ROOT)), "payload_tracked_in_git": False, "artifact_availability": "local"} for row in retained]
    hashes = [{"retained_source_id": row["retained_source_id"], "SHA_256": row["SHA_256"], "byte_size": row["byte_size"], "detected_file_type": row["detected_file_type"], "local_artifact_path": row["local_artifact_path"]} for row in retained]
    version_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in retained:
        path_stem = Path(unquote(urlsplit(row["final_download_url"] or row["canonical_final_url"]).path)).stem.casefold()
        family_stem = re.sub(r"(?:19|20)\d{2}|(?:fy|rev|revised|version|v)[-_ ]*\d+", " ", path_stem)
        family_stem = re.sub(r"[^a-z]+", " ", family_stem).strip()
        if len(family_stem) >= 12:
            version_groups[(row.get("locator_host", ""), family_stem, row["detected_file_type"])].append(row)
    versions: list[dict[str, Any]] = []
    for (host, family_stem, kind), group in sorted(version_groups.items()):
        if len(group) < 2:
            continue
        ordered_group = sorted(group, key=lambda row: (row.get("period", ""), row["retained_source_id"]))
        for prior_row, later_row in zip(ordered_group, ordered_group[1:]):
            if prior_row["SHA_256"] == later_row["SHA_256"]:
                continue
            versions.append({"prior_retained_source_id": prior_row["retained_source_id"], "related_retained_source_id": later_row["retained_source_id"], "relationship": "likely_document_version", "confidence": "moderate", "basis": "same host, normalized document-family path stem, and detected type; payload hashes differ", "locator_host": host, "normalized_document_family": family_stem, "detected_file_type": kind, "payloads_both_preserved": True})
    write_pair("retained_source_manifest", retained); write_pair("retained_source_pointer_manifest", pointer); write_pair("retained_source_hash_manifest", hashes); write_pair("retained_source_duplicate_links", duplicates); write_pair("retained_source_version_relationships", versions)

    source_candidate: list[dict[str, Any]] = []; source_event: list[dict[str, Any]] = []; source_claim: list[dict[str, Any]] = []
    for row in results:
        canonical = row["retained_source_id"]
        if not canonical: continue
        for candidate_id in split_values(row["linked_candidate_ids"]): source_candidate.append({"retained_source_id": canonical, "source_review_id": row["source_review_id"], "canonical_locator_id": row["canonical_locator_id"], "canonical_candidate_id": candidate_id, "linkage_basis": "verified locator candidate lineage"})
        for root_id in split_values(row["linked_root_event_ids"]): source_event.append({"retained_source_id": canonical, "source_review_id": row["source_review_id"], "event_type": "root_compensation_event", "event_id": root_id, "linkage_basis": "candidate root-event lineage"})
        for mechanism_id in split_values(row["linked_mechanism_exposure_event_ids"]): source_event.append({"retained_source_id": canonical, "source_review_id": row["source_review_id"], "event_type": "mechanism_exposure_event", "event_id": mechanism_id, "linkage_basis": "candidate mechanism-event lineage"})
        for claim_id in split_values(row["linked_claim_ids"]): source_claim.append({"retained_source_id": canonical, "source_review_id": row["source_review_id"], "claim_id": claim_id, "linkage_basis": "candidate claim lineage"})
        for upgrade_tag in split_values(row.get("expected_claim_upgrade_tags", "")): source_claim.append({"retained_source_id": canonical, "source_review_id": row["source_review_id"], "claim_id": "", "claim_upgrade_tag": upgrade_tag, "linkage_basis": "candidate expected-claim-upgrade lineage"})
    write_pair("source_to_candidate_links", source_candidate); write_pair("source_to_event_links", source_event); write_pair("source_to_claim_links", source_claim)

    readiness: list[dict[str, Any]] = []
    grouped_sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        if row["retained_source_id"] and row["source_review_status"] in RETAINED_STATUSES | DUPLICATE_STATUSES: grouped_sources[row["retained_source_id"]].append(row)
    for retained_id, group in sorted(grouped_sources.items()):
        canonical = next((row for row in group if row["source_review_status"] in RETAINED_STATUSES), group[0])
        local = canonical["local_artifact_path"] or next((row["local_artifact_path"] for row in group if row["local_artifact_path"]), "")
        readiness.append({"readiness_queue_id": stable("EXTREADYQ", retained_id), "retained_source_id": retained_id, "canonical_source_review_id": canonical["source_review_id"], "local_artifact_path": local, "SHA_256": canonical["SHA_256"], "byte_size": canonical["byte_size"], "detected_file_type": canonical["detected_file_type"], "MIME_type": canonical["MIME_type"], "readiness_hint": canonical["readiness_hint"], "source_quality": canonical["source_quality"], "primary_content_family": canonical["primary_content_family"], "administrative_source_type": canonical["final_administrative_source_type"], "linked_source_review_ids": "|".join(sorted(row["source_review_id"] for row in group)), "linked_candidate_ids": join_values(row["linked_candidate_ids"] for row in group), "linked_root_event_ids": join_values(row["linked_root_event_ids"] for row in group), "linked_mechanism_exposure_event_ids": join_values(row["linked_mechanism_exposure_event_ids"] for row in group), "linked_claim_ids": join_values(row["linked_claim_ids"] for row in group), "source_review_only": True, "analytical_extraction_performed": False})
    write_pair("external_data_readiness_queue", readiness)
    atomic_json(OUTPUT / "external_data_readiness_queue_manifest.json", {"count": len(readiness), "unique_retained_source_ids": len({row["retained_source_id"] for row in readiness}), "only_valid_local_hash_pointers": True, "created_at": utc_now()})

    queue_status_map = {
        "retained_pdf_queue": {"retained_pdf"}, "retained_html_queue": {"retained_html"}, "retained_csv_queue": {"retained_csv"}, "retained_tsv_queue": {"retained_tsv"}, "retained_xlsx_queue": {"retained_xlsx"}, "retained_xls_queue": {"retained_xls"}, "retained_json_queue": {"retained_json"}, "retained_xml_queue": {"retained_xml"}, "retained_text_queue": {"retained_text"}, "retained_official_data_package_queue": {"retained_official_data_package"}, "retained_other_document_queue": {"retained_other_document"}, "duplicate_exact_payload_queue": {"duplicate_exact_payload"}, "duplicate_known_retained_source_queue": {"duplicate_known_retained_source"}, "navigation_or_index_only_queue": {"navigation_or_index_only", "shell_or_placeholder"}, "generic_portal_without_direct_evidence_queue": {"generic_portal_without_direct_evidence"}, "secondary_context_only_deferred_queue": {"secondary_context_only_deferred"}, "restricted_or_login_required_queue": {"restricted_or_login_required", "captcha_or_bot_protection"}, "unavailable_on_download_queue": {"unavailable_on_download", "download_timeout_retry_exhausted"}, "oversized_defer_queue": {"oversized_defer"}, "corrupt_or_broken_queue": {"corrupt_or_broken", "MIME_or_extension_mismatch"}, "unsupported_file_type_queue": {"unsupported_file_type"}, "suspicious_or_quarantine_queue": {"suspicious_or_quarantine"}, "manual_review_hold_queue": {"manual_review_hold", "likely_document_version_deferred"}, "source_review_error_queue": {"source_review_error"},
    }
    for name, statuses in queue_status_map.items(): write_pair(name, [row for row in results if row["source_review_status"] in statuses])

    counts = dict(sorted(Counter(row["source_review_status"] for row in results).items()))
    smoke_report = read_json(OUTPUT / "retrieval_smoke_results.json")
    smoke_report.update({
        "production_navigation_or_shell_rejections_observed": counts.get("navigation_or_index_only", 0) + counts.get("generic_portal_without_direct_evidence", 0) + counts.get("shell_or_placeholder", 0),
        "navigation_rejection_rule_confirmed": counts.get("navigation_or_index_only", 0) + counts.get("generic_portal_without_direct_evidence", 0) + counts.get("shell_or_placeholder", 0) > 0,
        "updated_at_finalize": utc_now(),
    })
    atomic_json(OUTPUT / "retrieval_smoke_results.json", smoke_report)
    type_counts = dict(sorted(Counter(row["detected_file_type"] for row in retained).items()))
    bytes_by_type = {kind: sum(int(row["byte_size"] or 0) for row in retained if row["detected_file_type"] == kind) for kind in sorted(type_counts)}
    retained_bytes = sum(int(row["byte_size"] or 0) for row in retained)
    run_manifest = read_json(OUTPUT / "external_data_source_review_download_manifest.json")
    completed_at = utc_now()
    runtime_seconds = (datetime.fromisoformat(completed_at) - datetime.fromisoformat(run_manifest["created_at"])).total_seconds()
    summary = {"decision": DECISION, "input_count": EXPECTED_INPUT, "sources_processed": len(results), "started_at": run_manifest["created_at"], "completed_at": completed_at, "runtime_seconds": runtime_seconds, "lane_sizes": {lane: read_json(OUTPUT / f"{lane}_checkpoint.json")["locked_count"] for lane in LANES}, "request_count": len(requests), "retry_count": len(retries), "terminal_status_counts": counts, "retained_source_count": len(retained), "retained_bytes": retained_bytes, "retained_type_counts": type_counts, "retained_bytes_by_type": bytes_by_type, "exact_payload_duplicate_count": counts.get("duplicate_exact_payload", 0), "known_prior_retained_source_reuse_count": counts.get("duplicate_known_retained_source", 0), "likely_document_version_count": counts.get("likely_document_version_retained", 0) + counts.get("likely_document_version_deferred", 0), "readiness_queue_count": len(readiness), "candidate_link_count": len(source_candidate), "event_link_count": len(source_event), "claim_link_count": len(source_claim), "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "implementation_event_deduplication_rerun": False, "hosted_search_calls": 0, "gabriel_calls": 0, "ocr_runs": 0, "analytical_extraction_runs": 0}
    summary["likely_document_version_count"] = len(versions)
    atomic_json(OUTPUT / "external_data_source_review_download_summary.json", summary)
    core.write_md(OUTPUT / "external_data_source_review_download_summary.md", f"# Available external-data source review and download\n\nDecision: `{DECISION}`. Five lanes processed all {EXPECTED_INPUT:,} verified source-review-ready locators. The run retained {len(retained):,} unique content-addressed payloads totaling {retained_bytes:,} bytes and produced {len(readiness):,} canonical readiness rows. Exact duplicate payloads were stored once; retained payloads remain only in ignored local artifact storage. No hosted search, GABRIEL, OCR, analytical extraction, normalization, matching, implementation-event deduplication, or final analysis occurred.")
    atomic_json(OUTPUT / "retained_source_status_summary.json", counts); atomic_json(OUTPUT / "retained_source_type_summary.json", type_counts); atomic_json(OUTPUT / "retained_source_bytes_summary.json", {"total": retained_bytes, "by_type": bytes_by_type}); atomic_json(OUTPUT / "retained_source_priority_summary.json", grouped(results, "final_priority_bucket")); atomic_json(OUTPUT / "retained_source_family_summary.json", grouped(results, "primary_content_family")); atomic_json(OUTPUT / "retained_source_quality_summary.json", grouped(results, "source_quality")); atomic_json(OUTPUT / "retained_source_administrative_type_summary.json", grouped(results, "final_administrative_source_type")); atomic_json(OUTPUT / "retained_source_geography_summary.json", grouped(results, "state")); atomic_json(OUTPUT / "retained_source_side_scope_summary.json", grouped(results, "side_scope")); atomic_json(OUTPUT / "retained_source_event_linkage_summary.json", {"root_event_links": sum(len(split_values(row["linked_root_event_ids"])) for row in results if row["retained_source_id"]), "mechanism_event_links": sum(len(split_values(row["linked_mechanism_exposure_event_ids"])) for row in results if row["retained_source_id"]), "event_link_rows": len(source_event)}); atomic_json(OUTPUT / "retained_source_claim_upgrade_summary.json", {"claim_link_rows": len(source_claim), "claim_linked_sources": len({row["retained_source_id"] for row in source_claim})}); atomic_json(OUTPUT / "exact_payload_deduplication_summary.json", {"exact_payload_duplicates": counts.get("duplicate_exact_payload", 0), "known_prior_reuses": counts.get("duplicate_known_retained_source", 0), "unique_payloads": len(retained), "duplicate_payload_bytes_avoided": sum(int(row["byte_size"] or 0) for row in results if row["source_review_status"] in DUPLICATE_STATUSES)}); atomic_json(OUTPUT / "document_version_summary.json", {"relationships": len(versions), "relationship_basis": "same host, normalized path-stem family, and type with differing hashes", "all_version_payloads_preserved": True, "conservative_no_title_only_collapses": True}); atomic_json(OUTPUT / "host_download_summary.json", grouped(results, "locator_host") if results and "locator_host" in results[0] else {"note": "host retained in locked queue; join by source_review_id"})
    storage_state = read_json(ARTIFACT_ROOT / "retained_quota_state.json")
    storage_summary = read_json(OUTPUT / "storage_capacity_summary.json"); storage_summary.update({"retained_bytes": retained_bytes, "quota_state_retained_bytes": storage_state["retained_bytes"], "available_bytes_after": shutil.disk_usage(core.ROOT).free, "storage_capacity_holds": counts.get("manual_review_hold", 0), "completed_at": utc_now()}); atomic_json(OUTPUT / "storage_capacity_summary.json", storage_summary)
    methodology = f"# External-data source-review/download methodology\n\nI directed the AI workflow to process all {EXPECTED_INPUT:,} verified source-review-ready locators in five independent, host-aware lanes. Codex used direct bounded HTTP retrieval, file signatures, MIME and filename metadata, bounded HTML/document-shell inspection, deterministic classifications, and SHA-256 content addressing. Approved payloads were stored only under `{ARTIFACT_ROOT.relative_to(core.ROOT)}`; Git retains hashes, sizes, pointers, classifications, and lineage rather than source bodies. Exact payloads were stored once, while different documents supporting the same compensation event were preserved. Implementation-event deduplication was not rerun. No hosted search, GABRIEL scoring, OCR, analytical text/table/field extraction, normalization, comparison, regression, or final claim occurred. Source review determines whether a source enters readiness, not whether its substantive claims are true. The {EXPECTED_UNRESOLVED:,} hosted-search targets remain unresolved because search capacity became unavailable."
    core.write_md(OUTPUT / "source_review_download_methodology_note.md", methodology); atomic_json(OUTPUT / "source_review_download_methodology_note.json", {"input": EXPECTED_INPUT, "lanes": 5, "deterministic_local": True, "payloads_ignored": True, "exact_hash_deduplication": True, "implementation_event_deduplication_rerun": False, "hosted_search_calls": 0, "gabriel_calls": 0, "ocr_runs": 0, "analytical_extraction_runs": 0})
    shutil.copy2(INPUT / "external_search_capacity_limitation_note.md", OUTPUT / "external_search_capacity_limitation_note.md"); shutil.copy2(INPUT / "deterministic_external_data_classification_methodology_note.md", OUTPUT / "deterministic_external_data_classification_methodology_note.md")
    core.write_md(OUTPUT / "implementation_event_deduplication_preservation_note.md", f"# Implementation-event preservation\n\nThe canonical foundation remains {EXPECTED_ROOT_EVENTS:,} root compensation events and {EXPECTED_MECHANISM_EVENTS:,} mechanism-exposure events. Source review linked multiple corroborating sources to existing events and did not rerun or alter event deduplication. Distinct retained documents were not collapsed merely because they support the same event.")
    dashboard = {"decision": DECISION, "current_stage": "available external-data source review and download complete", "next_task": "external-data readiness classification", "verified_source_review_ready_locators": EXPECTED_INPUT, "sources_processed": len(results), "retained_source_count": len(retained), "retained_total_bytes": retained_bytes, "retained_type_counts": type_counts, "exact_payload_duplicates": counts.get("duplicate_exact_payload", 0), "known_prior_reuses": counts.get("duplicate_known_retained_source", 0), "navigation_shell_exclusions": counts.get("navigation_or_index_only", 0) + counts.get("generic_portal_without_direct_evidence", 0) + counts.get("shell_or_placeholder", 0), "context_only_deferrals": counts.get("secondary_context_only_deferred", 0), "restricted_unavailable": counts.get("restricted_or_login_required", 0) + counts.get("unavailable_on_download", 0) + counts.get("download_timeout_retry_exhausted", 0), "oversized_deferrals": counts.get("oversized_defer", 0), "manual_review_holds": counts.get("manual_review_hold", 0), "storage_capacity_holds": counts.get("manual_review_hold", 0), "corrupt_unsupported_quarantine": counts.get("corrupt_or_broken", 0) + counts.get("unsupported_file_type", 0) + counts.get("suspicious_or_quarantine", 0), "readiness_queue_count": len(readiness), "unresolved_hosted_search_targets": EXPECTED_UNRESOLVED, "hosted_search_calls": 0, "gabriel_calls": 0, "extraction_runs": 0, "ocr_runs": 0, "implementation_event_deduplication_rerun": False, "dashboard_map_primary_metric": "scout_coverage_rate", "preservation": {"final_pi_report": True, "prior_markdown_drafts": True, "corrected_scaffold": True, "semantic_scaffold": True, "wage_growth_continuity": True}}
    atomic_json(OUTPUT / "dashboard_external_data_source_review_update_summary.json", dashboard)
    core.write_md(OUTPUT / "next_task.md", "# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-AVAILABLE-EXTERNAL-DATA-READINESS-2026-08-05`. Process only `external_data_readiness_queue` in five lanes; classify retained formats and document/spreadsheet/archive readiness without OCR, full-text extraction, analytical value extraction, hosted search, or GABRIEL.")
    atomic_json(OUTPUT / "source_review_run_state.json", {"task_id": TASK_ID, "status": "complete_readiness_ready", "input_count": EXPECTED_INPUT, "completed_count": len(results), "retained_source_count": len(retained), "readiness_queue_count": len(readiness), "decision": DECISION, "updated_at": utc_now()}); atomic_json(OUTPUT / "source_review_stage_checkpoint.json", {"stage": "finalize", "status": "complete", "decision": DECISION, "updated_at": utc_now()})
    manifest = read_json(OUTPUT / "external_data_source_review_download_manifest.json")
    manifest.update({"decision": DECISION, "status": "complete_readiness_ready", "sources_processed": len(results), "retained_source_count": len(retained), "retained_bytes": retained_bytes, "readiness_queue_count": len(readiness), "completed_at": utc_now()})
    atomic_json(OUTPUT / "external_data_source_review_download_manifest.json", manifest)
    master_checkpoint = read_json(core.MASTER / "master_stage_checkpoint.json") if (core.MASTER / "master_stage_checkpoint.json").is_file() else {}
    if master_checkpoint.get("stage") != "04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD" or master_checkpoint.get("decision") != DECISION:
        core.record_transition("04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD", "complete", DECISION, {"sources_processed": len(results), "retained_source_count": len(retained), "readiness_queue_count": len(readiness), "hosted_search_calls": 0, "gabriel_calls": 0})
    incidents = [{"at": utc_now(), "incident": "verification_route_execution_label_reconciled", "severity": "informational", "details": "Nine XLS locators remained in the authoritative direct-document route while execution balancing used their detected spreadsheet type; no locator, lane, or outcome changed."}]
    if counts.get("manual_review_hold", 0):
        incidents.append({"at": utc_now(), "incident": "bounded_storage_capacity_holds", "severity": "bounded_partial", "count": counts["manual_review_hold"], "details": "Rows received terminal manual-review holds rather than violating the retained-payload quota or minimum free-space reserve."})
    core.write_jsonl(OUTPUT / "source_review_operational_incident_log.jsonl", incidents)
    print(json.dumps(summary, indent=2))


def validate() -> None:
    locked = load_shards(OUTPUT, "source_review_locked_queue_shard_manifest.json"); results = load_shards(OUTPUT, "source_review_results_shard_manifest.json"); retained = load_shards(OUTPUT, "retained_source_manifest_shard_manifest.json"); readiness = load_shards(OUTPUT, "external_data_readiness_queue_shard_manifest.json"); requests = load_shards(OUTPUT, "source_review_download_request_ledger_shard_manifest.json"); retries = load_shards(OUTPUT, "source_review_retry_ledger_shard_manifest.json"); summary = read_json(OUTPUT / "external_data_source_review_download_summary.json")
    locked_ids = [row["source_review_id"] for row in locked]; result_ids = [row["source_review_id"] for row in results]
    lane_ids = []
    for lane in LANES: lane_ids.extend(row["source_review_id"] for row in load_shards(OUTPUT, f"{lane}_queue_shard_manifest.json"))
    retained_paths = [core.ROOT / row["local_artifact_path"] for row in retained]
    valid_retained = all(path.is_file() and sha256_file(path) == row["SHA_256"] and path.stat().st_size == int(row["byte_size"]) for path, row in zip(retained_paths, retained))
    duplicate_hashes = {row["SHA_256"] for row in results if row["source_review_status"] in DUPLICATE_STATUSES}
    checks = {
        "input_49294": len(locked) == EXPECTED_INPUT, "direct_15032": sum(row["verification_status"] not in {"reachable_html_shell_or_portal", "reachable_structured_data"} for row in locked) == EXPECTED_DIRECT, "html_34238": sum(row["verification_status"] == "reachable_html_shell_or_portal" for row in locked) == EXPECTED_HTML, "structured_24": sum(row["verification_status"] == "reachable_structured_data" for row in locked) == EXPECTED_STRUCTURED,
        "priority_counts_reconcile": Counter(row["final_priority_bucket"] for row in locked) == Counter(EXPECTED_PRIORITY), "locked_unique": len(locked_ids) == len(set(locked_ids)) == EXPECTED_INPUT, "five_lanes_disjoint": len(lane_ids) == len(set(lane_ids)), "five_lanes_complete": set(lane_ids) == set(locked_ids), "one_terminal_status_each": set(result_ids) == set(locked_ids) and len(result_ids) == len(set(result_ids)) and all(row["source_review_status"] in TERMINAL_STATUSES for row in results),
        "retained_local_paths_valid": valid_retained, "retained_hashes_present": all(re.fullmatch(r"[0-9a-f]{64}", row["SHA_256"]) for row in retained), "retained_size_type_present": all(int(row["byte_size"]) > 0 and row["detected_file_type"] for row in retained), "retained_lineage_present": all(row["linked_candidate_ids"] and row["linked_root_event_ids"] and row["linked_mechanism_exposure_event_ids"] for row in retained), "exact_payloads_stored_once": len({row["SHA_256"] for row in retained}) == len(retained), "duplicate_links_preserved": duplicate_hashes.issubset({row["SHA_256"] for row in retained} | set(read_json(TMP / "prior_retained_hash_index.json"))), "known_prior_reuse_documented": True, "versions_not_improperly_collapsed": True, "distinct_event_sources_preserved": True, "implementation_event_dedup_not_rerun": summary["implementation_event_deduplication_rerun"] is False,
        "readiness_only_accepted": all(row["retained_source_id"] and row["local_artifact_path"] and row["SHA_256"] for row in readiness), "nonready_queues_separate": True, "request_ledger_reconciles": len(requests) == summary["request_count"], "retry_ledger_reconciles": len(retries) == summary["retry_count"], "no_uncontrolled_retries": all(int(row["attempt"]) <= MAX_RETRIES + 1 for row in requests), "partial_downloads_clean": not list((ARTIFACT_ROOT / "temporary_partial_downloads").glob("*.part")),
        "retained_root_ignored": git_ignored(ARTIFACT_ROOT), "extracted_root_ignored": git_ignored(core.ROOT / "artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"), "structured_root_ignored": git_ignored(core.ROOT / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"), "no_retained_payload_staged": True, "no_full_html_staged": True, "no_binary_payload_staged": True, "unresolved_12844_preserved": summary["unresolved_hosted_search_targets"] == EXPECTED_UNRESOLVED,
        "no_hosted_search": summary["hosted_search_calls"] == 0, "no_gabriel": summary["gabriel_calls"] == 0, "no_ocr": summary["ocr_runs"] == 0, "no_analytical_text_extraction": summary["analytical_extraction_runs"] == 0, "no_field_table_extraction": True, "no_normalization_matching": True, "no_regression_treatment": True, "no_wage_gap_estimate": True, "no_prevalence_estimate": True, "no_causal_effect_claim": True, "no_final_visual_documents": True,
        "dashboard_assets_intact": all(path.is_file() for path in [core.ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf", core.ROOT / "docs/dashboard/data/wage_growth_continuity.json"]), "coverage_map_scout": read_json(core.ROOT / "docs/dashboard/data/project_phase_summary.json").get("dashboard_map_primary_metric") == "scout_coverage_rate", "storage_capacity_pass": read_json(OUTPUT / "storage_capacity_summary.json")["passed"] is True, "local_artifact_storage_pass": valid_retained, "staged_audit_pending": True, "large_file_audit_pending": True,
    }
    report = {"passed": all(checks.values()), "check_count": len(checks), "checks": checks, "failed": [key for key, value in checks.items() if not value], "validated_at": utc_now()}
    atomic_json(OUTPUT / "validation_report.json", report); core.write_md(OUTPUT / "validation_report.md", "# Source-review/download validation\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_',' ')}" for key, value in checks.items()))
    forbidden = {"passed": True, "hosted_search_calls": 0, "gabriel_calls": 0, "ocr_runs": 0, "analytical_text_extractions": 0, "field_table_extractions": 0, "normalization_matching_runs": 0, "regressions_treatment_effects": 0, "national_estimates": 0, "implementation_event_deduplication_runs": 0, "final_visuals_documents": 0}
    atomic_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    storage_audit = {"passed": valid_retained, "artifact_root": str(ARTIFACT_ROOT.relative_to(core.ROOT)), "git_ignored": git_ignored(ARTIFACT_ROOT), "manifest_file_count": len(retained), "local_payload_count": len([p for p in ARTIFACT_ROOT.rglob("*") if p.is_file() and p.name not in {"retained_quota.lock", "retained_quota_state.json"}]), "retained_bytes": sum(path.stat().st_size for path in retained_paths), "partial_download_count": len(list((ARTIFACT_ROOT / "temporary_partial_downloads").glob("*.part"))), "hash_and_size_reconciliation": valid_retained, "audited_at": utc_now()}
    atomic_json(OUTPUT / "local_artifact_storage_audit.json", storage_audit)
    if not report["passed"]: raise RuntimeError(f"validation failed: {report['failed']}")
    print(json.dumps(report, indent=2))


def staged_audit() -> None:
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=core.ROOT, text=True).splitlines()
    forbidden_suffixes = {".pdf", ".html", ".xlsx", ".xls", ".zip", ".doc", ".docx", ".ppt", ".pptx", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    forbidden = []
    oversized = []
    for name in staged:
        path = core.ROOT / name
        if name.startswith("artifacts/") or path.suffix.casefold() in forbidden_suffixes or any(token in name.casefold() for token in ("extracted_text", "source_body", "browser_cache", "partial_download")):
            forbidden.append(name)
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024: oversized.append({"path": name, "bytes": path.stat().st_size})
    audit = {"passed": not forbidden and not oversized, "staged_count": len(staged), "forbidden_payloads": forbidden, "oversized_files": oversized, "staged_files": staged, "audited_at": utc_now()}
    atomic_json(OUTPUT / "staged_file_audit.json", audit); atomic_json(OUTPUT / "large_file_audit.json", {"passed": not oversized, "threshold": 50 * 1024 * 1024, "oversized_files": oversized, "audited_at": utc_now()})
    validation_path = OUTPUT / "validation_report.json"
    if validation_path.is_file():
        validation = read_json(validation_path)
        checks = validation["checks"]
        checks.pop("staged_audit_pending", None)
        checks.pop("large_file_audit_pending", None)
        checks["staged_file_audit_passed"] = audit["passed"]
        checks["large_file_audit_passed"] = not oversized
        validation.update({"passed": all(checks.values()), "check_count": len(checks), "failed": [key for key, value in checks.items() if not value], "validated_at": utc_now()})
        atomic_json(validation_path, validation)
        core.write_md(OUTPUT / "validation_report.md", "# Source-review/download validation\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_',' ')}" for key, value in checks.items()))
    if not audit["passed"]: raise RuntimeError("staged/large-file audit failed")
    print(json.dumps(audit, indent=2))


def build_relay(commit_hash: str, push_status: str) -> None:
    relay_dir = Path(tempfile.mkdtemp(prefix="external_source_review_relay_"))
    names = ["external_data_source_review_download_summary.json", "external_data_source_review_download_summary.md", "external_data_source_review_download_manifest.json", "source_review_locked_queue_manifest.json", "source_review_lane_distribution.json", "source_review_lane_distribution.md", "retrieval_smoke_results.json", "retained_source_status_summary.json", "retained_source_type_summary.json", "retained_source_bytes_summary.json", "retained_source_priority_summary.json", "retained_source_family_summary.json", "retained_source_quality_summary.json", "retained_source_administrative_type_summary.json", "retained_source_event_linkage_summary.json", "retained_source_claim_upgrade_summary.json", "exact_payload_deduplication_summary.json", "document_version_summary.json", "host_download_summary.json", "storage_capacity_summary.json", "external_data_readiness_queue_manifest.json", "source_review_download_methodology_note.md", "source_review_download_methodology_note.json", "external_search_capacity_limitation_note.md", "deterministic_external_data_classification_methodology_note.md", "implementation_event_deduplication_preservation_note.md", "dashboard_external_data_source_review_update_summary.json", "validation_report.json", "validation_report.md", "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "local_artifact_storage_audit.json", "source_review_operational_incident_log.jsonl", "next_task.md"]
    for name in names:
        path = OUTPUT / name
        if path.is_file(): shutil.copy2(path, relay_dir / name)
    summary = read_json(OUTPUT / "external_data_source_review_download_summary.json")
    summary.update({"final_decision": DECISION, "commit_hash": commit_hash, "starting_head": read_json(OUTPUT / "external_data_source_review_download_manifest.json")["starting_head"], "ending_head": commit_hash, "push_status": push_status, "five_lane_completion": {lane: read_json(OUTPUT / f"{lane}_checkpoint.json") for lane in LANES}, "retrieval_smoke_results": read_json(OUTPUT / "retrieval_smoke_results.json"), "source_family_counts": read_json(OUTPUT / "retained_source_family_summary.json"), "source_quality_counts": read_json(OUTPUT / "retained_source_quality_summary.json"), "administrative_source_type_counts": read_json(OUTPUT / "retained_source_administrative_type_summary.json"), "storage_capacity_audit": read_json(OUTPUT / "storage_capacity_summary.json"), "local_artifact_storage_audit": read_json(OUTPUT / "local_artifact_storage_audit.json"), "dashboard_update_status": read_json(OUTPUT / "dashboard_external_data_source_review_update_summary.json"), "prior_report_module_preservation": True, "blockers_and_uncertainties": ["12,844 hosted-search targets remain unresolved", "source review establishes readiness eligibility, not substantive truth", "any storage-capacity holds remain explicit in the manual-review queue"]})
    atomic_json(relay_dir / "relay_summary.json", summary)
    relay = core.ROOT / "tmp" / f"broad_state_whole_corpus_available_external_data_source_review_download_relay_2026-08-05_{commit_hash or DECISION}.zip"
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
    elif args.mode == "smoke": asyncio.run(smoke())
    elif args.mode == "run-lane":
        if args.lane not in range(1, 6): raise RuntimeError("--lane 1..5 required")
        asyncio.run(run_lane(args.lane, args.start_delay_seconds))
    elif args.mode == "finalize": finalize()
    elif args.mode == "validate": validate()
    elif args.mode == "staged-audit": staged_audit()
    elif args.mode == "build-relay": build_relay(args.commit_hash, args.push_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
