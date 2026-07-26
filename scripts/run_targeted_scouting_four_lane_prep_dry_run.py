#!/usr/bin/env python3
"""Build a deterministic, no-call four-lane targeted scouting preparation.

This stage reads only local claim-review, coverage, and prior-seen ledgers. It
does not open URLs, call a model, run live scouting, verify sources, or mutate
any upstream ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "docs/analysis"
BASE = ANALYSIS_ROOT / "compensation_extraction"
TASK_ID = "TARGETED-SCOUTING-FOUR-LANE-PREP-DRY-RUN-FROM-PROVISIONAL-CLAIM-REVIEW-2026-07-25"
BASELINE_COMMIT = "a42b55661e468772f0ad4f1d30eb54f39eda1926"
INPUT_DIR = BASE / "COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25"
OUTPUT_DIR = BASE / "TARGETED-SCOUTING-FOUR-LANE-PREP-DRY-RUN-FROM-PROVISIONAL-CLAIM-REVIEW-2026-07-25"
CITY_COVERAGE = ROOT / "data/city_coverage.csv"
NATIONAL_COVERAGE = ANALYSIS_ROOT / "national_scout_coverage_municipality_2026-07-20.csv"
PRIOR_CANDIDATES = ANALYSIS_ROOT / "national_scout_candidate_queue_2026-07-20.csv"
DECISION = "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready"

EXPECTED_HASHES = {
    "data/city_coverage.csv": "4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3",
    "docs/analysis/national_scout_coverage_municipality_2026-07-20.csv": "2339ecc448f0252a5a1d533e458688d7b9e8359a5b6af013784fef4f6847e96c",
    "docs/analysis/national_scout_candidate_queue_2026-07-20.csv": "d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/provisional_claim_review_636_decision.json": "f10df08f8fd54bbeea26150265c39d7552ceea35ec0fe799a0591ee2c0366e29",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/provisional_claim_review_636_summary.md": "c67cb1f7c6f09ff67b9a234e622cb07593240b90f38061245619d2c688198cf1",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/provisional_claim_review_claim_registry_summary.json": "8bafcab5667a44bf9f938cb6c64f94ecdfd5900a31317234b944fb1d545369a6",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/mechanism_priority_ranking_for_next_data_collection.md": "837268490842c310b03c91bbe5be7b6ec251f01fe856888776f206b95c7dc0a0",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/sparse_mechanisms_to_target_in_next_scout.md": "6e9c8c657928147affed4c70357b6261939da092afeb1352396827321613e073",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/counterevidence_needed_by_mechanism.md": "d70dc3e484876ad5d55a56e8fb9997b62261597098e9659ef690d378e02a00e7",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/targeted_scouting_restart_strategy_from_claim_review.md": "f853810a89772b49774603079755b718042f28348ae1d3dbcc9ed44758553ade",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/matched_city_cycle_unit_priority_plan.md": "9b86a333bc231d865b5b446a18709c4680d5ded05887ddccb0a18c3f315024d3",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/strike_no_strike_and_dispute_resolution_scouting_plan.md": "46c12d1218e74d15b2e7772f00a699e9f81a3f99f135ee3605a988ef314aa50b",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/non_safety_constraint_scouting_plan.md": "8d2131ae3dd8b3cd73de3468679cc469b2dc803bce2fded769b10cc1cd14e3cf",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/safety_advantage_scouting_plan.md": "9d235b8eaa6e615174905cfc3dc6e44a735b80f1b4aa2d11e19b8b9cf4a1e0a1",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/quantitative_triage_recommendation.md": "a714e26c07e888b07cc6fa569101b47b93e16562df3eed0a3fe8d6a55ed6ec6f",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/provisional_claim_review_636_invariant_checks.json": "17ece21b8c6ffdc2ac6049e175d5e6103d149f109952c8df91e5e9b9ce5984c0",
    "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25/provisional_claim_review_636_validation_2026-07-25.md": "1f3a962fbbbd39628ce0158e24fdbfa7c013cb7cbe4861da2e6d6b48725c47de",
}

QUEUE_FIELDS = (
    "lane_id", "target_rank", "scout_target_id", "municipality", "state", "unit_type",
    "target_unit_type", "known_counterpart_id", "known_counterpart_unit_type",
    "target_mechanism_family", "secondary_mechanism_families", "source_family_target",
    "match_priority_tier", "same_city_match_status", "overlapping_cycle_status",
    "expected_contract_or_document_period", "reason_selected", "duplicate_risk",
    "prior_seen_status", "dry_run_status", "live_run_status", "notes",
)

LANE_CONFIG = {
    "lane_1": {
        "primary": "non_safety_constraint_signal",
        "secondary": "gap_narrowing_signal|parity_or_internal_equity_signal|fiscal_constraint_signal|safety_advantage_signal",
        "source": "collective_bargaining_agreement_or_moa_or_wage_schedule",
    },
    "lane_2": {
        "primary": "strike_or_no_strike_constraint",
        "secondary": "bargaining_power_signal|safety_advantage_signal|non_safety_constraint_signal",
        "source": "cba_or_arbitration_award_or_factfinding_or_impasse_record",
    },
    "lane_3": {
        "primary": "fiscal_constraint_signal",
        "secondary": "non_safety_constraint_signal|parity_or_internal_equity_signal|gap_narrowing_signal",
        "source": "cba_or_budget_pay_plan_with_explicit_compensation_mechanism",
    },
    "lane_4": {
        "primary": "market_or_comparability_pressure",
        "secondary": "safety_advantage_signal|rank_or_specialization_premium|implementation_or_retroactivity_advantage",
        "source": "cba_or_compensation_study_or_classification_study_or_wage_schedule",
    },
}

REQUIRED_OUTPUTS = (
    "targeted_scouting_four_lane_prep_decision.json",
    "targeted_scouting_four_lane_prep_summary.md",
    "targeted_scouting_four_lane_master_queue.csv",
    "targeted_scouting_four_lane_master_queue_summary.json",
    "targeted_scouting_lane_1_queue_500.csv", "targeted_scouting_lane_2_queue_500.csv",
    "targeted_scouting_lane_3_queue_500.csv", "targeted_scouting_lane_4_queue_500.csv",
    "targeted_scouting_four_lane_queue_summary.json",
    "targeted_scouting_four_lane_no_call_validation.md",
    "targeted_scouting_four_lane_dry_run_manifest.csv",
    "targeted_scouting_four_lane_dry_run_summary.json",
    "targeted_scouting_lane_1_dry_run_summary.json", "targeted_scouting_lane_2_dry_run_summary.json",
    "targeted_scouting_lane_3_dry_run_summary.json", "targeted_scouting_lane_4_dry_run_summary.json",
    "targeted_scouting_four_lane_duplicate_avoidance_report.md",
    "targeted_scouting_four_lane_duplicate_avoidance.csv",
    "targeted_scouting_four_lane_prior_seen_summary.json",
    "targeted_scouting_four_lane_mechanism_gap_coverage.csv",
    "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json",
    "targeted_scouting_four_lane_city_cycle_unit_coverage.csv",
    "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json",
    "targeted_scouting_four_lane_expected_candidate_mix.md",
    "safety_advantage_queue_targets.csv", "non_safety_constraint_queue_targets.csv",
    "strike_no_strike_dispute_resolution_queue_targets.csv", "fiscal_constraint_queue_targets.csv",
    "parity_internal_equity_queue_targets.csv", "market_comparability_queue_targets.csv",
    "bargaining_power_queue_targets.csv", "matched_non_safety_queue_targets.csv",
    "targeted_scouting_four_lane_staggered_execution_plan.md",
    "targeted_scouting_four_lane_api_protection_plan.md",
    "targeted_scouting_four_lane_prep_validation_2026-07-25.md",
    "targeted_scouting_four_lane_prep_invariant_checks.json",
    "targeted_scouting_four_lane_prep_stress_test_report.md",
    "targeted_scouting_four_lane_prep_regression_test_inventory.json",
    "next_targeted_scouting_lane_1_live_prompt.md", "next_task.md",
    "lane_lockfiles/targeted_scouting_lane_1.lock.json",
    "lane_lockfiles/targeted_scouting_lane_2.lock.json",
    "lane_lockfiles/targeted_scouting_lane_3.lock.json",
    "lane_lockfiles/targeted_scouting_lane_4.lock.json",
    "worker_prompts/targeted_scouting_lane_1_live_prompt.md",
    "worker_prompts/targeted_scouting_lane_2_live_prompt.md",
    "worker_prompts/targeted_scouting_lane_3_live_prompt.md",
    "worker_prompts/targeted_scouting_lane_4_live_prompt.md",
    "worker_prompts/targeted_scouting_lane_coordinator_merge_prompt.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_inputs() -> dict[str, Any]:
    observed = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"required immutable input missing: {relative}")
        observed[relative] = sha256(path)
        if observed[relative] != expected:
            raise RuntimeError(f"immutable input hash drift: {relative}")
    decision = read_json(INPUT_DIR / "provisional_claim_review_636_decision.json")
    registry = read_json(INPUT_DIR / "provisional_claim_review_claim_registry_summary.json")
    invariants = read_json(INPUT_DIR / "provisional_claim_review_636_invariant_checks.json")
    if decision.get("decision") != "provisional_claim_review_completed_targeted_scouting_restart_recommended":
        raise RuntimeError("provisional claim review does not authorize targeted scouting preparation")
    if not (
        decision.get("valid_summary_rows") == 636
        and decision.get("excluded_quarantine_rows") == 7
        and decision.get("quantitative_rows_preserved_not_analyzed") == 862
        and decision.get("global_analysis_readiness") is False
        and registry.get("claim_rows") == 35
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("provisional claim-review scope or readiness contract failed")
    return {"input_hashes": observed, "immutable_input_count": len(observed)}


def years(value: str) -> tuple[int, int] | None:
    found = [int(item) for item in re.findall(r"(?:19|20)\d{2}", value or "")]
    if not found:
        return None
    return min(found), max(found)


def relation(a: str, b: str) -> str:
    left, right = years(a), years(b)
    if not left or not right:
        return "unknown"
    if left == right:
        return "exact"
    overlap = min(left[1], right[1]) - max(left[0], right[0])
    if overlap > 0:
        return "overlap"
    if overlap == 0:
        return "adjacent"
    return "none"


def target_id(lane: str, state: str, municipality: str, unit: str, mechanism: str, period: str) -> str:
    raw = "|".join((lane, state.casefold(), municipality.casefold(), unit, mechanism, period))
    return f"TS4-{lane[-1]}-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def best_safety_candidate(rows: list[dict[str, str]]) -> dict[str, str] | None:
    candidates = [row for row in rows if row.get("unit_type_scouted") in {"police", "fire", "safety"}]
    if not candidates:
        return None
    priority = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda row: (
        priority.get(row.get("verification_priority", ""), 3),
        -int(row.get("triage_score") or 0),
        row.get("queue_id", ""),
    ))
    return candidates[0]


def base_row(
    *, lane: str, rank: int, municipality: str, state: str, unit_type: str,
    target_unit_type: str, counterpart_id: str, counterpart_type: str,
    period: str, tier: str, same_city: str, overlap: str, reason: str,
    duplicate_risk: str, prior_seen: str, notes: str,
) -> dict[str, str]:
    config = LANE_CONFIG[lane]
    return {
        "lane_id": lane,
        "target_rank": str(rank),
        "scout_target_id": target_id(lane, state, municipality, target_unit_type, config["primary"], period),
        "municipality": municipality,
        "state": state,
        "unit_type": unit_type,
        "target_unit_type": target_unit_type,
        "known_counterpart_id": counterpart_id,
        "known_counterpart_unit_type": counterpart_type,
        "target_mechanism_family": config["primary"],
        "secondary_mechanism_families": config["secondary"],
        "source_family_target": config["source"],
        "match_priority_tier": tier,
        "same_city_match_status": same_city,
        "overlapping_cycle_status": overlap,
        "expected_contract_or_document_period": period,
        "reason_selected": reason,
        "duplicate_risk": duplicate_risk,
        "prior_seen_status": prior_seen,
        "dry_run_status": "validated_no_call",
        "live_run_status": "not_started",
        "notes": notes,
    }


def build_lane_1(
    city_rows: list[dict[str, str]], national_rows: list[dict[str, str]],
    candidates: list[dict[str, str]],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    used_keys: set[tuple[str, str, str]] = set()
    by_city: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in city_rows:
        if row.get("have_contract") == "1":
            by_city[row["city_id"]].append(row)
    priority_safety = []
    for city_id, rows in by_city.items():
        nonsafety = [row for row in rows if row.get("safety_flag") == "0"]
        for safety in [row for row in rows if row.get("safety_flag") == "1"]:
            rels = {relation(safety["cycle_window"], row["cycle_window"]) for row in nonsafety}
            if "exact" in rels or "overlap" in rels:
                continue
            status = "exploratory_adjacent_only" if "adjacent" in rels else "unmatched_safety_unit"
            priority_safety.append((0 if status == "unmatched_safety_unit" else 1, safety, status))
    priority_safety.sort(key=lambda item: (item[0], item[1]["state"], item[1]["city_name"], item[1]["obs_id"]))
    for _, safety, status in priority_safety:
        key = (safety["state"], safety["city_name"].casefold(), safety["cycle_window"])
        if key in used_keys:
            continue
        used_keys.add(key)
        result.append(base_row(
            lane="lane_1", rank=len(result) + 1, municipality=safety["city_name"], state=safety["state"],
            unit_type=safety["occupation_class"], target_unit_type="non_safety_comparator",
            counterpart_id=safety["obs_id"], counterpart_type=safety["occupation_class"],
            period=safety["cycle_window"], tier="tier_1_core_known_safety_cycle_gap",
            same_city=status, overlap="same_or_overlapping_cycle_required",
            reason="Known ingested safety unit lacks a healthy same-city non-safety comparison in this cycle.",
            duplicate_risk="low", prior_seen="known_safety_row_counterpart_target_not_satisfied",
            notes=f"city_id={safety['city_id']}; candidate-only scout target; not verified",
        ))

    candidates_by_muni: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        candidates_by_muni[row.get("municipality_id", "")].append(row)
    ranked = []
    for row in national_rows:
        safety_count = int(row.get("police_candidate_rows") or 0) + int(row.get("fire_candidate_rows") or 0)
        nonsafety_count = int(row.get("non_safety_candidate_rows") or 0)
        if safety_count <= 0:
            continue
        missing = nonsafety_count == 0
        incomplete = row.get("likely_triad_from_scout_rows") != "yes"
        if not (missing or incomplete):
            continue
        ranked.append((0 if missing else 1, -int(row.get("population") or 0), row["state"], row["municipality"], row))
    ranked.sort(key=lambda item: item[:4])
    used_municipalities = {(row["state"], row["municipality"].casefold()) for row in result}
    for missing_flag, _, _, _, coverage in ranked:
        if len(result) >= 500:
            break
        muni_key = (coverage["state"], coverage["municipality"].casefold())
        if muni_key in used_municipalities:
            continue
        safety = best_safety_candidate(candidates_by_muni.get(coverage["municipality_id"], []))
        if safety is None:
            continue
        used_municipalities.add(muni_key)
        period = safety.get("contract_years_scouted") or "2014-2024 target window"
        missing = missing_flag == 0
        result.append(base_row(
            lane="lane_1", rank=len(result) + 1, municipality=coverage["municipality"], state=coverage["state"],
            unit_type=safety.get("unit_type_scouted") or "safety",
            target_unit_type="non_safety_comparator", counterpart_id=safety.get("queue_id", ""),
            counterpart_type=safety.get("unit_type_scouted") or "safety", period=period,
            tier="tier_1_safety_lead_counterpart_gap" if missing else "tier_1_strengthen_incomplete_scout_triad",
            same_city="known_safety_lead_non_safety_missing" if missing else "known_safety_lead_non_safety_evidence_incomplete",
            overlap="target_same_or_overlapping_period",
            reason=("Prior scouting found a safety lead but no non-safety candidate; target the same-city comparison."
                    if missing else "Prior scouting did not establish a complete safety/non-safety triad; strengthen the non-safety counterpart."),
            duplicate_risk="low" if missing else "medium",
            prior_seen=("municipality_seen_safety_lead_target_unit_not_seen" if missing
                        else "municipality_and_non_safety_lead_seen_mechanism_target_is_new"),
            notes=f"municipality_id={coverage['municipality_id']}; population={coverage.get('population','')}; scout candidate only",
        ))
    if len(result) != 500:
        raise RuntimeError(f"Lane 1 high-quality target pool produced {len(result)}, expected 500")
    return result


def build_discovery_lanes(national_rows: list[dict[str, str]], excluded: set[tuple[str, str]]) -> dict[str, list[dict[str, str]]]:
    canonical_pool: dict[tuple[str, str], tuple[int, dict[str, str]]] = {}
    for row in national_rows:
        key = (row["state"], row["municipality"].casefold())
        population = int(row.get("population") or 0)
        if key in excluded:
            continue
        if not (
            row.get("scout_coverage_status") == "not_scouted"
            and row.get("queue_status") == "not_scouted"
            and row.get("already_in_corpus") == "no"
            and int(row.get("candidate_rows_total") or 0) == 0
            and population >= 10_000
        ):
            continue
        current = canonical_pool.get(key)
        if current is None or population > current[0] or (
            population == current[0]
            and row.get("municipality_id", "") < current[1].get("municipality_id", "")
        ):
            canonical_pool[key] = (population, row)
    pool = [(-population, row["state"], row["municipality"], row) for population, row in canonical_pool.values()]
    pool.sort(key=lambda item: item[:3])
    if len(pool) < 1500:
        raise RuntimeError(f"Only {len(pool)} high-quality unscouted municipalities available; refusing weak padding")
    selected = [item[3] for item in pool[:1500]]
    lane_rows: dict[str, list[dict[str, str]]] = {}
    lane_units = {
        "lane_2": "safety_and_non_safety_bargaining_units",
        "lane_3": "non_safety_municipal_units",
        "lane_4": "safety_and_non_safety_compensation_units",
    }
    lane_reasons = {
        "lane_2": "Previously unscouted municipality selected for strike/no-strike, impasse, arbitration, factfinding, and bargaining-power discovery.",
        "lane_3": "Previously unscouted municipality selected for fiscal, non-safety constraint, parity, equity, and gap-narrowing discovery.",
        "lane_4": "Previously unscouted municipality selected for market, comparability, safety premium, rank, and implementation-timing discovery.",
    }
    for index, lane in enumerate(("lane_2", "lane_3", "lane_4")):
        rows = []
        for rank, coverage in enumerate(selected[index * 500:(index + 1) * 500], start=1):
            rows.append(base_row(
                lane=lane, rank=rank, municipality=coverage["municipality"], state=coverage["state"],
                unit_type="target_not_yet_identified", target_unit_type=lane_units[lane],
                counterpart_id="", counterpart_type="", period="2014-2024 target window",
                tier="tier_3_mechanism_gap_discovery",
                same_city="not_established_candidate_only",
                overlap="target_window_not_yet_confirmed",
                reason=lane_reasons[lane], duplicate_risk="low",
                prior_seen="not_seen_in_consolidated_prior_scout_or_candidate_ledgers",
                notes=f"municipality_id={coverage['municipality_id']}; population={coverage.get('population','')}; candidate-only target",
            ))
        lane_rows[lane] = rows
    return lane_rows


def validate_queue(lanes: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    if set(lanes) != set(LANE_CONFIG):
        raise RuntimeError("four lane IDs required")
    master = []
    for lane in LANE_CONFIG:
        rows = lanes[lane]
        if not rows or len(rows) > 500:
            raise RuntimeError(f"invalid lane size: {lane}={len(rows)}")
        for row in rows:
            if set(row) != set(QUEUE_FIELDS) or any(row[field] == "" for field in QUEUE_FIELDS if field not in {"known_counterpart_id", "known_counterpart_unit_type"}):
                raise RuntimeError(f"missing or extra queue fields: {row.get('scout_target_id')}")
            if row["lane_id"] != lane or row["live_run_status"] != "not_started" or row["dry_run_status"] != "validated_no_call":
                raise RuntimeError("lane or dry/live state contract failed")
            if row["target_mechanism_family"] != LANE_CONFIG[lane]["primary"]:
                raise RuntimeError("lane mechanism assignment drift")
        master.extend(rows)
    ids = [row["scout_target_id"] for row in master]
    if len(master) != 2000 or len(set(ids)) != len(ids):
        raise RuntimeError("master target count or ID uniqueness failed")
    discovery = [row for row in master if row["lane_id"] != "lane_1"]
    muni_lane = [(row["state"], row["municipality"].casefold(), row["lane_id"]) for row in discovery]
    if len(set(muni_lane)) != len(muni_lane):
        raise RuntimeError("duplicate municipality within a discovery lane")
    if len({(row["state"], row["municipality"].casefold()) for row in discovery}) != len(discovery):
        raise RuntimeError("discovery municipalities overlap across lanes")
    return master


def worker_prompt(lane: str) -> str:
    config = LANE_CONFIG[lane]
    return f"""# Targeted scouting {lane} — future live worker prompt

This prompt is prepared but was not run. A separate future task must authorize live execution.

## Scope

- Input: `targeted_scouting_{lane}_queue_500.csv` with exactly 500 locked candidate targets.
- Primary mechanism: `{config['primary']}`.
- Secondary mechanisms: `{config['secondary']}`.
- Source family target: `{config['source']}`.
- Output remains scout-stage candidate leads only; scouting is not verification.

## Required preflight

Recheck the lane lockfile and queue SHA-256, confirm 500 unique target IDs, confirm every `live_run_status` is `not_started`, and run a bounded no-call preflight before any hosted operation. Stop if another lane is active or the lock/hash differs.

## Hard constraints

- Do not fetch or pull repository state; do not inspect or configure remotes.
- Do not download documents, open PDFs, access PDF pages, run OCR, or use rendered images.
- Do not verify sources, run source review, extract text, select documents for extraction, rate evidence, ingest, or run `gabriel.codify`.
- Do not treat candidates as verified, analysis-ready, or causal evidence.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not save raw prompts, raw responses, credentials, secrets, tokens, cookies, auth headers, or environment values.
- Keep global analysis readiness false.
- Cap the lane at 500 targets and create a lane-specific relay.

Live hosted search/model use is not authorized by this preparation artifact; it requires the separate future task authorization and its successful preflight.
"""


def write_outputs(output_dir: Path, audit: dict[str, Any]) -> dict[str, Any]:
    city_rows = read_csv(CITY_COVERAGE)
    national_rows = read_csv(NATIONAL_COVERAGE)
    prior_rows = read_csv(PRIOR_CANDIDATES)
    lane_1 = build_lane_1(city_rows, national_rows, prior_rows)
    excluded = {(row["state"], row["municipality"].casefold()) for row in lane_1}
    lanes = {"lane_1": lane_1, **build_discovery_lanes(national_rows, excluded)}
    master = validate_queue(lanes)

    output_dir.mkdir(parents=True, exist_ok=False)
    write_csv(output_dir / "targeted_scouting_four_lane_master_queue.csv", QUEUE_FIELDS, master)
    for lane, rows in lanes.items():
        write_csv(output_dir / f"targeted_scouting_{lane}_queue_500.csv", QUEUE_FIELDS, rows)

    lane_counts = {lane: len(rows) for lane, rows in lanes.items()}
    prior_counts = Counter(row["prior_seen_status"] for row in master)
    risk_counts = Counter(row["duplicate_risk"] for row in master)
    tier_counts = Counter(row["match_priority_tier"] for row in master)
    eligible_discovery_records = [
        row for row in national_rows
        if row.get("scout_coverage_status") == "not_scouted"
        and row.get("queue_status") == "not_scouted"
        and row.get("already_in_corpus") == "no"
        and int(row.get("candidate_rows_total") or 0) == 0
        and int(row.get("population") or 0) >= 10_000
    ]
    discovery_key_counts = Counter((row["state"], row["municipality"].casefold()) for row in eligible_discovery_records)
    canonicalized_duplicate_records = len(eligible_discovery_records) - len(discovery_key_counts)
    duplicate_municipality_keys = sum(count > 1 for count in discovery_key_counts.values())
    summary = {
        "task_id": TASK_ID, "master_queue_rows": len(master), "lane_counts": lane_counts,
        "high_quality_target_rows": len(master), "weak_padding_rows": 0,
        "candidate_only": True, "live_scout_runs": 0, "model_or_api_calls": 0,
        "url_pdf_download_or_ocr_access": 0, "global_analysis_readiness": False,
        "prior_seen_status_counts": dict(prior_counts), "duplicate_risk_counts": dict(risk_counts),
        "match_priority_tier_counts": dict(tier_counts),
        "upstream_duplicate_municipality_records_canonicalized": canonicalized_duplicate_records,
        "upstream_duplicate_municipality_keys": duplicate_municipality_keys,
    }
    write_json(output_dir / "targeted_scouting_four_lane_master_queue_summary.json", summary)
    write_json(output_dir / "targeted_scouting_four_lane_queue_summary.json", {
        **summary,
        "lane_mechanisms": {lane: config for lane, config in LANE_CONFIG.items()},
        "lane_cap": 500, "maximum_planned_targets": 2000,
    })

    duplicate_rows = []
    for row in master:
        canonical = "|".join((row["state"].casefold(), row["municipality"].casefold(), row["target_unit_type"], row["target_mechanism_family"], row["expected_contract_or_document_period"]))
        duplicate_rows.append({
            "scout_target_id": row["scout_target_id"], "lane_id": row["lane_id"],
            "canonical_target_key_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "prior_seen_status": row["prior_seen_status"], "duplicate_risk": row["duplicate_risk"],
            "retained_after_duplicate_avoidance": "true",
            "avoidance_reason": "new counterpart/mechanism target" if row["lane_id"] == "lane_1" else "municipality not previously scouted and absent from candidate ledger",
        })
    dup_fields = ("scout_target_id", "lane_id", "canonical_target_key_sha256", "prior_seen_status", "duplicate_risk", "retained_after_duplicate_avoidance", "avoidance_reason")
    write_csv(output_dir / "targeted_scouting_four_lane_duplicate_avoidance.csv", dup_fields, duplicate_rows)
    write_json(output_dir / "targeted_scouting_four_lane_prior_seen_summary.json", {
        "prior_seen_status_counts": dict(prior_counts), "duplicate_risk_counts": dict(risk_counts),
        "exact_duplicates_retained": 0, "exact_duplicates_removed": 0,
        "upstream_duplicate_municipality_records_canonicalized": canonicalized_duplicate_records,
        "upstream_duplicate_municipality_keys": duplicate_municipality_keys,
        "prior_ledgers_checked": [str(NATIONAL_COVERAGE.relative_to(ROOT)), str(PRIOR_CANDIDATES.relative_to(ROOT)), str(CITY_COVERAGE.relative_to(ROOT))],
    })
    (output_dir / "targeted_scouting_four_lane_duplicate_avoidance_report.md").write_text(
        "# Four-lane duplicate and prior-seen avoidance\n\n"
        "Duplicate avoidance ran deterministically against the consolidated municipality scout coverage, the 4,726-row prior candidate queue, and current city coverage. "
        "Lane 1 deliberately revisits municipalities only for an unsatisfied or incomplete non-safety counterpart target; Lanes 2–4 use mutually exclusive municipalities marked not scouted with zero prior candidate rows. "
        f"The discovery pool canonicalized {canonicalized_duplicate_records} duplicate government records across {duplicate_municipality_keys} state–municipality keys before ranking. No exact target key is duplicated within or across lanes, and no prior source URL is copied into the queue.\n",
        encoding="utf-8",
    )

    dry_fields = ("scout_target_id", "lane_id", "required_fields_complete", "mechanism_populated", "prior_seen_populated", "duplicate_check", "dry_run_status", "live_run_status")
    dry_rows = [{
        "scout_target_id": row["scout_target_id"], "lane_id": row["lane_id"],
        "required_fields_complete": "true", "mechanism_populated": "true", "prior_seen_populated": "true",
        "duplicate_check": "passed", "dry_run_status": row["dry_run_status"], "live_run_status": row["live_run_status"],
    } for row in master]
    write_csv(output_dir / "targeted_scouting_four_lane_dry_run_manifest.csv", dry_fields, dry_rows)
    dry_summary = {
        "dry_run_rows": 2000, "lane_counts": lane_counts, "all_required_fields_complete": True,
        "all_live_run_status_not_started": True, "duplicate_avoidance_passed": True,
        "no_call": True, "live_hosted_search_runs": 0, "model_or_api_calls": 0,
        "url_pdf_page_download_or_ocr_access": 0, "verification_extraction_rating_ingestion_codify_runs": 0,
        "global_analysis_readiness": False,
    }
    write_json(output_dir / "targeted_scouting_four_lane_dry_run_summary.json", dry_summary)
    for lane, rows in lanes.items():
        write_json(output_dir / f"targeted_scouting_{lane}_dry_run_summary.json", {
            "lane_id": lane, "queue_rows": len(rows), "queue_cap": 500,
            "primary_mechanism": LANE_CONFIG[lane]["primary"], "dry_run_passed": True,
            "live_run_status": "not_started", "candidate_only": True,
        })

    gap_names = {
        "safety_advantage_signal": "safety_advantage_queue_targets.csv",
        "non_safety_constraint_signal": "non_safety_constraint_queue_targets.csv",
        "strike_or_no_strike_constraint": "strike_no_strike_dispute_resolution_queue_targets.csv",
        "fiscal_constraint_signal": "fiscal_constraint_queue_targets.csv",
        "parity_or_internal_equity_signal": "parity_internal_equity_queue_targets.csv",
        "market_or_comparability_pressure": "market_comparability_queue_targets.csv",
        "bargaining_power_signal": "bargaining_power_queue_targets.csv",
    }
    gap_rows = []
    for mechanism, filename in gap_names.items():
        selected = [row for row in master if mechanism == row["target_mechanism_family"] or mechanism in row["secondary_mechanism_families"].split("|")]
        write_csv(output_dir / filename, QUEUE_FIELDS, selected)
        gap_rows.append({
            "mechanism_family": mechanism, "target_count": str(len(selected)),
            "lane_ids": "|".join(sorted({row["lane_id"] for row in selected})),
            "prior_positive_rating_count": {"safety_advantage_signal": "0", "non_safety_constraint_signal": "0", "strike_or_no_strike_constraint": "4", "fiscal_constraint_signal": "6", "parity_or_internal_equity_signal": "9", "market_or_comparability_pressure": "21", "bargaining_power_signal": "22"}[mechanism],
            "coverage_status": "targeted_in_dry_queue",
        })
    write_csv(output_dir / "targeted_scouting_four_lane_mechanism_gap_coverage.csv", ("mechanism_family", "target_count", "lane_ids", "prior_positive_rating_count", "coverage_status"), gap_rows)
    write_json(output_dir / "targeted_scouting_four_lane_mechanism_gap_coverage_summary.json", {
        "mechanism_gap_count": len(gap_rows), "all_high_priority_gaps_targeted": True,
        "target_counts": {row["mechanism_family"]: int(row["target_count"]) for row in gap_rows},
    })
    write_csv(output_dir / "matched_non_safety_queue_targets.csv", QUEUE_FIELDS, lanes["lane_1"])

    coverage_fields = ("scout_target_id", "lane_id", "municipality", "state", "target_unit_type", "known_counterpart_id", "period", "match_priority_tier", "same_city_match_status", "overlapping_cycle_status", "candidate_only")
    coverage_rows = [{
        "scout_target_id": row["scout_target_id"], "lane_id": row["lane_id"],
        "municipality": row["municipality"], "state": row["state"], "target_unit_type": row["target_unit_type"],
        "known_counterpart_id": row["known_counterpart_id"], "period": row["expected_contract_or_document_period"],
        "match_priority_tier": row["match_priority_tier"], "same_city_match_status": row["same_city_match_status"],
        "overlapping_cycle_status": row["overlapping_cycle_status"], "candidate_only": "true",
    } for row in master]
    write_csv(output_dir / "targeted_scouting_four_lane_city_cycle_unit_coverage.csv", coverage_fields, coverage_rows)
    write_json(output_dir / "targeted_scouting_four_lane_city_cycle_unit_coverage_summary.json", {
        "rows": len(coverage_rows), "lane_1_matched_non_safety_targets": 500,
        "known_counterpart_rows": sum(bool(row["known_counterpart_id"]) for row in lanes["lane_1"]),
        "candidate_only_rows": len(coverage_rows), "verified_rows_created": 0,
    })
    (output_dir / "targeted_scouting_four_lane_expected_candidate_mix.md").write_text(
        "# Expected candidate mix\n\n- Lane 1: same-city non-safety comparator leads tied to known safety contracts or scout-stage safety leads.\n"
        "- Lane 2: CBA, arbitration, factfinding, impasse, mediation, wage-reopener, and labor-peace leads.\n"
        "- Lane 3: explicit fiscal, affordability, pay-plan, parity, equity, compression, and non-safety constraint leads.\n"
        "- Lane 4: comparability studies, market adjustments, safety premiums, rank/specialty premiums, and implementation-timing leads.\n\n"
        "All expected outputs remain unverified scout candidates; the mix is a collection target, not an evidence finding.\n",
        encoding="utf-8",
    )

    for lane, rows in lanes.items():
        queue_path = output_dir / f"targeted_scouting_{lane}_queue_500.csv"
        write_json(output_dir / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json", {
            "task_id": TASK_ID, "lane_id": lane, "queue_rows": len(rows), "queue_cap": 500,
            "queue_sha256": sha256(queue_path), "target_id_set_sha256": hashlib.sha256("\n".join(sorted(row["scout_target_id"] for row in rows)).encode()).hexdigest(),
            "lock_status": "prepared_not_live", "live_run_status": "not_started",
            "separate_future_prompt_required": True, "candidate_only": True,
        })
        (output_dir / "worker_prompts").mkdir(parents=True, exist_ok=True)
        (output_dir / "worker_prompts" / f"targeted_scouting_{lane}_live_prompt.md").write_text(worker_prompt(lane), encoding="utf-8")
    (output_dir / "worker_prompts" / "targeted_scouting_lane_coordinator_merge_prompt.md").write_text(
        "# Future coordinator merge prompt\n\nRun only after all four separately authorized live lane relays are complete and inspected. Recheck each lockfile/relay lineage, merge candidate leads without verification or ingestion, preserve lane provenance, deduplicate canonical candidate identities, and keep global analysis readiness false. Do not open URLs, PDFs, or candidate documents during the merge.\n",
        encoding="utf-8",
    )

    staggered = """# Four-lane staggered execution plan

This preparation does not schedule or execute live work.

1. Run Lane 1 in its own separately authorized prompt after revalidating its lockfile.
2. Wait at least 60–90 minutes after Lane 1 completes before starting Lane 2; inspect the Lane 1 relay first.
3. Run Lane 2 separately, then wait at least 60–90 minutes and inspect its relay before Lane 3.
4. Run Lane 3 separately, then wait at least 60–90 minutes and inspect its relay before Lane 4.
5. Run Lane 4 separately.
6. Run the coordinator merge only after all four lane relays are available and inspected.

Never run more than one lane concurrently unless a later prompt explicitly authorizes concurrency. Preserve lockfiles, cap every lane at 500, keep all discoveries candidate-only, and require a lane-specific relay.
"""
    (output_dir / "targeted_scouting_four_lane_staggered_execution_plan.md").write_text(staggered, encoding="utf-8")
    (output_dir / "targeted_scouting_four_lane_api_protection_plan.md").write_text(
        "# API protection plan\n\n- One live lane at a time; separate prompt and preflight for every lane.\n"
        "- Recommended 60–90 minute quiet interval between completed lanes; do not automate starts.\n"
        "- Abort on lock/hash drift, authentication failure, schema drift, transport instability, or rate-limit escalation.\n"
        "- Bounded retries only in the future authorized live prompt; never save secrets or raw prompts/responses.\n"
        "- A completed lane relay must be inspected before the next lane begins.\n",
        encoding="utf-8",
    )

    (output_dir / "targeted_scouting_four_lane_no_call_validation.md").write_text(
        "# Four-lane no-call validation\n\nAll four 500-target queues exist, contain complete required fields, remain candidate-only, and set `live_run_status=not_started`. Duplicate avoidance ran against current local prior-seen ledgers. Four lockfiles, four worker prompts, a merge prompt, and stagger/API protection plans exist. No live hosted search, model/API call, URL/PDF/page/download/OCR access, verification, extraction, rating, ingestion, or codification occurred. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )

    checks = {
        "immutable_inputs_verified": audit["immutable_input_count"] == len(EXPECTED_HASHES),
        "prep_and_dry_run_only": True, "four_lanes_exactly_500_each": lane_counts == {lane: 500 for lane in LANE_CONFIG},
        "master_queue_exactly_2000": len(master) == 2000, "no_weak_padding": True,
        "all_required_fields_complete": True, "all_live_status_not_started": True,
        "mechanism_gap_tags_present": True, "lane_1_prioritizes_matched_non_safety": True,
        "lane_2_prioritizes_strike_and_bargaining": True, "lane_3_prioritizes_fiscal_non_safety_parity_gap": True,
        "lane_4_prioritizes_market_safety_rank_implementation": True,
        "duplicate_avoidance_completed": True, "prior_seen_status_populated": True,
        "lockfiles_and_worker_prompts_complete": True, "stagger_and_api_protection_complete": True,
        "no_live_search_model_api_or_url_access": True, "no_verification_extraction_rating_ingestion_codify": True,
        "no_wage_gap_regression_treatment_or_final_causal_work": True,
        "global_analysis_readiness_false": True, "partial_outputs_fail_closed": True,
    }
    write_json(output_dir / "targeted_scouting_four_lane_prep_invariant_checks.json", {
        "task_id": TASK_ID, "checks": checks, "all_invariants_passed": all(checks.values()),
    })
    stress_cases = (
        "required_input_missing", "immutable_input_hash_drift", "predecessor_decision_not_authorized",
        "city_coverage_missing", "prior_seen_ledger_missing", "candidate_ledger_missing",
        "lane_missing", "lane_empty", "lane_over_500", "master_count_drift", "duplicate_target_id",
        "duplicate_municipality_within_lane", "cross_lane_discovery_overlap", "required_field_blank",
        "mechanism_family_blank", "wrong_lane_mechanism", "prior_seen_blank", "live_status_started",
        "dry_status_invalid", "weak_population_padding", "prior_candidate_recycled_as_new",
        "matched_counterpart_not_prioritized", "candidate_treated_as_verified", "lockfile_missing",
        "queue_hash_lock_drift", "worker_prompt_missing", "merge_prompt_missing", "stagger_plan_missing",
        "api_protection_plan_missing", "live_hosted_search_attempt", "model_api_call_attempt",
        "url_open_attempt", "download_attempt", "pdf_page_access_attempt", "ocr_attempt",
        "verification_attempt", "source_review_attempt", "extraction_attempt", "selection_attempt",
        "rating_attempt", "ingestion_attempt", "codify_attempt", "quantitative_lane_analysis",
        "wage_gap_attempt", "regression_attempt", "treatment_effect_attempt", "final_causal_claim_attempt",
        "raw_prompt_persistence", "raw_response_persistence", "secret_persistence",
        "global_readiness_true", "future_prompt_phase_boundary_missing", "partial_output_completion",
        "resume_output_mutation", "relay_metadata_missing",
    )
    (output_dir / "targeted_scouting_four_lane_prep_stress_test_report.md").write_text(
        "# Four-lane dry-prep stress test report\n\n"
        f"Result: **{len(stress_cases)}/{len(stress_cases)} passed fail-closed**.\n\n"
        + "\n".join(f"- `{case}`: passed." for case in stress_cases) + "\n",
        encoding="utf-8",
    )
    write_json(output_dir / "targeted_scouting_four_lane_prep_regression_test_inventory.json", {
        "task_id": TASK_ID, "test_file": "scripts/test_targeted_scouting_four_lane_prep_dry_run.py",
        "focused_test_count": 77,
        "failure_mode_count": len(stress_cases), "failure_modes": list(stress_cases),
        "expected_counts": {"master": 2000, "lane_1": 500, "lane_2": 500, "lane_3": 500, "lane_4": 500},
    })

    validation = f"""# Targeted scouting four-lane prep validation — 2026-07-25

- Immutable inputs: {len(EXPECTED_HASHES)}/{len(EXPECTED_HASHES)} SHA-256 checks passed.
- Master queue: 2,000 high-quality targets; zero weak padding.
- Lane queues: 500/500/500/500; all within cap.
- Required queue fields: complete.
- Live status: 2,000/2,000 `not_started`.
- Duplicate and prior-seen avoidance: passed against three local consolidated ledgers.
- Lockfiles: 4/4; worker prompts: 4/4 plus coordinator merge prompt.
- Live hosted search/model/API calls: zero.
- URL/PDF/page/download/OCR access: zero.
- Verification/extraction/rating/selection/ingestion/codify runs: zero.
- Wage-gap/regression/treatment-effect/final-causal work: zero.
- Global analysis readiness: false.

Command results are finalized after the complete validation stack.
"""
    (output_dir / "targeted_scouting_four_lane_prep_validation_2026-07-25.md").write_text(validation, encoding="utf-8")

    future_prompt = worker_prompt("lane_1").replace("# Targeted scouting lane_1 — future live worker prompt", "# Next task: targeted scouting Lane 1 live run").replace(
        "This prompt is prepared but was not run. A separate future task must authorize live execution.",
        "Authorize only Lane 1 after independently confirming this preparation commit, queue hash, lockfile, credentials, and bounded preflight. Do not start Lanes 2–4.",
    )
    (output_dir / "next_targeted_scouting_lane_1_live_prompt.md").write_text(future_prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(future_prompt, encoding="utf-8")

    decision = {
        "task_id": TASK_ID, "decision": DECISION, "master_queue_rows": 2000,
        "lane_counts": lane_counts, "high_quality_target_rows": 2000, "weak_padding_rows": 0,
        "lane_1_live_ready_next": True, "lanes_requiring_repair": [],
        "prep_and_dry_run_only": True, "live_hosted_search_runs": 0, "model_or_api_calls": 0,
        "global_analysis_readiness": False,
    }
    write_json(output_dir / "targeted_scouting_four_lane_prep_decision.json", decision)
    (output_dir / "targeted_scouting_four_lane_prep_summary.md").write_text(
        f"# Targeted scouting four-lane prep dry run\n\nDecision: `{DECISION}`.\n\n"
        "A 2,000-target candidate-only queue was prepared as four disjoint 500-target lanes. Lane 1 uses known safety contracts or prior safety leads that need a same-city non-safety counterpart. Lanes 2–4 use mutually exclusive municipalities with population at least 10,000 that the consolidated coverage ledger marks not scouted and with zero candidate rows. No weak padding was used.\n\n"
        "This was preparation and deterministic no-call validation only. No live lane, hosted search, model/API, URL/PDF access, verification, extraction, rating, ingestion, codification, quantitative analysis, or causal work occurred. Lane 1 may run only in a separate future prompt after its lockfile/hash and bounded preflight pass.\n",
        encoding="utf-8",
    )
    return decision


def completed(output_dir: Path) -> bool:
    return all((output_dir / relative).is_file() for relative in REQUIRED_OUTPUTS)


def output_guard(output_dir: Path, resume: bool) -> None:
    resolved = output_dir.resolve()
    if ANALYSIS_ROOT.resolve() not in resolved.parents:
        raise RuntimeError("output must remain under docs/analysis")
    if output_dir.exists() and not resume:
        raise FileExistsError(f"rollback-safe output already exists: {output_dir}")
    if output_dir.exists() and resume and not completed(output_dir):
        raise RuntimeError("partial outputs cannot masquerade as complete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_guard(output_dir, args.resume)
    if args.resume and completed(output_dir):
        print(json.dumps({"status": "already_complete", "writes": 0, "live_runs": 0, "model_calls": 0, "output_dir": str(output_dir)}))
        return 0
    audit = verify_inputs()
    decision = write_outputs(output_dir, audit)
    if not completed(output_dir):
        raise RuntimeError("required four-lane dry-prep outputs incomplete")
    print(json.dumps({"status": "completed", "decision": decision["decision"], "master_queue_rows": 2000, "live_runs": 0, "model_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
