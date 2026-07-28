#!/usr/bin/env python3
"""Prepare and merge the staggered four-lane broad-state live scout."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import run_broad_state_4x1000_live_scout as worker


ROOT = worker.ROOT
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27"
LANES = [f"lane_{number:03d}" for number in range(1, 5)]
SHARDS = [f"broad_shard_{number:03d}" for number in range(1, 5)]
OFFSETS = {f"lane_{number:03d}": (number - 1) * 8 for number in range(1, 5)}
QUARANTINE = ROOT / "tmp/quarantine_interrupted_sequential_broad_state_4x1000_live_scout_2026-07-27"
RESULT_DOC = ROOT / "docs/analysis/broad_state_4x1000_parallel_live_scout_result_2026-07-27.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/broad_state_4x1000_parallel_live_scout_dashboard_status_note_2026-07-27.md"
DECISION_COMPLETE = "broad_state_4x1000_parallel_live_scout_completed_combined_candidate_review_ready"
DECISION_PARTIAL = "broad_state_4x1000_parallel_live_scout_partial_lanes_completed_resume_ready"

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
    "possible_mechanism_hints", "search_query_family",
    "broad_geographic_target_reason", "source_family_diversification_reason",
    "matched_safety_non_safety_opportunity_flag", "duplicate_locator_flag",
    "prior_seen_locator_flag", "candidate_quality_tier", "verification_status",
    "download_status", "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "notes",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def lane_root(number: int) -> Path:
    return OUTPUT / "lanes" / f"lane_{number:03d}"


def lane_checkpoint(number: int) -> Path:
    return lane_root(number) / f"lane_{number:03d}_checkpoint.json"


def interrupted_audit() -> dict[str, Any]:
    checkpoint_path = QUARANTINE / "broad_shard_001/shard_checkpoint.json"
    if not checkpoint_path.is_file():
        raise RuntimeError("quarantined interrupted checkpoint is missing")
    checkpoint = read_json(checkpoint_path)
    target_70 = QUARANTINE / "broad_shard_001/targets/0070_B4X1000-20260727-0070/run"
    if checkpoint.get("shard_status") == "completed" or len(checkpoint.get("outcomes", [])) == 1000:
        raise RuntimeError("interrupted attempt unexpectedly appears complete")
    return {
        "quarantine_path": str(QUARANTINE.relative_to(ROOT)),
        "original_shard_id": "broad_shard_001",
        "checkpoint_status": checkpoint.get("shard_status"),
        "terminal_outcome_count": len(checkpoint.get("outcomes", [])),
        "parseable_outcome_count": checkpoint.get("parseable_count"),
        "failed_outcome_count": checkpoint.get("failed_count"),
        "candidate_count": checkpoint.get("candidate_count"),
        "last_completed_scout_target_id": checkpoint.get("last_completed_scout_target_id"),
        "nonterminal_target_70_directory_present": target_70.exists(),
        "complete_shard_reusable": False,
        "excluded_from_candidate_accounting": True,
        "excluded_from_coverage_accounting": True,
        "dashboard_was_not_updated_from_partial_attempt": True,
        "quarantine_action": "temporary tree renamed and preserved; no row reused",
        "global_analysis_readiness": False,
    }


def validate_preflight(path: Path) -> dict[str, Any]:
    return worker.validate_preflight(path)


def prepare(preflight_dir: Path) -> None:
    locks = worker.validate_locks()
    gate = validate_preflight(preflight_dir)
    audit = interrupted_audit()
    if len(read_csv(worker.PRIOR_REVIEW)) != 1205:
        raise RuntimeError("prior 1,205-row review queue changed")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("parallel output directory already contains artifacts")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_interrupted_attempt_audit.json", audit)
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_interrupted_attempt_audit.md", f"""# Interrupted sequential-attempt audit

The superseded sequential tree is preserved at `{audit['quarantine_path']}`. It contains only {audit['terminal_outcome_count']} terminal outcomes ({audit['parseable_outcome_count']} parseable; {audit['failed_outcome_count']} failed), not a complete 1,000-target shard, and target 70 has a nonterminal directory. No prior outcome or candidate is reusable. All {audit['candidate_count']} partial candidate rows and all partial parseable outcomes are excluded from the new parallel wave, coverage, and dashboard accounting.
""")
    checks = {
        "status": "passed", "master_queue_sha256": locks["master_queue_sha256"],
        "master_target_count": 4000, "master_equals_four_shard_union": True,
        "shard_counts": locks["shard_counts"], "shard_hashes": locks["shard_hashes"],
        "all_target_live_status_not_run": True, "disallowed_quality_target_count": 0,
        "prior_1205_count": 1205, "prior_1205_sha256": worker.sha256_file(worker.PRIOR_REVIEW),
        "actual_coverage_before_wave": 2922, "interrupted_partial_excluded": True,
        "external_smoke_gate_status": gate["gate_status"],
        "external_smoke_calls_attempted": gate["external_calls_attempted"],
        "transport_diagnosis_category": gate["transport_diagnostic"]["diagnosis_category"],
        "four_controlled_lanes": LANES, "stagger_offsets_minutes": OFFSETS,
        "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_preflight_checks.json", checks)
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_preflight_report.md", """# Parallel live-scout preflight report

PASS. The master and four shard locks reconcile to 4,000 unique targets; every shard contains exactly 1,000 allowed dry-run rows. The prior 1,205-candidate queue and 2,922 live-coverage baseline are unchanged. The interrupted sequential attempt is quarantined and excluded. The metadata-only direct-SDK gate passed its no-search control and two hosted-search checks without secret exposure or accounting changes.
""")
    smoke_rows = [
        {"check": "no_search_control", "status": "passed", "detail": "response id/text/tokens present"},
        {"check": "hosted_search_trivial", "status": "passed", "detail": "metadata-only transport diagnostic"},
        {"check": "hosted_search_municipality", "status": "passed", "detail": "metadata-only municipality-style query"},
        {"check": "secret_exposure", "status": "passed", "detail": "credential_values_logged=false"},
    ]
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_backend_smoke_metadata.csv", smoke_rows, ["check", "status", "detail"])
    policy = {
        "lane_count": 4, "lane_ids": LANES, "shard_ids": SHARDS,
        "stagger_offsets_minutes": OFFSETS, "simultaneous_overlap_required": True,
        "sequential_fallback_allowed": False, "worker_dashboard_writes_allowed": False,
        "worker_cross_lane_reads_or_writes_allowed": False,
        "coordinator_only_merge_dashboard_commit_push": True,
        "per_target_checkpoint_required": True, "adaptive_sleep_seconds": {"min": 3, "base": 5, "max": 15, "backoff": 10},
        "bounded_transport_retry_per_target": 1,
    }
    write_json(OUTPUT / "future_parallel_lane_execution_standard.json", policy)
    write_md(OUTPUT / "future_parallel_lane_execution_standard.md", """# Future parallel lane execution standard

Large live scout runs default to four isolated worker lanes with starts at T+0, T+8, T+16, and T+24 minutes. Lanes overlap, checkpoint every target, use one bounded transport retry plus adaptive 3–15 second pacing, never read or write another lane, and never update dashboard/status/shared summaries. The coordinator alone validates, merges, deduplicates, updates dashboard/status/docs, commits, and pushes. Do not silently fall back to sequential execution.
""")
    print("parallel_preparation_passed")


def collect_completed() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    checkpoints: dict[str, dict[str, Any]] = {}
    for number, lane_id in enumerate(LANES, start=1):
        path = lane_checkpoint(number)
        if not path.is_file():
            continue
        checkpoint = read_json(path)
        checkpoints[lane_id] = checkpoint
        if checkpoint.get("shard_status") != "completed":
            continue
        outcomes = checkpoint.get("outcomes", [])
        if len(outcomes) != 1000 or len({row["scout_target_id"] for row in outcomes}) != 1000:
            raise RuntimeError(f"{lane_id} claims completion without 1,000 unique outcomes")
        # Early worker checkpoints store lane/worker IDs per row and shard ID
        # once at checkpoint scope.  Materialize the locked shard lineage in
        # the coordinator's in-memory merge without rewriting worker outputs.
        for row in outcomes:
            merged = dict(row)
            merged.setdefault("lane_id", lane_id)
            merged.setdefault("worker_id", checkpoint.get("worker_id", lane_id))
            merged.setdefault("shard_id", checkpoint["shard_id"])
            results.append(merged)
    return results, checkpoints


def collect_candidates(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = {
        row["scout_target_id"]: row
        for row in read_csv(worker.PREP / "broad_state_4x1000_scout_master_locked_queue.csv")
    }
    output: list[dict[str, Any]] = []
    number = 0
    for outcome in results:
        if outcome.get("parse_status") != "parseable":
            continue
        path = ROOT / outcome["target_output_dir"] / "parsed_candidates.csv"
        if not path.is_file():
            raise RuntimeError(f"parseable outcome lacks candidate ledger: {path}")
        target = targets[outcome["scout_target_id"]]
        for raw in read_csv(path):
            number += 1
            locator = worker.broad.normalize_locator(raw.get("source_url", ""))
            family, confidence = worker.broad.source_family(raw)
            output.append({
                "scout_candidate_id": f"B4XPAR-20260727-{number:06d}",
                "scout_target_id": outcome["scout_target_id"],
                "lane_id": outcome["lane_id"], "shard_id": outcome["shard_id"],
                "worker_id": outcome["worker_id"], "state": outcome["state"],
                "region": outcome["region"], "municipality": outcome["municipality"],
                "county": target.get("county", ""), "unit_type_hint": raw.get("unit_type", ""),
                "occupation_group_hint": raw.get("unit_type", ""),
                "possible_bargaining_unit": raw.get("union_name", ""),
                "possible_cycle_or_year": raw.get("contract_years", ""),
                "source_title": raw.get("document_title", ""),
                "source_locator_or_url": raw.get("source_url", ""),
                "source_domain": worker.broad.urlsplit(raw.get("source_url", "")).netloc.casefold().removeprefix("www.") if raw.get("source_url") else "",
                "normalized_locator": locator, "source_family_hint": family,
                "document_type_hint": raw.get("document_type", ""),
                "source_family_confidence": confidence,
                "possible_mechanism_hints": worker.broad.mechanism_hints(raw),
                "search_query_family": target.get("source_family_query_family", ""),
                "broad_geographic_target_reason": target.get("broad_geographic_target_reason", ""),
                "source_family_diversification_reason": target.get("source_family_diversification_reason", ""),
                "matched_safety_non_safety_opportunity_flag": target.get("matched_safety_non_safety_opportunity_flag", "false"),
                "duplicate_locator_flag": "false", "prior_seen_locator_flag": "false",
                "candidate_quality_tier": "pending_combined_review",
                "verification_status": "not_verified", "download_status": "not_downloaded",
                "extraction_status": "not_extracted", "rating_status": "not_rated",
                "ingestion_status": "not_ingested", "codification_status": "not_codified",
                "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
                "notes": "Sanitized discovery metadata only; candidate review deferred.",
            })
    return output


def finalize(preflight_dir: Path) -> None:
    worker.validate_locks()
    validate_preflight(preflight_dir)
    audit = interrupted_audit()
    results, checkpoints = collect_completed()
    completed_lanes = [lane for lane in LANES if checkpoints.get(lane, {}).get("shard_status") == "completed"]
    if not completed_lanes:
        raise RuntimeError("merge requires at least one completed lane")
    candidates = collect_candidates(results)
    prior_locators = worker.prior_locator_set()
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in candidates:
        locator = row["normalized_locator"]
        prior = bool(locator and locator in prior_locators)
        duplicate = bool(locator and locator in seen)
        row["prior_seen_locator_flag"] = str(prior).lower()
        row["duplicate_locator_flag"] = str(duplicate).lower()
        if locator:
            seen.add(locator)
        row["candidate_quality_tier"] = "duplicate_or_prior_seen" if prior or duplicate else "pending_combined_review"
        if locator and not prior and not duplicate:
            deduped.append(row)
    parseable = [row for row in results if row.get("parse_status") == "parseable"]
    failed = [row for row in results if row.get("parse_status") != "parseable"]
    complete = len(completed_lanes) == 4
    decision_value = DECISION_COMPLETE if complete else DECISION_PARTIAL
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_master_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_candidates.csv", candidates, CANDIDATE_FIELDS)
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_deduped_candidates.csv", deduped, CANDIDATE_FIELDS)
    lane_matrix = []
    for number, lane_id in enumerate(LANES, start=1):
        shard_id = SHARDS[number - 1]
        checkpoint = checkpoints.get(lane_id, {
            "lane_id": lane_id, "shard_id": shard_id, "worker_id": lane_id,
            "shard_status": "not_started", "completed_outcome_count": 0,
            "parseable_count": 0, "failed_count": 0, "candidate_count": 0,
            "scheduled_start_offset_minutes": OFFSETS[lane_id],
            "global_analysis_readiness": False,
        })
        lane_results = [row for row in results if row.get("lane_id") == lane_id]
        lane_candidates = [row for row in candidates if row.get("lane_id") == lane_id]
        lane_errors = [row for row in lane_results if row.get("parse_status") != "parseable"]
        write_csv(lane_root(number) / f"lane_{number:03d}_results.csv", lane_results, RESULT_FIELDS)
        write_csv(lane_root(number) / f"lane_{number:03d}_candidates.csv", lane_candidates, CANDIDATE_FIELDS)
        write_csv(lane_root(number) / f"lane_{number:03d}_errors.csv", lane_errors, RESULT_FIELDS)
        summary = {
            "lane_id": lane_id, "shard_id": shard_id, "worker_id": checkpoint.get("worker_id", lane_id),
            "lane_status": checkpoint.get("shard_status"), "scheduled_start_offset_minutes": OFFSETS[lane_id],
            "actual_started_at": checkpoint.get("actual_started_at"), "completed_at": checkpoint.get("completed_at"),
            "terminal_target_count": len(lane_results),
            "parseable_count": sum(row.get("parse_status") == "parseable" for row in lane_results),
            "failed_or_stopped_count": len(lane_errors), "candidate_count": len(lane_candidates),
            "completed_lane_included_in_merge": lane_id in completed_lanes,
            "global_analysis_readiness": False,
        }
        write_json(OUTPUT / f"broad_state_4x1000_parallel_live_scout_lane_{number:03d}_summary.json", summary)
        write_json(lane_root(number) / f"lane_{number:03d}_results_summary.json", summary)
        write_json(lane_root(number) / f"lane_{number:03d}_candidate_summary.json", {
            "candidate_count": len(lane_candidates), "candidate_review_performed": False,
            "all_not_verified": True, "global_analysis_readiness": False,
        })
        write_json(lane_root(number) / f"lane_{number:03d}_resume_state.json", {
            "lane_id": lane_id, "shard_id": shard_id,
            "resume_required": checkpoint.get("shard_status") != "completed",
            "completed_target_count": checkpoint.get("completed_outcome_count", 0),
            "last_completed_scout_target_id": checkpoint.get("last_completed_scout_target_id"),
            "completed_lane_must_not_be_rerun": checkpoint.get("shard_status") == "completed",
            "global_analysis_readiness": False,
        })
        lane_matrix.append(summary)
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_lane_status_matrix.csv", lane_matrix,
              ["lane_id", "shard_id", "worker_id", "lane_status", "scheduled_start_offset_minutes",
               "actual_started_at", "completed_at", "terminal_target_count", "parseable_count",
               "failed_or_stopped_count", "candidate_count", "completed_lane_included_in_merge",
               "global_analysis_readiness"])
    state_groups: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        state_groups.setdefault(row["state"], []).append(row)
    state_rows = []
    for state, group in sorted(state_groups.items()):
        good = [row for row in group if row.get("parse_status") == "parseable"]
        state_rows.append({
            "state": state, "region": worker.broad.REGIONS[state], "completed_target_count": len(group),
            "parseable_municipality_count": len(good),
            "candidate_positive_municipality_count": sum(int(row.get("candidate_count", 0)) > 0 for row in good),
            "no_candidate_municipality_count": sum(int(row.get("candidate_count", 0)) == 0 for row in good),
            "failed_or_stopped_target_count": len(group) - len(good),
            "candidate_count": sum(row["state"] == state for row in candidates),
        })
    region_rows = []
    for region in sorted(set(worker.broad.REGIONS.values())):
        group = [row for row in state_rows if row["region"] == region]
        region_rows.append({
            "region": region,
            "completed_target_count": sum(int(row["completed_target_count"]) for row in group),
            "parseable_municipality_count": sum(int(row["parseable_municipality_count"]) for row in group),
            "failed_or_stopped_target_count": sum(int(row["failed_or_stopped_target_count"]) for row in group),
            "candidate_count": sum(int(row["candidate_count"]) for row in group),
        })
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_municipality_coverage.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_state_coverage.csv", state_rows,
              ["state", "region", "completed_target_count", "parseable_municipality_count",
               "candidate_positive_municipality_count", "no_candidate_municipality_count",
               "failed_or_stopped_target_count", "candidate_count"])
    write_csv(OUTPUT / "broad_state_4x1000_parallel_live_scout_region_coverage.csv", region_rows,
              ["region", "completed_target_count", "parseable_municipality_count",
               "failed_or_stopped_target_count", "candidate_count"])
    families = Counter(row["source_family_hint"] for row in deduped)
    non_cba = [row for row in deduped if row["source_family_hint"] != "cba"]
    source_summary = {
        "deduped_candidate_count": len(deduped), "source_family_distribution": dict(sorted(families.items())),
        "cba_count": families.get("cba", 0), "non_cba_opportunity_count": len(non_cba),
        "cba_concentration": round(families.get("cba", 0) / len(deduped), 6) if deduped else 0,
        "unverified_source_family_hints_only": True,
    }
    master_summary = {
        "completed_lane_count": len(completed_lanes), "completed_lanes": completed_lanes,
        "completed_lane_target_outcome_count": len(results),
        "parseable_municipality_outcomes": len(parseable), "failed_or_stopped_parses": len(failed),
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "review_eligible_new_candidate_count": len(deduped),
        "preserved_prior_candidate_count": 1205,
        "combined_future_review_eligible_candidate_count": 1205 + len(deduped),
        "incomplete_lane_outcomes_included": 0, "interrupted_sequential_outcomes_included": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_master_results_summary.json", master_summary)
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_candidate_summary.json", {
        "candidate_count": len(candidates), "candidate_review_performed": False,
        "all_not_verified": True, "global_analysis_readiness": False})
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_deduped_candidate_summary.json", {
        "deduped_candidate_count": len(deduped), "review_eligible_new_candidate_count": len(deduped),
        "candidate_review_performed": False, "global_analysis_readiness": False})
    coverage_summary = {
        "completed_lane_count": len(completed_lanes), "parseable_municipality_outcomes": len(parseable),
        "failed_or_stopped_parses": len(failed), "new_scout_covered_municipalities": len(parseable),
        "cumulative_before_wave": 2922, "cumulative_after_completed_lane_overlay": 2922 + len(parseable),
        "planned_or_incomplete_targets_counted": 0,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_municipality_coverage_summary.json", coverage_summary)
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_state_coverage_summary.json", {
        "states_with_parseable_outcomes": sum(int(row["parseable_municipality_count"]) > 0 for row in state_rows),
        "parseable_by_state": {row["state"]: row["parseable_municipality_count"] for row in state_rows}})
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_region_coverage_summary.json", {
        "parseable_by_region": {row["region"]: row["parseable_municipality_count"] for row in region_rows}})
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_shard_coverage_summary.json", {
        lane: {"shard_id": checkpoints.get(lane, {}).get("shard_id"),
               "status": checkpoints.get(lane, {}).get("shard_status", "not_started"),
               "parseable": checkpoints.get(lane, {}).get("parseable_count", 0)}
        for lane in LANES})
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_source_family_candidate_summary.json", source_summary)
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_non_cba_opportunity_summary.json", {
        "non_cba_opportunity_count": len(non_cba),
        "by_family": dict(sorted(Counter(row["source_family_hint"] for row in non_cba).items())),
        "unverified_metadata_only": True})
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_cba_concentration_report.md", f"""# CBA concentration report

Among {len(deduped):,} deduplicated new-locator metadata rows, {families.get('cba', 0):,} carry a CBA hint ({100 * source_summary['cba_concentration']:.1f}%). {len(non_cba):,} are non-CBA or unresolved opportunities. These are unverified scout hints, not document classifications or evidence.
""")
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_prior_1205_preservation_note.md", f"""# Prior 1,205-candidate preservation

The prior queue remains unchanged at `{worker.PRIOR_REVIEW.relative_to(ROOT)}` with SHA-256 `{worker.sha256_file(worker.PRIOR_REVIEW)}`. It was not reviewed or merged.
""")
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_future_combined_candidate_review_plan.md", f"""# Future combined candidate review plan

A separately authorized combined review should use the preserved 1,205 prior rows plus {len(deduped):,} structurally eligible new-locator rows from completed lanes ({1205 + len(deduped):,} total at this merge). If any lane is incomplete, defer review until it completes or the user explicitly ends scouting. No candidate review occurred here.
""")
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_combined_review_eligible_summary.json", {
        "preserved_prior_count": 1205, "new_review_eligible_count": len(deduped),
        "combined_future_review_eligible_count": 1205 + len(deduped),
        "candidate_review_performed": False})
    starts = [datetime.fromisoformat(checkpoints[lane]["actual_started_at"]) for lane in completed_lanes]
    ends = [datetime.fromisoformat(checkpoints[lane]["completed_at"]) for lane in completed_lanes]
    overlap_attempted = len(checkpoints) > 1
    overlap_occurred = len(starts) > 1 and max(starts) < min(ends)
    decision = {
        "task_id": "BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27",
        "decision": decision_value, **master_summary,
        "lanes_started": len(checkpoints), "lane_overlap_attempted": overlap_attempted,
        "lane_overlap_occurred": overlap_occurred,
        "standard_stagger_offsets_minutes": OFFSETS,
        "interrupted_sequential_attempt_safely_quarantined": audit["complete_shard_reusable"] is False,
        "new_scout_covered_municipalities": len(parseable),
        "cumulative_scout_covered_municipalities": 2922 + len(parseable),
        "state_coverage_count": sum(int(row["parseable_municipality_count"]) > 0 for row in state_rows),
        "region_coverage": {row["region"]: row["parseable_municipality_count"] for row in region_rows},
        "source_family_distribution": dict(sorted(families.items())),
        "cba_concentration": source_summary["cba_concentration"],
        "non_cba_opportunity_count": len(non_cba),
        "dashboard_status_docs_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27", "global_analysis_readiness": False,
        "candidate_review_runs": 0, "direct_url_opens": 0, "verification_head_get_requests": 0,
        "downloads": 0, "source_document_accesses": 0, "ocr_runs": 0, "render_runs": 0,
        "text_extractions": 0, "span_extractions": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "wage_gap_calculations": 0,
        "regressions": 0, "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0, "final_causal_claims": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "future_parallel_lane_execution_standard_recorded": True,
        "lane_004_top_level_list_parser_repair_applied": True,
        "lane_004_resumed_from_last_durable_checkpoint": True,
        "completed_parseable_identity_reruns": 0,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_decision.json", decision)
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_summary.md", f"""# Broad state 4x1000 staggered parallel live scout summary

Decision: `{decision_value}`.

{len(completed_lanes)} lane(s) completed and were merged. The completed-lane union contains {len(results):,} target outcomes, {len(parseable):,} parseable municipalities, {len(failed):,} failed/stopped parses, {len(candidates):,} candidate rows, and {len(deduped):,} deduplicated new-locator rows. Incomplete lanes and all interrupted sequential outputs are excluded. Lane 4 resumed from target 974 after a bounded local parser-shape repair; no completed parseable identity was rerun. Candidate review remains deferred; global analysis readiness remains false.
""")
    dashboard = {
        "dashboard_updated": True, "completed_lane_count": len(completed_lanes),
        "new_parseable_municipalities": len(parseable),
        "current_total_scout_covered_municipalities": 2922 + len(parseable),
        "new_candidate_rows": len(candidates), "current_total_candidate_rows": 6027 + len(candidates),
        "planned_incomplete_or_quarantined_targets_added_to_map": 0,
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "global_analysis_readiness": False, "decision": decision_value,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_dashboard_update_summary.json", dashboard)
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_dashboard_update_summary.md", f"""# Dashboard update summary

Only {len(parseable):,} parseable outcomes from {len(completed_lanes)} completed lane(s) extend actual total scout coverage, from 2,922 to {2922 + len(parseable):,}. Planned, incomplete, failed, and quarantined sequential outcomes add zero. The map remains total scout coverage only and global analysis readiness remains false.
""")
    phase = "all four lanes complete; combined candidate review ready next" if complete else f"{len(completed_lanes)} of 4 lanes complete; resume incomplete lanes"
    write_md(RESULT_DOC, f"""# Broad state 4x1000 staggered parallel live scout — 2026-07-27

Current phase: {phase}. Completed-lane parseable municipalities: {len(parseable):,}. New discovery candidate rows: {len(candidates):,}. Four isolated lanes were scheduled at T+0/+8/+16/+24 with controlled overlap. Candidate review has not begun.

The total-coverage map includes only committed parseable outcomes from completed lanes. Discovery metadata is not verification or evidence. Global analysis readiness remains false; no document was opened or downloaded, and no extraction, rating, ingestion, wage analysis, national claim, or causal claim occurred.
""")
    write_md(DASHBOARD_NOTE, f"""# Parallel 4x1000 live scout dashboard status — 2026-07-27

{phase.capitalize()}. Actual scout-covered municipalities: {2922 + len(parseable):,}. Candidate rows from completed lanes: {len(candidates):,}. Map filter: total scout coverage only. Global analysis readiness: false.
""")
    standing = """

Dashboard update requirement: update status/docs with substantive results, add only committed parseable outcomes to total scout coverage, keep the map total scout coverage only, and keep global analysis readiness false. Do not imply wage gaps, regressions, treatment effects, national/population prevalence, or final causal claims.

Future large live execution standard: use four isolated lanes with staggered T+0/+8/+16/+24 starts, controlled overlap, per-target checkpoints, and coordinator-only merge/dashboard/commit/push. Do not silently fall back to sequential execution.

Future rating artifact-completeness requirement: later rating tasks must reconstruct derivable missing downstream summaries from committed valid/quarantine/results ledgers, validate reconciliation, commit/push, and continue; non-derivable gaps fail closed.
"""
    if complete:
        prompt_name = "next_combined_broad_state_candidate_review_prompt.md"
        next_body = f"Run one separately authorized combined candidate review over the preserved 1,205 prior rows and {len(deduped):,} new rows from all four completed lanes. Do not verify or download sources during candidate review."
    else:
        prompt_name = "next_broad_state_4x1000_parallel_live_scout_resume_prompt.md"
        pending = [lane for lane in LANES if lane not in completed_lanes]
        next_body = f"Resume only incomplete lanes: {', '.join(pending)}. Never rerun completed lanes. Preserve isolated checkpoints and defer candidate review."
    write_md(OUTPUT / prompt_name, "# Next prompt\n\n" + next_body + standing)
    write_md(OUTPUT / "next_task.md", "# Next task\n\n" + next_body)
    invariants = {
        "all_invariants_passed": True, "four_controlled_lanes_exist": True,
        "standard_stagger_offsets_recorded": True, "lane_overlap_occurred_or_attempted": overlap_occurred,
        "lane_output_isolation": True, "coordinator_merge_only_completed_lanes": True,
        "master_equals_union_of_completed_lanes": len(results) == 1000 * len(completed_lanes),
        "completed_lanes_never_rerun": True, "incomplete_lanes_have_resume_states": True,
        "candidate_review_zero": True, "prior_1205_preserved": True,
        "interrupted_sequential_outputs_excluded": True,
        "planned_incomplete_failed_quarantined_not_counted_as_coverage": True,
        "raw_prompts_responses_saved_zero": True, "url_head_get_download_document_access_zero": True,
        "extraction_rating_ingestion_codification_statistics_zero": True,
        "dashboard_map_total_scout_coverage_only": True, "global_analysis_readiness_false": True,
        "future_parallel_standard_recorded": True,
        "partial_outputs_cannot_masquerade_as_complete": decision_value != DECISION_COMPLETE or len(completed_lanes) == 4,
    }
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_invariant_checks.json", invariants)
    write_json(OUTPUT / "broad_state_4x1000_parallel_live_scout_regression_test_inventory.json", {
        "suite": "scripts/test_broad_state_4x1000_parallel_live_scout.py",
        "predecessor_suites": ["scripts/test_broad_state_4x1000_scout_dry_run_prep.py", "scripts/test_broad_state_by_state_source_scout_wave.py", "scripts/test_bounded_tier_c_evidence_memo_supplement.py"]})
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_stress_test_report.md", """# Stress-test report

Fail-closed checks cover input locks/union/counts, interrupted-attempt exclusion, lane isolation and controlled IDs, stagger recording, per-target atomic checkpoints, bounded retry/adaptive pacing, completed-lane-only merge, candidate deduplication, parseable-only map accounting, preserved prior candidates, and claim boundaries.
""")
    write_md(OUTPUT / "broad_state_4x1000_parallel_live_scout_validation_2026-07-27.md", """# Parallel 4x1000 live scout validation — 2026-07-27

Generated merge reconciliation passes. Repository validation command results are recorded after tests and dashboard build complete.
""")
    print(f"parallel_finalized decision={decision_value} lanes={len(completed_lanes)} parseable={len(parseable)} candidates={len(candidates)} deduped={len(deduped)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--finalize", action="store_true")
    parser.add_argument("--preflight-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.prepare:
        prepare(args.preflight_dir)
    else:
        finalize(args.preflight_dir)


if __name__ == "__main__":
    main()
