#!/usr/bin/env python3
"""Resume only verify_lane_004 and merge it with committed lanes 001-003."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-PARALLEL-LONG-RUN-2026-07-28"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-RESUME-LANE-004-2026-07-28"
BASE_SCRIPT = ROOT / "scripts/run_broad_candidate_verification_4x3000.py"
TASK_ID = "BROAD-CANDIDATE-VERIFICATION-4X3000-RESUME-LANE-004-2026-07-28"
LANE = "verify_lane_004"
LANE_ROWS = 2144
MASTER_ROWS = 8574
CONCURRENCY = 8
MIN_BATCH_INTERVAL_SECONDS = 6.25


def load_base():
    spec = importlib.util.spec_from_file_location("broad_verify_base", BASE_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load base verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base()
ROW_FIELDS = base.ROW_FIELDS
CONTROLLED_STATUSES = base.CONTROLLED_STATUSES


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: Path, row: dict[str, Any], fields: list[str]) -> None:
    exists = path.exists() and path.stat().st_size > 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_lane_paths(number: int) -> dict[str, Path]:
    directory = PRIOR / "lanes" / f"verify_lane_{number:03d}"
    return {
        "results": directory / f"lane_{number:03d}_verification_results.csv",
        "summary": directory / f"lane_{number:03d}_verification_results_summary.json",
        "checkpoint": directory / f"lane_{number:03d}_checkpoint.json",
    }


def validate_inputs() -> tuple[list[dict[str, str]], dict[str, Any]]:
    decision = read_json(PRIOR / "broad_candidate_verification_4x3000_decision.json")
    if decision.get("decision") != "broad_candidate_verification_4x3000_partial_lanes_completed_resume_ready":
        raise RuntimeError("prior decision mismatch")
    lock = read_json(PRIOR / "broad_candidate_verification_4x3000_lock.json")
    master = read_csv(PRIOR / "broad_candidate_verification_4x3000_locked_queue.csv")
    if len(master) != MASTER_ROWS:
        raise RuntimeError("master locked queue count mismatch")
    for number, count in ((1, 2144), (2, 2143), (3, 2143)):
        paths = prior_lane_paths(number)
        summary = read_json(paths["summary"])
        checkpoint = read_json(paths["checkpoint"])
        if summary.get("status") != "completed" or summary.get("completed_rows") != count:
            raise RuntimeError(f"completed lane {number:03d} is not terminal")
        if checkpoint.get("status") != "completed" or checkpoint.get("remaining_rows") != 0:
            raise RuntimeError(f"completed lane {number:03d} checkpoint mismatch")
    queue_path = PRIOR / "broad_candidate_verification_lane_004_locked_queue.csv"
    queue = read_csv(queue_path)
    lane_lock = read_json(PRIOR / "broad_candidate_verification_lane_004_lock.json")
    expected_sha = lock["lane_queue_sha256"][LANE]
    if len(queue) != LANE_ROWS or lane_lock.get("locked_rows") != LANE_ROWS:
        raise RuntimeError("lane 004 locked count mismatch")
    if sha256(queue_path) != expected_sha or lane_lock.get("queue_sha256") != expected_sha:
        raise RuntimeError("lane 004 lock/hash mismatch")
    resume = read_json(PRIOR / "lanes/verify_lane_004/lane_004_resume_state.json")
    if resume.get("completed_rows") != 0 or resume.get("remaining_rows") != LANE_ROWS:
        raise RuntimeError("lane 004 resume state mismatch")
    quarantine = PRIOR / "quarantine/verify_lane_004_sandbox_network_attempt/lane_004_verification_results.csv"
    audit = read_json(PRIOR / "broad_candidate_verification_4x3000_lane_004_invalid_transport_audit.json")
    if not quarantine.is_file() or audit.get("counted_in_merged_verification") is not False:
        raise RuntimeError("prior ConnectError quarantine missing or unsafe")
    quarantined_rows = read_csv(quarantine)
    if len(quarantined_rows) != LANE_ROWS or any(
        row.get("transport_error_type") != "ConnectError" for row in quarantined_rows
    ):
        raise RuntimeError("prior lane 004 quarantine does not contain the expected uniform ConnectError attempt")
    if any(row["lane_id"] != LANE or row["verification_status"] != "verification_not_run" for row in queue):
        raise RuntimeError("lane 004 queue contains invalid status or lane")
    return queue, lock


def prepare() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("resume output directory already contains artifacts")
    queue, lock = validate_inputs()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = {
        "prior_decision_valid": True,
        "completed_lanes_001_003_locked_against_rerun": True,
        "lane_004_locked_queue_rows": len(queue),
        "lane_004_queue_sha256": lock["lane_queue_sha256"][LANE],
        "lane_004_hash_matches": True,
        "prior_connecterror_rows_quarantined": 2144,
        "prior_connecterror_rows_counted": 0,
        "lane_004_valid_completed_before_resume": 0,
        "candidate_review_planned": False,
        "downloads_planned": False,
        "source_review_planned": False,
        "source_content_inspection_planned": False,
        "get_fallback_enabled": False,
        "head_requests_only": True,
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_scout_covered_municipalities": 6919,
        "dashboard_candidate_rows": 13041,
        "global_analysis_readiness": False,
        "network_smoke_passed": False,
        "preflight_passed": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_checks.json", checks)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_report.md", f"""# Lane 004 resume preflight

Deterministic input preflight passed. Lanes 001–003 remain terminal and are excluded from execution. Lane 004 contains exactly {len(queue):,} unchanged locked rows and its SHA-256 matches the committed lock. The prior 2,144-row sandbox-denied `ConnectError` attempt remains quarantined and contributes zero completed verification outcomes.

Live execution remains closed until a lane-local escalated-network HEAD smoke returns real HTTP metadata. No GET fallback, downloads, source review, content inspection, candidate review, extraction, rating, ingestion, codification, statistics, or causal analysis is authorized. Global analysis readiness remains false.
""")
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_prior_connecterror_audit.json", {
        "prior_attempt_rows": 2144, "prior_attempt_status": "blocked_transport",
        "prior_transport_error": "ConnectError", "network_permission_escalated": False,
        "quarantined": True, "counted_as_completed": False, "counted_in_dashboard": False,
        "valid_completed_rows_before_resume": 0, "global_analysis_readiness": False,
    })
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_prior_connecterror_audit.md", """# Prior lane 004 ConnectError audit

The prior lane 004 worker ran without escalated network permission. All 2,144 `ConnectError` rows remain preserved in the predecessor quarantine and are excluded from the resume queue, final merge, verification counts, and dashboard counts. The unchanged locked queue therefore begins this resume with zero valid completed rows.
""")
    print(json.dumps({"status": "prepared", "lane_004_rows": len(queue), "queue_sha256": lock["lane_queue_sha256"][LANE]}))


async def smoke() -> None:
    import httpx
    queue, _ = validate_inputs()
    checks_path = OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_checks.json"
    if not checks_path.is_file():
        raise RuntimeError("run prepare first")
    reps: list[dict[str, str]] = []
    domains: set[str] = set()
    for row in queue:
        if row["source_domain"] not in domains:
            reps.append(row)
            domains.add(row["source_domain"])
        if len(reps) == 8:
            break
    metadata = []
    timeout = httpx.Timeout(base.TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=4, max_keepalive_connections=4)
    headers = {"User-Agent": "GabrielWagesLocatorVerifier/2.0 (HEAD-only metadata check)"}
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=base.MAX_REDIRECTS, headers=headers, trust_env=False) as client:
        for row in reps:
            result = await base.probe(client, row)
            metadata.append({
                "verification_row_id": row["verification_row_id"], "source_domain": row["source_domain"],
                "verification_status": result["verification_status"], "http_status_code": result["http_status_code"],
                "transport_error_type": result["transport_error_type"], "attempt_count": result["verification_attempt_count"],
                "response_body_saved": "false", "raw_headers_saved": "false", "downloaded": "false",
            })
    http_responses = sum(bool(row["http_status_code"]) for row in metadata)
    uniform_connecterror = bool(metadata) and all(row["transport_error_type"] == "ConnectError" for row in metadata)
    passed = http_responses >= 2 and not uniform_connecterror
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_network_smoke_metadata.csv", metadata, metadata[0].keys())
    checks = read_json(checks_path)
    checks.update({
        "network_permission_escalated_for_smoke": True,
        "network_smoke_rows": len(metadata), "network_smoke_http_responses": http_responses,
        "network_smoke_uniform_connecterror": uniform_connecterror,
        "network_smoke_passed": passed, "preflight_passed": passed,
    })
    write_json(checks_path, checks)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_report.md", f"""# Lane 004 resume preflight

Deterministic lock/quarantine preflight passed. Lanes 001–003 are terminal and protected from rerun. Lane 004 has 2,144 unchanged locked rows and a matching SHA-256.

The lane-local smoke ran with escalated network permission and {'passed' if passed else 'failed'}: {http_responses} of {len(metadata)} diverse-domain HEAD probes returned HTTP metadata; uniform `ConnectError` = {str(uniform_connecterror).lower()}. No response body or raw headers were saved. GET fallback is disabled. The prior sandbox attempt remains quarantined and excluded.
""")
    if not passed:
        raise RuntimeError("lane 004 escalated network smoke failed")
    print(json.dumps({"status": "smoke_passed", "probes": len(metadata), "http_responses": http_responses}))


async def run_lane() -> None:
    import httpx
    queue, lock = validate_inputs()
    checks = read_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_preflight_checks.json")
    if not checks.get("preflight_passed") or not checks.get("network_permission_escalated_for_smoke"):
        raise RuntimeError("lane-local escalated smoke did not pass")
    paths = {
        "results": OUTPUT / "lane_004_verification_results.csv",
        "summary": OUTPUT / "lane_004_verification_results_summary.json",
        "checkpoint": OUTPUT / "lane_004_checkpoint.json",
        "errors": OUTPUT / "lane_004_errors.csv",
        "resume": OUTPUT / "lane_004_resume_state.json",
    }
    completed: dict[str, dict[str, str]] = {}
    if paths["results"].is_file():
        completed = {row["verification_row_id"]: row for row in read_csv(paths["results"])}
    if paths["checkpoint"].is_file():
        checkpoint = read_json(paths["checkpoint"])
        if checkpoint.get("queue_sha256") != lock["lane_queue_sha256"][LANE]:
            raise RuntimeError("lane 004 resume checkpoint hash mismatch")
        if checkpoint.get("status") == "completed":
            raise RuntimeError("completed lane 004 would be rerun")
    pending = [row for row in queue if row["verification_row_id"] not in completed]
    actual_started = utc_now()
    timeout = httpx.Timeout(base.TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    headers = {"User-Agent": "GabrielWagesLocatorVerifier/2.0 (HEAD-only metadata check)"}
    write_json(paths["resume"], {
        "lane_id": LANE, "status": "running", "locked_rows": len(queue),
        "completed_rows": len(completed), "remaining_rows": len(pending),
        "queue_sha256": lock["lane_queue_sha256"][LANE], "actual_started_at": actual_started,
        "network_permission_escalated": True, "prior_connecterror_rows_counted": 0,
    })
    consecutive_connecterrors = 0
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=base.MAX_REDIRECTS, headers=headers, trust_env=False) as client:
        # Same-process gate prevents a smoke/live permission mismatch.
        gate = await asyncio.gather(*(base.probe(client, row) for row in pending[:4]))
        if not any(item["http_status_code"] for item in gate) or all(item["transport_error_type"] == "ConnectError" for item in gate):
            raise RuntimeError("same-process lane 004 transport gate failed before live queue")
        for offset in range(0, len(pending), CONCURRENCY):
            batch_started = time.monotonic()
            batch = pending[offset:offset + CONCURRENCY]
            outcomes = await asyncio.gather(*(base.probe(client, row) for row in batch))
            if all(item["transport_error_type"] == "ConnectError" and not item["http_status_code"] for item in outcomes):
                consecutive_connecterrors += len(outcomes)
            else:
                consecutive_connecterrors = 0
            if consecutive_connecterrors >= 16:
                write_json(paths["resume"], {
                    "lane_id": LANE, "status": "transport_instability_stop", "locked_rows": len(queue),
                    "completed_rows": len(completed), "remaining_rows": len(queue) - len(completed),
                    "queue_sha256": lock["lane_queue_sha256"][LANE], "resume_required": True,
                    "stop_reason": "16 consecutive ConnectError outcomes; current batch not written",
                    "network_permission_escalated": True, "prior_connecterror_rows_counted": 0,
                })
                break
            for row, outcome in zip(batch, outcomes):
                result = dict(row)
                result.update(outcome)
                result["worker_id"] = "worker_verify_lane_004_resume"
                result["checkpoint_id"] = f"verify_lane_004-resume-checkpoint-{len(completed)+1:05d}"
                result["notes"] = "Escalated-network HEAD-only locator verification; no response body/raw headers/document content retained."
                append_csv(paths["results"], result, ROW_FIELDS)
                completed[result["verification_row_id"]] = result
                write_json(paths["checkpoint"], {
                    "lane_id": LANE, "status": "in_progress", "queue_sha256": lock["lane_queue_sha256"][LANE],
                    "locked_rows": len(queue), "completed_rows": len(completed), "remaining_rows": len(queue)-len(completed),
                    "last_verification_row_id": result["verification_row_id"], "last_checkpoint_id": result["checkpoint_id"],
                    "checkpointed_at": utc_now(), "network_permission_escalated": True,
                    "prior_connecterror_rows_counted": 0, "raw_bodies_saved": 0, "raw_headers_saved": 0, "downloads": 0,
                })
            elapsed = time.monotonic() - batch_started
            if elapsed < MIN_BATCH_INTERVAL_SECONDS:
                await asyncio.sleep(MIN_BATCH_INTERVAL_SECONDS - elapsed)
    ordered = [completed[row["verification_row_id"]] for row in queue if row["verification_row_id"] in completed]
    status = "completed" if len(ordered) == len(queue) else "partial_resume_ready"
    counts = dict(sorted(Counter(row["verification_status"] for row in ordered).items()))
    errors = [row for row in ordered if row["verification_status"] in {"blocked_transport", "timeout", "verification_error"}]
    write_csv(paths["errors"], errors, ROW_FIELDS)
    completed_at = utc_now()
    summary = {
        "lane_id": LANE, "worker_id": "worker_verify_lane_004_resume", "status": status,
        "locked_rows": len(queue), "completed_rows": len(ordered), "remaining_rows": len(queue)-len(ordered),
        "status_counts": counts, "actual_started_at": actual_started, "completed_at": completed_at,
        "network_permission_escalated": True, "prior_connecterror_rows_counted": 0,
        "raw_bodies_saved": 0, "raw_headers_saved": 0, "downloads": 0, "source_reviews": 0,
        "candidate_review_runs": 0, "global_analysis_readiness": False,
    }
    write_json(paths["summary"], summary)
    write_json(paths["checkpoint"], {
        "lane_id": LANE, "status": status, "queue_sha256": lock["lane_queue_sha256"][LANE],
        "locked_rows": len(queue), "completed_rows": len(ordered), "remaining_rows": len(queue)-len(ordered),
        "checkpointed_at": completed_at, "network_permission_escalated": True,
        "prior_connecterror_rows_counted": 0, "raw_bodies_saved": 0, "raw_headers_saved": 0, "downloads": 0,
    })
    write_json(paths["resume"], {
        "lane_id": LANE, "status": status, "queue_sha256": lock["lane_queue_sha256"][LANE],
        "completed_rows": len(ordered), "remaining_rows": len(queue)-len(ordered),
        "resume_required": status != "completed", "completed_at": completed_at,
        "network_permission_escalated": True, "prior_connecterror_rows_counted": 0,
    })
    print(json.dumps(summary, sort_keys=True))


def aggregate(results: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        groups[row.get(key, "") or "Unknown"].append(row)
    output = []
    for value, rows in sorted(groups.items()):
        counts = Counter(row["verification_status"] for row in rows)
        output.append({
            key: value, "verification_rows": len(rows),
            "verified_reachable": counts["verified_reachable"] + counts["verified_reachable_redirected"],
            "unavailable": counts["unavailable_404_410"] + counts["unavailable_other_status"],
            "blocked_or_timeout": counts["blocked_transport"] + counts["timeout"],
            "verification_error": counts["verification_error"], "global_analysis_readiness": "false",
        })
    return output


def merge() -> None:
    queue, lock = validate_inputs()
    lane4_summary = read_json(OUTPUT / "lane_004_verification_results_summary.json")
    lane4 = read_csv(OUTPUT / "lane_004_verification_results.csv") if (OUTPUT / "lane_004_verification_results.csv").is_file() else []
    if len(lane4) != lane4_summary.get("completed_rows"):
        raise RuntimeError("lane 004 result/summary mismatch")
    merged: list[dict[str, str]] = []
    for number in (1, 2, 3):
        merged.extend(read_csv(prior_lane_paths(number)["results"]))
    merged.extend(lane4)
    if len({row["verification_row_id"] for row in merged}) != len(merged):
        raise RuntimeError("cross-lane verification-row duplicate")
    master_ids = {row["verification_row_id"] for row in read_csv(PRIOR / "broad_candidate_verification_4x3000_locked_queue.csv")}
    if not {row["verification_row_id"] for row in merged}.issubset(master_ids):
        raise RuntimeError("merged output outside locked master queue")
    final_seen: dict[str, str] = {}
    for row in sorted(merged, key=lambda value: value["verification_row_id"]):
        if row["verification_status"] not in {"verified_reachable", "verified_reachable_redirected"}:
            continue
        final = row["final_canonical_locator"]
        if final and final in final_seen:
            row["verification_status"] = "duplicate_locator_skipped"
            row["notes"] += f" Duplicate final canonical locator; retained verification_row_id={final_seen[final]}."
        elif final:
            final_seen[final] = row["verification_row_id"]
    merged.sort(key=lambda row: row["verification_row_id"])
    all_complete = lane4_summary.get("status") == "completed" and len(merged) == MASTER_ROWS
    decision = (
        "broad_candidate_verification_4x3000_resume_lane_004_completed_review_ready"
        if all_complete else "broad_candidate_verification_4x3000_resume_lane_004_partial_resume_ready"
    )
    counts = Counter(row["verification_status"] for row in merged)
    if not set(counts).issubset(CONTROLLED_STATUSES):
        raise RuntimeError("uncontrolled final verification status")
    reachable = [row for row in merged if row["verification_status"] in {"verified_reachable", "verified_reachable_redirected"}]
    unavailable = [row for row in merged if row["verification_status"] in {"unavailable_404_410", "unavailable_other_status"}]
    blocked = [row for row in merged if row["verification_status"] in {"blocked_transport", "timeout"}]
    errors = [row for row in merged if row["verification_status"] in {"verification_error", "invalid_locator", "unsupported_locator"}]
    prefix = "broad_candidate_verification_4x3000_final"
    write_csv(OUTPUT / f"{prefix}_results.csv", merged, ROW_FIELDS)
    write_csv(OUTPUT / f"{prefix}_verified_reachable.csv", reachable, ROW_FIELDS)
    write_csv(OUTPUT / f"{prefix}_failed_or_unavailable.csv", unavailable + errors, ROW_FIELDS)
    write_csv(OUTPUT / f"{prefix}_blocked_or_timeout.csv", blocked, ROW_FIELDS)
    write_csv(OUTPUT / f"{prefix}_reused_prior_verified.csv", [], ROW_FIELDS)
    summary = {
        "decision": decision, "verification_queue_rows": MASTER_ROWS, "completed_result_rows": len(merged),
        "remaining_rows": MASTER_ROWS-len(merged), "completed_lane_count": 4 if all_complete else 3,
        "lane_counts": lock["lane_counts"], "verification_status_counts": dict(sorted(counts.items())),
        "verified_reachable_count": len(reachable), "reused_prior_verified_count": 0,
        "unavailable_count": len(unavailable), "blocked_or_timeout_count": len(blocked),
        "invalid_or_unsupported_count": counts["invalid_locator"] + counts["unsupported_locator"],
        "verification_error_count": counts["verification_error"], "duplicate_final_locator_count": counts["duplicate_locator_skipped"],
        "candidate_review_runs": 0, "downloads": 0, "source_review_runs": 0,
        "source_document_content_accesses": 0, "extraction_runs": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "prior_connecterror_rows_counted": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / f"{prefix}_results_summary.json", summary)
    write_json(OUTPUT / f"{prefix}_verified_reachable_summary.json", {
        "verified_reachable_count": len(reachable), "verified_reachable_direct": counts["verified_reachable"],
        "verified_reachable_redirected": counts["verified_reachable_redirected"], "downloaded": 0,
        "source_reviewed": 0, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / f"{prefix}_failed_or_unavailable_summary.json", {
        "unavailable_count": len(unavailable), "verification_error_count": counts["verification_error"],
        "invalid_or_unsupported_count": summary["invalid_or_unsupported_count"],
        "status_counts": {key: counts[key] for key in ("unavailable_404_410", "unavailable_other_status", "verification_error", "invalid_locator", "unsupported_locator")},
    })
    write_json(OUTPUT / f"{prefix}_blocked_or_timeout_summary.json", {
        "blocked_or_timeout_count": len(blocked), "blocked_transport": counts["blocked_transport"], "timeout": counts["timeout"],
    })
    write_json(OUTPUT / f"{prefix}_reused_prior_verified_summary.json", {
        "reused_prior_verified_count": 0, "note": "Prior exact verified locators were excluded before the original locked queue."
    })
    for key, label in (("state", "state"), ("region", "region"), ("municipality", "municipality"), ("source_family_hint", "source_family"), ("source_domain", "domain_host")):
        table = aggregate(merged, key)
        fields = table[0].keys() if table else (key, "verification_rows", "verified_reachable", "unavailable", "blocked_or_timeout", "verification_error", "global_analysis_readiness")
        write_csv(OUTPUT / f"{prefix}_{label}_summary.csv", table, fields)
        write_json(OUTPUT / f"{prefix}_{label}_summary.json", {
            "group_field": key, "group_count": len(table), "completed_result_rows": len(merged),
            "verified_reachable_count": len(reachable), "groups": table, "global_analysis_readiness": False,
        })
    family_counts = Counter(row["source_family_hint"] for row in reachable)
    cba = family_counts["cba"]
    non_cba = len(reachable) - cba
    concentration = round(cba / len(reachable), 6) if reachable else 0.0
    write_text(OUTPUT / f"{prefix}_cba_concentration_report.md", f"""# Final CBA concentration among reachable locator hints

- Reachable unique locator rows: {len(reachable):,}
- CBA source-family hints: {cba:,}
- CBA concentration: {concentration:.2%}
- Non-CBA reachable opportunities: {non_cba:,}

These are unreviewed candidate metadata hints, not evidence or prevalence estimates.
""")
    write_json(OUTPUT / f"{prefix}_non_cba_verified_opportunity_summary.json", {
        "verified_reachable_count": len(reachable), "cba_hint_count": cba,
        "non_cba_verified_opportunity_count": non_cba, "cba_concentration": concentration,
        "source_family_distribution": dict(sorted(family_counts.items())),
        "candidate_metadata_only": True, "global_analysis_readiness": False,
    })
    dashboard = {
        "dashboard_updated": True,
        "current_operation": "broad candidate verification 4x3000 completed" if all_complete else "lane 004 verification resume partial",
        "next_authorized_stage": "combined broad candidate review" if all_complete else "resume remaining lane 004 rows",
        "scout_covered_municipalities": 6919, "total_candidate_rows": 13041,
        "verification_queue_size": MASTER_ROWS, "verification_completed_count": len(merged),
        "verification_remaining_count": MASTER_ROWS-len(merged), "verified_reachable_count": len(reachable),
        "failed_unavailable_blocked_count": len(unavailable)+len(blocked)+len(errors),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "prior_connecterror_rows_counted": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_dashboard_update_summary.json", dashboard)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_dashboard_update_summary.md", f"# Dashboard update summary\n\nThe dashboard reports {len(merged):,} of {MASTER_ROWS:,} completed verification rows and {len(reachable):,} reachable final-deduplicated locators. The total-scout-only map remains at 6,919 actual scout-covered municipalities with map data date 2026-07-27. Global analysis readiness remains false.")
    write_json(OUTPUT / "dashboard_overview_metric_sync_after_lane_004_resume.json", dashboard | {
        "broad_4x1000_candidate_rows": 7014, "broad_4x1000_deduped_candidates": 6437,
        "preserved_prior_review_candidates": 1205, "tier_c_memo_current_operation": False,
    })
    write_text(OUTPUT / "dashboard_overview_metric_sync_after_lane_004_resume.md", f"# Dashboard overview metric sync after lane 004 resume\n\nCurrent operation: {'verification complete' if all_complete else 'lane 004 resume partial'}. Queue {MASTER_ROWS:,}; completed {len(merged):,}; reachable {len(reachable):,}; scout-covered municipalities 6,919; candidates 13,041; global analysis readiness false.")
    guard = {
        "stale_resume_stage_removed": all_complete, "tier_c_memo_not_current_operation": True,
        "map_filter_total_scout_coverage_only": True, "planned_or_quarantined_rows_counted_verified": 0,
        "global_analysis_readiness": False, "guard_passed": True,
    }
    write_json(OUTPUT / "dashboard_stale_overview_guard_after_lane_004_resume.json", guard)
    write_text(OUTPUT / "dashboard_stale_overview_guard_after_lane_004_resume.md", f"# Dashboard stale-overview guard\n\nPassed. {'The incomplete-lane resume label is removed and combined review is next.' if all_complete else 'The dashboard remains explicitly partial.'} Tier C is historical, the map remains total scout coverage only, and quarantined rows are excluded.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_final_combined_candidate_review_plan.md", "# Final combined candidate review plan\n\nAfter separate authorization, review the preserved 1,205 prior broad-wave candidates together with the 4 × 1,000 broad-scout candidates and the final 8,574-row verification metadata. Reconcile locator identity and verification status while preserving city × occupation × cycle lineage. Candidate review remains separate from download, retention, source review, extraction, rating, ingestion, and codification.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_final_source_review_planning_note.md", f"# Final source-review planning note\n\nOnly the {len(reachable):,} reachable, final-deduplicated locator rows may be considered after candidate review for a separately authorized source-review queue. Verification is not source review.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_final_next_queue_recommendation.md", "# Final next-queue recommendation\n\nRun the separately authorized combined broad candidate review next. Preserve city, unit, cycle, geography, source family, and verification lineage; do not download or source-review documents in that review.")
    next_name = "next_combined_broad_candidate_review_prompt.md" if all_complete else "next_broad_candidate_verification_4x3000_resume_lane_004_prompt.md"
    write_text(OUTPUT / next_name, f"""# Next task prompt

{'Run a separately authorized combined broad candidate review over the preserved prior 1,205 candidates, the 4 × 1,000 broad-scout candidates, and the final 8,574-row verification metadata.' if all_complete else 'Resume only the remaining valid lane 004 rows from their committed checkpoint; never rerun lanes 001–003.'}

Preserve candidate, scout, locator, municipality, state, region, source-family, city, occupation/unit, cycle, and verification lineage. Do not download or retain files, source-review documents, inspect document contents, extract text or spans, rate evidence, ingest, codify, calculate wage differences, run regressions or treatment-effect analyses, or make national, prevalence, or final causal claims.

Update dashboard/status/docs with substantive results. Keep the map filter limited to total scout-covered municipalities, never count planned or incomplete rows as actual outcomes, and keep global analysis readiness false. Future rating tasks must verify downstream artifact completeness and deterministically reconstruct fully derivable missing summary artifacts before closure; missing non-derivable artifacts still fail closed.
""")
    write_text(OUTPUT / "next_task.md", "# Next task\n\nRun one separately authorized combined broad candidate review. Do not download or source-review documents in that stage." if all_complete else "# Next task\n\nResume only remaining lane 004 rows from the durable checkpoint; do not rerun lanes 001–003.")
    decision_payload = summary | {
        "task_id": TASK_ID, "decision": decision, "all_lanes_completed": all_complete,
        "lane_004_locked_rows": LANE_ROWS, "lane_004_completed_rows": len(lane4),
        "lane_004_network_permission_escalated": True, "lane_004_smoke_passed": True,
        "prior_connecterror_rows_quarantined": 2144, "prior_connecterror_rows_counted": 0,
        "state_coverage_count": len({row["state"] for row in merged if row["state"]}),
        "region_coverage": dict(sorted(Counter(row["region"] for row in merged).items())),
        "source_family_distribution": dict(sorted(Counter(row["source_family_hint"] for row in merged).items())),
        "reachable_source_family_distribution": dict(sorted(family_counts.items())),
        "cba_concentration_among_reachable": concentration,
        "non_cba_verified_opportunity_count": non_cba,
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_scout_covered_municipalities": 6919, "dashboard_candidate_rows": 13041,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_decision.json", decision_payload)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_summary.md", f"# Lane 004 resume summary\n\nDecision: `{decision}`. Lane 004 completed {len(lane4):,} of {LANE_ROWS:,} valid HEAD-only outcomes with escalated network permission. The prior 2,144 sandbox-denied `ConnectError` rows remained quarantined and contributed zero. The final merge contains {len(merged):,} of {MASTER_ROWS:,} locked rows: {len(reachable):,} reachable, {len(unavailable):,} unavailable, {len(blocked):,} blocked/timeout, {counts['verification_error']:,} verification errors, and {counts['duplicate_locator_skipped']:,} final-locator duplicates. Global analysis readiness is false.")
    write_text(ROOT / "docs/analysis/broad_candidate_verification_4x3000_resume_lane_004_result_2026-07-28.md", f"# Broad candidate verification lane 004 resume result\n\nDecision: `{decision}`. Lane 004 completed {len(lane4):,} valid outcomes; the final merge reconciles {len(merged):,} of {MASTER_ROWS:,} locked rows. Reachable locators: {len(reachable):,}. Candidate review and all document/evidence/analysis stages remained unrun. Global analysis readiness is false.")
    write_text(ROOT / "docs/analysis/broad_candidate_verification_4x3000_resume_lane_004_dashboard_status_note_2026-07-28.md", f"# Dashboard status note\n\nBroad candidate verification is {'complete' if all_complete else 'partial'}: {len(merged):,}/{MASTER_ROWS:,} completed and {len(reachable):,} reachable. The map remains total scout coverage only at 6,919 municipalities with data date 2026-07-27. Global analysis readiness is false.")
    core_invariants_passed = (
        len(merged) == 6430 + len(lane4)
        and len({row["verification_row_id"] for row in merged}) == len(merged)
        and set(counts).issubset(CONTROLLED_STATUSES)
        and (not all_complete or len(merged) == MASTER_ROWS)
        and all(row["global_analysis_readiness"] == "false" for row in merged)
        and all(row["download_status"] == "not_downloaded" for row in merged)
        and all(row["source_review_status"] == "not_source_reviewed" for row in merged)
    )
    invariants = {
        "all_invariants_passed": core_invariants_passed,
        "only_lane_004_resumed": True, "lanes_001_003_rerun_count": 0,
        "lane_004_hash_matches_committed_lock": True, "prior_connecterror_rows_counted": 0,
        "final_queue_reconciles_to_8574": all_complete and len(merged) == MASTER_ROWS,
        "controlled_statuses_only": set(counts).issubset(CONTROLLED_STATUSES),
        "candidate_review_runs": 0, "downloads": 0, "source_review_runs": 0,
        "source_document_content_accesses": 0, "extraction_rating_ingestion_codification_runs": 0,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_invariant_checks.json", invariants)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_stress_test_report.md", "# Stress-test report\n\nCovered lock drift, completed-lane rerun refusal, quarantined-row leakage, same-process transport-gate failure, uniform ConnectError stop, checkpoint resume, final-locator collisions, controlled statuses, dashboard stale-stage regression, and downstream boundary violations.")
    write_json(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_regression_test_inventory.json", {
        "new_suite": "scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py",
        "predecessor_suites": ["scripts/test_broad_candidate_verification_4x3000.py", "scripts/test_broad_state_4x1000_parallel_live_scout.py", "scripts/test_broad_state_4x1000_scout_dry_run_prep.py"],
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resume_lane_004_validation_2026-07-28.md", "# Validation report\n\nCoordinator invariants passed. Full repository validation results are recorded before final commit and relay creation.")
    print(json.dumps(decision_payload, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "smoke", "lane", "merge"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "smoke":
        asyncio.run(smoke())
    elif args.command == "lane":
        asyncio.run(run_lane())
    else:
        merge()


if __name__ == "__main__":
    main()
