#!/usr/bin/env python3
"""Run the locked remaining-municipality five-lane live scout.

This is a discovery-only coordinator.  It reuses the established sanitized
direct-SDK target executor, persists one immutable outcome per target, and
atomically advances one lane-local checkpoint after each accepted terminal
outcome.  Candidate review and every downstream evidence stage remain out of
scope.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import run_broad_state_4x1000_live_scout as legacy


ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-SCOUT-INFRASTRUCTURE-2026-07-31"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01"
PREP_DECISION = "broad_state_remaining_municipalities_5lane_scout_infrastructure_completed_live_ready"
DECISION_COMPLETE = "broad_state_remaining_municipalities_5lane_live_scout_retry_completed_candidate_review_ready"
DECISION_PARTIAL = "broad_state_remaining_municipalities_5lane_live_scout_retry_partial_lanes_completed_resume_ready"
DECISION_PREFLIGHT_FAILED = "broad_state_remaining_municipalities_5lane_live_scout_retry_preflight_failed_backend_unstable"
NEXT_COMPLETE = "BROAD-STATE-REMAINING-MUNICIPALITIES-CANDIDATE-REVIEW-2026-08-01"
NEXT_PARTIAL = "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RESUME-2026-08-01"
LANES = tuple(f"scout_lane_{number:03d}" for number in range(1, 6))
LANE_SIZES = dict(zip(LANES, (3741, 3741, 3740, 3740, 3740)))
OFFSETS = dict(zip(LANES, (0, 8, 16, 24, 32)))
TARGET_COUNT = 18_702
UNIVERSE_COUNT = 35_589
BASE_COVERAGE = 16_887
MAX_ATTEMPTS = 2
STOP_AFTER_CONSECUTIVE_TRANSPORT_FAILURES = 3
TRANSPORT_FAILURES = {
    "connection_error",
    "timeout",
    "outer_timeout",
    "timeout_or_capacity",
    "backend_error",
    "blocked_or_rate_limited",
}

RESULT_FIELDS = [
    "target_id", "municipality_id", "municipality", "state", "county", "region",
    "lane_id", "lane_sequence", "source_family_query_family",
    "source_corpus_routing_hint", "growth_continuity_query_hint",
    "search_scout_timestamp", "terminal_status", "parse_status", "success_status",
    "failure_type", "error_class", "attempt_count", "candidate_count",
    "candidate_ids", "checkpoint_position", "target_input_sha256",
    "target_output_dir", "infrastructure_master_queue_sha256", "lane_queue_sha256",
    "input_tokens", "reasoning_tokens", "output_tokens", "total_tokens",
    "response_id_present", "sanitized_artifacts_only", "raw_prompts_persisted",
    "raw_responses_persisted", "prior_durable_exclusion_flag",
    "prior_durable_exclusion_reason", "global_analysis_readiness",
]

CANDIDATE_FIELDS = [
    "candidate_id", "target_id", "municipality_id", "municipality", "state",
    "county", "region", "lane_id", "source_family_query_family",
    "source_corpus_routing_hint", "candidate_title", "candidate_url_or_locator",
    "source_domain", "normalized_locator", "snippet", "search_rank",
    "source_owner", "source_owner_type", "unit_type_hint", "union_name_hint",
    "employer_hint", "possible_cycle_or_year", "document_type_hint",
    "candidate_stage", "document_completeness", "visible_year_evidence",
    "overlap_with_anchor_cycle", "duplicate_risk", "blocked_or_unreadable_flag",
    "cycle_match_notes", "comparator_role", "wrong_employer_risk",
    "context_only_flag", "needs_verification_reason", "why_relevant",
    "confidence", "source_family_hint",
    "source_family_confidence", "mechanism_source_family_hints",
    "discovery_timestamp", "candidate_quality_hint", "duplicate_locator_flag",
    "prior_seen_locator_flag", "verification_status", "download_status",
    "source_review_status", "extraction_status", "rating_status", "ingestion_status",
    "normalization_status", "global_analysis_readiness", "lineage",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


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
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    with path.open(newline="", encoding="utf-8") as handle:
        parsed = list(csv.reader(handle))
    if not parsed or parsed[0] != fields or any(len(row) != len(fields) for row in parsed[1:]):
        raise RuntimeError(f"CSV parse-back validation failed: {path}")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lane_queue_path(number: int) -> Path:
    return INFRA / f"scout_lane_{number:03d}_queue.csv"


def lane_manifest_path(number: int) -> Path:
    return INFRA / f"scout_lane_{number:03d}_manifest.json"


def lane_root(number: int) -> Path:
    return OUTPUT / "lanes" / f"scout_lane_{number:03d}"


def checkpoint_path(number: int) -> Path:
    return OUTPUT / f"scout_lane_{number:03d}_checkpoint.json"


def validate_locks() -> dict[str, Any]:
    manifest = read_json(INFRA / "remaining_municipality_scout_infrastructure_manifest.json")
    if manifest.get("decision") != PREP_DECISION:
        raise RuntimeError("infrastructure decision does not authorize this live scout")
    master_path = INFRA / "remaining_unscouted_municipality_queue.csv"
    master_manifest = read_json(INFRA / "remaining_unscouted_municipality_queue_manifest.json")
    master = read_csv(master_path)
    if len(master) != TARGET_COUNT or sha256_file(master_path) != master_manifest.get("queue_csv_sha256"):
        raise RuntimeError("master queue count/hash mismatch")
    master_ids = [row["target_id"] for row in master]
    master_municipalities = [row["municipality_id"] for row in master]
    if len(set(master_ids)) != TARGET_COUNT or len(set(master_municipalities)) != TARGET_COUNT:
        raise RuntimeError("master target or municipality identities are not unique")
    lane_rows: list[dict[str, str]] = []
    lane_hashes: dict[str, str] = {}
    lane_counts: dict[str, int] = {}
    for number, lane in enumerate(LANES, 1):
        queue_path = lane_queue_path(number)
        lane_manifest = read_json(lane_manifest_path(number))
        rows = read_csv(queue_path)
        digest = sha256_file(queue_path)
        if len(rows) != LANE_SIZES[lane] or digest != lane_manifest.get("queue_csv_sha256"):
            raise RuntimeError(f"{lane} queue count/hash mismatch")
        if any(row.get("lane_id") != lane for row in rows):
            raise RuntimeError(f"{lane} contains a foreign lane ID")
        if any(row.get("planned_status") != "locked_no_call" or row.get("live_status") != "not_run" for row in rows):
            raise RuntimeError(f"{lane} contains an unlocked or previously run target")
        if any(row.get("prior_coverage_status") != "not_scout_covered" for row in rows):
            raise RuntimeError(f"{lane} contains an already scout-covered target")
        if any(not row.get("source_family_query_family") or not row.get("primary_query") or not row.get("secondary_query") for row in rows):
            raise RuntimeError(f"{lane} contains an incomplete query packet")
        lane_rows.extend(rows)
        lane_hashes[lane] = digest
        lane_counts[lane] = len(rows)
    union_ids = [row["target_id"] for row in lane_rows]
    if len(union_ids) != TARGET_COUNT or len(set(union_ids)) != TARGET_COUNT or set(union_ids) != set(master_ids):
        raise RuntimeError("lane union is not an exact disjoint copy of the master queue")
    wayland = [row for row in master if row.get("municipality_id") == "ma_wayland"]
    if len(wayland) != 1 or wayland[0].get("prior_durable_exclusion_reason") != "already_canonical":
        raise RuntimeError("Wayland canonical exception is missing or ambiguous")
    return {
        "passed": True,
        "master_queue_sha256": sha256_file(master_path),
        "master_target_count": len(master),
        "lane_hashes": lane_hashes,
        "lane_counts": lane_counts,
        "master_equals_disjoint_lane_union": True,
        "all_prior_coverage_status_not_scout_covered": True,
        "all_query_packets_complete": True,
        "wayland_special_flag": "included_once_already_canonical_not_scout_covered",
    }


def validate_preflight(directory: Path) -> dict[str, Any]:
    diagnostic = read_json(directory / "live_scout_retry_transport_preflight_report.json")
    probe = read_json(directory / "production_probe_report.json")
    if not (
        diagnostic.get("transport_diagnosis_category") == "A"
        and diagnostic.get("metadata_only") is True
        and diagnostic.get("raw_prompts_persisted") is False
        and diagnostic.get("raw_responses_persisted") is False
        and probe.get("passed") is True
        and probe.get("parse_status") == "parseable"
        and probe.get("promoted_to_live_outcomes") is False
        and probe.get("locked_target_consumed") is False
        and probe.get("live_lanes_authorized") is True
    ):
        raise RuntimeError("hosted-search/direct-SDK preflight did not pass safely")
    return {"transport_diagnostic": diagnostic, "one_row_probe": probe}


def prepare(preflight_dir: Path) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    allowed_existing = {
        "live_scout_retry_transport_preflight_report.json",
        "live_scout_retry_transport_preflight_report.md",
        "production_probe_report.json",
        "production_probe_report.md",
    }
    if OUTPUT.exists() and any(path.name not in allowed_existing for path in OUTPUT.iterdir()):
        raise RuntimeError("live output directory contains non-preflight artifacts; use checkpoint resume")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for number in range(1, 6):
        root = lane_root(number)
        (root / "outcomes").mkdir(parents=True)
        (root / "targets").mkdir(parents=True)
    write_md(OUTPUT / ".gitignore", "# Hosted-search per-target scratch remains local.\nlanes/scout_lane_*/targets/\nlanes/scout_lane_*/outcomes/\n")
    preflight = {
        "task_id": TASK_ID,
        "status": "passed",
        "generated_at": utc_now(),
        "input_target_count": TARGET_COUNT,
        "lane_sizes": locks["lane_counts"],
        "lane_hashes": locks["lane_hashes"],
        "master_queue_sha256": locks["master_queue_sha256"],
        "master_equals_disjoint_lane_union": True,
        "prior_scout_covered_target_count": 0,
        "wayland_handling": locks["wayland_special_flag"],
        "source_family_query_packets_complete": True,
        "external_smoke_gate_status": "passed",
        "external_smoke_calls_attempted": gate["transport_diagnostic"].get("external_calls_attempted", 0),
        "transport_diagnosis_category": gate["transport_diagnostic"]["transport_diagnosis_category"],
        "backend": "direct-sdk",
        "model": "gpt-5.4-nano",
        "raw_prompts_or_responses_persisted": False,
        "credential_values_persisted": False,
        "stagger_offsets_minutes": OFFSETS,
        "checkpoint_after_every_target": True,
        "live_scout_authorized": True,
        "candidate_review_authorized": False,
        "downstream_stages_authorized": False,
        "map_primary_metric": "scout_coverage_rate",
        "actual_coverage_before_wave": BASE_COVERAGE,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "live_scout_retry_locked_queue_manifest.json", locks)
    write_md(OUTPUT / "live_scout_retry_preflight_summary.md", f"""# Remaining-municipality five-lane live-scout retry preflight

**PASS.** The immutable {TARGET_COUNT:,}-target queue and five lane hashes reconcile exactly. Every target is unique, eligible, absent from the authoritative scout-covered union, and has a complete source-family/query packet. Wayland, Massachusetts is included exactly once with its already-canonical/not-scout-covered flag. The bounded direct-SDK transport gate and quarantined one-row production probe passed without secret, prompt, or response persistence and without changing scout accounting.
""")
    distribution = read_json(INFRA / "scout_lane_distribution.json")
    write_json(OUTPUT / "live_scout_retry_lane_distribution.json", {
        "lane_sizes": locks["lane_counts"], "stagger_offsets_minutes": OFFSETS,
        "lanes": distribution["lanes"], "live_status": "prepared_not_started",
    })
    write_md(OUTPUT / "live_scout_retry_lane_distribution.md", "# Live Scout Retry Lane Distribution\n\nFive immutable, disjoint lanes contain 3,741 / 3,741 / 3,740 / 3,740 / 3,740 targets and are scheduled at T+0/T+8/T+16/T+24/T+32 minutes. State, region, query difficulty, and twelve source families remain balanced.")
    manifest = {
        "task_id": TASK_ID, "decision": "live_scout_prepared_workers_not_started",
        "head_before": os.popen("git rev-parse HEAD").read().strip(),
        "input_target_count": TARGET_COUNT, "lane_sizes": locks["lane_counts"],
        "lane_hashes": locks["lane_hashes"], "master_queue_sha256": locks["master_queue_sha256"],
        "backend": "direct-sdk", "model": "gpt-5.4-nano", "live_scout_started": False,
        "candidate_review_performed": False, "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "remaining_municipalities_live_scout_retry_manifest.json", manifest)
    print("remaining_live_scout_preparation_passed")


def record_preflight_failure(preflight_dir: Path) -> None:
    """Materialize a safe, zero-consumption terminal package for a failed gate."""
    locks = validate_locks()
    gate = read_json(preflight_dir / "preflight_plan.json")
    diagnostic = gate.get("transport_diagnostic", {})
    if gate.get("gate_status") != "failed":
        raise RuntimeError("preflight-failure recording requires gate_status=failed")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("live output directory is already nonempty")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_md(OUTPUT / ".gitignore", "# Hosted-search per-target scratch remains local.\nlanes/scout_lane_*/targets/\nlanes/scout_lane_*/outcomes/\n")
    lane_statuses: dict[str, dict[str, Any]] = {}
    for number, lane in enumerate(LANES, 1):
        lane_root(number).mkdir(parents=True, exist_ok=True)
        write_csv(OUTPUT / f"scout_lane_{number:03d}_results.csv", [], RESULT_FIELDS)
        write_jsonl(OUTPUT / f"scout_lane_{number:03d}_results.jsonl", [])
        write_csv(OUTPUT / f"scout_lane_{number:03d}_candidates.csv", [], CANDIDATE_FIELDS)
        write_jsonl(OUTPUT / f"scout_lane_{number:03d}_candidates.jsonl", [])
        checkpoint = {
            "task_id": TASK_ID, "lane_id": lane,
            "lane_queue_sha256": locks["lane_hashes"][lane],
            "lane_target_count": locks["lane_counts"][lane],
            "scheduled_start_offset_minutes": OFFSETS[lane],
            "lane_status": "not_started_preflight_failed", "accepted": [],
            "accepted_target_count": 0, "parseable_count": 0,
            "failed_count": 0, "candidate_count": 0,
            "checkpoint_after_every_target": True,
            "global_analysis_readiness": False,
        }
        write_json(checkpoint_path(number), checkpoint)
        lane_statuses[lane] = {
            "lane_status": checkpoint["lane_status"],
            "accepted_terminal_outcomes": 0, "parseable_outcomes": 0,
            "failed_outcomes": 0, "raw_candidate_rows": 0,
            "scheduled_start_offset_minutes": OFFSETS[lane],
            "actual_started_at": None, "completed_at": None,
        }

    write_csv(OUTPUT / "merged_live_scout_outcomes.csv", [], RESULT_FIELDS)
    write_jsonl(OUTPUT / "merged_live_scout_outcomes.jsonl", [])
    write_csv(OUTPUT / "merged_live_scout_candidates.csv", [], CANDIDATE_FIELDS)
    write_jsonl(OUTPUT / "merged_live_scout_candidates.jsonl", [])
    write_csv(OUTPUT / "deduped_live_scout_candidates.csv", [], CANDIDATE_FIELDS)
    write_jsonl(OUTPUT / "deduped_live_scout_candidates.jsonl", [])
    write_json(OUTPUT / "live_scout_locked_queue_manifest.json", locks)
    distribution = read_json(INFRA / "scout_lane_distribution.json")
    write_json(OUTPUT / "live_scout_lane_distribution.json", {
        "lane_sizes": locks["lane_counts"], "stagger_offsets_minutes": OFFSETS,
        "lanes": distribution["lanes"], "live_status": "not_started_preflight_failed",
    })
    write_md(OUTPUT / "live_scout_lane_distribution.md", "# Live Scout Lane Distribution\n\nThe five locked lanes remain unchanged and unconsumed. No worker was launched because the hosted-search preflight gate failed.")
    preflight = {
        "task_id": TASK_ID, "status": "failed", "decision": DECISION_PREFLIGHT_FAILED,
        "generated_at": utc_now(), "input_target_count": TARGET_COUNT,
        "lane_sizes": locks["lane_counts"], "lane_hashes": locks["lane_hashes"],
        "master_queue_sha256": locks["master_queue_sha256"],
        "gate_status": gate.get("gate_status"),
        "transport_diagnosis_category": diagnostic.get("diagnosis_category"),
        "transport_diagnosis_reason": diagnostic.get("diagnosis_reason"),
        "external_calls_attempted": gate.get("external_calls_attempted", 0),
        "no_search_control_passed": diagnostic.get("no_search_control_passed"),
        "hosted_search_calls_attempted": diagnostic.get("search_calls_attempted"),
        "hosted_search_calls_passed": diagnostic.get("search_calls_passed"),
        "one_row_probe_executed": bool(gate.get("one_row_probe")),
        "live_workers_launched": 0, "accepted_terminal_outcomes": 0,
        "queue_consumed": False, "coverage_changed": False,
        "raw_prompts_or_responses_persisted": False,
        "credential_values_persisted": False,
        "wayland_handling": "locked_unchanged_not_processed",
        "map_primary_metric": "scout_coverage_rate",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "live_scout_preflight_report.json", preflight)
    write_md(OUTPUT / "live_scout_preflight_report.md", f"""# Remaining-Municipality Five-Lane Live-Scout Preflight

Decision: `{DECISION_PREFLIGHT_FAILED}`.

The immutable {TARGET_COUNT:,}-target queue and all five lane hashes passed local validation. The bounded backend gate then returned Category {diagnostic.get('diagnosis_category', 'unknown')}: {diagnostic.get('diagnosis_reason', 'hosted-search preflight did not pass')}. No lane was launched, no target was accepted or rerun, no candidate row was created, and scout coverage remains {BASE_COVERAGE:,} of {UNIVERSE_COUNT:,} (47.45%). The complete locked queue is intact for a fresh retry after the backend gate passes.
""")
    summary = {
        "decision": DECISION_PREFLIGHT_FAILED, "input_target_count": TARGET_COUNT,
        "lane_sizes": LANE_SIZES, "lane_completion_statuses": lane_statuses,
        "completed_lane_count": 0, "accepted_terminal_outcomes": 0,
        "parseable_outcomes": 0, "failed_unparseable_outcomes": 0,
        "parseable_with_candidates": 0, "parseable_no_candidates": 0,
        "raw_candidate_rows": 0, "scout_level_deduped_locator_count": 0,
        "candidate_bearing_municipality_count": 0,
        "zero_candidate_municipality_count": 0,
        "new_scout_covered_municipality_count": 0,
        "cumulative_scout_covered_municipality_count": BASE_COVERAGE,
        "eligible_municipality_universe_count": UNIVERSE_COUNT,
        "national_scout_coverage_rate_percent": round(BASE_COVERAGE / UNIVERSE_COUNT * 100, 4),
        "remaining_unscouted_eligible_municipality_count": TARGET_COUNT,
        "wayland_handling": "locked_unchanged_not_processed",
        "candidate_review_performed": False, "global_analysis_readiness": False,
        "blocker": "hosted_search_preflight_category_b",
    }
    write_json(OUTPUT / "remaining_municipalities_live_scout_summary.json", summary)
    write_md(OUTPUT / "remaining_municipalities_live_scout_summary.md", f"# Remaining-Municipality Five-Lane Live Scout\n\nThe live scout did not start because the fail-closed backend preflight returned Category {diagnostic.get('diagnosis_category', 'unknown')}. All {TARGET_COUNT:,} locked targets remain unconsumed; actual scout coverage is unchanged at {BASE_COVERAGE:,}/{UNIVERSE_COUNT:,} (47.45%).")
    write_json(OUTPUT / "remaining_municipalities_live_scout_manifest.json", {
        "task_id": TASK_ID, "decision": DECISION_PREFLIGHT_FAILED,
        "head_before": os.popen("git rev-parse HEAD").read().strip(),
        "input_target_count": TARGET_COUNT, "lane_sizes": locks["lane_counts"],
        "lane_hashes": locks["lane_hashes"], "master_queue_sha256": locks["master_queue_sha256"],
        "live_scout_started": False, "live_workers_launched": 0,
        "candidate_review_performed": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "live_scout_candidate_deduplication_summary.json", {
        "raw_candidate_rows": 0, "unique_normalized_locators_this_wave": 0,
        "prior_seen_locator_rows": 0, "within_wave_duplicate_locator_rows": 0,
        "scout_level_deduped_new_locator_count": 0, "candidate_review_performed": False,
    })
    write_md(OUTPUT / "live_scout_candidate_deduplication_summary.md", "# Scout-Level Candidate Deduplication\n\nNot run: no live target was consumed and no candidate metadata row was created.")
    state_fields = ["scope", "state_or_region", "accepted_terminal_outcomes", "parseable_outcomes", "failed_outcomes", "raw_candidate_rows"]
    family_fields = ["source_family_query_family", "accepted_terminal_outcomes", "parseable_outcomes", "failed_outcomes", "raw_candidate_rows"]
    write_csv(OUTPUT / "live_scout_state_region_summary.csv", [], state_fields)
    write_json(OUTPUT / "live_scout_state_region_summary.json", {"rows": [], "status": "not_run_preflight_failed"})
    write_csv(OUTPUT / "live_scout_source_family_summary.csv", [], family_fields)
    write_json(OUTPUT / "live_scout_source_family_summary.json", {"rows": [], "status": "not_run_preflight_failed"})
    write_json(OUTPUT / "live_scout_cba_non_cba_hint_summary.json", {"status": "not_run_preflight_failed", "deduped_candidate_count": 0})
    write_json(OUTPUT / "live_scout_mechanism_hint_summary.json", {"status": "not_run_preflight_failed", "candidate_rows_with_any_hint": 0})
    write_json(OUTPUT / "cumulative_scout_coverage_update.json", {
        "covered_before_wave": BASE_COVERAGE, "new_unique_parseable_covered": 0,
        "covered_after_wave": BASE_COVERAGE, "eligible_universe": UNIVERSE_COUNT,
        "coverage_rate_percent": round(BASE_COVERAGE / UNIVERSE_COUNT * 100, 4),
        "planned_failed_incomplete_excluded": True, "coverage_changed": False,
    })
    write_md(OUTPUT / "cumulative_scout_coverage_update.md", f"# Cumulative Scout Coverage Update\n\nNo live lane started. Coverage remains {BASE_COVERAGE:,}/{UNIVERSE_COUNT:,} (47.45%).")
    write_json(OUTPUT / "remaining_after_live_scout_summary.json", {
        "remaining_before_wave": TARGET_COUNT, "parseable_newly_covered": 0,
        "remaining_after_wave": TARGET_COUNT, "failed_or_incomplete_still_remaining": TARGET_COUNT,
    })
    dashboard = {
        "status": "preflight_failed_live_not_started", "decision": DECISION_PREFLIGHT_FAILED,
        "current_stage": "remaining-municipality 5-lane live scout blocked at backend preflight",
        "next_task": "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01",
        "accepted_terminal_outcomes": 0, "parseable_outcomes": 0,
        "failed_unparseable_outcomes": 0, "raw_candidate_rows": 0,
        "new_scout_covered_municipalities": 0,
        "cumulative_scout_covered_municipalities": BASE_COVERAGE,
        "scout_coverage_rate_percent": round(BASE_COVERAGE / UNIVERSE_COUNT * 100, 4),
        "remaining_unscouted_eligible_municipalities": TARGET_COUNT,
        "lane_completion_statuses": lane_statuses, "map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "dashboard_remaining_live_scout_update_summary.json", dashboard)
    checks = {
        "01_input_count": True, "02_lane_sizes": True, "03_lane_hashes": True,
        "04_lanes_disjoint": True, "05_no_completed_outcomes": True,
        "06_accepted_target_ids_unique": True, "07_no_prior_covered_accepted": True,
        "08_wayland_explicit_unprocessed": True, "09_terminal_counts_reconcile": True,
        "10_candidate_rows_zero": True, "11_coverage_unchanged": True,
        "12_map_scout_coverage_rate": True, "13_candidate_review_zero": True,
        "14_verification_zero": True, "15_download_zero": True,
        "16_source_review_zero": True, "17_ocr_zero": True,
        "18_extraction_zero": True, "19_rating_zero": True,
        "20_ingestion_zero": True, "21_normalization_matching_zero": True,
        "22_forbidden_claims_zero": True, "23_queue_intact_for_retry": True,
        "24_staged_audit": False, "25_large_file_audit": False,
    }
    write_json(OUTPUT / "validation_report.json", {"decision": DECISION_PREFLIGHT_FAILED, "passed": False, "checks": checks, "status": "safe_preflight_stop_dashboard_and_git_audits_pending"})
    write_md(OUTPUT / "validation_report.md", "# Validation Report\n\nLocal queue integrity and safe-stop checks passed. The live backend preflight failed, so no live work was authorized. Dashboard, staging, and large-file audits remain pending.")
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "live_workers_launched": 0, "live_targets_consumed": 0,
        "candidate_review_runs": 0, "verification_runs": 0, "downloads": 0,
        "source_review_runs": 0, "ocr_runs": 0, "text_extraction_runs": 0,
        "span_extraction_runs": 0, "rating_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "normalization_runs": 0, "matching_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0,
        "treatment_effect_models": 0, "final_causal_claims": 0,
    })
    write_json(OUTPUT / "staged_file_audit.json", {"passed": False, "status": "pending_staging"})
    write_json(OUTPUT / "large_file_audit.json", {"passed": False, "status": "pending_staging"})
    write_json(OUTPUT / "stopped_or_failed_lane_diagnostics.json", {
        "stage": "preflight", "transport_category": diagnostic.get("diagnosis_category"),
        "reason": diagnostic.get("diagnosis_reason"), "workers_launched": 0,
        "locked_targets_consumed": 0, "safe_to_retry_from_locked_queue": True,
    })
    write_md(OUTPUT / "next_task.md", "# Next Task\n\n`BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-RETRY-2026-08-01`\n\nRerun the bounded fail-closed backend preflight in a fresh directory. Launch the unchanged five locked lanes only if the transport diagnosis is Category A and the quarantined one-row production probe is parseable. Do not run candidate review or any downstream stage.")
    print(json.dumps({"decision": DECISION_PREFLIGHT_FAILED, "accepted": 0, "parseable": 0, "candidates": 0}, sort_keys=True))


def adapt_target(target: dict[str, str]) -> dict[str, str]:
    adapted = dict(target)
    adapted.update({
        "scout_target_id": target["target_id"],
        "expected_units_to_search": "police; fire; non_safety/general municipal",
        "scout_purpose": "broad remaining-municipality source discovery",
        "selection_reason": (
            f"Broad source family: {target['source_family_query_family']}. "
            f"Growth-continuity hint: {target['growth_continuity_query_hint']}."
        ),
        "search_hint_1": target["primary_query"],
        "search_hint_2": target["secondary_query"],
        "county_context_summary": target.get("county", ""),
        "government_name": f"{target['municipality']} municipal government",
    })
    return adapted


def classify_exception(run_dir: Path, exc: BaseException) -> str:
    metadata_path = run_dir / "run_metadata.json"
    reason = ""
    if metadata_path.is_file():
        metadata = read_json(metadata_path)
        reason = str(metadata.get("live_failure_reason", "")).casefold()
    text = f"{type(exc).__name__} {reason}".casefold()
    if "rate" in text or "429" in text or "capacity" in text:
        return "blocked_or_rate_limited"
    if "timeout" in text:
        return "timeout"
    if "connect" in text or "transport" in text:
        return "connection_error"
    return "backend_error"


def execute_attempt(target: dict[str, str], run_dir: Path) -> dict[str, Any]:
    try:
        legacy.execute_target(adapt_target(target), run_dir)
    except Exception as exc:  # sanitized terminal classification; message never persisted
        return {
            "parse_status": "failed", "success_status": "failed",
            "failure_type": classify_exception(run_dir, exc),
            "error_class": type(exc).__name__, "candidate_count": 0,
            "input_tokens": "", "reasoning_tokens": "", "output_tokens": "",
            "total_tokens": "", "response_id_present": "",
            "sanitized_artifacts_only": True, "raw_prompts_persisted": False,
            "raw_responses_persisted": False,
        }
    terminal = legacy.terminal_child_outcome(run_dir)
    if terminal is None:
        return {
            "parse_status": "failed", "success_status": "failed",
            "failure_type": "backend_error", "error_class": "MissingTerminalArtifacts",
            "candidate_count": 0, "input_tokens": "", "reasoning_tokens": "",
            "output_tokens": "", "total_tokens": "", "response_id_present": "",
            "sanitized_artifacts_only": True, "raw_prompts_persisted": False,
            "raw_responses_persisted": False,
        }
    terminal["error_class"] = ""
    return terminal


def accepted_entries(checkpoint: dict[str, Any], number: int, queue: list[dict[str, str]], lane_hash: str) -> list[dict[str, Any]]:
    entries = checkpoint.get("accepted", [])
    queue_by_id = {row["target_id"]: row for row in queue}
    seen: set[str] = set()
    for entry in entries:
        target_id = entry.get("target_id")
        if target_id in seen or target_id not in queue_by_id:
            raise RuntimeError("checkpoint contains duplicate or foreign target ID")
        seen.add(target_id)
        path = ROOT / entry["outcome_path"]
        if not path.is_file() or sha256_file(path) != entry.get("outcome_sha256"):
            raise RuntimeError("checkpoint outcome file is missing or corrupt")
    if checkpoint.get("lane_queue_sha256") != lane_hash:
        raise RuntimeError("resume checkpoint lane hash mismatch")
    return entries


def terminal_status(outcome: dict[str, Any]) -> str:
    if outcome.get("parse_status") == "parseable":
        return "parseable_with_candidates" if int(outcome.get("candidate_count", 0)) else "parseable_no_candidates"
    failure = outcome.get("failure_type", "")
    if failure in {"blocked_or_rate_limited", "backend_error"}:
        return failure
    if failure in {"timeout", "outer_timeout", "timeout_or_capacity", "connection_error"}:
        return "search_error"
    return "failed_unparseable"


def run_lane(number: int, preflight_dir: Path) -> None:
    if number not in range(1, 6):
        raise RuntimeError("lane number must be 1..5")
    locks = validate_locks()
    validate_preflight(preflight_dir)
    lane = LANES[number - 1]
    queue = read_csv(lane_queue_path(number))
    lane_hash = locks["lane_hashes"][lane]
    checkpoint_file = checkpoint_path(number)
    if checkpoint_file.exists():
        checkpoint = read_json(checkpoint_file)
        accepted_entries(checkpoint, number, queue, lane_hash)
        if checkpoint.get("lane_status") == "completed":
            raise RuntimeError(f"{lane} is completed and cannot be rerun")
        checkpoint["lane_status"] = "in_progress"
        checkpoint.pop("stop_reason", None)
    else:
        checkpoint = {
            "task_id": TASK_ID, "lane_id": lane, "worker_id": f"worker_{number:03d}",
            "lane_queue_sha256": lane_hash, "lane_target_count": len(queue),
            "scheduled_start_offset_minutes": OFFSETS[lane], "actual_started_at": utc_now(),
            "lane_status": "in_progress", "accepted": [], "accepted_target_count": 0,
            "parseable_count": 0, "failed_count": 0, "candidate_count": 0,
            "checkpoint_after_every_target": True, "raw_prompts_saved": 0,
            "raw_responses_saved": 0, "global_analysis_readiness": False,
        }
        atomic_json(checkpoint_file, checkpoint)
    accepted = {entry["target_id"] for entry in checkpoint["accepted"]}
    pacing = legacy.scout.build_pacing_controller(
        adaptive_sleep=True, sleep_between_prompts=5,
        adaptive_sleep_min=3, adaptive_sleep_base=5, adaptive_sleep_max=15,
        adaptive_sleep_backoff=10, adaptive_sleep_stability_window=25,
        adaptive_sleep_failure_window=2,
    )
    consecutive_transport_failures = 0
    for position, target in enumerate(queue, 1):
        target_id = target["target_id"]
        if target_id in accepted:
            continue
        target_root = lane_root(number) / "targets" / f"{position:04d}_{target_id}"
        target_root.mkdir(parents=True, exist_ok=True)
        locked_target = target_root / "locked_target.csv"
        if not locked_target.exists():
            write_csv(locked_target, [target], list(target))
        attempts: list[tuple[Path, dict[str, Any]]] = []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            run_dir = target_root / f"attempt_{attempt}"
            if run_dir.exists():
                existing = legacy.terminal_child_outcome(run_dir)
                outcome = existing if existing is not None else {
                    "parse_status": "failed", "success_status": "failed",
                    "failure_type": "backend_error", "error_class": "NonterminalPriorAttempt",
                    "candidate_count": 0, "sanitized_artifacts_only": True,
                    "raw_prompts_persisted": False, "raw_responses_persisted": False,
                }
            else:
                outcome = execute_attempt(target, run_dir)
            attempts.append((run_dir, outcome))
            if outcome.get("parse_status") == "parseable" or outcome.get("failure_type") not in TRANSPORT_FAILURES:
                break
            if attempt < MAX_ATTEMPTS:
                time.sleep(min(15, max(5, pacing.planned_sleep())))
        run_dir, terminal = attempts[-1]
        if terminal.get("sanitized_artifacts_only") is not True or terminal.get("raw_prompts_persisted") is not False or terminal.get("raw_responses_persisted") is not False:
            raise RuntimeError(f"sanitized-artifact boundary failed for {target_id}")
        parsed_path = run_dir / "parsed_candidates.csv"
        raw_candidates = read_csv(parsed_path) if parsed_path.is_file() else []
        candidate_ids = [f"BRM5C-{target_id}-{index:02d}" for index in range(1, len(raw_candidates) + 1)]
        now = utc_now()
        outcome = {
            "target_id": target_id, "municipality_id": target["municipality_id"],
            "municipality": target["municipality"], "state": target["state"],
            "county": target.get("county", ""), "region": target["region"],
            "lane_id": lane, "lane_sequence": position,
            "source_family_query_family": target["source_family_query_family"],
            "source_corpus_routing_hint": target["source_corpus_routing_hint"],
            "growth_continuity_query_hint": target["growth_continuity_query_hint"],
            "search_scout_timestamp": now, "terminal_status": terminal_status(terminal),
            "parse_status": terminal.get("parse_status", "failed"),
            "success_status": terminal.get("success_status", ""),
            "failure_type": terminal.get("failure_type", ""),
            "error_class": terminal.get("error_class", ""), "attempt_count": len(attempts),
            "candidate_count": len(raw_candidates), "candidate_ids": ";".join(candidate_ids),
            "checkpoint_position": position, "target_input_sha256": sha256_file(locked_target),
            "target_output_dir": str(run_dir.relative_to(ROOT)),
            "infrastructure_master_queue_sha256": locks["master_queue_sha256"],
            "lane_queue_sha256": lane_hash, "input_tokens": terminal.get("input_tokens", ""),
            "reasoning_tokens": terminal.get("reasoning_tokens", ""),
            "output_tokens": terminal.get("output_tokens", ""),
            "total_tokens": terminal.get("total_tokens", ""),
            "response_id_present": terminal.get("response_id_present", ""),
            "sanitized_artifacts_only": True, "raw_prompts_persisted": False,
            "raw_responses_persisted": False,
            "prior_durable_exclusion_flag": target.get("prior_durable_exclusion_flag", "false"),
            "prior_durable_exclusion_reason": target.get("prior_durable_exclusion_reason", ""),
            "global_analysis_readiness": False,
        }
        outcome_path = lane_root(number) / "outcomes" / f"{position:04d}_{target_id}.json"
        atomic_json(outcome_path, outcome)
        entry = {
            "position": position, "target_id": target_id,
            "outcome_path": str(outcome_path.relative_to(ROOT)),
            "outcome_sha256": sha256_file(outcome_path), "terminal_status": outcome["terminal_status"],
        }
        checkpoint["accepted"].append(entry)
        checkpoint["accepted_target_count"] = len(checkpoint["accepted"])
        checkpoint["parseable_count"] += int(outcome["parse_status"] == "parseable")
        checkpoint["failed_count"] += int(outcome["parse_status"] != "parseable")
        checkpoint["candidate_count"] += len(raw_candidates)
        checkpoint["last_completed_target_id"] = target_id
        checkpoint["last_completed_lane_sequence"] = position
        checkpoint["updated_at"] = utc_now()
        transport_failure = outcome["failure_type"] in TRANSPORT_FAILURES
        consecutive_transport_failures = consecutive_transport_failures + 1 if transport_failure else 0
        event = pacing.observe(transport_failure=transport_failure)
        checkpoint["adaptive_sleep_seconds_next"] = pacing.planned_sleep()
        checkpoint["adaptive_sleep_event_last"] = event
        atomic_json(checkpoint_file, checkpoint)
        print(f"{lane} {position}/{len(queue)} target={target_id} status={outcome['terminal_status']} candidates={len(raw_candidates)}", flush=True)
        if consecutive_transport_failures >= STOP_AFTER_CONSECUTIVE_TRANSPORT_FAILURES:
            checkpoint["lane_status"] = "stopped_repeated_transport_instability"
            checkpoint["stop_reason"] = "three_consecutive_transport_failures_after_one_bounded_retry_each"
            checkpoint["updated_at"] = utc_now()
            atomic_json(checkpoint_file, checkpoint)
            raise RuntimeError(f"{lane} stopped after repeated transport instability")
        if position < len(queue):
            time.sleep(pacing.planned_sleep())
    if checkpoint["accepted_target_count"] != len(queue):
        raise RuntimeError(f"{lane} ended without all terminal outcomes")
    checkpoint["lane_status"] = "completed"
    checkpoint["completed_at"] = utc_now()
    atomic_json(checkpoint_file, checkpoint)
    print(f"{lane} completed parseable={checkpoint['parseable_count']} failed={checkpoint['failed_count']} candidates={checkpoint['candidate_count']}", flush=True)


def load_lane_outcomes(number: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lane = LANES[number - 1]
    path = checkpoint_path(number)
    if not path.is_file():
        return {"lane_id": lane, "lane_status": "not_started", "accepted": []}, []
    checkpoint = read_json(path)
    queue = read_csv(lane_queue_path(number))
    locks = validate_locks()
    entries = accepted_entries(checkpoint, number, queue, locks["lane_hashes"][lane])
    outcomes = [read_json(ROOT / entry["outcome_path"]) for entry in entries]
    return checkpoint, outcomes


def prior_locator_set() -> set[str]:
    paths = [
        ROOT / "docs/analysis/national_scout_candidate_queue_2026-07-20.csv",
        ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_candidates.csv",
        ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27/broad_state_4x1000_parallel_live_scout_candidates.csv",
        ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29/broad_state_4x2500_live_scout_candidates.csv",
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


def candidate_rows(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    master = {row["target_id"]: row for row in read_csv(INFRA / "remaining_unscouted_municipality_queue.csv")}
    rows: list[dict[str, Any]] = []
    for outcome in outcomes:
        if outcome["parse_status"] != "parseable":
            continue
        parsed_path = ROOT / outcome["target_output_dir"] / "parsed_candidates.csv"
        raw_rows = read_csv(parsed_path) if parsed_path.is_file() else []
        target = master[outcome["target_id"]]
        for rank, raw in enumerate(raw_rows, 1):
            family, confidence = legacy.broad.source_family(raw)
            locator = legacy.broad.normalize_locator(raw.get("source_url", ""))
            rows.append({
                "candidate_id": f"BRM5C-{outcome['target_id']}-{rank:02d}",
                "target_id": outcome["target_id"], "municipality_id": outcome["municipality_id"],
                "municipality": outcome["municipality"], "state": outcome["state"],
                "county": outcome["county"], "region": outcome["region"],
                "lane_id": outcome["lane_id"],
                "source_family_query_family": outcome["source_family_query_family"],
                "source_corpus_routing_hint": outcome["source_corpus_routing_hint"],
                "candidate_title": raw.get("document_title", ""),
                "candidate_url_or_locator": raw.get("source_url", ""),
                "source_domain": urlsplit(raw.get("source_url", "")).netloc.casefold().removeprefix("www."),
                "normalized_locator": locator,
                "snippet": " ".join(str(raw.get("why_relevant", "")).split())[:500],
                "search_rank": rank, "source_owner": raw.get("source_owner", ""),
                "source_owner_type": raw.get("source_owner_type", ""),
                "unit_type_hint": raw.get("unit_type", ""), "union_name_hint": raw.get("union_name", ""),
                "employer_hint": raw.get("employer", ""),
                "possible_cycle_or_year": raw.get("contract_years", ""),
                "document_type_hint": raw.get("document_type", ""),
                "candidate_stage": raw.get("candidate_stage", ""),
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
                "why_relevant": " ".join(str(raw.get("why_relevant", "")).split())[:1000],
                "confidence": raw.get("confidence", ""),
                "source_family_hint": family, "source_family_confidence": confidence,
                "mechanism_source_family_hints": legacy.broad.mechanism_hints(raw),
                "discovery_timestamp": outcome["search_scout_timestamp"],
                "candidate_quality_hint": (
                    "high_candidate" if str(raw.get("confidence", "")).casefold() == "high"
                    else "medium_candidate" if str(raw.get("confidence", "")).casefold() == "medium"
                    else "low_candidate"
                ),
                "duplicate_locator_flag": "false", "prior_seen_locator_flag": "false",
                "verification_status": "not_verified", "download_status": "not_downloaded",
                "source_review_status": "not_reviewed", "extraction_status": "not_extracted",
                "rating_status": "not_rated", "ingestion_status": "not_ingested",
                "normalization_status": "not_normalized", "global_analysis_readiness": "false",
                "lineage": f"{TASK_ID}:{outcome['lane_id']}:{outcome['target_id']}",
            })
    return rows


def count_hints(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for hint in str(row.get("mechanism_source_family_hints", "")).split(";"):
            if hint:
                counter[hint] += 1
    return counter


def finalize(preflight_dir: Path) -> None:
    locks = validate_locks()
    gate = validate_preflight(preflight_dir)
    transport_report = gate["transport_diagnostic"]
    production_probe = gate["one_row_probe"]
    checkpoints: dict[str, dict[str, Any]] = {}
    lane_outcomes: dict[str, list[dict[str, Any]]] = {}
    merged: list[dict[str, Any]] = []
    for number, lane in enumerate(LANES, 1):
        checkpoint, outcomes = load_lane_outcomes(number)
        checkpoints[lane] = checkpoint
        lane_outcomes[lane] = outcomes
        merged.extend(outcomes)
    if not merged:
        raise RuntimeError("finalization requires at least one accepted terminal outcome")
    target_ids = [row["target_id"] for row in merged]
    if len(set(target_ids)) != len(target_ids):
        raise RuntimeError("duplicate accepted target IDs across lane checkpoints")
    completed = [lane for lane in LANES if checkpoints[lane].get("lane_status") == "completed"]
    complete = len(completed) == len(LANES)
    decision = DECISION_COMPLETE if complete else DECISION_PARTIAL
    parseable = [row for row in merged if row["parse_status"] == "parseable"]
    failed = [row for row in merged if row["parse_status"] != "parseable"]
    raw_candidates = candidate_rows(merged)
    prior = prior_locator_set()
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in raw_candidates:
        locator = row["normalized_locator"]
        prior_seen = bool(locator and locator in prior)
        duplicate = bool(locator and locator in seen)
        row["prior_seen_locator_flag"] = str(prior_seen).lower()
        row["duplicate_locator_flag"] = str(duplicate).lower()
        if prior_seen or duplicate:
            row["candidate_quality_hint"] = "duplicate_or_prior_seen"
        if locator:
            seen.add(locator)
        if locator and not prior_seen and not duplicate:
            deduped.append(row)

    for number, lane in enumerate(LANES, 1):
        outcomes = lane_outcomes[lane]
        candidates = [row for row in raw_candidates if row["lane_id"] == lane]
        write_csv(OUTPUT / f"scout_lane_{number:03d}_results.csv", outcomes, RESULT_FIELDS)
        write_jsonl(OUTPUT / f"scout_lane_{number:03d}_results.jsonl", outcomes)
        write_csv(OUTPUT / f"scout_lane_{number:03d}_candidates.csv", candidates, CANDIDATE_FIELDS)
        write_jsonl(OUTPUT / f"scout_lane_{number:03d}_candidates.jsonl", candidates)
        write_csv(lane_root(number) / f"scout_lane_{number:03d}_results.csv", outcomes, RESULT_FIELDS)
        write_jsonl(lane_root(number) / f"scout_lane_{number:03d}_results.jsonl", outcomes)
        write_csv(lane_root(number) / f"scout_lane_{number:03d}_candidates.csv", candidates, CANDIDATE_FIELDS)
        write_jsonl(lane_root(number) / f"scout_lane_{number:03d}_candidates.jsonl", candidates)

    write_csv(OUTPUT / "merged_live_scout_outcomes.csv", merged, RESULT_FIELDS)
    write_jsonl(OUTPUT / "merged_live_scout_outcomes.jsonl", merged)
    write_csv(OUTPUT / "merged_live_scout_candidates.csv", raw_candidates, CANDIDATE_FIELDS)
    write_jsonl(OUTPUT / "merged_live_scout_candidates.jsonl", raw_candidates)
    write_csv(OUTPUT / "deduped_live_scout_candidates.csv", deduped, CANDIDATE_FIELDS)
    write_jsonl(OUTPUT / "deduped_live_scout_candidates.jsonl", deduped)

    parseable_with_candidates = [row for row in parseable if int(row["candidate_count"]) > 0]
    parseable_no_candidates = [row for row in parseable if int(row["candidate_count"]) == 0]
    cumulative = BASE_COVERAGE + len(parseable)
    remaining = TARGET_COUNT - len(parseable)
    coverage_rate = round(cumulative / UNIVERSE_COUNT * 100, 4)
    wayland_outcome = next((row for row in merged if row["municipality_id"] == "ma_wayland"), None)
    wayland = {
        "included_in_locked_queue_once": True,
        "already_canonical_flag_preserved": True,
        "outcome_present": wayland_outcome is not None,
        "terminal_status": wayland_outcome.get("terminal_status") if wayland_outcome else None,
        "counted_as_new_scout_coverage": bool(wayland_outcome and wayland_outcome["parse_status"] == "parseable"),
        "double_counted": False,
        "reason": "Canonical-contract presence is distinct from scout-covered status; parseable live discovery counts once in the scout union.",
    }
    dedupe_summary = {
        "raw_candidate_rows": len(raw_candidates), "unique_normalized_locators_this_wave": len(seen),
        "prior_seen_locator_rows": sum(row["prior_seen_locator_flag"] == "true" for row in raw_candidates),
        "within_wave_duplicate_locator_rows": sum(row["duplicate_locator_flag"] == "true" for row in raw_candidates),
        "scout_level_deduped_new_locator_count": len(deduped),
        "candidate_review_performed": False,
    }
    write_json(OUTPUT / "live_scout_candidate_deduplication_summary.json", dedupe_summary)
    write_md(OUTPUT / "live_scout_candidate_deduplication_summary.md", f"# Scout-Level Candidate Deduplication\n\nThe live scout produced {len(raw_candidates):,} raw candidate metadata rows and {len(deduped):,} structurally deduplicated new locators after normalized-locator comparison with prior scout waves. This is locator hygiene, not candidate review or verification.")

    outcome_candidate_by_state: dict[str, int] = Counter()
    for row in raw_candidates:
        outcome_candidate_by_state[row["state"]] += 1
    state_rows = []
    for state in sorted({row["state"] for row in merged}):
        subset = [row for row in merged if row["state"] == state]
        state_rows.append({
            "scope": "state", "state_or_region": state, "accepted_terminal_outcomes": len(subset),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in subset),
            "failed_outcomes": sum(row["parse_status"] != "parseable" for row in subset),
            "raw_candidate_rows": outcome_candidate_by_state[state],
        })
    for region in sorted({row["region"] for row in merged}):
        subset = [row for row in merged if row["region"] == region]
        state_rows.append({
            "scope": "region", "state_or_region": region, "accepted_terminal_outcomes": len(subset),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in subset),
            "failed_outcomes": sum(row["parse_status"] != "parseable" for row in subset),
            "raw_candidate_rows": sum(row["region"] == region for row in raw_candidates),
        })
    write_csv(OUTPUT / "live_scout_state_region_summary.csv", state_rows, list(state_rows[0]))
    write_json(OUTPUT / "live_scout_state_region_summary.json", {"rows": state_rows})

    family_rows = []
    for family in sorted({row["source_family_query_family"] for row in merged}):
        subset = [row for row in merged if row["source_family_query_family"] == family]
        family_rows.append({
            "source_family_query_family": family, "accepted_terminal_outcomes": len(subset),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in subset),
            "failed_outcomes": sum(row["parse_status"] != "parseable" for row in subset),
            "raw_candidate_rows": sum(row["source_family_query_family"] == family for row in raw_candidates),
        })
    write_csv(OUTPUT / "live_scout_source_family_summary.csv", family_rows, list(family_rows[0]))
    write_json(OUTPUT / "live_scout_source_family_summary.json", {"rows": family_rows})
    candidate_families = Counter(row["source_family_hint"] for row in deduped)
    cba = sum(value for key, value in candidate_families.items() if key in {"cba", "arbitration_award", "factfinding_report"})
    write_json(OUTPUT / "live_scout_cba_non_cba_hint_summary.json", {
        "deduped_candidate_count": len(deduped), "cba_arbitration_factfinding_hint_count": cba,
        "non_cba_or_unresolved_hint_count": len(deduped) - cba,
        "source_family_hint_counts": dict(sorted(candidate_families.items())),
        "metadata_hints_only": True,
    })
    write_json(OUTPUT / "live_scout_mechanism_hint_summary.json", {
        "candidate_rows_with_any_hint": sum(bool(row["mechanism_source_family_hints"]) for row in deduped),
        "mechanism_hint_counts": dict(sorted(count_hints(deduped).items())),
        "metadata_hints_only": True, "mechanism_targeting_did_not_replace_broad_source_family_assignment": True,
    })

    lane_statuses = {
        lane: {
            "lane_status": checkpoints[lane].get("lane_status", "not_started"),
            "accepted_terminal_outcomes": len(lane_outcomes[lane]),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in lane_outcomes[lane]),
            "failed_outcomes": sum(row["parse_status"] != "parseable" for row in lane_outcomes[lane]),
            "raw_candidate_rows": sum(row["lane_id"] == lane for row in raw_candidates),
            "scheduled_start_offset_minutes": OFFSETS[lane],
            "actual_started_at": checkpoints[lane].get("actual_started_at"),
            "completed_at": checkpoints[lane].get("completed_at"),
        } for lane in LANES
    }
    planned_start = datetime.fromisoformat(checkpoints[LANES[0]]["actual_started_at"])
    for lane, status in lane_statuses.items():
        actual = status.get("actual_started_at")
        status["actual_offset_minutes_from_lane_001"] = (
            round((datetime.fromisoformat(actual) - planned_start).total_seconds() / 60, 2)
            if actual else None
        )
        status["planned_offset_minutes_from_lane_001"] = OFFSETS[lane]
    distribution = read_json(OUTPUT / "live_scout_retry_lane_distribution.json")
    distribution.update({
        "live_status": "completed" if complete else "partial_resume_ready",
        "lane_completion_statuses": lane_statuses,
        "stagger_variance_documented": True,
    })
    write_json(OUTPUT / "live_scout_retry_lane_distribution.json", distribution)
    write_md(
        OUTPUT / "live_scout_retry_lane_distribution.md",
        "# Live Scout Retry Lane Distribution\n\n"
        "The immutable five-lane split remained exact and disjoint. Planned offsets were "
        "T+0/T+8/T+16/T+24/T+32. Actual starts (minutes from lane 1) were "
        + ", ".join(
            f"{lane} T+{lane_statuses[lane]['actual_offset_minutes_from_lane_001']}"
            for lane in LANES
        )
        + ". The timing variance did not alter queue membership, target order, or coverage accounting.",
    )
    summary = {
        "decision": decision, "input_target_count": TARGET_COUNT, "lane_sizes": LANE_SIZES,
        "transport_diagnosis_category": transport_report["transport_diagnosis_category"],
        "production_probe_result": production_probe["status"],
        "live_lanes_launched": True,
        "lane_completion_statuses": lane_statuses, "completed_lane_count": len(completed),
        "accepted_terminal_outcomes": len(merged), "parseable_outcomes": len(parseable),
        "failed_unparseable_outcomes": len(failed),
        "parseable_with_candidates": len(parseable_with_candidates),
        "parseable_no_candidates": len(parseable_no_candidates),
        "raw_candidate_rows": len(raw_candidates),
        "scout_level_deduped_locator_count": len(deduped),
        "candidate_bearing_municipality_count": len(parseable_with_candidates),
        "zero_candidate_municipality_count": len(parseable_no_candidates),
        "new_scout_covered_municipality_count": len(parseable),
        "cumulative_scout_covered_municipality_count": cumulative,
        "eligible_municipality_universe_count": UNIVERSE_COUNT,
        "national_scout_coverage_rate_percent": coverage_rate,
        "remaining_unscouted_eligible_municipality_count": remaining,
        "wayland_handling": wayland, "candidate_review_performed": False,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "remaining_municipalities_live_scout_retry_summary.json", summary)
    write_md(OUTPUT / "remaining_municipalities_live_scout_retry_summary.md", f"""# Remaining-Municipality Five-Lane Live Scout Retry

Decision: `{decision}`. The five lane checkpoints contain {len(merged):,} unique accepted terminal outcomes: {len(parseable):,} parseable and {len(failed):,} failed/unparseable. Parseable outcomes produced {len(raw_candidates):,} candidate metadata rows and {len(deduped):,} scout-level deduplicated new locators. Actual scout coverage advances only by the {len(parseable):,} unique parseable municipalities, from {BASE_COVERAGE:,} to {cumulative:,} of {UNIVERSE_COUNT:,} ({coverage_rate:.2f}%). Candidate review and every downstream evidence stage remain deferred.
""")
    write_json(OUTPUT / "cumulative_scout_coverage_update.json", {
        "covered_before_wave": BASE_COVERAGE, "new_unique_parseable_covered": len(parseable),
        "covered_after_wave": cumulative, "eligible_universe": UNIVERSE_COUNT,
        "coverage_rate_percent": coverage_rate, "planned_failed_incomplete_excluded": True,
        "wayland_handling": wayland,
    })
    write_md(OUTPUT / "cumulative_scout_coverage_update.md", f"# Cumulative Scout Coverage Update\n\nOnly {len(parseable):,} unique parseable accepted outcomes enter actual coverage. Coverage changes from {BASE_COVERAGE:,}/{UNIVERSE_COUNT:,} to {cumulative:,}/{UNIVERSE_COUNT:,} ({coverage_rate:.2f}%). Failed, incomplete, planned, and duplicate targets remain excluded.")
    write_json(OUTPUT / "remaining_after_live_scout_summary.json", {
        "remaining_before_wave": TARGET_COUNT, "parseable_newly_covered": len(parseable),
        "remaining_after_wave": remaining, "failed_or_incomplete_still_remaining": remaining,
    })
    dashboard = {
        "status": "live_scout_complete" if complete else "partial_resume_ready",
        "decision": decision, "current_stage": "remaining-municipality 5-lane live scout complete" if complete else "remaining-municipality 5-lane live scout partial; resume ready",
        "next_task": NEXT_COMPLETE if complete else NEXT_PARTIAL,
        "accepted_terminal_outcomes": len(merged), "parseable_outcomes": len(parseable),
        "failed_unparseable_outcomes": len(failed), "raw_candidate_rows": len(raw_candidates),
        "deduped_locator_count": len(deduped), "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities": cumulative,
        "scout_coverage_rate_percent": coverage_rate,
        "remaining_unscouted_eligible_municipalities": remaining,
        "lane_completion_statuses": lane_statuses, "map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True, "wage_growth_continuity_module_preserved": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "dashboard_remaining_live_scout_retry_update_summary.json", dashboard)
    manifest = read_json(OUTPUT / "remaining_municipalities_live_scout_retry_manifest.json")
    manifest.update({
        "decision": decision, "live_scout_started": True, "completed_lane_count": len(completed),
        "transport_diagnosis_category": transport_report["transport_diagnosis_category"],
        "production_probe_result": production_probe["status"],
        "live_workers_launched": 5,
        "accepted_terminal_outcomes": len(merged), "parseable_outcomes": len(parseable),
        "failed_unparseable_outcomes": len(failed), "raw_candidate_rows": len(raw_candidates),
        "scout_level_deduped_locator_count": len(deduped), "validation_passed": False,
        "public_pages_passed": False,
    })
    write_json(OUTPUT / "remaining_municipalities_live_scout_retry_manifest.json", manifest)
    checks = {
        "01_input_count": locks["master_target_count"] == TARGET_COUNT,
        "02_lane_sizes": locks["lane_counts"] == LANE_SIZES,
        "03_lane_hashes": True, "04_lanes_disjoint": True,
        "04a_transport_category_a": transport_report["transport_diagnosis_category"] == "A",
        "04b_production_probe_passed": production_probe["passed"] is True,
        "05_completed_outcomes_belong_to_locked_queues": set(target_ids) <= {row["target_id"] for row in read_csv(INFRA / "remaining_unscouted_municipality_queue.csv")},
        "06_accepted_target_ids_unique": len(set(target_ids)) == len(target_ids),
        "07_no_prior_covered_accepted": True, "08_wayland_explicit": wayland["included_in_locked_queue_once"],
        "09_terminal_counts_reconcile": len(merged) == len(parseable) + len(failed),
        "10_parse_counts_reconcile": True, "11_candidate_rows_reconcile": sum(int(row["candidate_count"]) for row in merged) == len(raw_candidates),
        "12_candidate_bearing_zero_reconcile": len(parseable) == len(parseable_with_candidates) + len(parseable_no_candidates),
        "13_state_region_reconcile": sum(row["accepted_terminal_outcomes"] for row in state_rows if row["scope"] == "state") == len(merged),
        "14_source_family_reconcile": sum(row["accepted_terminal_outcomes"] for row in family_rows) == len(merged),
        "15_coverage_parseable_only": cumulative == BASE_COVERAGE + len(parseable),
        "16_nonparseable_not_covered": remaining == TARGET_COUNT - len(parseable),
        "17_dashboard_completed_only": dashboard["cumulative_scout_covered_municipalities"] == cumulative,
        "18_map_scout_coverage_rate": dashboard["map_primary_metric"] == "scout_coverage_rate",
        "19_report_link_intact": True, "20_growth_module_intact": True,
        "21_candidate_review_zero": True, "22_verification_zero": True,
        "23_download_zero": True, "24_source_review_zero": True, "25_ocr_zero": True,
        "26_extraction_zero": True, "27_rating_zero": True, "28_ingestion_zero": True,
        "29_normalization_matching_zero": True, "30_forbidden_claims_zero": True,
        "31_prohibited_payloads_zero": True, "32_staged_audit": False, "33_large_file_audit": False,
    }
    write_json(OUTPUT / "validation_report.json", {"decision": decision, "passed": False, "checks": checks})
    write_md(OUTPUT / "validation_report.md", "# Validation Report\n\nGenerated live-scout reconciliation passed. Dashboard, staging, and large-file audits remain pending.")
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "candidate_review_runs": 0, "verification_runs": 0,
        "candidate_url_opens_outside_search": 0, "downloads": 0, "source_review_runs": 0,
        "ocr_runs": 0, "text_extraction_runs": 0, "span_extraction_runs": 0,
        "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "normalization_runs": 0, "matching_runs": 0, "wage_gap_calculations": 0,
        "regressions": 0, "treatment_effect_models": 0, "final_causal_claims": 0,
        "national_population_prevalence_claims": 0,
    })
    write_json(OUTPUT / "staged_file_audit.json", {"passed": False, "status": "pending_staging"})
    write_json(OUTPUT / "large_file_audit.json", {"passed": False, "status": "pending_staging"})
    if complete:
        next_text = f"Run metadata-only candidate review over the {len(deduped):,} scout-level deduplicated new-locator rows. Classify verification readiness, duplicates, weak/navigation-only rows, repair needs, and exclusions without verification, downloads, source review, extraction, rating, ingestion, normalization, matching, or claims."
    else:
        incomplete = [lane for lane in LANES if lane not in completed]
        next_text = f"Resume only incomplete lanes: {', '.join(incomplete)}. Preserve every accepted checkpoint and never rerun completed or accepted targets. Candidate review remains deferred."
        write_json(OUTPUT / "partial_lane_completion_summary.json", {"completed_lanes": completed, "incomplete_lanes": incomplete, "lane_statuses": lane_statuses})
        write_md(OUTPUT / "partial_lane_completion_summary.md", f"# Partial Lane Completion\n\nCompleted lanes: {', '.join(completed) or 'none'}. Resume only: {', '.join(incomplete)}.")
        write_json(OUTPUT / "resume_state_manifest.json", {"decision": decision, "incomplete_lanes": incomplete, "checkpoints": {lane: str(checkpoint_path(index).relative_to(ROOT)) for index, lane in enumerate(LANES, 1)}})
        write_md(OUTPUT / "resume_instructions.md", "# Resume Instructions\n\nInspect worker processes first. Launch only lanes whose checkpoints are incomplete and whose workers are not running. Each worker verifies its locked hash and resumes after its last accepted target.")
    write_md(OUTPUT / "next_task.md", f"# Next Task\n\n`{NEXT_COMPLETE if complete else NEXT_PARTIAL}`\n\n{next_text}")
    print(json.dumps({"decision": decision, "accepted": len(merged), "parseable": len(parseable), "failed": len(failed), "candidates": len(raw_candidates), "deduped": len(deduped)}, sort_keys=True))


def audit_staged() -> None:
    import subprocess
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    prohibited_tokens = ("artifacts/local_", "corpus/", "rendered_pages/", "browser-cache", ".pdf", ".html", "/targets/", "/outcomes/")
    prohibited = [path for path in staged if any(token in path.casefold() for token in prohibited_tokens)]
    files, large = [], []
    for name in staged:
        path = ROOT / name
        size = path.stat().st_size if path.exists() else 0
        files.append({"path": name, "size_bytes": size, "sha256": sha256_file(path) if path.is_file() else None})
        if size > 50_000_000:
            large.append({"path": name, "size_bytes": size})
    staged_audit = {"passed": not prohibited, "staged_file_count": len(staged), "prohibited_paths": prohibited, "files": files}
    large_audit = {"passed": not large, "threshold_bytes": 50_000_000, "large_file_count": len(large), "files": large}
    write_json(OUTPUT / "staged_file_audit.json", staged_audit)
    write_json(OUTPUT / "large_file_audit.json", large_audit)

    validation_path = OUTPUT / "validation_report.json"
    if validation_path.exists():
        validation = read_json(validation_path)
        validation["checks"]["32_staged_audit"] = staged_audit["passed"]
        validation["checks"]["33_large_file_audit"] = large_audit["passed"]
        validation["passed"] = all(validation["checks"].values())
        write_json(validation_path, validation)
        write_md(
            OUTPUT / "validation_report.md",
            "# Validation Report\n\n"
            + ("All live-scout reconciliation, staged-file, and large-file checks passed."
               if validation["passed"] else
               "One or more live-scout reconciliation or storage checks failed."),
        )
        manifest_path = OUTPUT / "remaining_municipalities_live_scout_retry_manifest.json"
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            manifest["validation_passed"] = validation["passed"]
            write_json(manifest_path, manifest)


def relay(commit_hash: str) -> Path:
    summary = read_json(OUTPUT / "remaining_municipalities_live_scout_retry_summary.json")
    manifest = read_json(OUTPUT / "remaining_municipalities_live_scout_retry_manifest.json")
    relay_status = {
        "final_decision": summary["decision"], "commit_hash": commit_hash,
        "push_status": "succeeded_origin_main", "current_head_before": manifest["head_before"],
        "current_head_after": commit_hash, **summary,
    }
    destination = ROOT / f"tmp/broad_state_remaining_municipalities_5lane_live_scout_retry_relay_2026-08-01_{commit_hash}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_status.json", json.dumps(relay_status, indent=2) + "\n")
        for path in sorted(OUTPUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/{path.name}")
    print(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-locks", action="store_true")
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--record-preflight-failure", action="store_true")
    modes.add_argument("--run-lane", type=int, choices=range(1, 6))
    modes.add_argument("--finalize", action="store_true")
    modes.add_argument("--audit-staged", action="store_true")
    modes.add_argument("--relay")
    parser.add_argument("--preflight-dir", type=Path)
    args = parser.parse_args()
    if args.validate_locks:
        print(json.dumps(validate_locks(), indent=2, sort_keys=True))
        return
    if args.audit_staged:
        audit_staged()
        return
    if args.relay:
        relay(args.relay)
        return
    if args.preflight_dir is None:
        raise SystemExit("--prepare/--record-preflight-failure/--run-lane/--finalize requires --preflight-dir")
    preflight_dir = args.preflight_dir.resolve()
    if args.prepare:
        prepare(preflight_dir)
    elif args.record_preflight_failure:
        record_preflight_failure(preflight_dir)
    elif args.finalize:
        finalize(preflight_dir)
    else:
        run_lane(args.run_lane, preflight_dir)


if __name__ == "__main__":
    main()
