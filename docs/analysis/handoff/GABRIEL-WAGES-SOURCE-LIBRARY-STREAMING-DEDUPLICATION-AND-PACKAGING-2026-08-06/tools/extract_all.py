#!/usr/bin/env python3
"""Safely extract independent source-library volumes into one destination."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile


RELEASE = "gabriel-wages-source-library-2026-08-06"
EXPECTED_PARTS = set(range(1, 29))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str) -> Path:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] != RELEASE:
        raise ValueError(f"unsafe archive member: {name}")
    return Path(*p.parts)


def extract_volume(archive: Path, destination: Path) -> None:
    proc = subprocess.Popen(["zstd", "-dcq", str(archive)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        for info in tar:
            relative = safe_name(info.name)
            if not info.isfile():
                raise ValueError(f"unsupported non-file member: {info.name}")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            incoming = tar.extractfile(info)
            if incoming is None:
                raise ValueError(f"unreadable member: {info.name}")
            if target.exists():
                h = hashlib.sha256()
                while chunk := incoming.read(8 * 1024**2):
                    h.update(chunk)
                if digest(target) != h.hexdigest():
                    raise FileExistsError(f"different-content file already exists: {target}")
                continue
            partial = target.with_name(target.name + ".partial")
            with partial.open("wb") as output:
                while chunk := incoming.read(8 * 1024**2):
                    output.write(chunk)
            partial.replace(target)
    proc.stdout.close()
    if proc.wait() != 0:
        raise RuntimeError(f"decompression failed: {archive}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parts_directory", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    parts = sorted(args.parts_directory.glob(f"{RELEASE}.part-*.tar.zst"))
    if not parts:
        raise SystemExit("no source-library parts found")
    pattern = re.compile(rf"^{re.escape(RELEASE)}\.part-(\d{{3}})\.tar\.zst$")
    numbers = []
    for part in parts:
        match = pattern.match(part.name)
        if not match:
            raise SystemExit(f"invalid part filename: {part.name}")
        numbers.append(int(match.group(1)))
    missing = sorted(EXPECTED_PARTS - set(numbers))
    duplicates = sorted(number for number in set(numbers) if numbers.count(number) > 1)
    unexpected = sorted(set(numbers) - EXPECTED_PARTS)
    if missing or duplicates or unexpected:
        raise SystemExit(f"incomplete archive set: missing={missing}, duplicates={duplicates}, unexpected={unexpected}")
    args.destination.mkdir(parents=True, exist_ok=True)
    for part in parts:
        extract_volume(part, args.destination)
        print(f"extracted {part.name}")


if __name__ == "__main__":
    main()
