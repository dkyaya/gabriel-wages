#!/usr/bin/env python3
"""Stream frozen source assignments into independent .tar.zst volumes.

This tool never creates an uncompressed staging tree. It reads source and
extracted-text files in place, assigns portable archive names supplied by a
locked CSV, and writes one independent Zstandard-compressed tar volume at a
time. Accepted archives are verified by streaming every member back from the
compressed file and checking hashes for all file members.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import time
from typing import Iterable


ARCHIVE_ROOT = "gabriel-wages-source-library-2026-08-06"
SAFE_FREE_FLOOR = 8 * 1024**3


def sha256_file(path: Path, chunk_size: int = 8 * 1024**2) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def safe_member_name(name: str) -> str:
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or ".." in p.parts:
        raise ValueError(f"unsafe archive member path: {name!r}")
    clean = p.as_posix()
    if clean.startswith("/") or "\x00" in clean:
        raise ValueError(f"unsafe archive member path: {name!r}")
    return clean


def read_assignments(path: Path, volume_id: str | None = None) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if volume_id:
        rows = [row for row in rows if row["volume_id"] == volume_id]
    if not rows:
        raise ValueError(f"no assignments found for {volume_id or 'input'}")
    return rows


def assignment_member_rows(rows: Iterable[dict[str, str]], repo_root: Path) -> list[dict[str, object]]:
    members: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        for kind, local_key, archive_key, size_key, hash_key in (
            ("source", "current_relative_path", "archive_relative_path", "source_size_bytes", "source_sha256"),
            ("extracted_text", "text_current_relative_path", "text_archive_relative_path", "text_size_bytes", "text_sha256"),
        ):
            local_value = row.get(local_key, "").strip()
            archive_value = row.get(archive_key, "").strip()
            if not local_value:
                continue
            local_path = repo_root / local_value
            if local_path.is_symlink() or not local_path.is_file():
                raise FileNotFoundError(f"missing or unsafe assigned {kind}: {local_value}")
            member_name = safe_member_name(f"{ARCHIVE_ROOT}/{archive_value}")
            if member_name in seen:
                raise ValueError(f"duplicate archive member path: {member_name}")
            seen.add(member_name)
            actual_size = local_path.stat().st_size
            expected_size = int(row.get(size_key) or actual_size)
            if actual_size != expected_size:
                raise ValueError(f"size mismatch for {local_value}: {actual_size} != {expected_size}")
            expected_hash = row.get(hash_key, "").strip()
            if not expected_hash:
                expected_hash = sha256_file(local_path)
            members.append(
                {
                    "kind": kind,
                    "source_id": row["source_id"],
                    "local_path": local_path,
                    "member_name": member_name,
                    "size": actual_size,
                    "sha256": expected_hash,
                }
            )
    return members


def normalized_tarinfo(tar: tarfile.TarFile, path: Path, arcname: str) -> tarfile.TarInfo:
    info = tar.gettarinfo(str(path), arcname=arcname)
    if not info.isfile():
        raise ValueError(f"only regular files may be archived: {path}")
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = 0
    info.mode = 0o644
    return info


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def write_volume(
    *,
    assignments: Path,
    volume_id: str,
    repo_root: Path,
    parts_dir: Path,
    compression_level: int,
    threads: int,
    free_floor: int,
) -> dict[str, object]:
    rows = read_assignments(assignments, volume_id)
    members = assignment_member_rows(rows, repo_root)
    planned_bytes = sum(int(member["size"]) for member in members)
    parts_dir.mkdir(parents=True, exist_ok=True)
    filename = rows[0]["volume_filename"]
    final_path = parts_dir / filename
    partial_path = parts_dir / f"{filename}.partial"
    if final_path.exists():
        raise FileExistsError(f"accepted archive already exists: {final_path}")
    if partial_path.exists():
        raise FileExistsError(f"partial archive requires bounded review: {partial_path}")
    before_free = free_bytes(parts_dir)
    if before_free - planned_bytes < free_floor:
        return {
            "volume_id": volume_id,
            "status": "held_for_space",
            "planned_total_bytes": planned_bytes,
            "free_bytes_before": before_free,
            "projected_free_bytes": before_free - planned_bytes,
            "required_floor_bytes": free_floor,
        }

    source_count = sum(1 for member in members if member["kind"] == "source")
    text_count = sum(1 for member in members if member["kind"] == "extracted_text")
    volume_metadata = {
        "volume_id": volume_id,
        "filename": filename,
        "archive_root": ARCHIVE_ROOT,
        "source_count": source_count,
        "text_companion_count": text_count,
        "planned_total_bytes": planned_bytes,
        "member_manifest": [
            {
                "kind": member["kind"],
                "source_id": member["source_id"],
                "archive_member": member["member_name"],
                "size_bytes": member["size"],
                "sha256": member["sha256"],
            }
            for member in members
        ],
    }
    metadata_bytes = (json.dumps(volume_metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
    metadata_name = safe_member_name(f"{ARCHIVE_ROOT}/volume_metadata/{volume_id}.json")

    started = time.monotonic()
    command = [
        "zstd",
        "--quiet",
        f"-{compression_level}",
        f"-T{threads}",
        "-o",
        str(partial_path),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        with tarfile.open(fileobj=proc.stdin, mode="w|") as tar:
            for member in members:
                local_path = member["local_path"]
                info = normalized_tarinfo(tar, local_path, str(member["member_name"]))
                with local_path.open("rb") as src:
                    tar.addfile(info, src)
            info = tarfile.TarInfo(metadata_name)
            info.size = len(metadata_bytes)
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = 0
            tar.addfile(info, io.BytesIO(metadata_bytes))
        proc.stdin.close()
        rc = proc.wait()
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    if rc != 0:
        raise RuntimeError(f"zstd exited with status {rc}")
    with partial_path.open("rb") as stream:
        os.fsync(stream.fileno())
    partial_path.replace(final_path)
    archive_sha = sha256_file(final_path)
    validation = verify_volume(final_path, rows, repo_root)
    elapsed = time.monotonic() - started
    return {
        "volume_id": volume_id,
        "filename": filename,
        "status": "accepted" if validation["verification_status"] == "pass" else "failed",
        "source_count": source_count,
        "source_bytes": sum(int(m["size"]) for m in members if m["kind"] == "source"),
        "text_companion_count": text_count,
        "text_bytes": sum(int(m["size"]) for m in members if m["kind"] == "extracted_text"),
        "planned_total_bytes": planned_bytes,
        "compressed_bytes": final_path.stat().st_size,
        "compression_ratio": round(final_path.stat().st_size / planned_bytes, 6) if planned_bytes else 0,
        "archive_sha256": archive_sha,
        "member_count": len(members) + 1,
        "validation_method": "zstd integrity plus 100% streaming member SHA-256",
        "verified_source_member_count": validation["verified_source_member_count"],
        "verified_text_member_count": validation["verified_text_member_count"],
        "verification_status": validation["verification_status"],
        "runtime_seconds": round(elapsed, 3),
        "free_bytes_before": before_free,
        "free_bytes_after": free_bytes(parts_dir),
    }


def verify_volume(archive: Path, rows: list[dict[str, str]], repo_root: Path) -> dict[str, object]:
    subprocess.run(["zstd", "--test", "--quiet", str(archive)], check=True)
    expected_members = assignment_member_rows(rows, repo_root)
    expected = {str(member["member_name"]): member for member in expected_members}
    seen: set[str] = set()
    source_verified = 0
    text_verified = 0
    proc = subprocess.Popen(["zstd", "--decompress", "--stdout", "--quiet", str(archive)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        for info in tar:
            name = safe_member_name(info.name)
            if name in seen:
                raise ValueError(f"duplicate archive member during validation: {name}")
            seen.add(name)
            if name.startswith(f"{ARCHIVE_ROOT}/volume_metadata/"):
                continue
            if name not in expected:
                raise ValueError(f"unexpected archive member: {name}")
            if not info.isfile():
                raise ValueError(f"non-file archive member: {name}")
            stream = tar.extractfile(info)
            if stream is None:
                raise ValueError(f"cannot read archive member: {name}")
            h = hashlib.sha256()
            size = 0
            while chunk := stream.read(8 * 1024**2):
                h.update(chunk)
                size += len(chunk)
            record = expected[name]
            if size != record["size"] or h.hexdigest() != record["sha256"]:
                raise ValueError(f"member verification failed: {name}")
            if record["kind"] == "source":
                source_verified += 1
            else:
                text_verified += 1
    proc.stdout.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"zstd decompression validation exited with status {rc}")
    missing = set(expected) - seen
    if missing:
        raise ValueError(f"archive is missing {len(missing)} expected members")
    return {
        "verification_status": "pass",
        "expected_file_member_count": len(expected),
        "verified_source_member_count": source_verified,
        "verified_text_member_count": text_verified,
        "missing_member_count": 0,
        "unexpected_member_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write-volume")
    write.add_argument("--assignments", type=Path, required=True)
    write.add_argument("--volume-id", required=True)
    write.add_argument("--repo-root", type=Path, default=Path.cwd())
    write.add_argument("--parts-dir", type=Path, required=True)
    write.add_argument("--compression-level", type=int, default=6)
    write.add_argument("--threads", type=int, default=2)
    write.add_argument("--free-floor-bytes", type=int, default=SAFE_FREE_FLOOR)
    verify = sub.add_parser("verify-volume")
    verify.add_argument("--assignments", type=Path, required=True)
    verify.add_argument("--volume-id", required=True)
    verify.add_argument("--repo-root", type=Path, default=Path.cwd())
    verify.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "write-volume":
        result = write_volume(
            assignments=args.assignments,
            volume_id=args.volume_id,
            repo_root=args.repo_root.resolve(),
            parts_dir=args.parts_dir,
            compression_level=args.compression_level,
            threads=args.threads,
            free_floor=args.free_floor_bytes,
        )
    else:
        rows = read_assignments(args.assignments, args.volume_id)
        result = verify_volume(args.archive, rows, args.repo_root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
