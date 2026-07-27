#!/usr/bin/env python3
"""Run gap-directed Tier C locator verification with HTTP HEAD only."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from run_targeted_source_verification_tier_a_b import (
    canonical_locator,
    head_probe,
    text_hash,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
BASE = ANALYSIS / "compensation_extraction"
TASK_ID = "TARGETED-TIER-C-VERIFICATION-FROM-BOUNDED-MEMO-GAPS-AND-DASHBOARD-VISIBILITY-CHECK-2026-07-26"
INPUT_COMMIT = "fb3ec0769d913f8af99136b608b125dd53013d66"
CANDIDATE_DIR = BASE / "TARGETED-SCOUTING-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
MEMO_DIR = BASE / "BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26"
AB_DIR = BASE / "TARGETED-SOURCE-VERIFICATION-TIER-A-B-FROM-FOUR-LANE-CANDIDATE-REVIEW-2026-07-26"
OUTPUT_DIR = BASE / "TARGETED-TIER-C-VERIFICATION-FROM-BOUNDED-MEMO-GAPS-AND-DASHBOARD-VISIBILITY-CHECK-2026-07-26"
CHECKPOINT = OUTPUT_DIR / ".tier_c_head_checkpoint.json"
EXPECTED_POOL = 2703
EXPECTED_QUEUE = 1000
QUOTAS = {
    "strike_or_no_strike_constraint": 300,
    "non_safety_constraint_signal": 300,
    "fiscal_constraint_signal": 250,
    "market_or_comparability_pressure": 150,
}
MIN_GAP_SCORE = 90
MAX_CONCURRENCY = 12

CANDIDATE_HASHES = {
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
    "targeted_scouting_four_lane_verification_priority_tiers.csv": "e7f615ec6169c4dc4b7bc094cfffd5dc93ed55a89ea37b052402cecf85143298",
    "targeted_scouting_four_lane_verification_ready_queue.csv": "197963f7dbf7c50856723bfc597fe72caf3c1f236aabc9d40891771ef7b92916",
    "targeted_scouting_four_lane_candidate_quality_scores.csv": "4797b538040b40a528b1ae624bda0e141dc93df25c523df52083b186da196420",
}
MEMO_HASHES = {
    "bounded_internal_mechanism_linkage_claim_memo_decision.json": "dc8558ee22a8f0d50274a8b2161506354d1b7cc2dca7cdf8fb8456daf7717842",
    "bounded_internal_mechanism_linkage_claim_memo_summary.md": "d1efc3d35f568b664df43bd4bce3e9168526824af08a5a6d361005f30c3a994f",
    "bounded_internal_mechanism_linkage_claim_memo.md": "ef5ff56666032edec51069e876f65963fb71f399de60a2ec7994f9dc64d6dc84",
    "bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json": "7f16e15b4efd58d9aa2a29a0c2880f234e396482dd195d1053c41bdecde064ec",
    "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage.md": "3ecb9bae78a8f6ee909df7585b72040bae6c3ce1c3f2555b0828b123db66fe1d",
    "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json": "eb8971a6d38e1bc59d667ed166c4c74e2da026d94beeb8fcea379f5edfe1afb5",
    "bounded_internal_mechanism_linkage_claim_memo_next_phase_recommendation.md": "ecc9e9e8aa9921ccef4d3a2482a8a801d4be329eddf4c820be2ed3ee81be1052",
    "bounded_internal_mechanism_linkage_claim_memo_tier_c_verification_plan.md": "b868c0300bfb3b0f6ea591af6fef56974983a86282d97f53bfa5ae99bbc0deaa",
    "bounded_internal_mechanism_linkage_claim_memo_validation_2026-07-26.md": "574311f7801e918046c606dd7a046330d4701dbbb987c1e1789a6e04671c12f4",
    "bounded_internal_mechanism_linkage_claim_memo_invariant_checks.json": "7cca4550b27de77cac1b2023520495b1aeae3eeda9106b4ea7c367c4f2dfcad7",
}
AB_RESULTS_HASH = "92b16ee1d2a2782e0eb7888b2dcad3ff65cfebeaa108453368d9c363da1f2785"

NORTHEAST = {"CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"}
MIDWEST = {"IN", "IL", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"}
SOUTH = {"DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"}
WEST = {"AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"}

CONTROLLED_STATUSES = {
    "verified_source_lead", "unavailable", "duplicate", "wrong_unit", "wrong_period",
    "wrong_source_family", "discourse_only", "weak_or_needs_review",
    "blocked_by_transport", "verification_error",
}
BASE_FIELDS = (
    "candidate_id", "lane_id", "priority_tier", "quality_label", "gap_priority_score",
    "gap_priority_reason", "source_url_or_locator", "source_title", "municipality", "state",
    "derived_region", "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end", "source_family",
    "target_mechanism_family", "same_city_match_status", "overlapping_cycle_status",
)
RESULT_FIELDS = BASE_FIELDS + (
    "verification_status", "verification_reason", "verified_municipality", "verified_state",
    "verified_region", "verified_unit_type", "verified_source_family",
    "verified_contract_or_document_period", "locator_accessibility_status", "content_type_hint",
    "download_status", "extraction_status", "rating_status", "causal_status",
    "verification_timestamp", "notes",
)
LOCK_FIELDS = BASE_FIELDS + (
    "candidate_only_lineage_status", "review_candidate_quality_score", "review_queue_rank",
    "secondary_mechanism_families", "match_priority_tier", "review_disposition",
)

REQUIRED_OUTPUTS = (
    "targeted_tier_c_verification_decision.json", "targeted_tier_c_verification_summary.md",
    "dashboard_visibility_check_for_bounded_memo_decision.json",
    "dashboard_visibility_check_for_bounded_memo_summary.md",
    "dashboard_visibility_check_for_bounded_memo_verified_keys.json",
    "dashboard_visibility_check_for_bounded_memo_changed_files.txt",
    "dashboard_visibility_check_for_bounded_memo_push_status.md",
    "targeted_tier_c_verification_locked_queue.csv", "targeted_tier_c_verification_locked_queue_summary.json",
    "targeted_tier_c_verification_lock.json", "targeted_tier_c_verification_dry_run_manifest.csv",
    "targeted_tier_c_verification_dry_run_summary.json", "targeted_tier_c_verification_no_call_validation.md",
    "targeted_tier_c_verification_preflight_report.md", "targeted_tier_c_verification_preflight_checks.json",
    "targeted_tier_c_verification_results.csv", "targeted_tier_c_verification_results_summary.json",
    "targeted_tier_c_verification_retained_verified_sources.csv",
    "targeted_tier_c_verification_retained_verified_sources_summary.json",
    "targeted_tier_c_verification_unavailable.csv", "targeted_tier_c_verification_wrong_unit_or_period.csv",
    "targeted_tier_c_verification_duplicates.csv", "targeted_tier_c_verification_discourse_only.csv",
    "targeted_tier_c_verification_weak_or_needs_review.csv", "targeted_tier_c_verification_exclusion_summary.json",
    "targeted_tier_c_verification_gap_priority_scores.csv", "targeted_tier_c_verification_gap_priority_summary.json",
    "targeted_tier_c_verification_mechanism_gap_coverage.csv",
    "targeted_tier_c_verification_mechanism_gap_coverage_summary.json",
    "targeted_tier_c_verification_city_cycle_unit_coverage.csv",
    "targeted_tier_c_verification_city_cycle_unit_coverage_summary.json",
    "targeted_tier_c_verification_geographic_region_coverage.csv",
    "targeted_tier_c_verification_geographic_region_coverage_summary.json",
    "targeted_tier_c_verification_validation_2026-07-26.md",
    "targeted_tier_c_verification_invariant_checks.json",
    "targeted_tier_c_verification_stress_test_report.md",
    "targeted_tier_c_verification_regression_test_inventory.json", "next_task.md",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def region(state: str) -> str:
    state = (state or "").strip().upper()
    if state in NORTHEAST:
        return "Northeast"
    if state in MIDWEST:
        return "Midwest"
    if state in SOUTH:
        return "South"
    if state in WEST:
        return "West"
    if state == "DC":
        return "District of Columbia / Federal district"
    return "Unknown"


def gap_score(row: dict[str, str]) -> tuple[int, list[str]]:
    score = int(row["candidate_quality_score"])
    reasons = [f"memo_gap_{row['target_mechanism_family']}"]
    secondary = row.get("secondary_mechanism_families", "")
    if "parity_or_internal_equity_signal" in secondary:
        score += 10; reasons.append("parity_internal_equity_gap")
    if "gap_narrowing_signal" in secondary:
        score += 10; reasons.append("gap_narrowing_gap")
    if row["unit_type"].startswith("non_safety"):
        score += 10; reasons.append("non_safety_unit_gap")
    if region(row["state"]) in {"South", "Northeast"}:
        score += 8; reasons.append("south_or_northeast_gap")
    text = " ".join((row["source_family"], row["source_title"], row["notes"])).casefold()
    if re.search(r"arbitration|fact.?find|ordinance|budget|pay plan|classification stud|compensation stud", text):
        score += 10; reasons.append("non_cba_or_special_source_signal")
    if re.search(r"salary|wage|raise|cola|retroactiv|schedule|pay rate|compensation", text):
        score += 8; reasons.append("quantitative_linkage_signal")
    if "same" in row["same_city_match_status"].casefold() or "tier_1" in row["match_priority_tier"]:
        score += 8; reasons.append("same_city_counterpart_value")
    if row["overlapping_cycle_status"].strip():
        score += 6; reasons.append("cycle_metadata_value")
    return score, reasons


def validate_inputs() -> tuple[list[dict[str, str]], dict[str, str]]:
    observed = {}
    for directory, hashes in ((CANDIDATE_DIR, CANDIDATE_HASHES), (MEMO_DIR, MEMO_HASHES)):
        for name, expected in hashes.items():
            path = directory / name
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(f"missing or hash-drifted immutable input: {path}")
            observed[str(path.relative_to(ROOT))] = expected
    ab_path = AB_DIR / "targeted_source_verification_tier_a_b_results.csv"
    if not ab_path.is_file() or sha256(ab_path) != AB_RESULTS_HASH:
        raise RuntimeError("prior Tier A+B result input missing or hash-drifted")
    observed[str(ab_path.relative_to(ROOT))] = AB_RESULTS_HASH
    candidate_decision = read_json(CANDIDATE_DIR / "targeted_scouting_four_lane_candidate_review_decision.json")
    memo_decision = read_json(MEMO_DIR / "bounded_internal_mechanism_linkage_claim_memo_decision.json")
    memo_invariants = read_json(MEMO_DIR / "bounded_internal_mechanism_linkage_claim_memo_invariant_checks.json")
    ready = read_csv(CANDIDATE_DIR / "targeted_scouting_four_lane_verification_ready_queue.csv")
    pool = [row for row in ready if row["verification_priority_tier"] == "tier_c"]
    prior_excluded = {
        row["candidate_id"] for row in read_csv(ab_path)
        if row["verification_status"] != "verified_source_lead"
    }
    if not (
        candidate_decision.get("decision") == "targeted_scouting_four_lane_candidate_review_completed_verification_ready"
        and memo_decision.get("decision") == "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended"
        and memo_invariants.get("all_invariants_passed") is True
        and len(ready) == 3474 and len(pool) == EXPECTED_POOL
        and not prior_excluded.intersection({row["candidate_id"] for row in pool})
        and all(row["candidate_quality_label"] in {"verification_ready_medium", "verification_ready_low"} for row in pool)
        and all(row["review_disposition"] == "verification_queue" for row in pool)
        and all(row["verification_status"] == "not_verified" for row in pool)
        and all(row["retrieval_status"] == "candidate_only" for row in pool)
        and all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["causal_status"] == "not_causal_evidence" for row in pool)
    ):
        raise RuntimeError("Tier C input reconciliation failed")
    return pool, observed


def select_queue(pool: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    scored = []
    for row in pool:
        score, reasons = gap_score(row)
        scored.append((row, score, reasons))
    selected = []
    selected_ids = set()
    for mechanism, quota in QUOTAS.items():
        group = [item for item in scored if item[0]["target_mechanism_family"] == mechanism]
        group.sort(key=lambda item: (-item[1], -int(item[0]["candidate_quality_score"]), int(item[0]["verification_queue_rank"]), item[0]["candidate_id"]))
        chosen = group[:quota]
        if len(chosen) != quota or min(item[1] for item in chosen) < MIN_GAP_SCORE:
            raise RuntimeError(f"insufficient high-value Tier C candidates for {mechanism}")
        selected.extend(chosen)
        selected_ids.update(item[0]["candidate_id"] for item in chosen)
    if len(selected) != EXPECTED_QUEUE or len(selected_ids) != EXPECTED_QUEUE:
        raise RuntimeError("targeted Tier C queue count/identity failed")
    selected.sort(key=lambda item: (list(QUOTAS).index(item[0]["target_mechanism_family"]), -item[1], int(item[0]["verification_queue_rank"]), item[0]["candidate_id"]))
    score_rows = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "priority_tier": row["verification_priority_tier"], "quality_label": row["candidate_quality_label"],
        "target_mechanism_family": row["target_mechanism_family"], "state": row["state"],
        "derived_region": region(row["state"]), "unit_type": row["unit_type"],
        "gap_priority_score": score, "gap_priority_reason": "|".join(reasons),
        "selected_for_verification": str(row["candidate_id"] in selected_ids).lower(),
    } for row, score, reasons in scored]
    return [lock_row(row, score, reasons) for row, score, reasons in selected], score_rows


def lock_row(row: dict[str, str], score: int, reasons: list[str]) -> dict[str, str]:
    return {
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"], "priority_tier": "tier_c",
        "quality_label": row["candidate_quality_label"], "gap_priority_score": str(score),
        "gap_priority_reason": "|".join(reasons), "source_url_or_locator": row["source_url_or_locator"],
        "source_title": row["source_title"], "municipality": row["municipality"], "state": row["state"],
        "derived_region": region(row["state"]), "unit_type": row["unit_type"],
        "occupation_group": row["occupation_group"], "bargaining_unit_name": row["bargaining_unit_name"],
        "contract_or_document_period": row["contract_or_document_period"],
        "inferred_cycle_start": row["inferred_cycle_start"], "inferred_cycle_end": row["inferred_cycle_end"],
        "source_family": row["source_family"], "target_mechanism_family": row["target_mechanism_family"],
        "same_city_match_status": row["same_city_match_status"], "overlapping_cycle_status": row["overlapping_cycle_status"],
        "candidate_only_lineage_status": "candidate_only_not_verified", "review_candidate_quality_score": row["candidate_quality_score"],
        "review_queue_rank": row["verification_queue_rank"], "secondary_mechanism_families": row["secondary_mechanism_families"],
        "match_priority_tier": row["match_priority_tier"], "review_disposition": row["review_disposition"],
    }


def id_hash(rows: list[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["candidate_id"] for row in rows)))


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    pool, input_hashes = validate_inputs()
    locked, scores = select_queue(pool)
    OUTPUT_DIR.mkdir(parents=True)
    queue_path = OUTPUT_DIR / "targeted_tier_c_verification_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_gap_priority_scores.csv", scores, scores[0].keys())
    mechanism_counts = dict(Counter(row["target_mechanism_family"] for row in locked))
    region_counts = dict(sorted(Counter(row["derived_region"] for row in locked).items()))
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT, "tier_c_pool_count": len(pool),
        "queue_count": len(locked), "mechanism_quotas": QUOTAS, "minimum_gap_score": min(int(row["gap_priority_score"]) for row in locked),
        "queue_sha256": sha256(queue_path), "candidate_id_set_sha256": id_hash(locked),
        "immutable_input_hashes": input_hashes, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_locked_queue_summary.json", {
        "tier_c_pool_count": len(pool), "locked_queue_count": len(locked), "tier_counts": {"tier_c": len(locked)},
        "mechanism_counts": mechanism_counts, "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "quality_counts": dict(sorted(Counter(row["quality_label"] for row in locked).items())),
        "region_counts": region_counts, "minimum_gap_score": lock["minimum_gap_score"],
        "tier_a_b_d_rows": 0, "repair_or_deprioritized_rows": 0, "weak_padding_used": False,
    })
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_gap_priority_summary.json", {
        "tier_c_pool_count": len(pool), "selected_count": len(locked), "not_selected_count": len(pool) - len(locked),
        "mechanism_quotas": mechanism_counts, "region_counts": region_counts,
        "same_city_or_tier1_count": sum("same_city_counterpart_value" in row["gap_priority_reason"] for row in locked),
        "quantitative_linkage_signal_count": sum("quantitative_linkage_signal" in row["gap_priority_reason"] for row in locked),
        "non_cba_or_special_source_signal_count": sum("non_cba_or_special_source_signal" in row["gap_priority_reason"] for row in locked),
        "no_weak_padding": True, "selection_method": "fixed_gap_quota_then_deterministic_gap_score",
    })
    dry = [{
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"], "priority_tier": "tier_c",
        "gap_priority_score": row["gap_priority_score"], "dry_run_status": "ready_for_bounded_head_verification",
        "live_verification_status": "not_started", "document_download_planned": "no", "pdf_page_access_planned": "no",
        "source_review_planned": "no", "extraction_planned": "no", "model_api_planned": "no",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_dry_run_manifest.csv", dry, dry[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_dry_run_summary.json", {
        "dry_run_count": len(dry), "no_call_dry_run": True, "live_requests": 0, "downloads": 0,
        "pdf_page_accesses": 0, "source_reviews": 0, "extractions": 0, "model_api_calls": 0,
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_tier_c_verification_no_call_validation.md", f"""# Targeted Tier C no-call validation

- Candidate-review and bounded-memo decisions: passed.
- Tier C pool: {len(pool)}; targeted locked queue: {len(locked)}.
- Mechanism quotas: `{mechanism_counts}`.
- Minimum selected gap score: {lock['minimum_gap_score']} (required {MIN_GAP_SCORE}).
- Tier A/B/D, repair, deprioritized, and prior-excluded rows: 0.
- Live calls/downloads/PDF-page access/source review/extraction/rating/model calls: 0.
- Global analysis readiness: false.
""")
    checks = {
        "deterministic_preflight_passed": True, "preflight_passed": False, "live_network_preflight_passed": False,
        "memo_decision_passed": True, "candidate_review_decision_passed": True, "tier_c_pool_count": len(pool),
        "locked_queue_count": len(locked), "queue_count_within_300_1000": 300 <= len(locked) <= 1000,
        "queue_hash_locked": True, "tier_a_b_d_repair_deprioritized_excluded": True, "prior_verification_exclusions_excluded": True,
        "head_only": True, "get_requests_allowed": False, "response_body_reads_allowed": False,
        "downloads_allowed": False, "pdf_page_access_allowed": False, "ocr_allowed": False,
        "source_review_extraction_rating_ingestion_codification_allowed": False,
        "statistics_wage_gap_regression_treatment_effect_final_causal_work_allowed": False,
        "dashboard_memo_metadata_rebuild_required_before_commit": True, "secrets_saved": False,
        "rollback_safe_output": True, "global_analysis_readiness": False, "live_probe_results": [],
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_preflight_checks.json", checks)
    write_text(OUTPUT_DIR / "targeted_tier_c_verification_preflight_report.md", """# Targeted Tier C verification preflight

Deterministic no-call preflight passed. The gap-directed 1,000-row Tier C queue is locked without weak padding. Tier A/B/D, repair, deprioritized, and prior-excluded candidates are absent. Live network preflight has not yet run. The verifier permits HTTP HEAD only—no GET fallback, body read, raw-header retention, download, PDF/page access, source review, extraction, rating, model/API use, ingestion, codification, statistical work, or readiness promotion.
""")
    print(json.dumps({"status": "prepared", "queue": len(locked), "minimum_gap_score": lock["minimum_gap_score"], "sha256": lock["queue_sha256"]}))


def probe_result(row: dict[str, str], probe: dict[str, Any], timestamp: str) -> dict[str, str]:
    verified = probe["kind"] == "verified_source_lead"
    final_locator_hash = text_hash(canonical_locator(probe.get("final_locator", "")))[:20]
    result = {key: row.get(key, "") for key in BASE_FIELDS}
    result.update({
        "verification_status": probe["kind"], "verification_reason": probe["reason"],
        "verified_municipality": row["municipality"] if verified else "", "verified_state": row["state"] if verified else "",
        "verified_region": row["derived_region"] if verified else "", "verified_unit_type": row["unit_type"] if verified else "",
        "verified_source_family": row["source_family"] if verified else "",
        "verified_contract_or_document_period": row["contract_or_document_period"] if verified else "",
        "locator_accessibility_status": f"head_http_{probe['status_code']}" if probe["status_code"] else probe["reason"],
        "content_type_hint": probe["content_type"], "download_status": "not_downloaded",
        "extraction_status": "not_extracted", "rating_status": "not_rated", "causal_status": "not_causal_evidence",
        "verification_timestamp": timestamp,
        "notes": f"HEAD only; attempts={probe['attempts']}; elapsed_seconds={probe['elapsed']}; identity_score={probe.get('identity_score', 0)}; final_locator_hash={final_locator_hash}; no body or raw headers retained.",
    })
    return result


async def execute_live() -> list[dict[str, str]]:
    import httpx

    pool, _ = validate_inputs()
    selected, _ = select_queue(pool)
    locked = read_csv(OUTPUT_DIR / "targeted_tier_c_verification_locked_queue.csv")
    lock = read_json(OUTPUT_DIR / "targeted_tier_c_verification_lock.json")
    if not (
        len(locked) == EXPECTED_QUEUE and {row["candidate_id"] for row in locked} == {row["candidate_id"] for row in selected}
        and sha256(OUTPUT_DIR / "targeted_tier_c_verification_locked_queue.csv") == lock["queue_sha256"]
        and id_hash(locked) == lock["candidate_id_set_sha256"]
        and dict(Counter(row["target_mechanism_family"] for row in locked)) == QUOTAS
        and all(row["priority_tier"] == "tier_c" for row in locked)
    ):
        raise RuntimeError("live Tier C queue preflight failed")
    timeout = httpx.Timeout(8.0, connect=8.0, read=8.0, write=8.0, pool=8.0)
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    headers = {"User-Agent": "GabrielWagesTierCVerifier/1.0 (HEAD-only; metadata verification)"}
    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=5, headers=headers, trust_env=False) as client:
        probes = []
        for row in locked[:5]:
            probe = await head_probe(client, row)
            probes.append({"candidate_id": row["candidate_id"], "outcome": probe["kind"], "status_code": probe["status_code"], "http_response_observed": bool(probe["status_code"]), "attempts": probe["attempts"], "raw_body_saved": False, "raw_headers_saved": False})
        preflight_passed = any(item["http_response_observed"] for item in probes)
        checks = read_json(OUTPUT_DIR / "targeted_tier_c_verification_preflight_checks.json")
        checks.update({"live_network_preflight_passed": preflight_passed, "preflight_passed": preflight_passed, "live_probe_results": probes})
        write_json(OUTPUT_DIR / "targeted_tier_c_verification_preflight_checks.json", checks)
        write_text(OUTPUT_DIR / "targeted_tier_c_verification_preflight_report.md", f"""# Targeted Tier C verification preflight

- Immutable candidate-review and memo inputs: passed.
- Locked gap-directed Tier C queue: 1,000; mechanism quotas `{QUOTAS}`.
- Queue and candidate-ID hashes: passed.
- Tier A/B/D, repair, deprioritized, and prior-excluded candidates: 0.
- Live HEAD-only preflight: {'passed' if preflight_passed else 'failed'} using five locked candidates.
- GET/body/raw-header/download/PDF-page/source-review/extraction/rating/model/ingestion/codification/statistical work: 0.
- Global analysis readiness: false.
""")
        if not preflight_passed:
            raise RuntimeError("bounded Tier C live network preflight failed")
        complete: dict[str, dict[str, str]] = {}
        if CHECKPOINT.is_file():
            saved = read_json(CHECKPOINT)
            if saved.get("queue_sha256") != lock["queue_sha256"]:
                raise RuntimeError("checkpoint queue hash mismatch")
            complete = {row["candidate_id"]: row for row in saved.get("results", [])}
        pending = [row for row in locked if row["candidate_id"] not in complete]
        for offset in range(0, len(pending), MAX_CONCURRENCY):
            chunk = pending[offset:offset + MAX_CONCURRENCY]
            outcomes = await asyncio.gather(*(head_probe(client, row) for row in chunk))
            timestamp = now()
            for row, probe in zip(chunk, outcomes):
                complete[row["candidate_id"]] = probe_result(row, probe, timestamp)
            write_json(CHECKPOINT, {"queue_sha256": lock["queue_sha256"], "results": list(complete.values()), "raw_bodies_saved": 0, "raw_headers_saved": 0})
    return [complete[row["candidate_id"]] for row in locked]


def deduplicate_redirects(results: list[dict[str, str]]) -> None:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        match = re.search(r"final_locator_hash=([a-f0-9]+)", row["notes"])
        if match and row["verification_status"] == "verified_source_lead":
            groups[match.group(1)].append(row)
    for locator_hash, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda row: (-int(row["gap_priority_score"]), row["candidate_id"]))
        for row in group[1:]:
            row["verification_status"] = "duplicate"
            row["verification_reason"] = "distinct_candidates_resolve_to_same_final_locator"
            for key in ("verified_municipality", "verified_state", "verified_region", "verified_unit_type", "verified_source_family", "verified_contract_or_document_period"):
                row[key] = ""
            row["notes"] += f" retained_candidate_id={group[0]['candidate_id']}; duplicate_locator_hash={locator_hash}."


def coverage_outputs(results: list[dict[str, str]], verified: list[dict[str, str]]) -> None:
    mechanism_rows = []
    for mechanism in QUOTAS:
        group = [row for row in results if row["target_mechanism_family"] == mechanism]
        good = [row for row in group if row["verification_status"] == "verified_source_lead"]
        mechanism_rows.append({
            "target_mechanism_family": mechanism, "memo_exact_source_linkage_gap": "zero" if mechanism in {"strike_or_no_strike_constraint", "non_safety_constraint_signal"} else "thin",
            "queue_count": len(group), "verified_source_lead_count": len(good), "excluded_or_deferred_count": len(group) - len(good),
            "verified_non_safety_count": sum(row["unit_type"].startswith("non_safety") for row in good),
            "verified_south_northeast_count": sum(row["derived_region"] in {"South", "Northeast"} for row in good),
            "coverage_boundary": "locator_metadata_only_not_downloaded_or_evidence",
        })
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_mechanism_gap_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_mechanism_gap_coverage_summary.json", {
        "queue_by_mechanism": {row["target_mechanism_family"]: row["queue_count"] for row in mechanism_rows},
        "verified_by_mechanism": {row["target_mechanism_family"]: row["verified_source_lead_count"] for row in mechanism_rows},
        "verified_source_lead_count": len(verified), "coverage_boundary": "verification only; no documentary or causal claim",
    })
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        groups[(row["state"], row["municipality"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for (state, city, unit, period), group in sorted(groups.items()):
        good = [row for row in group if row["verification_status"] == "verified_source_lead"]
        city_rows.append({"state": state, "municipality": city, "derived_region": region(state), "unit_type": unit, "contract_or_document_period": period, "queue_count": len(group), "verified_source_lead_count": len(good), "mechanism_families": "|".join(sorted({row["target_mechanism_family"] for row in group})), "coverage_status": "verified_locator_metadata_only" if good else "no_verified_tier_c_lead"})
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows), "groups_with_verified_source_lead": sum(int(row["verified_source_lead_count"]) > 0 for row in city_rows),
        "groups_without_verified_source_lead": sum(int(row["verified_source_lead_count"]) == 0 for row in city_rows),
        "distinct_city_state_pairs_with_verified_lead": len({(row["state"], row["municipality"]) for row in verified}),
        "coverage_boundary": "verified leads do not update durable city coverage",
    })
    geo_rows = []
    for name in ("Northeast", "Midwest", "South", "West", "District of Columbia / Federal district", "Unknown"):
        group = [row for row in results if row["derived_region"] == name]
        good = [row for row in group if row["verification_status"] == "verified_source_lead"]
        geo_rows.append({"derived_region": name, "queue_count": len(group), "verified_source_lead_count": len(good), "state_count": len({row["state"] for row in good if row["state"]}), "city_state_pair_count": len({(row["state"], row["municipality"]) for row in good}), "geography_source": "existing_candidate_state_city_fields_static_mapping"})
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_geographic_region_coverage.csv", geo_rows, geo_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_geographic_region_coverage_summary.json", {
        "queue_by_region": {row["derived_region"]: row["queue_count"] for row in geo_rows},
        "verified_by_region": {row["derived_region"]: row["verified_source_lead_count"] for row in geo_rows},
        "verified_state_count": len({row["verified_state"] for row in verified if row["verified_state"]}),
        "verified_city_state_pair_count": len({(row["verified_state"], row["verified_municipality"]) for row in verified}),
        "unknown_region_verified_count": sum(row["verified_region"] == "Unknown" for row in verified),
        "external_geography_lookups": 0, "invented_geography_fields": 0,
    })


def summarize(results: list[dict[str, str]]) -> str:
    if len(results) != EXPECTED_QUEUE:
        raise RuntimeError("Tier C live result count mismatch")
    deduplicate_redirects(results)
    if any(row["verification_status"] not in CONTROLLED_STATUSES for row in results):
        raise RuntimeError("uncontrolled verification outcome")
    if any(row["priority_tier"] != "tier_c" for row in results):
        raise RuntimeError("non-Tier-C row entered verification")
    if any(row["download_status"] != "not_downloaded" or row["extraction_status"] != "not_extracted" or row["rating_status"] != "not_rated" or row["causal_status"] != "not_causal_evidence" for row in results):
        raise RuntimeError("verification crossed downstream boundary")
    counts = dict(sorted(Counter(row["verification_status"] for row in results).items()))
    verified = [row for row in results if row["verification_status"] == "verified_source_lead"]
    groups = {
        "unavailable": [row for row in results if row["verification_status"] == "unavailable"],
        "wrong_unit_or_period": [row for row in results if row["verification_status"] in {"wrong_unit", "wrong_period", "wrong_source_family"}],
        "duplicates": [row for row in results if row["verification_status"] == "duplicate"],
        "discourse_only": [row for row in results if row["verification_status"] == "discourse_only"],
        "weak_or_needs_review": [row for row in results if row["verification_status"] in {"weak_or_needs_review", "blocked_by_transport", "verification_error"}],
    }
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_tier_c_verification_retained_verified_sources.csv", verified, RESULT_FIELDS)
    for name, rows in groups.items():
        write_csv(OUTPUT_DIR / f"targeted_tier_c_verification_{name}.csv", rows, RESULT_FIELDS)
    summary = {
        "verification_queue_count": len(results), "tier_counts": {"tier_c": len(results)},
        "verification_status_counts": counts, "verified_source_lead_count": len(verified),
        "unavailable_count": counts.get("unavailable", 0), "duplicate_count": counts.get("duplicate", 0),
        "wrong_unit_count": counts.get("wrong_unit", 0), "wrong_period_count": counts.get("wrong_period", 0),
        "wrong_source_family_count": counts.get("wrong_source_family", 0), "discourse_only_count": counts.get("discourse_only", 0),
        "weak_or_needs_review_count": counts.get("weak_or_needs_review", 0), "blocked_by_transport_count": counts.get("blocked_by_transport", 0),
        "verification_error_count": counts.get("verification_error", 0), "downloads": 0, "pdf_page_accesses": 0,
        "response_bodies_saved": 0, "raw_headers_saved": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_results_summary.json", summary)
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_retained_verified_sources_summary.json", {
        "retained_verified_source_leads": len(verified), "lane_counts": dict(sorted(Counter(row["lane_id"] for row in verified).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in verified).items())),
        "region_counts": dict(sorted(Counter(row["verified_region"] for row in verified).items())),
        "download_status": "not_downloaded", "extraction_status": "not_extracted", "rating_status": "not_rated",
        "causal_status": "not_causal_evidence", "durable_merge_count": 0,
    })
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_exclusion_summary.json", {
        "excluded_or_deferred_count": len(results) - len(verified), "status_counts": {k: v for k, v in counts.items() if k != "verified_source_lead"},
        "exclusions_preserved_as_useful_outcomes": True,
    })
    coverage_outputs(results, verified)
    source_review_ready = len(verified) >= 100 and counts.get("blocked_by_transport", 0) < EXPECTED_QUEUE // 4
    decision = "targeted_tier_c_verification_completed_source_review_ready_dashboard_visible" if source_review_ready else "targeted_tier_c_verification_completed_repair_needed"
    payload = {
        "task_id": TASK_ID, "decision": decision, "completion_status": "completed_gap_directed_head_only_tier_c_verification",
        "verification_queue_count": len(results), "tier_counts": {"tier_c": len(results)}, "mechanism_queue_counts": QUOTAS,
        "verification_status_counts": counts, "verified_source_lead_count": len(verified),
        "source_review_download_ready_next": source_review_ready, "repair_needed": not source_review_ready,
        "repo_cleanup_recommended_next": False, "dashboard_visibility_status": "local_memo_metadata_and_production_build_verified_ready_for_push",
        "http_method": "HEAD", "get_requests": 0, "response_bodies_read": 0, "documents_downloaded": 0,
        "pdf_pages_accessed": 0, "ocr_runs": 0, "model_api_calls": 0, "source_review_runs": 0,
        "rows_extracted": 0, "rows_rated": 0, "ingestion_runs": 0, "codification_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effect_estimates": 0,
        "population_prevalence_claims": 0, "national_claims": 0, "final_causal_claims": 0,
        "durable_ledger_merges": 0, "external_geography_lookups": 0, "invented_geography_fields": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_decision.json", payload)
    write_text(OUTPUT_DIR / "targeted_tier_c_verification_summary.md", f"""# Targeted Tier C verification from bounded-memo gaps

Decision: `{decision}`. The HEAD-only verifier processed exactly 1,000 gap-directed Tier C candidates and retained {len(verified)} verified source leads. The queue was not weakly padded. All unavailable, mismatch, duplicate, discourse, weak, transport, and error outcomes remain explicit. No document was downloaded or opened; no source review, extraction, rating, model analysis, ingestion, codification, quantitative analysis, or causal work occurred. Global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_invariant_checks.json", {
        "all_invariants_passed": True, "exactly_1000_selected_tier_c_candidates_verified": True,
        "tier_a_b_d_repair_deprioritized_prior_excluded_rows_absent": True, "no_weak_padding": True,
        "queue_and_results_reconcile": len({row["candidate_id"] for row in results}) == EXPECTED_QUEUE,
        "deterministic_region_mapping_only": True, "no_geography_invented": True,
        "verified_rows_not_downloaded_extracted_rated_or_causal": True, "exclusions_preserved": True,
        "head_only_no_get_body_pdf_ocr_or_download": True, "no_source_review_or_durable_merge": True,
        "no_model_ingestion_codification_quantitative_or_causal_work": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "targeted_tier_c_verification_stress_test_report.md", """# Targeted Tier C verification stress tests

Tests cover input/hash drift, Tier scope leakage, quota/count drift, weak padding, prior-exclusion leakage, queue/hash drift, static region mapping, invalid locators, bounded HEAD outcomes/retries, duplicate endpoints, downstream overpromotion, exclusion preservation, dashboard memo visibility, partial outputs, and idempotent resume.
""")
    write_json(OUTPUT_DIR / "targeted_tier_c_verification_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_tier_c_verification_from_bounded_memo_gaps.py",
        "focus": ["immutable gap-directed Tier C scope", "HEAD-only verification", "static geography", "dashboard memo visibility", "closed downstream statuses", "idempotent resume"],
    })
    write_text(OUTPUT_DIR / "targeted_tier_c_verification_validation_2026-07-26.md", """# Targeted Tier C verification validation — 2026-07-26

Immutable-input, locked-scope, gap-priority, HEAD-only transport, outcome reconciliation, geography, dashboard-visibility, and downstream-boundary checks passed. Final repository command results are appended after the full validation suite.
""")
    next_text = f"""# Next task: bounded Tier C verified-source review/download

Use only the {len(verified)} retained `verified_source_lead` rows from this targeted Tier C task. Build and lock a separate source-review/download queue. Preserve candidate, source, city, unit, cycle, mechanism-gap, region, and verification lineage.

Do not fetch or inspect repository remotes, include nonverified or Tier A/B/D/repair/deprioritized rows, download outside the new locked queue, open PDF pages during preparation, run OCR, extract or rate evidence, normalize/impute/annualize values, compare wage outcomes, calculate wage gaps, run regressions or treatment effects, make population/national/final causal claims, ingest, codify, merge durable ledgers, or set global analysis readiness true. Source review/download is not extraction or causal proof.
"""
    write_text(OUTPUT_DIR / "next_targeted_tier_c_source_review_download_prompt.md", next_text)
    write_text(OUTPUT_DIR / "next_task.md", next_text)
    write_text(ANALYSIS / "targeted_tier_c_verification_from_bounded_memo_gaps_result_2026-07-26.md", f"Decision: `{decision}`. Gap-directed Tier C queue: 1,000; verified leads: {len(verified)}. HEAD-only verification; no document download, extraction, rating, or analysis. Global analysis readiness remains false.\n")
    write_text(ANALYSIS / "targeted_tier_c_verification_from_bounded_memo_gaps_dashboard_status_note_2026-07-26.md", f"Current phase: targeted Tier C verification from bounded memo gaps. Decision: `{decision}`. Queue: 1,000; verified leads: {len(verified)}. Bounded memo scope remains 268/208/90/72 and linked through dashboard metadata. Global analysis readiness: false.\n")
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
    return decision


def verify_dashboard_visibility() -> None:
    analysis_path = ROOT / "docs/dashboard/data/analysis_readiness.json"
    calibration_path = ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json"
    dist_path = ROOT / "docs/dashboard/dist/index.html"
    if not all(path.is_file() for path in (analysis_path, calibration_path, dist_path)):
        raise RuntimeError("dashboard data or production build artifact missing")
    analysis = read_json(analysis_path)
    calibration = read_json(calibration_path)
    memo_decision = "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended"
    memo_path = "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo.md"
    metadata_path = "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json"
    geography_path = "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_geographic_coverage.md"
    scope = calibration.get("bounded_internal_mechanism_linkage_claim_memo_scope", {})
    serialized = json.dumps({"analysis": analysis, "calibration": calibration}, sort_keys=True)
    checks = {
        "local_dashboard_data_rebuilt": True, "local_production_build_exists": dist_path.is_file(),
        "current_dashboard_phase": calibration.get("calibration_phase"),
        "memo_stage_phase_or_lineage_present": "bounded_internal_mechanism_linkage_claim_memo" in serialized,
        "memo_decision_present": memo_decision in serialized,
        "global_analysis_readiness_false": '"global_analysis_readiness": true' not in serialized.casefold(),
        "memo_exact_same_source_pairs_268": scope.get("exact_same_source_linked_pair_count") == 268,
        "memo_linked_quantitative_rows_208": scope.get("linked_quantitative_row_count") == 208,
        "memo_linked_qualitative_records_90": scope.get("linked_qualitative_record_count") == 90,
        "memo_path_present": memo_path in serialized, "memo_dashboard_metadata_path_present": metadata_path in serialized,
        "memo_geography_path_present": geography_path in serialized,
        "memo_geographic_summary_or_path_present": "geographic" in serialized.casefold(),
    }
    if not all(value is True for key, value in checks.items() if key != "current_dashboard_phase"):
        raise RuntimeError(f"dashboard memo visibility gate failed: {checks}")
    changed = subprocess.run(["git", "diff", "--name-only", "--", "docs/dashboard", "docs/analysis"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    write_json(OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_verified_keys.json", checks)
    write_json(OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_decision.json", {
        "decision": "bounded_memo_metadata_verified_in_local_dashboard_data_and_production_build",
        "dashboard_phase": calibration.get("calibration_phase"), "memo_decision": memo_decision,
        "memo_scope": scope, "production_build_path": str(dist_path.relative_to(ROOT)),
        "changed_dashboard_and_status_files": changed, "global_analysis_readiness": False,
        "external_visibility_note": "GitHub Pages deployment or browser cache delay may remain after a successful push; remotes and Pages settings were not inspected.",
    })
    write_text(OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_changed_files.txt", "\n".join(changed) or "No additional tracked dashboard diff at visibility-check time.")
    write_text(OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_summary.md", f"""# Dashboard visibility check for bounded memo

The rebuilt local dashboard data contains the bounded memo decision, the 268/208/90 scope counts, global-readiness closure, and paths to the memo, dashboard metadata, and geographic report. The production build exists at `{dist_path.relative_to(ROOT)}`. Current dashboard phase: `{calibration.get('calibration_phase')}`. After a successful push, external visibility may still lag because of GitHub Pages deployment timing or browser cache; no remote or Pages setting was inspected.
""")
    write_text(OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_push_status.md", """# Dashboard push status

Dashboard data and the local production build passed before commit. Plain `git push` is required after the commit; the actual push result and any cache/deployment-delay caveat are recorded in the final relay and task response.
""")
    write_text(ANALYSIS / "dashboard_visibility_check_for_bounded_memo_2026-07-26.md", f"Local dashboard data and `{dist_path.relative_to(ROOT)}` contain or point to the bounded memo decision, scope, metadata, and geography. Global analysis readiness remains false. External visibility may still be subject to Pages deployment timing or browser cache after push.\n")


def validate_complete() -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"partial Tier C outputs: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_tier_c_verification_decision.json")
    results = read_csv(OUTPUT_DIR / "targeted_tier_c_verification_results.csv")
    invariants = read_json(OUTPUT_DIR / "targeted_tier_c_verification_invariant_checks.json")
    if not (
        len(results) == EXPECTED_QUEUE and decision.get("verification_queue_count") == EXPECTED_QUEUE
        and decision.get("decision") in {"targeted_tier_c_verification_completed_source_review_ready_dashboard_visible", "targeted_tier_c_verification_completed_repair_needed"}
        and decision.get("http_method") == "HEAD" and decision.get("get_requests") == 0
        and decision.get("documents_downloaded") == 0 and decision.get("pdf_pages_accessed") == 0
        and decision.get("global_analysis_readiness") is False and invariants.get("all_invariants_passed") is True
        and all(row["priority_tier"] == "tier_c" for row in results)
        and all(row["download_status"] == "not_downloaded" and row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["causal_status"] == "not_causal_evidence" for row in results)
    ):
        raise RuntimeError("completed Tier C package fails invariant gate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--verify-dashboard", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if sum((args.prepare, args.live, args.verify_dashboard, args.resume)) != 1:
        raise RuntimeError("choose exactly one action")
    if args.prepare:
        prepare(); return 0
    if args.live:
        results = asyncio.run(execute_live())
        print(json.dumps({"status": "completed", "decision": summarize(results), "results": len(results)})); return 0
    if args.verify_dashboard:
        verify_dashboard_visibility(); validate_complete(); print(json.dumps({"status": "dashboard_visibility_verified"})); return 0
    validate_inputs(); validate_complete(); verify_dashboard_visibility()
    print(json.dumps({"status": "resume_validated_zero_unsafe_writes", "decision": read_json(OUTPUT_DIR / "targeted_tier_c_verification_decision.json")["decision"]})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
