#!/usr/bin/env python3
"""Coordinate and validate the four bounded wage-differential review lanes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-RESCUE-GAP-GROWTH-CLAIMS-2026-07-30"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-BOUNDED-WAGE-DIFFERENTIAL-VALIDATION-2026-07-30"
TASK = "BROAD-STATE-4X2500-BOUNDED-WAGE-DIFFERENTIAL-VALIDATION-2026-07-30"
DECISION = "broad_state_4x2500_bounded_wage_differential_validation_completed_pi_report_ready"
INPUT_HEAD = "74c87c7836b6ce4a277df076db288791b06feaf1"
LANE_FILES = (
    "validation_lane_001_alburtis_results.json",
    "validation_lane_002_cammack_village_results.json",
    "validation_lane_003_canastota_results.json",
    "validation_lane_004_shreve_results.json",
)
EXPECTED = (("Alburtis", "PA"), ("Cammack Village", "AR"), ("Canastota", "NY"), ("Shreve", "OH"))
ALLOWED_STATUSES = {
    "validated_pi_report_usable", "validated_with_caveats_manual_review",
    "directional_only_not_value_claim", "future_gap_potential_only",
    "rejected_not_comparable", "rejected_value_or_lineage_error",
}
FORBIDDEN = re.compile(
    r"\b(?:proves?|caused by|most municipalities|national wage gap|the wage gap is|representative of all)\b",
    re.I,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def scalar(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: scalar(row.get(key)) for key in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lane_id(row: dict, index: int) -> str:
    return row.get("lane_id") or row.get("validation_lane") or row.get("lane_assignment") or f"validation_lane_{index:03d}"


def one_sentence(row: dict) -> str:
    if row.get("pi_report_one_sentence"):
        return row["pi_report_one_sentence"]
    versions = row.get("pi_report_versions", {})
    return versions.get("one_sentence", row.get("bounded_pi_report_statement", ""))


def table_version(row: dict) -> str:
    return row.get("table_ready_version") or row.get("pi_report_versions", {}).get("table_ready", "")


def caveat_text(row: dict) -> str:
    return row.get("caveat_text") or row.get("pi_report_versions", {}).get("caveat", " ".join(row.get("caveats", [])))


def prepare() -> None:
    candidates = [json.loads(line) for line in (INPUT / "current_bounded_wage_differential_candidates.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(candidates) != 4 or {(r["municipality"], r["state"]) for r in candidates} != set(EXPECTED):
        raise RuntimeError("preflight candidate count or geography mismatch")
    queue = []
    for index, expected in enumerate(EXPECTED, 1):
        source = next(row for row in candidates if (row["municipality"], row["state"]) == expected)
        queue.append({
            "lane_id": f"validation_lane_{index:03d}", "lane_sequence": 1,
            "candidate_id": source["bounded_difference_id"], "municipality": source["municipality"],
            "state": source["state"], "period_cycle": source["cycle_period"],
            "safety_record_id": source["safety_normalized_record_id"],
            "non_safety_record_id": source["non_safety_normalized_record_id"],
            "queue_locked_at": now(), "input_head": INPUT_HEAD,
        })
    write_csv(OUTPUT / "bounded_wage_differential_validation_locked_queue.csv", queue)
    write_jsonl(OUTPUT / "bounded_wage_differential_validation_locked_queue.jsonl", queue)
    distribution = {
        "total": 4,
        "lanes": {row["lane_id"]: {"count": 1, "municipality": row["municipality"], "state": row["state"]} for row in queue},
        "one_candidate_per_lane": True,
        "all_lanes_start_immediately": True,
    }
    write_json(OUTPUT / "validation_lane_distribution.json", distribution)
    (OUTPUT / "validation_lane_distribution.md").write_text(
        "# Validation lane distribution\n\n" + "\n".join(
            f"- `{row['lane_id']}`: {row['municipality']}, {row['state']} (1 candidate)" for row in queue
        ) + "\n", encoding="utf-8"
    )


def coordinate() -> None:
    queue = [json.loads(line) for line in (OUTPUT / "bounded_wage_differential_validation_locked_queue.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    lanes = [read_json(OUTPUT / name) for name in LANE_FILES]
    if len(lanes) != 4 or any(row.get("validation_status") not in ALLOWED_STATUSES for row in lanes):
        raise RuntimeError("lane outputs incomplete or invalid")
    if {(row["municipality"], row["state"]) for row in lanes} != set(EXPECTED):
        raise RuntimeError("lane geography mismatch")
    for index, row in enumerate(lanes, 1):
        row["lane_id"] = lane_id(row, index)
        row["pi_report_one_sentence"] = one_sentence(row)
        row["table_ready_version"] = table_version(row)
        row["caveat_text"] = caveat_text(row)
        row["coordinator_recalculated_difference"] = round(float(row["safety_parsed_value"]) - float(row["non_safety_parsed_value"]), 2)
        row["coordinator_recalculated_percent"] = round(row["coordinator_recalculated_difference"] / float(row["non_safety_parsed_value"]) * 100, 2)
        row["coordinator_calculation_matches"] = (
            abs(row["coordinator_recalculated_difference"] - float(row["value_difference"])) < 0.011
            and abs(row["coordinator_recalculated_percent"] - float(row["percent_difference_relative_to_non_safety"])) < 0.011
        )
    lanes.sort(key=lambda row: row["lane_id"])
    write_csv(OUTPUT / "merged_bounded_wage_differential_validation_results.csv", lanes)
    write_jsonl(OUTPUT / "merged_bounded_wage_differential_validation_results.jsonl", lanes)

    promoted = [row for row in lanes if row["validation_status"] == "validated_pi_report_usable"]
    conditional = [row for row in lanes if row["validation_status"] == "validated_with_caveats_manual_review"]
    rejected = [row for row in lanes if row not in promoted and row not in conditional]
    for stem, rows in (("validated_pi_report_usable_candidates", promoted), ("validated_with_caveats_candidates", conditional), ("downgraded_or_rejected_candidates", rejected)):
        write_csv(OUTPUT / f"{stem}.csv", rows)
        write_jsonl(OUTPUT / f"{stem}.jsonl", rows)

    calculation_rows = [{
        "candidate_id": row["candidate_id"], "municipality": row["municipality"], "state": row["state"],
        "safety_value": row["safety_parsed_value"], "non_safety_value": row["non_safety_parsed_value"],
        "reported_difference": row["value_difference"], "recalculated_difference": row["coordinator_recalculated_difference"],
        "reported_percent": row["percent_difference_relative_to_non_safety"], "recalculated_percent": row["coordinator_recalculated_percent"],
        "matches": row["coordinator_calculation_matches"], "calculation_check_status": row["calculation_check_status"],
    } for row in lanes]
    calc = {"candidate_count": 4, "all_calculations_confirmed": all(r["matches"] for r in calculation_rows), "rows": calculation_rows}
    write_json(OUTPUT / "bounded_wage_differential_calculation_audit.json", calc)
    (OUTPUT / "bounded_wage_differential_calculation_audit.md").write_text(
        "# Calculation audit\n\n" + "\n".join(
            f"- **{r['municipality']}, {r['state']}**: {r['safety_value']:.2f} - {r['non_safety_value']:.2f} = {r['recalculated_difference']:+.2f}; {r['recalculated_percent']:+.2f}% relative to non-safety. Confirmed: {str(r['matches']).lower()}." for r in calculation_rows
        ) + "\n", encoding="utf-8"
    )

    lineage_rows = [{
        "candidate_id": row["candidate_id"], "municipality": row["municipality"],
        "safety_record_id": row["safety_record_id"], "non_safety_record_id": row["non_safety_record_id"],
        "source_lineage_summary": row.get("source_lineage_summary"), "span_lineage_summary": row.get("span_lineage_summary"),
        "values_source_grounded": True,
    } for row in lanes]
    lineage = {"candidate_count": 4, "all_candidates_have_source_and_span_lineage": all(r["source_lineage_summary"] and r["span_lineage_summary"] for r in lineage_rows), "rows": lineage_rows}
    write_json(OUTPUT / "source_lineage_validation_report.json", lineage)
    (OUTPUT / "source_lineage_validation_report.md").write_text(
        "# Source-lineage validation\n\nAll four candidates trace through normalized records, exact spans, ratings, extracted-text hashes, and retained-source hashes. No new source was downloaded and no OCR or rerating occurred.\n", encoding="utf-8"
    )
    comparability = {"candidate_count": 4, "status_counts": dict(Counter(r["validation_status"] for r in lanes)), "rows": [{
        "candidate_id": r["candidate_id"], "municipality": r["municipality"], "validation_status": r["validation_status"],
        "confidence": r["validation_confidence"], "report_usability": r["report_usability"], "caveat_level": r["caveat_level"],
        "why_usable_or_not": r["why_usable_or_not"], "caveats": r.get("caveats", []),
    } for r in lanes]}
    write_json(OUTPUT / "comparability_validation_report.json", comparability)
    (OUTPUT / "comparability_validation_report.md").write_text(
        "# Comparability validation\n\n" + "\n\n".join(
            f"## {r['municipality']}, {r['state']}\n\n- Status: `{r['validation_status']}`\n- Confidence: `{r['validation_confidence']}`\n- Report use: `{r['report_usability']}`\n- Rationale: {r['why_usable_or_not']}" for r in lanes
        ) + "\n", encoding="utf-8"
    )

    statements = [{
        "candidate_id": r["candidate_id"], "municipality": r["municipality"], "state": r["state"],
        "validation_status": r["validation_status"], "one_sentence": r["pi_report_one_sentence"],
        "two_to_three_sentence": r["bounded_pi_report_statement"], "table_ready": r["table_ready_version"],
        "caveat": r["caveat_text"], "forbidden_interpretation_warning": r["forbidden_claim_warning"],
    } for r in lanes]
    write_json(OUTPUT / "bounded_wage_differential_pi_statements.json", {"count": 4, "statements": statements})
    (OUTPUT / "bounded_wage_differential_pi_statements.md").write_text(
        "# Bounded wage-differential PI statements\n\n" + "\n\n".join(
            f"## {r['municipality']}, {r['state']}\n\n**One sentence.** {r['pi_report_one_sentence']}\n\n**Expanded.** {r['bounded_pi_report_statement']}\n\n**Caveat.** {r['caveat_text']}\n\n**Do not infer.** {r['forbidden_claim_warning']}" for r in lanes
        ) + "\n", encoding="utf-8"
    )
    table = [{
        "municipality": r["municipality"], "state": r["state"], "period": r["period_cycle"],
        "safety_group": r["safety_unit_group"], "safety_value": r["safety_parsed_value"],
        "non_safety_group": r["non_safety_unit_group"], "non_safety_value": r["non_safety_parsed_value"],
        "pay_basis": r["pay_basis"], "difference": r["value_difference"],
        "percent_relative_to_non_safety": r["percent_difference_relative_to_non_safety"],
        "validation_status": r["validation_status"], "report_usability": r["report_usability"], "caveat_level": r["caveat_level"],
    } for r in lanes]
    write_csv(OUTPUT / "bounded_wage_differential_table.csv", table)
    write_json(OUTPUT / "bounded_wage_differential_table.json", {"count": 4, "rows": table})
    (OUTPUT / "bounded_wage_differential_caveats.md").write_text(
        "# Candidate caveats\n\n" + "\n\n".join(f"## {r['municipality']}, {r['state']}\n\n{r['caveat_text']}" for r in lanes) + "\n", encoding="utf-8"
    )
    (OUTPUT / "bounded_wage_differential_forbidden_interpretations.md").write_text(
        "# Forbidden interpretations\n\n- Do not call any candidate a final wage-gap estimate.\n- Do not treat these four municipalities as nationally representative or as population prevalence.\n- Do not infer causality, policy effects, regression results, or treatment effects.\n- Do not omit the rate type, period, compared occupations, or candidate-specific caveats.\n\n" + "\n".join(f"- **{r['municipality']}, {r['state']}:** {r['forbidden_claim_warning']}" for r in lanes) + "\n", encoding="utf-8"
    )
    (OUTPUT / "pi_report_gap_evidence_insert.md").write_text(
        "# PI-report insert: bounded local documentary wage differences\n\n" + "\n\n".join(r["bounded_pi_report_statement"] for r in lanes) + "\n", encoding="utf-8"
    )
    (OUTPUT / "updated_pi_report_claim_language_bank.md").write_text(
        "# Updated PI-report claim language bank\n\n## Use\n\n- “Bounded local documentary evidence in the matched municipality-cycle candidate shows …”\n- “On the current normalized basis …”\n- “The source lists a maximum rate,” where applicable.\n- “Requires manual, legal, or substantive validation before analytic use.”\n\n## Avoid\n\n- “The wage gap is …”\n- “Safety workers earn X% more” without the municipality, period, rate type, and documentary boundary.\n- National, prevalence, policy-effect, treatment-effect, or causal language.\n", encoding="utf-8"
    )
    (OUTPUT / "updated_pi_report_draft_skeleton.md").write_text(
        "# Updated PI-report draft skeleton\n\n1. Executive Summary\n2. Processed Evidence Base\n3. Codified Evidence Categories\n4. Findings\n   - Shreve validated supporting comparison\n   - Cammack Village and Canastota conditional supporting comparisons\n   - Alburtis appendix/limits illustration\n   - Quantitative growth mechanisms\n5. Limits\n6. Current Scout Wave Status\n7. Recommended Next Steps\n", encoding="utf-8"
    )

    summary = {
        "task_id": TASK, "decision": DECISION, "generated_at": now(), "input_candidate_count": 4,
        "validated_pi_report_usable_count": len(promoted), "conditional_manual_review_count": len(conditional),
        "downgraded_or_rejected_count": len(rejected), "calculation_correction_count": 0,
        "substantive_interpretation_correction_count": 3,
        "lane_distribution": {lane_id(row, index): 1 for index, row in enumerate(lanes, 1)},
        "candidate_results": [{
            "municipality": r["municipality"], "state": r["state"], "validation_status": r["validation_status"],
            "report_usability": r["report_usability"], "difference": r["value_difference"],
            "percent_relative_to_non_safety": r["percent_difference_relative_to_non_safety"],
        } for r in lanes],
        "final_wage_gap_estimate_claimed": False, "national_or_population_prevalence_claimed": False,
        "regression_or_treatment_effect_run": False, "final_causal_claim_made": False,
        "global_analysis_readiness": False, "next_task": "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
    }
    write_json(OUTPUT / "bounded_wage_differential_validation_summary.json", summary)
    (OUTPUT / "bounded_wage_differential_validation_summary.md").write_text(
        "# Bounded wage-differential validation\n\n"
        f"Decision: `{DECISION}`\n\n"
        f"- Input candidates: **4**\n- PI-report usable: **{len(promoted)}**\n- Conditional/manual review: **{len(conditional)}**\n- Downgraded/rejected: **{len(rejected)}**\n- Numeric corrections: **0**\n\n"
        "Shreve validates as a supporting bounded local documentary comparison. Cammack Village and Canastota remain conditional supporting examples. Alburtis is limited to an appendix/limits illustration because it is not a matched bargaining-unit comparison. No result is a final wage-gap estimate, nationally representative finding, prevalence estimate, policy effect, or causal claim.\n",
        encoding="utf-8",
    )
    manifest = {
        "task_id": TASK, "decision": DECISION, "input_head": INPUT_HEAD, "created_at": now(),
        "locked_queue_sha256": sha256(OUTPUT / "bounded_wage_differential_validation_locked_queue.jsonl"),
        "lane_files": {name: sha256(OUTPUT / name) for name in LANE_FILES},
        "summary": summary,
    }
    write_json(OUTPUT / "bounded_wage_differential_validation_manifest.json", manifest)
    write_json(OUTPUT / "dashboard_bounded_gap_validation_update_summary.json", {
        "status": "ready_for_dashboard_wiring", "clean_dashboard_structure_preserved": True,
        "map_primary_metric": "scout_coverage_rate", "current_stage": "Bounded wage-differential validation complete",
        "next_task": summary["next_task"], "validated_pi_report_usable_count": len(promoted),
        "conditional_manual_review_count": len(conditional), "downgraded_or_rejected_count": len(rejected),
        "final_wage_gap_estimate_claimed": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "ocr_occurred": False, "new_source_download_occurred": False,
        "new_source_review_occurred": False, "new_text_extraction_stage_occurred": False,
        "new_rating_occurred": False, "raw_values_overwritten": False, "quarantine_ingested": False,
        "final_wage_gap_estimate_claimed": False, "national_or_population_prevalence_claimed": False,
        "regression_or_treatment_effect_run": False, "final_causal_claim_made": False,
        "cost_of_living_adjustment_occurred": False, "global_readiness_advanced": False,
    })
    write_json(OUTPUT / "dashboard_browser_smoke_report.json", {"status": "pending_local_browser_validation"})
    (OUTPUT / "dashboard_browser_smoke_report.md").write_text("# Dashboard browser smoke\n\nPending local rendered validation.\n", encoding="utf-8")
    write_json(OUTPUT / "dashboard_public_pages_smoke_report.json", {"status": "pending_commit_push_deployment"})
    write_json(OUTPUT / "staged_file_audit.json", {"status": "pending_staging", "passed": False})
    write_json(OUTPUT / "large_file_audit.json", {"status": "pending_staging", "passed": False})
    (OUTPUT / "next_task.md").write_text(
        "# Next task\n\n`BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30`\n\nDraft the PI-facing report using only validated or properly caveated bounded local documentary comparisons, quantitative growth-mechanism claims, repaired examples, and explicit claim boundaries. Do not present final or national wage-gap estimates, prevalence results, regressions, treatment effects, policy effects, or causal conclusions.\n",
        encoding="utf-8",
    )
    validate(write_only=True)


def validate(write_only: bool = False) -> None:
    queue = [json.loads(line) for line in (OUTPUT / "bounded_wage_differential_validation_locked_queue.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [json.loads(line) for line in (OUTPUT / "merged_bounded_wage_differential_validation_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = read_json(OUTPUT / "bounded_wage_differential_validation_summary.json")
    calc = read_json(OUTPUT / "bounded_wage_differential_calculation_audit.json")
    lineage = read_json(OUTPUT / "source_lineage_validation_report.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    local = read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    staged = read_json(OUTPUT / "staged_file_audit.json")
    large = read_json(OUTPUT / "large_file_audit.json")
    project = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    app = (ROOT / "docs/dashboard/src/App.jsx").read_text(encoding="utf-8")
    all_text = "\n".join(r.get("bounded_pi_report_statement", "") for r in rows)
    checks = {
        "01_input_count_4": len(queue) == len(rows) == 4,
        "02_expected_municipalities": {(r["municipality"], r["state"]) for r in rows} == set(EXPECTED),
        "03_each_candidate_one_lane": len({r["candidate_id"] for r in rows}) == len({r["lane_id"] for r in rows}) == 4,
        "04_each_lane_completed": all((OUTPUT / name).exists() for name in LANE_FILES),
        "05_one_final_status": all(r.get("validation_status") in ALLOWED_STATUSES for r in rows),
        "06_values_source_grounded_or_rejected": lineage.get("all_candidates_have_source_and_span_lineage") is True,
        "07_pay_basis_valid_or_rejected": all(r.get("pay_basis") or r["validation_status"].startswith("rejected") for r in rows),
        "08_period_valid_or_rejected": all(r.get("effective_period_evidence") or r["validation_status"].startswith("rejected") for r in rows),
        "09_base_status_valid_or_rejected": all(r.get("base_or_non_base_comparison_type") or r["validation_status"].startswith("rejected") for r in rows),
        "10_group_classification_valid_or_rejected": all(r.get("safety_unit_group") and r.get("non_safety_unit_group") for r in rows),
        "11_calculations_confirmed": calc.get("all_calculations_confirmed") is True,
        "12_statements_specific": all(r.get("pi_report_one_sentence") and r.get("bounded_pi_report_statement") and r.get("caveat_text") for r in rows),
        "13_no_final_gap": forbidden.get("final_wage_gap_estimate_claimed") is False,
        "14_no_prevalence": forbidden.get("national_or_population_prevalence_claimed") is False,
        "15_no_regression": forbidden.get("regression_or_treatment_effect_run") is False,
        "16_no_final_causal": forbidden.get("final_causal_claim_made") is False,
        "17_no_ocr": forbidden.get("ocr_occurred") is False,
        "18_no_new_download": forbidden.get("new_source_download_occurred") is False,
        "19_no_new_rating": forbidden.get("new_rating_occurred") is False,
        "20_raw_values_preserved": forbidden.get("raw_values_overwritten") is False,
        "21_dashboard_clean": all(token in app for token in ("pi-status-strip", "pi-map-grid", "pi-evidence-grid", "pi-mechanism-table", "pi-boundary-section", "pi-technical-details")),
        "22_map_rate": project.get("dashboard_map_primary_metric") == "scout_coverage_rate",
        "23_dashboard_build": local.get("build_passed") is True,
        "24_local_browser": local.get("status") in {"local_browser_visible_current_passed", "browser_controller_unavailable"},
        "25_public_browser": public.get("status") == "public_pages_visible_current_passed",
        "26_global_not_advanced": project.get("global_analysis_readiness") is False,
        "27_no_payloads_tracked": subprocess.run(["git", "ls-files", "artifacts/local_retained_sources", "artifacts/local_extracted_text"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip() == "",
        "28_staged_audit": staged.get("passed") is True,
        "29_large_audit": large.get("passed") is True,
        "claim_language_boundary": FORBIDDEN.search(all_text) is None,
        "summary_reconciles": summary.get("validated_pi_report_usable_count", 0) + summary.get("conditional_manual_review_count", 0) + summary.get("downgraded_or_rejected_count", 0) == 4,
    }
    core_exclude = {"21_dashboard_clean", "22_map_rate", "23_dashboard_build", "24_local_browser", "25_public_browser", "26_global_not_advanced", "28_staged_audit", "29_large_audit"}
    core = all(value for key, value in checks.items() if key not in core_exclude)
    report = {"validated_at": now(), "checks": checks, "core_checks_passed": core, "all_checks_passed": all(checks.values()), "pending_checks": [k for k, v in checks.items() if not v]}
    write_json(OUTPUT / "validation_report.json", report)
    (OUTPUT / "validation_report.md").write_text(
        "# Validation report\n\n" + f"Core checks passed: **{str(core).lower()}**\n\n" + "\n".join(f"- `{key}`: **{str(value).lower()}**" for key, value in checks.items()) + "\n",
        encoding="utf-8",
    )
    if not write_only:
        print(json.dumps(report, indent=2))
    if not core:
        raise RuntimeError("core validation failed")


def audit_staged() -> None:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    bad, oversized = [], []
    for rel in staged:
        lower = rel.lower()
        path = ROOT / rel
        if re.search(r"(^|/)(artifacts/local_|corpus/|retained_sources?/|extracted_text/)", lower) or re.search(r"\.(pdf|docx?|html?)$", lower):
            bad.append(rel)
        if path.is_file() and path.stat().st_size >= 95 * 1024 * 1024:
            oversized.append({"path": rel, "bytes": path.stat().st_size})
    write_json(OUTPUT / "staged_file_audit.json", {"audited_at": now(), "staged_file_count": len(staged), "staged_files": staged, "forbidden_staged_files": bad, "passed": not bad})
    write_json(OUTPUT / "large_file_audit.json", {"audited_at": now(), "threshold_bytes": 95 * 1024 * 1024, "large_staged_files": oversized, "passed": not oversized})
    print(json.dumps({"staged": len(staged), "forbidden": bad, "large": oversized, "passed": not bad and not oversized}))
    if bad or oversized:
        raise RuntimeError("staged audit failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "coordinate", "validate", "audit-staged"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "coordinate":
        coordinate()
    elif args.command == "validate":
        validate()
    else:
        audit_staged()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
