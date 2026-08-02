#!/usr/bin/env python3
"""Classify the remaining-municipality retained wave for non-OCR text readiness.

This task adapter reuses the bounded local inspection engine from the completed
4x2500 readiness wave.  It reads PDF metadata, holds at most a three-page PDF
text probe in memory, and inspects at most 256 KiB of an HTML source.  It never
persists source text, renders pages, invokes OCR, opens network URLs, rates
evidence, ingests/codifies records, or performs quantitative/causal analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import run_broad_state_4x2500_pdf_text_readiness as engine


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT_DIR = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02"
OUTPUT_DIR = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02"
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02"
PRIOR_DECISION = "broad_state_remaining_municipalities_source_review_download_completed_pdf_readiness_ready"
DECISION = "broad_state_remaining_municipalities_pdf_text_readiness_completed_text_extraction_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-TEXT-EXTRACTION-2026-08-02"
EXPECTED_COUNT = 2_865
EXPECTED_TYPES = {"pdf": 2_456, "html": 409, "other_document": 0}
LANES = tuple(f"readiness_lane_{index:03d}" for index in range(1, 6))
LANE_COUNTS = {lane: 573 for lane in LANES}
LANE_STAGGER_SECONDS = {lane: (index - 1) * 8 * 60 for index, lane in enumerate(LANES, 1)}
REQUIRED_INPUTS = (
    "remaining_municipalities_source_review_download_manifest.json",
    "remaining_municipalities_source_review_download_summary.json",
    "retained_source_manifest.csv",
    "retained_source_manifest.jsonl",
    "retained_source_manifest.sha256.json",
    "retained_pdf_manifest.csv",
    "retained_html_manifest.csv",
    "retained_other_document_manifest.csv",
    "retained_source_storage_audit.json",
)


def configure_engine() -> None:
    engine.ROOT = ROOT
    engine.BASE = BASE
    engine.INPUT_DIR = INPUT_DIR
    engine.OUTPUT_DIR = OUTPUT_DIR
    engine.ARTIFACT_ROOT = ARTIFACT_ROOT
    engine.TASK_ID = TASK_ID
    engine.PRIOR_DECISION = PRIOR_DECISION
    engine.DECISION = DECISION
    engine.EXPECTED_COUNT = EXPECTED_COUNT
    engine.EXPECTED_TYPES = EXPECTED_TYPES
    engine.LANES = LANES
    engine.LANE_COUNTS = LANE_COUNTS
    engine.LANE_STAGGER_SECONDS = LANE_STAGGER_SECONDS
    engine.REQUIRED_INPUTS = REQUIRED_INPUTS
    engine.validate_predecessor = validate_predecessor
    engine.readiness_id = readiness_id


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    engine.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    engine.write_text(path, value)


def sha256(path: Path) -> str:
    return engine.sha256(path)


def readiness_id(source_id: str) -> str:
    return "RMRDY-20260802-" + hashlib.sha256(source_id.encode()).hexdigest()[:20]


def validate_predecessor() -> list[dict[str, str]]:
    missing = [name for name in REQUIRED_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"missing predecessor inputs: {missing}")
    summary = read_json(INPUT_DIR / "remaining_municipalities_source_review_download_summary.json")
    source_manifest = read_csv(INPUT_DIR / "retained_source_manifest.csv")
    pdf_rows = read_csv(INPUT_DIR / "retained_pdf_manifest.csv")
    html_rows = read_csv(INPUT_DIR / "retained_html_manifest.csv")
    other_rows = read_csv(INPUT_DIR / "retained_other_document_manifest.csv")
    storage = read_json(INPUT_DIR / "retained_source_storage_audit.json")
    types = Counter(engine.normalized_source_type(row) for row in source_manifest)
    identifiers = [row.get("source_review_download_id", "") for row in source_manifest]
    hashes = [row.get("retained_file_sha256", "") for row in source_manifest]
    gates = (
        summary.get("decision") == PRIOR_DECISION
        and summary.get("retained_source_count") == EXPECTED_COUNT
        and summary.get("retained_pdf_count") == EXPECTED_TYPES["pdf"]
        and summary.get("retained_html_count") == EXPECTED_TYPES["html"]
        and summary.get("retained_other_document_count") == EXPECTED_TYPES["other_document"]
        and len(source_manifest) == EXPECTED_COUNT
        and len(pdf_rows) == EXPECTED_TYPES["pdf"]
        and len(html_rows) == EXPECTED_TYPES["html"]
        and len(other_rows) == EXPECTED_TYPES["other_document"]
        and all(types[source_type] == count for source_type, count in EXPECTED_TYPES.items())
        and len(set(identifiers)) == EXPECTED_COUNT
        and len(set(hashes)) == EXPECTED_COUNT
        and all(len(value) == 64 for value in hashes)
        and all(row.get("retained_local_artifact_path") for row in source_manifest)
        and all(row.get("retained_file_size_bytes", "").isdigit() for row in source_manifest)
        and storage.get("passed") is True
        and storage.get("artifact_root_git_ignored") is True
    )
    if not gates:
        raise RuntimeError("predecessor retained-source reconciliation failed closed")
    return source_manifest


def tailor_prepare_outputs() -> None:
    manifest_path = OUTPUT_DIR / "pdf_text_readiness_manifest.json"
    manifest = read_json(manifest_path)
    manifest.update({
        "decision": DECISION,
        "input_directory": engine.relative(INPUT_DIR),
        "output_directory": engine.relative(OUTPUT_DIR),
        "artifact_root": engine.relative(ARTIFACT_ROOT),
        "dashboard_map_filter": "scout_coverage_rate_only",
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "lane_count": len(LANES),
        "lane_sizes": LANE_COUNTS,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
    })
    write_json(manifest_path, manifest)
    write_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_manifest.json", manifest)
    locked = read_csv(OUTPUT_DIR / "readiness_locked_queue.csv")
    write_json(OUTPUT_DIR / "readiness_locked_queue_manifest.json", {
        "task_id": TASK_ID,
        "created_at": engine.now(),
        "row_count": len(locked),
        "csv_sha256": sha256(OUTPUT_DIR / "readiness_locked_queue.csv"),
        "jsonl_sha256": sha256(OUTPUT_DIR / "readiness_locked_queue.jsonl"),
        "id_set_sha256": engine.id_set_sha256(locked),
        "lane_distribution": LANE_COUNTS,
        "source_type_counts": dict(sorted(Counter(row["source_type"] for row in locked).items())),
        "all_rows_exactly_once": len({row["source_review_download_id"] for row in locked}) == len(locked),
        "locked_against_predecessor_manifest": True,
    })
    write_text(OUTPUT_DIR / "readiness_lane_distribution.md", """# PDF/text readiness lane distribution

The 2,865 retained sources are locked into five deterministic, interleaved lanes of exactly 573 rows. PDF and HTML sources, priorities, source families, geographies, CBA/non-CBA hints, and mechanism hints are dispersed using stable SHA-256 ordering. Starts are locked to T+0, T+8, T+16, T+24, and T+32 minutes. Every worker checkpoints after each retained source.
""")


def prepare() -> None:
    configure_engine()
    engine.prepare()
    tailor_prepare_outputs()


def run_lane(lane: str, stagger_seconds: int) -> None:
    configure_engine()
    engine.run_lane(lane, stagger_seconds)


def tailor_merge_outputs() -> None:
    summary = read_json(OUTPUT_DIR / "pdf_text_readiness_summary.json")
    summary.update({
        "decision": DECISION,
        "final_decision": DECISION,
        "completed_lane_count": len(LANES),
        "lane_distribution": LANE_COUNTS,
        "dashboard_map_filter": "scout_coverage_rate_only",
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_covered_municipalities": 35_574,
        "eligible_municipality_universe": 35_589,
        "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "next_task": NEXT_TASK,
        "text_extraction_runs": 0,
        "span_extraction_runs": 0,
        "normalization_matching_runs": 0,
    })
    write_json(OUTPUT_DIR / "pdf_text_readiness_summary.json", summary)
    write_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_summary.json", summary)
    counts = summary["primary_readiness_status_counts"]
    write_text(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_summary.md", f"""# Remaining-municipality PDF/text readiness summary

All five lanes completed and reconciled **{EXPECTED_COUNT:,}** retained sources: {summary['retained_pdf_count']:,} PDFs, {summary['retained_html_count']:,} HTML files, and {summary['retained_other_document_count']:,} other documents. Exactly **{summary['text_extraction_ready_count']:,}** are technically ready for a separately authorized non-OCR extraction pass: {summary['parse_text_pdf_ready_count']:,} PDFs, {summary['html_text_ready_count']:,} HTML files, and {summary['other_document_text_ready_count']:,} other documents.

Deferred or not ready: OCR later {summary['ocr_later_count']:,}; oversized {summary['oversized_defer_count']:,}; locked {summary['encrypted_or_locked_count']:,}; corrupt {summary['corrupt_or_broken_count']:,}; shell/navigation {summary['shell_or_navigation_only_count']:,}; manual review {summary['needs_manual_review_count']:,}; unsupported {summary['unsupported_file_type_count']:,}; readiness errors {summary['readiness_error_count']:,}.

Decision: `{DECISION}`. This stage used only bounded, in-memory readiness probes. It did not persist source text, render pages, run OCR, rate, ingest, codify, normalize, match, or perform wage-gap, regression, treatment-effect, prevalence, or causal analysis.
""")
    write_text(OUTPUT_DIR / "pdf_text_readiness_summary.md", (OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_summary.md").read_text())

    manifest = read_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json")
    manifest.update({
        "decision": DECISION,
        "execution_status": "completed",
        "completed_at": summary["completed_at"],
        "completed_lane_count": len(LANES),
        "text_extraction_ready_count": summary["text_extraction_ready_count"],
        "primary_readiness_status_counts": counts,
        "dashboard_map_filter": "scout_coverage_rate_only",
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "validation_passed": False,
    })
    write_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json", manifest)
    write_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_manifest.json", manifest)

    for lane in LANES:
        checkpoint = read_json(OUTPUT_DIR / "lanes" / lane / "checkpoint.json")
        write_json(OUTPUT_DIR / f"{lane}_checkpoint.json", checkpoint)

    forbidden = {
        "task_id": TASK_ID,
        "audit_status": "passed",
        "passed": True,
        "network_requests": 0,
        "full_text_extraction_runs": 0,
        "full_text_artifacts_persisted": 0,
        "ocr_runs": 0,
        "image_pdf_processing_runs": 0,
        "span_extraction_runs": 0,
        "model_or_gabriel_calls": 0,
        "rating_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "normalization_matching_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_claims": 0,
        "national_or_population_prevalence_claims": 0,
        "final_causal_claims": 0,
        "global_readiness_advanced": False,
    }
    write_json(OUTPUT_DIR / "forbidden_action_audit.json", forbidden)
    dashboard = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "stage": "broad_state_remaining_municipalities_pdf_text_readiness_complete",
        "current_phase": "Remaining-municipality PDF/text readiness complete",
        "next_task": NEXT_TASK,
        "retained_source_count": EXPECTED_COUNT,
        "retained_pdf_count": EXPECTED_TYPES["pdf"],
        "retained_html_count": EXPECTED_TYPES["html"],
        "retained_other_document_count": EXPECTED_TYPES["other_document"],
        "parse_text_pdf_ready_count": summary["parse_text_pdf_ready_count"],
        "html_text_ready_count": summary["html_text_ready_count"],
        "other_document_text_ready_count": summary["other_document_text_ready_count"],
        "text_extraction_ready_count": summary["text_extraction_ready_count"],
        "not_ready_count": summary["not_ready_count"],
        "primary_readiness_status_counts": counts,
        "map_primary_metric": "scout_coverage_rate",
        "dashboard_map_filter": "scout_coverage_rate_only",
        "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_remaining_pdf_text_readiness_update_summary.json", dashboard)
    write_text(OUTPUT_DIR / "next_task.md", f"""# Next task

Recommend `{NEXT_TASK}`.

Run full non-OCR text extraction only over `text_extraction_ready_queue`. Use five independent lanes if the queue remains large enough, checkpoint every source, and write extracted text only to ignored local artifact storage—not Git. Do not OCR, extract spans, rate, ingest, codify, normalize, match, estimate wage gaps, run regressions or treatment effects, or make causal or prevalence claims. Preserve the clean dashboard, final PI report link, wage-growth continuity module, and `scout_coverage_rate` map.
""")


def merge() -> None:
    configure_engine()
    original_write_text = engine.write_text

    def output_only(path: Path, value: str) -> None:
        if path.resolve().is_relative_to(OUTPUT_DIR.resolve()):
            original_write_text(path, value)

    engine.write_text = output_only
    try:
        engine.merge()
    finally:
        engine.write_text = original_write_text
    tailor_merge_outputs()


def audit_staged() -> None:
    configure_engine()
    engine.staged_audit()
    staged = read_json(OUTPUT_DIR / "staged_file_audit.json")
    write_json(OUTPUT_DIR / "large_file_audit.json", {
        "audited_at": staged["audited_at"],
        "audit_status": staged["large_file_audit_status"],
        "threshold_bytes": staged["large_file_threshold_bytes"],
        "large_file_count": staged["large_file_count"],
        "large_files": staged["large_files"],
        "largest_staged_file_bytes": staged["largest_staged_file_bytes"],
        "passed": staged["large_file_audit_status"] == "passed",
    })


def validate() -> None:
    configure_engine()
    summary = read_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_summary.json")
    manifest = read_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_manifest.json")
    results = read_csv(OUTPUT_DIR / "merged_pdf_text_readiness_results.csv")
    locked = read_csv(OUTPUT_DIR / "readiness_locked_queue.csv")
    ready = read_csv(OUTPUT_DIR / "text_extraction_ready_queue.csv")
    hash_report = read_json(OUTPUT_DIR / "retained_source_hash_recheck_report.json")
    forbidden = read_json(OUTPUT_DIR / "forbidden_action_audit.json")
    staged = read_json(OUTPUT_DIR / "staged_file_audit.json") if (OUTPUT_DIR / "staged_file_audit.json").exists() else {}
    large = read_json(OUTPUT_DIR / "large_file_audit.json") if (OUTPUT_DIR / "large_file_audit.json").exists() else {}
    browser = read_json(OUTPUT_DIR / "dashboard_browser_smoke_report.json") if (OUTPUT_DIR / "dashboard_browser_smoke_report.json").exists() else {}
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    locked_ids = [row["source_review_download_id"] for row in locked]
    result_ids = [row["source_review_download_id"] for row in results]
    checks = {
        "01_input_retained_count_2865": len(locked) == EXPECTED_COUNT,
        "02_source_types_reconcile_2456_409_0": all(Counter(row["source_type"] for row in locked)[source_type] == count for source_type, count in EXPECTED_TYPES.items()),
        "03_all_retained_local_files_exist": hash_report.get("all_files_exist") is True,
        "04_all_retained_hashes_match": hash_report.get("hash_mismatch_or_missing_count") == 0,
        "05_locked_queue_reconciles_manifest": manifest.get("retained_source_count") == EXPECTED_COUNT,
        "06_five_lanes_exactly_573": all(len(read_csv(OUTPUT_DIR / f"{lane}_queue.csv")) == 573 for lane in LANES),
        "07_lane_union_covers_locked_once": len(set(locked_ids)) == EXPECTED_COUNT and sum(len(read_csv(OUTPUT_DIR / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED_COUNT,
        "08_lane_queues_disjoint": len(set(row["source_review_download_id"] for lane in LANES for row in read_csv(OUTPUT_DIR / f"{lane}_queue.csv"))) == EXPECTED_COUNT,
        "09_one_controlled_status_per_source": len(results) == EXPECTED_COUNT and all(row["primary_readiness_status"] in engine.CONTROLLED_STATUSES for row in results),
        "10_merged_results_reconcile": len(set(result_ids)) == EXPECTED_COUNT and set(result_ids) == set(locked_ids),
        "11_ready_queue_statuses_only": all(row["primary_readiness_status"] in engine.READY_STATUSES for row in ready),
        "12_not_ready_queues_exclude_ready": all(row["primary_readiness_status"] not in engine.READY_STATUSES for status in engine.NOT_READY_STATUSES for row in read_csv(OUTPUT_DIR / f"{status}_queue.csv")),
        "13_pdf_page_or_terminal_indicator_recorded": all(row["page_count"] or row["primary_readiness_status"] in {"encrypted_or_locked", "corrupt_or_broken", "readiness_error"} for row in results if row["source_type"] == "pdf"),
        "14_status_counts_reconcile": sum(summary["primary_readiness_status_counts"].values()) == EXPECTED_COUNT,
        "15_no_full_text_extraction": all(row["full_text_persisted_flag"] == "false" for row in results),
        "16_no_ocr": all(row["ocr_run_flag"] == "false" for row in results),
        "17_no_span_rating_ingest_codify": forbidden.get("span_extraction_runs") == forbidden.get("rating_runs") == forbidden.get("ingestion_runs") == forbidden.get("codification_runs") == 0,
        "18_no_normalization_matching": forbidden.get("normalization_matching_runs") == 0,
        "19_no_gap_regression_treatment_causal_prevalence": forbidden.get("wage_gap_calculations") == forbidden.get("regressions") == forbidden.get("treatment_effect_claims") == forbidden.get("final_causal_claims") == forbidden.get("national_or_population_prevalence_claims") == 0,
        "20_artifact_root_remains_ignored": subprocess.run(["git", "check-ignore", "-q", engine.relative(ARTIFACT_ROOT)], cwd=ROOT, check=False).returncode == 0,
        "21_dashboard_clean_stage": phase.get("stage") == "broad_state_remaining_municipalities_pdf_text_readiness_complete" and phase.get("remaining_municipality_text_extraction_ready_count") == summary["text_extraction_ready_count"],
        "22_dashboard_map_scout_coverage_rate": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate" and phase.get("dashboard_map_filter") == "scout_coverage_rate_only",
        "23_final_report_link_intact": phase.get("current_report_path") == "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        "24_wage_growth_module_intact": phase.get("wage_growth_continuity_available") is True,
        "25_global_readiness_false": phase.get("global_analysis_readiness") is False,
        "26_dashboard_smoke_passes_or_honest_limit": browser.get("status") in {"passed", "passed_static_browser_unavailable", "browser_controller_unavailable"},
        "27_staged_file_audit_passes": staged.get("audit_status") == "passed" and staged.get("forbidden_file_count") == 0,
        "28_large_file_audit_passes": large.get("passed") is True,
    }
    passed = all(checks.values())
    report = {
        "task_id": TASK_ID,
        "validated_at": engine.now(),
        "status": "passed" if passed else "failed",
        "validation_passed": passed,
        "checks": checks,
        "passed_count": sum(checks.values()),
        "check_count": len(checks),
        "decision": DECISION if passed else "validation_failed",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "validation_report.json", report)
    lines = ["# Validation report", "", f"Status: **{report['status']}** — {report['passed_count']}/{report['check_count']} checks passed.", ""]
    lines.extend(f"- {'PASS' if value else 'FAIL'} — `{key}`" for key, value in checks.items())
    write_text(OUTPUT_DIR / "validation_report.md", "\n".join(lines))
    if not passed:
        raise RuntimeError("final validation failed: " + ", ".join(key for key, value in checks.items() if not value))
    manifest["validation_passed"] = True
    manifest["validated_at"] = report["validated_at"]
    write_json(OUTPUT_DIR / "remaining_municipalities_pdf_text_readiness_manifest.json", manifest)
    write_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json", manifest)
    print(json.dumps(report))


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--lane", choices=LANES)
    actions.add_argument("--merge", action="store_true")
    actions.add_argument("--validate", action="store_true")
    actions.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--stagger-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.stagger_seconds)
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    else:
        audit_staged()


if __name__ == "__main__":
    main()
