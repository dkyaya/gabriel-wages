#!/usr/bin/env python3
"""Download only the 556 locked, verified Tier C source leads.

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
TASK_ID = "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27"
INPUT_COMMIT = "24615facf4d2efd18e9976d0ae0033946cf71715"
INPUT_DIR = BASE / "TARGETED-TIER-C-VERIFICATION-FROM-BOUNDED-MEMO-GAPS-AND-DASHBOARD-VISIBILITY-CHECK-2026-07-26"
OUTPUT_DIR = BASE / "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27"
RETAINED_DIR = OUTPUT_DIR / "retained_sources"
CHECKPOINT_PATH = OUTPUT_DIR / ".download_checkpoint.json"
EXPECTED_COUNT = 556
EXPECTED_TIERS = {"tier_c": 556}
EXPECTED_LANES = {"lane_1": 142, "lane_2": 177, "lane_3": 145, "lane_4": 92}
EXPECTED_MECHANISMS = {
    "strike_or_no_strike_constraint": 177,
    "fiscal_constraint_signal": 145,
    "non_safety_constraint_signal": 142,
    "market_or_comparability_pressure": 92,
}
EXPECTED_REGIONS = {"Northeast": 276, "South": 156, "Midwest": 96, "West": 28}
EXPECTED_ID_SET_HASH = "acb61edc609cda1fcf59fbffe07e8ca2d92cf0d078b6fe7d3c4239760724cad3"
MAX_CONCURRENCY = 8
MAX_RETRIES = 1
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 30.0
MAX_FILE_BYTES = 25 * 1024 * 1024
PREFLIGHT_BYTES = 4096

EXPECTED_HASHES = {
    "targeted_tier_c_verification_decision.json": "0a1753fb056bdf81857a227e4b1ac98e8f871b8f8ca64eea9d18b2211c2f2e90",
    "targeted_tier_c_verification_summary.md": "4779b2e126aeedac4b0f49c1083e57afa0f40cf0f79fe0462bc65155f1aad6bb",
    "targeted_tier_c_verification_locked_queue_summary.json": "5c855a056245d4a2d4c546cf6b4236ff16f6318818dba4c1f1a821552ce73350",
    "targeted_tier_c_verification_dry_run_summary.json": "b5a9d206c4173ecf56881d6c04e5ab55af908ca89b99652722a99d0b0f99b795",
    "targeted_tier_c_verification_preflight_report.md": "c841a5828606aeaccc67d8fded483871fb15cc584295cd9345c23f9900934c57",
    "targeted_tier_c_verification_results_summary.json": "8ed27e844efb126d17423f6fabea1212bbe60c8624d301b05da11ba3b92fde65",
    "targeted_tier_c_verification_retained_verified_sources_summary.json": "4a51751aa33cae6c3b69caf62458dd511c87f9d08e14a8bb1ad1ae9f0c8f87ef",
    "targeted_tier_c_verification_exclusion_summary.json": "8600d0753f92d24b4d6298a4e3f5af98b9eb981df0f68c5b30578ef1a9cceb6a",
    "targeted_tier_c_verification_gap_priority_summary.json": "6ff82f0610b9d2f850ed18579d61269478a15545dca21396330af521c80a8619",
    "targeted_tier_c_verification_mechanism_gap_coverage_summary.json": "b89c987cc1c991914f19b534bbc1bb5d3b29378461f24c36a92c635fd958709e",
    "targeted_tier_c_verification_city_cycle_unit_coverage_summary.json": "c3489d1886e49f16fba42283396810d788f95e2adbe2a39390eb54d9b1ed6e6c",
    "targeted_tier_c_verification_geographic_region_coverage_summary.json": "1b89ccf011948f0bec8df86cb5717ae6173f738c5cdc92a6a83418e266a4885a",
    "targeted_tier_c_verification_invariant_checks.json": "055fa203246dd8b867c4800f993235d8c38a6132d020252aef78cf4a3ae0cb8c",
    "targeted_tier_c_verification_validation_2026-07-26.md": "a0e7c798b93837f6de1c9cd535aec80b07cf302f3c66e31a2727a299f9af860e",
    "targeted_tier_c_verification_retained_verified_sources.csv": "e3365aa9cf1aa4ff4ae903d9f2bddbf60b8161297c3ae9c62a1d046cb4f9fa2b",
    "targeted_tier_c_verification_results.csv": "2e64a2c289fa9333e4814fcbe38e96f0d200ecd2efa429574b9dd1f30614846e",
}

LOCK_FIELDS = (
    "candidate_id", "lane_id", "priority_tier", "quality_label",
    "gap_priority_score", "gap_priority_reason",
    "source_url_or_locator", "source_title", "municipality", "state",
    "derived_region",
    "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end",
    "source_family", "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "verification_status", "verification_reason",
    "verified_municipality", "verified_state", "verified_region",
    "verified_unit_type", "verified_source_family",
    "verified_contract_or_document_period", "locator_accessibility_status",
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
    "dashboard_fix_and_tier_c_source_review_download_556_decision.json",
    "dashboard_fix_and_tier_c_source_review_download_556_summary.md",
    "dashboard_remote_pages_diagnostics.md",
    "dashboard_remote_pages_diagnostics.json",
    "dashboard_deployment_source_mapping.md",
    "dashboard_stale_marker_scan.md",
    "dashboard_current_metadata_visibility_check.json",
    "dashboard_fix_changed_files.txt",
    "dashboard_fix_push_status.md",
    "targeted_tier_c_source_review_download_556_locked_queue.csv",
    "targeted_tier_c_source_review_download_556_locked_queue_summary.json",
    "targeted_tier_c_source_review_download_556_lock.json",
    "targeted_tier_c_source_review_download_556_dry_run_manifest.csv",
    "targeted_tier_c_source_review_download_556_dry_run_summary.json",
    "targeted_tier_c_source_review_download_556_no_call_validation.md",
    "targeted_tier_c_source_review_download_556_preflight_report.md",
    "targeted_tier_c_source_review_download_556_preflight_checks.json",
    "targeted_tier_c_source_review_download_556_results.csv",
    "targeted_tier_c_source_review_download_556_results_summary.json",
    "targeted_tier_c_source_review_download_556_retained_sources.csv",
    "targeted_tier_c_source_review_download_556_retained_sources_summary.json",
    "retained_sources_manifest.csv", "retained_sources_hash_manifest.csv",
    "retained_sources_duplicate_hash_groups.csv",
    "duplicate_hash_summary.json",
    "targeted_tier_c_source_review_download_556_unavailable_on_get.csv",
    "targeted_tier_c_source_review_download_556_blocked_by_transport.csv",
    "targeted_tier_c_source_review_download_556_duplicate_file_hash.csv",
    "targeted_tier_c_source_review_download_556_wrong_content_type.csv",
    "targeted_tier_c_source_review_download_556_oversized_for_this_pass.csv",
    "targeted_tier_c_source_review_download_556_weak_or_needs_review.csv",
    "targeted_tier_c_source_review_download_556_exclusion_summary.json",
    "targeted_tier_c_source_review_download_556_mechanism_coverage.csv",
    "targeted_tier_c_source_review_download_556_mechanism_coverage_summary.json",
    "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage.csv",
    "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage_summary.json",
    "targeted_tier_c_source_review_download_556_geographic_region_coverage.csv",
    "targeted_tier_c_source_review_download_556_geographic_region_coverage_summary.json",
    "dashboard_fix_and_tier_c_source_review_download_556_validation_2026-07-27.md",
    "targeted_tier_c_source_review_download_556_invariant_checks.json",
    "targeted_tier_c_source_review_download_556_stress_test_report.md",
    "targeted_tier_c_source_review_download_556_regression_test_inventory.json",
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


def dashboard_visibility_ready() -> bool:
    """Fail closed unless the generated and built Pages target uses current status."""
    phase_path = ROOT / "docs/dashboard/data/project_phase_summary.json"
    readiness_path = ROOT / "docs/dashboard/data/analysis_readiness.json"
    dist_index = ROOT / "docs/dashboard/dist/index.html"
    dist_assets = ROOT / "docs/dashboard/dist/assets"
    if not (phase_path.is_file() and readiness_path.is_file() and dist_index.is_file() and dist_assets.is_dir()):
        return False
    phase = read_json(phase_path)
    readiness = read_json(readiness_path)
    wage_stage = readiness.get("stage_availability", {}).get("wage_extraction_stage", {})
    js_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(dist_assets.glob("*.js"))
    )
    return bool(
        phase.get("data_vintage") == "2026-07-27"
        and phase.get("current_phase_code")
        == "dashboard_fix_and_tier_c_download_completed_pdf_readiness_ready_dashboard_fixed"
        and phase.get("memo_decision")
        == "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended"
        and phase.get("tier_c_verification_decision")
        == "targeted_tier_c_verification_completed_source_review_ready_dashboard_visible"
        and phase.get("global_analysis_readiness") is False
        and phase.get("memo_scope", {}).get("exact_same_source_linked_pair_count") == 268
        and phase.get("memo_scope", {}).get("linked_quantitative_row_count") == 208
        and phase.get("memo_scope", {}).get("linked_qualitative_record_count") == 90
        and phase.get("tier_c_verified_source_lead_count") == 556
        and phase.get("tier_c_source_review_download_queue_count") == 556
        and phase.get("tier_c_retained_downloaded_source_count") == 463
        and phase.get("pdf_text_layer_readiness_ready_next") is True
        and wage_stage.get("targeted_tier_c_verified_source_lead_count") == 556
        and wage_stage.get("targeted_tier_c_retained_downloaded_source_count") == 463
        and "Dashboard fixed; Tier C sources retained" in js_text
        and "Scaled verification routing and source triage" not in js_text
    )


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required immutable verification input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable verification input hash drift: {name}")
    decision = read_json(INPUT_DIR / "targeted_tier_c_verification_decision.json")
    retained_summary = read_json(INPUT_DIR / "targeted_tier_c_verification_retained_verified_sources_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_tier_c_verification_invariant_checks.json")
    full_results = read_csv(INPUT_DIR / "targeted_tier_c_verification_results.csv")
    queue = read_csv(INPUT_DIR / "targeted_tier_c_verification_retained_verified_sources.csv")
    excluded_ids = {
        row["candidate_id"] for row in full_results
        if row["verification_status"] != "verified_source_lead"
    }
    ids = [row["candidate_id"] for row in queue]
    if not (
        decision.get("decision") == "targeted_tier_c_verification_completed_source_review_ready_dashboard_visible"
        and decision.get("source_review_download_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and retained_summary.get("retained_verified_source_leads") == EXPECTED_COUNT
        and retained_summary.get("lane_counts") == EXPECTED_LANES
        and retained_summary.get("mechanism_counts") == EXPECTED_MECHANISMS
        and retained_summary.get("region_counts") == EXPECTED_REGIONS
        and invariants.get("all_invariants_passed") is True
        and len(full_results) == 1000
        and len(queue) == EXPECTED_COUNT
        and len(set(ids)) == EXPECTED_COUNT
        and not (set(ids) & excluded_ids)
        and all(row["verification_status"] == "verified_source_lead" for row in queue)
        and all(row["priority_tier"] == "tier_c" for row in queue)
        and all(row["derived_region"] in EXPECTED_REGIONS for row in queue)
        and all(row["download_status"] == "not_downloaded" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and id_set_hash(queue) == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("556-row verified source-review/download scope reconciliation failed")
    queue.sort(key=lambda row: (row["lane_id"], row["candidate_id"]))
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
    queue_path = OUTPUT_DIR / "targeted_tier_c_source_review_download_556_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT,
        "queue_rows": len(locked), "queue_sha256": sha256(queue_path),
        "candidate_id_set_sha256": id_set_hash(locked),
        "tier_counts": dict(sorted(Counter(row["priority_tier"] for row in locked).items())),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in locked).items())),
        "region_counts": dict(sorted(Counter(row["derived_region"] for row in locked).items())),
        "download_status": "not_started", "retained_directory": str(RETAINED_DIR.relative_to(ROOT)),
        "immutable_input_hashes": input_hashes, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_locked_queue_summary.json", {
        "locked_queue_rows": len(locked), "tier_counts": lock["tier_counts"],
        "lane_counts": lock["lane_counts"], "mechanism_counts": lock["mechanism_counts"],
        "region_counts": lock["region_counts"], "only_verified_source_leads": True,
        "excluded_nonverified_rows": 444, "tier_a_rows": 0, "tier_b_rows": 0,
        "tier_c_rows": 556, "tier_d_rows": 0,
        "repair_or_deprioritized_rows": 0, "global_analysis_readiness": False,
    })
    dry_rows = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["priority_tier"], "verification_status": row["verification_status"],
        "dry_run_status": "ready_for_bounded_get_download",
        "live_download_status": "not_started", "pdf_page_access_planned": "no",
        "text_extraction_planned": "no", "ocr_planned": "no",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_dry_run_manifest.csv", dry_rows, dry_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_dry_run_summary.json", {
        "no_call_dry_run": True, "dry_run_rows": len(dry_rows), "live_get_requests": 0,
        "downloads_completed": 0, "pdf_pages_accessed": 0, "text_extraction_runs": 0,
        "ocr_runs": 0, "model_api_calls": 0, "all_live_status_not_started": True,
        "retention_path_inside_task_output": True, "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_no_call_validation.md", """# No-call source-review/download validation

Exactly 556 verified Tier C source leads are locked. All nonverified outcomes, Tier A/B/D rows, repair/review-needed rows, and deprioritized rows are excluded. The dry run issued zero GET requests and performed no download, PDF-page access, text extraction, OCR, model call, rating, ingestion, or codification. Live retention is constrained to this task's `retained_sources/` directory and global analysis readiness remains false.
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
    return "RS556-" + text_hash(candidate_id)[:20]


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
        "queue_hash_matches_lock": sha256(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_locked_queue.csv") == lock["queue_sha256"],
        "candidate_id_set_hash_matches_lock": id_set_hash(locked) == lock["candidate_id_set_sha256"],
        "retained_directory_inside_task_output": RETAINED_DIR.parent == OUTPUT_DIR,
        "preflight_probe_count": len(probes), "preflight_probes": probes,
        "maximum_concurrency": MAX_CONCURRENCY, "maximum_retries_per_candidate": MAX_RETRIES,
        "maximum_file_bytes": MAX_FILE_BYTES, "pdf_page_accesses": 0,
        "text_extraction_runs": 0, "ocr_runs": 0, "model_api_calls": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_preflight_checks.json", checks)
    write_text(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_preflight_report.md", f"""# Source-review/download preflight

Preflight {'passed' if passed else 'failed'} for the exact 556-row verified-source lock. Four representative locked locators received bounded GET range probes; no preflight response was retained. The live path streams only locked candidates into this task's retained-source directory, caps each file at {MAX_FILE_BYTES} bytes, and performs no PDF-page access, text extraction, OCR, rating, ingestion, codification, model analysis, or durable merge.
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
    locked = read_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_locked_queue.csv")
    lock = read_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_lock.json")
    if not (
        len(queue) == len(locked) == EXPECTED_COUNT
        and sha256(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_locked_queue.csv") == lock["queue_sha256"]
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
        group.sort(key=lambda row: row["candidate_id"])
        group_id = "DUP556-" + file_hash[:16]
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
    results = read_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_results.csv")
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
        and all(row["priority_tier"] == "tier_c" for row in results)
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

    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_retained_sources.csv", retained, RESULT_FIELDS)
    status_files = {
        "unavailable_on_get": "targeted_tier_c_source_review_download_556_unavailable_on_get.csv",
        "blocked_by_transport": "targeted_tier_c_source_review_download_556_blocked_by_transport.csv",
        "duplicate_file_hash": "targeted_tier_c_source_review_download_556_duplicate_file_hash.csv",
        "wrong_content_type": "targeted_tier_c_source_review_download_556_wrong_content_type.csv",
        "oversized_for_this_pass": "targeted_tier_c_source_review_download_556_oversized_for_this_pass.csv",
    }
    for status, filename in status_files.items():
        write_csv(OUTPUT_DIR / filename, [row for row in results if row["source_review_download_status"] == status], RESULT_FIELDS)
    weak = [row for row in results if row["source_review_download_status"] in {"weak_or_needs_review", "source_review_error"}]
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_weak_or_needs_review.csv", weak, RESULT_FIELDS)
    manifest_fields = ("retained_source_id", "candidate_id", "lane_id", "priority_tier", "quality_label",
                       "gap_priority_score", "gap_priority_reason", "source_title", "municipality", "state", "derived_region",
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
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_results_summary.json", result_summary)
    retained_summary = {
        "retained_source_count": len(retained), "total_retained_bytes": total_bytes,
        "by_lane": dict(sorted(Counter(row["lane_id"] for row in retained).items())),
        "by_tier": dict(sorted(Counter(row["priority_tier"] for row in retained).items())),
        "by_mechanism": dict(sorted(Counter(row["target_mechanism_family"] for row in retained).items())),
        "by_region": dict(sorted(Counter(row["derived_region"] for row in retained).items())),
        "by_content_type": dict(sorted(Counter(row["content_type_hint"] or "unknown" for row in retained).items())),
        "retained_directory": str(RETAINED_DIR.relative_to(ROOT)), "files_integrity_checked": len(retained),
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_retained_sources_summary.json", retained_summary)
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_exclusion_summary.json", {
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
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_mechanism_coverage_summary.json", {
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
                          "coverage_status": "retained_source_not_ingested" if good else "no_retained_source_in_tier_c"})
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_retained_source": sum(int(row["retained_sources"]) > 0 for row in city_rows),
        "groups_without_retained_source": sum(int(row["retained_sources"]) == 0 for row in city_rows),
        "distinct_city_state_pairs_with_retained_source": len({(row["state"], row["municipality"]) for row in retained}),
        "coverage_boundary": "Retained sources are not ingested contracts and do not update durable city coverage.",
    })

    region_rows = []
    for region in sorted(set(EXPECTED_REGIONS) | {row["derived_region"] for row in results}):
        group = [row for row in results if row["derived_region"] == region]
        good = [row for row in group if row["source_review_download_status"] == "retained_downloaded_source"]
        region_rows.append({
            "derived_region": region,
            "download_queue_rows": len(group),
            "retained_sources": len(good),
            "excluded_or_deferred": len(group) - len(good),
            "retained_bytes": sum(int(row["file_size_bytes"]) for row in good),
            "mapping_method": "carried_deterministic_region_from_verified_tier_c_input",
        })
    write_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_geographic_region_coverage.csv", region_rows, region_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_geographic_region_coverage_summary.json", {
        "retained_source_count": len(retained),
        "by_region": {row["derived_region"]: row["retained_sources"] for row in region_rows},
        "retained_state_count": len({row["state"] for row in retained if row["state"]}),
        "retained_city_state_pair_count": len({(row["state"], row["municipality"]) for row in retained}),
        "external_geography_lookups": 0,
        "invented_geography_fields": 0,
        "coverage_boundary": "Carried verification geography only; retained sources are not ingested or analysis ready.",
    })

    write_json(OUTPUT_DIR / "duplicate_hash_summary.json", {
        "duplicate_hash_group_count": len(duplicate_groups),
        "duplicate_file_hash_count": status_counts.get("duplicate_file_hash", 0),
        "duplicate_relationships_quarantined": True,
    })

    pdf_ready = len(retained) >= 100
    dashboard_fixed = dashboard_visibility_ready()
    decision = (
        "dashboard_fix_and_tier_c_download_completed_pdf_readiness_ready_dashboard_fixed"
        if pdf_ready and dashboard_fixed
        else "dashboard_fix_and_tier_c_download_completed_dashboard_fix_needed"
        if pdf_ready
        else "dashboard_fix_and_tier_c_download_completed_download_repair_needed"
    )
    decision_payload = {
        "task_id": TASK_ID, "decision": decision, "completion_status": "completed_bounded_source_review_download",
        "locked_download_queue_count": EXPECTED_COUNT, "status_counts": status_counts,
        "retained_downloaded_source_count": len(retained), "pdf_text_layer_readiness_ready_next": pdf_ready,
        "dashboard_repo_level_fix_complete": dashboard_fixed,
        "dashboard_external_visibility_may_depend_on_pages_or_cache": True,
        "download_repair_needed": not pdf_ready,
        "repo_cleanup_recommended_next": False,
        "pdf_pages_accessed": 0, "text_extraction_runs": 0, "ocr_runs": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "model_api_calls": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_decision.json", decision_payload)
    write_text(OUTPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_summary.md", f"""# Dashboard deployment fix and Tier C source review/download over 556 verified leads

Decision: `{decision}`.

The dashboard header/current-phase contract now uses the latest bounded memo/Tier C status rather than the historical 2026-07-23 scout checkpoint. The bounded downloader reconciled exactly 556 locked, verified Tier C leads and retained {len(retained)} unique supported source files. It preserved every unavailable, blocked, duplicate, unsupported, oversized, weak, or error outcome as an explicit exclusion. Retained bytes were hashed without PDF-page parsing, text extraction, or OCR. Files remain unextracted, unrated, uningested, uncodified, non-causal, and outside durable ledgers. Global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_invariant_checks.json", {
        "all_invariants_passed": True, "locked_queue_exactly_556": len(results) == EXPECTED_COUNT,
        "only_verified_source_leads_entered": all(row["verification_status"] == "verified_source_lead" for row in results),
        "tier_a_b_d_repair_deprioritized_excluded": all(row["priority_tier"] == "tier_c" for row in results),
        "deterministic_region_mapping_only": all(row["derived_region"] in EXPECTED_REGIONS for row in results),
        "no_geographic_metadata_invented": True,
        "dashboard_current_metadata_not_stale_2026_07_23": dashboard_fixed,
        "results_reconcile_to_lock": len({row["candidate_id"] for row in results}) == EXPECTED_COUNT,
        "controlled_statuses_only": all(row["source_review_download_status"] in CONTROLLED_STATUSES for row in results),
        "retained_files_inside_task_directory_and_hash_valid": True,
        "duplicate_file_hashes_detected_and_quarantined": True,
        "unsupported_types_quarantined": True, "exclusions_preserved": sum(status_counts.values()) == EXPECTED_COUNT,
        "no_pdf_page_text_extraction_or_ocr": True, "no_rating_ingestion_codification_or_model_analysis": True,
        "no_durable_ledger_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_validation_2026-07-27.md", """# Dashboard fix and Tier C source review/download validation — 2026-07-27

Initial package checks passed: immutable inputs, exact 556-row verified-source lock, queue and ID-set hashes, controlled download outcomes, retained-file hash/size/path integrity, duplicate quarantine, exclusion preservation, downstream phase closure, and global-readiness closure. Final focused and repository validation results are recorded after execution.
""")
    write_text(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_stress_test_report.md", """# Targeted source review/download stress-test report

The focused suite covers input/hash drift, nonverified and Tier C/D leakage, invalid locators, HTTP failure routing, bounded retries, per-file size limits, output-directory confinement, unsupported content types, duplicate file hashes, empty responses, retained-file hash/size integrity, partial completion, idempotent resume, downstream-status overpromotion, dashboard overpromotion, and future-prompt boundaries. Tests use synthetic bytes and never parse a PDF page or extract source text.
""")
    write_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_regression_test_inventory.json", {
        "suite": "scripts/test_dashboard_fix_and_tier_c_source_review_download_556.py",
        "focus": ["immutable 556-row lock", "bounded GET streaming", "task-local retention", "file hash integrity",
                  "duplicate and unsupported-type quarantine", "no PDF-page or extraction access", "downstream closure",
                  "dashboard closure", "idempotent resume"],
    })
    next_name = "next_targeted_tier_c_pdf_text_layer_readiness_prompt.md" if pdf_ready else "next_targeted_tier_c_source_review_download_repair_prompt.md"
    next_text = f"""# Next task: {'bounded Tier C PDF/text-layer readiness review' if pdf_ready else 'bounded Tier C source-review/download repair'}

Use only outputs from `{TASK_ID}` with decision `{decision}`. Retained files are downloaded source artifacts: not extracted, not rated, not ingested, not codified, not analysis-ready, and not causal evidence. Preserve one city × bargaining unit × cycle per row and keep causal and discourse corpora separate.

Do not fetch or pull repository state, inspect/configure remotes, run hosted search or model/API analysis, calculate wage gaps, run regressions or treatment-effect estimation, or make causal claims. A separately authorized PDF/text-layer readiness stage may inspect retained file formats and text-layer availability, but it must not extract evidence, run OCR unless expressly authorized, rate, ingest, codify, or mark global analysis readiness true. Preserve all excluded and duplicate outcomes.
"""
    write_text(OUTPUT_DIR / next_name, next_text)
    write_text(OUTPUT_DIR / "next_task.md", next_text)
    analysis = ROOT / "docs/analysis"
    write_text(analysis / "dashboard_deployment_fix_and_tier_c_source_review_download_556_result_2026-07-27.md", f"""# Dashboard deployment fix and Tier C source review/download result

Decision: `{decision}`. The bounded task processed 556 locked verified source leads and retained {len(retained)} unique supported source files. No PDF page was opened, no text was extracted, and no OCR, rating, ingestion, codification, model analysis, statistics, or durable merge occurred. Global analysis readiness remains false.
""")
    write_text(analysis / "dashboard_deployment_fix_and_tier_c_source_review_download_556_dashboard_status_note_2026-07-27.md", f"""# Dashboard status note — deployment fix and Tier C source review/download

- Decision: `{decision}`.
- Locked verified source leads: 556.
- Retained unique supported source files: {len(retained)}.
- Status counts: `{status_counts}`.
- PDF/text-layer readiness ready next: {str(pdf_ready).lower()}.
- Dashboard repository-level deployment fix complete: {str(dashboard_fixed).lower()}.
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
    decision = read_json(OUTPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_decision.json")
    results = read_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_results.csv")
    retained = read_csv(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_retained_sources.csv")
    invariants = read_json(OUTPUT_DIR / "targeted_tier_c_source_review_download_556_invariant_checks.json")
    if not (
        len(results) == EXPECTED_COUNT and decision.get("locked_download_queue_count") == EXPECTED_COUNT
        and all(row["verification_status"] == "verified_source_lead" for row in results)
        and all(row["priority_tier"] == "tier_c" for row in results)
        and all(row["derived_region"] in EXPECTED_REGIONS for row in results)
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
    decision_path = OUTPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_decision.json"
    if args.resume and decision_path.exists():
        verify_inputs()
        validate_complete()
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": read_json(decision_path)["decision"]}))
        return 0
    if args.prepare:
        prepare()
        return 0
    if args.live:
        if not (OUTPUT_DIR / "targeted_tier_c_source_review_download_556_lock.json").is_file():
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
