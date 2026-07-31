#!/usr/bin/env python3
"""Build the relay package for the Broad State 4x2500 PI report draft."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30"
HEAD_BEFORE = "df9802202a843f3c734818d39243079910ee7f5b"
DECISION = "broad_state_4x2500_pi_report_draft_completed_review_ready"


def read_json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--push-status", required=True)
    args = parser.parse_args()

    validation = read_json("validation_report.json")
    forbidden = read_json("forbidden_action_audit.json")
    staged = read_json("staged_file_audit.json")
    large = read_json("large_file_audit.json")
    public = read_json("dashboard_public_pages_smoke_report.json")
    local = read_json("dashboard_browser_smoke_report.json")
    manifest = read_json("pi_report_draft_manifest.json")
    dashboard = read_json("pi_report_dashboard_link_update_summary.json")
    claim_audit = read_json("pi_report_claim_audit_2026-07-30.json")

    required = {
        "validation": validation.get("all_checks_passed") is True,
        "forbidden_action_audit": forbidden.get("passed") is True,
        "staged_file_audit": staged.get("passed") is True,
        "large_file_audit": large.get("passed") is True,
        "public_pages": public.get("passed") is True,
        "local_dashboard": local.get("passed") is True,
        "claim_audit": claim_audit.get("passed") is True,
        "manifest_decision": manifest.get("decision") == DECISION,
        "dashboard_map": dashboard.get("map_primary_metric") == "scout_coverage_rate",
    }
    if not all(required.values()):
        raise SystemExit(f"relay precondition failed: {required}")

    commit = subprocess.run(
        ["git", "rev-parse", args.commit], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    report_files = sorted(path.name for path in OUTPUT.iterdir() if path.is_file())
    changed_files = git_lines("diff", "--name-only", f"{HEAD_BEFORE}..{commit}")
    blockers = [
        "DOCX visual rendering was unavailable because LibreOffice/soffice is not installed; structural DOCX validation passed.",
        "The configured in-app browser runtime reported no available browser; local and public validation used build, contract-test, HTML, and deployed-bundle checks without claiming a visual-browser pass.",
        "The four bounded local documentary comparisons still require candidate-specific final substantive/manual validation before analytic use.",
        "Final wage-gap, national-prevalence, regression, treatment-effect, policy-effect, and causal claims remain prohibited.",
    ]
    status = {
        "task_id": "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "final_decision": DECISION,
        "commit_hash": commit,
        "push_status": args.push_status,
        "head_before": HEAD_BEFORE,
        "head_after": commit,
        "report_artifacts_created": report_files,
        "docx_created": True,
        "docx_visual_render_status": "unavailable_soffice_missing_structural_validation_passed",
        "executive_summary_created": True,
        "one_page_brief_created": True,
        "appendix_and_table_artifacts_created": True,
        "required_seven_sections_present": True,
        "careful_claim_candidates_integrated": 18,
        "substantive_or_context_claims_integrated": 16,
        "limit_or_exclusion_claims_integrated": 2,
        "bounded_wage_differential_usage": {
            "total": 4,
            "pi_report_usable": 1,
            "conditional_manual_review": 3,
            "rejected": 0,
            "shreve": "cleanest supporting bounded local documentary example",
            "cammack_village": "qualified supporting example",
            "canastota": "qualified counterexample",
            "alburtis": "limits/appendix only",
        },
        "quantitative_growth_mechanism_usage": {
            "supported_records": 416,
            "validated_claim_candidates": 95,
            "selected_report_examples": 6,
        },
        "mechanism_findings": [
            "non-base compensation",
            "direct wage schedules and base-wage values",
            "implementation timing and retroactivity",
            "automatic raises, COLA/CPI, percentage increases, and step progression",
            "bargaining, arbitration, factfinding, and dispute resolution",
            "rank, step, specialization, and classification",
            "market, recruitment, retention, and staffing pressure",
        ],
        "claim_audit_passed": True,
        "forbidden_claim_audit_passed": True,
        "limits": [
            "no final or national wage-gap estimate",
            "no national/population prevalence claim",
            "no regression or treatment-effect result",
            "no final causal or policy-effect claim",
            "no analyst-side cost-of-living adjustment",
        ],
        "dashboard": {
            "current_stage": dashboard.get("current_stage"),
            "current_report_path": dashboard.get("current_report_path"),
            "clean_structure_preserved": dashboard.get("clean_dashboard_structure_preserved"),
            "map_primary_metric": dashboard.get("map_primary_metric"),
            "local_validation_status": local.get("status"),
            "public_validation_status": public.get("status"),
            "public_deployment_run_id": public.get("deployment_run_id"),
            "browser_controller_available": False,
        },
        "validation": validation,
        "forbidden_action_audit": forbidden,
        "staged_file_audit": staged,
        "large_file_audit": large,
        "blockers_or_uncertainties": blockers,
        "next_task": "BROAD-STATE-4X2500-PI-REPORT-REVIEW-FINALIZE-2026-07-30",
        "changed_files": changed_files,
    }

    relay_path = ROOT / "tmp" / f"broad_state_4x2500_pi_report_draft_relay_2026-07-30_{commit}.zip"
    relay_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pi_report_relay_", dir=ROOT / "tmp") as temp_dir:
        temp = Path(temp_dir)
        (temp / "relay_status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (temp / "final_decision.txt").write_text(DECISION + "\n", encoding="utf-8")
        (temp / "commit.txt").write_text(commit + "\n", encoding="utf-8")
        (temp / "push_status.txt").write_text(args.push_status + "\n", encoding="utf-8")
        with zipfile.ZipFile(relay_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(temp.iterdir()):
                archive.write(path, path.name)
            included: set[str] = set()
            for relative in changed_files:
                source = ROOT / relative
                if source.is_file() and relative not in included:
                    archive.write(source, f"repository/{relative}")
                    included.add(relative)
            for source in sorted(OUTPUT.iterdir()):
                if source.is_file():
                    relative = str(source.relative_to(ROOT))
                    if relative not in included:
                        archive.write(source, f"repository/{relative}")
                        included.add(relative)

    with zipfile.ZipFile(relay_path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"relay CRC failure: {bad}")
        names = archive.namelist()
    print(json.dumps({"relay": str(relay_path), "files": len(names), "crc_passed": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
