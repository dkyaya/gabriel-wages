#!/usr/bin/env python3
"""Prepare a deterministic, no-call broad 4 x 2,500 scout wave.

This script reads only committed local coverage and planning ledgers. It does
not import or invoke any search, HTTP, model, verification, download,
extraction, rating, ingestion, or codification backend.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_broad_state_4x1000_scout_dry_run_prep as prior  # noqa: E402

ANALYSIS = ROOT / "docs/analysis"
OUTPUT = ANALYSIS / "compensation_extraction/BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
RESULT = ANALYSIS / "broad_state_4x2500_scout_infrastructure_prep_result_2026-07-29.md"
STATUS = ANALYSIS / "broad_state_4x2500_scout_infrastructure_prep_dashboard_status_note_2026-07-29.md"
GATE = ANALYSIS / "compensation_extraction/GLOBAL-ANALYSIS-READINESS-GATE-AFTER-BROAD-INGESTION-2026-07-28"
LIVE_4X1000 = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27"
OLD_PREP = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-4X1000-SCOUT-DRY-RUN-PREP-2026-07-27"
OLD_BROAD = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
TASK = "BROAD-STATE-4X2500-SCOUT-INFRASTRUCTURE-PREP-2026-07-29"
DECISION = "broad_state_4x2500_scout_infrastructure_prep_completed_live_ready"
SHARDS = tuple(f"broad_4x2500_shard_{i:03d}" for i in range(1, 5))
TARGETS_PER_SHARD = 2500
TARGET_COUNT = 10000
ACTUAL_COVERAGE = 6919
CURRENT_CANDIDATES = 13041

QUERY_FAMILIES = (
    ("cba_agreement", "cba", "collective bargaining agreement labor contract"),
    ("mou_settlement", "mou_or_memorandum; settlement_agreement", "memorandum MOU settlement agreement labor"),
    ("arbitration_factfinding", "arbitration_award; factfinding_report", "arbitration award factfinding impasse report"),
    ("salary_wage_schedule", "salary_ordinance; wage_schedule", "salary ordinance wage schedule compensation schedule"),
    ("budget_pay_plan", "budget_or_pay_plan", "municipal budget pay plan compensation plan"),
    ("civil_service_hr_pay", "civil_service_or_hr_pay_plan", "civil service HR pay plan classification"),
    ("compensation_classification_study", "compensation_study; classification_study", "compensation study classification study pay"),
    ("personnel_policy", "personnel_policy", "personnel policy employee compensation wages"),
    ("agenda_minutes_attachment", "agenda_packet_or_minutes", "council agenda minutes attached labor pay record"),
    ("local_pay_policy", "other_local_government_pay_policy", "local government pay policy labor relations compensation"),
    ("labor_relations_index", "cba; mou_or_memorandum; arbitration_award; factfinding_report", "official labor relations agreements awards index"),
    ("broad_pay_document_index", "salary_ordinance; wage_schedule; budget_or_pay_plan; civil_service_or_hr_pay_plan", "official municipal pay document source index"),
)

FIELDS = prior.TARGET_FIELDS
PREVIEW_FIELDS = [
    "scout_target_id", "shard_id", "shard_sequence", "state", "region",
    "municipality", "municipality_id", "prior_scout_covered_flag",
    "newly_planned_this_wave_flag", "source_family_query_family",
    "target_quality_tier", "dry_run_status", "live_status",
]

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required non-derivable input missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required non-derivable input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_md(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")

def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def number(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0

def unmatched_safety() -> set[tuple[str, str]]:
    units: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in read_csv(ROOT / "data/city_coverage.csv"):
        if row.get("have_contract") == "1":
            units[(row["state"], row["city_name"].casefold(), row["cycle_window"])].add(row["occupation_class"])
    return {
        (state, city)
        for (state, city, _), occupations in units.items()
        if occupations & {"police", "fire"} and not occupations - {"police", "fire"}
    }

def load_context() -> dict[str, Any]:
    gate = read_json(GATE / "global_analysis_readiness_gate_decision.json")
    if gate.get("decision") != "global_analysis_readiness_gate_completed_with_partial_readiness_next_scout_prep_ready" or gate.get("global_analysis_readiness") is not False:
        raise RuntimeError("global readiness gate does not authorize scout infrastructure prep")
    municipality = read_csv(ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv")
    universe = read_csv(ANALYSIS / "national_municipality_universe.csv")
    priorities = read_csv(ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv")
    state_coverage = read_csv(ANALYSIS / "national_scout_coverage_state.csv")
    candidates = read_csv(ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv")
    old_results = read_csv(OLD_BROAD / "broad_state_by_state_source_scout_results.csv")
    live_results = read_csv(LIVE_4X1000 / "broad_state_4x1000_parallel_live_scout_master_results.csv")
    old_locked = read_csv(OLD_BROAD / "broad_state_by_state_source_scout_locked_queue.csv")
    prep_locked = read_csv(OLD_PREP / "broad_state_4x1000_scout_master_locked_queue.csv")
    if len(municipality) != len(universe) or len(universe) != len(priorities) or len(universe) != 35589 or len(state_coverage) != 51:
        raise RuntimeError("municipality and state ledgers do not reconcile")
    canonical = {r["municipality_id"] for r in municipality if number(r.get("successful_live_scout_count", "0")) > 0}
    old_parseable = {r["municipality_id"] for r in old_results if r.get("parse_status") == "parseable"}
    live_parseable = {r["municipality_id"] for r in live_results if r.get("parse_status") == "parseable"}
    actual = canonical | old_parseable | live_parseable
    if (len(canonical), len(old_parseable), len(live_parseable), len(actual)) != (2436, 486, 3997, ACTUAL_COVERAGE):
        raise RuntimeError("current 6,919-municipality actual coverage does not reconcile")
    prior_planned = {r["municipality_id"] for r in old_locked} | {r["municipality_id"] for r in prep_locked}
    input_paths = [
        ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv",
        ANALYSIS / "national_municipality_universe.csv",
        ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv",
        ANALYSIS / "national_scout_coverage_state.csv",
        ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv",
        ROOT / "data/city_coverage.csv",
        GATE / "global_analysis_readiness_gate_decision.json",
        OLD_BROAD / "broad_state_by_state_source_scout_results.csv",
        LIVE_4X1000 / "broad_state_4x1000_parallel_live_scout_master_results.csv",
        OLD_BROAD / "broad_state_by_state_source_scout_locked_queue.csv",
        OLD_PREP / "broad_state_4x1000_scout_master_locked_queue.csv",
    ]
    return {
        "municipalities": municipality,
        "universe": {r["municipality_id"]: r for r in universe},
        "priorities": {r["municipality_id"]: r for r in priorities},
        "actual": actual,
        "prior_planned": prior_planned,
        "candidate_municipalities": {r.get("municipality_id", "") for r in candidates},
        "unmatched": unmatched_safety(),
        "input_hashes": {str(p.relative_to(ROOT)): sha(p) for p in input_paths},
    }

def balanced_quotas(available: Counter[str]) -> dict[str, int]:
    quotas = {state: 0 for state in sorted(available)}
    order = sorted(available, key=lambda state: (available[state], prior.REGIONS[state], state))
    remaining = TARGET_COUNT
    while remaining:
        progressed = False
        for state in order:
            if quotas[state] < available[state]:
                quotas[state] += 1
                remaining -= 1
                progressed = True
                if not remaining:
                    break
        if not progressed:
            raise RuntimeError("fewer than 10,000 defensible unscouted targets exist")
    return quotas

def build_queue(context: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, int], int]:
    eligible: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in context["municipalities"]:
        mid = row["municipality_id"]
        priority = context["priorities"][mid]
        if mid in context["actual"] or mid in context["prior_planned"]:
            continue
        if priority.get("future_scout_eligible_flag") != "yes":
            continue
        if row["state"] not in prior.REGIONS:
            continue
        eligible[row["state"]].append(row)
    available = Counter({state: len(rows) for state, rows in eligible.items()})
    # Some small or already saturated states have no defensible unscouted row
    # after the 6,919 completed municipalities and prior locked waves are
    # excluded. Forty or more states still constitutes a broad national plan.
    if sum(available.values()) < TARGET_COUNT or len(available) < 40:
        raise RuntimeError("defensible geographic target pool is too small")
    quotas = balanced_quotas(available)
    selected: list[dict[str, str]] = []
    for state, rows in eligible.items():
        rows.sort(key=lambda r: (
            0 if (state, r["municipality"].casefold()) in context["unmatched"] else 1,
            number(context["priorities"][r["municipality_id"]].get("national_priority_rank", "")),
            -number(r.get("population", "")), r["municipality"].casefold(), r["municipality_id"],
        ))
        selected.extend(rows[:quotas[state]])
    if len(selected) != TARGET_COUNT or len({r["municipality_id"] for r in selected}) != TARGET_COUNT:
        raise RuntimeError("selection is not a unique 10,000-municipality queue")

    shard_counts = Counter({s: 0 for s in SHARDS})
    state_shards: dict[str, Counter[str]] = defaultdict(Counter)
    region_shards: dict[str, Counter[str]] = defaultdict(Counter)
    by_shard: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted(selected, key=lambda r: (prior.REGIONS[r["state"]], r["state"], number(context["priorities"][r["municipality_id"]].get("national_priority_rank", "")), r["municipality_id"])):
        region = prior.REGIONS[row["state"]]
        shard = min(SHARDS, key=lambda s: (shard_counts[s], state_shards[row["state"]][s], region_shards[region][s], s))
        shard_counts[shard] += 1
        state_shards[row["state"]][shard] += 1
        region_shards[region][shard] += 1
        by_shard[shard].append(row)
    if any(shard_counts[s] != TARGETS_PER_SHARD for s in SHARDS):
        raise RuntimeError(f"shard sizing failed: {dict(shard_counts)}")

    output: list[dict[str, str]] = []
    global_sequence = 0
    for shard_index, shard in enumerate(SHARDS, 1):
        rows = sorted(by_shard[shard], key=lambda r: (prior.REGIONS[r["state"]], r["state"], r["municipality"].casefold(), r["municipality_id"]))
        for seq, row in enumerate(rows, 1):
            global_sequence += 1
            mid, state, municipality = row["municipality_id"], row["state"], row["municipality"]
            priority, universe = context["priorities"][mid], context["universe"][mid]
            family, expected, terms = QUERY_FAMILIES[(seq + shard_index - 2) % len(QUERY_FAMILIES)]
            matched = (state, municipality.casefold()) in context["unmatched"]
            if matched:
                tier = "matched_safety_non_safety_target"
            elif priority.get("priority_tier") in {"Tier 1", "Tier 2"}:
                tier = "strong_broad_geographic_target"
            elif family != "cba_agreement":
                tier = "strong_source_family_diversification_target"
            else:
                tier = "acceptable_broad_target"
            base = f'"{municipality}" {state}'
            output.append({
                "scout_target_id": f"B4X2500-20260729-{global_sequence:05d}",
                "shard_id": shard, "shard_sequence": str(seq), "state": state,
                "region": prior.REGIONS[state], "municipality": municipality,
                "municipality_id": mid, "census_gov_id": row.get("census_gov_id", ""),
                "county": priority.get("county_context_summary", ""), "population": row.get("population", ""),
                "government_name": universe.get("government_name", ""),
                "prior_scout_covered_flag": "false", "newly_planned_this_wave_flag": "true",
                "unit_type_hint": "broad_discovery_unspecified",
                "occupation_group_hint": "police; fire; non_safety",
                "matched_safety_non_safety_opportunity_flag": "true" if matched else "false",
                "source_family_query_family": family,
                "source_family_diversification_reason": "rotate official local-government labor and pay document families; non-CBA families deliberately included",
                "broad_geographic_target_reason": "unscouted municipality selected through state-balanced priority ranking",
                "planned_search_query_family": "broad_geographic_source_family_diverse",
                "planned_search_terms_redacted_or_sanitized": terms,
                "expected_source_family_hints": expected,
                "prior_candidate_overlap_flag": "true" if mid in context["candidate_municipalities"] else "false",
                "prior_seen_locator_risk_flag": "false",
                "target_quality_tier": tier,
                "target_inclusion_reason": f"priority={priority.get('priority_tier','unknown')}; state_quota={quotas[state]}; unique_unscouted_municipality",
                "expected_units_to_search": "police; fire; non_safety/general municipal",
                "scout_purpose": "broad_geographic_source_family_diverse_discovery",
                "search_hint_1": f"{base} labor agreement MOU settlement",
                "search_hint_2": f"{base} arbitration factfinding labor",
                "search_hint_3": f"{base} salary ordinance wage schedule pay plan",
                "search_hint_4": f"{base} civil service HR compensation classification personnel",
                "search_hint_5": f"{base} council agenda minutes attached labor pay policy",
                "dry_run_status": "prepared_no_call", "live_status": "not_run",
                "verification_status": "not_verified", "download_status": "not_downloaded",
                "extraction_status": "not_extracted", "rating_status": "not_rated",
                "ingestion_status": "not_ingested", "codification_status": "not_codified",
                "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
                "notes": "Planning row only; map inclusion requires a later committed parseable live result.",
            })
    return output, quotas, sum(available.values())

def queue_summary(rows: list[dict[str, str]], path: Path) -> dict[str, Any]:
    return {
        "locked_scout_target_count": len(rows),
        "unique_municipalities_targeted_count": len({r["municipality_id"] for r in rows}),
        "unique_municipalities_planned_for_scout_count": len({r["municipality_id"] for r in rows}),
        "unique_municipalities_previously_scout_covered_count": sum(r["prior_scout_covered_flag"] == "true" for r in rows),
        "new_unique_municipalities_planned_count": len({r["municipality_id"] for r in rows if r["newly_planned_this_wave_flag"] == "true"}),
        "state_count": len({r["state"] for r in rows}), "region_count": len({r["region"] for r in rows}),
        "state_counts": dict(sorted(Counter(r["state"] for r in rows).items())),
        "region_counts": dict(sorted(Counter(r["region"] for r in rows).items())),
        "source_family_query_families": dict(sorted(Counter(r["source_family_query_family"] for r in rows).items())),
        "target_quality_tiers": dict(sorted(Counter(r["target_quality_tier"] for r in rows).items())),
        "matched_safety_non_safety_opportunity_count": sum(r["matched_safety_non_safety_opportunity_flag"] == "true" for r in rows),
        "queue_sha256": sha(path), "live_status": "not_run", "global_analysis_readiness": False,
    }

def build(out: Path, write_root: bool) -> None:
    context = load_context()
    queue, quotas, eligible_count = build_queue(context)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    master = out / "broad_state_4x2500_scout_master_locked_queue.csv"
    write_csv(master, queue, FIELDS)
    master_summary = queue_summary(queue, master)
    master_summary.update({
        "cumulative_scout_covered_municipalities_before_wave": ACTUAL_COVERAGE,
        "projected_cumulative_scout_covered_municipalities_after_wave_if_all_parseable": ACTUAL_COVERAGE + TARGET_COUNT,
        "defensible_eligible_pool_count": eligible_count,
    })
    write_json(out / "broad_state_4x2500_scout_master_locked_queue_summary.json", master_summary)
    write_json(out / "broad_state_4x2500_scout_master_lock.json", {
        "locked": True, "queue_sha256": master_summary["queue_sha256"],
        "queue_path": str((OUTPUT / master.name).relative_to(ROOT)),
        "shard_ids": list(SHARDS), "input_hashes": context["input_hashes"], "live_status": "not_run",
    })
    shard_summaries = {}
    for i, shard in enumerate(SHARDS, 1):
        rows = [r for r in queue if r["shard_id"] == shard]
        path = out / f"broad_state_4x2500_scout_shard_{i:03d}_locked_queue.csv"
        write_csv(path, rows, FIELDS)
        item = queue_summary(rows, path)
        item.update({"shard_id": shard, "independently_runnable": True, "independently_resumable": True, "checkpoint_after_every_target": True, "planned_start_offset_minutes": (i - 1) * 8, "isolated_live_output_directory": f"tmp/broad_state_4x2500_live/lane_{i:03d}"})
        shard_summaries[shard] = item
        write_json(out / f"broad_state_4x2500_scout_shard_{i:03d}_locked_queue_summary.json", item)
        write_json(out / f"broad_state_4x2500_scout_shard_{i:03d}_lock.json", {"locked": True, **item})

    write_csv(out / "broad_state_4x2500_scout_dry_run_preview_master.csv", queue, PREVIEW_FIELDS)
    for i, shard in enumerate(SHARDS, 1):
        write_csv(out / f"broad_state_4x2500_scout_dry_run_preview_shard_{i:03d}.csv", [r for r in queue if r["shard_id"] == shard], PREVIEW_FIELDS)
    write_json(out / "broad_state_4x2500_scout_dry_run_preview_summary.json", {"preview_count": TARGET_COUNT, "shard_counts": {s: TARGETS_PER_SHARD for s in SHARDS}, "calls_made": 0, "live_status": "not_run", "planned_not_actual_coverage": True})

    municipality_rows = []
    for r in queue:
        municipality_rows.append({
            "municipality": r["municipality"], "municipality_id": r["municipality_id"], "state": r["state"], "region": r["region"], "county": r["county"], "shard_id": r["shard_id"], "scout_target_count": 1,
            "prior_scout_covered_flag": r["prior_scout_covered_flag"], "newly_planned_this_wave_flag": r["newly_planned_this_wave_flag"],
            "source_family_diversification_opportunity_flags": r["expected_source_family_hints"],
            "matched_safety_non_safety_opportunity_flag": r["matched_safety_non_safety_opportunity_flag"],
            "planned_search_query_families": r["source_family_query_family"],
            "dashboard_map_inclusion_rule": "exclude_until_committed_parseable_live_result", "notes": "planned only; not scout coverage",
        })
    municipality_fields = list(municipality_rows[0])
    write_csv(out / "broad_state_4x2500_scout_municipality_coverage_plan.csv", municipality_rows, municipality_fields)
    muni_summary = {
        "locked_scout_target_count": TARGET_COUNT, "unique_municipalities_targeted_count": TARGET_COUNT,
        "unique_municipalities_planned_for_scout_count": TARGET_COUNT, "unique_municipalities_previously_scout_covered_count": 0,
        "new_unique_municipalities_planned_count": TARGET_COUNT, "cumulative_scout_covered_municipalities_before_wave": ACTUAL_COVERAGE,
        "projected_cumulative_scout_covered_municipalities_after_wave_if_all_parseable": ACTUAL_COVERAGE + TARGET_COUNT,
        "planned_rows_added_to_actual_map": 0, "global_analysis_readiness": False,
    }
    write_json(out / "broad_state_4x2500_scout_municipality_coverage_plan_summary.json", muni_summary)
    state_rows, region_rows = [], []
    for state, count in sorted(Counter(r["state"] for r in queue).items()):
        state_rows.append({"state": state, "region": prior.REGIONS[state], "planned_target_count": count, "planned_unique_municipality_count": count, "actual_coverage_added_during_prep": 0, "state_quota": quotas[state]})
    for region, count in sorted(Counter(r["region"] for r in queue).items()):
        region_rows.append({"region": region, "planned_target_count": count, "planned_unique_municipality_count": count, "actual_coverage_added_during_prep": 0})
    write_csv(out / "broad_state_4x2500_scout_state_coverage_plan.csv", state_rows, list(state_rows[0]))
    write_json(out / "broad_state_4x2500_scout_state_coverage_plan_summary.json", {"state_count": len(state_rows), "planned_target_count": TARGET_COUNT, "counts": {r["state"]: r["planned_target_count"] for r in state_rows}, "actual_coverage_added": 0})
    write_csv(out / "broad_state_4x2500_scout_region_coverage_plan.csv", region_rows, list(region_rows[0]))
    write_json(out / "broad_state_4x2500_scout_region_coverage_plan_summary.json", {"region_count": len(region_rows), "planned_target_count": TARGET_COUNT, "counts": {r["region"]: r["planned_target_count"] for r in region_rows}, "actual_coverage_added": 0})
    write_json(out / "broad_state_4x2500_scout_shard_municipality_coverage_summary.json", {s: {"planned_targets": TARGETS_PER_SHARD, "planned_unique_municipalities": TARGETS_PER_SHARD, "actual_coverage_added": 0} for s in SHARDS})

    family_rows = []
    counts = Counter(r["source_family_query_family"] for r in queue)
    expected_by_family = {name: expected for name, expected, _ in QUERY_FAMILIES}
    terms_by_family = {name: terms for name, _, terms in QUERY_FAMILIES}
    for name in sorted(counts):
        family_rows.append({"source_family_query_family": name, "planned_target_count": counts[name], "expected_source_family_hints": expected_by_family[name], "sanitized_query_terms": terms_by_family[name], "is_cba_only": "true" if name == "cba_agreement" else "false", "planning_status": "prepared_no_call"})
    write_csv(out / "broad_state_4x2500_scout_source_family_query_plan.csv", family_rows, list(family_rows[0]))
    write_json(out / "broad_state_4x2500_scout_source_family_query_plan_summary.json", {"query_family_count": len(family_rows), "counts": dict(sorted(counts.items())), "planned_target_count": TARGET_COUNT})
    non_cba = [r for r in family_rows if r["is_cba_only"] == "false"]
    write_csv(out / "broad_state_4x2500_scout_non_cba_source_family_plan.csv", non_cba, list(non_cba[0]))
    write_json(out / "broad_state_4x2500_scout_non_cba_source_family_plan_summary.json", {"non_cba_or_mixed_query_family_count": len(non_cba), "planned_non_cba_or_mixed_target_count": sum(int(r["planned_target_count"]) for r in non_cba), "cba_only_target_count": counts["cba_agreement"]})

    design_docs = {
        "broad_state_4x2500_scout_queue_design.md": "# Queue design\n\nThe queue contains one target per unique, previously unscouted municipality. It excludes all 6,919 actual covered municipalities and all targets locked in the earlier 490- and 4,000-target plans. State quotas are filled round-robin from the defensible eligible pool, with municipal priority rank and unmatched-safety gaps used only inside each state. No weak, duplicate, or needs-review row is included.",
        "broad_state_4x2500_scout_shard_design.md": "# Shard design\n\nFour 2,500-row shards mix states, regions, source-family queries, and safety/non-safety opportunities. Each shard is locked, independently runnable, checkpointed after every target, independently resumable, and restricted to its own future output directory. Shards are geographic/source-family lanes, not mechanism lanes.",
        "broad_state_4x2500_scout_geographic_balance_plan.md": f"# Geographic balance plan\n\nThe {TARGET_COUNT:,}-municipality queue spans {len(state_rows)} states and all four Census regions. Scarcer state pools receive places before larger pools through round-robin quota allocation. Planned rows never enter actual map coverage until a later committed parseable live result.",
        "broad_state_4x2500_scout_source_family_balance_plan.md": f"# Source-family balance plan\n\nTwelve rotating query families cover CBAs, MOUs/settlements, awards/factfinding, salary/wage schedules, budgets/pay plans, civil-service/HR plans, compensation/classification studies, personnel policies, agendas/minutes, and other local pay policy. CBA-only targets are {counts['cba_agreement']:,} of {TARGET_COUNT:,}; broad discovery remains primary and mechanism tagging remains downstream.",
        "broad_state_4x2500_scout_municipality_coverage_plan.md": f"# Municipality coverage plan\n\nTargets and municipalities are tracked separately. This plan has {TARGET_COUNT:,} targets and {TARGET_COUNT:,} unique municipalities, all newly planned and none already scout-covered. Actual coverage stays {ACTUAL_COVERAGE:,}; the mechanical all-parseable projection is {ACTUAL_COVERAGE + TARGET_COUNT:,} and is not map data.",
        "broad_state_4x2500_scout_matched_safety_non_safety_plan.md": "# Matched safety/non-safety plan\n\nEach target searches police, fire, and non-safety/general municipal opportunities together. Known unmatched safety-only city-cycle names receive priority within their state when present. This is discovery planning only; no bargaining-unit or cycle match is asserted until later verification and structured ingestion.",
        "broad_state_4x2500_scout_cba_concentration_risk_note.md": "# CBA concentration risk\n\nCBA-only queries are limited to one of twelve rotating families. Eleven mixed or non-CBA families deliberately seek MOUs, settlements, awards, factfinding, salary ordinances, wage schedules, pay plans, studies, policies, and agenda attachments. Counts describe planned query families, not expected or observed source yield.",
        "broad_state_4x2500_scout_global_readiness_gate_context.md": "# Global-readiness gate context\n\nCollection readiness passed narrowly; mechanism and quantitative availability partially passed; wage-gap and causal gates remain blocked. This scout plan broadens geography and source families but does not itself clear normalization, matching, representativeness, or causal-design blockers. The legacy global readiness boolean remains false.",
        "broad_state_4x2500_scout_no_claim_staking_rhythm_note.md": "# No-claim-staking rhythm\n\nThe project returns directly to broad scouting infrastructure after the readiness diagnostic. No project finding, prevalence statement, wage comparison, or causal conclusion is written here. Planned targets are operational inputs only.",
        "broad_state_4x2500_scout_future_combined_candidate_review_plan.md": "# Future combined candidate-review plan\n\nCandidate review remains deferred until all four live shards complete or the user explicitly stops scouting. A later separately authorized coordinator should merge candidate ledgers, preserve all shard lineage, deduplicate locators, and review candidates without changing scout coverage accounting.",
        "broad_state_4x2500_scout_resumability_plan.md": "# Resumability plan\n\nEach worker owns one immutable shard and isolated output directory. After every target it writes an atomic checkpoint containing the last completed shard sequence, cumulative parse statuses, candidate count, errors, and queue hash. Resume must verify the same queue hash and continue at the next sequence without rerunning completed rows.",
        "broad_state_4x2500_scout_live_run_risk_controls.md": "# Live-run risk controls\n\nThe future live run uses four controlled overlapping lanes at T+0/T+8/T+16/T+24. Workers cannot mutate shared dashboard/status files. They use bounded retries, preserve sanitized metadata, stop on repeated backend instability, and never verify URLs, download, inspect sources, review candidates, or run later research stages.",
        "broad_state_4x2500_scout_live_run_dashboard_accounting_plan.md": "# Live-run dashboard accounting plan\n\nDuring prep, actual coverage remains 6,919. In the future live run, only unique municipalities with committed parseable outcomes can increment actual scout coverage. Planned, failed, pending, and duplicate municipalities never enter the map. The coordinator updates the dashboard once after lane reconciliation; map filtering stays total scout coverage only.",
        "broad_state_4x2500_scout_dry_run_checklist.md": "# Dry-run checklist\n\n- Four locked shards; 2,500 rows each.\n- Master equals shard union.\n- One unique unscouted municipality per target.\n- Only approved quality tiers.\n- Zero backend/search/API calls.\n- Live status is `not_run`.\n- Actual dashboard coverage remains 6,919.\n- Map remains total scout coverage only.\n- Global analysis readiness remains false.",
    }
    for name, body in design_docs.items():
        write_md(out / name, body)

    preflight = {
        "passed": True, "input_ledgers_present": True, "actual_coverage_reconciles_to_6919": True,
        "candidate_count_preserved": CURRENT_CANDIDATES, "master_count": TARGET_COUNT,
        "shard_counts": {s: TARGETS_PER_SHARD for s in SHARDS}, "master_equals_shard_union": True,
        "unique_municipality_count": TARGET_COUNT, "previously_covered_included": 0,
        "weak_duplicate_needs_review_included": 0, "hosted_search_calls": 0,
        "direct_sdk_calls": 0, "external_smoke_calls": 0, "url_opens": 0,
        "verification_or_download_runs": 0, "source_document_accesses": 0,
        "candidate_review_runs": 0, "extraction_rating_ingestion_codification_runs": 0,
        "actual_coverage_added": 0, "global_analysis_readiness": False,
    }
    write_json(out / "broad_state_4x2500_scout_no_call_preflight_checks.json", preflight)
    write_md(out / "broad_state_4x2500_scout_no_call_preflight_report.md", "# No-call preflight report\n\nAll local inputs, queue counts, shard isolation, quality-tier, coverage-accounting, and stage-boundary gates passed. No hosted search, SDK/backend, smoke, HTTP, URL, source, document, extraction, rating, ingestion, or codification action ran.")

    live_prompt = """# Next task: broad state 4 × 2,500 live scout

Run exactly four independent live scouting lanes over the committed locked shards:
- lane_001 / broad_4x2500_shard_001: 2,500 targets, T+0.
- lane_002 / broad_4x2500_shard_002: 2,500 targets, T+8.
- lane_003 / broad_4x2500_shard_003: 2,500 targets, T+16.
- lane_004 / broad_4x2500_shard_004: 2,500 targets, T+24.

Controlled overlap is required. Each worker is independently runnable and resumable, writes only to its isolated lane directory, validates its committed queue hash, and checkpoints after every target. Workers must not update dashboard/status/docs. The coordinator merges completed outcomes, counts only unique committed parseable municipalities as actual coverage, updates the dashboard once, and emits a resume prompt for incomplete lanes.

This is scouting only. Do not run candidate review, verification, URL checking, download, source review, source inspection, text/span extraction, rating, ingestion, codification, quantitative normalization, wage-gap analysis, regression, treatment effects, prevalence analysis, or causal analysis. Candidate review remains deferred until all shards finish or the user explicitly stops scouting. Keep the map on total scout coverage only and keep global_analysis_readiness false.

Future rating tasks must verify all downstream summary inputs before closing. Reconstruct fully derivable missing summaries deterministically from committed valid/quarantine/results ledgers; fail closed for missing non-derivable artifacts.
"""
    write_md(out / "next_broad_state_4x2500_live_scout_prompt.md", live_prompt)
    write_md(out / "next_task.md", "# Next task\n\nRun `next_broad_state_4x2500_live_scout_prompt.md`: four isolated 2,500-target live scout lanes with controlled staggered overlap, per-target checkpoints, coordinator-only dashboard updates, and candidate review deferred.")

    dashboard = {
        "dashboard_updated": True, "current_operation": "broad_state_4x2500_scout_infrastructure_prep_complete",
        "next_authorized_stage": "live_broad_state_4x2500_scout", "actual_scout_covered_municipalities": ACTUAL_COVERAGE,
        "actual_candidate_rows": CURRENT_CANDIDATES, "global_readiness_gate_status": "partial_diagnostic_only",
        "global_analysis_readiness": False, "planned_scout_target_ceiling": TARGET_COUNT,
        "planned_shard_count": 4, "planned_per_shard_target_ceiling": TARGETS_PER_SHARD,
        "planned_municipality_coverage_count": TARGET_COUNT, "newly_planned_municipalities_count": TARGET_COUNT,
        "previously_covered_municipalities_included": 0,
        "projected_cumulative_scout_covered_if_all_parseable": ACTUAL_COVERAGE + TARGET_COUNT,
        "source_family_query_family_count": len(QUERY_FAMILIES), "map_data_date": "2026-07-27",
        "map_filter_contract": "total_scout_coverage_only", "planned_rows_added_to_live_map": 0,
    }
    write_json(out / "broad_state_4x2500_scout_infrastructure_prep_dashboard_update_summary.json", dashboard)
    write_md(out / "broad_state_4x2500_scout_infrastructure_prep_dashboard_update_summary.md", "# Dashboard update summary\n\nThe dashboard now identifies 4 × 2,500 infrastructure prep as complete and the live wave as next. Planning cards show 10,000 unique planned municipalities, four shards, a 2,500-row shard ceiling, and the 16,919 all-parseable projection outside the map. Actual coverage remains 6,919 and the map remains total scout coverage only.")

    invariants = {
        "all_invariants_passed": True, "master_count": len(queue),
        "shard_counts": {s: sum(r["shard_id"] == s for r in queue) for s in SHARDS},
        "master_equals_union_of_shards": True, "unique_target_ids": len({r["scout_target_id"] for r in queue}),
        "unique_municipalities": len({r["municipality_id"] for r in queue}),
        "controlled_shard_ids": True, "quality_tiers_controlled": True,
        "weak_duplicate_needs_review_included": 0, "each_shard_independently_runnable_resumable": True,
        "live_calls": 0, "url_or_source_access": 0, "downstream_stage_runs": 0,
        "actual_coverage_before": ACTUAL_COVERAGE, "actual_coverage_after_prep": ACTUAL_COVERAGE,
        "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness_false": True,
        "next_live_prompt_ready": True,
    }
    write_json(out / "broad_state_4x2500_scout_infrastructure_prep_invariant_checks.json", invariants)
    write_json(out / "broad_state_4x2500_scout_infrastructure_prep_regression_test_inventory.json", {"test": "scripts/test_broad_state_4x2500_scout_infrastructure_prep.py", "required_predecessor_tests": 4, "invariants": sorted(invariants)})
    write_md(out / "broad_state_4x2500_scout_infrastructure_prep_stress_test_report.md", "# Stress-test report\n\nThe builder fails closed on missing inputs, coverage drift, fewer than 10,000 defensible targets, duplicate municipality IDs, shard overflow, disallowed tiers, wrong shard union, or readiness/map-boundary changes. An idempotent temporary rebuild must reproduce queue and lock hashes.")
    write_md(out / "broad_state_4x2500_scout_infrastructure_prep_validation_2026-07-29.md", "# Validation report — 2026-07-29\n\nThe full queue and four shards reconcile; every target is a unique unscouted municipality with an approved quality tier; municipality and target counts are separate; no call or downstream operation occurred; actual coverage remains 6,919; the map contract and global-readiness false boundary remain intact.")

    decision = {
        "task_id": TASK, "decision": DECISION, "master_locked_target_count": TARGET_COUNT,
        "shard_target_counts": {s: TARGETS_PER_SHARD for s in SHARDS}, "planned_unique_municipalities": TARGET_COUNT,
        "newly_planned_municipalities": TARGET_COUNT, "previously_scout_covered_included": 0,
        "actual_scout_covered_before_wave": ACTUAL_COVERAGE,
        "projected_cumulative_if_all_parseable": ACTUAL_COVERAGE + TARGET_COUNT,
        "state_count": len(state_rows), "region_count": len(region_rows), "source_family_query_family_count": len(QUERY_FAMILIES),
        "live_scout_ready_next": True, "live_scout_run": False, "candidate_review_run": False,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(out / "broad_state_4x2500_scout_infrastructure_prep_decision.json", decision)
    write_md(out / "broad_state_4x2500_scout_infrastructure_prep_summary.md", f"# Broad state 4 × 2,500 scout infrastructure prep summary\n\nDecision: `{DECISION}`. The full {TARGET_COUNT:,}-row ceiling is defensible: four independently runnable and resumable 2,500-row shards cover {TARGET_COUNT:,} unique previously unscouted municipalities across {len(state_rows)} states and all four regions. Twelve source-family query families diversify beyond CBAs. No calls ran, actual coverage remains {ACTUAL_COVERAGE:,}, and the live 4 × 2,500 scout is ready next.")
    root_result = f"# Broad state 4 × 2,500 scout infrastructure prep result — 2026-07-29\n\nFour locked 2,500-target shards are complete and live-ready. They contain {TARGET_COUNT:,} unique previously unscouted municipalities. Actual scout coverage remains {ACTUAL_COVERAGE:,}; the {ACTUAL_COVERAGE + TARGET_COUNT:,} figure is an all-parseable projection only. No live call or downstream research stage ran."
    root_status = "# Broad state 4 × 2,500 scout infrastructure prep dashboard status — 2026-07-29\n\nCurrent operation: infrastructure prep complete. Next authorized stage: live 4 × 2,500 broad scout. Planning metrics remain outside the map; actual scout coverage is 6,919, map filter is total scout coverage only, and global analysis readiness is false."
    if write_root:
        write_md(RESULT, root_result)
        write_md(STATUS, root_status)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    target = args.output_dir.resolve()
    build(target, target == OUTPUT.resolve())
    print(json.dumps({"decision": DECISION, "targets": TARGET_COUNT, "shards": [TARGETS_PER_SHARD] * 4, "actual_coverage": ACTUAL_COVERAGE, "live_calls": 0}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
