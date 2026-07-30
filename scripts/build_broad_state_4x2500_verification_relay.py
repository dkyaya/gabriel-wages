#!/usr/bin/env python3
"""Build the compact relay for the completed 4x2500 verification wave."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-VERIFICATION-2026-07-30"
TMP = ROOT / "tmp"
DECISION = "broad_state_4x2500_verification_completed_source_review_ready"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--head-before", required=True)
    args = parser.parse_args()
    status = args.commit[:12] if args.commit else "status"
    staging = TMP / f"broad_state_4x2500_verification_relay_2026-07-30_{status}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    files = [
        "final_decision.json", "verification_manifest.json", "verification_summary.json",
        "verification_summary.md", "verification_lane_distribution.json",
        "verification_lane_distribution.md", "source_review_ready_manifest.json",
        "priority_outcome_summary.json", "source_family_outcome_summary.json",
        "geography_outcome_summary.json", "cba_non_cba_outcome_summary.json",
        "mechanism_hint_outcome_summary.json", "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json", "dashboard_status_input.json",
        "dashboard_status_update_summary.md", "next_task.md", "network_smoke_metadata.csv",
        "preflight_report.json",
    ]
    files.extend(f"verification_lane_{index:03d}_results.csv" for index in range(1, 5))
    for name in files:
        source = OUTPUT / name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, staging / name)
    summary = json.loads((OUTPUT / "verification_summary.json").read_text(encoding="utf-8"))
    relay = {
        "task_id": "BROAD-STATE-4X2500-VERIFICATION-2026-07-30",
        "final_decision": DECISION, "commit_hash": args.commit,
        "push_succeeded": args.push_succeeded == "true", "head_before": args.head_before,
        "head_after": args.commit, "verification_queue_size": summary["verification_queue_count"],
        "priority_distribution": summary["priority_counts_verified"],
        "lane_distribution": summary["lane_counts"],
        "source_review_ready_count": summary["source_review_ready_count"],
        "terminal_status_counts": summary["terminal_status_counts"],
        "forbidden_actions_occurred": False, "blockers": [],
        "uncertainties": [
            "Reachability is a HEAD-only metadata result and is not source-content review or evidence validation."
        ],
        "next_task_id": "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    (staging / "relay_manifest.json").write_text(json.dumps(relay, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    zip_path = TMP / f"broad_state_4x2500_verification_relay_2026-07-30_{status}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(staging.iterdir()):
            archive.write(path, arcname=path.name)
    print(json.dumps({"relay_zip": str(zip_path), "files": len(list(staging.iterdir())), **relay}, sort_keys=True))


if __name__ == "__main__":
    main()
