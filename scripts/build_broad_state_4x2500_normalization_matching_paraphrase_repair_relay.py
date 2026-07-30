#!/usr/bin/env python3
"""Build the bounded normalization/matching/paraphrase-repair relay ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-PARAPHRASE-REPAIR-2026-07-30"
TMP = ROOT / "tmp"
INPUT_HEAD = "3c3bb2ac01b0d069b79484f4facd92d096410cb8"
DECISION = "broad_state_4x2500_normalization_matching_paraphrase_repair_completed_pi_report_ready"


def read_json(name: str):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--push-status", required=True)
    args = parser.parse_args()

    summary = read_json("normalization_matching_paraphrase_repair_summary.json")
    public = read_json("dashboard_public_pages_smoke_report.json")
    claims = read_json("updated_careful_claim_candidates.json")["claims"]
    validation = read_json("validation_report.json")
    staged = read_json("staged_file_audit.json")
    large = read_json("large_file_audit.json")
    if summary["decision"] != DECISION or not validation["all_checks_passed"]:
        raise SystemExit("relay requires the successful decision and a fully passing validation report")
    if public.get("status") != "public_pages_visible_current_passed":
        raise SystemExit("relay requires a visibly current public Pages smoke")
    if not staged.get("passed") or not large.get("passed"):
        raise SystemExit("relay requires passing staged and large-file audits")

    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{INPUT_HEAD}..{args.commit}"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    relay_status = {
        "final_decision": DECISION,
        "commit_hash": args.commit,
        "push_status": args.push_status,
        "head_before": INPUT_HEAD,
        "head_after": args.commit,
        "pages_mismatch_reconciled": summary["pages_mismatch_reconciled"],
        "dashboard_public_pages_status": public["status"],
        "normalized_quantitative_record_count": summary["normalized_quantitative_record_count"],
        "normalization_status_counts": summary["normalization_status_counts"],
        "normalization_blocker_counts": summary["normalization_blocker_counts"],
        "hourly_annual_assumption_counts": summary["hourly_annual_assumption_counts"],
        "municipality_cycle_group_count": summary["municipality_cycle_group_count"],
        "matched_safety_non_safety_cycle_candidate_count": summary["matched_safety_non_safety_cycle_candidate_count"],
        "match_quality_counts": summary["match_quality_counts"],
        "comparable_normalized_wage_candidate_count": summary["comparable_normalized_wage_candidate_count"],
        "cycle_to_cycle_growth_readiness_candidate_count": summary["cycle_to_cycle_growth_readiness_candidate_count"],
        "repaired_example_count": summary["repaired_example_count"],
        "downgraded_or_unrepaired_example_count": summary["downgraded_or_unrepaired_example_count"],
        "updated_careful_claim_count": summary["updated_careful_claim_count"],
        "strongest_updated_careful_claims": [
            {"claim_id": item["claim_id"], "title": item["claim_title"], "claim": item["updated_claim_text"]}
            for item in claims[:8]
        ],
        "final_wage_gap_estimates_calculated": False,
        "regression_or_treatment_effect_run": False,
        "final_causal_or_prevalence_claim_made": False,
        "dashboard_cleaned_format_preserved": True,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "changed_files": changed,
        "next_task": "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
    }
    (OUTPUT / "relay_status.json").write_text(json.dumps(relay_status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    include = [
        "relay_status.json",
        "normalization_matching_paraphrase_repair_manifest.json",
        "normalization_matching_paraphrase_repair_summary.json",
        "normalization_matching_paraphrase_repair_summary.md",
        "pages_smoke_status_reconciliation.json", "pages_smoke_status_reconciliation.md",
        "dashboard_public_status_source_of_truth.json", "dashboard_public_status_repair_actions.json",
        "normalized_quantitative_records_manifest.json", "normalization_summary.json", "normalization_summary.md",
        "normalization_status_counts.json", "normalization_blocker_table.json",
        "hourly_annual_conversion_audit.json", "base_nonbase_classification_audit.json",
        "safety_category_classification_audit.json", "effective_period_parsing_audit.json",
        "normalized_value_quality_audit.json", "municipality_cycle_groups_summary.json",
        "matched_cycle_summary.json", "comparable_normalized_wage_summary.json",
        "growth_readiness_summary.json", "matched_structure_blocker_table.json",
        "matched_structure_validation_report.json", "matched_structure_summary.md",
        "paraphrase_repair_audit.json", "paraphrase_repair_audit.md",
        "paraphrase_quality_validation_report.json", "repaired_report_ready_examples.md",
        "unrepaired_or_downgraded_examples.json", "updated_careful_claim_candidates.json",
        "updated_careful_claim_candidates.md", "claim_strength_change_log.json", "claim_strength_change_log.md",
        "repaired_pi_report_core_findings_candidates.md", "repaired_pi_report_supporting_findings_candidates.md",
        "repaired_pi_report_context_findings_candidates.md", "repaired_pi_report_claim_language_bank.md",
        "repaired_pi_report_section_outline.md", "repaired_pi_report_draft_skeleton.md",
        "dashboard_normalization_matching_update_summary.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "dashboard_public_pages_smoke_report.json",
        "validation_report.json", "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    for screenshot_name in ("dashboard_local_smoke.png", "dashboard_public_smoke.png"):
        screenshot = OUTPUT / screenshot_name
        if screenshot.exists():
            include.append(screenshot.name)
    archive = TMP / f"broad_state_4x2500_normalization_matching_paraphrase_repair_relay_2026-07-30_{args.commit}.zip"
    with tempfile.TemporaryDirectory(dir=TMP, prefix="normalization_matching_relay_") as stage_text:
        stage = Path(stage_text)
        for name in include:
            source = OUTPUT / name
            if not source.exists():
                raise FileNotFoundError(source)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (stage / "changed_files_manifest.json").write_text(
            json.dumps({"commit": args.commit, "files": changed}, indent=2) + "\n", encoding="utf-8"
        )
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(stage))
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"relay ZIP CRC failure: {bad}")
    print(archive.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
