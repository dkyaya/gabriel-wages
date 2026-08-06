#!/usr/bin/env python3
"""Verify one independently extractable source-library volume."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile


RELEASE = "gabriel-wages-source-library-2026-08-06"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    archive_sha = sha(args.archive)
    if args.expected_sha256 and archive_sha != args.expected_sha256:
        raise SystemExit("archive checksum mismatch")
    subprocess.run(["zstd", "-tq", str(args.archive)], check=True)
    seen = set()
    metadata = None
    proc = subprocess.Popen(["zstd", "-dcq", str(args.archive)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        for info in tar:
            p = PurePosixPath(info.name)
            if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] != RELEASE:
                raise SystemExit(f"unsafe member: {info.name}")
            if info.name in seen:
                raise SystemExit(f"duplicate member: {info.name}")
            seen.add(info.name)
            if "/volume_metadata/" in info.name:
                stream = tar.extractfile(info)
                if stream:
                    metadata = json.load(stream)
    proc.stdout.close()
    if proc.wait() != 0:
        raise SystemExit("archive decompression failed")
    if metadata is None:
        raise SystemExit("volume metadata missing")
    expected = {m["archive_member"] for m in metadata["member_manifest"]}
    if expected - seen:
        raise SystemExit(f"missing {len(expected - seen)} expected members")
    print(json.dumps({"status": "pass", "archive": args.archive.name, "sha256": archive_sha, "member_count": len(seen), "source_count": metadata["source_count"], "text_companion_count": metadata["text_companion_count"]}, indent=2))


if __name__ == "__main__":
    main()
