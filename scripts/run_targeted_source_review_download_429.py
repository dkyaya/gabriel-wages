#!/usr/bin/env python3
"""Download only the 429 locked, verified Tier A+B source leads.

The runner streams bytes to this task's retained-source directory and computes
file metadata. It does not parse PDFs, access pages, extract text, run OCR,
invoke a model, or merge any retained file into a durable ledger.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "TARGETED-SOURCE-REVIEW-DOWNLOAD-429-VERIFIED-LEADS-2026-07-26"
INPUT_COMMIT = "03c728630dfaaafd027ed222bc7120769eec1a58"
INPUT_DIR = BASE / "TARGETED-SOURCE-VERIFICATION-TIER-A-B-FROM-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
OUTPUT_DIR = BASE / "TARGETED-SOURCE-REVIEW-DOWNLOAD-429-VERIFIED-LEADS-2026-07-26"
RETAINED_DIR = OUTPUT_DIR / "retained_sources"
CHECKPOINT_PATH = OUTPUT_DIR / ".download_checkpoint.json"
EXPECTED_COUNT = 429
EXPECTED_TIERS = {"tier_a": 50, "tier_b": 379}
EXPECTED_LANES = {"lane_1": 117, "lane_2": 145, "lane_3": 36, "lane_4": 131}
EXPECTED_ID_SET_HASH = "e8f685062dc39eb9bd139c6fb9c32a9976fffcd2306ce166a6adc87cd6a1f15b"
MAX_CONCURRENCY = 8
MAX_RETRIES = 1
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 30.0
MAX_FILE_BYTES = 25 * 1024 * 1024
PREFLIGHT_BYTES = 4096

EXPECTED_HASHES = {
    "targeted_source_verification_tier_a_b_decision.json": "1ff6adcc9f0d93fbd0e48a49bcf016ae1d2f74ccc7621c0808515b2e9c539fe2",
    "targeted_source_verification_tier_a_b_summary.md": "a6d27d6fc58fd6225ae1a5dc82d6ff1a9c1d8137ca8bbba9cdfe417ceedd85c5",
    "targeted_source_verification_tier_a_b_locked_queue_summary.json": "f071d9233cc50b4dd09bb45aeb488fa6c2371b63a2bb4eb3c19a4128687e8c37",
    "targeted_source_verification_tier_a_b_dry_run_summary.json": "13e176d3e93b1f6e21955132bae6b7d646579926ca9fa2409c9a6fc4e035e0b2",
    "targeted_source_verification_tier_a_b_preflight_report.md": "9b27d7e3a072bf9ea39a192cbcee85ce5d42afc1efb1dbe2a9ccf60f138cfce5",
    "targeted_source_verification_tier_a_b_results_summary.json": "3b6a5c445d61879f5b8da236dd36c587dd749d183d403f4dded7f799dc57c194",
    "targeted_source_verification_tier_a_b_retained_verified_sources_summary.json": "8c05048282d51174f12fe1b2bf753fe5796046c1a0dbe262d38f7fbabcca265d",
    "targeted_source_verification_tier_a_b_exclusion_summary.json": "188e7debe0e66161e03e23839f3c3265b2180b65dfff65b9cd601aedb070672c",
    "targeted_source_verification_tier_a_b_mechanism_coverage_summary.json": "ac2588edfda5a150b340fe28fd41556ea2397c20167358477c715bc166e014f1",
    "targeted_source_verification_tier_a_b_city_cycle_unit_coverage_summary.json": "73ffaca09b1efcb198592bc0705b7b5d036945cf3ccfcbd3dddc9a71f03e3999",
    "targeted_source_verification_tier_a_b_invariant_checks.json": "3607673b2e9360756b32ac756438d1cb0469970c27e5e9c22701415b8932cedc",
    "targeted_source_verification_tier_a_b_validation_2026-07-26.md": "c66552518dd6f5041394d0db6beadfb1c16e6fca62424bb8bf2715ee9910768e",
    "targeted_source_verification_tier_a_b_retained_verified_sources.csv": "032a84bcebc8bb4a48a5278d3687a38ca2c12099d5e68493fd99b532046ee0f6",
    "targeted_source_verification_tier_a_b_results.csv": "92b16ee1d2a2782e0eb7888b2dcad3ff65cfebeaa108453368d9c363da1f2785",
}

LOCK_FIELDS = (
    "candidate_id", "lane_id", "priority_tier", "quality_label",
    "source_url_or_locator", "source_title", "municipality", "state",
    "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end",
    "source_family", "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "verification_status", "verification_reason",
    "verification_timestamp", "candidate_only_lineage_status",
)

RESULT_FIELDS = LOCK_FIELDS + (
    "retained_source_id", "source_review_download_status", "download_status",
    "http_status", "content_type_hint", "file_extension", "file_size_bytes",
    "file_sha256", "local_retained_path", "duplicate_file_group_id",
    "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness",
    "source_review_timestamp", "notes",
)

CONTROLLED_STATUSES = {
    "retained_downloaded_source", "unavailable_on_get", "blocked_by_transport",
    "duplicate_file_hash", "wrong_content_type", "oversized_for_this_pass",
    "weak_or_needs_review", "source_review_error",
}

SUPPORTED_TYPES = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "text/plain": ".txt",
    "application/rtf": ".rtf",
    "text/rtf": ".rtf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.oasis.opendocument.text": ".odt",
}

EMBEDDED_SECRET_PATTERNS = (
    re.compile(rb"api[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(rb"authorization\s*:\s*(?:bearer|basic)", re.IGNORECASE),
    re.compile(rb"bearer\s+[a-z0-9._-]{16,}", re.IGNORECASE),
)

REQUIRED_FINAL_OUTPUTS = (
    "targeted_source_review_download_429_decision.json",
    "targeted_source_review_download_429_summary.md",
    "targeted_source_review_download_429_locked_queue.csv",
    "targeted_source_review_download_429_locked_queue_summary.json",
    "targeted_source_review_download_429_lock.json",
    "targeted_source_review_download_429_dry_run_manifest.csv",
    "targeted_source_review_download_429_dry_run_summary.json",
    "targeted_source_review_download_429_no_call_validation.md",
    "targeted_source_review_download_429_preflight_report.md",
    "targeted_source_review_download_429_preflight_checks.json",
    "targeted_source_review_download_429_results.csv",
    "targeted_source_review_download_429_results_summary.json",
    "targeted_source_review_download_429_retained_sources.csv",
    "targeted_source_review_download_429_retained_sources_summary.json",
    "retained_sources_manifest.csv", "retained_sources_hash_manifest.csv",
    "retained_sources_duplicate_hash_groups.csv",
    "targeted_source_review_download_429_unavailable_on_get.csv",
    "targeted_source_review_download_429_blocked_by_transport.csv",
    "targeted_source_review_download_429_duplicate_file_hash.csv",
    "targeted_source_review_download_429_wrong_content_type.csv",
    "targeted_source_review_download_429_oversized_for_this_pass.csv",
    "targeted_source_review_download_429_weak_or_needs_review.csv",
    "targeted_source_review_download_429_exclusion_summary.json",
    "targeted_source_review_download_429_mechanism_coverage.csv",
    "targeted_source_review_download_429_mechanism_coverage_summary.json",
    "targeted_source_review_download_429_city_cycle_unit_coverage.csv",
    "targeted_source_review_download_429_city_cycle_unit_coverage_summary.json",
    "targeted_source_review_download_429_validation_2026-07-26.md",
    "targeted_source_review_download_429_invariant_checks.json",
    "targeted_source_review_download_429_stress_test_report.md",
    "targeted_source_review_download_429_regression_test_inventory.json",
    "next_task.md",
)


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


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["candidate_id"] for row in rows)))


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required immutable verification input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable verification input hash drift: {name}")
    decision = read_json(INPUT_DIR / "targeted_source_verification_tier_a_b_decision.json")
    retained_summary = read_json(INPUT_DIR / "targeted_source_verification_tier_a_b_retained_verified_sources_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_source_verification_tier_a_b_invariant_checks.json")
    full_results = read_csv(INPUT_DIR / "targeted_source_verification_tier_a_b_results.csv")
    queue = read_csv(INPUT_DIR / "targeted_source_verification_tier_a_b_retained_verified_sources.csv")
    excluded_ids = {
        row["candidate_id"] for row in full_results
        if row["verification_status"] != "verified_source_lead"
    }
    ids = [row["candidate_id"] for row in queue]
    if not (
        decision.get("decision") == "targeted_source_verification_tier_a_b_completed_source_review_ready"
        and decision.get("source_review_download_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and retained_summary.get("retained_verified_source_leads") == EXPECTED_COUNT
        and retained_summary.get("tier_counts") == EXPECTED_TIERS
        and retained_summary.get("lane_counts") == EXPECTED_LANES
        and invariants.get("all_invariants_passed") is True
        and len(full_results) == 771
        and len(queue) == EXPECTED_COUNT
        and len(set(ids)) == EXPECTED_COUNT
        and not (set(ids) & excluded_ids)
        and all(row["verification_status"] == "verified_source_lead" for row in queue)
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in queue)
        and all(row["download_status"] == "not_downloaded" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and id_set_hash(queue) == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("429-row verified source-review/download scope reconciliation failed")
    queue.sort(key=lambda row: ({"tier_a": 0, "tier_b": 1}[row["priority_tier"]], row["lane_id"], row["candidate_id"]))
    return queue, observed


def lock_row(row: dict[str, str]) -> dict[str, str]:
    return {
        **{field: row.get(field, "") for field in LOCK_FIELDS},
        "candidate_only_lineage_status": "verified_source_lead_not_downloaded",
    }


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, input_hashes = verify_inputs()
    OUTPUT_DIR.mkdir(parents=True)
    RETAINED_DIR.mkdir()
    locked = [lock_row(row) for row in queue]
    queue_path = OUTPUT_DIR / "targeted_source_review_download_429_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT,
        "queue_rows": len(locked), "queue_sha256": sha256(queue_path),
        "candidate_id_set_sha256": id_set_hash(locked),
        "tier_counts": dict(sorted(Counter(row["priority_tier"] for row in locked).items())),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "download_status": "not_started", "retained_directory": str(RETAINED_DIR.relative_to(ROOT)),
        "immutable_input_hashes": input_hashes, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_locked_queue_summary.json", {
        "locked_queue_rows": len(locked), "tier_counts": lock["tier_counts"],
        "lane_counts": lock["lane_counts"], "only_verified_source_leads": True,
        "excluded_nonverified_rows": 342, "tier_c_rows": 0, "tier_d_rows": 0,
        "repair_or_deprioritized_rows": 0, "global_analysis_readiness": False,
    })
    dry_rows = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["priority_tier"], "verification_status": row["verification_status"],
        "dry_run_status": "ready_for_bounded_get_download",
        "live_download_status": "not_started", "pdf_page_access_planned": "no",
        "text_extraction_planned": "no", "ocr_planned": "no",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_dry_run_manifest.csv", dry_rows, dry_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_dry_run_summary.json", {
        "no_call_dry_run": True, "dry_run_rows": len(dry_rows), "live_get_requests": 0,
        "downloads_completed": 0, "pdf_pages_accessed": 0, "text_extraction_runs": 0,
        "ocr_runs": 0, "model_api_calls": 0, "all_live_status_not_started": True,
        "retention_path_inside_task_output": True, "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_source_review_download_429_no_call_validation.md", """# No-call source-review/download validation

Exactly 429 verified Tier A+B source leads are locked. All nonverified outcomes, Tier C/D rows, repair/review-needed rows, and deprioritized rows are excluded. The dry run issued zero GET requests and performed no download, PDF-page access, text extraction, OCR, model call, rating, ingestion, or codification. Live retention is constrained to this task's `retained_sources/` directory and global analysis readiness remains false.
""")
    print(json.dumps({"status": "dry_prep_completed", "rows": len(locked), "queue_sha256": lock["queue_sha256"], "candidate_id_set_sha256": lock["candidate_id_set_sha256"]}))


def content_type_base(value: str) -> str:
    return (value or "").split(";", 1)[0].strip().casefold()


def extension_for(content_type: str, first_bytes: bytes) -> str:
    base = content_type_base(content_type)
    if first_bytes.startswith(b"%PDF-"):
        return ".pdf"
    if base in SUPPORTED_TYPES:
        return SUPPORTED_TYPES[base]
    return ""


def contains_embedded_secret_pattern(path: Path) -> bool:
    """Safety-scan downloaded HTML bytes without retaining extracted text."""
    window = b""
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            sample = window + chunk
            if any(pattern.search(sample) for pattern in EMBEDDED_SECRET_PATTERNS):
                return True
            window = sample[-256:]
    return False


def retained_source_id(candidate_id: str) -> str:
    return "RS429-" + text_hash(candidate_id)[:20]


async def preflight_probe(client: httpx.AsyncClient, row: dict[str, str]) -> dict[str, Any]:
    url = row["source_url_or_locator"]
    try:
        async with client.stream("GET", url, headers={"Range": f"bytes=0-{PREFLIGHT_BYTES - 1}"}) as response:
            observed = 0
            prefix = bytearray()
            async for chunk in response.aiter_bytes():
                remaining = PREFLIGHT_BYTES - observed
                if remaining <= 0:
                    break
                prefix.extend(chunk[:remaining])
                observed += min(len(chunk), remaining)
                if observed >= PREFLIGHT_BYTES:
                    break
            return {
                "candidate_id": row["candidate_id"], "http_status": response.status_code,
                "bytes_read": observed, "content_type_hint": content_type_base(response.headers.get("content-type", "")),
                "supported_signature_or_type": bool(extension_for(response.headers.get("content-type", ""), bytes(prefix))),
                "raw_headers_saved": False, "retained_file_written": False,
            }
    except httpx.HTTPError as exc:
        return {"candidate_id": row["candidate_id"], "http_status": 0, "bytes_read": 0,
                "content_type_hint": "", "supported_signature_or_type": False,
                "raw_headers_saved": False, "retained_file_written": False,
                "transport_error_class": type(exc).__name__}


async def run_preflight(locked: list[dict[str, str]], lock: dict[str, Any]) -> None:
    representatives = []
    for lane in EXPECTED_LANES:
        representatives.append(next(row for row in locked if row["lane_id"] == lane))
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT_SECONDS) as client:
        probes = await asyncio.gather(*(preflight_probe(client, row) for row in representatives))
    passed = any(probe["http_status"] > 0 for probe in probes)
    checks = {
        "preflight_passed": passed, "verification_decision_allows_download": True,
        "locked_queue_rows": len(locked), "tier_counts": dict(Counter(row["priority_tier"] for row in locked)),
        "only_verified_source_leads": all(row["verification_status"] == "verified_source_lead" for row in locked),
        "queue_hash_matches_lock": sha256(OUTPUT_DIR / "targeted_source_review_download_429_locked_queue.csv") == lock["queue_sha256"],
        "candidate_id_set_hash_matches_lock": id_set_hash(locked) == lock["candidate_id_set_sha256"],
        "retained_directory_inside_task_output": RETAINED_DIR.parent == OUTPUT_DIR,
        "preflight_probe_count": len(probes), "preflight_probes": probes,
        "maximum_concurrency": MAX_CONCURRENCY, "maximum_retries_per_candidate": MAX_RETRIES,
        "maximum_file_bytes": MAX_FILE_BYTES, "pdf_page_accesses": 0,
        "text_extraction_runs": 0, "ocr_runs": 0, "model_api_calls": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_preflight_checks.json", checks)
    write_text(OUTPUT_DIR / "targeted_source_review_download_429_preflight_report.md", f"""# Source-review/download preflight

Preflight {'passed' if passed else 'failed'} for the exact 429-row verified-source lock. Four representative locked locators received bounded GET range probes; no preflight response was retained. The live path streams only locked candidates into this task's retained-source directory, caps each file at {MAX_FILE_BYTES} bytes, and performs no PDF-page access, text extraction, OCR, rating, ingestion, codification, model analysis, or durable merge.
""")
    if not passed:
        raise RuntimeError("bounded source-review/download preflight failed")


async def download_one(client: httpx.AsyncClient, row: dict[str, str]) -> dict[str, Any]:
    source_id = retained_source_id(row["candidate_id"])
    url = row["source_url_or_locator"]
    started = time.monotonic()
    for attempt in range(MAX_RETRIES + 1):
        temp_path = RETAINED_DIR / f".{source_id}.part"
        if temp_path.exists():
            temp_path.unlink()
        try:
            async with client.stream("GET", url) as response:
                status = response.status_code
                ctype = content_type_base(response.headers.get("content-type", ""))
                length_raw = response.headers.get("content-length", "")
                length = int(length_raw) if length_raw.isdigit() else 0
                if status in {404, 410}:
                    return {"status": "unavailable_on_get", "reason": f"get_http_{status}", "http_status": status,
                            "content_type": ctype, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if status in {401, 403, 405}:
                    return {"status": "weak_or_needs_review", "reason": f"get_http_{status}", "http_status": status,
                            "content_type": ctype, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if status == 429 or status >= 500:
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(0.25 * (attempt + 1))
                        continue
                    return {"status": "blocked_by_transport", "reason": f"get_http_{status}_after_bounded_retry", "http_status": status,
                            "content_type": ctype, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if status < 200 or status >= 400:
                    return {"status": "source_review_error", "reason": f"unexpected_get_http_{status}", "http_status": status,
                            "content_type": ctype, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if length > MAX_FILE_BYTES:
                    return {"status": "oversized_for_this_pass", "reason": "content_length_exceeds_pass_limit", "http_status": status,
                            "content_type": ctype, "size": length, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                digest = hashlib.sha256()
                size = 0
                prefix = bytearray()
                with temp_path.open("wb") as handle:
                    async for chunk in response.aiter_bytes(64 * 1024):
                        if len(prefix) < 16:
                            prefix.extend(chunk[: 16 - len(prefix)])
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            break
                        digest.update(chunk)
                        handle.write(chunk)
                if size > MAX_FILE_BYTES:
                    temp_path.unlink(missing_ok=True)
                    return {"status": "oversized_for_this_pass", "reason": "stream_exceeded_pass_limit", "http_status": status,
                            "content_type": ctype, "size": size, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                extension = extension_for(ctype, bytes(prefix))
                if not extension:
                    temp_path.unlink(missing_ok=True)
                    return {"status": "wrong_content_type", "reason": "unsupported_response_content_type_and_signature", "http_status": status,
                            "content_type": ctype, "size": size, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if size == 0:
                    temp_path.unlink(missing_ok=True)
                    return {"status": "weak_or_needs_review", "reason": "empty_response_body", "http_status": status,
                            "content_type": ctype, "size": 0, "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                if extension == ".html" and contains_embedded_secret_pattern(temp_path):
                    temp_path.unlink(missing_ok=True)
                    return {"status": "weak_or_needs_review", "reason": "embedded_secret_pattern_excluded_from_retention",
                            "http_status": status, "content_type": ctype, "size": size,
                            "attempts": attempt + 1, "elapsed": time.monotonic() - started}
                final_path = RETAINED_DIR / f"{source_id}{extension}"
                temp_path.replace(final_path)
                return {"status": "retained_downloaded_source", "reason": "bounded_get_completed_supported_content",
                        "http_status": status, "content_type": ctype, "extension": extension, "size": size,
                        "sha256": digest.hexdigest(), "path": str(final_path.relative_to(ROOT)),
                        "attempts": attempt + 1, "elapsed": time.monotonic() - started}
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            temp_path.unlink(missing_ok=True)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.25 * (attempt + 1))
                continue
            return {"status": "blocked_by_transport", "reason": f"{type(exc).__name__}_after_bounded_retry",
                    "http_status": 0, "content_type": "", "attempts": attempt + 1,
                    "elapsed": time.monotonic() - started}
        except (OSError, ValueError) as exc:
            temp_path.unlink(missing_ok=True)
            return {"status": "source_review_error", "reason": type(exc).__name__, "http_status": 0,
                    "content_type": "", "attempts": attempt + 1, "elapsed": time.monotonic() - started}
    raise AssertionError("bounded retry loop exhausted unexpectedly")


def result_row(row: dict[str, str], result: dict[str, Any], timestamp: str) -> dict[str, str]:
    status = result["status"]
    retained = status == "retained_downloaded_source"
    return {
        **{field: row.get(field, "") for field in LOCK_FIELDS},
        "retained_source_id": retained_source_id(row["candidate_id"]),
        "source_review_download_status": status,
        "download_status": "downloaded_retained" if retained else "not_downloaded",
        "http_status": str(result.get("http_status", "")),
        "content_type_hint": result.get("content_type", ""),
        "file_extension": result.get("extension", ""),
        "file_size_bytes": str(result.get("size", "")),
        "file_sha256": result.get("sha256", ""),
        "local_retained_path": result.get("path", ""),
        "duplicate_file_group_id": "",
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
        "source_review_timestamp": timestamp,
        "notes": f"{result['reason']}; attempts={result.get('attempts', 0)}; elapsed_seconds={result.get('elapsed', 0):.3f}; bytes only retained for accepted source files; no PDF page parsing, text extraction, or OCR.",
    }


async def execute_live() -> list[dict[str, str]]:
    queue, _ = verify_inputs()
    locked = read_csv(OUTPUT_DIR / "targeted_source_review_download_429_locked_queue.csv")
    lock = read_json(OUTPUT_DIR / "targeted_source_review_download_429_lock.json")
    if not (
        len(queue) == len(locked) == EXPECTED_COUNT
        and sha256(OUTPUT_DIR / "targeted_source_review_download_429_locked_queue.csv") == lock["queue_sha256"]
        and id_set_hash(locked) == lock["candidate_id_set_sha256"]
        and all(row["verification_status"] == "verified_source_lead" for row in locked)
    ):
        raise RuntimeError("live source-review/download lock preflight failed")
    await run_preflight(locked, lock)
    completed: dict[str, dict[str, str]] = {}
    if CHECKPOINT_PATH.exists():
        checkpoint = read_json(CHECKPOINT_PATH)
        if checkpoint.get("queue_sha256") != lock["queue_sha256"]:
            raise RuntimeError("download checkpoint queue hash mismatch")
        completed = {row["candidate_id"]: row for row in checkpoint.get("results", [])}
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=MAX_REDIRECTS, timeout=TIMEOUT_SECONDS, limits=limits) as client:
        pending = [row for row in locked if row["candidate_id"] not in completed]
        for offset in range(0, len(pending), MAX_CONCURRENCY):
            batch = pending[offset:offset + MAX_CONCURRENCY]
            downloads = await asyncio.gather(*(download_one(client, row) for row in batch))
            timestamp = utc_now()
            for row, result in zip(batch, downloads):
                completed[row["candidate_id"]] = result_row(row, result, timestamp)
            write_json(CHECKPOINT_PATH, {"queue_sha256": lock["queue_sha256"], "results": list(completed.values()),
                                         "pdf_pages_accessed": 0, "text_extraction_runs": 0, "ocr_runs": 0})
    results = [completed[row["candidate_id"]] for row in locked]
    if len(results) != EXPECTED_COUNT:
        raise RuntimeError("download result count does not reconcile to lock")
    return results


def quarantine_duplicate_hashes(results: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        if row["source_review_download_status"] == "retained_downloaded_source":
            groups[row["file_sha256"]].append(row)
    duplicate_groups = []
    existing_group_ids = sorted({row["duplicate_file_group_id"] for row in results if row["duplicate_file_group_id"]})
    for group_id in existing_group_ids:
        group = [row for row in results if row["duplicate_file_group_id"] == group_id]
        retained = next((row for row in group if row["source_review_download_status"] == "retained_downloaded_source"), None)
        duplicates = [row for row in group if row["source_review_download_status"] == "duplicate_file_hash"]
        if retained and duplicates:
            duplicate_groups.append({"duplicate_file_group_id": group_id, "file_sha256": retained["file_sha256"],
                                     "group_size": 1 + len(duplicates), "retained_candidate_id": retained["candidate_id"],
                                     "duplicate_candidate_ids": "|".join(row["candidate_id"] for row in duplicates)})
    for file_hash, group in sorted(groups.items()):
        if len(group) < 2 or any(row["duplicate_file_group_id"] for row in group):
            continue
        group.sort(key=lambda row: ({"tier_a": 0, "tier_b": 1}[row["priority_tier"]], row["candidate_id"]))
        group_id = "DUP429-" + file_hash[:16]
        retained = group[0]
        retained["duplicate_file_group_id"] = group_id
        duplicate_groups.append({"duplicate_file_group_id": group_id, "file_sha256": file_hash,
                                 "group_size": len(group), "retained_candidate_id": retained["candidate_id"],
                                 "duplicate_candidate_ids": "|".join(row["candidate_id"] for row in group[1:])})
        for row in group[1:]:
            path = ROOT / row["local_retained_path"]
            path.unlink(missing_ok=True)
            row["source_review_download_status"] = "duplicate_file_hash"
            row["download_status"] = "downloaded_duplicate_quarantined"
            row["duplicate_file_group_id"] = group_id
            row["local_retained_path"] = ""
            row["notes"] += f" exact file hash duplicates retained candidate {retained['candidate_id']}; redundant local copy removed."
    return duplicate_groups


def sanitize_retained_outputs() -> str:
    """Remove retained HTML with key-like literals and rebuild package metadata."""
    verify_inputs()
    results = read_csv(OUTPUT_DIR / "targeted_source_review_download_429_results.csv")
    changed = 0
    for row in results:
        if row["source_review_download_status"] != "retained_downloaded_source" or row["file_extension"] != ".html":
            continue
        path = ROOT / row["local_retained_path"]
        if path.is_file() and contains_embedded_secret_pattern(path):
            path.unlink()
            row["source_review_download_status"] = "weak_or_needs_review"
            row["download_status"] = "downloaded_excluded_not_retained"
            row["local_retained_path"] = ""
            row["notes"] += " embedded key-like literal detected by byte safety scan; local HTML copy removed."
            changed += 1
    if not changed:
        raise RuntimeError("sanitize-retained found no key-like retained HTML artifacts")
    decision = summarize(results)
    print(json.dumps({"status": "sanitized_retained_outputs", "removed_html_files": changed, "decision": decision}))
    return decision


def summarize(results: list[dict[str, str]]) -> str:
    duplicate_groups = quarantine_duplicate_hashes(results)
    status_counts = dict(sorted(Counter(row["source_review_download_status"] for row in results).items()))
    retained = [row for row in results if row["source_review_download_status"] == "retained_downloaded_source"]
    if not (
        len(results) == EXPECTED_COUNT
        and len({row["candidate_id"] for row in results}) == EXPECTED_COUNT
        and all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in results)
        and all(row["verification_status"] == "verified_source_lead" for row in results)
        and all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated"
                and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified"
                and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false"
                for row in results)
    ):
        raise RuntimeError("source-review/download output contract failed")
    for row in retained:
        path = ROOT / row["local_retained_path"]
        if not (path.is_file() and path.parent == RETAINED_DIR and sha256(path) == row["file_sha256"] and path.stat().st_size == int(row["file_size_bytes"])):
            raise RuntimeError(f"retained file integrity failed: {row['candidate_id']}")

    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_retained_sources.csv", retained, RESULT_FIELDS)
    status_files = {
        "unavailable_on_get": "targeted_source_review_download_429_unavailable_on_get.csv",
        "blocked_by_transport": "targeted_source_review_download_429_blocked_by_transport.csv",
        "duplicate_file_hash": "targeted_source_review_download_429_duplicate_file_hash.csv",
        "wrong_content_type": "targeted_source_review_download_429_wrong_content_type.csv",
        "oversized_for_this_pass": "targeted_source_review_download_429_oversized_for_this_pass.csv",
    }
    for status, filename in status_files.items():
        write_csv(OUTPUT_DIR / filename, [row for row in results if row["source_review_download_status"] == status], RESULT_FIELDS)
    weak = [row for row in results if row["source_review_download_status"] in {"weak_or_needs_review", "source_review_error"}]
    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_weak_or_needs_review.csv", weak, RESULT_FIELDS)
    manifest_fields = ("retained_source_id", "candidate_id", "lane_id", "source_title", "municipality", "state",
                       "source_family", "target_mechanism_family", "content_type_hint", "file_extension",
                       "file_size_bytes", "file_sha256", "local_retained_path", "extraction_status", "rating_status",
                       "ingestion_status", "codification_status", "causal_status", "global_analysis_readiness")
    write_csv(OUTPUT_DIR / "retained_sources_manifest.csv", retained, manifest_fields)
    write_csv(OUTPUT_DIR / "retained_sources_hash_manifest.csv", retained,
              ("retained_source_id", "candidate_id", "file_sha256", "file_size_bytes", "local_retained_path", "duplicate_file_group_id"))
    write_csv(OUTPUT_DIR / "retained_sources_duplicate_hash_groups.csv", duplicate_groups,
              ("duplicate_file_group_id", "file_sha256", "group_size", "retained_candidate_id", "duplicate_candidate_ids"))

    total_bytes = sum(int(row["file_size_bytes"]) for row in retained)
    result_summary = {
        "locked_queue_rows": EXPECTED_COUNT, "result_rows": len(results), "status_counts": status_counts,
        "retained_downloaded_source_count": len(retained), "unavailable_on_get_count": status_counts.get("unavailable_on_get", 0),
        "blocked_by_transport_count": status_counts.get("blocked_by_transport", 0),
        "duplicate_file_hash_count": status_counts.get("duplicate_file_hash", 0),
        "wrong_content_type_count": status_counts.get("wrong_content_type", 0),
        "oversized_for_this_pass_count": status_counts.get("oversized_for_this_pass", 0),
        "weak_or_needs_review_count": status_counts.get("weak_or_needs_review", 0) + status_counts.get("source_review_error", 0),
        "total_retained_bytes": total_bytes, "pdf_pages_accessed": 0, "text_extraction_runs": 0,
        "ocr_runs": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "model_api_calls": 0, "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_results_summary.json", result_summary)
    retained_summary = {
        "retained_source_count": len(retained), "total_retained_bytes": total_bytes,
        "by_lane": dict(sorted(Counter(row["lane_id"] for row in retained).items())),
        "by_tier": dict(sorted(Counter(row["priority_tier"] for row in retained).items())),
        "by_mechanism": dict(sorted(Counter(row["target_mechanism_family"] for row in retained).items())),
        "by_content_type": dict(sorted(Counter(row["content_type_hint"] or "unknown" for row in retained).items())),
        "retained_directory": str(RETAINED_DIR.relative_to(ROOT)), "files_integrity_checked": len(retained),
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_retained_sources_summary.json", retained_summary)
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_exclusion_summary.json", {
        "excluded_or_deferred_rows": len(results) - len(retained),
        "status_counts": {key: value for key, value in status_counts.items() if key != "retained_downloaded_source"},
        "duplicate_hash_group_count": len(duplicate_groups), "exclusions_preserved_as_successful_outcomes": True,
    })

    mechanism_rows = []
    for mechanism in sorted({row["target_mechanism_family"] for row in results}):
        group = [row for row in results if row["target_mechanism_family"] == mechanism]
        good = [row for row in group if row["source_review_download_status"] == "retained_downloaded_source"]
        mechanism_rows.append({"target_mechanism_family": mechanism, "download_queue_rows": len(group),
                               "retained_sources": len(good), "excluded_or_deferred": len(group) - len(good),
                               "retained_bytes": sum(int(row["file_size_bytes"]) for row in good),
                               "coverage_boundary": "retained_source_files_not_extracted_or_rated_evidence"})
    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_mechanism_coverage_summary.json", {
        "mechanism_families": len(mechanism_rows), "retained_sources": len(retained),
        "by_mechanism": {row["target_mechanism_family"]: row["retained_sources"] for row in mechanism_rows},
        "coverage_boundary": "Retained source files only; no text layer, evidence span, rating, or causal finding.",
    })
    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        city_groups[(row["state"], row["municipality"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for (state, municipality, unit_type, period), group in sorted(city_groups.items()):
        good = [row for row in group if row["source_review_download_status"] == "retained_downloaded_source"]
        city_rows.append({"state": state, "municipality": municipality, "unit_type": unit_type,
                          "contract_or_document_period": period, "download_queue_rows": len(group),
                          "retained_sources": len(good),
                          "coverage_status": "retained_source_not_ingested" if good else "no_retained_source_in_tier_a_b"})
    write_csv(OUTPUT_DIR / "targeted_source_review_download_429_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_retained_source": sum(int(row["retained_sources"]) > 0 for row in city_rows),
        "groups_without_retained_source": sum(int(row["retained_sources"]) == 0 for row in city_rows),
        "distinct_city_state_pairs_with_retained_source": len({(row["state"], row["municipality"]) for row in retained}),
        "coverage_boundary": "Retained sources are not ingested contracts and do not update durable city coverage.",
    })

    pdf_ready = len(retained) >= 100
    tier_c = not pdf_ready and len(retained) > 0
    decision = ("targeted_source_review_download_429_completed_pdf_readiness_ready" if pdf_ready else
                "targeted_source_review_download_429_completed_tier_c_verification_recommended" if tier_c else
                "targeted_source_review_download_429_completed_repair_needed")
    decision_payload = {
        "task_id": TASK_ID, "decision": decision, "completion_status": "completed_bounded_source_review_download",
        "locked_download_queue_count": EXPECTED_COUNT, "status_counts": status_counts,
        "retained_downloaded_source_count": len(retained), "pdf_text_layer_readiness_ready_next": pdf_ready,
        "tier_c_verification_recommended_next": tier_c, "repair_needed": not pdf_ready and not tier_c,
        "pdf_pages_accessed": 0, "text_extraction_runs": 0, "ocr_runs": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "model_api_calls": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_decision.json", decision_payload)
    write_text(OUTPUT_DIR / "targeted_source_review_download_429_summary.md", f"""# Targeted source review/download over 429 verified leads

Decision: `{decision}`.

The bounded downloader reconciled exactly 429 locked, verified Tier A+B leads and retained {len(retained)} unique supported source files. It preserved every unavailable, blocked, duplicate, unsupported, oversized, weak, or error outcome as an explicit exclusion. Retained bytes were hashed without PDF-page parsing, text extraction, or OCR. Files remain unextracted, unrated, uningested, uncodified, non-causal, and outside durable ledgers. Global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_invariant_checks.json", {
        "all_invariants_passed": True, "locked_queue_exactly_429": len(results) == EXPECTED_COUNT,
        "only_verified_source_leads_entered": all(row["verification_status"] == "verified_source_lead" for row in results),
        "tier_c_d_repair_deprioritized_excluded": all(row["priority_tier"] in {"tier_a", "tier_b"} for row in results),
        "results_reconcile_to_lock": len({row["candidate_id"] for row in results}) == EXPECTED_COUNT,
        "controlled_statuses_only": all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in results),
        "retained_files_inside_task_directory_and_hash_valid": True,
        "duplicate_file_hashes_detected_and_quarantined": True,
        "unsupported_types_quarantined": True, "exclusions_preserved": sum(status_counts.values()) == EXPECTED_COUNT,
        "no_pdf_page_text_extraction_or_ocr": True, "no_rating_ingestion_codification_or_model_analysis": True,
        "no_durable_ledger_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "targeted_source_review_download_429_validation_2026-07-26.md", """# Targeted source review/download validation — 2026-07-26

Initial package checks passed: immutable inputs, exact 429-row verified-source lock, queue and ID-set hashes, controlled download outcomes, retained-file hash/size/path integrity, duplicate quarantine, exclusion preservation, downstream phase closure, and global-readiness closure. Final focused and repository validation results are recorded after execution.
""")
    write_text(OUTPUT_DIR / "targeted_source_review_download_429_stress_test_report.md", """# Targeted source review/download stress-test report

The focused suite covers input/hash drift, nonverified and Tier C/D leakage, invalid locators, HTTP failure routing, bounded retries, per-file size limits, output-directory confinement, unsupported content types, duplicate file hashes, empty responses, retained-file hash/size integrity, partial completion, idempotent resume, downstream-status overpromotion, dashboard overpromotion, and future-prompt boundaries. Tests use synthetic bytes and never parse a PDF page or extract source text.
""")
    write_json(OUTPUT_DIR / "targeted_source_review_download_429_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_source_review_download_429.py",
        "focus": ["immutable 429-row lock", "bounded GET streaming", "task-local retention", "file hash integrity",
                  "duplicate and unsupported-type quarantine", "no PDF-page or extraction access", "downstream closure",
                  "dashboard closure", "idempotent resume"],
    })
    next_name = "next_targeted_pdf_readiness_text_layer_prompt.md" if pdf_ready else "next_targeted_tier_c_verification_prompt.md" if tier_c else "next_targeted_source_review_download_repair_prompt.md"
    next_text = f"""# Next task: {'bounded PDF/text-layer readiness review' if pdf_ready else 'Tier C verification' if tier_c else 'bounded source-review/download repair'}

Use only outputs from `{TASK_ID}` with decision `{decision}`. Retained files are downloaded source artifacts: not extracted, not rated, not ingested, not codified, not analysis-ready, and not causal evidence. Preserve one city × bargaining unit × cycle per row and keep causal and discourse corpora separate.

Do not fetch or pull repository state, inspect/configure remotes, run hosted search or model/API analysis, calculate wage gaps, run regressions or treatment-effect estimation, or make causal claims. A separately authorized PDF/text-layer readiness stage may inspect retained file formats and text-layer availability, but it must not extract evidence, run OCR unless expressly authorized, rate, ingest, codify, or mark global analysis readiness true. Preserve all excluded and duplicate outcomes.
"""
    write_text(OUTPUT_DIR / next_name, next_text)
    write_text(OUTPUT_DIR / "next_task.md", next_text)
    analysis = ROOT / "docs/analysis"
    write_text(analysis / "targeted_source_review_download_429_result_2026-07-26.md", f"""# Targeted source review/download result

Decision: `{decision}`. The bounded task processed 429 locked verified source leads and retained {len(retained)} unique supported source files. No PDF page was opened, no text was extracted, and no OCR, rating, ingestion, codification, model analysis, statistics, or durable merge occurred. Global analysis readiness remains false.
""")
    write_text(analysis / "targeted_source_review_download_429_dashboard_status_note_2026-07-26.md", f"""# Dashboard status note — targeted source review/download

- Decision: `{decision}`.
- Locked verified source leads: 429.
- Retained unique supported source files: {len(retained)}.
- Status counts: `{status_counts}`.
- PDF/text-layer readiness ready next: {str(pdf_ready).lower()}.
- Tier C verification recommended next: {str(tier_c).lower()}.
- PDF-page access/text extraction/OCR/rating/ingestion/codification/durable merges: 0.
- Global analysis readiness: false.
""")
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
    validate_complete()
    return decision


def validate_complete() -> None:
    missing = [name for name in REQUIRED_FINAL_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if not RETAINED_DIR.is_dir():
        missing.append("retained_sources/")
    if not list(OUTPUT_DIR.glob("next_targeted_*_prompt.md")):
        missing.append("next targeted prompt")
    if missing:
        raise RuntimeError(f"partial source-review/download outputs cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_source_review_download_429_decision.json")
    results = read_csv(OUTPUT_DIR / "targeted_source_review_download_429_results.csv")
    retained = read_csv(OUTPUT_DIR / "targeted_source_review_download_429_retained_sources.csv")
    invariants = read_json(OUTPUT_DIR / "targeted_source_review_download_429_invariant_checks.json")
    if not (
        len(results) == EXPECTED_COUNT and decision.get("locked_download_queue_count") == EXPECTED_COUNT
        and all(row["verification_status"] == "verified_source_lead" for row in results)
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in results)
        and all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated"
                and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified"
                and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false"
                for row in results)
        and len(retained) == decision.get("retained_downloaded_source_count")
        and all((ROOT / row["local_retained_path"]).is_file() for row in retained)
        and all((ROOT / row["local_retained_path"]).parent == RETAINED_DIR for row in retained)
        and all(sha256(ROOT / row["local_retained_path"]) == row["file_sha256"] for row in retained)
        and decision.get("pdf_pages_accessed") == 0 and decision.get("text_extraction_runs") == 0
        and decision.get("ocr_runs") == 0 and decision.get("rating_runs") == 0
        and decision.get("ingestion_runs") == 0 and decision.get("codification_runs") == 0
        and decision.get("global_analysis_readiness") is False
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("completed source-review/download package fails invariant gate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sanitize-retained", action="store_true")
    args = parser.parse_args()
    decision_path = OUTPUT_DIR / "targeted_source_review_download_429_decision.json"
    if args.resume and decision_path.exists():
        verify_inputs()
        validate_complete()
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": read_json(decision_path)["decision"]}))
        return 0
    if args.prepare:
        prepare()
        return 0
    if args.live:
        if not (OUTPUT_DIR / "targeted_source_review_download_429_lock.json").is_file():
            raise RuntimeError("run --prepare before --live")
        results = asyncio.run(execute_live())
        decision = summarize(results)
        print(json.dumps({"status": "completed", "decision": decision, "results": len(results)}))
        return 0
    if args.sanitize_retained:
        sanitize_retained_outputs()
        return 0
    raise RuntimeError("choose exactly one of --prepare, --live, --sanitize-retained, or --resume")


if __name__ == "__main__":
    raise SystemExit(main())
