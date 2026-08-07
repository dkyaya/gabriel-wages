#!/usr/bin/env python3
"""Sequentially write frozen source-library volumes until the disk floor stops work."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import time


RELEASE = "gabriel-wages-source-library-2026-08-06"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    manifests = package / "manifests"
    parts = package / "parts"
    logs = package / "logs"
    parts.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("packager", task / "tools/package_source_library.py")
    assert spec and spec.loader
    packager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packager)
    assignment = manifests / "source_library_volume_assignments.csv"
    if not assignment.exists():
        assignment = task / "source_library_volume_assignments.csv.gz"
    manifest_path = manifests / "VOLUME_MANIFEST.csv"
    with manifest_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    transferred_path = manifests / "source_library_transferred_volumes.csv"
    transferred_ids = set()
    if transferred_path.exists():
        with transferred_path.open(newline="", encoding="utf-8-sig") as stream:
            transferred_ids = {r["volume_id"] for r in csv.DictReader(stream) if r.get("confirmed_by_user", "").lower() == "true"}
    started = time.time()
    for row in rows:
        if row["status"] in {"accepted", "accepted_local_ready_for_transfer", "transferred", "transferred_by_user"}:
            expected_archive = parts / row["filename"]
            if not expected_archive.is_file() and row["volume_id"] not in transferred_ids:
                raise FileNotFoundError(f"accepted archive is absent and not confirmed transferred: {row['volume_id']}")
            continue
        result = packager.write_volume(
            assignments=assignment,
            volume_id=row["volume_id"],
            repo_root=repo,
            parts_dir=parts,
            compression_level=6,
            threads=2,
            free_floor=8 * 1024**3,
        )
        write_json(logs / f"{row['volume_id']}.json", result)
        if result["status"] == "held_for_space":
            row["status"] = "held_for_space"
            row["verification_status"] = "not_started_space_floor"
            break
        for key, manifest_key in (
            ("status", "status"),
            ("compressed_bytes", "compressed_bytes"),
            ("compression_ratio", "compression_ratio"),
            ("archive_sha256", "archive_SHA256"),
            ("member_count", "member_count"),
            ("validation_method", "validation_method"),
            ("verified_source_member_count", "verified_source_member_count"),
            ("verification_status", "verification_status"),
            ("runtime_seconds", "runtime_seconds"),
        ):
            row[manifest_key] = result[key]
        write_csv(manifest_path, rows)
        write_json(manifests / "VOLUME_MANIFEST.json", rows)
    held_started = False
    for row in rows:
        if row["status"] == "held_for_space":
            held_started = True
        elif held_started and row["status"] == "planned":
            row["status"] = "held_for_space"
            row["verification_status"] = "not_started_space_floor"
    write_csv(manifest_path, rows)
    write_json(manifests / "VOLUME_MANIFEST.json", rows)
    accepted = [r for r in rows if r["status"] in {"accepted", "accepted_local_ready_for_transfer"}]
    completed = [r for r in rows if r["status"] in {"accepted", "accepted_local_ready_for_transfer", "transferred", "transferred_by_user"}]
    remaining = [r for r in rows if r["status"] not in {"accepted", "accepted_local_ready_for_transfer", "transferred", "transferred_by_user"}]
    completed_fields = ["volume_id", "filename", "status", "compressed_bytes", "archive_SHA256", "verification_status", "runtime_seconds"]
    with (manifests / "source_library_completed_volumes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=completed_fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(accepted)
    with (manifests / "source_library_completed_volumes.jsonl").open("w", encoding="utf-8") as stream:
        for row in accepted: stream.write(json.dumps(row, sort_keys=True) + "\n")
    write_csv(manifests / "source_library_remaining_volumes.csv", remaining) if remaining else None
    with (manifests / "source_library_remaining_volumes.jsonl").open("w", encoding="utf-8") as stream:
        for row in remaining: stream.write(json.dumps(row, sort_keys=True) + "\n")
    transferred_fields = ["volume_id", "filename", "transferred_at", "destination_note", "confirmed_by_user"]
    transferred = manifests / "source_library_transferred_volumes.csv"
    if not transferred.exists():
        with transferred.open("w", newline="", encoding="utf-8") as stream:
            csv.DictWriter(stream, fieldnames=transferred_fields).writeheader()
        (manifests / "source_library_transferred_volumes.jsonl").write_text("", encoding="utf-8")
    checkpoint = {
        "status": "partial_transfer_space_required" if remaining else "complete",
        "accepted_volume_count": len(accepted),
        "completed_volume_count": len(completed),
        "transferred_volume_count": sum(r["status"] in {"transferred", "transferred_by_user"} for r in rows),
        "remaining_volume_count": len(remaining),
        "accepted_volume_ids": [r["volume_id"] for r in accepted],
        "next_incomplete_volume_id": remaining[0]["volume_id"] if remaining else None,
        "completed_compressed_bytes": sum(int(r["compressed_bytes"] or 0) for r in accepted),
        "remaining_planned_bytes": sum(int(r["planned_total_bytes"]) for r in remaining),
        "runtime_seconds": round(time.time() - started, 3),
    }
    write_json(manifests / "source_library_packaging_checkpoint.json", checkpoint)
    print(json.dumps(checkpoint, indent=2))


if __name__ == "__main__":
    main()
