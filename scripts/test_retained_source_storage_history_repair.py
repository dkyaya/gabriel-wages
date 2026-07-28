#!/usr/bin/env python3
"""Regression checks for retained-source storage/history repair."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE_RUN = (
    "docs/analysis/compensation_extraction/"
    "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
)
READINESS_RUN = (
    "docs/analysis/compensation_extraction/"
    "COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
)
REPAIR_RUN = (
    "docs/analysis/compensation_extraction/"
    "RETAINED-SOURCE-STORAGE-HISTORY-REPAIR-OPTION1-2026-07-28"
)
SOURCE_RETAINED = f"{SOURCE_RUN}/retained_sources"
ARTIFACT_ROOT = (
    "artifacts/local_retained_sources/"
    "combined_broad_source_review_download_5589_2026-07-28"
)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def load_json(path: str) -> dict:
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def read_csv(path: str) -> list[dict[str, str]]:
    with (REPO / path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def assert_no_retained_payload_in_ahead_history() -> None:
    assert not git("ls-files", SOURCE_RETAINED).splitlines()
    assert not git("ls-files", ARTIFACT_ROOT).splitlines()
    rev_output = git("rev-list", "--objects", "origin/main..HEAD")
    assert f"{SOURCE_RETAINED}/" not in rev_output
    checked = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectsize) %(rest)"],
        cwd=REPO,
        check=True,
        text=True,
        input=rev_output,
        stdout=subprocess.PIPE,
    ).stdout
    blob_sizes = [
        int(parts[1])
        for line in checked.splitlines()
        if len(parts := line.split(" ", 2)) >= 2 and parts[0] == "blob"
    ]
    assert all(size <= 100 * 1024 * 1024 for size in blob_sizes)


def assert_artifact_preservation() -> None:
    summary = load_json(
        f"{REPAIR_RUN}/retained_source_storage_history_repair_hash_validation_after_summary.json"
    )
    assert summary["row_count"] == 4961
    assert summary["original_hash_match_count"] == 4961
    assert summary["artifact_hash_match_count"] == 4961
    assert summary["total_expected_bytes"] == 12475949771
    assert summary["unique_expected_sha256_count"] == 4961
    assert summary["all_valid"] is True
    rows = read_csv(
        f"{REPAIR_RUN}/retained_source_storage_history_repair_local_artifact_manifest.csv"
    )
    assert len(rows) == 4961
    assert len({row["retained_file_sha256"] for row in rows}) == 4961
    for row in rows:
        original = REPO / row["original_retained_file_path"]
        artifact = REPO / row["local_artifact_file_path"]
        expected_size = int(row["retained_file_size_bytes"])
        assert original.is_file() and original.stat().st_size == expected_size
        assert artifact.is_file() and artifact.stat().st_size == expected_size


def assert_lightweight_artifacts_and_dashboard() -> None:
    required = [
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_decision.json",
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_summary.md",
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_retained_sources_manifest.csv",
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv",
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_results_summary.json",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_decision.json",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_summary.md",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_results_summary.json",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_parse_text_layer_later.csv",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_html_text_later.csv",
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_other_document_text_later.csv",
        "docs/dashboard/data/project_phase_summary.json",
        "docs/dashboard/data/pdf_readiness_status_summary.json",
    ]
    for path in required:
        assert (REPO / path).is_file(), path
        git("ls-files", "--error-unmatch", path)

    source_summary = load_json(
        f"{SOURCE_RUN}/combined_broad_source_review_download_5589_retained_sources_summary.json"
    )
    readiness_summary = load_json(
        f"{READINESS_RUN}/combined_broad_pdf_text_layer_readiness_4961_results_summary.json"
    )
    dashboard = load_json("docs/dashboard/data/project_phase_summary.json")
    assert source_summary["retained_source_count"] == 4961
    assert source_summary["retained_pdf_count"] == 3980
    assert source_summary["retained_html_count"] == 941
    assert readiness_summary["readiness_reviewed_count"] == 4961
    assert readiness_summary["extraction_ready_count"] == 4051
    assert readiness_summary["global_analysis_readiness"] is False
    assert dashboard["dashboard_map_filter"] == "total_scout_coverage_only"
    assert dashboard["global_analysis_readiness"] is False
    assert dashboard["source_review_download_retained_count"] == 4961
    assert dashboard["pdf_text_readiness_extraction_ready_count"] == 4051


def assert_storage_policy() -> None:
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "/artifacts/local_retained_sources/" in gitignore
    assert "/docs/analysis/compensation_extraction/*/retained_sources/" in gitignore
    for path in [
        f"{REPAIR_RUN}/future_artifact_storage_standard_for_retained_sources.md",
        f"{REPAIR_RUN}/future_source_review_download_artifact_storage_policy.md",
        f"{REPAIR_RUN}/future_large_artifact_push_preflight_policy.md",
    ]:
        assert (REPO / path).is_file()


def main() -> None:
    assert_no_retained_payload_in_ahead_history()
    assert_artifact_preservation()
    assert_lightweight_artifacts_and_dashboard()
    assert_storage_policy()
    print("retained source storage/history repair tests: PASS")


if __name__ == "__main__":
    main()
