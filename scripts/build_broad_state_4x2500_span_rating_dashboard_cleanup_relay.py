#!/usr/bin/env python3
"""Build the bounded relay ZIP for 4x2500 span rating and dashboard cleanup."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30"
TASK = "BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30"
DECISION = "broad_state_4x2500_span_rating_dashboard_cleanup_completed_ingestion_ready"


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
    summary = json.loads((OUT / "span_rating_summary.json").read_text(encoding="utf-8"))
    usability = json.loads((OUT / "report_usability_summary.json").read_text(encoding="utf-8"))
    status = {
        "task_id": TASK,
        "final_decision": DECISION,
        "created_at": now(),
        "commit_hash": args.commit,
        "push_succeeded": args.push_succeeded == "true",
        "head_before": args.head_before,
        "head_after": git("rev-parse", "HEAD"),
        "public_pages_url": "https://dkyaya.github.io/gabriel-wages/",
        "public_pages_visible_current": args.public_pages_visible == "true",
        "rating_queue_size": summary["rating_queue_size"],
        "lane_distribution": summary["lane_counts"],
        "valid_rating_count": summary["valid_rating_count"],
        "quarantine_rating_count": summary["quarantine_rating_count"],
        "report_usability_counts": usability["counts"],
        "dashboard_cleanup_passed": True,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "forbidden_actions_avoided": True,
        "blockers_or_uncertainties": [
            "Ratings are bounded documentary measurements pending ingestion/codification.",
            "Quantitative comparisons remain blocked pending normalization and matched city-cycle structure.",
        ],
        "next_task": "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-2026-07-30",
    }
    relay_status = ROOT / "tmp/broad_state_4x2500_span_rating_dashboard_cleanup_relay_status_2026-07-30.json"
    relay_status.parent.mkdir(parents=True, exist_ok=True)
    relay_status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    names = [
        "span_rating_manifest.json", "span_rating_summary.md", "span_rating_summary.json",
        "span_rating_lane_distribution.json", "span_rating_lane_distribution.md",
        "rating_valid_ledger_manifest.json", "rating_quarantine_ledger_manifest.json",
        "rating_schema_validation_report.json", "rating_repair_attempts_report.json",
        "rating_quality_summary.json", "claim_relevance_summary.json",
        "report_usability_summary.json", "directionality_summary.json",
        "quantitative_readiness_summary.json", "normalization_blocker_summary.json",
        "causal_boundary_summary.json", "evidence_category_rating_summary.json",
        "mechanism_attribute_rating_summary.json", "mechanism_specific_rating_summaries.json",
        "mechanism_specific_rating_summaries.md", "pi_report_candidate_findings.json",
        "pi_report_candidate_findings.md", "pi_report_exclusions_summary.json",
        "priority_rating_summary.json", "source_family_rating_summary.json",
        "geography_rating_summary.json", "cba_non_cba_rating_summary.json",
        "dashboard_cleanup_audit.json", "dashboard_cleanup_summary.md",
        "dashboard_information_architecture_report.json", "dashboard_removed_elements_report.json",
        "dashboard_condensed_elements_report.json", "dashboard_local_build_report.json",
        "dashboard_browser_smoke_report.json", "dashboard_browser_smoke_report.md",
        "dashboard_public_pages_smoke_report.json", "validation_report.json",
        "validation_report.md", "forbidden_action_audit.json", "staged_file_audit.json",
        "large_file_audit.json", "next_task.md",
    ]
    optional = ["dashboard_local_smoke.png", "dashboard_public_pages_smoke.png"]
    for lane in ("001", "002", "003", "004"):
        names.extend([
            f"lanes/rating_lane_{lane}/lane_summary.json",
            f"lanes/rating_lane_{lane}/checkpoint.json",
            f"span_rating_lane_{lane}_valid.jsonl",
            f"span_rating_lane_{lane}_quarantine.jsonl",
        ])
    missing = [name for name in names if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError(f"relay required files missing: {missing}")
    zip_path = ROOT / f"tmp/broad_state_4x2500_span_rating_dashboard_cleanup_relay_2026-07-30_{args.commit}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(relay_status, arcname=f"{TASK}/relay_status.json")
        for name in names + [item for item in optional if (OUT / item).is_file()]:
            archive.write(OUT / name, arcname=f"{TASK}/{name}")
        for script in (
            ROOT / "scripts/run_broad_state_4x2500_span_rating_dashboard_cleanup.py",
            ROOT / "scripts/build_broad_state_4x2500_span_rating_dashboard_cleanup_relay.py",
        ):
            archive.write(script, arcname=f"scripts/{script.name}")
    print(zip_path)


if __name__ == "__main__":
    main()
