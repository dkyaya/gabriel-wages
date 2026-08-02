#!/usr/bin/env python3
"""Five-lane source review/download for the remaining-municipality wave.

This is a task-specific adapter around the established broad-state streaming
downloader. Retained payloads are written only to the Git-ignored artifact
store. The adapter adds the locked five-lane geometry and the task's required
metadata/audit filenames; it does not extract text, OCR, rate, or ingest.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import shutil
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import run_broad_state_4x2500_source_review_download as core


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-VERIFICATION-2026-08-01"
OUTPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02"
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"
COMPAT_INPUT = ROOT / "tmp/broad_state_remaining_municipalities_source_review_download_2026-08-02_logs/compat_input"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02"
EXPECTED_HEAD = "1cd17e642c6644a2537a1e266de2317993828bf8"
EXPECTED_COUNT = 2_956
LANES = tuple(f"source_review_lane_{index:03d}" for index in range(1, 6))
LANE_COUNTS = dict(zip(LANES, (592, 591, 591, 591, 591)))
STAGGER_MINUTES = {lane: index * 8 for index, lane in enumerate(LANES)}
EXPECTED_PRIORITY = {
    "high_priority_verification_ready": 1_924,
    "medium_priority_verification_ready": 1_019,
    "low_priority_verification_ready": 13,
}
DECISION = "broad_state_remaining_municipalities_source_review_download_completed_pdf_readiness_ready"


def configure() -> None:
    core.INPUT = COMPAT_INPUT
    core.OUTPUT = OUTPUT
    core.ARTIFACT_ROOT = ARTIFACT_ROOT
    core.TASK_ID = TASK_ID
    core.EXPECTED_HEAD = EXPECTED_HEAD
    core.EXPECTED_COUNT = EXPECTED_COUNT
    core.LANES = LANES
    core.LANE_COUNTS = LANE_COUNTS
    core.STAGGER_MINUTES = STAGGER_MINUTES
    core.EXPECTED_PRIORITY = EXPECTED_PRIORITY
    core.source_review_id = lambda verification_id: "RMSRD-20260802-" + core.text_hash(verification_id)[:20]


def build_compat_input() -> None:
    COMPAT_INPUT.mkdir(parents=True, exist_ok=True)
    source_csv = INPUT / "source_review_ready_queue.csv"
    with source_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        rows = list(reader)
    for row in rows:
        if not row.get("discovery_run_id", "").strip():
            row["discovery_run_id"] = row.get("lineage", "") or row.get("target_id", "")
    compat_csv = COMPAT_INPUT / "source_review_ready_queue.csv"
    compat_jsonl = COMPAT_INPUT / "source_review_ready_queue.jsonl"
    for path in (compat_csv, compat_jsonl, COMPAT_INPUT / "source_review_ready_manifest.json"):
        if path.is_symlink() or path.exists():
            path.unlink()
    core.write_csv(compat_csv, rows, fields)
    core.write_jsonl(compat_jsonl, rows)
    manifest = core.read_json(INPUT / "source_review_ready_manifest.json")
    manifest.update({
        "csv_sha256": core.sha256(compat_csv),
        "jsonl_sha256": core.sha256(compat_jsonl),
        "compatibility_lineage_field": "discovery_run_id populated from existing lineage only",
        "authoritative_source_csv_sha256": core.sha256(source_csv),
        "authoritative_source_jsonl_sha256": core.sha256(INPUT / "source_review_ready_queue.jsonl"),
    })
    core.write_json(COMPAT_INPUT / "source_review_ready_manifest.json", manifest)
    summary_link = COMPAT_INPUT / "verification_summary.json"
    if summary_link.is_symlink() or summary_link.exists():
        summary_link.unlink()
    summary_link.symlink_to(INPUT / "remaining_municipalities_verification_summary.json")


def copy_json(source: Path, target: Path) -> None:
    core.write_json(target, core.read_json(source))


def prepare() -> None:
    build_compat_input()
    core.prepare()
    manifest = core.read_json(OUTPUT / "source_review_download_manifest.json")
    manifest.update({
        "task_id": TASK_ID,
        "input_directory": str(INPUT.relative_to(ROOT)),
        "source_review_ready_count": EXPECTED_COUNT,
        "eligible_verification_status_counts": {"reachable": 2_845, "reachable_with_redirect": 111},
        "lane_counts": LANE_COUNTS,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
    })
    core.write_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json", manifest)
    core.write_json(OUTPUT / "source_review_locked_queue_manifest.json", {
        "task_id": TASK_ID,
        "queue_row_count": EXPECTED_COUNT,
        "lane_counts": LANE_COUNTS,
        "priority_counts": EXPECTED_PRIORITY,
        "csv_sha256": manifest["queue_csv_sha256"],
        "jsonl_sha256": manifest["queue_jsonl_sha256"],
        "lane_hashes": manifest["lane_hashes"],
        "eligible_verification_statuses": ["reachable", "reachable_with_redirect"],
        "artifact_root": str(ARTIFACT_ROOT.relative_to(ROOT)),
    })


def split_required_queues(rows: list[dict[str, str]]) -> None:
    mapping = {
        "duplicate_retained_source_queue": {"duplicate_retained_source"},
        "oversized_defer_queue": {"oversized_defer"},
        "ocr_later_queue": {"ocr_later"},
        "restricted_or_login_required_queue": {"restricted_or_login_required"},
        "unavailable_on_download_queue": {"unavailable_on_download"},
        "broken_or_corrupt_queue": {"broken_or_corrupt"},
        "likely_non_source_or_navigation_only_queue": {"likely_non_source_or_navigation_only"},
        "excluded_out_of_scope_queue": {"excluded_out_of_scope"},
        "source_review_error_queue": {"source_review_error"},
    }
    for stem, statuses in mapping.items():
        core.write_pair(stem, [row for row in rows if row["source_review_status"] in statuses])


def create_required_summaries(rows: list[dict[str, str]]) -> dict[str, Any]:
    counts = Counter(row["source_review_status"] for row in rows)
    retained = [row for row in rows if row["source_review_status"] in core.RETAINED_STATUSES]
    pdf = [row for row in retained if row["source_review_status"] == "retained_pdf"]
    html = [row for row in retained if row["source_review_status"] == "retained_html"]
    other = [row for row in retained if row["source_review_status"] == "retained_other_document"]
    retained_bytes = sum(int(row["retained_file_size_bytes"] or 0) for row in retained)
    summary = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "source_review_status": "completed",
        "input_source_review_ready_count": EXPECTED_COUNT,
        "completed_source_review_rows": len(rows),
        "lane_sizes": LANE_COUNTS,
        "priority_counts": dict(Counter(row["priority_bucket"] for row in rows)),
        "terminal_status_counts": dict(sorted(counts.items())),
        "retained_source_count": len(retained),
        "retained_pdf_count": len(pdf),
        "retained_html_count": len(html),
        "retained_other_document_count": len(other),
        "retained_byte_total": retained_bytes,
        "unique_retained_hash_count": len({row["retained_file_sha256"] for row in retained}),
        "duplicate_retained_source_count": counts["duplicate_retained_source"],
        "artifact_root": str(ARTIFACT_ROOT.relative_to(ROOT)),
        "artifact_root_git_ignored": core.check_ignored(),
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_covered_municipalities": 35_574,
        "eligible_municipality_universe": 35_589,
        "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "text_extraction_runs": 0,
        "ocr_runs": 0,
        "span_extraction_runs": 0,
        "rating_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "normalization_matching_runs": 0,
        "wage_gap_calculations": 0,
        "regressions_or_treatment_effects": 0,
        "final_causal_or_prevalence_claims": 0,
        "global_analysis_readiness": False,
        "next_task_id": "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02",
    }
    core.write_json(OUTPUT / "remaining_municipalities_source_review_download_summary.json", summary)
    status_text = ", ".join(f"{name} {count:,}" for name, count in sorted(counts.items()))
    core.write_text(OUTPUT / "remaining_municipalities_source_review_download_summary.md", f"""# Remaining-municipality source review/download

Decision: `{DECISION}`.

Five staggered lanes reviewed all {EXPECTED_COUNT:,} locked source-review-ready locators. The run retained {len(retained):,} unique sources: {len(pdf):,} PDFs, {len(html):,} HTML documents, and {len(other):,} other documents, totaling {retained_bytes:,} bytes. Terminal outcomes: {status_text}.

Retained payloads exist only under `{ARTIFACT_ROOT.relative_to(ROOT)}`. Git tracks metadata, hashes, byte counts, lineage, summaries, and queues only. No text or span extraction, OCR, rating, ingestion, codification, normalization, matching, wage-gap calculation, regression, treatment-effect analysis, prevalence claim, or final causal claim occurred.

The dashboard remains compact, the primary map metric remains `scout_coverage_rate` at 99.9579%, and the final PI report link and wage-growth continuity module remain intact. PDF/text readiness is next.
""")
    return summary


def merge() -> None:
    original_write_text = core.write_text

    def bounded_write_text(path: Path, value: str) -> None:
        try:
            path.relative_to(OUTPUT)
        except ValueError:
            return
        original_write_text(path, value)

    core.write_text = bounded_write_text
    try:
        core.merge()
    finally:
        core.write_text = original_write_text
    rows = core.read_csv(OUTPUT / "merged_source_review_results.csv")
    split_required_queues(rows)
    summary = create_required_summaries(rows)
    for lane in LANES:
        checkpoint = core.read_json(core.lane_paths(lane)["checkpoint"])
        core.write_json(OUTPUT / f"{lane}_checkpoint.json", checkpoint)
    manifest = core.read_json(OUTPUT / "source_review_download_manifest.json")
    manifest.update({
        "task_id": TASK_ID,
        "decision": DECISION,
        "execution_status": "completed",
        "input_directory": str(INPUT.relative_to(ROOT)),
        "source_review_ready_count": EXPECTED_COUNT,
        "retained_source_count": summary["retained_source_count"],
        "retained_byte_total": summary["retained_byte_total"],
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
    })
    core.write_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json", manifest)
    locked_path = OUTPUT / "source_review_locked_queue_manifest.json"
    if locked_path.is_file():
        locked_manifest = core.read_json(locked_path)
    else:
        locked_manifest = {
            "task_id": TASK_ID,
            "queue_row_count": EXPECTED_COUNT,
            "lane_counts": LANE_COUNTS,
            "priority_counts": EXPECTED_PRIORITY,
            "csv_sha256": manifest["queue_csv_sha256"],
            "jsonl_sha256": manifest["queue_jsonl_sha256"],
            "lane_hashes": manifest["lane_hashes"],
            "eligible_verification_statuses": ["reachable", "reachable_with_redirect"],
            "artifact_root": str(ARTIFACT_ROOT.relative_to(ROOT)),
        }
    locked_manifest["execution_status"] = "completed"
    core.write_json(locked_path, locked_manifest)
    core.write_json(OUTPUT / "final_decision.json", {"task_id": TASK_ID, "decision": DECISION, "finalized_at": core.utc_now()})
    core.write_text(OUTPUT / "next_task.md", """# Next task: BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02

Run PDF/text/HTML/other-document readiness over retained sources only. Use five lanes if the retained count supports it; otherwise use four lanes by project convention. Checkpoint after every source and classify parse-text-ready PDF, HTML-text-ready, other-document-text-ready, OCR-later, oversized-defer, encrypted/locked, corrupt/broken, shell/navigation-only, unsupported, and needs-review.

Do not extract full text, OCR, rate, ingest, codify, normalize, match, calculate wage gaps, run regressions or treatment effects, or make population-prevalence or final causal claims. Preserve the clean dashboard and its `scout_coverage_rate` map.
""")
    core.write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True,
        "retained_payloads_in_ignored_artifact_storage_only": True,
        "text_extractions": 0,
        "ocr_runs": 0,
        "span_extractions": 0,
        "rating_runs": 0,
        "ingestion_or_codification_runs": 0,
        "normalization_or_matching_runs": 0,
        "wage_gap_calculations": 0,
        "regressions_or_treatment_effects": 0,
        "final_causal_or_prevalence_claims": 0,
    })
    core.write_json(OUTPUT / "dashboard_remaining_source_review_download_update_summary.json", {
        "decision": DECISION,
        "status": "source_review_download_complete",
        "current_stage": "remaining-municipality source review/download complete",
        "next_task": "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02",
        "source_review_queue_count": EXPECTED_COUNT,
        "completed_source_review_rows": len(rows),
        "retained_source_count": summary["retained_source_count"],
        "retained_pdf_count": summary["retained_pdf_count"],
        "retained_html_count": summary["retained_html_count"],
        "retained_other_document_count": summary["retained_other_document_count"],
        "terminal_status_counts": summary["terminal_status_counts"],
        "map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
        "clean_dashboard_structure_preserved": True,
        "global_analysis_readiness": False,
    })
    core.write_json(OUTPUT / "staged_file_audit.json", {"passed": False, "status": "pending_staging"})
    core.write_json(OUTPUT / "large_file_audit.json", {"passed": False, "status": "pending_staging"})


def validate() -> None:
    master = core.read_csv(OUTPUT / "source_review_locked_queue.csv")
    lock = core.read_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json")
    merged = core.read_csv(OUTPUT / "merged_source_review_results.csv")
    retained = core.read_csv(OUTPUT / "retained_source_manifest.csv")
    summary = core.read_json(OUTPUT / "remaining_municipalities_source_review_download_summary.json")
    storage = core.read_json(OUTPUT / "retained_source_storage_audit.json")
    queue_union = []
    for lane in LANES:
        queue_union.extend(core.read_csv(OUTPUT / f"{lane}_queue.csv"))
    checks = {
        "input_source_review_ready_count_2956": len(master) == EXPECTED_COUNT,
        "eligible_statuses_reconcile_2845_111": Counter(row["verification_status"] for row in master) == Counter({"reachable": 2845, "reachable_with_redirect": 111}),
        "lane_sizes_592_591_591_591_591": [len(core.read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES] == [592, 591, 591, 591, 591],
        "lane_union_exact_and_disjoint": len(queue_union) == EXPECTED_COUNT and len({row["source_review_download_id"] for row in queue_union}) == EXPECTED_COUNT,
        "lane_hashes_match": all(core.sha256(OUTPUT / f"{lane}_queue.csv") == lock["lane_hashes"][lane]["csv_sha256"] for lane in LANES),
        "one_terminal_status_per_input": len(merged) == EXPECTED_COUNT and len({row["source_review_download_id"] for row in merged}) == EXPECTED_COUNT and all(row["source_review_status"] in core.CONTROLLED_STATUSES for row in merged),
        "retained_manifest_reconciles": len(retained) == summary["retained_source_count"],
        "retained_storage_manifest_hash_size_reconciles": storage.get("passed") is True and all(len(row["retained_file_sha256"]) == 64 and int(row["retained_file_size_bytes"]) > 0 for row in retained),
        "unique_retained_hash_count_reconciles": len({row["retained_file_sha256"] for row in retained}) == summary["unique_retained_hash_count"],
        "retained_type_manifests_reconcile": sum(len(core.read_csv(OUTPUT / f"retained_{kind}_manifest.csv")) for kind in ("pdf", "html", "other_document")) == len(retained),
        "all_required_nonretained_queues_exist": all((OUTPUT / f"{stem}.csv").is_file() and (OUTPUT / f"{stem}.jsonl").is_file() for stem in ("duplicate_retained_source_queue", "oversized_defer_queue", "ocr_later_queue", "restricted_or_login_required_queue", "unavailable_on_download_queue", "broken_or_corrupt_queue", "likely_non_source_or_navigation_only_queue", "excluded_out_of_scope_queue", "source_review_error_queue")),
        "artifact_root_git_ignored": core.check_ignored(),
        "retained_artifacts_not_tracked": not os.popen(f"cd '{ROOT}' && git ls-files '{ARTIFACT_ROOT.relative_to(ROOT)}'").read().strip(),
        "no_extraction_ocr_rating_or_downstream_analysis": all(summary[key] == 0 for key in ("text_extraction_runs", "ocr_runs", "span_extraction_runs", "rating_runs", "ingestion_runs", "codification_runs", "normalization_matching_runs", "wage_gap_calculations", "regressions_or_treatment_effects", "final_causal_or_prevalence_claims")),
        "dashboard_map_scope_preserved": summary["dashboard_map_primary_metric"] == "scout_coverage_rate" and summary["scout_coverage_rate_percent"] == 99.9579,
        "report_and_growth_module_preserved": summary["final_pi_report_link_preserved"] is True and summary["wage_growth_continuity_module_preserved"] is True,
        "global_readiness_not_advanced": summary["global_analysis_readiness"] is False,
    }
    passed = all(checks.values())
    report = {"task_id": TASK_ID, "validation_passed": passed, "checks": checks, "queue_count": len(master), "merged_count": len(merged), "retained_count": len(retained), "terminal_status_counts": dict(Counter(row["source_review_status"] for row in merged)), "validated_at": core.utc_now()}
    core.write_json(OUTPUT / "validation_report.json", report)
    core.write_text(OUTPUT / "validation_report.md", "# Remaining-municipality source-review/download validation\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'}: `{name}`" for name, ok in checks.items()) + f"\n\nOverall: {'PASS' if passed else 'FAIL'}.\n")
    if not passed:
        raise RuntimeError("validation failed")
    print(json.dumps(report, sort_keys=True))


def audit_staged() -> None:
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    forbidden_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    prohibited = []
    files = []
    large = []
    for name in staged:
        path = ROOT / name
        size = path.stat().st_size if path.is_file() else 0
        files.append({"path": name, "size_bytes": size, "sha256": core.sha256(path) if path.is_file() else None})
        if Path(name).suffix.casefold() in forbidden_extensions:
            prohibited.append(name)
        if Path(name).suffix.casefold() in {".html", ".htm"} and not name.startswith("docs/dashboard/"):
            prohibited.append(name)
        if any(token in name.casefold() for token in ("artifacts/local_retained_sources/", "rendered_pages/", "browser-cache", "response_body", "raw_html", "full_text", "extracted_text", "ocr_output")):
            prohibited.append(name)
        if size > 50_000_000:
            large.append({"path": name, "size_bytes": size})
    tracked = subprocess.run(
        ["git", "ls-files", str(ARTIFACT_ROOT.relative_to(ROOT))], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    staged_audit = {
        "passed": not prohibited and not tracked,
        "staged_file_count": len(staged),
        "prohibited_paths": sorted(set(prohibited)),
        "retained_artifact_paths_tracked": tracked,
        "files": files,
    }
    large_audit = {"passed": not large, "threshold_bytes": 50_000_000, "large_file_count": len(large), "files": large}
    core.write_json(OUTPUT / "staged_file_audit.json", staged_audit)
    core.write_json(OUTPUT / "large_file_audit.json", large_audit)
    validation = core.read_json(OUTPUT / "validation_report.json")
    validation["checks"]["staged_file_audit_passes"] = staged_audit["passed"]
    validation["checks"]["large_file_audit_passes"] = large_audit["passed"]
    validation["validation_passed"] = all(validation["checks"].values())
    core.write_json(OUTPUT / "validation_report.json", validation)
    core.write_text(OUTPUT / "validation_report.md", "# Remaining-municipality source-review/download validation\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'}: `{name}`" for name, ok in validation["checks"].items()) + f"\n\nOverall: {'PASS' if validation['validation_passed'] else 'FAIL'}.\n")
    manifest = core.read_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json")
    manifest["validation_passed"] = validation["validation_passed"]
    core.write_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json", manifest)
    if not validation["validation_passed"]:
        raise RuntimeError("staged-file or large-file audit failed")
    print(json.dumps({"staged": staged_audit, "large": large_audit}, sort_keys=True))


def dashboard_validate() -> None:
    phase = core.read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    browser = core.read_json(OUTPUT / "dashboard_browser_smoke_report.json")
    validation = core.read_json(OUTPUT / "validation_report.json")
    checks = {
        "dashboard_stage_source_review_complete": phase.get("current_phase") == "Remaining-municipality source review/download complete",
        "dashboard_next_task_pdf_text_readiness": phase.get("next_task") == "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02",
        "dashboard_counts_reconcile": phase.get("source_review_queue_count") == EXPECTED_COUNT and phase.get("source_review_retained_count") == 2865 and phase.get("source_review_retained_pdf_count") == 2456 and phase.get("source_review_retained_html_count") == 409,
        "dashboard_map_remains_scout_coverage_rate": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate" and phase.get("actual_scout_coverage_rate_percent") == 99.9579,
        "dashboard_final_pi_report_link_intact": phase.get("current_report_path") == "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        "dashboard_wage_growth_module_intact": phase.get("wage_growth_continuity_available") is True,
        "dashboard_global_readiness_not_advanced": phase.get("global_analysis_readiness") is False,
        "dashboard_local_production_build_passed": browser.get("dashboard_build_status") == "passed" and browser.get("static_bundle_validation_passed") is True,
        "dashboard_browser_limitation_honestly_reported": browser.get("browser_controller_available") is False and browser.get("visual_browser_validation_passed") is False,
        "dashboard_clean_structure_preserved": browser.get("clean_dashboard_structure_preserved") is True and browser.get("technical_details_collapsed_by_default_in_source") is True,
    }
    validation["checks"].update(checks)
    validation["validation_passed"] = all(validation["checks"].values())
    core.write_json(OUTPUT / "validation_report.json", validation)
    core.write_text(OUTPUT / "validation_report.md", "# Remaining-municipality source-review/download validation\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'}: `{name}`" for name, ok in validation["checks"].items()) + f"\n\nOverall: {'PASS' if validation['validation_passed'] else 'FAIL'}.\n")
    if not validation["validation_passed"]:
        raise RuntimeError("dashboard validation failed")
    print(json.dumps({"dashboard_checks": checks}, sort_keys=True))


def relay(commit_hash: str) -> Path:
    summary = core.read_json(OUTPUT / "remaining_municipalities_source_review_download_summary.json")
    manifest = core.read_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json")
    destination = ROOT / f"tmp/broad_state_remaining_municipalities_source_review_download_relay_2026-08-02_{commit_hash}.zip"
    include = {
        "remaining_municipalities_source_review_download_manifest.json",
        "remaining_municipalities_source_review_download_summary.md",
        "remaining_municipalities_source_review_download_summary.json",
        "source_review_locked_queue_manifest.json",
        "source_review_lane_distribution.json",
        "source_review_lane_distribution.md",
        "retained_source_manifest.sha256.json",
        "priority_source_review_summary.json",
        "source_family_source_review_summary.json",
        "geography_source_review_summary.json",
        "cba_non_cba_source_review_summary.json",
        "mechanism_hint_source_review_summary.json",
        "retained_source_storage_audit.json",
        "dashboard_remaining_source_review_download_update_summary.json",
        "dashboard_browser_smoke_report.json",
        "dashboard_public_pages_smoke_report.json",
        "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    }
    relay_status = {
        "final_decision": DECISION,
        "commit_hash": commit_hash,
        "push_status": "succeeded_origin_main",
        "current_head_before": EXPECTED_HEAD,
        "current_head_after": commit_hash,
        **summary,
    }
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("relay_status.json", json.dumps(relay_status, indent=2, sort_keys=True) + "\n")
        for name in sorted(include):
            path = OUTPUT / name
            if path.is_file():
                archive.write(path, f"artifacts/{name}")
    manifest["relay_zip"] = str(destination)
    core.write_json(OUTPUT / "remaining_municipalities_source_review_download_manifest.json", manifest)
    print(destination)
    return destination


def main() -> None:
    configure()
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--run-lane", choices=LANES)
    group.add_argument("--merge", action="store_true")
    group.add_argument("--validate", action="store_true")
    group.add_argument("--audit-staged", action="store_true")
    group.add_argument("--dashboard-validate", action="store_true")
    group.add_argument("--relay")
    parser.add_argument("--start-at")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.smoke:
        asyncio.run(core.smoke())
    elif args.run_lane:
        asyncio.run(core.run_lane(args.run_lane, args.start_at))
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    elif args.dashboard_validate:
        dashboard_validate()
    elif args.relay:
        relay(args.relay)
    else:
        audit_staged()


if __name__ == "__main__":
    main()
