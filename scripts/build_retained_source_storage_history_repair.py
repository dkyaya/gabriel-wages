#!/usr/bin/env python3
"""Build deterministic integrity and Git-history repair artifacts.

This script never extracts document text. It reads only manifest metadata,
filesystem size/SHA-256 values, and Git object metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
SOURCE_RUN = REPO / (
    "docs/analysis/compensation_extraction/"
    "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
)
SOURCE_RETAINED = SOURCE_RUN / "retained_sources"
READINESS_RUN = REPO / (
    "docs/analysis/compensation_extraction/"
    "COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
)
OUTPUT = REPO / (
    "docs/analysis/compensation_extraction/"
    "RETAINED-SOURCE-STORAGE-HISTORY-REPAIR-OPTION1-2026-07-28"
)
ARTIFACT_ROOT = REPO / (
    "artifacts/local_retained_sources/"
    "combined_broad_source_review_download_5589_2026-07-28"
)
ARTIFACT_RETAINED = ARTIFACT_ROOT / "retained_sources"
MANIFEST = SOURCE_RUN / (
    "combined_broad_source_review_download_5589_retained_sources_manifest.csv"
)
HASH_MANIFEST = SOURCE_RUN / (
    "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv"
)


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_and_validate_manifests() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    manifest_rows = read_csv(MANIFEST)
    hash_rows = read_csv(HASH_MANIFEST)
    if len(manifest_rows) != 4961 or len(hash_rows) != 4961:
        raise SystemExit(
            f"manifest count mismatch: manifest={len(manifest_rows)} hash={len(hash_rows)}"
        )
    manifest_by_id = {row["source_review_download_id"]: row for row in manifest_rows}
    hash_by_id = {row["source_review_download_id"]: row for row in hash_rows}
    if len(manifest_by_id) != 4961 or len(hash_by_id) != 4961:
        raise SystemExit("duplicate source_review_download_id in retained manifests")
    if set(manifest_by_id) != set(hash_by_id):
        raise SystemExit("retained manifest and hash manifest IDs do not reconcile")
    unique_hashes = {row["retained_file_sha256"] for row in hash_rows}
    if len(unique_hashes) != 4961:
        raise SystemExit(f"expected 4961 unique hashes, found {len(unique_hashes)}")
    type_counts: dict[str, int] = {}
    for row in manifest_rows:
        file_type = row["retained_file_type"].lower()
        type_counts[file_type] = type_counts.get(file_type, 0) + 1
    if type_counts.get("pdf") != 3980 or type_counts.get("html") != 941:
        raise SystemExit(f"retained PDF/HTML type mismatch: {type_counts}")
    other_count = len(manifest_rows) - type_counts["pdf"] - type_counts["html"]
    if other_count != 40:
        raise SystemExit(f"retained other-document count mismatch: {other_count}")
    return hash_rows, manifest_by_id


def validation_row(
    hash_row: dict[str, str],
    path: Path,
    *,
    path_column: str,
) -> dict[str, object]:
    expected_size = int(hash_row["retained_file_size_bytes"])
    expected_hash = hash_row["retained_file_sha256"]
    exists = path.is_file()
    actual_size = path.stat().st_size if exists else None
    actual_hash = sha256_file(path) if exists else ""
    size_matches = exists and actual_size == expected_size
    hash_matches = exists and actual_hash == expected_hash
    return {
        "source_review_download_id": hash_row["source_review_download_id"],
        path_column: rel(path),
        "expected_size_bytes": expected_size,
        "actual_size_bytes": actual_size if actual_size is not None else "",
        "expected_sha256": expected_hash,
        "actual_sha256": actual_hash,
        "path_exists": str(exists).lower(),
        "size_matches": str(size_matches).lower(),
        "hash_matches": str(hash_matches).lower(),
        "validation_status": "valid" if size_matches and hash_matches else "invalid",
    }


def validate_set(
    hash_rows: list[dict[str, str]],
    path_for_row,
    *,
    path_column: str,
) -> list[dict[str, object]]:
    results = [
        validation_row(row, path_for_row(row), path_column=path_column)
        for row in hash_rows
    ]
    failures = [row for row in results if row["validation_status"] != "valid"]
    if failures:
        raise SystemExit(f"retained file validation failed for {len(failures)} rows")
    return results


def summary_for_validation(rows: list[dict[str, object]], phase: str) -> dict[str, object]:
    return {
        "phase": phase,
        "row_count": len(rows),
        "existing_file_count": sum(row["path_exists"] == "true" for row in rows),
        "size_match_count": sum(row["size_matches"] == "true" for row in rows),
        "hash_match_count": sum(row["hash_matches"] == "true" for row in rows),
        "total_expected_bytes": sum(int(row["expected_size_bytes"]) for row in rows),
        "unique_expected_sha256_count": len({str(row["expected_sha256"]) for row in rows}),
        "all_valid": all(row["validation_status"] == "valid" for row in rows),
        "text_extraction_runs": 0,
        "ocr_runs": 0,
        "render_runs": 0,
    }


def git_blob_rows() -> list[dict[str, object]]:
    rev_output = run_git("rev-list", "--objects", "origin/main..HEAD")
    checked = subprocess.run(
        [
            "git",
            "cat-file",
            "--batch-check=%(objecttype) %(objectsize) %(objectname) %(rest)",
        ],
        cwd=REPO,
        check=True,
        text=True,
        input=rev_output,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    rows: list[dict[str, object]] = []
    retained_prefix = rel(SOURCE_RETAINED) + "/"
    for line in checked.splitlines():
        parts = line.split(" ", 3)
        if len(parts) < 3 or parts[0] != "blob":
            continue
        size = int(parts[1])
        path = parts[3] if len(parts) == 4 else ""
        suffix = Path(path).suffix.lower()
        rows.append(
            {
                "object_id": parts[2],
                "size_bytes": size,
                "path": path,
                "is_retained_source": str(path.startswith(retained_prefix)).lower(),
                "is_source_binary": str(
                    suffix in {".pdf", ".html", ".htm", ".doc", ".docx", ".xls", ".xlsx", ".rtf"}
                ).lower(),
                "over_100mb": str(size > 100 * 1024 * 1024).lower(),
            }
        )
    return sorted(rows, key=lambda row: int(row["size_bytes"]), reverse=True)


def phase_before() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    hash_rows, manifest_by_id = load_and_validate_manifests()
    before_rows = validate_set(
        hash_rows,
        lambda row: REPO / row["retained_file_path"],
        path_column="retained_file_path",
    )
    before_fields = list(before_rows[0])
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_hash_validation_before.csv",
        before_fields,
        before_rows,
    )
    write_json(
        OUTPUT / "retained_source_storage_history_repair_hash_validation_before_summary.json",
        summary_for_validation(before_rows, "before_history_repair"),
    )

    tracked = set(run_git("ls-files", rel(SOURCE_RETAINED)).splitlines())
    tracked_rows: list[dict[str, object]] = []
    for hash_row in hash_rows:
        path = hash_row["retained_file_path"]
        manifest_row = manifest_by_id[hash_row["source_review_download_id"]]
        tracked_rows.append(
            {
                "source_review_download_id": hash_row["source_review_download_id"],
                "tracked_path": path,
                "retained_file_type": manifest_row["retained_file_type"],
                "retained_file_size_bytes": int(hash_row["retained_file_size_bytes"]),
                "retained_file_sha256": hash_row["retained_file_sha256"],
                "tracked_before_repair": str(path in tracked).lower(),
            }
        )
    if len(tracked) != 4961 or not all(row["tracked_before_repair"] == "true" for row in tracked_rows):
        raise SystemExit(f"expected 4961 tracked retained paths before repair, found {len(tracked)}")
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_tracked_retained_source_paths.csv",
        list(tracked_rows[0]),
        tracked_rows,
    )

    blobs = git_blob_rows()
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_large_blob_audit.csv",
        list(blobs[0]),
        blobs,
    )


def artifact_path(hash_row: dict[str, str]) -> Path:
    original = REPO / hash_row["retained_file_path"]
    return ARTIFACT_RETAINED / original.relative_to(SOURCE_RETAINED)


def phase_after() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    hash_rows, manifest_by_id = load_and_validate_manifests()
    original_rows = validate_set(
        hash_rows,
        lambda row: REPO / row["retained_file_path"],
        path_column="original_retained_file_path",
    )
    artifact_rows = validate_set(
        hash_rows,
        artifact_path,
        path_column="local_artifact_file_path",
    )
    artifact_by_id = {row["source_review_download_id"]: row for row in artifact_rows}
    after_rows: list[dict[str, object]] = []
    local_manifest_rows: list[dict[str, object]] = []
    for original in original_rows:
        source_id = str(original["source_review_download_id"])
        artifact = artifact_by_id[source_id]
        expected_hash = str(original["expected_sha256"])
        after_rows.append(
            {
                "source_review_download_id": source_id,
                "original_retained_file_path": original["original_retained_file_path"],
                "local_artifact_file_path": artifact["local_artifact_file_path"],
                "expected_size_bytes": original["expected_size_bytes"],
                "original_actual_size_bytes": original["actual_size_bytes"],
                "artifact_actual_size_bytes": artifact["actual_size_bytes"],
                "expected_sha256": expected_hash,
                "original_actual_sha256": original["actual_sha256"],
                "artifact_actual_sha256": artifact["actual_sha256"],
                "original_hash_matches": original["hash_matches"],
                "artifact_hash_matches": artifact["hash_matches"],
                "validation_status": (
                    "valid"
                    if original["hash_matches"] == "true" and artifact["hash_matches"] == "true"
                    else "invalid"
                ),
            }
        )
        manifest_row = manifest_by_id[source_id]
        local_manifest_rows.append(
            {
                "source_review_download_id": source_id,
                "retained_file_type": manifest_row["retained_file_type"],
                "original_retained_file_path": original["original_retained_file_path"],
                "local_artifact_file_path": artifact["local_artifact_file_path"],
                "retained_file_size_bytes": original["expected_size_bytes"],
                "retained_file_sha256": expected_hash,
                "storage_scope": "local_only_git_ignored",
                "storage_pointer_status": "resolved",
            }
        )
    if not all(row["validation_status"] == "valid" for row in after_rows):
        raise SystemExit("after-preservation validation failed")
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_hash_validation_after.csv",
        list(after_rows[0]),
        after_rows,
    )
    after_summary = {
        "phase": "after_local_artifact_preservation",
        "row_count": len(after_rows),
        "original_hash_match_count": sum(row["original_hash_matches"] == "true" for row in after_rows),
        "artifact_hash_match_count": sum(row["artifact_hash_matches"] == "true" for row in after_rows),
        "total_expected_bytes": sum(int(row["expected_size_bytes"]) for row in after_rows),
        "unique_expected_sha256_count": len({str(row["expected_sha256"]) for row in after_rows}),
        "all_valid": all(row["validation_status"] == "valid" for row in after_rows),
        "artifact_root": rel(ARTIFACT_ROOT),
        "operational_manifest_paths_remain_resolvable": True,
        "text_extraction_runs": 0,
        "ocr_runs": 0,
        "render_runs": 0,
    }
    write_json(
        OUTPUT / "retained_source_storage_history_repair_hash_validation_after_summary.json",
        after_summary,
    )
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_local_artifact_manifest.csv",
        list(local_manifest_rows[0]),
        local_manifest_rows,
    )
    write_json(
        OUTPUT / "retained_source_storage_history_repair_local_artifact_manifest_summary.json",
        {
            "artifact_root": rel(ARTIFACT_ROOT),
            "row_count": len(local_manifest_rows),
            "resolved_pointer_count": sum(
                row["storage_pointer_status"] == "resolved" for row in local_manifest_rows
            ),
            "total_bytes": sum(int(row["retained_file_size_bytes"]) for row in local_manifest_rows),
            "unique_sha256_count": len(
                {str(row["retained_file_sha256"]) for row in local_manifest_rows}
            ),
            "git_ignored_local_only": True,
            "all_valid": True,
        },
    )


def phase_final() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tracked_retained = run_git("ls-files", rel(SOURCE_RETAINED)).splitlines()
    tracked_artifacts = run_git("ls-files", rel(ARTIFACT_ROOT)).splitlines()
    blobs = git_blob_rows()
    retained_blobs = [row for row in blobs if row["is_retained_source"] == "true"]
    large_blobs = [row for row in blobs if int(row["size_bytes"]) > 100 * 1024 * 1024]
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    required_rules = [
        "/artifacts/local_retained_sources/",
        "/docs/analysis/compensation_extraction/*/retained_sources/",
    ]
    ignore_rules_present = all(rule in gitignore for rule in required_rules)
    write_json(
        OUTPUT / "retained_source_storage_history_repair_gitignore_validation.json",
        {
            "required_rules": required_rules,
            "all_required_rules_present": ignore_rules_present,
            "artifact_root_ignored": bool(
                subprocess.run(
                    ["git", "check-ignore", "-q", rel(ARTIFACT_RETAINED / "probe.pdf")],
                    cwd=REPO,
                ).returncode
                == 0
            ),
            "operational_retained_root_ignored": bool(
                subprocess.run(
                    ["git", "check-ignore", "-q", rel(SOURCE_RETAINED / "probe.pdf")],
                    cwd=REPO,
                ).returncode
                == 0
            ),
        },
    )
    no_tracked_payload = (
        not tracked_retained
        and not tracked_artifacts
        and not retained_blobs
        and not large_blobs
        and ignore_rules_present
    )
    write_json(
        OUTPUT / "retained_source_storage_history_repair_no_tracked_binaries_validation.json",
        {
            "tracked_operational_retained_path_count": len(tracked_retained),
            "tracked_local_artifact_path_count": len(tracked_artifacts),
            "retained_source_blob_count_ahead_of_origin_main": len(retained_blobs),
            "blob_over_100mb_count_ahead_of_origin_main": len(large_blobs),
            "new_blob_count_ahead_of_origin_main": len(blobs),
            "new_blob_bytes_ahead_of_origin_main": sum(int(row["size_bytes"]) for row in blobs),
            "all_storage_guards_pass": no_tracked_payload,
        },
    )
    if not no_tracked_payload:
        raise SystemExit("tracked retained binary or Git-history storage guard failed")

    changed_paths = run_git("diff", "--name-only", "origin/main..HEAD").splitlines()
    inventory: list[dict[str, object]] = []
    for path_text in changed_paths:
        path = REPO / path_text
        if not path.is_file():
            continue
        category = "other_lightweight"
        if path_text.startswith("scripts/"):
            category = "script_or_test"
        elif path_text.startswith("docs/dashboard/"):
            category = "dashboard"
        elif "READINESS-4961" in path_text:
            category = "readiness_artifact"
        elif "SOURCE-REVIEW-DOWNLOAD-5589" in path_text:
            category = "source_review_artifact"
        elif path_text.startswith("docs/analysis/"):
            category = "analysis_doc_or_manifest"
        inventory.append(
            {
                "path": path_text,
                "category": category,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "tracked": "true",
            }
        )
    write_csv(
        OUTPUT / "retained_source_storage_history_repair_lightweight_artifact_inventory.csv",
        list(inventory[0]),
        inventory,
    )
    category_counts: dict[str, int] = {}
    for row in inventory:
        category = str(row["category"])
        category_counts[category] = category_counts.get(category, 0) + 1
    write_json(
        OUTPUT / "retained_source_storage_history_repair_lightweight_artifact_inventory_summary.json",
        {
            "tracked_lightweight_artifact_count": len(inventory),
            "category_counts": category_counts,
            "total_bytes": sum(int(row["size_bytes"]) for row in inventory),
            "retained_binary_count": 0,
            "all_inventory_paths_tracked": True,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after", "final"), required=True)
    args = parser.parse_args()
    if args.phase == "before":
        phase_before()
    elif args.phase == "after":
        phase_after()
    else:
        phase_final()


if __name__ == "__main__":
    main()
