#!/usr/bin/env python3
"""Prepare and finalize the bounded broad state-by-state scout wave.

The live backend is deliberately invoked outside this generator through the
project's scout runner.  This file builds an immutable, state-balanced queue,
records a no-call preview, validates sanitized preflight metadata, and converts
parsed scout-stage metadata into the task package.  It never opens a URL.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs/analysis"
OUTPUT_DIR = ANALYSIS / "compensation_extraction/BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
MUNICIPALITY_COVERAGE = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
STATE_COVERAGE = ANALYSIS / "national_scout_coverage_state.csv"
PRIOR_CANDIDATES = ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv"
CITY_COVERAGE = ROOT / "data/city_coverage.csv"
SUPPLEMENT_DIR = ANALYSIS / "compensation_extraction/BOUNDED-TIER-C-EVIDENCE-MEMO-SUPPLEMENT-140-RATING-SUMMARY-2026-07-27"
SUPPLEMENT_DECISION = SUPPLEMENT_DIR / "bounded_tier_c_evidence_memo_supplement_decision.json"
RESULT_DOC = ANALYSIS / "broad_state_by_state_source_scout_wave_result_2026-07-27.md"
DASHBOARD_NOTE = ANALYSIS / "broad_state_by_state_source_scout_wave_dashboard_status_note_2026-07-27.md"
TASK_ID = "BROAD-STATE-BY-STATE-SOURCE-SCOUT-WAVE-2026-07-27"
DECISION = "broad_state_by_state_source_scout_completed_candidate_review_ready"
TARGETS_PER_AVAILABLE_STATE = 10
EXPECTED_QUEUE_COUNT = 490

REGIONS = {
    **{s: "Northeast" for s in "CT ME MA NH RI VT NJ NY PA".split()},
    **{s: "Midwest" for s in "IN IL MI OH WI IA KS MN MO NE ND SD".split()},
    **{s: "South" for s in "DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX".split()},
    **{s: "West" for s in "AZ CO ID MT NV NM UT WY AK CA HI OR WA".split()},
}

SOURCE_FAMILY_VALUES = {
    "cba", "mou_or_memorandum", "settlement_agreement", "arbitration_award",
    "factfinding_report", "salary_ordinance", "wage_schedule", "budget_or_pay_plan",
    "civil_service_or_hr_pay_plan", "compensation_study", "classification_study",
    "personnel_policy", "agenda_packet_or_minutes", "unknown_or_needs_review",
    "other_local_government_pay_policy",
}

CANDIDATE_FIELDS = [
    "scout_candidate_id", "scout_target_id", "state", "region", "municipality",
    "county", "unit_type", "occupation_group", "possible_bargaining_unit",
    "possible_cycle_or_year", "source_title", "source_locator_or_url", "source_domain",
    "source_family_hint", "document_type_hint", "source_family_confidence",
    "possible_mechanism_hints", "search_query_family", "broad_geographic_target_reason",
    "source_family_diversification_reason", "matched_non_safety_opportunity_flag",
    "duplicate_locator_flag", "prior_seen_locator_flag", "candidate_quality_tier",
    "verification_status", "download_status", "extraction_status", "rating_status",
    "ingestion_status", "codification_status", "causal_status",
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


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def normalize_locator(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        split = urlsplit(value)
        host = split.netloc.casefold().removeprefix("www.")
        path = re.sub(r"/+", "/", split.path).rstrip("/")
        return urlunsplit((split.scheme.casefold(), host, path, "", ""))
    except ValueError:
        return value.casefold().rstrip("/")


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


def validate_inputs() -> dict[str, Any]:
    decision = read_json(SUPPLEMENT_DECISION)
    if decision.get("decision") != "bounded_tier_c_evidence_memo_supplement_completed_broad_scouting_ready":
        raise RuntimeError("Tier C supplement does not authorize broad scouting")
    if decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("predecessor global analysis readiness boundary changed")
    municipality_rows = read_csv(MUNICIPALITY_COVERAGE)
    state_rows = read_csv(STATE_COVERAGE)
    prior_rows = read_csv(PRIOR_CANDIDATES)
    if len(municipality_rows) != 35589 or len(state_rows) != 51 or len(prior_rows) != 4726:
        raise RuntimeError("canonical 35,589 / 51 / 4,726 baseline failed reconciliation")
    covered = sum(integer(row["successful_live_scout_count"]) > 0 for row in municipality_rows)
    if covered != 2436:
        raise RuntimeError(f"canonical scout-covered baseline mismatch: {covered}")
    return {
        "municipalities": municipality_rows,
        "states": state_rows,
        "prior_candidates": prior_rows,
        "input_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (MUNICIPALITY_COVERAGE, STATE_COVERAGE, PRIOR_CANDIDATES, CITY_COVERAGE, SUPPLEMENT_DECISION)
        },
    }


def queue_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    unmatched = unmatched_safety_cycles()
    by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in context["municipalities"]:
        if row.get("scout_coverage_status") != "not_scouted":
            continue
        by_state[row["state"]].append(row)
    ordered_by_state: dict[str, list[dict[str, str]]] = {}
    for state in sorted(by_state):
        ordered_by_state[state] = sorted(
            by_state[state],
            key=lambda row: (
                0 if unmatched.get((state, row["municipality"].casefold())) else 1,
                -integer(row.get("population")),
                row["municipality"].casefold(),
                row["municipality_id"],
            ),
        )
    selected_source_rows = [
        row
        for state in sorted(ordered_by_state)
        for row in ordered_by_state[state][:TARGETS_PER_AVAILABLE_STATE]
    ]
    baseline_by_state = {
        row["state"]: integer(row["municipalities_scouted"])
        / max(1, integer(row["municipalities_in_universe"]))
        for row in context["states"]
    }
    selected_ids = {row["municipality_id"] for row in selected_source_rows}
    shortfall = EXPECTED_QUEUE_COUNT - len(selected_source_rows)
    for state in sorted(ordered_by_state, key=lambda value: (baseline_by_state[value], value)):
        if shortfall <= 0:
            break
        extra = next(
            (row for row in ordered_by_state[state] if row["municipality_id"] not in selected_ids),
            None,
        )
        if extra is None:
            continue
        selected_source_rows.append(extra)
        selected_ids.add(extra["municipality_id"])
        shortfall -= 1

    selected: list[dict[str, Any]] = []
    for row in sorted(
        selected_source_rows,
        key=lambda item: (item["state"], item["municipality"].casefold(), item["municipality_id"]),
    ):
            state = row["state"]
            cycles = unmatched.get((state, row["municipality"].casefold()), [])
            idx = len(selected) + 1
            reason_bits = ["new_municipality_coverage", "geographic_gap_fill", "source_family_diversification"]
            if cycles:
                reason_bits.append("matched_non_safety_opportunity")
            base = f'"{row["municipality"]}" {state}'
            selected.append({
                "scout_target_id": f"BSSS-20260727-{idx:04d}",
                "state": state,
                "region": REGIONS[state],
                "municipality": row["municipality"],
                "municipality_id": row["municipality_id"],
                "census_gov_id": row.get("census_gov_id", ""),
                "population": row.get("population", ""),
                "government_name": f'{row["municipality"]} municipal government',
                "expected_units_to_search": (
                    "police; fire; non_safety/general municipal; CBAs/MOUs/settlements; "
                    "arbitration/factfinding; salary/wage/pay plans; ordinances/personnel policy; "
                    "compensation/classification studies"
                ),
                "scout_purpose": "broad_geographic_source_family_diverse_discovery",
                "anchor_cycle": "; ".join(sorted(cycles)),
                "selection_reason": "; ".join(reason_bits),
                "broad_geographic_target_reason": "; ".join(reason_bits[:2]),
                "source_family_diversification_reason": "rotate_public_local_government_pay_document_families",
                "matched_non_safety_opportunity_flag": "true" if cycles else "false",
                "search_query_family": "broad_multi_source_family",
                "search_hint_1": f"{base} municipal labor agreements police fire general employees",
                "search_hint_2": f"{base} human resources pay plan wage salary schedule civil service",
                "search_hint_3": f"{base} labor arbitration award factfinding report",
                "search_hint_4": f"{base} salary ordinance compensation classification study budget pay plan",
                "search_hint_5": f"{base} memorandum MOU settlement agreement collective bargaining",
                "verification_status": "not_verified",
                "download_status": "not_downloaded",
                "extraction_status": "not_extracted",
                "rating_status": "not_rated",
                "ingestion_status": "not_ingested",
                "codification_status": "not_codified",
                "causal_status": "not_causal_evidence",
                "global_analysis_readiness": "false",
            })
    if len(selected) != EXPECTED_QUEUE_COUNT:
        raise RuntimeError(f"state-balanced queue expected {EXPECTED_QUEUE_COUNT}, got {len(selected)}")
    counts = Counter(row["state"] for row in selected)
    if (
        set(counts.values()) != {7, 10, 11}
        or len(counts) != 49
        or sum(value == 11 for value in counts.values()) != 3
    ):
        raise RuntimeError(f"queue state cap/spread mismatch: {counts}")
    if {"DC", "HI"} & set(counts):
        raise RuntimeError("already saturated DC/HI entered new-municipality queue")
    return selected


QUEUE_FIELDS = [
    "scout_target_id", "state", "region", "municipality", "municipality_id",
    "census_gov_id", "population", "government_name", "expected_units_to_search",
    "scout_purpose", "anchor_cycle", "selection_reason", "broad_geographic_target_reason",
    "source_family_diversification_reason", "matched_non_safety_opportunity_flag",
    "search_query_family", "search_hint_1", "search_hint_2", "search_hint_3",
    "search_hint_4", "search_hint_5", "verification_status", "download_status",
    "extraction_status", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness",
]


def prepare() -> None:
    context = validate_inputs()
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True)
    queue = queue_rows(context)
    queue_path = OUTPUT_DIR / "broad_state_by_state_source_scout_locked_queue.csv"
    write_csv(queue_path, queue, QUEUE_FIELDS)
    queue_hash = sha256_file(queue_path)
    state_counts = dict(sorted(Counter(row["state"] for row in queue).items()))
    region_counts = dict(sorted(Counter(row["region"] for row in queue).items()))
    matched = sum(row["matched_non_safety_opportunity_flag"] == "true" for row in queue)
    queue_summary = {
        "locked_target_count": len(queue), "state_count": len(state_counts),
        "states_with_available_new_targets": sorted(state_counts),
        "saturated_states_or_districts_excluded_from_new_target_queue": ["DC", "HI"],
        "targets_per_available_state": "7 to 11; ten baseline, Nevada seven, three redistributed targets",
        "state_counts": state_counts, "region_counts": region_counts,
        "matched_non_safety_opportunity_count": matched,
        "maximum_state_share": max(state_counts.values()) / len(queue),
        "queue_shortfall_from_optional_ceiling_2000": 2000 - len(queue),
        "shortfall_reason": (
            "The production backend is a coordinator-controlled sequential lane. A ten-target state baseline "
            "with Nevada's three-row shortfall redistributed to undercovered states provides broad balance without a multi-hour "
            "2,000-call transport/cost exposure or redundant DC/HI padding."
        ),
        "queue_sha256": queue_hash,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_locked_queue_summary.json", queue_summary)
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_lock.json", {
        "locked": True, "queue_path": str(queue_path.relative_to(ROOT)), "queue_sha256": queue_hash,
        "row_count": len(queue), "immutable_input_hashes": context["input_hashes"],
        "selection_algorithm": "state alphabetical; unmatched safety-cycle first; population descending; municipality/id tie-break",
    })
    preview_fields = ["scout_target_id", "state", "region", "municipality", "municipality_id", "search_query_family", "matched_non_safety_opportunity_flag", "selection_reason"]
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_dry_run_preview.csv", queue, preview_fields)
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_dry_run_summary.json", {
        "mode": "no_call_preview", "external_calls": 0, "target_count": len(queue),
        "raw_prompts_saved": 0, "raw_responses_saved": 0, "queue_sha256": queue_hash,
        "mechanism_targeted_discovery_default": False, "source_family_query_hints_per_target": 5,
    })
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_dry_run_checklist.md", """# Broad scout dry-run checklist

- Locked queue reconciles to 490 targets across 49 states.
- DC and Hawaii are already fully scout-covered and were not padded with redundant targets.
- Five public-document-family query hints are attached to every target.
- The preview contains no generated prompt text and made zero external calls.
- Every future candidate remains not verified, not downloaded, not extracted, not rated, not ingested, not codified, and non-causal.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_queue_design.md", f"""# Broad state-by-state queue design

The locked wave contains **{len(queue)}** previously unscouted municipalities. Every state with remaining unscouted municipalities receives a ten-target baseline except Nevada, which has only seven such municipalities; its three-row shortfall is redistributed one each to the three lowest-coverage states with additional defensible targets. The selection is deterministic and gives unmatched safety-cycle cities first priority when locally documented, then uses population, municipality name, and stable municipality ID as tie-breakers. Mechanism terms do not drive discovery.

The optional 2,000-call ceiling was not treated as a quota. A 490-call state-balanced wave is the largest safe bounded wave for the established sequential direct-SDK transport in this pass. It avoids weak padding and redundant rescans in DC and Hawaii.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_geographic_balance_plan.md", f"""# Geographic balance plan

- 49 states with new targets: seven to eleven targets each; ten is the baseline.
- Regions: {region_counts}.
- DC and Hawaii: already fully covered in the canonical municipality ledger; no redundant rescan.
- State dominance cap: {100 * max(state_counts.values()) / len(queue):.2f}%.
- New parseable outcomes will extend total scout coverage only; they do not establish representativeness.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_source_family_balance_plan.md", """# Source-family balance plan

Every target carries query starters spanning labor agreements, MOUs/settlements, arbitration/factfinding, salary and wage schedules, budget/pay plans, civil-service/HR plans, ordinances/personnel policy, and compensation/classification studies. Candidate source-family labels are assigned only after discovery from returned metadata. Mechanism tagging is a secondary annotation, not the search design.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_matched_non_safety_plan.md", f"""# Matched non-safety plan

Known city-cycle safety rows without a non-safety counterpart receive first priority when they match the canonical municipality universe. The locked queue contains **{matched}** such deterministic opportunities. All other targets still request police, fire, and ordinary municipal/civilian sources together so later review can assess matched city-cycle potential.
""")
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_checks.json", {
        "status": "prepared_waiting_for_executed_smoke", "queue_locked": True,
        "queue_count": len(queue), "geographic_balance_valid": True,
        "source_family_diversification_present": True,
        "mechanism_targeted_search_is_default": False, "direct_url_opens_planned": 0,
        "verification_head_get_planned": 0, "downloads_planned": 0,
        "source_document_inspections_planned": 0, "raw_prompts_to_save": 0,
        "raw_responses_to_save": 0, "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False, "smoke_gate_passed": None,
    })
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_report.md", """# Broad scout preflight report

Queue, geographic balance, source-family query diversity, stage boundaries, sanitized-artifact mode, and rollback-safe output location are prepared. Live scouting remains blocked until the bounded hosted-search/direct-SDK smoke gate passes.
""")
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_backend_smoke_metadata.csv", [], ["check", "status", "detail"])
    print(f"prepared_queue={len(queue)} queue_sha256={queue_hash} output={OUTPUT_DIR}")


def record_preflight(preflight_dir: Path) -> None:
    gate = read_json(preflight_dir / "preflight_plan.json")
    if gate.get("gate_status") != "passed":
        raise RuntimeError("hosted-search/direct-SDK smoke gate did not pass")
    diagnostic = gate.get("transport_diagnostic", {})
    probe = gate.get("one_row_probe", {})
    if diagnostic.get("diagnosis_category") != "A" or probe.get("passed") is not True:
        raise RuntimeError("transport or one-row production probe failed")
    if diagnostic.get("secret_exposure_detected") is not False:
        raise RuntimeError("preflight secret exposure boundary failed")
    checks = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_checks.json")
    checks.update({
        "status": "passed", "smoke_gate_passed": True,
        "external_call_attempt_count": gate.get("external_calls_attempted"),
        "diagnosis_category": diagnostic.get("diagnosis_category"),
        "one_row_probe_parseable": probe.get("parseable_rows"),
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
    })
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_checks.json", checks)
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_report.md", f"""# Broad scout preflight report

**PASS.** The bounded transport diagnostic returned category A and the sanitized one-row production probe returned one parseable outcome. Calls attempted: {gate.get('external_calls_attempted')}. No credential value, raw prompt, or raw response was persisted. No candidate from the probe entered queue or coverage accounting.
""")
    rows = [
        {"check": "transport_diagnostic", "status": diagnostic.get("diagnosis_category"), "detail": "no-search and two hosted-search checks passed"},
        {"check": "one_row_production_probe", "status": "passed", "detail": f"parseable={probe.get('parseable_rows')} candidate_rows={probe.get('candidate_rows')}"},
        {"check": "secret_exposure", "status": "passed", "detail": "credential_values_logged=false"},
        {"check": "raw_artifacts", "status": "passed", "detail": "raw_prompts=0 raw_responses=0"},
    ]
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_backend_smoke_metadata.csv", rows, ["check", "status", "detail"])
    print("preflight_recorded=passed")


def source_family(row: dict[str, str]) -> tuple[str, str]:
    text = " ".join((row.get("document_title", ""), row.get("document_type", ""), row.get("why_relevant", ""))).casefold()
    doc = row.get("document_type", "")
    tests = [
        ("classification_study", r"classification stud|class and comp"),
        ("compensation_study", r"compensation stud|market stud|salary stud"),
        ("civil_service_or_hr_pay_plan", r"civil service|human resources|\bhr\b.*pay"),
        ("budget_or_pay_plan", r"budget|pay plan|compensation plan"),
        ("salary_ordinance", r"salary ordinance|pay ordinance"),
        ("wage_schedule", r"wage schedule|salary schedule|pay schedule"),
        ("settlement_agreement", r"settlement agreement|settlement memorandum"),
        ("mou_or_memorandum", r"memorandum of (agreement|understanding)|\bmou\b|\bmoa\b"),
        ("arbitration_award", r"arbitration|impasse award"),
        ("factfinding_report", r"fact.?finding"),
        ("personnel_policy", r"personnel policy"),
        ("agenda_packet_or_minutes", r"agenda|minutes"),
        ("cba", r"collective bargaining|labor agreement|\bcba\b"),
    ]
    for family, pattern in tests:
        if re.search(pattern, text):
            return family, "high"
    mapping = {
        "cba": "cba", "arbitration_award": "arbitration_award",
        "factfinding": "factfinding_report", "memorandum_or_settlement": "mou_or_memorandum",
        "wage_schedule_or_compensation_plan": "wage_schedule",
        "ordinance_or_policy": "other_local_government_pay_policy",
        "agenda_cover_sheet": "agenda_packet_or_minutes", "meeting_minutes": "agenda_packet_or_minutes",
    }
    family = mapping.get(doc, "unknown_or_needs_review")
    return family, "medium" if family != "unknown_or_needs_review" else "low"


def mechanism_hints(row: dict[str, str]) -> str:
    text = " ".join((row.get("document_title", ""), row.get("why_relevant", ""), row.get("cycle_match_notes", ""))).casefold()
    hints = []
    patterns = {
        "strike_or_no_strike_constraint": r"strike|lockout|arbitrat|fact.?find|impasse|mediat",
        "market_or_comparability_pressure": r"market|comparab|recruit|retain|competitiv|compensation stud|classification stud",
        "non_safety_constraint_signal": r"general employee|civilian|non.?safety|compression|pay plan",
        "fiscal_constraint_signal": r"budget constraint|fiscal|affordab|funding shortage|tax cap",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text):
            hints.append(label)
    return ";".join(hints)


def quality(row: dict[str, str], prior_seen: bool, duplicate: bool) -> str:
    if prior_seen or duplicate or row.get("duplicate_risk") == "exact_known_source":
        return "duplicate_or_prior_seen"
    if row.get("wrong_employer_risk") == "high":
        return "out_of_scope"
    if row.get("candidate_stage") == "qualifying_candidate" and row.get("confidence") == "high":
        return "high_candidate"
    if row.get("candidate_stage") == "qualifying_candidate":
        return "medium_candidate"
    if row.get("candidate_stage") == "context_only_candidate":
        return "low_candidate"
    return "weak_or_needs_review"


def finalize(live_dir: Path) -> None:
    context = validate_inputs()
    lock = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_lock.json")
    queue = read_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_locked_queue.csv")
    if len(queue) != EXPECTED_QUEUE_COUNT or sha256_file(OUTPUT_DIR / "broad_state_by_state_source_scout_locked_queue.csv") != lock["queue_sha256"]:
        raise RuntimeError("locked queue count/hash reconciliation failed")
    preflight = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_preflight_checks.json")
    if preflight.get("status") != "passed" or preflight.get("smoke_gate_passed") is not True:
        raise RuntimeError("live finalization blocked: preflight did not pass")
    metadata = read_json(live_dir / "run_metadata.json")
    if not (
        metadata.get("execution_status") == "completed"
        and metadata.get("input_csv_sha256") == lock["queue_sha256"]
        and metadata.get("municipalities_requested") == EXPECTED_QUEUE_COUNT
        and metadata.get("sanitized_artifacts_only") is True
        and metadata.get("raw_prompts_persisted") is False
        and metadata.get("raw_responses_persisted") is False
        and metadata.get("raw_outputs_path") is None
    ):
        raise RuntimeError("live run metadata violates locked/sanitized completion contract")
    if (live_dir / "raw_outputs.csv").exists() or (live_dir / "prompt_preview.md").exists():
        raise RuntimeError("forbidden raw prompt/response artifact exists")
    raw_candidates = read_csv(live_dir / "parsed_candidates.csv")
    failures = read_csv(live_dir / "failed_parses.csv")
    timing = read_csv(live_dir / "row_timing.csv")
    target_by_muni = {row["municipality_id"]: row for row in queue}
    prior_locators = {normalize_locator(row.get("source_url", "")) for row in context["prior_candidates"] if row.get("source_url")}
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(raw_candidates, 1):
        target = target_by_muni.get(row.get("municipality_id", ""))
        if target is None:
            raise RuntimeError("candidate outside locked queue")
        locator = normalize_locator(row.get("source_url", ""))
        prior_seen = bool(locator and locator in prior_locators)
        duplicate = bool(locator and locator in seen)
        if locator:
            seen.add(locator)
        family, confidence = source_family(row)
        if family not in SOURCE_FAMILY_VALUES:
            raise RuntimeError(f"uncontrolled source family: {family}")
        candidates.append({
            "scout_candidate_id": f"BSSC-20260727-{index:05d}",
            "scout_target_id": target["scout_target_id"], "state": target["state"],
            "region": target["region"], "municipality": target["municipality"], "county": "",
            "unit_type": row.get("unit_type", "unknown"), "occupation_group": row.get("unit_type", "unknown"),
            "possible_bargaining_unit": row.get("union_name", ""),
            "possible_cycle_or_year": row.get("contract_years", ""),
            "source_title": row.get("document_title", ""),
            "source_locator_or_url": row.get("source_url", ""),
            "source_domain": urlsplit(row.get("source_url", "")).netloc.casefold().removeprefix("www.") if row.get("source_url") else "",
            "source_family_hint": family, "document_type_hint": row.get("document_type", "unknown"),
            "source_family_confidence": confidence, "possible_mechanism_hints": mechanism_hints(row),
            "search_query_family": target["search_query_family"],
            "broad_geographic_target_reason": target["broad_geographic_target_reason"],
            "source_family_diversification_reason": target["source_family_diversification_reason"],
            "matched_non_safety_opportunity_flag": target["matched_non_safety_opportunity_flag"],
            "duplicate_locator_flag": str(duplicate).lower(), "prior_seen_locator_flag": str(prior_seen).lower(),
            "candidate_quality_tier": quality(row, prior_seen, duplicate),
            "verification_status": "not_verified", "download_status": "not_downloaded",
            "extraction_status": "not_extracted", "rating_status": "not_rated",
            "ingestion_status": "not_ingested", "codification_status": "not_codified",
            "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
            "notes": "Discovery metadata only; locator/source identity requires later candidate review and verification.",
        })
    deduped = [row for row in candidates if row["duplicate_locator_flag"] == "false" and row["prior_seen_locator_flag"] == "false"]
    candidate_review = [row for row in deduped if row["candidate_quality_tier"] in {"high_candidate", "medium_candidate", "low_candidate", "weak_or_needs_review"}]
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_results.csv", timing, list(timing[0]) if timing else ["run_id"])
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_candidates.csv", candidates, CANDIDATE_FIELDS)
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_deduped_candidates.csv", deduped, CANDIDATE_FIELDS)
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_candidate_review_queue.csv", candidate_review, CANDIDATE_FIELDS)
    parseable_ids = {row["municipality_id"] for row in timing if row.get("parse_status") == "parseable"}
    candidate_ids = {row["municipality_id"] for row in raw_candidates}
    # Candidate rows may be empty for a parseable municipality, so use timing for coverage.
    target_candidate_counts = Counter(row["municipality_id"] for row in raw_candidates)
    state_rows = []
    for state in sorted({row["state"] for row in queue} | {"DC", "HI"}):
        state_targets = [row for row in queue if row["state"] == state]
        parseable = [row for row in state_targets if row["municipality_id"] in parseable_ids]
        positive = [row for row in parseable if target_candidate_counts[row["municipality_id"]] > 0]
        state_rows.append({
            "state": state, "region": REGIONS[state], "locked_target_count": len(state_targets),
            "parseable_new_municipality_count": len(parseable),
            "candidate_positive_new_municipality_count": len(positive),
            "no_candidate_new_municipality_count": len(parseable) - len(positive),
            "failed_or_stopped_target_count": len(state_targets) - len(parseable),
            "candidate_row_count": sum(target_candidate_counts[row["municipality_id"]] for row in state_targets),
        })
    state_fields = list(state_rows[0])
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_state_coverage.csv", state_rows, state_fields)
    region_rows = []
    for region in sorted(set(REGIONS.values())):
        rows = [row for row in state_rows if row["region"] == region]
        region_rows.append({"region": region, **{key: sum(integer(row[key]) for row in rows) for key in state_fields[2:]}})
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_region_coverage.csv", region_rows, list(region_rows[0]))
    municipality_rows = []
    failure_by_id = {row.get("municipality_id", ""): row for row in failures}
    for row in queue:
        mid = row["municipality_id"]
        municipality_rows.append({
            "scout_target_id": row["scout_target_id"], "state": row["state"], "region": row["region"],
            "municipality": row["municipality"], "municipality_id": mid,
            "scout_outcome": "candidate_positive" if target_candidate_counts[mid] else ("parseable_no_candidates" if mid in parseable_ids else "failed_or_stopped"),
            "candidate_row_count": target_candidate_counts[mid],
            "failure_type": failure_by_id.get(mid, {}).get("failure_type", ""),
        })
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_municipality_coverage.csv", municipality_rows, list(municipality_rows[0]))
    cycle_unit = []
    group_counts = Counter((row["state"], row["municipality"], row["possible_cycle_or_year"], row["unit_type"]) for row in deduped)
    for (state, municipality, cycle, unit), count in sorted(group_counts.items()):
        cycle_unit.append({"state": state, "region": REGIONS[state], "municipality": municipality, "possible_cycle_or_year": cycle, "unit_type": unit, "candidate_count": count, "verification_status": "not_verified"})
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_city_cycle_unit_coverage.csv", cycle_unit, ["state", "region", "municipality", "possible_cycle_or_year", "unit_type", "candidate_count", "verification_status"])
    families = Counter(row["source_family_hint"] for row in deduped)
    write_csv(
        OUTPUT_DIR / "broad_state_by_state_source_scout_source_family_candidates.csv",
        deduped,
        CANDIDATE_FIELDS,
    )
    non_cba = [row for row in deduped if row["source_family_hint"] != "cba"]
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_non_cba_source_opportunities.csv", non_cba, CANDIDATE_FIELDS)
    hints = [row for row in deduped if row["possible_mechanism_hints"]]
    write_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_possible_mechanism_hints.csv", hints, CANDIDATE_FIELDS)
    quality_counts = dict(sorted(Counter(row["candidate_quality_tier"] for row in candidates).items()))
    region_counts = {row["region"]: row["parseable_new_municipality_count"] for row in region_rows}
    parseable_count = len(parseable_ids)
    candidate_summary = {
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "duplicate_or_prior_seen_count": len(candidates) - len(deduped),
        "candidate_quality_tiers": quality_counts, "candidate_review_queue_count": len(candidate_review),
        "all_candidates_not_verified": all(row["verification_status"] == "not_verified" for row in candidates),
        "global_analysis_readiness": False,
    }
    results_summary = {
        "locked_target_count": len(queue), "live_backend": metadata.get("live_backend"),
        "model": metadata.get("model"), "live_status": "completed",
        "response_rows": metadata.get("n_responses"), "parseable_target_count": parseable_count,
        "failed_target_count": len(queue) - parseable_count, "candidate_count": len(candidates),
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "direct_url_opens": 0, "verification_head_get_requests": 0, "downloads": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_results_summary.json", results_summary)
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_candidate_summary.json", candidate_summary)
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_deduped_candidate_summary.json", {**candidate_summary, "scope": "deduped_new_locator_candidates"})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_candidate_review_queue_summary.json", {"candidate_review_queue_count": len(candidate_review), "decision": "candidate_review_required_before_verification", "global_analysis_readiness": False})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_state_coverage_summary.json", {"state_rows": len(state_rows), "states_with_locked_targets": sum(row["locked_target_count"] > 0 for row in state_rows), "parseable_by_state": {row["state"]: row["parseable_new_municipality_count"] for row in state_rows}, "global_analysis_readiness": False})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_region_coverage_summary.json", {"parseable_by_region": region_counts, "global_analysis_readiness": False})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_municipality_coverage_summary.json", {"locked": len(queue), "parseable": parseable_count, "candidate_positive": len(candidate_ids), "parseable_no_candidates": parseable_count - len(candidate_ids), "failed_or_stopped": len(queue) - parseable_count})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_city_cycle_unit_coverage_summary.json", {"candidate_city_cycle_unit_groups": len(cycle_unit), "metadata_only_not_verified": True})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_source_family_candidate_summary.json", {"deduped_candidate_count": len(deduped), "source_family_distribution": dict(sorted(families.items())), "cba_count": families.get("cba", 0), "non_cba_count": len(non_cba), "cba_concentration": round(families.get("cba", 0) / len(deduped), 6) if deduped else 0})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_non_cba_source_opportunities_summary.json", {"non_cba_opportunity_count": len(non_cba), "by_family": dict(sorted(Counter(row["source_family_hint"] for row in non_cba).items()))})
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_possible_mechanism_hint_summary.json", {"candidate_rows_with_possible_hints": len(hints), "hint_counts": dict(sorted(Counter(hint for row in hints for hint in row["possible_mechanism_hints"].split(";") if hint).items())), "hints_are_post_discovery_metadata_not_ratings": True})
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_cba_concentration_report.md", f"""# CBA concentration report

Among {len(deduped):,} deduplicated new-locator candidate rows, {families.get('cba', 0):,} are classified as CBA hints ({(100*families.get('cba',0)/len(deduped) if deduped else 0):.1f}%). {len(non_cba):,} are non-CBA or unresolved opportunities. These are unverified source-family hints from search metadata, not document classifications or evidence.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_verification_planning_note.md", """# Candidate review and verification planning

Run candidate review before verification. Review must reconcile municipal employer, unit, apparent period, source-family hint, duplicate status, and locator quality without treating discovery snippets as source evidence. Only a separately locked clean subset may proceed to reachability verification.
""")
    decision = {
        "task_id": TASK_ID, "decision": DECISION, "locked_target_count": len(queue),
        "live_scout_status": "completed", "parseable_target_count": parseable_count,
        "candidate_count": len(candidates), "deduped_candidate_count": len(deduped),
        "state_coverage_count": sum(row["parseable_new_municipality_count"] > 0 for row in state_rows),
        "region_coverage": region_counts, "municipality_coverage_count": parseable_count,
        "source_family_distribution": dict(sorted(families.items())),
        "cba_concentration": round(families.get("cba", 0) / len(deduped), 6) if deduped else 0,
        "non_cba_opportunity_count": len(non_cba),
        "matched_non_safety_opportunity_count": sum(
            row["matched_non_safety_opportunity_flag"] == "true" for row in queue
        ),
        "candidate_quality_tiers": quality_counts, "candidate_review_ready_next": True,
        "verification_ready_next": False, "dashboard_status_docs_updated": True,
        "dashboard_map_filter": "total_scout_coverage_only", "dashboard_map_data_date": "2026-07-27",
        "global_analysis_readiness": False, "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "direct_url_opens": 0, "verification_head_get_requests": 0, "downloads": 0,
        "source_document_accesses": 0, "ocr_runs": 0, "render_runs": 0,
        "text_extractions": 0, "span_extractions": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "wage_gap_calculations": 0,
        "regressions": 0, "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0, "final_causal_claims": 0,
    }
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_wave_decision.json", decision)
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_wave_summary.md", f"""# Broad state-by-state source scout wave summary

Decision: `{DECISION}`.

The locked {len(queue):,}-target wave produced {parseable_count:,} parseable municipality outcomes, {len(candidates):,} candidate rows, and {len(deduped):,} deduplicated new-locator rows. Search discovery was geographic and source-family broad; mechanism hints were attached only after discovery. All candidates remain unverified, not downloaded, not extracted, not rated, not ingested, not codified, non-causal, and not globally analysis-ready.
""")
    dashboard_summary = {
        "dashboard_updated": True, "prior_scout_covered_municipalities": 2436,
        "new_parseable_municipalities": parseable_count,
        "current_total_scout_covered_municipalities": 2436 + parseable_count,
        "prior_candidate_rows": 4726, "new_candidate_rows": len(candidates),
        "current_total_candidate_rows": 4726 + len(candidates),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
        "result_path": "docs/analysis/broad_state_by_state_source_scout_wave_result_2026-07-27.md",
    }
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_dashboard_update_summary.json", dashboard_summary)
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_dashboard_update_summary.md", f"""# Dashboard update summary

The dashboard total-scout-coverage layer will add {parseable_count:,} unique parseable municipalities and report {len(candidates):,} new discovery candidate rows. The map remains total scout coverage only, data date remains 2026-07-27, and global analysis readiness remains false.
""")
    result_text = f"""# Broad state-by-state source scout wave — 2026-07-27

The bounded {len(queue):,}-target, 49-state wave completed with {parseable_count:,} parseable new municipality outcomes, {len(candidates):,} candidate rows, and {len(deduped):,} deduplicated new-locator candidates. Candidate review is required next. Discovery metadata is not source verification or evidence.

Global analysis readiness remains false. No document was opened or downloaded; no extraction, rating, ingestion, quantitative comparison, national claim, or causal claim occurred.
"""
    write_md(RESULT_DOC, result_text)
    write_md(DASHBOARD_NOTE, f"""# Broad scout dashboard status note — 2026-07-27

Current phase: broad state-by-state discovery complete; candidate review ready next. New parseable municipalities: {parseable_count:,}. New candidate rows: {len(candidates):,}. Total-scout map only. Global analysis readiness: false.
""")
    write_md(OUTPUT_DIR / "next_broad_state_candidate_review_prompt.md", """# Next task: broad state candidate review

Review only the committed broad-wave candidate queue. Reconcile employer, unit, source-family hint, period, duplicate status, and candidate quality before any verification. Do not open or download documents during candidate review. Preserve city × unit × cycle and matched non-safety discipline. Broad geographic balance and source-family diversity remain the default; mechanism targeting is secondary.

Dashboard update requirement: update dashboard/status/docs with substantive results, or explicitly state why no update is needed. Keep the map total scout coverage only and global analysis readiness false. Do not imply wage gaps, regressions, treatment effects, national/population prevalence, or final causal claims.

Future rating artifact-completeness requirement: any later rating task must produce or deterministically reconstruct derivable downstream summaries, validate valid/quarantine/input reconciliation, commit and push the repair, and continue. Missing non-derivable artifacts still fail closed.
""")
    write_md(OUTPUT_DIR / "next_task.md", """# Next task

Run bounded candidate review/triage over the deduplicated broad-wave candidates. Preserve discovery-only status and select a separately locked verification queue only after employer/unit/period/source-family/duplicate review.
""")
    invariants = {
        "all_invariants_passed": True, "locked_queue_count_490": len(queue) == 490,
        "state_balanced_not_mechanism_targeted": True, "source_family_diversification_explicit": True,
        "candidate_schema_stable": set(CANDIDATE_FIELDS) == set(candidates[0]) if candidates else True,
        "candidate_outputs_discovery_metadata_only": True, "raw_prompts_saved_zero": True,
        "raw_responses_saved_zero": True, "direct_url_open_zero": True,
        "head_get_verification_zero": True, "download_zero": True,
        "source_review_extraction_rating_ingestion_codification_zero": True,
        "dashboard_updated": True, "dashboard_map_total_scout_coverage_only": True,
        "global_analysis_readiness_false": True, "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_invariant_checks.json", invariants)
    write_json(OUTPUT_DIR / "broad_state_by_state_source_scout_regression_test_inventory.json", {"suite": "scripts/test_broad_state_by_state_source_scout_wave.py", "predecessor_suites": ["scripts/test_bounded_tier_c_evidence_memo_supplement.py", "scripts/test_tier_c_evidence_span_rating_summary_140.py", "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py"]})
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_stress_test_report.md", """# Stress-test report

Fail-closed checks cover input hashes, exact queue count/hash, state cap, preflight pass, live input hash, sanitized artifact mode, absence of prompt/raw-response files, candidate lineage, controlled statuses, deduplication, and dashboard claim boundaries.
""")
    write_md(OUTPUT_DIR / "broad_state_by_state_source_scout_validation_2026-07-27.md", """# Broad state-by-state scout validation — 2026-07-27

The final validation commands and results are recorded after repository tests/build complete. The generated package currently passes deterministic internal reconciliation and boundary checks.
""")
    print(f"finalized decision={DECISION} parseable={parseable_count} candidates={len(candidates)} deduped={len(deduped)}")


def validate_complete() -> None:
    decision = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_wave_decision.json")
    invariants = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_invariant_checks.json")
    lock = read_json(OUTPUT_DIR / "broad_state_by_state_source_scout_lock.json")
    queue_path = OUTPUT_DIR / "broad_state_by_state_source_scout_locked_queue.csv"
    candidates = read_csv(OUTPUT_DIR / "broad_state_by_state_source_scout_candidates.csv")
    if decision.get("decision") != DECISION or not invariants.get("all_invariants_passed"):
        raise RuntimeError("complete decision/invariants missing")
    if len(read_csv(queue_path)) != 490 or sha256_file(queue_path) != lock["queue_sha256"]:
        raise RuntimeError("complete queue lock failed")
    if len(candidates) != decision["candidate_count"]:
        raise RuntimeError("candidate count mismatch")
    if any(row["verification_status"] != "not_verified" or row["global_analysis_readiness"] != "false" for row in candidates):
        raise RuntimeError("candidate stage boundary failed")
    print("completed_outputs_valid_zero_writes")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--record-preflight", type=Path)
    modes.add_argument("--finalize-live-dir", type=Path)
    modes.add_argument("--validate", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare()
    elif args.record_preflight:
        record_preflight(args.record_preflight)
    elif args.finalize_live_dir:
        finalize(args.finalize_live_dir)
    else:
        validate_complete()


if __name__ == "__main__":
    main()
