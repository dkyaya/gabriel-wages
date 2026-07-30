#!/usr/bin/env python3
"""Build the commit-addressed relay for broad-state PDF/text readiness."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"
TASK_ID = "BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()


def read_json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-head", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    head = git("rev-parse", "HEAD")
    origin = git("rev-parse", "origin/main")
    summary = read_json("pdf_text_readiness_summary.json")
    validation = read_json("validation_report.json")
    browser = read_json("dashboard_browser_smoke_report.json")
    build = read_json("dashboard_build_report.json")
    audit = read_json("staged_file_audit.json")
    hash_report = read_json("retained_source_hash_recheck_report.json")
    decision = read_json("final_decision.json")
    ahead_objects = git("rev-list", "--objects", f"{args.pre_head}..{head}").splitlines()
    retained_leak = any("artifacts/local_retained_sources/" in line for line in ahead_objects)
    blockers: list[str] = []
    if validation.get("status") != "passed":
        blockers.append("validation did not pass")
    if audit.get("audit_status") != "passed":
        blockers.append("staged-file audit did not pass")
    if retained_leak:
        blockers.append("ahead commit history contains retained artifact path")
    if args.push_succeeded == "true" and origin != head:
        blockers.append("origin/main does not equal committed HEAD after reported push")
    if blockers:
        raise RuntimeError("relay blocked: " + "; ".join(blockers))

    relay = {
        "task_id": TASK_ID,
        "relay_created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "final_decision": decision["decision"], "commit_hash": head,
        "current_head_before": args.pre_head, "current_head_after": head,
        "push_succeeded": args.push_succeeded == "true", "origin_main_after_push": origin,
        "retained_source_count": summary["retained_source_count"],
        "retained_pdf_count": summary["retained_pdf_count"],
        "retained_html_count": summary["retained_html_count"],
        "retained_other_document_count": summary["retained_other_document_count"],
        "lane_distribution": summary["lane_distribution"],
        "parse_text_pdf_ready_count": summary["parse_text_pdf_ready_count"],
        "html_text_ready_count": summary["html_text_ready_count"],
        "other_document_text_ready_count": summary["other_document_text_ready_count"],
        "text_extraction_ready_count": summary["text_extraction_ready_count"],
        "ocr_later_count": summary["ocr_later_count"],
        "oversized_defer_count": summary["oversized_defer_count"],
        "encrypted_or_locked_count": summary["encrypted_or_locked_count"],
        "corrupt_or_broken_count": summary["corrupt_or_broken_count"],
        "shell_or_navigation_only_count": summary["shell_or_navigation_only_count"],
        "needs_manual_review_count": summary["needs_manual_review_count"],
        "unsupported_file_type_count": summary["unsupported_file_type_count"],
        "readiness_error_count": summary["readiness_error_count"],
        "dashboard_build_result": build.get("status"),
        "dashboard_browser_smoke_result": browser.get("status"),
        "forbidden_actions_avoided": read_json("forbidden_action_audit.json").get("audit_status") == "passed",
        "retained_hash_recheck_status": "passed" if hash_report.get("hash_mismatch_or_missing_count") == 0 else "failed",
        "ahead_history_object_entries": len(ahead_objects),
        "ahead_history_contains_retained_artifact_path": retained_leak,
        "blockers": blockers,
        "uncertainties": ["GitHub Pages deployment timing is external; the required built local dashboard received a visible browser smoke check."],
        "next_task": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30",
    }
    zip_path = ROOT / "tmp" / f"broad_state_4x2500_pdf_text_readiness_relay_2026-07-30_{head}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    include = [
        "final_decision.json", "pdf_text_readiness_manifest.json",
        "pdf_text_readiness_summary.json", "pdf_text_readiness_summary.md",
        "preflight_report.json", "readiness_smoke_preflight.json",
        "readiness_lane_distribution.json", "readiness_lane_distribution.md",
        "text_extraction_ready_manifest.json", "page_count_summary.json",
        "file_size_summary.json", "source_type_readiness_summary.json",
        "priority_readiness_summary.json", "source_family_readiness_summary.json",
        "geography_readiness_summary.json", "cba_non_cba_readiness_summary.json",
        "mechanism_hint_readiness_summary.json", "retained_source_hash_recheck_report.json",
        "dashboard_status_input.json", "dashboard_status_update_summary.md",
        "dashboard_build_report.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "validation_report.json",
        "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "next_task.md",
    ]
    for lane in range(1, 5):
        include.extend([
            f"lanes/readiness_lane_{lane:03d}/summary.json",
            f"lanes/readiness_lane_{lane:03d}/checkpoint.json",
            f"readiness_lane_{lane:03d}_results.csv",
            f"readiness_lane_{lane:03d}_results.jsonl",
        ])
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("relay_status.json", json.dumps(relay, indent=2, sort_keys=True) + "\n")
        for name in include:
            path = OUTPUT / name
            if not path.is_file():
                raise RuntimeError(f"required relay artifact missing: {name}")
            archive.write(path, path.relative_to(ROOT).as_posix())
        for path in (
            ROOT / "docs/analysis/broad_state_4x2500_pdf_text_readiness_result_2026-07-30.md",
            ROOT / "docs/analysis/broad_state_4x2500_pdf_text_readiness_dashboard_status_note_2026-07-30.md",
        ):
            archive.write(path, path.relative_to(ROOT).as_posix())
        if args.screenshot:
            screenshot = ROOT / args.screenshot
            if screenshot.is_file():
                archive.write(screenshot, screenshot.relative_to(ROOT).as_posix())
    relay["relay_zip"] = str(zip_path)
    print(json.dumps(relay, sort_keys=True))


if __name__ == "__main__":
    main()
