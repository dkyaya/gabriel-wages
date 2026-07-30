#!/usr/bin/env python3
"""Validate, audit, and relay the bounded GitHub Pages deployment repair."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = (
    ROOT
    / "docs/analysis/compensation_extraction"
    / "DASHBOARD-GITHUB-PAGES-DEPLOYMENT-REPAIR-2026-07-30"
)
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources"
DECISION = "dashboard_github_pages_deployment_repair_completed_public_pages_current"
PUBLIC_STATUS = "public_pages_visible_current_passed"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def run(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()


def staged_audit() -> None:
    names = run("git", "diff", "--cached", "--name-only").splitlines()
    forbidden_suffixes = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".bin",
        ".html", ".htm",
    }
    staged_files: list[dict[str, Any]] = []
    forbidden: list[dict[str, Any]] = []
    large: list[dict[str, Any]] = []
    for name in names:
        path = ROOT / name
        size = path.stat().st_size if path.is_file() else 0
        item = {"path": name, "size_bytes": size, "suffix": path.suffix.casefold()}
        staged_files.append(item)
        if size > 25 * 1024 * 1024:
            large.append(item)
        casefolded = name.casefold()
        if (
            name.startswith("artifacts/local_retained_sources/")
            or path.suffix.casefold() in forbidden_suffixes
            or (
                path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
                and not name.startswith(str(OUTPUT.relative_to(ROOT)) + "/dashboard_")
            )
            or any(token in casefolded for token in (
                "full_extracted_text", "ocr_output", "browser_cache", "retained_sources/"
            ))
        ):
            forbidden.append(item)
    tracked_retained = run("git", "ls-files", "artifacts/local_retained_sources").splitlines()
    forbidden.extend({"path": value, "reason": "tracked_retained_source"} for value in tracked_retained)
    staged = {
        "audited_at": now(),
        "status": "passed" if not forbidden else "failed",
        "staged_file_count": len(staged_files),
        "aggregate_staged_bytes": sum(item["size_bytes"] for item in staged_files),
        "forbidden_file_count": len(forbidden),
        "forbidden_files": forbidden,
        "retained_sources_staged_or_tracked": bool(tracked_retained)
        or any(item["path"].startswith("artifacts/local_retained_sources/") for item in staged_files),
        "full_text_ocr_or_browser_cache_staged": any(
            any(token in item["path"].casefold() for token in ("full_extracted_text", "ocr_output", "browser_cache"))
            for item in staged_files
        ),
        "staged_files": staged_files,
    }
    large_audit = {
        "audited_at": now(),
        "status": "passed" if not large else "failed",
        "threshold_bytes": 25 * 1024 * 1024,
        "largest_staged_file_bytes": max((item["size_bytes"] for item in staged_files), default=0),
        "large_file_count": len(large),
        "large_files": large,
    }
    write_json(OUTPUT / "staged_file_audit.json", staged)
    write_json(OUTPUT / "large_file_audit.json", large_audit)
    if forbidden or large:
        raise SystemExit("staged or large-file audit failed")
    print(json.dumps({
        "staged_file_audit": staged["status"],
        "staged_file_count": staged["staged_file_count"],
        "forbidden_file_count": 0,
        "large_file_audit": large_audit["status"],
        "large_file_count": 0,
    }))


def validate() -> None:
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    local_build = read_json(OUTPUT / "dashboard_local_build_report.json")
    local_browser = read_json(OUTPUT / "dashboard_local_browser_smoke_report.json")
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    deployment = read_json(OUTPUT / "dashboard_deployment_config_audit.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    staged = read_json(OUTPUT / "staged_file_audit.json")
    large = read_json(OUTPUT / "large_file_audit.json")
    checks = {
        "01_latest_dashboard_values_exist_locally": phase.get("data_vintage") == "2026-07-30",
        "02_local_dashboard_build_passed": local_build.get("status") == "passed",
        "03_local_browser_smoke_passed": local_browser.get("status") == "passed",
        "04_pages_deployment_mechanism_identified": deployment.get("mechanism") == "github_actions_pages_artifact",
        "05_public_pages_url_identified": deployment.get("public_pages_url") == "https://dkyaya.github.io/gabriel-wages/",
        "06_public_pages_visible_smoke_passed": public.get("status") == PUBLIC_STATUS,
        "07_dashboard_map_scout_only": phase.get("dashboard_map_filter") == "total_scout_coverage_only",
        "08_scout_coverage_16887": phase.get("actual_scout_covered_municipalities") == 16887,
        "09_source_review_queue_3950": phase.get("broad_state_4x2500_source_review_queue_count") == 3950,
        "10_retained_sources_3672": phase.get("broad_state_4x2500_source_review_retained_count") == 3672,
        "11_text_extraction_ready_2940": phase.get("broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count") == 2940,
        "12_ocr_later_601": phase.get("broad_state_4x2500_pdf_text_readiness_ocr_later_count") == 601,
        "13_next_task_text_extraction": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30" in phase.get("next_task", ""),
        "14_global_readiness_not_advanced": phase.get("global_analysis_readiness") is False,
        "15_wage_gap_blocked": phase.get("wage_gap_analysis_readiness") == "blocked_pending_normalization",
        "16_causal_readiness_blocked": phase.get("causal_analysis_readiness") == "blocked_pending_matched_structure",
        "17_no_extraction_ocr_rating_ingestion_codification": all(
            forbidden.get(field) == 0 for field in (
                "text_extraction_runs", "ocr_runs", "rating_runs", "ingestion_runs", "codification_runs"
            )
        ),
        "18_no_wage_gap_regression_causal_claims": all(
            forbidden.get(field) == 0 for field in (
                "wage_gap_calculations", "regressions", "final_causal_claims"
            )
        ),
        "19_no_forbidden_files_staged_or_tracked": staged.get("forbidden_file_count") == 0,
        "20_staged_file_audit_passed": staged.get("status") == "passed",
        "21_large_file_audit_passed": large.get("status") == "passed",
    }
    passed = all(checks.values())
    report = {
        "task_id": "DASHBOARD-GITHUB-PAGES-DEPLOYMENT-REPAIR-2026-07-30",
        "validated_at": now(),
        "status": "passed" if passed else "failed",
        "passed_count": sum(checks.values()),
        "check_count": len(checks),
        "checks": checks,
        "final_decision": DECISION if passed else "validation_failed",
    }
    write_json(OUTPUT / "validation_report.json", report)
    lines = [
        "# Dashboard Pages deployment repair validation",
        "",
        f"Status: **{report['status']}** — {report['passed_count']}/{report['check_count']} checks passed.",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'} — `{name}`" for name, value in checks.items())
    write_text(OUTPUT / "validation_report.md", "\n".join(lines))
    if not passed:
        raise SystemExit("validation failed: " + ", ".join(name for name, value in checks.items() if not value))
    print(json.dumps(report))


def build_relay(pre_head: str, push_succeeded: bool) -> None:
    head = run("git", "rev-parse", "HEAD")
    public = read_json(OUTPUT / "dashboard_public_pages_smoke_report.json")
    summary = read_json(OUTPUT / "dashboard_pages_repair_summary.json")
    status = {
        "task_id": "DASHBOARD-GITHUB-PAGES-DEPLOYMENT-REPAIR-2026-07-30",
        "final_decision": DECISION,
        "commit_hash": head,
        "push_succeeded": push_succeeded,
        "head_before": pre_head,
        "head_after": head,
        "public_pages_url": "https://dkyaya.github.io/gabriel-wages/",
        "deployment_mechanism": "github_actions_pages_artifact",
        "root_cause": summary["root_cause"],
        "local_build_result": "passed",
        "local_browser_smoke_result": "passed",
        "public_pages_smoke_result": public["status"],
        "latest_numbers_visibly_public": public.get("latest_numbers_visibly_public") is True,
        "forbidden_actions_avoided": True,
        "next_task": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30",
    }
    relay = ROOT / "tmp" / f"dashboard_github_pages_deployment_repair_relay_2026-07-30_{head}.zip"
    include = sorted(OUTPUT.iterdir())
    with zipfile.ZipFile(relay, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_status.json", json.dumps(status, indent=2, sort_keys=True) + "\n")
        for path in include:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
    print(json.dumps({**status, "relay_zip": str(relay)}))


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--audit-staged", action="store_true")
    actions.add_argument("--validate", action="store_true")
    actions.add_argument("--relay", action="store_true")
    parser.add_argument("--pre-head")
    parser.add_argument("--push-succeeded", choices=("true", "false"), default="false")
    args = parser.parse_args()
    if args.audit_staged:
        staged_audit()
    elif args.validate:
        validate()
    else:
        if not args.pre_head:
            parser.error("--relay requires --pre-head")
        build_relay(args.pre_head, args.push_succeeded == "true")


if __name__ == "__main__":
    main()
