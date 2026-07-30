#!/usr/bin/env python3
"""Build the normalization-rescue, bounded-gap, and growth-claim relay ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-NORMALIZATION-RESCUE-GAP-GROWTH-CLAIMS-2026-07-30"
TMP = ROOT / "tmp"
INPUT_HEAD = "940cb65b657fbb4b0efe91761fe4ad0de60763a5"
DECISION = "broad_state_4x2500_normalization_rescue_gap_growth_completed_pi_report_ready"


def read_json(name: str):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--push-status", required=True)
    args = parser.parse_args()

    summary = read_json("normalization_rescue_gap_growth_summary.json")
    partial = read_json("partial_repair_summary.json")
    mechanism = read_json("mechanism_only_repair_summary.json")
    gap = read_json("bounded_gap_evidence_summary.json")
    lane_results = read_json("normalization_rescue_lane_results_summary.json")
    gap_claims = read_json("bounded_current_wage_gap_evidence_claims.json")["claims"]
    growth_claims = read_json("quantitative_growth_mechanism_claims.json")["claims"]
    public = read_json("dashboard_public_pages_smoke_report.json")
    validation = read_json("validation_report.json")
    staged = read_json("staged_file_audit.json")
    large = read_json("large_file_audit.json")
    if summary["decision"] != DECISION or not validation["all_checks_passed"]:
        raise SystemExit("relay requires successful decision and complete validation")
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
        "partial_input_count": summary["partial_input_count"],
        "mechanism_only_input_count": summary["mechanism_only_input_count"],
        "lane_distribution": summary["lane_counts"],
        "lane_results": lane_results,
        "partial_status_counts": partial["status_counts"],
        "mechanism_status_counts": mechanism["status_counts"],
        "rescued_full_normalization_count": summary["rescued_full_normalization_count"],
        "rescued_gap_claim_ready_count": summary["rescued_gap_claim_ready_count"],
        "rescued_near_gap_ready_count": summary["rescued_near_gap_ready_count"],
        "still_partial_count": summary["still_partial_count"],
        "downgraded_partial_count": summary["downgraded_partial_count"],
        "quantitative_growth_mechanism_supported_count": summary["quantitative_growth_mechanism_supported_count"],
        "current_bounded_wage_differential_candidate_count": gap["current_bounded_wage_differential_candidate_count"],
        "current_bounded_growth_mechanism_comparison_candidate_count": gap["current_bounded_growth_mechanism_comparison_candidate_count"],
        "current_directional_documentary_hint_count": gap["current_directional_documentary_hint_count"],
        "future_gap_potential_only_count": gap["future_gap_potential_only_count"],
        "strongest_bounded_current_wage_gap_evidence_claims": gap_claims[:10],
        "strongest_quantitative_growth_mechanism_claims": growth_claims[:10],
        "repaired_example_count": summary["repaired_example_count"],
        "downgraded_or_unrepaired_example_count": summary["downgraded_or_unrepaired_example_count"],
        "dashboard_cleaned_format_preserved": True,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "dashboard_local_browser_status": read_json("dashboard_browser_smoke_report.json").get("status"),
        "dashboard_public_pages_status": public["status"],
        "forbidden_actions_avoided": read_json("forbidden_action_audit.json").get("passed"),
        "changed_files": changed,
        "blockers_or_uncertainties": [
            "All bounded documentary differential candidates require final manual validation.",
            "No candidate is a final or national wage-gap estimate, population-prevalence result, regression, treatment effect, or causal claim.",
        ],
        "next_task": "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
    }
    include = [
        "normalization_rescue_gap_growth_manifest.json",
        "normalization_rescue_gap_growth_summary.json", "normalization_rescue_gap_growth_summary.md",
        "normalization_rescue_locked_queue_manifest.json", "normalization_rescue_lane_distribution.json",
        "normalization_rescue_lane_distribution.md", "normalization_rescue_lane_results_summary.json",
        "partial_repair_summary.json", "partial_repair_summary.md", "mechanism_only_repair_summary.json",
        "mechanism_only_repair_summary.md", "bounded_gap_evidence_summary.json", "bounded_gap_evidence_summary.md",
        "matched_cycle_current_evidence_statements.json", "matched_cycle_current_evidence_statements.md",
        "bounded_current_wage_gap_evidence_claims.json", "bounded_current_wage_gap_evidence_claims.md",
        "quantitative_growth_mechanism_claims.json", "quantitative_growth_mechanism_claims.md",
        "rescued_gap_growth_claim_candidates.json", "rescued_gap_growth_claim_candidates.md",
        "matched_cycle_claim_language_bank.md", "pi_report_gap_potential_section_draft.md",
        "pi_report_growth_mechanism_section_draft.md", "rescue_repaired_report_examples.md",
        "rescue_repaired_core_findings.json", "rescue_repaired_core_findings.md",
        "rescue_repaired_supporting_findings.json", "rescue_repaired_supporting_findings.md",
        "rescue_repaired_context_findings.json", "rescue_repaired_context_findings.md",
        "rescue_updated_claim_language_bank.md", "rescue_updated_pi_report_outline.md",
        "rescue_updated_pi_report_draft_skeleton.md", "rescue_paraphrase_quality_validation_report.json",
        "dashboard_normalization_rescue_update_summary.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "dashboard_public_pages_smoke_report.json",
        "validation_report.json", "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    for lane in range(1, 5):
        include.extend([
            f"rescue_lane_{lane:03d}_checkpoint.json",
            f"rescue_lane_{lane:03d}_results.jsonl",
        ])
    for screenshot_name in ("dashboard_local_smoke.png", "dashboard_public_smoke.png"):
        if (OUTPUT / screenshot_name).exists():
            include.append(screenshot_name)
    archive = TMP / f"broad_state_4x2500_normalization_rescue_gap_growth_claims_relay_2026-07-30_{args.commit}.zip"
    with tempfile.TemporaryDirectory(dir=TMP, prefix="normalization_rescue_relay_") as stage_text:
        stage = Path(stage_text)
        (stage / "relay_status.json").write_text(
            json.dumps(relay_status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        for name in include:
            source = OUTPUT / name
            if not source.exists():
                raise FileNotFoundError(source)
            shutil.copy2(source, stage / name)
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
