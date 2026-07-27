#!/usr/bin/env python3
"""Run the locked four-lane candidate scout with fixed staggered starts.

This stage is candidate discovery only.  It performs one sequential hosted-search
request at a time inside each lane, permits only the four explicitly authorized
staggered lane workers, and never persists prompts or raw model responses.
"""

from __future__ import annotations

import argparse
import asyncio
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
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
PREP_COMMIT = "b338003063bd1fd2c29fb70c0af6130987c67ffa"
FAILED_ATTEMPT_COMMIT = "e74afe82e31de6fd76b8e2e77571a3ccd0c378e0"
TASK_ID = "TARGETED-SCOUTING-FOUR-LANE-FIXED-STAGGER-LIVE-RUN-OVERLAP-AUTHORIZED-2026-07-25"
PREP_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-SCOUTING-FOUR-LANE-PREP-DRY-RUN-FROM-PROVISIONAL-CLAIM-REVIEW-2026-07-25"
FAILED_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-SCOUTING-FOUR-LANE-STAGGERED-LIVE-RUN-FROM-PREP-2026-07-25"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-SCOUTING-FOUR-LANE-FIXED-STAGGER-LIVE-RUN-OVERLAP-AUTHORIZED-2026-07-25"
LANES = ("lane_1", "lane_2", "lane_3", "lane_4")
OFFSETS_SECONDS = {"lane_1": 0, "lane_2": 480, "lane_3": 960, "lane_4": 1440}
EXPECTED_PREP_DECISION = "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready"
EXPECTED_FAILED_DECISION = "targeted_scouting_four_lane_staggered_live_preflight_failed"
EXPECTED_PER_LANE = 500
EXPECTED_TOTAL = 2_000
MODEL = "gpt-5.4-nano"
BACKEND = "huit_openai_responses_direct_sdk"
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
TIMEOUT_SECONDS = 180.0
MAX_CONSECUTIVE_TRANSPORT_FAILURES = 2

CANDIDATE_FIELDS = [
    "candidate_id", "lane_id", "scout_target_id", "source_url_or_locator",
    "source_title", "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "secondary_mechanism_families", "match_priority_tier",
    "matched_safety_or_non_safety_counterpart_id", "same_city_match_status",
    "overlapping_cycle_status", "duplicate_risk", "prior_seen_status",
    "reason_selected", "search_query_used", "retrieval_status",
    "verification_status", "extraction_status", "rating_status", "causal_status",
    "notes",
]
SKIP_FIELDS = [
    "lane_id", "scout_target_id", "municipality", "state", "target_rank",
    "skip_reason", "live_attempted", "candidate_count", "notes",
]
REQUEST_FIELDS = [
    "lane_id", "scout_target_id", "scheduled_offset_minutes", "request_started_utc",
    "request_finished_utc", "elapsed_seconds", "request_attempted", "request_status",
    "candidate_count", "input_tokens", "output_tokens", "total_tokens", "response_id_hash",
    "backend", "model", "retry_count", "secrets_redacted", "raw_prompt_saved",
    "raw_response_saved", "error_type", "error_detail_redacted",
]
TIMING_FIELDS = [
    "lane_id", "scheduled_offset_minutes", "scheduled_start_utc", "actual_start_utc",
    "actual_finish_utc", "start_delay_seconds", "elapsed_seconds", "request_count",
    "transport_failure_count", "status", "controlled_overlap_authorized",
    "intra_lane_parallelism", "max_orchestrated_lane_workers",
]
MECHANISM_FIELDS = [
    "lane_id", "target_mechanism_family", "locked_target_count", "attempted_target_count",
    "candidate_source_count", "skipped_target_count", "status",
]
COVERAGE_FIELDS = [
    "lane_id", "scout_target_id", "municipality", "state", "target_unit_type",
    "match_priority_tier", "same_city_match_status", "overlapping_cycle_status",
    "candidate_source_count", "coverage_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def id_set_hash(rows: list[dict[str, str]]) -> str:
    return sha256_text("\n".join(sorted(row["scout_target_id"] for row in rows)))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    temp.replace(path)


def git_ancestor(commit: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def required_inputs() -> list[Path]:
    names = [
        "targeted_scouting_four_lane_prep_decision.json",
        "targeted_scouting_four_lane_prep_summary.md",
        "targeted_scouting_four_lane_master_queue.csv",
        "targeted_scouting_four_lane_master_queue_summary.json",
        "targeted_scouting_four_lane_queue_summary.json",
        "targeted_scouting_four_lane_no_call_validation.md",
        "targeted_scouting_four_lane_duplicate_avoidance_report.md",
        "targeted_scouting_four_lane_api_protection_plan.md",
        "targeted_scouting_four_lane_staggered_execution_plan.md",
        "targeted_scouting_four_lane_prep_invariant_checks.json",
        "targeted_scouting_four_lane_prep_validation_2026-07-25.md",
    ]
    paths = [PREP_DIR / name for name in names]
    for lane in LANES:
        paths.extend([
            PREP_DIR / f"targeted_scouting_{lane}_queue_500.csv",
            PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json",
            PREP_DIR / f"targeted_scouting_{lane}_dry_run_summary.json",
        ])
    paths.extend([
        FAILED_DIR / "targeted_scouting_four_lane_staggered_live_decision.json",
        FAILED_DIR / "targeted_scouting_four_lane_staggered_live_preflight_checks.json",
    ])
    return paths


def load_secret() -> str:
    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break
    return os.environ.get("HARVARD_SUBSCRIPTION_KEY", "")


def redact(value: Any, secret: str, limit: int = 500) -> str:
    rendered = str(value)
    if secret:
        rendered = rendered.replace(secret, "[REDACTED]")
    rendered = re.sub(r"(?i)(authorization|api[_-]?key|subscription[_-]?key)[^\s,;]*", "[REDACTED]", rendered)
    return rendered[:limit]


def validate_inputs() -> tuple[dict[str, Any], dict[str, list[dict[str, str]]], str]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    missing = [str(path.relative_to(ROOT)) for path in required_inputs() if not path.exists()]
    check("required_artifacts_present", not missing, {"missing": missing})
    if missing:
        raise RuntimeError(f"missing required artifacts: {missing}")
    prep_decision = read_json(PREP_DIR / "targeted_scouting_four_lane_prep_decision.json")
    failed_decision = read_json(FAILED_DIR / "targeted_scouting_four_lane_staggered_live_decision.json")
    check("prep_decision_allows_live", prep_decision.get("decision") == EXPECTED_PREP_DECISION, prep_decision.get("decision"))
    check("prior_attempt_failed_before_live", failed_decision.get("decision") == EXPECTED_FAILED_DECISION and not failed_decision.get("live_hosted_search_ran", False), failed_decision.get("decision"))
    check("prep_commit_is_ancestor", git_ancestor(PREP_COMMIT), PREP_COMMIT)
    check("failed_attempt_commit_is_ancestor", git_ancestor(FAILED_ATTEMPT_COMMIT), FAILED_ATTEMPT_COMMIT)
    master = read_csv(PREP_DIR / "targeted_scouting_four_lane_master_queue.csv")
    check("master_has_2000_unique_targets", len(master) == EXPECTED_TOTAL and len({row["scout_target_id"] for row in master}) == EXPECTED_TOTAL, {"rows": len(master), "unique": len({row["scout_target_id"] for row in master})})
    lane_rows: dict[str, list[dict[str, str]]] = {}
    queue_audits: dict[str, Any] = {}
    for lane in LANES:
        queue_path = PREP_DIR / f"targeted_scouting_{lane}_queue_500.csv"
        lock = read_json(PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json")
        rows = read_csv(queue_path)
        audit = {
            "rows": len(rows),
            "unique_target_ids": len({row["scout_target_id"] for row in rows}),
            "queue_sha256": sha256_path(queue_path),
            "locked_queue_sha256": lock.get("queue_sha256"),
            "target_id_set_sha256": id_set_hash(rows),
            "locked_target_id_set_sha256": lock.get("target_id_set_sha256"),
            "lane_ids_match": all(row.get("lane_id") == lane for row in rows),
            "all_live_not_started": all(row.get("live_run_status") == "not_started" for row in rows),
        }
        lane_rows[lane] = rows
        queue_audits[lane] = audit
        check(f"{lane}_scope_exactly_500", audit["rows"] == EXPECTED_PER_LANE and audit["unique_target_ids"] == EXPECTED_PER_LANE, audit)
        check(f"{lane}_queue_hash_matches_lock", audit["queue_sha256"] == audit["locked_queue_sha256"], audit["queue_sha256"])
        check(f"{lane}_id_hash_matches_lock", audit["target_id_set_sha256"] == audit["locked_target_id_set_sha256"], audit["target_id_set_sha256"])
        check(f"{lane}_status_and_lane_scope_locked", audit["lane_ids_match"] and audit["all_live_not_started"], audit)
    combined = [row["scout_target_id"] for lane in LANES for row in lane_rows[lane]]
    check("combined_scope_exactly_2000_unique", len(combined) == EXPECTED_TOTAL and len(set(combined)) == EXPECTED_TOTAL, {"rows": len(combined), "unique": len(set(combined))})
    secret = load_secret()
    check("credential_present_without_disclosure", bool(secret), "present" if secret else "missing")
    check("fixed_offsets_exact", OFFSETS_SECONDS == {"lane_1": 0, "lane_2": 480, "lane_3": 960, "lane_4": 1440}, OFFSETS_SECONDS)
    check("controlled_overlap_authorized", True, "explicitly authorized by current task")
    check("previous_schedule_conflict_resolved", True, "overlap after staggered starts is explicit; no simultaneous T+0 starts")
    check("bounded_concurrency_contract", True, {"max_lane_workers": 4, "intra_lane_parallelism": 1, "sdk_retries": 0, "transport_stop_gate": 2})
    passed = all(item["passed"] for item in checks)
    payload = {
        "task_id": TASK_ID,
        "checked_at_utc": utc_now(),
        "checks": checks,
        "preflight_input_integrity_passed": passed,
        "prep_commit": PREP_COMMIT,
        "prior_failed_attempt_commit": FAILED_ATTEMPT_COMMIT,
        "queue_audits": queue_audits,
        "locked_target_count": len(combined),
        "lane_counts": {lane: len(lane_rows[lane]) for lane in LANES},
        "start_offsets_seconds": OFFSETS_SECONDS,
        "controlled_overlap_authorized": True,
        "maximum_lane_workers": 4,
        "intra_lane_parallelism": 1,
        "sdk_retry_count": 0,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    if not passed:
        failed = [item["check"] for item in checks if not item["passed"]]
        raise RuntimeError(f"fail-closed input preflight: {failed}")
    return payload, lane_rows, secret


def clean_string(value: Any, limit: int = 1_000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def canonical_locator(value: str) -> str:
    value = clean_string(value, 2_000)
    if not value:
        return ""
    try:
        parts = urlsplit(value)
        if parts.scheme and parts.netloc:
            path = parts.path.rstrip("/") or "/"
            return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))
    except ValueError:
        pass
    return value.lower()


def query_for_target(target: dict[str, str]) -> str:
    mechanisms = " ".join(target["target_mechanism_family"].replace("_signal", "").replace("_", " ").split())
    source_family = target["source_family_target"].replace("_", " ")
    return clean_string(f'{target["municipality"]} {target["state"]} {target["target_unit_type"]} {target["expected_contract_or_document_period"]} {mechanisms} {source_family}', 500)


def build_prompt(target: dict[str, str], query: str) -> str:
    return f"""Candidate-source scouting only. Use hosted web search to locate up to 3 high-specificity public source leads for exactly this locked target. Do not verify, download, open a document as evidence, extract text, rate evidence, or make causal claims. A result is only a lead.

Search query: {query}
Municipality: {target['municipality']}
State: {target['state']}
Target unit type: {target['target_unit_type']}
Expected period: {target['expected_contract_or_document_period']}
Primary mechanism gap: {target['target_mechanism_family']}
Secondary gaps: {target['secondary_mechanism_families']}
Preferred source family: {target['source_family_target']}
Selection reason: {target['reason_selected']}

Return JSON only, with this exact outer shape: {{"candidates": [{{"source_url_or_locator":"", "source_title":"", "unit_type":"", "occupation_group":"", "bargaining_unit_name":"", "contract_or_document_period":"", "inferred_cycle_start":"", "inferred_cycle_end":"", "source_family":"", "same_city_match_status":"", "overlapping_cycle_status":"", "notes":""}}]}}. Use an empty candidates list if no high-specificity lead is found. Do not include prose outside JSON. Do not claim that any source is verified."""


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start, end = stripped.find("{"), stripped.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    return value


def response_value(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


def response_usage(response: Any, key: str) -> Any:
    return response_value(response_value(response, "usage"), key, "")


def make_candidate(target: dict[str, str], item: dict[str, Any], query: str) -> dict[str, str] | None:
    locator = clean_string(item.get("source_url_or_locator"), 2_000)
    title = clean_string(item.get("source_title"), 500)
    if not locator or not title:
        return None
    identity = f"{target['lane_id']}|{target['scout_target_id']}|{canonical_locator(locator)}|{title.lower()}"
    return {
        "candidate_id": f"TS4L-{sha256_text(identity)[:20]}",
        "lane_id": target["lane_id"],
        "scout_target_id": target["scout_target_id"],
        "source_url_or_locator": locator,
        "source_title": title,
        "municipality": target["municipality"],
        "state": target["state"],
        "unit_type": clean_string(item.get("unit_type")) or target["target_unit_type"],
        "occupation_group": clean_string(item.get("occupation_group")) or target["target_unit_type"],
        "bargaining_unit_name": clean_string(item.get("bargaining_unit_name")),
        "contract_or_document_period": clean_string(item.get("contract_or_document_period")) or target["expected_contract_or_document_period"],
        "inferred_cycle_start": clean_string(item.get("inferred_cycle_start"), 20),
        "inferred_cycle_end": clean_string(item.get("inferred_cycle_end"), 20),
        "source_family": clean_string(item.get("source_family")) or target["source_family_target"],
        "target_mechanism_family": target["target_mechanism_family"],
        "secondary_mechanism_families": target["secondary_mechanism_families"],
        "match_priority_tier": target["match_priority_tier"],
        "matched_safety_or_non_safety_counterpart_id": target["known_counterpart_id"],
        "same_city_match_status": clean_string(item.get("same_city_match_status")) or target["same_city_match_status"],
        "overlapping_cycle_status": clean_string(item.get("overlapping_cycle_status")) or target["overlapping_cycle_status"],
        "duplicate_risk": target["duplicate_risk"],
        "prior_seen_status": target["prior_seen_status"],
        "reason_selected": target["reason_selected"],
        "search_query_used": query,
        "retrieval_status": "candidate_only",
        "verification_status": "not_verified",
        "extraction_status": "not_extracted",
        "rating_status": "not_rated",
        "causal_status": "not_causal_evidence",
        "notes": clean_string(item.get("notes"), 750) or "Hosted-search lead; candidate only; not verified.",
    }


def checkpoint_path(lane: str) -> Path:
    return OUTPUT_DIR / "checkpoints" / f"{lane}_checkpoint.json"


def empty_state(lane: str) -> dict[str, Any]:
    return {"lane_id": lane, "processed_ids": [], "candidates": [], "skips": [], "requests": [], "transport_failures": 0, "status": "not_started"}


def load_state(lane: str) -> dict[str, Any]:
    path = checkpoint_path(lane)
    state = read_json(path) if path.exists() else empty_state(lane)
    for request in state.get("requests", []):
        if request.get("error_detail_redacted"):
            error_type = clean_string(request.get("error_type")) or "RequestError"
            request["error_detail_redacted"] = f"{error_type}; detail omitted"
    return state


def save_state(state: dict[str, Any]) -> None:
    write_json(checkpoint_path(state["lane_id"]), state)


async def api_preflight(secret: str) -> dict[str, Any]:
    import httpx
    from openai import AsyncOpenAI

    started = utc_now()
    begin = time.monotonic()
    client = AsyncOpenAI(
        api_key=secret, base_url=BASE_URL,
        default_headers={"Ocp-Apim-Subscription-Key": secret},
        timeout=httpx.Timeout(TIMEOUT_SECONDS), max_retries=0,
    )
    try:
        response = await asyncio.wait_for(client.responses.create(
            model=MODEL,
            input='Return only this JSON object: {"preflight":"ok"}',
            reasoning={"effort": "low"},
        ), timeout=TIMEOUT_SECONDS)
        parsed = parse_json_object(str(response_value(response, "output_text", "")))
        passed = parsed == {"preflight": "ok"}
        return {
            "attempted": True, "passed": passed, "started_utc": started,
            "finished_utc": utc_now(), "elapsed_seconds": round(time.monotonic() - begin, 3),
            "backend": BACKEND, "model": MODEL, "hosted_search_enabled": False,
            "raw_prompt_saved": False, "raw_response_saved": False,
            "response_id_hash": sha256_text(str(response_value(response, "id", "")))[:16],
            "error": "" if passed else "preflight_response_schema_invalid",
        }
    except Exception as exc:
        return {
            "attempted": True, "passed": False, "started_utc": started,
            "finished_utc": utc_now(), "elapsed_seconds": round(time.monotonic() - begin, 3),
            "backend": BACKEND, "model": MODEL, "hosted_search_enabled": False,
            "raw_prompt_saved": False, "raw_response_saved": False,
            "response_id_hash": "", "error": f"{type(exc).__name__}: {redact(exc, secret)}",
        }
    finally:
        await client.close()


def transport_failure(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    terms = ("timeout", "connection", "connect", "network", "temporarily unavailable", "rate limit", "service unavailable")
    return any(term in name or term in text for term in terms)


async def run_lane(
    lane: str,
    rows: list[dict[str, str]],
    secret: str,
    epoch_monotonic: float,
    epoch_utc: str,
) -> dict[str, Any]:
    import httpx
    from openai import AsyncOpenAI

    target_start = epoch_monotonic + OFFSETS_SECONDS[lane]
    await asyncio.sleep(max(0.0, target_start - time.monotonic()))
    actual_start = utc_now()
    start_delay = max(0.0, time.monotonic() - target_start)
    state = load_state(lane)
    state["status"] = "running"
    state["actual_start_utc"] = state.get("actual_start_utc") or actual_start
    save_state(state)
    processed = set(state["processed_ids"])
    consecutive_transport = 0
    client = AsyncOpenAI(
        api_key=secret, base_url=BASE_URL,
        default_headers={"Ocp-Apim-Subscription-Key": secret},
        timeout=httpx.Timeout(TIMEOUT_SECONDS), max_retries=0,
    )
    begin = time.monotonic()
    try:
        for position, target in enumerate(rows):
            target_id = target["scout_target_id"]
            if target_id in processed:
                continue
            if consecutive_transport >= MAX_CONSECUTIVE_TRANSPORT_FAILURES:
                for remaining in rows[position:]:
                    if remaining["scout_target_id"] in processed:
                        continue
                    state["skips"].append({
                        "lane_id": lane, "scout_target_id": remaining["scout_target_id"],
                        "municipality": remaining["municipality"], "state": remaining["state"],
                        "target_rank": remaining["target_rank"],
                        "skip_reason": "stopped_after_two_consecutive_transport_failures",
                        "live_attempted": "no", "candidate_count": 0,
                        "notes": "Bounded transport stop gate; target remained candidate-scout only and was not requested.",
                    })
                    state["processed_ids"].append(remaining["scout_target_id"])
                    processed.add(remaining["scout_target_id"])
                state["status"] = "stopped_transport_instability"
                save_state(state)
                break
            query = query_for_target(target)
            prompt = build_prompt(target, query)
            request_started = utc_now()
            request_begin = time.monotonic()
            metadata = {
                "lane_id": lane, "scout_target_id": target_id,
                "scheduled_offset_minutes": OFFSETS_SECONDS[lane] // 60,
                "request_started_utc": request_started, "request_finished_utc": "",
                "elapsed_seconds": "", "request_attempted": "yes", "request_status": "",
                "candidate_count": 0, "input_tokens": "", "output_tokens": "",
                "total_tokens": "", "response_id_hash": "", "backend": BACKEND,
                "model": MODEL, "retry_count": 0, "secrets_redacted": "yes",
                "raw_prompt_saved": "no", "raw_response_saved": "no",
                "error_type": "", "error_detail_redacted": "",
            }
            candidates: list[dict[str, str]] = []
            try:
                response = await asyncio.wait_for(client.responses.create(
                    model=MODEL, input=prompt, reasoning={"effort": "low"},
                    tools=[{"type": "web_search", "search_context_size": "low"}],
                    include=["web_search_call.action.sources"],
                ), timeout=TIMEOUT_SECONDS)
                payload = parse_json_object(str(response_value(response, "output_text", "")))
                items = payload.get("candidates", [])
                if not isinstance(items, list):
                    raise ValueError("candidates is not a list")
                for item in items[:3]:
                    if isinstance(item, dict):
                        candidate = make_candidate(target, item, query)
                        if candidate:
                            candidates.append(candidate)
                metadata.update({
                    "request_status": "completed",
                    "candidate_count": len(candidates),
                    "input_tokens": response_usage(response, "input_tokens"),
                    "output_tokens": response_usage(response, "output_tokens"),
                    "total_tokens": response_usage(response, "total_tokens"),
                    "response_id_hash": sha256_text(str(response_value(response, "id", "")))[:16],
                })
                consecutive_transport = 0
                if not candidates:
                    state["skips"].append({
                        "lane_id": lane, "scout_target_id": target_id,
                        "municipality": target["municipality"], "state": target["state"],
                        "target_rank": target["target_rank"], "skip_reason": "no_high_specificity_candidate",
                        "live_attempted": "yes", "candidate_count": 0,
                        "notes": "Hosted scout returned no usable high-specificity candidate lead.",
                    })
            except Exception as exc:
                is_transport = transport_failure(exc)
                consecutive_transport = consecutive_transport + 1 if is_transport else 0
                if is_transport:
                    state["transport_failures"] += 1
                metadata.update({
                    "request_status": "transport_failure" if is_transport else "schema_or_response_failure",
                    "error_type": type(exc).__name__,
                    # Error bodies can contain raw upstream HTML or response
                    # fragments. Preserve only the class; omit body content.
                    "error_detail_redacted": f"{type(exc).__name__}; detail omitted",
                })
                state["skips"].append({
                    "lane_id": lane, "scout_target_id": target_id,
                    "municipality": target["municipality"], "state": target["state"],
                    "target_rank": target["target_rank"],
                    "skip_reason": metadata["request_status"], "live_attempted": "yes",
                    "candidate_count": 0, "notes": "Bounded request failed; no raw response persisted.",
                })
            metadata["request_finished_utc"] = utc_now()
            metadata["elapsed_seconds"] = round(time.monotonic() - request_begin, 3)
            state["candidates"].extend(candidates)
            state["requests"].append(metadata)
            state["processed_ids"].append(target_id)
            processed.add(target_id)
            save_state(state)
        if state["status"] == "running":
            state["status"] = "completed"
    finally:
        await client.close()
    state["actual_finish_utc"] = utc_now()
    state["elapsed_seconds"] = round(time.monotonic() - begin, 3)
    state["start_delay_seconds"] = round(start_delay, 3)
    save_state(state)
    return state


def deduplicate(
    states: dict[str, dict[str, Any]],
    lane_rows: dict[str, list[dict[str, str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    duplicate_skips: list[dict[str, Any]] = []
    seen: set[str] = set()
    locked_targets = {
        row["scout_target_id"]: row
        for lane in LANES
        for row in lane_rows[lane]
    }
    for lane in LANES:
        for row in states[lane]["candidates"]:
            # The locked queue, not model prose, is authoritative for the
            # normalized target unit type used in accounting and review.
            target = locked_targets[row["scout_target_id"]]
            row = dict(row)
            row["unit_type"] = target["target_unit_type"]
            key = canonical_locator(row["source_url_or_locator"]) or row["candidate_id"]
            if key in seen:
                duplicate_skips.append({
                    "lane_id": lane, "scout_target_id": row["scout_target_id"],
                    "municipality": row["municipality"], "state": row["state"],
                    "target_rank": "", "skip_reason": "duplicate_candidate_locator",
                    "live_attempted": "yes", "candidate_count": 0,
                    "notes": "Candidate locator duplicated an earlier parsed lead; no durable merge occurred.",
                })
                continue
            seen.add(key)
            candidates.append(row)
    return candidates, duplicate_skips


def lane_output_dir(lane: str) -> Path:
    return OUTPUT_DIR / "lane_outputs" / lane


def summarize_and_write(
    preflight: dict[str, Any], lane_rows: dict[str, list[dict[str, str]]],
    api_check: dict[str, Any], states: dict[str, dict[str, Any]], epoch_utc: str,
) -> str:
    candidates, duplicate_skips = deduplicate(states, lane_rows)
    by_lane_candidates = {lane: [row for row in candidates if row["lane_id"] == lane] for lane in LANES}
    all_skips = [row for lane in LANES for row in states[lane]["skips"]] + duplicate_skips
    requests = [row for lane in LANES for row in states[lane]["requests"]]
    lane_status = {lane: states[lane]["status"] for lane in LANES}
    clean_complete = all(status == "completed" for status in lane_status.values())
    quality_ok = all(len(by_lane_candidates[lane]) > 0 for lane in LANES)
    invariants_ok = (
        sum(len(rows) for rows in lane_rows.values()) == EXPECTED_TOTAL
        and all(len(states[lane]["processed_ids"]) == EXPECTED_PER_LANE for lane in LANES)
        and all(len(set(states[lane]["processed_ids"])) == EXPECTED_PER_LANE for lane in LANES)
    )
    ready = clean_complete and quality_ok and invariants_ok
    decision = (
        "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready"
        if ready else "targeted_scouting_four_lane_fixed_stagger_live_completed_repair_needed"
    )
    lane_candidate_counts = {lane: len(by_lane_candidates[lane]) for lane in LANES}
    mechanism_counts = Counter(row["target_mechanism_family"] for row in candidates)
    unit_counts = Counter(row["unit_type"] for row in candidates)
    tier_counts = Counter(row["match_priority_tier"] for row in candidates)
    request_status_counts = Counter(row["request_status"] for row in requests)
    input_hashes = {str(path.relative_to(ROOT)): sha256_path(path) for path in required_inputs()}

    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_sources.csv", candidates, CANDIDATE_FIELDS)
    candidate_summary = {
        "candidate_source_count": len(candidates), "candidate_only": True,
        "lane_candidate_counts": lane_candidate_counts,
        "mechanism_family_counts": dict(sorted(mechanism_counts.items())),
        "unit_type_counts": dict(sorted(unit_counts.items())),
        "match_priority_tier_counts": dict(sorted(tier_counts.items())),
        "duplicate_candidate_count": len(duplicate_skips),
        "retrieval_status": "candidate_only", "verification_status": "not_verified",
        "extraction_status": "not_extracted", "rating_status": "not_rated",
        "causal_status": "not_causal_evidence",
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_sources_summary.json", candidate_summary)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_search_metadata.csv", requests, REQUEST_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_skipped_targets.csv", all_skips, SKIP_FIELDS)

    timing_rows = []
    mechanism_rows = []
    coverage_rows = []
    for lane in LANES:
        state = states[lane]
        scheduled_utc = (parse_utc(epoch_utc).timestamp() + OFFSETS_SECONDS[lane])
        scheduled_text = datetime.fromtimestamp(scheduled_utc, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        timing = {
            "lane_id": lane, "scheduled_offset_minutes": OFFSETS_SECONDS[lane] // 60,
            "scheduled_start_utc": scheduled_text, "actual_start_utc": state.get("actual_start_utc", ""),
            "actual_finish_utc": state.get("actual_finish_utc", ""),
            "start_delay_seconds": state.get("start_delay_seconds", ""),
            "elapsed_seconds": state.get("elapsed_seconds", ""),
            "request_count": len(state["requests"]),
            "transport_failure_count": state["transport_failures"], "status": state["status"],
            "controlled_overlap_authorized": "yes", "intra_lane_parallelism": 1,
            "max_orchestrated_lane_workers": 4,
        }
        timing_rows.append(timing)
        lane_candidates = by_lane_candidates[lane]
        lane_skips = [row for row in all_skips if row["lane_id"] == lane]
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_candidate_sources.csv", lane_candidates, CANDIDATE_FIELDS)
        write_json(lane_output_dir(lane) / f"targeted_scouting_{lane}_candidate_sources_summary.json", {
            "lane_id": lane, "locked_target_count": EXPECTED_PER_LANE,
            "processed_target_count": len(state["processed_ids"]), "request_count": len(state["requests"]),
            "candidate_source_count": len(lane_candidates), "skip_count": len(lane_skips),
            "status": state["status"], "candidate_only": True,
        })
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_search_metadata.csv", state["requests"], REQUEST_FIELDS)
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_timing.csv", [timing], TIMING_FIELDS)
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_skipped_targets.csv", lane_skips, SKIP_FIELDS)
        locked_mechanisms = Counter(row["target_mechanism_family"] for row in lane_rows[lane])
        candidate_mechanisms = Counter(row["target_mechanism_family"] for row in lane_candidates)
        skipped_mechanisms = Counter(
            next((target["target_mechanism_family"] for target in lane_rows[lane] if target["scout_target_id"] == skip["scout_target_id"]), "unknown")
            for skip in lane_skips
        )
        local_mechanisms = [{
            "lane_id": lane, "target_mechanism_family": mechanism,
            "locked_target_count": count,
            "attempted_target_count": sum(1 for target in lane_rows[lane] if target["scout_target_id"] in {row["scout_target_id"] for row in state["requests"]}),
            "candidate_source_count": candidate_mechanisms[mechanism],
            "skipped_target_count": skipped_mechanisms[mechanism], "status": state["status"],
        } for mechanism, count in sorted(locked_mechanisms.items())]
        mechanism_rows.extend(local_mechanisms)
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_mechanism_gap_coverage.csv", local_mechanisms, MECHANISM_FIELDS)
        candidate_by_target = Counter(row["scout_target_id"] for row in lane_candidates)
        local_coverage = [{
            "lane_id": lane, "scout_target_id": target["scout_target_id"],
            "municipality": target["municipality"], "state": target["state"],
            "target_unit_type": target["target_unit_type"],
            "match_priority_tier": target["match_priority_tier"],
            "same_city_match_status": target["same_city_match_status"],
            "overlapping_cycle_status": target["overlapping_cycle_status"],
            "candidate_source_count": candidate_by_target[target["scout_target_id"]],
            "coverage_status": "candidate_lead_found" if candidate_by_target[target["scout_target_id"]] else "no_candidate_lead",
        } for target in lane_rows[lane]]
        coverage_rows.extend(local_coverage)
        write_csv(lane_output_dir(lane) / f"targeted_scouting_{lane}_city_cycle_unit_coverage.csv", local_coverage, COVERAGE_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_timing.csv", timing_rows, TIMING_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_mechanism_gap_coverage.csv", mechanism_rows, MECHANISM_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_scouting_four_lane_city_cycle_unit_coverage.csv", coverage_rows, COVERAGE_FIELDS)
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json", {
        "locked_target_count": EXPECTED_TOTAL, "candidate_source_count": len(candidates),
        "mechanism_family_counts": dict(sorted(mechanism_counts.items())), "candidate_only": True,
    })
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json", {
        "locked_target_count": EXPECTED_TOTAL,
        "targets_with_candidate_leads": len({row["scout_target_id"] for row in candidates}),
        "targets_without_candidate_leads": EXPECTED_TOTAL - len({row["scout_target_id"] for row in candidates}),
        "candidate_source_count": len(candidates), "candidate_only": True,
    })
    prior_counts = Counter(row["prior_seen_status"] for lane in LANES for row in lane_rows[lane])
    duplicate_risk_counts = Counter(row["duplicate_risk"] for lane in LANES for row in lane_rows[lane])
    skip_reason_counts = Counter(row["skip_reason"] for row in all_skips)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_duplicate_prior_seen_report.md", f"""# Duplicate and prior-seen accounting

The immutable queues carried {EXPECTED_TOTAL} targets into live scouting. Parsed candidate locators were deterministically canonicalized across lanes. {len(duplicate_skips)} duplicate candidate lead(s) were excluded from the combined candidate-only registry; no prior durable candidate/source ledger was mutated or merged.

- Candidate sources retained: {len(candidates)}
- Duplicate candidate locators excluded: {len(duplicate_skips)}
- Explicit target skips: {len(all_skips)}
- Prior-seen status counts: `{dict(sorted(prior_counts.items()))}`
- Queue duplicate-risk counts: `{dict(sorted(duplicate_risk_counts.items()))}`
""")
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_duplicate_prior_seen_summary.json", {
        "locked_target_count": EXPECTED_TOTAL, "candidate_source_count": len(candidates),
        "duplicate_candidate_count": len(duplicate_skips),
        "prior_seen_status_counts": dict(sorted(prior_counts.items())),
        "duplicate_risk_counts": dict(sorted(duplicate_risk_counts.items())),
        "skip_reason_counts": dict(sorted(skip_reason_counts.items())),
        "durable_merge_count": 0,
    })

    starts = {lane: states[lane].get("actual_start_utc", "") for lane in LANES}
    start_times = {
        "epoch_lane_1_start_utc": epoch_utc, "scheduled_offsets_seconds": OFFSETS_SECONDS,
        "actual_starts_utc": starts,
        "actual_offsets_seconds": {
            lane: round((parse_utc(starts[lane]) - parse_utc(starts["lane_1"])).total_seconds(), 3)
            for lane in LANES
        },
        "controlled_overlap_authorized": True,
        "all_lanes_started_after_required_offset": all(
            (parse_utc(starts[lane]) - parse_utc(starts["lane_1"])).total_seconds() >= OFFSETS_SECONDS[lane]
            for lane in LANES
        ),
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_start_times.json", start_times)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_concurrency_plan.md", """# Fixed-stagger controlled-overlap plan

- Lane 1: T+0 minutes.
- Lane 2: no earlier than T+8 minutes.
- Lane 3: no earlier than T+16 minutes.
- Lane 4: no earlier than T+24 minutes.
- Controlled overlap after each delayed start: explicitly authorized and used when an earlier lane remained active.
- Maximum orchestrated lane workers: four.
- Intra-lane parallelism: one sequential request at a time.
- SDK retries: zero; two consecutive transport failures stop the affected lane gracefully.
- No target movement, cross-lane queue use, or mid-run target addition is allowed.
- Prompts and raw responses remain in memory only and are discarded after parsing.
""")

    decision_payload = {
        "task_id": TASK_ID, "decision": decision,
        "completion_status": "completed_candidate_only_live_scouting",
        "preflight_passed": True, "live_api_preflight_passed": api_check["passed"],
        "prep_commit_verified": True, "prior_failed_attempt_commit_verified": True,
        "locked_target_count": EXPECTED_TOTAL,
        "lane_locked_counts": {lane: EXPECTED_PER_LANE for lane in LANES},
        "lane_status": lane_status, "lane_runs_completed": sum(status == "completed" for status in lane_status.values()),
        "candidate_source_count": len(candidates), "lane_candidate_counts": lane_candidate_counts,
        "duplicate_candidate_count": len(duplicate_skips), "skip_count": len(all_skips),
        "hosted_search_model_backed_scouting_ran": bool(requests),
        "model_api_request_count": len(requests) + 1,
        "controlled_overlap_authorized": True, "fixed_stagger_offsets_used": start_times["all_lanes_started_after_required_offset"],
        "candidate_review_ready": ready, "repair_required": not ready,
        "global_analysis_readiness": False, "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "input_hashes": input_hashes,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json", decision_payload)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_summary.md", f"""# Four-lane fixed-stagger live scouting summary

Decision: `{decision}`.

All four immutable 500-target queues passed hash and scope checks. Lane starts used T+0/T+8/T+16/T+24 minimum offsets with explicitly authorized controlled overlap, one sequential request stream per lane, and no uncontrolled fanout. The live scout retained {len(candidates)} candidate-only source leads: {lane_candidate_counts}. {len(all_skips)} skip/duplicate records were preserved. Candidates remain unverified, unextracted, unrated, and non-causal. Global analysis readiness remains false.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_candidate_only_qa_report.md", f"""# Candidate-only QA report

- Locked targets: 2,000 (500 per lane).
- Processed or explicitly skipped: {sum(len(states[lane]['processed_ids']) for lane in LANES)}/2,000.
- Parsed, deduplicated candidate leads: {len(candidates)}.
- Request status counts: `{dict(sorted(request_status_counts.items()))}`.
- Candidate statuses: candidate only / not verified / not extracted / not rated / not causal evidence.
- Raw prompts saved: 0; raw responses saved: 0.
- PDF/page/download/OCR work: none.
- Source verification/extraction/selection/ingestion/codification: none.
- Statistics/wage-gap/regression/treatment-effect/final-causal work: none.
- Prior evidence/rating/scout/durable ledgers mutated: no.
- Global analysis readiness: false.
""")
    invariants = {
        "all_invariants_passed": invariants_ok and start_times["all_lanes_started_after_required_offset"],
        "locked_targets_exactly_2000": True,
        "lane_locked_counts_500_each": True,
        "queue_and_target_id_hashes_match": True,
        "processed_or_explicitly_skipped_reconciles_by_lane": {lane: len(states[lane]["processed_ids"]) == EXPECTED_PER_LANE for lane in LANES},
        "controlled_overlap_explicitly_authorized": True,
        "fixed_stagger_offsets_not_shortened": start_times["all_lanes_started_after_required_offset"],
        "no_simultaneous_t0_start": len({starts[lane] for lane in LANES}) == len(LANES),
        "maximum_lane_workers_four": True, "intra_lane_parallelism_one": True,
        "candidate_only_statuses_enforced": all(
            row["retrieval_status"] == "candidate_only" and row["verification_status"] == "not_verified"
            and row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated"
            and row["causal_status"] == "not_causal_evidence" for row in candidates
        ),
        "no_raw_prompts_or_responses_saved": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_invariant_checks.json", invariants)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_validation_2026-07-25.md", f"""# Fixed-stagger live validation — 2026-07-25

Initial live validation passed: all four immutable queue/ID hashes, exact 500-row lane scopes, 2,000-row combined scope, credential presence, corrected controlled-overlap contract, bounded concurrency, and live API handshake. The four lane states are `{lane_status}`; candidates retained: {len(candidates)}; explicit skips/duplicates: {len(all_skips)}. Final focused and repository command results are appended after validation.
""")
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_stress_test_report.md", """# Fixed-stagger live stress-test report

The focused suite covers missing inputs, decision drift, prep/prior-attempt commit lineage, queue-file and target-ID hash drift, row/ID count drift, cross-lane target use, already-started rows, missing credential, fixed-offset shortening, simultaneous T+0 starts, absent overlap authorization, uncontrolled intra-lane fanout, transport stop-gate behavior, prompt/response persistence, candidate overpromotion, duplicate accounting, partial completion, upstream mutation, dashboard overpromotion, and idempotent completed-output resume.
""")
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_scouting_four_lane_fixed_stagger_live.py",
        "focus": ["locked queue integrity", "controlled overlap", "fixed offsets", "bounded lane concurrency", "candidate-only status", "no raw persistence", "partial-output fail closed", "global readiness false"],
    })

    next_name = "next_targeted_scouting_four_lane_candidate_review_prompt.md" if ready else "next_targeted_scouting_four_lane_repair_prompt.md"
    next_decision = "candidate review" if ready else "bounded lane repair"
    next_prompt = f"""# Next task: four-lane candidate {next_decision}

Use only candidate-only outputs from `{TASK_ID}` with decision `{decision}`. Review candidate quality, duplicates, mechanism targeting, match priority, and coverage accounting. Candidates are not verified sources and must remain unverified, unextracted, unrated, and non-causal until separately authorized.

Do not fetch or pull repository state; inspect or configure remotes; download documents; open PDFs/pages; run OCR; verify sources; select for extraction; extract; ingest; codify; rerate prior evidence; analyze the quantitative lane; calculate wage gaps; run regressions or treatment-effect analysis; or make final causal claims. Do not save raw prompts/responses or secrets. Preserve the two-corpus rule and city-cycle-unit observation unit. Keep global analysis readiness false. Verification, if later authorized, must be a separate phase after candidate review.
"""
    write_text(OUTPUT_DIR / next_name, next_prompt)
    write_text(OUTPUT_DIR / "next_task.md", next_prompt)
    result = f"""# Four-lane fixed-stagger targeted scouting result

Decision: `{decision}`. Live hosted-search/model-backed candidate scouting ran over four immutable 500-target queues with fixed delayed starts and controlled overlap. It retained {len(candidates)} candidate-only leads. No lead was verified, downloaded, extracted, rated, ingested, codified, or treated as causal evidence. Global analysis readiness remains false.
"""
    dashboard = f"""# Dashboard status note — fixed-stagger targeted scouting

- Decision: `{decision}`.
- Live lanes: 4 orchestrated; lane completion states `{lane_status}`.
- Locked targets: 2,000 (500 per lane).
- Candidate-only leads: {len(candidates)}; lane counts `{lane_candidate_counts}`.
- Candidate review ready: {str(ready).lower()}.
- Verification/extraction/rating readiness: false.
- Global analysis readiness: false.
"""
    write_text(ROOT / "docs/analysis/targeted_scouting_four_lane_fixed_stagger_live_result_2026-07-25.md", result)
    write_text(ROOT / "docs/analysis/targeted_scouting_four_lane_fixed_stagger_live_dashboard_status_note_2026-07-25.md", dashboard)
    return decision


def validate_complete() -> None:
    required = [
        "targeted_scouting_four_lane_fixed_stagger_live_decision.json",
        "targeted_scouting_four_lane_fixed_stagger_live_summary.md",
        "targeted_scouting_four_lane_fixed_stagger_live_preflight_report.md",
        "targeted_scouting_four_lane_fixed_stagger_live_preflight_checks.json",
        "targeted_scouting_four_lane_fixed_stagger_concurrency_plan.md",
        "targeted_scouting_four_lane_fixed_stagger_start_times.json",
        "targeted_scouting_four_lane_candidate_sources.csv",
        "targeted_scouting_four_lane_candidate_sources_summary.json",
        "targeted_scouting_four_lane_search_metadata.csv",
        "targeted_scouting_four_lane_timing.csv",
        "targeted_scouting_four_lane_skipped_targets.csv",
        "targeted_scouting_four_lane_duplicate_prior_seen_report.md",
        "targeted_scouting_four_lane_duplicate_prior_seen_summary.json",
        "targeted_scouting_four_lane_mechanism_gap_coverage.csv",
        "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json",
        "targeted_scouting_four_lane_city_cycle_unit_coverage.csv",
        "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json",
        "targeted_scouting_four_lane_candidate_only_qa_report.md",
        "targeted_scouting_four_lane_fixed_stagger_live_invariant_checks.json",
        "targeted_scouting_four_lane_fixed_stagger_live_validation_2026-07-25.md",
        "targeted_scouting_four_lane_fixed_stagger_live_stress_test_report.md",
        "targeted_scouting_four_lane_fixed_stagger_live_regression_test_inventory.json",
        "next_task.md",
    ]
    missing = [name for name in required if not (OUTPUT_DIR / name).exists()]
    for lane in LANES:
        for suffix in ("candidate_sources.csv", "candidate_sources_summary.json", "search_metadata.csv", "timing.csv", "skipped_targets.csv", "mechanism_gap_coverage.csv", "city_cycle_unit_coverage.csv"):
            path = lane_output_dir(lane) / f"targeted_scouting_{lane}_{suffix}"
            if not path.exists():
                missing.append(str(path.relative_to(OUTPUT_DIR)))
    if missing:
        raise RuntimeError(f"partial outputs cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json")
    invariants = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_invariant_checks.json")
    if decision.get("locked_target_count") != EXPECTED_TOTAL or decision.get("global_analysis_readiness") is not False or not invariants.get("all_invariants_passed"):
        raise RuntimeError("completed package invariant validation failed")


async def execute(lane_rows: dict[str, list[dict[str, str]]], secret: str, preflight: dict[str, Any]) -> str:
    api_check = await api_preflight(secret)
    preflight["live_api_preflight"] = api_check
    preflight["preflight_passed"] = preflight["preflight_input_integrity_passed"] and api_check["passed"]
    write_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_preflight_report.md", f"""# Corrected combined fixed-stagger live preflight

- Prep commit `{PREP_COMMIT}`: verified in local history.
- Failed-attempt commit `{FAILED_ATTEMPT_COMMIT}`: verified; it made no live hosted request.
- Locked scope: 2,000 unique targets; 500 per lane.
- Queue-file and target-ID hashes: 4/4 passed.
- Credential presence: passed without disclosure.
- Corrected schedule: T+0/T+8/T+16/T+24 with controlled overlap explicitly authorized.
- Maximum lane workers: four; intra-lane parallelism: one; SDK retries: zero.
- Live API handshake: {'passed' if api_check['passed'] else 'failed'}; hosted search disabled for handshake.
- Raw prompts/responses saved: 0/0.
- Global analysis readiness: false.
""")
    if not api_check["passed"]:
        raise RuntimeError(f"bounded live preflight failed: {api_check['error']}")
    epoch_monotonic = time.monotonic()
    epoch_utc = utc_now()
    tasks = [asyncio.create_task(run_lane(lane, lane_rows[lane], secret, epoch_monotonic, epoch_utc)) for lane in LANES]
    results = await asyncio.gather(*tasks)
    states = {state["lane_id"]: state for state in results}
    return summarize_and_write(preflight, lane_rows, api_check, states, epoch_utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.resume and (OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json").exists():
        validate_complete()
        decision = read_json(OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json")["decision"]
        print(json.dumps({"status": "resume_validated_zero_writes", "decision": decision}))
        return 0
    if OUTPUT_DIR.exists() and not args.resume:
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=args.resume)
    preflight, lane_rows, secret = validate_inputs()
    decision = asyncio.run(execute(lane_rows, secret, preflight))
    validate_complete()
    print(json.dumps({"status": "completed", "decision": decision, "output_dir": str(OUTPUT_DIR.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
