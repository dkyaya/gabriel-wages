#!/usr/bin/env python3
"""Build the focused bounded wage-differential validation relay ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "BROAD-STATE-4X2500-BOUNDED-WAGE-DIFFERENTIAL-VALIDATION-2026-07-30"
)
TMP = ROOT / "tmp"
HEAD_BEFORE = "74c87c7836b6ce4a277df076db288791b06feaf1"
DECISION = "broad_state_4x2500_bounded_wage_differential_validation_completed_pi_report_ready"


def read_json(name: str):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (OUTPUT / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--push-status", required=True)
    args = parser.parse_args()

    summary = read_json("bounded_wage_differential_validation_summary.json")
    validation = read_json("validation_report.json")
    forbidden = read_json("forbidden_action_audit.json")
    staged = read_json("staged_file_audit.json")
    large = read_json("large_file_audit.json")
    local = read_json("dashboard_browser_smoke_report.json")
    public = read_json("dashboard_public_pages_smoke_report.json")
    dashboard = read_json("dashboard_bounded_gap_validation_update_summary.json")
    lanes = read_json("validation_lane_distribution.json")
    results = read_jsonl("merged_bounded_wage_differential_validation_results.jsonl")
    statements = read_json("bounded_wage_differential_pi_statements.json")["statements"]

    if summary.get("decision") != DECISION:
        raise SystemExit("relay requires the completed PI-report-ready decision")
    if not validation.get("all_checks_passed"):
        raise SystemExit("relay requires passing validation")
    if not forbidden.get("passed") or not staged.get("passed") or not large.get("passed"):
        raise SystemExit("relay requires passing forbidden-action, staged-file, and large-file audits")
    if not local.get("passed"):
        raise SystemExit("relay requires passing local browser smoke")
    if public.get("status") != "public_pages_visible_current_passed" or not public.get("passed"):
        raise SystemExit("relay requires a visibly current public Pages smoke")

    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{HEAD_BEFORE}..{args.commit}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    corrections = {
        "numeric_value_or_calculation_corrections": [],
        "substantive_interpretation_corrections": [
            "Alburtis comparison period narrowed to the overlapping January 1-June 30, 2018 window; the police rate is for the Chief, who the ordinance removes from the police bargaining unit.",
            "Cammack Village values are maximum authorized salary-schedule rates, not evidence that the named positions were actually paid those rates; enactment fields in the retained packet also require manual confirmation.",
            "Canastota's non-safety record is Code Enforcement Officer; an upstream police safety-category tag was erroneous and was corrected only in the validation interpretation, without overwriting raw upstream data.",
        ],
    }
    relay_status = {
        "final_decision": DECISION,
        "commit_hash": args.commit,
        "push_status": args.push_status,
        "head_before": HEAD_BEFORE,
        "head_after": args.commit,
        "input_candidate_count": summary["input_candidate_count"],
        "validation_lane_distribution": lanes,
        "validation_results": results,
        "promoted_count": summary["validated_pi_report_usable_count"],
        "conditional_count": summary["conditional_manual_review_count"],
        "downgraded_or_rejected_count": summary["downgraded_or_rejected_count"],
        "corrected_values_or_calculations": corrections,
        "validated_pi_report_statements": statements,
        "caveats": [row.get("caveats", []) for row in results],
        "forbidden_interpretation_warnings": [
            row.get("forbidden_claim_warning") for row in results
        ],
        "dashboard_update_summary": dashboard,
        "dashboard_cleaned_format_preserved": dashboard["clean_dashboard_structure_preserved"],
        "dashboard_map_primary_metric": dashboard["map_primary_metric"],
        "dashboard_local_build_passed": local["build_passed"],
        "dashboard_local_browser_status": local["status"],
        "dashboard_public_pages_status": public["status"],
        "dashboard_deployment_run_id": public["deployment_run_id"],
        "dashboard_deployment_source_commit": public["deployment_source_commit"],
        "validation_outputs_passed": validation["all_checks_passed"],
        "forbidden_actions_avoided": forbidden["passed"],
        "staged_file_audit_passed": staged["passed"],
        "large_file_audit_passed": large["passed"],
        "blockers_or_uncertainties": [
            "Only Shreve meets the PI-usable validation tier; Alburtis, Cammack Village, and Canastota require candidate-specific manual validation before analytic use.",
            "None of the four comparisons is a final wage-gap estimate, nationally representative estimate, population-prevalence result, regression, treatment effect, or causal finding.",
        ],
        "next_task": "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
        "changed_files": changed,
    }

    archive = TMP / (
        "broad_state_4x2500_bounded_wage_differential_validation_relay_"
        f"2026-07-30_{args.commit}.zip"
    )
    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP, prefix="bounded_wage_validation_relay_") as stage_text:
        stage = Path(stage_text)
        (stage / "relay_status.json").write_text(
            json.dumps(relay_status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        for source in sorted(OUTPUT.iterdir()):
            if source.is_file():
                shutil.copy2(source, stage / source.name)
        (stage / "changed_files_manifest.json").write_text(
            json.dumps({"commit": args.commit, "files": changed}, indent=2) + "\n",
            encoding="utf-8",
        )
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(stage.iterdir()):
                if path.is_file():
                    zf.write(path, path.name)

    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"relay ZIP CRC failure: {bad}")
    print(archive.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
