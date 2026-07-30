#!/usr/bin/env python3
"""Run the bounded 4x2500 broad-state candidate verification wave.

The live portion performs HTTP HEAD metadata checks only. It never reads or
retains response bodies, downloads documents, or performs source review,
extraction, OCR, rating, ingestion, codification, or statistical analysis.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-4X2500-CANDIDATE-REVIEW-2026-07-30"
OUTPUT = BASE / "BROAD-STATE-4X2500-VERIFICATION-2026-07-30"
TASK_ID = "BROAD-STATE-4X2500-VERIFICATION-2026-07-30"
EXPECTED_HEAD = "83752800124c7f5fcb83f1d2324a75451dcf3807"
QUEUE_ROWS = 5768
LANES = tuple(f"verification_lane_{i:03d}" for i in range(1, 5))
STAGGER_MINUTES = {lane: i * 8 for i, lane in enumerate(LANES)}
PRIORITIES = (
    "high_priority_verification_ready",
    "medium_priority_verification_ready",
    "low_priority_verification_ready",
)
EXPECTED_PRIORITY = dict(zip(PRIORITIES, (4281, 1352, 135)))
LANE_TARGETS = {
    LANES[0]: dict(zip(PRIORITIES, (1071, 338, 33))),
    LANES[1]: dict(zip(PRIORITIES, (1070, 338, 34))),
    LANES[2]: dict(zip(PRIORITIES, (1070, 338, 34))),
    LANES[3]: dict(zip(PRIORITIES, (1070, 338, 34))),
}
CONCURRENCY = 8
TIMEOUT_SECONDS = 8.0
MAX_RETRIES = 1
MAX_REDIRECTS = 5
MIN_BATCH_INTERVAL_SECONDS = 6.25
READY_STATUSES = {"reachable", "reachable_with_redirect"}
TERMINAL_STATUSES = {
    "reachable", "reachable_with_redirect", "unavailable", "blocked_or_forbidden",
    "timeout", "malformed_locator", "duplicate_final_locator", "verification_error",
}
VERIFY_FIELDS = (
    "verification_row_id", "verification_lane_id", "verification_lane_sequence",
    "candidate_id", "scout_candidate_id", "scout_target_id", "lane_id", "shard_id",
    "worker_id", "state", "region", "municipality", "county", "unit_type_hint",
    "occupation_group_hint", "possible_bargaining_unit", "possible_cycle_or_year",
    "source_title", "source_locator_or_url", "source_domain", "normalized_locator",
    "canonical_review_locator", "canonical_locator_before_verification",
    "source_family_hint", "document_type_hint", "source_family_confidence",
    "possible_mechanism_hints", "sanitized_snippet", "search_query_family",
    "broad_geographic_target_reason", "source_family_diversification_reason",
    "matched_safety_non_safety_opportunity_flag", "candidate_quality_tier",
    "discovery_run_id", "lane_completed_at", "review_score", "review_score_reasons",
    "primary_bucket", "priority_bucket", "prior_duplicate_source", "cba_non_cba_hint",
    "review_method", "verification_status", "http_status_code", "final_url_or_locator",
    "final_canonical_locator", "redirect_count", "content_type", "content_length_header",
    "verification_method", "verification_attempt_count", "verification_started_at",
    "verification_completed_at", "error_class", "error_message_redacted",
    "pre_duplicate_verification_status", "checkpoint_id", "download_status",
    "source_review_status", "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "notes",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] = VERIFY_FIELDS) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str] = VERIFY_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if new:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
        handle.flush()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_locator(value: str) -> str:
    try:
        parts = urlsplit((value or "").strip())
    except ValueError:
        return ""
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return ""
    host = parts.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", parts.path).rstrip("/")
    return urlunsplit((parts.scheme.casefold(), host, path, "", ""))


def source_domain(value: str) -> str:
    try:
        return urlsplit(value).netloc.casefold().removeprefix("www.")
    except ValueError:
        return ""


def current_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def stable_priority_rows(rows: list[dict[str, str]], priority: str) -> list[dict[str, str]]:
    return sorted(
        (row for row in rows if row["priority_bucket"] == priority),
        key=lambda row: (
            row.get("state", ""), row.get("region", ""), row.get("source_family_hint", ""),
            row.get("source_domain", ""), row.get("municipality", ""), row.get("candidate_id", ""),
        ),
    )


def interleave(groups: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    """Stable proportional merge; minimizes long runs without reordering a class."""
    used = Counter()
    totals = {priority: len(groups[priority]) for priority in PRIORITIES}
    output: list[dict[str, str]] = []
    while len(output) < sum(totals.values()):
        available = [priority for priority in PRIORITIES if used[priority] < totals[priority]]
        priority = min(
            available,
            key=lambda item: ((used[item] + 1) / totals[item], PRIORITIES.index(item)),
        )
        output.append(groups[priority][used[priority]])
        used[priority] += 1
    return output


def prepare() -> None:
    if OUTPUT.exists():
        raise RuntimeError(f"output already exists: {OUTPUT}")
    head = current_head()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected preflight HEAD: {head}")
    queue_path = INPUT / "verification_ready_queue.csv"
    manifest_path = INPUT / "verification_ready_queue_manifest.json"
    review_summary_path = INPUT / "candidate_review_summary.json"
    duplicate_path = INPUT / "duplicate_suppression_summary.json"
    for path in (queue_path, manifest_path, review_summary_path, duplicate_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = read_json(manifest_path)
    summary = read_json(review_summary_path)
    duplicate = read_json(duplicate_path)
    rows = read_csv(queue_path)
    priorities = Counter(row.get("priority_bucket", "") for row in rows)
    required = {
        "candidate_id", "source_locator_or_url", "municipality", "state", "priority_bucket",
        "source_family_hint", "scout_target_id", "lane_id", "search_query_family", "discovery_run_id",
    }
    errors: list[str] = []
    if len(rows) != QUEUE_ROWS or manifest.get("queue_row_count") != QUEUE_ROWS:
        errors.append("verification queue count mismatch")
    if dict(priorities) != EXPECTED_PRIORITY:
        errors.append(f"priority mismatch: {dict(priorities)}")
    if sha256(queue_path) != manifest.get("queue_sha256"):
        errors.append("candidate-review queue hash mismatch")
    missing = [row.get("candidate_id", f"row-{i}") for i, row in enumerate(rows, 1) if any(not row.get(f, "").strip() for f in required)]
    if missing:
        errors.append(f"required fields missing for {len(missing)} rows")
    candidate_ids = [row["candidate_id"] for row in rows]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("duplicate candidate_id in input queue")
    if any(row.get("primary_bucket") != row.get("priority_bucket") for row in rows):
        errors.append("primary/priority bucket mismatch")
    if any(row.get("priority_bucket") not in PRIORITIES for row in rows):
        errors.append("non-verification bucket entered queue")
    if not duplicate.get("duplicate_rows_excluded_from_verification_ready_queue"):
        errors.append("duplicate suppression lineage not preserved")
    forbidden_downstream = {
        "download_status": {"", "not_downloaded"}, "source_review_status": {"", "not_source_reviewed"},
        "extraction_status": {"", "not_extracted"}, "rating_status": {"", "not_rated"},
        "ingestion_status": {"", "not_ingested"}, "codification_status": {"", "not_codified"},
    }
    if any(row.get(field, "") not in allowed for row in rows for field, allowed in forbidden_downstream.items()):
        errors.append("input contains downstream-phase status")
    if errors:
        raise RuntimeError("; ".join(errors))

    OUTPUT.mkdir(parents=True)
    (OUTPUT / "lanes").mkdir()
    assigned: dict[str, dict[str, list[dict[str, str]]]] = {
        lane: {priority: [] for priority in PRIORITIES} for lane in LANES
    }
    for priority in PRIORITIES:
        ordered = stable_priority_rows(rows, priority)
        cursor = 0
        lane_cycle = list(LANES)
        while cursor < len(ordered):
            progressed = False
            for lane in lane_cycle:
                if len(assigned[lane][priority]) < LANE_TARGETS[lane][priority] and cursor < len(ordered):
                    assigned[lane][priority].append(dict(ordered[cursor]))
                    cursor += 1
                    progressed = True
            if not progressed:
                raise RuntimeError(f"could not allocate {priority}")

    lane_rows: dict[str, list[dict[str, str]]] = {}
    all_rows: list[dict[str, str]] = []
    sequence = 0
    for lane in LANES:
        lane_rows[lane] = interleave(assigned[lane])
        for lane_sequence, row in enumerate(lane_rows[lane], 1):
            sequence += 1
            row["verification_row_id"] = f"B4X2500V-20260730-{sequence:05d}"
            row["verification_lane_id"] = lane
            row["verification_lane_sequence"] = str(lane_sequence)
            row["canonical_locator_before_verification"] = canonical_locator(row["source_locator_or_url"])
            row["source_domain"] = row.get("source_domain") or source_domain(row["source_locator_or_url"])
            row["verification_status"] = "verification_not_run"
            row["http_status_code"] = ""
            row["final_url_or_locator"] = ""
            row["final_canonical_locator"] = ""
            row["redirect_count"] = ""
            row["content_type"] = ""
            row["content_length_header"] = ""
            row["verification_method"] = "HEAD"
            row["verification_attempt_count"] = "0"
            row["verification_started_at"] = ""
            row["verification_completed_at"] = ""
            row["error_class"] = ""
            row["error_message_redacted"] = ""
            row["pre_duplicate_verification_status"] = ""
            row["checkpoint_id"] = ""
            row["download_status"] = "not_downloaded"
            row["source_review_status"] = "not_source_reviewed"
            row["extraction_status"] = "not_extracted"
            row["rating_status"] = "not_rated"
            row["ingestion_status"] = "not_ingested"
            row["codification_status"] = "not_codified"
            row["causal_status"] = "not_causal_evidence"
            row["global_analysis_readiness"] = "false"
            all_rows.append(row)

    locked_csv = OUTPUT / "verification_locked_queue.csv"
    write_csv(locked_csv, all_rows)
    write_jsonl(OUTPUT / "verification_locked_queue.jsonl", all_rows)
    lane_hashes: dict[str, dict[str, str]] = {}
    distribution: dict[str, Any] = {}
    for lane in LANES:
        short = lane[-3:]
        csv_path = OUTPUT / f"verification_lane_{short}_queue.csv"
        jsonl_path = OUTPUT / f"verification_lane_{short}_queue.jsonl"
        write_csv(csv_path, lane_rows[lane])
        write_jsonl(jsonl_path, lane_rows[lane])
        (OUTPUT / "lanes" / lane).mkdir()
        counts = Counter(row["priority_bucket"] for row in lane_rows[lane])
        distribution[lane] = {
            "total_rows": len(lane_rows[lane]), "priority_counts": dict(counts),
            "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
        }
        lane_hashes[lane] = {"csv_sha256": sha256(csv_path), "jsonl_sha256": sha256(jsonl_path)}
        write_json(OUTPUT / "lanes" / lane / "lane_manifest.json", {
            "task_id": TASK_ID, "lane_id": lane, **distribution[lane], **lane_hashes[lane],
            "checkpoint_frequency": "after_every_row", "verification_method": "HEAD_metadata_only",
        })
    lock = {
        "task_id": TASK_ID, "created_at": utc_now(), "preflight_head": head,
        "input_paths": {
            str(queue_path.relative_to(ROOT)): sha256(queue_path),
            str(manifest_path.relative_to(ROOT)): sha256(manifest_path),
            str(review_summary_path.relative_to(ROOT)): sha256(review_summary_path),
            str(duplicate_path.relative_to(ROOT)): sha256(duplicate_path),
        },
        "queue_row_count": len(all_rows), "priority_counts": dict(Counter(row["priority_bucket"] for row in all_rows)),
        "locked_queue_csv_sha256": sha256(locked_csv),
        "locked_queue_jsonl_sha256": sha256(OUTPUT / "verification_locked_queue.jsonl"),
        "lane_hashes": lane_hashes, "lane_distribution": distribution,
        "candidate_id_set_sha256": hashlib.sha256("\n".join(sorted(candidate_ids)).encode()).hexdigest(),
        "duplicate_suppression_lineage_preserved": True, "network_requests": 0,
        "documents_downloaded": 0, "response_bodies_saved": 0,
    }
    write_json(OUTPUT / "verification_manifest.json", lock)
    write_json(OUTPUT / "verification_lane_distribution.json", {
        "lane_distribution": distribution, "total_rows": len(all_rows),
        "priority_totals": dict(Counter(row["priority_bucket"] for row in all_rows)),
        "exact_target_distribution_passed": True, "priority_interleaving": "stable proportional merge",
    })
    md_lines = ["# Verification lane distribution", "", "All 5,768 verification-ready rows are locked exactly once.", "", "| lane | high | medium | low | total | stagger |", "|---|---:|---:|---:|---:|---:|"]
    for lane in LANES:
        c = distribution[lane]["priority_counts"]
        md_lines.append(f"| {lane} | {c[PRIORITIES[0]]:,} | {c[PRIORITIES[1]]:,} | {c[PRIORITIES[2]]:,} | {distribution[lane]['total_rows']:,} | T+{STAGGER_MINUTES[lane]} min |")
    md_lines.extend(["", "Within each lane, stable proportional interleaving disperses all three priority classes."])
    write_text(OUTPUT / "verification_lane_distribution.md", "\n".join(md_lines))
    write_json(OUTPUT / "preflight_report.json", {
        "deterministic_preflight_passed": True, "network_smoke_passed": False,
        "queue_count": len(all_rows), "priority_counts": lock["priority_counts"],
        "lane_distribution": distribution, "all_required_fields_present": True,
        "one_priority_bucket_per_row": True, "non_verification_bucket_rows": 0,
        "duplicate_suppression_lineage_preserved": True, "response_bodies_planned": 0,
        "downloads_planned": 0, "forbidden_downstream_work_planned": 0,
    })
    print(json.dumps({"status": "prepared", "queue_rows": len(all_rows), "priority_counts": lock["priority_counts"], "lanes": distribution}, sort_keys=True))


def validate_locks() -> tuple[list[dict[str, str]], dict[str, Any]]:
    lock = read_json(OUTPUT / "verification_manifest.json")
    master_path = OUTPUT / "verification_locked_queue.csv"
    master = read_csv(master_path)
    if len(master) != QUEUE_ROWS or sha256(master_path) != lock["locked_queue_csv_sha256"]:
        raise RuntimeError("master lock count/hash mismatch")
    master_jsonl = OUTPUT / "verification_locked_queue.jsonl"
    if sha256(master_jsonl) != lock["locked_queue_jsonl_sha256"]:
        raise RuntimeError("master JSONL lock hash mismatch")
    union: list[dict[str, str]] = []
    for lane in LANES:
        short = lane[-3:]
        path = OUTPUT / f"verification_lane_{short}_queue.csv"
        jsonl_path = OUTPUT / f"verification_lane_{short}_queue.jsonl"
        rows = read_csv(path)
        if len(rows) != 1442 or sha256(path) != lock["lane_hashes"][lane]["csv_sha256"]:
            raise RuntimeError(f"{lane} lock count/hash mismatch")
        if sha256(jsonl_path) != lock["lane_hashes"][lane]["jsonl_sha256"]:
            raise RuntimeError(f"{lane} JSONL lock hash mismatch")
        if Counter(row["priority_bucket"] for row in rows) != Counter(LANE_TARGETS[lane]):
            raise RuntimeError(f"{lane} priority distribution mismatch")
        if any(row["verification_lane_id"] != lane for row in rows):
            raise RuntimeError(f"{lane} scope violation")
        union.extend(rows)
    ids = [row["verification_row_id"] for row in union]
    if len(ids) != len(set(ids)) or set(ids) != {row["verification_row_id"] for row in master}:
        raise RuntimeError("lane union does not equal master exactly once")
    return master, lock


async def probe(client: Any, row: dict[str, str]) -> dict[str, str]:
    locator = row["source_locator_or_url"]
    started = utc_now()
    if not canonical_locator(locator):
        return {
            "verification_status": "malformed_locator", "verification_started_at": started,
            "verification_completed_at": utc_now(), "verification_method": "none",
            "verification_attempt_count": "0", "error_class": "invalid_http_locator",
            "error_message_redacted": "locator is not a supported absolute HTTP(S) URL",
        }
    last_status = "verification_error"
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            async with client.stream("HEAD", locator) as response:
                code = int(response.status_code)
                redirects = len(response.history)
                final_canonical = canonical_locator(str(response.url))
                # Final locators are query/fragment-free to avoid retaining redirect tokens.
                final_url = final_canonical
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
                content_length = response.headers.get("content-length", "").strip()
            if 200 <= code < 400:
                status = "reachable_with_redirect" if redirects or final_canonical != row["canonical_locator_before_verification"] else "reachable"
            elif code in {401, 403, 429} or 500 <= code < 600:
                last_status = "blocked_or_forbidden"
                last_error = f"head_http_{code}"
                if (code == 429 or code >= 500) and attempt <= MAX_RETRIES:
                    await asyncio.sleep(float(attempt))
                    continue
                status = last_status
            else:
                status = "unavailable"
            return {
                "verification_status": status, "http_status_code": str(code),
                "final_url_or_locator": final_url, "final_canonical_locator": final_canonical,
                "redirect_count": str(redirects), "content_type": content_type or "not_reported",
                "content_length_header": content_length or "not_reported", "verification_method": "HEAD",
                "verification_attempt_count": str(attempt), "verification_started_at": started,
                "verification_completed_at": utc_now(), "error_class": last_error if status == "blocked_or_forbidden" else "",
                "error_message_redacted": last_error if status == "blocked_or_forbidden" else "",
            }
        except Exception as exc:
            name = type(exc).__name__
            if "Timeout" in name:
                last_status = "timeout"
            elif name in {"ConnectError", "RemoteProtocolError", "ProxyError", "NetworkError", "ReadError", "WriteError"}:
                last_status = "blocked_or_forbidden"
            else:
                last_status = "verification_error"
            last_error = name
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(float(attempt))
                continue
            return {
                "verification_status": last_status, "http_status_code": "", "final_url_or_locator": "",
                "final_canonical_locator": "", "redirect_count": "", "content_type": "not_reported",
                "content_length_header": "not_reported", "verification_method": "HEAD",
                "verification_attempt_count": str(attempt), "verification_started_at": started,
                "verification_completed_at": utc_now(), "error_class": name,
                "error_message_redacted": name,
            }
    raise AssertionError("unreachable")


def make_client(httpx: Any, connections: int) -> Any:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(TIMEOUT_SECONDS),
        limits=httpx.Limits(max_connections=connections, max_keepalive_connections=connections),
        follow_redirects=True, max_redirects=MAX_REDIRECTS,
        headers={"User-Agent": "GabrielWagesLocatorVerifier/2.1 (HEAD-only metadata check)"},
        trust_env=False,
    )


async def smoke() -> None:
    import httpx
    master, _ = validate_locks()
    selected: list[dict[str, str]] = []
    families: set[str] = set()
    for priority in PRIORITIES:
        candidates = [row for row in master if row["priority_bucket"] == priority]
        row = next((candidate for candidate in candidates if candidate["source_family_hint"] not in families), candidates[0])
        selected.append(row)
        families.add(row["source_family_hint"])
    metadata = []
    async with make_client(httpx, 3) as client:
        for row in selected:
            result = await probe(client, row)
            metadata.append({
                "verification_row_id": row["verification_row_id"], "priority_bucket": row["priority_bucket"],
                "source_family_hint": row["source_family_hint"], "source_domain": row["source_domain"],
                "verification_status": result["verification_status"], "http_status_code": result.get("http_status_code", ""),
                "error_class": result.get("error_class", ""), "response_body_saved": "false",
                "raw_headers_saved": "false", "downloaded": "false",
            })
    observed = any(row["http_status_code"] for row in metadata)
    write_csv(OUTPUT / "network_smoke_metadata.csv", metadata, metadata[0].keys())
    report = read_json(OUTPUT / "preflight_report.json")
    report.update({
        "network_smoke_passed": observed, "network_smoke_rows": len(metadata),
        "network_smoke_http_responses": sum(bool(row["http_status_code"]) for row in metadata),
        "network_smoke_priority_coverage": sorted({row["priority_bucket"] for row in metadata}),
        "network_smoke_source_families": sorted({row["source_family_hint"] for row in metadata}),
        "network_smoke_response_bodies_saved": 0, "network_smoke_downloads": 0,
    })
    write_json(OUTPUT / "preflight_report.json", report)
    if not observed:
        raise RuntimeError("global HEAD metadata transport smoke failed")
    print(json.dumps({"status": "smoke_passed", "rows": metadata}, sort_keys=True))


async def wait_until(start_at: str | None) -> None:
    if not start_at:
        return
    target = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
    while True:
        remaining = (target - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return
        await asyncio.sleep(min(30.0, remaining))


def lane_paths(lane: str) -> dict[str, Path]:
    directory = OUTPUT / "lanes" / lane
    return {
        "directory": directory, "results": directory / "results.csv",
        "checkpoint": directory / "checkpoint.json", "summary": directory / "summary.json",
        "resume": directory / "resume_state.json",
    }


async def run_lane(lane: str, start_at: str | None) -> None:
    import httpx
    if lane not in LANES:
        raise RuntimeError(f"unknown lane: {lane}")
    _, lock = validate_locks()
    if not read_json(OUTPUT / "preflight_report.json").get("network_smoke_passed"):
        raise RuntimeError("network smoke did not pass")
    short = lane[-3:]
    queue = read_csv(OUTPUT / f"verification_lane_{short}_queue.csv")
    paths = lane_paths(lane)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    completed: dict[str, dict[str, str]] = {}
    if paths["results"].is_file():
        prior = read_csv(paths["results"])
        completed = {row["verification_row_id"]: row for row in prior}
        if len(completed) != len(prior):
            raise RuntimeError(f"{lane} result checkpoint has duplicate rows")
    if paths["checkpoint"].is_file():
        checkpoint = read_json(paths["checkpoint"])
        if checkpoint.get("queue_sha256") != lock["lane_hashes"][lane]["csv_sha256"]:
            raise RuntimeError(f"{lane} checkpoint lock mismatch")
        if checkpoint.get("status") == "completed":
            print(json.dumps({"lane_id": lane, "status": "already_completed", "completed_rows": len(completed)}))
            return
    await wait_until(start_at)
    started = utc_now()
    initial_completed = len(completed)
    remaining = [row for row in queue if row["verification_row_id"] not in completed]
    async with make_client(httpx, CONCURRENCY) as client:
        for offset in range(0, len(remaining), CONCURRENCY):
            batch = remaining[offset:offset + CONCURRENCY]
            batch_started = asyncio.get_running_loop().time()
            results = await asyncio.gather(*(probe(client, row) for row in batch))
            for row, metadata in zip(batch, results):
                result = dict(row)
                result.update(metadata)
                result["checkpoint_id"] = f"{lane}-{int(row['verification_lane_sequence']):04d}"
                result["download_status"] = "not_downloaded"
                result["source_review_status"] = "not_source_reviewed"
                result["extraction_status"] = "not_extracted"
                result["rating_status"] = "not_rated"
                result["ingestion_status"] = "not_ingested"
                result["codification_status"] = "not_codified"
                result["causal_status"] = "not_causal_evidence"
                result["global_analysis_readiness"] = "false"
                append_csv(paths["results"], result)
                completed[result["verification_row_id"]] = result
                write_json(paths["checkpoint"], {
                    "task_id": TASK_ID, "lane_id": lane, "status": "in_progress",
                    "queue_sha256": lock["lane_hashes"][lane]["csv_sha256"],
                    "locked_rows": len(queue), "completed_rows": len(completed),
                    "remaining_rows": len(queue) - len(completed),
                    "last_verification_row_id": result["verification_row_id"],
                    "checkpointed_at": utc_now(), "checkpoint_frequency": "after_every_row",
                    "response_bodies_saved": 0, "downloads": 0,
                })
            elapsed = asyncio.get_running_loop().time() - batch_started
            if offset + CONCURRENCY < len(remaining) and elapsed < MIN_BATCH_INTERVAL_SECONDS:
                await asyncio.sleep(MIN_BATCH_INTERVAL_SECONDS - elapsed)
    ordered = [completed[row["verification_row_id"]] for row in queue]
    finished = utc_now()
    counts = Counter(row["verification_status"] for row in ordered)
    summary = {
        "task_id": TASK_ID, "lane_id": lane, "status": "completed",
        "locked_rows": len(queue), "completed_rows": len(ordered), "remaining_rows": 0,
        "priority_counts": dict(Counter(row["priority_bucket"] for row in ordered)),
        "terminal_status_counts": dict(counts), "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
        "scheduled_start_at": start_at or started, "actual_started_at": started, "completed_at": finished,
        "resumed_completed_rows": initial_completed, "checkpoint_frequency": "after_every_row",
        "verification_method": "HEAD_metadata_only", "response_bodies_saved": 0,
        "raw_headers_saved": 0, "downloads": 0, "source_reviews": 0,
    }
    write_json(paths["summary"], summary)
    write_json(paths["checkpoint"], {
        "task_id": TASK_ID, "lane_id": lane, "status": "completed",
        "queue_sha256": lock["lane_hashes"][lane]["csv_sha256"], "locked_rows": len(queue),
        "completed_rows": len(ordered), "remaining_rows": 0,
        "last_verification_row_id": queue[-1]["verification_row_id"], "checkpointed_at": finished,
        "checkpoint_frequency": "after_every_row", "response_bodies_saved": 0, "downloads": 0,
    })
    write_json(paths["resume"], {
        "lane_id": lane, "status": "completed", "completed_rows": len(ordered),
        "remaining_rows": 0, "resume_required": False, "queue_sha256": lock["lane_hashes"][lane]["csv_sha256"],
    })
    print(json.dumps(summary, sort_keys=True))


def outcome_table(rows: list[dict[str, str]], field: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field, "") or "unknown"].append(row)
    values = {}
    for key, group in sorted(grouped.items()):
        counts = Counter(row["verification_status"] for row in group)
        values[key] = {
            "total": len(group), "source_review_ready": sum(counts[s] for s in READY_STATUSES),
            "terminal_status_counts": dict(sorted(counts.items())),
        }
    return {"grouping_field": field, "total_rows": len(rows), "groups": values}


def write_queue_pair(stem: str, rows: list[dict[str, str]]) -> None:
    write_csv(OUTPUT / f"{stem}.csv", rows)
    write_jsonl(OUTPUT / f"{stem}.jsonl", rows)


def merge() -> None:
    master, lock = validate_locks()
    merged: list[dict[str, str]] = []
    lane_summaries: dict[str, Any] = {}
    for lane in LANES:
        paths = lane_paths(lane)
        if not paths["summary"].is_file() or read_json(paths["summary"]).get("status") != "completed":
            raise RuntimeError(f"{lane} is incomplete")
        rows = read_csv(paths["results"])
        if len(rows) != 1442 or len({row["verification_row_id"] for row in rows}) != 1442:
            raise RuntimeError(f"{lane} results do not reconcile")
        for row in rows:
            # Normalize redirect destinations after live work as an additional token-redaction guard.
            row["final_url_or_locator"] = row.get("final_canonical_locator", "")
        write_csv(paths["results"], rows)
        lane_summaries[lane] = read_json(paths["summary"])
        merged.extend(rows)
    by_id = {row["verification_row_id"]: row for row in merged}
    if len(by_id) != QUEUE_ROWS or set(by_id) != {row["verification_row_id"] for row in master}:
        raise RuntimeError("merged results do not equal locked queue")
    merged = [by_id[row["verification_row_id"]] for row in master]
    final_seen: dict[str, str] = {}
    for row in merged:
        final = row.get("final_canonical_locator", "")
        if row["verification_status"] in READY_STATUSES and final:
            if final in final_seen:
                row["pre_duplicate_verification_status"] = row["verification_status"]
                row["verification_status"] = "duplicate_final_locator"
                row["notes"] = (row.get("notes", "") + f" Canonical final locator duplicate of {final_seen[final]}.").strip()
            else:
                final_seen[final] = row["verification_row_id"]
    for lane in LANES:
        short = lane[-3:]
        rows = [row for row in merged if row["verification_lane_id"] == lane]
        write_queue_pair(f"verification_lane_{short}_results", rows)
    write_queue_pair("merged_verification_results", merged)
    ready = [row for row in merged if row["verification_status"] in READY_STATUSES]
    unavailable = [row for row in merged if row["verification_status"] == "unavailable"]
    blocked = [row for row in merged if row["verification_status"] in {"blocked_or_forbidden", "timeout"}]
    duplicates = [row for row in merged if row["verification_status"] == "duplicate_final_locator"]
    errors = [row for row in merged if row["verification_status"] in {"verification_error", "malformed_locator"}]
    write_queue_pair("source_review_ready_queue", ready)
    write_queue_pair("unavailable_or_failed_queue", unavailable)
    write_queue_pair("blocked_timeout_queue", blocked)
    write_queue_pair("duplicate_final_locator_queue", duplicates)
    write_queue_pair("verification_error_queue", errors)
    status_counts = Counter(row["verification_status"] for row in merged)
    summaries = {
        "priority_outcome_summary.json": outcome_table(merged, "priority_bucket"),
        "source_family_outcome_summary.json": outcome_table(merged, "source_family_hint"),
        "geography_outcome_summary.json": {
            "state": outcome_table(merged, "state"), "region": outcome_table(merged, "region")
        },
        "cba_non_cba_outcome_summary.json": outcome_table(merged, "cba_non_cba_hint"),
        "mechanism_hint_outcome_summary.json": outcome_table(merged, "possible_mechanism_hints"),
    }
    for name, value in summaries.items():
        write_json(OUTPUT / name, value)
    decision = "broad_state_4x2500_verification_completed_source_review_ready"
    summary = {
        "task_id": TASK_ID, "decision": decision, "verification_status": "completed",
        "verification_queue_count": len(merged), "completed_verification_rows": len(merged),
        "priority_counts_verified": dict(Counter(row["priority_bucket"] for row in merged)),
        "lane_counts": {lane: 1442 for lane in LANES}, "lane_summaries": lane_summaries,
        "terminal_status_counts": dict(sorted(status_counts.items())),
        "source_review_ready_count": len(ready), "unavailable_count": len(unavailable),
        "blocked_or_timeout_count": len(blocked), "duplicate_final_locator_count": len(duplicates),
        "verification_error_or_malformed_count": len(errors), "verification_method": "HEAD_metadata_only",
        "response_bodies_saved": 0, "raw_headers_saved": 0, "documents_downloaded": 0,
        "source_documents_inspected": 0, "source_reviews": 0, "text_extractions": 0,
        "ocr_runs": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "final_causal_claims": 0,
        "dashboard_map_filter": "total_scout_coverage_only", "dashboard_scout_covered_municipalities": 16887,
        "global_readiness_flags_preserved": {
            "global_collection_readiness": "pass", "global_mechanism_analysis_readiness": "partial_pass",
            "global_quantitative_evidence_readiness": "partial_pass",
            "global_wage_gap_analysis_readiness": "blocked_pending_normalization",
            "global_causal_analysis_readiness": "blocked_pending_matched_structure",
            "overall_global_analysis_readiness": "partial_pass",
        },
        "global_analysis_readiness": False,
        "next_task_id": "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30",
    }
    write_json(OUTPUT / "verification_summary.json", summary)
    write_json(OUTPUT / "final_decision.json", {
        "task_id": TASK_ID, "decision": decision, "verification_completed": True,
        "source_review_download_ready_next": True, "global_analysis_readiness": False,
        "documents_downloaded": 0, "finalized_at": utc_now(),
    })
    write_json(OUTPUT / "source_review_ready_manifest.json", {
        "task_id": TASK_ID, "queue_row_count": len(ready),
        "eligible_terminal_statuses": sorted(READY_STATUSES),
        "terminal_status_counts": dict(Counter(row["verification_status"] for row in ready)),
        "csv_sha256": sha256(OUTPUT / "source_review_ready_queue.csv"),
        "jsonl_sha256": sha256(OUTPUT / "source_review_ready_queue.jsonl"),
        "all_rows_from_locked_verification_queue": True, "documents_downloaded": 0,
    })
    lock.update({
        "execution_status": "completed", "decision": decision,
        "completed_verification_rows": len(merged), "terminal_status_counts": dict(sorted(status_counts.items())),
        "source_review_ready_count": len(ready),
        "merged_results_csv_sha256": sha256(OUTPUT / "merged_verification_results.csv"),
        "merged_results_jsonl_sha256": sha256(OUTPUT / "merged_verification_results.jsonl"),
        "completed_at": utc_now(), "response_bodies_saved": 0, "documents_downloaded": 0,
    })
    write_json(OUTPUT / "verification_manifest.json", lock)
    write_text(OUTPUT / "verification_summary.md", f"""# Broad-state 4 x 2,500 verification summary

Decision: `{decision}`.

All {len(merged):,} locked candidates were checked using HEAD-only response metadata across four independently checkpointed lanes of 1,442 rows. The result is {len(ready):,} unique reachable locators ready for source review/download. Terminal outcomes were: {', '.join(f'{key} {value:,}' for key, value in sorted(status_counts.items()))}.

Priority coverage is complete: 4,281 high, 1,352 medium, and 135 low rows. No response body, raw header set, source file, or downloaded document was retained. No source review, content inspection, extraction, OCR, rating, ingestion, codification, wage-gap calculation, regression, or causal analysis occurred.

The dashboard map remains total scout coverage only at 16,887 municipalities. Global collection readiness remains passed, mechanism and quantitative readiness remain partial, wage-gap readiness remains blocked pending normalization, causal readiness remains blocked pending matched structure, and overall readiness remains partial diagnostic only.
""")
    write_text(OUTPUT / "next_task.md", """# Next task: BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30

Run source review/download only over `source_review_ready_queue.csv` using four independent staggered lanes. Checkpoint every row. Retain binaries only in ignored local artifact storage, never Git, and produce retained-source manifests plus PDF/HTML/other source-type summaries. Update dashboard/status/docs.

Do not extract text, OCR, rate, ingest, codify, calculate wage gaps, run regressions, or make final causal claims. Preserve the total-scout-coverage-only dashboard map and all current global-readiness boundaries.
""")
    dashboard_status = {
        "task_id": TASK_ID, "decision": decision, "verification_queue_count": len(merged),
        "verified_row_count": len(merged), "source_review_ready_count": len(ready),
        "terminal_status_counts": dict(sorted(status_counts.items())),
        "priority_counts": summary["priority_counts_verified"], "lane_counts": summary["lane_counts"],
        "map_filter": "total_scout_coverage_only", "scout_covered_municipalities": 16887,
        "global_analysis_readiness": False, "next_stage": "four_lane_source_review_download",
    }
    write_json(OUTPUT / "dashboard_status_input.json", dashboard_status)
    dashboard_note = f"""# Broad state 4 x 2,500 verification dashboard update

All {len(merged):,} verification-ready candidates received terminal HEAD-only metadata outcomes across four lanes. {len(ready):,} unique reachable locators are ready for source review/download. Verification counts appear only in side panels and tables; the map remains actual total scout coverage at 16,887 municipalities.

Global collection readiness remains passed; mechanism and quantitative readiness remain partial; wage-gap readiness remains blocked pending normalization; causal readiness remains blocked pending matched structure; overall readiness remains partial diagnostic only.
"""
    write_text(OUTPUT / "dashboard_status_update_summary.md", dashboard_note)
    write_text(ROOT / "docs/analysis/broad_state_4x2500_verification_result_2026-07-30.md", f"""# Broad state 4 x 2,500 verification — 2026-07-30

Decision: `{decision}`. All {len(merged):,} queued rows were verified across four 1,442-row lanes, covering 4,281 high-, 1,352 medium-, and 135 low-priority candidates. {len(ready):,} canonical reachable locators are source-review-ready. Terminal outcomes: {', '.join(f'{key} {value:,}' for key, value in sorted(status_counts.items()))}.

The run used HEAD-only metadata checks and retained no response bodies, raw headers, or source files. No source review, extraction, OCR, rating, ingestion, codification, wage-gap calculation, regression, or final causal analysis occurred. Four-lane source review/download is next.
""")
    write_text(ROOT / "docs/analysis/broad_state_4x2500_verification_dashboard_status_note_2026-07-30.md", dashboard_note)
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "http_method": "HEAD_only", "response_bodies_saved": 0,
        "raw_headers_saved": 0, "documents_downloaded": 0, "source_files_retained": 0,
        "source_documents_inspected": 0, "source_reviews": 0, "text_extractions": 0,
        "ocr_runs": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effect_claims": 0,
        "final_causal_claims": 0, "full_html_bodies_saved": 0, "full_pdf_bodies_saved": 0,
    })
    print(json.dumps(summary, sort_keys=True))


def validate() -> None:
    master, lock = validate_locks()
    merged = read_csv(OUTPUT / "merged_verification_results.csv")
    ready = read_csv(OUTPUT / "source_review_ready_queue.csv")
    summary = read_json(OUTPUT / "verification_summary.json")
    dashboard = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    forbidden_output_suffixes = {".pdf", ".doc", ".docx", ".html", ".htm", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    forbidden_output_files = [
        str(path.relative_to(ROOT)) for path in OUTPUT.rglob("*")
        if path.is_file() and path.suffix.casefold() in forbidden_output_suffixes
    ]
    checks = {
        "input_queue_count_5768": len(master) == QUEUE_ROWS,
        "priority_counts_exact": Counter(row["priority_bucket"] for row in master) == Counter(EXPECTED_PRIORITY),
        "lane_counts_exact_1442_each": all(lock["lane_distribution"][lane]["total_rows"] == 1442 for lane in LANES),
        "lane_priority_distributions_exact": all(lock["lane_distribution"][lane]["priority_counts"] == LANE_TARGETS[lane] for lane in LANES),
        "every_row_in_exactly_one_lane": len({row["verification_row_id"] for row in master}) == QUEUE_ROWS,
        "no_non_verification_bucket_entered": all(row["priority_bucket"] in PRIORITIES for row in master),
        "lane_hashes_match_manifests": True,
        "one_terminal_status_per_completed_row": len(merged) == QUEUE_ROWS and all(row["verification_status"] in TERMINAL_STATUSES for row in merged),
        "merged_rows_reconcile_5768": len(merged) == QUEUE_ROWS and len({row["verification_row_id"] for row in merged}) == QUEUE_ROWS,
        "source_review_ready_eligible_only": all(row["verification_status"] in READY_STATUSES for row in ready),
        "source_review_ready_subset_of_merged": {row["verification_row_id"] for row in ready}.issubset({row["verification_row_id"] for row in merged}),
        "no_response_bodies_stored": summary["response_bodies_saved"] == 0,
        "no_source_files_downloaded": summary["documents_downloaded"] == 0,
        "no_extraction_ocr_rating_ingestion_codification": all(summary[key] == 0 for key in ("text_extractions", "ocr_runs", "rating_runs", "ingestion_runs", "codification_runs")),
        "no_wage_gap_regression_final_causal_claims": all(summary[key] == 0 for key in ("wage_gap_calculations", "regressions", "final_causal_claims")),
        "no_binary_or_full_body_artifacts_in_output": not forbidden_output_files,
        "dashboard_map_scout_coverage_only": summary["dashboard_map_filter"] == "total_scout_coverage_only" and dashboard.get("dashboard_map_filter") == "total_scout_coverage_only",
        "dashboard_actual_coverage_unchanged_16887": dashboard.get("current_scout_covered") == 16887,
        "dashboard_verification_counts_reconcile": dashboard.get("broad_state_4x2500_verified_row_count") == QUEUE_ROWS and dashboard.get("broad_state_4x2500_source_review_ready_count") == len(ready),
        "global_readiness_not_advanced": summary["global_analysis_readiness"] is False and summary["global_readiness_flags_preserved"]["overall_global_analysis_readiness"] == "partial_pass" and dashboard.get("global_analysis_readiness") is False,
    }
    passed = all(checks.values())
    report = {
        "task_id": TASK_ID, "validation_passed": passed, "checks": checks,
        "queue_count": len(master), "merged_count": len(merged), "source_review_ready_count": len(ready),
        "terminal_status_counts": dict(Counter(row["verification_status"] for row in merged)),
        "forbidden_output_files": forbidden_output_files,
        "validated_at": utc_now(),
    }
    write_json(OUTPUT / "validation_report.json", report)
    write_text(OUTPUT / "validation_report.md", "# Verification validation report\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'}: `{name}`" for name, ok in checks.items()) + f"\n\nOverall: {'PASS' if passed else 'FAIL'}.")
    if not passed:
        raise RuntimeError("verification validation failed")
    print(json.dumps(report, sort_keys=True))


def audit_staged() -> None:
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    forbidden_extensions = {".pdf", ".doc", ".docx", ".zip", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    forbidden_names = [name for name in staged if Path(name).suffix.casefold() in forbidden_extensions]
    forbidden_names.extend(
        name for name in staged
        if Path(name).suffix.casefold() in {".html", ".htm"} and not name.startswith("docs/dashboard/")
    )
    full_text_names = [
        name for name in staged
        if any(token in Path(name).name.casefold() for token in ("full_text", "extracted_text", "response_body", "raw_html"))
    ]
    large = []
    for name in staged:
        path = ROOT / name
        if path.is_file() and path.stat().st_size > 25 * 1024 * 1024:
            large.append({"path": name, "bytes": path.stat().st_size})
    allowed_prefixes = (
        "scripts/", "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-VERIFICATION-2026-07-30/",
        "docs/dashboard/", "docs/analysis/",
    )
    unexpected = [name for name in staged if not name.startswith(allowed_prefixes)]
    audit = {
        "passed": not forbidden_names and not full_text_names and not large and not unexpected,
        "staged_file_count": len(staged), "staged_files": staged,
        "forbidden_binary_or_body_extensions": forbidden_names, "full_text_or_body_named_files": full_text_names,
        "files_over_25_mib": large,
        "unexpected_staged_paths": unexpected, "retained_pdfs_staged": 0,
        "downloaded_binaries_staged": 0, "full_html_bodies_staged": 0,
        "full_extracted_text_staged": 0, "audited_at": utc_now(),
    }
    write_json(OUTPUT / "staged_file_audit.json", audit)
    if not audit["passed"]:
        raise RuntimeError("staged-file audit failed")
    print(json.dumps(audit, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--run-lane", choices=LANES)
    group.add_argument("--merge", action="store_true")
    group.add_argument("--validate", action="store_true")
    group.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--start-at")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.smoke:
        asyncio.run(smoke())
    elif args.run_lane:
        asyncio.run(run_lane(args.run_lane, args.start_at))
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    else:
        audit_staged()


if __name__ == "__main__":
    main()
