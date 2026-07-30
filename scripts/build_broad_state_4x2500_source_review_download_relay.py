#!/usr/bin/env python3
"""Build the compact handoff relay for the broad-state source-review wave."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30"
PREFIX = "broad_state_4x2500_source_review_download_relay_2026-07-30"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-head", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--screenshot")
    args = parser.parse_args()

    summary = read_json(OUTPUT / "source_review_download_summary.json")
    dashboard_build = read_json(OUTPUT / "dashboard_build_report.json")
    dashboard_browser = read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    decision = summary["decision"]
    commit = git("rev-parse", "HEAD")
    origin = git("rev-parse", "origin/main")
    ahead_objects = git("rev-list", "--objects", f"{args.pre_head}..{commit}").splitlines()
    status = {
        "task_id": summary["task_id"],
        "final_decision": decision,
        "commit_hash": commit,
        "push_succeeded": args.push_succeeded == "true",
        "current_head_before": args.pre_head,
        "current_head_after": commit,
        "origin_main_after_push": origin,
        "source_review_queue_size": summary["source_review_queue_count"],
        "lane_distribution": summary["lane_counts"],
        "retained_source_count": summary["retained_source_count"],
        "retained_pdf_count": summary["retained_pdf_count"],
        "retained_html_count": summary["retained_html_count"],
        "retained_other_document_count": summary["retained_other_document_count"],
        "terminal_status_counts": summary["terminal_status_counts"],
        "retained_source_local_artifact_directory": summary["artifact_root"],
        "retained_byte_total": summary["retained_byte_total"],
        "unique_retained_hashes": summary["unique_retained_hashes"],
        "dashboard_build_result": dashboard_build.get("status"),
        "dashboard_browser_smoke_result": dashboard_browser.get("status"),
        "blockers": [],
        "uncertainties": [
            "GitHub Pages deployment timing is external; the required built local dashboard received a visible browser smoke check."
        ],
        "ahead_history_object_entries": len(ahead_objects),
        "ahead_history_contains_retained_artifact_path": any(
            "artifacts/local_retained_sources/" in line for line in ahead_objects
        ),
        "relay_created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    relay_status = ROOT / "tmp/broad_state_4x2500_source_review_download_relay_status.json"
    relay_status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    names = [
        "final_decision.json", "source_review_download_manifest.json",
        "preflight_report.json",
        "source_review_download_summary.json", "source_review_download_summary.md",
        "source_review_lane_distribution.json", "source_review_lane_distribution.md",
        "priority_source_review_summary.json", "source_family_source_review_summary.json",
        "geography_source_review_summary.json", "cba_non_cba_source_review_summary.json",
        "mechanism_hint_source_review_summary.json", "retained_source_manifest.sha256.json",
        "retained_source_storage_audit.json", "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json",
        "dashboard_status_input.json", "dashboard_status_update_summary.md",
        "dashboard_build_report.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "next_task.md",
    ]
    files = [OUTPUT / name for name in names if (OUTPUT / name).is_file()]
    for lane in range(1, 5):
        files.extend(
            path for path in (
                OUTPUT / "lanes" / f"source_review_lane_{lane:03d}" / "summary.json",
                OUTPUT / "lanes" / f"source_review_lane_{lane:03d}" / "checkpoint.json",
                OUTPUT / f"source_review_lane_{lane:03d}_results.csv",
                OUTPUT / f"source_review_lane_{lane:03d}_results.jsonl",
            ) if path.is_file()
        )
    files.extend(
        path for path in (
            ROOT / "docs/analysis/broad_state_4x2500_source_review_download_result_2026-07-30.md",
            ROOT / "docs/analysis/broad_state_4x2500_source_review_download_dashboard_status_note_2026-07-30.md",
        ) if path.is_file()
    )
    if args.screenshot:
        screenshot = Path(args.screenshot).resolve()
        if screenshot.is_file():
            files.append(screenshot)

    relay = ROOT / "tmp" / f"{PREFIX}_{commit}.zip"
    with zipfile.ZipFile(relay, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.write(relay_status, "relay_status.json")
        for path in files:
            try:
                arcname = str(path.relative_to(ROOT))
            except ValueError:
                arcname = f"browser_smoke/{path.name}"
            archive.write(path, arcname)
    print(json.dumps({"relay_zip": str(relay), **status}, sort_keys=True))


if __name__ == "__main__":
    main()
