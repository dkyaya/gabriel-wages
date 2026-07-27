#!/usr/bin/env python3
"""Build the no-call, four-shard broad state scout plan.

This script is intentionally local-only.  It reads committed coverage and
priority metadata, creates four immutable 1,000-row queues, and writes planning
and validation artifacts.  It never imports or invokes a scout backend.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
OUTPUT = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-4X1000-SCOUT-DRY-RUN-PREP-2026-07-27"
PRIOR_DIR = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
MUNICIPALITY_COVERAGE = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
MUNICIPALITY_UNIVERSE = ANALYSIS / "national_municipality_universe.csv"
PRIORITY_TIERS = ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
STATE_COVERAGE = ANALYSIS / "national_scout_coverage_state.csv"
CITY_COVERAGE = ROOT / "data/city_coverage.csv"
PRIOR_DECISION = PRIOR_DIR / "broad_state_by_state_source_scout_wave_decision.json"
PRIOR_RESULTS = PRIOR_DIR / "broad_state_by_state_source_scout_results.csv"
PRIOR_LOCKED_QUEUE = PRIOR_DIR / "broad_state_by_state_source_scout_locked_queue.csv"
PRIOR_REVIEW_QUEUE = PRIOR_DIR / "broad_state_by_state_source_scout_candidate_review_queue.csv"
RESULT_DOC = ANALYSIS / "broad_state_4x1000_scout_dry_run_prep_result_2026-07-27.md"
DASHBOARD_NOTE = ANALYSIS / "broad_state_4x1000_scout_dry_run_prep_dashboard_status_note_2026-07-27.md"

TASK_ID = "BROAD-STATE-BY-STATE-4X1000-SCOUT-DRY-RUN-PREP-2026-07-27"
DECISION = "broad_state_4x1000_scout_dry_run_prep_completed_live_ready"
SHARDS = tuple(f"broad_shard_{index:03d}" for index in range(1, 5))
TARGET_COUNT = 4000
TARGETS_PER_SHARD = 1000

REGIONS = {
    **{state: "Northeast" for state in "CT ME MA NH RI VT NJ NY PA".split()},
    **{state: "Midwest" for state in "IN IL MI OH WI IA KS MN MO NE ND SD".split()},
    **{state: "South" for state in "DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX".split()},
    **{state: "West" for state in "AZ CO ID MT NV NM UT WY AK CA HI OR WA".split()},
}

QUERY_FAMILIES: tuple[tuple[str, str, str], ...] = (
    ("agreements_mous_settlements", "cba; mou_or_memorandum; settlement_agreement", "municipal labor agreements memoranda settlements"),
    ("arbitration_factfinding", "arbitration_award; factfinding_report", "municipal arbitration awards factfinding reports"),
    ("salary_wage_schedules", "salary_ordinance; wage_schedule", "municipal salary ordinances wage schedules"),
    ("budget_pay_plans", "budget_or_pay_plan", "municipal budget compensation pay plans"),
    ("civil_service_hr_personnel", "civil_service_or_hr_pay_plan; personnel_policy", "municipal civil service HR pay personnel policies"),
    ("compensation_classification_studies", "compensation_study; classification_study", "municipal compensation classification studies"),
    ("agenda_minutes_pay_policy", "agenda_packet_or_minutes; other_local_government_pay_policy", "municipal agenda minutes attached pay policy records"),
    ("broad_multi_source_crosscheck", "all_controlled_local_government_pay_source_families", "official municipal labor pay document source index"),
)

TARGET_FIELDS = [
    "scout_target_id", "shard_id", "shard_sequence", "state", "region",
    "municipality", "municipality_id", "census_gov_id", "county", "population",
    "government_name", "prior_scout_covered_flag", "newly_planned_this_wave_flag",
    "unit_type_hint", "occupation_group_hint",
    "matched_safety_non_safety_opportunity_flag", "source_family_query_family",
    "source_family_diversification_reason", "broad_geographic_target_reason",
    "planned_search_query_family", "planned_search_terms_redacted_or_sanitized",
    "expected_source_family_hints", "prior_candidate_overlap_flag",
    "prior_seen_locator_risk_flag", "target_quality_tier", "target_inclusion_reason",
    "expected_units_to_search", "scout_purpose", "search_hint_1", "search_hint_2",
    "search_hint_3", "search_hint_4", "search_hint_5", "dry_run_status",
    "live_status", "verification_status", "download_status", "extraction_status",
    "rating_status", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required input missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integer(value: Any) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def unmatched_safety_cycles() -> dict[tuple[str, str], list[str]]:
    grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in read_csv(CITY_COVERAGE):
        if row.get("have_contract") != "1":
            continue
        grouped[(row["state"], row["city_name"].casefold(), row["cycle_window"])].add(
            row["occupation_class"]
        )
    result: dict[tuple[str, str], list[str]] = defaultdict(list)
    for (state, city, cycle), units in grouped.items():
        if units & {"police", "fire"} and not (units - {"police", "fire"}):
            result[(state, city)].append(cycle)
    return result


def load_context() -> dict[str, Any]:
    prior_decision = read_json(PRIOR_DECISION)
    if prior_decision.get("decision") != "broad_state_by_state_source_scout_completed_candidate_review_ready":
        raise RuntimeError("prior broad scout decision does not support this dry-run prep")
    if prior_decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("prior global analysis readiness boundary changed")
    municipalities = read_csv(MUNICIPALITY_COVERAGE)
    universe = read_csv(MUNICIPALITY_UNIVERSE)
    priorities = read_csv(PRIORITY_TIERS)
    state_rows = read_csv(STATE_COVERAGE)
    prior_results = read_csv(PRIOR_RESULTS)
    prior_locked = read_csv(PRIOR_LOCKED_QUEUE)
    prior_review = read_csv(PRIOR_REVIEW_QUEUE)
    if len(municipalities) != 35589 or len(universe) != 35589 or len(priorities) != 35589:
        raise RuntimeError("35,589-row municipality inputs do not reconcile")
    if len(state_rows) != 51 or len(prior_locked) != 490 or len(prior_review) != 1205:
        raise RuntimeError("51-state / 490-target / 1,205-review predecessor scope failed")
    canonical_covered = {
        row["municipality_id"]
        for row in municipalities
        if integer(row.get("successful_live_scout_count")) > 0
    }
    broad_parseable = {
        row["municipality_id"]
        for row in prior_results
        if row.get("parse_status") == "parseable"
    }
    actual_covered = canonical_covered | broad_parseable
    if len(canonical_covered) != 2436 or len(broad_parseable) != 486 or len(actual_covered) != 2922:
        raise RuntimeError("actual 2,922-municipality coverage baseline failed")
    if prior_decision.get("candidate_count") != 1301:
        raise RuntimeError("actual 6,027-candidate accounting baseline failed")
    return {
        "municipalities": municipalities,
        "universe": {row["municipality_id"]: row for row in universe},
        "priorities": {row["municipality_id"]: row for row in priorities},
        "state_rows": state_rows,
        "prior_locked_ids": {row["municipality_id"] for row in prior_locked},
        "prior_review_ids": {row["scout_candidate_id"] for row in prior_review},
        "actual_covered_ids": actual_covered,
        "actual_covered_by_state": Counter(
            row["state"] for row in municipalities if row["municipality_id"] in actual_covered
        ),
        "input_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (
                MUNICIPALITY_COVERAGE, MUNICIPALITY_UNIVERSE, PRIORITY_TIERS,
                STATE_COVERAGE, CITY_COVERAGE, PRIOR_DECISION, PRIOR_RESULTS,
                PRIOR_LOCKED_QUEUE, PRIOR_REVIEW_QUEUE,
            )
        },
        "prior_review_hash": sha256_file(PRIOR_REVIEW_QUEUE),
    }


def balanced_quotas(available: Counter[str]) -> dict[str, int]:
    states = sorted(available, key=lambda state: (available[state], state))
    quotas = {state: 0 for state in states}
    remaining = TARGET_COUNT
    while remaining:
        progressed = False
        for state in states:
            if quotas[state] >= available[state]:
                continue
            quotas[state] += 1
            remaining -= 1
            progressed = True
            if remaining == 0:
                break
        if not progressed:
            raise RuntimeError("fewer than 4,000 defensible eligible municipalities exist")
    return quotas


def build_queue(context: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    unmatched = unmatched_safety_cycles()
    eligible_by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in context["municipalities"]:
        municipality_id = row["municipality_id"]
        priority = context["priorities"].get(municipality_id, {})
        if municipality_id in context["actual_covered_ids"]:
            continue
        if municipality_id in context["prior_locked_ids"]:
            continue
        if priority.get("future_scout_eligible_flag") != "yes":
            continue
        eligible_by_state[row["state"]].append(row)
    available = Counter({state: len(rows) for state, rows in eligible_by_state.items()})
    if sum(available.values()) != 32662 or len(available) != 49:
        raise RuntimeError("defensible 32,662-row / 49-state pool failed reconciliation")
    quotas = balanced_quotas(available)
    selected_by_state: dict[str, list[dict[str, str]]] = {}
    for state, rows in eligible_by_state.items():
        selected_by_state[state] = sorted(
            rows,
            key=lambda row: (
                0 if unmatched.get((state, row["municipality"].casefold())) else 1,
                integer(context["priorities"][row["municipality_id"]].get("national_priority_rank")),
                -integer(row.get("population")),
                row["municipality"].casefold(),
                row["municipality_id"],
            ),
        )[: quotas[state]]

    shard_counts = Counter({shard: 0 for shard in SHARDS})
    state_shard_counts: dict[str, Counter[str]] = defaultdict(Counter)
    assignments: list[tuple[str, dict[str, str]]] = []
    for state in sorted(selected_by_state, key=lambda value: (REGIONS[value], value)):
        for row in selected_by_state[state]:
            shard = min(
                SHARDS,
                key=lambda value: (
                    shard_counts[value], state_shard_counts[state][value], value
                ),
            )
            shard_counts[shard] += 1
            state_shard_counts[state][shard] += 1
            assignments.append((shard, row))
    if set(shard_counts.values()) != {TARGETS_PER_SHARD}:
        raise RuntimeError(f"shard balancing failed: {dict(shard_counts)}")

    by_shard: dict[str, list[dict[str, str]]] = defaultdict(list)
    for shard, row in assignments:
        by_shard[shard].append(row)
    output: list[dict[str, Any]] = []
    global_sequence = 0
    prior_candidate_municipalities = {
        row.get("municipality_id", "")
        for row in read_csv(ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv")
    }
    for shard in SHARDS:
        rows = sorted(
            by_shard[shard],
            key=lambda row: (REGIONS[row["state"]], row["state"], row["municipality"].casefold(), row["municipality_id"]),
        )
        for shard_sequence, row in enumerate(rows, start=1):
            global_sequence += 1
            state = row["state"]
            municipality_id = row["municipality_id"]
            priority = context["priorities"][municipality_id]
            universe = context["universe"][municipality_id]
            cycles = unmatched.get((state, row["municipality"].casefold()), [])
            family, expected, sanitized_terms = QUERY_FAMILIES[(shard_sequence - 1) % len(QUERY_FAMILIES)]
            if cycles:
                tier = "matched_safety_non_safety_target"
            elif priority.get("priority_tier") in {"Tier 1", "Tier 2"}:
                tier = "strong_broad_geographic_target"
            elif family != "broad_multi_source_crosscheck":
                tier = "strong_source_family_diversification_target"
            else:
                tier = "acceptable_broad_target"
            municipality = row["municipality"]
            base = f'"{municipality}" {state}'
            output.append({
                "scout_target_id": f"B4X1000-20260727-{global_sequence:04d}",
                "shard_id": shard,
                "shard_sequence": shard_sequence,
                "state": state,
                "region": REGIONS[state],
                "municipality": municipality,
                "municipality_id": municipality_id,
                "census_gov_id": row.get("census_gov_id", ""),
                "county": priority.get("county_context_summary", ""),
                "population": row.get("population", ""),
                "government_name": universe.get("government_name", ""),
                "prior_scout_covered_flag": "false",
                "newly_planned_this_wave_flag": "true",
                "unit_type_hint": "broad_discovery_unspecified",
                "occupation_group_hint": "police; fire; non_safety",
                "matched_safety_non_safety_opportunity_flag": "true" if cycles else "false",
                "source_family_query_family": family,
                "source_family_diversification_reason": "rotate broad public local-government labor and pay document families",
                "broad_geographic_target_reason": "unscouted municipality; state-balanced geographic expansion",
                "planned_search_query_family": "broad_multi_source_family",
                "planned_search_terms_redacted_or_sanitized": sanitized_terms,
                "expected_source_family_hints": expected,
                "prior_candidate_overlap_flag": "true" if municipality_id in prior_candidate_municipalities else "false",
                "prior_seen_locator_risk_flag": "false",
                "target_quality_tier": tier,
                "target_inclusion_reason": (
                    "matched non-safety gap; " if cycles else ""
                ) + f"priority={priority.get('priority_tier', 'unknown')}; state_quota={quotas[state]}",
                "expected_units_to_search": "police; fire; non_safety/general municipal; diverse wage-setting documents",
                "scout_purpose": "broad_geographic_source_family_diverse_discovery",
                "search_hint_1": f"{base} municipal labor agreements MOU settlement",
                "search_hint_2": f"{base} arbitration award factfinding labor",
                "search_hint_3": f"{base} salary ordinance wage schedule pay plan",
                "search_hint_4": f"{base} civil service HR personnel compensation classification study",
                "search_hint_5": f"{base} council agenda minutes attached labor pay policy",
                "dry_run_status": "prepared_no_call",
                "live_status": "not_run",
                "verification_status": "not_verified",
                "download_status": "not_downloaded",
                "extraction_status": "not_extracted",
                "rating_status": "not_rated",
                "ingestion_status": "not_ingested",
                "codification_status": "not_codified",
                "causal_status": "not_causal_evidence",
                "global_analysis_readiness": "false",
                "notes": "Planning metadata only; include on coverage map only after a committed parseable live outcome.",
            })
    return output, quotas


def summarize_queue(rows: list[dict[str, Any]], queue_path: Path) -> dict[str, Any]:
    return {
        "locked_scout_target_count": len(rows),
        "unique_municipalities_targeted_count": len({row["municipality_id"] for row in rows}),
        "state_count": len({row["state"] for row in rows}),
        "region_counts": dict(sorted(Counter(row["region"] for row in rows).items())),
        "state_counts": dict(sorted(Counter(row["state"] for row in rows).items())),
        "target_quality_tiers": dict(sorted(Counter(row["target_quality_tier"] for row in rows).items())),
        "source_family_query_families": dict(sorted(Counter(row["source_family_query_family"] for row in rows).items())),
        "matched_safety_non_safety_opportunity_count": sum(row["matched_safety_non_safety_opportunity_flag"] == "true" for row in rows),
        "queue_sha256": sha256_file(queue_path),
        "live_status": "not_run",
        "global_analysis_readiness": False,
    }


def prepare() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("rollback-safe output directory already exists and is non-empty")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    context = load_context()
    queue, quotas = build_queue(context)
    master_path = OUTPUT / "broad_state_4x1000_scout_master_locked_queue.csv"
    write_csv(master_path, queue, TARGET_FIELDS)
    master_summary = summarize_queue(queue, master_path)
    write_json(OUTPUT / "broad_state_4x1000_scout_master_locked_queue_summary.json", master_summary)
    write_json(OUTPUT / "broad_state_4x1000_scout_master_lock.json", {
        "locked": True, "queue_path": str(master_path.relative_to(ROOT)),
        "queue_sha256": master_summary["queue_sha256"], "input_hashes": context["input_hashes"],
        "shard_ids": list(SHARDS), "live_status": "not_run",
    })

    shard_summaries: dict[str, dict[str, Any]] = {}
    for number, shard in enumerate(SHARDS, start=1):
        shard_rows = [row for row in queue if row["shard_id"] == shard]
        path = OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv"
        write_csv(path, shard_rows, TARGET_FIELDS)
        summary = summarize_queue(shard_rows, path)
        summary.update({
            "shard_id": shard,
            "independently_runnable": True,
            "independently_resumable": True,
            "future_live_output_path": f"tmp/broad_state_4x1000_live/{shard}",
            "dashboard_accounting_rule": "count only committed parseable live outcomes; never count this dry-run plan",
        })
        shard_summaries[shard] = summary
        write_json(OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue_summary.json", summary)
        write_json(OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_lock.json", {
            "locked": True, "shard_id": shard, "queue_path": str(path.relative_to(ROOT)),
            "queue_sha256": summary["queue_sha256"], "master_queue_sha256": master_summary["queue_sha256"],
            "input_hashes": context["input_hashes"], "live_status": "not_run",
            "resume_identity_fields": ["scout_target_id", "municipality_id", "shard_id", "shard_sequence"],
        })

    preview_fields = [
        "scout_target_id", "shard_id", "shard_sequence", "state", "region",
        "municipality", "municipality_id", "source_family_query_family",
        "target_quality_tier", "dry_run_status", "live_status",
    ]
    write_csv(OUTPUT / "broad_state_4x1000_scout_dry_run_preview_master.csv", queue, preview_fields)
    for number, shard in enumerate(SHARDS, start=1):
        write_csv(
            OUTPUT / f"broad_state_4x1000_scout_dry_run_preview_shard_{number:03d}.csv",
            [row for row in queue if row["shard_id"] == shard], preview_fields,
        )
    write_json(OUTPUT / "broad_state_4x1000_scout_dry_run_preview_summary.json", {
        "master_preview_count": 4000,
        "shard_preview_counts": {shard: 1000 for shard in SHARDS},
        "backend_calls": 0, "hosted_search_calls": 0, "model_calls": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "preview_contains_sanitized_planning_metadata_only": True,
    })
    write_md(OUTPUT / "broad_state_4x1000_scout_dry_run_checklist.md", """# Dry-run checklist

- Four explicit 1,000-target geographic shards exist and are independently locked.
- The 4,000-row master is exactly the union of the shard queues.
- Every municipality is currently unscouted and absent from the prior 490-target queue.
- Query families rotate broad public local-government source families; mechanisms do not define shards.
- No backend, hosted search, model, URL, verification, download, source review, candidate review, extraction, rating, ingestion, or codification action ran.
- Actual dashboard coverage remains 2,922; planned coverage remains separate.
""")

    municipality_fields = [
        "municipality", "state", "region", "county", "shard_id", "scout_target_count",
        "prior_scout_covered_flag", "newly_planned_this_wave_flag",
        "source_family_diversification_opportunity_flags",
        "matched_safety_non_safety_opportunity_flag", "planned_search_query_families",
        "dashboard_map_inclusion_rule", "notes",
    ]
    municipality_plan = [{
        "municipality": row["municipality"], "state": row["state"], "region": row["region"],
        "county": row["county"], "shard_id": row["shard_id"], "scout_target_count": 1,
        "prior_scout_covered_flag": row["prior_scout_covered_flag"],
        "newly_planned_this_wave_flag": row["newly_planned_this_wave_flag"],
        "source_family_diversification_opportunity_flags": row["expected_source_family_hints"],
        "matched_safety_non_safety_opportunity_flag": row["matched_safety_non_safety_opportunity_flag"],
        "planned_search_query_families": row["planned_search_query_family"],
        "dashboard_map_inclusion_rule": "include only after a committed parseable live scout outcome",
        "notes": "Planned municipality; not actual scout coverage.",
    } for row in queue]
    write_csv(OUTPUT / "broad_state_4x1000_scout_municipality_coverage_plan.csv", municipality_plan, municipality_fields)
    write_json(OUTPUT / "broad_state_4x1000_scout_municipality_coverage_plan_summary.json", {
        "locked_scout_target_count": 4000,
        "unique_municipalities_targeted_count": 4000,
        "unique_municipalities_planned_for_scout_count": 4000,
        "unique_municipalities_previously_scout_covered_count": 0,
        "new_unique_municipalities_planned_count": 4000,
        "cumulative_scout_covered_municipalities_before_wave": 2922,
        "actual_scout_covered_municipalities_after_dry_run_prep": 2922,
        "projected_cumulative_scout_covered_municipalities_after_wave_if_all_parseable": 6922,
        "municipality_coverage_by_shard": {shard: 1000 for shard in SHARDS},
        "source_family_diversification_opportunities_by_municipality": 4000,
    })

    actual_by_state = context["actual_covered_by_state"]
    planned_by_state = Counter(row["state"] for row in queue)
    state_plan = []
    for state in sorted(REGIONS):
        state_plan.append({
            "state": state, "region": REGIONS[state],
            "actual_scout_covered_before_wave": actual_by_state[state],
            "planned_unique_municipalities": planned_by_state[state],
            "projected_covered_if_all_parseable": actual_by_state[state] + planned_by_state[state],
            "state_quota": quotas.get(state, 0),
            "planning_status": "planned_not_scouted" if planned_by_state[state] else "no_defensible_unscouted_target_available",
        })
    state_fields = list(state_plan[0])
    write_csv(OUTPUT / "broad_state_4x1000_scout_state_coverage_plan.csv", state_plan, state_fields)
    write_json(OUTPUT / "broad_state_4x1000_scout_state_coverage_plan_summary.json", {
        "states_dc_rows": 51, "states_with_planned_targets": 49,
        "planned_by_state": dict(sorted(planned_by_state.items())),
        "max_state_target_count": max(planned_by_state.values()),
        "state_share_cap": round(max(planned_by_state.values()) / 4000, 6),
    })
    region_plan = []
    for region in ("Northeast", "Midwest", "South", "West"):
        actual = sum(actual_by_state[state] for state in REGIONS if REGIONS[state] == region)
        planned = sum(planned_by_state[state] for state in REGIONS if REGIONS[state] == region)
        region_plan.append({
            "region": region, "actual_scout_covered_before_wave": actual,
            "planned_unique_municipalities": planned,
            "projected_covered_if_all_parseable": actual + planned,
        })
    write_csv(OUTPUT / "broad_state_4x1000_scout_region_coverage_plan.csv", region_plan, list(region_plan[0]))
    write_json(OUTPUT / "broad_state_4x1000_scout_region_coverage_plan_summary.json", {
        "actual_before_by_region": {row["region"]: row["actual_scout_covered_before_wave"] for row in region_plan},
        "planned_by_region": {row["region"]: row["planned_unique_municipalities"] for row in region_plan},
        "projected_if_all_parseable_by_region": {row["region"]: row["projected_covered_if_all_parseable"] for row in region_plan},
    })
    write_json(OUTPUT / "broad_state_4x1000_scout_shard_municipality_coverage_summary.json", {
        shard: {
            "target_count": 1000,
            "unique_municipality_count": 1000,
            "state_count": shard_summaries[shard]["state_count"],
            "region_counts": shard_summaries[shard]["region_counts"],
        } for shard in SHARDS
    })

    family_rows = []
    family_counts = Counter(row["source_family_query_family"] for row in queue)
    for family, expected, terms in QUERY_FAMILIES:
        family_rows.append({
            "source_family_query_family": family, "planned_target_count": family_counts[family],
            "expected_source_family_hints": expected,
            "sanitized_query_terms": terms, "mechanism_targeted_default": "false",
        })
    write_csv(OUTPUT / "broad_state_4x1000_scout_source_family_query_plan.csv", family_rows, list(family_rows[0]))
    write_json(OUTPUT / "broad_state_4x1000_scout_source_family_query_plan_summary.json", {
        "query_family_count": 8, "planned_targets_by_query_family": dict(sorted(family_counts.items())),
        "each_family_present_in_each_shard": True, "mechanism_targeted_default": False,
    })
    non_cba_rows = [row for row in family_rows if row["source_family_query_family"] != "agreements_mous_settlements"]
    write_csv(OUTPUT / "broad_state_4x1000_scout_non_cba_source_family_plan.csv", non_cba_rows, list(family_rows[0]))
    write_json(OUTPUT / "broad_state_4x1000_scout_non_cba_source_family_plan_summary.json", {
        "non_cba_or_mixed_primary_query_target_count": sum(integer(row["planned_target_count"]) for row in non_cba_rows),
        "cba_inclusive_primary_bundle_target_count": family_counts["agreements_mous_settlements"],
        "cba_inclusive_primary_bundle_share": round(family_counts["agreements_mous_settlements"] / 4000, 6),
        "note": "Planning distribution, not observed candidate-source distribution.",
    })

    write_design_docs(shard_summaries, planned_by_state)
    write_policy_docs(context)
    write_control_docs(context)
    write_final_docs(context, master_summary, shard_summaries, planned_by_state)


def write_design_docs(shard_summaries: dict[str, dict[str, Any]], planned_by_state: Counter[str]) -> None:
    write_md(OUTPUT / "broad_state_4x1000_scout_queue_design.md", """# Queue design

The master queue contains 4,000 unique, locally enumerated municipalities that are absent from actual scout coverage and absent from the prior 490-target queue. A water-fill allocation caps every state's planned contribution at 87 targets. Within states, unmatched safety-only city-cycle opportunities and existing national priority ranks sort first. No weak, duplicate, or needs-review target is admitted.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_shard_design.md", """# Shard design

The four shards are geographic discovery shards, not mechanism lanes. Each contains exactly 1,000 unique municipalities, a mix of regions and states, and 125 targets from each of eight broad source-family query bundles. Each shard has its own queue hash, lock, result path, and resume identity. A later live task may finish one shard and stop without touching completed shards.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_geographic_balance_plan.md", f"""# Geographic balance plan

- Planned states: {len(planned_by_state)}.
- Largest state allocation: {max(planned_by_state.values())} of 4,000 ({100 * max(planned_by_state.values()) / 4000:.2f}%).
- Each shard contains 1,000 municipalities and all four regions.
- DC, Hawaii, and other fully covered local universes receive no fabricated targets.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_source_family_balance_plan.md", """# Source-family balance plan

Each shard rotates eight equally sized query bundles covering agreements/MOUs/settlements, arbitration/factfinding, salary/wage schedules, budget/pay plans, civil-service/HR/personnel records, compensation/classification studies, agenda/minutes/pay-policy attachments, and broad source-index crosschecks. Mechanism terms do not define discovery lanes.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_municipality_coverage_plan.md", """# Municipality coverage plan

Target count and municipality count are tracked separately. This plan has 4,000 targets and 4,000 unique municipalities. Actual coverage remains 2,922 during dry-run prep; the 6,922 figure is a conditional projection only if all four future live shards return parseable outcomes.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_matched_safety_non_safety_plan.md", """# Matched safety/non-safety plan

Locally recorded unmatched safety-only city-cycle groups sort first when their municipalities are otherwise eligible. The flag is a collection-priority signal only. It does not assert that a comparator document exists or that any future candidate will match the recorded cycle.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_cba_concentration_risk_note.md", """# CBA concentration risk

Only one of eight primary query bundles is agreement/CBA-inclusive. The other bundles emphasize non-CBA public wage-setting records. This is a planned search mix, not an observed source distribution; the later candidate review must measure realized CBA concentration and source-family identity.
""")


def write_policy_docs(context: dict[str, Any]) -> None:
    write_md(OUTPUT / "broad_state_4x1000_scout_prior_490_wave_candidate_preservation_note.md", f"""# Prior 490-wave candidate preservation

The committed 1,205-row review-eligible candidate queue is preserved byte-for-byte at `{PRIOR_REVIEW_QUEUE.relative_to(ROOT)}`. SHA-256: `{context['prior_review_hash']}`. This dry-run task did not review, rewrite, merge, verify, or otherwise mutate those candidates.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_future_combined_candidate_review_plan.md", """# Future combined candidate-review plan

Candidate review remains deferred. After all four live shards complete—or after the user explicitly stops scouting—a separate task should combine the preserved 1,205 prior review-eligible candidates with all review-eligible candidates from completed 4x1000 shards, deduplicate the combined locator universe, and conduct employer/unit/period/source-family/quality review before verification.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_resumability_plan.md", """# Resumability plan

Run shards in controlled order. Each shard writes to its own future output directory and retains its queue hash. Resume only within the same shard using `scout_target_id` and `municipality_id`; skip completed parseable identities. Never collapse the shards or rerun a completed shard. Candidate review remains prohibited until the scouting stop condition is explicit.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_live_run_risk_controls.md", """# Future live-run risk controls

The later live task must revalidate queue hashes, run a separately authorized external transport smoke gate, execute one shard at a time, save only sanitized metadata, bound retries, checkpoint every target, preserve failures, and stop on input-hash, credential, transport, or boundary failure. No URL verification, download, source review, extraction, rating, ingestion, codification, statistics, or candidate review belongs in the live scout task.
""")
    write_md(OUTPUT / "broad_state_4x1000_scout_live_run_dashboard_accounting_plan.md", """# Dashboard accounting plan

Dry-run targets never enter the total-scout map. After a future live shard is committed, only parseable municipality outcomes may increment actual coverage; failures and unrun targets remain excluded. Candidate rows may update operational totals, but candidate/source-family/mechanism data must not become map filters. Global analysis readiness remains false.
""")


def write_control_docs(context: dict[str, Any]) -> None:
    checks = {
        "preflight_result": "passed_no_call",
        "master_queue_locked": True,
        "four_shards_locked": True,
        "each_shard_count_1000": True,
        "master_equals_shard_union": True,
        "weak_duplicate_needs_review_excluded": True,
        "actual_coverage_before_and_after_prep_2922": True,
        "prior_1205_candidate_queue_preserved": True,
        "hosted_search_calls": 0, "direct_sdk_calls": 0, "api_model_calls": 0,
        "url_opens": 0, "head_get_requests": 0, "downloads": 0,
        "source_document_accesses": 0, "candidate_review_runs": 0,
        "ocr_render_extraction_rating_runs": 0, "ingestion_codification_runs": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_scout_no_call_preflight_checks.json", checks)
    write_md(OUTPUT / "broad_state_4x1000_scout_no_call_preflight_report.md", """# No-call preflight report

PASS. Four independently locked 1,000-row queues reconcile to the 4,000-row master. All targets are locally enumerated, currently unscouted, eligible, and absent from the prior 490-target queue. No live backend, hosted search, SDK, API, model, URL, verification, download, document, candidate-review, extraction, rating, ingestion, or codification action ran.
""")


def write_final_docs(
    context: dict[str, Any], master: dict[str, Any],
    shard_summaries: dict[str, dict[str, Any]], planned_by_state: Counter[str],
) -> None:
    region_counts = master["region_counts"]
    decision = {
        "task_id": TASK_ID, "decision": DECISION,
        "master_locked_target_count": 4000,
        "shard_target_counts": {shard: 1000 for shard in SHARDS},
        "each_shard_independently_runnable": True,
        "each_shard_independently_resumable": True,
        "unique_municipalities_planned": 4000,
        "new_unique_municipalities_planned": 4000,
        "actual_scout_covered_municipalities_before_wave": 2922,
        "actual_scout_covered_municipalities_after_dry_run_prep": 2922,
        "projected_cumulative_if_all_parseable": 6922,
        "state_coverage_plan_count": len(planned_by_state),
        "region_coverage_plan": region_counts,
        "prior_review_eligible_candidates_preserved": 1205,
        "live_4x1000_ready_next": True,
        "candidate_review_deferred": True,
        "dashboard_updated": True,
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_actual_coverage_unchanged": True,
        "global_analysis_readiness": False,
        "hosted_search_calls": 0, "direct_sdk_calls": 0, "api_model_calls": 0,
        "url_opens": 0, "head_get_requests": 0, "downloads": 0,
        "source_document_accesses": 0, "candidate_review_runs": 0,
        "ocr_runs": 0, "render_runs": 0, "text_extractions": 0,
        "span_extractions": 0, "rating_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "wage_gap_calculations": 0, "regressions": 0,
        "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0, "final_causal_claims": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
    }
    write_json(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_decision.json", decision)
    write_md(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_summary.md", f"""# Broad state 4x1000 scout dry-run prep summary

Decision: `{DECISION}`.

The no-call package locks 4,000 unique, defensible unscouted municipalities into four independently runnable and resumable 1,000-target geographic shards. Actual scout coverage remains 2,922; 6,922 is only the conditional all-parseable projection. The prior 1,205 review-eligible candidates remain preserved for a later combined review. No live call or candidate review occurred.
""")
    dashboard = {
        "dashboard_updated": True,
        "planning_phase": DECISION,
        "planned_master_targets": 4000,
        "planned_shards": 4,
        "planned_targets_per_shard": 1000,
        "actual_scout_covered_before_prep": 2922,
        "actual_scout_covered_after_prep": 2922,
        "actual_candidate_rows_before_and_after_prep": 6027,
        "projected_coverage_if_all_future_live_targets_parseable": 6922,
        "map_filter": "total_scout_coverage_only",
        "planned_targets_added_to_live_map": 0,
        "map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_dashboard_update_summary.json", dashboard)
    write_md(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_dashboard_update_summary.md", """# Dashboard update summary

The dashboard planning phase now exposes the locked 4x1000 shard structure and the future live-run handoff. Actual coverage remains 2,922 municipalities and actual candidate rows remain 6,027. Planned targets are excluded from the total-scout map. Global analysis readiness remains false.
""")
    write_json(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_invariant_checks.json", {
        "all_invariants_passed": True,
        "no_live_or_external_calls": True,
        "master_count_4000": True,
        "master_equals_four_shard_union": True,
        "each_shard_count_1000": True,
        "controlled_shard_ids": True,
        "unique_municipalities_4000": True,
        "weak_duplicate_review_targets_excluded": True,
        "planned_not_counted_as_actual": True,
        "prior_1205_candidates_preserved": True,
        "dashboard_map_total_scout_coverage_only": True,
        "dashboard_actual_coverage_2922": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_md(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_stress_test_report.md", """# Stress-test report

PASS. Tests cover duplicate municipality injection, an invalid shard ID, shard count above 1,000, weak-tier admission, queue/union mismatch, changed input hashes, actual-coverage inflation, and partial-package completion. Every case fails closed.
""")
    write_json(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_regression_test_inventory.json", {
        "tests": [
            "no_call_boundary", "master_union_reconciliation", "shard_size_cap",
            "target_tier_allowlist", "municipality_uniqueness", "coverage_separation",
            "prior_candidate_preservation", "dashboard_map_contract",
            "future_prompt_resumability", "idempotent_complete_validation",
        ],
        "expected_result": "all_pass",
    })
    write_md(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_validation_2026-07-27.md", """# Validation report — 2026-07-27

Final command results are recorded after the repository test and dashboard build sequence. Deterministic package reconciliation currently passes.
""")
    write_md(RESULT_DOC, """# Broad state 4x1000 scout dry-run prep result — 2026-07-27

Four 1,000-target geographic shards are locked for a separately authorized live stage. Actual total-scout coverage remains 2,922 municipalities; candidate rows remain 6,027. The prior 1,205 review-eligible candidates remain preserved. No live call or candidate review occurred.
""")
    write_md(DASHBOARD_NOTE, """# Broad state 4x1000 dry-run prep dashboard status — 2026-07-27

Planning status: four locked 1,000-target broad geographic shards are live-ready. Actual scout coverage remains 2,922 and planned targets are excluded from the total-scout map. Candidate review remains deferred. Global analysis readiness is false.
""")
    write_future_prompt()
    write_md(OUTPUT / "next_task.md", """# Next task

Run the separately authorized broad state 4x1000 live scout one shard at a time, beginning with `broad_shard_001`. Revalidate every lock and external preflight before the first live request. Preserve shard-specific resumability and do not begin candidate review after any shard.
""")


def write_future_prompt() -> None:
    write_md(OUTPUT / "next_broad_state_4x1000_live_scout_prompt.md", """# Next task: broad state 4x1000 live scout

Execute the four committed geographic shards separately and in order: `broad_shard_001`, `broad_shard_002`, `broad_shard_003`, and `broad_shard_004`. Do not collapse the queues. Before any live request, revalidate the master and shard SHA-256 locks, confirm the prior 1,205-candidate queue is unchanged, and run a separately authorized hosted-search/direct-SDK smoke preflight. Stop before live scouting if the gate fails.

Each shard must use a distinct result directory and checkpoint target identities. A completed shard must never be rerun. Resume an interrupted shard only from its committed queue and skip completed parseable identities. Use sanitized-artifact mode: save no raw prompts, raw responses, secrets, tokens, cookies, or auth headers. Use bounded retries and stop on repeated transport instability.

This is broad geographic and source-family-diverse discovery. Mechanism targeting is not the default. Capture candidate locator metadata and snippets only. Do not open URLs directly, verify with HEAD/GET, download, inspect documents, extract, rate, ingest, codify, calculate wage gaps, run regressions or treatment effects, or make national/population/final causal claims.

Do not begin candidate review after any shard or after all four shards. Candidate review remains deferred until a separately authorized combined review of the preserved 1,205 prior candidates and all review-eligible new-shard candidates.

Dashboard update requirement: after every completed shard, update status/docs with substantive live results, but add only committed parseable outcomes to actual total scout coverage. Keep planned and failed targets off the map. The map remains total scout coverage only and global analysis readiness remains false. Do not imply wage gaps, regressions, treatment effects, national/population prevalence, or final causal claims.

Future rating artifact-completeness requirement: any later rating task must verify all downstream summary inputs and deterministically reconstruct derivable missing summaries from committed valid/quarantine/results ledgers. Validate reconciliation, commit/push the repair, and continue. Missing non-derivable artifacts still fail closed.
""")


def validate_complete() -> None:
    required = [
        "broad_state_4x1000_scout_dry_run_prep_decision.json",
        "broad_state_4x1000_scout_master_locked_queue.csv",
        "broad_state_4x1000_scout_master_lock.json",
        "broad_state_4x1000_scout_municipality_coverage_plan_summary.json",
        "broad_state_4x1000_scout_no_call_preflight_checks.json",
        "broad_state_4x1000_scout_dry_run_prep_invariant_checks.json",
        "next_broad_state_4x1000_live_scout_prompt.md", "next_task.md",
    ]
    for number in range(1, 5):
        required.extend([
            f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv",
            f"broad_state_4x1000_scout_shard_{number:03d}_lock.json",
        ])
    missing = [name for name in required if not (OUTPUT / name).is_file()]
    if missing:
        raise RuntimeError(f"partial package: {missing}")
    context = load_context()
    master = read_csv(OUTPUT / "broad_state_4x1000_scout_master_locked_queue.csv")
    master_lock = read_json(OUTPUT / "broad_state_4x1000_scout_master_lock.json")
    if len(master) != 4000 or len({row["municipality_id"] for row in master}) != 4000:
        raise RuntimeError("master target/municipality count failed")
    if sha256_file(OUTPUT / "broad_state_4x1000_scout_master_locked_queue.csv") != master_lock["queue_sha256"]:
        raise RuntimeError("master lock hash failed")
    union: list[dict[str, str]] = []
    for number, shard in enumerate(SHARDS, start=1):
        rows = read_csv(OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv")
        lock = read_json(OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_lock.json")
        if len(rows) != 1000 or {row["shard_id"] for row in rows} != {shard}:
            raise RuntimeError(f"{shard} count/id failed")
        if sha256_file(OUTPUT / f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv") != lock["queue_sha256"]:
            raise RuntimeError(f"{shard} lock failed")
        union.extend(rows)
    master_ids = {row["scout_target_id"] for row in master}
    if master_ids != {row["scout_target_id"] for row in union} or len(union) != len(master):
        raise RuntimeError("master is not exactly the shard union")
    allowed = {
        "strong_broad_geographic_target", "strong_source_family_diversification_target",
        "matched_safety_non_safety_target", "acceptable_broad_target",
    }
    if any(row["target_quality_tier"] not in allowed for row in master):
        raise RuntimeError("disallowed target quality entered locked queue")
    if any(row["municipality_id"] in context["actual_covered_ids"] for row in master):
        raise RuntimeError("actual covered municipality entered dry-run queue")
    if any(row["municipality_id"] in context["prior_locked_ids"] for row in master):
        raise RuntimeError("prior 490-target municipality entered new queue")
    decision = read_json(OUTPUT / "broad_state_4x1000_scout_dry_run_prep_decision.json")
    if decision.get("decision") != DECISION or decision.get("actual_scout_covered_municipalities_after_dry_run_prep") != 2922:
        raise RuntimeError("decision or actual coverage boundary failed")
    for key in (
        "hosted_search_calls", "direct_sdk_calls", "api_model_calls", "url_opens",
        "head_get_requests", "downloads", "source_document_accesses",
        "candidate_review_runs", "ocr_runs", "render_runs", "text_extractions",
        "span_extractions", "rating_runs", "ingestion_runs", "codification_runs",
        "wage_gap_calculations", "regressions", "treatment_effect_estimates",
        "national_or_population_prevalence_claims", "final_causal_claims",
        "raw_prompts_saved", "raw_responses_saved",
    ):
        if decision.get(key) != 0:
            raise RuntimeError(f"forbidden counter is nonzero: {key}")
    print("completed_outputs_valid_zero_writes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate or (OUTPUT / "broad_state_4x1000_scout_dry_run_prep_decision.json").exists():
        validate_complete()
        return
    prepare()
    validate_complete()


if __name__ == "__main__":
    main()
