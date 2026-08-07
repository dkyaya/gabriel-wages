#!/usr/bin/env python3
"""Validate and record the user-confirmed resume state for VOL-023--VOL-028."""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile


RELEASE = "gabriel-wages-source-library-2026-08-06"
EXPECTED_HASH = "5ee307c414b5370e16b5533c0285a861c99ea0562fa3796fff3ea9ddae1a8fcd"
TRANSFER_FIELDS = [
    "volume_id", "filename", "prior_archive_SHA256", "prior_compressed_bytes",
    "prior_source_count", "prior_text_companion_count", "prior_validation_status",
    "transfer_status", "transfer_destination_label", "transfer_destination_type",
    "confirmation_basis", "confirmation_date", "local_archive_present",
    "rebuild_required", "previously_locally_verified_before_transfer",
    "remote_post_transfer_verification", "confirmed_by_user",
]


def read_csv(path: Path, gz: bool = False) -> list[dict[str, str]]:
    opener = gzip.open if gz else open
    with opener(path, "rt" if gz else "r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")


def safe_path(value: str) -> bool:
    p = PurePosixPath(value)
    return bool(value) and not p.is_absolute() and ".." not in p.parts and "\x00" not in value


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    resume = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-PACKAGING-RESUME-VOL023-028-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    manifests = package / "manifests"
    parts = package / "parts"
    assignment_path = task / "source_library_volume_assignments.csv.gz"

    h = hashlib.sha256()
    with gzip.open(assignment_path, "rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    if h.hexdigest() != EXPECTED_HASH:
        raise RuntimeError(f"assignment hash mismatch: {h.hexdigest()} != {EXPECTED_HASH}")

    assignments = read_csv(assignment_path, gz=True)
    if len(assignments) != 26635:
        raise RuntimeError(f"unexpected assignment rows: {len(assignments)}")
    volume_rows = read_csv(manifests / "VOLUME_MANIFEST.csv")
    by_volume = {row["volume_id"]: row for row in volume_rows}
    if sorted(by_volume) != [f"VOL-{i:03d}" for i in range(1, 29)]:
        raise RuntimeError("volume manifest does not contain exactly VOL-001 through VOL-028")

    transfer_rows = []
    for number in range(1, 23):
        volume_id = f"VOL-{number:03d}"
        row = by_volume[volume_id]
        if row["status"] not in {"accepted", "transferred_by_user"}:
            raise RuntimeError(f"{volume_id} was not previously accepted")
        if not row["archive_SHA256"] or not row["compressed_bytes"] or row["verification_status"] not in {"pass", "accepted_before_transfer"}:
            raise RuntimeError(f"{volume_id} lacks accepted validation metadata")
        local_path = parts / row["filename"]
        if local_path.exists():
            raise RuntimeError(f"expected transferred archive still present locally: {local_path}")
        transfer_rows.append({
            "volume_id": volume_id,
            "filename": row["filename"],
            "prior_archive_SHA256": row["archive_SHA256"],
            "prior_compressed_bytes": row["compressed_bytes"],
            "prior_source_count": row["source_count"],
            "prior_text_companion_count": row["text_companion_count"],
            "prior_validation_status": "accepted_before_transfer",
            "transfer_status": "transferred_by_user",
            "transfer_destination_label": "Safety_NonSafety_Source_Library",
            "transfer_destination_type": "user_managed_google_drive",
            "confirmation_basis": "explicit_user_confirmation",
            "confirmation_date": "2026-08-06",
            "local_archive_present": "false",
            "rebuild_required": "false",
            "previously_locally_verified_before_transfer": "true",
            "remote_post_transfer_verification": "not_performed_by_this_task",
            "confirmed_by_user": "true",
        })
        row["status"] = "transferred_by_user"
        row["verification_status"] = "accepted_before_transfer"

    for number in range(23, 29):
        row = by_volume[f"VOL-{number:03d}"]
        if row["status"] not in {"held_for_space", "planned"}:
            raise RuntimeError(f"unexpected resume status for {row['volume_id']}: {row['status']}")
        row["status"] = "planned"
        row["verification_status"] = "not_started_resume_preflight"

    all_members: set[str] = set()
    earlier_source_ids: set[str] = set()
    remaining_source_ids: set[str] = set()
    remaining_source_count = 0
    remaining_text_count = 0
    remaining_source_bytes = 0
    remaining_text_bytes = 0
    missing = []
    size_mismatches = []
    unsafe = []
    for row in assignments:
        is_remaining = row["volume_id"] in {f"VOL-{i:03d}" for i in range(23, 29)}
        (remaining_source_ids if is_remaining else earlier_source_ids).add(row["source_id"])
        for kind, local_key, archive_key, size_key in (
            ("source", "current_relative_path", "archive_relative_path", "source_size_bytes"),
            ("text", "text_current_relative_path", "text_archive_relative_path", "text_size_bytes"),
        ):
            local = row.get(local_key, "").strip()
            archive = row.get(archive_key, "").strip()
            if not local:
                continue
            member = f"{RELEASE}/{archive}"
            if not safe_path(member) or member in all_members:
                unsafe.append({"source_id": row["source_id"], "member": member})
            all_members.add(member)
            if not is_remaining:
                continue
            path = repo / local
            if not path.is_file() or path.is_symlink():
                missing.append(local)
                continue
            expected = int(row.get(size_key) or 0)
            if path.stat().st_size != expected:
                size_mismatches.append({"path": local, "expected": expected, "actual": path.stat().st_size})
            if kind == "source":
                remaining_source_count += 1; remaining_source_bytes += expected
            else:
                remaining_text_count += 1; remaining_text_bytes += expected
    if earlier_source_ids & remaining_source_ids:
        raise RuntimeError("a source ID overlaps earlier and remaining volume assignments")
    if unsafe or missing or size_mismatches:
        raise RuntimeError(f"resume source/path audit failed: unsafe={len(unsafe)} missing={len(missing)} size={len(size_mismatches)}")
    if remaining_source_count != 5570 or remaining_text_count != 4875:
        raise RuntimeError(f"remaining totals differ: sources={remaining_source_count}, text={remaining_text_count}")

    for target in (task, manifests):
        write_csv(target / "source_library_transferred_volumes.csv", transfer_rows, TRANSFER_FIELDS)
        write_jsonl(target / "source_library_transferred_volumes.jsonl", transfer_rows)
        write_csv(target / "VOLUME_MANIFEST.csv", volume_rows)
        write_json(target / "VOLUME_MANIFEST.json", volume_rows)

    # A bounded smoke archive proves the gzip-backed frozen assignment can be
    # read and that the writer still produces the established archive layout.
    spec = importlib.util.spec_from_file_location("packager", task / "tools/package_source_library.py")
    assert spec and spec.loader
    packager = importlib.util.module_from_spec(spec); spec.loader.exec_module(packager)
    candidates = [r for r in assignments if r["volume_id"] == "VOL-023"]
    candidates.sort(key=lambda r: int(r["source_size_bytes"]))
    smoke_rows = []
    for row in candidates[:4]:
        item = dict(row); item["volume_id"] = "VOL-SMOKE"; item["volume_filename"] = "resume-smoke.tar.zst"
        smoke_rows.append(item)
    smoke_root = repo / "tmp/gabriel_wages_source_library_resume_smoke"
    smoke_root.mkdir(parents=True, exist_ok=True)
    smoke_csv = smoke_root / "assignments.csv"
    write_csv(smoke_csv, smoke_rows)
    result = packager.write_volume(assignments=smoke_csv, volume_id="VOL-SMOKE", repo_root=repo, parts_dir=smoke_root, compression_level=3, threads=1, free_floor=8 * 1024**3)
    if result["status"] != "accepted" or result["verified_source_member_count"] != 4:
        raise RuntimeError("resume smoke archive failed")
    (smoke_root / "resume-smoke.tar.zst").unlink()
    smoke_csv.unlink()

    free = shutil.disk_usage(repo).free
    summary = {
        "status": "pass",
        "assignment_sha256": EXPECTED_HASH,
        "assignment_rows": len(assignments),
        "transferred_by_user_volume_count": 22,
        "earlier_local_archive_count": 0,
        "earlier_volumes_rebuilt": 0,
        "resume_volume_ids": [f"VOL-{i:03d}" for i in range(23, 29)],
        "remaining_source_count": remaining_source_count,
        "remaining_source_bytes": remaining_source_bytes,
        "remaining_text_companion_count": remaining_text_count,
        "remaining_text_bytes": remaining_text_bytes,
        "missing_source_count": 0,
        "size_mismatch_count": 0,
        "archive_member_collision_count": 0,
        "free_bytes_after_preflight": free,
        "safe_floor_bytes": 8 * 1024**3,
        "smoke_archive_status": "pass_and_temporary_output_deleted",
    }
    write_json(resume / "resume_preflight_audit.json", summary)
    (resume / "resume_preflight_audit.md").write_text(
        "# Resume preflight audit\n\nThe frozen assignment hash matched. VOL-001 through VOL-022 were recorded as transferred by the user and were not rebuilt. The remaining 5,570 sources and 4,875 text companions exist at their frozen paths with matching sizes. The bounded resume smoke archive passed and its temporary output was deleted.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
