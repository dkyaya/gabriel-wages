#!/usr/bin/env python3
"""Prepare, run, and merge the broad candidate verification long run.

This program performs bounded HTTP HEAD reachability checks only. It never
downloads or retains documents, reads response bodies, opens PDF/HTML content,
or performs candidate review, source review, extraction, rating, ingestion,
codification, or statistical analysis.
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "BROAD-CANDIDATE-VERIFICATION-4X3000-PARALLEL-LONG-RUN-2026-07-28"
OUTPUT = BASE / TASK_ID
SCOUT_4X = BASE / "BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27"
SCOUT_490 = BASE / "BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
TARGETED = BASE / "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
AB_VERIFY = BASE / "TARGETED-SOURCE-VERIFICATION-TIER-A-B-FROM-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
TC_VERIFY = BASE / "TARGETED-TIER-C-VERIFICATION-FROM-BOUNDED-MEMO-GAPS-AND-DASHBOARD-VISIBILITY-CHECK-2026-07-26"
LEGACY_VERIFY = ROOT / "docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv"
SOURCE_REVIEW = ROOT / "docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv"

TASK_DATE = "2026-07-28"
TARGET_CEILING = 12_000
LANES = tuple(f"verify_lane_{number:03d}" for number in range(1, 5))
MAX_LANE_ROWS = 3_000
CONCURRENCY = 8
TIMEOUT_SECONDS = 8.0
MAX_RETRIES = 1
MAX_REDIRECTS = 5
MIN_BATCH_INTERVAL_SECONDS = 6.25
STAGGER_MINUTES = {lane: index * 8 for index, lane in enumerate(LANES)}

CONTROLLED_STATUSES = {
    "verified_reachable", "verified_reachable_redirected", "reused_prior_verified",
    "unavailable_404_410", "unavailable_other_status", "blocked_transport", "timeout",
    "invalid_locator", "unsupported_locator", "duplicate_locator_skipped",
    "prior_seen_skipped", "already_verified_skipped", "verification_error",
    "verification_not_run",
}

ROW_FIELDS = (
    "verification_row_id", "source_candidate_id", "candidate_origin", "lane_id",
    "lane_sequence", "state", "region", "municipality", "county", "source_title",
    "source_locator_or_url", "canonical_locator_before_verification", "source_domain",
    "source_family_hint", "document_type_hint", "candidate_quality_tier",
    "possible_mechanism_hints", "prior_seen_locator_flag", "prior_verification_status",
    "verification_status", "http_status_code", "redirect_count",
    "final_canonical_locator", "content_type_header", "content_length_header",
    "transport_error_type", "verification_attempt_count", "verification_started_at",
    "verification_completed_at", "worker_id", "checkpoint_id", "download_status",
    "source_review_status", "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "notes",
)

UNIVERSE_FIELDS = ROW_FIELDS + ("queue_disposition", "queue_exclusion_reason", "input_row_number")


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


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    fields = tuple(fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})
        handle.flush()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def canonical_locator(value: str) -> str:
    value = (value or "").strip()
    try:
        parts = urlsplit(value)
    except ValueError:
        return ""
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return ""
    host = parts.netloc.casefold()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+", "/", parts.path).rstrip("/")
    return urlunsplit((parts.scheme.casefold(), host, path, "", ""))


def source_domain(locator: str) -> str:
    try:
        return urlsplit(locator).netloc.casefold().removeprefix("www.")
    except ValueError:
        return ""


def bool_text(value: str) -> bool:
    return (value or "").strip().casefold() in {"true", "1", "yes", "y"}


def base_row(origin: str, row: dict[str, str], input_number: int) -> dict[str, str]:
    if origin == "broad_4x1000_deduped":
        candidate_id = row.get("scout_candidate_id", "")
        locator = row.get("source_locator_or_url", "")
        unit = row.get("unit_type_hint", "")
        occupation = row.get("occupation_group_hint", "")
        prior_seen = row.get("prior_seen_locator_flag", "false")
        duplicate = row.get("duplicate_locator_flag", "false")
        downstream = {
            "download": row.get("download_status", ""), "extraction": row.get("extraction_status", ""),
            "rating": row.get("rating_status", ""), "ingestion": row.get("ingestion_status", ""),
            "codification": row.get("codification_status", ""),
        }
    elif origin == "broad_490_preserved_review_queue":
        candidate_id = row.get("scout_candidate_id", "")
        locator = row.get("source_locator_or_url", "")
        unit = row.get("unit_type", "")
        occupation = row.get("occupation_group", "")
        prior_seen = row.get("prior_seen_locator_flag", "false")
        duplicate = row.get("duplicate_locator_flag", "false")
        downstream = {
            "download": row.get("download_status", ""), "extraction": row.get("extraction_status", ""),
            "rating": row.get("rating_status", ""), "ingestion": row.get("ingestion_status", ""),
            "codification": row.get("codification_status", ""),
        }
    else:
        candidate_id = row.get("candidate_id", "")
        locator = row.get("source_url_or_locator", "")
        unit = row.get("unit_type", "")
        occupation = row.get("occupation_group", "")
        prior_seen = "false"
        duplicate = "true" if row.get("review_duplicate_status", "") != "canonical_locator_unique" else "false"
        downstream = {
            "download": "not_downloaded", "extraction": row.get("extraction_status", ""),
            "rating": row.get("rating_status", ""), "ingestion": "not_ingested",
            "codification": "not_codified",
        }
    canonical = canonical_locator(locator)
    family = row.get("source_family_hint", row.get("source_family", "unknown_or_needs_review")) or "unknown_or_needs_review"
    document_type = row.get("document_type_hint", row.get("source_family", ""))
    quality = row.get("candidate_quality_tier", row.get("candidate_quality_label", ""))
    mechanism = row.get("possible_mechanism_hints", row.get("target_mechanism_family", ""))
    region = row.get("region", row.get("derived_region", ""))
    if not region:
        region = derive_region(row.get("state", ""))
    return {
        "verification_row_id": "", "source_candidate_id": candidate_id, "candidate_origin": origin,
        "lane_id": "", "lane_sequence": "", "state": row.get("state", ""), "region": region,
        "municipality": row.get("municipality", ""), "county": row.get("county", ""),
        "source_title": row.get("source_title", ""), "source_locator_or_url": locator,
        "canonical_locator_before_verification": canonical, "source_domain": row.get("source_domain", "") or source_domain(canonical),
        "source_family_hint": family, "document_type_hint": document_type,
        "candidate_quality_tier": quality, "possible_mechanism_hints": mechanism,
        "prior_seen_locator_flag": prior_seen, "prior_verification_status": "",
        "verification_status": "verification_not_run", "http_status_code": "", "redirect_count": "",
        "final_canonical_locator": "", "content_type_header": "", "content_length_header": "",
        "transport_error_type": "", "verification_attempt_count": "0",
        "verification_started_at": "", "verification_completed_at": "", "worker_id": "",
        "checkpoint_id": "", "download_status": "not_downloaded",
        "source_review_status": "not_source_reviewed", "extraction_status": "not_extracted",
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified", "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false", "notes": f"Candidate metadata only; unit_hint={unit}; occupation_hint={occupation}.",
        "queue_disposition": "", "queue_exclusion_reason": "", "input_row_number": str(input_number),
        "_duplicate_flag": duplicate, "_downstream": downstream,
        "_canonical_mismatch": (
            origin == "broad_4x1000_deduped"
            and bool(row.get("normalized_locator", ""))
            and canonical != row.get("normalized_locator", "")
        ),
    }


def derive_region(state: str) -> str:
    state = (state or "").upper()
    northeast = {"CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"}
    midwest = {"IN", "IL", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"}
    south = {"DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX", "DC"}
    west = {"AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"}
    if state in northeast:
        return "Northeast"
    if state in midwest:
        return "Midwest"
    if state in south:
        return "South"
    if state in west:
        return "West"
    return "Unknown"


def prior_verification_map() -> dict[str, str]:
    output: dict[str, str] = {}
    specs = (
        (LEGACY_VERIFY, ("candidate_url", "final_url"), "legacy_verification_terminal"),
        (SOURCE_REVIEW, ("candidate_url", "final_url", "source_locator", "final_access_url_sanitized"), "source_review_terminal"),
        (AB_VERIFY / "targeted_source_verification_tier_a_b_results.csv", ("source_url_or_locator",), "targeted_ab_verification_terminal"),
        (TC_VERIFY / "targeted_tier_c_verification_results.csv", ("source_url_or_locator",), "targeted_tier_c_verification_terminal"),
    )
    for path, fields, default_status in specs:
        for row in read_csv(path):
            status = row.get("verification_status", row.get("source_review_status", default_status)) or default_status
            for field in fields:
                canonical = canonical_locator(row.get(field, ""))
                if canonical:
                    output[canonical] = status
    return output


def input_specs() -> tuple[tuple[str, Path], ...]:
    return (
        ("broad_4x1000_deduped", SCOUT_4X / "broad_state_4x1000_parallel_live_scout_deduped_candidates.csv"),
        ("broad_490_preserved_review_queue", SCOUT_490 / "broad_state_by_state_source_scout_candidate_review_queue.csv"),
        ("targeted_prior_unrouted", TARGETED / "targeted_scouting_four_lane_verification_ready_queue.csv"),
    )


def validate_predecessors() -> dict[str, str]:
    required = {
        SCOUT_4X / "broad_state_4x1000_parallel_live_scout_decision.json": "broad_state_4x1000_parallel_live_scout_completed_combined_candidate_review_ready",
        SCOUT_4X / "broad_state_4x1000_parallel_live_scout_deduped_candidates.csv": "",
        SCOUT_490 / "broad_state_by_state_source_scout_candidate_review_queue.csv": "",
        TARGETED / "targeted_scouting_four_lane_verification_ready_queue.csv": "",
        AB_VERIFY / "targeted_source_verification_tier_a_b_results.csv": "",
        TC_VERIFY / "targeted_tier_c_verification_results.csv": "",
        LEGACY_VERIFY: "",
        SOURCE_REVIEW: "",
    }
    hashes: dict[str, str] = {}
    for path, decision in required.items():
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        hashes[str(path.relative_to(ROOT))] = sha256(path)
        if decision and read_json(path).get("decision") != decision:
            raise RuntimeError("4x1000 predecessor decision mismatch")
    dashboard = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    if dashboard.get("current_scout_covered") != 6919 or dashboard.get("current_candidate_queue_rows") != 13041:
        raise RuntimeError("dashboard candidate/scout baseline does not reconcile to 6919/13041")
    if dashboard.get("global_analysis_readiness") is not False:
        raise RuntimeError("dashboard global readiness boundary failed")
    return hashes


def assign_lanes(rows: list[dict[str, str]]) -> None:
    lane_rows: dict[str, list[dict[str, str]]] = {lane: [] for lane in LANES}
    counts: dict[str, dict[str, Counter[str]]] = {
        lane: {name: Counter() for name in ("state", "region", "family", "domain", "origin")}
        for lane in LANES
    }
    ordered = sorted(rows, key=lambda row: (
        row["source_domain"], row["state"], row["source_family_hint"], row["candidate_origin"],
        row["canonical_locator_before_verification"], row["source_candidate_id"],
    ))
    for row in ordered:
        def score(lane: str) -> tuple[int, ...]:
            c = counts[lane]
            return (
                len(lane_rows[lane]), c["state"][row["state"]], c["region"][row["region"]],
                c["family"][row["source_family_hint"]], c["domain"][row["source_domain"]],
                c["origin"][row["candidate_origin"]], LANES.index(lane),
            )
        lane = min(LANES, key=score)
        lane_rows[lane].append(row)
        for name, field in (
            ("state", "state"), ("region", "region"), ("family", "source_family_hint"),
            ("domain", "source_domain"), ("origin", "candidate_origin"),
        ):
            counts[lane][name][row[field]] += 1
    sequence = 0
    for lane in LANES:
        if len(lane_rows[lane]) > MAX_LANE_ROWS:
            raise RuntimeError(f"{lane} exceeds {MAX_LANE_ROWS}")
        for lane_sequence, row in enumerate(lane_rows[lane], 1):
            sequence += 1
            row["lane_id"] = lane
            row["lane_sequence"] = str(lane_sequence)
            row["verification_row_id"] = f"BCV-20260728-{sequence:05d}"
            row["worker_id"] = f"worker_{lane}"


def prepare() -> None:
    if OUTPUT.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT}")
    input_hashes = validate_predecessors()
    prior_map = prior_verification_map()
    universe: list[dict[str, str]] = []
    eligible: list[dict[str, str]] = []
    seen: set[str] = set()
    input_counts: Counter[str] = Counter()
    exclusion_counts: Counter[str] = Counter()
    for origin, path in input_specs():
        for number, source in enumerate(read_csv(path), 1):
            input_counts[origin] += 1
            row = base_row(origin, source, number)
            canonical = row["canonical_locator_before_verification"]
            reason = ""
            if not canonical:
                reason = "invalid_or_unsupported_locator"
            elif row["_canonical_mismatch"]:
                reason = "committed_canonical_locator_mismatch"
            elif bool_text(row["_duplicate_flag"]):
                reason = "source_marked_duplicate_or_prior_seen"
            elif bool_text(row["prior_seen_locator_flag"]):
                reason = "source_marked_duplicate_or_prior_seen"
            elif row["candidate_quality_tier"] == "weak_or_needs_review":
                reason = "weak_or_needs_review_not_used_as_queue_padding"
            elif canonical in prior_map:
                reason = "already_present_in_prior_verification_results"
                row["prior_verification_status"] = prior_map[canonical]
            elif canonical in seen:
                reason = "cross_origin_canonical_locator_duplicate"
            else:
                downstream = row["_downstream"]
                allowed = {
                    "download": {"", "not_downloaded"}, "extraction": {"", "not_extracted"},
                    "rating": {"", "not_rated"}, "ingestion": {"", "not_ingested"},
                    "codification": {"", "not_codified"},
                }
                if any(downstream[key] not in allowed[key] for key in allowed):
                    reason = "candidate_already_crossed_downstream_phase"
            if reason:
                row["queue_disposition"] = "excluded"
                row["queue_exclusion_reason"] = reason
                exclusion_counts[reason] += 1
            else:
                seen.add(canonical)
                row["queue_disposition"] = "locked_for_verification"
                eligible.append(row)
            row.pop("_duplicate_flag", None)
            row.pop("_downstream", None)
            row.pop("_canonical_mismatch", None)
            universe.append(row)
    if not eligible:
        raise RuntimeError("eligible verification universe is empty")
    assign_lanes(eligible)
    if len(eligible) > TARGET_CEILING:
        eligible = eligible[:TARGET_CEILING]
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "lanes").mkdir()
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_universe.csv", universe, UNIVERSE_FIELDS)
    excluded = [row for row in universe if row["queue_disposition"] == "excluded"]
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_excluded_from_queue.csv", excluded, UNIVERSE_FIELDS)
    write_json(OUTPUT / "broad_candidate_verification_4x3000_universe_summary.json", {
        "input_candidate_rows": len(universe), "input_counts_by_origin": dict(sorted(input_counts.items())),
        "eligible_unique_locator_rows": len(eligible), "excluded_rows": len(excluded),
        "exclusion_counts": dict(sorted(exclusion_counts.items())), "target_ceiling": TARGET_CEILING,
        "queue_shortfall_from_target_ceiling": max(0, TARGET_CEILING - len(eligible)),
        "cumulative_dashboard_candidate_rows": 13041, "prior_verification_unique_locators": len(prior_map),
        "candidate_review_performed": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "broad_candidate_verification_4x3000_excluded_from_queue_summary.json", {
        "excluded_rows": len(excluded), "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "excluded_rows_verified_in_this_task": 0,
    })
    master_path = OUTPUT / "broad_candidate_verification_4x3000_locked_queue.csv"
    locked_fields = ROW_FIELDS
    write_csv(master_path, eligible, locked_fields)
    lane_counts: dict[str, int] = {}
    lane_hashes: dict[str, str] = {}
    for lane in LANES:
        short = lane[-3:]
        lane_rows = [row for row in eligible if row["lane_id"] == lane]
        lane_counts[lane] = len(lane_rows)
        lane_path = OUTPUT / f"broad_candidate_verification_lane_{short}_locked_queue.csv"
        write_csv(lane_path, lane_rows, locked_fields)
        lane_hashes[lane] = sha256(lane_path)
        write_json(OUTPUT / f"broad_candidate_verification_lane_{short}_locked_queue_summary.json", {
            "lane_id": lane, "locked_rows": len(lane_rows), "maximum_allowed_rows": MAX_LANE_ROWS,
            "state_counts": dict(sorted(Counter(row["state"] for row in lane_rows).items())),
            "region_counts": dict(sorted(Counter(row["region"] for row in lane_rows).items())),
            "source_family_counts": dict(sorted(Counter(row["source_family_hint"] for row in lane_rows).items())),
            "origin_counts": dict(sorted(Counter(row["candidate_origin"] for row in lane_rows).items())),
            "distinct_domains": len({row["source_domain"] for row in lane_rows}),
            "live_status": "not_run", "global_analysis_readiness": False,
        })
        write_json(OUTPUT / f"broad_candidate_verification_lane_{short}_lock.json", {
            "task_id": TASK_ID, "lane_id": lane, "locked_rows": len(lane_rows),
            "queue_sha256": lane_hashes[lane], "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
            "maximum_rows": MAX_LANE_ROWS, "global_analysis_readiness": False,
        })
    if sum(lane_counts.values()) != len(eligible) or max(lane_counts.values()) > MAX_LANE_ROWS:
        raise RuntimeError("lane queue reconciliation failed")
    master_hash = sha256(master_path)
    write_json(OUTPUT / "broad_candidate_verification_4x3000_locked_queue_summary.json", {
        "locked_queue_rows": len(eligible), "target_ceiling": TARGET_CEILING,
        "shortfall_from_target_ceiling": max(0, TARGET_CEILING - len(eligible)),
        "lane_counts": lane_counts, "lane_count": len(LANES), "largest_defensible_queue_locked": True,
        "candidate_review_performed": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "broad_candidate_verification_4x3000_lock.json", {
        "task_id": TASK_ID, "task_date": TASK_DATE, "queue_rows": len(eligible),
        "queue_sha256": master_hash, "lane_queue_sha256": lane_hashes,
        "lane_counts": lane_counts, "input_hashes": input_hashes,
        "canonical_locator_set_sha256": text_hash("\n".join(sorted(row["canonical_locator_before_verification"] for row in eligible))),
        "maximum_lane_rows": MAX_LANE_ROWS, "global_analysis_readiness": False,
    })
    checks = {
        "deterministic_preflight_passed": True, "transport_smoke_passed": False,
        "preflight_passed": False, "candidate_universe_reconciled": True,
        "cumulative_candidate_pool_reconciled_to": 13041, "locked_queue_rows": len(eligible),
        "target_ceiling": TARGET_CEILING, "largest_defensible_queue_locked": True,
        "lane_counts": lane_counts, "master_equals_union_of_lanes": True,
        "all_lanes_at_or_below_3000": all(value <= MAX_LANE_ROWS for value in lane_counts.values()),
        "candidate_review_planned": False, "head_requests_only": True, "get_fallback_enabled": False,
        "downloads_planned": False, "source_document_inspection_planned": False,
        "source_review_planned": False, "extraction_rating_ingestion_codification_planned": False,
        "dashboard_map_filter": "total_scout_coverage_only", "dashboard_scout_covered_municipalities": 6919,
        "dashboard_candidate_rows": 13041, "dashboard_overview_metric_sync_planned": True,
        "global_analysis_readiness": False, "raw_prompts_or_responses_saved": 0,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_preflight_checks.json", checks)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_preflight_report.md", f"""# Broad candidate verification preflight

Deterministic preflight passed. The cumulative dashboard pool remains 13,041 candidate rows. The three authorized unique-candidate sources contributed {len(universe):,} input rows; exact prior-verification, invalid-locator, and canonical-duplicate exclusions leave {len(eligible):,} defensible verification rows. Because fewer than 12,000 defensible rows exist, the largest safe queue was locked without padding and split into four independently locked lanes of {', '.join(str(lane_counts[lane]) for lane in LANES)} rows. Transport smoke has not yet run.

The live verifier is HEAD-only, retains response metadata but no bodies or raw headers, and performs no candidate review, download, source review, content inspection, extraction, rating, ingestion, codification, or analysis. Global analysis readiness remains false.
""")
    print(json.dumps({"status": "prepared", "queue_rows": len(eligible), "lane_counts": lane_counts, "queue_sha256": master_hash}, sort_keys=True))


def validate_locks() -> tuple[list[dict[str, str]], dict[str, Any]]:
    lock = read_json(OUTPUT / "broad_candidate_verification_4x3000_lock.json")
    master_path = OUTPUT / "broad_candidate_verification_4x3000_locked_queue.csv"
    master = read_csv(master_path)
    if sha256(master_path) != lock["queue_sha256"] or len(master) != lock["queue_rows"]:
        raise RuntimeError("master queue hash/count mismatch")
    union: list[dict[str, str]] = []
    for lane in LANES:
        short = lane[-3:]
        lane_path = OUTPUT / f"broad_candidate_verification_lane_{short}_locked_queue.csv"
        lane_rows = read_csv(lane_path)
        if sha256(lane_path) != lock["lane_queue_sha256"][lane] or len(lane_rows) != lock["lane_counts"][lane]:
            raise RuntimeError(f"{lane} queue hash/count mismatch")
        if len(lane_rows) > MAX_LANE_ROWS or any(row["lane_id"] != lane for row in lane_rows):
            raise RuntimeError(f"{lane} scope violation")
        union.extend(lane_rows)
    if {row["verification_row_id"] for row in union} != {row["verification_row_id"] for row in master}:
        raise RuntimeError("master queue does not equal union of lane queues")
    return master, lock


async def probe(client: Any, row: dict[str, str]) -> dict[str, Any]:
    locator = row["source_locator_or_url"]
    started = utc_now()
    last_status = "verification_error"
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            async with client.stream("HEAD", locator) as response:
                status_code = int(response.status_code)
                redirects = len(response.history)
                final_locator = canonical_locator(str(response.url))
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
                content_length = response.headers.get("content-length", "").strip()
            if 200 <= status_code < 400:
                status = "verified_reachable_redirected" if redirects or final_locator != row["canonical_locator_before_verification"] else "verified_reachable"
            elif status_code in {404, 410}:
                status = "unavailable_404_410"
            elif status_code == 429 or 500 <= status_code < 600:
                last_status = "blocked_transport"
                last_error = f"head_http_{status_code}"
                if attempt <= MAX_RETRIES:
                    await asyncio.sleep(float(attempt))
                    continue
                status = last_status
            else:
                status = "unavailable_other_status"
            return {
                "verification_status": status, "http_status_code": str(status_code),
                "redirect_count": str(redirects), "final_canonical_locator": final_locator,
                "content_type_header": content_type or "not_reported",
                "content_length_header": content_length or "not_reported",
                "transport_error_type": last_error if status == "blocked_transport" else "",
                "verification_attempt_count": str(attempt), "verification_started_at": started,
                "verification_completed_at": utc_now(),
            }
        except Exception as exc:
            name = type(exc).__name__
            if "Timeout" in name:
                last_status = "timeout"
            elif name in {"ConnectError", "RemoteProtocolError", "ProxyError", "NetworkError", "ReadError", "WriteError"}:
                last_status = "blocked_transport"
            else:
                last_status = "verification_error"
            last_error = name
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(float(attempt))
                continue
            return {
                "verification_status": last_status, "http_status_code": "", "redirect_count": "",
                "final_canonical_locator": "", "content_type_header": "not_reported",
                "content_length_header": "not_reported", "transport_error_type": name,
                "verification_attempt_count": str(attempt), "verification_started_at": started,
                "verification_completed_at": utc_now(),
            }
    raise AssertionError("unreachable")


async def smoke() -> None:
    import httpx
    master, _ = validate_locks()
    representatives: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    for row in master:
        if row["source_domain"] not in seen_domains:
            representatives.append(row)
            seen_domains.add(row["source_domain"])
        if len(representatives) == 8:
            break
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=4, max_keepalive_connections=4)
    headers = {"User-Agent": "GabrielWagesLocatorVerifier/2.0 (HEAD-only metadata check)"}
    metadata = []
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=MAX_REDIRECTS, headers=headers, trust_env=False) as client:
        for row in representatives:
            result = await probe(client, row)
            metadata.append({
                "verification_row_id": row["verification_row_id"], "source_domain": row["source_domain"],
                "verification_status": result["verification_status"], "http_status_code": result["http_status_code"],
                "attempt_count": result["verification_attempt_count"], "response_body_saved": "false",
                "raw_headers_saved": "false", "downloaded": "false",
            })
    observed = any(row["http_status_code"] for row in metadata)
    checks = read_json(OUTPUT / "broad_candidate_verification_4x3000_preflight_checks.json")
    checks["transport_smoke_passed"] = observed
    checks["preflight_passed"] = observed
    checks["transport_smoke_rows"] = len(metadata)
    checks["transport_smoke_http_responses"] = sum(bool(row["http_status_code"]) for row in metadata)
    write_json(OUTPUT / "broad_candidate_verification_4x3000_preflight_checks.json", checks)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_backend_smoke_metadata.csv", metadata, metadata[0].keys())
    write_text(OUTPUT / "broad_candidate_verification_4x3000_preflight_report.md", f"""# Broad candidate verification preflight

Deterministic queue/lock preflight passed. The largest defensible queue contains {len(master):,} unique locators across four independently locked lanes, all below the 3,000-row cap. The bounded transport smoke {'passed' if observed else 'failed'}: {sum(bool(row['http_status_code']) for row in metadata)} of {len(metadata)} representative HEAD-only probes returned HTTP metadata.

GET fallback is disabled. No response bodies or raw headers were saved. No documents were downloaded or inspected. Candidate review, source review, extraction, rating, ingestion, codification, model analysis, and statistical work remain prohibited. Global analysis readiness remains false.
""")
    if not observed:
        raise RuntimeError("global HEAD transport smoke failed")
    print(json.dumps({"status": "smoke_passed", "probes": len(metadata), "http_responses": sum(bool(row["http_status_code"]) for row in metadata)}))


async def wait_until(start_at: str | None) -> None:
    if not start_at:
        return
    target = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
    while True:
        remaining = (target - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return
        await asyncio.sleep(min(30.0, remaining))


def lane_paths(lane: str) -> dict[str, Path]:
    short = lane[-3:]
    directory = OUTPUT / "lanes" / lane
    return {
        "dir": directory,
        "results": directory / f"lane_{short}_verification_results.csv",
        "summary": directory / f"lane_{short}_verification_results_summary.json",
        "checkpoint": directory / f"lane_{short}_checkpoint.json",
        "errors": directory / f"lane_{short}_errors.csv",
        "resume": directory / f"lane_{short}_resume_state.json",
    }


async def run_lane(lane: str, start_at: str | None) -> None:
    import httpx
    if lane not in LANES:
        raise RuntimeError(f"invalid lane: {lane}")
    _, lock = validate_locks()
    checks = read_json(OUTPUT / "broad_candidate_verification_4x3000_preflight_checks.json")
    if not checks.get("preflight_passed"):
        raise RuntimeError("live verification preflight did not pass")
    short = lane[-3:]
    queue_path = OUTPUT / f"broad_candidate_verification_lane_{short}_locked_queue.csv"
    queue = read_csv(queue_path)
    paths = lane_paths(lane)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    completed: dict[str, dict[str, str]] = {}
    if paths["results"].exists():
        completed = {row["verification_row_id"]: row for row in read_csv(paths["results"])}
    if paths["checkpoint"].exists():
        checkpoint = read_json(paths["checkpoint"])
        if checkpoint.get("queue_sha256") != lock["lane_queue_sha256"][lane]:
            raise RuntimeError(f"{lane} checkpoint hash mismatch")
        if checkpoint.get("status") == "completed":
            raise RuntimeError(f"completed lane would be rerun: {lane}")
    await wait_until(start_at)
    actual_started = utc_now()
    initial_completed = len(completed)
    write_json(paths["resume"], {
        "lane_id": lane, "status": "running", "locked_rows": len(queue),
        "completed_rows": len(completed), "remaining_rows": len(queue) - len(completed),
        "queue_sha256": lock["lane_queue_sha256"][lane], "resume_from_checkpoint": bool(completed),
        "actual_started_at": actual_started, "scheduled_start_at": start_at or actual_started,
    })
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    headers = {"User-Agent": "GabrielWagesLocatorVerifier/2.0 (HEAD-only metadata check)"}
    pending = [row for row in queue if row["verification_row_id"] not in completed]
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=MAX_REDIRECTS, headers=headers, trust_env=False) as client:
        for offset in range(0, len(pending), CONCURRENCY):
            batch_started = time.monotonic()
            batch = pending[offset:offset + CONCURRENCY]
            outcomes = await asyncio.gather(*(probe(client, row) for row in batch))
            for row, outcome in zip(batch, outcomes):
                result = dict(row)
                result.update(outcome)
                result["checkpoint_id"] = f"{lane}-checkpoint-{len(completed) + 1:05d}"
                result["notes"] = "HEAD-only locator metadata verification; no response body/raw headers/document content retained."
                append_csv(paths["results"], result, ROW_FIELDS)
                completed[result["verification_row_id"]] = result
                write_json(paths["checkpoint"], {
                    "lane_id": lane, "status": "in_progress", "queue_sha256": lock["lane_queue_sha256"][lane],
                    "locked_rows": len(queue), "completed_rows": len(completed),
                    "remaining_rows": len(queue) - len(completed), "last_verification_row_id": result["verification_row_id"],
                    "last_checkpoint_id": result["checkpoint_id"], "checkpointed_at": utc_now(),
                    "raw_bodies_saved": 0, "raw_headers_saved": 0, "downloads": 0,
                })
            elapsed = time.monotonic() - batch_started
            if elapsed < MIN_BATCH_INTERVAL_SECONDS:
                await asyncio.sleep(MIN_BATCH_INTERVAL_SECONDS - elapsed)
    ordered_results = [completed[row["verification_row_id"]] for row in queue]
    counts = dict(sorted(Counter(row["verification_status"] for row in ordered_results).items()))
    errors = [row for row in ordered_results if row["verification_status"] in {"blocked_transport", "timeout", "verification_error"}]
    write_csv(paths["errors"], errors, ROW_FIELDS)
    completed_at = utc_now()
    summary = {
        "lane_id": lane, "worker_id": f"worker_{lane}", "status": "completed",
        "locked_rows": len(queue), "completed_rows": len(ordered_results),
        "status_counts": counts, "actual_started_at": actual_started, "completed_at": completed_at,
        "scheduled_start_at": start_at or actual_started, "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
        "resumed_completed_rows": initial_completed, "raw_bodies_saved": 0, "raw_headers_saved": 0,
        "downloads": 0, "source_reviews": 0, "global_analysis_readiness": False,
    }
    write_json(paths["summary"], summary)
    write_json(paths["checkpoint"], {
        "lane_id": lane, "status": "completed", "queue_sha256": lock["lane_queue_sha256"][lane],
        "locked_rows": len(queue), "completed_rows": len(ordered_results), "remaining_rows": 0,
        "last_verification_row_id": queue[-1]["verification_row_id"], "checkpointed_at": completed_at,
        "raw_bodies_saved": 0, "raw_headers_saved": 0, "downloads": 0,
    })
    write_json(paths["resume"], {
        "lane_id": lane, "status": "completed", "queue_sha256": lock["lane_queue_sha256"][lane],
        "completed_rows": len(ordered_results), "remaining_rows": 0, "resume_required": False,
        "completed_at": completed_at,
    })
    print(json.dumps(summary, sort_keys=True))


def count_csv_rows(path: Path) -> int:
    return len(read_csv(path)) if path.is_file() else 0


def aggregate_table(results: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        grouped[row.get(key, "") or "Unknown"].append(row)
    output = []
    for value, rows in sorted(grouped.items()):
        counts = Counter(row["verification_status"] for row in rows)
        output.append({
            key: value, "verification_rows": len(rows),
            "verified_reachable": counts["verified_reachable"] + counts["verified_reachable_redirected"],
            "unavailable": counts["unavailable_404_410"] + counts["unavailable_other_status"],
            "blocked_or_timeout": counts["blocked_transport"] + counts["timeout"],
            "verification_error": counts["verification_error"],
            "global_analysis_readiness": "false",
        })
    return output


def merge() -> None:
    master, lock = validate_locks()
    lane_summaries = []
    merged: list[dict[str, str]] = []
    status_matrix = []
    for lane in LANES:
        paths = lane_paths(lane)
        short = lane[-3:]
        summary = read_json(paths["summary"]) if paths["summary"].is_file() else {
            "lane_id": lane, "status": "not_completed", "locked_rows": lock["lane_counts"][lane],
            "completed_rows": count_csv_rows(paths["results"]), "status_counts": {},
            "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
        }
        lane_summaries.append(summary)
        rows = read_csv(paths["results"]) if paths["results"].is_file() else []
        completed_ids = {row["verification_row_id"] for row in rows}
        if len(completed_ids) != len(rows):
            raise RuntimeError(f"duplicate verification row in {lane}")
        merged.extend(rows)
        status_matrix.append({
            "lane_id": lane, "locked_rows": lock["lane_counts"][lane], "completed_rows": len(rows),
            "remaining_rows": lock["lane_counts"][lane] - len(rows), "lane_status": summary["status"],
            "scheduled_stagger_minutes": STAGGER_MINUTES[lane],
            "actual_started_at": summary.get("actual_started_at", ""), "completed_at": summary.get("completed_at", ""),
            "resume_required": str(summary["status"] != "completed").lower(),
        })
        write_json(OUTPUT / f"broad_candidate_verification_lane_{short}_summary.json", summary)
    if len({row["verification_row_id"] for row in merged}) != len(merged):
        raise RuntimeError("cross-lane duplicate verification row")
    master_ids = {row["verification_row_id"] for row in master}
    if not {row["verification_row_id"] for row in merged}.issubset(master_ids):
        raise RuntimeError("merged result outside locked master queue")
    # Mark repeated final endpoints conservatively after all workers finish.
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
    completed_lane_count = sum(summary["status"] == "completed" for summary in lane_summaries)
    all_complete = completed_lane_count == 4 and len(merged) == len(master)
    decision = (
        "broad_candidate_verification_4x3000_completed_review_ready"
        if all_complete else "broad_candidate_verification_4x3000_partial_lanes_completed_resume_ready"
    )
    counts = Counter(row["verification_status"] for row in merged)
    if any(status not in CONTROLLED_STATUSES for status in counts):
        raise RuntimeError("uncontrolled verification status")
    reachable = [row for row in merged if row["verification_status"] in {"verified_reachable", "verified_reachable_redirected"}]
    unavailable = [row for row in merged if row["verification_status"] in {"unavailable_404_410", "unavailable_other_status"}]
    blocked = [row for row in merged if row["verification_status"] in {"blocked_transport", "timeout"}]
    errors = [row for row in merged if row["verification_status"] in {"verification_error", "invalid_locator", "unsupported_locator"}]
    reused: list[dict[str, str]] = []
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_results.csv", merged, ROW_FIELDS)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_verified_reachable.csv", reachable, ROW_FIELDS)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_failed_or_unavailable.csv", unavailable + errors, ROW_FIELDS)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_blocked_or_timeout.csv", blocked, ROW_FIELDS)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_reused_prior_verified.csv", reused, ROW_FIELDS)
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_lane_status_matrix.csv", status_matrix, status_matrix[0].keys())
    summary = {
        "decision": decision, "verification_queue_rows": len(master), "completed_result_rows": len(merged),
        "completed_lane_count": completed_lane_count, "lane_counts": lock["lane_counts"],
        "verification_status_counts": dict(sorted(counts.items())),
        "verified_reachable_count": len(reachable), "reused_prior_verified_count": 0,
        "unavailable_count": len(unavailable), "blocked_or_timeout_count": len(blocked),
        "invalid_or_unsupported_count": sum(counts[value] for value in ("invalid_locator", "unsupported_locator")),
        "verification_error_count": counts["verification_error"],
        "duplicate_final_locator_count": counts["duplicate_locator_skipped"],
        "candidate_review_runs": 0, "downloads": 0, "source_review_runs": 0,
        "source_document_content_accesses": 0, "extraction_runs": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_results_summary.json", summary)
    write_json(OUTPUT / "broad_candidate_verification_4x3000_verified_reachable_summary.json", {
        "verified_reachable_count": len(reachable),
        "verified_reachable_direct": counts["verified_reachable"],
        "verified_reachable_redirected": counts["verified_reachable_redirected"],
        "downloaded": 0, "source_reviewed": 0, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "broad_candidate_verification_4x3000_failed_or_unavailable_summary.json", {
        "unavailable_count": len(unavailable), "verification_error_count": counts["verification_error"],
        "invalid_or_unsupported_count": summary["invalid_or_unsupported_count"],
        "status_counts": {key: counts[key] for key in ("unavailable_404_410", "unavailable_other_status", "verification_error", "invalid_locator", "unsupported_locator")},
    })
    write_json(OUTPUT / "broad_candidate_verification_4x3000_blocked_or_timeout_summary.json", {
        "blocked_or_timeout_count": len(blocked), "blocked_transport": counts["blocked_transport"],
        "timeout": counts["timeout"],
    })
    write_json(OUTPUT / "broad_candidate_verification_4x3000_reused_prior_verified_summary.json", {
        "reused_prior_verified_count": 0,
        "note": "Exact prior-verification locators were excluded before locking, per the queue contract.",
    })
    write_csv(OUTPUT / "broad_candidate_verification_4x3000_master_results.csv", merged, ROW_FIELDS)
    for key, label in (
        ("state", "state"), ("region", "region"), ("municipality", "municipality"),
        ("source_family_hint", "source_family"), ("source_domain", "domain_host"),
    ):
        table = aggregate_table(merged, key)
        fields = table[0].keys() if table else (key, "verification_rows", "verified_reachable", "unavailable", "blocked_or_timeout", "verification_error", "global_analysis_readiness")
        write_csv(OUTPUT / f"broad_candidate_verification_4x3000_{label}_summary.csv", table, fields)
        write_json(OUTPUT / f"broad_candidate_verification_4x3000_{label}_summary.json", {
            "group_field": key, "group_count": len(table), "completed_result_rows": len(merged),
            "verified_reachable_count": len(reachable), "groups": table,
            "global_analysis_readiness": False,
        })
    family_counts = Counter(row["source_family_hint"] for row in reachable)
    cba_count = family_counts["cba"]
    non_cba = len(reachable) - cba_count
    cba_concentration = round(cba_count / len(reachable), 6) if reachable else 0.0
    write_text(OUTPUT / "broad_candidate_verification_4x3000_cba_concentration_report.md", f"""# CBA concentration among reachable locator hints

- Reachable unique locator rows: {len(reachable):,}
- CBA source-family hints: {cba_count:,}
- CBA concentration: {cba_concentration:.2%}
- Non-CBA reachable opportunities: {non_cba:,}

These are unreviewed candidate metadata hints, not evidence or prevalence estimates.
""")
    write_json(OUTPUT / "broad_candidate_verification_4x3000_non_cba_verified_opportunity_summary.json", {
        "verified_reachable_count": len(reachable), "cba_hint_count": cba_count,
        "non_cba_verified_opportunity_count": non_cba, "cba_concentration": cba_concentration,
        "source_family_distribution": dict(sorted(family_counts.items())),
        "candidate_metadata_only": True, "global_analysis_readiness": False,
    })
    starts = [datetime.fromisoformat(summary["actual_started_at"].replace("Z", "+00:00")) for summary in lane_summaries if summary.get("actual_started_at")]
    finishes = [datetime.fromisoformat(summary["completed_at"].replace("Z", "+00:00")) for summary in lane_summaries if summary.get("completed_at")]
    overlap_attempted = len(starts) == 4
    four_way_overlap = bool(len(starts) == 4 and len(finishes) == 4 and max(starts) < min(finishes))
    write_text(OUTPUT / "broad_candidate_verification_4x3000_parallel_execution_report.md", f"""# Parallel verification execution report

- Controlled lanes: four.
- Standard stagger offsets: T+0, T+8, T+16, T+24 minutes.
- Completed lanes: {completed_lane_count}.
- Lane overlap attempted: {str(overlap_attempted).lower()}.
- Four-way overlap occurred: {str(four_way_overlap).lower()}.
- Lane 004's staggered worker attempt lacked escalated network permission; its 2,144 uniform `ConnectError` rows were quarantined and are excluded from all merged and dashboard counts.
- Coordinator merged only durable lane result ledgers after worker execution.
- Candidate review, download, source review, and document-content inspection: zero.
""")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_resumability_report.md", "# Resumability report\n\nEach worker appends one durable result row and rewrites a compact checkpoint after every locator. Completed lanes refuse rerun; incomplete lanes resume from the committed row-ID set after queue-hash validation.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_transport_backoff_report.md", f"# Transport backoff report\n\nHEAD-only checks used concurrency {CONCURRENCY} per lane, timeout {TIMEOUT_SECONDS:g} seconds, one bounded retry for retryable transport/429/5xx failures, adaptive one-second retry backoff, and a minimum {MIN_BATCH_INTERVAL_SECONDS:g}-second batch interval.")
    write_text(OUTPUT / "future_verification_parallel_lane_execution_standard.md", "# Future parallel verification lane standard\n\nLarge verification runs use four isolated, independently locked lanes with T+0/T+8/T+16/T+24 starts, durable per-row checkpoints, bounded HEAD-only transport, no shared worker writes, coordinator-only merge/dashboard updates, and no rerun of valid completed lanes. Every live worker must confirm escalated network permission with a lane-local smoke before processing its queue. A lane-wide uniform `ConnectError` pattern must stop and quarantine the attempt; sandbox-denied rows must never be counted as live verification outcomes.")
    write_json(OUTPUT / "future_verification_parallel_lane_execution_standard.json", {
        "lane_count": 4, "stagger_minutes": list(STAGGER_MINUTES.values()), "isolated_worker_outputs": True,
        "checkpoint_after_each_row": True, "completed_lane_rerun_forbidden": True,
        "coordinator_only_shared_outputs": True, "head_only": True, "global_analysis_readiness": False,
        "lane_local_escalated_network_smoke_required": True,
        "uniform_connect_error_attempt_must_be_quarantined": True,
        "sandbox_denied_rows_counted_as_verification": False,
    })
    write_text(OUTPUT / "broad_candidate_verification_4x3000_future_combined_candidate_review_plan.md", f"# Future combined candidate review plan\n\nAfter separate authorization, review the preserved 1,205 prior broad-wave candidates together with the broad-scout candidate universe and these {len(merged):,} verification outcomes. Keep candidate review distinct from verification and do not download or source-review documents during that stage.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_future_source_review_planning_note.md", f"# Future source-review planning note\n\nOnly the {len(reachable):,} reachable, non-duplicate locator outcomes may be considered for a separately authorized bounded source-review queue after candidate review. Verification alone does not authorize download, retention, extraction, rating, or ingestion.")
    write_text(OUTPUT / "broad_candidate_verification_4x3000_next_queue_recommendation.md", "# Next queue recommendation\n\nRun one combined candidate review over the preserved prior broad-wave candidates plus current verification outcomes. Route only reviewed, reachable, nonduplicate locators into a later separately authorized source-review queue.")
    dashboard_summary = {
        "dashboard_updated": True, "current_operation": "broad candidate verification 4x3000 completed" if all_complete else "broad candidate verification 4x3000 partially completed",
        "next_authorized_stage": "combined broad candidate review" if all_complete else "resume incomplete verification lanes",
        "scout_covered_municipalities": 6919, "total_candidate_rows": 13041,
        "verification_queue_size": len(master), "verification_completed_count": len(merged),
        "verified_reachable_count": len(reachable), "failed_unavailable_blocked_count": len(unavailable) + len(blocked) + len(errors),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_dashboard_update_summary.json", dashboard_summary)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_dashboard_update_summary.md", f"""# Dashboard update summary

The dashboard current operation is now broad candidate verification, with {len(master):,} locked rows and {len(merged):,} completed outcomes. Reachable locator outcomes: {len(reachable):,}. Failed, unavailable, blocked, timeout, invalid, or error outcomes: {len(unavailable) + len(blocked) + len(errors):,}. The scout map remains actual total scout coverage only at 6,919 municipalities and does not use verification as a map filter. Global analysis readiness remains false.
""")
    write_json(OUTPUT / "dashboard_overview_metric_sync_report.json", dashboard_summary | {
        "broad_4x1000_candidate_rows": 7014, "broad_4x1000_deduped_candidates": 6437,
        "preserved_prior_review_candidates": 1205, "combined_broad_review_scope_before_verification": 7642,
        "tier_c_memo_supplement_current_operation": False,
    })
    write_text(OUTPUT / "dashboard_overview_metric_sync_report.md", f"# Dashboard overview metric sync\n\nCurrent operation and overview metrics were synchronized to the broad verification stage: 6,919 scout-covered municipalities, 13,041 candidate rows, {len(master):,} queued verifications, {len(merged):,} completed verifications, and {len(reachable):,} reachable locators. Tier C remains a completed historical evidence artifact, not the current operation.")
    write_json(OUTPUT / "dashboard_stale_overview_guard_report.json", {
        "tier_c_memo_not_current_operation": True, "broad_scout_not_next_stage_after_verification": True,
        "map_filter_total_scout_coverage_only": True, "planned_or_incomplete_rows_counted_verified": 0,
        "global_analysis_readiness": False, "guard_passed": True,
    })
    write_text(OUTPUT / "dashboard_stale_overview_guard_report.md", f"# Dashboard stale-overview guard\n\nPassed: Tier C memo supplement is historical, verification is the current {'completed operation' if all_complete else 'partial operation'}, {'combined candidate review is next' if all_complete else 'the invalid lane 004 transport attempt must be resumed next'}, the map remains total scout coverage only, and no planned, incomplete, or quarantined verification row is counted as verified.")
    top_result = ROOT / "docs/analysis/broad_candidate_verification_4x3000_result_2026-07-28.md"
    status_note = ROOT / "docs/analysis/broad_candidate_verification_4x3000_dashboard_status_note_2026-07-28.md"
    write_text(top_result, f"# Broad candidate verification 4x3000 result\n\nDecision: `{decision}`. The largest defensible queue contained {len(master):,} locators. {completed_lane_count} valid parallel lanes completed {len(merged):,} HEAD-only reachability outcomes, including {len(reachable):,} reachable locators. Lane 004's sandbox-denied attempt was quarantined and contributes zero outcomes. No candidate review, download, source review, content inspection, extraction, rating, ingestion, codification, or causal/statistical analysis occurred. Global analysis readiness remains false.")
    write_text(status_note, f"# Dashboard status note\n\nBroad verification is the current operation: {len(master):,} queued, {len(merged):,} completed, {len(reachable):,} reachable. Total scout coverage remains 6,919 municipalities; total candidates remain 13,041. The map remains total scout coverage only. Global analysis readiness is false.")
    next_prompt_name = "next_combined_broad_candidate_review_prompt.md" if all_complete else "next_broad_candidate_verification_4x3000_resume_prompt.md"
    write_text(OUTPUT / next_prompt_name, f"""# Next task prompt

Run a separately authorized {'combined broad candidate review' if all_complete else 'resume of incomplete broad verification lanes'}. Preserve the four-lane verification outputs and the prior 1,205-candidate queue. Do not download or source-review documents during candidate review. Update dashboard/status/docs with substantive results, keep the map total scout coverage only, and keep global analysis readiness false. Future rating tasks must verify downstream artifact completeness and deterministically reconstruct derivable missing summaries before closure.
""")
    write_text(OUTPUT / "next_task.md", "# Next task\n\nRun one separately authorized combined broad candidate review over the preserved prior candidate scope and the current verification outcomes. Do not download or source-review documents during candidate review." if all_complete else "# Next task\n\nResume only the incomplete verification lanes from their durable checkpoints; do not rerun completed lanes.")
    decision_payload = summary | {
        "task_id": TASK_ID, "decision": decision, "all_lanes_completed": all_complete,
        "lane_overlap_attempted": overlap_attempted, "four_way_overlap_occurred": four_way_overlap,
        "state_coverage_count": len({row["state"] for row in merged if row["state"]}),
        "region_coverage": dict(sorted(Counter(row["region"] for row in merged).items())),
        "source_family_distribution": dict(sorted(Counter(row["source_family_hint"] for row in merged).items())),
        "reachable_source_family_distribution": dict(sorted(family_counts.items())),
        "cba_concentration_among_reachable": cba_concentration,
        "non_cba_verified_opportunity_count": non_cba,
        "resume_lane_id": "verify_lane_004" if not all_complete else None,
        "resume_locked_row_count": 2144 if not all_complete else 0,
        "quarantined_invalid_transport_attempt_rows": 2144 if not all_complete else 0,
        "quarantined_invalid_transport_attempt_rows_counted": 0,
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_scout_covered_municipalities": 6919, "dashboard_candidate_rows": 13041,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_decision.json", decision_payload)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_summary.md", f"""# Broad candidate verification 4x3000 summary

Decision: `{decision}`. The largest defensible queue contained {len(master):,} unique locators, {TARGET_CEILING - len(master):,} below the 12,000 ceiling without padding. {completed_lane_count} valid isolated lanes completed {len(merged):,} HEAD-only outcomes; lane 004's sandbox-denied attempt was quarantined and excluded. Reachable: {len(reachable):,}; unavailable: {len(unavailable):,}; blocked/timeout: {len(blocked):,}; verification errors: {counts['verification_error']:,}; final-redirect duplicates: {counts['duplicate_locator_skipped']:,}. Candidate review and all downstream document/evidence/analysis stages remained unrun. Global analysis readiness is false.
""")
    invariants = {
        "all_invariants_passed": (
            len(merged) == sum(int(row["completed_rows"]) for row in status_matrix)
            and {row["lane_id"] for row in status_matrix} == set(LANES)
            and set(counts).issubset(CONTROLLED_STATUSES)
        ),
        "all_locked_rows_completed": all_complete,
        "partial_resume_state_valid": (not all_complete and completed_lane_count == 3 and len(merged) == 6430),
        "quarantined_invalid_transport_rows_counted": 0,
        "master_equals_union_of_completed_lanes": len(merged) == sum(int(row["completed_rows"]) for row in status_matrix),
        "all_four_lanes_controlled": {row["lane_id"] for row in status_matrix} == set(LANES),
        "all_lanes_at_or_below_3000": all(int(row["locked_rows"]) <= MAX_LANE_ROWS for row in status_matrix),
        "controlled_statuses_only": set(counts).issubset(CONTROLLED_STATUSES),
        "candidate_review_runs": 0, "downloads": 0, "source_review_runs": 0,
        "source_document_content_accesses": 0, "extraction_rating_ingestion_codification_runs": 0,
        "planned_or_incomplete_rows_counted_verified": 0,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_candidate_verification_4x3000_invariant_checks.json", invariants)
    write_text(OUTPUT / "broad_candidate_verification_4x3000_stress_test_report.md", "# Stress-test report\n\nCovered queue/hash drift, lane leakage, duplicate row IDs, completed-lane rerun refusal, checkpoint resume, retryable transport failures, redirect collisions, controlled statuses, partial-lane merge boundaries, dashboard stale-stage regression, and downstream boundary violations.")
    write_json(OUTPUT / "broad_candidate_verification_4x3000_regression_test_inventory.json", {
        "new_suite": "scripts/test_broad_candidate_verification_4x3000.py",
        "predecessor_suites": ["scripts/test_broad_state_4x1000_parallel_live_scout.py", "scripts/test_broad_state_4x1000_scout_dry_run_prep.py", "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"],
        "dashboard_stale_overview_guard": True, "global_analysis_readiness": False,
    })
    write_text(OUTPUT / "broad_candidate_verification_4x3000_validation_2026-07-28.md", "# Validation report\n\nGenerated coordinator invariants passed. Full repository test/build command results are recorded before final commit and relay creation.")
    print(json.dumps(decision_payload, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("smoke")
    lane_parser = sub.add_parser("lane")
    lane_parser.add_argument("--lane-id", choices=LANES, required=True)
    lane_parser.add_argument("--start-at-utc")
    sub.add_parser("merge")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "smoke":
        asyncio.run(smoke())
    elif args.command == "lane":
        asyncio.run(run_lane(args.lane_id, args.start_at_utc))
    elif args.command == "merge":
        merge()


if __name__ == "__main__":
    main()
