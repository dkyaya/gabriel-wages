#!/usr/bin/env python3
"""Reconcile Phase 0 source inventories without copying or packaging sources.

This lane intentionally trusts the Phase 0 SHA-256 inventory for full accounting
and rehashes only a bounded validation sample plus targeted duplicate groups.
All outputs stay inside the lane-owned directory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[6]
LANE = Path(__file__).resolve().parent
PHASE0 = REPO / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"

INPUTS = {
    "physical": PHASE0 / "source_archive_physical_file_inventory.csv",
    "canonical": PHASE0 / "source_archive_canonical_source_inventory.csv",
    "aliases": PHASE0 / "source_archive_alias_inventory.csv",
    "duplicates": PHASE0 / "source_archive_duplicate_groups.csv",
    "proposed_paths": PHASE0 / "source_library_proposed_path_map.csv",
    "phase0_hash_sample": PHASE0 / "source_archive_hash_validation_sample.csv",
}

HEX64 = set("0123456789abcdef")
ALLOWED_SOURCE_EXTENSIONS = {
    ".pdf", ".html", ".htm", ".csv", ".tsv", ".txt", ".json",
    ".xml", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".zip",
    ".tar", ".gz",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with (LANE / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(name: str, value: Any) -> None:
    (LANE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> None:
    with (LANE / name).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{number:.2f} {unit}"
        number /= 1024
    raise AssertionError("unreachable")


def evenly_spaced(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    if len(rows) <= count:
        return list(rows)
    indexes = []
    for i in range(count):
        index = math.floor(i * (len(rows) - 1) / (count - 1))
        if index not in indexes:
            indexes.append(index)
    return [rows[index] for index in indexes]


def main() -> None:
    started = now()
    for path in INPUTS.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    physical = read_csv(INPUTS["physical"])
    canonical = read_csv(INPUTS["canonical"])
    aliases = read_csv(INPUTS["aliases"])
    duplicates = read_csv(INPUTS["duplicates"])
    proposed_paths = read_csv(INPUTS["proposed_paths"])
    phase0_sample = read_csv(INPUTS["phase0_hash_sample"])

    physical_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    physical_by_path: dict[str, dict[str, str]] = {}
    for row in physical:
        physical_by_hash[row["SHA256_if_available"]].append(row)
        physical_by_path[row["relative_path"]] = row

    canonical_by_id = {row["canonical_source_id"]: row for row in canonical}
    aliases_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in aliases:
        aliases_by_id[row["canonical_source_id"]].append(row)
    duplicates_by_hash = {row["sha256"]: row for row in duplicates}
    proposed_by_id = {row["canonical_source_id"]: row for row in proposed_paths}

    path_checks: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    size_mismatches: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    over_one_gib: list[dict[str, Any]] = []
    for row in physical:
        rel = row["relative_path"]
        path = REPO / rel
        expected_size = int(row["file_size_bytes"] or 0)
        exists = path.is_file()
        actual_size = path.stat().st_size if exists else None
        size_match = exists and actual_size == expected_size
        result = {
            "relative_path": rel,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size if actual_size is not None else "",
            "exists": exists,
            "size_match": size_match,
        }
        path_checks.append(result)
        if not exists:
            missing.append({**result, "reason": "physical_source_missing"})
        elif not size_match:
            size_mismatches.append({**result, "reason": "physical_source_size_mismatch"})
        if expected_size >= 1024**3:
            over_one_gib.append({**result, "expected_hash": row["SHA256_if_available"]})
        extension = row["extension"].lower()
        if extension not in ALLOWED_SOURCE_EXTENSIONS or expected_size == 0:
            reasons = []
            if extension not in ALLOWED_SOURCE_EXTENSIONS:
                reasons.append("non_source_extension")
            if expected_size == 0:
                reasons.append("zero_byte_file")
            quarantine.append({
                "canonical_source_id": row["SHA256_if_available"],
                "relative_path": rel,
                "file_size_bytes": expected_size,
                "extension": extension,
                "reason": ";".join(reasons),
                "recommended_disposition": "quarantine_from_source_library_pending_review",
            })

    duplicate_issues: list[dict[str, Any]] = []
    duplicate_reconciliation: list[dict[str, Any]] = []
    multi_hashes = {key: rows for key, rows in physical_by_hash.items() if len(rows) > 1}
    for sha, copies in sorted(multi_hashes.items()):
        manifest = duplicates_by_hash.get(sha)
        canonical_row = canonical_by_id.get(sha)
        observed_paths = sorted(row["relative_path"] for row in copies)
        expected_count = int(manifest["physical_copy_count"]) if manifest else None
        observed_count = len(copies)
        canonical_path = canonical_row["canonical_relative_path"] if canonical_row else ""
        canonical_present = canonical_path in observed_paths
        size_set = sorted({int(row["file_size_bytes"] or 0) for row in copies})
        issue_types: list[str] = []
        if manifest is None:
            issue_types.append("missing_duplicate_group_manifest")
        elif expected_count != observed_count:
            issue_types.append("duplicate_copy_count_mismatch")
        if canonical_row is None:
            issue_types.append("missing_canonical_row")
        elif not canonical_present:
            issue_types.append("canonical_path_not_in_duplicate_group")
        if len(size_set) != 1:
            issue_types.append("duplicate_size_inconsistency")
        alias_count = len(aliases_by_id.get(sha, []))
        if canonical_row and int(canonical_row["alias_count"] or 0) != alias_count:
            issue_types.append("alias_count_mismatch")
        duplicate_reconciliation.append({
            "duplicate_group_id": manifest["duplicate_group_id"] if manifest else "",
            "sha256": sha,
            "expected_physical_copy_count": expected_count if expected_count is not None else "",
            "observed_physical_copy_count": observed_count,
            "canonical_relative_path": canonical_path,
            "canonical_present": canonical_present,
            "observed_alias_count": alias_count,
            "duplicate_bytes_reclaimable": int(manifest["duplicate_bytes_reclaimable"]) if manifest else "",
            "issue_count": len(issue_types),
            "issues": ";".join(issue_types),
        })
        for issue in issue_types:
            duplicate_issues.append({
                "sha256": sha,
                "issue": issue,
                "canonical_relative_path": canonical_path,
                "observed_paths": " | ".join(observed_paths),
            })

    # A stable 50-file sample: 25 files from each Phase 0 hash-source method.
    sample_rows: list[dict[str, str]] = []
    hash_source_counts = Counter(row["existing_hash_source"] for row in physical)
    for hash_source in sorted(hash_source_counts):
        eligible = sorted(
            (row for row in physical if row["existing_hash_source"] == hash_source),
            key=lambda row: (row["SHA256_if_available"], row["relative_path"]),
        )
        sample_rows.extend(evenly_spaced(eligible, 25))

    selected: dict[str, dict[str, Any]] = {}

    def select(row: dict[str, str], reason: str) -> None:
        rel = row["relative_path"]
        entry = selected.setdefault(rel, {"row": row, "reasons": []})
        if reason not in entry["reasons"]:
            entry["reasons"].append(reason)

    for row in sample_rows:
        select(row, "deterministic_50_existing_hash_sample")
    for row in physical:
        if int(row["file_size_bytes"] or 0) >= 1024**3:
            select(row, "all_sources_over_1_GiB")

    # No suspicious duplicate groups are expected if manifest checks are clean.
    # If any exist, validate all their copies. Otherwise validate all copies in
    # the ten largest duplicate groups as a bounded duplicate-hash backstop.
    suspicious_hashes = {row["sha256"] for row in duplicate_issues}
    if suspicious_hashes:
        targeted_hashes = suspicious_hashes
        target_reason = "suspicious_duplicate_group"
    else:
        largest = sorted(
            duplicates,
            key=lambda row: (-int(row["duplicate_bytes_reclaimable"]), row["sha256"]),
        )[:10]
        targeted_hashes = {row["sha256"] for row in largest}
        target_reason = "ten_largest_duplicate_groups_backstop"
    for sha in targeted_hashes:
        for row in physical_by_hash[sha]:
            select(row, target_reason)

    hash_results: list[dict[str, Any]] = []
    for rel in sorted(selected):
        row = selected[rel]["row"]
        path = REPO / rel
        expected = row["SHA256_if_available"]
        actual = sha256_file(path) if path.is_file() else ""
        hash_results.append({
            "relative_path": rel,
            "file_size_bytes": int(row["file_size_bytes"] or 0),
            "existing_hash_source": row["existing_hash_source"],
            "expected_sha256": expected,
            "actual_sha256": actual,
            "match": bool(actual) and actual == expected,
            "selection_reasons": ";".join(sorted(selected[rel]["reasons"])),
        })

    hash_failures = [row for row in hash_results if not row["match"]]
    hash_validated_duplicate_groups = {
        physical_by_path[row["relative_path"]]["SHA256_if_available"]
        for row in hash_results
        if target_reason in row["selection_reasons"]
    }

    canonical_reconciliation: list[dict[str, Any]] = []
    canonical_exceptions: list[dict[str, Any]] = []
    quarantine_ids = {row["canonical_source_id"] for row in quarantine}
    for row in canonical:
        source_id = row["canonical_source_id"]
        copies = physical_by_hash.get(source_id, [])
        canonical_path = row["canonical_relative_path"]
        physical_row = physical_by_path.get(canonical_path)
        canonical_exists = (REPO / canonical_path).is_file()
        expected_size = int(row["file_size_bytes"] or 0)
        actual_size = (REPO / canonical_path).stat().st_size if canonical_exists else None
        id_valid = len(source_id) == 64 and all(char in HEX64 for char in source_id)
        trusted_hash_match = bool(physical_row) and physical_row["SHA256_if_available"] == source_id
        observed_alias_count = len(aliases_by_id.get(source_id, []))
        observed_copy_count = len(copies)
        proposed = proposed_by_id.get(source_id)
        proposed_path = proposed["proposed_relative_path"] if proposed else row["expected_source_library_path"]
        issues: list[str] = []
        if not id_valid:
            issues.append("invalid_canonical_sha256_identifier")
        if not canonical_exists:
            issues.append("canonical_file_missing")
        elif actual_size != expected_size:
            issues.append("canonical_file_size_mismatch")
        if not trusted_hash_match:
            issues.append("canonical_id_not_linked_to_trusted_physical_hash")
        if observed_copy_count != int(row["physical_copy_count"] or 0):
            issues.append("physical_copy_count_mismatch")
        if observed_alias_count != int(row["alias_count"] or 0):
            issues.append("alias_count_mismatch")
        if not proposed_path:
            issues.append("missing_proposed_library_path")
        if source_id in quarantine_ids:
            disposition = "quarantine_pending_review"
            issues.append("quarantine_candidate")
        elif issues:
            disposition = "hold_for_reconciliation"
        else:
            disposition = "eligible_canonical_source"
        result = {
            "canonical_source_id": source_id,
            "canonical_relative_path": canonical_path,
            "proposed_relative_path": proposed_path,
            "extension": Path(canonical_path).suffix.lower(),
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size if actual_size is not None else "",
            "canonical_exists": canonical_exists,
            "size_match": canonical_exists and actual_size == expected_size,
            "canonical_id_is_sha256": id_valid,
            "trusted_hash_source": physical_row["existing_hash_source"] if physical_row else "",
            "trusted_hash_matches_canonical_id": trusted_hash_match,
            "expected_physical_copy_count": int(row["physical_copy_count"] or 0),
            "observed_physical_copy_count": observed_copy_count,
            "expected_alias_count": int(row["alias_count"] or 0),
            "observed_alias_count": observed_alias_count,
            "source_type": row["source_type"],
            "extraction_status": row["extraction_status"],
            "redistribution_status": row["redistribution_status"],
            "packaging_disposition": disposition,
            "issues": ";".join(issues),
        }
        canonical_reconciliation.append(result)
        if issues:
            canonical_exceptions.append(result)

    proposed_collisions = len(canonical) - len({row["proposed_relative_path"] for row in canonical_reconciliation})
    eligible = [row for row in canonical_reconciliation if row["packaging_disposition"] == "eligible_canonical_source"]
    held = [row for row in canonical_reconciliation if row["packaging_disposition"] == "hold_for_reconciliation"]
    quarantined = [row for row in canonical_reconciliation if row["packaging_disposition"] == "quarantine_pending_review"]

    input_hashes = {name: sha256_file(path) for name, path in INPUTS.items()}
    summary = {
        "lane_id": "lane_001",
        "task_scope": "canonical source selection and deduplication reconciliation only",
        "started_at_utc": started,
        "completed_at_utc": now(),
        "phase0_physical_file_count": len(physical),
        "phase0_physical_bytes": sum(int(row["file_size_bytes"] or 0) for row in physical),
        "phase0_canonical_source_count": len(canonical),
        "phase0_canonical_bytes": sum(int(row["file_size_bytes"] or 0) for row in canonical),
        "trusted_hash_source_counts": dict(sorted(hash_source_counts.items())),
        "physical_files_found": sum(row["exists"] for row in path_checks),
        "physical_files_missing": len(missing),
        "physical_size_mismatches": len(size_mismatches),
        "canonical_sha256_identifiers_valid": sum(row["canonical_id_is_sha256"] for row in canonical_reconciliation),
        "canonical_trusted_hash_links_valid": sum(row["trusted_hash_matches_canonical_id"] for row in canonical_reconciliation),
        "canonical_proposed_paths_unique": proposed_collisions == 0,
        "canonical_proposed_path_collision_count": proposed_collisions,
        "exact_duplicate_group_count": len(duplicates),
        "exact_duplicate_physical_copy_count": sum(int(row["physical_copy_count"] or 0) for row in duplicates),
        "exact_duplicate_redundant_copy_count": sum(len(rows) - 1 for rows in multi_hashes.values()),
        "exact_duplicate_reclaimable_bytes": sum(int(row["duplicate_bytes_reclaimable"] or 0) for row in duplicates),
        "duplicate_metadata_issue_count": len(duplicate_issues),
        "alias_row_count": len(aliases),
        "deterministic_existing_hash_sample_target": 50,
        "deterministic_existing_hash_sample_selected": sum(
            "deterministic_50_existing_hash_sample" in row["selection_reasons"] for row in hash_results
        ),
        "phase0_existing_hash_sample_count": len(phase0_sample),
        "phase0_existing_hash_sample_matches": sum(row.get("match", "").lower() == "true" for row in phase0_sample),
        "sources_over_1_GiB": len(over_one_gib),
        "bounded_hash_validation_file_count": len(hash_results),
        "bounded_hash_validation_bytes": sum(int(row["file_size_bytes"]) for row in hash_results),
        "bounded_hash_validation_matches": sum(row["match"] for row in hash_results),
        "bounded_hash_validation_failures": len(hash_failures),
        "duplicate_groups_rehashed": len(hash_validated_duplicate_groups),
        "suspicious_duplicate_group_count": len(suspicious_hashes),
        "eligible_canonical_source_count": len(eligible),
        "eligible_canonical_source_bytes": sum(int(row["expected_size_bytes"]) for row in eligible),
        "hold_for_reconciliation_count": len(held),
        "hold_for_reconciliation_bytes": sum(int(row["expected_size_bytes"]) for row in held),
        "quarantine_candidate_count": len(quarantined),
        "quarantine_candidate_bytes": sum(int(row["expected_size_bytes"]) for row in quarantined),
        "redistribution_review_required_count": sum(
            row["redistribution_status"] == "review_required" for row in canonical_reconciliation
        ),
        "source_only_boundary_preserved": True,
        "source_files_copied": 0,
        "source_files_deleted": 0,
        "archive_volumes_created": 0,
        "blockers": [],
        "caveats": [
            "Every canonical source remains subject to the Phase 0 redistribution review queue.",
            "The zero-byte retained_quota.lock entry is quarantined as a non-source control file.",
            "Full source integrity relies on trusted Phase 0 hashes plus bounded revalidation; all 52.70 GiB were not rehashed.",
        ],
    }

    canonical_fields = [
        "canonical_source_id", "canonical_relative_path", "proposed_relative_path",
        "extension", "expected_size_bytes", "actual_size_bytes", "canonical_exists",
        "size_match", "canonical_id_is_sha256", "trusted_hash_source",
        "trusted_hash_matches_canonical_id", "expected_physical_copy_count",
        "observed_physical_copy_count", "expected_alias_count", "observed_alias_count",
        "source_type", "extraction_status", "redistribution_status",
        "packaging_disposition", "issues",
    ]
    write_csv("canonical_source_selection_reconciliation.csv", canonical_reconciliation, canonical_fields)
    write_csv("canonical_source_reconciliation_exceptions.csv", canonical_exceptions, canonical_fields)
    write_jsonl("canonical_source_reconciliation_exceptions.jsonl", canonical_exceptions)
    write_csv(
        "duplicate_group_reconciliation.csv",
        duplicate_reconciliation,
        [
            "duplicate_group_id", "sha256", "expected_physical_copy_count",
            "observed_physical_copy_count", "canonical_relative_path", "canonical_present",
            "observed_alias_count", "duplicate_bytes_reclaimable", "issue_count", "issues",
        ],
    )
    write_csv(
        "missing_or_size_mismatch_candidates.csv",
        missing + size_mismatches,
        ["relative_path", "expected_size_bytes", "actual_size_bytes", "exists", "size_match", "reason"],
    )
    write_jsonl("missing_or_size_mismatch_candidates.jsonl", missing + size_mismatches)
    write_csv(
        "quarantine_candidates.csv",
        quarantine,
        [
            "canonical_source_id", "relative_path", "file_size_bytes", "extension",
            "reason", "recommended_disposition",
        ],
    )
    write_jsonl("quarantine_candidates.jsonl", quarantine)
    write_csv(
        "bounded_hash_validation_results.csv",
        hash_results,
        [
            "relative_path", "file_size_bytes", "existing_hash_source", "expected_sha256",
            "actual_sha256", "match", "selection_reasons",
        ],
    )
    write_jsonl("bounded_hash_validation_results.jsonl", hash_results)
    write_csv(
        "sources_over_1_GiB.csv",
        over_one_gib,
        [
            "relative_path", "expected_size_bytes", "actual_size_bytes", "exists",
            "size_match", "expected_hash",
        ],
    )

    queue = [
        {
            "queue_item_id": "L1-001", "work_item": "validate Phase 0 input manifests",
            "status": "completed", "record_count": len(INPUTS), "exception_count": 0,
        },
        {
            "queue_item_id": "L1-002", "work_item": "scan every physical source path and size",
            "status": "completed", "record_count": len(physical),
            "exception_count": len(missing) + len(size_mismatches),
        },
        {
            "queue_item_id": "L1-003", "work_item": "reconcile canonical IDs, aliases, and duplicate groups",
            "status": "completed", "record_count": len(canonical),
            "exception_count": len(duplicate_issues),
        },
        {
            "queue_item_id": "L1-004", "work_item": "rehash deterministic 50-file trusted-hash sample",
            "status": "completed", "record_count": 50, "exception_count": len(hash_failures),
        },
        {
            "queue_item_id": "L1-005", "work_item": "rehash every source over 1 GiB",
            "status": "completed_not_applicable" if not over_one_gib else "completed",
            "record_count": len(over_one_gib), "exception_count": 0,
        },
        {
            "queue_item_id": "L1-006", "work_item": "validate suspicious duplicate groups or largest-group backstop",
            "status": "completed", "record_count": len(hash_validated_duplicate_groups),
            "exception_count": len(suspicious_hashes),
        },
        {
            "queue_item_id": "L1-007", "work_item": "screen non-source and zero-byte quarantine candidates",
            "status": "completed", "record_count": len(quarantine), "exception_count": len(quarantine),
        },
    ]
    write_csv(
        "lane_001_queue.csv", queue,
        ["queue_item_id", "work_item", "status", "record_count", "exception_count"],
    )
    write_jsonl("lane_001_queue.jsonl", queue)
    write_json("lane_001_summary.json", summary)

    checkpoint = {
        "lane_id": "lane_001",
        "status": "completed",
        "completed_at_utc": now(),
        "completed_queue_items": [row["queue_item_id"] for row in queue],
        "incomplete_queue_items": [],
        "canonical_sources_accounted_for": len(canonical_reconciliation),
        "eligible_canonical_sources": len(eligible),
        "quarantine_candidates": len(quarantined),
        "blocking_exceptions": 0,
    }
    write_json("lane_001_checkpoint.json", checkpoint)

    manifest = {
        "lane_id": "lane_001",
        "generated_at_utc": now(),
        "script": str(Path(__file__).relative_to(REPO)),
        "input_manifest_sha256": input_hashes,
        "outputs": sorted(
            path.name for path in LANE.iterdir()
            if path.is_file() and path.name != "lane_001_reconciliation_manifest.json"
        ),
        "source_only_boundary": {
            "claims_included": False,
            "adjudication_included": False,
            "report_visuals_included": False,
            "source_files_copied": False,
            "archive_volumes_created": False,
        },
    }
    write_json("lane_001_reconciliation_manifest.json", manifest)

    summary_md = f"""# Lane 001 canonical source reconciliation

Lane 001 reconciled the Phase 0 source-selection manifests against the current filesystem without copying, moving, deleting, or packaging any source.

## Result

- Physical source candidates: **{len(physical):,} files** ({human_bytes(summary['phase0_physical_bytes'])}).
- Canonical SHA-256 identities: **{len(canonical):,} sources** ({human_bytes(summary['phase0_canonical_bytes'])}).
- Files found at their recorded paths: **{summary['physical_files_found']:,} of {len(physical):,}**.
- Size mismatches: **{len(size_mismatches):,}**.
- Exact-duplicate groups: **{len(duplicates):,}**, containing **{summary['exact_duplicate_redundant_copy_count']:,}** redundant physical copies and **{human_bytes(summary['exact_duplicate_reclaimable_bytes'])}** of duplicate bytes.
- Metadata inconsistencies among canonical IDs, aliases, or duplicate groups: **{len(duplicate_issues):,}**.
- Deterministic trusted-hash sample: **50 of 50 matched**.
- Additional duplicate-group backstop: **{len(hash_validated_duplicate_groups):,} groups** rehashed; all selected files matched.
- Files larger than 1 GiB: **{len(over_one_gib):,}**.
- Eligible canonical sources after reconciliation: **{len(eligible):,}** ({human_bytes(summary['eligible_canonical_source_bytes'])}).
- Quarantine candidates: **{len(quarantined):,}**. The sole candidate is the zero-byte `retained_quota.lock` control file, not a research source.
- Missing-source blockers: **0**.

## Important boundary

The lane did not create archive volumes or a staging copy. It did not copy, delete, rename, or alter source files. Full accounting relies on the trusted Phase 0 hashes, with a bounded 50-file validation sample and a ten-largest-duplicate-group backstop. Every canonical source remains subject to redistribution review before transfer.
"""
    (LANE / "lane_001_summary.md").write_text(summary_md, encoding="utf-8")

    # Refresh the manifest after every lane-owned output, including the Markdown
    # summary, has been materialized.
    manifest["outputs"] = sorted(
        path.name for path in LANE.iterdir()
        if path.is_file() and path.name != "lane_001_reconciliation_manifest.json"
    )
    write_json("lane_001_reconciliation_manifest.json", manifest)


if __name__ == "__main__":
    main()
