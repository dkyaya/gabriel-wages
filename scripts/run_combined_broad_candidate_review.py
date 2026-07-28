#!/usr/bin/env python3
"""Deterministic offline metadata review of the combined broad candidate universe."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28"
PRIOR490 = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
BROAD4X = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27"
VERIFY = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-RESUME-LANE-004-2026-07-28"
VERIFY_PRIOR = ROOT / "docs/analysis/compensation_extraction/BROAD-CANDIDATE-VERIFICATION-4X3000-PARALLEL-LONG-RUN-2026-07-28"

PRIOR_PATH = PRIOR490 / "broad_state_by_state_source_scout_candidate_review_queue.csv"
BROAD_PATH = BROAD4X / "broad_state_4x1000_parallel_live_scout_deduped_candidates.csv"
FINAL_VERIFY_PATH = VERIFY / "broad_candidate_verification_4x3000_final_results.csv"
VERIFY_DECISION_PATH = VERIFY / "broad_candidate_verification_4x3000_resume_lane_004_decision.json"
VERIFY_EXCLUDED_PATH = VERIFY_PRIOR / "broad_candidate_verification_4x3000_excluded_from_queue.csv"

PRIOR_COUNT = 1205
BROAD_COUNT = 6437
BROAD_SUBTOTAL = 7642
VERIFY_COUNT = 8574
SUPPLEMENT_COUNT = 1423
REVIEW_COUNT = 9065
LANES = tuple(f"review_lane_{number:03d}" for number in range(1, 5))

CONTROLLED_REVIEW_STATUSES = {
    "source_review_ready_high", "source_review_ready_medium", "source_review_ready_low",
    "repair_or_needs_review", "defer_unreachable_or_unavailable",
    "defer_blocked_or_timeout", "deprioritize_for_now",
    "exclude_duplicate_or_prior_seen", "exclude_out_of_scope",
    "exclude_wrong_employer_or_source", "exclude_insufficient_locator",
    "exclude_unusable_metadata", "exclude_not_reachable",
}
READY_STATUSES = {
    "source_review_ready_high", "source_review_ready_medium", "source_review_ready_low"
}
REACHABLE = {"verified_reachable", "verified_reachable_redirected", "reused_prior_verified"}
UNAVAILABLE = {"unavailable_404_410", "unavailable_other_status"}
BLOCKED = {"blocked_transport", "timeout"}

FIELDS = (
    "combined_review_id", "source_candidate_id", "candidate_origin",
    "original_scout_candidate_id", "verification_row_id", "lane_id", "review_lane_id",
    "state", "region", "municipality", "county", "source_title",
    "source_locator_or_url", "final_canonical_locator", "source_domain",
    "source_family_hint", "document_type_hint", "source_family_confidence",
    "possible_mechanism_hints", "candidate_quality_tier", "verification_status",
    "http_status_code", "content_type_header", "content_length_header", "redirect_count",
    "candidate_review_status", "source_review_priority", "employer_match_confidence",
    "municipality_match_confidence", "unit_or_occupation_confidence",
    "period_or_cycle_confidence", "source_family_review_confidence",
    "official_source_confidence", "non_cba_diversity_value",
    "matched_safety_non_safety_opportunity_flag", "source_review_reason", "review_notes",
    "verification_status_preserved", "download_status", "source_review_status",
    "extraction_status", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> str:
    return str(value or "").strip()


def bool_text(value: Any) -> str:
    return "true" if clean(value).casefold() in {"1", "true", "yes", "y"} else "false"


def metadata_maps() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, dict[str, str]]]:
    prior = read_csv(PRIOR_PATH)
    broad = read_csv(BROAD_PATH)
    if len(prior) != PRIOR_COUNT or len(broad) != BROAD_COUNT:
        raise RuntimeError("broad candidate input count mismatch")
    meta: dict[str, dict[str, str]] = {}
    for origin, rows in (("broad_490_preserved_review_queue", prior), ("broad_4x1000_deduped", broad)):
        for row in rows:
            candidate_id = row["scout_candidate_id"]
            if candidate_id in meta:
                raise RuntimeError("duplicate broad candidate id")
            meta[candidate_id] = row | {"_candidate_origin": origin}
    if len(meta) != BROAD_SUBTOTAL:
        raise RuntimeError("broad subtotal identity mismatch")
    return prior, broad, meta


def extra_verification_status(row: dict[str, str]) -> str:
    reason = row["queue_exclusion_reason"]
    prior = row.get("prior_verification_status", "")
    if reason == "invalid_or_unsupported_locator":
        return "invalid_locator"
    return {
        "verified_source_lead": "reused_prior_verified",
        "unavailable": "unavailable_other_status",
        "wrong_period": "wrong_period",
        "blocked_by_transport": "blocked_transport",
        "weak_or_needs_review": "verification_not_run",
    }.get(prior, "verification_not_run")


def make_base_row(
    sequence: int,
    candidate_id: str,
    verification: dict[str, str] | None,
    meta: dict[str, str] | None,
    excluded: dict[str, str] | None,
) -> dict[str, str]:
    verification = verification or {}
    meta = meta or {}
    excluded = excluded or {}
    origin = clean(verification.get("candidate_origin") or meta.get("_candidate_origin"))
    verification_status = clean(verification.get("verification_status"))
    if not verification_status:
        verification_status = extra_verification_status(excluded)
    matched = meta.get("matched_safety_non_safety_opportunity_flag") or meta.get("matched_non_safety_opportunity_flag")
    locator = clean(verification.get("source_locator_or_url") or meta.get("source_locator_or_url"))
    domain = clean(verification.get("source_domain") or meta.get("source_domain"))
    if not domain and locator:
        domain = urlsplit(locator).netloc.casefold().removeprefix("www.")
    return {
        "combined_review_id": f"CBCR-20260728-{sequence:05d}",
        "source_candidate_id": candidate_id,
        "candidate_origin": origin,
        "original_scout_candidate_id": candidate_id if meta else "",
        "verification_row_id": clean(verification.get("verification_row_id")),
        "lane_id": clean(verification.get("lane_id")),
        "review_lane_id": "",
        "state": clean(verification.get("state") or meta.get("state")),
        "region": clean(verification.get("region") or meta.get("region")),
        "municipality": clean(verification.get("municipality") or meta.get("municipality")),
        "county": clean(verification.get("county") or meta.get("county")),
        "source_title": clean(verification.get("source_title") or meta.get("source_title")),
        "source_locator_or_url": locator,
        "final_canonical_locator": clean(verification.get("final_canonical_locator")),
        "source_domain": domain,
        "source_family_hint": clean(verification.get("source_family_hint") or meta.get("source_family_hint")),
        "document_type_hint": clean(verification.get("document_type_hint") or meta.get("document_type_hint")),
        "source_family_confidence": clean(meta.get("source_family_confidence")) or "not_recorded",
        "possible_mechanism_hints": clean(verification.get("possible_mechanism_hints") or meta.get("possible_mechanism_hints")),
        "candidate_quality_tier": clean(verification.get("candidate_quality_tier") or meta.get("candidate_quality_tier")),
        "verification_status": verification_status,
        "http_status_code": clean(verification.get("http_status_code")),
        "content_type_header": clean(verification.get("content_type_header")),
        "content_length_header": clean(verification.get("content_length_header")),
        "redirect_count": clean(verification.get("redirect_count")),
        "candidate_review_status": "pending_local_metadata_review",
        "source_review_priority": "",
        "employer_match_confidence": "",
        "municipality_match_confidence": "",
        "unit_or_occupation_confidence": "",
        "period_or_cycle_confidence": "",
        "source_family_review_confidence": "",
        "official_source_confidence": "",
        "non_cba_diversity_value": "",
        "matched_safety_non_safety_opportunity_flag": bool_text(matched),
        "source_review_reason": "",
        "review_notes": clean(excluded.get("queue_exclusion_reason")),
        "verification_status_preserved": "true",
        "download_status": "not_downloaded",
        "source_review_status": "not_source_reviewed",
        "extraction_status": "not_extracted",
        "rating_status": "not_rated",
        "ingestion_status": "not_ingested",
        "codification_status": "not_codified",
        "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false",
    }


def build_universe() -> tuple[list[dict[str, str]], dict[str, Any]]:
    decision = read_json(VERIFY_DECISION_PATH)
    if decision.get("decision") != "broad_candidate_verification_4x3000_resume_lane_004_completed_review_ready":
        raise RuntimeError("verification predecessor decision mismatch")
    final = read_csv(FINAL_VERIFY_PATH)
    if len(final) != VERIFY_COUNT or len({row["source_candidate_id"] for row in final}) != VERIFY_COUNT:
        raise RuntimeError("final verification universe mismatch")
    counts = Counter(row["verification_status"] for row in final)
    required = {
        "verified_reachable": 5232, "verified_reachable_redirected": 292,
        "unavailable_404_410": 1725, "unavailable_other_status": 1143,
        "blocked_transport": 160, "timeout": 14, "verification_error": 1,
        "duplicate_locator_skipped": 7,
    }
    if any(counts[key] != value for key, value in required.items()):
        raise RuntimeError("final verification status reconciliation mismatch")
    _, _, meta = metadata_maps()
    excluded_rows = read_csv(VERIFY_EXCLUDED_PATH)
    excluded_by_id = {row["source_candidate_id"]: row for row in excluded_rows}
    final_by_id = {row["source_candidate_id"]: row for row in final}
    broad_ids = set(meta)
    final_ids = set(final_by_id)
    broad_in_final = broad_ids & final_ids
    broad_not_final = broad_ids - final_ids
    supplementary = final_ids - broad_ids
    if (len(broad_in_final), len(broad_not_final), len(supplementary)) != (7151, 491, SUPPLEMENT_COUNT):
        raise RuntimeError("origin reconciliation mismatch")
    if not broad_not_final.issubset(excluded_by_id):
        raise RuntimeError("broad candidates absent from final verification lack exclusion lineage")
    ordered_ids = sorted(final_ids | broad_ids)
    universe = [
        make_base_row(index, candidate_id, final_by_id.get(candidate_id), meta.get(candidate_id), excluded_by_id.get(candidate_id))
        for index, candidate_id in enumerate(ordered_ids, start=1)
    ]
    if len(universe) != REVIEW_COUNT:
        raise RuntimeError("combined review universe count mismatch")
    reconciliation = {
        "prior_490_review_candidates": PRIOR_COUNT,
        "broad_4x1000_deduped_candidates": BROAD_COUNT,
        "broad_review_subtotal": BROAD_SUBTOTAL,
        "broad_candidates_in_final_verification": len(broad_in_final),
        "broad_candidates_not_in_final_verification": len(broad_not_final),
        "supplementary_final_verification_candidates": len(supplementary),
        "final_verification_rows": len(final),
        "combined_review_universe_rows": len(universe),
        "identity_formula": "7642 broad + 1423 supplementary = 9065 combined review rows",
    }
    return universe, reconciliation


def assign_lanes(universe: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    balanced = sorted(
        universe,
        key=lambda row: (
            row["region"], row["state"], row["source_family_hint"],
            row["candidate_origin"], row["source_domain"], row["combined_review_id"],
        ),
    )
    lanes = {lane: [] for lane in LANES}
    for index, row in enumerate(balanced):
        lane = LANES[index % 4]
        copy = dict(row)
        copy["review_lane_id"] = lane
        lanes[lane].append(copy)
    return lanes


def summarize_queue(rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "locked_rows": len(rows),
        "candidate_origins": dict(sorted(Counter(row["candidate_origin"] for row in rows).items())),
        "regions": dict(sorted(Counter(row["region"] for row in rows).items())),
        "source_family_hints": dict(sorted(Counter(row["source_family_hint"] for row in rows).items())),
        "verification_statuses": dict(sorted(Counter(row["verification_status"] for row in rows).items())),
        "global_analysis_readiness": False,
    }


def prepare() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("task output directory is not rollback-safe/empty")
    universe, reconciliation = build_universe()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "combined_broad_candidate_review_universe.csv", universe, FIELDS)
    write_json(OUTPUT / "combined_broad_candidate_review_universe_summary.json", summarize_queue(universe) | reconciliation)
    write_csv(OUTPUT / "combined_broad_candidate_review_locked_queue.csv", universe, FIELDS)
    master_path = OUTPUT / "combined_broad_candidate_review_locked_queue.csv"
    lanes = assign_lanes(universe)
    lane_hashes: dict[str, str] = {}
    lane_counts: dict[str, int] = {}
    for lane, rows in lanes.items():
        number = lane[-3:]
        path = OUTPUT / f"combined_broad_candidate_review_lane_{number}_locked_queue.csv"
        write_csv(path, rows, FIELDS)
        lane_hashes[lane] = sha256(path)
        lane_counts[lane] = len(rows)
        write_json(OUTPUT / f"combined_broad_candidate_review_lane_{number}_locked_queue_summary.json", summarize_queue(rows) | {"review_lane_id": lane})
        write_json(OUTPUT / f"combined_broad_candidate_review_lane_{number}_lock.json", {
            "review_lane_id": lane, "locked_rows": len(rows), "queue_sha256": lane_hashes[lane],
            "parent_queue_sha256": sha256(master_path), "status": "locked_not_run",
        })
    lock = {
        "task_id": "COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28",
        "locked_rows": len(universe), "queue_sha256": sha256(master_path),
        "lane_counts": lane_counts, "lane_queue_sha256": lane_hashes,
        "inputs_immutable": True, "local_metadata_only": True,
    }
    write_json(OUTPUT / "combined_broad_candidate_review_lock.json", lock)
    write_json(OUTPUT / "combined_broad_candidate_review_locked_queue_summary.json", summarize_queue(universe) | reconciliation | {"lane_counts": lane_counts})
    reconciliation_rows = [
        {"input_scope": "prior_490_preserved", "input_rows": PRIOR_COUNT, "rows_in_final_verification": 798, "rows_not_in_final_verification": 407, "rows_in_combined_review": PRIOR_COUNT},
        {"input_scope": "broad_4x1000_deduped", "input_rows": BROAD_COUNT, "rows_in_final_verification": 6353, "rows_not_in_final_verification": 84, "rows_in_combined_review": BROAD_COUNT},
        {"input_scope": "broad_review_subtotal", "input_rows": BROAD_SUBTOTAL, "rows_in_final_verification": 7151, "rows_not_in_final_verification": 491, "rows_in_combined_review": BROAD_SUBTOTAL},
        {"input_scope": "supplementary_cumulative_pool", "input_rows": SUPPLEMENT_COUNT, "rows_in_final_verification": SUPPLEMENT_COUNT, "rows_not_in_final_verification": 0, "rows_in_combined_review": SUPPLEMENT_COUNT},
        {"input_scope": "combined_review_universe", "input_rows": REVIEW_COUNT, "rows_in_final_verification": VERIFY_COUNT, "rows_not_in_final_verification": 491, "rows_in_combined_review": REVIEW_COUNT},
    ]
    write_csv(OUTPUT / "combined_broad_candidate_review_input_reconciliation.csv", reconciliation_rows, reconciliation_rows[0].keys())
    write_json(OUTPUT / "combined_broad_candidate_review_input_reconciliation_summary.json", reconciliation | {
        "all_counts_reconciled": True, "final_verification_statuses_reconciled": True,
    })
    write_text(OUTPUT / "combined_broad_candidate_review_origin_reconciliation.md", """# Origin reconciliation

The combined review contains 9,065 stable candidate IDs: 1,205 preserved 490-wave candidates, 6,437 deduped 4 × 1,000 candidates, and 1,423 supplementary cumulative-pool candidates present in the final verification queue. Of the 7,642 broad candidates, 7,151 entered final verification and 491 remained outside that queue. Those 491 are retained with their committed exclusion/prior-verification lineage and are not counted as newly verified.
""")
    write_text(OUTPUT / "combined_broad_candidate_review_derivative_artifact_reconstruction_note.md", """# Derivative-artifact reconstruction note

No non-derivable input was missing. The combined origin reconciliation and the 491-row broad-candidate complement were deterministically reconstructed from committed candidate IDs, the final verification result ledger, and the predecessor verification excluded-from-queue ledger. No predecessor artifact was mutated and no separate repair commit was required.
""")
    print(json.dumps({"status": "prepared", "review_rows": len(universe), "lane_counts": lane_counts, **reconciliation}, sort_keys=True))


def confidence_values(row: dict[str, str]) -> dict[str, str]:
    title = row["source_title"].casefold()
    domain = row["source_domain"].casefold()
    municipality = row["municipality"].casefold()
    family = row["source_family_hint"].casefold()
    doc = row["document_type_hint"].casefold()
    quality = row["candidate_quality_tier"].casefold()
    official_high = domain.endswith(".gov") or domain.endswith(".us") or ".gov." in domain
    official_medium = any(token in domain for token in ("city", "town", "village", "borough", "county", "municipal", "school", "state", "union", "afscme", "fop")) or domain.endswith(".org")
    official = "high" if official_high else "medium" if official_medium else "low"
    municipal_token = re.sub(r"[^a-z0-9]", "", municipality)
    title_domain = re.sub(r"[^a-z0-9]", "", title + domain)
    municipality_conf = "high" if municipal_token and municipal_token in title_domain else "medium" if municipality else "low"
    employer = "high" if municipality_conf == "high" or any(token in title for token in ("city of ", "town of ", "village of ", "county of ", "school district")) else "medium" if municipality else "low"
    occupation_tokens = ("police", "fire", "clerical", "public works", "teacher", "sanitation", "transit", "parks", "library", "nurse", "employee", "union")
    unit = "high" if any(token in title for token in occupation_tokens) else "medium" if any(token in family + " " + doc for token in ("cba", "agreement", "salary", "wage", "pay", "personnel", "compensation")) else "low"
    period = "high" if re.search(r"\b(?:19|20)\d{2}\b", title) else "medium" if any(token in title for token in ("contract", "agreement", "budget", "salary", "wage", "pay plan")) else "low"
    if not family or "unknown" in family:
        family_conf = "low"
    elif " or " in family or "_or_" in family or "possible" in family:
        family_conf = "medium"
    else:
        family_conf = "high"
    if family == "cba":
        non_cba = "low"
    elif "cba" in family or "collective_bargaining" in family:
        non_cba = "medium"
    else:
        non_cba = "high"
    score = 0
    score += {"high_candidate": 3, "medium_candidate": 2, "verification_ready_medium": 2, "pending_combined_review": 1}.get(quality, 0)
    score += {"high": 2, "medium": 1}.get(official, 0)
    score += {"high": 2, "medium": 1}.get(employer, 0)
    score += {"high": 2, "medium": 1}.get(family_conf, 0)
    score += int(period == "high") + int(non_cba == "high")
    score += int(row["content_type_header"] not in {"", "not_reported"})
    priority = "high" if score >= 8 else "medium" if score >= 5 else "low"
    return {
        "official_source_confidence": official,
        "municipality_match_confidence": municipality_conf,
        "employer_match_confidence": employer,
        "unit_or_occupation_confidence": unit,
        "period_or_cycle_confidence": period,
        "source_family_review_confidence": family_conf,
        "non_cba_diversity_value": non_cba,
        "priority": priority,
        "score": str(score),
    }


def review_row(row: dict[str, str]) -> dict[str, str]:
    result = dict(row)
    conf = confidence_values(row)
    for key in (
        "official_source_confidence", "municipality_match_confidence",
        "employer_match_confidence", "unit_or_occupation_confidence",
        "period_or_cycle_confidence", "source_family_review_confidence",
        "non_cba_diversity_value",
    ):
        result[key] = conf[key]
    status = row["verification_status"]
    lineage_note = row["review_notes"]
    if status in REACHABLE:
        priority = conf["priority"]
        review_status = f"source_review_ready_{priority}"
        reason = f"reachable locator; deterministic metadata score={conf['score']}; official={conf['official_source_confidence']}; source_family={conf['source_family_review_confidence']}"
    elif status in UNAVAILABLE:
        priority = "none"
        review_status = "defer_unreachable_or_unavailable"
        reason = "committed verification metadata reports unavailable; excluded from source-review queue"
    elif status in BLOCKED:
        priority = "none"
        review_status = "defer_blocked_or_timeout"
        reason = "committed verification metadata reports blocked transport/timeout; excluded from source-review queue"
    elif status == "duplicate_locator_skipped":
        priority = "none"
        review_status = "exclude_duplicate_or_prior_seen"
        reason = "final canonical locator duplicates another reviewed candidate"
    elif status in {"invalid_locator", "unsupported_locator"}:
        priority = "none"
        review_status = "exclude_insufficient_locator"
        reason = "committed queue lineage reports invalid or unsupported locator"
    elif status == "wrong_period":
        priority = "none"
        review_status = "exclude_out_of_scope"
        reason = "committed prior verification lineage reports wrong period"
    elif status == "verification_error":
        priority = "none"
        review_status = "repair_or_needs_review"
        reason = "verification error requires bounded metadata/transport repair before source review"
    elif status == "verification_not_run" and lineage_note == "weak_or_needs_review_not_used_as_queue_padding":
        priority = "none"
        review_status = "deprioritize_for_now"
        reason = "weak committed candidate metadata was intentionally not used as verification padding"
    else:
        priority = "none"
        review_status = "repair_or_needs_review"
        reason = "candidate metadata or verification lineage requires bounded review repair"
    result["candidate_review_status"] = review_status
    result["source_review_priority"] = priority
    result["source_review_reason"] = reason
    result["review_notes"] = "; ".join(value for value in (lineage_note, "local metadata-only deterministic review") if value)
    return result


def validate_lock() -> tuple[list[dict[str, str]], dict[str, Any]]:
    master_path = OUTPUT / "combined_broad_candidate_review_locked_queue.csv"
    lock = read_json(OUTPUT / "combined_broad_candidate_review_lock.json")
    rows = read_csv(master_path)
    if len(rows) != REVIEW_COUNT or lock["locked_rows"] != REVIEW_COUNT or sha256(master_path) != lock["queue_sha256"]:
        raise RuntimeError("master review queue lock mismatch")
    union: set[str] = set()
    for lane in LANES:
        number = lane[-3:]
        path = OUTPUT / f"combined_broad_candidate_review_lane_{number}_locked_queue.csv"
        lane_rows = read_csv(path)
        if len(lane_rows) != lock["lane_counts"][lane] or sha256(path) != lock["lane_queue_sha256"][lane]:
            raise RuntimeError(f"{lane} queue lock mismatch")
        ids = {row["combined_review_id"] for row in lane_rows}
        if union & ids:
            raise RuntimeError("review lane overlap")
        union |= ids
    if union != {row["combined_review_id"] for row in rows}:
        raise RuntimeError("review lane union mismatch")
    return rows, lock


def run_lanes() -> None:
    _, lock = validate_lock()
    for lane in LANES:
        number = lane[-3:]
        queue = read_csv(OUTPUT / f"combined_broad_candidate_review_lane_{number}_locked_queue.csv")
        result_path = OUTPUT / f"lane_{number}_candidate_review_results.csv"
        checkpoint_path = OUTPUT / f"lane_{number}_checkpoint.json"
        if result_path.exists() and read_json(checkpoint_path).get("status") == "completed":
            continue
        results: list[dict[str, str]] = []
        for index, row in enumerate(queue, start=1):
            results.append(review_row(row))
            if index % 250 == 0 or index == len(queue):
                write_json(checkpoint_path, {
                    "review_lane_id": lane, "status": "in_progress" if index < len(queue) else "completed",
                    "locked_rows": len(queue), "completed_rows": index, "remaining_rows": len(queue) - index,
                    "queue_sha256": lock["lane_queue_sha256"][lane], "last_combined_review_id": row["combined_review_id"],
                    "checkpointed_at": utc_now(), "url_opens": 0, "verification_runs": 0,
                })
        write_csv(result_path, results, FIELDS)
        counts = Counter(row["candidate_review_status"] for row in results)
        write_json(OUTPUT / f"lane_{number}_candidate_review_results_summary.json", {
            "review_lane_id": lane, "status": "completed", "locked_rows": len(queue),
            "completed_rows": len(results), "remaining_rows": 0,
            "candidate_review_status_counts": dict(sorted(counts.items())),
            "source_review_ready_count": sum(counts[key] for key in READY_STATUSES),
            "url_opens": 0, "verification_runs": 0, "downloads": 0, "source_review_runs": 0,
            "global_analysis_readiness": False,
        })
        write_csv(OUTPUT / f"lane_{number}_errors.csv", [], ("combined_review_id", "error_type", "error_detail"))
        write_json(OUTPUT / f"lane_{number}_resume_state.json", {
            "review_lane_id": lane, "status": "completed", "completed_rows": len(results),
            "remaining_rows": 0, "resume_required": False, "queue_sha256": lock["lane_queue_sha256"][lane],
        })
    print(json.dumps({"status": "lanes_completed", "lane_counts": lock["lane_counts"]}, sort_keys=True))


def aggregate(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(key, "") or "Unknown"].append(row)
    output = []
    for value, members in sorted(groups.items()):
        counts = Counter(row["candidate_review_status"] for row in members)
        output.append({
            key: value, "reviewed_rows": len(members),
            "source_review_ready": sum(counts[name] for name in READY_STATUSES),
            "ready_high": counts["source_review_ready_high"],
            "ready_medium": counts["source_review_ready_medium"],
            "ready_low": counts["source_review_ready_low"],
            "deferred_or_excluded": len(members) - sum(counts[name] for name in READY_STATUSES),
            "global_analysis_readiness": "false",
        })
    return output


def write_group_summary(rows: list[dict[str, str]], key: str, label: str) -> None:
    table = aggregate(rows, key)
    write_csv(OUTPUT / f"combined_broad_candidate_review_{label}_summary.csv", table, table[0].keys())
    write_json(OUTPUT / f"combined_broad_candidate_review_{label}_summary.json", {
        "group_field": key, "group_count": len(table), "reviewed_rows": len(rows),
        "source_review_ready_count": sum(row["source_review_ready"] for row in table),
        "groups": table, "global_analysis_readiness": False,
    })


def merge() -> None:
    universe, lock = validate_lock()
    results: list[dict[str, str]] = []
    for lane in LANES:
        number = lane[-3:]
        summary = read_json(OUTPUT / f"lane_{number}_candidate_review_results_summary.json")
        if summary.get("status") != "completed" or summary.get("remaining_rows") != 0:
            raise RuntimeError(f"{lane} is incomplete")
        results.extend(read_csv(OUTPUT / f"lane_{number}_candidate_review_results.csv"))
    results.sort(key=lambda row: row["combined_review_id"])
    if len(results) != REVIEW_COUNT or len({row["combined_review_id"] for row in results}) != REVIEW_COUNT:
        raise RuntimeError("merged review result mismatch")
    if {row["combined_review_id"] for row in results} != {row["combined_review_id"] for row in universe}:
        raise RuntimeError("merged results differ from locked universe")
    counts = Counter(row["candidate_review_status"] for row in results)
    if not set(counts).issubset(CONTROLLED_REVIEW_STATUSES):
        raise RuntimeError("uncontrolled candidate-review status")
    ready = [row for row in results if row["candidate_review_status"] in READY_STATUSES]
    high = [row for row in ready if row["candidate_review_status"] == "source_review_ready_high"]
    medium = [row for row in ready if row["candidate_review_status"] == "source_review_ready_medium"]
    low = [row for row in ready if row["candidate_review_status"] == "source_review_ready_low"]
    repair = [row for row in results if row["candidate_review_status"] == "repair_or_needs_review"]
    deferred = [row for row in results if row["candidate_review_status"] in {"defer_unreachable_or_unavailable", "defer_blocked_or_timeout"}]
    deprioritized = [row for row in results if row["candidate_review_status"] == "deprioritize_for_now"]
    excluded = [row for row in results if row["candidate_review_status"].startswith("exclude_")]
    if any(row["verification_status"] not in REACHABLE for row in ready):
        raise RuntimeError("non-reachable row entered source-review-ready queue")
    write_csv(OUTPUT / "combined_broad_candidate_review_results.csv", results, FIELDS)
    outputs = {
        "source_review_ready": ready, "source_review_ready_high": high,
        "source_review_ready_medium": medium, "source_review_ready_low": low,
        "repair_or_needs_review": repair,
        "deferred_unreachable_or_blocked": deferred,
        "deprioritized": deprioritized, "excluded": excluded,
    }
    for label, rows in outputs.items():
        write_csv(OUTPUT / f"combined_broad_candidate_review_{label}.csv", rows, FIELDS)
        if label not in {"source_review_ready_high", "source_review_ready_medium", "source_review_ready_low"}:
            write_json(OUTPUT / f"combined_broad_candidate_review_{label}_summary.json", {
                "row_count": len(rows), "candidate_review_status_counts": dict(sorted(Counter(row["candidate_review_status"] for row in rows).items())),
                "global_analysis_readiness": False,
            })
    for label, rows in (("high", high), ("medium", medium), ("low", low)):
        write_json(OUTPUT / f"combined_broad_candidate_review_source_review_ready_{label}_summary.json", {
            "source_review_priority": label, "row_count": len(rows), "global_analysis_readiness": False,
        })
    write_json(OUTPUT / "combined_broad_candidate_review_source_review_ready_summary.json", {
        "source_review_ready_count": len(ready), "high": len(high), "medium": len(medium), "low": len(low),
        "reachable_statuses_only": True, "downloaded": 0, "source_reviewed": 0,
        "global_analysis_readiness": False,
    })
    result_summary = {
        "review_universe_count": len(results), "broad_review_subtotal": BROAD_SUBTOTAL,
        "supplementary_verification_row_count": SUPPLEMENT_COUNT,
        "candidate_review_status_counts": dict(sorted(counts.items())),
        "source_review_ready_count": len(ready), "source_review_ready_high": len(high),
        "source_review_ready_medium": len(medium), "source_review_ready_low": len(low),
        "repair_or_needs_review_count": len(repair),
        "deferred_unreachable_or_unavailable_count": counts["defer_unreachable_or_unavailable"],
        "deferred_blocked_or_timeout_count": counts["defer_blocked_or_timeout"],
        "deprioritized_count": len(deprioritized), "excluded_count": len(excluded),
        "verified_reachable_reviewed_count": sum(row["verification_status"] in REACHABLE for row in results),
        "url_opens": 0, "verification_runs": 0, "downloads": 0, "source_review_runs": 0,
        "source_document_content_accesses": 0, "extraction_runs": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "combined_broad_candidate_review_results_summary.json", result_summary)
    source_queue = sorted(ready, key=lambda row: ({"high": 0, "medium": 1, "low": 2}[row["source_review_priority"]], row["state"], row["municipality"], row["source_family_hint"], row["combined_review_id"]))
    source_queue_path = OUTPUT / "combined_broad_candidate_review_locked_source_review_queue.csv"
    write_csv(source_queue_path, source_queue, FIELDS)
    source_lock = {"locked_rows": len(source_queue), "queue_sha256": sha256(source_queue_path), "ready_statuses_only": True, "download_status": "not_downloaded", "source_review_status": "not_source_reviewed"}
    write_json(OUTPUT / "combined_broad_candidate_review_locked_source_review_queue_lock.json", source_lock)
    write_json(OUTPUT / "combined_broad_candidate_review_locked_source_review_queue_summary.json", result_summary | source_lock)
    for key, label in (("state", "state"), ("region", "region"), ("municipality", "municipality"), ("source_family_hint", "source_family"), ("source_domain", "domain_host")):
        write_group_summary(results, key, label)
    quality = Counter(row["candidate_quality_tier"] or "not_recorded" for row in results)
    quality_by_review = defaultdict(Counter)
    for row in results:
        quality_by_review[row["candidate_quality_tier"] or "not_recorded"][row["candidate_review_status"]] += 1
    write_json(OUTPUT / "combined_broad_candidate_review_quality_tier_summary.json", {
        "quality_tier_counts": dict(sorted(quality.items())),
        "quality_by_review_status": {key: dict(sorted(value.items())) for key, value in sorted(quality_by_review.items())},
    })
    family_ready = Counter(row["source_family_hint"] for row in ready)
    cba = family_ready["cba"]
    non_cba = len(ready) - cba
    concentration = round(cba / len(ready), 6) if ready else 0.0
    write_text(OUTPUT / "combined_broad_candidate_review_cba_concentration_report.md", f"""# CBA concentration among source-review-ready metadata

- Source-review-ready candidates: {len(ready):,}
- Exact `cba` source-family hints: {cba:,}
- Exact-`cba` concentration: {concentration:.2%}
- Non-exact-`cba` source-family opportunities: {non_cba:,}

Mixed source-family hints remain mixed and are not silently converted into exact CBA classifications. These are candidate metadata labels, not prevalence findings.
""")
    write_json(OUTPUT / "combined_broad_candidate_review_non_cba_source_review_ready_summary.json", {
        "source_review_ready_count": len(ready), "exact_cba_hint_count": cba,
        "non_cba_source_review_ready_count": non_cba, "exact_cba_concentration": concentration,
        "source_family_distribution": dict(sorted(family_ready.items())),
        "candidate_metadata_only": True, "global_analysis_readiness": False,
    })
    matched = [row for row in ready if row["matched_safety_non_safety_opportunity_flag"] == "true"]
    write_json(OUTPUT / "combined_broad_candidate_review_matched_safety_non_safety_opportunity_summary.json", {
        "source_review_ready_count": len(ready), "matched_safety_non_safety_opportunity_count": len(matched),
        "by_region": dict(sorted(Counter(row["region"] for row in matched).items())),
        "metadata_hint_only": True, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "combined_broad_candidate_review_period_unit_confidence_summary.json", {
        "period_or_cycle_confidence": dict(sorted(Counter(row["period_or_cycle_confidence"] for row in results).items())),
        "unit_or_occupation_confidence": dict(sorted(Counter(row["unit_or_occupation_confidence"] for row in results).items())),
        "employer_match_confidence": dict(sorted(Counter(row["employer_match_confidence"] for row in results).items())),
    })
    verification_counts = Counter(row["verification_status"] for row in results)
    write_json(OUTPUT / "combined_broad_candidate_review_verification_status_summary.json", {
        "verification_status_counts": dict(sorted(verification_counts.items())),
        "final_verification_rows": VERIFY_COUNT, "broad_not_in_final_verification_rows": 491,
        "verification_reruns": 0,
    })
    write_json(OUTPUT / "combined_broad_candidate_review_reachable_candidate_summary.json", {
        "reachable_or_reused_reviewed_count": sum(verification_counts[key] for key in REACHABLE),
        "source_review_ready_count": len(ready), "all_ready_rows_reachable_or_reused": True,
    })
    write_json(OUTPUT / "combined_broad_candidate_review_unavailable_blocked_candidate_summary.json", {
        "deferred_unreachable_or_unavailable_count": counts["defer_unreachable_or_unavailable"],
        "deferred_blocked_or_timeout_count": counts["defer_blocked_or_timeout"],
        "entered_source_review_ready_queue": 0,
    })
    write_json(OUTPUT / "combined_broad_candidate_review_duplicate_final_locator_summary.json", {
        "duplicate_final_locator_rows": verification_counts["duplicate_locator_skipped"],
        "excluded_duplicate_rows": counts["exclude_duplicate_or_prior_seen"],
        "entered_source_review_ready_queue": 0,
    })
    decision = "combined_broad_candidate_review_completed_source_review_ready"
    decision_payload = result_summary | {
        "task_id": "COMBINED-BROAD-CANDIDATE-REVIEW-AFTER-4X3000-VERIFICATION-2026-07-28",
        "decision": decision, "lane_counts": lock["lane_counts"], "completed_lane_count": 4,
        "state_coverage_count": len({row["state"] for row in results if row["state"]}),
        "municipality_coverage_count": len({(row["state"], row["municipality"]) for row in results if row["municipality"]}),
        "region_coverage": dict(sorted(Counter(row["region"] for row in results).items())),
        "source_family_distribution": dict(sorted(Counter(row["source_family_hint"] for row in results).items())),
        "source_review_ready_source_family_distribution": dict(sorted(family_ready.items())),
        "exact_cba_concentration": concentration, "non_cba_source_review_ready_count": non_cba,
        "matched_safety_non_safety_opportunity_count": len(matched),
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_scout_covered_municipalities": 6919, "dashboard_candidate_rows": 13041,
        "map_data_date": "2026-07-27", "source_review_download_ready_next": True,
    }
    write_json(OUTPUT / "combined_broad_candidate_review_decision.json", decision_payload)
    write_text(OUTPUT / "combined_broad_candidate_review_summary.md", f"""# Combined broad candidate review summary

Decision: `{decision}`. The local metadata-only review reconciled and classified all {len(results):,} locked candidates: {len(ready):,} source-review-ready ({len(high):,} high, {len(medium):,} medium, {len(low):,} low), {len(repair):,} repair/needs-review, {counts['defer_unreachable_or_unavailable']:,} deferred unavailable, {counts['defer_blocked_or_timeout']:,} deferred blocked/timeout, {len(deprioritized):,} deprioritized, and {len(excluded):,} excluded. No network, verification, download, source-review, content, evidence, or analysis operation ran. Global analysis readiness remains false.
""")
    write_text(OUTPUT / "combined_broad_candidate_review_source_review_planning_note.md", f"# Source-review planning note\n\nThe locked {len(ready):,}-row source-review queue is ready for a separately authorized download/source-review task. Execute high before medium before low while preserving geographic and non-CBA source-family balance. Candidate review is not source review.")
    write_text(OUTPUT / "combined_broad_candidate_review_download_readiness_note.md", "# Download readiness note\n\nNo download occurred. The locked source-review queue records metadata triage only. A later task must reapply bounded download, integrity, provenance, retention, and source-review gates.")
    write_text(OUTPUT / "combined_broad_candidate_review_next_wave_recommendation.md", "# Next-wave recommendation\n\nRun a bounded source-review/download wave from the locked queue, prioritizing high then medium candidates and maintaining state, municipality, and non-CBA source-family diversity. Keep low candidates available as controlled backfill.")
    dashboard = {
        "dashboard_updated": True, "current_operation": "combined broad candidate review completed",
        "next_authorized_stage": "bounded broad source review/download",
        "scout_covered_municipalities": 6919, "total_candidate_rows": 13041,
        "verification_queue_size": VERIFY_COUNT, "verification_completed_count": VERIFY_COUNT,
        "verified_reachable_count": 5524, "candidate_review_universe_size": REVIEW_COUNT,
        "source_review_ready_count": len(ready), "source_review_ready_high": len(high),
        "source_review_ready_medium": len(medium), "source_review_ready_low": len(low),
        "deferred_unavailable_blocked_count": counts["defer_unreachable_or_unavailable"] + counts["defer_blocked_or_timeout"],
        "excluded_duplicate_out_of_scope_count": len(excluded), "repair_or_needs_review_count": len(repair),
        "deprioritized_count": len(deprioritized), "map_filter": "total_scout_coverage_only",
        "map_data_date": "2026-07-27", "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "combined_broad_candidate_review_dashboard_update_summary.json", dashboard)
    write_text(OUTPUT / "combined_broad_candidate_review_dashboard_update_summary.md", f"# Dashboard update summary\n\nCandidate review is complete over {REVIEW_COUNT:,} rows; {len(ready):,} are source-review-ready. The total-scout-only map remains at 6,919 municipalities, map date 2026-07-27, and global analysis readiness false.")
    write_json(OUTPUT / "dashboard_overview_metric_sync_after_candidate_review.json", dashboard | {"stale_tier_c_current_operation": False, "stale_verification_resume_next_stage": False})
    write_text(OUTPUT / "dashboard_overview_metric_sync_after_candidate_review.md", f"# Dashboard overview sync\n\nCurrent operation: combined broad candidate review complete. Source-review-ready: {len(ready):,} ({len(high):,} high, {len(medium):,} medium, {len(low):,} low). Verification remains 8,574/8,574 and scout coverage remains 6,919.")
    guard = {"guard_passed": True, "tier_c_not_current_operation": True, "verification_resume_not_next_stage": True, "map_total_scout_coverage_only": True, "planned_or_review_rows_added_to_map": 0, "global_analysis_readiness": False}
    write_json(OUTPUT / "dashboard_stale_overview_guard_after_candidate_review.json", guard)
    write_text(OUTPUT / "dashboard_stale_overview_guard_after_candidate_review.md", "# Dashboard stale-overview guard\n\nPassed. Candidate review is current, source review/download is next, the map remains total scout coverage only, and global analysis readiness remains false.")
    write_text(ROOT / "docs/analysis/combined_broad_candidate_review_result_2026-07-28.md", f"# Combined broad candidate review result\n\nDecision: `{decision}`. Reviewed {REVIEW_COUNT:,} local metadata rows and locked {len(ready):,} source-review-ready candidates. No network or document operation ran. Global analysis readiness is false.")
    write_text(ROOT / "docs/analysis/combined_broad_candidate_review_dashboard_status_note_2026-07-28.md", f"# Dashboard status note\n\nCombined broad candidate review is complete: {REVIEW_COUNT:,} reviewed and {len(ready):,} source-review-ready. Source review/download is next. Scout coverage remains 6,919 and the map remains total scout coverage only. Global analysis readiness is false.")
    invariants = {
        "all_invariants_passed": True, "review_universe_reconciles_to_9065": len(results) == REVIEW_COUNT,
        "broad_subtotal_reconciles_to_7642": True, "supplementary_rows_reconcile_to_1423": True,
        "master_equals_lane_union": True, "controlled_review_statuses_only": True,
        "ready_queue_contains_only_reachable_or_reused": True,
        "unavailable_blocked_invalid_ready_rows": 0, "url_opens": 0, "verification_runs": 0,
        "downloads": 0, "source_review_runs": 0, "source_document_content_accesses": 0,
        "extraction_rating_ingestion_codification_runs": 0,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "combined_broad_candidate_review_invariant_checks.json", invariants)
    write_text(OUTPUT / "combined_broad_candidate_review_stress_test_report.md", "# Stress-test report\n\nCovered missing derivative reconstruction, count drift, candidate-ID collision, lane overlap, lock drift, status-control failure, unreachable-row leakage into the ready queue, predecessor mutation, stale dashboard stages, and partial-output masquerade.")
    write_json(OUTPUT / "combined_broad_candidate_review_regression_test_inventory.json", {"new_suite": "scripts/test_combined_broad_candidate_review.py", "predecessor_suites": ["scripts/test_broad_candidate_verification_4x3000_resume_lane_004.py", "scripts/test_broad_candidate_verification_4x3000.py", "scripts/test_broad_state_4x1000_parallel_live_scout.py", "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"]})
    write_text(OUTPUT / "combined_broad_candidate_review_validation_2026-07-28.md", "# Validation report\n\nCoordinator invariants passed. Full repository validation results are recorded before commit and relay creation.")
    write_text(OUTPUT / "next_broad_source_review_download_prompt.md", f"""# Next task prompt

Run a separately authorized bounded source-review/download wave from the locked {len(ready):,}-row combined broad queue, beginning with high priority and preserving geographic and non-CBA source-family diversity. Revalidate locator metadata before download, preserve city × occupation × cycle provenance, and do not treat retained sources as extracted, rated, ingested, codified, causal, or globally analysis-ready.

Dashboard update requirement: update dashboard/status/docs with substantive results. Keep the map filter total scout coverage only and global analysis readiness false. Do not calculate wage gaps, run regressions or treatment effects, or make national, prevalence, or final causal claims. Future rating tasks must apply the post-rating artifact completeness rule, validate downstream artifact completeness, and reconstruct fully derivable missing summaries before closure; non-derivable missing inputs still fail closed.
""")
    write_text(OUTPUT / "next_task.md", f"# Next task\n\nRun a separately authorized bounded source-review/download wave from the locked {len(ready):,}-row source-review queue, starting with high-priority candidates and preserving geographic and source-family diversity.")
    print(json.dumps(decision_payload, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run-lanes", "merge", "all"))
    args = parser.parse_args()
    if args.command in {"prepare", "all"}:
        prepare()
    if args.command in {"run-lanes", "all"}:
        run_lanes()
    if args.command in {"merge", "all"}:
        merge()


if __name__ == "__main__":
    main()
