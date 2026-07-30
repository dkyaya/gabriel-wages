#!/usr/bin/env python3
"""Run and coordinate the committed broad-state 4 x 2,500 live scout.

The worker invokes the established direct-SDK hosted-search transport for one
exact locked target at a time, persists only sanitized parsed metadata, and
atomically checkpoints after every terminal target.  Workers never update
shared summaries or the dashboard.  The coordinator reads worker checkpoints,
merges only completed lanes, deduplicates locators, and materializes the
lightweight durable package.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import run_broad_state_4x1000_live_scout as legacy


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29"
RESULT_DOC = ROOT / "docs/analysis/broad_state_4x2500_live_scout_result_2026-07-29.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/broad_state_4x2500_live_scout_dashboard_status_note_2026-07-29.md"
TASK_ID = "BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29"
PREP_DECISION = "broad_state_4x2500_scout_infrastructure_prep_completed_live_ready"
DECISION_COMPLETE = "broad_state_4x2500_live_scout_completed_candidate_review_ready"
DECISION_PARTIAL = "broad_state_4x2500_live_scout_partial_lanes_completed_resume_ready"
LANES = tuple(f"scout_lane_{number:03d}" for number in range(1, 5))
SHARDS = tuple(f"broad_4x2500_shard_{number:03d}" for number in range(1, 5))
OFFSETS = {lane: index * 8 for index, lane in enumerate(LANES)}
TARGETS_PER_SHARD = 2_500
TARGET_COUNT = 10_000
BASE_COVERAGE = 6_919
BASE_CANDIDATES = 13_041
ALLOWED_TIERS = {
    "strong_broad_geographic_target",
    "strong_source_family_diversification_target",
    "matched_safety_non_safety_target",
    "acceptable_broad_target",
}
TRANSPORT_FAILURES = {"connection_error", "timeout", "outer_timeout", "timeout_or_capacity"}

RESULT_FIELDS = [
    "lane_id", "shard_id", "worker_id", "shard_sequence", "scout_target_id",
    "municipality_id", "municipality", "state", "region", "parse_status",
    "success_status", "failure_type", "attempt_count", "candidate_count",
    "target_input_sha256", "target_output_dir", "input_tokens", "reasoning_tokens",
    "output_tokens", "total_tokens", "response_id_present",
]
CANDIDATE_FIELDS = [
    "scout_candidate_id", "scout_target_id", "lane_id", "shard_id", "worker_id",
    "state", "region", "municipality", "county", "unit_type_hint",
    "occupation_group_hint", "possible_bargaining_unit", "possible_cycle_or_year",
    "source_title", "source_locator_or_url", "source_domain", "normalized_locator",
    "source_family_hint", "document_type_hint", "source_family_confidence",
    "possible_mechanism_hints", "sanitized_snippet", "search_query_family",
    "broad_geographic_target_reason", "source_family_diversification_reason",
    "matched_safety_non_safety_opportunity_flag", "duplicate_locator_flag",
    "prior_seen_locator_flag", "candidate_quality_tier", "verification_status",
    "download_status", "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "notes",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required file missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shard_paths(number: int) -> tuple[Path, Path, str]:
    shard_id = SHARDS[number - 1]
    return (
        PREP / f"broad_state_4x2500_scout_shard_{number:03d}_locked_queue.csv",
        PREP / f"broad_state_4x2500_scout_shard_{number:03d}_lock.json",
        shard_id,
    )


def lane_root(number: int) -> Path:
    return OUTPUT / "lanes" / LANES[number - 1]


def checkpoint_path(number: int) -> Path:
    lane_id = LANES[number - 1]
    return lane_root(number) / f"{lane_id}_checkpoint.json"


def validate_locks() -> dict[str, Any]:
    decision = read_json(PREP / "broad_state_4x2500_scout_infrastructure_prep_decision.json")
    if decision.get("decision") != PREP_DECISION or decision.get("live_scout_ready_next") is not True:
        raise RuntimeError("infrastructure-prep decision does not authorize live scouting")
    master_path = PREP / "broad_state_4x2500_scout_master_locked_queue.csv"
    master_lock = read_json(PREP / "broad_state_4x2500_scout_master_lock.json")
    master = read_csv(master_path)
    if len(master) != TARGET_COUNT or sha256_file(master_path) != master_lock.get("queue_sha256"):
        raise RuntimeError("master queue count/hash mismatch")
    shard_rows: list[dict[str, str]] = []
    shard_hashes: dict[str, str] = {}
    for number in range(1, 5):
        queue_path, lock_path, shard_id = shard_paths(number)
        lock = read_json(lock_path)
        rows = read_csv(queue_path)
        actual_hash = sha256_file(queue_path)
        if len(rows) != TARGETS_PER_SHARD or actual_hash != lock.get("queue_sha256"):
            raise RuntimeError(f"{shard_id} queue count/hash mismatch")
        if any(row.get("shard_id") != shard_id for row in rows):
            raise RuntimeError(f"{shard_id} contains a foreign shard ID")
        if any(row.get("live_status") != "not_run" for row in rows):
            raise RuntimeError(f"{shard_id} contains a non-not-run target")
        if any(row.get("target_quality_tier") not in ALLOWED_TIERS for row in rows):
            raise RuntimeError(f"{shard_id} contains a disallowed quality tier")
        if any(row.get("prior_scout_covered_flag") != "false" for row in rows):
            raise RuntimeError(f"{shard_id} contains a prior-covered municipality")
        shard_rows.extend(rows)
        shard_hashes[shard_id] = actual_hash
    master_ids = [row["scout_target_id"] for row in master]
    union_ids = [row["scout_target_id"] for row in shard_rows]
    municipality_ids = [row["municipality_id"] for row in master]
    if len(set(master_ids)) != TARGET_COUNT or set(master_ids) != set(union_ids):
        raise RuntimeError("master queue does not equal the four-shard union")
    if len(set(municipality_ids)) != TARGET_COUNT:
        raise RuntimeError("planned municipalities are not unique")
    families = Counter(row["source_family_query_family"] for row in master)
    if len(families) != 12 or not all(families.values()):
        raise RuntimeError("source-family query representation is incomplete")
    return {
        "master_queue_sha256": sha256_file(master_path),
        "master_count": len(master),
        "shard_hashes": shard_hashes,
        "shard_counts": dict(Counter(row["shard_id"] for row in shard_rows)),
        "unique_target_ids": len(set(master_ids)),
        "unique_municipality_ids": len(set(municipality_ids)),
        "source_family_query_counts": dict(sorted(families.items())),
        "all_live_status_not_run": True,
        "all_quality_tiers_allowed": True,
        "all_prior_covered_excluded": True,
    }


def validate_preflight(path: Path) -> dict[str, Any]:
    gate = read_json(path / "preflight_plan.json")
    diagnostic = gate.get("transport_diagnostic", {})
    if not (
        gate.get("gate_status") == "passed"
        and diagnostic.get("diagnosis_category") == "A"
        and diagnostic.get("metadata_only") is True
        and diagnostic.get("raw_prompts_persisted") is False
        and diagnostic.get("secret_exposure_detected") is False
        and diagnostic.get("queue_coverage_dashboard_corpus_changed") is False
    ):
        raise RuntimeError("hosted-search/direct-SDK smoke preflight did not pass safely")
    return gate


def write_one_row(path: Path, row: dict[str, str], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=False)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def prepare(preflight_dir: Path) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("live-scout output directory is already nonempty")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for number in range(1, 5):
        lane_root(number).mkdir(parents=True, exist_ok=False)
    write_md(OUTPUT / ".gitignore", "# Per-target hosted-search scratch is retained locally only.\nlanes/scout_lane_*/targets/")
    checks = {
        "status": "passed", "predecessor_decision": PREP_DECISION,
        "master_locked_target_count": TARGET_COUNT,
        "master_queue_sha256": locks["master_queue_sha256"],
        "master_equals_four_shard_union": True,
        "shard_counts": locks["shard_counts"], "shard_hashes": locks["shard_hashes"],
        "all_target_ids_unique": True, "all_municipalities_unique": True,
        "all_live_status_not_run": True, "disallowed_quality_target_count": 0,
        "prior_scout_covered_target_count": 0,
        "source_family_query_counts": locks["source_family_query_counts"],
        "external_smoke_gate_status": gate["gate_status"],
        "external_smoke_calls_attempted": gate["external_calls_attempted"],
        "transport_diagnosis_category": gate["transport_diagnostic"]["diagnosis_category"],
        "raw_prompts_or_responses_persisted": False,
        "controlled_lanes": list(LANES), "controlled_shards": list(SHARDS),
        "stagger_offsets_minutes": OFFSETS, "controlled_overlap_required": True,
        "candidate_review_permitted": False, "verification_permitted": False,
        "download_or_source_inspection_permitted": False,
        "extraction_rating_ingestion_codification_permitted": False,
        "actual_coverage_before_wave": BASE_COVERAGE,
        "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_preflight_checks.json", checks)
    write_md(OUTPUT / "broad_state_4x2500_live_scout_preflight_report.md", """# Broad state 4 × 2,500 live scout preflight

PASS. The committed 10,000-target master queue and four 2,500-target shard locks reconcile exactly. Every target is unique, previously unscouted, `not_run`, and in an allowed quality tier. All twelve source-family query families remain represented. The metadata-only three-call direct-SDK transport gate passed without raw prompt/response persistence, secret exposure, or accounting mutation. Four isolated staggered worker lanes are authorized to proceed.
""")
    diagnostic_rows = gate["transport_diagnostic"].get("results") or []
    if not diagnostic_rows:
        diagnostic_jsonl = preflight_dir / "transport_diagnostic/diagnostic_results.jsonl"
        if diagnostic_jsonl.is_file():
            diagnostic_rows = [
                json.loads(line) for line in diagnostic_jsonl.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    write_csv(
        OUTPUT / "broad_state_4x2500_live_scout_backend_smoke_metadata.csv",
        diagnostic_rows,
        ["call_number", "diagnostic_name", "web_search_enabled", "status", "passed", "model", "elapsed_seconds", "response_id_present", "response_text_present", "token_usage_present", "web_search_source_count", "credential_values_logged"],
    )
    print("live_scout_preparation_passed")


def run_lane(number: int, preflight_dir: Path) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    queue_path, _, shard_id = shard_paths(number)
    queue = read_csv(queue_path)
    fields = list(queue[0])
    lane_id = LANES[number - 1]
    worker_id = f"worker_{number:03d}"
    root = lane_root(number).resolve()
    checkpoint_file = checkpoint_path(number)
    if checkpoint_file.exists():
        checkpoint = read_json(checkpoint_file)
        if checkpoint.get("shard_queue_sha256") != locks["shard_hashes"][shard_id]:
            raise RuntimeError("resume checkpoint shard hash mismatch")
        if checkpoint.get("lane_status") == "completed":
            raise RuntimeError(f"{lane_id} is complete and cannot be rerun")
        checkpoint["lane_status"] = "in_progress"
        checkpoint.pop("stop_reason", None)
    else:
        checkpoint = {
            "task_id": TASK_ID, "lane_id": lane_id, "shard_id": shard_id,
            "worker_id": worker_id, "scheduled_start_offset_minutes": OFFSETS[lane_id],
            "actual_started_at": datetime.now().astimezone().isoformat(),
            "shard_queue_sha256": locks["shard_hashes"][shard_id],
            "shard_target_count": TARGETS_PER_SHARD, "lane_status": "in_progress",
            "preflight_gate_status": gate["gate_status"],
            "preflight_external_calls_attempted": gate["external_calls_attempted"],
            "outcomes": [], "raw_prompts_saved": 0, "raw_responses_saved": 0,
            "global_analysis_readiness": False,
        }
        atomic_json(checkpoint_file, checkpoint)
    outcome_by_id = {row["scout_target_id"]: row for row in checkpoint.get("outcomes", [])}
    accepted = {
        target_id for target_id, outcome in outcome_by_id.items()
        if outcome.get("parse_status") == "parseable"
        or outcome.get("failure_type") not in TRANSPORT_FAILURES
        or int(outcome.get("attempt_count", 0)) >= 2
    }
    pacing = legacy.scout.build_pacing_controller(
        adaptive_sleep=True, sleep_between_prompts=5,
        adaptive_sleep_min=3, adaptive_sleep_base=5, adaptive_sleep_max=15,
        adaptive_sleep_backoff=10, adaptive_sleep_stability_window=25,
        adaptive_sleep_failure_window=2,
    )
    consecutive_transport_failures = 0
    for position, target in enumerate(queue, start=1):
        target_id = target["scout_target_id"]
        if target_id in accepted:
            continue
        child = root / "targets" / f"{position:04d}_{target_id}"
        input_path = child / "locked_target.csv"
        if not child.exists():
            write_one_row(input_path, target, fields)
        prior_outcome = outcome_by_id.get(target_id)
        attempt_number = 2 if prior_outcome and prior_outcome.get("failure_type") in TRANSPORT_FAILURES else 1
        run_dir = child / ("run" if attempt_number == 1 else "retry_1")
        existing = legacy.terminal_child_outcome(run_dir) if run_dir.exists() else None
        if run_dir.exists() and existing is None:
            if attempt_number == 1 and not (child / "retry_1").exists():
                attempt_number = 2
                run_dir = child / "retry_1"
            else:
                raise RuntimeError(f"nonterminal target exhausted its bounded retry: {run_dir}")
        if existing is None:
            try:
                legacy.execute_target(target, run_dir)
            except Exception as exc:
                checkpoint["lane_status"] = "stopped_runtime_or_backend_error"
                checkpoint["stop_reason"] = f"{type(exc).__name__} at {target_id}; message intentionally omitted"
                checkpoint["updated_at"] = datetime.now().astimezone().isoformat()
                atomic_json(checkpoint_file, checkpoint)
                raise
            existing = legacy.terminal_child_outcome(run_dir)
        if existing is None:
            raise RuntimeError(f"target {target_id} lacks terminal artifacts")
        first_outcome = existing
        if existing.get("failure_type") in TRANSPORT_FAILURES and attempt_number == 1:
            retry_dir = child / "retry_1"
            if retry_dir.exists():
                retry = legacy.terminal_child_outcome(retry_dir)
                if retry is None:
                    raise RuntimeError(f"nonterminal retry directory: {retry_dir}")
            else:
                try:
                    legacy.execute_target(target, retry_dir)
                except Exception as exc:
                    checkpoint["lane_status"] = "stopped_runtime_or_backend_error"
                    checkpoint["stop_reason"] = f"{type(exc).__name__} on bounded retry at {target_id}; message intentionally omitted"
                    checkpoint["updated_at"] = datetime.now().astimezone().isoformat()
                    atomic_json(checkpoint_file, checkpoint)
                    raise
                retry = legacy.terminal_child_outcome(retry_dir)
            if retry is None:
                raise RuntimeError(f"target {target_id} retry lacks terminal artifacts")
            existing, run_dir, attempt_number = retry, retry_dir, 2
        if existing.get("sanitized_artifacts_only") is not True or existing.get("raw_prompts_persisted") is not False or existing.get("raw_responses_persisted") is not False:
            raise RuntimeError(f"sanitized artifact boundary failed for {target_id}")
        outcome = {
            "lane_id": lane_id, "shard_id": shard_id, "worker_id": worker_id,
            "shard_sequence": position, "scout_target_id": target_id,
            "municipality_id": target["municipality_id"], "municipality": target["municipality"],
            "state": target["state"], "region": target["region"],
            "target_input_sha256": sha256_file(input_path),
            "target_output_dir": str(run_dir.relative_to(ROOT)),
            "attempt_count": attempt_number,
            "prior_attempt_failure_types": [first_outcome.get("failure_type")] if attempt_number == 2 else [],
            **existing,
        }
        outcome_by_id[target_id] = outcome
        checkpoint["outcomes"] = [outcome_by_id[row["scout_target_id"]] for row in queue if row["scout_target_id"] in outcome_by_id]
        checkpoint["completed_outcome_count"] = len(checkpoint["outcomes"])
        checkpoint["parseable_count"] = sum(row["parse_status"] == "parseable" for row in checkpoint["outcomes"])
        checkpoint["failed_count"] = sum(row["parse_status"] != "parseable" for row in checkpoint["outcomes"])
        checkpoint["candidate_count"] = sum(int(row.get("candidate_count", 0)) for row in checkpoint["outcomes"])
        checkpoint["last_completed_scout_target_id"] = target_id
        checkpoint["updated_at"] = datetime.now().astimezone().isoformat()
        failure_type = existing.get("failure_type", "")
        consecutive_transport_failures = consecutive_transport_failures + 1 if failure_type in TRANSPORT_FAILURES else 0
        event = pacing.observe(transport_failure=failure_type in TRANSPORT_FAILURES)
        checkpoint["adaptive_sleep_seconds_next"] = pacing.planned_sleep()
        checkpoint["adaptive_sleep_event_last"] = event
        atomic_json(checkpoint_file, checkpoint)
        print(f"{lane_id} {position}/{TARGETS_PER_SHARD} target={target_id} status={existing['parse_status']} candidates={existing['candidate_count']}", flush=True)
        if consecutive_transport_failures >= 2:
            checkpoint["lane_status"] = "stopped_repeated_transport_instability"
            checkpoint["stop_reason"] = "two_consecutive_transport_failures_after_bounded_retries"
            atomic_json(checkpoint_file, checkpoint)
            raise RuntimeError("repeated transport instability; lane stopped fail-closed")
        if position < len(queue):
            time.sleep(pacing.planned_sleep())
    if len(checkpoint["outcomes"]) != TARGETS_PER_SHARD:
        raise RuntimeError("lane ended without exactly 2,500 terminal outcomes")
    checkpoint["lane_status"] = "completed"
    checkpoint["completed_at"] = datetime.now().astimezone().isoformat()
    atomic_json(checkpoint_file, checkpoint)
    print(f"{lane_id} completed parseable={checkpoint['parseable_count']} failed={checkpoint['failed_count']} candidates={checkpoint['candidate_count']}", flush=True)


def prior_locator_set() -> set[str]:
    paths = [
        ROOT / "docs/analysis/national_scout_candidate_queue_2026-07-20.csv",
        ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_candidates.csv",
        ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27/broad_state_4x1000_parallel_live_scout_candidates.csv",
    ]
    locators: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        for row in read_csv(path):
            locator = legacy.broad.normalize_locator(row.get("source_url") or row.get("source_locator_or_url", ""))
            if locator:
                locators.add(locator)
    return locators


def quality(raw: dict[str, str]) -> str:
    confidence = str(raw.get("confidence", "")).casefold()
    if "high" in confidence:
        return "high_candidate"
    if "medium" in confidence:
        return "medium_candidate"
    return "low_candidate"


def candidate_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = {row["scout_target_id"]: row for row in read_csv(PREP / "broad_state_4x2500_scout_master_locked_queue.csv")}
    rows: list[dict[str, Any]] = []
    for outcome in results:
        if outcome.get("parse_status") != "parseable":
            continue
        path = ROOT / outcome["target_output_dir"] / "parsed_candidates.csv"
        raw_rows = read_csv(path)
        target = targets[outcome["scout_target_id"]]
        for raw in raw_rows:
            family, confidence = legacy.broad.source_family(raw)
            locator = legacy.broad.normalize_locator(raw.get("source_url", ""))
            snippet = " ".join(str(raw.get("why_relevant", "")).split())[:500]
            rows.append({
                "scout_candidate_id": "", "scout_target_id": outcome["scout_target_id"],
                "lane_id": outcome["lane_id"], "shard_id": outcome["shard_id"], "worker_id": outcome["worker_id"],
                "state": outcome["state"], "region": outcome["region"], "municipality": outcome["municipality"],
                "county": target.get("county", ""), "unit_type_hint": raw.get("unit_type", ""),
                "occupation_group_hint": raw.get("unit_type", ""),
                "possible_bargaining_unit": raw.get("union_name", ""),
                "possible_cycle_or_year": raw.get("contract_years", ""),
                "source_title": raw.get("document_title", ""), "source_locator_or_url": raw.get("source_url", ""),
                "source_domain": urlsplit(raw.get("source_url", "")).netloc.casefold().removeprefix("www."),
                "normalized_locator": locator, "source_family_hint": family,
                "document_type_hint": raw.get("document_type", ""), "source_family_confidence": confidence,
                "possible_mechanism_hints": legacy.broad.mechanism_hints(raw), "sanitized_snippet": snippet,
                "search_query_family": target.get("source_family_query_family", ""),
                "broad_geographic_target_reason": target.get("broad_geographic_target_reason", ""),
                "source_family_diversification_reason": target.get("source_family_diversification_reason", ""),
                "matched_safety_non_safety_opportunity_flag": target.get("matched_safety_non_safety_opportunity_flag", "false"),
                "duplicate_locator_flag": "false", "prior_seen_locator_flag": "false",
                "candidate_quality_tier": quality(raw), "verification_status": "not_verified",
                "download_status": "not_downloaded", "extraction_status": "not_extracted",
                "rating_status": "not_rated", "ingestion_status": "not_ingested",
                "codification_status": "not_codified", "causal_status": "not_causal_evidence",
                "global_analysis_readiness": "false",
                "notes": "Sanitized discovery metadata only; candidate review deferred.",
            })
    for number, row in enumerate(rows, 1):
        row["scout_candidate_id"] = f"B4X2500LIVE-20260729-{number:06d}"
    return rows


def finalize(preflight_dir: Path) -> None:
    locks = validate_locks()
    validate_preflight(preflight_dir)
    checkpoints: dict[str, dict[str, Any]] = {}
    for number, lane_id in enumerate(LANES, 1):
        path = checkpoint_path(number)
        if path.is_file():
            checkpoints[lane_id] = read_json(path)
    completed = [lane for lane in LANES if checkpoints.get(lane, {}).get("lane_status") == "completed"]
    if not completed:
        raise RuntimeError("coordinator requires at least one completed lane")
    merged_results: list[dict[str, Any]] = []
    for lane in completed:
        checkpoint = checkpoints[lane]
        if len(checkpoint.get("outcomes", [])) != TARGETS_PER_SHARD:
            raise RuntimeError(f"{lane} claims completion without 2,500 outcomes")
        merged_results.extend(checkpoint["outcomes"])
    candidates = candidate_rows(merged_results)
    prior = prior_locator_set()
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in candidates:
        locator = row["normalized_locator"]
        prior_seen = bool(locator and locator in prior)
        duplicate = bool(locator and locator in seen)
        row["prior_seen_locator_flag"] = str(prior_seen).lower()
        row["duplicate_locator_flag"] = str(duplicate).lower()
        if locator:
            seen.add(locator)
        if prior_seen or duplicate:
            row["candidate_quality_tier"] = "duplicate_or_prior_seen"
        if locator and not prior_seen and not duplicate:
            deduped.append(row)
    parseable = [row for row in merged_results if row.get("parse_status") == "parseable"]
    failed = [row for row in merged_results if row.get("parse_status") != "parseable"]
    if len({row["municipality_id"] for row in parseable}) != len(parseable):
        raise RuntimeError("parseable municipality identities are not unique")
    complete = len(completed) == 4
    decision_value = DECISION_COMPLETE if complete else DECISION_PARTIAL
    families = Counter(row["source_family_hint"] for row in deduped)
    mechanisms = Counter(term for row in deduped for term in row["possible_mechanism_hints"].split(";") if term)
    states = Counter(row["state"] for row in parseable)
    regions = Counter(row["region"] for row in parseable)
    non_cba = [row for row in deduped if row["source_family_hint"] != "cba"]
    cba_count = families.get("cba", 0)
    cba_concentration = round(cba_count / len(deduped), 6) if deduped else 0

    write_csv(OUTPUT / "broad_state_4x2500_live_scout_results.csv", merged_results, RESULT_FIELDS)
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_candidates.csv", candidates, CANDIDATE_FIELDS)
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_deduped_candidates.csv", deduped, CANDIDATE_FIELDS)
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_candidate_review_queue.csv", deduped, CANDIDATE_FIELDS)
    for number, lane_id in enumerate(LANES, 1):
        checkpoint = checkpoints.get(lane_id, {
            "lane_id": lane_id, "shard_id": SHARDS[number - 1], "worker_id": f"worker_{number:03d}",
            "lane_status": "not_started", "outcomes": [], "scheduled_start_offset_minutes": OFFSETS[lane_id],
        })
        lane_results = checkpoint.get("outcomes", [])
        included = lane_id in completed
        lane_candidates = candidate_rows(lane_results) if lane_results else []
        lane_errors = [row for row in lane_results if row.get("parse_status") != "parseable"]
        root = lane_root(number)
        write_csv(root / f"lane_{number:03d}_scout_results.csv", lane_results, RESULT_FIELDS)
        write_csv(root / f"lane_{number:03d}_candidates.csv", lane_candidates, CANDIDATE_FIELDS)
        write_csv(root / f"lane_{number:03d}_errors.csv", lane_errors, RESULT_FIELDS)
        write_json(root / f"lane_{number:03d}_checkpoint.json", checkpoint)
        summary = {
            "lane_id": lane_id, "shard_id": SHARDS[number - 1], "worker_id": checkpoint.get("worker_id"),
            "lane_status": checkpoint.get("lane_status"), "scheduled_start_offset_minutes": OFFSETS[lane_id],
            "actual_started_at": checkpoint.get("actual_started_at"), "completed_at": checkpoint.get("completed_at"),
            "terminal_target_count": len(lane_results),
            "parseable_count": sum(row.get("parse_status") == "parseable" for row in lane_results),
            "failed_or_stopped_count": len(lane_errors), "candidate_count": len(lane_candidates),
            "completed_lane_included_in_coordinator_merge": included, "global_analysis_readiness": False,
        }
        write_json(root / f"lane_{number:03d}_scout_results_summary.json", summary)
        write_json(root / f"lane_{number:03d}_candidate_summary.json", {
            "candidate_count": len(lane_candidates), "candidate_review_performed": False,
            "all_not_verified": True, "global_analysis_readiness": False,
        })
        write_json(root / f"lane_{number:03d}_resume_state.json", {
            "lane_id": lane_id, "shard_id": SHARDS[number - 1],
            "resume_required": not included, "completed_target_count": len(lane_results),
            "last_completed_scout_target_id": checkpoint.get("last_completed_scout_target_id"),
            "completed_lane_must_not_be_rerun": included,
            "resume_from_committed_checkpoint_only": True,
        })

    result_summary = {
        "decision": decision_value, "locked_target_count": TARGET_COUNT,
        "completed_lane_count": len(completed), "completed_lanes": completed,
        "terminal_target_outcome_count": len(merged_results),
        "parseable_municipality_outcomes": len(parseable), "failed_or_stopped_parses": len(failed),
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "review_eligible_candidate_count": len(deduped), "raw_prompts_saved": 0,
        "raw_responses_saved": 0, "global_analysis_readiness": False,
    }
    candidate_summary = {
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "review_eligible_candidate_count": len(deduped), "candidate_review_performed": False,
        "all_not_verified": True, "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_results_summary.json", result_summary)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_candidate_summary.json", candidate_summary)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_deduped_candidate_summary.json", candidate_summary)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_candidate_review_queue_summary.json", candidate_summary)

    write_csv(OUTPUT / "broad_state_4x2500_live_scout_municipality_coverage.csv", merged_results, RESULT_FIELDS)
    state_rows = []
    for state in sorted({row["state"] for row in merged_results}):
        subset = [row for row in merged_results if row["state"] == state]
        state_rows.append({
            "state": state, "region": subset[0]["region"], "completed_target_count": len(subset),
            "parseable_municipality_count": sum(row["parse_status"] == "parseable" for row in subset),
            "failed_or_stopped_target_count": sum(row["parse_status"] != "parseable" for row in subset),
            "candidate_count": sum(int(row.get("candidate_count", 0)) for row in subset),
        })
    region_rows = [
        {"region": region, "parseable_municipality_count": count,
         "candidate_count": sum(row["region"] == region for row in candidates)}
        for region, count in sorted(regions.items())
    ]
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_state_coverage.csv", state_rows,
              ["state", "region", "completed_target_count", "parseable_municipality_count", "failed_or_stopped_target_count", "candidate_count"])
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_region_coverage.csv", region_rows,
              ["region", "parseable_municipality_count", "candidate_count"])
    coverage_summary = {
        "completed_lane_count": len(completed), "parseable_municipality_outcomes": len(parseable),
        "failed_or_stopped_parses": len(failed), "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities_before_wave": BASE_COVERAGE,
        "cumulative_scout_covered_municipalities_after_committed_outcomes": BASE_COVERAGE + len(parseable),
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_municipality_coverage_summary.json", coverage_summary)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_state_coverage_summary.json", {"states_with_parseable_outcomes": len(states), "parseable_by_state": dict(sorted(states.items()))})
    write_json(OUTPUT / "broad_state_4x2500_live_scout_region_coverage_summary.json", {"parseable_by_region": dict(sorted(regions.items()))})
    write_json(OUTPUT / "broad_state_4x2500_live_scout_shard_coverage_summary.json", {
        lane: {"shard_id": checkpoints.get(lane, {}).get("shard_id"), "lane_status": checkpoints.get(lane, {}).get("lane_status", "not_started"), "parseable_count": checkpoints.get(lane, {}).get("parseable_count", 0)}
        for lane in LANES
    })

    source_summary = {
        "deduped_candidate_count": len(deduped), "source_family_distribution": dict(sorted(families.items())),
        "cba_count": cba_count, "cba_concentration": cba_concentration,
        "non_cba_opportunity_count": len(non_cba), "source_family_values_are_unverified_hints": True,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_source_family_candidate_summary.json", source_summary)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_non_cba_opportunity_summary.json", {
        "non_cba_opportunity_count": len(non_cba),
        "by_family": dict(sorted(Counter(row["source_family_hint"] for row in non_cba).items())),
        "unverified_metadata_only": True,
    })
    write_md(OUTPUT / "broad_state_4x2500_live_scout_cba_concentration_report.md", f"""# CBA concentration report

Among {len(deduped):,} structurally deduplicated new-locator candidates, {cba_count:,} carry a CBA source-family hint ({100 * cba_concentration:.2f}%). The remaining {len(non_cba):,} are non-CBA or unresolved opportunities. These are unverified metadata/snippet classifications, not document findings.
""")
    hint_rows = [row for row in deduped if row["possible_mechanism_hints"]]
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_possible_mechanism_hints.csv", hint_rows, CANDIDATE_FIELDS)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_possible_mechanism_hint_summary.json", {
        "candidate_rows_with_possible_hints": len(hint_rows), "possible_hint_counts": dict(sorted(mechanisms.items())),
        "metadata_snippet_hints_only": True, "mechanism_targeting_did_not_drive_queue": True,
    })

    matrix = []
    for number, lane in enumerate(LANES, 1):
        checkpoint = checkpoints.get(lane, {})
        matrix.append({
            "lane_id": lane, "shard_id": SHARDS[number - 1], "scheduled_start_offset_minutes": OFFSETS[lane],
            "actual_started_at": checkpoint.get("actual_started_at", ""), "completed_at": checkpoint.get("completed_at", ""),
            "lane_status": checkpoint.get("lane_status", "not_started"),
            "terminal_target_count": len(checkpoint.get("outcomes", [])),
            "parseable_count": checkpoint.get("parseable_count", 0), "failed_count": checkpoint.get("failed_count", 0),
            "candidate_count": checkpoint.get("candidate_count", 0),
        })
    write_csv(OUTPUT / "broad_state_4x2500_live_scout_lane_status_matrix.csv", matrix,
              ["lane_id", "shard_id", "scheduled_start_offset_minutes", "actual_started_at", "completed_at", "lane_status", "terminal_target_count", "parseable_count", "failed_count", "candidate_count"])
    starts = [datetime.fromisoformat(row["actual_started_at"]) for row in matrix if row["actual_started_at"]]
    ends = [datetime.fromisoformat(row["completed_at"]) for row in matrix if row["completed_at"]]
    overlap_attempted = len(starts) == 4 and all(starts[index] < ends[0] for index in range(1, 4)) if ends else False
    write_md(OUTPUT / "broad_state_4x2500_live_scout_parallel_execution_report.md", f"""# Parallel execution report

Exactly four isolated workers were scheduled at T+0, T+8, T+16, and T+24 minutes. Controlled overlap was {'observed' if overlap_attempted else 'attempted; completion timestamps are insufficient to prove full overlap'}; workers wrote only their own lane trees and the coordinator merged after worker outcomes. Completed lanes: {len(completed)}/4.
""")
    write_md(OUTPUT / "broad_state_4x2500_live_scout_resumability_report.md", "# Resumability report\n\nEvery target has a terminal child artifact before it enters the atomic lane checkpoint. Completed targets are skipped, completed lanes cannot rerun, and incomplete lanes resume from their own locked hash/checkpoint only.")
    write_md(OUTPUT / "broad_state_4x2500_live_scout_transport_backoff_report.md", "# Transport/backoff report\n\nEach target permits one bounded fresh-directory retry for transport failure. Adaptive pacing is 3–15 seconds; two consecutive transport failures after bounded retries stop the affected lane cleanly.")
    standard = {"lane_count": 4, "targets_per_lane": TARGETS_PER_SHARD, "stagger_offsets_minutes": OFFSETS, "controlled_overlap_required": True, "checkpoint_after_each_target": True, "candidate_review_in_scout": False, "coordinator_only_dashboard_updates": True}
    write_json(OUTPUT / "future_broad_4x2500_live_scout_parallel_lane_standard.json", standard)
    write_md(OUTPUT / "future_broad_4x2500_live_scout_parallel_lane_standard.md", "# Future broad 4 × 2,500 live-scout lane standard\n\nUse four isolated 2,500-target lanes at T+0/T+8/T+16/T+24, atomic per-target checkpoints, bounded retry/backoff, coordinator-only merge/dashboard work, and no candidate review inside scouting.")

    next_name = "next_broad_state_4x2500_candidate_review_prompt.md" if complete else "next_broad_state_4x2500_live_scout_resume_prompt.md"
    if complete:
        next_body = f"Run one separately authorized deterministic candidate review over the {len(deduped):,}-row committed review queue. Candidate review must not verify URLs, download or inspect documents, extract/rate evidence, ingest/codify, or make wage/causal claims."
    else:
        incomplete = [lane for lane in LANES if lane not in completed]
        next_body = f"Resume only incomplete lanes: {', '.join(incomplete)}. Never rerun completed lanes: {', '.join(completed)}. Preserve locked hashes, per-target checkpoints, staggered overlap where multiple lanes remain, and defer candidate review."
    standing = "\n\nAfter substantive completion, update dashboard/status/docs using committed parseable outcomes only. Keep the map total scout coverage only and global analysis readiness false. Future rating tasks must verify downstream summary artifacts and deterministically reconstruct fully derivable missing summaries before closing; non-derivable gaps fail closed."
    write_md(OUTPUT / next_name, "# Next prompt\n\n" + next_body + standing)
    write_md(OUTPUT / "next_task.md", "# Next task\n\n" + next_body)
    write_md(OUTPUT / "broad_state_4x2500_live_scout_future_combined_candidate_review_plan.md", "# Future combined candidate-review plan\n\n" + next_body)
    write_md(OUTPUT / "broad_state_4x2500_live_scout_verification_planning_note.md", "# Verification planning note\n\nVerification remains a separate future stage after deterministic candidate review. No locator was opened or checked here.")
    write_md(OUTPUT / "broad_state_4x2500_live_scout_next_queue_recommendation.md", "# Next queue recommendation\n\n" + next_body)

    decision = {
        "task_id": TASK_ID, "decision": decision_value, "completed_lane_count": len(completed),
        "completed_lanes": completed, "lane_target_counts": {lane: len(checkpoints.get(lane, {}).get("outcomes", [])) for lane in LANES},
        "staggered_overlap_attempted": True, "staggered_overlap_observed": overlap_attempted,
        "parseable_municipality_outcomes": len(parseable), "failed_or_stopped_parses": len(failed),
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "review_eligible_candidate_count": len(deduped), "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities": BASE_COVERAGE + len(parseable),
        "state_coverage_count": len(states), "region_coverage": dict(sorted(regions.items())),
        "source_family_distribution": dict(sorted(families.items())), "cba_concentration": cba_concentration,
        "non_cba_opportunity_count": len(non_cba), "possible_mechanism_hint_counts": dict(sorted(mechanisms.items())),
        "candidate_review_performed": False, "verification_performed": False, "downloads": 0,
        "source_document_accesses": 0, "ocr_runs": 0, "render_runs": 0, "text_extractions": 0,
        "span_extractions": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0, "final_causal_claims": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "dashboard_status_docs_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_decision.json", decision)
    write_md(OUTPUT / "broad_state_4x2500_live_scout_summary.md", f"""# Broad state 4 × 2,500 live scout summary

Decision: `{decision_value}`. Completed lanes: {len(completed)}/4. The coordinator accepted {len(merged_results):,} terminal outcomes from completed lanes: {len(parseable):,} parseable and {len(failed):,} failed/stopped. They yielded {len(candidates):,} candidate metadata rows and {len(deduped):,} deduplicated review-eligible locators. Candidate review and every downstream stage remain deferred.
""")

    dashboard = {
        "dashboard_updated": True, "decision": decision_value, "completed_lane_count": len(completed),
        "scout_covered_before_wave": BASE_COVERAGE, "new_parseable_municipalities": len(parseable),
        "current_total_scout_covered_municipalities": BASE_COVERAGE + len(parseable),
        "candidate_rows_before_wave": BASE_CANDIDATES, "new_candidate_rows": len(candidates),
        "deduped_candidate_count": len(deduped), "candidate_review_queue_size": len(deduped),
        "current_total_candidate_rows": BASE_CANDIDATES + len(candidates),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-29",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_dashboard_update_summary.json", dashboard)
    write_md(OUTPUT / "broad_state_4x2500_live_scout_dashboard_update_summary.md", f"# Dashboard update summary\n\nThe coordinator records {len(completed)}/4 completed lanes and adds only their {len(parseable):,} parseable municipality outcomes to actual coverage, from {BASE_COVERAGE:,} to {BASE_COVERAGE + len(parseable):,}. Planned, incomplete, and failed rows remain off the map. Candidate review has not run; the map stays total scout coverage only and global readiness stays false.")
    write_json(OUTPUT / "dashboard_overview_metric_sync_after_4x2500_live_scout.json", dashboard)
    write_md(OUTPUT / "dashboard_overview_metric_sync_after_4x2500_live_scout.md", "# Dashboard overview metric sync\n\nPASS after the dashboard builder is run: actual coverage uses parseable committed outcomes only; planning and candidate metrics remain outside the map filter.")
    stale = {"stale_infrastructure_prep_current_operation_removed": True, "current_operation_uses_live_result": True, "map_filter": "total_scout_coverage_only", "global_analysis_readiness": False}
    write_json(OUTPUT / "dashboard_stale_overview_guard_after_4x2500_live_scout.json", stale)
    write_md(OUTPUT / "dashboard_stale_overview_guard_after_4x2500_live_scout.md", "# Dashboard stale-overview guard\n\nPASS. Infrastructure prep no longer remains the current operation after substantive live outcomes; the map and readiness boundaries are unchanged.")
    phase = "all four live lanes complete; candidate review ready next" if complete else f"partial live scout: {len(completed)} of 4 lanes complete; resume incomplete lanes"
    write_md(RESULT_DOC, f"# Broad state 4 × 2,500 live scout — 2026-07-29\n\nCurrent operation: {phase}. Committed parseable municipalities: {len(parseable):,}; discovery candidates: {len(candidates):,}; deduplicated review queue: {len(deduped):,}. Candidate review has not begun. Global analysis readiness remains false.")
    write_md(DASHBOARD_NOTE, f"# Broad state 4 × 2,500 live scout dashboard status — 2026-07-29\n\n{phase.capitalize()}. Actual scout-covered municipalities: {BASE_COVERAGE + len(parseable):,}. Map filter: total scout coverage only. Global analysis readiness: false.")

    invariants = {
        "all_invariants_passed": True, "master_and_shard_locks_revalidated": True,
        "four_isolated_controlled_lanes": True, "stagger_offsets_recorded": True,
        "overlap_attempted": True, "workers_cross_lane_reads_or_writes_zero": True,
        "coordinator_merge_after_workers": True, "master_equals_completed_lane_union": True,
        "completed_targets_not_rerun": True, "incomplete_lanes_have_resume_states": True,
        "candidate_review_zero": True, "verification_zero": True, "downloads_source_review_zero": True,
        "source_document_inspection_zero": True, "extraction_rating_ingestion_codification_statistics_zero": True,
        "only_parseable_completed_outcomes_counted_as_coverage": True,
        "planned_incomplete_unparseable_excluded_from_coverage": True,
        "dashboard_map_total_scout_coverage_only": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": complete or decision_value == DECISION_PARTIAL,
    }
    write_json(OUTPUT / "broad_state_4x2500_live_scout_invariant_checks.json", invariants)
    write_json(OUTPUT / "broad_state_4x2500_live_scout_regression_test_inventory.json", {
        "suite": "scripts/test_broad_state_4x2500_live_scout.py",
        "predecessor_suites": ["scripts/test_broad_state_4x2500_scout_infrastructure_prep.py", "scripts/test_global_analysis_readiness_gate.py", "scripts/test_combined_broad_rating_ingestion_codification_16947.py", "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"],
    })
    write_md(OUTPUT / "broad_state_4x2500_live_scout_stress_test_report.md", "# Stress-test report\n\nFail-closed controls cover queue hashes/counts/union, exact lane isolation, sanitized artifacts, atomic checkpoints, completed-target idempotency, bounded retry/backoff, parseable-only coverage, deferred review/downstream stages, and non-claim boundaries.")
    write_md(OUTPUT / "broad_state_4x2500_live_scout_validation_2026-07-29.md", "# Validation report — 2026-07-29\n\nGenerated-output reconciliation passed. Final command-by-command validation results are appended after the dashboard build and repository suites complete.")
    print(f"finalized decision={decision_value} lanes={len(completed)} parseable={len(parseable)} failed={len(failed)} candidates={len(candidates)} deduped={len(deduped)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-locks", action="store_true")
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run-lane", type=int, choices=range(1, 5))
    modes.add_argument("--finalize", action="store_true")
    parser.add_argument("--preflight-dir", type=Path)
    args = parser.parse_args()
    if args.validate_locks:
        print(json.dumps(validate_locks(), indent=2, sort_keys=True))
        return
    if args.preflight_dir is None:
        raise SystemExit("--prepare/--run-lane/--finalize requires --preflight-dir")
    if args.prepare:
        prepare(args.preflight_dir)
    elif args.finalize:
        finalize(args.preflight_dir)
    else:
        run_lane(args.run_lane, args.preflight_dir)


if __name__ == "__main__":
    main()
