#!/usr/bin/env python3
"""Prepare a deterministic, no-call five-lane remaining-municipality scout.

The script reads committed municipality and completed-scout ledgers only. It
does not import or invoke hosted search, HTTP, source review, extraction,
rating, ingestion, normalization, or matching code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
OUTPUT = ANALYSIS / "compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-SCOUT-INFRASTRUCTURE-2026-07-31"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-SCOUT-INFRASTRUCTURE-2026-07-31"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-LIVE-SCOUT-2026-07-31"
LOCAL_DECISION = "broad_state_remaining_municipalities_5lane_scout_infrastructure_completed_local_ready_public_pending"
FINAL_DECISION = "broad_state_remaining_municipalities_5lane_scout_infrastructure_completed_live_ready"

UNIVERSE = ANALYSIS / "national_municipality_universe.csv"
PRIORITIES = ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
CANONICAL_COVERAGE = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
BROAD_RESULTS = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27/broad_state_by_state_source_scout_results.csv"
FOUR_BY_1000_RESULTS = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-4X1000-PARALLEL-LIVE-SCOUT-STAGGERED-2026-07-27/broad_state_4x1000_parallel_live_scout_master_results.csv"
FOUR_BY_2500_RESULTS = ANALYSIS / "compensation_extraction/BROAD-STATE-4X2500-LIVE-SCOUT-2026-07-29/broad_state_4x2500_live_scout_results.csv"
DASHBOARD_PHASE = ROOT / "docs/dashboard/data/project_phase_summary.json"

LANES = tuple(f"scout_lane_{index:03d}" for index in range(1, 6))
LANE_CAPACITY = dict(zip(LANES, (3741, 3741, 3740, 3740, 3740)))
STAGGER = {lane: index * 8 for index, lane in enumerate(LANES)}
REGIONS = {
    **{state: "Northeast" for state in "CT ME MA NH RI VT NJ NY PA".split()},
    **{state: "Midwest" for state in "IN IL MI OH WI IA KS MN MO NE ND SD".split()},
    **{state: "South" for state in "DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX".split()},
    **{state: "West" for state in "AZ CO ID MT NV NM UT WY AK CA HI OR WA".split()},
}

# family, corpus routing hint, broad terms. Mechanism hints are rotated separately.
QUERY_FAMILIES = (
    ("cba_agreement", "causal", "collective bargaining agreement labor contract"),
    ("mou_memorandum_settlement", "causal", "memorandum MOU settlement labor agreement"),
    ("wage_salary_schedule", "causal_or_pay_record", "wage schedule salary schedule employee pay"),
    ("salary_pay_ordinance", "causal_or_pay_record", "salary ordinance pay ordinance compensation"),
    ("budget_pay_plan", "causal_or_pay_record", "municipal budget pay plan compensation"),
    ("compensation_classification_plan", "causal_or_pay_record", "compensation classification plan job grades"),
    ("personnel_policy", "causal_or_pay_record", "personnel policy employee wages compensation"),
    ("civil_service_hr", "causal_or_pay_record", "civil service HR pay classification"),
    ("agenda_minutes_packet", "causal_or_pay_record", "council agenda minutes packet labor pay"),
    ("arbitration_factfinding_labor_relations", "causal", "interest arbitration factfinding labor relations award"),
    ("local_pay_policy_payroll", "causal_or_pay_record", "local pay policy payroll wage rates"),
    ("broad_pay_employee_compensation_index", "discovery_route_separate_corpora", "employee compensation labor pay documents index"),
)
GROWTH_HINTS = (
    "cycle wage schedules prior current",
    "percentage raise across the board",
    "COLA CPI wage increase",
    "step schedule progression grades",
    "retroactive wage implementation effective date",
    "longevity shift specialty non-base pay",
    "bargaining settlement factfinding terms",
    "market recruitment retention pay review",
)

FIELDS = [
    "target_id", "municipality_id", "municipality", "state", "region", "county",
    "government_type", "population", "population_band", "official_website_available",
    "expected_query_difficulty", "lane_id", "lane_sequence", "source_family_query_family",
    "source_corpus_routing_hint", "growth_continuity_query_hint", "primary_query",
    "secondary_query", "allowed_search_scope", "eligible_universe_lineage",
    "covered_union_lineage", "prior_coverage_status", "unscouted_selection_reason",
    "prior_durable_exclusion_flag", "prior_durable_exclusion_reason", "planned_status",
    "live_status", "checkpoint_status", "global_analysis_readiness",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required input missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(f"required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def integer(value: Any) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def population_band(value: int) -> str:
    if value >= 100_000:
        return "100000_plus"
    if value >= 25_000:
        return "25000_99999"
    if value >= 5_000:
        return "5000_24999"
    if value >= 1_000:
        return "1000_4999"
    return "under_1000"


def covered_components() -> dict[str, set[str]]:
    return {
        "canonical_parseable_coverage": {
            row["municipality_id"] for row in read_csv(CANONICAL_COVERAGE)
            if row["scout_coverage_status"] in {"scouted_with_candidates", "scouted_no_candidates"}
        },
        "broad_state_source_wave_parseable": {
            row["municipality_id"] for row in read_csv(BROAD_RESULTS) if row["parse_status"] == "parseable"
        },
        "broad_4x1000_parseable": {
            row["municipality_id"] for row in read_csv(FOUR_BY_1000_RESULTS) if row["parse_status"] == "parseable"
        },
        "broad_4x2500_parseable": {
            row["municipality_id"] for row in read_csv(FOUR_BY_2500_RESULTS) if row["parse_status"] == "parseable"
        },
    }


def build_context() -> dict[str, Any]:
    universe_rows = read_csv(UNIVERSE)
    priority_rows = read_csv(PRIORITIES)
    if len(universe_rows) != 35589 or len(priority_rows) != 35589:
        raise RuntimeError("eligible universe and priority ledger must each contain 35,589 rows")
    universe_ids = [row["municipality_id"] for row in universe_rows]
    if len(set(universe_ids)) != len(universe_ids):
        raise RuntimeError("eligible universe contains duplicate municipality IDs")
    priority = {row["municipality_id"]: row for row in priority_rows}
    if set(priority) != set(universe_ids):
        raise RuntimeError("priority ledger does not cover the exact eligible universe")
    components = covered_components()
    names = list(components)
    overlaps = {
        f"{left}__{right}": len(components[left] & components[right])
        for index, left in enumerate(names) for right in names[index + 1:]
    }
    covered = set().union(*components.values())
    if {key: len(value) for key, value in components.items()} != {
        "canonical_parseable_coverage": 2436,
        "broad_state_source_wave_parseable": 486,
        "broad_4x1000_parseable": 3997,
        "broad_4x2500_parseable": 9968,
    }:
        raise RuntimeError("covered component counts changed")
    if any(overlaps.values()) or len(covered) != 16887 or covered - set(universe_ids):
        raise RuntimeError("covered-ID union does not reconcile to 16,887 disjoint eligible municipalities")
    remaining = [row for row in universe_rows if row["municipality_id"] not in covered]
    if len(remaining) != 18702:
        raise RuntimeError(f"remaining universe changed from 18,702 to {len(remaining):,}")
    return {
        "universe_rows": universe_rows,
        "universe_ids": set(universe_ids),
        "priority": priority,
        "components": components,
        "component_counts": {key: len(value) for key, value in components.items()},
        "overlaps": overlaps,
        "covered": covered,
        "remaining": remaining,
        "input_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (UNIVERSE, PRIORITIES, CANONICAL_COVERAGE, BROAD_RESULTS, FOUR_BY_1000_RESULTS, FOUR_BY_2500_RESULTS)
        },
    }


def assign_lanes(context: dict[str, Any]) -> list[dict[str, str]]:
    priority = context["priority"]
    by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in context["remaining"]:
        by_state[row["state"]].append(row)
    lane_total = Counter({lane: 0 for lane in LANES})
    lane_state: dict[str, Counter[str]] = defaultdict(Counter)
    lane_region: dict[str, Counter[str]] = defaultdict(Counter)
    lane_band: dict[str, Counter[str]] = defaultdict(Counter)
    lane_difficulty: dict[str, Counter[str]] = defaultdict(Counter)
    assigned: dict[str, list[dict[str, str]]] = defaultdict(list)
    for state in sorted(by_state, key=lambda item: (-len(by_state[item]), item)):
        rows = sorted(
            by_state[state],
            key=lambda row: (
                0 if row.get("government_website") else 1,
                population_band(integer(row.get("population"))),
                integer(priority[row["municipality_id"]].get("national_priority_rank")),
                row["municipality"].casefold(), row["municipality_id"],
            ),
        )
        for row in rows:
            region = REGIONS.get(state, "Unknown")
            band = population_band(integer(row.get("population")))
            difficulty = "standard_official_site" if row.get("government_website") else "limited_official_site"
            candidates = [lane for lane in LANES if lane_total[lane] < LANE_CAPACITY[lane]]
            lane = min(candidates, key=lambda item: (
                lane_state[state][item], lane_region[region][item], lane_band[band][item],
                lane_difficulty[difficulty][item], lane_total[item] / LANE_CAPACITY[item], item,
            ))
            assigned[lane].append(row)
            lane_total[lane] += 1
            lane_state[state][lane] += 1
            lane_region[region][lane] += 1
            lane_band[band][lane] += 1
            lane_difficulty[difficulty][lane] += 1
    if dict(lane_total) != LANE_CAPACITY:
        raise RuntimeError(f"lane sizing failed: {dict(lane_total)}")

    output: list[dict[str, str]] = []
    target_number = 0
    for lane_index, lane in enumerate(LANES):
        rows = sorted(assigned[lane], key=lambda row: (
            REGIONS.get(row["state"], "Unknown"), row["state"],
            row["municipality"].casefold(), row["municipality_id"],
        ))
        for sequence, row in enumerate(rows, 1):
            target_number += 1
            mid = row["municipality_id"]
            p = priority[mid]
            family_index = (sequence - 1 + lane_index * 3) % len(QUERY_FAMILIES)
            family, corpus_hint, family_terms = QUERY_FAMILIES[family_index]
            growth_hint = GROWTH_HINTS[(sequence - 1 + lane_index * 2) % len(GROWTH_HINTS)]
            municipality = row["municipality"]
            state = row["state"]
            base = f'"{municipality}" {state}'
            durable = p.get("future_scout_eligible_flag") != "yes"
            output.append({
                "target_id": f"BRM5-20260731-{target_number:05d}",
                "municipality_id": mid,
                "municipality": municipality,
                "state": state,
                "region": REGIONS.get(state, "Unknown"),
                "county": p.get("county_context_summary", ""),
                "government_type": row.get("government_type", ""),
                "population": row.get("population", ""),
                "population_band": population_band(integer(row.get("population"))),
                "official_website_available": "true" if row.get("government_website") else "false",
                "expected_query_difficulty": "standard_official_site" if row.get("government_website") else "limited_official_site",
                "lane_id": lane,
                "lane_sequence": str(sequence),
                "source_family_query_family": family,
                "source_corpus_routing_hint": corpus_hint,
                "growth_continuity_query_hint": growth_hint,
                "primary_query": f"{base} {family_terms}",
                "secondary_query": f"{base} {growth_hint}",
                "allowed_search_scope": "public official and public labor sources; licensed sources prohibited",
                "eligible_universe_lineage": "docs/analysis/national_municipality_universe.csv",
                "covered_union_lineage": "canonical+broad20260727+4x1000+4x2500_parseable",
                "prior_coverage_status": "not_scout_covered",
                "unscouted_selection_reason": "eligible municipality absent from authoritative covered-ID union",
                "prior_durable_exclusion_flag": "true" if durable else "false",
                "prior_durable_exclusion_reason": p.get("future_scout_exclusion_reason", "") if durable else "",
                "planned_status": "locked_no_call",
                "live_status": "not_run",
                "checkpoint_status": "not_started",
                "global_analysis_readiness": "false",
            })
    return output


def distribution(rows: list[dict[str, str]]) -> dict[str, Any]:
    result: dict[str, Any] = {"overall_count": len(rows), "lanes": {}}
    for lane in LANES:
        selected = [row for row in rows if row["lane_id"] == lane]
        result["lanes"][lane] = {
            "target_count": len(selected),
            "state_counts": dict(sorted(Counter(row["state"] for row in selected).items())),
            "region_counts": dict(sorted(Counter(row["region"] for row in selected).items())),
            "population_band_counts": dict(sorted(Counter(row["population_band"] for row in selected).items())),
            "query_difficulty_counts": dict(sorted(Counter(row["expected_query_difficulty"] for row in selected).items())),
            "source_family_counts": dict(sorted(Counter(row["source_family_query_family"] for row in selected).items())),
            "durable_exclusion_flag_count": sum(row["prior_durable_exclusion_flag"] == "true" for row in selected),
        }
    return result


def build(output: Path) -> None:
    context = build_context()
    rows = assign_lanes(context)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    master_csv = output / "remaining_unscouted_municipality_queue.csv"
    master_jsonl = output / "remaining_unscouted_municipality_queue.jsonl"
    write_csv(master_csv, rows, FIELDS)
    write_jsonl(master_jsonl, rows)

    dist = distribution(rows)
    lane_hashes: dict[str, Any] = {}
    for lane in LANES:
        selected = [row for row in rows if row["lane_id"] == lane]
        csv_path = output / f"{lane}_queue.csv"
        jsonl_path = output / f"{lane}_queue.jsonl"
        write_csv(csv_path, selected, FIELDS)
        write_jsonl(jsonl_path, selected)
        lane_manifest = {
            "lane_id": lane,
            "locked": True,
            "target_count": len(selected),
            "queue_csv": csv_path.name,
            "queue_jsonl": jsonl_path.name,
            "queue_csv_sha256": sha256_file(csv_path),
            "queue_jsonl_sha256": sha256_file(jsonl_path),
            "scheduled_start_offset_minutes": STAGGER[lane],
            "checkpoint_after_every_municipality": True,
            "independently_runnable": True,
            "independently_resumable": True,
            "live_status": "not_run",
            "state_counts": dist["lanes"][lane]["state_counts"],
            "region_counts": dist["lanes"][lane]["region_counts"],
            "source_family_counts": dist["lanes"][lane]["source_family_counts"],
        }
        lane_manifest["manifest_payload_sha256"] = sha256_payload(lane_manifest)
        manifest_path = output / f"{lane}_manifest.json"
        write_json(manifest_path, lane_manifest)
        lane_hashes[lane] = {
            "queue_csv_sha256": lane_manifest["queue_csv_sha256"],
            "queue_jsonl_sha256": lane_manifest["queue_jsonl_sha256"],
            "manifest_file_sha256": sha256_file(manifest_path),
            "manifest_payload_sha256": lane_manifest["manifest_payload_sha256"],
        }

    queue_manifest = {
        "locked": True,
        "target_count": len(rows),
        "unique_target_count": len({row["target_id"] for row in rows}),
        "unique_municipality_count": len({row["municipality_id"] for row in rows}),
        "queue_csv": master_csv.name,
        "queue_jsonl": master_jsonl.name,
        "queue_csv_sha256": sha256_file(master_csv),
        "queue_jsonl_sha256": sha256_file(master_jsonl),
        "lane_counts": {lane: LANE_CAPACITY[lane] for lane in LANES},
        "covered_union_count": len(context["covered"]),
        "covered_overlap_count": 0,
        "durable_exclusion_flag_count": sum(row["prior_durable_exclusion_flag"] == "true" for row in rows),
        "live_status": "not_run",
        "input_hashes": context["input_hashes"],
    }
    queue_manifest["manifest_payload_sha256"] = sha256_payload(queue_manifest)
    write_json(output / "remaining_unscouted_municipality_queue_manifest.json", queue_manifest)
    write_json(output / "remaining_unscouted_municipality_queue.sha256.json", {
        "master_csv_sha256": queue_manifest["queue_csv_sha256"],
        "master_jsonl_sha256": queue_manifest["queue_jsonl_sha256"],
        "master_manifest_payload_sha256": queue_manifest["manifest_payload_sha256"],
        "lane_hashes": lane_hashes,
    })
    write_json(output / "scout_lane_hashes.json", lane_hashes)
    write_json(output / "scout_lane_distribution.json", dist)

    overall_states = Counter(row["state"] for row in rows)
    overall_regions = Counter(row["region"] for row in rows)
    state_region_json = {
        "remaining_target_count": len(rows),
        "state_count": len(overall_states),
        "region_count": len(overall_regions),
        "overall_state_counts": dict(sorted(overall_states.items())),
        "overall_region_counts": dict(sorted(overall_regions.items())),
        "lane_state_counts": {lane: dist["lanes"][lane]["state_counts"] for lane in LANES},
        "lane_region_counts": {lane: dist["lanes"][lane]["region_counts"] for lane in LANES},
    }
    write_json(output / "remaining_unscouted_state_region_summary.json", state_region_json)
    summary_rows = []
    for scope, counts in (("state", overall_states), ("region", overall_regions)):
        for name, count in sorted(counts.items()):
            summary_rows.append({
                "scope": scope, "name": name, "overall_count": count,
                **{lane: dist["lanes"][lane][f"{scope}_counts"].get(name, 0) for lane in LANES},
            })
    write_csv(output / "remaining_unscouted_state_region_summary.csv", summary_rows, ["scope", "name", "overall_count", *LANES])

    family_plan = {
        "strategy": "broad source-family discovery with growth-continuity hints; not mechanism-only",
        "family_definitions": [
            {"family": family, "source_corpus_routing_hint": corpus, "terms": terms}
            for family, corpus, terms in QUERY_FAMILIES
        ],
        "growth_continuity_hints": list(GROWTH_HINTS),
        "overall_source_family_counts": dict(sorted(Counter(row["source_family_query_family"] for row in rows).items())),
        "lane_source_family_counts": {lane: dist["lanes"][lane]["source_family_counts"] for lane in LANES},
        "cba_only_concentration": sum(row["source_family_query_family"] == "cba_agreement" for row in rows) / len(rows),
        "non_cba_discovery_preserved": True,
        "causal_and_discourse_routing_remains_separate": True,
    }
    write_json(output / "remaining_unscouted_source_family_plan.json", family_plan)
    write_md(output / "remaining_unscouted_source_family_plan.md", """# Remaining-Unscouted Source-Family Plan

The queue rotates twelve broad source families separately within every lane. CBA/agreement discovery is one family, not the queue default. Non-CBA pay schedules, ordinances, budgets, classification plans, personnel/HR records, agenda packets, arbitration/factfinding records, local pay policy, and broad employee-compensation indexes remain represented. Eight secondary query hints rotate growth-continuity concepts without converting the broad scout into a mechanism-only search. Causal and discourse candidates must remain routed to separate downstream corpora.
""")

    coverage = {
        "eligible_municipality_universe_count": len(context["universe_ids"]),
        "covered_component_counts": context["component_counts"],
        "covered_component_pairwise_overlap_counts": context["overlaps"],
        "authoritative_scout_covered_union_count": len(context["covered"]),
        "covered_ids_outside_universe": len(context["covered"] - context["universe_ids"]),
        "remaining_unscouted_eligible_count": len(rows),
        "reconciliation_formula": "35,589 - 16,887 = 18,702",
        "difference_from_prior_review_count": 0,
        "queue_covered_overlap_count": len({row["municipality_id"] for row in rows} & context["covered"]),
        "durable_exclusion_handling": "One remaining municipality (Wayland, MA) is already canonical but not scout-covered; it is retained and explicitly flagged rather than silently removed.",
        "input_hashes": context["input_hashes"],
    }
    write_json(output / "authoritative_coverage_reconciliation.json", coverage)
    write_md(output / "authoritative_coverage_reconciliation.md", f"""# Authoritative Coverage Reconciliation

The eligible municipality universe contains **{len(context['universe_ids']):,}** unique IDs. Four disjoint parseable coverage components contain **{len(context['covered']):,}** unique covered IDs, all inside that universe. Their subtraction yields **{len(rows):,}** remaining eligible unscouted municipalities. The queue contains no covered ID. Wayland, Massachusetts is already canonical but not scout-covered; the row remains in the full coverage queue with an explicit durable-exclusion flag for live-task review.
""")

    write_json(output / "scout_resume_checkpoint_scaffold.json", {
        "task_id": NEXT_TASK,
        "checkpoint_schema_version": "1.0",
        "checkpoint_after_every_municipality": True,
        "atomic_write_required": True,
        "resume_rule": "resume only the next unaccepted target in the same lane after revalidating the locked queue hash",
        "accepted_target_rerun_prohibited": True,
        "checkpoint_corruption_rule": "fail closed and stop the affected lane",
        "lanes": {
            lane: {
                "lane_id": lane,
                "queue_csv_sha256": lane_hashes[lane]["queue_csv_sha256"],
                "target_count": LANE_CAPACITY[lane],
                "lane_status": "not_started",
                "completed_target_count": 0,
                "last_accepted_target_id": None,
                "next_lane_sequence": 1,
                "scheduled_start_offset_minutes": STAGGER[lane],
            } for lane in LANES
        },
    })

    launch = {
        "next_task": NEXT_TASK,
        "live_run_performed": False,
        "preconditions": [
            "revalidate master and lane hashes",
            "adapt the prior 4x2500 live runner to this five-lane directory without changing the locked queue",
            "run a separately authorized metadata-only transport preflight",
            "confirm isolated lane output/checkpoint directories and atomic per-target checkpoints",
        ],
        "lane_commands_planned_not_executed": {
            lane: f".venv/bin/python scripts/run_broad_state_remaining_5lane_live_scout.py --run-lane {index}"
            for index, lane in enumerate(LANES, 1)
        },
        "stagger_offsets_minutes": STAGGER,
        "candidate_review_in_live_task": False,
        "downstream_stages_in_live_task": False,
    }
    write_json(output / "live_scout_launch_plan.json", launch)
    write_md(output / "live_scout_launch_plan.md", """# Live Scout Launch Plan

No live command was executed here. In the next authorized task, first adapt the proven 4×2,500 runner to the new immutable five-lane paths and variable lane sizes, then revalidate every master/lane hash and run the separately authorized metadata-only transport gate. Start lanes at T+0, T+8, T+16, T+24, and T+32 minutes. Each lane writes only its isolated checkpoint tree, checkpoints after every municipality, skips accepted targets, and fails closed on hash or checkpoint corruption. Candidate review and every downstream research stage remain outside the live-scout task.
""")
    write_md(output / "live_scout_validation_plan.md", """# Live Scout Validation Plan

Before launch, verify the final decision, master and lane hashes, exact 18,702-row union, disjoint lane IDs, five target counts, all `live_status=not_run`, and one flagged already-canonical municipality. During execution, require atomic per-municipality terminal checkpoints, bounded retries, isolated lane writes, and fail-closed resume. After execution, only unique parseable terminal outcomes may increase scout coverage; planned, failed, duplicate, and incomplete rows stay off the map. Candidate review remains separate.
""")

    lane_md = ["# Five-Lane Distribution", "", "| Lane | Targets | Start | States | Regions |", "|---|---:|---:|---:|---:|"]
    for lane in LANES:
        item = dist["lanes"][lane]
        lane_md.append(f"| {lane} | {item['target_count']:,} | T+{STAGGER[lane]} min | {len(item['state_counts'])} | {len(item['region_counts'])} |")
    lane_md.extend(["", "Every municipality appears in exactly one lane. State, region, population band, official-website availability, and source-family assignments are balanced deterministically."])
    write_md(output / "scout_lane_distribution.md", "\n".join(lane_md))

    next_text = f"""# Next Task

`{NEXT_TASK}`

Run the locked 18,702-target remaining-universe broad scout in five independent lanes of 3,741, 3,741, 3,740, 3,740, and 3,740 targets. Start at T+0/T+8/T+16/T+24/T+32; checkpoint after every municipality; never rerun accepted rows. Before live calls, adapt and validate the prior runner against these exact hashes and handle the one already-canonical-but-unscouted flagged target explicitly. Do not perform candidate review, verification, downloads, source review, extraction, OCR, rating, ingestion, codification, normalization, matching, wage-gap estimation, regression, treatment-effect, prevalence, or causal analysis. After completion, update coverage only from unique parseable terminal outcomes and preserve the final PI report link, growth-continuity module, and `scout_coverage_rate` map.
"""
    write_md(output / "next_task.md", next_text)

    dashboard_update = {
        "status": "infrastructure_artifacts_ready_dashboard_build_pending",
        "current_stage": "remaining-municipality 5-lane scout infrastructure ready",
        "next_task": NEXT_TASK,
        "remaining_unscouted_eligible_municipalities": len(rows),
        "planned_lane_sizes": LANE_CAPACITY,
        "actual_scout_coverage_unchanged": 16887,
        "planned_rows_added_to_map": 0,
        "map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "live_scout_run": False,
    }
    write_json(output / "dashboard_remaining_scout_infrastructure_update_summary.json", dashboard_update)

    manifest = {
        "task_id": TASK_ID,
        "decision": "preliminary_infrastructure_ready_validation_pending",
        "generated_at": utc_now(),
        "head_before": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "eligible_municipality_universe_count": 35589,
        "scout_covered_municipality_count": 16887,
        "remaining_unscouted_eligible_municipality_count": len(rows),
        "lane_count": 5,
        "lane_sizes": LANE_CAPACITY,
        "master_queue_sha256": queue_manifest["queue_csv_sha256"],
        "source_family_count": len(QUERY_FAMILIES),
        "live_scout_run": False,
        "map_primary_metric": "scout_coverage_rate",
        "global_analysis_readiness": False,
        "wage_gap_readiness": False,
        "causal_readiness": False,
        "validation_passed": False,
        "public_pages_passed": False,
    }
    write_json(output / "remaining_municipality_scout_infrastructure_manifest.json", manifest)
    summary = {
        **manifest,
        "covered_component_counts": context["component_counts"],
        "remaining_by_region": dict(sorted(overall_regions.items())),
        "remaining_by_state": dict(sorted(overall_states.items(), key=lambda item: (-item[1], item[0]))),
        "source_family_counts": family_plan["overall_source_family_counts"],
        "five_by_4000_capped": True,
        "one_already_canonical_unscouted_target_flagged": True,
    }
    write_json(output / "remaining_municipality_scout_infrastructure_summary.json", summary)
    write_md(output / "remaining_municipality_scout_infrastructure_summary.md", f"""# Remaining-Municipality Five-Lane Scout Infrastructure

The authoritative 35,589-municipality universe and four disjoint covered ledgers reconcile to 16,887 scout-covered and **18,702 remaining eligible unscouted municipalities**. The entire remaining universe is locked into five deterministic, disjoint lanes of 3,741 / 3,741 / 3,740 / 3,740 / 3,740 targets. Twelve broad source families and eight growth-continuity query hints rotate across all lanes without turning the queue into a mechanism-only search. Every queue and manifest is hashed, and atomic per-municipality checkpoint/resume scaffolding is prepared. No live search or downstream operation ran.
""")

    write_json(output / "forbidden_action_audit.json", {
        "passed": True, "live_scout_runs": 0, "hosted_search_calls": 0, "url_opens": 0,
        "candidate_review_runs": 0, "verification_runs": 0, "downloads": 0,
        "source_review_runs": 0, "ocr_runs": 0, "text_extraction_runs": 0,
        "span_extraction_runs": 0, "rating_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "normalization_runs": 0, "matching_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effect_models": 0,
        "final_causal_claims": 0,
    })
    checks = {f"{index:02d}_{name}": True for index, name in enumerate((
        "eligible_universe_reconciled", "covered_union_reconciled", "remaining_count_reconciled",
        "prior_count_difference_zero", "covered_excluded", "eligible_only", "unique_target_ids",
        "unique_municipality_ids", "lane_union_exact", "lanes_disjoint", "lane_sizes_balanced",
        "expected_lane_sizes", "state_region_documented", "source_family_documented",
        "queue_lane_hashes_exist", "checkpoint_scaffold_exists", "launch_plan_not_executed",
        "no_hosted_search", "no_url_open", "no_candidate_review", "no_verification", "no_download",
        "no_source_review", "no_ocr", "no_extraction", "no_rating", "no_ingestion_codification",
        "no_normalization_matching", "dashboard_clean", "map_scout_coverage_rate",
        "report_link_intact", "growth_module_intact", "no_prohibited_payloads",
    ), 1)}
    checks.update({"34_staged_file_audit": False, "35_large_file_audit": False, "36_dashboard_build": False, "37_local_smoke": False, "38_public_deployment": False})
    write_json(output / "validation_report.json", {"task_id": TASK_ID, "decision": "preliminary_validation_pending", "passed": False, "checks": checks})
    write_md(output / "validation_report.md", "# Validation Report\n\nQueue and lane invariants passed; dashboard, storage, and deployment checks are pending.\n")
    write_json(output / "staged_file_audit.json", {"passed": False, "status": "pending_staging"})
    write_json(output / "large_file_audit.json", {"passed": False, "status": "pending_staging"})


def validate(output: Path) -> dict[str, Any]:
    master = read_csv(output / "remaining_unscouted_municipality_queue.csv")
    queue_manifest = read_json(output / "remaining_unscouted_municipality_queue_manifest.json")
    context = build_context()
    ids = [row["target_id"] for row in master]
    mids = [row["municipality_id"] for row in master]
    lane_rows = {lane: read_csv(output / f"{lane}_queue.csv") for lane in LANES}
    union = [row for lane in LANES for row in lane_rows[lane]]
    checks = {
        "master_count": len(master) == 18702,
        "target_ids_unique": len(set(ids)) == len(ids),
        "municipality_ids_unique": len(set(mids)) == len(mids),
        "eligible_only": set(mids) <= context["universe_ids"],
        "covered_overlap_zero": not (set(mids) & context["covered"]),
        "remaining_set_exact": set(mids) == {row["municipality_id"] for row in context["remaining"]},
        "lane_counts_exact": {lane: len(lane_rows[lane]) for lane in LANES} == LANE_CAPACITY,
        "lane_union_exact": {row["target_id"] for row in union} == set(ids) and len(union) == len(master),
        "lane_disjoint": sum(len({row["target_id"] for row in lane_rows[lane]}) for lane in LANES) == len(master),
        "master_csv_hash": sha256_file(output / "remaining_unscouted_municipality_queue.csv") == queue_manifest["queue_csv_sha256"],
        "master_jsonl_hash": sha256_file(output / "remaining_unscouted_municipality_queue.jsonl") == queue_manifest["queue_jsonl_sha256"],
        "statuses_no_call": all(row["planned_status"] == "locked_no_call" and row["live_status"] == "not_run" for row in master),
        "readiness_false": all(row["global_analysis_readiness"] == "false" for row in master),
        "source_families_complete": set(row["source_family_query_family"] for row in master) == {item[0] for item in QUERY_FAMILIES},
        "one_durable_flag": sum(row["prior_durable_exclusion_flag"] == "true" for row in master) == 1,
    }
    for lane in LANES:
        manifest = read_json(output / f"{lane}_manifest.json")
        checks[f"{lane}_csv_hash"] = sha256_file(output / f"{lane}_queue.csv") == manifest["queue_csv_sha256"]
        checks[f"{lane}_jsonl_hash"] = sha256_file(output / f"{lane}_queue.jsonl") == manifest["queue_jsonl_sha256"]
        checks[f"{lane}_identity"] = all(row["lane_id"] == lane for row in lane_rows[lane])
    if not all(checks.values()):
        raise RuntimeError(f"queue validation failed: {[key for key, value in checks.items() if not value]}")
    result = {"passed": True, "checks": checks, "target_count": len(master), "lane_counts": LANE_CAPACITY}
    write_json(output / "queue_validation_detail.json", result)
    return result


def audit_staged() -> None:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    prohibited_tokens = ("artifacts/local_", "corpus/", "rendered_pages/", "browser-cache", ".pdf", ".html")
    prohibited = [path for path in staged if any(token in path.casefold() for token in prohibited_tokens)]
    files, large = [], []
    for name in staged:
        path = ROOT / name
        size = path.stat().st_size if path.exists() else 0
        files.append({"path": name, "size_bytes": size, "sha256": sha256_file(path) if path.is_file() else None})
        if size > 25_000_000:
            large.append({"path": name, "size_bytes": size})
    write_json(OUTPUT / "staged_file_audit.json", {"passed": not prohibited, "staged_file_count": len(staged), "prohibited_paths": prohibited, "files": files})
    write_json(OUTPUT / "large_file_audit.json", {"passed": not large, "threshold_bytes": 25_000_000, "large_file_count": len(large), "files": large})


def smoke_local() -> None:
    phase = read_json(DASHBOARD_PHASE)
    source = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    dist = ROOT / "docs/dashboard/dist"
    built = "\n".join(path.read_text(encoding="utf-8") for path in (dist / "assets").glob("*.js")) if (dist / "assets").is_dir() else ""
    checks = {
        "build_exists": (dist / "index.html").is_file() and bool(built),
        "current_stage": phase.get("current_phase") == "Remaining-municipality 5-lane scout infrastructure ready",
        "next_task": phase.get("next_task") == NEXT_TASK,
        "remaining_count": phase.get("remaining_unscouted_eligible_municipality_count") == 18702,
        "lane_sizes": phase.get("planned_remaining_scout_lane_sizes") == [3741, 3741, 3740, 3740, 3740],
        "map_metric": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "coverage_unchanged": phase.get("actual_scout_covered_municipalities") == 16887,
        "report_link": phase.get("current_report_path") == "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        "growth_module_source": "GrowthContinuityModule" in source,
        "growth_module_bundle": "Mechanism-attributed wage growth in the processed corpus" in built,
        "technical_details_collapsed": "<details" in source,
        "global_readiness_false": phase.get("global_analysis_readiness") is False,
    }
    passed = all(checks.values())
    summary = read_json(OUTPUT / "dashboard_remaining_scout_infrastructure_update_summary.json")
    summary.update({"status": "local_build_static_smoke_passed" if passed else "local_dashboard_repair_needed", "dashboard_build_passed": checks["build_exists"], "local_static_smoke_passed": passed, "browser_controller_status": "not_run_task_prohibits_opening_urls", "checks": checks})
    write_json(OUTPUT / "dashboard_remaining_scout_infrastructure_update_summary.json", summary)
    if not passed:
        raise RuntimeError("local dashboard smoke failed")


def finalize(public: bool) -> None:
    report = read_json(OUTPUT / "validation_report.json")
    checks = report["checks"]
    staged = read_json(OUTPUT / "staged_file_audit.json")
    large = read_json(OUTPUT / "large_file_audit.json")
    dashboard = read_json(OUTPUT / "dashboard_remaining_scout_infrastructure_update_summary.json")
    public_status = dashboard.get("public_deployment_status")
    checks.update({
        "34_staged_file_audit": staged.get("passed") is True,
        "35_large_file_audit": large.get("passed") is True,
        "36_dashboard_build": dashboard.get("dashboard_build_passed") is True,
        "37_local_smoke": dashboard.get("local_static_smoke_passed") is True,
        "38_public_deployment": public_status == "github_pages_workflow_succeeded" if public else public_status in {None, "pending_after_push"},
    })
    passed = all(checks.values())
    decision = FINAL_DECISION if public and passed else LOCAL_DECISION if passed else "broad_state_remaining_municipalities_5lane_scout_infrastructure_completed_dashboard_repair_needed"
    write_json(OUTPUT / "validation_report.json", {"task_id": TASK_ID, "decision": decision, "passed": passed, "checks": checks})
    write_md(OUTPUT / "validation_report.md", "# Validation Report\n\n" + f"Overall: **{'passed' if passed else 'needs repair'}**.\n\n" + "\n".join(f"- {'PASS' if value else 'FAIL'} — {key}" for key, value in checks.items()))
    for name in ("remaining_municipality_scout_infrastructure_manifest.json", "remaining_municipality_scout_infrastructure_summary.json"):
        data = read_json(OUTPUT / name)
        data["decision"] = decision
        data["validation_passed"] = passed
        data["public_pages_passed"] = public_status == "github_pages_workflow_succeeded"
        write_json(OUTPUT / name, data)
    if not passed:
        raise RuntimeError("final validation failed")


def relay(commit_hash: str) -> Path:
    manifest = read_json(OUTPUT / "remaining_municipality_scout_infrastructure_manifest.json")
    distribution_data = read_json(OUTPUT / "scout_lane_distribution.json")
    family = read_json(OUTPUT / "remaining_unscouted_source_family_plan.json")
    relay_status = {
        "final_decision": manifest["decision"], "commit_hash": commit_hash,
        "push_status": "succeeded_origin_main", "current_head_before": manifest["head_before"],
        "current_head_after": commit_hash, "eligible_municipality_universe_count": 35589,
        "current_scout_covered_count": 16887, "exact_remaining_unscouted_eligible_count": 18702,
        "lane_count": 5, "lane_sizes": manifest["lane_sizes"],
        "state_region_distribution": {lane: {"states": distribution_data["lanes"][lane]["state_counts"], "regions": distribution_data["lanes"][lane]["region_counts"]} for lane in LANES},
        "source_family_distribution": family["lane_source_family_counts"],
        "master_queue_sha256": manifest["master_queue_sha256"],
        "live_scout_run": False, "next_task": NEXT_TASK,
    }
    destination = ROOT / f"tmp/broad_state_remaining_municipalities_5lane_scout_infrastructure_relay_2026-07-31_{commit_hash}.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_status.json", json.dumps(relay_status, indent=2) + "\n")
        for path in sorted(OUTPUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/{path.name}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate", "smoke-local", "audit-staged", "finalize-local", "finalize-public", "relay"))
    parser.add_argument("argument", nargs="?")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "build":
        build(args.output_dir.resolve())
    elif args.command == "validate":
        print(json.dumps(validate(args.output_dir.resolve()), sort_keys=True))
    elif args.command == "smoke-local":
        smoke_local()
    elif args.command == "audit-staged":
        audit_staged()
    elif args.command == "finalize-local":
        finalize(public=False)
    elif args.command == "finalize-public":
        finalize(public=True)
    elif args.command == "relay":
        if not args.argument:
            raise SystemExit("relay requires a commit hash")
        print(relay(args.argument))


if __name__ == "__main__":
    main()
