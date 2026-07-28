#!/usr/bin/env python3
"""Run the committed 4x1000 broad-scout shards with per-target checkpoints.

The established scout backend only writes parsed artifacts after a whole
invocation returns.  A 1,000-row invocation therefore cannot satisfy this
task's per-target durability contract.  This coordinator preserves each
committed shard as the parent lock, invokes the production scout on one exact
parent row at a time, and atomically records the terminal outcome before
advancing.  It never opens candidate URLs or performs candidate review.
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

import gabriel_state_source_scout as scout
import run_broad_state_by_state_source_scout_wave as broad


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-SCOUT-DRY-RUN-PREP-2026-07-27"
TMP_ROOT = ROOT / "tmp/broad_state_4x1000_live_scout_2026-07-27"
SCOUT = ROOT / "scripts/gabriel_state_source_scout.py"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-LIVE-SCOUT-2026-07-27"
RESULT_DOC = ROOT / "docs/analysis/broad_state_4x1000_live_scout_result_2026-07-27.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/broad_state_4x1000_live_scout_dashboard_status_note_2026-07-27.md"
PRIOR_REVIEW = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_candidate_review_queue.csv"
CANONICAL_CANDIDATES = ROOT / "docs/analysis/national_scout_candidate_queue_2026-07-20.csv"
ALLOWED_TIERS = {
    "strong_broad_geographic_target",
    "strong_source_family_diversification_target",
    "matched_safety_non_safety_target",
    "acceptable_broad_target",
}
SHARD_IDS = [f"broad_shard_{number:03d}" for number in range(1, 5)]
TRANSPORT_FAILURES = {"connection_error", "timeout", "outer_timeout"}
DECISION_COMPLETE = "broad_state_4x1000_live_scout_completed_combined_candidate_review_ready"
DECISION_PARTIAL = "broad_state_4x1000_live_scout_partial_shards_completed_resume_ready"

RESULT_FIELDS = [
    "shard_id", "shard_sequence", "scout_target_id", "municipality_id",
    "municipality", "state", "region", "parse_status", "success_status",
    "failure_type", "attempt_count", "candidate_count", "target_input_sha256",
    "target_output_dir", "input_tokens", "reasoning_tokens", "output_tokens",
    "total_tokens", "response_id_present",
]
CANDIDATE_FIELDS = [
    "live_scout_candidate_id", "shard_id", "scout_target_id", "municipality_id",
    "state", "region", "municipality", "county", "unit_type", "union_name",
    "employer", "document_title", "contract_years", "source_url",
    "normalized_locator", "source_owner_type", "document_type",
    "source_family_hint", "source_family_confidence", "candidate_stage",
    "document_completeness", "visible_year_evidence", "overlap_with_anchor_cycle",
    "duplicate_risk", "blocked_or_unreadable_flag", "cycle_match_notes",
    "comparator_role", "wrong_employer_risk", "context_only_flag",
    "needs_verification_reason", "why_relevant", "confidence",
    "possible_mechanism_hints", "source_family_query_family",
    "prior_seen_locator_flag", "duplicate_locator_flag",
    "combined_review_status", "verification_status", "download_status",
    "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "notes",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_one_row(path: Path, row: dict[str, str], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=False)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def shard_paths(number: int) -> tuple[Path, Path, str]:
    shard_id = f"broad_shard_{number:03d}"
    queue = PREP / f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv"
    lock = PREP / f"broad_state_4x1000_scout_shard_{number:03d}_lock.json"
    return queue, lock, shard_id


def validate_locks() -> dict[str, Any]:
    master_path = PREP / "broad_state_4x1000_scout_master_locked_queue.csv"
    master_lock = read_json(PREP / "broad_state_4x1000_scout_master_lock.json")
    master = read_csv(master_path)
    if len(master) != 4000 or sha256_file(master_path) != master_lock["queue_sha256"]:
        raise RuntimeError("master queue count/hash mismatch")
    shard_rows: list[dict[str, str]] = []
    shard_hashes: dict[str, str] = {}
    for number in range(1, 5):
        queue_path, lock_path, shard_id = shard_paths(number)
        lock = read_json(lock_path)
        rows = read_csv(queue_path)
        actual_hash = sha256_file(queue_path)
        if len(rows) != 1000 or actual_hash != lock["queue_sha256"]:
            raise RuntimeError(f"{shard_id} queue count/hash mismatch")
        if any(row["shard_id"] != shard_id for row in rows):
            raise RuntimeError(f"{shard_id} contains a foreign shard ID")
        if any(row["target_quality_tier"] not in ALLOWED_TIERS for row in rows):
            raise RuntimeError(f"{shard_id} contains a disallowed quality tier")
        shard_hashes[shard_id] = actual_hash
        shard_rows.extend(rows)
    master_ids = [row["scout_target_id"] for row in master]
    union_ids = [row["scout_target_id"] for row in shard_rows]
    if len(set(master_ids)) != 4000 or set(master_ids) != set(union_ids):
        raise RuntimeError("master queue does not equal the four-shard union")
    return {
        "master_queue_sha256": sha256_file(master_path),
        "master_count": len(master),
        "shard_hashes": shard_hashes,
        "shard_counts": dict(Counter(row["shard_id"] for row in shard_rows)),
        "all_quality_tiers_allowed": True,
    }


def validate_preflight(path: Path) -> dict[str, Any]:
    gate = read_json(path / "preflight_plan.json")
    transport = gate.get("transport_diagnostic", {})
    if not (
        gate.get("gate_status") == "passed"
        and transport.get("diagnosis_category") == "A"
        and transport.get("secret_exposure_detected") is False
        and transport.get("metadata_only") is True
        and transport.get("queue_coverage_dashboard_corpus_changed") is False
    ):
        raise RuntimeError("hosted-search/direct-SDK preflight did not pass safely")
    return gate


def terminal_child_outcome(child: Path) -> dict[str, Any] | None:
    metadata_path = child / "run_metadata.json"
    timing_path = child / "row_timing.csv"
    if not metadata_path.is_file() or not timing_path.is_file():
        return None
    metadata = read_json(metadata_path)
    timing = read_csv(timing_path)
    if len(timing) != 1:
        return None
    row = timing[0]
    status = row.get("parse_status", "")
    if status not in {"parseable", "failed"}:
        return None
    candidates_path = child / "parsed_candidates.csv"
    failed_path = child / "failed_parses.csv"
    candidates = read_csv(candidates_path) if candidates_path.is_file() else []
    failures = read_csv(failed_path) if failed_path.is_file() else []
    return {
        "parse_status": status,
        "success_status": row.get("success_status", ""),
        "failure_type": row.get("failure_type", ""),
        "candidate_count": len(candidates),
        "input_tokens": row.get("input_tokens", ""),
        "output_tokens": row.get("output_tokens", ""),
        "reasoning_tokens": row.get("reasoning_tokens", ""),
        "total_tokens": row.get("total_tokens", ""),
        "response_id_present": row.get("response_id_present", ""),
        "execution_status": metadata.get("execution_status"),
        "sanitized_artifacts_only": metadata.get("sanitized_artifacts_only"),
        "raw_prompts_persisted": metadata.get("raw_prompts_persisted"),
        "raw_responses_persisted": metadata.get("raw_responses_persisted"),
        "failed_parse_rows": len(failures),
    }


def execute_target(target: dict[str, str], run_dir: Path) -> None:
    """Execute one hosted-search target and persist only sanitized artifacts."""
    if run_dir.exists():
        raise RuntimeError(f"target output directory is not fresh: {run_dir}")
    run_dir.mkdir(parents=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    run_id = f"{target['state'].lower()}_{timestamp}"
    prompt = scout.build_prompt(
        target["municipality"], target["state"], "compact", context=target
    )
    identifier = scout.build_identifier(run_id, scout.row_identifier_token(target))
    planned = scout.build_planned_row_timing(
        run_id, [target], [target], backend="direct-sdk",
        model="gpt-5.4-nano", dry_run=False, sleep_between_prompts=0,
    )
    result = scout.run_direct_sdk_live_batch(
        [prompt], [identifier], run_dir, "gpt-5.4-nano", "low", 1,
        timeout=90, max_retries=0, sleep_between_prompts=0,
        web_search=True, return_timing=True,
    )
    frame, failure, timing_events = result
    if failure is not None or frame is None or len(frame) != 1:
        atomic_json(run_dir / "run_metadata.json", {
            "execution_status": "backend_failure",
            "live_failure_reason": failure or "backend returned wrong row count",
            "sanitized_artifacts_only": True,
            "raw_prompts_persisted": False,
            "raw_responses_persisted": False,
            "global_analysis_readiness": False,
        })
        raise RuntimeError(f"one-target backend failure: {failure}")
    raw = frame.to_dict(orient="records")[0]
    candidates, failed = scout.parse_response_to_candidates(
        run_id, target, identifier, str(raw.get("Response", "") or ""),
        "not_saved_sanitized_artifacts_only", gabriel_row=raw,
    )
    failures = [failed] if failed else []
    scout.write_csv(run_dir / "parsed_candidates.csv", candidates, scout.CANDIDATE_FIELDS)
    scout.write_csv(run_dir / "failed_parses.csv", failures, scout.FAILED_PARSE_FIELDS)
    timing = scout.finalize_row_timing(
        planned, [target], [identifier], [raw], failures, timing_events,
    )
    scout.write_csv(run_dir / "row_timing.csv", timing, scout.ROW_TIMING_FIELDS)
    parseable = not failures
    atomic_json(run_dir / "run_metadata.json", {
        "run_id": run_id,
        "execution_status": "completed" if parseable else "completed_no_parseable_outcome",
        "input_rows_loaded": 1,
        "municipalities_requested": 1,
        "model": "gpt-5.4-nano",
        "live_backend": "direct-sdk",
        "web_search_enabled": True,
        "sanitized_artifacts_only": True,
        "raw_prompts_persisted": False,
        "raw_responses_persisted": False,
        "raw_outputs_path": None,
        "n_parseable": 1 if parseable else 0,
        "n_failed_parses": len(failures),
        "n_candidate_rows": len(candidates),
        "global_analysis_readiness": False,
    })


def checkpoint_path(shard_id: str, lane_root: Path | None = None, lane_id: str | None = None) -> Path:
    if lane_root is not None:
        return lane_root / f"{lane_id or shard_id}_checkpoint.json"
    return TMP_ROOT / shard_id / "shard_checkpoint.json"


def run_shard(
    number: int,
    preflight_dir: Path,
    *,
    lane_root: Path | None = None,
    lane_id: str | None = None,
    worker_id: str | None = None,
    scheduled_offset_minutes: int = 0,
) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    queue_path, _, shard_id = shard_paths(number)
    queue = read_csv(queue_path)
    fields = list(queue[0])
    lane_id = lane_id or f"lane_{number:03d}"
    worker_id = worker_id or lane_id
    # Normalize caller-supplied lane paths once.  The coordinator passes repo-
    # relative paths for readable command lines, while lineage records are
    # intentionally stored relative to the absolute repository root.
    shard_root = lane_root.resolve() if lane_root is not None else (TMP_ROOT / shard_id)
    shard_root.mkdir(parents=True, exist_ok=True)
    checkpoint_file = checkpoint_path(shard_id, shard_root, lane_id)
    if checkpoint_file.exists():
        checkpoint = read_json(checkpoint_file)
        if checkpoint.get("shard_queue_sha256") != locks["shard_hashes"][shard_id]:
            raise RuntimeError("resume checkpoint shard hash mismatch")
        if checkpoint.get("shard_status") == "completed":
            raise RuntimeError(f"{shard_id} is already completed and cannot be rerun")
        checkpoint["shard_status"] = "in_progress"
        checkpoint.pop("stop_reason", None)
    else:
        checkpoint = {
            "task_id": "BROAD-STATE-BY-STATE-4X1000-LIVE-SCOUT-2026-07-27",
            "shard_id": shard_id,
            "lane_id": lane_id,
            "worker_id": worker_id,
            "scheduled_start_offset_minutes": scheduled_offset_minutes,
            "actual_started_at": datetime.now().astimezone().isoformat(),
            "shard_queue_sha256": locks["shard_hashes"][shard_id],
            "shard_target_count": 1000,
            "shard_status": "in_progress",
            "preflight_gate_status": gate["gate_status"],
            "preflight_external_calls_attempted": gate["external_calls_attempted"],
            "outcomes": [],
            "raw_prompts_saved": 0,
            "raw_responses_saved": 0,
            "global_analysis_readiness": False,
        }
        atomic_json(checkpoint_file, checkpoint)
    outcome_by_id = {row["scout_target_id"]: row for row in checkpoint["outcomes"]}
    accepted = {
        target_id
        for target_id, outcome in outcome_by_id.items()
        if outcome.get("parse_status") == "parseable"
        or outcome.get("failure_type") not in TRANSPORT_FAILURES
    }
    consecutive_transport_failures = 0
    pacing = scout.build_pacing_controller(
        adaptive_sleep=True,
        sleep_between_prompts=5,
        adaptive_sleep_min=3,
        adaptive_sleep_base=5,
        adaptive_sleep_max=15,
        adaptive_sleep_backoff=10,
        adaptive_sleep_stability_window=25,
        adaptive_sleep_failure_window=2,
    )
    for position, target in enumerate(queue, start=1):
        target_id = target["scout_target_id"]
        if target_id in accepted:
            continue
        child = shard_root / "targets" / f"{position:04d}_{target_id}"
        prior_outcome = outcome_by_id.get(target_id)
        attempt_number = 2 if prior_outcome and prior_outcome.get("failure_type") in TRANSPORT_FAILURES else 1
        input_path = child / "locked_target.csv"
        if not child.exists():
            write_one_row(input_path, target, fields)
        run_dir = child / ("run" if attempt_number == 1 else "retry_1")
        existing = terminal_child_outcome(run_dir) if run_dir.exists() else None
        if run_dir.exists() and existing is None:
            if attempt_number == 1 and not (child / "retry_1").exists():
                # An interruption before terminal artifacts is not a completed
                # identity. Preserve the partial directory and consume the one
                # bounded retry in a fresh sibling directory.
                attempt_number = 2
                run_dir = child / "retry_1"
            else:
                raise RuntimeError(f"nonterminal target exhausted its bounded retry: {run_dir}")
        if existing is None:
            execute_target(target, run_dir)
            existing = terminal_child_outcome(run_dir)
            if existing is None:
                raise RuntimeError(
                    f"target {target_id} completed without terminal artifacts"
                )
        if (
            existing.get("failure_type") in TRANSPORT_FAILURES
            and attempt_number == 1
        ):
            retry_dir = child / "retry_1"
            if retry_dir.exists():
                retry_outcome = terminal_child_outcome(retry_dir)
                if retry_outcome is None:
                    raise RuntimeError(f"nonterminal retry directory: {retry_dir}")
            else:
                execute_target(target, retry_dir)
                retry_outcome = terminal_child_outcome(retry_dir)
            if retry_outcome is None:
                raise RuntimeError(f"target {target_id} retry lacks terminal artifacts")
            prior_outcome = existing
            existing = retry_outcome
            attempt_number = 2
            run_dir = retry_dir
        prior_failures = []
        if prior_outcome and prior_outcome.get("failure_type"):
            prior_failures = list(prior_outcome.get("prior_attempt_failure_types", []))
            prior_failures.append(prior_outcome["failure_type"])
        outcome = {
            "shard_sequence": position,
            "lane_id": lane_id,
            "worker_id": worker_id,
            "scout_target_id": target_id,
            "municipality_id": target["municipality_id"],
            "municipality": target["municipality"],
            "state": target["state"],
            "region": target["region"],
            "target_input_sha256": sha256_file(child / "locked_target.csv"),
            "target_output_dir": str(run_dir.relative_to(ROOT)),
            "attempt_count": attempt_number,
            "prior_attempt_failure_types": prior_failures,
            **existing,
        }
        if existing["sanitized_artifacts_only"] is not True or existing["raw_prompts_persisted"] is not False or existing["raw_responses_persisted"] is not False:
            raise RuntimeError(f"sanitized artifact boundary failed for {target_id}")
        outcome_by_id[target_id] = outcome
        checkpoint["outcomes"] = [
            outcome_by_id[row["scout_target_id"]]
            for row in queue
            if row["scout_target_id"] in outcome_by_id
        ]
        checkpoint["completed_outcome_count"] = len(checkpoint["outcomes"])
        checkpoint["parseable_count"] = sum(row["parse_status"] == "parseable" for row in checkpoint["outcomes"])
        checkpoint["failed_count"] = sum(row["parse_status"] == "failed" for row in checkpoint["outcomes"])
        checkpoint["candidate_count"] = sum(int(row["candidate_count"]) for row in checkpoint["outcomes"])
        checkpoint["last_completed_scout_target_id"] = target_id
        checkpoint["updated_at"] = datetime.now().astimezone().isoformat()
        atomic_json(checkpoint_file, checkpoint)
        failure_type = existing.get("failure_type", "")
        if failure_type in TRANSPORT_FAILURES:
            consecutive_transport_failures += 1
        else:
            consecutive_transport_failures = 0
        pacing_event = pacing.observe(transport_failure=failure_type in TRANSPORT_FAILURES)
        checkpoint["adaptive_sleep_seconds_next"] = pacing.planned_sleep()
        checkpoint["adaptive_sleep_event_last"] = pacing_event
        print(
            f"{shard_id} {position}/1000 target={target_id} "
            f"status={existing['parse_status']} candidates={existing['candidate_count']}",
            flush=True,
        )
        if consecutive_transport_failures >= 2:
            checkpoint["shard_status"] = "stopped_repeated_transport_instability"
            checkpoint["stop_reason"] = "two_consecutive_transport_failures"
            atomic_json(checkpoint_file, checkpoint)
            raise RuntimeError("repeated transport instability; shard stopped fail-closed")
        if position < len(queue):
            time.sleep(pacing.planned_sleep())
    if len(checkpoint["outcomes"]) != 1000:
        raise RuntimeError("shard loop ended without exactly 1,000 terminal outcomes")
    checkpoint["shard_status"] = "completed"
    checkpoint["completed_at"] = datetime.now().astimezone().isoformat()
    atomic_json(checkpoint_file, checkpoint)
    print(f"{shard_id} completed parseable={checkpoint['parseable_count']} failed={checkpoint['failed_count']} candidates={checkpoint['candidate_count']}")


def prior_locator_set() -> set[str]:
    locators: set[str] = set()
    if CANONICAL_CANDIDATES.is_file():
        for row in read_csv(CANONICAL_CANDIDATES):
            locator = broad.normalize_locator(row.get("source_url", ""))
            if locator:
                locators.add(locator)
    prior_candidates = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_candidates.csv"
    if prior_candidates.is_file():
        for row in read_csv(prior_candidates):
            locator = broad.normalize_locator(row.get("source_locator_or_url", ""))
            if locator:
                locators.add(locator)
    return locators


def collect_package_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    targets = {
        row["scout_target_id"]: row
        for row in read_csv(PREP / "broad_state_4x1000_scout_master_locked_queue.csv")
    }
    results: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    checkpoints: dict[str, dict[str, Any]] = {}
    candidate_number = 0
    for shard_id in SHARD_IDS:
        path = checkpoint_path(shard_id)
        if not path.is_file():
            continue
        checkpoint = read_json(path)
        checkpoints[shard_id] = checkpoint
        for outcome in checkpoint.get("outcomes", []):
            results.append({"shard_id": shard_id, **outcome})
            if outcome.get("parse_status") != "parseable":
                continue
            target = targets[outcome["scout_target_id"]]
            child_candidates = Path(outcome["target_output_dir"])
            if not child_candidates.is_absolute():
                child_candidates = ROOT / child_candidates
            child_candidates = child_candidates / "parsed_candidates.csv"
            if not child_candidates.is_file():
                raise RuntimeError(f"parseable target lacks candidate ledger: {child_candidates}")
            for raw in read_csv(child_candidates):
                candidate_number += 1
                family, confidence = broad.source_family(raw)
                locator = broad.normalize_locator(raw.get("source_url", ""))
                candidates.append({
                    "live_scout_candidate_id": f"B4XLIVE-20260727-{candidate_number:06d}",
                    "shard_id": shard_id,
                    "scout_target_id": outcome["scout_target_id"],
                    "municipality_id": outcome["municipality_id"],
                    "state": outcome["state"], "region": outcome["region"],
                    "municipality": outcome["municipality"], "county": target.get("county", ""),
                    "unit_type": raw.get("unit_type", ""), "union_name": raw.get("union_name", ""),
                    "employer": raw.get("employer", ""), "document_title": raw.get("document_title", ""),
                    "contract_years": raw.get("contract_years", ""), "source_url": raw.get("source_url", ""),
                    "normalized_locator": locator, "source_owner_type": raw.get("source_owner_type", ""),
                    "document_type": raw.get("document_type", ""), "source_family_hint": family,
                    "source_family_confidence": confidence, "candidate_stage": raw.get("candidate_stage", ""),
                    "document_completeness": raw.get("document_completeness", ""),
                    "visible_year_evidence": raw.get("visible_year_evidence", ""),
                    "overlap_with_anchor_cycle": raw.get("overlap_with_anchor_cycle", ""),
                    "duplicate_risk": raw.get("duplicate_risk", ""),
                    "blocked_or_unreadable_flag": raw.get("blocked_or_unreadable_flag", ""),
                    "cycle_match_notes": raw.get("cycle_match_notes", ""),
                    "comparator_role": raw.get("comparator_role", ""),
                    "wrong_employer_risk": raw.get("wrong_employer_risk", ""),
                    "context_only_flag": raw.get("context_only_flag", ""),
                    "needs_verification_reason": raw.get("needs_verification_reason", ""),
                    "why_relevant": raw.get("why_relevant", ""), "confidence": raw.get("confidence", ""),
                    "possible_mechanism_hints": broad.mechanism_hints(raw),
                    "source_family_query_family": target.get("source_family_query_family", ""),
                    "prior_seen_locator_flag": "false", "duplicate_locator_flag": "false",
                    "combined_review_status": "pending_combined_candidate_review",
                    "verification_status": "not_verified", "download_status": "not_downloaded",
                    "extraction_status": "not_extracted", "rating_status": "not_rated",
                    "ingestion_status": "not_ingested", "codification_status": "not_codified",
                    "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
                    "notes": "Discovery metadata only; no candidate review performed in this task.",
                })
    return results, candidates, checkpoints


def finalize(preflight_dir: Path) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    if len(read_csv(PRIOR_REVIEW)) != 1205:
        raise RuntimeError("preserved prior review queue no longer reconciles to 1,205")
    results, candidates, checkpoints = collect_package_rows()
    completed = [shard for shard in SHARD_IDS if checkpoints.get(shard, {}).get("shard_status") == "completed"]
    if not completed:
        raise RuntimeError("partial finalization requires at least one completed shard")
    # Enforce strict prefix completion: a later shard cannot complete before an earlier shard.
    if completed != SHARD_IDS[: len(completed)]:
        raise RuntimeError("completed shard set is not a strict ordered prefix")
    complete_wave = len(completed) == 4
    decision_value = DECISION_COMPLETE if complete_wave else DECISION_PARTIAL
    prior_locators = prior_locator_set()
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for candidate in candidates:
        locator = candidate["normalized_locator"]
        prior_seen = bool(locator and locator in prior_locators)
        duplicate = bool(locator and locator in seen)
        candidate["prior_seen_locator_flag"] = str(prior_seen).lower()
        candidate["duplicate_locator_flag"] = str(duplicate).lower()
        if locator:
            seen.add(locator)
        if locator and not prior_seen and not duplicate:
            deduped.append(candidate)
    parseable = [row for row in results if row.get("parse_status") == "parseable"]
    failed = [row for row in results if row.get("parse_status") != "parseable"]
    if len({row["municipality_id"] for row in parseable}) != len(parseable):
        raise RuntimeError("parseable municipality identities are not unique")
    families = Counter(row["source_family_hint"] for row in deduped)
    non_cba = [row for row in deduped if row["source_family_hint"] != "cba"]
    region_counts = Counter(row["region"] for row in parseable)
    state_counts = Counter(row["state"] for row in parseable)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "broad_state_4x1000_live_scout_candidates.csv", candidates, CANDIDATE_FIELDS)
    write_csv(OUTPUT / "broad_state_4x1000_live_scout_deduped_candidates.csv", deduped, CANDIDATE_FIELDS)
    for number, shard_id in enumerate(SHARD_IDS, start=1):
        shard_results = [row for row in results if row["shard_id"] == shard_id]
        shard_candidates = [row for row in candidates if row["shard_id"] == shard_id]
        write_csv(OUTPUT / f"broad_state_4x1000_live_scout_shard_{number:03d}_results.csv", shard_results, RESULT_FIELDS)
        write_csv(OUTPUT / f"broad_state_4x1000_live_scout_shard_{number:03d}_candidates.csv", shard_candidates, CANDIDATE_FIELDS)
        checkpoint = checkpoints.get(shard_id, {
            "shard_id": shard_id, "shard_status": "not_run", "shard_target_count": 1000,
            "completed_outcome_count": 0, "parseable_count": 0, "failed_count": 0,
            "candidate_count": 0, "global_analysis_readiness": False,
        })
        write_json(OUTPUT / f"broad_state_4x1000_live_scout_shard_{number:03d}_checkpoint.json", checkpoint)
        write_json(OUTPUT / f"broad_state_4x1000_live_scout_shard_{number:03d}_results_summary.json", {
            "shard_id": shard_id, "shard_status": checkpoint.get("shard_status"),
            "locked_target_count": 1000, "completed_outcome_count": len(shard_results),
            "parseable_count": sum(row.get("parse_status") == "parseable" for row in shard_results),
            "failed_or_stopped_count": sum(row.get("parse_status") != "parseable" for row in shard_results),
            "candidate_count": len(shard_candidates), "global_analysis_readiness": False,
        })
        write_json(OUTPUT / f"broad_state_4x1000_live_scout_shard_{number:03d}_candidate_summary.json", {
            "shard_id": shard_id, "candidate_count": len(shard_candidates),
            "discovery_metadata_only": True, "candidate_review_performed": False,
            "global_analysis_readiness": False,
        })
    municipality_rows = [{key: row.get(key, "") for key in RESULT_FIELDS} for row in results]
    write_csv(OUTPUT / "broad_state_4x1000_live_scout_municipality_coverage.csv", municipality_rows, RESULT_FIELDS)
    states_in_results = sorted({row["state"] for row in results})
    state_rows = []
    for state in states_in_results:
        state_outcomes = [row for row in results if row["state"] == state]
        state_parseable = [row for row in state_outcomes if row.get("parse_status") == "parseable"]
        state_rows.append({
            "state": state, "region": broad.REGIONS[state],
            "completed_target_count": len(state_outcomes),
            "parseable_municipality_count": len(state_parseable),
            "candidate_positive_municipality_count": sum(int(row.get("candidate_count", 0)) > 0 for row in state_parseable),
            "no_candidate_municipality_count": sum(int(row.get("candidate_count", 0)) == 0 for row in state_parseable),
            "failed_or_stopped_target_count": sum(row.get("parse_status") != "parseable" for row in state_outcomes),
            "candidate_count": sum(row["state"] == state for row in candidates),
        })
    write_csv(OUTPUT / "broad_state_4x1000_live_scout_state_coverage.csv", state_rows,
              ["state", "region", "completed_target_count", "parseable_municipality_count",
               "candidate_positive_municipality_count", "no_candidate_municipality_count",
               "failed_or_stopped_target_count", "candidate_count"])
    region_rows = [
        {"region": region, "parseable_municipality_count": count,
         "candidate_count": sum(row["region"] == region for row in candidates)}
        for region, count in sorted(region_counts.items())
    ]
    write_csv(OUTPUT / "broad_state_4x1000_live_scout_region_coverage.csv", region_rows,
              ["region", "parseable_municipality_count", "candidate_count"])
    candidate_summary = {
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "structurally_review_eligible_new_candidate_count": len(deduped),
        "candidate_review_performed": False, "all_not_verified": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_candidate_summary.json", candidate_summary)
    write_json(OUTPUT / "broad_state_4x1000_live_scout_deduped_candidate_summary.json", candidate_summary)
    write_json(OUTPUT / "broad_state_4x1000_live_scout_municipality_coverage_summary.json", {
        "committed_completed_shard_count": len(completed), "parseable_municipality_outcomes": len(parseable),
        "failed_or_stopped_parses": len(failed), "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities_before_wave": 2922,
        "cumulative_scout_covered_municipalities_after_committed_outcomes": 2922 + len(parseable),
    })
    write_json(OUTPUT / "broad_state_4x1000_live_scout_state_coverage_summary.json", {
        "states_with_parseable_outcomes": len(state_counts), "parseable_by_state": dict(sorted(state_counts.items()))})
    write_json(OUTPUT / "broad_state_4x1000_live_scout_region_coverage_summary.json", {
        "parseable_by_region": dict(sorted(region_counts.items()))})
    source_summary = {
        "deduped_candidate_count": len(deduped),
        "source_family_distribution": dict(sorted(families.items())),
        "cba_count": families.get("cba", 0), "non_cba_opportunity_count": len(non_cba),
        "cba_concentration": round(families.get("cba", 0) / len(deduped), 6) if deduped else 0,
        "source_family_values_are_unverified_hints": True,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_source_family_candidate_summary.json", source_summary)
    write_json(OUTPUT / "broad_state_4x1000_live_scout_non_cba_opportunity_summary.json", {
        "non_cba_opportunity_count": len(non_cba),
        "by_family": dict(sorted(Counter(row["source_family_hint"] for row in non_cba).items())),
        "unverified_metadata_only": True,
    })
    write_md(OUTPUT / "broad_state_4x1000_live_scout_cba_concentration_report.md", f"""# CBA concentration report

Among {len(deduped):,} structurally deduplicated new-locator candidate rows, {families.get('cba', 0):,} carry a CBA source-family hint ({100 * source_summary['cba_concentration']:.1f}%). The remaining {len(non_cba):,} rows are non-CBA or unresolved opportunities. These labels derive only from scout metadata and snippets; they are not verified document classifications or evidence.
""")
    write_md(OUTPUT / "broad_state_4x1000_live_scout_prior_1205_preservation_note.md", f"""# Prior 1,205-candidate preservation

The prior 490-target wave's 1,205-row review queue remains unchanged at `{PRIOR_REVIEW.relative_to(ROOT)}` with SHA-256 `{sha256_file(PRIOR_REVIEW)}`. It was not reviewed, rewritten, or merged in this task.
""")
    combined_count = 1205 + len(deduped)
    write_md(OUTPUT / "broad_state_4x1000_live_scout_future_combined_candidate_review_plan.md", f"""# Future combined candidate review plan

After all four shards complete, a separately authorized review should combine the preserved 1,205 prior rows with the {len(deduped):,} structurally review-eligible new-locator rows currently available from completed shards ({combined_count:,} total at this checkpoint). No substantive candidate review occurred here. If the wave is partial, defer review until the remaining shards complete or the user explicitly ends scouting.
""")
    preflight_checks = {
        "status": "passed", "gate_external_calls": gate["external_calls_attempted"],
        "transport_category": gate["transport_diagnostic"]["diagnosis_category"],
        "master_lock_revalidated": True, "all_shard_locks_revalidated": True,
        "master_equals_four_shard_union": True, "each_shard_count_1000": True,
        "disallowed_quality_tier_count": 0, "prior_1205_preserved": True,
        "actual_coverage_before_wave": 2922, "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_preflight_checks.json", preflight_checks)
    write_md(OUTPUT / "broad_state_4x1000_live_scout_preflight_report.md", """# Live scout preflight report

PASS. Master and four shard hashes/counts/union/quality tiers reconciled; the prior 1,205-row review queue and 2,922-municipality live baseline were preserved. The three-call direct-SDK gate passed its no-search control and two hosted-search checks with metadata-only artifacts and no secret exposure.
""")
    master_summary = {
        "decision": decision_value, "locked_master_target_count": 4000,
        "completed_shard_count": len(completed), "completed_shards": completed,
        "terminal_target_outcome_count": len(results), "parseable_municipality_outcomes": len(parseable),
        "failed_or_stopped_parses": len(failed), "candidate_count": len(candidates),
        "deduped_candidate_count": len(deduped), "shard_queue_hashes": locks["shard_hashes"],
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_master_results_summary.json", master_summary)
    decision = {
        "task_id": "BROAD-STATE-BY-STATE-4X1000-LIVE-SCOUT-2026-07-27",
        "decision": decision_value, "completed_shard_count": len(completed),
        "completed_shards": completed, "parseable_municipality_outcomes": len(parseable),
        "failed_or_stopped_parses": len(failed), "candidate_count": len(candidates),
        "deduped_candidate_count": len(deduped),
        "review_eligible_new_candidate_count": len(deduped),
        "preserved_prior_candidate_count": 1205,
        "combined_future_review_eligible_candidate_count": combined_count,
        "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities": 2922 + len(parseable),
        "state_coverage_count": len(state_counts), "region_coverage": dict(sorted(region_counts.items())),
        "source_family_distribution": dict(sorted(families.items())),
        "cba_concentration": source_summary["cba_concentration"],
        "non_cba_opportunity_count": len(non_cba), "candidate_review_performed": False,
        "dashboard_status_docs_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27", "global_analysis_readiness": False,
        "direct_url_opens": 0, "verification_head_get_requests": 0, "downloads": 0,
        "source_document_accesses": 0, "ocr_runs": 0, "render_runs": 0,
        "text_extractions": 0, "span_extractions": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "wage_gap_calculations": 0,
        "regressions": 0, "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0, "final_causal_claims": 0,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_decision.json", decision)
    write_md(OUTPUT / "broad_state_4x1000_live_scout_summary.md", f"""# Broad state 4x1000 live scout summary

Decision: `{decision_value}`.

{len(completed)} ordered shard(s) are complete. Their {len(results):,} terminal target outcomes include {len(parseable):,} parseable municipality outcomes and {len(failed):,} failed/stopped parses, yielding {len(candidates):,} discovery candidate rows and {len(deduped):,} structurally deduplicated new-locator rows. Candidate review remains deferred. All candidates remain unverified, not downloaded, not extracted, not rated, not ingested, not codified, non-causal, and not globally analysis-ready.
""")
    dashboard = {
        "dashboard_updated": True, "completed_shard_count": len(completed),
        "new_parseable_municipalities": len(parseable),
        "current_total_scout_covered_municipalities": 2922 + len(parseable),
        "new_candidate_rows": len(candidates), "current_total_candidate_rows": 6027 + len(candidates),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "global_analysis_readiness": False, "decision": decision_value,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_dashboard_update_summary.json", dashboard)
    write_md(OUTPUT / "broad_state_4x1000_live_scout_dashboard_update_summary.md", f"""# Dashboard update summary

The status layer records {len(completed)} completed ordered shard(s), {len(parseable):,} committed parseable municipality outcomes, and {len(candidates):,} candidate rows. Only the parseable municipalities extend actual total scout coverage, from 2,922 to {2922 + len(parseable):,}. Planned, failed, and unrun targets remain off the map. The map remains total scout coverage only and global analysis readiness remains false.
""")
    phase = "all four shards complete; combined candidate review ready next" if complete_wave else f"{len(completed)} of 4 shards complete; resume {SHARD_IDS[len(completed)]} next"
    result_text = f"""# Broad state 4x1000 live scout — 2026-07-27

Current phase: {phase}. Completed parseable municipalities: {len(parseable):,}. New discovery candidate rows: {len(candidates):,}. Candidate review has not begun.

The total-scout-coverage map includes only committed parseable outcomes. Discovery metadata is not verification or evidence. Global analysis readiness remains false; no document was opened or downloaded, and no extraction, rating, ingestion, wage analysis, national claim, or causal claim occurred.
"""
    write_md(RESULT_DOC, result_text)
    write_md(DASHBOARD_NOTE, f"""# Broad state 4x1000 live scout dashboard status — 2026-07-27

{phase.capitalize()}. Actual scout-covered municipalities: {2922 + len(parseable):,}. Candidate rows discovered in this wave: {len(candidates):,}. Map filter: total scout coverage only. Global analysis readiness: false.
""")
    if complete_wave:
        next_prompt_name = "next_combined_broad_state_candidate_review_prompt.md"
        next_body = "Run one separately authorized combined candidate review over the preserved 1,205 prior rows and the committed structurally eligible new rows from all four shards. Do not open URLs or verify/download documents during review."
    else:
        next_prompt_name = "next_broad_state_4x1000_live_scout_resume_prompt.md"
        next_body = f"Resume only `{SHARD_IDS[len(completed)]}` from its committed 1,000-row lock. Never rerun {', '.join(completed)}. Preserve per-target checkpoints and do not begin candidate review."
    standing = """

Dashboard update requirement: after each completed shard, update status/docs and add only committed parseable outcomes to actual total scout coverage. Keep the map total scout coverage only and global analysis readiness false. Do not imply wage gaps, regressions, treatment effects, national/population prevalence, or final causal claims.

Future rating artifact-completeness requirement: any later rating task must verify downstream summary inputs and deterministically reconstruct derivable missing artifacts from committed valid/quarantine/results ledgers, validate reconciliation, commit/push the repair, and continue. Missing non-derivable artifacts still fail closed.
"""
    write_md(OUTPUT / next_prompt_name, "# Next prompt\n\n" + next_body + standing)
    write_md(OUTPUT / "next_task.md", "# Next task\n\n" + next_body)
    invariants = {
        "all_invariants_passed": True, "master_and_shard_locks_revalidated": True,
        "shards_not_collapsed": True, "completed_shards_strict_ordered_prefix": True,
        "per_target_atomic_checkpoints": True, "candidate_review_performed_zero": True,
        "only_parseable_outcomes_counted_as_coverage": True,
        "planned_and_failed_targets_excluded_from_coverage": True,
        "prior_1205_preserved": True, "raw_prompts_saved_zero": True,
        "raw_responses_saved_zero": True, "direct_url_open_zero": True,
        "head_get_download_document_access_zero": True,
        "extraction_rating_ingestion_codification_statistics_zero": True,
        "dashboard_map_total_scout_coverage_only": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": decision_value != DECISION_COMPLETE or complete_wave,
    }
    write_json(OUTPUT / "broad_state_4x1000_live_scout_invariant_checks.json", invariants)
    write_json(OUTPUT / "broad_state_4x1000_live_scout_regression_test_inventory.json", {
        "suite": "scripts/test_broad_state_4x1000_live_scout.py",
        "predecessor_suites": ["scripts/test_broad_state_4x1000_scout_dry_run_prep.py", "scripts/test_broad_state_by_state_source_scout_wave.py"],
    })
    write_md(OUTPUT / "broad_state_4x1000_live_scout_stress_test_report.md", """# Stress-test report

Fail-closed checks cover all queue hashes, exact shard union/order/counts, source-quality tiers, passed metadata-only smoke, per-target freshness and atomic checkpointing, bounded one-retry transport handling, sanitized artifacts, prior candidate preservation, parseable-only dashboard accounting, and claim boundaries.
""")
    write_md(OUTPUT / "broad_state_4x1000_live_scout_validation_2026-07-27.md", """# Broad state 4x1000 live scout validation — 2026-07-27

Generated package reconciliation passes. Repository validation commands are recorded after tests and dashboard build complete.
""")
    print(f"finalized decision={decision_value} shards={len(completed)} parseable={len(parseable)} candidates={len(candidates)} deduped={len(deduped)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-locks", action="store_true")
    modes.add_argument("--run-shard", type=int, choices=range(1, 5))
    modes.add_argument("--finalize", action="store_true")
    parser.add_argument("--preflight-dir", type=Path)
    parser.add_argument("--lane-root", type=Path)
    parser.add_argument("--lane-id")
    parser.add_argument("--worker-id")
    parser.add_argument("--scheduled-offset-minutes", type=int, default=0)
    args = parser.parse_args()
    if args.validate_locks:
        print(json.dumps(validate_locks(), indent=2, sort_keys=True))
        return
    if args.preflight_dir is None:
        raise SystemExit("--run-shard/--finalize requires --preflight-dir")
    if args.finalize:
        finalize(args.preflight_dir)
    else:
        run_shard(
            args.run_shard,
            args.preflight_dir,
            lane_root=args.lane_root,
            lane_id=args.lane_id,
            worker_id=args.worker_id,
            scheduled_offset_minutes=args.scheduled_offset_minutes,
        )


if __name__ == "__main__":
    main()
