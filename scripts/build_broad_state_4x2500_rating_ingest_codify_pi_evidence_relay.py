#!/usr/bin/env python3
"""Build the bounded relay ZIP for rating ingestion/codification and PI evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30"
TASK = "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30"
DECISION = "broad_state_4x2500_rating_ingest_codify_completed_normalization_matching_ready"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def read_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--head-before", required=True)
    parser.add_argument("--push-succeeded", choices=("true", "false"), required=True)
    parser.add_argument("--public-pages-visible", choices=("true", "false"), required=True)
    args = parser.parse_args()

    summary = read_json("rating_ingest_codify_summary.json")
    claims = read_json("careful_claim_candidates.json")
    mechanism = read_json("mechanism_cluster_summary.json")
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
        "valid_rating_input_count": summary["valid_rating_input_count"],
        "quarantine_count": summary["quarantine_count"],
        "codified_record_count": summary["codified_record_count"],
        "careful_claim_candidate_count": summary["careful_claim_candidate_count"],
        "finding_classification_counts": summary["finding_classification_counts"],
        "report_usability_counts": summary["report_usability_counts"],
        "top_mechanism_clusters": mechanism["clusters"],
        "claim_ids": [row["claim_id"] for row in claims["claims"]],
        "directionality_counts": summary["directionality_counts"],
        "normalization_blocker_counts": summary["normalization_blocker_counts"],
        "causal_prevalence_boundary": {
            "causal_claim_allowed": False,
            "population_prevalence_claim_allowed": False,
            "national_prevalence_claim_allowed": False,
            "global_analysis_readiness": False,
        },
        "dashboard_cleaned_format_preserved": True,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "dashboard_local_build_passed": read_json("dashboard_local_build_report.json")["status"] == "passed",
        "dashboard_local_browser_passed": read_json("dashboard_browser_smoke_report.json")["status"] == "passed",
        "dashboard_public_pages_passed": read_json("dashboard_public_pages_smoke_report.json")["status"] == "passed",
        "forbidden_actions_avoided": read_json("forbidden_action_audit.json")["passed"],
        "pi_evidence_base_format": "verified CSV table set; XLSX omitted because the required artifact-tool dependency loader was unavailable",
        "blockers_or_uncertainties": [
            "11,548 valid ratings contain quantitative values requiring one or more normalization operations before comparison.",
            "No matched city-cycle structure, wage-gap estimate, regression, population-prevalence claim, or causal claim is included.",
            "Directional evidence remains documentary and uneven; most records are neutral/general or not applicable.",
        ],
        "next_task": "BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-2026-07-30",
    }
    relay_status = ROOT / "tmp/broad_state_4x2500_rating_ingest_codify_pi_evidence_relay_status_2026-07-30.json"
    relay_status.parent.mkdir(parents=True, exist_ok=True)
    relay_status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    names = [
        "rating_ingest_codify_manifest.json",
        "rating_ingest_codify_summary.md",
        "rating_ingest_codify_summary.json",
        "codified_valid_ratings_manifest.json",
        "quarantine_exclusion_summary.json",
        "quarantine_exclusion_summary.md",
        "mechanism_cluster_summary.json",
        "mechanism_cluster_summary.md",
        "mechanism_cluster_strength_table.csv",
        "mechanism_cluster_strength_table.json",
        "evidence_category_codified_summary.json",
        "claim_relevance_codified_summary.json",
        "report_usability_codified_summary.json",
        "directionality_codified_summary.json",
        "quantitative_readiness_codified_summary.json",
        "normalization_blocker_codified_summary.json",
        "causal_boundary_codified_summary.json",
        "careful_claim_candidates.json",
        "careful_claim_candidates.md",
        "careful_claim_candidates.csv",
        "careful_claim_boundary_table.csv",
        "careful_claim_boundary_table.json",
        "pi_report_core_findings_candidates.md",
        "pi_report_core_findings_candidates.json",
        "pi_report_supporting_findings_candidates.md",
        "pi_report_supporting_findings_candidates.json",
        "pi_report_context_findings_candidates.md",
        "pi_report_context_findings_candidates.json",
        "pi_report_exclusion_and_limits.md",
        "pi_report_exclusion_and_limits.json",
        "pi_report_evidence_base_tables_manifest.json",
        "pi_report_evidence_base_summary.md",
        "pi_report_claim_language_bank.md",
        "pi_report_section_outline.md",
        "pi_report_draft_skeleton.md",
        "report_ready_examples.jsonl",
        "report_ready_examples.md",
        "mechanism_specific_ingested_summaries.json",
        "mechanism_specific_ingested_summaries.md",
        "source_family_ingested_summary.json",
        "geography_ingested_summary.json",
        "cba_non_cba_ingested_summary.json",
        "dashboard_ingestion_update_summary.json",
        "dashboard_local_build_report.json",
        "dashboard_browser_smoke_report.json",
        "dashboard_browser_smoke_report.md",
        "dashboard_public_pages_smoke_report.json",
        "validation_report.json",
        "validation_report.md",
        "forbidden_action_audit.json",
        "staged_file_audit.json",
        "large_file_audit.json",
        "next_task.md",
    ]
    names.extend(
        name
        for name in [
            "pi_report_evidence_base_overview.csv",
            "pi_report_evidence_base_mechanism_clusters.csv",
            "pi_report_evidence_base_claim_candidates.csv",
            "pi_report_evidence_base_claim_boundaries.csv",
            "pi_report_evidence_base_normalization_blockers.csv",
            "pi_report_evidence_base_directionality.csv",
            "dashboard_local_smoke.png",
            "dashboard_public_pages_smoke.png",
        ]
        if (OUT / name).is_file()
    )
    missing = [name for name in names if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError(f"relay required files missing: {missing}")

    zip_path = ROOT / f"tmp/broad_state_4x2500_rating_ingest_codify_pi_evidence_relay_2026-07-30_{args.commit}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(relay_status, arcname=f"{TASK}/relay_status.json")
        for name in names:
            archive.write(OUT / name, arcname=f"{TASK}/{name}")
        for script in (
            ROOT / "scripts/run_broad_state_4x2500_rating_ingest_codify_pi_evidence.py",
            ROOT / "scripts/build_broad_state_4x2500_rating_ingest_codify_pi_evidence_relay.py",
        ):
            archive.write(script, arcname=f"scripts/{script.name}")
    print(zip_path)


if __name__ == "__main__":
    main()
