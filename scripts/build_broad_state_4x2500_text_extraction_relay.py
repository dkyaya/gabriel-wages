#!/usr/bin/env python3
"""Build the lightweight relay for the 4x2500 text-extraction wave."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30"
DECISION = "broad_state_4x2500_text_extraction_completed_span_extraction_ready"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--head-before", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--deployment-commit", default="")
    args = parser.parse_args()
    suffix = args.commit[:12] if args.commit else "status"
    destination = ROOT / f"tmp/broad_state_4x2500_text_extraction_relay_2026-07-30_{suffix}.zip"
    required = [
        "text_extraction_manifest.json", "text_extraction_summary.md", "text_extraction_summary.json",
        "text_extraction_lane_distribution.json", "text_extraction_lane_distribution.md",
        "extracted_text_manifest.sha256.json", "span_extraction_ready_manifest.json",
        "source_type_extraction_summary.json", "priority_extraction_summary.json",
        "source_family_extraction_summary.json", "geography_extraction_summary.json",
        "cba_non_cba_extraction_summary.json", "mechanism_hint_extraction_summary.json",
        "character_count_summary.json", "page_count_extraction_summary.json",
        "extraction_quality_summary.json", "extracted_text_storage_audit.json",
        "retained_source_hash_recheck_report.json", "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json",
        "dashboard_status_input.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "dashboard_public_pages_smoke_report.json",
        "next_task.md",
    ]
    for lane in range(1, 5):
        required.extend((f"text_extraction_lane_{lane:03d}_results.csv", f"text_extraction_lane_{lane:03d}_results.jsonl"))
    missing = [name for name in required if not (OUTPUT / name).is_file()]
    if missing:
        raise SystemExit(f"relay inputs missing: {missing}")
    summary = json.loads((OUTPUT / "text_extraction_summary.json").read_text())
    payload = {
        "task_id": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30",
        "final_decision": DECISION, "commit_hash": args.commit,
        "deployment_commit": args.deployment_commit or args.commit,
        "push_succeeded": args.push_succeeded == "true", "head_before": args.head_before,
        "head_after": args.commit, "public_pages_url": "https://dkyaya.github.io/gabriel-wages/",
        "summary": summary, "artifact_root": summary["artifact_root"],
        "local_browser_smoke": json.loads((OUTPUT / "dashboard_browser_smoke_report.json").read_text()),
        "public_pages_smoke": json.loads((OUTPUT / "dashboard_public_pages_smoke_report.json").read_text()),
        "blockers_or_uncertainties": [],
        "next_task": "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    manifest_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("relay_manifest.json", manifest_bytes)
        for name in required:
            archive.write(OUTPUT / name, f"artifacts/{name}")
        for path in (
            ROOT / "scripts/run_broad_state_4x2500_text_extraction.py",
            ROOT / "scripts/test_broad_state_4x2500_text_extraction.py",
            ROOT / "scripts/build_broad_state_4x2500_text_extraction_relay.py",
            ROOT / "scripts/build_dashboard_data.py",
            ROOT / ".github/workflows/deploy-dashboard.yml",
        ):
            archive.write(path, f"changes/{path.relative_to(ROOT).as_posix()}")
    print(json.dumps({"relay_zip": str(destination), "bytes": destination.stat().st_size,
                      "sha256": sha256(destination), "decision": DECISION}, indent=2))


if __name__ == "__main__":
    main()
