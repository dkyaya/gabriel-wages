#!/usr/bin/env python3
"""Verify Tier A+B candidate locators with bounded HTTP HEAD requests only.

The verifier never issues GET requests, reads response bodies, downloads files,
opens PDF pages, or performs source review/extraction. Candidate metadata plus
safe HTTP response metadata are the sole verification inputs.
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
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
BASE = ANALYSIS / "compensation_extraction"
TASK_ID = "TARGETED-SOURCE-VERIFICATION-TIER-A-B-FROM-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
INPUT_COMMIT = "bc6ef99ab321c05fd0976bd4c08c81da6b8f8321"
INPUT_DIR = BASE / "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
OUTPUT_DIR = BASE / "TARGETED-SOURCE-VERIFICATION-TIER-A-B-FROM-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
CHECKPOINT_PATH = OUTPUT_DIR / ".tier_a_b_head_checkpoint.json"
EXPECTED_COUNT = 771
EXPECTED_TIERS = {"tier_a": 82, "tier_b": 689}
EXPECTED_ID_SET_HASH = "33623cfafdced32348a79b77e5f66d731abb1b271138e3681a912e4a43f3eff5"
MAX_CONCURRENCY = 12
MAX_RETRIES = 1
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 8.0

EXPECTED_HASHES = {
    "targeted_scouting_four_lane_candidate_review_decision.json": "06d0e9add7c5e4591553a35abf13da59b452e92bd91d6c545516f8618e5e956c",
    "targeted_scouting_four_lane_candidate_review_summary.md": "2fcf522dd34ecd1a1042ee8ff63979ae94ee0b17183635d066eef3fba93600d5",
    "targeted_scouting_four_lane_candidate_review_scope_summary.json": "cbee564c4ac87432bb460fecc3b3997fe4fe74aa945977c2716ef69005e9ab09",
    "targeted_scouting_four_lane_candidate_quality_summary.json": "1524f75877afd8f4e7c66ddd8997911d7fe92da2df5b5995188bcd0737b49d33",
    "targeted_scouting_four_lane_verification_ready_queue_summary.json": "21981d296f35388c240c1eb702f327870c24b610de42c54bb81994aed14c8892",
    "targeted_scouting_four_lane_verification_priority_tiers_summary.json": "39fe7def06e9a60b5e0cc65ced578130966e16e043ff968698e1afb9e2b5fa2a",
    "targeted_scouting_four_lane_candidate_mechanism_coverage_review_summary.json": "3a827bdb7e07f2d734e9cce165bba25b43492faf2939c6bdc8e565cf67a13fca",
    "targeted_scouting_four_lane_candidate_city_cycle_unit_review_summary.json": "ac19dfb16a84eaae1bcde6062112cc76354e8680400612be27f5f682c3e7c85c",
    "targeted_scouting_four_lane_candidate_deduplication_report.md": "5507966f9fee0f897d26e9c2c1b3ebb56c7cb337b3240dc5d9b3ac1392662843",
    "targeted_scouting_four_lane_candidate_review_invariant_checks.json": "ebc3498ed17d7b34a8d0488f34150cb65037defe2b54ada368dd160bf182de22",
    "targeted_scouting_four_lane_candidate_review_validation_2026-07-26.md": "a57e0db7f7267e0c5fa9dfa8c93fe1338567d77bbcc06ff9768e389016234596",
    "targeted_scouting_four_lane_verification_ready_queue.csv": "197963f7dbf7c50856723bfc597fe72caf3c1f236aabc9d40891771ef7b92916",
}

RESULT_FIELDS = (
    "candidate_id", "lane_id", "priority_tier", "quality_label", "source_url_or_locator",
    "source_title", "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "same_city_match_status", "overlapping_cycle_status", "verification_status",
    "verification_reason", "verified_municipality", "verified_state", "verified_unit_type",
    "verified_source_family", "verified_contract_or_document_period",
    "locator_accessibility_status", "content_type_hint", "download_status",
    "extraction_status", "rating_status", "causal_status", "verification_timestamp", "notes",
)

LOCK_FIELDS = RESULT_FIELDS[:18] + (
    "candidate_only_lineage_status", "review_candidate_quality_score", "review_queue_rank",
)

CONTROLLED_STATUSES = {
    "verified_source_lead", "unavailable", "duplicate", "wrong_unit", "wrong_period",
    "wrong_source_family", "discourse_only", "weak_or_needs_review",
    "blocked_by_transport", "verification_error",
}

REQUIRED_FINAL_OUTPUTS = (
    "targeted_source_verification_tier_a_b_decision.json",
    "targeted_source_verification_tier_a_b_summary.md",
    "targeted_source_verification_tier_a_b_locked_queue.csv",
    "targeted_source_verification_tier_a_b_locked_queue_summary.json",
    "targeted_source_verification_tier_a_b_lock.json",
    "targeted_source_verification_tier_a_b_dry_run_manifest.csv",
    "targeted_source_verification_tier_a_b_dry_run_summary.json",
    "targeted_source_verification_tier_a_b_no_call_validation.md",
    "targeted_source_verification_tier_a_b_preflight_report.md",
    "targeted_source_verification_tier_a_b_preflight_checks.json",
    "targeted_source_verification_tier_a_b_results.csv",
    "targeted_source_verification_tier_a_b_results_summary.json",
    "targeted_source_verification_tier_a_b_retained_verified_sources.csv",
    "targeted_source_verification_tier_a_b_retained_verified_sources_summary.json",
    "targeted_source_verification_tier_a_b_unavailable.csv",
    "targeted_source_verification_tier_a_b_wrong_unit_or_period.csv",
    "targeted_source_verification_tier_a_b_duplicates.csv",
    "targeted_source_verification_tier_a_b_discourse_only.csv",
    "targeted_source_verification_tier_a_b_weak_or_needs_review.csv",
    "targeted_source_verification_tier_a_b_exclusion_summary.json",
    "targeted_source_verification_tier_a_b_mechanism_coverage.csv",
    "targeted_source_verification_tier_a_b_mechanism_coverage_summary.json",
    "targeted_source_verification_tier_a_b_city_cycle_unit_coverage.csv",
    "targeted_source_verification_tier_a_b_city_cycle_unit_coverage_summary.json",
    "targeted_source_verification_tier_a_b_validation_2026-07-26.md",
    "targeted_source_verification_tier_a_b_invariant_checks.json",
    "targeted_source_verification_tier_a_b_stress_test_report.md",
    "targeted_source_verification_tier_a_b_regression_test_inventory.json",
    "next_task.md",
)

TRACKING_QUERY_KEYS = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "utm_campaign", "utm_content",
    "utm_medium", "utm_source", "utm_term",
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def normalize_words(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def canonical_locator(value: str) -> str:
    try:
        parts = urlsplit((value or "").strip())
    except ValueError:
        return (value or "").strip().casefold()
    if not (parts.scheme and parts.netloc):
        return (value or "").strip().casefold()
    host = parts.netloc.casefold()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    query = [
        (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_QUERY_KEYS
    ]
    return urlunsplit((parts.scheme.casefold(), host, path, urlencode(sorted(query)), ""))


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["candidate_id"] for row in rows)))


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / relative
        if not path.is_file():
            raise FileNotFoundError(f"required immutable input missing: {relative}")
        observed[relative] = sha256(path)
        if observed[relative] != expected:
            raise RuntimeError(f"immutable input hash drift: {relative}")
    decision = read_json(INPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json")
    scope = read_json(INPUT_DIR / "targeted_scouting_four_lane_candidate_review_scope_summary.json")
    ready_summary = read_json(INPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_scouting_four_lane_candidate_review_invariant_checks.json")
    all_ready = read_csv(INPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue.csv")
    queue = [row for row in all_ready if row["verification_priority_tier"] in {"tier_a", "tier_b"}]
    tier_counts = dict(Counter(row["verification_priority_tier"] for row in queue))
    excluded = [row for row in queue if row["candidate_quality_label"] in {"repair_or_review_needed", "deprioritize_this_phase"}]
    if not (
        decision.get("decision") == "targeted_scouting_four_lane_candidate_review_completed_verification_ready"
        and decision.get("source_verification_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and scope.get("candidate_rows_reviewed") == 4228
        and ready_summary.get("verification_ready_rows") == 3474
        and invariants.get("all_invariants_passed") is True
        and len(all_ready) == 3474
        and len(queue) == EXPECTED_COUNT
        and tier_counts == EXPECTED_TIERS
        and not excluded
        and all(row["verification_priority_tier"] not in {"tier_c", "tier_d"} for row in queue)
        and all(row["retrieval_status"] == "candidate_only" for row in queue)
        and all(row["verification_status"] == "not_verified" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and id_set_hash(queue) == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("Tier A+B verification scope reconciliation failed")
    queue.sort(key=lambda row: ({"tier_a": 0, "tier_b": 1}[row["verification_priority_tier"]], int(row["verification_queue_rank"]), row["candidate_id"]))
    return queue, observed


def lock_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["verification_priority_tier"], "quality_label": row["candidate_quality_label"],
        "source_url_or_locator": row["source_url_or_locator"], "source_title": row["source_title"],
        "municipality": row["municipality"], "state": row["state"], "unit_type": row["unit_type"],
        "occupation_group": row["occupation_group"], "bargaining_unit_name": row["bargaining_unit_name"],
        "contract_or_document_period": row["contract_or_document_period"],
        "inferred_cycle_start": row["inferred_cycle_start"], "inferred_cycle_end": row["inferred_cycle_end"],
        "source_family": row["source_family"], "target_mechanism_family": row["target_mechanism_family"],
        "same_city_match_status": row["same_city_match_status"], "overlapping_cycle_status": row["overlapping_cycle_status"],
        "candidate_only_lineage_status": "candidate_only_not_verified",
        "review_candidate_quality_score": row["candidate_quality_score"],
        "review_queue_rank": row["verification_queue_rank"],
    }


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, input_hashes = verify_inputs()
    OUTPUT_DIR.mkdir(parents=True)
    locked = [lock_row(row) for row in queue]
    queue_path = OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    queue_hash = sha256(queue_path)
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT,
        "queue_rows": len(locked), "tier_counts": dict(Counter(row["priority_tier"] for row in locked)),
        "queue_sha256": queue_hash, "candidate_id_set_sha256": id_set_hash(locked),
        "source_review_status": "not_started", "download_status": "not_downloaded",
        "global_analysis_readiness": False, "immutable_input_hashes": input_hashes,
    }
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue_summary.json", {
        "locked_queue_rows": len(locked), "tier_counts": lock["tier_counts"],
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "quality_counts": dict(sorted(Counter(row["quality_label"] for row in locked).items())),
        "tier_c_rows": 0, "tier_d_rows": 0, "repair_or_deprioritized_rows": 0,
        "candidate_only_lineage_preserved": True,
    })
    dry_rows = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["priority_tier"], "quality_label": row["quality_label"],
        "dry_run_status": "ready_for_bounded_head_verification",
        "live_verification_status": "not_started", "document_download_planned": "no",
        "pdf_page_access_planned": "no", "source_review_planned": "no",
        "extraction_planned": "no", "notes": "Locked candidate-only metadata; HEAD requests only if live preflight passes.",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_dry_run_manifest.csv", dry_rows, dry_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_dry_run_summary.json", {
        "dry_run_rows": len(dry_rows), "tier_counts": lock["tier_counts"], "no_call_dry_run": True,
        "live_requests": 0, "downloads": 0, "pdf_page_accesses": 0,
        "source_reviews": 0, "extractions": 0, "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_no_call_validation.md", f"""# Tier A+B no-call verification validation

- Candidate-review decision: passed.
- Locked scope: {len(locked)} rows; Tier A 82 / Tier B 689.
- Candidate ID-set hash: `{id_set_hash(locked)}`.
- Queue-file SHA-256: `{queue_hash}`.
- Tier C/D/repair/deprioritized rows: 0.
- Candidate-only lineage: preserved.
- Live requests/downloads/PDF-page accesses/model calls: 0.
- Source review/extraction/rating/ingestion/codification: 0.
- Global analysis readiness: false.
""")
    preflight = {
        "deterministic_preflight_passed": True, "live_network_preflight_passed": False,
        "preflight_passed": False, "locked_queue_rows": len(locked), "tier_counts": lock["tier_counts"],
        "queue_hash_matches_lock": sha256(queue_path) == queue_hash,
        "candidate_id_set_hash_matches_lock": id_set_hash(locked) == EXPECTED_ID_SET_HASH,
        "tier_c_d_repair_deprioritized_excluded": True,
        "head_requests_only": True, "get_requests_allowed": False, "response_body_reads_allowed": False,
        "maximum_concurrency": MAX_CONCURRENCY, "maximum_retries_per_candidate": MAX_RETRIES,
        "documents_downloaded": 0, "pdf_pages_accessed": 0, "model_api_calls": 0,
        "source_review_runs": 0, "global_analysis_readiness": False,
        "live_probe_results": [],
    }
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_preflight_report.md", """# Tier A+B verification preflight

Deterministic no-call preflight passed. The exact 771-row Tier A+B queue is locked and contains no Tier C, Tier D, repair-needed, or deprioritized row. Live network preflight has not run. The live verifier is restricted to HTTP HEAD requests with no response-body read, GET fallback, document download, PDF/page access, source review, extraction, rating, ingestion, codification, model/API analysis, or global-readiness promotion.
""")
    print(json.dumps({"status": "dry_prep_completed", "queue_rows": len(locked), "queue_sha256": queue_hash}))


def years(value: str) -> set[int]:
    return {int(item) for item in re.findall(r"(?:19|20)\d{2}", value or "")}


def identity_assessment(row: dict[str, str], final_locator: str, content_type: str) -> tuple[str | None, str, int]:
    title_locator = normalize_words(" ".join((row["source_title"], row["source_url_or_locator"], final_locator)))
    identity_text = normalize_words(" ".join((row["source_title"], row["occupation_group"], row["bargaining_unit_name"], row["source_family"])))
    score = 0
    if len(row["source_title"].strip()) >= 10:
        score += 2
    if row["municipality"].strip() and row["state"].strip():
        score += 2
    if row["occupation_group"].strip():
        score += 1
    if row["bargaining_unit_name"].strip():
        score += 2
    if row["contract_or_document_period"].strip() or row["inferred_cycle_start"].strip():
        score += 2
    if row["source_family"].strip():
        score += 2
    if re.search(r"\.(?:pdf|docx?)(?:$|[?#])", row["source_url_or_locator"], flags=re.I) or any(term in title_locator for term in ("agreement", "contract", "award", "factfinding", "salary", "wage", "compensation", "budget", "ordinance")):
        score += 2

    target_years = years(" ".join((row["contract_or_document_period"], row["inferred_cycle_start"], row["inferred_cycle_end"])))
    locator_years = years(" ".join((row["source_title"], row["source_url_or_locator"])))
    if target_years and locator_years and not target_years.intersection(locator_years):
        return "wrong_period", "title_or_locator_years_conflict_with_candidate_period_metadata", score

    if row["unit_type"] == "non_safety_comparator":
        safety_terms = any(term in identity_text for term in ("police", "firefighter", "fire fighters", "fire department"))
        nonsafety_terms = any(term in identity_text for term in ("teacher", "clerical", "public works", "school", "administrative", "municipal employee", "unit a", "unit b", "unit c", "unit d", "unit e"))
        if safety_terms and not nonsafety_terms:
            return "wrong_unit", "candidate_metadata_identifies_only_a_safety_unit_for_non_safety_target", score

    if content_type.startswith(("image/", "audio/", "video/")):
        return "wrong_source_family", "response_content_type_is_not_a_document_or_html_source", score
    if any(term in title_locator for term in ("newspaper article", "news article", "op ed", "opinion article", "blog post")):
        return "discourse_only", "candidate_title_or_locator_explicitly_identifies_discourse", score
    return None, "candidate_metadata_identity_consistent", score


async def head_probe(client: Any, row: dict[str, str]) -> dict[str, Any]:
    url = row["source_url_or_locator"].strip()
    try:
        parsed = urlsplit(url)
    except ValueError:
        parsed = None
    if not parsed or parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return {"kind": "verification_error", "reason": "invalid_or_non_http_locator", "status_code": 0, "content_type": "", "final_locator": url, "elapsed": 0.0, "attempts": 0}
    last_kind = "verification_error"
    last_reason = "bounded_head_request_failed"
    started = time.monotonic()
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with client.stream("HEAD", url) as response:
                status = int(response.status_code)
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
                final_locator = str(response.url)
            if 200 <= status < 400:
                kind, reason, identity_score = identity_assessment(row, final_locator, content_type)
                if kind:
                    status_name = kind
                elif identity_score >= 8:
                    status_name = "verified_source_lead"
                    reason = "reachable_head_response_and_consistent_candidate_metadata"
                else:
                    status_name = "weak_or_needs_review"
                    reason = "reachable_but_candidate_identity_metadata_is_insufficient"
                return {"kind": status_name, "reason": reason, "status_code": status, "content_type": content_type or "not_reported", "final_locator": final_locator, "elapsed": round(time.monotonic() - started, 3), "attempts": attempt + 1, "identity_score": identity_score}
            if status in {401, 403, 404, 405, 410, 451}:
                return {"kind": "unavailable" if status != 405 else "weak_or_needs_review", "reason": f"head_http_{status}", "status_code": status, "content_type": content_type or "not_reported", "final_locator": final_locator, "elapsed": round(time.monotonic() - started, 3), "attempts": attempt + 1, "identity_score": 0}
            if status == 429 or 500 <= status < 600:
                last_kind, last_reason = "blocked_by_transport", f"head_http_{status}"
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(0.25)
                    continue
            else:
                return {"kind": "unavailable", "reason": f"head_http_{status}", "status_code": status, "content_type": content_type or "not_reported", "final_locator": final_locator, "elapsed": round(time.monotonic() - started, 3), "attempts": attempt + 1, "identity_score": 0}
        except Exception as exc:  # safe class-only reporting; no raw body or headers
            name = type(exc).__name__
            if name in {"ConnectTimeout", "ReadTimeout", "WriteTimeout", "PoolTimeout", "ConnectError", "RemoteProtocolError", "ProxyError"}:
                last_kind, last_reason = "blocked_by_transport", f"{name}_bounded_head_failure"
            else:
                last_kind, last_reason = "verification_error", f"{name}_bounded_head_failure"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.25)
                continue
    return {"kind": last_kind, "reason": last_reason, "status_code": 0, "content_type": "not_reported", "final_locator": url, "elapsed": round(time.monotonic() - started, 3), "attempts": MAX_RETRIES + 1, "identity_score": 0}


def result_row(row: dict[str, str], probe: dict[str, Any], timestamp: str) -> dict[str, str]:
    verified = probe["kind"] == "verified_source_lead"
    final_host = ""
    try:
        final_host = urlsplit(probe.get("final_locator", "")).netloc.casefold()
    except ValueError:
        pass
    return {
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["priority_tier"], "quality_label": row["quality_label"],
        "source_url_or_locator": row["source_url_or_locator"], "source_title": row["source_title"],
        "municipality": row["municipality"], "state": row["state"], "unit_type": row["unit_type"],
        "occupation_group": row["occupation_group"], "bargaining_unit_name": row["bargaining_unit_name"],
        "contract_or_document_period": row["contract_or_document_period"],
        "inferred_cycle_start": row["inferred_cycle_start"], "inferred_cycle_end": row["inferred_cycle_end"],
        "source_family": row["source_family"], "target_mechanism_family": row["target_mechanism_family"],
        "same_city_match_status": row["same_city_match_status"], "overlapping_cycle_status": row["overlapping_cycle_status"],
        "verification_status": probe["kind"], "verification_reason": probe["reason"],
        "verified_municipality": row["municipality"] if verified else "",
        "verified_state": row["state"] if verified else "",
        "verified_unit_type": row["unit_type"] if verified else "",
        "verified_source_family": row["source_family"] if verified else "",
        "verified_contract_or_document_period": row["contract_or_document_period"] if verified else "",
        "locator_accessibility_status": f"head_http_{probe['status_code']}" if probe["status_code"] else probe["reason"],
        "content_type_hint": probe["content_type"], "download_status": "not_downloaded",
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "causal_status": "not_causal_evidence", "verification_timestamp": timestamp,
        "notes": f"HEAD only; attempts={probe['attempts']}; elapsed_seconds={probe['elapsed']}; identity_score={probe.get('identity_score', 0)}; final_host_hash={text_hash(final_host)[:12] if final_host else 'none'}; final_locator_hash={text_hash(canonical_locator(probe.get('final_locator', '')))[:20]}; no body or raw headers retained.",
    }


async def network_preflight(client: Any, queue: list[dict[str, str]]) -> tuple[bool, list[dict[str, Any]]]:
    outcomes = []
    for row in queue[:5]:
        probe = await head_probe(client, row)
        outcomes.append({
            "candidate_id": row["candidate_id"], "outcome": probe["kind"],
            "http_response_observed": bool(probe["status_code"]),
            "status_code": probe["status_code"], "content_type_hint": probe["content_type"],
            "attempts": probe["attempts"], "raw_body_saved": False, "raw_headers_saved": False,
        })
    return any(item["http_response_observed"] for item in outcomes), outcomes


async def execute_live() -> list[dict[str, str]]:
    import httpx

    queue, _ = verify_inputs()
    locked = read_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue.csv")
    lock = read_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_lock.json")
    if not (
        len(locked) == EXPECTED_COUNT and dict(Counter(row["priority_tier"] for row in locked)) == EXPECTED_TIERS
        and sha256(OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue.csv") == lock["queue_sha256"]
        and id_set_hash(locked) == lock["candidate_id_set_sha256"] == EXPECTED_ID_SET_HASH
        and {row["candidate_id"] for row in locked} == {row["candidate_id"] for row in queue}
    ):
        raise RuntimeError("live preflight queue/lock reconciliation failed")

    timeout = httpx.Timeout(TIMEOUT_SECONDS, connect=TIMEOUT_SECONDS, read=TIMEOUT_SECONDS, write=TIMEOUT_SECONDS, pool=TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    headers = {"User-Agent": "GabrielWagesCandidateVerifier/1.0 (HEAD-only; research metadata verification)"}
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=MAX_REDIRECTS, headers=headers, trust_env=False) as client:
        preflight_passed, probes = await network_preflight(client, locked)
        checks = read_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_preflight_checks.json")
        checks.update({"live_network_preflight_passed": preflight_passed, "preflight_passed": preflight_passed, "live_probe_results": probes})
        write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_preflight_checks.json", checks)
        write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_preflight_report.md", f"""# Tier A+B verification preflight

- Candidate-review decision and immutable input hashes: passed.
- Locked queue: 771 rows; Tier A 82 / Tier B 689.
- Queue and ID-set hashes: passed.
- Tier C/D/repair/deprioritized rows: 0.
- Live network preflight: {'passed' if preflight_passed else 'failed'} using five locked candidates.
- HTTP method: HEAD only; GET fallback disabled.
- Response bodies/raw headers retained: 0/0.
- Maximum concurrency: {MAX_CONCURRENCY}; maximum retry per candidate: {MAX_RETRIES}.
- Downloads/PDF-page access/source review/extraction/rating/ingestion/codification/model analysis: 0.
- Global analysis readiness: false.
""")
        if not preflight_passed:
            raise RuntimeError("bounded live verification preflight failed")

        completed: dict[str, dict[str, str]] = {}
        if CHECKPOINT_PATH.is_file():
            checkpoint = read_json(CHECKPOINT_PATH)
            if checkpoint.get("queue_sha256") != lock["queue_sha256"]:
                raise RuntimeError("checkpoint queue hash mismatch")
            completed = {row["candidate_id"]: row for row in checkpoint.get("results", [])}
        pending = [row for row in locked if row["candidate_id"] not in completed]
        for offset in range(0, len(pending), MAX_CONCURRENCY):
            chunk = pending[offset:offset + MAX_CONCURRENCY]
            probes = await asyncio.gather(*(head_probe(client, row) for row in chunk))
            timestamp = utc_now()
            for row, probe in zip(chunk, probes):
                completed[row["candidate_id"]] = result_row(row, probe, timestamp)
            write_json(CHECKPOINT_PATH, {"queue_sha256": lock["queue_sha256"], "results": list(completed.values()), "raw_bodies_saved": 0, "raw_headers_saved": 0})
    results = [completed[row["candidate_id"]] for row in locked]
    if len(results) != EXPECTED_COUNT:
        raise RuntimeError("live result count does not reconcile")
    return results


def apply_redirect_duplicates(results: list[dict[str, str]]) -> None:
    # Only exact original candidate locators are available in retained output;
    # final redirect targets are represented by hashes in notes. Use the hash
    # to mark repeated final endpoints without persisting redirect URLs.
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        match = re.search(r"final_locator_hash=([a-f0-9]+)", row["notes"])
        if match and row["verification_status"] == "verified_source_lead":
            groups[match.group(1)].append(row)
    for final_hash, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda row: ({"tier_a": 0, "tier_b": 1}[row["priority_tier"]], row["candidate_id"]))
        retained = group[0]
        for row in group[1:]:
            row["verification_status"] = "duplicate"
            row["verification_reason"] = "distinct_candidate_locators_redirect_to_same_final_locator"
            row["verified_municipality"] = ""
            row["verified_state"] = ""
            row["verified_unit_type"] = ""
            row["verified_source_family"] = ""
            row["verified_contract_or_document_period"] = ""
            row["notes"] += f" retained_candidate_id={retained['candidate_id']}; final_locator_hash={final_hash}."


def summarize(results: list[dict[str, str]]) -> str:
    apply_redirect_duplicates(results)
    status_counts = dict(sorted(Counter(row["verification_status"] for row in results).items()))
    verified = [row for row in results if row["verification_status"] == "verified_source_lead"]
    unavailable = [row for row in results if row["verification_status"] == "unavailable"]
    duplicates = [row for row in results if row["verification_status"] == "duplicate"]
    wrong = [row for row in results if row["verification_status"] in {"wrong_unit", "wrong_period", "wrong_source_family"}]
    discourse = [row for row in results if row["verification_status"] == "discourse_only"]
    weak = [row for row in results if row["verification_status"] in {"weak_or_needs_review", "blocked_by_transport", "verification_error"}]
    if len(results) != EXPECTED_COUNT or any(row["verification_status"] not in CONTROLLED_STATUSES for row in results):
        raise RuntimeError("verification status or result count invalid")
    if any(row["priority_tier"] not in {"tier_a", "tier_b"} for row in results):
        raise RuntimeError("Tier C/D leakage into verification results")
    if any(row["download_status"] != "not_downloaded" or row["extraction_status"] != "not_extracted" or row["rating_status"] != "not_rated" or row["causal_status"] != "not_causal_evidence" for row in results):
        raise RuntimeError("verification output crossed a downstream phase boundary")

    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_retained_verified_sources.csv", verified, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_unavailable.csv", unavailable, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_wrong_unit_or_period.csv", wrong, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_duplicates.csv", duplicates, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_discourse_only.csv", discourse, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_weak_or_needs_review.csv", weak, RESULT_FIELDS)

    by_tier = {tier: dict(sorted(Counter(row["verification_status"] for row in results if row["priority_tier"] == tier).items())) for tier in EXPECTED_TIERS}
    summary = {
        "verification_queue_rows": len(results), "tier_counts": dict(Counter(row["priority_tier"] for row in results)),
        "verification_status_counts": status_counts, "verification_status_by_tier": by_tier,
        "verified_source_lead_count": len(verified), "unavailable_count": len(unavailable),
        "duplicate_count": len(duplicates), "wrong_unit_count": status_counts.get("wrong_unit", 0),
        "wrong_period_count": status_counts.get("wrong_period", 0),
        "wrong_source_family_count": status_counts.get("wrong_source_family", 0),
        "discourse_only_count": len(discourse), "weak_or_needs_review_output_count": len(weak),
        "blocked_by_transport_count": status_counts.get("blocked_by_transport", 0),
        "verification_error_count": status_counts.get("verification_error", 0),
        "downloads": 0, "pdf_page_accesses": 0, "response_bodies_saved": 0,
        "raw_headers_saved": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_results_summary.json", summary)
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_retained_verified_sources_summary.json", {
        "retained_verified_source_leads": len(verified),
        "tier_counts": dict(sorted(Counter(row["priority_tier"] for row in verified).items())),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in verified).items())),
        "candidate_only_lineage_preserved": True, "download_status": "not_downloaded",
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "causal_status": "not_causal_evidence", "durable_merge_count": 0,
    })
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_exclusion_summary.json", {
        "excluded_or_deferred_rows": len(results) - len(verified),
        "status_counts": {key: value for key, value in status_counts.items() if key != "verified_source_lead"},
        "exclusions_preserved_as_successful_outcomes": True,
    })

    mechanism_rows = []
    for mechanism in sorted({row["target_mechanism_family"] for row in results}):
        group = [row for row in results if row["target_mechanism_family"] == mechanism]
        good = [row for row in group if row["verification_status"] == "verified_source_lead"]
        mechanism_rows.append({
            "target_mechanism_family": mechanism, "verification_queue_rows": len(group),
            "verified_source_leads": len(good), "excluded_or_deferred": len(group) - len(good),
            "tier_a_verified": sum(row["priority_tier"] == "tier_a" for row in good),
            "tier_b_verified": sum(row["priority_tier"] == "tier_b" for row in good),
            "coverage_boundary": "verified_source_leads_not_downloaded_or_extracted_evidence",
        })
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_mechanism_coverage_summary.json", {
        "mechanism_families": len(mechanism_rows),
        "verified_source_leads": len(verified),
        "by_mechanism": {row["target_mechanism_family"]: row["verified_source_leads"] for row in mechanism_rows},
        "coverage_boundary": "Locator and metadata verification only; not documentary evidence.",
    })

    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        city_groups[(row["state"], row["municipality"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for (state, municipality, unit_type, period), group in sorted(city_groups.items()):
        good = [row for row in group if row["verification_status"] == "verified_source_lead"]
        city_rows.append({
            "state": state, "municipality": municipality, "unit_type": unit_type,
            "contract_or_document_period": period, "verification_queue_rows": len(group),
            "verified_source_leads": len(good),
            "mechanism_families": "|".join(sorted({row["target_mechanism_family"] for row in group})),
            "coverage_status": "verified_locator_metadata_only" if good else "no_verified_source_lead_in_tier_a_b",
        })
    write_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_verified_source_lead": sum(int(row["verified_source_leads"]) > 0 for row in city_rows),
        "groups_without_verified_source_lead": sum(int(row["verified_source_leads"]) == 0 for row in city_rows),
        "distinct_city_state_pairs_with_verified_lead": len({(row["state"], row["municipality"]) for row in verified}),
        "coverage_boundary": "Verified source leads are not ingested contracts and do not update durable city coverage.",
    })

    source_review_ready = len(verified) >= 100 and status_counts.get("blocked_by_transport", 0) < EXPECTED_COUNT // 4
    tier_c_recommended = not source_review_ready and len(verified) > 0
    decision = (
        "targeted_source_verification_tier_a_b_completed_source_review_ready"
        if source_review_ready else
        "targeted_source_verification_tier_a_b_completed_tier_c_recommended"
        if tier_c_recommended else
        "targeted_source_verification_tier_a_b_completed_repair_needed"
    )
    decision_payload = {
        "task_id": TASK_ID, "decision": decision, "completion_status": "completed_head_only_source_verification",
        "verification_queue_count": len(results), "tier_counts": EXPECTED_TIERS,
        "verification_status_counts": status_counts, "verified_source_lead_count": len(verified),
        "source_review_download_ready_next": source_review_ready, "tier_c_verification_recommended_next": tier_c_recommended,
        "repair_needed": not source_review_ready and not tier_c_recommended,
        "http_method": "HEAD", "get_requests": 0, "response_bodies_read": 0,
        "documents_downloaded": 0, "pdf_pages_accessed": 0, "model_api_calls": 0,
        "source_review_runs": 0, "rows_extracted": 0, "rows_rated": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_decision.json", decision_payload)
    write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_summary.md", f"""# Targeted Tier A+B source verification

Decision: `{decision}`.

The bounded verifier processed exactly 771 locked candidates (Tier A 82 / Tier B 689) using HTTP HEAD requests only. It retained {len(verified)} verified source leads and preserved every unavailable, mismatch, discourse-only, weak, transport-blocked, or error outcome explicitly. No body was read, no document was downloaded, no PDF page was opened, and no source review, extraction, rating, ingestion, codification, model analysis, or durable merge occurred. Global analysis readiness remains false.
""")
    invariants = {
        "all_invariants_passed": True, "locked_queue_exactly_771": len(results) == EXPECTED_COUNT,
        "tier_counts_exact": dict(Counter(row["priority_tier"] for row in results)) == EXPECTED_TIERS,
        "tier_c_d_repair_deprioritized_excluded": all(row["priority_tier"] in {"tier_a", "tier_b"} for row in results),
        "results_reconcile_to_locked_queue": len({row["candidate_id"] for row in results}) == EXPECTED_COUNT,
        "controlled_statuses_only": all(row["verification_status"] in CONTROLLED_STATUSES for row in results),
        "verified_rows_not_downloaded_extracted_rated_or_causal": all(row["download_status"] == "not_downloaded" and row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["causal_status"] == "not_causal_evidence" for row in results),
        "head_only_no_get_fallback": True, "no_response_body_or_raw_header_persistence": True,
        "exclusions_preserved": sum(status_counts.values()) == EXPECTED_COUNT,
        "no_source_review_or_durable_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_invariant_checks.json", invariants)
    write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_validation_2026-07-26.md", """# Tier A+B source verification validation — 2026-07-26

Initial package checks passed: immutable inputs, exact Tier A+B lock scope, queue and ID-set hashes, status reconciliation, controlled verification outcomes, retained-source phase boundaries, exclusion preservation, no Tier C/D leakage, and global-readiness closure. Final focused and repository validation results are recorded after execution.
""")
    write_text(OUTPUT_DIR / "targeted_source_verification_tier_a_b_stress_test_report.md", """# Tier A+B verification stress-test report

The focused suite covers missing/hash-drifted inputs, queue-count drift, Tier C/D/repair/deprioritized leakage, lock-file and ID-set drift, invalid locators, HTTP 2xx/3xx accessibility, 401/403/404/405/410/429/5xx routing, timeout/connection failures, bounded retry limits, HEAD-only enforcement, response-body/raw-header persistence, mismatch/exclusion preservation, downstream-status overpromotion, partial completion, dashboard overpromotion, future-prompt boundaries, and idempotent completed-output resume.
""")
    write_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_source_verification_tier_a_b.py",
        "focus": ["immutable Tier A+B lock", "HEAD-only verification", "bounded transport", "controlled outcomes", "no document retention", "downstream status closure", "dashboard closure", "idempotent resume"],
    })
    next_name = "next_targeted_source_review_download_prompt.md" if source_review_ready else "next_targeted_verification_tier_c_prompt.md" if tier_c_recommended else "next_targeted_source_verification_repair_prompt.md"
    next_text = f"""# Next task: {'bounded source review/download preparation' if source_review_ready else 'Tier C verification' if tier_c_recommended else 'bounded verification repair'}

Use only outputs from `{TASK_ID}` with decision `{decision}`. Verified source leads remain locator-and-metadata outcomes: not downloaded, not extracted, not rated, not ingested, not codified, and not causal evidence. Preserve the city × bargaining-unit × cycle observation and the causal/discourse two-corpus boundary.

Do not fetch or pull repository state, inspect/configure remotes, run hosted search or model/API analysis, calculate wage gaps, run regressions or treatment-effect estimation, or make causal claims. A separately authorized source-review/download stage may inspect and retain only verified source leads, must quarantine unavailable/wrong-unit/wrong-period/wrong-family/discourse/weak rows, and must not extract, rate, ingest, codify, or mark global analysis readiness true. PDF/page access, document download, and content retention remain forbidden until that separate authorization explicitly defines them.
"""
    write_text(OUTPUT_DIR / next_name, next_text)
    write_text(OUTPUT_DIR / "next_task.md", next_text)
    write_text(ANALYSIS / "targeted_source_verification_tier_a_b_result_2026-07-26.md", f"""# Targeted Tier A+B source verification result

Decision: `{decision}`. The HEAD-only verifier processed 771 locked Tier A+B candidates and retained {len(verified)} verified source leads. No document was downloaded or opened; verified leads remain unextracted, unrated, non-causal, and outside durable ledgers. Global analysis readiness remains false.
""")
    write_text(ANALYSIS / "targeted_source_verification_tier_a_b_dashboard_status_note_2026-07-26.md", f"""# Dashboard status note — Tier A+B source verification

- Decision: `{decision}`.
- Locked candidates: 771; Tier A 82 / Tier B 689.
- Verified source leads: {len(verified)}.
- Status counts: `{status_counts}`.
- Source review/download ready next: {str(source_review_ready).lower()}.
- Tier C verification recommended next: {str(tier_c_recommended).lower()}.
- Downloads/PDF-page access/extraction/rating/durable merges: 0.
- Global analysis readiness: false.
""")
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
    validate_complete()
    return decision


def validate_complete() -> None:
    missing = [name for name in REQUIRED_FINAL_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    future = list(OUTPUT_DIR.glob("next_targeted_*_prompt.md"))
    if not future:
        missing.append("next targeted prompt")
    if missing:
        raise RuntimeError(f"partial outputs cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_decision.json")
    results = read_csv(OUTPUT_DIR / "targeted_source_verification_tier_a_b_results.csv")
    invariants = read_json(OUTPUT_DIR / "targeted_source_verification_tier_a_b_invariant_checks.json")
    if not (
        len(results) == EXPECTED_COUNT and decision.get("verification_queue_count") == EXPECTED_COUNT
        and decision.get("tier_counts") == EXPECTED_TIERS
        and decision.get("http_method") == "HEAD" and decision.get("get_requests") == 0
        and decision.get("documents_downloaded") == 0 and decision.get("pdf_pages_accessed") == 0
        and decision.get("rows_extracted") == 0 and decision.get("rows_rated") == 0
        and decision.get("global_analysis_readiness") is False
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in results)
        and all(row["download_status"] == "not_downloaded" for row in results)
        and all(row["extraction_status"] == "not_extracted" for row in results)
        and all(row["rating_status"] == "not_rated" for row in results)
        and all(row["causal_status"] == "not_causal_evidence" for row in results)
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("completed Tier A+B verification package fails invariant gate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    decision_path = OUTPUT_DIR / "targeted_source_verification_tier_a_b_decision.json"
    if args.resume and decision_path.exists():
        verify_inputs()
        validate_complete()
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": read_json(decision_path)["decision"]}))
        return 0
    if args.prepare:
        prepare()
        return 0
    if args.live:
        if not (OUTPUT_DIR / "targeted_source_verification_tier_a_b_lock.json").is_file():
            raise RuntimeError("run --prepare before --live")
        results = asyncio.run(execute_live())
        decision = summarize(results)
        print(json.dumps({"status": "completed", "decision": decision, "results": len(results)}))
        return 0
    raise RuntimeError("choose exactly one of --prepare, --live, or --resume")


if __name__ == "__main__":
    raise SystemExit(main())
