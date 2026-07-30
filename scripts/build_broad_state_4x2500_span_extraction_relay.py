#!/usr/bin/env python3
"""Build the bounded relay ZIP for BROAD-STATE 4x2500 span extraction."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30"
DECISION = "broad_state_4x2500_span_extraction_completed_rating_ready"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--head-before", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--public-pages-visible", choices=("true", "false"), required=True)
    args = parser.parse_args()
    summary = json.loads((OUT / "span_extraction_summary.json").read_text())
    status = {
        "task_id": "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30",
        "final_decision": DECISION,
        "created_at": now(),
        "commit_hash": args.commit,
        "push_succeeded": args.push_succeeded == "true",
        "head_before": args.head_before,
        "head_after": git("rev-parse", "HEAD"),
        "public_pages_url": "https://dkyaya.github.io/gabriel-wages/",
        "public_pages_visible_current": args.public_pages_visible == "true",
        "summary": summary,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "forbidden_actions_avoided": True,
        "blockers_or_uncertainties": [
            "Deterministic candidate labels require downstream rating.",
            "Prior normalized text does not preserve PDF page separators for every source; character, line, and paragraph offsets are retained.",
        ],
        "next_task": "BROAD-STATE-4X2500-SPAN-RATING-2026-07-30",
    }
    relay_status = ROOT / "tmp/broad_state_4x2500_span_extraction_relay_status_2026-07-30.json"
    relay_status.parent.mkdir(parents=True, exist_ok=True)
    relay_status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    names = [
        "span_extraction_manifest.json", "span_extraction_summary.md",
        "span_extraction_summary.json", "span_extraction_lane_distribution.json",
        "span_extraction_lane_distribution.md", "source_level_span_summary.json",
        "evidence_category_summary.json", "mechanism_attribute_summary.json",
        "quant_span_type_summary.json", "qualitative_mechanism_type_summary.json",
        "priority_span_summary.json", "source_family_span_summary.json",
        "geography_span_summary.json", "cba_non_cba_span_summary.json",
        "span_rating_ready_manifest.json", "coverage_rate_map_metric_update_report.json",
        "dashboard_map_semantics_validation.json", "extracted_text_hash_recheck_report.json",
        "validation_report.json", "validation_report.md", "forbidden_action_audit.json",
        "staged_file_audit.json", "large_file_audit.json", "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md", "dashboard_public_pages_smoke_report.json",
        "dashboard_local_build_report.json", "next_task.md",
    ]
    for lane in ("001", "002", "003", "004"):
        names.extend([
            f"span_extraction_lane_{lane}_results.csv",
            f"span_extraction_lane_{lane}_results.jsonl",
            f"lanes/span_extraction_lane_{lane}/lane_summary.json",
            f"lanes/span_extraction_lane_{lane}/checkpoint.json",
        ])
    missing = [name for name in names if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError(f"relay required files missing: {missing}")
    zip_path = ROOT / f"tmp/broad_state_4x2500_span_extraction_relay_2026-07-30_{args.commit}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(relay_status, arcname="BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30/relay_status.json")
        for name in names:
            archive.write(OUT / name, arcname=f"BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30/{name}")
        for script in (
            ROOT / "scripts/run_broad_state_4x2500_span_extraction.py",
            ROOT / "scripts/test_broad_state_4x2500_span_extraction.py",
        ):
            archive.write(script, arcname=f"scripts/{script.name}")
    print(zip_path)


if __name__ == "__main__":
    main()
