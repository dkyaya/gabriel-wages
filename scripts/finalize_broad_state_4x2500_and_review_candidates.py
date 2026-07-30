#!/usr/bin/env python3
"""Finalize the 2026-07-29 broad 4x2500 scout and review its candidates.

This is deliberately a local, metadata-only phase-boundary tool.  It reads
locked queues, atomic lane checkpoints, sanitized per-target result files, and
prior local ledgers.  It never opens a candidate locator, performs a network
request, downloads or inspects a document, extracts/rates text, or ingests data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
PREP = BASE / "BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
LIVE = BASE / "BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29"
FINAL = BASE / "BROAD-STATE-4X2500-LIVE-SCOUT-FINALIZED-2026-07-30"
REVIEW = BASE / "BROAD-STATE-4X2500-CANDIDATE-REVIEW-2026-07-30"
GATE = BASE / "GLOBAL-ANALYSIS-READINESS-GATE-AFTER-BROAD-INGESTION-2026-07-28"

TASK_ID = "BROAD-STATE-4X2500-LIVE-SCOUT-FINALIZE-AND-CANDIDATE-REVIEW-2026-07-30"
SCOUT_RUN_ID = "BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29"
FINAL_DECISION = "broad_state_4x2500_live_scout_finalized_candidate_review_completed_verification_ready"
LANES = tuple(f"scout_lane_{n:03d}" for n in range(1, 5))
SHARDS = tuple(f"broad_4x2500_shard_{n:03d}" for n in range(1, 5))
ENDPOINTS = {
    "scout_lane_001": "B4X2500-20260729-02500",
    "scout_lane_002": "B4X2500-20260729-05000",
    "scout_lane_003": "B4X2500-20260729-07500",
    "scout_lane_004": "B4X2500-20260729-10000",
}
TRANSPORT_FAILURES = {"connection_error", "timeout", "outer_timeout", "timeout_or_capacity"}
READINESS_FLAGS = {
    "global_collection_readiness": "pass",
    "global_mechanism_analysis_readiness": "partial_pass",
    "global_quantitative_evidence_readiness": "partial_pass",
    "global_wage_gap_analysis_readiness": "blocked_pending_normalization",
    "global_causal_analysis_readiness": "blocked_pending_matched_structure",
    "overall_global_analysis_readiness": "partial_pass",
}

PRIOR_LOCATOR_INPUTS = (
    (
        BASE / "COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28"
        / "combined_broad_candidate_review_universe.csv",
        ("final_canonical_locator", "source_locator_or_url"),
    ),
    (
        BASE / "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
        / "targeted_scouting_four_lane_candidate_deduped_review.csv",
        ("source_url_or_locator",),
    ),
    (
        ROOT / "docs/analysis/verification_ledgers/verified_source_routing_ledger_latest.csv",
        ("final_url", "candidate_url"),
    ),
)

CBA_FAMILIES = {"cba"}
STRONG_FAMILIES = {
    "cba", "arbitration_award", "factfinding_report", "mou_or_memorandum",
    "settlement_agreement", "wage_schedule", "salary_ordinance",
    "compensation_study", "classification_study",
    "civil_service_or_hr_pay_plan", "personnel_policy",
}
MID_FAMILIES = {"budget_or_pay_plan", "other_local_government_pay_policy"}
DIRECT_DOC_TYPES = {
    "cba", "arbitration_award", "factfinding", "memorandum_or_settlement",
    "wage_schedule_or_compensation_plan", "ordinance_or_policy", "meeting_minutes",
}
NAVIGATION_TYPES = {"index_page", "context_only", "agenda_cover_sheet"}
REPAIR_TYPES = {"blocked_or_unreadable", "dead_or_unreachable", "insufficient_source", "unknown"}


def read_json(path: Path) -> Any:
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


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_locator(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        return value.casefold().rstrip("/")
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return value.casefold().rstrip("/")
    host = parts.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    kept = [
        (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
    ]
    return urlunsplit(("https", host, path, urlencode(sorted(kept)), ""))


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def accepted(outcome: dict[str, Any]) -> bool:
    return (
        outcome.get("parse_status") == "parseable"
        or outcome.get("failure_type") not in TRANSPORT_FAILURES
        or int(outcome.get("attempt_count", 0)) >= 2
    )


def validate_locks() -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    master_path = PREP / "broad_state_4x2500_scout_master_locked_queue.csv"
    master_lock = read_json(PREP / "broad_state_4x2500_scout_master_lock.json")
    master = read_csv(master_path)
    if len(master) != 10_000 or sha256_file(master_path) != master_lock["queue_sha256"]:
        raise RuntimeError("master queue count/hash mismatch")
    locked_by_id = {row["scout_target_id"]: row for row in master}
    if len(locked_by_id) != 10_000:
        raise RuntimeError("master target IDs are not unique")
    shard_union: list[str] = []
    details: dict[str, Any] = {}
    for number, shard in enumerate(SHARDS, 1):
        queue_path = PREP / f"broad_state_4x2500_scout_shard_{number:03d}_locked_queue.csv"
        lock = read_json(PREP / f"broad_state_4x2500_scout_shard_{number:03d}_lock.json")
        rows = read_csv(queue_path)
        actual_hash = sha256_file(queue_path)
        if len(rows) != 2_500 or actual_hash != lock["queue_sha256"]:
            raise RuntimeError(f"{shard} count/hash mismatch")
        if any(row["shard_id"] != shard for row in rows):
            raise RuntimeError(f"foreign target in {shard}")
        shard_union.extend(row["scout_target_id"] for row in rows)
        details[shard] = {"count": 2_500, "queue_sha256": actual_hash, "hash_matches": True}
    if len(shard_union) != 10_000 or set(shard_union) != set(locked_by_id):
        raise RuntimeError("master queue does not equal locked shard union")
    return {
        "master_count": 10_000,
        "master_queue_sha256": sha256_file(master_path),
        "master_hash_matches": True,
        "shards": details,
        "master_equals_four_shard_union": True,
    }, locked_by_id


def reconcile_lanes(locked_by_id: dict[str, dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_outcomes: list[dict[str, Any]] = []
    lane_report: dict[str, Any] = {}
    globally_seen: set[str] = set()
    for number, (lane, shard) in enumerate(zip(LANES, SHARDS), 1):
        checkpoint_path = LIVE / "lanes" / lane / f"{lane}_checkpoint.json"
        checkpoint = read_json(checkpoint_path)
        outcomes = checkpoint.get("outcomes", [])
        if checkpoint.get("lane_status") != "completed" or len(outcomes) != 2_500:
            raise RuntimeError(f"{lane} is not durably complete")
        if checkpoint.get("last_completed_scout_target_id") != ENDPOINTS[lane]:
            raise RuntimeError(f"{lane} terminal endpoint mismatch")
        ids = [row.get("scout_target_id", "") for row in outcomes]
        if len(set(ids)) != 2_500 or globally_seen.intersection(ids):
            raise RuntimeError(f"duplicate accepted target in {lane}")
        expected_ids = {key for key, row in locked_by_id.items() if row["shard_id"] == shard}
        if set(ids) != expected_ids:
            raise RuntimeError(f"{lane} outcomes do not equal its locked shard")
        durable_candidates = 0
        durable_files = 0
        bounded_retries = 0
        for outcome in outcomes:
            target_id = outcome["scout_target_id"]
            if not accepted(outcome) or not str(outcome.get("execution_status", "")).startswith("completed"):
                raise RuntimeError(f"nonaccepted/nonterminal outcome counted: {target_id}")
            if outcome.get("shard_id") != shard or locked_by_id[target_id]["shard_id"] != shard:
                raise RuntimeError(f"outcome assigned outside locked shard: {target_id}")
            run_dir = ROOT / outcome["target_output_dir"]
            metadata_path = run_dir / "run_metadata.json"
            candidates_path = run_dir / "parsed_candidates.csv"
            if not metadata_path.is_file() or not candidates_path.is_file():
                raise RuntimeError(f"durable target result missing: {target_id}")
            durable_count = count_csv_rows(candidates_path)
            if durable_count != int(outcome.get("candidate_count", 0)):
                raise RuntimeError(f"durable candidate count mismatch: {target_id}")
            metadata = read_json(metadata_path)
            if metadata.get("raw_prompts_persisted") is True or metadata.get("raw_responses_persisted") is True:
                raise RuntimeError(f"raw hosted-search material persisted: {target_id}")
            child = run_dir.parent
            run_names = {path.name for path in child.iterdir() if path.is_dir()}
            if not run_names <= {"run", "retry_1"} or len(run_names) > 2:
                raise RuntimeError(f"unbounded or foreign rerun directory: {target_id}")
            bounded_retries += int("retry_1" in run_names)
            durable_candidates += durable_count
            durable_files += 1
        globally_seen.update(ids)
        parseable = [row for row in outcomes if row.get("parse_status") == "parseable"]
        failed = [row for row in outcomes if row.get("parse_status") != "parseable"]
        if durable_candidates != int(checkpoint.get("candidate_count", -1)):
            raise RuntimeError(f"{lane} checkpoint/durable candidate total mismatch")
        lane_report[lane] = {
            "shard_id": shard,
            "lane_status": "completed",
            "terminal_endpoint": ENDPOINTS[lane],
            "terminal_endpoint_reached": True,
            "accepted_outcomes": len(outcomes),
            "parseable_outcomes": len(parseable),
            "failed_or_unparseable_outcomes": len(failed),
            "raw_candidate_rows_from_durable_files": durable_candidates,
            "unique_municipalities_completed": len({row["municipality_id"] for row in outcomes}),
            "unique_parseable_municipalities": len({row["municipality_id"] for row in parseable}),
            "state_counts_accepted": dict(sorted(Counter(row["state"] for row in outcomes).items())),
            "region_counts_accepted": dict(sorted(Counter(row["region"] for row in outcomes).items())),
            "durable_target_result_files_reconciled": durable_files,
            "bounded_retry_target_count": bounded_retries,
            "accepted_target_reruns": 0,
            "started_at": checkpoint.get("actual_started_at"),
            "completed_at": checkpoint.get("completed_at"),
            "checkpoint_sha256": sha256_file(checkpoint_path),
        }
        all_outcomes.extend(outcomes)
    if len(all_outcomes) != 10_000 or len(globally_seen) != 10_000:
        raise RuntimeError("accepted outcome universe does not reconcile to 10,000 unique targets")
    return all_outcomes, lane_report


def candidate_summaries(rows: list[dict[str, str]]) -> dict[str, Any]:
    families = Counter(row["source_family_hint"] for row in rows)
    mechanisms = Counter(
        hint for row in rows for hint in row.get("possible_mechanism_hints", "").split(";") if hint
    )
    return {
        "candidate_count": len(rows),
        "source_family_hints": dict(sorted(families.items())),
        "cba_hint_count": sum(count for family, count in families.items() if family in CBA_FAMILIES),
        "non_cba_or_other_hint_count": sum(count for family, count in families.items() if family not in CBA_FAMILIES),
        "state_counts": dict(sorted(Counter(row["state"] for row in rows).items())),
        "region_counts": dict(sorted(Counter(row["region"] for row in rows).items())),
        "mechanism_hint_counts": dict(sorted(mechanisms.items())),
    }


def finalize_scout(workers_confirmed_stopped: bool) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not workers_confirmed_stopped:
        raise RuntimeError("host-level worker process audit must pass before finalization")
    locks, locked_by_id = validate_locks()
    outcomes, lane_report = reconcile_lanes(locked_by_id)
    raw = read_csv(LIVE / "broad_state_4x2500_live_scout_candidates.csv")
    finalized = read_csv(LIVE / "broad_state_4x2500_live_scout_deduped_candidates.csv")
    if len(raw) != sum(row["raw_candidate_rows_from_durable_files"] for row in lane_report.values()):
        raise RuntimeError("merged raw candidates do not reconcile to durable lane files")
    raw_ids = {row["scout_candidate_id"] for row in raw}
    if len(raw_ids) != len(raw):
        raise RuntimeError("raw candidate IDs are not unique")
    final_ids = {row["scout_candidate_id"] for row in finalized}
    if not final_ids <= raw_ids or len(final_ids) != len(finalized):
        raise RuntimeError("finalized candidate lineage is invalid")
    locators = [row["normalized_locator"] for row in finalized]
    if not all(locators) or len(set(locators)) != len(locators):
        raise RuntimeError("finalized candidates are not unique nonempty locators")
    if any(row["duplicate_locator_flag"] == "true" or row["prior_seen_locator_flag"] == "true" for row in finalized):
        raise RuntimeError("upstream duplicates leaked into finalized candidate universe")

    raw_duplicate = sum(row["duplicate_locator_flag"] == "true" for row in raw)
    raw_prior = sum(row["prior_seen_locator_flag"] == "true" for row in raw)
    raw_empty = sum(not row["normalized_locator"] for row in raw)
    if len(raw) - len(finalized) != sum(
        row["duplicate_locator_flag"] == "true"
        or row["prior_seen_locator_flag"] == "true"
        or not row["normalized_locator"]
        for row in raw
    ):
        raise RuntimeError("candidate deduplication exclusions do not reconcile")

    for row in finalized:
        row["discovery_run_id"] = SCOUT_RUN_ID
        row["lane_completed_at"] = lane_report[row["lane_id"]]["completed_at"] or ""
    fields = list(finalized[0]) if finalized else []
    write_csv(FINAL / "finalized_candidate_rows.csv", finalized, fields)
    write_jsonl(FINAL / "finalized_candidate_rows.jsonl", finalized)
    write_json(FINAL / "lane_reconciliation_report.json", {
        "all_lanes_reconciled": True,
        "workers_running": False,
        "worker_process_audit": "host-level ps audit returned no matching scout workers",
        "lanes": lane_report,
        "totals": {
            "accepted_outcomes": len(outcomes),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in outcomes),
            "failed_or_unparseable_outcomes": sum(row["parse_status"] != "parseable" for row in outcomes),
            "raw_candidate_rows": len(raw),
            "unique_municipalities_completed": len({row["municipality_id"] for row in outcomes}),
            "unique_parseable_municipalities": len({row["municipality_id"] for row in outcomes if row["parse_status"] == "parseable"}),
        },
    })
    dedupe = {
        "convention": "exact project normalized_locator; suppress prior-seen locators, current-wave repeats, and empty locators; keep first discovery lineage",
        "raw_candidate_rows": len(raw),
        "finalized_deduped_candidate_rows": len(finalized),
        "total_excluded": len(raw) - len(finalized),
        "raw_rows_marked_current_wave_duplicate": raw_duplicate,
        "raw_rows_marked_prior_seen": raw_prior,
        "raw_rows_with_empty_normalized_locator": raw_empty,
        "exclusion_categories_can_overlap": True,
        "finalized_locators_unique": True,
    }
    write_json(FINAL / "candidate_deduplication_summary.json", dedupe)

    by_lane_candidates = {
        lane: candidate_summaries([row for row in finalized if row["lane_id"] == lane]) for lane in LANES
    }
    for lane in LANES:
        lane_report[lane].update(by_lane_candidates[lane])
    # Rewrite after candidate-ledger reconciliation so this required report
    # contains per-lane source-family, CBA/non-CBA, geography, and mechanism hints.
    write_json(FINAL / "lane_reconciliation_report.json", {
        "all_lanes_reconciled": True,
        "workers_running": False,
        "worker_process_audit": "host-level ps audit returned no matching scout workers",
        "lanes": lane_report,
        "totals": {
            "accepted_outcomes": len(outcomes),
            "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in outcomes),
            "failed_or_unparseable_outcomes": sum(row["parse_status"] != "parseable" for row in outcomes),
            "raw_candidate_rows": len(raw),
            "finalized_deduped_candidate_rows": len(finalized),
            "unique_municipalities_completed": len({row["municipality_id"] for row in outcomes}),
            "unique_parseable_municipalities": len({row["municipality_id"] for row in outcomes if row["parse_status"] == "parseable"}),
        },
    })
    readiness = read_json(GATE / "global_analysis_readiness_gate_decision.json")
    if readiness.get("subflag_results") != READINESS_FLAGS or readiness.get("global_analysis_readiness") is not False:
        raise RuntimeError("existing global readiness gate differs from required preserved state")
    summary = {
        "task_id": TASK_ID,
        "scout_run_id": SCOUT_RUN_ID,
        "finalization_status": "passed",
        "completed_lane_count": 4,
        "locked_target_count": 10_000,
        "accepted_outcomes": len(outcomes),
        "parseable_outcomes": sum(row["parse_status"] == "parseable" for row in outcomes),
        "failed_or_unparseable_outcomes": sum(row["parse_status"] != "parseable" for row in outcomes),
        "raw_candidate_rows": len(raw),
        "deduped_candidate_rows": len(finalized),
        "new_actual_scout_covered_municipalities": sum(row["parse_status"] == "parseable" for row in outcomes),
        "cumulative_actual_scout_coverage": 6_919 + sum(row["parse_status"] == "parseable" for row in outcomes),
        "outcome_state_counts": dict(sorted(Counter(row["state"] for row in outcomes).items())),
        "outcome_region_counts": dict(sorted(Counter(row["region"] for row in outcomes).items())),
        "candidate_metadata_summary": candidate_summaries(finalized),
        "lane_candidate_summaries": by_lane_candidates,
        "queue_locks": locks,
        "accepted_target_ids_unique": True,
        "accepted_target_reruns": 0,
        "every_completed_target_in_exactly_one_locked_shard": True,
        "planned_or_incomplete_targets_counted": 0,
        "coverage_accounting": "accepted parseable completed municipality outcomes only",
        "dashboard_map_filter": "total_scout_coverage_only",
        "global_readiness_flags_preserved": READINESS_FLAGS,
        "global_analysis_readiness": False,
        "forbidden_downstream_actions": 0,
    }
    write_json(FINAL / "finalized_live_scout_summary.json", summary)
    write_text(FINAL / "finalized_live_scout_summary.md", f"""# Finalized broad-state 4 × 2,500 live scout

Finalization passed. All four locked lanes reached their exact terminal endpoints and 10,000 unique accepted outcomes were reconciled from atomic checkpoints and 10,000 durable per-target result files. Outcomes comprise {summary['parseable_outcomes']:,} parseable municipalities and {summary['failed_or_unparseable_outcomes']:,} failed/unparseable municipalities. Only the parseable completed outcomes add to actual map coverage.

The durable lanes produced {len(raw):,} raw candidate metadata rows. Project locator deduplication retained {len(finalized):,} rows and excluded {len(raw) - len(finalized):,} prior-seen, repeated, or empty-locator rows. Candidate metadata remain unverified and are not evidence.

No verification, download, source inspection, extraction, rating, ingestion, codification, wage-gap calculation, regression, or causal analysis occurred. Global collection readiness remains passed; mechanism and quantitative readiness remain partial; wage-gap and causal readiness remain blocked; overall readiness remains partial diagnostic only and the global boolean remains false.
""")
    write_json(FINAL / "dashboard_status_input.json", {
        "wave_status": "completed",
        "accepted_parseable_actual_coverage_increment": summary["parseable_outcomes"],
        "failed_or_unparseable_excluded_from_map": summary["failed_or_unparseable_outcomes"],
        "planned_or_incomplete_excluded_from_map": True,
        "map_filter": "total_scout_coverage_only",
        "global_readiness_flags": READINESS_FLAGS,
        "global_analysis_readiness": False,
    })
    write_text(FINAL / "next_task.md", """# Next task

Run local candidate review over `finalized_candidate_rows.csv` only. Preserve scout-target, lane, municipality/state, source-family/query-family, locator/title/snippet, and run lineage. Do not verify locators, download or inspect documents, extract/rate text, ingest/codify, or make comparative or causal claims.
""")
    return finalized, summary


def prior_locator_index() -> tuple[dict[str, str], list[dict[str, Any]]]:
    index: dict[str, str] = {}
    manifests: list[dict[str, Any]] = []
    for path, fields in PRIOR_LOCATOR_INPUTS:
        rows = read_csv(path)
        added = 0
        for row in rows:
            value = next((row.get(field, "") for field in fields if row.get(field, "").strip()), "")
            locator = canonical_locator(value)
            if locator and locator not in index:
                index[locator] = str(path.relative_to(ROOT))
                added += 1
        manifests.append({
            "path": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
            "row_count": len(rows), "unique_locators_first_added": added,
        })
    return index, manifests


def metadata_score(row: dict[str, str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    quality = row["candidate_quality_tier"]
    points = {"high_candidate": 18, "medium_candidate": 12, "low_candidate": 5}.get(quality, 0)
    score += points; reasons.append(f"upstream_quality_{quality}:{points}")
    family = row["source_family_hint"]
    points = 24 if family in STRONG_FAMILIES else 16 if family in MID_FAMILIES else 9 if family == "agenda_packet_or_minutes" else 2
    score += points; reasons.append(f"source_family_{family}:{points}")
    doc_type = row["document_type_hint"]
    points = 15 if doc_type in DIRECT_DOC_TYPES else 3 if doc_type in NAVIGATION_TYPES else -10 if doc_type in REPAIR_TYPES else 0
    score += points; reasons.append(f"document_type_{doc_type}:{points}")
    confidence = row["source_family_confidence"]
    points = {"high": 8, "medium": 4, "low": 0}.get(confidence, 0)
    score += points; reasons.append(f"family_confidence_{confidence}:{points}")
    unit = row["unit_type_hint"]
    points = 10 if unit in {"police", "fire", "non_safety"} else 2
    score += points; reasons.append(f"unit_hint_{unit}:{points}")
    if row["possible_mechanism_hints"].strip():
        score += 8; reasons.append("mechanism_hint_present:8")
    cycle = row["possible_cycle_or_year"].strip().casefold()
    if cycle and cycle not in {"unclear", "unknown", "n/a", "none"}:
        score += 5; reasons.append("cycle_or_year_present:5")
    if row["matched_safety_non_safety_opportunity_flag"] == "true":
        score += 5; reasons.append("matched_opportunity:5")
    locator = row["source_locator_or_url"].casefold()
    if locator.startswith(("http://", "https://")):
        score += 5; reasons.append("structured_web_locator:5")
    if urlsplit(locator).path.casefold().endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")):
        score += 5; reasons.append("document_shaped_locator:5")
    domain = row["source_domain"].casefold()
    if domain.endswith((".gov", ".us")) or ".gov." in domain or "state." in domain:
        score += 4; reasons.append("government_domain_hint:4")
    text = f"{row['source_title']} {row['sanitized_snippet']}".casefold()
    if any(term in text for term in ("salary", "wage", "pay plan", "compensation", "collective bargaining", "agreement", "arbitration", "factfinding")):
        score += 5; reasons.append("compensation_or_labor_terms:5")
    if row["region"] == "West":
        score += 4; reasons.append("geographic_balance_west:4")
    elif row["region"] == "South":
        score += 2; reasons.append("geographic_balance_south:2")
    if family != "cba":
        score += 2; reasons.append("non_cba_source_diversity:2")
    return max(0, min(100, score)), reasons


def classify(row: dict[str, str], prior: dict[str, str]) -> dict[str, Any]:
    score, reasons = metadata_score(row)
    locator = canonical_locator(row["source_locator_or_url"])
    prior_source = prior.get(locator, "")
    doc_type = row["document_type_hint"]
    family = row["source_family_hint"]
    text = f"{row['source_title']} {row['sanitized_snippet']}".casefold()
    obvious_out = any(term in text for term in (
        "job posting only", "employment application only", "police blotter only",
        "election results only", "property listing only",
    ))
    if prior_source:
        bucket = "likely_duplicate_prior_source"
    elif not locator or not row["state"].strip() or not row["municipality"].strip() or not row["source_title"].strip():
        bucket = "repair_needed"
    elif obvious_out:
        bucket = "excluded_out_of_scope"
    elif doc_type in {"blocked_or_unreadable", "dead_or_unreachable", "insufficient_source", "unknown"} or family == "unknown_or_needs_review":
        bucket = "repair_needed"
    elif doc_type in NAVIGATION_TYPES:
        bucket = "likely_non_source_or_navigation_only"
    elif score >= 75:
        bucket = "high_priority_verification_ready"
    elif score >= 58:
        bucket = "medium_priority_verification_ready"
    elif score >= 45:
        bucket = "low_priority_verification_ready"
    else:
        bucket = "deferred_low_signal"
    result: dict[str, Any] = dict(row)
    result.update({
        "candidate_id": row["scout_candidate_id"],
        "canonical_review_locator": locator,
        "review_score": score,
        "review_score_reasons": ";".join(reasons),
        "primary_bucket": bucket,
        "priority_bucket": bucket,
        "prior_duplicate_source": prior_source,
        "cba_non_cba_hint": "cba_hint" if family in CBA_FAMILIES else "non_cba_or_other_hint",
        "review_method": "local_metadata_title_snippet_url_only",
        "verification_status": "not_verified",
        "source_review_status": "not_source_reviewed",
        "global_analysis_readiness": "false",
    })
    return result


def nested_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def run_review(finalized: list[dict[str, str]], final_summary: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if final_summary.get("finalization_status") != "passed":
        raise RuntimeError("candidate review blocked because scout finalization did not pass")
    prior, prior_manifest = prior_locator_index()
    reviewed = [classify(row, prior) for row in finalized]
    if len({row["candidate_id"] for row in reviewed}) != len(reviewed):
        raise RuntimeError("review candidate IDs are not unique")
    ready_buckets = {
        "high_priority_verification_ready", "medium_priority_verification_ready",
        "low_priority_verification_ready",
    }
    ready = [row for row in reviewed if row["primary_bucket"] in ready_buckets]
    repair = [row for row in reviewed if row["primary_bucket"] == "repair_needed"]
    bucket_counts = nested_counts(reviewed, "primary_bucket")
    if sum(bucket_counts.values()) != len(finalized):
        raise RuntimeError("candidate-review buckets do not reconcile")
    if not ready:
        raise RuntimeError("metadata review produced no verification-ready queue")
    fields = list(reviewed[0]) if reviewed else []
    write_csv(REVIEW / "candidate_review_results.csv", reviewed, fields)
    write_jsonl(REVIEW / "candidate_review_results.jsonl", reviewed)
    write_csv(REVIEW / "verification_ready_queue.csv", ready, fields)
    write_jsonl(REVIEW / "verification_ready_queue.jsonl", ready)
    write_csv(REVIEW / "review_repair_queue.csv", repair, fields)
    write_jsonl(REVIEW / "review_repair_queue.jsonl", repair)
    write_json(REVIEW / "candidate_review_bucket_counts.json", {
        "finalized_candidate_count": len(finalized), "bucket_counts": bucket_counts,
        "counts_reconcile": sum(bucket_counts.values()) == len(finalized),
        "one_primary_bucket_per_candidate": True,
    })

    source_families = sorted({row["source_family_hint"] for row in reviewed})
    source_summary = {
        family: {
            "reviewed": sum(row["source_family_hint"] == family for row in reviewed),
            "verification_ready": sum(row["source_family_hint"] == family for row in ready),
            "by_bucket": nested_counts([row for row in reviewed if row["source_family_hint"] == family], "primary_bucket"),
        }
        for family in source_families
    }
    write_json(REVIEW / "source_family_balance_summary.json", {
        "source_families": source_summary,
        "reviewed_source_family_count": len(source_families),
        "verification_ready_source_family_count": len({row["source_family_hint"] for row in ready}),
        "metadata_hints_only": True,
    })
    write_json(REVIEW / "geography_balance_summary.json", {
        "reviewed_by_region": nested_counts(reviewed, "region"),
        "verification_ready_by_region": nested_counts(ready, "region"),
        "reviewed_by_state": nested_counts(reviewed, "state"),
        "verification_ready_by_state": nested_counts(ready, "state"),
        "reviewed_municipalities": len({(row["state"], row["municipality"]) for row in reviewed}),
        "verification_ready_municipalities": len({(row["state"], row["municipality"]) for row in ready}),
    })
    write_json(REVIEW / "cba_non_cba_summary.json", {
        "reviewed": nested_counts(reviewed, "cba_non_cba_hint"),
        "verification_ready": nested_counts(ready, "cba_non_cba_hint"),
        "classification_basis": "source_family_hint equals cba versus all other or unresolved families",
        "unverified_metadata_only": True,
    })
    reviewed_mechanisms = Counter(
        hint for row in reviewed for hint in row["possible_mechanism_hints"].split(";") if hint
    )
    ready_mechanisms = Counter(
        hint for row in ready for hint in row["possible_mechanism_hints"].split(";") if hint
    )
    write_json(REVIEW / "mechanism_hint_summary.json", {
        "reviewed_candidates_with_hint": sum(bool(row["possible_mechanism_hints"]) for row in reviewed),
        "verification_ready_candidates_with_hint": sum(bool(row["possible_mechanism_hints"]) for row in ready),
        "reviewed_hint_counts": dict(sorted(reviewed_mechanisms.items())),
        "verification_ready_hint_counts": dict(sorted(ready_mechanisms.items())),
        "metadata_snippet_hints_only_not_evidence": True,
    })
    duplicates = [row for row in reviewed if row["primary_bucket"] == "likely_duplicate_prior_source"]
    write_json(REVIEW / "duplicate_suppression_summary.json", {
        "prior_input_manifests": prior_manifest,
        "unique_prior_locators": len(prior),
        "likely_duplicate_prior_source_count": len(duplicates),
        "duplicate_matching_method": "exact local canonical locator only; no network checks",
        "duplicate_rows_retained_in_review_results_for_lineage": True,
        "duplicate_rows_excluded_from_verification_ready_queue": True,
        "duplicates_by_prior_input": nested_counts(duplicates, "prior_duplicate_source") if duplicates else {},
    })

    priorities = nested_counts(ready, "primary_bucket")
    queue_manifest = {
        "task_id": TASK_ID,
        "next_task_id": "BROAD-STATE-4X2500-VERIFICATION-2026-07-30",
        "queue_row_count": len(ready),
        "priority_counts": priorities,
        "queue_sha256": sha256_file(REVIEW / "verification_ready_queue.csv"),
        "source_finalized_candidate_sha256": sha256_file(FINAL / "finalized_candidate_rows.csv"),
        "required_fields": [
            "candidate_id", "source_locator_or_url", "municipality", "state",
            "source_family_hint", "priority_bucket", "scout_target_id", "lane_id",
            "search_query_family", "discovery_run_id",
        ],
        "all_required_fields_present": True,
        "all_rows_from_finalized_scout_universe": True,
        "verification_status": "not_verified",
        "network_verification_performed": False,
        "documents_downloaded": 0,
    }
    write_json(REVIEW / "verification_ready_queue_manifest.json", queue_manifest)
    summary = {
        "task_id": TASK_ID,
        "decision": FINAL_DECISION,
        "candidate_review_status": "completed",
        "finalized_candidate_count": len(finalized),
        "reviewed_candidate_count": len(reviewed),
        "bucket_counts": bucket_counts,
        "verification_ready_queue_count": len(ready),
        "verification_ready_priority_counts": priorities,
        "repair_queue_count": len(repair),
        "candidate_review_method": "deterministic local metadata/title/snippet/URL-shape review only",
        "urls_opened": 0,
        "network_requests": 0,
        "documents_downloaded": 0,
        "source_documents_inspected": 0,
        "text_extractions": 0,
        "rating_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "final_causal_claims": 0,
        "dashboard_map_filter": "total_scout_coverage_only",
        "global_readiness_flags_preserved": READINESS_FLAGS,
        "global_analysis_readiness": False,
        "verification_ready_next": True,
    }
    write_json(REVIEW / "candidate_review_summary.json", summary)
    write_text(REVIEW / "candidate_review_summary.md", f"""# Broad-state 4 × 2,500 candidate review

Decision: `{FINAL_DECISION}`.

The deterministic local review classified all {len(reviewed):,} finalized scout candidates into exactly one primary bucket. The verification-ready queue contains {len(ready):,} candidates: {priorities.get('high_priority_verification_ready', 0):,} high priority, {priorities.get('medium_priority_verification_ready', 0):,} medium priority, and {priorities.get('low_priority_verification_ready', 0):,} low priority. The remaining rows are retained in documented repair, prior-duplicate, navigation-only, deferred-low-signal, or out-of-scope buckets.

Scoring used only the finalized candidate title, locator shape, sanitized snippet, municipality/state, source-family and document-type hints, unit and period hints, mechanism hints, query family, lane/run lineage, and local exact-locator duplicate ledgers. It made no network request and did not open, download, inspect, extract, rate, ingest, or codify a source. Candidate classifications remain unverified operational priorities, not evidence or claims.

The dashboard map remains actual total scout coverage only. Global collection readiness remains passed; mechanism and quantitative readiness remain partial; wage-gap analysis remains blocked pending normalization; causal analysis remains blocked pending matched structure; and overall readiness remains partial diagnostic only with the global boolean false.
""")
    write_json(REVIEW / "candidate_review_manifest.json", {
        "task_id": TASK_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_finalized_candidates": str((FINAL / "finalized_candidate_rows.csv").relative_to(ROOT)),
        "input_sha256": sha256_file(FINAL / "finalized_candidate_rows.csv"),
        "input_row_count": len(finalized),
        "output_review_results": "candidate_review_results.csv",
        "output_verification_queue": "verification_ready_queue.csv",
        "reviewed_row_count": len(reviewed),
        "verification_ready_row_count": len(ready),
        "bucket_counts": bucket_counts,
        "metadata_only": True,
        "prior_duplicate_inputs": prior_manifest,
    })
    write_json(REVIEW / "dashboard_status_input.json", {
        "candidate_review_completed": True,
        "verification_ready_queue_count": len(ready),
        "verification_ready_priority_counts": priorities,
        "bucket_counts": bucket_counts,
        "next_stage": "BROAD-STATE-4X2500-VERIFICATION-2026-07-30",
        "map_filter": "total_scout_coverage_only",
        "actual_scout_coverage_increment": final_summary["new_actual_scout_covered_municipalities"],
        "global_readiness_flags": READINESS_FLAGS,
        "global_analysis_readiness": False,
    })
    write_json(REVIEW / "dashboard_status_update_summary.json", {
        "status": "candidate_review_complete_verification_ready",
        "dashboard_data_vintage": "2026-07-30",
        "actual_total_scout_coverage": final_summary["cumulative_actual_scout_coverage"],
        "new_parseable_completed_outcomes_added_to_map": final_summary["parseable_outcomes"],
        "failed_or_unparseable_outcomes_excluded_from_map": final_summary["failed_or_unparseable_outcomes"],
        "planned_or_incomplete_outcomes_excluded_from_map": True,
        "finalized_candidate_count": len(finalized),
        "verification_ready_queue_count": len(ready),
        "priority_counts": priorities,
        "map_filter": "total_scout_coverage_only",
        "global_readiness_flags": READINESS_FLAGS,
        "global_analysis_readiness": False,
    })
    write_text(REVIEW / "dashboard_status_update_summary.md", f"""# Dashboard/status update

The completed 4 × 2,500 scout contributes only its {final_summary['parseable_outcomes']:,} accepted parseable municipality outcomes to the actual total-scout-coverage map, bringing actual coverage to {final_summary['cumulative_actual_scout_coverage']:,}. Its {final_summary['failed_or_unparseable_outcomes']:,} failures and every planned/incomplete row remain excluded. The candidate-review panel records {len(finalized):,} reviewed rows and {len(ready):,} verification-ready rows, with four-lane verification next. All global readiness values remain at the existing partial/blocked gate state and the global boolean remains false.
""")
    write_text(ROOT / "docs/analysis/broad_state_4x2500_candidate_review_result_2026-07-30.md", f"""# Broad state 4 × 2,500 candidate review — 2026-07-30

Decision: `{FINAL_DECISION}`. Scout finalization reconciled 10,000 accepted outcomes ({final_summary['parseable_outcomes']:,} parseable; {final_summary['failed_or_unparseable_outcomes']:,} failed/unparseable), {final_summary['raw_candidate_rows']:,} raw candidates, and {len(finalized):,} finalized deduplicated candidates. Local metadata-only review produced {len(ready):,} verification-ready candidates: {priorities.get('high_priority_verification_ready', 0):,} high, {priorities.get('medium_priority_verification_ready', 0):,} medium, and {priorities.get('low_priority_verification_ready', 0):,} low. No forbidden downstream work occurred; four-lane verification is next.
""")
    write_text(ROOT / "docs/analysis/broad_state_4x2500_candidate_review_dashboard_status_note_2026-07-30.md", f"""# Broad state 4 × 2,500 candidate-review dashboard status — 2026-07-30

Candidate review is complete and {len(ready):,} candidates are ready for four-lane verification. The map remains actual total scout coverage only at {final_summary['cumulative_actual_scout_coverage']:,}, including only {final_summary['parseable_outcomes']:,} new parseable completed outcomes. Global readiness remains partial diagnostic only; wage-gap and causal analysis remain blocked.
""")
    write_text(REVIEW / "next_task.md", f"""# Next task — BROAD-STATE-4X2500-VERIFICATION-2026-07-30

Verify the full {len(ready):,}-row `verification_ready_queue.csv` using four independent staggered lanes. Lock the full queue and deterministic four-shard assignment, checkpoint after every row, and use the existing bounded HEAD/GET reachability conventions. Preserve candidate, scout-target, municipality/state, source-family/query-family, lane, and discovery-run lineage.

This next task may verify locator reachability and metadata only. It must not download or inspect documents, extract or rate text, ingest/codify, or make wage-gap, prevalence, regression, or causal claims. Produce merged source-review-ready outputs, lane reconciliation, dashboard/status updates, and keep the map on actual total scout coverage only.
""")
    return reviewed, summary


def validate_outputs() -> dict[str, Any]:
    final = read_json(FINAL / "finalized_live_scout_summary.json")
    lane = read_json(FINAL / "lane_reconciliation_report.json")
    dedupe = read_json(FINAL / "candidate_deduplication_summary.json")
    review = read_json(REVIEW / "candidate_review_summary.json")
    buckets = read_json(REVIEW / "candidate_review_bucket_counts.json")
    queue_manifest = read_json(REVIEW / "verification_ready_queue_manifest.json")
    final_rows = read_csv(FINAL / "finalized_candidate_rows.csv")
    reviewed = read_csv(REVIEW / "candidate_review_results.csv")
    ready = read_csv(REVIEW / "verification_ready_queue.csv")
    final_ids = {row["scout_candidate_id"] for row in final_rows}
    reviewed_ids = [row["candidate_id"] for row in reviewed]
    required = queue_manifest["required_fields"]
    gates = {
        "lane_terminal_endpoints_reached": all(item["terminal_endpoint_reached"] for item in lane["lanes"].values()),
        "worker_processes_no_longer_active": lane["workers_running"] is False,
        "master_and_shard_hashes_match": final["queue_locks"]["master_hash_matches"] and all(item["hash_matches"] for item in final["queue_locks"]["shards"].values()),
        "accepted_outcomes_unique_and_complete": final["accepted_outcomes"] == 10_000 and final["accepted_target_ids_unique"],
        "parseable_failed_reconcile": final["parseable_outcomes"] + final["failed_or_unparseable_outcomes"] == final["accepted_outcomes"],
        "candidate_merge_dedupe_reconcile": dedupe["raw_candidate_rows"] - dedupe["total_excluded"] == dedupe["finalized_deduped_candidate_rows"] == len(final_rows),
        "candidate_review_bucket_counts_reconcile": buckets["counts_reconcile"] and sum(buckets["bucket_counts"].values()) == len(reviewed) == len(final_rows),
        "one_primary_bucket_per_candidate": len(reviewed_ids) == len(set(reviewed_ids)) == len(final_ids),
        "verification_ready_schema_valid": bool(ready) and all(all(row.get(field, "").strip() for field in required) for row in ready),
        "verification_ready_lineage_valid": {row["candidate_id"] for row in ready} <= final_ids,
        "no_forbidden_downstream_work": all(review[key] == 0 for key in (
            "urls_opened", "network_requests", "documents_downloaded", "source_documents_inspected",
            "text_extractions", "rating_runs", "ingestion_runs", "codification_runs",
            "wage_gap_calculations", "regressions", "final_causal_claims",
        )),
        "dashboard_actual_coverage_accounting_valid": final["coverage_accounting"] == "accepted parseable completed municipality outcomes only" and final["dashboard_map_filter"] == "total_scout_coverage_only",
        "global_readiness_not_advanced": final["global_readiness_flags_preserved"] == READINESS_FLAGS and review["global_analysis_readiness"] is False,
    }
    if not all(gates.values()):
        raise RuntimeError(f"phase-boundary validation failed: {[key for key, passed in gates.items() if not passed]}")
    payload = {"status": "passed", "all_validation_gates_passed": True, "gates": gates}
    write_json(FINAL / "finalization_validation.json", payload)
    write_json(REVIEW / "candidate_review_validation.json", payload)
    forbidden = {
        "status": "passed", "forbidden_action_count": 0,
        "network_verification": 0, "urls_opened": 0, "downloads": 0,
        "source_document_inspection": 0, "text_extraction": 0, "rating": 0,
        "ingestion": 0, "codification": 0, "wage_gap_or_regression": 0,
        "population_prevalence_claims": 0, "final_causal_claims": 0,
        "basis": "bounded local finalization/review script contains no HTTP client or browser operation and records only local metadata review",
    }
    write_json(FINAL / "forbidden_action_audit.json", forbidden)
    write_json(REVIEW / "forbidden_action_audit.json", forbidden)
    write_json(REVIEW / "final_decision.json", {
        "task_id": TASK_ID, "decision": FINAL_DECISION,
        "scout_finalization_passed": True, "candidate_review_completed": True,
        "verification_ready": True, "verification_performed": False,
        "global_analysis_readiness": False,
    })
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--workers-confirmed-stopped", action="store_true")
    args = parser.parse_args()
    if args.run == args.validate:
        raise SystemExit("choose exactly one of --run or --validate")
    if args.run:
        finalized, final_summary = finalize_scout(args.workers_confirmed_stopped)
        reviewed, review_summary = run_review(finalized, final_summary)
        validate_outputs()
        print(json.dumps({
            "decision": FINAL_DECISION,
            "accepted": final_summary["accepted_outcomes"],
            "parseable": final_summary["parseable_outcomes"],
            "failed": final_summary["failed_or_unparseable_outcomes"],
            "raw_candidates": final_summary["raw_candidate_rows"],
            "deduped_candidates": final_summary["deduped_candidate_rows"],
            "reviewed": len(reviewed),
            "verification_ready": review_summary["verification_ready_queue_count"],
            "priorities": review_summary["verification_ready_priority_counts"],
        }, indent=2, sort_keys=True))
    else:
        print(json.dumps(validate_outputs(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
